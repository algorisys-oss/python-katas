"""
Ignite Rate Limiting Middleware

Sliding-window rate limiter that tracks per-client request timestamps,
enforces configurable limits, and returns standard ``X-RateLimit-*``
response headers.

Imports from sibling ignite modules: middleware, request, response.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

from ignite.middleware import Middleware
from ignite.request import Request
from ignite.response import JSONResponse


# ---------------------------------------------------------------------------
# Rate limit result
# ---------------------------------------------------------------------------

@dataclass
class RateLimitResult:
    """Outcome of a single rate-limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: float = 0.0

    def headers(self) -> dict[str, str]:
        """Standard ``X-RateLimit-*`` response headers."""
        h: dict[str, str] = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }
        if not self.allowed:
            h["Retry-After"] = str(int(self.retry_after) + 1)
        return h


# ---------------------------------------------------------------------------
# Sliding-window limiter
# ---------------------------------------------------------------------------

class SlidingWindowLimiter:
    """Per-key sliding-window rate limiter.

    Stores a list of request timestamps per key and prunes entries
    outside the current window on every check.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, now: float | None = None) -> RateLimitResult:
        now = now or time.time()
        window_start = now - self.window_seconds

        # Prune expired timestamps
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]
        timestamps = self._requests[key]

        remaining = self.max_requests - len(timestamps)
        reset_at = now + self.window_seconds

        if remaining > 0:
            timestamps.append(now)
            return RateLimitResult(
                allowed=True,
                limit=self.max_requests,
                remaining=remaining - 1,
                reset_at=reset_at,
            )

        oldest = timestamps[0] if timestamps else now
        retry_after = oldest + self.window_seconds - now
        return RateLimitResult(
            allowed=False,
            limit=self.max_requests,
            remaining=0,
            reset_at=reset_at,
            retry_after=max(0.0, retry_after),
        )

    def reset(self, key: str) -> None:
        self._requests.pop(key, None)

    def reset_all(self) -> None:
        self._requests.clear()


# ---------------------------------------------------------------------------
# Rate limit middleware (ASGI)
# ---------------------------------------------------------------------------

class RateLimitMiddleware(Middleware):
    """ASGI middleware that enforces a sliding-window rate limit.

    Identifies clients by their IP address (from the ASGI ``client``
    tuple).  Returns ``429 Too Many Requests`` with appropriate headers
    when the limit is exceeded; otherwise injects ``X-RateLimit-*``
    headers into the downstream response.
    """

    def __init__(
        self,
        app: Any,
        *,
        max_requests: int = 100,
        window_seconds: float = 60.0,
    ) -> None:
        super().__init__(app)
        self.limiter = SlidingWindowLimiter(max_requests, window_seconds)

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Determine client key
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        result = self.limiter.check(client_ip)

        if not result.allowed:
            response = JSONResponse(
                {
                    "error": {
                        "status_code": 429,
                        "detail": "Too Many Requests",
                        "retry_after": int(result.retry_after) + 1,
                    }
                },
                status_code=429,
                headers=result.headers(),
            )
            await response(scope, receive, send)
            return

        # Inject rate-limit headers into the downstream response
        extra_headers = result.headers()

        async def send_with_headers(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in extra_headers.items():
                    headers.append((key.lower().encode(), value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
