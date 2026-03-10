# Kata 08 -- Enums & Pattern Matching

[prev: 07-dataclasses-attrs](./07-dataclasses-attrs.md) | [next: 09-error-handling](./09-error-handling.md)

---

## What We're Building

Python's `enum` module gives you type-safe symbolic constants, and structural pattern matching (`match`/`case`, introduced in Python 3.10) gives you a powerful way to dispatch on the shape of data. Together they replace sprawling `if`/`elif` chains with code that's readable, exhaustive, and maintainable.

In this kata we'll build enums of increasing sophistication -- from basic `Enum` through `IntEnum`, `StrEnum`, and `Flag` -- then pair them with `match`/`case` to build real things: a calculator, an HTTP status classifier, a command parser, and a traffic light state machine.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `enum.Enum` | Named constants grouped in a class | Replace magic strings/ints with typed symbols |
| `enum.IntEnum` | Enum with `int` values (supports arithmetic) | Status codes, exit codes, numeric constants |
| `enum.StrEnum` | Enum with `str` values (supports string ops) | Config keys, API parameters, string constants |
| `enum.Flag` | Combinable flags via bitwise OR | Permissions, feature flags, option sets |
| `auto()` | Automatic value assignment | When you don't care about specific values |
| Custom methods | Methods/properties on enum classes | Add behavior to your constants |
| `match`/`case` | Structural pattern matching | Dispatch on value shape, type, or structure |
| Literal patterns | `case 42:`, `case "hello":` | Match exact values |
| Variable capture | `case x:` | Bind matched value to a name |
| OR patterns | `case A \| B:` | Match any of several alternatives |
| Guards | `case x if x > 0:` | Add conditions to patterns |
| Sequence patterns | `case [a, b, *rest]:` | Destructure lists/tuples |
| Mapping patterns | `case {"key": value}:` | Destructure dicts |
| Class patterns | `case Point(x=0, y=y):` | Destructure objects by attribute |

## The Code

### Step 1: Basic `Enum` -- defining, accessing, iteration

An `Enum` is a class where each member is a unique constant. Members are accessed by name or value, and the class is iterable.

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

# Access by name
print(Color.RED)           # Output: Color.RED
print(Color.RED.name)      # Output: RED
print(Color.RED.value)     # Output: 1

# Access by value
print(Color(2))            # Output: Color.GREEN

# Access by name string
print(Color["BLUE"])       # Output: Color.BLUE

# Iteration
for color in Color:
    print(f"  {color.name} = {color.value}")
# Output:
#   RED = 1
#   GREEN = 2
#   BLUE = 3

# Identity and equality
print(Color.RED is Color.RED)    # Output: True
print(Color.RED == Color.RED)    # Output: True
print(Color.RED == 1)            # Output: False  (Enum != int)
```

**Key insight:** `Enum` members are NOT equal to their values. `Color.RED == 1` is `False`. This is intentional -- it prevents accidental mixing of enums with raw values.

### Step 2: `IntEnum` and `StrEnum` -- when values matter

Sometimes you need enum members to behave like their underlying type. `IntEnum` members are also `int`, and `StrEnum` members are also `str`.

```python
from enum import IntEnum, StrEnum

class HttpStatus(IntEnum):
    OK = 200
    NOT_FOUND = 404
    SERVER_ERROR = 500

# IntEnum members compare equal to their int values
print(HttpStatus.OK == 200)         # Output: True
print(HttpStatus.NOT_FOUND + 1)     # Output: 405  (arithmetic works)
print(HttpStatus.OK < HttpStatus.NOT_FOUND)  # Output: True

class Direction(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

# StrEnum members behave like strings
print(Direction.NORTH == "north")          # Output: True
print(Direction.NORTH.upper())             # Output: NORTH
print(f"Heading {Direction.EAST}!")        # Output: Heading east!
```

**When to use which:** Use `Enum` for pure symbolic constants (no need to compare with raw values). Use `IntEnum`/`StrEnum` when you need interop with APIs, databases, or serialization formats that use raw ints/strings.

### Step 3: `Flag` -- combinable flags with bitwise ops

`Flag` members can be combined using bitwise operators (`|`, `&`, `~`). Each member's value should be a power of 2.

```python
from enum import Flag, auto

class Permission(Flag):
    READ = auto()     # 1
    WRITE = auto()    # 2
    EXECUTE = auto()  # 4

# Combine flags
rw = Permission.READ | Permission.WRITE
print(rw)                              # Output: Permission.READ|WRITE
print(Permission.READ in rw)           # Output: True
print(Permission.EXECUTE in rw)        # Output: False

# All permissions
all_perms = Permission.READ | Permission.WRITE | Permission.EXECUTE
print(all_perms)                       # Output: Permission.READ|WRITE|EXECUTE

# Remove a permission
no_write = all_perms & ~Permission.WRITE
print(no_write)                        # Output: Permission.READ|EXECUTE
print(Permission.WRITE in no_write)    # Output: False

# Iterate over set flags
for perm in rw:
    print(f"  Has: {perm.name}")
# Output:
#   Has: READ
#   Has: WRITE
```

### Step 4: `auto()` and custom methods

`auto()` assigns values automatically (1, 2, 3, ... for `Enum`; powers of 2 for `Flag`). You can also add methods to enums -- they're classes, after all.

```python
from enum import Enum, auto

class Season(Enum):
    SPRING = auto()
    SUMMER = auto()
    AUTUMN = auto()
    WINTER = auto()

    def is_warm(self) -> bool:
        return self in (Season.SPRING, Season.SUMMER)

    @property
    def next_season(self) -> "Season":
        members = list(Season)
        idx = members.index(self)
        return members[(idx + 1) % len(members)]

print(Season.SUMMER.is_warm())        # Output: True
print(Season.WINTER.is_warm())        # Output: False
print(Season.AUTUMN.next_season)      # Output: Season.WINTER
print(Season.WINTER.next_season)      # Output: Season.SPRING
```

### Step 5: `match`/`case` basics -- literal patterns, variable capture

Python 3.10 introduced structural pattern matching. The simplest patterns match literal values or capture into variables.

```python
def describe_status(status: int) -> str:
    match status:
        case 200:
            return "OK"
        case 301:
            return "Moved Permanently"
        case 404:
            return "Not Found"
        case 500:
            return "Internal Server Error"
        case _:
            return f"Unknown status: {status}"

print(describe_status(200))    # Output: OK
print(describe_status(404))    # Output: Not Found
print(describe_status(418))    # Output: Unknown status: 418
```

**Important:** `_` is the wildcard pattern -- it matches anything and discards the value. A bare name like `case x:` also matches anything but *captures* the value into `x`.

### Step 6: OR patterns with `|`

Use `|` to match any of several alternatives in a single case.

```python
def classify_char(ch: str) -> str:
    match ch.lower():
        case "a" | "e" | "i" | "o" | "u":
            return "vowel"
        case " " | "\t" | "\n":
            return "whitespace"
        case _:
            return "consonant"

print(classify_char("A"))     # Output: vowel
print(classify_char("x"))     # Output: consonant
print(classify_char(" "))     # Output: whitespace
```

### Step 7: Guards with `if` in case clauses

Guards add conditions to patterns. The pattern must match AND the guard must be true.

```python
def classify_number(n: int | float) -> str:
    match n:
        case 0:
            return "zero"
        case x if x > 0:
            return f"positive ({x})"
        case x if x < 0:
            return f"negative ({x})"

print(classify_number(42))     # Output: positive (42)
print(classify_number(-7))     # Output: negative (-7)
print(classify_number(0))      # Output: zero
```

### Step 8: Structural patterns -- sequences, mappings, classes

Pattern matching really shines with structured data. You can destructure lists, dicts, and objects in the pattern itself.

```python
# Sequence patterns
def process_command(command: list[str]) -> str:
    match command:
        case ["quit"]:
            return "Goodbye!"
        case ["greet", name]:
            return f"Hello, {name}!"
        case ["move", direction, distance]:
            return f"Moving {direction} by {distance}"
        case ["add", *numbers]:
            total = sum(int(n) for n in numbers)
            return f"Sum: {total}"
        case []:
            return "Empty command"
        case _:
            return f"Unknown command: {command}"

print(process_command(["quit"]))              # Output: Goodbye!
print(process_command(["greet", "Alice"]))     # Output: Hello, Alice!
print(process_command(["move", "north", "5"])) # Output: Moving north by 5
print(process_command(["add", "1", "2", "3"])) # Output: Sum: 6

# Mapping patterns
def handle_event(event: dict) -> str:
    match event:
        case {"type": "click", "x": x, "y": y}:
            return f"Click at ({x}, {y})"
        case {"type": "keypress", "key": key}:
            return f"Key pressed: {key}"
        case {"type": "resize", "width": w, "height": h}:
            return f"Resized to {w}x{h}"
        case _:
            return f"Unknown event: {event}"

print(handle_event({"type": "click", "x": 100, "y": 200}))
# Output: Click at (100, 200)
print(handle_event({"type": "keypress", "key": "Enter"}))
# Output: Key pressed: Enter
```

**Mapping patterns are partial:** `{"type": "click", "x": x, "y": y}` matches any dict that has those keys -- extra keys are ignored.

### Step 9: Class patterns -- matching object attributes

Class patterns destructure objects by their attributes. For this to work, the class needs `__match_args__` (dataclasses provide this automatically).

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Circle:
    center: Point
    radius: float

@dataclass
class Rectangle:
    origin: Point
    width: float
    height: float

def describe_shape(shape) -> str:
    match shape:
        case Circle(center=Point(x=0, y=0), radius=r):
            return f"Circle at origin with radius {r}"
        case Circle(center=center, radius=r) if r > 100:
            return f"Large circle at {center} with radius {r}"
        case Circle(center=center, radius=r):
            return f"Circle at {center} with radius {r}"
        case Rectangle(origin=origin, width=w, height=h) if w == h:
            return f"Square at {origin}, side {w}"
        case Rectangle(origin=origin, width=w, height=h):
            return f"Rectangle at {origin}, {w}x{h}"
        case _:
            return "Unknown shape"

print(describe_shape(Circle(Point(0, 0), 5)))
# Output: Circle at origin with radius 5
print(describe_shape(Circle(Point(1, 2), 150)))
# Output: Large circle at Point(x=1, y=2) with radius 150
print(describe_shape(Rectangle(Point(0, 0), 10, 10)))
# Output: Square at Point(x=0, y=0), side 10
```

### Step 10: Combining enums with pattern matching

Enums and `match`/`case` are natural partners. Here's an HTTP status classifier and a command parser.

```python
from enum import Enum, IntEnum, auto

class HttpStatus(IntEnum):
    OK = 200
    CREATED = 201
    MOVED = 301
    BAD_REQUEST = 400
    NOT_FOUND = 404
    FORBIDDEN = 403
    SERVER_ERROR = 500
    BAD_GATEWAY = 502

def classify_response(status: HttpStatus) -> str:
    match status:
        case HttpStatus.OK | HttpStatus.CREATED:
            return "Success"
        case HttpStatus.MOVED:
            return "Redirect"
        case HttpStatus.BAD_REQUEST | HttpStatus.NOT_FOUND | HttpStatus.FORBIDDEN:
            return "Client Error"
        case HttpStatus.SERVER_ERROR | HttpStatus.BAD_GATEWAY:
            return "Server Error"
        case _:
            return "Unknown"

# State machine: traffic light
class LightState(Enum):
    GREEN = auto()
    YELLOW = auto()
    RED = auto()

def next_light(state: LightState) -> LightState:
    match state:
        case LightState.GREEN:
            return LightState.YELLOW
        case LightState.YELLOW:
            return LightState.RED
        case LightState.RED:
            return LightState.GREEN

# Run the state machine
light = LightState.GREEN
cycle = [light]
for _ in range(5):
    light = next_light(light)
    cycle.append(light)
print([l.name for l in cycle])
# Output: ['GREEN', 'YELLOW', 'RED', 'GREEN', 'YELLOW', 'RED']
```

### Step 11: Real-world -- calculator with match

Combining everything: a calculator that parses and evaluates expressions using enums and pattern matching.

```python
from enum import Enum, auto
from dataclasses import dataclass

class Op(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()

@dataclass
class Expr:
    left: float
    op: Op
    right: float

def parse_op(symbol: str) -> Op:
    match symbol:
        case "+":
            return Op.ADD
        case "-":
            return Op.SUB
        case "*":
            return Op.MUL
        case "/":
            return Op.DIV
        case _:
            raise ValueError(f"Unknown operator: {symbol}")

def evaluate(expr: Expr) -> float:
    match expr.op:
        case Op.ADD:
            return expr.left + expr.right
        case Op.SUB:
            return expr.left - expr.right
        case Op.MUL:
            return expr.left * expr.right
        case Op.DIV:
            if expr.right == 0:
                raise ZeroDivisionError("Division by zero")
            return expr.left / expr.right

def calc(expression: str) -> float:
    parts = expression.split()
    match parts:
        case [left, op, right]:
            return evaluate(Expr(float(left), parse_op(op), float(right)))
        case _:
            raise ValueError(f"Invalid expression: {expression}")

print(calc("10 + 5"))    # Output: 15.0
print(calc("20 / 4"))    # Output: 5.0
print(calc("3 * 7"))     # Output: 21.0
```

## Playground

Run the full interactive demo:

```bash
python playground/08_enums_pattern_matching.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Enum internals

When Python executes `class Color(Enum)`, the `EnumMeta` metaclass intercepts class creation:

```
class Color(Enum):      →  EnumMeta.__new__() runs
    RED = 1              →  Creates Color.RED as a singleton instance
    GREEN = 2            →  Creates Color.GREEN as a singleton instance
    BLUE = 3             →  Creates Color.BLUE as a singleton instance

Color.RED is Color.RED   →  True (always the same object)
Color(1) is Color.RED    →  True (lookup, not creation)
```

Each member is an *instance* of the enum class, stored in a class-level mapping. Calling `Color(1)` looks up the existing instance by value -- it never creates a new one.

### Pattern matching compilation

`match`/`case` is NOT a switch statement (though it can be used like one). It's a structural pattern matcher:

```
match subject:
    case pattern:
        body

1. Evaluate subject once
2. Try each case pattern top-to-bottom:
   a. Does the pattern's structure match?
   b. If there's a guard (if ...), does it pass?
   c. First match wins → bind variables → execute body
3. If no case matches → do nothing (no error)
```

The compiler optimizes common cases (literal matching, type checking) but the general mechanism supports arbitrarily nested structural matching.

### Pattern types at a glance

| Pattern | Syntax | Matches |
|---|---|---|
| Literal | `case 42:` | Exact value |
| Capture | `case x:` | Anything (binds to `x`) |
| Wildcard | `case _:` | Anything (discards) |
| OR | `case A \| B:` | Either alternative |
| Sequence | `case [a, b]:` | Length-2 sequence |
| Star | `case [a, *rest]:` | 1+ items, rest captured |
| Mapping | `case {"k": v}:` | Dict with key "k" |
| Class | `case MyClass(x=1):` | Instance with attr x==1 |
| Guard | `case x if x > 0:` | Pattern + condition |

## Exercises

### Exercise 1: Build a simple calculator with match

Extend the calculator to support modulo (`%`) and power (`**`) operations. Add input validation that returns an error message for division by zero instead of raising an exception.

```python
# Expected behavior:
# calc("10 % 3")   → 1.0
# calc("2 ** 8")   → 256.0
# calc("5 / 0")    → "Error: Division by zero"
```

### Exercise 2: Implement a traffic light state machine with durations

Build a traffic light that tracks both state and remaining duration. Each state has a fixed duration: GREEN=30, YELLOW=5, RED=20. The `tick()` function decrements the timer and transitions when it hits zero.

```python
# Expected behavior:
# light = TrafficLight(LightState.GREEN, 30)
# After 30 ticks → YELLOW, 5
# After 5 more ticks → RED, 20
# After 20 more ticks → GREEN, 30
```

## What's Next

In [Kata 09 -- Error Handling](./09-error-handling.md), we'll explore Python's exception hierarchy, custom exceptions, context managers for cleanup, and structured error handling patterns. You'll learn how to design error types that carry meaningful context and use `match`/`case` to dispatch on different error conditions.

---

[prev: 07-dataclasses-attrs](./07-dataclasses-attrs.md) | [next: 09-error-handling](./09-error-handling.md)
