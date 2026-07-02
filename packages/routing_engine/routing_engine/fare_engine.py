"""
Tuki Routing Engine — Fare Engine

Calculates fares per segment and total based on the fare matrix.
"""

import logging
from typing import Any

from routing_engine.graph_models import RouteResult, RouteSegment, TransportMode

logger = logging.getLogger("tuki.routing.fare")

# Default fare values (LTFRB Traditional PUJ, Oct 2023)
DEFAULT_JEEP_BASE_FARE = 13.0  # First 4km
DEFAULT_JEEP_PER_KM = 1.80  # Beyond 4km
DEFAULT_JEEP_BASE_DISTANCE_KM = 4.0

DEFAULT_TRICYCLE_BASE_FARE = 20.0  # Typical base
DEFAULT_TRICYCLE_PER_KM = 5.0


class FareEngine:
    """
    Calculates transport fares using the fare matrix.

    Can be initialized with custom fare matrices or use defaults.
    """

    def __init__(self, fare_matrix: list[dict[str, Any]] | None = None) -> None:
        """
        Initialize with an optional fare matrix.

        fare_matrix format:
        [{"transport_type": "traditional_puj", "distance_km": 4.0,
          "regular_fare": 13.0, "student_fare": 10.40, "discounted_fare": 10.40}, ...]
        """
        self.fare_matrix = fare_matrix or []

    def calculate_segment_fare(
        self,
        segment: RouteSegment,
        is_student: bool = False,
        is_discounted: bool = False,
    ) -> float:
        """Calculate fare for a single route segment."""
        if segment.mode == TransportMode.WALK:
            return 0.0

        if segment.mode == TransportMode.TRANSFER:
            return 0.0

        distance_km = segment.distance_m / 1000

        if segment.mode == TransportMode.JEEP:
            fare = self._lookup_jeep_fare(distance_km, is_student, is_discounted)
        elif segment.mode == TransportMode.TRICYCLE:
            fare = self._calculate_tricycle_fare(distance_km)
        else:
            fare = 0.0

        return round(fare, 2)

    def calculate_total_fare(
        self,
        route: RouteResult,
        is_student: bool = False,
        is_discounted: bool = False,
    ) -> float:
        """Calculate total fare for a complete route."""
        total = 0.0
        for segment in route.segments:
            segment.fare = self.calculate_segment_fare(segment, is_student, is_discounted)
            total += segment.fare
        route.total_fare = round(total, 2)
        return route.total_fare

    def _lookup_jeep_fare(
        self, distance_km: float, is_student: bool, is_discounted: bool
    ) -> float:
        """Look up jeep fare from the matrix, fallback to defaults."""
        # Try fare matrix first
        for entry in sorted(self.fare_matrix, key=lambda e: e.get("distance_km", 0)):
            if (
                entry.get("transport_type") == "traditional_puj"
                and entry.get("distance_km", 0) >= distance_km
            ):
                if is_student:
                    return entry.get("student_fare", entry.get("regular_fare", 13.0))
                if is_discounted:
                    return entry.get("discounted_fare", entry.get("regular_fare", 13.0))
                return entry.get("regular_fare", 13.0)

        # Fallback to default calculation
        if distance_km <= DEFAULT_JEEP_BASE_DISTANCE_KM:
            fare = DEFAULT_JEEP_BASE_FARE
        else:
            extra_km = distance_km - DEFAULT_JEEP_BASE_DISTANCE_KM
            fare = DEFAULT_JEEP_BASE_FARE + (extra_km * DEFAULT_JEEP_PER_KM)

        if is_student or is_discounted:
            fare *= 0.80  # 20% discount

        return fare

    def _calculate_tricycle_fare(self, distance_km: float) -> float:
        """Calculate tricycle fare (mocked, varies by terminal)."""
        return DEFAULT_TRICYCLE_BASE_FARE + (distance_km * DEFAULT_TRICYCLE_PER_KM)
