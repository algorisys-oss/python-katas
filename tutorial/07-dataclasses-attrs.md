# Kata 07 -- Dataclasses & Attrs

[prev: 06-type-hints-protocols](./06-type-hints-protocols.md) | [next: 08-enums-pattern-matching](./08-enums-pattern-matching.md)

---

## What We're Building

Python's `dataclasses` module (introduced in 3.7, enhanced in 3.10+) eliminates the boilerplate of writing `__init__`, `__repr__`, `__eq__`, and other dunder methods for classes that are primarily data containers. In this kata we'll master every feature of `@dataclass` -- from basic usage through `field()` customization, `__post_init__` validation, frozen/slotted/ordered variants, conversion utilities, and inheritance patterns. By the end you'll know exactly when to reach for a dataclass vs a namedtuple vs a plain class vs a dict.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `@dataclass` | Auto-generate `__init__`, `__repr__`, `__eq__` | Any class that's primarily data |
| `field()` | Customize individual fields (defaults, factories, metadata) | Mutable defaults, hidden fields, non-comparable fields |
| `__post_init__` | Run logic after auto-generated `__init__` | Validation, computed fields |
| `frozen=True` | Make instances immutable (hashable!) | Config objects, dict keys, set members |
| `slots=True` | Use `__slots__` for memory efficiency (3.10+) | High-volume instances |
| `order=True` | Auto-generate `__lt__`, `__le__`, `__gt__`, `__ge__` | Sortable data |
| `kw_only=True` | Force keyword-only arguments (3.10+) | APIs with many fields |
| `asdict`, `astuple` | Convert to dict/tuple (deep copy) | Serialization, JSON output |
| `replace` | Create a modified copy | Immutable update pattern |
| `make_dataclass` | Create a dataclass dynamically | Metaprogramming, dynamic schemas |
| Inheritance | Subclass dataclasses | Extending data models |
| vs `namedtuple` | Lightweight immutable tuples | Simple records, compatibility |

## The Code

### Step 1: Basic `@dataclass` -- auto `__init__`, `__repr__`, `__eq__`

The simplest use: annotate your fields with types, and `@dataclass` generates the boilerplate.

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

p1 = Point(3.0, 4.0)
p2 = Point(3.0, 4.0)
p3 = Point(1.0, 2.0)

print(p1)
# Output: Point(x=3.0, y=4.0)

print(p1 == p2)
# Output: True  (auto __eq__ compares all fields)

print(p1 == p3)
# Output: False
```

**What you get for free:** `__init__`, `__repr__`, and `__eq__`. No more typing `self.x = x; self.y = y` in every class.

### Step 2: `field()` -- default factories, metadata, repr/compare control

`field()` gives you fine-grained control over individual fields. The most important parameter is `default_factory` -- use it for mutable defaults (lists, dicts, sets).

```python
from dataclasses import dataclass, field

@dataclass
class Player:
    name: str
    score: int = 0
    # NEVER do: tags: list[str] = []  -- shared mutable default!
    tags: list[str] = field(default_factory=list)
    _internal_id: str = field(default="", repr=False)   # hidden from repr
    timestamp: float = field(default=0.0, compare=False)  # ignored in ==

    # metadata is for your own tools (serialization, validation, etc.)
    email: str = field(default="", metadata={"max_length": 255})

p = Player("Alice", 100, ["veteran", "admin"], "abc123", 1234567890.0, "alice@example.com")
print(p)
# Output: Player(name='Alice', score=100, tags=['veteran', 'admin'], timestamp=1234567890.0, email='alice@example.com')
# Note: _internal_id is NOT shown (repr=False)

p2 = Player("Alice", 100, ["veteran", "admin"], "xyz789", 9999999999.0, "alice@example.com")
print(p == p2)
# Output: True  (timestamp and _internal_id differ, but compare=False / repr=False don't affect eq by default -- only compare=False does)
```

**Key insight:** `repr=False` hides a field from the string representation. `compare=False` excludes it from `__eq__` (and ordering if `order=True`). `default_factory` is mandatory for mutable defaults -- if you use `field(default=[])`, Python raises a `ValueError`.

### Step 3: `__post_init__` -- validation and computed fields

`__post_init__` runs right after the generated `__init__`. Use it for validation, computed fields, or any setup logic.

```python
from dataclasses import dataclass, field

@dataclass
class Temperature:
    celsius: float
    fahrenheit: float = field(init=False)  # computed, not passed to __init__
    kelvin: float = field(init=False)

    def __post_init__(self):
        if self.celsius < -273.15:
            raise ValueError(f"Temperature {self.celsius}C is below absolute zero")
        self.fahrenheit = self.celsius * 9 / 5 + 32
        self.kelvin = self.celsius + 273.15

t = Temperature(100)
print(t)
# Output: Temperature(celsius=100, fahrenheit=212.0, kelvin=373.15)

t2 = Temperature(0)
print(f"{t2.celsius}C = {t2.fahrenheit}F = {t2.kelvin}K")
# Output: 0C = 32.0F = 273.15K

# Validation works:
try:
    Temperature(-300)
except ValueError as e:
    print(f"Caught: {e}")
# Output: Caught: Temperature -300C is below absolute zero
```

### Step 4: `frozen=True` -- immutable dataclasses

Frozen dataclasses raise `FrozenInstanceError` on attribute assignment. This makes them hashable (usable as dict keys and set members).

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

red = Color(255, 0, 0)
blue = Color(0, 0, 255)

print(red)
# Output: Color(r=255, g=0, b=0)

# Immutable!
try:
    red.r = 128
except AttributeError as e:
    print(f"Caught: {e}")
# Output: Caught: cannot assign to field 'r'

# Hashable -- can be used as dict keys and in sets
palette = {red: "red", blue: "blue"}
print(palette[Color(255, 0, 0)])
# Output: red

color_set = {red, blue, Color(255, 0, 0)}
print(len(color_set))
# Output: 2  (red appears once -- same hash and equality)
```

### Step 5: `slots=True` -- memory optimization (Python 3.10+)

`slots=True` generates `__slots__` for the class, which uses less memory per instance and provides slightly faster attribute access.

```python
from dataclasses import dataclass
import sys

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

print(f"Regular: {sys.getsizeof(r)} bytes, has __dict__: {hasattr(r, '__dict__')}")
# Output: Regular: 48 bytes, has __dict__: True

print(f"Slotted: {sys.getsizeof(s)} bytes, has __dict__: {hasattr(s, '__dict__')}")
# Output: Slotted: 48 bytes, has __dict__: False
# (sys.getsizeof doesn't count __dict__ overhead -- real savings show with many instances)

# Slotted classes prevent adding arbitrary attributes
try:
    s.z = 3.0
except AttributeError as e:
    print(f"Caught: {e}")
# Output: Caught: 'SlottedPoint' object has no attribute 'z'
```

**When to use:** High-volume data objects (thousands+ instances). The trade-off is you can't add arbitrary attributes at runtime.

### Step 6: `order=True` -- auto-generated comparison methods

`order=True` generates `__lt__`, `__le__`, `__gt__`, `__ge__` based on the fields (compared as tuples in declaration order).

```python
from dataclasses import dataclass

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

for v in sorted(versions):
    print(v)
# Output:
# Version(major=1, minor=0, patch=0)
# Version(major=1, minor=9, patch=5)
# Version(major=2, minor=0, patch=1)
# Version(major=2, minor=1, patch=0)

print(Version(2, 0, 0) > Version(1, 9, 9))
# Output: True
```

### Step 7: `kw_only=True` -- keyword-only fields (Python 3.10+)

`kw_only=True` forces all fields to be keyword-only in the generated `__init__`. This prevents positional argument mix-ups in classes with many fields.

```python
from dataclasses import dataclass

@dataclass(kw_only=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 5
    timeout: float = 30.0

# Must use keyword arguments:
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="myapp",
    user="admin",
    password="secret",
)
print(config)
# Output: DatabaseConfig(host='localhost', port=5432, database='myapp', user='admin', password='secret', pool_size=5, timeout=30.0)

# Positional args raise TypeError:
try:
    DatabaseConfig("localhost", 5432, "myapp", "admin", "secret")
except TypeError as e:
    print(f"Caught: {e}")
# Output: Caught: DatabaseConfig.__init__() takes 1 positional argument but 6 were given
```

### Step 8: `asdict`, `astuple`, `replace` -- conversion utilities

These functions convert dataclasses to standard Python types or create modified copies.

```python
from dataclasses import dataclass, asdict, astuple, replace

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

# asdict: deep conversion to dict (nested dataclasses become nested dicts)
d = asdict(person)
print(d)
# Output: {'name': 'Alice', 'age': 30, 'address': {'street': '123 Main St', 'city': 'Springfield', 'state': 'IL', 'zip_code': '62701'}}

# Great for JSON serialization:
import json
print(json.dumps(d, indent=2))

# astuple: deep conversion to tuple
t = astuple(person)
print(t)
# Output: ('Alice', 30, ('123 Main St', 'Springfield', 'IL', '62701'))

# replace: create a modified copy (the original is unchanged)
person2 = replace(person, age=31)
print(person2)
# Output: Person(name='Alice', age=31, address=Address(street='123 Main St', ...))
print(person.age)
# Output: 30  (original unchanged)

# replace is especially useful with frozen dataclasses:
@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "USD"

price = Money(100)
discounted = replace(price, amount=80)
print(f"{price} -> {discounted}")
# Output: Money(amount=100, currency='USD') -> Money(amount=80, currency='USD')
```

### Step 9: Inheritance -- field ordering rules and `__post_init__` chain

Dataclasses support inheritance, but there's a crucial rule: **a subclass cannot add non-default fields after a parent with default fields**.

```python
from dataclasses import dataclass, field

@dataclass
class Animal:
    name: str
    species: str

@dataclass
class Pet(Animal):
    owner: str
    vaccinated: bool = True

dog = Pet("Rex", "Dog", "Alice")
print(dog)
# Output: Pet(name='Rex', species='Dog', owner='Alice', vaccinated=True)

# __post_init__ chain: call super().__post_init__() to chain
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
        super().__post_init__()  # validate value from Base
        self.label = self.label.upper()

d = Derived(42, "hello")
print(d)
# Output: Derived(value=42, label='HELLO')

try:
    Derived(-1)
except ValueError as e:
    print(f"Caught: {e}")
# Output: Caught: value must be non-negative
```

**Field ordering rule:** In the MRO, all non-default fields must come before default fields. This means if a parent has fields with defaults, a child can only add fields with defaults (or use `kw_only`).

### Step 10: `make_dataclass` -- dynamic creation

`make_dataclass` creates dataclass types at runtime, useful for metaprogramming and dynamic schemas.

```python
from dataclasses import make_dataclass, field

# Create a dataclass dynamically
Coordinate = make_dataclass("Coordinate", ["x", "y", "z"])
c = Coordinate(1.0, 2.0, 3.0)
print(c)
# Output: Coordinate(x=1.0, y=2.0, z=3.0)

# With types and defaults
Config = make_dataclass(
    "Config",
    [
        ("host", str),
        ("port", int, field(default=8080)),
        ("debug", bool, field(default=False)),
    ],
)
cfg = Config(host="localhost")
print(cfg)
# Output: Config(host='localhost', port=8080, debug=False)
```

### Step 11: Comparison -- dataclass vs namedtuple vs plain class vs dict

```
                    dataclass     namedtuple    plain class    dict
__init__ auto       Yes           Yes           No             N/A
__repr__ auto       Yes           Yes           No             Yes
__eq__ auto         Yes           Yes (by val)  No (by id)     Yes (by val)
Mutable             Yes*          No            Yes            Yes
Hashable            frozen only   Yes           if __hash__    No
Type checking       Yes           Partial       Yes            No
Default values      Yes           Yes (3.6+)    Manual         N/A
Validation          __post_init__ No            Manual         No
Slots               Yes (3.10+)   No**          Manual         No
Inheritance         Yes           Awkward       Yes            N/A

* Unless frozen=True
** _fields provides similar introspection
```

**When to use what:**
- **dataclass** -- Most cases. Structured data with validation, defaults, mutability control.
- **namedtuple** -- Simple immutable records. Interop with tuple unpacking. Legacy code.
- **plain class** -- Complex behavior beyond data storage. Heavy method logic.
- **dict** -- Dynamic keys, JSON-shaped data, quick prototyping.

## Playground

Run the full interactive demo:

```bash
python playground/07_dataclasses_attrs.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Decorator magic

`@dataclass` is a class decorator that inspects the class body for annotated fields, then generates and attaches dunder methods. It uses `inspect`-level introspection but does everything at class creation time (not at instance creation time), so there's zero runtime overhead per instance.

```
@dataclass
class Point:
    x: float
    y: float

# Python sees the annotations {'x': float, 'y': float}
# and generates:
#   def __init__(self, x: float, y: float): ...
#   def __repr__(self): return f"Point(x={self.x!r}, y={self.y!r})"
#   def __eq__(self, other): return (self.x, self.y) == (other.x, other.y)
```

### Field resolution order

When you subclass a dataclass, Python merges fields from all classes in the MRO. Fields are ordered: parent fields first, then child fields. This is why you can't put a non-default field in a child after a parent that has default fields -- it would violate Python's rule that positional parameters must come before keyword parameters.

### `frozen=True` internals

Frozen dataclasses generate `__setattr__` and `__delattr__` that raise `FrozenInstanceError`. The generated `__init__` uses `object.__setattr__` to bypass its own restriction during initialization.

## Exercises

### Exercise 1: Build a `Config` dataclass with validation

Build a `Config` dataclass with fields `host` (str), `port` (int), `debug` (bool, default `False`), and `tags` (list of str, default empty). Add `__post_init__` validation: port must be 1-65535, host must not be empty.

```python
@dataclass
class Config:
    host: str
    port: int
    debug: bool = False
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        # validate host and port
        ...

# Should work:
c = Config("localhost", 8080, tags=["web", "api"])
print(c)

# Should raise ValueError:
Config("", 8080)    # empty host
Config("localhost", 99999)  # invalid port
```

### Exercise 2: Implement a frozen `Money` class

Create a frozen, ordered dataclass `Money` with `amount` (int, in cents) and `currency` (str, default "USD"). Implement `__add__` for same-currency addition, and a `dollars` property. Use `replace` for currency conversion.

```python
@dataclass(frozen=True, order=True)
class Money:
    amount: int  # in cents
    currency: str = "USD"

    @property
    def dollars(self) -> str:
        return f"${self.amount / 100:.2f}"

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return replace(self, amount=self.amount + other.amount)

price = Money(1999)  # $19.99
tax = Money(160)     # $1.60
total = price + tax
print(f"{price.dollars} + {tax.dollars} = {total.dollars}")
# Expected: $19.99 + $1.60 = $21.59
```

## What's Next

In [Kata 08 -- Enums & Pattern Matching](./08-enums-pattern-matching.md), we'll explore Python's `enum` module and the `match`/`case` statement (Python 3.10+). You'll learn how to model finite sets of values, use structural pattern matching for clean control flow, and combine enums with dataclasses for expressive domain models.

---

[prev: 06-type-hints-protocols](./06-type-hints-protocols.md) | [next: 08-enums-pattern-matching](./08-enums-pattern-matching.md)
