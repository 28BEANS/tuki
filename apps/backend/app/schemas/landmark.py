"""
Tuki Backend — Landmark Schemas
"""

import uuid

from pydantic import BaseModel, Field

from app.models.landmark import LandmarkCategory


class LandmarkResponse(BaseModel):
    """Landmark response for search results and lists."""

    id: uuid.UUID
    name: str
    aliases: list[str] | None = None
    category: LandmarkCategory
    latitude: float
    longitude: float
    barangay_name: str | None = None

    model_config = {"from_attributes": True}


class LandmarkQuery(BaseModel):
    """Query parameters for landmark search."""

    q: str | None = Field(None, description="Search query string", min_length=1)
    category: LandmarkCategory | None = Field(None, description="Filter by category")
    latitude: float | None = Field(None, description="Reference latitude for proximity search")
    longitude: float | None = Field(None, description="Reference longitude for proximity search")
    radius_m: float = Field(1000, description="Search radius in meters", ge=100, le=10000)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
