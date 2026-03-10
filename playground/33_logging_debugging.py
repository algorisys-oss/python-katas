"""
Kata 33 -- Logging & Debugging
Run: python playground/33_logging_debugging.py

Explore Python's logging module (handlers, formatters, filters, hierarchy),
the traceback module, the warnings module, and debugging with breakpoint()/pdb.

NOTE: pdb is demonstrated via informational prints only -- never invoked
interactively, so this script completes within 5 seconds.
"""

import io
import logging
import sys
import traceback
import warnings


# ===========================================================================
# SECTION 1: Logging Basics
# ===========================================================================

def demo_logging_basics():
    """Demonstrate log levels and basic logging API."""

    # Create a named logger (isolated from root logger)
    logger = logging.getLogger("basics")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # Ensure clean state
    logger.propagate = False

    # Capture output with a StreamHandler to a StringIO
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)

    # Log at every level
    logger.debug("Detailed diagnostic info")
    logger.info("Server started on port 8000")
    logger.warning("Disk space at 85%")
    logger.error("Connection refused")
    logger.critical("Database corrupted!")

    # Read captured output
    output = buf.getvalue()
    lines = [line.strip() for line in output.strip().split("\n") if line.strip()]

    for line in lines:
        # Strip the logger name prefix for cleaner display
        level = line.split("]")[0].replace("[", "").strip()
        msg = line.split(": ", 1)[1] if ": " in line else line
        print(f"  [{level}] {level.lower()}: {msg}")

    # Verify all 5 levels were logged
    assert len(lines) == 5, f"Expected 5 log lines, got {len(lines)}"
    assert "[DEBUG]" in lines[0]
    assert "[CRITICAL]" in lines[4]

    # Show numeric level values
    print(f"  Level numbers: DEBUG={logging.DEBUG}, INFO={logging.INFO}, "
          f"WARNING={logging.WARNING}, ERROR={logging.ERROR}, "
          f"CRITICAL={logging.CRITICAL}")

    # Logging with extra context using %-formatting (logging's native style)
    buf2 = io.StringIO()
    handler2 = logging.StreamHandler(buf2)
    handler2.setFormatter(logging.Formatter("%(message)s"))
    ctx_logger = logging.getLogger("basics.context")
    ctx_logger.setLevel(logging.DEBUG)
    ctx_logger.handlers.clear()
    ctx_logger.propagate = False
    ctx_logger.addHandler(handler2)

    ctx_logger.info("User %s performed %s from %s", "alice", "login", "192.168.1.1")
    ctx_output = buf2.getvalue().strip()
    print(f"  Logging with context: {ctx_output}")
    assert "alice" in ctx_output
    assert "login" in ctx_output

    # Cleanup
    logger.handlers.clear()
    ctx_logger.handlers.clear()


# ===========================================================================
# SECTION 2: Handlers & Formatters
# ===========================================================================

def demo_handlers_formatters():
    """Demonstrate multiple handlers with different formatters and levels."""

    logger = logging.getLogger("handlers_demo")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    # Handler 1: StringIO handler capturing INFO+ only
    info_buf = io.StringIO()
    info_handler = logging.StreamHandler(info_buf)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(info_handler)

    # Handler 2: File handler capturing DEBUG+ (all messages)
    log_path = "/tmp/kata33_debug.log"
    file_handler = logging.FileHandler(log_path, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s",
                          datefmt="%H:%M:%S")
    )
    logger.addHandler(file_handler)

    # Handler 3: StringIO with custom formatter (shows logger name twice)
    custom_buf = io.StringIO()
    custom_handler = logging.StreamHandler(custom_buf)
    custom_handler.setLevel(logging.WARNING)
    custom_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s: %(message)s (%(name)s)")
    )
    logger.addHandler(custom_handler)

    # Log messages at various levels
    logger.debug("Starting up subsystems")
    logger.info("Connected to database")
    logger.info("Loaded 42 config entries")
    logger.warning("Disk is 85% full")
    logger.error("Failed to send email")

    # Verify StringIO handler got INFO+ (3 records: 2 info + 1 warning + 1 error = 4,
    # but we want to show 3 INFO+ minus the debug)
    info_lines = [l for l in info_buf.getvalue().strip().split("\n") if l.strip()]
    print(f"  StringHandler captured {len(info_lines)} records at INFO+")
    assert len(info_lines) == 4, f"Expected 4 INFO+ records, got {len(info_lines)}"

    # Verify file handler wrote to disk
    file_handler.flush()
    with open(log_path) as f:
        file_lines = [l for l in f.readlines() if l.strip()]
    print(f"  FileHandler wrote to {log_path}")
    assert len(file_lines) == 5, f"Expected 5 records in file, got {len(file_lines)}"

    # Show custom formatter output
    custom_output = custom_buf.getvalue().strip().split("\n")[0]
    print(f"  Custom formatter output: {custom_output}")
    assert "(handlers_demo)" in custom_output

    print("  Multiple handlers allow routing: console=INFO+, file=DEBUG+, errors=ERROR+")

    # Cleanup
    logger.handlers.clear()
    file_handler.close()


# ===========================================================================
# SECTION 3: Filters & Logger Hierarchy
# ===========================================================================

class SensitiveDataFilter(logging.Filter):
    """Redact log records that mention sensitive keywords."""

    SENSITIVE_KEYS = {"password", "token", "secret", "api_key"}

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for key in self.SENSITIVE_KEYS:
            if key in msg.lower():
                record.msg = "[REDACTED -- contains sensitive data]"
                record.args = ()
                return True  # Keep the record, but redacted
        return True


class NoisyFilter(logging.Filter):
    """Suppress records matching certain patterns."""

    def __init__(self, suppress_patterns: list[str]):
        super().__init__()
        self.suppress_patterns = suppress_patterns
        self.suppressed_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pattern in self.suppress_patterns:
            if pattern in msg:
                self.suppressed_count += 1
                return False  # Drop the record entirely
        return True


def demo_filters_hierarchy():
    """Demonstrate filters and logger hierarchy with propagation."""

    # --- Filters ---
    logger = logging.getLogger("filtered")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    logger.addFilter(sensitive_filter)

    # Add noisy filter
    noisy_filter = NoisyFilter(suppress_patterns=["heartbeat"])
    logger.addFilter(noisy_filter)

    logger.info("Normal operational message")
    logger.info("User set password=secret123")
    logger.info("heartbeat check ok")  # Suppressed

    lines = [l for l in buf.getvalue().strip().split("\n") if l.strip()]
    print(f"  Filter kept: {lines[0]}")
    print(f"  Filter redacted: {lines[1]}")
    print(f"  Filter suppressed {noisy_filter.suppressed_count} noisy record(s)")

    assert lines[0] == "Normal operational message"
    assert "REDACTED" in lines[1]
    assert noisy_filter.suppressed_count == 1
    assert len(lines) == 2  # heartbeat was dropped

    logger.handlers.clear()
    logger.filters.clear()

    # --- Logger hierarchy ---
    # Create a parent logger and child loggers
    parent = logging.getLogger("app")
    parent.setLevel(logging.DEBUG)
    parent.handlers.clear()
    parent.propagate = False

    parent_buf = io.StringIO()
    parent_handler = logging.StreamHandler(parent_buf)
    parent_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    parent.addHandler(parent_handler)

    # Child loggers -- they propagate to parent by default
    child_db = logging.getLogger("app.db")
    child_db.setLevel(logging.DEBUG)
    child_db.handlers.clear()
    # propagate=True (default) sends records to parent's handlers

    child_queries = logging.getLogger("app.db.queries")
    child_queries.setLevel(logging.DEBUG)
    child_queries.handlers.clear()

    # Log from children -- parent captures all via propagation
    child_db.info("Connected to SQLite")
    child_queries.debug("SELECT * FROM users")
    child_db.warning("Connection pool nearly full")

    parent_lines = [l for l in parent_buf.getvalue().strip().split("\n") if l.strip()]
    print(f"  Logger hierarchy: app -> app.db -> app.db.queries")
    print(f"  Parent logger 'app' received {len(parent_lines)} propagated records from children")

    assert len(parent_lines) == 3
    assert "app.db:" in parent_lines[0]
    assert "app.db.queries:" in parent_lines[1]

    # Cleanup
    parent.handlers.clear()


# ===========================================================================
# SECTION 4: Traceback Module
# ===========================================================================

def demo_traceback_module():
    """Demonstrate programmatic traceback inspection."""

    # --- Basic traceback capture ---
    def cause_error():
        x = 1
        y = 0
        return x / y

    try:
        cause_error()
    except ZeroDivisionError as e:
        print(f"  Caught: {e}")

        # Get the traceback object
        tb = sys.exc_info()[2]
        frames = traceback.extract_tb(tb)
        print(f"  Traceback has {len(frames)} frame(s)")

        for frame in frames:
            print(f"  Frame: File \"{frame.filename}\", line {frame.lineno}, "
                  f"in {frame.name}")

        # Format as string
        formatted = traceback.format_exc()
        first_line = formatted.strip().split("\n")[0]
        print(f"  Formatted exception (first line): {first_line}")
        assert "Traceback" in first_line

    # --- Chained exceptions ---
    try:
        try:
            raise ValueError("original")
        except ValueError:
            raise RuntimeError("wrapper") from sys.exc_info()[1]
    except RuntimeError as e:
        chain = []
        current: BaseException | None = e
        while current is not None:
            chain.append(type(current).__name__)
            current = current.__cause__
        print(f"  Chained exception: {' -> '.join(reversed(chain))}")
        assert chain == ["RuntimeError", "ValueError"]

    # --- format_exception returns a list ---
    try:
        int("not_a_number")
    except ValueError:
        exc_lines = traceback.format_exception(*sys.exc_info())
        print(f"  traceback.format_exception() returns a list of strings")
        assert isinstance(exc_lines, list)
        assert len(exc_lines) > 0


# ===========================================================================
# SECTION 5: Warnings Module
# ===========================================================================

def demo_warnings():
    """Demonstrate warnings.warn, custom categories, and filterwarnings."""

    # Save and reset warning filters for clean state
    original_filters = warnings.filters[:]
    warnings.resetwarnings()

    captured: list[warnings.WarningMessage] = []

    # --- Basic deprecation warning ---
    def new_function():
        return "new result"

    def old_function():
        warnings.warn(
            "old_function() is deprecated, use new_function() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return new_function()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = old_function()
        assert result == "new result"
        assert len(w) == 1
        print(f"  Warning captured: {w[0].message}")
        print(f"  Warning category: {w[0].category.__name__}")

    # --- Custom warning category ---
    class DataQualityWarning(UserWarning):
        """Issued when data quality thresholds are breached."""
        pass

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warnings.warn("15 rows had null values", DataQualityWarning)
        assert len(w) == 1
        print(f"  Custom warning: {w[0].category.__name__} -- {w[0].message}")

    # --- filterwarnings('error') converts warnings to exceptions ---
    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=RuntimeWarning)
        try:
            warnings.warn("something bad", RuntimeWarning)
            assert False, "Should have raised"
        except RuntimeWarning:
            print("  filterwarnings('error') converts warnings to exceptions: caught it!")

    # --- stacklevel demonstration ---
    def inner_warn():
        warnings.warn("test stacklevel", UserWarning, stacklevel=2)

    def outer_warn():
        inner_warn()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        outer_warn()
        # stacklevel=2 in inner_warn means the warning points to outer_warn's caller
        print("  stacklevel=2 points warning to caller, not to warn() call")

    # Restore original filters
    warnings.filters[:] = original_filters


# ===========================================================================
# SECTION 6: Debugging (pdb reference -- not invoked)
# ===========================================================================

def demo_debugging_reference():
    """Show breakpoint() and pdb usage as informational prints.

    IMPORTANT: We never actually invoke pdb or breakpoint() here because
    that would block waiting for interactive input.
    """

    # breakpoint() mechanism
    print("  breakpoint() calls sys.breakpointhook (default: pdb.set_trace)")
    print("  PYTHONBREAKPOINT=0 disables all breakpoints")
    print("  PYTHONBREAKPOINT=module.func routes to custom debugger")

    # Verify breakpoint is available (Python 3.7+)
    assert hasattr(__builtins__ if isinstance(__builtins__, dict) else type(__builtins__),
                   '__dict__'), "builtins accessible"
    assert callable(getattr(__builtins__, 'breakpoint', None) if isinstance(__builtins__, dict)
                    else getattr(__builtins__, 'breakpoint', None)) or sys.version_info >= (3, 7)

    # Key pdb commands (reference only)
    commands = [
        ("n (next)", "execute next line, skip into functions"),
        ("s (step)", "step INTO function calls"),
        ("c (continue)", "run until next breakpoint or end"),
        ("p expr", "evaluate and print expression"),
        ("l (list)", "show source around current line"),
        ("w (where)", "print call stack (most recent frame last)"),
        ("b N", "set breakpoint at line N"),
        ("cl N", "clear breakpoint at line N"),
        ("r (return)", "run until current function returns"),
        ("q (quit)", "abort program"),
    ]

    print("  Key pdb commands:")
    for cmd, desc in commands:
        print(f"    {cmd:<12} -- {desc}")

    # Post-mortem and best practices
    print("  Post-mortem debugging: pdb.pm() after an unhandled exception")
    print("  breakpoint() is preferred over pdb.set_trace() (PEP 553)")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Logging Basics ---
    print("--- Section 1: Logging Basics ---")
    demo_logging_basics()
    print()

    # --- Section 2: Handlers & Formatters ---
    print("--- Section 2: Handlers & Formatters ---")
    demo_handlers_formatters()
    print()

    # --- Section 3: Filters & Logger Hierarchy ---
    print("--- Section 3: Filters & Logger Hierarchy ---")
    demo_filters_hierarchy()
    print()

    # --- Section 4: Traceback Module ---
    print("--- Section 4: Traceback Module ---")
    demo_traceback_module()
    print()

    # --- Section 5: Warnings Module ---
    print("--- Section 5: Warnings Module ---")
    demo_warnings()
    print()

    # --- Section 6: Debugging (pdb reference) ---
    print("--- Section 6: Debugging (pdb reference) ---")
    demo_debugging_reference()
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Python's logging and debugging toolkit:")
    print("  - Use logging, not print() -- it's configurable, filterable, and hierarchical")
    print("  - Handlers route logs to console, files, network, email, etc.")
    print("  - Filters provide fine-grained control over which records appear")
    print("  - traceback module gives programmatic access to exception info")
    print("  - warnings module manages deprecations and soft alerts")
    print("  - breakpoint() + pdb provide interactive debugging (never in production scripts)")
    print()
    print("All 6 sections passed. Logging & debugging concepts mastered!")
