"""
Kata 28 -- Async Iterators & Generators
Run: python playground/skeletons/28_async_iterators.py

Async iteration protocol: __aiter__/__anext__, async generators, async
comprehensions, and async context managers for streaming data and resource
lifecycle management.

IMPORTANT: All I/O is simulated with asyncio.sleep(0.01) to complete within 5 seconds.
"""

import asyncio
from contextlib import asynccontextmanager


# ===========================================================================
# SECTION 1: Async Iterator (Data Stream)
# ===========================================================================

class AsyncDataStream:
    """Async iterator that simulates reading from a sensor data stream."""

    def __init__(self, sensor_ids: list[str]):
        self._items = sensor_ids
        self._index = 0

    def __aiter__(self):
        """Return the async iterator object (not a coroutine)."""
        # TODO: return the iterator object
        # HINT: just return self, same as sync iterators
        pass

    async def __anext__(self) -> str:
        """Return next item, simulating async I/O."""
        # TODO: check if exhausted -- raise StopAsyncIteration if so
        # TODO: get current item, increment index
        # TODO: await asyncio.sleep(0.01) to simulate I/O
        # TODO: return f"[stream] {item}"
        # HINT: raise StopAsyncIteration (not StopIteration!)
        pass


async def demo_async_iterator():
    """Demonstrate async iterator protocol with async for."""
    sensor_ids = [f"sensor-{i:03d}" for i in range(1, 6)]

    print("  Reading from async data stream...")

    collected = []
    stream = AsyncDataStream(sensor_ids)
    # TODO: use 'async for value in stream:' to iterate
    # TODO: print each value and append to collected list
    # HINT: async for value in stream:
    pass

    assert len(collected) == 5
    assert collected[0] == "[stream] sensor-001"
    assert collected[4] == "[stream] sensor-005"

    print(f"  Collected {len(collected)} items from async data stream.")


# ===========================================================================
# SECTION 2: Async Generator (Paginated API)
# ===========================================================================

async def paginated_fetch(base_url: str, total_pages: int):
    """Async generator that simulates fetching paginated API results.

    Yields one page at a time -- the caller controls the pace.
    """
    # TODO: loop through pages 1..total_pages
    # TODO: await asyncio.sleep(0.01) to simulate API call
    # TODO: create items list: [f"user_{page}_{i}" for i in range(3)]
    # TODO: yield {"page": page, "data": items}
    # HINT: use 'yield' inside an 'async def' to make an async generator
    pass


async def demo_async_generator():
    """Demonstrate async generators for lazy async data production."""
    print("  Fetching paginated data from /api/users...")

    all_items = []
    page_count = 0

    # TODO: use 'async for result in paginated_fetch(...)' to consume pages
    # TODO: count pages and collect all items
    # HINT: async for result in paginated_fetch("/api/users", total_pages=4):
    pass

    assert page_count == 4
    assert len(all_items) == 12
    assert all_items[0] == "user_1_0"
    assert all_items[-1] == "user_4_2"

    print(f"  Fetched {page_count} pages with {len(all_items)} total items.")


# ===========================================================================
# SECTION 3: Async Context Manager (Resource Management)
# ===========================================================================

class AsyncConnection:
    """Async context manager for a simulated database connection."""

    def __init__(self, name: str):
        self.name = name
        self.active = False

    async def __aenter__(self):
        """Simulate async connection setup."""
        # TODO: print opening message
        # TODO: await asyncio.sleep(0.01) to simulate setup
        # TODO: set self.active = True
        # TODO: return self
        # HINT: __aenter__ must return the resource (usually self)
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Simulate async connection teardown."""
        # TODO: print closing message
        # TODO: await asyncio.sleep(0.01) to simulate cleanup
        # TODO: set self.active = False
        # TODO: return False (don't suppress exceptions)
        pass

    async def query(self, n: int) -> list[str]:
        """Simulate an async database query."""
        await asyncio.sleep(0.01)
        return [f"result_{i}" for i in range(n)]


async def demo_async_context_manager():
    """Demonstrate async context manager with async with."""
    conn = None
    # TODO: use 'async with AsyncConnection("db-primary") as conn:'
    # TODO: print connection status, run a query, print results
    # HINT: async with AsyncConnection("db-primary") as conn:
    pass

    if conn is not None:
        print(f"  Connection {conn.name} active after close: {conn.active}")
        assert conn.active is False
    else:
        raise AssertionError("conn not set -- async with block not implemented")

    print("  Resource cleanup verified.")


# ===========================================================================
# SECTION 4: contextlib.asynccontextmanager
# ===========================================================================

@asynccontextmanager
async def managed_resource(name: str):
    """Acquire and release a resource using the decorator shortcut."""
    # TODO: print acquiring message
    # TODO: await asyncio.sleep(0.01) for setup
    # TODO: create resource dict: {"name": name, "active": True}
    # TODO: yield resource inside a try/finally
    # TODO: in finally: set active=False, await cleanup, print released
    # HINT: try: yield resource  finally: resource["active"] = False
    pass


async def demo_asynccontextmanager():
    """Demonstrate the decorator-based async context manager."""
    # TODO: use 'async with managed_resource("cache-pool") as pool:'
    # TODO: verify pool is active inside the block
    # TODO: verify pool is inactive after the block
    # HINT: async with managed_resource("cache-pool") as pool:
    pass

    print("  Decorator-based async context manager works.")


# ===========================================================================
# SECTION 5: Async Comprehensions
# ===========================================================================

async def async_range(n: int):
    """Simple async generator for use in comprehensions."""
    for i in range(n):
        await asyncio.sleep(0.01)
        yield i


async def demo_async_comprehensions():
    """Demonstrate async list, set, and dict comprehensions."""
    # TODO: async list comprehension -- squares of 0..4
    # HINT: squares = [x * x async for x in async_range(5)]
    squares = []  # Replace with async comprehension

    print(f"  Squares: {squares}")
    assert squares == [0, 1, 4, 9, 16]

    # TODO: async list comprehension with filter -- even numbers from 0..9
    # HINT: evens = [x async for x in async_range(10) if x % 2 == 0]
    evens = []  # Replace with async comprehension

    print(f"  Evens: {evens}")
    assert evens == [0, 2, 4, 6, 8]

    # TODO: async set comprehension -- unique values of x % 3 for 0..8
    # HINT: unique_mods = {x % 3 async for x in async_range(9)}
    unique_mods = set()  # Replace with async comprehension

    print(f"  Unique mod 3: {unique_mods}")
    assert unique_mods == {0, 1, 2}

    # TODO: async dict comprehension -- {x: f"item_{x}" for x in 0..3}
    # HINT: name_map = {x: f"item_{x}" async for x in async_range(4)}
    name_map = {}  # Replace with async comprehension

    print(f"  Name map: {name_map}")
    assert name_map == {0: "item_0", 1: "item_1", 2: "item_2", 3: "item_3"}

    print("  All async comprehension types verified.")


# ===========================================================================
# SECTION 6: Combining Patterns
# ===========================================================================

async def sensor_readings(hub_name: str, count: int):
    """Async generator that produces sensor readings."""
    for i in range(count):
        await asyncio.sleep(0.01)
        yield {"hub": hub_name, "temp": 20.0 + i * 0.5}


async def demo_combined():
    """Combine async generator + async context manager + async comprehension."""
    # TODO: use 'async with managed_resource("sensor-hub") as hub:'
    # TODO: inside the block, use an async comprehension to collect readings
    #       from sensor_readings(hub["name"], 3)
    # TODO: print each reading and compute the average temperature
    # HINT: readings = [reading async for reading in sensor_readings(hub["name"], 3)]
    pass

    print("  Combined async patterns work together.")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

async def main():
    # --- Section 1: Async Iterator ---
    print("--- Section 1: Async Iterator (Data Stream) ---")
    try:
        await demo_async_iterator()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: Async Generator ---
    print("--- Section 2: Async Generator (Paginated API) ---")
    try:
        await demo_async_generator()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: Async Context Manager ---
    print("--- Section 3: Async Context Manager (Resource Management) ---")
    try:
        await demo_async_context_manager()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: contextlib.asynccontextmanager ---
    print("--- Section 4: contextlib.asynccontextmanager ---")
    try:
        await demo_asynccontextmanager()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: Async Comprehensions ---
    print("--- Section 5: Async Comprehensions ---")
    try:
        await demo_async_comprehensions()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 6: Combining Patterns ---
    print("--- Section 6: Combining Patterns ---")
    try:
        await demo_combined()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Async iteration provides non-blocking data streaming:")
    print("  - __aiter__/__anext__: async iterator protocol (async for)")
    print("  - async def + yield: async generators (lazy async production)")
    print("  - __aenter__/__aexit__: async context managers (async with)")
    print("  - asynccontextmanager: decorator shortcut for simple cases")
    print("  - async comprehensions: [x async for x in aiter] for concise collection")
    print("  - StopAsyncIteration: signals end of async iteration")
    print()
    print("Skeleton run complete. Implement the TODOs above to make all sections pass!")


if __name__ == "__main__":
    asyncio.run(main())
