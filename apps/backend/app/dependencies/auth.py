"""
Tuki Backend — Authentication Dependencies

FastAPI dependencies for JWT-based authentication via Supabase.
"""

from typing import Annotated

from fastapi import Depends, Header

from app.core.exceptions import AuthenticationError
from app.core.security import extract_user_id, verify_supabase_token


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract and verify the current user's ID from the Authorization header.

    Expects: Authorization: Bearer <jwt_token>

    Returns:
        The authenticated user's UUID string.

    Raises:
        AuthenticationError: If no token or invalid token.
    """
    if not authorization:
        raise AuthenticationError("Authorization header required")

    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization scheme. Use: Bearer <token>")

    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_supabase_token(token)
    return extract_user_id(payload)


async def get_optional_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    """
    Optionally extract user ID. Returns None for unauthenticated requests.
    Useful for public endpoints that behave differently for logged-in users.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.removeprefix("Bearer ").strip()
        payload = verify_supabase_token(token)
        return extract_user_id(payload)
    except AuthenticationError:
        return None
