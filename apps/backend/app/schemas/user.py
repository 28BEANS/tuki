"""
Tuki Backend — User Profile Schemas
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserProfileCreate(BaseModel):
    """Schema for creating a user profile after Supabase signup."""

    id: uuid.UUID = Field(..., description="Supabase Auth user UUID")
    email: EmailStr
    full_name: str | None = None


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: uuid.UUID
    email: str
    full_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
