"""
Kata 64 -- CORS Middleware
Run: python playground/64_cors_middleware.py

Build CORS middleware for Ignite. Handle preflight OPTIONS requests.
Configurable allowed origins (including wildcard), methods, headers.
Add Access-Control-* response headers. Support credentials mode.

Completes within 5 seconds.
"""

from __future__ import annotations

from typing import Any, Callable


# ===========================================================================
# SECTION 1: Request / Response
# ===========================================================================
# Simplified request/response objects for demonstrating CORS logic.

class Request:
    """Simulated HTTP request with headers."""

    def __init__(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
    ):
        self.method = method.upper()
        self.path = path
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}

    def get_header(self, name: str) -> str | None:
        """Get a request header (case-insensitive)."""
        return self.headers.get(name.lower())


class Response:
    """Simulated HTTP response with headers."""

    def __init__(self, body: Any = None, status_code: int = 200):
        self.body = body
        self.status_code = status_code
        self.headers: dict[str, str] = {}

    def set_header(self, name: str, value: str) -> None:
        self.headers[name] = value

    def __repr__(self) -> str:
        return f"Response(status={self.status_code}, headers={self.headers})"


# ===========================================================================
# SECTION 2: CORS Configuration
# ===========================================================================
# CORSConfig holds all configurable CORS settings.
# These map directly to the Access-Control-* response headers.

class CORSConfig:
    """Configuration for CORS middleware.

    Attributes:
        allow_origins: Origins that are allowed ("*" for all, or list of specific origins)
        allow_methods: HTTP methods allowed for CORS requests
        allow_headers: Request headers allowed in CORS requests
        expose_headers: Response headers that browsers can access
        allow_credentials: Whether to allow cookies/auth headers in CORS requests
        max_age: How long preflight results can be cached (seconds)
    """

    def __init__(
        self,
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        self.allow_headers = allow_headers or ["Content-Type", "Authorization"]
        self.expose_headers = expose_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def is_origin_allowed(self, origin: str) -> bool:
        """Check if the given origin is allowed.

        "*" means all origins are allowed (but incompatible with credentials).
        Otherwise, check if the origin is in the allow list.
        """
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins

    def is_method_allowed(self, method: str) -> bool:
        """Check if the HTTP method is allowed for CORS."""
        return method.upper() in [m.upper() for m in self.allow_methods]


# ===========================================================================
# SECTION 3: CORS Middleware
# ===========================================================================
# The middleware intercepts requests and adds CORS headers.
# Preflight (OPTIONS) requests get a special response.

class CORSMiddleware:
    """CORS middleware that handles preflight and adds response headers.

    Preflight flow (browser sends OPTIONS before the real request):
    1. Browser sends OPTIONS with Origin, Access-Control-Request-Method
    2. Middleware checks origin and method against config
    3. Returns 204 with Access-Control-Allow-* headers
    4. Browser sends the real request if preflight succeeds

    Simple/actual request flow:
    1. Browser sends request with Origin header
    2. Middleware adds Access-Control-Allow-Origin to response
    3. Browser checks if origin is allowed
    """

    def __init__(self, handler: Callable[[Request], Response], config: CORSConfig):
        self.handler = handler
        self.config = config

    def __call__(self, request: Request) -> Response:
        """Process a request through CORS logic."""
        origin = request.get_header("origin")

        # No Origin header = not a CORS request, pass through
        if not origin:
            return self.handler(request)

        # Check if origin is allowed
        if not self.config.is_origin_allowed(origin):
            # Origin not allowed -- return response without CORS headers
            # The browser will block the response
            return self.handler(request)

        # Is this a preflight request?
        if request.method == "OPTIONS" and request.get_header("access-control-request-method"):
            return self._handle_preflight(request, origin)

        # Actual CORS request -- process and add headers
        response = self.handler(request)
        self._add_cors_headers(response, origin)
        return response

    def _handle_preflight(self, request: Request, origin: str) -> Response:
        """Handle a CORS preflight (OPTIONS) request.

        Returns 204 No Content with all the CORS headers the browser needs
        to decide whether to send the actual request.
        """
        response = Response(status_code=204)

        # Check if the requested method is allowed
        requested_method = request.get_header("access-control-request-method")
        if requested_method and not self.config.is_method_allowed(requested_method):
            # Method not allowed -- return 204 without CORS headers
            return response

        self._add_cors_headers(response, origin)

        # Preflight-specific headers
        response.set_header(
            "Access-Control-Allow-Methods",
            ", ".join(self.config.allow_methods),
        )
        response.set_header(
            "Access-Control-Allow-Headers",
            ", ".join(self.config.allow_headers),
        )
        response.set_header(
            "Access-Control-Max-Age",
            str(self.config.max_age),
        )

        return response

    def _add_cors_headers(self, response: Response, origin: str) -> None:
        """Add CORS headers to any response (preflight or actual).

        Key rule: if credentials are allowed, we CANNOT use "*" for
        Access-Control-Allow-Origin -- we must echo the specific origin.
        """
        # Set the allowed origin
        if self.config.allow_credentials or "*" not in self.config.allow_origins:
            # Must echo the specific origin
            response.set_header("Access-Control-Allow-Origin", origin)
            # Vary header tells caches the response depends on Origin
            response.set_header("Vary", "Origin")
        else:
            # Wildcard origin
            response.set_header("Access-Control-Allow-Origin", "*")

        # Credentials
        if self.config.allow_credentials:
            response.set_header("Access-Control-Allow-Credentials", "true")

        # Expose headers (which response headers JS can read)
        if self.config.expose_headers:
            response.set_header(
                "Access-Control-Expose-Headers",
                ", ".join(self.config.expose_headers),
            )


# ===========================================================================
# SECTION 4: Demos
# ===========================================================================

def make_handler(body: Any = None, status: int = 200) -> Callable[[Request], Response]:
    """Create a simple request handler that returns a fixed response."""
    def handler(request: Request) -> Response:
        return Response(body=body or {"ok": True}, status_code=status)
    return handler


def demo_cors_config():
    """Show CORS configuration."""
    print("--- Section 1: CORS Configuration ---")

    # Default config (allow all origins)
    config = CORSConfig()
    assert config.is_origin_allowed("https://example.com")
    assert config.is_origin_allowed("http://localhost:3000")
    assert config.is_method_allowed("GET")
    assert config.is_method_allowed("DELETE")
    print("  Default config: all origins allowed")

    # Restricted origins
    config2 = CORSConfig(
        allow_origins=["https://myapp.com", "https://staging.myapp.com"],
        allow_methods=["GET", "POST"],
    )
    assert config2.is_origin_allowed("https://myapp.com")
    assert not config2.is_origin_allowed("https://evil.com")
    assert config2.is_method_allowed("GET")
    assert not config2.is_method_allowed("DELETE")
    print("  Restricted config: only specific origins/methods")

    print("  [PASS] CORS configuration works")


def demo_preflight():
    """Show preflight (OPTIONS) handling."""
    print("\n--- Section 2: Preflight Handling ---")

    config = CORSConfig(
        allow_origins=["https://myapp.com"],
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "Authorization", "X-Custom"],
        max_age=3600,
    )
    middleware = CORSMiddleware(make_handler(), config)

    # Preflight for a POST request
    req = Request("OPTIONS", "/api/data", headers={
        "Origin": "https://myapp.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    })
    resp = middleware(req)
    print(f"  Preflight response: status={resp.status_code}")
    print(f"  Headers: {resp.headers}")

    assert resp.status_code == 204
    assert resp.headers["Access-Control-Allow-Origin"] == "https://myapp.com"
    assert "POST" in resp.headers["Access-Control-Allow-Methods"]
    assert "Content-Type" in resp.headers["Access-Control-Allow-Headers"]
    assert resp.headers["Access-Control-Max-Age"] == "3600"

    # Preflight from disallowed origin
    req2 = Request("OPTIONS", "/api/data", headers={
        "Origin": "https://evil.com",
        "Access-Control-Request-Method": "POST",
    })
    resp2 = middleware(req2)
    print(f"  Disallowed origin: no CORS headers")
    assert "Access-Control-Allow-Origin" not in resp2.headers

    # Preflight with disallowed method
    req3 = Request("OPTIONS", "/api/data", headers={
        "Origin": "https://myapp.com",
        "Access-Control-Request-Method": "DELETE",
    })
    resp3 = middleware(req3)
    print(f"  Disallowed method (DELETE): status={resp3.status_code}")
    assert "Access-Control-Allow-Origin" not in resp3.headers

    print("  [PASS] Preflight handling works")


def demo_actual_requests():
    """Show CORS headers on actual (non-preflight) requests."""
    print("\n--- Section 3: Actual Requests ---")

    config = CORSConfig(
        allow_origins=["https://myapp.com"],
        expose_headers=["X-Request-Id", "X-Rate-Limit"],
    )
    middleware = CORSMiddleware(make_handler({"data": "hello"}), config)

    # CORS request with allowed origin
    req = Request("GET", "/api/data", headers={"Origin": "https://myapp.com"})
    resp = middleware(req)
    print(f"  Allowed: {resp.headers}")
    assert resp.headers["Access-Control-Allow-Origin"] == "https://myapp.com"
    assert "X-Request-Id" in resp.headers["Access-Control-Expose-Headers"]
    assert resp.body == {"data": "hello"}

    # CORS request from disallowed origin
    req2 = Request("GET", "/api/data", headers={"Origin": "https://evil.com"})
    resp2 = middleware(req2)
    print(f"  Disallowed origin: CORS headers absent")
    assert "Access-Control-Allow-Origin" not in resp2.headers

    # Non-CORS request (no Origin header)
    req3 = Request("GET", "/api/data")
    resp3 = middleware(req3)
    print(f"  No Origin: passed through, no CORS headers")
    assert "Access-Control-Allow-Origin" not in resp3.headers
    assert resp3.body == {"data": "hello"}

    print("  [PASS] Actual request handling works")


def demo_wildcard():
    """Show wildcard origin behavior."""
    print("\n--- Section 4: Wildcard Origin ---")

    config = CORSConfig(allow_origins=["*"])
    middleware = CORSMiddleware(make_handler(), config)

    # Any origin is allowed with wildcard
    req = Request("GET", "/api", headers={"Origin": "https://anywhere.com"})
    resp = middleware(req)
    print(f"  Wildcard: {resp.headers['Access-Control-Allow-Origin']}")
    assert resp.headers["Access-Control-Allow-Origin"] == "*"
    # No Vary header with wildcard
    assert "Vary" not in resp.headers

    print("  [PASS] Wildcard origin works")


def demo_credentials():
    """Show CORS with credentials (cookies/auth)."""
    print("\n--- Section 5: Credentials Mode ---")

    config = CORSConfig(
        allow_origins=["https://myapp.com"],
        allow_credentials=True,
    )
    middleware = CORSMiddleware(make_handler(), config)

    # With credentials, must echo specific origin (not "*")
    req = Request("GET", "/api", headers={"Origin": "https://myapp.com"})
    resp = middleware(req)
    print(f"  Origin: {resp.headers['Access-Control-Allow-Origin']}")
    print(f"  Credentials: {resp.headers.get('Access-Control-Allow-Credentials')}")
    assert resp.headers["Access-Control-Allow-Origin"] == "https://myapp.com"
    assert resp.headers["Access-Control-Allow-Credentials"] == "true"
    assert resp.headers["Vary"] == "Origin"  # Must vary on origin

    # Preflight with credentials
    req2 = Request("OPTIONS", "/api", headers={
        "Origin": "https://myapp.com",
        "Access-Control-Request-Method": "POST",
    })
    resp2 = middleware(req2)
    assert resp2.headers["Access-Control-Allow-Credentials"] == "true"
    print("  Preflight with credentials: correct headers set")

    print("  [PASS] Credentials mode works")


def demo_full_flow():
    """Show complete preflight + actual request flow."""
    print("\n--- Section 6: Full CORS Flow ---")

    config = CORSConfig(
        allow_origins=["https://spa.example.com"],
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["X-Request-Id"],
        allow_credentials=True,
        max_age=7200,
    )

    def api_handler(request: Request) -> Response:
        return Response(body={"users": ["alice", "bob"]}, status_code=200)

    middleware = CORSMiddleware(api_handler, config)

    # Step 1: Browser sends preflight
    preflight = Request("OPTIONS", "/api/users", headers={
        "Origin": "https://spa.example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization",
    })
    pf_resp = middleware(preflight)
    print(f"  1. Preflight: status={pf_resp.status_code}")
    print(f"     Allow-Origin: {pf_resp.headers['Access-Control-Allow-Origin']}")
    print(f"     Allow-Methods: {pf_resp.headers['Access-Control-Allow-Methods']}")
    print(f"     Max-Age: {pf_resp.headers['Access-Control-Max-Age']}")
    assert pf_resp.status_code == 204

    # Step 2: Browser sends actual request
    actual = Request("POST", "/api/users", headers={
        "Origin": "https://spa.example.com",
        "Content-Type": "application/json",
    })
    act_resp = middleware(actual)
    print(f"  2. Actual: status={act_resp.status_code}")
    print(f"     Allow-Origin: {act_resp.headers['Access-Control-Allow-Origin']}")
    print(f"     Expose-Headers: {act_resp.headers['Access-Control-Expose-Headers']}")
    assert act_resp.status_code == 200
    assert act_resp.body == {"users": ["alice", "bob"]}

    print("  [PASS] Full CORS flow works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_cors_config()
    demo_preflight()
    demo_actual_requests()
    demo_wildcard()
    demo_credentials()
    demo_full_flow()

    print("\n--- Summary ---")
    print("CORS middleware gives our Ignite framework:")
    print("  - Configurable allowed origins, methods, headers")
    print("  - Preflight (OPTIONS) request handling with 204 response")
    print("  - Access-Control-Allow-* response headers")
    print("  - Wildcard origin support")
    print("  - Credentials mode (cookies/auth in cross-origin requests)")
    print("  - Expose-Headers for custom response headers")
    print("  - Max-Age caching for preflight responses")
    print("\nAll 6 sections passed. CORS middleware mastered!")
    print("Next up: Kata 65 -- CSRF protection!")


if __name__ == "__main__":
    main()
