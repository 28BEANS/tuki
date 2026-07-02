"""
Tuki Backend — Auth Endpoints

Manages user profiles linked to Supabase Auth.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.exceptions import NotFoundError
from app.dependencies.auth import get_current_user_id
from app.dependencies.database import DBSession
from app.schemas.user import UserProfileCreate, UserProfileResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth")


@router.post("/signup", response_model=UserProfileResponse)
async def create_profile(
    data: UserProfileCreate,
    session: DBSession,
) -> UserProfileResponse:
    """
    Create a user profile after Supabase signup.

    Idempotent — safe to call multiple times for the same user.
    """
    service = UserService(session)
    return await service.create_or_get_profile(data)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    session: DBSession,
) -> UserProfileResponse:
    """Get the authenticated user's profile."""
    service = UserService(session)
    profile = await service.get_profile(UUID(user_id))
    if not profile:
        raise NotFoundError("User profile", user_id)
    return profile
