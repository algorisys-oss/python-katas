# Kata 54 -- SQLite Integration

[prev: 53-swagger-ui](./53-swagger-ui.md) | [next: 55-repository-pattern](./55-repository-pattern.md)

---

## What We're Building

A **database layer** using Python's built-in `sqlite3` module. Every real application needs persistent storage, and SQLite is the simplest production-quality database available -- it ships with Python, requires zero configuration, and runs entirely in-process. We build:

1. **Connection management** -- context managers that handle open/close, commit/rollback
2. **Parameterized queries** -- safe query execution that prevents SQL injection
3. **CRUD operations** -- a `UserStore` class with create, read, update, delete methods
4. **Row factories** -- dict-like access to query results instead of index-based tuples
5. **Transactions** -- atomic groups of operations that either all succeed or all rollback

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `sqlite3.connect()` | Opens a database connection | Any database operation |
| `:memory:` database | In-memory SQLite (lost on close) | Testing, prototyping |
| Context managers | Auto commit/rollback/close | Every database interaction |
| `?` placeholders | Positional parameterized queries | Preventing SQL injection |
| `:name` parameters | Named parameterized queries | Complex inserts/updates |
| `executemany()` | Bulk insert/update | Batch operations |
| `sqlite3.Row` | Access columns by name | Readable query results |
| `row_factory` | Custom result formatting | Dict-like rows |
| `PRAGMA foreign_keys` | Enable FK enforcement | Relational integrity |
| `cursor.lastrowid` | Get auto-increment ID | After INSERT |
| `cursor.rowcount` | Rows affected by last query | After UPDATE/DELETE |

## The Code

### 1. Connection Management

A `Database` class that wraps connection lifecycle in context managers:

```python
class Database:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def get_connection(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()       # Auto-commit on success
        except Exception:
            conn.rollback()     # Rollback on error
            raise
        finally:
            conn.close()        # Always close

    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row   # Dict-like rows
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
```

The layered design: `get_cursor()` uses `get_connection()`, which handles commit/rollback/close. You never forget to clean up.

### 2. Parameterized Queries

**Never** use f-strings or `.format()` for SQL:

```python
# DANGEROUS -- SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")

# SAFE -- parameterized with ?
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))

# SAFE -- named parameters
cursor.execute(
    "INSERT INTO users (name, email) VALUES (:name, :email)",
    {"name": "Alice", "email": "alice@example.com"}
)

# SAFE -- bulk insert
cursor.executemany(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    [("Alice", "a@x.com"), ("Bob", "b@x.com")]
)
```

### 3. CRUD Operations

A `UserStore` with the four fundamental data operations:

```python
# CREATE -- returns the new row ID
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
new_id = cursor.lastrowid

# READ -- find one or many
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
row = cursor.fetchone()   # Returns sqlite3.Row or None

# UPDATE -- dynamic field updates
set_clause = ", ".join(f"{key} = ?" for key in fields)
cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
updated = cursor.rowcount > 0

# DELETE -- hard or soft
cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
# Soft delete: UPDATE users SET active = 0 WHERE id = ?
```

### 4. Row Factory

Control how query results are returned:

```python
# Default: tuples
row = cursor.fetchone()    # (1, "Alice", "alice@x.com")
name = row[1]              # Index-based -- fragile

# sqlite3.Row: dict-like access
conn.row_factory = sqlite3.Row
row = cursor.fetchone()
name = row["name"]         # Name-based -- readable
keys = row.keys()          # ["id", "name", "email"]

# Custom factory: actual dicts
def dict_factory(cursor, row):
    columns = [d[0] for d in cursor.description]
    return dict(zip(columns, row))
```

### 5. Transactions

The context manager pattern ensures atomicity:

```python
# Both updates succeed or both rollback
with db.get_cursor() as cursor:
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (200, 1))
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (200, 2))
    # Committed together on exit

# If an error occurs, everything rolls back
try:
    with db.get_cursor() as cursor:
        cursor.execute("UPDATE accounts SET balance = balance - 5000 WHERE id = ?", (1,))
        # CHECK constraint fails -> IntegrityError -> rollback
except sqlite3.IntegrityError:
    pass  # Balances unchanged
```

## Playground

Open **`playground/54_sqlite_integration.py`** and run:

```bash
python playground/54_sqlite_integration.py
```

### Expected Output (excerpt)

```
============================================================
Kata 54 -- SQLite Integration
============================================================

--- Parameterized Queries ---
  Injection attempt found rows: []
  Users safe after injection attempt: 5

--- CRUD Operations ---
  Created users with IDs: 1, 2, 3
  Find by ID 1: {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'age': 30, 'active': 1}
  Updated user 1: True
  Deleted user 3: True

--- Row Factories ---
  tuple_access: id=1, name=Widget
  row_by_name: id=1, name=Widget
  dict_row: {'id': 1, 'name': 'Widget', 'price': 9.99}

--- Transactions ---
  After successful transfer: [{'owner': 'Alice', 'balance': 800.0}, {'owner': 'Bob', 'balance': 700.0}]
  After failed transfer (rolled back): [{'owner': 'Alice', 'balance': 800.0}, {'owner': 'Bob', 'balance': 700.0}]

============================================================
All SQLite integration demos passed!
============================================================
```

Or work through the skeleton at **`playground/skeletons/54_sqlite_integration.py`** to build it yourself.

## How It Works

1. **Database class** wraps `sqlite3.connect()` with PRAGMAs for foreign keys and WAL mode
2. **get_connection()** is a context manager: yields a connection, commits on success, rolls back on error, always closes
3. **get_cursor()** layers on top: sets `row_factory = sqlite3.Row` so results are dict-like
4. **Parameterized queries** use `?` or `:name` placeholders -- sqlite3 handles escaping, preventing injection
5. **CRUD methods** build SQL strings with safe placeholders and validate column names against an allowlist
6. **Transactions** are implicit in the context manager -- a group of statements either all commit or all rollback

### Why Not String Formatting?

```python
name = "'; DROP TABLE users; --"

# With f-string: executes DROP TABLE
f"SELECT * FROM users WHERE name = '{name}'"
# -> SELECT * FROM users WHERE name = ''; DROP TABLE users; --'

# With ?: treats entire string as a value
"SELECT * FROM users WHERE name = ?"  # (name,)
# -> SELECT * FROM users WHERE name = '''; DROP TABLE users; --'
```

The parameterized version sends the SQL structure and values separately. The database engine never interprets user input as SQL.

## Exercises

1. **Add a search method** -- implement `find_by_name_prefix(cursor, prefix)` that uses `LIKE` with a parameterized query (`WHERE name LIKE ? || '%'`)
2. **Add timestamps** -- modify the schema to include `created_at` and `updated_at` columns using `DEFAULT CURRENT_TIMESTAMP`
3. **Add pagination** -- implement `find_paginated(cursor, page, per_page)` using `LIMIT ? OFFSET ?`
4. **Add a related table** -- create a `posts` table with a `user_id` foreign key and demonstrate cascading deletes

## What's Next

In [Kata 55 -- Repository Pattern](./55-repository-pattern.md), we abstract the data access layer behind a clean interface, decoupling business logic from SQL details.
