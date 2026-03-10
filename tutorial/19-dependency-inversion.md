# Kata 19 -- Dependency Inversion Principle

[prev: 18-interface-segregation](./18-interface-segregation.md) | [next: 20-design-patterns](./20-design-patterns.md)

---

## What We're Building

The **Dependency Inversion Principle** (DIP) is the fifth and final SOLID principle. It states: *high-level modules should not depend on low-level modules -- both should depend on abstractions*. And: *abstractions should not depend on details -- details should depend on abstractions*.

In this kata we'll start with a `NotificationService` that depends directly on a concrete `EmailSender` class. When we need to add SMS or push notifications, we're stuck -- the service is welded to email. We'll refactor to depend on a `MessageSender` protocol, use constructor injection, build a simple DI container, and prove testability with mock implementations.

This kata is particularly important because it sets up the mental model for FastAPI's `Depends()` pattern, which we'll build from scratch in later katas.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Dependency Inversion Principle | High-level depends on abstractions, not concretions | Always -- it's the capstone of SOLID |
| `Protocol` for abstractions | Structural subtyping (duck typing with type safety) | Defining contracts without inheritance |
| Constructor injection | Pass dependencies through `__init__` | Default pattern for DI in Python |
| Inversion of control | The caller decides which implementation to use | Decoupling creation from usage |
| DI container | A registry that wires dependencies automatically | Managing complex dependency graphs |
| Test doubles | Mock/fake implementations for testing | Verifying behavior without side effects |

## The Code

### Step 1: The tightly coupled version (violates DIP)

Here's a `NotificationService` that creates its own `EmailSender` internally. The high-level module (`NotificationService`) depends directly on the low-level module (`EmailSender`):

```python
class EmailSender:
    """Low-level module: knows how to send emails."""

    def __init__(self):
        self.sent: list[dict] = []

    def send_email(self, to: str, subject: str, body: str):
        message = {"to": to, "subject": subject, "body": body}
        self.sent.append(message)
        print(f"  [EMAIL] To: {to} | Subject: {subject}")


class NotificationService:
    """High-level module -- but it's WELDED to EmailSender."""

    def __init__(self):
        self.sender = EmailSender()  # <-- creates its own dependency!

    def notify(self, user: str, message: str):
        self.sender.send_email(user, "Notification", message)
```

Problems with this design:

- **Can't switch to SMS** without modifying `NotificationService`
- **Can't test** without actually "sending emails"
- **Can't reuse** `NotificationService` with a different sender
- **Violates OCP** -- adding new channels requires changing existing code

### Step 2: The abstraction -- `MessageSender` protocol

The fix is to introduce an **abstraction** that both high-level and low-level modules depend on. In Python, `Protocol` is the idiomatic way to define this contract:

```python
from typing import Protocol


class MessageSender(Protocol):
    """The abstraction both sides depend on.

    Any class with a send(to, subject, body) method satisfies this protocol.
    No inheritance required -- this is structural subtyping.
    """

    def send(self, to: str, subject: str, body: str) -> None: ...
```

Why `Protocol` instead of `ABC`? Because Protocol uses **structural subtyping** -- any class that has the right methods is automatically compatible, without needing to inherit from anything. This is Python's version of Go interfaces or TypeScript structural types.

### Step 3: Concrete implementations

Each implementation handles one delivery channel. They don't know about each other or about `NotificationService`:

```python
class EmailSender:
    """Concrete implementation: sends via email."""

    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        message = {"to": to, "subject": subject, "body": body, "channel": "email"}
        self.sent.append(message)
        print(f"  [EMAIL] To: {to} | Subject: {subject}")


class SmsSender:
    """Concrete implementation: sends via SMS."""

    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        message = {"to": to, "subject": subject, "body": body, "channel": "sms"}
        self.sent.append(message)
        print(f"  [SMS] To: {to} | Message: {body}")


class PushSender:
    """Concrete implementation: sends via push notification."""

    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        message = {"to": to, "subject": subject, "body": body, "channel": "push"}
        self.sent.append(message)
        print(f"  [PUSH] To: {to} | Title: {subject} | Body: {body}")
```

Notice: none of these classes inherit from `MessageSender`. They satisfy the protocol structurally -- they all have `send(to, subject, body) -> None`.

### Step 4: The refactored NotificationService (depends on abstraction)

Now `NotificationService` depends on the `MessageSender` protocol, not on any concrete class:

```python
class NotificationService:
    """High-level module -- depends on MessageSender abstraction.

    Doesn't know or care whether it's sending email, SMS, or push.
    The caller decides which implementation to inject.
    """

    def __init__(self, sender: MessageSender):
        self.sender = sender  # <-- injected, not created!

    def notify(self, user: str, message: str):
        self.sender.send(user, "Notification", message)

    def send_welcome(self, user: str):
        self.sender.send(user, "Welcome!", f"Welcome to the platform, {user}!")

    def send_alert(self, user: str, alert: str):
        self.sender.send(user, "Alert", f"ALERT: {alert}")
```

This is **inversion of control** -- the `NotificationService` no longer controls which sender it uses. That decision is pushed up to the caller (the "composition root").

### Step 5: Constructor injection in action

The caller (composition root) wires everything together:

```python
# The caller decides which implementation to use
email = EmailSender()
sms = SmsSender()
push = PushSender()

# Same NotificationService, different behaviors
email_notifier = NotificationService(email)
sms_notifier = NotificationService(sms)
push_notifier = NotificationService(push)

email_notifier.notify("alice@example.com", "Your order shipped!")
sms_notifier.notify("+1-555-0123", "Your order shipped!")
push_notifier.notify("alice_device_token", "Your order shipped!")
```

The `NotificationService` code never changed. We added two new channels (SMS, push) without modifying a single line of existing code. That's DIP + OCP working together.

### Step 6: A simple DI container

In real applications, manually wiring dependencies gets tedious. A DI container automates this. Here's a minimal one:

```python
class Container:
    """Simple dependency injection container.

    Register factories for types, then resolve them on demand.
    This is a simplified version of what FastAPI's Depends() does.
    """

    def __init__(self):
        self._factories: dict[str, callable] = {}
        self._singletons: dict[str, object] = {}

    def register(self, name: str, factory: callable, singleton: bool = False):
        """Register a factory function for a dependency."""
        self._factories[name] = (factory, singleton)

    def resolve(self, name: str) -> object:
        """Resolve a dependency by name."""
        if name in self._singletons:
            return self._singletons[name]

        if name not in self._factories:
            raise KeyError(f"No factory registered for '{name}'")

        factory, singleton = self._factories[name]
        instance = factory(self)

        if singleton:
            self._singletons[name] = instance

        return instance
```

Usage:

```python
container = Container()

# Register factories -- the container knows HOW to create things
container.register("sender", lambda c: EmailSender())
container.register("notifier", lambda c: NotificationService(c.resolve("sender")))

# Resolve -- the container creates and wires everything
notifier = container.resolve("notifier")
notifier.notify("alice@example.com", "Container wired this!")
```

To switch from email to SMS, change one line:

```python
container.register("sender", lambda c: SmsSender())
```

Everything downstream automatically gets the new implementation.

### Step 7: Testability with mock implementations

The biggest payoff of DIP is testability. Create a mock that records calls without side effects:

```python
class MockSender:
    """Test double that records all sends without side effects."""

    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


def test_notification_service():
    mock = MockSender()
    service = NotificationService(mock)

    service.notify("alice@test.com", "Test message")
    assert len(mock.sent) == 1
    assert mock.sent[0]["to"] == "alice@test.com"
    assert mock.sent[0]["subject"] == "Notification"

    service.send_welcome("bob@test.com")
    assert len(mock.sent) == 2
    assert "Welcome" in mock.sent[1]["subject"]

    service.send_alert("charlie@test.com", "Server down!")
    assert len(mock.sent) == 3
    assert "ALERT" in mock.sent[2]["body"]
```

No real emails. No SMTP connections. No network. Pure logic testing.

### Step 8: Multi-sender -- composing abstractions

Once you depend on abstractions, you can compose them freely:

```python
class MultiSender:
    """Sends via multiple channels simultaneously.

    Itself satisfies MessageSender protocol -- it's turtles all the way down.
    """

    def __init__(self, senders: list[MessageSender]):
        self.senders = senders

    def send(self, to: str, subject: str, body: str) -> None:
        for sender in self.senders:
            sender.send(to, subject, body)
```

`MultiSender` satisfies the `MessageSender` protocol too. You can inject it into `NotificationService` just like any other sender. This is the power of depending on abstractions -- implementations are infinitely composable.

## Playground

Run the full demonstration with tests:

```bash
python playground/19_dependency_inversion.py
```

```
--- Section 1: Tightly Coupled (Violates DIP) ---
  [EMAIL] To: alice@example.com | Subject: Notification
  Tightly coupled version works -- but we can't swap the sender.

--- Section 2: The Abstraction (MessageSender Protocol) ---
  MessageSender protocol defines the contract: send(to, subject, body) -> None
  EmailSender satisfies the protocol (structural subtyping -- no inheritance!)
  SmsSender satisfies the protocol
  PushSender satisfies the protocol

--- Section 3: Refactored NotificationService (Depends on Abstraction) ---
  [EMAIL] To: alice@example.com | Subject: Notification
  [SMS] To: +1-555-0123 | Message: Your order shipped!
  [PUSH] To: alice_device | Title: Notification | Body: Your order shipped!
  Same NotificationService, three different behaviors -- zero code changes!

--- Section 4: Constructor Injection ---
  [EMAIL] To: user@example.com | Subject: Welcome!
  [SMS] To: +1-555-9999 | Message: ALERT: Server overloaded!
  Constructor injection lets the caller control the implementation.

--- Section 5: Simple DI Container ---
  [EMAIL] To: alice@example.com | Subject: Notification
  Container resolved and wired dependencies automatically.
  Switching to SMS -- only change the registration:
  [SMS] To: alice@example.com | Message: Same code, different sender!
  One line change swapped the entire notification channel!

--- Section 6: Testability with Mock ---
  notify() test passed!
  send_welcome() test passed!
  send_alert() test passed!
  Mock sender: zero side effects, full verification.

--- Section 7: Multi-Sender Composition ---
  [EMAIL] To: admin@example.com | Subject: Alert
  [SMS] To: admin@example.com | Message: ALERT: Database failover triggered
  [PUSH] To: admin@example.com | Title: Alert | Body: ALERT: Database failover triggered
  MultiSender itself satisfies MessageSender -- composable abstractions!

--- Section 8: DIP vs. No DIP Comparison ---
  WITHOUT DIP:
    - NotificationService creates EmailSender internally
    - Can't swap sender without modifying NotificationService
    - Can't test without side effects
    - Adding channels requires changing existing code
  WITH DIP:
    - NotificationService depends on MessageSender protocol
    - Any sender can be injected (email, SMS, push, mock, multi)
    - Testing is trivial with MockSender
    - New channels never touch existing code

--- Summary ---
Dependency Inversion Principle:
  - High-level modules depend on abstractions, not concretions
  - Use Protocol for structural subtyping (no inheritance needed)
  - Constructor injection: pass dependencies via __init__
  - Inversion of control: caller decides the implementation
  - DI containers automate wiring for complex graphs
  - MockSender pattern makes testing trivial
  - This is the foundation for FastAPI's Depends() system

All 8 sections passed. You've mastered the Dependency Inversion Principle!
```

## How It Works

```
BEFORE (DIP violation):               AFTER (DIP applied):

+--------------------+                +--------------------+
| NotificationService|                | NotificationService|
|   (high-level)     |                |   (high-level)     |
+---------+----------+                +---------+----------+
          |                                     |
          | creates                             | depends on
          | directly                            v
          v                           +--------------------+
+---------+----------+                |  MessageSender     |
|    EmailSender     |                |    (Protocol)      |
|   (low-level)      |                +----+------+--------+
+--------------------+                     |      |       |
                                    implements implements implements
                                     |      |       |
                               +-----+-+ +--+---+ ++-------+
                               | Email | | SMS  | | Push   |
                               | Sender| |Sender| | Sender |
                               +-------+ +------+ +--------+

BEFORE: High-level → Low-level (direct dependency)
AFTER:  High-level → Abstraction ← Low-level (both depend on abstraction)

The arrow between high-level and low-level is INVERTED -- hence "Dependency Inversion."
```

The key insight: **both** the high-level module and the low-level modules depend on the abstraction. The abstraction is owned by the high-level module (it defines what it needs), and the low-level modules conform to that contract. The dependency arrow between high and low is *inverted* compared to the naive design.

### Connection to FastAPI's `Depends()`

FastAPI's dependency injection system is DIP in action:

```python
# FastAPI's Depends() is constructor injection for route handlers
from fastapi import Depends

def get_db():
    return Database()  # factory function

@app.get("/users")
def list_users(db = Depends(get_db)):  # injected!
    return db.query("SELECT * FROM users")
```

In later katas, we'll build this exact pattern from scratch. The mental model is identical:
1. The route handler (high-level) depends on an abstraction (the `db` parameter type)
2. The factory function (low-level) provides the concrete implementation
3. `Depends()` is the DI container that wires them together

## Exercises

### Exercise 1: Add a logging sender decorator

Create a `LoggingSender` that wraps any `MessageSender` and logs before/after sending. It should itself satisfy the `MessageSender` protocol:

```python
class LoggingSender:
    """Decorator that logs sends -- wraps any MessageSender."""

    def __init__(self, inner: MessageSender, logger: Logger): ...

    def send(self, to: str, subject: str, body: str) -> None:
        # Log before sending
        # Delegate to inner.send()
        # Log after sending
        ...

# Usage:
logged_email = LoggingSender(EmailSender(), logger)
service = NotificationService(logged_email)
```

### Exercise 2: Build a priority-based sender

Create a `PrioritySender` that routes messages to different senders based on a priority level:

```python
class PrioritySender:
    """Routes to different senders based on priority."""

    def __init__(self, low: MessageSender, high: MessageSender): ...

    def send(self, to: str, subject: str, body: str) -> None:
        # Check if subject contains "ALERT" or "URGENT"
        # If so, use self.high sender; otherwise use self.low sender
        ...

# Usage:
priority = PrioritySender(low=EmailSender(), high=SmsSender())
service = NotificationService(priority)
```

### Exercise 3: Extend the DI container with auto-wiring

Add type-hint-based auto-resolution to the `Container`:

```python
import inspect

class AutoContainer(Container):
    def auto_resolve(self, cls: type) -> object:
        """Create an instance by inspecting __init__ type hints."""
        hints = inspect.get_type_hints(cls.__init__)
        # For each parameter, resolve the type from the container
        # Then call cls(**resolved_params)
        ...
```

## What's Next

In [Kata 20 -- Design Patterns](./20-design-patterns.md), we'll explore the classic patterns that build on SOLID -- Strategy, Observer, Factory, and Decorator. You've already seen several of these emerge naturally from SOLID principles; now we'll formalize them and see how Python's dynamic features make many patterns simpler than their Java/C++ originals.

---

[prev: 18-interface-segregation](./18-interface-segregation.md) | [next: 20-design-patterns](./20-design-patterns.md)
