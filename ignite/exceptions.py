"""Ignite Exceptions — HTTP errors and exception handler registry."""

from __future__ import annotations

import json
from typing import Any, Callable

from .response import JSONResponse, Response


# ---------------------------------------------------------------------------
# Standard HTTP status phrases
# ---------------------------------------------------------------------------

HTTP_STATUS_PHRASES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


# ---------------------------------------------------------------------------
# HTTPException and convenience subclasses
# ---------------------------------------------------------------------------

class HTTPException(Exception):
    """An HTTP error response as an exception.

    Raise this in route handlers to return an error response:
        raise HTTPException(404, detail="User not found")
    """

    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail or HTTP_STATUS_PHRASES.get(status_code, "Error")
        self.headers = headers or {}
        super().__init__(self.detail)

    def to_response(self) -> dict[str, Any]:
        """Convert to a JSON-serializable response body."""
        return {
            "error": {
                "status_code": self.status_code,
                "detail": self.detail,
                "type": HTTP_STATUS_PHRASES.get(self.status_code, "Error"),
            }
        }

    def __repr__(self) -> str:
        return (
            f"HTTPException(status_code={self.status_code}, "
            f"detail={self.detail!r})"
        )


class NotFound(HTTPException):
    """404 Not Found."""
    def __init__(self, detail: str = "Not Found") -> None:
        super().__init__(404, detail)


class BadRequest(HTTPException):
    """400 Bad Request."""
    def __init__(self, detail: str = "Bad Request") -> None:
        super().__init__(400, detail)


class Unauthorized(HTTPException):
    """401 Unauthorized."""
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(401, detail)


class Forbidden(HTTPException):
    """403 Forbidden."""
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(403, detail)


# ---------------------------------------------------------------------------
# Exception Handler Registry
# ---------------------------------------------------------------------------

# Type alias for exception handler functions
ExceptionHandler = Callable[..., Response]


class ExceptionHandlerRegistry:
    """Registry that maps exception types to handler functions.

    Supports:
    - Exact type matching
    - MRO-based lookup (handler for parent class catches child)
    - Default handlers for HTTPException and generic Exception
    - Custom handlers for application-specific exceptions
    """

    def __init__(self) -> None:
        self._handlers: dict[type, ExceptionHandler] = {}
        self._install_defaults()

    def _install_defaults(self) -> None:
        """Register default handlers for common exception types."""

        def handle_http_exception(request: Any, exc: HTTPException) -> Response:
            return JSONResponse(
                content=exc.to_response(),
                status_code=exc.status_code,
                headers=exc.headers or None,
            )

        def handle_generic_error(request: Any, exc: Exception) -> Response:
            return JSONResponse(
                content={
                    "error": {
                        "status_code": 500,
                        "detail": "Internal Server Error",
                        "type": "Internal Server Error",
                    }
                },
                status_code=500,
            )

        self._handlers[HTTPException] = handle_http_exception
        self._handlers[Exception] = handle_generic_error

    def add(self, exc_class: type, handler: ExceptionHandler) -> None:
        """Register a handler for an exception type."""
        self._handlers[exc_class] = handler

    def handle(self, request: Any, exc: Exception) -> Response:
        """Find and call the best matching handler for an exception.

        Walks the exception's MRO to find the closest registered handler.
        """
        exc_type = type(exc)

        # Exact match first
        if exc_type in self._handlers:
            return self._handlers[exc_type](request, exc)

        # Walk MRO for parent class match
        for cls in exc_type.__mro__:
            if cls in self._handlers:
                return self._handlers[cls](request, exc)

        # Fallback (should not reach here since Exception is registered)
        return JSONResponse(
            content={"error": {"detail": str(exc), "status_code": 500}},
            status_code=500,
        )

    def __contains__(self, exc_class: type) -> bool:
        return exc_class in self._handlers
