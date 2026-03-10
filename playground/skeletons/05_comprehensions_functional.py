"""
Kata 05 -- Comprehensions & Functional Style
Run: python playground/skeletons/05_comprehensions_functional.py

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
    try:
        # TODO: create a list of squares of 1..10 using a list comprehension
        # HINT: [x ** 2 for x in range(...)]
        squares = []  # replace this
        print(f"Squares: {squares}")
        assert squares == [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

        # TODO: create a list of squares of EVEN numbers 1..10 using a comprehension with a filter
        # HINT: add "if x % 2 == 0" after the for clause
        even_squares = []  # replace this
        print(f"Even squares: {even_squares}")
        assert even_squares == [4, 16, 36, 64, 100]

        # TODO: find all numbers 1..30 divisible by BOTH 3 and 5
        # HINT: you can chain multiple "if" conditions after the for clause
        fizzbuzz = []  # replace this
        print(f"FizzBuzz (div by 3 AND 5): {fizzbuzz}")
        assert fizzbuzz == [15, 30]

        # TODO: create labels "even" or "odd" for numbers 1..5
        # HINT: use a conditional expression BEFORE the for: "even" if ... else "odd"
        labels = []  # replace this
        print(f"Labels: {labels}")
        assert labels == ["odd", "even", "odd", "even", "odd"]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: Nested comprehensions ---
    print("--- Section 2: Nested Comprehensions ---")
    try:
        matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

        # TODO: flatten the matrix into a single list [1, 2, 3, 4, 5, 6, 7, 8, 9]
        # HINT: [x for row in matrix for x in row]
        flat = []  # replace this
        print(f"Flat matrix: {flat}")
        assert flat == [1, 2, 3, 4, 5, 6, 7, 8, 9]

        ranks = ["A", "K", "Q"]
        suits = ["\u2660", "\u2665"]

        # TODO: create all rank+suit combinations like ["A♠", "A♥", "K♠", ...]
        # HINT: [f"{r}{s}" for r in ranks for s in suits]
        cards = []  # replace this
        print(f"Cards: {cards}")
        assert len(cards) == 6
        assert cards[0] == "A\u2660"

        # TODO: create all (x, y) pairs where x != y, with x and y in range(4)
        # HINT: [(x, y) for x in range(4) for y in range(4) if x != y]
        pairs = []  # replace this
        print(f"Pairs (x != y): {pairs}")
        assert len(pairs) == 12
        assert (0, 0) not in pairs
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Dict comprehensions ---
    print("--- Section 3: Dict Comprehensions ---")
    try:
        words = ["hello", "world", "python", "kata"]

        # TODO: create a dict mapping each word to its length
        # HINT: {w: len(w) for w in words}
        word_lengths = {}  # replace this
        print(f"Word lengths: {word_lengths}")
        assert word_lengths == {"hello": 5, "world": 5, "python": 6, "kata": 4}

        original = {"a": 1, "b": 2, "c": 3}

        # TODO: invert the dict (swap keys and values)
        # HINT: {v: k for k, v in original.items()}
        inverted = {}  # replace this
        print(f"Inverted: {inverted}")
        assert inverted == {1: "a", 2: "b", 3: "c"}

        scores = {"alice": 92, "bob": 67, "carol": 85, "dave": 43}

        # TODO: filter to only passing scores (>= 70)
        # HINT: {name: score for name, score in scores.items() if ...}
        passing = {}  # replace this
        print(f"Passing: {passing}")
        assert passing == {"alice": 92, "carol": 85}

        # TODO: group these words by first letter
        words = ["apple", "avocado", "banana", "blueberry", "cherry", "coconut"]
        # HINT: first get unique first letters with a set comprehension,
        #       then build a dict where each key maps to a filtered list
        first_letters = set()  # replace this
        grouped = {}  # replace this
        print(f"Grouped: {grouped}")
        assert grouped.get("a") == ["apple", "avocado"]
        assert grouped.get("b") == ["banana", "blueberry"]
        assert grouped.get("c") == ["cherry", "coconut"]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Set comprehensions ---
    print("--- Section 4: Set Comprehensions ---")
    try:
        words = ["apple", "avocado", "banana", "blueberry", "cherry"]

        # TODO: get unique first characters using a set comprehension
        # HINT: {w[0] for w in words}
        first_chars = set()  # replace this
        print(f"First chars: {sorted(first_chars)}")
        assert first_chars == {"a", "b", "c"}

        # TODO: get unique word lengths using a set comprehension
        lengths = set()  # replace this
        print(f"Unique lengths: {sorted(lengths)}")
        assert lengths == {5, 6, 7, 9}
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: map() and filter() ---
    print("--- Section 5: map() and filter() ---")
    try:
        nums = [1, 2, 3, 4, 5]

        # TODO: double each number using map()
        # HINT: list(map(lambda x: x * 2, nums))
        doubled = []  # replace this
        print(f"Doubled: {doubled}")
        assert doubled == [2, 4, 6, 8, 10]

        words = ["hello", "WORLD", "Python"]

        # TODO: lowercase each word using map() with str.lower
        # HINT: list(map(str.lower, words))
        lowered = []  # replace this
        print(f"Lowered: {lowered}")
        assert lowered == ["hello", "world", "python"]

        # TODO: filter even numbers from 1..10
        # HINT: list(filter(lambda x: x % 2 == 0, range(1, 11)))
        evens = []  # replace this
        print(f"Evens: {evens}")
        assert evens == [2, 4, 6, 8, 10]

        # TODO: use filter(None, ...) to remove falsy values
        mixed = [0, 1, "", "hello", None, 42, [], [1]]
        truthy = []  # replace this
        print(f"Truthy values: {truthy}")
        assert truthy == [1, "hello", 42, [1]]

        # TODO: chain map + filter to uppercase words longer than 4 chars
        words = ["hello", "WORLD", "Python"]
        result = []  # replace this
        print(f"Chained map+filter: {result}")
        assert result == ["HELLO", "WORLD", "PYTHON"]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 6: functools.reduce() ---
    print("--- Section 6: functools.reduce() ---")
    try:
        # TODO: compute sum of [1,2,3,4,5] using reduce
        # HINT: reduce(lambda acc, x: acc + x, [1, 2, 3, 4, 5])
        total = 0  # replace this
        print(f"Sum via reduce: {total}")
        assert total == 15

        # TODO: compute product of [1,2,3,4,5] using reduce
        product = 0  # replace this
        print(f"Product via reduce: {product}")
        assert product == 120

        # TODO: build a nested dict from a path
        def set_nested(path: list[str], value: str) -> dict:
            """Build a nested dict: ['a', 'b', 'c'] -> {'a': {'b': {'c': value}}}"""
            # TODO: use reduce with reversed(path)
            # HINT: reduce(lambda acc, key: {key: acc}, reversed(path), value)
            pass

        nested = set_nested(["config", "db", "host"], "localhost")
        print(f"Nested dict: {nested}")
        assert nested == {"config": {"db": {"host": "localhost"}}}

        # TODO: flatten [[1,2],[3,4],[5,6]] using reduce
        # HINT: reduce(lambda acc, lst: acc + lst, nested_lists, [])
        nested_lists = [[1, 2], [3, 4], [5, 6]]
        flat = []  # replace this
        print(f"Flattened: {flat}")
        assert flat == [1, 2, 3, 4, 5, 6]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: functools.partial() ---
    print("--- Section 7: functools.partial() ---")
    try:
        def power(base, exponent):
            return base ** exponent

        # TODO: create square and cube using partial
        # HINT: partial(power, exponent=2)
        square = None  # replace this
        cube = None  # replace this

        print(f"square(5) = {square(5)}")
        assert square(5) == 25

        print(f"cube(3) = {cube(3)}")
        assert cube(3) == 27

        # TODO: create a pretty_json function using partial
        # HINT: partial(json.dumps, indent=2, sort_keys=True)
        pretty_json = None  # replace this
        data = {"name": "alice", "age": 30, "active": True}
        formatted = pretty_json(data)
        print(f"Pretty JSON:\n{formatted}")
        assert '"active": true' in formatted

        # TODO: create to_hex using partial(int, base=16), then map over hex strings
        to_hex = None  # replace this
        hex_values = []  # replace this
        print(f"Hex values: {hex_values}")
        assert hex_values == [255, 160, 27]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 8: operator module ---
    print("--- Section 8: operator Module ---")
    try:
        records = [
            {"name": "alice", "age": 30, "score": 92},
            {"name": "bob", "age": 25, "score": 67},
            {"name": "carol", "age": 35, "score": 85},
        ]

        # TODO: sort records by score descending using itemgetter
        # HINT: sorted(records, key=itemgetter("score"), reverse=True)
        by_score = []  # replace this
        names_by_score = [r["name"] for r in by_score]
        print(f"By score (desc): {names_by_score}")
        assert names_by_score == ["alice", "carol", "bob"]

        # TODO: create a multi-key itemgetter for "name" and "score"
        # HINT: itemgetter("name", "score")
        get_name_score = None  # replace this
        print(f"Name+score of first: {get_name_score(records[0])}")
        assert get_name_score(records[0]) == ("alice", 92)

        class Student:
            def __init__(self, name, grade):
                self.name = name
                self.grade = grade
            def __repr__(self):
                return f"Student({self.name!r}, {self.grade!r})"

        students = [Student("Alice", 92), Student("Bob", 67), Student("Carol", 85)]

        # TODO: sort students by grade descending using attrgetter
        # HINT: sorted(students, key=attrgetter("grade"), reverse=True)
        by_grade = []  # replace this
        print(f"By grade (desc): {by_grade}")
        assert by_grade[0].name == "Alice"
        assert by_grade[1].name == "Carol"
        assert by_grade[2].name == "Bob"

        # TODO: strip whitespace from words using methodcaller
        # HINT: list(map(methodcaller("strip"), words))
        words = ["  hello  ", "  world  ", "  python  "]
        stripped = []  # replace this
        print(f"Stripped: {stripped}")
        assert stripped == ["hello", "world", "python"]

        # TODO: center strings to width 20 with "-" fill using methodcaller
        # HINT: methodcaller("center", 20, "-")
        padded = []  # replace this
        print(f"Padded: {padded}")
        assert padded[0] == "-------hello--------"
        assert padded[1] == "-------world--------"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 9: Walrus operator := in comprehensions ---
    print("--- Section 9: Walrus Operator := ---")
    try:
        words = ["hi", "hello", "hey", "howdy", "hola"]

        # TODO: use the walrus operator to compute len(w) once, filter > 3, and include the length
        # HINT: [(w, length) for w in words if (length := len(w)) > 3]
        result_walrus = []  # replace this
        print(f"With walrus: {result_walrus}")
        assert result_walrus == [("hello", 5), ("howdy", 5), ("hola", 4)]

        # TODO: filter positive numbers, compute sqrt, keep only roots > 2
        # HINT: [root for x in values if x > 0 if (root := math.sqrt(x)) > 2]
        values = [1, -4, 9, -16, 25, -36]
        roots = []  # replace this
        print(f"Roots > 2: {roots}")
        assert roots == [3.0, 5.0]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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

    # --- Section 11: Exercise -- Flatten nested data ---
    print("--- Section 11: Exercise -- Flatten Nested Data ---")
    try:
        students_data = [
            {"name": "Alice", "courses": ["Math", "Physics"]},
            {"name": "Bob", "courses": ["Math", "Chemistry", "Biology"]},
            {"name": "Carol", "courses": ["Physics", "Biology"]},
        ]

        # TODO: create a flat list of (student_name, course) tuples
        # HINT: [(s["name"], course) for s in students_data for course in s["courses"]]
        enrollments = []  # replace this
        print(f"Enrollments: {enrollments}")
        assert len(enrollments) == 7
        assert enrollments[0] == ("Alice", "Math")
        assert enrollments[-1] == ("Carol", "Biology")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    print("--- Section 12: Exercise -- Pipeline with map/filter/reduce ---")
    try:
        transactions = [
            {"id": 1, "status": "completed", "amount": 120.50},
            {"id": 2, "status": "pending", "amount": 45.00},
            {"id": 3, "status": "completed", "amount": 89.99},
            {"id": 4, "status": "cancelled", "amount": 200.00},
            {"id": 5, "status": "completed", "amount": 30.00},
            {"id": 6, "status": "completed", "amount": 75.25},
        ]

        # TODO: build a pipeline using filter, filter, map, reduce
        # Step 1: filter completed transactions
        # Step 2: filter amount > 50
        # Step 3: extract amounts with map (use itemgetter("amount"))
        # Step 4: sum with reduce
        # HINT: chain filter -> filter -> map -> reduce
        total = 0  # replace this
        print(f"Total of completed orders > $50: ${total:.2f}")
        assert abs(total - 285.74) < 0.01
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    print("--- Section 13: Exercise -- compose() with reduce ---")
    try:
        # TODO: implement compose using reduce
        def compose(*fns):
            """compose(f, g, h)(x) == f(g(h(x)))"""
            # HINT: reduce(lambda f, g: lambda x: f(g(x)), fns)
            pass

        add1 = lambda x: x + 1
        double = lambda x: x * 2
        negate = lambda x: -x

        transform = compose(negate, double, add1)
        result = transform(5)
        print(f"compose(negate, double, add1)(5) = {result}")
        assert result == -12  # add1(5)=6, double(6)=12, negate(12)=-12

        transform2 = compose(str, abs, negate, double)
        result2 = transform2(7)
        print(f"compose(str, abs, negate, double)(7) = {result2!r}")
        assert result2 == "14"  # double(7)=14, negate(14)=-14, abs(-14)=14, str(14)='14'
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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
