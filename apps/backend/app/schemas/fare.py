"""
Tuki Backend — Fare Schemas
"""

import uuid

from pydantic import BaseModel, Field


class FareMatrixResponse(BaseModel):
    """Fare matrix entry response."""

    id: uuid.UUID
    transport_type: str
    distance_km: float
    regular_fare: float
    discounted_fare: float
    student_fare: float

    model_config = {"from_attributes": True}


class FareCalculationRequest(BaseModel):
    """Request to calculate fare for a trip."""

    origin_lat: float = Field(..., description="Origin latitude")
    origin_lon: float = Field(..., description="Origin longitude")
    destination_lat: float = Field(..., description="Destination latitude")
    destination_lon: float = Field(..., description="Destination longitude")
    is_student: bool = Field(False, description="Apply student discount")
    is_discounted: bool = Field(False, description="Apply senior/PWD discount")


class FareCalculationResponse(BaseModel):
    """Calculated fare breakdown."""

    total_fare: float = Field(..., description="Total fare in PHP")
    distance_km: float = Field(..., description="Estimated distance in km")
    fare_type: str = Field("regular", description="Fare type applied")
    breakdown: list[dict] = Field(
        default_factory=list, description="Per-segment fare breakdown"
    )
