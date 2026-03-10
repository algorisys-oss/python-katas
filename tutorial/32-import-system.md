# Kata 32 -- Import System & Modules

[prev: 31-slots-memory](./31-slots-memory.md) | [next: 33-logging-debugging](./33-logging-debugging.md)

---

## What We're Building

A deep dive into **Python's import system** -- one of the most powerful and customizable parts of the language. We'll explore how `import` actually works under the hood, build custom import hooks, implement lazy loading, and understand the pitfalls of circular imports.

We'll build five demonstrations:
1. **Module attributes** -- `__name__`, `__file__`, `__package__`, `__spec__`, and what they tell us
2. **`sys.modules` cache & `importlib`** -- how Python caches imports and how to reload/dynamically import
3. **`__all__` and controlled exports** -- controlling what `from module import *` exposes
4. **Lazy imports** -- deferring expensive imports until first use
5. **Import hooks** -- custom finders and loaders that intercept the import machinery
6. **Circular imports** -- why they happen and patterns to avoid them

All examples are **self-contained** -- no actual module files needed. We simulate packages and modules inline using `sys.modules`, `types.ModuleType`, and `importlib`.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `importlib.import_module()` | Dynamically import a module by name string | Plugin systems, dynamic loading |
| `importlib.reload()` | Re-execute a module's code (bypass cache) | Development, hot-reloading |
| `sys.modules` | Dict cache of all imported modules | Inspecting, mocking, or replacing modules |
| `__all__` | List of names exported by `from mod import *` | Controlling public API of a package |
| `__name__` | Module's fully qualified name (or `"__main__"`) | Guard scripts, identify context |
| `__file__` | Path to the module's source file | Locating resources relative to module |
| `__package__` | Package the module belongs to | Resolving relative imports |
| `__import__()` | Built-in function behind the `import` statement | Low-level import customization |
| `types.ModuleType` | Create module objects programmatically | Dynamic module generation |
| Lazy imports | Defer module loading until first attribute access | Reducing startup time |
| Import hooks (finders/loaders) | Intercept and customize import behavior | Custom module sources, transpilers |
| Circular imports | Mutual imports between modules | Understanding and avoiding them |

## The Code

### Module Attributes

Every Python module has special attributes set automatically by the import system. Understanding these is foundational.

```python
import sys
import types

# __name__: the module's fully qualified name
# When run as a script, __name__ == "__main__"
# When imported, __name__ == the module name
print(f"This module's __name__: {__name__}")

# __file__: path to source file (not always available)
print(f"This module's __file__: {__file__}")

# __package__: the parent package (None for top-level scripts)
print(f"This module's __package__: {__package__}")

# Create a module dynamically to inspect attributes
mod = types.ModuleType("my_dynamic_module")
mod.__file__ = "/fake/path/my_module.py"
mod.__package__ = "my_package"
mod.greeting = "Hello from dynamic module!"

# Register it in sys.modules so import can find it
sys.modules["my_dynamic_module"] = mod

# Now we can import it!
import my_dynamic_module
print(my_dynamic_module.greeting)  # "Hello from dynamic module!"
```

The `__name__ == "__main__"` idiom is Python's most common pattern -- it distinguishes between a module being run as a script vs being imported.

### sys.modules Cache and importlib

When you write `import foo`, Python doesn't always read from disk. It first checks `sys.modules`, a dict that caches every module imported during the session.

```python
import sys
import importlib
import types

# sys.modules is just a dict: module_name -> module_object
print(f"Number of cached modules: {len(sys.modules)}")
print(f"'sys' in sys.modules: {'sys' in sys.modules}")

# importlib.import_module() -- dynamic imports by string name
json_mod = importlib.import_module("json")
print(f"Dynamically imported: {json_mod.__name__}")
print(f"json.dumps works: {json_mod.dumps([1, 2, 3])}")

# Import a submodule dynamically
os_path = importlib.import_module("os.path")
print(f"os.path.join: {os_path.join('a', 'b', 'c')}")

# importlib.reload() -- re-execute module code
# Useful during development, but be careful: existing references
# to the old module's objects won't update
counter_mod = types.ModuleType("counter_mod")
counter_mod.count = 0
exec("count += 1", counter_mod.__dict__)
print(f"count after exec: {counter_mod.count}")  # 1
```

**Key insight:** `sys.modules` is mutable. You can inject fake modules, remove cached modules to force re-import, or replace modules with mocks for testing.

### __all__ and Controlled Exports

`__all__` defines the public API of a module -- what gets exported when someone does `from module import *`.

```python
import sys
import types

# Simulate a module with __all__
math_utils = types.ModuleType("math_utils")
math_utils.__all__ = ["add", "subtract"]  # Only these are "public"

# Public functions
math_utils.add = lambda a, b: a + b
math_utils.subtract = lambda a, b: a - b

# Internal function (not in __all__)
math_utils._validate = lambda x: isinstance(x, (int, float))
math_utils.multiply = lambda a, b: a * b  # Also not in __all__

sys.modules["math_utils"] = math_utils

# __all__ controls "from module import *" behavior
public_names = math_utils.__all__
print(f"Public API: {public_names}")       # ['add', 'subtract']
print(f"add(2, 3) = {math_utils.add(2, 3)}")
print(f"multiply exists but not in __all__: {math_utils.multiply(2, 3)}")
```

**Best practice:** Always define `__all__` in your `__init__.py` files and public modules. It serves as documentation AND controls star-import behavior.

### __import__ -- The Built-in Behind import

The `import` statement ultimately calls `__import__()`. You rarely use it directly, but understanding it helps when you need low-level control.

```python
# These are equivalent:
import json                           # Statement form
json2 = __import__("json")            # Built-in function form

print(f"Same object: {json is json2}")  # True

# __import__ with fromlist for submodules
os_path = __import__("os.path", fromlist=["path"])
print(f"os.path.exists: {os_path.exists.__name__}")

# Prefer importlib.import_module() over __import__()
# It's cleaner and handles edge cases better
```

### Lazy Imports

Large applications can have slow startup times because all imports happen eagerly at module load. Lazy imports defer loading until a module is actually used.

```python
import sys
import types
import importlib

class LazyModule:
    """A descriptor that imports a module on first access."""

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module = None

    def _load(self):
        if self._module is None:
            self._module = importlib.import_module(self._module_name)
        return self._module

    def __getattr__(self, name):
        return getattr(self._load(), name)

    def __repr__(self):
        if self._module is None:
            return f"<LazyModule '{self._module_name}' (not loaded)>"
        return f"<LazyModule '{self._module_name}' (loaded)>"


# Usage: defer importing heavy modules
lazy_json = LazyModule("json")
print(f"Before use: {lazy_json}")           # not loaded
result = lazy_json.dumps({"a": 1})          # triggers import
print(f"After use: {lazy_json}")            # loaded
print(f"Result: {result}")                  # '{"a": 1}'

# Python 3.12+ pattern: module-level __getattr__ for lazy exports
# In a real module file, you'd write:
#
# def __getattr__(name):
#     if name == "heavy_lib":
#         import heavy_lib
#         globals()["heavy_lib"] = heavy_lib
#         return heavy_lib
#     raise AttributeError(f"module has no attribute {name}")
```

**PEP 690** proposes built-in lazy imports for Python. Until then, the `LazyModule` pattern and module-level `__getattr__` (PEP 562) are the standard approaches.

### Import Hooks -- Custom Finders and Loaders

Python's import system is extensible through **meta path finders** (`sys.meta_path`) and **path hooks** (`sys.path_hooks`). This lets you import from databases, URLs, or even generate modules on the fly.

```python
import sys
import types
import importlib
import importlib.abc
import importlib.machinery

class DictModuleLoader(importlib.abc.Loader):
    """Loader that populates modules from a config dict."""

    def __init__(self, config: dict):
        self._config = config

    def create_module(self, spec):
        return None  # Use default module creation

    def exec_module(self, module):
        """Populate module attributes from config."""
        config = self._config[module.__name__]
        for key, value in config.items():
            setattr(module, key, value)

class DictModuleFinder(importlib.abc.MetaPathFinder):
    """An import hook that creates modules from a config dict."""

    def __init__(self, config: dict):
        self._config = config
        self._loader = DictModuleLoader(config)

    def find_spec(self, fullname, path, target=None):
        """Called by the import system to find a module."""
        if fullname in self._config:
            return importlib.machinery.ModuleSpec(
                fullname, self._loader,
                origin=f"<dict:{fullname}>",
            )
        return None  # Let other finders try

# Register our custom finder
config_modules = {
    "app_config": {
        "DEBUG": True,
        "DATABASE_URL": "sqlite:///app.db",
        "MAX_CONNECTIONS": 10,
    },
    "feature_flags": {
        "ENABLE_CACHE": True,
        "ENABLE_LOGGING": False,
        "NEW_UI": True,
    },
}

finder = DictModuleFinder(config_modules)
sys.meta_path.insert(0, finder)

# Now we can import these "virtual" modules!
app_config = importlib.import_module("app_config")
print(f"DEBUG: {app_config.DEBUG}")
print(f"DB URL: {app_config.DATABASE_URL}")

feature_flags = importlib.import_module("feature_flags")
print(f"Cache enabled: {feature_flags.ENABLE_CACHE}")

# Clean up: remove our hook and fake modules
sys.meta_path.remove(finder)
del sys.modules["app_config"]
del sys.modules["feature_flags"]
```

The import hook system has two layers:
1. **`sys.meta_path`** -- list of finders checked first (before filesystem)
2. **`sys.path_hooks`** -- list of callables that create finders for specific path entries

### Circular Imports and How to Avoid Them

Circular imports happen when module A imports module B, and module B imports module A. They're a common source of `ImportError` and `AttributeError`.

```python
import sys
import types

# Simulate circular imports to understand the problem
# Module A wants to use B, and B wants to use A

# --- The BROKEN way (simplified) ---
# When A imports B, B tries to import A, but A isn't finished loading yet.
# B gets a partially-initialized A module -- some attributes missing!

mod_a = types.ModuleType("circular_a")
mod_b = types.ModuleType("circular_b")

# Simulate partial initialization
mod_a.value_a = 42
# mod_a.func_a is NOT defined yet (still loading)

sys.modules["circular_a"] = mod_a
sys.modules["circular_b"] = mod_b

# B tries to access A's attribute that doesn't exist yet
try:
    _ = mod_a.func_a  # AttributeError!
except AttributeError as e:
    print(f"Circular import problem: {e}")

# --- Solutions ---
print("\nSolution 1: Import at function level (defer the import)")
print("  def process():")
print("      from other_module import helper  # imported when called, not at load")

print("\nSolution 2: Import the module, not the name")
print("  import other_module  # works: module object exists even if incomplete")
print("  other_module.helper()  # resolved at call time, not import time")

print("\nSolution 3: Restructure -- extract shared code into a third module")
print("  common.py  <- shared utilities")
print("  module_a.py -> imports common")
print("  module_b.py -> imports common")

print("\nSolution 4: Use TYPE_CHECKING for type hints only")
print("  from __future__ import annotations")
print("  from typing import TYPE_CHECKING")
print("  if TYPE_CHECKING:")
print("      from other_module import SomeClass  # never runs at runtime")

# Clean up
del sys.modules["circular_a"]
del sys.modules["circular_b"]
```

**Rule of thumb:** If you have circular imports, your modules are too tightly coupled. Refactor shared code into a separate module.

## Playground

See `playground/32_import_system.py` for a complete runnable demonstration covering all six sections.

## How It Works

```
                       Python Import System
                       ====================

  import foo          ┌──────────────────────────┐
  ─────────────────>  │   1. Check sys.modules   │
                      │      (module cache)       │
                      └─────────┬────────────────┘
                                │
                         Found? │
                    ┌───────────┼───────────────┐
                    │ Yes       │           No  │
                    ▼           │               ▼
              Return cached     │    ┌──────────────────┐
              module            │    │ 2. sys.meta_path  │
                                │    │    finders        │
                                │    └────────┬─────────┘
                                │             │
                                │             ▼
                                │    ┌──────────────────┐
                                │    │ 3. sys.path +    │
                                │    │    sys.path_hooks │
                                │    └────────┬─────────┘
                                │             │
                                │             ▼
                                │    ┌──────────────────┐
                                │    │ 4. Load module   │
                                │    │    (exec code)   │
                                │    └────────┬─────────┘
                                │             │
                                │             ▼
                                │    ┌──────────────────┐
                                │    │ 5. Cache in      │
                                │    │    sys.modules   │
                                │    └────────┬─────────┘
                                │             │
                                └─────────────┘
                                      │
                                      ▼
                              Module object returned


  Module Attributes:
  ┌─────────────────────────────────────────────────┐
  │  __name__     "foo" or "__main__"               │
  │  __file__     "/path/to/foo.py"                 │
  │  __package__  "parent_package" or ""            │
  │  __spec__     ModuleSpec (loader, origin, etc.) │
  │  __all__      ["public", "names"]               │
  │  __dict__     Module's namespace (globals)      │
  └─────────────────────────────────────────────────┘
```

## Exercises

1. **Plugin loader:** Build a system that discovers and loads "plugin" modules from a dict, where each plugin must implement a `register()` function. Use import hooks.

2. **Lazy import timer:** Extend `LazyModule` to track how long each module takes to import. Print a report of import times at program exit using `atexit`.

3. **Circular import detector:** Write a function that walks `sys.modules` and checks for circular import chains by inspecting each module's imports. (Hint: use `inspect.getmembers()` and check for module types.)

4. **Module rewriter:** Create an import hook that transforms module source code before execution (e.g., replace all `print()` calls with `logging.info()` calls). This is how tools like `pytest` rewrite assertions.

5. **Export validator:** Write a decorator `@public` that automatically adds a function's name to the module's `__all__`. Verify it works by checking `__all__` after decorating several functions.

## What's Next

In [Kata 33 -- Logging & Debugging](./33-logging-debugging.md), we'll explore Python's `logging` module in depth -- configuring handlers, formatters, and filters, plus debugging techniques with `pdb`, `breakpoint()`, and `traceback`. The import system knowledge from this kata will help us understand how logging's module-level logger pattern works.

---

[prev: 31-slots-memory](./31-slots-memory.md) | [next: 33-logging-debugging](./33-logging-debugging.md)
