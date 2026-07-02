"""
Tuki Backend — Walking Edge Model

Stores OSM walking network edges imported via OSMnx.
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WalkingEdge(Base):
    """
    An edge in the walking network, imported from OpenStreetMap.

    Each edge connects two walking nodes and represents a street segment.
    """

    __tablename__ = "walking_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("walking_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("walking_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=False,
    )
    length_m: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    highway_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Relationships
    source_node = relationship("WalkingNode", foreign_keys=[source_node_id], lazy="selectin")
    target_node = relationship("WalkingNode", foreign_keys=[target_node_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<WalkingEdge(src={self.source_node_id}, tgt={self.target_node_id}, len={self.length_m}m)>"
