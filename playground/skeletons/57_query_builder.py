"""
Kata 57 -- Query Builder
Run: python playground/skeletons/57_query_builder.py

Build a chainable query builder. Query("users").where("age >", 18)
.order_by("name").limit(10) generates parameterized SQL. Support
select, insert, update, delete. Method chaining pattern. Test by
building queries and executing against in-memory SQLite.

Completes within 5 seconds.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterator


# ===========================================================================
# SECTION 1: Database Connection
# ===========================================================================

class Database:
    """Minimal database wrapper."""

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
# SECTION 2: Where Clause
# ===========================================================================

@dataclass
class WhereClause:
    """A single WHERE condition."""
    column: str
    operator: str
    value: Any

    def to_sql(self) -> tuple[str, list[Any]]:
        """Generate SQL fragment and parameters."""
        op = self.operator.upper()

        if op == "IN":
            # TODO: Build "column IN (?, ?, ?)" with list of values
            pass

        if op == "IS NULL":
            # TODO: Return "column IS NULL" with no params
            pass

        if op == "IS NOT NULL":
            # TODO: Return "column IS NOT NULL" with no params
            pass

        # TODO: Return "column op ?" with [value]
        return f"{self.column} {op} ?", [self.value]


# ===========================================================================
# SECTION 3: Query Builder
# ===========================================================================

class Query:
    """Chainable SQL query builder.

    Usage:
        q = (Query("users")
             .select("name", "email")
             .where("age >", 18)
             .order_by("name")
             .limit(10))
        sql, params = q.build()
    """

    OPERATORS = {"=", "!=", "<", ">", "<=", ">=", "LIKE", "IN", "IS NULL", "IS NOT NULL"}

    def __init__(self, table: str) -> None:
        self._table = table
        self._type = "SELECT"
        self._columns: list[str] = []
        self._wheres: list[WhereClause] = []
        self._or_wheres: list[WhereClause] = []
        self._order_by: list[str] = []
        self._limit_val: int | None = None
        self._offset_val: int | None = None
        self._values: dict[str, Any] = {}

    def _clone(self) -> Query:
        """Return a deep copy so chaining is immutable."""
        return deepcopy(self)

    # -- SELECT --
    def select(self, *columns: str) -> Query:
        """Specify columns to select."""
        q = self._clone()
        q._type = "SELECT"
        q._columns = list(columns)
        return q

    # -- WHERE --
    def where(self, condition: str, value: Any = None) -> Query:
        """Add a WHERE condition (AND)."""
        q = self._clone()
        column, operator = self._parse_condition(condition)
        q._wheres.append(WhereClause(column=column, operator=operator, value=value))
        return q

    def or_where(self, condition: str, value: Any = None) -> Query:
        """Add a WHERE condition (OR)."""
        q = self._clone()
        column, operator = self._parse_condition(condition)
        q._or_wheres.append(WhereClause(column=column, operator=operator, value=value))
        return q

    def where_in(self, column: str, values: list[Any]) -> Query:
        """Add a WHERE column IN (...) condition."""
        q = self._clone()
        q._wheres.append(WhereClause(column=column, operator="IN", value=values))
        return q

    def where_null(self, column: str) -> Query:
        """Add a WHERE column IS NULL condition."""
        q = self._clone()
        q._wheres.append(WhereClause(column=column, operator="IS NULL", value=None))
        return q

    def where_not_null(self, column: str) -> Query:
        """Add a WHERE column IS NOT NULL condition."""
        q = self._clone()
        q._wheres.append(WhereClause(column=column, operator="IS NOT NULL", value=None))
        return q

    # -- ORDER BY --
    def order_by(self, column: str, direction: str = "ASC") -> Query:
        """Add an ORDER BY clause."""
        # TODO: Clone, validate direction (ASC/DESC), append "column direction"
        q = self._clone()
        return q

    # -- LIMIT / OFFSET --
    def limit(self, n: int) -> Query:
        """Set LIMIT."""
        # TODO: Clone and set _limit_val
        q = self._clone()
        return q

    def offset(self, n: int) -> Query:
        """Set OFFSET."""
        # TODO: Clone and set _offset_val
        q = self._clone()
        return q

    # -- INSERT --
    def insert(self, **values: Any) -> Query:
        """Build an INSERT query."""
        q = self._clone()
        q._type = "INSERT"
        q._values = values
        return q

    # -- UPDATE --
    def update(self, **values: Any) -> Query:
        """Build an UPDATE query."""
        q = self._clone()
        q._type = "UPDATE"
        q._values = values
        return q

    # -- DELETE --
    def delete(self) -> Query:
        """Build a DELETE query."""
        q = self._clone()
        q._type = "DELETE"
        return q

    # -- BUILD --
    def build(self) -> tuple[str, list[Any]]:
        """Generate the SQL string and parameters."""
        if self._type == "SELECT":
            return self._build_select()
        elif self._type == "INSERT":
            return self._build_insert()
        elif self._type == "UPDATE":
            return self._build_update()
        elif self._type == "DELETE":
            return self._build_delete()
        else:
            raise ValueError(f"Unknown query type: {self._type}")

    def _build_select(self) -> tuple[str, list[Any]]:
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols} FROM {self._table}"
        params: list[Any] = []

        # TODO: Build and append WHERE clause
        # TODO: Append ORDER BY if _order_by is not empty
        # TODO: Append LIMIT ? if _limit_val is set, add to params
        # TODO: Append OFFSET ? if _offset_val is set, add to params

        return sql, params

    def _build_insert(self) -> tuple[str, list[Any]]:
        if not self._values:
            raise ValueError("INSERT requires values")
        # TODO: Build "INSERT INTO table (col1, col2) VALUES (?, ?)"
        # TODO: Return (sql, list(self._values.values()))
        return "", []

    def _build_update(self) -> tuple[str, list[Any]]:
        if not self._values:
            raise ValueError("UPDATE requires values")
        # TODO: Build "UPDATE table SET col1 = ?, col2 = ?"
        # TODO: Append WHERE clause if present
        # TODO: Return (sql, params)
        return "", []

    def _build_delete(self) -> tuple[str, list[Any]]:
        # TODO: Build "DELETE FROM table"
        # TODO: Append WHERE clause if present
        return "", []

    def _build_where(self) -> tuple[str, list[Any]]:
        """Build the WHERE clause from all conditions."""
        if not self._wheres and not self._or_wheres:
            return "", []

        parts: list[str] = []
        params: list[Any] = []

        # TODO: Process AND conditions from self._wheres
        # For each clause, call to_sql() and collect fragments + params

        # TODO: Process OR conditions from self._or_wheres
        # Combine AND and OR parts appropriately

        and_sql = " AND ".join(parts) if parts else ""
        return and_sql, params

    @staticmethod
    def _parse_condition(condition: str) -> tuple[str, str]:
        """Parse 'column operator' into (column, operator).

        Examples:
            "age >"     -> ("age", ">")
            "name ="    -> ("name", "=")
            "name LIKE" -> ("name", "LIKE")
            "name"      -> ("name", "=")  (default to equality)
        """
        # TODO: Handle multi-word operators (IS NULL, IS NOT NULL)
        # TODO: Split on whitespace, default to "=" if no operator
        parts = condition.split(None, 1)
        if len(parts) == 1:
            return parts[0], "="
        return parts[0], parts[1].upper()

    # -- EXECUTE --
    def execute(self, db: Database) -> list[dict[str, Any]]:
        """Execute the query against a database."""
        sql, params = self.build()
        with db.transaction() as cursor:
            cursor.execute(sql, params)
            if self._type == "SELECT":
                return [dict(row) for row in cursor.fetchall()]
            elif self._type == "INSERT":
                return [{"lastrowid": cursor.lastrowid}]
            else:
                return [{"rowcount": cursor.rowcount}]

    def __repr__(self) -> str:
        sql, params = self.build()
        return f"Query({sql!r}, {params!r})"


# ===========================================================================
# SECTION 4: Helper Functions
# ===========================================================================

def setup_test_db(db: Database) -> None:
    """Create and populate test tables."""
    with db.transaction() as cursor:
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                role TEXT DEFAULT 'user'
            )
        """)
        users = [
            ("Alice", "alice@example.com", 30, 1, "admin"),
            ("Bob", "bob@example.com", 25, 1, "user"),
            ("Charlie", "charlie@example.com", 35, 0, "user"),
            ("Diana", "diana@example.com", 28, 1, "moderator"),
            ("Eve", "eve@example.com", 22, 1, "user"),
        ]
        cursor.executemany(
            "INSERT INTO users (name, email, age, active, role) VALUES (?, ?, ?, ?, ?)",
            users,
        )


# ===========================================================================
# DEMO
# ===========================================================================

def main() -> None:
    print("=" * 60)
    print("Kata 57 -- Query Builder")
    print("=" * 60)

    db = Database(":memory:")
    setup_test_db(db)

    # --- Basic SELECT ---
    print("\n--- Basic SELECT ---")
    try:
        q = Query("users")
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        results = q.execute(db)
        print(f"  Results: {len(results)} rows")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- SELECT with columns ---
    print("\n--- SELECT specific columns ---")
    try:
        q = Query("users").select("name", "email")
        sql, params = q.build()
        print(f"  SQL: {sql}")
        results = q.execute(db)
        print(f"  First row: {results[0]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- WHERE ---
    print("\n--- WHERE clause ---")
    try:
        q = Query("users").where("age >", 25)
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        results = q.execute(db)
        print(f"  Matches: {[r['name'] for r in results]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Multiple WHERE (AND) ---
    print("\n--- Multiple WHERE (AND) ---")
    try:
        q = (Query("users")
             .where("age >", 24)
             .where("active =", 1))
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        results = q.execute(db)
        print(f"  Matches: {[r['name'] for r in results]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- WHERE IN ---
    print("\n--- WHERE IN ---")
    try:
        q = Query("users").where_in("role", ["admin", "moderator"])
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        results = q.execute(db)
        print(f"  Matches: {[r['name'] for r in results]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- ORDER BY ---
    print("\n--- ORDER BY ---")
    try:
        q = Query("users").select("name", "age").order_by("age", "DESC")
        sql, params = q.build()
        print(f"  SQL: {sql}")
        results = q.execute(db)
        print(f"  Ordered: {[(r['name'], r['age']) for r in results]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- LIMIT and OFFSET ---
    print("\n--- LIMIT and OFFSET ---")
    try:
        q = (Query("users")
             .select("name")
             .order_by("name")
             .limit(3)
             .offset(1))
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        results = q.execute(db)
        print(f"  Page: {[r['name'] for r in results]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Full chain ---
    print("\n--- Full chain ---")
    try:
        q = (Query("users")
             .select("name", "email", "age")
             .where("age >", 20)
             .where("active =", 1)
             .order_by("age")
             .limit(3))
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        results = q.execute(db)
        for r in results:
            print(f"    {r['name']} ({r['age']}): {r['email']}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- INSERT ---
    print("\n--- INSERT ---")
    try:
        q = Query("users").insert(name="Frank", email="frank@example.com", age=40, active=1, role="user")
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        result = q.execute(db)
        print(f"  Inserted: lastrowid={result[0]['lastrowid']}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- UPDATE ---
    print("\n--- UPDATE ---")
    try:
        q = Query("users").update(age=31, role="senior").where("name =", "Alice")
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        result = q.execute(db)
        print(f"  Updated: rowcount={result[0]['rowcount']}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- DELETE ---
    print("\n--- DELETE ---")
    try:
        q = Query("users").delete().where("active =", 0)
        sql, params = q.build()
        print(f"  SQL: {sql}")
        print(f"  Params: {params}")
        result = q.execute(db)
        print(f"  Deleted: rowcount={result[0]['rowcount']}")

        remaining = Query("users").select("name").execute(db)
        print(f"  Remaining: {[r['name'] for r in remaining]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # --- Reusable partial queries ---
    print("\n--- Reusable partial queries ---")
    try:
        active_users = Query("users").where("active =", 1)
        young = active_users.where("age <", 26)
        old = active_users.where("age >=", 30)

        young_results = young.execute(db)
        old_results = old.execute(db)
        print(f"  Young active: {[r['name'] for r in young_results]}")
        print(f"  Older active: {[r['name'] for r in old_results]}")

        all_active = active_users.execute(db)
        print(f"  All active (base unchanged): {[r['name'] for r in all_active]}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    db.close()

    print("\n" + "=" * 60)
    print("Implement the TODOs above to make all sections pass!")
    print("=" * 60)


if __name__ == "__main__":
    main()
