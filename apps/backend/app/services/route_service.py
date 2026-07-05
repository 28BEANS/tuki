"""
Tuki Backend — Route Service

Orchestrates the routing engine and formats navigation output.
Uses the cached transport graph from GraphService for all routing requests.

At query time, injects temporary walking nodes for the user's origin and
destination, connecting them to nearby jeep stops. These virtual nodes are
cleaned up after each request so the base graph remains unchanged.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import httpx

from app.schemas.routing import (
    NavigationInstruction,
    RouteRequest,
    RouteResponse,
    RouteSegment,
)

if TYPE_CHECKING:
    from app.services.graph_service import GraphService

logger = logging.getLogger("tuki.services.route")

# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum walking distance (metres) to connect virtual nodes to jeep stops.
# Stops beyond this radius are not reachable on foot and won't be connected.
WALK_RADIUS_M = 500.0

# Walking speed used to estimate walk segment travel time.
WALK_SPEED_KMH = 4.5

# IDs for virtual nodes injected per request — cleaned up before returning.
_VIRTUAL_ORIGIN = "virtual_origin"
_VIRTUAL_DEST = "virtual_destination"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in metres between two WGS-84 coords."""
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _walk_time_min(distance_m: float) -> float:
    """Estimated walking time in minutes."""
    return round((distance_m / 1000) / WALK_SPEED_KMH * 60, 1)


class RouteService:
    """
    Service for multimodal route calculation.

    Accepts a GraphService instance (injected from the API layer) and uses
    its cached NetworkX graph. Injects virtual walking nodes at query time
    to connect arbitrary user coordinates to the jeep stop network.
    """

    def __init__(self, graph_svc: GraphService) -> None:
        self._graph_svc = graph_svc

    async def calculate_route(self, request: RouteRequest) -> RouteResponse | None:
        """
        Calculate a multimodal route from origin to destination.

        Returns a RouteResponse on success, or None if no path exists.
        Raises RuntimeError if the graph is unavailable.

        Strategy:
        1. Inject virtual origin/destination nodes with walking edges.
        2. Run pathfinding on the augmented graph.
        3. Convert engine RouteResult → API RouteResponse with waypoints.
        4. Clean up virtual nodes so the base graph stays unchanged.
        """
        logger.info(
            "Route requested: (%.4f, %.4f) → (%.4f, %.4f) [prefer=%s]",
            request.origin_lat,
            request.origin_lon,
            request.destination_lat,
            request.destination_lon,
            request.prefer,
        )

        if not self._graph_svc.is_ready:
            raise RuntimeError("Routing graph unavailable")

        graph = self._graph_svc.graph
        assert graph is not None  # guaranteed by is_ready

        try:
            # 1. Inject virtual walking nodes
            self._inject_virtual_node(
                graph,
                _VIRTUAL_ORIGIN,
                request.origin_lat,
                request.origin_lon,
                "Your Location",
            )
            self._inject_virtual_node(
                graph,
                _VIRTUAL_DEST,
                request.destination_lat,
                request.destination_lon,
                "Destination",
            )

            # 2. Check if origin and destination are the same virtual node
            #    (both snap to the same area)
            if _VIRTUAL_ORIGIN == _VIRTUAL_DEST:
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

            # 3. Run pathfinding
            result = await self._run_pathfinding(graph, request)
            if result is None:
                return None

            return result

        finally:
            # 4. Always clean up virtual nodes
            self._remove_virtual_nodes(graph)

    # ── Virtual node injection ────────────────────────────────────────────────

    def _inject_virtual_node(
        self,
        graph,
        node_id: str,
        lat: float,
        lon: float,
        name: str,
    ) -> None:
        """
        Add a virtual node at (lat, lon) and connect it via walking edges
        to all jeep stops within WALK_RADIUS_M.

        The walking edges are bidirectional so pathfinding can reach
        jeep stops from the origin and reach the destination from jeep stops.
        """
        # Add the virtual node
        graph.add_node(
            node_id,
            name=name,
            latitude=lat,
            longitude=lon,
            node_type="walk",
            virtual=True,
        )

        # Find nearby jeep stops and connect with walking edges
        nearby = self._graph_svc.find_nearby_nodes(lat, lon, radius_m=WALK_RADIUS_M)

        if not nearby:
            # If no stops within default radius, connect to the single nearest stop
            nearest_id = self._graph_svc.find_nearest_node(lat, lon)
            if nearest_id:
                n_data = graph.nodes.get(nearest_id, {})
                dist = _haversine_m(
                    lat, lon,
                    n_data.get("latitude", 0.0),
                    n_data.get("longitude", 0.0),
                )
                nearby = [{"id": nearest_id, "distance_m": round(dist, 1)}]
                logger.warning(
                    "No stops within %.0fm of %s — connecting to nearest (%.0fm away)",
                    WALK_RADIUS_M, name, dist,
                )

        for stop in nearby:
            walk_dist = stop["distance_m"]
            walk_time = _walk_time_min(walk_dist)

            # Bidirectional walking edges
            for src, tgt in [(node_id, stop["id"]), (stop["id"], node_id)]:
                graph.add_edge(
                    src, tgt,
                    mode="walk",
                    distance_m=walk_dist,
                    fare=0.0,
                    travel_time_min=walk_time,
                    weight_time=walk_time,
                    weight_fare=0.0,
                    virtual=True,
                )

        logger.info(
            "Injected virtual node '%s' at (%.4f, %.4f) — %d walking edges",
            name, lat, lon, len(nearby) * 2,
        )

    def _remove_virtual_nodes(self, graph) -> None:
        """Remove all virtual nodes and their edges from the graph."""
        for vid in [_VIRTUAL_ORIGIN, _VIRTUAL_DEST]:
            if vid in graph:
                graph.remove_node(vid)

    # ── Pathfinding ───────────────────────────────────────────────────────────

    async def _get_road_following_waypoints(
        self, coords: list[list[float]], mode: str
    ) -> list[list[float]]:
        """
        Fetch road-following geometry between a list of coordinates from OSRM.
        Falls back to raw coordinates if OSRM is unreachable or fails.
        """
        if len(coords) < 2:
            return coords

        # OSRM expects lon,lat separated by semicolons
        coord_strs = [f"{lon},{lat}" for lat, lon in coords]
        coords_param = ";".join(coord_strs)

        # Profile is 'foot' for walk/transfer, 'driving' for jeepney/tricycle
        profile = "foot" if mode in ("walk", "transfer") else "driving"
        url = f"http://router.project-osrm.org/route/v1/{profile}/{coords_param}?overview=full&geometries=geojson"

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        geom = data["routes"][0]["geometry"]
                        return [[lat, lon] for lon, lat in geom["coordinates"]]
        except Exception as e:
            logger.warning("OSRM routing failed (falling back to straight lines): %s", e)

        return coords

    async def _run_pathfinding(
        self, graph, request: RouteRequest
    ) -> RouteResponse | None:
        """Run pathfinding on the augmented graph and build the response."""
        from routing_engine.graph_models import TransportMode
        from routing_engine.pathfinding import find_route
        from routing_engine.route_generator import RouteGenerator
        from routing_engine.fare_engine import FareEngine
        from routing_engine.eta_engine import ETAEngine

        route_result = find_route(
            graph, _VIRTUAL_ORIGIN, _VIRTUAL_DEST, strategy=request.prefer
        )
        if route_result is None:
            logger.warning("No path found between origin and destination")
            return None

        # Enrich with fare and ETA
        fare_engine = FareEngine()
        eta_engine = ETAEngine()
        fare_engine.calculate_total_fare(route_result, is_student=request.is_student)
        eta_engine.estimate_total_time(route_result)

        # Generate instructions
        generator = RouteGenerator()
        raw_instructions = generator.generate_instructions(route_result)

        # Map routing engine segments → API schema segments (with road-following waypoints)
        segments: list[RouteSegment] = []
        for seg in route_result.segments:
            # Collect waypoint coordinates from all nodes in this segment
            raw_waypoints: list[list[float]] = []
            for node_id in seg.nodes:
                node_data = graph.nodes.get(node_id, {})
                lat = node_data.get("latitude")
                lon = node_data.get("longitude")
                if lat is not None and lon is not None:
                    raw_waypoints.append([lat, lon])

            # Get road-following path via OSRM
            waypoints = await self._get_road_following_waypoints(
                raw_waypoints, seg.mode.value
            )

            board_node = seg.nodes[0] if seg.nodes else None
            alight_node = seg.nodes[-1] if seg.nodes else None

            board_lat = graph.nodes[board_node].get("latitude") if board_node else None
            board_lon = graph.nodes[board_node].get("longitude") if board_node else None
            alight_lat = (
                graph.nodes[alight_node].get("latitude") if alight_node else None
            )
            alight_lon = (
                graph.nodes[alight_node].get("longitude") if alight_node else None
            )

            if seg.mode == TransportMode.TRANSFER:
                # Represent transfers as short walk segments in the API
                segments.append(
                    RouteSegment(
                        mode="walk",
                        distance_m=seg.distance_m,
                        duration_min=seg.duration_min,
                        fare=0,
                        board_at=seg.board_at,
                        board_lat=board_lat,
                        board_lon=board_lon,
                        alight_at=seg.alight_at,
                        alight_lat=alight_lat,
                        alight_lon=alight_lon,
                        waypoints=waypoints if len(waypoints) >= 2 else None,
                    )
                )
            else:
                segments.append(
                    RouteSegment(
                        mode=seg.mode.value,
                        route=seg.route_name,
                        route_color=seg.route_color,
                        board_at=seg.board_at,
                        board_lat=board_lat,
                        board_lon=board_lon,
                        alight_at=seg.alight_at,
                        alight_lat=alight_lat,
                        alight_lon=alight_lon,
                        distance_m=seg.distance_m,
                        duration_min=seg.duration_min,
                        fare=seg.fare,
                        waypoints=waypoints if len(waypoints) >= 2 else None,
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
