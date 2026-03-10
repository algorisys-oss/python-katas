# Kata 57 -- Query Builder

[prev: 56-migrations](./56-migrations.md) | [next: 58-websocket-protocol](./58-websocket-protocol.md)

---

## What We're Building

A **chainable query builder** that generates parameterized SQL without writing raw SQL strings. Instead of string concatenation (which invites SQL injection), you compose queries with a fluent API:

```python
q = (Query("users")
     .select("name", "email")
     .where("age >", 18)
     .where("active =", 1)
     .order_by("name")
     .limit(10))

sql, params = q.build()
# -> ("SELECT name, email FROM users WHERE age > ? AND active = ? ORDER BY name ASC LIMIT ?",
#     [18, 1, 10])
```

We build support for SELECT, INSERT, UPDATE, DELETE, plus WHERE IN, LIKE, IS NULL, ORDER BY, LIMIT, and OFFSET. Each chain step returns a new Query (immutable), so partial queries are reusable.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Method chaining | Each method returns `self` (or a clone) | Fluent API design |
| Immutable chaining | `deepcopy` on each step | Reusable partial queries |
| Builder pattern | Accumulate config, build once | Complex object construction |
| `_parse_condition()` | Split `"age >"` into column + operator | Natural query syntax |
| `WhereClause` | Dataclass for each condition | Structured WHERE generation |
| Parameterized output | Always `?` placeholders | SQL injection prevention |
| `*args` / `**kwargs` | `.select("a", "b")` and `.insert(name="x")` | Flexible APIs |

## The Code

### 1. WhereClause

Each condition is a structured object that knows how to generate SQL:

```python
@dataclass
class WhereClause:
    column: str
    operator: str
    value: Any

    def to_sql(self) -> tuple[str, list[Any]]:
        op = self.operator.upper()
        if op == "IN":
            placeholders = ", ".join("?" for _ in self.value)
            return f"{self.column} IN ({placeholders})", list(self.value)
        if op == "IS NULL":
            return f"{self.column} IS NULL", []
        return f"{self.column} {op} ?", [self.value]
```

### 2. Condition Parsing

The `where("age >", 18)` syntax parses `"age >"` into column + operator:

```python
@staticmethod
def _parse_condition(condition: str) -> tuple[str, str]:
    parts = condition.split(None, 1)
    if len(parts) == 1:
        return parts[0], "="     # Default to equality
    return parts[0], parts[1].upper()

# "age >"      -> ("age", ">")
# "name LIKE"  -> ("name", "LIKE")
# "name"       -> ("name", "=")
```

### 3. Immutable Method Chaining

Each method clones the query so partial queries are reusable:

```python
def where(self, condition, value=None):
    q = deepcopy(self)       # Clone, don't mutate
    column, op = self._parse_condition(condition)
    q._wheres.append(WhereClause(column, op, value))
    return q

# Reusable base query
active = Query("users").where("active =", 1)
young = active.where("age <", 25)   # Doesn't modify `active`
old = active.where("age >", 40)     # Doesn't modify `active`
```

### 4. Building SQL

The `build()` method assembles everything:

```python
def _build_select(self):
    cols = ", ".join(self._columns) if self._columns else "*"
    sql = f"SELECT {cols} FROM {self._table}"
    params = []

    where_sql, where_params = self._build_where()
    if where_sql:
        sql += f" WHERE {where_sql}"
        params.extend(where_params)

    if self._order_by:
        sql += " ORDER BY " + ", ".join(self._order_by)
    if self._limit_val is not None:
        sql += " LIMIT ?"
        params.append(self._limit_val)
    return sql, params
```

### 5. INSERT, UPDATE, DELETE

```python
# INSERT
Query("users").insert(name="Alice", email="a@x.com", age=30)
# -> INSERT INTO users (name, email, age) VALUES (?, ?, ?)

# UPDATE with WHERE
Query("users").update(age=31).where("name =", "Alice")
# -> UPDATE users SET age = ? WHERE name = ?

# DELETE with WHERE
Query("users").delete().where("active =", 0)
# -> DELETE FROM users WHERE active = ?
```

## Playground

Open **`playground/57_query_builder.py`** and run:

```bash
python playground/57_query_builder.py
```

### Expected Output (excerpt)

```
============================================================
Kata 57 -- Query Builder
============================================================

--- Basic SELECT ---
  SQL: SELECT * FROM users
  Params: []
  Results: 5 rows

--- WHERE clause ---
  SQL: SELECT * FROM users WHERE age > ?
  Params: [25]
  Matches: ['Alice', 'Charlie', 'Diana']

--- Multiple WHERE (AND) ---
  SQL: SELECT * FROM users WHERE age > ? AND active = ?
  Params: [24, 1]

--- ORDER BY ---
  SQL: SELECT name, age FROM users ORDER BY age DESC
  Ordered: [('Charlie', 35), ('Alice', 30), ('Diana', 28), ('Bob', 25), ('Eve', 22)]

--- INSERT ---
  SQL: INSERT INTO users (name, email, age, active, role) VALUES (?, ?, ?, ?, ?)
  Inserted: lastrowid=6

--- UPDATE ---
  SQL: UPDATE users SET age = ?, role = ? WHERE name = ?
  Updated: rowcount=1
```

Or work through the skeleton at **`playground/skeletons/57_query_builder.py`** to build it yourself.

## How It Works

1. **`Query("users")`** creates a builder targeting the `users` table, defaulting to SELECT
2. **`.where("age >", 18)`** parses the condition, creates a `WhereClause`, clones the query, and appends
3. **`.order_by("name")`** clones and appends `"name ASC"` to the ordering list
4. **`.limit(10)`** clones and stores the limit value
5. **`.build()`** dispatches to `_build_select()`, which assembles SQL from all accumulated parts
6. **All values become `?` parameters** -- never interpolated into the SQL string
7. **`deepcopy`** on every chain step means the original query is never mutated

### Why Immutable Chaining?

```python
# Mutable (dangerous):
base = Query("users")
young = base.where("age <", 25)  # Mutates base!
old = base.where("age >", 40)    # base already has age < 25

# Immutable (safe):
base = Query("users")
young = base.where("age <", 25)  # Returns new Query
old = base.where("age >", 40)    # base is unchanged
```

The `deepcopy` approach is slightly slower but much safer for composable APIs.

## Exercises

1. **Add `.count()` builder** -- generates `SELECT COUNT(*) FROM ...` instead of `SELECT * FROM ...`
2. **Add `.join()` support** -- `Query("users").join("posts", "users.id = posts.user_id")` generates `JOIN` clause
3. **Add `.group_by()` and `.having()`** -- aggregate query support
4. **Add raw SQL escape hatch** -- `Query("users").where_raw("age > ? AND age < ?", [18, 65])` for complex conditions

## What's Next

In [Kata 58 -- WebSocket Protocol](./58-websocket-protocol.md), we move to real-time communication by implementing the WebSocket handshake and frame protocol.
