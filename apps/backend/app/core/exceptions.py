"""
Tuki Backend — Custom Exception Hierarchy

All application exceptions inherit from TukiError.
The global exception handler maps these to HTTP responses.
"""

from typing import Any


class TukiError(Exception):
    """Base exception for all Tuki application errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        detail: Any = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(TukiError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", identifier: Any = None) -> None:
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message=message, status_code=404)


class ValidationError(TukiError):
    """Raised when input validation fails beyond Pydantic checks."""

    def __init__(self, message: str = "Validation error", detail: Any = None) -> None:
        super().__init__(message=message, status_code=422, detail=detail)


class AuthenticationError(TukiError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, status_code=401)


class AuthorizationError(TukiError):
    """Raised when a user lacks permissions."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, status_code=403)


class RoutingError(TukiError):
    """Raised when the routing engine cannot compute a route."""

    def __init__(self, message: str = "Unable to compute route", detail: Any = None) -> None:
        super().__init__(message=message, status_code=400, detail=detail)


class ExternalServiceError(TukiError):
    """Raised when an external API call fails (Google, etc.)."""

    def __init__(self, service: str = "External service", message: str = "Service unavailable") -> None:
        super().__init__(message=f"{service}: {message}", status_code=502)


class DatabaseError(TukiError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database error") -> None:
        super().__init__(message=message, status_code=500)
