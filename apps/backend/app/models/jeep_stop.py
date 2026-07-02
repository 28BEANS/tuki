"""
Tuki Backend — Jeepney Stop Model

Stores boarding/alighting locations for jeepney routes.
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class JeepStop(Base, TimestampMixin):
    """A boarding or alighting point along a jeepney route."""

    __tablename__ = "jeep_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stop_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Relationships
    route_stops = relationship("JeepRouteStop", back_populates="stop", lazy="selectin")

    def __repr__(self) -> str:
        return f"<JeepStop(name={self.stop_name!r})>"
