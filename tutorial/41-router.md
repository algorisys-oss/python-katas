# Kata 41 -- Router

[prev: 40-response-object](./40-response-object.md) | [next: 42-path-parameters](./42-path-parameters.md)

---

## What We're Building

An Ignite **Router** that maps HTTP method + path combinations to handler functions. The router is the traffic controller of any web framework -- it receives every incoming request and decides which handler should process it.

We'll build five capabilities:
1. **Route registration** -- manual `add_route()` and decorator syntax (`@router.get`)
2. **Successful dispatch** -- matching a request to its handler and returning the response
3. **404 Not Found** -- proper error response when no route matches the path
4. **405 Method Not Allowed** -- proper error when the path exists but the method is wrong
5. **ASGI interface** -- making the Router itself an ASGI application

This builds directly on the Request (Kata 39) and Response (Kata 40) classes.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Route | Maps a method + path pair to a handler function | Every URL in your app |
| Router | Collection of routes with dispatch logic | Central request routing |
| Decorators for routing | `@router.get("/path")` syntax for clean registration | Every web framework |
| 404 Not Found | No route matches the requested path | Missing pages/endpoints |
| 405 Method Not Allowed | Path exists but not for that HTTP method | POST to a GET-only route |
| Allow header | Lists valid methods for a path in 405 responses | HTTP spec compliance |
| ASGI `__call__` | Router as callable ASGI application | Framework entry point |

## The Code

### 1. The Route Class

```python
class Route:
    def __init__(self, method: str, path: str, handler: callable):
        self.method = method.upper()
        self.path = path
        self.handler = handler

    def matches(self, method: str, path: str) -> bool:
        return self.method == method.upper() and self.path == path
```

A Route is a simple data object: it knows its method, path, and handler. The `matches()` method checks if an incoming request matches this route.

### 2. Route Registration

```python
class Router:
    def __init__(self):
        self.routes: list[Route] = []

    def add_route(self, method, path, handler):
        self.routes.append(Route(method, path, handler))

    def get(self, path):
        return self.route(path, methods=["GET"])

    def post(self, path):
        return self.route(path, methods=["POST"])

    def route(self, path, methods=None):
        if methods is None:
            methods = ["GET"]
        def decorator(handler):
            for method in methods:
                self.add_route(method, path, handler)
            return handler
        return decorator
```

Three registration styles:
- **Manual:** `router.add_route("GET", "/", handler)`
- **Decorator shortcut:** `@router.get("/users")`
- **Multi-method:** `@router.route("/items", methods=["GET", "POST"])`

### 3. Dispatch Logic

```python
async def dispatch(self, request: Request) -> Response:
    method = request.method
    path = request.path

    # Try exact match
    route = self._find_route(method, path)
    if route is not None:
        return await route.handler(request)

    # Path exists but wrong method -> 405
    routes_for_path = self._find_routes_for_path(path)
    if routes_for_path:
        allowed = sorted(set(r.method for r in routes_for_path))
        return JSONResponse(
            content={"error": "Method Not Allowed",
                     "allowed_methods": allowed},
            status_code=405,
            headers={"allow": ", ".join(allowed)})

    # No match at all -> 404
    return JSONResponse(
        content={"error": "Not Found"},
        status_code=404)
```

The dispatch logic has three outcomes:
1. **Match found** -- call the handler, return its response
2. **Path exists, wrong method** -- 405 with `Allow` header listing valid methods
3. **No matching path** -- 404

### 4. ASGI Interface

```python
async def __call__(self, scope, receive, send):
    request = Request(scope, receive)
    response = await self.dispatch(request)
    await response(scope, receive, send)
```

This three-line method makes the Router a complete ASGI application. An ASGI server calls `await router(scope, receive, send)`, and the router handles everything: creating the Request, finding the handler, and sending the Response.

## Playground

```bash
python playground/41_router.py
```

Expected output:

```
--- Section 1: Route Registration ---
  Registered routes:
    GET /
    GET /api/health
    POST /api/users
    GET /api/items
    POST /api/items
  [PASS] Route registration works correctly

--- Section 2: Successful Dispatch ---
  GET / -> 200: 'Welcome to Ignite!'
  GET /api/health -> 200: '{"status": "ok"}'
  POST /api/users -> 201: '{"created": true}'
  [PASS] Dispatch to matching handlers works

--- Section 3: 404 Not Found ---
  GET /nonexistent -> 404: '{"error": "Not Found", "detail": "/nonexistent not found"}'
  [PASS] 404 Not Found works correctly

--- Section 4: 405 Method Not Allowed ---
  DELETE /api/health -> 405: '{"error": "Method Not Allowed", "detail": "DELETE /api/health not allowed", "allowed_methods": ["GET"]}'
  PUT /api/items -> 405: '{"error": "Method Not Allowed", "detail": "PUT /api/items not allowed", "allowed_methods": ["GET", "POST"]}'
  [PASS] 405 Method Not Allowed works correctly

--- Section 5: ASGI Interface ---
  ASGI call GET /api/health -> 200
  ASGI call GET /missing -> 404
  [PASS] Router works as an ASGI application

--- Summary ---
The Router is the traffic controller of a web framework:
  - Register routes with method + path -> handler
  - Use decorators (@router.get, @router.post) for clean syntax
  - Dispatch incoming requests to the right handler
  - Return 404 for unknown paths
  - Return 405 with Allow header for wrong methods
  - Acts as a full ASGI application via __call__

All 5 sections passed. Router mastered!
Next up: Kata 42 -- Path Parameters
```

## How It Works

### Request Lifecycle Through the Router

```
ASGI Server
    |
    v
Router.__call__(scope, receive, send)
    |
    +-- Request(scope, receive)        Create Request object
    |
    +-- dispatch(request)              Find matching route
    |       |
    |       +-- _find_route(method, path)
    |       |       |
    |       |       +-- Found? -> await handler(request)
    |       |       |
    |       |       +-- Not found? -> check path exists
    |       |               |
    |       |               +-- Path exists? -> 405 + Allow header
    |       |               |
    |       |               +-- No path? -> 404
    |       |
    |       +-- Returns Response
    |
    +-- await response(scope, receive, send)   Send to client
```

### 404 vs 405: Why It Matters

```
Routes registered:
  GET  /api/users
  POST /api/users

Request: GET /api/users    -> 200 (exact match)
Request: POST /api/users   -> 201 (exact match)
Request: DELETE /api/users -> 405 (path exists, wrong method)
                              Allow: GET, POST
Request: GET /api/orders   -> 404 (path doesn't exist at all)
```

The distinction matters for API clients:
- **404** means "this endpoint doesn't exist" -- check your URL
- **405** means "this endpoint exists but doesn't accept that method" -- check your HTTP verb

### Route Matching Strategy

Our router uses **exact string matching** -- `"/api/users"` matches `"/api/users"` and nothing else. This is simple and fast, but doesn't support:
- Path parameters (`/users/{id}`)
- Wildcards (`/static/*`)
- Regex patterns

We'll add path parameters in Kata 42.

## Exercises

1. **Add `HEAD` method support** -- automatically handle HEAD requests for any registered GET route by calling the GET handler but stripping the response body.

2. **Add `OPTIONS` method support** -- automatically respond to OPTIONS requests with the list of allowed methods for that path (useful for CORS).

3. **Implement route listing as an endpoint** -- add a built-in `GET /routes` endpoint that returns all registered routes as JSON.

4. **Add route name support** -- let routes be registered with a name (`@router.get("/users", name="user_list")`) and implement `router.url_for("user_list")` to get the path back.

5. **Implement route grouping** -- create a `RouteGroup` class with a prefix (e.g., `/api/v1`) that prepends the prefix to all routes registered within it.

## What's Next

Static path matching is limiting. In [Kata 42: Path Parameters](./42-path-parameters.md), we add **dynamic path segments** -- turning `/users/{user_id}/posts/{post_id}` into extracted parameters that handlers receive automatically, just like FastAPI.

---

[prev: 40-response-object](./40-response-object.md) | [next: 42-path-parameters](./42-path-parameters.md)
