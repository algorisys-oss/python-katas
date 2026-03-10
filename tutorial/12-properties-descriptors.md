# Kata 12 -- Properties & Descriptors

[prev: 11-classes-inheritance](./11-classes-inheritance.md) | [next: 13-metaclasses](./13-metaclasses.md)

---

## What We're Building

Python's attribute access is deceptively powerful. Behind every `obj.x` is a protocol that lets you intercept reads, writes, and deletes. The `@property` decorator is the friendly face of this system, but underneath lies the **descriptor protocol** -- one of Python's most important mechanisms. Descriptors power properties, methods, `classmethod`, `staticmethod`, `__slots__`, and even plain function binding.

In this kata we'll build a `Temperature` class with property-based Celsius/Fahrenheit conversion, a reusable `Validated` descriptor for type and range checking, and a `LazyProperty` descriptor for deferred computation. By the end you'll understand the machinery behind `@property` and be able to build your own attribute-level abstractions.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `@property` | Define computed attributes with getter/setter/deleter | Controlled attribute access without changing API |
| Getter/Setter/Deleter | Read/write/delete hooks on an attribute | Validation, transformation, side effects |
| `__get__` / `__set__` / `__delete__` | Descriptor protocol methods | Reusable attribute behavior across classes |
| `__set_name__` | Automatic attribute name discovery | Descriptors that need to know their own name |
| Data descriptor | Defines `__set__` or `__delete__` | Override instance `__dict__` (properties, validated fields) |
| Non-data descriptor | Only defines `__get__` | Provide defaults, can be overridden by instance attrs |
| Computed attributes | Derived values calculated on access | Fahrenheit from Celsius, full name from parts |
| Validation descriptors | Reusable type/range enforcement | Schema-like field validation without external libs |

## The Code

### Step 1: The `@property` decorator -- computed attributes

The simplest way to add logic to attribute access. A property looks like an attribute from the outside but calls methods behind the scenes.

```python
class Circle:
    def __init__(self, radius):
        self._radius = radius  # Convention: _ prefix for "private"

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
        import math
        return math.pi * self._radius ** 2

c = Circle(5)
print(c.radius)   # 5 -- calls the getter
print(c.area)     # 78.539... -- computed on access
c.radius = 10     # calls the setter
print(c.radius)   # 10
# c.area = 100    # AttributeError: can't set (no setter defined)
```

The key insight: **`@property` lets you start with a plain attribute and add validation/computation later without changing the caller's code.** This is why Python doesn't need Java-style getters and setters.

### Step 2: Temperature class -- full property lifecycle

A `Temperature` class that stores Celsius internally but exposes both Celsius and Fahrenheit as properties, with validation.

```python
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
        print("Resetting temperature to 0°C")
        self._celsius = 0.0

    @property
    def fahrenheit(self):
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value):
        self.celsius = (value - 32) * 5 / 9  # Reuses celsius setter validation

    def __repr__(self):
        return f"Temperature({self._celsius}°C / {self.fahrenheit}°F)"

t = Temperature(100)
print(t)               # Temperature(100.0°C / 212.0°F)
print(t.fahrenheit)    # 212.0
t.fahrenheit = 32
print(t.celsius)       # 0.0
del t.celsius          # Resetting temperature to 0°C
```

### Step 3: The descriptor protocol -- `__get__`, `__set__`, `__delete__`

A **descriptor** is any object that defines `__get__`, `__set__`, or `__delete__`. When such an object is a class attribute, Python calls these methods instead of normal attribute access.

```python
class Verbose:
    """A descriptor that prints every access."""

    def __set_name__(self, owner, name):
        # Called automatically when the descriptor is assigned to a class attribute
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # Accessed from the class, not an instance
        value = getattr(obj, self.private_name, "NOT SET")
        print(f"  Getting {self.name}: {value}")
        return value

    def __set__(self, obj, value):
        print(f"  Setting {self.name} = {value}")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj):
        print(f"  Deleting {self.name}")
        delattr(obj, self.private_name)

class Demo:
    x = Verbose()
    y = Verbose()

d = Demo()
d.x = 10         # Setting x = 10
d.y = 20         # Setting y = 20
print(d.x)       # Getting x: 10 → prints 10
del d.x          # Deleting x
```

The `__set_name__` method (Python 3.6+) is called by the metaclass when the class is created, passing the owner class and the attribute name. This means the descriptor knows its own name without you telling it.

### Step 4: Data vs non-data descriptors

This distinction controls **attribute lookup priority**:

- **Data descriptor** (defines `__set__` and/or `__delete__`): Takes priority over instance `__dict__`. Properties are data descriptors.
- **Non-data descriptor** (only defines `__get__`): Instance `__dict__` takes priority. Functions are non-data descriptors (which is how method binding works).

```python
class DataDescriptor:
    """Has __set__ → always wins over instance __dict__."""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(f"_dd_{self.name}", "default")

    def __set__(self, obj, value):
        obj.__dict__[f"_dd_{self.name}"] = value

class NonDataDescriptor:
    """Only __get__ → instance __dict__ can override."""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return f"NonDataDescriptor({self.name})"

class Lookup:
    data = DataDescriptor()
    nondata = NonDataDescriptor()

obj = Lookup()
obj.data = "via descriptor"
print(obj.data)                      # "via descriptor" -- data descriptor wins

# Non-data descriptor can be shadowed by instance attribute
obj.__dict__["nondata"] = "instance wins"
print(obj.nondata)                   # "instance wins" -- instance __dict__ wins
```

**Lookup order:**
1. Data descriptors on the class (and its MRO)
2. Instance `__dict__`
3. Non-data descriptors on the class (and its MRO)

### Step 5: Validated descriptor -- reusable type and range checking

This is where descriptors shine: build once, reuse across classes. A `Validated` descriptor enforces type constraints and optional min/max range.

```python
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
                f"{self.name} must be {self.expected_type.__name__}, "
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
        self.name = name          # Goes through Validated.__set__
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"Product({self.name!r}, ${self.price}, qty={self.quantity})"

p = Product("Widget", 9.99, 100)
print(p)  # Product('Widget', $9.99, qty=100)

# p.price = -1     # ValueError: price must be >= 0, got -1
# p.quantity = "a"  # TypeError: quantity must be int, got str
# p.name = 42       # TypeError: name must be str, got int
```

### Step 6: LazyProperty descriptor -- computed once, cached forever

A non-data descriptor that computes a value on first access and caches it in the instance `__dict__`. Because it's a non-data descriptor (no `__set__`), the cached instance attribute shadows it on subsequent access -- no computation cost after the first call.

```python
class LazyProperty:
    """Descriptor that computes a value once and caches it on the instance."""

    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Compute the value
        value = self.func(obj)
        # Cache it directly on the instance -- shadows the descriptor
        setattr(obj, self.name, value)
        return value

class DataProcessor:
    def __init__(self, data):
        self.data = data

    @LazyProperty
    def processed(self):
        """Expensive computation, only done once."""
        print("  Computing processed data...")
        return [x ** 2 for x in self.data]

    @LazyProperty
    def summary(self):
        """Depends on processed data."""
        print("  Computing summary...")
        return {
            "count": len(self.processed),
            "total": sum(self.processed),
            "mean": sum(self.processed) / len(self.processed),
        }

dp = DataProcessor([1, 2, 3, 4, 5])
print(dp.processed)   # Computing processed data... → [1, 4, 9, 16, 25]
print(dp.processed)   # No computation! Cached in instance __dict__
print(dp.summary)     # Computing summary... → {'count': 5, 'total': 55, 'mean': 11.0}
```

This pattern is so useful that Python 3.8+ includes `functools.cached_property` which does the same thing. But building it yourself teaches you exactly how non-data descriptors work.

### Step 7: How methods are descriptors

Functions are non-data descriptors. When you access a function through an instance, its `__get__` method returns a bound method:

```python
class Dog:
    def bark(self):
        return "Woof!"

d = Dog()

# Accessing via the class → unbound function
print(Dog.bark)         # <function Dog.bark at ...>

# Accessing via the instance → bound method (self is baked in)
print(d.bark)           # <bound method Dog.bark of <Dog object>>

# This is equivalent:
print(Dog.bark.__get__(d, Dog))  # <bound method Dog.bark of <Dog object>>

# That's why d.bark() works -- it calls Dog.bark.__get__(d, Dog)()
print(d.bark())         # Woof!
```

This is why `self` appears automatically -- the descriptor protocol binds the instance as the first argument.

## Playground

Run the full interactive demo:

```bash
python playground/12_properties_descriptors.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Property mechanics

`@property` creates a **data descriptor** object with `__get__`, `__set__`, and `__delete__` methods. The decorator syntax is syntactic sugar:

```
class C:
    @property          # celsius = property(fget=celsius_getter)
    def celsius(self): ...

    @celsius.setter    # celsius = celsius.setter(celsius_setter)
    def celsius(self, value): ...
```

The property object stores references to the getter, setter, and deleter functions. When you access the attribute, Python finds the property descriptor on the class and calls the appropriate method.

### Descriptor lookup order

```
obj.attr
  1. type(obj).__mro__  → find attr on a class in the MRO
  2. If attr is a DATA descriptor (has __set__ or __delete__):
       → call attr.__get__(obj, type(obj))
  3. If attr is in obj.__dict__:
       → return obj.__dict__["attr"]
  4. If attr is a NON-DATA descriptor (only __get__):
       → call attr.__get__(obj, type(obj))
  5. If attr is a plain class attribute:
       → return it
  6. → raise AttributeError
```

### Why LazyProperty works

`LazyProperty` only defines `__get__` (non-data descriptor). On first access, it computes the value and stores it in `obj.__dict__` under the same name. On subsequent access, step 3 above finds the value in `obj.__dict__` before reaching step 4, so the descriptor is never called again.

## Exercises

### Exercise 1: Add a `kelvin` property to Temperature

Extend the `Temperature` class with a `kelvin` property that converts to/from Celsius (Kelvin = Celsius + 273.15). The setter should validate that Kelvin is not negative.

```python
t = Temperature(0)
print(t.kelvin)       # 273.15
t.kelvin = 373.15
print(t.celsius)      # 100.0
# t.kelvin = -1       # ValueError
```

### Exercise 2: Build a `StringField` descriptor

Create a `StringField` descriptor that enforces string type, optional `min_length` and `max_length`, and an optional `pattern` (regex). Use it to validate user input fields.

```python
import re

class StringField:
    def __init__(self, *, min_length=0, max_length=None, pattern=None): ...

class User:
    username = StringField(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    email = StringField(pattern=r"^[^@]+@[^@]+\.[^@]+$")

u = User()
u.username = "alice_42"      # OK
# u.username = "ab"          # ValueError: too short
# u.username = "inv@lid!"    # ValueError: doesn't match pattern
```

### Exercise 3: Build a `CachedProperty` with TTL

Extend `LazyProperty` to accept a `ttl` (time-to-live in seconds). After the TTL expires, the next access recomputes the value.

```python
import time

class CachedProperty:
    def __init__(self, func=None, *, ttl=None): ...

class StockPrice:
    @CachedProperty(ttl=5)
    def price(self):
        # Simulate expensive API call
        return round(random.uniform(100, 200), 2)

s = StockPrice()
print(s.price)       # Computed
print(s.price)       # Cached
time.sleep(6)
print(s.price)       # Recomputed (TTL expired)
```

## What's Next

In [Kata 13 -- Metaclasses](./13-metaclasses.md), we'll go deeper into Python's object model and explore **metaclasses** -- the classes that create classes. You'll learn how `type` works as both a function and a metaclass, build custom metaclasses for automatic registration and validation, and understand how `__init_subclass__` provides a simpler alternative for many metaclass use cases.

---

[prev: 11-classes-inheritance](./11-classes-inheritance.md) | [next: 13-metaclasses](./13-metaclasses.md)
