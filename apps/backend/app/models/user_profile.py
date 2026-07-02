"""
Tuki Backend — User Profile Model

Linked to Supabase Auth. Created automatically after signup.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserProfile(Base):
    """
    User profile linked to Supabase Auth.

    The 'id' matches the Supabase Auth user UUID.
    Created automatically on first login/signup.
    """

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    first_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    last_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<UserProfile(email={self.email!r})>"
