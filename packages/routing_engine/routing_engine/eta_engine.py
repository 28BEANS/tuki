"""
Tuki Routing Engine — ETA Engine

Estimates travel time per segment based on transport mode speeds.
"""

import logging

from routing_engine.graph_models import RouteResult, RouteSegment, TransportMode

logger = logging.getLogger("tuki.routing.eta")

# Average speeds in km/h
MODE_SPEEDS: dict[TransportMode, float] = {
    TransportMode.JEEP: 15.0,       # City traffic, frequent stops
    TransportMode.WALK: 4.5,        # Average walking speed
    TransportMode.TRICYCLE: 20.0,   # Slightly faster than jeep
    TransportMode.TRANSFER: 4.5,    # Walking during transfer
}

# Additional time penalties in minutes
JEEP_WAIT_TIME_MIN = 5.0       # Average wait for a jeep
TRICYCLE_WAIT_TIME_MIN = 3.0   # Average wait for a tricycle
TRANSFER_PENALTY_MIN = 2.0     # Penalty per transfer


class ETAEngine:
    """Estimates travel time for route segments and complete routes."""

    def __init__(
        self,
        custom_speeds: dict[TransportMode, float] | None = None,
    ) -> None:
        self.speeds = {**MODE_SPEEDS, **(custom_speeds or {})}

    def estimate_segment_time(self, segment: RouteSegment) -> float:
        """
        Estimate travel time for a segment in minutes.

        Includes mode-specific wait times.
        """
        speed_kmh = self.speeds.get(segment.mode, 4.5)
        distance_km = segment.distance_m / 1000
        travel_min = (distance_km / speed_kmh) * 60

        # Add wait times
        if segment.mode == TransportMode.JEEP:
            travel_min += JEEP_WAIT_TIME_MIN
        elif segment.mode == TransportMode.TRICYCLE:
            travel_min += TRICYCLE_WAIT_TIME_MIN
        elif segment.mode == TransportMode.TRANSFER:
            travel_min += TRANSFER_PENALTY_MIN

        return round(travel_min, 1)

    def estimate_total_time(self, route: RouteResult) -> float:
        """Estimate total travel time for a complete route."""
        total = 0.0
        for segment in route.segments:
            segment.duration_min = self.estimate_segment_time(segment)
            total += segment.duration_min
        route.total_time_min = round(total, 1)
        return route.total_time_min
