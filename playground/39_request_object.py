"""
Kata 39 -- Request Object
Run: python playground/39_request_object.py

Build an Ignite Request class that wraps the ASGI scope and receive
callable, providing clean access to method, path, headers, query
parameters, and async body parsing.

Completes within 5 seconds.
"""

import asyncio
import json
from urllib.parse import parse_qs, unquote


# ===========================================================================
# SECTION 1: The Request Class
# ===========================================================================

class Request:
    """Wraps an ASGI scope and receive callable into a clean interface.

    ASGI passes raw dicts and callables around. The Request class turns
    that into a developer-friendly object with properties like .method,
    .path, .headers, and .query_params, plus an async .body() method
    for reading the request body.
    """

    def __init__(self, scope: dict, receive: callable):
        """Initialize a Request from an ASGI scope and receive callable.

        Args:
            scope: ASGI connection scope dict with keys like 'type',
                   'method', 'path', 'query_string', 'headers'.
            receive: Async callable that yields ASGI messages (used
                     to read the request body).
        """
        self._scope = scope
        self._receive = receive
        self._body: bytes | None = None  # Cache the body after first read

    # -- Basic properties --------------------------------------------------

    @property
    def method(self) -> str:
        """HTTP method (GET, POST, PUT, DELETE, etc.)."""
        return self._scope.get("method", "GET")

    @property
    def path(self) -> str:
        """Request path, e.g. '/users/42'."""
        return self._scope.get("path", "/")

    @property
    def query_string(self) -> str:
        """Raw query string (bytes in ASGI, we decode it)."""
        raw = self._scope.get("query_string", b"")
        if isinstance(raw, bytes):
            return raw.decode("utf-8")
        return raw

    # -- Headers -----------------------------------------------------------

    @property
    def headers(self) -> dict[str, str]:
        """Parse ASGI headers into a case-insensitive-ish dict.

        ASGI headers arrive as a list of [name, value] byte pairs:
            [(b'content-type', b'application/json'), ...]

        We decode them into a regular dict with lowercase keys.
        Duplicate header names: last value wins (simple approach).
        """
        raw_headers = self._scope.get("headers", [])
        result = {}
        for name, value in raw_headers:
            # ASGI headers are bytes -- decode to str
            key = name.decode("utf-8") if isinstance(name, bytes) else name
            val = value.decode("utf-8") if isinstance(value, bytes) else value
            result[key.lower()] = val
        return result

    # -- Query parameters --------------------------------------------------

    @property
    def query_params(self) -> dict[str, list[str]]:
        """Parse query string into a dict of lists.

        Example: '?color=red&size=lg&color=blue'
        Returns: {'color': ['red', 'blue'], 'size': ['lg']}

        Uses urllib.parse.parse_qs which handles URL-decoding and
        multiple values for the same key.
        """
        return parse_qs(self.query_string)

    def get_query_param(self, key: str, default: str | None = None) -> str | None:
        """Get a single query parameter value (first occurrence).

        Convenience method when you expect only one value per key.
        """
        values = self.query_params.get(key)
        if values:
            return values[0]
        return default

    # -- Body reading ------------------------------------------------------

    async def body(self) -> bytes:
        """Read the full request body.

        ASGI delivers the body in chunks via the receive callable.
        Each chunk is an 'http.request' message with a 'body' key
        and a 'more_body' flag. We accumulate chunks until done.

        The result is cached so multiple calls to body() return
        the same bytes without re-reading.
        """
        if self._body is not None:
            return self._body

        chunks = []
        while True:
            message = await self._receive()
            body_chunk = message.get("body", b"")
            if body_chunk:
                chunks.append(body_chunk)
            # 'more_body' defaults to False -- when absent or False, we're done
            if not message.get("more_body", False):
                break

        self._body = b"".join(chunks)
        return self._body

    async def json(self) -> dict:
        """Read the body and parse it as JSON.

        Convenience method for JSON APIs.
        """
        raw = await self.body()
        return json.loads(raw)

    async def text(self) -> str:
        """Read the body and decode it as UTF-8 text."""
        raw = await self.body()
        return raw.decode("utf-8")

    # -- Scope access ------------------------------------------------------

    @property
    def scope(self) -> dict:
        """Direct access to the raw ASGI scope (escape hatch)."""
        return self._scope

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"


# ===========================================================================
# SECTION 2: Mock ASGI helpers for testing
# ===========================================================================

def make_scope(
    method: str = "GET",
    path: str = "/",
    query_string: str = "",
    headers: dict[str, str] | None = None,
) -> dict:
    """Create a mock ASGI HTTP scope dict.

    In a real ASGI server (like uvicorn), this dict is built from
    the incoming HTTP request. We simulate it here for testing.
    """
    raw_headers = []
    if headers:
        for key, value in headers.items():
            raw_headers.append((key.lower().encode(), value.encode()))

    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "query_string": query_string.encode("utf-8"),
        "headers": raw_headers,
        "server": ("localhost", 8000),
    }


def make_receive(body: bytes = b"") -> callable:
    """Create a mock ASGI receive callable.

    Returns an async function that yields the body in a single chunk,
    simulating how an ASGI server delivers the request body.
    """
    sent = False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        # After the body is consumed, return disconnect
        return {"type": "http.disconnect"}

    return receive


def make_chunked_receive(chunks: list[bytes]) -> callable:
    """Create a mock receive that delivers the body in multiple chunks.

    This simulates large request bodies that arrive in pieces.
    """
    index = 0

    async def receive():
        nonlocal index
        if index < len(chunks):
            chunk = chunks[index]
            index += 1
            more = index < len(chunks)
            return {"type": "http.request", "body": chunk, "more_body": more}
        return {"type": "http.disconnect"}

    return receive


# ===========================================================================
# SECTION 3: Demonstrations
# ===========================================================================

async def demo_basic_properties():
    """Demonstrate basic Request properties: method, path, headers."""
    scope = make_scope(
        method="GET",
        path="/api/users",
        headers={
            "Host": "example.com",
            "Accept": "application/json",
            "Authorization": "Bearer token123",
        },
    )
    receive = make_receive()
    req = Request(scope, receive)

    print(f"  repr: {req!r}")
    print(f"  method: {req.method}")
    print(f"  path: {req.path}")
    print(f"  headers: {req.headers}")

    assert req.method == "GET"
    assert req.path == "/api/users"
    assert req.headers["host"] == "example.com"
    assert req.headers["accept"] == "application/json"
    assert req.headers["authorization"] == "Bearer token123"
    assert repr(req) == "<Request GET /api/users>"

    print("  [PASS] Basic properties work correctly")


async def demo_query_params():
    """Demonstrate query parameter parsing."""
    scope = make_scope(
        method="GET",
        path="/search",
        query_string="q=python+async&page=2&tag=web&tag=api",
    )
    receive = make_receive()
    req = Request(scope, receive)

    print(f"  query_string: {req.query_string!r}")
    print(f"  query_params: {req.query_params}")
    print(f"  get_query_param('q'): {req.get_query_param('q')!r}")
    print(f"  get_query_param('page'): {req.get_query_param('page')!r}")
    print(f"  get_query_param('missing', 'default'): "
          f"{req.get_query_param('missing', 'default')!r}")

    # Single-value params
    assert req.get_query_param("q") == "python async"
    assert req.get_query_param("page") == "2"

    # Multi-value param
    assert req.query_params["tag"] == ["web", "api"]

    # Missing param with default
    assert req.get_query_param("missing") is None
    assert req.get_query_param("missing", "default") == "default"

    # Empty query string
    empty_req = Request(make_scope(), make_receive())
    assert empty_req.query_params == {}
    assert empty_req.get_query_param("anything") is None

    print("  [PASS] Query parameters parsed correctly")


async def demo_body_reading():
    """Demonstrate reading the request body."""
    payload = {"username": "alice", "email": "alice@example.com"}
    body_bytes = json.dumps(payload).encode("utf-8")

    scope = make_scope(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(body_bytes)),
        },
    )
    receive = make_receive(body_bytes)
    req = Request(scope, receive)

    # Read body as bytes
    raw = await req.body()
    print(f"  raw body: {raw}")

    # Read again -- should use cached value
    raw2 = await req.body()
    assert raw is raw2, "Body should be cached"
    print("  body caching: works (same object returned)")

    # Parse as JSON
    data = await req.json()
    print(f"  parsed JSON: {data}")
    assert data == payload

    # Read as text
    text = await req.text()
    print(f"  as text: {text}")
    assert text == json.dumps(payload)

    print("  [PASS] Body reading and parsing work correctly")


async def demo_chunked_body():
    """Demonstrate reading a body delivered in multiple chunks."""
    chunks = [b"Hello, ", b"chunked ", b"world!"]
    scope = make_scope(method="POST", path="/upload")
    receive = make_chunked_receive(chunks)
    req = Request(scope, receive)

    body = await req.body()
    text = await req.text()

    print(f"  chunks received: {chunks}")
    print(f"  assembled body: {body}")
    print(f"  as text: {text!r}")

    assert body == b"Hello, chunked world!"
    assert text == "Hello, chunked world!"

    print("  [PASS] Chunked body reading works correctly")


async def demo_scope_access():
    """Demonstrate direct scope access (escape hatch)."""
    scope = make_scope(method="DELETE", path="/api/users/42")
    req = Request(scope, make_receive())

    print(f"  scope type: {req.scope['type']}")
    print(f"  ASGI version: {req.scope['asgi']['version']}")
    print(f"  HTTP version: {req.scope['http_version']}")
    print(f"  server: {req.scope['server']}")

    assert req.scope["type"] == "http"
    assert req.scope["asgi"]["version"] == "3.0"
    assert req.scope["http_version"] == "1.1"
    assert req.scope["server"] == ("localhost", 8000)

    print("  [PASS] Raw scope access works")


# ===========================================================================
# MAIN
# ===========================================================================

async def main():
    print("--- Section 1: Basic Properties ---")
    await demo_basic_properties()
    print()

    print("--- Section 2: Query Parameters ---")
    await demo_query_params()
    print()

    print("--- Section 3: Body Reading ---")
    await demo_body_reading()
    print()

    print("--- Section 4: Chunked Body ---")
    await demo_chunked_body()
    print()

    print("--- Section 5: Scope Access ---")
    await demo_scope_access()
    print()

    print("--- Summary ---")
    print("The Request object transforms raw ASGI into a clean API:")
    print("  - .method, .path for routing decisions")
    print("  - .headers dict for content negotiation, auth, etc.")
    print("  - .query_params for URL parameters")
    print("  - await .body() / .json() / .text() for request payloads")
    print("  - .scope for direct ASGI access when needed")
    print()
    print("All 5 sections passed. Request object mastered!")
    print("Next up: Kata 40 -- Response Object")


if __name__ == "__main__":
    asyncio.run(main())
