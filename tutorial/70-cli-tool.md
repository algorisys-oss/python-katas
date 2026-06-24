# Kata 70 -- CLI Tool

[prev: 69-structured-logging](./69-structured-logging.md) | [next: 71-static-files](./71-static-files.md)

---

## What We're Building

The **Ignite CLI** using Python's `argparse` (no external dependencies like Click). We build three subcommands:

1. **`ignite run`** -- start the development server with host, port, reload, and worker options
2. **`ignite routes`** -- list registered routes in table, JSON, or plain format
3. **`ignite migrate`** -- run database migrations with dry-run and version targeting

Plus a **command registry** that lets users add their own subcommands.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| `argparse.ArgumentParser` | Parse command-line arguments | Building CLI tools |
| `add_subparsers()` | Create subcommands | `git commit`, `docker run` style CLIs |
| `set_defaults(func=...)` | Bind handler to subcommand | Dispatch to the right function |
| `store_true` action | Boolean flags (`--reload`) | On/off switches |
| `choices` parameter | Restrict allowed values | `--format table\|json\|plain` |
| Command registry pattern | Decorator-based registration | Extensible CLI frameworks |

## The Code

### 1. CommandArg and Command

```python
class CommandArg:
    def __init__(self, name, flags, help="", default=None,
                 type=str, action=None, choices=None):
        self.name = name
        self.flags = flags  # e.g., ["--port", "-p"]
        # ...

    def add_to_parser(self, parser):
        kwargs = {"help": self.help, "default": self.default}
        if self.action:
            kwargs["action"] = self.action
        else:
            kwargs["type"] = self.type
        parser.add_argument(*self.flags, **kwargs)

class Command:
    def register(self, subparsers):
        parser = subparsers.add_parser(self.name, help=self.help)
        for arg in self.args:
            arg.add_to_parser(parser)
        parser.set_defaults(func=self.handler)
```

### 2. Command Registry

```python
class CommandRegistry:
    def command(self, name, help="", args=None):
        def decorator(func):
            cmd = Command(name, func, help, args)
            self.register(cmd)
            return func
        return decorator

# Usage:
@registry.command(name="run", help="Start server", args=[...])
def cmd_run(args):
    print(f"Starting on {args.host}:{args.port}")
```

### 3. IgniteCLI

```python
class IgniteCLI:
    def build_parser(self):
        parser = argparse.ArgumentParser(prog="ignite")
        subparsers = parser.add_subparsers(dest="command")
        for cmd in self.registry.all():
            cmd.register(subparsers)
        return parser

    def run(self, args=None):
        parsed = self.build_parser().parse_args(args)
        if hasattr(parsed, "func"):
            return parsed.func(parsed)
        return 1
```

## Playground

```bash
python playground/70_cli_tool.py
```

Expected output:

```
--- Section 1: Run Command ---
  $ ignite run
  Starting Ignite server...
    Host: 127.0.0.1
    Port: 8000
    Reload: False
    Workers: 1
    Log level: info

  $ ignite run --host 0.0.0.0 --port 3000 --reload --workers 4
  Starting Ignite server...
    Host: 0.0.0.0
    Port: 3000
    Reload: True
    Workers: 4
  [PASS] Run command works

--- Section 2: Routes Command ---
  $ ignite routes
  Method   Path                      Handler
  -------------------------------------------------
  GET      /                         index
  GET      /api/users                list_users
  ...
  [PASS] Routes command works
```

## How It Works

### argparse Subcommand Pattern

```
ignite run --host 0.0.0.0 --port 3000
  ^     ^    ^          ^    ^       ^
  |     |    |          |    |       |
  prog  |    flag       |    flag    value
        |               |
     subcommand      value

ArgumentParser
  +-- add_subparsers(dest="command")
        +-- add_parser("run")
        |     +-- add_argument("--host")
        |     +-- add_argument("--port", type=int)
        |     +-- set_defaults(func=cmd_run)
        |
        +-- add_parser("routes")
        |     +-- add_argument("--format", choices=[...])
        |
        +-- add_parser("migrate")
```

### Command Dispatch Flow

```
CLI args: ["run", "--port", "3000"]
    |
    v
parser.parse_args(args)
    |  -> Namespace(command="run", port=3000, func=cmd_run)
    v
parsed.func(parsed)
    |  -> cmd_run(Namespace(port=3000, ...))
    v
Return exit code (0 = success)
```

## Exercises

1. **Add a `create` command** -- `ignite create myproject` that generates a project skeleton with `main.py`, `routes/`, `models/`, and `config.py`.

2. **Add tab completion** -- generate shell completion scripts for bash/zsh using argparse's `argcomplete` integration pattern.

3. **Add colored output** -- use ANSI escape codes to colorize output: green for success, red for errors, yellow for warnings. Add a `--no-color` global flag.

4. **Add a plugin system** -- scan a `plugins/` directory for Python files that register custom commands. Each plugin exports a `register(cli)` function.

5. **Add configuration file support** -- read default values from an `ignite.toml` or `ignite.json` config file, with CLI flags overriding config values.

## What's Next

With a CLI tool, developers can manage their Ignite project from the terminal. In [Kata 71: Static Files](./71-static-files.md), we'll build static file serving with MIME type detection, cache headers, and path traversal security.

---

[prev: 69-structured-logging](./69-structured-logging.md) | [next: 71-static-files](./71-static-files.md)
