"""
Kata 48 -- Error Handling & Exception Handlers
Run: python playground/48_error_handling.py

Build Ignite's error handling system: HTTPException with status codes,
exception handler registry that maps exception types to handler functions,
validation error formatting, and default handlers for common errors.

Completes within 5 seconds.
"""

from __future__ import annotations

import json
import traceback
from typing import Any, Callable


# ===========================================================================
# SECTION 1: HTTPException
# ===========================================================================
# The foundation of web framework error handling. Every HTTP error is an
# exception with a status code, detail message, and optional headers.

# Standard HTTP status codes and their reason phrases
HTTP_STATUS_PHRASES = {
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
    ):
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
                "type": HTTP_STATUS_PHRASES.get(
                    self.status_code, "Error"
                ),
            }
        }

    def __repr__(self) -> str:
        return f"HTTPException(status_code={self.status_code}, detail={self.detail!r})"


# Convenience subclasses for common errors
class NotFoundError(HTTPException):
    """404 Not Found."""
    def __init__(self, detail: str = "Not Found"):
        super().__init__(404, detail)


class BadRequestError(HTTPException):
    """400 Bad Request."""
    def __init__(self, detail: str = "Bad Request"):
        super().__init__(400, detail)


class UnauthorizedError(HTTPException):
    """401 Unauthorized."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(401, detail)


class ForbiddenError(HTTPException):
    """403 Forbidden."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)


class ConflictError(HTTPException):
    """409 Conflict."""
    def __init__(self, detail: str = "Conflict"):
        super().__init__(409, detail)


# ===========================================================================
# SECTION 2: Validation Error Formatting
# ===========================================================================
# Validation errors (from kata 45) get their own structured format,
# similar to how FastAPI formats Pydantic validation errors.

class ValidationError(Exception):
    """Structured validation error with field-level details."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors
        super().__init__(f"{len(errors)} validation error(s)")

    def to_response(self) -> dict[str, Any]:
        """Convert to a structured JSON response matching FastAPI format."""
        return {
            "error": {
                "status_code": 422,
                "detail": "Validation Error",
                "type": "Unprocessable Entity",
                "errors": [
                    {
                        "loc": ["body", err.get("field", "unknown")],
                        "msg": err.get("message", "invalid value"),
                        "type": err.get("type", "value_error"),
                    }
                    for err in self.errors
                ],
            }
        }


# ===========================================================================
# SECTION 3: Exception Handler Registry
# ===========================================================================
# The registry maps exception types to handler functions. When an exception
# is raised, we walk the MRO to find the best matching handler.

# Type alias for exception handler functions
ExceptionHandler = Callable[[Any, Exception], "Response"]


class Response:
    """Simplified HTTP response for error handling demos."""

    def __init__(
        self,
        body: dict[str, Any],
        status_code: int = 500,
        headers: dict[str, str] | None = None,
    ):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {"content-type": "application/json"}

    def to_json(self) -> str:
        return json.dumps(self.body)

    def __repr__(self) -> str:
        return f"Response(status={self.status_code}, body={self.body})"


class ExceptionHandlerRegistry:
    """Registry that maps exception types to handler functions.

    Supports:
    - Exact type matching
    - MRO-based lookup (handler for parent class catches child)
    - Default handlers for common HTTP errors
    - Custom handlers for application-specific exceptions
    """

    def __init__(self):
        self._handlers: dict[type, ExceptionHandler] = {}
        self._install_defaults()

    def _install_defaults(self):
        """Register default handlers for common exception types."""

        # HTTPException -> structured JSON error
        def handle_http_exception(request: Any, exc: HTTPException) -> Response:
            return Response(
                body=exc.to_response(),
                status_code=exc.status_code,
                headers=exc.headers,
            )

        # ValidationError -> 422 with field details
        def handle_validation_error(
            request: Any, exc: ValidationError
        ) -> Response:
            return Response(
                body=exc.to_response(),
                status_code=422,
            )

        # Generic Exception -> 500 Internal Server Error
        def handle_generic_error(request: Any, exc: Exception) -> Response:
            return Response(
                body={
                    "error": {
                        "status_code": 500,
                        "detail": "Internal Server Error",
                        "type": "Internal Server Error",
                    }
                },
                status_code=500,
            )

        self._handlers[HTTPException] = handle_http_exception
        self._handlers[ValidationError] = handle_validation_error
        self._handlers[Exception] = handle_generic_error

    def add(
        self,
        exc_class: type,
        handler: ExceptionHandler,
    ) -> None:
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
        return Response(
            body={"error": {"detail": str(exc), "status_code": 500}},
            status_code=500,
        )

    def __contains__(self, exc_class: type) -> bool:
        return exc_class in self._handlers


# ===========================================================================
# SECTION 4: Ignite App Integration
# ===========================================================================
# Show how exception handling integrates with the Ignite app's request
# processing pipeline.

class Request:
    """Simulated HTTP request."""
    def __init__(self, method: str, path: str):
        self.method = method
        self.path = path


class IgniteApp:
    """Simplified Ignite app showing error handling integration."""

    def __init__(self):
        self.exception_handlers = ExceptionHandlerRegistry()
        self._routes: dict[str, Callable] = {}

    def route(self, path: str):
        """Register a route handler."""
        def decorator(func: Callable) -> Callable:
            self._routes[path] = func
            return func
        return decorator

    def add_exception_handler(
        self,
        exc_class: type,
        handler: ExceptionHandler,
    ) -> None:
        """Register a custom exception handler."""
        self.exception_handlers.add(exc_class, handler)

    def handle_request(self, request: Request) -> Response:
        """Process a request, catching any exceptions.

        This is the core error-handling pipeline:
        1. Find the route handler
        2. Call it inside a try/except
        3. If an exception is raised, look up the handler
        4. Return the error response
        """
        try:
            handler = self._routes.get(request.path)
            if handler is None:
                raise NotFoundError(
                    f"No route matches '{request.path}'"
                )
            result = handler(request)
            if isinstance(result, Response):
                return result
            # Auto-wrap dict responses
            return Response(body=result, status_code=200)

        except Exception as exc:
            return self.exception_handlers.handle(request, exc)


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_http_exceptions():
    """Show HTTPException and its subclasses."""
    print("--- Section 1: HTTPException ---")

    # Basic HTTPException
    exc = HTTPException(404, "User not found")
    print(f"  {exc!r}")
    print(f"  Response: {exc.to_response()}")
    assert exc.status_code == 404
    assert exc.detail == "User not found"

    # Default detail from status code
    exc2 = HTTPException(500)
    print(f"  Default detail: {exc2.detail!r}")
    assert exc2.detail == "Internal Server Error"

    # With custom headers
    exc3 = HTTPException(
        429, "Rate limit exceeded",
        headers={"Retry-After": "60"},
    )
    print(f"  With headers: {exc3.headers}")
    assert exc3.headers["Retry-After"] == "60"

    # Convenience subclasses
    assert NotFoundError().status_code == 404
    assert BadRequestError().status_code == 400
    assert UnauthorizedError().status_code == 401
    assert ForbiddenError().status_code == 403
    assert ConflictError().status_code == 409
    print("  Convenience classes: NotFound=404, BadRequest=400, "
          "Unauthorized=401, Forbidden=403, Conflict=409")

    print("  [PASS] HTTPException works")


def demo_validation_errors():
    """Show structured validation error formatting."""
    print("\n--- Section 2: Validation Error Formatting ---")

    errors = [
        {"field": "name", "message": "field is required"},
        {"field": "age", "message": "value must be >= 0", "type": "value_error.number"},
        {"field": "email", "message": "invalid email format"},
    ]
    exc = ValidationError(errors)
    response = exc.to_response()
    print(f"  Validation error with {len(errors)} fields:")
    for err in response["error"]["errors"]:
        print(f"    loc={err['loc']}, msg={err['msg']}")

    assert response["error"]["status_code"] == 422
    assert len(response["error"]["errors"]) == 3
    assert response["error"]["errors"][0]["loc"] == ["body", "name"]

    print("  [PASS] Validation error formatting works")


def demo_handler_registry():
    """Show exception handler registry with MRO lookup."""
    print("\n--- Section 3: Exception Handler Registry ---")

    registry = ExceptionHandlerRegistry()

    # HTTPException handled
    exc = HTTPException(403, "Access denied")
    resp = registry.handle(None, exc)
    print(f"  HTTPException(403): status={resp.status_code}")
    assert resp.status_code == 403

    # NotFoundError (subclass of HTTPException) uses parent handler
    exc2 = NotFoundError("Page missing")
    resp2 = registry.handle(None, exc2)
    print(f"  NotFoundError: status={resp2.status_code} (via MRO)")
    assert resp2.status_code == 404

    # ValidationError
    exc3 = ValidationError([{"field": "x", "message": "bad"}])
    resp3 = registry.handle(None, exc3)
    print(f"  ValidationError: status={resp3.status_code}")
    assert resp3.status_code == 422

    # Unknown exception -> 500
    exc4 = RuntimeError("Something broke")
    resp4 = registry.handle(None, exc4)
    print(f"  RuntimeError: status={resp4.status_code} (generic handler)")
    assert resp4.status_code == 500

    # Custom handler
    class RateLimitError(Exception):
        pass

    def handle_rate_limit(request: Any, exc: RateLimitError) -> Response:
        return Response(
            body={"error": {"detail": "Too many requests", "status_code": 429}},
            status_code=429,
            headers={"Retry-After": "30"},
        )

    registry.add(RateLimitError, handle_rate_limit)
    exc5 = RateLimitError()
    resp5 = registry.handle(None, exc5)
    print(f"  RateLimitError (custom): status={resp5.status_code}")
    assert resp5.status_code == 429
    assert resp5.headers["Retry-After"] == "30"

    print("  [PASS] Handler registry works")


def demo_mro_lookup():
    """Show MRO-based handler lookup in detail."""
    print("\n--- Section 4: MRO-Based Lookup ---")

    registry = ExceptionHandlerRegistry()

    # Define a hierarchy
    class AppError(Exception):
        pass

    class DatabaseError(AppError):
        pass

    class ConnectionError_(DatabaseError):
        pass

    # Register handler for AppError (catches all descendants)
    def handle_app_error(request: Any, exc: AppError) -> Response:
        return Response(
            body={"error": {"detail": str(exc), "status_code": 500,
                            "type": "application_error"}},
            status_code=500,
        )

    registry.add(AppError, handle_app_error)

    # DatabaseError is caught by AppError handler (MRO walk)
    exc1 = DatabaseError("Connection pool exhausted")
    resp1 = registry.handle(None, exc1)
    print(f"  DatabaseError -> AppError handler: type={resp1.body['error']['type']}")
    assert resp1.body["error"]["type"] == "application_error"

    # ConnectionError_ also caught by AppError handler
    exc2 = ConnectionError_("Timeout")
    resp2 = registry.handle(None, exc2)
    print(f"  ConnectionError_ -> AppError handler (2 levels up)")
    assert resp2.body["error"]["type"] == "application_error"

    # Register more specific handler for DatabaseError
    def handle_db_error(request: Any, exc: DatabaseError) -> Response:
        return Response(
            body={"error": {"detail": str(exc), "status_code": 503,
                            "type": "database_error"}},
            status_code=503,
        )

    registry.add(DatabaseError, handle_db_error)

    # Now DatabaseError uses its own handler
    resp3 = registry.handle(None, DatabaseError("Pool full"))
    print(f"  DatabaseError -> own handler: type={resp3.body['error']['type']}")
    assert resp3.body["error"]["type"] == "database_error"

    # ConnectionError_ now matches DatabaseError (closer in MRO)
    resp4 = registry.handle(None, ConnectionError_("Reset"))
    print(f"  ConnectionError_ -> DatabaseError handler (closer match)")
    assert resp4.body["error"]["type"] == "database_error"

    print("  [PASS] MRO-based lookup works")


def demo_app_integration():
    """Show error handling in the Ignite app pipeline."""
    print("\n--- Section 5: App Integration ---")

    app = IgniteApp()

    @app.route("/users")
    def get_users(request: Request) -> dict:
        return {"users": ["Alice", "Bob"]}

    @app.route("/users/1")
    def get_user(request: Request) -> dict:
        raise NotFoundError("User 1 not found")

    @app.route("/admin")
    def admin_panel(request: Request) -> dict:
        raise ForbiddenError("Admin access required")

    @app.route("/crash")
    def crash_endpoint(request: Request) -> dict:
        raise RuntimeError("Unexpected failure")

    @app.route("/validate")
    def validate_endpoint(request: Request) -> dict:
        raise ValidationError([
            {"field": "email", "message": "invalid format"},
        ])

    # Successful request
    resp = app.handle_request(Request("GET", "/users"))
    print(f"  GET /users -> {resp.status_code}: {resp.body}")
    assert resp.status_code == 200

    # 404 from route handler
    resp2 = app.handle_request(Request("GET", "/users/1"))
    print(f"  GET /users/1 -> {resp2.status_code}: {resp2.body['error']['detail']}")
    assert resp2.status_code == 404

    # 404 from missing route
    resp3 = app.handle_request(Request("GET", "/nonexistent"))
    print(f"  GET /nonexistent -> {resp3.status_code}: {resp3.body['error']['detail']}")
    assert resp3.status_code == 404

    # 403
    resp4 = app.handle_request(Request("GET", "/admin"))
    print(f"  GET /admin -> {resp4.status_code}: {resp4.body['error']['detail']}")
    assert resp4.status_code == 403

    # 500 from unhandled exception
    resp5 = app.handle_request(Request("GET", "/crash"))
    print(f"  GET /crash -> {resp5.status_code}: {resp5.body['error']['detail']}")
    assert resp5.status_code == 500

    # 422 from validation error
    resp6 = app.handle_request(Request("POST", "/validate"))
    print(f"  POST /validate -> {resp6.status_code}: validation errors")
    assert resp6.status_code == 422

    print("  [PASS] App integration works")


def demo_custom_app_handlers():
    """Show adding custom exception handlers to the app."""
    print("\n--- Section 6: Custom App Handlers ---")

    app = IgniteApp()

    # Custom business exception
    class InsufficientFundsError(Exception):
        def __init__(self, balance: float, required: float):
            self.balance = balance
            self.required = required
            super().__init__(
                f"Insufficient funds: have {balance}, need {required}"
            )

    # Custom handler
    def handle_insufficient_funds(
        request: Any, exc: InsufficientFundsError
    ) -> Response:
        return Response(
            body={
                "error": {
                    "status_code": 402,
                    "detail": str(exc),
                    "type": "payment_required",
                    "balance": exc.balance,
                    "required": exc.required,
                }
            },
            status_code=402,
        )

    app.add_exception_handler(InsufficientFundsError, handle_insufficient_funds)

    @app.route("/purchase")
    def purchase(request: Request) -> dict:
        raise InsufficientFundsError(balance=10.0, required=49.99)

    resp = app.handle_request(Request("POST", "/purchase"))
    print(f"  Custom handler: status={resp.status_code}")
    print(f"  Body: {resp.body}")
    assert resp.status_code == 402
    assert resp.body["error"]["balance"] == 10.0
    assert resp.body["error"]["type"] == "payment_required"

    print("  [PASS] Custom app handlers work")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_http_exceptions()
    demo_validation_errors()
    demo_handler_registry()
    demo_mro_lookup()
    demo_app_integration()
    demo_custom_app_handlers()

    print("\n--- Summary ---")
    print("Error handling gives our Ignite framework:")
    print("  - HTTPException with status codes and details")
    print("  - Convenience classes: NotFoundError, BadRequestError, etc.")
    print("  - Structured validation error formatting (422)")
    print("  - Exception handler registry with MRO-based lookup")
    print("  - Default handlers for HTTP, validation, and generic errors")
    print("  - Custom handlers for business-specific exceptions")
    print("  - Seamless integration in the request processing pipeline")
    print("\nAll 6 sections passed. Error handling & exception handlers mastered!")
    print("Next up: Kata 49 -- route decorators!")


if __name__ == "__main__":
    main()
