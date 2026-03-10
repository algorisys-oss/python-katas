"""
Kata 76 -- Testing Utilities
Run: python playground/76_testing_utilities.py

Build Ignite testing utilities: TestClient for simulated ASGI requests,
dependency override mechanism, test helper functions, and patterns for
testing Ignite apps without a real server.

Completes within 5 seconds.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Simulated HTTP Types
# ===========================================================================
# Minimal request/response types for our Ignite framework. In a real
# framework these would be full ASGI-compatible objects.

@dataclass
class Request:
    """Simulated HTTP request."""
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    client_ip: str = "127.0.0.1"


@dataclass
class Response:
    """Simulated HTTP response."""
    status_code: int = 200
    body: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=lambda: {"content-type": "application/json"})

    @property
    def json(self) -> dict[str, Any]:
        return self.body

    @property
    def text(self) -> str:
        return json.dumps(self.body)


# ===========================================================================
# SECTION 2: Ignite App (Simplified)
# ===========================================================================
# A simplified Ignite app that supports route registration, dependency
# injection, and middleware -- enough to demonstrate testing patterns.

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = "Error"):
        self.status_code = status_code
        self.detail = detail


class IgniteApp:
    """Simplified Ignite application for testing demos."""

    def __init__(self):
        self._routes: dict[tuple[str, str], Callable] = {}
        self._dependencies: dict[str, Callable] = {}
        self._dependency_overrides: dict[str, Callable] = {}
        self._middleware: list[Callable] = []

    # -- Routing --

    def route(self, path: str, method: str = "GET"):
        """Register a route handler."""
        def decorator(func: Callable) -> Callable:
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

    def dependency(self, name: str, factory: Callable) -> None:
        """Register a dependency factory."""
        self._dependencies[name] = factory

    def resolve_dependency(self, name: str) -> Any:
        """Resolve a dependency, using override if set."""
        # Overrides take priority (this is the key testing feature)
        if name in self._dependency_overrides:
            return self._dependency_overrides[name]()
        if name in self._dependencies:
            return self._dependencies[name]()
        raise KeyError(f"Unknown dependency: {name}")

    # -- Middleware --

    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the pipeline."""
        self._middleware.append(middleware)

    # -- Request Processing --

    def handle_request(self, request: Request) -> Response:
        """Process a request through the middleware and route handler."""
        try:
            # Find route handler
            key = (request.method.upper(), request.path)
            handler = self._routes.get(key)
            if handler is None:
                raise HTTPException(404, f"Not Found: {request.path}")

            # Run middleware (simplified: before-only)
            for mw in self._middleware:
                result = mw(request)
                if isinstance(result, Response):
                    return result  # Middleware short-circuited

            # Call handler
            result = handler(request)

            if isinstance(result, Response):
                return result
            if isinstance(result, dict):
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
# SECTION 3: TestClient
# ===========================================================================
# The TestClient sends simulated requests to an IgniteApp without starting
# a real HTTP server. This is how FastAPI's TestClient and Django's
# test client work.

class TestClient:
    """Test client for Ignite apps.

    Sends simulated HTTP requests without starting a server.
    Provides a clean API for writing tests.

    Usage:
        app = IgniteApp()
        client = TestClient(app)
        response = client.get("/users")
        assert response.status_code == 200
    """

    def __init__(self, app: IgniteApp):
        self.app = app

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        client_ip: str = "testclient",
    ) -> Response:
        """Send a simulated request to the app."""
        request = Request(
            method=method.upper(),
            path=path,
            headers=headers or {},
            query_params=query_params or {},
            body=json_body,
            client_ip=client_ip,
        )
        return self.app.handle_request(request)

    def get(self, path: str, **kwargs) -> Response:
        """Send a GET request."""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Response:
        """Send a POST request."""
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> Response:
        """Send a PUT request."""
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> Response:
        """Send a DELETE request."""
        return self._request("DELETE", path, **kwargs)

    def patch(self, path: str, **kwargs) -> Response:
        """Send a PATCH request."""
        return self._request("PATCH", path, **kwargs)


# ===========================================================================
# SECTION 4: Dependency Overrides
# ===========================================================================
# In tests, you want to replace real dependencies (database, external API)
# with fakes/mocks. The override mechanism makes this clean.

class DependencyOverrideContext:
    """Context manager for temporarily overriding dependencies.

    Usage:
        with DependencyOverrideContext(app, {"db": lambda: FakeDB()}):
            response = client.get("/users")
            # Uses FakeDB instead of real database
        # Original dependencies restored
    """

    def __init__(self, app: IgniteApp, overrides: dict[str, Callable]):
        self.app = app
        self.overrides = overrides
        self._saved: dict[str, Callable] = {}

    def __enter__(self):
        # Save existing overrides and apply new ones
        for name, factory in self.overrides.items():
            if name in self.app._dependency_overrides:
                self._saved[name] = self.app._dependency_overrides[name]
            self.app._dependency_overrides[name] = factory
        return self

    def __exit__(self, *args):
        # Restore original state
        for name in self.overrides:
            if name in self._saved:
                self.app._dependency_overrides[name] = self._saved[name]
            else:
                self.app._dependency_overrides.pop(name, None)


# ===========================================================================
# SECTION 5: Test Helpers
# ===========================================================================
# Utility functions that make writing tests more concise.

def assert_status(response: Response, expected: int, msg: str = "") -> None:
    """Assert response has the expected status code."""
    assert response.status_code == expected, (
        f"Expected status {expected}, got {response.status_code}"
        f"{': ' + msg if msg else ''}"
    )


def assert_json_contains(response: Response, key: str, value: Any = ...) -> None:
    """Assert response JSON contains a key (optionally with a specific value)."""
    assert key in response.json, f"Key '{key}' not found in response: {response.json}"
    if value is not ...:
        assert response.json[key] == value, (
            f"Expected {key}={value!r}, got {response.json[key]!r}"
        )


def assert_error(response: Response, status_code: int, detail_contains: str = "") -> None:
    """Assert response is an error with expected status and detail."""
    assert_status(response, status_code)
    assert "error" in response.json, f"No 'error' key in response: {response.json}"
    if detail_contains:
        detail = response.json["error"].get("detail", "")
        assert detail_contains in detail, (
            f"Expected detail to contain {detail_contains!r}, got {detail!r}"
        )


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_test_client():
    """Show TestClient usage."""
    print("--- Section 1: TestClient ---")

    app = IgniteApp()

    @app.get("/users")
    def list_users(request: Request) -> dict:
        return {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

    @app.get("/users/1")
    def get_user(request: Request) -> dict:
        return {"id": 1, "name": "Alice", "email": "alice@example.com"}

    @app.post("/users")
    def create_user(request: Request) -> Response:
        body = request.body or {}
        return Response(
            status_code=201,
            body={"id": 3, "name": body.get("name", "Unknown")},
        )

    client = TestClient(app)

    # GET request
    resp = client.get("/users")
    print(f"  GET /users -> {resp.status_code}")
    assert resp.status_code == 200
    assert len(resp.json["users"]) == 2

    # GET with path
    resp2 = client.get("/users/1")
    print(f"  GET /users/1 -> {resp2.status_code}: {resp2.json['name']}")
    assert resp2.json["name"] == "Alice"

    # POST with JSON body
    resp3 = client.post("/users", json_body={"name": "Charlie"})
    print(f"  POST /users -> {resp3.status_code}: {resp3.json}")
    assert resp3.status_code == 201
    assert resp3.json["name"] == "Charlie"

    # 404 for unknown route
    resp4 = client.get("/nonexistent")
    print(f"  GET /nonexistent -> {resp4.status_code}")
    assert resp4.status_code == 404

    print("  [PASS] TestClient works")


def demo_dependency_overrides():
    """Show dependency override mechanism."""
    print("\n--- Section 2: Dependency Overrides ---")

    app = IgniteApp()

    # Real database dependency
    class RealDatabase:
        def get_users(self):
            return [{"id": 1, "name": "Alice"}]  # Would query real DB

    app.dependency("db", RealDatabase)

    @app.get("/users")
    def list_users(request: Request) -> dict:
        db = app.resolve_dependency("db")
        return {"users": db.get_users()}

    client = TestClient(app)

    # Without override: uses real dependency
    resp1 = client.get("/users")
    print(f"  Real DB: {resp1.json}")
    assert resp1.json["users"][0]["name"] == "Alice"

    # With override: uses fake dependency
    class FakeDatabase:
        def get_users(self):
            return [{"id": 99, "name": "TestUser"}]

    with DependencyOverrideContext(app, {"db": FakeDatabase}):
        resp2 = client.get("/users")
        print(f"  Fake DB: {resp2.json}")
        assert resp2.json["users"][0]["name"] == "TestUser"

    # After context: back to real dependency
    resp3 = client.get("/users")
    print(f"  Back to real: {resp3.json}")
    assert resp3.json["users"][0]["name"] == "Alice"

    print("  [PASS] Dependency overrides work")


def demo_test_helpers():
    """Show test helper functions."""
    print("\n--- Section 3: Test Helpers ---")

    app = IgniteApp()

    @app.get("/ok")
    def ok_handler(request: Request) -> dict:
        return {"message": "hello", "count": 42}

    @app.get("/fail")
    def fail_handler(request: Request):
        raise HTTPException(403, "Access denied")

    client = TestClient(app)

    # assert_status
    resp = client.get("/ok")
    assert_status(resp, 200)
    print("  assert_status(200): passed")

    # assert_json_contains
    assert_json_contains(resp, "message", "hello")
    assert_json_contains(resp, "count", 42)
    assert_json_contains(resp, "message")  # Just check key exists
    print("  assert_json_contains: passed")

    # assert_error
    resp2 = client.get("/fail")
    assert_error(resp2, 403, "Access denied")
    print("  assert_error(403, 'Access denied'): passed")

    print("  [PASS] Test helpers work")


def demo_testing_middleware():
    """Show testing apps with middleware."""
    print("\n--- Section 4: Testing Middleware ---")

    app = IgniteApp()
    middleware_log = []

    def logging_middleware(request: Request):
        middleware_log.append(f"{request.method} {request.path}")
        return None  # Continue processing

    def auth_middleware(request: Request):
        if request.path.startswith("/admin"):
            token = request.headers.get("Authorization")
            if token != "Bearer secret":
                return Response(
                    status_code=401,
                    body={"error": {"status_code": 401, "detail": "Unauthorized"}},
                )
        return None

    app.add_middleware(logging_middleware)
    app.add_middleware(auth_middleware)

    @app.get("/public")
    def public_route(request: Request) -> dict:
        return {"page": "public"}

    @app.get("/admin/dashboard")
    def admin_route(request: Request) -> dict:
        return {"page": "admin dashboard"}

    client = TestClient(app)

    # Public route works
    resp1 = client.get("/public")
    assert_status(resp1, 200)
    print(f"  Public route: {resp1.status_code}")

    # Admin without auth fails
    resp2 = client.get("/admin/dashboard")
    assert_status(resp2, 401)
    print(f"  Admin without auth: {resp2.status_code}")

    # Admin with auth works
    resp3 = client.get("/admin/dashboard", headers={"Authorization": "Bearer secret"})
    assert_status(resp3, 200)
    assert_json_contains(resp3, "page", "admin dashboard")
    print(f"  Admin with auth: {resp3.status_code}")

    # Middleware logged all requests
    print(f"  Middleware log: {middleware_log}")
    assert len(middleware_log) == 3

    print("  [PASS] Testing middleware works")


def demo_testing_error_handling():
    """Show testing error handling."""
    print("\n--- Section 5: Testing Error Handling ---")

    app = IgniteApp()

    @app.get("/items/1")
    def get_item(request: Request) -> dict:
        return {"id": 1, "name": "Widget"}

    @app.post("/items")
    def create_item(request: Request) -> Response:
        body = request.body or {}
        if "name" not in body:
            raise HTTPException(422, "name is required")
        return Response(status_code=201, body={"id": 99, "name": body["name"]})

    @app.delete("/items/1")
    def delete_item(request: Request) -> Response:
        return Response(status_code=204, body={})

    client = TestClient(app)

    # Happy path
    resp1 = client.get("/items/1")
    assert_status(resp1, 200)
    assert_json_contains(resp1, "name", "Widget")
    print("  GET /items/1: 200 OK")

    # Validation error
    resp2 = client.post("/items", json_body={})
    assert_error(resp2, 422, "name is required")
    print("  POST /items (no name): 422")

    # Successful creation
    resp3 = client.post("/items", json_body={"name": "Gadget"})
    assert_status(resp3, 201)
    assert_json_contains(resp3, "name", "Gadget")
    print("  POST /items (with name): 201")

    # Delete
    resp4 = client.delete("/items/1")
    assert_status(resp4, 204)
    print("  DELETE /items/1: 204")

    # Not found
    resp5 = client.get("/items/999")
    assert_status(resp5, 404)
    print("  GET /items/999: 404")

    print("  [PASS] Error handling tests work")


def demo_full_test_suite():
    """Show a complete test suite pattern."""
    print("\n--- Section 6: Full Test Suite Pattern ---")

    # -- Setup: Build the app --

    app = IgniteApp()
    todos: list[dict] = []

    class TodoRepository:
        def list_all(self):
            return todos

        def add(self, title: str):
            todo = {"id": len(todos) + 1, "title": title, "done": False}
            todos.append(todo)
            return todo

    app.dependency("todo_repo", TodoRepository)

    @app.get("/todos")
    def list_todos(request: Request) -> dict:
        repo = app.resolve_dependency("todo_repo")
        return {"todos": repo.list_all()}

    @app.post("/todos")
    def create_todo(request: Request) -> Response:
        repo = app.resolve_dependency("todo_repo")
        body = request.body or {}
        if "title" not in body:
            raise HTTPException(422, "title is required")
        todo = repo.add(body["title"])
        return Response(status_code=201, body=todo)

    # -- Tests: Using TestClient and overrides --

    class FakeTodoRepo:
        def __init__(self):
            self.items = [{"id": 1, "title": "Test Todo", "done": False}]

        def list_all(self):
            return self.items

        def add(self, title: str):
            item = {"id": len(self.items) + 1, "title": title, "done": False}
            self.items.append(item)
            return item

    # Test with fake repo
    fake_repo = FakeTodoRepo()
    with DependencyOverrideContext(app, {"todo_repo": lambda: fake_repo}):
        client = TestClient(app)

        # Test list
        resp = client.get("/todos")
        assert_status(resp, 200)
        assert len(resp.json["todos"]) == 1
        print(f"  List todos: {len(resp.json['todos'])} items")

        # Test create
        resp2 = client.post("/todos", json_body={"title": "New Task"})
        assert_status(resp2, 201)
        assert_json_contains(resp2, "title", "New Task")
        print(f"  Create todo: {resp2.json}")

        # Test list after create
        resp3 = client.get("/todos")
        assert len(resp3.json["todos"]) == 2
        print(f"  After create: {len(resp3.json['todos'])} items")

        # Test validation
        resp4 = client.post("/todos", json_body={})
        assert_error(resp4, 422, "title is required")
        print(f"  Missing title: {resp4.status_code}")

    print("  [PASS] Full test suite pattern works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_test_client()
    demo_dependency_overrides()
    demo_test_helpers()
    demo_testing_middleware()
    demo_testing_error_handling()
    demo_full_test_suite()

    print("\n--- Summary ---")
    print("Testing utilities give our Ignite framework:")
    print("  - TestClient for sending simulated requests")
    print("  - GET, POST, PUT, DELETE convenience methods")
    print("  - Dependency override context manager for mocking")
    print("  - assert_status, assert_json_contains, assert_error helpers")
    print("  - Middleware testing patterns")
    print("  - Full test suite patterns with setup and teardown")
    print("\nAll 6 sections passed. Testing utilities mastered!")
    print("Next up: Kata 77 -- Todo API capstone!")


if __name__ == "__main__":
    main()
