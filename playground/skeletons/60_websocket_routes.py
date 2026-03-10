"""
Kata 60 -- WebSocket Routes & Handlers
Run: python playground/skeletons/60_websocket_routes.py

Add WebSocket route support to Ignite: @app.websocket() decorator,
ConnectionManager class for tracking connections and broadcasting,
and test by simulating multiple WebSocket connections.

Completes within 5 seconds.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable


# ===========================================================================
# SECTION 1: WebSocket Connection (simplified from Kata 59)
# ===========================================================================

class WebSocketState:
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocketDisconnect(Exception):
    def __init__(self, code: int = 1000):
        self.code = code
        super().__init__(f"WebSocket disconnected with code {code}")


class WebSocketConnection:
    """High-level WebSocket connection wrapping ASGI receive/send."""

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
        self.client_id: str = scope.get("client_id", "unknown")

    async def accept(self) -> None:
        message = await self._receive()
        if message["type"] != "websocket.connect":
            raise RuntimeError(f"Expected connect, got {message['type']}")
        await self._send({"type": "websocket.accept"})
        self.state = WebSocketState.CONNECTED

    async def receive_text(self) -> str:
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot receive: state is {self.state}")
        message = await self._receive()
        if message["type"] == "websocket.disconnect":
            self.state = WebSocketState.DISCONNECTED
            raise WebSocketDisconnect(message.get("code", 1000))
        return message.get("text", "")

    async def receive_json(self) -> Any:
        text = await self.receive_text()
        return json.loads(text)

    async def send_text(self, text: str) -> None:
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError(f"Cannot send: state is {self.state}")
        await self._send({"type": "websocket.send", "text": text})

    async def send_json(self, data: Any) -> None:
        await self.send_text(json.dumps(data))

    async def close(self, code: int = 1000) -> None:
        if self.state == WebSocketState.DISCONNECTED:
            return
        await self._send({"type": "websocket.close", "code": code})
        self.state = WebSocketState.DISCONNECTED


# ===========================================================================
# SECTION 2: Mock Transport (simplified from Kata 59)
# ===========================================================================

class MockASGITransport:
    """Simulates ASGI receive/send for testing."""

    def __init__(self):
        self.client_queue: asyncio.Queue[dict] = asyncio.Queue()
        self.server_queue: asyncio.Queue[dict] = asyncio.Queue()

    async def receive(self) -> dict:
        return await self.client_queue.get()

    async def send(self, message: dict) -> None:
        await self.server_queue.put(message)

    async def client_connect(self) -> None:
        await self.client_queue.put({"type": "websocket.connect"})

    async def client_send_text(self, text: str) -> None:
        await self.client_queue.put({"type": "websocket.receive", "text": text})

    async def client_disconnect(self, code: int = 1000) -> None:
        await self.client_queue.put({"type": "websocket.disconnect", "code": code})

    async def get_server_message(self) -> dict:
        return await self.server_queue.get()


# ===========================================================================
# SECTION 3: ConnectionManager
# ===========================================================================
# Tracks all active WebSocket connections. Supports sending to a specific
# client, broadcasting to all, and removing disconnected clients.

class ConnectionManager:
    """Manages a set of active WebSocket connections.

    Supports:
    - Adding/removing connections
    - Sending to a specific client by ID
    - Broadcasting to all connected clients
    - Broadcasting to all except one (e.g., the sender)
    """

    def __init__(self):
        # TODO: Initialize a dict to store connections: client_id -> WebSocketConnection
        self._connections: dict[str, WebSocketConnection] = {}

    @property
    def active_count(self) -> int:
        """Number of active connections."""
        # TODO: Return the number of connections
        pass

    @property
    def client_ids(self) -> list[str]:
        """List of connected client IDs."""
        # TODO: Return list of keys from self._connections
        pass

    async def connect(self, websocket: WebSocketConnection) -> None:
        """Accept and register a new WebSocket connection."""
        # TODO: Call websocket.accept() and store in self._connections
        # keyed by websocket.client_id
        pass

    def disconnect(self, websocket: WebSocketConnection) -> None:
        """Remove a WebSocket connection from the manager."""
        # TODO: Remove the websocket from self._connections
        # HINT: self._connections.pop(websocket.client_id, None)
        pass

    async def send_to(self, client_id: str, message: str) -> bool:
        """Send a text message to a specific client.

        Returns True if the client was found and message sent.
        """
        # TODO: Look up the client in self._connections
        # If found and state is CONNECTED, call send_text and return True
        # Otherwise return False
        pass

    async def send_json_to(self, client_id: str, data: Any) -> bool:
        """Send a JSON message to a specific client."""
        return await self.send_to(client_id, json.dumps(data))

    async def broadcast(self, message: str) -> int:
        """Send a text message to all connected clients.

        Returns the number of clients the message was sent to.
        """
        # TODO: Iterate over all connections and send the message
        # Track how many were sent successfully
        # Clean up any disconnected clients
        # Return the count
        pass

    async def broadcast_json(self, data: Any) -> int:
        """Broadcast a JSON message to all connected clients."""
        return await self.broadcast(json.dumps(data))

    async def broadcast_except(
        self, message: str, exclude_id: str
    ) -> int:
        """Broadcast to all clients except the specified one.

        Useful for relaying a client's message to everyone else.
        """
        # TODO: Same as broadcast but skip the client with exclude_id
        pass


# ===========================================================================
# SECTION 4: WebSocket Router
# ===========================================================================
# A router that maps paths to WebSocket handler functions, similar to
# HTTP route decorators.

WebSocketHandler = Callable[[WebSocketConnection], Any]


class WebSocketRouter:
    """Routes WebSocket connections to handler functions by path."""

    def __init__(self):
        self._routes: dict[str, WebSocketHandler] = {}

    def add_route(self, path: str, handler: WebSocketHandler) -> None:
        """Register a WebSocket handler for a path."""
        self._routes[path] = handler

    def websocket(self, path: str) -> Callable:
        """Decorator to register a WebSocket handler.

        Usage:
            @router.websocket("/ws/chat")
            async def chat_handler(ws: WebSocketConnection):
                ...
        """
        # TODO: Return a decorator that stores the handler in self._routes
        # and returns the original function
        def decorator(func: WebSocketHandler) -> WebSocketHandler:
            # TODO: Store func in self._routes[path]
            return func
        return decorator

    def get_handler(self, path: str) -> WebSocketHandler | None:
        """Look up the handler for a given path."""
        return self._routes.get(path)

    @property
    def routes(self) -> list[str]:
        """List all registered WebSocket paths."""
        return list(self._routes.keys())


# ===========================================================================
# SECTION 5: Ignite App with WebSocket Support
# ===========================================================================

class IgniteApp:
    """Simplified Ignite app with both HTTP and WebSocket routing."""

    def __init__(self):
        self._http_routes: dict[str, Callable] = {}
        self._ws_router = WebSocketRouter()
        self.connection_manager = ConnectionManager()

    def route(self, path: str) -> Callable:
        """Register an HTTP route handler."""
        def decorator(func: Callable) -> Callable:
            self._http_routes[path] = func
            return func
        return decorator

    def websocket(self, path: str) -> Callable:
        """Register a WebSocket handler.

        Usage:
            @app.websocket("/ws")
            async def ws_handler(ws: WebSocketConnection):
                await ws.accept()
                ...
        """
        # TODO: Delegate to self._ws_router.websocket(path)
        pass

    async def handle_websocket(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        """Route a WebSocket connection to its handler."""
        # TODO: Get the path from scope
        # Look up the handler using self._ws_router.get_handler(path)
        # If no handler: consume the connect event, send close with code 4004
        # If handler found: create WebSocketConnection and call handler(ws)
        pass


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

async def demo_connection_manager():
    """Demonstrate the ConnectionManager class."""
    print("--- Section 1: ConnectionManager ---")

    manager = ConnectionManager()
    assert manager.active_count == 0

    # Create 3 mock connections
    transports = []
    connections = []
    for i in range(3):
        transport = MockASGITransport()
        scope = {"type": "websocket", "path": "/ws", "client_id": f"user_{i}"}
        ws = WebSocketConnection(scope, transport.receive, transport.send)
        await transport.client_connect()
        transports.append(transport)
        connections.append(ws)

    # Connect all
    for ws in connections:
        await manager.connect(ws)

    assert manager.active_count == 3
    print(f"  Connected: {manager.client_ids}")

    # Consume accept messages
    for t in transports:
        msg = await t.get_server_message()
        assert msg["type"] == "websocket.accept"

    # Send to specific client
    sent = await manager.send_to("user_1", "Hello user_1!")
    assert sent
    msg = await transports[1].get_server_message()
    print(f"  Send to user_1: '{msg['text']}'")
    assert msg["text"] == "Hello user_1!"

    # Send to nonexistent client
    sent = await manager.send_to("user_99", "Hello?")
    assert not sent
    print("  Send to user_99: not found (returned False)")

    # Broadcast to all
    count = await manager.broadcast("Attention everyone!")
    assert count == 3
    for i, t in enumerate(transports):
        msg = await t.get_server_message()
        assert msg["text"] == "Attention everyone!"
    print(f"  Broadcast to {count} clients")

    # Broadcast except sender
    count = await manager.broadcast_except("user_0 says hi!", "user_0")
    assert count == 2
    for t in transports[1:]:
        msg = await t.get_server_message()
        assert msg["text"] == "user_0 says hi!"
    print(f"  Broadcast except user_0: sent to {count} clients")

    # Disconnect one
    manager.disconnect(connections[2])
    assert manager.active_count == 2
    print(f"  After disconnect: {manager.client_ids}")

    print("  [PASS] ConnectionManager works")


async def demo_websocket_router():
    """Demonstrate the WebSocket router."""
    print("\n--- Section 2: WebSocket Router ---")

    router = WebSocketRouter()

    @router.websocket("/ws/echo")
    async def echo_handler(ws: WebSocketConnection):
        await ws.accept()
        try:
            while True:
                text = await ws.receive_text()
                await ws.send_text(f"echo: {text}")
        except WebSocketDisconnect:
            pass

    @router.websocket("/ws/time")
    async def time_handler(ws: WebSocketConnection):
        await ws.accept()
        await ws.send_text("current_time_placeholder")
        await ws.close()

    print(f"  Registered routes: {router.routes}")
    assert len(router.routes) == 2
    assert router.get_handler("/ws/echo") is echo_handler
    assert router.get_handler("/ws/time") is time_handler
    assert router.get_handler("/ws/missing") is None
    print("  Handler lookup works")

    # Test echo handler
    transport = MockASGITransport()
    scope = {"type": "websocket", "path": "/ws/echo", "client_id": "test"}
    ws = WebSocketConnection(scope, transport.receive, transport.send)

    async def run_echo():
        await echo_handler(ws)

    task = asyncio.create_task(run_echo())
    await transport.client_connect()
    accept = await transport.get_server_message()
    assert accept["type"] == "websocket.accept"

    await transport.client_send_text("hello")
    reply = await transport.get_server_message()
    assert reply["text"] == "echo: hello"
    print(f"  Echo handler: 'hello' -> '{reply['text']}'")

    await transport.client_disconnect()
    await task

    print("  [PASS] WebSocket router works")


async def demo_ignite_app():
    """Demonstrate the Ignite app with WebSocket support."""
    print("\n--- Section 3: Ignite App ---")

    app = IgniteApp()

    @app.websocket("/ws/chat")
    async def chat_handler(ws: WebSocketConnection):
        await app.connection_manager.connect(ws)
        try:
            while True:
                text = await ws.receive_text()
                await app.connection_manager.broadcast(
                    f"[{ws.client_id}]: {text}"
                )
        except WebSocketDisconnect:
            app.connection_manager.disconnect(ws)

    # Simulate 2 clients connecting to chat
    transports = []
    for i in range(2):
        t = MockASGITransport()
        scope = {
            "type": "websocket",
            "path": "/ws/chat",
            "client_id": f"alice" if i == 0 else "bob",
        }
        transports.append((t, scope))

    tasks = []
    for t, scope in transports:
        await t.client_connect()
        task = asyncio.create_task(
            app.handle_websocket(scope, t.receive, t.send)
        )
        tasks.append(task)

    # Consume accept messages
    for t, _ in transports:
        msg = await t.get_server_message()
        assert msg["type"] == "websocket.accept"

    assert app.connection_manager.active_count == 2
    print(f"  Clients connected: {app.connection_manager.client_ids}")

    # Alice sends a message
    await transports[0][0].client_send_text("Hello everyone!")
    for t, _ in transports:
        msg = await t.get_server_message()
        assert msg["text"] == "[alice]: Hello everyone!"
    print("  Alice sent: 'Hello everyone!' -> broadcast to 2 clients")

    # Bob sends a message
    await transports[1][0].client_send_text("Hi Alice!")
    for t, _ in transports:
        msg = await t.get_server_message()
        assert msg["text"] == "[bob]: Hi Alice!"
    print("  Bob sent: 'Hi Alice!' -> broadcast to 2 clients")

    # Alice disconnects
    await transports[0][0].client_disconnect()
    await asyncio.sleep(0.01)

    assert app.connection_manager.active_count == 1
    print(f"  Alice disconnected. Active: {app.connection_manager.client_ids}")

    # Bob disconnects
    await transports[1][0].client_disconnect()
    await asyncio.sleep(0.01)

    for task in tasks:
        await task

    print("  [PASS] Ignite app with WebSocket works")


async def demo_rejected_connection():
    """Show what happens with an unregistered WebSocket path."""
    print("\n--- Section 4: Rejected Connection ---")

    app = IgniteApp()

    transport = MockASGITransport()
    scope = {"type": "websocket", "path": "/ws/unknown", "client_id": "x"}

    await transport.client_connect()
    await app.handle_websocket(scope, transport.receive, transport.send)

    msg = await transport.get_server_message()
    assert msg["type"] == "websocket.close"
    assert msg["code"] == 4004
    print(f"  Unregistered path /ws/unknown: closed with code {msg['code']}")

    print("  [PASS] Rejected connection works")


async def demo_broadcast_json():
    """Demonstrate JSON broadcasting."""
    print("\n--- Section 5: JSON Broadcasting ---")

    manager = ConnectionManager()

    transports = []
    for i in range(3):
        t = MockASGITransport()
        scope = {"type": "websocket", "path": "/ws", "client_id": f"c{i}"}
        ws = WebSocketConnection(scope, t.receive, t.send)
        await t.client_connect()
        await manager.connect(ws)
        _ = await t.get_server_message()  # consume accept
        transports.append(t)

    # Broadcast JSON
    data = {"event": "notification", "payload": {"msg": "System update"}}
    count = await manager.broadcast_json(data)
    assert count == 3

    for t in transports:
        msg = await t.get_server_message()
        parsed = json.loads(msg["text"])
        assert parsed == data
    print(f"  Broadcast JSON to {count} clients: {data}")

    # Send JSON to specific client
    sent = await manager.send_json_to("c1", {"private": True})
    assert sent
    msg = await transports[1].get_server_message()
    parsed = json.loads(msg["text"])
    assert parsed == {"private": True}
    print(f"  Sent JSON to c1: {parsed}")

    print("  [PASS] JSON broadcasting works")


async def demo_chat_room():
    """Simulate a mini chat room scenario."""
    print("\n--- Section 6: Chat Room Simulation ---")

    app = IgniteApp()
    manager = app.connection_manager

    @app.websocket("/ws/room")
    async def room_handler(ws: WebSocketConnection):
        await manager.connect(ws)
        # Announce join
        await manager.broadcast(f"** {ws.client_id} joined **")
        try:
            while True:
                text = await ws.receive_text()
                await manager.broadcast(f"{ws.client_id}: {text}")
        except WebSocketDisconnect:
            manager.disconnect(ws)
            await manager.broadcast(f"** {ws.client_id} left **")

    # 3 users join
    users = ["Alice", "Bob", "Charlie"]
    transports = []
    tasks = []

    for name in users:
        t = MockASGITransport()
        scope = {"type": "websocket", "path": "/ws/room", "client_id": name}
        await t.client_connect()
        task = asyncio.create_task(
            app.handle_websocket(scope, t.receive, t.send)
        )
        tasks.append(task)
        transports.append(t)

        # Consume accept
        msg = await t.get_server_message()
        assert msg["type"] == "websocket.accept"

        # Consume join messages for all currently connected users
        for prev_t in transports:
            msg = await prev_t.get_server_message()
            assert f"{name} joined" in msg["text"]

    print(f"  Users connected: {manager.client_ids}")
    assert manager.active_count == 3

    # Alice says something
    await transports[0].client_send_text("Hey!")
    for t in transports:
        msg = await t.get_server_message()
        assert msg["text"] == "Alice: Hey!"
    print("  Alice: Hey! -> broadcast to 3")

    # Bob leaves
    await transports[1].client_disconnect()
    await asyncio.sleep(0.01)

    # Remaining users see the leave message
    for t in [transports[0], transports[2]]:
        msg = await t.get_server_message()
        assert "Bob left" in msg["text"]
    print("  Bob left -> 2 users notified")

    assert manager.active_count == 2

    # Clean up
    await transports[0].client_disconnect()
    await transports[2].client_disconnect()
    await asyncio.sleep(0.01)
    for task in tasks:
        await task

    print("  [PASS] Chat room simulation works")


async def _run_with_timeout(coro, label):
    """Run a coroutine with a 3-second timeout; print friendly message on failure."""
    try:
        await asyncio.wait_for(coro, timeout=3.0)
    except asyncio.TimeoutError:
        print(f"  ❌ Not yet implemented: {label} timed out (stubs not returning data)")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


async def async_main():
    await _run_with_timeout(demo_connection_manager(), "demo_connection_manager")
    await _run_with_timeout(demo_websocket_router(), "demo_websocket_router")
    await _run_with_timeout(demo_ignite_app(), "demo_ignite_app")
    await _run_with_timeout(demo_rejected_connection(), "demo_rejected_connection")
    await _run_with_timeout(demo_broadcast_json(), "demo_broadcast_json")
    await _run_with_timeout(demo_chat_room(), "demo_chat_room")


def main():
    asyncio.run(async_main())

    print("\n--- Summary ---")
    print("WebSocket routes & handlers implementation covers:")
    print("  - ConnectionManager: track, send, broadcast, disconnect")
    print("  - WebSocketRouter with @router.websocket() decorator")
    print("  - IgniteApp with @app.websocket() support")
    print("  - Broadcast to all, broadcast except sender")
    print("  - JSON message broadcasting")
    print("  - Rejected connections for unregistered paths")
    print("  - Chat room simulation with join/leave notifications")
    print("\nImplement the TODOs above to make all 6 sections pass!")
    print("Next up: Kata 61 -- PubSub system!")


if __name__ == "__main__":
    main()
