"""
Tuki Routing Engine — Graph Models

Dataclasses representing the transportation graph structure.
These are independent of SQLAlchemy models.
"""

from dataclasses import dataclass, field
from enum import Enum

JEEP_WAIT_TIME_MIN = 5.0
TRANSFER_PENALTY_MIN = 2.0


class TransportMode(str, Enum):
    """Available transport modes in the network."""

    JEEP = "jeep"
    WALK = "walk"
    TRICYCLE = "tricycle"
    TRANSFER = "transfer"  # Virtual edge for mode changes


@dataclass(frozen=True)
class TransportNode:
    """
    A node in the transportation graph.

    Represents a jeep stop, walking intersection, transfer point,
    or tricycle terminal.
    """

    id: str
    name: str
    latitude: float
    longitude: float
    node_type: TransportMode
    route_id: str | None = None  # For jeep stops, the route they belong to

    @property
    def coords(self) -> tuple[float, float]:
        """Return (lat, lon) tuple."""
        return (self.latitude, self.longitude)


@dataclass(frozen=True)
class TransportEdge:
    """
    An edge in the transportation graph.

    Connects two nodes with transport mode, distance, fare, and travel time.
    """

    source_id: str
    target_id: str
    mode: TransportMode
    distance_m: float
    fare: float = 0.0
    travel_time_min: float = 0.0
    route_name: str | None = None
    route_color: str | None = None

    @property
    def weight_time(self) -> float:
        """Weight for fastest-route optimization, including a route change."""
        if self.mode == TransportMode.TRANSFER:
            return (
                self.travel_time_min
                + TRANSFER_PENALTY_MIN
                + JEEP_WAIT_TIME_MIN
            )
        return self.travel_time_min

    @property
    def weight_fare(self) -> float:
        """Weight for cheapest-route optimization."""
        return self.fare

    @property
    def weight_transfers(self) -> float:
        """Weight penalizing transfers (1.0 for transfers, 0.0 otherwise)."""
        return 1.0 if self.mode == TransportMode.TRANSFER else 0.0


@dataclass
class RouteSegment:
    """A single segment of a computed route."""

    mode: TransportMode
    route_name: str | None = None
    route_color: str | None = None
    board_at: str | None = None
    alight_at: str | None = None
    distance_m: float = 0.0
    duration_min: float = 0.0
    fare: float = 0.0
    nodes: list[str] = field(default_factory=list)


@dataclass
class RouteResult:
    """Complete result of a route computation."""

    segments: list[RouteSegment] = field(default_factory=list)
    total_fare: float = 0.0
    total_distance_m: float = 0.0
    total_time_min: float = 0.0
    transfers: int = 0

    def add_segment(self, segment: RouteSegment) -> None:
        """Add a segment and update totals."""
        self.segments.append(segment)
        self.total_fare += segment.fare
        self.total_distance_m += segment.distance_m
        self.total_time_min += segment.duration_min
        if segment.mode == TransportMode.TRANSFER:
            self.transfers += 1
