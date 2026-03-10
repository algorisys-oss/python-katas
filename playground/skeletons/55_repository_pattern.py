"""
Kata 55 -- Repository Pattern
Run: python playground/skeletons/55_repository_pattern.py

Build a Repository pattern abstraction over SQLite. Generic base repository
with create/read/update/delete. Concrete repositories (UserRepository,
PostRepository). Decouples business logic from data access. Tests with
in-memory SQLite.

Completes within 5 seconds.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from typing import Any, Generic, Iterator, TypeVar


# ===========================================================================
# SECTION 1: Database Connection (reused from Kata 54)
# ===========================================================================

class Database:
    """Minimal database wrapper with context-managed connections."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Provide a cursor within a transaction."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ===========================================================================
# SECTION 2: Entity Models
# ===========================================================================

@dataclass
class User:
    """A user entity."""
    name: str
    email: str
    age: int = 0
    active: bool = True
    id: int | None = None


@dataclass
class Post:
    """A blog post entity."""
    title: str
    body: str
    user_id: int
    published: bool = False
    id: int | None = None


T = TypeVar("T")


# ===========================================================================
# SECTION 3: Abstract Repository
# ===========================================================================
# The abstract base defines the contract that all repositories must follow.

class AbstractRepository(ABC, Generic[T]):
    """Abstract repository defining the data access contract."""

    @abstractmethod
    def create(self, entity: T) -> T:
        """Persist a new entity and return it with its assigned ID."""
        ...

    @abstractmethod
    def find_by_id(self, entity_id: int) -> T | None:
        """Find an entity by its primary key."""
        ...

    @abstractmethod
    def find_all(self, **filters: Any) -> list[T]:
        """Find all entities, optionally filtered by field values."""
        ...

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        ...


# ===========================================================================
# SECTION 4: SQLite Base Repository
# ===========================================================================
# A concrete base that implements the repository contract using SQLite.

class SQLiteRepository(AbstractRepository[T], ABC):
    """Base SQLite repository with generic CRUD implementation.

    Subclasses must implement:
        - table_name, columns
        - _row_to_entity, _entity_to_values
        - create_table
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.create_table()

    @property
    @abstractmethod
    def table_name(self) -> str:
        ...

    @property
    @abstractmethod
    def columns(self) -> list[str]:
        ...

    @abstractmethod
    def _row_to_entity(self, row: sqlite3.Row) -> T:
        ...

    @abstractmethod
    def _entity_to_values(self, entity: T) -> dict[str, Any]:
        ...

    @abstractmethod
    def create_table(self) -> None:
        ...

    def create(self, entity: T) -> T:
        """Insert entity into the database and return it with its new ID."""
        values = self._entity_to_values(entity)
        # TODO: Build INSERT SQL with column names and ? placeholders
        # TODO: Execute the INSERT
        # TODO: Fetch the newly created row by lastrowid
        # TODO: Return _row_to_entity(row)
        pass  # type: ignore[return-value]

    def find_by_id(self, entity_id: int) -> T | None:
        """Find an entity by primary key."""
        # TODO: Execute SELECT * FROM table WHERE id = ?
        # TODO: Return _row_to_entity(row) if found, None otherwise
        pass

    def find_all(self, **filters: Any) -> list[T]:
        """Find all entities, optionally filtered."""
        sql = f"SELECT * FROM {self.table_name}"
        params: list[Any] = []

        if filters:
            # TODO: Validate filter keys against columns + {"id"}
            # TODO: Build WHERE clause with AND
            # TODO: Append values to params
            pass

        sql += " ORDER BY id"

        with self.db.transaction() as cursor:
            cursor.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        values = self._entity_to_values(entity)
        entity_id = getattr(entity, "id")
        if entity_id is None:
            raise ValueError("Cannot update entity without an ID")

        # TODO: Build SET clause: "col1 = ?, col2 = ?"
        # TODO: Execute UPDATE with params + entity_id
        # TODO: Raise ValueError if rowcount == 0
        # TODO: Fetch and return updated entity
        pass  # type: ignore[return-value]

    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        # TODO: Execute DELETE WHERE id = ?
        # TODO: Return True if rowcount > 0
        return False

    def count(self, **filters: Any) -> int:
        """Count entities, optionally filtered."""
        sql = f"SELECT COUNT(*) as cnt FROM {self.table_name}"
        params: list[Any] = []

        if filters:
            valid = set(self.columns) | {"id"}
            safe = {k: v for k, v in filters.items() if k in valid}
            if safe:
                clauses = [f"{col} = ?" for col in safe]
                sql += " WHERE " + " AND ".join(clauses)
                params = list(safe.values())

        with self.db.transaction() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()["cnt"]


# ===========================================================================
# SECTION 5: Concrete Repositories
# ===========================================================================

class UserRepository(SQLiteRepository[User]):
    """Repository for User entities."""

    @property
    def table_name(self) -> str:
        return "users"

    @property
    def columns(self) -> list[str]:
        return ["name", "email", "age", "active"]

    def create_table(self) -> None:
        with self.db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    age INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1
                )
            """)

    def _row_to_entity(self, row: sqlite3.Row) -> User:
        # TODO: Convert sqlite3.Row to User dataclass
        # Hint: User(id=row["id"], name=row["name"], ...)
        pass  # type: ignore[return-value]

    def _entity_to_values(self, entity: User) -> dict[str, Any]:
        # TODO: Convert User to dict of column->value (no 'id')
        # Hint: {"name": entity.name, "email": entity.email, ...}
        # Remember: bool -> int for SQLite (active field)
        pass  # type: ignore[return-value]

    def find_by_email(self, email: str) -> User | None:
        """Find a user by email address."""
        results = self.find_all(email=email)
        return results[0] if results else None

    def find_active(self) -> list[User]:
        """Find all active users."""
        return self.find_all(active=1)


class PostRepository(SQLiteRepository[Post]):
    """Repository for Post entities."""

    @property
    def table_name(self) -> str:
        return "posts"

    @property
    def columns(self) -> list[str]:
        return ["title", "body", "user_id", "published"]

    def create_table(self) -> None:
        with self.db.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    published INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

    def _row_to_entity(self, row: sqlite3.Row) -> Post:
        # TODO: Convert sqlite3.Row to Post dataclass
        pass  # type: ignore[return-value]

    def _entity_to_values(self, entity: Post) -> dict[str, Any]:
        # TODO: Convert Post to dict of column->value (no 'id')
        pass  # type: ignore[return-value]

    def find_by_user(self, user_id: int) -> list[Post]:
        """Find all posts by a specific user."""
        return self.find_all(user_id=user_id)

    def find_published(self) -> list[Post]:
        """Find all published posts."""
        return self.find_all(published=1)


# ===========================================================================
# SECTION 6: Service Layer (Business Logic)
# ===========================================================================
# The service layer depends on AbstractRepository, NOT on SQLite.

class BlogService:
    """Business logic that depends on repository abstractions."""

    def __init__(
        self,
        users: AbstractRepository[User],
        posts: AbstractRepository[Post],
    ) -> None:
        self.users = users
        self.posts = posts

    def register_user(self, name: str, email: str, age: int = 0) -> User:
        """Register a new user."""
        # TODO: Create a User and pass to self.users.create()
        pass  # type: ignore[return-value]

    def create_post(self, user_id: int, title: str, body: str) -> Post:
        """Create a draft post for a user."""
        # TODO: Verify user exists with self.users.find_by_id()
        # TODO: Raise ValueError if not found
        # TODO: Create Post and pass to self.posts.create()
        pass  # type: ignore[return-value]

    def publish_post(self, post_id: int) -> Post:
        """Mark a post as published."""
        # TODO: Find post, set published=True, update via repository
        pass  # type: ignore[return-value]

    def get_user_posts(self, user_id: int) -> list[Post]:
        """Get all posts by a user."""
        return self.posts.find_all(user_id=user_id)

    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account."""
        # TODO: Find user, set active=False, update via repository
        pass  # type: ignore[return-value]


# ===========================================================================
# DEMO
# ===========================================================================

def main() -> None:
    print("=" * 60)
    print("Kata 55 -- Repository Pattern")
    print("=" * 60)

    # --- Setup ---
    try:
        db = Database(":memory:")
        user_repo = UserRepository(db)
        post_repo = PostRepository(db)
        service = BlogService(user_repo, post_repo)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Setup failed: {e}")
        return

    # --- User CRUD ---
    print("\n--- User CRUD via Repository ---")
    alice = bob = charlie = None
    try:
        alice = service.register_user("Alice", "alice@example.com", 30)
        bob = service.register_user("Bob", "bob@example.com", 25)
        charlie = service.register_user("Charlie", "charlie@example.com", 35)
        print(f"  Created: {alice}")
        print(f"  Created: {bob}")
        print(f"  Created: {charlie}")

        found = user_repo.find_by_email("bob@example.com")
        print(f"  Find by email: {found}")

        all_users = user_repo.find_all()
        print(f"  All users: {len(all_users)} total")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Post CRUD ---
    print("\n--- Post CRUD via Repository ---")
    post1 = None
    try:
        post1 = service.create_post(alice.id, "Hello World", "My first post!")
        post2 = service.create_post(alice.id, "Python Tips", "Use type hints.")
        post3 = service.create_post(bob.id, "Bob's Post", "Hello from Bob.")
        print(f"  Created: {post1}")
        print(f"  Created: {post2}")

        published = service.publish_post(post1.id)
        print(f"  Published: {published}")

        alice_posts = service.get_user_posts(alice.id)
        print(f"  Alice's posts: {len(alice_posts)}")

        pub_posts = post_repo.find_published()
        print(f"  Published posts: {len(pub_posts)}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Update & Delete ---
    print("\n--- Update & Delete ---")
    try:
        alice.name = "Alice Updated"
        alice.age = 31
        updated = user_repo.update(alice)
        print(f"  Updated: {updated}")

        deactivated = service.deactivate_user(bob.id)
        print(f"  Deactivated: {deactivated}")

        active_users = user_repo.find_active()
        print(f"  Active users: {[u.name for u in active_users]}")

        deleted = user_repo.delete(charlie.id)
        print(f"  Deleted Charlie: {deleted}")
        print(f"  Total users now: {user_repo.count()}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Counts ---
    print("\n--- Counts ---")
    try:
        print(f"  Total users: {user_repo.count()}")
        print(f"  Active users: {user_repo.count(active=1)}")
        print(f"  Total posts: {post_repo.count()}")
        print(f"  Published posts: {post_repo.count(published=1)}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Error handling ---
    print("\n--- Error Handling ---")
    try:
        service.create_post(999, "Bad Post", "No such user")
    except ValueError as e:
        print(f"  Expected error: {e}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        service.publish_post(999)
    except ValueError as e:
        print(f"  Expected error: {e}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    db.close()

    print("\n" + "=" * 60)
    print("Implement the TODOs above to make all sections pass!")
    print("=" * 60)


if __name__ == "__main__":
    main()
