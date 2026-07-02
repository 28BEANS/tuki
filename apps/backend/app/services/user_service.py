"""
Tuki Backend — User Service

Profile management and post-signup hooks.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.schemas.user import UserProfileCreate, UserProfileResponse

logger = logging.getLogger("tuki.services.user")


class UserService:
    """Service for user profile management."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def create_or_get_profile(
        self, data: UserProfileCreate
    ) -> UserProfileResponse:
        """
        Create a user profile after Supabase signup, or return existing.

        This is idempotent — safe to call multiple times for the same user.
        """
        profile = await self.repo.get_or_create(
            id=data.id,
            email=data.email,
            full_name=data.full_name,
        )

        return UserProfileResponse.model_validate(profile)

    async def get_profile(self, user_id: UUID) -> UserProfileResponse | None:
        """Get a user profile by ID."""
        profile = await self.repo.get_by_id(user_id)
        if not profile:
            return None
        return UserProfileResponse.model_validate(profile)
