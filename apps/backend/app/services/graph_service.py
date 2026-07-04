"""
Tuki Backend — Graph Service

Loads the Angeles City transport network from the database at startup,
builds the NetworkX routing graph once, and caches it in memory.
All routing requests read from the cached graph instead of hitting the DB.
"""

import logging
import math
from typing import Any

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import async_session_factory
from app.models.jeep_route import JeepRoute
from app.models.jeep_route_stop import JeepRouteStop
from app.models.jeep_stop import JeepStop
from app.models.transfer_point import TransferPoint
from routing_engine.graph_builder import TransportGraphBuilder
from routing_engine.graph_models import TransportEdge, TransportMode, TransportNode

logger = logging.getLogger("tuki.services.graph")

# Average speeds (km/h) used when computing edge travel times
_SPEEDS: dict[TransportMode, float] = {
    TransportMode.JEEP: 15.0,
    TransportMode.WALK: 4.5,
    TransportMode.TRICYCLE: 20.0,
    TransportMode.TRANSFER: 4.5,
}

# Jeep base fare constants (LTFRB PUJ, Oct 2023)
_JEEP_BASE_FARE = 13.0
_JEEP_BASE_DISTANCE_KM = 4.0
_JEEP_PER_KM = 1.80

# Transfer walk distance assumed when connecting routes at a transfer point
_TRANSFER_WALK_M = 150.0


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance in metres between two WGS-84 coords."""
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _jeep_fare(distance_m: float) -> float:
    """LTFRB jeep fare for a given segment distance."""
    km = distance_m / 1000
    if km <= _JEEP_BASE_DISTANCE_KM:
        return _JEEP_BASE_FARE
    return round(_JEEP_BASE_FARE + (km - _JEEP_BASE_DISTANCE_KM) * _JEEP_PER_KM, 2)


def _travel_min(distance_m: float, mode: TransportMode) -> float:
    speed = _SPEEDS.get(mode, 4.5)
    return round((distance_m / 1000) / speed * 60, 1)


class GraphService:
    """
    Manages the in-memory transport graph for Angeles City.

    Responsibilities:
    - Load all routes, stops, and transfer points from Supabase on startup.
    - Build a NetworkX MultiDiGraph via TransportGraphBuilder.
    - Expose the cached graph to RouteService.
    - Provide a refresh() method for future hot-reload without restarting.
    """

    def __init__(self) -> None:
        self._graph: nx.MultiDiGraph | None = None
        self._node_index: list[dict[str, Any]] = []  # Fast nearest-node lookup

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def graph(self) -> nx.MultiDiGraph | None:
        """Return the cached routing graph (None if not yet initialised)."""
        return self._graph

    @property
    def node_index(self) -> list[dict[str, Any]]:
        """Return the list of {id, lat, lon} dicts for nearest-node queries."""
        return self._node_index

    @property
    def is_ready(self) -> bool:
        return self._graph is not None and self._graph.number_of_nodes() > 0

    async def initialise(self) -> None:
        """
        Load data from the DB and build the routing graph.
        Called once from the FastAPI lifespan on startup.
        """
        logger.info("Initialising transport graph from database...")
        try:
            await self._build_graph()
            logger.info(
                "Transport graph ready: %d nodes, %d edges",
                self._graph.number_of_nodes() if self._graph else 0,
                self._graph.number_of_edges() if self._graph else 0,
            )
        except Exception as exc:
            logger.warning(
                "Graph initialisation failed — routing will use mock fallback: %s", exc
            )
            self._graph = None
            self._node_index = []

    async def refresh(self) -> None:
        """
        Rebuild the graph from the current DB state.
        Safe to call at runtime for hot-reload (e.g., after a data import).
        """
        logger.info("Refreshing transport graph...")
        await self._build_graph()
        logger.info("Transport graph refreshed.")

    def find_nearest_node(self, lat: float, lon: float) -> str | None:
        """
        Return the node ID whose coordinates are closest to (lat, lon).
        Returns None if the graph has no nodes.
        """
        if not self._node_index:
            return None
        best = min(
            self._node_index,
            key=lambda n: _haversine_m(lat, lon, n["lat"], n["lon"]),
        )
        return best["id"]

    # ── Private builders ──────────────────────────────────────────────────────

    async def _build_graph(self) -> None:
        """Query the DB and build the routing graph in memory."""
        async with async_session_factory() as session:
            routes = await self._load_routes(session)
            transfers = await self._load_transfers(session)

        nodes: list[TransportNode] = []
        edges: list[TransportEdge] = []

        # Build nodes + sequential jeep edges per route
        for route in routes:
            route_stops = sorted(route.route_stops, key=lambda rs: rs.sequence)
            prev_stop: JeepStop | None = None

            for route_stop in route_stops:
                stop: JeepStop = route_stop.stop

                node = TransportNode(
                    id=str(stop.id),
                    name=stop.stop_name,
                    latitude=stop.latitude,
                    longitude=stop.longitude,
                    node_type=TransportMode.JEEP,
                    route_id=str(route.id),
                )
                nodes.append(node)

                if prev_stop is not None:
                    dist = _haversine_m(
                        prev_stop.latitude, prev_stop.longitude,
                        stop.latitude, stop.longitude,
                    )
                    time_min = _travel_min(dist, TransportMode.JEEP)
                    fare = _jeep_fare(dist)

                    edges.append(TransportEdge(
                        source_id=str(prev_stop.id),
                        target_id=str(stop.id),
                        mode=TransportMode.JEEP,
                        distance_m=round(dist, 1),
                        fare=fare,
                        travel_time_min=time_min,
                        route_name=route.route_name,
                        route_color=route.route_color,
                    ))

                prev_stop = stop

        # Build transfer edges — short walking edge between stops on diff routes
        for tp in transfers:
            if not tp.from_route or not tp.to_route:
                continue

            # Find the last stop of from_route and first stop of to_route
            # as proxy boarding/alighting points for the transfer
            from_stops = sorted(
                [rs for rs in tp.from_route.route_stops],
                key=lambda rs: rs.sequence,
            )
            to_stops = sorted(
                [rs for rs in tp.to_route.route_stops],
                key=lambda rs: rs.sequence,
            )

            if not from_stops or not to_stops:
                continue

            # Use nearest stop from each route relative to the transfer point
            # We pick the last stop of from_route and first of to_route as a
            # simple heuristic — sufficient until a spatial query is added.
            from_stop = from_stops[-1].stop
            to_stop = to_stops[0].stop

            dist = _haversine_m(
                from_stop.latitude, from_stop.longitude,
                to_stop.latitude, to_stop.longitude,
            )
            time_min = _travel_min(dist, TransportMode.TRANSFER)

            edges.append(TransportEdge(
                source_id=str(from_stop.id),
                target_id=str(to_stop.id),
                mode=TransportMode.TRANSFER,
                distance_m=round(dist, 1),
                fare=0.0,
                travel_time_min=time_min,
                route_name=None,
                route_color=None,
            ))

        # Build the graph
        builder = TransportGraphBuilder()
        self._graph = builder.build(nodes, edges)

        # Build the flat node index for nearest-node lookups
        self._node_index = [
            {
                "id": n,
                "lat": self._graph.nodes[n].get("latitude", 0.0),
                "lon": self._graph.nodes[n].get("longitude", 0.0),
            }
            for n in self._graph.nodes
        ]

    @staticmethod
    async def _load_routes(session: Any) -> list[JeepRoute]:
        """Eagerly load all routes with their ordered stops."""
        stmt = (
            select(JeepRoute)
            .options(
                joinedload(JeepRoute.route_stops)
                .joinedload(JeepRouteStop.stop)
            )
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    @staticmethod
    async def _load_transfers(session: Any) -> list[TransferPoint]:
        """Eagerly load all transfer points with both route relationships."""
        stmt = (
            select(TransferPoint)
            .options(
                joinedload(TransferPoint.from_route)
                .joinedload(JeepRoute.route_stops)
                .joinedload(JeepRouteStop.stop),
                joinedload(TransferPoint.to_route)
                .joinedload(JeepRoute.route_stops)
                .joinedload(JeepRouteStop.stop),
            )
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())


# ── Module-level singleton ───────────────────────────────────────────────────
graph_service = GraphService()
