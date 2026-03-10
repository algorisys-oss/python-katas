"""
Kata 41 -- Router
Run: python playground/41_router.py

Build an Ignite Router class that maps HTTP method + path combinations
to handler functions, supports 404 (not found) and 405 (method not
allowed) responses, and dispatches incoming requests.

Completes within 5 seconds.
"""

import asyncio
import json
from urllib.parse import parse_qs


# ===========================================================================
# Inline dependencies from previous katas (Request + Response)
# ===========================================================================

class Request:
    """Minimal Request class (from Kata 39)."""

    def __init__(self, scope: dict, receive: callable):
        self._scope = scope
        self._receive = receive
        self._body: bytes | None = None

    @property
    def method(self) -> str:
        return self._scope.get("method", "GET")

    @property
    def path(self) -> str:
        return self._scope.get("path", "/")

    @property
    def headers(self) -> dict[str, str]:
        raw = self._scope.get("headers", [])
        return {
            (k.decode() if isinstance(k, bytes) else k).lower():
            (v.decode() if isinstance(v, bytes) else v)
            for k, v in raw
        }

    @property
    def query_params(self) -> dict[str, list[str]]:
        qs = self._scope.get("query_string", b"")
        if isinstance(qs, bytes):
            qs = qs.decode()
        return parse_qs(qs)

    async def body(self) -> bytes:
        if self._body is not None:
            return self._body
        chunks = []
        while True:
            msg = await self._receive()
            chunks.append(msg.get("body", b""))
            if not msg.get("more_body", False):
                break
        self._body = b"".join(chunks)
        return self._body

    async def json(self) -> dict:
        return json.loads(await self.body())

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"


class Response:
    """Minimal Response class (from Kata 40)."""

    media_type: str | None = None
    charset: str = "utf-8"

    def __init__(self, content: str | bytes = b"", status_code: int = 200,
                 headers: dict[str, str] | None = None,
                 media_type: str | None = None):
        self.status_code = status_code
        self.media_type = media_type or self.media_type
        self.body = content.encode(self.charset) if isinstance(content, str) else content
        self.raw_headers = self._build_headers(headers or {})

    def _build_headers(self, extra: dict[str, str]) -> list[tuple[bytes, bytes]]:
        h = {}
        if self.media_type:
            ct = self.media_type
            if self.charset and "text" in ct:
                ct += f"; charset={self.charset}"
            h["content-type"] = ct
        h["content-length"] = str(len(self.body))
        for k, v in extra.items():
            h[k.lower()] = v
        return [(k.encode(), v.encode()) for k, v in h.items()]

    async def __call__(self, scope, receive, send):
        await send({"type": "http.response.start", "status": self.status_code,
                     "headers": self.raw_headers})
        await send({"type": "http.response.body", "body": self.body})


class JSONResponse(Response):
    media_type = "application/json"

    def __init__(self, content=None, status_code=200, headers=None):
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        super().__init__(content=body, status_code=status_code,
                         headers=headers, media_type=self.media_type)


class PlainTextResponse(Response):
    media_type = "text/plain"

    def __init__(self, content="", status_code=200, headers=None):
        super().__init__(content=content, status_code=status_code,
                         headers=headers, media_type=self.media_type)


# ===========================================================================
# SECTION 1: Route Registration
# ===========================================================================

class Route:
    """A single registered route: method + path -> handler.

    The handler is an async function that takes a Request and returns
    a Response.
    """

    def __init__(self, method: str, path: str, handler: callable):
        self.method = method.upper()
        self.path = path
        self.handler = handler

    def matches(self, method: str, path: str) -> bool:
        """Check if this route matches the given method and path."""
        return self.method == method.upper() and self.path == path

    def __repr__(self) -> str:
        return f"<Route {self.method} {self.path} -> {self.handler.__name__}>"


# ===========================================================================
# SECTION 2: Router Class
# ===========================================================================

class Router:
    """Maps HTTP requests to handler functions.

    The router maintains a list of Route objects and provides:
    - add_route(method, path, handler) for manual registration
    - .get(), .post(), .put(), .delete() decorator shortcuts
    - dispatch(request) to find and call the right handler
    - Proper 404 and 405 error responses
    """

    def __init__(self):
        self.routes: list[Route] = []

    # -- Registration methods ----------------------------------------------

    def add_route(self, method: str, path: str, handler: callable) -> None:
        """Register a route manually.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (e.g., '/api/users')
            handler: Async function(Request) -> Response
        """
        self.routes.append(Route(method, path, handler))

    def route(self, path: str, methods: list[str] | None = None) -> callable:
        """Decorator to register a handler for one or more methods.

        Usage:
            @router.route('/users', methods=['GET', 'POST'])
            async def users(request):
                ...
        """
        if methods is None:
            methods = ["GET"]

        def decorator(handler: callable) -> callable:
            for method in methods:
                self.add_route(method, path, handler)
            return handler

        return decorator

    def get(self, path: str) -> callable:
        """Decorator shortcut for GET routes."""
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> callable:
        """Decorator shortcut for POST routes."""
        return self.route(path, methods=["POST"])

    def put(self, path: str) -> callable:
        """Decorator shortcut for PUT routes."""
        return self.route(path, methods=["PUT"])

    def delete(self, path: str) -> callable:
        """Decorator shortcut for DELETE routes."""
        return self.route(path, methods=["DELETE"])

    # -- Dispatch ----------------------------------------------------------

    def _find_routes_for_path(self, path: str) -> list[Route]:
        """Find all routes registered for a given path (any method)."""
        return [r for r in self.routes if r.path == path]

    def _find_route(self, method: str, path: str) -> Route | None:
        """Find the exact route matching method + path."""
        for r in self.routes:
            if r.matches(method, path):
                return r
        return None

    async def dispatch(self, request: Request) -> Response:
        """Dispatch a request to the matching handler.

        Returns:
            - The handler's response if a matching route is found.
            - 405 Method Not Allowed if the path exists but method doesn't.
            - 404 Not Found if no route matches the path.
        """
        method = request.method
        path = request.path

        # First, try to find an exact match
        route = self._find_route(method, path)
        if route is not None:
            return await route.handler(request)

        # Path exists but wrong method -> 405
        routes_for_path = self._find_routes_for_path(path)
        if routes_for_path:
            allowed = sorted(set(r.method for r in routes_for_path))
            return JSONResponse(
                content={
                    "error": "Method Not Allowed",
                    "detail": f"{method} {path} not allowed",
                    "allowed_methods": allowed,
                },
                status_code=405,
                headers={"allow": ", ".join(allowed)},
            )

        # No matching path at all -> 404
        return JSONResponse(
            content={
                "error": "Not Found",
                "detail": f"{path} not found",
            },
            status_code=404,
        )

    # -- ASGI interface ----------------------------------------------------

    async def __call__(self, scope: dict, receive: callable, send: callable) -> None:
        """ASGI application interface.

        Creates a Request from the scope/receive, dispatches it,
        and sends the resulting Response.
        """
        request = Request(scope, receive)
        response = await self.dispatch(request)
        await response(scope, receive, send)

    # -- Utility -----------------------------------------------------------

    def list_routes(self) -> list[str]:
        """Return a list of registered routes as strings."""
        return [f"{r.method} {r.path}" for r in self.routes]


# ===========================================================================
# SECTION 3: Test Helpers
# ===========================================================================

def make_scope(method="GET", path="/", query_string="", headers=None):
    """Create a mock ASGI scope."""
    raw_headers = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode(), v.encode()))
    return {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query_string.encode(),
        "headers": raw_headers,
    }


def make_receive(body=b""):
    """Create a mock ASGI receive callable."""
    sent = False
    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}
    return receive


class MessageCollector:
    """Captures ASGI send messages for inspection."""

    def __init__(self):
        self.messages = []

    async def send(self, message):
        self.messages.append(message)

    @property
    def status_code(self):
        for m in self.messages:
            if m["type"] == "http.response.start":
                return m["status"]
        return 0

    @property
    def headers(self):
        for m in self.messages:
            if m["type"] == "http.response.start":
                return {k.decode(): v.decode() for k, v in m.get("headers", [])}
        return {}

    @property
    def body(self):
        return b"".join(
            m.get("body", b"") for m in self.messages
            if m["type"] == "http.response.body"
        )

    @property
    def json(self):
        return json.loads(self.body)


# ===========================================================================
# SECTION 4: Demonstrations
# ===========================================================================

async def demo_route_registration():
    """Demonstrate registering routes with the Router."""
    router = Router()

    # Method 1: manual registration
    async def index(request):
        return PlainTextResponse("Welcome to Ignite!")

    router.add_route("GET", "/", index)

    # Method 2: decorator syntax
    @router.get("/api/health")
    async def health(request):
        return JSONResponse({"status": "ok"})

    @router.post("/api/users")
    async def create_user(request):
        return JSONResponse({"created": True}, status_code=201)

    # Method 3: multi-method decorator
    @router.route("/api/items", methods=["GET", "POST"])
    async def items(request):
        if request.method == "GET":
            return JSONResponse({"items": []})
        return JSONResponse({"created": True}, status_code=201)

    routes = router.list_routes()
    print(f"  Registered routes:")
    for r in routes:
        print(f"    {r}")

    assert len(router.routes) == 5
    assert "GET /" in routes
    assert "GET /api/health" in routes
    assert "POST /api/users" in routes
    assert "GET /api/items" in routes
    assert "POST /api/items" in routes

    print("  [PASS] Route registration works correctly")
    return router


async def demo_dispatch_success(router: Router):
    """Demonstrate successful request dispatch."""
    # GET /
    scope = make_scope("GET", "/")
    req = Request(scope, make_receive())
    resp = await router.dispatch(req)

    collector = MessageCollector()
    await resp(scope, None, collector.send)

    print(f"  GET / -> {collector.status_code}: {collector.body.decode()!r}")
    assert collector.status_code == 200
    assert collector.body == b"Welcome to Ignite!"

    # GET /api/health
    scope = make_scope("GET", "/api/health")
    req = Request(scope, make_receive())
    resp = await router.dispatch(req)

    collector = MessageCollector()
    await resp(scope, None, collector.send)

    print(f"  GET /api/health -> {collector.status_code}: {collector.body.decode()!r}")
    assert collector.status_code == 200
    assert collector.json == {"status": "ok"}

    # POST /api/users
    scope = make_scope("POST", "/api/users")
    req = Request(scope, make_receive(json.dumps({"name": "Alice"}).encode()))
    resp = await router.dispatch(req)

    collector = MessageCollector()
    await resp(scope, None, collector.send)

    print(f"  POST /api/users -> {collector.status_code}: {collector.body.decode()!r}")
    assert collector.status_code == 201

    print("  [PASS] Dispatch to matching handlers works")


async def demo_404_not_found(router: Router):
    """Demonstrate 404 response for unknown paths."""
    scope = make_scope("GET", "/nonexistent")
    req = Request(scope, make_receive())
    resp = await router.dispatch(req)

    collector = MessageCollector()
    await resp(scope, None, collector.send)

    print(f"  GET /nonexistent -> {collector.status_code}: {collector.body.decode()!r}")
    assert collector.status_code == 404
    assert collector.json["error"] == "Not Found"
    assert "/nonexistent" in collector.json["detail"]

    print("  [PASS] 404 Not Found works correctly")


async def demo_405_method_not_allowed(router: Router):
    """Demonstrate 405 response for wrong methods."""
    # DELETE /api/health -- path exists (GET) but DELETE is not registered
    scope = make_scope("DELETE", "/api/health")
    req = Request(scope, make_receive())
    resp = await router.dispatch(req)

    collector = MessageCollector()
    await resp(scope, None, collector.send)

    print(f"  DELETE /api/health -> {collector.status_code}: {collector.body.decode()!r}")
    assert collector.status_code == 405
    assert collector.json["error"] == "Method Not Allowed"
    assert "GET" in collector.json["allowed_methods"]
    assert collector.headers["allow"] == "GET"

    # PUT /api/items -- path exists (GET, POST) but PUT is not registered
    scope = make_scope("PUT", "/api/items")
    req = Request(scope, make_receive())
    resp = await router.dispatch(req)

    collector = MessageCollector()
    await resp(scope, None, collector.send)

    print(f"  PUT /api/items -> {collector.status_code}: {collector.body.decode()!r}")
    assert collector.status_code == 405
    assert "GET" in collector.json["allowed_methods"]
    assert "POST" in collector.json["allowed_methods"]
    assert collector.headers["allow"] == "GET, POST"

    print("  [PASS] 405 Method Not Allowed works correctly")


async def demo_asgi_interface(router: Router):
    """Demonstrate the Router as an ASGI application."""
    # The router itself is an ASGI app -- call it directly with scope/receive/send
    scope = make_scope("GET", "/api/health")
    receive = make_receive()
    collector = MessageCollector()

    # Call router as an ASGI app
    await router(scope, receive, collector.send)

    print(f"  ASGI call GET /api/health -> {collector.status_code}")
    assert collector.status_code == 200
    assert collector.json == {"status": "ok"}

    # 404 via ASGI interface
    scope = make_scope("GET", "/missing")
    collector = MessageCollector()
    await router(scope, make_receive(), collector.send)

    print(f"  ASGI call GET /missing -> {collector.status_code}")
    assert collector.status_code == 404

    print("  [PASS] Router works as an ASGI application")


# ===========================================================================
# MAIN
# ===========================================================================

async def main():
    print("--- Section 1: Route Registration ---")
    router = await demo_route_registration()
    print()

    print("--- Section 2: Successful Dispatch ---")
    await demo_dispatch_success(router)
    print()

    print("--- Section 3: 404 Not Found ---")
    await demo_404_not_found(router)
    print()

    print("--- Section 4: 405 Method Not Allowed ---")
    await demo_405_method_not_allowed(router)
    print()

    print("--- Section 5: ASGI Interface ---")
    await demo_asgi_interface(router)
    print()

    print("--- Summary ---")
    print("The Router is the traffic controller of a web framework:")
    print("  - Register routes with method + path -> handler")
    print("  - Use decorators (@router.get, @router.post) for clean syntax")
    print("  - Dispatch incoming requests to the right handler")
    print("  - Return 404 for unknown paths")
    print("  - Return 405 with Allow header for wrong methods")
    print("  - Acts as a full ASGI application via __call__")
    print()
    print("All 5 sections passed. Router mastered!")
    print("Next up: Kata 42 -- Path Parameters")


if __name__ == "__main__":
    asyncio.run(main())
