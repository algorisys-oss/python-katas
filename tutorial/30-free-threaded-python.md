# Kata 30 -- Free-Threaded Python

[prev: 29-subinterpreters](./29-subinterpreters.md) | [next: 31-slots-memory](./31-slots-memory.md)

---

## What We're Building

A comprehensive exploration of **free-threaded Python** (PEP 703) -- the most significant change to CPython's concurrency model since the GIL was introduced in 1992. We'll build detection utilities, demonstrate the implications of GIL-free execution, and understand what changes for developers.

We'll build four demonstrations:
1. **GIL detection** -- runtime checks for free-threaded builds using `sys._is_gil_enabled()` and build flags
2. **Thread safety audit** -- common patterns that become unsafe without the GIL
3. **CPU-bound threading comparison** -- timing threads vs sequential for CPU work (where the GIL matters most)
4. **Migration checklist** -- practical code patterns that work on both standard and free-threaded Python

Free-threaded Python is available as an experimental build since Python 3.13 (`python3.13t`). Most users will still run standard CPython with the GIL. All code in this kata works on **both** builds -- we use feature detection throughout.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| PEP 703 | Proposes removing the GIL from CPython | Understanding Python's concurrency future |
| `python3.13t` | Free-threaded CPython build (no GIL) | When you want true thread parallelism |
| `sys._is_gil_enabled()` | Check if the GIL is active at runtime | Feature detection in library code |
| `sysconfig.get_config_var("Py_GIL_DISABLED")` | Check build-time GIL configuration | Detecting free-threaded builds |
| Thread safety | Protecting shared mutable state | Always, but critical without the GIL |
| `threading.Lock` | Mutual exclusion for shared data | Any shared mutable state across threads |
| Atomic operations | Operations that complete without interruption | Understanding what's safe without locks |
| Race conditions | Bugs from unsynchronized concurrent access | Debugging and prevention |

## The Code

### Detecting Free-Threaded Python

The first step in working with free-threaded Python is knowing whether you're running on it. Python 3.13+ provides `sys._is_gil_enabled()`, but older versions don't have it at all.

```python
import sys
import sysconfig

def detect_gil_status() -> dict:
    """Detect GIL status using multiple methods."""
    info = {}

    # Method 1: sys._is_gil_enabled() (Python 3.13+)
    if hasattr(sys, "_is_gil_enabled"):
        info["gil_enabled"] = sys._is_gil_enabled()
    else:
        info["gil_enabled"] = True  # Pre-3.13 always has GIL

    # Method 2: Build configuration
    gil_disabled_flag = sysconfig.get_config_var("Py_GIL_DISABLED")
    info["build_gil_disabled"] = bool(gil_disabled_flag)

    # Method 3: Check for 't' suffix in version (e.g., "3.13t")
    info["is_free_threaded_build"] = hasattr(sys, "_is_gil_enabled") and not sys._is_gil_enabled()

    # Method 4: Python version
    info["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    info["supports_free_threading"] = sys.version_info >= (3, 13)

    return info
```

Key points:
- `sys._is_gil_enabled()` is the **runtime** check -- the GIL can be enabled/disabled dynamically on free-threaded builds
- `sysconfig.get_config_var("Py_GIL_DISABLED")` is the **build-time** check -- was CPython compiled without GIL support?
- The `_` prefix on `_is_gil_enabled` signals it's a provisional API -- it may change in future versions
- On standard CPython, `sys._is_gil_enabled()` doesn't exist, so always check with `hasattr` first

### Why the GIL Exists (and Why It's Going Away)

The GIL (Global Interpreter Lock) has been CPython's answer to thread safety since the beginning:

```
STANDARD CPYTHON (with GIL):

  Thread A          GIL           Thread B
     │               │               │
     ├── acquire ────►│               │
     │   (running)    │  blocked ◄────┤
     │                │               │
     ├── release ────►│               │
     │                │── acquire ───►│
     │   blocked ◄────│   (running)   │
     │                │               │

  Only ONE thread executes Python bytecode at a time.
  Threads take turns, even on multi-core CPUs.

FREE-THREADED PYTHON (no GIL):

  Thread A                        Thread B
     │                               │
     ├── running ──────────── running─┤
     │   (true parallel)              │
     │                               │
     │   Both threads execute         │
     │   Python bytecode              │
     │   simultaneously on            │
     │   different CPU cores           │
```

The GIL made CPython simpler and C extensions safer, but it prevents true multi-core parallelism for CPU-bound Python code. PEP 703 removes it while maintaining backward compatibility through:
- **Biased reference counting** -- efficient single-threaded refcounting with thread-safe fallback
- **Per-object locks** -- fine-grained locking instead of one global lock
- **Deferred reference counting** -- immortalizing frequently shared objects
- **Thread-safe memory allocator** -- mimalloc replaces the default allocator

### Thread Safety Without the GIL

With the GIL, many "unsafe" patterns accidentally work because only one thread runs at a time. Without it, race conditions become real:

```python
import threading

# UNSAFE on free-threaded Python (and technically unsafe WITH GIL too!)
counter = 0

def increment_unsafe():
    global counter
    for _ in range(100_000):
        counter += 1  # NOT atomic: read, add, store

# SAFE: use a lock
lock = threading.Lock()
safe_counter = 0

def increment_safe():
    global safe_counter
    for _ in range(100_000):
        with lock:
            safe_counter += 1
```

What changes without the GIL:
- **`x += 1` is NOT atomic** -- it was never guaranteed to be, but the GIL masked the bug
- **Compound operations on containers still need locks** -- CPython's built-in `list`/`dict`/`set` use internal locks, so a single `.append()` won't corrupt memory, but multi-step invariants (check-then-act, read-modify-write) still race. Don't rely on that internal locking as a language guarantee -- use a `Lock` for correctness and portability
- **Global mutable state is dangerous** -- module-level variables shared across threads need protection
- **C extensions must be thread-safe** -- extensions that relied on the GIL for safety will break

### What Stays the Same

Many things DON'T change with free-threaded Python:
- **`threading.Lock`** still works -- and you should already be using it
- **`queue.Queue`** is still thread-safe -- the recommended way to communicate between threads
- **`concurrent.futures`** works identically -- just potentially faster for CPU-bound work
- **`asyncio`** is unaffected -- it's single-threaded by design
- **I/O-bound threading** sees minimal change -- the GIL was already released during I/O

### CPU-Bound Threading Comparison

The biggest impact of removing the GIL is on CPU-bound threaded code:

```python
import threading
import time

def cpu_work(n: int) -> int:
    """Pure CPU work: sum of squares."""
    total = 0
    for i in range(n):
        total += i * i
    return total

def benchmark_sequential(work_size: int, num_tasks: int) -> float:
    """Run tasks sequentially, return elapsed time."""
    start = time.perf_counter()
    results = [cpu_work(work_size) for _ in range(num_tasks)]
    return time.perf_counter() - start

def benchmark_threaded(work_size: int, num_tasks: int) -> float:
    """Run tasks in threads, return elapsed time."""
    results = [None] * num_tasks

    def worker(idx):
        results[idx] = cpu_work(work_size)

    start = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_tasks)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return time.perf_counter() - start
```

On standard CPython (with GIL):
- Threaded CPU-bound work is **slower** than sequential (GIL contention + context switching overhead)
- This is why `multiprocessing` exists -- to sidestep the GIL

On free-threaded Python (no GIL):
- Threaded CPU-bound work scales with cores -- potentially **N times faster** with N threads
- `multiprocessing` is still useful for isolation, but threading becomes viable for CPU work

### Checking GIL Status in Libraries

If you're writing a library that needs to work on both standard and free-threaded Python:

```python
import sys
import threading

def _gil_is_enabled() -> bool:
    """Check if the GIL is currently enabled."""
    if hasattr(sys, "_is_gil_enabled"):
        return sys._is_gil_enabled()
    return True  # Pre-3.13 always has GIL

class ThreadSafeCounter:
    """Counter that's safe on both standard and free-threaded Python.

    Uses a lock unconditionally -- the small overhead is worth the safety.
    Don't try to be clever by skipping locks when the GIL is enabled.
    """

    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value
```

Best practices for library authors:
- **Always use proper synchronization** -- don't rely on the GIL, even on standard CPython
- **Use `threading.Lock`** for shared mutable state -- it's cheap when uncontended
- **Prefer immutable data** -- tuples, frozensets, and strings are inherently thread-safe
- **Use `queue.Queue`** for producer-consumer patterns -- thread-safe by design
- **Document thread safety** -- be explicit about what's safe to call from multiple threads

### The PYTHONGIL Environment Variable

On free-threaded builds, you can control the GIL at startup:

```bash
# On a free-threaded build (python3.13t):
PYTHONGIL=0 python3.13t script.py   # GIL disabled (default on free-threaded builds)
PYTHONGIL=1 python3.13t script.py   # GIL re-enabled (for compatibility)

# On standard CPython, PYTHONGIL has no effect
```

This is useful for:
- Testing if your code works without the GIL
- Re-enabling the GIL if a C extension requires it
- Gradual migration -- start with GIL enabled, then disable once safe

## Playground

Run the full demonstration:

```bash
python playground/30_free_threaded_python.py
```

```
--- Section 1: GIL Detection ---
  Python version: 3.12.x (or your version)
  Has sys._is_gil_enabled: False (pre-3.13 or standard build)
  GIL is enabled: True
  Build GIL disabled flag: False
  Free-threaded build: No
  Supports free-threading API: No (requires 3.13+)
  Conclusion: Running standard CPython with GIL enabled.

--- Section 2: Thread Safety Demonstration ---
  Running unsafe counter with 4 threads (100000 increments each)...
  Unsafe counter: expected 400000, got 400000
  (With GIL, unsafe counter often appears correct -- the GIL masks the bug)
  Running safe counter with 4 threads (100000 increments each)...
  Safe counter: expected 400000, got 400000
  Safe counter is always correct, with or without GIL.

--- Section 3: CPU-Bound Threading vs Sequential ---
  Work size: 200000, Tasks: 4
  Sequential: 0.XXXXs
  Threaded:   0.XXXXs
  Ratio (threaded/sequential): X.XXx
  With GIL: threaded CPU work is typically slower than sequential.
  Without GIL: threaded CPU work could be up to Nx faster (N = core count).

--- Section 4: Thread-Safe Data Structures ---
  Thread-safe list append: 4000 items (expected 4000)
  Thread-safe dict update: 4000 entries (expected 4000)
  Always protect shared mutable data with locks.

--- Section 5: Migration Readiness Check ---
  [PASS] threading.Lock works correctly
  [PASS] queue.Queue is thread-safe
  [PASS] ThreadPoolExecutor works correctly
  [PASS] Immutable data (tuples, frozensets) is inherently safe
  [INFO] Your code uses proper synchronization -- ready for free-threaded Python!

--- Summary ---
Free-threaded Python (PEP 703) removes the GIL for true thread parallelism:
  - Detect with sys._is_gil_enabled() (Python 3.13+)
  - Always use threading.Lock for shared mutable state
  - Don't rely on the GIL for thread safety (it was never a guarantee)
  - CPU-bound threads benefit most from GIL removal
  - I/O-bound threads see minimal change
  - Write code that works on both builds: proper locks, queues, immutables

All 5 sections passed. Free-threaded Python concepts mastered!
```

## How It Works

```
THE GIL REMOVAL TIMELINE:

  Python 3.12     Python 3.13          Python 3.14+        Future
      │               │                     │                 │
      │           Experimental           Improved           Default?
      │           free-threaded          stability,          No GIL
      │           build (3.13t)          more C ext          build
      │               │                  support              │
      ▼               ▼                     ▼                 ▼

WHAT CHANGES FOR DEVELOPERS:

  Before (GIL era):                 After (free-threaded):

  ┌─────────────────┐               ┌─────────────────┐
  │ CPU-bound work  │               │ CPU-bound work  │
  │ threading: SLOW │  ──────────►  │ threading: FAST │
  │ (use multiproc) │               │ (true parallel) │
  └─────────────────┘               └─────────────────┘

  ┌─────────────────┐               ┌─────────────────┐
  │ I/O-bound work  │               │ I/O-bound work  │
  │ threading: GOOD │  ──────────►  │ threading: GOOD │
  │ (GIL released)  │               │ (no change)     │
  └─────────────────┘               └─────────────────┘

  ┌─────────────────┐               ┌─────────────────┐
  │ Shared state    │               │ Shared state    │
  │ "works" w/o     │  ──────────►  │ MUST use locks  │
  │ locks (unsafe!) │               │ (race conditions│
  └─────────────────┘               │  are real now)  │
                                    └─────────────────┘

FEATURE DETECTION FLOW:

  hasattr(sys, "_is_gil_enabled")?
       │
       ├── No ──► Python < 3.13, GIL is always enabled
       │
       └── Yes ──► sys._is_gil_enabled()
                       │
                       ├── True ──► GIL enabled (standard or PYTHONGIL=1)
                       │
                       └── False ──► Free-threaded mode! True parallelism.
```

## Exercises

### Exercise 1: Thread-safe accumulator

Build an accumulator that safely collects results from multiple threads:

```python
class ThreadSafeAccumulator:
    """Accumulate values from multiple threads safely."""

    def __init__(self):
        # TODO: initialize storage and a lock
        ...

    def add(self, value):
        """Thread-safe add."""
        # TODO: use lock to protect the append
        ...

    def total(self) -> float:
        """Thread-safe sum of all values."""
        # TODO: use lock to protect the read
        ...

    def values(self) -> list:
        """Thread-safe copy of all values."""
        # TODO: return a copy (not the original list!)
        ...

acc = ThreadSafeAccumulator()
# Launch 4 threads, each adding 1000 values
# Assert total == sum of all added values
```

### Exercise 2: GIL-aware benchmark

Write a function that benchmarks a callable with both sequential and threaded execution, and reports whether the GIL appears to be limiting performance:

```python
def benchmark_gil_impact(fn, args_list, num_workers=4) -> dict:
    """Benchmark fn with sequential vs threaded execution.

    Returns dict with 'sequential_time', 'threaded_time', 'speedup',
    and 'gil_likely_limiting' (True if threaded is slower than sequential).
    """
    # TODO: time sequential execution
    # TODO: time threaded execution with num_workers threads
    # TODO: compute speedup ratio
    # TODO: determine if GIL is likely limiting (speedup < 1.0 for CPU-bound)
    ...
```

### Exercise 3: Write a compatibility shim

Create a decorator that adds thread safety to any function that modifies shared state:

```python
def thread_safe(lock=None):
    """Decorator that wraps function execution in a lock.

    If no lock is provided, creates a per-function lock.
    Works on both standard and free-threaded Python.
    """
    # TODO: if lock is None, create a new threading.Lock()
    # TODO: return a decorator that acquires the lock before calling fn
    # HINT: use functools.wraps to preserve the original function metadata
    ...

shared_list = []

@thread_safe()
def append_item(item):
    shared_list.append(item)
```

## What's Next

In [Kata 31 -- __slots__ and Memory](./31-slots-memory.md), we'll explore how Python objects use memory, how `__slots__` eliminates per-instance `__dict__` overhead, and techniques for reducing memory consumption in large-scale applications. Understanding memory layout becomes even more important in free-threaded Python where multiple threads may create objects simultaneously.

---

[prev: 29-subinterpreters](./29-subinterpreters.md) | [next: 31-slots-memory](./31-slots-memory.md)
