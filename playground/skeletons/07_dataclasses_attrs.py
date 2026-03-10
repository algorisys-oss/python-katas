"""
Kata 07 -- Dataclasses & Attrs
Run: python playground/skeletons/07_dataclasses_attrs.py

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
    try:
        # TODO: create a Point dataclass with x: float and y: float
        # HINT: use @dataclass decorator and annotate fields with types
        class Point:
            pass

        p1 = Point(3.0, 4.0)
        p2 = Point(3.0, 4.0)
        p3 = Point(1.0, 2.0)

        print(f"p1 = {p1}")
        assert repr(p1) == "Point(x=3.0, y=4.0)"

        print(f"p1 == p2: {p1 == p2}")
        assert p1 == p2

        print(f"p1 == p3: {p1 == p3}")
        assert p1 != p3
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: field() ---
    print("--- Section 2: field() -- defaults, factories, repr, compare ---")
    try:
        # TODO: create a Player dataclass with:
        #   name: str
        #   score: int = 0
        #   tags: list[str] -- default empty list (use field(default_factory=list))
        #   _internal_id: str -- default "", hidden from repr (use repr=False)
        #   timestamp: float -- default 0.0, excluded from equality (use compare=False)
        #   email: str -- default "", with metadata={"max_length": 255}
        # HINT: use field() for tags, _internal_id, timestamp, and email
        class Player:
            pass

        p = Player("Alice", 100, ["veteran", "admin"], "abc123", 1234567890.0, "alice@example.com")
        print(f"Player: {p}")
        assert "_internal_id" not in repr(p)
        assert "abc123" not in repr(p)

        p2 = Player("Alice", 100, ["veteran", "admin"], "abc123", 9999999999.0, "alice@example.com")
        print(f"Same player, different timestamp: p == p2 = {p == p2}")
        assert p == p2

        email_field = [f for f in fields(Player) if f.name == "email"][0]
        print(f"Email metadata: {email_field.metadata}")
        assert email_field.metadata["max_length"] == 255

        p3 = Player("Bob")
        p4 = Player("Carol")
        p3.tags.append("new")
        print(f"Bob's tags: {p3.tags}, Carol's tags: {p4.tags}")
        assert p3.tags == ["new"]
        assert p4.tags == []
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: __post_init__ ---
    print("--- Section 3: __post_init__ -- validation & computed fields ---")
    try:
        # TODO: create a Temperature dataclass with:
        #   celsius: float
        #   fahrenheit: float -- computed, not in __init__ (use field(init=False))
        #   kelvin: float -- computed, not in __init__
        #   __post_init__ that:
        #     - raises ValueError if celsius < -273.15
        #     - computes fahrenheit = celsius * 9 / 5 + 32
        #     - computes kelvin = celsius + 273.15
        # HINT: use field(init=False) for computed fields
        class Temperature:
            pass

        t = Temperature(100)
        print(f"100C = {t}")
        assert t.fahrenheit == 212.0
        assert t.kelvin == 373.15

        t2 = Temperature(0)
        print(f"0C = {t2.fahrenheit}F = {t2.kelvin}K")
        assert t2.fahrenheit == 32.0
        assert t2.kelvin == 273.15

        try:
            Temperature(-300)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"Caught: {e}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: frozen=True ---
    print("--- Section 4: frozen=True -- immutable dataclasses ---")
    try:
        # TODO: create a Color dataclass with frozen=True
        #   r: int, g: int, b: int
        # HINT: @dataclass(frozen=True)
        class Color:
            pass

        red = Color(255, 0, 0)
        blue = Color(0, 0, 255)
        print(f"red = {red}")

        try:
            red.r = 128
            assert False, "Should have raised"
        except AttributeError as e:
            print(f"Caught: {e}")

        palette = {red: "red", blue: "blue"}
        print(f"palette[Color(255, 0, 0)] = {palette[Color(255, 0, 0)]}")
        assert palette[Color(255, 0, 0)] == "red"

        color_set = {red, blue, Color(255, 0, 0)}
        print(f"color_set size: {len(color_set)}")
        assert len(color_set) == 2
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: slots=True ---
    print("--- Section 5: slots=True -- memory optimization ---")
    try:
        # TODO: create RegularPoint (normal dataclass) and SlottedPoint (with slots=True)
        #   both with x: float, y: float
        # HINT: @dataclass(slots=True)
        class RegularPoint:
            pass

        class SlottedPoint:
            pass

        r = RegularPoint(1.0, 2.0)
        s = SlottedPoint(1.0, 2.0)

        print(f"Regular has __dict__: {hasattr(r, '__dict__')}")
        assert hasattr(r, "__dict__")

        print(f"Slotted has __dict__: {hasattr(s, '__dict__')}")
        assert not hasattr(s, "__dict__")

        try:
            s.z = 3.0
            assert False, "Should have raised"
        except AttributeError as e:
            print(f"Caught: {e}")

        r.z = 3.0
        print(f"Regular point with z: x={r.x}, y={r.y}, z={r.z}")
        assert r.z == 3.0
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: order=True ---
    print("--- Section 6: order=True -- comparison methods ---")
    try:
        # TODO: create a Version dataclass with order=True
        #   major: int, minor: int, patch: int
        # HINT: @dataclass(order=True)
        class Version:
            pass

        versions = [
            Version(2, 1, 0),
            Version(1, 9, 5),
            Version(2, 0, 1),
            Version(1, 0, 0),
        ]

        sorted_versions = sorted(versions)
        for v in sorted_versions:
            print(f"  {v}")
        assert sorted_versions[0] == Version(1, 0, 0)
        assert sorted_versions[-1] == Version(2, 1, 0)

        print(f"Version(2,0,0) > Version(1,9,9): {Version(2,0,0) > Version(1,9,9)}")
        assert Version(2, 0, 0) > Version(1, 9, 9)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: kw_only=True ---
    print("--- Section 7: kw_only=True -- keyword-only fields ---")
    try:
        # TODO: create a DatabaseConfig dataclass with kw_only=True
        #   host: str, port: int, database: str, user: str, password: str
        #   pool_size: int = 5, timeout: float = 30.0
        # HINT: @dataclass(kw_only=True)
        class DatabaseConfig:
            pass

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

        try:
            DatabaseConfig("localhost", 5432, "myapp", "admin", "secret")
            assert False, "Should have raised TypeError"
        except TypeError as e:
            print(f"Caught: {e}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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

    try:
        # TODO: convert person to dict using asdict()
        # HINT: asdict(person)
        d = {}  # replace this
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

        # TODO: convert to JSON string
        json_str = ""  # replace this
        print(f"JSON:\n{json_str}")
        assert '"name": "Alice"' in json_str

        # TODO: convert person to tuple using astuple()
        # HINT: astuple(person)
        t = ()  # replace this
        print(f"astuple: {t}")
        assert t == ("Alice", 30, ("123 Main St", "Springfield", "IL", "62701"))

        # TODO: create modified copy with age=31 using replace()
        # HINT: replace(person, age=31)
        person2 = person  # replace this
        print(f"Original age: {person.age}, replaced age: {person2.age}")
        assert person.age == 30
        assert person2.age == 31
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
        # TODO: create a frozen Money dataclass and use replace
        # HINT: @dataclass(frozen=True) with amount: int, currency: str = "USD"
        class Money:
            pass

        price = Money(100)
        discounted = replace(price, amount=80)
        print(f"Price: {price} -> Discounted: {discounted}")
        assert price.amount == 100
        assert discounted.amount == 80
        assert discounted.currency == "USD"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (Money): {e}")

    print()

    # --- Section 9: Inheritance ---
    print("--- Section 9: Inheritance ---")
    try:
        # TODO: create Animal dataclass with name: str, species: str
        # Then create Pet(Animal) adding owner: str, vaccinated: bool = True
        # HINT: both need @dataclass decorator
        class Animal:
            pass

        class Pet(Animal):
            pass

        dog = Pet("Rex", "Dog", "Alice")
        print(f"Pet: {dog}")
        assert dog.name == "Rex"
        assert dog.species == "Dog"
        assert dog.owner == "Alice"
        assert dog.vaccinated is True
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (Animal/Pet): {e}")

    try:
        # TODO: create Base dataclass with value: int and __post_init__ that validates value >= 0
        # Then create Derived(Base) with label: str = "default" and __post_init__ that
        #   calls super().__post_init__() and uppercases self.label
        # HINT: don't forget super().__post_init__() in Derived
        class Base:
            pass

        class Derived(Base):
            pass

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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (Base/Derived): {e}")

    print()

    # --- Section 10: make_dataclass ---
    print("--- Section 10: make_dataclass -- dynamic creation ---")
    try:
        # TODO: create a Coordinate dataclass dynamically with fields x, y, z
        # HINT: make_dataclass("Coordinate", ["x", "y", "z"])
        Coordinate = None  # replace this

        c = Coordinate(1.0, 2.0, 3.0)
        print(f"Coordinate: {c}")
        assert c.x == 1.0
        assert c.y == 2.0
        assert c.z == 3.0

        # TODO: create a Config dataclass dynamically with:
        #   host: str, port: int (default 8080), debug: bool (default False)
        # HINT: use tuples with field() for defaults
        Config = None  # replace this

        cfg = Config(host="localhost")
        print(f"Config: {cfg}")
        assert cfg.host == "localhost"
        assert cfg.port == 8080
        assert cfg.debug is False
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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

    print(f"namedtuple: {pnt}")
    print(f"dataclass:  {pdc}")

    x, y = pnt
    print(f"Unpacked namedtuple: x={x}, y={y}")
    assert x == 3.0

    try:
        pnt.x = 5.0
        assert False, "Should have raised"
    except AttributeError:
        print("namedtuple is immutable (AttributeError on assignment)")

    point_set = {pnt, PointNT(3.0, 4.0)}
    print(f"namedtuple set size: {len(point_set)}")
    assert len(point_set) == 1

    pdc.x = 5.0
    print(f"Mutated dataclass: {pdc}")
    assert pdc.x == 5.0

    print(f"PointNT(3.0, 4.0) == (3.0, 4.0): {PointNT(3.0, 4.0) == (3.0, 4.0)}")
    assert PointNT(3.0, 4.0) == (3.0, 4.0)

    print()

    # --- Section 12: Exercise -- Config with validation ---
    print("--- Section 12: Exercise -- Config with Validation ---")
    try:
        # TODO: create an AppConfig dataclass with:
        #   host: str, port: int, debug: bool = False, tags: list[str] (default empty)
        #   __post_init__ that validates: host must not be empty, port must be 1-65535
        # HINT: use field(default_factory=list) for tags
        class AppConfig:
            pass

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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 13: Exercise -- Frozen Money class ---
    print("--- Section 13: Exercise -- Frozen Money Class ---")
    try:
        # TODO: create a CurrencyAmount dataclass that is:
        #   - frozen=True (immutable)
        #   - order=True (comparable)
        #   Fields: amount: int (in cents), currency: str = "USD"
        #   Add a @property 'dollars' that returns f"${self.amount / 100:.2f}"
        #   Add __add__ that:
        #     - returns NotImplemented if other is not CurrencyAmount
        #     - raises ValueError if currencies differ
        #     - returns replace(self, amount=self.amount + other.amount)
        # HINT: use replace() for creating new instances since it's frozen
        class CurrencyAmount:
            pass

        price = CurrencyAmount(1999)
        tax = CurrencyAmount(160)
        total = price + tax
        print(f"{price.dollars} + {tax.dollars} = {total.dollars}")
        assert total.amount == 2159
        assert total.dollars == "$21.59"

        try:
            price.amount = 0
            assert False, "Should have raised"
        except AttributeError:
            print("CurrencyAmount is frozen (immutable)")

        money_set = {price, tax, CurrencyAmount(1999)}
        print(f"Money set size: {len(money_set)}")
        assert len(money_set) == 2

        print(f"$19.99 > $1.60: {price > tax}")
        assert price > tax

        eur = replace(price, currency="EUR")
        print(f"EUR version: {eur}")
        assert eur.amount == 1999
        assert eur.currency == "EUR"

        try:
            price + eur
            assert False, "Should have raised"
        except ValueError as e:
            print(f"Caught: {e}")
            assert "Cannot add" in str(e)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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
