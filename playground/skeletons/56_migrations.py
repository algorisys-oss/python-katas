"""
Kata 56 -- Migrations
Run: python playground/skeletons/56_migrations.py

Build a migration system for SQLite. Each migration has up() and down()
functions. Track applied migrations in a _migrations table. Support
running up/down migrations. Migration runner applies pending migrations
in order. Tests with in-memory SQLite.

Completes within 5 seconds.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterator


# ===========================================================================
# SECTION 1: Database Connection
# ===========================================================================

class Database:
    """Minimal database wrapper for migrations."""

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
# SECTION 2: Migration Definition
# ===========================================================================

@dataclass
class Migration:
    """A single database migration.

    Attributes:
        version: Unique version string, e.g. "001", "002".
        name: Human-readable description.
        up: Function that applies the migration (receives a cursor).
        down: Function that reverts the migration (receives a cursor).
    """
    version: str
    name: str
    up: Callable[[sqlite3.Cursor], None]
    down: Callable[[sqlite3.Cursor], None]

    def __repr__(self) -> str:
        return f"Migration({self.version}: {self.name})"


# ===========================================================================
# SECTION 3: Migration Registry
# ===========================================================================

class MigrationRegistry:
    """Collects and orders migrations."""

    def __init__(self) -> None:
        self._migrations: dict[str, Migration] = {}

    def add(
        self,
        version: str,
        name: str,
        up: Callable[[sqlite3.Cursor], None],
        down: Callable[[sqlite3.Cursor], None],
    ) -> Migration:
        """Register a migration."""
        # TODO: Check for duplicate version, raise ValueError
        # TODO: Create Migration and store in self._migrations
        pass  # type: ignore[return-value]

    def get_all(self) -> list[Migration]:
        """Return all migrations sorted by version."""
        # TODO: Sort self._migrations.values() by version
        return []

    def get(self, version: str) -> Migration | None:
        """Get a migration by version."""
        return self._migrations.get(version)

    def __len__(self) -> int:
        return len(self._migrations)


# ===========================================================================
# SECTION 4: Migration Runner
# ===========================================================================

class MigrationRunner:
    """Runs migrations up and down, tracking state in a _migrations table."""

    TRACKING_TABLE = "_migrations"

    def __init__(self, db: Database, registry: MigrationRegistry) -> None:
        self.db = db
        self.registry = registry
        self._ensure_tracking_table()

    def _ensure_tracking_table(self) -> None:
        """Create the _migrations tracking table if it doesn't exist."""
        # TODO: CREATE TABLE IF NOT EXISTS _migrations
        #   version TEXT PRIMARY KEY
        #   name TEXT NOT NULL
        #   applied_at TEXT NOT NULL
        pass

    def get_applied_versions(self) -> list[str]:
        """Return list of applied migration versions, sorted."""
        # TODO: SELECT version FROM _migrations ORDER BY version
        return []

    def get_pending(self) -> list[Migration]:
        """Return migrations that haven't been applied yet."""
        # TODO: Filter registry.get_all() to exclude applied versions
        return []

    def get_applied(self) -> list[Migration]:
        """Return migrations that have been applied, in order."""
        # TODO: Filter registry.get_all() to include only applied versions
        return []

    def migrate_up(self, steps: int | None = None) -> list[Migration]:
        """Apply pending migrations.

        Args:
            steps: Number of migrations to apply. None means all pending.
        """
        pending = self.get_pending()
        if steps is not None:
            pending = pending[:steps]

        applied: list[Migration] = []
        for migration in pending:
            # TODO: Within a transaction:
            #   1. Call migration.up(cursor)
            #   2. INSERT into _migrations tracking table
            # TODO: Append to applied list
            pass

        return applied

    def migrate_down(self, steps: int = 1) -> list[Migration]:
        """Revert applied migrations, most recent first.

        Args:
            steps: Number of migrations to revert.
        """
        applied = self.get_applied()
        # TODO: Reverse and take first `steps` items
        to_revert: list[Migration] = []

        reverted: list[Migration] = []
        for migration in to_revert:
            # TODO: Within a transaction:
            #   1. Call migration.down(cursor)
            #   2. DELETE from _migrations tracking table
            # TODO: Append to reverted list
            pass

        return reverted

    def migrate_to(self, target_version: str) -> list[Migration]:
        """Migrate up or down to reach a specific version."""
        applied_versions = set(self.get_applied_versions())

        if target_version not in {m.version for m in self.registry.get_all()}:
            raise ValueError(f"Unknown migration version: {target_version}")

        if target_version not in applied_versions:
            # TODO: Apply pending migrations up to and including target
            pass
        else:
            # TODO: Revert applied migrations that are after target
            pass

        return []

    def status(self) -> dict[str, Any]:
        """Return current migration status."""
        all_migrations = self.registry.get_all()
        applied = set(self.get_applied_versions())
        pending = self.get_pending()

        return {
            "total": len(all_migrations),
            "applied": len(applied),
            "pending": len(pending),
            "current_version": max(applied) if applied else None,
            "migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "applied": m.version in applied,
                }
                for m in all_migrations
            ],
        }


# ===========================================================================
# SECTION 5: Example Migrations
# ===========================================================================

def create_example_migrations() -> MigrationRegistry:
    """Create a set of example migrations for a blog application."""
    registry = MigrationRegistry()

    # --- Migration 001: Create users table ---
    def up_001(cursor: sqlite3.Cursor) -> None:
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)

    def down_001(cursor: sqlite3.Cursor) -> None:
        cursor.execute("DROP TABLE IF EXISTS users")

    registry.add("001", "create_users_table", up_001, down_001)

    # TODO: Migration 002 -- Add age column to users
    # up: ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0
    # down: Recreate table without age column (use backup table pattern)

    # TODO: Migration 003 -- Create posts table
    # up: CREATE TABLE posts (id, title, body, user_id FK, published)
    # down: DROP TABLE posts

    # TODO: Migration 004 -- Add created_at to posts
    # up: ALTER TABLE posts ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP
    # down: Recreate table without created_at column

    return registry


# ===========================================================================
# SECTION 6: CLI-style Runner
# ===========================================================================

def run_cli(runner: MigrationRunner, command: str, args: list[str] | None = None) -> str:
    """Simulate a CLI migration command.

    Commands:
        status   -- Show migration status
        up       -- Apply all pending (or N steps with args)
        down     -- Revert last migration (or N steps with args)
        to VER   -- Migrate to a specific version
    """
    args = args or []

    if command == "status":
        info = runner.status()
        lines = [
            f"Migrations: {info['applied']}/{info['total']} applied, "
            f"{info['pending']} pending",
            f"Current version: {info['current_version'] or '(none)'}",
            "",
        ]
        for m in info["migrations"]:
            marker = "[x]" if m["applied"] else "[ ]"
            lines.append(f"  {marker} {m['version']}: {m['name']}")
        return "\n".join(lines)

    elif command == "up":
        steps = int(args[0]) if args else None
        applied = runner.migrate_up(steps)
        if not applied:
            return "No pending migrations."
        lines = [f"Applied {len(applied)} migration(s):"]
        for m in applied:
            lines.append(f"  + {m.version}: {m.name}")
        return "\n".join(lines)

    elif command == "down":
        steps = int(args[0]) if args else 1
        reverted = runner.migrate_down(steps)
        if not reverted:
            return "No migrations to revert."
        lines = [f"Reverted {len(reverted)} migration(s):"]
        for m in reverted:
            lines.append(f"  - {m.version}: {m.name}")
        return "\n".join(lines)

    elif command == "to":
        if not args:
            return "Error: 'to' requires a version argument."
        result = runner.migrate_to(args[0])
        if not result:
            return f"Already at version {args[0]}."
        return f"Migrated {len(result)} step(s) to version {args[0]}."

    else:
        return f"Unknown command: {command}"


# ===========================================================================
# DEMO
# ===========================================================================

def main() -> None:
    print("=" * 60)
    print("Kata 56 -- Migrations")
    print("=" * 60)

    try:
        db = Database(":memory:")
        registry = create_example_migrations()
        runner = MigrationRunner(db, registry)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Setup failed: {e}")
        return

    # --- Initial status ---
    print("\n--- Initial Status ---")
    try:
        print(run_cli(runner, "status"))
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Apply migrations one at a time ---
    print("\n--- Apply 1 migration ---")
    try:
        print(run_cli(runner, "up", ["1"]))
        print()
        print(run_cli(runner, "status"))
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Apply remaining migrations ---
    print("\n--- Apply all remaining ---")
    try:
        print(run_cli(runner, "up"))
        print()
        print(run_cli(runner, "status"))
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Verify schema works ---
    print("\n--- Verify Schema ---")
    try:
        with db.transaction() as cursor:
            cursor.execute(
                "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                ("Alice", "alice@example.com", 30),
            )
            cursor.execute(
                "INSERT INTO posts (title, body, user_id) VALUES (?, ?, ?)",
                ("Hello", "World", 1),
            )
            cursor.execute("SELECT * FROM users")
            user = dict(cursor.fetchone())
            print(f"  User: {user}")

            cursor.execute("SELECT * FROM posts")
            post = dict(cursor.fetchone())
            print(f"  Post: {post}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Revert last migration ---
    print("\n--- Revert last migration ---")
    try:
        print(run_cli(runner, "down"))
        print()
        print(run_cli(runner, "status"))
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Revert all ---
    print("\n--- Revert all ---")
    try:
        print(run_cli(runner, "down", ["3"]))
        print()
        print(run_cli(runner, "status"))
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Migrate to a specific version ---
    print("\n--- Migrate to version 002 ---")
    try:
        print(run_cli(runner, "up"))
        print(run_cli(runner, "to", ["002"]))
        print()
        print(run_cli(runner, "status"))
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    db.close()

    print("\n" + "=" * 60)
    print("Implement the TODOs above to make all sections pass!")
    print("=" * 60)


if __name__ == "__main__":
    main()
