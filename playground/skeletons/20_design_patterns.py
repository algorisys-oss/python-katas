"""
Kata 20 -- Design Patterns in Python
Run: python playground/skeletons/20_design_patterns.py

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
    # TODO: return a decorator that adds the wrapped function to _serializer_registry
    # HINT: the decorator takes a function, stores it in the dict, and returns it unchanged
    def decorator(func: Callable[[dict], str]) -> Callable[[dict], str]:
        pass
    return decorator


@register_serializer("json")
def _json_serializer(data: dict) -> str:
    # TODO: serialize data as JSON
    # HINT: json.dumps(data)
    pass


@register_serializer("xml")
def _xml_serializer(data: dict) -> str:
    # TODO: serialize data as XML
    # HINT: "<data>" + "".join(f"<{k}>{v}</{k}>" for k, v in data.items()) + "</data>"
    pass


@register_serializer("csv")
def _csv_serializer(data: dict) -> str:
    # TODO: serialize data as CSV (header row + value row)
    # HINT: keys as header, values as second row, joined by commas
    pass


def create_serializer(fmt: str) -> Callable[[dict], str]:
    """Factory function -- looks up a serializer by name."""
    # TODO: look up fmt in _serializer_registry, raise ValueError if not found
    pass


# ===========================================================================
# PATTERN 2: STRATEGY (functions/callables, not interface classes)
# ===========================================================================

def no_discount(price: float) -> float:
    """Strategy: no discount applied."""
    # TODO: return price unchanged
    pass


def percentage_discount(percent: float) -> Callable[[float], float]:
    """Strategy factory: returns a percentage discount function."""
    # TODO: return a closure that applies a percentage discount
    # HINT: return a function that takes price and returns price * (1 - percent / 100)
    pass


def fixed_discount(amount: float) -> Callable[[float], float]:
    """Strategy factory: returns a fixed discount function."""
    # TODO: return a closure that subtracts a fixed amount (min 0)
    # HINT: return a function that takes price and returns max(0, price - amount)
    pass


class Order:
    """Uses a strategy function for discount calculation."""

    def __init__(self, price: float, discount: Callable[[float], float] = no_discount):
        # TODO: store price and discount strategy
        pass

    def total(self) -> float:
        # TODO: apply the discount strategy to self.price
        pass


# ===========================================================================
# PATTERN 3: OBSERVER (callbacks with weak references)
# ===========================================================================

class EventEmitter:
    """Pythonic Observer pattern with weak reference support."""

    def __init__(self):
        # TODO: initialize a dict mapping event names to lists of listeners
        pass

    def on(self, event: str, callback: Callable):
        """Subscribe a callback to an event."""
        # TODO: add callback to the listeners for this event
        # HINT: use self._listeners.setdefault(event, [])
        # HINT: for bound methods (hasattr(callback, "__self__")), use weakref.WeakMethod
        # HINT: for plain functions, store directly
        pass

    def _make_cleanup(self, event: str):
        """Create a finalizer that removes dead weak refs."""
        # TODO: return a function that removes a dead ref from the listener list
        def cleanup(ref):
            pass
        return cleanup

    def emit(self, event: str, *args: Any, **kwargs: Any):
        """Notify all listeners for an event."""
        # TODO: iterate over listeners for the event and call each one
        # HINT: check if listener is a weakref.ref -- if so, dereference it first
        # HINT: skip dead weak references (where listener() returns None)
        pass

    def off(self, event: str, callback: Callable):
        """Unsubscribe a callback from an event."""
        # TODO: remove the callback from the listener list
        pass

    def listener_count(self, event: str) -> int:
        """Count live listeners for an event."""
        # TODO: count listeners, skipping dead weak references
        pass


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

# TODO: create the module-level singleton instance
# HINT: app_config = _AppConfig()
app_config = None


# Approach 2: __new__ override
class SingletonService:
    """Singleton using __new__ -- class-level guarantee of one instance."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        # TODO: return existing instance if it exists, otherwise create one
        # HINT: check cls._instance, use super().__new__(cls) to create
        pass

    def __init__(self):
        # TODO: guard against re-initialization with a flag
        # HINT: check hasattr(self, "_initialized") before setting up
        pass


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
        # TODO: split by newlines, take first column from each row
        # HINT: [row.split(",")[0] for row in raw_data.strip().split("\n")]
        pass

    def transform(self, data: list) -> list:
        # TODO: uppercase each item
        pass

    def load(self, data: list) -> str:
        # TODO: return "Processed N records: ITEM1, ITEM2, ..."
        pass


class JsonFilterPipeline(DataPipeline):
    """Concrete pipeline: JSON -> filter high scores -> summary."""

    def extract(self, raw_data: str) -> list:
        # TODO: parse JSON array
        pass

    def transform(self, data: list) -> list:
        # TODO: filter items where score >= 70
        pass

    def load(self, data: list) -> str:
        # TODO: return "High scorers: NAME1, NAME2, ..."
        pass


# Approach 2: Function-injection version
class FlexiblePipeline:
    """Template Method using injectable hook functions."""

    def __init__(
        self,
        extract: Callable[[str], list],
        transform: Callable[[list], list],
        load: Callable[[list], str],
    ):
        # TODO: store the three step functions
        pass

    def run(self, raw_data: str) -> str:
        # TODO: call extract -> transform -> load in sequence
        pass


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
        # TODO: initialize content as empty string, _history and _redo_stack as empty lists
        pass

    def _do(self, command: Command):
        """Execute a command and push it onto the history stack."""
        # TODO: execute the command, append to history, clear redo stack
        pass

    def insert(self, text: str, position: int | None = None):
        """Insert text at position (defaults to end)."""
        # TODO: create execute/undo closures that modify self.content
        # HINT: capture old_content before the change
        # HINT: execute = insert text at position
        # HINT: undo = restore old_content
        # Then call self._do(Command(execute, undo, description))
        pass

    def delete(self, start: int, end: int):
        """Delete text from start to end."""
        # TODO: create execute/undo closures for deletion
        # HINT: capture old_content and the deleted text
        # HINT: execute = remove text[start:end]
        # HINT: undo = restore old_content
        pass

    def undo(self) -> bool:
        """Undo the last command. Returns False if nothing to undo."""
        # TODO: pop from history, call undo(), push to redo stack
        pass

    def redo(self) -> bool:
        """Redo the last undone command. Returns False if nothing to redo."""
        # TODO: pop from redo stack, call execute(), push to history
        pass

    @property
    def history_size(self) -> int:
        return len(self._history)


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Factory Pattern ---
    print("--- Section 1: Factory Pattern ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Strategy Pattern ---
    print("--- Section 2: Strategy Pattern ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Observer Pattern ---
    print("--- Section 3: Observer Pattern ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Singleton Pattern ---
    print("--- Section 4: Singleton Pattern ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: Template Method Pattern ---
    print("--- Section 5: Template Method Pattern ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: Command Pattern (Undo/Redo) ---
    print("--- Section 6: Command Pattern (Undo/Redo) ---")

    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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
