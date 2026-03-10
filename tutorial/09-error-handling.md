# Kata 09 -- Error Handling Done Right

[prev: 08-enums-pattern-matching](./08-enums-pattern-matching.md) | [next: 10-closures-scoping](./10-closures-scoping.md)

---

## What We're Building

Most Python tutorials teach you `try`/`except` and stop there. Real-world error handling is far richer -- and getting it wrong leads to silent failures, lost context, and debugging nightmares. In this kata we'll master Python's full exception toolkit: custom exception hierarchies, explicit chaining with `raise from`, the LBYL vs EAFP debate, and the powerful Python 3.11+ features `ExceptionGroup`, `except*`, and `add_note()`.

By the end you'll build a validation system that collects *all* errors in a single pass (instead of failing on the first one) and reports them using `ExceptionGroup` -- the same pattern used by asyncio's `TaskGroup` and modern Python libraries.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Exception hierarchy | `BaseException` -> `Exception` -> custom types | Understanding what to catch and where |
| Custom exceptions | Subclass `Exception` with extra attributes | Domain-specific error reporting |
| `raise from` | Explicit exception chaining | Wrapping low-level errors with domain context |
| LBYL vs EAFP | "Look Before You Leap" vs "Easier to Ask Forgiveness" | Choosing the right error-checking style |
| `else` / `finally` | Success-only and cleanup blocks in `try` | Separating happy path from error path |
| `ExceptionGroup` | Group multiple exceptions into one (3.11+) | Concurrent errors, validation collecting all errors |
| `except*` | Selectively handle exceptions in a group (3.11+) | Filtering specific error types from a group |
| `add_note()` | Attach contextual notes to an exception (3.11+) | Adding debugging context without wrapping |
| Best practices | Specific catches, log-and-reraise, avoid bare `except` | Writing maintainable error handling |

## The Code

### Step 1: The exception hierarchy

Python's exception hierarchy is a tree rooted at `BaseException`. Understanding it is essential -- it determines what `except Exception` catches (and what it doesn't).

```
BaseException
├── SystemExit           # sys.exit() -- don't catch this
├── KeyboardInterrupt    # Ctrl+C -- don't catch this
├── GeneratorExit        # generator.close() -- don't catch this
└── Exception            # everything you SHOULD catch derives from here
    ├── ValueError
    ├── TypeError
    ├── KeyError
    ├── AttributeError
    ├── OSError
    │   ├── FileNotFoundError
    │   ├── PermissionError
    │   └── ConnectionError
    ├── RuntimeError
    └── ... (your custom exceptions go here)
```

**Key insight:** `except Exception` catches all "normal" errors but lets `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit` propagate. Never use bare `except:` or `except BaseException:` unless you have a very specific reason (like a top-level crash handler that logs and re-raises).

```python
# WRONG: catches KeyboardInterrupt and SystemExit
try:
    do_work()
except:  # bare except -- NEVER do this
    pass

# WRONG: same problem
try:
    do_work()
except BaseException:
    pass

# RIGHT: catches normal errors, lets system signals through
try:
    do_work()
except Exception as e:
    handle_error(e)
```

### Step 2: Writing custom exceptions

Custom exceptions let you create a domain-specific error vocabulary. Always inherit from `Exception` (not `BaseException`), and add attributes that carry structured data about the error.

```python
class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: object, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"{field}: {message} (got {value!r})")


class NotFoundError(Exception):
    """Raised when a requested resource doesn't exist."""

    def __init__(self, resource_type: str, resource_id: str | int):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} {resource_id!r} not found")


# Usage:
try:
    raise ValidationError("age", -5, "must be non-negative")
except ValidationError as e:
    print(f"Field: {e.field}, Value: {e.value}")
    print(f"Message: {e}")
# Output:
# Field: age, Value: -5
# Message: age: must be non-negative (got -5)
```

**Convention:** Call `super().__init__()` with a human-readable message. Store structured data as attributes so callers can programmatically inspect the error without parsing strings.

### Step 3: `raise from` -- explicit exception chaining

When you catch one exception and raise another, Python supports *exception chaining*. Use `raise ... from original` to explicitly link the cause -- this preserves the full traceback chain for debugging.

```python
class DatabaseError(Exception):
    pass

def get_user(user_id: int) -> dict:
    try:
        # Simulate a low-level database error
        raise ConnectionError("connection refused")
    except ConnectionError as e:
        # Wrap with domain context -- the original error is preserved as __cause__
        raise DatabaseError(f"failed to fetch user {user_id}") from e

try:
    get_user(42)
except DatabaseError as e:
    print(f"Caught: {e}")
    print(f"Original cause: {e.__cause__}")
# Output:
# Caught: failed to fetch user 42
# Original cause: connection refused
```

There are three chaining scenarios:
- `raise X from Y` -- **explicit chaining**, sets `__cause__` (shown as "caused by")
- `raise X` inside `except` -- **implicit chaining**, sets `__context__` (shown as "during handling")
- `raise X from None` -- **suppresses chaining**, hides the original error

```python
# Suppress chaining when the original error is irrelevant to the caller
def parse_config(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("invalid config format") from None
```

### Step 4: LBYL vs EAFP

Python has two styles for handling potential errors:

**LBYL (Look Before You Leap):** Check conditions before attempting an operation.

```python
# LBYL style
def get_value_lbyl(data: dict, key: str) -> str:
    if key in data:
        return data[key]
    return "default"
```

**EAFP (Easier to Ask Forgiveness than Permission):** Just try it, handle the exception if it fails.

```python
# EAFP style (more Pythonic)
def get_value_eafp(data: dict, key: str) -> str:
    try:
        return data[key]
    except KeyError:
        return "default"
```

**When to use each:**
- **EAFP** is preferred in Python when the failure case is rare (it avoids redundant checks and race conditions).
- **LBYL** is better when the check is cheap and failure is common (avoids the overhead of exception handling).
- **LBYL** is necessary when the operation has side effects you can't undo.

```python
# LBYL is better here: failure is common, check is cheap
if user_input.isdigit():
    number = int(user_input)
else:
    number = 0

# EAFP is better here: failure is rare, avoids race condition
try:
    with open(path) as f:
        data = f.read()
except FileNotFoundError:
    data = ""
```

### Step 5: `else` and `finally` in try blocks

The full `try` statement has four clauses, each with a distinct purpose:

```python
def read_config(path: str) -> dict:
    try:
        f = open(path)
    except FileNotFoundError:
        print(f"{path} not found, using defaults")
        return {}
    else:
        # Only runs if try succeeded -- no exception
        # Put success logic here, NOT in the try block
        data = json.load(f)
        return data
    finally:
        # ALWAYS runs -- cleanup goes here
        # Runs whether try succeeded, except caught, or else ran
        if 'f' in locals():
            f.close()
```

**Why `else` matters:** Code in `else` only runs if the `try` block completed without an exception. If you put it inside `try`, you'd accidentally catch exceptions from the success logic too.

```python
# BAD: catches json.JSONDecodeError even though we only wanted FileNotFoundError
try:
    f = open(path)
    data = json.load(f)  # this error gets caught too!
except FileNotFoundError:
    return {}

# GOOD: json errors propagate naturally
try:
    f = open(path)
except FileNotFoundError:
    return {}
else:
    data = json.load(f)  # errors here are NOT caught -- correct!
```

### Step 6: `ExceptionGroup` (Python 3.11+) -- grouping multiple errors

`ExceptionGroup` lets you bundle multiple exceptions into a single raisable object. This is essential when you have multiple independent operations that can each fail -- you want to report *all* failures, not just the first one.

```python
# Raise multiple errors at once
errors = [
    ValueError("name is required"),
    TypeError("age must be an integer"),
    ValueError("email format invalid"),
]
raise ExceptionGroup("validation failed", errors)
```

`ExceptionGroup` is a subclass of `Exception` and can be nested:

```python
# Nested groups
group = ExceptionGroup("outer", [
    ValueError("error 1"),
    ExceptionGroup("inner", [
        TypeError("error 2"),
        KeyError("error 3"),
    ]),
])
```

You can inspect an `ExceptionGroup` with `.exceptions` (the tuple of contained exceptions) and `.subgroup()` / `.split()` for filtering.

```python
# subgroup: filter to only matching exceptions (returns ExceptionGroup or None)
eg = ExceptionGroup("mixed", [
    ValueError("v1"),
    TypeError("t1"),
    ValueError("v2"),
])

val_errors = eg.subgroup(ValueError)
print(val_errors)
# ExceptionGroup('mixed', [ValueError('v1'), ValueError('v2')])

type_errors = eg.subgroup(TypeError)
print(type_errors)
# ExceptionGroup('mixed', [TypeError('t1')])

# split: partition into (match, rest) -- both ExceptionGroup or None
match, rest = eg.split(ValueError)
print(f"Match: {match}")   # ExceptionGroup with ValueErrors
print(f"Rest: {rest}")     # ExceptionGroup with TypeErrors
```

### Step 7: `except*` -- handling exception groups selectively

The `except*` syntax (Python 3.11+) lets you handle specific exception types within an `ExceptionGroup`. Multiple `except*` clauses can each match *different* exceptions from the same group -- unlike regular `except`, they don't short-circuit.

```python
try:
    raise ExceptionGroup("errors", [
        ValueError("bad value 1"),
        TypeError("wrong type"),
        ValueError("bad value 2"),
    ])
except* ValueError as eg:
    print(f"Caught {len(eg.exceptions)} ValueErrors:")
    for e in eg.exceptions:
        print(f"  - {e}")
except* TypeError as eg:
    print(f"Caught {len(eg.exceptions)} TypeErrors:")
    for e in eg.exceptions:
        print(f"  - {e}")
# Output:
# Caught 2 ValueErrors:
#   - bad value 1
#   - bad value 2
# Caught 1 TypeErrors:
#   - wrong type
```

**Key differences from regular `except`:**
- `except*` receives an `ExceptionGroup`, even if only one exception matched
- Multiple `except*` clauses can all fire for the same `raise`
- You cannot mix `except` and `except*` in the same `try` block

### Step 8: `add_note()` (Python 3.11+) -- adding context

`add_note()` lets you attach additional context to an existing exception without wrapping it. Notes are displayed in the traceback and stored in `__notes__`.

```python
def process_batch(items: list[str]) -> list[int]:
    results = []
    errors = []
    for i, item in enumerate(items):
        try:
            results.append(int(item))
        except ValueError as e:
            e.add_note(f"occurred at index {i}")
            e.add_note(f"raw input: {item!r}")
            errors.append(e)
    if errors:
        raise ExceptionGroup("batch processing failed", errors)
    return results

try:
    process_batch(["10", "abc", "20", "xyz"])
except* ValueError as eg:
    for e in eg.exceptions:
        print(f"Error: {e}")
        print(f"Notes: {e.__notes__}")
# Output:
# Error: invalid literal for int() with base 10: 'abc'
# Notes: ['occurred at index 1', "raw input: 'abc'"]
# Error: invalid literal for int() with base 10: 'xyz'
# Notes: ['occurred at index 3', "raw input: 'xyz'"]
```

`add_note()` is especially powerful in combination with `ExceptionGroup` -- you can annotate each error with context before bundling them together.

### Step 9: Best practices

**1. Be specific in what you catch:**

```python
# BAD: catches everything, hides bugs
try:
    result = compute(data)
except Exception:
    result = default_value

# GOOD: catch only what you expect
try:
    result = compute(data)
except (ValueError, ZeroDivisionError) as e:
    log.warning(f"computation failed: {e}")
    result = default_value
```

**2. Log and re-raise -- don't swallow errors:**

```python
import logging

log = logging.getLogger(__name__)

try:
    response = call_external_api()
except ConnectionError as e:
    log.error(f"API call failed: {e}")
    raise  # re-raise the original exception, preserving the traceback
```

**3. Use `raise from` when wrapping errors:**

```python
# BAD: implicit chaining -- confusing traceback
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    raise AppError("invalid payload")

# GOOD: explicit chaining -- clear cause
try:
    data = json.loads(raw)
except json.JSONDecodeError as e:
    raise AppError("invalid payload") from e
```

**4. Don't use exceptions for flow control:**

```python
# BAD: using StopIteration for logic
def find_item(lst, predicate):
    try:
        return next(x for x in lst if predicate(x))
    except StopIteration:
        return None

# GOOD: use next() with a default
def find_item(lst, predicate):
    return next((x for x in lst if predicate(x)), None)
```

### Step 10: Real-world patterns

**Pattern 1: Validation that collects all errors**

Instead of failing on the first invalid field, collect all errors and report them together:

```python
class FieldError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_user(data: dict) -> dict:
    errors: list[FieldError] = []

    name = data.get("name", "")
    if not name:
        errors.append(FieldError("name", "is required"))
    elif len(name) < 2:
        errors.append(FieldError("name", "must be at least 2 characters"))

    age = data.get("age")
    if age is None:
        errors.append(FieldError("age", "is required"))
    elif not isinstance(age, int):
        errors.append(FieldError("age", "must be an integer"))
    elif age < 0 or age > 150:
        errors.append(FieldError("age", "must be between 0 and 150"))

    email = data.get("email", "")
    if not email:
        errors.append(FieldError("email", "is required"))
    elif "@" not in email:
        errors.append(FieldError("email", "must contain @"))

    if errors:
        raise ExceptionGroup("validation failed", errors)

    return data
```

**Pattern 2: Retry with exception chaining**

When retrying an operation, chain the final error to the original failures:

```python
import time

def retry(fn, max_attempts: int = 3, delay: float = 0.1):
    """Retry a function, chaining all failures."""
    errors: list[Exception] = []
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            e.add_note(f"attempt {attempt} of {max_attempts}")
            errors.append(e)
            if attempt < max_attempts:
                time.sleep(delay)
    raise ExceptionGroup(
        f"all {max_attempts} attempts failed", errors
    )
```

## Playground

Run the full interactive demo:

```bash
python playground/09_error_handling.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Exception propagation

When an exception is raised, Python unwinds the call stack frame by frame, looking for a matching `except` clause. If none is found, the exception reaches the top level and Python prints the traceback and exits.

```
raise ValueError("oops")
  → Python checks the current try/except scope
  → no match? unwind one frame up
  → no match? unwind one frame up
  → ... until a match is found or we hit the top level
  → top level: print traceback, exit with code 1
```

### ExceptionGroup tree structure

An `ExceptionGroup` is a tree -- it can contain plain exceptions and other `ExceptionGroup` nodes. Methods like `.subgroup()` and `.split()` traverse this tree, preserving the nesting structure.

```
ExceptionGroup("validation failed", [
    FieldError("name", "required"),
    ExceptionGroup("address errors", [
        FieldError("street", "required"),
        FieldError("zip", "invalid format"),
    ]),
    FieldError("email", "invalid"),
])
```

### `except*` matching semantics

When Python encounters `except*`, it walks the exception group tree and partitions the exceptions. Each `except*` clause receives a *new* `ExceptionGroup` containing only its matches. If any exceptions remain unhandled after all `except*` clauses, they are re-raised automatically.

## Exercises

### Exercise 1: Build a validation system with ExceptionGroup

Implement a `validate_product` function that validates all fields of a product dict and raises an `ExceptionGroup` with all errors:

```python
def validate_product(data: dict) -> dict:
    """Validate a product dict. Collect all errors, raise as ExceptionGroup."""
    # Validate: name (required, min 2 chars), price (required, positive number),
    # quantity (required, non-negative integer)
    ...

# Should raise ExceptionGroup with 3 FieldErrors:
validate_product({"name": "", "price": -10, "quantity": "five"})
```

### Exercise 2: Implement a retry decorator that uses exception chaining

```python
def with_retry(max_attempts: int = 3):
    """Decorator that retries a function, collecting failures in ExceptionGroup."""
    def decorator(fn):
        ...
    return decorator

@with_retry(max_attempts=3)
def flaky_operation():
    import random
    if random.random() < 0.7:
        raise ConnectionError("server unavailable")
    return "success"
```

### Exercise 3: Use `except*` to handle mixed error types

```python
# Given an ExceptionGroup with ValueError, TypeError, and KeyError,
# handle each type separately and print a summary.
```

## What's Next

In [Kata 10 -- Closures & Scoping](./10-closures-scoping.md), we'll explore how Python's scoping rules work -- LEGB scope resolution, closures, `nonlocal`, and the patterns that make decorators, factories, and callbacks possible. Understanding closures is the key to writing powerful higher-order functions.

---

[prev: 08-enums-pattern-matching](./08-enums-pattern-matching.md) | [next: 10-closures-scoping](./10-closures-scoping.md)
