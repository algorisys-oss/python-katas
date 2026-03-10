"""
Ignite Database Module

SQLite database layer with connection management, context managers,
parameterised queries, and a chainable query builder.

Self-contained -- only stdlib imports.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterator


# ---------------------------------------------------------------------------
# Database connection manager
# ---------------------------------------------------------------------------

class Database:
    """Manages SQLite connections and provides a clean query interface.

    For ``:memory:`` databases the same connection is reused so that
    tables persist.  For file-backed databases each context-manager
    call opens a fresh connection.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """Open (or reuse) a connection with sensible defaults."""
        if self.db_path == ":memory:":
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path)
                self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.row_factory = sqlite3.Row
            return self._connection

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Provide a connection that auto-commits or rolls back."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self.db_path != ":memory:":
                conn.close()

    @contextmanager
    def get_cursor(self) -> Iterator[sqlite3.Cursor]:
        """Provide a cursor (with ``sqlite3.Row`` row-factory)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Alias for :meth:`get_cursor` (matches Kata-57 API)."""
        with self.get_cursor() as cursor:
            yield cursor

    def close(self) -> None:
        """Explicitly close a kept-alive in-memory connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


# ---------------------------------------------------------------------------
# WhereClause helper
# ---------------------------------------------------------------------------

@dataclass
class WhereClause:
    """A single ``WHERE`` condition with its parameters."""
    column: str
    operator: str
    value: Any

    def to_sql(self) -> tuple[str, list[Any]]:
        op = self.operator.upper()
        if op == "IN":
            if not isinstance(self.value, (list, tuple)):
                raise ValueError("IN operator requires a list/tuple value")
            placeholders = ", ".join("?" for _ in self.value)
            return f"{self.column} IN ({placeholders})", list(self.value)
        if op == "IS NULL":
            return f"{self.column} IS NULL", []
        if op == "IS NOT NULL":
            return f"{self.column} IS NOT NULL", []
        return f"{self.column} {op} ?", [self.value]


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------

class Query:
    """Chainable SQL query builder.

    Every mutating method returns a **new** ``Query`` (immutable chaining)
    so partial queries can be reused safely.

    Example::

        q = (Query("users")
             .select("name", "email")
             .where("age >", 18)
             .order_by("name")
             .limit(10))
        sql, params = q.build()
    """

    OPERATORS = {
        "=", "!=", "<", ">", "<=", ">=", "LIKE", "IN",
        "IS NULL", "IS NOT NULL",
    }

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
        return deepcopy(self)

    # -- SELECT --------------------------------------------------------------

    def select(self, *columns: str) -> Query:
        q = self._clone()
        q._type = "SELECT"
        q._columns = list(columns)
        return q

    # -- WHERE ---------------------------------------------------------------

    def where(self, condition: str, value: Any = None) -> Query:
        q = self._clone()
        column, operator = self._parse_condition(condition)
        q._wheres.append(WhereClause(column=column, operator=operator, value=value))
        return q

    def or_where(self, condition: str, value: Any = None) -> Query:
        q = self._clone()
        column, operator = self._parse_condition(condition)
        q._or_wheres.append(WhereClause(column=column, operator=operator, value=value))
        return q

    def where_in(self, column: str, values: list[Any]) -> Query:
        q = self._clone()
        q._wheres.append(WhereClause(column=column, operator="IN", value=values))
        return q

    def where_null(self, column: str) -> Query:
        q = self._clone()
        q._wheres.append(WhereClause(column=column, operator="IS NULL", value=None))
        return q

    def where_not_null(self, column: str) -> Query:
        q = self._clone()
        q._wheres.append(WhereClause(column=column, operator="IS NOT NULL", value=None))
        return q

    # -- ORDER BY / LIMIT / OFFSET ------------------------------------------

    def order_by(self, column: str, direction: str = "ASC") -> Query:
        q = self._clone()
        direction = direction.upper()
        if direction not in ("ASC", "DESC"):
            raise ValueError(f"Invalid direction: {direction}")
        q._order_by.append(f"{column} {direction}")
        return q

    def limit(self, n: int) -> Query:
        q = self._clone()
        q._limit_val = n
        return q

    def offset(self, n: int) -> Query:
        q = self._clone()
        q._offset_val = n
        return q

    # -- INSERT / UPDATE / DELETE --------------------------------------------

    def insert(self, **values: Any) -> Query:
        q = self._clone()
        q._type = "INSERT"
        q._values = values
        return q

    def update(self, **values: Any) -> Query:
        q = self._clone()
        q._type = "UPDATE"
        q._values = values
        return q

    def delete(self) -> Query:
        q = self._clone()
        q._type = "DELETE"
        return q

    # -- BUILD ---------------------------------------------------------------

    def build(self) -> tuple[str, list[Any]]:
        """Generate ``(sql, params)`` ready for ``cursor.execute``."""
        builders = {
            "SELECT": self._build_select,
            "INSERT": self._build_insert,
            "UPDATE": self._build_update,
            "DELETE": self._build_delete,
        }
        builder = builders.get(self._type)
        if builder is None:
            raise ValueError(f"Unknown query type: {self._type}")
        return builder()

    def _build_select(self) -> tuple[str, list[Any]]:
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols} FROM {self._table}"
        params: list[Any] = []
        where_sql, where_params = self._build_where()
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)
        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)
        if self._limit_val is not None:
            sql += " LIMIT ?"
            params.append(self._limit_val)
        if self._offset_val is not None:
            sql += " OFFSET ?"
            params.append(self._offset_val)
        return sql, params

    def _build_insert(self) -> tuple[str, list[Any]]:
        if not self._values:
            raise ValueError("INSERT requires values")
        cols = ", ".join(self._values.keys())
        placeholders = ", ".join("?" for _ in self._values)
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        return sql, list(self._values.values())

    def _build_update(self) -> tuple[str, list[Any]]:
        if not self._values:
            raise ValueError("UPDATE requires values")
        set_clause = ", ".join(f"{c} = ?" for c in self._values)
        sql = f"UPDATE {self._table} SET {set_clause}"
        params = list(self._values.values())
        where_sql, where_params = self._build_where()
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)
        return sql, params

    def _build_delete(self) -> tuple[str, list[Any]]:
        sql = f"DELETE FROM {self._table}"
        params: list[Any] = []
        where_sql, where_params = self._build_where()
        if where_sql:
            sql += f" WHERE {where_sql}"
            params.extend(where_params)
        return sql, params

    def _build_where(self) -> tuple[str, list[Any]]:
        if not self._wheres and not self._or_wheres:
            return "", []
        parts: list[str] = []
        params: list[Any] = []
        for clause in self._wheres:
            frag, p = clause.to_sql()
            parts.append(frag)
            params.extend(p)
        and_sql = " AND ".join(parts) if parts else ""
        or_parts: list[str] = []
        for clause in self._or_wheres:
            frag, p = clause.to_sql()
            or_parts.append(frag)
            params.extend(p)
        if and_sql and or_parts:
            return f"({and_sql}) OR {' OR '.join(or_parts)}", params
        if and_sql:
            return and_sql, params
        return " OR ".join(or_parts), params

    @staticmethod
    def _parse_condition(condition: str) -> tuple[str, str]:
        upper = condition.upper()
        for op in ("IS NOT NULL", "IS NULL"):
            if upper.endswith(op):
                column = condition[: -len(op)].strip()
                return column, op
        parts = condition.split(None, 1)
        if len(parts) == 1:
            return parts[0], "="
        return parts[0], parts[1].upper()

    # -- Execute -------------------------------------------------------------

    def execute(self, db: Database) -> list[dict[str, Any]]:
        """Execute against *db* and return results as dicts."""
        sql, params = self.build()
        with db.transaction() as cursor:
            cursor.execute(sql, params)
            if self._type == "SELECT":
                return [dict(row) for row in cursor.fetchall()]
            if self._type == "INSERT":
                return [{"lastrowid": cursor.lastrowid}]
            return [{"rowcount": cursor.rowcount}]

    def __repr__(self) -> str:
        sql, params = self.build()
        return f"Query({sql!r}, {params!r})"
