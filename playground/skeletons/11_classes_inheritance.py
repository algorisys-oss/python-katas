"""
Kata 11 -- Classes & Inheritance
Run: python playground/skeletons/11_classes_inheritance.py

Master MRO (Method Resolution Order), super(), multiple inheritance, mixins,
__init_subclass__, cooperative multiple inheritance, and the diamond problem.
"""

import json


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Basic class hierarchy -- Animal kingdom ---
    print("--- Section 1: Animal Hierarchy ---")

    class Animal:
        """Base class for all animals."""

        def __init__(self, name: str, sound: str):
            self.name = name
            self.sound = sound

        def speak(self) -> str:
            # TODO: return f"{self.name} says {self.sound}!"
            pass

        def __repr__(self) -> str:
            return f"{type(self).__name__}(name={self.name!r})"

    class Dog(Animal):
        def __init__(self, name: str, breed: str):
            # TODO: call super().__init__ with name and sound="Woof", then set self.breed
            # HINT: super().__init__(name, sound="Woof")
            pass

        def fetch(self, item: str) -> str:
            # TODO: return f"{self.name} fetches the {item}!"
            pass

    class Cat(Animal):
        def __init__(self, name: str, indoor: bool = True):
            # TODO: call super().__init__ with name and sound="Meow", then set self.indoor
            pass

        def purr(self) -> str:
            # TODO: return f"{self.name} purrs contentedly."
            pass

    try:
        dog = Dog("Rex", breed="German Shepherd")
        cat = Cat("Whiskers")

        print(f"  {dog.speak()}")
        assert dog.speak() == "Rex says Woof!"
        print(f"  {cat.speak()}")
        assert cat.speak() == "Whiskers says Meow!"
        print(f"  {dog.fetch('ball')}")
        assert dog.fetch("ball") == "Rex fetches the ball!"
        print(f"  {cat.purr()}")
        assert cat.purr() == "Whiskers purrs contentedly."
        print(f"  {repr(dog)}")
        assert repr(dog) == "Dog(name='Rex')"
        assert dog.breed == "German Shepherd"
        assert cat.indoor is True
        assert isinstance(dog, Animal)
        assert isinstance(cat, Animal)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Method Resolution Order (MRO) ---
    print("--- Section 2: Method Resolution Order ---")

    class A:
        def greet(self):
            return "A"

    class B(A):
        def greet(self):
            return "B"

    class C(A):
        def greet(self):
            return "C"

    # TODO: define class D that inherits from B and C (in that order)
    # HINT: class D(B, C): pass
    class D:
        pass

    try:
        d = D()
        print(f"  D().greet() = {d.greet()!r}")
        assert d.greet() == "B"  # B comes before C in MRO

        # TODO: get the MRO as a list of class names
        # HINT: [cls.__name__ for cls in D.__mro__]
        mro_names = []  # replace this
        print(f"  D.__mro__ = {mro_names}")
        assert mro_names == ["D", "B", "C", "A", "object"]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: The diamond problem ---
    print("--- Section 3: Diamond Problem ---")

    class Base:
        def __init__(self):
            print("    Base.__init__")
            self.base_initialized = True

    class Left(Base):
        def __init__(self):
            print("    Left.__init__")
            # TODO: call super().__init__() to continue up the MRO
            self.left_initialized = True

    class Right(Base):
        def __init__(self):
            print("    Right.__init__")
            # TODO: call super().__init__() to continue up the MRO
            self.right_initialized = True

    class Diamond(Left, Right):
        def __init__(self):
            print("    Diamond.__init__")
            # TODO: call super().__init__() to start the MRO chain
            self.diamond_initialized = True

    try:
        # MRO: Diamond -> Left -> Right -> Base -> object
        diamond_mro = [cls.__name__ for cls in Diamond.__mro__]
        print(f"  Diamond MRO: {diamond_mro}")
        assert diamond_mro == ["Diamond", "Left", "Right", "Base", "object"]

        print("  Creating Diamond instance:")
        diamond = Diamond()
        # Output order: Diamond, Left, Right, Base -- each called exactly once
        assert diamond.base_initialized is True
        assert diamond.left_initialized is True
        assert diamond.right_initialized is True
        assert diamond.diamond_initialized is True
        print("  All four __init__ methods called exactly once!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: How super() actually works ---
    print("--- Section 4: super() Dispatch ---")

    class A2:
        def method(self):
            return "A"

    class B2(A2):
        def method(self):
            # TODO: call super().method() and prepend "B -> "
            # HINT: result = super().method(); return f"B -> {result}"
            pass

    class C2(A2):
        def method(self):
            # TODO: call super().method() and prepend "C -> "
            pass

    class D2(B2, C2):
        def method(self):
            # TODO: call super().method() and prepend "D -> "
            pass

    try:
        # MRO: D2 -> B2 -> C2 -> A2 -> object
        result = D2().method()
        print(f"  D2().method() = {result!r}")
        assert result == "D -> B -> C -> A"

        # Demonstrate: same B2 class, different behavior based on instance type
        result_b = B2().method()
        print(f"  B2().method() = {result_b!r}")
        assert result_b == "B -> A"

        print("  super() is instance-aware: same class, different MRO paths!")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Cooperative multiple inheritance with **kwargs ---
    print("--- Section 5: Cooperative **kwargs ---")

    class Animal2:
        def __init__(self, name: str, **kwargs):
            super().__init__(**kwargs)
            self.name = name

    class Swimmer:
        def __init__(self, swim_speed: int = 5, **kwargs):
            # TODO: call super().__init__(**kwargs), then set self.swim_speed
            pass

        def swim(self) -> str:
            # TODO: return f"{self.name} swims at speed {self.swim_speed}"
            pass

    class Flyer:
        def __init__(self, max_altitude: int = 1000, **kwargs):
            # TODO: call super().__init__(**kwargs), then set self.max_altitude
            pass

        def fly(self) -> str:
            # TODO: return f"{self.name} flies up to {self.max_altitude}m"
            pass

    class Duck(Animal2, Swimmer, Flyer):
        def __init__(self, name: str, **kwargs):
            # TODO: call super().__init__(name=name, **kwargs)
            pass

        def describe(self) -> str:
            return f"{self.name}: can swim and fly!"

    try:
        duck = Duck("Donald", swim_speed=8, max_altitude=500)
        print(f"  {duck.swim()}")
        assert duck.swim() == "Donald swims at speed 8"
        print(f"  {duck.fly()}")
        assert duck.fly() == "Donald flies up to 500m"
        print(f"  {duck.describe()}")
        assert duck.describe() == "Donald: can swim and fly!"

        # MRO: Duck -> Animal2 -> Swimmer -> Flyer -> object
        duck_mro = [cls.__name__ for cls in Duck.__mro__]
        print(f"  Duck MRO: {duck_mro}")
        assert duck_mro == ["Duck", "Animal2", "Swimmer", "Flyer", "object"]

        # Default values work too
        default_duck = Duck("Daisy")
        assert default_duck.swim_speed == 5
        assert default_duck.max_altitude == 1000
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Mixins -- SerializableMixin ---
    print("--- Section 6: SerializableMixin ---")

    class SerializableMixin:
        """Mixin that adds JSON serialization."""

        def to_dict(self) -> dict:
            """Convert public attributes to a dict."""
            # TODO: return a dict of all non-underscore-prefixed attributes
            # HINT: {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
            pass

        def to_json(self) -> str:
            """Serialize to JSON string."""
            # TODO: return json.dumps(self.to_dict(), default=str)
            pass

        @classmethod
        def from_dict(cls, data: dict):
            """Create instance from dict."""
            # TODO: return cls(**data)
            pass

    class Product(SerializableMixin):
        def __init__(self, name: str, price: float):
            self.name = name
            self.price = price

        def __repr__(self):
            return f"Product({self.name!r}, {self.price})"

    try:
        p = Product("Widget", 9.99)
        d = p.to_dict()
        print(f"  to_dict: {d}")
        assert d == {"name": "Widget", "price": 9.99}

        j = p.to_json()
        print(f"  to_json: {j}")
        assert json.loads(j) == {"name": "Widget", "price": 9.99}

        p2 = Product.from_dict({"name": "Gadget", "price": 24.99})
        print(f"  from_dict: {p2}")
        assert p2.name == "Gadget"
        assert p2.price == 24.99
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Mixins -- LoggableMixin ---
    print("--- Section 7: LoggableMixin ---")

    class LoggableMixin:
        """Mixin that adds logging to method calls."""

        _log: list = []

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls._log = []  # Each subclass gets its own log

        def log(self, message: str):
            # TODO: create entry as f"[{type(self).__name__}] {message}" and append to class log
            # HINT: type(self)._log.append(entry)
            pass

        @classmethod
        def get_log(cls) -> list:
            return cls._log.copy()

        @classmethod
        def clear_log(cls):
            cls._log.clear()

    try:
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
        print(f"  {user.to_json()}")
        assert json.loads(user.to_json()) == {"username": "alice", "email": "alice@example.com"}

        user.update_email("alice@newdomain.com")
        log = User.get_log()
        print(f"  Log: {log}")
        assert log == ["[User] Email changed: alice@example.com -> alice@newdomain.com"]

        user2 = User.from_dict({"username": "bob", "email": "bob@example.com"})
        print(f"  from_dict: {user2}")
        assert user2.username == "bob"

        # Verify separate logs per class
        class Admin(SerializableMixin, LoggableMixin):
            def __init__(self, username: str, level: int):
                self.username = username
                self.level = level

            def promote(self):
                self.level += 1
                self.log(f"Promoted to level {self.level}")

        admin = Admin("superuser", 1)
        admin.promote()
        print(f"  Admin log: {Admin.get_log()}")
        assert Admin.get_log() == ["[Admin] Promoted to level 2"]
        assert len(User.get_log()) == 1

        User.clear_log()
        Admin.clear_log()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: __init_subclass__ -- plugin registration ---
    print("--- Section 8: __init_subclass__ Plugin Registration ---")

    class Plugin:
        """Base class that auto-registers plugins."""
        _registry: dict[str, type] = {}

        def __init_subclass__(cls, plugin_name: str | None = None, **kwargs):
            super().__init_subclass__(**kwargs)
            # TODO: register cls in Plugin._registry using plugin_name or cls.__name__.lower()
            # HINT: name = plugin_name or cls.__name__.lower(); Plugin._registry[name] = cls
            pass

        @classmethod
        def create(cls, name: str, **kwargs):
            """Factory: create a plugin by registered name."""
            # TODO: look up name in _registry, raise ValueError if not found, else instantiate
            pass

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

    try:
        plugins = Plugin.list_plugins()
        print(f"  Registered plugins: {plugins}")
        assert "json" in plugins
        assert "xml" in plugins
        assert "csvplugin" in plugins

        jp = Plugin.create("json")
        result = jp.process({"key": "value"})
        print(f"  {result}")
        assert result == "Processing as JSON: {'key': 'value'}"

        xp = Plugin.create("xml")
        result = xp.process("<root/>")
        print(f"  {result}")
        assert result == "Processing as XML: <root/>"

        cp = Plugin.create("csvplugin")
        result = cp.process("a,b,c")
        print(f"  {result}")
        assert result == "Processing as CSV: a,b,c"

        # Test error for unknown plugin
        try:
            Plugin.create("yaml")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"  Expected error: {e}")
            assert "yaml" in str(e)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 9: Combining everything -- Notifier system ---
    print("--- Section 9: Notifier System ---")

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

    # TODO: implement EmailNotifier, SMSNotifier, SlackNotifier
    # Each should inherit from Notifier and SerializableNotifierMixin
    # Each should specify a channel keyword and implement send()
    # HINT: class EmailNotifier(Notifier, SerializableNotifierMixin, channel="email"):
    #           def send(self, message): return f"Email to {self.recipient}: {message}"

    class EmailNotifier(Notifier, SerializableNotifierMixin, channel="email"):
        def send(self, message: str) -> str:
            pass

    class SMSNotifier(Notifier, SerializableNotifierMixin, channel="sms"):
        def send(self, message: str) -> str:
            pass

    class SlackNotifier(Notifier, SerializableNotifierMixin, channel="slack"):
        def send(self, message: str) -> str:
            pass

    try:
        # Factory usage
        email_n = Notifier.for_channel("email", "alice@example.com")
        result = email_n.send("Hello!")
        print(f"  {result}")
        assert result == "Email to alice@example.com: Hello!"

        email_json = email_n.to_json()
        print(f"  {email_json}")
        assert json.loads(email_json) == {"type": "EmailNotifier", "recipient": "alice@example.com"}

        # Send to multiple channels
        channels = [("email", "bob@test.com"), ("sms", "+1234"), ("slack", "general")]
        for channel, recipient in channels:
            n = Notifier.for_channel(channel, recipient)
            msg = n.send("Server deployed!")
            print(f"  {msg}")

        assert SMSNotifier("x").send("hi") == "SMS to x: hi"
        assert SlackNotifier("ch").send("yo") == "Slack to #ch: yo"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 10: Exercise -- Shape hierarchy ---
    print("--- Section 10: Exercise -- Shape Hierarchy ---")

    import math

    class Shape:
        def area(self) -> float:
            raise NotImplementedError

        def perimeter(self) -> float:
            raise NotImplementedError

        def describe(self) -> str:
            return f"{type(self).__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"

    # TODO: implement Circle with radius, area = pi*r^2, perimeter = 2*pi*r
    class Circle(Shape):
        def __init__(self, radius: float):
            self.radius = radius

        def area(self) -> float:
            pass

        def perimeter(self) -> float:
            pass

    # TODO: implement Rectangle with width and height
    class Rectangle(Shape):
        def __init__(self, width: float, height: float):
            self.width = width
            self.height = height

        def area(self) -> float:
            pass

        def perimeter(self) -> float:
            pass

    # TODO: implement Square inheriting from Rectangle, using super().__init__
    # HINT: class Square(Rectangle): def __init__(self, side): super().__init__(width=side, height=side)
    class Square(Rectangle):
        def __init__(self, side: float):
            pass

    try:
        c = Circle(radius=5)
        r = Rectangle(width=4, height=6)
        s = Square(side=3)

        print(f"  {c.describe()}")
        assert abs(c.area() - 78.54) < 0.01
        assert abs(c.perimeter() - 31.42) < 0.01

        print(f"  {r.describe()}")
        assert r.area() == 24.0
        assert r.perimeter() == 20.0

        print(f"  {s.describe()}")
        assert s.area() == 9.0
        assert s.perimeter() == 12.0

        # Square is a Rectangle
        assert isinstance(s, Rectangle)
        assert isinstance(s, Shape)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 11: Exercise -- ComparableMixin & PrintableMixin ---
    print("--- Section 11: Exercise -- ComparableMixin & PrintableMixin ---")

    class ComparableMixin:
        """Adds comparison operators based on a _compare_key() method."""

        def _compare_key(self):
            raise NotImplementedError

        # TODO: implement __lt__, __le__, __gt__, __ge__, __eq__
        # Each should compare self._compare_key() with other._compare_key()
        # HINT: def __lt__(self, other): return self._compare_key() < other._compare_key()
        def __lt__(self, other):
            pass

        def __le__(self, other):
            pass

        def __gt__(self, other):
            pass

        def __ge__(self, other):
            pass

        def __eq__(self, other):
            # HINT: check isinstance first, return NotImplemented if wrong type
            pass

    class PrintableMixin:
        """Adds pretty __str__ using public attributes."""

        def __str__(self):
            # TODO: build string like "ClassName(attr1=val1, attr2=val2)"
            # HINT: use self.__dict__.items(), skip underscore-prefixed keys
            pass

    class SortableProduct(ComparableMixin, PrintableMixin):
        def __init__(self, name: str, price: float):
            self.name = name
            self.price = price

        def _compare_key(self):
            return self.price

    try:
        p1 = SortableProduct("Widget", 9.99)
        p2 = SortableProduct("Gadget", 24.99)
        p3 = SortableProduct("Doohickey", 9.99)

        print(f"  p1 < p2: {p1 < p2}")
        assert p1 < p2
        print(f"  p2 > p1: {p2 > p1}")
        assert p2 > p1
        print(f"  p1 == p3: {p1 == p3}")
        assert p1 == p3  # Same price
        print(f"  p1 <= p3: {p1 <= p3}")
        assert p1 <= p3
        print(f"  p2 >= p1: {p2 >= p1}")
        assert p2 >= p1

        print(f"  str(p1): {p1}")
        assert str(p1) == "SortableProduct(name='Widget', price=9.99)"
        print(f"  str(p2): {p2}")
        assert str(p2) == "SortableProduct(name='Gadget', price=24.99)"

        # Sorting works because __lt__ is defined
        products = [p2, p1, p3]
        sorted_products = sorted(products)
        print(f"  Sorted: {[str(p) for p in sorted_products]}")
        assert sorted_products[0].name in ("Widget", "Doohickey")
        assert sorted_products[-1].name == "Gadget"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Classes & inheritance in Python:")
    print("  - Animal hierarchy: base class + subclasses with super().__init__")
    print("  - MRO: C3 linearization determines method lookup order")
    print("  - Diamond problem: super() follows MRO, calling each __init__ once")
    print("  - super() is instance-aware: dispatches to next in MRO, not parent")
    print("  - Cooperative **kwargs: pass unrecognized args up the chain")
    print("  - SerializableMixin: to_dict, to_json, from_dict")
    print("  - LoggableMixin: per-class log via __init_subclass__")
    print("  - __init_subclass__: auto-register plugins on subclass creation")
    print("  - Notifier system: combines inheritance, mixins, and plugin pattern")
    print("  - Shape hierarchy: area/perimeter with super() in Square")
    print("  - ComparableMixin + PrintableMixin: composable behaviors")
    print()
    print("All 11 sections passed. You've mastered classes & inheritance!")
