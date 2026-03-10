"""
Kata 72 -- Template Rendering
Run: python playground/skeletons/72_template_rendering.py

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


TOKEN_RE = re.compile(
    r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})",
    re.DOTALL,
)


def tokenize(template: str) -> list[Token]:
    """Split a template string into tokens."""
    tokens: list[Token] = []
    parts = TOKEN_RE.split(template)

    # TODO: For each part:
    #   - If starts with "{{" and ends with "}}" -> TokenType.VAR (strip {{ }})
    #   - If starts with "{%" and ends with "%}" -> TokenType.TAG (strip {% %})
    #   - If starts with "{#" and ends with "#}" -> TokenType.COMMENT
    #   - Otherwise -> TokenType.TEXT
    # Skip empty parts

    return tokens


# ===========================================================================
# SECTION 2: Filters
# ===========================================================================

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
    """Apply a chain of filters to a value."""
    # TODO: Split filter_chain by "|"
    # For each filter expression:
    #   1. Parse name and optional args: re.match(r"(\w+)(?:\((.+)\))?", expr)
    #   2. Look up the filter in the filters dict
    #   3. Call it with the value (and arg if present)
    #   4. Update value with the result
    return value


def parse_var_expression(expr: str) -> tuple[str, str]:
    """Parse a variable expression into (var_path, filter_chain)."""
    # TODO: Split expr on first "|"
    # Return (var_path, filter_chain) or (var_path, "") if no filters
    return expr.strip(), ""


# ===========================================================================
# SECTION 3: Variable Resolution
# ===========================================================================

def resolve_var(context: dict[str, Any], path: str) -> Any:
    """Resolve a dotted variable path in the context.

    Examples:
    - "name" -> context["name"]
    - "user.name" -> context["user"]["name"]
    """
    # TODO: Split path by "." and walk the context:
    # For each part:
    #   - If value is a dict, get value[part]
    #   - If value is a list/tuple, try value[int(part)]
    #   - If value has the attribute, use getattr
    #   - Otherwise return ""
    return context.get(path, "")


# ===========================================================================
# SECTION 4: Template Engine
# ===========================================================================

class TemplateEngine:
    """A minimal template engine."""

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

        # TODO: Extract blocks from child template using regex:
        # Pattern: {% block name %}content{% endblock %}
        # Replace matching blocks in parent with child content
        # Keep parent's default content for blocks not overridden

        block_re = re.compile(
            r'\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}',
            re.DOTALL,
        )
        child_blocks: dict[str, str] = {}
        for block_match in block_re.finditer(template):
            child_blocks[block_match.group(1)] = block_match.group(2)

        def replace_block(m: re.Match) -> str:
            block_name = m.group(1)
            default_content = m.group(2)
            return child_blocks.get(block_name, default_content)

        resolved = block_re.sub(replace_block, parent_source)
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
                i += 1

            elif token.type == TokenType.VAR:
                # TODO: Parse variable expression with parse_var_expression()
                # Resolve the variable with resolve_var()
                # Apply filters if any with apply_filters()
                # Append str(value) to output
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
                    i += 1

        return "".join(output)

    def _handle_if(
        self,
        tokens: list[Token],
        start: int,
        context: dict[str, Any],
    ) -> tuple[str, int]:
        """Handle {% if %}...{% elif %}...{% else %}...{% endif %}."""
        branches: list[tuple[str, list[Token]]] = []
        else_tokens: list[Token] = []
        current_condition = tokens[start].value.strip()[3:]
        current_tokens: list[Token] = []
        depth = 1
        i = start + 1

        # TODO: Walk tokens to collect branches:
        # Track nesting depth (nested ifs)
        # On "elif" at depth 1: save current branch, start new one
        # On "else" at depth 1: save current branch, collect else tokens
        # On "endif" at depth 1: save and break
        #
        # Then evaluate branches: find the first true condition,
        # render its tokens, and return (rendered, tokens_consumed)

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

        for condition, branch_tokens in branches:
            if self._eval_condition(condition.strip(), context):
                return self._render_tokens(branch_tokens, context), i - start

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

        # TODO: Get the iterable by resolving iterable_expr
        # For each item, create a new context with:
        #   loop_var -> current item
        #   "loop" -> {"index": 1-based, "index0": 0-based,
        #              "first": bool, "last": bool, "length": int}
        # Render body_tokens for each item and join results

        return "", i - start

    def _eval_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a simple condition expression."""
        condition = condition.strip()

        if condition.startswith("not "):
            return not self._eval_condition(condition[4:], context)

        if " and " in condition:
            parts = condition.split(" and ", 1)
            return (self._eval_condition(parts[0], context)
                    and self._eval_condition(parts[1], context))

        if " or " in condition:
            parts = condition.split(" or ", 1)
            return (self._eval_condition(parts[0], context)
                    or self._eval_condition(parts[1], context))

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

        value = self._resolve_value(condition, context)
        return bool(value)

    def _resolve_value(self, expr: str, context: dict[str, Any]) -> Any:
        """Resolve a value expression."""
        expr = expr.strip()

        if (expr.startswith("'") and expr.endswith("'")) or \
           (expr.startswith('"') and expr.endswith('"')):
            return expr[1:-1]

        try:
            return int(expr)
        except ValueError:
            try:
                return float(expr)
            except ValueError:
                pass

        if expr == "True":
            return True
        if expr == "False":
            return False
        if expr == "None":
            return None

        return resolve_var(context, expr)


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_variable_substitution():
    """Show basic variable substitution."""
    print("--- Section 1: Variable Substitution ---")

    try:
        engine = TemplateEngine()

        result = engine.render(
            "Hello, {{ name }}! You are {{ age }} years old.",
            {"name": "Alice", "age": 30},
        )
        assert result == "Hello, Alice! You are 30 years old."
        print(f"  Simple: {result}")

        result2 = engine.render(
            "{{ user.name }} ({{ user.email }})",
            {"user": {"name": "Bob", "email": "bob@example.com"}},
        )
        assert result2 == "Bob (bob@example.com)"
        print(f"  Dotted: {result2}")

        result3 = engine.render(
            "Hello, {{ name }}! Age: {{ age }}",
            {"name": "Charlie"},
        )
        assert result3 == "Hello, Charlie! Age: "
        print(f"  Missing: {result3}")

        print("  [PASS] Variable substitution works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_filters():
    """Show filter chains."""
    print("\n--- Section 2: Filters ---")

    try:
        engine = TemplateEngine()

        result = engine.render("{{ name|upper }}", {"name": "alice"})
        assert result == "ALICE"
        print(f"  upper: {result}")

        result2 = engine.render("{{ name|title }}", {"name": "hello world"})
        assert result2 == "Hello World"
        print(f"  title: {result2}")

        result3 = engine.render("{{ name|lower|title }}", {"name": "ALICE BOB"})
        assert result3 == "Alice Bob"
        print(f"  chain (lower|title): {result3}")

        result4 = engine.render("{{ items|join }}", {"items": ["a", "b", "c"]})
        assert result4 == "a, b, c"
        print(f"  join: {result4}")

        result5 = engine.render("{{ items|length }}", {"items": [1, 2, 3]})
        assert result5 == "3"
        print(f"  length: {result5}")

        result6 = engine.render(
            "{{ html|escape }}",
            {"html": "<script>alert('xss')</script>"},
        )
        assert "<script>" not in result6
        assert "&lt;script&gt;" in result6
        print(f"  escape: {result6}")

        engine.add_filter("double", lambda v: v * 2)
        result7 = engine.render("{{ num|double }}", {"num": 21})
        assert result7 == "42"
        print(f"  custom (double): {result7}")

        print("  [PASS] Filters work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_conditionals():
    """Show if/elif/else control flow."""
    print("\n--- Section 3: Conditionals ---")

    try:
        engine = TemplateEngine()

        tmpl = "{% if show %}visible{% endif %}"
        assert engine.render(tmpl, {"show": True}) == "visible"
        assert engine.render(tmpl, {"show": False}) == ""
        print(f"  if True: 'visible'")
        print(f"  if False: ''")

        tmpl2 = "{% if logged_in %}Welcome!{% else %}Please log in{% endif %}"
        assert engine.render(tmpl2, {"logged_in": True}) == "Welcome!"
        assert engine.render(tmpl2, {"logged_in": False}) == "Please log in"
        print(f"  if/else: works")

        tmpl3 = ("{% if role == 'admin' %}Admin"
                 "{% elif role == 'mod' %}Moderator"
                 "{% else %}User{% endif %}")
        assert engine.render(tmpl3, {"role": "admin"}) == "Admin"
        assert engine.render(tmpl3, {"role": "mod"}) == "Moderator"
        assert engine.render(tmpl3, {"role": "viewer"}) == "User"
        print(f"  if/elif/else: works")

        tmpl4 = "{% if count > 0 %}has items{% else %}empty{% endif %}"
        assert engine.render(tmpl4, {"count": 5}) == "has items"
        assert engine.render(tmpl4, {"count": 0}) == "empty"
        print(f"  comparison (>): works")

        tmpl5 = "{% if not error %}OK{% else %}Error!{% endif %}"
        assert engine.render(tmpl5, {"error": False}) == "OK"
        assert engine.render(tmpl5, {"error": True}) == "Error!"
        print(f"  not: works")

        print("  [PASS] Conditionals work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_loops():
    """Show for loop iteration."""
    print("\n--- Section 4: Loops ---")

    try:
        engine = TemplateEngine()

        tmpl = "{% for item in items %}{{ item }} {% endfor %}"
        result = engine.render(tmpl, {"items": ["a", "b", "c"]})
        assert result == "a b c "
        print(f"  Simple loop: {result!r}")

        tmpl2 = "{% for user in users %}{{ loop.index }}. {{ user }}\n{% endfor %}"
        result2 = engine.render(tmpl2, {"users": ["Alice", "Bob", "Charlie"]})
        print(f"  With index:\n{result2.rstrip()}")

        tmpl3 = ("{% for item in items %}"
                 "{% if loop.first %}[{% endif %}"
                 "{{ item }}"
                 "{% if not loop.last %}, {% endif %}"
                 "{% if loop.last %}]{% endif %}"
                 "{% endfor %}")
        result3 = engine.render(tmpl3, {"items": ["x", "y", "z"]})
        assert result3 == "[x, y, z]"
        print(f"  first/last: {result3}")

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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_inheritance():
    """Show template inheritance with extends and blocks."""
    print("\n--- Section 5: Template Inheritance ---")

    try:
        engine = TemplateEngine()

        engine.register_template("base", """<!DOCTYPE html>
<html>
<head><title>{% block title %}Default Title{% endblock %}</title></head>
<body>
{% block content %}Default content{% endblock %}
<footer>{% block footer %}Copyright 2024{% endblock %}</footer>
</body>
</html>""")

        child = """{% extends "base" %}
{% block title %}My Page{% endblock %}
{% block content %}<h1>Hello World</h1>
<p>This is my page.</p>{% endblock %}"""

        result = engine.render(child)
        assert "My Page" in result
        assert "<h1>Hello World</h1>" in result
        assert "Copyright 2024" in result
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
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_full_template():
    """Show a realistic template with all features combined."""
    print("\n--- Section 6: Full Template ---")

    try:
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

        result2 = engine.render(template, {"title": "team", "users": []})
        assert "No users found." in result2
        print(f"  Empty list: shows 'No users found.'")

        print("  [PASS] Full template works")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


def demo_comments():
    """Show template comments."""
    print("\n--- Section 7: Comments ---")

    try:
        engine = TemplateEngine()

        result = engine.render(
            "Hello{# this is a comment #}, {{ name }}!",
            {"name": "World"},
        )
        assert result == "Hello, World!"
        assert "comment" not in result
        print(f"  Comment stripped: {result}")

        print("  [PASS] Comments work")
    except (AssertionError, TypeError, AttributeError, Exception) as e:
        print(f"  ❌ Not yet implemented: {e}")


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
    print("\nAll 7 sections attempted. Template rendering skeleton ready!")
    print("Next up: Kata 73 -- health check!")


if __name__ == "__main__":
    main()
