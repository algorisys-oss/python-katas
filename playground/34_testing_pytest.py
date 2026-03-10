"""
Kata 34 -- Testing with pytest
Run: python playground/34_testing_pytest.py

Build a mini test framework that demonstrates pytest's core concepts:
assertions, fixtures, parametrize, markers, mocking, and pytest.raises.

Since the playground runs code via subprocess -c, we can't invoke pytest
directly. Instead, we simulate the same patterns with a lightweight runner.
All demos complete within 5 seconds.
"""

import inspect
import traceback
from unittest.mock import Mock, patch, MagicMock


# ===========================================================================
# SECTION 1: Mini Test Framework Core
# ===========================================================================

class TestResult:
    """Stores the outcome of a single test run."""

    def __init__(self, name: str, status: str, message: str = ""):
        self.name = name
        self.status = status  # PASSED, FAILED, ERROR, SKIPPED, XFAIL
        self.message = message

    def __repr__(self):
        icons = {"PASSED": ".", "FAILED": "F", "ERROR": "E",
                 "SKIPPED": "s", "XFAIL": "x"}
        return icons.get(self.status, "?")


class TestRunner:
    """Minimal test runner with fixture injection, parametrize, and markers."""

    def __init__(self):
        self._fixtures: dict[str, callable] = {}
        self._results: list[TestResult] = []

    # -- Fixture system (like @pytest.fixture) --

    def fixture(self, func):
        """Register a fixture function. Its return value is injected by name."""
        self._fixtures[func.__name__] = func
        return func

    def _resolve_fixtures(self, test_func) -> dict:
        """Inspect the test's signature and resolve fixture dependencies."""
        sig = inspect.signature(test_func)
        kwargs = {}
        for param_name in sig.parameters:
            if param_name in self._fixtures:
                result = self._fixtures[param_name]()
                # Support generator fixtures (yield = setup + teardown)
                if inspect.isgenerator(result):
                    value = next(result)
                    kwargs[param_name] = value
                    # Store generator for teardown later
                    kwargs.setdefault("_generators", []).append(result)
                else:
                    kwargs[param_name] = result
        return kwargs

    # -- Run a single test --

    def _run_one(self, name: str, func, extra_kwargs: dict | None = None):
        """Execute a single test function and record the result."""
        # Check skip marker
        if hasattr(func, "_skip"):
            self._results.append(TestResult(name, "SKIPPED", func._skip))
            return

        try:
            kwargs = self._resolve_fixtures(func)
            generators = kwargs.pop("_generators", [])
            if extra_kwargs:
                kwargs.update(extra_kwargs)
            func(**kwargs)

            # Teardown generator fixtures
            for gen in generators:
                try:
                    next(gen)
                except StopIteration:
                    pass

            # Check xfail -- test passed but was expected to fail
            if hasattr(func, "_xfail"):
                self._results.append(TestResult(name, "XFAIL", func._xfail))
            else:
                self._results.append(TestResult(name, "PASSED"))

        except AssertionError as e:
            if hasattr(func, "_xfail"):
                self._results.append(TestResult(name, "XFAIL", func._xfail))
            else:
                self._results.append(TestResult(name, "FAILED", str(e)))

        except Exception as e:
            self._results.append(TestResult(name, "ERROR", str(e)))

    # -- Run a list of test functions --

    def run(self, tests: list[callable], group_name: str = ""):
        """Run a group of test functions, expanding parametrize."""
        if group_name:
            print(f"\n--- {group_name} ---")

        for test_func in tests:
            if hasattr(test_func, "_parametrize"):
                # Expand parametrized tests
                names_list, values_list = test_func._parametrize[0]
                for values in values_list:
                    if not isinstance(values, (list, tuple)):
                        values = (values,)
                    label = ", ".join(str(v) for v in values)
                    test_name = f"{test_func.__name__}[{label}]"
                    extra = dict(zip(names_list, values))
                    self._run_one(test_name, test_func, extra)
                    print(f"  {test_name}: {self._results[-1].status}")
            else:
                self._run_one(test_func.__name__, test_func)
                r = self._results[-1]
                msg = f" ({r.message})" if r.message else ""
                print(f"  {test_func.__name__}: {r.status}{msg}")

    # -- Summary report --

    def summary(self):
        """Print a pytest-style summary."""
        counts = {}
        for r in self._results:
            counts[r.status] = counts.get(r.status, 0) + 1

        parts = []
        for status in ["PASSED", "FAILED", "ERROR", "SKIPPED", "XFAIL"]:
            if status in counts:
                label = status.lower()
                if status == "PASSED":
                    label = "passed"
                elif status == "FAILED":
                    label = "failed"
                elif status == "SKIPPED":
                    label = "skipped"
                parts.append(f"{counts[status]} {label}")

        print(f"\n==================")
        print(", ".join(parts))
        return counts.get("FAILED", 0) + counts.get("ERROR", 0)


# ===========================================================================
# SECTION 2: Markers (skip, xfail)
# ===========================================================================

def skip(reason: str = ""):
    """Mark a test to be skipped (like @pytest.mark.skip)."""
    def decorator(func):
        func._skip = reason or "skipped"
        return func
    return decorator


def xfail(reason: str = ""):
    """Mark a test as expected to fail (like @pytest.mark.xfail)."""
    def decorator(func):
        func._xfail = reason or "expected failure"
        return func
    return decorator


# ===========================================================================
# SECTION 3: Parametrize
# ===========================================================================

def parametrize(argnames: str, argvalues: list):
    """Run a test with multiple parameter sets (like @pytest.mark.parametrize)."""
    names = [n.strip() for n in argnames.split(",")]
    def decorator(func):
        func._parametrize = [(names, argvalues)]
        return func
    return decorator


# ===========================================================================
# SECTION 4: pytest.raises equivalent
# ===========================================================================

class raises:
    """Context manager asserting that an exception is raised.

    Usage:
        with raises(ValueError, match="invalid"):
            int("not_a_number")
    """

    def __init__(self, expected_exc, match: str | None = None):
        self.expected = expected_exc
        self.match = match
        self.exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        if exc_type is None:
            raise AssertionError(f"{self.expected.__name__} not raised")
        if not issubclass(exc_type, self.expected):
            return False  # re-raise unexpected exception
        if self.match and self.match not in str(exc_val):
            raise AssertionError(
                f"Pattern '{self.match}' not found in '{exc_val}'")
        self.exception = exc_val
        return True  # suppress the expected exception


# ===========================================================================
# SECTION 5: Monkeypatch
# ===========================================================================

class Monkeypatch:
    """Temporarily modify attributes, dict items, and env vars.

    Like pytest's monkeypatch fixture, but as a context manager.
    """

    def __init__(self):
        self._undo: list[callable] = []

    def setattr(self, obj, name: str, value):
        """Replace obj.name with value; restore on undo()."""
        old = getattr(obj, name)
        setattr(obj, name, value)
        self._undo.append(lambda: setattr(obj, name, old))

    def setitem(self, mapping, key, value):
        """Replace mapping[key] with value; restore on undo()."""
        sentinel = object()
        old = mapping.get(key, sentinel)
        mapping[key] = value
        if old is sentinel:
            self._undo.append(lambda: mapping.pop(key, None))
        else:
            self._undo.append(lambda: mapping.__setitem__(key, old))

    def delattr(self, obj, name: str):
        """Remove obj.name; restore on undo()."""
        old = getattr(obj, name)
        delattr(obj, name)
        self._undo.append(lambda: setattr(obj, name, old))

    def undo(self):
        """Restore all modifications in reverse order."""
        for restore in reversed(self._undo):
            restore()
        self._undo.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.undo()
        return False


# ===========================================================================
# DEMO: Run the full test suite
# ===========================================================================

if __name__ == "__main__":
    print("=== Mini Test Framework (pytest concepts) ===")

    runner = TestRunner()

    # -- Register fixtures --

    @runner.fixture
    def sample_list():
        """Fixture providing a fresh list for each test."""
        return [1, 2, 3, 4, 5]

    @runner.fixture
    def db():
        """Fixture simulating a database connection."""
        data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        return data

    # -- Fixture tests --

    def test_with_fixture(sample_list):
        assert len(sample_list) == 5
        sample_list.append(6)
        assert len(sample_list) == 6

    def test_with_db_fixture(db):
        assert len(db["users"]) == 2
        assert db["users"][0]["name"] == "Alice"

    runner.run([test_with_fixture, test_with_db_fixture], "Fixtures")

    # -- Assertion tests (pytest rewrites assert for rich messages) --

    def test_string_methods():
        s = "hello world"
        assert s.upper() == "HELLO WORLD"
        assert s.split() == ["hello", "world"]
        assert s.startswith("hello")
        assert "world" in s

    def test_list_operations():
        nums = [3, 1, 4, 1, 5]
        assert sorted(nums) == [1, 1, 3, 4, 5]
        assert max(nums) == 5
        assert nums.count(1) == 2

    def test_dict_access():
        d = {"a": 1, "b": 2}
        assert d["a"] == 1
        assert d.get("c", 0) == 0
        assert set(d.keys()) == {"a", "b"}

    runner.run([test_string_methods, test_list_operations, test_dict_access],
               "Assertions")

    # -- Parametrize tests --

    @parametrize("x, expected", [(2, 4), (3, 9), (-1, 1), (0, 0)])
    def test_square(x, expected):
        assert x ** 2 == expected

    runner.run([test_square], "Parametrize")

    # -- Marker tests --

    @skip(reason="not implemented yet")
    def test_not_ready():
        assert False, "should never reach here"

    @xfail(reason="known bug")
    def test_known_bug():
        result = 1 / 1  # "bug" that actually works -- xfail records it
        assert result == 1

    runner.run([test_not_ready, test_known_bug], "Markers")

    # -- Mocking tests --

    def test_mock_basics():
        """Demonstrate unittest.mock.Mock and patch."""
        # Mock creates a fake object that records calls
        api_client = Mock()
        api_client.get.return_value = {"status": 200, "data": [1, 2, 3]}

        response = api_client.get("/users")
        assert response["status"] == 200
        assert len(response["data"]) == 3
        api_client.get.assert_called_once_with("/users")

        # MagicMock supports magic methods
        magic = MagicMock()
        magic.__len__.return_value = 42
        assert len(magic) == 42

    def test_monkeypatch():
        """Demonstrate monkeypatch for temporary modifications."""
        import os

        class Config:
            debug = False
            db_url = "postgres://prod"

        with Monkeypatch() as mp:
            mp.setattr(Config, "debug", True)
            mp.setattr(Config, "db_url", "sqlite://test")
            assert Config.debug is True
            assert Config.db_url == "sqlite://test"

        # After context manager exits, values are restored
        assert Config.debug is False
        assert Config.db_url == "postgres://prod"

    runner.run([test_mock_basics, test_monkeypatch], "Mocking")

    # -- pytest.raises tests --

    def test_raises_value_error():
        with raises(ValueError):
            int("not_a_number")

    def test_raises_with_match():
        with raises(ZeroDivisionError, match="division by zero"):
            1 / 0

    runner.run([test_raises_value_error, test_raises_with_match], "pytest.raises")

    # -- Summary --
    failures = runner.summary()

    # Verify the framework itself works correctly
    assert failures == 0, f"Expected 0 failures, got {failures}"
    print("\nAll pytest concepts demonstrated successfully!")
