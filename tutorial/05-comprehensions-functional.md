# Kata 05 -- Comprehensions & Functional Style

[prev: 04-context-managers](./04-context-managers.md) | [next: 06-type-hints-protocols](./06-type-hints-protocols.md)

---

## What We're Building

Python gives you two powerful paradigms for transforming data: **comprehensions** (a declarative, Pythonic syntax for building collections) and **functional tools** (`map`, `filter`, `reduce`, `partial`, `operator`). Mastering both -- and knowing when to reach for each -- is what separates fluent Python from "Python-shaped Java."

In this kata we'll build increasingly sophisticated data transformations, from simple list comprehensions through nested dict comprehensions, and then explore the functional toolkit in `functools` and `operator`. By the end you'll have a clear mental model for when to use comprehensions, when to use `map`/`filter`, and when a plain `for` loop is the right call.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| List comprehension | `[expr for x in iterable if cond]` | Transform + filter into a list |
| Dict comprehension | `{k: v for x in iterable}` | Build dicts from iterables |
| Set comprehension | `{expr for x in iterable}` | Unique transformed values |
| Nested comprehension | `[expr for x in outer for y in inner]` | Flatten / cross-product |
| `map(fn, iterable)` | Apply function to every item (lazy) | Simple 1:1 transforms, esp. with existing functions |
| `filter(fn, iterable)` | Keep items where `fn(item)` is truthy (lazy) | Select items with an existing predicate |
| `functools.reduce()` | Accumulate values left-to-right | Running totals, combining values |
| `functools.partial()` | Fix some arguments of a function | Function specialization, callbacks |
| `operator.itemgetter()` | Create a callable that fetches items by key/index | Sort keys, data extraction |
| `operator.attrgetter()` | Create a callable that fetches attributes | Sort keys for objects |
| `operator.methodcaller()` | Create a callable that calls a method | Transform pipelines |
| Walrus `:=` in comprehensions | Assign + use a value in the same expression | Avoid redundant computation |

## The Code

### Step 1: List comprehensions -- the bread and butter

A list comprehension replaces the pattern "create empty list, loop, append" with a single expression. The structure is always `[expression for variable in iterable if condition]`.

```python
# Basic: squares of 1-10
squares = [x ** 2 for x in range(1, 11)]
print(squares)
# Output: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

# With a condition: only even squares
even_squares = [x ** 2 for x in range(1, 11) if x % 2 == 0]
print(even_squares)
# Output: [4, 16, 36, 64, 100]

# Multiple conditions (AND logic -- all conditions must pass)
fizzbuzz = [x for x in range(1, 31) if x % 3 == 0 if x % 5 == 0]
print(fizzbuzz)
# Output: [15, 30]

# If/else in the expression (not the filter) -- conditional transform
labels = ["even" if x % 2 == 0 else "odd" for x in range(1, 6)]
print(labels)
# Output: ['odd', 'even', 'odd', 'even', 'odd']
```

**Key insight:** `if` after `for` is a *filter* (it decides whether to include the item). `if`/`else` before `for` is a *conditional expression* (it decides what value to produce). They're different things.

### Step 2: Nested comprehensions -- flattening and cross-products

When you have nested data, nested `for` clauses let you flatten in a single expression. The order reads left-to-right, just like nested `for` loops.

```python
# Flatten a matrix (list of lists)
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [x for row in matrix for x in row]
print(flat)
# Output: [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Cross-product: all (rank, suit) combinations
ranks = ["A", "K", "Q"]
suits = ["♠", "♥"]
cards = [f"{r}{s}" for r in ranks for s in suits]
print(cards)
# Output: ['A♠', 'A♥', 'K♠', 'K♥', 'Q♠', 'Q♥']

# Nested with filtering
pairs = [(x, y) for x in range(4) for y in range(4) if x != y]
print(pairs)
# Output: [(0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), ...]
```

**Reading order:** `for r in ranks for s in suits` means the outer loop is `ranks`, inner is `suits` -- exactly as if you wrote:

```python
result = []
for r in ranks:        # outer (first for)
    for s in suits:    # inner (second for)
        result.append(f"{r}{s}")
```

### Step 3: Dict comprehensions -- inverting and grouping

Dict comprehensions use the syntax `{key_expr: value_expr for x in iterable}`. They're perfect for transforming, inverting, and grouping data.

```python
# Basic: word → length
words = ["hello", "world", "python", "kata"]
word_lengths = {w: len(w) for w in words}
print(word_lengths)
# Output: {'hello': 5, 'world': 5, 'python': 6, 'kata': 4}

# Invert a dict (swap keys and values)
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
print(inverted)
# Output: {1: 'a', 2: 'b', 3: 'c'}

# Filter a dict: only items where value > threshold
scores = {"alice": 92, "bob": 67, "carol": 85, "dave": 43}
passing = {name: score for name, score in scores.items() if score >= 70}
print(passing)
# Output: {'alice': 92, 'carol': 85}

# Grouping with a dict comprehension + set
from collections import defaultdict

# Group words by their first letter (using defaultdict, not a pure comprehension)
words = ["apple", "avocado", "banana", "blueberry", "cherry", "coconut"]
groups = defaultdict(list)
for w in words:
    groups[w[0]].append(w)
print(dict(groups))
# Output: {'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry'], 'c': ['cherry', 'coconut']}

# But you CAN use a dict comprehension if you have the keys ahead of time:
first_letters = {ch for w in words for ch in w[0]}
grouped = {ch: [w for w in words if w[0] == ch] for ch in first_letters}
print(grouped)
# Output: {'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry'], 'c': ['cherry', 'coconut']}
```

### Step 4: Set comprehensions -- unique transformations

Set comprehensions use `{expr for x in iterable}` and automatically deduplicate results.

```python
# Unique first characters
words = ["apple", "avocado", "banana", "blueberry", "cherry"]
first_chars = {w[0] for w in words}
print(first_chars)
# Output: {'a', 'b', 'c'}

# Unique word lengths
lengths = {len(w) for w in words}
print(sorted(lengths))
# Output: [5, 6, 7, 9]
```

### Step 5: `map()` and `filter()` vs comprehensions

`map()` and `filter()` are lazy -- they return iterators, not lists. They shine when you already have a named function to apply.

```python
# map() applies a function to every item
nums = [1, 2, 3, 4, 5]
doubled = list(map(lambda x: x * 2, nums))
print(doubled)
# Output: [2, 4, 6, 8, 10]

# Same thing as a comprehension -- often more readable
doubled_comp = [x * 2 for x in nums]
print(doubled_comp)
# Output: [2, 4, 6, 8, 10]

# map() wins when you have an existing function
words = ["hello", "WORLD", "Python"]
lowered = list(map(str.lower, words))
print(lowered)
# Output: ['hello', 'world', 'python']

# filter() keeps items where the function returns True
evens = list(filter(lambda x: x % 2 == 0, range(1, 11)))
print(evens)
# Output: [2, 4, 6, 8, 10]

# filter(None, ...) removes falsy values
mixed = [0, 1, "", "hello", None, 42, [], [1]]
truthy = list(filter(None, mixed))
print(truthy)
# Output: [1, 'hello', 42, [1]]

# Chaining map + filter (lazy pipeline)
result = list(map(str.upper, filter(lambda w: len(w) > 4, words)))
print(result)
# Output: ['HELLO', 'WORLD', 'PYTHON']

# Same as comprehension -- usually clearer
result_comp = [w.upper() for w in words if len(w) > 4]
print(result_comp)
# Output: ['HELLO', 'WORLD', 'PYTHON']
```

**Rule of thumb:** Use comprehensions when the logic is simple and inline. Use `map()`/`filter()` when you have existing named functions (especially built-in methods like `str.lower`).

### Step 6: `functools.reduce()` -- accumulation patterns

`reduce()` applies a two-argument function cumulatively to items, reducing the iterable to a single value. It's powerful but can be hard to read -- use it deliberately.

```python
from functools import reduce

# Sum (reduce is overkill here -- use sum())
total = reduce(lambda acc, x: acc + x, [1, 2, 3, 4, 5])
print(total)
# Output: 15

# Product (no built-in, so reduce shines)
import math
product = reduce(lambda acc, x: acc * x, [1, 2, 3, 4, 5])
print(product)
# Output: 120
# (Python 3.8+ also has math.prod)

# Building a nested dict from a path
def set_nested(path: list[str], value: str) -> dict:
    """Build a nested dict: ['a', 'b', 'c'] → {'a': {'b': {'c': value}}}"""
    return reduce(lambda acc, key: {key: acc}, reversed(path), value)

print(set_nested(["config", "db", "host"], "localhost"))
# Output: {'config': {'db': {'host': 'localhost'}}}

# Flatten a list of lists
nested = [[1, 2], [3, 4], [5, 6]]
flat = reduce(lambda acc, lst: acc + lst, nested, [])
print(flat)
# Output: [1, 2, 3, 4, 5, 6]
# Note: for large data, use itertools.chain.from_iterable instead
```

### Step 7: `functools.partial()` -- function specialization

`partial()` freezes some arguments of a function, creating a new callable. It's a clean alternative to lambdas for simple cases.

```python
from functools import partial

# Create specialized functions from a general one
def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube = partial(power, exponent=3)

print(square(5))
# Output: 25
print(cube(3))
# Output: 27

# Useful for callbacks and map()
import json

# json.dumps with specific formatting
pretty_json = partial(json.dumps, indent=2, sort_keys=True)
data = {"name": "alice", "age": 30, "active": True}
print(pretty_json(data))
# Output:
# {
#   "active": true,
#   "age": 30,
#   "name": "alice"
# }

# partial + map: convert strings to ints with a specific base
to_hex = partial(int, base=16)
hex_values = list(map(to_hex, ["ff", "a0", "1b"]))
print(hex_values)
# Output: [255, 160, 27]
```

### Step 8: The `operator` module -- callable operators

The `operator` module provides function versions of Python operators. The most useful are `itemgetter`, `attrgetter`, and `methodcaller` -- they create lean, fast callables.

```python
from operator import itemgetter, attrgetter, methodcaller

# itemgetter: access items by key or index
records = [
    {"name": "alice", "age": 30, "score": 92},
    {"name": "bob", "age": 25, "score": 67},
    {"name": "carol", "age": 35, "score": 85},
]

# Sort by score (descending)
by_score = sorted(records, key=itemgetter("score"), reverse=True)
print([r["name"] for r in by_score])
# Output: ['alice', 'carol', 'bob']

# Multi-key itemgetter: extract multiple fields
get_name_score = itemgetter("name", "score")
print(get_name_score(records[0]))
# Output: ('alice', 92)

# attrgetter: access attributes on objects
class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade
    def __repr__(self):
        return f"Student({self.name!r}, {self.grade!r})"

students = [Student("Alice", 92), Student("Bob", 67), Student("Carol", 85)]
by_grade = sorted(students, key=attrgetter("grade"), reverse=True)
print(by_grade)
# Output: [Student('Alice', 92), Student('Carol', 85), Student('Bob', 67)]

# methodcaller: call a method with arguments
words = ["  hello  ", "  world  ", "  python  "]
stripped = list(map(methodcaller("strip"), words))
print(stripped)
# Output: ['hello', 'world', 'python']

# methodcaller with arguments
padded = list(map(methodcaller("center", 20, "-"), ["hello", "world"]))
print(padded)
# Output: ['-------hello--------', '-------world--------']
```

### Step 9: Walrus operator `:=` in comprehensions

The walrus operator (`:=`) lets you assign a value and use it in the same expression. In comprehensions, this avoids computing the same thing twice.

```python
# Without walrus: compute len(w) twice
words = ["hi", "hello", "hey", "howdy", "hola"]
result = [(w, len(w)) for w in words if len(w) > 3]
print(result)
# Output: [('hello', 5), ('howdy', 5), ('hola', 4)]

# With walrus: compute once, use twice
result = [(w, length) for w in words if (length := len(w)) > 3]
print(result)
# Output: [('hello', 5), ('howdy', 5), ('hola', 4)]

# Walrus with expensive computation
import math

# Filter and transform in one pass
values = [1, -4, 9, -16, 25, -36]
roots = [root for x in values if x > 0 if (root := math.sqrt(x)) > 2]
print(roots)
# Output: [3.0, 5.0]
```

### Step 10: When to use what -- the decision guide

```
Need a list/dict/set from an iterable?
├─ Simple transform + optional filter → Comprehension
├─ Already have a named function → map() / filter()
├─ Complex logic, side effects, or multiple statements → for loop
└─ Accumulating into a single value → reduce() or for loop

Need to pass a function somewhere?
├─ Simple expression → lambda
├─ Freezing some args of existing function → partial()
├─ Accessing a key/attr/method → operator (itemgetter, attrgetter, methodcaller)
└─ Complex logic → define a named function
```

**Guidelines:**
- Comprehensions are preferred in Python -- they're faster and more readable for simple cases.
- Never nest more than 2 levels of `for` in a comprehension -- use a loop instead.
- `map`/`filter` with `lambda` is almost always less readable than a comprehension.
- `map`/`filter` with a *named function* can be more readable than a comprehension.
- `reduce` is a power tool -- use it when the pattern genuinely is "fold left." Otherwise, use `sum()`, `min()`, `max()`, `any()`, `all()`, or a loop.

## Playground

Run the full interactive demo:

```bash
python playground/05_comprehensions_functional.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### Comprehension compilation

When Python encounters `[x * 2 for x in range(10)]`, it compiles the comprehension into a nested function call. The comprehension has its own scope -- variables defined in the `for` clause don't leak into the enclosing scope (unlike in Python 2).

```
[x * 2 for x in range(10)]
  → Python creates an anonymous function
  → calls it with the iterable as argument
  → the function builds and returns a list
  → x does NOT exist in the outer scope afterward
```

### Lazy vs eager

| Tool | Eager/Lazy | Returns |
|---|---|---|
| List comprehension `[...]` | Eager | `list` |
| Dict comprehension `{k:v ...}` | Eager | `dict` |
| Set comprehension `{...}` | Eager | `set` |
| Generator expression `(...)` | Lazy | `generator` |
| `map()` | Lazy | `map` iterator |
| `filter()` | Lazy | `filter` iterator |

Lazy tools are memory-efficient for large data -- they produce values one at a time. Eager tools build the entire collection in memory.

### Performance

Comprehensions are generally faster than equivalent `map(lambda, ...)` because they avoid the overhead of calling a Python function object on each iteration. When using `map` with a C-implemented function (like `str.lower` or `int`), `map` can be faster than a comprehension because it stays entirely in C.

## Exercises

### Exercise 1: Flatten nested data

Given a list of students with their courses, produce a flat list of `(student, course)` tuples:

```python
students = [
    {"name": "Alice", "courses": ["Math", "Physics"]},
    {"name": "Bob", "courses": ["Math", "Chemistry", "Biology"]},
    {"name": "Carol", "courses": ["Physics", "Biology"]},
]

# Expected output:
# [('Alice', 'Math'), ('Alice', 'Physics'), ('Bob', 'Math'), ('Bob', 'Chemistry'),
#  ('Bob', 'Biology'), ('Carol', 'Physics'), ('Carol', 'Biology')]
```

### Exercise 2: Build a data pipeline with map/filter/reduce

Process a list of transactions to compute the total value of "completed" orders over $50:

```python
from functools import reduce

transactions = [
    {"id": 1, "status": "completed", "amount": 120.50},
    {"id": 2, "status": "pending", "amount": 45.00},
    {"id": 3, "status": "completed", "amount": 89.99},
    {"id": 4, "status": "cancelled", "amount": 200.00},
    {"id": 5, "status": "completed", "amount": 30.00},
    {"id": 6, "status": "completed", "amount": 75.25},
]

# Step 1: filter for "completed" status
# Step 2: filter for amount > 50
# Step 3: extract amounts
# Step 4: reduce to sum
# Expected: 285.74
```

### Exercise 3: Implement a `compose()` function using reduce

Write a `compose()` function that takes multiple single-argument functions and returns a new function that applies them right-to-left:

```python
def compose(*fns):
    """compose(f, g, h)(x) == f(g(h(x)))"""
    # Use reduce to combine the functions
    ...

add1 = lambda x: x + 1
double = lambda x: x * 2
negate = lambda x: -x

transform = compose(negate, double, add1)
print(transform(5))
# Expected: -12  (add1(5)=6, double(6)=12, negate(12)=-12)
```

## What's Next

In [Kata 06 -- Type Hints & Protocols](./06-type-hints-protocols.md), we'll explore Python's type annotation system and structural subtyping with `Protocol`. You'll learn how to write self-documenting code that tools like mypy can verify at compile time -- without sacrificing Python's dynamic flexibility.

---

[prev: 04-context-managers](./04-context-managers.md) | [next: 06-type-hints-protocols](./06-type-hints-protocols.md)
