"""
Tuki Backend — Route Service

Orchestrates the routing engine and formats navigation output.
Uses the cached transport graph from GraphService for all routing requests.
Falls back to mock data when the graph is not yet available.
"""

from __future__ import annotations

import logging

from app.schemas.routing import (
    NavigationInstruction,
    RouteRequest,
    RouteResponse,
    RouteSegment,
)

logger = logging.getLogger("tuki.services.route")

# ── Mock fallback (used when graph is not available) ──────────────────────────

_MOCK_SEGMENTS = [
    RouteSegment(
        mode="walk",
        board_at=None,
        alight_at=None,
        distance_m=250,
        duration_min=3,
        fare=0,
    ),
    RouteSegment(
        mode="jeep",
        route="Checkpoint – Holy – Highway",
        route_color="Lavender",
        board_at="Holy Angel University",
        alight_at="Jenra Mall",
        distance_m=3200,
        duration_min=12,
        fare=13,
    ),
    RouteSegment(
        mode="walk",
        distance_m=180,
        duration_min=2,
        fare=0,
    ),
    RouteSegment(
        mode="tricycle",
        distance_m=800,
        duration_min=5,
        fare=25,
    ),
]

_MOCK_INSTRUCTIONS = [
    NavigationInstruction(
        step=1,
        instruction="Walk 250 meters to Holy Angel University jeepney stop.",
        mode="walk",
    ),
    NavigationInstruction(
        step=2,
        instruction="Board the Lavender Jeep (Checkpoint–Holy–Highway) at Holy Angel University.",
        mode="jeep",
    ),
    NavigationInstruction(
        step=3,
        instruction="Stay on the jeep until Jenra Mall.",
        mode="jeep",
    ),
    NavigationInstruction(
        step=4,
        instruction="Walk approximately 180 meters toward the tricycle terminal.",
        mode="walk",
    ),
    NavigationInstruction(
        step=5,
        instruction="Ride the tricycle to your destination.",
        mode="tricycle",
    ),
]


class RouteService:
    """
    Service for multimodal route calculation.

    Accepts a GraphService instance (injected from the API layer) and uses
    its cached NetworkX graph. Gracefully falls back to mock data when the
    graph is unavailable (e.g., DB unreachable at startup).
    """

    def __init__(self, graph_svc: "GraphService | None" = None) -> None:  # noqa: F821
        self._graph_svc = graph_svc

    async def calculate_route(self, request: RouteRequest) -> RouteResponse:
        """
        Calculate a multimodal route from origin to destination.

        Strategy:
        1. If graph is available → find nearest nodes, run pathfinding.
        2. Convert RouteResult (engine model) → RouteResponse (API schema).
        3. Generate landmark-based NavigationInstructions.
        4. Fallback to mock if no path found or graph is unavailable.
        """
        logger.info(
            "Route requested: (%.4f, %.4f) → (%.4f, %.4f) [prefer=%s]",
            request.origin_lat,
            request.origin_lon,
            request.destination_lat,
            request.destination_lon,
            request.prefer,
        )

        if self._graph_svc and self._graph_svc.is_ready:
            result = await self._calculate_from_graph(request)
            if result is not None:
                return result
            logger.warning("Graph pathfinding returned no path — falling back to mock")

        logger.info("Using mock route response")
        return RouteResponse(
            total_fare=38,
            total_distance_m=4430,
            travel_time_min=22,
            segments=_MOCK_SEGMENTS,
            instructions=_MOCK_INSTRUCTIONS,
            transfers=2,
        )

    async def _calculate_from_graph(
        self, request: RouteRequest
    ) -> RouteResponse | None:
        """Run pathfinding on the cached graph and build the response."""
        from routing_engine.graph_models import TransportMode
        from routing_engine.pathfinding import find_route
        from routing_engine.route_generator import RouteGenerator
        from routing_engine.fare_engine import FareEngine
        from routing_engine.eta_engine import ETAEngine

        graph = self._graph_svc.graph  # type: ignore[union-attr]

        origin_id = self._graph_svc.find_nearest_node(  # type: ignore[union-attr]
            request.origin_lat, request.origin_lon
        )
        dest_id = self._graph_svc.find_nearest_node(  # type: ignore[union-attr]
            request.destination_lat, request.destination_lon
        )

        if not origin_id or not dest_id:
            return None

        if origin_id == dest_id:
            # Already at destination
            return RouteResponse(
                total_fare=0,
                total_distance_m=0,
                travel_time_min=0,
                segments=[],
                instructions=[
                    NavigationInstruction(
                        step=1,
                        instruction="You are already at your destination.",
                        mode="walk",
                    )
                ],
                transfers=0,
            )

        route_result = find_route(graph, origin_id, dest_id, strategy=request.prefer)
        if route_result is None:
            return None

        # Enrich with fare and ETA
        fare_engine = FareEngine()
        eta_engine = ETAEngine()
        fare_engine.calculate_total_fare(route_result, is_student=request.is_student)
        eta_engine.estimate_total_time(route_result)

        # Generate instructions
        generator = RouteGenerator()
        raw_instructions = generator.generate_instructions(route_result)

        # Map routing engine segments → API schema segments
        segments: list[RouteSegment] = []
        for seg in route_result.segments:
            if seg.mode == TransportMode.TRANSFER:
                # Represent transfers as short walk segments in the API
                segments.append(
                    RouteSegment(
                        mode="walk",
                        distance_m=seg.distance_m,
                        duration_min=seg.duration_min,
                        fare=0,
                    )
                )
            else:
                segments.append(
                    RouteSegment(
                        mode=seg.mode.value,
                        route=seg.route_name,
                        route_color=seg.route_color,
                        board_at=seg.board_at,
                        alight_at=seg.alight_at,
                        distance_m=seg.distance_m,
                        duration_min=seg.duration_min,
                        fare=seg.fare,
                    )
                )

        instructions: list[NavigationInstruction] = [
            NavigationInstruction(
                step=instr["step"],
                instruction=instr["instruction"],
                mode=instr["mode"],
            )
            for instr in raw_instructions
        ]

        return RouteResponse(
            total_fare=route_result.total_fare,
            total_distance_m=round(route_result.total_distance_m, 1),
            travel_time_min=round(route_result.total_time_min, 1),
            segments=segments,
            instructions=instructions,
            transfers=route_result.transfers,
        )
