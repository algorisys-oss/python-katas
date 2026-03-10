"""
Kata 77 -- Todo API (Capstone 1)
Run: python playground/77_todo_api.py

Build a complete Todo REST API showcasing all Ignite features: route
decorators, path/query params, request body validation, response models,
error handling, middleware (logging, CORS), dependency injection, SQLite
repository, health checks. Full CRUD tested with TestClient.

Completes within 5 seconds.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Framework Core (Ignite Mini)
# ===========================================================================
# A compact version of the Ignite framework combining features from
# previous katas. This is what we've been building toward.

@dataclass
class Request:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    path_params: dict[str, str] = field(default_factory=dict)
    client_ip: str = "127.0.0.1"


@dataclass
class Response:
    status_code: int = 200
    body: dict[str, Any] | list | None = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=lambda: {"content-type": "application/json"})

    @property
    def json(self) -> Any:
        return self.body


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = "Error"):
        self.status_code = status_code
        self.detail = detail


class IgniteApp:
    """Compact Ignite framework with all key features."""

    def __init__(self):
        self._routes: dict[tuple[str, str], Callable] = {}
        self._dependencies: dict[str, Callable] = {}
        self._dependency_overrides: dict[str, Callable] = {}
        self._middleware: list[Callable] = []
        self._health_checks: dict[str, Callable] = {}

    # -- Routing --
    def route(self, path: str, method: str = "GET"):
        def decorator(func):
            self._routes[(method.upper(), path)] = func
            return func
        return decorator

    def get(self, path: str):
        return self.route(path, "GET")

    def post(self, path: str):
        return self.route(path, "POST")

    def put(self, path: str):
        return self.route(path, "PUT")

    def delete(self, path: str):
        return self.route(path, "DELETE")

    # -- Dependency Injection --
    def dependency(self, name: str, factory: Callable):
        self._dependencies[name] = factory

    def resolve(self, name: str) -> Any:
        if name in self._dependency_overrides:
            return self._dependency_overrides[name]()
        if name in self._dependencies:
            return self._dependencies[name]()
        raise KeyError(f"Unknown dependency: {name}")

    # -- Middleware --
    def add_middleware(self, mw: Callable):
        self._middleware.append(mw)

    # -- Health Checks --
    def health_check(self, name: str, check: Callable):
        self._health_checks[name] = check

    # -- Request Handling --
    def _match_route(self, method: str, path: str) -> tuple[Callable | None, dict[str, str]]:
        """Match a route, supporting path parameters like /todos/{id}."""
        key = (method, path)
        if key in self._routes:
            return self._routes[key], {}

        # Try pattern matching for path params
        for (m, pattern), handler in self._routes.items():
            if m != method:
                continue
            if "{" not in pattern:
                continue
            pattern_parts = pattern.split("/")
            path_parts = path.split("/")
            if len(pattern_parts) != len(path_parts):
                continue
            params = {}
            match = True
            for pp, rp in zip(pattern_parts, path_parts):
                if pp.startswith("{") and pp.endswith("}"):
                    params[pp[1:-1]] = rp
                elif pp != rp:
                    match = False
                    break
            if match:
                return handler, params

        return None, {}

    def handle_request(self, request: Request) -> Response:
        try:
            # Run middleware before route matching (e.g. CORS preflight)
            for mw in self._middleware:
                result = mw(request)
                if isinstance(result, Response):
                    return result

            handler, path_params = self._match_route(request.method.upper(), request.path)
            if handler is None:
                raise HTTPException(404, f"Not Found: {request.path}")

            request.path_params = path_params

            result = handler(request)
            if isinstance(result, Response):
                return result
            if isinstance(result, (dict, list)):
                return Response(status_code=200, body=result)
            return Response(status_code=200, body={"result": result})

        except HTTPException as exc:
            return Response(
                status_code=exc.status_code,
                body={"error": {"status_code": exc.status_code, "detail": exc.detail}},
            )
        except Exception as exc:
            return Response(
                status_code=500,
                body={"error": {"status_code": 500, "detail": str(exc)}},
            )


# ===========================================================================
# SECTION 2: TestClient
# ===========================================================================

class TestClient:
    def __init__(self, app: IgniteApp):
        self.app = app

    def _request(self, method, path, *, headers=None, query_params=None,
                 json_body=None, client_ip="testclient"):
        req = Request(
            method=method.upper(), path=path,
            headers=headers or {}, query_params=query_params or {},
            body=json_body, client_ip=client_ip,
        )
        return self.app.handle_request(req)

    def get(self, path, **kw): return self._request("GET", path, **kw)
    def post(self, path, **kw): return self._request("POST", path, **kw)
    def put(self, path, **kw): return self._request("PUT", path, **kw)
    def delete(self, path, **kw): return self._request("DELETE", path, **kw)


# ===========================================================================
# SECTION 3: SQLite Todo Repository
# ===========================================================================
# Persistent storage using SQLite. The repository pattern abstracts
# database operations behind a clean interface.

class TodoRepository:
    """SQLite-backed todo storage."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                done INTEGER DEFAULT 0,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self.conn.commit()

    def list_all(self, *, done: bool | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
        """List todos with optional filtering."""
        query = "SELECT * FROM todos"
        params: list[Any] = []
        if done is not None:
            query += " WHERE done = ?"
            params.append(1 if done else 0)
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_by_id(self, todo_id: int) -> dict | None:
        """Get a single todo by ID."""
        row = self.conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def create(self, title: str, description: str = "") -> dict:
        """Create a new todo."""
        cursor = self.conn.execute(
            "INSERT INTO todos (title, description) VALUES (?, ?)",
            (title, description),
        )
        self.conn.commit()
        return self.get_by_id(cursor.lastrowid)

    def update(self, todo_id: int, **fields) -> dict | None:
        """Update a todo's fields."""
        existing = self.get_by_id(todo_id)
        if existing is None:
            return None

        updates = []
        params = []
        for key, value in fields.items():
            if key in ("title", "description"):
                updates.append(f"{key} = ?")
                params.append(value)
            elif key == "done":
                updates.append("done = ?")
                params.append(1 if value else 0)

        if not updates:
            return existing

        params.append(todo_id)
        self.conn.execute(
            f"UPDATE todos SET {', '.join(updates)} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_by_id(todo_id)

    def delete(self, todo_id: int) -> bool:
        """Delete a todo. Returns True if it existed."""
        cursor = self.conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM todos").fetchone()
        return row["cnt"]

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "done": bool(row["done"]),
            "created_at": row["created_at"],
        }


# ===========================================================================
# SECTION 4: Middleware
# ===========================================================================

def create_logging_middleware() -> tuple[Callable, list]:
    """Create logging middleware that records all requests."""
    log: list[str] = []

    def middleware(request: Request):
        log.append(f"{request.method} {request.path}")
        return None  # Continue processing

    return middleware, log


def create_cors_middleware(allowed_origins: list[str] | None = None) -> Callable:
    """Create CORS middleware that adds headers to responses."""
    origins = allowed_origins or ["*"]

    # Note: In a real framework, CORS middleware modifies the response.
    # Here we use a simpler approach since our middleware runs before the handler.
    def middleware(request: Request):
        # For OPTIONS preflight, return immediately
        if request.method == "OPTIONS":
            return Response(
                status_code=204,
                body={},
                headers={
                    "Access-Control-Allow-Origin": origins[0],
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                },
            )
        return None

    return middleware


# ===========================================================================
# SECTION 5: Todo API Routes
# ===========================================================================
# Register all REST API routes for the Todo application.

def register_todo_routes(app: IgniteApp):
    """Register Todo CRUD routes on the app."""

    @app.get("/todos")
    def list_todos(request: Request) -> Response:
        repo = app.resolve("todo_repo")
        done_param = request.query_params.get("done")
        done_filter = None
        if done_param == "true":
            done_filter = True
        elif done_param == "false":
            done_filter = False
        limit = int(request.query_params.get("limit", "100"))
        offset = int(request.query_params.get("offset", "0"))

        todos = repo.list_all(done=done_filter, limit=limit, offset=offset)
        total = repo.count()
        return Response(
            status_code=200,
            body={"todos": todos, "total": total, "limit": limit, "offset": offset},
        )

    @app.post("/todos")
    def create_todo(request: Request) -> Response:
        repo = app.resolve("todo_repo")
        body = request.body or {}

        # Validation
        if "title" not in body or not body["title"].strip():
            raise HTTPException(422, "title is required and cannot be empty")

        title = body["title"].strip()
        description = body.get("description", "")

        todo = repo.create(title, description)
        return Response(status_code=201, body=todo)

    @app.get("/todos/{id}")
    def get_todo(request: Request) -> Response:
        repo = app.resolve("todo_repo")
        todo_id = int(request.path_params["id"])
        todo = repo.get_by_id(todo_id)
        if todo is None:
            raise HTTPException(404, f"Todo {todo_id} not found")
        return Response(status_code=200, body=todo)

    @app.put("/todos/{id}")
    def update_todo(request: Request) -> Response:
        repo = app.resolve("todo_repo")
        todo_id = int(request.path_params["id"])
        body = request.body or {}

        todo = repo.update(todo_id, **body)
        if todo is None:
            raise HTTPException(404, f"Todo {todo_id} not found")
        return Response(status_code=200, body=todo)

    @app.delete("/todos/{id}")
    def delete_todo(request: Request) -> Response:
        repo = app.resolve("todo_repo")
        todo_id = int(request.path_params["id"])
        deleted = repo.delete(todo_id)
        if not deleted:
            raise HTTPException(404, f"Todo {todo_id} not found")
        return Response(status_code=204, body={})

    # Health check endpoint
    @app.get("/health")
    def health(request: Request) -> dict:
        checks = {}
        for name, check_fn in app._health_checks.items():
            try:
                checks[name] = check_fn()
            except Exception as exc:
                checks[name] = {"status": "unhealthy", "error": str(exc)}
        all_healthy = all(
            c.get("status") == "healthy" if isinstance(c, dict) else c
            for c in checks.values()
        )
        status = "healthy" if all_healthy else "unhealthy"
        return {"status": status, "checks": checks}


# ===========================================================================
# SECTION 6: App Factory
# ===========================================================================

def create_app(db_path: str = ":memory:") -> IgniteApp:
    """Create and configure the Todo API application."""
    app = IgniteApp()

    # Dependencies
    repo = TodoRepository(db_path)
    app.dependency("todo_repo", lambda: repo)

    # Middleware
    logging_mw, _ = create_logging_middleware()
    app.add_middleware(logging_mw)
    app.add_middleware(create_cors_middleware(["http://localhost:3000"]))

    # Health checks
    app.health_check("database", lambda: {"status": "healthy", "type": "sqlite"})

    # Routes
    register_todo_routes(app)

    return app


# ===========================================================================
# SECTION 7: Demos
# ===========================================================================

def demo_create_todos():
    """Test creating todos."""
    print("--- Section 1: Create Todos ---")

    app = create_app()
    client = TestClient(app)

    # Create a todo
    resp = client.post("/todos", json_body={"title": "Buy groceries", "description": "Milk, eggs, bread"})
    print(f"  POST /todos -> {resp.status_code}: {resp.json}")
    assert resp.status_code == 201
    assert resp.json["title"] == "Buy groceries"
    assert resp.json["done"] is False
    assert resp.json["id"] == 1

    # Create another
    resp2 = client.post("/todos", json_body={"title": "Write tests"})
    assert resp2.status_code == 201
    assert resp2.json["id"] == 2

    # Validation: missing title
    resp3 = client.post("/todos", json_body={})
    assert resp3.status_code == 422
    print(f"  Missing title -> {resp3.status_code}: {resp3.json['error']['detail']}")

    # Validation: empty title
    resp4 = client.post("/todos", json_body={"title": "  "})
    assert resp4.status_code == 422
    print(f"  Empty title -> {resp4.status_code}")

    print("  [PASS] Create todos works")


def demo_list_todos():
    """Test listing todos with filtering."""
    print("\n--- Section 2: List Todos ---")

    app = create_app()
    client = TestClient(app)

    # Create some todos
    client.post("/todos", json_body={"title": "Task 1"})
    client.post("/todos", json_body={"title": "Task 2"})
    client.post("/todos", json_body={"title": "Task 3"})

    # Complete one
    client.put("/todos/2", json_body={"done": True})

    # List all
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.json["total"] == 3
    print(f"  All todos: {resp.json['total']} items")

    # Filter by done
    resp2 = client.get("/todos", query_params={"done": "true"})
    assert len(resp2.json["todos"]) == 1
    assert resp2.json["todos"][0]["title"] == "Task 2"
    print(f"  Done todos: {len(resp2.json['todos'])} items")

    # Filter by not done
    resp3 = client.get("/todos", query_params={"done": "false"})
    assert len(resp3.json["todos"]) == 2
    print(f"  Pending todos: {len(resp3.json['todos'])} items")

    # Pagination
    resp4 = client.get("/todos", query_params={"limit": "2", "offset": "0"})
    assert len(resp4.json["todos"]) == 2
    print(f"  Page 1 (limit=2): {len(resp4.json['todos'])} items")

    resp5 = client.get("/todos", query_params={"limit": "2", "offset": "2"})
    assert len(resp5.json["todos"]) == 1
    print(f"  Page 2 (limit=2): {len(resp5.json['todos'])} items")

    print("  [PASS] List todos works")


def demo_get_todo():
    """Test getting a single todo."""
    print("\n--- Section 3: Get Todo ---")

    app = create_app()
    client = TestClient(app)

    client.post("/todos", json_body={"title": "My Task", "description": "Details here"})

    resp = client.get("/todos/1")
    assert resp.status_code == 200
    assert resp.json["title"] == "My Task"
    assert resp.json["description"] == "Details here"
    print(f"  GET /todos/1 -> {resp.json['title']}")

    # Not found
    resp2 = client.get("/todos/999")
    assert resp2.status_code == 404
    print(f"  GET /todos/999 -> {resp2.status_code}")

    print("  [PASS] Get todo works")


def demo_update_todo():
    """Test updating todos."""
    print("\n--- Section 4: Update Todo ---")

    app = create_app()
    client = TestClient(app)

    client.post("/todos", json_body={"title": "Original Title"})

    # Update title
    resp = client.put("/todos/1", json_body={"title": "Updated Title"})
    assert resp.status_code == 200
    assert resp.json["title"] == "Updated Title"
    print(f"  Update title: {resp.json['title']}")

    # Mark as done
    resp2 = client.put("/todos/1", json_body={"done": True})
    assert resp2.status_code == 200
    assert resp2.json["done"] is True
    print(f"  Mark done: {resp2.json['done']}")

    # Update description
    resp3 = client.put("/todos/1", json_body={"description": "New description"})
    assert resp3.json["description"] == "New description"
    print(f"  Update description: {resp3.json['description']}")

    # Not found
    resp4 = client.put("/todos/999", json_body={"title": "X"})
    assert resp4.status_code == 404
    print(f"  PUT /todos/999 -> {resp4.status_code}")

    print("  [PASS] Update todo works")


def demo_delete_todo():
    """Test deleting todos."""
    print("\n--- Section 5: Delete Todo ---")

    app = create_app()
    client = TestClient(app)

    client.post("/todos", json_body={"title": "To Delete"})

    # Delete
    resp = client.delete("/todos/1")
    assert resp.status_code == 204
    print(f"  DELETE /todos/1 -> {resp.status_code}")

    # Verify gone
    resp2 = client.get("/todos/1")
    assert resp2.status_code == 404
    print(f"  GET /todos/1 after delete -> {resp2.status_code}")

    # Delete again -> 404
    resp3 = client.delete("/todos/1")
    assert resp3.status_code == 404
    print(f"  DELETE /todos/1 again -> {resp3.status_code}")

    print("  [PASS] Delete todo works")


def demo_middleware():
    """Test middleware integration."""
    print("\n--- Section 6: Middleware ---")

    app = IgniteApp()
    log_mw, log = create_logging_middleware()
    app.add_middleware(log_mw)
    app.add_middleware(create_cors_middleware(["http://localhost:3000"]))

    repo = TodoRepository(":memory:")
    app.dependency("todo_repo", lambda: repo)
    register_todo_routes(app)

    client = TestClient(app)

    client.post("/todos", json_body={"title": "Test"})
    client.get("/todos")

    print(f"  Request log: {log}")
    assert len(log) == 2
    assert "POST /todos" in log
    assert "GET /todos" in log

    # CORS preflight
    resp = client._request("OPTIONS", "/todos")
    assert resp.status_code == 204
    assert "Access-Control-Allow-Origin" in resp.headers
    print(f"  OPTIONS /todos -> {resp.status_code} (CORS preflight)")

    print("  [PASS] Middleware works")


def demo_health_check():
    """Test health check endpoint."""
    print("\n--- Section 7: Health Check ---")

    app = create_app()
    client = TestClient(app)

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "healthy"
    print(f"  GET /health -> {resp.json}")

    print("  [PASS] Health check works")


def demo_full_workflow():
    """Test a complete user workflow."""
    print("\n--- Section 8: Full Workflow ---")

    app = create_app()
    client = TestClient(app)

    # 1. Start with empty list
    resp = client.get("/todos")
    assert resp.json["total"] == 0
    print("  1. Empty todo list")

    # 2. Create todos
    client.post("/todos", json_body={"title": "Learn Python", "description": "Katas 1-78"})
    client.post("/todos", json_body={"title": "Build Ignite", "description": "Web framework"})
    client.post("/todos", json_body={"title": "Deploy App", "description": "To production"})
    print("  2. Created 3 todos")

    # 3. List all
    resp = client.get("/todos")
    assert resp.json["total"] == 3
    print(f"  3. Listed {resp.json['total']} todos")

    # 4. Get specific todo
    resp = client.get("/todos/1")
    assert resp.json["title"] == "Learn Python"
    print(f"  4. Got todo: {resp.json['title']}")

    # 5. Update todo
    client.put("/todos/1", json_body={"done": True})
    resp = client.get("/todos/1")
    assert resp.json["done"] is True
    print(f"  5. Marked todo 1 as done: {resp.json['done']}")

    # 6. Filter completed
    resp = client.get("/todos", query_params={"done": "true"})
    assert len(resp.json["todos"]) == 1
    print(f"  6. Completed todos: {len(resp.json['todos'])}")

    # 7. Delete a todo
    client.delete("/todos/3")
    resp = client.get("/todos")
    assert resp.json["total"] == 2
    print(f"  7. After delete: {resp.json['total']} todos")

    # 8. Health check
    resp = client.get("/health")
    assert resp.json["status"] == "healthy"
    print(f"  8. Health: {resp.json['status']}")

    print("  [PASS] Full workflow works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_create_todos()
    demo_list_todos()
    demo_get_todo()
    demo_update_todo()
    demo_delete_todo()
    demo_middleware()
    demo_health_check()
    demo_full_workflow()

    print("\n--- Summary ---")
    print("The Todo API capstone combines:")
    print("  - IgniteApp with route decorators (@app.get, @app.post, etc.)")
    print("  - Path parameters (/todos/{id})")
    print("  - Query parameters (?done=true&limit=10)")
    print("  - Request body validation")
    print("  - SQLite repository with CRUD operations")
    print("  - Error handling (404, 422 with detail messages)")
    print("  - Middleware (logging, CORS)")
    print("  - Dependency injection (todo_repo)")
    print("  - Health check endpoint")
    print("  - TestClient for comprehensive testing")
    print("\nAll 8 sections passed. Todo API capstone complete!")
    print("Next up: Kata 78 -- real-time chat capstone!")


if __name__ == "__main__":
    main()
