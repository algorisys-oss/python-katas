"""
Ignite WebSocket Module

WebSocketConnection wrapping the ASGI WebSocket protocol, and
ConnectionManager for tracking active connections and broadcasting.

Self-contained -- only stdlib imports.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable


# ---------------------------------------------------------------------------
# WebSocket state constants
# ---------------------------------------------------------------------------

class WebSocketState:
    """Tracks the lifecycle state of a WebSocket connection."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class WebSocketDisconnect(Exception):
    """Raised when a WebSocket client disconnects."""

    def __init__(self, code: int = 1000) -> None:
        self.code = code
        super().__init__(f"WebSocket disconnected with code {code}")


# ---------------------------------------------------------------------------
# WebSocketConnection
# ---------------------------------------------------------------------------

class WebSocketConnection:
    """High-level WebSocket connection wrapping ASGI receive/send.

    Usage inside a handler::

        async def handler(ws: WebSocketConnection):
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
    ) -> None:
        self.scope = scope
        self._receive = receive
        self._send = send
        self.state = WebSocketState.CONNECTING
        self.path: str = scope.get("path", "/")
        self.query_string: bytes = scope.get("query_string", b"")
        self.headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        self.subprotocols: list[str] = scope.get("subprotocols", [])
        self.client_id: str = scope.get("client_id", "unknown")

    # -- Lifecycle -----------------------------------------------------------

    async def accept(
        self,
        subprotocol: str | None = None,
        headers: list[tuple[bytes, bytes]] | None = None,
    ) -> None:
        """Accept the incoming WebSocket connection.

        Must be called before sending or receiving messages.
        """
        if self.state != WebSocketState.CONNECTING:
            raise RuntimeError(
                f"Cannot accept: state is {self.state}, expected connecting"
            )

        message = await self._receive()
        if message["type"] != "websocket.connect":
            raise RuntimeError(
                f"Expected websocket.connect, got {message['type']}"
            )

        accept_msg: dict[str, Any] = {"type": "websocket.accept"}
        if subprotocol:
            accept_msg["subprotocol"] = subprotocol
        if headers:
            accept_msg["headers"] = headers

        await self._send(accept_msg)
        self.state = WebSocketState.CONNECTED

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection from the server side."""
        if self.state == WebSocketState.DISCONNECTED:
            return
        msg: dict[str, Any] = {"type": "websocket.close", "code": code}
        if reason:
            msg["reason"] = reason
        await self._send(msg)
        self.state = WebSocketState.DISCONNECTED

    # -- Receiving -----------------------------------------------------------

    async def receive_message(self) -> dict[str, Any]:
        """Receive a raw ASGI WebSocket message.

        Raises :class:`WebSocketDisconnect` when the client disconnects.
        """
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot receive: state is {self.state}")

        message = await self._receive()

        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise WebSocketDisconnect(message.get("code", 1000))

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
        """Receive and parse a JSON text message."""
        text = await self.receive_text()
        return json.loads(text)

    # -- Sending -------------------------------------------------------------

    async def send_text(self, text: str) -> None:
        """Send a text message to the client."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot send: state is {self.state}")
        await self._send({"type": "websocket.send", "text": text})

    async def send_bytes(self, data: bytes) -> None:
        """Send binary data to the client."""
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot send: state is {self.state}")
        await self._send({"type": "websocket.send", "bytes": data})

    async def send_json(self, data: Any) -> None:
        """Send a JSON-serialized text message."""
        await self.send_text(json.dumps(data))


# ---------------------------------------------------------------------------
# ConnectionManager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages a set of active WebSocket connections.

    Supports adding/removing connections, sending to a specific client,
    broadcasting to all, and broadcasting to all except one.
    """

    def __init__(self) -> None:
        self._connections: dict[str, WebSocketConnection] = {}

    @property
    def active_count(self) -> int:
        """Number of currently tracked connections."""
        return len(self._connections)

    @property
    def client_ids(self) -> list[str]:
        """List of connected client IDs."""
        return list(self._connections.keys())

    async def connect(self, websocket: WebSocketConnection) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self._connections[websocket.client_id] = websocket

    def disconnect(self, websocket: WebSocketConnection) -> None:
        """Remove a WebSocket connection from the manager."""
        self._connections.pop(websocket.client_id, None)

    async def send_to(self, client_id: str, message: str) -> bool:
        """Send a text message to a specific client.

        Returns ``True`` if the message was sent successfully.
        """
        ws = self._connections.get(client_id)
        if ws and ws.state == WebSocketState.CONNECTED:
            await ws.send_text(message)
            return True
        return False

    async def send_json_to(self, client_id: str, data: Any) -> bool:
        """Send a JSON message to a specific client."""
        return await self.send_to(client_id, json.dumps(data))

    async def broadcast(self, message: str) -> int:
        """Send a text message to every connected client.

        Returns the number of clients the message was sent to.
        Disconnected clients are automatically cleaned up.
        """
        sent_count = 0
        disconnected: list[str] = []

        for client_id, ws in self._connections.items():
            if ws.state == WebSocketState.CONNECTED:
                try:
                    await ws.send_text(message)
                    sent_count += 1
                except Exception:
                    disconnected.append(client_id)
            else:
                disconnected.append(client_id)

        for cid in disconnected:
            self._connections.pop(cid, None)

        return sent_count

    async def broadcast_json(self, data: Any) -> int:
        """Broadcast a JSON-serialized message to all clients."""
        return await self.broadcast(json.dumps(data))

    async def broadcast_except(self, message: str, exclude_id: str) -> int:
        """Broadcast to all clients except the one with *exclude_id*."""
        sent_count = 0
        for client_id, ws in self._connections.items():
            if client_id != exclude_id and ws.state == WebSocketState.CONNECTED:
                try:
                    await ws.send_text(message)
                    sent_count += 1
                except Exception:
                    pass
        return sent_count
