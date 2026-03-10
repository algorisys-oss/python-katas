"""
Kata 76 -- Testing Utilities
Run: python playground/skeletons/76_testing_utilities.py

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

    def route(self, path: str, method: str = "GET"):
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

    def dependency(self, name: str, factory: Callable) -> None:
        self._dependencies[name] = factory

    def resolve_dependency(self, name: str) -> Any:
        """Resolve a dependency, using override if set."""
        # TODO: Check self._dependency_overrides first, then self._dependencies
        # If name is in overrides, call overrides[name]() and return
        # If name is in dependencies, call dependencies[name]() and return
        # Otherwise raise KeyError
        pass

    def add_middleware(self, middleware: Callable) -> None:
        self._middleware.append(middleware)

    def handle_request(self, request: Request) -> Response:
        """Process a request through the middleware and route handler."""
        try:
            key = (request.method.upper(), request.path)
            handler = self._routes.get(key)
            if handler is None:
                raise HTTPException(404, f"Not Found: {request.path}")

            for mw in self._middleware:
                result = mw(request)
                if isinstance(result, Response):
                    return result

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

class TestClient:
    """Test client for Ignite apps.

    Sends simulated HTTP requests without starting a server.
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
        # TODO: Create a Request object and pass it to self.app.handle_request
        pass

    def get(self, path: str, **kwargs) -> Response:
        """Send a GET request."""
        # TODO: Call self._request("GET", path, **kwargs)
        pass

    def post(self, path: str, **kwargs) -> Response:
        """Send a POST request."""
        # TODO: Call self._request("POST", path, **kwargs)
        pass

    def put(self, path: str, **kwargs) -> Response:
        """Send a PUT request."""
        # TODO: Call self._request("PUT", path, **kwargs)
        pass

    def delete(self, path: str, **kwargs) -> Response:
        """Send a DELETE request."""
        # TODO: Call self._request("DELETE", path, **kwargs)
        pass

    def patch(self, path: str, **kwargs) -> Response:
        """Send a PATCH request."""
        return self._request("PATCH", path, **kwargs)


# ===========================================================================
# SECTION 4: Dependency Overrides
# ===========================================================================

class DependencyOverrideContext:
    """Context manager for temporarily overriding dependencies.

    Usage:
        with DependencyOverrideContext(app, {"db": lambda: FakeDB()}):
            response = client.get("/users")
    """

    def __init__(self, app: IgniteApp, overrides: dict[str, Callable]):
        self.app = app
        self.overrides = overrides
        self._saved: dict[str, Callable] = {}

    def __enter__(self):
        # TODO: Save existing overrides, then apply new ones
        # For each name in self.overrides:
        #   If name already in app._dependency_overrides, save it
        #   Set app._dependency_overrides[name] = new factory
        pass

    def __exit__(self, *args):
        # TODO: Restore original state
        # For each name in self.overrides:
        #   If saved, restore it
        #   Otherwise, remove it from overrides
        pass


# ===========================================================================
# SECTION 5: Test Helpers
# ===========================================================================

def assert_status(response: Response, expected: int, msg: str = "") -> None:
    """Assert response has the expected status code."""
    assert response.status_code == expected, (
        f"Expected status {expected}, got {response.status_code}"
        f"{': ' + msg if msg else ''}"
    )


def assert_json_contains(response: Response, key: str, value: Any = ...) -> None:
    """Assert response JSON contains a key (optionally with a specific value)."""
    # TODO: Assert key is in response.json
    # If value is not ... (sentinel), also assert response.json[key] == value
    pass


def assert_error(response: Response, status_code: int, detail_contains: str = "") -> None:
    """Assert response is an error with expected status and detail."""
    # TODO: Assert status code matches
    # Assert "error" key is in response.json
    # If detail_contains is not empty, assert it's in the error detail
    pass


# ===========================================================================
# SECTION 6: Demos
# ===========================================================================

def demo_test_client():
    """Show TestClient usage."""
    print("--- Section 1: TestClient ---")

    try:
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

        resp = client.get("/users")
        print(f"  GET /users -> {resp.status_code}")
        assert resp.status_code == 200
        assert len(resp.json["users"]) == 2

        resp2 = client.get("/users/1")
        print(f"  GET /users/1 -> {resp2.status_code}: {resp2.json['name']}")
        assert resp2.json["name"] == "Alice"

        resp3 = client.post("/users", json_body={"name": "Charlie"})
        print(f"  POST /users -> {resp3.status_code}: {resp3.json}")
        assert resp3.status_code == 201
        assert resp3.json["name"] == "Charlie"

        resp4 = client.get("/nonexistent")
        print(f"  GET /nonexistent -> {resp4.status_code}")
        assert resp4.status_code == 404

        print("  [PASS] TestClient works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_dependency_overrides():
    """Show dependency override mechanism."""
    print("\n--- Section 2: Dependency Overrides ---")

    try:
        app = IgniteApp()

        class RealDatabase:
            def get_users(self):
                return [{"id": 1, "name": "Alice"}]

        app.dependency("db", RealDatabase)

        @app.get("/users")
        def list_users(request: Request) -> dict:
            db = app.resolve_dependency("db")
            return {"users": db.get_users()}

        client = TestClient(app)

        resp1 = client.get("/users")
        print(f"  Real DB: {resp1.json}")
        assert resp1.json["users"][0]["name"] == "Alice"

        class FakeDatabase:
            def get_users(self):
                return [{"id": 99, "name": "TestUser"}]

        with DependencyOverrideContext(app, {"db": FakeDatabase}):
            resp2 = client.get("/users")
            print(f"  Fake DB: {resp2.json}")
            assert resp2.json["users"][0]["name"] == "TestUser"

        resp3 = client.get("/users")
        print(f"  Back to real: {resp3.json}")
        assert resp3.json["users"][0]["name"] == "Alice"

        print("  [PASS] Dependency overrides work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_test_helpers():
    """Show test helper functions."""
    print("\n--- Section 3: Test Helpers ---")

    try:
        app = IgniteApp()

        @app.get("/ok")
        def ok_handler(request: Request) -> dict:
            return {"message": "hello", "count": 42}

        @app.get("/fail")
        def fail_handler(request: Request):
            raise HTTPException(403, "Access denied")

        client = TestClient(app)

        resp = client.get("/ok")
        assert_status(resp, 200)
        print("  assert_status(200): passed")

        assert_json_contains(resp, "message", "hello")
        assert_json_contains(resp, "count", 42)
        assert_json_contains(resp, "message")
        print("  assert_json_contains: passed")

        resp2 = client.get("/fail")
        assert_error(resp2, 403, "Access denied")
        print("  assert_error(403, 'Access denied'): passed")

        print("  [PASS] Test helpers work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_testing_middleware():
    """Show testing apps with middleware."""
    print("\n--- Section 4: Testing Middleware ---")

    try:
        app = IgniteApp()
        middleware_log = []

        def logging_middleware(request: Request):
            middleware_log.append(f"{request.method} {request.path}")
            return None

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

        resp1 = client.get("/public")
        assert_status(resp1, 200)
        print(f"  Public route: {resp1.status_code}")

        resp2 = client.get("/admin/dashboard")
        assert_status(resp2, 401)
        print(f"  Admin without auth: {resp2.status_code}")

        resp3 = client.get("/admin/dashboard", headers={"Authorization": "Bearer secret"})
        assert_status(resp3, 200)
        assert_json_contains(resp3, "page", "admin dashboard")
        print(f"  Admin with auth: {resp3.status_code}")

        print(f"  Middleware log: {middleware_log}")
        assert len(middleware_log) == 3

        print("  [PASS] Testing middleware works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_testing_error_handling():
    """Show testing error handling."""
    print("\n--- Section 5: Testing Error Handling ---")

    try:
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

        resp1 = client.get("/items/1")
        assert_status(resp1, 200)
        assert_json_contains(resp1, "name", "Widget")
        print("  GET /items/1: 200 OK")

        resp2 = client.post("/items", json_body={})
        assert_error(resp2, 422, "name is required")
        print("  POST /items (no name): 422")

        resp3 = client.post("/items", json_body={"name": "Gadget"})
        assert_status(resp3, 201)
        assert_json_contains(resp3, "name", "Gadget")
        print("  POST /items (with name): 201")

        resp4 = client.delete("/items/1")
        assert_status(resp4, 204)
        print("  DELETE /items/1: 204")

        resp5 = client.get("/items/999")
        assert_status(resp5, 404)
        print("  GET /items/999: 404")

        print("  [PASS] Error handling tests work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_full_test_suite():
    """Show a complete test suite pattern."""
    print("\n--- Section 6: Full Test Suite Pattern ---")

    try:
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

        class FakeTodoRepo:
            def __init__(self):
                self.items = [{"id": 1, "title": "Test Todo", "done": False}]

            def list_all(self):
                return self.items

            def add(self, title: str):
                item = {"id": len(self.items) + 1, "title": title, "done": False}
                self.items.append(item)
                return item

        fake_repo = FakeTodoRepo()
        with DependencyOverrideContext(app, {"todo_repo": lambda: fake_repo}):
            client = TestClient(app)

            resp = client.get("/todos")
            assert_status(resp, 200)
            assert len(resp.json["todos"]) == 1
            print(f"  List todos: {len(resp.json['todos'])} items")

            resp2 = client.post("/todos", json_body={"title": "New Task"})
            assert_status(resp2, 201)
            assert_json_contains(resp2, "title", "New Task")
            print(f"  Create todo: {resp2.json}")

            resp3 = client.get("/todos")
            assert len(resp3.json["todos"]) == 2
            print(f"  After create: {len(resp3.json['todos'])} items")

            resp4 = client.post("/todos", json_body={})
            assert_error(resp4, 422, "title is required")
            print(f"  Missing title: {resp4.status_code}")

        print("  [PASS] Full test suite pattern works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


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
    print("\nAll 6 sections attempted. Testing utilities skeleton ready!")
    print("Next up: Kata 77 -- Todo API capstone!")


if __name__ == "__main__":
    main()
