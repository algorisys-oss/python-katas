"""
Kata 21 -- Threading Basics
Run: python playground/21_threading_basics.py

Learn to create threads, protect shared state with locks, coordinate threads
with events and conditions, and understand daemon vs non-daemon threads.
"""

import threading
import time


# ===========================================================================
# SECTION 1: THREAD BASICS -- creating and joining threads
# ===========================================================================

def worker(name: str, duration: float, log: list[str]):
    """Simulate work that takes some time. Appends to log for verification."""
    log.append(f"{name}-start")
    time.sleep(duration)
    log.append(f"{name}-done")


# ===========================================================================
# SECTION 2: RACE CONDITION -- the bug
# ===========================================================================

def unsafe_increment(counter_ref: list[int], n: int):
    """Increment counter n times WITHOUT a lock -- racy!"""
    for _ in range(n):
        counter_ref[0] += 1  # Read-modify-write is NOT atomic


# ===========================================================================
# SECTION 3: FIXING WITH LOCK
# ===========================================================================

def safe_increment(counter_ref: list[int], n: int, lock: threading.Lock):
    """Increment counter n times WITH a lock -- thread-safe."""
    for _ in range(n):
        with lock:
            counter_ref[0] += 1


# ===========================================================================
# SECTION 4: RLOCK -- reentrant lock
# ===========================================================================

class BankAccount:
    """Bank account using RLock so transfer_to can call withdraw (both lock)."""

    def __init__(self, name: str, balance: float):
        self.name = name
        self.balance = balance
        self._lock = threading.RLock()

    def deposit(self, amount: float):
        with self._lock:
            self.balance += amount

    def withdraw(self, amount: float):
        with self._lock:
            self.balance -= amount

    def transfer_to(self, other: 'BankAccount', amount: float):
        """Transfer money -- acquires self._lock, then calls self.withdraw (reentrant)."""
        with self._lock:
            self.withdraw(amount)   # Re-acquires same RLock -- OK!
            other.deposit(amount)


# ===========================================================================
# SECTION 5: EVENT -- simple thread signaling
# ===========================================================================

def event_worker(name: str, start_event: threading.Event, results: list[str]):
    """Wait for the start event, then record completion."""
    start_event.wait()  # Blocks until event is set
    results.append(name)


# ===========================================================================
# SECTION 6: CONDITION -- producer-consumer
# ===========================================================================

def producer(items: list[int], buffer: list[int], max_size: int,
             condition: threading.Condition):
    """Produce items into buffer, waiting if buffer is full."""
    for item in items:
        with condition:
            while len(buffer) >= max_size:
                condition.wait()
            buffer.append(item)
            condition.notify_all()


def consumer(count: int, buffer: list[int], condition: threading.Condition,
             consumed: list[int]):
    """Consume count items from buffer, waiting if buffer is empty."""
    for _ in range(count):
        with condition:
            while len(buffer) == 0:
                condition.wait()
            consumed.append(buffer.pop(0))
            condition.notify_all()


# ===========================================================================
# SECTION 7: DAEMON VS NON-DAEMON THREADS
# ===========================================================================

def daemon_task(log: list[str], stop_event: threading.Event):
    """Simulates a daemon background task that runs until stopped."""
    while not stop_event.is_set():
        time.sleep(0.01)
    log.append("daemon-stopped")


def regular_task(log: list[str]):
    """Short-lived non-daemon task."""
    time.sleep(0.02)
    log.append("regular-done")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Thread Basics ---
    print("--- Section 1: Thread Basics ---")

    log: list[str] = []
    print("  Creating and joining threads...")

    t1 = threading.Thread(target=worker, args=("Alice", 0.02, log))
    t2 = threading.Thread(target=worker, args=("Bob", 0.01, log))

    t1.start()
    print(f"  [Alice] starting (duration=0.02s)")
    t2.start()
    print(f"  [Bob] starting (duration=0.01s)")

    t2.join()  # Bob finishes first (shorter sleep)
    print(f"  [Bob] done")
    t1.join()
    print(f"  [Alice] done")

    # Both threads completed -- verify via log
    assert "Alice-start" in log
    assert "Alice-done" in log
    assert "Bob-start" in log
    assert "Bob-done" in log

    print("  Both threads finished in order (join guarantees it)")
    print("  Thread basics -- start(), join(), target, args.")

    print()

    # --- Section 2: Race Condition (The Bug) ---
    print("--- Section 2: Race Condition (The Bug) ---")

    print("  Incrementing counter 1000x across 10 threads WITHOUT lock...")

    # Use a list to hold the counter so we can share it across threads
    unsafe_counter = [0]
    threads = [
        threading.Thread(target=unsafe_increment, args=(unsafe_counter, 1000))
        for _ in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # The result is unpredictable -- might be 10000, might be less
    print(f"  Expected: 10000, Got: {unsafe_counter[0]} (race condition!)")
    # We can't assert an exact value -- the whole point is it's unpredictable.
    # But we CAN assert it completed (didn't crash).
    assert isinstance(unsafe_counter[0], int)
    print("  Race condition demonstrated -- counter += 1 is not atomic.")

    print()

    # --- Section 3: Fixing with Lock ---
    print("--- Section 3: Fixing with Lock ---")

    print("  Incrementing counter 1000x across 10 threads WITH lock...")

    safe_counter = [0]
    lock = threading.Lock()
    threads = [
        threading.Thread(target=safe_increment, args=(safe_counter, 1000, lock))
        for _ in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"  Expected: 10000, Got: {safe_counter[0]}")
    assert safe_counter[0] == 10000  # Always correct with lock!
    print("  Lock guarantees mutual exclusion -- always correct.")

    print()

    # --- Section 4: RLock (Reentrant Lock) ---
    print("--- Section 4: RLock (Reentrant Lock) ---")

    account_a = BankAccount("A", 1000.0)
    account_b = BankAccount("B", 500.0)

    print("  BankAccount with RLock:")
    print(f"    Account A: {account_a.balance:.2f}, Account B: {account_b.balance:.2f}")
    print("    Transfer $200 from A to B...")

    # Transfer in a separate thread to prove thread safety
    t = threading.Thread(target=account_a.transfer_to, args=(account_b, 200.0))
    t.start()
    t.join()

    print(f"    Account A: {account_a.balance:.2f}, Account B: {account_b.balance:.2f}")
    assert account_a.balance == 800.0
    assert account_b.balance == 700.0

    # Concurrent transfers to verify RLock works under contention
    account_c = BankAccount("C", 10000.0)
    account_d = BankAccount("D", 0.0)
    transfer_threads = [
        threading.Thread(target=account_c.transfer_to, args=(account_d, 1.0))
        for _ in range(100)
    ]
    for t in transfer_threads:
        t.start()
    for t in transfer_threads:
        t.join()

    assert account_c.balance == 9900.0
    assert account_d.balance == 100.0

    print("  RLock -- same thread can acquire it multiple times.")

    print()

    # --- Section 5: Event (Thread Signaling) ---
    print("--- Section 5: Event (Thread Signaling) ---")

    start_event = threading.Event()
    results: list[str] = []

    print("  Workers waiting for start signal...")

    workers = [
        threading.Thread(target=event_worker, args=(f"W{i}", start_event, results))
        for i in range(3)
    ]
    for w in workers:
        w.start()

    time.sleep(0.02)  # Give threads time to reach wait()
    print("  [main] sending start signal!")
    start_event.set()  # All waiting threads wake up

    for w in workers:
        w.join()

    assert len(results) == 3
    assert set(results) == {"W0", "W1", "W2"}

    print("  All workers received the signal and completed.")
    print("  Event -- simple boolean signaling between threads.")

    print()

    # --- Section 6: Condition (Producer-Consumer) ---
    print("--- Section 6: Condition (Producer-Consumer) ---")

    buffer: list[int] = []
    condition = threading.Condition()
    items_to_produce = list(range(8))
    consumed_items: list[int] = []

    print(f"  Producer producing {len(items_to_produce)} items, consumer consuming {len(items_to_produce)}...")

    prod_thread = threading.Thread(
        target=producer, args=(items_to_produce, buffer, 3, condition)
    )
    cons_thread = threading.Thread(
        target=consumer, args=(len(items_to_produce), buffer, condition, consumed_items)
    )

    prod_thread.start()
    cons_thread.start()
    prod_thread.join()
    cons_thread.join()

    print(f"  Produced: {items_to_produce}")
    print(f"  Consumed: {consumed_items}")
    assert consumed_items == items_to_produce  # All items consumed in order
    assert len(buffer) == 0  # Buffer is empty after all items consumed

    print("  Condition -- wait/notify for producer-consumer coordination.")

    print()

    # --- Section 7: Daemon vs Non-Daemon Threads ---
    print("--- Section 7: Daemon vs Non-Daemon Threads ---")

    daemon_log: list[str] = []
    stop_event = threading.Event()

    daemon_thread = threading.Thread(
        target=daemon_task, args=(daemon_log, stop_event), daemon=True
    )
    daemon_thread.start()
    print(f"  Daemon thread started (is_alive={daemon_thread.is_alive()}, daemon={daemon_thread.daemon})")

    assert daemon_thread.is_alive()
    assert daemon_thread.daemon is True

    regular_log: list[str] = []
    regular_thread = threading.Thread(target=regular_task, args=(regular_log,))
    regular_thread.start()
    print(f"  Non-daemon thread started (is_alive={regular_thread.is_alive()}, daemon={regular_thread.daemon})")

    assert regular_thread.daemon is False

    regular_thread.join()
    print("  Non-daemon thread completed.")
    assert "regular-done" in regular_log

    # Clean up daemon thread explicitly (since we're not exiting the process)
    stop_event.set()
    daemon_thread.join(timeout=1.0)

    print("  Daemon threads are killed when main exits; non-daemon threads keep process alive.")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Threading Basics:")
    print("  - Thread(target, args): run functions in parallel")
    print("  - Lock: mutual exclusion for shared state")
    print("  - RLock: reentrant lock for nested locking")
    print("  - Event: simple signaling (set/wait/clear)")
    print("  - Condition: lock + wait/notify for producer-consumer")
    print("  - Daemon threads: background tasks killed on exit")
    print("  - Race conditions: always protect shared mutable state")
    print()
    print("All 7 sections passed. You've mastered threading basics!")
