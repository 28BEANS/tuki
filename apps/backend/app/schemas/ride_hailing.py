"""
Tuki Backend — Ride-Hailing Comparison Schemas
"""

from pydantic import BaseModel, Field


class RideComparisonRequest(BaseModel):
    """Request for ride-hailing fare comparison."""

    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float


class RideOption(BaseModel):
    """A single ride-hailing option."""

    provider: str = Field(..., description="Provider name: grab, maxim")
    service_type: str = Field(..., description="Service type: car, motorcycle")
    estimated_fare_min: float = Field(..., description="Minimum estimated fare in PHP")
    estimated_fare_max: float = Field(..., description="Maximum estimated fare in PHP")
    estimated_duration_min: float = Field(..., description="Estimated duration in minutes")
    surge_multiplier: float = Field(1.0, description="Surge pricing multiplier")


class RideComparisonResponse(BaseModel):
    """Ride-hailing comparison response with all providers."""

    origin_address: str | None = None
    destination_address: str | None = None
    distance_km: float
    options: list[RideOption] = Field(default_factory=list)
