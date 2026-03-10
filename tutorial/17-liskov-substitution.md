# Kata 17 -- Liskov Substitution Principle

[prev: 16-open-closed](./16-open-closed.md) | [next: 18-interface-segregation](./18-interface-segregation.md)

---

## What We're Building

The **Liskov Substitution Principle** (LSP) is the third SOLID principle. Barbara Liskov stated it in 1987: *if S is a subtype of T, then objects of type T may be replaced with objects of type S without altering any of the desirable properties of the program*. In plain terms: **subclasses must be usable wherever their parent class is expected, without surprises**.

This sounds obvious until you hit the classic violations. A `Square` that inherits from `Rectangle` breaks client code that assumes width and height are independent. A `Penguin` that inherits from `Bird` blows up when you call `fly()`. These aren't just academic puzzles -- they're real bugs that surface when you model "is-a" relationships based on real-world taxonomy instead of behavioral contracts.

In this kata we'll break LSP, understand *why* it breaks, and then build hierarchies that respect behavioral subtyping.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Liskov Substitution Principle | Subtypes must honor the parent's behavioral contract | Designing any inheritance hierarchy |
| Behavioral subtyping | Subtype must satisfy same preconditions, postconditions, invariants | Validating that substitution is safe |
| Preconditions | What must be true *before* a method is called | Subtypes must not strengthen preconditions |
| Postconditions | What must be true *after* a method returns | Subtypes must not weaken postconditions |
| Invariants | What must always be true about an object's state | Subtypes must preserve parent invariants |
| Covariance / contravariance | How types change in subtype method signatures | Return types (covariant) vs. parameter types (contravariant) |
| Contract enforcement | Using assertions to verify behavioral contracts | Testing LSP compliance programmatically |

## The Code

### Step 1: The classic Rectangle/Square violation

This is the most famous LSP violation in software engineering. Mathematically, a square *is* a rectangle. But in code, that "is-a" relationship breaks substitutability:

```python
class Rectangle:
    """A rectangle with independent width and height."""

    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float):
        self._width = value

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        self._height = value

    def area(self) -> float:
        return self._width * self._height


class Square(Rectangle):
    """A square IS-A rectangle... right?"""

    def __init__(self, side: float):
        super().__init__(side, side)

    @Rectangle.width.setter
    def width(self, value: float):
        # Must keep width == height for a square
        self._width = value
        self._height = value

    @Rectangle.height.setter
    def height(self, value: float):
        # Must keep width == height for a square
        self._width = value
        self._height = value
```

Now watch it break:

```python
def resize_rectangle(rect: Rectangle):
    """Client code that assumes width and height are independent."""
    rect.width = 5
    rect.height = 10
    assert rect.area() == 50  # 5 * 10 = 50... right?

r = Rectangle(2, 3)
resize_rectangle(r)  # Works fine

s = Square(7)
resize_rectangle(s)  # BOOM! area() returns 100, not 50
```

The `Square` violates LSP because it **strengthens the postcondition** of the width setter: setting width also changes height. Client code that depends on the Rectangle contract (setting width doesn't affect height) breaks silently.

### Step 2: Why the violation matters

The problem isn't that `Square` is buggy in isolation. `Square` works perfectly when you use it as a square. The problem is **substitutability**: any function that accepts a `Rectangle` must work correctly with a `Square`, and it doesn't.

LSP violations are insidious because:
- They pass type checks (a `Square` IS a `Rectangle` to the type checker)
- They often pass unit tests of the subclass itself
- They break in *client code* that uses the parent type
- They surface at runtime, not at definition time

### Step 3: Fixing Rectangle/Square with composition

The fix is to stop pretending a square "is-a" rectangle in the behavioral sense. Instead, model what they *share* -- they're both shapes with an area:

```python
from abc import ABC, abstractmethod


class Shape(ABC):
    """Abstract shape -- the common contract."""

    @abstractmethod
    def area(self) -> float:
        """Return the area of this shape."""
        ...

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable description."""
        ...


class RectangleFixed(Shape):
    """A rectangle with independent width and height."""

    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float):
        self._width = value

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        self._height = value

    def area(self) -> float:
        return self._width * self._height

    def describe(self) -> str:
        return f"Rectangle({self._width}x{self._height})"


class SquareFixed(Shape):
    """A square -- NOT a subclass of Rectangle."""

    def __init__(self, side: float):
        self._side = side

    @property
    def side(self) -> float:
        return self._side

    @side.setter
    def side(self, value: float):
        self._side = value

    def area(self) -> float:
        return self._side ** 2

    def describe(self) -> str:
        return f"Square({self._side})"
```

Now both `RectangleFixed` and `SquareFixed` implement `Shape`. Any function that works with `Shape` can safely use either one, because the contract (`area()` returns a float, `describe()` returns a string) is honored by both.

### Step 4: The Bird/Penguin problem

Here's another classic: not all birds fly. Modeling `fly()` on a base `Bird` class violates LSP for penguins, ostriches, and kiwis:

```python
class Bird:
    """A bird that can fly."""

    def __init__(self, name: str):
        self.name = name

    def fly(self, distance: float) -> str:
        return f"{self.name} flew {distance}m"


class Penguin(Bird):
    """Penguins can't fly. What do we do?"""

    def fly(self, distance: float) -> str:
        raise NotImplementedError("Penguins can't fly!")
```

This violates LSP because client code calling `bird.fly(100)` expects a string back, not an exception. The subtype *weakens the postcondition* (sometimes returns a string, sometimes raises).

### Step 5: Fixing Bird/Penguin with proper abstractions

The fix is to separate "can move" from "can fly". Birds share movement, but flying is a specific capability:

```python
from abc import ABC, abstractmethod


class BirdBase(ABC):
    """All birds can move and make sounds, but not all fly."""

    def __init__(self, name: str, speed: float):
        self.name = name
        self.speed = speed

    @abstractmethod
    def move(self, distance: float) -> str:
        """All birds can move somehow."""
        ...

    @abstractmethod
    def sound(self) -> str:
        """All birds make sounds."""
        ...

    def describe(self) -> str:
        return f"{self.name} (speed: {self.speed} km/h)"


class FlyingBird(BirdBase):
    """Birds that can fly."""

    def __init__(self, name: str, speed: float, altitude: float):
        super().__init__(name, speed)
        self.altitude = altitude

    def move(self, distance: float) -> str:
        return f"{self.name} flew {distance}m at {self.altitude}m altitude"

    def fly(self, distance: float) -> str:
        return self.move(distance)


class FlightlessBird(BirdBase):
    """Birds that walk/swim instead of fly."""

    def move(self, distance: float) -> str:
        return f"{self.name} walked {distance}m"
```

Now concrete birds inherit from the right base:

```python
class Eagle(FlyingBird):
    def __init__(self):
        super().__init__("Eagle", 160.0, 3000.0)

    def sound(self) -> str:
        return "Screech!"


class Sparrow(FlyingBird):
    def __init__(self):
        super().__init__("Sparrow", 45.0, 100.0)

    def sound(self) -> str:
        return "Chirp!"


class PenguinFixed(FlightlessBird):
    def __init__(self):
        super().__init__("Penguin", 8.0)

    def move(self, distance: float) -> str:
        return f"{self.name} waddled {distance}m"

    def sound(self) -> str:
        return "Honk!"

    def swim(self, distance: float) -> str:
        return f"{self.name} swam {distance}m"


class Ostrich(FlightlessBird):
    def __init__(self):
        super().__init__("Ostrich", 70.0)

    def sound(self) -> str:
        return "Boom!"
```

Any function that accepts `BirdBase` can call `move()` and `sound()` on any bird safely. Only functions that specifically need flight accept `FlyingBird`.

### Step 6: Preconditions and postconditions

LSP has precise rules about how subtypes can relate to their parent's contract:

| Rule | Meaning | Example |
|---|---|---|
| **Preconditions cannot be strengthened** | Subtype must accept everything the parent accepts | If parent accepts negative numbers, subtype can't reject them |
| **Postconditions cannot be weakened** | Subtype must deliver at least what the parent promises | If parent guarantees non-negative return, subtype must too |
| **Invariants must be preserved** | Subtype must maintain all parent state constraints | If parent guarantees `balance >= 0`, subtype must too |

```python
class PaymentProcessor:
    """Processes payments with clear pre/postconditions."""

    def process(self, amount: float) -> dict:
        """
        Precondition: amount > 0
        Postcondition: returns {"status": "success"|"failed", "amount": float}
        """
        assert amount > 0, f"Precondition: amount must be positive, got {amount}"
        result = {"status": "success", "amount": amount}
        assert "status" in result and "amount" in result  # postcondition
        return result


class CreditCardProcessor(PaymentProcessor):
    """LSP-compliant: same preconditions, honors postconditions."""

    def __init__(self):
        self.fee_rate = 0.03

    def process(self, amount: float) -> dict:
        assert amount > 0, f"Precondition: amount must be positive, got {amount}"
        total = amount + (amount * self.fee_rate)
        result = {"status": "success", "amount": total, "fee": amount * self.fee_rate}
        # Postcondition honored: has "status" and "amount"
        # Extra fields (fee) are fine -- we can ADD, not REMOVE
        return result


class StrictProcessor(PaymentProcessor):
    """LSP VIOLATION: strengthens precondition (rejects small amounts)."""

    def process(self, amount: float) -> dict:
        # BAD: parent accepts any positive amount, this rejects < 10
        assert amount >= 10, "Minimum payment is $10"
        return {"status": "success", "amount": amount}
```

### Step 7: Contract enforcement with testing

You can write a generic test that verifies LSP compliance for any subtype:

```python
def verify_lsp_shape(shape: Shape) -> bool:
    """Verify any Shape subtype honors the contract."""
    # area() must return a non-negative float
    a = shape.area()
    assert isinstance(a, float), f"area() must return float, got {type(a)}"
    assert a >= 0, f"area() must be non-negative, got {a}"

    # describe() must return a non-empty string
    d = shape.describe()
    assert isinstance(d, str), f"describe() must return str, got {type(d)}"
    assert len(d) > 0, "describe() must return non-empty string"

    return True


def verify_lsp_bird(bird: BirdBase) -> bool:
    """Verify any BirdBase subtype honors the contract."""
    # move() must return a string
    result = bird.move(100)
    assert isinstance(result, str), f"move() must return str, got {type(result)}"

    # sound() must return a string
    s = bird.sound()
    assert isinstance(s, str), f"sound() must return str, got {type(s)}"

    # describe() must return a string
    d = bird.describe()
    assert isinstance(d, str), f"describe() must return str, got {type(d)}"

    return True
```

This is the power of LSP: you write one test against the base type, and it validates every subtype. If a new subtype passes this test, it's safe to use anywhere the base type is expected.

### Step 8: Covariance and contravariance

These terms describe how types can change in subtype method signatures:

- **Covariant return types**: a subtype's method can return a *more specific* type than the parent. If `Animal.speak()` returns `str`, then `Dog.speak()` can return `str` (same or more specific). This is safe because callers expecting `str` still get `str`.

- **Contravariant parameter types**: a subtype's method can *accept a broader* type than the parent. If `Processor.process(CreditCard)` accepts credit cards, a subtype could accept `PaymentMethod` (broader). This is safe because anything the caller passes (a `CreditCard`) is still accepted.

Python doesn't enforce these at the type level (duck typing), but violating them causes runtime failures:

```python
class AnimalShelter:
    """Shelter that accepts animals."""

    def accept(self, animal: object) -> str:
        return f"Accepted {animal}"


class DogShelter(AnimalShelter):
    """LSP VIOLATION: only accepts dogs (strengthened precondition)."""

    def accept(self, animal: object) -> str:
        if not hasattr(animal, "bark"):
            raise TypeError("Only dogs allowed!")
        return f"Accepted dog {animal}"
```

`DogShelter` violates LSP because it strengthens the precondition: the parent accepts any animal, but the subtype rejects non-dogs.

## Playground

Run the full LSP exploration with working and broken examples:

```bash
python playground/17_liskov_substitution.py
```

```
--- Section 1: The Rectangle/Square Violation ---
  Rectangle(5x10) area: 50.0 -- correct!
  Square after resize: width=10, height=10, area=100.0
  Expected area 50 but got 100.0 -- LSP VIOLATED!
  The Square broke client code that assumed independent width/height.

--- Section 2: The Fix -- Shape Hierarchy ---
  RectangleFixed: Rectangle(5x10) area=50.0
  SquareFixed: Square(7) area=49.0
  All shapes pass the LSP contract test!
  Shape hierarchy is LSP-compliant.

--- Section 3: The Bird/Penguin Violation ---
  Eagle flew 100m -- works fine
  Penguin.fly() raised NotImplementedError -- LSP VIOLATED!
  Client code can't safely call fly() on all Birds.

--- Section 4: The Fix -- BirdBase Hierarchy ---
  Eagle: Eagle flew 100.0m at 3000.0m altitude
  Sparrow: Sparrow flew 100.0m at 100.0m altitude
  Penguin: Penguin waddled 100.0m
  Ostrich: Ostrich walked 100.0m
  All birds pass the LSP contract test!
  Bird hierarchy is LSP-compliant.

--- Section 5: Preconditions and Postconditions ---
  PaymentProcessor.process(100): {'status': 'success', 'amount': 100}
  CreditCardProcessor.process(100): {'status': 'success', 'amount': 103.0, 'fee': 3.0}
  CreditCardProcessor is LSP-compliant -- same preconditions, honors postconditions.
  StrictProcessor.process(5) raised AssertionError -- LSP VIOLATED!
  StrictProcessor strengthened the precondition (rejects amounts < 10).

--- Section 6: Contract Enforcement ---
  Rectangle(3x4): area=12.0, describe='Rectangle(3x4)' -- LSP OK
  Square(5): area=25.0, describe='Square(5)' -- LSP OK
  Rectangle(10x1): area=10.0, describe='Rectangle(10x1)' -- LSP OK
  Square(1): area=1.0, describe='Square(1)' -- LSP OK
  Eagle: move='Eagle flew 100.0m at 3000.0m altitude', sound='Screech!' -- LSP OK
  Sparrow: move='Sparrow flew 100.0m at 100.0m altitude', sound='Chirp!' -- LSP OK
  Penguin: move='Penguin waddled 100.0m', sound='Honk!' -- LSP OK
  Ostrich: move='Ostrich walked 100.0m', sound='Boom!' -- LSP OK
  All contract tests passed!

--- Summary ---
Liskov Substitution Principle:
  - Subtypes must be substitutable for their base types
  - Rectangle/Square: don't inherit if behavioral contracts differ
  - Bird/Penguin: separate capabilities into proper hierarchies
  - Preconditions: subtypes must not strengthen them
  - Postconditions: subtypes must not weaken them
  - Invariants: subtypes must preserve them
  - Write contract tests against the base type to catch violations

All 6 sections passed. You've mastered the Liskov Substitution Principle!
```

## How It Works

```
LSP VIOLATION:                         LSP COMPLIANT:

  Rectangle                              Shape (ABC)
     ^                                   /         \
     |                             Rectangle     Square
   Square                         (independent   (single side,
   (couples width                  w & h,         own area())
    and height --                  own area())
    breaks contract!)

  Bird                                 BirdBase (ABC)
     ^                                /            \
     |                          FlyingBird     FlightlessBird
   Penguin                      /       \       /          \
   (raises on fly() --       Eagle   Sparrow  Penguin    Ostrich
    breaks contract!)

RULES:
  Parent's contract = {preconditions, postconditions, invariants}
  Subtype MUST NOT strengthen preconditions  (accept at least as much)
  Subtype MUST NOT weaken postconditions     (deliver at least as much)
  Subtype MUST preserve invariants           (maintain all guarantees)
```

The key insight: **inheritance should model behavioral compatibility, not real-world taxonomy**. A square *is* a rectangle in geometry, but a `Square` object is not a behavioral substitute for a `Rectangle` object. Design your hierarchies around what the code *does*, not what the real world *is*.

## Exercises

### Exercise 1: ReadOnlyFile violation

A `ReadOnlyFile` that extends `File` violates LSP if `File` has a `write()` method. Design a fix using proper abstractions:

```python
class Readable(ABC):
    @abstractmethod
    def read(self) -> str: ...

class Writable(ABC):
    @abstractmethod
    def write(self, data: str): ...

class ReadOnlyFile(Readable): ...
class ReadWriteFile(Readable, Writable): ...
```

### Exercise 2: Build a vehicle hierarchy

Design an LSP-compliant vehicle hierarchy where some vehicles are electric and some are gas-powered. Avoid the trap of putting `refuel()` on the base class:

```python
class Vehicle(ABC):
    """All vehicles can start, stop, and report range."""
    @abstractmethod
    def start(self) -> str: ...
    @abstractmethod
    def stop(self) -> str: ...
    @abstractmethod
    def remaining_range(self) -> float: ...

class ElectricVehicle(Vehicle):
    def charge(self, kwh: float) -> str: ...

class GasVehicle(Vehicle):
    def refuel(self, liters: float) -> str: ...
```

Write contract tests that verify any `Vehicle` subtype honors the base contract.

## What's Next

In [Kata 18 -- Interface Segregation Principle](./18-interface-segregation.md), we'll tackle the fourth SOLID principle: no client should be forced to depend on methods it does not use. You'll learn to split fat interfaces into focused ones using Python's `Protocol` and `ABC`, so that each consumer depends only on the slice of functionality it actually needs.

---

[prev: 16-open-closed](./16-open-closed.md) | [next: 18-interface-segregation](./18-interface-segregation.md)
