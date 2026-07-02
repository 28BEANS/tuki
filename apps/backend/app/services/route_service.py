"""
Tuki Backend — Route Service

Orchestrates the routing engine and formats navigation output.
Initially returns mocked data using the correct response schema.
"""

import logging

from app.schemas.routing import (
    NavigationInstruction,
    RouteRequest,
    RouteResponse,
    RouteSegment,
)

logger = logging.getLogger("tuki.services.route")


class RouteService:
    """
    Service for multimodal route calculation.

    Currently returns mocked responses. Will integrate with the
    routing_engine package once the transport graph is built.
    """

    async def calculate_route(self, request: RouteRequest) -> RouteResponse:
        """
        Calculate a multimodal route from origin to destination.

        TODO: Replace mock with actual routing engine integration:
        1. Build/load transport graph
        2. Find nearest nodes to origin/destination
        3. Run pathfinding algorithm
        4. Generate segments and fare breakdown
        5. Produce landmark-based navigation instructions
        """
        logger.info(
            "Route requested: (%.4f, %.4f) → (%.4f, %.4f) [prefer=%s]",
            request.origin_lat,
            request.origin_lon,
            request.destination_lat,
            request.destination_lon,
            request.prefer,
        )

        # Mock response demonstrating the schema structure
        segments = [
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

        instructions = [
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

        return RouteResponse(
            total_fare=38,
            total_distance_m=4430,
            travel_time_min=22,
            segments=segments,
            instructions=instructions,
            transfers=2,
        )
