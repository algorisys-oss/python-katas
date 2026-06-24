# Kata 24 -- Multiprocessing

[prev: 23-thread-synchronization](./23-thread-synchronization.md) | [next: 25-concurrent-futures](./25-concurrent-futures.md)

---

## What We're Building

A parallel computation toolkit using Python's `multiprocessing` module. Unlike threads (which share the GIL), multiprocessing spawns **separate OS processes**, each with its own Python interpreter and memory space. This gives you true parallelism for CPU-bound work -- but requires explicit mechanisms for inter-process communication and shared state.

We'll build three things:
1. **CPU-bound parallel computation** with `Pool` -- distribute work across cores
2. **Inter-process communication** with `Queue` and `Pipe` -- pass data between processes
3. **Shared counter** with `Value` + `Lock` -- safely share mutable state across processes

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `Process` | Spawns a new OS process | When you need a single background worker |
| `Pool` | Manages a pool of worker processes | Parallel map/apply over data |
| `Queue` | Thread/process-safe FIFO queue | Producer-consumer across processes |
| `Pipe` | Two-way connection between two processes | Fast point-to-point communication |
| `Value` / `Array` | Shared memory for simple types | Counters, flags, small arrays |
| `Manager` | Proxy objects for complex shared state | Shared dicts, lists across processes |
| `Lock` | Mutual exclusion for shared resources | Protecting shared `Value`/`Array` |

### When to Use Multiprocessing vs Threading

| Factor | Threading | Multiprocessing |
|---|---|---|
| **GIL** | Blocked by GIL for CPU work | Bypasses GIL entirely |
| **Best for** | I/O-bound (network, disk) | CPU-bound (math, data processing) |
| **Memory** | Shared (easy, but dangerous) | Separate (safe, but requires IPC) |
| **Overhead** | Low (lightweight threads) | High (full process per worker) |
| **Data sharing** | Direct attribute access | Queue, Pipe, Value, Manager |
| **Debugging** | Harder (race conditions) | Easier (isolated processes) |

**Rule of thumb:** Use threading for I/O-bound tasks, multiprocessing for CPU-bound tasks. When in doubt, `concurrent.futures` (Kata 25) provides a unified interface for both.

## The Code

### 1. CPU-Bound Parallel Computation with Pool

`Pool` is the workhorse of multiprocessing. It manages a fixed number of worker processes and distributes tasks across them.

```python
from multiprocessing import Pool

def square(n: int) -> int:
    """CPU-bound work: compute n squared."""
    return n * n

if __name__ == "__main__":
    numbers = list(range(20))

    # Pool.map() distributes work across processes
    with Pool(processes=4) as pool:
        results = pool.map(square, numbers)

    print(f"Squares: {results}")
    # → Squares: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, ...]
```

Key `Pool` methods:
- **`map(func, iterable)`** -- parallel version of `map()`, blocks until done
- **`map_async(func, iterable)`** -- non-blocking, returns `AsyncResult`
- **`apply(func, args)`** -- run a single call in a worker, blocks
- **`apply_async(func, args)`** -- non-blocking single call
- **`starmap(func, iterable)`** -- like `map()` but unpacks argument tuples

### 2. Inter-Process Communication with Queue

`Queue` is a process-safe FIFO queue. Producers `put()` items, consumers `get()` them.

```python
from multiprocessing import Process, Queue

def producer(q: Queue, items: list[str]) -> None:
    for item in items:
        q.put(item)
    q.put(None)  # sentinel to signal "done"

def consumer(q: Queue, results: list) -> None:
    while True:
        item = q.get()
        if item is None:
            break
        results.append(item.upper())

if __name__ == "__main__":
    q: Queue = Queue()
    # Note: can't share a plain list across processes -- use Manager or Queue
```

### 3. Inter-Process Communication with Pipe

`Pipe()` creates a pair of connected `Connection` objects. Faster than `Queue` for two-process communication.

```python
from multiprocessing import Process, Pipe

def sender(conn):
    conn.send({"type": "greeting", "msg": "hello"})
    conn.send({"type": "data", "values": [1, 2, 3]})
    conn.close()

def receiver(conn):
    while True:
        try:
            msg = conn.recv()
            print(f"Received: {msg}")
        except EOFError:
            break

if __name__ == "__main__":
    parent_conn, child_conn = Pipe()
    # sender uses one end, receiver uses the other
```

### 4. Shared Counter with Value + Lock

`Value` creates a shared memory scalar. Without a `Lock`, concurrent increments cause race conditions -- just like threading.

```python
from multiprocessing import Process, Value, Lock

def increment(counter: Value, lock: Lock, n: int) -> None:
    for _ in range(n):
        with lock:
            counter.value += 1

if __name__ == "__main__":
    counter = Value('i', 0)  # 'i' = signed int, initial value 0
    lock = Lock()
    # spawn processes that all increment the same counter
```

Type codes for `Value`:
- `'i'` -- signed int
- `'d'` -- double (float)
- `'c'` -- char
- `'b'` -- signed byte

### 5. Manager for Complex Shared State

`Manager` creates a server process that hosts Python objects (dicts, lists) and exposes them via proxies. Slower than `Value`/`Array` but supports any Python type.

```python
from multiprocessing import Process, Manager

def worker(shared_dict, key, value):
    shared_dict[key] = value

if __name__ == "__main__":
    with Manager() as manager:
        d = manager.dict()
        processes = [
            Process(target=worker, args=(d, f"key_{i}", i * 10))
            for i in range(4)
        ]
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        print(dict(d))  # → {'key_0': 0, 'key_1': 10, 'key_2': 20, 'key_3': 30}
```

## Playground

```bash
python playground/24_multiprocessing.py
```

## How It Works

```
Main Process
├── Pool(processes=4)
│   ├── Worker 0 ──→ square(0), square(4), square(8), ...
│   ├── Worker 1 ──→ square(1), square(5), square(9), ...
│   ├── Worker 2 ──→ square(2), square(6), square(10), ...
│   └── Worker 3 ──→ square(3), square(7), square(11), ...
│
├── Queue (producer-consumer)
│   Producer ──put()──→ [Queue] ──get()──→ Consumer
│
├── Pipe (point-to-point)
│   Process A ──send()──→ [Connection] ──recv()──→ Process B
│
└── Value + Lock (shared memory)
    Process 1 ──lock──→ counter.value += 1 ──unlock──→
    Process 2 ──lock──→ counter.value += 1 ──unlock──→
```

**Memory model:** Each process gets its own copy of the Python interpreter and memory space. Objects passed to child processes are **pickled** (serialized) and **unpickled** in the child. This means:
- Lambdas and inner functions cannot be passed (not picklable)
- Large objects are expensive to transfer (serialization overhead)
- `Value`/`Array` use shared memory (no pickle, fast)
- `Queue`/`Pipe` pickle each message

## Exercises

1. **Parallel sum:** Use `Pool.map()` to compute the sum of squares of the first 1000 numbers in parallel by splitting the range into chunks
2. **Pipeline:** Create a 3-stage pipeline using Queues: Stage 1 generates numbers, Stage 2 squares them, Stage 3 collects results
3. **Shared array:** Use `Array('d', 10)` to create a shared array of 10 doubles, have multiple processes write to different indices
4. **Manager dict:** Use a `Manager().dict()` to collect results from multiple worker processes, each computing a different value
5. **Error handling:** Add error handling to a Pool computation -- what happens when a worker raises an exception?

## What's Next

In [Kata 25 -- Concurrent Futures](./25-concurrent-futures.md), we'll learn `concurrent.futures` -- a high-level interface that unifies threading and multiprocessing behind `ThreadPoolExecutor` and `ProcessPoolExecutor`, with `Future` objects for managing async results.

---

[prev: 23-thread-synchronization](./23-thread-synchronization.md) | [next: 25-concurrent-futures](./25-concurrent-futures.md)
