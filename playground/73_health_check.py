"""
Kata 73 -- Health Check Endpoints
Run: python playground/73_health_check.py

Build health check endpoints for Ignite: liveness probes (/health/live),
readiness probes (/health/ready), health check registry, aggregate status,
and proper HTTP status codes (200 healthy, 503 unhealthy).

Completes within 5 seconds.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Health Status Model
# ===========================================================================
# Health checks report one of three statuses. We use an enum so that
# comparisons are explicit and typo-proof.

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    def is_up(self) -> bool:
        """Healthy or degraded counts as 'up' for liveness."""
        return self in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@dataclass
class CheckResult:
    """Result from a single health check."""
    name: str
    status: HealthStatus
    details: dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "details": self.details,
            "response_time_ms": round(self.response_time_ms, 2),
        }


@dataclass
class HealthReport:
    """Aggregate health report across all checks."""
    status: HealthStatus
    checks: list[CheckResult] = field(default_factory=list)
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "checks": [c.to_dict() for c in self.checks],
        }

    @property
    def http_status_code(self) -> int:
        """200 for healthy/degraded, 503 for unhealthy."""
        return 200 if self.status.is_up() else 503


# ===========================================================================
# SECTION 2: Health Check Registry
# ===========================================================================
# Components register health checks. Each check is a callable that returns
# a CheckResult. The registry runs all checks and computes the aggregate.

# Type alias: a health check function takes no args and returns CheckResult
HealthCheck = Callable[[], CheckResult]


class HealthCheckRegistry:
    """Registry where components register their health checks.

    Supports:
    - Registering checks by name
    - Running individual checks
    - Running all checks and computing aggregate status
    - Separate liveness and readiness probes
    """

    def __init__(self):
        self._checks: dict[str, HealthCheck] = {}
        self._liveness_checks: dict[str, HealthCheck] = {}
        self._readiness_checks: dict[str, HealthCheck] = {}

    def register(
        self,
        name: str,
        check: HealthCheck,
        *,
        liveness: bool = False,
        readiness: bool = True,
    ) -> None:
        """Register a health check.

        Args:
            name: Unique name for the check (e.g. "database", "cache").
            check: Callable that returns a CheckResult.
            liveness: Include in liveness probes (is process alive?).
            readiness: Include in readiness probes (can serve traffic?).
        """
        self._checks[name] = check
        if liveness:
            self._liveness_checks[name] = check
        if readiness:
            self._readiness_checks[name] = check

    def run_check(self, name: str) -> CheckResult:
        """Run a single named check with timing."""
        check = self._checks.get(name)
        if check is None:
            return CheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                details={"error": f"Unknown check: {name}"},
            )
        start = time.monotonic()
        try:
            result = check()
            result.response_time_ms = (time.monotonic() - start) * 1000
            return result
        except Exception as exc:
            return CheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                details={"error": str(exc)},
                response_time_ms=(time.monotonic() - start) * 1000,
            )

    def _run_checks(self, checks: dict[str, HealthCheck]) -> HealthReport:
        """Run a set of checks and compute aggregate status."""
        results: list[CheckResult] = []
        for name, check in checks.items():
            result = self.run_check(name)
            results.append(result)

        # Aggregate: unhealthy if any check is unhealthy,
        # degraded if any is degraded, else healthy
        aggregate = HealthStatus.HEALTHY
        for r in results:
            if r.status == HealthStatus.UNHEALTHY:
                aggregate = HealthStatus.UNHEALTHY
                break
            if r.status == HealthStatus.DEGRADED:
                aggregate = HealthStatus.DEGRADED

        return HealthReport(
            status=aggregate,
            checks=results,
            timestamp=time.time(),
        )

    def run_all(self) -> HealthReport:
        """Run all registered checks."""
        return self._run_checks(self._checks)

    def run_liveness(self) -> HealthReport:
        """Run liveness checks only.

        Liveness = is the process running and not deadlocked?
        Kubernetes restarts the pod if liveness fails.
        """
        if not self._liveness_checks:
            # No liveness checks registered = process is alive
            return HealthReport(
                status=HealthStatus.HEALTHY,
                timestamp=time.time(),
            )
        return self._run_checks(self._liveness_checks)

    def run_readiness(self) -> HealthReport:
        """Run readiness checks only.

        Readiness = can the service handle requests?
        Kubernetes removes the pod from load balancer if readiness fails.
        """
        return self._run_checks(self._readiness_checks)


# ===========================================================================
# SECTION 3: Health Check Endpoint Handler
# ===========================================================================
# Simulates HTTP endpoint handling for health checks. In a real framework
# these would be actual route handlers.

class Response:
    """Simplified HTTP response."""
    def __init__(self, body: dict, status_code: int = 200):
        self.body = body
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}

    def __repr__(self) -> str:
        return f"Response(status={self.status_code})"


class HealthEndpoints:
    """Health check HTTP endpoint handlers.

    Provides three endpoints:
    - /health       -> full health report
    - /health/live  -> liveness probe
    - /health/ready -> readiness probe
    """

    def __init__(self, registry: HealthCheckRegistry):
        self.registry = registry

    def handle_health(self) -> Response:
        """GET /health -- full health report."""
        report = self.registry.run_all()
        return Response(
            body=report.to_dict(),
            status_code=report.http_status_code,
        )

    def handle_liveness(self) -> Response:
        """GET /health/live -- liveness probe."""
        report = self.registry.run_liveness()
        return Response(
            body=report.to_dict(),
            status_code=report.http_status_code,
        )

    def handle_readiness(self) -> Response:
        """GET /health/ready -- readiness probe."""
        report = self.registry.run_readiness()
        return Response(
            body=report.to_dict(),
            status_code=report.http_status_code,
        )


# ===========================================================================
# SECTION 4: Example Health Checks
# ===========================================================================
# Factory functions that create health checks for common dependencies.
# Each returns a callable that can be registered with the registry.

def create_db_check(*, connected: bool = True) -> HealthCheck:
    """Create a database health check."""
    def check() -> CheckResult:
        if connected:
            return CheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                details={"engine": "sqlite", "pool_size": 5, "active": 2},
            )
        return CheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            details={"error": "Connection refused"},
        )
    return check


def create_cache_check(*, hit_rate: float = 0.95) -> HealthCheck:
    """Create a cache health check."""
    def check() -> CheckResult:
        if hit_rate > 0.8:
            status = HealthStatus.HEALTHY
        elif hit_rate > 0.5:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY
        return CheckResult(
            name="cache",
            status=status,
            details={"hit_rate": hit_rate, "type": "in-memory"},
        )
    return check


def create_external_api_check(*, reachable: bool = True) -> HealthCheck:
    """Create an external API health check."""
    def check() -> CheckResult:
        if reachable:
            return CheckResult(
                name="external_api",
                status=HealthStatus.HEALTHY,
                details={"endpoint": "https://api.example.com", "latency_ms": 45},
            )
        return CheckResult(
            name="external_api",
            status=HealthStatus.UNHEALTHY,
            details={"endpoint": "https://api.example.com", "error": "Timeout"},
        )
    return check


def create_disk_check(*, usage_pct: float = 60.0) -> HealthCheck:
    """Create a disk space health check."""
    def check() -> CheckResult:
        if usage_pct < 80:
            status = HealthStatus.HEALTHY
        elif usage_pct < 95:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY
        return CheckResult(
            name="disk",
            status=status,
            details={"usage_percent": usage_pct, "path": "/data"},
        )
    return check


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_health_status():
    """Show health status model."""
    print("--- Section 1: Health Status Model ---")

    assert HealthStatus.HEALTHY.is_up() is True
    assert HealthStatus.DEGRADED.is_up() is True
    assert HealthStatus.UNHEALTHY.is_up() is False
    print("  HEALTHY.is_up() = True")
    print("  DEGRADED.is_up() = True")
    print("  UNHEALTHY.is_up() = False")

    result = CheckResult(
        name="database",
        status=HealthStatus.HEALTHY,
        details={"engine": "sqlite"},
        response_time_ms=1.23,
    )
    d = result.to_dict()
    print(f"  CheckResult: {d}")
    assert d["status"] == "healthy"
    assert d["name"] == "database"

    print("  [PASS] Health status model works")


def demo_health_registry():
    """Show health check registry and aggregation."""
    print("\n--- Section 2: Health Check Registry ---")

    registry = HealthCheckRegistry()

    # Register checks
    registry.register("database", create_db_check(connected=True), readiness=True)
    registry.register("cache", create_cache_check(hit_rate=0.95), readiness=True)
    registry.register("disk", create_disk_check(usage_pct=60), liveness=True)

    # Run all
    report = registry.run_all()
    print(f"  All checks: status={report.status.value}")
    for c in report.checks:
        print(f"    {c.name}: {c.status.value} ({c.response_time_ms:.2f}ms)")
    assert report.status == HealthStatus.HEALTHY
    assert report.http_status_code == 200

    # Run single
    result = registry.run_check("database")
    print(f"  Single check: {result.name}={result.status.value}")
    assert result.status == HealthStatus.HEALTHY

    print("  [PASS] Health check registry works")


def demo_unhealthy_scenario():
    """Show what happens when a dependency is unhealthy."""
    print("\n--- Section 3: Unhealthy Scenario ---")

    registry = HealthCheckRegistry()
    registry.register("database", create_db_check(connected=False), readiness=True)
    registry.register("cache", create_cache_check(hit_rate=0.95), readiness=True)

    report = registry.run_all()
    print(f"  Status: {report.status.value}")
    for c in report.checks:
        print(f"    {c.name}: {c.status.value}")
    assert report.status == HealthStatus.UNHEALTHY
    assert report.http_status_code == 503

    print("  [PASS] Unhealthy scenario detected")


def demo_degraded_scenario():
    """Show degraded status (partially healthy)."""
    print("\n--- Section 4: Degraded Scenario ---")

    registry = HealthCheckRegistry()
    registry.register("database", create_db_check(connected=True), readiness=True)
    registry.register("cache", create_cache_check(hit_rate=0.65), readiness=True)

    report = registry.run_all()
    print(f"  Status: {report.status.value}")
    for c in report.checks:
        print(f"    {c.name}: {c.status.value}")
    assert report.status == HealthStatus.DEGRADED
    assert report.http_status_code == 200  # degraded is still "up"

    print("  [PASS] Degraded scenario detected")


def demo_liveness_vs_readiness():
    """Show difference between liveness and readiness probes."""
    print("\n--- Section 5: Liveness vs Readiness ---")

    registry = HealthCheckRegistry()

    # Disk check is liveness only (process alive + disk OK)
    registry.register(
        "disk", create_disk_check(usage_pct=50),
        liveness=True, readiness=False,
    )
    # DB is readiness only (can we serve requests?)
    registry.register(
        "database", create_db_check(connected=False),
        liveness=False, readiness=True,
    )
    # External API is readiness only
    registry.register(
        "external_api", create_external_api_check(reachable=True),
        liveness=False, readiness=True,
    )

    # Liveness should pass (disk is healthy)
    live_report = registry.run_liveness()
    print(f"  Liveness: {live_report.status.value} (HTTP {live_report.http_status_code})")
    assert live_report.status == HealthStatus.HEALTHY
    assert live_report.http_status_code == 200

    # Readiness should fail (database is down)
    ready_report = registry.run_readiness()
    print(f"  Readiness: {ready_report.status.value} (HTTP {ready_report.http_status_code})")
    for c in ready_report.checks:
        print(f"    {c.name}: {c.status.value}")
    assert ready_report.status == HealthStatus.UNHEALTHY
    assert ready_report.http_status_code == 503

    print("  Kubernetes: liveness OK -> don't restart pod")
    print("  Kubernetes: readiness FAIL -> remove from load balancer")
    print("  [PASS] Liveness vs readiness works")


def demo_health_endpoints():
    """Show HTTP endpoint integration."""
    print("\n--- Section 6: Health Endpoints ---")

    registry = HealthCheckRegistry()
    registry.register("database", create_db_check(connected=True), readiness=True)
    registry.register("cache", create_cache_check(hit_rate=0.95), readiness=True)
    registry.register("disk", create_disk_check(usage_pct=70), liveness=True)

    endpoints = HealthEndpoints(registry)

    # GET /health
    resp = endpoints.handle_health()
    print(f"  GET /health -> {resp.status_code}")
    print(f"    status: {resp.body['status']}")
    print(f"    checks: {len(resp.body['checks'])}")
    assert resp.status_code == 200
    assert resp.body["status"] == "healthy"

    # GET /health/live
    resp2 = endpoints.handle_liveness()
    print(f"  GET /health/live -> {resp2.status_code}")
    assert resp2.status_code == 200

    # GET /health/ready
    resp3 = endpoints.handle_readiness()
    print(f"  GET /health/ready -> {resp3.status_code}")
    assert resp3.status_code == 200

    print("  [PASS] Health endpoints work")


def demo_check_exception_handling():
    """Show that checks that raise exceptions are caught gracefully."""
    print("\n--- Section 7: Check Exception Handling ---")

    registry = HealthCheckRegistry()

    def broken_check() -> CheckResult:
        raise ConnectionError("Cannot reach service")

    registry.register("broken_service", broken_check, readiness=True)
    registry.register("database", create_db_check(connected=True), readiness=True)

    report = registry.run_all()
    print(f"  Status: {report.status.value}")
    for c in report.checks:
        print(f"    {c.name}: {c.status.value} -- {c.details}")
    assert report.status == HealthStatus.UNHEALTHY

    # The broken check is caught and reported as unhealthy
    broken = [c for c in report.checks if c.name == "broken_service"][0]
    assert broken.status == HealthStatus.UNHEALTHY
    assert "Cannot reach service" in broken.details["error"]

    print("  [PASS] Check exceptions handled gracefully")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_health_status()
    demo_health_registry()
    demo_unhealthy_scenario()
    demo_degraded_scenario()
    demo_liveness_vs_readiness()
    demo_health_endpoints()
    demo_check_exception_handling()

    print("\n--- Summary ---")
    print("Health checks give our Ignite framework:")
    print("  - HealthStatus enum: healthy, degraded, unhealthy")
    print("  - CheckResult with name, status, details, response time")
    print("  - HealthCheckRegistry for registering and running checks")
    print("  - Aggregate status computation (worst-of-all)")
    print("  - Separate liveness and readiness probes")
    print("  - HTTP endpoints with proper status codes (200/503)")
    print("  - Graceful handling of checks that throw exceptions")
    print("\nAll 7 sections passed. Health check endpoints mastered!")
    print("Next up: Kata 74 -- rate limiting!")


if __name__ == "__main__":
    main()
