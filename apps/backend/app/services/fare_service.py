"""
Tuki Backend — Fare Service

Fare calculation using the national fare matrix.
"""

import logging
import math

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.fare_matrix_repo import FareMatrixRepository
from app.schemas.fare import FareCalculationRequest, FareCalculationResponse

logger = logging.getLogger("tuki.services.fare")

# Average walking speed in km/h
WALKING_SPEED_KMH = 4.5
# Earth radius in km for Haversine
EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


class FareService:
    """Service for fare calculation using the national fare matrix."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = FareMatrixRepository(session)

    async def calculate_fare(
        self, request: FareCalculationRequest
    ) -> FareCalculationResponse:
        """
        Calculate fare based on straight-line distance.

        In production, this will use the actual route distance from the routing engine.
        """
        distance_km = haversine_distance(
            request.origin_lat, request.origin_lon,
            request.destination_lat, request.destination_lon,
        )

        # Look up fare from matrix
        fare_entry = await self.repo.get_fare("traditional_puj", distance_km)

        if fare_entry:
            if request.is_student:
                fare = fare_entry.student_fare
                fare_type = "student"
            elif request.is_discounted:
                fare = fare_entry.discounted_fare
                fare_type = "discounted"
            else:
                fare = fare_entry.regular_fare
                fare_type = "regular"
        else:
            # Fallback: minimum fare
            fare = 13.0
            fare_type = "regular"

        return FareCalculationResponse(
            total_fare=fare,
            distance_km=round(distance_km, 2),
            fare_type=fare_type,
            breakdown=[
                {
                    "mode": "jeep",
                    "distance_km": round(distance_km, 2),
                    "fare": fare,
                }
            ],
        )
