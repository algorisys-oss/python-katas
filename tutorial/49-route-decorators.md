# Kata 49 -- @app.get() / @app.post() Route Decorators

[prev: 48-error-handling](./48-error-handling.md) | [next: 50-parameter-injection](./50-parameter-injection.md)

---

## What We're Building

**FastAPI-style route decorators** for our Ignite framework. Instead of a generic `@app.route("/path")`, we build method-specific decorators:

```python
@app.get("/users", tags=["users"], summary="List users")
def list_users(request):
    return {"users": ["Alice", "Bob"]}

@app.post("/users", tags=["users"], summary="Create user")
def create_user(request):
    return {"created": True}
```

Each decorator registers the handler with its HTTP method, path, and OpenAPI metadata (tags, summary, description, deprecated). The registry indexes routes by `(METHOD, path)` tuples for fast lookup and supports dispatching with proper 404/405 handling.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Decorator factories | `@app.get(path)` returns a decorator | Parameterized decorators |
| Route metadata | `RouteInfo` stores method, path, handler, and OpenAPI fields | API documentation |
| Route registry | `(METHOD, path)` keyed dict for fast lookup | Request dispatching |
| Method dispatching | Same path, different methods = different handlers | REST APIs |
| 404 vs 405 | "path not found" vs "wrong method for this path" | Correct HTTP semantics |
| ASGI interface | `__call__(scope, receive, send)` protocol | Server compatibility |
| OpenAPI metadata | tags, summary, description, deprecated | Auto-generated docs |

## The Code

### 1. RouteInfo -- Metadata Container

```python
class RouteInfo:
    def __init__(self, path, method, handler, *,
                 tags=None, summary=None, description=None,
                 response_model=None, status_code=200, deprecated=False):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.tags = tags or []
        self.summary = summary or handler.__name__.replace("_", " ").title()
        self.description = description or handler.__doc__ or ""
```

Auto-generating the summary from `fetch_all_records` to `"Fetch All Records"` gives sensible defaults with zero effort.

### 2. Route Registry

```python
class RouteRegistry:
    def __init__(self):
        self._routes = {}  # (METHOD, path) -> RouteInfo
        self._ordered = []

    def add(self, route):
        key = (route.method, route.path)
        if key in self._routes:
            raise ValueError(f"Route already registered: {route.method} {route.path}")
        self._routes[key] = route
        self._ordered.append(route)

    def lookup(self, method, path):
        return self._routes.get((method.upper(), path))
```

### 3. The Decorator Factory Pattern

This is the core pattern. Each method (`get`, `post`, etc.) is a thin wrapper around `_route_decorator`:

```python
class IgniteApp:
    def get(self, path, **kwargs):
        return self._route_decorator(path, "GET", status_code=200, **kwargs)

    def post(self, path, **kwargs):
        return self._route_decorator(path, "POST", status_code=201, **kwargs)

    def _route_decorator(self, path, method, **kwargs):
        def decorator(func):
            route = RouteInfo(path, method, func, **kwargs)
            self.registry.add(route)
            func._route_info = route  # attach metadata
            return func
        return decorator
```

### 4. Dispatching with 404/405

```python
def dispatch(self, request):
    route = self.registry.lookup(request.method, request.path)
    if route is None:
        # Check if path exists with different method -> 405
        for method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            if self.registry.lookup(method, request.path):
                return Response(body={"error": "Method Not Allowed"}, status_code=405)
        return Response(body={"error": "Not Found"}, status_code=404)
    result = route.handler(request)
    return Response(body=result, status_code=route.status_code)
```

## Playground

```python
python playground/49_route_decorators.py
```

Expected output:

```
--- Section 1: Basic Route Decorators ---
  Registered 3 routes
  GET /users: summary='List all users', tags=['users']
  POST /users: status_code=201
  [PASS] Basic route decorators work

--- Section 2: All HTTP Methods ---
  Methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
  Default status codes: GET=200, POST=201, DELETE=204
  [PASS] All HTTP methods work

--- Section 3: OpenAPI Metadata ---
  /products: tags=['products', 'catalog'], deprecated=False
  /products/legacy: deprecated=True
  Routes tagged 'products': 2
  Routes tagged 'catalog': 1
  [PASS] OpenAPI metadata works

--- Section 4: Request Dispatching ---
  GET /hello -> 200: {'message': 'Hello, World!'}
  POST /echo -> 201: {'body': 'test data'}
  GET /nonexistent -> 404: {'error': 'Not Found: /nonexistent'}
  DELETE /hello -> 405: {'error': 'Method Not Allowed'}
  [PASS] Dispatching works

--- Section 5: ASGI Simulation ---
  ASGI status: 200
  ASGI body: {'status': 'healthy'}
  [PASS] ASGI simulation works

--- Section 6: Function Metadata ---
  Handler callable: True
  _route_info: RouteInfo(GET /test, handler='my_handler', tags=['testing'])
  Auto-summary: 'Fetch All Records' (from 'fetch_all_records')
  [PASS] Function metadata preserved

All 6 sections passed. Route decorators mastered!
```

## How It Works

### Decorator Factory Flow

```
@app.get("/users", tags=["users"])    # 1. app.get() called
def list_users(request): ...          # 2. Returns decorator
                                      # 3. decorator(list_users) called
                                      # 4. RouteInfo created
                                      # 5. Registered in RouteRegistry
                                      # 6. list_users returned (unchanged)
```

### Dispatch Decision Tree

```
Request arrives: GET /users
    |
    v
lookup("GET", "/users") -> RouteInfo?
    |
    YES -> call handler -> Response(200)
    |
    NO -> any method matches "/users"?
        |
        YES -> 405 Method Not Allowed
        NO  -> 404 Not Found
```

### Default Status Codes

| Method | Default Status | Reason |
|---|---|---|
| GET | 200 | Returning data |
| POST | 201 | Created a resource |
| PUT | 200 | Updated a resource |
| PATCH | 200 | Partially updated |
| DELETE | 204 | No content to return |

## Exercises

1. **Add `@app.options()` and `@app.head()`** -- complete the HTTP method set. `OPTIONS` should auto-generate the `Allow` header listing valid methods for the path.

2. **Route groups with prefixes** -- implement `app.group("/api/v1")` that returns a sub-router where all registered paths are prefixed.

3. **Duplicate detection** -- when a route is already registered, show a helpful warning with the file/line where the original was registered (use `inspect.stack()`).

4. **Middleware per route** -- allow `@app.get("/path", middleware=[auth, logging])` and wrap the handler in the middleware chain before dispatching.

5. **Wildcard routes** -- support `@app.get("/files/{path:path}")` where the path parameter captures the rest of the URL including slashes.

## What's Next

Route decorators register handlers, but currently the handler signature is ignored -- all params come from the request object. In [Kata 50: Parameter Injection](./50-parameter-injection.md), we'll use `inspect.signature()` to automatically inject path params, query params, request body, and dependencies directly into handler arguments.

---

[prev: 48-error-handling](./48-error-handling.md) | [next: 50-parameter-injection](./50-parameter-injection.md)
