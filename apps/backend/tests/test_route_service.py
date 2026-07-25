"""Integration-style tests for per-request route assembly."""

import asyncio
from typing import Any

import networkx as nx
import pytest
from routing_engine.graph_builder import TransportGraphBuilder
from routing_engine.graph_models import TransportEdge, TransportMode, TransportNode

from app.schemas.routing import RouteRequest
from app.services.route_service import RouteService, _haversine_m


class _FakeGraphService:
    def __init__(self, graph: nx.MultiDiGraph) -> None:
        self.graph = graph
        self.node_index = [
            {
                "id": node_id,
                "lat": data["latitude"],
                "lon": data["longitude"],
            }
            for node_id, data in graph.nodes(data=True)
        ]

    @property
    def is_ready(self) -> bool:
        return self.graph.number_of_nodes() > 0

    def find_nearby_nodes(
        self,
        latitude: float,
        longitude: float,
        radius_m: float = 500.0,
    ) -> list[dict[str, Any]]:
        nearby = []
        for node in self.node_index:
            distance = _haversine_m(
                latitude,
                longitude,
                node["lat"],
                node["lon"],
            )
            if distance <= radius_m:
                nearby.append({**node, "distance_m": round(distance, 1)})
        return sorted(nearby, key=lambda node: node["distance_m"])

    def find_nearest_node(self, latitude: float, longitude: float) -> str | None:
        if not self.node_index:
            return None
        return min(
            self.node_index,
            key=lambda node: _haversine_m(
                latitude,
                longitude,
                node["lat"],
                node["lon"],
            ),
        )["id"]


class _PassthroughGeometryService:
    async def get_geometry(
        self,
        coordinates: list[list[float]],
        mode: str,
    ) -> list[list[float]]:
        await asyncio.sleep(0)
        return [coordinate.copy() for coordinate in coordinates]


def _build_graph() -> nx.MultiDiGraph:
    nodes = [
        TransportNode(
            "a",
            "Stop A",
            15.1300,
            120.5800,
            TransportMode.JEEP,
            route_id="route-1",
        ),
        TransportNode(
            "b",
            "Stop B",
            15.1400,
            120.5850,
            TransportMode.JEEP,
            route_id="route-1",
        ),
        TransportNode(
            "c",
            "Stop C",
            15.1550,
            120.5920,
            TransportMode.JEEP,
            route_id="route-1",
        ),
    ]
    edges = []
    for source, target in [("a", "b"), ("b", "a"), ("b", "c"), ("c", "b")]:
        edges.append(
            TransportEdge(
                source,
                target,
                TransportMode.JEEP,
                distance_m=1_300,
                fare=13,
                travel_time_min=5,
                route_name="Test Route",
                route_color="Blue",
            )
        )
    return TransportGraphBuilder().build(nodes, edges)


@pytest.mark.anyio
async def test_route_uses_exact_user_endpoints_without_mutating_cached_graph() -> None:
    graph = _build_graph()
    original_nodes = set(graph.nodes)
    original_edges = graph.number_of_edges()
    service = RouteService(
        _FakeGraphService(graph),  # type: ignore[arg-type]
        _PassthroughGeometryService(),  # type: ignore[arg-type]
    )
    request = RouteRequest(
        origin_lat=15.1299,
        origin_lon=120.5800,
        destination_lat=15.1551,
        destination_lon=120.5920,
    )

    result = await service.calculate_route(request)

    assert result is not None
    assert result.segments[0].waypoints[0] == [
        request.origin_lat,
        request.origin_lon,
    ]
    assert result.segments[-1].waypoints[-1] == [
        request.destination_lat,
        request.destination_lon,
    ]
    for current, following in zip(
        result.segments,
        result.segments[1:],
        strict=False,
    ):
        assert current.waypoints[-1] == following.waypoints[0]
    assert set(graph.nodes) == original_nodes
    assert graph.number_of_edges() == original_edges


@pytest.mark.anyio
async def test_concurrent_routes_cannot_overwrite_each_others_endpoints() -> None:
    graph = _build_graph()
    service = RouteService(
        _FakeGraphService(graph),  # type: ignore[arg-type]
        _PassthroughGeometryService(),  # type: ignore[arg-type]
    )
    first_request = RouteRequest(
        origin_lat=15.1299,
        origin_lon=120.5800,
        destination_lat=15.1551,
        destination_lon=120.5920,
    )
    second_request = RouteRequest(
        origin_lat=15.1551,
        origin_lon=120.5920,
        destination_lat=15.1299,
        destination_lon=120.5800,
    )

    first_result, second_result = await asyncio.gather(
        service.calculate_route(first_request),
        service.calculate_route(second_request),
    )

    assert first_result is not None
    assert second_result is not None
    assert first_result.segments[0].waypoints[0] == [
        first_request.origin_lat,
        first_request.origin_lon,
    ]
    assert first_result.segments[-1].waypoints[-1] == [
        first_request.destination_lat,
        first_request.destination_lon,
    ]
    assert second_result.segments[0].waypoints[0] == [
        second_request.origin_lat,
        second_request.origin_lon,
    ]
    assert second_result.segments[-1].waypoints[-1] == [
        second_request.destination_lat,
        second_request.destination_lon,
    ]
    assert "virtual_origin" not in graph
    assert "virtual_destination" not in graph
