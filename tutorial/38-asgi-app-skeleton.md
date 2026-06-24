# Kata 38 -- ASGI App Skeleton (Ignite begins!)

[prev: 37-asgi-primer](./37-asgi-primer.md) | [next: 39-request-object](./39-request-object.md)

---

## What We're Building

The **Ignite class** -- the core of our web framework. This is the first real piece of the Ignite framework, and everything from here forward builds on it. Ignite is an ASGI callable that handles routing, lifespan events, and automatic response serialization.

We'll build five demonstrations:
1. **Basic routing** -- `@app.route("/")` decorator dispatches requests to handler functions
2. **Shorthand decorators** -- `@app.get()` and `@app.post()` for cleaner route registration
3. **Lifespan events** -- `@app.on_startup` and `@app.on_shutdown` for resource management
4. **Error handling** -- handler exceptions become proper 500 responses
5. **uvicorn integration** -- how Ignite plugs into a real ASGI server

All testing is done by simulating ASGI calls directly (no uvicorn needed for the 5-second subprocess constraint). The Ignite class is ready to run with uvicorn when you choose to.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| ASGI callable class | `__call__(self, scope, receive, send)` | Framework entry point |
| Route registration | Decorator maps `(method, path)` to handler | Every web framework |
| Response serialization | Dicts become JSON, strings become text | Automatic content negotiation |
| Lifespan hooks | Startup/shutdown event handlers | DB pools, caches, ML models |
| `asyncio.iscoroutine()` | Detect if a result needs `await` | Supporting both sync and async handlers |
| ASGI simulator | Test harness for ASGI apps | Testing without a running server |
| `__call__` protocol | Makes a class instance callable | ASGI requires `app(scope, receive, send)` |
| Method-based routing | Different handlers for GET vs POST on same path | REST APIs |

## The Code

### 1. The Ignite Class

The core of our framework. An ASGI callable that routes requests to handlers.

```python
import asyncio
import json
from typing import Any, Callable

class Ignite:
    """A minimal ASGI web framework."""

    def __init__(self):
        self._routes: dict[tuple[str, str], Callable] = {}
        self._on_startup: list[Callable] = []
        self._on_shutdown: list[Callable] = []
        self.state: dict[str, Any] = {}

    async def __call__(self, scope, receive, send):
        """ASGI entry point."""
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        elif scope["type"] == "http":
            await self._handle_http(scope, receive, send)
```

The `__call__` method is what makes `Ignite` an ASGI callable. When uvicorn imports `app = Ignite()`, it calls `await app(scope, receive, send)` for every connection.

### 2. Route Registration

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
    def route(self, path, methods=None):
        """Register a route handler (decorator)."""
        if methods is None:
            methods = ["GET"]

        def decorator(func):
            for method in methods:
                self._routes[(method, path)] = func
            return func
        return decorator

    def get(self, path):
        return self.route(path, methods=["GET"])

    def post(self, path):
        return self.route(path, methods=["POST"])
```

Usage:

```python
app = Ignite()

@app.route("/")
async def index():
    return "Hello, Ignite!"

@app.get("/users")
async def list_users():
    return {"users": ["alice", "bob"]}

@app.route("/data", methods=["GET", "POST"])
async def data():
    return {"status": "ok"}
```

### 3. HTTP Request Handling

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
    async def _handle_http(self, scope, receive, send):
        # Read request body
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        method = scope["method"]
        path = scope["path"]
        handler = self._routes.get((method, path))

        if handler is not None:
            result = handler()
            if asyncio.iscoroutine(result):
                result = await result

            # Auto-serialize based on return type
            if isinstance(result, dict):
                response_body = json.dumps(result).encode()
                content_type = b"application/json"
            else:
                response_body = str(result).encode()
                content_type = b"text/plain; charset=utf-8"

            await self._send_response(send, 200, response_body, content_type)
        else:
            await self._send_response(send, 404, b"Not Found", b"text/plain")
```

### 4. Response Helper

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
    async def _send_response(self, send, status, body, content_type):
        """Send a complete HTTP response (two ASGI messages)."""
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                [b"content-type", content_type],
                [b"content-length", str(len(body)).encode()],
                [b"server", b"Ignite/0.1"],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
```

### 5. Lifespan Events

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
    def on_startup(self, func):
        self._on_startup.append(func)
        return func

    def on_shutdown(self, func):
        self._on_shutdown.append(func)
        return func

    async def _handle_lifespan(self, scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                for handler in self._on_startup:
                    result = handler(self.state)
                    if asyncio.iscoroutine(result):
                        await result
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                for handler in self._on_shutdown:
                    result = handler(self.state)
                    if asyncio.iscoroutine(result):
                        await result
                await send({"type": "lifespan.shutdown.complete"})
                return
```

## Playground

```bash
python playground/38_asgi_app_skeleton.py
```

Expected output:

```
--- Section 1: Basic Routing ---
  GET / -> 200 | Hello, Ignite!
  GET /about -> 200 | Ignite is a learning framework
  GET /json -> 200 | {'framework': 'Ignite', 'version': '0.1.0', 'kata': 38}
  POST /greet -> 200 | Greetings!
  GET /nonexistent -> 404 | 404 Not Found: GET /nonexistent
  [VALID] Basic routing works correctly

--- Section 2: Shorthand Decorators ---
  GET /users -> 200 | {'users': ['alice', 'bob', 'charlie']}
  POST /users -> 200 | {'created': True}
  DELETE /users -> 404 (not registered)
  [VALID] Shorthand decorators work correctly

--- Section 3: Lifespan Events ---
  Events: ['startup', 'shutdown']
  Messages: ['lifespan.startup.complete', 'lifespan.shutdown.complete']
  State after startup: {'db': None, 'cache': None}
  [VALID] Lifespan events handled correctly

--- Section 4: Error Handling ---
  GET /boom -> 500 | Internal Server Error: Something went wrong!
  GET /sync -> 200 | Sync handlers work too!
  [VALID] Error handling works correctly

--- Section 5: Using Ignite with uvicorn ---
  How to use Ignite with uvicorn:
    ...usage instructions...
  Ignite() is callable: True
  Ignite.__call__ is async: True
  [VALID] Ignite is a proper ASGI app callable

--- Summary ---
The Ignite ASGI framework skeleton is ready:
  - Ignite class is an ASGI callable (scope, receive, send)
  - @app.route() decorator for path-based routing
  - @app.get() and @app.post() shorthand decorators
  - @app.on_startup / @app.on_shutdown for lifespan events
  - Dict return values auto-serialize to JSON
  - String return values become text/plain responses
  - Handler errors produce 500 responses
  - Works with uvicorn: uvicorn myapp:app --reload

All 5 sections passed. Ignite ASGI skeleton complete!
Next up: Kata 39 -- building the Request object!
```

## How It Works

### Ignite Architecture

```
uvicorn (ASGI Server)
  |
  v
Ignite.__call__(scope, receive, send)
  |
  +-- scope["type"] == "lifespan"
  |     |
  |     +-- lifespan.startup -> run _on_startup handlers
  |     +-- lifespan.shutdown -> run _on_shutdown handlers
  |
  +-- scope["type"] == "http"
        |
        +-- Read body via receive()
        +-- Look up handler: _routes[(method, path)]
        |     |
        |     +-- Found: call handler, serialize result, send 200
        |     +-- Not found: send 404
        |     +-- Handler raised: send 500
        |
        +-- _send_response(send, status, body, content_type)
              |
              +-- http.response.start (status + headers)
              +-- http.response.body (response bytes)
```

### Response Serialization

The Ignite class automatically converts handler return values:

| Return Type | Content-Type | Conversion |
|---|---|---|
| `dict` | `application/json` | `json.dumps(result).encode()` |
| `str` | `text/plain; charset=utf-8` | `result.encode("utf-8")` |
| `bytes` | `application/octet-stream` | Used as-is |

### Route Lookup

Routes are stored as `(method, path) -> handler`:

```python
_routes = {
    ("GET", "/"): index_handler,
    ("GET", "/users"): list_users,
    ("POST", "/users"): create_user,
    ("GET", "/greet"): greet,
    ("POST", "/greet"): greet,      # same handler, two methods
}
```

Lookup is O(1) dict access. No regex matching yet -- that comes in a later kata.

### Sync vs Async Handlers

Ignite supports both sync and async handlers:

```python
@app.get("/sync")
def sync_handler():       # No async -- called directly
    return "Hello!"

@app.get("/async")
async def async_handler(): # Async -- awaited
    return "Hello!"
```

The trick is `asyncio.iscoroutine()`: if calling `handler()` returns a coroutine, we `await` it. Otherwise, we use the result directly.

## Exercises

1. **Add `@app.put()` and `@app.delete()` shorthand decorators** -- follow the same pattern as `get()` and `post()`.

2. **Response class** -- create a `Response(body, status_code, content_type)` class. If a handler returns a `Response` instance, use its fields instead of auto-serializing.

3. **Wildcard routes** -- support `@app.route("/users/*")` that matches any path starting with `/users/`. Store these separately and check them when exact match fails.

4. **Startup failure** -- test what happens when a startup handler raises an exception. Verify that `lifespan.startup.failed` is sent with the error message.

5. **Request body access** -- modify `_handle_http` to pass the request body to the handler. This previews what we'll build properly in kata 39 (Request object).

## What's Next

The Ignite skeleton is alive! We have routing, lifespan events, and response serialization. In [Kata 39: Request Object](./39-request-object.md), we build a **Request class** that wraps the raw ASGI scope and body into a developer-friendly object with properties like `request.method`, `request.path`, `request.json()`, and `request.query_params`. This is what FastAPI's `Request` object does under the hood.

---

[prev: 37-asgi-primer](./37-asgi-primer.md) | [next: 39-request-object](./39-request-object.md)
