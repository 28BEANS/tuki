"""
Tuki Backend — Routing Endpoint
"""

from fastapi import APIRouter

from app.schemas.routing import RouteRequest, RouteResponse
from app.services.graph_service import graph_service
from app.services.route_service import RouteService

router = APIRouter()


@router.post("/calculate-route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest) -> RouteResponse:
    """
    Calculate a multimodal route.

    Uses the in-memory transport graph built at startup.
    Falls back to mock data if the graph is not available.
    """
    service = RouteService(graph_service)
    return await service.calculate_route(request)


@router.post("/graph/refresh")
async def refresh_graph() -> dict:
    """
    Refresh the in-memory transport graph from the current database state.

    Useful after a data import without restarting the server.
    """
    await graph_service.refresh()
    return {
        "status": "ok",
        "nodes": graph_service.graph.number_of_nodes() if graph_service.graph else 0,
        "edges": graph_service.graph.number_of_edges() if graph_service.graph else 0,
    }
