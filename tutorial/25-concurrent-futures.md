# Kata 25 -- concurrent.futures

[prev: 24-multiprocessing](./24-multiprocessing.md) | [next: 26-async-await](./26-async-await.md)

---

## What We're Building

A high-level concurrency toolkit using `concurrent.futures` -- Python's unified API for thread-based and process-based parallelism. Instead of manually creating threads or processes, managing queues, and joining workers, you submit callables to an **executor** and get back **Future** objects that represent pending results.

We'll build four practical demos:
1. **Parallel URL fetching** with `ThreadPoolExecutor` -- I/O-bound tasks that benefit from threading
2. **CPU-bound computation** with `ProcessPoolExecutor` -- work that benefits from true parallelism
3. **Progress reporting** with `as_completed` -- process results as they finish, not in submission order
4. **Robust error handling** -- timeouts, exceptions, cancellation, and the `wait` function

The `concurrent.futures` module is the bridge between low-level threading/multiprocessing (Katas 21-24) and high-level async/await (Kata 26). It gives you 80% of the power with 20% of the complexity.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `ThreadPoolExecutor` | Pool of threads for I/O-bound tasks | Network calls, file I/O, database queries |
| `ProcessPoolExecutor` | Pool of processes for CPU-bound tasks | Number crunching, image processing, parsing |
| `executor.submit()` | Submit a single callable, get a `Future` | When you need per-task control or error handling |
| `executor.map()` | Submit many callables, get results in order | When you want ordered results like built-in `map()` |
| `as_completed()` | Iterate futures as they finish (any order) | Progress bars, first-result-wins, logging |
| `Future` objects | Represent a pending result | Check status, get result, add callbacks |
| `Future.result(timeout=)` | Get result with optional timeout | Prevent indefinite blocking |
| `Future.exception()` | Get exception without re-raising | Inspect errors without try/except |
| `Future.cancel()` | Cancel a pending future | Abort unneeded work |
| `wait()` | Wait for multiple futures with conditions | Wait for first completion or all done |
| Context manager | `with executor:` ensures clean shutdown | Always -- prevents resource leaks |

## The Code

### ThreadPoolExecutor -- Parallel I/O

The `ThreadPoolExecutor` manages a pool of worker threads. Because I/O-bound tasks release the GIL while waiting, threads run truly concurrently for network calls, file reads, and database queries.

```python
from concurrent.futures import ThreadPoolExecutor
import time

def fetch_url(url: str) -> dict:
    """Simulate fetching a URL (I/O-bound)."""
    time.sleep(0.02)  # Simulate network latency
    return {"url": url, "status": 200, "size": len(url) * 42}

urls = [f"https://api.example.com/users/{i}" for i in range(8)]

# Sequential: ~0.16s (8 * 0.02s)
# Parallel with 4 workers: ~0.04s (2 batches of 4)
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(fetch_url, urls))

for r in results:
    print(f"  {r['url']} -> {r['status']} ({r['size']} bytes)")
```

Key points:
- `executor.map(func, iterable)` works like built-in `map()` but runs calls in parallel
- Results come back **in submission order** (not completion order)
- The context manager (`with`) calls `executor.shutdown(wait=True)` on exit -- all tasks complete before proceeding
- `max_workers` defaults to `min(32, os.cpu_count() + 4)` for threads

### submit() vs map()

`submit()` gives you a `Future` object for each task, providing fine-grained control:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_url(url: str) -> dict:
    delay = 0.01 + (hash(url) % 5) * 0.01  # Variable latency
    time.sleep(delay)
    if "bad" in url:
        raise ConnectionError(f"Failed to fetch {url}")
    return {"url": url, "status": 200}

with ThreadPoolExecutor(max_workers=4) as executor:
    # submit() returns a Future immediately
    future_to_url = {
        executor.submit(fetch_url, url): url
        for url in urls
    }

    # as_completed() yields futures as they finish (fastest first)
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result = future.result()
            print(f"  OK: {url}")
        except ConnectionError as e:
            print(f"  FAILED: {url} -- {e}")
```

When to use each:
- **`map()`**: Simple cases -- same function, ordered results, no per-task error handling
- **`submit()`**: Complex cases -- different arguments, error handling, progress tracking, cancellation

### ProcessPoolExecutor -- CPU-Bound Work

For CPU-bound tasks, `ProcessPoolExecutor` sidesteps the GIL by running work in separate processes:

```python
from concurrent.futures import ProcessPoolExecutor
import math

def is_prime(n: int) -> bool:
    """CPU-bound prime check."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

numbers = [112272535095293, 112582705942171, 115280095190773]

# ProcessPoolExecutor for CPU-bound work
with ProcessPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(is_prime, numbers))
```

Important differences from `ThreadPoolExecutor`:
- Arguments and results must be **picklable** (serialized across process boundaries)
- Higher startup cost per worker (new Python interpreter)
- `max_workers` defaults to `os.cpu_count()`
- Cannot share mutable state between tasks (use `multiprocessing.Manager` if needed)

### Future Objects -- The Control Handle

A `Future` represents a computation that may not have completed yet:

```python
future = executor.submit(some_function, arg1, arg2)

# Check state (non-blocking)
future.done()       # True if completed (success or exception)
future.running()    # True if currently executing
future.cancelled()  # True if successfully cancelled

# Get result (blocking)
result = future.result(timeout=5.0)  # Raises TimeoutError if not done in 5s

# Get exception (blocking, but doesn't raise)
exc = future.exception(timeout=5.0)  # Returns None if no exception

# Cancel (only works if not yet running)
was_cancelled = future.cancel()  # Returns True if successfully cancelled

# Add a callback (called when future completes)
future.add_done_callback(lambda f: print(f"Done: {f.result()}"))
```

### wait() -- Flexible Waiting

The `wait()` function provides more control than `as_completed()`:

```python
from concurrent.futures import wait, FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED

futures = [executor.submit(task, i) for i in range(5)]

# Wait for the first one to finish
done, not_done = wait(futures, return_when=FIRST_COMPLETED)

# Wait for the first exception (or all done if no exceptions)
done, not_done = wait(futures, return_when=FIRST_EXCEPTION)

# Wait for all with a timeout
done, not_done = wait(futures, timeout=2.0, return_when=ALL_COMPLETED)
```

The return value is a named tuple of two sets: `done` (completed futures) and `not_done` (still pending).

### Exception Handling

Exceptions in worker tasks are captured by the `Future` and re-raised when you call `.result()`:

```python
def risky_task(x):
    if x == 3:
        raise ValueError(f"Bad input: {x}")
    return x * 10

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(risky_task, i) for i in range(5)]

    for future in as_completed(futures):
        try:
            result = future.result(timeout=1.0)
            print(f"  Result: {result}")
        except ValueError as e:
            print(f"  Error: {e}")
        except TimeoutError:
            print("  Timed out!")
```

The exception is raised in the **calling thread**, not the worker thread. The original traceback is preserved, making debugging straightforward.

### Timeout Patterns

```python
# Per-future timeout
try:
    result = future.result(timeout=2.0)
except TimeoutError:
    print("Task took too long")
    future.cancel()  # Try to cancel (may fail if already running)

# Global timeout with wait()
done, not_done = wait(futures, timeout=3.0)
for future in not_done:
    future.cancel()  # Cancel anything still pending
```

## Playground

Run the full demonstration:

```bash
python playground/25_concurrent_futures.py
```

```
--- Section 1: ThreadPoolExecutor (Parallel I/O) ---
  Fetching 8 URLs with 4 workers...
  Fetched https://api.example.com/users/0 -> 200 (1554 bytes) in 0.02s
  Fetched https://api.example.com/users/1 -> 200 (1596 bytes) in 0.02s
  Fetched https://api.example.com/users/2 -> 200 (1638 bytes) in 0.02s
  Fetched https://api.example.com/users/3 -> 200 (1680 bytes) in 0.02s
  Fetched https://api.example.com/users/4 -> 200 (1722 bytes) in 0.02s
  Fetched https://api.example.com/users/5 -> 200 (1764 bytes) in 0.02s
  Fetched https://api.example.com/users/6 -> 200 (1806 bytes) in 0.02s
  Fetched https://api.example.com/users/7 -> 200 (1848 bytes) in 0.02s
  All 8 fetches completed (parallel with ThreadPool)
  Speedup: parallel is faster than sequential

--- Section 2: ProcessPoolExecutor (CPU-Bound) ---
  Computing CPU-bound tasks with 2 workers...
  cpu_task(0) = 0
  cpu_task(1) = 1
  cpu_task(2) = 8
  cpu_task(3) = 27
  cpu_task(4) = 64
  cpu_task(5) = 125
  ProcessPoolExecutor handles CPU-bound work across processes.

--- Section 3: submit() + as_completed() (Progress Reporting) ---
  Submitting 6 tasks with variable latency...
  [Progress] Completed task -> result: ... (1/6)
  [Progress] Completed task -> result: ... (2/6)
  [Progress] Completed task -> result: ... (3/6)
  [Progress] Completed task -> result: ... (4/6)
  [Progress] Completed task -> result: ... (5/6)
  [Progress] Completed task -> result: ... (6/6)
  All 6 tasks completed. Results collected out of order, reported as finished.

--- Section 4: Exception Handling ---
  Submitting tasks (some will fail)...
  Task 0: result = 0
  Task 1: result = 10
  Task 2: error = Bad value: 2
  Task 3: result = 30
  Task 4: error = Bad value: 4
  Handled 3 successes and 2 errors gracefully.

--- Section 5: Timeouts and Cancellation ---
  Submitting slow + fast tasks...
  Fast task completed: 42
  Slow task: timed out (expected)
  Timeouts prevent indefinite blocking.

--- Section 6: wait() with FIRST_COMPLETED ---
  Submitting 4 tasks...
  First completed: got 1 done, 3 still pending
  After waiting for rest: all 4 done
  wait() gives fine-grained control over completion.

--- Summary ---
concurrent.futures provides a unified high-level API for parallelism:
  - ThreadPoolExecutor: I/O-bound tasks (network, file, DB)
  - ProcessPoolExecutor: CPU-bound tasks (computation, parsing)
  - submit() + as_completed(): progress reporting, error handling
  - map(): simple ordered results (like built-in map)
  - Future: result(), exception(), cancel(), add_done_callback()
  - wait(): FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED
  - Context manager: always use 'with' for clean shutdown

All 6 sections passed. concurrent.futures mastered!
```

## How It Works

```
LOW-LEVEL (Katas 21-24)              HIGH-LEVEL (concurrent.futures)

  Thread()                            ThreadPoolExecutor
  Process()           ────────►         .submit(fn, *args) ──► Future
  Queue()                               .map(fn, iterable)
  Lock()                              ProcessPoolExecutor
  Pool()                                (same API!)

  Manual lifecycle:                   Automatic lifecycle:
  1. Create thread/process            1. Submit callable
  2. Start it                         2. Get Future back
  3. Put work on queue                3. Collect result
  4. Get result from queue
  5. Join thread/process              with executor:  # auto shutdown

  FUTURE LIFECYCLE:

  submit(fn) ──► PENDING ──► RUNNING ──► FINISHED
                    │                       │
                    ▼                       ├── .result() ──► value
                 CANCELLED                  └── .exception() ──► error

  COMPLETION STRATEGIES:

  map()           ──► results in submission order (like built-in map)
  as_completed()  ──► futures in completion order (fastest first)
  wait()          ──► (done, not_done) sets with flexible conditions
```

## Exercises

### Exercise 1: Parallel file processor

Build a function that processes multiple "files" in parallel, returning results as they complete:

```python
def process_files(filenames: list[str], max_workers: int = 3) -> dict[str, str]:
    """Process files in parallel, return {filename: result} dict."""
    # TODO: use ThreadPoolExecutor + as_completed
    # Simulate: each "file" takes 0.01-0.03s to process
    # Return a dict mapping filename to its processed content
    ...

results = process_files(["a.txt", "b.txt", "c.txt", "d.txt"])
assert len(results) == 4
```

### Exercise 2: Retry with futures

Build a function that retries failed tasks up to N times using `submit()`:

```python
def submit_with_retry(executor, fn, *args, max_retries: int = 3):
    """Submit a task, retrying on failure up to max_retries times."""
    # TODO: submit fn(*args), if it raises, resubmit up to max_retries
    # Return the final Future (successful or last failure)
    ...
```

### Exercise 3: First successful result

Build a function that submits multiple tasks and returns the first successful result, cancelling the rest:

```python
def first_success(executor, fn, args_list: list):
    """Run fn with each args, return first successful result."""
    # TODO: use wait(FIRST_COMPLETED) in a loop
    # Cancel remaining futures once you get a success
    # Raise RuntimeError if all fail
    ...
```

## What's Next

In [Kata 26 -- async/await](./26-async-await.md), we'll move from thread/process-based concurrency to Python's async model. You'll learn how a single thread can handle thousands of concurrent I/O operations using coroutines, the event loop, and `asyncio` -- the foundation for modern Python web frameworks like FastAPI.

---

[prev: 24-multiprocessing](./24-multiprocessing.md) | [next: 26-async-await](./26-async-await.md)
