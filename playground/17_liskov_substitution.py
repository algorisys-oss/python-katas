"""
Kata 17 -- Liskov Substitution Principle
Run: python playground/17_liskov_substitution.py

Explore the Liskov Substitution Principle through the classic Rectangle/Square
and Bird/Penguin violations, then build LSP-compliant hierarchies with proper
behavioral subtyping, preconditions, postconditions, and contract enforcement.
"""

from abc import ABC, abstractmethod


# ===========================================================================
# VIOLATION 1: RECTANGLE / SQUARE
# ===========================================================================

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
    """A square that VIOLATES LSP -- setting width also changes height."""

    def __init__(self, side: float):
        super().__init__(side, side)

    @Rectangle.width.setter
    def width(self, value: float):
        self._width = value
        self._height = value  # Couples width and height

    @Rectangle.height.setter
    def height(self, value: float):
        self._width = value  # Couples width and height
        self._height = value


def resize_rectangle(rect: Rectangle) -> float:
    """Client code that assumes width and height are independent."""
    rect.width = 5
    rect.height = 10
    return rect.area()


# ===========================================================================
# FIX 1: SHAPE HIERARCHY (Rectangle and Square as siblings)
# ===========================================================================

class Shape(ABC):
    """Abstract shape -- the common behavioral contract."""

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
    """A square -- NOT a subclass of Rectangle. Sibling under Shape."""

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


# ===========================================================================
# VIOLATION 2: BIRD / PENGUIN
# ===========================================================================

class Bird:
    """A bird that can fly -- but not ALL birds can fly."""

    def __init__(self, name: str):
        self.name = name

    def fly(self, distance: float) -> str:
        return f"{self.name} flew {distance}m"


class Penguin(Bird):
    """Penguins can't fly -- violates LSP by raising on fly()."""

    def fly(self, distance: float) -> str:
        raise NotImplementedError("Penguins can't fly!")


# ===========================================================================
# FIX 2: BIRD HIERARCHY (separate flying from non-flying)
# ===========================================================================

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
    """Birds that walk/swim instead of flying."""

    def move(self, distance: float) -> str:
        return f"{self.name} walked {distance}m"


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


# ===========================================================================
# PRECONDITIONS AND POSTCONDITIONS
# ===========================================================================

class PaymentProcessor:
    """Processes payments with clear pre/postconditions."""

    def process(self, amount: float) -> dict:
        """
        Precondition: amount > 0
        Postcondition: returns dict with "status" and "amount" keys
        """
        assert amount > 0, f"Precondition: amount must be positive, got {amount}"
        result = {"status": "success", "amount": amount}
        return result


class CreditCardProcessor(PaymentProcessor):
    """LSP-compliant: same preconditions, honors postconditions."""

    def __init__(self):
        self.fee_rate = 0.03

    def process(self, amount: float) -> dict:
        assert amount > 0, f"Precondition: amount must be positive, got {amount}"
        total = amount + (amount * self.fee_rate)
        # Postcondition honored: has "status" and "amount"
        # Extra field "fee" is fine -- we ADD, not REMOVE
        return {"status": "success", "amount": total, "fee": amount * self.fee_rate}


class StrictProcessor(PaymentProcessor):
    """LSP VIOLATION: strengthens precondition (rejects small amounts)."""

    def process(self, amount: float) -> dict:
        # BAD: parent accepts any positive amount, this rejects < 10
        assert amount >= 10, f"Minimum payment is $10, got {amount}"
        return {"status": "success", "amount": amount}


# ===========================================================================
# CONTRACT ENFORCEMENT
# ===========================================================================

def verify_lsp_shape(shape: Shape) -> bool:
    """Verify any Shape subtype honors the contract."""
    # area() must return a non-negative number
    a = shape.area()
    assert isinstance(a, (int, float)), f"area() must return a number, got {type(a)}"
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


def verify_lsp_processor(processor: PaymentProcessor, amount: float) -> bool:
    """Verify any PaymentProcessor subtype honors the contract."""
    result = processor.process(amount)
    assert isinstance(result, dict), f"process() must return dict, got {type(result)}"
    assert "status" in result, "process() result must have 'status' key"
    assert "amount" in result, "process() result must have 'amount' key"
    return True


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The Rectangle/Square Violation ---
    print("--- Section 1: The Rectangle/Square Violation ---")

    # Rectangle works fine
    r = Rectangle(2, 3)
    result = resize_rectangle(r)
    assert result == 50
    print(f"  Rectangle(5x10) area: {result} -- correct!")

    # Square breaks the contract
    s = Square(7)
    result = resize_rectangle(s)
    print(f"  Square after resize: width={s.width}, height={s.height}, area={result}")
    assert result != 50, "Square should have broken the contract"
    assert result == 100, "Square couples width and height"
    print(f"  Expected area 50 but got {result} -- LSP VIOLATED!")
    print("  The Square broke client code that assumed independent width/height.")

    print()

    # --- Section 2: The Fix -- Shape Hierarchy ---
    print("--- Section 2: The Fix -- Shape Hierarchy ---")

    rect = RectangleFixed(5, 10)
    sq = SquareFixed(7)

    print(f"  RectangleFixed: {rect.describe()} area={rect.area()}")
    print(f"  SquareFixed: {sq.describe()} area={sq.area()}")

    assert rect.area() == 50
    assert sq.area() == 49

    # Both satisfy the Shape contract
    shapes: list[Shape] = [
        RectangleFixed(3, 4),
        SquareFixed(5),
        RectangleFixed(10, 1),
        SquareFixed(1),
    ]
    for shape in shapes:
        assert verify_lsp_shape(shape)
    print("  All shapes pass the LSP contract test!")

    # Verify they are NOT in a parent-child relationship
    assert not issubclass(SquareFixed, RectangleFixed)
    assert not issubclass(RectangleFixed, SquareFixed)
    assert issubclass(SquareFixed, Shape)
    assert issubclass(RectangleFixed, Shape)
    print("  Shape hierarchy is LSP-compliant.")

    print()

    # --- Section 3: The Bird/Penguin Violation ---
    print("--- Section 3: The Bird/Penguin Violation ---")

    eagle_bad = Bird("Eagle")
    penguin_bad = Penguin("Penguin")

    print(f"  {eagle_bad.fly(100)} -- works fine")

    try:
        penguin_bad.fly(100)
        print("  This should not print!")
    except NotImplementedError as e:
        print(f"  Penguin.fly() raised NotImplementedError -- LSP VIOLATED!")
    print("  Client code can't safely call fly() on all Birds.")

    print()

    # --- Section 4: The Fix -- BirdBase Hierarchy ---
    print("--- Section 4: The Fix -- BirdBase Hierarchy ---")

    birds: list[BirdBase] = [Eagle(), Sparrow(), PenguinFixed(), Ostrich()]

    for bird in birds:
        result = bird.move(100)
        print(f"  {bird.name}: {result}")

    # All pass the contract test
    for bird in birds:
        assert verify_lsp_bird(bird)
    print("  All birds pass the LSP contract test!")

    # Verify hierarchy structure
    assert issubclass(Eagle, FlyingBird)
    assert issubclass(Sparrow, FlyingBird)
    assert issubclass(PenguinFixed, FlightlessBird)
    assert issubclass(Ostrich, FlightlessBird)
    assert issubclass(FlyingBird, BirdBase)
    assert issubclass(FlightlessBird, BirdBase)
    print("  Bird hierarchy is LSP-compliant.")

    print()

    # --- Section 5: Preconditions and Postconditions ---
    print("--- Section 5: Preconditions and Postconditions ---")

    base_proc = PaymentProcessor()
    cc_proc = CreditCardProcessor()
    strict_proc = StrictProcessor()

    # Base processor works
    result = base_proc.process(100)
    print(f"  PaymentProcessor.process(100): {result}")
    assert result["status"] == "success"
    assert result["amount"] == 100

    # CreditCardProcessor is LSP-compliant (same preconditions, extra postcondition data)
    result = cc_proc.process(100)
    print(f"  CreditCardProcessor.process(100): {result}")
    assert result["status"] == "success"
    assert result["amount"] == 103.0
    assert result["fee"] == 3.0
    print("  CreditCardProcessor is LSP-compliant -- same preconditions, honors postconditions.")

    # StrictProcessor violates LSP (strengthened precondition)
    try:
        strict_proc.process(5)  # Parent accepts 5, strict rejects it
        print("  This should not print!")
    except AssertionError:
        print("  StrictProcessor.process(5) raised AssertionError -- LSP VIOLATED!")
    print("  StrictProcessor strengthened the precondition (rejects amounts < 10).")

    print()

    # --- Section 6: Contract Enforcement ---
    print("--- Section 6: Contract Enforcement ---")

    # Test all shapes
    test_shapes: list[Shape] = [
        RectangleFixed(3, 4),
        SquareFixed(5),
        RectangleFixed(10, 1),
        SquareFixed(1),
    ]
    for shape in test_shapes:
        verify_lsp_shape(shape)
        print(f"  {shape.describe()}: area={shape.area()}, describe='{shape.describe()}' -- LSP OK")

    # Test all birds
    test_birds: list[BirdBase] = [Eagle(), Sparrow(), PenguinFixed(), Ostrich()]
    for bird in test_birds:
        verify_lsp_bird(bird)
        print(f"  {bird.name}: move='{bird.move(100)}', sound='{bird.sound()}' -- LSP OK")

    # Test compliant processors
    for proc in [PaymentProcessor(), CreditCardProcessor()]:
        verify_lsp_processor(proc, 50)

    print("  All contract tests passed!")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Liskov Substitution Principle:")
    print("  - Subtypes must be substitutable for their base types")
    print("  - Rectangle/Square: don't inherit if behavioral contracts differ")
    print("  - Bird/Penguin: separate capabilities into proper hierarchies")
    print("  - Preconditions: subtypes must not strengthen them")
    print("  - Postconditions: subtypes must not weaken them")
    print("  - Invariants: subtypes must preserve them")
    print("  - Write contract tests against the base type to catch violations")
    print()
    print("All 6 sections passed. You've mastered the Liskov Substitution Principle!")
