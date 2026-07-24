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

# Maximum acceptable distance (metres) from the requested coordinate to the
# nearest graph node.  Beyond this the snapping is considered unreliable.
_MAX_SNAP_DISTANCE_M = 1000.0

# Maximum acceptable distance (metres) between a route endpoint and the
# requested origin/destination.  Routes that exceed this are rejected.
_MAX_ENDPOINT_DRIFT_M = 500.0

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

                # Warn if the nearest node is unreasonably far
                if dist > _MAX_SNAP_DISTANCE_M:
                    logger.warning(
                        "Nearest graph node for '%s' is %.0fm away — "
                        "route may be unreliable",
                        name, dist,
                    )

        # Log snapped node info for diagnostics
        if nearby:
            closest = nearby[0]
            logger.info(
                "[DIAG] '%s' snapped to node '%s' (%.1fm away)",
                name, closest["id"], closest["distance_m"],
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

        origin_coord = [request.origin_lat, request.origin_lon]
        dest_coord = [request.destination_lat, request.destination_lon]

        logger.info(
            "[DIAG] Point A: (%.6f, %.6f), Point B: (%.6f, %.6f)",
            origin_coord[0], origin_coord[1],
            dest_coord[0], dest_coord[1],
        )

        route_result = find_route(
            graph, _VIRTUAL_ORIGIN, _VIRTUAL_DEST, strategy=request.prefer
        )
        if route_result is None:
            logger.warning("No path found between origin and destination")
            return None

        # Log path node IDs for diagnostics
        for seg in route_result.segments:
            logger.info(
                "[DIAG] Segment %s: nodes=%s (first=%s, last=%s)",
                seg.mode.value,
                [seg.nodes[0], "...", seg.nodes[-1]] if len(seg.nodes) > 2 else seg.nodes,
                seg.nodes[0] if seg.nodes else None,
                seg.nodes[-1] if seg.nodes else None,
            )

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

        # ── Connector segments: ensure route starts at Point A / ends at Point B ──
        self._ensure_endpoint_connectors(segments, origin_coord, dest_coord)

        # ── Validate route endpoints ──────────────────────────────────────────
        if not self._validate_route_endpoints(segments, origin_coord, dest_coord):
            logger.error(
                "Route endpoints too far from requested coordinates — rejecting"
            )
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
            dist = _haversine_m(
                origin_coord[0], origin_coord[1], first_wp[0], first_wp[1]
            )
            # Only prepend if the first waypoint is noticeably different
            if dist > 5.0:  # more than 5 metres
                first_seg.waypoints.insert(0, origin_coord)
                logger.info(
                    "[DIAG] Prepended origin connector (%.1fm to first waypoint)",
                    dist,
                )
        elif first_seg.board_lat is not None and first_seg.board_lon is not None:
            dist = _haversine_m(
                origin_coord[0], origin_coord[1],
                first_seg.board_lat, first_seg.board_lon,
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
            dist = _haversine_m(
                dest_coord[0], dest_coord[1], last_wp[0], last_wp[1]
            )
            if dist > 5.0:
                last_seg.waypoints.append(dest_coord)
                logger.info(
                    "[DIAG] Appended destination connector (%.1fm to last waypoint)",
                    dist,
                )
        elif last_seg.alight_lat is not None and last_seg.alight_lon is not None:
            dist = _haversine_m(
                dest_coord[0], dest_coord[1],
                last_seg.alight_lat, last_seg.alight_lon,
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
            origin_drift = _haversine_m(
                origin_coord[0], origin_coord[1], first_pt[0], first_pt[1]
            )
            logger.info(
                "[DIAG] Origin drift: %.1fm (first route pt: %.6f,%.6f)",
                origin_drift, first_pt[0], first_pt[1],
            )
            if origin_drift > _MAX_ENDPOINT_DRIFT_M:
                logger.error(
                    "Route start (%.6f,%.6f) is %.0fm from requested origin "
                    "(%.6f,%.6f) — exceeds %.0fm threshold",
                    first_pt[0], first_pt[1], origin_drift,
                    origin_coord[0], origin_coord[1],
                    _MAX_ENDPOINT_DRIFT_M,
                )
                return False

        # Check destination
        if last_pt:
            dest_drift = _haversine_m(
                dest_coord[0], dest_coord[1], last_pt[0], last_pt[1]
            )
            logger.info(
                "[DIAG] Destination drift: %.1fm (last route pt: %.6f,%.6f)",
                dest_drift, last_pt[0], last_pt[1],
            )
            if dest_drift > _MAX_ENDPOINT_DRIFT_M:
                logger.error(
                    "Route end (%.6f,%.6f) is %.0fm from requested destination "
                    "(%.6f,%.6f) — exceeds %.0fm threshold",
                    last_pt[0], last_pt[1], dest_drift,
                    dest_coord[0], dest_coord[1],
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
        """Log a compact summary of the assembled route for diagnostics."""
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

        logger.info(
            "[DIAG] Route summary: %d segments, %.0fm total | "
            "first=(%.6f,%.6f) last=(%.6f,%.6f)",
            len(segments), total_dist,
            first_pt[0], first_pt[1],
            last_pt[0], last_pt[1],
        )
