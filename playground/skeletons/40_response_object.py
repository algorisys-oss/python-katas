"""
Kata 40 -- Response Object
Run: python playground/skeletons/40_response_object.py

Build Ignite response classes: Response, JSONResponse, HTMLResponse,
and RedirectResponse. Each implements the ASGI __call__ protocol to
send HTTP responses back to the client.

Completes within 5 seconds.
"""

import asyncio
import json


# ===========================================================================
# SECTION 1: Base Response Class
# ===========================================================================

class Response:
    """Base ASGI response that sends a body with status and headers.

    In ASGI, sending a response means calling the 'send' callable twice:
    1. First with an 'http.response.start' message (status + headers)
    2. Then with an 'http.response.body' message (the actual content)
    """

    media_type: str | None = None
    charset: str = "utf-8"

    def __init__(
        self,
        content: str | bytes = b"",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
    ):
        self.status_code = status_code
        self.media_type = media_type or self.media_type

        # TODO: Convert str content to bytes using self.charset
        # HINT: self.body = content.encode(self.charset) if isinstance(content, str) else content
        self.body = b""

        self.raw_headers = self._build_headers(headers or {})

    def _build_headers(self, extra_headers: dict[str, str]) -> list[tuple[bytes, bytes]]:
        """Build ASGI-format headers (list of byte pairs).

        Automatically adds Content-Type and Content-Length if not
        already specified in extra_headers.
        """
        headers = {}

        # TODO: Add Content-Type header if self.media_type is set
        # HINT: If media_type contains "text", append "; charset={self.charset}"
        # HINT: headers["content-type"] = ct

        # TODO: Add Content-Length header based on len(self.body)
        # HINT: headers["content-length"] = str(len(self.body))

        # TODO: Merge extra_headers (user-provided override defaults)
        # HINT: for key, value in extra_headers.items():
        #           headers[key.lower()] = value

        # TODO: Convert to ASGI format: list of (bytes, bytes) tuples
        # HINT: return [(k.encode(), v.encode()) for k, v in headers.items()]
        return []

    async def __call__(self, scope: dict, receive: callable, send: callable) -> None:
        """ASGI interface: send the response.

        This makes Response objects callable as ASGI apps.
        """
        # TODO: Send http.response.start message with status_code and headers
        # HINT: await send({"type": "http.response.start",
        #                   "status": self.status_code,
        #                   "headers": self.raw_headers})

        # TODO: Send http.response.body message with self.body
        # HINT: await send({"type": "http.response.body", "body": self.body})
        pass


# ===========================================================================
# SECTION 2: JSONResponse
# ===========================================================================

class JSONResponse(Response):
    """Response that serializes content as JSON.

    Automatically sets Content-Type to application/json.
    """

    media_type = "application/json"

    def __init__(
        self,
        content: dict | list | str | int | float | bool | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        # TODO: Serialize content to JSON bytes
        # HINT: body = json.dumps(content, ensure_ascii=False).encode("utf-8")

        # TODO: Call super().__init__ with the serialized body
        # HINT: super().__init__(content=body, status_code=status_code,
        #                        headers=headers, media_type=self.media_type)
        pass


# ===========================================================================
# SECTION 3: HTMLResponse
# ===========================================================================

class HTMLResponse(Response):
    """Response that serves HTML content.

    Sets Content-Type to text/html; charset=utf-8.
    """

    media_type = "text/html"

    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        # TODO: Call super().__init__ with the HTML content
        # HINT: super().__init__(content=content, status_code=status_code,
        #                        headers=headers, media_type=self.media_type)
        pass


# ===========================================================================
# SECTION 4: PlainTextResponse
# ===========================================================================

class PlainTextResponse(Response):
    """Response that serves plain text content."""

    media_type = "text/plain"

    def __init__(
        self,
        content: str = "",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        # TODO: Call super().__init__ with the text content
        pass


# ===========================================================================
# SECTION 5: RedirectResponse
# ===========================================================================

class RedirectResponse(Response):
    """Response that redirects the client to a different URL.

    Sets the Location header and uses a 3xx status code.
    Common codes: 301 (permanent), 302 (found), 307 (temporary).
    """

    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: dict[str, str] | None = None,
    ):
        # TODO: Create headers dict with "location" set to url
        # TODO: Call super().__init__ with empty body and redirect status
        # HINT: redirect_headers = dict(headers) if headers else {}
        #       redirect_headers["location"] = url
        #       super().__init__(content=b"", status_code=status_code,
        #                        headers=redirect_headers)
        pass


# ===========================================================================
# SECTION 6: Streaming Response
# ===========================================================================

class StreamingResponse:
    """Response that streams content in chunks.

    Useful for large files or server-sent events.
    """

    def __init__(
        self,
        content_iterator,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/octet-stream",
    ):
        self.content_iterator = content_iterator
        self.status_code = status_code
        self.media_type = media_type

        # Build headers (no Content-Length since we're streaming)
        raw_headers = {"content-type": media_type}
        if headers:
            for k, v in headers.items():
                raw_headers[k.lower()] = v
        self.raw_headers = [(k.encode(), v.encode()) for k, v in raw_headers.items()]

    async def __call__(self, scope: dict, receive: callable, send: callable) -> None:
        """Send the response as a stream of chunks."""
        # TODO: Send http.response.start (status + headers)
        # HINT: await send({"type": "http.response.start", ...})

        # TODO: Iterate over self.content_iterator with async for
        # TODO: For each chunk, encode str to bytes if needed
        # TODO: Send each chunk with more_body=True
        # HINT: async for chunk in self.content_iterator:
        #           if isinstance(chunk, str): chunk = chunk.encode("utf-8")
        #           await send({"type": "http.response.body",
        #                       "body": chunk, "more_body": True})

        # TODO: Send empty final chunk with more_body=False
        # HINT: await send({"type": "http.response.body",
        #                   "body": b"", "more_body": False})
        pass


# ===========================================================================
# SECTION 7: Test Helpers
# ===========================================================================

class MessageCollector:
    """Captures ASGI messages sent via the send callable."""

    def __init__(self):
        self.messages: list[dict] = []

    async def send(self, message: dict) -> None:
        self.messages.append(message)

    @property
    def start_message(self) -> dict | None:
        for msg in self.messages:
            if msg["type"] == "http.response.start":
                return msg
        return None

    @property
    def body_messages(self) -> list[dict]:
        return [m for m in self.messages if m["type"] == "http.response.body"]

    @property
    def status_code(self) -> int:
        start = self.start_message
        return start["status"] if start else 0

    @property
    def headers(self) -> dict[str, str]:
        start = self.start_message
        if not start:
            return {}
        return {k.decode(): v.decode() for k, v in start.get("headers", [])}

    @property
    def full_body(self) -> bytes:
        return b"".join(m.get("body", b"") for m in self.body_messages)


# ===========================================================================
# SECTION 8: Demonstrations
# ===========================================================================

async def demo_base_response():
    """Demonstrate the base Response class."""
    resp = Response(
        content="Hello, Ignite!",
        status_code=200,
        headers={"X-Custom": "test-value"},
        media_type="text/plain",
    )

    collector = MessageCollector()
    await resp({}, None, collector.send)

    print(f"  status: {collector.status_code}")
    print(f"  headers: {collector.headers}")
    print(f"  body: {collector.full_body}")

    assert collector.status_code == 200
    assert collector.full_body == b"Hello, Ignite!"
    assert collector.headers["content-type"] == "text/plain; charset=utf-8"
    assert collector.headers["content-length"] == "14"
    assert collector.headers["x-custom"] == "test-value"
    assert len(collector.messages) == 2

    print("  [PASS] Base Response works correctly")


async def demo_json_response():
    """Demonstrate JSONResponse."""
    data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
    resp = JSONResponse(content=data, status_code=200)

    collector = MessageCollector()
    await resp({}, None, collector.send)

    body_str = collector.full_body.decode()
    parsed = json.loads(body_str)

    print(f"  status: {collector.status_code}")
    print(f"  content-type: {collector.headers['content-type']}")
    print(f"  body: {body_str}")

    assert collector.status_code == 200
    assert collector.headers["content-type"] == "application/json"
    assert parsed == data

    error_resp = JSONResponse(
        content={"error": "Not found"},
        status_code=404,
    )
    error_collector = MessageCollector()
    await error_resp({}, None, error_collector.send)
    assert error_collector.status_code == 404

    print("  [PASS] JSONResponse works correctly")


async def demo_html_response():
    """Demonstrate HTMLResponse."""
    html = "<html><body><h1>Welcome to Ignite</h1></body></html>"
    resp = HTMLResponse(content=html, status_code=200)

    collector = MessageCollector()
    await resp({}, None, collector.send)

    print(f"  status: {collector.status_code}")
    print(f"  content-type: {collector.headers['content-type']}")
    print(f"  body length: {len(collector.full_body)} bytes")

    assert collector.status_code == 200
    assert "text/html" in collector.headers["content-type"]
    assert collector.full_body == html.encode()

    print("  [PASS] HTMLResponse works correctly")


async def demo_plain_text_response():
    """Demonstrate PlainTextResponse."""
    resp = PlainTextResponse("Just plain text.", status_code=200)

    collector = MessageCollector()
    await resp({}, None, collector.send)

    assert collector.status_code == 200
    assert "text/plain" in collector.headers["content-type"]
    assert collector.full_body == b"Just plain text."

    print(f"  status: {collector.status_code}")
    print(f"  content-type: {collector.headers['content-type']}")
    print("  [PASS] PlainTextResponse works correctly")


async def demo_redirect_response():
    """Demonstrate RedirectResponse."""
    resp = RedirectResponse(url="/new-location", status_code=301)

    collector = MessageCollector()
    await resp({}, None, collector.send)

    print(f"  status: {collector.status_code}")
    print(f"  location: {collector.headers['location']}")
    print(f"  body: {collector.full_body!r} (empty for redirects)")

    assert collector.status_code == 301
    assert collector.headers["location"] == "/new-location"
    assert collector.full_body == b""

    temp = RedirectResponse(url="https://example.com/login")
    temp_collector = MessageCollector()
    await temp({}, None, temp_collector.send)
    assert temp_collector.status_code == 307
    assert temp_collector.headers["location"] == "https://example.com/login"

    print("  [PASS] RedirectResponse works correctly")


async def demo_streaming_response():
    """Demonstrate StreamingResponse."""

    async def generate_chunks():
        for i in range(3):
            yield f"chunk-{i}\n"

    resp = StreamingResponse(
        content_iterator=generate_chunks(),
        status_code=200,
        media_type="text/plain",
    )

    collector = MessageCollector()
    await resp({}, None, collector.send)

    print(f"  status: {collector.status_code}")
    print(f"  body messages: {len(collector.body_messages)}")
    print(f"  full body: {collector.full_body!r}")

    assert collector.status_code == 200
    assert len(collector.body_messages) == 4
    assert collector.full_body == b"chunk-0\nchunk-1\nchunk-2\n"

    last = collector.body_messages[-1]
    assert last["body"] == b""
    assert last["more_body"] is False

    print("  [PASS] StreamingResponse works correctly")


# ===========================================================================
# MAIN
# ===========================================================================

async def main():
    print("--- Section 1: Base Response ---")
    try:
        await demo_base_response()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 2: JSONResponse ---")
    try:
        await demo_json_response()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 3: HTMLResponse ---")
    try:
        await demo_html_response()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 4: PlainTextResponse ---")
    try:
        await demo_plain_text_response()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 5: RedirectResponse ---")
    try:
        await demo_redirect_response()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Section 6: StreamingResponse ---")
    try:
        await demo_streaming_response()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    print("--- Summary ---")
    print("Response objects encapsulate the ASGI send protocol:")
    print("  - Response: base class with status, headers, body")
    print("  - JSONResponse: auto-serializes dicts/lists to JSON")
    print("  - HTMLResponse: serves HTML with correct Content-Type")
    print("  - PlainTextResponse: serves plain text")
    print("  - RedirectResponse: sets Location header for redirects")
    print("  - StreamingResponse: sends body in chunks")
    print()
    print("All 6 sections passed. Response objects mastered!")
    print("Next up: Kata 41 -- Router")


if __name__ == "__main__":
    asyncio.run(main())
