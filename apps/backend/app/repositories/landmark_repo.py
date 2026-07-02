"""
Tuki Backend — Landmark Repository

Searchable landmarks with spatial proximity queries.
"""

from geoalchemy2.functions import (
    ST_Distance,
    ST_DWithin,
    ST_MakePoint,
    ST_SetSRID,
    ST_Transform,
)
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from app.models.landmark import Landmark, LandmarkCategory
from app.repositories.base import BaseRepository


class LandmarkRepository(BaseRepository[Landmark]):
    """Repository for landmark queries including spatial search."""

    model = Landmark

    async def search(
        self,
        query: str | None = None,
        category: LandmarkCategory | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Landmark], int]:
        """Search landmarks by name/alias and optional category filter."""
        stmt = select(Landmark).options(joinedload(Landmark.barangay))

        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Landmark.name.ilike(search_pattern),
                    Landmark.aliases.any(query),
                )
            )

        if category:
            stmt = stmt.where(Landmark.category == category)

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().unique().all())

        return items, total

    async def get_nearby(
        self,
        lat: float,
        lon: float,
        radius_m: float = 1000,
        limit: int = 20,
    ) -> list[Landmark]:
        """Find landmarks within a radius (meters) of a point."""
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)

        stmt = (
            select(Landmark)
            .options(joinedload(Landmark.barangay))
            .where(
                ST_DWithin(
                    ST_Transform(Landmark.geometry, 3857),
                    ST_Transform(point, 3857),
                    radius_m,
                )
            )
            .order_by(ST_Distance(Landmark.geometry, point))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
