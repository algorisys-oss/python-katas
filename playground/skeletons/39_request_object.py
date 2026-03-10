"""
Kata 39 -- Request Object
Run: python playground/skeletons/39_request_object.py

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
        """HTTP method (GET, POST, PUT, DELETE, etc.).

        Read from the ASGI scope's 'method' key.
        """
        # TODO: Return the HTTP method from self._scope
        # HINT: self._scope.get("method", "GET")
        pass

    @property
    def path(self) -> str:
        """Request path, e.g. '/users/42'.

        Read from the ASGI scope's 'path' key.
        """
        # TODO: Return the path from self._scope
        # HINT: self._scope.get("path", "/")
        pass

    @property
    def query_string(self) -> str:
        """Raw query string (bytes in ASGI, we decode it).

        The ASGI scope stores query_string as bytes. We decode to str.
        """
        # TODO: Get 'query_string' from scope (default b""), decode if bytes
        # HINT: raw = self._scope.get("query_string", b"")
        #       return raw.decode("utf-8") if isinstance(raw, bytes) else raw
        pass

    # -- Headers -----------------------------------------------------------

    @property
    def headers(self) -> dict[str, str]:
        """Parse ASGI headers into a dict with lowercase keys.

        ASGI headers arrive as a list of [name, value] byte pairs:
            [(b'content-type', b'application/json'), ...]

        Decode them into a regular dict. Duplicate keys: last value wins.
        """
        raw_headers = self._scope.get("headers", [])
        result = {}
        # TODO: Iterate over raw_headers, decode each (name, value) pair
        # TODO: Store in result dict with lowercase key
        # HINT: for name, value in raw_headers:
        #           key = name.decode("utf-8") if isinstance(name, bytes) else name
        #           val = value.decode("utf-8") if isinstance(value, bytes) else value
        #           result[key.lower()] = val
        return result

    # -- Query parameters --------------------------------------------------

    @property
    def query_params(self) -> dict[str, list[str]]:
        """Parse query string into a dict of lists.

        Example: '?color=red&size=lg&color=blue'
        Returns: {'color': ['red', 'blue'], 'size': ['lg']}
        """
        # TODO: Use parse_qs() from urllib.parse to parse self.query_string
        # HINT: return parse_qs(self.query_string)
        pass

    def get_query_param(self, key: str, default: str | None = None) -> str | None:
        """Get a single query parameter value (first occurrence).

        Convenience method when you expect only one value per key.
        """
        # TODO: Look up key in self.query_params, return first value or default
        # HINT: values = self.query_params.get(key)
        #       return values[0] if values else default
        pass

    # -- Body reading ------------------------------------------------------

    async def body(self) -> bytes:
        """Read the full request body.

        ASGI delivers the body in chunks via the receive callable.
        Each chunk is an 'http.request' message with a 'body' key
        and a 'more_body' flag. Accumulate chunks until done.

        Cache the result so multiple calls return the same bytes.
        """
        # TODO: Return cached body if self._body is not None
        # HINT: if self._body is not None: return self._body

        # TODO: Accumulate body chunks in a loop:
        #   1. Call await self._receive() to get a message
        #   2. Append message.get("body", b"") to a chunks list
        #   3. Break when message.get("more_body", False) is False
        # HINT: while True:
        #           message = await self._receive()
        #           chunks.append(message.get("body", b""))
        #           if not message.get("more_body", False): break

        # TODO: Join chunks with b"".join(chunks), cache in self._body, return
        pass

    async def json(self) -> dict:
        """Read the body and parse it as JSON."""
        # TODO: Read body with await self.body(), parse with json.loads()
        pass

    async def text(self) -> str:
        """Read the body and decode it as UTF-8 text."""
        # TODO: Read body with await self.body(), decode with .decode("utf-8")
        pass

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

    Returns an async function that yields the body in a single chunk.
    """
    sent = False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return receive


def make_chunked_receive(chunks: list[bytes]) -> callable:
    """Create a mock receive that delivers the body in multiple chunks."""
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

    assert req.get_query_param("q") == "python async"
    assert req.get_query_param("page") == "2"
    assert req.query_params["tag"] == ["web", "api"]
    assert req.get_query_param("missing") is None
    assert req.get_query_param("missing", "default") == "default"

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

    raw = await req.body()
    print(f"  raw body: {raw}")

    raw2 = await req.body()
    assert raw is raw2, "Body should be cached"
    print("  body caching: works (same object returned)")

    data = await req.json()
    print(f"  parsed JSON: {data}")
    assert data == payload

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
    try:
        await demo_basic_properties()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 2: Query Parameters ---")
    try:
        await demo_query_params()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 3: Body Reading ---")
    try:
        await demo_body_reading()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 4: Chunked Body ---")
    try:
        await demo_chunked_body()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 5: Scope Access ---")
    try:
        await demo_scope_access()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
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
