# Kata 33 -- Logging & Debugging

[prev: 32-import-system](./32-import-system.md) | [next: 34-testing-pytest](./34-testing-pytest.md)

---

## What We're Building

A comprehensive exploration of Python's **logging** and **debugging** toolkit -- the tools every professional Python developer reaches for when things go wrong (or when they want to make sure things go right).

We'll build six demonstrations:
1. **Logging basics** -- log levels, basic configuration, and the `logging` module API
2. **Handlers and formatters** -- directing log output to multiple destinations with custom formats
3. **Filters and logger hierarchy** -- fine-grained control over which messages appear and where
4. **The `traceback` module** -- programmatic exception inspection and formatting
5. **The `warnings` module** -- deprecation notices, resource warnings, and custom warning categories
6. **Debugging with `breakpoint()` and `pdb`** -- interactive debugging commands and techniques (shown as informational prints to avoid blocking)

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `logging.getLogger()` | Get a named logger (creates hierarchy) | Always -- never use `print()` for production logging |
| `logging.basicConfig()` | Quick one-shot logging setup | Simple scripts, prototyping |
| `logging.Handler` | Directs log records to a destination | File logging, network logging, email alerts |
| `logging.Formatter` | Controls log message format | Structured logs, timestamps, context |
| `logging.Filter` | Selectively allows/blocks log records | Filtering by source, level, or content |
| Logger hierarchy | Dot-separated names create parent-child trees | Modular logging (`app.db`, `app.http`) |
| `traceback.format_exc()` | Capture exception traceback as a string | Logging exceptions, error reporting |
| `traceback.extract_tb()` | Parse traceback into structured data | Programmatic error analysis |
| `warnings.warn()` | Issue a deprecation or runtime warning | API evolution, resource issues |
| `warnings.filterwarnings()` | Control which warnings are shown | Suppress noise, promote errors |
| `breakpoint()` | Drop into the debugger (PEP 553) | Interactive debugging (Python 3.7+) |
| `pdb` commands | Step, continue, inspect in the debugger | Tracing execution flow |

## The Code

### Logging Basics

The `logging` module provides five standard levels. Each level includes all levels above it -- setting `WARNING` shows warnings, errors, and critical messages, but hides info and debug.

```python
import logging

# Create a named logger (not the root logger)
logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)

# Without handlers, nothing is output. Add a console handler:
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.debug("Variable x = 42")         # Detailed diagnostic info
logger.info("Server started on :8000")   # Confirmation things work
logger.warning("Disk usage at 85%")      # Something unexpected
logger.error("Connection refused")       # Something failed
logger.critical("Database corrupted!")    # Program may not continue
```

The five levels have numeric values: `DEBUG=10`, `INFO=20`, `WARNING=30`, `ERROR=40`, `CRITICAL=50`. You can also define custom levels with `logging.addLevelName()`.

### Handlers and Formatters

Handlers determine *where* log records go. You can attach multiple handlers to a single logger -- one for the console, one for a file, one for errors only.

```python
import logging

logger = logging.getLogger("myapp.handlers")
logger.setLevel(logging.DEBUG)

# Console handler -- shows INFO and above
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

# File handler -- captures everything (DEBUG+)
file_handler = logging.FileHandler("/tmp/myapp.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
)

# Error-only handler -- only ERROR and CRITICAL
error_handler = logging.FileHandler("/tmp/myapp_errors.log")
error_handler.setLevel(logging.ERROR)

logger.addHandler(console)
logger.addHandler(file_handler)
logger.addHandler(error_handler)
```

A `MemoryHandler` is useful for buffering: it collects records and only flushes when a threshold is reached or a high-severity record appears.

### Filters and Logger Hierarchy

Logger names with dots create a hierarchy. `app.db` is a child of `app`, and messages propagate upward. Filters let you intercept records at any point.

```python
import logging

class SensitiveDataFilter(logging.Filter):
    """Strip sensitive data from log records."""
    SENSITIVE_KEYS = {"password", "token", "secret"}

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for key in self.SENSITIVE_KEYS:
            if key in msg.lower():
                record.msg = "[REDACTED -- contains sensitive data]"
                record.args = ()
                break
        return True  # True = keep the record (modified)
```

Returning `True` from `filter()` keeps the record; returning `False` suppresses it entirely.

### The `traceback` Module

When you catch an exception, `traceback` lets you inspect it programmatically instead of just printing it.

```python
import traceback

try:
    result = 1 / 0
except ZeroDivisionError:
    # Get the formatted traceback as a string
    tb_str = traceback.format_exc()
    print(tb_str)

    # Extract structured frame info
    import sys
    tb = sys.exc_info()[2]
    frames = traceback.extract_tb(tb)
    for frame in frames:
        print(f"  File {frame.filename}, line {frame.lineno}, in {frame.name}")
```

### The `warnings` Module

Warnings are for things that aren't errors yet but might become errors later -- deprecated APIs, resource leaks, or suspicious usage patterns.

```python
import warnings

# Issue a deprecation warning
def old_api():
    warnings.warn("old_api() is deprecated, use new_api()", DeprecationWarning, stacklevel=2)
    return new_api()

# Control which warnings appear
warnings.filterwarnings("ignore", category=DeprecationWarning)   # Silence
warnings.filterwarnings("error", category=ResourceWarning)       # Promote to exception
warnings.filterwarnings("always", message=".*critical.*")        # Always show
```

The `stacklevel` parameter controls which frame appears in the warning message -- `stacklevel=2` points to the *caller* of the function, not the `warn()` call itself.

### Debugging with `breakpoint()` and `pdb`

Python 3.7+ provides `breakpoint()` as the standard way to drop into a debugger. It calls `sys.breakpointhook()`, which defaults to `pdb.set_trace()`.

```python
# In production code, you'd write:
# breakpoint()  # Drops into pdb at this line

# Key pdb commands (shown as reference, not invoked):
# n (next)      -- execute next line
# s (step)      -- step into function call
# c (continue)  -- continue to next breakpoint
# p expr        -- print expression value
# pp expr       -- pretty-print expression
# l (list)      -- show source code around current line
# w (where)     -- show call stack
# b line        -- set breakpoint at line number
# q (quit)      -- exit debugger

# Disable breakpoints via environment variable:
# PYTHONBREAKPOINT=0 python script.py
```

**Never invoke `pdb.set_trace()` or `breakpoint()` in automated scripts** -- it blocks waiting for interactive input.

## Playground

```python
python playground/33_logging_debugging.py
```

### Expected Output

```
--- Section 1: Logging Basics ---
  [DEBUG] debug: Detailed diagnostic info
  [INFO] info: Server started on port 8000
  [WARNING] warning: Disk space at 85%
  [ERROR] error: Connection refused
  [CRITICAL] critical: Database corrupted!
  Level numbers: DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50
  Logging with context: User alice performed login from 192.168.1.1

--- Section 2: Handlers & Formatters ---
  StringHandler captured 4 records at INFO+
  FileHandler wrote to /tmp/kata33_debug.log
  Custom formatter output: [WARNING] handlers_demo: Disk is 85% full (handlers_demo)
  Multiple handlers allow routing: console=INFO+, file=DEBUG+, errors=ERROR+

--- Section 3: Filters & Logger Hierarchy ---
  Filter kept: Normal operational message
  Filter redacted: [REDACTED -- contains sensitive data]
  Filter suppressed 1 noisy record(s)
  Logger hierarchy: app -> app.db -> app.db.queries
  Parent logger 'app' received 3 propagated records from children

--- Section 4: Traceback Module ---
  Caught: division by zero
  Traceback has 2 frame(s)
  Frame: File "playground/33_logging_debugging.py", line N, in demo_traceback_module
  Frame: File "playground/33_logging_debugging.py", line N, in cause_error
  Formatted exception (first line): Traceback (most recent call last):
  Chained exception: original -> wrapper
  traceback.format_exception() returns a list of strings

--- Section 5: Warnings Module ---
  Warning captured: old_function() is deprecated, use new_function() instead
  Warning category: DeprecationWarning
  Custom warning: DataQualityWarning -- 15 rows had null values
  filterwarnings('error') converts warnings to exceptions: caught it!
  stacklevel=2 points warning to caller, not to warn() call

--- Section 6: Debugging (pdb reference) ---
  breakpoint() calls sys.breakpointhook (default: pdb.set_trace)
  PYTHONBREAKPOINT=0 disables all breakpoints
  PYTHONBREAKPOINT=module.func routes to custom debugger
  Key pdb commands:
    n (next)     -- execute next line, skip into functions
    s (step)     -- step INTO function calls
    c (continue) -- run until next breakpoint or end
    p expr       -- evaluate and print expression
    l (list)     -- show source around current line
    w (where)    -- print call stack (most recent frame last)
    b N          -- set breakpoint at line N
    cl N         -- clear breakpoint at line N
    r (return)   -- run until current function returns
    q (quit)     -- abort program
  Post-mortem debugging: pdb.pm() after an unhandled exception
  breakpoint() is preferred over pdb.set_trace() (PEP 553)

--- Summary ---
Python's logging and debugging toolkit:
  - Use logging, not print() -- it's configurable, filterable, and hierarchical
  - Handlers route logs to console, files, network, email, etc.
  - Filters provide fine-grained control over which records appear
  - traceback module gives programmatic access to exception info
  - warnings module manages deprecations and soft alerts
  - breakpoint() + pdb provide interactive debugging (never in production scripts)

All 6 sections passed. Logging & debugging concepts mastered!
```

## How It Works

```
LOGGING ARCHITECTURE:

  Logger ("app.db")          Logger ("app.http")
       │                          │
       ▼                          ▼
  ┌─────────┐              ┌─────────┐
  │ Filter  │              │ Filter  │
  │ (level, │              │ (level, │
  │  custom)│              │  custom)│
  └────┬────┘              └────┬────┘
       │                        │
       │     propagate=True     │
       └──────────┬─────────────┘
                  │
                  ▼
           Logger ("app")        ◄── parent logger
                  │
                  ▼
         ┌────────┴────────┐
         │                 │
    ┌────▼────┐      ┌────▼────┐
    │ Console │      │  File   │
    │ Handler │      │ Handler │
    │ (INFO+) │      │ (DEBUG+)│
    └────┬────┘      └────┬────┘
         │                │
    ┌────▼────┐      ┌────▼────┐
    │Formatter│      │Formatter│
    │ simple  │      │ detailed│
    └─────────┘      └─────────┘

LOG LEVELS:

  CRITICAL  50  ████████████████████████  Program can't continue
  ERROR     40  ██████████████████████    Operation failed
  WARNING   30  ████████████████████      Unexpected but handled
  INFO      20  ██████████████████        Normal operation
  DEBUG     10  ████████████████          Diagnostic detail
  NOTSET     0  (inherits parent level)

DEBUGGING FLOW:

  breakpoint()
       │
       ▼
  sys.breakpointhook()
       │
       ├── PYTHONBREAKPOINT=0 ──► disabled (no-op)
       │
       ├── PYTHONBREAKPOINT="" ──► pdb.set_trace() (default)
       │
       └── PYTHONBREAKPOINT=mod.fn ──► import mod; mod.fn()
                                       (custom debugger)
```

## Exercises

### Exercise 1: Structured JSON logger

Build a handler that outputs log records as JSON lines (one JSON object per log message):

```python
import json
import logging

class JsonHandler(logging.Handler):
    """Emit log records as JSON lines."""

    def emit(self, record: logging.LogRecord):
        # TODO: build a dict with timestamp, level, name, message
        # TODO: if record.exc_info, include formatted traceback
        # TODO: write JSON line to a stream (e.g., sys.stderr)
        ...

logger = logging.getLogger("json_demo")
logger.addHandler(JsonHandler())
logger.setLevel(logging.DEBUG)
logger.info("User logged in", extra={"user_id": 42})
# Should output: {"timestamp": "...", "level": "INFO", "name": "json_demo", "message": "User logged in"}
```

### Exercise 2: Context-injecting filter

Create a filter that automatically adds request context to every log record:

```python
import logging
import threading

class RequestContextFilter(logging.Filter):
    """Inject request ID and user into every log record."""

    _local = threading.local()

    @classmethod
    def set_context(cls, request_id: str, user: str):
        # TODO: store request_id and user on the thread-local
        ...

    def filter(self, record: logging.LogRecord) -> bool:
        # TODO: add request_id and user attributes to the record
        # HINT: use getattr(self._local, "request_id", "N/A")
        ...

# Usage:
# RequestContextFilter.set_context("req-123", "alice")
# logger.info("Processing order")  # → "[req-123] alice: Processing order"
```

### Exercise 3: Custom warning with auto-escalation

Write a warning system that automatically escalates to errors after N occurrences:

```python
import warnings

class EscalatingWarning:
    """Track warning counts and escalate to errors."""

    def __init__(self, threshold: int = 3):
        # TODO: initialize counter dict and threshold
        ...

    def warn(self, message: str, category=UserWarning):
        # TODO: increment count for this message
        # TODO: if count >= threshold, raise an exception instead
        # TODO: otherwise, issue a warnings.warn()
        ...

ew = EscalatingWarning(threshold=3)
ew.warn("Retry failed")  # warning
ew.warn("Retry failed")  # warning
ew.warn("Retry failed")  # raises RuntimeError!
```

## What's Next

In [Kata 34 -- Testing with pytest](./34-testing-pytest.md), we'll explore Python's testing ecosystem -- writing tests with `pytest`, fixtures, parametrize, mocking, and test-driven development. Logging and debugging are essential companions to testing: you'll use `caplog` to assert on log output and `pdb` to diagnose failing tests.

---

[prev: 32-import-system](./32-import-system.md) | [next: 34-testing-pytest](./34-testing-pytest.md)
