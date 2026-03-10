"""
Kata 29 -- Subinterpreters
Run: python playground/skeletons/29_subinterpreters.py

True parallelism within a single process using subinterpreters (PEP 734).
Each subinterpreter has its own GIL, enabling CPU-bound parallelism without
the overhead of multiprocessing.

NOTE: The interpreters module is experimental in Python 3.12/3.13.
All demos gracefully handle the case where it's unavailable.

IMPORTANT: Must complete within 5 seconds.
"""

import sys
import threading
import time

# Try to import the interpreters module (experimental, may not be available)
_interpreters_available = False
_interpreters_module = None

try:
    import _interpreters
    _interpreters_module = _interpreters
    _interpreters_available = True
    _USE_PRIVATE_API = True
except ImportError:
    _USE_PRIVATE_API = False
    try:
        import interpreters  # type: ignore[import-not-found]
        _interpreters_module = interpreters
        _interpreters_available = True
    except ImportError:
        pass


# ===========================================================================
# Helper functions to abstract over the private/public API
# ===========================================================================

def _create_interpreter():
    """Create a new subinterpreter, returning its ID or object."""
    # TODO: use _interpreters.create() if _USE_PRIVATE_API, else _interpreters_module.create()
    # HINT: check the _USE_PRIVATE_API flag to decide which API to call
    pass


def _run_in_interpreter(interp, code: str):
    """Run code string in the given subinterpreter."""
    # TODO: use _interpreters.run_string(interp, code) if private API
    # TODO: use interp.run(code) if public API
    # HINT: check _USE_PRIVATE_API
    pass


def _close_interpreter(interp):
    """Close/destroy a subinterpreter."""
    # TODO: use _interpreters.destroy(interp) if private API
    # TODO: use interp.close() if public API
    # HINT: check _USE_PRIVATE_API
    pass


def _list_all_interpreters():
    """List all active interpreters."""
    # TODO: use _interpreters.list_all() if private API
    # TODO: use _interpreters_module.list_all() if public API
    # HINT: check _USE_PRIVATE_API
    pass


def _get_interp_id(interp):
    """Get a printable ID for an interpreter."""
    if _USE_PRIVATE_API:
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

    # TODO: list interpreters before creating any
    # HINT: initial_interps = _list_all_interpreters()
    initial_interps = []  # Replace with _list_all_interpreters()
    initial_count = len(initial_interps)

    # TODO: create a subinterpreter
    # HINT: interp = _create_interpreter()
    interp = None  # Replace with _create_interpreter()

    interp_id = _get_interp_id(interp)
    print(f"  Created subinterpreter with id: {interp_id}")

    # TODO: list all interpreters and verify count increased by 1
    # HINT: all_interps = _list_all_interpreters()
    all_interps = []  # Replace with _list_all_interpreters()
    active_count = len(all_interps)
    print(f"  Active interpreters: {active_count} (main + {active_count - 1} sub)")
    assert active_count == initial_count + 1

    # TODO: run code in the subinterpreter
    # HINT: _run_in_interpreter(interp, "x = 42")
    pass  # Replace with _run_in_interpreter call

    print("  Subinterpreter executed code successfully")

    # TODO: close the subinterpreter and verify count went back down
    # HINT: _close_interpreter(interp)
    pass  # Replace with _close_interpreter call

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

    # TODO: create a subinterpreter
    # TODO: run a computation in it (e.g., sum of range(1000))
    # HINT: _run_in_interpreter(interp, "total = sum(range(1000))")
    pass  # Replace with subinterpreter creation and code execution

    print("  Ran computation in subinterpreter: completed")

    # TODO: create a second subinterpreter
    # TODO: define a variable in interp1, try to access it from interp2
    # TODO: verify that the variable is NOT visible (expect an exception)
    # HINT: this demonstrates isolation between interpreters
    pass  # Replace with isolation demonstration

    # TODO: close both interpreters
    # HINT: _close_interpreter(interp) for each

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

    # TODO: measure sequential time (create interp, run, close, repeat)
    # HINT: use time.perf_counter() for timing
    start = time.perf_counter()
    # TODO: run cpu_code in two subinterpreters sequentially
    pass  # Replace with sequential execution
    sequential_time = time.perf_counter() - start

    print(f"  Sequential time: {sequential_time:.3f}s")

    # TODO: define a helper function that creates an interp, runs code, closes it
    # TODO: measure parallel time using two threads, each running the helper
    # HINT: t1 = threading.Thread(target=run_in_sub, args=(cpu_code,))
    start = time.perf_counter()
    # TODO: run cpu_code in two subinterpreters in parallel (via threads)
    pass  # Replace with parallel execution
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

    # TODO: define a CPU-bound function that loops `iterations` times
    # HINT: total = 0; for i in range(iterations): total += i * i
    def cpu_work_python():
        pass  # Replace with CPU-bound computation

    # TODO: measure time for 2 threads running cpu_work_python
    # HINT: create threads, start, join, measure with perf_counter
    threading_time = 0  # Replace with actual timing
    print(f"  Threading (2 CPU-bound tasks, shared GIL): {threading_time:.3f}s")

    # TODO: measure time for 2 subinterpreters running equivalent code
    # HINT: use the pattern from Section 3
    subinterp_time = 0  # Replace with actual timing
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

    # TODO: create 3 subinterpreters and store them in a list
    # HINT: interpreters_list = [_create_interpreter() for _ in range(3)]
    interpreters_list = []  # Replace with creation of 3 interpreters

    all_active = _list_all_interpreters()
    print(f"  Created 3 subinterpreters. Total active: {len(all_active)}")

    # TODO: run different code in each interpreter
    # HINT: _run_in_interpreter(interp, f"my_id = {i}; result = my_id ** 2")
    pass  # Replace with code execution in each

    print("  Ran isolated code in each subinterpreter.")

    # TODO: close all interpreters
    # HINT: for interp in interpreters_list: _close_interpreter(interp)
    pass  # Replace with cleanup

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
        print("  - Experimental API (Python 3.12+, PEP 734)")
        print("  - Best for: CPU-bound tasks needing lightweight parallelism")
        print()
        print("To try subinterpreters, use Python 3.12+ built with subinterpreter support.")
        print("The API is available via 'import interpreters' or 'import _interpreters'.")
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
        print("  - Experimental API (Python 3.12+, PEP 734)")
        print("  - Best for: CPU-bound tasks needing lightweight parallelism")
        print()
        print("All sections completed. Subinterpreters explored!")
