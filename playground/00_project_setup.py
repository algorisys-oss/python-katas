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

# Python 3.12+ is required
assert sys.version_info >= (3, 12), (
    f"Python 3.12+ required, got {sys.version_info.major}.{sys.version_info.minor}"
)

# We should be able to import stdlib modules
assert sys is not None
assert os is not None
assert json is not None

# Virtual env check (informational, not required for webapp runner)
venv_active = os.environ.get("VIRTUAL_ENV")
if venv_active:
    print(f"Virtual environment is active: {venv_active}")
else:
    print("No virtual environment active (ok when running from webapp)")

print("All assertions passed!")
