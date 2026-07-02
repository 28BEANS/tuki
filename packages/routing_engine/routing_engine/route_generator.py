"""
Tuki Routing Engine — Route Generator

Generates landmark-based navigation instructions from route results.
"""

import logging
from typing import Any

from routing_engine.graph_models import RouteResult, RouteSegment, TransportMode

logger = logging.getLogger("tuki.routing.generator")


class RouteGenerator:
    """
    Generates human-readable, landmark-based navigation instructions.

    Example output:
    1. Walk 250 meters to Holy Angel University.
    2. Board the Lavender Jeep (Checkpoint–Holy–Highway) at Holy Angel University.
    3. Stay on the jeep until Jenra Mall.
    4. Walk approximately 180 meters toward 7-Eleven.
    5. Ride the tricycle to your destination.
    """

    def generate_instructions(
        self,
        route: RouteResult,
        nearby_landmarks: dict[str, list[str]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate landmark-based navigation instructions.

        Args:
            route: The computed route result.
            nearby_landmarks: Optional dict mapping node_id → list of nearby landmark names.

        Returns:
            List of instruction dicts with step, instruction text, and mode.
        """
        instructions: list[dict[str, Any]] = []
        step = 1

        for i, segment in enumerate(route.segments):
            segment_instructions = self._generate_segment_instructions(
                segment, step, i == 0, i == len(route.segments) - 1,
                nearby_landmarks,
            )
            instructions.extend(segment_instructions)
            step += len(segment_instructions)

        return instructions

    def _generate_segment_instructions(
        self,
        segment: RouteSegment,
        start_step: int,
        is_first: bool,
        is_last: bool,
        nearby_landmarks: dict[str, list[str]] | None,
    ) -> list[dict[str, Any]]:
        """Generate instructions for a single segment."""
        instructions: list[dict[str, Any]] = []
        step = start_step

        if segment.mode == TransportMode.WALK:
            distance_text = self._format_distance(segment.distance_m)

            if is_first:
                # First segment: walking to a stop
                landmark = self._get_landmark_near(segment.alight_at, nearby_landmarks)
                text = f"Walk {distance_text} to {segment.alight_at or 'the nearest stop'}"
                if landmark:
                    text += f" (near {landmark})"
                text += "."
            elif is_last:
                text = f"Walk {distance_text} to your destination."
            else:
                landmark = self._get_landmark_near(segment.alight_at, nearby_landmarks)
                target = segment.alight_at or "the next stop"
                text = f"Walk approximately {distance_text} toward {target}"
                if landmark:
                    text += f" (near {landmark})"
                text += "."

            instructions.append({
                "step": step,
                "instruction": text,
                "mode": segment.mode.value,
            })

        elif segment.mode == TransportMode.JEEP:
            color = segment.route_color or ""
            route_name = segment.route_name or "Jeep"

            instructions.append({
                "step": step,
                "instruction": (
                    f"Board the {color} Jeep ({route_name}) "
                    f"at {segment.board_at or 'the stop'}."
                ),
                "mode": segment.mode.value,
            })

            if segment.alight_at:
                instructions.append({
                    "step": step + 1,
                    "instruction": f"Stay on the jeep until {segment.alight_at}.",
                    "mode": segment.mode.value,
                })

        elif segment.mode == TransportMode.TRICYCLE:
            if is_last:
                instructions.append({
                    "step": step,
                    "instruction": "Ride the tricycle to your destination.",
                    "mode": segment.mode.value,
                })
            else:
                instructions.append({
                    "step": step,
                    "instruction": (
                        f"Ride the tricycle to {segment.alight_at or 'the next stop'}."
                    ),
                    "mode": segment.mode.value,
                })

        return instructions

    @staticmethod
    def _format_distance(meters: float) -> str:
        """Format distance as human-readable string."""
        if meters < 100:
            return f"{int(meters)} meters"
        elif meters < 1000:
            return f"{int(round(meters / 10) * 10)} meters"
        else:
            return f"{meters / 1000:.1f} km"

    @staticmethod
    def _get_landmark_near(
        node_name: str | None,
        nearby_landmarks: dict[str, list[str]] | None,
    ) -> str | None:
        """Get a nearby landmark name for context."""
        if not node_name or not nearby_landmarks:
            return None
        landmarks = nearby_landmarks.get(node_name, [])
        return landmarks[0] if landmarks else None
