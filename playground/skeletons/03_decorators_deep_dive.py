"""
Kata 03 -- Decorators Deep Dive
Run: python playground/skeletons/03_decorators_deep_dive.py

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
    # TODO: define a wrapper function that:
    #   1. Records the start time with time.perf_counter()
    #   2. Calls func(*args, **kwargs) and stores the result
    #   3. Records the end time
    #   4. Prints f"[timer] {func.__name__} took {elapsed:.4f}s"
    #   5. Returns the result
    # HINT: use @wraps(func) on the wrapper to preserve metadata
    pass


# ---------------------------------------------------------------------------
# Section 2: Bad decorator (no @wraps) vs good decorator
# ---------------------------------------------------------------------------

def bad_timer(func):
    """A decorator that DOESN'T use @wraps -- metadata is lost."""
    # TODO: same as timer, but WITHOUT @wraps(func)
    # This demonstrates why @wraps matters
    pass


# ---------------------------------------------------------------------------
# Section 3: Decorator factory -- decorators with arguments
# ---------------------------------------------------------------------------

def retry(max_attempts=3, delay=0.01):
    """Retry a function up to max_attempts times on exception."""
    # TODO: three levels of nesting:
    #   1. retry(max_attempts, delay) -- captures config (this function)
    #   2. decorator(func) -- captures the function
    #   3. wrapper(*args, **kwargs) -- runs on each call
    #
    # In wrapper:
    #   - Loop from 1 to max_attempts
    #   - Try calling func(*args, **kwargs) and return the result
    #   - On exception: print the attempt number, sleep if not last attempt
    #   - After all attempts exhausted, raise the last exception
    #
    # HINT: return decorator from retry(), return wrapper from decorator()
    pass


# ---------------------------------------------------------------------------
# Section 4: @validate_types using type hints
# ---------------------------------------------------------------------------

def validate_types(func):
    """Validate function arguments match their type annotations."""
    # TODO:
    #   1. Get the function's signature with inspect.signature(func)
    #   2. Get type hints from func.__annotations__
    #   3. In wrapper: bind args/kwargs with sig.bind(*args, **kwargs)
    #   4. Call bound.apply_defaults() to fill in defaults
    #   5. For each argument, check if it matches the expected type
    #   6. Raise TypeError if not: f"Argument '{name}' expected {type}, got {actual}"
    #   7. Call and return func(*args, **kwargs) if all types pass
    #
    # HINT: skip the "return" key in annotations -- it's the return type, not a param
    pass


# ---------------------------------------------------------------------------
# Section 5: Stacking decorators
# ---------------------------------------------------------------------------

def bold(func):
    """Wrap the return value in <b> tags."""
    # TODO: return a wrapper that returns f"<b>{func(...)}</b>"
    # HINT: use @wraps(func)
    pass


def italic(func):
    """Wrap the return value in <i> tags."""
    # TODO: return a wrapper that returns f"<i>{func(...)}</i>"
    # HINT: use @wraps(func)
    pass


# ---------------------------------------------------------------------------
# Section 6: @singleton class decorator
# ---------------------------------------------------------------------------

def singleton(cls):
    """Class decorator that ensures only one instance exists."""
    # TODO:
    #   1. Create an empty dict `instances`
    #   2. Define get_instance(*args, **kwargs) that:
    #      - Checks if cls is in instances
    #      - If not, creates cls(*args, **kwargs) and stores it
    #      - Returns the stored instance
    #   3. Return get_instance
    #
    # HINT: use @wraps(cls) on get_instance
    pass


# ---------------------------------------------------------------------------
# Section 7: Real-world patterns
# ---------------------------------------------------------------------------

# --- Manual LRU cache ---

def cache(maxsize=128):
    """LRU cache decorator with configurable max size."""
    # TODO: decorator factory that:
    #   1. Creates an OrderedDict as cache_store
    #   2. In wrapper: build a cache key from (args, tuple(sorted(kwargs.items())))
    #   3. If key exists: move_to_end(key) and return cached result
    #   4. If not: compute result, store it, evict oldest if over maxsize
    #   5. Add cache_info() and cache_clear() methods to wrapper
    #
    # HINT: OrderedDict.popitem(last=False) removes the oldest entry
    pass


# --- @deprecated warning decorator ---

def deprecated(reason=""):
    """Mark a function as deprecated with an optional reason."""
    # TODO: decorator factory that:
    #   1. Builds a message: f"{func.__name__} is deprecated"
    #   2. Appends f": {reason}" if reason is provided
    #   3. In wrapper: call warnings.warn(message, DeprecationWarning, stacklevel=2)
    #   4. Then call and return func(*args, **kwargs)
    #
    # HINT: stacklevel=2 makes the warning point to the caller, not the decorator
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Simple @timer decorator ---
    print("--- Section 1: Simple @timer decorator ---")
    try:
        @timer
        def slow_add(a, b):
            """Add two numbers slowly."""
            time.sleep(0.05)
            return a + b

        result = slow_add(2, 3)
        assert result == 5
        print(f"Result: {result}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: @wraps preserves metadata ---
    print("--- Section 2: @wraps preserves metadata ---")
    try:
        @bad_timer
        def add_bad(a, b):
            """Add two numbers."""
            return a + b

        print(f"Without @wraps: __name__ = {add_bad.__name__!r}")
        assert add_bad.__name__ == "wrapper"

        print(f"Without @wraps: __doc__  = {add_bad.__doc__!r}")
        assert add_bad.__doc__ is None
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        @timer  # timer uses @wraps
        def add_good(a, b):
            """Add two numbers."""
            return a + b

        print(f"With @wraps:    __name__ = {add_good.__name__!r}")
        assert add_good.__name__ == "add_good"

        print(f"With @wraps:    __doc__  = {add_good.__doc__!r}")
        assert add_good.__doc__ == "Add two numbers."

        assert hasattr(add_good, "__wrapped__")
        print(f"With @wraps:    __wrapped__ is accessible: {hasattr(add_good, '__wrapped__')}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Decorator factory (@retry) ---
    print("--- Section 3: Decorator factory (@retry) ---")
    try:
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
        print(f"Result: {result}")
        assert result == "success"
        assert call_count == 3

        assert flaky_function.__name__ == "flaky_function"
        print(f"Metadata preserved: __name__ = {flaky_function.__name__!r}")

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
        assert fail_count >= 2
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: @validate_types ---
    print("--- Section 4: @validate_types ---")
    try:
        @validate_types
        def greet(name: str, times: int = 1) -> str:
            return f"Hello, {name}! " * times

        result = greet("Alice", 2)
        print(f"greet('Alice', 2) = {result!r}")
        assert result == "Hello, Alice! Hello, Alice! "

        result = greet("Bob")
        print(f"greet('Bob') = {result!r}")
        assert result == "Hello, Bob! "

        try:
            greet(42)
        except TypeError as e:
            print(f"TypeError caught: {e}")
        assert greet.__name__ == "greet"

        try:
            greet("Alice", "many")
        except TypeError as e:
            print(f"TypeError caught: {e}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Stacking decorators ---
    print("--- Section 5: Stacking decorators ---")
    try:
        @bold
        @italic
        def say(text):
            """Say something with style."""
            return text

        result = say("hello")
        print(f"say('hello') = {result!r}")
        assert result == "<b><i>hello</i></b>"

        @italic
        @bold
        def say_reversed(text):
            return text

        result = say_reversed("hello")
        print(f"say_reversed('hello') = {result!r}")
        assert result == "<i><b>hello</b></i>"

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
        assert result == "<b><i><u>wow</u></i></b>"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: @singleton class decorator ---
    print("--- Section 6: @singleton class decorator ---")
    try:
        @singleton
        class DatabaseConnection:
            def __init__(self, url="sqlite:///db.sqlite"):
                self.url = url
                print(f"[singleton] Connecting to {url}")

        db1 = DatabaseConnection()
        db2 = DatabaseConnection()

        print(f"db1 is db2: {db1 is db2}")
        assert db1 is db2

        print(f"db1.url = {db1.url!r}")
        assert db1.url == "sqlite:///db.sqlite"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7a: Manual LRU cache ---
    print("--- Section 7a: Manual LRU cache ---")
    try:
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
        assert result == 55

        info = fibonacci.cache_info()
        print(f"Cache info: {info}")
        assert info["maxsize"] == 3
        assert info["size"] <= 3

        old_count = computation_count
        result2 = fibonacci(10)
        assert result2 == 55
        print(f"Second call: computation_count unchanged = {computation_count == old_count}")

        fibonacci.cache_clear()
        assert fibonacci.cache_info()["size"] == 0
        print(f"After cache_clear: size = {fibonacci.cache_info()['size']}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7b: @deprecated warning decorator ---
    print("--- Section 7b: @deprecated warning decorator ---")
    try:
        @deprecated(reason="Use new_function() instead")
        def old_function():
            """This function is old."""
            return "old result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()
            assert result == "old result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_function is deprecated" in str(w[0].message)
            assert "Use new_function() instead" in str(w[0].message)
            print(f"Warning caught: {w[0].message}")

        assert old_function.__name__ == "old_function"
        assert old_function.__doc__ == "This function is old."
        print(f"Metadata preserved: __name__ = {old_function.__name__!r}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: The @ syntax is sugar ---
    print("--- Section 8: The @ syntax is sugar ---")
    try:
        def multiply(a, b):
            """Multiply two numbers."""
            return a * b

        multiply_timed = timer(multiply)
        result = multiply_timed(6, 7)
        assert result == 42
        print(f"Result: {result}")

        assert multiply_timed.__wrapped__ is multiply
        print(f"__wrapped__ points to original: {multiply_timed.__wrapped__.__name__!r}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Decorators are functions that take functions and return functions.")
    print("  - Simple decorator: def deco(func) -> wrapper")
    print("  - @wraps(func): always use it to preserve metadata")
    print("  - Decorator factory: def deco(args) -> decorator -> wrapper")
    print("  - Stacking: @A @B @C -> func = A(B(C(func)))")
    print("  - Class decorator: same pattern, but takes/returns a class")
    print("  - Real-world: @cache, @deprecated, @retry, @validate_types")
    print()
    print("All sections passed. You've mastered decorators!")
