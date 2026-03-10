"""
Kata 07 -- Dataclasses & Attrs
Run: python playground/07_dataclasses_attrs.py

Master Python dataclasses: @dataclass, field(), __post_init__, frozen,
slots, order, kw_only, asdict/astuple/replace, inheritance, and
comparison with namedtuple.
"""

from dataclasses import (
    dataclass,
    field,
    asdict,
    astuple,
    replace,
    make_dataclass,
    fields,
)
import json
import sys


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Basic @dataclass ---
    print("--- Section 1: Basic @dataclass ---")

    @dataclass
    class Point:
        x: float
        y: float

    p1 = Point(3.0, 4.0)
    p2 = Point(3.0, 4.0)
    p3 = Point(1.0, 2.0)

    print(f"p1 = {p1}")
    # Output: p1 = Point(x=3.0, y=4.0)
    assert repr(p1) == "Point(x=3.0, y=4.0)"

    print(f"p1 == p2: {p1 == p2}")
    # Output: p1 == p2: True
    assert p1 == p2

    print(f"p1 == p3: {p1 == p3}")
    # Output: p1 == p3: False
    assert p1 != p3

    print()

    # --- Section 2: field() ---
    print("--- Section 2: field() -- defaults, factories, repr, compare ---")

    @dataclass
    class Player:
        name: str
        score: int = 0
        tags: list[str] = field(default_factory=list)
        _internal_id: str = field(default="", repr=False)
        timestamp: float = field(default=0.0, compare=False)
        email: str = field(default="", metadata={"max_length": 255})

    p = Player("Alice", 100, ["veteran", "admin"], "abc123", 1234567890.0, "alice@example.com")
    print(f"Player: {p}")
    # _internal_id is hidden from repr
    assert "_internal_id" not in repr(p)
    assert "abc123" not in repr(p)

    # compare=False means timestamp is ignored in equality
    p2 = Player("Alice", 100, ["veteran", "admin"], "abc123", 9999999999.0, "alice@example.com")
    print(f"Same player, different timestamp: p == p2 = {p == p2}")
    assert p == p2  # timestamp differs but compare=False

    # Metadata is accessible via fields()
    email_field = [f for f in fields(Player) if f.name == "email"][0]
    print(f"Email metadata: {email_field.metadata}")
    # Output: Email metadata: {'max_length': 255}
    assert email_field.metadata["max_length"] == 255

    # default_factory ensures each instance gets its own list
    p3 = Player("Bob")
    p4 = Player("Carol")
    p3.tags.append("new")
    print(f"Bob's tags: {p3.tags}, Carol's tags: {p4.tags}")
    # Output: Bob's tags: ['new'], Carol's tags: []
    assert p3.tags == ["new"]
    assert p4.tags == []  # NOT shared!

    print()

    # --- Section 3: __post_init__ ---
    print("--- Section 3: __post_init__ -- validation & computed fields ---")

    @dataclass
    class Temperature:
        celsius: float
        fahrenheit: float = field(init=False)
        kelvin: float = field(init=False)

        def __post_init__(self):
            if self.celsius < -273.15:
                raise ValueError(f"Temperature {self.celsius}C is below absolute zero")
            self.fahrenheit = self.celsius * 9 / 5 + 32
            self.kelvin = self.celsius + 273.15

    t = Temperature(100)
    print(f"100C = {t}")
    # Output: 100C = Temperature(celsius=100, fahrenheit=212.0, kelvin=373.15)
    assert t.fahrenheit == 212.0
    assert t.kelvin == 373.15

    t2 = Temperature(0)
    print(f"0C = {t2.fahrenheit}F = {t2.kelvin}K")
    # Output: 0C = 32.0F = 273.15K
    assert t2.fahrenheit == 32.0
    assert t2.kelvin == 273.15

    try:
        Temperature(-300)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Caught: {e}")
        # Output: Caught: Temperature -300C is below absolute zero

    print()

    # --- Section 4: frozen=True ---
    print("--- Section 4: frozen=True -- immutable dataclasses ---")

    @dataclass(frozen=True)
    class Color:
        r: int
        g: int
        b: int

    red = Color(255, 0, 0)
    blue = Color(0, 0, 255)
    print(f"red = {red}")
    # Output: red = Color(r=255, g=0, b=0)

    # Immutable
    try:
        red.r = 128
        assert False, "Should have raised"
    except AttributeError as e:
        print(f"Caught: {e}")
        # Output: Caught: cannot assign to field 'r'

    # Hashable -- usable as dict keys and in sets
    palette = {red: "red", blue: "blue"}
    print(f"palette[Color(255, 0, 0)] = {palette[Color(255, 0, 0)]}")
    # Output: palette[Color(255, 0, 0)] = red
    assert palette[Color(255, 0, 0)] == "red"

    color_set = {red, blue, Color(255, 0, 0)}
    print(f"color_set size: {len(color_set)}")
    # Output: color_set size: 2
    assert len(color_set) == 2

    print()

    # --- Section 5: slots=True ---
    print("--- Section 5: slots=True -- memory optimization ---")

    @dataclass
    class RegularPoint:
        x: float
        y: float

    @dataclass(slots=True)
    class SlottedPoint:
        x: float
        y: float

    r = RegularPoint(1.0, 2.0)
    s = SlottedPoint(1.0, 2.0)

    print(f"Regular has __dict__: {hasattr(r, '__dict__')}")
    # Output: Regular has __dict__: True
    assert hasattr(r, "__dict__")

    print(f"Slotted has __dict__: {hasattr(s, '__dict__')}")
    # Output: Slotted has __dict__: False
    assert not hasattr(s, "__dict__")

    # Slotted classes prevent adding arbitrary attributes
    try:
        s.z = 3.0
        assert False, "Should have raised"
    except AttributeError as e:
        print(f"Caught: {e}")
        # Output: Caught: 'SlottedPoint' object has no attribute 'z'

    # Regular classes allow it
    r.z = 3.0
    print(f"Regular point with z: x={r.x}, y={r.y}, z={r.z}")
    assert r.z == 3.0

    print()

    # --- Section 6: order=True ---
    print("--- Section 6: order=True -- comparison methods ---")

    @dataclass(order=True)
    class Version:
        major: int
        minor: int
        patch: int

    versions = [
        Version(2, 1, 0),
        Version(1, 9, 5),
        Version(2, 0, 1),
        Version(1, 0, 0),
    ]

    sorted_versions = sorted(versions)
    for v in sorted_versions:
        print(f"  {v}")
    # Output:
    #   Version(major=1, minor=0, patch=0)
    #   Version(major=1, minor=9, patch=5)
    #   Version(major=2, minor=0, patch=1)
    #   Version(major=2, minor=1, patch=0)
    assert sorted_versions[0] == Version(1, 0, 0)
    assert sorted_versions[-1] == Version(2, 1, 0)

    print(f"Version(2,0,0) > Version(1,9,9): {Version(2,0,0) > Version(1,9,9)}")
    # Output: Version(2,0,0) > Version(1,9,9): True
    assert Version(2, 0, 0) > Version(1, 9, 9)

    print()

    # --- Section 7: kw_only=True ---
    print("--- Section 7: kw_only=True -- keyword-only fields ---")

    @dataclass(kw_only=True)
    class DatabaseConfig:
        host: str
        port: int
        database: str
        user: str
        password: str
        pool_size: int = 5
        timeout: float = 30.0

    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="myapp",
        user="admin",
        password="secret",
    )
    print(f"Config: {config}")
    assert config.host == "localhost"
    assert config.pool_size == 5

    # Positional args raise TypeError
    try:
        DatabaseConfig("localhost", 5432, "myapp", "admin", "secret")
        assert False, "Should have raised TypeError"
    except TypeError as e:
        print(f"Caught: {e}")
        # Output: Caught: DatabaseConfig.__init__() takes 1 positional argument but 6 were given

    print()

    # --- Section 8: asdict, astuple, replace ---
    print("--- Section 8: asdict, astuple, replace ---")

    @dataclass
    class Address:
        street: str
        city: str
        state: str
        zip_code: str

    @dataclass
    class Person:
        name: str
        age: int
        address: Address

    addr = Address("123 Main St", "Springfield", "IL", "62701")
    person = Person("Alice", 30, addr)

    # asdict: deep conversion
    d = asdict(person)
    print(f"asdict: {d}")
    assert d == {
        "name": "Alice",
        "age": 30,
        "address": {
            "street": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
        },
    }

    # JSON serialization
    json_str = json.dumps(d, indent=2)
    print(f"JSON:\n{json_str}")
    assert '"name": "Alice"' in json_str

    # astuple: deep conversion
    t = astuple(person)
    print(f"astuple: {t}")
    assert t == ("Alice", 30, ("123 Main St", "Springfield", "IL", "62701"))

    # replace: create modified copy
    person2 = replace(person, age=31)
    print(f"Original age: {person.age}, replaced age: {person2.age}")
    assert person.age == 30  # unchanged
    assert person2.age == 31

    # replace with frozen dataclass
    @dataclass(frozen=True)
    class Money:
        amount: int
        currency: str = "USD"

    price = Money(100)
    discounted = replace(price, amount=80)
    print(f"Price: {price} -> Discounted: {discounted}")
    assert price.amount == 100
    assert discounted.amount == 80
    assert discounted.currency == "USD"

    print()

    # --- Section 9: Inheritance ---
    print("--- Section 9: Inheritance ---")

    @dataclass
    class Animal:
        name: str
        species: str

    @dataclass
    class Pet(Animal):
        owner: str
        vaccinated: bool = True

    dog = Pet("Rex", "Dog", "Alice")
    print(f"Pet: {dog}")
    assert dog.name == "Rex"
    assert dog.species == "Dog"
    assert dog.owner == "Alice"
    assert dog.vaccinated is True

    # __post_init__ chain
    @dataclass
    class Base:
        value: int

        def __post_init__(self):
            if self.value < 0:
                raise ValueError("value must be non-negative")

    @dataclass
    class Derived(Base):
        label: str = "default"

        def __post_init__(self):
            super().__post_init__()
            self.label = self.label.upper()

    d = Derived(42, "hello")
    print(f"Derived: {d}")
    assert d.label == "HELLO"
    assert d.value == 42

    try:
        Derived(-1)
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Caught: {e}")
        assert "non-negative" in str(e)

    print()

    # --- Section 10: make_dataclass ---
    print("--- Section 10: make_dataclass -- dynamic creation ---")

    Coordinate = make_dataclass("Coordinate", ["x", "y", "z"])
    c = Coordinate(1.0, 2.0, 3.0)
    print(f"Coordinate: {c}")
    assert c.x == 1.0
    assert c.y == 2.0
    assert c.z == 3.0

    Config = make_dataclass(
        "Config",
        [
            ("host", str),
            ("port", int, field(default=8080)),
            ("debug", bool, field(default=False)),
        ],
    )
    cfg = Config(host="localhost")
    print(f"Config: {cfg}")
    assert cfg.host == "localhost"
    assert cfg.port == 8080
    assert cfg.debug is False

    print()

    # --- Section 11: Comparison -- dataclass vs namedtuple ---
    print("--- Section 11: dataclass vs namedtuple ---")

    from collections import namedtuple

    PointNT = namedtuple("PointNT", ["x", "y"])
    pnt = PointNT(3.0, 4.0)

    @dataclass
    class PointDC:
        x: float
        y: float

    pdc = PointDC(3.0, 4.0)

    # Both have auto __repr__
    print(f"namedtuple: {pnt}")
    print(f"dataclass:  {pdc}")

    # namedtuple supports tuple unpacking
    x, y = pnt
    print(f"Unpacked namedtuple: x={x}, y={y}")
    assert x == 3.0

    # namedtuple is immutable
    try:
        pnt.x = 5.0
        assert False, "Should have raised"
    except AttributeError:
        print("namedtuple is immutable (AttributeError on assignment)")

    # namedtuple is hashable
    point_set = {pnt, PointNT(3.0, 4.0)}
    print(f"namedtuple set size: {len(point_set)}")
    assert len(point_set) == 1

    # dataclass is mutable by default
    pdc.x = 5.0
    print(f"Mutated dataclass: {pdc}")
    assert pdc.x == 5.0

    # namedtuple compares equal to plain tuples (sometimes a gotcha)
    print(f"PointNT(3.0, 4.0) == (3.0, 4.0): {PointNT(3.0, 4.0) == (3.0, 4.0)}")
    assert PointNT(3.0, 4.0) == (3.0, 4.0)  # this can be surprising!

    print()

    # --- Section 12: Exercise -- Config with validation ---
    print("--- Section 12: Exercise -- Config with Validation ---")

    @dataclass
    class AppConfig:
        host: str
        port: int
        debug: bool = False
        tags: list[str] = field(default_factory=list)

        def __post_init__(self):
            if not self.host:
                raise ValueError("host must not be empty")
            if not (1 <= self.port <= 65535):
                raise ValueError(f"port must be 1-65535, got {self.port}")

    c = AppConfig("localhost", 8080, tags=["web", "api"])
    print(f"Config: {c}")
    assert c.host == "localhost"
    assert c.port == 8080
    assert c.tags == ["web", "api"]

    try:
        AppConfig("", 8080)
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Caught empty host: {e}")
        assert "host" in str(e)

    try:
        AppConfig("localhost", 99999)
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Caught invalid port: {e}")
        assert "port" in str(e)

    try:
        AppConfig("localhost", 0)
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Caught zero port: {e}")
        assert "port" in str(e)

    print()

    # --- Section 13: Exercise -- Frozen Money class ---
    print("--- Section 13: Exercise -- Frozen Money Class ---")

    @dataclass(frozen=True, order=True)
    class CurrencyAmount:
        amount: int  # in cents
        currency: str = "USD"

        @property
        def dollars(self) -> str:
            return f"${self.amount / 100:.2f}"

        def __add__(self, other):
            if not isinstance(other, CurrencyAmount):
                return NotImplemented
            if self.currency != other.currency:
                raise ValueError(f"Cannot add {self.currency} and {other.currency}")
            return replace(self, amount=self.amount + other.amount)

    price = CurrencyAmount(1999)
    tax = CurrencyAmount(160)
    total = price + tax
    print(f"{price.dollars} + {tax.dollars} = {total.dollars}")
    # Output: $19.99 + $1.60 = $21.59
    assert total.amount == 2159
    assert total.dollars == "$21.59"

    # Frozen: immutable
    try:
        price.amount = 0
        assert False, "Should have raised"
    except AttributeError:
        print("CurrencyAmount is frozen (immutable)")

    # Hashable: can use in sets
    money_set = {price, tax, CurrencyAmount(1999)}
    print(f"Money set size: {len(money_set)}")
    assert len(money_set) == 2

    # Ordered: can compare
    print(f"$19.99 > $1.60: {price > tax}")
    assert price > tax

    # replace for "mutation"
    eur = replace(price, currency="EUR")
    print(f"EUR version: {eur}")
    assert eur.amount == 1999
    assert eur.currency == "EUR"

    # Can't add different currencies
    try:
        price + eur
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Caught: {e}")
        assert "Cannot add" in str(e)

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Dataclasses in Python:")
    print("  - @dataclass for auto __init__, __repr__, __eq__")
    print("  - field() for default factories, repr/compare control, metadata")
    print("  - __post_init__ for validation and computed fields")
    print("  - frozen=True for immutable, hashable instances")
    print("  - slots=True for memory efficiency (3.10+)")
    print("  - order=True for sortable data")
    print("  - kw_only=True for keyword-only constructors (3.10+)")
    print("  - asdict/astuple for serialization, replace for immutable updates")
    print("  - Inheritance with __post_init__ chaining")
    print("  - make_dataclass for dynamic class creation")
    print()
    print("All 13 sections passed. You've mastered dataclasses!")
