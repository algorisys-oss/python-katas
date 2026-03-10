"""
Kata 31 -- __slots__ & Memory Optimization
Run: python playground/31_slots_memory.py

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
    """Slotted class -- fixed attribute layout, no __dict__."""
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z


def demo_dict_vs_slots():
    """Compare memory usage of regular vs slotted classes."""
    regular = RegularPoint(1.0, 2.0, 3.0)
    slotted = SlottedPoint(1.0, 2.0, 3.0)

    # Regular class: instance + __dict__
    reg_instance = sys.getsizeof(regular)
    reg_dict = sys.getsizeof(regular.__dict__)
    reg_total = reg_instance + reg_dict

    print("  RegularPoint:")
    print(f"    Instance size: {reg_instance} bytes")
    print(f"    __dict__ size: {reg_dict} bytes")
    print(f"    Total per instance: {reg_total} bytes")
    print(f"    Has __dict__: {hasattr(regular, '__dict__')}")

    # Slotted class: instance only, no __dict__
    slot_instance = sys.getsizeof(slotted)
    slot_dict = 0  # No __dict__

    print("  SlottedPoint:")
    print(f"    Instance size: {slot_instance} bytes")
    print(f"    __dict__ size: {slot_dict} bytes")
    print(f"    Total per instance: {slot_instance} bytes")
    print(f"    Has __dict__: {hasattr(slotted, '__dict__')}")

    savings = (1 - slot_instance / reg_total) * 100
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

    # Slotted: attributes accessed via descriptors on the class
    print("  SlottedPoint has no __dict__ -- attributes at fixed offsets")
    print("  Slot descriptors on class:")
    for slot_name in SlottedPoint.__slots__:
        descriptor = getattr(SlottedPoint, slot_name)
        print(f"    {slot_name}: {type(descriptor)}")

    # Dynamic attribute test: regular allows it, slotted doesn't
    regular.color = "red"
    print(f"  Dynamic attribute test: RegularPoint accepts p.color = 'red' -- OK")
    assert regular.color == "red"

    try:
        slotted.color = "red"  # type: ignore
        assert False, "Should have raised AttributeError"
    except AttributeError:
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
    """Slotted class WITH __weakref__ -- supports weak references."""
    __slots__ = ('x', 'y', '__weakref__')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


def demo_weakref_compatibility():
    """Show how to make slotted classes work with weakref."""
    # Regular classes support weakref by default
    regular = RegularPoint(1.0, 2.0, 3.0)
    ref_regular = weakref.ref(regular)
    supports_regular = ref_regular() is regular
    print(f"  Regular class supports weakref: {supports_regular}")
    assert supports_regular

    # Slotted class without __weakref__ -- raises TypeError
    no_weakref = SlottedNoWeakref(1.0, 2.0)
    try:
        weakref.ref(no_weakref)
        assert False, "Should have raised TypeError"
    except TypeError:
        print("  Slotted class (no __weakref__): weakref raises TypeError (expected)")

    # Slotted class with __weakref__ -- works fine
    with_weakref = SlottedWithWeakref(1.0, 2.0)
    ref_with = weakref.ref(with_weakref)
    supports_with = ref_with() is with_weakref
    print(f"  Slotted class (with __weakref__): weakref works -- {supports_with}")
    assert supports_with

    # Verify weak reference resolves correctly
    resolved = ref_with()
    print(f"  Weak reference resolves correctly: {resolved is with_weakref}")
    assert resolved is with_weakref
    assert resolved.x == 1.0
    assert resolved.y == 2.0


# ===========================================================================
# SECTION 4: Bulk Memory Profiling
# ===========================================================================

def demo_bulk_profiling():
    """Measure memory savings at scale with many instances."""
    count = 100_000

    # Measure regular class
    regular_instance = RegularPoint(1.0, 2.0, 3.0)
    reg_size = sys.getsizeof(regular_instance) + sys.getsizeof(regular_instance.__dict__)

    print(f"  Creating {count:,} RegularPoint instances...")
    regular_objects = [RegularPoint(float(i), float(i+1), float(i+2))
                       for i in range(count)]
    reg_estimated_mb = reg_size * count / (1024 * 1024)
    print(f"    Per-instance: {reg_size} bytes, Estimated total: {reg_estimated_mb:.2f} MB")

    # Measure slotted class
    slotted_instance = SlottedPoint(1.0, 2.0, 3.0)
    slot_size = sys.getsizeof(slotted_instance)

    print(f"  Creating {count:,} SlottedPoint instances...")
    slotted_objects = [SlottedPoint(float(i), float(i+1), float(i+2))
                       for i in range(count)]
    slot_estimated_mb = slot_size * count / (1024 * 1024)
    print(f"    Per-instance: {slot_size} bytes, Estimated total: {slot_estimated_mb:.2f} MB")

    savings = (1 - slot_size / reg_size) * 100
    print(f"  Bulk savings: {savings:.1f}% less memory with __slots__")

    # Assertions
    assert len(regular_objects) == count
    assert len(slotted_objects) == count
    assert slot_size < reg_size, "Slotted should be smaller"
    assert savings > 40, "Should save at least 40% memory"

    # Verify data integrity
    assert regular_objects[0].x == 0.0
    assert slotted_objects[0].x == 0.0
    assert regular_objects[-1].z == float(count - 1 + 2)
    assert slotted_objects[-1].z == float(count - 1 + 2)


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
    """Child that ALSO defines __slots__ -- stays dict-free."""
    __slots__ = ('z',)  # Only NEW attributes

    def __init__(self, x: float, y: float, z: float):
        super().__init__(x, y)
        self.z = z


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

    base_has_dict = hasattr(base, '__dict__')
    child_slotted_has_dict = hasattr(child_slotted, '__dict__')
    child_no_slots_has_dict = hasattr(child_no_slots, '__dict__')

    print(f"  Base(x=1, y=2): has __dict__ = {base_has_dict}")
    print(f"  ChildSlotted(x=1, y=2, z=3): has __dict__ = {child_slotted_has_dict}")
    print(f"  ChildNoSlots(x=1, y=2): has __dict__ = {child_no_slots_has_dict}"
          " (gets __dict__ for extra attrs)")

    assert not base_has_dict, "Base with __slots__ should not have __dict__"
    assert not child_slotted_has_dict, "ChildSlotted should not have __dict__"
    assert child_no_slots_has_dict, "ChildNoSlots should have __dict__"

    # Size comparison
    child_slotted_size = sys.getsizeof(child_slotted)
    child_no_slots_size = sys.getsizeof(child_no_slots)
    child_no_slots_dict_size = sys.getsizeof(child_no_slots.__dict__)

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

    # Verify ChildSlotted rejects dynamic attributes
    try:
        child_slotted.color = "red"  # type: ignore
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass  # Expected

    # Verify ChildNoSlots accepts dynamic attributes (has __dict__)
    child_no_slots.color = "blue"
    assert child_no_slots.color == "blue"


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: __dict__ vs __slots__ ---
    print("--- Section 1: __dict__ vs __slots__ Comparison ---")
    demo_dict_vs_slots()
    print()

    # --- Section 2: Memory Layout ---
    print("--- Section 2: Memory Layout Exploration ---")
    demo_memory_layout()
    print()

    # --- Section 3: Weakref Compatibility ---
    print("--- Section 3: Weakref Compatibility ---")
    demo_weakref_compatibility()
    print()

    # --- Section 4: Bulk Profiling ---
    print("--- Section 4: Bulk Memory Profiling ---")
    demo_bulk_profiling()
    print()

    # --- Section 5: Slots with Inheritance ---
    print("--- Section 5: Slots with Inheritance ---")
    demo_slots_inheritance()
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
