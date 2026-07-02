"""
Tuki Backend — Landmark Model

Stores searchable destinations: schools, malls, hospitals, terminals, etc.
"""

import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class LandmarkCategory(str, enum.Enum):
    """Categories for landmark classification."""

    SCHOOL = "school"
    MALL = "mall"
    HOSPITAL = "hospital"
    GOVERNMENT = "government"
    CHURCH = "church"
    TERMINAL = "terminal"
    MARKET = "market"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    PARK = "park"
    BANK = "bank"
    GAS_STATION = "gas_station"
    OTHER = "other"


class Landmark(Base, TimestampMixin):
    """Searchable point of interest within Angeles City."""

    __tablename__ = "landmarks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    aliases: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    category: Mapped[LandmarkCategory] = mapped_column(
        Enum(LandmarkCategory, name="landmark_category"),
        nullable=False,
        index=True,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    barangay_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("barangays.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    barangay = relationship("Barangay", back_populates="landmarks", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Landmark(name={self.name!r}, category={self.category.value})>"
