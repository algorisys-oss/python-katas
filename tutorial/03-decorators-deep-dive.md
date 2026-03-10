# Kata 03 -- Decorators Deep Dive

[prev: 02-iterators-generators](./02-iterators-generators.md) | [next: 04-context-managers](./04-context-managers.md)

---

## What We're Building

Decorators are one of Python's most powerful features -- and one of the most misunderstood. At their core, decorators are just functions that take functions and return functions. The `@` syntax is pure sugar. But once you understand that simple truth, you can build retry logic, caching, rate limiting, type validation, deprecation warnings, and singletons -- all as reusable, composable wrappers.

In this kata we build decorators from the ground up: simple function decorators, decorator factories (decorators that accept arguments), class decorators, and real-world patterns you'll use in production code.

## Concepts You'll Learn

| Concept | What It Does |
|---|---|
| Function decorator | Wraps a function to add behavior before/after the call |
| `functools.wraps` | Preserves the original function's name, docstring, and metadata |
| Decorator factory | A decorator that accepts arguments (returns a decorator) |
| Stacking decorators | Applying multiple decorators (execution order matters) |
| Class decorator | A decorator applied to a class (modifies or replaces the class) |
| `functools.lru_cache` | Built-in memoization decorator (for comparison with our manual version) |

## The Code

### Step 1: A simple `@timer` decorator

The simplest useful decorator: measure how long a function takes to run.

```python
import time
from functools import wraps

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

@timer
def slow_add(a, b):
    """Add two numbers slowly."""
    time.sleep(0.1)
    return a + b

result = slow_add(2, 3)
# Output: [timer] slow_add took 0.10XXs
print(result)
# Output: 5
```

**What just happened?** Writing `@timer` above `slow_add` is exactly equivalent to `slow_add = timer(slow_add)`. Python calls `timer(slow_add)`, which returns `wrapper`. From that point on, the name `slow_add` refers to `wrapper`. When you call `slow_add(2, 3)`, you're actually calling `wrapper(2, 3)`, which records the time, calls the *original* `slow_add`, records the time again, and prints the difference.

### Step 2: Why `@wraps` matters

Without `@wraps(func)`, the wrapper function replaces the original's metadata:

```python
def bad_timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[timer] {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@bad_timer
def add(a, b):
    """Add two numbers."""
    return a + b

print(add.__name__)
# Output: wrapper      <-- WRONG! Should be "add"

print(add.__doc__)
# Output: None          <-- WRONG! Should be "Add two numbers."
```

Adding `@wraps(func)` to the wrapper copies `__name__`, `__doc__`, `__module__`, `__qualname__`, and `__dict__` from the original function. It also sets `__wrapped__` so you can access the original:

```python
@timer  # uses @wraps inside
def multiply(a, b):
    """Multiply two numbers."""
    return a * b

print(multiply.__name__)
# Output: multiply

print(multiply.__doc__)
# Output: Multiply two numbers.

print(multiply.__wrapped__)
# Output: <function multiply at 0x...>
```

**Rule:** Always use `@wraps(func)` in your decorators. Always.

### Step 3: Decorator factory -- decorators with arguments

What if you want `@retry(max_attempts=3)`? You need a function that takes arguments and *returns* a decorator. This is a **decorator factory** -- three levels of nesting:

```python
def retry(max_attempts=3, delay=0.1):
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
print(result)
# Output: success
```

**The three layers:** `retry(max_attempts=3)` is called first, returning `decorator`. Then `@decorator` is applied to `flaky_function`, which returns `wrapper`. Three levels of nesting, each with a purpose:
1. `retry(...)` -- captures the configuration arguments
2. `decorator(func)` -- captures the function being decorated
3. `wrapper(*args, **kwargs)` -- runs on each call

### Step 4: A `@validate_types` decorator using type hints

Use `inspect.get_annotations()` and `inspect.signature()` to validate argument types at runtime:

```python
import inspect

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

@validate_types
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times

print(greet("Alice", 2))
# Output: Hello, Alice! Hello, Alice!

try:
    greet(42)
except TypeError as e:
    print(f"TypeError: {e}")
# Output: TypeError: Argument 'name' expected str, got int
```

### Step 5: Stacking decorators -- execution order

You can stack multiple decorators on a single function. The order matters -- decorators are applied bottom-up (innermost first) but execute top-down (outermost first):

```python
def bold(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"<b>{func(*args, **kwargs)}</b>"
    return wrapper

def italic(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"<i>{func(*args, **kwargs)}</i>"
    return wrapper

@bold
@italic
def say(text):
    return text

# This is equivalent to: say = bold(italic(say))
# italic wraps say first, then bold wraps the result

print(say("hello"))
# Output: <b><i>hello</i></b>
```

**Reading order:** `@bold` is on top, so it's the *outermost* wrapper. When you call `say("hello")`:
1. `bold`'s wrapper runs, calling `func(...)` which is `italic`'s wrapper
2. `italic`'s wrapper runs, calling `func(...)` which is the original `say`
3. The original `say` returns `"hello"`
4. `italic`'s wrapper returns `"<i>hello</i>"`
5. `bold`'s wrapper returns `"<b><i>hello</i></b>"`

### Step 6: A `@singleton` class decorator

Decorators aren't just for functions -- they work on classes too. A classic use case: ensuring only one instance of a class ever exists.

```python
def singleton(cls):
    """Class decorator that ensures only one instance exists."""
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class DatabaseConnection:
    def __init__(self, url="sqlite:///db.sqlite"):
        self.url = url
        print(f"[singleton] Connecting to {url}")

db1 = DatabaseConnection()
# Output: [singleton] Connecting to sqlite:///db.sqlite
db2 = DatabaseConnection()
# No output -- reuses existing instance

print(db1 is db2)
# Output: True
```

### Step 7: Real-world patterns

#### Manual LRU cache

Build your own caching decorator to understand how `functools.lru_cache` works:

```python
from collections import OrderedDict

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

@cache(maxsize=3)
def fibonacci(n):
    """Compute the nth Fibonacci number recursively."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(10))
# Output: 55

print(fibonacci.cache_info())
# Output: {'size': 3, 'maxsize': 3}
```

#### `@deprecated` warning decorator

Warn users when they call a function that's scheduled for removal:

```python
import warnings

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

@deprecated(reason="Use new_function() instead")
def old_function():
    return "old result"

# Calling old_function() will emit:
# DeprecationWarning: old_function is deprecated: Use new_function() instead
```

## Playground

Run the full interactive demo:

```bash
python playground/03_decorators_deep_dive.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Decorators are just functions

The `@decorator` syntax is syntactic sugar. These two blocks are identical:

```
# With @ syntax:                    # Without @ syntax:
@timer                              def slow_add(a, b):
def slow_add(a, b):                     time.sleep(0.1)
    time.sleep(0.1)                     return a + b
    return a + b                    slow_add = timer(slow_add)
```

### The wrapping chain

When you apply a decorator, here's the object graph:

```
Before:   slow_add → <original function>

After:    slow_add → <wrapper function>
                         ↓ calls
                     <original function> (via closure)
```

The wrapper captures the original function in its closure (the `func` variable). Every call goes through the wrapper, which can add behavior before and after calling the original.

### Decorator factory dispatch

A decorator factory adds one more layer of indirection:

```
@retry(max_attempts=3)     →  decorator = retry(max_attempts=3)
def fetch():               →  fetch = decorator(fetch)
    ...                    →  fetch is now wrapper (with retry logic)
```

Step 1: `retry(max_attempts=3)` executes, returning `decorator`.
Step 2: `@decorator` is applied to `fetch`, returning `wrapper`.
Step 3: Calls to `fetch()` go through `wrapper`, which has the retry logic.

### Stacking execution order

```
@A        means:  func = A(B(C(original)))
@B
@C        Call order:  A's wrapper → B's wrapper → C's wrapper → original
def func
```

Decorators are applied bottom-up (C first, then B, then A), but when the decorated function is *called*, execution flows top-down through the wrappers (A's wrapper runs first, then calls B's, which calls C's, which calls the original).

## Exercises

### Exercise 1: Implement `@rate_limit`

Build a `@rate_limit(calls=5, period=60)` decorator that limits how many times a function can be called within a time window. If the limit is exceeded, raise a `RuntimeError`:

```python
@rate_limit(calls=3, period=1.0)
def api_call():
    return "response"

api_call()  # ok
api_call()  # ok
api_call()  # ok
api_call()  # RuntimeError: Rate limit exceeded (3 calls per 1.0s)
```

Hint: Store call timestamps in a `collections.deque` and remove timestamps older than `period` seconds on each call.

### Exercise 2: Implement `@memoize` with TTL

Build a `@memoize(ttl=5.0)` decorator that caches results but expires them after `ttl` seconds:

```python
@memoize(ttl=2.0)
def fetch_data(key):
    print(f"Computing for {key}...")
    return f"result-{key}"

fetch_data("a")   # Computing for a...  → "result-a"
fetch_data("a")   # Cache hit            → "result-a" (no print)
time.sleep(2.1)
fetch_data("a")   # Computing for a...  → "result-a" (cache expired)
```

Hint: Store `(result, timestamp)` tuples in the cache dict. On lookup, check if `time.time() - timestamp > ttl`.

## What's Next

In [Kata 04 -- Context Managers](./04-context-managers.md), we'll explore the `with` statement and the context manager protocol. You'll learn how `__enter__` and `__exit__` work, build custom context managers with `contextlib.contextmanager`, and understand how Python guarantees cleanup even when exceptions occur.

---

[prev: 02-iterators-generators](./02-iterators-generators.md) | [next: 04-context-managers](./04-context-managers.md)
