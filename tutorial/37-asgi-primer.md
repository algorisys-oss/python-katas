# Kata 37 -- ASGI Primer

[prev: 36-tcp-socket-server](./36-tcp-socket-server.md) | [next: 38-asgi-app-skeleton](./38-asgi-app-skeleton.md)

---

## What We're Building

A deep dive into the **ASGI (Asynchronous Server Gateway Interface)** protocol -- the standard that connects web servers to Python web frameworks. We'll build ASGI apps from scratch and simulate the full protocol.

We'll build five demonstrations:
1. **WSGI vs ASGI** -- compare the old synchronous interface with the new async one
2. **The scope dict** -- understand the connection descriptor that ASGI passes to your app
3. **Receive and send callables** -- implement the async message-passing pattern
4. **Lifespan events** -- handle startup/shutdown hooks for resource management
5. **Message flow visualization** -- trace the full lifecycle of an ASGI request

This kata is the bridge between raw TCP sockets (kata 36) and the Ignite framework (kata 38). Understanding ASGI at this level means you'll know exactly what your framework does and why.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| ASGI spec | Interface between server and app | Every modern async Python web framework |
| `scope` dict | Describes the connection (type, path, method, headers) | Passed to your app on every connection |
| `receive()` | Async callable to get request body/events | Reading request data, WebSocket messages |
| `send()` | Async callable to send response events | Sending HTTP responses, WebSocket frames |
| `scope["type"]` | Connection type: `"http"`, `"websocket"`, `"lifespan"` | Dispatching to the right handler |
| `http.response.start` | First response message (status + headers) | Beginning an HTTP response |
| `http.response.body` | Second response message (body bytes) | Completing an HTTP response |
| `lifespan.startup` | Server starting up | Connecting to databases, loading models |
| `lifespan.shutdown` | Server shutting down | Closing connections, flushing buffers |
| WSGI (comparison) | Older synchronous interface | Understanding what ASGI replaced |

## The Code

### 1. WSGI -- The Old Way

WSGI (PEP 3333) has served Python web development well, but it's fundamentally synchronous:

```python
def wsgi_app(environ, start_response):
    """Synchronous. One thread per request. No WebSockets."""
    status = "200 OK"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)
    return [b"Hello from WSGI!"]
```

### 2. ASGI -- The New Way

ASGI uses async/await and a message-passing pattern:

```python
async def asgi_app(scope, receive, send):
    """Async. Event-loop based. WebSocket support. Lifespan events."""
    if scope["type"] == "http":
        # Read request body
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        # Send response (always two messages)
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"Hello from ASGI!",
        })
```

### 3. The Scope Dict

The scope describes the incoming connection. Different types have different fields:

```python
# HTTP scope
http_scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.4"},
    "http_version": "1.1",
    "method": "GET",
    "path": "/api/users",
    "root_path": "",
    "scheme": "http",
    "query_string": b"page=1&limit=10",
    "headers": [
        (b"host", b"localhost:8000"),
        (b"content-type", b"application/json"),
    ],
    "server": ("127.0.0.1", 8000),
    "client": ("127.0.0.1", 54321),
}

# WebSocket scope
ws_scope = {
    "type": "websocket",
    "scheme": "ws",
    "path": "/ws/chat",
    # ... similar fields but no "method"
}

# Lifespan scope
lifespan_scope = {
    "type": "lifespan",
    "asgi": {"version": "3.0"},
}
```

### 4. Simulating ASGI

Since we can't run uvicorn in a 5-second subprocess, we simulate the ASGI server:

*Excerpt — core logic only (some details elided); not a standalone runnable snippet.*

```python
class AsgiSimulator:
    def __init__(self, request_body=b""):
        self.request_body = request_body
        self.sent_messages = []
        self._body_sent = False

    async def receive(self):
        if not self._body_sent:
            self._body_sent = True
            return {"type": "http.request", "body": self.request_body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(self, message):
        self.sent_messages.append(message)

# Usage:
sim = AsgiSimulator()
scope = {"type": "http", "method": "GET", "path": "/", ...}
await my_app(scope, sim.receive, sim.send)
assert sim.sent_messages[0]["status"] == 200
```

### 5. Lifespan Events

```python
async def app_with_lifespan(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                # Initialize DB, cache, etc.
                scope["state"]["db"] = "connected"
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                # Clean up
                scope["state"]["db"] = None
                await send({"type": "lifespan.shutdown.complete"})
                return

    elif scope["type"] == "http":
        # Handle HTTP request using initialized state
        ...
```

## Playground

```bash
python playground/37_asgi_primer.py
```

Expected output:

```
--- Section 1: WSGI vs ASGI ---
  WSGI response: status=200 OK, body=b'Hello from WSGI!'
  ASGI messages sent: 2
    1. http.response.start (status=200)
    2. http.response.body (body=b'Hello from ASGI!')

  WSGI vs ASGI comparison:
  +-----------------+-------------------+-------------------+
  | Feature         | WSGI              | ASGI              |
  +-----------------+-------------------+-------------------+
  | Async           | No (sync only)    | Yes (async/await) |
  | WebSockets      | No                | Yes               |
  | HTTP/2          | No                | Yes               |
  | Lifespan events | No                | Yes               |
  | Threading model | 1 thread/request  | Event loop        |
  | Interface       | (environ, start)  | (scope, rcv, snd) |
  +-----------------+-------------------+-------------------+
  [VALID] WSGI and ASGI comparison complete

--- Section 2: The ASGI Scope Dict ---
  HTTP scope:
    type: http
    method: POST
    path: /api/users
    ...
  WebSocket scope:
    type: websocket
    ...
  [VALID] ASGI scope dicts created correctly

--- Section 3: Receive and Send Callables ---
  GET / -> status=200, body=b'Welcome to ASGI!'
  POST /echo -> status=200, body=b'Ping!'
  GET /json -> status=200, data={'message': 'Hello', 'protocol': 'ASGI'}
  GET /missing -> status=404, body=b'Not Found'
  [VALID] ASGI receive/send pattern works correctly

--- Section 4: Lifespan Events ---
  Lifespan messages sent by app:
    lifespan.startup.complete
    lifespan.shutdown.complete
  ...
  [VALID] Lifespan events handled correctly

--- Section 5: ASGI Message Flow ---
  ASGI HTTP request/response message flow:
  ...visual diagram...

--- Summary ---
ASGI is the interface between server and framework:
  - scope dict describes the connection (HTTP, WebSocket, lifespan)
  - receive() is an async callable to get request data / events
  - send() is an async callable to send response data / events
  - HTTP responses require two send() calls (start + body)
  - Lifespan events enable startup/shutdown hooks
  - ASGI replaces WSGI for modern async Python web apps

All 5 sections passed. ASGI protocol concepts mastered!
Next up: Kata 38 -- building the Ignite ASGI app skeleton!
```

## How It Works

### The Three ASGI Arguments

```
scope (dict)              receive (async callable)      send (async callable)
==========                ======================        ====================
Describes the             Gets data FROM the            Sends data TO the
connection.               client/server.                client/server.
Immutable for the         Called multiple times          Called multiple times
lifetime of the           for streaming bodies.          for streaming responses.
connection.

For HTTP:                 Returns:                      Accepts:
  type, method, path,     {"type": "http.request",      {"type": "http.response.start",
  headers, query_string    "body": b"...",               "status": 200,
  server, client           "more_body": False}           "headers": [...]}
                                                        {"type": "http.response.body",
                                                         "body": b"..."}
```

### Why Two send() Calls?

HTTP responses have two parts: headers and body. ASGI separates them because:

1. **Streaming**: You can send headers immediately and stream the body in chunks
2. **Header finalization**: The server may need to add headers (like `Transfer-Encoding`)
3. **Early responses**: You can send a 100 Continue before the body

```
await send({"type": "http.response.start", ...})  # Headers go on the wire
await send({"type": "http.response.body", ...})    # Body goes on the wire
```

### ASGI Connection Types

```
scope["type"]     When                    Messages
=============     ====                    ========
"http"            Every HTTP request      receive: http.request
                                          send: http.response.start, http.response.body

"websocket"       WebSocket connection    receive: websocket.connect, websocket.receive
                                          send: websocket.accept, websocket.send

"lifespan"        Server start/stop       receive: lifespan.startup, lifespan.shutdown
                                          send: lifespan.startup.complete, etc.
```

## Exercises

1. **Chunked response** -- modify the ASGI app to send the response body in multiple chunks by calling `send({"type": "http.response.body", "body": chunk, "more_body": True})` for all but the last chunk.

2. **Header extraction** -- write a helper function `get_header(scope, name) -> str | None` that finds a header by name in the scope's headers list (remember: headers are lowercase bytes).

3. **WebSocket simulation** -- extend the `AsgiSimulator` to support WebSocket connections. Implement `websocket.connect`, `websocket.accept`, `websocket.receive`, and `websocket.send` messages.

4. **Middleware pattern** -- write an ASGI middleware that wraps another app and adds a `X-Request-Id` header to every response. The middleware itself should be an ASGI callable that delegates to the inner app.

5. **Error handling** -- write an ASGI app that catches exceptions from route handlers and returns a proper 500 Internal Server Error response with a JSON body containing the error message.

## What's Next

Now that we understand the ASGI protocol at the byte level, we're ready to build on top of it. In [Kata 38: ASGI App Skeleton](./38-asgi-app-skeleton.md), we create the **Ignite class** -- our framework's core ASGI callable. It will handle routing, lifespan events, and response serialization, providing the developer-friendly API that hides all the scope/receive/send machinery we just learned.

---

[prev: 36-tcp-socket-server](./36-tcp-socket-server.md) | [next: 38-asgi-app-skeleton](./38-asgi-app-skeleton.md)
