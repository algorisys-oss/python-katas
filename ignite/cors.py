"""
Ignite CORS Middleware

Configurable Cross-Origin Resource Sharing middleware with preflight
handling, origin validation, credential support, and expose headers.

Imports from sibling ignite modules: middleware, request, response.
"""

from __future__ import annotations

from typing import Any, Callable

from ignite.middleware import Middleware
from ignite.request import Request
from ignite.response import Response


# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------

class CORSConfig:
    """Holds all configurable CORS settings.

    Attributes:
        allow_origins:  Allowed origins (``["*"]`` for any).
        allow_methods:  HTTP methods permitted in CORS requests.
        allow_headers:  Request headers the client may send.
        expose_headers: Response headers the browser may read.
        allow_credentials: Whether cookies/auth are allowed.
        max_age:        Preflight cache duration in seconds.
    """

    def __init__(
        self,
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
    ) -> None:
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS",
        ]
        self.allow_headers = allow_headers or [
            "Content-Type", "Authorization",
        ]
        self.expose_headers = expose_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def is_origin_allowed(self, origin: str) -> bool:
        """Return ``True`` if *origin* is in the allow-list (or ``*``)."""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins

    def is_method_allowed(self, method: str) -> bool:
        """Return ``True`` if *method* is permitted."""
        return method.upper() in [m.upper() for m in self.allow_methods]


# ---------------------------------------------------------------------------
# CORSMiddleware
# ---------------------------------------------------------------------------

class CORSMiddleware(Middleware):
    """CORS middleware that handles preflight and adds response headers.

    Preflight flow (browser sends ``OPTIONS`` before the real request):

    1. Browser sends OPTIONS with ``Origin`` and
       ``Access-Control-Request-Method``.
    2. Middleware checks origin and method against configuration.
    3. Returns 204 with ``Access-Control-Allow-*`` headers.
    4. Browser proceeds with the actual request if preflight succeeds.

    Actual-request flow:

    1. Browser sends a request with an ``Origin`` header.
    2. Middleware adds ``Access-Control-Allow-Origin`` to the response.
    3. Browser checks whether the origin is allowed.
    """

    def __init__(
        self,
        app: Any,
        config: CORSConfig | None = None,
        *,
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
    ) -> None:
        super().__init__(app)
        if config is not None:
            self.config = config
        else:
            self.config = CORSConfig(
                allow_origins=allow_origins,
                allow_methods=allow_methods,
                allow_headers=allow_headers,
                expose_headers=expose_headers,
                allow_credentials=allow_credentials,
                max_age=max_age,
            )

    # -- ASGI interface ------------------------------------------------------

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        origin = request.headers.get("origin", "")

        # No Origin header => not a CORS request -- pass through.
        if not origin:
            await self.app(scope, receive, send)
            return

        # Origin not allowed => pass through without CORS headers.
        if not self.config.is_origin_allowed(origin):
            await self.app(scope, receive, send)
            return

        # Preflight?
        if (
            request.method == "OPTIONS"
            and "access-control-request-method" in request.headers
        ):
            response = self._preflight_response(request, origin)
            await response(scope, receive, send)
            return

        # Actual CORS request -- wrap send to inject headers.
        cors_headers = self._build_cors_headers(origin)

        async def send_with_cors(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in cors_headers.items():
                    headers.append(
                        (key.lower().encode(), value.encode())
                    )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_cors)

    # -- Helpers -------------------------------------------------------------

    def _preflight_response(self, request: Request, origin: str) -> Response:
        """Build the 204 preflight response."""
        requested_method = request.headers.get(
            "access-control-request-method", ""
        )
        if requested_method and not self.config.is_method_allowed(
            requested_method
        ):
            return Response(status_code=204)

        headers = self._build_cors_headers(origin)
        headers["Access-Control-Allow-Methods"] = ", ".join(
            self.config.allow_methods
        )
        headers["Access-Control-Allow-Headers"] = ", ".join(
            self.config.allow_headers
        )
        headers["Access-Control-Max-Age"] = str(self.config.max_age)

        return Response(status_code=204, headers=headers)

    def _build_cors_headers(self, origin: str) -> dict[str, str]:
        """Return the common CORS headers for a given *origin*."""
        headers: dict[str, str] = {}

        if (
            self.config.allow_credentials
            or "*" not in self.config.allow_origins
        ):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        else:
            headers["Access-Control-Allow-Origin"] = "*"

        if self.config.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        if self.config.expose_headers:
            headers["Access-Control-Expose-Headers"] = ", ".join(
                self.config.expose_headers
            )

        return headers
