"""
Kata 32 -- Import System & Modules
Run: python playground/32_import_system.py

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
    # When run as a script: __name__ == "__main__"
    # When imported: __name__ == module's dotted path
    print(f"  __name__ of this script: {__name__}")
    print(f"  __name__ of sys module:  {sys.__name__}")
    print(f"  __name__ of types:       {types.__name__}")

    # --- __file__: path to source file ---
    print(f"  __file__ of this script: {__file__}")
    # Some built-in modules have no __file__
    has_file = hasattr(sys, "__file__")
    print(f"  sys has __file__: {has_file}")

    # --- __package__: parent package name ---
    print(f"  __package__ of this script: {__package__!r}")
    print(f"  __package__ of json.decoder: {importlib.import_module('json.decoder').__package__}")

    # --- __spec__: ModuleSpec with full import metadata ---
    json_spec = importlib.import_module("json").__spec__
    print(f"  json __spec__.name: {json_spec.name}")
    print(f"  json __spec__.origin: {json_spec.origin}")

    # --- Create a dynamic module with attributes ---
    mod = types.ModuleType("my_dynamic_mod")
    mod.__file__ = "<dynamic>"
    mod.__package__ = ""
    mod.value = 99
    mod.greet = lambda name: f"Hello, {name}!"

    sys.modules["my_dynamic_mod"] = mod

    # Import the dynamic module
    my_dynamic_mod = importlib.import_module("my_dynamic_mod")
    assert my_dynamic_mod.value == 99
    assert my_dynamic_mod.greet("Python") == "Hello, Python!"
    print(f"  Dynamic module value: {my_dynamic_mod.value}")
    print(f"  Dynamic module greet: {my_dynamic_mod.greet('Python')}")

    # Clean up
    del sys.modules["my_dynamic_mod"]


# ===========================================================================
# SECTION 2: sys.modules Cache & importlib
# ===========================================================================

def demo_sys_modules_and_importlib():
    """Demonstrate the module cache and dynamic imports."""

    # --- sys.modules is a dict of all imported modules ---
    total_modules = len(sys.modules)
    print(f"  Total cached modules: {total_modules}")
    print(f"  'sys' in cache: {'sys' in sys.modules}")
    print(f"  'json' in cache: {'json' in sys.modules}")

    # --- importlib.import_module() for dynamic imports ---
    json_mod = importlib.import_module("json")
    print(f"  Dynamically imported: {json_mod.__name__}")
    print(f"  json.dumps([1,2]): {json_mod.dumps([1, 2])}")

    # Import submodule by dotted name
    os_path = importlib.import_module("os.path")
    print(f"  os.path.join('a','b'): {os_path.join('a', 'b')}")

    # --- Injecting a fake module into sys.modules ---
    fake_mod = types.ModuleType("fake_database")
    fake_mod.connect = lambda: "Connected to fake DB"
    fake_mod.query = lambda sql: f"Results for: {sql}"
    sys.modules["fake_database"] = fake_mod

    fake_database = importlib.import_module("fake_database")
    assert fake_database.connect() == "Connected to fake DB"
    assert fake_database.query("SELECT 1") == "Results for: SELECT 1"
    print(f"  Fake module connect: {fake_database.connect()}")
    print(f"  Fake module query: {fake_database.query('SELECT 1')}")

    del sys.modules["fake_database"]

    # --- __import__() -- the built-in behind 'import' ---
    json2 = __import__("json")
    assert json2 is json_mod  # Same cached object
    print(f"  __import__('json') is importlib result: {json2 is json_mod}")

    # For submodules, __import__ needs fromlist
    os_path2 = __import__("os.path", fromlist=["path"])
    assert os_path2 is os_path
    print(f"  __import__ with fromlist works: {os_path2 is os_path}")

    # --- importlib.reload() ---
    # Create a module, modify it, reload
    counter_mod = types.ModuleType("counter_mod")
    counter_mod.__file__ = "<test>"  # reload requires __file__
    counter_mod.__loader__ = type("L", (), {"load_module": staticmethod(lambda n: counter_mod)})()
    counter_mod.__spec__ = importlib.machinery.ModuleSpec("counter_mod", counter_mod.__loader__)
    counter_mod.count = 0
    sys.modules["counter_mod"] = counter_mod

    print(f"  Before modification: count = {counter_mod.count}")
    counter_mod.count = 42
    print(f"  After modification: count = {counter_mod.count}")
    # Note: reload() re-executes the module's code from disk.
    # For dynamically created modules, it calls the loader.
    print("  importlib.reload() re-executes module code from source")

    del sys.modules["counter_mod"]


# ===========================================================================
# SECTION 3: __all__ and Controlled Exports
# ===========================================================================

def demo_all_exports():
    """Demonstrate __all__ for controlling public API."""

    # --- Create a module with __all__ ---
    mathlib = types.ModuleType("mathlib")
    mathlib.__all__ = ["add", "subtract", "PI"]

    # Public API (in __all__)
    mathlib.add = lambda a, b: a + b
    mathlib.subtract = lambda a, b: a - b
    mathlib.PI = 3.14159

    # Internal / not in __all__
    mathlib._validate = lambda x: isinstance(x, (int, float))
    mathlib.multiply = lambda a, b: a * b  # exists but not exported
    mathlib._INTERNAL_CONST = 42

    sys.modules["mathlib"] = mathlib

    # __all__ controls what "from mathlib import *" would expose
    public_api = mathlib.__all__
    all_attrs = [a for a in dir(mathlib) if not a.startswith("__")]
    non_public = [a for a in all_attrs if a not in public_api]

    print(f"  __all__ (public API): {public_api}")
    print(f"  All attributes: {all_attrs}")
    print(f"  Not in __all__: {non_public}")
    print(f"  add(10, 20) = {mathlib.add(10, 20)}")
    print(f"  multiply still accessible: {mathlib.multiply(3, 4)}")
    print("  __all__ controls star-imports, not access!")

    # --- @public decorator pattern ---
    registry_all = []

    def public(func):
        """Decorator that auto-adds function name to __all__."""
        registry_all.append(func.__name__)
        return func

    @public
    def process_data(data):
        return sorted(data)

    @public
    def validate_input(value):
        return value is not None

    def _helper():  # Not decorated, stays private
        pass

    print(f"  Auto-built __all__: {registry_all}")
    assert registry_all == ["process_data", "validate_input"]

    del sys.modules["mathlib"]


# ===========================================================================
# SECTION 4: Lazy Imports
# ===========================================================================

def demo_lazy_imports():
    """Demonstrate lazy module loading patterns."""

    # --- Pattern 1: LazyModule wrapper ---
    class LazyModule:
        """Proxy that imports a module on first attribute access."""

        def __init__(self, module_name: str):
            # Use object.__setattr__ to avoid triggering __getattr__
            object.__setattr__(self, "_module_name", module_name)
            object.__setattr__(self, "_module", None)
            object.__setattr__(self, "_access_count", 0)

        def _load(self):
            mod = object.__getattribute__(self, "_module")
            if mod is None:
                name = object.__getattribute__(self, "_module_name")
                mod = importlib.import_module(name)
                object.__setattr__(self, "_module", mod)
            return mod

        def __getattr__(self, name):
            object.__setattr__(self, "_access_count",
                               object.__getattribute__(self, "_access_count") + 1)
            return getattr(self._load(), name)

        def __repr__(self):
            mod = object.__getattribute__(self, "_module")
            name = object.__getattribute__(self, "_module_name")
            count = object.__getattribute__(self, "_access_count")
            status = "loaded" if mod else "not loaded"
            return f"<LazyModule '{name}' ({status}, {count} accesses)>"

    lazy_json = LazyModule("json")
    lazy_math = LazyModule("math")

    print(f"  Before use: {lazy_json}")
    print(f"  Before use: {lazy_math}")

    # First access triggers import
    result = lazy_json.dumps({"key": "value"})
    print(f"  json.dumps result: {result}")
    print(f"  After use: {lazy_json}")

    pi = lazy_math.pi
    print(f"  math.pi: {pi}")
    print(f"  After use: {lazy_math}")

    # Multiple accesses don't re-import
    _ = lazy_json.loads('{"a": 1}')
    print(f"  After 2nd use: {lazy_json}")

    # --- Pattern 2: Module __getattr__ (PEP 562) ---
    # In a real module, you'd define this at module level:
    #
    # _lazy_imports = {
    #     "numpy": "numpy",
    #     "pandas": "pandas",
    # }
    #
    # def __getattr__(name):
    #     if name in _lazy_imports:
    #         mod = importlib.import_module(_lazy_imports[name])
    #         globals()[name] = mod
    #         return mod
    #     raise AttributeError(f"module has no attribute {name}")

    # Simulate module-level __getattr__
    lazy_ns = {"__loaded": {}}

    def module_getattr(name):
        registry = {"csv_mod": "csv", "io_mod": "io"}
        if name in registry:
            if name not in lazy_ns["__loaded"]:
                lazy_ns["__loaded"][name] = importlib.import_module(registry[name])
            return lazy_ns["__loaded"][name]
        raise AttributeError(f"no attribute {name}")

    csv = module_getattr("csv_mod")
    print(f"  PEP 562 lazy load: csv module = {csv.__name__}")
    assert "csv_mod" in lazy_ns["__loaded"]
    print("  Module cached after first access")


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
        """Loader that populates modules from a config dict."""

        def __init__(self, configs: dict):
            self._configs = configs

        def create_module(self, spec):
            return None  # Use default module creation

        def exec_module(self, module):
            config = self._configs[module.__name__]
            for key, value in config.items():
                setattr(module, key, value)

    class ConfigModuleFinder(importlib.abc.MetaPathFinder):
        """Import hook that creates modules from config data."""

        def __init__(self, configs: dict):
            self._configs = configs
            self._loader = ConfigModuleLoader(configs)

        def find_spec(self, fullname, path, target=None):
            if fullname in self._configs:
                return importlib.machinery.ModuleSpec(
                    fullname, self._loader,
                    origin=f"<config:{fullname}>",
                )
            return None

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

    finder = ConfigModuleFinder(configs)
    sys.meta_path.insert(0, finder)

    # Now import our virtual modules!
    app_settings = importlib.import_module("app_settings")
    db_config = importlib.import_module("db_config")

    print(f"  app_settings.DEBUG: {app_settings.DEBUG}")
    print(f"  app_settings.VERSION: {app_settings.VERSION}")
    print(f"  db_config.HOST: {db_config.HOST}")
    print(f"  db_config.connection_string(): {db_config.connection_string()}")

    assert app_settings.DEBUG is True
    assert app_settings.VERSION == "1.0.0"
    assert db_config.PORT == 5432

    # --- Custom finder: prefix-based module generator ---
    class AutoModuleLoader(importlib.abc.Loader):
        """Loader that auto-generates module content from the name."""

        def create_module(self, spec):
            return None  # Use default module creation

        def exec_module(self, module):
            suffix = module.__name__[5:]  # Remove "auto_" prefix
            module.name = suffix
            module.describe = lambda s=suffix: f"Auto-generated module: {s}"
            module.data = {f"{suffix}_key": f"{suffix}_value"}

    class AutoModuleFinder(importlib.abc.MetaPathFinder):
        """Generates modules for any import starting with 'auto_'."""

        def __init__(self):
            self._loader = AutoModuleLoader()

        def find_spec(self, fullname, path, target=None):
            if fullname.startswith("auto_"):
                return importlib.machinery.ModuleSpec(
                    fullname, self._loader,
                    origin=f"<auto:{fullname}>",
                )
            return None

    auto_finder = AutoModuleFinder()
    sys.meta_path.insert(0, auto_finder)

    auto_users = importlib.import_module("auto_users")
    auto_products = importlib.import_module("auto_products")

    print(f"  auto_users.describe(): {auto_users.describe()}")
    print(f"  auto_products.data: {auto_products.data}")

    assert auto_users.name == "users"
    assert auto_products.data == {"products_key": "products_value"}

    # Clean up all hooks and fake modules
    sys.meta_path.remove(finder)
    sys.meta_path.remove(auto_finder)
    for name in ["app_settings", "db_config", "auto_users", "auto_products"]:
        del sys.modules[name]

    print("  All import hooks cleaned up")


# ===========================================================================
# SECTION 6: Circular Imports
# ===========================================================================

def demo_circular_imports():
    """Demonstrate circular import problems and solutions."""

    # --- Simulate the circular import problem ---
    # Module A imports B, B imports A -- A is only partially initialized
    # when B tries to use it.

    mod_a = types.ModuleType("circ_a")
    mod_b = types.ModuleType("circ_b")

    # Simulate: A starts loading, defines some attributes
    mod_a.VALUE_A = 42
    # A is registered before it finishes (this is what Python does)
    sys.modules["circ_a"] = mod_a
    sys.modules["circ_b"] = mod_b

    # B tries to access an attribute that A hasn't defined yet
    try:
        _ = mod_a.func_a  # A hasn't defined func_a yet!
        print("  ERROR: Should not reach here")
    except AttributeError as e:
        print(f"  Circular import problem: {e}")
        print("  B tried to use A's 'func_a' before A finished loading")

    # Now A finishes loading and defines func_a
    mod_a.func_a = lambda: "I exist now!"
    print(f"  After A finishes: func_a() = {mod_a.func_a()}")

    # --- Solution 1: Import at function level ---
    print("\n  Solution 1: Defer imports to function level")

    mod_x = types.ModuleType("sol1_x")
    mod_y = types.ModuleType("sol1_y")

    def x_process():
        """Instead of top-level 'from sol1_y import helper',
        import inside the function."""
        y = sys.modules["sol1_y"]
        return y.helper()

    def y_helper():
        return "Helper result from Y"

    mod_x.process = x_process
    mod_y.helper = y_helper

    sys.modules["sol1_x"] = mod_x
    sys.modules["sol1_y"] = mod_y

    result = mod_x.process()
    print(f"    x.process() -> y.helper() = {result}")
    assert result == "Helper result from Y"

    # --- Solution 2: Import module, not names ---
    print("\n  Solution 2: Import the module object, not individual names")
    print("    'import other' works even if other is incomplete")
    print("    'from other import X' fails if X isn't defined yet")

    # --- Solution 3: Extract shared code ---
    print("\n  Solution 3: Extract shared code into a third module")

    common = types.ModuleType("common")
    common.shared_util = lambda x: x * 2
    sys.modules["common"] = common

    mod_p = types.ModuleType("mod_p")
    mod_q = types.ModuleType("mod_q")

    # Both use common instead of each other
    mod_p.process = lambda x: common.shared_util(x) + 1
    mod_q.process = lambda x: common.shared_util(x) + 2

    assert mod_p.process(5) == 11  # 5*2 + 1
    assert mod_q.process(5) == 12  # 5*2 + 2
    print(f"    mod_p.process(5) = {mod_p.process(5)}")
    print(f"    mod_q.process(5) = {mod_q.process(5)}")
    print("    No circular dependency -- both depend on 'common'")

    # --- Solution 4: TYPE_CHECKING guard ---
    print("\n  Solution 4: TYPE_CHECKING guard for type hints")
    print("    from __future__ import annotations")
    print("    from typing import TYPE_CHECKING")
    print("    if TYPE_CHECKING:")
    print("        from other_module import SomeClass  # never runs!")
    print("    This import only runs during static analysis, not at runtime")

    # --- Detection: find potential circular imports ---
    print("\n  Detecting import relationships:")
    # In real code, you'd inspect module __dict__ for module-type values
    test_modules = {"circ_a": mod_a, "circ_b": mod_b}
    for name, mod in test_modules.items():
        imported_modules = [
            attr_name for attr_name in dir(mod)
            if isinstance(getattr(mod, attr_name, None), types.ModuleType)
            and not attr_name.startswith("__")
        ]
        if imported_modules:
            print(f"    {name} imports: {imported_modules}")
        else:
            print(f"    {name}: no module-level imports detected")

    # Clean up
    for name in ["circ_a", "circ_b", "sol1_x", "sol1_y", "common"]:
        sys.modules.pop(name, None)


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
