"""
Tuki Backend — Jeep Stop Schemas
"""

import uuid

from pydantic import BaseModel


class JeepStopResponse(BaseModel):
    """Jeep stop response."""

    id: uuid.UUID
    stop_name: str
    latitude: float
    longitude: float
    sequence: int | None = None

    model_config = {"from_attributes": True}
