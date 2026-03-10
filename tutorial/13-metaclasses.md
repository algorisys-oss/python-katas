# Kata 13 -- Metaclasses & `__init_subclass__`

[prev: 12-properties-descriptors](./12-properties-descriptors.md) | [next: 14-abstract-base-classes](./14-abstract-base-classes.md)

---

## What We're Building

Every class in Python is itself an **object** -- an instance of its **metaclass**. By default that metaclass is `type`. Understanding this mechanism unlocks the ability to customize class creation itself: auto-registering subclasses, enforcing constraints on class bodies, injecting methods, and building plugin systems.

In this kata we'll trace exactly how Python creates classes, build custom metaclasses with `__new__` and `__init__`, discover `__prepare__` for controlling the class namespace, and then learn why `__init_subclass__` (introduced in Python 3.6) and class decorators are almost always the better choice. By the end you'll know when metaclasses are warranted -- and when they're overkill.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `type()` | The default metaclass; creates classes at runtime | Dynamic class creation, understanding the machinery |
| Custom metaclass (`__new__`) | Intercept and modify class creation | Registry patterns, ORM field collection, validation |
| Custom metaclass (`__init__`) | Post-process a class after creation | Adding methods, wrapping attributes |
| `__prepare__` | Supply a custom namespace dict for the class body | Ordered attribute collection, DSLs |
| `__init_subclass__` | Hook called on the **parent** when subclassed | Plugin registration, field validation (simpler than metaclass) |
| Class decorators | Transform a class after creation | Adding/wrapping behavior without metaclass complexity |
| Registry pattern | Auto-collect subclasses by name | Plugin systems, serialization, factory dispatch |

## The Code

### Step 1: How classes are created -- `type()` as metaclass

When you write `class Foo: ...`, Python calls `type('Foo', bases, namespace)` behind the scenes. `type` is both a function (returns an object's type) and the default metaclass (creates new classes).

```python
# These two are equivalent:

# 1. Normal class statement
class Dog:
    sound = "woof"
    def speak(self):
        return self.sound

# 2. Creating the same class with type()
def speak(self):
    return self.sound

Dog2 = type("Dog2", (), {"sound": "woof", "speak": speak})

d = Dog2()
print(d.speak())  # woof
print(type(Dog2))  # <class 'type'>
print(type(Dog))   # <class 'type'>
```

Every class is an instance of `type`. Even `type` itself:

```python
print(type(type))  # <class 'type'> -- type is its own metaclass
print(type(int))   # <class 'type'>
print(type(str))   # <class 'type'>
```

### Step 2: Custom metaclasses with `__new__` and `__init__`

A metaclass is a class whose instances are classes. By subclassing `type`, you can intercept class creation.

**`__new__`** is called to create the class object. This is where you can modify the class name, bases, or namespace before the class exists.

**`__init__`** is called after the class is created. Use it to post-process or register the class.

```python
class RegistryMeta(type):
    """Metaclass that auto-registers all subclasses into a registry dict."""
    _registry: dict[str, type] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # Don't register the base class itself
        if bases:
            RegistryMeta._registry[name] = cls
        return cls

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

print(RegistryMeta._registry)
# {'JSONSerializer': <class 'JSONSerializer'>, 'XMLSerializer': ..., 'YAMLSerializer': ...}

# Factory function using the registry
def get_serializer(name):
    cls = RegistryMeta._registry[name]
    return cls()

s = get_serializer("JSONSerializer")
print(s.serialize({"key": "value"}))  # JSON: {'key': 'value'}
```

### Step 3: ValidatedMeta -- enforcing class constraints

A metaclass can inspect the class body and reject invalid definitions at **class creation time**, not at instantiation time.

```python
class ValidatedMeta(type):
    """Metaclass that enforces rules on class definitions."""

    def __new__(mcs, name, bases, namespace):
        # Skip validation for the base class
        if bases:
            # Rule 1: must define a 'validate' method
            if "validate" not in namespace:
                raise TypeError(
                    f"Class {name!r} must define a 'validate' method"
                )

            # Rule 2: collect type-annotated fields and store them
            annotations = namespace.get("__annotations__", {})
            namespace["_fields"] = dict(annotations)

        cls = super().__new__(mcs, name, bases, namespace)
        return cls

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
print(f"{u.name}, age {u.age}")  # Alice, age 30
```

### Step 4: `__prepare__` -- controlling the class namespace

Before the class body executes, Python calls `metaclass.__prepare__(name, bases)` to get the namespace dict. By returning a custom mapping, you can track attribute definition order or implement DSL-like syntax.

```python
from collections import OrderedDict

class OrderedMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, dict(namespace))
        cls._field_order = [
            k for k in namespace
            if not k.startswith("_") and not callable(namespace[k])
        ]
        return cls

class Schema(metaclass=OrderedMeta):
    first_name = "str"
    last_name = "str"
    email = "str"
    age = "int"

print(Schema._field_order)
# ['first_name', 'last_name', 'email', 'age']
```

Note: since Python 3.7, regular `dict` preserves insertion order, so `__prepare__` is less commonly needed for ordering. It remains useful for custom namespace behavior (e.g., auto-numbering, duplicate detection).

### Step 5: `__init_subclass__` -- the simpler alternative

Python 3.6 introduced `__init_subclass__` as a hook on the **parent class** that fires whenever a new subclass is created. It covers most use cases that previously required a metaclass -- with far less complexity.

```python
class Plugin:
    """Base class with automatic subclass registration."""
    _plugins: dict[str, type] = {}

    def __init_subclass__(cls, *, plugin_name: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__
        Plugin._plugins[name] = cls

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

print(Plugin._plugins)
# {'audio': <class 'AudioPlugin'>, 'video': <class 'VideoPlugin'>, 'ImagePlugin': <class 'ImagePlugin'>}

p = Plugin.create("audio")
print(p.process())  # Processing audio...
```

### Step 6: `__init_subclass__` for field validation

`__init_subclass__` can also validate that subclasses define required attributes -- no metaclass needed.

```python
class Configurable:
    """Base that requires subclasses to declare certain attributes."""

    required_fields: list[str] = []

    def __init_subclass__(cls, *, required: list[str] | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if required is not None:
            cls.required_fields = required

        # Validate that required fields have type annotations
        annotations = getattr(cls, "__annotations__", {})
        for field in cls.required_fields:
            if field not in annotations:
                raise TypeError(
                    f"Class {cls.__name__!r} must annotate field {field!r}"
                )

class DatabaseConfig(Configurable, required=["host", "port", "dbname"]):
    host: str
    port: int
    dbname: str

print(f"DatabaseConfig fields: {DatabaseConfig.required_fields}")
# DatabaseConfig fields: ['host', 'port', 'dbname']
print(f"Annotations: {DatabaseConfig.__annotations__}")
# Annotations: {'host': <class 'str'>, 'port': <class 'int'>, 'dbname': <class 'str'>}

# This would fail at class-creation time:
# class BadConfig(Configurable, required=["host"]):
#     pass  # TypeError: Class 'BadConfig' must annotate field 'host'
```

### Step 7: Class decorators -- often the right tool

Before reaching for a metaclass, consider a class decorator. It receives the class after creation and can modify or replace it. Decorators compose easily and don't conflict with other metaclasses.

```python
def add_repr(cls):
    """Decorator that auto-generates __repr__ from annotations."""
    fields = list(cls.__annotations__)

    def __repr__(self):
        parts = ", ".join(f"{f}={getattr(self, f)!r}" for f in fields)
        return f"{cls.__name__}({parts})"

    cls.__repr__ = __repr__
    return cls

def frozen(cls):
    """Decorator that makes instances immutable after __init__."""
    original_init = cls.__init__

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "_frozen", False)
        original_init(self, *args, **kwargs)
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(f"Cannot modify frozen instance: {name!r}")
        object.__setattr__(self, name, value)

    cls.__init__ = __init__
    cls.__setattr__ = __setattr__
    return cls

@add_repr
@frozen
class Point:
    x: float
    y: float

    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1.0, 2.0)
print(p)  # Point(x=1.0, y=2.0)

try:
    p.x = 99
except AttributeError as e:
    print(f"Frozen: {e}")  # Cannot modify frozen instance: 'x'
```

### Step 8: When to use -- and when to avoid -- metaclasses

**Use metaclasses when:**
- You need to control class creation **before** the class object exists (e.g., modifying `__new__` arguments)
- You need `__prepare__` for a custom class namespace
- You need the metaclass to define methods that are callable on the **class itself** (not instances)
- You're building an ORM, validation framework, or DSL where the metaclass API is hidden from users

**Prefer `__init_subclass__` when:**
- You want to register subclasses or validate class definitions
- You want to pass parameters via `class MyClass(Base, key=value)`
- You want simpler code that doesn't require understanding metaclass mechanics

**Prefer class decorators when:**
- You want to add or modify methods/attributes after class creation
- You want composable transformations (stack multiple decorators)
- You don't need to intercept the class creation process itself

**Decision flowchart:**

```
Need to customize class creation?
├── No → Use a regular class or function
├── Yes → Can you do it after the class is created?
│   ├── Yes → Use a class decorator
│   └── No → Do you need to hook into subclassing?
│       ├── Yes → Use __init_subclass__
│       └── No → Do you need __prepare__ or metaclass-level methods?
│           ├── Yes → Use a metaclass
│           └── No → Use __init_subclass__ or a decorator
```

## Playground

Run the full interactive demo:

```bash
python playground/13_metaclasses.py
```

This script implements all patterns above -- RegistryMeta, ValidatedMeta, `__init_subclass__` plugins, class decorators -- with assertions at every step.

## How It Works

### Class creation sequence

```
1. Python encounters: class Foo(Base, metaclass=Meta): ...
2. Python calls Meta.__prepare__("Foo", (Base,)) → returns namespace dict
3. Python executes the class body in that namespace
4. Python calls Meta.__new__(Meta, "Foo", (Base,), namespace) → creates class object
5. Python calls Meta.__init__(cls, "Foo", (Base,), namespace) → initializes class
6. Python calls Base.__init_subclass__(cls) on each base that defines it
7. The class object is bound to the name "Foo" in the enclosing scope
```

### Metaclass resolution

When multiple bases have different metaclasses, Python finds the "most derived" metaclass. If no single metaclass is a subclass of all others, you get a `TypeError`:

```
class A(metaclass=Meta1): ...
class B(metaclass=Meta2): ...
class C(A, B): ...  # TypeError if Meta1 and Meta2 are unrelated
```

### `__init_subclass__` vs metaclass

| Feature | `__init_subclass__` | Metaclass |
|---|---|---|
| Complexity | Low | High |
| Keyword args | `class Sub(Base, key=val)` | Must override `__init_subclass__` anyway |
| Composability | Works with any metaclass | Can conflict with other metaclasses |
| `__prepare__` | No | Yes |
| Class-level methods | No | Yes |
| Typical use | Registration, validation | ORMs, DSLs, framework internals |

## Exercises

### Exercise 1: Singleton metaclass

Build a metaclass `SingletonMeta` that ensures only one instance of each class exists:

```python
class SingletonMeta(type):
    # Track instances per class
    ...

class Database(metaclass=SingletonMeta):
    def __init__(self, url="sqlite://"):
        self.url = url

db1 = Database("postgres://localhost")
db2 = Database("mysql://localhost")  # Returns same instance as db1
assert db1 is db2
print(db1.url)  # postgres://localhost
```

### Exercise 2: Enum-like class with `__init_subclass__`

Use `__init_subclass__` to build a simple enum system where class attributes become enum members:

```python
class AutoEnum:
    def __init_subclass__(cls, **kwargs):
        # Collect class-level string attributes as enum members
        # Store them in cls._members dict
        ...

class Color(AutoEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

print(Color._members)
# {'RED': 'red', 'GREEN': 'green', 'BLUE': 'blue'}
print(Color.RED)  # red
```

### Exercise 3: Method timing decorator (class decorator)

Write a class decorator that wraps all public methods with timing:

```python
import time

def timed_methods(cls):
    """Wrap all public methods with timing output."""
    ...

@timed_methods
class Calculator:
    def add(self, a, b):
        return a + b

    def slow_multiply(self, a, b):
        time.sleep(0.01)
        return a * b

c = Calculator()
c.add(2, 3)        # prints: add took 0.0000s
c.slow_multiply(2, 3)  # prints: slow_multiply took 0.01Xs
```

## What's Next

In [Kata 14 -- Abstract Base Classes](./14-abstract-base-classes.md), we'll explore Python's `abc` module -- `ABC`, `abstractmethod`, virtual subclasses with `register()`, and how ABCs interact with the metaclass system we just learned. You'll see how `ABCMeta` is itself a metaclass that enforces interface contracts.

---

[prev: 12-properties-descriptors](./12-properties-descriptors.md) | [next: 14-abstract-base-classes](./14-abstract-base-classes.md)
