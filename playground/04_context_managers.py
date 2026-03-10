"""
Kata 04 -- Context Managers
Run: python playground/04_context_managers.py

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
        self._start = time.perf_counter()
        return self  # this becomes the 'as' variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        print(f"  [{self.label}] {self.elapsed:.4f}s")
        return False  # don't suppress exceptions


# ---------------------------------------------------------------------------
# Section 2: Class-based context manager -- TempDirectory
# ---------------------------------------------------------------------------

class TempDirectory:
    """Creates a temp directory on enter, cleans it up on exit."""

    def __init__(self, prefix: str = "kata_") -> None:
        self.prefix = prefix
        self.path: str | None = None

    def __enter__(self) -> str:
        self.path = tempfile.mkdtemp(prefix=self.prefix)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path and os.path.exists(self.path):
            shutil.rmtree(self.path)
        return False


# ---------------------------------------------------------------------------
# Section 3: Generator-based context manager with @contextmanager
# ---------------------------------------------------------------------------

@contextmanager
def timer(label: str = "Block"):
    """Generator-based timer context manager."""
    start = time.perf_counter()
    result = {"label": label, "elapsed": 0.0}
    try:
        yield result  # yielded value becomes the 'as' variable
    finally:
        result["elapsed"] = time.perf_counter() - start
        print(f"  [{label}] {result['elapsed']:.4f}s")


# ---------------------------------------------------------------------------
# Section 4: Exception handling in __exit__ -- SuppressErrors
# ---------------------------------------------------------------------------

class SuppressErrors:
    """Suppresses specified exception types, like contextlib.suppress."""

    def __init__(self, *exceptions: type[BaseException]) -> None:
        self.exceptions = exceptions
        self.exception: BaseException | None = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and issubclass(exc_type, self.exceptions):
            self.exception = exc_val
            return True  # suppress the exception
        return False  # let other exceptions propagate


# ---------------------------------------------------------------------------
# Section 5: ExitStack for dynamic context manager stacking
# ---------------------------------------------------------------------------

def create_temp_files(names: list[str], base_dir: str) -> list[str]:
    """Create multiple temp files using ExitStack to manage them."""
    paths = []
    with ExitStack() as stack:
        for name in names:
            filepath = os.path.join(base_dir, name)
            f = stack.enter_context(open(filepath, "w"))
            f.write(f"content of {name}\n")
            paths.append(filepath)
    # All files are closed here (ExitStack called __exit__ on each)
    return paths


# ---------------------------------------------------------------------------
# Section 6: Async context managers
# ---------------------------------------------------------------------------

class AsyncTimer:
    """Async context manager for timing async operations."""

    def __init__(self, label: str = "Block") -> None:
        self.label = label
        self.elapsed: float = 0.0

    async def __aenter__(self):
        self._start = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self._start
        print(f"  [async {self.label}] {self.elapsed:.4f}s")
        return False


@asynccontextmanager
async def async_timer(label: str = "Block"):
    """Generator-based async context manager."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"  [async-gen {label}] {elapsed:.4f}s")


# ---------------------------------------------------------------------------
# Section 7: Real-world patterns
# ---------------------------------------------------------------------------

@contextmanager
def capture_stdout():
    """Capture print output to a StringIO."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old_stdout


@contextmanager
def patch_attr(obj, attr, value):
    """Temporarily replace an attribute, restore on exit."""
    old_value = getattr(obj, attr)
    setattr(obj, attr, value)
    try:
        yield old_value
    finally:
        setattr(obj, attr, old_value)


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Class-based Timer ---
    print("--- Section 1: Class-based Timer ---")

    with Timer("sleep-test") as t:
        time.sleep(0.05)
    # Output: [sleep-test] 0.05XXs

    print(f"  Elapsed is accessible after: {t.elapsed:.2f}s")
    assert t.elapsed >= 0.05
    assert isinstance(t, Timer)
    print(f"  'as' variable is the Timer instance: {type(t).__name__}")

    print()

    # --- Section 2: TempDirectory ---
    print("--- Section 2: TempDirectory ---")

    with TempDirectory(prefix="kata_test_") as tmpdir:
        print(f"  Created temp dir: {tmpdir}")
        assert os.path.isdir(tmpdir)

        # Write a file inside it
        testfile = os.path.join(tmpdir, "hello.txt")
        with open(testfile, "w") as f:
            f.write("hello from context manager")
        assert os.path.exists(testfile)
        print(f"  File exists inside: {os.path.basename(testfile)}")
        saved_path = tmpdir

    # After the with block, the directory is gone
    assert not os.path.exists(saved_path)
    print(f"  Temp dir cleaned up: {not os.path.exists(saved_path)}")

    print()

    # --- Section 3: Generator-based @contextmanager ---
    print("--- Section 3: Generator-based @contextmanager ---")

    with timer("generator-timer") as info:
        time.sleep(0.05)
    # Output: [generator-timer] 0.05XXs

    print(f"  Yielded value: {info}")
    assert info["label"] == "generator-timer"
    assert info["elapsed"] >= 0.05

    print()

    # --- Section 4: Exception handling -- SuppressErrors ---
    print("--- Section 4: SuppressErrors ---")

    # Suppress a KeyError
    with SuppressErrors(KeyError, FileNotFoundError) as s:
        d: dict = {}
        _ = d["missing"]  # raises KeyError

    # We reach here because the KeyError was suppressed
    print(f"  Suppressed exception: {type(s.exception).__name__}: {s.exception}")
    assert isinstance(s.exception, KeyError)

    # Suppress FileNotFoundError
    with SuppressErrors(FileNotFoundError) as s2:
        open("/nonexistent/path/file.txt")

    print(f"  Suppressed exception: {type(s2.exception).__name__}")
    assert isinstance(s2.exception, FileNotFoundError)

    # Non-matching exceptions still propagate
    propagated = False
    try:
        with SuppressErrors(KeyError):
            raise ValueError("this should propagate")
    except ValueError as e:
        propagated = True
        print(f"  ValueError propagated correctly: {e}")

    assert propagated

    # No exception means .exception stays None
    with SuppressErrors(KeyError) as s3:
        x = 42  # no exception

    assert s3.exception is None
    print(f"  No exception: s3.exception is {s3.exception}")

    print()

    # --- Section 5: ExitStack ---
    print("--- Section 5: ExitStack ---")

    # Dynamic context manager stacking
    with TempDirectory(prefix="exitstack_") as tmpdir:
        filenames = ["a.txt", "b.txt", "c.txt"]
        paths = create_temp_files(filenames, tmpdir)

        # Verify all files were written and closed properly
        for path in paths:
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            print(f"  {os.path.basename(path)}: {content.strip()}")

    # ExitStack callback ordering (LIFO)
    print()
    print("  ExitStack callback order (LIFO):")
    callback_order: list[int] = []

    with ExitStack() as stack:
        stack.callback(lambda: callback_order.append(3))
        stack.callback(lambda: callback_order.append(2))
        stack.callback(lambda: callback_order.append(1))

    print(f"  Callback execution order: {callback_order}")
    # Callbacks fire in reverse registration order (LIFO)
    assert callback_order == [1, 2, 3]

    print()

    # --- Section 6: Async context managers ---
    print("--- Section 6: Async context managers ---")

    async def demo_async():
        # Class-based async CM
        async with AsyncTimer("async-sleep") as at:
            await asyncio.sleep(0.05)

        assert at.elapsed >= 0.05
        print(f"  Async elapsed: {at.elapsed:.2f}s")

        # Generator-based async CM
        async with async_timer("async-gen-sleep"):
            await asyncio.sleep(0.05)

    asyncio.run(demo_async())

    print()

    # --- Section 7: Real-world patterns ---
    print("--- Section 7: Real-world patterns ---")

    # Pattern 1: capture_stdout
    with capture_stdout() as output:
        print("captured line 1")
        print("captured line 2")

    captured = output.getvalue()
    print(f"  Captured output: {captured.strip()!r}")
    assert "captured line 1" in captured
    assert "captured line 2" in captured

    # Pattern 2: patch_attr
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

    # Pattern 3: Nested context managers
    print()
    print("  Nested context managers:")
    with Timer("outer") as t_outer:
        with Timer("inner") as t_inner:
            time.sleep(0.02)
        # inner exits first
    # outer exits second
    assert t_outer.elapsed >= t_inner.elapsed

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
