"""
Kata 74 -- Rate Limiting
Run: python playground/skeletons/74_rate_limiting.py

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

@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: float = 0.0

    def headers(self) -> dict[str, str]:
        """Generate standard X-RateLimit-* response headers."""
        # TODO: Return a dict with:
        #   "X-RateLimit-Limit": str(self.limit)
        #   "X-RateLimit-Remaining": str(max(0, self.remaining))
        #   "X-RateLimit-Reset": str(int(self.reset_at))
        # If not self.allowed, also add "Retry-After": str(int(self.retry_after) + 1)
        pass


# ===========================================================================
# SECTION 2: Sliding Window Rate Limiter
# ===========================================================================

class SlidingWindowLimiter:
    """Rate limiter using a sliding window algorithm.

    For each client key, we store a list of request timestamps.
    On each check, we remove timestamps outside the window and count
    what remains.
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, now: float | None = None) -> RateLimitResult:
        """Check if a request from key is allowed."""
        now = now or time.time()
        window_start = now - self.window_seconds

        # TODO: Prune old timestamps outside the window
        # self._requests[key] = [t for t in timestamps if t > window_start]
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > window_start]
        timestamps = self._requests[key]

        remaining = self.max_requests - len(timestamps)
        reset_at = now + self.window_seconds

        # TODO: If remaining > 0:
        #   - Append current timestamp to timestamps
        #   - Return RateLimitResult(allowed=True, remaining=remaining-1, ...)
        # Else:
        #   - Calculate retry_after from oldest timestamp
        #   - Return RateLimitResult(allowed=False, remaining=0, ...)
        pass

    def reset(self, key: str) -> None:
        """Reset rate limit for a specific key."""
        self._requests.pop(key, None)

    def reset_all(self) -> None:
        """Reset all rate limits."""
        self._requests.clear()


# ===========================================================================
# SECTION 3: Per-Route Rate Limiting
# ===========================================================================

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
    """Manages rate limits across multiple routes."""

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
        # TODO: Create a RouteRateLimit and store it in self._route_limits
        pass

    def check(
        self,
        client_ip: str,
        path: str,
        now: float | None = None,
    ) -> RateLimitResult:
        """Check rate limit for a client on a specific path."""
        # TODO: Look up route-specific limiter in self._route_limits
        # If found, use key = f"{client_ip}:{path}" and check route limiter
        # Otherwise, use key = client_ip and check self.default_limiter
        pass


# ===========================================================================
# SECTION 4: Rate Limit Middleware
# ===========================================================================

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
    """Middleware that enforces rate limits on incoming requests."""

    def __init__(self, manager: RateLimitManager):
        self.manager = manager

    def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Response],
    ) -> Response:
        """Process request through rate limiting."""
        # TODO:
        # 1. Check rate limit: self.manager.check(request.client_ip, request.path)
        # 2. If not allowed: return 429 Response with error body and rate limit headers
        # 3. If allowed: call next_handler(request), add rate limit headers, return
        pass


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_rate_limit_result():
    """Show rate limit result and headers."""
    print("--- Section 1: Rate Limit Result ---")

    try:
        result = RateLimitResult(
            allowed=True, limit=100, remaining=95, reset_at=1700000060.0
        )
        headers = result.headers()
        print(f"  Allowed: {result.allowed}")
        print(f"  Headers: {headers}")
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "95"
        assert "Retry-After" not in headers

        blocked = RateLimitResult(
            allowed=False, limit=10, remaining=0,
            reset_at=1700000060.0, retry_after=30.5,
        )
        headers2 = blocked.headers()
        print(f"  Blocked headers: {headers2}")
        assert "Retry-After" in headers2

        print("  [PASS] Rate limit result works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_sliding_window():
    """Show sliding window algorithm."""
    print("\n--- Section 2: Sliding Window ---")

    try:
        limiter = SlidingWindowLimiter(max_requests=3, window_seconds=10.0)

        base_time = 1000.0

        for i in range(3):
            result = limiter.check("client-1", now=base_time + i)
            print(f"  Request {i + 1}: allowed={result.allowed}, remaining={result.remaining}")
            assert result.allowed is True

        result4 = limiter.check("client-1", now=base_time + 3)
        print(f"  Request 4: allowed={result4.allowed}, remaining={result4.remaining}")
        assert result4.allowed is False
        assert result4.remaining == 0

        result5 = limiter.check("client-1", now=base_time + 11)
        print(f"  Request 5 (after window): allowed={result5.allowed}")
        assert result5.allowed is True

        result_c2 = limiter.check("client-2", now=base_time)
        print(f"  Client-2 first request: allowed={result_c2.allowed}")
        assert result_c2.allowed is True

        print("  [PASS] Sliding window works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_sliding_window_precision():
    """Show that sliding window avoids fixed-window boundary bursts."""
    print("\n--- Section 3: Sliding Window Precision ---")

    try:
        limiter = SlidingWindowLimiter(max_requests=5, window_seconds=10.0)
        base_time = 1000.0

        for i in range(5):
            t = base_time + 8 + (i * 0.1)
            limiter.check("client", now=t)

        result = limiter.check("client", now=base_time + 10)
        print(f"  At t=10 (1s after last burst): allowed={result.allowed}")
        assert result.allowed is False

        result2 = limiter.check("client", now=base_time + 19)
        print(f"  At t=19 (window expired): allowed={result2.allowed}")
        assert result2.allowed is True

        print("  [PASS] Sliding window prevents boundary bursts")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_per_route_limits():
    """Show per-route rate limiting."""
    print("\n--- Section 4: Per-Route Rate Limits ---")

    try:
        manager = RateLimitManager(
            default_max_requests=100,
            default_window_seconds=60.0,
        )

        manager.add_route_limit("/auth/login", max_requests=3, window_seconds=60.0)
        manager.add_route_limit("/search", max_requests=10, window_seconds=60.0)

        base_time = 1000.0

        for i in range(3):
            r = manager.check("192.168.1.1", "/auth/login", now=base_time + i)
            assert r.allowed is True

        r_blocked = manager.check("192.168.1.1", "/auth/login", now=base_time + 4)
        print(f"  /auth/login after 3 requests: allowed={r_blocked.allowed}")
        assert r_blocked.allowed is False

        r_search = manager.check("192.168.1.1", "/search", now=base_time)
        print(f"  /search (separate limit): allowed={r_search.allowed}")
        assert r_search.allowed is True

        r_default = manager.check("192.168.1.1", "/api/users", now=base_time)
        print(f"  /api/users (default limit): allowed={r_default.allowed}")
        assert r_default.allowed is True

        print("  [PASS] Per-route rate limits work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_middleware():
    """Show rate limiting middleware in action."""
    print("\n--- Section 5: Rate Limit Middleware ---")

    try:
        manager = RateLimitManager(default_max_requests=3, default_window_seconds=60.0)
        middleware = RateLimitMiddleware(manager)

        def handler(request: Request) -> Response:
            return Response(body={"message": "OK"}, status_code=200)

        base_time = 1000.0

        for i in range(4):
            req = Request("GET", "/api/data", client_ip="10.0.0.1")
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_middleware_integration():
    """Show full middleware integration with handler chain."""
    print("\n--- Section 6: Full Middleware Integration ---")

    try:
        manager = RateLimitManager(default_max_requests=2, default_window_seconds=10.0)
        middleware = RateLimitMiddleware(manager)

        call_count = 0

        def handler(request: Request) -> Response:
            nonlocal call_count
            call_count += 1
            return Response(body={"data": "hello"}, status_code=200)

        resp1 = middleware.process(Request("GET", "/api", "1.2.3.4"), handler)
        resp2 = middleware.process(Request("GET", "/api", "1.2.3.4"), handler)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert "X-RateLimit-Remaining" in resp1.headers
        print(f"  Request 1: {resp1.status_code}, remaining={resp1.headers['X-RateLimit-Remaining']}")
        print(f"  Request 2: {resp2.status_code}, remaining={resp2.headers['X-RateLimit-Remaining']}")

        resp3 = middleware.process(Request("GET", "/api", "1.2.3.4"), handler)
        assert resp3.status_code == 429
        assert call_count == 2
        print(f"  Request 3: {resp3.status_code} (handler not called, call_count={call_count})")
        print(f"  429 body: {resp3.body}")

        resp4 = middleware.process(Request("GET", "/api", "5.6.7.8"), handler)
        assert resp4.status_code == 200
        print(f"  Request from 5.6.7.8: {resp4.status_code} (different client)")

        print("  [PASS] Full middleware integration works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_reset():
    """Show resetting rate limits."""
    print("\n--- Section 7: Reset ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


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
    print("\nAll 7 sections attempted. Rate limiting skeleton ready!")
    print("Next up: Kata 75 -- background tasks!")


if __name__ == "__main__":
    main()
