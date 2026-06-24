# Kata 22 -- The GIL Explained

[prev: 21-threading-basics](./21-threading-basics.md) | [next: 23-thread-synchronization](./23-thread-synchronization.md)

---

## What We're Building

A hands-on exploration of the **Global Interpreter Lock (GIL)** -- the single most misunderstood feature of CPython. We'll prove with timing experiments that threading makes CPU-bound work **slower** (GIL contention), but makes I/O-bound work **faster** (GIL release during I/O). By the end, you'll know exactly when to reach for threads, when to reach for processes, and why.

## Concepts You'll Learn

| Concept | What It Does | When It Matters |
|---|---|---|
| The GIL | A per-interpreter mutex that lets only one thread execute Python bytecode at a time | Always -- it's baked into CPython |
| Why it exists | Protects CPython's reference-counting garbage collector from race conditions | Understanding tradeoffs in CPython's design |
| CPU-bound vs I/O-bound | CPU-bound = pure computation; I/O-bound = waiting on network/disk/sleep | Determines whether threads help or hurt |
| GIL release during I/O | CPython releases the GIL when a thread enters a blocking I/O call | Why threads still help for I/O-heavy workloads |
| Per-thread state | Each thread has its own Python stack, but shares the process's heap | Understanding what's shared vs. private |
| `sys.getswitchinterval()` | How often the GIL scheduler gives other threads a chance to run (default 5ms) | Tuning thread responsiveness |
| Timing comparisons | `time.perf_counter()` for precise wall-clock measurements | Proving GIL effects empirically |

## The Code

### Part 1: What Is the GIL?

The **Global Interpreter Lock** is a mutex (mutual exclusion lock) inside CPython that allows only **one thread** to execute Python bytecode at any given moment. Even if you create 10 threads on a 10-core machine, only one thread runs Python code at a time.

```
Thread 1: ████░░░░████░░░░████     (runs, waits, runs, waits, runs)
Thread 2: ░░░░████░░░░████░░░░     (waits, runs, waits, runs, waits)
                                    ← only one █ at any time slice
```

**Why does it exist?** CPython uses reference counting for memory management. Every Python object has a reference count (`ob_refcnt`). Without the GIL, two threads incrementing/decrementing `ob_refcnt` simultaneously would corrupt it -- objects would leak or be freed while still in use. The GIL makes all reference count operations atomically safe without per-object locks.

### Part 2: What the GIL Blocks (and What It Doesn't)

The GIL blocks **Python bytecode execution**. It does NOT block:
- **I/O operations** -- `socket.recv()`, `file.read()`, `time.sleep()` all release the GIL
- **C extensions** -- NumPy, OpenSSL, and other C code can explicitly release the GIL
- **`subprocess` calls** -- the child process has its own GIL

This is why the rule of thumb is simple:
- **CPU-bound** (number crunching in pure Python) → threads HURT (GIL contention overhead)
- **I/O-bound** (network calls, file I/O, database queries) → threads HELP (GIL released during wait)

### Part 3: CPU-Bound Demo -- Threading Is Slower

Let's prove it. We'll run a CPU-bound function (summing numbers) both sequentially and with threads, and compare wall-clock time.

```python
import threading
import time

def cpu_work(n: int) -> int:
    """Pure CPU work -- sum of squares. GIL is held the entire time."""
    total = 0
    for i in range(n):
        total += i * i
    return total

WORKLOAD = 200_000  # small enough to finish fast
NUM_TASKS = 4

# --- Sequential ---
start = time.perf_counter()
for _ in range(NUM_TASKS):
    cpu_work(WORKLOAD)
sequential_time = time.perf_counter() - start

# --- Threaded ---
start = time.perf_counter()
threads = [threading.Thread(target=cpu_work, args=(WORKLOAD,)) for _ in range(NUM_TASKS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
threaded_time = time.perf_counter() - start

print(f"CPU-bound sequential: {sequential_time:.4f}s")
print(f"CPU-bound threaded:   {threaded_time:.4f}s")
print(f"Threaded is {'slower' if threaded_time >= sequential_time else 'faster'} (GIL contention)")
```

**Expected output** (approximate):
```
CPU-bound sequential: 0.08s
CPU-bound threaded:   0.09s
Threaded is slower (GIL contention)
```

The threaded version is equal or slower because all four threads compete for the same GIL. The overhead of acquiring/releasing the GIL and context switching adds up.

### Part 4: I/O-Bound Demo -- Threading Helps

Now let's simulate I/O-bound work with `time.sleep()`. When a thread calls `time.sleep()`, it **releases the GIL**, allowing other threads to run.

```python
def io_work(duration: float = 0.01) -> None:
    """Simulated I/O -- GIL is released during sleep."""
    time.sleep(duration)

IO_TASKS = 20

# --- Sequential ---
start = time.perf_counter()
for _ in range(IO_TASKS):
    io_work()
sequential_io = time.perf_counter() - start

# --- Threaded ---
start = time.perf_counter()
threads = [threading.Thread(target=io_work) for _ in range(IO_TASKS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
threaded_io = time.perf_counter() - start

speedup = sequential_io / threaded_io
print(f"I/O-bound sequential: {sequential_io:.4f}s")
print(f"I/O-bound threaded:   {threaded_io:.4f}s")
print(f"Speedup: {speedup:.1f}x (GIL released during I/O)")
```

**Expected output** (approximate):
```
I/O-bound sequential: 0.20s
I/O-bound threaded:   0.01s
Speedup: 15.0x (GIL released during I/O)
```

All 20 threads sleep concurrently -- the total time is roughly `max(sleep_times)` not `sum(sleep_times)`.

### Part 5: Mixed Workloads -- The Real World

Most real programs do both CPU and I/O. A web server parses requests (CPU), queries a database (I/O), renders a template (CPU), and sends the response (I/O). Threads help because the I/O portions dominate.

```python
def mixed_work(n: int = 10_000, io_time: float = 0.02) -> int:
    """CPU work + simulated I/O."""
    total = sum(i * i for i in range(n))  # CPU (GIL held)
    time.sleep(io_time)                    # I/O (GIL released)
    return total

MIXED_TASKS = 10

# --- Sequential ---
start = time.perf_counter()
for _ in range(MIXED_TASKS):
    mixed_work()
sequential_mixed = time.perf_counter() - start

# --- Threaded ---
start = time.perf_counter()
threads = [threading.Thread(target=mixed_work) for _ in range(MIXED_TASKS)]
for t in threads:
    t.start()
for t in threads:
    t.join()
threaded_mixed = time.perf_counter() - start

print(f"Mixed sequential: {sequential_mixed:.4f}s")
print(f"Mixed threaded:   {threaded_mixed:.4f}s")
print(f"Speedup: {sequential_mixed / threaded_mixed:.1f}x")
```

### Part 6: Per-Thread State and the Switch Interval

Each thread has its own **call stack** (local variables, function call chain), but all threads share the **heap** (global variables, objects, module state). The GIL doesn't protect your data structures -- it only protects CPython's internal reference counts.

```python
import sys

print(f"GIL switch interval: {sys.getswitchinterval():.4f}s ({sys.getswitchinterval()*1000:.1f}ms)")
```

The switch interval (default 5ms) controls how often a thread holding the GIL yields to allow other threads to run. You can change it with `sys.setswitchinterval()`, but there's rarely a reason to.

### Part 7: Proving the GIL with a Shared Counter

This demonstrates that the GIL does NOT make your code thread-safe. While individual bytecode operations are atomic, compound operations are not.

```python
counter = 0

def increment_many(n: int) -> None:
    global counter
    for _ in range(n):
        counter += 1  # READ + ADD + STORE = 3 bytecodes, GIL can release between them

counter = 0
threads = [threading.Thread(target=increment_many, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

expected = 4 * 100_000
print(f"Expected: {expected}, Got: {counter}, Lost: {expected - counter}")
```

**Expected output** (non-deterministic):
```
Expected: 400000, Got: 387421, Lost: 12579
```

The GIL switches between threads mid-increment (`counter += 1` is three bytecodes: LOAD, ADD, STORE), causing lost updates.

## Playground

The full playground script combines all demos with assertions and clear output:

```bash
python playground/22_the_gil_explained.py
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    CPython Process                       │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │Thread 1 │  │Thread 2 │  │Thread 3 │  │Thread 4 │  │
│  │(stack)  │  │(stack)  │  │(stack)  │  │(stack)  │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │
│       │            │            │            │         │
│       └────────────┴─────┬──────┴────────────┘         │
│                          │                              │
│                    ┌─────▼─────┐                        │
│                    │    GIL    │  ← only ONE thread     │
│                    │  (mutex)  │    holds this at a     │
│                    └─────┬─────┘    time                │
│                          │                              │
│              ┌───────────▼───────────┐                  │
│              │  Python Bytecode      │                  │
│              │  Interpreter Loop     │                  │
│              └───────────┬───────────┘                  │
│                          │                              │
│              ┌───────────▼───────────┐                  │
│              │  Shared Heap          │                  │
│              │  (objects, globals,   │                  │
│              │   reference counts)   │                  │
│              └───────────────────────┘                  │
└─────────────────────────────────────────────────────────┘

CPU-bound:  Thread holds GIL → other threads WAIT
I/O-bound:  Thread releases GIL → other threads RUN
```

## Exercises

1. **Vary the workload size:** Change `WORKLOAD` from 200,000 to 50,000 and 1,000,000. How does the CPU-bound ratio change?
2. **Increase I/O tasks:** Change `IO_TASKS` to 100. Does the speedup increase proportionally?
3. **Change switch interval:** Call `sys.setswitchinterval(0.0001)` before the shared counter test. Does it lose more or fewer updates?
4. **Thread count vs. CPU ratio:** Run the CPU-bound test with 2, 4, 8, and 16 threads. Plot the slowdown.

## What's Next

In [Kata 23 -- Thread Synchronization](./23-thread-synchronization.md), we'll learn how to protect shared state with `Lock`, `RLock`, `Condition`, and `Semaphore` -- the tools that make multithreaded code correct despite the GIL's limitations.

---

[prev: 21-threading-basics](./21-threading-basics.md) | [next: 23-thread-synchronization](./23-thread-synchronization.md)
