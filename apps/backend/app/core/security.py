"""
Tuki Backend — Supabase JWT Security

Verifies JWTs issued by Supabase Auth.
Extracts user identity from tokens.
"""

from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


def verify_supabase_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a Supabase JWT token.

    Args:
        token: The JWT token string.

    Returns:
        Decoded token payload.

    Raises:
        AuthenticationError: If the token is invalid or expired.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",
        )
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}") from e

    # Check expiration
    exp = payload.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(tz=timezone.utc):
        raise AuthenticationError("Token has expired")

    return payload


def extract_user_id(payload: dict[str, Any]) -> str:
    """
    Extract user ID from a decoded JWT payload.

    Args:
        payload: Decoded JWT payload.

    Returns:
        The user's UUID string.

    Raises:
        AuthenticationError: If the payload is missing user identity.
    """
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user identity")
    return user_id
