"""
Kata 14 -- Abstract Base Classes
Run: python playground/14_abstract_base_classes.py

Master abc.ABC, @abstractmethod, abstract properties, virtual subclasses with
register(), __subclasshook__, ABCs vs Protocols, and collections.abc ABCs.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Protocol, runtime_checkable
import math


# ===========================================================================
# CLASS DEFINITIONS (used by demonstrations below)
# ===========================================================================

# --- Shape ABC hierarchy ---

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


class Triangle(Shape):
    """Triangle using Heron's formula for area."""

    def __init__(self, a: float, b: float, c: float):
        if a + b <= c or a + c <= b or b + c <= a:
            raise ValueError(f"Invalid triangle sides: {a}, {b}, {c}")
        self.a = a
        self.b = b
        self.c = c

    def area(self) -> float:
        s = (self.a + self.b + self.c) / 2
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))

    def perimeter(self) -> float:
        return self.a + self.b + self.c


# --- Animal ABC with abstract properties ---

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


# --- Serializable ABC with register() ---

class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> str:
        ...


class JsonConfig:
    """Does NOT inherit from Serializable."""

    def __init__(self, data: dict):
        self.data = data

    def serialize(self) -> str:
        import json
        return json.dumps(self.data)


# Register as virtual subclass
Serializable.register(JsonConfig)


# --- Renderable ABC with __subclasshook__ ---

class Renderable(ABC):
    @abstractmethod
    def render(self) -> str:
        ...

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Renderable:
            if hasattr(C, "render"):
                return True
        return NotImplemented


class HtmlWidget:
    """Has render() but does NOT inherit from Renderable."""

    def render(self) -> str:
        return "<div>Widget</div>"


class PlainText:
    """Does NOT have render()."""

    def display(self) -> str:
        return "plain text"


# --- ABCs vs Protocols comparison ---

class DrawableABC(ABC):
    @abstractmethod
    def draw(self) -> str:
        ...


class CircleDrawableABC(DrawableABC):
    def draw(self) -> str:
        return "Drawing circle (ABC)"


@runtime_checkable
class DrawableProto(Protocol):
    def draw(self) -> str:
        ...


class Square:
    """No inheritance -- just has draw()."""

    def draw(self) -> str:
        return "Drawing square (Protocol)"


# --- Custom Container ABC: TypedCollection ---

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


# --- Plugin ABC with __subclasshook__ (Exercise 2) ---

class Plugin(ABC):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Plugin:
            if hasattr(C, "name") and hasattr(C, "execute"):
                return True
        return NotImplemented


class MyPlugin:
    """Does NOT inherit from Plugin."""
    name = "my-plugin"

    def execute(self, data):
        return f"Processing {data}"


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Basic ABC with @abstractmethod ---
    print("--- Section 1: Basic ABC with @abstractmethod ---")

    # Cannot instantiate abstract class
    try:
        Shape()
    except TypeError as e:
        print(f"  Shape() raises: {e}")

    c = Circle(5)
    r = Rectangle(3, 4)

    print(f"  {c.describe()}")
    assert abs(c.area() - 78.5398) < 0.01
    assert abs(c.perimeter() - 31.4159) < 0.01

    print(f"  {r.describe()}")
    assert r.area() == 12.0
    assert r.perimeter() == 14.0

    # Both are Shape instances
    assert isinstance(c, Shape)
    assert isinstance(r, Shape)
    print(f"  isinstance(Circle(5), Shape) = True")
    print(f"  isinstance(Rectangle(3,4), Shape) = True")

    print()

    # --- Section 2: Incomplete implementation caught at instantiation ---
    print("--- Section 2: Incomplete Implementation ---")

    class BadShape(Shape):
        def area(self) -> float:
            return 0.0
        # Missing perimeter()!

    try:
        BadShape()
    except TypeError as e:
        print(f"  BadShape() raises: {e}")
        assert "perimeter" in str(e)

    print()

    # --- Section 3: Triangle (Heron's formula) ---
    print("--- Section 3: Triangle ---")

    t = Triangle(3, 4, 5)
    print(f"  {t.describe()}")
    assert abs(t.area() - 6.0) < 0.01
    assert t.perimeter() == 12.0

    # Invalid triangle
    try:
        Triangle(1, 2, 10)
    except ValueError as e:
        print(f"  Triangle(1,2,10) raises: {e}")

    print()

    # --- Section 4: Abstract properties ---
    print("--- Section 4: Abstract Properties ---")

    # Cannot instantiate Animal directly
    try:
        Animal()
    except TypeError as e:
        print(f"  Animal() raises: {e}")

    dog = Dog()
    snake = Snake()

    print(f"  {dog.describe()}")
    assert dog.sound == "Woof"
    assert dog.legs == 4

    print(f"  {snake.describe()}")
    assert snake.sound == "Hiss"
    assert snake.legs == 0

    print()

    # --- Section 5: Virtual subclasses with register() ---
    print("--- Section 5: Virtual Subclasses (register) ---")

    config = JsonConfig({"key": "value"})

    print(f"  isinstance(JsonConfig(...), Serializable) = {isinstance(config, Serializable)}")
    assert isinstance(config, Serializable)

    print(f"  issubclass(JsonConfig, Serializable) = {issubclass(JsonConfig, Serializable)}")
    assert issubclass(JsonConfig, Serializable)

    # But JsonConfig is NOT in Serializable's MRO
    print(f"  Serializable in JsonConfig.__mro__ = {Serializable in JsonConfig.__mro__}")
    assert Serializable not in JsonConfig.__mro__

    # The serialize method still works
    result = config.serialize()
    print(f"  config.serialize() = {result!r}")
    assert result == '{"key": "value"}'

    print()

    # --- Section 6: __subclasshook__ ---
    print("--- Section 6: __subclasshook__ ---")

    widget = HtmlWidget()
    text = PlainText()

    print(f"  isinstance(HtmlWidget(), Renderable) = {isinstance(widget, Renderable)}")
    assert isinstance(widget, Renderable)

    print(f"  isinstance(PlainText(), Renderable) = {isinstance(text, Renderable)}")
    assert not isinstance(text, Renderable)

    print(f"  issubclass(HtmlWidget, Renderable) = {issubclass(HtmlWidget, Renderable)}")
    assert issubclass(HtmlWidget, Renderable)

    print(f"  issubclass(PlainText, Renderable) = {issubclass(PlainText, Renderable)}")
    assert not issubclass(PlainText, Renderable)

    print()

    # --- Section 7: ABCs vs Protocols ---
    print("--- Section 7: ABCs vs Protocols ---")

    circle_abc = CircleDrawableABC()
    square = Square()

    # ABC: requires explicit inheritance
    print(f"  isinstance(CircleDrawableABC(), DrawableABC) = {isinstance(circle_abc, DrawableABC)}")
    assert isinstance(circle_abc, DrawableABC)
    print(f"  isinstance(Square(), DrawableABC) = {isinstance(square, DrawableABC)}")
    assert not isinstance(square, DrawableABC)

    # Protocol: checks structure
    print(f"  isinstance(Square(), DrawableProto) = {isinstance(square, DrawableProto)}")
    assert isinstance(square, DrawableProto)
    print(f"  isinstance(CircleDrawableABC(), DrawableProto) = {isinstance(circle_abc, DrawableProto)}")
    assert isinstance(circle_abc, DrawableProto)

    # Both produce output
    print(f"  {circle_abc.draw()}")
    assert circle_abc.draw() == "Drawing circle (ABC)"
    print(f"  {square.draw()}")
    assert square.draw() == "Drawing square (Protocol)"

    # A class without draw() fails Protocol check
    class NoDraw:
        pass

    print(f"  isinstance(NoDraw(), DrawableProto) = {isinstance(NoDraw(), DrawableProto)}")
    assert not isinstance(NoDraw(), DrawableProto)

    print()

    # --- Section 8: collections.abc ---
    print("--- Section 8: collections.abc ---")

    from collections.abc import Sized, Iterable, Container, Sequence

    # Built-in types implement these ABCs
    print(f"  isinstance([1,2], Sized) = {isinstance([1, 2], Sized)}")
    assert isinstance([1, 2], Sized)

    print(f"  isinstance([1,2], Iterable) = {isinstance([1, 2], Iterable)}")
    assert isinstance([1, 2], Iterable)

    print(f"  isinstance([1,2], Sequence) = {isinstance([1, 2], Sequence)}")
    assert isinstance([1, 2], Sequence)

    print(f"  isinstance({{1,2}}, Sequence) = {isinstance({1, 2}, Sequence)}")
    assert not isinstance({1, 2}, Sequence)

    print(f"  isinstance({{1,2}}, Container) = {isinstance({1, 2}, Container)}")
    assert isinstance({1, 2}, Container)

    # dict is a Mapping, not a Sequence
    from collections.abc import Mapping

    print(f"  isinstance({{}}, Mapping) = {isinstance({}, Mapping)}")
    assert isinstance({}, Mapping)

    print(f"  isinstance({{}}, Sequence) = {isinstance({}, Sequence)}")
    assert not isinstance({}, Sequence)

    print()

    # --- Section 9: Custom Container ABC (TypedCollection) ---
    print("--- Section 9: Custom Container ABC ---")

    int_set = TypedSet(int)
    int_set.add(1)
    int_set.add(2)
    int_set.add(3)

    print(f"  {int_set}")
    assert len(int_set) == 3
    assert 2 in int_set
    assert 99 not in int_set

    print(f"  len(int_set) = {len(int_set)}")
    print(f"  2 in int_set = {2 in int_set}")

    # Iteration
    items = sorted(int_set)
    print(f"  sorted(int_set) = {items}")
    assert items == [1, 2, 3]

    # Type safety: reject wrong types
    try:
        int_set.add("hello")
    except TypeError as e:
        print(f"  int_set.add('hello') raises: {e}")
        assert "Expected int" in str(e)

    # TypedSet is a TypedCollection
    assert isinstance(int_set, TypedCollection)
    print(f"  isinstance(int_set, TypedCollection) = True")

    # String set
    str_set = TypedSet(str)
    str_set.add("hello")
    str_set.add("world")
    print(f"  {str_set}")
    assert len(str_set) == 2
    assert "hello" in str_set

    try:
        str_set.add(42)
    except TypeError as e:
        print(f"  str_set.add(42) raises: {e}")
        assert "Expected str" in str(e)

    print()

    # --- Section 10: Plugin ABC with __subclasshook__ (Exercise) ---
    print("--- Section 10: Plugin ABC with __subclasshook__ ---")

    plugin = MyPlugin()

    print(f"  isinstance(MyPlugin(), Plugin) = {isinstance(plugin, Plugin)}")
    assert isinstance(plugin, Plugin)

    print(f"  issubclass(MyPlugin, Plugin) = {issubclass(MyPlugin, Plugin)}")
    assert issubclass(MyPlugin, Plugin)

    print(f"  plugin.name = {plugin.name!r}")
    assert plugin.name == "my-plugin"

    result = plugin.execute("test-data")
    print(f"  plugin.execute('test-data') = {result!r}")
    assert result == "Processing test-data"

    # A class without execute should NOT be a Plugin
    class NotAPlugin:
        name = "nope"

    print(f"  isinstance(NotAPlugin(), Plugin) = {isinstance(NotAPlugin(), Plugin)}")
    assert not isinstance(NotAPlugin(), Plugin)

    print()

    # --- Section 11: __abstractmethods__ introspection ---
    print("--- Section 11: __abstractmethods__ Introspection ---")

    print(f"  Shape.__abstractmethods__ = {Shape.__abstractmethods__}")
    assert "area" in Shape.__abstractmethods__
    assert "perimeter" in Shape.__abstractmethods__

    print(f"  Circle.__abstractmethods__ = {Circle.__abstractmethods__}")
    assert len(Circle.__abstractmethods__) == 0

    print(f"  Animal.__abstractmethods__ = {Animal.__abstractmethods__}")
    assert "sound" in Animal.__abstractmethods__
    assert "legs" in Animal.__abstractmethods__

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Abstract Base Classes in Python:")
    print("  - abc.ABC: base class for defining abstract interfaces")
    print("  - @abstractmethod: marks required methods (enforced at instantiation)")
    print("  - Abstract properties: @property + @abstractmethod")
    print("  - register(): declare virtual subclasses without inheritance")
    print("  - __subclasshook__: custom isinstance()/issubclass() logic")
    print("  - ABCs = nominal typing (must inherit), Protocols = structural (must have methods)")
    print("  - collections.abc: standard ABCs for containers (Iterable, Sequence, Mapping, etc.)")
    print("  - TypedCollection: custom ABC with type safety enforcement")
    print()
    print("All 11 sections passed. You've mastered abstract base classes!")
