"""
Tuki Backend — Transfer Point Schemas
"""

import uuid

from pydantic import BaseModel

from app.models.transfer_point import TransferType


class TransferPointResponse(BaseModel):
    """Transfer point response."""

    id: uuid.UUID
    name: str | None = None
    transfer_type: TransferType
    from_route_name: str | None = None
    to_route_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = {"from_attributes": True}
