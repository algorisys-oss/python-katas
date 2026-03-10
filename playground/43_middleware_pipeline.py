"""
Kata 43 -- Middleware Pipeline
Run: python playground/43_middleware_pipeline.py

Build an ASGI middleware system for the Ignite framework. Each middleware
wraps the app like onion layers, intercepting requests and responses.
Includes LoggingMiddleware, TimingMiddleware, and CORSMiddleware examples.

Completes within 5 seconds.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Simulated ASGI Types
# ===========================================================================

# ASGI is an async protocol: the app receives (scope, receive, send).
# We simulate it here without needing uvicorn.

Scope = dict[str, Any]
Message = dict[str, Any]
Receive = Callable[[], Any]      # simplified: returns next message
Send = Callable[[Message], Any]  # simplified: sends a message
ASGIApp = Callable[[Scope, Receive, Send], Any]  # async callable


@dataclass
class Request:
    """Minimal request parsed from an ASGI scope."""
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    @classmethod
    def from_scope(cls, scope: Scope) -> "Request":
        """Build a Request from an ASGI scope dict."""
        headers = {}
        for name, value in scope.get("headers", []):
            headers[name.decode() if isinstance(name, bytes) else name] = (
                value.decode() if isinstance(value, bytes) else value
            )
        return cls(
            method=scope.get("method", "GET"),
            path=scope.get("path", "/"),
            headers=headers,
        )


@dataclass
class Response:
    """Minimal response object."""
    status: int = 200
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)


def demo_asgi_types():
    """Show how ASGI scope maps to our Request."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/users/42",
        "headers": [
            (b"host", b"localhost:8000"),
            (b"accept", b"application/json"),
        ],
    }
    req = Request.from_scope(scope)
    print(f"  Scope -> Request: {req.method} {req.path}")
    print(f"  Headers: {req.headers}")
    assert req.method == "GET"
    assert req.path == "/users/42"
    assert req.headers["host"] == "localhost:8000"
    print(f"  [VALID] ASGI scope converts to Request correctly")


# ===========================================================================
# SECTION 2: Base Middleware & The Onion Model
# ===========================================================================

class Middleware:
    """Base ASGI middleware class.

    The onion model: each middleware wraps the next app. A request passes
    through middlewares outside-in, and the response passes back inside-out.

        Request -->  [CORS]  -->  [Timing]  -->  [Logging]  -->  App
        Response <-- [CORS]  <--  [Timing]  <--  [Logging]  <--  App

    Each middleware can:
    - Inspect/modify the request before calling the inner app
    - Inspect/modify the response after the inner app returns
    - Short-circuit by not calling the inner app at all
    """

    def __init__(self, app: ASGIApp):
        self.app = app  # the next layer (inner app or another middleware)

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        """Default: just pass through to the inner app."""
        await self.app(scope, receive, send)


# A simple "app" that returns a JSON response
async def sample_app(scope: Scope, receive: Receive, send: Send) -> None:
    """A minimal ASGI app that returns a fixed response."""
    response_body = b'{"message": "Hello from Ignite!"}'
    # Send response start
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
        ],
    })
    # Send response body
    await send({
        "type": "http.response.body",
        "body": response_body,
    })


def demo_base_middleware():
    """Show that base middleware passes through transparently."""
    captured: list[Message] = []

    async def mock_send(message: Message):
        captured.append(message)

    async def mock_receive():
        return {"type": "http.request", "body": b""}

    # Wrap sample_app with base middleware (should pass through)
    wrapped = Middleware(sample_app)
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}

    asyncio.run(wrapped(scope, mock_receive, mock_send))

    assert len(captured) == 2  # response.start + response.body
    assert captured[0]["status"] == 200
    assert captured[1]["body"] == b'{"message": "Hello from Ignite!"}'
    print(f"  Base middleware passes through: status={captured[0]['status']}")
    print(f"  Response body: {captured[1]['body'].decode()}")
    print(f"  [VALID] Base middleware is transparent")


# ===========================================================================
# SECTION 3: Practical Middlewares
# ===========================================================================

class LoggingMiddleware(Middleware):
    """Logs each request method and path.

    In a real app, this would write to a logging framework.
    Here we append to a log list for testing.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logs: list[str] = []

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        # Before: log the incoming request
        method = scope.get("method", "?")
        path = scope.get("path", "?")
        self.logs.append(f"{method} {path}")

        # Wrap send to capture the status code
        status_code = None

        async def logging_send(message: Message):
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        # Call inner app with our wrapped send
        await self.app(scope, receive, logging_send)

        # After: log the response status
        self.logs.append(f"  -> {status_code}")


class TimingMiddleware(Middleware):
    """Measures request processing time.

    Adds an X-Process-Time header to the response with the elapsed
    time in milliseconds.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.last_duration_ms: float = 0.0

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        start = time.perf_counter()

        async def timing_send(message: Message):
            if message.get("type") == "http.response.start":
                elapsed = (time.perf_counter() - start) * 1000
                self.last_duration_ms = elapsed
                # Add timing header
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-process-time", f"{elapsed:.2f}ms".encode())
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, timing_send)


class CORSMiddleware(Middleware):
    """Adds Cross-Origin Resource Sharing headers.

    Handles preflight OPTIONS requests and adds CORS headers to
    all responses.
    """

    def __init__(self, app: ASGIApp,
                 allow_origins: list[str] | None = None,
                 allow_methods: list[str] | None = None,
                 allow_headers: list[str] | None = None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE"]
        self.allow_headers = allow_headers or ["*"]

    def _cors_headers(self) -> list[tuple[bytes, bytes]]:
        """Build the CORS response headers."""
        return [
            (b"access-control-allow-origin",
             ", ".join(self.allow_origins).encode()),
            (b"access-control-allow-methods",
             ", ".join(self.allow_methods).encode()),
            (b"access-control-allow-headers",
             ", ".join(self.allow_headers).encode()),
        ]

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        # Handle preflight OPTIONS requests
        if scope.get("method") == "OPTIONS":
            await send({
                "type": "http.response.start",
                "status": 204,
                "headers": self._cors_headers(),
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })
            return

        # For other methods, add CORS headers to the response
        async def cors_send(message: Message):
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self._cors_headers())
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, cors_send)


def demo_practical_middlewares():
    """Test each middleware individually."""
    captured: list[Message] = []

    async def mock_send(message: Message):
        captured.append(message)

    async def mock_receive():
        return {"type": "http.request", "body": b""}

    scope = {
        "type": "http", "method": "GET", "path": "/api/users",
        "headers": [],
    }

    # --- LoggingMiddleware ---
    captured.clear()
    logging_mw = LoggingMiddleware(sample_app)
    asyncio.run(logging_mw(scope, mock_receive, mock_send))
    print(f"  LoggingMiddleware logs: {logging_mw.logs}")
    assert logging_mw.logs[0] == "GET /api/users"
    assert "200" in logging_mw.logs[1]

    # --- TimingMiddleware ---
    captured.clear()
    timing_mw = TimingMiddleware(sample_app)
    asyncio.run(timing_mw(scope, mock_receive, mock_send))
    # Check that X-Process-Time header was added
    start_msg = captured[0]
    header_names = [h[0] for h in start_msg["headers"]]
    assert b"x-process-time" in header_names
    print(f"  TimingMiddleware: {timing_mw.last_duration_ms:.2f}ms")

    # --- CORSMiddleware ---
    captured.clear()
    cors_mw = CORSMiddleware(
        sample_app,
        allow_origins=["https://example.com"],
        allow_methods=["GET", "POST"],
    )
    asyncio.run(cors_mw(scope, mock_receive, mock_send))
    start_msg = captured[0]
    header_dict = {h[0]: h[1] for h in start_msg["headers"]}
    assert b"access-control-allow-origin" in header_dict
    print(f"  CORSMiddleware headers: origin={header_dict[b'access-control-allow-origin'].decode()}")

    # --- CORS preflight ---
    captured.clear()
    options_scope = {**scope, "method": "OPTIONS"}
    asyncio.run(cors_mw(options_scope, mock_receive, mock_send))
    assert captured[0]["status"] == 204
    print(f"  CORS preflight: status={captured[0]['status']} (no body)")

    print(f"  [VALID] All three middlewares work correctly")


# ===========================================================================
# SECTION 4: Composing the Middleware Stack
# ===========================================================================

class MiddlewareStack:
    """Composes multiple middlewares around an app.

    Middlewares are applied in order: the first added is the outermost.
    This creates the onion-layer pattern.
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self._middleware_classes: list[tuple[type, dict]] = []

    def add(self, middleware_cls: type, **kwargs) -> "MiddlewareStack":
        """Add a middleware class (with optional kwargs) to the stack."""
        self._middleware_classes.append((middleware_cls, kwargs))
        return self  # allow chaining

    def build(self) -> ASGIApp:
        """Build the composed app by wrapping middlewares outside-in.

        If we add [A, B, C], the call order is: A -> B -> C -> app.
        So we wrap in reverse: app = C(app), app = B(app), app = A(app).
        """
        app = self.app
        # Wrap in reverse so first-added is outermost
        for cls, kwargs in reversed(self._middleware_classes):
            app = cls(app, **kwargs)
        return app


def demo_middleware_stack():
    """Demonstrate composing multiple middlewares."""
    captured: list[Message] = []

    async def mock_send(message: Message):
        captured.append(message)

    async def mock_receive():
        return {"type": "http.request", "body": b""}

    # Build middleware stack
    stack = MiddlewareStack(sample_app)
    stack.add(LoggingMiddleware)  # outermost -- logs first
    stack.add(TimingMiddleware)   # middle -- times inner layers
    stack.add(CORSMiddleware, allow_origins=["*"])  # innermost before app

    composed_app = stack.build()

    # The composed app is: LoggingMW(TimingMW(CORSMiddleware(sample_app)))
    print(f"  Stack layers: Logging -> Timing -> CORS -> App")

    scope = {
        "type": "http", "method": "GET", "path": "/api/data",
        "headers": [],
    }
    asyncio.run(composed_app(scope, mock_receive, mock_send))

    # Check all headers are present
    start_msg = captured[0]
    header_dict = {h[0]: h[1] for h in start_msg["headers"]}
    print(f"  Response status: {start_msg['status']}")
    print(f"  Headers present: {[h[0].decode() for h in start_msg['headers']]}")

    assert b"x-process-time" in header_dict, "TimingMiddleware header missing"
    assert b"access-control-allow-origin" in header_dict, "CORS header missing"
    assert start_msg["status"] == 200

    # Check logging middleware captured the request (it's the outermost wrapper)
    # We need to get a reference to it -- in the composed app, it's the top layer
    # Since we built it, the outermost is a LoggingMiddleware
    assert isinstance(composed_app, LoggingMiddleware)
    print(f"  Logging captured: {composed_app.logs}")
    assert "GET /api/data" in composed_app.logs[0]

    print(f"  [VALID] Middleware stack composes correctly")


# ===========================================================================
# SECTION 5: Short-Circuit Middleware (Auth Example)
# ===========================================================================

class AuthMiddleware(Middleware):
    """Authentication middleware that short-circuits unauthorized requests.

    If the request doesn't have a valid Authorization header, return 401
    without ever reaching the inner app.
    """

    def __init__(self, app: ASGIApp, valid_tokens: set[str] | None = None):
        super().__init__(app)
        self.valid_tokens = valid_tokens or {"secret-token-123"}

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        headers = dict(scope.get("headers", []))
        auth_key = b"authorization"
        token = headers.get(auth_key, b"").decode()

        if token not in self.valid_tokens:
            # Short-circuit: return 401 without calling the inner app
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"error": "Unauthorized"}',
            })
            return

        # Token valid -- proceed to inner app
        await self.app(scope, receive, send)


def demo_auth_middleware():
    """Demonstrate middleware that short-circuits the pipeline."""
    captured: list[Message] = []

    async def mock_send(message: Message):
        captured.append(message)

    async def mock_receive():
        return {"type": "http.request", "body": b""}

    auth_app = AuthMiddleware(sample_app, valid_tokens={"my-secret"})

    # Request WITHOUT valid token -- should get 401
    captured.clear()
    scope_no_auth = {
        "type": "http", "method": "GET", "path": "/secret",
        "headers": [(b"authorization", b"wrong-token")],
    }
    asyncio.run(auth_app(scope_no_auth, mock_receive, mock_send))
    assert captured[0]["status"] == 401
    print(f"  No valid token -> {captured[0]['status']}: {captured[1]['body'].decode()}")

    # Request WITH valid token -- should get 200
    captured.clear()
    scope_auth = {
        "type": "http", "method": "GET", "path": "/secret",
        "headers": [(b"authorization", b"my-secret")],
    }
    asyncio.run(auth_app(scope_auth, mock_receive, mock_send))
    assert captured[0]["status"] == 200
    print(f"  Valid token -> {captured[0]['status']}: {captured[1]['body'].decode()}")

    # Full stack with auth
    captured.clear()
    stack = MiddlewareStack(sample_app)
    stack.add(LoggingMiddleware)
    stack.add(AuthMiddleware, valid_tokens={"admin-key"})
    composed = stack.build()

    scope_blocked = {
        "type": "http", "method": "GET", "path": "/admin",
        "headers": [(b"authorization", b"bad")],
    }
    asyncio.run(composed(scope_blocked, mock_receive, mock_send))
    assert captured[0]["status"] == 401
    print(f"  Stack with auth (bad key) -> {captured[0]['status']}")

    captured.clear()
    scope_allowed = {
        "type": "http", "method": "GET", "path": "/admin",
        "headers": [(b"authorization", b"admin-key")],
    }
    asyncio.run(composed(scope_allowed, mock_receive, mock_send))
    assert captured[0]["status"] == 200
    print(f"  Stack with auth (good key) -> {captured[0]['status']}")

    print(f"  [VALID] Auth middleware short-circuits correctly")


# ===========================================================================
# Main
# ===========================================================================

def main():
    print("--- Section 1: Simulated ASGI Types ---")
    demo_asgi_types()
    print()

    print("--- Section 2: Base Middleware & The Onion Model ---")
    demo_base_middleware()
    print()

    print("--- Section 3: Practical Middlewares ---")
    demo_practical_middlewares()
    print()

    print("--- Section 4: Composing the Middleware Stack ---")
    demo_middleware_stack()
    print()

    print("--- Section 5: Short-Circuit Middleware (Auth) ---")
    demo_auth_middleware()
    print()

    print("--- Summary ---")
    print("Middleware wraps your app in composable layers:")
    print("  - Each middleware receives (scope, receive, send)")
    print("  - Can modify request before calling inner app")
    print("  - Can modify response by wrapping the send callable")
    print("  - Can short-circuit by sending a response without calling inner app")
    print("  - Composes like onion layers: first added = outermost")
    print()
    print("All 5 sections passed. Middleware pipeline mastered!")
    print("Next up: Kata 44 -- Dependency Injection System")


if __name__ == "__main__":
    main()
