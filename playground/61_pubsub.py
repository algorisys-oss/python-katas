"""
Kata 61 -- PubSub System
Run: python playground/61_pubsub.py

Build an in-memory pub/sub system with topic-based and pattern-based
subscriptions, integrate with WebSocket connections for real-time
messaging, and test with async pub/sub scenarios.

Completes within 5 seconds.
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Subscriber and Message
# ===========================================================================
# A subscriber is an async callback that receives messages. A message has
# a topic, payload, and optional metadata.

class Message:
    """A pub/sub message published to a topic."""

    def __init__(
        self,
        topic: str,
        payload: Any,
        publisher_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.topic = topic
        self.payload = payload
        self.publisher_id = publisher_id
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the message to a dict."""
        result: dict[str, Any] = {
            "topic": self.topic,
            "payload": self.payload,
        }
        if self.publisher_id:
            result["publisher_id"] = self.publisher_id
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    def __repr__(self) -> str:
        return f"Message(topic={self.topic!r}, payload={self.payload!r})"


# Subscriber callback type: async function taking a Message
SubscriberCallback = Callable[[Message], Any]


class Subscription:
    """Represents a single subscription to a topic or pattern."""

    def __init__(
        self,
        subscriber_id: str,
        topic_or_pattern: str,
        callback: SubscriberCallback,
        is_pattern: bool = False,
    ):
        self.subscriber_id = subscriber_id
        self.topic_or_pattern = topic_or_pattern
        self.callback = callback
        self.is_pattern = is_pattern
        self.message_count = 0

    def matches(self, topic: str) -> bool:
        """Check if this subscription matches a given topic."""
        if self.is_pattern:
            return fnmatch.fnmatch(topic, self.topic_or_pattern)
        return self.topic_or_pattern == topic

    def __repr__(self) -> str:
        kind = "pattern" if self.is_pattern else "exact"
        return (
            f"Subscription({self.subscriber_id!r}, "
            f"{self.topic_or_pattern!r}, {kind})"
        )


# ===========================================================================
# SECTION 2: PubSub Engine
# ===========================================================================
# The core pub/sub system. Manages topics, subscriptions, and message
# delivery.

class PubSub:
    """In-memory publish/subscribe system.

    Supports:
    - Exact topic subscriptions: subscribe("chat.general", callback)
    - Pattern subscriptions: psubscribe("chat.*", callback)
    - Publishing to topics with delivery to all matching subscribers
    - Unsubscribe by subscriber ID or topic
    - Topic listing and subscriber counts
    """

    def __init__(self):
        # Exact topic subscriptions: topic -> list of Subscription
        self._subscriptions: dict[str, list[Subscription]] = {}
        # Pattern subscriptions: stored separately for matching
        self._pattern_subscriptions: list[Subscription] = []
        # Track all subscriptions by subscriber ID for cleanup
        self._by_subscriber: dict[str, list[Subscription]] = {}

    def subscribe(
        self,
        topic: str,
        subscriber_id: str,
        callback: SubscriberCallback,
    ) -> Subscription:
        """Subscribe to an exact topic.

        Args:
            topic: The topic to subscribe to (e.g., "chat.general")
            subscriber_id: Unique identifier for the subscriber
            callback: Async function called when a message is published
        """
        sub = Subscription(subscriber_id, topic, callback, is_pattern=False)

        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(sub)

        if subscriber_id not in self._by_subscriber:
            self._by_subscriber[subscriber_id] = []
        self._by_subscriber[subscriber_id].append(sub)

        return sub

    def psubscribe(
        self,
        pattern: str,
        subscriber_id: str,
        callback: SubscriberCallback,
    ) -> Subscription:
        """Subscribe with a glob pattern.

        Pattern examples:
        - "chat.*"      matches "chat.general", "chat.random"
        - "user.*.login" matches "user.alice.login", "user.bob.login"
        - "*"           matches everything

        Uses fnmatch for pattern matching.
        """
        sub = Subscription(subscriber_id, pattern, callback, is_pattern=True)
        self._pattern_subscriptions.append(sub)

        if subscriber_id not in self._by_subscriber:
            self._by_subscriber[subscriber_id] = []
        self._by_subscriber[subscriber_id].append(sub)

        return sub

    def unsubscribe(self, subscriber_id: str, topic: str | None = None) -> int:
        """Unsubscribe a subscriber.

        If topic is provided, only unsubscribe from that topic.
        If topic is None, unsubscribe from all topics.

        Returns the number of subscriptions removed.
        """
        removed = 0
        subs = self._by_subscriber.get(subscriber_id, [])

        to_remove = []
        for sub in subs:
            if topic is None or sub.topic_or_pattern == topic:
                to_remove.append(sub)

        for sub in to_remove:
            subs.remove(sub)
            removed += 1

            if sub.is_pattern:
                if sub in self._pattern_subscriptions:
                    self._pattern_subscriptions.remove(sub)
            else:
                topic_subs = self._subscriptions.get(sub.topic_or_pattern, [])
                if sub in topic_subs:
                    topic_subs.remove(sub)
                # Clean up empty topic lists
                if not topic_subs and sub.topic_or_pattern in self._subscriptions:
                    del self._subscriptions[sub.topic_or_pattern]

        if not subs:
            self._by_subscriber.pop(subscriber_id, None)

        return removed

    async def publish(
        self,
        topic: str,
        payload: Any,
        publisher_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Publish a message to a topic.

        Delivers to all exact subscribers and matching pattern subscribers.
        Returns the number of subscribers that received the message.
        """
        message = Message(topic, payload, publisher_id, metadata)
        delivered = 0

        # Exact topic subscribers
        for sub in self._subscriptions.get(topic, []):
            await sub.callback(message)
            sub.message_count += 1
            delivered += 1

        # Pattern subscribers
        for sub in self._pattern_subscriptions:
            if sub.matches(topic):
                await sub.callback(message)
                sub.message_count += 1
                delivered += 1

        return delivered

    @property
    def topics(self) -> list[str]:
        """List all topics with active subscriptions."""
        return list(self._subscriptions.keys())

    @property
    def patterns(self) -> list[str]:
        """List all active subscription patterns."""
        return [sub.topic_or_pattern for sub in self._pattern_subscriptions]

    def subscriber_count(self, topic: str) -> int:
        """Count subscribers for a specific topic (exact only)."""
        return len(self._subscriptions.get(topic, []))

    def get_subscriber_topics(self, subscriber_id: str) -> list[str]:
        """Get all topics/patterns a subscriber is subscribed to."""
        return [
            sub.topic_or_pattern
            for sub in self._by_subscriber.get(subscriber_id, [])
        ]


# ===========================================================================
# SECTION 3: WebSocket PubSub Integration
# ===========================================================================
# Bridge between WebSocket connections and the pub/sub system.

class WebSocketState:
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocketDisconnect(Exception):
    def __init__(self, code: int = 1000):
        self.code = code
        super().__init__(f"WebSocket disconnected with code {code}")


class MockWebSocket:
    """Simplified WebSocket mock for pub/sub integration testing."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.state = WebSocketState.CONNECTED
        self.sent_messages: list[str] = []

    async def send_text(self, text: str) -> None:
        if self.state != WebSocketState.CONNECTED:
            raise RuntimeError("Not connected")
        self.sent_messages.append(text)

    async def send_json(self, data: Any) -> None:
        await self.send_text(json.dumps(data))


class WebSocketPubSub:
    """Integrates WebSocket connections with the PubSub system.

    Each WebSocket client can subscribe to topics. When a message is
    published, it's delivered to the WebSocket as a JSON text message.
    """

    def __init__(self):
        self.pubsub = PubSub()
        self._websockets: dict[str, MockWebSocket] = {}

    def register(self, ws: MockWebSocket) -> None:
        """Register a WebSocket connection."""
        self._websockets[ws.client_id] = ws

    def unregister(self, ws: MockWebSocket) -> None:
        """Unregister a WebSocket and remove all its subscriptions."""
        self.pubsub.unsubscribe(ws.client_id)
        self._websockets.pop(ws.client_id, None)

    async def subscribe(self, ws: MockWebSocket, topic: str) -> Subscription:
        """Subscribe a WebSocket client to a topic."""
        async def deliver(message: Message) -> None:
            target = self._websockets.get(ws.client_id)
            if target and target.state == WebSocketState.CONNECTED:
                await target.send_json(message.to_dict())

        return self.pubsub.subscribe(topic, ws.client_id, deliver)

    async def psubscribe(self, ws: MockWebSocket, pattern: str) -> Subscription:
        """Subscribe a WebSocket client to a pattern."""
        async def deliver(message: Message) -> None:
            target = self._websockets.get(ws.client_id)
            if target and target.state == WebSocketState.CONNECTED:
                await target.send_json(message.to_dict())

        return self.pubsub.psubscribe(pattern, ws.client_id, deliver)

    async def publish(
        self,
        topic: str,
        payload: Any,
        publisher_id: str | None = None,
    ) -> int:
        """Publish a message to a topic."""
        return await self.pubsub.publish(topic, payload, publisher_id)


# ===========================================================================
# SECTION 4: Demos
# ===========================================================================

async def demo_basic_pubsub():
    """Demonstrate basic pub/sub subscribe and publish."""
    print("--- Section 1: Basic PubSub ---")

    pubsub = PubSub()
    received: list[Message] = []

    async def on_message(msg: Message) -> None:
        received.append(msg)

    # Subscribe
    sub = pubsub.subscribe("chat.general", "user_1", on_message)
    print(f"  Subscribed: {sub}")
    assert pubsub.subscriber_count("chat.general") == 1

    # Publish
    count = await pubsub.publish("chat.general", "Hello!", publisher_id="admin")
    assert count == 1
    assert len(received) == 1
    assert received[0].payload == "Hello!"
    assert received[0].topic == "chat.general"
    assert received[0].publisher_id == "admin"
    print(f"  Published to {count} subscriber: '{received[0].payload}'")

    # Publish to a topic with no subscribers
    count = await pubsub.publish("chat.random", "Anyone here?")
    assert count == 0
    print(f"  Published to empty topic: {count} subscribers")

    # Multiple subscribers
    received2: list[Message] = []

    async def on_message2(msg: Message) -> None:
        received2.append(msg)

    pubsub.subscribe("chat.general", "user_2", on_message2)
    assert pubsub.subscriber_count("chat.general") == 2

    count = await pubsub.publish("chat.general", "Hi all!")
    assert count == 2
    assert len(received) == 2  # user_1 got 2 total
    assert len(received2) == 1  # user_2 got 1
    print(f"  Published to {count} subscribers: '{received[-1].payload}'")

    print("  [PASS] Basic pub/sub works")


async def demo_pattern_subscriptions():
    """Demonstrate pattern-based subscriptions."""
    print("\n--- Section 2: Pattern Subscriptions ---")

    pubsub = PubSub()
    received: list[Message] = []

    async def on_message(msg: Message) -> None:
        received.append(msg)

    # Subscribe to chat.* pattern
    sub = pubsub.psubscribe("chat.*", "monitor", on_message)
    print(f"  Pattern subscription: {sub}")

    # Publish to various chat topics
    await pubsub.publish("chat.general", "msg1")
    await pubsub.publish("chat.random", "msg2")
    await pubsub.publish("chat.dev", "msg3")
    await pubsub.publish("news.today", "msg4")  # Should NOT match

    assert len(received) == 3
    topics = [m.topic for m in received]
    assert "chat.general" in topics
    assert "chat.random" in topics
    assert "chat.dev" in topics
    print(f"  chat.* matched: {topics}")

    # Wildcard subscription
    all_received: list[Message] = []

    async def on_all(msg: Message) -> None:
        all_received.append(msg)

    pubsub.psubscribe("*", "admin", on_all)
    await pubsub.publish("anything.here", "test")
    assert len(all_received) == 1
    print(f"  * matched: {all_received[0].topic}")

    # Nested pattern: user.*.login
    login_received: list[Message] = []

    async def on_login(msg: Message) -> None:
        login_received.append(msg)

    pubsub.psubscribe("user.*.login", "security", on_login)
    await pubsub.publish("user.alice.login", "login event")
    await pubsub.publish("user.bob.login", "login event")
    await pubsub.publish("user.alice.logout", "logout event")  # No match

    assert len(login_received) == 2
    print(f"  user.*.login matched: {[m.topic for m in login_received]}")

    print("  [PASS] Pattern subscriptions work")


async def demo_unsubscribe():
    """Demonstrate unsubscribing."""
    print("\n--- Section 3: Unsubscribe ---")

    pubsub = PubSub()
    received: list[Message] = []

    async def on_message(msg: Message) -> None:
        received.append(msg)

    pubsub.subscribe("topic_a", "user_1", on_message)
    pubsub.subscribe("topic_b", "user_1", on_message)
    pubsub.subscribe("topic_a", "user_2", on_message)

    # user_1 is on topic_a and topic_b
    topics = pubsub.get_subscriber_topics("user_1")
    print(f"  user_1 topics: {topics}")
    assert len(topics) == 2

    # Unsubscribe user_1 from topic_a only
    removed = pubsub.unsubscribe("user_1", "topic_a")
    assert removed == 1
    print(f"  Removed {removed} subscription for user_1 from topic_a")

    topics = pubsub.get_subscriber_topics("user_1")
    assert topics == ["topic_b"]

    # Publish to topic_a: only user_2 receives
    count = await pubsub.publish("topic_a", "test")
    assert count == 1
    assert len(received) == 1
    print(f"  Published to topic_a: {count} subscriber (user_2 only)")

    # Unsubscribe user_1 from everything
    removed = pubsub.unsubscribe("user_1")
    assert removed == 1
    print(f"  Removed all {removed} remaining subscription(s) for user_1")

    topics = pubsub.get_subscriber_topics("user_1")
    assert topics == []

    # Pattern unsubscribe
    pubsub.psubscribe("events.*", "logger", on_message)
    assert len(pubsub.patterns) == 1
    removed = pubsub.unsubscribe("logger")
    assert removed == 1
    assert len(pubsub.patterns) == 0
    print(f"  Removed pattern subscription for logger")

    print("  [PASS] Unsubscribe works")


async def demo_message_serialization():
    """Demonstrate message serialization."""
    print("\n--- Section 4: Message Serialization ---")

    msg = Message(
        topic="chat.general",
        payload={"text": "Hello!", "emoji": True},
        publisher_id="alice",
        metadata={"timestamp": "2026-01-01T00:00:00Z"},
    )

    d = msg.to_dict()
    print(f"  to_dict: {d}")
    assert d["topic"] == "chat.general"
    assert d["payload"]["text"] == "Hello!"
    assert d["publisher_id"] == "alice"
    assert d["metadata"]["timestamp"] == "2026-01-01T00:00:00Z"

    j = msg.to_json()
    parsed = json.loads(j)
    assert parsed == d
    print(f"  to_json round-trip: OK")

    # Message without optional fields
    simple = Message("test", "data")
    d2 = simple.to_dict()
    assert "publisher_id" not in d2
    assert "metadata" not in d2
    print(f"  Simple message: {d2}")

    print("  [PASS] Message serialization works")


async def demo_websocket_integration():
    """Demonstrate WebSocket + PubSub integration."""
    print("\n--- Section 5: WebSocket Integration ---")

    ws_pubsub = WebSocketPubSub()

    # Create mock WebSocket clients
    ws_alice = MockWebSocket("alice")
    ws_bob = MockWebSocket("bob")
    ws_charlie = MockWebSocket("charlie")

    ws_pubsub.register(ws_alice)
    ws_pubsub.register(ws_bob)
    ws_pubsub.register(ws_charlie)

    # Alice subscribes to chat.general
    await ws_pubsub.subscribe(ws_alice, "chat.general")
    # Bob subscribes to chat.general and chat.dev
    await ws_pubsub.subscribe(ws_bob, "chat.general")
    await ws_pubsub.subscribe(ws_bob, "chat.dev")
    # Charlie subscribes to all chat.* via pattern
    await ws_pubsub.psubscribe(ws_charlie, "chat.*")

    # Publish to chat.general
    count = await ws_pubsub.publish("chat.general", "Hello!", "system")
    # Alice (exact), Bob (exact), Charlie (pattern) = 3
    assert count == 3
    print(f"  Published to chat.general: {count} recipients")

    # Alice should have 1 message
    assert len(ws_alice.sent_messages) == 1
    msg_alice = json.loads(ws_alice.sent_messages[0])
    assert msg_alice["topic"] == "chat.general"
    assert msg_alice["payload"] == "Hello!"

    # Publish to chat.dev
    count = await ws_pubsub.publish("chat.dev", "Bug fix deployed")
    # Bob (exact), Charlie (pattern) = 2
    assert count == 2
    print(f"  Published to chat.dev: {count} recipients")

    assert len(ws_alice.sent_messages) == 1  # Alice didn't get this
    assert len(ws_bob.sent_messages) == 2     # Bob got both
    assert len(ws_charlie.sent_messages) == 2  # Charlie got both via pattern

    # Unregister Bob
    ws_pubsub.unregister(ws_bob)
    count = await ws_pubsub.publish("chat.general", "After Bob left")
    assert count == 2  # Alice + Charlie
    print(f"  After Bob unregistered: {count} recipients")

    print("  [PASS] WebSocket integration works")


async def demo_complex_scenario():
    """Simulate a realistic pub/sub scenario."""
    print("\n--- Section 6: Complex Scenario ---")

    pubsub = PubSub()

    # Track all events per subscriber
    events: dict[str, list[str]] = {
        "dashboard": [],
        "alerter": [],
        "logger": [],
    }

    async def make_callback(name: str):
        async def cb(msg: Message) -> None:
            events[name].append(f"{msg.topic}: {msg.payload}")
        return cb

    # Dashboard subscribes to specific metrics
    pubsub.subscribe("metrics.cpu", "dashboard", await make_callback("dashboard"))
    pubsub.subscribe("metrics.memory", "dashboard", await make_callback("dashboard"))

    # Alerter subscribes to all alerts via pattern
    pubsub.psubscribe("alert.*", "alerter", await make_callback("alerter"))

    # Logger subscribes to everything
    pubsub.psubscribe("*", "logger", await make_callback("logger"))

    # Publish various events
    await pubsub.publish("metrics.cpu", 85.5)
    await pubsub.publish("metrics.memory", 72.1)
    await pubsub.publish("metrics.disk", 45.0)
    await pubsub.publish("alert.high_cpu", "CPU > 80%")
    await pubsub.publish("alert.low_disk", "Disk < 50%")
    await pubsub.publish("system.startup", "App started")

    # Dashboard got cpu and memory only
    assert len(events["dashboard"]) == 2
    print(f"  Dashboard events: {events['dashboard']}")

    # Alerter got both alerts
    assert len(events["alerter"]) == 2
    print(f"  Alerter events: {events['alerter']}")

    # Logger got everything
    assert len(events["logger"]) == 6
    print(f"  Logger events: {len(events['logger'])} total")

    # Show topic listing
    print(f"  Active topics: {pubsub.topics}")
    print(f"  Active patterns: {pubsub.patterns}")

    # Subscriber counts
    assert pubsub.subscriber_count("metrics.cpu") == 1
    assert pubsub.subscriber_count("metrics.memory") == 1

    print("  [PASS] Complex scenario works")


async def async_main():
    await demo_basic_pubsub()
    await demo_pattern_subscriptions()
    await demo_unsubscribe()
    await demo_message_serialization()
    await demo_websocket_integration()
    await demo_complex_scenario()


def main():
    asyncio.run(async_main())

    print("\n--- Summary ---")
    print("PubSub system implementation covers:")
    print("  - Topic-based exact subscriptions")
    print("  - Pattern-based subscriptions with glob matching (fnmatch)")
    print("  - Publish to topics with delivery to all matching subscribers")
    print("  - Unsubscribe by subscriber ID or specific topic")
    print("  - Message serialization (dict, JSON)")
    print("  - WebSocket integration for real-time delivery")
    print("  - Complex multi-subscriber, multi-topic scenarios")
    print("\nAll 6 sections passed. PubSub system mastered!")
    print("Next up: Kata 62 -- Cookie handling!")


if __name__ == "__main__":
    main()
