"""
Tuki Backend — Fare Matrix Model

Stores the national jeepney fare matrix (distance-based fare brackets).
"""

import uuid

from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class FareMatrix(Base, TimestampMixin):
    """
    Distance-based fare bracket from the national fare matrix.

    Each row defines fare for a distance range and transport type.
    Source: LTFRB Fare Guide for Traditional PUJ (Oct 2023).
    """

    __tablename__ = "fare_matrix"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transport_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    distance_km: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    regular_fare: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    discounted_fare: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    student_fare: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<FareMatrix(type={self.transport_type!r}, "
            f"dist={self.distance_km}km, fare=₱{self.regular_fare})>"
        )
