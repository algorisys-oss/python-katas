# Kata 76 -- Testing Utilities

[prev: 75-background-tasks](./75-background-tasks.md) | [next: 77-todo-api](./77-todo-api.md)

---

## What We're Building

**Testing utilities** for our Ignite framework. Real frameworks like FastAPI and Django provide tools that let you test your app without starting a server. We build:

1. **TestClient** -- sends simulated HTTP requests to your app (GET, POST, PUT, DELETE)
2. **Dependency overrides** -- replace real dependencies (database, APIs) with fakes in tests
3. **Test helpers** -- `assert_status`, `assert_json_contains`, `assert_error` for clean test code
4. **Middleware testing** -- verify middleware behavior (auth, logging) through the TestClient

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| TestClient | Sends simulated requests without a server | All endpoint tests |
| Dependency override | Replaces real deps with fakes | Isolating tests from external systems |
| Context manager | Temporarily applies overrides, restores on exit | Clean test setup/teardown |
| Test helpers | Assertion functions with clear error messages | Readable test code |
| Fixture pattern | Setup fake data before tests | Consistent test state |

## The Code

### 1. TestClient

```python
class TestClient:
    def __init__(self, app):
        self.app = app

    def _request(self, method, path, *, headers=None, json_body=None):
        request = Request(method=method, path=path, headers=headers or {},
                         body=json_body)
        return self.app.handle_request(request)

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)
```

### 2. Dependency Overrides

```python
class DependencyOverrideContext:
    def __enter__(self):
        for name, factory in self.overrides.items():
            self.app._dependency_overrides[name] = factory
        return self

    def __exit__(self, *args):
        for name in self.overrides:
            self.app._dependency_overrides.pop(name, None)

# Usage:
with DependencyOverrideContext(app, {"db": lambda: FakeDB()}):
    client = TestClient(app)
    response = client.get("/users")  # Uses FakeDB
```

### 3. Test Helpers

```python
def assert_status(response, expected):
    assert response.status_code == expected

def assert_json_contains(response, key, value=...):
    assert key in response.json
    if value is not ...:
        assert response.json[key] == value

def assert_error(response, status_code, detail_contains=""):
    assert_status(response, status_code)
    assert "error" in response.json
```

## Playground

```python
python playground/76_testing_utilities.py
```

Expected output:

```
--- Section 1: TestClient ---
  GET /users -> 200
  GET /users/1 -> 200: Alice
  POST /users -> 201: {'id': 3, 'name': 'Charlie'}
  GET /nonexistent -> 404
  [PASS] TestClient works

--- Section 2: Dependency Overrides ---
  Real DB: {'users': [{'id': 1, 'name': 'Alice'}]}
  Fake DB: {'users': [{'id': 99, 'name': 'TestUser'}]}
  Back to real: {'users': [{'id': 1, 'name': 'Alice'}]}
  [PASS] Dependency overrides work

--- Section 3: Test Helpers ---
  assert_status(200): passed
  assert_json_contains: passed
  assert_error(403, 'Access denied'): passed
  [PASS] Test helpers work

--- Section 4-6: Middleware, Error Handling, Full Suite ---
  [PASS] All sections pass
```

## How It Works

### TestClient Flow

```
Test Code                    TestClient                    IgniteApp
    |                            |                            |
    | client.get("/users")       |                            |
    |--------------------------->|                            |
    |                            | Request("GET", "/users")   |
    |                            |--------------------------->|
    |                            |                            | Route lookup
    |                            |                            | Middleware
    |                            |                            | Handler
    |                            |     Response(200, {...})    |
    |                            |<---------------------------|
    |     Response(200, {...})   |                            |
    |<---------------------------|                            |
    |                            |                            |
    | assert resp.status == 200  |                            |
```

### Dependency Override Pattern

```
Production:
  app.resolve("db") -> RealDatabase -> PostgreSQL

Testing:
  with DependencyOverrideContext(app, {"db": FakeDB}):
    app.resolve("db") -> FakeDB -> in-memory list

  # After context exits:
  app.resolve("db") -> RealDatabase -> PostgreSQL
```

## Exercises

1. **Add response history** -- make TestClient record all requests/responses for debugging: `client.history` returns a list of `(request, response)` tuples.

2. **Add cookie support** -- make TestClient maintain cookies across requests, like a real browser session.

3. **Add `assert_json_schema`** -- validate that the response JSON matches an expected structure (keys and types) without checking specific values.

4. **Add test fixtures** -- create a `@fixture` decorator that sets up test data before each test and tears it down after.

5. **Add snapshot testing** -- record the first response as a "snapshot" and assert future responses match it.

## What's Next

With testing utilities in place, we have everything we need to build and verify complete applications. In [Kata 77: Todo API](./77-todo-api.md), our first capstone project, we'll bring together all the Ignite features to build a full CRUD REST API.

---

[prev: 75-background-tasks](./75-background-tasks.md) | [next: 77-todo-api](./77-todo-api.md)
