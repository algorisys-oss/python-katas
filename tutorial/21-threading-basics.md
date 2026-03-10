# Kata 21 -- Threading Basics

[prev: 20-design-patterns](./20-design-patterns.md) | [next: 22-the-gil-explained](./22-the-gil-explained.md)

---

## What We're Building

A hands-on tour of Python's `threading` module. We'll start with the basics -- creating and joining threads -- then encounter the classic **race condition** bug when multiple threads modify shared state. We'll fix it with locks, coordinate threads with events and conditions, and understand the difference between daemon and non-daemon threads.

By the end, you'll know how to use threads safely and understand *why* shared mutable state is the root of all concurrency evil.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `threading.Thread` | Runs a function in a separate OS thread | I/O-bound parallelism, background tasks |
| `Thread.join()` | Blocks until the thread finishes | When you need a thread's result before continuing |
| `Thread.daemon` | Marks thread as daemon (killed when main exits) | Background housekeeping that shouldn't block shutdown |
| `threading.Lock` | Mutual exclusion -- only one thread holds it at a time | Protecting shared mutable state from race conditions |
| `threading.RLock` | Reentrant lock -- same thread can acquire it multiple times | When a locked function calls another locked function |
| `threading.Event` | Simple signaling between threads (set/wait/clear) | "Start now" or "stop now" signals |
| `threading.Condition` | Lock + notification -- wait until a condition is true | Producer-consumer queues, bounded buffers |
| Race condition | Bug where outcome depends on thread scheduling order | What you're trying to *prevent* |

## The Code

### Thread Basics: Creating and Joining

The simplest way to run code in a thread is `Thread(target=func, args=(...))`:

```python
import threading
import time

def worker(name: str, duration: float):
    """Simulate work that takes some time."""
    print(f"  [{name}] starting")
    time.sleep(duration)
    print(f"  [{name}] done")

# Create threads
t1 = threading.Thread(target=worker, args=("Alice", 0.02))
t2 = threading.Thread(target=worker, args=("Bob", 0.01))

t1.start()  # Begins execution in a new thread
t2.start()

# Wait for both to finish
t1.join()
t2.join()
print("Both threads finished")
```

Key points:
- `start()` launches the thread -- the function runs concurrently with the main thread
- `join()` blocks until the thread completes -- use it to synchronize
- Threads share the same process memory -- that's both the power and the danger

### Race Conditions: The Problem

When multiple threads read-modify-write shared state without coordination, the result depends on unpredictable scheduling. This is a **race condition**:

```python
import threading

counter = 0

def increment(n: int):
    """Increment counter n times -- NOT thread-safe!"""
    global counter
    for _ in range(n):
        # This is THREE operations: read counter, add 1, write counter
        # Another thread can read between the read and the write
        counter += 1

threads = [threading.Thread(target=increment, args=(1000,)) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Expected: 10000. Actual: often less, because increments get lost
print(f"Counter: {counter}")  # Race condition! Could be 9823, 9951, etc.
```

The bug: `counter += 1` is *not atomic*. It compiles to LOAD, ADD, STORE. If two threads both LOAD the same value, they both STORE the same incremented value -- one increment is lost.

### Fixing It with Lock

A `Lock` ensures only one thread executes the critical section at a time:

```python
import threading

counter = 0
lock = threading.Lock()

def safe_increment(n: int):
    """Increment counter n times -- thread-safe with lock."""
    global counter
    for _ in range(n):
        with lock:          # Acquires the lock (blocks if another thread holds it)
            counter += 1    # Only one thread runs this at a time
                            # Lock is released automatically when 'with' block exits

threads = [threading.Thread(target=safe_increment, args=(1000,)) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert counter == 10000  # Always correct now
```

Always use `with lock:` (context manager) instead of manual `lock.acquire()` / `lock.release()` -- it guarantees the lock is released even if an exception occurs.

### RLock: Reentrant Lock

A regular `Lock` deadlocks if the same thread tries to acquire it twice. An `RLock` (reentrant lock) allows the *same* thread to acquire it multiple times -- it just needs to release it the same number of times:

```python
import threading

rlock = threading.RLock()

class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance
        self._lock = threading.RLock()

    def deposit(self, amount: float):
        with self._lock:
            self.balance += amount

    def withdraw(self, amount: float):
        with self._lock:
            self.balance -= amount

    def transfer_to(self, other: 'BankAccount', amount: float):
        with self._lock:            # Acquires lock (count=1)
            self.withdraw(amount)   # Acquires SAME lock again (count=2) -- OK with RLock!
            other.deposit(amount)   # Different lock on 'other'
                                    # Inner release (count=1), outer release (count=0)
```

Use `RLock` when a method that holds a lock needs to call another method on the same object that also acquires the lock. With a regular `Lock`, this would deadlock.

### Event: Simple Thread Signaling

An `Event` is a boolean flag that threads can wait on. One thread sets it, others wake up:

```python
import threading
import time

start_event = threading.Event()

def worker(name: str):
    print(f"  [{name}] waiting for start signal...")
    start_event.wait()  # Blocks until event is set
    print(f"  [{name}] started!")

threads = [threading.Thread(target=worker, args=(f"W{i}",)) for i in range(3)]
for t in threads:
    t.start()

time.sleep(0.02)  # Simulate setup time
print("  [main] sending start signal!")
start_event.set()  # All waiting threads wake up

for t in threads:
    t.join()
```

Common use cases:
- **Start gate:** All workers wait until setup is complete
- **Shutdown signal:** Workers check `stop_event.is_set()` in their loop
- **One-time notification:** "The data is ready"

### Condition: Producer-Consumer

A `Condition` combines a lock with the ability to wait for a specific condition to become true. This is the classic pattern for producer-consumer:

```python
import threading
import time

buffer: list[int] = []
MAX_SIZE = 5
condition = threading.Condition()

def producer(items: list[int]):
    for item in items:
        with condition:
            while len(buffer) >= MAX_SIZE:
                condition.wait()        # Release lock and sleep until notified
            buffer.append(item)
            condition.notify_all()      # Wake up waiting consumers

def consumer(count: int) -> list[int]:
    consumed = []
    for _ in range(count):
        with condition:
            while len(buffer) == 0:
                condition.wait()        # Release lock and sleep until notified
            consumed.append(buffer.pop(0))
            condition.notify_all()      # Wake up waiting producers
    return consumed
```

The key insight: `condition.wait()` **releases the lock** while sleeping, then **reacquires it** when woken up. Always use `while` (not `if`) before `wait()` because of **spurious wakeups** -- the thread might wake up even though the condition isn't actually true yet.

### Daemon Threads

A **daemon thread** is automatically killed when the main thread exits. A **non-daemon thread** keeps the process alive until it finishes:

```python
import threading
import time

def background_task():
    """Runs forever -- only makes sense as a daemon."""
    while True:
        time.sleep(0.01)

# Daemon thread: killed when main thread exits
daemon = threading.Thread(target=background_task, daemon=True)
daemon.start()

# Non-daemon thread: main thread waits for it
def short_task():
    time.sleep(0.02)
    print("Short task done")

regular = threading.Thread(target=short_task)
regular.start()
# Main thread exits here, but process stays alive until regular finishes
# daemon is killed automatically
```

Rules:
- **Default:** threads are non-daemon (`daemon=False`)
- **Daemon threads** are for background housekeeping (logging, monitoring, heartbeats)
- **Never use daemon threads for work that must complete** -- they're killed without cleanup
- The process exits when all non-daemon threads have finished

### Thread Lifecycle

```
                    start()
    CREATED ──────────────► RUNNING ──────────► TERMINATED
                               │                    ▲
                               │ waiting for        │
                               │ lock/event/etc     │ target function
                               ▼                    │ returns or raises
                            BLOCKED ────────────────┘
                          (waiting)
```

- `Thread.is_alive()` -- returns `True` if the thread has started and hasn't finished
- `Thread.join(timeout)` -- wait up to `timeout` seconds (returns `None` either way; check `is_alive()`)
- `Thread.name` -- human-readable name for debugging
- `threading.active_count()` -- number of alive threads (including main)
- `threading.current_thread()` -- the Thread object for the calling thread

## Playground

Run the full demonstration:

```bash
python playground/21_threading_basics.py
```

```
--- Section 1: Thread Basics ---
  Creating and joining threads...
  [Alice] starting (duration=0.02s)
  [Bob] starting (duration=0.01s)
  [Bob] done
  [Alice] done
  Both threads finished in order (join guarantees it)
  Thread basics -- start(), join(), target, args.

--- Section 2: Race Condition (The Bug) ---
  Incrementing counter 1000x across 10 threads WITHOUT lock...
  Expected: 10000, Got: some value (race condition!)
  Race condition demonstrated -- counter += 1 is not atomic.

--- Section 3: Fixing with Lock ---
  Incrementing counter 1000x across 10 threads WITH lock...
  Expected: 10000, Got: 10000
  Lock guarantees mutual exclusion -- always correct.

--- Section 4: RLock (Reentrant Lock) ---
  BankAccount with RLock:
    Account A: 1000.00, Account B: 500.00
    Transfer $200 from A to B...
    Account A: 800.00, Account B: 700.00
  RLock -- same thread can acquire it multiple times.

--- Section 5: Event (Thread Signaling) ---
  Workers waiting for start signal...
  [main] sending start signal!
  All workers received the signal and completed.
  Event -- simple boolean signaling between threads.

--- Section 6: Condition (Producer-Consumer) ---
  Producer producing 8 items, consumer consuming 8...
  Produced: [0, 1, 2, 3, 4, 5, 6, 7]
  Consumed: [0, 1, 2, 3, 4, 5, 6, 7]
  Condition -- wait/notify for producer-consumer coordination.

--- Section 7: Daemon vs Non-Daemon Threads ---
  Daemon thread started (is_alive=True, daemon=True)
  Non-daemon thread started (is_alive=True, daemon=False)
  Non-daemon thread completed.
  Daemon threads are killed when main exits; non-daemon threads keep process alive.

--- Summary ---
Threading Basics:
  - Thread(target, args): run functions in parallel
  - Lock: mutual exclusion for shared state
  - RLock: reentrant lock for nested locking
  - Event: simple signaling (set/wait/clear)
  - Condition: lock + wait/notify for producer-consumer
  - Daemon threads: background tasks killed on exit
  - Race conditions: always protect shared mutable state

All 7 sections passed. You've mastered threading basics!
```

## How It Works

```
THREADING PRIMITIVES:

  Lock (mutual exclusion):
    Thread A          Thread B
    acquire() ──►     acquire() ──► BLOCKED
    [critical]                      ...waiting...
    release() ──►                   acquire() ──► OK
                                    [critical]
                                    release()

  Event (signaling):
    Thread A          Thread B         Thread C
    wait() ──►        wait() ──►       set() ──► all wake up!
    BLOCKED           BLOCKED

  Condition (producer-consumer):
    Producer           Consumer
    acquire()          acquire()
    buffer.append()    while empty: wait()  ◄── releases lock, sleeps
    notify_all() ────► wake up! ──► reacquire lock
    release()          buffer.pop()
                       notify_all()
                       release()
```

The golden rule: **if two threads can access the same mutable data, you need synchronization.** The question is *which* primitive to use:
- **Lock** -- simple mutual exclusion (most common)
- **RLock** -- when locked code calls other locked code on the same object
- **Event** -- one-shot or repeated boolean signals
- **Condition** -- "wait until X is true" (producer-consumer, bounded buffers)

## Exercises

### Exercise 1: Thread-safe counter class

Build a `ThreadSafeCounter` class with `increment()`, `decrement()`, and `value` property. Use a `Lock` internally. Test it by spawning 10 threads that each increment 1000 times:

```python
class ThreadSafeCounter:
    def __init__(self, initial: int = 0):
        ...

    def increment(self) -> None: ...
    def decrement(self) -> None: ...

    @property
    def value(self) -> int: ...

counter = ThreadSafeCounter()
threads = [Thread(target=lambda: [counter.increment() for _ in range(1000)]) for _ in range(10)]
# ... start, join ...
assert counter.value == 10000
```

### Exercise 2: Worker pool with shutdown signal

Create a pool of 4 worker threads that process items from a shared list. Use an `Event` as a shutdown signal -- workers keep checking for work until the event is set:

```python
def worker(work_queue: list, results: list, shutdown: threading.Event):
    while not shutdown.is_set():
        # Try to grab work from the queue (use a lock!)
        # Process it and append to results
        ...

# Main thread: add work items, wait, then signal shutdown
```

### Exercise 3: Bounded buffer with Condition

Implement a `BoundedBuffer` class with `put(item)` and `get()` methods using a `Condition`. The buffer has a maximum size -- `put()` blocks when full, `get()` blocks when empty:

```python
class BoundedBuffer:
    def __init__(self, max_size: int):
        self._buffer: list = []
        self._max_size = max_size
        self._condition = threading.Condition()

    def put(self, item): ...  # Block if full
    def get(self): ...        # Block if empty
```

## What's Next

In [Kata 22 -- The GIL Explained](./22-the-gil-explained.md), we'll dive into Python's **Global Interpreter Lock** -- the reason threading in Python is different from every other language. You'll learn what the GIL actually protects, why CPU-bound threads don't run in parallel, and when threads are still the right tool despite the GIL.

---

[prev: 20-design-patterns](./20-design-patterns.md) | [next: 22-the-gil-explained](./22-the-gil-explained.md)
