# Kata 69 -- Structured Logging

[prev: 68-debug-error-page](./68-debug-error-page.md) | [next: 70-cli-tool](./70-cli-tool.md)

---

## What We're Building

A **structured logging system** for our Ignite framework. Instead of plain text logs, we output JSON -- making logs machine-parseable for tools like ELK, Datadog, and CloudWatch. We build three layers:

1. **JSONFormatter** -- custom `logging.Formatter` that outputs JSON
2. **Request ID propagation** -- use `contextvars` to attach a unique ID to all logs within a request
3. **Timing middleware** -- log request duration automatically

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `logging.Formatter` | Controls log output format | Custom log formats |
| `logging.Filter` | Injects extra fields into records | Adding context to all logs |
| `contextvars.ContextVar` | Per-task/per-request state | Request ID, user context |
| `time.monotonic()` | High-resolution timer | Measuring durations |
| `json.dumps(default=str)` | JSON serialization with fallback | Logging non-serializable objects |
| `io.StringIO` | In-memory text stream | Capturing log output for testing |

## The Code

### 1. JSON Formatter

```python
class JSONFormatter(logging.Formatter):
    RESERVED_ATTRS = {"args", "asctime", "created", "exc_info", ...}

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add extra fields (from extra={} parameter)
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, default=str)
```

### 2. Request ID via contextvars

```python
request_id_var = contextvars.ContextVar("request_id", default=None)

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True  # Never filter out -- just add the field

# Usage:
request_id_var.set("abc-123-def")
logger.info("Processing")  # -> {"request_id": "abc-123-def", ...}
```

### 3. Timing Middleware

```python
class TimingMiddleware:
    def wrap(self, handler):
        def timed_handler(request):
            self.logger.info("Request started", extra={"path": path})
            start = time.monotonic()

            try:
                response = handler(request)
                duration_ms = (time.monotonic() - start) * 1000
                self.logger.info("Request completed",
                    extra={"duration_ms": round(duration_ms, 2)})
                return response
            except Exception as exc:
                self.logger.error("Request failed", exc_info=True)
                raise

        return timed_handler
```

## Playground

```bash
python playground/69_structured_logging.py
```

Expected output:

```
--- Section 1: JSON Log Formatter ---
  {"timestamp": "...", "level": "INFO", "message": "Server starting", "host": "0.0.0.0", "port": 8000}
  {"timestamp": "...", "level": "WARNING", "message": "Deprecated endpoint called", "path": "/v1/users"}
  ...
  [PASS] JSON formatter works

--- Section 2: Request ID via contextvars ---
  Generated 6 log entries:
    [INFO] Processing request request_id=abc123
    [INFO] Fetching data from DB request_id=abc123
    [INFO] Request complete request_id=abc123
    [INFO] Processing request request_id=def456
    ...
  [PASS] Request ID propagation works

--- Section 3: Timing Middleware ---
  Timing log entries:
    [INFO] Request started path=/api/users duration=N/Ams
    [INFO] Request completed path=/api/users duration=10.5ms
    ...
  [PASS] Timing middleware works
```

## How It Works

### Log Record Flow

```
logger.info("msg", extra={"key": "val"})
    |
    v
LogRecord created (with msg, level, extras)
    |
    v
RequestIDFilter.filter(record)
    |  Adds record.request_id from contextvars
    v
JSONFormatter.format(record)
    |  Builds JSON: {timestamp, level, message, request_id, key, ...}
    v
StreamHandler.emit(record)
    |  Writes JSON line to output stream
    v
stdout / file / log aggregator
```

### contextvars: Why Not Threading.local?

```
Threading.local:
  Thread 1: request_id = "aaa"
  Thread 2: request_id = "bbb"
  Problem: asyncio runs many tasks on ONE thread

contextvars:
  Task A (Thread 1): request_id = "aaa"
  Task B (Thread 1): request_id = "bbb"  <- separate context!
  Works with both threads AND async tasks
```

### Log Level Hierarchy

```
CRITICAL (50)  -- System is unusable
ERROR    (40)  -- Operation failed
WARNING  (30)  -- Something unexpected
INFO     (20)  -- Normal operation
DEBUG    (10)  -- Detailed diagnostics

Setting level=WARNING filters out INFO and DEBUG
```

## Exercises

1. **Add log correlation** -- extend the system to support a `correlation_id` that spans multiple services. Parent request IDs propagate to child service calls.

2. **Add sensitive data redaction** -- automatically redact fields like `password`, `token`, `secret` in log output. Use a configurable list of field patterns.

3. **Add log sampling** -- for high-traffic endpoints, only log a percentage of requests (e.g., 10%). Use a `SamplingFilter` that decides based on a configured rate.

4. **Add structured error context** -- build a context manager `with log_context(user_id=42, action="purchase"):` that adds fields to all logs within the block.

5. **Add log rotation** -- implement a handler that rotates log files by size (max 10MB) or time (daily), keeping a configurable number of backups.

## What's Next

With structured logging, our Ignite framework produces machine-parseable logs with request correlation. In [Kata 70: CLI Tool](./70-cli-tool.md), we'll build the `ignite` CLI using argparse -- `ignite run`, `ignite routes`, `ignite migrate` -- giving developers a clean command-line interface.

---

[prev: 68-debug-error-page](./68-debug-error-page.md) | [next: 70-cli-tool](./70-cli-tool.md)
