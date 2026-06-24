# Kata 74 -- Rate Limiting

[prev: 73-health-check](./73-health-check.md) | [next: 75-background-tasks](./75-background-tasks.md)

---

## What We're Building

A **rate limiting system** for our Ignite framework. Rate limiting protects your service from abuse and ensures fair access. We build:

1. **Sliding window algorithm** -- tracks request timestamps per client IP, avoiding the boundary-burst problem of fixed windows
2. **X-RateLimit-\* headers** -- standard headers that tell clients their limit, remaining quota, and reset time
3. **429 Too Many Requests** -- proper HTTP response when a client exceeds the limit
4. **Per-route limits** -- different routes can have different limits (login = strict, search = moderate)
5. **Middleware integration** -- rate limiting sits in the request pipeline before the route handler

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Sliding window | Tracks timestamps, counts requests in window | Smooth rate limiting without boundary bursts |
| Fixed vs sliding | Fixed resets at intervals, sliding is continuous | Sliding is more accurate |
| X-RateLimit-Limit | Header: max requests per window | Always include in responses |
| X-RateLimit-Remaining | Header: requests left in current window | Client can pace itself |
| X-RateLimit-Reset | Header: when window resets (unix timestamp) | Client knows when to retry |
| 429 status code | Too Many Requests | Standard rate limit exceeded response |
| Per-route limits | Different limits for different endpoints | Protect sensitive routes |

## The Code

### 1. Sliding Window Algorithm

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
class SlidingWindowLimiter:
    def __init__(self, max_requests, window_seconds):
        self._requests = defaultdict(list)  # key -> [timestamps]

    def check(self, key, now=None):
        now = now or time.time()
        window_start = now - self.window_seconds

        # Prune old timestamps
        self._requests[key] = [t for t in timestamps if t > window_start]

        remaining = self.max_requests - len(timestamps)
        if remaining > 0:
            timestamps.append(now)  # Record this request
            return RateLimitResult(allowed=True, remaining=remaining - 1, ...)
        else:
            return RateLimitResult(allowed=False, remaining=0, ...)
```

### 2. Rate Limit Headers

```python
@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: float = 0.0

    def headers(self):
        h = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_at)),
        }
        if not self.allowed:
            h["Retry-After"] = str(int(self.retry_after) + 1)
        return h
```

### 3. Middleware

```python
class RateLimitMiddleware:
    def process(self, request, next_handler):
        result = self.manager.check(request.client_ip, request.path)

        if not result.allowed:
            response = Response(status_code=429, body={"error": ...})
            response.headers.update(result.headers())
            return response

        response = next_handler(request)
        response.headers.update(result.headers())
        return response
```

## Playground

```bash
python playground/74_rate_limiting.py
```

Expected output:

```
--- Section 1: Rate Limit Result ---
  Allowed: True
  Headers: {'X-RateLimit-Limit': '100', 'X-RateLimit-Remaining': '95', ...}
  [PASS] Rate limit result works

--- Section 2: Sliding Window ---
  Request 1: allowed=True, remaining=2
  Request 2: allowed=True, remaining=1
  Request 3: allowed=True, remaining=0
  Request 4: allowed=False, remaining=0
  Request 5 (after window): allowed=True
  [PASS] Sliding window works

--- Section 3: Sliding Window Precision ---
  At t=10 (1s after last burst): allowed=False
  At t=19 (window expired): allowed=True
  [PASS] Sliding window prevents boundary bursts

--- Section 4: Per-Route Rate Limits ---
  /auth/login after 3 requests: allowed=False
  /search (separate limit): allowed=True
  /api/users (default limit): allowed=True
  [PASS] Per-route rate limits work

--- Section 5-7: Middleware, Integration, Reset ---
  [PASS] All sections pass
```

## How It Works

### Sliding Window vs Fixed Window

```
Fixed Window (problem):
|----Window 1----|----Window 2----|
              ^^^^^^^^
         5 at end + 5 at start = 10 burst!

Sliding Window (solution):
       |<--- 10 sec window --->|
       Counts ALL requests in last 10 seconds
       No boundary burst possible
```

### Request Flow

```
Client Request
     |
     v
RateLimitMiddleware
     |
     v
Check: client_ip + path
     |
     +-- Route-specific limiter?
     |      YES -> use route limiter
     |      NO  -> use default limiter
     |
     v
SlidingWindowLimiter.check()
     |
     +-- Prune expired timestamps
     +-- Count remaining
     |
     +-- allowed?
     |      YES -> call next_handler
     |             add X-RateLimit-* headers
     |             return response
     |
     |      NO  -> return 429
     |             add X-RateLimit-* headers
     |             add Retry-After header
```

## Exercises

1. **Token bucket algorithm** -- implement an alternative rate limiting algorithm where tokens are added at a fixed rate and consumed per request. Compare with sliding window.

2. **Distributed rate limiting** -- store rate limit counters in a shared dict (simulating Redis) so multiple "server instances" share the same limits.

3. **Rate limit by API key** -- instead of IP-based limiting, support limiting by an API key passed in an `Authorization` header.

4. **Burst allowance** -- allow a small burst above the limit (e.g. 120% of max) but with degraded priority, rather than hard-blocking at the limit.

5. **Rate limit dashboard** -- track and expose rate limit statistics: total requests, blocked requests, top rate-limited clients.

## What's Next

With rate limiting protecting our service, in [Kata 75: Background Tasks](./75-background-tasks.md) we'll build a system for running tasks after the response is sent -- like sending emails, processing uploads, or updating caches without blocking the client.

---

[prev: 73-health-check](./73-health-check.md) | [next: 75-background-tasks](./75-background-tasks.md)
