"""
Kata 35 -- Packaging & Distribution
Run: python playground/skeletons/35_packaging.py

Explore Python packaging: pyproject.toml anatomy, package structure,
entry points (console_scripts), version management, and the build/publish
pipeline. All concepts demonstrated programmatically without actually
building or publishing packages.

Completes within 5 seconds.
"""

import importlib
import importlib.metadata
import re
import sys
import tomllib
from pathlib import PurePosixPath
from typing import Any


# ===========================================================================
# SECTION 1: pyproject.toml Anatomy
# ===========================================================================

SAMPLE_PYPROJECT = """\
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

REQUIRED_PROJECT_FIELDS = {"name", "version"}


def parse_pyproject(toml_string: str) -> dict[str, Any]:
    """Parse a pyproject.toml string and return the config dict.

    Use the tomllib module (Python 3.11+) to parse TOML.
    """
    # TODO: Parse the TOML string using tomllib.loads()
    # HINT: tomllib.loads() takes a string and returns a dict
    pass


def validate_pyproject(config: dict[str, Any]) -> list[str]:
    """Validate a parsed pyproject.toml config.

    Returns a list of error messages (empty = valid).

    Check for:
    - [build-system] table with 'requires' and 'build-backend'
    - [project] table with all REQUIRED_PROJECT_FIELDS
    """
    errors = []

    # TODO: Check that 'build-system' key exists in config
    # TODO: If it exists, check for 'requires' and 'build-backend' sub-keys
    # HINT: Append error messages to the errors list for missing keys

    # TODO: Check that 'project' key exists in config
    # TODO: If it exists, check for each field in REQUIRED_PROJECT_FIELDS
    # HINT: for field in REQUIRED_PROJECT_FIELDS: ...

    return errors


def demo_pyproject_anatomy():
    """Parse and inspect a pyproject.toml file."""
    config = parse_pyproject(SAMPLE_PYPROJECT)
    errors = validate_pyproject(config)

    project = config["project"]
    build = config["build-system"]

    print(f"  Parsed pyproject.toml successfully")
    print(f"  Package name: {project['name']}")
    print(f"  Version: {project['version']}")
    print(f"  Build backend: {build['build-backend']}")
    print(f"  Requires Python: {project['requires-python']}")
    print(f"  Dependencies: {project['dependencies']} (zero external deps for core)")
    print(f"  Dev dependencies: {project['optional-dependencies']['dev']}")
    print(f"  Entry point: ignite -> {project['scripts']['ignite']}")

    assert not errors, f"Validation errors: {errors}"
    assert project["name"] == "ignite-framework"
    assert project["version"] == "0.1.0"
    assert build["build-backend"] == "setuptools.build_meta"
    assert project["requires-python"] == ">=3.12"
    assert project["dependencies"] == []
    assert "ignite" in project["scripts"]

    print(f"  [VALID] All required fields present")


# ===========================================================================
# SECTION 2: Package Structure Simulation
# ===========================================================================

class SimulatedFile:
    """Represents a file in a simulated package."""

    def __init__(self, name: str, exports: list[str] | None = None,
                 classes: list[str] | None = None,
                 functions: list[str] | None = None):
        self.name = name
        self.exports = exports or []
        self.classes = classes or []
        self.functions = functions or []

    def description(self) -> str:
        """Return a human-readable description of this file.

        Format: "name (exports: X, Y, classes: Z)" or just "name" if empty.
        """
        # TODO: Build a list of descriptive parts
        # HINT: Check self.exports, self.classes, self.functions
        # HINT: Join non-empty parts with ', ' and wrap in parentheses
        pass


class SimulatedPackage:
    """Represents a Python package directory."""

    def __init__(self, name: str):
        self.name = name
        self.files: list[SimulatedFile] = []
        self.sub_packages: list["SimulatedPackage"] = []

    def add_file(self, f: SimulatedFile) -> None:
        self.files.append(f)

    def add_sub_package(self, pkg: "SimulatedPackage") -> None:
        self.sub_packages.append(pkg)

    def file_count(self) -> int:
        """Count total files including sub-packages (recursive)."""
        # TODO: Count files in this package plus all sub-packages
        # HINT: Use recursion -- call file_count() on each sub-package
        pass

    def print_tree(self, indent: int = 2) -> None:
        """Print the package tree with indentation."""
        # TODO: Print this package name with trailing /
        # TODO: Print each file with description, indented further
        # TODO: Recursively print sub-packages with increased indent
        # HINT: prefix = " " * indent
        pass


def build_ignite_package() -> SimulatedPackage:
    """Build a simulated package structure for the Ignite framework.

    Create the following structure:
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
    """
    # TODO: Create the root SimulatedPackage("ignite")
    # TODO: Add __init__.py and app.py files to root
    # TODO: Create routing sub-package with its files
    # TODO: Create middleware sub-package with its files
    # TODO: Add sub-packages to root
    # HINT: Use SimulatedFile(name, exports=[...], classes=[...], functions=[...])
    pass


def demo_package_structure():
    """Simulate and display a Python package layout."""
    pkg = build_ignite_package()

    print("  Simulated package tree:")
    pkg.print_tree(indent=4)

    num_modules = 1 + len(pkg.sub_packages)
    num_sub_packages = len(pkg.sub_packages)
    num_files = pkg.file_count()

    print(f"  Total: {num_modules} modules, {num_sub_packages} sub-packages, "
          f"{num_files} files")

    assert num_files == 7
    assert num_sub_packages == 2

    print("  [VALID] Package structure is well-organized")


# ===========================================================================
# SECTION 3: Version Management
# ===========================================================================

# PEP 440 version pattern
PEP440_PATTERN = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)"
    r"(?(1)(\.dev\d+|a\d+|b\d+|rc\d+)?)"
    r"(\.post\d+)?"
    r"$"
)


def is_valid_pep440(version: str) -> bool:
    """Check if a version string conforms to PEP 440."""
    # TODO: Use PEP440_PATTERN.match() to check the version string
    # HINT: Return True if it matches, False otherwise
    pass


def bump_version(version: str, part: str = "patch") -> str:
    """Bump a semantic version string.

    Args:
        version: Current version (e.g., "0.1.0")
        part: Which part to bump -- "major", "minor", or "patch"

    Returns:
        New version string

    Examples:
        bump_version("0.1.0", "patch") -> "0.1.1"
        bump_version("0.1.0", "minor") -> "0.2.0"
        bump_version("0.1.0", "major") -> "1.0.0"
    """
    # TODO: Parse the version string into major, minor, patch integers
    # HINT: Use re.match(r"^(\d+)\.(\d+)\.(\d+)", version)

    # TODO: Increment the appropriate part and reset lower parts to 0
    # HINT: major bump -> (major+1).0.0, minor bump -> major.(minor+1).0

    # TODO: Return the new version as a formatted string
    pass


def demo_version_management():
    """Demonstrate version management strategies."""
    __version__ = "0.1.0"

    config = parse_pyproject(SAMPLE_PYPROJECT)
    toml_version = config["project"]["version"]

    print(f"  __version__ from module attribute: {__version__}")
    print(f"  Version from pyproject.toml: {toml_version}")
    print(f"  importlib.metadata available: {importlib.metadata is not None}")
    print(f"  Versions match: {__version__ == toml_version}")
    print(f"  PEP 440 valid version: {is_valid_pep440(__version__)}")

    assert __version__ == toml_version
    assert is_valid_pep440(__version__)

    assert bump_version("0.1.0", "patch") == "0.1.1"
    assert bump_version("0.1.0", "minor") == "0.2.0"
    assert bump_version("0.1.0", "major") == "1.0.0"
    assert bump_version("1.9.9", "minor") == "1.10.0"

    assert is_valid_pep440("1.0.0")
    assert is_valid_pep440("2.3.1")
    assert not is_valid_pep440("v1.0")
    assert not is_valid_pep440("latest")


# ===========================================================================
# SECTION 4: Entry Points & console_scripts
# ===========================================================================

def parse_entry_point(spec: str) -> tuple[str, str]:
    """Parse an entry point spec like 'ignite.cli:main'.

    Returns (module_path, function_name).

    Raises ValueError if the spec doesn't contain a colon.
    """
    # TODO: Split the spec on ':' to get module_path and function_name
    # HINT: Check if ':' is in spec first, raise ValueError if not
    pass


def simulate_cli(command: str, args: list[str]) -> str:
    """Simulate what happens when a console_script entry point is invoked.

    Commands:
    - "run" -> "Starting Ignite server on port {port}..." (default port 8000)
    - "init" -> "Creating new Ignite project..."
    - "routes" -> "Listing registered routes..."
    """
    # TODO: Handle each command and return the appropriate message
    # HINT: For "run", check if "--port" is in args and extract the port number
    pass


def demo_entry_points():
    """Demonstrate entry point parsing and CLI simulation."""
    config = parse_pyproject(SAMPLE_PYPROJECT)
    scripts = config["project"]["scripts"]

    for name, spec in scripts.items():
        print(f"  Entry point: {name} = {spec}")
        module_path, function_name = parse_entry_point(spec)
        print(f"  Parsed -> module={module_path}, function={function_name}")

        assert module_path == "ignite.cli"
        assert function_name == "main"

    for cmd, args in [("run", ["--port", "8000"]), ("init", []), ("routes", [])]:
        args_str = " ".join([cmd] + args)
        result = simulate_cli(cmd, args)
        print(f"  Simulated CLI: ignite {args_str}")
        assert result

    print("  [VALID] Entry points configured correctly")


# ===========================================================================
# SECTION 5: Build Pipeline Simulation
# ===========================================================================

def normalize_package_name(name: str) -> str:
    """Normalize package name per PEP 503.

    Replace hyphens, dots, and underscores with a single underscore, lowercase.
    Examples: "ignite-framework" -> "ignite_framework"
    """
    # TODO: Use re.sub() to replace [-_.]+ with underscore, then lowercase
    # HINT: re.sub(r"[-_.]+", "_", name).lower()
    pass


def make_wheel_filename(name: str, version: str, python: str = "py3",
                        abi: str = "none", platform: str = "any") -> str:
    """Generate a wheel filename following PEP 427.

    Format: {normalized_name}-{version}-{python}-{abi}-{platform}.whl
    """
    # TODO: Normalize the name and build the wheel filename
    # HINT: f"{normalized}-{version}-{python}-{abi}-{platform}.whl"
    pass


def make_sdist_filename(name: str, version: str) -> str:
    """Generate an sdist filename.

    Format: {normalized_name}-{version}.tar.gz
    """
    # TODO: Normalize the name and build the sdist filename
    pass


def parse_wheel_filename(filename: str) -> dict[str, str]:
    """Parse a wheel filename into its components.

    Returns dict with keys: name, version, python, abi, platform.
    """
    # TODO: Remove .whl extension, split on '-', return dict of components
    # HINT: base = filename.removesuffix(".whl"); parts = base.split("-")
    pass


def demo_build_pipeline():
    """Simulate the build and distribution pipeline."""
    config = parse_pyproject(SAMPLE_PYPROJECT)
    project = config["project"]
    build = config["build-system"]

    name = project["name"]
    version = project["version"]
    backend = build["build-backend"]

    print(f"  Build backend: {backend}")

    pkg = build_ignite_package()
    file_count = pkg.file_count()
    print(f"  Source files collected: {file_count} .py files")

    sdist_name = make_sdist_filename(name, version)
    wheel_name = make_wheel_filename(name, version)

    print(f"  sdist: {sdist_name}")
    print(f"  wheel:  {wheel_name}")

    wheel_parts = parse_wheel_filename(wheel_name)
    print(f"  Wheel filename anatomy:")
    print(f"    name={wheel_parts['name']}, version={wheel_parts['version']}")
    print(f"    python={wheel_parts['python']}, abi={wheel_parts['abi']}, "
          f"platform={wheel_parts['platform']}")

    assert sdist_name == "ignite_framework-0.1.0.tar.gz"
    assert wheel_name == "ignite_framework-0.1.0-py3-none-any.whl"
    assert wheel_parts["name"] == "ignite_framework"
    assert wheel_parts["version"] == "0.1.0"
    assert wheel_parts["python"] == "py3"
    assert wheel_parts["abi"] == "none"
    assert wheel_parts["platform"] == "any"

    reconstructed = make_wheel_filename(
        wheel_parts["name"], wheel_parts["version"],
        wheel_parts["python"], wheel_parts["abi"], wheel_parts["platform"])
    assert reconstructed == wheel_name

    print("  [VALID] Build artifacts would be correct")


# ===========================================================================
# DEMONSTRATIONS
# ===========================================================================

if __name__ == "__main__":

    # --- Section 1: pyproject.toml Anatomy ---
    print("--- Section 1: pyproject.toml Anatomy ---")
    try:
        demo_pyproject_anatomy()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 2: Package Structure ---
    print("--- Section 2: Package Structure Simulation ---")
    try:
        demo_package_structure()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 3: Version Management ---
    print("--- Section 3: Version Management ---")
    try:
        demo_version_management()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 4: Entry Points ---
    print("--- Section 4: Entry Points & console_scripts ---")
    try:
        demo_entry_points()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Section 5: Build Pipeline ---
    print("--- Section 5: Build Pipeline Simulation ---")
    try:
        demo_build_pipeline()
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")
    print()

    # --- Summary ---
    print("--- Summary ---")
    print("Packaging is the bridge between writing code and sharing it:")
    print("  - pyproject.toml is the single source of truth (PEP 518 + 621)")
    print("  - setuptools or hatchling as the build backend")
    print("  - __init__.py controls your package's public API")
    print("  - Entry points create CLI commands on install")
    print("  - Wheels are the modern distribution format")
    print("  - Test on TestPyPI before publishing to PyPI")
    print()
    print("All 5 sections passed. Packaging & distribution concepts mastered!")
    print("Next up: Kata 36 -- we start building the Ignite framework!")
