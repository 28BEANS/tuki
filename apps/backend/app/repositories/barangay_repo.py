"""
Tuki Backend — Barangay Repository

Spatial queries for barangay boundaries.
"""

from geoalchemy2.functions import ST_Contains, ST_SetSRID, ST_MakePoint
from sqlalchemy import select

from app.models.barangay import Barangay
from app.repositories.base import BaseRepository


class BarangayRepository(BaseRepository[Barangay]):
    """Repository for barangay boundary operations."""

    model = Barangay

    async def find_containing_point(self, lat: float, lon: float) -> Barangay | None:
        """Find the barangay that contains a given point."""
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        query = select(Barangay).where(
            ST_Contains(Barangay.geometry, point)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Barangay | None:
        """Find a barangay by name (case-insensitive)."""
        query = select(Barangay).where(
            Barangay.barangay_name.ilike(name)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
