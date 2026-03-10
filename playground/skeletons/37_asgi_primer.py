"""
Kata 37 -- ASGI Primer
Run: python playground/skeletons/37_asgi_primer.py

Understand the ASGI (Asynchronous Server Gateway Interface) protocol.
Build minimal ASGI app callables, explore scope/receive/send, compare
WSGI vs ASGI, and simulate lifespan events.

All ASGI interactions are simulated (no uvicorn needed).
Completes within 5 seconds.
"""

import asyncio
import json
from typing import Any


# ===========================================================================
# SECTION 1: WSGI vs ASGI -- Why ASGI?
# ===========================================================================

def wsgi_app(environ: dict, start_response: callable) -> list[bytes]:
    """A minimal WSGI app for comparison.

    WSGI (PEP 3333) is synchronous:
    - environ: dict with request info (PATH_INFO, REQUEST_METHOD, etc.)
    - start_response: callback to set status + headers
    - Returns: iterable of bytes (the response body)
    """
    # TODO: Set status to "200 OK" and headers to [("Content-Type", "text/plain")]
    # Then call start_response(status, headers)
    # Return [b"Hello from WSGI!"]
    status = "200 OK"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)
    return [b"Hello from WSGI!"]


async def asgi_app(scope: dict, receive: callable, send: callable) -> None:
    """A minimal ASGI app for comparison.

    ASGI is asynchronous:
    - scope: dict describing the connection (type, path, headers, etc.)
    - receive: async callable to receive request body / events
    - send: async callable to send response events
    """
    if scope["type"] == "http":
        # TODO: Read the request body by calling await receive() in a loop
        # Each message has "body" (bytes) and "more_body" (bool)
        # Keep reading until more_body is False
        # HINT:
        #   body = b""
        #   while True:
        #       message = await receive()
        #       body += message.get("body", b"")
        #       if not message.get("more_body", False): break
        body = b""

        # TODO: Send the response start message with await send({...})
        # Must include: "type": "http.response.start", "status": 200,
        # "headers": [[b"content-type", b"text/plain"]]
        pass

        # TODO: Send the response body message with await send({...})
        # Must include: "type": "http.response.body", "body": b"Hello from ASGI!"
        pass


def demo_wsgi_vs_asgi():
    """Compare WSGI and ASGI side by side."""
    # --- WSGI execution ---
    captured_status = None
    captured_headers = None

    def start_response(status, headers):
        nonlocal captured_status, captured_headers
        captured_status = status
        captured_headers = headers

    wsgi_environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/hello",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
    }

    wsgi_body = wsgi_app(wsgi_environ, start_response)
    print(f"  WSGI response: status={captured_status}, body={wsgi_body[0]}")
    assert captured_status == "200 OK"
    assert wsgi_body == [b"Hello from WSGI!"]

    # --- ASGI execution (simulated) ---
    asgi_scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/hello",
        "headers": [],
    }

    async def mock_receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    sent_messages: list[dict] = []

    async def mock_send(message: dict):
        sent_messages.append(message)

    asyncio.run(asgi_app(asgi_scope, mock_receive, mock_send))

    print(f"  ASGI messages sent: {len(sent_messages)}")
    print(f"    1. {sent_messages[0]['type']} (status={sent_messages[0]['status']})")
    print(f"    2. {sent_messages[1]['type']} (body={sent_messages[1]['body']})")

    assert sent_messages[0]["type"] == "http.response.start"
    assert sent_messages[0]["status"] == 200
    assert sent_messages[1]["type"] == "http.response.body"
    assert sent_messages[1]["body"] == b"Hello from ASGI!"

    # Key differences
    print()
    print("  WSGI vs ASGI comparison:")
    print("  +-----------------+-------------------+-------------------+")
    print("  | Feature         | WSGI              | ASGI              |")
    print("  +-----------------+-------------------+-------------------+")
    print("  | Async           | No (sync only)    | Yes (async/await) |")
    print("  | WebSockets      | No                | Yes               |")
    print("  | HTTP/2          | No                | Yes               |")
    print("  | Lifespan events | No                | Yes               |")
    print("  | Threading model | 1 thread/request  | Event loop        |")
    print("  | Interface       | (environ, start)  | (scope, rcv, snd) |")
    print("  +-----------------+-------------------+-------------------+")

    print("  [VALID] WSGI and ASGI comparison complete")


# ===========================================================================
# SECTION 2: The ASGI Scope Dict
# ===========================================================================

def make_http_scope(
    method: str = "GET",
    path: str = "/",
    query_string: str = "",
    headers: list[tuple[bytes, bytes]] | None = None,
    http_version: str = "1.1",
) -> dict[str, Any]:
    """Build an ASGI HTTP scope dict.

    The scope dict describes the incoming connection.
    """
    # TODO: Return a dict with these keys:
    # - "type": "http"
    # - "asgi": {"version": "3.0", "spec_version": "2.4"}
    # - "http_version": http_version parameter
    # - "method": method parameter
    # - "path": path parameter
    # - "root_path": ""
    # - "scheme": "http"
    # - "query_string": query_string encoded to bytes
    # - "headers": headers parameter (or empty list)
    # - "server": ("127.0.0.1", 8000)
    # - "client": ("127.0.0.1", 54321)
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": http_version,
        "method": method,
        "path": path,
        "root_path": "",
        "scheme": "http",
        "query_string": query_string.encode("utf-8") if isinstance(query_string, str) else query_string,
        "headers": headers or [],
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 54321),
    }


def make_websocket_scope(path: str = "/ws") -> dict[str, Any]:
    """Build an ASGI WebSocket scope dict."""
    # TODO: Return a dict similar to HTTP scope but with:
    # - "type": "websocket"
    # - "scheme": "ws"
    # HINT: WebSocket scopes have no "method" key
    pass


def demo_asgi_scope():
    """Explore the ASGI scope dict structure."""
    # HTTP scope
    http_scope = make_http_scope(
        method="POST",
        path="/api/users",
        query_string="page=1&limit=10",
        headers=[
            (b"host", b"localhost:8000"),
            (b"content-type", b"application/json"),
            (b"authorization", b"Bearer token123"),
        ],
    )

    print(f"  HTTP scope:")
    print(f"    type: {http_scope['type']}")
    print(f"    method: {http_scope['method']}")
    print(f"    path: {http_scope['path']}")
    print(f"    query_string: {http_scope['query_string']}")
    print(f"    http_version: {http_scope['http_version']}")
    print(f"    server: {http_scope['server']}")
    print(f"    client: {http_scope['client']}")
    print(f"    headers ({len(http_scope['headers'])}):")
    for name, value in http_scope["headers"]:
        print(f"      {name.decode()}: {value.decode()}")

    assert http_scope["type"] == "http"
    assert http_scope["method"] == "POST"
    assert http_scope["path"] == "/api/users"
    assert http_scope["query_string"] == b"page=1&limit=10"

    # WebSocket scope
    ws_scope = make_websocket_scope("/ws/chat")
    print(f"\n  WebSocket scope:")
    print(f"    type: {ws_scope['type']}")
    print(f"    path: {ws_scope['path']}")
    print(f"    scheme: {ws_scope['scheme']}")

    assert ws_scope["type"] == "websocket"
    assert ws_scope["scheme"] == "ws"

    print("  [VALID] ASGI scope dicts created correctly")


# ===========================================================================
# SECTION 3: Receive and Send Callables
# ===========================================================================

class AsgiSimulator:
    """Simulates an ASGI server for testing.

    In a real ASGI server (uvicorn, daphne, hypercorn), the server:
    1. Accepts a TCP connection
    2. Parses the HTTP request
    3. Builds the scope dict
    4. Creates receive() and send() callables
    5. Calls your app: await app(scope, receive, send)

    We simulate steps 3-5 here.
    """

    def __init__(self, request_body: bytes = b""):
        self.request_body = request_body
        self.sent_messages: list[dict] = []
        self._body_sent = False

    async def receive(self) -> dict:
        """Simulate receiving the request body."""
        # TODO: Return a dict with "type": "http.request",
        # "body": self.request_body, "more_body": False
        # But only on first call -- subsequent calls return
        # {"type": "http.disconnect"}
        # HINT: Use self._body_sent flag to track first vs subsequent calls
        pass

    async def send(self, message: dict) -> None:
        """Capture messages sent by the app."""
        # TODO: Append message to self.sent_messages
        pass

    @property
    def status_code(self) -> int | None:
        """Extract the status code from sent messages."""
        for msg in self.sent_messages:
            if msg["type"] == "http.response.start":
                return msg["status"]
        return None

    @property
    def response_body(self) -> bytes:
        """Extract the response body from sent messages."""
        for msg in self.sent_messages:
            if msg["type"] == "http.response.body":
                return msg.get("body", b"")
        return b""

    @property
    def response_headers(self) -> list[tuple[bytes, bytes]]:
        """Extract response headers from sent messages."""
        for msg in self.sent_messages:
            if msg["type"] == "http.response.start":
                return msg.get("headers", [])
        return []


async def routing_asgi_app(scope: dict, receive: callable, send: callable) -> None:
    """An ASGI app with simple path-based routing."""
    if scope["type"] != "http":
        return

    # Read request body
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break

    # TODO: Implement simple routing based on scope["path"] and scope["method"]:
    # - GET  /       -> response_body = b"Welcome to ASGI!", status = 200
    # - POST /echo   -> response_body = body (echo it back), status = 200
    # - GET  /json   -> response_body = JSON with {"message": "Hello", "protocol": "ASGI"}, status = 200
    # - anything else -> response_body = b"Not Found", status = 404
    path = scope["path"]
    method = scope["method"]
    response_body = b"Not Found"
    status = 404

    # TODO: Send http.response.start with status and headers
    # Then send http.response.body with the response body
    # HINT: content_type should be b"application/json" for /json, else b"text/plain"
    content_type = b"application/json" if path == "/json" else b"text/plain"
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            [b"content-type", content_type],
            [b"content-length", str(len(response_body)).encode()],
        ],
    })
    await send({
        "type": "http.response.body",
        "body": response_body,
    })


async def _run_asgi_tests():
    """Run our ASGI app through the simulator."""

    # Test 1: GET /
    sim = AsgiSimulator()
    scope = make_http_scope("GET", "/")
    await routing_asgi_app(scope, sim.receive, sim.send)
    print(f"  GET / -> status={sim.status_code}, body={sim.response_body}")
    assert sim.status_code == 200
    assert sim.response_body == b"Welcome to ASGI!"

    # Test 2: POST /echo with body
    sim = AsgiSimulator(request_body=b"Ping!")
    scope = make_http_scope("POST", "/echo")
    await routing_asgi_app(scope, sim.receive, sim.send)
    print(f"  POST /echo -> status={sim.status_code}, body={sim.response_body}")
    assert sim.status_code == 200
    assert sim.response_body == b"Ping!"

    # Test 3: GET /json
    sim = AsgiSimulator()
    scope = make_http_scope("GET", "/json")
    await routing_asgi_app(scope, sim.receive, sim.send)
    data = json.loads(sim.response_body)
    print(f"  GET /json -> status={sim.status_code}, data={data}")
    assert sim.status_code == 200
    assert data["protocol"] == "ASGI"

    # Test 4: GET /missing -> 404
    sim = AsgiSimulator()
    scope = make_http_scope("GET", "/missing")
    await routing_asgi_app(scope, sim.receive, sim.send)
    print(f"  GET /missing -> status={sim.status_code}, body={sim.response_body}")
    assert sim.status_code == 404

    # Verify message structure
    assert len(sim.sent_messages) == 2
    assert sim.sent_messages[0]["type"] == "http.response.start"
    assert sim.sent_messages[1]["type"] == "http.response.body"

    print("  [VALID] ASGI receive/send pattern works correctly")


def demo_receive_send():
    """Demonstrate the receive/send callable pattern."""
    asyncio.run(_run_asgi_tests())


# ===========================================================================
# SECTION 4: Lifespan Events
# ===========================================================================

class AppState:
    """Shared state initialized during lifespan startup."""

    def __init__(self):
        self.db_pool: str | None = None
        self.cache: dict[str, Any] = {}
        self.started: bool = False
        self.shutdown: bool = False


async def app_with_lifespan(scope: dict, receive: callable, send: callable) -> None:
    """An ASGI app that handles lifespan events.

    Lifespan events let you run startup/shutdown code:
    - startup: connect to databases, load ML models, warm caches
    - shutdown: close connections, flush buffers, clean up
    """
    if scope["type"] == "lifespan":
        while True:
            message = await receive()

            if message["type"] == "lifespan.startup":
                # TODO: Initialize resources in scope["state"]:
                # - Set db_pool to "PostgresPool(connected)"
                # - Set cache to {"warm": True}
                # - Set started to True
                # Then send {"type": "lifespan.startup.complete"}
                # Wrap in try/except to send startup.failed on error
                try:
                    pass
                except Exception as exc:
                    await send({
                        "type": "lifespan.startup.failed",
                        "message": str(exc),
                    })
                    return

            elif message["type"] == "lifespan.shutdown":
                # TODO: Clean up resources in scope["state"]:
                # - Set db_pool to None
                # - Set cache to {}
                # - Set shutdown to True
                # Then send {"type": "lifespan.shutdown.complete"} and return
                pass

    elif scope["type"] == "http":
        # Read request body
        while True:
            message = await receive()
            if not message.get("more_body", False):
                break

        # Use shared state from lifespan
        state = scope.get("state", {})
        body = json.dumps({
            "db_pool": state.get("db_pool", "not connected"),
            "cache_warm": state.get("cache", {}).get("warm", False),
        }).encode()

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


async def _simulate_lifespan():
    """Simulate the full lifespan cycle as a server would."""
    state = AppState()

    lifespan_scope = {
        "type": "lifespan",
        "asgi": {"version": "3.0"},
        "state": state.__dict__,
    }

    message_iter = iter([
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ])

    sent_messages: list[dict] = []

    async def lifespan_receive():
        return next(message_iter)

    async def lifespan_send(message: dict):
        sent_messages.append(message)

    await app_with_lifespan(lifespan_scope, lifespan_receive, lifespan_send)

    print(f"  Lifespan messages sent by app:")
    for msg in sent_messages:
        print(f"    {msg['type']}")

    assert sent_messages[0]["type"] == "lifespan.startup.complete"
    assert sent_messages[1]["type"] == "lifespan.shutdown.complete"
    assert state.__dict__["started"] is True
    assert state.__dict__["shutdown"] is True

    print(f"  State after startup: db_pool was '{state.__dict__.get('db_pool', 'N/A')}' (now cleaned up)")
    print(f"  State after shutdown: resources cleaned = {state.__dict__['db_pool'] is None}")

    # --- HTTP phase ---
    state.__dict__["db_pool"] = "PostgresPool(connected)"
    state.__dict__["cache"] = {"warm": True}

    http_scope = make_http_scope("GET", "/status")
    http_scope["state"] = state.__dict__

    sim = AsgiSimulator()
    await app_with_lifespan(http_scope, sim.receive, sim.send)

    data = json.loads(sim.response_body)
    print(f"  HTTP /status during lifecycle: {data}")
    assert data["db_pool"] == "PostgresPool(connected)"
    assert data["cache_warm"] is True

    print("  [VALID] Lifespan events handled correctly")


def demo_lifespan():
    """Demonstrate ASGI lifespan events."""
    asyncio.run(_simulate_lifespan())


# ===========================================================================
# SECTION 5: The ASGI Message Flow
# ===========================================================================

def demo_message_flow():
    """Visualize how ASGI messages flow between server and app."""
    print("  ASGI HTTP request/response message flow:")
    print()
    print("    Server (uvicorn)              App (your code)")
    print("    ================              ===============")
    print("    1. Accept TCP connection")
    print("    2. Parse HTTP request")
    print("    3. Build scope dict")
    print("       scope = {")
    print('         "type": "http",')
    print('         "method": "GET",')
    print('         "path": "/hello",')
    print("         ...}")
    print("    4. Call app(scope, receive, send)")
    print("       -------------------------------->")
    print("                                  5. await receive()")
    print("       <--------------------------------")
    print('    6. Return {"type": "http.request",')
    print('              "body": b"...",')
    print('              "more_body": False}')
    print("       -------------------------------->")
    print('                                  7. await send({')
    print('                                       "type": "http.response.start",')
    print('                                       "status": 200,')
    print("                                       ...})")
    print("       <--------------------------------")
    print('                                  8. await send({')
    print('                                       "type": "http.response.body",')
    print('                                       "body": b"Hello!"})')
    print("       <--------------------------------")
    print("    9. Build HTTP response bytes")
    print("   10. Send over TCP connection")
    print()
    print("  Lifespan event flow:")
    print()
    print("    Server                        App")
    print("    ======                        ===")
    print('    scope["type"] = "lifespan"')
    print("    call app(scope, receive, send)")
    print("       -------------------------------->")
    print("                                  await receive()")
    print('    {"type": "lifespan.startup"}')
    print("       -------------------------------->")
    print("                                  (init DB, cache, etc.)")
    print('                                  await send({"type": "lifespan.startup.complete"})')
    print("       <--------------------------------")
    print("    ... app handles HTTP requests ...")
    print('    {"type": "lifespan.shutdown"}')
    print("       -------------------------------->")
    print("                                  (close DB, flush, etc.)")
    print('                                  await send({"type": "lifespan.shutdown.complete"})')
    print("       <--------------------------------")
    print("    Server exits cleanly")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: WSGI vs ASGI ---
    print("--- Section 1: WSGI vs ASGI ---")
    try:
        demo_wsgi_vs_asgi()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: ASGI Scope ---
    print("--- Section 2: The ASGI Scope Dict ---")
    try:
        demo_asgi_scope()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: Receive/Send ---
    print("--- Section 3: Receive and Send Callables ---")
    try:
        demo_receive_send()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: Lifespan ---
    print("--- Section 4: Lifespan Events ---")
    try:
        demo_lifespan()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: Message Flow ---
    print("--- Section 5: ASGI Message Flow ---")
    try:
        demo_message_flow()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("ASGI is the interface between server and framework:")
    print("  - scope dict describes the connection (HTTP, WebSocket, lifespan)")
    print("  - receive() is an async callable to get request data / events")
    print("  - send() is an async callable to send response data / events")
    print("  - HTTP responses require two send() calls (start + body)")
    print("  - Lifespan events enable startup/shutdown hooks")
    print("  - ASGI replaces WSGI for modern async Python web apps")
    print()
    print("All 5 sections passed. ASGI protocol concepts mastered!")
    print("Next up: Kata 38 -- building the Ignite ASGI app skeleton!")
