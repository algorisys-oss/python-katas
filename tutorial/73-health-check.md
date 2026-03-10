# Kata 73 -- Health Check Endpoints

[prev: 72-template-rendering](./72-template-rendering.md) | [next: 74-rate-limiting](./74-rate-limiting.md)

---

## What We're Building

A **health check system** for our Ignite framework. Production services need endpoints that report whether the application is healthy, so orchestrators like Kubernetes can restart unhealthy pods and remove unready ones from load balancers. We build:

1. **Health status model** -- an enum (healthy, degraded, unhealthy) plus structured check results
2. **Health check registry** -- register checks for each dependency (database, cache, external APIs)
3. **Liveness vs readiness probes** -- two different questions: "is the process alive?" vs "can it serve traffic?"
4. **HTTP endpoints** -- `/health`, `/health/live`, `/health/ready` with proper status codes (200 or 503)

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Health status enum | Three states: healthy, degraded, unhealthy | Categorizing service health |
| Check result | Name, status, details, response time | Reporting individual checks |
| Health registry | Register and run checks by name | Managing multiple dependencies |
| Liveness probe | Is the process alive and running? | Kubernetes restart decisions |
| Readiness probe | Are all dependencies available? | Load balancer routing |
| Aggregate status | Worst-of-all check results | Overall service health |
| HTTP status codes | 200 (up) vs 503 (down) | Standard health check protocol |

## The Code

### 1. Health Status Model

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    def is_up(self) -> bool:
        return self in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

@dataclass
class CheckResult:
    name: str
    status: HealthStatus
    details: dict[str, Any]
    response_time_ms: float
```

### 2. Health Check Registry

The registry stores callable health checks, runs them with timing, and catches any exceptions:

```python
class HealthCheckRegistry:
    def register(self, name, check, *, liveness=False, readiness=True):
        self._checks[name] = check
        if liveness:
            self._liveness_checks[name] = check
        if readiness:
            self._readiness_checks[name] = check

    def run_check(self, name):
        start = time.monotonic()
        try:
            result = check()
            result.response_time_ms = (time.monotonic() - start) * 1000
            return result
        except Exception as exc:
            return CheckResult(name=name, status=UNHEALTHY, ...)
```

### 3. Aggregate Status

The aggregate is the worst status across all checks:

```python
aggregate = HealthStatus.HEALTHY
for r in results:
    if r.status == UNHEALTHY:
        aggregate = UNHEALTHY
        break
    if r.status == DEGRADED:
        aggregate = DEGRADED
```

### 4. Liveness vs Readiness

```python
# Liveness: is the process running?
# Register: disk space, memory, deadlock detection
registry.register("disk", disk_check, liveness=True, readiness=False)

# Readiness: can it serve traffic?
# Register: database, cache, external APIs
registry.register("database", db_check, liveness=False, readiness=True)
```

### 5. HTTP Endpoints

```python
class HealthEndpoints:
    def handle_health(self) -> Response:
        report = self.registry.run_all()
        return Response(body=report.to_dict(),
                       status_code=report.http_status_code)

    def handle_liveness(self) -> Response:
        report = self.registry.run_liveness()
        return Response(body=report.to_dict(),
                       status_code=report.http_status_code)
```

## Playground

```python
python playground/73_health_check.py
```

Expected output:

```
--- Section 1: Health Status Model ---
  HEALTHY.is_up() = True
  DEGRADED.is_up() = True
  UNHEALTHY.is_up() = False
  CheckResult: {'name': 'database', 'status': 'healthy', ...}
  [PASS] Health status model works

--- Section 2: Health Check Registry ---
  All checks: status=healthy
    database: healthy (0.01ms)
    cache: healthy (0.00ms)
    disk: healthy (0.00ms)
  Single check: database=healthy
  [PASS] Health check registry works

--- Section 3: Unhealthy Scenario ---
  Status: unhealthy
    database: unhealthy
    cache: healthy
  [PASS] Unhealthy scenario detected

--- Section 4: Degraded Scenario ---
  Status: degraded
    database: healthy
    cache: degraded
  [PASS] Degraded scenario detected

--- Section 5: Liveness vs Readiness ---
  Liveness: healthy (HTTP 200)
  Readiness: unhealthy (HTTP 503)
  [PASS] Liveness vs readiness works

--- Section 6: Health Endpoints ---
  GET /health -> 200
  GET /health/live -> 200
  GET /health/ready -> 200
  [PASS] Health endpoints work

--- Section 7: Check Exception Handling ---
  Status: unhealthy
    broken_service: unhealthy -- {'error': 'Cannot reach service'}
    database: healthy -- ...
  [PASS] Check exceptions handled gracefully

All 7 sections passed. Health check endpoints mastered!
```

## How It Works

### Health Check Architecture

```
                    HealthCheckRegistry
                    +------------------+
                    |  _checks:        |
    register() --> |    database -----> check_fn() -> CheckResult
                    |    cache -------> check_fn() -> CheckResult
                    |    disk --------> check_fn() -> CheckResult
                    |                  |
                    |  _liveness:      |
    /health/live -> |    disk -------> check_fn()
                    |                  |
                    |  _readiness:     |
    /health/ready ->|    database ---> check_fn()
                    |    cache ------> check_fn()
                    +------------------+
                           |
                           v
                    Aggregate Status
                    (worst of all checks)
                           |
                           v
                    HealthReport
                    {status, checks[], timestamp}
                           |
                           v
                    HTTP Response
                    200 (up) or 503 (down)
```

### Liveness vs Readiness in Kubernetes

```
Pod starts
    |
    v
Liveness probe: /health/live
    |                    |
    OK (200)          FAIL (503)
    |                    |
    v                    v
Keep running        Restart pod
    |
    v
Readiness probe: /health/ready
    |                    |
    OK (200)          FAIL (503)
    |                    |
    v                    v
Add to LB          Remove from LB
(serve traffic)     (stop routing)
```

## Exercises

1. **Add caching** -- cache health check results for a configurable TTL (e.g. 5 seconds) so rapid polling doesn't hammer dependencies.

2. **Add check timeouts** -- if a health check takes longer than N seconds, mark it as unhealthy rather than blocking the probe response.

3. **Add startup probes** -- a third probe type that checks if the application has finished initializing (e.g. migrations complete, caches warmed).

4. **Add dependency ordering** -- some checks depend on others (cache depends on database). Run them in dependency order and skip downstream checks if upstream fails.

5. **Add health history** -- store the last N check results and expose a `/health/history` endpoint showing health over time.

## What's Next

With health checks in place, our Ignite framework can report its status to orchestrators. In [Kata 74: Rate Limiting](./74-rate-limiting.md), we'll build rate limiting middleware to protect our service from being overwhelmed by too many requests.

---

[prev: 72-template-rendering](./72-template-rendering.md) | [next: 74-rate-limiting](./74-rate-limiting.md)
