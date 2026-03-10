"""
Kata 26 -- Async/Await Fundamentals
Run: python playground/26_async_await.py

Cooperative concurrency with asyncio: coroutines, event loop, gather, tasks, queues, semaphores.
Single-threaded concurrency -- no locks needed, no GIL worries.

IMPORTANT: All I/O is simulated with asyncio.sleep(0.01-0.05) to complete within 5 seconds.
"""

import asyncio
import time


# ===========================================================================
# SECTION 1: Async Hello World
# ===========================================================================

async def greet(name: str) -> str:
    """A simple coroutine that simulates async work."""
    await asyncio.sleep(0.01)  # Simulate async I/O
    return f"Hello, {name}!"


async def demo_hello_world():
    """Basic async/await usage."""
    # Await a single coroutine
    result = await greet("asyncio")
    print(f"  greeting = {result}")
    assert result == "Hello, asyncio!"

    # Await multiple coroutines sequentially
    names = ["Alice", "Bob", "Charlie"]
    greetings = []
    for name in names:
        g = await greet(name)
        greetings.append(g)
    print(f"  multiple greetings: {greetings}")

    assert len(greetings) == 3
    assert greetings[0] == "Hello, Alice!"
    assert greetings[2] == "Hello, Charlie!"

    print("  Coroutines are defined with async def and called with await.")


# ===========================================================================
# SECTION 2: asyncio.gather() -- Concurrent Coroutines
# ===========================================================================

async def fetch_data(item_id: int) -> dict:
    """Simulate fetching data with async I/O."""
    await asyncio.sleep(0.02)  # Simulate network latency
    return {"id": item_id, "data": f"result_{item_id}"}


async def demo_gather():
    """Run multiple coroutines concurrently with gather()."""
    item_count = 6
    print(f"  Gathering {item_count} fetches concurrently...")

    start = time.perf_counter()

    # gather() runs all coroutines concurrently
    results = await asyncio.gather(
        *[fetch_data(i) for i in range(item_count)]
    )

    elapsed = time.perf_counter() - start

    for r in results:
        print(f"  Fetched item {r['id']}: {r['data']}")

    assert len(results) == item_count
    # Results are in submission order
    assert results[0]["id"] == 0
    assert results[5]["id"] == 5

    # Concurrent: should take ~0.02s, not ~0.12s
    sequential_estimate = item_count * 0.02
    assert elapsed < sequential_estimate, (
        f"Should be concurrent (~0.02s), took {elapsed:.3f}s"
    )

    print(f"  All {item_count} fetches completed concurrently in ~{elapsed:.2f}s "
          f"(not ~{sequential_estimate:.2f}s)")
    print("  gather() returns results in submission order.")


# ===========================================================================
# SECTION 3: asyncio.create_task() -- Background Tasks
# ===========================================================================

async def background_job(name: str, delay: float) -> str:
    """A background task that completes after a delay."""
    await asyncio.sleep(delay)
    return f"{name} done ({delay}s)"


async def demo_create_task():
    """Schedule background tasks with create_task()."""
    tasks_info = [
        ("alpha", 0.03),
        ("beta", 0.01),
        ("gamma", 0.02),
        ("delta", 0.01),
    ]

    print(f"  Created {len(tasks_info)} background tasks...")

    # create_task() schedules coroutines -- they start at the next await
    tasks = []
    for name, delay in tasks_info:
        task = asyncio.create_task(background_job(name, delay))
        tasks.append((name, task))

    # Await each task and collect results
    for name, task in tasks:
        result = await task
        print(f"  Task {name} completed: {result}")

    # All tasks should have completed
    for name, task in tasks:
        assert task.done()
        assert not task.cancelled()
        assert task.exception() is None

    print("  Tasks run concurrently; create_task() returns a handle for control.")


# ===========================================================================
# SECTION 4: asyncio.Queue -- Producer/Consumer
# ===========================================================================

async def producer(queue: asyncio.Queue, items: list[str], log: list):
    """Produce items into the async queue."""
    for item in items:
        await asyncio.sleep(0.01)  # Simulate producing work
        await queue.put(item)
        log.append(f"Produced: {item}")
        print(f"  Produced: {item}")
    # Signal completion
    await queue.put(None)


async def consumer(queue: asyncio.Queue, results: list, log: list):
    """Consume items from the async queue."""
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        await asyncio.sleep(0.01)  # Simulate processing
        processed = f"processed:{item}"
        results.append(processed)
        log.append(f"Consumed: {item} -> {processed}")
        print(f"  Consumed: {item} -> {processed}")
        queue.task_done()


async def demo_queue():
    """Producer/consumer pipeline with asyncio.Queue."""
    print("  Starting producer/consumer pipeline...")

    queue = asyncio.Queue(maxsize=3)
    items = [f"item_{i}" for i in range(5)]
    results = []
    log = []

    # Run producer and consumer concurrently
    await asyncio.gather(
        producer(queue, items, log),
        consumer(queue, results, log),
    )

    assert len(results) == 5
    assert results[0] == "processed:item_0"
    assert results[4] == "processed:item_4"

    print(f"  Pipeline complete: {len(items)} items produced, {len(results)} processed.")


# ===========================================================================
# SECTION 5: asyncio.Semaphore -- Throttled Concurrency
# ===========================================================================

async def limited_fetch(
    sem: asyncio.Semaphore,
    url: str,
    active_counter: dict,
    max_limit: int,
) -> dict:
    """Fetch with concurrency limited by semaphore."""
    async with sem:
        active_counter["count"] += 1
        current = active_counter["count"]
        print(f"  [sem] Fetching {url} (active: {current}/{max_limit})")
        assert current <= max_limit, (
            f"Semaphore violated: {current} active > {max_limit} limit"
        )

        await asyncio.sleep(0.02)  # Simulate I/O

        active_counter["count"] -= 1
        print(f"  [sem] Done {url}")
        return {"url": url, "status": 200}


async def demo_semaphore():
    """Throttle concurrency with asyncio.Semaphore."""
    max_concurrent = 3
    urls = [f"https://api.example.com/{i}" for i in range(10)]

    print(f"  Fetching {len(urls)} URLs with max {max_concurrent} concurrent...")

    sem = asyncio.Semaphore(max_concurrent)
    active_counter = {"count": 0}

    results = await asyncio.gather(
        *[limited_fetch(sem, url, active_counter, max_concurrent) for url in urls]
    )

    assert len(results) == 10
    assert all(r["status"] == 200 for r in results)

    print(f"  All {len(urls)} URLs fetched with concurrency limited to {max_concurrent}.")


# ===========================================================================
# SECTION 6: Error Handling with gather()
# ===========================================================================

async def maybe_failing(x: int) -> int:
    """Coroutine that fails for odd inputs."""
    await asyncio.sleep(0.01)
    if x % 2 == 1:
        raise ValueError(f"Bad value: {x}")
    return x * 10


async def demo_error_handling():
    """Error handling with gather(return_exceptions=True)."""
    # return_exceptions=True captures exceptions as results instead of raising
    results = await asyncio.gather(
        *[maybe_failing(i) for i in range(5)],
        return_exceptions=True,
    )

    print("  gather(return_exceptions=True) captures errors without crashing:")

    successes = 0
    errors = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  Task {i}: error = {result!r}")
            errors += 1
        else:
            print(f"  Task {i}: result = {result}")
            successes += 1

    assert successes == 3  # 0, 2, 4 succeed
    assert errors == 2      # 1, 3 fail
    assert results[0] == 0
    assert isinstance(results[1], ValueError)
    assert results[2] == 20

    print(f"  Handled {successes} successes and {errors} errors.")


# ===========================================================================
# MAIN
# ===========================================================================

async def main():
    # --- Section 1: Async Hello World ---
    print("--- Section 1: Async Hello World ---")
    await demo_hello_world()
    print()

    # --- Section 2: asyncio.gather() ---
    print("--- Section 2: asyncio.gather() (Concurrent Coroutines) ---")
    await demo_gather()
    print()

    # --- Section 3: asyncio.create_task() ---
    print("--- Section 3: asyncio.create_task() (Background Tasks) ---")
    await demo_create_task()
    print()

    # --- Section 4: asyncio.Queue ---
    print("--- Section 4: asyncio.Queue (Producer/Consumer) ---")
    await demo_queue()
    print()

    # --- Section 5: asyncio.Semaphore ---
    print("--- Section 5: asyncio.Semaphore (Throttled Concurrency) ---")
    await demo_semaphore()
    print()

    # --- Section 6: Error Handling ---
    print("--- Section 6: Error Handling with gather() ---")
    await demo_error_handling()
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("asyncio provides cooperative concurrency on a single thread:")
    print("  - async def / await: define and call coroutines")
    print("  - asyncio.run(): top-level entry point")
    print("  - asyncio.gather(): run multiple coroutines concurrently")
    print("  - asyncio.create_task(): schedule background tasks")
    print("  - asyncio.Queue: async producer/consumer pipelines")
    print("  - asyncio.Semaphore: throttle concurrency (rate limiting)")
    print("  - Event loop: schedules coroutines at await points")
    print()
    print("All 6 sections passed. async/await fundamentals mastered!")


if __name__ == "__main__":
    asyncio.run(main())
