"""
Kata 35 -- Packaging & Distribution
Run: python playground/35_packaging.py

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
    """Parse a pyproject.toml string and return the config dict."""
    return tomllib.loads(toml_string)


def validate_pyproject(config: dict[str, Any]) -> list[str]:
    """Validate a parsed pyproject.toml config.

    Returns a list of error messages (empty = valid).
    """
    errors = []

    # Must have [build-system]
    if "build-system" not in config:
        errors.append("Missing [build-system] table")
    else:
        bs = config["build-system"]
        if "requires" not in bs:
            errors.append("Missing build-system.requires")
        if "build-backend" not in bs:
            errors.append("Missing build-system.build-backend")

    # Must have [project] with required fields
    if "project" not in config:
        errors.append("Missing [project] table")
    else:
        project = config["project"]
        for field in REQUIRED_PROJECT_FIELDS:
            if field not in project:
                errors.append(f"Missing project.{field}")

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
        parts = []
        if self.exports:
            parts.append(f"exports: {', '.join(self.exports)}")
        if self.classes:
            parts.append(f"classes: {', '.join(self.classes)}")
        if self.functions:
            parts.append(f"functions: {', '.join(self.functions)}")
        return f"{self.name} ({', '.join(parts)})" if parts else self.name


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
        total = len(self.files)
        for sub in self.sub_packages:
            total += sub.file_count()
        return total

    def print_tree(self, indent: int = 2) -> None:
        prefix = " " * indent
        print(f"{prefix}{self.name}/")
        for f in self.files:
            print(f"{prefix}  {f.description()}")
        for sub in self.sub_packages:
            sub.print_tree(indent + 2)


def build_ignite_package() -> SimulatedPackage:
    """Build a simulated package structure for the Ignite framework."""
    root = SimulatedPackage("ignite")
    root.add_file(SimulatedFile(
        "__init__.py", exports=["Ignite", "__version__"]))
    root.add_file(SimulatedFile(
        "app.py", classes=["Ignite"]))

    routing = SimulatedPackage("routing")
    routing.add_file(SimulatedFile(
        "__init__.py", exports=["Router", "route"]))
    routing.add_file(SimulatedFile(
        "router.py", classes=["Router"]))
    routing.add_file(SimulatedFile(
        "decorators.py", functions=["route", "get", "post"]))
    root.add_sub_package(routing)

    middleware = SimulatedPackage("middleware")
    middleware.add_file(SimulatedFile(
        "__init__.py", exports=["Middleware"]))
    middleware.add_file(SimulatedFile(
        "base.py", classes=["Middleware"]))
    root.add_sub_package(middleware)

    return root


def demo_package_structure():
    """Simulate and display a Python package layout."""
    pkg = build_ignite_package()

    print("  Simulated package tree:")
    pkg.print_tree(indent=4)

    num_modules = 1 + len(pkg.sub_packages)  # root + sub-packages as modules
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
    return PEP440_PATTERN.match(version) is not None


def bump_version(version: str, part: str = "patch") -> str:
    """Bump a semantic version string.

    Args:
        version: Current version (e.g., "0.1.0")
        part: Which part to bump -- "major", "minor", or "patch"

    Returns:
        New version string
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version: {version}")

    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Unknown part: {part} (use major, minor, or patch)")


def demo_version_management():
    """Demonstrate version management strategies."""
    # Simulate __version__ from module attribute
    __version__ = "0.1.0"

    # Read version from pyproject.toml
    config = parse_pyproject(SAMPLE_PYPROJECT)
    toml_version = config["project"]["version"]

    print(f"  __version__ from module attribute: {__version__}")
    print(f"  Version from pyproject.toml: {toml_version}")
    print(f"  importlib.metadata available: {importlib.metadata is not None}")
    print(f"  Versions match: {__version__ == toml_version}")
    print(f"  PEP 440 valid version: {is_valid_pep440(__version__)}")

    assert __version__ == toml_version
    assert is_valid_pep440(__version__)

    # Test version bumping
    assert bump_version("0.1.0", "patch") == "0.1.1"
    assert bump_version("0.1.0", "minor") == "0.2.0"
    assert bump_version("0.1.0", "major") == "1.0.0"
    assert bump_version("1.9.9", "minor") == "1.10.0"

    # Test PEP 440 compliance
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
    """
    if ":" not in spec:
        raise ValueError(f"Invalid entry point spec: {spec} (expected 'module:function')")
    module_path, function_name = spec.split(":", 1)
    return module_path, function_name


def simulate_cli(command: str, args: list[str]) -> str:
    """Simulate what happens when a console_script entry point is invoked."""
    if command == "run":
        port = 8000
        if "--port" in args:
            idx = args.index("--port")
            port = int(args[idx + 1])
        return f"Starting Ignite server on port {port}..."
    elif command == "init":
        return "Creating new Ignite project..."
    elif command == "routes":
        return "Listing registered routes..."
    else:
        return f"Unknown command: {command}"


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

    # Simulate CLI invocations
    for cmd, args in [("run", ["--port", "8000"]), ("init", []), ("routes", [])]:
        args_str = " ".join([cmd] + args)
        result = simulate_cli(cmd, args)
        print(f"  Simulated CLI: ignite {args_str}")
        assert result  # Non-empty response

    print("  [VALID] Entry points configured correctly")


# ===========================================================================
# SECTION 5: Build Pipeline Simulation
# ===========================================================================

def normalize_package_name(name: str) -> str:
    """Normalize package name per PEP 503 (replace hyphens/dots with underscores)."""
    return re.sub(r"[-_.]+", "_", name).lower()


def make_wheel_filename(name: str, version: str, python: str = "py3",
                        abi: str = "none", platform: str = "any") -> str:
    """Generate a wheel filename following PEP 427."""
    normalized = normalize_package_name(name)
    return f"{normalized}-{version}-{python}-{abi}-{platform}.whl"


def make_sdist_filename(name: str, version: str) -> str:
    """Generate an sdist filename."""
    normalized = normalize_package_name(name)
    return f"{normalized}-{version}.tar.gz"


def parse_wheel_filename(filename: str) -> dict[str, str]:
    """Parse a wheel filename into its components."""
    # Remove .whl extension
    base = filename.removesuffix(".whl")
    parts = base.split("-")
    if len(parts) < 5:
        raise ValueError(f"Invalid wheel filename: {filename}")
    return {
        "name": parts[0],
        "version": parts[1],
        "python": parts[2],
        "abi": parts[3],
        "platform": parts[4],
    }


def demo_build_pipeline():
    """Simulate the build and distribution pipeline."""
    config = parse_pyproject(SAMPLE_PYPROJECT)
    project = config["project"]
    build = config["build-system"]

    name = project["name"]
    version = project["version"]
    backend = build["build-backend"]

    print(f"  Build backend: {backend}")

    # Count source files from our simulated package
    pkg = build_ignite_package()
    file_count = pkg.file_count()
    print(f"  Source files collected: {file_count} .py files")

    # Generate artifact filenames
    sdist_name = make_sdist_filename(name, version)
    wheel_name = make_wheel_filename(name, version)

    print(f"  sdist: {sdist_name}")
    print(f"  wheel:  {wheel_name}")

    # Parse wheel filename back
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

    # Verify round-trip
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
    demo_pyproject_anatomy()
    print()

    # --- Section 2: Package Structure ---
    print("--- Section 2: Package Structure Simulation ---")
    demo_package_structure()
    print()

    # --- Section 3: Version Management ---
    print("--- Section 3: Version Management ---")
    demo_version_management()
    print()

    # --- Section 4: Entry Points ---
    print("--- Section 4: Entry Points & console_scripts ---")
    demo_entry_points()
    print()

    # --- Section 5: Build Pipeline ---
    print("--- Section 5: Build Pipeline Simulation ---")
    demo_build_pipeline()
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
