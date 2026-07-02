"""
Tuki Backend — Landmarks Endpoints
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.database import DBSession
from app.models.landmark import LandmarkCategory
from app.schemas.common import PaginatedResponse
from app.schemas.landmark import LandmarkResponse
from app.services.landmark_service import LandmarkService

router = APIRouter(prefix="/landmarks")


@router.get("", response_model=PaginatedResponse[LandmarkResponse])
async def list_landmarks(
    session: DBSession,
    q: str | None = Query(None, description="Search query"),
    category: LandmarkCategory | None = Query(None, description="Filter by category"),
    latitude: float | None = Query(None, description="Latitude for proximity search"),
    longitude: float | None = Query(None, description="Longitude for proximity search"),
    radius_m: float = Query(1000, ge=100, le=10000, description="Search radius in meters"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[LandmarkResponse]:
    """
    Search and list landmarks.

    Supports text search, category filter, and proximity-based search.
    """
    service = LandmarkService(session)

    if latitude is not None and longitude is not None:
        items = await service.get_nearby_landmarks(
            lat=latitude, lon=longitude, radius_m=radius_m, limit=page_size
        )
        return PaginatedResponse(
            items=items,
            total=len(items),
            page=1,
            page_size=page_size,
            has_next=False,
        )

    items, total = await service.search_landmarks(
        query=q, category=category, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/{landmark_id}", response_model=LandmarkResponse)
async def get_landmark(
    landmark_id: UUID,
    session: DBSession,
) -> LandmarkResponse:
    """Get a landmark by ID."""
    from app.core.exceptions import NotFoundError
    from app.repositories.landmark_repo import LandmarkRepository

    repo = LandmarkRepository(session)
    landmark = await repo.get_by_id(landmark_id)
    if not landmark:
        raise NotFoundError("Landmark", landmark_id)

    return LandmarkResponse(
        id=landmark.id,
        name=landmark.name,
        aliases=landmark.aliases,
        category=landmark.category,
        latitude=landmark.latitude,
        longitude=landmark.longitude,
        barangay_name=landmark.barangay.barangay_name if landmark.barangay else None,
    )
