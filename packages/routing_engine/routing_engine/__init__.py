"""
Tuki Routing Engine

Standalone multimodal routing package for Angeles City.
Independent of FastAPI — can be used in background jobs, CLI tools, or offline processing.

Usage:
    from routing_engine import TransportGraphBuilder, find_route

    builder = TransportGraphBuilder()
    graph = builder.build(nodes, edges)
    result = find_route(graph, origin, destination)
"""

from routing_engine.graph_builder import TransportGraphBuilder
from routing_engine.graph_models import (
    RouteResult,
    RouteSegment,
    TransportEdge,
    TransportMode,
    TransportNode,
)
from routing_engine.pathfinding import find_route

__all__ = [
    "TransportGraphBuilder",
    "TransportNode",
    "TransportEdge",
    "TransportMode",
    "RouteSegment",
    "RouteResult",
    "find_route",
]

__version__ = "0.1.0"
