# Kata 23 -- Thread Synchronization

[prev: 22-the-gil-explained](./22-the-gil-explained.md) | [next: 24-multiprocessing](./24-multiprocessing.md)

---

## What We're Building

Thread synchronization primitives that go beyond basic locks. We'll build four real-world patterns: a **bounded buffer** using `queue.Queue` for producer-consumer communication, a **connection pool** using `Semaphore` to limit concurrent access, a **parallel computation** using `Barrier` to coordinate phases, and a **deadlock example** with its fix. These are the building blocks of every concurrent system -- web servers, database pools, task queues, and pipeline architectures.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `queue.Queue` | Thread-safe FIFO with blocking put/get | Producer-consumer, task distribution, pipelines |
| `Semaphore` | Limits concurrent access to N slots | Connection pools, rate limiting, resource caps |
| `Barrier` | Blocks N threads until all arrive | Phased computation, parallel map-reduce steps |
| Deadlock | Circular wait where threads block forever | Understanding what NOT to do |
| Lock ordering | Acquire locks in consistent global order | Preventing deadlocks |
| Thread-safe data structures | `queue.Queue`, `collections.deque` (with locks) | Any shared mutable state across threads |

## The Code

### Section 1: Producer-Consumer with Queue

The `queue.Queue` class is Python's thread-safe Swiss Army knife. It handles all locking internally -- you never need to wrap it with your own lock. The `maxsize` parameter creates a **bounded buffer**: producers block when the queue is full, consumers block when it's empty.

```python
import queue
import threading
import time

def bounded_buffer_demo():
    """Producer-consumer with a bounded queue."""
    buffer: queue.Queue[str] = queue.Queue(maxsize=3)
    produced = []
    consumed = []

    def producer(name: str, items: list[str]):
        for item in items:
            buffer.put(item)  # Blocks if full
            produced.append(f"{name}:{item}")
            time.sleep(0.01)
        buffer.put(None)  # Sentinel to signal "done"

    def consumer(name: str):
        while True:
            item = buffer.get()  # Blocks if empty
            if item is None:
                buffer.put(None)  # Re-post sentinel for other consumers
                break
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
```

Key points:
- `put()` blocks when `maxsize` is reached -- **backpressure** is automatic
- `get()` blocks when the queue is empty -- no busy-waiting needed
- The `None` sentinel pattern cleanly signals "no more work"
- Re-posting the sentinel lets multiple consumers all see the stop signal

### Section 2: Connection Pool with Semaphore

A `Semaphore` is a counter-based lock: it allows up to N threads through simultaneously. This is perfect for connection pools, rate limiters, and any resource with a fixed capacity.

```python
import threading
import time

class ConnectionPool:
    """Fixed-size pool using Semaphore to limit concurrent connections."""

    def __init__(self, size: int):
        self._semaphore = threading.Semaphore(size)
        self._lock = threading.Lock()
        self._connections: list[str] = [f"conn-{i}" for i in range(size)]
        self._in_use: list[str] = []
        self.max_concurrent = 0

    def acquire(self) -> str:
        self._semaphore.acquire()  # Blocks if all connections in use
        with self._lock:
            conn = self._connections.pop()
            self._in_use.append(conn)
            self.max_concurrent = max(self.max_concurrent, len(self._in_use))
            return conn

    def release(self, conn: str):
        with self._lock:
            self._in_use.remove(conn)
            self._connections.append(conn)
        self._semaphore.release()  # Allow another thread through
```

The Semaphore acts as a gatekeeper: `acquire()` decrements the counter (blocking at 0), and `release()` increments it. The internal `Lock` protects the list mutations -- Semaphore only controls *how many* threads enter, not the data access itself.

### Section 3: Parallel Computation with Barrier

A `Barrier` synchronizes exactly N threads at a rendezvous point. All threads must call `barrier.wait()` before any can proceed. This is essential for phased computations where each phase must complete before the next begins.

```python
import threading

def parallel_sum_with_barrier(data: list[int], num_workers: int) -> int:
    """Split data across workers, barrier-sync, then combine results."""
    chunk_size = len(data) // num_workers
    partial_results: list[int] = [0] * num_workers
    barrier = threading.Barrier(num_workers)

    def worker(worker_id: int):
        start = worker_id * chunk_size
        end = start + chunk_size if worker_id < num_workers - 1 else len(data)

        # Phase 1: compute partial sum
        partial_results[worker_id] = sum(data[start:end])

        # Barrier: wait for all workers to finish Phase 1
        barrier.wait()

    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(num_workers)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(partial_results)
```

The barrier guarantees that all partial sums are computed before anyone reads `partial_results`. Without it, a fast thread might read incomplete results from slower threads.

### Section 4: Deadlock -- The Problem and the Fix

Deadlock occurs when two threads each hold a lock the other needs. Thread A holds Lock 1 and waits for Lock 2; Thread B holds Lock 2 and waits for Lock 1. Neither can proceed.

```python
import threading
import time

def deadlock_demo():
    """Demonstrate deadlock with two locks acquired in different order."""
    lock_a = threading.Lock()
    lock_b = threading.Lock()
    deadlocked = threading.Event()

    def thread_1():
        lock_a.acquire()
        time.sleep(0.01)  # Give thread_2 time to grab lock_b
        if not lock_b.acquire(timeout=0.05):
            deadlocked.set()
            lock_a.release()
            return
        lock_b.release()
        lock_a.release()

    def thread_2():
        lock_b.acquire()  # Opposite order!
        time.sleep(0.01)
        if not lock_a.acquire(timeout=0.05):
            deadlocked.set()
            lock_b.release()
            return
        lock_a.release()
        lock_b.release()

    t1 = threading.Thread(target=thread_1)
    t2 = threading.Thread(target=thread_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return deadlocked.is_set()  # True -- deadlock detected
```

**The fix: consistent lock ordering.** Always acquire locks in the same global order. If every thread acquires `lock_a` before `lock_b`, circular waits become impossible.

```python
def no_deadlock_demo():
    """Fix deadlock by always acquiring locks in the same order."""
    lock_a = threading.Lock()
    lock_b = threading.Lock()
    results = []

    def worker(name: str):
        # Always acquire lock_a first, then lock_b
        with lock_a:
            time.sleep(0.01)
            with lock_b:
                results.append(f"{name} acquired both locks")

    t1 = threading.Thread(target=worker, args=("T1",))
    t2 = threading.Thread(target=worker, args=("T2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    return results  # Both threads succeed -- no deadlock
```

## Playground

Run the full demonstration with all synchronization patterns:

```bash
python playground/23_thread_synchronization.py
```

```
--- Section 1: Producer-Consumer with Queue ---
  Buffer maxsize: 3
  Produced 6 items across 2 producers
  Consumed 6 items across 2 consumers
  All items accounted for: True
  Queue backpressure works -- producers block when buffer is full.

--- Section 2: Connection Pool with Semaphore ---
  Pool size: 2, workers: 4
  Max concurrent connections: 2
  Semaphore enforces pool limit: True
  All 4 workers completed successfully.
  Connection pool -- Semaphore limits concurrent access to N slots.

--- Section 3: Parallel Sum with Barrier ---
  Data: 1000 integers
  Workers: 4
  Expected sum: 499500
  Parallel sum:  499500
  Results match: True
  Barrier ensures all partial sums complete before combining.

--- Section 4: Deadlock Demo ---
  Deadlock detected (with timeout): True
  Threads held locks in opposite order -- classic circular wait.

--- Section 5: Deadlock Fix (Lock Ordering) ---
  Both threads acquired locks safely: True
  Fix: always acquire locks in the same global order.

--- Summary ---
Thread Synchronization Primitives:
  - Queue: thread-safe bounded buffer for producer-consumer
  - Semaphore: limits concurrent access to N resources
  - Barrier: synchronizes N threads at a rendezvous point
  - Deadlock: circular lock waits -- fix with consistent ordering

All 5 sections passed. You've mastered thread synchronization!
```

## How It Works

```
PRODUCER-CONSUMER (Queue):

  Producer 1 ──put()──┐                ┌──get()── Consumer 1
                       ├── [ Q U E ] ──┤
  Producer 2 ──put()──┘   (bounded)    └──get()── Consumer 2
                       blocks if full   blocks if empty


CONNECTION POOL (Semaphore):

  Semaphore(N=2)
    ┌────────────────────┐
    │  slot 1: [in use]  │  Thread A (acquired)
    │  slot 2: [in use]  │  Thread B (acquired)
    └────────────────────┘
       Thread C: BLOCKED (waits for release)
       Thread D: BLOCKED (waits for release)


BARRIER (N=3):

  Thread 1: ████████░░░ wait() ──┐
  Thread 2: ████░░░░░░░ wait() ──┤── all 3 arrive ──► all proceed
  Thread 3: ██████████░ wait() ──┘


DEADLOCK (circular wait):

  Thread 1:  holds Lock A ──wants──► Lock B
                  ▲                      │
                  │    CIRCULAR WAIT     │
                  │                      ▼
  Thread 2:  holds Lock B ──wants──► Lock A

  FIX: Both threads acquire Lock A first, then Lock B
       → No circular dependency → No deadlock
```

## Exercises

### Exercise 1: Multi-stage pipeline

Build a 3-stage pipeline using Queues -- each stage is a separate thread:

```python
def pipeline(data: list[int]) -> list[str]:
    """
    Stage 1: double each number
    Stage 2: filter evens only (they'll all be even after doubling)
    Stage 3: convert to string with prefix "result-"

    Use one Queue between each pair of stages.
    """
    q1: queue.Queue = queue.Queue()
    q2: queue.Queue = queue.Queue()
    q3: queue.Queue = queue.Queue()
    ...
    # Return list of "result-N" strings
```

### Exercise 2: Read-write lock

Implement a read-write lock that allows multiple concurrent readers but exclusive writers:

```python
class ReadWriteLock:
    """Multiple readers OR one writer, never both."""

    def __init__(self):
        self._readers = 0
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()

    def acquire_read(self): ...
    def release_read(self): ...
    def acquire_write(self): ...
    def release_write(self): ...
```

### Exercise 3: Dining philosophers

Implement the classic dining philosophers problem with 5 philosophers and 5 forks. Use lock ordering to prevent deadlock:

```python
def dining_philosophers(num_meals: int = 3) -> list[str]:
    """
    5 philosophers, 5 forks (locks).
    Each philosopher picks up lower-numbered fork first.
    Returns list of "Philosopher N ate meal M" strings.
    """
    ...
```

## What's Next

In [Kata 24 -- Multiprocessing](./24-multiprocessing.md), we'll escape the GIL entirely by using separate processes instead of threads. You'll learn how `multiprocessing.Process`, `Pool`, shared memory, and `Queue` let you achieve true CPU parallelism in Python.

---

[prev: 22-the-gil-explained](./22-the-gil-explained.md) | [next: 24-multiprocessing](./24-multiprocessing.md)
