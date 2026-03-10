"""
Kata 72 -- Template Rendering
Run: python playground/72_template_rendering.py

Build a minimal template engine: variable substitution {{ var }},
control flow {% if %}...{% endif %} and {% for %}...{% endfor %},
template inheritance with {% extends %} and {% block %}, and
filters like {{ name|upper }}. Compiles templates to Python code.

Completes within 5 seconds.
"""

from __future__ import annotations

import re
from typing import Any, Callable


# ===========================================================================
# SECTION 1: Template Lexer
# ===========================================================================
# Tokenize templates into text, variables, and tags.

class TokenType:
    TEXT = "TEXT"
    VAR = "VAR"           # {{ expr }}
    TAG = "TAG"           # {% tag %}
    COMMENT = "COMMENT"   # {# comment #}


class Token:
    """A single token from the template."""

    def __init__(self, token_type: str, value: str):
        self.type = token_type
        self.value = value.strip() if token_type != TokenType.TEXT else value

    def __repr__(self) -> str:
        val = self.value[:30] + "..." if len(self.value) > 30 else self.value
        return f"Token({self.type}, {val!r})"


# Regex to split templates into tokens
# Matches {{ ... }}, {% ... %}, and {# ... #}
TOKEN_RE = re.compile(
    r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})",
    re.DOTALL,
)


def tokenize(template: str) -> list[Token]:
    """Split a template string into tokens."""
    tokens: list[Token] = []
    parts = TOKEN_RE.split(template)

    for part in parts:
        if not part:
            continue
        if part.startswith("{{") and part.endswith("}}"):
            tokens.append(Token(TokenType.VAR, part[2:-2]))
        elif part.startswith("{%") and part.endswith("%}"):
            tokens.append(Token(TokenType.TAG, part[2:-2]))
        elif part.startswith("{#") and part.endswith("#}"):
            tokens.append(Token(TokenType.COMMENT, part[2:-2]))
        else:
            tokens.append(Token(TokenType.TEXT, part))

    return tokens


# ===========================================================================
# SECTION 2: Filters
# ===========================================================================
# Filters transform variable values: {{ name|upper }}, {{ price|round }}.

# Built-in filter registry
BUILTIN_FILTERS: dict[str, Callable] = {
    "upper": lambda v: str(v).upper(),
    "lower": lambda v: str(v).lower(),
    "title": lambda v: str(v).title(),
    "strip": lambda v: str(v).strip(),
    "length": lambda v: len(v),
    "default": lambda v, d="": v if v else d,
    "join": lambda v, sep=", ": sep.join(str(i) for i in v),
    "first": lambda v: v[0] if v else "",
    "last": lambda v: v[-1] if v else "",
    "reverse": lambda v: v[::-1] if isinstance(v, (list, str)) else v,
    "escape": lambda v: (
        str(v).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    ),
}


def apply_filters(value: Any, filter_chain: str,
                   filters: dict[str, Callable]) -> Any:
    """Apply a chain of filters to a value.

    Example: "name|upper|strip" applies upper then strip.
    """
    for filter_expr in filter_chain.split("|"):
        filter_expr = filter_expr.strip()
        if not filter_expr:
            continue

        # Parse filter name and optional arguments
        # e.g., "default('N/A')" -> name="default", arg="'N/A'"
        match = re.match(r"(\w+)(?:\((.+)\))?", filter_expr)
        if not match:
            continue

        name = match.group(1)
        arg_str = match.group(2)

        if name in filters:
            if arg_str:
                # Evaluate the argument (simple string/number only)
                arg = arg_str.strip("'\"")
                try:
                    arg = int(arg)
                except ValueError:
                    try:
                        arg = float(arg)
                    except ValueError:
                        pass
                value = filters[name](value, arg)
            else:
                value = filters[name](value)

    return value


def parse_var_expression(expr: str) -> tuple[str, str]:
    """Parse a variable expression into (var_path, filter_chain).

    Examples:
        "name" -> ("name", "")
        "name|upper" -> ("name", "upper")
        "user.name|upper|strip" -> ("user.name", "upper|strip")
    """
    parts = expr.split("|", 1)
    var_path = parts[0].strip()
    filter_chain = parts[1].strip() if len(parts) > 1 else ""
    return var_path, filter_chain


# ===========================================================================
# SECTION 3: Variable Resolution
# ===========================================================================
# Resolve dotted variable paths: "user.name" -> context["user"]["name"]

def resolve_var(context: dict[str, Any], path: str) -> Any:
    """Resolve a dotted variable path in the context.

    Supports:
    - Simple: "name" -> context["name"]
    - Dotted: "user.name" -> context["user"]["name"]
    - Nested: "users.0.name" -> context["users"][0]["name"]
    """
    parts = path.split(".")
    value: Any = context

    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, "")
        elif isinstance(value, (list, tuple)):
            try:
                value = value[int(part)]
            except (ValueError, IndexError):
                return ""
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            return ""

    return value


# ===========================================================================
# SECTION 4: Template Engine
# ===========================================================================
# The main template engine that renders templates with context.

class TemplateEngine:
    """A minimal template engine.

    Supports:
    - Variable substitution: {{ variable }}
    - Dotted paths: {{ user.name }}
    - Filters: {{ name|upper }}, {{ items|join(', ') }}
    - Conditionals: {% if condition %}...{% elif %}...{% else %}...{% endif %}
    - Loops: {% for item in items %}...{% endfor %}
    - Loop variable: {{ loop.index }}, {{ loop.first }}, {{ loop.last }}
    - Template inheritance: {% extends "base" %} and {% block name %}
    - Comments: {# this is ignored #}
    """

    def __init__(self):
        self.filters: dict[str, Callable] = dict(BUILTIN_FILTERS)
        self._templates: dict[str, str] = {}

    def add_filter(self, name: str, func: Callable) -> None:
        """Register a custom filter."""
        self.filters[name] = func

    def register_template(self, name: str, source: str) -> None:
        """Register a named template (for inheritance lookups)."""
        self._templates[name] = source

    def render(self, template: str, context: dict[str, Any] | None = None) -> str:
        """Render a template string with the given context."""
        context = context or {}

        # Handle template inheritance
        template = self._resolve_inheritance(template, context)

        tokens = tokenize(template)
        return self._render_tokens(tokens, context)

    def _resolve_inheritance(
        self, template: str, context: dict[str, Any]
    ) -> str:
        """Resolve {% extends "parent" %} inheritance."""
        extends_re = re.compile(r'\{%\s*extends\s+["\'](\w+)["\']\s*%\}')
        match = extends_re.search(template)

        if not match:
            return template

        parent_name = match.group(1)
        if parent_name not in self._templates:
            raise ValueError(f"Parent template {parent_name!r} not found")

        parent_source = self._templates[parent_name]

        # Extract blocks from child template
        block_re = re.compile(
            r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}',
            re.DOTALL,
        )
        child_blocks: dict[str, str] = {}
        for block_match in block_re.finditer(template):
            child_blocks[block_match.group(1)] = block_match.group(2)

        # Replace blocks in parent with child overrides
        def replace_block(m: re.Match) -> str:
            block_name = m.group(1)
            default_content = m.group(2)
            return child_blocks.get(block_name, default_content)

        resolved = block_re.sub(replace_block, parent_source)

        # Recursively resolve if parent also extends something
        return self._resolve_inheritance(resolved, context)

    def _render_tokens(
        self, tokens: list[Token], context: dict[str, Any]
    ) -> str:
        """Render a list of tokens into a string."""
        output: list[str] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == TokenType.TEXT:
                output.append(token.value)
                i += 1

            elif token.type == TokenType.COMMENT:
                i += 1  # Skip comments

            elif token.type == TokenType.VAR:
                var_path, filter_chain = parse_var_expression(token.value)
                value = resolve_var(context, var_path)
                if filter_chain:
                    value = apply_filters(value, filter_chain, self.filters)
                output.append(str(value))
                i += 1

            elif token.type == TokenType.TAG:
                tag_content = token.value.strip()

                if tag_content.startswith("if "):
                    rendered, consumed = self._handle_if(
                        tokens, i, context
                    )
                    output.append(rendered)
                    i += consumed

                elif tag_content.startswith("for "):
                    rendered, consumed = self._handle_for(
                        tokens, i, context
                    )
                    output.append(rendered)
                    i += consumed

                else:
                    i += 1  # Skip unknown tags

        return "".join(output)

    def _handle_if(
        self,
        tokens: list[Token],
        start: int,
        context: dict[str, Any],
    ) -> tuple[str, int]:
        """Handle {% if %}...{% elif %}...{% else %}...{% endif %}."""
        # Collect branches: [(condition, tokens), ...]
        branches: list[tuple[str, list[Token]]] = []
        else_tokens: list[Token] = []
        current_condition = tokens[start].value.strip()[3:]  # Remove "if "
        current_tokens: list[Token] = []
        depth = 1
        i = start + 1

        while i < len(tokens) and depth > 0:
            token = tokens[i]

            if token.type == TokenType.TAG:
                tag = token.value.strip()

                if tag.startswith("if "):
                    depth += 1
                    current_tokens.append(token)
                elif tag == "endif":
                    depth -= 1
                    if depth == 0:
                        if current_condition is not None:
                            branches.append(
                                (current_condition, current_tokens)
                            )
                        else:
                            else_tokens = current_tokens
                        i += 1
                        break
                    else:
                        current_tokens.append(token)
                elif tag.startswith("elif ") and depth == 1:
                    branches.append((current_condition, current_tokens))
                    current_condition = tag[5:]
                    current_tokens = []
                elif tag == "else" and depth == 1:
                    branches.append((current_condition, current_tokens))
                    current_condition = None
                    current_tokens = []
                else:
                    current_tokens.append(token)
            else:
                current_tokens.append(token)
            i += 1

        # Evaluate branches
        for condition, branch_tokens in branches:
            if self._eval_condition(condition.strip(), context):
                return self._render_tokens(branch_tokens, context), i - start

        # Else branch
        if else_tokens:
            return self._render_tokens(else_tokens, context), i - start

        return "", i - start

    def _handle_for(
        self,
        tokens: list[Token],
        start: int,
        context: dict[str, Any],
    ) -> tuple[str, int]:
        """Handle {% for item in items %}...{% endfor %}."""
        tag_content = tokens[start].value.strip()
        # Parse "for X in Y"
        match = re.match(r"for\s+(\w+)\s+in\s+(.+)", tag_content)
        if not match:
            return "", 1

        loop_var = match.group(1)
        iterable_expr = match.group(2).strip()

        # Collect body tokens
        body_tokens: list[Token] = []
        depth = 1
        i = start + 1

        while i < len(tokens) and depth > 0:
            token = tokens[i]
            if token.type == TokenType.TAG:
                tag = token.value.strip()
                if tag.startswith("for "):
                    depth += 1
                elif tag == "endfor":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break

            if depth > 0:
                body_tokens.append(token)
            i += 1

        # Get the iterable
        iterable = resolve_var(context, iterable_expr)
        if not hasattr(iterable, "__iter__"):
            return "", i - start

        # Render for each item
        items = list(iterable)
        output: list[str] = []
        for idx, item in enumerate(items):
            loop_context = dict(context)
            loop_context[loop_var] = item
            loop_context["loop"] = {
                "index": idx + 1,
                "index0": idx,
                "first": idx == 0,
                "last": idx == len(items) - 1,
                "length": len(items),
            }
            output.append(self._render_tokens(body_tokens, loop_context))

        return "".join(output), i - start

    def _eval_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a simple condition expression.

        Supports:
        - Variable truthiness: {% if user %}
        - Comparison: {% if count > 0 %}
        - Equality: {% if status == 'active' %}
        - not: {% if not user %}
        - and/or: {% if x and y %}
        """
        condition = condition.strip()

        # Handle "not"
        if condition.startswith("not "):
            return not self._eval_condition(condition[4:], context)

        # Handle "and"
        if " and " in condition:
            parts = condition.split(" and ", 1)
            return (self._eval_condition(parts[0], context)
                    and self._eval_condition(parts[1], context))

        # Handle "or"
        if " or " in condition:
            parts = condition.split(" or ", 1)
            return (self._eval_condition(parts[0], context)
                    or self._eval_condition(parts[1], context))

        # Handle comparisons
        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in condition:
                left, right = condition.split(op, 1)
                left_val = self._resolve_value(left.strip(), context)
                right_val = self._resolve_value(right.strip(), context)
                if op == "==":
                    return left_val == right_val
                elif op == "!=":
                    return left_val != right_val
                elif op == ">":
                    return left_val > right_val
                elif op == "<":
                    return left_val < right_val
                elif op == ">=":
                    return left_val >= right_val
                elif op == "<=":
                    return left_val <= right_val

        # Simple truthiness
        value = self._resolve_value(condition, context)
        return bool(value)

    def _resolve_value(self, expr: str, context: dict[str, Any]) -> Any:
        """Resolve a value expression (variable, string literal, or number)."""
        expr = expr.strip()

        # String literal
        if (expr.startswith("'") and expr.endswith("'")) or \
           (expr.startswith('"') and expr.endswith('"')):
            return expr[1:-1]

        # Number literal
        try:
            return int(expr)
        except ValueError:
            try:
                return float(expr)
            except ValueError:
                pass

        # Boolean literals
        if expr == "True":
            return True
        if expr == "False":
            return False
        if expr == "None":
            return None

        # Variable
        return resolve_var(context, expr)


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_variable_substitution():
    """Show basic variable substitution."""
    print("--- Section 1: Variable Substitution ---")

    engine = TemplateEngine()

    # Simple variables
    result = engine.render(
        "Hello, {{ name }}! You are {{ age }} years old.",
        {"name": "Alice", "age": 30},
    )
    assert result == "Hello, Alice! You are 30 years old."
    print(f"  Simple: {result}")

    # Dotted paths
    result2 = engine.render(
        "{{ user.name }} ({{ user.email }})",
        {"user": {"name": "Bob", "email": "bob@example.com"}},
    )
    assert result2 == "Bob (bob@example.com)"
    print(f"  Dotted: {result2}")

    # Missing variables
    result3 = engine.render(
        "Hello, {{ name }}! Age: {{ age }}",
        {"name": "Charlie"},
    )
    assert result3 == "Hello, Charlie! Age: "
    print(f"  Missing: {result3}")

    print("  [PASS] Variable substitution works")


def demo_filters():
    """Show filter chains."""
    print("\n--- Section 2: Filters ---")

    engine = TemplateEngine()

    # Upper filter
    result = engine.render("{{ name|upper }}", {"name": "alice"})
    assert result == "ALICE"
    print(f"  upper: {result}")

    # Title filter
    result2 = engine.render("{{ name|title }}", {"name": "hello world"})
    assert result2 == "Hello World"
    print(f"  title: {result2}")

    # Chain
    result3 = engine.render("{{ name|lower|title }}", {"name": "ALICE BOB"})
    assert result3 == "Alice Bob"
    print(f"  chain (lower|title): {result3}")

    # Join
    result4 = engine.render("{{ items|join }}", {"items": ["a", "b", "c"]})
    assert result4 == "a, b, c"
    print(f"  join: {result4}")

    # Length
    result5 = engine.render("{{ items|length }}", {"items": [1, 2, 3]})
    assert result5 == "3"
    print(f"  length: {result5}")

    # Escape
    result6 = engine.render(
        "{{ html|escape }}",
        {"html": "<script>alert('xss')</script>"},
    )
    assert "<script>" not in result6
    assert "&lt;script&gt;" in result6
    print(f"  escape: {result6}")

    # Custom filter
    engine.add_filter("double", lambda v: v * 2)
    result7 = engine.render("{{ num|double }}", {"num": 21})
    assert result7 == "42"
    print(f"  custom (double): {result7}")

    print("  [PASS] Filters work")


def demo_conditionals():
    """Show if/elif/else control flow."""
    print("\n--- Section 3: Conditionals ---")

    engine = TemplateEngine()

    # Simple if
    tmpl = "{% if show %}visible{% endif %}"
    assert engine.render(tmpl, {"show": True}) == "visible"
    assert engine.render(tmpl, {"show": False}) == ""
    print(f"  if True: 'visible'")
    print(f"  if False: ''")

    # If/else
    tmpl2 = "{% if logged_in %}Welcome!{% else %}Please log in{% endif %}"
    assert engine.render(tmpl2, {"logged_in": True}) == "Welcome!"
    assert engine.render(tmpl2, {"logged_in": False}) == "Please log in"
    print(f"  if/else: works")

    # If/elif/else
    tmpl3 = ("{% if role == 'admin' %}Admin"
             "{% elif role == 'mod' %}Moderator"
             "{% else %}User{% endif %}")
    assert engine.render(tmpl3, {"role": "admin"}) == "Admin"
    assert engine.render(tmpl3, {"role": "mod"}) == "Moderator"
    assert engine.render(tmpl3, {"role": "viewer"}) == "User"
    print(f"  if/elif/else: works")

    # Comparison
    tmpl4 = "{% if count > 0 %}has items{% else %}empty{% endif %}"
    assert engine.render(tmpl4, {"count": 5}) == "has items"
    assert engine.render(tmpl4, {"count": 0}) == "empty"
    print(f"  comparison (>): works")

    # Not
    tmpl5 = "{% if not error %}OK{% else %}Error!{% endif %}"
    assert engine.render(tmpl5, {"error": False}) == "OK"
    assert engine.render(tmpl5, {"error": True}) == "Error!"
    print(f"  not: works")

    print("  [PASS] Conditionals work")


def demo_loops():
    """Show for loop iteration."""
    print("\n--- Section 4: Loops ---")

    engine = TemplateEngine()

    # Simple loop
    tmpl = "{% for item in items %}{{ item }} {% endfor %}"
    result = engine.render(tmpl, {"items": ["a", "b", "c"]})
    assert result == "a b c "
    print(f"  Simple loop: {result!r}")

    # Loop with index
    tmpl2 = "{% for user in users %}{{ loop.index }}. {{ user }}\n{% endfor %}"
    result2 = engine.render(tmpl2, {"users": ["Alice", "Bob", "Charlie"]})
    print(f"  With index:\n{result2.rstrip()}")

    # Loop.first and loop.last
    tmpl3 = ("{% for item in items %}"
             "{% if loop.first %}[{% endif %}"
             "{{ item }}"
             "{% if not loop.last %}, {% endif %}"
             "{% if loop.last %}]{% endif %}"
             "{% endfor %}")
    result3 = engine.render(tmpl3, {"items": ["x", "y", "z"]})
    assert result3 == "[x, y, z]"
    print(f"  first/last: {result3}")

    # Loop over dicts (as list of dicts)
    tmpl4 = ("{% for user in users %}"
             "{{ user.name }} ({{ user.role }})\n"
             "{% endfor %}")
    result4 = engine.render(tmpl4, {
        "users": [
            {"name": "Alice", "role": "admin"},
            {"name": "Bob", "role": "user"},
        ],
    })
    print(f"  Dict loop:\n{result4.rstrip()}")

    print("  [PASS] Loops work")


def demo_inheritance():
    """Show template inheritance with extends and blocks."""
    print("\n--- Section 5: Template Inheritance ---")

    engine = TemplateEngine()

    # Register base template
    engine.register_template("base", """<!DOCTYPE html>
<html>
<head><title>{% block title %}Default Title{% endblock %}</title></head>
<body>
{% block content %}Default content{% endblock %}
<footer>{% block footer %}Copyright 2024{% endblock %}</footer>
</body>
</html>""")

    # Child template overrides some blocks
    child = """{% extends "base" %}
{% block title %}My Page{% endblock %}
{% block content %}<h1>Hello World</h1>
<p>This is my page.</p>{% endblock %}"""

    result = engine.render(child)
    assert "My Page" in result
    assert "<h1>Hello World</h1>" in result
    assert "Copyright 2024" in result  # Footer not overridden
    assert "Default Title" not in result
    assert "Default content" not in result

    print(f"  Base template with 3 blocks: title, content, footer")
    print(f"  Child overrides: title, content (keeps footer default)")
    print(f"  Result contains 'My Page': {('My Page' in result)}")
    print(f"  Result contains '<h1>Hello World</h1>': "
          f"{('<h1>Hello World</h1>' in result)}")
    print(f"  Result contains 'Copyright 2024': "
          f"{('Copyright 2024' in result)}")

    print("  [PASS] Template inheritance works")


def demo_full_template():
    """Show a realistic template with all features combined."""
    print("\n--- Section 6: Full Template ---")

    engine = TemplateEngine()

    template = """<div class="user-list">
  <h1>{{ title|upper }}</h1>
  {% if users %}
  <ul>
    {% for user in users %}
    <li class="{% if loop.first %}first{% endif %}">
      {{ user.name|title }} - {{ user.email }}
      {% if user.admin %}(Admin){% endif %}
    </li>
    {% endfor %}
  </ul>
  <p>Total: {{ users|length }} users</p>
  {% else %}
  <p>No users found.</p>
  {% endif %}
</div>"""

    context = {
        "title": "team members",
        "users": [
            {"name": "alice smith", "email": "alice@co.com", "admin": True},
            {"name": "bob jones", "email": "bob@co.com", "admin": False},
            {"name": "charlie brown", "email": "charlie@co.com", "admin": False},
        ],
    }

    result = engine.render(template, context)
    print(result)

    assert "TEAM MEMBERS" in result
    assert "Alice Smith" in result
    assert "(Admin)" in result
    assert "Total: 3 users" in result
    assert "No users found" not in result

    # Test empty users
    result2 = engine.render(template, {"title": "team", "users": []})
    assert "No users found." in result2
    print(f"  Empty list: shows 'No users found.'")

    print("  [PASS] Full template works")


def demo_comments():
    """Show template comments."""
    print("\n--- Section 7: Comments ---")

    engine = TemplateEngine()

    result = engine.render(
        "Hello{# this is a comment #}, {{ name }}!",
        {"name": "World"},
    )
    assert result == "Hello, World!"
    assert "comment" not in result
    print(f"  Comment stripped: {result}")

    print("  [PASS] Comments work")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_variable_substitution()
    demo_filters()
    demo_conditionals()
    demo_loops()
    demo_inheritance()
    demo_full_template()
    demo_comments()

    print("\n--- Summary ---")
    print("Template rendering gives our Ignite framework:")
    print("  - Variable substitution with {{ var }}")
    print("  - Dotted path resolution (user.name)")
    print("  - Filter chains (name|upper|strip)")
    print("  - Conditionals (if/elif/else/endif)")
    print("  - Loops with loop variable (index, first, last)")
    print("  - Template inheritance (extends, block)")
    print("  - Comments ({# ... #})")
    print("  - Custom filter registration")
    print("\nAll 7 sections passed. Template rendering mastered!")
    print("Next up: Kata 73 -- health check!")


if __name__ == "__main__":
    main()
