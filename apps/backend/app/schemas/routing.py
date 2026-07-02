"""
Tuki Backend — Routing Schemas

Defines the structured navigation output format.
"""

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    """Request for multimodal route calculation."""

    origin_lat: float = Field(..., description="Origin latitude")
    origin_lon: float = Field(..., description="Origin longitude")
    destination_lat: float = Field(..., description="Destination latitude")
    destination_lon: float = Field(..., description="Destination longitude")
    prefer: str = Field(
        "fastest",
        description="Route preference: fastest, cheapest, fewest_transfers",
    )
    is_student: bool = Field(False, description="Apply student fare")


class RouteSegment(BaseModel):
    """A single segment of a multimodal route."""

    mode: str = Field(..., description="Transport mode: jeep, walk, tricycle")
    route: str | None = Field(None, description="Route name (for jeep segments)")
    route_color: str | None = Field(None, description="Route color (for jeep segments)")
    board_at: str | None = Field(None, description="Boarding location name")
    alight_at: str | None = Field(None, description="Alighting location name")
    distance_m: float | None = Field(None, description="Segment distance in meters")
    duration_min: float | None = Field(None, description="Estimated duration in minutes")
    fare: float | None = Field(None, description="Segment fare in PHP")


class NavigationInstruction(BaseModel):
    """Human-readable, landmark-based navigation instruction."""

    step: int = Field(..., description="Step number")
    instruction: str = Field(..., description="Landmark-based instruction text")
    mode: str = Field(..., description="Transport mode for this step")


class RouteResponse(BaseModel):
    """Complete multimodal route response."""

    total_fare: float = Field(..., description="Total fare in PHP")
    total_distance_m: float = Field(..., description="Total distance in meters")
    travel_time_min: float = Field(..., description="Total estimated travel time in minutes")
    segments: list[RouteSegment] = Field(..., description="Ordered route segments")
    instructions: list[NavigationInstruction] = Field(
        default_factory=list, description="Landmark-based navigation instructions"
    )
    transfers: int = Field(0, description="Number of transfers")
