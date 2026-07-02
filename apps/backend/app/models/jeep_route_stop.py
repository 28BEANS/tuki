"""
Tuki Backend — Jeepney Route-Stop Association Model

Links jeep routes to their stops with ordering.
"""

import uuid

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JeepRouteStop(Base):
    """
    Association table linking jeep routes to stops.

    The 'sequence' field determines the order of stops along a route.
    """

    __tablename__ = "jeep_route_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    jeep_route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jeep_routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jeep_stops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    # Relationships
    route = relationship("JeepRoute", back_populates="route_stops")
    stop = relationship("JeepStop", back_populates="route_stops")

    def __repr__(self) -> str:
        return f"<JeepRouteStop(route={self.jeep_route_id}, stop={self.stop_id}, seq={self.sequence})>"
