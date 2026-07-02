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
