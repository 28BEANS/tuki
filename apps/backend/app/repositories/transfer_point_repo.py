"""
Tuki Backend — Transfer Point Repository
"""

from uuid import UUID

from sqlalchemy import select

from app.models.transfer_point import TransferPoint
from app.repositories.base import BaseRepository


class TransferPointRepository(BaseRepository[TransferPoint]):
    """Repository for transfer point operations."""

    model = TransferPoint

    async def get_between_routes(
        self, from_route_id: UUID, to_route_id: UUID
    ) -> list[TransferPoint]:
        """Find transfer points between two specific routes."""
        stmt = select(TransferPoint).where(
            TransferPoint.from_route_id == from_route_id,
            TransferPoint.to_route_id == to_route_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
