"""
Kata 54 -- SQLite Integration
Run: python playground/54_sqlite_integration.py

Build a database layer using sqlite3. Connection management with context
managers, parameterized queries (prevent SQL injection), CRUD operations,
and row_factory for dict-like results. Uses :memory: database for testing.

Completes within 5 seconds.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator


# ===========================================================================
# SECTION 1: Connection Management
# ===========================================================================
# sqlite3 connections should be properly opened and closed. A context manager
# ensures the connection is always cleaned up, even if an error occurs.
# We also enable WAL mode and foreign keys for production-like behavior.

class Database:
    """Manages SQLite connections and provides a clean query interface.

    Uses :memory: for testing or a file path for persistence.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """Open a connection and configure it for best practices.

        For :memory: databases, reuses the same connection so that
        tables persist across calls. For file databases, each call
        opens a fresh connection.
        """
        if self.db_path == ":memory:":
            # Reuse connection for in-memory databases
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path)
                self._connection.execute("PRAGMA foreign_keys = ON")
            return self._connection

        conn = sqlite3.connect(self.db_path)
        # Enable foreign key enforcement (off by default in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        # Use Write-Ahead Logging for better concurrent read performance
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager that provides a connection with automatic cleanup.

        Usage:
            with db.get_connection() as conn:
                conn.execute("SELECT ...")
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()  # Auto-commit on success
        except Exception:
            conn.rollback()  # Rollback on error
            raise
        finally:
            # Only close file-based connections; keep :memory: alive
            if self.db_path != ":memory:":
                conn.close()

    @contextmanager
    def get_cursor(self) -> Iterator[sqlite3.Cursor]:
        """Context manager that provides a cursor with dict-like rows.

        Rows can be accessed by column name:
            row["id"], row["name"], row["email"]
        """
        with self.get_connection() as conn:
            # row_factory makes rows accessible by column name
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()


# ===========================================================================
# SECTION 2: Parameterized Queries
# ===========================================================================
# NEVER use string formatting for SQL queries -- it leads to SQL injection.
# Always use ? placeholders or :named parameters.

def demonstrate_parameterized_queries(db: Database) -> dict[str, Any]:
    """Show safe parameterized queries vs. dangerous string formatting."""

    with db.get_cursor() as cursor:
        # Create a test table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER DEFAULT 0
            )
        """)

        # --- SAFE: Positional parameters with ? ---
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            ("Alice", "alice@example.com", 30),
        )

        # --- SAFE: Named parameters with :name ---
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (:name, :email, :age)",
            {"name": "Bob", "email": "bob@example.com", "age": 25},
        )

        # --- SAFE: executemany for bulk inserts ---
        bulk_users = [
            ("Charlie", "charlie@example.com", 35),
            ("Diana", "diana@example.com", 28),
            ("Eve", "eve@example.com", 22),
        ]
        cursor.executemany(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            bulk_users,
        )

        # --- DANGEROUS (never do this): ---
        # name = "'; DROP TABLE users; --"
        # cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
        # The parameterized version is safe against injection:
        malicious_input = "'; DROP TABLE users; --"
        cursor.execute("SELECT * FROM users WHERE name = ?", (malicious_input,))
        injection_result = cursor.fetchall()  # Returns empty, table is safe

        # Verify all rows are intact
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        count = cursor.fetchone()["cnt"]

        return {
            "injection_result": list(injection_result),
            "total_users_after_injection_attempt": count,
        }


# ===========================================================================
# SECTION 3: CRUD Operations
# ===========================================================================
# Create, Read, Update, Delete -- the four fundamental data operations.

class UserStore:
    """CRUD operations for users using parameterized queries."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_table(self, cursor: sqlite3.Cursor) -> None:
        """Create the users table if it doesn't exist."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1
            )
        """)

    # -- CREATE --
    def insert(self, cursor: sqlite3.Cursor, name: str, email: str, age: int = 0) -> int:
        """Insert a new user and return the new row ID."""
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            (name, email, age),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    # -- READ --
    def find_by_id(self, cursor: sqlite3.Cursor, user_id: int) -> dict[str, Any] | None:
        """Find a user by ID. Returns None if not found."""
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_all(
        self,
        cursor: sqlite3.Cursor,
        *,
        active_only: bool = False,
        order_by: str = "id",
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find all users with optional filtering and ordering."""
        query = "SELECT * FROM users"
        params: list[Any] = []

        if active_only:
            query += " WHERE active = ?"
            params.append(1)

        # Only allow known columns to prevent injection via order_by
        allowed_columns = {"id", "name", "email", "age"}
        if order_by in allowed_columns:
            query += f" ORDER BY {order_by}"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def find_by_email(self, cursor: sqlite3.Cursor, email: str) -> dict[str, Any] | None:
        """Find a user by email address."""
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # -- UPDATE --
    def update(self, cursor: sqlite3.Cursor, user_id: int, **fields: Any) -> bool:
        """Update specific fields of a user. Returns True if a row was updated."""
        if not fields:
            return False

        allowed = {"name", "email", "age", "active"}
        safe_fields = {k: v for k, v in fields.items() if k in allowed}
        if not safe_fields:
            return False

        set_clause = ", ".join(f"{key} = ?" for key in safe_fields)
        values = list(safe_fields.values()) + [user_id]

        cursor.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?",
            values,
        )
        return cursor.rowcount > 0

    # -- DELETE --
    def delete(self, cursor: sqlite3.Cursor, user_id: int) -> bool:
        """Delete a user by ID. Returns True if a row was deleted."""
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

    def soft_delete(self, cursor: sqlite3.Cursor, user_id: int) -> bool:
        """Soft-delete by setting active = 0 instead of removing the row."""
        return self.update(cursor, user_id, active=0)


# ===========================================================================
# SECTION 4: Row Factory and Dict-Like Results
# ===========================================================================
# sqlite3.Row lets you access columns by name. You can also build custom
# row factories for more specialized behavior.

def custom_row_factory(cursor: sqlite3.Cursor, row: tuple) -> dict[str, Any]:
    """A custom row factory that returns plain dicts.

    The built-in sqlite3.Row is read-only and dict-like.
    This factory returns actual mutable dicts.
    """
    columns = [description[0] for description in cursor.description]
    return dict(zip(columns, row))


def demonstrate_row_factories(db: Database) -> dict[str, Any]:
    """Show different ways to access query results."""
    results: dict[str, Any] = {}

    with db.get_connection() as conn:
        conn.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL
            )
        """)
        conn.execute(
            "INSERT INTO products VALUES (1, 'Widget', 9.99)"
        )

        # Default: rows are tuples
        cursor = conn.execute("SELECT * FROM products")
        tuple_row = cursor.fetchone()
        results["tuple_access"] = f"id={tuple_row[0]}, name={tuple_row[1]}"

        # sqlite3.Row: access by name and index
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM products")
        row = cursor.fetchone()
        results["row_by_name"] = f"id={row['id']}, name={row['name']}"
        results["row_keys"] = list(row.keys())

        # Custom row factory: plain dicts
        conn.row_factory = custom_row_factory
        cursor = conn.execute("SELECT * FROM products")
        dict_row = cursor.fetchone()
        results["dict_row"] = dict_row
        results["dict_is_mutable"] = isinstance(dict_row, dict)

    return results


# ===========================================================================
# SECTION 5: Transactions
# ===========================================================================
# Transactions ensure that a group of operations either all succeed or all
# fail together (atomicity).

def demonstrate_transactions(db: Database) -> dict[str, Any]:
    """Show transaction commit and rollback behavior."""
    results: dict[str, Any] = {}

    # Setup
    with db.get_cursor() as cursor:
        cursor.execute("""
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY,
                owner TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0 CHECK(balance >= 0)
            )
        """)
        cursor.execute("INSERT INTO accounts VALUES (1, 'Alice', 1000)")
        cursor.execute("INSERT INTO accounts VALUES (2, 'Bob', 500)")

    # Successful transfer
    with db.get_cursor() as cursor:
        amount = 200
        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount, 1),
        )
        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, 2),
        )
        # Both committed together on context manager exit

    with db.get_cursor() as cursor:
        cursor.execute("SELECT owner, balance FROM accounts ORDER BY id")
        results["after_transfer"] = [dict(r) for r in cursor.fetchall()]

    # Failed transfer (overdraw triggers CHECK constraint)
    try:
        with db.get_cursor() as cursor:
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (5000, 1),  # More than Alice has
            )
            # This would violate the CHECK constraint
    except sqlite3.IntegrityError:
        pass  # Rolled back by context manager

    with db.get_cursor() as cursor:
        cursor.execute("SELECT owner, balance FROM accounts ORDER BY id")
        results["after_failed_transfer"] = [dict(r) for r in cursor.fetchall()]

    return results


# ===========================================================================
# DEMO
# ===========================================================================

def main() -> None:
    print("=" * 60)
    print("Kata 54 -- SQLite Integration")
    print("=" * 60)

    # --- Parameterized Queries ---
    print("\n--- Parameterized Queries ---")
    db = Database(":memory:")
    result = demonstrate_parameterized_queries(db)
    print(f"  Injection attempt found rows: {result['injection_result']}")
    print(f"  Users safe after injection attempt: {result['total_users_after_injection_attempt']}")

    # --- CRUD Operations ---
    print("\n--- CRUD Operations ---")
    db = Database(":memory:")
    store = UserStore(db)

    with db.get_cursor() as cursor:
        store.create_table(cursor)

        # Create
        id1 = store.insert(cursor, "Alice", "alice@example.com", 30)
        id2 = store.insert(cursor, "Bob", "bob@example.com", 25)
        id3 = store.insert(cursor, "Charlie", "charlie@example.com", 35)
        print(f"  Created users with IDs: {id1}, {id2}, {id3}")

        # Read
        user = store.find_by_id(cursor, id1)
        print(f"  Find by ID {id1}: {user}")

        found = store.find_by_email(cursor, "bob@example.com")
        print(f"  Find by email: {found}")

        all_users = store.find_all(cursor, order_by="age", limit=2)
        print(f"  Find all (order by age, limit 2): {all_users}")

        # Update
        updated = store.update(cursor, id1, name="Alice Updated", age=31)
        print(f"  Updated user {id1}: {updated}")
        print(f"  After update: {store.find_by_id(cursor, id1)}")

        # Delete
        deleted = store.delete(cursor, id3)
        print(f"  Deleted user {id3}: {deleted}")
        print(f"  After delete: {store.find_all(cursor)}")

        # Soft delete
        store.insert(cursor, "Diana", "diana@example.com", 28)
        store.soft_delete(cursor, id2)
        active = store.find_all(cursor, active_only=True)
        print(f"  Active users after soft-delete: {active}")

    # --- Row Factories ---
    print("\n--- Row Factories ---")
    db = Database(":memory:")
    row_results = demonstrate_row_factories(db)
    for key, value in row_results.items():
        print(f"  {key}: {value}")

    # --- Transactions ---
    print("\n--- Transactions ---")
    db = Database(":memory:")
    tx_results = demonstrate_transactions(db)
    print(f"  After successful transfer: {tx_results['after_transfer']}")
    print(f"  After failed transfer (rolled back): {tx_results['after_failed_transfer']}")

    print("\n" + "=" * 60)
    print("All SQLite integration demos passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
