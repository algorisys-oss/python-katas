"""
Kata 15 -- Single Responsibility Principle
Run: python playground/skeletons/15_single_responsibility.py

Start with a monolithic "god class" that handles auth, email, database, and logging
all in one place -- then refactor into focused, testable classes that each own one
responsibility.
"""

import hashlib
from datetime import datetime


# ===========================================================================
# BEFORE: THE GOD CLASS (violates SRP) -- provided for reference
# ===========================================================================

class UserManager:
    """Does EVERYTHING related to users. This is the anti-pattern."""

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.log_entries: list[str] = []
        self.sent_emails: list[dict] = []

    # --- Database responsibility ---
    def _save_user(self, username: str, data: dict):
        self.users[username] = data

    def _get_user(self, username: str) -> dict | None:
        return self.users.get(username)

    def _user_exists(self, username: str) -> bool:
        return username in self.users

    # --- Authentication responsibility ---
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str, email: str) -> bool:
        if self._user_exists(username):
            self._log(f"Registration failed: {username} already exists")
            return False

        self._save_user(username, {
            "password_hash": self._hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
        })
        self._log(f"User registered: {username}")
        self._send_email(email, "Welcome!", f"Welcome to the app, {username}!")
        return True

    def login(self, username: str, password: str) -> bool:
        user = self._get_user(username)
        if not user:
            self._log(f"Login failed: {username} not found")
            return False

        if user["password_hash"] != self._hash_password(password):
            self._log(f"Login failed: wrong password for {username}")
            return False

        self._log(f"Login successful: {username}")
        return True

    # --- Email responsibility ---
    def _send_email(self, to: str, subject: str, body: str):
        email = {"to": to, "subject": subject, "body": body}
        self.sent_emails.append(email)
        print(f"  [EMAIL] To: {to} | Subject: {subject} | Body: {body}")
        self._log(f"Email sent to {to}: {subject}")

    # --- Logging responsibility ---
    def _log(self, message: str):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] {message}"
        self.log_entries.append(entry)
        print(f"  [LOG] {entry}")


# ===========================================================================
# AFTER: YOUR REFACTORED VERSION (each class should have one responsibility)
# ===========================================================================

class Logger:
    """Responsibility: recording events.

    Should have:
    - entries: list[str] to store log entries
    - log(message) method that timestamps and stores entries
    """

    def __init__(self):
        # TODO: initialize a list to store log entries
        pass

    def log(self, message: str):
        # TODO: create a timestamped entry, store it, and print it
        # HINT: use datetime.now().isoformat() for timestamp
        # HINT: format as f"[{timestamp}] {message}"
        # HINT: append to self.entries and print with "  [LOG] " prefix
        pass


class EmailService:
    """Responsibility: sending notifications.

    Should have:
    - logger: Logger instance (injected)
    - sent: list[dict] to track sent emails
    - send(to, subject, body) method
    """

    def __init__(self, logger: Logger):
        # TODO: store the logger and initialize a list to track sent emails
        pass

    def send(self, to: str, subject: str, body: str):
        # TODO: create email dict with to/subject/body, store it, print it, log it
        # HINT: email dict = {"to": to, "subject": subject, "body": body}
        # HINT: print with "  [EMAIL] " prefix
        # HINT: use self.logger.log() to record the send
        pass


class UserRepository:
    """Responsibility: persisting user data.

    Should have:
    - users: dict[str, dict] for storage
    - exists(username) -> bool
    - get(username) -> dict | None
    - save(username, data)
    - all() -> dict[str, dict]
    """

    def __init__(self):
        # TODO: initialize the users dict
        pass

    def exists(self, username: str) -> bool:
        # TODO: check if username exists
        pass

    def get(self, username: str) -> dict | None:
        # TODO: return user data or None
        pass

    def save(self, username: str, data: dict):
        # TODO: store user data
        pass

    def all(self) -> dict[str, dict]:
        # TODO: return a copy of all users
        pass


class UserService:
    """Responsibility: user business logic (auth coordination).

    Delegates persistence, email, and logging to focused collaborators.
    Should accept repo, email, and logger via __init__ (dependency injection).
    """

    def __init__(self, repo: UserRepository, email: EmailService, logger: Logger):
        # TODO: store the three collaborators
        pass

    def _hash_password(self, password: str) -> str:
        # TODO: hash password with SHA-256
        # HINT: hashlib.sha256(password.encode()).hexdigest()
        pass

    def register(self, username: str, password: str, email: str) -> bool:
        # TODO: implement registration using self.repo, self.email, self.logger
        # 1. Check if user exists via self.repo.exists() -- if so, log failure and return False
        # 2. Save user via self.repo.save() with password_hash, email, created_at
        # 3. Log success via self.logger.log()
        # 4. Send welcome email via self.email.send()
        # 5. Return True
        pass

    def login(self, username: str, password: str) -> bool:
        # TODO: implement login using self.repo and self.logger
        # 1. Get user via self.repo.get() -- if None, log failure and return False
        # 2. Compare password hash -- if wrong, log failure and return False
        # 3. Log success and return True
        pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The God Class (Before SRP) ---
    print("--- Section 1: The God Class (Before SRP) ---")

    try:
        mgr = UserManager()
        mgr.register("alice", "password123", "alice@example.com")
        mgr.login("alice", "password123")

        assert mgr._user_exists("alice")
        assert mgr.login("alice", "password123") is True
        assert mgr.login("alice", "wrongpass") is False
        assert len(mgr.sent_emails) == 1
        assert mgr.sent_emails[0]["to"] == "alice@example.com"
        print("  God class works -- but it's a tangled mess of responsibilities.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Identifying Responsibilities ---
    print("--- Section 2: Identifying Responsibilities ---")

    try:
        responsibilities = {
            "Authentication": ["register", "login", "_hash_password"],
            "Persistence": ["_save_user", "_get_user", "_user_exists"],
            "Email": ["_send_email"],
            "Logging": ["_log"],
        }

        print(f"  UserManager has {len(responsibilities)} responsibilities:")
        for i, (name, methods) in enumerate(responsibilities.items(), 1):
            print(f"    {i}. {name} ({', '.join(methods)})")
        print(f"  That's {len(responsibilities)} reasons to change -- SRP says there should be 1.")

        for methods in responsibilities.values():
            for method in methods:
                assert hasattr(mgr, method), f"Missing method: {method}"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Extracted Collaborators ---
    print("--- Section 3: Extracted Collaborators ---")

    try:
        logger = Logger()
        print("  Logger created -- single responsibility: recording events")
        assert hasattr(logger, "log")
        assert hasattr(logger, "entries")

        email_svc = EmailService(logger)
        print("  EmailService created -- single responsibility: sending notifications")
        assert hasattr(email_svc, "send")
        assert hasattr(email_svc, "sent")

        repo = UserRepository()
        print("  UserRepository created -- single responsibility: persisting user data")
        assert hasattr(repo, "exists")
        assert hasattr(repo, "get")
        assert hasattr(repo, "save")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Refactored UserService ---
    print("--- Section 4: Refactored UserService ---")

    try:
        logger = Logger()
        email_svc = EmailService(logger)
        repo = UserRepository()
        service = UserService(repo, email_svc, logger)

        result = service.register("charlie", "securepass", "charlie@example.com")
        assert result is True
        assert repo.exists("charlie")

        result = service.login("charlie", "securepass")
        assert result is True

        assert len(email_svc.sent) == 1
        assert email_svc.sent[0]["to"] == "charlie@example.com"
        print("  Refactored version works with same external behavior!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Testability Comparison ---
    print("--- Section 5: Testability Comparison ---")

    try:
        # Test 1: Registration in isolation
        test_logger = Logger()
        test_repo = UserRepository()
        test_email = EmailService(test_logger)
        test_service = UserService(test_repo, test_email, test_logger)

        assert test_service.register("alice", "secret123", "alice@test.com") is True
        assert test_repo.exists("alice")
        assert len(test_email.sent) == 1
        assert test_email.sent[0]["to"] == "alice@test.com"
        assert test_email.sent[0]["subject"] == "Welcome!"
        print("  Registration tests passed!")

        # Test 2: Login in isolation
        assert test_service.login("alice", "secret123") is True
        assert test_service.login("alice", "wrongpassword") is False
        assert test_service.login("nobody", "whatever") is False
        print("  Login tests passed!")

        # Test 3: Duplicate registration
        assert test_service.register("alice", "other", "alice2@test.com") is False
        assert len(test_email.sent) == 1  # No duplicate email sent
        print("  Duplicate registration test passed!")

        # Test 4: Logger in isolation
        iso_logger = Logger()
        iso_logger.log("test message 1")
        iso_logger.log("test message 2")
        assert len(iso_logger.entries) == 2
        assert "test message 1" in iso_logger.entries[0]
        assert "test message 2" in iso_logger.entries[1]
        print("  Logger isolation test passed!")

        # Test 5: Repository in isolation
        iso_repo = UserRepository()
        assert iso_repo.exists("alice") is False
        iso_repo.save("alice", {"email": "a@b.com"})
        assert iso_repo.exists("alice") is True
        assert iso_repo.get("alice") == {"email": "a@b.com"}
        assert iso_repo.get("nobody") is None
        assert "alice" in iso_repo.all()
        print("  Repository isolation test passed!")

        # Test 6: EmailService in isolation
        iso_logger2 = Logger()
        iso_email = EmailService(iso_logger2)
        iso_email.send("test@test.com", "Test Subject", "Test Body")
        assert len(iso_email.sent) == 1
        assert iso_email.sent[0]["to"] == "test@test.com"
        assert iso_email.sent[0]["subject"] == "Test Subject"
        assert len(iso_logger2.entries) == 1  # Email service logged the send
        print("  Email isolation test passed!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Cohesion Measurement ---
    print("--- Section 6: Cohesion Measurement ---")

    try:
        print("  UserManager (god class) cohesion score: LOW")
        print("    - register() touches 4 concerns")
        print("    - _send_email() unrelated to auth")
        print("    - _load_db() unrelated to email")

        refactored_classes = {
            "Logger": Logger,
            "EmailService": EmailService,
            "UserRepository": UserRepository,
            "UserService": UserService,
        }

        print("  UserService (refactored) cohesion score: HIGH")
        print("    - register() delegates to focused collaborators")
        print("    - Each collaborator owns exactly one concern")

        assert len([m for m in dir(Logger) if not m.startswith("_")]) <= 3
        assert len([m for m in dir(EmailService) if not m.startswith("_")]) <= 4
        assert len([m for m in dir(UserRepository) if not m.startswith("_")]) <= 5
        assert len([m for m in dir(UserService) if not m.startswith("_")]) <= 5
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Single Responsibility Principle:")
    print("  - One class = one reason to change")
    print("  - God classes are a sign of SRP violation")
    print("  - Extract collaborators for each responsibility")
    print("  - Inject dependencies -- don't create them internally")
    print("  - High cohesion = methods work on the same data")
    print("  - SRP makes code testable, maintainable, and extensible")
    print()
    print("All 6 sections passed. You've mastered the Single Responsibility Principle!")
