"""
Tuki Backend — Jeep Stop Repository
"""

from geoalchemy2.functions import ST_Distance, ST_MakePoint, ST_SetSRID
from sqlalchemy import select

from app.models.jeep_stop import JeepStop
from app.repositories.base import BaseRepository


class JeepStopRepository(BaseRepository[JeepStop]):
    """Repository for jeep stop operations."""

    model = JeepStop

    async def find_nearest(
        self, lat: float, lon: float, limit: int = 5
    ) -> list[JeepStop]:
        """Find nearest jeep stops to a point."""
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        stmt = (
            select(JeepStop)
            .order_by(ST_Distance(JeepStop.geometry, point))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
