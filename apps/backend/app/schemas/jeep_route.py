"""
Tuki Backend — Jeep Route Schemas
"""

import uuid

from pydantic import BaseModel, Field

from app.schemas.jeep_stop import JeepStopResponse


class JeepRouteResponse(BaseModel):
    """Jeep route list response."""

    id: uuid.UUID
    route_name: str
    route_color: str
    description: str | None = None
    operating_direction: str | None = None

    model_config = {"from_attributes": True}


class JeepRouteDetail(JeepRouteResponse):
    """Jeep route detail with ordered stops and geometry."""

    stops: list[JeepStopResponse] = Field(default_factory=list)
    geometry: dict | None = Field(None, description="GeoJSON geometry object")
