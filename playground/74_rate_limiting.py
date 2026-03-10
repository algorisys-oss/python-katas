"""
Kata 74 -- Rate Limiting
Run: python playground/74_rate_limiting.py

Build rate limiting middleware for Ignite: sliding window algorithm per
client IP, X-RateLimit-* headers, 429 Too Many Requests, and per-route
rate limits.

Completes within 5 seconds.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Rate Limit Result
# ===========================================================================
# Every rate limit check produces a result that tells the caller whether
# the request is allowed and provides the standard X-RateLimit-* headers.

@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    limit: int          # Maximum requests per window
    remaining: int      # Requests remaining in current window
    reset_at: float     # Unix timestamp when the window resets
    retry_after: float = 0.0  # Seconds until the client can retry

    def headers(self) -> dict[str, str]:
        """Generate standard X-RateLimit-* response headers."""
        h = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }
        if not self.allowed:
            h["Retry-After"] = str(int(self.retry_after) + 1)
        return h


# ===========================================================================
# SECTION 2: Sliding Window Rate Limiter
# ===========================================================================
# The sliding window algorithm tracks timestamps of recent requests for
# each client. It counts how many requests fall within the current window
# and rejects requests that exceed the limit.

class SlidingWindowLimiter:
    """Rate limiter using a sliding window algorithm.

    For each client key (typically IP address), we store a list of request
    timestamps. On each check, we remove timestamps outside the window
    and count what remains.

    This is more accurate than fixed windows because there's no "boundary
    burst" problem where a client sends max requests at the end of one
    window and the start of the next.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, now: float | None = None) -> RateLimitResult:
        """Check if a request from key is allowed.

        Args:
            key: Client identifier (e.g. IP address).
            now: Current time (injectable for testing).

        Returns:
            RateLimitResult indicating if the request is allowed.
        """
        now = now or time.time()
        window_start = now - self.window_seconds

        # Prune old timestamps outside the window
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]
        timestamps = self._requests[key]

        remaining = self.max_requests - len(timestamps)
        reset_at = now + self.window_seconds

        if remaining > 0:
            # Allow request and record timestamp
            timestamps.append(now)
            return RateLimitResult(
                allowed=True,
                limit=self.max_requests,
                remaining=remaining - 1,  # -1 because we just used one
                reset_at=reset_at,
            )
        else:
            # Rate limit exceeded
            # Calculate when the oldest request in the window expires
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
        """Reset rate limit for a specific key."""
        self._requests.pop(key, None)

    def reset_all(self) -> None:
        """Reset all rate limits."""
        self._requests.clear()


# ===========================================================================
# SECTION 3: Per-Route Rate Limiting
# ===========================================================================
# Different routes can have different rate limits. A login endpoint might
# allow 5 requests/minute while a search endpoint allows 100/minute.

@dataclass
class RouteRateLimit:
    """Rate limit configuration for a specific route."""
    path: str
    max_requests: int
    window_seconds: float
    limiter: SlidingWindowLimiter = field(init=False)

    def __post_init__(self):
        self.limiter = SlidingWindowLimiter(self.max_requests, self.window_seconds)


class RateLimitManager:
    """Manages rate limits across multiple routes.

    Supports:
    - Global default rate limit
    - Per-route rate limits
    - Client identification by IP
    """

    def __init__(
        self,
        default_max_requests: int = 100,
        default_window_seconds: float = 60.0,
    ):
        self.default_limiter = SlidingWindowLimiter(
            default_max_requests, default_window_seconds
        )
        self._route_limits: dict[str, RouteRateLimit] = {}

    def add_route_limit(
        self,
        path: str,
        max_requests: int,
        window_seconds: float = 60.0,
    ) -> None:
        """Add a rate limit for a specific route."""
        self._route_limits[path] = RouteRateLimit(
            path=path,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    def check(
        self,
        client_ip: str,
        path: str,
        now: float | None = None,
    ) -> RateLimitResult:
        """Check rate limit for a client on a specific path."""
        # Use route-specific limiter if configured, else default
        route_limit = self._route_limits.get(path)
        if route_limit:
            key = f"{client_ip}:{path}"
            return route_limit.limiter.check(key, now)
        else:
            key = client_ip
            return self.default_limiter.check(key, now)


# ===========================================================================
# SECTION 4: Rate Limit Middleware
# ===========================================================================
# The middleware sits in the request pipeline, checks rate limits before
# calling the route handler, and adds headers to every response.

class Request:
    """Simulated HTTP request."""
    def __init__(self, method: str, path: str, client_ip: str = "127.0.0.1"):
        self.method = method
        self.path = path
        self.client_ip = client_ip


class Response:
    """Simulated HTTP response."""
    def __init__(
        self,
        body: dict[str, Any],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

    def __repr__(self) -> str:
        return f"Response(status={self.status_code}, headers={self.headers})"


class RateLimitMiddleware:
    """Middleware that enforces rate limits on incoming requests.

    Checks the rate limit before calling the next handler.
    Adds X-RateLimit-* headers to all responses.
    Returns 429 Too Many Requests when the limit is exceeded.
    """

    def __init__(self, manager: RateLimitManager):
        self.manager = manager

    def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Response],
    ) -> Response:
        """Process request through rate limiting."""
        result = self.manager.check(request.client_ip, request.path)

        if not result.allowed:
            # 429 Too Many Requests
            response = Response(
                body={
                    "error": {
                        "status_code": 429,
                        "detail": "Too Many Requests",
                        "retry_after": int(result.retry_after) + 1,
                    }
                },
                status_code=429,
            )
            response.headers.update(result.headers())
            return response

        # Request allowed -- call the next handler
        response = next_handler(request)
        # Add rate limit headers to successful responses too
        response.headers.update(result.headers())
        return response


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_rate_limit_result():
    """Show rate limit result and headers."""
    print("--- Section 1: Rate Limit Result ---")

    result = RateLimitResult(
        allowed=True, limit=100, remaining=95, reset_at=1700000060.0
    )
    headers = result.headers()
    print(f"  Allowed: {result.allowed}")
    print(f"  Headers: {headers}")
    assert headers["X-RateLimit-Limit"] == "100"
    assert headers["X-RateLimit-Remaining"] == "95"
    assert "Retry-After" not in headers  # only on 429

    blocked = RateLimitResult(
        allowed=False, limit=10, remaining=0,
        reset_at=1700000060.0, retry_after=30.5,
    )
    headers2 = blocked.headers()
    print(f"  Blocked headers: {headers2}")
    assert "Retry-After" in headers2

    print("  [PASS] Rate limit result works")


def demo_sliding_window():
    """Show sliding window algorithm."""
    print("\n--- Section 2: Sliding Window ---")

    limiter = SlidingWindowLimiter(max_requests=3, window_seconds=10.0)

    base_time = 1000.0

    # First 3 requests should be allowed
    for i in range(3):
        result = limiter.check("client-1", now=base_time + i)
        print(f"  Request {i + 1}: allowed={result.allowed}, remaining={result.remaining}")
        assert result.allowed is True

    # 4th request should be blocked
    result4 = limiter.check("client-1", now=base_time + 3)
    print(f"  Request 4: allowed={result4.allowed}, remaining={result4.remaining}")
    assert result4.allowed is False
    assert result4.remaining == 0

    # After window expires, requests are allowed again
    result5 = limiter.check("client-1", now=base_time + 11)
    print(f"  Request 5 (after window): allowed={result5.allowed}")
    assert result5.allowed is True

    # Different clients have separate limits
    result_c2 = limiter.check("client-2", now=base_time)
    print(f"  Client-2 first request: allowed={result_c2.allowed}")
    assert result_c2.allowed is True

    print("  [PASS] Sliding window works")


def demo_sliding_window_precision():
    """Show that sliding window avoids fixed-window boundary bursts."""
    print("\n--- Section 3: Sliding Window Precision ---")

    limiter = SlidingWindowLimiter(max_requests=5, window_seconds=10.0)
    base_time = 1000.0

    # Send 5 requests at t=8,9 (end of "first window")
    for i in range(5):
        t = base_time + 8 + (i * 0.1)
        limiter.check("client", now=t)

    # At t=10 (start of "next window" in fixed-window),
    # sliding window still counts the requests from t=8-9
    result = limiter.check("client", now=base_time + 10)
    print(f"  At t=10 (1s after last burst): allowed={result.allowed}")
    assert result.allowed is False  # Sliding window prevents boundary burst

    # At t=19 (all old requests expired), we can send again
    result2 = limiter.check("client", now=base_time + 19)
    print(f"  At t=19 (window expired): allowed={result2.allowed}")
    assert result2.allowed is True

    print("  [PASS] Sliding window prevents boundary bursts")


def demo_per_route_limits():
    """Show per-route rate limiting."""
    print("\n--- Section 4: Per-Route Rate Limits ---")

    manager = RateLimitManager(
        default_max_requests=100,
        default_window_seconds=60.0,
    )

    # Strict limit on login
    manager.add_route_limit("/auth/login", max_requests=3, window_seconds=60.0)
    # Moderate limit on search
    manager.add_route_limit("/search", max_requests=10, window_seconds=60.0)

    base_time = 1000.0

    # Login: should block after 3
    for i in range(3):
        r = manager.check("192.168.1.1", "/auth/login", now=base_time + i)
        assert r.allowed is True

    r_blocked = manager.check("192.168.1.1", "/auth/login", now=base_time + 4)
    print(f"  /auth/login after 3 requests: allowed={r_blocked.allowed}")
    assert r_blocked.allowed is False

    # Same client on /search still has quota
    r_search = manager.check("192.168.1.1", "/search", now=base_time)
    print(f"  /search (separate limit): allowed={r_search.allowed}")
    assert r_search.allowed is True

    # Default route uses global limit (100/min)
    r_default = manager.check("192.168.1.1", "/api/users", now=base_time)
    print(f"  /api/users (default limit): allowed={r_default.allowed}")
    assert r_default.allowed is True

    print("  [PASS] Per-route rate limits work")


def demo_middleware():
    """Show rate limiting middleware in action."""
    print("\n--- Section 5: Rate Limit Middleware ---")

    manager = RateLimitManager(default_max_requests=3, default_window_seconds=60.0)
    middleware = RateLimitMiddleware(manager)

    def handler(request: Request) -> Response:
        return Response(body={"message": "OK"}, status_code=200)

    base_time = 1000.0

    # Send requests through middleware
    for i in range(4):
        req = Request("GET", "/api/data", client_ip="10.0.0.1")
        # Inject time by directly checking manager
        result = manager.check("10.0.0.1", "/api/data", now=base_time + i)
        if result.allowed:
            resp = Response(body={"message": "OK"}, status_code=200)
            resp.headers.update(result.headers())
        else:
            resp = Response(
                body={"error": {"status_code": 429, "detail": "Too Many Requests"}},
                status_code=429,
            )
            resp.headers.update(result.headers())

        if i < 3:
            print(f"  Request {i + 1}: status={resp.status_code}, "
                  f"remaining={resp.headers.get('X-RateLimit-Remaining')}")
            assert resp.status_code == 200
        else:
            print(f"  Request {i + 1}: status={resp.status_code} "
                  f"(Retry-After={resp.headers.get('Retry-After')})")
            assert resp.status_code == 429

    print("  [PASS] Rate limit middleware works")


def demo_middleware_integration():
    """Show full middleware integration with handler chain."""
    print("\n--- Section 6: Full Middleware Integration ---")

    manager = RateLimitManager(default_max_requests=2, default_window_seconds=10.0)
    middleware = RateLimitMiddleware(manager)

    call_count = 0

    def handler(request: Request) -> Response:
        nonlocal call_count
        call_count += 1
        return Response(body={"data": "hello"}, status_code=200)

    # Two requests should reach the handler
    resp1 = middleware.process(Request("GET", "/api", "1.2.3.4"), handler)
    resp2 = middleware.process(Request("GET", "/api", "1.2.3.4"), handler)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert "X-RateLimit-Remaining" in resp1.headers
    print(f"  Request 1: {resp1.status_code}, remaining={resp1.headers['X-RateLimit-Remaining']}")
    print(f"  Request 2: {resp2.status_code}, remaining={resp2.headers['X-RateLimit-Remaining']}")

    # Third request should be blocked (handler never called)
    resp3 = middleware.process(Request("GET", "/api", "1.2.3.4"), handler)
    assert resp3.status_code == 429
    assert call_count == 2  # Handler was only called twice
    print(f"  Request 3: {resp3.status_code} (handler not called, call_count={call_count})")
    print(f"  429 body: {resp3.body}")

    # Different IP is not affected
    resp4 = middleware.process(Request("GET", "/api", "5.6.7.8"), handler)
    assert resp4.status_code == 200
    print(f"  Request from 5.6.7.8: {resp4.status_code} (different client)")

    print("  [PASS] Full middleware integration works")


def demo_reset():
    """Show resetting rate limits."""
    print("\n--- Section 7: Reset ---")

    limiter = SlidingWindowLimiter(max_requests=2, window_seconds=60.0)

    limiter.check("client-1")
    limiter.check("client-1")
    result = limiter.check("client-1")
    assert result.allowed is False
    print(f"  After 2 requests: allowed={result.allowed}")

    limiter.reset("client-1")
    result2 = limiter.check("client-1")
    assert result2.allowed is True
    print(f"  After reset: allowed={result2.allowed}")

    print("  [PASS] Reset works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_rate_limit_result()
    demo_sliding_window()
    demo_sliding_window_precision()
    demo_per_route_limits()
    demo_middleware()
    demo_middleware_integration()
    demo_reset()

    print("\n--- Summary ---")
    print("Rate limiting gives our Ignite framework:")
    print("  - Sliding window algorithm per client IP")
    print("  - X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers")
    print("  - 429 Too Many Requests with Retry-After header")
    print("  - Per-route rate limit configuration")
    print("  - Rate limit middleware in the request pipeline")
    print("  - Reset capability for testing and admin")
    print("\nAll 7 sections passed. Rate limiting mastered!")
    print("Next up: Kata 75 -- background tasks!")


if __name__ == "__main__":
    main()
