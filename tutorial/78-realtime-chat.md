# Kata 78 -- Real-Time Chat (Capstone 2)

[prev: 77-todo-api](./77-todo-api.md) | next: none

---

## What We're Building

A **real-time chat system** -- our final capstone project that combines HTTP routes with WebSocket communication. This is the most complex kata, bringing together everything we've built:

- **Chat rooms** -- create and list rooms via HTTP
- **User presence** -- join/leave notifications, member tracking
- **Message history** -- stored in SQLite, replayed when users join
- **WebSocket broadcasting** -- messages sent to all room members in real-time
- **Room isolation** -- messages stay in their room

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Chat room model | Room with ID, name, creator | Multi-room chat systems |
| Message store | SQLite persistence for messages | History and replay |
| Presence manager | Track who is in which room | Online status, notifications |
| WebSocket simulation | Send/receive without a real server | Testing real-time features |
| Broadcasting | Send to all connected clients | Real-time updates |
| Join/leave events | System messages for room changes | Activity tracking |
| Room isolation | Messages scoped to a room | Multi-channel systems |
| History replay | Send recent messages to new joiners | Context for newcomers |

## The Code

### 1. Message Store

```python
class MessageStore:
    def save_message(self, room_id, username, content, msg_type="message"):
        cursor = self.conn.execute(
            "INSERT INTO messages (...) VALUES (?, ?, ?, ?, ?)",
            (room_id, username, content, time.time(), msg_type))
        return ChatMessage(id=cursor.lastrowid, ...)

    def get_history(self, room_id, limit=50):
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE room_id = ? "
            "ORDER BY timestamp DESC LIMIT ?", (room_id, limit))
        return [ChatMessage(...) for r in reversed(rows)]
```

### 2. Presence Manager

```python
class PresenceManager:
    def __init__(self):
        self._rooms = defaultdict(set)  # room_id -> {usernames}

    def join(self, room_id, username):
        if username in self._rooms[room_id]:
            return False  # Already in room
        self._rooms[room_id].add(username)
        return True

    def leave(self, room_id, username):
        self._rooms[room_id].discard(username)
        return True
```

### 3. WebSocket Broadcasting

```python
class WebSocketBroadcaster:
    def broadcast(self, room_id, data, exclude=None):
        count = 0
        for ws in self._connections[room_id]:
            if ws is not exclude and ws.connected:
                ws.send(data)
                count += 1
        return count
```

### 4. Chat Server

```python
class ChatServer:
    def handle_join(self, room_id, ws):
        self.presence.join(room_id, ws.username)
        self.broadcaster.connect(room_id, ws)
        msg = self.store.save_message(room_id, ws.username, "joined", "join")
        self.broadcaster.broadcast(room_id, {"type": "join", ...}, exclude=ws)
        ws.send({"type": "room_info", "members": ..., "history": ...})

    def handle_message(self, room_id, ws, content):
        msg = self.store.save_message(room_id, ws.username, content)
        self.broadcaster.broadcast(room_id, {"type": "message", ...})

    def handle_leave(self, room_id, ws):
        self.presence.leave(room_id, ws.username)
        self.broadcaster.disconnect(room_id, ws)
        self.broadcaster.broadcast(room_id, {"type": "leave", ...})
```

## Playground

```bash
python playground/78_realtime_chat.py
```

Expected output:

```
--- Section 1: Message Store ---
  Created rooms: general, random
  History: 3 messages
    [alice]: Hello everyone!
    [bob]: Hi Alice!
    [alice]: How's it going?
  [PASS] Message store works

--- Section 2: Presence Manager ---
  Members: ['alice', 'bob']
  After bob leaves: ['alice']
  [PASS] Presence manager works

--- Section 3: WebSocket Broadcaster ---
  Broadcast to all: 3 clients
  Broadcast excluding sender: 2 clients
  [PASS] WebSocket broadcaster works

--- Section 4-8: HTTP, WebSocket, Rooms, Full Scenario ---
  [PASS] All sections pass

Congratulations! You've completed all 78 Python Katas
and built the Ignite framework from scratch!
```

## How It Works

### System Architecture

```
                         ChatServer
                    +-------------------+
                    |                   |
HTTP Endpoints      |   WebSocket       |
                    |   Handlers        |
GET  /rooms ------->|                   |
POST /rooms ------->|  handle_join()    |<---- WS connect
GET  /history ----->|  handle_message() |<---- WS message
                    |  handle_leave()   |<---- WS disconnect
                    |                   |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
        MessageStore   PresenceManager  Broadcaster
        (SQLite)       (room->users)   (room->websockets)
              |              |              |
        Persistent     In-memory       In-memory
        History        Membership      Connections
```

### Message Flow

```
Alice sends "Hello!" in #general

1. ChatServer.handle_message("general", ws_alice, "Hello!")
2. MessageStore.save_message("general", "alice", "Hello!")
   -> INSERT INTO messages ...
   -> ChatMessage(id=42, ...)
3. Broadcaster.broadcast("general", {"type": "message", ...})
   -> ws_alice.send(data)  -- sender gets it too
   -> ws_bob.send(data)    -- all room members
   -> ws_charlie.send(data)
```

### Join Flow

```
Charlie joins #general

1. PresenceManager.join("general", "charlie") -> True (new)
2. Broadcaster.connect("general", ws_charlie)
3. MessageStore.save_message(..., "charlie joined", type="join")
4. Broadcaster.broadcast(..., exclude=ws_charlie)
   -> Alice and Bob see "charlie joined the room"
5. ws_charlie.send({
     "type": "room_info",
     "members": ["alice", "bob", "charlie"],
     "history": [... last 20 messages ...]
   })
```

## Exercises

1. **Add typing indicators** -- when a user starts typing, broadcast a `{"type": "typing", "username": "alice"}` event to other room members. Clear after a timeout.

2. **Add private messages** -- support direct messages between users that aren't in any room. Store them in a separate table.

3. **Add message editing and deletion** -- support `handle_edit(room_id, ws, message_id, new_content)` and `handle_delete(room_id, ws, message_id)` with appropriate broadcast events.

4. **Add room permissions** -- implement roles (owner, admin, member) with different capabilities. Only owners can delete rooms, admins can kick users.

5. **Add message reactions** -- allow users to react to messages with emoji reactions. Broadcast reaction events to the room.

## What's Next

Congratulations! You've completed all 78 Python Katas and built the Ignite framework from scratch!

Here's what you've accomplished across the full kata series:

- **Modules 1-4**: Python fundamentals -- types, functions, OOP, data structures
- **Modules 5-7**: Advanced Python -- iterators, generators, decorators, context managers, descriptors, metaclasses
- **Modules 8-9**: Concurrency -- asyncio, threading, multiprocessing
- **Module 10**: Web framework foundations -- HTTP parsing, routing, ASGI, middleware, dependency injection, request validation, response models, error handling, route decorators, templating
- **Module 11**: Production features -- health checks, rate limiting, background tasks, testing utilities
- **Module 12**: Capstones -- a full CRUD Todo API and a real-time chat system

You've gone from Python basics to building a production-ready web framework. The patterns you've learned -- dependency injection, middleware pipelines, repository pattern, pub/sub broadcasting -- are the same patterns used in FastAPI, Django, Flask, and every major web framework.

Keep building. Keep learning. The best way to master programming is to build things that matter to you.

---

[prev: 77-todo-api](./77-todo-api.md) | next: none
