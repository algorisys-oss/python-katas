"""
Kata 20 -- Design Patterns in Python
Run: python playground/20_design_patterns.py

Pythonic implementations of classic design patterns. Python's first-class functions,
closures, and duck typing make many patterns far simpler than their Java/C++ equivalents.
"""

import json
import weakref
from dataclasses import dataclass
from typing import Any, Callable


# ===========================================================================
# PATTERN 1: FACTORY (function-based, not class-based)
# ===========================================================================

# Registry of serializer functions -- the dict IS the factory
_serializer_registry: dict[str, Callable[[dict], str]] = {}


def register_serializer(name: str):
    """Decorator that registers a serializer function."""
    def decorator(func: Callable[[dict], str]) -> Callable[[dict], str]:
        _serializer_registry[name] = func
        return func
    return decorator


@register_serializer("json")
def _json_serializer(data: dict) -> str:
    return json.dumps(data)


@register_serializer("xml")
def _xml_serializer(data: dict) -> str:
    return "<data>" + "".join(
        f"<{k}>{v}</{k}>" for k, v in data.items()
    ) + "</data>"


@register_serializer("csv")
def _csv_serializer(data: dict) -> str:
    return ",".join(data.keys()) + "\n" + ",".join(str(v) for v in data.values())


def create_serializer(fmt: str) -> Callable[[dict], str]:
    """Factory function -- looks up a serializer by name."""
    if fmt not in _serializer_registry:
        raise ValueError(f"Unknown format: {fmt!r}. Available: {list(_serializer_registry)}")
    return _serializer_registry[fmt]


# ===========================================================================
# PATTERN 2: STRATEGY (functions/callables, not interface classes)
# ===========================================================================

def no_discount(price: float) -> float:
    """Strategy: no discount applied."""
    return price


def percentage_discount(percent: float) -> Callable[[float], float]:
    """Strategy factory: returns a percentage discount function."""
    def apply(price: float) -> float:
        return round(price * (1 - percent / 100), 2)
    return apply


def fixed_discount(amount: float) -> Callable[[float], float]:
    """Strategy factory: returns a fixed discount function."""
    def apply(price: float) -> float:
        return round(max(0, price - amount), 2)
    return apply


class Order:
    """Uses a strategy function for discount calculation."""

    def __init__(self, price: float, discount: Callable[[float], float] = no_discount):
        self.price = price
        self.discount = discount

    def total(self) -> float:
        return self.discount(self.price)


# ===========================================================================
# PATTERN 3: OBSERVER (callbacks with weak references)
# ===========================================================================

class EventEmitter:
    """Pythonic Observer pattern with weak reference support."""

    def __init__(self):
        self._listeners: dict[str, list] = {}

    def on(self, event: str, callback: Callable):
        """Subscribe a callback to an event."""
        self._listeners.setdefault(event, [])
        # Use weak reference for bound methods to avoid preventing GC
        if hasattr(callback, "__self__"):
            ref = weakref.WeakMethod(callback, self._make_cleanup(event))
            self._listeners[event].append(ref)
        else:
            # Plain functions -- store directly (they're module-level, won't be GC'd)
            self._listeners[event].append(callback)

    def _make_cleanup(self, event: str):
        """Create a finalizer that removes dead weak refs."""
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

    def listener_count(self, event: str) -> int:
        """Count live listeners for an event."""
        count = 0
        for cb in self._listeners.get(event, []):
            if isinstance(cb, weakref.ref):
                if cb() is not None:
                    count += 1
            else:
                count += 1
        return count


# ===========================================================================
# PATTERN 4: SINGLETON (module-level and __new__)
# ===========================================================================

# Approach 1: Module-level singleton (preferred)
class _AppConfig:
    """Private class -- users import the instance, not the class."""

    def __init__(self):
        self.debug: bool = False
        self.database_url: str = "sqlite:///app.db"
        self.max_connections: int = 10

app_config = _AppConfig()  # THE singleton


# Approach 2: __new__ override
class SingletonService:
    """Singleton using __new__ -- class-level guarantee of one instance."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.settings: dict[str, Any] = {}


# ===========================================================================
# PATTERN 5: TEMPLATE METHOD (ABC and function-injection)
# ===========================================================================

from abc import ABC, abstractmethod


# Approach 1: ABC version
class DataPipeline(ABC):
    """Template Method: run() defines the skeleton, subclasses fill in steps."""

    def run(self, raw_data: str) -> str:
        data = self.extract(raw_data)
        data = self.transform(data)
        return self.load(data)

    @abstractmethod
    def extract(self, raw_data: str) -> list:
        ...

    @abstractmethod
    def transform(self, data: list) -> list:
        ...

    @abstractmethod
    def load(self, data: list) -> str:
        ...


class CsvUpperPipeline(DataPipeline):
    """Concrete pipeline: CSV -> uppercase -> count summary."""

    def extract(self, raw_data: str) -> list:
        rows = raw_data.strip().split("\n")
        return [row.split(",")[0] for row in rows]

    def transform(self, data: list) -> list:
        return [item.upper() for item in data]

    def load(self, data: list) -> str:
        return f"Processed {len(data)} records: {', '.join(data)}"


class JsonFilterPipeline(DataPipeline):
    """Concrete pipeline: JSON -> filter high scores -> summary."""

    def extract(self, raw_data: str) -> list:
        return json.loads(raw_data)

    def transform(self, data: list) -> list:
        return [item for item in data if item.get("score", 0) >= 70]

    def load(self, data: list) -> str:
        names = [item["name"] for item in data]
        return f"High scorers: {', '.join(names)}"


# Approach 2: Function-injection version
class FlexiblePipeline:
    """Template Method using injectable hook functions."""

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


# ===========================================================================
# PATTERN 6: COMMAND (undo/redo with closures)
# ===========================================================================

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
        """Execute a command and push it onto the history stack."""
        command.execute()
        self._history.append(command)
        self._redo_stack.clear()

    def insert(self, text: str, position: int | None = None):
        """Insert text at position (defaults to end)."""
        pos = position if position is not None else len(self.content)
        old_content = self.content

        def execute():
            self.content = old_content[:pos] + text + old_content[pos:]

        def undo():
            self.content = old_content

        self._do(Command(execute, undo, f"insert '{text}' at {pos}"))

    def delete(self, start: int, end: int):
        """Delete text from start to end."""
        old_content = self.content
        deleted = self.content[start:end]

        def execute():
            self.content = old_content[:start] + old_content[end:]

        def undo():
            self.content = old_content

        self._do(Command(execute, undo, f"delete '{deleted}' [{start}:{end}]"))

    def undo(self) -> bool:
        """Undo the last command. Returns False if nothing to undo."""
        if not self._history:
            return False
        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)
        return True

    def redo(self) -> bool:
        """Redo the last undone command. Returns False if nothing to redo."""
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)
        return True

    @property
    def history_size(self) -> int:
        return len(self._history)


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Factory Pattern ---
    print("--- Section 1: Factory Pattern ---")

    test_data = {"name": "Alice", "age": 30}

    json_ser = create_serializer("json")
    xml_ser = create_serializer("xml")
    csv_ser = create_serializer("csv")

    json_result = json_ser(test_data)
    xml_result = xml_ser(test_data)
    csv_result = csv_ser(test_data)

    print("  JSON-style factory:")
    print(f'    create_serializer("json"): {json_result}')
    print(f'    create_serializer("xml"):  {xml_result}')
    print(f'    create_serializer("csv"):  {csv_result}')

    assert json_result == '{"name": "Alice", "age": 30}'
    assert xml_result == "<data><name>Alice</name><age>30</age></data>"
    assert csv_result == "name,age\nAlice,30"

    # Register a new format dynamically
    @register_serializer("yaml")
    def _yaml_serializer(data: dict) -> str:
        return "\n".join(f"{k}: {v}" for k, v in data.items())

    yaml_ser = create_serializer("yaml")
    yaml_result = yaml_ser(test_data)

    print("  Factory with registration:")
    print("    Registered format 'yaml' dynamically")
    print(f'    create_serializer("yaml"): {yaml_result}')

    assert yaml_result == "name: Alice\nage: 30"

    # Test error for unknown format
    try:
        create_serializer("unknown")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  Factory pattern -- no base class, no abstract methods, just functions.")

    print()

    # --- Section 2: Strategy Pattern ---
    print("--- Section 2: Strategy Pattern ---")

    order1 = Order(100.00)
    order2 = Order(100.00, discount=percentage_discount(20))
    order3 = Order(100.00, discount=fixed_discount(15))
    order4 = Order(100.00, discount=lambda p: round(p * 0.9, 2))

    print(f"  No discount:  Order(100.00) = {order1.total():.2f}")
    print(f"  20% off:      Order(100.00) = {order2.total():.2f}")
    print(f"  Fixed $15 off: Order(100.00) = {order3.total():.2f}")
    print(f"  Lambda 10% off: Order(100.00) = {order4.total():.2f}")

    assert order1.total() == 100.00
    assert order2.total() == 80.00
    assert order3.total() == 85.00
    assert order4.total() == 90.00

    # Strategy can be swapped at runtime
    order = Order(100.00, discount=percentage_discount(20))
    before = order.total()
    order.discount = fixed_discount(15)
    after = order.total()

    print("  Strategy swapped at runtime:")
    print(f"    Before swap: {before:.2f}")
    print(f"    After swap:  {after:.2f}")

    assert before == 80.00
    assert after == 85.00

    print("  Strategy pattern -- callables replace interface hierarchies.")

    print()

    # --- Section 3: Observer Pattern ---
    print("--- Section 3: Observer Pattern ---")

    emitter = EventEmitter()
    received_events: list[tuple[str, Any]] = []

    def login_handler(username: str):
        msg = f"User logged in: {username}"
        received_events.append(("login", username))
        print(f"    [login_handler] {msg}")

    def audit_handler(username: str):
        msg = f"AUDIT: user_login -- {username}"
        received_events.append(("audit", username))
        print(f"    [audit_handler] {msg}")

    def order_handler(order_id: str, username: str):
        msg = f"Order placed: {order_id} by {username}"
        received_events.append(("order", order_id))
        print(f"    [order_handler] {msg}")

    emitter.on("user_login", login_handler)
    emitter.on("user_login", audit_handler)
    emitter.on("order_placed", order_handler)

    print("  Emitting 'user_login' event...")
    emitter.emit("user_login", "alice")
    assert len(received_events) == 2
    assert received_events[0] == ("login", "alice")
    assert received_events[1] == ("audit", "alice")

    print("  Emitting 'order_placed' event...")
    emitter.emit("order_placed", "order-42", "alice")
    assert len(received_events) == 3
    assert received_events[2] == ("order", "order-42")

    # Weak reference cleanup demo
    print("  Weak reference cleanup:")

    weak_emitter = EventEmitter()

    class TempObserver:
        def on_event(self, data):
            pass

    observer = TempObserver()
    weak_emitter.on("test", observer.on_event)
    print(f"    Listeners before delete: {weak_emitter.listener_count('test')}")
    assert weak_emitter.listener_count("test") == 1

    del observer  # Should trigger weak reference cleanup
    print(f"    Listeners after delete: {weak_emitter.listener_count('test')}")
    assert weak_emitter.listener_count("test") == 0

    print("  Observer pattern -- EventEmitter with weak reference support.")

    print()

    # --- Section 4: Singleton Pattern ---
    print("--- Section 4: Singleton Pattern ---")

    # Module-level singleton
    config1 = app_config
    config2 = app_config
    config1.debug = True

    print("  Module-level singleton:")
    print(f"    config1 is config2: {config1 is config2}")
    print(f"    Setting persists across imports: {config2.debug}")
    assert config1 is config2
    assert config2.debug is True

    # __new__ singleton
    s1 = SingletonService()
    s1.settings["key"] = "value"
    s2 = SingletonService()

    print("  __new__ singleton:")
    print(f"    s1 is s2: {s1 is s2}")
    print(f"    s1.settings is s2.settings: {s1.settings is s2.settings}")
    print(f"    State shared: {s2.settings.get('key') == 'value'}")
    assert s1 is s2
    assert s2.settings["key"] == "value"

    print("  Singleton pattern -- module-level is preferred in Python.")

    print()

    # --- Section 5: Template Method Pattern ---
    print("--- Section 5: Template Method Pattern ---")

    # ABC version
    csv_input = "alice,30\nbob,25\ncharlie,35"
    csv_pipeline = CsvUpperPipeline()
    csv_result = csv_pipeline.run(csv_input)

    print("  Pipeline 1 (CSV -> uppercase -> count):")
    print(f"    Input:  {csv_input!r}")
    print(f"    Output: {csv_result!r}")
    assert csv_result == "Processed 3 records: ALICE, BOB, CHARLIE"

    # JSON pipeline
    json_input = json.dumps([
        {"name": "A", "score": 85},
        {"name": "B", "score": 42},
    ])
    json_pipeline = JsonFilterPipeline()
    json_result = json_pipeline.run(json_input)

    print("  Pipeline 2 (JSON -> filter -> summary):")
    print(f"    Input:  {json_input!r}")
    print(f"    Output: {json_result!r}")
    assert json_result == "High scorers: A"

    # Function-injection version
    flex_pipeline = FlexiblePipeline(
        extract=lambda raw: raw.strip().split("\n"),
        transform=lambda data: [line.upper() for line in data],
        load=lambda data: f"Lines: {len(data)}",
    )
    flex_result = flex_pipeline.run("hello\nworld")
    assert flex_result == "Lines: 2"

    print("  Template Method -- ABC version and function-injection version both work.")

    print()

    # --- Section 6: Command Pattern (Undo/Redo) ---
    print("--- Section 6: Command Pattern (Undo/Redo) ---")

    editor = TextEditor()

    editor.insert("Hello")
    print(f"  insert 'Hello': content={editor.content!r}")
    assert editor.content == "Hello"

    editor.insert(" World")
    print(f"  insert ' World': content={editor.content!r}")
    assert editor.content == "Hello World"

    editor.insert("!")
    print(f"  insert '!': content={editor.content!r}")
    assert editor.content == "Hello World!"

    editor.undo()
    print(f"  undo: content={editor.content!r}")
    assert editor.content == "Hello World"

    editor.undo()
    print(f"  undo: content={editor.content!r}")
    assert editor.content == "Hello"

    editor.redo()
    print(f"  redo: content={editor.content!r}")
    assert editor.content == "Hello World"

    editor.delete(5, 11)
    print(f"  delete [5:11]: content={editor.content!r}")
    assert editor.content == "Hello"

    editor.undo()
    print(f"  undo delete: content={editor.content!r}")
    assert editor.content == "Hello World"

    print(f"  Command history: {editor.history_size} commands")
    assert editor.history_size == 2

    # Redo stack is cleared after new action
    editor2 = TextEditor()
    editor2.insert("A")
    editor2.insert("B")
    editor2.undo()
    assert editor2.content == "A"
    editor2.insert("C")  # Clears redo stack
    assert editor2.redo() is False  # Can't redo after new action

    print("  Command pattern -- closures capture state for undo/redo.")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Design Patterns in Python:")
    print("  - Factory: dict of callables replaces abstract factory class")
    print("  - Strategy: pass functions, not interface implementors")
    print("  - Observer: EventEmitter with weak references for cleanup")
    print("  - Singleton: module-level instance (preferred) or __new__")
    print("  - Template Method: ABC or injectable function hooks")
    print("  - Command: dataclass with execute/undo callables")
    print("  - Iterator: see Kata 02 (generators, __iter__/__next__)")
    print("  - Decorator: see Kata 03 (functools.wraps, decorator factories)")
    print()
    print("All 6 sections passed. You've mastered Pythonic design patterns!")
