"""
Kata 09 -- Error Handling Done Right
Run: python playground/09_error_handling.py

Master Python's full exception toolkit: custom exceptions, raise from,
LBYL vs EAFP, ExceptionGroup, except*, and add_note().
"""

import json
import time


# ===========================================================================
# CUSTOM EXCEPTIONS
# ===========================================================================

class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: object, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"{field}: {message} (got {value!r})")


class NotFoundError(Exception):
    """Raised when a requested resource doesn't exist."""

    def __init__(self, resource_type: str, resource_id: str | int):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} {resource_id!r} not found")


class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


class FieldError(Exception):
    """Raised when a single field fails validation."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Exception hierarchy ---
    print("--- Section 1: Exception Hierarchy ---")

    # Verify the hierarchy
    assert issubclass(ValueError, Exception)
    assert issubclass(Exception, BaseException)
    assert issubclass(KeyboardInterrupt, BaseException)
    assert not issubclass(KeyboardInterrupt, Exception)
    assert issubclass(FileNotFoundError, OSError)
    assert issubclass(OSError, Exception)

    print("BaseException")
    print("├── SystemExit (not caught by 'except Exception')")
    print("├── KeyboardInterrupt (not caught by 'except Exception')")
    print("├── GeneratorExit (not caught by 'except Exception')")
    print("└── Exception (everything you should catch)")
    print("    ├── ValueError, TypeError, KeyError, ...")
    print("    ├── OSError -> FileNotFoundError, PermissionError, ...")
    print("    └── YourCustomExceptions")
    print()
    print("KeyboardInterrupt is BaseException:", issubclass(KeyboardInterrupt, BaseException))
    print("KeyboardInterrupt is Exception:", issubclass(KeyboardInterrupt, Exception))
    assert issubclass(KeyboardInterrupt, BaseException)
    assert not issubclass(KeyboardInterrupt, Exception)

    print()

    # --- Section 2: Custom exceptions ---
    print("--- Section 2: Custom Exceptions ---")

    # ValidationError with structured data
    try:
        raise ValidationError("age", -5, "must be non-negative")
    except ValidationError as e:
        print(f"Field: {e.field}, Value: {e.value}")
        print(f"Message: {e}")
        assert e.field == "age"
        assert e.value == -5
        assert e.message == "must be non-negative"
        assert "age: must be non-negative (got -5)" in str(e)

    # NotFoundError
    try:
        raise NotFoundError("User", 42)
    except NotFoundError as e:
        print(f"Resource: {e.resource_type} {e.resource_id}")
        print(f"Message: {e}")
        assert e.resource_type == "User"
        assert e.resource_id == 42
        assert "User 42 not found" in str(e)

    print()

    # --- Section 3: raise from -- explicit exception chaining ---
    print("--- Section 3: raise from -- Explicit Exception Chaining ---")

    def get_user(user_id: int) -> dict:
        try:
            raise ConnectionError("connection refused")
        except ConnectionError as e:
            raise DatabaseError(f"failed to fetch user {user_id}") from e

    # Explicit chaining: __cause__ is set
    try:
        get_user(42)
    except DatabaseError as e:
        print(f"Caught: {e}")
        print(f"Original cause: {e.__cause__}")
        assert str(e) == "failed to fetch user 42"
        assert isinstance(e.__cause__, ConnectionError)
        assert str(e.__cause__) == "connection refused"

    # Implicit chaining: __context__ is set (raise inside except without 'from')
    def implicit_chaining():
        try:
            raise ValueError("original")
        except ValueError:
            raise RuntimeError("new error")  # __context__ set implicitly

    try:
        implicit_chaining()
    except RuntimeError as e:
        print(f"Implicit chaining -- caught: {e}")
        print(f"Context: {e.__context__}")
        assert isinstance(e.__context__, ValueError)

    # Suppressed chaining: raise from None
    def suppressed_chaining():
        try:
            raise ValueError("internal detail")
        except ValueError:
            raise RuntimeError("clean error") from None

    try:
        suppressed_chaining()
    except RuntimeError as e:
        print(f"Suppressed chaining -- caught: {e}")
        print(f"Cause: {e.__cause__}")
        print(f"Suppress context: {e.__suppress_context__}")
        assert e.__cause__ is None
        assert e.__suppress_context__ is True

    print()

    # --- Section 4: LBYL vs EAFP ---
    print("--- Section 4: LBYL vs EAFP ---")

    data = {"name": "Alice", "age": 30}

    # LBYL: check before accessing
    def get_value_lbyl(d: dict, key: str, default: str = "N/A") -> object:
        if key in d:
            return d[key]
        return default

    # EAFP: try and handle exception
    def get_value_eafp(d: dict, key: str, default: str = "N/A") -> object:
        try:
            return d[key]
        except KeyError:
            return default

    # Both produce the same results
    assert get_value_lbyl(data, "name") == "Alice"
    assert get_value_lbyl(data, "email") == "N/A"
    assert get_value_eafp(data, "name") == "Alice"
    assert get_value_eafp(data, "email") == "N/A"
    print(f"LBYL get 'name': {get_value_lbyl(data, 'name')}")
    print(f"EAFP get 'name': {get_value_eafp(data, 'name')}")
    print(f"LBYL get 'email': {get_value_lbyl(data, 'email')}")
    print(f"EAFP get 'email': {get_value_eafp(data, 'email')}")

    # EAFP is preferred when failure is rare
    # LBYL is preferred when checks are cheap and failure is common
    print()
    print("LBYL: check before acting (good when failure is common)")
    print("EAFP: try and catch (good when failure is rare -- more Pythonic)")

    print()

    # --- Section 5: else and finally ---
    print("--- Section 5: else and finally in try Blocks ---")

    # Demonstrate try/except/else/finally flow
    def demonstrate_try_flow(should_fail: bool) -> str:
        log = []
        try:
            log.append("try")
            if should_fail:
                raise ValueError("oops")
        except ValueError:
            log.append("except")
        else:
            log.append("else")
        finally:
            log.append("finally")
        return " -> ".join(log)

    success_flow = demonstrate_try_flow(False)
    print(f"Success: {success_flow}")
    assert success_flow == "try -> else -> finally"

    failure_flow = demonstrate_try_flow(True)
    print(f"Failure: {failure_flow}")
    assert failure_flow == "try -> except -> finally"

    # Why else matters: avoiding over-broad catches
    def parse_safe(text: str) -> dict | None:
        """Demonstrate else to avoid catching the wrong exception."""
        try:
            # Only catch errors from this specific operation
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"  parse_safe: invalid JSON")
            return None
        else:
            # Success -- this code is NOT protected by the except above
            print(f"  parse_safe: parsed successfully -> {data}")
            return data

    result = parse_safe('{"key": "value"}')
    assert result == {"key": "value"}

    result = parse_safe('not json')
    assert result is None

    print()

    # --- Section 6: ExceptionGroup (Python 3.11+) ---
    print("--- Section 6: ExceptionGroup ---")

    # Basic ExceptionGroup
    try:
        raise ExceptionGroup("multiple errors", [
            ValueError("bad value 1"),
            TypeError("wrong type"),
            ValueError("bad value 2"),
        ])
    except ExceptionGroup as eg:
        print(f"Caught ExceptionGroup: {eg}")
        print(f"Number of exceptions: {len(eg.exceptions)}")
        for i, exc in enumerate(eg.exceptions):
            print(f"  [{i}] {type(exc).__name__}: {exc}")
        assert len(eg.exceptions) == 3

    print()

    # subgroup: filter to matching exceptions
    eg = ExceptionGroup("mixed", [
        ValueError("v1"),
        TypeError("t1"),
        ValueError("v2"),
        KeyError("k1"),
    ])

    val_group = eg.subgroup(ValueError)
    print(f"ValueError subgroup: {val_group}")
    assert val_group is not None
    assert len(val_group.exceptions) == 2

    type_group = eg.subgroup(TypeError)
    print(f"TypeError subgroup: {type_group}")
    assert type_group is not None
    assert len(type_group.exceptions) == 1

    # split: partition into (match, rest)
    match, rest = eg.split(ValueError)
    print(f"Split match (ValueError): {match}")
    print(f"Split rest (non-ValueError): {rest}")
    assert match is not None and len(match.exceptions) == 2
    assert rest is not None and len(rest.exceptions) == 2  # TypeError + KeyError

    print()

    # --- Section 7: except* -- handling exception groups selectively ---
    print("--- Section 7: except* ---")

    value_errors_caught = []
    type_errors_caught = []

    try:
        raise ExceptionGroup("errors", [
            ValueError("bad value 1"),
            TypeError("wrong type"),
            ValueError("bad value 2"),
        ])
    except* ValueError as eg:
        print(f"Caught {len(eg.exceptions)} ValueErrors:")
        for e in eg.exceptions:
            print(f"  - {e}")
            value_errors_caught.append(str(e))
    except* TypeError as eg:
        print(f"Caught {len(eg.exceptions)} TypeErrors:")
        for e in eg.exceptions:
            print(f"  - {e}")
            type_errors_caught.append(str(e))

    assert value_errors_caught == ["bad value 1", "bad value 2"]
    assert type_errors_caught == ["wrong type"]

    print()

    # --- Section 8: add_note() (Python 3.11+) ---
    print("--- Section 8: add_note() ---")

    def process_batch(items: list[str]) -> list[int]:
        results = []
        errors = []
        for i, item in enumerate(items):
            try:
                results.append(int(item))
            except ValueError as e:
                e.add_note(f"occurred at index {i}")
                e.add_note(f"raw input: {item!r}")
                errors.append(e)
        if errors:
            raise ExceptionGroup("batch processing failed", errors)
        return results

    try:
        process_batch(["10", "abc", "20", "xyz"])
    except* ValueError as eg:
        for e in eg.exceptions:
            print(f"Error: {e}")
            print(f"Notes: {e.__notes__}")
        assert len(eg.exceptions) == 2
        assert "occurred at index 1" in eg.exceptions[0].__notes__
        assert "occurred at index 3" in eg.exceptions[1].__notes__

    # add_note on a simple exception
    try:
        err = ValueError("something went wrong")
        err.add_note("additional context here")
        err.add_note("more details")
        raise err
    except ValueError as e:
        print(f"\nSimple add_note: {e}")
        print(f"Notes: {e.__notes__}")
        assert len(e.__notes__) == 2
        assert e.__notes__[0] == "additional context here"
        assert e.__notes__[1] == "more details"

    print()

    # --- Section 9: Best practices ---
    print("--- Section 9: Best Practices ---")

    print("1. Be specific: catch ValueError, not Exception")
    print("2. Log and re-raise: don't swallow errors silently")
    print("3. Use 'raise from' when wrapping exceptions")
    print("4. Don't use exceptions for flow control")
    print("5. Use else/finally to separate concerns in try blocks")
    print("6. Never use bare 'except:' -- it catches SystemExit and KeyboardInterrupt")
    print()

    # Demonstrate: specific vs broad catching
    def divide_safe(a: float, b: float) -> float | None:
        """Only catch the specific error we expect."""
        try:
            return a / b
        except ZeroDivisionError:
            return None
        # We do NOT catch TypeError here -- that's a bug, let it propagate

    assert divide_safe(10, 2) == 5.0
    assert divide_safe(10, 0) is None

    try:
        divide_safe("10", 2)  # type error -- should NOT be caught
    except TypeError:
        print("Correctly propagated TypeError (not caught by divide_safe)")

    print()

    # --- Section 10: Real-world pattern -- validation collecting all errors ---
    print("--- Section 10: Validation with ExceptionGroup ---")

    def validate_user(data: dict) -> dict:
        """Validate a user dict. Collect all errors, raise as ExceptionGroup."""
        errors: list[FieldError] = []

        name = data.get("name", "")
        if not name:
            errors.append(FieldError("name", "is required"))
        elif len(name) < 2:
            errors.append(FieldError("name", "must be at least 2 characters"))

        age = data.get("age")
        if age is None:
            errors.append(FieldError("age", "is required"))
        elif not isinstance(age, int):
            errors.append(FieldError("age", "must be an integer"))
        elif age < 0 or age > 150:
            errors.append(FieldError("age", "must be between 0 and 150"))

        email = data.get("email", "")
        if not email:
            errors.append(FieldError("email", "is required"))
        elif "@" not in email:
            errors.append(FieldError("email", "must contain @"))

        if errors:
            raise ExceptionGroup("validation failed", errors)

        return data

    # Valid data -- no errors
    valid = validate_user({"name": "Alice", "age": 30, "email": "alice@example.com"})
    print(f"Valid: {valid}")
    assert valid["name"] == "Alice"

    # Invalid data -- collects ALL errors
    try:
        validate_user({"name": "", "age": -5, "email": "bad"})
    except ExceptionGroup as eg:
        print(f"Validation errors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  - {e}")
        assert len(eg.exceptions) == 3

    # Partially invalid
    try:
        validate_user({"name": "Bob", "age": 200, "email": "bob@test.com"})
    except ExceptionGroup as eg:
        print(f"Validation errors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  - {e}")
        assert len(eg.exceptions) == 1
        assert eg.exceptions[0].field == "age"

    print()

    # --- Section 11: Real-world pattern -- retry with exception chaining ---
    print("--- Section 11: Retry with Exception Chaining ---")

    def retry(fn, max_attempts: int = 3, delay: float = 0.01):
        """Retry a function, collecting all failures in an ExceptionGroup."""
        errors: list[Exception] = []
        for attempt in range(1, max_attempts + 1):
            try:
                return fn()
            except Exception as e:
                e.add_note(f"attempt {attempt} of {max_attempts}")
                errors.append(e)
                if attempt < max_attempts:
                    time.sleep(delay)
        raise ExceptionGroup(f"all {max_attempts} attempts failed", errors)

    # Simulate a function that always fails
    call_count = [0]

    def always_fails():
        call_count[0] += 1
        raise ConnectionError(f"server unavailable (call {call_count[0]})")

    try:
        retry(always_fails, max_attempts=3, delay=0.01)
    except ExceptionGroup as eg:
        print(f"Retry failed after {len(eg.exceptions)} attempts:")
        for e in eg.exceptions:
            print(f"  - {e} (notes: {e.__notes__})")
        assert len(eg.exceptions) == 3
        assert "attempt 1 of 3" in eg.exceptions[0].__notes__
        assert "attempt 3 of 3" in eg.exceptions[2].__notes__

    # Simulate a function that succeeds on attempt 2
    attempt_counter = [0]

    def succeeds_eventually():
        attempt_counter[0] += 1
        if attempt_counter[0] < 2:
            raise ConnectionError("not yet")
        return "success!"

    result = retry(succeeds_eventually, max_attempts=3, delay=0.01)
    print(f"Retry succeeded: {result}")
    assert result == "success!"

    print()

    # --- Section 12: Exercise -- validate_product ---
    print("--- Section 12: Exercise -- validate_product ---")

    def validate_product(data: dict) -> dict:
        """Validate a product dict. Collect all errors, raise as ExceptionGroup."""
        errors: list[FieldError] = []

        name = data.get("name", "")
        if not name:
            errors.append(FieldError("name", "is required"))
        elif len(name) < 2:
            errors.append(FieldError("name", "must be at least 2 characters"))

        price = data.get("price")
        if price is None:
            errors.append(FieldError("price", "is required"))
        elif not isinstance(price, (int, float)):
            errors.append(FieldError("price", "must be a number"))
        elif price <= 0:
            errors.append(FieldError("price", "must be positive"))

        quantity = data.get("quantity")
        if quantity is None:
            errors.append(FieldError("quantity", "is required"))
        elif not isinstance(quantity, int):
            errors.append(FieldError("quantity", "must be an integer"))
        elif quantity < 0:
            errors.append(FieldError("quantity", "must be non-negative"))

        if errors:
            raise ExceptionGroup("product validation failed", errors)

        return data

    # Valid product
    valid_product = validate_product({"name": "Widget", "price": 9.99, "quantity": 100})
    print(f"Valid product: {valid_product}")
    assert valid_product["name"] == "Widget"

    # All fields invalid
    try:
        validate_product({"name": "", "price": -10, "quantity": "five"})
    except ExceptionGroup as eg:
        print(f"Product validation errors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  - {e}")
        assert len(eg.exceptions) == 3

    # Edge case: missing fields
    try:
        validate_product({})
    except ExceptionGroup as eg:
        print(f"Missing fields errors ({len(eg.exceptions)}):")
        for e in eg.exceptions:
            print(f"  - {e}")
        assert len(eg.exceptions) == 3

    print()

    # --- Section 13: Exercise -- retry decorator ---
    print("--- Section 13: Exercise -- Retry Decorator ---")

    def with_retry(max_attempts: int = 3, delay: float = 0.01):
        """Decorator that retries a function, collecting failures in ExceptionGroup."""
        def decorator(fn):
            def wrapper(*args, **kwargs):
                errors: list[Exception] = []
                for attempt in range(1, max_attempts + 1):
                    try:
                        return fn(*args, **kwargs)
                    except Exception as e:
                        e.add_note(f"attempt {attempt} of {max_attempts}")
                        errors.append(e)
                        if attempt < max_attempts:
                            time.sleep(delay)
                raise ExceptionGroup(
                    f"{fn.__name__}: all {max_attempts} attempts failed", errors
                )
            return wrapper
        return decorator

    # Test the decorator
    retry_count = [0]

    @with_retry(max_attempts=3, delay=0.01)
    def unstable_operation():
        retry_count[0] += 1
        if retry_count[0] < 3:
            raise ConnectionError(f"failed (attempt {retry_count[0]})")
        return "finally worked"

    result = unstable_operation()
    print(f"Retry decorator result: {result}")
    assert result == "finally worked"

    # Test total failure
    @with_retry(max_attempts=2, delay=0.01)
    def always_broken():
        raise RuntimeError("permanently broken")

    try:
        always_broken()
    except ExceptionGroup as eg:
        print(f"Total failure after {len(eg.exceptions)} attempts:")
        for e in eg.exceptions:
            print(f"  - {e}")
        assert len(eg.exceptions) == 2

    print()

    # --- Section 14: Exercise -- except* for mixed types ---
    print("--- Section 14: Exercise -- except* for Mixed Types ---")

    val_summary = []
    type_summary = []
    key_summary = []

    try:
        raise ExceptionGroup("mixed errors", [
            ValueError("invalid age"),
            TypeError("expected str, got int"),
            KeyError("missing_field"),
            ValueError("invalid email"),
            TypeError("expected list, got dict"),
        ])
    except* ValueError as eg:
        for e in eg.exceptions:
            val_summary.append(str(e))
        print(f"ValueErrors ({len(eg.exceptions)}): {val_summary}")
    except* TypeError as eg:
        for e in eg.exceptions:
            type_summary.append(str(e))
        print(f"TypeErrors ({len(eg.exceptions)}): {type_summary}")
    except* KeyError as eg:
        for e in eg.exceptions:
            key_summary.append(str(e))
        print(f"KeyErrors ({len(eg.exceptions)}): {key_summary}")

    assert val_summary == ["invalid age", "invalid email"]
    assert type_summary == ["expected str, got int", "expected list, got dict"]
    assert key_summary == ["'missing_field'"]

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Error handling done right in Python:")
    print("  - Exception hierarchy: BaseException -> Exception -> your custom types")
    print("  - Custom exceptions: structured data via attributes, not string parsing")
    print("  - raise from: explicit exception chaining preserves debugging context")
    print("  - LBYL vs EAFP: choose based on failure frequency and side effects")
    print("  - else/finally: separate success, error, and cleanup concerns")
    print("  - ExceptionGroup: bundle multiple errors (validation, concurrency)")
    print("  - except*: selectively handle exceptions from a group")
    print("  - add_note(): attach context without wrapping")
    print()
    print("All 14 sections passed. You've mastered error handling done right!")
