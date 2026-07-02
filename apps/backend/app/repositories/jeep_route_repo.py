"""
Tuki Backend — Jeep Route Repository

Queries for jeepney routes with related stops.
"""

from uuid import UUID

from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_Transform
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.jeep_route import JeepRoute
from app.models.jeep_route_stop import JeepRouteStop
from app.repositories.base import BaseRepository


class JeepRouteRepository(BaseRepository[JeepRoute]):
    """Repository for jeepney route operations."""

    model = JeepRoute

    async def get_with_stops(self, route_id: UUID) -> JeepRoute | None:
        """Get a route with its ordered stops."""
        stmt = (
            select(JeepRoute)
            .options(
                joinedload(JeepRoute.route_stops).joinedload(JeepRouteStop.stop)
            )
            .where(JeepRoute.id == route_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_routes_near(
        self, lat: float, lon: float, radius_m: float = 500
    ) -> list[JeepRoute]:
        """Find routes whose geometry passes near a point."""
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        stmt = (
            select(JeepRoute)
            .where(
                ST_DWithin(
                    ST_Transform(JeepRoute.geometry, 3857),
                    ST_Transform(point, 3857),
                    radius_m,
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_color(self, color: str) -> JeepRoute | None:
        """Get a route by its color code."""
        stmt = select(JeepRoute).where(JeepRoute.route_color.ilike(color))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
