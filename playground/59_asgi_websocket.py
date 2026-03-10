"""
Kata 59 -- ASGI WebSocket
Run: python playground/59_asgi_websocket.py

Build ASGI WebSocket handling: the WebSocket scope dict, the connect/accept/
send/receive/disconnect lifecycle, and a WebSocketConnection wrapper class.
Test by simulating the ASGI protocol with mock receive/send callables.

Completes within 5 seconds.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any


# ===========================================================================
# SECTION 1: WebSocket Scope
# ===========================================================================
# In ASGI, every connection starts with a "scope" dict that describes the
# connection. For WebSocket, type="websocket".

def make_websocket_scope(
    path: str = "/ws",
    headers: list[tuple[bytes, bytes]] | None = None,
    query_string: bytes = b"",
    subprotocols: list[str] | None = None,
) -> dict[str, Any]:
    """Create an ASGI WebSocket scope dict.

    The scope is passed to the ASGI app when a WebSocket connection starts.
    It contains metadata about the connection but NOT the messages themselves.
    """
    return {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "scheme": "ws",
        "path": path,
        "root_path": "",
        "query_string": query_string,
        "headers": headers or [],
        "subprotocols": subprotocols or [],
    }


# ===========================================================================
# SECTION 2: ASGI WebSocket Message Types
# ===========================================================================
# The WebSocket lifecycle in ASGI is a sequence of messages exchanged
# through the receive() and send() callables:
#
# Client connects:
#   receive() -> {"type": "websocket.connect"}
#
# Server accepts:
#   send({"type": "websocket.accept"})
#
# Client sends text:
#   receive() -> {"type": "websocket.receive", "text": "..."}
#
# Client sends binary:
#   receive() -> {"type": "websocket.receive", "bytes": b"..."}
#
# Server sends text:
#   send({"type": "websocket.send", "text": "..."})
#
# Server sends binary:
#   send({"type": "websocket.send", "bytes": b"..."})
#
# Client disconnects:
#   receive() -> {"type": "websocket.disconnect", "code": 1000}
#
# Server closes:
#   send({"type": "websocket.close", "code": 1000})

class ASGIMessageType:
    """Constants for ASGI WebSocket message types."""
    CONNECT = "websocket.connect"
    ACCEPT = "websocket.accept"
    RECEIVE = "websocket.receive"
    SEND = "websocket.send"
    DISCONNECT = "websocket.disconnect"
    CLOSE = "websocket.close"


# ===========================================================================
# SECTION 3: Mock ASGI Transport
# ===========================================================================
# For testing, we simulate the ASGI receive/send callables using queues.

class MockASGITransport:
    """Simulates the ASGI receive/send interface for testing.

    The client_queue holds messages the server will receive (client -> server).
    The server_queue holds messages the server sends (server -> client).
    """

    def __init__(self):
        self.client_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.server_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def receive(self) -> dict[str, Any]:
        """ASGI receive callable -- gets the next client message."""
        return await self.client_queue.get()

    async def send(self, message: dict[str, Any]) -> None:
        """ASGI send callable -- records the server's message."""
        await self.server_queue.put(message)

    # Helper methods for the test "client" side
    async def client_connect(self) -> None:
        """Simulate a client connecting."""
        await self.client_queue.put({"type": ASGIMessageType.CONNECT})

    async def client_send_text(self, text: str) -> None:
        """Simulate a client sending a text message."""
        await self.client_queue.put({
            "type": ASGIMessageType.RECEIVE,
            "text": text,
        })

    async def client_send_bytes(self, data: bytes) -> None:
        """Simulate a client sending binary data."""
        await self.client_queue.put({
            "type": ASGIMessageType.RECEIVE,
            "bytes": data,
        })

    async def client_disconnect(self, code: int = 1000) -> None:
        """Simulate a client disconnecting."""
        await self.client_queue.put({
            "type": ASGIMessageType.DISCONNECT,
            "code": code,
        })

    async def get_server_message(self) -> dict[str, Any]:
        """Get the next message the server sent."""
        return await self.server_queue.get()


# ===========================================================================
# SECTION 4: WebSocketConnection
# ===========================================================================
# A high-level wrapper around the raw ASGI receive/send that provides a
# clean API for WebSocket handlers.

class WebSocketState:
    """Tracks the state of a WebSocket connection."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocketConnection:
    """High-level WebSocket connection wrapping ASGI receive/send.

    Usage:
        async def websocket_handler(ws: WebSocketConnection):
            await ws.accept()
            data = await ws.receive_text()
            await ws.send_text(f"Echo: {data}")
            await ws.close()
    """

    def __init__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ):
        self.scope = scope
        self._receive = receive
        self._send = send
        self.state = WebSocketState.CONNECTING
        self.path: str = scope.get("path", "/")
        self.query_string: bytes = scope.get("query_string", b"")
        self.headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        self.subprotocols: list[str] = scope.get("subprotocols", [])

    async def accept(
        self,
        subprotocol: str | None = None,
        headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        """Accept the WebSocket connection.

        Must be called after receiving a websocket.connect event.
        """
        if self.state != WebSocketState.CONNECTING:
            raise RuntimeError(
                f"Cannot accept: state is {self.state}, expected connecting"
            )

        # Wait for the connect event
        message = await self._receive()
        if message["type"] != ASGIMessageType.CONNECT:
            raise RuntimeError(
                f"Expected websocket.connect, got {message['type']}"
            )

        # Send accept
        accept_msg: dict[str, Any] = {"type": ASGIMessageType.ACCEPT}
        if subprotocol:
            accept_msg["subprotocol"] = subprotocol
        if headers:
            accept_msg["headers"] = headers

        await self._send(accept_msg)
        self.state = WebSocketState.CONNECTED

    async def receive_message(self) -> dict[str, Any]:
        """Receive a raw ASGI WebSocket message.

        Returns the message dict. Raises WebSocketDisconnect if the
        client has disconnected.
        """
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot receive: state is {self.state}")

        message = await self._receive()

        if message["type"] == ASGIMessageType.DISCONNECT:
            self.state = WebSocketState.DISCONNECTED
            code = message.get("code", 1000)
            raise WebSocketDisconnect(code)

        return message

    async def receive_text(self) -> str:
        """Receive a text message from the client."""
        message = await self.receive_message()
        return message.get("text", "")

    async def receive_bytes(self) -> bytes:
        """Receive a binary message from the client."""
        message = await self.receive_message()
        return message.get("bytes", b"")

    async def receive_json(self) -> Any:
        """Receive and parse a JSON message from the client."""
        text = await self.receive_text()
        return json.loads(text)

    async def send_text(self, text: str) -> None:
        """Send a text message to the client."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot send: state is {self.state}")
        await self._send({
            "type": ASGIMessageType.SEND,
            "text": text,
        })

    async def send_bytes(self, data: bytes) -> None:
        """Send binary data to the client."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot send: state is {self.state}")
        await self._send({
            "type": ASGIMessageType.SEND,
            "bytes": data,
        })

    async def send_json(self, data: Any) -> None:
        """Send a JSON-serialized message to the client."""
        await self.send_text(json.dumps(data))

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection from the server side."""
        if self.state == WebSocketState.DISCONNECTED:
            return  # Already closed

        msg: dict[str, Any] = {
            "type": ASGIMessageType.CLOSE,
            "code": code,
        }
        if reason:
            msg["reason"] = reason

        await self._send(msg)
        self.state = WebSocketState.DISCONNECTED


class WebSocketDisconnect(Exception):
    """Raised when a WebSocket client disconnects."""

    def __init__(self, code: int = 1000):
        self.code = code
        super().__init__(f"WebSocket disconnected with code {code}")


# ===========================================================================
# SECTION 5: Example ASGI WebSocket App
# ===========================================================================
# A raw ASGI app that handles WebSocket connections.

async def echo_app(
    scope: dict[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """A simple ASGI WebSocket echo app.

    This is what a raw ASGI WebSocket handler looks like -- no framework,
    just the protocol.
    """
    assert scope["type"] == "websocket"

    # Wait for connection
    event = await receive()
    assert event["type"] == ASGIMessageType.CONNECT

    # Accept
    await send({"type": ASGIMessageType.ACCEPT})

    # Echo loop
    while True:
        message = await receive()

        if message["type"] == ASGIMessageType.DISCONNECT:
            break

        if message["type"] == ASGIMessageType.RECEIVE:
            text = message.get("text", "")
            await send({
                "type": ASGIMessageType.SEND,
                "text": f"echo: {text}",
            })


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_websocket_scope():
    """Show WebSocket scope creation."""
    print("--- Section 1: WebSocket Scope ---")

    scope = make_websocket_scope(
        path="/ws/chat",
        query_string=b"room=general",
        subprotocols=["graphql-ws"],
    )
    print(f"  type: {scope['type']}")
    print(f"  path: {scope['path']}")
    print(f"  query: {scope['query_string']}")
    print(f"  subprotocols: {scope['subprotocols']}")

    assert scope["type"] == "websocket"
    assert scope["path"] == "/ws/chat"
    assert scope["query_string"] == b"room=general"
    assert scope["subprotocols"] == ["graphql-ws"]

    print("  [PASS] WebSocket scope works")


def demo_message_types():
    """Show all ASGI WebSocket message types."""
    print("\n--- Section 2: Message Types ---")

    messages = [
        {"type": ASGIMessageType.CONNECT},
        {"type": ASGIMessageType.ACCEPT},
        {"type": ASGIMessageType.RECEIVE, "text": "hello"},
        {"type": ASGIMessageType.RECEIVE, "bytes": b"\x00\x01"},
        {"type": ASGIMessageType.SEND, "text": "world"},
        {"type": ASGIMessageType.SEND, "bytes": b"\x02\x03"},
        {"type": ASGIMessageType.DISCONNECT, "code": 1000},
        {"type": ASGIMessageType.CLOSE, "code": 1000},
    ]

    for msg in messages:
        label = msg["type"]
        extra = ""
        if "text" in msg:
            extra = f", text={msg['text']!r}"
        elif "bytes" in msg:
            extra = f", bytes={msg['bytes']!r}"
        elif "code" in msg:
            extra = f", code={msg['code']}"
        print(f"  {label}{extra}")

    assert ASGIMessageType.CONNECT == "websocket.connect"
    assert ASGIMessageType.ACCEPT == "websocket.accept"
    assert ASGIMessageType.RECEIVE == "websocket.receive"
    assert ASGIMessageType.SEND == "websocket.send"
    assert ASGIMessageType.DISCONNECT == "websocket.disconnect"
    assert ASGIMessageType.CLOSE == "websocket.close"

    print("  [PASS] Message types correct")


async def demo_raw_asgi_app():
    """Demonstrate a raw ASGI WebSocket echo app."""
    print("\n--- Section 3: Raw ASGI App ---")

    transport = MockASGITransport()
    scope = make_websocket_scope(path="/ws/echo")

    # Run the app in background
    async def run_app():
        await echo_app(scope, transport.receive, transport.send)

    app_task = asyncio.create_task(run_app())

    # Client connects
    await transport.client_connect()
    accept_msg = await transport.get_server_message()
    print(f"  Server: {accept_msg['type']}")
    assert accept_msg["type"] == ASGIMessageType.ACCEPT

    # Client sends messages
    await transport.client_send_text("Hello")
    reply = await transport.get_server_message()
    print(f"  Client: 'Hello' -> Server: '{reply['text']}'")
    assert reply["text"] == "echo: Hello"

    await transport.client_send_text("World")
    reply2 = await transport.get_server_message()
    print(f"  Client: 'World' -> Server: '{reply2['text']}'")
    assert reply2["text"] == "echo: World"

    # Client disconnects
    await transport.client_disconnect()
    await app_task

    print("  [PASS] Raw ASGI app works")


async def demo_websocket_connection():
    """Demonstrate the WebSocketConnection wrapper class."""
    print("\n--- Section 4: WebSocketConnection ---")

    transport = MockASGITransport()
    scope = make_websocket_scope(path="/ws/chat")
    ws = WebSocketConnection(scope, transport.receive, transport.send)

    assert ws.state == WebSocketState.CONNECTING
    assert ws.path == "/ws/chat"

    # Simulate client connect
    await transport.client_connect()

    # Server accepts
    await ws.accept()
    assert ws.state == WebSocketState.CONNECTED
    accept_msg = await transport.get_server_message()
    assert accept_msg["type"] == ASGIMessageType.ACCEPT
    print(f"  State after accept: {ws.state}")

    # Receive text
    await transport.client_send_text("Hi there")
    text = await ws.receive_text()
    print(f"  Received text: '{text}'")
    assert text == "Hi there"

    # Send text
    await ws.send_text("Hello back!")
    sent = await transport.get_server_message()
    print(f"  Sent text: '{sent['text']}'")
    assert sent["text"] == "Hello back!"

    # JSON round-trip
    await transport.client_send_text('{"action": "ping"}')
    data = await ws.receive_json()
    print(f"  Received JSON: {data}")
    assert data == {"action": "ping"}

    await ws.send_json({"action": "pong"})
    json_msg = await transport.get_server_message()
    print(f"  Sent JSON: {json_msg['text']}")
    assert json.loads(json_msg["text"]) == {"action": "pong"}

    # Server close
    await ws.close(code=1000)
    close_msg = await transport.get_server_message()
    assert close_msg["type"] == ASGIMessageType.CLOSE
    assert close_msg["code"] == 1000
    assert ws.state == WebSocketState.DISCONNECTED
    print(f"  State after close: {ws.state}")

    print("  [PASS] WebSocketConnection works")


async def demo_disconnect_handling():
    """Show handling of client disconnection."""
    print("\n--- Section 5: Disconnect Handling ---")

    transport = MockASGITransport()
    scope = make_websocket_scope()
    ws = WebSocketConnection(scope, transport.receive, transport.send)

    await transport.client_connect()
    await ws.accept()
    _ = await transport.get_server_message()

    # Send a message, then disconnect
    await transport.client_send_text("Last message")
    text = await ws.receive_text()
    print(f"  Received: '{text}'")

    # Client disconnects
    await transport.client_disconnect(code=1001)

    try:
        await ws.receive_text()
        assert False, "Should have raised WebSocketDisconnect"
    except WebSocketDisconnect as exc:
        print(f"  Caught disconnect: code={exc.code}")
        assert exc.code == 1001

    assert ws.state == WebSocketState.DISCONNECTED
    print(f"  State: {ws.state}")

    # Trying to send after disconnect raises
    try:
        await ws.send_text("This should fail")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        print(f"  Send after disconnect: {exc}")

    print("  [PASS] Disconnect handling works")


async def demo_binary_messages():
    """Show binary message handling."""
    print("\n--- Section 6: Binary Messages ---")

    transport = MockASGITransport()
    scope = make_websocket_scope()
    ws = WebSocketConnection(scope, transport.receive, transport.send)

    await transport.client_connect()
    await ws.accept()
    _ = await transport.get_server_message()

    # Send binary data
    binary_data = bytes(range(256))
    await transport.client_send_bytes(binary_data)
    received = await ws.receive_bytes()
    assert received == binary_data
    print(f"  Received {len(received)} bytes of binary data")

    # Server sends binary
    await ws.send_bytes(b"\xDE\xAD\xBE\xEF")
    sent = await transport.get_server_message()
    assert sent["bytes"] == b"\xDE\xAD\xBE\xEF"
    print(f"  Sent binary: {sent['bytes'].hex()}")

    await ws.close()
    _ = await transport.get_server_message()

    print("  [PASS] Binary messages work")


async def async_main():
    demo_websocket_scope()
    demo_message_types()
    await demo_raw_asgi_app()
    await demo_websocket_connection()
    await demo_disconnect_handling()
    await demo_binary_messages()


def main():
    asyncio.run(async_main())

    print("\n--- Summary ---")
    print("ASGI WebSocket implementation covers:")
    print("  - WebSocket scope with path, query, headers, subprotocols")
    print("  - ASGI message types: connect, accept, receive, send, close")
    print("  - MockASGITransport for testing without a real server")
    print("  - WebSocketConnection wrapper with clean API")
    print("  - Text, binary, and JSON message support")
    print("  - Disconnect handling with WebSocketDisconnect exception")
    print("  - Connection state tracking (connecting/connected/disconnected)")
    print("\nAll 6 sections passed. ASGI WebSocket mastered!")
    print("Next up: Kata 60 -- WebSocket routes & handlers!")


if __name__ == "__main__":
    main()
