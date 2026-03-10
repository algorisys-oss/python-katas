"""
Kata 02 -- Iterators & Generators
Run: python playground/02_iterators_generators.py

Explore the iterator protocol (__iter__, __next__, StopIteration),
generator functions (yield), generator expressions, itertools, and
generator pipelines for memory-efficient data processing.
"""

import sys
import itertools


# ---------------------------------------------------------------------------
# Manual iterator: Range class implementing the iterator protocol
# ---------------------------------------------------------------------------

class Range:
    """A custom range that implements the iterator protocol manually.

    Separating the iterable (Range) from the iterator (RangeIterator)
    allows multiple independent iterations over the same object.
    """

    def __init__(self, start: int, stop: int, step: int = 1) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self):
        """Return a fresh iterator each time -- enables multiple for-loops."""
        return RangeIterator(self.start, self.stop, self.step)

    def __repr__(self) -> str:
        return f"Range({self.start}, {self.stop}, {self.step})"


class RangeIterator:
    """The iterator half of the protocol -- holds position state."""

    def __init__(self, start: int, stop: int, step: int) -> None:
        self._current = start
        self._stop = stop
        self._step = step

    def __iter__(self):
        """Iterators must return themselves."""
        return self

    def __next__(self) -> int:
        """Return the next value, or raise StopIteration when done."""
        if self._current >= self._stop:
            raise StopIteration
        value = self._current
        self._current += self._step
        return value


# ---------------------------------------------------------------------------
# Generator function: fibonacci
# ---------------------------------------------------------------------------

def fibonacci(limit: int | None = None):
    """Generate Fibonacci numbers, optionally up to a limit.

    Uses yield to lazily produce values one at a time.
    """
    a, b = 0, 1
    while limit is None or a < limit:
        yield a
        a, b = b, a + b


# ---------------------------------------------------------------------------
# Generator pipelines
# ---------------------------------------------------------------------------

def read_lines(lines):
    """Stage 1: yield each line stripped of whitespace."""
    for line in lines:
        yield line.strip()


def filter_comments(lines):
    """Stage 2: skip lines starting with #."""
    for line in lines:
        if not line.startswith("#"):
            yield line


def to_upper(lines):
    """Stage 3: convert each line to uppercase."""
    for line in lines:
        yield line.upper()


# ---------------------------------------------------------------------------
# Exercise solutions: chunked and flatten
# ---------------------------------------------------------------------------

def chunked(iterable, size: int):
    """Yield successive chunks of `size` items from any iterable.

    The last chunk may be smaller than `size`.
    """
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            return
        yield chunk


def flatten(iterable):
    """Recursively flatten nested iterables (except strings).

    Strings are treated as atoms, not sequences of characters.
    """
    for item in iterable:
        if hasattr(item, "__iter__") and not isinstance(item, (str, bytes)):
            yield from flatten(item)
        else:
            yield item


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Manual Iterator Protocol ---
    print("--- Manual Iterator Protocol ---")

    r = Range(0, 5)

    # First iteration
    result1 = list(r)
    print(f"list(Range(0, 5)): {result1}")
    # Output: list(Range(0, 5)): [0, 1, 2, 3, 4]
    assert result1 == [0, 1, 2, 3, 4]

    # Second iteration -- works because __iter__ returns a fresh iterator
    result2 = list(r)
    print(f"Second iteration:  {result2}")
    # Output: Second iteration:  [0, 1, 2, 3, 4]
    assert result2 == [0, 1, 2, 3, 4]

    # With step
    result3 = list(Range(0, 10, 2))
    print(f"Range(0, 10, 2):   {result3}")
    # Output: Range(0, 10, 2):   [0, 2, 4, 6, 8]
    assert result3 == [0, 2, 4, 6, 8]

    # Manual __next__ calls
    it = iter(Range(1, 4))
    print(f"next(it) = {next(it)}")
    # Output: next(it) = 1
    print(f"next(it) = {next(it)}")
    # Output: next(it) = 2
    print(f"next(it) = {next(it)}")
    # Output: next(it) = 3

    try:
        next(it)
        assert False, "Should have raised StopIteration"
    except StopIteration:
        print("next(it) -> StopIteration (iterator exhausted)")
        # Output: next(it) -> StopIteration (iterator exhausted)

    print()

    # --- Section 2: Generator Functions ---
    print("--- Generator Functions ---")

    # Fibonacci with limit
    fib_list = list(fibonacci(100))
    print(f"fibonacci(100): {fib_list}")
    # Output: fibonacci(100): [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    assert fib_list == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

    # Infinite fibonacci -- take first 10 using islice
    fib = fibonacci()
    first_10 = list(itertools.islice(fib, 10))
    print(f"First 10 fibonacci: {first_10}")
    # Output: First 10 fibonacci: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert first_10 == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    # A generator function returns a generator object
    gen = fibonacci(10)
    print(f"Type: {type(gen)}")
    # Output: Type: <class 'generator'>
    assert hasattr(gen, "__iter__")
    assert hasattr(gen, "__next__")

    print()

    # --- Section 3: Generator Expressions vs List Comprehensions ---
    print("--- Generator Expressions vs List Comprehensions ---")

    # List comprehension -- entire list in memory
    squares_list = [x ** 2 for x in range(10_000)]

    # Generator expression -- lazy, produces on demand
    squares_gen = (x ** 2 for x in range(10_000))

    list_size = sys.getsizeof(squares_list)
    gen_size = sys.getsizeof(squares_gen)

    print(f"List size:      {list_size:>8,} bytes")
    # Output: List size:        85,176 bytes
    print(f"Generator size: {gen_size:>8,} bytes")
    # Output: Generator size:       200 bytes

    assert gen_size < list_size, "Generator should use much less memory"
    print(f"Memory ratio:   {list_size / gen_size:.0f}x more for list")
    # Output: Memory ratio:   426x more for list

    # Generator expressions work as function arguments
    total = sum(x ** 2 for x in range(1000))
    print(f"sum(x**2 for x in range(1000)) = {total}")
    # Output: sum(x**2 for x in range(1000)) = 332833500
    assert total == 332833500

    # Both produce the same values
    list_result = [x * 2 for x in range(5)]
    gen_result = list(x * 2 for x in range(5))
    print(f"List comp: {list_result}")
    # Output: List comp: [0, 2, 4, 6, 8]
    print(f"Gen expr:  {gen_result}")
    # Output: Gen expr:  [0, 2, 4, 6, 8]
    assert list_result == gen_result

    print()

    # --- Section 4: itertools ---
    print("--- itertools ---")

    # chain -- concatenate multiple iterables
    chained = list(itertools.chain([1, 2], [3, 4], [5]))
    print(f"chain([1,2], [3,4], [5]): {chained}")
    # Output: chain([1,2], [3,4], [5]): [1, 2, 3, 4, 5]
    assert chained == [1, 2, 3, 4, 5]

    # chain.from_iterable -- flatten one level
    nested = [[1, 2], [3, 4], [5, 6]]
    flat = list(itertools.chain.from_iterable(nested))
    print(f"chain.from_iterable: {flat}")
    # Output: chain.from_iterable: [1, 2, 3, 4, 5, 6]
    assert flat == [1, 2, 3, 4, 5, 6]

    # islice -- slice an iterator (can't use [] on iterators)
    fib = fibonacci()
    sliced = list(itertools.islice(fib, 3, 8))
    print(f"islice(fibonacci(), 3, 8): {sliced}")
    # Output: islice(fibonacci(), 3, 8): [2, 3, 5, 8, 13]
    assert sliced == [2, 3, 5, 8, 13]

    # count -- infinite counter
    counter = itertools.count(start=10, step=3)
    first_four = [next(counter) for _ in range(4)]
    print(f"count(10, 3): {first_four}")
    # Output: count(10, 3): [10, 13, 16, 19]
    assert first_four == [10, 13, 16, 19]

    # cycle -- repeat forever
    cycler = itertools.cycle(["A", "B", "C"])
    first_seven = [next(cycler) for _ in range(7)]
    print(f"cycle(['A','B','C']): {first_seven}")
    # Output: cycle(['A','B','C']): ['A', 'B', 'C', 'A', 'B', 'C', 'A']
    assert first_seven == ["A", "B", "C", "A", "B", "C", "A"]

    # groupby -- group consecutive elements by a key (data must be sorted!)
    data = sorted(["apple", "avocado", "banana", "blueberry", "cherry"])
    print("groupby (first letter):")
    grouped = {}
    for letter, group in itertools.groupby(data, key=lambda w: w[0]):
        words = list(group)
        grouped[letter] = words
        print(f"  {letter}: {words}")
    # Output:
    #   a: ['apple', 'avocado']
    #   b: ['banana', 'blueberry']
    #   c: ['cherry']
    assert grouped["a"] == ["apple", "avocado"]
    assert grouped["b"] == ["banana", "blueberry"]
    assert grouped["c"] == ["cherry"]

    print()

    # --- Section 5: Generator Pipelines ---
    print("--- Generator Pipelines ---")

    raw = ["  hello  ", "# comment", "  world  ", "# ignore", "  python  "]

    # Build the pipeline -- nothing executes until we consume it
    pipeline = to_upper(filter_comments(read_lines(raw)))

    # Now values flow through all stages one at a time
    result = list(pipeline)
    print(f"Pipeline result: {result}")
    # Output: Pipeline result: ['HELLO', 'WORLD', 'PYTHON']
    assert result == ["HELLO", "WORLD", "PYTHON"]

    # More complex pipeline: number processing
    def evens(numbers):
        """Yield only even numbers."""
        for n in numbers:
            if n % 2 == 0:
                yield n

    def squared(numbers):
        """Yield each number squared."""
        for n in numbers:
            yield n ** 2

    def under_limit(numbers, limit):
        """Yield numbers below the limit."""
        for n in numbers:
            if n < limit:
                yield n

    pipe = under_limit(squared(evens(range(20))), limit=200)
    result = list(pipe)
    print(f"evens -> squared -> under 200: {result}")
    # Output: evens -> squared -> under 200: [0, 4, 16, 36, 64, 100, 144, 196]
    assert result == [0, 4, 16, 36, 64, 100, 144, 196]

    print()

    # --- Section 6: chunked() generator ---
    print("--- chunked() Generator ---")

    chunks = list(chunked([1, 2, 3, 4, 5, 6, 7], 3))
    print(f"chunked([1..7], 3): {chunks}")
    # Output: chunked([1..7], 3): [[1, 2, 3], [4, 5, 6], [7]]
    assert chunks == [[1, 2, 3], [4, 5, 6], [7]]

    chunks2 = list(chunked("abcdefg", 2))
    print(f"chunked('abcdefg', 2): {chunks2}")
    # Output: chunked('abcdefg', 2): [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g']]
    assert chunks2 == [["a", "b"], ["c", "d"], ["e", "f"], ["g"]]

    chunks3 = list(chunked(range(6), 3))
    print(f"chunked(range(6), 3): {chunks3}")
    # Output: chunked(range(6), 3): [[0, 1, 2], [3, 4, 5]]
    assert chunks3 == [[0, 1, 2], [3, 4, 5]]

    # Works with generators too
    chunks4 = list(chunked(fibonacci(20), 3))
    print(f"chunked(fibonacci(20), 3): {chunks4}")
    # Output: chunked(fibonacci(20), 3): [[0, 1, 1], [2, 3, 5], [8, 13]]
    assert chunks4 == [[0, 1, 1], [2, 3, 5], [8, 13]]

    print()

    # --- Section 7: flatten() generator ---
    print("--- flatten() Generator ---")

    flat1 = list(flatten([1, [2, 3], [4, [5, 6]], 7]))
    print(f"flatten([1, [2,3], [4,[5,6]], 7]): {flat1}")
    # Output: flatten([1, [2,3], [4,[5,6]], 7]): [1, 2, 3, 4, 5, 6, 7]
    assert flat1 == [1, 2, 3, 4, 5, 6, 7]

    flat2 = list(flatten([[1, 2], [[3]], [4, [5, [6]]]]))
    print(f"flatten([[1,2], [[3]], [4,[5,[6]]]]): {flat2}")
    # Output: flatten([[1,2], [[3]], [4,[5,[6]]]]): [1, 2, 3, 4, 5, 6]
    assert flat2 == [1, 2, 3, 4, 5, 6]

    # Strings are NOT flattened (treated as atoms)
    flat3 = list(flatten(["hello", ["world", ["python"]]]))
    print(f"flatten with strings: {flat3}")
    # Output: flatten with strings: ['hello', 'world', 'python']
    assert flat3 == ["hello", "world", "python"]

    # Empty and single-element cases
    assert list(flatten([])) == []
    assert list(flatten([1])) == [1]
    assert list(flatten([[], [[]]])) == []
    print("Edge cases (empty, nested empty): passed")
    # Output: Edge cases (empty, nested empty): passed

    print()

    # --- Section 8: Iterable vs Iterator ---
    print("--- Iterable vs Iterator ---")

    # A list is iterable but not an iterator
    my_list = [1, 2, 3]
    print(f"list has __iter__: {hasattr(my_list, '__iter__')}")
    # Output: list has __iter__: True
    print(f"list has __next__: {hasattr(my_list, '__next__')}")
    # Output: list has __next__: False

    # iter() gives us an iterator
    my_iter = iter(my_list)
    print(f"iter(list) has __iter__: {hasattr(my_iter, '__iter__')}")
    # Output: iter(list) has __iter__: True
    print(f"iter(list) has __next__: {hasattr(my_iter, '__next__')}")
    # Output: iter(list) has __next__: True

    # An iterator IS its own iterable (iter(it) returns itself)
    assert iter(my_iter) is my_iter
    print(f"iter(iterator) is iterator: {iter(my_iter) is my_iter}")
    # Output: iter(iterator) is iterator: True

    # Generators are iterators (single-use)
    gen = (x for x in [1, 2, 3])
    first_pass = list(gen)
    second_pass = list(gen)
    print(f"Generator first pass:  {first_pass}")
    # Output: Generator first pass:  [1, 2, 3]
    print(f"Generator second pass: {second_pass}")
    # Output: Generator second pass: []
    assert first_pass == [1, 2, 3]
    assert second_pass == []  # exhausted!

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("The iterator protocol gives Python its unified iteration model:")
    print("  - __iter__ returns an iterator")
    print("  - __next__ returns the next value or raises StopIteration")
    print("  - yield turns a function into a generator (automatic iterator)")
    print("  - Generator expressions: lazy comprehensions with ()")
    print("  - itertools: chain, islice, groupby, count, cycle, and more")
    print("  - Generator pipelines: compose generators for streaming processing")
    print()
    print("All 8 sections passed. You understand iterators and generators!")
