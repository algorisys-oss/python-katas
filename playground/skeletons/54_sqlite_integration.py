"""
Kata 54 -- SQLite Integration
Run: python playground/skeletons/54_sqlite_integration.py

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
        tables persist across calls. For file databases, opens fresh.
        """
        if self.db_path == ":memory:":
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path)
                # TODO: Enable foreign key enforcement with PRAGMA
            return self._connection

        conn = sqlite3.connect(self.db_path)
        # TODO: Enable foreign key enforcement with PRAGMA
        # TODO: Enable WAL journal mode for file databases
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
            # TODO: Commit on success
        except Exception:
            # TODO: Rollback on error, then re-raise
            raise
        finally:
            # TODO: Close the connection (only for file-based, not :memory:)
            pass

    @contextmanager
    def get_cursor(self) -> Iterator[sqlite3.Cursor]:
        """Context manager that provides a cursor with dict-like rows.

        Rows can be accessed by column name:
            row["id"], row["name"], row["email"]
        """
        with self.get_connection() as conn:
            # TODO: Set conn.row_factory to sqlite3.Row
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

        # TODO: Insert Alice using positional parameters (?)
        # Name: "Alice", Email: "alice@example.com", Age: 30

        # TODO: Insert Bob using named parameters (:name, :email, :age)
        # Name: "Bob", Email: "bob@example.com", Age: 25

        # TODO: Use executemany for bulk inserts with these users:
        # ("Charlie", "charlie@example.com", 35)
        # ("Diana", "diana@example.com", 28)
        # ("Eve", "eve@example.com", 22)

        # TODO: Try a SQL injection attempt safely using parameterized query
        # Search for: "'; DROP TABLE users; --"
        malicious_input = "'; DROP TABLE users; --"
        # TODO: Execute SELECT with ? parameter (safe against injection)
        injection_result = []  # TODO: fetch results

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
        # TODO: Execute INSERT with parameterized values
        # TODO: Return cursor.lastrowid
        pass  # type: ignore[return-value]

    # -- READ --
    def find_by_id(self, cursor: sqlite3.Cursor, user_id: int) -> dict[str, Any] | None:
        """Find a user by ID. Returns None if not found."""
        # TODO: Execute SELECT WHERE id = ? and fetch one row
        # TODO: Return dict(row) if found, None otherwise
        pass

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

        # TODO: Add WHERE active = ? clause if active_only is True

        # TODO: Add ORDER BY clause (validate against allowed columns)
        allowed_columns = {"id", "name", "email", "age"}

        # TODO: Add LIMIT ? clause if limit is not None

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def find_by_email(self, cursor: sqlite3.Cursor, email: str) -> dict[str, Any] | None:
        """Find a user by email address."""
        # TODO: Execute SELECT WHERE email = ? and fetch one row
        pass

    # -- UPDATE --
    def update(self, cursor: sqlite3.Cursor, user_id: int, **fields: Any) -> bool:
        """Update specific fields of a user. Returns True if a row was updated."""
        if not fields:
            return False

        allowed = {"name", "email", "age", "active"}
        safe_fields = {k: v for k, v in fields.items() if k in allowed}
        if not safe_fields:
            return False

        # TODO: Build SET clause like "name = ?, age = ?"
        # TODO: Build values list with field values + user_id
        # TODO: Execute UPDATE ... WHERE id = ?
        # TODO: Return True if cursor.rowcount > 0
        return False

    # -- DELETE --
    def delete(self, cursor: sqlite3.Cursor, user_id: int) -> bool:
        """Delete a user by ID. Returns True if a row was deleted."""
        # TODO: Execute DELETE WHERE id = ?
        # TODO: Return True if cursor.rowcount > 0
        return False

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
    # TODO: Extract column names from cursor.description
    # TODO: Return a dict mapping column names to row values
    pass  # type: ignore[return-value]


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

        # TODO: Fetch a row using default tuple access
        # results["tuple_access"] = f"id={row[0]}, name={row[1]}"

        # TODO: Set conn.row_factory = sqlite3.Row and fetch by name
        # results["row_by_name"] = f"id={row['id']}, name={row['name']}"
        # results["row_keys"] = list(row.keys())

        # TODO: Set conn.row_factory = custom_row_factory and fetch
        # results["dict_row"] = dict_row
        # results["dict_is_mutable"] = isinstance(dict_row, dict)

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

    # TODO: Perform a successful transfer of 200 from Alice to Bob
    # Use db.get_cursor() context manager
    # UPDATE accounts SET balance = balance - ? WHERE id = ?
    # UPDATE accounts SET balance = balance + ? WHERE id = ?

    with db.get_cursor() as cursor:
        cursor.execute("SELECT owner, balance FROM accounts ORDER BY id")
        results["after_transfer"] = [dict(r) for r in cursor.fetchall()]

    # TODO: Attempt a failed transfer (overdraw: 5000 from Alice)
    # Wrap in try/except sqlite3.IntegrityError
    # The context manager should rollback on error

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
    try:
        db = Database(":memory:")
        result = demonstrate_parameterized_queries(db)
        print(f"  Injection attempt found rows: {result['injection_result']}")
        print(f"  Users safe after injection attempt: {result['total_users_after_injection_attempt']}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- CRUD Operations ---
    print("\n--- CRUD Operations ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Row Factories ---
    print("\n--- Row Factories ---")
    try:
        db = Database(":memory:")
        row_results = demonstrate_row_factories(db)
        for key, value in row_results.items():
            print(f"  {key}: {value}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Transactions ---
    print("\n--- Transactions ---")
    try:
        db = Database(":memory:")
        tx_results = demonstrate_transactions(db)
        print(f"  After successful transfer: {tx_results['after_transfer']}")
        print(f"  After failed transfer (rolled back): {tx_results['after_failed_transfer']}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print("\n" + "=" * 60)
    print("Implement the TODOs above to make all sections pass!")
    print("=" * 60)


if __name__ == "__main__":
    main()
