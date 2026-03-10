"""
Kata 02 -- Iterators & Generators
Run: python playground/skeletons/02_iterators_generators.py

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
        # TODO: return a new RangeIterator with start, stop, step
        pass

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
        # TODO: return self
        # HINT: this is what makes an iterator usable in a for-loop directly
        pass

    def __next__(self) -> int:
        """Return the next value, or raise StopIteration when done."""
        # TODO: if _current >= _stop, raise StopIteration
        #       otherwise, save _current, advance by _step, return saved value
        # HINT: save the value before incrementing!
        pass


# ---------------------------------------------------------------------------
# Generator function: fibonacci
# ---------------------------------------------------------------------------

def fibonacci(limit: int | None = None):
    """Generate Fibonacci numbers, optionally up to a limit.

    Uses yield to lazily produce values one at a time.
    """
    # TODO: start with a=0, b=1
    #       while limit is None or a < limit: yield a, then update a, b
    # HINT: a, b = b, a + b is the Fibonacci recurrence
    pass


# ---------------------------------------------------------------------------
# Generator pipelines
# ---------------------------------------------------------------------------

def read_lines(lines):
    """Stage 1: yield each line stripped of whitespace."""
    # TODO: for each line, yield line.strip()
    pass


def filter_comments(lines):
    """Stage 2: skip lines starting with #."""
    # TODO: for each line, yield it only if it doesn't start with '#'
    pass


def to_upper(lines):
    """Stage 3: convert each line to uppercase."""
    # TODO: for each line, yield line.upper()
    pass


# ---------------------------------------------------------------------------
# Exercise solutions: chunked and flatten
# ---------------------------------------------------------------------------

def chunked(iterable, size: int):
    """Yield successive chunks of `size` items from any iterable.

    The last chunk may be smaller than `size`.
    """
    # TODO: convert iterable to an iterator with iter()
    #       in a loop, take `size` items using itertools.islice
    #       if the chunk is empty, return; otherwise yield the chunk
    # HINT: chunk = list(itertools.islice(it, size))
    pass


def flatten(iterable):
    """Recursively flatten nested iterables (except strings).

    Strings are treated as atoms, not sequences of characters.
    """
    # TODO: for each item, check if it's iterable (but not str/bytes)
    #       if iterable: yield from flatten(item)
    #       otherwise: yield item
    # HINT: use hasattr(item, '__iter__') to check iterability
    #       use isinstance(item, (str, bytes)) to exclude strings
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Manual Iterator Protocol ---
    print("--- Manual Iterator Protocol ---")
    try:
        r = Range(0, 5)

        result1 = list(r)
        print(f"list(Range(0, 5)): {result1}")
        assert result1 == [0, 1, 2, 3, 4]

        result2 = list(r)
        print(f"Second iteration:  {result2}")
        assert result2 == [0, 1, 2, 3, 4]

        result3 = list(Range(0, 10, 2))
        print(f"Range(0, 10, 2):   {result3}")
        assert result3 == [0, 2, 4, 6, 8]

        it = iter(Range(1, 4))
        print(f"next(it) = {next(it)}")
        print(f"next(it) = {next(it)}")
        print(f"next(it) = {next(it)}")

        try:
            next(it)
            assert False, "Should have raised StopIteration"
        except StopIteration:
            print("next(it) -> StopIteration (iterator exhausted)")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Generator Functions ---
    print("--- Generator Functions ---")
    try:
        fib_list = list(fibonacci(100))
        print(f"fibonacci(100): {fib_list}")
        assert fib_list == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

        fib = fibonacci()
        first_10 = list(itertools.islice(fib, 10))
        print(f"First 10 fibonacci: {first_10}")
        assert first_10 == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

        gen = fibonacci(10)
        print(f"Type: {type(gen)}")
        assert hasattr(gen, "__iter__")
        assert hasattr(gen, "__next__")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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
    print(f"Generator size: {gen_size:>8,} bytes")

    assert gen_size < list_size, "Generator should use much less memory"
    print(f"Memory ratio:   {list_size / gen_size:.0f}x more for list")

    total = sum(x ** 2 for x in range(1000))
    print(f"sum(x**2 for x in range(1000)) = {total}")
    assert total == 332833500

    list_result = [x * 2 for x in range(5)]
    gen_result = list(x * 2 for x in range(5))
    print(f"List comp: {list_result}")
    print(f"Gen expr:  {gen_result}")
    assert list_result == gen_result

    print()

    # --- Section 4: itertools ---
    print("--- itertools ---")

    chained = list(itertools.chain([1, 2], [3, 4], [5]))
    print(f"chain([1,2], [3,4], [5]): {chained}")
    assert chained == [1, 2, 3, 4, 5]

    nested = [[1, 2], [3, 4], [5, 6]]
    flat = list(itertools.chain.from_iterable(nested))
    print(f"chain.from_iterable: {flat}")
    assert flat == [1, 2, 3, 4, 5, 6]

    try:
        fib = fibonacci()
        sliced = list(itertools.islice(fib, 3, 8))
        print(f"islice(fibonacci(), 3, 8): {sliced}")
        assert sliced == [2, 3, 5, 8, 13]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (fibonacci): {e}")

    counter = itertools.count(start=10, step=3)
    first_four = [next(counter) for _ in range(4)]
    print(f"count(10, 3): {first_four}")
    assert first_four == [10, 13, 16, 19]

    cycler = itertools.cycle(["A", "B", "C"])
    first_seven = [next(cycler) for _ in range(7)]
    print(f"cycle(['A','B','C']): {first_seven}")
    assert first_seven == ["A", "B", "C", "A", "B", "C", "A"]

    data = sorted(["apple", "avocado", "banana", "blueberry", "cherry"])
    print("groupby (first letter):")
    grouped = {}
    for letter, group in itertools.groupby(data, key=lambda w: w[0]):
        words = list(group)
        grouped[letter] = words
        print(f"  {letter}: {words}")
    assert grouped["a"] == ["apple", "avocado"]
    assert grouped["b"] == ["banana", "blueberry"]
    assert grouped["c"] == ["cherry"]

    print()

    # --- Section 5: Generator Pipelines ---
    print("--- Generator Pipelines ---")
    try:
        raw = ["  hello  ", "# comment", "  world  ", "# ignore", "  python  "]

        pipeline = to_upper(filter_comments(read_lines(raw)))
        result = list(pipeline)
        print(f"Pipeline result: {result}")
        assert result == ["HELLO", "WORLD", "PYTHON"]

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
        assert result == [0, 4, 16, 36, 64, 100, 144, 196]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: chunked() generator ---
    print("--- chunked() Generator ---")
    try:
        chunks = list(chunked([1, 2, 3, 4, 5, 6, 7], 3))
        print(f"chunked([1..7], 3): {chunks}")
        assert chunks == [[1, 2, 3], [4, 5, 6], [7]]

        chunks2 = list(chunked("abcdefg", 2))
        print(f"chunked('abcdefg', 2): {chunks2}")
        assert chunks2 == [["a", "b"], ["c", "d"], ["e", "f"], ["g"]]

        chunks3 = list(chunked(range(6), 3))
        print(f"chunked(range(6), 3): {chunks3}")
        assert chunks3 == [[0, 1, 2], [3, 4, 5]]

        chunks4 = list(chunked(fibonacci(20), 3))
        print(f"chunked(fibonacci(20), 3): {chunks4}")
        assert chunks4 == [[0, 1, 1], [2, 3, 5], [8, 13]]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: flatten() generator ---
    print("--- flatten() Generator ---")
    try:
        flat1 = list(flatten([1, [2, 3], [4, [5, 6]], 7]))
        print(f"flatten([1, [2,3], [4,[5,6]], 7]): {flat1}")
        assert flat1 == [1, 2, 3, 4, 5, 6, 7]

        flat2 = list(flatten([[1, 2], [[3]], [4, [5, [6]]]]))
        print(f"flatten([[1,2], [[3]], [4,[5,[6]]]]): {flat2}")
        assert flat2 == [1, 2, 3, 4, 5, 6]

        flat3 = list(flatten(["hello", ["world", ["python"]]]))
        print(f"flatten with strings: {flat3}")
        assert flat3 == ["hello", "world", "python"]

        assert list(flatten([])) == []
        assert list(flatten([1])) == [1]
        assert list(flatten([[], [[]]])) == []
        print("Edge cases (empty, nested empty): passed")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: Iterable vs Iterator ---
    print("--- Iterable vs Iterator ---")

    my_list = [1, 2, 3]
    print(f"list has __iter__: {hasattr(my_list, '__iter__')}")
    print(f"list has __next__: {hasattr(my_list, '__next__')}")

    my_iter = iter(my_list)
    print(f"iter(list) has __iter__: {hasattr(my_iter, '__iter__')}")
    print(f"iter(list) has __next__: {hasattr(my_iter, '__next__')}")

    assert iter(my_iter) is my_iter
    print(f"iter(iterator) is iterator: {iter(my_iter) is my_iter}")

    gen = (x for x in [1, 2, 3])
    first_pass = list(gen)
    second_pass = list(gen)
    print(f"Generator first pass:  {first_pass}")
    print(f"Generator second pass: {second_pass}")
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
