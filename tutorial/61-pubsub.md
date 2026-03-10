# Kata 61 -- PubSub System

[prev: 60-websocket-routes](./60-websocket-routes.md) | [next: 62-cookie-handling](./62-cookie-handling.md)

---

## What We're Building

An **in-memory publish/subscribe system** -- the messaging pattern that decouples message producers from consumers. Instead of sending messages directly to specific clients, publishers send to topics and subscribers listen to topics they care about:

1. **Topic-based subscriptions** -- subscribe to exact topics like `"chat.general"`
2. **Pattern-based subscriptions** -- subscribe to glob patterns like `"chat.*"` or `"user.*.login"`
3. **WebSocket integration** -- bridge pub/sub with WebSocket connections for real-time delivery

This is the pattern behind Redis Pub/Sub, MQTT, and event-driven architectures -- but we build it from scratch with Python's `asyncio` and `fnmatch`.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Topic subscription | Listen to a specific topic | Exact topic interest |
| Pattern subscription | Listen to topics matching a glob | Wildcard listeners |
| `fnmatch` | Glob-style pattern matching | `"chat.*"` matches `"chat.general"` |
| Publish | Send a message to all subscribers of a topic | Broadcasting events |
| Unsubscribe | Remove subscriptions by ID or topic | Client disconnect |
| Message serialization | Convert messages to dict/JSON | Wire format |
| WebSocket bridge | Deliver pub/sub messages via WebSocket | Real-time UI updates |

## The Code

### 1. Message and Subscription

```python
class Message:
    def __init__(self, topic, payload, publisher_id=None, metadata=None):
        self.topic = topic
        self.payload = payload
        self.publisher_id = publisher_id
        self.metadata = metadata or {}

class Subscription:
    def __init__(self, subscriber_id, topic_or_pattern, callback, is_pattern=False):
        self.subscriber_id = subscriber_id
        self.topic_or_pattern = topic_or_pattern
        self.callback = callback
        self.is_pattern = is_pattern

    def matches(self, topic):
        if self.is_pattern:
            return fnmatch.fnmatch(topic, self.topic_or_pattern)
        return self.topic_or_pattern == topic
```

### 2. PubSub Engine

```python
class PubSub:
    def __init__(self):
        self._subscriptions = {}           # topic -> [Subscription]
        self._pattern_subscriptions = []   # [Subscription] with patterns
        self._by_subscriber = {}           # subscriber_id -> [Subscription]

    def subscribe(self, topic, subscriber_id, callback):
        sub = Subscription(subscriber_id, topic, callback)
        self._subscriptions.setdefault(topic, []).append(sub)
        self._by_subscriber.setdefault(subscriber_id, []).append(sub)
        return sub

    def psubscribe(self, pattern, subscriber_id, callback):
        sub = Subscription(subscriber_id, pattern, callback, is_pattern=True)
        self._pattern_subscriptions.append(sub)
        return sub

    async def publish(self, topic, payload, publisher_id=None):
        message = Message(topic, payload, publisher_id)
        delivered = 0

        # Exact subscribers
        for sub in self._subscriptions.get(topic, []):
            await sub.callback(message)
            delivered += 1

        # Pattern subscribers
        for sub in self._pattern_subscriptions:
            if sub.matches(topic):
                await sub.callback(message)
                delivered += 1

        return delivered
```

### 3. Pattern Matching

```python
# fnmatch uses shell-style wildcards:
fnmatch.fnmatch("chat.general", "chat.*")     # True
fnmatch.fnmatch("chat.random", "chat.*")      # True
fnmatch.fnmatch("news.today", "chat.*")       # False
fnmatch.fnmatch("user.alice.login", "user.*.login")  # True
fnmatch.fnmatch("anything", "*")              # True
```

### 4. WebSocket Integration

```python
class WebSocketPubSub:
    def __init__(self):
        self.pubsub = PubSub()
        self._websockets = {}

    async def subscribe(self, ws, topic):
        async def deliver(message):
            await ws.send_json(message.to_dict())
        return self.pubsub.subscribe(topic, ws.client_id, deliver)

    def unregister(self, ws):
        self.pubsub.unsubscribe(ws.client_id)
        del self._websockets[ws.client_id]
```

## Playground

```
python playground/61_pubsub.py
```

Expected output:

```
--- Section 1: Basic PubSub ---
  Subscribed: Subscription('user_1', 'chat.general', exact)
  Published to 1 subscriber: 'Hello!'
  Published to empty topic: 0 subscribers
  Published to 2 subscribers: 'Hi all!'
  [PASS] Basic pub/sub works

--- Section 2: Pattern Subscriptions ---
  Pattern subscription: Subscription('monitor', 'chat.*', pattern)
  chat.* matched: ['chat.general', 'chat.random', 'chat.dev']
  * matched: anything.here
  user.*.login matched: ['user.alice.login', 'user.bob.login']
  [PASS] Pattern subscriptions work

--- Section 3: Unsubscribe ---
  user_1 topics: ['topic_a', 'topic_b']
  Removed 1 subscription for user_1 from topic_a
  Published to topic_a: 1 subscriber (user_2 only)
  [PASS] Unsubscribe works

--- Section 4: Message Serialization ---
  to_dict: {'topic': 'chat.general', 'payload': {...}, ...}
  to_json round-trip: OK
  Simple message: {'topic': 'test', 'payload': 'data'}
  [PASS] Message serialization works

--- Section 5: WebSocket Integration ---
  Published to chat.general: 3 recipients
  Published to chat.dev: 2 recipients
  After Bob unregistered: 2 recipients
  [PASS] WebSocket integration works

--- Section 6: Complex Scenario ---
  Dashboard events: ['metrics.cpu: 85.5', 'metrics.memory: 72.1']
  Alerter events: ['alert.high_cpu: CPU > 80%', 'alert.low_disk: Disk < 50%']
  Logger events: 6 total
  [PASS] Complex scenario works

All 6 sections passed. PubSub system mastered!
```

## How It Works

### Publish Flow

```
publish("chat.general", "Hello!")
        |
        +---> Exact subscribers for "chat.general"
        |       user_1 -> callback("Hello!")  ✓
        |       user_2 -> callback("Hello!")  ✓
        |
        +---> Pattern subscribers
                "chat.*" (monitor) -> matches? YES -> callback("Hello!")  ✓
                "*" (logger) -> matches? YES -> callback("Hello!")  ✓
                "user.*" (auth) -> matches? NO -> skip

Result: delivered to 4 subscribers
```

### Subscription Registry

```
_subscriptions (exact):
    "chat.general" -> [user_1, user_2]
    "chat.dev"     -> [user_2]
    "metrics.cpu"  -> [dashboard]

_pattern_subscriptions:
    "chat.*"        -> [monitor]
    "*"             -> [logger]
    "user.*.login"  -> [security]

_by_subscriber:
    "user_1"    -> [chat.general]
    "user_2"    -> [chat.general, chat.dev]
    "monitor"   -> [chat.*]
    "logger"    -> [*]
    "dashboard" -> [metrics.cpu]
    "security"  -> [user.*.login]
```

### WebSocket + PubSub Integration

```
Browser A                PubSub                Browser B
    |                      |                       |
    | subscribe("chat.*")  |                       |
    | ─────────────────>   |                       |
    |                      |  subscribe("chat.general")
    |                      |  <──────────────────── |
    |                      |                       |
    |  publish("chat.general", "Hi!")              |
    | ─────────────────>   |                       |
    |                      | deliver via callback  |
    | <── {"topic":"chat.general", "payload":"Hi!"}|
    |                      | ──────────────────> B |
    |                      |  {"topic":"chat.general", "payload":"Hi!"}
```

## Exercises

1. **Add message history** -- store the last N messages per topic. When a new subscriber joins, replay the history so they see recent context.

2. **Implement dead letter queue** -- when a subscriber's callback raises an exception, move the message to a dead letter topic for later inspection instead of losing it.

3. **Add subscription filters** -- allow subscribers to filter messages by payload content, e.g., `subscribe("orders", filter=lambda m: m.payload["amount"] > 100)`.

4. **Build topic namespacing** -- implement hierarchical topics where subscribing to `"chat"` automatically receives messages from `"chat.general"`, `"chat.random"`, etc. (MQTT-style topic trees).

5. **Add pub/sub metrics** -- track publish count, delivery count, average delivery time per topic. Expose via a `pubsub.stats()` method.

## What's Next

With the pub/sub system complete, our Ignite framework now supports real-time messaging with topic-based routing. In [Kata 62: Cookie Handling](./62-cookie-handling.md), we'll implement HTTP cookies -- parsing, setting, security attributes, and cookie-based sessions.

---

[prev: 60-websocket-routes](./60-websocket-routes.md) | [next: 62-cookie-handling](./62-cookie-handling.md)
