"""
Kata 78 -- Real-Time Chat (Capstone 2)
Run: python playground/skeletons/78_realtime_chat.py

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
        # TODO: INSERT into messages table with room_id, username, content,
        # timestamp (time.time()), and msg_type
        # Return a ChatMessage with the inserted data
        pass

    def get_history(self, room_id: str, limit: int = 50) -> list[ChatMessage]:
        """Get recent messages for a room."""
        # TODO: SELECT from messages WHERE room_id = ?
        # ORDER BY timestamp DESC LIMIT ?
        # Return in chronological order (reverse the results)
        pass


# ===========================================================================
# SECTION 3: Presence Manager
# ===========================================================================

class PresenceManager:
    """Tracks user presence in chat rooms."""

    def __init__(self):
        self._rooms: dict[str, set[str]] = defaultdict(set)

    def join(self, room_id: str, username: str) -> bool:
        """User joins a room. Returns True if this is a new join."""
        # TODO: If username already in room, return False
        # Otherwise add to room and return True
        pass

    def leave(self, room_id: str, username: str) -> bool:
        """User leaves a room. Returns True if they were in the room."""
        # TODO: If username not in room, return False
        # Otherwise remove from room and return True
        # Clean up empty rooms
        pass

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

@dataclass
class WebSocketMessage:
    type: str
    data: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.data)


class SimulatedWebSocket:
    """Simulates a WebSocket connection for testing."""

    def __init__(self, username: str):
        self.username = username
        self.sent_messages: list[dict[str, Any]] = []
        self.connected = True

    def send(self, data: dict[str, Any]) -> None:
        if self.connected:
            self.sent_messages.append(data)

    def disconnect(self) -> None:
        self.connected = False


class WebSocketBroadcaster:
    """Broadcasts messages to all connected WebSocket clients in a room."""

    def __init__(self):
        self._connections: dict[str, list[SimulatedWebSocket]] = defaultdict(list)

    def connect(self, room_id: str, ws: SimulatedWebSocket) -> None:
        self._connections[room_id].append(ws)

    def disconnect(self, room_id: str, ws: SimulatedWebSocket) -> None:
        if room_id in self._connections:
            self._connections[room_id] = [
                c for c in self._connections[room_id] if c is not ws
            ]
            if not self._connections[room_id]:
                del self._connections[room_id]

    def broadcast(self, room_id: str, data: dict[str, Any],
                  exclude: SimulatedWebSocket | None = None) -> int:
        """Broadcast a message to all clients in a room."""
        # TODO: Iterate over connections for room_id
        # Skip excluded WebSocket and disconnected ones
        # Call ws.send(data) for each
        # Return count of messages sent
        pass

    def get_connection_count(self, room_id: str) -> int:
        return len(self._connections.get(room_id, []))


# ===========================================================================
# SECTION 5: Chat Server
# ===========================================================================

class ChatServer:
    """Real-time chat server combining HTTP and WebSocket handlers."""

    def __init__(self, db_path: str = ":memory:"):
        self.store = MessageStore(db_path)
        self.presence = PresenceManager()
        self.broadcaster = WebSocketBroadcaster()

    # -- HTTP Handlers --

    def create_room(self, room_id: str, name: str, created_by: str) -> dict:
        existing = self.store.get_room(room_id)
        if existing:
            return {"error": f"Room '{room_id}' already exists"}
        room = self.store.create_room(room_id, name, created_by)
        return {"room": room.to_dict()}

    def list_rooms(self) -> dict:
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
            # TODO:
            # 1. Save a "join" message to history
            # 2. Broadcast join notification to others (exclude ws)
            # 3. Send room_info to the joiner (room details, members, history)
            msg = self.store.save_message(
                room_id, ws.username,
                f"{ws.username} joined the room",
                msg_type="join",
            )
            self.broadcaster.broadcast(
                room_id,
                {"type": "join", "username": ws.username, "message": msg.to_dict()},
                exclude=ws,
            )
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

        msg = self.store.save_message(room_id, ws.username, content)

        # TODO: Broadcast message to all in room (including sender)
        # Data format: {"type": "message", "message": msg.to_dict()}
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
    print("--- Section 1: Message Store ---")

    try:
        store = MessageStore()

        room1 = store.create_room("general", "General", "admin")
        room2 = store.create_room("random", "Random", "admin")
        print(f"  Created rooms: {room1.id}, {room2.id}")

        msg1 = store.save_message("general", "alice", "Hello everyone!")
        msg2 = store.save_message("general", "bob", "Hi Alice!")
        msg3 = store.save_message("general", "alice", "How's it going?")
        print(f"  Saved 3 messages to general")

        history = store.get_history("general")
        assert len(history) == 3
        assert history[0].username == "alice"
        assert history[0].content == "Hello everyone!"
        print(f"  History: {len(history)} messages")
        for m in history:
            print(f"    [{m.username}]: {m.content}")

        rooms = store.list_rooms()
        assert len(rooms) == 2
        print(f"  Rooms: {[r.id for r in rooms]}")

        print("  [PASS] Message store works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_presence():
    print("\n--- Section 2: Presence Manager ---")

    try:
        presence = PresenceManager()

        assert presence.join("general", "alice") is True
        assert presence.join("general", "bob") is True
        assert presence.join("general", "alice") is False
        print(f"  Members: {presence.get_members('general')}")
        assert presence.get_room_count("general") == 2

        assert presence.leave("general", "bob") is True
        assert presence.leave("general", "bob") is False
        print(f"  After bob leaves: {presence.get_members('general')}")
        assert presence.get_room_count("general") == 1

        assert presence.is_in_room("general", "alice") is True
        assert presence.is_in_room("general", "bob") is False

        print("  [PASS] Presence manager works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_broadcaster():
    print("\n--- Section 3: WebSocket Broadcaster ---")

    try:
        broadcaster = WebSocketBroadcaster()

        ws_alice = SimulatedWebSocket("alice")
        ws_bob = SimulatedWebSocket("bob")
        ws_charlie = SimulatedWebSocket("charlie")

        broadcaster.connect("general", ws_alice)
        broadcaster.connect("general", ws_bob)
        broadcaster.connect("general", ws_charlie)
        print(f"  Connected: {broadcaster.get_connection_count('general')} clients")

        count = broadcaster.broadcast("general", {"text": "Hello all!"})
        assert count == 3
        print(f"  Broadcast to all: {count} clients")
        assert len(ws_alice.sent_messages) == 1

        count2 = broadcaster.broadcast(
            "general",
            {"text": "From alice", "sender": "alice"},
            exclude=ws_alice,
        )
        assert count2 == 2
        assert len(ws_alice.sent_messages) == 1
        assert len(ws_bob.sent_messages) == 2
        print(f"  Broadcast excluding sender: {count2} clients")

        broadcaster.disconnect("general", ws_charlie)
        count3 = broadcaster.broadcast("general", {"text": "After disconnect"})
        assert count3 == 2
        print(f"  After disconnect: {count3} clients")

        print("  [PASS] WebSocket broadcaster works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_chat_server_http():
    print("\n--- Section 4: Chat Server HTTP ---")

    try:
        server = ChatServer()

        result = server.create_room("general", "General Chat", "admin")
        assert "room" in result
        print(f"  Created: {result['room']['name']}")

        result2 = server.create_room("dev", "Developer Chat", "alice")
        print(f"  Created: {result2['room']['name']}")

        result3 = server.create_room("general", "General", "bob")
        assert "error" in result3
        print(f"  Duplicate: {result3['error']}")

        rooms = server.list_rooms()
        assert len(rooms["rooms"]) == 2
        print(f"  Rooms: {[r['name'] for r in rooms['rooms']]}")

        history = server.get_history("general")
        assert history["count"] == 0
        print(f"  History (empty): {history['count']} messages")

        result4 = server.get_history("nonexistent")
        assert "error" in result4
        print(f"  Nonexistent room: {result4['error']}")

        print("  [PASS] Chat server HTTP works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_chat_server_websocket():
    print("\n--- Section 5: Chat Server WebSocket ---")

    try:
        server = ChatServer()
        server.create_room("general", "General Chat", "admin")

        ws_alice = SimulatedWebSocket("alice")
        ws_bob = SimulatedWebSocket("bob")

        result = server.handle_join("general", ws_alice)
        assert result["joined"] == "general"
        assert result["is_new"] is True
        print(f"  Alice joined: {result}")

        assert len(ws_alice.sent_messages) == 1
        room_info = ws_alice.sent_messages[0]
        assert room_info["type"] == "room_info"
        assert "alice" in room_info["members"]
        print(f"  Alice got room_info: members={room_info['members']}")

        result2 = server.handle_join("general", ws_bob)
        assert result2["is_new"] is True
        print(f"  Bob joined")

        assert len(ws_alice.sent_messages) == 2
        join_notif = ws_alice.sent_messages[1]
        assert join_notif["type"] == "join"
        assert join_notif["username"] == "bob"
        print(f"  Alice got join notification: {join_notif['username']} joined")

        result3 = server.handle_message("general", ws_alice, "Hello Bob!")
        assert result3["sent"] is True
        print(f"  Alice sent: {result3['message']['content']}")

        alice_msgs = [m for m in ws_alice.sent_messages if m.get("type") == "message"]
        bob_msgs = [m for m in ws_bob.sent_messages if m.get("type") == "message"]
        assert len(alice_msgs) == 1
        assert len(bob_msgs) == 1
        print(f"  Both received the message")

        server.handle_message("general", ws_bob, "Hey Alice!")
        print(f"  Bob replied")

        history = server.get_history("general")
        msg_messages = [m for m in history["messages"] if m["type"] == "message"]
        assert len(msg_messages) == 2
        print(f"  History: {len(history['messages'])} total messages (including joins)")

        print("  [PASS] Chat server WebSocket works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_leave_and_presence():
    print("\n--- Section 6: Leave and Presence ---")

    try:
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

        result = server.handle_leave("general", ws_bob)
        assert result["left"] == "general"
        print(f"  Bob left: {result}")

        members = server.presence.get_members("general")
        print(f"  Members after: {members}")
        assert len(members) == 2
        assert "bob" not in members

        alice_leave = [m for m in ws_alice.sent_messages if m.get("type") == "leave"]
        assert len(alice_leave) == 1
        assert alice_leave[0]["username"] == "bob"
        print(f"  Alice got leave notification for bob")

        print("  [PASS] Leave and presence works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_multiple_rooms():
    print("\n--- Section 7: Multiple Rooms ---")

    try:
        server = ChatServer()
        server.create_room("general", "General", "admin")
        server.create_room("dev", "Development", "admin")

        ws_alice_general = SimulatedWebSocket("alice")
        ws_alice_dev = SimulatedWebSocket("alice")
        ws_bob_general = SimulatedWebSocket("bob")

        server.handle_join("general", ws_alice_general)
        server.handle_join("dev", ws_alice_dev)
        server.handle_join("general", ws_bob_general)

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

        rooms = server.list_rooms()
        for r in rooms["rooms"]:
            print(f"    {r['name']}: {r['members']} members")

        print("  [PASS] Multiple rooms work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_full_scenario():
    print("\n--- Section 8: Full Chat Scenario ---")

    try:
        server = ChatServer()

        server.create_room("python-help", "Python Help", "moderator")
        print("  1. Room 'python-help' created")

        ws_mod = SimulatedWebSocket("moderator")
        ws_alice = SimulatedWebSocket("alice")
        ws_bob = SimulatedWebSocket("bob")

        server.handle_join("python-help", ws_mod)
        server.handle_join("python-help", ws_alice)
        server.handle_join("python-help", ws_bob)
        print(f"  2. Users joined: {server.presence.get_members('python-help')}")

        server.handle_message("python-help", ws_alice, "How do I use asyncio?")
        server.handle_message("python-help", ws_mod, "Great question! Start with asyncio.run()")
        server.handle_message("python-help", ws_bob, "I had the same question!")
        server.handle_message("python-help", ws_mod, "Check out kata 38 for async generators")
        print("  3. Conversation: 4 messages exchanged")

        server.handle_leave("python-help", ws_bob)
        print(f"  4. Bob left. Members: {server.presence.get_members('python-help')}")

        ws_charlie = SimulatedWebSocket("charlie")
        server.handle_join("python-help", ws_charlie)
        room_info = ws_charlie.sent_messages[0]
        print(f"  5. Charlie joined. Got {len(room_info['history'])} messages of history")

        history = server.get_history("python-help")
        all_messages = history["messages"]
        chat_messages = [m for m in all_messages if m["type"] == "message"]
        join_messages = [m for m in all_messages if m["type"] == "join"]
        leave_messages = [m for m in all_messages if m["type"] == "leave"]

        print(f"  6. Final history: {len(chat_messages)} messages, "
              f"{len(join_messages)} joins, {len(leave_messages)} leaves")

        assert len(chat_messages) == 4
        assert len(join_messages) == 4
        assert len(leave_messages) == 1

        rooms = server.list_rooms()
        assert len(rooms["rooms"]) == 1
        assert rooms["rooms"][0]["members"] == 3
        print(f"  7. Room has {rooms['rooms'][0]['members']} active members")

        print("  [PASS] Full chat scenario works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


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
    print("\nAll 8 sections attempted. Real-time chat skeleton ready!")
    print("\nFill in the TODOs to complete the Ignite framework!")


if __name__ == "__main__":
    main()
