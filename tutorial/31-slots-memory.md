# Kata 31 -- __slots__ & Memory Optimization

[prev: 30-free-threaded-python](./30-free-threaded-python.md) | [next: 32-import-system](./32-import-system.md)

---

## What We're Building

A deep dive into **Python's memory model** and `__slots__` -- the most impactful single optimization for reducing per-instance memory overhead. We'll build tools to measure, compare, and optimize object memory usage.

We'll build five demonstrations:
1. **`__dict__` vs `__slots__` comparison** -- measuring the memory difference side-by-side with `sys.getsizeof`
2. **Memory layout visualization** -- understanding how CPython stores instance attributes internally
3. **Weakref compatibility** -- making slotted classes work with `weakref` when needed
4. **Bulk object profiling** -- measuring real memory savings when creating thousands of instances
5. **When (not) to use slots** -- practical guidelines with inheritance, mixins, and dynamic attributes

`__slots__` can reduce per-instance memory by 40-60% for attribute-heavy objects. This matters when you have millions of instances (ORMs, data pipelines, game entities, scientific computing).

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `__dict__` | Per-instance attribute dictionary | Default for all regular classes |
| `__slots__` | Declare fixed attribute names, skip `__dict__` | High-volume objects where memory matters |
| `sys.getsizeof()` | Size of a single object in bytes | Quick memory measurement |
| `__weakref__` | Slot to enable weak references | Slotted classes that need `weakref` support |
| `object.__sizeof__()` | Raw object size without GC overhead | Low-level memory measurement |
| Descriptor protocol | How slots actually work under the hood | Understanding the mechanism |
| Memory profiling | Measuring total memory of object collections | Optimizing real applications |

## The Code

### Understanding `__dict__` -- The Default

Every regular Python object carries a `__dict__` -- a dictionary that stores all instance attributes:

```python
import sys

class RegularPoint:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

p = RegularPoint(1.0, 2.0, 3.0)
print(p.__dict__)          # {'x': 1.0, 'y': 2.0, 'z': 3.0}
print(sys.getsizeof(p))   # ~48 bytes (the instance itself)
print(sys.getsizeof(p.__dict__))  # ~184 bytes (the attribute dict!)
```

The `__dict__` is a full hash table -- it supports dynamic attribute creation (`p.color = "red"`), but that flexibility costs memory. Each instance carries its own dict, even if every instance has the exact same attributes.

### `__slots__` -- Fixed Attribute Layout

`__slots__` tells Python: "these are the ONLY attributes this class will have." Python replaces the per-instance `__dict__` with compact, fixed-offset storage:

```python
class SlottedPoint:
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

p = SlottedPoint(1.0, 2.0, 3.0)
print(hasattr(p, '__dict__'))  # False -- no instance dict!
print(sys.getsizeof(p))       # ~64 bytes (everything included)

# This will raise AttributeError:
# p.color = "red"  # Can't add attributes not in __slots__
```

### How Slots Work -- Descriptors Under the Hood

When you define `__slots__`, Python creates a **descriptor** (specifically a `member_descriptor`) on the class for each slot name. These descriptors store values at fixed byte offsets in the instance's memory:

```python
# Each slot is actually a descriptor on the class
print(type(SlottedPoint.x))  # <class 'member_descriptor'>

# The descriptor reads/writes at a fixed memory offset
# No hash table lookup needed -- just pointer arithmetic
```

```
REGULAR CLASS MEMORY LAYOUT:

  Instance (48 bytes)     __dict__ (184+ bytes)
  ┌──────────────────┐    ┌──────────────────────┐
  │ PyObject header   │    │ Hash table overhead   │
  │ (type, refcount)  │    │ (buckets, resize)     │
  │                   │    │                       │
  │ __dict__ ptr ─────┼───►│ 'x' → 1.0            │
  │ __weakref__ ptr   │    │ 'y' → 2.0            │
  └──────────────────┘    │ 'z' → 3.0            │
                          └──────────────────────┘
  Total: ~232 bytes per instance

SLOTTED CLASS MEMORY LAYOUT:

  Instance (64 bytes)
  ┌──────────────────┐
  │ PyObject header   │
  │ (type, refcount)  │
  │                   │
  │ slot 0: x → 1.0   │  ◄── Fixed offset, no hash lookup
  │ slot 1: y → 2.0   │
  │ slot 2: z → 3.0   │
  └──────────────────┘

  Total: ~64 bytes per instance (72% smaller!)
```

### Weakref Compatibility

By default, slotted classes don't support `weakref.ref()` because there's no `__weakref__` slot. Add it explicitly if you need weak references:

```python
import weakref

class SlottedWithWeakref:
    __slots__ = ('x', 'y', '__weakref__')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

obj = SlottedWithWeakref(1.0, 2.0)
ref = weakref.ref(obj)  # Works!
print(ref() is obj)     # True
```

Without `__weakref__` in slots, `weakref.ref(obj)` raises `TypeError`. This is a common gotcha when converting classes to use slots.

### Measuring Memory at Scale

The real payoff of `__slots__` shows up when you have thousands or millions of instances:

```python
import sys
import os

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB (Linux/macOS)."""
    try:
        import resource
        # maxrss is in KB on Linux, bytes on macOS
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == 'darwin':
            return usage / (1024 * 1024)  # bytes → MB
        return usage / 1024  # KB → MB
    except ImportError:
        return 0.0

def measure_collection_memory(cls, count: int) -> dict:
    """Measure memory used by `count` instances of `cls`."""
    single = cls(1.0, 2.0, 3.0)
    instance_size = sys.getsizeof(single)
    dict_size = sys.getsizeof(single.__dict__) if hasattr(single, '__dict__') else 0

    # Create many instances
    objects = [cls(float(i), float(i+1), float(i+2)) for i in range(count)]

    return {
        'class': cls.__name__,
        'count': count,
        'instance_size': instance_size,
        'dict_size': dict_size,
        'total_per_instance': instance_size + dict_size,
        'estimated_total_mb': (instance_size + dict_size) * count / (1024 * 1024),
        'has_dict': hasattr(single, '__dict__'),
        'has_slots': hasattr(cls, '__slots__'),
    }
```

### Slots with Inheritance

Slots interact with inheritance in specific ways that you must understand:

```python
class Base:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

class Child(Base):
    __slots__ = ('z',)  # Only NEW attributes -- don't repeat parent slots

    def __init__(self, x, y, z):
        super().__init__(x, y)
        self.z = z

# This works -- child has x, y, z
c = Child(1, 2, 3)
print(c.x, c.y, c.z)  # 1 2 3
print(hasattr(c, '__dict__'))  # False -- fully slotted

# WARNING: If child doesn't define __slots__, it gets a __dict__
class ChildWithDict(Base):
    def __init__(self, x, y, z):
        super().__init__(x, y)
        self.z = z  # Goes into __dict__

cd = ChildWithDict(1, 2, 3)
print(hasattr(cd, '__dict__'))  # True -- __dict__ for non-slot attrs
```

Rules for slots with inheritance:
1. **Only list NEW attributes** in child's `__slots__` -- never repeat parent slots
2. **Every class in the hierarchy** must define `__slots__` to avoid `__dict__`
3. **Multiple inheritance** with conflicting non-empty slots raises `TypeError`
4. A child **without `__slots__`** inherits parent slots but also gets a `__dict__`

### When to Use `__slots__`

Use `__slots__` when:
- You're creating **many instances** (thousands+) of a class with fixed attributes
- Memory is a constraint (embedded, data pipelines, game entities)
- You want to **prevent typos** -- AttributeError on misspelled attributes
- You need slightly **faster attribute access** (fixed offset vs hash lookup)

Don't use `__slots__` when:
- You need **dynamic attributes** (monkey-patching, flexible data objects)
- The class is a **base class** that others will subclass freely
- You're using `__slots__` prematurely -- profile first, optimize second
- You need compatibility with libraries that use `__dict__` (some ORMs, serializers)

## Playground

Run the full demonstration:

```bash
python playground/31_slots_memory.py
```

> **Note:** The byte counts below are from CPython 3.12 on a 64-bit Linux system. Exact values may vary by Python version and platform.

```
--- Section 1: __dict__ vs __slots__ Comparison ---
  RegularPoint:
    Instance size: 48 bytes
    __dict__ size: 184 bytes
    Total per instance: 232 bytes
    Has __dict__: True
  SlottedPoint:
    Instance size: 64 bytes
    __dict__ size: 0 bytes
    Total per instance: 64 bytes
    Has __dict__: False
  Memory savings with __slots__: 72.4%

--- Section 2: Memory Layout Exploration ---
  RegularPoint attributes stored in __dict__: {'x': 1.0, 'y': 2.0, 'z': 3.0}
  SlottedPoint has no __dict__ -- attributes at fixed offsets
  Slot descriptors on class:
    x: <class 'member_descriptor'>
    y: <class 'member_descriptor'>
    z: <class 'member_descriptor'>
  Dynamic attribute test: RegularPoint accepts p.color = 'red' -- OK
  Dynamic attribute test: SlottedPoint rejects p.color = 'red' -- AttributeError (expected)

--- Section 3: Weakref Compatibility ---
  Regular class supports weakref: True
  Slotted class (no __weakref__): weakref raises TypeError (expected)
  Slotted class (with __weakref__): weakref works -- True
  Weak reference resolves correctly: True

--- Section 4: Bulk Memory Profiling ---
  Creating 100,000 RegularPoint instances...
    Per-instance: 232 bytes, Estimated total: 22.12 MB
  Creating 100,000 SlottedPoint instances...
    Per-instance: 64 bytes, Estimated total: 6.10 MB
  Bulk savings: 72.4% less memory with __slots__

--- Section 5: Slots with Inheritance ---
  Base(x=1, y=2): has __dict__ = False
  ChildSlotted(x=1, y=2, z=3): has __dict__ = False
  ChildNoSlots(x=1, y=2): has __dict__ = True (gets __dict__ for extra attrs)
  ChildSlotted size: 72 bytes (compact)
  ChildNoSlots size: 48 bytes + 104 bytes dict = 152 bytes

--- Summary ---
__slots__ eliminates per-instance __dict__ for significant memory savings:
  - 72% less memory per instance (3 attributes)
  - Add __weakref__ to slots if you need weak references
  - Every class in hierarchy must define __slots__ to stay dict-free
  - Use for high-volume objects: ORMs, data pipelines, game entities
  - Profile first -- premature optimization is the root of all evil

All 5 sections passed. __slots__ & memory optimization mastered!
```

## How It Works

```
PYTHON OBJECT MEMORY MODEL:

  Every object in CPython has this header:

  ┌────────────────────────┐
  │ ob_refcnt (8 bytes)    │  Reference count for garbage collection
  │ ob_type (8 bytes)      │  Pointer to type/class object
  └────────────────────────┘
       16 bytes minimum

  REGULAR CLASS adds:

  ┌────────────────────────┐
  │ ob_refcnt              │
  │ ob_type                │
  │ __dict__ ptr (8 bytes) │  → points to PyDictObject (~184+ bytes)
  │ __weakref__ (8 bytes)  │  → for weakref support
  └────────────────────────┘
       32 bytes + ~184 bytes dict = ~216+ bytes

  SLOTTED CLASS adds:

  ┌────────────────────────┐
  │ ob_refcnt              │
  │ ob_type                │
  │ slot_0 ptr (8 bytes)   │  → direct pointer to value
  │ slot_1 ptr (8 bytes)   │  → no hash table needed
  │ slot_2 ptr (8 bytes)   │  → O(1) fixed-offset access
  └────────────────────────┘
       40 bytes total (for 3 slots)


ATTRIBUTE LOOKUP COMPARISON:

  obj.x on regular class:          obj.x on slotted class:

  1. Look in type.__dict__         1. Look in type.__dict__
  2. Check for data descriptor     2. Find member_descriptor
  3. Look in obj.__dict__          3. Read from fixed offset
  4. Hash 'x'                         (pointer arithmetic)
  5. Find bucket
  6. Return value

  ~5 steps + hash                  ~3 steps, no hash


sys.getsizeof() vs TOTAL MEMORY:

  sys.getsizeof(obj) returns only the SHALLOW size:
  - The instance struct itself
  - Does NOT include __dict__ contents
  - Does NOT include referenced objects

  Total memory = sys.getsizeof(obj)
               + sys.getsizeof(obj.__dict__)  (if regular class)
               + sum(sys.getsizeof(v) for v in obj.__dict__.values())
```

## Exercises

### Exercise 1: Memory-efficient data record

Build a `StockTick` class using `__slots__` that stores high-frequency trading data. Measure memory savings vs a regular class with 1 million instances:

```python
class StockTick:
    __slots__ = ('symbol', 'price', 'volume', 'timestamp', 'bid', 'ask')

    def __init__(self, symbol: str, price: float, volume: int,
                 timestamp: float, bid: float, ask: float):
        # TODO: assign all attributes
        ...

# Create 1M instances, measure memory with sys.getsizeof
# Compare with a regular class version
# Target: 50%+ memory reduction
```

### Exercise 2: Slotted class with `__repr__` and `__eq__`

Slots don't prevent you from defining methods. Build a full-featured slotted class:

```python
class Vec3:
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        # TODO: assign attributes
        ...

    def __repr__(self) -> str:
        # TODO: return "Vec3(x=1.0, y=2.0, z=3.0)" format
        ...

    def __eq__(self, other) -> bool:
        # TODO: compare x, y, z with isinstance check
        ...

    def __add__(self, other: 'Vec3') -> 'Vec3':
        # TODO: return new Vec3 with summed components
        ...

    def magnitude(self) -> float:
        # TODO: return sqrt(x^2 + y^2 + z^2)
        ...
```

### Exercise 3: Slots-compatible mixin

Write a mixin that works with slotted classes. The challenge: mixins often need their own state, but adding slots to mixins can cause conflicts:

```python
class TimestampMixin:
    """Mixin that records creation time. Works with slotted classes."""
    __slots__ = ('_created_at',)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # TODO: wrap __init__ to auto-set _created_at

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def age_seconds(self) -> float:
        # TODO: return time since creation
        ...

class Event(TimestampMixin):
    __slots__ = ('name', 'data')

    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

e = Event("click", {"x": 100})
print(e.created_at)    # timestamp
print(e.age_seconds)   # ~0.0001
print(hasattr(e, '__dict__'))  # False -- still fully slotted
```

## What's Next

In [Kata 32 -- The Import System](./32-import-system.md), we'll explore how Python finds, loads, and caches modules. We'll build custom import hooks, understand `sys.path`, `sys.modules`, and the finder/loader protocol -- the machinery that makes `import` work.

---

[prev: 30-free-threaded-python](./30-free-threaded-python.md) | [next: 32-import-system](./32-import-system.md)
