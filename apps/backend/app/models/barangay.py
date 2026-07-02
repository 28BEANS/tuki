"""
Tuki Backend — Barangay Model

Stores Angeles City barangay boundaries imported from GeoJSON.
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Barangay(Base, TimestampMixin):
    """Barangay boundary polygon imported from PSGC GeoJSON."""

    __tablename__ = "barangays"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    barangay_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    psgc_code: Mapped[str | None] = mapped_column(
        String(20), nullable=True, unique=True
    )
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Relationships
    landmarks = relationship("Landmark", back_populates="barangay", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Barangay(name={self.barangay_name!r})>"
