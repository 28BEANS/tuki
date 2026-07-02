"""
Tuki Backend — Routing Endpoint
"""

from fastapi import APIRouter

from app.schemas.routing import RouteRequest, RouteResponse
from app.services.route_service import RouteService

router = APIRouter()


@router.post("/calculate-route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest) -> RouteResponse:
    """
    Calculate a multimodal route.

    Currently returns mocked data using the correct response schema.
    Will integrate with the routing engine once transport graph is built.
    """
    service = RouteService()
    return await service.calculate_route(request)
