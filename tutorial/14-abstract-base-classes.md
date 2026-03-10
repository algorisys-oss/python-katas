# Kata 14 -- Abstract Base Classes

[prev: 13-metaclasses](./13-metaclasses.md) | [next: 15-single-responsibility](./15-single-responsibility.md)

---

## What We're Building

Abstract Base Classes (ABCs) let you define **interfaces** that subclasses must implement. Unlike duck typing where errors surface at runtime when a method is missing, ABCs catch incomplete implementations **at instantiation time**. They sit between Python's permissive duck typing and strict interface enforcement.

In this kata we'll build a Shape ABC hierarchy with abstract methods and properties, create a custom Container ABC, explore virtual subclasses with `register()` and `__subclasshook__`, compare ABCs with Protocols (structural vs nominal typing), and tour the `collections.abc` module that powers Python's built-in container interfaces.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `abc.ABC` | Base class for defining abstract classes | When you need to enforce an interface |
| `@abstractmethod` | Marks a method that subclasses must implement | Required methods in your interface |
| Abstract properties | `@property` + `@abstractmethod` for required properties | Required computed attributes |
| `register()` | Declare a class as a "virtual subclass" without inheritance | Third-party classes that match your interface |
| `__subclasshook__` | Customize `isinstance()`/`issubclass()` checks | Structural type checking at runtime |
| ABCs vs Protocols | Nominal (ABC) vs structural (Protocol) subtyping | ABC for enforcement, Protocol for flexibility |
| `collections.abc` | Standard library ABCs for containers | Implementing custom containers correctly |

## The Code

### Step 1: Your first ABC with `abc.ABC` and `@abstractmethod`

An abstract base class defines an interface. You cannot instantiate it directly -- you must subclass it and implement all abstract methods.

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    """Abstract base class for geometric shapes."""

    @abstractmethod
    def area(self) -> float:
        """Calculate the area of the shape."""
        ...

    @abstractmethod
    def perimeter(self) -> float:
        """Calculate the perimeter of the shape."""
        ...

    def describe(self) -> str:
        """Concrete method -- subclasses inherit this."""
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"
```

Key points:
- `ABC` is a convenience class -- it sets `ABCMeta` as the metaclass.
- `@abstractmethod` marks methods that subclasses **must** override.
- You can mix abstract and concrete methods. Concrete methods can call abstract ones.
- Attempting to instantiate `Shape()` directly raises `TypeError`.

### Step 2: Implementing the ABC

```python
import math

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

c = Circle(5)
r = Rectangle(3, 4)
print(c.describe())  # Circle: area=78.54, perimeter=31.42
print(r.describe())  # Rectangle: area=12.00, perimeter=14.00

# Both are Shape instances
print(isinstance(c, Shape))  # True
print(isinstance(r, Shape))  # True
```

If you forget to implement a required method, Python catches it immediately:

```python
class BadShape(Shape):
    def area(self) -> float:
        return 0.0
    # Missing perimeter()!

# TypeError: Can't instantiate abstract class BadShape
# with abstract method perimeter
# bad = BadShape()
```

### Step 3: Abstract properties

You can combine `@property` with `@abstractmethod` to require computed attributes:

```python
class Animal(ABC):
    @property
    @abstractmethod
    def sound(self) -> str:
        """The sound this animal makes."""
        ...

    @property
    @abstractmethod
    def legs(self) -> int:
        """Number of legs."""
        ...

    def describe(self) -> str:
        return f"{self.__class__.__name__}: {self.legs} legs, says '{self.sound}'"

class Dog(Animal):
    @property
    def sound(self) -> str:
        return "Woof"

    @property
    def legs(self) -> int:
        return 4

class Snake(Animal):
    @property
    def sound(self) -> str:
        return "Hiss"

    @property
    def legs(self) -> int:
        return 0

print(Dog().describe())    # Dog: 4 legs, says 'Woof'
print(Snake().describe())  # Snake: 0 legs, says 'Hiss'
```

**Important:** `@property` must come **before** `@abstractmethod` in the decorator stack (outermost first). Python 3.3+ handles this correctly in either order, but the convention is `@property` on top.

### Step 4: Virtual subclasses with `register()`

Sometimes you want a class to be considered a subclass of your ABC **without actually inheriting from it**. This is useful for third-party classes you cannot modify.

```python
class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> str:
        ...

# This class doesn't inherit from Serializable
class JsonConfig:
    def __init__(self, data: dict):
        self.data = data

    def serialize(self) -> str:
        import json
        return json.dumps(self.data)

# Register it as a virtual subclass
Serializable.register(JsonConfig)

config = JsonConfig({"key": "value"})
print(isinstance(config, Serializable))    # True
print(issubclass(JsonConfig, Serializable))  # True
```

**Warning:** `register()` does NOT enforce that the class actually implements the abstract methods. It is a declaration of intent -- you are promising that the class conforms. If it does not, you will get runtime errors when calling the methods.

### Step 5: `__subclasshook__` -- structural checking

`__subclasshook__` lets you define custom `isinstance()`/`issubclass()` logic based on what methods a class has, rather than its inheritance tree. This brings **structural typing** to ABCs.

```python
class Renderable(ABC):
    @abstractmethod
    def render(self) -> str:
        ...

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Renderable:
            # Check if C has a 'render' method
            if hasattr(C, "render"):
                return True
        return NotImplemented

# This class has a render() method but doesn't inherit from Renderable
class HtmlWidget:
    def render(self) -> str:
        return "<div>Widget</div>"

# This class does NOT have render()
class PlainText:
    def display(self) -> str:
        return "plain text"

print(isinstance(HtmlWidget(), Renderable))   # True  (has render)
print(isinstance(PlainText(), Renderable))     # False (no render)
print(issubclass(HtmlWidget, Renderable))      # True
```

Returning `NotImplemented` from `__subclasshook__` falls back to the normal `isinstance()` behavior (checking the inheritance chain and registered subclasses).

### Step 6: ABCs vs Protocols -- when to use each

Python offers two ways to define interfaces: **ABCs** (nominal typing) and **Protocols** (structural typing from `typing`). They solve different problems.

```python
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

# ABC approach: classes MUST inherit or register
class DrawableABC(ABC):
    @abstractmethod
    def draw(self) -> str:
        ...

class CircleABC(DrawableABC):
    def draw(self) -> str:
        return "Drawing circle (ABC)"

# Protocol approach: classes just need matching methods
@runtime_checkable
class DrawableProto(Protocol):
    def draw(self) -> str:
        ...

class Square:
    """No inheritance needed -- just has draw()."""
    def draw(self) -> str:
        return "Drawing square (Protocol)"

# ABC: requires explicit inheritance
print(isinstance(CircleABC(), DrawableABC))    # True
# print(isinstance(Square(), DrawableABC))     # False -- no inheritance

# Protocol: checks structure (with @runtime_checkable)
print(isinstance(Square(), DrawableProto))     # True -- has draw()
print(isinstance(CircleABC(), DrawableProto))  # True -- also has draw()
```

**When to use ABCs:**
- You want to **enforce** that subclasses implement methods (catch at instantiation time).
- You need shared concrete methods that call abstract ones (template method pattern).
- You want `register()` for third-party classes.
- You are building a framework where implementers explicitly opt in.

**When to use Protocols:**
- You want **duck typing with type checker support** -- no inheritance required.
- You are writing library code that accepts "anything with method X".
- You want maximum flexibility and decoupling.
- You are working with third-party code you cannot modify and do not want to register.

**Rule of thumb:** Use Protocols for function parameters ("I accept anything drawable"). Use ABCs for class hierarchies ("all shapes must implement area and perimeter").

### Step 7: `collections.abc` -- standard library ABCs

Python's `collections.abc` module defines ABCs for container types. When you implement a custom container, inheriting from these ABCs tells Python (and type checkers) what your container can do.

```python
from collections.abc import Sized, Iterable, Container, Sequence

# Check what built-in types implement
print(isinstance([1, 2], Sized))      # True
print(isinstance([1, 2], Iterable))   # True
print(isinstance([1, 2], Sequence))   # True
print(isinstance({1, 2}, Sequence))   # False -- sets are not sequences
```

Key `collections.abc` ABCs:

| ABC | Required Methods | Mixin Methods Provided |
|---|---|---|
| `Iterable` | `__iter__` | -- |
| `Iterator` | `__next__` | `__iter__` |
| `Sized` | `__len__` | -- |
| `Container` | `__contains__` | -- |
| `Collection` | `__contains__`, `__iter__`, `__len__` | -- |
| `Sequence` | `__getitem__`, `__len__` | `__contains__`, `__iter__`, `__reversed__`, `index`, `count` |
| `MutableSequence` | `__getitem__`, `__setitem__`, `__delitem__`, `__len__`, `insert` | `append`, `clear`, `reverse`, `extend`, `pop`, `__iadd__`, `__contains__`, `index`, `count` |
| `Mapping` | `__getitem__`, `__len__`, `__iter__` | `__contains__`, `keys`, `items`, `values`, `get`, `__eq__`, `__ne__` |
| `Set` | `__contains__`, `__iter__`, `__len__` | Comparison operators, `__and__`, `__or__`, `__sub__`, `__xor__`, `isdisjoint` |

The power of these ABCs is the **mixin methods**: implement a few required methods and get many more for free.

### Step 8: Building a custom Container ABC

Let us build a `TypedCollection` ABC that enforces type-safe containers, then implement it:

```python
from abc import ABC, abstractmethod
from collections.abc import Iterator

class TypedCollection(ABC):
    """ABC for type-safe collections."""

    @property
    @abstractmethod
    def element_type(self) -> type:
        """The type of elements this collection holds."""
        ...

    @abstractmethod
    def add(self, item) -> None:
        """Add an item (must match element_type)."""
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator:
        ...

    @abstractmethod
    def __contains__(self, item) -> bool:
        ...

    def validate(self, item) -> None:
        """Check that item matches element_type."""
        if not isinstance(item, self.element_type):
            raise TypeError(
                f"Expected {self.element_type.__name__}, "
                f"got {type(item).__name__}"
            )

class TypedSet(TypedCollection):
    """A set that only accepts elements of a specific type."""

    def __init__(self, elem_type: type):
        self._type = elem_type
        self._data: set = set()

    @property
    def element_type(self) -> type:
        return self._type

    def add(self, item) -> None:
        self.validate(item)
        self._data.add(item)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def __contains__(self, item) -> bool:
        return item in self._data

    def __repr__(self) -> str:
        return f"TypedSet({self._type.__name__}, {self._data})"

int_set = TypedSet(int)
int_set.add(1)
int_set.add(2)
int_set.add(3)
print(int_set)         # TypedSet(int, {1, 2, 3})
print(len(int_set))    # 3
print(2 in int_set)    # True

# Type safety:
# int_set.add("hello")  # TypeError: Expected int, got str
```

## Playground

Run the full interactive demo:

```bash
python playground/14_abstract_base_classes.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### ABC enforcement mechanics

When Python creates a class with `ABCMeta` as its metaclass (which `ABC` provides), it tracks all methods decorated with `@abstractmethod` in a set called `__abstractmethods__`. At instantiation time (`__call__` on the metaclass), Python checks if this set is empty. If not, it raises `TypeError`.

```
class Shape(ABC):
    @abstractmethod
    def area(self): ...
    @abstractmethod
    def perimeter(self): ...

Shape.__abstractmethods__  →  frozenset({'area', 'perimeter'})

class Circle(Shape):
    def area(self): ...
    def perimeter(self): ...

Circle.__abstractmethods__  →  frozenset()  (all implemented)
Circle()  →  OK

class BadShape(Shape):
    def area(self): ...

BadShape.__abstractmethods__  →  frozenset({'perimeter'})
BadShape()  →  TypeError!
```

### Virtual subclass resolution

When you call `isinstance(obj, SomeABC)`, Python checks in order:
1. Is `type(obj)` in the MRO of `SomeABC`? (normal inheritance)
2. Has `type(obj)` been registered with `SomeABC.register()`?
3. Does `SomeABC.__subclasshook__(type(obj))` return `True`?

### ABCs vs Protocols at a glance

```
ABC (Nominal Typing)              Protocol (Structural Typing)
─────────────────────              ──────────────────────────────
Must inherit or register            Just implement the methods
Enforced at instantiation           Checked by type checker (mypy)
Shared concrete methods             No shared implementation
register() for third parties        @runtime_checkable for isinstance()
"Is-a" relationship                 "Has-the-right-methods" relationship
```

## Exercises

### Exercise 1: Extend the Shape hierarchy

Add a `Triangle` class that takes three side lengths. It must implement both `area()` (use Heron's formula) and `perimeter()`. Verify it works with `describe()`.

```python
class Triangle(Shape):
    def __init__(self, a: float, b: float, c: float):
        # Validate triangle inequality
        ...

    def area(self) -> float:
        # Heron's formula: s = (a+b+c)/2, area = sqrt(s*(s-a)*(s-b)*(s-c))
        ...

    def perimeter(self) -> float:
        ...

t = Triangle(3, 4, 5)
print(t.describe())
# Expected: Triangle: area=6.00, perimeter=12.00
```

### Exercise 2: Build a Plugin ABC with `__subclasshook__`

Create a `Plugin` ABC that considers any class with `name` (property) and `execute()` method as a valid subclass, even without inheritance:

```python
class Plugin(ABC):
    @classmethod
    def __subclasshook__(cls, C):
        # Check for 'name' and 'execute' attributes
        ...

class MyPlugin:
    """Does NOT inherit from Plugin."""
    name = "my-plugin"

    def execute(self, data):
        return f"Processing {data}"

print(isinstance(MyPlugin(), Plugin))  # True
```

### Exercise 3: Compare ABC and Protocol approaches

Implement a `Cacheable` interface both as an ABC and as a Protocol. Create two classes: one using each approach. Show that the Protocol version works without inheritance while the ABC version requires it.

## What's Next

In [Kata 15 -- Single Responsibility Principle](./15-single-responsibility.md), we'll apply the first SOLID principle: every class should have exactly one reason to change. You'll refactor a monolithic class into focused, composable components -- using the ABCs and Protocols you learned here to define clean interfaces between them.

---

[prev: 13-metaclasses](./13-metaclasses.md) | [next: 15-single-responsibility](./15-single-responsibility.md)
