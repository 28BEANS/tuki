"""
Tuki Backend — Jeepney Route Model

Stores route metadata for Angeles City's color-coded jeepney routes.
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class JeepRoute(Base, TimestampMixin):
    """
    A jeepney route in Angeles City.

    Each route has a color code and a line geometry representing its path.
    Routes are linked to stops via the jeep_route_stops association table.
    """

    __tablename__ = "jeep_routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    route_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    route_color: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    operating_direction: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Relationships
    route_stops = relationship(
        "JeepRouteStop", back_populates="route", lazy="selectin",
        order_by="JeepRouteStop.sequence",
    )

    def __repr__(self) -> str:
        return f"<JeepRoute(name={self.route_name!r}, color={self.route_color!r})>"
