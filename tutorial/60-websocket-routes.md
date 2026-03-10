# Kata 60 -- WebSocket Routes & Handlers

[prev: 59-asgi-websocket](./59-asgi-websocket.md) | [next: 61-pubsub](./61-pubsub.md)

---

## What We're Building

**WebSocket routing and connection management** for our Ignite framework. While Kata 59 handled a single WebSocket connection, real applications need to manage many clients simultaneously:

1. **`@app.websocket()` decorator** -- register WebSocket handlers by path, just like HTTP routes
2. **ConnectionManager** -- track active connections, send to specific clients, broadcast to all
3. **Chat room simulation** -- a complete multi-user scenario with join/leave notifications

This is the pattern used by Starlette, FastAPI, and channels -- a WebSocket router paired with a connection manager.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `@app.websocket("/ws")` | Register WebSocket handler for a path | Route WebSocket connections |
| `ConnectionManager` | Track all active connections | Multi-client apps |
| `send_to(id, msg)` | Send to a specific client | Private messages |
| `broadcast(msg)` | Send to all connected clients | Notifications, chat |
| `broadcast_except(msg, id)` | Send to all except one | Relay sender's message |
| Connection rejection | Close with code 4004 for unknown paths | Security |
| JSON broadcasting | Send structured data to all clients | API-style WebSocket |

## The Code

### 1. ConnectionManager

```python
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocketConnection] = {}

    async def connect(self, ws):
        await ws.accept()
        self._connections[ws.client_id] = ws

    def disconnect(self, ws):
        self._connections.pop(ws.client_id, None)

    async def send_to(self, client_id, message):
        ws = self._connections.get(client_id)
        if ws and ws.state == "connected":
            await ws.send_text(message)
            return True
        return False

    async def broadcast(self, message):
        sent = 0
        for ws in self._connections.values():
            if ws.state == "connected":
                await ws.send_text(message)
                sent += 1
        return sent

    async def broadcast_except(self, message, exclude_id):
        sent = 0
        for cid, ws in self._connections.items():
            if cid != exclude_id and ws.state == "connected":
                await ws.send_text(message)
                sent += 1
        return sent
```

### 2. WebSocket Router

```python
class WebSocketRouter:
    def __init__(self):
        self._routes = {}

    def websocket(self, path):
        def decorator(func):
            self._routes[path] = func
            return func
        return decorator

    def get_handler(self, path):
        return self._routes.get(path)
```

### 3. Ignite App Integration

```python
class IgniteApp:
    def __init__(self):
        self._ws_router = WebSocketRouter()
        self.connection_manager = ConnectionManager()

    def websocket(self, path):
        return self._ws_router.websocket(path)

    async def handle_websocket(self, scope, receive, send):
        path = scope["path"]
        handler = self._ws_router.get_handler(path)
        if handler is None:
            await receive()  # consume connect
            await send({"type": "websocket.close", "code": 4004})
            return
        ws = WebSocketConnection(scope, receive, send)
        await handler(ws)
```

### 4. Chat Room Handler

```python
@app.websocket("/ws/room")
async def room_handler(ws):
    await manager.connect(ws)
    await manager.broadcast(f"** {ws.client_id} joined **")
    try:
        while True:
            text = await ws.receive_text()
            await manager.broadcast(f"{ws.client_id}: {text}")
    except WebSocketDisconnect:
        manager.disconnect(ws)
        await manager.broadcast(f"** {ws.client_id} left **")
```

## Playground

```
python playground/60_websocket_routes.py
```

Expected output:

```
--- Section 1: ConnectionManager ---
  Connected: ['user_0', 'user_1', 'user_2']
  Send to user_1: 'Hello user_1!'
  Send to user_99: not found (returned False)
  Broadcast to 3 clients
  Broadcast except user_0: sent to 2 clients
  After disconnect: ['user_0', 'user_1']
  [PASS] ConnectionManager works

--- Section 2: WebSocket Router ---
  Registered routes: ['/ws/echo', '/ws/time']
  Handler lookup works
  Echo handler: 'hello' -> 'echo: hello'
  [PASS] WebSocket router works

--- Section 3: Ignite App ---
  Clients connected: ['alice', 'bob']
  Alice sent: 'Hello everyone!' -> broadcast to 2 clients
  Bob sent: 'Hi Alice!' -> broadcast to 2 clients
  Alice disconnected. Active: ['bob']
  [PASS] Ignite app with WebSocket works

--- Section 4: Rejected Connection ---
  Unregistered path /ws/unknown: closed with code 4004
  [PASS] Rejected connection works

--- Section 5: JSON Broadcasting ---
  Broadcast JSON to 3 clients: {'event': 'notification', ...}
  Sent JSON to c1: {'private': True}
  [PASS] JSON broadcasting works

--- Section 6: Chat Room Simulation ---
  Users connected: ['Alice', 'Bob', 'Charlie']
  Alice: Hey! -> broadcast to 3
  Bob left -> 2 users notified
  [PASS] Chat room simulation works

All 6 sections passed. WebSocket routes & handlers mastered!
```

## How It Works

### Connection Lifecycle

```
Client A          Server                    Client B
   |                 |                         |
   | -- connect -->  |                         |
   |                 | manager.connect(A)      |
   |                 | broadcast("A joined")   |
   | <-- "A joined"  |  "A joined" -->         |
   |                 |                         |
   | -- "Hello" -->  |                         |
   |                 | broadcast("A: Hello")   |
   | <-- "A: Hello"  |  "A: Hello" -->         |
   |                 |                         |
   | -- disconnect   |                         |
   |                 | manager.disconnect(A)   |
   |                 | broadcast("A left")     |
   |                 |  "A left" -->            |
```

### Route Matching

```
Incoming WebSocket connection to /ws/chat

  WebSocketRouter._routes:
    "/ws/echo"  -> echo_handler
    "/ws/chat"  -> chat_handler     <-- match!
    "/ws/time"  -> time_handler

  Result: call chat_handler(ws)
```

### Connection Manager State

```
After 3 connections:
  _connections = {
    "alice":   WebSocketConnection(state=CONNECTED),
    "bob":     WebSocketConnection(state=CONNECTED),
    "charlie": WebSocketConnection(state=CONNECTED),
  }

broadcast("Hello") -> sends to alice, bob, charlie (3)
broadcast_except("Hello", "alice") -> sends to bob, charlie (2)
send_to("bob", "Private") -> sends only to bob (1)
disconnect(charlie) -> removes from dict (2 remaining)
```

## Exercises

1. **Add room support** -- extend ConnectionManager to support named rooms. `manager.join_room(ws, "general")`, `manager.broadcast_to_room("general", msg)`. Track which clients are in which rooms.

2. **Implement rate limiting** -- add a rate limiter to the WebSocket handler that limits each client to N messages per second. Close the connection with code 1008 (Policy Violation) if exceeded.

3. **Add authentication** -- check a token in the WebSocket query string or headers during the accept phase. Reject unauthenticated connections with a close code.

4. **Build a presence system** -- track which users are online and broadcast presence updates (join/leave) to all connected clients. Add a `/ws/presence` endpoint that streams presence events.

5. **Implement heartbeat** -- add a ping/pong mechanism where the server periodically pings clients and disconnects those that don't respond within a timeout.

## What's Next

With WebSocket routing and connection management in place, in [Kata 61: PubSub System](./61-pubsub.md) we'll build a topic-based publish/subscribe system that integrates with WebSocket connections for real-time messaging with pattern matching.

---

[prev: 59-asgi-websocket](./59-asgi-websocket.md) | [next: 61-pubsub](./61-pubsub.md)
