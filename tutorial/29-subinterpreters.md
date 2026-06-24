# Kata 29 -- Subinterpreters

[prev: 28-async-iterators](./28-async-iterators.md) | [next: 30-free-threaded-python](./30-free-threaded-python.md)

---

## What We're Building

A hands-on exploration of Python's **subinterpreters** -- a concurrency model that gives you true parallelism like `multiprocessing` but without the overhead of spawning separate OS processes. Each subinterpreter gets its own GIL, its own `__main__` module, and its own global state, while sharing the same process memory space.

We'll build four practical demos:
1. **Creating and running subinterpreters** -- spawn isolated Python interpreters within a single process
2. **Channel-based communication** -- send data between interpreters using `interpreters.channels`
3. **True parallelism** -- demonstrate that subinterpreters bypass the GIL for CPU-bound work
4. **Comparison with threading and multiprocessing** -- understand the tradeoffs

> **Note:** Subinterpreters (PEP 734) shipped as the stdlib **`concurrent.interpreters`** module in **Python 3.14** -- import it with `from concurrent import interpreters`. On Python 3.12/3.13 the API was experimental and only reachable via the private `_interpreters` module (or a standalone backport), and some builds omit it entirely. All examples in this kata gracefully handle the case where the module is unavailable.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| PEP 734 (`concurrent.interpreters`) | High-level API for subinterpreters | True parallelism without process overhead |
| `interpreters.create()` | Create a new subinterpreter | When you need isolated execution |
| `interpreters.list_all()` | List all active interpreters | Debugging, monitoring |
| `interp.exec(code)` | Execute a code string in a subinterpreter | Running isolated computations |
| `interp.call(fn, *args)` | Call a picklable function in a subinterpreter | Running isolated callables |
| `interp.close()` | Destroy a subinterpreter | Cleanup after use |
| Separate GIL per interpreter | Each interpreter has its own GIL | CPU-bound parallelism |
| `interpreters.create_queue()` | Thread-safe queue for inter-interpreter data | Structured data exchange |
| Isolation model | No shared Python objects between interpreters | Safety, no race conditions on Python objects |

## The Code

### Why Subinterpreters?

Python's concurrency landscape has a gap:

```
Threading          Multiprocessing      Subinterpreters
─────────          ───────────────      ───────────────
Same process       Separate processes   Same process
Shared GIL         Separate GILs        Separate GILs
No true parallel   True parallel         True parallel
Low overhead       High overhead         Medium overhead
Shared objects     Pickle to share       Channels to share
Race conditions    No shared state       No shared state
```

Subinterpreters combine the best of both worlds: true parallelism (separate GILs) with low overhead (same process, no pickling of code).

### Creating a Subinterpreter

```python
from concurrent import interpreters

# Create a new subinterpreter
interp = interpreters.create()

# Run code in it
interp.exec('x = 1 + 2')
interp.exec('print(f"Result: {x}")')  # prints "Result: 3"

# The main interpreter can't see x -- it's isolated
# x would raise NameError here in the main interpreter

# Clean up
interp.close()
```

Key points:
- Each subinterpreter is a fully isolated Python environment
- Variables defined in one interpreter are invisible to others
- `exec()` runs a string of Python code in the subinterpreter (use `call()` to invoke a function)
- Always `close()` interpreters when done (or use them as context managers)

### Listing Interpreters

```python
from concurrent import interpreters

# The main interpreter is always ID 0
all_interps = interpreters.list_all()
print(f"Main interpreter: {all_interps[0].id}")

# Create a few more
interp1 = interpreters.create()
interp2 = interpreters.create()

all_interps = interpreters.list_all()
print(f"Active interpreters: {len(all_interps)}")
# → Active interpreters: 3

interp1.close()
interp2.close()
```

### Channel Communication

Subinterpreters can communicate through channels -- a send/receive pair for passing data:

```python
from concurrent import interpreters

# Create a queue for communication
queue = interpreters.create_queue()

interp = interpreters.create()

# The subinterpreter puts data on the queue
interp.exec("""
from concurrent import interpreters
result = sum(range(1000))
""")

# For simple data, we can use exec() and capture via shared queues
# The queue supports basic types: str, int, float, bytes, bool, None
```

Channels support these types (shareable across interpreters):
- `str`, `bytes`, `int`, `float`, `bool`, `None`
- These are copied (not shared) between interpreters

### Separate GIL -- True Parallelism

The killer feature of subinterpreters is that each one has its own GIL:

```python
from concurrent import interpreters
import threading
import time

def run_in_subinterpreter(code: str):
    """Create a subinterpreter, run code, close it."""
    interp = interpreters.create()
    interp.exec(code)
    interp.close()

cpu_code = """
total = 0
for i in range(1_000_000):
    total += i * i
"""

# Run two CPU-bound tasks in parallel using threads + subinterpreters
# Each subinterpreter has its own GIL, so they truly run in parallel
start = time.perf_counter()
t1 = threading.Thread(target=run_in_subinterpreter, args=(cpu_code,))
t2 = threading.Thread(target=run_in_subinterpreter, args=(cpu_code,))
t1.start()
t2.start()
t1.join()
t2.join()
parallel_time = time.perf_counter() - start
```

With regular threading, two CPU-bound threads fight over one GIL and get no speedup. With subinterpreters, each thread's interpreter has its own GIL, enabling true parallelism.

### Comparison: Threading vs Multiprocessing vs Subinterpreters

```
                    Threading    Multiprocessing   Subinterpreters
─────────────────   ─────────    ───────────────   ───────────────
Startup cost        ~0.001s      ~0.05-0.1s        ~0.001-0.01s
Memory overhead     Minimal      Full process       Minimal
GIL                 Shared       Separate           Separate
CPU parallelism     No           Yes                Yes
Data sharing        Direct       Pickle/shared mem  Channels
Isolation           None         Full (OS-level)    Python-level
Object sharing      Yes          No (copy)          No (copy)
Best for            I/O-bound    CPU-bound          CPU-bound (lightweight)
```

## Playground

Run the full demonstration:

```bash
python playground/29_subinterpreters.py
```

```
--- Section 1: Creating Subinterpreters ---
  NOTE: interpreters module not available in this Python build.
  This is expected -- the API is experimental in Python 3.12/3.13.
  Skipping subinterpreter demos. See tutorial for concepts.

  OR (if available):

  Created subinterpreter with id: 1
  Active interpreters: 2 (main + 1 sub)
  Subinterpreter executed code successfully
  Closed subinterpreter. Active: 1
  Subinterpreters provide isolated Python execution environments.

--- Section 2: Running Code in Subinterpreters ---
  Ran computation in subinterpreter: completed
  Each subinterpreter has its own namespace -- full isolation.

--- Section 3: Parallel Execution with Subinterpreters ---
  Running 2 CPU-bound tasks...
  Sequential time: 0.XXs
  Parallel time (subinterpreters + threads): 0.XXs
  Subinterpreters enable true parallelism (separate GILs).

--- Section 4: Comparison with Threading ---
  Threading (2 CPU-bound tasks, shared GIL): 0.XXs
  Subinterpreters (2 CPU-bound tasks, separate GILs): 0.XXs
  Subinterpreters can outperform threading for CPU-bound work.

--- Summary ---
Subinterpreters provide true parallelism within a single process:
  - Each interpreter has its own GIL (no contention)
  - Lower overhead than multiprocessing (no process spawn)
  - Full isolation (no shared Python objects)
  - Channel-based communication for data exchange
  - Stdlib API since Python 3.14 (PEP 734)
  - Best for: CPU-bound tasks needing lightweight parallelism

All sections completed. Subinterpreters explored!
```

## How It Works

```
PROCESS MEMORY SPACE
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Interpreter 0│  │ Interpreter 1│                 │
│  │ (main)       │  │ (sub)        │                 │
│  │              │  │              │                 │
│  │  ┌────────┐  │  │  ┌────────┐  │                 │
│  │  │ GIL  0 │  │  │  │ GIL  1 │  │  ← Separate    │
│  │  └────────┘  │  │  └────────┘  │    GILs!        │
│  │              │  │              │                 │
│  │  globals     │  │  globals     │  ← Separate     │
│  │  __main__    │  │  __main__    │    namespaces    │
│  │  imports     │  │  imports     │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                         │
│         │   ┌─────────┐   │                         │
│         └──►│ Channel │◄──┘  ← Communication        │
│             │ (Queue) │      via channels            │
│             └─────────┘                             │
│                                                     │
│  Shared: C extensions, file descriptors, OS memory  │
│  Isolated: Python objects, GIL, module state        │
└─────────────────────────────────────────────────────┘

COMPARISON:

  Threading:           1 process, 1 GIL, N threads
  Multiprocessing:     N processes, N GILs, N memory spaces
  Subinterpreters:     1 process, N GILs, N namespaces  ← sweet spot

EVOLUTION OF PYTHON PARALLELISM:

  Kata 21: Threading      → concurrent I/O, shared GIL
  Kata 22: The GIL        → why threads can't parallelize CPU work
  Kata 24: Multiprocessing → true parallelism, heavy overhead
  Kata 29: Subinterpreters → true parallelism, light overhead  ← YOU ARE HERE
  Kata 30: Free-threaded   → no GIL at all (PEP 703)
```

## Exercises

### Exercise 1: Subinterpreter pool

Build a simple pool of subinterpreters that can execute tasks:

```python
def subinterpreter_pool(task_code: str, count: int = 4):
    """Create `count` subinterpreters, run task_code in each, close them."""
    # TODO: create `count` subinterpreters
    # TODO: run task_code in each one (use threads for parallelism)
    # TODO: close all interpreters
    # HINT: combine threading.Thread with interpreters.create()
    ...

subinterpreter_pool("total = sum(range(100_000))", count=4)
```

### Exercise 2: Producer-consumer with channels

Build a producer-consumer pattern using subinterpreters and queues:

```python
def producer_consumer():
    """Producer subinterpreter sends data, consumer subinterpreter receives."""
    # TODO: create a Queue
    # TODO: create a producer interpreter that puts items on the queue
    # TODO: create a consumer interpreter that gets items from the queue
    # HINT: interpreters.create_queue() for communication
    ...
```

### Exercise 3: Benchmark comparison

Write a benchmark that compares threading vs subinterpreters for CPU-bound work:

```python
def benchmark_comparison(iterations: int = 500_000):
    """Compare threading vs subinterpreters for CPU-bound work."""
    # TODO: run the same CPU-bound task with:
    #   1. Two regular threads (shared GIL)
    #   2. Two threads with subinterpreters (separate GILs)
    # TODO: print timing comparison
    # HINT: time.perf_counter() for accurate timing
    ...
```

## What's Next

In [Kata 30 -- Free-Threaded Python](./30-free-threaded-python.md), we'll explore PEP 703 and the experimental no-GIL build of Python. While subinterpreters give each interpreter its own GIL, free-threaded Python removes the GIL entirely -- allowing regular threads to run truly in parallel. This is the future of Python concurrency.

---

[prev: 28-async-iterators](./28-async-iterators.md) | [next: 30-free-threaded-python](./30-free-threaded-python.md)
