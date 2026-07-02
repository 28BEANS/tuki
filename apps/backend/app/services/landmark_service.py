"""
Tuki Backend — Landmark Service

Business logic for landmark search with Google Places fallback.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.landmark import LandmarkCategory
from app.repositories.landmark_repo import LandmarkRepository
from app.schemas.landmark import LandmarkResponse

logger = logging.getLogger("tuki.services.landmark")


class LandmarkService:
    """Service for landmark search and retrieval."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = LandmarkRepository(session)

    async def search_landmarks(
        self,
        query: str | None = None,
        category: LandmarkCategory | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LandmarkResponse], int]:
        """Search landmarks with optional text query and category filter."""
        items, total = await self.repo.search(
            query=query, category=category, page=page, page_size=page_size
        )

        responses = [
            LandmarkResponse(
                id=item.id,
                name=item.name,
                aliases=item.aliases,
                category=item.category,
                latitude=item.latitude,
                longitude=item.longitude,
                barangay_name=item.barangay.barangay_name if item.barangay else None,
            )
            for item in items
        ]

        return responses, total

    async def get_nearby_landmarks(
        self,
        lat: float,
        lon: float,
        radius_m: float = 1000,
        limit: int = 20,
    ) -> list[LandmarkResponse]:
        """Find landmarks near a point."""
        items = await self.repo.get_nearby(lat, lon, radius_m, limit)

        return [
            LandmarkResponse(
                id=item.id,
                name=item.name,
                aliases=item.aliases,
                category=item.category,
                latitude=item.latitude,
                longitude=item.longitude,
                barangay_name=item.barangay.barangay_name if item.barangay else None,
            )
            for item in items
        ]
