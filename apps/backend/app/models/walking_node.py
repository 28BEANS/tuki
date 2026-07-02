"""
Tuki Backend — Walking Node Model

Stores OSM walking network nodes imported via OSMnx.
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WalkingNode(Base):
    """
    A node in the walking network, imported from OpenStreetMap.

    Each node represents an intersection or waypoint in the pedestrian network.
    """

    __tablename__ = "walking_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    osm_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    geometry: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<WalkingNode(osm_id={self.osm_id})>"
