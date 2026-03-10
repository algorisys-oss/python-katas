"""
Kata 25 -- concurrent.futures
Run: python playground/25_concurrent_futures.py

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
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_url, urls))
    parallel_time = time.perf_counter() - start

    for r in results:
        print(f"  Fetched {r['url']} -> {r['status']} ({r['size']} bytes) in 0.02s")

    assert len(results) == 8
    assert all(r["status"] == 200 for r in results)
    # Results are in submission order (map guarantees this)
    assert results[0]["url"] == urls[0]
    assert results[7]["url"] == urls[7]

    print(f"  All 8 fetches completed (parallel with ThreadPool)")

    # Sequential would take ~0.16s, parallel ~0.04s
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

    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(cpu_task, numbers))

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

    with ThreadPoolExecutor(max_workers=3) as executor:
        # submit() returns a Future for each task
        future_to_id = {
            executor.submit(variable_task, i): i
            for i in range(task_count)
        }

        # as_completed() yields futures as they finish (fastest first)
        for idx, future in enumerate(as_completed(future_to_id), 1):
            task_id = future_to_id[future]
            result = future.result()
            collected_results.append(result)
            print(f"  [Progress] Completed task {task_id} -> "
                  f"result: {result['result']} ({idx}/{task_count})")

    assert len(collected_results) == task_count
    # All results should be present (though order may vary)
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

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(maybe_failing_task, i): i
            for i in range(5)
        }

        # Process in submission order for deterministic output
        for i in range(5):
            # Find the future for this task_id
            future = [f for f, tid in futures.items() if tid == i][0]
            try:
                result = future.result(timeout=2.0)
                print(f"  Task {i}: result = {result}")
                successes += 1
            except ValueError as e:
                print(f"  Task {i}: error = {e}")
                errors += 1

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

    with ThreadPoolExecutor(max_workers=2) as executor:
        fast_future = executor.submit(fast_task)
        slow_future = executor.submit(slow_task)

        # Fast task should complete quickly
        fast_result = fast_future.result(timeout=1.0)
        print(f"  Fast task completed: {fast_result}")
        assert fast_result == 42

        # Slow task should time out
        try:
            slow_future.result(timeout=0.05)
            assert False, "Should have timed out"
        except TimeoutError:
            print("  Slow task: timed out (expected)")
            # Note: timeout doesn't cancel the task, it just stops waiting
            # The task continues running in the background

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

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(timed_task, i) for i in range(4)]

        # Wait for the first one to complete
        done, not_done = wait(futures, return_when=FIRST_COMPLETED)
        print(f"  First completed: got {len(done)} done, {len(not_done)} still pending")
        assert len(done) >= 1
        assert len(done) + len(not_done) == 4

        # Now wait for everything
        done, not_done = wait(futures, return_when=ALL_COMPLETED)
        print(f"  After waiting for rest: all {len(done)} done")
        assert len(done) == 4
        assert len(not_done) == 0

        # Verify all results
        results = {f.result() for f in done}
        assert results == {0, 1, 2, 3}

    print("  wait() gives fine-grained control over completion.")


# ===========================================================================
# BONUS: Future object introspection
# ===========================================================================

def demo_future_inspection():
    """Demonstrate Future object methods."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: 99)
        result = future.result(timeout=1.0)

        # After completion
        assert future.done() is True
        assert future.cancelled() is False
        assert future.exception() is None
        assert result == 99

    # Callback demo
    callback_results = []

    def on_done(f: Future):
        callback_results.append(f.result())

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: 77)
        future.add_done_callback(on_done)

    # After executor shutdown, callback should have fired
    assert callback_results == [77], f"Callback should have captured 77, got {callback_results}"


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: ThreadPoolExecutor ---
    print("--- Section 1: ThreadPoolExecutor (Parallel I/O) ---")
    demo_thread_pool()
    print()

    # --- Section 2: ProcessPoolExecutor ---
    print("--- Section 2: ProcessPoolExecutor (CPU-Bound) ---")
    demo_process_pool()
    print()

    # --- Section 3: submit() + as_completed() ---
    print("--- Section 3: submit() + as_completed() (Progress Reporting) ---")
    demo_as_completed()
    print()

    # --- Section 4: Exception Handling ---
    print("--- Section 4: Exception Handling ---")
    demo_exception_handling()
    print()

    # --- Section 5: Timeouts and Cancellation ---
    print("--- Section 5: Timeouts and Cancellation ---")
    demo_timeouts()
    print()

    # --- Section 6: wait() with FIRST_COMPLETED ---
    print("--- Section 6: wait() with FIRST_COMPLETED ---")
    demo_wait()
    print()

    # --- Bonus: Future inspection ---
    demo_future_inspection()

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
    print("All 6 sections passed. concurrent.futures mastered!")
