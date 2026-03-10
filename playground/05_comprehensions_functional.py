"""
Kata 05 -- Comprehensions & Functional Style
Run: python playground/05_comprehensions_functional.py

Master Python comprehensions (list, dict, set, nested) and functional tools
(map, filter, reduce, partial, operator module, walrus operator).
"""

from functools import reduce, partial
from operator import itemgetter, attrgetter, methodcaller
import json
import math


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: List comprehensions ---
    print("--- Section 1: List Comprehensions ---")

    # Basic: squares
    squares = [x ** 2 for x in range(1, 11)]
    print(f"Squares: {squares}")
    # Output: Squares: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
    assert squares == [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

    # With filter condition
    even_squares = [x ** 2 for x in range(1, 11) if x % 2 == 0]
    print(f"Even squares: {even_squares}")
    # Output: Even squares: [4, 16, 36, 64, 100]
    assert even_squares == [4, 16, 36, 64, 100]

    # Multiple filter conditions (AND)
    fizzbuzz = [x for x in range(1, 31) if x % 3 == 0 if x % 5 == 0]
    print(f"FizzBuzz (div by 3 AND 5): {fizzbuzz}")
    # Output: FizzBuzz (div by 3 AND 5): [15, 30]
    assert fizzbuzz == [15, 30]

    # Conditional expression (if/else BEFORE for)
    labels = ["even" if x % 2 == 0 else "odd" for x in range(1, 6)]
    print(f"Labels: {labels}")
    # Output: Labels: ['odd', 'even', 'odd', 'even', 'odd']
    assert labels == ["odd", "even", "odd", "even", "odd"]

    print()

    # --- Section 2: Nested comprehensions ---
    print("--- Section 2: Nested Comprehensions ---")

    # Flatten a matrix
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    flat = [x for row in matrix for x in row]
    print(f"Flat matrix: {flat}")
    # Output: Flat matrix: [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert flat == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Cross-product
    ranks = ["A", "K", "Q"]
    suits = ["\u2660", "\u2665"]
    cards = [f"{r}{s}" for r in ranks for s in suits]
    print(f"Cards: {cards}")
    # Output: Cards: ['A♠', 'A♥', 'K♠', 'K♥', 'Q♠', 'Q♥']
    assert len(cards) == 6
    assert cards[0] == "A\u2660"

    # Nested with filter
    pairs = [(x, y) for x in range(4) for y in range(4) if x != y]
    print(f"Pairs (x != y): {pairs}")
    # Output: Pairs (x != y): [(0, 1), (0, 2), (0, 3), (1, 0), ...]
    assert len(pairs) == 12
    assert (0, 0) not in pairs

    print()

    # --- Section 3: Dict comprehensions ---
    print("--- Section 3: Dict Comprehensions ---")

    # Word lengths
    words = ["hello", "world", "python", "kata"]
    word_lengths = {w: len(w) for w in words}
    print(f"Word lengths: {word_lengths}")
    # Output: Word lengths: {'hello': 5, 'world': 5, 'python': 6, 'kata': 4}
    assert word_lengths == {"hello": 5, "world": 5, "python": 6, "kata": 4}

    # Invert a dict
    original = {"a": 1, "b": 2, "c": 3}
    inverted = {v: k for k, v in original.items()}
    print(f"Inverted: {inverted}")
    # Output: Inverted: {1: 'a', 2: 'b', 3: 'c'}
    assert inverted == {1: "a", 2: "b", 3: "c"}

    # Filter a dict
    scores = {"alice": 92, "bob": 67, "carol": 85, "dave": 43}
    passing = {name: score for name, score in scores.items() if score >= 70}
    print(f"Passing: {passing}")
    # Output: Passing: {'alice': 92, 'carol': 85}
    assert passing == {"alice": 92, "carol": 85}

    # Grouping: words by first letter
    words = ["apple", "avocado", "banana", "blueberry", "cherry", "coconut"]
    first_letters = {w[0] for w in words}
    grouped = {ch: [w for w in words if w[0] == ch] for ch in sorted(first_letters)}
    print(f"Grouped: {grouped}")
    # Output: Grouped: {'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry'], 'c': ['cherry', 'coconut']}
    assert grouped["a"] == ["apple", "avocado"]
    assert grouped["b"] == ["banana", "blueberry"]
    assert grouped["c"] == ["cherry", "coconut"]

    print()

    # --- Section 4: Set comprehensions ---
    print("--- Section 4: Set Comprehensions ---")

    words = ["apple", "avocado", "banana", "blueberry", "cherry"]

    # Unique first characters
    first_chars = {w[0] for w in words}
    print(f"First chars: {sorted(first_chars)}")
    # Output: First chars: ['a', 'b', 'c']
    assert first_chars == {"a", "b", "c"}

    # Unique word lengths
    lengths = {len(w) for w in words}
    print(f"Unique lengths: {sorted(lengths)}")
    # Output: Unique lengths: [5, 6, 7, 9]
    assert lengths == {5, 6, 7, 9}

    print()

    # --- Section 5: map() and filter() ---
    print("--- Section 5: map() and filter() ---")

    # map with lambda
    nums = [1, 2, 3, 4, 5]
    doubled = list(map(lambda x: x * 2, nums))
    print(f"Doubled: {doubled}")
    # Output: Doubled: [2, 4, 6, 8, 10]
    assert doubled == [2, 4, 6, 8, 10]

    # map with existing function (cleaner than comprehension here)
    words = ["hello", "WORLD", "Python"]
    lowered = list(map(str.lower, words))
    print(f"Lowered: {lowered}")
    # Output: Lowered: ['hello', 'world', 'python']
    assert lowered == ["hello", "world", "python"]

    # filter with predicate
    evens = list(filter(lambda x: x % 2 == 0, range(1, 11)))
    print(f"Evens: {evens}")
    # Output: Evens: [2, 4, 6, 8, 10]
    assert evens == [2, 4, 6, 8, 10]

    # filter(None, ...) removes falsy values
    mixed = [0, 1, "", "hello", None, 42, [], [1]]
    truthy = list(filter(None, mixed))
    print(f"Truthy values: {truthy}")
    # Output: Truthy values: [1, 'hello', 42, [1]]
    assert truthy == [1, "hello", 42, [1]]

    # Chaining map + filter
    words = ["hello", "WORLD", "Python"]
    result = list(map(str.upper, filter(lambda w: len(w) > 4, words)))
    print(f"Chained map+filter: {result}")
    # Output: Chained map+filter: ['HELLO', 'WORLD', 'PYTHON']
    assert result == ["HELLO", "WORLD", "PYTHON"]

    # Same as comprehension
    result_comp = [w.upper() for w in words if len(w) > 4]
    assert result_comp == result

    print()

    # --- Section 6: functools.reduce() ---
    print("--- Section 6: functools.reduce() ---")

    # Sum (reduce is overkill -- use sum())
    total = reduce(lambda acc, x: acc + x, [1, 2, 3, 4, 5])
    print(f"Sum via reduce: {total}")
    # Output: Sum via reduce: 15
    assert total == 15

    # Product
    product = reduce(lambda acc, x: acc * x, [1, 2, 3, 4, 5])
    print(f"Product via reduce: {product}")
    # Output: Product via reduce: 120
    assert product == 120

    # Building nested dicts from a path
    def set_nested(path: list[str], value: str) -> dict:
        """Build a nested dict: ['a', 'b', 'c'] -> {'a': {'b': {'c': value}}}"""
        return reduce(lambda acc, key: {key: acc}, reversed(path), value)

    nested = set_nested(["config", "db", "host"], "localhost")
    print(f"Nested dict: {nested}")
    # Output: Nested dict: {'config': {'db': {'host': 'localhost'}}}
    assert nested == {"config": {"db": {"host": "localhost"}}}

    # Flatten lists
    nested_lists = [[1, 2], [3, 4], [5, 6]]
    flat = reduce(lambda acc, lst: acc + lst, nested_lists, [])
    print(f"Flattened: {flat}")
    # Output: Flattened: [1, 2, 3, 4, 5, 6]
    assert flat == [1, 2, 3, 4, 5, 6]

    print()

    # --- Section 7: functools.partial() ---
    print("--- Section 7: functools.partial() ---")

    # Create specialized functions
    def power(base, exponent):
        return base ** exponent

    square = partial(power, exponent=2)
    cube = partial(power, exponent=3)

    print(f"square(5) = {square(5)}")
    # Output: square(5) = 25
    assert square(5) == 25

    print(f"cube(3) = {cube(3)}")
    # Output: cube(3) = 27
    assert cube(3) == 27

    # partial for formatting
    pretty_json = partial(json.dumps, indent=2, sort_keys=True)
    data = {"name": "alice", "age": 30, "active": True}
    formatted = pretty_json(data)
    print(f"Pretty JSON:\n{formatted}")
    # Output:
    # Pretty JSON:
    # {
    #   "active": true,
    #   "age": 30,
    #   "name": "alice"
    # }
    assert '"active": true' in formatted

    # partial + map: convert strings to ints with a specific base
    to_hex = partial(int, base=16)
    hex_values = list(map(to_hex, ["ff", "a0", "1b"]))
    print(f"Hex values: {hex_values}")
    # Output: Hex values: [255, 160, 27]
    assert hex_values == [255, 160, 27]

    print()

    # --- Section 8: operator module ---
    print("--- Section 8: operator Module ---")

    # itemgetter: sort dicts by a key
    records = [
        {"name": "alice", "age": 30, "score": 92},
        {"name": "bob", "age": 25, "score": 67},
        {"name": "carol", "age": 35, "score": 85},
    ]

    by_score = sorted(records, key=itemgetter("score"), reverse=True)
    names_by_score = [r["name"] for r in by_score]
    print(f"By score (desc): {names_by_score}")
    # Output: By score (desc): ['alice', 'carol', 'bob']
    assert names_by_score == ["alice", "carol", "bob"]

    # Multi-key itemgetter
    get_name_score = itemgetter("name", "score")
    print(f"Name+score of first: {get_name_score(records[0])}")
    # Output: Name+score of first: ('alice', 92)
    assert get_name_score(records[0]) == ("alice", 92)

    # attrgetter: sort objects by attribute
    class Student:
        def __init__(self, name, grade):
            self.name = name
            self.grade = grade
        def __repr__(self):
            return f"Student({self.name!r}, {self.grade!r})"

    students = [Student("Alice", 92), Student("Bob", 67), Student("Carol", 85)]
    by_grade = sorted(students, key=attrgetter("grade"), reverse=True)
    print(f"By grade (desc): {by_grade}")
    # Output: By grade (desc): [Student('Alice', 92), Student('Carol', 85), Student('Bob', 67)]
    assert by_grade[0].name == "Alice"
    assert by_grade[1].name == "Carol"
    assert by_grade[2].name == "Bob"

    # methodcaller: call a method on each item
    words = ["  hello  ", "  world  ", "  python  "]
    stripped = list(map(methodcaller("strip"), words))
    print(f"Stripped: {stripped}")
    # Output: Stripped: ['hello', 'world', 'python']
    assert stripped == ["hello", "world", "python"]

    # methodcaller with arguments
    padded = list(map(methodcaller("center", 20, "-"), ["hello", "world"]))
    print(f"Padded: {padded}")
    # Output: Padded: ['-------hello--------', '-------world--------']
    assert padded[0] == "-------hello--------"
    assert padded[1] == "-------world--------"

    print()

    # --- Section 9: Walrus operator := in comprehensions ---
    print("--- Section 9: Walrus Operator := ---")

    # Without walrus: compute len(w) twice
    words = ["hi", "hello", "hey", "howdy", "hola"]
    result_no_walrus = [(w, len(w)) for w in words if len(w) > 3]
    print(f"Without walrus: {result_no_walrus}")
    # Output: Without walrus: [('hello', 5), ('howdy', 5), ('hola', 4)]

    # With walrus: compute once, use twice
    result_walrus = [(w, length) for w in words if (length := len(w)) > 3]
    print(f"With walrus: {result_walrus}")
    # Output: With walrus: [('hello', 5), ('howdy', 5), ('hola', 4)]
    assert result_walrus == [("hello", 5), ("howdy", 5), ("hola", 4)]
    assert result_walrus == result_no_walrus

    # Walrus with expensive computation
    values = [1, -4, 9, -16, 25, -36]
    roots = [root for x in values if x > 0 if (root := math.sqrt(x)) > 2]
    print(f"Roots > 2: {roots}")
    # Output: Roots > 2: [3.0, 5.0]
    assert roots == [3.0, 5.0]

    print()

    # --- Section 10: Decision guide ---
    print("--- Section 10: When to Use What ---")
    print()
    print("  Comprehensions  -> simple transform + optional filter")
    print("  map/filter      -> existing named function (str.lower, int, etc.)")
    print("  for loop        -> complex logic, side effects, multiple statements")
    print("  reduce          -> genuine fold/accumulate pattern")
    print("  partial         -> freeze some args of an existing function")
    print("  operator module -> sort keys, data extraction from dicts/objects")
    print("  walrus :=       -> avoid redundant computation in comprehensions")

    print()

    # --- Section 11: Exercise solutions ---
    print("--- Section 11: Exercise -- Flatten Nested Data ---")

    students_data = [
        {"name": "Alice", "courses": ["Math", "Physics"]},
        {"name": "Bob", "courses": ["Math", "Chemistry", "Biology"]},
        {"name": "Carol", "courses": ["Physics", "Biology"]},
    ]
    enrollments = [
        (s["name"], course)
        for s in students_data
        for course in s["courses"]
    ]
    print(f"Enrollments: {enrollments}")
    # Output: [('Alice', 'Math'), ('Alice', 'Physics'), ('Bob', 'Math'), ...]
    assert len(enrollments) == 7
    assert enrollments[0] == ("Alice", "Math")
    assert enrollments[-1] == ("Carol", "Biology")

    print()

    print("--- Section 12: Exercise -- Pipeline with map/filter/reduce ---")

    transactions = [
        {"id": 1, "status": "completed", "amount": 120.50},
        {"id": 2, "status": "pending", "amount": 45.00},
        {"id": 3, "status": "completed", "amount": 89.99},
        {"id": 4, "status": "cancelled", "amount": 200.00},
        {"id": 5, "status": "completed", "amount": 30.00},
        {"id": 6, "status": "completed", "amount": 75.25},
    ]

    # Pipeline: filter completed -> filter amount > 50 -> extract amounts -> sum
    completed = filter(lambda t: t["status"] == "completed", transactions)
    over_50 = filter(lambda t: t["amount"] > 50, completed)
    amounts = map(itemgetter("amount"), over_50)
    total = reduce(lambda acc, x: acc + x, amounts)
    print(f"Total of completed orders > $50: ${total:.2f}")
    # Output: Total of completed orders > $50: $285.74
    assert abs(total - 285.74) < 0.01

    print()

    print("--- Section 13: Exercise -- compose() with reduce ---")

    def compose(*fns):
        """compose(f, g, h)(x) == f(g(h(x)))"""
        return reduce(lambda f, g: lambda x: f(g(x)), fns)

    add1 = lambda x: x + 1
    double = lambda x: x * 2
    negate = lambda x: -x

    transform = compose(negate, double, add1)
    result = transform(5)
    print(f"compose(negate, double, add1)(5) = {result}")
    # Output: compose(negate, double, add1)(5) = -12
    assert result == -12  # add1(5)=6, double(6)=12, negate(12)=-12

    # Compose works with any number of functions
    transform2 = compose(str, abs, negate, double)
    result2 = transform2(7)
    print(f"compose(str, abs, negate, double)(7) = {result2!r}")
    # Output: compose(str, abs, negate, double)(7) = '14'
    assert result2 == "14"  # double(7)=14, negate(14)=-14, abs(-14)=14, str(14)='14'

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Comprehensions & functional tools in Python:")
    print("  - List/dict/set comprehensions for declarative collection building")
    print("  - Nested comprehensions for flattening and cross-products")
    print("  - map() and filter() for lazy transforms with existing functions")
    print("  - functools.reduce() for accumulation patterns")
    print("  - functools.partial() for function specialization")
    print("  - operator module for fast, readable sort keys and extractors")
    print("  - Walrus operator := to avoid redundant computation")
    print()
    print("All 13 sections passed. You've mastered comprehensions & functional style!")
