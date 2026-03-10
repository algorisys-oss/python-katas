# Kata 04 -- Context Managers

[prev: 03-decorators-deep-dive](./03-decorators-deep-dive.md) | [next: 05-comprehensions-functional](./05-comprehensions-functional.md)

---

## What We're Building

Every time you write `with open("file.txt") as f:`, you're using a **context manager** -- an object that knows how to set something up and tear it down, even when exceptions occur. The `with` statement is Python's way of saying "guarantee this cleanup happens."

In this kata we build several context managers from scratch -- a `Timer`, a `TempDirectory`, exception suppressors, and more. By the end you'll understand the context manager protocol (`__enter__`/`__exit__`), the `@contextmanager` decorator shortcut, how exception handling works inside `with` blocks, and how to compose context managers dynamically with `ExitStack`.

## Concepts You'll Learn

| Concept | What It Does |
|---|---|
| `__enter__` / `__exit__` | The context manager protocol -- called by `with` |
| `@contextmanager` | Generator-based shortcut for writing context managers |
| Exception handling in `__exit__` | Inspect and optionally suppress exceptions |
| Nested `with` statements | Composing multiple context managers |
| `ExitStack` | Dynamic context manager stacking at runtime |
| `async with` | Async context managers (`__aenter__` / `__aexit__`) |

## The Code

### Step 1: Class-based context manager -- `Timer`

The most explicit way to build a context manager is as a class with `__enter__` and `__exit__` methods.

```python
import time

class Timer:
    """Measures elapsed time for a code block."""

    def __init__(self, label: str = "Block") -> None:
        self.label = label
        self.elapsed: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self  # this becomes the 'as' variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        print(f"[{self.label}] {self.elapsed:.4f}s")
        return False  # don't suppress exceptions
```

**How it works:** When Python encounters `with Timer("test") as t:`, it calls `t.__enter__()` and binds the return value to `t`. When the block exits -- normally or via exception -- Python calls `t.__exit__(exc_type, exc_val, exc_tb)`. If no exception occurred, all three arguments are `None`.

```python
with Timer("sleep") as t:
    time.sleep(0.1)

print(f"Measured: {t.elapsed:.1f}s")
# Output: [sleep] 0.1000s (approximate)
# Output: Measured: 0.1s (approximate)
assert t.elapsed >= 0.1
```

### Step 2: A `TempDirectory` context manager

A context manager that creates a temporary directory on enter and cleans it up on exit -- a real-world pattern you'll see in test suites.

```python
import os
import shutil
import tempfile

class TempDirectory:
    """Creates a temp directory, cleans it up on exit."""

    def __init__(self, prefix: str = "kata_") -> None:
        self.prefix = prefix
        self.path: str | None = None

    def __enter__(self) -> str:
        self.path = tempfile.mkdtemp(prefix=self.prefix)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path and os.path.exists(self.path):
            shutil.rmtree(self.path)
        return False
```

```python
with TempDirectory(prefix="test_") as tmpdir:
    filepath = os.path.join(tmpdir, "data.txt")
    with open(filepath, "w") as f:
        f.write("hello")
    assert os.path.exists(filepath)

# After the with block, the directory is gone
assert not os.path.exists(tmpdir)
```

### Step 3: Generator-based context managers with `@contextmanager`

Writing a class with `__enter__` and `__exit__` is verbose. The `contextlib.contextmanager` decorator lets you write a context manager as a generator function with a single `yield`:

```python
from contextlib import contextmanager

@contextmanager
def timer(label: str = "Block"):
    """Generator-based timer context manager."""
    start = time.perf_counter()
    try:
        yield {"label": label}  # yielded value becomes the 'as' variable
    finally:
        elapsed = time.perf_counter() - start
        print(f"[{label}] {elapsed:.4f}s")
```

**The rule:** Everything before `yield` is `__enter__`. Everything after `yield` is `__exit__`. The `try/finally` ensures cleanup happens even if an exception occurs.

```python
with timer("generator-based") as info:
    time.sleep(0.05)
print(f"Label was: {info['label']}")
# Output: [generator-based] 0.0500s (approximate)
# Output: Label was: generator-based
```

### Step 4: Exception handling in `__exit__`

The `__exit__` method receives exception information. By returning `True`, you can **suppress** the exception -- the code after the `with` block continues normally.

```python
class SuppressErrors:
    """Suppresses specified exception types, like contextlib.suppress."""

    def __init__(self, *exceptions: type[BaseException]) -> None:
        self.exceptions = exceptions
        self.exception: BaseException | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, self.exceptions):
            self.exception = exc_val
            return True  # suppress the exception
        return False  # let other exceptions propagate
```

```python
with SuppressErrors(FileNotFoundError, KeyError) as s:
    raise KeyError("missing key")

# We reach here because the KeyError was suppressed
print(f"Suppressed: {s.exception}")
# Output: Suppressed: 'missing key'

# Other exceptions still propagate:
try:
    with SuppressErrors(FileNotFoundError):
        raise ValueError("not suppressed")
except ValueError as e:
    print(f"Propagated: {e}")
    # Output: Propagated: not suppressed
```

### Step 5: `ExitStack` for dynamic context manager stacking

Sometimes you don't know how many context managers you need until runtime. `ExitStack` lets you push them onto a stack dynamically:

```python
from contextlib import ExitStack

def process_files(filenames: list[str]) -> list[str]:
    """Open a dynamic number of files using ExitStack."""
    with ExitStack() as stack:
        files = [
            stack.enter_context(open(fn, "w"))
            for fn in filenames
        ]
        for f in files:
            f.write(f"data for {f.name}\n")
        return [f.name for f in files]
```

`ExitStack` also supports adding arbitrary cleanup callbacks:

```python
with ExitStack() as stack:
    stack.callback(print, "Third: final cleanup")
    stack.callback(print, "Second: middle cleanup")
    print("First: inside the block")
# Output: First: inside the block
# Output: Second: middle cleanup
# Output: Third: final cleanup
# (callbacks fire in LIFO order -- last registered, first called)
```

### Step 6: Async context managers

For async code, Python provides `async with` and the `__aenter__`/`__aexit__` protocol:

```python
import asyncio

class AsyncTimer:
    """Async context manager for timing async operations."""

    def __init__(self, label: str = "Block") -> None:
        self.label = label
        self.elapsed: float = 0.0

    async def __aenter__(self):
        self._start = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        print(f"[async {self.label}] {self.elapsed:.4f}s")
        return False

async def demo_async():
    async with AsyncTimer("fetch") as t:
        await asyncio.sleep(0.05)
    print(f"Async elapsed: {t.elapsed:.2f}s")
    assert t.elapsed >= 0.05
```

You can also use `contextlib.asynccontextmanager` for the generator-based approach:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_timer(label: str = "Block"):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[async {label}] {elapsed:.4f}s")
```

### Step 7: Real-world patterns

**Pattern 1: Database transaction manager**

```python
@contextmanager
def transaction(conn):
    """Commit on success, rollback on failure."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

**Pattern 2: Redirect stdout**

```python
import sys
from io import StringIO

@contextmanager
def capture_stdout():
    """Capture print output to a string."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old_stdout
```

```python
with capture_stdout() as output:
    print("captured!")
print(f"Got: {output.getvalue().strip()}")
# Output: Got: captured!
```

**Pattern 3: Temporary attribute change**

```python
@contextmanager
def patch_attr(obj, attr, value):
    """Temporarily replace an attribute, restore on exit."""
    old_value = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield old_value
    finally:
        setattr(obj, attr, old_value)
```

## Playground

Run the full interactive demo:

```bash
python playground/04_context_managers.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### The `with` statement protocol

When Python executes `with EXPR as VAR:`, here's what happens:

```
1. manager = EXPR                    # evaluate the expression
2. VAR = manager.__enter__()         # call __enter__, bind result to VAR
3. try:
       BLOCK                         # execute the with-block body
   except:
       if not manager.__exit__(*sys.exc_info()):
           raise                     # re-raise if __exit__ returns falsy
   else:
       manager.__exit__(None, None, None)  # no exception
```

### What `__exit__` receives

| Scenario | `exc_type` | `exc_val` | `exc_tb` |
|---|---|---|---|
| No exception | `None` | `None` | `None` |
| Exception raised | Exception class | Exception instance | Traceback object |

### Suppressing exceptions

If `__exit__` returns a truthy value, the exception is **suppressed** -- execution continues after the `with` block as if nothing happened. If it returns `False` or `None`, the exception propagates normally.

### Generator-based flow

With `@contextmanager`:

```
@contextmanager
def my_cm():
    # __enter__ code
    setup()
    try:
        yield value     # value → 'as' variable; execution pauses here
    finally:
        teardown()      # __exit__ code (runs even on exception)
```

If an exception occurs in the `with` block, it's thrown into the generator at the `yield` point. That's why you need `try/finally` -- without it, an exception would skip your cleanup code.

### ExitStack ordering

`ExitStack` calls cleanup handlers in LIFO (last-in, first-out) order, matching how nested `with` statements unwind:

```
with A() as a:           ExitStack:
    with B() as b:         stack.enter_context(A())
        with C() as c:     stack.enter_context(B())
            ...            stack.enter_context(C())
        # C.__exit__       # C exits first
    # B.__exit__           # B exits second
# A.__exit__               # A exits last
```

## Exercises

### Exercise 1: `@contextmanager`-based database transaction

Implement a `transaction` context manager using `@contextmanager` that:
- Yields the connection
- Calls `conn.commit()` if no exception occurs
- Calls `conn.rollback()` if an exception occurs, then re-raises

```python
@contextmanager
def transaction(conn):
    # your code here
    ...

# Usage:
import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE items (name TEXT)")

with transaction(conn):
    conn.execute("INSERT INTO items VALUES ('apple')")
# Should be committed

try:
    with transaction(conn):
        conn.execute("INSERT INTO items VALUES ('bomb')")
        raise ValueError("abort!")
except ValueError:
    pass
# 'bomb' should NOT be in the table (rolled back)
```

### Exercise 2: Implement `SuppressErrors`

Build a class-based context manager that:
- Accepts a list of exception types to suppress
- Stores the suppressed exception as `.exception`
- Lets other exception types propagate

```python
class SuppressErrors:
    def __init__(self, *exceptions):
        # your code here
        ...

    def __enter__(self):
        # your code here
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        # your code here
        ...

# Usage:
with SuppressErrors(KeyError) as s:
    d = {}
    _ = d["missing"]

assert isinstance(s.exception, KeyError)
```

### Exercise 3: Build a `redirect_stdout` context manager

Using `@contextmanager`, build a context manager that captures all `print()` output into a `StringIO` and restores `sys.stdout` on exit:

```python
with capture_stdout() as output:
    print("hello")
    print("world")

assert output.getvalue() == "hello\nworld\n"
```

## What's Next

In [Kata 05 -- Comprehensions & Functional Python](./05-comprehensions-functional.md), we'll explore list/dict/set comprehensions, generator expressions, and functional tools like `map()`, `filter()`, `reduce()`, and `functools.partial` -- the building blocks of concise, expressive Python.

---

[prev: 03-decorators-deep-dive](./03-decorators-deep-dive.md) | [next: 05-comprehensions-functional](./05-comprehensions-functional.md)
