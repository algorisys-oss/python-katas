"""
Kata 28 -- Async Iterators & Generators
Run: python playground/28_async_iterators.py

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
        return self

    async def __anext__(self) -> str:
        """Return next item, simulating async I/O."""
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        await asyncio.sleep(0.01)  # Simulate I/O delay
        return f"[stream] {item}"


async def demo_async_iterator():
    """Demonstrate async iterator protocol with async for."""
    sensor_ids = [f"sensor-{i:03d}" for i in range(1, 6)]

    print("  Reading from async data stream...")

    collected = []
    stream = AsyncDataStream(sensor_ids)
    async for value in stream:
        print(f"  Received: {value}")
        collected.append(value)

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
    for page in range(1, total_pages + 1):
        await asyncio.sleep(0.01)  # Simulate API call
        items = [f"user_{page}_{i}" for i in range(3)]
        yield {"page": page, "data": items}


async def demo_async_generator():
    """Demonstrate async generators for lazy async data production."""
    print("  Fetching paginated data from /api/users...")

    all_items = []
    page_count = 0

    async for result in paginated_fetch("/api/users", total_pages=4):
        page_count += 1
        print(f"  Page {result['page']}: {result['data']}")
        all_items.extend(result["data"])

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
        print(f"  Opening connection to {self.name}...")
        await asyncio.sleep(0.01)
        self.active = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Simulate async connection teardown."""
        print(f"  Closing connection to {self.name}...")
        await asyncio.sleep(0.01)
        self.active = False
        return False  # Don't suppress exceptions

    async def query(self, n: int) -> list[str]:
        """Simulate an async database query."""
        await asyncio.sleep(0.01)
        return [f"result_{i}" for i in range(n)]


async def demo_async_context_manager():
    """Demonstrate async context manager with async with."""
    async with AsyncConnection("db-primary") as conn:
        print(f"  Connection {conn.name} active: {conn.active}")
        assert conn.active is True

        results = await conn.query(3)
        print(f"  Queried: {results}")
        assert len(results) == 3

    print(f"  Connection {conn.name} active after close: {conn.active}")
    assert conn.active is False

    print("  Resource cleanup verified.")


# ===========================================================================
# SECTION 4: contextlib.asynccontextmanager
# ===========================================================================

@asynccontextmanager
async def managed_resource(name: str):
    """Acquire and release a resource using the decorator shortcut."""
    print(f"  Acquiring {name}...")
    await asyncio.sleep(0.01)
    resource = {"name": name, "active": True}
    try:
        yield resource
    finally:
        await asyncio.sleep(0.01)
        resource["active"] = False
        print(f"  Released {name}")


async def demo_asynccontextmanager():
    """Demonstrate the decorator-based async context manager."""
    async with managed_resource("cache-pool") as pool:
        print(f"  Cache pool active: {pool['active']}")
        assert pool["active"] is True

    print(f"  Cache pool active after release: {pool['active']}")
    assert pool["active"] is False

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
    # Async list comprehension
    squares = [x * x async for x in async_range(5)]
    print(f"  Squares: {squares}")
    assert squares == [0, 1, 4, 9, 16]

    # Async list comprehension with filter
    evens = [x async for x in async_range(10) if x % 2 == 0]
    print(f"  Evens: {evens}")
    assert evens == [0, 2, 4, 6, 8]

    # Async set comprehension
    unique_mods = {x % 3 async for x in async_range(9)}
    print(f"  Unique mod 3: {unique_mods}")
    assert unique_mods == {0, 1, 2}

    # Async dict comprehension
    name_map = {x: f"item_{x}" async for x in async_range(4)}
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
    async with managed_resource("sensor-hub") as hub:
        assert hub["active"] is True

        # Use async comprehension to collect readings from async generator
        readings = [
            reading async for reading in sensor_readings(hub["name"], 3)
        ]

        for r in readings:
            print(f"  [{r['hub']}] reading: temp={r['temp']}")

    assert hub["active"] is False

    assert len(readings) == 3
    avg_temp = sum(r["temp"] for r in readings) / len(readings)
    print(f"  Processed {len(readings)} readings. Average temp: {avg_temp:.2f}")
    assert abs(avg_temp - 20.5) < 0.01

    print("  Combined async patterns work together.")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

async def main():
    # --- Section 1: Async Iterator ---
    print("--- Section 1: Async Iterator (Data Stream) ---")
    await demo_async_iterator()
    print()

    # --- Section 2: Async Generator ---
    print("--- Section 2: Async Generator (Paginated API) ---")
    await demo_async_generator()
    print()

    # --- Section 3: Async Context Manager ---
    print("--- Section 3: Async Context Manager (Resource Management) ---")
    await demo_async_context_manager()
    print()

    # --- Section 4: contextlib.asynccontextmanager ---
    print("--- Section 4: contextlib.asynccontextmanager ---")
    await demo_asynccontextmanager()
    print()

    # --- Section 5: Async Comprehensions ---
    print("--- Section 5: Async Comprehensions ---")
    await demo_async_comprehensions()
    print()

    # --- Section 6: Combining Patterns ---
    print("--- Section 6: Combining Patterns ---")
    await demo_combined()
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
    print("All 6 sections passed. Async iterators & generators mastered!")


if __name__ == "__main__":
    asyncio.run(main())
