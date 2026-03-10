# Kata 26 -- Async/Await Fundamentals

[prev: 25-concurrent-futures](./25-concurrent-futures.md) | [next: 27-async-io-patterns](./27-async-io-patterns.md)

---

## What We're Building

A hands-on tour of Python's `asyncio` module -- the foundation for modern async programming. Instead of threads or processes, you'll use **coroutines** that cooperatively yield control on a single thread, letting one event loop handle thousands of concurrent I/O operations.

We'll build five practical demos:
1. **Async hello world** -- define and run your first coroutine with `async def` and `await`
2. **Gathering multiple coroutines** -- run coroutines concurrently with `asyncio.gather`
3. **Task creation** -- schedule coroutines as background tasks with `asyncio.create_task`
4. **Async queue** -- producer/consumer pipeline using `asyncio.Queue`
5. **Semaphore-limited concurrency** -- throttle parallelism with `asyncio.Semaphore`

This is the async counterpart to `concurrent.futures` (Kata 25). Where executors use threads/processes, asyncio uses coroutines -- lighter, faster, and the foundation for frameworks like FastAPI.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `async def` | Declares a coroutine function | Any function that needs to `await` |
| `await` | Suspends coroutine until result ready | Calling other coroutines or async I/O |
| `asyncio.run()` | Creates event loop, runs a coroutine | Top-level entry point for async code |
| `asyncio.gather()` | Run multiple coroutines concurrently | Fan-out: parallel HTTP requests, batch jobs |
| `asyncio.create_task()` | Schedule coroutine as a background task | Fire-and-forget or concurrent work within a coroutine |
| `asyncio.sleep()` | Non-blocking sleep (yields to event loop) | Simulating I/O, delays, rate limiting |
| `asyncio.Queue` | Async-safe FIFO queue | Producer/consumer patterns |
| `asyncio.Semaphore` | Limit concurrent coroutines | Rate limiting, connection pools |
| Event loop | Schedules and runs coroutines | The engine behind all async operations |
| `Task` | A wrapped coroutine tracked by the loop | Inspect status, cancel, await result |

## The Code

### Async Hello World

A coroutine is defined with `async def` and called with `await`. Calling a coroutine function doesn't execute it -- it returns a coroutine object. You must `await` it (or schedule it) to actually run the code.

```python
import asyncio

async def greet(name: str) -> str:
    """A simple coroutine."""
    await asyncio.sleep(0.01)  # Simulate async I/O
    return f"Hello, {name}!"

async def main():
    result = await greet("asyncio")
    print(result)  # Hello, asyncio!

asyncio.run(main())
```

Key points:
- `async def` creates a coroutine function -- calling it returns a coroutine object
- `await` suspends the current coroutine until the awaited coroutine completes
- `asyncio.run()` is the top-level entry point -- it creates an event loop, runs the coroutine, and cleans up
- `asyncio.sleep()` is the async equivalent of `time.sleep()` -- it yields control to the event loop instead of blocking the thread

### asyncio.gather() -- Concurrent Coroutines

`gather()` runs multiple coroutines concurrently and returns all results in the order they were passed:

```python
import asyncio

async def fetch_data(item_id: int) -> dict:
    """Simulate fetching data (I/O-bound)."""
    await asyncio.sleep(0.02)  # Simulate network latency
    return {"id": item_id, "data": f"result_{item_id}"}

async def main():
    # Run 5 fetches concurrently -- all start at once
    results = await asyncio.gather(
        fetch_data(1),
        fetch_data(2),
        fetch_data(3),
        fetch_data(4),
        fetch_data(5),
    )
    # Results are in submission order, not completion order
    for r in results:
        print(f"  {r['id']}: {r['data']}")

asyncio.run(main())
```

With `gather()`, all five coroutines run concurrently on the same thread. Total time is ~0.02s (the slowest), not ~0.10s (sum of all). The event loop switches between coroutines at each `await` point.

### asyncio.create_task() -- Background Tasks

`create_task()` schedules a coroutine to run in the background. Unlike `await` (which blocks the current coroutine), `create_task()` returns a `Task` object immediately:

```python
import asyncio

async def background_job(name: str, delay: float) -> str:
    """A background task."""
    await asyncio.sleep(delay)
    return f"{name} done"

async def main():
    # Schedule tasks -- they start running immediately
    task1 = asyncio.create_task(background_job("alpha", 0.03))
    task2 = asyncio.create_task(background_job("beta", 0.01))

    # Do other work while tasks run...
    await asyncio.sleep(0.01)

    # Now collect results
    result1 = await task1
    result2 = await task2
    print(f"  {result1}, {result2}")

asyncio.run(main())
```

Key differences from `gather()`:
- `create_task()` gives you a `Task` handle -- you can cancel it, check its status, or add callbacks
- Tasks start running at the next `await` point in the current coroutine
- `gather()` is better for "run these N things and wait for all"; `create_task()` is better for "start this in the background"

### asyncio.Queue -- Producer/Consumer

`asyncio.Queue` is the async equivalent of `queue.Queue`. It's the backbone of producer/consumer patterns in async code:

```python
import asyncio

async def producer(queue: asyncio.Queue, items: list[str]):
    """Produce items into the queue."""
    for item in items:
        await asyncio.sleep(0.01)  # Simulate producing work
        await queue.put(item)
    await queue.put(None)  # Sentinel to signal completion

async def consumer(queue: asyncio.Queue, results: list):
    """Consume items from the queue."""
    while True:
        item = await queue.get()
        if item is None:
            break
        await asyncio.sleep(0.01)  # Simulate processing
        results.append(f"processed:{item}")
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=5)
    results = []

    await asyncio.gather(
        producer(queue, ["a", "b", "c"]),
        consumer(queue, results),
    )
    print(f"  Results: {results}")

asyncio.run(main())
```

Key points:
- `queue.put()` blocks (suspends) if the queue is full (`maxsize`)
- `queue.get()` blocks if the queue is empty
- `queue.task_done()` signals that a consumed item has been processed
- Use a sentinel value (`None`) or `queue.join()` to coordinate shutdown

### asyncio.Semaphore -- Throttled Concurrency

A semaphore limits how many coroutines can run a critical section concurrently. This is essential for rate limiting API calls or database connections:

```python
import asyncio

async def limited_fetch(sem: asyncio.Semaphore, url: str) -> dict:
    """Fetch with concurrency limit."""
    async with sem:  # Only N coroutines enter at a time
        await asyncio.sleep(0.02)  # Simulate I/O
        return {"url": url, "status": 200}

async def main():
    sem = asyncio.Semaphore(3)  # Max 3 concurrent fetches
    urls = [f"https://api.example.com/{i}" for i in range(10)]

    # All 10 start, but only 3 run at a time
    results = await asyncio.gather(
        *[limited_fetch(sem, url) for url in urls]
    )
    print(f"  Fetched {len(results)} URLs with max 3 concurrent")

asyncio.run(main())
```

The `async with sem:` pattern acquires the semaphore (decrementing the counter) and releases it on exit. When the counter reaches 0, additional coroutines suspend until one releases the semaphore.

## Playground

Run the full demonstration:

```bash
python playground/26_async_await.py
```

```
--- Section 1: Async Hello World ---
  greeting = Hello, asyncio!
  multiple greetings: ['Hello, Alice!', 'Hello, Bob!', 'Hello, Charlie!']
  Coroutines are defined with async def and called with await.

--- Section 2: asyncio.gather() (Concurrent Coroutines) ---
  Gathering 6 fetches concurrently...
  Fetched item 0: result_0
  Fetched item 1: result_1
  Fetched item 2: result_2
  Fetched item 3: result_3
  Fetched item 4: result_4
  Fetched item 5: result_5
  All 6 fetches completed concurrently in ~0.02s (not ~0.12s)
  gather() returns results in submission order.

--- Section 3: asyncio.create_task() (Background Tasks) ---
  Created 4 background tasks...
  Task alpha completed: alpha done (0.03s)
  Task beta completed: beta done (0.01s)
  Task gamma completed: gamma done (0.02s)
  Task delta completed: delta done (0.01s)
  Tasks run concurrently; create_task() returns a handle for control.

--- Section 4: asyncio.Queue (Producer/Consumer) ---
  Starting producer/consumer pipeline...
  Produced: item_0
  Produced: item_1
  Consumed: item_0 -> processed:item_0
  Produced: item_2
  Consumed: item_1 -> processed:item_1
  Produced: item_3
  Consumed: item_2 -> processed:item_2
  Produced: item_4
  Consumed: item_3 -> processed:item_3
  Consumed: item_4 -> processed:item_4
  Pipeline complete: 5 items produced, 5 processed.

--- Section 5: asyncio.Semaphore (Throttled Concurrency) ---
  Fetching 10 URLs with max 3 concurrent...
  [sem] Fetching https://api.example.com/0 (active: 1/3)
  [sem] Fetching https://api.example.com/1 (active: 2/3)
  [sem] Fetching https://api.example.com/2 (active: 3/3)
  [sem] Done https://api.example.com/0
  [sem] Fetching https://api.example.com/3 (active: 3/3)
  [sem] Done https://api.example.com/1
  [sem] Fetching https://api.example.com/4 (active: 3/3)
  [sem] Done https://api.example.com/2
  [sem] Fetching https://api.example.com/5 (active: 3/3)
  ...
  All 10 URLs fetched with concurrency limited to 3.

--- Section 6: Error Handling with gather() ---
  gather(return_exceptions=True) captures errors without crashing:
  Task 0: result = 0
  Task 1: error = ValueError('Bad value: 1')
  Task 2: result = 20
  Task 3: error = ValueError('Bad value: 3')
  Task 4: result = 40
  Handled 3 successes and 2 errors.

--- Summary ---
asyncio provides cooperative concurrency on a single thread:
  - async def / await: define and call coroutines
  - asyncio.run(): top-level entry point
  - asyncio.gather(): run multiple coroutines concurrently
  - asyncio.create_task(): schedule background tasks
  - asyncio.Queue: async producer/consumer pipelines
  - asyncio.Semaphore: throttle concurrency (rate limiting)
  - Event loop: schedules coroutines at await points

All 6 sections passed. async/await fundamentals mastered!
```

## How It Works

```
THREAD-BASED (Katas 21-25)              ASYNC (asyncio)

  Thread()                               async def coroutine():
  ThreadPoolExecutor     ────────►         await asyncio.sleep()
  Process()                              asyncio.run(main())

  Multiple OS threads                    Single thread, event loop
  OS schedules threads                   Loop schedules coroutines
  Preemptive switching                   Cooperative switching (at await)
  Shared memory + locks                  No locks needed (single thread!)

  EVENT LOOP LIFECYCLE:

  asyncio.run(main())
       │
       ▼
  ┌─────────────────┐
  │   Event Loop     │
  │                  │
  │  ┌── main() ──┐ │     create_task() or gather()
  │  │  await ...  │─┼──►  schedules coroutines
  │  └────────────┘ │
  │  ┌── coro_1 ──┐ │     await suspends current,
  │  │  await ...  │─┼──►  loop picks next ready coroutine
  │  └────────────┘ │
  │  ┌── coro_2 ──┐ │     when I/O completes,
  │  │  await ...  │─┼──►  coroutine resumes
  │  └────────────┘ │
  └─────────────────┘
       │
       ▼
  Loop exits when main() returns

  GATHER vs CREATE_TASK:

  gather(a(), b(), c())     create_task(a())
       │                         │
       ▼                         ▼
  Run all, wait for all     Schedule a(), get Task handle
  Returns [result_a,        Continue current coroutine
           result_b,        await task later (or never)
           result_c]        task.cancel() to abort
```

## Exercises

### Exercise 1: Async retry

Build a function that retries a failing async operation:

```python
async def retry_async(coro_func, *args, max_retries: int = 3, delay: float = 0.01):
    """Retry a coroutine function up to max_retries times."""
    # TODO: call coro_func(*args) in a loop
    # If it raises, wait `delay` seconds and retry
    # After max_retries failures, raise the last exception
    ...

async def flaky_operation(x):
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network error")
    return x * 10

result = await retry_async(flaky_operation, 5, max_retries=5)
```

### Exercise 2: Async timeout wrapper

Build a function that wraps any coroutine with a timeout:

```python
async def with_timeout(coro, timeout: float):
    """Run a coroutine with a timeout. Raise TimeoutError if too slow."""
    # TODO: use asyncio.wait_for() or asyncio.timeout()
    # HINT: asyncio.wait_for(coro, timeout=timeout) raises asyncio.TimeoutError
    ...
```

### Exercise 3: Async worker pool

Build a worker pool using Queue and multiple consumers:

```python
async def worker_pool(tasks: list, num_workers: int = 3) -> list:
    """Process tasks using N concurrent workers via asyncio.Queue."""
    # TODO: create a Queue, spawn num_workers consumer tasks
    # Each worker pulls from queue, processes, puts result in results list
    # Use create_task() to spawn workers, gather() to wait for all
    ...
```

## What's Next

In [Kata 27 -- Async I/O Patterns](./27-async-io-patterns.md), we'll build on these fundamentals to tackle real-world async patterns: async context managers, async iterators, async generators, `async for`, `async with`, and combining asyncio with threads for legacy blocking code.

---

[prev: 25-concurrent-futures](./25-concurrent-futures.md) | [next: 27-async-io-patterns](./27-async-io-patterns.md)
