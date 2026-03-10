"""
Kata 32 -- Import System & Modules
Run: python playground/skeletons/32_import_system.py

Deep dive into Python's import machinery: importlib, sys.modules cache,
__all__, lazy imports, import hooks, circular imports, and module attributes.

All examples are self-contained -- no external module files needed.
Completes within 5 seconds.
"""

import importlib
import importlib.abc
import importlib.machinery
import sys
import types


# ===========================================================================
# SECTION 1: Module Attributes
# ===========================================================================

def demo_module_attributes():
    """Explore __name__, __file__, __package__, __spec__ and friends."""

    # --- __name__: module's fully qualified name ---
    # TODO: Print __name__ of this script, sys module, and types module
    # HINT: Access __name__ directly or via module.__name__

    # --- __file__: path to source file ---
    # TODO: Print __file__ of this script
    # TODO: Check if sys has __file__ using hasattr()

    # --- __package__: parent package name ---
    # TODO: Print __package__ of this script (will be None or empty)
    # TODO: Import json.decoder and print its __package__
    # HINT: importlib.import_module('json.decoder').__package__

    # --- __spec__: ModuleSpec with import metadata ---
    # TODO: Import json and print its __spec__.name and __spec__.origin
    pass

    # --- Create a dynamic module ---
    # TODO: Create a module using types.ModuleType("my_dynamic_mod")
    # TODO: Set __file__, __package__, and add a 'value' attribute (99)
    # TODO: Add a 'greet' function: lambda name: f"Hello, {name}!"
    # TODO: Register it in sys.modules
    # HINT: sys.modules["my_dynamic_mod"] = mod
    pass

    # TODO: Import my_dynamic_mod and verify value == 99
    # TODO: Verify greet("Python") == "Hello, Python!"
    pass

    # TODO: Clean up by removing from sys.modules
    # HINT: del sys.modules["my_dynamic_mod"]
    pass


# ===========================================================================
# SECTION 2: sys.modules Cache & importlib
# ===========================================================================

def demo_sys_modules_and_importlib():
    """Demonstrate the module cache and dynamic imports.

    Key functions:
    - importlib.import_module(name) -> module
    - sys.modules[name] -> cached module
    - __import__(name) -> module (low-level)
    """

    # --- sys.modules is a dict of all imported modules ---
    # TODO: Print the total number of cached modules: len(sys.modules)
    # TODO: Check if 'sys' and 'json' are in the cache
    pass

    # --- importlib.import_module() for dynamic imports ---
    # TODO: Dynamically import "json" and call dumps([1, 2])
    # HINT: json_mod = importlib.import_module("json")
    pass

    # TODO: Import a submodule: importlib.import_module("os.path")
    # TODO: Call os_path.join('a', 'b')
    pass

    # --- Inject a fake module into sys.modules ---
    # TODO: Create a types.ModuleType("fake_database")
    # TODO: Add .connect = lambda: "Connected to fake DB"
    # TODO: Add .query = lambda sql: f"Results for: {sql}"
    # TODO: Register in sys.modules and verify you can import it
    pass

    # TODO: Clean up fake_database from sys.modules
    pass

    # --- __import__() -- the built-in behind 'import' ---
    # TODO: Use __import__("json") and verify it returns the same object
    # HINT: json2 = __import__("json"); assert json2 is json_mod
    pass

    # TODO: Use __import__("os.path", fromlist=["path"]) for submodules
    pass


# ===========================================================================
# SECTION 3: __all__ and Controlled Exports
# ===========================================================================

def demo_all_exports():
    """Demonstrate __all__ for controlling public API."""

    # --- Create a module with __all__ ---
    # TODO: Create types.ModuleType("mathlib")
    # TODO: Set __all__ = ["add", "subtract", "PI"]
    # TODO: Add public functions: add, subtract, and PI constant
    # TODO: Add internal items: _validate, multiply, _INTERNAL_CONST
    # HINT: mathlib.add = lambda a, b: a + b
    pass

    # TODO: Register in sys.modules
    pass

    # TODO: Print the public API (__all__) vs all attributes
    # TODO: Show that multiply is accessible even though not in __all__
    # HINT: __all__ controls star-imports, not direct access
    pass

    # --- @public decorator pattern ---
    # TODO: Create a list registry_all = []
    # TODO: Write a @public decorator that appends func.__name__ to registry_all
    # TODO: Decorate two functions and verify registry_all has their names
    # HINT: def public(func): registry_all.append(func.__name__); return func
    pass

    # TODO: Clean up mathlib from sys.modules
    pass


# ===========================================================================
# SECTION 4: Lazy Imports
# ===========================================================================

def demo_lazy_imports():
    """Demonstrate lazy module loading patterns."""

    # --- Pattern 1: LazyModule wrapper ---
    class LazyModule:
        """Proxy that imports a module on first attribute access.

        Requirements:
        - Store module_name, but don't import yet
        - On first __getattr__ call, import the module
        - Cache the module so subsequent accesses don't re-import
        - Track access count
        - __repr__ should show loaded/not-loaded status
        """

        def __init__(self, module_name: str):
            # TODO: Store module_name, _module (None), _access_count (0)
            # HINT: Use object.__setattr__ to avoid triggering __getattr__
            pass

        def _load(self):
            # TODO: If _module is None, import it with importlib.import_module
            # TODO: Cache the result and return it
            # HINT: object.__getattribute__(self, "_module") to read without triggering __getattr__
            pass

        def __getattr__(self, name):
            # TODO: Increment _access_count
            # TODO: Return getattr(self._load(), name)
            pass

        def __repr__(self):
            # TODO: Show module name, loaded/not-loaded status, access count
            pass

    # TODO: Create LazyModule("json") and LazyModule("math")
    # TODO: Print their repr BEFORE any use (should show "not loaded")
    # TODO: Call lazy_json.dumps({"key": "value"}) -- triggers import
    # TODO: Print repr AFTER use (should show "loaded")
    # TODO: Access lazy_math.pi
    # TODO: Verify multiple accesses increment count but don't re-import
    pass

    # --- Pattern 2: Module __getattr__ (PEP 562) ---
    # TODO: Simulate module-level __getattr__ using a dict namespace
    # TODO: Create a lookup dict mapping names to real module names
    # TODO: Write a function that imports on first access and caches
    # HINT: See PEP 562 for the pattern
    pass


# ===========================================================================
# SECTION 5: Import Hooks (Custom Finders & Loaders)
# ===========================================================================

def demo_import_hooks():
    """Build custom meta path finders and loaders."""

    # --- Show the default meta_path finders ---
    print("  Default sys.meta_path finders:")
    for i, finder in enumerate(sys.meta_path):
        print(f"    [{i}] {type(finder).__name__}")

    # --- Custom finder: generate modules from a config dict ---
    class ConfigModuleLoader(importlib.abc.Loader):
        """Loader that populates modules from a config dict.

        Implement:
        - __init__(self, configs: dict) -- store the config dict
        - create_module(self, spec) -- return None (use default creation)
        - exec_module(self, module) -- populate module attrs from config
        """

        def __init__(self, configs: dict):
            # TODO: Store the configs dict
            pass

        def create_module(self, spec):
            # TODO: Return None to use default module creation
            pass

        def exec_module(self, module):
            # TODO: Get config for module.__name__ from self._configs
            # TODO: Loop over config items and setattr on module
            # HINT: for key, value in config.items(): setattr(module, key, value)
            pass

    class ConfigModuleFinder(importlib.abc.MetaPathFinder):
        """Import hook that finds modules from config data.

        Implement:
        - __init__(self, configs) -- store configs and create loader
        - find_spec(self, fullname, path, target=None) -- return ModuleSpec if found
        """

        def __init__(self, configs: dict):
            # TODO: Store configs and create ConfigModuleLoader
            pass

        def find_spec(self, fullname, path, target=None):
            # TODO: If fullname in configs, return ModuleSpec(fullname, loader, origin=...)
            # HINT: importlib.machinery.ModuleSpec(fullname, self._loader, origin=f"<config:{fullname}>")
            # TODO: Return None if not found
            pass

    configs = {
        "app_settings": {
            "DEBUG": True,
            "VERSION": "1.0.0",
            "MAX_RETRIES": 3,
            "get_all": lambda: {k: v for k, v in configs["app_settings"].items()
                                if k.isupper()},
        },
        "db_config": {
            "HOST": "localhost",
            "PORT": 5432,
            "DATABASE": "myapp",
            "connection_string": lambda: "postgresql://localhost:5432/myapp",
        },
    }

    # TODO: Create ConfigModuleFinder and insert into sys.meta_path
    # HINT: sys.meta_path.insert(0, finder)
    pass

    # TODO: Import app_settings and db_config using importlib.import_module()
    # TODO: Verify app_settings.DEBUG is True, VERSION is "1.0.0"
    # TODO: Verify db_config.PORT == 5432
    # TODO: Print connection_string()
    # HINT: app_settings = importlib.import_module("app_settings")
    pass

    # --- Custom finder: prefix-based auto-generator ---
    class AutoModuleLoader(importlib.abc.Loader):
        """Loader that auto-generates module content from the name.

        Implement:
        - create_module(self, spec) -- return None
        - exec_module(self, module) -- set name, describe(), data from suffix
        """

        def create_module(self, spec):
            # TODO: Return None to use default module creation
            pass

        def exec_module(self, module):
            # TODO: Get suffix by removing "auto_" prefix from module.__name__
            # TODO: Set module.name = suffix
            # TODO: Set module.describe = lambda s=suffix: f"Auto-generated module: {s}"
            # TODO: Set module.data = {f"{suffix}_key": f"{suffix}_value"}
            # HINT: Use default arg (s=suffix) in lambda to capture suffix value
            pass

    class AutoModuleFinder(importlib.abc.MetaPathFinder):
        """Generates modules for any import starting with 'auto_'.

        Implement:
        - find_spec: match names starting with "auto_", return ModuleSpec
        """

        def __init__(self):
            # TODO: Create AutoModuleLoader instance
            pass

        def find_spec(self, fullname, path, target=None):
            # TODO: If fullname starts with "auto_", return ModuleSpec
            # HINT: importlib.machinery.ModuleSpec(fullname, self._loader, origin=...)
            pass

    # TODO: Register AutoModuleFinder in sys.meta_path
    # TODO: Import auto_users and auto_products using importlib.import_module()
    # TODO: Verify auto_users.name == "users"
    # TODO: Verify auto_products.data == {"products_key": "products_value"}
    pass

    # TODO: Clean up -- remove finders from sys.meta_path
    # TODO: Remove all fake modules from sys.modules
    # HINT: sys.meta_path.remove(finder); del sys.modules["app_settings"]
    pass

    print("  All import hooks cleaned up")


# ===========================================================================
# SECTION 6: Circular Imports
# ===========================================================================

def demo_circular_imports():
    """Demonstrate circular import problems and solutions."""

    # --- Simulate the circular import problem ---
    # TODO: Create two modules: circ_a and circ_b using types.ModuleType
    # TODO: Set circ_a.VALUE_A = 42 (partially initialized)
    # TODO: Register both in sys.modules
    pass

    # TODO: Try to access circ_a.func_a (should raise AttributeError)
    # TODO: Catch the error and print the message
    # HINT: mod_a hasn't defined func_a yet -- simulates partial initialization
    pass

    # TODO: Now add func_a to mod_a and show it works
    # HINT: mod_a.func_a = lambda: "I exist now!"
    pass

    # --- Solution 1: Import at function level ---
    print("\n  Solution 1: Defer imports to function level")

    # TODO: Create sol1_x and sol1_y modules
    # TODO: x_process() should access sol1_y at call time (not import time)
    # TODO: y_helper() returns "Helper result from Y"
    # TODO: Verify x.process() calls y.helper() successfully
    # HINT: def x_process(): y = sys.modules["sol1_y"]; return y.helper()
    pass

    # --- Solution 2: Import module, not names ---
    print("\n  Solution 2: Import the module object, not individual names")
    print("    'import other' works even if other is incomplete")
    print("    'from other import X' fails if X isn't defined yet")

    # --- Solution 3: Extract shared code ---
    print("\n  Solution 3: Extract shared code into a third module")

    # TODO: Create a "common" module with shared_util = lambda x: x * 2
    # TODO: Create mod_p and mod_q that both use common instead of each other
    # TODO: mod_p.process(x) = common.shared_util(x) + 1
    # TODO: mod_q.process(x) = common.shared_util(x) + 2
    # TODO: Verify mod_p.process(5) == 11 and mod_q.process(5) == 12
    pass

    # --- Solution 4: TYPE_CHECKING guard ---
    print("\n  Solution 4: TYPE_CHECKING guard for type hints")
    print("    from __future__ import annotations")
    print("    from typing import TYPE_CHECKING")
    print("    if TYPE_CHECKING:")
    print("        from other_module import SomeClass  # never runs!")
    print("    This import only runs during static analysis, not at runtime")

    # TODO: Clean up all simulated modules from sys.modules
    # HINT: sys.modules.pop(name, None) for each module name
    pass


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: Module Attributes ---
    print("--- Section 1: Module Attributes ---")
    demo_module_attributes()
    print()

    # --- Section 2: sys.modules & importlib ---
    print("--- Section 2: sys.modules Cache & importlib ---")
    demo_sys_modules_and_importlib()
    print()

    # --- Section 3: __all__ & Exports ---
    print("--- Section 3: __all__ and Controlled Exports ---")
    demo_all_exports()
    print()

    # --- Section 4: Lazy Imports ---
    print("--- Section 4: Lazy Imports ---")
    demo_lazy_imports()
    print()

    # --- Section 5: Import Hooks ---
    print("--- Section 5: Import Hooks (Custom Finders & Loaders) ---")
    demo_import_hooks()
    print()

    # --- Section 6: Circular Imports ---
    print("--- Section 6: Circular Imports ---")
    demo_circular_imports()
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Python's import system is fully customizable:")
    print("  - sys.modules caches all imported modules (it's just a dict)")
    print("  - importlib.import_module() for dynamic imports by string name")
    print("  - __all__ controls 'from module import *' exports")
    print("  - LazyModule pattern defers imports until first use")
    print("  - Import hooks (sys.meta_path) let you import from anywhere")
    print("  - Circular imports = tight coupling; refactor to fix")
    print("  - Module attributes (__name__, __file__, __package__) reveal context")
    print()
    print("All 6 sections passed. Import system mastered!")
