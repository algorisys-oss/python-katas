"""
Kata 12 -- Properties & Descriptors
Run: python playground/12_properties_descriptors.py

Master @property, getter/setter/deleter, the descriptor protocol (__get__,
__set__, __delete__, __set_name__), data vs non-data descriptors, computed
attributes, and validation descriptors.
"""

import math


# ===========================================================================
# CLASSES (defined at module level for descriptor protocol)
# ===========================================================================

class Temperature:
    """Temperature with Celsius storage and Fahrenheit conversion."""

    def __init__(self, celsius=0.0):
        self.celsius = celsius  # Goes through the setter

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError(f"Temperature {value}°C is below absolute zero")
        self._celsius = float(value)

    @celsius.deleter
    def celsius(self):
        self._celsius = 0.0

    @property
    def fahrenheit(self):
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value):
        self.celsius = (value - 32) * 5 / 9  # Reuses celsius setter validation

    @property
    def kelvin(self):
        return self._celsius + 273.15

    @kelvin.setter
    def kelvin(self, value):
        if value < 0:
            raise ValueError(f"Kelvin cannot be negative, got {value}")
        self.celsius = value - 273.15

    def __repr__(self):
        return f"Temperature({self._celsius}°C / {self.fahrenheit}°F)"


class Validated:
    """Descriptor that enforces type and optional range constraints."""

    def __init__(self, expected_type, *, min_value=None, max_value=None):
        self.expected_type = expected_type
        self.min_value = min_value
        self.max_value = max_value

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} must be {self.expected_type.__name__ if isinstance(self.expected_type, type) else self.expected_type}, "
                f"got {type(value).__name__}"
            )
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} must be >= {self.min_value}, got {value}")
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} must be <= {self.max_value}, got {value}")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj):
        if hasattr(obj, self.private_name):
            delattr(obj, self.private_name)


class Product:
    name = Validated(str)
    price = Validated((int, float), min_value=0)
    quantity = Validated(int, min_value=0, max_value=10000)

    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Product({self.name!r}, ${self.price}, qty={self.quantity})"


class LazyProperty:
    """Descriptor that computes a value once and caches it on the instance."""

    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = self.func(obj)
        # Cache directly on the instance -- shadows the descriptor
        setattr(obj, self.name, value)
        return value


class DataProcessor:
    def __init__(self, data):
        self.data = data

    @LazyProperty
    def processed(self):
        """Expensive computation, only done once."""
        print("    Computing processed data...")
        return [x ** 2 for x in self.data]

    @LazyProperty
    def summary(self):
        """Depends on processed data."""
        print("    Computing summary...")
        return {
            "count": len(self.processed),
            "total": sum(self.processed),
            "mean": sum(self.processed) / len(self.processed),
        }


# Verbose descriptor for demonstration
class Verbose:
    """A descriptor that prints every access."""

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = getattr(obj, self.private_name, "NOT SET")
        print(f"    Getting {self.name}: {value}")
        return value

    def __set__(self, obj, value):
        print(f"    Setting {self.name} = {value}")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj):
        print(f"    Deleting {self.name}")
        delattr(obj, self.private_name)


class VerboseDemo:
    x = Verbose()
    y = Verbose()


# Data vs non-data descriptor demo
class DataDescriptor:
    """Has __set__ -> always wins over instance __dict__."""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(f"_dd_{self.name}", "default")

    def __set__(self, obj, value):
        obj.__dict__[f"_dd_{self.name}"] = value


class NonDataDescriptor:
    """Only __get__ -> instance __dict__ can override."""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return f"NonDataDescriptor({self.name})"


class LookupDemo:
    data = DataDescriptor()
    nondata = NonDataDescriptor()


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: @property basics ---
    print("--- Section 1: @property Basics ---")

    class Circle:
        def __init__(self, radius):
            self._radius = radius

        @property
        def radius(self):
            """The radius of the circle."""
            return self._radius

        @radius.setter
        def radius(self, value):
            if value < 0:
                raise ValueError("Radius cannot be negative")
            self._radius = value

        @property
        def area(self):
            """Computed: area from radius (read-only)."""
            return math.pi * self._radius ** 2

    c = Circle(5)
    print(f"  radius = {c.radius}")
    assert c.radius == 5

    print(f"  area = {c.area:.4f}")
    assert abs(c.area - 78.5398) < 0.001

    c.radius = 10
    print(f"  radius after set = {c.radius}")
    assert c.radius == 10
    print(f"  area after set = {c.area:.4f}")
    assert abs(c.area - 314.1593) < 0.001

    # Read-only property -- no setter
    try:
        c.area = 100
        assert False, "Should have raised AttributeError"
    except AttributeError:
        print("  c.area = 100 → AttributeError (read-only property)")

    # Validation
    try:
        c.radius = -1
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  c.radius = -1 → ValueError: {e}")

    print()

    # --- Section 2: Temperature class -- full property lifecycle ---
    print("--- Section 2: Temperature Class ---")

    t = Temperature(100)
    print(f"  {t}")
    assert t.celsius == 100.0
    assert t.fahrenheit == 212.0

    t.fahrenheit = 32
    print(f"  After setting fahrenheit=32: celsius={t.celsius}")
    assert t.celsius == 0.0

    t.kelvin = 373.15
    print(f"  After setting kelvin=373.15: celsius={t.celsius}")
    assert abs(t.celsius - 100.0) < 0.01

    print(f"  kelvin = {t.kelvin}")
    assert abs(t.kelvin - 373.15) < 0.01

    # Deleter resets to 0
    del t.celsius
    print(f"  After del celsius: {t.celsius}")
    assert t.celsius == 0.0

    # Validation: below absolute zero
    try:
        t.celsius = -300
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  celsius = -300 → ValueError: {e}")

    # Validation: negative kelvin
    try:
        t.kelvin = -1
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  kelvin = -1 → ValueError: {e}")

    print()

    # --- Section 3: Descriptor protocol -- __get__, __set__, __delete__ ---
    print("--- Section 3: Descriptor Protocol ---")

    d = VerboseDemo()
    d.x = 10
    d.y = 20
    val = d.x
    assert val == 10
    del d.x

    # Access from class returns the descriptor itself
    desc = VerboseDemo.x
    print(f"  VerboseDemo.x is Verbose instance: {isinstance(desc, Verbose)}")
    assert isinstance(desc, Verbose)

    print()

    # --- Section 4: __set_name__ ---
    print("--- Section 4: __set_name__ ---")

    # __set_name__ is called automatically when the class is created
    print(f"  VerboseDemo.x descriptor name: {VerboseDemo.x.name}")
    assert VerboseDemo.x.name == "x"
    print(f"  VerboseDemo.y descriptor name: {VerboseDemo.y.name}")
    assert VerboseDemo.y.name == "y"

    print()

    # --- Section 5: Data vs non-data descriptors ---
    print("--- Section 5: Data vs Non-Data Descriptors ---")

    obj = LookupDemo()

    # Data descriptor: always goes through __set__/__get__
    obj.data = "via descriptor"
    print(f"  obj.data = {obj.data!r}")
    assert obj.data == "via descriptor"

    # Non-data descriptor: instance __dict__ can override
    print(f"  obj.nondata (descriptor) = {obj.nondata!r}")
    assert obj.nondata == "NonDataDescriptor(nondata)"

    obj.__dict__["nondata"] = "instance wins"
    print(f"  obj.nondata (after __dict__ set) = {obj.nondata!r}")
    assert obj.nondata == "instance wins"

    # Clean up
    del obj.__dict__["nondata"]
    print(f"  obj.nondata (after __dict__ del) = {obj.nondata!r}")
    assert obj.nondata == "NonDataDescriptor(nondata)"

    print()

    # --- Section 6: Validated descriptor ---
    print("--- Section 6: Validated Descriptor ---")

    p = Product("Widget", 9.99, 100)
    print(f"  {p}")
    assert p.name == "Widget"
    assert p.price == 9.99
    assert p.quantity == 100

    # Type checking
    try:
        p.name = 42
        assert False, "Should have raised TypeError"
    except TypeError as e:
        print(f"  name = 42 → TypeError: {e}")

    # Range checking: min
    try:
        p.price = -1
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  price = -1 → ValueError: {e}")

    # Range checking: max
    try:
        p.quantity = 99999
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  quantity = 99999 → ValueError: {e}")

    # Valid update
    p.price = 19.99
    p.quantity = 50
    print(f"  After update: {p}")
    assert p.price == 19.99
    assert p.quantity == 50

    # Delete
    del p.name
    print(f"  After del name: {p.name}")
    assert p.name is None

    print()

    # --- Section 7: LazyProperty descriptor ---
    print("--- Section 7: LazyProperty Descriptor ---")

    dp = DataProcessor([1, 2, 3, 4, 5])

    # First access computes
    print("  First access to processed:")
    result = dp.processed
    print(f"  processed = {result}")
    assert result == [1, 4, 9, 16, 25]

    # Second access uses cached value (no "Computing..." message)
    print("  Second access to processed:")
    result2 = dp.processed
    print(f"  processed = {result2}")
    assert result2 == [1, 4, 9, 16, 25]

    # Verify it's cached in instance __dict__
    print(f"  'processed' in dp.__dict__: {('processed' in dp.__dict__)}")
    assert "processed" in dp.__dict__

    # Summary depends on processed
    print("  First access to summary:")
    s = dp.summary
    print(f"  summary = {s}")
    assert s == {"count": 5, "total": 55, "mean": 11.0}

    print()

    # --- Section 8: How methods are descriptors ---
    print("--- Section 8: Methods as Descriptors ---")

    class Dog:
        def bark(self):
            return "Woof!"

    dog = Dog()

    # Accessing via class → unbound function
    print(f"  Dog.bark = {Dog.bark}")
    assert callable(Dog.bark)

    # Accessing via instance → bound method
    print(f"  dog.bark = {dog.bark}")
    assert "bound method" in str(dog.bark)

    # Manual descriptor call
    bound = Dog.bark.__get__(dog, Dog)
    print(f"  Dog.bark.__get__(dog, Dog) = {bound}")
    assert bound() == "Woof!"
    assert dog.bark() == "Woof!"

    # Functions have __get__
    print(f"  hasattr(Dog.bark, '__get__') = {hasattr(Dog.bark, '__get__')}")
    assert hasattr(Dog.bark, "__get__")

    # Functions do NOT have __set__ → non-data descriptor
    print(f"  hasattr(Dog.bark, '__set__') = {hasattr(Dog.bark, '__set__')}")
    assert not hasattr(Dog.bark, "__set__")

    print()

    # --- Section 9: Descriptor lookup order ---
    print("--- Section 9: Descriptor Lookup Order ---")

    print("  Attribute lookup order:")
    print("    1. Data descriptors (has __set__ or __delete__) on class MRO")
    print("    2. Instance __dict__")
    print("    3. Non-data descriptors (only __get__) on class MRO")
    print("    4. Plain class attributes")
    print("    5. __getattr__ (if defined)")
    print("    6. AttributeError")

    # Demonstrate with property (data descriptor)
    class PropDemo:
        @property
        def x(self):
            return "from property"

    pd = PropDemo()
    # Even if we force a value into __dict__, property wins
    pd.__dict__["x"] = "from instance"
    print(f"  PropDemo instance with __dict__['x'] = 'from instance'")
    print(f"  pd.x = {pd.x!r}")
    assert pd.x == "from property"  # Data descriptor wins!

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Properties & descriptors in Python:")
    print("  - @property: computed attributes with getter/setter/deleter")
    print("  - Temperature: celsius/fahrenheit/kelvin with validation")
    print("  - Descriptor protocol: __get__, __set__, __delete__, __set_name__")
    print("  - Data descriptors: define __set__ or __delete__, win over instance __dict__")
    print("  - Non-data descriptors: only __get__, instance __dict__ can override")
    print("  - Validated descriptor: reusable type + range checking")
    print("  - LazyProperty: compute once, cache in instance __dict__")
    print("  - Methods are non-data descriptors (function.__get__ returns bound method)")
    print()
    print("All 9 sections passed. You've mastered properties & descriptors!")
