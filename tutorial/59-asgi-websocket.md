# Kata 59 -- ASGI WebSocket

[prev: 58-websocket-protocol](./58-websocket-protocol.md) | [next: 60-websocket-routes](./60-websocket-routes.md)

---

## What We're Building

The **ASGI WebSocket interface** -- the standard Python async protocol for handling WebSocket connections. While Kata 58 dealt with raw bytes and frame parsing, ASGI abstracts that away into a clean message-passing interface:

1. **WebSocket scope** -- the connection metadata dict with `type="websocket"`
2. **Message lifecycle** -- connect, accept, receive, send, disconnect events
3. **WebSocketConnection class** -- a high-level wrapper that provides `accept()`, `receive_text()`, `send_json()`, and `close()`

This is exactly how Starlette and FastAPI handle WebSocket connections internally.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| WebSocket scope | Dict with connection metadata (path, headers, etc.) | Connection setup |
| `websocket.connect` | Client wants to connect | Trigger accept/reject |
| `websocket.accept` | Server accepts the connection | After connect event |
| `websocket.receive` | Client sent a message (text or bytes) | Reading messages |
| `websocket.send` | Server sends a message | Writing messages |
| `websocket.disconnect` | Client disconnected | Cleanup |
| `websocket.close` | Server closes connection | Graceful shutdown |
| Connection state | CONNECTING -> CONNECTED -> DISCONNECTED | State machine |

## The Code

### 1. WebSocket Scope

```python
scope = {
    "type": "websocket",
    "asgi": {"version": "3.0"},
    "path": "/ws/chat",
    "query_string": b"room=general",
    "headers": [(b"host", b"example.com")],
    "subprotocols": ["graphql-ws"],
}
```

Unlike HTTP scopes (which have a method), WebSocket scopes have no method -- the connection type is always bidirectional.

### 2. The ASGI Lifecycle

```python
async def websocket_app(scope, receive, send):
    # 1. Wait for connection
    event = await receive()  # {"type": "websocket.connect"}

    # 2. Accept
    await send({"type": "websocket.accept"})

    # 3. Message loop
    while True:
        message = await receive()
        if message["type"] == "websocket.disconnect":
            break
        text = message.get("text", "")
        await send({"type": "websocket.send", "text": f"echo: {text}"})
```

### 3. WebSocketConnection Wrapper

```python
class WebSocketConnection:
    async def accept(self):
        message = await self._receive()
        assert message["type"] == "websocket.connect"
        await self._send({"type": "websocket.accept"})
        self.state = "connected"

    async def receive_text(self) -> str:
        message = await self._receive()
        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(message.get("code", 1000))
        return message.get("text", "")

    async def send_text(self, text: str):
        await self._send({"type": "websocket.send", "text": text})

    async def close(self, code=1000):
        await self._send({"type": "websocket.close", "code": code})
```

### 4. Mock Transport for Testing

```python
class MockASGITransport:
    def __init__(self):
        self.client_queue = asyncio.Queue()  # client -> server
        self.server_queue = asyncio.Queue()  # server -> client

    async def receive(self):
        return await self.client_queue.get()

    async def send(self, message):
        await self.server_queue.put(message)
```

## Playground

```
python playground/59_asgi_websocket.py
```

Expected output:

```
--- Section 1: WebSocket Scope ---
  type: websocket
  path: /ws/chat
  query: b'room=general'
  subprotocols: ['graphql-ws']
  [PASS] WebSocket scope works

--- Section 2: Message Types ---
  websocket.connect
  websocket.accept
  websocket.receive, text='hello'
  ...
  [PASS] Message types correct

--- Section 3: Raw ASGI App ---
  Server: websocket.accept
  Client: 'Hello' -> Server: 'echo: Hello'
  Client: 'World' -> Server: 'echo: World'
  [PASS] Raw ASGI app works

--- Section 4: WebSocketConnection ---
  State after accept: connected
  Received text: 'Hi there'
  Sent text: 'Hello back!'
  Received JSON: {'action': 'ping'}
  Sent JSON: {"action": "pong"}
  State after close: disconnected
  [PASS] WebSocketConnection works

--- Section 5: Disconnect Handling ---
  Caught disconnect: code=1001
  Send after disconnect: Cannot send: state is disconnected
  [PASS] Disconnect handling works

--- Section 6: Binary Messages ---
  Received 256 bytes of binary data
  Sent binary: deadbeef
  [PASS] Binary messages work

All 6 sections passed. ASGI WebSocket mastered!
```

## How It Works

### Connection State Machine

```
                  client_connect
  CONNECTING  ─────────────────────>  receive: {"type": "websocket.connect"}
      |
      |  accept()
      v
  CONNECTED   <────────────────────>  send/receive messages
      |
      |  close() or disconnect
      v
  DISCONNECTED
```

### Message Flow

```
Client (browser)              ASGI App (Python)
     |                              |
     |  -- connect event -->        |
     |                       receive() -> {"type": "websocket.connect"}
     |                              |
     |  <-- accept event --        |
     |                       send({"type": "websocket.accept"})
     |                              |
     |  -- text message -->        |
     |                       receive() -> {"type": "websocket.receive",
     |                                      "text": "hello"}
     |                              |
     |  <-- text message --        |
     |                       send({"type": "websocket.send",
     |                              "text": "echo: hello"})
     |                              |
     |  -- disconnect -->          |
     |                       receive() -> {"type": "websocket.disconnect",
     |                                      "code": 1000}
```

### ASGI Message Types Summary

| Direction | Message Type | Key Fields |
|---|---|---|
| Client -> Server | `websocket.connect` | _(none)_ |
| Server -> Client | `websocket.accept` | `subprotocol`, `headers` |
| Client -> Server | `websocket.receive` | `text` or `bytes` |
| Server -> Client | `websocket.send` | `text` or `bytes` |
| Client -> Server | `websocket.disconnect` | `code` |
| Server -> Client | `websocket.close` | `code`, `reason` |

## Exercises

1. **Add subprotocol negotiation** -- when accepting, check if the client's requested subprotocols (from scope) include one the server supports. Accept with the matching subprotocol.

2. **Implement receive timeout** -- add a `receive_text(timeout=5.0)` parameter that raises `asyncio.TimeoutError` if no message arrives within the timeout.

3. **Build a WebSocket middleware** -- create a middleware that wraps WebSocket connections to log all sent/received messages with timestamps.

4. **Add message size limits** -- reject messages larger than a configurable maximum (e.g., 64KB) by closing the connection with code 1009 (Message Too Big).

5. **Build a connection pool** -- create a `WebSocketPool` that limits the total number of concurrent WebSocket connections and queues excess connections.

## What's Next

With the ASGI WebSocket interface built, in [Kata 60: WebSocket Routes & Handlers](./60-websocket-routes.md) we'll add WebSocket routing to our Ignite framework -- `@app.websocket("/ws")` decorators, a ConnectionManager for tracking clients, and broadcasting support.

---

[prev: 58-websocket-protocol](./58-websocket-protocol.md) | [next: 60-websocket-routes](./60-websocket-routes.md)
