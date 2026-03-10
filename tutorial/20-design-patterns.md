# Kata 20 -- Design Patterns in Python

[prev: 19-dependency-inversion](./19-dependency-inversion.md) | [next: 21-threading-basics](./21-threading-basics.md)

---

## What We're Building

Classic design patterns -- Factory, Strategy, Observer, Singleton, Template Method, Command -- reimagined for Python. Many patterns that require elaborate class hierarchies in Java or C++ collapse into a few lines of Python thanks to first-class functions, duck typing, and built-in protocols. In this kata we'll show the "traditional OOP way" alongside the **Pythonic way** for each pattern, so you can see exactly how much ceremony Python eliminates.

We'll skip Iterator and Decorator because you've already mastered them:
- **Iterator:** Kata 02 covered `__iter__`/`__next__`, generators, and `itertools`
- **Decorator:** Kata 03 covered function decorators, `functools.wraps`, and decorator factories

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Factory pattern | Creates objects without exposing construction logic | When object creation depends on runtime data |
| Strategy pattern | Swaps algorithms at runtime | When behavior should be pluggable |
| Observer pattern | Notifies subscribers when state changes | Event systems, UI updates, logging hooks |
| Singleton pattern | Ensures exactly one instance exists | Config, connection pools, registries |
| Template Method pattern | Defines skeleton algorithm, lets subclasses fill in steps | Frameworks, pipelines with customizable steps |
| Command pattern | Encapsulates actions as objects | Undo/redo, task queues, macro recording |
| First-class functions | Functions as objects you can pass, store, return | Replacing interface classes in Python |
| `weakref` | References that don't prevent garbage collection | Observer callbacks without memory leaks |

## The Code

### Pattern 1: Factory

The Factory pattern creates objects without the caller needing to know the exact class. In Java, this means an abstract `Creator` class with a `createProduct()` method and concrete subclass overrides. In Python, **a function is enough**.

**The Java way (in Python syntax):**

```python
from abc import ABC, abstractmethod

class Serializer(ABC):
    @abstractmethod
    def serialize(self, data: dict) -> str: ...

class JsonSerializer(Serializer):
    def serialize(self, data: dict) -> str:
        import json
        return json.dumps(data)

class XmlSerializer(Serializer):
    def serialize(self, data: dict) -> str:
        return "<data>" + "".join(f"<{k}>{v}</{k}>" for k, v in data.items()) + "</data>"

class CsvSerializer(Serializer):
    def serialize(self, data: dict) -> str:
        return ",".join(data.keys()) + "\n" + ",".join(str(v) for v in data.values())

# Factory class -- Java-style
class SerializerFactory:
    _serializers = {
        "json": JsonSerializer,
        "xml": XmlSerializer,
        "csv": CsvSerializer,
    }

    @classmethod
    def create(cls, fmt: str) -> Serializer:
        if fmt not in cls._serializers:
            raise ValueError(f"Unknown format: {fmt}")
        return cls._serializers[fmt]()
```

That's 30+ lines for a simple registry. Here's the Pythonic version:

**The Pythonic way -- a function with a dict:**

```python
import json

def create_serializer(fmt: str):
    """Factory function -- no base class needed."""
    serializers = {
        "json": lambda data: json.dumps(data),
        "xml": lambda data: "<data>" + "".join(
            f"<{k}>{v}</{k}>" for k, v in data.items()
        ) + "</data>",
        "csv": lambda data: (
            ",".join(data.keys()) + "\n" + ",".join(str(v) for v in data.values())
        ),
    }
    if fmt not in serializers:
        raise ValueError(f"Unknown format: {fmt}")
    return serializers[fmt]
```

Even simpler: if the factory just maps strings to callables, a plain dict *is* the factory. No class needed.

### Pattern 2: Strategy

The Strategy pattern lets you swap algorithms at runtime. In Java, you define a `Strategy` interface, write concrete implementations, and inject them. In Python, **any callable is a strategy**.

**The Java way (in Python syntax):**

```python
from abc import ABC, abstractmethod

class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, price: float) -> float: ...

class NoDiscount(DiscountStrategy):
    def calculate(self, price: float) -> float:
        return price

class PercentageDiscount(DiscountStrategy):
    def __init__(self, percent: float):
        self.percent = percent
    def calculate(self, price: float) -> float:
        return price * (1 - self.percent / 100)

class FixedDiscount(DiscountStrategy):
    def __init__(self, amount: float):
        self.amount = amount
    def calculate(self, price: float) -> float:
        return max(0, price - self.amount)

class Order:
    def __init__(self, price: float, strategy: DiscountStrategy):
        self.price = price
        self.strategy = strategy

    def total(self) -> float:
        return self.strategy.calculate(self.price)
```

**The Pythonic way -- just pass a function:**

```python
from typing import Callable

def no_discount(price: float) -> float:
    return price

def percentage_discount(percent: float) -> Callable[[float], float]:
    """Returns a strategy function (closure)."""
    def apply(price: float) -> float:
        return price * (1 - percent / 100)
    return apply

def fixed_discount(amount: float) -> Callable[[float], float]:
    """Returns a strategy function (closure)."""
    def apply(price: float) -> float:
        return max(0, price - amount)
    return apply

class Order:
    def __init__(self, price: float, discount: Callable[[float], float] = no_discount):
        self.price = price
        self.discount = discount

    def total(self) -> float:
        return self.discount(self.price)
```

No base class. No interface. Closures capture parameters naturally. You can even use a `lambda`:

```python
order = Order(100.0, discount=lambda p: p * 0.85)  # 15% off
```

### Pattern 3: Observer

The Observer pattern lets objects subscribe to events and get notified when something happens. The key Pythonic improvement: use **weak references** so observers can be garbage-collected without the subject holding them alive.

```python
import weakref
from typing import Callable, Any

class EventEmitter:
    """Pythonic Observer using callbacks and weak references."""

    def __init__(self):
        self._listeners: dict[str, list] = {}

    def on(self, event: str, callback: Callable):
        """Subscribe a callback to an event."""
        self._listeners.setdefault(event, [])
        # Store a weak reference if it's a bound method
        if hasattr(callback, "__self__"):
            ref = weakref.WeakMethod(callback, self._make_cleanup(event))
            self._listeners[event].append(ref)
        else:
            self._listeners[event].append(callback)

    def _make_cleanup(self, event: str):
        """Create a weak reference finalizer that removes dead refs."""
        def cleanup(ref):
            if event in self._listeners:
                self._listeners[event] = [
                    r for r in self._listeners[event] if r is not ref
                ]
        return cleanup

    def emit(self, event: str, *args: Any, **kwargs: Any):
        """Notify all listeners for an event."""
        for listener in list(self._listeners.get(event, [])):
            if isinstance(listener, weakref.ref):
                callback = listener()
                if callback is not None:
                    callback(*args, **kwargs)
            else:
                listener(*args, **kwargs)

    def off(self, event: str, callback: Callable):
        """Unsubscribe a callback from an event."""
        if event not in self._listeners:
            return
        self._listeners[event] = [
            cb for cb in self._listeners[event]
            if (isinstance(cb, weakref.ref) and cb() is not callback)
            or (not isinstance(cb, weakref.ref) and cb is not callback)
        ]
```

Why weak references matter: without them, the emitter keeps observers alive forever, causing memory leaks. With `WeakMethod`, when an observer object is deleted, its callback is automatically cleaned up.

### Pattern 4: Singleton

The Singleton pattern ensures only one instance of a class exists. In Java, this involves private constructors, double-checked locking, and synchronization. Python offers simpler approaches.

**Approach 1: Module-level instance (simplest, most Pythonic)**

```python
# config.py
class _Config:
    def __init__(self):
        self.debug = False
        self.database_url = "sqlite:///app.db"

config = _Config()  # THE singleton -- import it, don't instantiate

# usage: from config import config
```

This works because Python modules are only imported once -- the module itself is the singleton mechanism.

**Approach 2: `__new__` override (when you need class-level guarantees)**

```python
class Singleton:
    """Singleton using __new__ -- only one instance ever created."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # __init__ is called every time, so guard against re-init
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.settings: dict = {}
```

**Approach 3: `__init_subclass__` hook (metaclass-free)**

```python
class SingletonMeta(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
```

The module-level approach is almost always the right choice in Python. Reserve `__new__` for cases where you need to enforce single-instance at the class level (e.g., frameworks where users subclass your base).

### Pattern 5: Template Method

The Template Method defines the skeleton of an algorithm in a base class, letting subclasses override specific steps without changing the overall structure.

**The Java way (abstract base class):**

```python
from abc import ABC, abstractmethod

class DataPipeline(ABC):
    """Template Method: run() is the skeleton, steps are customizable."""

    def run(self, raw_data: str) -> str:
        data = self.extract(raw_data)
        data = self.transform(data)
        result = self.load(data)
        return result

    @abstractmethod
    def extract(self, raw_data: str) -> list: ...

    @abstractmethod
    def transform(self, data: list) -> list: ...

    @abstractmethod
    def load(self, data: list) -> str: ...
```

This pattern is actually still useful in Python -- the ABC version is fine. But we can also use **callable hooks** for lighter-weight cases:

**The Pythonic way -- inject step functions:**

```python
from typing import Callable

class DataPipeline:
    """Template Method using injectable hooks."""

    def __init__(
        self,
        extract: Callable[[str], list],
        transform: Callable[[list], list],
        load: Callable[[list], str],
    ):
        self._extract = extract
        self._transform = transform
        self._load = load

    def run(self, raw_data: str) -> str:
        data = self._extract(raw_data)
        data = self._transform(data)
        return self._load(data)
```

Both approaches are valid. Use ABC when steps are complex and benefit from being full classes. Use injectable functions when steps are simple and you want maximum flexibility.

### Pattern 6: Command

The Command pattern encapsulates an action as an object, enabling undo/redo, queuing, and macro recording.

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Command:
    """A command captures an action that can be executed and undone."""
    execute: Callable
    undo: Callable
    description: str = ""

class TextEditor:
    """Editor with undo/redo using the Command pattern."""

    def __init__(self):
        self.content: str = ""
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []

    def _do(self, command: Command):
        command.execute()
        self._history.append(command)
        self._redo_stack.clear()  # New action invalidates redo

    def insert(self, text: str, position: int | None = None):
        pos = position if position is not None else len(self.content)
        old_content = self.content

        def execute():
            self.content = old_content[:pos] + text + old_content[pos:]

        def undo():
            self.content = old_content

        self._do(Command(execute, undo, f"insert '{text}' at {pos}"))

    def delete(self, start: int, end: int):
        old_content = self.content
        deleted = self.content[start:end]

        def execute():
            self.content = old_content[:start] + old_content[end:]

        def undo():
            self.content = old_content

        self._do(Command(execute, undo, f"delete '{deleted}' [{start}:{end}]"))

    def undo(self) -> bool:
        if not self._history:
            return False
        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)
        return True
```

Notice that `Command` is a dataclass with two callables -- no need for a `Command` interface with concrete subclass per action. Closures capture all the state needed for execute and undo.

## Playground

Run the full demonstration with all patterns:

```bash
python playground/20_design_patterns.py
```

```
--- Section 1: Factory Pattern ---
  JSON-style factory:
    create_serializer("json"): {"name": "Alice", "age": 30}
    create_serializer("xml"):  <data><name>Alice</name><age>30</age></data>
    create_serializer("csv"):  name,age\nAlice,30
  Factory with registration:
    Registered format 'yaml' dynamically
    create_serializer("yaml"): name: Alice\nage: 30
  Factory pattern -- no base class, no abstract methods, just functions.

--- Section 2: Strategy Pattern ---
  No discount:  Order(100.00) = 100.00
  20% off:      Order(100.00) = 80.00
  Fixed $15 off: Order(100.00) = 85.00
  Lambda 10% off: Order(100.00) = 90.00
  Strategy swapped at runtime:
    Before swap: 80.00
    After swap:  85.00
  Strategy pattern -- callables replace interface hierarchies.

--- Section 3: Observer Pattern ---
  Emitting 'user_login' event...
    [login_handler] User logged in: alice
    [audit_handler] AUDIT: user_login -- alice
  Emitting 'order_placed' event...
    [order_handler] Order placed: order-42 by alice
  Weak reference cleanup:
    Listeners before delete: 1
    Listeners after delete: 0
  Observer pattern -- EventEmitter with weak reference support.

--- Section 4: Singleton Pattern ---
  Module-level singleton:
    config1 is config2: True
    Setting persists across imports: True
  __new__ singleton:
    s1 is s2: True
    s1.settings is s2.settings: True
    State shared: True
  Singleton pattern -- module-level is preferred in Python.

--- Section 5: Template Method Pattern ---
  Pipeline 1 (CSV -> uppercase -> count):
    Input:  'alice,30\nbob,25\ncharlie,35'
    Output: 'Processed 3 records: ALICE, BOB, CHARLIE'
  Pipeline 2 (JSON -> filter -> summary):
    Input:  '[{"name": "A", "score": 85}, {"name": "B", "score": 42}]'
    Output: 'High scorers: A'
  Template Method -- ABC version and function-injection version both work.

--- Section 6: Command Pattern (Undo/Redo) ---
  insert 'Hello': content='Hello'
  insert ' World': content='Hello World'
  insert '!': content='Hello World!'
  undo: content='Hello World'
  undo: content='Hello'
  redo: content='Hello World'
  delete [5:11]: content='Hello'
  undo delete: content='Hello World'
  Command history: 2 commands
  Command pattern -- closures capture state for undo/redo.

--- Summary ---
Design Patterns in Python:
  - Factory: dict of callables replaces abstract factory class
  - Strategy: pass functions, not interface implementors
  - Observer: EventEmitter with weak references for cleanup
  - Singleton: module-level instance (preferred) or __new__
  - Template Method: ABC or injectable function hooks
  - Command: dataclass with execute/undo callables
  - Iterator: see Kata 02 (generators, __iter__/__next__)
  - Decorator: see Kata 03 (functools.wraps, decorator factories)

All 6 sections passed. You've mastered Pythonic design patterns!
```

## How It Works

```
JAVA/C++ WAY:                         PYTHONIC WAY:

  Interface                             Callable (function/lambda)
    |                                     |
  ConcreteImpl1                         closure or plain function
  ConcreteImpl2                         (no class hierarchy needed)
  ConcreteImpl3

  AbstractFactory                       dict[str, Callable]
    |                                     |
  ConcreteFactory                       factory_function(key)

  Subject ─── Observer interface        EventEmitter ─── callbacks
    |              |                      |              |
  ConcreteSubj  ConcreteObs1            emitter.on()   any callable
                ConcreteObs2            emitter.emit()  weakref cleanup
```

The pattern is consistent: **Python's first-class functions eliminate the need for single-method interfaces**. When a pattern exists solely to pass behavior around, a callable replaces the entire class hierarchy.

When the pattern involves *state and multiple methods* (like Command with execute + undo, or Template Method with multiple steps), classes are still the right tool -- but Python's dataclasses and closures keep them lightweight.

## Exercises

### Exercise 1: Plugin registry with decorators

Build a `@register` decorator that auto-registers factory functions:

```python
_registry: dict[str, Callable] = {}

def register(name: str):
    """Decorator that registers a factory function."""
    ...

@register("markdown")
def markdown_serializer(data: dict) -> str:
    ...

@register("toml")
def toml_serializer(data: dict) -> str:
    ...

# Usage: _registry["markdown"]({"key": "value"})
```

### Exercise 2: Observable property

Combine the Observer and Descriptor patterns (from Kata 12) to create a property that emits events on change:

```python
class ObservableProperty:
    """Descriptor that emits 'changed' events when set."""

    def __init__(self, name: str):
        self.name = name
        self._listeners: list[Callable] = []

    def on_change(self, callback: Callable): ...
    def __set_name__(self, owner, name): ...
    def __get__(self, obj, objtype=None): ...
    def __set__(self, obj, value): ...

class User:
    name = ObservableProperty("name")
    email = ObservableProperty("email")
```

### Exercise 3: Macro recorder

Extend the Command pattern's `TextEditor` to support macros -- record a sequence of commands and replay them:

```python
class TextEditor:
    ...
    def start_recording(self): ...
    def stop_recording(self) -> list[Command]: ...
    def replay(self, macro: list[Command]): ...

# Usage:
editor.start_recording()
editor.insert("Hello")
editor.insert(" World")
macro = editor.stop_recording()

editor.content = ""  # Reset
editor.replay(macro)  # Replays: insert "Hello", insert " World"
assert editor.content == "Hello World"
```

## What's Next

In [Kata 21 -- Threading Basics](./21-threading-basics.md), we'll move from object design to concurrency. You'll learn how to run code in parallel with threads, protect shared state with locks, and understand why Python's GIL makes threading different from other languages.

---

[prev: 19-dependency-inversion](./19-dependency-inversion.md) | [next: 21-threading-basics](./21-threading-basics.md)
