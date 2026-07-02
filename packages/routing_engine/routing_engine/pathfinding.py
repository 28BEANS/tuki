"""
Tuki Routing Engine — Pathfinding

Implements shortest path algorithms on the transportation graph.
"""

import logging
from typing import Literal

import networkx as nx

from routing_engine.graph_models import RouteResult, RouteSegment, TransportMode

logger = logging.getLogger("tuki.routing.pathfinding")

WeightStrategy = Literal["fastest", "cheapest", "fewest_transfers"]


def find_route(
    graph: nx.MultiDiGraph,
    origin_id: str,
    destination_id: str,
    strategy: WeightStrategy = "fastest",
) -> RouteResult | None:
    """
    Find the optimal route between two nodes.

    Args:
        graph: The transportation MultiDiGraph.
        origin_id: Source node ID.
        destination_id: Target node ID.
        strategy: Optimization strategy.

    Returns:
        RouteResult with segments, or None if no path exists.
    """
    weight_key = _get_weight_key(strategy)

    try:
        # Find shortest path using Dijkstra
        path = nx.dijkstra_path(graph, origin_id, destination_id, weight=weight_key)
    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        logger.warning("No route found: %s → %s (%s)", origin_id, destination_id, e)
        return None

    if len(path) < 2:
        return RouteResult()

    # Build segments from path
    return _build_route_result(graph, path)


def find_alternative_routes(
    graph: nx.MultiDiGraph,
    origin_id: str,
    destination_id: str,
    k: int = 3,
    strategy: WeightStrategy = "fastest",
) -> list[RouteResult]:
    """
    Find up to k alternative routes.

    Uses Yen's K-shortest paths algorithm.
    """
    weight_key = _get_weight_key(strategy)
    results: list[RouteResult] = []

    try:
        paths = list(
            nx.shortest_simple_paths(graph, origin_id, destination_id, weight=weight_key)
        )
        for path in paths[:k]:
            result = _build_route_result(graph, path)
            if result:
                results.append(result)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass

    return results


def _get_weight_key(strategy: WeightStrategy) -> str:
    """Map strategy to edge weight attribute name."""
    return {
        "fastest": "weight_time",
        "cheapest": "weight_fare",
        "fewest_transfers": "weight_time",  # Use time but prefer fewer transfers
    }[strategy]


def _build_route_result(graph: nx.MultiDiGraph, path: list[str]) -> RouteResult:
    """Build a RouteResult from a node path."""
    result = RouteResult()
    current_segment: RouteSegment | None = None

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]

        # Get the best edge between u and v
        edge_data = _get_best_edge(graph, u, v)
        mode = TransportMode(edge_data.get("mode", "walk"))

        # Check if we should continue the current segment or start a new one
        if current_segment and _should_merge(current_segment, mode, edge_data):
            # Continue current segment
            current_segment.distance_m += edge_data.get("distance_m", 0)
            current_segment.duration_min += edge_data.get("travel_time_min", 0)
            current_segment.fare += edge_data.get("fare", 0)
            current_segment.alight_at = graph.nodes[v].get("name", v)
            current_segment.nodes.append(v)
        else:
            # Save current segment and start a new one
            if current_segment:
                result.add_segment(current_segment)

            current_segment = RouteSegment(
                mode=mode,
                route_name=edge_data.get("route_name"),
                route_color=edge_data.get("route_color"),
                board_at=graph.nodes[u].get("name", u),
                alight_at=graph.nodes[v].get("name", v),
                distance_m=edge_data.get("distance_m", 0),
                duration_min=edge_data.get("travel_time_min", 0),
                fare=edge_data.get("fare", 0),
                nodes=[u, v],
            )

    # Don't forget the last segment
    if current_segment:
        result.add_segment(current_segment)

    return result


def _get_best_edge(graph: nx.MultiDiGraph, u: str, v: str) -> dict:
    """Get the edge with lowest weight_time between two nodes."""
    edges = graph[u][v]
    best = min(edges.values(), key=lambda e: e.get("weight_time", float("inf")))
    return dict(best)


def _should_merge(
    segment: RouteSegment,
    mode: TransportMode,
    edge_data: dict,
) -> bool:
    """Determine if an edge should be merged into the current segment."""
    if segment.mode != mode:
        return False
    if mode == TransportMode.JEEP:
        return segment.route_name == edge_data.get("route_name")
    return mode == TransportMode.WALK
