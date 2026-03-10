"""
Kata 30 -- Free-Threaded Python
Run: python playground/skeletons/30_free_threaded_python.py

Explore PEP 703 and free-threaded Python (no-GIL builds).
Detect GIL status, demonstrate thread safety implications, and compare
CPU-bound threading performance with and without the GIL.

IMPORTANT: Works on standard CPython (with GIL). Uses feature detection throughout.
All demos complete within 5 seconds.
"""

import queue
import sys
import sysconfig
import threading
import time
from concurrent.futures import ThreadPoolExecutor


# ===========================================================================
# SECTION 1: GIL Detection
# ===========================================================================

def detect_gil_status() -> dict:
    """Detect GIL status using multiple methods.

    Works on any Python version -- uses feature detection, never crashes.

    Should return a dict with keys:
    - has_is_gil_enabled: bool (whether sys._is_gil_enabled exists)
    - gil_enabled: bool (True if GIL is active)
    - build_gil_disabled: bool (build-time flag)
    - is_free_threaded: bool (True if running without GIL)
    - python_version: str (e.g., "3.12.0")
    - supports_free_threading_api: bool (True if Python >= 3.13)
    """
    info = {}

    # TODO: Check if sys._is_gil_enabled exists using hasattr()
    # HINT: has_gil_check = hasattr(sys, "_is_gil_enabled")
    # TODO: If it exists, call it to get the runtime GIL status
    # TODO: If it doesn't exist, assume GIL is enabled (pre-3.13)

    # TODO: Check build configuration with sysconfig.get_config_var("Py_GIL_DISABLED")
    # HINT: The flag is truthy if the build was compiled without GIL support

    # TODO: Determine if this is a free-threaded build with GIL actually off
    # HINT: is_free_threaded = has_gil_check and not gil_enabled

    # TODO: Add Python version info and check if version >= 3.13

    return info


def demo_gil_detection():
    """Detect and report GIL status."""
    info = detect_gil_status()

    print(f"  Python version: {info['python_version']}")
    print(f"  Has sys._is_gil_enabled: {info['has_is_gil_enabled']}")
    print(f"  GIL is enabled: {info['gil_enabled']}")
    print(f"  Build GIL disabled flag: {info['build_gil_disabled']}")
    print(f"  Free-threaded build: {'Yes' if info['is_free_threaded'] else 'No'}")
    print(f"  Supports free-threading API: "
          f"{'Yes' if info['supports_free_threading_api'] else 'No (requires 3.13+)'}")

    if info["is_free_threaded"]:
        print("  Conclusion: Running FREE-THREADED Python -- GIL is disabled!")
    elif info["has_is_gil_enabled"] and info["gil_enabled"]:
        print("  Conclusion: Free-threaded build available but GIL is currently enabled.")
    else:
        print("  Conclusion: Running standard CPython with GIL enabled.")

    # Assertions -- these always pass regardless of build
    assert isinstance(info["gil_enabled"], bool)
    assert isinstance(info["python_version"], str)
    assert isinstance(info["is_free_threaded"], bool)


# ===========================================================================
# SECTION 2: Thread Safety Demonstration
# ===========================================================================

def demo_thread_safety():
    """Show why proper synchronization matters, with or without GIL."""
    num_threads = 4
    increments_per_thread = 100_000

    # --- Unsafe counter (no lock) ---
    unsafe_counter = [0]  # Use list to allow mutation in nested function

    def increment_unsafe():
        for _ in range(increments_per_thread):
            unsafe_counter[0] += 1

    print(f"  Running unsafe counter with {num_threads} threads "
          f"({increments_per_thread} increments each)...")

    # TODO: create num_threads threads, each running increment_unsafe
    # TODO: start all threads, then join all threads
    # HINT: threads = [threading.Thread(target=increment_unsafe) for _ in range(num_threads)]
    pass  # Replace with thread creation, start, and join

    expected = num_threads * increments_per_thread
    unsafe_result = unsafe_counter[0]
    print(f"  Unsafe counter: expected {expected}, got {unsafe_result}")

    if unsafe_result == expected:
        print("  (With GIL, unsafe counter often appears correct -- "
              "the GIL masks the bug)")
    else:
        print(f"  (Race condition detected! Lost {expected - unsafe_result} increments)")

    # --- Safe counter (with lock) ---
    safe_counter = [0]
    lock = threading.Lock()

    def increment_safe():
        for _ in range(increments_per_thread):
            # TODO: acquire lock, increment safe_counter[0], release lock
            # HINT: use 'with lock:' for automatic acquire/release
            pass  # Replace with locked increment

    print(f"  Running safe counter with {num_threads} threads "
          f"({increments_per_thread} increments each)...")

    # TODO: create, start, and join threads running increment_safe
    pass  # Replace with thread creation, start, and join

    safe_result = safe_counter[0]
    print(f"  Safe counter: expected {expected}, got {safe_result}")
    assert safe_result == expected, f"Safe counter should be {expected}, got {safe_result}"
    print("  Safe counter is always correct, with or without GIL.")


# ===========================================================================
# SECTION 3: CPU-Bound Threading vs Sequential
# ===========================================================================

def cpu_work(n: int) -> int:
    """Pure CPU work: sum of squares up to n."""
    total = 0
    for i in range(n):
        total += i * i
    return total


def demo_cpu_bound_comparison():
    """Compare sequential vs threaded performance for CPU-bound work."""
    work_size = 200_000
    num_tasks = 4

    # --- Sequential ---
    # TODO: time how long it takes to run cpu_work(work_size) num_tasks times sequentially
    # HINT: use time.perf_counter() before and after
    # HINT: sequential_results = [cpu_work(work_size) for _ in range(num_tasks)]
    sequential_time = 0  # Replace with timing
    sequential_results = []  # Replace with results

    # --- Threaded ---
    threaded_results = [None] * num_tasks

    def worker(idx):
        threaded_results[idx] = cpu_work(work_size)

    # TODO: time how long it takes to run cpu_work in num_tasks threads
    # HINT: create threads with target=worker, args=(i,)
    # HINT: start all, then join all
    threaded_time = 0  # Replace with timing

    print(f"  Work size: {work_size}, Tasks: {num_tasks}")
    print(f"  Sequential: {sequential_time:.4f}s")
    print(f"  Threaded:   {threaded_time:.4f}s")

    ratio = threaded_time / sequential_time if sequential_time > 0 else 0
    print(f"  Ratio (threaded/sequential): {ratio:.2f}x")

    # Verify correctness
    assert all(r == sequential_results[0] for r in sequential_results)
    assert all(r == sequential_results[0] for r in threaded_results)

    info = detect_gil_status()
    if info["is_free_threaded"]:
        print("  Without GIL: threaded CPU work could be up to "
              f"{num_tasks}x faster (true parallelism).")
    else:
        print("  With GIL: threaded CPU work is typically slower than sequential.")
        print("  Without GIL: threaded CPU work could be up to "
              f"{num_tasks}x faster (N = core count).")


# ===========================================================================
# SECTION 4: Thread-Safe Data Structures
# ===========================================================================

def demo_thread_safe_structures():
    """Demonstrate thread-safe patterns for shared mutable data."""
    num_threads = 4
    items_per_thread = 1_000

    # --- Thread-safe list with lock ---
    safe_list = []
    list_lock = threading.Lock()

    def append_to_list(thread_id: int):
        for i in range(items_per_thread):
            # TODO: acquire list_lock, then append (thread_id, i) to safe_list
            # HINT: with list_lock: safe_list.append(...)
            pass  # Replace with locked append

    # TODO: create, start, and join num_threads threads running append_to_list
    pass  # Replace with thread creation

    expected_count = num_threads * items_per_thread
    print(f"  Thread-safe list append: {len(safe_list)} items "
          f"(expected {expected_count})")
    assert len(safe_list) == expected_count

    # --- Thread-safe dict with lock ---
    safe_dict = {}
    dict_lock = threading.Lock()

    def update_dict(thread_id: int):
        for i in range(items_per_thread):
            key = f"t{thread_id}_item{i}"
            # TODO: acquire dict_lock, then set safe_dict[key] = thread_id * 1000 + i
            pass  # Replace with locked dict update

    # TODO: create, start, and join num_threads threads running update_dict
    pass  # Replace with thread creation

    print(f"  Thread-safe dict update: {len(safe_dict)} entries "
          f"(expected {expected_count})")
    assert len(safe_dict) == expected_count

    print("  Always protect shared mutable data with locks.")


# ===========================================================================
# SECTION 5: Migration Readiness Check
# ===========================================================================

def demo_migration_check():
    """Verify that common concurrency patterns work correctly."""

    # Test 1: threading.Lock
    lock = threading.Lock()
    value = [0]

    def locked_increment():
        for _ in range(1000):
            # TODO: use lock to safely increment value[0]
            pass  # Replace with locked increment

    # TODO: create 4 threads running locked_increment, start and join them
    pass  # Replace with thread creation
    assert value[0] == 4000
    print("  [PASS] threading.Lock works correctly")

    # Test 2: queue.Queue
    q = queue.Queue()
    results = []

    def producer():
        # TODO: put integers 0-99 into the queue, then put None as sentinel
        pass  # Replace with producer logic

    def consumer():
        # TODO: get items from queue until None sentinel, append to results
        pass  # Replace with consumer logic

    # TODO: create producer and consumer threads, start and join them
    pass  # Replace with thread creation
    assert len(results) == 100
    print("  [PASS] queue.Queue is thread-safe")

    # Test 3: ThreadPoolExecutor
    # TODO: use ThreadPoolExecutor to map lambda x: x * 2 over range(10)
    # HINT: with ThreadPoolExecutor(max_workers=2) as executor:
    #           futures_results = list(executor.map(lambda x: x * 2, range(10)))
    futures_results = []  # Replace with executor.map result
    assert futures_results == [x * 2 for x in range(10)]
    print("  [PASS] ThreadPoolExecutor works correctly")

    # Test 4: Immutable data
    immutable_tuple = (1, 2, 3)
    immutable_frozenset = frozenset({4, 5, 6})
    immutable_string = "hello"

    read_results = []

    def read_immutables():
        for _ in range(100):
            read_results.append(len(immutable_tuple))
            read_results.append(len(immutable_frozenset))
            read_results.append(len(immutable_string))

    # TODO: create 4 threads running read_immutables, start and join them
    pass  # Replace with thread creation
    assert all(v in (3, 5) for v in read_results)
    print("  [PASS] Immutable data (tuples, frozensets) is inherently safe")

    print("  [INFO] Your code uses proper synchronization -- "
          "ready for free-threaded Python!")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: GIL Detection ---
    print("--- Section 1: GIL Detection ---")
    try:
        demo_gil_detection()
    except (AssertionError, TypeError, AttributeError, KeyError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: Thread Safety ---
    print("--- Section 2: Thread Safety Demonstration ---")
    try:
        demo_thread_safety()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: CPU-Bound Comparison ---
    print("--- Section 3: CPU-Bound Threading vs Sequential ---")
    try:
        demo_cpu_bound_comparison()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: Thread-Safe Data Structures ---
    print("--- Section 4: Thread-Safe Data Structures ---")
    try:
        demo_thread_safe_structures()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: Migration Readiness ---
    print("--- Section 5: Migration Readiness Check ---")
    try:
        demo_migration_check()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Free-threaded Python (PEP 703) removes the GIL for true thread parallelism:")
    print("  - Detect with sys._is_gil_enabled() (Python 3.13+)")
    print("  - Always use threading.Lock for shared mutable state")
    print("  - Don't rely on the GIL for thread safety (it was never a guarantee)")
    print("  - CPU-bound threads benefit most from GIL removal")
    print("  - I/O-bound threads see minimal change")
    print("  - Write code that works on both builds: proper locks, queues, immutables")
    print()
    print("Skeleton run complete. Implement the TODOs above to make all sections pass!")
