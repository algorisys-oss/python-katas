"""
Kata 00 -- Project Setup
Verify your Python environment is configured correctly.
"""
import sys
import os

# --- Python version info ---
print("=== Python Environment Info ===")
print(f"Python version: {sys.version.split()[0]}")
print(f"Python path: {sys.executable}")

# Show virtual environment (if active)
venv = os.environ.get("VIRTUAL_ENV", "Not active")
print(f"Virtual env: {venv}")

# --- sys.path: where Python searches for imports ---
print(f"\n=== sys.path (where Python looks for modules) ===")
for i, path in enumerate(sys.path):
    print(f"  [{i}] {path}")

# --- Module locations ---
print(f"\n=== Module Check ===")
print(f"sys module loaded from: {getattr(sys, '__file__', 'built-in')}")
print(f"os module loaded from: {os.__file__}")

import json
print(f"json module loaded from: {json.__file__}")

# --- Assertions to verify the setup ---
print(f"\n=== Basic Assertions ===")

# TODO: Write an assertion that checks we're running Python 3.12 or higher.
# HINT: use sys.version_info and compare it as a tuple, e.g. (3, 12)
try:
    pass
except (AssertionError, TypeError, AttributeError, Exception) as e:
    print(f"  ❌ Not yet implemented: {e}")

# TODO: Assert that sys, os, and json are not None (i.e. they imported successfully).
try:
    pass
except (AssertionError, TypeError, AttributeError, Exception) as e:
    print(f"  ❌ Not yet implemented: {e}")

# TODO: Check whether a virtual environment is active using os.environ.get("VIRTUAL_ENV").
#       Print the path if active, or a message saying it's not active.
# HINT: This is informational — no assertion needed, just an if/else print.
try:
    pass
except (AssertionError, TypeError, AttributeError, Exception) as e:
    print(f"  ❌ Not yet implemented: {e}")

print("All assertions passed!")
