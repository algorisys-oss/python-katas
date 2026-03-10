"""
Kata 33 -- Logging & Debugging
Run: python playground/skeletons/33_logging_debugging.py

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

    # TODO: Create a named logger with logging.getLogger("basics")
    # TODO: Set the logger level to DEBUG
    # TODO: Clear any existing handlers and set propagate=False
    # HINT: logger.handlers.clear(); logger.propagate = False

    # TODO: Create a StringIO buffer and a StreamHandler writing to it
    # TODO: Set the handler level to DEBUG
    # TODO: Create a Formatter with "[%(levelname)s] %(name)s: %(message)s"
    # TODO: Attach formatter to handler, then handler to logger

    # TODO: Log one message at each level: debug, info, warning, error, critical
    # HINT: logger.debug("Detailed diagnostic info"), etc.

    # TODO: Read the buffer and print each line
    # TODO: Verify all 5 levels were logged (assert len == 5)

    # Show numeric level values
    print(f"  Level numbers: DEBUG={logging.DEBUG}, INFO={logging.INFO}, "
          f"WARNING={logging.WARNING}, ERROR={logging.ERROR}, "
          f"CRITICAL={logging.CRITICAL}")

    # TODO: Create a second logger "basics.context" with a simple formatter
    # TODO: Log a message with %-style arguments: "User %s performed %s from %s"
    # HINT: logger.info("User %s performed %s from %s", "alice", "login", "192.168.1.1")

    pass


# ===========================================================================
# SECTION 2: Handlers & Formatters
# ===========================================================================

def demo_handlers_formatters():
    """Demonstrate multiple handlers with different formatters and levels."""

    # TODO: Create logger "handlers_demo" at DEBUG level, clear handlers
    # HINT: logger.propagate = False to avoid root logger noise

    # TODO: Create Handler 1 -- StringIO handler at INFO level
    # HINT: logging.StreamHandler(io.StringIO())

    # TODO: Create Handler 2 -- FileHandler at DEBUG level writing to /tmp/kata33_debug.log
    # HINT: logging.FileHandler(path, mode="w")

    # TODO: Create Handler 3 -- StringIO handler at WARNING level with custom formatter
    # HINT: Formatter("[%(levelname)s] %(name)s: %(message)s (%(name)s)")

    # TODO: Add all three handlers to the logger

    # TODO: Log messages at DEBUG, INFO (x2), WARNING, ERROR levels

    # TODO: Verify StringIO handler captured 4 records (INFO+)
    # TODO: Verify file handler wrote 5 records (DEBUG+)
    # TODO: Print the custom formatter output

    print("  Multiple handlers allow routing: console=INFO+, file=DEBUG+, errors=ERROR+")

    pass


# ===========================================================================
# SECTION 3: Filters & Logger Hierarchy
# ===========================================================================

class SensitiveDataFilter(logging.Filter):
    """Redact log records that mention sensitive keywords."""

    SENSITIVE_KEYS = {"password", "token", "secret", "api_key"}

    def filter(self, record: logging.LogRecord) -> bool:
        # TODO: Get the message with record.getMessage()
        # TODO: Check if any SENSITIVE_KEYS appear in the message (case-insensitive)
        # TODO: If found, replace record.msg with "[REDACTED -- contains sensitive data]"
        #       and set record.args = ()
        # TODO: Return True to keep the record (modified or not)
        # HINT: Returning False would drop the record entirely
        pass


class NoisyFilter(logging.Filter):
    """Suppress records matching certain patterns."""

    def __init__(self, suppress_patterns: list[str]):
        super().__init__()
        self.suppress_patterns = suppress_patterns
        self.suppressed_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        # TODO: Check if any suppress_patterns appear in the message
        # TODO: If found, increment suppressed_count and return False (drop it)
        # TODO: Otherwise return True (keep it)
        pass


def demo_filters_hierarchy():
    """Demonstrate filters and logger hierarchy with propagation."""

    # --- Filters ---
    # TODO: Create logger "filtered" at DEBUG, clear handlers, propagate=False
    # TODO: Add a StreamHandler with StringIO buffer
    # TODO: Add SensitiveDataFilter and NoisyFilter(["heartbeat"]) to logger

    # TODO: Log three messages:
    #   1. "Normal operational message" (kept as-is)
    #   2. "User set password=secret123" (redacted by SensitiveDataFilter)
    #   3. "heartbeat check ok" (dropped by NoisyFilter)

    # TODO: Verify: 2 lines in output, first is normal, second is REDACTED
    # TODO: Verify: noisy_filter.suppressed_count == 1

    # --- Logger hierarchy ---
    # TODO: Create parent logger "app" with a StringIO handler
    # TODO: Create child loggers "app.db" and "app.db.queries" (no handlers)
    # HINT: Children propagate to parent by default (propagate=True)

    # TODO: Log from children:
    #   child_db.info("Connected to SQLite")
    #   child_queries.debug("SELECT * FROM users")
    #   child_db.warning("Connection pool nearly full")

    # TODO: Verify parent received 3 propagated records
    print(f"  Logger hierarchy: app -> app.db -> app.db.queries")

    pass


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

    # TODO: Wrap cause_error() in try/except ZeroDivisionError
    # TODO: Print the exception message
    # TODO: Get traceback with sys.exc_info()[2]
    # TODO: Extract frames with traceback.extract_tb(tb)
    # TODO: Print frame count and each frame's file/line/name
    # HINT: frame.filename, frame.lineno, frame.name

    # TODO: Format full exception with traceback.format_exc()
    # TODO: Print the first line and verify it contains "Traceback"

    # --- Chained exceptions ---
    # TODO: Raise ValueError("original"), catch it, then raise RuntimeError("wrapper")
    #       using "raise ... from ..." syntax
    # TODO: Walk the __cause__ chain and print it
    # HINT: current = e; while current: chain.append(...); current = current.__cause__

    # --- format_exception returns a list ---
    # TODO: Catch a ValueError from int("not_a_number")
    # TODO: Call traceback.format_exception(*sys.exc_info())
    # TODO: Verify it returns a list of strings
    print(f"  traceback.format_exception() returns a list of strings")

    pass


# ===========================================================================
# SECTION 5: Warnings Module
# ===========================================================================

def demo_warnings():
    """Demonstrate warnings.warn, custom categories, and filterwarnings."""

    original_filters = warnings.filters[:]
    warnings.resetwarnings()

    # --- Basic deprecation warning ---
    def new_function():
        return "new result"

    def old_function():
        # TODO: Issue a DeprecationWarning with warnings.warn()
        # HINT: warnings.warn("message", DeprecationWarning, stacklevel=2)
        return new_function()

    # TODO: Use warnings.catch_warnings(record=True) context manager
    # TODO: Set warnings.simplefilter("always") inside the context
    # TODO: Call old_function() and verify 1 warning was captured
    # TODO: Print the warning message and category name

    # --- Custom warning category ---
    class DataQualityWarning(UserWarning):
        """Issued when data quality thresholds are breached."""
        pass

    # TODO: Issue a DataQualityWarning and capture it
    # TODO: Print: "Custom warning: DataQualityWarning -- 15 rows had null values"

    # --- filterwarnings('error') converts warnings to exceptions ---
    # TODO: Use filterwarnings("error", category=RuntimeWarning)
    # TODO: Issue a RuntimeWarning and catch the resulting exception
    # TODO: Print confirmation that it was caught

    # --- stacklevel demonstration ---
    # TODO: Write inner_warn() that calls warnings.warn() with stacklevel=2
    # TODO: Write outer_warn() that calls inner_warn()
    # TODO: Verify the warning points to the caller, not the warn() call
    print("  stacklevel=2 points warning to caller, not to warn() call")

    warnings.filters[:] = original_filters


# ===========================================================================
# SECTION 6: Debugging (pdb reference -- not invoked)
# ===========================================================================

def demo_debugging_reference():
    """Show breakpoint() and pdb usage as informational prints.

    IMPORTANT: We never actually invoke pdb or breakpoint() here because
    that would block waiting for interactive input.
    """

    # TODO: Print information about breakpoint() mechanism:
    #   - breakpoint() calls sys.breakpointhook
    #   - PYTHONBREAKPOINT=0 disables all breakpoints
    #   - PYTHONBREAKPOINT=module.func routes to custom debugger

    # TODO: Print key pdb commands as a reference table:
    #   n (next), s (step), c (continue), p expr, l (list),
    #   w (where), b N, cl N, r (return), q (quit)
    # HINT: Store commands as a list of (command, description) tuples

    # TODO: Print post-mortem and best practices info
    print("  Post-mortem debugging: pdb.pm() after an unhandled exception")
    print("  breakpoint() is preferred over pdb.set_trace() (PEP 553)")

    pass


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
