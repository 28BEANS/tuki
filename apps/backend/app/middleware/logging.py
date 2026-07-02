"""
Tuki Backend — Request/Response Logging Middleware

Logs incoming requests and outgoing responses with timing information.
"""

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("tuki.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs request method, path, status code, and response time."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            "→ %s %s",
            request.method,
            request.url.path,
        )

        response = await call_next(request)

        # Calculate response time
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log outgoing response
        logger.info(
            "← %s %s %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        return response
