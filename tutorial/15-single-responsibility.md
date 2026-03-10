# Kata 15 -- Single Responsibility Principle

[prev: 14-abstract-base-classes](./14-abstract-base-classes.md) | [next: 16-open-closed](./16-open-closed.md)

---

## What We're Building

The **Single Responsibility Principle** (SRP) is the first of the five SOLID principles. It states: *a class should have only one reason to change*. In practice, this means each class should own exactly one responsibility -- one piece of the system's behavior.

In this kata we'll start with a realistic "god class" -- a `UserManager` that handles authentication, email notifications, database persistence, and logging all in one place. We'll identify each responsibility, extract it into a focused class, and prove through tests that the refactored version is easier to test, maintain, and extend.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Single Responsibility Principle | One class = one reason to change | Always -- it's the foundation of good OOP |
| Cohesion | How closely related a class's methods are | Measuring whether a class does too much |
| God class | A class that knows and does too much | Recognizing the anti-pattern to refactor |
| Dependency injection | Pass collaborators in, don't create them | Decoupling classes for testability |
| Interface segregation (preview) | Depend on narrow interfaces, not fat classes | Designing collaborator contracts |
| Test doubles | Fakes/stubs replacing real collaborators | Testing classes in isolation |

## The Code

### Step 1: The "god class" -- everything in one place

Here's a `UserManager` that handles four completely separate concerns. This is disturbingly common in real codebases:

```python
import hashlib
import json
import os
from datetime import datetime


class UserManager:
    """Does EVERYTHING related to users. This is the problem."""

    def __init__(self, db_path: str = "users.json"):
        self.db_path = db_path
        self.log_file = "app.log"
        self.users: dict[str, dict] = {}
        self._load_db()

    # --- Database responsibility ---
    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path) as f:
                self.users = json.load(f)

    def _save_db(self):
        with open(self.db_path, "w") as f:
            json.dump(self.users, f, indent=2)

    # --- Authentication responsibility ---
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str, email: str) -> bool:
        if username in self.users:
            self._log(f"Registration failed: {username} already exists")
            return False

        self.users[username] = {
            "password_hash": self._hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
        }
        self._save_db()
        self._log(f"User registered: {username}")
        self._send_email(email, "Welcome!", f"Welcome to the app, {username}!")
        return True

    def login(self, username: str, password: str) -> bool:
        user = self.users.get(username)
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
        # In production this would use smtplib
        print(f"  [EMAIL] To: {to} | Subject: {subject} | Body: {body}")
        self._log(f"Email sent to {to}: {subject}")

    # --- Logging responsibility ---
    def _log(self, message: str):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] {message}"
        print(f"  [LOG] {entry}")
        with open(self.log_file, "a") as f:
            f.write(entry + "\n")
```

### Step 2: Identifying the responsibilities

Look at the methods and ask: *if I change how we send emails, which methods change? If I switch the database, which methods change?* Each group of methods that changes together is a separate responsibility.

| Responsibility | Methods | Reason to Change |
|---|---|---|
| **Authentication** | `register`, `login`, `_hash_password` | Auth rules change (e.g., add password validation, 2FA) |
| **Persistence** | `_load_db`, `_save_db` | Storage backend changes (JSON to SQLite, Postgres, etc.) |
| **Email** | `_send_email` | Email provider changes (SMTP, SendGrid, SES) |
| **Logging** | `_log` | Logging format or destination changes (file, stdout, remote) |

Four reasons to change = four responsibilities = four classes.

### Step 3: Measuring cohesion

**Cohesion** measures how strongly related the methods of a class are. A highly cohesive class has methods that all work on the same data toward the same purpose. The god class has low cohesion -- `_send_email` has nothing to do with `_load_db`.

A quick heuristic: *if you can split a class into groups of methods that don't call each other, those groups are separate responsibilities.*

### Step 4: Extract the collaborators

Each responsibility becomes its own class with a clean interface:

```python
from datetime import datetime


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
```

Each class is focused. `UserRepository` only knows about storing and retrieving users. `EmailService` only knows about sending messages. `Logger` only knows about recording entries.

### Step 5: The refactored UserService

Now `UserService` (renamed from `UserManager` -- "manager" is a smell) has exactly one job: **coordinating user operations**. It delegates everything else:

```python
import hashlib
from datetime import datetime


class UserService:
    """Responsibility: user business logic (auth + coordination)."""

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
```

Notice what changed:

- **No file I/O in UserService** -- that's the repository's job
- **No email logic in UserService** -- that's the email service's job
- **No logging format logic in UserService** -- that's the logger's job
- **Collaborators are injected** via `__init__` -- not created internally

### Step 6: Why this is more testable

The god class was nearly impossible to unit test without side effects. Every call to `register()` hit the filesystem (JSON and log file) and tried to send email. The refactored version lets you inject test doubles:

```python
def test_registration():
    """Test registration WITHOUT touching filesystem or sending email."""
    logger = Logger()
    repo = UserRepository()
    email_svc = EmailService(logger)

    service = UserService(repo, email_svc, logger)

    # Register a new user
    result = service.register("alice", "secret123", "alice@example.com")
    assert result is True
    assert repo.exists("alice")
    assert len(email_svc.sent) == 1
    assert email_svc.sent[0]["to"] == "alice@example.com"

    # Try to register the same user again
    result = service.register("alice", "other", "alice2@example.com")
    assert result is False
    assert len(email_svc.sent) == 1  # No duplicate email

    print("  Registration tests passed!")


def test_login():
    """Test login in isolation."""
    logger = Logger()
    repo = UserRepository()
    email_svc = EmailService(logger)

    service = UserService(repo, email_svc, logger)
    service.register("bob", "mypassword", "bob@example.com")

    assert service.login("bob", "mypassword") is True
    assert service.login("bob", "wrongpassword") is False
    assert service.login("nobody", "whatever") is False

    print("  Login tests passed!")
```

No temp files. No mocking `smtplib`. No cleaning up after tests. Each collaborator is a simple in-memory object that you can inspect after the test.

### Step 7: The cohesion test

How do we know the refactored version is better? Count how many instance variables each method touches:

**Before (UserManager):**
- `register()` touches: `self.users`, `self.db_path`, `self.log_file` -- 3 variables, 3 responsibilities
- `_send_email()` touches: `self.log_file` -- unrelated to user data
- `_load_db()` touches: `self.db_path`, `self.users` -- unrelated to auth

**After (UserService):**
- `register()` touches: `self.repo`, `self.email`, `self.logger` -- all collaborators for the one job of coordinating
- Each collaborator only touches its own state

High cohesion = each class's methods all work with the same data.

### Step 8: Real-world SRP examples

SRP isn't just about user management. Here are patterns you'll see everywhere:

**HTTP handler vs. business logic:**
```python
# BAD: handler does validation, business logic, and response formatting
class OrderHandler:
    def handle(self, request):
        # validate input (responsibility 1)
        # check inventory (responsibility 2)
        # charge payment (responsibility 3)
        # send confirmation (responsibility 4)
        # format response (responsibility 5)
        ...

# GOOD: handler coordinates, specialists execute
class OrderHandler:
    def __init__(self, validator, inventory, payments, notifications):
        ...

    def handle(self, request):
        data = self.validator.validate(request)
        self.inventory.reserve(data.items)
        self.payments.charge(data.payment)
        self.notifications.send_confirmation(data.email)
```

**File parser vs. data processor:**
```python
# BAD: one class parses CSV AND computes statistics
class DataAnalyzer:
    def load_csv(self, path): ...
    def compute_mean(self): ...
    def generate_report(self): ...

# GOOD: separate concerns
class CsvReader:
    def read(self, path) -> list[dict]: ...

class StatisticsEngine:
    def compute(self, data) -> Stats: ...

class ReportGenerator:
    def generate(self, stats) -> str: ...
```

## Playground

Run the full before/after comparison with tests:

```bash
python playground/15_single_responsibility.py
```

```
--- Section 1: The God Class (Before SRP) ---
  [LOG] [2026-03-10T...] User registered: alice
  [EMAIL] To: alice@example.com | Subject: Welcome! | Body: Welcome to the app, alice!
  [LOG] [2026-03-10T...] Email sent to alice@example.com: Welcome!
  [LOG] [2026-03-10T...] Login successful: alice
  God class works -- but it's a tangled mess of responsibilities.

--- Section 2: Identifying Responsibilities ---
  UserManager has 4 responsibilities:
    1. Authentication (register, login, _hash_password)
    2. Persistence (_load_db, _save_db)
    3. Email (_send_email)
    4. Logging (_log)
  That's 4 reasons to change -- SRP says there should be 1.

--- Section 3: Extracted Collaborators ---
  Logger created -- single responsibility: recording events
  EmailService created -- single responsibility: sending notifications
  UserRepository created -- single responsibility: persisting user data

--- Section 4: Refactored UserService ---
  [LOG] [2026-03-10T...] User registered: charlie
  [EMAIL] To: charlie@example.com | Subject: Welcome! | Body: Welcome to the app, charlie!
  [LOG] [2026-03-10T...] Email sent to charlie@example.com: Welcome!
  [LOG] [2026-03-10T...] Login successful: charlie
  Refactored version works with same external behavior!

--- Section 5: Testability Comparison ---
  Registration tests passed!
  Login tests passed!
  Duplicate registration test passed!
  Logger isolation test passed!
  Repository isolation test passed!
  Email isolation test passed!

--- Section 6: Cohesion Measurement ---
  UserManager (god class) cohesion score: LOW
    - register() touches 4 concerns
    - _send_email() unrelated to auth
    - _load_db() unrelated to email
  UserService (refactored) cohesion score: HIGH
    - register() delegates to focused collaborators
    - Each collaborator owns exactly one concern

--- Summary ---
Single Responsibility Principle:
  - One class = one reason to change
  - God classes are a sign of SRP violation
  - Extract collaborators for each responsibility
  - Inject dependencies -- don't create them internally
  - High cohesion = methods work on the same data
  - SRP makes code testable, maintainable, and extensible

All 6 sections passed. You've mastered the Single Responsibility Principle!
```

## How It Works

```
BEFORE (God Class):                    AFTER (SRP):

+-------------------+                 +---------------+
|   UserManager     |                 |  UserService  |
|                   |                 | (coordination)|
| - register()      |                 +-------+-------+
| - login()         |                         |
| - _hash_password()|                +--------+--------+--------+
| - _load_db()      |                |        |        |        |
| - _save_db()      |          +-----+--+ +---+---+ +-+------+ |
| - _send_email()   |          | User   | | Email | | Logger | |
| - _log()          |          | Repo   | | Svc   | |        | |
|                   |          +--------+ +-------+ +--------+ |
| 4 reasons to      |                                          |
|   change           |          Each class: 1 reason to change  |
+-------------------+
```

The key insight: **the god class changes whenever ANY of its four responsibilities change**. The refactored version localizes change -- switching from JSON to SQLite only touches `UserRepository`. Switching from SMTP to SendGrid only touches `EmailService`. No other class needs modification.

## Exercises

### Exercise 1: Extract a password policy

The `_hash_password` method lives in `UserService`, but password policy (minimum length, complexity rules) is its own responsibility. Extract a `PasswordHasher` class:

```python
class PasswordHasher:
    """Responsibility: password hashing and validation."""

    def hash(self, password: str) -> str:
        """Hash a password."""
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        ...

    def validate(self, password: str) -> tuple[bool, str]:
        """Check password meets policy (min 8 chars, has digit)."""
        ...

# Update UserService to use PasswordHasher
service = UserService(repo, email_svc, logger, password_hasher)
```

### Exercise 2: Build a notification hub

Replace the single `EmailService` with a `NotificationHub` that supports multiple channels. Each channel is its own class (SRP), and the hub coordinates:

```python
class NotificationChannel:
    """Base for all notification channels."""
    def send(self, to: str, subject: str, body: str): ...

class EmailChannel(NotificationChannel): ...
class SmsChannel(NotificationChannel): ...
class PushChannel(NotificationChannel): ...

class NotificationHub:
    """Coordinates sending across channels -- but doesn't know HOW each sends."""
    def __init__(self, channels: list[NotificationChannel]): ...
    def notify(self, to: str, subject: str, body: str): ...
```

## What's Next

In [Kata 16 -- Open/Closed Principle](./16-open-closed.md), we'll tackle the second SOLID principle: software entities should be open for extension but closed for modification. You'll learn to design systems where adding new behavior never requires changing existing code -- using abstract base classes, the strategy pattern, and plugin architectures.

---

[prev: 14-abstract-base-classes](./14-abstract-base-classes.md) | [next: 16-open-closed](./16-open-closed.md)
