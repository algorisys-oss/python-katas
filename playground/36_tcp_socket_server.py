"""
Kata 36 -- TCP Socket Server
Run: python playground/36_tcp_socket_server.py

Build a raw TCP server that speaks HTTP. Understand that HTTP is just
structured text over a TCP connection. Parse request lines, headers,
and send proper HTTP/1.1 responses.

Starts a server in a background thread, sends requests to it, then shuts down.
Completes within 5 seconds.
"""

import socket
import threading
import time
from typing import NamedTuple


# ===========================================================================
# SECTION 1: HTTP Message Parsing
# ===========================================================================

class HttpRequest(NamedTuple):
    """Parsed HTTP request."""
    method: str
    path: str
    version: str
    headers: dict[str, str]
    body: str


class HttpResponse(NamedTuple):
    """HTTP response to send."""
    status_code: int
    status_text: str
    headers: dict[str, str]
    body: str


# Standard HTTP status texts
STATUS_TEXTS = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}


def parse_http_request(raw: bytes) -> HttpRequest:
    """Parse raw HTTP request bytes into an HttpRequest.

    HTTP request format:
        METHOD /path HTTP/1.1\r\n
        Header-Name: Header-Value\r\n
        \r\n
        optional body
    """
    # Decode bytes to string
    text = raw.decode("utf-8", errors="replace")

    # Split headers from body at the blank line (\r\n\r\n)
    if "\r\n\r\n" in text:
        head_section, body = text.split("\r\n\r\n", 1)
    else:
        head_section = text
        body = ""

    # Split into individual lines
    lines = head_section.split("\r\n")

    # First line is the request line: "GET /path HTTP/1.1"
    request_line = lines[0]
    parts = request_line.split(" ", 2)
    if len(parts) != 3:
        raise ValueError(f"Malformed request line: {request_line!r}")

    method, path, version = parts

    # Remaining lines are headers: "Key: Value"
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    return HttpRequest(
        method=method,
        path=path,
        version=version,
        headers=headers,
        body=body,
    )


def build_http_response(response: HttpResponse) -> bytes:
    """Build raw HTTP response bytes from an HttpResponse.

    HTTP response format:
        HTTP/1.1 200 OK\r\n
        Header-Name: Header-Value\r\n
        \r\n
        body
    """
    # Status line
    status_line = f"HTTP/1.1 {response.status_code} {response.status_text}"

    # Add Content-Length if not present
    headers = dict(response.headers)
    if "Content-Length" not in headers:
        headers["Content-Length"] = str(len(response.body.encode("utf-8")))
    if "Content-Type" not in headers:
        headers["Content-Type"] = "text/plain; charset=utf-8"

    # Build header lines
    header_lines = [f"{key}: {value}" for key, value in headers.items()]

    # Join everything with \r\n (HTTP line ending)
    head = "\r\n".join([status_line] + header_lines)

    # Headers and body separated by blank line
    raw = f"{head}\r\n\r\n{response.body}"
    return raw.encode("utf-8")


def demo_http_parsing():
    """Demonstrate HTTP request parsing and response building."""
    # Simulate a raw HTTP request
    raw_request = (
        b"GET /hello?name=world HTTP/1.1\r\n"
        b"Host: localhost:9999\r\n"
        b"User-Agent: PythonKata/1.0\r\n"
        b"Accept: text/plain\r\n"
        b"\r\n"
    )

    request = parse_http_request(raw_request)
    print(f"  Method: {request.method}")
    print(f"  Path: {request.path}")
    print(f"  Version: {request.version}")
    print(f"  Headers: {dict(request.headers)}")

    assert request.method == "GET"
    assert request.path == "/hello?name=world"
    assert request.version == "HTTP/1.1"
    assert request.headers["Host"] == "localhost:9999"
    assert request.headers["User-Agent"] == "PythonKata/1.0"

    # Build a response
    response = HttpResponse(
        status_code=200,
        status_text="OK",
        headers={"Server": "Ignite/0.1"},
        body="Hello, World!",
    )
    raw_response = build_http_response(response)
    response_text = raw_response.decode("utf-8")

    print(f"  Response starts with: {response_text.split(chr(13))[0]}")
    assert response_text.startswith("HTTP/1.1 200 OK")
    assert "Content-Length: 13" in response_text
    assert response_text.endswith("Hello, World!")

    # Test POST with body
    raw_post = (
        b"POST /users HTTP/1.1\r\n"
        b"Host: localhost:9999\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 27\r\n"
        b"\r\n"
        b'{"name": "ignite learner"}'
    )
    post_req = parse_http_request(raw_post)
    assert post_req.method == "POST"
    assert post_req.path == "/users"
    assert post_req.body == '{"name": "ignite learner"}'
    assert post_req.headers["Content-Type"] == "application/json"
    print(f"  POST body parsed: {post_req.body}")

    print("  [VALID] HTTP parsing works correctly")


# ===========================================================================
# SECTION 2: Raw TCP Server
# ===========================================================================

def handle_client(client_socket: socket.socket, address: tuple[str, int],
                  routes: dict[str, callable]) -> None:
    """Handle a single client connection.

    Reads raw bytes, parses the HTTP request, finds a handler,
    and sends back an HTTP response.
    """
    try:
        # Read up to 4KB from the client
        raw_data = client_socket.recv(4096)
        if not raw_data:
            return

        # Parse the HTTP request
        try:
            request = parse_http_request(raw_data)
        except ValueError:
            # Malformed request -- send 400
            response = HttpResponse(400, "Bad Request", {}, "Bad Request")
            client_socket.sendall(build_http_response(response))
            return

        # Find a handler for this path (strip query string)
        path = request.path.split("?")[0]
        handler = routes.get(path)

        if handler:
            body = handler(request)
            response = HttpResponse(200, "OK", {"Server": "Ignite/0.1"}, body)
        else:
            response = HttpResponse(
                404, "Not Found", {"Server": "Ignite/0.1"},
                f"404 Not Found: {path}",
            )

        client_socket.sendall(build_http_response(response))

    finally:
        client_socket.close()


class TcpServer:
    """A minimal TCP server that speaks HTTP.

    This is NOT production-ready -- it's educational. It shows what
    frameworks like Flask/FastAPI do under the hood (via WSGI/ASGI servers).
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        # port=0 lets the OS pick an available port (avoids conflicts)
        self.host = host
        self.port = port
        self.routes: dict[str, callable] = {}
        self._server_socket: socket.socket | None = None
        self._running = False

    def route(self, path: str):
        """Register a route handler (decorator pattern)."""
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator

    def start(self) -> int:
        """Start the server and return the actual port number.

        Uses SO_REUSEADDR to allow quick restart.
        Returns the port the OS assigned.
        """
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow port reuse (avoids "Address already in use" on restart)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)
        # Set a timeout so accept() doesn't block forever
        self._server_socket.settimeout(0.5)

        # Get the actual port (important when port=0)
        actual_port = self._server_socket.getsockname()[1]
        self.port = actual_port
        self._running = True
        return actual_port

    def serve_forever(self):
        """Accept connections until stopped.

        Each connection is handled in the current thread (single-threaded).
        A real server would use threads, asyncio, or a process pool.
        """
        while self._running:
            try:
                client_socket, address = self._server_socket.accept()
                handle_client(client_socket, address, self.routes)
            except socket.timeout:
                # Timeout from settimeout() -- loop back and check _running
                continue
            except OSError:
                # Socket was closed
                break

    def stop(self):
        """Stop the server."""
        self._running = False
        if self._server_socket:
            self._server_socket.close()


def send_http_request(host: str, port: int, method: str, path: str,
                      headers: dict[str, str] | None = None,
                      body: str = "") -> tuple[str, str]:
    """Send a raw HTTP request using a TCP socket.

    Returns (status_line, response_body).
    This is what curl, wget, and browsers do under the hood.
    """
    headers = headers or {}
    headers.setdefault("Host", f"{host}:{port}")
    headers.setdefault("Connection", "close")

    # Build the raw request
    request_line = f"{method} {path} HTTP/1.1"
    header_lines = [f"{k}: {v}" for k, v in headers.items()]
    raw = "\r\n".join([request_line] + header_lines) + "\r\n\r\n" + body

    # Connect and send
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(raw.encode("utf-8"))

        # Read the full response
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)

    response_text = b"".join(chunks).decode("utf-8")

    # Split into status line and body
    if "\r\n\r\n" in response_text:
        head, resp_body = response_text.split("\r\n\r\n", 1)
        status_line = head.split("\r\n")[0]
    else:
        status_line = response_text.split("\r\n")[0]
        resp_body = ""

    return status_line, resp_body


def demo_tcp_server():
    """Start a TCP server, send requests to it, verify responses."""

    # --- Create server and register routes ---
    server = TcpServer(host="127.0.0.1", port=0)

    @server.route("/")
    def index(request: HttpRequest) -> str:
        return "Welcome to Ignite!"

    @server.route("/hello")
    def hello(request: HttpRequest) -> str:
        # Parse query string manually (no urllib needed)
        query = ""
        if "?" in request.path:
            query = request.path.split("?", 1)[1]
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        name = params.get("name", "World")
        return f"Hello, {name}!"

    @server.route("/json")
    def json_endpoint(request: HttpRequest) -> str:
        return '{"framework": "Ignite", "version": "0.1.0"}'

    # --- Start server in background thread ---
    port = server.start()
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"  Server started on 127.0.0.1:{port}")

    # Give the server a moment to be ready
    time.sleep(0.1)

    try:
        # --- Send requests and verify responses ---

        # Test 1: GET /
        status, body = send_http_request("127.0.0.1", port, "GET", "/")
        print(f"  GET / -> {status}")
        print(f"    Body: {body}")
        assert "200 OK" in status
        assert body == "Welcome to Ignite!"

        # Test 2: GET /hello?name=Kata
        status, body = send_http_request("127.0.0.1", port, "GET", "/hello?name=Kata")
        print(f"  GET /hello?name=Kata -> {status}")
        print(f"    Body: {body}")
        assert "200 OK" in status
        assert body == "Hello, Kata!"

        # Test 3: GET /json
        status, body = send_http_request("127.0.0.1", port, "GET", "/json")
        print(f"  GET /json -> {status}")
        print(f"    Body: {body}")
        assert "200 OK" in status
        assert '"Ignite"' in body

        # Test 4: GET /nonexistent -> 404
        status, body = send_http_request("127.0.0.1", port, "GET", "/nonexistent")
        print(f"  GET /nonexistent -> {status}")
        print(f"    Body: {body}")
        assert "404" in status

        print("  [VALID] All HTTP requests handled correctly")

    finally:
        server.stop()
        server_thread.join(timeout=2)
        print("  Server stopped")


# ===========================================================================
# SECTION 3: Understanding the Layers
# ===========================================================================

def demo_layers():
    """Show the layers between your code and the network."""
    layers = [
        ("Your Code", "def hello(): return 'Hello!'", "Application logic"),
        ("Framework", "route('/hello', hello)", "URL routing, middleware"),
        ("ASGI/WSGI", "async app(scope, receive, send)", "Protocol interface"),
        ("Server", "uvicorn / gunicorn", "Connection management"),
        ("TCP Socket", "socket.accept(), socket.recv()", "Raw bytes over network"),
        ("OS Kernel", "TCP/IP stack", "Packet routing, checksums"),
        ("Network", "Ethernet / WiFi", "Physical transmission"),
    ]

    print("  The HTTP request/response stack:")
    print()
    for i, (layer, example, description) in enumerate(layers):
        indent = "    " + "  " * i
        print(f"{indent}[{layer}]")
        print(f"{indent}  {example}")
        print(f"{indent}  -- {description}")
        if i < len(layers) - 1:
            print(f"{indent}  |")

    print()
    print("  In this kata we built the TCP Socket + Framework layers.")
    print("  Next: we learn ASGI, the standard interface between Server and Framework.")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: HTTP Parsing ---
    print("--- Section 1: HTTP Message Parsing ---")
    demo_http_parsing()
    print()

    # --- Section 2: TCP Server ---
    print("--- Section 2: Raw TCP Server ---")
    demo_tcp_server()
    print()

    # --- Section 3: Layers ---
    print("--- Section 3: Understanding the Layers ---")
    demo_layers()
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("HTTP is just structured text over TCP:")
    print("  - Request: METHOD /path HTTP/1.1 + headers + body")
    print("  - Response: HTTP/1.1 STATUS_CODE STATUS_TEXT + headers + body")
    print("  - \\r\\n separates lines, \\r\\n\\r\\n separates headers from body")
    print("  - socket module gives us raw TCP (what web servers use internally)")
    print("  - Frameworks abstract all of this away for you")
    print()
    print("All 3 sections passed. TCP socket server concepts mastered!")
    print("Next up: Kata 37 -- ASGI protocol primer!")
