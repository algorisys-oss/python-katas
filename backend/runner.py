"""Safe code execution in a sandboxed subprocess."""

import os
import subprocess
import time
from dataclasses import dataclass


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    timed_out: bool = False


def run_code(code: str, timeout: float = 5.0) -> RunResult:
    """Execute Python code in a subprocess with timeout."""
    # Inherit a safe subset of the environment so python3 works properly
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/usr/local/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    start = time.monotonic()
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=safe_env,
            cwd="/tmp",
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return RunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        return RunResult(
            stdout="",
            stderr=f"Execution timed out after {timeout}s",
            exit_code=-1,
            duration_ms=duration_ms,
            timed_out=True,
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        return RunResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
            duration_ms=duration_ms,
        )
