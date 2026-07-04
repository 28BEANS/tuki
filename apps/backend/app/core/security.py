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
        # Try to verify the token normally using the configured key/algorithm
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm, "HS256", "RS256", "ES256"],
            audience="authenticated",
        )
    except JWTError as e:
        import logging
        logger = logging.getLogger("tuki.security")
        try:
            unverified_header = jwt.get_unverified_header(token)
            logger.warning("Failed verifying token. Unverified header: %s", unverified_header)
        except Exception:
            pass

        # In development mode, if verification fails (due to key/algorithm mismatch),
        # fallback to decoding the payload without verification to avoid blocking local dev.
        if settings.is_development:
            logger.warning(
                "Signature verification failed (%s). Falling back to unverified decode in development mode.", e
            )
            try:
                payload = jwt.decode(
                    token,
                    "",
                    options={"verify_signature": False, "verify_aud": False},
                )
                return payload
            except Exception as fallback_err:
                raise AuthenticationError(f"Invalid token: {fallback_err}") from fallback_err

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
