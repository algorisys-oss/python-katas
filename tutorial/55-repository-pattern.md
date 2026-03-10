# Kata 55 -- Repository Pattern

[prev: 54-sqlite-integration](./54-sqlite-integration.md) | [next: 56-migrations](./56-migrations.md)

---

## What We're Building

A **Repository pattern** abstraction over SQLite. The repository sits between your business logic and the database, providing a clean interface for data access. We build:

1. **Abstract repository** -- an interface (ABC) that defines `create`, `find_by_id`, `find_all`, `update`, `delete`
2. **SQLite base repository** -- a generic implementation that handles SQL generation and execution
3. **Concrete repositories** -- `UserRepository` and `PostRepository` with entity-specific schemas
4. **Service layer** -- business logic that depends on the abstract interface, not on SQLite directly

The key benefit: you can swap the storage backend (SQLite, PostgreSQL, a mock) without changing any business logic.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Repository pattern | Abstracts data access behind an interface | Separating storage from logic |
| `ABC` + `Generic[T]` | Type-safe abstract base for any entity type | Reusable base classes |
| `TypeVar` | Parameterize the repository over entity type | Generic CRUD methods |
| `@abstractmethod` | Force subclasses to implement conversion methods | Defining contracts |
| `@property` (abstract) | Subclasses define table name and columns | Per-entity configuration |
| Entity dataclasses | Domain objects with typed fields | Clean data modeling |
| Service layer | Business logic depending on abstractions | Decoupled architecture |
| Column validation | Allowlist filter keys before building SQL | Preventing injection |

## The Code

### 1. Abstract Repository

The contract that all repositories must follow:

```python
class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    def create(self, entity: T) -> T: ...

    @abstractmethod
    def find_by_id(self, entity_id: int) -> T | None: ...

    @abstractmethod
    def find_all(self, **filters: Any) -> list[T]: ...

    @abstractmethod
    def update(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, entity_id: int) -> bool: ...
```

Business logic depends on `AbstractRepository[User]`, not on `SQLiteUserRepository`. This is the Dependency Inversion Principle (Kata 19) in action.

### 2. SQLite Base Repository

The generic SQL implementation. Subclasses only define their schema:

```python
class SQLiteRepository(AbstractRepository[T], ABC):
    @property
    @abstractmethod
    def table_name(self) -> str: ...

    @property
    @abstractmethod
    def columns(self) -> list[str]: ...

    @abstractmethod
    def _row_to_entity(self, row: sqlite3.Row) -> T: ...

    @abstractmethod
    def _entity_to_values(self, entity: T) -> dict[str, Any]: ...

    def create(self, entity: T) -> T:
        values = self._entity_to_values(entity)
        cols = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        sql = f"INSERT INTO {self.table_name} ({cols}) VALUES ({placeholders})"
        # execute, fetch by lastrowid, return entity
```

### 3. Concrete Repository

Each entity gets a thin subclass:

```python
class UserRepository(SQLiteRepository[User]):
    @property
    def table_name(self) -> str:
        return "users"

    @property
    def columns(self) -> list[str]:
        return ["name", "email", "age", "active"]

    def _row_to_entity(self, row) -> User:
        return User(id=row["id"], name=row["name"], ...)

    def _entity_to_values(self, entity) -> dict:
        return {"name": entity.name, "email": entity.email, ...}

    # Domain-specific queries
    def find_by_email(self, email: str) -> User | None:
        results = self.find_all(email=email)
        return results[0] if results else None
```

### 4. Service Layer

Business logic that uses repositories:

```python
class BlogService:
    def __init__(self, users: AbstractRepository[User],
                 posts: AbstractRepository[Post]):
        self.users = users
        self.posts = posts

    def create_post(self, user_id, title, body):
        user = self.users.find_by_id(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        return self.posts.create(Post(title=title, body=body, user_id=user_id))
```

## Playground

Open **`playground/55_repository_pattern.py`** and run:

```bash
python playground/55_repository_pattern.py
```

### Expected Output (excerpt)

```
============================================================
Kata 55 -- Repository Pattern
============================================================

--- User CRUD via Repository ---
  Created: User(name='Alice', email='alice@example.com', age=30, active=True, id=1)
  Created: User(name='Bob', email='bob@example.com', age=25, active=True, id=2)
  Find by email: User(name='Bob', email='bob@example.com', age=25, active=True, id=2)
  All users: 3 total

--- Post CRUD via Repository ---
  Created: Post(title='Hello World', body='My first post!', user_id=1, published=False, id=1)
  Published: Post(title='Hello World', body='My first post!', user_id=1, published=True, id=1)
  Alice's posts: 2
  Published posts: 1

--- Error Handling ---
  Expected error: User 999 not found
  Expected error: Post 999 not found

============================================================
All repository pattern demos passed!
============================================================
```

Or work through the skeleton at **`playground/skeletons/55_repository_pattern.py`** to build it yourself.

## How It Works

1. **Entity dataclasses** (`User`, `Post`) represent domain objects with typed fields
2. **AbstractRepository** defines the CRUD contract using `ABC` and `Generic[T]`
3. **SQLiteRepository** implements CRUD generically -- it builds SQL from `table_name`, `columns`, and conversion methods
4. **Concrete repositories** (`UserRepository`, `PostRepository`) provide the schema-specific bits: table DDL, row-to-entity conversion, entity-to-values conversion
5. **BlogService** depends on `AbstractRepository[User]` and `AbstractRepository[Post]` -- it never imports `sqlite3`
6. **Filters** in `find_all(**filters)` are validated against the column allowlist before building WHERE clauses

### Why This Pattern?

Without the repository pattern:
```python
# Business logic is tangled with SQL
def create_post(db, user_id, title, body):
    cursor = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        raise ValueError("User not found")
    db.execute("INSERT INTO posts ...", (title, body, user_id))
```

With the repository pattern:
```python
# Business logic reads like English
def create_post(self, user_id, title, body):
    if self.users.find_by_id(user_id) is None:
        raise ValueError("User not found")
    return self.posts.create(Post(title=title, body=body, user_id=user_id))
```

The second version is testable (mock the repository), readable, and storage-agnostic.

## Exercises

1. **Add a `find_or_create` method** -- look up by a unique field, create if not found
2. **Add pagination** -- implement `find_paginated(page, per_page)` in the base repository
3. **Create an InMemoryRepository** -- implement `AbstractRepository[T]` using a plain dict, proving the abstraction works without SQLite
4. **Add a CommentRepository** -- model comments with `post_id` and `user_id` foreign keys

## What's Next

In [Kata 56 -- Migrations](./56-migrations.md), we build a schema versioning system to evolve database tables over time without losing data.
