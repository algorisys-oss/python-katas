"""
Kata 38 -- ASGI App Skeleton (Ignite begins!)
Run: python playground/38_asgi_app_skeleton.py

Build the first piece of the Ignite framework: an Ignite class that is
a proper ASGI callable. It handles lifespan events and HTTP requests,
with a simple routing mechanism. Tested by simulating ASGI calls directly.

To run with uvicorn (not tested here due to 5s constraint):
    # app.py
    from ignite import Ignite
    app = Ignite()

    @app.route("/")
    async def index():
        return "Hello, Ignite!"

    # Terminal: uvicorn app:app --reload

Completes within 5 seconds.
"""

import asyncio
import json
from typing import Any, Callable


# ===========================================================================
# SECTION 1: The Ignite Class -- Core ASGI App
# ===========================================================================

class Ignite:
    """A minimal ASGI web framework.

    This is the foundation of our framework. It:
    - Is an ASGI callable (implements __call__)
    - Handles lifespan events (startup/shutdown)
    - Routes HTTP requests to handler functions
    - Returns proper HTTP responses

    Usage with uvicorn:
        app = Ignite()

        @app.route("/")
        async def index():
            return "Hello, Ignite!"

        # uvicorn myapp:app --reload
    """

    def __init__(self) -> None:
        # Route registry: maps (method, path) -> handler
        self._routes: dict[tuple[str, str], Callable] = {}
        # Lifespan event handlers
        self._on_startup: list[Callable] = []
        self._on_shutdown: list[Callable] = []
        # Shared application state (available during lifespan)
        self.state: dict[str, Any] = {}

    # --- ASGI Interface ---

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """ASGI entry point -- called by the server for every connection.

        The server (uvicorn) calls this with:
        - scope: connection info (type, path, method, etc.)
        - receive: async callable to get request body / events
        - send: async callable to send response events
        """
        scope_type = scope["type"]

        if scope_type == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        elif scope_type == "http":
            await self._handle_http(scope, receive, send)
        else:
            # Ignore unknown scope types (e.g., websocket -- for now)
            pass

    # --- Lifespan Handling ---

    async def _handle_lifespan(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Handle ASGI lifespan events (startup/shutdown).

        The server sends lifespan events so we can:
        - startup: initialize DB pools, load config, warm caches
        - shutdown: close connections, flush buffers
        """
        while True:
            message = await receive()

            if message["type"] == "lifespan.startup":
                try:
                    # Run all registered startup handlers
                    for handler in self._on_startup:
                        result = handler(self.state)
                        # Support both sync and async handlers
                        if asyncio.iscoroutine(result):
                            await result
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    await send({
                        "type": "lifespan.startup.failed",
                        "message": str(exc),
                    })
                    return

            elif message["type"] == "lifespan.shutdown":
                try:
                    # Run all registered shutdown handlers
                    for handler in self._on_shutdown:
                        result = handler(self.state)
                        if asyncio.iscoroutine(result):
                            await result
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception:
                    await send({"type": "lifespan.shutdown.complete"})
                return

    # --- HTTP Handling ---

    async def _handle_http(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Handle an HTTP request.

        Steps:
        1. Read the request body from receive()
        2. Look up the route handler
        3. Call the handler
        4. Send the response via send()
        """
        # Read request body
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        method = scope["method"]
        path = scope["path"]

        # Look up route handler
        handler = self._routes.get((method, path))

        if handler is None:
            # Try method-agnostic route (registered with method="*")
            handler = self._routes.get(("*", path))

        if handler is not None:
            try:
                # Call the handler
                result = handler()
                if asyncio.iscoroutine(result):
                    result = await result

                # Convert result to response
                if isinstance(result, dict):
                    # Dict -> JSON response
                    response_body = json.dumps(result).encode("utf-8")
                    content_type = b"application/json"
                elif isinstance(result, bytes):
                    response_body = result
                    content_type = b"application/octet-stream"
                else:
                    # String or other -> text response
                    response_body = str(result).encode("utf-8")
                    content_type = b"text/plain; charset=utf-8"

                await self._send_response(send, 200, response_body, content_type)

            except Exception as exc:
                # Handler raised an error -> 500
                error_body = f"Internal Server Error: {exc}".encode("utf-8")
                await self._send_response(send, 500, error_body, b"text/plain")
        else:
            # No handler found -> 404
            not_found_body = f"404 Not Found: {method} {path}".encode("utf-8")
            await self._send_response(send, 404, not_found_body, b"text/plain")

    async def _send_response(
        self, send: Callable, status: int, body: bytes, content_type: bytes
    ) -> None:
        """Send an HTTP response (two ASGI messages)."""
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

    # --- Route Registration ---

    def route(self, path: str, methods: list[str] | None = None) -> Callable:
        """Register a route handler (decorator).

        Usage:
            @app.route("/hello")
            async def hello():
                return "Hello!"

            @app.route("/data", methods=["GET", "POST"])
            async def data():
                return {"key": "value"}
        """
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable) -> Callable:
            for method in methods:
                self._routes[(method, path)] = func
            return func

        return decorator

    def get(self, path: str) -> Callable:
        """Shorthand for @app.route(path, methods=["GET"])."""
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> Callable:
        """Shorthand for @app.route(path, methods=["POST"])."""
        return self.route(path, methods=["POST"])

    # --- Lifespan Event Registration ---

    def on_startup(self, func: Callable) -> Callable:
        """Register a startup handler.

        Usage:
            @app.on_startup
            async def startup(state):
                state["db"] = await connect_db()
        """
        self._on_startup.append(func)
        return func

    def on_shutdown(self, func: Callable) -> Callable:
        """Register a shutdown handler.

        Usage:
            @app.on_shutdown
            async def shutdown(state):
                await state["db"].close()
        """
        self._on_shutdown.append(func)
        return func


# ===========================================================================
# SECTION 2: ASGI Simulator (for testing without uvicorn)
# ===========================================================================

class AsgiSimulator:
    """Test harness that simulates an ASGI server.

    Instead of running uvicorn, we call the app directly with
    mock scope/receive/send to verify behavior.
    """

    def __init__(self, request_body: bytes = b""):
        self.request_body = request_body
        self.sent_messages: list[dict] = []
        self._body_sent = False

    async def receive(self) -> dict:
        """Simulate receiving the request body."""
        if not self._body_sent:
            self._body_sent = True
            return {
                "type": "http.request",
                "body": self.request_body,
                "more_body": False,
            }
        return {"type": "http.disconnect"}

    async def send(self, message: dict) -> None:
        """Capture sent messages."""
        self.sent_messages.append(message)

    @property
    def status_code(self) -> int | None:
        for msg in self.sent_messages:
            if msg["type"] == "http.response.start":
                return msg["status"]
        return None

    @property
    def response_body(self) -> bytes:
        for msg in self.sent_messages:
            if msg["type"] == "http.response.body":
                return msg.get("body", b"")
        return b""

    @property
    def response_headers(self) -> dict[str, str]:
        for msg in self.sent_messages:
            if msg["type"] == "http.response.start":
                return {
                    k.decode(): v.decode()
                    for k, v in msg.get("headers", [])
                }
        return {}

    async def simulate_request(
        self, app: Callable, method: str, path: str,
        body: bytes = b"",
    ) -> "AsgiSimulator":
        """Send a simulated HTTP request to the app."""
        self.request_body = body
        self._body_sent = False
        self.sent_messages = []

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "path": path,
            "root_path": "",
            "scheme": "http",
            "query_string": b"",
            "headers": [],
            "server": ("127.0.0.1", 8000),
            "client": ("127.0.0.1", 54321),
        }

        await app(scope, self.receive, self.send)
        return self


# ===========================================================================
# SECTION 3: Demos
# ===========================================================================

async def _demo_basic_routing():
    """Test the Ignite app with basic route registration."""
    app = Ignite()

    # Register routes using decorators
    @app.route("/")
    async def index():
        return "Hello, Ignite!"

    @app.route("/about")
    async def about():
        return "Ignite is a learning framework"

    @app.route("/json")
    async def json_endpoint():
        return {"framework": "Ignite", "version": "0.1.0", "kata": 38}

    @app.route("/greet", methods=["GET", "POST"])
    async def greet():
        return "Greetings!"

    # --- Test routes ---
    sim = AsgiSimulator()

    # GET /
    await sim.simulate_request(app, "GET", "/")
    print(f"  GET / -> {sim.status_code} | {sim.response_body.decode()}")
    assert sim.status_code == 200
    assert sim.response_body == b"Hello, Ignite!"

    # GET /about
    await sim.simulate_request(app, "GET", "/about")
    print(f"  GET /about -> {sim.status_code} | {sim.response_body.decode()}")
    assert sim.status_code == 200
    assert b"learning framework" in sim.response_body

    # GET /json -> JSON response
    await sim.simulate_request(app, "GET", "/json")
    data = json.loads(sim.response_body)
    print(f"  GET /json -> {sim.status_code} | {data}")
    assert sim.status_code == 200
    assert data["framework"] == "Ignite"
    assert data["kata"] == 38
    assert sim.response_headers["content-type"] == "application/json"

    # POST /greet (registered for both GET and POST)
    await sim.simulate_request(app, "POST", "/greet")
    print(f"  POST /greet -> {sim.status_code} | {sim.response_body.decode()}")
    assert sim.status_code == 200

    # GET /nonexistent -> 404
    await sim.simulate_request(app, "GET", "/nonexistent")
    print(f"  GET /nonexistent -> {sim.status_code} | {sim.response_body.decode()}")
    assert sim.status_code == 404

    # Verify server header
    assert sim.response_headers.get("server") == "Ignite/0.1"

    print("  [VALID] Basic routing works correctly")


def demo_basic_routing():
    asyncio.run(_demo_basic_routing())


async def _demo_shorthand_decorators():
    """Test the shorthand @app.get and @app.post decorators."""
    app = Ignite()

    @app.get("/users")
    async def list_users():
        return {"users": ["alice", "bob", "charlie"]}

    @app.post("/users")
    async def create_user():
        return {"created": True}

    sim = AsgiSimulator()

    # GET /users
    await sim.simulate_request(app, "GET", "/users")
    data = json.loads(sim.response_body)
    print(f"  GET /users -> {sim.status_code} | {data}")
    assert sim.status_code == 200
    assert len(data["users"]) == 3

    # POST /users
    await sim.simulate_request(app, "POST", "/users")
    data = json.loads(sim.response_body)
    print(f"  POST /users -> {sim.status_code} | {data}")
    assert sim.status_code == 200
    assert data["created"] is True

    # DELETE /users -> 404 (not registered)
    await sim.simulate_request(app, "DELETE", "/users")
    print(f"  DELETE /users -> {sim.status_code} (not registered)")
    assert sim.status_code == 404

    print("  [VALID] Shorthand decorators work correctly")


def demo_shorthand_decorators():
    asyncio.run(_demo_shorthand_decorators())


async def _demo_lifespan():
    """Test lifespan startup and shutdown events."""
    app = Ignite()
    events_log: list[str] = []

    @app.on_startup
    def on_start(state):
        state["db"] = "PostgresPool(connected)"
        state["cache"] = {"initialized": True}
        events_log.append("startup")

    @app.on_shutdown
    def on_stop(state):
        state["db"] = None
        state["cache"] = None
        events_log.append("shutdown")

    # Simulate lifespan
    lifespan_scope = {"type": "lifespan", "asgi": {"version": "3.0"}}

    message_iter = iter([
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ])
    sent_messages: list[dict] = []

    async def lifespan_receive():
        return next(message_iter)

    async def lifespan_send(message):
        sent_messages.append(message)

    await app(lifespan_scope, lifespan_receive, lifespan_send)

    print(f"  Events: {events_log}")
    print(f"  Messages: {[m['type'] for m in sent_messages]}")
    print(f"  State after startup: {app.state}")

    assert events_log == ["startup", "shutdown"]
    assert sent_messages[0]["type"] == "lifespan.startup.complete"
    assert sent_messages[1]["type"] == "lifespan.shutdown.complete"

    print("  [VALID] Lifespan events handled correctly")


def demo_lifespan():
    asyncio.run(_demo_lifespan())


async def _demo_error_handling():
    """Test that handler errors produce 500 responses."""
    app = Ignite()

    @app.get("/boom")
    async def explode():
        raise ValueError("Something went wrong!")

    @app.get("/sync")
    def sync_handler():
        return "Sync handlers work too!"

    sim = AsgiSimulator()

    # Error handler -> 500
    await sim.simulate_request(app, "GET", "/boom")
    print(f"  GET /boom -> {sim.status_code} | {sim.response_body.decode()}")
    assert sim.status_code == 500
    assert b"Something went wrong" in sim.response_body

    # Sync handler (non-async)
    await sim.simulate_request(app, "GET", "/sync")
    print(f"  GET /sync -> {sim.status_code} | {sim.response_body.decode()}")
    assert sim.status_code == 200
    assert sim.response_body == b"Sync handlers work too!"

    print("  [VALID] Error handling works correctly")


def demo_error_handling():
    asyncio.run(_demo_error_handling())


def demo_uvicorn_usage():
    """Show how Ignite would be used with uvicorn."""
    print("  How to use Ignite with uvicorn:")
    print()
    print("    # app.py")
    print("    from ignite import Ignite")
    print()
    print("    app = Ignite()")
    print()
    print('    @app.route("/")')
    print("    async def index():")
    print('        return "Hello, Ignite!"')
    print()
    print('    @app.get("/api/data")')
    print("    async def get_data():")
    print('        return {"status": "ok"}')
    print()
    print("    @app.on_startup")
    print("    async def startup(state):")
    print('        state["db"] = await connect_db()')
    print()
    print("    # Terminal:")
    print("    #   pip install uvicorn")
    print("    #   uvicorn app:app --reload --port 8000")
    print()
    print("  uvicorn will:")
    print("    1. Import your app object")
    print("    2. Send lifespan.startup event")
    print("    3. Listen on port 8000 for TCP connections")
    print("    4. For each request: build scope, call app(scope, receive, send)")
    print("    5. On ctrl+c: send lifespan.shutdown event")

    # Verify the Ignite class is a proper ASGI callable
    app = Ignite()
    assert callable(app), "Ignite must be callable"
    assert asyncio.iscoroutinefunction(app.__call__), "Ignite.__call__ must be async"
    print()
    print(f"  Ignite() is callable: {callable(app)}")
    print(f"  Ignite.__call__ is async: {asyncio.iscoroutinefunction(app.__call__)}")
    print("  [VALID] Ignite is a proper ASGI app callable")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Basic Routing ---
    print("--- Section 1: Basic Routing ---")
    demo_basic_routing()
    print()

    # --- Section 2: Shorthand Decorators ---
    print("--- Section 2: Shorthand Decorators ---")
    demo_shorthand_decorators()
    print()

    # --- Section 3: Lifespan Events ---
    print("--- Section 3: Lifespan Events ---")
    demo_lifespan()
    print()

    # --- Section 4: Error Handling ---
    print("--- Section 4: Error Handling ---")
    demo_error_handling()
    print()

    # --- Section 5: uvicorn Usage ---
    print("--- Section 5: Using Ignite with uvicorn ---")
    demo_uvicorn_usage()
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("The Ignite ASGI framework skeleton is ready:")
    print("  - Ignite class is an ASGI callable (scope, receive, send)")
    print("  - @app.route() decorator for path-based routing")
    print("  - @app.get() and @app.post() shorthand decorators")
    print("  - @app.on_startup / @app.on_shutdown for lifespan events")
    print("  - Dict return values auto-serialize to JSON")
    print("  - String return values become text/plain responses")
    print("  - Handler errors produce 500 responses")
    print("  - Works with uvicorn: uvicorn myapp:app --reload")
    print()
    print("All 5 sections passed. Ignite ASGI skeleton complete!")
    print("Next up: Kata 39 -- building the Request object!")
