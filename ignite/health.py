"""
Ignite Health Check Module

Health-check registry with liveness and readiness probes, aggregate
status computation, and route registration helpers.

Imports from sibling ignite modules: response, routing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from ignite.response import JSONResponse
from ignite.routing import Router


# ---------------------------------------------------------------------------
# Health status model
# ---------------------------------------------------------------------------

class HealthStatus(Enum):
    """Possible outcomes of a health check."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    def is_up(self) -> bool:
        """``True`` for healthy or degraded (process is alive)."""
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


# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

HealthCheck = Callable[[], CheckResult]


# ---------------------------------------------------------------------------
# HealthCheckRegistry
# ---------------------------------------------------------------------------

class HealthCheckRegistry:
    """Registry where components register their health checks.

    Supports separate liveness and readiness probes, individual or
    aggregate check execution, and graceful exception handling.
    """

    def __init__(self) -> None:
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
            name:      Unique name (e.g. ``"database"``).
            check:     Callable returning a :class:`CheckResult`.
            liveness:  Include in liveness probes.
            readiness: Include in readiness probes.
        """
        self._checks[name] = check
        if liveness:
            self._liveness_checks[name] = check
        if readiness:
            self._readiness_checks[name] = check

    def run_check(self, name: str) -> CheckResult:
        """Run a single named check (with timing)."""
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

    def _run_checks(
        self, checks: dict[str, HealthCheck]
    ) -> HealthReport:
        results: list[CheckResult] = []
        for name in checks:
            results.append(self.run_check(name))

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
        """Run every registered check."""
        return self._run_checks(self._checks)

    def run_liveness(self) -> HealthReport:
        """Run liveness checks only (is the process alive?)."""
        if not self._liveness_checks:
            return HealthReport(status=HealthStatus.HEALTHY, timestamp=time.time())
        return self._run_checks(self._liveness_checks)

    def run_readiness(self) -> HealthReport:
        """Run readiness checks only (can we serve traffic?)."""
        return self._run_checks(self._readiness_checks)

    # -- Route registration helper ------------------------------------------

    def register_routes(self, router: Router, prefix: str = "/health") -> None:
        """Add ``/health``, ``/health/live``, and ``/health/ready`` routes
        to *router*.
        """
        registry = self  # capture for closures

        async def health_handler(request: Any) -> JSONResponse:
            report = registry.run_all()
            return JSONResponse(report.to_dict(), status_code=report.http_status_code)

        async def liveness_handler(request: Any) -> JSONResponse:
            report = registry.run_liveness()
            return JSONResponse(report.to_dict(), status_code=report.http_status_code)

        async def readiness_handler(request: Any) -> JSONResponse:
            report = registry.run_readiness()
            return JSONResponse(report.to_dict(), status_code=report.http_status_code)

        router.add_route("GET", prefix, health_handler)
        router.add_route("GET", f"{prefix}/live", liveness_handler)
        router.add_route("GET", f"{prefix}/ready", readiness_handler)
