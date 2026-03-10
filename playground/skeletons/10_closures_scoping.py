"""
Kata 10 -- Closures, Scoping & First-Class Functions
Run: python playground/skeletons/10_closures_scoping.py

Master Python's scoping rules (LEGB), closures, nonlocal, higher-order functions,
functools.partial, functools.singledispatch, lambda, and callable objects.
"""

from functools import partial, singledispatch


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: LEGB scope rule ---
    print("--- Section 1: LEGB Scope Rule ---")

    x = "global"

    def outer():
        # TODO: assign x to "enclosing" in this scope
        pass

        def inner():
            # TODO: assign x to "local" in this scope
            pass
            print(f"  inner sees: {x}")

        inner()
        print(f"  outer sees: {x}")

    outer()
    print(f"  module sees: {x}")

    def outer2():
        x2 = "enclosing"

        def inner2():
            print(f"  inner2 sees: {x2}")

        inner2()

    outer2()

    print()

    # --- Section 2: nonlocal keyword ---
    print("--- Section 2: nonlocal Keyword ---")

    def counter():
        count = 0

        def increment():
            # TODO: use nonlocal to modify count from enclosing scope
            # HINT: nonlocal count; count += 1; return count
            pass

        return increment

    try:
        c = counter()
        print(f"  c() = {c()}")  # 1
        print(f"  c() = {c()}")  # 2
        print(f"  c() = {c()}")  # 3
        assert c() == 4
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # Compare with global
    module_var = 0

    def modify_global():
        # TODO: use global to modify module_var
        # HINT: global module_var; module_var += 1
        pass

    try:
        modify_global()
        modify_global()
        print(f"  module_var after 2 calls: {module_var}")
        assert module_var == 2
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Closures -- capturing environment ---
    print("--- Section 3: Closures ---")

    def make_greeter(greeting):
        """Factory that returns a greeting function."""
        # TODO: define an inner function greet(name) that returns f"{greeting}, {name}!"
        # HINT: the inner function captures 'greeting' from the enclosing scope
        def greet(name):
            pass
        return greet

    try:
        hello = make_greeter("Hello")
        hola = make_greeter("Hola")

        print(f"  {hello('Alice')}")
        assert hello("Alice") == "Hello, Alice!"

        print(f"  {hola('Bob')}")
        assert hola("Bob") == "Hola, Bob!"

        print(f"  hello.__closure__[0].cell_contents = {hello.__closure__[0].cell_contents!r}")
        assert hello.__closure__[0].cell_contents == "Hello"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Closure use cases -- factories ---
    print("--- Section 4: Closure Factories ---")

    # Counter factory
    def make_counter(start=0):
        count = start

        def increment(step=1):
            # TODO: use nonlocal to modify count, add step, return count
            pass

        def get():
            return count

        def reset():
            # TODO: use nonlocal to reset count to start
            pass

        increment.get = get
        increment.reset = reset
        return increment

    try:
        ctr = make_counter(10)
        print(f"  ctr() = {ctr()}")        # 11
        assert ctr.get() == 11
        print(f"  ctr(5) = {ctr(5)}")      # 16
        assert ctr.get() == 16
        ctr.reset()
        print(f"  after reset: {ctr.get()}")  # 10
        assert ctr.get() == 10
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (make_counter): {e}")

    # Multiplier factory
    def make_multiplier(factor):
        # TODO: return a function that multiplies its argument by factor
        # HINT: def multiply(x): return x * factor
        def multiply(x):
            pass
        return multiply

    try:
        double = make_multiplier(2)
        triple = make_multiplier(3)

        print(f"  double(5) = {double(5)}")
        assert double(5) == 10
        print(f"  triple(5) = {triple(5)}")
        assert triple(5) == 15
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (make_multiplier): {e}")

    # Config factory
    def make_formatter(template, **defaults):
        """Create a string formatter with default values baked in."""
        def format(**kwargs):
            # TODO: merge defaults with kwargs, then format the template
            # HINT: merged = {**defaults, **kwargs}; return template.format(**merged)
            pass
        return format

    try:
        log_fmt = make_formatter(
            "[{level}] {timestamp} - {message}",
            level="INFO",
            timestamp="N/A"
        )

        result1 = log_fmt(message="Server started")
        print(f"  {result1}")
        assert result1 == "[INFO] N/A - Server started"

        result2 = log_fmt(message="Error!", level="ERROR", timestamp="12:00")
        print(f"  {result2}")
        assert result2 == "[ERROR] 12:00 - Error!"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (make_formatter): {e}")

    print()

    # --- Section 5: Late binding gotcha ---
    print("--- Section 5: Late Binding Gotcha ---")

    # BUG: all functions see i=4
    functions_bad = []
    for i in range(5):
        functions_bad.append(lambda: i)

    results_bad = [f() for f in functions_bad]
    print(f"  Late binding (bug): {results_bad}")
    assert results_bad == [4, 4, 4, 4, 4]

    # TODO: Fix 1 -- use default argument to capture current value of i
    # HINT: lambda i=i: i
    functions_fix1 = []
    for i in range(5):
        functions_fix1.append(lambda: i)  # FIX THIS LINE

    try:
        results_fix1 = [f() for f in functions_fix1]
        print(f"  Fix 1 (default arg): {results_fix1}")
        assert results_fix1 == [0, 1, 2, 3, 4]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (Fix 1): {e}")

    # TODO: Fix 2 -- use a factory function
    # HINT: def make_fn(val): return lambda: val
    def make_fn(val):
        pass

    try:
        functions_fix2 = [make_fn(i) for i in range(5)]
        results_fix2 = [f() for f in functions_fix2]
        print(f"  Fix 2 (factory): {results_fix2}")
        assert results_fix2 == [0, 1, 2, 3, 4]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (Fix 2): {e}")

    print()

    # --- Section 6: Functions as first-class objects ---
    print("--- Section 6: First-Class Functions ---")

    def add(a, b):
        """Add two numbers."""
        return a + b

    print(f"  add.__name__ = {add.__name__!r}")
    assert add.__name__ == "add"

    try:
        # TODO: assign add to a variable called plus, then call it
        plus = None  # replace this
        print(f"  plus(3, 4) = {plus(3, 4)}")
        assert plus(3, 4) == 7
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (plus): {e}")

    try:
        # TODO: create a dict mapping operator symbols to functions
        # HINT: {"+": add, "-": lambda a, b: a - b, "*": lambda a, b: a * b}
        operations = {}  # replace this

        for op, fn in operations.items():
            result = fn(10, 3)
            print(f"  10 {op} 3 = {result}")

        assert operations["+"](10, 3) == 13
        assert operations["-"](10, 3) == 7
        assert operations["*"](10, 3) == 30
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (operations): {e}")

    # TODO: write apply_op that takes a function and two arguments, returns fn(a, b)
    def apply_op(fn, a, b):
        pass

    try:
        print(f"  apply_op(add, 5, 3) = {apply_op(add, 5, 3)}")
        assert apply_op(add, 5, 3) == 8
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (apply_op): {e}")

    print()

    # --- Section 7: Higher-order functions ---
    print("--- Section 7: Higher-Order Functions ---")

    # TODO: implement apply_to_all -- takes a function and items, returns [fn(item) for item in items]
    def apply_to_all(fn, items):
        """Apply fn to each item, return results."""
        pass

    try:
        result = apply_to_all(str.upper, ["hello", "world"])
        print(f"  apply_to_all(str.upper, ...) = {result}")
        assert result == ["HELLO", "WORLD"]

        result = apply_to_all(len, ["hello", "world", "hi"])
        print(f"  apply_to_all(len, ...) = {result}")
        assert result == [5, 5, 2]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (apply_to_all): {e}")

    # TODO: implement compose(f, g) that returns a function: compose(f, g)(x) == f(g(x))
    def compose(f, g):
        """compose(f, g)(x) == f(g(x))"""
        # HINT: def composed(x): return f(g(x)); return composed
        pass

    try:
        shout = compose(str.upper, str.strip)
        result = shout("  hello  ")
        print(f"  compose(str.upper, str.strip)('  hello  ') = {result!r}")
        assert result == "HELLO"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (compose): {e}")

    # TODO: implement with_logging -- wraps a function with print statements
    def with_logging(fn):
        # HINT: def wrapper(*args, **kwargs): print(...); result = fn(...); print(...); return result
        pass

    try:
        logged_add = with_logging(add)
        result = logged_add(3, 4)
        assert result == 7
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (with_logging): {e}")

    print()

    # --- Section 8: functools.partial ---
    print("--- Section 8: functools.partial ---")

    def power(base, exponent):
        return base ** exponent

    try:
        # TODO: create square and cube using partial
        # HINT: partial(power, exponent=2)
        square = None  # replace this
        cube = None  # replace this

        print(f"  square(5) = {square(5)}")
        assert square(5) == 25
        print(f"  cube(3) = {cube(3)}")
        assert cube(3) == 27

        print(f"  square.func = {square.func.__name__}")
        assert square.func is power
        print(f"  square.keywords = {square.keywords}")
        assert square.keywords == {"exponent": 2}
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (square/cube): {e}")

    try:
        # TODO: create info and error loggers using partial
        def log(level, message, timestamp="N/A"):
            return f"[{level}] {timestamp}: {message}"

        # HINT: partial(log, "INFO") and partial(log, "ERROR")
        info = None  # replace this
        error = None  # replace this

        result = info("Server started")
        print(f"  {result}")
        assert result == "[INFO] N/A: Server started"

        result = error("Connection failed")
        print(f"  {result}")
        assert result == "[ERROR] N/A: Connection failed"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (info/error loggers): {e}")

    print()

    # --- Section 9: functools.singledispatch ---
    print("--- Section 9: functools.singledispatch ---")

    # TODO: implement format_value using singledispatch
    # Default: return str(value)
    # int: return f"{value:,}"
    # float: return f"{value:.2f}"
    # list: format each item, join with ", ", wrap in brackets
    # dict: format each k: v pair, join with ", ", wrap in braces
    # HINT: @singledispatch for the base, @format_value.register(int) for overloads
    @singledispatch
    def format_value(value):
        pass

    @format_value.register(int)
    def _(value):
        pass

    @format_value.register(float)
    def _(value):
        pass

    @format_value.register(list)
    def _(value):
        pass

    @format_value.register(dict)
    def _(value):
        pass

    try:
        print(f"  format_value(1234567) = {format_value(1234567)!r}")
        assert format_value(1234567) == "1,234,567"

        print(f"  format_value(3.14159) = {format_value(3.14159)!r}")
        assert format_value(3.14159) == "3.14"

        print(f"  format_value([1, 2.5, 'hello']) = {format_value([1, 2.5, 'hello'])!r}")
        assert format_value([1, 2.5, "hello"]) == "[1, 2.50, hello]"

        result = format_value({"age": 30, "pi": 3.14})
        print(f"  format_value(dict) = {result!r}")
        assert result == "{age: 30, pi: 3.14}"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 10: Lambda expressions ---
    print("--- Section 10: Lambda Expressions ---")
    try:
        # TODO: sort names case-insensitively using lambda as sort key
        # HINT: sorted(names, key=lambda s: s.lower())
        names = ["Alice", "bob", "Carol", "dave"]
        sorted_names = []  # replace this
        print(f"  Sorted case-insensitive: {sorted_names}")
        assert sorted_names == ["Alice", "bob", "Carol", "dave"]

        # TODO: sort pairs by second element using lambda
        # HINT: sorted(pairs, key=lambda p: p[1])
        pairs = [(1, "b"), (3, "a"), (2, "c")]
        sorted_pairs = []  # replace this
        print(f"  Sorted by second element: {sorted_pairs}")
        assert sorted_pairs == [(3, "a"), (1, "b"), (2, "c")]

        # TODO: use map+filter with lambdas to double even numbers from [1..8]
        # HINT: list(map(lambda x: x * 2, filter(lambda x: x % 2 == 0, nums)))
        nums = [1, 2, 3, 4, 5, 6, 7, 8]
        evens_doubled = []  # replace this
        print(f"  Evens doubled: {evens_doubled}")
        assert evens_doubled == [4, 8, 12, 16]
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 11: Callable objects ---
    print("--- Section 11: Callable Objects ---")

    class Accumulator:
        """A callable that accumulates values."""

        def __init__(self, start=0):
            self.total = start
            self.history = []

        def __call__(self, value):
            # TODO: add value to self.total, append to self.history, return self.total
            pass

        def reset(self):
            # TODO: reset total to 0 and clear history
            pass

        def __repr__(self):
            return f"Accumulator(total={self.total}, calls={len(self.history)})"

    try:
        acc = Accumulator()
        r1 = acc(10)
        print(f"  acc(10) = {r1}")
        assert r1 == 10
        r2 = acc(20)
        print(f"  acc(20) = {r2}")
        assert r2 == 30
        r3 = acc(5)
        print(f"  acc(5) = {r3}")
        assert r3 == 35
        print(f"  {acc}")
        assert repr(acc) == "Accumulator(total=35, calls=3)"
        print(f"  acc.history = {acc.history}")
        assert acc.history == [10, 20, 5]

        print(f"  callable(acc) = {callable(acc)}")
        assert callable(acc) is True
        print(f"  callable(42) = {callable(42)}")
        assert callable(42) is False

        acc.reset()
        assert acc.total == 0
        assert acc.history == []
        print(f"  After reset: {acc}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 12: Exercise -- Middleware chain ---
    print("--- Section 12: Exercise -- Middleware Chain ---")

    def middleware_chain(handler, middlewares):
        """Apply middlewares to a handler, outermost first."""
        # TODO: apply middlewares in reverse order so the first one is outermost
        # HINT: for mw in reversed(middlewares): handler = mw(handler); return handler
        pass

    def logging_middleware(handler):
        def wrapper(request):
            print(f"    LOG: Processing {request}")
            response = handler(request)
            print(f"    LOG: Response: {response}")
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

    try:
        chain = middleware_chain(
            my_handler,
            [logging_middleware, auth_middleware, uppercase_middleware]
        )

        print("  Valid request:")
        result = chain({"user": "Alice", "token": "abc123"})
        print(f"  Result: {result}")
        assert result == {"body": "HELLO, ALICE!"}

        print("  Unauthorized request:")
        result = chain({"user": "Bob"})
        print(f"  Result: {result}")
        assert result == {"error": "unauthorized"}
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 13: Exercise -- Event system ---
    print("--- Section 13: Exercise -- Event System ---")

    def create_event_system():
        """Create an event system with on(), off(), and emit()."""
        # TODO: create a listeners dict, then define on, off, emit functions
        # on(event, callback) -- add callback to listeners[event]
        # off(event, callback) -- remove callback from listeners[event]
        # emit(event, *args, **kwargs) -- call all callbacks for event
        # HINT: return {"on": on, "off": off, "emit": emit}
        listeners = {}

        def on(event, callback):
            pass

        def off(event, callback):
            pass

        def emit(event, *args, **kwargs):
            pass

        return {"on": on, "off": off, "emit": emit}

    try:
        events = create_event_system()

        login_log = []

        def on_login(user):
            login_log.append(f"{user} logged in")
            print(f"    {user} logged in")

        def on_login_email(user):
            login_log.append(f"Sending welcome email to {user}")
            print(f"    Sending welcome email to {user}")

        events["on"]("login", on_login)
        events["on"]("login", on_login_email)

        print("  Emitting 'login' event:")
        events["emit"]("login", "Alice")
        assert login_log == ["Alice logged in", "Sending welcome email to Alice"]

        events["off"]("login", on_login_email)
        login_log.clear()
        print("  After removing email handler:")
        events["emit"]("login", "Bob")
        assert login_log == ["Bob logged in"]

        events["emit"]("logout", "Charlie")  # Should not raise
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Closures, scoping & first-class functions in Python:")
    print("  - LEGB: Local -> Enclosing -> Global -> Built-in")
    print("  - nonlocal: modify enclosing scope variables")
    print("  - Closures: functions that capture their environment")
    print("  - Factories: counter, multiplier, config patterns")
    print("  - Late binding gotcha: loop variables captured by reference")
    print("  - Functions are objects: assign, pass, store in data structures")
    print("  - Higher-order functions: take/return functions")
    print("  - functools.partial: pre-fill arguments")
    print("  - functools.singledispatch: overload by type")
    print("  - Lambda: anonymous single-expression functions")
    print("  - Callable objects: __call__ for stateful callables")
    print()
    print("All 13 sections passed. You've mastered closures & first-class functions!")
