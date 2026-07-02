"""
Tuki Backend — Common Schemas

Shared types used across multiple schema modules.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class GeoJSONPoint(BaseModel):
    """GeoJSON point representation for API responses."""

    type: str = "Point"
    coordinates: list[float] = Field(
        ..., description="[longitude, latitude]", min_length=2, max_length=2
    )


class GeoJSONLineString(BaseModel):
    """GeoJSON linestring representation for API responses."""

    type: str = "LineString"
    coordinates: list[list[float]] = Field(
        ..., description="Array of [longitude, latitude] pairs"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""

    items: list[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Items per page")
    has_next: bool = Field(False, description="Whether more pages exist")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: bool = True
    message: str
    detail: Any = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
    environment: str
