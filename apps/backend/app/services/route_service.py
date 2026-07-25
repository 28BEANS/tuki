"""
Tuki Backend — Route Service

Orchestrates the routing engine and formats navigation output.
Uses the cached transport graph from GraphService for all routing requests.

At query time, injects temporary walking nodes for the user's origin and
destination into a per-request graph copy, connecting them to nearby jeep
stops without mutating the shared cached graph.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from routing_engine.graph_models import JEEP_WAIT_TIME_MIN

from app.schemas.routing import (
    NavigationInstruction,
    RouteRequest,
    RouteResponse,
    RouteSegment,
)
from app.services.road_geometry_service import RoadGeometryService

if TYPE_CHECKING:
    from app.services.graph_service import GraphService

logger = logging.getLogger("tuki.services.route")

# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum walking distance (metres) to connect virtual nodes to jeep stops.
# Stops beyond this radius are not reachable on foot and won't be connected.
WALK_RADIUS_M = 500.0

# Walking speed used to estimate walk segment travel time.
WALK_SPEED_KMH = 4.5

# Maximum acceptable distance (metres) from the requested coordinate to the
# nearest graph node.  Beyond this the snapping is considered unreliable.
_MAX_SNAP_DISTANCE_M = 1000.0

# Maximum acceptable distance (metres) between a route endpoint and the
# requested origin/destination.  Routes that exceed this are rejected.
_MAX_ENDPOINT_DRIFT_M = 500.0

# Short trips may be completed entirely on foot.
_MAX_DIRECT_WALK_M = 1_500.0

# Stable IDs are safe because every request works on its own graph copy.
_VIRTUAL_ORIGIN = "virtual_origin"
_VIRTUAL_DEST = "virtual_destination"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in metres between two WGS-84 coords."""
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
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

    def __init__(
        self,
        graph_svc: GraphService,
        geometry_svc: RoadGeometryService | None = None,
    ) -> None:
        self._graph_svc = graph_svc
        self._geometry_svc = geometry_svc or RoadGeometryService()

    async def calculate_route(self, request: RouteRequest) -> RouteResponse | None:
        """
        Calculate a multimodal route from origin to destination.

        Returns a RouteResponse on success, or None if no path exists.
        Raises RuntimeError if the graph is unavailable.

        Strategy:
        1. Copy the cached graph for request isolation.
        2. Inject virtual origin/destination nodes with walking edges.
        3. Run pathfinding on the augmented graph.
        4. Convert engine RouteResult → API RouteResponse with waypoints.
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

        direct_distance = _haversine_m(
            request.origin_lat,
            request.origin_lon,
            request.destination_lat,
            request.destination_lon,
        )
        if direct_distance <= 5.0:
            return RouteResponse(
                total_fare=0,
                total_distance_m=round(direct_distance, 1),
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

        base_graph = self._graph_svc.graph
        assert base_graph is not None  # guaranteed by is_ready
        graph = base_graph.copy(as_view=False)

        origin_connected = self._inject_virtual_node(
            graph,
            _VIRTUAL_ORIGIN,
            request.origin_lat,
            request.origin_lon,
            "Your Location",
        )
        destination_connected = self._inject_virtual_node(
            graph,
            _VIRTUAL_DEST,
            request.destination_lat,
            request.destination_lon,
            "Destination",
        )
        if not origin_connected or not destination_connected:
            return None

        if direct_distance <= _MAX_DIRECT_WALK_M:
            direct_walk_time = _walk_time_min(direct_distance)
            graph.add_edge(
                _VIRTUAL_ORIGIN,
                _VIRTUAL_DEST,
                mode="walk",
                distance_m=round(direct_distance, 1),
                fare=0.0,
                travel_time_min=direct_walk_time,
                weight_time=direct_walk_time,
                weight_fare=0.0,
                virtual=True,
            )

        return await self._run_pathfinding(graph, request)

    # ── Virtual node injection ────────────────────────────────────────────────

    def _inject_virtual_node(
        self,
        graph,
        node_id: str,
        lat: float,
        lon: float,
        name: str,
    ) -> bool:
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
                    lat,
                    lon,
                    n_data.get("latitude", 0.0),
                    n_data.get("longitude", 0.0),
                )
                if dist > _MAX_SNAP_DISTANCE_M:
                    logger.warning(
                        "Rejecting '%s': nearest graph node is %.0fm away",
                        name,
                        dist,
                    )
                    graph.remove_node(node_id)
                    return False

                nearby = [{"id": nearest_id, "distance_m": round(dist, 1)}]
                logger.warning(
                    "No stops within %.0fm of %s — connecting to nearest (%.0fm away)",
                    WALK_RADIUS_M,
                    name,
                    dist,
                )

        if not nearby:
            graph.remove_node(node_id)
            return False

        # Log snapped node info
        if nearby:
            closest = nearby[0]
            logger.debug(
                "'%s' snapped to node '%s' (%.1fm away)",
                name,
                closest["id"],
                closest["distance_m"],
            )

        for stop in nearby:
            walk_dist = stop["distance_m"]
            walk_time = _walk_time_min(walk_dist)

            # Bidirectional walking edges
            for src, tgt in [(node_id, stop["id"]), (stop["id"], node_id)]:
                routing_time = walk_time
                if node_id == _VIRTUAL_ORIGIN and src == node_id:
                    # The fastest-route weight must account for the first
                    # jeep wait. ETAEngine already reports this wait in the
                    # final duration; this only affects route selection.
                    routing_time += JEEP_WAIT_TIME_MIN
                graph.add_edge(
                    src,
                    tgt,
                    mode="walk",
                    distance_m=walk_dist,
                    fare=0.0,
                    travel_time_min=walk_time,
                    weight_time=round(routing_time, 1),
                    weight_fare=0.0,
                    virtual=True,
                )

        logger.info(
            "Injected virtual node '%s' at (%.4f, %.4f) — %d walking edges",
            name,
            lat,
            lon,
            len(nearby) * 2,
        )
        return True

    # ── Pathfinding ───────────────────────────────────────────────────────────

    async def _run_pathfinding(self, graph, request: RouteRequest) -> RouteResponse | None:
        """Run pathfinding on the augmented graph and build the response."""
        from routing_engine.eta_engine import ETAEngine
        from routing_engine.fare_engine import FareEngine
        from routing_engine.graph_models import TransportMode
        from routing_engine.pathfinding import find_route
        from routing_engine.route_generator import RouteGenerator

        origin_coord = [request.origin_lat, request.origin_lon]
        dest_coord = [request.destination_lat, request.destination_lon]

        route_result = find_route(graph, _VIRTUAL_ORIGIN, _VIRTUAL_DEST, strategy=request.prefer)
        if route_result is None:
            logger.warning("No path found between origin and destination")
            return None

        # Enrich with fare and ETA
        fare_engine = FareEngine()
        eta_engine = ETAEngine()
        fare_engine.calculate_total_fare(route_result, is_student=request.is_student)
        eta_engine.estimate_total_time(route_result)

        # Virtual endpoints and shared transfer stops can create zero-metre
        # walking segments. They add duplicate markers and misleading
        # instructions without contributing any geometry.
        route_result.segments = [
            segment for segment in route_result.segments if segment.distance_m >= 1.0
        ]

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

            # Resolve road-following geometry while preserving exact graph
            # endpoints and the authoritative stop order.
            waypoints = await self._geometry_svc.get_geometry(raw_waypoints, seg.mode.value)

            board_node = seg.nodes[0] if seg.nodes else None
            alight_node = seg.nodes[-1] if seg.nodes else None

            board_lat = graph.nodes[board_node].get("latitude") if board_node else None
            board_lon = graph.nodes[board_node].get("longitude") if board_node else None
            alight_lat = graph.nodes[alight_node].get("latitude") if alight_node else None
            alight_lon = graph.nodes[alight_node].get("longitude") if alight_node else None

            if seg.mode == TransportMode.TRANSFER:
                # Represent transfers as short walk segments in the API
                segments.append(
                    RouteSegment(
                        mode="walk",
                        route=None,
                        route_color=None,
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

        # ── Connector segments: ensure route starts at Point A / ends at Point B ──
        self._ensure_endpoint_connectors(segments, origin_coord, dest_coord)

        # ── Validate route endpoints ──────────────────────────────────────────
        if not self._validate_route_endpoints(segments, origin_coord, dest_coord):
            logger.error("Route endpoints too far from requested coordinates — rejecting")
            return None

        # ── Diagnostic: log final route geometry summary ──────────────────────
        self._log_route_summary(segments, origin_coord, dest_coord)

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

    # ── Endpoint connectors ───────────────────────────────────────────────────

    @staticmethod
    def _ensure_endpoint_connectors(
        segments: list[RouteSegment],
        origin_coord: list[float],
        dest_coord: list[float],
    ) -> None:
        """
        Prepend the exact origin coordinate to the first segment's waypoints
        and append the exact destination coordinate to the last segment's
        waypoints so the rendered polyline begins at Point A and ends at
        Point B.
        """
        if not segments:
            return

        # ── Prepend origin ────────────────────────────────────────────────────
        first_seg = segments[0]
        if first_seg.waypoints and len(first_seg.waypoints) >= 1:
            first_wp = first_seg.waypoints[0]
            dist = _haversine_m(origin_coord[0], origin_coord[1], first_wp[0], first_wp[1])
            # Only prepend if the first waypoint is noticeably different
            if dist > 5.0:  # more than 5 metres
                first_seg.waypoints.insert(0, origin_coord)
        elif first_seg.board_lat is not None and first_seg.board_lon is not None:
            dist = _haversine_m(
                origin_coord[0],
                origin_coord[1],
                first_seg.board_lat,
                first_seg.board_lon,
            )
            if dist > 5.0:
                first_seg.waypoints = [
                    origin_coord,
                    [first_seg.board_lat, first_seg.board_lon],
                ]

        # ── Append destination ────────────────────────────────────────────────
        last_seg = segments[-1]
        if last_seg.waypoints and len(last_seg.waypoints) >= 1:
            last_wp = last_seg.waypoints[-1]
            dist = _haversine_m(dest_coord[0], dest_coord[1], last_wp[0], last_wp[1])
            if dist > 5.0:
                last_seg.waypoints.append(dest_coord)
        elif last_seg.alight_lat is not None and last_seg.alight_lon is not None:
            dist = _haversine_m(
                dest_coord[0],
                dest_coord[1],
                last_seg.alight_lat,
                last_seg.alight_lon,
            )
            if dist > 5.0:
                last_seg.waypoints = [
                    [last_seg.alight_lat, last_seg.alight_lon],
                    dest_coord,
                ]

    # ── Route endpoint validation ─────────────────────────────────────────────

    @staticmethod
    def _validate_route_endpoints(
        segments: list[RouteSegment],
        origin_coord: list[float],
        dest_coord: list[float],
    ) -> bool:
        """
        Validate that the assembled route geometry starts near the requested
        origin and ends near the requested destination.

        Returns True if valid, False if the route is too far off.
        """
        if not segments:
            return False

        # Find the first coordinate of the route
        first_seg = segments[0]
        first_pt = None
        if first_seg.waypoints and len(first_seg.waypoints) >= 1:
            first_pt = first_seg.waypoints[0]
        elif first_seg.board_lat is not None and first_seg.board_lon is not None:
            first_pt = [first_seg.board_lat, first_seg.board_lon]

        # Find the last coordinate of the route
        last_seg = segments[-1]
        last_pt = None
        if last_seg.waypoints and len(last_seg.waypoints) >= 1:
            last_pt = last_seg.waypoints[-1]
        elif last_seg.alight_lat is not None and last_seg.alight_lon is not None:
            last_pt = [last_seg.alight_lat, last_seg.alight_lon]

        # Check origin
        if first_pt:
            origin_drift = _haversine_m(origin_coord[0], origin_coord[1], first_pt[0], first_pt[1])
            if origin_drift > _MAX_ENDPOINT_DRIFT_M:
                logger.error(
                    "Route start (%.6f,%.6f) is %.0fm from requested origin "
                    "(%.6f,%.6f) — exceeds %.0fm threshold",
                    first_pt[0],
                    first_pt[1],
                    origin_drift,
                    origin_coord[0],
                    origin_coord[1],
                    _MAX_ENDPOINT_DRIFT_M,
                )
                return False

        # Check destination
        if last_pt:
            dest_drift = _haversine_m(dest_coord[0], dest_coord[1], last_pt[0], last_pt[1])
            if dest_drift > _MAX_ENDPOINT_DRIFT_M:
                logger.error(
                    "Route end (%.6f,%.6f) is %.0fm from requested destination "
                    "(%.6f,%.6f) — exceeds %.0fm threshold",
                    last_pt[0],
                    last_pt[1],
                    dest_drift,
                    dest_coord[0],
                    dest_coord[1],
                    _MAX_ENDPOINT_DRIFT_M,
                )
                return False

        return True

    # ── Diagnostic logging ────────────────────────────────────────────────────

    @staticmethod
    def _log_route_summary(
        segments: list[RouteSegment],
        origin_coord: list[float],
        dest_coord: list[float],
    ) -> None:
        """Log a compact summary of the assembled route."""
        if not segments:
            return

        # First and last points
        first_seg = segments[0]
        last_seg = segments[-1]
        first_pt = (
            first_seg.waypoints[0]
            if first_seg.waypoints
            else [first_seg.board_lat, first_seg.board_lon]
        )
        last_pt = (
            last_seg.waypoints[-1]
            if last_seg.waypoints
            else [last_seg.alight_lat, last_seg.alight_lon]
        )

        total_dist = sum(s.distance_m or 0 for s in segments)

        logger.debug(
            "Route summary: %d segments, %.0fm total | " "first=(%.6f,%.6f) last=(%.6f,%.6f)",
            len(segments),
            total_dist,
            first_pt[0],
            first_pt[1],
            last_pt[0],
            last_pt[1],
        )
