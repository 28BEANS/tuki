"""
Tuki Backend — Global Error Handler Middleware

Catches TukiError exceptions and converts them to structured JSON responses.
"""

import logging
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.exceptions import TukiError

logger = logging.getLogger("tuki.errors")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches application exceptions and returns structured error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except TukiError as e:
            logger.warning(
                "Application error: %s (status=%d, path=%s)",
                e.message,
                e.status_code,
                request.url.path,
            )
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.message,
                    "detail": e.detail,
                },
            )
        except Exception as e:
            logger.exception(
                "Unhandled exception on %s %s",
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "detail": str(e) if logger.isEnabledFor(logging.DEBUG) else None,
                },
            )
