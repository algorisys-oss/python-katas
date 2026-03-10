# Kata 35 -- Packaging & Distribution

[prev: 34-testing-pytest](./34-testing-pytest.md) | [next: 36-tcp-socket-server](./36-tcp-socket-server.md)

---

## What We're Building

A complete tour of **Python packaging and distribution** -- the final piece before we start building the Ignite framework. We'll dissect `pyproject.toml`, understand package structure, define entry points, manage versions, and learn how wheels get built and published.

We'll build four demonstrations:
1. **pyproject.toml anatomy** -- parse and validate every section of a modern Python project config
2. **Package structure simulation** -- model a real package layout with `__init__.py`, sub-packages, and namespace packages
3. **Entry points & console_scripts** -- how `pip install mypackage` creates CLI commands
4. **Build & publish pipeline** -- the lifecycle from source tree to PyPI (simulated)

This kata ties together everything from Module 4 (memory, imports, testing) -- a well-packaged project uses proper imports (kata 32), is thoroughly tested (kata 34), and has a clean module structure.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `pyproject.toml` | Single config file for build system, metadata, tools | Every modern Python project |
| `setuptools` | Most common build backend | Default choice for most packages |
| `hatch` / `hatchling` | Modern build backend with version management | New projects wanting simplicity |
| `[project.scripts]` | Define console_scripts entry points | Making CLI tools from packages |
| `__version__` | Package version string | Tracking releases programmatically |
| `__init__.py` | Package marker and initialization | Every Python package directory |
| Namespace packages | Packages split across multiple directories (no `__init__.py`) | Plugin architectures, large orgs |
| Wheels (`.whl`) | Pre-built binary distribution format | `pip install` uses these |
| `sdist` | Source distribution (`.tar.gz`) | Fallback when no wheel available |
| PyPI | Python Package Index | Publishing packages for others |

## The Code

### 1. pyproject.toml Anatomy

The `pyproject.toml` file replaced `setup.py`, `setup.cfg`, and `requirements.txt` as the single source of truth for Python projects (PEP 518, PEP 621).

```python
import tomllib  # Python 3.11+ (use tomli for older versions)

PYPROJECT_TOML = """
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ignite-framework"
version = "0.1.0"
description = "A FastAPI-like web framework built from scratch"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
authors = [{name = "Kata Learner", email = "learner@example.com"}]
keywords = ["web", "framework", "asgi"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3.12",
]
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.3.0"]

[project.scripts]
ignite = "ignite.cli:main"

[project.urls]
Homepage = "https://github.com/example/ignite"
Documentation = "https://ignite.readthedocs.io"

[tool.ruff]
line-length = 99
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""

config = tomllib.loads(PYPROJECT_TOML)
print(f"Package: {config['project']['name']}")
print(f"Version: {config['project']['version']}")
print(f"Python:  {config['project']['requires-python']}")
print(f"Build:   {config['build-system']['build-backend']}")
```

**Key sections:**
- **`[build-system]`** -- which tool builds the package (`setuptools`, `hatchling`, `flit`, `maturin`)
- **`[project]`** -- PEP 621 metadata (name, version, dependencies)
- **`[project.scripts]`** -- console entry points (creates CLI commands on install)
- **`[project.optional-dependencies]`** -- extras like `pip install mypackage[dev]`
- **`[tool.*]`** -- tool-specific config (ruff, pytest, mypy, etc.)

### 2. Package Structure

A proper Python package follows a predictable layout. The `__init__.py` file marks a directory as a package and controls what gets imported.

```python
# Simulating a package structure:
#
# ignite/
#   __init__.py          <- Package root, defines __version__
#   app.py               <- Application class
#   routing/
#     __init__.py         <- Sub-package
#     router.py           <- Router implementation
#     decorators.py       <- Route decorators
#   middleware/
#     __init__.py         <- Sub-package
#     base.py             <- Base middleware class

# The __init__.py controls the public API:
# ignite/__init__.py would contain:
#   from .app import Ignite
#   __version__ = "0.1.0"
#   __all__ = ["Ignite", "__version__"]
#
# This means users can write:
#   from ignite import Ignite
# Instead of:
#   from ignite.app import Ignite
```

### 3. Version Management

There are several strategies for keeping `__version__` in sync with `pyproject.toml`:

```python
# Strategy 1: Single source in pyproject.toml
# version = "0.1.0"  (in pyproject.toml)
# Then read it at runtime via importlib.metadata

import importlib.metadata

# In a real installed package:
# version = importlib.metadata.version("ignite-framework")

# Strategy 2: dynamic version from __init__.py
# pyproject.toml: dynamic = ["version"]
# [tool.setuptools.dynamic]
# version = {attr = "ignite.__version__"}

# Strategy 3: Hatch version management
# [tool.hatch.version]
# path = "src/ignite/__init__.py"
```

### 4. Entry Points (console_scripts)

Entry points are how `pip install mypackage` creates executable commands:

```python
# In pyproject.toml:
# [project.scripts]
# ignite = "ignite.cli:main"
#
# This means:
# 1. pip creates a script called "ignite" in your PATH
# 2. Running "ignite" calls ignite.cli.main()
# 3. The function receives no arguments (use argparse/click inside)

def main():
    """Entry point for the 'ignite' CLI command."""
    import argparse
    parser = argparse.ArgumentParser(prog="ignite")
    parser.add_argument("command", choices=["run", "init", "routes"])
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "run":
        print(f"Starting Ignite server on port {args.port}...")
    elif args.command == "init":
        print("Creating new Ignite project...")
    elif args.command == "routes":
        print("Listing registered routes...")
```

### 5. Namespace Packages

Namespace packages (PEP 420) allow a package to be split across multiple directories -- no `__init__.py` required:

```python
# Namespace packages are used by large organizations:
#
# Directory A (installed via pip install company-auth):
#   company/
#     auth/
#       __init__.py
#       login.py
#
# Directory B (installed via pip install company-billing):
#   company/
#     billing/
#       __init__.py
#       invoice.py
#
# Notice: company/ has NO __init__.py!
# Python merges both into one "company" namespace:
#   from company.auth import login
#   from company.billing import invoice

import importlib
import sys

# Check if a package uses namespace packaging
def is_namespace_package(name: str) -> bool:
    """Detect if a module is a namespace package (no __init__.py)."""
    try:
        mod = importlib.import_module(name)
        # Namespace packages have no __file__ attribute
        return not hasattr(mod, "__file__") or mod.__file__ is None
    except ImportError:
        return False
```

### 6. Building & Publishing

```python
# Build commands (run from project root):
#
# Build both sdist and wheel:
#   python -m build
#
# This creates:
#   dist/
#     ignite_framework-0.1.0.tar.gz    <- sdist (source)
#     ignite_framework-0.1.0-py3-none-any.whl  <- wheel (built)
#
# Wheel filename anatomy:
#   {name}-{version}-{python}-{abi}-{platform}.whl
#   py3    = Python 3 only
#   none   = no ABI dependency (pure Python)
#   any    = runs on any platform
#
# Publish to PyPI:
#   python -m twine upload dist/*
#
# Publish to Test PyPI first:
#   python -m twine upload --repository testpypi dist/*
#
# Install from Test PyPI:
#   pip install --index-url https://test.pypi.org/simple/ ignite-framework
```

## Playground

```python
python playground/35_packaging.py
```

Expected output:

```
--- Section 1: pyproject.toml Anatomy ---
  Parsed pyproject.toml successfully
  Package name: ignite-framework
  Version: 0.1.0
  Build backend: setuptools.build_meta
  Requires Python: >=3.12
  Dependencies: [] (zero external deps for core)
  Dev dependencies: ['pytest>=8.0', 'ruff>=0.3.0']
  Entry point: ignite -> ignite.cli:main
  [VALID] All required fields present

--- Section 2: Package Structure Simulation ---
  Simulated package tree:
    ignite/
      __init__.py (exports: Ignite, __version__)
      app.py (classes: Ignite)
      routing/
        __init__.py (exports: Router, route)
        router.py (classes: Router)
        decorators.py (functions: route, get, post)
      middleware/
        __init__.py (exports: Middleware)
        base.py (classes: Middleware)
  Total: 3 modules, 2 sub-packages, 7 files
  [VALID] Package structure is well-organized

--- Section 3: Version Management ---
  __version__ from module attribute: 0.1.0
  Version from pyproject.toml: 0.1.0
  importlib.metadata available: True
  Versions match: True
  PEP 440 valid version: True

--- Section 4: Entry Points & console_scripts ---
  Entry point: ignite = ignite.cli:main
  Parsed -> module=ignite.cli, function=main
  Simulated CLI: ignite run --port 8000
  Simulated CLI: ignite init
  Simulated CLI: ignite routes
  [VALID] Entry points configured correctly

--- Section 5: Build Pipeline Simulation ---
  Build backend: setuptools.build_meta
  Source files collected: 7 .py files
  sdist: ignite_framework-0.1.0.tar.gz
  wheel:  ignite_framework-0.1.0-py3-none-any.whl
  Wheel filename anatomy:
    name=ignite_framework, version=0.1.0
    python=py3, abi=none, platform=any
  [VALID] Build artifacts would be correct

--- Summary ---
Packaging is the bridge between writing code and sharing it:
  - pyproject.toml is the single source of truth (PEP 518 + 621)
  - setuptools or hatchling as the build backend
  - __init__.py controls your package's public API
  - Entry points create CLI commands on install
  - Wheels are the modern distribution format
  - Test on TestPyPI before publishing to PyPI

All 5 sections passed. Packaging & distribution concepts mastered!
Next up: Kata 36 -- we start building the Ignite framework!
```

## How It Works

### The Packaging Pipeline

```
Source Code                    pyproject.toml               Distribution
-----------                    --------------               ------------
ignite/                   +--> [build-system]          +--> sdist (.tar.gz)
  __init__.py             |    [project]               |    wheel (.whl)
  app.py                  |    [project.scripts]       |
  routing/                |    [tool.*]                |
    router.py       ------+                      ------+
                          build                        upload
                    (python -m build)            (python -m twine)
                                                       |
                                                       v
                                                     PyPI
                                                       |
                                                       v
                                                  pip install
```

### Build Backends Compared

| Backend | Config | Strengths |
|---|---|---|
| `setuptools` | `[build-system] requires = ["setuptools"]` | Most mature, handles C extensions |
| `hatchling` | `[build-system] requires = ["hatchling"]` | Modern, great version management |
| `flit-core` | `[build-system] requires = ["flit-core"]` | Simplest for pure-Python packages |
| `maturin` | `[build-system] requires = ["maturin"]` | Rust + Python (PyO3) packages |

### Package vs Namespace Package

```
Regular package:              Namespace package:
  mypackage/                    org/           <- NO __init__.py
    __init__.py  <- REQUIRED      auth/
    module.py                       __init__.py
                                    login.py
                                  billing/     <- separate install
                                    __init__.py
                                    invoice.py
```

## Exercises

1. **Add a `[project.gui-scripts]`** section to the pyproject.toml parser and validate it creates GUI entry points (like `console_scripts` but for windowed apps).

2. **Implement version bumping** -- write a function that reads a version string like `"0.1.0"`, accepts a bump type (`major`, `minor`, `patch`), and returns the new version (e.g., `bump("0.1.0", "minor")` -> `"0.2.0"`).

3. **Detect circular imports** -- given the simulated package structure, write a function that checks if any module's imports would create a circular dependency.

4. **Wheel filename parser** -- write a function that takes a `.whl` filename and returns a dict with `name`, `version`, `python`, `abi`, and `platform`.

5. **Compare build backends** -- extend the pyproject.toml parser to accept `hatchling` and `flit-core` as build backends and validate each backend's specific config sections.

## What's Next

With packaging mastered, we have all the Python fundamentals we need. In [Kata 36: TCP Socket Server](./36-tcp-socket-server.md), we begin **Module 5: Building Ignite** -- starting with a raw TCP socket server to understand what happens beneath HTTP. Everything from Module 1-4 comes together as we build a real framework.

---

[prev: 34-testing-pytest](./34-testing-pytest.md) | [next: 36-tcp-socket-server](./36-tcp-socket-server.md)
