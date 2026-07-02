"""
Tuki Backend — User Repository
"""

from uuid import UUID

from sqlalchemy import select

from app.models.user_profile import UserProfile
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserProfile]):
    """Repository for user profile operations."""

    model = UserProfile

    async def get_by_email(self, email: str) -> UserProfile | None:
        """Find a user by email."""
        stmt = select(UserProfile).where(UserProfile.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self, id: UUID, email: str, full_name: str | None = None
    ) -> UserProfile:
        """Get existing profile or create one (idempotent signup)."""
        existing = await self.get_by_id(id)
        if existing:
            return existing
        return await self.create(id=id, email=email, full_name=full_name)
