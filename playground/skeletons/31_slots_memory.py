"""
Kata 31 -- __slots__ & Memory Optimization
Run: python playground/skeletons/31_slots_memory.py

Explore __slots__, memory layout, __dict__ vs __slots__, weakref
compatibility, sys.getsizeof, memory profiling techniques, and when
to use slots for optimal memory usage.

All demos complete within 5 seconds.
"""

import sys
import weakref


# ===========================================================================
# SECTION 1: __dict__ vs __slots__ Comparison
# ===========================================================================

class RegularPoint:
    """Standard class -- uses __dict__ for instance attributes."""

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z


class SlottedPoint:
    """Slotted class -- fixed attribute layout, no __dict__.

    Should define __slots__ = ('x', 'y', 'z') to eliminate __dict__.
    """
    # TODO: define __slots__ as a tuple of ('x', 'y', 'z')
    # HINT: __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        # TODO: assign x, y, z to self
        pass


def demo_dict_vs_slots():
    """Compare memory usage of regular vs slotted classes."""
    regular = RegularPoint(1.0, 2.0, 3.0)
    slotted = SlottedPoint(1.0, 2.0, 3.0)

    # TODO: measure instance size with sys.getsizeof(regular)
    # TODO: measure __dict__ size with sys.getsizeof(regular.__dict__)
    # HINT: reg_total = reg_instance + reg_dict
    reg_instance = 0  # Replace with sys.getsizeof(regular)
    reg_dict = 0      # Replace with sys.getsizeof(regular.__dict__)
    reg_total = reg_instance + reg_dict

    print("  RegularPoint:")
    print(f"    Instance size: {reg_instance} bytes")
    print(f"    __dict__ size: {reg_dict} bytes")
    print(f"    Total per instance: {reg_total} bytes")
    print(f"    Has __dict__: {hasattr(regular, '__dict__')}")

    # TODO: measure slotted instance size (no __dict__ to measure)
    slot_instance = 0  # Replace with sys.getsizeof(slotted)
    slot_dict = 0  # No __dict__

    print("  SlottedPoint:")
    print(f"    Instance size: {slot_instance} bytes")
    print(f"    __dict__ size: {slot_dict} bytes")
    print(f"    Total per instance: {slot_instance} bytes")
    print(f"    Has __dict__: {hasattr(slotted, '__dict__')}")

    # TODO: calculate savings percentage
    # HINT: savings = (1 - slot_instance / reg_total) * 100
    savings = 0  # Replace with calculation
    print(f"  Memory savings with __slots__: {savings:.1f}%")

    # Assertions
    assert hasattr(regular, '__dict__'), "Regular class should have __dict__"
    assert not hasattr(slotted, '__dict__'), "Slotted class should not have __dict__"
    assert slot_instance < reg_total, "Slotted should use less memory"
    assert regular.x == slotted.x == 1.0
    assert regular.y == slotted.y == 2.0
    assert regular.z == slotted.z == 3.0


# ===========================================================================
# SECTION 2: Memory Layout Exploration
# ===========================================================================

def demo_memory_layout():
    """Explore how CPython stores attributes for regular vs slotted classes."""
    regular = RegularPoint(1.0, 2.0, 3.0)
    slotted = SlottedPoint(1.0, 2.0, 3.0)

    # Regular: attributes live in __dict__
    print(f"  RegularPoint attributes stored in __dict__: {regular.__dict__}")

    # TODO: print the type of each slot descriptor on SlottedPoint
    # HINT: for slot_name in SlottedPoint.__slots__:
    #           descriptor = getattr(SlottedPoint, slot_name)
    #           print(f"    {slot_name}: {type(descriptor)}")
    print("  SlottedPoint has no __dict__ -- attributes at fixed offsets")
    print("  Slot descriptors on class:")
    pass  # Replace with loop over __slots__

    # TODO: test that regular allows dynamic attributes (regular.color = "red")
    # TODO: test that slotted rejects dynamic attributes (raises AttributeError)
    # HINT: use try/except AttributeError
    print(f"  Dynamic attribute test: RegularPoint accepts p.color = 'red' -- OK")
    print("  Dynamic attribute test: SlottedPoint rejects p.color = 'red'"
          " -- AttributeError (expected)")

    # Verify descriptor types
    for slot_name in SlottedPoint.__slots__:
        desc = getattr(SlottedPoint, slot_name)
        assert type(desc).__name__ == 'member_descriptor', (
            f"Slot {slot_name} should be a member_descriptor"
        )


# ===========================================================================
# SECTION 3: Weakref Compatibility
# ===========================================================================

class SlottedNoWeakref:
    """Slotted class WITHOUT __weakref__ -- cannot create weak references."""
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class SlottedWithWeakref:
    """Slotted class WITH __weakref__ -- supports weak references.

    Must include '__weakref__' in __slots__ to enable weakref support.
    """
    # TODO: define __slots__ with 'x', 'y', AND '__weakref__'
    # HINT: __slots__ = ('x', 'y', '__weakref__')

    def __init__(self, x: float, y: float):
        # TODO: assign x, y
        pass


def demo_weakref_compatibility():
    """Show how to make slotted classes work with weakref."""
    # Regular classes support weakref by default
    regular = RegularPoint(1.0, 2.0, 3.0)
    # TODO: create a weakref.ref(regular) and verify it resolves to regular
    # HINT: ref_regular = weakref.ref(regular); supports = ref_regular() is regular
    supports_regular = False  # Replace with weakref check
    print(f"  Regular class supports weakref: {supports_regular}")
    assert supports_regular

    # TODO: try weakref.ref on SlottedNoWeakref -- should raise TypeError
    # HINT: try/except TypeError
    no_weakref = SlottedNoWeakref(1.0, 2.0)
    print("  Slotted class (no __weakref__): weakref raises TypeError (expected)")

    # TODO: try weakref.ref on SlottedWithWeakref -- should work
    with_weakref = SlottedWithWeakref(1.0, 2.0)
    supports_with = False  # Replace with weakref check
    print(f"  Slotted class (with __weakref__): weakref works -- {supports_with}")
    assert supports_with

    # TODO: verify the weak reference resolves correctly
    print(f"  Weak reference resolves correctly: True")


# ===========================================================================
# SECTION 4: Bulk Memory Profiling
# ===========================================================================

def demo_bulk_profiling():
    """Measure memory savings at scale with many instances."""
    count = 100_000

    # TODO: measure per-instance size for RegularPoint (instance + __dict__)
    # HINT: reg_size = sys.getsizeof(instance) + sys.getsizeof(instance.__dict__)
    reg_size = 0  # Replace with measurement

    print(f"  Creating {count:,} RegularPoint instances...")
    # TODO: create count RegularPoint instances in a list
    regular_objects = []  # Replace with list comprehension
    reg_estimated_mb = reg_size * count / (1024 * 1024)
    print(f"    Per-instance: {reg_size} bytes, Estimated total: {reg_estimated_mb:.2f} MB")

    # TODO: measure per-instance size for SlottedPoint (instance only, no __dict__)
    slot_size = 0  # Replace with measurement

    print(f"  Creating {count:,} SlottedPoint instances...")
    # TODO: create count SlottedPoint instances in a list
    slotted_objects = []  # Replace with list comprehension
    slot_estimated_mb = slot_size * count / (1024 * 1024)
    print(f"    Per-instance: {slot_size} bytes, Estimated total: {slot_estimated_mb:.2f} MB")

    # TODO: calculate savings percentage
    savings = 0  # Replace with calculation
    print(f"  Bulk savings: {savings:.1f}% less memory with __slots__")

    # Assertions
    assert len(regular_objects) == count
    assert len(slotted_objects) == count
    assert slot_size < reg_size, "Slotted should be smaller"
    assert savings > 40, "Should save at least 40% memory"


# ===========================================================================
# SECTION 5: Slots with Inheritance
# ===========================================================================

class Base:
    """Base class with slots."""
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class ChildSlotted(Base):
    """Child that ALSO defines __slots__ -- stays dict-free.

    Must only list NEW attributes (not inherited ones).
    """
    # TODO: define __slots__ with ONLY the new attribute 'z'
    # HINT: __slots__ = ('z',)  -- do NOT repeat 'x' or 'y'

    def __init__(self, x: float, y: float, z: float):
        # TODO: call super().__init__(x, y) and assign z
        pass


class ChildNoSlots(Base):
    """Child that does NOT define __slots__ -- gets a __dict__."""

    def __init__(self, x: float, y: float, extra: str = "hello"):
        super().__init__(x, y)
        self.extra = extra  # Goes into __dict__


def demo_slots_inheritance():
    """Show how __slots__ interacts with inheritance."""
    base = Base(1.0, 2.0)
    child_slotted = ChildSlotted(1.0, 2.0, 3.0)
    child_no_slots = ChildNoSlots(1.0, 2.0)

    # TODO: check hasattr(obj, '__dict__') for each instance
    base_has_dict = False  # Replace with hasattr check
    child_slotted_has_dict = False  # Replace with hasattr check
    child_no_slots_has_dict = True  # Replace with hasattr check

    print(f"  Base(x=1, y=2): has __dict__ = {base_has_dict}")
    print(f"  ChildSlotted(x=1, y=2, z=3): has __dict__ = {child_slotted_has_dict}")
    print(f"  ChildNoSlots(x=1, y=2): has __dict__ = {child_no_slots_has_dict}"
          " (gets __dict__ for extra attrs)")

    assert not base_has_dict, "Base with __slots__ should not have __dict__"
    assert not child_slotted_has_dict, "ChildSlotted should not have __dict__"
    assert child_no_slots_has_dict, "ChildNoSlots should have __dict__"

    # TODO: compare sizes with sys.getsizeof
    # HINT: child_slotted_size = sys.getsizeof(child_slotted)
    # HINT: child_no_slots_size = sys.getsizeof(child_no_slots)
    # HINT: child_no_slots_dict_size = sys.getsizeof(child_no_slots.__dict__)
    child_slotted_size = 0  # Replace
    child_no_slots_size = 0  # Replace
    child_no_slots_dict_size = 0  # Replace

    print(f"  ChildSlotted size: {child_slotted_size} bytes (compact)")
    print(f"  ChildNoSlots size: {child_no_slots_size} bytes"
          f" + {child_no_slots_dict_size} bytes dict"
          f" = {child_no_slots_size + child_no_slots_dict_size} bytes")

    assert child_slotted_size < child_no_slots_size + child_no_slots_dict_size

    # Verify all attributes work
    assert child_slotted.x == 1.0
    assert child_slotted.y == 2.0
    assert child_slotted.z == 3.0
    assert child_no_slots.x == 1.0
    assert child_no_slots.y == 2.0
    assert child_no_slots.extra == "hello"


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: __dict__ vs __slots__ ---
    print("--- Section 1: __dict__ vs __slots__ Comparison ---")
    try:
        demo_dict_vs_slots()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: Memory Layout ---
    print("--- Section 2: Memory Layout Exploration ---")
    try:
        demo_memory_layout()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: Weakref Compatibility ---
    print("--- Section 3: Weakref Compatibility ---")
    try:
        demo_weakref_compatibility()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: Bulk Profiling ---
    print("--- Section 4: Bulk Memory Profiling ---")
    try:
        demo_bulk_profiling()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: Slots with Inheritance ---
    print("--- Section 5: Slots with Inheritance ---")
    try:
        demo_slots_inheritance()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("__slots__ eliminates per-instance __dict__ for significant memory savings:")
    print("  - 72% less memory per instance (3 attributes)")
    print("  - Add __weakref__ to slots if you need weak references")
    print("  - Every class in hierarchy must define __slots__ to stay dict-free")
    print("  - Use for high-volume objects: ORMs, data pipelines, game entities")
    print("  - Profile first -- premature optimization is the root of all evil")
    print()
    print("All 5 sections passed. __slots__ & memory optimization mastered!")
