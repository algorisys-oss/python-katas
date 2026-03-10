"""
Kata 22 -- The GIL Explained
Run: python playground/skeletons/22_the_gil_explained.py

Demonstrates CPython's Global Interpreter Lock through timing experiments.
CPU-bound work is slower with threads (GIL contention), but I/O-bound work
is faster (GIL released during I/O). All demos complete well within 5 seconds.
"""

import sys
import threading
import time


# ===========================================================================
# PART 1: CPU-BOUND WORK -- THREADING IS SLOWER (GIL contention)
# ===========================================================================

def cpu_work(n: int) -> int:
    """Pure CPU work -- sum of squares. GIL is held the entire time."""
    # TODO: loop from 0 to n, summing i * i into a total, then return it
    # HINT: use a for loop with range(n) and accumulate total += i * i
    pass


def demo_cpu_bound() -> None:
    """Prove that threads make CPU-bound work slower due to GIL contention."""
    print("=" * 60)
    print("PART 1: CPU-BOUND (threading hurts)")
    print("=" * 60)

    workload = 200_000
    num_tasks = 4

    # --- Sequential ---
    # TODO: time how long it takes to call cpu_work(workload) num_tasks times in a loop
    # HINT: use time.perf_counter() before and after the loop
    start = time.perf_counter()
    pass  # replace with loop
    sequential_time = time.perf_counter() - start

    # --- Threaded ---
    # TODO: create num_tasks threads, each calling cpu_work(workload), start and join them
    # HINT: threads = [threading.Thread(target=cpu_work, args=(workload,)) for _ in range(...)]
    start = time.perf_counter()
    pass  # replace with thread creation, start, and join
    threaded_time = time.perf_counter() - start

    print(f"  Sequential: {sequential_time:.4f}s")
    print(f"  Threaded:   {threaded_time:.4f}s")
    ratio = threaded_time / sequential_time if sequential_time > 0 else 0
    print(f"  Ratio:      {ratio:.2f}x (>= 1.0 means threads didn't help)")

    try:
        assert threaded_time >= sequential_time * 0.8, (
            f"Threaded should not be significantly faster for CPU-bound work"
        )
        print("  ✓ Confirmed: threading does NOT speed up CPU-bound work\n")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}\n")


# ===========================================================================
# PART 2: I/O-BOUND WORK -- THREADING HELPS (GIL released during I/O)
# ===========================================================================

def io_work(duration: float = 0.01) -> None:
    """Simulated I/O -- GIL is released during time.sleep()."""
    # TODO: call time.sleep(duration) to simulate I/O
    pass


def demo_io_bound() -> None:
    """Prove that threads make I/O-bound work faster because the GIL is released."""
    print("=" * 60)
    print("PART 2: I/O-BOUND (threading helps)")
    print("=" * 60)

    io_tasks = 20
    io_duration = 0.01  # 10ms per task

    # --- Sequential ---
    # TODO: time how long it takes to call io_work(io_duration) io_tasks times in a loop
    start = time.perf_counter()
    pass  # replace with loop
    sequential_time = time.perf_counter() - start

    # --- Threaded ---
    # TODO: create io_tasks threads, each calling io_work(io_duration), start and join them
    start = time.perf_counter()
    pass  # replace with thread creation, start, and join
    threaded_time = time.perf_counter() - start

    speedup = sequential_time / threaded_time if threaded_time > 0 else 0
    print(f"  Sequential: {sequential_time:.4f}s")
    print(f"  Threaded:   {threaded_time:.4f}s")
    print(f"  Speedup:    {speedup:.1f}x")

    try:
        assert speedup > 3.0, f"Expected significant speedup, got {speedup:.1f}x"
        print("  ✓ Confirmed: threading speeds up I/O-bound work\n")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}\n")


# ===========================================================================
# PART 3: MIXED WORKLOAD -- CPU + I/O
# ===========================================================================

def mixed_work(n: int = 10_000, io_time: float = 0.02) -> int:
    """CPU work followed by simulated I/O."""
    # TODO: sum i*i for i in range(n) using a generator expression, then sleep for io_time
    # HINT: total = sum(i * i for i in range(n)); time.sleep(io_time); return total
    pass


def demo_mixed() -> None:
    """Show that mixed workloads still benefit from threading (I/O dominates)."""
    print("=" * 60)
    print("PART 3: MIXED WORKLOAD (CPU + I/O)")
    print("=" * 60)

    mixed_tasks = 10

    # --- Sequential ---
    # TODO: time how long it takes to call mixed_work() mixed_tasks times
    start = time.perf_counter()
    pass  # replace with loop
    sequential_time = time.perf_counter() - start

    # --- Threaded ---
    # TODO: create mixed_tasks threads, each calling mixed_work(), start and join them
    start = time.perf_counter()
    pass  # replace with thread creation, start, and join
    threaded_time = time.perf_counter() - start

    speedup = sequential_time / threaded_time if threaded_time > 0 else 0
    print(f"  Sequential: {sequential_time:.4f}s")
    print(f"  Threaded:   {threaded_time:.4f}s")
    print(f"  Speedup:    {speedup:.1f}x")

    try:
        assert speedup > 1.2, f"Expected speedup for mixed workload, got {speedup:.1f}x"
        print("  ✓ Confirmed: mixed workloads benefit from threading\n")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}\n")


# ===========================================================================
# PART 4: GIL SWITCH INTERVAL
# ===========================================================================

def demo_switch_interval() -> None:
    """Show the GIL's thread switch interval setting."""
    print("=" * 60)
    print("PART 4: GIL SWITCH INTERVAL")
    print("=" * 60)

    # TODO: get the switch interval using sys.getswitchinterval()
    # HINT: interval = sys.getswitchinterval()
    interval = 0.005  # replace with actual call
    print(f"  Default switch interval: {interval:.4f}s ({interval * 1000:.1f}ms)")
    print(f"  This means every {interval * 1000:.1f}ms, the GIL scheduler considers")
    print(f"  letting another thread run.")

    try:
        assert 0.004 <= interval <= 0.006, f"Expected ~5ms, got {interval * 1000:.1f}ms"
        print("  ✓ Confirmed: default switch interval is ~5ms\n")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}\n")


# ===========================================================================
# PART 5: GIL DOES NOT MAKE CODE THREAD-SAFE
# ===========================================================================

counter = 0


def increment_many(n: int) -> None:
    """Increment a global counter n times. NOT thread-safe despite the GIL."""
    global counter
    # TODO: loop n times and do counter += 1 each iteration
    # HINT: for _ in range(n): counter += 1
    pass


def demo_not_thread_safe() -> None:
    """Prove that the GIL does NOT make compound operations thread-safe."""
    global counter
    print("=" * 60)
    print("PART 5: GIL DOES NOT MAKE CODE THREAD-SAFE")
    print("=" * 60)

    increments_per_thread = 100_000
    num_threads = 4
    expected = num_threads * increments_per_thread

    # TODO: run 3 trials. In each trial:
    #   1. reset counter to 0
    #   2. create num_threads threads, each calling increment_many(increments_per_thread)
    #   3. start and join all threads
    #   4. compare counter to expected and print the difference
    # HINT: track whether any trial lost updates with a boolean flag
    lost_any = False
    for trial in range(3):
        counter = 0
        pass  # replace with thread creation, start, and join

        lost = expected - counter
        if lost > 0:
            lost_any = True
            print(f"  Trial {trial + 1}: expected={expected}, got={counter}, lost={lost}")
        else:
            print(f"  Trial {trial + 1}: expected={expected}, got={counter}, lost=0 (lucky!)")

    if lost_any:
        print("  ✓ Confirmed: counter += 1 is NOT atomic -- updates were lost")
    else:
        print("  Note: no lost updates this run (race conditions are non-deterministic)")
    print("  → Always use Lock for shared mutable state (see Kata 23)\n")


# ===========================================================================
# PART 6: PER-THREAD STATE
# ===========================================================================

def demo_per_thread_state() -> None:
    """Show that each thread has its own stack but shares the heap."""
    print("=" * 60)
    print("PART 6: PER-THREAD STATE")
    print("=" * 60)

    results: dict[str, int] = {}

    def worker(name: str, value: int) -> None:
        """Each thread has its own local variables (name, value) on its stack."""
        # TODO: compute local_var = value * 2, then store it in results[name]
        # HINT: local_var is thread-local, results is shared
        pass

    # TODO: create 4 threads, each calling worker(f"thread-{i}", i), start and join
    threads = []  # replace with thread creation
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  Thread results: {results}")
    try:
        assert len(results) == 4, "Expected 4 results"
        for i in range(4):
            key = f"thread-{i}"
            assert results[key] == i * 2, f"Expected {i * 2} for {key}"

        print("  ✓ Each thread computed independently with its own local variables")
        print("  ✓ Results were stored in a shared dict (the heap)\n")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}\n")


# ===========================================================================
# SUMMARY
# ===========================================================================

def demo_summary() -> None:
    """Print a summary table of when to use threads."""
    print("=" * 60)
    print("SUMMARY: WHEN TO USE THREADS")
    print("=" * 60)
    print()
    print("  Workload Type  │ Threads Help? │ Why")
    print("  ───────────────┼───────────────┼──────────────────────────")
    print("  CPU-bound      │ No (slower)   │ GIL prevents parallelism")
    print("  I/O-bound      │ Yes (faster)  │ GIL released during I/O")
    print("  Mixed          │ Usually yes   │ I/O portions overlap")
    print()
    print("  For CPU-bound parallelism → use multiprocessing (Kata 25)")
    print("  For I/O-bound concurrency → use threading or asyncio")
    print()


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    print("Kata 22 -- The GIL Explained\n")

    demo_cpu_bound()
    demo_io_bound()
    demo_mixed()
    demo_switch_interval()
    demo_not_thread_safe()
    demo_per_thread_state()
    demo_summary()

    print("All demos complete!")
