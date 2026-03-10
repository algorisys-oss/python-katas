"""
Kata 55 -- Repository Pattern
Run: python playground/55_repository_pattern.py

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
# Dataclasses represent our domain objects. The repository converts between
# these objects and database rows.

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


# A TypeVar so our base repository can work with any entity type
T = TypeVar("T")


# ===========================================================================
# SECTION 3: Abstract Repository
# ===========================================================================
# The abstract base defines the contract that all repositories must follow.
# Business logic depends on this interface, not on SQLite directly.

class AbstractRepository(ABC, Generic[T]):
    """Abstract repository defining the data access contract.

    Business logic code depends on this interface, making it easy to
    swap the storage backend (SQLite, PostgreSQL, in-memory dict, etc.)
    without changing application code.
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Persist a new entity and return it with its assigned ID."""
        ...

    @abstractmethod
    def find_by_id(self, entity_id: int) -> T | None:
        """Find an entity by its primary key. Returns None if not found."""
        ...

    @abstractmethod
    def find_all(self, **filters: Any) -> list[T]:
        """Find all entities, optionally filtered by field values."""
        ...

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an existing entity. Returns the updated entity."""
        ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID. Returns True if deleted."""
        ...


# ===========================================================================
# SECTION 4: SQLite Base Repository
# ===========================================================================
# A concrete base that implements the repository contract using SQLite.
# Concrete subclasses only need to define table name, columns, and
# how to convert between rows and entity objects.

class SQLiteRepository(AbstractRepository[T], ABC):
    """Base SQLite repository with generic CRUD implementation.

    Subclasses must implement:
        - table_name: the SQL table name
        - columns: list of column names (excluding 'id')
        - _row_to_entity: convert a sqlite3.Row to an entity object
        - _entity_to_values: convert an entity to a dict of column->value
        - create_table: execute CREATE TABLE DDL
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.create_table()

    @property
    @abstractmethod
    def table_name(self) -> str:
        """The SQL table name."""
        ...

    @property
    @abstractmethod
    def columns(self) -> list[str]:
        """Column names excluding 'id'."""
        ...

    @abstractmethod
    def _row_to_entity(self, row: sqlite3.Row) -> T:
        """Convert a database row to an entity object."""
        ...

    @abstractmethod
    def _entity_to_values(self, entity: T) -> dict[str, Any]:
        """Convert an entity to a dict of column->value (excluding id)."""
        ...

    @abstractmethod
    def create_table(self) -> None:
        """Execute CREATE TABLE IF NOT EXISTS."""
        ...

    def create(self, entity: T) -> T:
        """Insert entity into the database and return it with its new ID."""
        values = self._entity_to_values(entity)
        cols = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        sql = f"INSERT INTO {self.table_name} ({cols}) VALUES ({placeholders})"

        with self.db.transaction() as cursor:
            cursor.execute(sql, list(values.values()))
            # Fetch the newly created row to return the full entity
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (cursor.lastrowid,),
            )
            return self._row_to_entity(cursor.fetchone())

    def find_by_id(self, entity_id: int) -> T | None:
        """Find an entity by primary key."""
        with self.db.transaction() as cursor:
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (entity_id,),
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None

    def find_all(self, **filters: Any) -> list[T]:
        """Find all entities, optionally filtered by column values."""
        sql = f"SELECT * FROM {self.table_name}"
        params: list[Any] = []

        if filters:
            # Validate column names to prevent injection
            valid = set(self.columns) | {"id"}
            safe = {k: v for k, v in filters.items() if k in valid}
            if safe:
                clauses = [f"{col} = ?" for col in safe]
                sql += " WHERE " + " AND ".join(clauses)
                params = list(safe.values())

        sql += " ORDER BY id"

        with self.db.transaction() as cursor:
            cursor.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def update(self, entity: T) -> T:
        """Update an existing entity in the database."""
        values = self._entity_to_values(entity)
        entity_id = getattr(entity, "id")
        if entity_id is None:
            raise ValueError("Cannot update entity without an ID")

        set_clause = ", ".join(f"{col} = ?" for col in values)
        params = list(values.values()) + [entity_id]

        with self.db.transaction() as cursor:
            cursor.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
                params,
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Entity with id={entity_id} not found")
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (entity_id,),
            )
            return self._row_to_entity(cursor.fetchone())

    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        with self.db.transaction() as cursor:
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (entity_id,),
            )
            return cursor.rowcount > 0

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
# Each entity gets its own repository subclass. The subclass defines the
# table schema and conversion logic; CRUD is inherited for free.

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
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            age=row["age"],
            active=bool(row["active"]),
        )

    def _entity_to_values(self, entity: User) -> dict[str, Any]:
        return {
            "name": entity.name,
            "email": entity.email,
            "age": entity.age,
            "active": int(entity.active),
        }

    # -- Domain-specific queries --
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
        return Post(
            id=row["id"],
            title=row["title"],
            body=row["body"],
            user_id=row["user_id"],
            published=bool(row["published"]),
        )

    def _entity_to_values(self, entity: Post) -> dict[str, Any]:
        return {
            "title": entity.title,
            "body": entity.body,
            "user_id": entity.user_id,
            "published": int(entity.published),
        }

    # -- Domain-specific queries --
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
# This is the key benefit: business logic is decoupled from storage.

class BlogService:
    """Business logic that depends on repository abstractions.

    This service knows nothing about SQL or SQLite. It could work with
    any backend that implements AbstractRepository.
    """

    def __init__(
        self,
        users: AbstractRepository[User],
        posts: AbstractRepository[Post],
    ) -> None:
        self.users = users
        self.posts = posts

    def register_user(self, name: str, email: str, age: int = 0) -> User:
        """Register a new user."""
        user = User(name=name, email=email, age=age)
        return self.users.create(user)

    def create_post(self, user_id: int, title: str, body: str) -> Post:
        """Create a draft post for a user."""
        # Verify user exists
        user = self.users.find_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        post = Post(title=title, body=body, user_id=user_id)
        return self.posts.create(post)

    def publish_post(self, post_id: int) -> Post:
        """Mark a post as published."""
        post = self.posts.find_by_id(post_id)
        if post is None:
            raise ValueError(f"Post {post_id} not found")
        post.published = True
        return self.posts.update(post)

    def get_user_posts(self, user_id: int) -> list[Post]:
        """Get all posts by a user."""
        return self.posts.find_all(user_id=user_id)

    def deactivate_user(self, user_id: int) -> User:
        """Deactivate a user account."""
        user = self.users.find_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        user.active = False
        return self.users.update(user)


# ===========================================================================
# DEMO
# ===========================================================================

def main() -> None:
    print("=" * 60)
    print("Kata 55 -- Repository Pattern")
    print("=" * 60)

    # --- Setup ---
    db = Database(":memory:")
    user_repo = UserRepository(db)
    post_repo = PostRepository(db)
    service = BlogService(user_repo, post_repo)

    # --- User CRUD ---
    print("\n--- User CRUD via Repository ---")
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

    # --- Post CRUD ---
    print("\n--- Post CRUD via Repository ---")
    post1 = service.create_post(alice.id, "Hello World", "My first post!")
    post2 = service.create_post(alice.id, "Python Tips", "Use type hints.")
    post3 = service.create_post(bob.id, "Bob's Post", "Hello from Bob.")
    print(f"  Created: {post1}")
    print(f"  Created: {post2}")

    # Publish a post
    published = service.publish_post(post1.id)
    print(f"  Published: {published}")

    # Find posts by user
    alice_posts = service.get_user_posts(alice.id)
    print(f"  Alice's posts: {len(alice_posts)}")

    # Find published posts
    pub_posts = post_repo.find_published()
    print(f"  Published posts: {len(pub_posts)}")

    # --- Update & Delete ---
    print("\n--- Update & Delete ---")
    alice.name = "Alice Updated"
    alice.age = 31
    updated = user_repo.update(alice)
    print(f"  Updated: {updated}")

    # Deactivate user
    deactivated = service.deactivate_user(bob.id)
    print(f"  Deactivated: {deactivated}")

    active_users = user_repo.find_active()
    print(f"  Active users: {[u.name for u in active_users]}")

    # Delete
    deleted = user_repo.delete(charlie.id)
    print(f"  Deleted Charlie: {deleted}")
    print(f"  Total users now: {user_repo.count()}")

    # --- Counts ---
    print("\n--- Counts ---")
    print(f"  Total users: {user_repo.count()}")
    print(f"  Active users: {user_repo.count(active=1)}")
    print(f"  Total posts: {post_repo.count()}")
    print(f"  Published posts: {post_repo.count(published=1)}")

    # --- Error handling ---
    print("\n--- Error Handling ---")
    try:
        service.create_post(999, "Bad Post", "No such user")
    except ValueError as e:
        print(f"  Expected error: {e}")

    try:
        service.publish_post(999)
    except ValueError as e:
        print(f"  Expected error: {e}")

    db.close()

    print("\n" + "=" * 60)
    print("All repository pattern demos passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
