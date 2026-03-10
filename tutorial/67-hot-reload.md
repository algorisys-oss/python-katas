# Kata 67 -- Hot Reload

[prev: 66-authentication](./66-authentication.md) | [next: 68-debug-error-page](./68-debug-error-page.md)

---

## What We're Building

A **hot reload system** for our Ignite framework. When a developer edits code, the dev server detects the change and restarts automatically. We build three layers:

1. **FileSnapshot** -- detect single-file changes using `os.stat()` mtime polling
2. **DirectoryScanner** -- walk a directory tree and find all Python files
3. **Reloader** -- compare snapshots over time, detect created/modified/deleted files, and trigger restart callbacks

This is the same approach Flask and Django use in development mode. We also discuss `watchfiles` as the production-grade alternative.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `os.stat().st_mtime` | File modification timestamp | Detecting file changes |
| `os.walk()` | Recursive directory traversal | Scanning project trees |
| Polling-based watching | Periodic stat() checks | Simple file watching |
| Snapshot comparison | Diff old vs new file states | Detecting creates/deletes |
| Callback registration | Functions called on events | Decoupled change handling |
| `watchfiles` | OS-level file notifications | Production file watching |

## The Code

### 1. FileSnapshot

The simplest unit of change detection -- track one file's mtime:

```python
class FileSnapshot:
    def __init__(self, path):
        self.path = path
        self.mtime = self._get_mtime()

    def _get_mtime(self):
        try:
            return os.stat(self.path).st_mtime
        except OSError:
            return 0.0

    def has_changed(self):
        current_mtime = self._get_mtime()
        if current_mtime != self.mtime:
            self.mtime = current_mtime
            return True
        return False
```

### 2. DirectoryScanner

Walk a directory tree and collect all Python files with their mtimes:

```python
class DirectoryScanner:
    def __init__(self, root, extensions=(".py",), exclude_dirs=("__pycache__",)):
        self.root = root
        self.extensions = extensions
        self.exclude_dirs = exclude_dirs

    def scan(self):
        result = {}
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in self.exclude_dirs]
            for f in filenames:
                if any(f.endswith(ext) for ext in self.extensions):
                    path = os.path.join(dirpath, f)
                    result[path] = os.stat(path).st_mtime
        return result
```

Key trick: modifying `dirnames[:]` in-place tells `os.walk()` to skip those subdirectories.

### 3. Reloader

Compare snapshots to detect three types of changes:

```python
class Reloader:
    def check_changes(self):
        current = self.take_snapshot()
        events = []

        for path, mtime in current.items():
            if path not in self._snapshots:
                events.append(ChangeEvent(path, "created"))
            elif mtime != self._snapshots[path]:
                events.append(ChangeEvent(path, "modified"))

        for path in self._snapshots:
            if path not in current:
                events.append(ChangeEvent(path, "deleted"))

        self._snapshots = current
        return events
```

### 4. DevServer Integration

```python
class DevServer:
    def __init__(self, app_dir):
        self.reloader = Reloader()
        self.reloader.watch(app_dir)
        self.reloader.on_change(self._handle_changes)

    def _handle_changes(self, events):
        for event in events:
            print(f"[{event.change_type}] {event.path}")
        print("Server restarting...")

    def check(self):
        events = self.reloader.check_changes()
        if events:
            self.reloader.notify(events)
        return events
```

## Playground

```python
python playground/67_hot_reload.py
```

Expected output:

```
--- Section 1: File Change Detection ---
  Created snapshot: FileSnapshot(path='...', mtime=...)
  has_changed() = False (no modification)
  has_changed() = True (file was modified)
  has_changed() = False (snapshot updated)
  Non-existent file: mtime=0.0
  [PASS] File change detection works

--- Section 2: Directory Scanner ---
  Scanned /tmp/...
  Found 4 Python files:
    app/main.py
    app/models.py
    app/routes/posts.py
    app/routes/users.py
  [PASS] Directory scanner works

--- Section 3: Reloader ---
  Initial snapshot: 2 files
  No changes detected (as expected)
  Detected: ChangeEvent('modified', '...')
  Detected: ChangeEvent('created', '...')
  Detected: ChangeEvent('deleted', '...')
  Callbacks notified: ... total events
  [PASS] Reloader works

--- Section 4: Dev Server Simulation ---
  Dev server watching: /tmp/...
  Tracking 2 file(s)
  [Simulating: developer edits routes.py]
  [MODIFIED] routes.py
  -> Server restarting... (restart #1)
  [Simulating: developer creates models.py]
  [CREATED] models.py
  -> Server restarting... (restart #2)
  ...
  [PASS] Dev server simulation works
```

## How It Works

### Polling Loop

```
Start
  |
  v
Take initial snapshot (record all file mtimes)
  |
  v
+---> Sleep(poll_interval)
|       |
|       v
|     Take new snapshot
|       |
|       v
|     Compare: old snapshot vs new snapshot
|       |
|       +-- New files?     -> "created" events
|       +-- Changed mtime? -> "modified" events
|       +-- Missing files? -> "deleted" events
|       |
|       v
|     Any events? -> notify callbacks -> restart server
|       |
+-------+
```

### Polling vs OS Notifications

| Feature | Polling (our approach) | watchfiles |
|---|---|---|
| Mechanism | `os.stat()` loop | inotify / FSEvents / kqueue |
| CPU usage | Proportional to file count | Near zero |
| Latency | Up to `poll_interval` | Milliseconds |
| Dependencies | None (stdlib only) | Rust extension |
| Cross-platform | Yes | Yes (via Rust) |
| Reliability | May miss rapid changes | Catches everything |

## Exercises

1. **Add glob pattern filtering** -- extend the scanner to accept glob patterns like `"**/*.py"` or `"*.html"` instead of just extensions.

2. **Debounce rapid changes** -- if a developer saves multiple times quickly, batch the changes and only trigger one restart. Add a debounce delay (e.g., 200ms).

3. **Ignore patterns** -- add support for a `.reloadignore` file (similar to `.gitignore`) that lists patterns to skip during watching.

4. **Track change frequency** -- add statistics tracking: which files change most often, average time between changes, etc.

5. **Add graceful shutdown** -- when restarting, implement a grace period that lets in-flight requests finish before killing the server process.

## What's Next

With hot reload, developers get instant feedback when they edit code. In [Kata 68: Debug Error Page](./68-debug-error-page.md), we'll build a rich error page that shows tracebacks, local variables, and request context -- making debugging even faster.

---

[prev: 66-authentication](./66-authentication.md) | [next: 68-debug-error-page](./68-debug-error-page.md)
