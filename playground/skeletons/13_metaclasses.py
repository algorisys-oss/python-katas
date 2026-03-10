"""
Kata 13 -- Metaclasses & __init_subclass__
Run: python playground/skeletons/13_metaclasses.py

Master how Python creates classes: type() as metaclass, custom metaclasses with
__new__/__init__, __prepare__, __init_subclass__, registry patterns, class decorators,
and when to choose each approach.
"""

import time
from collections import OrderedDict


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: type() as metaclass ---
    print("--- Section 1: type() as Metaclass ---")

    # Normal class
    class Dog:
        sound = "woof"
        def speak(self):
            return self.sound

    # TODO: create the same class using type()
    # HINT: Dog2 = type("Dog2", (), {"sound": "woof", "speak": <function>})
    def speak(self):
        return self.sound

    Dog2 = None  # replace this with type() call

    try:
        d1 = Dog()
        d2 = Dog2()
        print(f"  Dog().speak() = {d1.speak()!r}")
        assert d1.speak() == "woof"
        print(f"  Dog2().speak() = {d2.speak()!r}")
        assert d2.speak() == "woof"

        # Every class is an instance of type
        print(f"  type(Dog) = {type(Dog)}")
        assert type(Dog) is type
        print(f"  type(Dog2) = {type(Dog2)}")
        assert type(Dog2) is type
        print(f"  type(type) = {type(type)}")
        assert type(type) is type

        # TODO: create a Cat class dynamically with type()
        # It should have sound="meow", speak method, and __repr__
        # HINT: Cat = type("Cat", (), {"sound": "meow", "speak": speak, "__repr__": lambda self: ...})
        Cat = None  # replace this

        c = Cat()
        print(f"  Cat().speak() = {c.speak()!r}")
        assert c.speak() == "meow"
        print(f"  repr(Cat()) = {c!r}")
        assert repr(c) == "Cat(sound='meow')"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Custom metaclass -- RegistryMeta ---
    print("--- Section 2: RegistryMeta ---")

    class RegistryMeta(type):
        """Metaclass that auto-registers all subclasses into a registry dict."""
        _registry: dict[str, type] = {}

        def __new__(mcs, name, bases, namespace):
            # TODO: create the class using super().__new__
            # Then register it in _registry if it has bases (skip the base class)
            # HINT: cls = super().__new__(mcs, name, bases, namespace)
            # HINT: if bases: RegistryMeta._registry[name] = cls
            pass

    try:
        class Serializer(metaclass=RegistryMeta):
            """Base class -- subclasses are auto-registered."""
            def serialize(self, data):
                raise NotImplementedError

        class JSONSerializer(Serializer):
            def serialize(self, data):
                return f"JSON: {data}"

        class XMLSerializer(Serializer):
            def serialize(self, data):
                return f"XML: {data}"

        class YAMLSerializer(Serializer):
            def serialize(self, data):
                return f"YAML: {data}"

        print(f"  Registry keys: {list(RegistryMeta._registry.keys())}")
        assert "JSONSerializer" in RegistryMeta._registry
        assert "XMLSerializer" in RegistryMeta._registry
        assert "YAMLSerializer" in RegistryMeta._registry
        assert "Serializer" not in RegistryMeta._registry

        # Factory function using the registry
        def get_serializer(name):
            cls = RegistryMeta._registry[name]
            return cls()

        s = get_serializer("JSONSerializer")
        result = s.serialize({"key": "value"})
        print(f"  JSONSerializer.serialize(...) = {result!r}")
        assert result == "JSON: {'key': 'value'}"

        s = get_serializer("XMLSerializer")
        result = s.serialize("<data/>")
        print(f"  XMLSerializer.serialize(...) = {result!r}")
        assert result == "XML: <data/>"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: ValidatedMeta -- enforcing class constraints ---
    print("--- Section 3: ValidatedMeta ---")

    class ValidatedMeta(type):
        """Metaclass that enforces rules on class definitions."""

        def __new__(mcs, name, bases, namespace):
            # TODO: skip validation for the base class (when bases is empty)
            # For subclasses:
            #   1. Check that 'validate' is in namespace, raise TypeError if not
            #   2. Collect __annotations__ and store as namespace["_fields"]
            # Finally: create and return the class with super().__new__
            # HINT: if bases: check namespace for 'validate' and '__annotations__'
            pass

    try:
        class ValidatedModel(metaclass=ValidatedMeta):
            """Base for models that are validated at class-creation time."""
            _fields: dict = {}

            def __init__(self, **kwargs):
                for field_name, field_type in self._fields.items():
                    if field_name not in kwargs:
                        raise ValueError(f"Missing required field: {field_name!r}")
                    value = kwargs[field_name]
                    if not isinstance(value, field_type):
                        raise TypeError(
                            f"Field {field_name!r} expected {field_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
                    setattr(self, field_name, value)
                self.validate()

            def validate(self):
                pass

        class User(ValidatedModel):
            name: str
            age: int

            def validate(self):
                if self.age < 0:
                    raise ValueError("Age cannot be negative")

        u = User(name="Alice", age=30)
        print(f"  User: {u.name}, age {u.age}")
        assert u.name == "Alice"
        assert u.age == 30
        print(f"  User._fields = {User._fields}")
        assert User._fields == {"name": str, "age": int}

        # Test type checking
        try:
            User(name="Bob", age="thirty")
        except TypeError as e:
            print(f"  Type error caught: {e}")
            assert "expected int" in str(e)

        # Test missing field
        try:
            User(name="Charlie")
        except ValueError as e:
            print(f"  Missing field caught: {e}")
            assert "age" in str(e)

        # Test custom validation
        try:
            User(name="Dave", age=-5)
        except ValueError as e:
            print(f"  Validation error caught: {e}")
            assert "negative" in str(e)

        # Test that class without validate() is rejected
        try:
            class BadModel(ValidatedModel):
                name: str
                # No validate method!
        except TypeError as e:
            print(f"  Missing validate caught: {e}")
            assert "must define" in str(e)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: __prepare__ -- custom namespace ---
    print("--- Section 4: __prepare__ ---")

    class OrderedMeta(type):
        @classmethod
        def __prepare__(mcs, name, bases):
            # TODO: return an OrderedDict instead of a regular dict
            # HINT: return OrderedDict()
            pass

        def __new__(mcs, name, bases, namespace):
            # TODO: create the class, then set cls._field_order to the list of
            # non-private, non-callable keys from namespace
            # HINT: cls._field_order = [k for k in namespace if not k.startswith("_") and not callable(namespace[k])]
            pass

    try:
        class Schema(metaclass=OrderedMeta):
            first_name = "str"
            last_name = "str"
            email = "str"
            age = "int"

        print(f"  Schema._field_order = {Schema._field_order}")
        assert Schema._field_order == ["first_name", "last_name", "email", "age"]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: __init_subclass__ -- plugin system ---
    print("--- Section 5: __init_subclass__ Plugin System ---")

    class Plugin:
        """Base class with automatic subclass registration."""
        _plugins: dict[str, type] = {}

        def __init_subclass__(cls, *, plugin_name: str = "", **kwargs):
            # TODO: register the subclass in Plugin._plugins
            # Use plugin_name if provided, otherwise use cls.__name__
            # Don't forget to call super().__init_subclass__(**kwargs)
            # HINT: name = plugin_name or cls.__name__; Plugin._plugins[name] = cls
            pass

        @classmethod
        def create(cls, name, *args, **kwargs):
            """Factory: create a plugin by registered name."""
            plugin_cls = cls._plugins[name]
            return plugin_cls(*args, **kwargs)

    class AudioPlugin(Plugin, plugin_name="audio"):
        def process(self):
            return "Processing audio..."

    class VideoPlugin(Plugin, plugin_name="video"):
        def process(self):
            return "Processing video..."

    class ImagePlugin(Plugin):  # Uses class name as default
        def process(self):
            return "Processing image..."

    try:
        print(f"  Plugin._plugins keys: {list(Plugin._plugins.keys())}")
        assert "audio" in Plugin._plugins
        assert "video" in Plugin._plugins
        assert "ImagePlugin" in Plugin._plugins

        p = Plugin.create("audio")
        result = p.process()
        print(f"  Plugin.create('audio').process() = {result!r}")
        assert result == "Processing audio..."

        p = Plugin.create("video")
        result = p.process()
        print(f"  Plugin.create('video').process() = {result!r}")
        assert result == "Processing video..."

        p = Plugin.create("ImagePlugin")
        result = p.process()
        print(f"  Plugin.create('ImagePlugin').process() = {result!r}")
        assert result == "Processing image..."
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: __init_subclass__ for field validation ---
    print("--- Section 6: __init_subclass__ Field Validation ---")

    class Configurable:
        """Base that requires subclasses to declare certain attributes."""

        required_fields: list[str] = []

        def __init_subclass__(cls, *, required: list[str] | None = None, **kwargs):
            # TODO: call super().__init_subclass__(**kwargs)
            # If required is not None, set cls.required_fields = required
            # Then validate that each required field has a type annotation
            # HINT: annotations = getattr(cls, "__annotations__", {})
            # HINT: raise TypeError if a required field is not in annotations
            pass

    try:
        class DatabaseConfig(Configurable, required=["host", "port", "dbname"]):
            host: str
            port: int
            dbname: str

        print(f"  DatabaseConfig.required_fields = {DatabaseConfig.required_fields}")
        assert DatabaseConfig.required_fields == ["host", "port", "dbname"]
        print(f"  DatabaseConfig.__annotations__ = {DatabaseConfig.__annotations__}")
        assert "host" in DatabaseConfig.__annotations__
        assert "port" in DatabaseConfig.__annotations__
        assert "dbname" in DatabaseConfig.__annotations__

        # Test that missing annotation raises TypeError
        try:
            class BadConfig(Configurable, required=["host"]):
                pass  # No host annotation!
        except TypeError as e:
            print(f"  Missing annotation caught: {e}")
            assert "must annotate" in str(e)
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Class decorators ---
    print("--- Section 7: Class Decorators ---")

    def add_repr(cls):
        """Decorator that auto-generates __repr__ from annotations."""
        # TODO: get the list of annotated fields from cls.__annotations__
        # Define a __repr__ method that shows cls.__name__(field1=val1, field2=val2)
        # Assign it to cls.__repr__ and return cls
        # HINT: fields = list(cls.__annotations__)
        # HINT: parts = ", ".join(f"{f}={getattr(self, f)!r}" for f in fields)
        pass

    def frozen(cls):
        """Decorator that makes instances immutable after __init__."""
        # TODO: wrap __init__ to set _frozen=False before, _frozen=True after
        # Override __setattr__ to raise AttributeError when _frozen is True
        # HINT: use object.__setattr__(self, "_frozen", False/True)
        # HINT: original_init = cls.__init__
        pass

    try:
        @add_repr
        @frozen
        class Point:
            x: float
            y: float

            def __init__(self, x, y):
                self.x = x
                self.y = y

        p = Point(1.0, 2.0)
        print(f"  Point(1.0, 2.0) = {p!r}")
        assert repr(p) == "Point(x=1.0, y=2.0)"

        # Test frozen behavior
        try:
            p.x = 99
        except AttributeError as e:
            print(f"  Frozen: {e}")
            assert "Cannot modify" in str(e)

        # Decorators compose -- both add_repr and frozen work together
        @add_repr
        class MutablePoint:
            x: float
            y: float

            def __init__(self, x, y):
                self.x = x
                self.y = y

        mp = MutablePoint(3.0, 4.0)
        print(f"  MutablePoint(3.0, 4.0) = {mp!r}")
        assert repr(mp) == "MutablePoint(x=3.0, y=4.0)"
        mp.x = 5.0  # Mutable -- no frozen decorator
        print(f"  After mp.x = 5.0: {mp!r}")
        assert mp.x == 5.0
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: Exercise -- Singleton metaclass ---
    print("--- Section 8: Exercise -- Singleton Metaclass ---")

    class SingletonMeta(type):
        """Metaclass that ensures only one instance per class."""
        _instances: dict[type, object] = {}

        def __call__(cls, *args, **kwargs):
            # TODO: check if cls is already in _instances
            # If not, create a new instance with super().__call__(*args, **kwargs)
            # Return the cached instance
            # HINT: if cls not in SingletonMeta._instances: ...
            pass

    try:
        class Database(metaclass=SingletonMeta):
            def __init__(self, url="sqlite://"):
                self.url = url

        db1 = Database("postgres://localhost")
        db2 = Database("mysql://localhost")
        print(f"  db1 is db2: {db1 is db2}")
        assert db1 is db2
        print(f"  db1.url = {db1.url!r}")
        assert db1.url == "postgres://localhost"

        class Cache(metaclass=SingletonMeta):
            def __init__(self):
                self.data = {}

        c1 = Cache()
        c2 = Cache()
        assert c1 is c2
        c1.data["key"] = "value"
        print(f"  c2.data = {c2.data}")
        assert c2.data == {"key": "value"}
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 9: Exercise -- AutoEnum with __init_subclass__ ---
    print("--- Section 9: Exercise -- AutoEnum ---")

    class AutoEnum:
        """Simple enum system using __init_subclass__."""
        def __init_subclass__(cls, **kwargs):
            # TODO: call super().__init_subclass__(**kwargs)
            # Collect all non-private string attributes into cls._members dict
            # HINT: for key, value in vars(cls).items():
            # HINT:     if not key.startswith("_") and isinstance(value, str): ...
            pass

    try:
        class Color(AutoEnum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        print(f"  Color._members = {Color._members}")
        assert Color._members == {"RED": "red", "GREEN": "green", "BLUE": "blue"}
        print(f"  Color.RED = {Color.RED!r}")
        assert Color.RED == "red"

        class Status(AutoEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"
            PENDING = "pending"

        print(f"  Status._members = {Status._members}")
        assert Status._members == {
            "ACTIVE": "active", "INACTIVE": "inactive", "PENDING": "pending"
        }
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 10: Exercise -- Method timing decorator ---
    print("--- Section 10: Exercise -- Method Timing Decorator ---")

    def timed_methods(cls):
        """Wrap all public methods with timing output."""
        # TODO: iterate over vars(cls).items()
        # For each callable that doesn't start with "_", wrap it with timing
        # HINT: use a factory function to avoid late-binding issues!
        # HINT: def make_timed(fn): def timed(*a, **kw): ... return timed
        # HINT: setattr(cls, name, make_timed(method))
        pass

    try:
        @timed_methods
        class Calculator:
            def add(self, a, b):
                return a + b

            def slow_multiply(self, a, b):
                time.sleep(0.01)
                return a * b

        calc = Calculator()
        result = calc.add(2, 3)
        print(f"  calc.add(2, 3) = {result}")
        assert result == 5

        result = calc.slow_multiply(4, 5)
        print(f"  calc.slow_multiply(4, 5) = {result}")
        assert result == 20
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Metaclasses & __init_subclass__ in Python:")
    print("  - type() is the default metaclass; creates classes at runtime")
    print("  - Custom metaclass __new__: intercept class creation")
    print("  - Custom metaclass __init__: post-process class")
    print("  - RegistryMeta: auto-register subclasses by name")
    print("  - ValidatedMeta: enforce rules on class definitions")
    print("  - __prepare__: custom namespace for class body")
    print("  - __init_subclass__: simpler hook for subclass registration/validation")
    print("  - Class decorators: composable post-creation transforms")
    print("  - Prefer __init_subclass__ and decorators over metaclasses in most cases")
    print()
    print("All 10 sections passed. You've mastered metaclasses & __init_subclass__!")
