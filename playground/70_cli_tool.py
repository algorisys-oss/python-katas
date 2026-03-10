"""
Kata 70 -- CLI Tool
Run: python playground/70_cli_tool.py

Build an Ignite CLI using argparse with subcommands: run (start server),
routes (list registered routes), migrate (run migrations). Includes a
command registration framework and argument parsing.

Completes within 5 seconds.
"""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Command Registry
# ===========================================================================
# A registry for CLI commands. Each command has a name, description,
# argument definitions, and a handler function.

class CommandArg:
    """Definition of a CLI argument."""

    def __init__(
        self,
        name: str,
        flags: list[str] | None = None,
        help: str = "",
        default: Any = None,
        type: type = str,
        required: bool = False,
        action: str | None = None,
        choices: list[str] | None = None,
    ):
        self.name = name
        self.flags = flags or [f"--{name}"]
        self.help = help
        self.default = default
        self.type = type
        self.required = required
        self.action = action
        self.choices = choices

    def add_to_parser(self, parser: argparse.ArgumentParser) -> None:
        """Add this argument to an argparse parser."""
        default = self.default
        if self.action == "store_true" and default is None:
            default = False
        kwargs: dict[str, Any] = {
            "help": self.help,
            "default": default,
        }
        if self.action:
            kwargs["action"] = self.action
        else:
            kwargs["type"] = self.type
        if self.required:
            kwargs["required"] = self.required
        if self.choices:
            kwargs["choices"] = self.choices
        parser.add_argument(*self.flags, **kwargs)


class Command:
    """A CLI command with its arguments and handler."""

    def __init__(
        self,
        name: str,
        handler: Callable[..., int],
        help: str = "",
        args: list[CommandArg] | None = None,
    ):
        self.name = name
        self.handler = handler
        self.help = help
        self.args = args or []

    def register(self, subparsers: Any) -> argparse.ArgumentParser:
        """Register this command with argparse subparsers."""
        parser = subparsers.add_parser(self.name, help=self.help)
        for arg in self.args:
            arg.add_to_parser(parser)
        parser.set_defaults(func=self.handler)
        return parser


class CommandRegistry:
    """Registry of CLI commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command

    def command(
        self,
        name: str,
        help: str = "",
        args: list[CommandArg] | None = None,
    ) -> Callable:
        """Decorator to register a command handler."""
        def decorator(func: Callable) -> Callable:
            cmd = Command(name=name, handler=func, help=help, args=args)
            self.register(cmd)
            return func
        return decorator

    def get(self, name: str) -> Command | None:
        """Get a command by name."""
        return self._commands.get(name)

    def all(self) -> list[Command]:
        """Get all registered commands."""
        return list(self._commands.values())


# ===========================================================================
# SECTION 2: Ignite CLI
# ===========================================================================
# The main CLI class that builds the argparse parser and runs commands.

class IgniteCLI:
    """The Ignite framework CLI.

    Usage:
        ignite run --host 0.0.0.0 --port 8000 --reload
        ignite routes --format table
        ignite migrate --target head
        ignite migrate --target head --dry-run
    """

    def __init__(self, prog: str = "ignite"):
        self.prog = prog
        self.registry = CommandRegistry()
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register the built-in commands: run, routes, migrate."""

        # --- run command ---
        @self.registry.command(
            name="run",
            help="Start the development server",
            args=[
                CommandArg("host", ["--host", "-H"],
                           help="Host to bind to",
                           default="127.0.0.1"),
                CommandArg("port", ["--port", "-p"],
                           help="Port to listen on",
                           default=8000, type=int),
                CommandArg("reload", ["--reload", "-r"],
                           help="Enable auto-reload",
                           action="store_true"),
                CommandArg("workers", ["--workers", "-w"],
                           help="Number of worker processes",
                           default=1, type=int),
                CommandArg("log_level", ["--log-level"],
                           help="Log level",
                           default="info",
                           choices=["debug", "info", "warning", "error"]),
            ],
        )
        def cmd_run(args: argparse.Namespace) -> int:
            print(f"Starting Ignite server...")
            print(f"  Host: {args.host}")
            print(f"  Port: {args.port}")
            print(f"  Reload: {args.reload}")
            print(f"  Workers: {args.workers}")
            print(f"  Log level: {args.log_level}")
            # In a real CLI, this would start the server
            return 0

        # --- routes command ---
        @self.registry.command(
            name="routes",
            help="List all registered routes",
            args=[
                CommandArg("format", ["--format", "-f"],
                           help="Output format",
                           default="table",
                           choices=["table", "json", "plain"]),
                CommandArg("method", ["--method", "-m"],
                           help="Filter by HTTP method"),
                CommandArg("verbose", ["--verbose", "-v"],
                           help="Show additional details",
                           action="store_true"),
            ],
        )
        def cmd_routes(args: argparse.Namespace) -> int:
            # Simulated route data
            routes = [
                {"method": "GET", "path": "/", "handler": "index",
                 "middleware": ["auth"]},
                {"method": "GET", "path": "/api/users", "handler": "list_users",
                 "middleware": []},
                {"method": "POST", "path": "/api/users", "handler": "create_user",
                 "middleware": ["auth", "validate"]},
                {"method": "GET", "path": "/api/users/{id}", "handler": "get_user",
                 "middleware": ["auth"]},
                {"method": "DELETE", "path": "/api/users/{id}", "handler": "delete_user",
                 "middleware": ["auth", "admin"]},
                {"method": "GET", "path": "/health", "handler": "health_check",
                 "middleware": []},
            ]

            # Filter by method if specified
            if args.method:
                routes = [r for r in routes
                          if r["method"] == args.method.upper()]

            if args.format == "json":
                import json
                print(json.dumps(routes, indent=2))
            elif args.format == "table":
                print(f"{'Method':<8} {'Path':<25} {'Handler':<15}"
                      f"{'Middleware' if args.verbose else ''}")
                print("-" * (48 + (20 if args.verbose else 0)))
                for r in routes:
                    mid = ", ".join(r["middleware"]) if args.verbose else ""
                    print(f"{r['method']:<8} {r['path']:<25} "
                          f"{r['handler']:<15} {mid}")
            else:  # plain
                for r in routes:
                    print(f"{r['method']} {r['path']}")

            print(f"\n{len(routes)} route(s) found")
            return 0

        # --- migrate command ---
        @self.registry.command(
            name="migrate",
            help="Run database migrations",
            args=[
                CommandArg("target", ["--target", "-t"],
                           help="Migration target (version or 'head')",
                           default="head"),
                CommandArg("dry_run", ["--dry-run"],
                           help="Show what would be done without executing",
                           action="store_true"),
                CommandArg("verbose", ["--verbose", "-v"],
                           help="Show detailed migration info",
                           action="store_true"),
            ],
        )
        def cmd_migrate(args: argparse.Namespace) -> int:
            # Simulated migration data
            migrations = [
                {"version": "001", "name": "create_users_table",
                 "status": "applied"},
                {"version": "002", "name": "add_email_column",
                 "status": "applied"},
                {"version": "003", "name": "create_posts_table",
                 "status": "pending"},
                {"version": "004", "name": "add_indexes",
                 "status": "pending"},
            ]

            pending = [m for m in migrations if m["status"] == "pending"]
            applied = [m for m in migrations if m["status"] == "applied"]

            if args.target == "head":
                target_migrations = pending
            else:
                target_migrations = [
                    m for m in pending
                    if m["version"] <= args.target
                ]

            prefix = "[DRY RUN] " if args.dry_run else ""

            print(f"{prefix}Migration status:")
            print(f"  Applied: {len(applied)}")
            print(f"  Pending: {len(pending)}")
            print(f"  Target: {args.target}")

            if target_migrations:
                print(f"\n{prefix}Running migrations:")
                for m in target_migrations:
                    if args.verbose:
                        print(f"  {m['version']}: {m['name']} "
                              f"(status: {m['status']})")
                    else:
                        print(f"  {m['version']}: {m['name']}")
                    if not args.dry_run:
                        m["status"] = "applied"
                print(f"\n{prefix}{len(target_migrations)} migration(s) "
                      f"{'would be ' if args.dry_run else ''}applied")
            else:
                print(f"\n{prefix}No pending migrations")

            return 0

    def build_parser(self) -> argparse.ArgumentParser:
        """Build the argparse parser with all registered commands."""
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description="Ignite -- A Python web framework CLI",
        )
        parser.add_argument(
            "--version", action="version", version="Ignite 1.0.0"
        )

        subparsers = parser.add_subparsers(
            title="commands",
            dest="command",
            help="Available commands",
        )

        for cmd in self.registry.all():
            cmd.register(subparsers)

        return parser

    def run(self, args: list[str] | None = None) -> int:
        """Parse arguments and run the appropriate command.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self.build_parser()
        parsed = parser.parse_args(args)

        if not parsed.command:
            parser.print_help()
            return 1

        if hasattr(parsed, "func"):
            return parsed.func(parsed)

        return 1


# ===========================================================================
# SECTION 3: Custom Commands
# ===========================================================================
# Show how users can add their own commands to the CLI.

def register_custom_commands(cli: IgniteCLI) -> None:
    """Register application-specific commands."""

    @cli.registry.command(
        name="shell",
        help="Start an interactive Python shell with app context",
        args=[
            CommandArg("no_banner", ["--no-banner"],
                       help="Hide the startup banner",
                       action="store_true"),
        ],
    )
    def cmd_shell(args: argparse.Namespace) -> int:
        if not args.no_banner:
            print("Ignite Interactive Shell")
            print("App context loaded. Available: app, db, User, Post")
            print("Type 'exit()' to quit.")
        print(">>> # Shell would start here (simulated)")
        return 0

    @cli.registry.command(
        name="seed",
        help="Seed the database with sample data",
        args=[
            CommandArg("count", ["--count", "-n"],
                       help="Number of records to create",
                       default=10, type=int),
            CommandArg("table", ["--table", "-t"],
                       help="Table to seed",
                       default="all"),
        ],
    )
    def cmd_seed(args: argparse.Namespace) -> int:
        print(f"Seeding database:")
        print(f"  Table: {args.table}")
        print(f"  Count: {args.count}")
        tables = ["users", "posts", "comments"] if args.table == "all" \
            else [args.table]
        for table in tables:
            print(f"  Created {args.count} {table} records")
        return 0


# ===========================================================================
# SECTION 4: Demos
# ===========================================================================

def demo_run_command():
    """Show the 'run' command with various options."""
    print("--- Section 1: Run Command ---")

    cli = IgniteCLI()

    # Default options
    print("  $ ignite run")
    code = cli.run(["run"])
    assert code == 0

    # Custom options
    print("\n  $ ignite run --host 0.0.0.0 --port 3000 --reload --workers 4")
    code = cli.run(["run", "--host", "0.0.0.0", "--port", "3000",
                     "--reload", "--workers", "4"])
    assert code == 0

    print("  [PASS] Run command works")


def demo_routes_command():
    """Show the 'routes' command with different formats."""
    print("\n--- Section 2: Routes Command ---")

    cli = IgniteCLI()

    # Table format (default)
    print("  $ ignite routes")
    code = cli.run(["routes"])
    assert code == 0

    # Filter by method
    print("\n  $ ignite routes --method POST")
    code = cli.run(["routes", "--method", "POST"])
    assert code == 0

    # Verbose mode
    print("\n  $ ignite routes --verbose")
    code = cli.run(["routes", "--verbose"])
    assert code == 0

    # Plain format
    print("\n  $ ignite routes --format plain")
    code = cli.run(["routes", "--format", "plain"])
    assert code == 0

    print("  [PASS] Routes command works")


def demo_migrate_command():
    """Show the 'migrate' command."""
    print("\n--- Section 3: Migrate Command ---")

    cli = IgniteCLI()

    # Run all pending migrations
    print("  $ ignite migrate")
    code = cli.run(["migrate"])
    assert code == 0

    # Dry run
    print("\n  $ ignite migrate --dry-run --verbose")
    code = cli.run(["migrate", "--dry-run", "--verbose"])
    assert code == 0

    # Specific target
    print("\n  $ ignite migrate --target 003")
    code = cli.run(["migrate", "--target", "003"])
    assert code == 0

    print("  [PASS] Migrate command works")


def demo_custom_commands():
    """Show adding custom commands."""
    print("\n--- Section 4: Custom Commands ---")

    cli = IgniteCLI()
    register_custom_commands(cli)

    # Verify custom commands are registered
    assert cli.registry.get("shell") is not None
    assert cli.registry.get("seed") is not None

    print("  $ ignite shell")
    code = cli.run(["shell"])
    assert code == 0

    print("\n  $ ignite seed --count 5 --table users")
    code = cli.run(["seed", "--count", "5", "--table", "users"])
    assert code == 0

    print("\n  $ ignite seed")
    code = cli.run(["seed"])
    assert code == 0

    print("  [PASS] Custom commands work")


def demo_argument_parsing():
    """Show argument parsing details."""
    print("\n--- Section 5: Argument Parsing ---")

    cli = IgniteCLI()
    parser = cli.build_parser()

    # Test parsing various argument combinations
    test_cases = [
        (["run"], {"command": "run", "host": "127.0.0.1", "port": 8000,
                    "reload": False, "workers": 1}),
        (["run", "-H", "0.0.0.0", "-p", "3000", "-r"],
         {"command": "run", "host": "0.0.0.0", "port": 3000,
          "reload": True}),
        (["routes", "-f", "json"],
         {"command": "routes", "format": "json"}),
        (["migrate", "--dry-run", "-v"],
         {"command": "migrate", "dry_run": True, "verbose": True}),
    ]

    for args, expected in test_cases:
        parsed = parser.parse_args(args)
        print(f"  '{' '.join(args)}' ->")
        for key, value in expected.items():
            actual = getattr(parsed, key)
            assert actual == value, (
                f"    {key}: expected {value!r}, got {actual!r}"
            )
            print(f"    {key}={actual!r}")

    print("  [PASS] Argument parsing works")


def demo_command_registry():
    """Show the command registry pattern."""
    print("\n--- Section 6: Command Registry ---")

    registry = CommandRegistry()

    # Register commands with the decorator
    @registry.command(
        name="test",
        help="Run test suite",
        args=[
            CommandArg("pattern", ["--pattern", "-k"],
                       help="Test name pattern"),
            CommandArg("verbose", ["--verbose", "-v"],
                       help="Verbose output",
                       action="store_true"),
        ],
    )
    def cmd_test(args: argparse.Namespace) -> int:
        return 0

    @registry.command(name="lint", help="Run linter")
    def cmd_lint(args: argparse.Namespace) -> int:
        return 0

    # Check registry
    all_cmds = registry.all()
    print(f"  Registered commands: {len(all_cmds)}")
    for cmd in all_cmds:
        arg_names = [a.name for a in cmd.args]
        print(f"    {cmd.name}: {cmd.help} "
              f"(args: {arg_names if arg_names else 'none'})")

    assert len(all_cmds) == 2
    assert registry.get("test") is not None
    assert registry.get("test").args[0].name == "pattern"
    assert registry.get("lint") is not None
    assert registry.get("nonexistent") is None

    print("  [PASS] Command registry works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_run_command()
    demo_routes_command()
    demo_migrate_command()
    demo_custom_commands()
    demo_argument_parsing()
    demo_command_registry()

    print("\n--- Summary ---")
    print("CLI tool gives our Ignite framework:")
    print("  - 'ignite run' with host, port, reload, workers options")
    print("  - 'ignite routes' with table/json/plain formats and filtering")
    print("  - 'ignite migrate' with dry-run and target version")
    print("  - Command registry with decorator-based registration")
    print("  - Extensible: add custom commands (shell, seed, etc.)")
    print("  - Built on argparse -- no external dependencies")
    print("\nAll 6 sections passed. CLI tool mastered!")
    print("Next up: Kata 71 -- static files!")


if __name__ == "__main__":
    main()
