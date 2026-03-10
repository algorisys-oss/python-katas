"""
Kata 27 -- Async I/O Patterns
Run: python playground/27_async_io_patterns.py

Advanced async patterns: fan-out/fan-in, semaphore-limited concurrency,
timeout with fallback, asyncio.shield, TaskGroup, and graceful cancellation.

IMPORTANT: All I/O is simulated with asyncio.sleep() to complete within 5 seconds.
"""

import asyncio
import time


# ===========================================================================
# SECTION 1: Fan-Out/Fan-In
# ===========================================================================

async def fetch_user(user_id: int) -> dict:
    """Simulate fetching a user from an API."""
    await asyncio.sleep(0.02)  # Simulate network I/O
    return {"id": user_id, "name": f"User_{user_id}", "active": user_id % 3 != 0}


async def demo_fan_out_fan_in():
    """Dispatch many concurrent tasks, collect all results."""
    user_ids = [1, 2, 3, 4, 5, 6, 7, 8]

    print("  Fetching 8 users concurrently...")

    start = time.perf_counter()

    # Fan-out: launch all fetches concurrently
    # Fan-in: gather collects results in submission order
    results = await asyncio.gather(*(fetch_user(uid) for uid in user_ids))

    elapsed = time.perf_counter() - start

    print(f"  Fan-out: launched {len(user_ids)} tasks")
    print(f"  Fan-in: collected {len(results)} results in ~{elapsed:.2f}s")

    active_users = [u for u in results if u["active"]]
    print(f"  Active users: {len(active_users)} out of {len(results)}")

    assert len(results) == 8
    assert results[0]["id"] == 1
    assert results[7]["id"] == 8
    assert len(active_users) == 6  # IDs 1,2,4,5,7,8 active (3,6 inactive)
    # Should complete in ~0.02s, not 0.16s
    assert elapsed < 0.15, f"Should be concurrent, took {elapsed:.2f}s"

    print("  Fan-out/fan-in complete.")


# ===========================================================================
# SECTION 2: Semaphore-Limited Concurrency
# ===========================================================================

async def rate_limited_fetch(
    sem: asyncio.Semaphore,
    url: str,
    tracker: dict,
) -> dict:
    """Fetch a URL with semaphore-limited concurrency."""
    async with sem:
        tracker["current"] += 1
        tracker["max_seen"] = max(tracker["max_seen"], tracker["current"])
        await asyncio.sleep(0.02)  # Simulate API call
        tracker["current"] -= 1
        return {"url": url, "status": 200}


async def demo_semaphore():
    """Rate-limit concurrent operations with asyncio.Semaphore."""
    sem = asyncio.Semaphore(3)  # Max 3 concurrent requests
    urls = [f"https://api.example.com/item/{i}" for i in range(10)]
    tracker = {"current": 0, "max_seen": 0}

    print("  Fetching 10 URLs with max 3 concurrent...")

    results = await asyncio.gather(
        *(rate_limited_fetch(sem, url, tracker) for url in urls)
    )

    print(f"  All {len(results)} fetches completed.")
    print(f"  Max concurrent observed: {tracker['max_seen']}")

    assert len(results) == 10
    assert all(r["status"] == 200 for r in results)
    assert tracker["max_seen"] <= 3, f"Semaphore violated: {tracker['max_seen']} concurrent"

    print("  Semaphore enforces concurrency limit.")


# ===========================================================================
# SECTION 3: Timeout with Fallback
# ===========================================================================

async def fast_api_call() -> str:
    """An API call that completes quickly."""
    await asyncio.sleep(0.01)
    return "fast_result"


async def slow_api_call() -> str:
    """An API call that takes too long."""
    await asyncio.sleep(1.0)
    return "slow_result"


async def fetch_with_timeout(coro, timeout: float, fallback: str) -> str:
    """Wrap a coroutine with a timeout, returning fallback on timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return fallback


async def demo_timeout():
    """Timeout handling with asyncio.wait_for and fallback values."""
    # Fast call should succeed
    result1 = await fetch_with_timeout(fast_api_call(), timeout=0.5, fallback="default_value")
    print(f"  Fast call: result = {result1}")
    assert result1 == "fast_result"

    # Slow call should time out and use fallback
    result2 = await fetch_with_timeout(slow_api_call(), timeout=0.05, fallback="default_value")
    print(f"  Slow call: timed out, using fallback = {result2}")
    assert result2 == "default_value"

    print("  Timeout with fallback complete.")


# ===========================================================================
# SECTION 4: asyncio.shield
# ===========================================================================

async def critical_save(data: str, tracker: dict) -> str:
    """A critical operation that must not be interrupted."""
    await asyncio.sleep(0.03)  # Simulate DB write
    tracker["saved"] = True
    return f"saved:{data}"


async def demo_shield():
    """Protect critical operations from cancellation with asyncio.shield."""
    tracker = {"saved": False}

    # Create the save coroutine
    save_coro = critical_save("critical_data", tracker)

    # Shield it -- timeout fires but the save continues
    try:
        result = await asyncio.wait_for(
            asyncio.shield(save_coro),
            timeout=0.01,
        )
        # If we get here, the save completed before timeout
        print(f"  Save completed before timeout: {result}")
    except asyncio.TimeoutError:
        print("  Shielded save continues despite timeout.")
        # Give the shielded task time to complete
        await asyncio.sleep(0.05)

    assert tracker["saved"], "Shielded save should have completed"
    print(f"  Save result: saved:critical_data")

    print("  Shield protects critical operations from cancellation.")


# ===========================================================================
# SECTION 5: TaskGroup (Structured Concurrency) -- Python 3.11+
# ===========================================================================

async def fetch_source(source: str) -> dict:
    """Fetch data from a named source."""
    await asyncio.sleep(0.02)
    if source == "bad_source":
        raise ValueError(f"Source '{source}' is unavailable")
    return {"source": source, "data": f"data_from_{source}"}


async def demo_taskgroup():
    """Structured concurrency with asyncio.TaskGroup."""
    # --- Success case: all tasks complete ---
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for source in ["db", "cache", "api"]:
            task = tg.create_task(fetch_source(source))
            tasks.append(task)

    # After the async with block, all tasks are done
    results = [t.result() for t in tasks]
    sources = [r["source"] for r in results]
    print(f"  All tasks succeeded: {sources}")

    assert len(results) == 3
    assert sources == ["db", "cache", "api"]

    # --- Failure case: one task fails, others are cancelled ---
    error_count = 0
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fetch_source("db"))
            tg.create_task(fetch_source("bad_source"))  # This will fail
            tg.create_task(fetch_source("api"))
    except* ValueError as eg:
        error_count = len(eg.exceptions)
        print(f"  TaskGroup with failure: caught {error_count} error(s)")
        for exc in eg.exceptions:
            print(f"  Error: {exc}")

    assert error_count == 1

    print("  TaskGroup provides automatic cleanup on failure.")


# ===========================================================================
# SECTION 6: Graceful Cancellation
# ===========================================================================

async def long_running_worker(name: str, tracker: dict):
    """A worker that handles cancellation gracefully."""
    try:
        iteration = 0
        while True:
            await asyncio.sleep(0.01)
            iteration += 1
            tracker["iterations"] = iteration
    except asyncio.CancelledError:
        print(f"  {name}: cleaning up resources...")
        tracker["cleaned_up"] = True
        await asyncio.sleep(0.005)  # Simulate cleanup I/O
        raise  # Always re-raise CancelledError!


async def demo_cancellation():
    """Graceful task cancellation with cleanup."""
    tracker = {"iterations": 0, "cleaned_up": False}

    task = asyncio.create_task(long_running_worker("worker-1", tracker))

    # Let it run for a bit
    await asyncio.sleep(0.05)

    print(f"  Worker ran {tracker['iterations']} iterations before cancellation.")

    # Cancel the task
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass

    assert tracker["iterations"] >= 3, f"Worker should have run, got {tracker['iterations']} iterations"
    assert tracker["cleaned_up"], "Worker should have cleaned up"

    print("  Task cancelled cleanly.")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

async def main():
    # --- Section 1: Fan-Out/Fan-In ---
    print("--- Section 1: Fan-Out/Fan-In ---")
    await demo_fan_out_fan_in()
    print()

    # --- Section 2: Semaphore-Limited Concurrency ---
    print("--- Section 2: Semaphore-Limited Concurrency ---")
    await demo_semaphore()
    print()

    # --- Section 3: Timeout with Fallback ---
    print("--- Section 3: Timeout with Fallback ---")
    await demo_timeout()
    print()

    # --- Section 4: asyncio.shield ---
    print("--- Section 4: asyncio.shield ---")
    await demo_shield()
    print()

    # --- Section 5: TaskGroup (Structured Concurrency) ---
    print("--- Section 5: TaskGroup (Structured Concurrency) ---")
    await demo_taskgroup()
    print()

    # --- Section 6: Graceful Cancellation ---
    print("--- Section 6: Graceful Cancellation ---")
    await demo_cancellation()
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Async I/O patterns for production code:")
    print("  - Fan-out/fan-in: dispatch many, collect all")
    print("  - Semaphore: limit concurrent operations")
    print("  - wait_for: timeout with automatic cancellation")
    print("  - shield: protect critical work from cancellation")
    print("  - TaskGroup: structured concurrency with auto-cleanup")
    print("  - Cancellation: catch CancelledError, cleanup, re-raise")
    print()
    print("All 6 sections passed. Async I/O patterns mastered!")


if __name__ == "__main__":
    asyncio.run(main())
