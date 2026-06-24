# Kata 40 -- Response Object

[prev: 39-request-object](./39-request-object.md) | [next: 41-router](./41-router.md)

---

## What We're Building

Ignite **response classes** that encapsulate the ASGI send protocol. Instead of manually constructing and sending ASGI messages, handlers will return clean response objects: `Response`, `JSONResponse`, `HTMLResponse`, `PlainTextResponse`, `RedirectResponse`, and `StreamingResponse`.

We'll build six response types:
1. **Response** -- base class handling status, headers, and body encoding
2. **JSONResponse** -- auto-serializes Python dicts/lists to JSON
3. **HTMLResponse** -- serves HTML with the correct Content-Type
4. **PlainTextResponse** -- serves plain text content
5. **RedirectResponse** -- sends 3xx redirects with Location header
6. **StreamingResponse** -- sends body in chunks for large payloads

This is the "output" half of the request/response cycle that pairs with the Request object from Kata 39.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| ASGI send protocol | Two-step: `http.response.start` then `http.response.body` | Every HTTP response |
| `__call__` as ASGI | Making response objects callable as ASGI apps | Framework integration |
| Content-Type headers | Tell the client what format the body is in | JSON, HTML, text responses |
| Content-Length | Tell the client how many bytes to expect | Non-streaming responses |
| Location header | Tell the client where to redirect | 301, 302, 307 redirects |
| Streaming | Send body in multiple chunks without buffering | Large files, SSE |
| Class inheritance | Specialized responses inherit from base Response | DRY code organization |

## The Code

### 1. The ASGI Send Protocol

Sending an HTTP response in ASGI requires exactly two messages:

```python
# Message 1: Start the response (status + headers)
await send({
    "type": "http.response.start",
    "status": 200,
    "headers": [
        (b"content-type", b"application/json"),
        (b"content-length", b"27"),
    ],
})

# Message 2: Send the body
await send({
    "type": "http.response.body",
    "body": b'{"message": "Hello world!"}',
})
```

Our Response class encapsulates this into a single callable object.

### 2. Base Response Class

```python
class Response:
    media_type: str | None = None
    charset: str = "utf-8"

    def __init__(self, content="", status_code=200,
                 headers=None, media_type=None):
        self.status_code = status_code
        self.media_type = media_type or self.media_type

        # Convert str to bytes
        if isinstance(content, str):
            self.body = content.encode(self.charset)
        else:
            self.body = content

        self.raw_headers = self._build_headers(headers or {})

    async def __call__(self, scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": self.raw_headers,
        })
        await send({
            "type": "http.response.body",
            "body": self.body,
        })
```

The `__call__` method makes every Response an ASGI application. The framework can call `await response(scope, receive, send)` to transmit it.

### 3. JSONResponse

```python
class JSONResponse(Response):
    media_type = "application/json"

    def __init__(self, content=None, status_code=200, headers=None):
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        super().__init__(content=body, status_code=status_code,
                         headers=headers, media_type=self.media_type)
```

Subclassing is elegant here: `JSONResponse` only needs to serialize the content and set the right media type. Everything else (headers, ASGI send) is inherited.

### 4. RedirectResponse

```python
class RedirectResponse(Response):
    def __init__(self, url, status_code=307, headers=None):
        redirect_headers = dict(headers) if headers else {}
        redirect_headers["location"] = url
        super().__init__(content=b"", status_code=status_code,
                         headers=redirect_headers)
```

Redirects have an empty body and a `Location` header. The browser follows the redirect automatically.

### 5. StreamingResponse

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
class StreamingResponse:
    def __init__(self, content_iterator, status_code=200,
                 headers=None, media_type="application/octet-stream"):
        self.content_iterator = content_iterator
        # ... setup headers (no Content-Length!) ...

    async def __call__(self, scope, receive, send):
        await send({"type": "http.response.start", ...})

        async for chunk in self.content_iterator:
            await send({"type": "http.response.body",
                        "body": chunk, "more_body": True})

        await send({"type": "http.response.body",
                    "body": b"", "more_body": False})
```

Streaming sends multiple body messages with `more_body: True`, then a final empty chunk with `more_body: False` to signal completion. Note: no Content-Length header since we don't know the total size upfront.

## Playground

```bash
python playground/40_response_object.py
```

Expected output:

```
--- Section 1: Base Response ---
  status: 200
  headers: {'content-type': 'text/plain; charset=utf-8', 'content-length': '14', 'x-custom': 'test-value'}
  body: b'Hello, Ignite!'
  [PASS] Base Response works correctly

--- Section 2: JSONResponse ---
  status: 200
  content-type: application/json
  body: {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
  [PASS] JSONResponse works correctly

--- Section 3: HTMLResponse ---
  status: 200
  content-type: text/html; charset=utf-8
  body length: 52 bytes
  [PASS] HTMLResponse works correctly

--- Section 4: PlainTextResponse ---
  status: 200
  content-type: text/plain; charset=utf-8
  [PASS] PlainTextResponse works correctly

--- Section 5: RedirectResponse ---
  status: 301
  location: /new-location
  body: b'' (empty for redirects)
  [PASS] RedirectResponse works correctly

--- Section 6: StreamingResponse ---
  status: 200
  body messages: 4
  full body: b'chunk-0\nchunk-1\nchunk-2\n'
  [PASS] StreamingResponse works correctly

--- Summary ---
Response objects encapsulate the ASGI send protocol:
  - Response: base class with status, headers, body
  - JSONResponse: auto-serializes dicts/lists to JSON
  - HTMLResponse: serves HTML with correct Content-Type
  - PlainTextResponse: serves plain text
  - RedirectResponse: sets Location header for redirects
  - StreamingResponse: sends body in chunks

All 6 sections passed. Response objects mastered!
Next up: Kata 41 -- Router
```

## How It Works

### The Response Class Hierarchy

```
Response (base)
  |
  +-- JSONResponse        media_type = "application/json"
  |                       Serializes Python objects to JSON
  |
  +-- HTMLResponse        media_type = "text/html"
  |                       Serves HTML content
  |
  +-- PlainTextResponse   media_type = "text/plain"
  |                       Serves plain text
  |
  +-- RedirectResponse    Sets Location header
                          Empty body, 3xx status

StreamingResponse (separate -- different send pattern)
  Sends body in chunks via async iteration
```

### ASGI Message Flow

```
Response.__call__(scope, receive, send)
        |
        v
send({"type": "http.response.start",   <-- Headers go to client
      "status": 200,
      "headers": [...]})
        |
        v
send({"type": "http.response.body",    <-- Body goes to client
      "body": b"..."})
```

For streaming:

```
StreamingResponse.__call__(scope, receive, send)
        |
        v
send(http.response.start)
        |
        v
send(body chunk 1, more_body=True)  --->  client receives partial data
send(body chunk 2, more_body=True)  --->  client receives more data
send(body chunk 3, more_body=True)  --->  client receives more data
send(empty body, more_body=False)   --->  client knows response is complete
```

### Header Building

```python
# Input:
media_type = "text/html"
charset = "utf-8"
extra_headers = {"X-Request-Id": "abc123"}

# Auto-generated headers:
{
    "content-type": "text/html; charset=utf-8",  # from media_type
    "content-length": "52",                       # from body length
    "x-request-id": "abc123",                     # from extra_headers
}

# ASGI format (list of byte tuples):
[
    (b"content-type", b"text/html; charset=utf-8"),
    (b"content-length", b"52"),
    (b"x-request-id", b"abc123"),
]
```

## Exercises

1. **Add `set_cookie()` method** to the base Response that appends a `Set-Cookie` header. Handle name, value, max_age, path, and httponly parameters.

2. **Build a `FileResponse`** class that reads a file from disk and serves it with the correct Content-Type based on the file extension (use `mimetypes.guess_type`).

3. **Add `delete_cookie()` method** that sets a cookie with `max_age=0` to instruct the browser to delete it.

4. **Implement `ServerSentEventResponse`** -- a streaming response that formats chunks as SSE events: `data: {json}\n\n`. This is how real-time updates work without WebSockets.

5. **Add ETag support** -- compute an MD5 hash of the response body and add it as an `ETag` header. Return 304 Not Modified if the request's `If-None-Match` header matches.

## What's Next

We have Request (input) and Response (output). In [Kata 41: Router](./41-router.md), we build the **Router** -- the component that maps incoming requests to the right handler based on HTTP method and path, with proper 404 and 405 error handling.

---

[prev: 39-request-object](./39-request-object.md) | [next: 41-router](./41-router.md)
