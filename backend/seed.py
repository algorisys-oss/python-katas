"""Seed the database with kata data from playground/ and tutorial/ files."""

import re
from pathlib import Path

from db import init_db, upsert_kata

PROJECT_ROOT = Path(__file__).parent.parent
PLAYGROUND_DIR = PROJECT_ROOT / "playground"
SKELETON_DIR = PLAYGROUND_DIR / "skeletons"
TUTORIAL_DIR = PROJECT_ROOT / "tutorial"

# Map kata number ranges to module names
MODULES = [
    (0, 10, "Pythonic Foundations"),
    (11, 20, "OOP & SOLID Principles"),
    (21, 30, "Concurrency & Parallelism"),
    (31, 35, "Advanced Language Features"),
    (36, 48, "HTTP Foundations (Ignite)"),
    (49, 53, "Decorator-Driven API Design"),
    (54, 57, "Data Layer"),
    (58, 61, "WebSocket Support"),
    (62, 66, "Security & Sessions"),
    (67, 72, "Developer Experience"),
    (73, 76, "Production"),
    (77, 78, "Capstone"),
    (79, 80, "Advanced HTTP"),
]


def get_module(number: int) -> str:
    for start, end, name in MODULES:
        if start <= number <= end:
            return name
    return "Unknown"


def title_from_filename(filename: str) -> str:
    """Extract a title from a filename like '01_python_data_model.py'."""
    name = filename.removesuffix(".py")
    # Remove leading number and underscore
    name = re.sub(r"^\d+_", "", name)
    return name.replace("_", " ").title()


def find_tutorial(number: int) -> str | None:
    """Find matching tutorial markdown file for a kata number."""
    pattern = f"{number:02d}-*.md"
    matches = list(TUTORIAL_DIR.glob(pattern))
    return str(matches[0].relative_to(PROJECT_ROOT)) if matches else None


def seed():
    init_db()
    count = 0

    for py_file in sorted(PLAYGROUND_DIR.glob("*.py")):
        match = re.match(r"^(\d+)", py_file.name)
        if not match:
            continue

        number = int(match.group(1))
        kata_id = py_file.stem  # e.g., "01_python_data_model"
        title = title_from_filename(py_file.name)
        module = get_module(number)
        code = py_file.read_text()
        tutorial_path = find_tutorial(number)

        # Look for a corresponding skeleton file
        skeleton_file = SKELETON_DIR / py_file.name
        skeleton_code = skeleton_file.read_text() if skeleton_file.exists() else code

        upsert_kata(kata_id, number, title, module, code, tutorial_path or "", skeleton_code=skeleton_code)
        count += 1
        print(f"  Seeded: {kata_id} ({module})")

    print(f"\nSeeded {count} katas.")


if __name__ == "__main__":
    seed()
