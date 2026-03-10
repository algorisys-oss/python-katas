"""
Kata 25 -- concurrent.futures
Run: python playground/skeletons/25_concurrent_futures.py

High-level concurrency with ThreadPoolExecutor and ProcessPoolExecutor.
Unified API for thread-based and process-based parallelism using Future objects.

IMPORTANT: All I/O is simulated with time.sleep(0.01-0.05) to complete within 5 seconds.
"""

import math
import time
from concurrent.futures import (
    ALL_COMPLETED,
    FIRST_COMPLETED,
    Future,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
    wait,
)


# ===========================================================================
# SECTION 1: ThreadPoolExecutor -- Parallel I/O
# ===========================================================================

def fetch_url(url: str) -> dict:
    """Simulate fetching a URL (I/O-bound work)."""
    time.sleep(0.02)  # Simulate network latency
    return {"url": url, "status": 200, "size": len(url) * 42}


def demo_thread_pool():
    """Parallel URL fetching with ThreadPoolExecutor."""
    urls = [f"https://api.example.com/users/{i}" for i in range(8)]

    print("  Fetching 8 URLs with 4 workers...")

    start = time.perf_counter()

    # TODO: use ThreadPoolExecutor with max_workers=4 to fetch all URLs in parallel
    # HINT: use executor.map(fetch_url, urls) to get results in submission order
    # HINT: wrap in a context manager: with ThreadPoolExecutor(...) as executor:
    results = []  # Replace with parallel fetch

    parallel_time = time.perf_counter() - start

    for r in results:
        print(f"  Fetched {r['url']} -> {r['status']} ({r['size']} bytes) in 0.02s")

    assert len(results) == 8
    assert all(r["status"] == 200 for r in results)
    assert results[0]["url"] == urls[0]
    assert results[7]["url"] == urls[7]

    print(f"  All 8 fetches completed (parallel with ThreadPool)")

    sequential_estimate = 8 * 0.02
    print(f"  Speedup: parallel is faster than sequential")
    assert parallel_time < sequential_estimate, "Parallel should be faster"


# ===========================================================================
# SECTION 2: ProcessPoolExecutor -- CPU-Bound Work
# ===========================================================================

def cpu_task(n: int) -> int:
    """Simulate CPU-bound work: compute n^3 with a tiny delay."""
    time.sleep(0.01)  # Simulate computation time
    return n ** 3


def demo_process_pool():
    """CPU-bound computation with ProcessPoolExecutor."""
    numbers = list(range(6))

    print("  Computing CPU-bound tasks with 2 workers...")

    # TODO: use ProcessPoolExecutor with max_workers=2 to compute cpu_task for each number
    # HINT: same API as ThreadPoolExecutor -- executor.map(cpu_task, numbers)
    results = []  # Replace with parallel computation

    for n, result in zip(numbers, results):
        print(f"  cpu_task({n}) = {result}")

    expected = [n ** 3 for n in numbers]
    assert results == expected, f"Expected {expected}, got {results}"

    print("  ProcessPoolExecutor handles CPU-bound work across processes.")


# ===========================================================================
# SECTION 3: submit() + as_completed() -- Progress Reporting
# ===========================================================================

def variable_task(task_id: int) -> dict:
    """Task with variable completion time."""
    delay = 0.01 + (task_id % 3) * 0.01  # 0.01s, 0.02s, or 0.03s
    time.sleep(delay)
    return {"task_id": task_id, "delay": delay, "result": task_id * 10}


def demo_as_completed():
    """Progress reporting with submit() and as_completed()."""
    task_count = 6

    print(f"  Submitting {task_count} tasks with variable latency...")

    collected_results = []

    # TODO: use ThreadPoolExecutor with max_workers=3
    # TODO: use executor.submit() to submit each task (not map!)
    # TODO: create a dict mapping future -> task_id for tracking
    # TODO: iterate with as_completed() to process results as they finish
    # HINT: future_to_id = {executor.submit(variable_task, i): i for i in range(task_count)}
    # HINT: for idx, future in enumerate(as_completed(future_to_id), 1):
    pass  # Replace with submit + as_completed logic

    assert len(collected_results) == task_count
    result_ids = {r["task_id"] for r in collected_results}
    assert result_ids == set(range(task_count))

    print(f"  All {task_count} tasks completed. Results collected out of order, "
          f"reported as finished.")


# ===========================================================================
# SECTION 4: Exception Handling
# ===========================================================================

def maybe_failing_task(x: int) -> int:
    """Task that fails for even inputs."""
    time.sleep(0.01)
    if x % 2 == 0 and x > 0:
        raise ValueError(f"Bad value: {x}")
    return x * 10


def demo_exception_handling():
    """Graceful error handling with futures."""
    print("  Submitting tasks (some will fail)...")

    successes = 0
    errors = 0

    # TODO: use ThreadPoolExecutor with max_workers=2
    # TODO: submit maybe_failing_task for i in range(5)
    # TODO: for each future, call .result(timeout=2.0) inside try/except
    # TODO: catch ValueError for failed tasks, count successes and errors
    # HINT: use a dict mapping future -> task_id to track which task failed
    pass  # Replace with exception handling logic

    assert successes == 3, f"Expected 3 successes, got {successes}"
    assert errors == 2, f"Expected 2 errors, got {errors}"

    print(f"  Handled {successes} successes and {errors} errors gracefully.")


# ===========================================================================
# SECTION 5: Timeouts and Cancellation
# ===========================================================================

def slow_task() -> str:
    """A task that takes too long."""
    time.sleep(0.5)
    return "slow result"


def fast_task() -> int:
    """A task that completes quickly."""
    time.sleep(0.01)
    return 42


def demo_timeouts():
    """Timeout handling and cancellation."""
    print("  Submitting slow + fast tasks...")

    # TODO: use ThreadPoolExecutor with max_workers=2
    # TODO: submit fast_task and slow_task
    # TODO: get fast_task result with timeout=1.0
    # TODO: try to get slow_task result with timeout=0.05 -- catch TimeoutError
    # HINT: future.result(timeout=0.05) raises TimeoutError if not done
    pass  # Replace with timeout logic

    print("  Timeouts prevent indefinite blocking.")


# ===========================================================================
# SECTION 6: wait() with FIRST_COMPLETED
# ===========================================================================

def timed_task(task_id: int) -> int:
    """Task with varying completion times."""
    delay = 0.01 + task_id * 0.01
    time.sleep(delay)
    return task_id


def demo_wait():
    """Using wait() for flexible completion control."""
    print("  Submitting 4 tasks...")

    # TODO: use ThreadPoolExecutor with max_workers=4
    # TODO: submit timed_task for i in range(4)
    # TODO: use wait(futures, return_when=FIRST_COMPLETED) to get first result
    # TODO: use wait(futures, return_when=ALL_COMPLETED) to get all results
    # HINT: wait() returns (done, not_done) -- two sets of futures
    pass  # Replace with wait logic

    print("  wait() gives fine-grained control over completion.")


# ===========================================================================
# BONUS: Future object introspection
# ===========================================================================

def demo_future_inspection():
    """Demonstrate Future object methods."""
    # TODO: submit a lambda that returns 99 with ThreadPoolExecutor
    # TODO: verify future.done() is True after getting result
    # TODO: verify future.cancelled() is False
    # TODO: verify future.exception() is None
    # HINT: with ThreadPoolExecutor(max_workers=1) as executor:

    # Callback demo
    callback_results = []

    def on_done(f: Future):
        callback_results.append(f.result())

    # TODO: submit a lambda that returns 77
    # TODO: add on_done as a callback with future.add_done_callback(on_done)
    # HINT: the callback fires when the future completes
    pass  # Replace with future inspection logic

    assert callback_results == [77], f"Callback should have captured 77, got {callback_results}"


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: ThreadPoolExecutor ---
    print("--- Section 1: ThreadPoolExecutor (Parallel I/O) ---")
    try:
        demo_thread_pool()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: ProcessPoolExecutor ---
    print("--- Section 2: ProcessPoolExecutor (CPU-Bound) ---")
    try:
        demo_process_pool()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: submit() + as_completed() ---
    print("--- Section 3: submit() + as_completed() (Progress Reporting) ---")
    try:
        demo_as_completed()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: Exception Handling ---
    print("--- Section 4: Exception Handling ---")
    try:
        demo_exception_handling()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: Timeouts and Cancellation ---
    print("--- Section 5: Timeouts and Cancellation ---")
    try:
        demo_timeouts()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 6: wait() with FIRST_COMPLETED ---
    print("--- Section 6: wait() with FIRST_COMPLETED ---")
    try:
        demo_wait()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Bonus: Future inspection ---
    try:
        demo_future_inspection()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (future inspection): {e}")

    # --- Summary ---
    print("--- Summary ---")
    print("concurrent.futures provides a unified high-level API for parallelism:")
    print("  - ThreadPoolExecutor: I/O-bound tasks (network, file, DB)")
    print("  - ProcessPoolExecutor: CPU-bound tasks (computation, parsing)")
    print("  - submit() + as_completed(): progress reporting, error handling")
    print("  - map(): simple ordered results (like built-in map)")
    print("  - Future: result(), exception(), cancel(), add_done_callback()")
    print("  - wait(): FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED")
    print("  - Context manager: always use 'with' for clean shutdown")
    print()
    print("Skeleton run complete. Implement the TODOs above to make all sections pass!")
