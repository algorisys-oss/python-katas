# Kata 56 -- Migrations

[prev: 55-repository-pattern](./55-repository-pattern.md) | [next: 57-query-builder](./57-query-builder.md)

---

## What We're Building

A **database migration system** for evolving schemas over time. In production, you cannot just drop and recreate tables -- you need versioned, reversible changes. We build:

1. **Migration definition** -- each migration has `up()` (apply) and `down()` (revert) functions
2. **Migration registry** -- collects and orders migrations by version
3. **Migration runner** -- tracks applied migrations in a `_migrations` table, applies pending ones in order, reverts in reverse order
4. **CLI-style interface** -- `status`, `up`, `down`, and `to` commands

This is how Alembic, Django migrations, and Rails ActiveRecord migrations work under the hood.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Migration | A versioned schema change with up/down | Evolving database schema |
| Tracking table | Records which migrations have been applied | State management |
| Up migration | Applies a schema change (CREATE, ALTER, etc.) | Moving forward |
| Down migration | Reverts a schema change (DROP, recreate, etc.) | Rolling back |
| Version ordering | Migrations run in sorted version order | Deterministic state |
| `ALTER TABLE` | Modify an existing table's schema | Adding columns |
| Backup table pattern | Recreate table to "drop" columns in SQLite | Working around SQLite limits |
| `Callable[[Cursor], None]` | Type for migration functions | Clean function signatures |
| Dataclass for config | `Migration` holds version, name, up, down | Structured metadata |

## The Code

### 1. Migration Definition

A migration is a dataclass holding its metadata and two functions:

```python
@dataclass
class Migration:
    version: str                              # "001", "002", etc.
    name: str                                 # "create_users_table"
    up: Callable[[sqlite3.Cursor], None]      # Apply the change
    down: Callable[[sqlite3.Cursor], None]    # Revert the change
```

### 2. Registry

Collects migrations and returns them sorted:

```python
class MigrationRegistry:
    def add(self, version, name, up, down) -> Migration:
        if version in self._migrations:
            raise ValueError(f"Duplicate version: {version}")
        migration = Migration(version, name, up, down)
        self._migrations[version] = migration
        return migration

    def get_all(self) -> list[Migration]:
        return sorted(self._migrations.values(), key=lambda m: m.version)
```

### 3. Runner

The runner is the brain of the system:

```python
class MigrationRunner:
    def migrate_up(self, steps=None):
        for migration in self.get_pending()[:steps]:
            with self.db.transaction() as cursor:
                migration.up(cursor)                    # Apply change
                cursor.execute(                          # Record it
                    "INSERT INTO _migrations VALUES (?, ?, ?)",
                    (migration.version, migration.name, now()),
                )

    def migrate_down(self, steps=1):
        for migration in reversed(self.get_applied())[:steps]:
            with self.db.transaction() as cursor:
                migration.down(cursor)                   # Revert change
                cursor.execute(
                    "DELETE FROM _migrations WHERE version = ?",
                    (migration.version,),
                )
```

### 4. Writing Migrations

```python
# Migration 001: Create users table
def up_001(cursor):
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    """)

def down_001(cursor):
    cursor.execute("DROP TABLE IF EXISTS users")

registry.add("001", "create_users_table", up_001, down_001)

# Migration 002: Add a column
def up_002(cursor):
    cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER DEFAULT 0")

def down_002(cursor):
    # SQLite doesn't support DROP COLUMN easily.
    # Workaround: create backup, copy data, swap tables.
    cursor.execute("CREATE TABLE users_backup (...)")
    cursor.execute("INSERT INTO users_backup SELECT id, name, email FROM users")
    cursor.execute("DROP TABLE users")
    cursor.execute("ALTER TABLE users_backup RENAME TO users")
```

## Playground

Open **`playground/56_migrations.py`** and run:

```bash
python playground/56_migrations.py
```

### Expected Output (excerpt)

```
============================================================
Kata 56 -- Migrations
============================================================

--- Initial Status ---
Migrations: 0/4 applied, 4 pending
Current version: (none)

  [ ] 001: create_users_table
  [ ] 002: add_age_to_users
  [ ] 003: create_posts_table
  [ ] 004: add_created_at_to_posts

--- Apply 1 migration ---
Applied 1 migration(s):
  + 001: create_users_table

--- Apply all remaining ---
Applied 3 migration(s):
  + 002: add_age_to_users
  + 003: create_posts_table
  + 004: add_created_at_to_posts

Migrations: 4/4 applied, 0 pending
Current version: 004

--- Revert last migration ---
Reverted 1 migration(s):
  - 004: add_created_at_to_posts
```

Or work through the skeleton at **`playground/skeletons/56_migrations.py`** to build it yourself.

## How It Works

1. **Registry** collects `Migration` objects and sorts them by version string
2. **Runner** creates a `_migrations` table to track which versions have been applied
3. **`migrate_up()`** finds pending migrations (not in `_migrations`), runs their `up()` function, and records them
4. **`migrate_down()`** takes applied migrations in reverse order, runs their `down()` function, and removes the tracking record
5. **`migrate_to()`** calculates whether to go up or down to reach the target version
6. **Each migration runs in a transaction** -- if `up()` or `down()` fails, the entire migration is rolled back

### The Backup Table Pattern

SQLite has limited `ALTER TABLE` support. To "drop a column," you:
1. Create a new table without that column
2. Copy data from the old table
3. Drop the old table
4. Rename the new table

This is a common SQLite migration pattern that more powerful databases handle with `ALTER TABLE ... DROP COLUMN`.

## Exercises

1. **Add a `reset` command** -- revert all migrations then apply all (full rebuild)
2. **Add timestamps** -- track `started_at` and `finished_at` for each migration to measure execution time
3. **Add dry-run mode** -- print what would be done without actually executing SQL
4. **Add dependency tracking** -- migrations can declare dependencies on other versions, and the runner topologically sorts them

## What's Next

In [Kata 57 -- Query Builder](./57-query-builder.md), we build a chainable API for constructing parameterized SQL queries without writing raw SQL strings.
