"""
Kata 49 -- @app.get() / @app.post() Route Decorators
Run: python playground/skeletons/49_route_decorators.py

Build FastAPI-style route decorators: @app.get("/path"), @app.post("/path")
that register handlers with method + path + OpenAPI metadata. Support tags,
summary, description for OpenAPI docs. Test by registering routes and
dispatching requests via ASGI simulation.

Completes within 5 seconds.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Route Metadata
# ===========================================================================
# Each registered route stores its HTTP method, path, handler function,
# and OpenAPI metadata (tags, summary, description, response model).

class RouteInfo:
    """Metadata for a registered route.

    Stores everything needed to match requests and generate OpenAPI docs.
    """

    def __init__(
        self,
        path: str,
        method: str,
        handler: Callable,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_model: type | None = None,
        status_code: int = 200,
        deprecated: bool = False,
    ):
        self.path = path
        self.method = method.upper()
        self.handler = handler
        # TODO: Set self.tags -- use provided tags or default to empty list
        self.tags = []
        # TODO: Set self.summary -- use provided summary or auto-generate
        # from handler.__name__ by replacing "_" with " " and calling .title()
        self.summary = ""
        # TODO: Set self.description -- use provided description or handler.__doc__ or ""
        self.description = ""
        self.response_model = response_model
        self.status_code = status_code
        self.deprecated = deprecated

    def __repr__(self) -> str:
        return (
            f"RouteInfo({self.method} {self.path}, "
            f"handler={self.handler.__name__!r}, tags={self.tags})"
        )


# ===========================================================================
# SECTION 2: Route Registry
# ===========================================================================
# The registry holds all routes indexed by (method, path) for fast lookup.

class RouteRegistry:
    """Stores and looks up routes by method and path.

    Routes are indexed by (METHOD, path) tuples so GET /users and
    POST /users are distinct entries.
    """

    def __init__(self):
        self._routes: dict[tuple[str, str], RouteInfo] = {}
        self._ordered: list[RouteInfo] = []

    def add(self, route: RouteInfo) -> None:
        """Register a new route."""
        key = (route.method, route.path)
        # TODO: Check if key already exists in self._routes
        # If so, raise ValueError(f"Route already registered: ...")
        # Otherwise, store it and append to self._ordered
        pass

    def lookup(self, method: str, path: str) -> RouteInfo | None:
        """Find a route by method and path."""
        # TODO: Look up (method.upper(), path) in self._routes
        pass

    def all_routes(self) -> list[RouteInfo]:
        """Return all routes in registration order."""
        return list(self._ordered)

    def routes_by_tag(self, tag: str) -> list[RouteInfo]:
        """Return routes that have a given tag."""
        # TODO: Filter self._ordered for routes where tag is in r.tags
        return []

    def __len__(self) -> int:
        return len(self._routes)


# ===========================================================================
# SECTION 3: HTTP Method Decorators
# ===========================================================================
# The app class provides @app.get(), @app.post(), etc. Each is a thin
# wrapper that creates a RouteInfo and registers it.

class HTTPException(Exception):
    """Simple HTTP error for dispatching."""
    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail or {404: "Not Found", 405: "Method Not Allowed"}.get(
            status_code, "Error"
        )


class Request:
    """Simulated HTTP request for testing."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        query_string: str = "",
    ):
        self.method = method.upper()
        self.path = path
        self.body = body
        self.headers = headers or {}
        self.query_string = query_string


class Response:
    """Simulated HTTP response."""

    def __init__(
        self,
        body: Any = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {"content-type": "application/json"}

    def json(self) -> str:
        return json.dumps(self.body)


class IgniteApp:
    """A mini web framework with FastAPI-style route decorators.

    Usage:
        app = IgniteApp()

        @app.get("/users", tags=["users"], summary="List all users")
        def list_users(request):
            return {"users": ["Alice", "Bob"]}

        @app.post("/users", tags=["users"], summary="Create user")
        def create_user(request):
            return {"created": True}
    """

    def __init__(self, title: str = "Ignite API", version: str = "1.0.0"):
        self.title = title
        self.version = version
        self.registry = RouteRegistry()

    # -- Decorator factories for each HTTP method -------------------------

    def get(
        self,
        path: str,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_model: type | None = None,
        status_code: int = 200,
        deprecated: bool = False,
    ) -> Callable:
        """Register a GET route handler."""
        # TODO: Call self._route_decorator with method="GET" and all kwargs
        # Return the result (a decorator function)
        pass

    def post(
        self,
        path: str,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_model: type | None = None,
        status_code: int = 201,
        deprecated: bool = False,
    ) -> Callable:
        """Register a POST route handler."""
        # TODO: Call self._route_decorator with method="POST"
        # Note: default status_code for POST is 201
        pass

    def put(
        self,
        path: str,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_model: type | None = None,
        status_code: int = 200,
        deprecated: bool = False,
    ) -> Callable:
        """Register a PUT route handler."""
        # TODO: Call self._route_decorator with method="PUT"
        pass

    def delete(
        self,
        path: str,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        status_code: int = 204,
        deprecated: bool = False,
    ) -> Callable:
        """Register a DELETE route handler."""
        # TODO: Call self._route_decorator with method="DELETE"
        pass

    def patch(
        self,
        path: str,
        *,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_model: type | None = None,
        status_code: int = 200,
        deprecated: bool = False,
    ) -> Callable:
        """Register a PATCH route handler."""
        # TODO: Call self._route_decorator with method="PATCH"
        pass

    def _route_decorator(
        self,
        path: str,
        method: str,
        **kwargs: Any,
    ) -> Callable:
        """Internal factory that builds the actual decorator.

        This is the core pattern: return a decorator that wraps the handler,
        creates a RouteInfo, and registers it.
        """
        # TODO: Return a decorator function that:
        # 1. Creates a RouteInfo(path, method, func, **kwargs)
        # 2. Calls self.registry.add(route) to register it
        # 3. Attaches the route info: func._route_info = route
        # 4. Returns the original func
        def decorator(func: Callable) -> Callable:
            pass
        return decorator

    # -- Request dispatching -----------------------------------------------

    def dispatch(self, request: Request) -> Response:
        """Find and call the handler matching a request.

        Returns a Response with the handler's return value as the body.
        """
        route = self.registry.lookup(request.method, request.path)
        if route is None:
            # TODO: Check if path exists with a different method -> 405
            # Loop through GET, POST, PUT, DELETE, PATCH and check if any
            # method matches the path. If so, return 405 Method Not Allowed.
            # Otherwise, return 404 Not Found.
            return Response(
                body={"error": f"Not Found: {request.path}"},
                status_code=404,
            )
        try:
            result = route.handler(request)
            return Response(body=result, status_code=route.status_code)
        except HTTPException as exc:
            return Response(
                body={"error": exc.detail},
                status_code=exc.status_code,
            )

    # -- ASGI interface (simulated) ----------------------------------------

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        """ASGI application interface.

        Translates ASGI scope/receive/send into our Request/Response model.
        """
        if scope["type"] != "http":
            return

        # TODO: Build a Request from the ASGI scope
        # method = scope.get("method", "GET")
        # path = scope.get("path", "/")
        # query_string = scope.get("query_string", b"").decode()
        # headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
        request = Request()

        # TODO: Read request body from receive()
        # body_parts = []
        # while True:
        #     message = await receive()
        #     body_parts.append(message.get("body", b""))
        #     if not message.get("more_body", False):
        #         break
        # request.body = b"".join(body_parts)

        # Dispatch and send response
        response = self.dispatch(request)
        body_bytes = json.dumps(response.body).encode() if response.body else b""

        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                [k.encode(), v.encode()]
                for k, v in response.headers.items()
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body_bytes,
        })


# ===========================================================================
# SECTION 4: Demos
# ===========================================================================

def demo_basic_decorators():
    """Show @app.get() and @app.post() decorator usage."""
    print("--- Section 1: Basic Route Decorators ---")

    app = IgniteApp()

    @app.get("/users", tags=["users"], summary="List all users")
    def list_users(request: Request) -> dict:
        """Return all users in the system."""
        return {"users": ["Alice", "Bob", "Charlie"]}

    @app.post("/users", tags=["users"], summary="Create a new user")
    def create_user(request: Request) -> dict:
        """Create a user from the request body."""
        return {"created": True, "id": 1}

    @app.get("/users/{id}", tags=["users"], summary="Get user by ID")
    def get_user(request: Request) -> dict:
        return {"id": 1, "name": "Alice"}

    # Verify routes are registered
    assert len(app.registry) == 3
    print(f"  Registered {len(app.registry)} routes")

    # Check route metadata
    route = app.registry.lookup("GET", "/users")
    assert route is not None
    assert route.method == "GET"
    assert route.path == "/users"
    assert route.tags == ["users"]
    assert route.summary == "List all users"
    assert route.description == "Return all users in the system."
    print(f"  GET /users: summary={route.summary!r}, tags={route.tags}")

    route2 = app.registry.lookup("POST", "/users")
    assert route2 is not None
    assert route2.method == "POST"
    assert route2.status_code == 201  # POST defaults to 201
    print(f"  POST /users: status_code={route2.status_code}")

    print("  [PASS] Basic route decorators work")


def demo_all_methods():
    """Show all HTTP method decorators."""
    print("\n--- Section 2: All HTTP Methods ---")

    app = IgniteApp()

    @app.get("/items")
    def list_items(req): return {"items": []}

    @app.post("/items")
    def create_item(req): return {"created": True}

    @app.put("/items/{id}")
    def replace_item(req): return {"replaced": True}

    @app.patch("/items/{id}")
    def update_item(req): return {"updated": True}

    @app.delete("/items/{id}")
    def delete_item(req): return {"deleted": True}

    assert len(app.registry) == 5
    methods = [r.method for r in app.registry.all_routes()]
    assert methods == ["GET", "POST", "PUT", "PATCH", "DELETE"]
    print(f"  Methods: {methods}")

    # Default status codes
    assert app.registry.lookup("GET", "/items").status_code == 200
    assert app.registry.lookup("POST", "/items").status_code == 201
    assert app.registry.lookup("DELETE", "/items/{id}").status_code == 204
    print("  Default status codes: GET=200, POST=201, DELETE=204")

    print("  [PASS] All HTTP methods work")


def demo_openapi_metadata():
    """Show OpenAPI metadata on routes."""
    print("\n--- Section 3: OpenAPI Metadata ---")

    app = IgniteApp()

    @app.get(
        "/products",
        tags=["products", "catalog"],
        summary="List products",
        description="Returns a paginated list of all products in the catalog.",
        deprecated=False,
    )
    def list_products(request):
        return {"products": []}

    @app.get(
        "/products/legacy",
        tags=["products"],
        summary="Legacy product list",
        deprecated=True,
    )
    def legacy_products(request):
        """This endpoint is deprecated. Use /products instead."""
        return {"products": []}

    route = app.registry.lookup("GET", "/products")
    assert route.tags == ["products", "catalog"]
    assert route.summary == "List products"
    assert route.deprecated is False
    print(f"  /products: tags={route.tags}, deprecated={route.deprecated}")

    legacy = app.registry.lookup("GET", "/products/legacy")
    assert legacy.deprecated is True
    print(f"  /products/legacy: deprecated={legacy.deprecated}")

    # Query by tag
    product_routes = app.registry.routes_by_tag("products")
    assert len(product_routes) == 2
    print(f"  Routes tagged 'products': {len(product_routes)}")

    catalog_routes = app.registry.routes_by_tag("catalog")
    assert len(catalog_routes) == 1
    print(f"  Routes tagged 'catalog': {len(catalog_routes)}")

    print("  [PASS] OpenAPI metadata works")


def demo_dispatching():
    """Show request dispatching through decorators."""
    print("\n--- Section 4: Request Dispatching ---")

    app = IgniteApp()

    @app.get("/hello")
    def hello(request):
        return {"message": "Hello, World!"}

    @app.post("/echo")
    def echo(request):
        return {"body": request.body.decode()}

    # Successful GET
    resp = app.dispatch(Request("GET", "/hello"))
    assert resp.status_code == 200
    assert resp.body == {"message": "Hello, World!"}
    print(f"  GET /hello -> {resp.status_code}: {resp.body}")

    # Successful POST
    resp2 = app.dispatch(Request("POST", "/echo", body=b"test data"))
    assert resp2.status_code == 201
    assert resp2.body["body"] == "test data"
    print(f"  POST /echo -> {resp2.status_code}: {resp2.body}")

    # 404 Not Found
    resp3 = app.dispatch(Request("GET", "/nonexistent"))
    assert resp3.status_code == 404
    print(f"  GET /nonexistent -> {resp3.status_code}: {resp3.body}")

    # 405 Method Not Allowed (path exists but wrong method)
    resp4 = app.dispatch(Request("DELETE", "/hello"))
    assert resp4.status_code == 405
    print(f"  DELETE /hello -> {resp4.status_code}: {resp4.body}")

    print("  [PASS] Dispatching works")


def demo_asgi_simulation():
    """Show the ASGI interface working."""
    print("\n--- Section 5: ASGI Simulation ---")

    app = IgniteApp()

    @app.get("/api/health")
    def health_check(request):
        return {"status": "healthy"}

    # Simulate ASGI call
    captured: dict[str, Any] = {"responses": []}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        captured["responses"].append(message)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/health",
        "query_string": b"",
        "headers": [],
    }

    asyncio.run(app(scope, receive, send))

    assert len(captured["responses"]) == 2
    start = captured["responses"][0]
    body_msg = captured["responses"][1]

    assert start["type"] == "http.response.start"
    assert start["status"] == 200
    print(f"  ASGI status: {start['status']}")

    body = json.loads(body_msg["body"].decode())
    assert body == {"status": "healthy"}
    print(f"  ASGI body: {body}")

    print("  [PASS] ASGI simulation works")


def demo_function_metadata():
    """Show that decorators preserve function metadata."""
    print("\n--- Section 6: Function Metadata ---")

    app = IgniteApp()

    @app.get("/test", tags=["testing"])
    def my_handler(request):
        """A test handler."""
        return {}

    # Handler is still callable
    assert callable(my_handler)
    print(f"  Handler callable: True")

    # Route info is attached to the function
    assert hasattr(my_handler, "_route_info")
    info = my_handler._route_info
    assert info.method == "GET"
    assert info.path == "/test"
    assert info.tags == ["testing"]
    print(f"  _route_info: {info}")

    # Auto-generated summary from function name
    app2 = IgniteApp()

    @app2.get("/auto")
    def fetch_all_records(request):
        return {}

    route = app2.registry.lookup("GET", "/auto")
    assert route.summary == "Fetch All Records"
    print(f"  Auto-summary: {route.summary!r} (from 'fetch_all_records')")

    print("  [PASS] Function metadata preserved")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    try:
        demo_basic_decorators()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_all_methods()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_openapi_metadata()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_dispatching()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_asgi_simulation()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        demo_function_metadata()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print("\n--- Summary ---")
    print("Route decorators give our Ignite framework:")
    print("  - @app.get(), @app.post(), @app.put(), @app.patch(), @app.delete()")
    print("  - OpenAPI metadata: tags, summary, description, deprecated")
    print("  - Route registry with (method, path) lookup")
    print("  - Request dispatching with 404/405 handling")
    print("  - ASGI-compatible interface")
    print("  - Preserved function metadata via _route_info")
    print("\nImplement the TODOs above to make all 6 sections pass!")
    print("Next up: Kata 50 -- automatic parameter injection!")


if __name__ == "__main__":
    main()
