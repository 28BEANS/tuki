"""
Tuki Backend — Jeep Routes, Stops & Transfer Points Endpoints
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundError
from app.dependencies.database import DBSession
from app.repositories.jeep_route_repo import JeepRouteRepository
from app.repositories.jeep_stop_repo import JeepStopRepository
from app.repositories.transfer_point_repo import TransferPointRepository
from app.schemas.common import PaginatedResponse
from app.schemas.jeep_route import JeepRouteDetail, JeepRouteResponse
from app.schemas.jeep_stop import JeepStopResponse
from app.schemas.transfer_point import TransferPointResponse

router = APIRouter()


@router.get("/routes", response_model=PaginatedResponse[JeepRouteResponse])
async def list_routes(
    session: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[JeepRouteResponse]:
    """List all jeepney routes."""
    repo = JeepRouteRepository(session)
    items, total = await repo.get_all(page=page, page_size=page_size)

    return PaginatedResponse(
        items=[JeepRouteResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/routes/{route_id}", response_model=JeepRouteDetail)
async def get_route(route_id: UUID, session: DBSession) -> JeepRouteDetail:
    """Get a jeepney route with its ordered stops."""
    repo = JeepRouteRepository(session)
    route = await repo.get_with_stops(route_id)

    if not route:
        raise NotFoundError("Jeep Route", route_id)

    stops = [
        JeepStopResponse(
            id=rs.stop.id,
            stop_name=rs.stop.stop_name,
            latitude=rs.stop.latitude,
            longitude=rs.stop.longitude,
            sequence=rs.sequence,
        )
        for rs in route.route_stops
    ]

    return JeepRouteDetail(
        id=route.id,
        route_name=route.route_name,
        route_color=route.route_color,
        description=route.description,
        operating_direction=route.operating_direction,
        stops=stops,
    )


@router.get("/jeep-routes", response_model=list[JeepRouteResponse])
async def list_jeep_routes(session: DBSession) -> list[JeepRouteResponse]:
    """List all jeep routes (alias for /routes)."""
    repo = JeepRouteRepository(session)
    items, _ = await repo.get_all(page=1, page_size=100)
    return [JeepRouteResponse.model_validate(item) for item in items]


@router.get("/jeep-stops", response_model=list[JeepStopResponse])
async def list_jeep_stops(session: DBSession) -> list[JeepStopResponse]:
    """List all jeep stops."""
    repo = JeepStopRepository(session)
    items, _ = await repo.get_all(page=1, page_size=500)
    return [JeepStopResponse.model_validate(item) for item in items]


@router.get("/transfer-points", response_model=list[TransferPointResponse])
async def list_transfer_points(session: DBSession) -> list[TransferPointResponse]:
    """List all transfer points."""
    repo = TransferPointRepository(session)
    items, _ = await repo.get_all(page=1, page_size=500)

    return [
        TransferPointResponse(
            id=item.id,
            name=item.name,
            transfer_type=item.transfer_type,
            from_route_name=item.from_route.route_name if item.from_route else None,
            to_route_name=item.to_route.route_name if item.to_route else None,
        )
        for item in items
    ]
