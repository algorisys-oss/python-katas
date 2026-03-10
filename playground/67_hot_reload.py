"""
Kata 67 -- Hot Reload
Run: python playground/67_hot_reload.py

Build a file watcher that detects changes using os.stat() polling.
A Reloader class watches directories, detects file modifications,
and triggers callbacks. Demonstrates how dev servers restart on
code changes -- using simulated file changes (no long-running watcher).

Completes within 5 seconds.
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Callable


# ===========================================================================
# SECTION 1: File Change Detection
# ===========================================================================
# The simplest change detection: poll os.stat() for mtime changes.
# This is how many dev servers (Flask, Django) detect code changes.

class FileSnapshot:
    """A snapshot of a file's modification time."""

    def __init__(self, path: str):
        self.path = path
        self.mtime = self._get_mtime()

    def _get_mtime(self) -> float:
        """Get file modification time, or 0.0 if file doesn't exist."""
        try:
            return os.stat(self.path).st_mtime
        except OSError:
            return 0.0

    def has_changed(self) -> bool:
        """Check if the file has been modified since the snapshot."""
        current_mtime = self._get_mtime()
        if current_mtime != self.mtime:
            self.mtime = current_mtime
            return True
        return False

    def __repr__(self) -> str:
        return f"FileSnapshot(path={self.path!r}, mtime={self.mtime:.2f})"


# ===========================================================================
# SECTION 2: Directory Scanner
# ===========================================================================
# Scan a directory tree for Python files and track their mtimes.

class DirectoryScanner:
    """Scan a directory for files matching a pattern."""

    def __init__(
        self,
        root: str,
        extensions: tuple[str, ...] = (".py",),
        exclude_dirs: tuple[str, ...] = ("__pycache__", ".git", "node_modules"),
    ):
        self.root = root
        self.extensions = extensions
        self.exclude_dirs = exclude_dirs

    def scan(self) -> dict[str, float]:
        """Return a dict of {filepath: mtime} for all matching files."""
        result: dict[str, float] = {}
        for dirpath, dirnames, filenames in os.walk(self.root):
            # Filter out excluded directories (modifying in-place skips them)
            dirnames[:] = [
                d for d in dirnames if d not in self.exclude_dirs
            ]
            for filename in filenames:
                if any(filename.endswith(ext) for ext in self.extensions):
                    filepath = os.path.join(dirpath, filename)
                    try:
                        result[filepath] = os.stat(filepath).st_mtime
                    except OSError:
                        continue
        return result


# ===========================================================================
# SECTION 3: Reloader
# ===========================================================================
# The Reloader watches directories, detects changes (new, modified,
# deleted files), and triggers callbacks.

class ChangeEvent:
    """Represents a file change event."""

    def __init__(self, path: str, change_type: str):
        self.path = path
        self.change_type = change_type  # "modified", "created", "deleted"

    def __repr__(self) -> str:
        return f"ChangeEvent({self.change_type!r}, {self.path!r})"


# Type alias for change callback
ChangeCallback = Callable[[list[ChangeEvent]], None]


class Reloader:
    """Watches directories for file changes and triggers callbacks.

    This is a polling-based reloader similar to what Flask and Django use.
    It periodically scans directories and compares mtimes to detect changes.

    In production, you'd use `watchfiles` (which uses OS-level file system
    notifications: inotify on Linux, FSEvents on macOS) for efficiency.
    """

    def __init__(self, poll_interval: float = 1.0):
        self.poll_interval = poll_interval
        self._watch_dirs: list[str] = []
        self._scanner: DirectoryScanner | None = None
        self._snapshots: dict[str, float] = {}
        self._callbacks: list[ChangeCallback] = []
        self._extensions: tuple[str, ...] = (".py",)

    def watch(self, directory: str, extensions: tuple[str, ...] = (".py",)) -> None:
        """Add a directory to watch."""
        self._watch_dirs.append(directory)
        self._extensions = extensions

    def on_change(self, callback: ChangeCallback) -> None:
        """Register a callback for file changes."""
        self._callbacks.append(callback)

    def take_snapshot(self) -> dict[str, float]:
        """Scan all watched directories and return current file states."""
        all_files: dict[str, float] = {}
        for directory in self._watch_dirs:
            scanner = DirectoryScanner(directory, self._extensions)
            all_files.update(scanner.scan())
        return all_files

    def check_changes(self) -> list[ChangeEvent]:
        """Compare current state to snapshot, return list of changes.

        Detects three types of changes:
        - modified: file exists in both snapshots but mtime differs
        - created: file exists now but not in previous snapshot
        - deleted: file existed before but not now
        """
        current = self.take_snapshot()
        events: list[ChangeEvent] = []

        # Check for modified and created files
        for path, mtime in current.items():
            if path not in self._snapshots:
                events.append(ChangeEvent(path, "created"))
            elif mtime != self._snapshots[path]:
                events.append(ChangeEvent(path, "modified"))

        # Check for deleted files
        for path in self._snapshots:
            if path not in current:
                events.append(ChangeEvent(path, "deleted"))

        # Update snapshot
        self._snapshots = current
        return events

    def notify(self, events: list[ChangeEvent]) -> None:
        """Call all registered callbacks with the change events."""
        for callback in self._callbacks:
            callback(events)

    def initialize(self) -> None:
        """Take the initial snapshot (no events fired)."""
        self._snapshots = self.take_snapshot()


# ===========================================================================
# SECTION 4: Dev Server Simulator
# ===========================================================================
# Show how a dev server would use the Reloader to restart on changes.

class DevServer:
    """Simulated dev server that restarts on code changes.

    In a real framework, this would:
    1. Start the server process
    2. Watch for file changes
    3. Kill and restart the server on changes

    We simulate this without actually running a server.
    """

    def __init__(self, app_dir: str):
        self.app_dir = app_dir
        self.reloader = Reloader(poll_interval=0.5)
        self.restart_count = 0
        self.change_log: list[str] = []

        # Set up watching
        self.reloader.watch(app_dir)
        self.reloader.on_change(self._handle_changes)

    def _handle_changes(self, events: list[ChangeEvent]) -> None:
        """Handle detected file changes."""
        for event in events:
            filename = os.path.basename(event.path)
            msg = f"  [{event.change_type.upper()}] {filename}"
            self.change_log.append(msg)
            print(msg)

        self.restart_count += 1
        print(f"  -> Server restarting... (restart #{self.restart_count})")

    def start(self) -> None:
        """Initialize the reloader (take first snapshot)."""
        self.reloader.initialize()
        print(f"  Dev server watching: {self.app_dir}")
        print(f"  Tracking {len(self.reloader._snapshots)} file(s)")

    def check(self) -> list[ChangeEvent]:
        """Check for changes and trigger callbacks if any found."""
        events = self.reloader.check_changes()
        if events:
            self.reloader.notify(events)
        return events


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_file_snapshot():
    """Show basic file change detection with FileSnapshot."""
    print("--- Section 1: File Change Detection ---")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("# original content\n")
        temp_path = f.name

    try:
        snapshot = FileSnapshot(temp_path)
        print(f"  Created snapshot: {snapshot}")

        # No changes yet
        assert not snapshot.has_changed()
        print(f"  has_changed() = False (no modification)")

        # Modify the file -- need to ensure mtime actually changes
        time.sleep(0.05)
        with open(temp_path, "w") as f:
            f.write("# modified content\n")
        # Force a different mtime by using os.utime
        os.utime(temp_path, (time.time() + 1, time.time() + 1))

        assert snapshot.has_changed()
        print(f"  has_changed() = True (file was modified)")

        # After detecting change, snapshot is updated
        assert not snapshot.has_changed()
        print(f"  has_changed() = False (snapshot updated)")

    finally:
        os.unlink(temp_path)

    # Non-existent file
    snapshot2 = FileSnapshot("/tmp/nonexistent_file.py")
    assert snapshot2.mtime == 0.0
    print(f"  Non-existent file: mtime=0.0")

    print("  [PASS] File change detection works")


def demo_directory_scanner():
    """Show directory scanning for Python files."""
    print("\n--- Section 2: Directory Scanner ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a project structure
        os.makedirs(os.path.join(tmpdir, "app"))
        os.makedirs(os.path.join(tmpdir, "app", "routes"))
        os.makedirs(os.path.join(tmpdir, "__pycache__"))

        files = [
            "app/main.py",
            "app/models.py",
            "app/routes/users.py",
            "app/routes/posts.py",
            "app/config.json",          # Not .py -- should be excluded
            "__pycache__/main.cpython-312.pyc",  # Excluded directory
        ]
        for f in files:
            path = os.path.join(tmpdir, f)
            with open(path, "w") as fh:
                fh.write(f"# {f}\n")

        scanner = DirectoryScanner(tmpdir)
        result = scanner.scan()

        print(f"  Scanned {tmpdir}")
        print(f"  Found {len(result)} Python files:")
        for path in sorted(result.keys()):
            relpath = os.path.relpath(path, tmpdir)
            print(f"    {relpath}")

        # Should find 4 .py files (not .json, not __pycache__)
        assert len(result) == 4
        basenames = {os.path.basename(p) for p in result}
        assert "main.py" in basenames
        assert "models.py" in basenames
        assert "users.py" in basenames
        assert "posts.py" in basenames
        assert "config.json" not in basenames

    print("  [PASS] Directory scanner works")


def demo_reloader():
    """Show the Reloader detecting file changes."""
    print("\n--- Section 3: Reloader ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create initial files
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("# main app\n")
        with open(os.path.join(tmpdir, "models.py"), "w") as f:
            f.write("# models\n")

        reloader = Reloader()
        reloader.watch(tmpdir)

        # Collect events for testing
        collected_events: list[ChangeEvent] = []
        reloader.on_change(lambda events: collected_events.extend(events))

        # Initialize snapshot
        reloader.initialize()
        print(f"  Initial snapshot: {len(reloader._snapshots)} files")
        assert len(reloader._snapshots) == 2

        # No changes yet
        events = reloader.check_changes()
        assert len(events) == 0
        print(f"  No changes detected (as expected)")

        # Modify a file
        time.sleep(0.05)
        with open(os.path.join(tmpdir, "app.py"), "w") as f:
            f.write("# modified app\n")
        os.utime(os.path.join(tmpdir, "app.py"),
                  (time.time() + 1, time.time() + 1))

        events = reloader.check_changes()
        assert len(events) == 1
        assert events[0].change_type == "modified"
        print(f"  Detected: {events[0]}")

        # Create a new file
        with open(os.path.join(tmpdir, "routes.py"), "w") as f:
            f.write("# routes\n")

        events = reloader.check_changes()
        assert len(events) == 1
        assert events[0].change_type == "created"
        print(f"  Detected: {events[0]}")

        # Delete a file
        os.unlink(os.path.join(tmpdir, "models.py"))

        events = reloader.check_changes()
        assert len(events) == 1
        assert events[0].change_type == "deleted"
        print(f"  Detected: {events[0]}")

        # Notify callbacks
        reloader.notify(events)
        assert len(collected_events) > 0
        print(f"  Callbacks notified: {len(collected_events)} total events")

    print("  [PASS] Reloader works")


def demo_dev_server():
    """Show how a dev server uses the Reloader."""
    print("\n--- Section 4: Dev Server Simulation ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake project
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("from ignite import Ignite\napp = Ignite()\n")
        with open(os.path.join(tmpdir, "routes.py"), "w") as f:
            f.write("@app.get('/users')\ndef users(): ...\n")

        server = DevServer(tmpdir)
        server.start()

        # Simulate editing a file
        print("\n  [Simulating: developer edits routes.py]")
        time.sleep(0.05)
        with open(os.path.join(tmpdir, "routes.py"), "w") as f:
            f.write("@app.get('/users')\ndef users(): return []\n")
        os.utime(os.path.join(tmpdir, "routes.py"),
                  (time.time() + 1, time.time() + 1))

        events = server.check()
        assert len(events) == 1
        assert server.restart_count == 1

        # Simulate adding a new file
        print("\n  [Simulating: developer creates models.py]")
        with open(os.path.join(tmpdir, "models.py"), "w") as f:
            f.write("class User: ...\n")

        events = server.check()
        assert len(events) == 1
        assert server.restart_count == 2

        # Simulate multiple changes at once
        print("\n  [Simulating: developer modifies two files]")
        time.sleep(0.05)
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("from ignite import Ignite\napp = Ignite(debug=True)\n")
        os.utime(os.path.join(tmpdir, "main.py"),
                  (time.time() + 2, time.time() + 2))
        with open(os.path.join(tmpdir, "routes.py"), "w") as f:
            f.write("@app.get('/users')\ndef users(): return ['alice']\n")
        os.utime(os.path.join(tmpdir, "routes.py"),
                  (time.time() + 2, time.time() + 2))

        events = server.check()
        assert len(events) == 2
        assert server.restart_count == 3

        print(f"\n  Total restarts: {server.restart_count}")
        print(f"  Change log entries: {len(server.change_log)}")

    print("  [PASS] Dev server simulation works")


def demo_watchfiles_comparison():
    """Compare polling vs OS-level file watching."""
    print("\n--- Section 5: Polling vs watchfiles ---")

    print("  Our Reloader uses POLLING (os.stat):")
    print("    + Simple, cross-platform, no dependencies")
    print("    + Works everywhere Python runs")
    print("    - CPU overhead (constant stat() calls)")
    print("    - Latency depends on poll interval")
    print("    - Misses rapid changes between polls")
    print()
    print("  Production alternative: watchfiles (pip install watchfiles)")
    print("    + Uses OS-level notifications (inotify/FSEvents/kqueue)")
    print("    + Near-zero CPU overhead")
    print("    + Instant detection")
    print("    - External dependency (Rust extension)")
    print()
    print("  Usage comparison:")
    print("    # Polling (our implementation):")
    print("    reloader = Reloader(poll_interval=0.5)")
    print("    reloader.watch('./app')")
    print("    reloader.on_change(restart_server)")
    print()
    print("    # watchfiles:")
    print("    # from watchfiles import watch")
    print("    # for changes in watch('./app'):")
    print("    #     restart_server(changes)")

    print("  [PASS] Comparison complete")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_file_snapshot()
    demo_directory_scanner()
    demo_reloader()
    demo_dev_server()
    demo_watchfiles_comparison()

    print("\n--- Summary ---")
    print("Hot reload gives our Ignite framework:")
    print("  - FileSnapshot for tracking individual file changes")
    print("  - DirectoryScanner for finding Python files in a tree")
    print("  - Reloader that detects created, modified, and deleted files")
    print("  - DevServer that triggers restarts on code changes")
    print("  - Polling-based approach (production uses watchfiles)")
    print("\nAll 5 sections passed. Hot reload mastered!")
    print("Next up: Kata 68 -- debug error page!")


if __name__ == "__main__":
    main()
