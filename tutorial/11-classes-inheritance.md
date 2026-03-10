# Kata 11 -- Classes & Inheritance

[prev: 10-closures-scoping](./10-closures-scoping.md) | [next: 12-properties-descriptors](./12-properties-descriptors.md)

---

## What We're Building

Python's class system is built on a remarkably flexible foundation. Single inheritance is straightforward, but Python also supports **multiple inheritance** -- and with it comes the **diamond problem**, **Method Resolution Order (MRO)**, and the elegant `super()` function that makes cooperative inheritance possible.

In this kata we'll build an animal class hierarchy, create reusable **mixins** (SerializableMixin, LoggableMixin), use `__init_subclass__` for automatic plugin registration, and understand how `super()` navigates the MRO to enable **cooperative multiple inheritance**. By the end you'll know exactly how Python resolves methods, why the diamond problem isn't really a problem in Python, and how to design clean, composable class hierarchies.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| MRO (C3 linearization) | Determines method lookup order for a class | Understanding which method gets called in a hierarchy |
| `super()` | Delegates to the next class in the MRO | Calling parent methods without hardcoding class names |
| Multiple inheritance | A class inherits from multiple base classes | Composing behavior from orthogonal sources |
| Mixins | Small, focused classes that add a single capability | Reusable cross-cutting concerns (serialization, logging) |
| `__init_subclass__` | Hook called when a class is subclassed | Plugin registration, validation, auto-configuration |
| Cooperative multiple inheritance | All classes in a hierarchy use `super()` consistently | Making diamond inheritance work correctly |
| Diamond problem | Same base class reached via multiple paths | Understanding why MRO and `super()` matter |

## The Code

### Step 1: Basic class hierarchy -- Animal kingdom

Start with a simple single-inheritance hierarchy to establish the fundamentals:

```python
class Animal:
    """Base class for all animals."""

    def __init__(self, name: str, sound: str):
        self.name = name
        self.sound = sound

    def speak(self) -> str:
        return f"{self.name} says {self.sound}!"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"


class Dog(Animal):
    def __init__(self, name: str, breed: str):
        super().__init__(name, sound="Woof")
        self.breed = breed

    def fetch(self, item: str) -> str:
        return f"{self.name} fetches the {item}!"


class Cat(Animal):
    def __init__(self, name: str, indoor: bool = True):
        super().__init__(name, sound="Meow")
        self.indoor = indoor

    def purr(self) -> str:
        return f"{self.name} purrs contentedly."


dog = Dog("Rex", breed="German Shepherd")
cat = Cat("Whiskers")

print(dog.speak())   # Rex says Woof!
print(cat.speak())   # Whiskers says Meow!
print(dog.fetch("ball"))  # Rex fetches the ball!
```

`super().__init__(...)` calls `Animal.__init__` without hardcoding the parent class name. This matters for multiple inheritance -- `super()` doesn't mean "parent class", it means "next class in the MRO".

### Step 2: Method Resolution Order (MRO)

When you call a method, Python searches the class and its ancestors in a specific order called the **MRO**. Python uses the **C3 linearization** algorithm to compute it.

```python
class A:
    def greet(self):
        return "A"

class B(A):
    def greet(self):
        return "B"

class C(A):
    def greet(self):
        return "C"

class D(B, C):
    pass

# D doesn't define greet, so Python searches the MRO
print(D().greet())  # B -- because B comes before C in D's MRO

# Inspect the MRO
print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)

# Also available as a list
print(D.mro())
# [<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>]
```

The C3 linearization guarantees:
1. **Children come before parents** -- D before B, B before A
2. **Left-to-right order is preserved** -- B before C (as declared in `class D(B, C)`)
3. **Monotonicity** -- if B comes before C in D's MRO, B comes before C in every subclass of D

### Step 3: The diamond problem

The diamond problem occurs when a class inherits from two classes that share a common ancestor. Without MRO, methods from the shared ancestor could be called multiple times.

```python
class Base:
    def __init__(self):
        print("  Base.__init__")
        self.base_initialized = True

class Left(Base):
    def __init__(self):
        print("  Left.__init__")
        super().__init__()  # Calls next in MRO, NOT necessarily Base
        self.left_initialized = True

class Right(Base):
    def __init__(self):
        print("  Right.__init__")
        super().__init__()  # Calls next in MRO
        self.right_initialized = True

class Diamond(Left, Right):
    def __init__(self):
        print("  Diamond.__init__")
        super().__init__()  # Calls Left.__init__
        self.diamond_initialized = True

# MRO: Diamond -> Left -> Right -> Base -> object
print(Diamond.__mro__)

d = Diamond()
# Output:
#   Diamond.__init__
#   Left.__init__
#   Right.__init__
#   Base.__init__

# Base.__init__ is called exactly ONCE, even though both Left and Right inherit from it.
# This is because super() follows the MRO, not the direct parent.
print(d.base_initialized)   # True
print(d.left_initialized)   # True
print(d.right_initialized)  # True
print(d.diamond_initialized)  # True
```

Key insight: `super().__init__()` in `Left` doesn't call `Base.__init__` -- it calls `Right.__init__`, because `Right` is next in Diamond's MRO. This is why it's called **cooperative** multiple inheritance: every class cooperates by calling `super()`.

### Step 4: How `super()` actually works

`super()` returns a proxy object that delegates method calls to the next class in the MRO. It uses two pieces of information: the current class and the instance.

```python
class A:
    def method(self):
        print(f"  A.method (MRO next: object)")
        return "A"

class B(A):
    def method(self):
        print(f"  B.method (MRO next: A)")
        result = super().method()  # Calls A.method
        return f"B -> {result}"

class C(A):
    def method(self):
        print(f"  C.method (MRO next: A)")
        result = super().method()  # In C's own MRO, next is A
        return f"C -> {result}"

class D(B, C):
    def method(self):
        print(f"  D.method (MRO next: B)")
        result = super().method()  # Calls B.method
        return f"D -> {result}"

# MRO: D -> B -> C -> A -> object
print(D().method())
# Output:
#   D.method (MRO next: B)
#   B.method (MRO next: A)    -- WRONG comment! super() in B calls C, not A
#   C.method (MRO next: A)
#   A.method (MRO next: object)
#   D -> B -> C -> A

# Wait -- B.method's super() called C.method, not A.method!
# That's because super() uses the MRO of the INSTANCE's class (D),
# not the MRO of the class where super() is written (B).
```

This is the crucial insight: `super()` is **instance-aware**. When called inside `B.method` on a `D` instance, it looks at D's MRO (D -> B -> C -> A), finds B's position, and calls the **next** class (C), not B's direct parent (A).

### Step 5: Cooperative multiple inheritance with `**kwargs`

For cooperative `__init__` to work with different parameter sets, use `**kwargs` to pass unrecognized arguments up the chain:

```python
class Animal:
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)  # Pass remaining kwargs to object()
        self.name = name

class Swimmer:
    def __init__(self, swim_speed: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.swim_speed = swim_speed

    def swim(self) -> str:
        return f"{self.name} swims at speed {self.swim_speed}"

class Flyer:
    def __init__(self, max_altitude: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self.max_altitude = max_altitude

    def fly(self) -> str:
        return f"{self.name} flies up to {self.max_altitude}m"

class Duck(Animal, Swimmer, Flyer):
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)

    def describe(self) -> str:
        return f"{self.name}: can swim and fly!"

duck = Duck("Donald", swim_speed=8, max_altitude=500)
print(duck.swim())      # Donald swims at speed 8
print(duck.fly())       # Donald flies up to 500m
print(duck.describe())  # Donald: can swim and fly!

# MRO: Duck -> Animal -> Swimmer -> Flyer -> object
print(Duck.__mro__)
```

The `**kwargs` pattern lets each class extract the arguments it needs and forward the rest. This is the standard pattern for cooperative multiple inheritance.

### Step 6: Mixins -- composable behavior

A **mixin** is a class designed to be combined with other classes via multiple inheritance. It adds a single, focused capability. Mixins typically:
- Don't have their own `__init__` (or use `**kwargs` cooperatively)
- Provide methods that enhance the class they're mixed into
- Are not meant to be instantiated alone

```python
import json

class SerializableMixin:
    """Mixin that adds JSON serialization."""

    def to_dict(self) -> dict:
        """Convert public attributes to a dict."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dict."""
        return cls(**data)


class LoggableMixin:
    """Mixin that adds logging to method calls."""

    _log: list = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._log = []  # Each subclass gets its own log

    def log(self, message: str):
        entry = f"[{type(self).__name__}] {message}"
        type(self)._log.append(entry)

    @classmethod
    def get_log(cls) -> list:
        return cls._log.copy()

    @classmethod
    def clear_log(cls):
        cls._log.clear()


class User(SerializableMixin, LoggableMixin):
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

    def update_email(self, new_email: str):
        old = self.email
        self.email = new_email
        self.log(f"Email changed: {old} -> {new_email}")

    def __repr__(self):
        return f"User({self.username!r}, {self.email!r})"


user = User("alice", "alice@example.com")
print(user.to_json())
# {"username": "alice", "email": "alice@example.com"}

user.update_email("alice@newdomain.com")
print(User.get_log())
# ["[User] Email changed: alice@example.com -> alice@newdomain.com"]

user2 = User.from_dict({"username": "bob", "email": "bob@example.com"})
print(user2)  # User('bob', 'bob@example.com')
```

### Step 7: `__init_subclass__` -- hook into subclassing

`__init_subclass__` is called whenever a class is subclassed. It's perfect for plugin registration, validation, and auto-configuration -- without needing metaclasses.

```python
class Plugin:
    """Base class that auto-registers plugins."""
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, plugin_name: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__.lower()
        Plugin._registry[name] = cls

    @classmethod
    def create(cls, name: str, **kwargs):
        """Factory: create a plugin by registered name."""
        if name not in cls._registry:
            raise ValueError(f"Unknown plugin: {name!r}")
        return cls._registry[name](**kwargs)

    @classmethod
    def list_plugins(cls) -> list[str]:
        return list(cls._registry.keys())


class JSONPlugin(Plugin, plugin_name="json"):
    def process(self, data):
        return f"Processing as JSON: {data}"

class XMLPlugin(Plugin, plugin_name="xml"):
    def process(self, data):
        return f"Processing as XML: {data}"

class CSVPlugin(Plugin):  # Uses default name: "csvplugin"
    def process(self, data):
        return f"Processing as CSV: {data}"


print(Plugin.list_plugins())
# ['json', 'xml', 'csvplugin']

p = Plugin.create("json")
print(p.process({"key": "value"}))
# Processing as JSON: {'key': 'value'}

p = Plugin.create("xml")
print(p.process("<root/>"))
# Processing as XML: <root/>
```

`__init_subclass__` receives keyword arguments passed in the class definition (`plugin_name="json"`). This is cleaner than decorators for this pattern because it's impossible to forget to register -- subclassing automatically registers.

### Step 8: Practical example -- combining everything

Let's build a notification system that combines the animal hierarchy, mixins, and plugin registration:

```python
import json
from datetime import datetime


class Notifier:
    """Base notifier with plugin registration via __init_subclass__."""
    _notifiers: dict[str, type] = {}

    def __init_subclass__(cls, channel: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if channel:
            Notifier._notifiers[channel] = cls

    def __init__(self, recipient: str, **kwargs):
        super().__init__(**kwargs)
        self.recipient = recipient

    def send(self, message: str) -> str:
        raise NotImplementedError

    @classmethod
    def for_channel(cls, channel: str, recipient: str) -> "Notifier":
        return cls._notifiers[channel](recipient=recipient)


class SerializableNotifierMixin:
    """Adds serialization to notifiers."""

    def to_dict(self) -> dict:
        return {
            "type": type(self).__name__,
            "recipient": self.recipient,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EmailNotifier(Notifier, SerializableNotifierMixin, channel="email"):
    def send(self, message: str) -> str:
        return f"Email to {self.recipient}: {message}"


class SMSNotifier(Notifier, SerializableNotifierMixin, channel="sms"):
    def send(self, message: str) -> str:
        return f"SMS to {self.recipient}: {message}"


class SlackNotifier(Notifier, SerializableNotifierMixin, channel="slack"):
    def send(self, message: str) -> str:
        return f"Slack to #{self.recipient}: {message}"


# Factory usage
notifier = Notifier.for_channel("email", "alice@example.com")
print(notifier.send("Hello!"))
# Email to alice@example.com: Hello!
print(notifier.to_json())
# {"type": "EmailNotifier", "recipient": "alice@example.com"}

# Send to multiple channels
for channel, recipient in [("email", "bob@test.com"), ("sms", "+1234"), ("slack", "general")]:
    n = Notifier.for_channel(channel, recipient)
    print(n.send("Server deployed!"))
```

## Playground

Run the full interactive demo:

```bash
python playground/11_classes_inheritance.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### C3 Linearization Algorithm

The MRO is computed using C3 linearization, which merges the MROs of parent classes while preserving local precedence order:

```
For class D(B, C):
  L[D] = D + merge(L[B], L[C], [B, C])

Where merge takes the first head that doesn't appear in the tail of any other list.

Example:
  L[A] = [A, object]
  L[B] = [B, A, object]
  L[C] = [C, A, object]
  L[D] = [D] + merge([B, A, object], [C, A, object], [B, C])
       = [D, B] + merge([A, object], [C, A, object], [C])
       = [D, B, C] + merge([A, object], [A, object])
       = [D, B, C, A, object]
```

### super() dispatch mechanism

```
super() in class X on instance of class D:
  1. Get D.__mro__ = [D, B, C, A, object]
  2. Find X's position in the MRO
  3. Return a proxy that delegates to the NEXT class after X
  4. If X is B, next is C (not A!)
```

### Mixin design principles

```
Good mixin:                     Bad mixin:
  - Single responsibility         - Multiple concerns
  - No __init__ (or **kwargs)     - Complex __init__
  - No instance state (or minimal)- Lots of state
  - Methods use self.xxx          - Methods use mixin-specific state
  - Named XxxMixin                - Named like a regular class
```

## Exercises

### Exercise 1: Build a shape hierarchy with area calculation

Create a `Shape` base class with `area()` and `perimeter()` methods. Implement `Circle`, `Rectangle`, and `Square` (inheriting from `Rectangle`). Use `super()` properly.

```python
import math

class Shape:
    def area(self) -> float:
        raise NotImplementedError
    def perimeter(self) -> float:
        raise NotImplementedError
    def describe(self) -> str:
        return f"{type(self).__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"

class Circle(Shape):
    ...

class Rectangle(Shape):
    ...

class Square(Rectangle):
    ...

c = Circle(radius=5)
r = Rectangle(width=4, height=6)
s = Square(side=3)

print(c.describe())  # Circle: area=78.54, perimeter=31.42
print(r.describe())  # Rectangle: area=24.00, perimeter=20.00
print(s.describe())  # Square: area=9.00, perimeter=12.00
```

### Exercise 2: Create a `ComparableMixin` and a `PrintableMixin`

Build two mixins and combine them with a `Product` class:

```python
class ComparableMixin:
    """Adds comparison operators based on a _compare_key() method."""
    # Subclasses must implement _compare_key() -> comparable value
    # Provide: __lt__, __le__, __gt__, __ge__, __eq__
    ...

class PrintableMixin:
    """Adds pretty __str__ using public attributes."""
    ...

class Product(ComparableMixin, PrintableMixin):
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def _compare_key(self):
        return self.price

p1 = Product("Widget", 9.99)
p2 = Product("Gadget", 24.99)

print(p1 < p2)   # True (by price)
print(p1)         # Product(name='Widget', price=9.99)
```

## What's Next

In [Kata 12 -- Properties & Descriptors](./12-properties-descriptors.md), we'll explore Python's descriptor protocol -- the mechanism behind `@property`, `__get__`, `__set__`, and `__delete__`. You'll build custom descriptors for validation, lazy attributes, and type-checked fields, understanding the foundation that powers much of Python's OOP magic.

---

[prev: 10-closures-scoping](./10-closures-scoping.md) | [next: 12-properties-descriptors](./12-properties-descriptors.md)
