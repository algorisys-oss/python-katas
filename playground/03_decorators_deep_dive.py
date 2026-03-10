"""
Kata 03 -- Decorators Deep Dive
Run: python playground/03_decorators_deep_dive.py

Master decorators from simple wrappers to advanced patterns: decorator
factories, stacking, class decorators, caching, and deprecation warnings.
"""

import time
import inspect
import warnings
from functools import wraps
from collections import OrderedDict


# ---------------------------------------------------------------------------
# Section 1: A simple @timer decorator
# ---------------------------------------------------------------------------

def timer(func):
    """Measure and print the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[timer] {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


# ---------------------------------------------------------------------------
# Section 2: Bad decorator (no @wraps) vs good decorator
# ---------------------------------------------------------------------------

def bad_timer(func):
    """A decorator that DOESN'T use @wraps -- metadata is lost."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[bad_timer] {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper


# ---------------------------------------------------------------------------
# Section 3: Decorator factory -- decorators with arguments
# ---------------------------------------------------------------------------

def retry(max_attempts=3, delay=0.01):
    """Retry a function up to max_attempts times on exception."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"[retry] {func.__name__} attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Section 4: @validate_types using type hints
# ---------------------------------------------------------------------------

def validate_types(func):
    """Validate function arguments match their type annotations."""
    sig = inspect.signature(func)
    hints = func.__annotations__

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        for param_name, value in bound.arguments.items():
            if param_name in hints and param_name != "return":
                expected_type = hints[param_name]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Argument '{param_name}' expected {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        return func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Section 5: Stacking decorators
# ---------------------------------------------------------------------------

def bold(func):
    """Wrap the return value in <b> tags."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"<b>{func(*args, **kwargs)}</b>"
    return wrapper


def italic(func):
    """Wrap the return value in <i> tags."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"<i>{func(*args, **kwargs)}</i>"
    return wrapper


# ---------------------------------------------------------------------------
# Section 6: @singleton class decorator
# ---------------------------------------------------------------------------

def singleton(cls):
    """Class decorator that ensures only one instance exists."""
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


# ---------------------------------------------------------------------------
# Section 7: Real-world patterns
# ---------------------------------------------------------------------------

# --- Manual LRU cache ---

def cache(maxsize=128):
    """LRU cache decorator with configurable max size."""
    def decorator(func):
        cache_store = OrderedDict()

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key in cache_store:
                cache_store.move_to_end(key)
                return cache_store[key]
            result = func(*args, **kwargs)
            cache_store[key] = result
            if len(cache_store) > maxsize:
                cache_store.popitem(last=False)
            return result

        wrapper.cache_info = lambda: {
            "size": len(cache_store),
            "maxsize": maxsize,
        }
        wrapper.cache_clear = lambda: cache_store.clear()
        return wrapper
    return decorator


# --- @deprecated warning decorator ---

def deprecated(reason=""):
    """Mark a function as deprecated with an optional reason."""
    def decorator(func):
        message = f"{func.__name__} is deprecated"
        if reason:
            message += f": {reason}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Simple @timer decorator ---
    print("--- Section 1: Simple @timer decorator ---")

    @timer
    def slow_add(a, b):
        """Add two numbers slowly."""
        time.sleep(0.05)
        return a + b

    result = slow_add(2, 3)
    # Output: [timer] slow_add took 0.05XXs
    assert result == 5
    print(f"Result: {result}")
    # Output: Result: 5

    print()

    # --- Section 2: @wraps preserves metadata ---
    print("--- Section 2: @wraps preserves metadata ---")

    @bad_timer
    def add_bad(a, b):
        """Add two numbers."""
        return a + b

    print(f"Without @wraps: __name__ = {add_bad.__name__!r}")
    # Output: Without @wraps: __name__ = 'wrapper'
    assert add_bad.__name__ == "wrapper"

    print(f"Without @wraps: __doc__  = {add_bad.__doc__!r}")
    # Output: Without @wraps: __doc__  = None
    assert add_bad.__doc__ is None

    @timer  # timer uses @wraps
    def add_good(a, b):
        """Add two numbers."""
        return a + b

    print(f"With @wraps:    __name__ = {add_good.__name__!r}")
    # Output: With @wraps:    __name__ = 'add_good'
    assert add_good.__name__ == "add_good"

    print(f"With @wraps:    __doc__  = {add_good.__doc__!r}")
    # Output: With @wraps:    __doc__  = 'Add two numbers.'
    assert add_good.__doc__ == "Add two numbers."

    # __wrapped__ gives access to the original function
    assert hasattr(add_good, "__wrapped__")
    print(f"With @wraps:    __wrapped__ is accessible: {hasattr(add_good, '__wrapped__')}")
    # Output: With @wraps:    __wrapped__ is accessible: True

    print()

    # --- Section 3: Decorator factory (@retry) ---
    print("--- Section 3: Decorator factory (@retry) ---")

    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    def flaky_function():
        """Simulates a function that fails twice then succeeds."""
        global call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"Attempt {call_count} failed")
        return "success"

    result = flaky_function()
    # Output: [retry] flaky_function attempt 1/3 failed: Attempt 1 failed
    # Output: [retry] flaky_function attempt 2/3 failed: Attempt 2 failed
    print(f"Result: {result}")
    # Output: Result: success
    assert result == "success"
    assert call_count == 3

    # Verify metadata preserved
    assert flaky_function.__name__ == "flaky_function"
    print(f"Metadata preserved: __name__ = {flaky_function.__name__!r}")
    # Output: Metadata preserved: __name__ = 'flaky_function'

    # Verify that exhausting retries raises the last exception
    fail_count = 0

    @retry(max_attempts=2, delay=0.01)
    def always_fails():
        global fail_count
        fail_count += 1
        raise ValueError(f"fail #{fail_count}")

    try:
        always_fails()
    except ValueError as e:
        print(f"Exhausted retries, raised: {e}")
        # Output: Exhausted retries, raised: fail #<N>
    assert fail_count >= 2

    print()

    # --- Section 4: @validate_types ---
    print("--- Section 4: @validate_types ---")

    @validate_types
    def greet(name: str, times: int = 1) -> str:
        return f"Hello, {name}! " * times

    result = greet("Alice", 2)
    print(f"greet('Alice', 2) = {result!r}")
    # Output: greet('Alice', 2) = 'Hello, Alice! Hello, Alice! '
    assert result == "Hello, Alice! Hello, Alice! "

    # Valid call with default
    result = greet("Bob")
    print(f"greet('Bob') = {result!r}")
    # Output: greet('Bob') = 'Hello, Bob! '
    assert result == "Hello, Bob! "

    # Invalid type raises TypeError
    try:
        greet(42)
    except TypeError as e:
        print(f"TypeError caught: {e}")
        # Output: TypeError caught: Argument 'name' expected str, got int
    assert greet.__name__ == "greet"

    # Invalid second arg
    try:
        greet("Alice", "many")
    except TypeError as e:
        print(f"TypeError caught: {e}")
        # Output: TypeError caught: Argument 'times' expected int, got str

    print()

    # --- Section 5: Stacking decorators ---
    print("--- Section 5: Stacking decorators ---")

    @bold
    @italic
    def say(text):
        """Say something with style."""
        return text

    # Equivalent to: say = bold(italic(say))
    result = say("hello")
    print(f"say('hello') = {result!r}")
    # Output: say('hello') = '<b><i>hello</i></b>'
    assert result == "<b><i>hello</i></b>"

    # Reverse order
    @italic
    @bold
    def say_reversed(text):
        return text

    result = say_reversed("hello")
    print(f"say_reversed('hello') = {result!r}")
    # Output: say_reversed('hello') = '<i><b>hello</b></i>'
    assert result == "<i><b>hello</b></i>"

    # Triple stacking
    def underline(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return f"<u>{func(*args, **kwargs)}</u>"
        return wrapper

    @bold
    @italic
    @underline
    def fancy(text):
        return text

    result = fancy("wow")
    print(f"fancy('wow') = {result!r}")
    # Output: fancy('wow') = '<b><i><u>wow</u></i></b>'
    assert result == "<b><i><u>wow</u></i></b>"

    print()

    # --- Section 6: @singleton class decorator ---
    print("--- Section 6: @singleton class decorator ---")

    @singleton
    class DatabaseConnection:
        def __init__(self, url="sqlite:///db.sqlite"):
            self.url = url
            print(f"[singleton] Connecting to {url}")

    db1 = DatabaseConnection()
    # Output: [singleton] Connecting to sqlite:///db.sqlite
    db2 = DatabaseConnection()
    # No output -- reuses existing instance

    print(f"db1 is db2: {db1 is db2}")
    # Output: db1 is db2: True
    assert db1 is db2

    print(f"db1.url = {db1.url!r}")
    # Output: db1.url = 'sqlite:///db.sqlite'
    assert db1.url == "sqlite:///db.sqlite"

    print()

    # --- Section 7a: Manual LRU cache ---
    print("--- Section 7a: Manual LRU cache ---")

    computation_count = 0

    @cache(maxsize=3)
    def fibonacci(n):
        """Compute the nth Fibonacci number recursively."""
        global computation_count
        computation_count += 1
        if n < 2:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    result = fibonacci(10)
    print(f"fibonacci(10) = {result}")
    # Output: fibonacci(10) = 55
    assert result == 55

    info = fibonacci.cache_info()
    print(f"Cache info: {info}")
    # Output: Cache info: {'size': 3, 'maxsize': 3}
    assert info["maxsize"] == 3
    assert info["size"] <= 3

    # Calling again should hit the cache (no new computations)
    old_count = computation_count
    result2 = fibonacci(10)
    assert result2 == 55
    # fibonacci(10) is in cache, so no new computations
    # (fibonacci(10) calls fibonacci(9) and fibonacci(8), which are also cached)
    print(f"Second call: computation_count unchanged = {computation_count == old_count}")
    # Output: Second call: computation_count unchanged = True

    # Test cache_clear
    fibonacci.cache_clear()
    assert fibonacci.cache_info()["size"] == 0
    print(f"After cache_clear: size = {fibonacci.cache_info()['size']}")
    # Output: After cache_clear: size = 0

    print()

    # --- Section 7b: @deprecated warning decorator ---
    print("--- Section 7b: @deprecated warning decorator ---")

    @deprecated(reason="Use new_function() instead")
    def old_function():
        """This function is old."""
        return "old result"

    # Capture the warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = old_function()
        assert result == "old result"
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "old_function is deprecated" in str(w[0].message)
        assert "Use new_function() instead" in str(w[0].message)
        print(f"Warning caught: {w[0].message}")
        # Output: Warning caught: old_function is deprecated: Use new_function() instead

    # Metadata preserved
    assert old_function.__name__ == "old_function"
    assert old_function.__doc__ == "This function is old."
    print(f"Metadata preserved: __name__ = {old_function.__name__!r}")
    # Output: Metadata preserved: __name__ = 'old_function'

    print()

    # --- Section 8: The @ syntax is sugar ---
    print("--- Section 8: The @ syntax is sugar ---")

    def multiply(a, b):
        """Multiply two numbers."""
        return a * b

    # Manually applying the decorator (no @ syntax)
    multiply_timed = timer(multiply)
    result = multiply_timed(6, 7)
    # Output: [timer] multiply took 0.0000s
    assert result == 42
    print(f"Result: {result}")
    # Output: Result: 42

    # The two approaches are identical:
    assert multiply_timed.__wrapped__ is multiply
    print(f"__wrapped__ points to original: {multiply_timed.__wrapped__.__name__!r}")
    # Output: __wrapped__ points to original: 'multiply'

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Decorators are functions that take functions and return functions.")
    print("  - Simple decorator: def deco(func) -> wrapper")
    print("  - @wraps(func): always use it to preserve metadata")
    print("  - Decorator factory: def deco(args) -> decorator -> wrapper")
    print("  - Stacking: @A @B @C → func = A(B(C(func)))")
    print("  - Class decorator: same pattern, but takes/returns a class")
    print("  - Real-world: @cache, @deprecated, @retry, @validate_types")
    print()
    print("All sections passed. You've mastered decorators!")
