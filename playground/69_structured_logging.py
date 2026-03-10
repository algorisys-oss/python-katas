"""
Kata 69 -- Structured Logging
Run: python playground/69_structured_logging.py

Build structured JSON logging with request IDs via contextvars,
a custom JSON log formatter, and timing middleware that logs
request duration. Demonstrates production-grade logging patterns.

Completes within 5 seconds.
"""

from __future__ import annotations

import contextvars
import io
import json
import logging
import time
import uuid
from typing import Any, Callable


# ===========================================================================
# SECTION 1: JSON Log Formatter
# ===========================================================================
# A custom logging.Formatter that outputs JSON instead of plain text.
# Structured logs are machine-parseable -- essential for log aggregation
# tools like ELK, Datadog, or CloudWatch.

class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects.

    Each log line is a single JSON object with fields:
    - timestamp: ISO format timestamp
    - level: log level name (INFO, WARNING, ERROR, etc.)
    - message: the log message
    - logger: logger name
    - Any extra fields passed via the `extra` parameter

    Example output:
    {"timestamp": "2024-01-15T10:30:00", "level": "INFO",
     "message": "Request received", "request_id": "abc-123"}
    """

    # Fields from LogRecord that we always include
    BASE_FIELDS = {"timestamp", "level", "message", "logger"}

    # LogRecord attributes to exclude from extras
    RESERVED_ATTRS = {
        "args", "asctime", "created", "exc_info", "exc_text",
        "filename", "funcName", "levelname", "levelno", "lineno",
        "module", "msecs", "msg", "name", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "taskName",
        "thread", "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format a LogRecord as a JSON string."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add any extra fields (passed via `extra={}` in log calls)
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and key not in self.BASE_FIELDS:
                # Skip private attributes
                if not key.startswith("_"):
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, default=str)


# ===========================================================================
# SECTION 2: Request ID via contextvars
# ===========================================================================
# contextvars provides per-task/per-request context. A request_id set
# at the start of a request is automatically available to all log calls
# within that request -- even in deeply nested functions.

# The context variable that holds the current request ID
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIDFilter(logging.Filter):
    """Logging filter that adds request_id from contextvars to every record.

    This is the bridge between contextvars and the logging system:
    the filter reads the current request_id and injects it into every
    log record as an attribute, which the JSONFormatter then includes.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Always returns True (never filters out). Adds request_id field."""
        record.request_id = request_id_var.get()  # type: ignore[attr-defined]
        return True


def generate_request_id() -> str:
    """Generate a short, unique request ID."""
    return uuid.uuid4().hex[:12]


# ===========================================================================
# SECTION 3: Timing Middleware
# ===========================================================================
# Middleware that logs request duration and adds timing information.

class TimingMiddleware:
    """Middleware that logs the duration of each request.

    Wraps a handler function and logs:
    - Request start (with method, path)
    - Request end (with status code, duration in ms)
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("ignite.timing")

    def wrap(self, handler: Callable) -> Callable:
        """Wrap a handler function with timing."""
        def timed_handler(request: dict[str, Any]) -> dict[str, Any]:
            method = request.get("method", "GET")
            path = request.get("path", "/")

            self.logger.info(
                "Request started",
                extra={"method": method, "path": path},
            )

            start = time.monotonic()
            try:
                response = handler(request)
                duration_ms = (time.monotonic() - start) * 1000
                status = response.get("status_code", 200)

                self.logger.info(
                    "Request completed",
                    extra={
                        "method": method,
                        "path": path,
                        "status_code": status,
                        "duration_ms": round(duration_ms, 2),
                    },
                )
                return response

            except Exception as exc:
                duration_ms = (time.monotonic() - start) * 1000
                self.logger.error(
                    "Request failed",
                    extra={
                        "method": method,
                        "path": path,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(exc),
                    },
                    exc_info=True,
                )
                raise

        return timed_handler


# ===========================================================================
# SECTION 4: Structured Logger Setup
# ===========================================================================
# Helper to set up a logger with JSON formatting and request ID injection.

def setup_logger(
    name: str = "ignite",
    level: int = logging.DEBUG,
    stream: io.StringIO | None = None,
) -> tuple[logging.Logger, io.StringIO]:
    """Create a configured structured logger.

    Returns (logger, stream) so we can inspect the output in demos.
    """
    logger = logging.Logger(name, level=level)

    # Use provided stream or create one
    output = stream or io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIDFilter())
    logger.addHandler(handler)

    return logger, output


def parse_log_lines(output: io.StringIO) -> list[dict[str, Any]]:
    """Parse JSON log lines from a StringIO stream."""
    output.seek(0)
    lines = output.read().strip().split("\n")
    return [json.loads(line) for line in lines if line.strip()]


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_json_formatter():
    """Show JSON log output."""
    print("--- Section 1: JSON Log Formatter ---")

    logger, output = setup_logger("demo.formatter")

    logger.info("Server starting", extra={"host": "0.0.0.0", "port": 8000})
    logger.warning("Deprecated endpoint called", extra={"path": "/v1/users"})
    logger.error("Database connection failed", extra={
        "host": "db.example.com",
        "retry_count": 3,
    })

    logs = parse_log_lines(output)

    for log in logs:
        print(f"  {json.dumps(log, indent=None)}")

    assert len(logs) == 3
    assert logs[0]["level"] == "INFO"
    assert logs[0]["message"] == "Server starting"
    assert logs[0]["host"] == "0.0.0.0"
    assert logs[0]["port"] == 8000
    assert logs[1]["level"] == "WARNING"
    assert logs[2]["level"] == "ERROR"
    assert logs[2]["retry_count"] == 3

    print("  [PASS] JSON formatter works")


def demo_request_id():
    """Show request ID propagation via contextvars."""
    print("\n--- Section 2: Request ID via contextvars ---")

    logger, output = setup_logger("demo.reqid")

    # Simulate two concurrent requests
    def handle_request(path: str):
        """Each request gets its own request_id."""
        rid = generate_request_id()
        request_id_var.set(rid)

        logger.info("Processing request", extra={"path": path})
        # Simulate calling a nested function
        fetch_data(logger, path)
        logger.info("Request complete", extra={"path": path})

    def fetch_data(log: logging.Logger, path: str):
        """Deeply nested function -- still gets the request_id."""
        log.info("Fetching data from DB", extra={"table": "users"})

    handle_request("/api/users")
    handle_request("/api/posts")

    logs = parse_log_lines(output)

    print(f"  Generated {len(logs)} log entries:")
    for log in logs:
        print(f"    [{log['level']}] {log['message']} "
              f"request_id={log.get('request_id', 'none')}")

    # Verify request IDs are present and consistent within each request
    assert len(logs) == 6
    # First 3 logs should share a request_id
    first_rid = logs[0]["request_id"]
    assert logs[1]["request_id"] == first_rid
    assert logs[2]["request_id"] == first_rid
    # Next 3 should share a different one
    second_rid = logs[3]["request_id"]
    assert second_rid != first_rid
    assert logs[4]["request_id"] == second_rid
    assert logs[5]["request_id"] == second_rid

    print("  [PASS] Request ID propagation works")

    # Reset for other demos
    request_id_var.set(None)


def demo_timing_middleware():
    """Show timing middleware logging request duration."""
    print("\n--- Section 3: Timing Middleware ---")

    logger, output = setup_logger("demo.timing")
    middleware = TimingMiddleware(logger)

    def slow_handler(request: dict) -> dict:
        """Simulate a slow handler."""
        time.sleep(0.01)  # 10ms delay
        return {"status_code": 200, "body": {"users": ["Alice"]}}

    def error_handler(request: dict) -> dict:
        """Handler that raises an error."""
        raise ValueError("Something went wrong")

    # Set a request ID for context
    request_id_var.set(generate_request_id())

    # Successful request
    timed = middleware.wrap(slow_handler)
    response = timed({"method": "GET", "path": "/api/users"})
    assert response["status_code"] == 200

    # Failed request
    timed_error = middleware.wrap(error_handler)
    try:
        timed_error({"method": "POST", "path": "/api/crash"})
    except ValueError:
        pass

    logs = parse_log_lines(output)

    print(f"  Timing log entries:")
    for log in logs:
        duration = log.get("duration_ms", "N/A")
        print(f"    [{log['level']}] {log['message']} "
              f"path={log.get('path', '?')} duration={duration}ms")

    # Verify timing
    assert len(logs) == 4  # start + end for each request
    completed = [l for l in logs if l["message"] == "Request completed"]
    assert len(completed) == 1
    assert completed[0]["duration_ms"] >= 5  # At least some time passed
    assert completed[0]["status_code"] == 200

    failed = [l for l in logs if l["message"] == "Request failed"]
    assert len(failed) == 1
    assert "error" in failed[0]

    print("  [PASS] Timing middleware works")

    request_id_var.set(None)


def demo_log_levels():
    """Show log level filtering."""
    print("\n--- Section 4: Log Levels & Filtering ---")

    # Logger that only shows WARNING and above
    logger, output = setup_logger("demo.levels", level=logging.WARNING)

    logger.debug("This should be filtered out")
    logger.info("This should also be filtered out")
    logger.warning("Disk space low", extra={"percent_free": 5})
    logger.error("Out of memory", extra={"available_mb": 12})
    logger.critical("System shutting down")

    logs = parse_log_lines(output)

    print(f"  Logger level: WARNING")
    print(f"  Messages logged: {len(logs)} (out of 5 attempted)")
    for log in logs:
        print(f"    [{log['level']}] {log['message']}")

    assert len(logs) == 3
    assert logs[0]["level"] == "WARNING"
    assert logs[1]["level"] == "ERROR"
    assert logs[2]["level"] == "CRITICAL"

    print("  [PASS] Log level filtering works")


def demo_exception_logging():
    """Show exception info in structured logs."""
    print("\n--- Section 5: Exception Logging ---")

    logger, output = setup_logger("demo.exceptions")

    try:
        data = {"users": []}
        first_user = data["users"][0]
    except IndexError:
        logger.error(
            "Failed to get first user",
            extra={"data_keys": list(data.keys())},
            exc_info=True,
        )

    logs = parse_log_lines(output)
    assert len(logs) == 1

    log = logs[0]
    print(f"  Log entry with exception:")
    print(f"    level: {log['level']}")
    print(f"    message: {log['message']}")
    print(f"    exception.type: {log['exception']['type']}")
    print(f"    exception.message: {log['exception']['message']}")
    print(f"    traceback present: {bool(log['exception']['traceback'])}")
    print(f"    extra data_keys: {log['data_keys']}")

    assert log["exception"]["type"] == "IndexError"
    assert "traceback" in log["exception"]
    assert log["data_keys"] == ["users"]

    print("  [PASS] Exception logging works")


def demo_full_request_flow():
    """Show a complete request flow with structured logging."""
    print("\n--- Section 6: Full Request Flow ---")

    logger, output = setup_logger("ignite")
    middleware = TimingMiddleware(logger)

    def get_users_handler(request: dict) -> dict:
        logger.info("Querying database", extra={"table": "users"})
        users = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        logger.info("Query complete", extra={"count": len(users)})
        return {"status_code": 200, "body": {"users": users}}

    # Simulate a request
    rid = generate_request_id()
    request_id_var.set(rid)

    timed = middleware.wrap(get_users_handler)
    response = timed({"method": "GET", "path": "/api/users"})

    logs = parse_log_lines(output)

    print(f"  Request flow ({len(logs)} log entries):")
    for log in logs:
        extras = {k: v for k, v in log.items()
                  if k not in ("timestamp", "level", "message",
                               "logger", "request_id")}
        extras_str = ", ".join(f"{k}={v}" for k, v in extras.items())
        print(f"    [{log['level']}] {log['message']}"
              f"{' | ' + extras_str if extras_str else ''}")

    # All logs should have the same request_id
    for log in logs:
        assert log["request_id"] == rid, (
            f"Expected request_id={rid}, got {log['request_id']}"
        )
    print(f"\n  All {len(logs)} entries share request_id={rid}")
    assert response["status_code"] == 200

    request_id_var.set(None)

    print("  [PASS] Full request flow works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_json_formatter()
    demo_request_id()
    demo_timing_middleware()
    demo_log_levels()
    demo_exception_logging()
    demo_full_request_flow()

    print("\n--- Summary ---")
    print("Structured logging gives our Ignite framework:")
    print("  - JSON log output (machine-parseable)")
    print("  - Request ID propagation via contextvars")
    print("  - Timing middleware for request duration")
    print("  - Log level filtering (DEBUG through CRITICAL)")
    print("  - Exception info with traceback in JSON")
    print("  - Correlated logs across the full request lifecycle")
    print("\nAll 6 sections passed. Structured logging mastered!")
    print("Next up: Kata 70 -- CLI tool!")


if __name__ == "__main__":
    main()
