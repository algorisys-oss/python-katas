# Kata 06 -- Type Hints & Protocols

[prev: 05-comprehensions-functional](./05-comprehensions-functional.md) | [next: 07-dataclasses-attrs](./07-dataclasses-attrs.md)

---

## What We're Building

Python is dynamically typed -- but that doesn't mean you should fly blind. Python's type annotation system lets you add type information that tools like mypy verify *statically* (at "compile time"), while the runtime happily ignores them. You get the best of both worlds: duck typing flexibility with IDE autocompletion and static verification.

In this kata we'll master the full type system: basic annotations, generics, `Protocol` (structural subtyping -- duck typing with type safety), `ParamSpec` for decorator type safety, and runtime introspection with `get_type_hints()`. By the end you'll understand *why* FastAPI and Pydantic lean so heavily on type annotations -- and you'll be ready to build systems that do the same.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Basic type hints | `def greet(name: str) -> str` | Every function signature |
| `Optional[X]` | Value can be `X` or `None` | Nullable parameters/returns |
| `Union[X, Y]` / `X \| Y` | Value can be one of several types | Multi-type parameters |
| Container types | `list[int]`, `dict[str, int]`, `tuple[int, ...]` | Typed collections |
| `TypeVar` | Generic type parameter | Functions that work on any type |
| `Generic[T]` | Generic classes | Reusable typed containers |
| `Protocol` | Structural subtyping (duck typing) | Interface without inheritance |
| `ParamSpec` | Preserve function signatures through decorators | Type-safe decorators |
| `Callable` | Type for function objects | Higher-order functions |
| `TypeAlias` | Named type alias | Complex type readability |
| `get_type_hints()` | Runtime annotation introspection | Frameworks, validation |
| `get_args()` / `get_origin()` | Inspect generic types at runtime | Framework internals |

## The Code

### Step 1: Basic type annotations

Type hints annotate function parameters, return types, and variables. They're *completely ignored* at runtime -- they're metadata for tools and humans.

```python
# Function annotations
def greet(name: str, excited: bool = False) -> str:
    if excited:
        return f"Hello, {name}!!!"
    return f"Hello, {name}"

# Variable annotations
age: int = 30
name: str = "Alice"
scores: list[float] = [98.5, 87.0, 92.3]

# Python does NOT enforce types at runtime -- this runs fine!
result = greet(42)  # No error at runtime, mypy would catch it
print(result)
# Output: Hello, 42
```

**Key insight:** Type hints are *metadata*. Python never checks them. They exist for static analysis tools (mypy, pyright), IDEs, and frameworks that introspect annotations at runtime.

### Step 2: Container types

Since Python 3.9, you can use built-in types directly as generic types. Before 3.9, you needed `from typing import List, Dict, Tuple`.

```python
# Modern syntax (3.9+): use built-in types directly
names: list[str] = ["Alice", "Bob"]
scores: dict[str, int] = {"Alice": 92, "Bob": 85}
point: tuple[float, float] = (1.5, 2.7)
coords: tuple[int, ...] = (1, 2, 3, 4)  # variable-length tuple of ints

# Nested container types
matrix: list[list[int]] = [[1, 2], [3, 4]]
registry: dict[str, list[str]] = {"admin": ["Alice"], "user": ["Bob", "Carol"]}
```

### Step 3: Optional, Union, and the pipe syntax

`Optional[X]` means "X or None." `Union[X, Y]` means "X or Y." Python 3.10+ introduced `X | Y` as sugar.

```python
from typing import Optional, Union

# Optional = Union[X, None]
def find_user(user_id: int) -> Optional[str]:
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)  # returns str or None

# Union: multiple types
def normalize(value: Union[str, int, float]) -> str:
    return str(value).strip()

# Python 3.10+ pipe syntax (equivalent to Union)
def normalize_modern(value: str | int | float) -> str:
    return str(value).strip()

# Optional with pipe syntax
def find_modern(user_id: int) -> str | None:
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)
```

### Step 4: TypeVar -- generic functions

`TypeVar` lets you write functions that preserve the relationship between input and output types. Without it, you'd lose type information.

```python
from typing import TypeVar, Sequence

T = TypeVar("T")

def first(items: Sequence[T]) -> T:
    """Return the first item. The return type matches the input element type."""
    return items[0]

# mypy knows these return types:
x: int = first([1, 2, 3])        # T = int
y: str = first(["a", "b", "c"])  # T = str

# Bounded TypeVar: restrict to specific types
Number = TypeVar("Number", int, float)

def double(x: Number) -> Number:
    return x * 2

# Bound TypeVar: must be a subclass
from typing import TypeVar
Comparable = TypeVar("Comparable", bound="SupportLessThan")
```

### Step 5: Generic classes

`Generic[T]` lets you create your own parameterized types, like `list[int]` or `dict[str, int]`.

```python
from typing import TypeVar, Generic, Iterator

T = TypeVar("T")

class Stack(Generic[T]):
    """A typed stack. Stack[int] only accepts ints."""

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

# Usage -- mypy tracks the type parameter
int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
print(int_stack.pop())  # 2 -- mypy knows this is int
```

### Step 6: Protocol -- structural subtyping (duck typing with type safety)

`Protocol` defines an interface based on *structure*, not inheritance. If a class has the right methods/attributes, it satisfies the protocol -- even without explicitly inheriting from it. This is Python's answer to Go interfaces.

```python
from typing import Protocol, runtime_checkable

class Drawable(Protocol):
    def draw(self) -> str: ...

# These classes DON'T inherit from Drawable -- but they match the structure
class Circle:
    def __init__(self, radius: float) -> None:
        self.radius = radius
    def draw(self) -> str:
        return f"Circle(r={self.radius})"

class Square:
    def __init__(self, side: float) -> None:
        self.side = side
    def draw(self) -> str:
        return f"Square(s={self.side})"

def render(shape: Drawable) -> str:
    """Accepts anything with a draw() -> str method."""
    return shape.draw()

# Both work -- structural subtyping!
print(render(Circle(5.0)))   # Circle(r=5.0)
print(render(Square(3.0)))   # Square(s=3.0)

# @runtime_checkable makes isinstance() work with protocols
@runtime_checkable
class Sized(Protocol):
    def __len__(self) -> int: ...

print(isinstance([1, 2, 3], Sized))  # True -- list has __len__
print(isinstance(42, Sized))          # False -- int has no __len__
```

### Step 7: ParamSpec -- type-safe decorators

`ParamSpec` captures the *entire signature* of a function, so decorators can preserve type information. Without it, decorated functions lose their parameter types.

```python
from typing import TypeVar, ParamSpec, Callable
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")

def log_call(func: Callable[P, R]) -> Callable[P, R]:
    """A decorator that preserves the wrapped function's type signature."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"  -> returned {result!r}")
        return result
    return wrapper

@log_call
def add(a: int, b: int) -> int:
    return a + b

# mypy knows add(a: int, b: int) -> int, not add(*args, **kwargs) -> Any
result = add(3, 4)
# Output:
# Calling add
#   -> returned 7
```

### Step 8: Callable types

`Callable[[ArgTypes...], ReturnType]` describes the type of a function object.

```python
from typing import Callable

# A function that takes two ints and returns an int
Operation = Callable[[int, int], int]

def apply_op(op: Operation, a: int, b: int) -> int:
    return op(a, b)

print(apply_op(lambda a, b: a + b, 10, 20))  # 30
print(apply_op(lambda a, b: a * b, 10, 20))  # 200

# Callable with no args
Factory = Callable[[], str]

def make_greeter() -> Factory:
    return lambda: "Hello!"

greet = make_greeter()
print(greet())  # Hello!
```

### Step 9: TypeAlias and complex types

`TypeAlias` makes complex type definitions readable.

```python
from typing import TypeAlias

# Without alias -- hard to read
def process(data: dict[str, list[tuple[int, float]]]) -> None: ...

# With alias -- clear intent
Row: TypeAlias = tuple[int, float]
Table: TypeAlias = dict[str, list[Row]]

def process_clean(data: Table) -> None: ...

# JSON type alias (recursive types need forward references)
JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
```

### Step 10: Runtime introspection with get_type_hints()

Type hints are stored in `__annotations__`, but `get_type_hints()` resolves forward references and string annotations properly. Frameworks like FastAPI and Pydantic use this heavily.

```python
from typing import get_type_hints, get_args, get_origin, Optional

def create_user(name: str, age: int, email: Optional[str] = None) -> dict:
    return {"name": name, "age": age, "email": email}

# get_type_hints resolves all annotations
hints = get_type_hints(create_user)
print(hints)
# {'name': <class 'str'>, 'age': <class 'int'>,
#  'email': typing.Optional[str], 'return': <class 'dict'>}

# Inspect generic types
from typing import get_args, get_origin
print(get_origin(list[int]))      # <class 'list'>
print(get_args(list[int]))        # (<class 'int'>,)
print(get_origin(Optional[str]))  # typing.Union
print(get_args(Optional[str]))    # (<class 'str'>, <class 'NoneType'>)
```

### Step 11: Static vs runtime -- type hints DON'T enforce

This is the most important thing to understand: Python's type hints are **purely informational at runtime**. They don't prevent misuse -- only tools like mypy do.

```python
def add_ints(a: int, b: int) -> int:
    return a + b

# Python happily runs this -- no TypeError!
result = add_ints("hello", "world")
print(result)
# Output: helloworld

# The annotations are just metadata
print(add_ints.__annotations__)
# {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}

# You can even set annotations to nonsense
x: "this is not a type" = 42
print(x)  # 42 -- Python doesn't care
```

**This is by design.** Python's philosophy is that type hints are *opt-in tooling*, not runtime enforcement. If you want runtime enforcement, you build it yourself (which is exactly what Pydantic and our Ignite framework will do).

## Playground

Run the full interactive demo:

```bash
python playground/06_type_hints_protocols.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### The annotations machinery

When Python encounters `def f(x: int) -> str`, it stores the annotations in `f.__annotations__` (a plain dict). It does **not** generate any type-checking code. The `typing` module provides special forms (`Union`, `Optional`, `Generic`) that create objects representing complex types -- but these are still just metadata.

```
def f(x: int) -> str:        # Python stores {'x': int, 'return': str}
    return str(x)             # No runtime check is generated

get_type_hints(f)             # Resolves forward refs, returns the dict
f.__annotations__             # Raw annotations dict
```

### Protocol vs ABC

| Feature | ABC (nominal) | Protocol (structural) |
|---|---|---|
| Requires inheritance? | Yes (`class Foo(ABC)`) | No |
| isinstance check? | Always works | Only with `@runtime_checkable` |
| Duck typing? | No | Yes -- matches by structure |
| Use when? | You control the class hierarchy | You want to accept any matching object |

### TypeVar binding

When you call `first([1, 2, 3])`, mypy *binds* `T` to `int` for that call. Each call site gets its own binding. This is how generic functions maintain type safety without code duplication.

```
first: (Sequence[T]) -> T

first([1, 2, 3])      # T=int,  returns int
first(["a", "b"])      # T=str,  returns str
first([(1,), (2,)])    # T=tuple[int, ...], returns tuple[int, ...]
```

## Exercises

### Exercise 1: Generic Result type

Build a `Result[T, E]` type that represents either a success value (`Ok[T]`) or an error (`Err[E]`). This is a common pattern in Rust and functional programming.

```python
T = TypeVar("T")
E = TypeVar("E")

class Result(Generic[T, E]):
    """Base class -- don't instantiate directly."""
    ...

class Ok(Result[T, E]):
    """Wraps a success value."""
    ...

class Err(Result[T, E]):
    """Wraps an error value."""
    ...

# Usage:
def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("division by zero")
    return Ok(a / b)

ok = divide(10, 3)
err = divide(10, 0)
assert ok.is_ok() and ok.unwrap() == 10 / 3
assert err.is_err() and err.unwrap_err() == "division by zero"
```

### Exercise 2: Sortable protocol

Implement a `Sortable` protocol and a generic `sort_items()` function:

```python
class Sortable(Protocol):
    def __lt__(self, other: "Sortable") -> bool: ...

def sort_items(items: list[Sortable]) -> list[Sortable]:
    """Sort anything that supports < comparison."""
    ...

# Should work with ints, strings, and custom classes
print(sort_items([3, 1, 4, 1, 5]))  # [1, 1, 3, 4, 5]
print(sort_items(["banana", "apple", "cherry"]))  # ['apple', 'banana', 'cherry']
```

## What's Next

In [Kata 07 -- Dataclasses & Attrs](./07-dataclasses-attrs.md), we'll explore Python's `dataclasses` module -- a decorator that auto-generates `__init__`, `__repr__`, `__eq__`, and more from type-annotated class attributes. You'll see how type hints go from documentation to code generation -- a preview of how frameworks like Pydantic work.

---

[prev: 05-comprehensions-functional](./05-comprehensions-functional.md) | [next: 07-dataclasses-attrs](./07-dataclasses-attrs.md)
