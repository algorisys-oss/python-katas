"""
Kata 78 -- Real-Time Chat (Capstone 2)
Run: python playground/78_realtime_chat.py

Build a real-time chat system: chat rooms, user presence (join/leave),
message history in SQLite, WebSocket message broadcasting within rooms.
Combines HTTP routes (create room, get history) with WebSocket routes
(real-time messaging). All simulated without an actual server.

Completes within 5 seconds.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Message and Room Models
# ===========================================================================

@dataclass
class ChatMessage:
    """A message in a chat room."""
    id: int
    room_id: str
    username: str
    content: str
    timestamp: float
    msg_type: str = "message"  # "message", "join", "leave"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "username": self.username,
            "content": self.content,
            "timestamp": self.timestamp,
            "type": self.msg_type,
        }


@dataclass
class ChatRoom:
    """A chat room with metadata."""
    id: str
    name: str
    created_at: float
    created_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }


# ===========================================================================
# SECTION 2: Message Store (SQLite)
# ===========================================================================
# Persists chat messages so users can see history when they join a room.

class MessageStore:
    """SQLite-backed message storage."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at REAL NOT NULL,
                created_by TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                msg_type TEXT DEFAULT 'message',
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            );
        """)
        self.conn.commit()

    def create_room(self, room_id: str, name: str, created_by: str) -> ChatRoom:
        """Create a new chat room."""
        now = time.time()
        self.conn.execute(
            "INSERT INTO rooms (id, name, created_at, created_by) VALUES (?, ?, ?, ?)",
            (room_id, name, now, created_by),
        )
        self.conn.commit()
        return ChatRoom(id=room_id, name=name, created_at=now, created_by=created_by)

    def get_room(self, room_id: str) -> ChatRoom | None:
        row = self.conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if row is None:
            return None
        return ChatRoom(id=row["id"], name=row["name"],
                       created_at=row["created_at"], created_by=row["created_by"])

    def list_rooms(self) -> list[ChatRoom]:
        rows = self.conn.execute("SELECT * FROM rooms ORDER BY created_at").fetchall()
        return [
            ChatRoom(id=r["id"], name=r["name"],
                    created_at=r["created_at"], created_by=r["created_by"])
            for r in rows
        ]

    def save_message(
        self,
        room_id: str,
        username: str,
        content: str,
        msg_type: str = "message",
    ) -> ChatMessage:
        """Save a message to the store."""
        now = time.time()
        cursor = self.conn.execute(
            "INSERT INTO messages (room_id, username, content, timestamp, msg_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (room_id, username, content, now, msg_type),
        )
        self.conn.commit()
        return ChatMessage(
            id=cursor.lastrowid, room_id=room_id, username=username,
            content=content, timestamp=now, msg_type=msg_type,
        )

    def get_history(self, room_id: str, limit: int = 50) -> list[ChatMessage]:
        """Get recent messages for a room."""
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE room_id = ? ORDER BY timestamp DESC LIMIT ?",
            (room_id, limit),
        ).fetchall()
        messages = [
            ChatMessage(
                id=r["id"], room_id=r["room_id"], username=r["username"],
                content=r["content"], timestamp=r["timestamp"],
                msg_type=r["msg_type"],
            )
            for r in reversed(rows)  # Return in chronological order
        ]
        return messages


# ===========================================================================
# SECTION 3: Presence Manager
# ===========================================================================
# Tracks which users are in which rooms. Generates join/leave events.

class PresenceManager:
    """Tracks user presence in chat rooms."""

    def __init__(self):
        # room_id -> set of usernames
        self._rooms: dict[str, set[str]] = defaultdict(set)

    def join(self, room_id: str, username: str) -> bool:
        """User joins a room. Returns True if this is a new join."""
        if username in self._rooms[room_id]:
            return False  # Already in room
        self._rooms[room_id].add(username)
        return True

    def leave(self, room_id: str, username: str) -> bool:
        """User leaves a room. Returns True if they were in the room."""
        if username not in self._rooms[room_id]:
            return False
        self._rooms[room_id].discard(username)
        if not self._rooms[room_id]:
            del self._rooms[room_id]
        return True

    def get_members(self, room_id: str) -> list[str]:
        """Get sorted list of users in a room."""
        return sorted(self._rooms.get(room_id, set()))

    def get_room_count(self, room_id: str) -> int:
        return len(self._rooms.get(room_id, set()))

    def is_in_room(self, room_id: str, username: str) -> bool:
        return username in self._rooms.get(room_id, set())


# ===========================================================================
# SECTION 4: WebSocket Simulation
# ===========================================================================
# Since we can't run a real WebSocket server in a standalone script, we
# simulate the WebSocket connection and message broadcasting.

@dataclass
class WebSocketMessage:
    """A message sent or received over a WebSocket."""
    type: str  # "send", "receive", "connect", "disconnect"
    data: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.data)


class SimulatedWebSocket:
    """Simulates a WebSocket connection for testing.

    Collects messages that would be sent to the client.
    """

    def __init__(self, username: str):
        self.username = username
        self.sent_messages: list[dict[str, Any]] = []
        self.connected = True

    def send(self, data: dict[str, Any]) -> None:
        """Simulate sending a message to this client."""
        if self.connected:
            self.sent_messages.append(data)

    def disconnect(self) -> None:
        self.connected = False


class WebSocketBroadcaster:
    """Broadcasts messages to all connected WebSocket clients in a room."""

    def __init__(self):
        # room_id -> list of SimulatedWebSocket
        self._connections: dict[str, list[SimulatedWebSocket]] = defaultdict(list)

    def connect(self, room_id: str, ws: SimulatedWebSocket) -> None:
        """Register a WebSocket connection for a room."""
        self._connections[room_id].append(ws)

    def disconnect(self, room_id: str, ws: SimulatedWebSocket) -> None:
        """Remove a WebSocket connection."""
        if room_id in self._connections:
            self._connections[room_id] = [
                c for c in self._connections[room_id] if c is not ws
            ]
            if not self._connections[room_id]:
                del self._connections[room_id]

    def broadcast(self, room_id: str, data: dict[str, Any],
                  exclude: SimulatedWebSocket | None = None) -> int:
        """Broadcast a message to all clients in a room.

        Args:
            room_id: The room to broadcast to.
            data: The message data.
            exclude: Optional WebSocket to exclude (the sender).

        Returns:
            Number of clients the message was sent to.
        """
        count = 0
        for ws in self._connections.get(room_id, []):
            if ws is not exclude and ws.connected:
                ws.send(data)
                count += 1
        return count

    def get_connection_count(self, room_id: str) -> int:
        return len(self._connections.get(room_id, []))


# ===========================================================================
# SECTION 5: Chat Server
# ===========================================================================
# The ChatServer ties together the message store, presence manager,
# broadcaster, and provides both HTTP and WebSocket handlers.

class ChatServer:
    """Real-time chat server combining HTTP and WebSocket handlers."""

    def __init__(self, db_path: str = ":memory:"):
        self.store = MessageStore(db_path)
        self.presence = PresenceManager()
        self.broadcaster = WebSocketBroadcaster()

    # -- HTTP Handlers --

    def create_room(self, room_id: str, name: str, created_by: str) -> dict:
        """HTTP: Create a new chat room."""
        existing = self.store.get_room(room_id)
        if existing:
            return {"error": f"Room '{room_id}' already exists"}
        room = self.store.create_room(room_id, name, created_by)
        return {"room": room.to_dict()}

    def list_rooms(self) -> dict:
        """HTTP: List all chat rooms with member counts."""
        rooms = self.store.list_rooms()
        return {
            "rooms": [
                {
                    **room.to_dict(),
                    "members": self.presence.get_room_count(room.id),
                }
                for room in rooms
            ]
        }

    def get_history(self, room_id: str, limit: int = 50) -> dict:
        """HTTP: Get message history for a room."""
        room = self.store.get_room(room_id)
        if room is None:
            return {"error": f"Room '{room_id}' not found"}
        messages = self.store.get_history(room_id, limit)
        return {
            "room": room.to_dict(),
            "messages": [m.to_dict() for m in messages],
            "count": len(messages),
        }

    # -- WebSocket Handlers --

    def handle_join(self, room_id: str, ws: SimulatedWebSocket) -> dict:
        """WebSocket: User joins a room."""
        room = self.store.get_room(room_id)
        if room is None:
            return {"error": f"Room '{room_id}' not found"}

        is_new = self.presence.join(room_id, ws.username)
        self.broadcaster.connect(room_id, ws)

        if is_new:
            # Save join message to history
            msg = self.store.save_message(
                room_id, ws.username,
                f"{ws.username} joined the room",
                msg_type="join",
            )
            # Broadcast join notification to others
            self.broadcaster.broadcast(
                room_id,
                {"type": "join", "username": ws.username, "message": msg.to_dict()},
                exclude=ws,
            )
            # Send room info to the joiner
            ws.send({
                "type": "room_info",
                "room": room.to_dict(),
                "members": self.presence.get_members(room_id),
                "history": [m.to_dict() for m in self.store.get_history(room_id, 20)],
            })

        return {"joined": room_id, "username": ws.username, "is_new": is_new}

    def handle_message(self, room_id: str, ws: SimulatedWebSocket,
                       content: str) -> dict:
        """WebSocket: User sends a message."""
        if not self.presence.is_in_room(room_id, ws.username):
            return {"error": "Not in room"}

        # Save to history
        msg = self.store.save_message(room_id, ws.username, content)

        # Broadcast to all in room (including sender)
        msg_data = {"type": "message", "message": msg.to_dict()}
        self.broadcaster.broadcast(room_id, msg_data)

        return {"sent": True, "message": msg.to_dict()}

    def handle_leave(self, room_id: str, ws: SimulatedWebSocket) -> dict:
        """WebSocket: User leaves a room."""
        was_member = self.presence.leave(room_id, ws.username)
        self.broadcaster.disconnect(room_id, ws)

        if was_member:
            msg = self.store.save_message(
                room_id, ws.username,
                f"{ws.username} left the room",
                msg_type="leave",
            )
            self.broadcaster.broadcast(
                room_id,
                {"type": "leave", "username": ws.username, "message": msg.to_dict()},
            )

        ws.disconnect()
        return {"left": room_id, "username": ws.username}


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_message_store():
    """Show message persistence in SQLite."""
    print("--- Section 1: Message Store ---")

    store = MessageStore()

    # Create rooms
    room1 = store.create_room("general", "General", "admin")
    room2 = store.create_room("random", "Random", "admin")
    print(f"  Created rooms: {room1.id}, {room2.id}")

    # Save messages
    msg1 = store.save_message("general", "alice", "Hello everyone!")
    msg2 = store.save_message("general", "bob", "Hi Alice!")
    msg3 = store.save_message("general", "alice", "How's it going?")
    print(f"  Saved {3} messages to general")

    # Get history
    history = store.get_history("general")
    assert len(history) == 3
    assert history[0].username == "alice"
    assert history[0].content == "Hello everyone!"
    print(f"  History: {len(history)} messages")
    for m in history:
        print(f"    [{m.username}]: {m.content}")

    # List rooms
    rooms = store.list_rooms()
    assert len(rooms) == 2
    print(f"  Rooms: {[r.id for r in rooms]}")

    print("  [PASS] Message store works")


def demo_presence():
    """Show presence tracking."""
    print("\n--- Section 2: Presence Manager ---")

    presence = PresenceManager()

    # Join
    assert presence.join("general", "alice") is True
    assert presence.join("general", "bob") is True
    assert presence.join("general", "alice") is False  # Already in room
    print(f"  Members: {presence.get_members('general')}")
    assert presence.get_room_count("general") == 2

    # Leave
    assert presence.leave("general", "bob") is True
    assert presence.leave("general", "bob") is False  # Already left
    print(f"  After bob leaves: {presence.get_members('general')}")
    assert presence.get_room_count("general") == 1

    # Check membership
    assert presence.is_in_room("general", "alice") is True
    assert presence.is_in_room("general", "bob") is False

    print("  [PASS] Presence manager works")


def demo_broadcaster():
    """Show WebSocket broadcasting."""
    print("\n--- Section 3: WebSocket Broadcaster ---")

    broadcaster = WebSocketBroadcaster()

    ws_alice = SimulatedWebSocket("alice")
    ws_bob = SimulatedWebSocket("bob")
    ws_charlie = SimulatedWebSocket("charlie")

    broadcaster.connect("general", ws_alice)
    broadcaster.connect("general", ws_bob)
    broadcaster.connect("general", ws_charlie)
    print(f"  Connected: {broadcaster.get_connection_count('general')} clients")

    # Broadcast to all
    count = broadcaster.broadcast("general", {"text": "Hello all!"})
    assert count == 3
    print(f"  Broadcast to all: {count} clients")
    assert len(ws_alice.sent_messages) == 1

    # Broadcast excluding sender
    count2 = broadcaster.broadcast(
        "general",
        {"text": "From alice", "sender": "alice"},
        exclude=ws_alice,
    )
    assert count2 == 2
    assert len(ws_alice.sent_messages) == 1  # Alice didn't get it
    assert len(ws_bob.sent_messages) == 2
    print(f"  Broadcast excluding sender: {count2} clients")

    # Disconnect
    broadcaster.disconnect("general", ws_charlie)
    count3 = broadcaster.broadcast("general", {"text": "After disconnect"})
    assert count3 == 2
    print(f"  After disconnect: {count3} clients")

    print("  [PASS] WebSocket broadcaster works")


def demo_chat_server_http():
    """Show HTTP endpoints for chat."""
    print("\n--- Section 4: Chat Server HTTP ---")

    server = ChatServer()

    # Create rooms
    result = server.create_room("general", "General Chat", "admin")
    assert "room" in result
    print(f"  Created: {result['room']['name']}")

    result2 = server.create_room("dev", "Developer Chat", "alice")
    print(f"  Created: {result2['room']['name']}")

    # Duplicate room
    result3 = server.create_room("general", "General", "bob")
    assert "error" in result3
    print(f"  Duplicate: {result3['error']}")

    # List rooms
    rooms = server.list_rooms()
    assert len(rooms["rooms"]) == 2
    print(f"  Rooms: {[r['name'] for r in rooms['rooms']]}")

    # Get history (empty)
    history = server.get_history("general")
    assert history["count"] == 0
    print(f"  History (empty): {history['count']} messages")

    # Nonexistent room
    result4 = server.get_history("nonexistent")
    assert "error" in result4
    print(f"  Nonexistent room: {result4['error']}")

    print("  [PASS] Chat server HTTP works")


def demo_chat_server_websocket():
    """Show WebSocket real-time messaging."""
    print("\n--- Section 5: Chat Server WebSocket ---")

    server = ChatServer()
    server.create_room("general", "General Chat", "admin")

    # Users connect
    ws_alice = SimulatedWebSocket("alice")
    ws_bob = SimulatedWebSocket("bob")

    # Alice joins
    result = server.handle_join("general", ws_alice)
    assert result["joined"] == "general"
    assert result["is_new"] is True
    print(f"  Alice joined: {result}")

    # Alice should receive room info
    assert len(ws_alice.sent_messages) == 1
    room_info = ws_alice.sent_messages[0]
    assert room_info["type"] == "room_info"
    assert "alice" in room_info["members"]
    print(f"  Alice got room_info: members={room_info['members']}")

    # Bob joins
    result2 = server.handle_join("general", ws_bob)
    assert result2["is_new"] is True
    print(f"  Bob joined")

    # Alice should receive bob's join notification
    assert len(ws_alice.sent_messages) == 2
    join_notif = ws_alice.sent_messages[1]
    assert join_notif["type"] == "join"
    assert join_notif["username"] == "bob"
    print(f"  Alice got join notification: {join_notif['username']} joined")

    # Alice sends a message
    result3 = server.handle_message("general", ws_alice, "Hello Bob!")
    assert result3["sent"] is True
    print(f"  Alice sent: {result3['message']['content']}")

    # Both should receive the message (broadcast to all)
    alice_msgs = [m for m in ws_alice.sent_messages if m.get("type") == "message"]
    bob_msgs = [m for m in ws_bob.sent_messages if m.get("type") == "message"]
    assert len(alice_msgs) == 1
    assert len(bob_msgs) == 1
    print(f"  Both received the message")

    # Bob replies
    server.handle_message("general", ws_bob, "Hey Alice!")
    print(f"  Bob replied")

    # Check history
    history = server.get_history("general")
    msg_messages = [m for m in history["messages"] if m["type"] == "message"]
    assert len(msg_messages) == 2
    print(f"  History: {len(history['messages'])} total messages (including joins)")

    print("  [PASS] Chat server WebSocket works")


def demo_leave_and_presence():
    """Show leave notifications and presence updates."""
    print("\n--- Section 6: Leave and Presence ---")

    server = ChatServer()
    server.create_room("general", "General", "admin")

    ws_alice = SimulatedWebSocket("alice")
    ws_bob = SimulatedWebSocket("bob")
    ws_charlie = SimulatedWebSocket("charlie")

    server.handle_join("general", ws_alice)
    server.handle_join("general", ws_bob)
    server.handle_join("general", ws_charlie)

    members = server.presence.get_members("general")
    print(f"  Members before: {members}")
    assert len(members) == 3

    # Bob leaves
    result = server.handle_leave("general", ws_bob)
    assert result["left"] == "general"
    print(f"  Bob left: {result}")

    members = server.presence.get_members("general")
    print(f"  Members after: {members}")
    assert len(members) == 2
    assert "bob" not in members

    # Alice and Charlie should have received leave notification
    alice_leave = [m for m in ws_alice.sent_messages if m.get("type") == "leave"]
    assert len(alice_leave) == 1
    assert alice_leave[0]["username"] == "bob"
    print(f"  Alice got leave notification for bob")

    print("  [PASS] Leave and presence works")


def demo_multiple_rooms():
    """Show users in multiple rooms."""
    print("\n--- Section 7: Multiple Rooms ---")

    server = ChatServer()
    server.create_room("general", "General", "admin")
    server.create_room("dev", "Development", "admin")

    ws_alice_general = SimulatedWebSocket("alice")
    ws_alice_dev = SimulatedWebSocket("alice")
    ws_bob_general = SimulatedWebSocket("bob")

    server.handle_join("general", ws_alice_general)
    server.handle_join("dev", ws_alice_dev)
    server.handle_join("general", ws_bob_general)

    # Message in general doesn't appear in dev
    server.handle_message("general", ws_alice_general, "Hello general!")
    server.handle_message("dev", ws_alice_dev, "Hello dev!")

    general_history = server.get_history("general")
    dev_history = server.get_history("dev")

    general_chat = [m for m in general_history["messages"] if m["type"] == "message"]
    dev_chat = [m for m in dev_history["messages"] if m["type"] == "message"]

    assert len(general_chat) == 1
    assert general_chat[0]["content"] == "Hello general!"
    assert len(dev_chat) == 1
    assert dev_chat[0]["content"] == "Hello dev!"

    print(f"  General messages: {len(general_chat)}")
    print(f"  Dev messages: {len(dev_chat)}")
    print("  Messages are isolated to their rooms")

    # List rooms shows member counts
    rooms = server.list_rooms()
    for r in rooms["rooms"]:
        print(f"    {r['name']}: {r['members']} members")

    print("  [PASS] Multiple rooms work")


def demo_full_scenario():
    """Show a complete chat scenario."""
    print("\n--- Section 8: Full Chat Scenario ---")

    server = ChatServer()

    # 1. Create a room
    server.create_room("python-help", "Python Help", "moderator")
    print("  1. Room 'python-help' created")

    # 2. Users join
    ws_mod = SimulatedWebSocket("moderator")
    ws_alice = SimulatedWebSocket("alice")
    ws_bob = SimulatedWebSocket("bob")

    server.handle_join("python-help", ws_mod)
    server.handle_join("python-help", ws_alice)
    server.handle_join("python-help", ws_bob)
    print(f"  2. Users joined: {server.presence.get_members('python-help')}")

    # 3. Conversation
    server.handle_message("python-help", ws_alice, "How do I use asyncio?")
    server.handle_message("python-help", ws_mod, "Great question! Start with asyncio.run()")
    server.handle_message("python-help", ws_bob, "I had the same question!")
    server.handle_message("python-help", ws_mod, "Check out kata 38 for async generators")
    print("  3. Conversation: 4 messages exchanged")

    # 4. Bob leaves
    server.handle_leave("python-help", ws_bob)
    print(f"  4. Bob left. Members: {server.presence.get_members('python-help')}")

    # 5. New user joins and sees history
    ws_charlie = SimulatedWebSocket("charlie")
    server.handle_join("python-help", ws_charlie)
    room_info = ws_charlie.sent_messages[0]
    print(f"  5. Charlie joined. Got {len(room_info['history'])} messages of history")

    # 6. Check final state
    history = server.get_history("python-help")
    all_messages = history["messages"]
    chat_messages = [m for m in all_messages if m["type"] == "message"]
    join_messages = [m for m in all_messages if m["type"] == "join"]
    leave_messages = [m for m in all_messages if m["type"] == "leave"]

    print(f"  6. Final history: {len(chat_messages)} messages, "
          f"{len(join_messages)} joins, {len(leave_messages)} leaves")

    assert len(chat_messages) == 4
    assert len(join_messages) == 4  # mod, alice, bob, charlie
    assert len(leave_messages) == 1  # bob

    # Verify room list
    rooms = server.list_rooms()
    assert len(rooms["rooms"]) == 1
    assert rooms["rooms"][0]["members"] == 3  # mod, alice, charlie
    print(f"  7. Room has {rooms['rooms'][0]['members']} active members")

    print("  [PASS] Full chat scenario works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_message_store()
    demo_presence()
    demo_broadcaster()
    demo_chat_server_http()
    demo_chat_server_websocket()
    demo_leave_and_presence()
    demo_multiple_rooms()
    demo_full_scenario()

    print("\n--- Summary ---")
    print("The Real-Time Chat capstone combines:")
    print("  - SQLite message store for persistent history")
    print("  - Presence manager for tracking room membership")
    print("  - WebSocket broadcaster for real-time messaging")
    print("  - HTTP endpoints: create room, list rooms, get history")
    print("  - WebSocket handlers: join, message, leave")
    print("  - Join/leave notifications broadcast to room members")
    print("  - Message isolation between rooms")
    print("  - History replay for new joiners")
    print("\nAll 8 sections passed. Real-time chat capstone complete!")
    print("\nCongratulations! You've completed all 81 Python Katas")
    print("and built the Ignite framework from scratch!")


if __name__ == "__main__":
    main()
