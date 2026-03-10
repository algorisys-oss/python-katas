# Kata 27 -- Async I/O Patterns

[prev: 26-async-await](./26-async-await.md) | [next: 28-async-iterators](./28-async-iterators.md)

---

## What We're Building

Advanced async patterns that go beyond basic `async/await`. In Kata 26 you learned the fundamentals -- coroutines, `gather`, `create_task`, and `Queue`. Now we tackle the patterns you need for **production async code**:

1. **Fan-out/fan-in** -- dispatch many concurrent tasks, collect all results
2. **Semaphore-limited concurrency** -- rate-limit parallel operations (e.g., max 3 API calls at once)
3. **Timeout with fallback** -- `asyncio.wait_for` with graceful degradation
4. **Shielding from cancellation** -- `asyncio.shield` to protect critical work
5. **TaskGroup (Python 3.11+)** -- structured concurrency with automatic cleanup
6. **Graceful cancellation** -- cancelling tasks cleanly with proper exception handling

We'll simulate all I/O with `asyncio.sleep()` so everything runs in under 5 seconds with no network calls.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Fan-out/fan-in | Dispatch N tasks, await all results | Parallel API calls, batch processing |
| `asyncio.Semaphore` | Limit concurrent coroutines | Rate limiting, connection pooling |
| `asyncio.wait_for(coro, timeout)` | Cancel a coroutine after timeout | Prevent indefinite hangs |
| `asyncio.shield(coro)` | Protect from external cancellation | Critical operations (DB writes, payments) |
| `asyncio.TaskGroup` | Structured concurrency (3.11+) | Groups of related tasks with auto-cleanup |
| `ExceptionGroup` | Multiple exceptions from TaskGroup | Handling partial failures in task groups |
| `asyncio.wait()` | Low-level wait with conditions | FIRST_COMPLETED, ALL_COMPLETED patterns |
| Task cancellation | `task.cancel()` + `CancelledError` | Graceful shutdown, timeout cleanup |

## The Code

### Fan-Out/Fan-In Pattern

The most common async pattern: launch many concurrent operations, collect all results. Use `asyncio.gather` for the simple case or `create_task` + manual collection for more control.

```python
import asyncio

async def fetch_user(user_id: int) -> dict:
    """Simulate fetching a user from an API."""
    await asyncio.sleep(0.02)  # Simulate network I/O
    return {"id": user_id, "name": f"User_{user_id}", "active": user_id % 3 != 0}

async def fan_out_fan_in():
    user_ids = [1, 2, 3, 4, 5, 6, 7, 8]

    # Fan-out: launch all fetches concurrently
    # Fan-in: gather collects all results in submission order
    results = await asyncio.gather(*(fetch_user(uid) for uid in user_ids))

    active_users = [u for u in results if u["active"]]
    print(f"  {len(active_users)} active out of {len(results)} total")  # 6 active
```

Key insight: `gather` runs all coroutines concurrently on a **single thread**. Eight fetches that each take 0.02s complete in ~0.02s total, not 0.16s.

### Semaphore-Limited Concurrency

Real APIs have rate limits. Use `asyncio.Semaphore` to cap the number of concurrent operations:

```python
async def rate_limited_fetch(sem: asyncio.Semaphore, url: str) -> dict:
    async with sem:  # Only N coroutines enter at a time
        await asyncio.sleep(0.02)  # Simulate API call
        return {"url": url, "status": 200}

async def demo_semaphore():
    sem = asyncio.Semaphore(3)  # Max 3 concurrent requests
    urls = [f"https://api.example.com/item/{i}" for i in range(10)]

    results = await asyncio.gather(
        *(rate_limited_fetch(sem, url) for url in urls)
    )
    # All 10 complete, but never more than 3 at the same time
```

The semaphore acts like a bouncer -- it lets coroutines in up to the limit, then makes the rest wait until a slot opens.

### Timeout with Fallback

`asyncio.wait_for` wraps a coroutine with a timeout. If it exceeds the deadline, the coroutine is **cancelled** and `asyncio.TimeoutError` is raised:

```python
async def slow_api_call() -> str:
    await asyncio.sleep(1.0)  # Takes too long
    return "slow result"

async def demo_timeout():
    try:
        result = await asyncio.wait_for(slow_api_call(), timeout=0.05)
    except asyncio.TimeoutError:
        result = "default_value"  # Fallback
        print(f"  Timed out, using fallback: {result}")
```

Important: `wait_for` **cancels** the underlying coroutine on timeout. If you need the work to continue even after timeout, use `asyncio.shield`.

### Shielding from Cancellation

`asyncio.shield` prevents a coroutine from being cancelled by an outer `wait_for` or task cancellation:

```python
async def critical_save(data: str) -> str:
    """Must not be cancelled mid-operation."""
    await asyncio.sleep(0.03)  # Simulate DB write
    return f"saved:{data}"

async def demo_shield():
    try:
        result = await asyncio.wait_for(
            asyncio.shield(critical_save("important")),
            timeout=0.01  # Timeout fires, but save continues!
        )
    except asyncio.TimeoutError:
        print("  Timeout fired, but shielded task continues in background")
        await asyncio.sleep(0.05)  # Give it time to finish
```

Shield wraps the coroutine in a separate internal future. When the outer wait times out, only the outer wrapper is cancelled -- the inner work continues.

### TaskGroup -- Structured Concurrency (Python 3.11+)

`TaskGroup` is the modern replacement for `gather` with better error handling. If any task fails, **all other tasks in the group are automatically cancelled**:

```python
async def fetch_data(source: str) -> dict:
    await asyncio.sleep(0.02)
    if source == "bad_source":
        raise ValueError(f"Source '{source}' is unavailable")
    return {"source": source, "data": f"data_from_{source}"}

async def demo_taskgroup():
    results = []
    async with asyncio.TaskGroup() as tg:
        for source in ["db", "cache", "api"]:
            task = tg.create_task(fetch_data(source))
            # Can't access task.result() here -- must wait for group to exit

    # After the `async with` block, all tasks are done
    # Access results via the task objects
```

If any task raises, `TaskGroup.__aexit__` cancels all remaining tasks and raises an `ExceptionGroup` containing all exceptions. Handle it with `except*`:

```python
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(fetch_data("good"))
        tg.create_task(fetch_data("bad_source"))
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"  Caught: {exc}")
```

### Graceful Cancellation

Tasks can be cancelled externally. Well-written async code catches `CancelledError` to perform cleanup:

```python
async def long_running_worker(name: str):
    try:
        while True:
            await asyncio.sleep(0.01)
            # Do work...
    except asyncio.CancelledError:
        print(f"  {name}: cleaning up before exit")
        await asyncio.sleep(0.005)  # Cleanup I/O
        raise  # Always re-raise CancelledError!

async def demo_cancellation():
    task = asyncio.create_task(long_running_worker("worker-1"))
    await asyncio.sleep(0.05)  # Let it run briefly
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("  Task was cancelled cleanly")
```

Golden rule: **always re-raise `CancelledError`** after cleanup. Swallowing it prevents proper cancellation propagation.

## Playground

Run the full demonstration:

```bash
python playground/27_async_io_patterns.py
```

```
--- Section 1: Fan-Out/Fan-In ---
  Fetching 8 users concurrently...
  Fan-out: launched 8 tasks
  Fan-in: collected 8 results in ~0.02s
  Active users: 6 out of 8
  Fan-out/fan-in complete.

--- Section 2: Semaphore-Limited Concurrency ---
  Fetching 10 URLs with max 3 concurrent...
  All 10 fetches completed.
  Max concurrent observed: 3
  Semaphore enforces concurrency limit.

--- Section 3: Timeout with Fallback ---
  Fast call: result = fast_result
  Slow call: timed out, using fallback = default_value
  Timeout with fallback complete.

--- Section 4: asyncio.shield ---
  Shielded save continues despite timeout.
  Save result: saved:critical_data
  Shield protects critical operations from cancellation.

--- Section 5: TaskGroup (Structured Concurrency) ---
  All tasks succeeded: ['db', 'cache', 'api']
  TaskGroup with failure: caught 1 error(s)
  Error: Source 'bad_source' is unavailable
  TaskGroup provides automatic cleanup on failure.

--- Section 6: Graceful Cancellation ---
  Worker ran 4 iterations before cancellation.
  worker-1: cleaning up resources...
  Task cancelled cleanly.

--- Summary ---
Async I/O patterns for production code:
  - Fan-out/fan-in: dispatch many, collect all
  - Semaphore: limit concurrent operations
  - wait_for: timeout with automatic cancellation
  - shield: protect critical work from cancellation
  - TaskGroup: structured concurrency with auto-cleanup
  - Cancellation: catch CancelledError, cleanup, re-raise

All 6 sections passed. Async I/O patterns mastered!
```

## How It Works

```
ASYNC CONCURRENCY PATTERNS

  Fan-Out / Fan-In:
                    ┌── fetch(1) ──┐
  asyncio.gather ───┼── fetch(2) ──┼──► [result1, result2, ..., resultN]
                    ├── fetch(3) ──┤
                    └── fetch(N) ──┘

  Semaphore-Limited:
                    ┌── fetch(1) ──┐
  Semaphore(3) ─────┼── fetch(2) ──┼──► Only 3 run at a time
                    ├── fetch(3) ──┤    Others wait for a slot
                    ├── fetch(4)···│
                    └── fetch(N)···┘

  Timeout + Shield:
  ┌─────────────────────────────────┐
  │  wait_for(coro, timeout=1.0)    │  ← Cancels coro on timeout
  │  wait_for(shield(coro), t=1.0)  │  ← Timeout fires, coro continues
  └─────────────────────────────────┘

  TaskGroup (Structured Concurrency):
  ┌─────────────────────────────┐
  │  async with TaskGroup():    │
  │    task1 = tg.create_task() │  ← If any task fails,
  │    task2 = tg.create_task() │    ALL others are cancelled
  │    task3 = tg.create_task() │    ExceptionGroup is raised
  └─────────────────────────────┘

  Cancellation Flow:
  task.cancel() ──► CancelledError raised in coroutine
                         │
                    try/except CancelledError
                         │
                    cleanup resources
                         │
                    raise  ← MUST re-raise!
```

## Exercises

### Exercise 1: Rate-limited batch processor

Build a function that processes items in batches with a concurrency limit:

```python
async def batch_process(
    items: list[str],
    max_concurrent: int = 3,
) -> list[dict]:
    """Process items with limited concurrency, return results in order."""
    # TODO: use asyncio.Semaphore to limit concurrent processing
    # Each item takes 0.01s to process
    # Return results in the SAME ORDER as input items
    ...

results = asyncio.run(batch_process(["a", "b", "c", "d", "e"]))
assert len(results) == 5
assert results[0]["item"] == "a"  # Order preserved
```

### Exercise 2: Timeout with retry

Build a function that retries an async operation with timeout:

```python
async def fetch_with_retry(
    url: str,
    timeout: float = 0.05,
    max_retries: int = 3,
) -> dict:
    """Fetch URL with timeout and retry logic."""
    # TODO: use asyncio.wait_for with timeout
    # On TimeoutError, retry up to max_retries times
    # On success, return the result
    # If all retries fail, raise TimeoutError
    ...
```

### Exercise 3: First successful with TaskGroup

Build a function that launches multiple async operations and returns the first successful result:

```python
async def first_success(coros: list) -> any:
    """Run coroutines concurrently, return first success, cancel the rest."""
    # TODO: use asyncio.wait with FIRST_COMPLETED
    # Check if the completed task succeeded
    # If so, cancel remaining and return result
    # If all fail, raise RuntimeError
    ...
```

## What's Next

In [Kata 28 -- Async Iterators](./28-async-iterators.md), we'll explore `async for`, `async generators`, and `__aiter__`/`__anext__` -- the async equivalents of Python's iteration protocol. You'll learn how to stream data asynchronously, build async pipelines, and implement the patterns used by async database drivers and web frameworks.

---

[prev: 26-async-await](./26-async-await.md) | [next: 28-async-iterators](./28-async-iterators.md)
