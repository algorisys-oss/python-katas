"""
Kata 29 -- Subinterpreters
Run: python playground/29_subinterpreters.py

True parallelism within a single process using subinterpreters (PEP 734).
Each subinterpreter has its own GIL, enabling CPU-bound parallelism without
the overhead of multiprocessing.

NOTE: Subinterpreters ship as the `concurrent.interpreters` module in Python 3.14+.
On 3.12/3.13 the API was experimental (private `_interpreters` module) and some
builds omit it, so all demos gracefully handle the case where it's unavailable.

IMPORTANT: Must complete within 5 seconds.
"""

import sys
import threading
import time

# Try to import a subinterpreters module. Preference order:
#   1. concurrent.interpreters -- public stdlib API (Python 3.14+)
#   2. interpreters            -- experimental standalone backport
#   3. _interpreters           -- private low-level module (3.12/3.13 builds)
_interpreters_available = False
_interpreters_module = None
_API = None  # one of: "public", "private"

try:
    from concurrent import interpreters as _interpreters_module
    _interpreters_available = True
    _API = "public"
except ImportError:
    try:
        import interpreters as _interpreters_module  # type: ignore[import-not-found]
        _interpreters_available = True
        _API = "public"
    except ImportError:
        try:
            import _interpreters as _interpreters_module
            _interpreters_available = True
            _API = "private"
        except ImportError:
            pass


# ===========================================================================
# Helper functions to abstract over the public/private API
# ===========================================================================

def _create_interpreter():
    """Create a new subinterpreter, returning its ID or object."""
    return _interpreters_module.create()


def _run_in_interpreter(interp, code: str):
    """Run code string in the given subinterpreter."""
    if _API == "private":
        _interpreters_module.run_string(interp, code)
    else:
        # Public API: prefer exec() (3.14+), fall back to run() (older backport)
        runner = getattr(interp, "exec", None) or getattr(interp, "run")
        runner(code)


def _close_interpreter(interp):
    """Close/destroy a subinterpreter."""
    if _API == "private":
        _interpreters_module.destroy(interp)
    else:
        interp.close()


def _list_all_interpreters():
    """List all active interpreters."""
    return _interpreters_module.list_all()


def _get_interp_id(interp):
    """Get a printable ID for an interpreter."""
    if _API == "private":
        return interp  # _interpreters returns raw int IDs
    else:
        return interp.id if hasattr(interp, 'id') else interp


# ===========================================================================
# SECTION 1: Creating Subinterpreters
# ===========================================================================

def demo_create_subinterpreters():
    """Create, inspect, and close subinterpreters."""
    if not _interpreters_available:
        print("  NOTE: interpreters module not available in this Python build.")
        print(f"  Python version: {sys.version}")
        print("  This is expected -- the API is experimental in Python 3.12/3.13.")
        print("  Skipping subinterpreter demos. See tutorial for concepts.")
        return False

    # List interpreters before creating any
    initial_interps = _list_all_interpreters()
    initial_count = len(initial_interps)
    main_id = _get_interp_id(initial_interps[0])

    # Create a subinterpreter
    interp = _create_interpreter()
    interp_id = _get_interp_id(interp)
    print(f"  Created subinterpreter with id: {interp_id}")

    # List all interpreters
    all_interps = _list_all_interpreters()
    active_count = len(all_interps)
    print(f"  Active interpreters: {active_count} (main + {active_count - 1} sub)")
    assert active_count == initial_count + 1, (
        f"Expected {initial_count + 1} interpreters, got {active_count}"
    )

    # Run code in the subinterpreter
    _run_in_interpreter(interp, "x = 42")
    print("  Subinterpreter executed code successfully")

    # Close and verify
    _close_interpreter(interp)
    after_close = _list_all_interpreters()
    print(f"  Closed subinterpreter. Active: {len(after_close)}")
    assert len(after_close) == initial_count

    print("  Subinterpreters provide isolated Python execution environments.")
    return True


# ===========================================================================
# SECTION 2: Running Code in Subinterpreters
# ===========================================================================

def demo_run_code():
    """Run computations in subinterpreters demonstrating isolation."""
    if not _interpreters_available:
        print("  SKIPPED: interpreters module not available.")
        return

    interp = _create_interpreter()

    # Run a computation
    _run_in_interpreter(interp, """
total = 0
for i in range(1000):
    total += i
# total = 499500 (only visible inside this interpreter)
""")
    print("  Ran computation in subinterpreter: completed")

    # Demonstrate isolation: define something in one, it's invisible in another
    interp2 = _create_interpreter()
    _run_in_interpreter(interp, "secret = 'hello from interp1'")

    try:
        _run_in_interpreter(interp2, "print(secret)")  # Should fail
        print("  ERROR: should not have seen 'secret' from interp1")
    except Exception:
        pass  # Expected -- secret is isolated to interp1

    _close_interpreter(interp)
    _close_interpreter(interp2)

    print("  Each subinterpreter has its own namespace -- full isolation.")


# ===========================================================================
# SECTION 3: Parallel Execution with Subinterpreters
# ===========================================================================

def demo_parallel_execution():
    """Demonstrate true parallelism using subinterpreters + threads."""
    if not _interpreters_available:
        print("  SKIPPED: interpreters module not available.")
        return

    cpu_code = """
total = 0
for i in range(200_000):
    total += i * i
"""

    # Sequential: run two tasks one after another
    start = time.perf_counter()
    interp_seq1 = _create_interpreter()
    _run_in_interpreter(interp_seq1, cpu_code)
    _close_interpreter(interp_seq1)
    interp_seq2 = _create_interpreter()
    _run_in_interpreter(interp_seq2, cpu_code)
    _close_interpreter(interp_seq2)
    sequential_time = time.perf_counter() - start

    print(f"  Sequential time: {sequential_time:.3f}s")

    # Parallel: run two tasks in parallel using threads + subinterpreters
    def run_in_sub(code: str):
        interp = _create_interpreter()
        _run_in_interpreter(interp, code)
        _close_interpreter(interp)

    start = time.perf_counter()
    t1 = threading.Thread(target=run_in_sub, args=(cpu_code,))
    t2 = threading.Thread(target=run_in_sub, args=(cpu_code,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    parallel_time = time.perf_counter() - start

    print(f"  Parallel time (subinterpreters + threads): {parallel_time:.3f}s")
    print("  Subinterpreters enable true parallelism (separate GILs).")


# ===========================================================================
# SECTION 4: Comparison with Threading
# ===========================================================================

def demo_comparison_with_threading():
    """Compare regular threading vs subinterpreters for CPU-bound work."""
    if not _interpreters_available:
        print("  SKIPPED: interpreters module not available.")
        print()
        print("  Conceptual comparison:")
        print("  Threading:        1 GIL shared → no CPU parallelism")
        print("  Subinterpreters:  separate GILs → true CPU parallelism")
        print("  Multiprocessing:  separate processes → true parallelism but heavy")
        return

    iterations = 200_000

    # Regular threading (shared GIL -- no true parallelism for CPU work)
    def cpu_work_python():
        total = 0
        for i in range(iterations):
            total += i * i
        return total

    start = time.perf_counter()
    t1 = threading.Thread(target=cpu_work_python)
    t2 = threading.Thread(target=cpu_work_python)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    threading_time = time.perf_counter() - start

    print(f"  Threading (2 CPU-bound tasks, shared GIL): {threading_time:.3f}s")

    # Subinterpreters (separate GILs -- true parallelism)
    cpu_code = f"""
total = 0
for i in range({iterations}):
    total += i * i
"""

    def run_in_sub(code: str):
        interp = _create_interpreter()
        _run_in_interpreter(interp, code)
        _close_interpreter(interp)

    start = time.perf_counter()
    t1 = threading.Thread(target=run_in_sub, args=(cpu_code,))
    t2 = threading.Thread(target=run_in_sub, args=(cpu_code,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    subinterp_time = time.perf_counter() - start

    print(f"  Subinterpreters (2 CPU-bound tasks, separate GILs): {subinterp_time:.3f}s")
    print("  Subinterpreters can outperform threading for CPU-bound work.")


# ===========================================================================
# SECTION 5: Interpreter Lifecycle and Safety
# ===========================================================================

def demo_lifecycle():
    """Demonstrate proper lifecycle management of subinterpreters."""
    if not _interpreters_available:
        print("  SKIPPED: interpreters module not available.")
        return

    # Create multiple interpreters
    interpreters_list = []
    for i in range(3):
        interp = _create_interpreter()
        interpreters_list.append(interp)

    all_active = _list_all_interpreters()
    print(f"  Created 3 subinterpreters. Total active: {len(all_active)}")

    # Run different code in each
    for i, interp in enumerate(interpreters_list):
        _run_in_interpreter(interp, f"my_id = {i}; result = my_id ** 2")

    print("  Ran isolated code in each subinterpreter.")

    # Clean up all
    for interp in interpreters_list:
        _close_interpreter(interp)

    remaining = _list_all_interpreters()
    print(f"  Cleaned up. Remaining interpreters: {len(remaining)}")
    assert len(remaining) == len(all_active) - 3

    print("  Always close subinterpreters to free resources.")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Creating Subinterpreters ---
    print("--- Section 1: Creating Subinterpreters ---")
    available = demo_create_subinterpreters()
    print()

    if not _interpreters_available:
        # Print conceptual summary even if module isn't available
        print("--- Conceptual Summary (module not available) ---")
        print("Subinterpreters provide true parallelism within a single process:")
        print("  - Each interpreter has its own GIL (no contention)")
        print("  - Lower overhead than multiprocessing (no process spawn)")
        print("  - Full isolation (no shared Python objects)")
        print("  - Channel-based communication for data exchange")
        print("  - Stdlib API since Python 3.14 (PEP 734)")
        print("  - Best for: CPU-bound tasks needing lightweight parallelism")
        print()
        print("To try subinterpreters, use Python 3.14+ ('from concurrent import interpreters').")
        print("On 3.12/3.13 the experimental private '_interpreters' module may be available.")
        print()
        print("All sections completed (with graceful skips). Subinterpreters explored!")
    else:
        # --- Section 2: Running Code ---
        print("--- Section 2: Running Code in Subinterpreters ---")
        demo_run_code()
        print()

        # --- Section 3: Parallel Execution ---
        print("--- Section 3: Parallel Execution with Subinterpreters ---")
        demo_parallel_execution()
        print()

        # --- Section 4: Comparison with Threading ---
        print("--- Section 4: Comparison with Threading ---")
        demo_comparison_with_threading()
        print()

        # --- Section 5: Lifecycle Management ---
        print("--- Section 5: Interpreter Lifecycle and Safety ---")
        demo_lifecycle()
        print()

        # --- Summary ---
        print("--- Summary ---")
        print("Subinterpreters provide true parallelism within a single process:")
        print("  - Each interpreter has its own GIL (no contention)")
        print("  - Lower overhead than multiprocessing (no process spawn)")
        print("  - Full isolation (no shared Python objects)")
        print("  - Channel-based communication for data exchange")
        print("  - Stdlib API since Python 3.14 (PEP 734)")
        print("  - Best for: CPU-bound tasks needing lightweight parallelism")
        print()
        print("All sections completed. Subinterpreters explored!")
