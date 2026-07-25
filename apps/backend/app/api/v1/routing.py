"""
Tuki Backend — Routing Endpoint
"""

from fastapi import APIRouter, HTTPException

from app.schemas.routing import RouteRequest, RouteResponse
from app.services.graph_service import graph_service
from app.services.route_service import RouteService

router = APIRouter()


@router.post("/calculate-route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest) -> RouteResponse:
    """
    Calculate a multimodal route.

    Uses the in-memory transport graph built at startup.
    Returns HTTP 503 if the graph is unavailable, or HTTP 404 if no
    route exists between the given origin and destination.
    """
    service = RouteService(graph_service)

    try:
        result = await service.calculate_route(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No route found between the selected locations.",
        )

    return result


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
