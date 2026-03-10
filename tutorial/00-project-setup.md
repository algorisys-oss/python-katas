# Kata 00: Project Setup

[Next: Kata 01 - Python Data Model ->](01-python-data-model.md)

---

## What We're Building

Welcome to **Python Katas** -- a 79-step tutorial series that takes you from
core Python all the way to building **Ignite**, a FastAPI-like web framework,
from scratch.

Here's the full roadmap:

| Module | Katas | What You'll Learn |
|--------|-------|-------------------|
| 1. Pythonic Foundations | 00--10 | Data model, generators, decorators, type hints |
| 2. OOP & SOLID | 11--20 | Classes, descriptors, metaclasses, SOLID principles |
| 3. Concurrency | 21--30 | Threading, GIL, multiprocessing, async, free-threaded Python |
| 4. Advanced Features | 31--35 | Memory, imports, testing, packaging |
| 5--12. Build Ignite | 36--78 | A full FastAPI-like framework on ASGI |

Katas 00--35 use **zero external dependencies** -- pure stdlib only. You'll
understand Python deeply before reaching for any library.

In this kata, we set up the project: a virtual environment, a `pyproject.toml`,
and a project structure that will carry us through all 79 steps.

## Prerequisites

- **Python 3.12+** installed. Check with:
  ```bash
  python3 --version
  ```
  If not installed, follow the [official guide](https://www.python.org/downloads/).

- **A text editor** -- VS Code with the Python extension, PyCharm, or anything you prefer.

- **A terminal** -- all commands in this tutorial use bash.

## Concepts You'll Learn

- **Virtual environments** (`venv`) -- isolated Python installations per project
- **`pyproject.toml`** -- the modern Python project configuration file
- **Project structure** -- organizing source code, tests, and tutorials
- **`sys.path`** -- how Python finds modules to import

## The Code

### 1. Create the project directory

If you're starting fresh (skip if you already cloned this repo):

```bash
mkdir python-katas && cd python-katas
```

### 2. Create a virtual environment

A virtual environment gives your project its own isolated Python installation.
Packages you install here won't pollute your system Python.

```bash
python3 -m venv .venv
```

This creates a `.venv/` directory containing:
- A copy of the Python interpreter
- Its own `pip` for installing packages
- An empty `site-packages/` directory for project dependencies

### 3. Activate the virtual environment

```bash
source .venv/bin/activate
```

Your terminal prompt changes to show `(.venv)` -- this means all `python` and
`pip` commands now use the isolated environment.

Verify it's working:

```bash
which python
# Output: /path/to/python-katas/.venv/bin/python

python --version
# Output: Python 3.12.x (or newer)
```

To deactivate later, just run `deactivate`.

### 4. Create `pyproject.toml`

`pyproject.toml` is the modern standard for Python project configuration
(PEP 621). It replaces the old `setup.py` and `setup.cfg` approach.

```toml
[project]
name = "python-katas"
version = "0.1.0"
description = "Core Python mastery -> Build a FastAPI-like framework from scratch, step by step."
requires-python = ">=3.12"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

### 5. Create the directory structure

```bash
mkdir -p src/ignite tutorial playground tests
```

The layout:

```
python-katas/
├── src/                  # Source code
│   └── ignite/           # Framework core (built from kata 36 onward)
├── tutorial/             # Step-by-step kata markdown files
├── playground/           # Standalone runnable scripts for each kata
├── tests/                # Test files
├── pyproject.toml        # Project configuration
└── .gitignore            # Git ignore patterns
```

- **`src/ignite/`** stays empty until kata 36. Katas 00--35 focus on core Python.
- **`playground/`** holds one runnable script per kata -- your sandbox for experimentation.
- **`tutorial/`** holds the markdown tutorials you're reading right now.

### 6. Create the entry point

Create `src/app.py` -- this will eventually be the demo application using
the Ignite framework. For now, a simple hello:

```python
# src/app.py
print("Ignite is ready!")
```

### 7. Verify it works

```bash
python src/app.py
```

You should see:

```
Ignite is ready!
```

### 8. Run the playground script

Every kata has a playground script in `playground/`. Run this kata's:

```bash
python playground/00_project_setup.py
```

Expected output:

```
=== Python Environment Info ===
Python version: 3.12.x
Python path: /path/to/python-katas/.venv/bin/python
Virtual env: /path/to/python-katas/.venv

=== sys.path (where Python looks for modules) ===
  [0] /path/to/python-katas/playground
  [1] /path/to/python-katas/.venv/lib/python3.12/...
  ...

=== Module Check ===
sys module loaded from: /usr/lib/python3.12/sys (built-in)
os module loaded from: /usr/lib/python3.12/os.py
json module loaded from: /usr/lib/python3.12/json/__init__.py

=== Basic Assertions ===
All assertions passed!
```

(Exact paths will differ on your machine.)

## Playground

```python
# playground/00_project_setup.py
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

# Virtual env should be active
assert os.environ.get("VIRTUAL_ENV"), (
    "Virtual environment not active! Run: source .venv/bin/activate"
)

print("All assertions passed!")
```

Run it:

```bash
python playground/00_project_setup.py
```

## How It Works

### Virtual Environments (`venv`)

When you run `python3 -m venv .venv`, Python creates an isolated copy of itself:

```
.venv/
├── bin/
│   ├── python          # Symlink to Python interpreter
│   ├── pip             # Package installer for this env
│   └── activate        # Shell script to activate the env
├── lib/
│   └── python3.12/
│       └── site-packages/   # Installed packages go here (empty initially)
└── pyvenv.cfg          # Config: points to base Python installation
```

**Why use a venv?**

Without one, `pip install` puts packages into your system Python. That means:
- Different projects can't use different versions of the same package
- You might break system tools that depend on specific package versions
- You can't cleanly reproduce your project's dependencies

With a venv, each project gets its own `site-packages/`. Clean, isolated, reproducible.

**How activation works:**

`source .venv/bin/activate` prepends `.venv/bin/` to your `$PATH`. That's it.
When you type `python`, your shell finds `.venv/bin/python` before
`/usr/bin/python`. Deactivating just removes it from `$PATH`.

### `pyproject.toml`

This is the modern standard for Python project metadata (PEP 621, PEP 517):

```toml
[project]
name = "python-katas"           # Package name (used by pip)
version = "0.1.0"               # Semantic versioning
description = "..."             # One-line description
requires-python = ">=3.12"      # Minimum Python version

[build-system]
requires = ["setuptools>=68.0"]           # Build tool
build-backend = "setuptools.backends._legacy:_Backend"  # How to build the package
```

**Key fields:**
- **`name`** -- the installable package name. `pip install python-katas` would look for this.
- **`requires-python`** -- enforced by pip. If someone tries to install on Python 3.10, pip refuses.
- **`[build-system]`** -- tells pip which tool to use when building the package.

Before `pyproject.toml`, Python projects used `setup.py` (executable code) or
`setup.cfg` (INI format). `pyproject.toml` is the unified, declarative replacement.

### `sys.path` -- How Python Finds Modules

When you write `import json`, Python searches directories in `sys.path` order:

1. The directory containing the script being run
2. `PYTHONPATH` environment variable entries (if set)
3. The virtual environment's `site-packages/`
4. The standard library

The first match wins. This is why you can shadow stdlib modules (accidentally
naming your file `json.py` would break `import json`).

## Exercises

### Exercise 1: Create a module and import it

Create a file `playground/greet.py`:

```python
# playground/greet.py
def hello(name: str) -> str:
    return f"Hello, {name}! Welcome to Python Katas."
```

Then create `playground/test_greet.py`:

```python
# playground/test_greet.py
from greet import hello

message = hello("Developer")
print(message)
# Output: Hello, Developer! Welcome to Python Katas.

assert message == "Hello, Developer! Welcome to Python Katas."
print("Import test passed!")
```

Run it:

```bash
python playground/test_greet.py
```

**Why does this work?** Because Python adds the script's directory
(`playground/`) to `sys.path[0]`, so `from greet import hello` finds
`playground/greet.py`.

### Exercise 2: Break it on purpose

Try running `test_greet.py` from the project root without the path:

```bash
cd /path/to/python-katas
python -c "from greet import hello; print(hello('test'))"
```

This fails with `ModuleNotFoundError` because the current directory is
`python-katas/`, not `playground/`. Python can't find `greet.py`.

**Fix it** by adding the path:

```bash
PYTHONPATH=playground python -c "from greet import hello; print(hello('test'))"
# Output: Hello, test! Welcome to Python Katas.
```

### Exercise 3: Inspect your environment

Run Python interactively and explore:

```python
python3
>>> import sys
>>> sys.version_info
# Output: sys.version_info(major=3, minor=12, micro=...)
>>> sys.prefix
# Output: '/path/to/python-katas/.venv'  (your venv path)
>>> sys.base_prefix
# Output: '/usr'  (or wherever system Python lives)
>>> sys.prefix == sys.base_prefix
# Output: False  (this confirms you're in a venv!)
```

When `sys.prefix != sys.base_prefix`, you know a virtual environment is active.

## What's Next

Your project is set up and verified. In **Kata 01 -- Python Data Model**, we'll
dive into the dunder methods that make Python objects work: `__repr__`,
`__str__`, `__eq__`, `__hash__`, `__len__`, and `__getitem__`. You'll build a
`Card` and `Deck` class that behaves like a built-in Python collection.

---

[Next: Kata 01 - Python Data Model ->](01-python-data-model.md)
