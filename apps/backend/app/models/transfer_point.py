"""
Tuki Backend — Transfer Point Model

Stores valid transfer locations between transport modes.
"""

import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class TransferType(str, enum.Enum):
    """Types of transfers between transport modes."""

    JEEP_JEEP = "jeep_jeep"
    JEEP_WALK = "jeep_walk"
    WALK_TRICYCLE = "walk_tricycle"
    JEEP_TRICYCLE = "jeep_tricycle"
    WALK_JEEP = "walk_jeep"
    TRICYCLE_WALK = "tricycle_walk"


class TransferPoint(Base, TimestampMixin):
    """
    A location where commuters can transfer between routes or modes.

    Links two routes with a transfer type (e.g., Jeep→Jeep, Jeep→Walk).
    """

    __tablename__ = "transfer_points"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    from_route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jeep_routes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    to_route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jeep_routes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transfer_type: Mapped[TransferType] = mapped_column(
        Enum(
            TransferType,
            name="transfer_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )

    # Relationships
    from_route = relationship("JeepRoute", foreign_keys=[from_route_id], lazy="selectin")
    to_route = relationship("JeepRoute", foreign_keys=[to_route_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<TransferPoint(type={self.transfer_type.value}, name={self.name!r})>"
