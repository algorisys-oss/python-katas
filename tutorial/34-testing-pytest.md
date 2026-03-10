# Kata 34 -- Testing with pytest

[prev: 33-logging-debugging](./33-logging-debugging.md) | [next: 35-packaging](./35-packaging.md)

---

## What We're Building

A **mini test framework** that mirrors pytest's key features -- assertions, fixtures, parametrize, markers, mocking, and test organization. Since our playground runs code via `subprocess -c`, we can't invoke pytest directly. Instead, we build a lightweight test runner that demonstrates the same concepts, and show real pytest code examples throughout.

We'll build five components:
1. **Test discovery & runner** -- find and run test functions by naming convention
2. **Fixture system** -- setup/teardown with dependency injection via function signatures
3. **Parametrize decorator** -- run the same test with multiple inputs
4. **Markers** -- tag tests to skip, expect failure, or filter by category
5. **Mock & monkeypatch** -- replace objects and attributes for isolated testing

By the end, you'll understand every major pytest concept and be ready to use it in real projects.

## Concepts You'll Learn

| Concept | pytest Equivalent | What It Does |
|---|---|---|
| Test discovery | `pytest` CLI | Finds functions named `test_*` automatically |
| Assertions | `assert` with rewriting | Rich failure messages from plain `assert` |
| Fixtures | `@pytest.fixture` | Setup/teardown with dependency injection |
| Parametrize | `@pytest.mark.parametrize` | Run one test with many inputs |
| Markers | `@pytest.mark.skip`, `xfail` | Skip tests, expect failures, tag tests |
| Mocking | `unittest.mock.patch` | Replace objects with fakes for isolation |
| Monkeypatch | `monkeypatch` fixture | Temporarily modify attributes, env vars, dicts |
| conftest.py | `conftest.py` | Share fixtures across test modules |
| `pytest.raises` | `pytest.raises(Exception)` | Assert that code raises a specific exception |
| Test organization | `test_*/Test*` | Group tests by module, class, function |

## The Code

### Part 1: Test Discovery and Running

pytest finds tests by convention: files named `test_*.py`, functions named `test_*`, classes named `Test*`. Our mini runner does the same using `inspect`.

```python
import inspect
import functools
import traceback

class TestResult:
    """Stores the outcome of a single test."""
    def __init__(self, name, status, message=""):
        self.name = name
        self.status = status  # "PASSED", "FAILED", "ERROR", "SKIPPED", "XFAIL"
        self.message = message

    def __repr__(self):
        mark = {"PASSED": ".", "FAILED": "F", "ERROR": "E",
                "SKIPPED": "s", "XFAIL": "x"}
        return mark.get(self.status, "?")
```

The runner collects test functions, inspects their signatures for fixtures, and invokes them.

### Part 2: Fixtures -- Setup with Dependency Injection

In pytest, fixtures are functions decorated with `@pytest.fixture`. When a test function declares a parameter with the same name, pytest injects the fixture's return value automatically. This is **dependency injection** via `inspect.signature()`.

```python
# Real pytest usage:
# @pytest.fixture
# def db_connection():
#     conn = sqlite3.connect(":memory:")
#     yield conn        # yield = setup + teardown
#     conn.close()
#
# def test_insert(db_connection):   # <-- injected automatically
#     db_connection.execute("CREATE TABLE t (id INTEGER)")

# Our mini version uses the same inspect-based injection:
_fixtures = {}

def fixture(func):
    """Register a fixture function."""
    _fixtures[func.__name__] = func
    return func

def _resolve_fixtures(test_func):
    """Inspect test signature and resolve fixture values."""
    sig = inspect.signature(test_func)
    kwargs = {}
    for param_name in sig.parameters:
        if param_name in _fixtures:
            kwargs[param_name] = _fixtures[param_name]()
    return kwargs
```

### Part 3: Parametrize -- One Test, Many Inputs

`@pytest.mark.parametrize` runs a test function multiple times with different arguments. It's the cleanest way to test edge cases without writing repetitive test functions.

```python
# Real pytest:
# @pytest.mark.parametrize("input,expected", [
#     ("hello", 5),
#     ("", 0),
#     ("pytest", 6),
# ])
# def test_length(input, expected):
#     assert len(input) == expected

# Our version attaches params as metadata:
def parametrize(argnames, argvalues):
    """Decorator to run a test with multiple parameter sets."""
    names = [n.strip() for n in argnames.split(",")]
    def decorator(func):
        func._parametrize = [(names, argvalues)]
        return func
    return decorator
```

### Part 4: Markers -- Skip, Xfail, and Custom Tags

Markers let you control which tests run and how failures are interpreted.

```python
# Real pytest:
# @pytest.mark.skip(reason="not implemented yet")
# @pytest.mark.xfail(reason="known bug #42")
# @pytest.mark.slow  # custom marker, filter with: pytest -m "not slow"

def skip(reason=""):
    """Mark a test to be skipped."""
    def decorator(func):
        func._skip = reason or "skipped"
        return func
    return decorator

def xfail(reason=""):
    """Mark a test as expected to fail."""
    def decorator(func):
        func._xfail = reason or "expected failure"
        return func
    return decorator
```

### Part 5: Mocking and Monkeypatch

`unittest.mock` is Python's built-in mocking library. pytest's `monkeypatch` fixture provides a simpler API for temporarily replacing attributes.

```python
from unittest.mock import Mock, patch, MagicMock

# Mock: create a fake object
mock_db = Mock()
mock_db.query.return_value = [{"id": 1, "name": "Alice"}]

# patch: temporarily replace an attribute
# with patch("module.function") as mock_func:
#     mock_func.return_value = 42
#     result = module.function()  # returns 42

# monkeypatch: pytest's simpler alternative
# def test_env(monkeypatch):
#     monkeypatch.setenv("API_KEY", "test-key")
#     monkeypatch.setattr(requests, "get", lambda url: FakeResponse())
```

Our mini framework includes a `Monkeypatch` context manager:

```python
class Monkeypatch:
    """Temporarily modify attributes, dict items, and env vars."""
    def __init__(self):
        self._undo = []

    def setattr(self, obj, name, value):
        old = getattr(obj, name)
        setattr(obj, name, value)
        self._undo.append(lambda: setattr(obj, name, old))

    def undo(self):
        for restore in reversed(self._undo):
            restore()
```

### Part 6: pytest.raises -- Asserting Exceptions

```python
# Real pytest:
# with pytest.raises(ValueError, match="invalid"):
#     int("not_a_number")

# Our version:
class raises:
    """Context manager to assert an exception is raised."""
    def __init__(self, expected_exc, match=None):
        self.expected = expected_exc
        self.match = match

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        if exc_type is None:
            raise AssertionError(f"{self.expected.__name__} not raised")
        if not issubclass(exc_type, self.expected):
            return False  # re-raise unexpected exception
        if self.match and self.match not in str(exc_val):
            raise AssertionError(
                f"Pattern '{self.match}' not in '{exc_val}'")
        return True  # suppress the expected exception
```

### Part 7: conftest.py and Test Organization

In real pytest projects, `conftest.py` files share fixtures across test modules without importing them:

```
tests/
    conftest.py          # fixtures available to ALL tests below
    test_models.py
    test_views.py
    integration/
        conftest.py      # fixtures for integration tests only
        test_api.py
```

**Key conftest.py rules:**
- Fixtures defined in `conftest.py` are auto-discovered (no imports needed)
- Each directory can have its own `conftest.py`
- Fixtures cascade: inner conftest overrides outer conftest
- Plugins and hooks can also be defined in conftest

## Playground

The playground builds a complete mini test framework and runs a suite demonstrating every concept:

```
=== Mini Test Framework (pytest concepts) ===

--- Fixtures ---
  test_with_fixture: PASSED
  test_with_db_fixture: PASSED

--- Assertions ---
  test_string_methods: PASSED
  test_list_operations: PASSED
  test_dict_access: PASSED

--- Parametrize ---
  test_square[2, 4]: PASSED
  test_square[3, 9]: PASSED
  test_square[-1, 1]: PASSED
  test_square[0, 0]: PASSED

--- Markers ---
  test_not_ready: SKIPPED (not implemented yet)
  test_known_bug: XFAIL (known bug)

--- Mocking ---
  test_mock_basics: PASSED
  test_monkeypatch: PASSED

--- pytest.raises ---
  test_raises_value_error: PASSED
  test_raises_with_match: PASSED

==================
15 passed, 1 skipped, 1 xfail
```

## How It Works

```
Test Discovery (by naming convention)
        |
        v
Signature Inspection (inspect.signature)
        |
        v
Fixture Resolution (inject dependencies)
        |
        v
Parametrize Expansion (multiply test cases)
        |
        v
Marker Processing (skip / xfail / filter)
        |
        v
Test Execution + Result Collection
        |
        v
Summary Report (passed/failed/skipped/xfail)
```

**pytest's magic is dependency injection via `inspect.signature()`** -- the same pattern we'll use in Ignite's `Depends()` system (kata 43+).

## Exercises

1. **Add `@fixture(scope="module")`** -- make a fixture that runs once per test group instead of once per test
2. **Add `--filter` support** -- run only tests matching a substring (like `pytest -k`)
3. **Add `capsys` fixture** -- capture stdout/stderr during a test (like pytest's `capsys`)
4. **Add nested parametrize** -- support stacking multiple `@parametrize` decorators (cartesian product)
5. **Add `@fixture` with `yield`** -- implement setup/teardown using generator fixtures

## What's Next

In [Kata 35 -- Packaging](./35-packaging.md), we'll learn how to package Python projects with `pyproject.toml`, build distributable wheels, and publish to PyPI -- the final step before we start building the Ignite framework.

---

[prev: 33-logging-debugging](./33-logging-debugging.md) | [next: 35-packaging](./35-packaging.md)
