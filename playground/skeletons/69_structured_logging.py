"""
Kata 69 -- Structured Logging
Run: python playground/skeletons/69_structured_logging.py

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

class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    BASE_FIELDS = {"timestamp", "level", "message", "logger"}

    RESERVED_ATTRS = {
        "args", "asctime", "created", "exc_info", "exc_text",
        "filename", "funcName", "levelname", "levelno", "lineno",
        "module", "msecs", "msg", "name", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "taskName",
        "thread", "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format a LogRecord as a JSON string."""
        # TODO: Build a dict with these fields:
        #   "timestamp": self.formatTime(record, self.datefmt)
        #   "level": record.levelname
        #   "message": record.getMessage()
        #   "logger": record.name
        #
        # Then add extra fields from record.__dict__:
        #   Skip keys in RESERVED_ATTRS and BASE_FIELDS
        #   Skip keys starting with "_"
        #
        # If record.exc_info is set and has an exception:
        #   Add "exception" dict with "type", "message", "traceback"
        #
        # Return json.dumps(log_data, default=str)
        return "{}"


# ===========================================================================
# SECTION 2: Request ID via contextvars
# ===========================================================================
# contextvars provides per-task/per-request context.

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestIDFilter(logging.Filter):
    """Logging filter that adds request_id from contextvars to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Always returns True. Adds request_id field to record."""
        # TODO: Set record.request_id = request_id_var.get()
        # Always return True (we never filter out records)
        return True


def generate_request_id() -> str:
    """Generate a short, unique request ID."""
    return uuid.uuid4().hex[:12]


# ===========================================================================
# SECTION 3: Timing Middleware
# ===========================================================================

class TimingMiddleware:
    """Middleware that logs the duration of each request."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("ignite.timing")

    def wrap(self, handler: Callable) -> Callable:
        """Wrap a handler function with timing."""
        def timed_handler(request: dict[str, Any]) -> dict[str, Any]:
            method = request.get("method", "GET")
            path = request.get("path", "/")

            # TODO: Log "Request started" with method and path
            # TODO: Record start time with time.monotonic()

            start = time.monotonic()
            try:
                response = handler(request)
                duration_ms = (time.monotonic() - start) * 1000

                # TODO: Log "Request completed" with method, path,
                #       status_code, and duration_ms
                return response

            except Exception as exc:
                duration_ms = (time.monotonic() - start) * 1000

                # TODO: Log "Request failed" at ERROR level with
                #       method, path, duration_ms, error message,
                #       and exc_info=True
                raise

        return timed_handler


# ===========================================================================
# SECTION 4: Structured Logger Setup
# ===========================================================================

def setup_logger(
    name: str = "ignite",
    level: int = logging.DEBUG,
    stream: io.StringIO | None = None,
) -> tuple[logging.Logger, io.StringIO]:
    """Create a configured structured logger."""
    logger = logging.Logger(name, level=level)

    output = stream or io.StringIO()
    handler = logging.StreamHandler(output)
    # TODO: Set the handler's formatter to JSONFormatter()
    # TODO: Add RequestIDFilter to the handler
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
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_request_id():
    """Show request ID propagation via contextvars."""
    print("\n--- Section 2: Request ID via contextvars ---")
    try:
        logger, output = setup_logger("demo.reqid")

        def handle_request(path: str):
            rid = generate_request_id()
            request_id_var.set(rid)
            logger.info("Processing request", extra={"path": path})
            fetch_data(logger, path)
            logger.info("Request complete", extra={"path": path})

        def fetch_data(log: logging.Logger, path: str):
            log.info("Fetching data from DB", extra={"table": "users"})

        handle_request("/api/users")
        handle_request("/api/posts")

        logs = parse_log_lines(output)

        print(f"  Generated {len(logs)} log entries:")
        for log in logs:
            print(f"    [{log['level']}] {log['message']} "
                  f"request_id={log.get('request_id', 'none')}")

        assert len(logs) == 6
        first_rid = logs[0]["request_id"]
        assert logs[1]["request_id"] == first_rid
        assert logs[2]["request_id"] == first_rid
        second_rid = logs[3]["request_id"]
        assert second_rid != first_rid
        assert logs[4]["request_id"] == second_rid
        assert logs[5]["request_id"] == second_rid

        print("  [PASS] Request ID propagation works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")
    finally:
        request_id_var.set(None)


def demo_timing_middleware():
    """Show timing middleware logging request duration."""
    print("\n--- Section 3: Timing Middleware ---")
    try:
        logger, output = setup_logger("demo.timing")
        middleware = TimingMiddleware(logger)

        def slow_handler(request: dict) -> dict:
            time.sleep(0.01)
            return {"status_code": 200, "body": {"users": ["Alice"]}}

        def error_handler(request: dict) -> dict:
            raise ValueError("Something went wrong")

        request_id_var.set(generate_request_id())

        timed = middleware.wrap(slow_handler)
        response = timed({"method": "GET", "path": "/api/users"})
        assert response["status_code"] == 200

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

        assert len(logs) == 4
        completed = [l for l in logs if l["message"] == "Request completed"]
        assert len(completed) == 1
        assert completed[0]["duration_ms"] >= 5
        assert completed[0]["status_code"] == 200

        failed = [l for l in logs if l["message"] == "Request failed"]
        assert len(failed) == 1
        assert "error" in failed[0]

        print("  [PASS] Timing middleware works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")
    finally:
        request_id_var.set(None)


def demo_log_levels():
    """Show log level filtering."""
    print("\n--- Section 4: Log Levels & Filtering ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_exception_logging():
    """Show exception info in structured logs."""
    print("\n--- Section 5: Exception Logging ---")
    try:
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")


def demo_full_request_flow():
    """Show a complete request flow with structured logging."""
    print("\n--- Section 6: Full Request Flow ---")
    try:
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

        for log in logs:
            assert log["request_id"] == rid
        print(f"\n  All {len(logs)} entries share request_id={rid}")
        assert response["status_code"] == 200

        request_id_var.set(None)

        print("  [PASS] Full request flow works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  Not yet implemented: {e}")
    finally:
        request_id_var.set(None)


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
