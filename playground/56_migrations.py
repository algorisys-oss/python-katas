"""
Kata 56 -- Migrations
Run: python playground/56_migrations.py

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
# A migration is a named, ordered change to the database schema.
# Each migration has an up() function (apply) and down() function (revert).

@dataclass
class Migration:
    """A single database migration.

    Attributes:
        version: Unique version string, e.g. "001", "002".
                 Migrations run in version-sorted order.
        name: Human-readable description of the change.
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
# Collect migrations in a registry so the runner can discover them.

class MigrationRegistry:
    """Collects and orders migrations.

    Usage:
        registry = MigrationRegistry()
        registry.add("001", "create_users", up_fn, down_fn)
        registry.add("002", "add_email_index", up_fn, down_fn)
    """

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
        if version in self._migrations:
            raise ValueError(f"Duplicate migration version: {version}")
        migration = Migration(version=version, name=name, up=up, down=down)
        self._migrations[version] = migration
        return migration

    def get_all(self) -> list[Migration]:
        """Return all migrations sorted by version."""
        return sorted(self._migrations.values(), key=lambda m: m.version)

    def get(self, version: str) -> Migration | None:
        """Get a migration by version."""
        return self._migrations.get(version)

    def __len__(self) -> int:
        return len(self._migrations)


# ===========================================================================
# SECTION 4: Migration Runner
# ===========================================================================
# The runner tracks which migrations have been applied in a _migrations
# table and can apply or revert migrations.

class MigrationRunner:
    """Runs migrations up and down, tracking state in a _migrations table.

    The _migrations table stores:
        - version: the migration version string
        - name: the migration name
        - applied_at: when the migration was applied
    """

    TRACKING_TABLE = "_migrations"

    def __init__(self, db: Database, registry: MigrationRegistry) -> None:
        self.db = db
        self.registry = registry
        self._ensure_tracking_table()

    def _ensure_tracking_table(self) -> None:
        """Create the _migrations tracking table if it doesn't exist."""
        with self.db.transaction() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TRACKING_TABLE} (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)

    def get_applied_versions(self) -> list[str]:
        """Return list of applied migration versions, sorted."""
        with self.db.transaction() as cursor:
            cursor.execute(
                f"SELECT version FROM {self.TRACKING_TABLE} ORDER BY version"
            )
            return [row["version"] for row in cursor.fetchall()]

    def get_pending(self) -> list[Migration]:
        """Return migrations that haven't been applied yet."""
        applied = set(self.get_applied_versions())
        return [m for m in self.registry.get_all() if m.version not in applied]

    def get_applied(self) -> list[Migration]:
        """Return migrations that have been applied, in order."""
        applied = set(self.get_applied_versions())
        return [m for m in self.registry.get_all() if m.version in applied]

    def migrate_up(self, steps: int | None = None) -> list[Migration]:
        """Apply pending migrations.

        Args:
            steps: Number of migrations to apply. None means all pending.

        Returns:
            List of migrations that were applied.
        """
        pending = self.get_pending()
        if steps is not None:
            pending = pending[:steps]

        applied: list[Migration] = []
        for migration in pending:
            with self.db.transaction() as cursor:
                # Run the up() function
                migration.up(cursor)
                # Record in tracking table
                cursor.execute(
                    f"INSERT INTO {self.TRACKING_TABLE} (version, name, applied_at) "
                    "VALUES (?, ?, ?)",
                    (migration.version, migration.name, datetime.now().isoformat()),
                )
            applied.append(migration)

        return applied

    def migrate_down(self, steps: int = 1) -> list[Migration]:
        """Revert applied migrations, most recent first.

        Args:
            steps: Number of migrations to revert.

        Returns:
            List of migrations that were reverted.
        """
        applied = self.get_applied()
        # Revert in reverse order (most recent first)
        to_revert = list(reversed(applied))[:steps]

        reverted: list[Migration] = []
        for migration in to_revert:
            with self.db.transaction() as cursor:
                # Run the down() function
                migration.down(cursor)
                # Remove from tracking table
                cursor.execute(
                    f"DELETE FROM {self.TRACKING_TABLE} WHERE version = ?",
                    (migration.version,),
                )
            reverted.append(migration)

        return reverted

    def migrate_to(self, target_version: str) -> list[Migration]:
        """Migrate up or down to reach a specific version.

        If target is ahead: apply pending migrations up to target.
        If target is behind: revert applied migrations after target.
        """
        applied_versions = set(self.get_applied_versions())

        if target_version not in {m.version for m in self.registry.get_all()}:
            raise ValueError(f"Unknown migration version: {target_version}")

        # Check if we need to go up or down
        if target_version not in applied_versions:
            # Need to go up: apply all pending up to and including target
            result = []
            for m in self.get_pending():
                with self.db.transaction() as cursor:
                    m.up(cursor)
                    cursor.execute(
                        f"INSERT INTO {self.TRACKING_TABLE} (version, name, applied_at) "
                        "VALUES (?, ?, ?)",
                        (m.version, m.name, datetime.now().isoformat()),
                    )
                result.append(m)
                if m.version == target_version:
                    break
            return result
        else:
            # Need to go down: revert everything after target
            result = []
            applied = self.get_applied()
            to_revert = [m for m in reversed(applied) if m.version > target_version]
            for m in to_revert:
                with self.db.transaction() as cursor:
                    m.down(cursor)
                    cursor.execute(
                        f"DELETE FROM {self.TRACKING_TABLE} WHERE version = ?",
                        (m.version,),
                    )
                result.append(m)
            return result

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
# Define a set of migrations that build up a blog schema step by step.

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

    # --- Migration 002: Add age column to users ---
    def up_002(cursor: sqlite3.Cursor) -> None:
        cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0")

    def down_002(cursor: sqlite3.Cursor) -> None:
        # SQLite doesn't support DROP COLUMN before 3.35.0.
        # Workaround: recreate without the column.
        cursor.execute("""
            CREATE TABLE users_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        cursor.execute("INSERT INTO users_backup (id, name, email) SELECT id, name, email FROM users")
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_backup RENAME TO users")

    registry.add("002", "add_age_to_users", up_002, down_002)

    # --- Migration 003: Create posts table ---
    def up_003(cursor: sqlite3.Cursor) -> None:
        cursor.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                published INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

    def down_003(cursor: sqlite3.Cursor) -> None:
        cursor.execute("DROP TABLE IF EXISTS posts")

    registry.add("003", "create_posts_table", up_003, down_003)

    # --- Migration 004: Add created_at to posts ---
    def up_004(cursor: sqlite3.Cursor) -> None:
        cursor.execute(
            "ALTER TABLE posts ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP"
        )

    def down_004(cursor: sqlite3.Cursor) -> None:
        cursor.execute("""
            CREATE TABLE posts_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                published INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute(
            "INSERT INTO posts_backup (id, title, body, user_id, published) "
            "SELECT id, title, body, user_id, published FROM posts"
        )
        cursor.execute("DROP TABLE posts")
        cursor.execute("ALTER TABLE posts_backup RENAME TO posts")

    registry.add("004", "add_created_at_to_posts", up_004, down_004)

    return registry


# ===========================================================================
# SECTION 6: CLI-style Runner
# ===========================================================================
# Simulate a command-line migration tool.

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

    db = Database(":memory:")
    registry = create_example_migrations()
    runner = MigrationRunner(db, registry)

    # --- Initial status ---
    print("\n--- Initial Status ---")
    print(run_cli(runner, "status"))

    # --- Apply migrations one at a time ---
    print("\n--- Apply 1 migration ---")
    print(run_cli(runner, "up", ["1"]))
    print()
    print(run_cli(runner, "status"))

    # --- Apply remaining migrations ---
    print("\n--- Apply all remaining ---")
    print(run_cli(runner, "up"))
    print()
    print(run_cli(runner, "status"))

    # --- Verify schema works ---
    print("\n--- Verify Schema ---")
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

    # --- Revert last migration ---
    print("\n--- Revert last migration ---")
    print(run_cli(runner, "down"))
    print()
    print(run_cli(runner, "status"))

    # Verify posts table no longer has created_at
    with db.transaction() as cursor:
        cursor.execute("PRAGMA table_info(posts)")
        columns = [row["name"] for row in cursor.fetchall()]
        print(f"  Posts columns after revert: {columns}")

    # --- Revert all ---
    print("\n--- Revert all (3 steps) ---")
    print(run_cli(runner, "down", ["3"]))
    print()
    print(run_cli(runner, "status"))

    # --- Migrate to a specific version ---
    print("\n--- Migrate to version 002 ---")
    print(run_cli(runner, "up"))  # Apply all first
    print(run_cli(runner, "to", ["002"]))
    print()
    print(run_cli(runner, "status"))

    # --- Edge case: no pending ---
    print("\n--- Up when already current ---")
    print(run_cli(runner, "up"))
    print(run_cli(runner, "to", ["002"]))

    db.close()

    print("\n" + "=" * 60)
    print("All migration demos passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
