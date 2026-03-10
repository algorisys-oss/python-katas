"""
Kata 43 -- Middleware Pipeline
Run: python playground/skeletons/43_middleware_pipeline.py

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

Scope = dict[str, Any]
Message = dict[str, Any]
Receive = Callable[[], Any]
Send = Callable[[Message], Any]
ASGIApp = Callable[[Scope, Receive, Send], Any]


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
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        """Default: just pass through to the inner app."""
        # TODO: Call self.app(scope, receive, send) with await
        pass


async def sample_app(scope: Scope, receive: Receive, send: Send) -> None:
    """A minimal ASGI app that returns a fixed response."""
    response_body = b'{"message": "Hello from Ignite!"}'
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
        ],
    })
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

    wrapped = Middleware(sample_app)
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}

    asyncio.run(wrapped(scope, mock_receive, mock_send))

    assert len(captured) == 2
    assert captured[0]["status"] == 200
    assert captured[1]["body"] == b'{"message": "Hello from Ignite!"}'
    print(f"  Base middleware passes through: status={captured[0]['status']}")
    print(f"  Response body: {captured[1]['body'].decode()}")
    print(f"  [VALID] Base middleware is transparent")


# ===========================================================================
# SECTION 3: Practical Middlewares
# ===========================================================================

class LoggingMiddleware(Middleware):
    """Logs each request method, path, and response status."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logs: list[str] = []

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        # TODO: Extract method and path from scope
        # TODO: Append f"{method} {path}" to self.logs
        # HINT: method = scope.get("method", "?")

        # TODO: Create a logging_send wrapper that captures status_code
        #       from "http.response.start" messages, then calls await send(message)
        # HINT: Use nonlocal status_code; check message.get("type")

        status_code = None

        async def logging_send(message: Message):
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        # TODO: Call self.app with scope, receive, and logging_send
        # TODO: After the call, append f"  -> {status_code}" to self.logs
        pass


class TimingMiddleware(Middleware):
    """Measures request processing time and adds X-Process-Time header."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.last_duration_ms: float = 0.0

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        # TODO: Record start time using time.perf_counter()

        # TODO: Create a timing_send wrapper that:
        #   - On "http.response.start", calculates elapsed time
        #   - Stores it in self.last_duration_ms
        #   - Adds (b"x-process-time", f"{elapsed:.2f}ms".encode()) to headers
        #   - Calls await send(message)
        # HINT: headers = list(message.get("headers", []))
        #       headers.append((...)); message = {**message, "headers": headers}

        # TODO: Call self.app with scope, receive, and timing_send
        pass


class CORSMiddleware(Middleware):
    """Adds Cross-Origin Resource Sharing headers."""

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
        # TODO: Return a list of (name, value) tuples for:
        #   - access-control-allow-origin
        #   - access-control-allow-methods
        #   - access-control-allow-headers
        # HINT: Join list items with ", " and encode to bytes
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
        # TODO: If scope method is "OPTIONS", short-circuit:
        #   - Send response.start with status 204 and CORS headers
        #   - Send response.body with empty body
        #   - Return early (don't call inner app)

        # TODO: For other methods, create cors_send wrapper that adds
        #       CORS headers to "http.response.start" messages
        # TODO: Call self.app with scope, receive, and cors_send
        pass


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
    """Composes multiple middlewares around an app."""

    def __init__(self, app: ASGIApp):
        self.app = app
        self._middleware_classes: list[tuple[type, dict]] = []

    def add(self, middleware_cls: type, **kwargs) -> "MiddlewareStack":
        """Add a middleware class (with optional kwargs) to the stack."""
        # TODO: Append (middleware_cls, kwargs) to self._middleware_classes
        # TODO: Return self for chaining
        pass

    def build(self) -> ASGIApp:
        """Build the composed app by wrapping middlewares outside-in.

        If we add [A, B, C], the call order is: A -> B -> C -> app.
        So we wrap in reverse: app = C(app), app = B(app), app = A(app).
        """
        # TODO: Start with app = self.app
        # TODO: Iterate over reversed(self._middleware_classes)
        # TODO: For each (cls, kwargs), wrap: app = cls(app, **kwargs)
        # TODO: Return the fully wrapped app
        pass


def demo_middleware_stack():
    """Demonstrate composing multiple middlewares."""
    captured: list[Message] = []

    async def mock_send(message: Message):
        captured.append(message)

    async def mock_receive():
        return {"type": "http.request", "body": b""}

    stack = MiddlewareStack(sample_app)
    stack.add(LoggingMiddleware)
    stack.add(TimingMiddleware)
    stack.add(CORSMiddleware, allow_origins=["*"])

    composed_app = stack.build()

    print(f"  Stack layers: Logging -> Timing -> CORS -> App")

    scope = {
        "type": "http", "method": "GET", "path": "/api/data",
        "headers": [],
    }
    asyncio.run(composed_app(scope, mock_receive, mock_send))

    start_msg = captured[0]
    header_dict = {h[0]: h[1] for h in start_msg["headers"]}
    print(f"  Response status: {start_msg['status']}")
    print(f"  Headers present: {[h[0].decode() for h in start_msg['headers']]}")

    assert b"x-process-time" in header_dict, "TimingMiddleware header missing"
    assert b"access-control-allow-origin" in header_dict, "CORS header missing"
    assert start_msg["status"] == 200

    assert isinstance(composed_app, LoggingMiddleware)
    print(f"  Logging captured: {composed_app.logs}")
    assert "GET /api/data" in composed_app.logs[0]

    print(f"  [VALID] Middleware stack composes correctly")


# ===========================================================================
# SECTION 5: Short-Circuit Middleware (Auth Example)
# ===========================================================================

class AuthMiddleware(Middleware):
    """Authentication middleware that short-circuits unauthorized requests."""

    def __init__(self, app: ASGIApp, valid_tokens: set[str] | None = None):
        super().__init__(app)
        self.valid_tokens = valid_tokens or {"secret-token-123"}

    async def __call__(self, scope: Scope, receive: Receive,
                       send: Send) -> None:
        # TODO: Extract the authorization header from scope["headers"]
        # HINT: headers = dict(scope.get("headers", []))
        #       token = headers.get(b"authorization", b"").decode()

        # TODO: If token not in self.valid_tokens, short-circuit:
        #   - Send response.start with status 401
        #   - Send response.body with b'{"error": "Unauthorized"}'
        #   - Return early

        # TODO: If token is valid, call self.app(scope, receive, send)
        pass


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
    try:
        demo_asgi_types()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 2: Base Middleware & The Onion Model ---")
    try:
        demo_base_middleware()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 3: Practical Middlewares ---")
    try:
        demo_practical_middlewares()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 4: Composing the Middleware Stack ---")
    try:
        demo_middleware_stack()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 5: Short-Circuit Middleware (Auth) ---")
    try:
        demo_auth_middleware()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
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
