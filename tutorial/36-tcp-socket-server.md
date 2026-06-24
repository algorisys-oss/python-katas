# Kata 36 -- TCP Socket Server

[prev: 35-packaging](./35-packaging.md) | [next: 37-asgi-primer](./37-asgi-primer.md)

---

## What We're Building

A **raw TCP server that speaks HTTP** -- understanding that HTTP is just structured text sent over a TCP socket. We begin Module 5 (Building Ignite) by going all the way down to the metal.

We'll build three demonstrations:
1. **HTTP message parsing** -- parse request lines, headers, and bodies from raw bytes; build proper HTTP/1.1 response bytes
2. **Raw TCP server** -- a socket-based server that accepts connections, routes requests, and sends responses (started in a thread, tested with real TCP requests, then shut down)
3. **Understanding the layers** -- visualize the full stack from your application code down to the network

This kata bridges packaging (kata 35) and the ASGI protocol (kata 37). Before you can appreciate what ASGI abstracts away, you need to see what raw HTTP over TCP looks like.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `socket.socket()` | Creates a raw TCP socket | Building servers/clients from scratch |
| `AF_INET` / `SOCK_STREAM` | IPv4 + TCP (reliable, ordered byte stream) | Almost all HTTP communication |
| `bind()` / `listen()` / `accept()` | Server-side socket setup | Accepting incoming connections |
| `recv()` / `sendall()` | Read/write bytes on a connection | Transferring data over TCP |
| `SO_REUSEADDR` | Allow immediate port reuse after restart | Avoiding "Address already in use" errors |
| HTTP request format | `METHOD /path HTTP/1.1\r\nHeaders\r\n\r\nBody` | Understanding what frameworks parse |
| HTTP response format | `HTTP/1.1 STATUS TEXT\r\nHeaders\r\n\r\nBody` | Understanding what frameworks build |
| `\r\n` (CRLF) | HTTP line separator | HTTP protocol requires this, not just `\n` |
| `\r\n\r\n` | Header/body separator | Detecting where headers end and body begins |
| `NamedTuple` | Lightweight immutable data class | Clean structured data without boilerplate |

## The Code

### 1. HTTP Request Parsing

HTTP is just text with a specific format. Every web framework parses this under the hood.

```python
from typing import NamedTuple

class HttpRequest(NamedTuple):
    method: str      # GET, POST, PUT, DELETE, etc.
    path: str        # /hello?name=world
    version: str     # HTTP/1.1
    headers: dict[str, str]
    body: str

def parse_http_request(raw: bytes) -> HttpRequest:
    """Parse raw bytes into structured request data."""
    text = raw.decode("utf-8", errors="replace")

    # Headers and body are separated by a blank line
    if "\r\n\r\n" in text:
        head_section, body = text.split("\r\n\r\n", 1)
    else:
        head_section, body = text, ""

    lines = head_section.split("\r\n")

    # First line: "GET /path HTTP/1.1"
    method, path, version = lines[0].split(" ", 2)

    # Remaining lines: "Key: Value"
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    return HttpRequest(method, path, version, headers, body)
```

A raw GET request looks like this on the wire:

```
GET /hello?name=world HTTP/1.1\r\n
Host: localhost:9999\r\n
User-Agent: PythonKata/1.0\r\n
\r\n
```

### 2. HTTP Response Building

```python
class HttpResponse(NamedTuple):
    status_code: int
    status_text: str
    headers: dict[str, str]
    body: str

def build_http_response(response: HttpResponse) -> bytes:
    status_line = f"HTTP/1.1 {response.status_code} {response.status_text}"
    headers = dict(response.headers)
    headers.setdefault("Content-Length", str(len(response.body.encode())))
    headers.setdefault("Content-Type", "text/plain; charset=utf-8")

    header_lines = [f"{k}: {v}" for k, v in headers.items()]
    head = "\r\n".join([status_line] + header_lines)
    return f"{head}\r\n\r\n{response.body}".encode("utf-8")
```

### 3. Raw TCP Server

```python
import socket
import threading

class TcpServer:
    def __init__(self, host="127.0.0.1", port=0):
        self.host = host
        self.port = port           # port=0 -> OS picks available port
        self.routes = {}
        self._server_socket = None
        self._running = False

    def route(self, path):
        """Register a handler via decorator."""
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator

    def start(self) -> int:
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)
        self._server_socket.settimeout(0.5)
        self.port = self._server_socket.getsockname()[1]
        self._running = True
        return self.port

    def serve_forever(self):
        while self._running:
            try:
                client_socket, address = self._server_socket.accept()
                handle_client(client_socket, address, self.routes)
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        self._running = False
        self._server_socket.close()
```

### 4. Sending a Request with Raw Sockets

```python
def send_http_request(host, port, method, path):
    """What curl and browsers do under the hood."""
    raw = f"{method} {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n\r\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(raw.encode("utf-8"))

        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)

    response = b"".join(chunks).decode("utf-8")
    head, body = response.split("\r\n\r\n", 1)
    return head.split("\r\n")[0], body  # (status_line, body)
```

## Playground

```bash
python playground/36_tcp_socket_server.py
```

Expected output:

```
--- Section 1: HTTP Message Parsing ---
  Method: GET
  Path: /hello?name=world
  Version: HTTP/1.1
  Headers: {'Host': 'localhost:9999', 'User-Agent': 'PythonKata/1.0', 'Accept': 'text/plain'}
  Response starts with: HTTP/1.1 200 OK
  POST body parsed: {"name": "ignite learner"}
  [VALID] HTTP parsing works correctly

--- Section 2: Raw TCP Server ---
  Server started on 127.0.0.1:<port>
  GET / -> HTTP/1.1 200 OK
    Body: Welcome to Ignite!
  GET /hello?name=Kata -> HTTP/1.1 200 OK
    Body: Hello, Kata!
  GET /json -> HTTP/1.1 200 OK
    Body: {"framework": "Ignite", "version": "0.1.0"}
  GET /nonexistent -> HTTP/1.1 404 Not Found
    Body: 404 Not Found: /nonexistent
  [VALID] All HTTP requests handled correctly
  Server stopped

--- Section 3: Understanding the Layers ---
  The HTTP request/response stack:
    ...layers from Your Code down to Network...

--- Summary ---
HTTP is just structured text over TCP:
  - Request: METHOD /path HTTP/1.1 + headers + body
  - Response: HTTP/1.1 STATUS_CODE STATUS_TEXT + headers + body
  - \r\n separates lines, \r\n\r\n separates headers from body
  - socket module gives us raw TCP (what web servers use internally)
  - Frameworks abstract all of this away for you

All 3 sections passed. TCP socket server concepts mastered!
Next up: Kata 37 -- ASGI protocol primer!
```

## How It Works

### HTTP Message Anatomy

```
Request:                           Response:
----------------------------       ----------------------------
GET /path HTTP/1.1\r\n             HTTP/1.1 200 OK\r\n
Host: localhost:8000\r\n           Content-Type: text/plain\r\n
Accept: text/plain\r\n             Content-Length: 13\r\n
\r\n                               \r\n
(optional body)                    Hello, World!
```

Key observations:
- **`\r\n`** (carriage return + line feed) separates each line -- this is required by the HTTP spec
- **`\r\n\r\n`** (blank line) separates headers from body
- The **request line** has three parts: method, path, version
- The **status line** has three parts: version, code, text
- Headers are **key: value** pairs, one per line

### TCP Socket Lifecycle

```
Server                              Client
======                              ======
socket()                            socket()
bind((host, port))
listen(backlog)
accept() -------- blocks --------
                                    connect((host, port))
      <---- TCP handshake ---->
accept() returns (client_sock, addr)
recv(4096) <---- blocks ----        sendall(request_bytes)
      <---- request bytes ----
sendall(response_bytes)             recv(4096)
      ---- response bytes ---->
close()                             close()
```

### Why port=0?

When you bind to port 0, the operating system picks an available port. This avoids "Address already in use" errors when running tests. After binding, call `getsockname()[1]` to discover the assigned port.

## Exercises

1. **Add method routing** -- modify `handle_client` to check `request.method` and return 405 Method Not Allowed for unsupported methods (e.g., a route registered for GET only should reject POST).

2. **Parse query strings** -- write a function `parse_query_string(path: str) -> dict[str, str]` that extracts query parameters from a path like `/search?q=python&page=2`.

3. **Add Content-Type detection** -- if a route handler returns a string starting with `{` or `[`, set the Content-Type to `application/json` instead of `text/plain`.

4. **Multi-threaded server** -- modify `serve_forever` to handle each client in a new thread using `threading.Thread(target=handle_client, ...)`, allowing multiple simultaneous connections.

5. **Connection keep-alive** -- instead of closing the connection after each request, support HTTP/1.1 keep-alive by reading multiple requests from the same socket until the client sends `Connection: close`.

## What's Next

We now understand what happens at the lowest level -- raw bytes flowing over TCP sockets. In [Kata 37: ASGI Primer](./37-asgi-primer.md), we learn the **ASGI protocol**, which standardizes the interface between web servers (like uvicorn) and web frameworks (like what we're building). ASGI is the "contract" that lets our Ignite framework plug into any ASGI server.

---

[prev: 35-packaging](./35-packaging.md) | [next: 37-asgi-primer](./37-asgi-primer.md)
