"""
Kata 09 -- Error Handling Done Right
Run: python playground/skeletons/09_error_handling.py

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
        # TODO: store field, value, message as attributes
        # TODO: call super().__init__() with a formatted message like "field: message (got value)"
        # HINT: super().__init__(f"{field}: {message} (got {value!r})")
        pass


class NotFoundError(Exception):
    """Raised when a requested resource doesn't exist."""

    def __init__(self, resource_type: str, resource_id: str | int):
        # TODO: store resource_type and resource_id as attributes
        # TODO: call super().__init__() with a formatted message
        # HINT: super().__init__(f"{resource_type} {resource_id!r} not found")
        pass


class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


class FieldError(Exception):
    """Raised when a single field fails validation."""

    def __init__(self, field: str, message: str):
        # TODO: store field and message as attributes
        # TODO: call super().__init__() with a formatted message
        # HINT: super().__init__(f"{field}: {message}")
        pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Exception hierarchy ---
    print("--- Section 1: Exception Hierarchy ---")

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

    print()

    # --- Section 2: Custom exceptions ---
    print("--- Section 2: Custom Exceptions ---")

    # TODO: raise a ValidationError and catch it, then inspect its attributes
    # HINT: raise ValidationError("age", -5, "must be non-negative")
    try:
        pass  # TODO: raise ValidationError here
    except ValidationError as e:
        print(f"Field: {e.field}, Value: {e.value}")
        print(f"Message: {e}")
        try:
            assert e.field == "age"
            assert e.value == -5
            assert e.message == "must be non-negative"
            assert "age: must be non-negative (got -5)" in str(e)
        except (AssertionError, AttributeError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")
    except Exception:
        print("  ❌ TODO: raise ValidationError('age', -5, 'must be non-negative')")

    # TODO: raise a NotFoundError and catch it
    # HINT: raise NotFoundError("User", 42)
    try:
        pass  # TODO: raise NotFoundError here
    except NotFoundError as e:
        print(f"Resource: {e.resource_type} {e.resource_id}")
        print(f"Message: {e}")
        try:
            assert e.resource_type == "User"
            assert e.resource_id == 42
            assert "User 42 not found" in str(e)
        except (AssertionError, AttributeError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")
    except Exception:
        print("  ❌ TODO: raise NotFoundError('User', 42)")

    print()

    # --- Section 3: raise from -- explicit exception chaining ---
    print("--- Section 3: raise from -- Explicit Exception Chaining ---")

    def get_user(user_id: int) -> dict:
        # TODO: try to raise a ConnectionError, then catch it and raise DatabaseError from it
        # HINT: raise DatabaseError(f"failed to fetch user {user_id}") from e
        try:
            raise ConnectionError("connection refused")
        except ConnectionError as e:
            pass  # TODO: raise DatabaseError from e here

    try:
        get_user(42)
    except DatabaseError as e:
        print(f"Caught: {e}")
        print(f"Original cause: {e.__cause__}")
        try:
            assert str(e) == "failed to fetch user 42"
            assert isinstance(e.__cause__, ConnectionError)
            assert str(e.__cause__) == "connection refused"
        except (AssertionError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")
    except Exception:
        print("  ❌ TODO: raise DatabaseError from the ConnectionError")

    # TODO: demonstrate implicit chaining (__context__)
    def implicit_chaining():
        try:
            raise ValueError("original")
        except ValueError:
            pass  # TODO: raise RuntimeError here (no 'from')

    try:
        implicit_chaining()
    except RuntimeError as e:
        print(f"Implicit chaining -- caught: {e}")
        print(f"Context: {e.__context__}")
        try:
            assert isinstance(e.__context__, ValueError)
        except (AssertionError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")
    except Exception:
        print("  ❌ TODO: raise RuntimeError inside implicit_chaining")

    # TODO: demonstrate suppressed chaining (raise from None)
    def suppressed_chaining():
        try:
            raise ValueError("internal detail")
        except ValueError:
            pass  # TODO: raise RuntimeError from None

    try:
        suppressed_chaining()
    except RuntimeError as e:
        print(f"Suppressed chaining -- caught: {e}")
        print(f"Cause: {e.__cause__}")
        print(f"Suppress context: {e.__suppress_context__}")
        try:
            assert e.__cause__ is None
            assert e.__suppress_context__ is True
        except (AssertionError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")
    except Exception:
        print("  ❌ TODO: raise RuntimeError from None inside suppressed_chaining")

    print()

    # --- Section 4: LBYL vs EAFP ---
    print("--- Section 4: LBYL vs EAFP ---")

    data = {"name": "Alice", "age": 30}

    # TODO: implement LBYL style -- check 'if key in d' before accessing
    def get_value_lbyl(d: dict, key: str, default: str = "N/A") -> object:
        # HINT: if key in d: return d[key] else return default
        pass

    # TODO: implement EAFP style -- try/except KeyError
    def get_value_eafp(d: dict, key: str, default: str = "N/A") -> object:
        # HINT: try: return d[key] except KeyError: return default
        pass

    try:
        assert get_value_lbyl(data, "name") == "Alice"
        assert get_value_lbyl(data, "email") == "N/A"
        assert get_value_eafp(data, "name") == "Alice"
        assert get_value_eafp(data, "email") == "N/A"
        print(f"LBYL get 'name': {get_value_lbyl(data, 'name')}")
        print(f"EAFP get 'name': {get_value_eafp(data, 'name')}")
        print(f"LBYL get 'email': {get_value_lbyl(data, 'email')}")
        print(f"EAFP get 'email': {get_value_eafp(data, 'email')}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()
    print("LBYL: check before acting (good when failure is common)")
    print("EAFP: try and catch (good when failure is rare -- more Pythonic)")

    print()

    # --- Section 5: else and finally ---
    print("--- Section 5: else and finally in try Blocks ---")

    # TODO: implement demonstrate_try_flow to show try/except/else/finally ordering
    # HINT: append "try", raise if should_fail, append "except" or "else", append "finally"
    def demonstrate_try_flow(should_fail: bool) -> str:
        log = []
        # TODO: use try/except/else/finally, appending to log in each block
        # HINT: try: log "try", if should_fail raise ValueError
        #       except: log "except"
        #       else: log "else"
        #       finally: log "finally"
        return " -> ".join(log)

    try:
        success_flow = demonstrate_try_flow(False)
        print(f"Success: {success_flow}")
        assert success_flow == "try -> else -> finally"

        failure_flow = demonstrate_try_flow(True)
        print(f"Failure: {failure_flow}")
        assert failure_flow == "try -> except -> finally"
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # Demonstrate why else matters
    def parse_safe(text: str) -> dict | None:
        """Demonstrate else to avoid catching the wrong exception."""
        # TODO: try json.loads(text), catch JSONDecodeError, use else for success path
        # HINT: try: data = json.loads(text)
        #       except json.JSONDecodeError: return None
        #       else: return data
        pass

    try:
        result = parse_safe('{"key": "value"}')
        assert result == {"key": "value"}

        result = parse_safe('not json')
        assert result is None
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (parse_safe): {e}")

    print()

    # --- Section 6: ExceptionGroup (Python 3.11+) ---
    print("--- Section 6: ExceptionGroup ---")

    # TODO: create and raise an ExceptionGroup with mixed exception types
    # HINT: raise ExceptionGroup("multiple errors", [ValueError(...), TypeError(...), ...])
    try:
        pass  # TODO: raise ExceptionGroup here
    except ExceptionGroup as eg:
        print(f"Caught ExceptionGroup: {eg}")
        print(f"Number of exceptions: {len(eg.exceptions)}")
        for i, exc in enumerate(eg.exceptions):
            print(f"  [{i}] {type(exc).__name__}: {exc}")
        try:
            assert len(eg.exceptions) == 3
        except (AssertionError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")
    except Exception:
        print("  ❌ TODO: raise ExceptionGroup with 3 exceptions")

    print()

    # TODO: use subgroup() to filter exceptions by type
    # HINT: eg.subgroup(ValueError) returns a new ExceptionGroup with only ValueErrors
    eg = ExceptionGroup("mixed", [
        ValueError("v1"),
        TypeError("t1"),
        ValueError("v2"),
        KeyError("k1"),
    ])

    try:
        val_group = None  # TODO: eg.subgroup(ValueError)
        print(f"ValueError subgroup: {val_group}")
        assert val_group is not None
        assert len(val_group.exceptions) == 2

        type_group = None  # TODO: eg.subgroup(TypeError)
        print(f"TypeError subgroup: {type_group}")
        assert type_group is not None
        assert len(type_group.exceptions) == 1

        # TODO: use split() to partition into (match, rest)
        # HINT: match, rest = eg.split(ValueError)
        match, rest = None, None  # TODO: eg.split(ValueError)
        print(f"Split match (ValueError): {match}")
        print(f"Split rest (non-ValueError): {rest}")
        assert match is not None and len(match.exceptions) == 2
        assert rest is not None and len(rest.exceptions) == 2
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

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

    # TODO: implement process_batch that converts strings to ints,
    # collecting errors with add_note() for context
    def process_batch(items: list[str]) -> list[int]:
        results = []
        errors = []
        for i, item in enumerate(items):
            try:
                results.append(int(item))
            except ValueError as e:
                # TODO: use e.add_note() to add index and raw input context
                # HINT: e.add_note(f"occurred at index {i}")
                #       e.add_note(f"raw input: {item!r}")
                errors.append(e)
        if errors:
            raise ExceptionGroup("batch processing failed", errors)
        return results

    try:
        process_batch(["10", "abc", "20", "xyz"])
    except* ValueError as eg:
        for e in eg.exceptions:
            print(f"Error: {e}")
            print(f"Notes: {getattr(e, '__notes__', [])}")
        try:
            assert len(eg.exceptions) == 2
            assert "occurred at index 1" in eg.exceptions[0].__notes__
            assert "occurred at index 3" in eg.exceptions[1].__notes__
        except (AssertionError, AttributeError, Exception) as ae:
            print(f"  ❌ Not yet implemented (add_note): {ae}")

    # TODO: create a simple exception with add_note
    # HINT: err = ValueError("something"); err.add_note("context"); raise err
    try:
        err = ValueError("something went wrong")
        # TODO: add two notes to err, then raise it
        raise err
    except ValueError as e:
        print(f"\nSimple add_note: {e}")
        print(f"Notes: {getattr(e, '__notes__', [])}")
        try:
            assert len(e.__notes__) == 2
            assert e.__notes__[0] == "additional context here"
            assert e.__notes__[1] == "more details"
        except (AssertionError, AttributeError, Exception) as ae:
            print(f"  ❌ Not yet implemented: {ae}")

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

    # TODO: implement divide_safe that catches only ZeroDivisionError
    # HINT: try: return a / b except ZeroDivisionError: return None
    def divide_safe(a: float, b: float) -> float | None:
        """Only catch the specific error we expect."""
        pass

    try:
        assert divide_safe(10, 2) == 5.0
        assert divide_safe(10, 0) is None

        try:
            divide_safe("10", 2)  # type error -- should NOT be caught
        except TypeError:
            print("Correctly propagated TypeError (not caught by divide_safe)")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 10: Real-world pattern -- validation collecting all errors ---
    print("--- Section 10: Validation with ExceptionGroup ---")

    # TODO: implement validate_user that collects all field errors into ExceptionGroup
    def validate_user(data: dict) -> dict:
        """Validate a user dict. Collect all errors, raise as ExceptionGroup."""
        errors: list[FieldError] = []

        # TODO: validate 'name' (required, min 2 chars)
        # TODO: validate 'age' (required, must be int, 0-150)
        # TODO: validate 'email' (required, must contain @)
        # HINT: append FieldError("field_name", "error message") for each failure
        #       if errors: raise ExceptionGroup("validation failed", errors)

        if errors:
            raise ExceptionGroup("validation failed", errors)

        return data

    try:
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
    except (AssertionError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 11: Real-world pattern -- retry with exception chaining ---
    print("--- Section 11: Retry with Exception Chaining ---")

    # TODO: implement retry() that collects all failures with add_note()
    def retry(fn, max_attempts: int = 3, delay: float = 0.01):
        """Retry a function, collecting all failures in an ExceptionGroup."""
        errors: list[Exception] = []
        # TODO: loop max_attempts times, try fn(), catch exceptions,
        #       add_note with attempt number, append to errors
        # HINT: for attempt in range(1, max_attempts + 1):
        #           try: return fn()
        #           except Exception as e: e.add_note(...); errors.append(e)
        if errors:
            raise ExceptionGroup(f"all {max_attempts} attempts failed", errors)
        raise RuntimeError("retry: not yet implemented")

    call_count = [0]

    def always_fails():
        call_count[0] += 1
        raise ConnectionError(f"server unavailable (call {call_count[0]})")

    try:
        retry(always_fails, max_attempts=3, delay=0.01)
    except ExceptionGroup as eg:
        print(f"Retry failed after {len(eg.exceptions)} attempts:")
        for e in eg.exceptions:
            print(f"  - {e} (notes: {getattr(e, '__notes__', [])})")
        try:
            assert len(eg.exceptions) == 3
            assert "attempt 1 of 3" in eg.exceptions[0].__notes__
            assert "attempt 3 of 3" in eg.exceptions[2].__notes__
        except (AssertionError, AttributeError, Exception) as ae:
            print(f"  ❌ Not yet implemented (retry): {ae}")
    except Exception as e:
        print(f"  ❌ Not yet implemented (retry): {e}")

    # Simulate a function that succeeds on attempt 2
    attempt_counter = [0]

    def succeeds_eventually():
        attempt_counter[0] += 1
        if attempt_counter[0] < 2:
            raise ConnectionError("not yet")
        return "success!"

    try:
        result = retry(succeeds_eventually, max_attempts=3, delay=0.01)
        print(f"Retry succeeded: {result}")
        assert result == "success!"
    except (AssertionError, ExceptionGroup, Exception) as e:
        print(f"  ❌ Not yet implemented (retry success): {e}")

    print()

    # --- Section 12: Exercise -- validate_product ---
    print("--- Section 12: Exercise -- validate_product ---")

    # TODO: implement validate_product following the same pattern as validate_user
    def validate_product(data: dict) -> dict:
        """Validate a product dict. Collect all errors, raise as ExceptionGroup."""
        errors: list[FieldError] = []

        # TODO: validate 'name' (required, min 2 chars)
        # TODO: validate 'price' (required, must be number, must be positive)
        # TODO: validate 'quantity' (required, must be int, must be non-negative)
        # HINT: follow the same pattern as validate_user

        if errors:
            raise ExceptionGroup("product validation failed", errors)

        return data

    try:
        valid_product = validate_product({"name": "Widget", "price": 9.99, "quantity": 100})
        print(f"Valid product: {valid_product}")
        assert valid_product["name"] == "Widget"

        try:
            validate_product({"name": "", "price": -10, "quantity": "five"})
        except ExceptionGroup as eg:
            print(f"Product validation errors ({len(eg.exceptions)}):")
            for e in eg.exceptions:
                print(f"  - {e}")
            assert len(eg.exceptions) == 3

        try:
            validate_product({})
        except ExceptionGroup as eg:
            print(f"Missing fields errors ({len(eg.exceptions)}):")
            for e in eg.exceptions:
                print(f"  - {e}")
            assert len(eg.exceptions) == 3
    except (AssertionError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 13: Exercise -- retry decorator ---
    print("--- Section 13: Exercise -- Retry Decorator ---")

    # TODO: implement with_retry decorator
    def with_retry(max_attempts: int = 3, delay: float = 0.01):
        """Decorator that retries a function, collecting failures in ExceptionGroup."""
        def decorator(fn):
            def wrapper(*args, **kwargs):
                errors: list[Exception] = []
                # TODO: loop, try fn(*args, **kwargs), catch, add_note, append
                # HINT: same logic as the retry() function above, but as a decorator
                if errors:
                    raise ExceptionGroup(
                        f"{fn.__name__}: all {max_attempts} attempts failed", errors
                    )
                raise RuntimeError("with_retry: not yet implemented")
            return wrapper
        return decorator

    retry_count = [0]

    @with_retry(max_attempts=3, delay=0.01)
    def unstable_operation():
        retry_count[0] += 1
        if retry_count[0] < 3:
            raise ConnectionError(f"failed (attempt {retry_count[0]})")
        return "finally worked"

    try:
        result = unstable_operation()
        print(f"Retry decorator result: {result}")
        assert result == "finally worked"
    except (AssertionError, ExceptionGroup, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    try:
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
    except (AssertionError, Exception) as e:
        print(f"  ❌ Not yet implemented (always_broken): {e}")

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
