"""
Tuki Routing Engine — Unit Tests
"""

import pytest
import networkx as nx

from routing_engine.graph_models import (
    TransportEdge,
    TransportMode,
    TransportNode,
    RouteResult,
    RouteSegment,
)
from routing_engine.graph_builder import TransportGraphBuilder
from routing_engine.pathfinding import find_route
from routing_engine.fare_engine import FareEngine
from routing_engine.eta_engine import ETAEngine


class TestGraphModels:
    """Tests for graph model dataclasses."""

    def test_transport_node(self):
        node = TransportNode(
            id="stop_1", name="HAU", latitude=15.1285,
            longitude=120.5970, node_type=TransportMode.JEEP,
        )
        assert node.coords == (15.1285, 120.5970)

    def test_transport_edge_weights(self):
        edge = TransportEdge(
            source_id="a", target_id="b",
            mode=TransportMode.JEEP,
            distance_m=3000, fare=13.0, travel_time_min=12.0,
        )
        assert edge.weight_time == 12.0
        assert edge.weight_fare == 13.0
        assert edge.weight_transfers == 0.0

    def test_transfer_edge_penalty(self):
        edge = TransportEdge(
            source_id="a", target_id="b",
            mode=TransportMode.TRANSFER,
            distance_m=50, fare=0, travel_time_min=1.0,
        )
        assert edge.weight_transfers == 1.0

    def test_route_result_add_segment(self):
        result = RouteResult()
        result.add_segment(RouteSegment(
            mode=TransportMode.JEEP, distance_m=3000,
            duration_min=12, fare=13,
        ))
        result.add_segment(RouteSegment(
            mode=TransportMode.WALK, distance_m=200,
            duration_min=3, fare=0,
        ))
        assert result.total_fare == 13
        assert result.total_distance_m == 3200
        assert result.total_time_min == 15


class TestGraphBuilder:
    """Tests for graph construction."""

    def test_build_simple_graph(self):
        builder = TransportGraphBuilder()
        nodes = [
            TransportNode("a", "Stop A", 15.14, 120.58, TransportMode.JEEP),
            TransportNode("b", "Stop B", 15.15, 120.59, TransportMode.JEEP),
        ]
        edges = [
            TransportEdge("a", "b", TransportMode.JEEP, 2000, 13.0, 8.0),
        ]
        graph = builder.build(nodes, edges)

        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1
        assert graph.has_edge("a", "b")

    def test_empty_graph(self):
        builder = TransportGraphBuilder()
        graph = builder.build([], [])
        assert graph.number_of_nodes() == 0


class TestPathfinding:
    """Tests for route finding."""

    def test_find_direct_route(self):
        builder = TransportGraphBuilder()
        nodes = [
            TransportNode("a", "Origin", 15.14, 120.58, TransportMode.JEEP),
            TransportNode("b", "Middle", 15.145, 120.585, TransportMode.JEEP),
            TransportNode("c", "Dest", 15.15, 120.59, TransportMode.JEEP),
        ]
        edges = [
            TransportEdge("a", "b", TransportMode.JEEP, 1000, 0, 5.0,
                          route_name="Yellow", route_color="Yellow"),
            TransportEdge("b", "c", TransportMode.JEEP, 1000, 0, 5.0,
                          route_name="Yellow", route_color="Yellow"),
        ]
        graph = builder.build(nodes, edges)
        result = find_route(graph, "a", "c", "fastest")

        assert result is not None
        assert len(result.segments) >= 1

    def test_no_route_found(self):
        builder = TransportGraphBuilder()
        nodes = [
            TransportNode("a", "A", 15.14, 120.58, TransportMode.JEEP),
            TransportNode("b", "B", 15.15, 120.59, TransportMode.JEEP),
        ]
        graph = builder.build(nodes, [])  # No edges
        result = find_route(graph, "a", "b")

        assert result is None


class TestFareEngine:
    """Tests for fare calculation."""

    def test_jeep_base_fare(self):
        engine = FareEngine()
        segment = RouteSegment(
            mode=TransportMode.JEEP, distance_m=3000,
        )
        fare = engine.calculate_segment_fare(segment)
        assert fare == 13.0  # Base fare for <= 4km

    def test_walking_is_free(self):
        engine = FareEngine()
        segment = RouteSegment(mode=TransportMode.WALK, distance_m=500)
        fare = engine.calculate_segment_fare(segment)
        assert fare == 0.0

    def test_student_discount(self):
        engine = FareEngine()
        segment = RouteSegment(mode=TransportMode.JEEP, distance_m=3000)
        fare = engine.calculate_segment_fare(segment, is_student=True)
        assert fare < 13.0  # Should be discounted


class TestETAEngine:
    """Tests for travel time estimation."""

    def test_walking_eta(self):
        engine = ETAEngine()
        segment = RouteSegment(mode=TransportMode.WALK, distance_m=450)
        time = engine.estimate_segment_time(segment)
        assert time > 0  # Should have some duration

    def test_jeep_includes_wait(self):
        engine = ETAEngine()
        segment = RouteSegment(mode=TransportMode.JEEP, distance_m=3000)
        time = engine.estimate_segment_time(segment)
        # Should include 5 min wait + travel time
        assert time > 5.0


class TestRouteCorrectness:
    """Tests that verify route endpoint correctness and ordering."""

    @staticmethod
    def _make_graph():
        """Build a small test graph with known coordinates."""
        builder = TransportGraphBuilder()
        nodes = [
            TransportNode("origin", "Origin Stop", 15.1380, 120.5910, TransportMode.JEEP, route_id="r1"),
            TransportNode("mid1", "Mid Stop 1", 15.1400, 120.5920, TransportMode.JEEP, route_id="r1"),
            TransportNode("mid2", "Mid Stop 2", 15.1450, 120.5880, TransportMode.JEEP, route_id="r1"),
            TransportNode("dest", "Dest Stop", 15.1510, 120.5850, TransportMode.JEEP, route_id="r1"),
        ]
        edges = [
            TransportEdge("origin", "mid1", TransportMode.JEEP, 500, 0, 3.0,
                          route_name="Yellow", route_color="Yellow"),
            TransportEdge("mid1", "mid2", TransportMode.JEEP, 800, 0, 4.0,
                          route_name="Yellow", route_color="Yellow"),
            TransportEdge("mid2", "dest", TransportMode.JEEP, 600, 0, 3.5,
                          route_name="Yellow", route_color="Yellow"),
        ]
        return builder.build(nodes, edges)

    def test_route_starts_at_origin(self):
        """First node in the route path must be the origin node."""
        graph = self._make_graph()
        result = find_route(graph, "origin", "dest", "fastest")

        assert result is not None
        assert len(result.segments) >= 1
        first_segment = result.segments[0]
        assert first_segment.nodes[0] == "origin"

    def test_route_ends_at_destination(self):
        """Last node in the route path must be the destination node."""
        graph = self._make_graph()
        result = find_route(graph, "origin", "dest", "fastest")

        assert result is not None
        last_segment = result.segments[-1]
        assert last_segment.nodes[-1] == "dest"

    def test_origin_and_destination_not_swapped(self):
        """The first segment must board at the origin, not the destination."""
        graph = self._make_graph()
        result = find_route(graph, "origin", "dest", "fastest")

        assert result is not None
        first_segment = result.segments[0]
        # board_at should be the origin stop's name, not the destination's
        assert first_segment.board_at == "Origin Stop"
        last_segment = result.segments[-1]
        assert last_segment.alight_at == "Dest Stop"

    def test_lat_lon_ordering_preserved(self):
        """Node coords property returns (lat, lon) — not reversed."""
        node = TransportNode(
            id="test", name="Test", latitude=15.1380,
            longitude=120.5910, node_type=TransportMode.JEEP,
        )
        lat, lon = node.coords
        assert lat == 15.1380
        assert lon == 120.5910
        # Latitude for Angeles City is around 15, longitude around 120
        assert 14.0 < lat < 16.0, "Latitude should be ~15 for Angeles City"
        assert 119.0 < lon < 122.0, "Longitude should be ~120 for Angeles City"

    def test_no_stale_reuse_between_different_inputs(self):
        """Running pathfinding twice with different endpoints produces different results."""
        graph = self._make_graph()

        result_1 = find_route(graph, "origin", "mid2", "fastest")
        result_2 = find_route(graph, "origin", "dest", "fastest")

        assert result_1 is not None
        assert result_2 is not None

        # Route 1 should end at mid2, route 2 at dest
        last_1 = result_1.segments[-1].nodes[-1]
        last_2 = result_2.segments[-1].nodes[-1]
        assert last_1 == "mid2"
        assert last_2 == "dest"
        assert last_1 != last_2, "Different destinations must produce different routes"

    def test_unreachable_destination_returns_none(self):
        """Disconnected graph returns None, not an incorrect route."""
        builder = TransportGraphBuilder()
        nodes = [
            TransportNode("a", "A", 15.14, 120.58, TransportMode.JEEP),
            TransportNode("b", "B", 15.20, 120.60, TransportMode.JEEP),
        ]
        graph = builder.build(nodes, [])  # No edges — unreachable
        result = find_route(graph, "a", "b")

        assert result is None, "Unreachable destination must return None, not a fake route"

    def test_reversed_origin_dest_gives_reversed_path(self):
        """Swapping origin and destination reverses the path direction."""
        builder = TransportGraphBuilder()
        nodes = [
            TransportNode("a", "Stop A", 15.14, 120.58, TransportMode.JEEP, route_id="r1"),
            TransportNode("b", "Stop B", 15.15, 120.59, TransportMode.JEEP, route_id="r1"),
        ]
        edges = [
            TransportEdge("a", "b", TransportMode.JEEP, 1000, 0, 5.0,
                          route_name="Test", route_color="Blue"),
            TransportEdge("b", "a", TransportMode.JEEP, 1000, 0, 5.0,
                          route_name="Test", route_color="Blue"),
        ]
        graph = builder.build(nodes, edges)

        fwd = find_route(graph, "a", "b")
        rev = find_route(graph, "b", "a")

        assert fwd is not None and rev is not None
        assert fwd.segments[0].nodes[0] == "a"
        assert fwd.segments[-1].nodes[-1] == "b"
        assert rev.segments[0].nodes[0] == "b"
        assert rev.segments[-1].nodes[-1] == "a"

