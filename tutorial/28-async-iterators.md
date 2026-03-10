# Kata 28 -- Async Iterators & Generators

[prev: 27-async-io-patterns](./27-async-io-patterns.md) | [next: 29-subinterpreters](./29-subinterpreters.md)

---

## What We're Building

An async data processing toolkit that demonstrates Python's async iteration protocol -- the async counterparts to `__iter__`/`__next__`, generators, comprehensions, and context managers. These are the building blocks for handling streaming data, paginated APIs, and resource lifecycle management in async code.

We'll build four practical demos:
1. **Async iterator class** with `__aiter__`/`__anext__` -- a data stream that yields values asynchronously
2. **Async generator for paginated API** -- `async def` + `yield` to lazily fetch pages on demand
3. **Async context manager** -- resource acquisition/release with `async with` and `contextlib.asynccontextmanager`
4. **Async comprehensions** -- `async for` in list/set/dict comprehensions for concise data transformation

These patterns are everywhere in modern Python -- database cursors, HTTP streaming, WebSocket message loops, and ASGI middleware all use async iteration under the hood.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `__aiter__` / `__anext__` | Async iterator protocol | Custom async data sources |
| `async for` | Iterate over async iterables | Consuming streams, paginated APIs |
| `async def` + `yield` | Async generator function | Lazy async data production |
| `async with` | Async context manager protocol | Resource lifecycle (connections, files) |
| `__aenter__` / `__aexit__` | Async context manager methods | Custom async resource managers |
| `contextlib.asynccontextmanager` | Decorator for async context managers | Quick async resource wrappers |
| Async comprehensions | `[x async for x in aiter]` | Collecting async results concisely |
| `StopAsyncIteration` | Signals end of async iteration | Returned by `__anext__` when exhausted |

## The Code

### Async Iterator Protocol -- `__aiter__` / `__anext__`

Just as `__iter__`/`__next__` power synchronous `for` loops, `__aiter__`/`__anext__` power `async for` loops. The key difference: `__anext__` is a coroutine that can `await` I/O.

```python
import asyncio

class AsyncDataStream:
    """Async iterator that simulates reading from a data source."""

    def __init__(self, items: list[str]):
        self._items = items
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        await asyncio.sleep(0.01)  # Simulate I/O delay
        return f"[stream] {item}"

# Usage with async for
async def main():
    stream = AsyncDataStream(["alpha", "beta", "gamma"])
    async for value in stream:
        print(value)
```

Key points:
- `__aiter__` returns the iterator object (usually `self`) -- it is **not** a coroutine
- `__anext__` is an `async` method -- it can `await` I/O operations
- Raise `StopAsyncIteration` to signal the end (not `StopIteration`)
- Use `async for` to consume -- you cannot use regular `for` with async iterators

### Async Generators -- `async def` + `yield`

Async generators are the easiest way to create async iterables, just like regular generators simplify `__iter__`/`__next__`:

```python
async def paginated_fetch(url: str, total_pages: int):
    """Async generator that fetches pages one at a time."""
    for page in range(1, total_pages + 1):
        await asyncio.sleep(0.01)  # Simulate API call
        data = [f"{url}/item_{page}_{i}" for i in range(3)]
        yield {"page": page, "data": data}

async def main():
    async for page_result in paginated_fetch("/api/users", 3):
        print(f"Page {page_result['page']}: {page_result['data']}")
```

Why async generators over classes:
- Far less boilerplate (no `__aiter__`, `__anext__`, index tracking)
- Local variables maintain state naturally between yields
- Cleanup code after the last `yield` runs when the generator is closed

### Async Context Managers -- `async with`

Async context managers handle resources that require async setup/teardown (database connections, HTTP sessions, file handles):

```python
class AsyncConnection:
    """Async context manager for a simulated database connection."""

    def __init__(self, name: str):
        self.name = name
        self.connected = False

    async def __aenter__(self):
        await asyncio.sleep(0.01)  # Simulate connection setup
        self.connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(0.01)  # Simulate cleanup
        self.connected = False
        return False  # Don't suppress exceptions

async def main():
    async with AsyncConnection("db-1") as conn:
        print(f"Connected: {conn.connected}")  # True
    print(f"Connected: {conn.connected}")  # False
```

### `contextlib.asynccontextmanager` -- Decorator Shortcut

For simple cases, the decorator approach is more concise:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource(name: str):
    """Acquire and release a resource using decorator syntax."""
    print(f"  Acquiring {name}...")
    await asyncio.sleep(0.01)
    resource = {"name": name, "active": True}
    try:
        yield resource  # Caller gets this value
    finally:
        await asyncio.sleep(0.01)
        resource["active"] = False
        print(f"  Released {name}")
```

The `yield` splits the context manager into setup (before) and teardown (after). The `finally` block ensures cleanup even if an exception occurs.

### Async Comprehensions

Python supports `async for` inside comprehensions for concise async data collection:

```python
async def async_range(n: int):
    """Simple async generator for demonstration."""
    for i in range(n):
        await asyncio.sleep(0.01)
        yield i

async def main():
    # Async list comprehension
    squares = [x * x async for x in async_range(5)]

    # Async list comprehension with filter
    evens = [x async for x in async_range(10) if x % 2 == 0]

    # Async set comprehension
    unique = {x % 3 async for x in async_range(9)}

    # Async dict comprehension
    mapping = {x: x * x async for x in async_range(5)}
```

Note: async comprehensions can **only** be used inside `async def` functions.

## Playground

Run the full demonstration:

```bash
python playground/28_async_iterators.py
```

```
--- Section 1: Async Iterator (Data Stream) ---
  Reading from async data stream...
  Received: [stream] sensor-001
  Received: [stream] sensor-002
  Received: [stream] sensor-003
  Received: [stream] sensor-004
  Received: [stream] sensor-005
  Collected 5 items from async data stream.

--- Section 2: Async Generator (Paginated API) ---
  Fetching paginated data from /api/users...
  Page 1: ['user_1_0', 'user_1_1', 'user_1_2']
  Page 2: ['user_2_0', 'user_2_1', 'user_2_2']
  Page 3: ['user_3_0', 'user_3_1', 'user_3_2']
  Page 4: ['user_4_0', 'user_4_1', 'user_4_2']
  Fetched 4 pages with 12 total items.

--- Section 3: Async Context Manager (Resource Management) ---
  Opening connection to db-primary...
  Connection db-primary active: True
  Queried: [result_0, result_1, result_2]
  Closing connection to db-primary...
  Connection db-primary active after close: False
  Resource cleanup verified.

--- Section 4: contextlib.asynccontextmanager ---
  Acquiring cache-pool...
  Cache pool active: True
  Released cache-pool
  Cache pool active after release: False
  Decorator-based async context manager works.

--- Section 5: Async Comprehensions ---
  Squares: [0, 1, 4, 9, 16]
  Evens: [0, 2, 4, 6, 8]
  Unique mod 3: {0, 1, 2}
  Name map: {0: 'item_0', 1: 'item_1', 2: 'item_2', 3: 'item_3'}
  All async comprehension types verified.

--- Section 6: Combining Patterns ---
  Acquiring sensor-hub...
  [sensor-hub] reading: temp=20.0
  [sensor-hub] reading: temp=20.5
  [sensor-hub] reading: temp=21.0
  Released sensor-hub
  Processed 3 readings. Average temp: 20.50
  Combined async patterns work together.

--- Summary ---
Async iteration provides non-blocking data streaming:
  - __aiter__/__anext__: async iterator protocol (async for)
  - async def + yield: async generators (lazy async production)
  - __aenter__/__aexit__: async context managers (async with)
  - asynccontextmanager: decorator shortcut for simple cases
  - async comprehensions: [x async for x in aiter] for concise collection
  - StopAsyncIteration: signals end of async iteration

All 6 sections passed. Async iterators & generators mastered!
```

## How It Works

```
SYNC PROTOCOL                    ASYNC PROTOCOL

  __iter__()                       __aiter__()
  __next__()                       async __anext__()
  StopIteration                    StopAsyncIteration
  for x in iterable:               async for x in aitable:

  def gen():                       async def agen():
      yield value                      yield value    (can await between yields)

  __enter__/__exit__               async __aenter__/async __aexit__
  with resource:                   async with resource:

  [x for x in iter]               [x async for x in aiter]

  ASYNC GENERATOR LIFECYCLE:

  caller                          async generator
    |                                 |
    |--- async for x in gen() ------->|
    |                                 |--- await I/O
    |                                 |<-- I/O complete
    |<-------- yield value -----------|
    |                                 |    (suspended)
    |--- next iteration ------------->|
    |                                 |--- await I/O
    |<-------- yield value -----------|
    |                                 |
    |--- (loop ends) ---------------->|
    |                                 |--- StopAsyncIteration

  ASYNC CONTEXT MANAGER FLOW:

  async with resource as r:
      │
      ├── __aenter__()  →  await setup  →  return resource
      │
      ├── (use resource)
      │
      └── __aexit__()   →  await cleanup  →  done
```

## Exercises

### Exercise 1: Async file reader

Build an async iterator that reads "lines" from a simulated file:

```python
class AsyncFileReader:
    """Async iterator that simulates reading lines from a file."""

    def __init__(self, lines: list[str]):
        # TODO: store lines and initialize index
        ...

    def __aiter__(self):
        # TODO: return self
        ...

    async def __anext__(self) -> str:
        # TODO: return next line with simulated I/O delay
        # Raise StopAsyncIteration when exhausted
        ...

async def test():
    reader = AsyncFileReader(["line 1", "line 2", "line 3"])
    collected = []
    async for line in reader:
        collected.append(line)
    assert collected == ["line 1", "line 2", "line 3"]
```

### Exercise 2: Async retry generator

Build an async generator that retries a failing operation:

```python
async def retry_fetch(url: str, max_retries: int = 3):
    """Async generator that yields retry attempts until success."""
    # TODO: for each attempt, simulate a fetch (await asyncio.sleep)
    # Yield {"attempt": n, "status": "error"} for failures
    # Yield {"attempt": n, "status": "ok", "data": ...} on success
    # Simulate: fail for attempts < max_retries, succeed on last
    ...
```

### Exercise 3: Async pool context manager

Build an async context manager that manages a pool of connections:

```python
@asynccontextmanager
async def connection_pool(size: int):
    """Manage a pool of async connections."""
    # TODO: create `size` connections (simulate with asyncio.sleep)
    # yield the pool (list of connection dicts)
    # cleanup: close all connections in finally block
    ...
```

## What's Next

In [Kata 29 -- Subinterpreters](./29-subinterpreters.md), we'll explore Python's subinterpreter API -- a way to achieve true parallelism within a single process by running multiple Python interpreters with isolated state, bridging the gap between threading (shared memory, GIL-limited) and multiprocessing (separate processes, high overhead).

---

[prev: 27-async-io-patterns](./27-async-io-patterns.md) | [next: 29-subinterpreters](./29-subinterpreters.md)
