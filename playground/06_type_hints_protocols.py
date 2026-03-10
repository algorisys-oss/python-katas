"""
Kata 06 -- Type Hints & Protocols
Run: python playground/06_type_hints_protocols.py

Master Python's type annotation system: basic hints, Optional, Union,
TypeVar, Generic, Protocol (structural subtyping), ParamSpec, Callable,
TypeAlias, and runtime introspection with get_type_hints().
"""

from typing import (
    TypeVar,
    Generic,
    Protocol,
    runtime_checkable,
    Optional,
    Union,
    Callable,
    TypeAlias,
    ParamSpec,
    Sequence,
    Iterator,
    get_type_hints,
    get_args,
    get_origin,
)
from functools import wraps


# ===========================================================================
# TYPE DEFINITIONS
# ===========================================================================

T = TypeVar("T")
E = TypeVar("E")
P = ParamSpec("P")
R = TypeVar("R")

# TypeAlias for readability
Row: TypeAlias = tuple[int, float]
Table: TypeAlias = dict[str, list[Row]]
JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


# ===========================================================================
# GENERIC FUNCTIONS
# ===========================================================================

def first(items: Sequence[T]) -> T:
    """Return the first item of a sequence, preserving the element type."""
    return items[0]


def pair(a: T, b: T) -> tuple[T, T]:
    """Return a tuple of two items of the same type."""
    return (a, b)


# ===========================================================================
# GENERIC CLASS: Stack[T]
# ===========================================================================

class Stack(Generic[T]):
    """A typed stack. Stack[int] only accepts ints (statically)."""

    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(reversed(self._items))

    def __repr__(self) -> str:
        return f"Stack({list(reversed(self._items))})"


# ===========================================================================
# PROTOCOL: Drawable (structural subtyping)
# ===========================================================================

class Drawable(Protocol):
    """Any object with a draw() -> str method satisfies this protocol."""
    def draw(self) -> str: ...


class Circle:
    """Does NOT inherit from Drawable -- but matches its structure."""
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def draw(self) -> str:
        return f"Circle(r={self.radius})"


class Square:
    """Does NOT inherit from Drawable -- but matches its structure."""
    def __init__(self, side: float) -> None:
        self.side = side

    def draw(self) -> str:
        return f"Square(s={self.side})"


def render(shape: Drawable) -> str:
    """Accept anything with a draw() -> str method."""
    return shape.draw()


# ===========================================================================
# PROTOCOL: Sortable
# ===========================================================================

@runtime_checkable
class Sortable(Protocol):
    """Any object that supports < comparison."""
    def __lt__(self, other: "Sortable") -> bool: ...


S = TypeVar("S", bound=Sortable)


def sort_items(items: list[S]) -> list[S]:
    """Sort anything that supports < comparison."""
    return sorted(items)


# ===========================================================================
# PARAMSPEC: Type-safe decorator
# ===========================================================================

def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """A decorator that preserves the wrapped function's type signature."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"    [log] Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"    [log]   -> returned {result!r}")
        return result
    return wrapper


@log_call
def add(a: int, b: int) -> int:
    return a + b


@log_call
def greet(name: str, excited: bool = False) -> str:
    if excited:
        return f"Hello, {name}!!!"
    return f"Hello, {name}"


# ===========================================================================
# CALLABLE TYPES
# ===========================================================================

Operation: TypeAlias = Callable[[int, int], int]


def apply_op(op: Operation, a: int, b: int) -> int:
    """Apply a binary int operation."""
    return op(a, b)


# ===========================================================================
# GENERIC RESULT TYPE (Exercise solution)
# ===========================================================================

class Result(Generic[T, E]):
    """Base for Ok/Err -- represents success or failure."""

    def is_ok(self) -> bool:
        return isinstance(self, Ok)

    def is_err(self) -> bool:
        return isinstance(self, Err)

    def unwrap(self) -> T:
        if isinstance(self, Ok):
            return self.value
        raise ValueError(f"Called unwrap() on Err: {self}")

    def unwrap_err(self) -> E:
        if isinstance(self, Err):
            return self.error
        raise ValueError(f"Called unwrap_err() on Ok: {self}")


class Ok(Result[T, E]):
    """Wraps a success value."""

    def __init__(self, value: T) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


class Err(Result[T, E]):
    """Wraps an error value."""

    def __init__(self, error: E) -> None:
        self.error = error

    def __repr__(self) -> str:
        return f"Err({self.error!r})"


def divide(a: float, b: float) -> Result[float, str]:
    """Divide a by b, returning Ok(result) or Err(message)."""
    if b == 0:
        return Err("division by zero")
    return Ok(a / b)


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Basic type annotations ---
    print("--- Section 1: Basic Type Annotations ---")

    def greet_basic(name: str, excited: bool = False) -> str:
        if excited:
            return f"Hello, {name}!!!"
        return f"Hello, {name}"

    result = greet_basic("Alice")
    print(f"greet('Alice') = {result!r}")
    # Output: greet('Alice') = 'Hello, Alice'
    assert result == "Hello, Alice"

    result_excited = greet_basic("Bob", excited=True)
    print(f"greet('Bob', excited=True) = {result_excited!r}")
    # Output: greet('Bob', excited=True) = 'Hello, Bob!!!'
    assert result_excited == "Hello, Bob!!!"

    # Variable annotations
    age: int = 30
    name: str = "Alice"
    scores: list[float] = [98.5, 87.0, 92.3]
    print(f"age={age}, name={name!r}, scores={scores}")
    # Output: age=30, name='Alice', scores=[98.5, 87.0, 92.3]

    print()

    # --- Section 2: Container types ---
    print("--- Section 2: Container Types ---")

    names: list[str] = ["Alice", "Bob", "Carol"]
    grades: dict[str, int] = {"Alice": 92, "Bob": 85, "Carol": 78}
    point: tuple[float, float] = (1.5, 2.7)
    coords: tuple[int, ...] = (1, 2, 3, 4)
    matrix: list[list[int]] = [[1, 2], [3, 4]]
    registry: dict[str, list[str]] = {"admin": ["Alice"], "user": ["Bob", "Carol"]}

    print(f"names: {names}")
    print(f"grades: {grades}")
    print(f"point: {point}")
    print(f"coords: {coords}")
    print(f"matrix: {matrix}")
    print(f"registry: {registry}")

    assert isinstance(names, list)
    assert isinstance(grades, dict)
    assert isinstance(point, tuple) and len(point) == 2
    assert isinstance(coords, tuple) and len(coords) == 4

    print()

    # --- Section 3: Optional and Union ---
    print("--- Section 3: Optional and Union ---")

    def find_user(user_id: int) -> Optional[str]:
        users = {1: "Alice", 2: "Bob"}
        return users.get(user_id)

    found = find_user(1)
    not_found = find_user(99)
    print(f"find_user(1) = {found!r}")
    # Output: find_user(1) = 'Alice'
    print(f"find_user(99) = {not_found!r}")
    # Output: find_user(99) = None
    assert found == "Alice"
    assert not_found is None

    def normalize(value: Union[str, int, float]) -> str:
        return str(value).strip()

    assert normalize("  hello  ") == "hello"
    assert normalize(42) == "42"
    assert normalize(3.14) == "3.14"
    print(f"normalize('  hello  ') = {normalize('  hello  ')!r}")
    print(f"normalize(42) = {normalize(42)!r}")

    # Pipe syntax (3.10+) -- same semantics
    def normalize_modern(value: str | int | float) -> str:
        return str(value).strip()

    assert normalize_modern("  test  ") == "test"
    print(f"normalize_modern('  test  ') = {normalize_modern('  test  ')!r}")

    print()

    # --- Section 4: TypeVar -- generic functions ---
    print("--- Section 4: TypeVar -- Generic Functions ---")

    int_first = first([10, 20, 30])
    str_first = first(["alpha", "beta", "gamma"])
    print(f"first([10, 20, 30]) = {int_first}")
    # Output: first([10, 20, 30]) = 10
    print(f"first(['alpha', 'beta', 'gamma']) = {str_first!r}")
    # Output: first(['alpha', 'beta', 'gamma']) = 'alpha'
    assert int_first == 10
    assert str_first == "alpha"

    int_pair = pair(1, 2)
    str_pair = pair("a", "b")
    print(f"pair(1, 2) = {int_pair}")
    print(f"pair('a', 'b') = {str_pair}")
    assert int_pair == (1, 2)
    assert str_pair == ("a", "b")

    print()

    # --- Section 5: Generic classes -- Stack[T] ---
    print("--- Section 5: Generic Classes -- Stack[T] ---")

    int_stack: Stack[int] = Stack()
    int_stack.push(10)
    int_stack.push(20)
    int_stack.push(30)
    print(f"Stack after pushes: {int_stack}")
    # Output: Stack after pushes: Stack([10, 20, 30])
    assert len(int_stack) == 3

    top = int_stack.pop()
    print(f"Popped: {top}")
    # Output: Popped: 30
    assert top == 30
    assert len(int_stack) == 2

    peeked = int_stack.peek()
    print(f"Peek: {peeked}")
    # Output: Peek: 20
    assert peeked == 20
    assert len(int_stack) == 2  # peek doesn't remove

    # Iterate (LIFO order)
    items = list(int_stack)
    print(f"Items (LIFO): {items}")
    # Output: Items (LIFO): [20, 10]
    assert items == [20, 10]

    # String stack
    str_stack: Stack[str] = Stack()
    str_stack.push("hello")
    str_stack.push("world")
    assert str_stack.pop() == "world"
    assert str_stack.pop() == "hello"
    assert str_stack.is_empty()
    print(f"String stack works too (now empty: {str_stack.is_empty()})")

    print()

    # --- Section 6: Protocol -- structural subtyping ---
    print("--- Section 6: Protocol -- Structural Subtyping ---")

    circle = Circle(5.0)
    square = Square(3.0)

    # Neither Circle nor Square inherits from Drawable -- but both match
    print(f"render(circle) = {render(circle)!r}")
    # Output: render(circle) = 'Circle(r=5.0)'
    print(f"render(square) = {render(square)!r}")
    # Output: render(square) = 'Square(s=3.0)'
    assert render(circle) == "Circle(r=5.0)"
    assert render(square) == "Square(s=3.0)"

    # Render a list of shapes
    shapes: list[Drawable] = [Circle(1.0), Square(2.0), Circle(3.0)]
    rendered = [render(s) for s in shapes]
    print(f"Rendered shapes: {rendered}")
    assert rendered == ["Circle(r=1.0)", "Square(s=2.0)", "Circle(r=3.0)"]

    # runtime_checkable protocol: isinstance works
    print(f"isinstance([1,2,3], Sortable) = {isinstance([1, 2, 3], Sortable)}")
    # Output: isinstance([1,2,3], Sortable) = True (list has __lt__)
    print(f"isinstance(42, Sortable) = {isinstance(42, Sortable)}")
    # Output: isinstance(42, Sortable) = True (int has __lt__)
    assert isinstance([1, 2, 3], Sortable)
    assert isinstance(42, Sortable)
    assert isinstance("hello", Sortable)

    print()

    # --- Section 7: Sortable protocol + sort_items ---
    print("--- Section 7: Sortable Protocol + sort_items ---")

    sorted_ints = sort_items([3, 1, 4, 1, 5, 9, 2, 6])
    print(f"sort_items([3,1,4,1,5,9,2,6]) = {sorted_ints}")
    # Output: sort_items([3,1,4,1,5,9,2,6]) = [1, 1, 2, 3, 4, 5, 6, 9]
    assert sorted_ints == [1, 1, 2, 3, 4, 5, 6, 9]

    sorted_strs = sort_items(["banana", "apple", "cherry"])
    print(f"sort_items(['banana','apple','cherry']) = {sorted_strs}")
    # Output: sort_items(['banana','apple','cherry']) = ['apple', 'banana', 'cherry']
    assert sorted_strs == ["apple", "banana", "cherry"]

    sorted_floats = sort_items([3.14, 1.41, 2.72])
    print(f"sort_items([3.14, 1.41, 2.72]) = {sorted_floats}")
    assert sorted_floats == [1.41, 2.72, 3.14]

    print()

    # --- Section 8: ParamSpec -- type-safe decorators ---
    print("--- Section 8: ParamSpec -- Type-Safe Decorators ---")

    # add and greet are decorated with @log_call
    result = add(3, 4)
    # Output:
    #     [log] Calling add
    #     [log]   -> returned 7
    assert result == 7

    result = greet("Alice", excited=True)
    # Output:
    #     [log] Calling greet
    #     [log]   -> returned 'Hello, Alice!!!'
    assert result == "Hello, Alice!!!"

    # The decorated functions preserve their names
    assert add.__name__ == "add"
    assert greet.__name__ == "greet"
    print(f"add.__name__ = {add.__name__!r}")
    print(f"greet.__name__ = {greet.__name__!r}")

    print()

    # --- Section 9: Callable types ---
    print("--- Section 9: Callable Types ---")

    result_add = apply_op(lambda a, b: a + b, 10, 20)
    result_mul = apply_op(lambda a, b: a * b, 10, 20)
    print(f"apply_op(add, 10, 20) = {result_add}")
    # Output: apply_op(add, 10, 20) = 30
    print(f"apply_op(mul, 10, 20) = {result_mul}")
    # Output: apply_op(mul, 10, 20) = 200
    assert result_add == 30
    assert result_mul == 200

    # Callable with no args
    Factory: TypeAlias = Callable[[], str]

    def make_greeter(name: str) -> Factory:
        return lambda: f"Hello, {name}!"

    greeter = make_greeter("World")
    print(f"greeter() = {greeter()!r}")
    # Output: greeter() = 'Hello, World!'
    assert greeter() == "Hello, World!"

    print()

    # --- Section 10: TypeAlias ---
    print("--- Section 10: TypeAlias ---")

    # Complex types become readable with aliases
    sample_table: Table = {
        "sensor_a": [(1, 23.5), (2, 24.1)],
        "sensor_b": [(1, 18.3), (2, 19.0)],
    }
    print(f"Table: {sample_table}")
    assert len(sample_table) == 2
    assert sample_table["sensor_a"][0] == (1, 23.5)

    # Row alias makes individual entries clear
    row: Row = (3, 25.0)
    sample_table["sensor_a"].append(row)
    assert len(sample_table["sensor_a"]) == 3
    print(f"After adding row: {sample_table['sensor_a']}")

    print()

    # --- Section 11: Runtime introspection ---
    print("--- Section 11: Runtime Introspection ---")

    def create_user(name: str, age: int, email: Optional[str] = None) -> dict:
        return {"name": name, "age": age, "email": email}

    hints = get_type_hints(create_user)
    print(f"Type hints for create_user: {hints}")
    # Output: {'name': <class 'str'>, 'age': <class 'int'>,
    #          'email': typing.Optional[str], 'return': <class 'dict'>}
    assert hints["name"] is str
    assert hints["age"] is int
    assert hints["return"] is dict

    # Inspect generic type structure
    print(f"get_origin(list[int]) = {get_origin(list[int])}")
    # Output: get_origin(list[int]) = <class 'list'>
    print(f"get_args(list[int]) = {get_args(list[int])}")
    # Output: get_args(list[int]) = (<class 'int'>,)
    assert get_origin(list[int]) is list
    assert get_args(list[int]) == (int,)

    print(f"get_origin(dict[str, int]) = {get_origin(dict[str, int])}")
    print(f"get_args(dict[str, int]) = {get_args(dict[str, int])}")
    assert get_origin(dict[str, int]) is dict
    assert get_args(dict[str, int]) == (str, int)

    # Optional is Union[X, None]
    print(f"get_origin(Optional[str]) = {get_origin(Optional[str])}")
    print(f"get_args(Optional[str]) = {get_args(Optional[str])}")
    assert get_origin(Optional[str]) is Union
    assert get_args(Optional[str]) == (str, type(None))

    print()

    # --- Section 12: Type hints DON'T enforce at runtime ---
    print("--- Section 12: Type Hints DON'T Enforce at Runtime ---")

    def add_ints(a: int, b: int) -> int:
        return a + b

    # Python happily runs this -- no TypeError!
    wrong_result = add_ints("hello", " world")
    print(f"add_ints('hello', ' world') = {wrong_result!r}")
    # Output: add_ints('hello', ' world') = 'hello world'
    assert wrong_result == "hello world"  # str + str works fine at runtime

    # Annotations are just metadata
    print(f"add_ints.__annotations__ = {add_ints.__annotations__}")
    # Output: add_ints.__annotations__ = {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}

    # You can even annotate with nonsense strings
    x: "this is not a real type" = 42
    print(f"x = {x} (annotation is nonsense, Python doesn't care)")
    # Output: x = 42 (annotation is nonsense, Python doesn't care)
    assert x == 42

    # Variable annotations don't create variables
    class Demo:
        declared: int  # this does NOT create Demo.declared

    assert not hasattr(Demo(), "declared")
    print(f"Demo has 'declared' attribute? {hasattr(Demo(), 'declared')}")
    # Output: Demo has 'declared' attribute? False
    print("  (annotations don't create attributes -- they're just metadata)")

    print()

    # --- Section 13: Exercise -- Result[T, E] ---
    print("--- Section 13: Exercise -- Result[T, E] ---")

    ok_result = divide(10, 3)
    err_result = divide(10, 0)

    print(f"divide(10, 3) = {ok_result}")
    # Output: divide(10, 3) = Ok(3.3333333333333335)
    print(f"divide(10, 0) = {err_result}")
    # Output: divide(10, 0) = Err('division by zero')

    assert ok_result.is_ok()
    assert not ok_result.is_err()
    assert abs(ok_result.unwrap() - 10 / 3) < 1e-10
    print(f"  ok_result.is_ok() = {ok_result.is_ok()}")
    print(f"  ok_result.unwrap() = {ok_result.unwrap()}")

    assert err_result.is_err()
    assert not err_result.is_ok()
    assert err_result.unwrap_err() == "division by zero"
    print(f"  err_result.is_err() = {err_result.is_err()}")
    print(f"  err_result.unwrap_err() = {err_result.unwrap_err()!r}")

    # unwrap on Err should raise
    try:
        err_result.unwrap()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  err_result.unwrap() raised ValueError: {e}")
    # Output:   err_result.unwrap() raised ValueError: Called unwrap() on Err: Err('division by zero')

    # unwrap_err on Ok should raise
    try:
        ok_result.unwrap_err()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  ok_result.unwrap_err() raised ValueError: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Python type hints & protocols:")
    print("  - Type hints are metadata -- NOT enforced at runtime")
    print("  - Basic: str, int, float, bool, None")
    print("  - Containers: list[int], dict[str, int], tuple[int, ...]")
    print("  - Optional[X] = X | None,  Union[X, Y] = X | Y")
    print("  - TypeVar for generic functions that preserve types")
    print("  - Generic[T] for generic classes (Stack[int], Result[T, E])")
    print("  - Protocol for structural subtyping (duck typing + type safety)")
    print("  - ParamSpec for type-safe decorators")
    print("  - Callable[[Args], Return] for function types")
    print("  - get_type_hints() for runtime introspection")
    print("  - get_origin() / get_args() to inspect generic types")
    print()
    print("All 13 sections passed. You've mastered type hints & protocols!")
