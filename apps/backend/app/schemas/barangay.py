"""
Tuki Backend — Barangay Schemas
"""

import uuid

from pydantic import BaseModel, Field


class BarangayResponse(BaseModel):
    """Barangay list item response."""

    id: uuid.UUID
    barangay_name: str
    psgc_code: str | None = None

    model_config = {"from_attributes": True}


class BarangayDetail(BarangayResponse):
    """Barangay detail response with geometry."""

    geometry: dict | None = Field(None, description="GeoJSON geometry object")
    landmark_count: int = Field(0, description="Number of landmarks in this barangay")
