"""
Kata 17 -- Liskov Substitution Principle
Run: python playground/skeletons/17_liskov_substitution.py

Explore the Liskov Substitution Principle through the classic Rectangle/Square
and Bird/Penguin violations, then build LSP-compliant hierarchies with proper
behavioral subtyping, preconditions, postconditions, and contract enforcement.
"""

from abc import ABC, abstractmethod


# ===========================================================================
# VIOLATION 1: RECTANGLE / SQUARE (provided for reference)
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
# FIX 1: YOUR SHAPE HIERARCHY (Rectangle and Square as siblings)
# ===========================================================================

class Shape(ABC):
    """Abstract shape -- the common behavioral contract.

    Should have:
    - area() -> float: return the area
    - describe() -> str: return a human-readable description
    """

    @abstractmethod
    def area(self) -> float:
        """Return the area of this shape."""
        ...

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable description."""
        ...


class RectangleFixed(Shape):
    """A rectangle with independent width and height.

    Should have:
    - width and height properties (with setters)
    - area() returning width * height
    - describe() returning 'Rectangle(WxH)'
    """

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
        # TODO: return width * height
        pass

    def describe(self) -> str:
        # TODO: return f"Rectangle({width}x{height})"
        pass


class SquareFixed(Shape):
    """A square -- NOT a subclass of Rectangle. Sibling under Shape.

    Should have:
    - side property (with setter)
    - area() returning side ** 2
    - describe() returning 'Square(S)'
    """

    def __init__(self, side: float):
        self._side = side

    @property
    def side(self) -> float:
        return self._side

    @side.setter
    def side(self, value: float):
        self._side = value

    def area(self) -> float:
        # TODO: return side squared
        pass

    def describe(self) -> str:
        # TODO: return f"Square({side})"
        pass


# ===========================================================================
# VIOLATION 2: BIRD / PENGUIN (provided for reference)
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
# FIX 2: YOUR BIRD HIERARCHY (separate flying from non-flying)
# ===========================================================================

class BirdBase(ABC):
    """All birds can move and make sounds, but not all fly.

    Should have:
    - name: str and speed: float attributes
    - move(distance) -> str: abstract -- all birds move somehow
    - sound() -> str: abstract -- all birds make sounds
    - describe() -> str: return name and speed
    """

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
    """Birds that can fly.

    Should have:
    - altitude: float attribute
    - move() returning "{name} flew {distance}m at {altitude}m altitude"
    - fly() delegating to move()
    """

    def __init__(self, name: str, speed: float, altitude: float):
        super().__init__(name, speed)
        self.altitude = altitude

    def move(self, distance: float) -> str:
        # TODO: return f"{self.name} flew {distance}m at {self.altitude}m altitude"
        pass

    def fly(self, distance: float) -> str:
        # TODO: delegate to self.move()
        pass


class FlightlessBird(BirdBase):
    """Birds that walk/swim instead of flying.

    Should have:
    - move() returning "{name} walked {distance}m"
    """

    def move(self, distance: float) -> str:
        # TODO: return f"{self.name} walked {distance}m"
        pass


class Eagle(FlyingBird):
    """An eagle -- flying bird."""

    def __init__(self):
        # TODO: call super().__init__ with name="Eagle", speed=160.0, altitude=3000.0
        pass

    def sound(self) -> str:
        # TODO: return "Screech!"
        pass


class Sparrow(FlyingBird):
    """A sparrow -- flying bird."""

    def __init__(self):
        # TODO: call super().__init__ with name="Sparrow", speed=45.0, altitude=100.0
        pass

    def sound(self) -> str:
        # TODO: return "Chirp!"
        pass


class PenguinFixed(FlightlessBird):
    """A penguin -- flightless bird that waddles and swims."""

    def __init__(self):
        # TODO: call super().__init__ with name="Penguin", speed=8.0
        pass

    def move(self, distance: float) -> str:
        # TODO: return f"{self.name} waddled {distance}m"
        pass

    def sound(self) -> str:
        # TODO: return "Honk!"
        pass

    def swim(self, distance: float) -> str:
        # TODO: return f"{self.name} swam {distance}m"
        pass


class Ostrich(FlightlessBird):
    """An ostrich -- flightless bird."""

    def __init__(self):
        # TODO: call super().__init__ with name="Ostrich", speed=70.0
        pass

    def sound(self) -> str:
        # TODO: return "Boom!"
        pass


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
    """LSP-compliant: same preconditions, honors postconditions.

    Should:
    - Keep the same precondition (amount > 0)
    - Return dict with "status", "amount", AND "fee" keys
    - Add a 3% fee to the amount
    """

    def __init__(self):
        self.fee_rate = 0.03

    def process(self, amount: float) -> dict:
        # TODO: implement LSP-compliant processor
        # 1. Assert amount > 0 (same precondition as parent)
        # 2. Calculate total = amount + (amount * self.fee_rate)
        # 3. Return dict with "status", "amount" (total), and "fee"
        # HINT: extra fields in the return dict are fine -- adding is OK
        pass


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
    # TODO: verify that area() returns a non-negative float
    # TODO: verify that describe() returns a non-empty string
    # HINT: use isinstance() and assert
    pass


def verify_lsp_bird(bird: BirdBase) -> bool:
    """Verify any BirdBase subtype honors the contract."""
    # TODO: verify that move(100) returns a string
    # TODO: verify that sound() returns a string
    # TODO: verify that describe() returns a string
    pass


def verify_lsp_processor(processor: PaymentProcessor, amount: float) -> bool:
    """Verify any PaymentProcessor subtype honors the contract."""
    # TODO: verify that process(amount) returns a dict with "status" and "amount" keys
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: The Rectangle/Square Violation ---
    print("--- Section 1: The Rectangle/Square Violation ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: The Fix -- Shape Hierarchy ---
    print("--- Section 2: The Fix -- Shape Hierarchy ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: The Bird/Penguin Violation ---
    print("--- Section 3: The Bird/Penguin Violation ---")

    try:
        eagle_bad = Bird("Eagle")
        penguin_bad = Penguin("Penguin")

        print(f"  {eagle_bad.fly(100)} -- works fine")

        try:
            penguin_bad.fly(100)
            print("  This should not print!")
        except NotImplementedError as e:
            print(f"  Penguin.fly() raised NotImplementedError -- LSP VIOLATED!")
        print("  Client code can't safely call fly() on all Birds.")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: The Fix -- BirdBase Hierarchy ---
    print("--- Section 4: The Fix -- BirdBase Hierarchy ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Preconditions and Postconditions ---
    print("--- Section 5: Preconditions and Postconditions ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Contract Enforcement ---
    print("--- Section 6: Contract Enforcement ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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
