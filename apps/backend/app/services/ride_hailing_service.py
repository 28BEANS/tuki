"""
Tuki Backend — Ride-Hailing Comparison Service

Mocked Grab & Maxim fare estimation.
Will integrate with actual APIs when available.
"""

import logging

from app.services.fare_service import haversine_distance
from app.schemas.ride_hailing import (
    RideComparisonRequest,
    RideComparisonResponse,
    RideOption,
)

logger = logging.getLogger("tuki.services.ride_hailing")

# Mocked pricing constants
GRAB_BASE_FARE = 40.0
GRAB_PER_KM = 15.0
GRAB_PER_MIN = 2.0
MAXIM_BASE_FARE = 35.0
MAXIM_PER_KM = 12.0
MAXIM_PER_MIN = 1.5
AVG_CITY_SPEED_KMH = 20.0


class RideHailingService:
    """
    Service for comparing ride-hailing fares.

    Currently uses mocked pricing logic. Will integrate with
    Grab/Maxim APIs when available.
    """

    async def compare_options(
        self, request: RideComparisonRequest
    ) -> RideComparisonResponse:
        """Generate mocked fare comparison for Grab and Maxim."""
        distance_km = haversine_distance(
            request.origin_lat, request.origin_lon,
            request.destination_lat, request.destination_lon,
        )

        # Estimate duration
        duration_min = (distance_km / AVG_CITY_SPEED_KMH) * 60

        # Calculate mocked fares
        grab_fare = GRAB_BASE_FARE + (GRAB_PER_KM * distance_km) + (GRAB_PER_MIN * duration_min)
        maxim_fare = MAXIM_BASE_FARE + (MAXIM_PER_KM * distance_km) + (MAXIM_PER_MIN * duration_min)

        options = [
            RideOption(
                provider="grab",
                service_type="car",
                estimated_fare_min=round(grab_fare * 0.9, 2),
                estimated_fare_max=round(grab_fare * 1.2, 2),
                estimated_duration_min=round(duration_min, 1),
                surge_multiplier=1.0,
            ),
            RideOption(
                provider="grab",
                service_type="motorcycle",
                estimated_fare_min=round(grab_fare * 0.5, 2),
                estimated_fare_max=round(grab_fare * 0.7, 2),
                estimated_duration_min=round(duration_min * 0.7, 1),
                surge_multiplier=1.0,
            ),
            RideOption(
                provider="maxim",
                service_type="car",
                estimated_fare_min=round(maxim_fare * 0.9, 2),
                estimated_fare_max=round(maxim_fare * 1.15, 2),
                estimated_duration_min=round(duration_min, 1),
                surge_multiplier=1.0,
            ),
            RideOption(
                provider="maxim",
                service_type="motorcycle",
                estimated_fare_min=round(maxim_fare * 0.45, 2),
                estimated_fare_max=round(maxim_fare * 0.65, 2),
                estimated_duration_min=round(duration_min * 0.7, 1),
                surge_multiplier=1.0,
            ),
        ]

        return RideComparisonResponse(
            distance_km=round(distance_km, 2),
            options=options,
        )
