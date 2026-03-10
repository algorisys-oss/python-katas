"""
Kata 26 -- Async/Await Fundamentals
Run: python playground/skeletons/26_async_await.py

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
    # TODO: await asyncio.sleep(0.01) to simulate I/O
    # TODO: return f"Hello, {name}!"
    # HINT: use 'await' before asyncio.sleep()
    pass


async def demo_hello_world():
    """Basic async/await usage."""
    # TODO: await the greet() coroutine with "asyncio" and store in result
    # HINT: result = await greet("asyncio")
    result = None  # Replace with await call

    print(f"  greeting = {result}")
    assert result == "Hello, asyncio!"

    # TODO: await greet() for each name in ["Alice", "Bob", "Charlie"]
    # HINT: loop through names, await greet(name) for each, collect in a list
    names = ["Alice", "Bob", "Charlie"]
    greetings = []  # Replace with sequential await loop

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

    # TODO: use asyncio.gather() to run fetch_data(i) for i in range(item_count) concurrently
    # HINT: results = await asyncio.gather(*[fetch_data(i) for i in range(item_count)])
    results = []  # Replace with gather call

    elapsed = time.perf_counter() - start

    for r in results:
        print(f"  Fetched item {r['id']}: {r['data']}")

    assert len(results) == item_count
    assert results[0]["id"] == 0
    assert results[5]["id"] == 5

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

    # TODO: use asyncio.create_task() to schedule each background_job
    # TODO: collect (name, task) pairs in a list
    # TODO: await each task and print the result
    # HINT: task = asyncio.create_task(background_job(name, delay))
    # HINT: result = await task
    tasks = []  # Replace with create_task logic

    for name, task in tasks:
        result = await task
        print(f"  Task {name} completed: {result}")

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
    # TODO: for each item, sleep 0.01s, put item in queue, log it
    # TODO: put None as sentinel to signal completion
    # HINT: await queue.put(item)
    pass


async def consumer(queue: asyncio.Queue, results: list, log: list):
    """Consume items from the async queue."""
    # TODO: loop forever, get items from queue
    # TODO: if item is None, call queue.task_done() and break
    # TODO: otherwise, sleep 0.01s, append "processed:{item}" to results, log it
    # HINT: item = await queue.get()
    # HINT: queue.task_done() signals the item is processed
    pass


async def demo_queue():
    """Producer/consumer pipeline with asyncio.Queue."""
    print("  Starting producer/consumer pipeline...")

    queue = asyncio.Queue(maxsize=3)
    items = [f"item_{i}" for i in range(5)]
    results = []
    log = []

    # TODO: use asyncio.gather() to run producer and consumer concurrently
    # HINT: await asyncio.gather(producer(...), consumer(...))
    pass  # Replace with gather call

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
    # TODO: use 'async with sem:' to acquire the semaphore
    # TODO: inside the block, increment active_counter["count"]
    # TODO: assert active count <= max_limit
    # TODO: await asyncio.sleep(0.02) to simulate I/O
    # TODO: decrement active_counter["count"]
    # TODO: return {"url": url, "status": 200}
    # HINT: async with sem:  (this acquires and auto-releases)
    pass


async def demo_semaphore():
    """Throttle concurrency with asyncio.Semaphore."""
    max_concurrent = 3
    urls = [f"https://api.example.com/{i}" for i in range(10)]

    print(f"  Fetching {len(urls)} URLs with max {max_concurrent} concurrent...")

    # TODO: create a Semaphore with max_concurrent
    # TODO: use asyncio.gather() with limited_fetch for each URL
    # HINT: sem = asyncio.Semaphore(max_concurrent)
    # HINT: results = await asyncio.gather(*[limited_fetch(sem, url, ...) for url in urls])
    results = []  # Replace with semaphore + gather logic

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
    # TODO: use asyncio.gather() with return_exceptions=True
    # TODO: this captures exceptions as results instead of raising them
    # HINT: results = await asyncio.gather(*[...], return_exceptions=True)
    results = []  # Replace with gather call

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
    try:
        await demo_hello_world()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: asyncio.gather() ---
    print("--- Section 2: asyncio.gather() (Concurrent Coroutines) ---")
    try:
        await demo_gather()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: asyncio.create_task() ---
    print("--- Section 3: asyncio.create_task() (Background Tasks) ---")
    try:
        await demo_create_task()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: asyncio.Queue ---
    print("--- Section 4: asyncio.Queue (Producer/Consumer) ---")
    try:
        await demo_queue()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: asyncio.Semaphore ---
    print("--- Section 5: asyncio.Semaphore (Throttled Concurrency) ---")
    try:
        await demo_semaphore()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 6: Error Handling ---
    print("--- Section 6: Error Handling with gather() ---")
    try:
        await demo_error_handling()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
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
    print("Skeleton run complete. Implement the TODOs above to make all sections pass!")


if __name__ == "__main__":
    asyncio.run(main())
