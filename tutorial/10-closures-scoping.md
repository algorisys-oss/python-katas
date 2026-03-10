# Kata 10 -- Closures, Scoping & First-Class Functions

[prev: 09-error-handling](./09-error-handling.md) | [next: 11-classes-inheritance](./11-classes-inheritance.md)

---

## What We're Building

Functions in Python are not just executable blocks -- they are **objects**. You can assign them to variables, pass them as arguments, return them from other functions, and store them in data structures. When a function captures variables from its enclosing scope, it becomes a **closure** -- one of the most powerful patterns in programming.

In this kata we'll master Python's scoping rules (LEGB), learn how closures capture their environment, build practical factories using closures, explore higher-order functions, and understand callable objects. By the end you'll be able to build middleware chains and event systems using nothing but functions and closures.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| LEGB rule | Local, Enclosing, Global, Built-in scope resolution | Understanding where Python looks up names |
| `nonlocal` | Modify a variable in the enclosing scope | Mutable state in closures |
| Closures | Functions that capture their enclosing environment | Factories, callbacks, stateful functions |
| `functools.partial` | Pre-fill some arguments of a function | Function specialization without lambdas |
| Higher-order functions | Functions that take or return functions | Composition, pipelines, strategies |
| `functools.singledispatch` | Dispatch to different implementations by argument type | Function overloading |
| Lambda expressions | Anonymous single-expression functions | Short callbacks, sort keys |
| Callable objects | Objects with `__call__` | Stateful callables with methods |
| First-class functions | Functions are objects with attributes | Dynamic dispatch, registries |

## The Code

### Step 1: The LEGB scope rule

Python resolves names by searching four scopes in order: **L**ocal, **E**nclosing, **G**lobal, **B**uilt-in. The first match wins.

```python
x = "global"  # Global scope

def outer():
    x = "enclosing"  # Enclosing scope

    def inner():
        x = "local"  # Local scope
        print(f"inner sees: {x}")

    inner()
    print(f"outer sees: {x}")

outer()
print(f"module sees: {x}")
# Output:
# inner sees: local
# outer sees: enclosing
# module sees: global
```

Without a local assignment, Python looks outward:

```python
x = "global"

def outer():
    x = "enclosing"

    def inner():
        # No local x -- Python finds the enclosing one
        print(f"inner sees: {x}")

    inner()

outer()
# Output: inner sees: enclosing
```

The Built-in scope contains names like `len`, `print`, `range`. You can shadow them (but shouldn't):

```python
# Don't do this!
# len = 42  # Shadows the built-in len()
# print(len([1, 2, 3]))  # TypeError: 'int' object is not callable
```

### Step 2: The `nonlocal` keyword

By default, assigning to a variable in a nested function creates a **new local** variable. To modify a variable in the enclosing scope, use `nonlocal`:

```python
def counter():
    count = 0

    def increment():
        nonlocal count  # Without this, "count += 1" would fail
        count += 1
        return count

    return increment

c = counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3
```

Without `nonlocal`, Python treats `count += 1` as creating a local `count`, and you get an `UnboundLocalError` because you're reading it before assignment.

Compare with `global`:

```python
module_var = 0

def modify_global():
    global module_var
    module_var += 1

modify_global()
print(module_var)  # 1
```

**Rule of thumb:** `nonlocal` targets the enclosing function scope. `global` targets the module scope. Prefer `nonlocal` over `global` -- global mutable state is a source of bugs.

### Step 3: Closures -- functions that capture their environment

A closure is a function that remembers variables from the scope where it was defined, even after that scope has exited. The "closed-over" variables are stored in the function's `__closure__` attribute.

```python
def make_greeter(greeting):
    """Factory that returns a greeting function."""
    def greet(name):
        return f"{greeting}, {name}!"
    return greet

hello = make_greeter("Hello")
hola = make_greeter("Hola")

print(hello("Alice"))  # Hello, Alice!
print(hola("Bob"))     # Hola, Bob!

# The closure captures the 'greeting' variable
print(hello.__closure__[0].cell_contents)  # Hello
print(hola.__closure__[0].cell_contents)   # Hola
```

### Step 4: Closure use cases -- practical factories

**Counter factory:**

```python
def make_counter(start=0):
    count = start

    def increment(step=1):
        nonlocal count
        count += step
        return count

    def get():
        return count

    def reset():
        nonlocal count
        count = start

    increment.get = get
    increment.reset = reset
    return increment

counter = make_counter(10)
print(counter())     # 11
print(counter(5))    # 16
print(counter.get()) # 16
counter.reset()
print(counter.get()) # 10
```

**Multiplier factory:**

```python
def make_multiplier(factor):
    def multiply(x):
        return x * factor
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))   # 10
print(triple(5))   # 15

# Use with map
print(list(map(double, [1, 2, 3, 4])))  # [2, 4, 6, 8]
```

**Config factory:**

```python
def make_formatter(template, **defaults):
    """Create a string formatter with default values baked in."""
    def format(**kwargs):
        merged = {**defaults, **kwargs}
        return template.format(**merged)
    return format

log_fmt = make_formatter(
    "[{level}] {timestamp} - {message}",
    level="INFO",
    timestamp="N/A"
)

print(log_fmt(message="Server started"))
# Output: [INFO] N/A - Server started
print(log_fmt(message="Error!", level="ERROR", timestamp="12:00"))
# Output: [ERROR] 12:00 - Error!
```

### Step 5: The late binding gotcha

Closures capture variables **by reference**, not by value. This means loop variables are looked up at call time, not at definition time:

```python
# BUG: all functions see i=4 (the final value)
functions = []
for i in range(5):
    functions.append(lambda: i)

print([f() for f in functions])
# Output: [4, 4, 4, 4, 4]  -- NOT [0, 1, 2, 3, 4]!
```

**Fix 1: Default argument (captures value at definition time):**

```python
functions = []
for i in range(5):
    functions.append(lambda i=i: i)  # i=i captures current value

print([f() for f in functions])
# Output: [0, 1, 2, 3, 4]
```

**Fix 2: Factory function (creates a new scope per iteration):**

```python
def make_fn(val):
    return lambda: val

functions = [make_fn(i) for i in range(5)]
print([f() for f in functions])
# Output: [0, 1, 2, 3, 4]
```

### Step 6: Functions as first-class objects

Functions in Python are objects with attributes. You can assign them, store them in data structures, and inspect them.

```python
def add(a, b):
    """Add two numbers."""
    return a + b

# Functions have attributes
print(add.__name__)    # add
print(add.__doc__)     # Add two numbers.

# Assign to a variable
plus = add
print(plus(3, 4))      # 7

# Store in a data structure
operations = {
    "+": add,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
}

for op, fn in operations.items():
    print(f"10 {op} 3 = {fn(10, 3)}")
# Output:
# 10 + 3 = 13
# 10 - 3 = 7
# 10 * 3 = 30

# Pass as an argument
def apply_op(fn, a, b):
    return fn(a, b)

print(apply_op(add, 5, 3))  # 8
```

### Step 7: Higher-order functions

A higher-order function either takes a function as an argument, returns a function, or both.

```python
# Takes a function: apply_to_all
def apply_to_all(fn, items):
    """Apply fn to each item, return results."""
    return [fn(item) for item in items]

print(apply_to_all(str.upper, ["hello", "world"]))
# Output: ['HELLO', 'WORLD']
print(apply_to_all(len, ["hello", "world", "hi"]))
# Output: [5, 5, 2]

# Returns a function: compose
def compose(f, g):
    """compose(f, g)(x) == f(g(x))"""
    def composed(x):
        return f(g(x))
    return composed

shout = compose(str.upper, str.strip)
print(shout("  hello  "))
# Output: HELLO

# Takes AND returns a function: logging wrapper
def with_logging(fn):
    def wrapper(*args, **kwargs):
        print(f"Calling {fn.__name__}({args}, {kwargs})")
        result = fn(*args, **kwargs)
        print(f"  -> {result}")
        return result
    return wrapper

logged_add = with_logging(add)
logged_add(3, 4)
# Output:
# Calling add((3, 4), {})
#   -> 7
```

### Step 8: `functools.partial` -- pre-filling arguments

`partial` creates a new function with some arguments frozen. It's cleaner than lambda for simple cases and preserves function metadata.

```python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube = partial(power, exponent=3)

print(square(5))  # 25
print(cube(3))    # 27

# partial preserves info about the original function
print(square.func)      # <function power at ...>
print(square.keywords)  # {'exponent': 2}

# Practical: create specialized loggers
def log(level, message, timestamp="N/A"):
    print(f"[{level}] {timestamp}: {message}")

info = partial(log, "INFO")
error = partial(log, "ERROR")

info("Server started")       # [INFO] N/A: Server started
error("Connection failed")   # [ERROR] N/A: Connection failed
```

### Step 9: `functools.singledispatch` -- function overloading by type

`singledispatch` lets you define different implementations of a function based on the type of the first argument -- a form of function overloading.

```python
from functools import singledispatch

@singledispatch
def format_value(value):
    """Default: convert to string."""
    return str(value)

@format_value.register(int)
def _(value):
    return f"{value:,}"

@format_value.register(float)
def _(value):
    return f"{value:.2f}"

@format_value.register(list)
def _(value):
    items = ", ".join(format_value(v) for v in value)
    return f"[{items}]"

@format_value.register(dict)
def _(value):
    pairs = ", ".join(f"{k}: {format_value(v)}" for k, v in value.items())
    return f"{{{pairs}}}"

print(format_value(1234567))                    # 1,234,567
print(format_value(3.14159))                    # 3.14
print(format_value([1, 2.5, "hello"]))          # [1, 2.50, hello]
print(format_value({"age": 30, "pi": 3.14}))   # {age: 30, pi: 3.14}
```

### Step 10: Lambda expressions -- when to use and when NOT to

Lambda creates an anonymous function with a single expression. Use it for short, throwaway callbacks. Never assign a lambda to a variable -- use `def` instead.

```python
# GOOD: lambda as a sort key
names = ["Alice", "bob", "Carol", "dave"]
sorted_names = sorted(names, key=lambda s: s.lower())
print(sorted_names)
# Output: ['Alice', 'bob', 'Carol', 'dave']

# GOOD: lambda in higher-order functions
pairs = [(1, "b"), (3, "a"), (2, "c")]
sorted_pairs = sorted(pairs, key=lambda p: p[1])
print(sorted_pairs)
# Output: [(3, 'a'), (1, 'b'), (2, 'c')]

# BAD: assigning a lambda to a variable -- use def instead
# square = lambda x: x ** 2   # Don't do this

# GOOD: def for named functions
def square(x):
    return x ** 2

# BAD: complex lambda -- hard to read
# transform = lambda x: x ** 2 + 3 * x - 1 if x > 0 else abs(x)  # Don't

# GOOD: named function for complex logic
def transform(x):
    if x > 0:
        return x ** 2 + 3 * x - 1
    return abs(x)
```

**Rule of thumb:** If you need to give it a name, use `def`. Lambda is for anonymous, inline, single-expression callbacks.

### Step 11: Callable objects -- `__call__`

Any object with a `__call__` method is callable. This lets you create function-like objects that carry state and support additional methods.

```python
class Accumulator:
    """A callable that accumulates values."""

    def __init__(self, start=0):
        self.total = start
        self.history = []

    def __call__(self, value):
        self.total += value
        self.history.append(value)
        return self.total

    def reset(self):
        self.total = 0
        self.history.clear()

    def __repr__(self):
        return f"Accumulator(total={self.total}, calls={len(self.history)})"

acc = Accumulator()
print(acc(10))    # 10
print(acc(20))    # 30
print(acc(5))     # 35
print(acc)        # Accumulator(total=35, calls=3)
print(acc.history)  # [10, 20, 5]

# callable() checks if an object is callable
print(callable(acc))     # True
print(callable(42))      # False
print(callable(print))   # True
```

**When to use callable objects vs closures:**

- **Closure:** simple stateful function, no need for methods or introspection.
- **Callable object:** when you need methods (`reset`, `get_stats`), serialization, or complex state.

## Playground

Run the full interactive demo:

```bash
python playground/10_closures_scoping.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Closure mechanics

When Python compiles a nested function, it detects which variables are referenced from enclosing scopes. These are stored as "cell" objects in the function's `__closure__` tuple. When the function is called, it reads/writes through these cell objects, which are shared references -- not copies.

```
make_greeter("Hello")
  → creates local variable greeting = "Hello"
  → compiles greet() which references greeting
  → greeting becomes a cell object (shared reference)
  → returns greet function with __closure__ = (cell(greeting),)
  → make_greeter's frame is destroyed, but cell keeps greeting alive
```

### LEGB resolution order

```
Name lookup: x
  1. Local scope     → current function's locals
  2. Enclosing scope → outer function(s), inner to outer
  3. Global scope    → module-level names
  4. Built-in scope  → builtins module (len, print, etc.)
  → NameError if not found in any scope
```

### Closure vs class

Both closures and classes encapsulate state with behavior. Closures are lighter weight; classes are more explicit and support inheritance, protocols, and rich introspection.

| Feature | Closure | Callable Class |
|---|---|---|
| State | Captured variables | Instance attributes |
| Methods | Attach to function object (hacky) | Normal methods |
| Introspection | `__closure__`, cells | Normal attributes |
| Inheritance | No | Yes |
| Serialization (pickle) | Difficult | Easy |
| Weight | Lighter | Heavier |

## Exercises

### Exercise 1: Build a middleware chain using closures

Create a `middleware_chain` function that composes a list of middleware functions. Each middleware takes a handler and returns a new handler:

```python
def middleware_chain(handler, middlewares):
    """Apply middlewares to a handler, outermost first."""
    # Each middleware is: middleware(handler) -> new_handler
    # Apply in reverse so the first middleware in the list is outermost
    ...

def logging_middleware(handler):
    def wrapper(request):
        print(f"  LOG: Processing {request}")
        response = handler(request)
        print(f"  LOG: Response: {response}")
        return response
    return wrapper

def auth_middleware(handler):
    def wrapper(request):
        if "token" not in request:
            return {"error": "unauthorized"}
        return handler(request)
    return wrapper

def uppercase_middleware(handler):
    def wrapper(request):
        response = handler(request)
        if "body" in response:
            response["body"] = response["body"].upper()
        return response
    return wrapper

def my_handler(request):
    return {"body": f"Hello, {request['user']}!"}

chain = middleware_chain(my_handler, [logging_middleware, auth_middleware, uppercase_middleware])
print(chain({"user": "Alice", "token": "abc123"}))
# Expected: {"body": "HELLO, ALICE!"}
```

### Exercise 2: Implement a simple event system

Build an event system using closures and first-class functions:

```python
def create_event_system():
    """Create an event system with on(), off(), and emit()."""
    # Return a dict/namespace with on, off, and emit functions
    # on(event, callback) -- register a callback
    # off(event, callback) -- remove a callback
    # emit(event, *args, **kwargs) -- call all callbacks for the event
    ...

events = create_event_system()
events["on"]("login", lambda user: print(f"  {user} logged in"))
events["on"]("login", lambda user: print(f"  Sending welcome email to {user}"))
events["emit"]("login", "Alice")
# Expected:
#   Alice logged in
#   Sending welcome email to Alice
```

## What's Next

In [Kata 11 -- Classes & Inheritance](./11-classes-inheritance.md), we'll dive deep into Python's class system -- `__init__`, `__repr__`, class vs instance attributes, single and multiple inheritance, MRO (Method Resolution Order), and the `super()` function. You'll build a class hierarchy that models real-world entities with clean, Pythonic OOP.

---

[prev: 09-error-handling](./09-error-handling.md) | [next: 11-classes-inheritance](./11-classes-inheritance.md)
