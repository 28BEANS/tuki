"""
Tuki Backend — Fare Matrix Repository
"""

from sqlalchemy import select

from app.models.fare_matrix import FareMatrix
from app.repositories.base import BaseRepository


class FareMatrixRepository(BaseRepository[FareMatrix]):
    """Repository for fare matrix queries."""

    model = FareMatrix

    async def get_fare(
        self, transport_type: str, distance_km: float
    ) -> FareMatrix | None:
        """Find the fare bracket for a given transport type and distance."""
        stmt = (
            select(FareMatrix)
            .where(
                FareMatrix.transport_type == transport_type,
                FareMatrix.distance_km <= distance_km,
            )
            .order_by(FareMatrix.distance_km.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_type(self, transport_type: str) -> list[FareMatrix]:
        """Get all fare entries for a transport type, ordered by distance."""
        stmt = (
            select(FareMatrix)
            .where(FareMatrix.transport_type == transport_type)
            .order_by(FareMatrix.distance_km)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
