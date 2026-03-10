# Kata 39 -- Request Object

[prev: 38-asgi-app-skeleton](./38-asgi-app-skeleton.md) | [next: 40-response-object](./40-response-object.md)

---

## What We're Building

An Ignite **Request** class that wraps the raw ASGI scope and receive callable into a clean, developer-friendly interface. Instead of digging through dicts of byte tuples, handlers will access `request.method`, `request.path`, `request.headers`, `request.query_params`, and `await request.body()`.

We'll build five capabilities:
1. **Basic properties** -- method, path extracted from the ASGI scope
2. **Header parsing** -- ASGI byte-pair headers decoded into a dict
3. **Query parameter parsing** -- URL query strings parsed into multi-value dicts
4. **Body reading** -- async body consumption with chunked support and caching
5. **Scope access** -- escape hatch to the raw ASGI scope when needed

This is the "input" half of the request/response cycle. Every framework (Flask, Django, FastAPI) has a Request object -- now we build our own.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| ASGI scope | Dict describing the incoming connection (method, path, headers) | Every ASGI request |
| ASGI receive | Async callable that yields request body chunks | Reading POST/PUT bodies |
| Header decoding | Convert `[(b'name', b'value'), ...]` to `{'name': 'value'}` | Content negotiation, auth |
| `parse_qs()` | Parse URL query strings into multi-value dicts | `?key=val&key=val2` |
| Body caching | Read body once, return cached bytes on subsequent calls | Avoiding double-reads |
| `async/await` | Asynchronous body reading | Non-blocking I/O |

## The Code

### 1. The ASGI Scope

Every ASGI HTTP request arrives as a **scope dict** -- a plain Python dict describing the connection:

```python
# What an ASGI server (uvicorn) passes to your app:
scope = {
    "type": "http",
    "asgi": {"version": "3.0"},
    "http_version": "1.1",
    "method": "GET",
    "path": "/api/users",
    "query_string": b"page=2&sort=name",
    "headers": [
        (b"host", b"example.com"),
        (b"accept", b"application/json"),
    ],
    "server": ("localhost", 8000),
}
```

Notice: headers are byte tuples, query_string is bytes. Our Request class will clean this up.

### 2. Wrapping the Scope

```python
class Request:
    def __init__(self, scope: dict, receive: callable):
        self._scope = scope
        self._receive = receive
        self._body: bytes | None = None  # Cache after first read

    @property
    def method(self) -> str:
        return self._scope.get("method", "GET")

    @property
    def path(self) -> str:
        return self._scope.get("path", "/")
```

Properties give us clean attribute-style access (`request.method`) while reading from the raw scope under the hood.

### 3. Header Parsing

```python
@property
def headers(self) -> dict[str, str]:
    raw_headers = self._scope.get("headers", [])
    result = {}
    for name, value in raw_headers:
        key = name.decode("utf-8") if isinstance(name, bytes) else name
        val = value.decode("utf-8") if isinstance(value, bytes) else value
        result[key.lower()] = val
    return result
```

ASGI headers are byte pairs. We decode them to strings and lowercase the keys for consistent lookups (HTTP headers are case-insensitive per RFC 7230).

### 4. Query Parameters

```python
from urllib.parse import parse_qs

@property
def query_params(self) -> dict[str, list[str]]:
    return parse_qs(self.query_string)

def get_query_param(self, key: str, default=None) -> str | None:
    values = self.query_params.get(key)
    return values[0] if values else default
```

`parse_qs` returns lists because a key can appear multiple times: `?tag=web&tag=api` produces `{'tag': ['web', 'api']}`. The convenience method `get_query_param()` returns just the first value.

### 5. Async Body Reading

```python
async def body(self) -> bytes:
    if self._body is not None:
        return self._body  # Return cached body

    chunks = []
    while True:
        message = await self._receive()
        chunks.append(message.get("body", b""))
        if not message.get("more_body", False):
            break

    self._body = b"".join(chunks)
    return self._body
```

The ASGI receive callable delivers the body in chunks. Each message has a `body` key (bytes) and a `more_body` flag. We accumulate chunks until `more_body` is `False`, then cache the result.

### 6. JSON and Text Convenience Methods

```python
async def json(self) -> dict:
    raw = await self.body()
    return json.loads(raw)

async def text(self) -> str:
    raw = await self.body()
    return raw.decode("utf-8")
```

These build on `body()` -- since body is cached, calling `json()` then `text()` doesn't re-read from the network.

## Playground

```bash
python playground/39_request_object.py
```

Expected output:

```
--- Section 1: Basic Properties ---
  repr: <Request GET /api/users>
  method: GET
  path: /api/users
  headers: {'host': 'example.com', 'accept': 'application/json', 'authorization': 'Bearer token123'}
  [PASS] Basic properties work correctly

--- Section 2: Query Parameters ---
  query_string: 'q=python+async&page=2&tag=web&tag=api'
  query_params: {'q': ['python async'], 'page': ['2'], 'tag': ['web', 'api']}
  get_query_param('q'): 'python async'
  get_query_param('page'): '2'
  get_query_param('missing', 'default'): 'default'
  [PASS] Query parameters parsed correctly

--- Section 3: Body Reading ---
  raw body: b'{"username": "alice", "email": "alice@example.com"}'
  body caching: works (same object returned)
  parsed JSON: {'username': 'alice', 'email': 'alice@example.com'}
  as text: {"username": "alice", "email": "alice@example.com"}
  [PASS] Body reading and parsing work correctly

--- Section 4: Chunked Body ---
  chunks received: [b'Hello, ', b'chunked ', b'world!']
  assembled body: b'Hello, chunked world!'
  as text: 'Hello, chunked world!'
  [PASS] Chunked body reading works correctly

--- Section 5: Scope Access ---
  scope type: http
  ASGI version: 3.0
  HTTP version: 1.1
  server: ('localhost', 8000)
  [PASS] Raw scope access works

--- Summary ---
The Request object transforms raw ASGI into a clean API:
  - .method, .path for routing decisions
  - .headers dict for content negotiation, auth, etc.
  - .query_params for URL parameters
  - await .body() / .json() / .text() for request payloads
  - .scope for direct ASGI access when needed

All 5 sections passed. Request object mastered!
Next up: Kata 40 -- Response Object
```

## How It Works

### The ASGI Request Flow

```
Client sends HTTP request
        |
        v
ASGI Server (uvicorn) parses it
        |
        v
Creates scope dict + receive callable
        |
        v
Calls your app(scope, receive, send)
        |
        v
Request(scope, receive) wraps them
        |
        v
Handler accesses request.method, .path, .headers,
  await request.body(), etc.
```

### Why Cache the Body?

The ASGI receive callable is a stream -- once you read it, it's gone. If two parts of your code both call `await request.body()`, the second call would get nothing without caching. Our `_body` cache ensures the body is read exactly once and returned consistently.

### Headers: Bytes to Dict

```
ASGI format:        [(b'content-type', b'application/json'),
                     (b'authorization', b'Bearer xyz')]
                            |
                     decode + lowercase
                            |
                            v
Request.headers:    {'content-type': 'application/json',
                     'authorization': 'Bearer xyz'}
```

### Query String: Raw to Parsed

```
URL:          /search?q=python+async&tag=web&tag=api
                            |
query_string:         "q=python+async&tag=web&tag=api"
                            |
                      parse_qs()
                            |
                            v
query_params:   {'q': ['python async'], 'tag': ['web', 'api']}
                            |
                 get_query_param('q')
                            |
                            v
                      'python async'
```

## Exercises

1. **Add a `content_type` property** that returns the Content-Type header value (or `None` if missing). Use it to auto-detect whether to parse as JSON, form data, or plain text.

2. **Implement `form()` method** -- parse the body as URL-encoded form data (`application/x-www-form-urlencoded`) using `parse_qs`. Only parse if the Content-Type header matches.

3. **Add cookie parsing** -- read the `Cookie` header, split on `; `, and parse each `name=value` pair into a dict. Example: `"session=abc123; theme=dark"` becomes `{'session': 'abc123', 'theme': 'dark'}`.

4. **Implement a `url` property** that reconstructs the full URL from the scope: `http://localhost:8000/path?query`.

5. **Add `client` property** that returns the client IP address and port from `scope.get("client")`, with a sensible default for when it's not provided.

## What's Next

We have the input side covered. In [Kata 40: Response Object](./40-response-object.md), we build the output side -- `Response`, `JSONResponse`, `HTMLResponse`, and `RedirectResponse` classes that implement the ASGI send protocol to deliver HTTP responses back to the client.

---

[prev: 38-asgi-app-skeleton](./38-asgi-app-skeleton.md) | [next: 40-response-object](./40-response-object.md)
