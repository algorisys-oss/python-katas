"""
Kata 64 -- CORS Middleware
Run: python playground/skeletons/64_cors_middleware.py

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
        # TODO: Return True if "*" is in self.allow_origins OR
        #       if origin is in self.allow_origins
        pass

    def is_method_allowed(self, method: str) -> bool:
        """Check if the HTTP method is allowed for CORS."""
        # TODO: Check if method.upper() is in self.allow_methods (case-insensitive)
        pass


# ===========================================================================
# SECTION 3: CORS Middleware
# ===========================================================================

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

        # TODO: If no Origin header, pass through to self.handler (not CORS)

        # TODO: If origin is not allowed, pass through without CORS headers

        # TODO: If this is a preflight request (OPTIONS with
        #       Access-Control-Request-Method header), call _handle_preflight

        # TODO: Otherwise, call self.handler, add CORS headers, return
        pass

    def _handle_preflight(self, request: Request, origin: str) -> Response:
        """Handle a CORS preflight (OPTIONS) request.

        Returns 204 No Content with all the CORS headers.
        """
        response = Response(status_code=204)

        # TODO: Check if the requested method is allowed
        # requested_method = request.get_header("access-control-request-method")
        # If not allowed, return 204 without CORS headers

        # TODO: Add CORS headers with self._add_cors_headers(response, origin)

        # TODO: Add preflight-specific headers:
        #   Access-Control-Allow-Methods: comma-separated list
        #   Access-Control-Allow-Headers: comma-separated list
        #   Access-Control-Max-Age: self.config.max_age as string

        return response

    def _add_cors_headers(self, response: Response, origin: str) -> None:
        """Add CORS headers to any response (preflight or actual).

        Key rule: if credentials are allowed, we CANNOT use "*" for
        Access-Control-Allow-Origin -- we must echo the specific origin.
        """
        # TODO: Set Access-Control-Allow-Origin header
        # If credentials enabled or origins are not wildcard:
        #   - Set to the specific origin, add Vary: Origin
        # Else:
        #   - Set to "*"

        # TODO: If credentials enabled, set Access-Control-Allow-Credentials: true

        # TODO: If expose_headers configured, set Access-Control-Expose-Headers
        pass


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
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_preflight():
    """Show preflight (OPTIONS) handling."""
    print("\n--- Section 2: Preflight Handling ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_actual_requests():
    """Show CORS headers on actual (non-preflight) requests."""
    print("\n--- Section 3: Actual Requests ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_wildcard():
    """Show wildcard origin behavior."""
    print("\n--- Section 4: Wildcard Origin ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_credentials():
    """Show CORS with credentials (cookies/auth)."""
    print("\n--- Section 5: Credentials Mode ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_full_flow():
    """Show complete preflight + actual request flow."""
    print("\n--- Section 6: Full CORS Flow ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


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
