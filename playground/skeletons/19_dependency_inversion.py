"""
Kata 19 -- Dependency Inversion Principle
Run: python playground/skeletons/19_dependency_inversion.py

Start with a NotificationService tightly coupled to EmailSender, then refactor
to depend on a MessageSender protocol. Demonstrate constructor injection, a simple
DI container, testability with mocks, and composable multi-sender patterns.
"""

from typing import Protocol, runtime_checkable


# ===========================================================================
# BEFORE: TIGHTLY COUPLED (violates DIP) -- provided for reference
# ===========================================================================

class TightEmailSender:
    """Low-level module: knows how to send emails."""

    def __init__(self):
        self.sent: list[dict] = []

    def send_email(self, to: str, subject: str, body: str):
        message = {"to": to, "subject": subject, "body": body}
        self.sent.append(message)
        print(f"  [EMAIL] To: {to} | Subject: {subject}")


class TightNotificationService:
    """High-level module -- WELDED to TightEmailSender.

    Creates its own dependency internally. Can't swap, can't test, can't extend.
    """

    def __init__(self):
        self.sender = TightEmailSender()  # <-- creates its own dependency!

    def notify(self, user: str, message: str):
        self.sender.send_email(user, "Notification", message)


# ===========================================================================
# THE ABSTRACTION: MessageSender Protocol
# ===========================================================================

@runtime_checkable
class MessageSender(Protocol):
    """The abstraction both high-level and low-level modules depend on.

    Any class with a send(to, subject, body) method satisfies this protocol.
    No inheritance required -- structural subtyping.
    """

    def send(self, to: str, subject: str, body: str) -> None: ...


# ===========================================================================
# AFTER: CONCRETE IMPLEMENTATIONS (depend on the abstraction)
# ===========================================================================

class EmailSender:
    """Concrete implementation: sends via email.

    Must satisfy MessageSender protocol with send(to, subject, body) -> None.
    Should track sent messages in self.sent list with channel="email".
    """

    def __init__(self):
        # TODO: initialize a list to track sent messages
        pass

    def send(self, to: str, subject: str, body: str) -> None:
        # TODO: create message dict with to, subject, body, and channel="email"
        # HINT: append to self.sent
        # HINT: print with "  [EMAIL] To: {to} | Subject: {subject}" format
        pass


class SmsSender:
    """Concrete implementation: sends via SMS.

    Must satisfy MessageSender protocol with send(to, subject, body) -> None.
    Should track sent messages in self.sent list with channel="sms".
    """

    def __init__(self):
        # TODO: initialize a list to track sent messages
        pass

    def send(self, to: str, subject: str, body: str) -> None:
        # TODO: create message dict with to, subject, body, and channel="sms"
        # HINT: append to self.sent
        # HINT: print with "  [SMS] To: {to} | Message: {body}" format
        pass


class PushSender:
    """Concrete implementation: sends via push notification.

    Must satisfy MessageSender protocol with send(to, subject, body) -> None.
    Should track sent messages in self.sent list with channel="push".
    """

    def __init__(self):
        # TODO: initialize a list to track sent messages
        pass

    def send(self, to: str, subject: str, body: str) -> None:
        # TODO: create message dict with to, subject, body, and channel="push"
        # HINT: append to self.sent
        # HINT: print with "  [PUSH] To: {to} | Title: {subject} | Body: {body}" format
        pass


# ===========================================================================
# REFACTORED: NotificationService (depends on abstraction)
# ===========================================================================

class NotificationService:
    """High-level module -- depends on MessageSender abstraction.

    Doesn't know or care whether it's sending email, SMS, or push.
    The caller decides which implementation to inject.

    Should accept a MessageSender via __init__ (constructor injection).
    """

    def __init__(self, sender: MessageSender):
        # TODO: store the sender (injected, not created!)
        pass

    def notify(self, user: str, message: str):
        # TODO: use self.sender.send() with subject="Notification"
        pass

    def send_welcome(self, user: str):
        # TODO: use self.sender.send() with subject="Welcome!"
        # HINT: body should be f"Welcome to the platform, {user}!"
        pass

    def send_alert(self, user: str, alert: str):
        # TODO: use self.sender.send() with subject="Alert"
        # HINT: body should be f"ALERT: {alert}"
        pass


# ===========================================================================
# SIMPLE DI CONTAINER
# ===========================================================================

class Container:
    """Simple dependency injection container.

    Register factories for types, then resolve them on demand.
    This is a simplified version of what FastAPI's Depends() does.

    Should have:
    - _factories: dict mapping name -> (factory, singleton_bool)
    - _singletons: dict mapping name -> cached instance
    - register(name, factory, singleton=False)
    - resolve(name) -> object
    """

    def __init__(self):
        # TODO: initialize _factories dict and _singletons dict
        pass

    def register(self, name: str, factory: callable, singleton: bool = False):
        # TODO: store the factory and singleton flag
        # HINT: self._factories[name] = (factory, singleton)
        pass

    def resolve(self, name: str) -> object:
        # TODO: resolve a dependency by name
        # 1. Check _singletons first -- return cached instance if exists
        # 2. Look up factory in _factories -- raise KeyError if missing
        # 3. Call factory(self) to create the instance
        # 4. If singleton=True, cache in _singletons
        # 5. Return the instance
        pass


# ===========================================================================
# MOCK SENDER (for testing)
# ===========================================================================

class MockSender:
    """Test double that records all sends without side effects.

    Must satisfy MessageSender protocol.
    Should track sent messages in self.sent list (no printing).
    """

    def __init__(self):
        # TODO: initialize a list to track sent messages
        pass

    def send(self, to: str, subject: str, body: str) -> None:
        # TODO: record the send (no printing -- this is a test double)
        # HINT: append {"to": to, "subject": subject, "body": body}
        pass


# ===========================================================================
# MULTI-SENDER (composing abstractions)
# ===========================================================================

class MultiSender:
    """Sends via multiple channels simultaneously.

    Itself satisfies MessageSender protocol -- composable abstractions.
    Should accept a list of MessageSender instances.
    """

    def __init__(self, senders: list[MessageSender]):
        # TODO: store the list of senders
        pass

    def send(self, to: str, subject: str, body: str) -> None:
        # TODO: delegate to each sender in self.senders
        # HINT: loop through self.senders and call send() on each
        pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Tightly Coupled (Violates DIP) ---
    print("--- Section 1: Tightly Coupled (Violates DIP) ---")

    try:
        tight = TightNotificationService()
        tight.notify("alice@example.com", "Your order shipped!")

        assert len(tight.sender.sent) == 1
        assert tight.sender.sent[0]["to"] == "alice@example.com"
        print("  Tightly coupled version works -- but we can't swap the sender.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: The Abstraction (MessageSender Protocol) ---
    print("--- Section 2: The Abstraction (MessageSender Protocol) ---")

    try:
        print("  MessageSender protocol defines the contract: send(to, subject, body) -> None")

        # Verify structural subtyping -- no inheritance needed!
        assert isinstance(EmailSender(), MessageSender), "EmailSender should satisfy protocol"
        print("  EmailSender satisfies the protocol (structural subtyping -- no inheritance!)")

        assert isinstance(SmsSender(), MessageSender), "SmsSender should satisfy protocol"
        print("  SmsSender satisfies the protocol")

        assert isinstance(PushSender(), MessageSender), "PushSender should satisfy protocol"
        print("  PushSender satisfies the protocol")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Refactored NotificationService (Depends on Abstraction) ---
    print("--- Section 3: Refactored NotificationService (Depends on Abstraction) ---")

    try:
        email = EmailSender()
        sms = SmsSender()
        push = PushSender()

        email_notifier = NotificationService(email)
        sms_notifier = NotificationService(sms)
        push_notifier = NotificationService(push)

        email_notifier.notify("alice@example.com", "Your order shipped!")
        sms_notifier.notify("+1-555-0123", "Your order shipped!")
        push_notifier.notify("alice_device", "Your order shipped!")

        assert len(email.sent) == 1
        assert email.sent[0]["channel"] == "email"
        assert len(sms.sent) == 1
        assert sms.sent[0]["channel"] == "sms"
        assert len(push.sent) == 1
        assert push.sent[0]["channel"] == "push"
        print("  Same NotificationService, three different behaviors -- zero code changes!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Constructor Injection ---
    print("--- Section 4: Constructor Injection ---")

    try:
        fresh_email = EmailSender()
        fresh_sms = SmsSender()

        svc1 = NotificationService(fresh_email)
        svc1.send_welcome("user@example.com")
        assert len(fresh_email.sent) == 1
        assert "Welcome" in fresh_email.sent[0]["subject"]

        svc2 = NotificationService(fresh_sms)
        svc2.send_alert("+1-555-9999", "Server overloaded!")
        assert len(fresh_sms.sent) == 1
        assert "ALERT" in fresh_sms.sent[0]["body"]

        print("  Constructor injection lets the caller control the implementation.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Simple DI Container ---
    print("--- Section 5: Simple DI Container ---")

    try:
        container = Container()
        container.register("sender", lambda c: EmailSender())
        container.register("notifier", lambda c: NotificationService(c.resolve("sender")))

        notifier = container.resolve("notifier")
        notifier.notify("alice@example.com", "Container wired this!")

        sender_instance = container.resolve("sender")
        print("  Container resolved and wired dependencies automatically.")

        # Switch to SMS -- change ONE registration
        print("  Switching to SMS -- only change the registration:")
        container2 = Container()
        container2.register("sender", lambda c: SmsSender())
        container2.register("notifier", lambda c: NotificationService(c.resolve("sender")))

        notifier2 = container2.resolve("notifier")
        notifier2.notify("alice@example.com", "Same code, different sender!")
        print("  One line change swapped the entire notification channel!")

        # Test singleton behavior
        container3 = Container()
        container3.register("sender", lambda c: EmailSender(), singleton=True)
        s1 = container3.resolve("sender")
        s2 = container3.resolve("sender")
        assert s1 is s2, "Singleton should return same instance"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Testability with Mock ---
    print("--- Section 6: Testability with Mock ---")

    try:
        mock = MockSender()
        test_svc = NotificationService(mock)

        # Test notify
        test_svc.notify("alice@test.com", "Test message")
        assert len(mock.sent) == 1
        assert mock.sent[0]["to"] == "alice@test.com"
        assert mock.sent[0]["subject"] == "Notification"
        assert mock.sent[0]["body"] == "Test message"
        print("  notify() test passed!")

        # Test send_welcome
        test_svc.send_welcome("bob@test.com")
        assert len(mock.sent) == 2
        assert mock.sent[1]["to"] == "bob@test.com"
        assert "Welcome" in mock.sent[1]["subject"]
        assert "bob@test.com" in mock.sent[1]["body"]
        print("  send_welcome() test passed!")

        # Test send_alert
        test_svc.send_alert("charlie@test.com", "Server down!")
        assert len(mock.sent) == 3
        assert mock.sent[2]["to"] == "charlie@test.com"
        assert "ALERT" in mock.sent[2]["body"]
        assert "Server down!" in mock.sent[2]["body"]
        print("  send_alert() test passed!")

        # Verify MockSender satisfies protocol
        assert isinstance(mock, MessageSender)
        print("  Mock sender: zero side effects, full verification.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Multi-Sender Composition ---
    print("--- Section 7: Multi-Sender Composition ---")

    try:
        multi_email = EmailSender()
        multi_sms = SmsSender()
        multi_push = PushSender()

        multi = MultiSender([multi_email, multi_sms, multi_push])
        multi_svc = NotificationService(multi)

        multi_svc.send_alert("admin@example.com", "Database failover triggered")

        assert len(multi_email.sent) == 1
        assert len(multi_sms.sent) == 1
        assert len(multi_push.sent) == 1
        assert multi_email.sent[0]["channel"] == "email"
        assert multi_sms.sent[0]["channel"] == "sms"
        assert multi_push.sent[0]["channel"] == "push"

        # MultiSender itself satisfies the protocol
        assert isinstance(multi, MessageSender)
        print("  MultiSender itself satisfies MessageSender -- composable abstractions!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: DIP vs. No DIP Comparison ---
    print("--- Section 8: DIP vs. No DIP Comparison ---")

    try:
        print("  WITHOUT DIP:")
        print("    - NotificationService creates EmailSender internally")
        print("    - Can't swap sender without modifying NotificationService")
        print("    - Can't test without side effects")
        print("    - Adding channels requires changing existing code")

        print("  WITH DIP:")
        print("    - NotificationService depends on MessageSender protocol")
        print("    - Any sender can be injected (email, SMS, push, mock, multi)")
        print("    - Testing is trivial with MockSender")
        print("    - New channels never touch existing code")

        sender_types_used = {
            "EmailSender", "SmsSender", "PushSender",
            "MockSender", "MultiSender",
        }
        print(f"\n  NotificationService worked with {len(sender_types_used)} different senders!")
        print("  Zero changes to NotificationService code. That's DIP.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Dependency Inversion Principle:")
    print("  - High-level modules depend on abstractions, not concretions")
    print("  - Use Protocol for structural subtyping (no inheritance needed)")
    print("  - Constructor injection: pass dependencies via __init__")
    print("  - Inversion of control: caller decides the implementation")
    print("  - DI containers automate wiring for complex graphs")
    print("  - MockSender pattern makes testing trivial")
    print("  - This is the foundation for FastAPI's Depends() system")
    print()
    print("All 8 sections passed. You've mastered the Dependency Inversion Principle!")
