"""
Tuki Backend — Tricycle Terminal Model

Stores tricycle terminal locations and service areas.
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class TricycleTerminal(Base, TimestampMixin):
    """
    A tricycle terminal with a point location and polygon service area.

    Tricycles operate within defined service areas around their terminals.
    """

    __tablename__ = "tricycle_terminals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    service_area: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<TricycleTerminal(name={self.name!r})>"
