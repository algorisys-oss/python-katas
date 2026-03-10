# Kata 02 -- Iterators & Generators

[prev: 01-python-data-model](./01-python-data-model.md) | [next: 03-decorators-deep-dive](./03-decorators-deep-dive.md)

---

## What We're Building

In Kata 01 we saw that `__iter__` makes an object iterable. But what *is* an iterator, exactly? And why does Python have both `__iter__` and `__next__`? In this kata we go deep on the **iterator protocol** -- the two-method contract that powers every `for` loop, list comprehension, and unpacking operation in Python.

Then we discover **generators** -- Python's most elegant tool for producing sequences lazily. Instead of building an entire list in memory, a generator yields one value at a time, pausing and resuming its execution on demand. This is the foundation of memory-efficient data processing pipelines.

By the end you'll be able to build custom iterators, write generator functions and expressions, compose generator pipelines, and use `itertools` to solve real problems.

## Concepts You'll Learn

| Concept | What It Does |
|---|---|
| `__iter__` | Returns an iterator object (often `self`) |
| `__next__` | Returns the next value, or raises `StopIteration` |
| `StopIteration` | Signal that the iterator is exhausted |
| `yield` | Pauses a function, turning it into a generator |
| Generator expressions | Lazy comprehensions: `(x for x in items)` |
| `itertools` | Standard library of iterator building blocks |
| Generator pipelines | Chaining generators for streaming data processing |

## The Code

### Step 1: The iterator protocol -- `__iter__` and `__next__`

When Python encounters `for x in obj:`, here's what actually happens:

```
for x in obj:       1. iterator = obj.__iter__()
    do_something()   2. x = iterator.__next__()   ← called repeatedly
                     3. StopIteration raised       ← loop ends
```

An **iterable** is any object with `__iter__`. An **iterator** is any object with both `__iter__` (returning `self`) and `__next__`. Let's build one from scratch -- a `Range` class that mimics Python's `range()`:

```python
class Range:
    """A custom range that implements the iterator protocol manually."""

    def __init__(self, start: int, stop: int, step: int = 1) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self):
        """Return a fresh iterator. Each for-loop gets its own state."""
        return RangeIterator(self.start, self.stop, self.step)

    def __repr__(self) -> str:
        return f"Range({self.start}, {self.stop}, {self.step})"


class RangeIterator:
    """The actual iterator -- holds the current position."""

    def __init__(self, start: int, stop: int, step: int) -> None:
        self._current = start
        self._stop = stop
        self._step = step

    def __iter__(self):
        """Iterators return themselves -- this makes them work in for-loops."""
        return self

    def __next__(self) -> int:
        if self._current >= self._stop:
            raise StopIteration
        value = self._current
        self._current += self._step
        return value
```

**Why separate the iterable from the iterator?** Because you might want to iterate over the same object multiple times. Each call to `__iter__` returns a *fresh* iterator with its own position. If the iterable *were* its own iterator, a second `for` loop would resume from wherever the first one left off.

```python
r = Range(0, 5)

# First iteration
print(list(r))
# Output: [0, 1, 2, 3, 4]

# Second iteration -- works because __iter__ returns a fresh RangeIterator
print(list(r))
# Output: [0, 1, 2, 3, 4]
```

### Step 2: Generators -- `yield` makes everything simpler

Writing a separate iterator class every time is tedious. Python's `yield` keyword turns any function into a **generator function**. When called, it returns a generator object that implements `__iter__` and `__next__` automatically:

```python
def fibonacci(limit: int | None = None):
    """Generate Fibonacci numbers, optionally up to a limit."""
    a, b = 0, 1
    while limit is None or a < limit:
        yield a          # ← pauses here, returns a
        a, b = b, a + b  # ← resumes here on next __next__() call
```

Every time `yield` executes, the function **freezes** its entire state -- local variables, instruction pointer, everything. The next call to `__next__()` resumes exactly where it left off.

```python
# Get first 10 Fibonacci numbers
fib = fibonacci()
first_10 = [next(fib) for _ in range(10)]
print(first_10)
# Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# With a limit
print(list(fibonacci(100)))
# Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
```

### Step 3: Generator expressions vs list comprehensions

A list comprehension builds the entire list in memory. A generator expression is lazy -- it produces values one at a time:

```python
import sys

# List comprehension -- entire list in memory
squares_list = [x ** 2 for x in range(10_000)]

# Generator expression -- produces values on demand
squares_gen = (x ** 2 for x in range(10_000))

print(f"List size:      {sys.getsizeof(squares_list):>8,} bytes")
# Output: List size:        85,176 bytes

print(f"Generator size: {sys.getsizeof(squares_gen):>8,} bytes")
# Output: Generator size:       200 bytes
```

The generator expression uses a fixed ~200 bytes regardless of how many items it represents. Use generator expressions when you only need to iterate once and don't need random access.

**Rule of thumb:** Use `[]` when you need to access items by index or iterate multiple times. Use `()` when you're feeding data into another function like `sum()`, `max()`, or `"".join()`.

```python
# Generator expressions work great as function arguments
total = sum(x ** 2 for x in range(1000))  # no extra [] needed
print(f"Sum of squares: {total}")
# Output: Sum of squares: 332833500
```

### Step 4: `itertools` -- the standard library's iterator toolkit

The `itertools` module provides fast, memory-efficient building blocks for working with iterators. Here are the most useful ones:

```python
import itertools

# chain -- concatenate multiple iterables
combined = list(itertools.chain([1, 2], [3, 4], [5]))
print(f"chain: {combined}")
# Output: chain: [1, 2, 3, 4, 5]

# islice -- slice an iterator (which you can't do with [start:stop])
fib = fibonacci()
first_five_fib = list(itertools.islice(fib, 5))
print(f"islice fibonacci: {first_five_fib}")
# Output: islice fibonacci: [0, 1, 1, 2, 3]

# count -- infinite counter
counter = itertools.count(start=10, step=3)
first_four = [next(counter) for _ in range(4)]
print(f"count(10, 3): {first_four}")
# Output: count(10, 3): [10, 13, 16, 19]

# cycle -- repeat an iterable forever
cycler = itertools.cycle(["A", "B", "C"])
first_seven = [next(cycler) for _ in range(7)]
print(f"cycle: {first_seven}")
# Output: cycle: ['A', 'B', 'C', 'A', 'B', 'C', 'A']

# groupby -- group consecutive elements by a key
data = sorted(["apple", "avocado", "banana", "blueberry", "cherry"])
for letter, group in itertools.groupby(data, key=lambda w: w[0]):
    print(f"  {letter}: {list(group)}")
# Output:
#   a: ['apple', 'avocado']
#   b: ['banana', 'blueberry']
#   c: ['cherry']
```

**Important:** `groupby` only groups *consecutive* elements with the same key. If your data isn't sorted by the key, sort it first or you'll get multiple groups for the same key.

### Step 5: Generator pipelines -- composing data transformations

The real power of generators appears when you chain them together into **pipelines**. Each stage processes one item at a time, so you can handle datasets larger than memory:

```python
def read_lines(lines):
    """Stage 1: yield each line stripped."""
    for line in lines:
        yield line.strip()

def filter_comments(lines):
    """Stage 2: skip lines starting with #."""
    for line in lines:
        if not line.startswith("#"):
            yield line

def to_upper(lines):
    """Stage 3: convert to uppercase."""
    for line in lines:
        yield line.upper()

# Build the pipeline -- nothing executes yet!
raw = ["  hello  ", "# comment", "  world  ", "# ignore", "  python  "]
pipeline = to_upper(filter_comments(read_lines(raw)))

# Only now do values flow through all stages, one at a time
result = list(pipeline)
print(result)
# Output: ['HELLO', 'WORLD', 'PYTHON']
```

Each generator in the pipeline yields one value at a time. No intermediate lists are created. This is how tools like Unix pipes work, and it's the foundation of stream processing in Python.

## Playground

Run the full interactive demo:

```bash
python playground/02_iterators_generators.py
```

This script implements everything above and runs assertions to verify correctness. Every section is clearly labeled -- read the output to reinforce your understanding.

## How It Works

### The iterator protocol flow

```
for x in iterable:
    process(x)

Internally:
┌─────────────────────────────────────────────────────┐
│  iterator = iter(iterable)     # calls __iter__()   │
│                                                     │
│  loop:                                              │
│    try:                                             │
│      x = next(iterator)        # calls __next__()   │
│      process(x)                                     │
│    except StopIteration:                            │
│      break                     # loop ends          │
└─────────────────────────────────────────────────────┘
```

### Lazy evaluation

Generators use **lazy evaluation** -- they compute values only when asked. This has three benefits:

1. **Memory efficiency:** Only one value exists in memory at a time. A generator over 10 million items uses the same memory as a generator over 10 items.

2. **Time efficiency:** If you only need the first few values from a large computation, a generator stops early. A list comprehension computes everything upfront.

3. **Infinite sequences:** Generators can represent sequences that never end (like Fibonacci). You just take what you need with `islice()` or a `break`.

### Generator lifecycle

```
def gen():
    yield 1       ← suspended here after first next()
    yield 2       ← suspended here after second next()
    return        ← raises StopIteration

g = gen()         # creates generator object (GEN_CREATED)
next(g)  → 1      # runs to first yield (GEN_SUSPENDED)
next(g)  → 2      # resumes, runs to second yield (GEN_SUSPENDED)
next(g)  → StopIteration  # resumes, hits return (GEN_CLOSED)
```

### Iterable vs Iterator

```
Iterable                        Iterator
────────                        ────────
Has __iter__()                  Has __iter__() AND __next__()
Returns an iterator             __iter__() returns self
Can be iterated multiple times  Can only be consumed once
Examples: list, dict, str,      Examples: generator objects,
  Range, file objects              RangeIterator, map(), filter()
```

## Exercises

### Exercise 1: Implement `chunked()` -- split an iterable into fixed-size chunks

Write a generator function that yields chunks of a given size from any iterable:

```python
def chunked(iterable, size):
    """Yield successive chunks of `size` items from `iterable`."""
    ...

print(list(chunked([1, 2, 3, 4, 5, 6, 7], 3)))
# Output: [[1, 2, 3], [4, 5, 6], [7]]

print(list(chunked("abcdefg", 2)))
# Output: [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g']]
```

Hint: Use `iter()` to get an iterator, then use `itertools.islice` to take `size` items at a time. The generator should work with any iterable, not just sequences.

### Exercise 2: Implement `flatten()` -- recursively flatten nested iterables

Write a generator function that flattens arbitrarily nested lists:

```python
def flatten(iterable):
    """Recursively flatten nested iterables (except strings)."""
    ...

print(list(flatten([1, [2, 3], [4, [5, 6]], 7])))
# Output: [1, 2, 3, 4, 5, 6, 7]

print(list(flatten([[1, 2], [[3]], [4, [5, [6]]]])))
# Output: [1, 2, 3, 4, 5, 6]
```

Hint: Check if each element is iterable (but not a string!) using `hasattr(item, '__iter__')`. If it is, recursively `yield from flatten(item)`. Otherwise, just `yield item`.

### Exercise 3: Build a data processing pipeline

Create a pipeline of generators that processes a list of raw log entries:

```python
logs = [
    "  2024-01-15 INFO  User logged in  ",
    "  2024-01-15 DEBUG Connection pool stats  ",
    "  2024-01-15 ERROR Database timeout  ",
    "  2024-01-15 INFO  Request completed  ",
    "  2024-01-15 ERROR Disk space low  ",
]
```

Build generators for: strip whitespace, filter only ERROR lines, extract the message after the level, convert to uppercase. The final output should be `['DATABASE TIMEOUT', 'DISK SPACE LOW']`.

## What's Next

In [Kata 03 -- Decorators Deep Dive](./03-decorators-deep-dive.md), we'll explore another cornerstone of Pythonic code: decorators. You'll learn how closures work, build decorators with and without arguments, and understand `functools.wraps` -- the key to writing decorators that don't break introspection.

---

[prev: 01-python-data-model](./01-python-data-model.md) | [next: 03-decorators-deep-dive](./03-decorators-deep-dive.md)
