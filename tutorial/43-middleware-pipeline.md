# Kata 43 -- Middleware Pipeline

[prev: 42-path-parameters](./42-path-parameters.md) | [next: 44-dependency-injection](./44-dependency-injection.md)

---

## What We're Building

An **ASGI middleware system** for the Ignite framework -- composable layers that wrap around your application, intercepting every request and response. This is the same pattern used by FastAPI, Starlette, Django, and every serious web framework.

We'll build five components:
1. **ASGI type simulation** -- model the ASGI protocol (scope, receive, send) without needing uvicorn
2. **Base middleware class** -- the foundation that all middlewares inherit from
3. **Practical middlewares** -- LoggingMiddleware, TimingMiddleware, CORSMiddleware
4. **Middleware stack** -- compose multiple middlewares into a pipeline
5. **Short-circuit middleware** -- AuthMiddleware that rejects requests before they reach the app

The key insight: middleware is just function wrapping. Each middleware takes an app, returns a new app that does something extra.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| ASGI protocol | Async Server Gateway Interface (scope, receive, send) | Any async Python web framework |
| Middleware pattern | Wrap an app to add cross-cutting behavior | Logging, auth, CORS, timing |
| Onion model | Request flows in through layers, response flows back out | Understanding middleware order |
| `send` wrapping | Intercept outgoing response messages | Adding headers, logging status codes |
| Short-circuiting | Return early without calling the inner app | Auth failures, rate limiting |
| Middleware composition | Stack multiple middlewares in order | Building a full request pipeline |

## The Code

### 1. ASGI Basics

ASGI apps are async callables that receive three arguments:

```python
async def app(scope: dict, receive: Callable, send: Callable) -> None:
    # scope  = request metadata (method, path, headers)
    # receive = async function to get request body
    # send   = async function to send response parts

    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"application/json")],
    })
    await send({
        "type": "http.response.body",
        "body": b'{"message": "Hello!"}',
    })
```

### 2. The Middleware Pattern

A middleware wraps an ASGI app. It receives the same `(scope, receive, send)` and decides what to do:

```python
class Middleware:
    def __init__(self, app):
        self.app = app  # the inner app (or next middleware)

    async def __call__(self, scope, receive, send):
        # Before: inspect/modify the request
        # ...
        await self.app(scope, receive, send)  # call inner app
        # After: the response has already been sent via send()
```

### 3. Wrapping `send` to Intercept Responses

Since ASGI sends responses via the `send` callback, middleware intercepts responses by wrapping `send`:

```python
class TimingMiddleware(Middleware):
    async def __call__(self, scope, receive, send):
        start = time.perf_counter()

        async def timing_send(message):
            if message["type"] == "http.response.start":
                elapsed = (time.perf_counter() - start) * 1000
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{elapsed:.2f}ms".encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, timing_send)
```

### 4. Short-Circuiting

A middleware can respond directly without calling the inner app:

```python
class AuthMiddleware(Middleware):
    async def __call__(self, scope, receive, send):
        token = extract_token(scope)
        if token not in self.valid_tokens:
            # Respond with 401 -- inner app never runs
            await send({"type": "http.response.start", "status": 401, ...})
            await send({"type": "http.response.body", "body": b"Unauthorized"})
            return  # <-- short-circuit here

        await self.app(scope, receive, send)  # token valid, proceed
```

### 5. Composing the Stack

Middlewares compose by nesting. The first added is the outermost layer:

```python
# Add order: [Logging, Timing, CORS]
# Build in reverse: CORS(app), Timing(CORS(app)), Logging(Timing(CORS(app)))
# Request flow: Logging -> Timing -> CORS -> App -> CORS -> Timing -> Logging

class MiddlewareStack:
    def build(self) -> ASGIApp:
        app = self.app
        for cls, kwargs in reversed(self._middleware_classes):
            app = cls(app, **kwargs)
        return app
```

## Playground

```bash
python playground/43_middleware_pipeline.py
```

Expected output:

```
--- Section 1: Simulated ASGI Types ---
  Scope -> Request: GET /users/42
  Headers: {'host': 'localhost:8000', 'accept': 'application/json'}
  [VALID] ASGI scope converts to Request correctly

--- Section 2: Base Middleware & The Onion Model ---
  Base middleware passes through: status=200
  Response body: {"message": "Hello from Ignite!"}
  [VALID] Base middleware is transparent

--- Section 3: Practical Middlewares ---
  LoggingMiddleware logs: ['GET /api/users', '  -> 200']
  TimingMiddleware: 0.01ms
  CORSMiddleware headers: origin=https://example.com
  CORS preflight: status=204 (no body)
  [VALID] All three middlewares work correctly

--- Section 4: Composing the Middleware Stack ---
  Stack layers: Logging -> Timing -> CORS -> App
  Response status: 200
  Headers present: ['content-type', 'access-control-allow-origin', 'access-control-allow-methods', 'access-control-allow-headers', 'x-process-time']
  Logging captured: ['GET /api/data', '  -> 200']
  [VALID] Middleware stack composes correctly

--- Section 5: Short-Circuit Middleware (Auth) ---
  No valid token -> 401: {"error": "Unauthorized"}
  Valid token -> 200: {"message": "Hello from Ignite!"}
  Stack with auth (bad key) -> 401
  Stack with auth (good key) -> 200
  [VALID] Auth middleware short-circuits correctly

--- Summary ---
Middleware wraps your app in composable layers:
  - Each middleware receives (scope, receive, send)
  - Can modify request before calling inner app
  - Can modify response by wrapping the send callable
  - Can short-circuit by sending a response without calling inner app
  - Composes like onion layers: first added = outermost

All 5 sections passed. Middleware pipeline mastered!
Next up: Kata 44 -- Dependency Injection System
```

## How It Works

### The Onion Model

```
                    Request
                       |
                       v
              +------------------+
              |  LoggingMiddleware |  <- logs method & path
              |  +-------------+  |
              |  | TimingMW    |  |  <- starts timer
              |  | +---------+ |  |
              |  | | CORS MW | |  |  <- adds CORS headers
              |  | | +-----+ | |  |
              |  | | | App | | |  |  <- generates response
              |  | | +-----+ | |  |
              |  | +---------+ |  |
              |  +-------------+  |
              +------------------+
                       |
                       v
                    Response
                 (with all headers)
```

### How `send` Wrapping Works

Each middleware creates a new `send` function that intercepts response messages:

```
Original send:      send(message)
After CORS:         cors_send(message)    -> adds CORS headers -> send(message)
After Timing:       timing_send(message)  -> adds X-Process-Time -> cors_send(message)
After Logging:      logging_send(message) -> captures status -> timing_send(message)
```

The inner app calls `send()` -- but it's actually calling `logging_send()`, which calls `timing_send()`, which calls `cors_send()`, which calls the real `send()`. Each layer adds its own behavior.

### ASGI Message Types

```
Request phase:
  scope = {"type": "http", "method": "GET", "path": "/api", "headers": [...]}
  receive() -> {"type": "http.request", "body": b"..."}

Response phase (two messages):
  send({"type": "http.response.start", "status": 200, "headers": [...]})
  send({"type": "http.response.body", "body": b"..."})
```

## Exercises

1. **RateLimitMiddleware** -- build a middleware that tracks request counts per IP (from headers) and returns 429 Too Many Requests after a configurable limit. Use a dict to store counts and reset them periodically.

2. **CompressionMiddleware** -- create a middleware that checks the `accept-encoding` header. If the client accepts gzip, compress the response body using `gzip.compress()` and add `content-encoding: gzip` to the response headers.

3. **ErrorHandlerMiddleware** -- build a middleware that catches exceptions from the inner app, logs them, and returns a clean 500 response instead of crashing. Include the exception type in the response for debugging.

4. **Conditional middleware** -- extend `MiddlewareStack` with an `add_if(condition, middleware_cls)` method that only includes a middleware if the condition is True. Useful for `add_if(DEBUG, LoggingMiddleware)`.

5. **Middleware ordering test** -- write a test that verifies the exact order in which middlewares process a request and response. Create three simple middlewares that append "A-in", "B-in", "C-in" (request) and "C-out", "B-out", "A-out" (response) to a shared list, then assert the final order.

## What's Next

With middleware handling cross-cutting concerns, we need a way to inject shared services (database connections, auth, config) into our route handlers cleanly. In [Kata 44: Dependency Injection](./44-dependency-injection.md), we build a FastAPI-style `Depends()` system that resolves, caches, and injects dependencies automatically.

---

[prev: 42-path-parameters](./42-path-parameters.md) | [next: 44-dependency-injection](./44-dependency-injection.md)
