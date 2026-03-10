"""
Kata 15 -- Single Responsibility Principle
Run: python playground/15_single_responsibility.py

Start with a monolithic "god class" that handles auth, email, database, and logging
all in one place -- then refactor into focused, testable classes that each own one
responsibility.
"""

import hashlib
from datetime import datetime


# ===========================================================================
# BEFORE: THE GOD CLASS (violates SRP)
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
# AFTER: REFACTORED (each class has one responsibility)
# ===========================================================================

class Logger:
    """Responsibility: recording events."""

    def __init__(self):
        self.entries: list[str] = []

    def log(self, message: str):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] {message}"
        self.entries.append(entry)
        print(f"  [LOG] {entry}")


class EmailService:
    """Responsibility: sending notifications."""

    def __init__(self, logger: Logger):
        self.logger = logger
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str):
        email = {"to": to, "subject": subject, "body": body}
        self.sent.append(email)
        print(f"  [EMAIL] To: {to} | Subject: {subject} | Body: {body}")
        self.logger.log(f"Email sent to {to}: {subject}")


class UserRepository:
    """Responsibility: persisting user data."""

    def __init__(self):
        self.users: dict[str, dict] = {}

    def exists(self, username: str) -> bool:
        return username in self.users

    def get(self, username: str) -> dict | None:
        return self.users.get(username)

    def save(self, username: str, data: dict):
        self.users[username] = data

    def all(self) -> dict[str, dict]:
        return dict(self.users)


class UserService:
    """Responsibility: user business logic (auth coordination).

    Delegates persistence, email, and logging to focused collaborators.
    """

    def __init__(self, repo: UserRepository, email: EmailService, logger: Logger):
        self.repo = repo
        self.email = email
        self.logger = logger

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str, email: str) -> bool:
        if self.repo.exists(username):
            self.logger.log(f"Registration failed: {username} already exists")
            return False

        self.repo.save(username, {
            "password_hash": self._hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
        })
        self.logger.log(f"User registered: {username}")
        self.email.send(email, "Welcome!", f"Welcome to the app, {username}!")
        return True

    def login(self, username: str, password: str) -> bool:
        user = self.repo.get(username)
        if not user:
            self.logger.log(f"Login failed: {username} not found")
            return False

        if user["password_hash"] != self._hash_password(password):
            self.logger.log(f"Login failed: wrong password for {username}")
            return False

        self.logger.log(f"Login successful: {username}")
        return True


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The God Class (Before SRP) ---
    print("--- Section 1: The God Class (Before SRP) ---")

    mgr = UserManager()
    mgr.register("alice", "password123", "alice@example.com")
    mgr.login("alice", "password123")

    assert mgr._user_exists("alice")
    assert mgr.login("alice", "password123") is True
    assert mgr.login("alice", "wrongpass") is False
    assert len(mgr.sent_emails) == 1
    assert mgr.sent_emails[0]["to"] == "alice@example.com"
    print("  God class works -- but it's a tangled mess of responsibilities.")

    print()

    # --- Section 2: Identifying Responsibilities ---
    print("--- Section 2: Identifying Responsibilities ---")

    # Count the distinct responsibilities in UserManager
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

    # Verify all methods exist on the god class
    for methods in responsibilities.values():
        for method in methods:
            assert hasattr(mgr, method), f"Missing method: {method}"

    print()

    # --- Section 3: Extracted Collaborators ---
    print("--- Section 3: Extracted Collaborators ---")

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

    print()

    # --- Section 4: Refactored UserService ---
    print("--- Section 4: Refactored UserService ---")

    service = UserService(repo, email_svc, logger)

    result = service.register("charlie", "securepass", "charlie@example.com")
    assert result is True
    assert repo.exists("charlie")

    result = service.login("charlie", "securepass")
    assert result is True

    assert len(email_svc.sent) == 1
    assert email_svc.sent[0]["to"] == "charlie@example.com"
    print("  Refactored version works with same external behavior!")

    print()

    # --- Section 5: Testability Comparison ---
    print("--- Section 5: Testability Comparison ---")

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

    print()

    # --- Section 6: Cohesion Measurement ---
    print("--- Section 6: Cohesion Measurement ---")

    # Measure cohesion: what instance variables does each method touch?
    print("  UserManager (god class) cohesion score: LOW")
    print("    - register() touches 4 concerns")
    print("    - _send_email() unrelated to auth")
    print("    - _load_db() unrelated to email")

    # Count methods per class in refactored version
    refactored_classes = {
        "Logger": Logger,
        "EmailService": EmailService,
        "UserRepository": UserRepository,
        "UserService": UserService,
    }

    print("  UserService (refactored) cohesion score: HIGH")
    print("    - register() delegates to focused collaborators")
    print("    - Each collaborator owns exactly one concern")

    # Verify each refactored class has a focused interface
    assert len([m for m in dir(Logger) if not m.startswith("_")]) <= 3
    assert len([m for m in dir(EmailService) if not m.startswith("_")]) <= 4
    assert len([m for m in dir(UserRepository) if not m.startswith("_")]) <= 5
    assert len([m for m in dir(UserService) if not m.startswith("_")]) <= 5

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
