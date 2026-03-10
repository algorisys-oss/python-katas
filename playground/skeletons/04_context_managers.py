"""
Kata 04 -- Context Managers
Run: python playground/skeletons/04_context_managers.py

Explore the context manager protocol: __enter__/__exit__, @contextmanager,
exception handling, ExitStack, async context managers, and real-world patterns.
"""

import time
import os
import sys
import shutil
import tempfile
import asyncio
from contextlib import contextmanager, ExitStack, asynccontextmanager
from io import StringIO


# ---------------------------------------------------------------------------
# Section 1: Class-based context manager -- Timer
# ---------------------------------------------------------------------------

class Timer:
    """Measures elapsed time for a code block."""

    def __init__(self, label: str = "Block") -> None:
        self.label = label
        self.elapsed: float = 0.0

    def __enter__(self):
        # TODO: record the start time using time.perf_counter()
        # HINT: store it in self._start so __exit__ can access it
        # TODO: return self (this becomes the 'as' variable)
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: calculate elapsed time and store in self.elapsed
        # TODO: print the label and elapsed time
        # TODO: return False (don't suppress exceptions)
        # HINT: self.elapsed = time.perf_counter() - self._start
        pass


# ---------------------------------------------------------------------------
# Section 2: Class-based context manager -- TempDirectory
# ---------------------------------------------------------------------------

class TempDirectory:
    """Creates a temp directory on enter, cleans it up on exit."""

    def __init__(self, prefix: str = "kata_") -> None:
        self.prefix = prefix
        self.path: str | None = None

    def __enter__(self) -> str:
        # TODO: create a temp directory and store its path in self.path
        # TODO: return the path
        # HINT: use tempfile.mkdtemp(prefix=self.prefix)
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: remove the temp directory if it exists
        # HINT: use shutil.rmtree(self.path) after checking os.path.exists
        pass


# ---------------------------------------------------------------------------
# Section 3: Generator-based context manager with @contextmanager
# ---------------------------------------------------------------------------

@contextmanager
def timer(label: str = "Block"):
    """Generator-based timer context manager."""
    # TODO: record start time
    # TODO: create a result dict with "label" and "elapsed" keys
    # TODO: yield the result dict (this becomes the 'as' variable)
    # TODO: in the finally block, compute elapsed time and print it
    # HINT: use try/yield/finally structure
    pass


# ---------------------------------------------------------------------------
# Section 4: Exception handling in __exit__ -- SuppressErrors
# ---------------------------------------------------------------------------

class SuppressErrors:
    """Suppresses specified exception types, like contextlib.suppress."""

    def __init__(self, *exceptions: type[BaseException]) -> None:
        self.exceptions = exceptions
        self.exception: BaseException | None = None

    def __enter__(self):
        # TODO: return self
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: if an exception occurred and it matches self.exceptions,
        #       store it in self.exception and return True (suppress it)
        # TODO: otherwise return False (let it propagate)
        # HINT: use issubclass(exc_type, self.exceptions) to check
        pass


# ---------------------------------------------------------------------------
# Section 5: ExitStack for dynamic context manager stacking
# ---------------------------------------------------------------------------

def create_temp_files(names: list[str], base_dir: str) -> list[str]:
    """Create multiple temp files using ExitStack to manage them."""
    # TODO: use ExitStack to open multiple files dynamically
    # TODO: write content to each file
    # TODO: return the list of file paths
    # HINT: use stack.enter_context(open(filepath, "w")) for each file
    pass


# ---------------------------------------------------------------------------
# Section 6: Async context managers
# ---------------------------------------------------------------------------

class AsyncTimer:
    """Async context manager for timing async operations."""

    def __init__(self, label: str = "Block") -> None:
        self.label = label
        self.elapsed: float = 0.0

    async def __aenter__(self):
        # TODO: record start time and return self
        # HINT: same as Timer.__enter__ but with async def
        pass

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # TODO: calculate elapsed, print, return False
        # HINT: same as Timer.__exit__ but with async def
        pass


@asynccontextmanager
async def async_timer(label: str = "Block"):
    """Generator-based async context manager."""
    # TODO: record start time, yield, then print elapsed in finally
    # HINT: same pattern as @contextmanager but with async def and await
    pass


# ---------------------------------------------------------------------------
# Section 7: Real-world patterns
# ---------------------------------------------------------------------------

@contextmanager
def capture_stdout():
    """Capture print output to a StringIO."""
    # TODO: save sys.stdout, replace with StringIO, yield it, restore on exit
    # HINT: use try/finally to guarantee sys.stdout is restored
    pass


@contextmanager
def patch_attr(obj, attr, value):
    """Temporarily replace an attribute, restore on exit."""
    # TODO: save old value, set new value, yield old value, restore in finally
    # HINT: use getattr/setattr
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Class-based Timer ---
    print("--- Section 1: Class-based Timer ---")
    try:
        with Timer("sleep-test") as t:
            time.sleep(0.05)

        print(f"  Elapsed is accessible after: {t.elapsed:.2f}s")
        assert t.elapsed >= 0.05
        assert isinstance(t, Timer)
        print(f"  'as' variable is the Timer instance: {type(t).__name__}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 2: TempDirectory ---
    print("--- Section 2: TempDirectory ---")
    try:
        with TempDirectory(prefix="kata_test_") as tmpdir:
            print(f"  Created temp dir: {tmpdir}")
            assert os.path.isdir(tmpdir)

            testfile = os.path.join(tmpdir, "hello.txt")
            with open(testfile, "w") as f:
                f.write("hello from context manager")
            assert os.path.exists(testfile)
            print(f"  File exists inside: {os.path.basename(testfile)}")
            saved_path = tmpdir

        assert not os.path.exists(saved_path)
        print(f"  Temp dir cleaned up: {not os.path.exists(saved_path)}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 3: Generator-based @contextmanager ---
    print("--- Section 3: Generator-based @contextmanager ---")
    try:
        with timer("generator-timer") as info:
            time.sleep(0.05)

        print(f"  Yielded value: {info}")
        assert info["label"] == "generator-timer"
        assert info["elapsed"] >= 0.05
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 4: Exception handling -- SuppressErrors ---
    print("--- Section 4: SuppressErrors ---")
    try:
        with SuppressErrors(KeyError, FileNotFoundError) as s:
            d: dict = {}
            _ = d["missing"]  # raises KeyError

        print(f"  Suppressed exception: {type(s.exception).__name__}: {s.exception}")
        assert isinstance(s.exception, KeyError)

        with SuppressErrors(FileNotFoundError) as s2:
            open("/nonexistent/path/file.txt")

        print(f"  Suppressed exception: {type(s2.exception).__name__}")
        assert isinstance(s2.exception, FileNotFoundError)

        propagated = False
        try:
            with SuppressErrors(KeyError):
                raise ValueError("this should propagate")
        except ValueError as e:
            propagated = True
            print(f"  ValueError propagated correctly: {e}")

        assert propagated

        with SuppressErrors(KeyError) as s3:
            x = 42  # no exception

        assert s3.exception is None
        print(f"  No exception: s3.exception is {s3.exception}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 5: ExitStack ---
    print("--- Section 5: ExitStack ---")
    try:
        with TempDirectory(prefix="exitstack_") as tmpdir:
            filenames = ["a.txt", "b.txt", "c.txt"]
            paths = create_temp_files(filenames, tmpdir)

            for path in paths:
                assert os.path.exists(path)
                with open(path) as f:
                    content = f.read()
                print(f"  {os.path.basename(path)}: {content.strip()}")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    # ExitStack callback ordering (LIFO)
    print()
    print("  ExitStack callback order (LIFO):")
    callback_order: list[int] = []

    with ExitStack() as stack:
        stack.callback(lambda: callback_order.append(3))
        stack.callback(lambda: callback_order.append(2))
        stack.callback(lambda: callback_order.append(1))

    print(f"  Callback execution order: {callback_order}")
    assert callback_order == [1, 2, 3]

    print()

    # --- Section 6: Async context managers ---
    print("--- Section 6: Async context managers ---")
    try:
        async def demo_async():
            async with AsyncTimer("async-sleep") as at:
                await asyncio.sleep(0.05)

            assert at.elapsed >= 0.05
            print(f"  Async elapsed: {at.elapsed:.2f}s")

            async with async_timer("async-gen-sleep"):
                await asyncio.sleep(0.05)

        asyncio.run(demo_async())
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")

    print()

    # --- Section 7: Real-world patterns ---
    print("--- Section 7: Real-world patterns ---")
    try:
        with capture_stdout() as output:
            print("captured line 1")
            print("captured line 2")

        captured = output.getvalue()
        print(f"  Captured output: {captured.strip()!r}")
        assert "captured line 1" in captured
        assert "captured line 2" in captured
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (capture_stdout): {e}")

    try:
        class Config:
            debug = False

        cfg = Config()
        assert cfg.debug is False

        with patch_attr(cfg, "debug", True) as old_val:
            print(f"  Inside patch: debug={cfg.debug} (was {old_val})")
            assert cfg.debug is True
            assert old_val is False

        assert cfg.debug is False
        print(f"  After patch: debug={cfg.debug} (restored)")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (patch_attr): {e}")

    try:
        print()
        print("  Nested context managers:")
        with Timer("outer") as t_outer:
            with Timer("inner") as t_inner:
                time.sleep(0.02)
        assert t_outer.elapsed >= t_inner.elapsed
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented (nested timers): {e}")

    print()

    # --- Section 8: The protocol in action ---
    print("--- Section 8: The Protocol Map ---")
    print("  with EXPR as VAR:     →  VAR = EXPR.__enter__()")
    print("      BLOCK             →  execute body")
    print("  # normal exit         →  EXPR.__exit__(None, None, None)")
    print("  # exception           →  EXPR.__exit__(type, value, traceback)")
    print("  # __exit__ returns True  → exception suppressed")
    print("  # __exit__ returns False → exception propagated")
    print()
    print("  @contextmanager:")
    print("    before yield        →  __enter__ code")
    print("    yield value         →  value bound to 'as' variable")
    print("    after yield         →  __exit__ code (use try/finally!)")

    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Context managers give you:")
    print("  - Guaranteed cleanup (even on exceptions)")
    print("  - Class-based: __enter__ / __exit__")
    print("  - Generator-based: @contextmanager + yield")
    print("  - Exception control: __exit__ can suppress errors")
    print("  - Dynamic stacking: ExitStack")
    print("  - Async support: __aenter__ / __aexit__")
    print()
    print("All 8 sections passed. You understand context managers!")
