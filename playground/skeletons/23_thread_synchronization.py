"""
Kata 23 -- Thread Synchronization
Run: python playground/skeletons/23_thread_synchronization.py

Thread synchronization primitives beyond basic locks: Queue for producer-consumer,
Semaphore for connection pools, Barrier for phased computation, and deadlock
avoidance through consistent lock ordering.
"""

import queue
import threading
import time


# ===========================================================================
# SECTION 1: PRODUCER-CONSUMER WITH QUEUE
# ===========================================================================

def bounded_buffer_demo() -> tuple[list[str], list[str]]:
    """Producer-consumer with a bounded queue (maxsize=3)."""
    buffer: queue.Queue[str | None] = queue.Queue(maxsize=3)
    produced: list[str] = []
    consumed: list[str] = []
    produced_lock = threading.Lock()
    consumed_lock = threading.Lock()

    def producer(name: str, items: list[str]):
        for item in items:
            # TODO: put item into buffer (blocks if full)
            # HINT: buffer.put(item)
            pass
            with produced_lock:
                produced.append(f"{name}:{item}")
            time.sleep(0.01)
        # TODO: put a sentinel (None) to signal "done"
        pass

    def consumer(name: str):
        while True:
            # TODO: get an item from buffer (blocks if empty)
            # HINT: buffer.get()
            item = None
            if item is None:
                # TODO: re-post sentinel for other consumers
                # HINT: buffer.put(None)
                pass
                break
            with consumed_lock:
                consumed.append(f"{name}:{item}")
            time.sleep(0.01)

    items = [f"item-{i}" for i in range(6)]
    threads = [
        threading.Thread(target=producer, args=("P1", items[:3])),
        threading.Thread(target=producer, args=("P2", items[3:])),
        threading.Thread(target=consumer, args=("C1",)),
        threading.Thread(target=consumer, args=("C2",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return produced, consumed


# ===========================================================================
# SECTION 2: CONNECTION POOL WITH SEMAPHORE
# ===========================================================================

class ConnectionPool:
    """Fixed-size pool using Semaphore to limit concurrent connections."""

    def __init__(self, size: int):
        # TODO: create a Semaphore with 'size' permits
        # HINT: threading.Semaphore(size)
        self._semaphore = None
        self._lock = threading.Lock()
        self._connections: list[str] = [f"conn-{i}" for i in range(size)]
        self._in_use: list[str] = []
        self.max_concurrent = 0

    def acquire(self) -> str:
        """Acquire a connection, blocking if none available."""
        # TODO: acquire the semaphore (blocks if all connections in use)
        # HINT: self._semaphore.acquire()
        pass
        with self._lock:
            conn = self._connections.pop()
            self._in_use.append(conn)
            self.max_concurrent = max(self.max_concurrent, len(self._in_use))
            return conn

    def release(self, conn: str):
        """Return a connection to the pool."""
        with self._lock:
            self._in_use.remove(conn)
            self._connections.append(conn)
        # TODO: release the semaphore to allow another thread through
        # HINT: self._semaphore.release()
        pass

    @property
    def available(self) -> int:
        with self._lock:
            return len(self._connections)


def connection_pool_demo() -> tuple[int, list[str]]:
    """Demonstrate Semaphore-based connection pool."""
    pool = ConnectionPool(size=2)
    results: list[str] = []
    results_lock = threading.Lock()

    def worker(name: str):
        conn = pool.acquire()
        time.sleep(0.01)  # Simulate work with the connection
        with results_lock:
            results.append(f"{name} used {conn}")
        pool.release(conn)

    threads = [
        threading.Thread(target=worker, args=(f"W{i}",))
        for i in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return pool.max_concurrent, results


# ===========================================================================
# SECTION 3: PARALLEL SUM WITH BARRIER
# ===========================================================================

def parallel_sum_with_barrier(data: list[int], num_workers: int) -> int:
    """Split data across workers, barrier-sync, then combine results."""
    chunk_size = len(data) // num_workers
    partial_results: list[int] = [0] * num_workers
    # TODO: create a Barrier for num_workers threads
    # HINT: threading.Barrier(num_workers)
    barrier = None

    def worker(worker_id: int):
        start = worker_id * chunk_size
        end = start + chunk_size if worker_id < num_workers - 1 else len(data)

        # TODO: Phase 1 -- compute partial sum and store in partial_results[worker_id]
        # HINT: partial_results[worker_id] = sum(data[start:end])
        pass

        # TODO: wait at the barrier for all workers to finish Phase 1
        # HINT: barrier.wait()
        pass

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_workers)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(partial_results)


# ===========================================================================
# SECTION 4: DEADLOCK DEMO
# ===========================================================================

def deadlock_demo() -> bool:
    """Demonstrate deadlock with two locks acquired in different order.

    Uses timeouts to detect deadlock without hanging forever.
    Returns True if deadlock was detected.
    """
    lock_a = threading.Lock()
    lock_b = threading.Lock()
    deadlocked = threading.Event()

    def thread_1():
        # TODO: acquire lock_a, sleep briefly, then try to acquire lock_b with timeout
        # HINT: lock_a.acquire(), time.sleep(0.01), lock_b.acquire(timeout=0.05)
        # If lock_b times out, set deadlocked event and release lock_a
        pass

    def thread_2():
        # TODO: acquire lock_b (opposite order!), sleep, try lock_a with timeout
        # HINT: same pattern but reversed locks -- this creates the deadlock
        pass

    t1 = threading.Thread(target=thread_1)
    t2 = threading.Thread(target=thread_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return deadlocked.is_set()


# ===========================================================================
# SECTION 5: DEADLOCK FIX (CONSISTENT LOCK ORDERING)
# ===========================================================================

def no_deadlock_demo() -> list[str]:
    """Fix deadlock by always acquiring locks in the same order."""
    lock_a = threading.Lock()
    lock_b = threading.Lock()
    results: list[str] = []
    results_lock = threading.Lock()

    def worker(name: str):
        # TODO: acquire lock_a first, then lock_b (same order in every thread)
        # HINT: use nested 'with' statements: with lock_a: with lock_b:
        # Append f"{name} acquired both locks" to results (protected by results_lock)
        pass

    t1 = threading.Thread(target=worker, args=("T1",))
    t2 = threading.Thread(target=worker, args=("T2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return results


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Producer-Consumer with Queue ---
    print("--- Section 1: Producer-Consumer with Queue ---")

    try:
        produced, consumed = bounded_buffer_demo()

        print(f"  Buffer maxsize: 3")
        print(f"  Produced {len(produced)} items across 2 producers")
        print(f"  Consumed {len(consumed)} items across 2 consumers")

        # Extract just the item names (strip producer/consumer prefix)
        produced_items = sorted(p.split(":")[1] for p in produced)
        consumed_items = sorted(c.split(":")[1] for c in consumed)
        all_accounted = produced_items == consumed_items

        print(f"  All items accounted for: {all_accounted}")
        assert len(produced) == 6, f"Expected 6 produced, got {len(produced)}"
        assert len(consumed) == 6, f"Expected 6 consumed, got {len(consumed)}"
        assert all_accounted, "Produced and consumed items don't match"

        print("  Queue backpressure works -- producers block when buffer is full.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Connection Pool with Semaphore ---
    print("--- Section 2: Connection Pool with Semaphore ---")

    try:
        # Suppress in-thread exceptions that may occur if semaphore is not implemented
        _orig_excepthook = threading.excepthook
        threading.excepthook = lambda args: None
        try:
            max_concurrent, pool_results = connection_pool_demo()
        finally:
            threading.excepthook = _orig_excepthook

        print(f"  Pool size: 2, workers: 4")
        print(f"  Max concurrent connections: {max_concurrent}")
        print(f"  Semaphore enforces pool limit: {max_concurrent <= 2}")
        print(f"  All {len(pool_results)} workers completed successfully.")

        assert max_concurrent <= 2, f"Pool exceeded limit: {max_concurrent}"
        assert len(pool_results) == 4, f"Expected 4 results, got {len(pool_results)}"

        print("  Connection pool -- Semaphore limits concurrent access to N slots.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Parallel Sum with Barrier ---
    print("--- Section 3: Parallel Sum with Barrier ---")

    try:
        data = list(range(1000))
        expected = sum(data)
        parallel_result = parallel_sum_with_barrier(data, num_workers=4)

        print(f"  Data: {len(data)} integers")
        print(f"  Workers: 4")
        print(f"  Expected sum: {expected}")
        print(f"  Parallel sum:  {parallel_result}")
        print(f"  Results match: {parallel_result == expected}")

        assert parallel_result == expected, (
            f"Parallel sum {parallel_result} != expected {expected}"
        )

        print("  Barrier ensures all partial sums complete before combining.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Deadlock Demo ---
    print("--- Section 4: Deadlock Demo ---")

    try:
        was_deadlocked = deadlock_demo()

        print(f"  Deadlock detected (with timeout): {was_deadlocked}")
        assert was_deadlocked, "Expected deadlock to be detected"

        print("  Threads held locks in opposite order -- classic circular wait.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Deadlock Fix (Lock Ordering) ---
    print("--- Section 5: Deadlock Fix (Lock Ordering) ---")

    try:
        fix_results = no_deadlock_demo()

        print(f"  Both threads acquired locks safely: {len(fix_results) == 2}")
        assert len(fix_results) == 2, f"Expected 2 results, got {len(fix_results)}"

        print("  Fix: always acquire locks in the same global order.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Thread Synchronization Primitives:")
    print("  - Queue: thread-safe bounded buffer for producer-consumer")
    print("  - Semaphore: limits concurrent access to N resources")
    print("  - Barrier: synchronizes N threads at a rendezvous point")
    print("  - Deadlock: circular lock waits -- fix with consistent ordering")
    print()
    print("Skeleton run complete. Implement the TODOs above to make all sections pass!")
