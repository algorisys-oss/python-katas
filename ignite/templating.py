"""
Ignite Template Engine

Minimal template engine supporting variable substitution (``{{ var }}``),
control flow (``{% if %}``, ``{% for %}``), filters (``|upper``), comments
(``{# ... #}``), and template inheritance (``{% extends %}`` / ``{% block %}``).

Self-contained -- no ignite imports, only stdlib.
"""

from __future__ import annotations

import re
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

class _TokenType:
    TEXT = "TEXT"
    VAR = "VAR"       # {{ expr }}
    TAG = "TAG"       # {% tag %}
    COMMENT = "COMMENT"  # {# comment #}


class _Token:
    __slots__ = ("type", "value")

    def __init__(self, token_type: str, value: str) -> None:
        self.type = token_type
        self.value = value.strip() if token_type != _TokenType.TEXT else value

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r:.30})"


_TOKEN_RE = re.compile(
    r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})",
    re.DOTALL,
)


def _tokenize(template: str) -> list[_Token]:
    tokens: list[_Token] = []
    for part in _TOKEN_RE.split(template):
        if not part:
            continue
        if part.startswith("{{") and part.endswith("}}"):
            tokens.append(_Token(_TokenType.VAR, part[2:-2]))
        elif part.startswith("{%") and part.endswith("%}"):
            tokens.append(_Token(_TokenType.TAG, part[2:-2]))
        elif part.startswith("{#") and part.endswith("#}"):
            tokens.append(_Token(_TokenType.COMMENT, part[2:-2]))
        else:
            tokens.append(_Token(_TokenType.TEXT, part))
    return tokens


# ---------------------------------------------------------------------------
# Built-in filters
# ---------------------------------------------------------------------------

BUILTIN_FILTERS: dict[str, Callable[..., Any]] = {
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
        str(v)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    ),
}


def _apply_filters(
    value: Any,
    filter_chain: str,
    filters: dict[str, Callable[..., Any]],
) -> Any:
    """Apply a pipe-separated chain of filters to *value*."""
    for filter_expr in filter_chain.split("|"):
        filter_expr = filter_expr.strip()
        if not filter_expr:
            continue
        match = re.match(r"(\w+)(?:\((.+)\))?", filter_expr)
        if not match:
            continue
        name = match.group(1)
        arg_str = match.group(2)
        if name not in filters:
            continue
        if arg_str:
            arg: Any = arg_str.strip("'\"")
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


def _parse_var_expression(expr: str) -> tuple[str, str]:
    """Split ``'name|upper|strip'`` into ``('name', 'upper|strip')``."""
    parts = expr.split("|", 1)
    var_path = parts[0].strip()
    filter_chain = parts[1].strip() if len(parts) > 1 else ""
    return var_path, filter_chain


# ---------------------------------------------------------------------------
# Variable resolution
# ---------------------------------------------------------------------------

def _resolve_var(context: dict[str, Any], path: str) -> Any:
    """Resolve dotted paths: ``user.name`` -> ``context["user"]["name"]``."""
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


# ---------------------------------------------------------------------------
# Template Engine
# ---------------------------------------------------------------------------

class TemplateEngine:
    """Minimal template engine.

    Supports:

    * ``{{ variable }}`` with dotted paths (``user.name``)
    * Filters: ``{{ name|upper }}``, ``{{ items|join(', ') }}``
    * ``{% if cond %}`` / ``{% elif %}`` / ``{% else %}`` / ``{% endif %}``
    * ``{% for item in items %}`` / ``{% endfor %}`` with ``loop.index``,
      ``loop.first``, ``loop.last``
    * Template inheritance: ``{% extends "base" %}`` / ``{% block name %}``
    * Comments: ``{# ignored #}``
    """

    def __init__(self) -> None:
        self.filters: dict[str, Callable[..., Any]] = dict(BUILTIN_FILTERS)
        self._templates: dict[str, str] = {}

    def add_filter(self, name: str, func: Callable[..., Any]) -> None:
        """Register a custom filter."""
        self.filters[name] = func

    def register_template(self, name: str, source: str) -> None:
        """Register a named template (used for inheritance lookups)."""
        self._templates[name] = source

    def render(
        self,
        template: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render *template* with the given *context*."""
        context = context or {}
        template = self._resolve_inheritance(template, context)
        tokens = _tokenize(template)
        return self._render_tokens(tokens, context)

    # -- Inheritance ---------------------------------------------------------

    def _resolve_inheritance(
        self, template: str, context: dict[str, Any]
    ) -> str:
        extends_re = re.compile(r'\{%\s*extends\s+["\'](\w+)["\']\s*%\}')
        match = extends_re.search(template)
        if not match:
            return template

        parent_name = match.group(1)
        if parent_name not in self._templates:
            raise ValueError(f"Parent template {parent_name!r} not found")

        parent_source = self._templates[parent_name]

        block_re = re.compile(
            r"\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}",
            re.DOTALL,
        )
        child_blocks: dict[str, str] = {
            m.group(1): m.group(2) for m in block_re.finditer(template)
        }

        def _replace(m: re.Match) -> str:
            return child_blocks.get(m.group(1), m.group(2))

        resolved = block_re.sub(_replace, parent_source)
        return self._resolve_inheritance(resolved, context)

    # -- Rendering -----------------------------------------------------------

    def _render_tokens(
        self,
        tokens: list[_Token],
        context: dict[str, Any],
    ) -> str:
        output: list[str] = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]

            if tok.type == _TokenType.TEXT:
                output.append(tok.value)
                i += 1

            elif tok.type == _TokenType.COMMENT:
                i += 1

            elif tok.type == _TokenType.VAR:
                var_path, filter_chain = _parse_var_expression(tok.value)
                value = _resolve_var(context, var_path)
                if filter_chain:
                    value = _apply_filters(value, filter_chain, self.filters)
                output.append(str(value))
                i += 1

            elif tok.type == _TokenType.TAG:
                tag = tok.value.strip()
                if tag.startswith("if "):
                    rendered, consumed = self._handle_if(tokens, i, context)
                    output.append(rendered)
                    i += consumed
                elif tag.startswith("for "):
                    rendered, consumed = self._handle_for(tokens, i, context)
                    output.append(rendered)
                    i += consumed
                else:
                    i += 1
        return "".join(output)

    # -- if / elif / else / endif -------------------------------------------

    def _handle_if(
        self,
        tokens: list[_Token],
        start: int,
        context: dict[str, Any],
    ) -> tuple[str, int]:
        branches: list[tuple[str, list[_Token]]] = []
        else_tokens: list[_Token] = []
        current_cond: str | None = tokens[start].value.strip()[3:]
        current_tokens: list[_Token] = []
        depth = 1
        i = start + 1

        while i < len(tokens) and depth > 0:
            tok = tokens[i]
            if tok.type == _TokenType.TAG:
                tag = tok.value.strip()
                if tag.startswith("if "):
                    depth += 1
                    current_tokens.append(tok)
                elif tag == "endif":
                    depth -= 1
                    if depth == 0:
                        if current_cond is not None:
                            branches.append((current_cond, current_tokens))
                        else:
                            else_tokens = current_tokens
                        i += 1
                        break
                    else:
                        current_tokens.append(tok)
                elif tag.startswith("elif ") and depth == 1:
                    branches.append((current_cond or "", current_tokens))
                    current_cond = tag[5:]
                    current_tokens = []
                elif tag == "else" and depth == 1:
                    branches.append((current_cond or "", current_tokens))
                    current_cond = None
                    current_tokens = []
                else:
                    current_tokens.append(tok)
            else:
                current_tokens.append(tok)
            i += 1

        for cond, branch_tokens in branches:
            if self._eval_condition(cond.strip(), context):
                return self._render_tokens(branch_tokens, context), i - start

        if else_tokens:
            return self._render_tokens(else_tokens, context), i - start

        return "", i - start

    # -- for / endfor -------------------------------------------------------

    def _handle_for(
        self,
        tokens: list[_Token],
        start: int,
        context: dict[str, Any],
    ) -> tuple[str, int]:
        tag_content = tokens[start].value.strip()
        match = re.match(r"for\s+(\w+)\s+in\s+(.+)", tag_content)
        if not match:
            return "", 1

        loop_var = match.group(1)
        iterable_expr = match.group(2).strip()

        body_tokens: list[_Token] = []
        depth = 1
        i = start + 1
        while i < len(tokens) and depth > 0:
            tok = tokens[i]
            if tok.type == _TokenType.TAG:
                tag = tok.value.strip()
                if tag.startswith("for "):
                    depth += 1
                elif tag == "endfor":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
            if depth > 0:
                body_tokens.append(tok)
            i += 1

        iterable = _resolve_var(context, iterable_expr)
        if not hasattr(iterable, "__iter__"):
            return "", i - start

        items = list(iterable)
        parts: list[str] = []
        for idx, item in enumerate(items):
            loop_ctx = dict(context)
            loop_ctx[loop_var] = item
            loop_ctx["loop"] = {
                "index": idx + 1,
                "index0": idx,
                "first": idx == 0,
                "last": idx == len(items) - 1,
                "length": len(items),
            }
            parts.append(self._render_tokens(body_tokens, loop_ctx))
        return "".join(parts), i - start

    # -- Condition evaluation ------------------------------------------------

    def _eval_condition(
        self, condition: str, context: dict[str, Any]
    ) -> bool:
        condition = condition.strip()
        if condition.startswith("not "):
            return not self._eval_condition(condition[4:], context)
        if " and " in condition:
            left, right = condition.split(" and ", 1)
            return self._eval_condition(left, context) and self._eval_condition(
                right, context
            )
        if " or " in condition:
            left, right = condition.split(" or ", 1)
            return self._eval_condition(left, context) or self._eval_condition(
                right, context
            )
        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in condition:
                l_str, r_str = condition.split(op, 1)
                l_val = self._resolve_value(l_str.strip(), context)
                r_val = self._resolve_value(r_str.strip(), context)
                return {
                    "==": lambda a, b: a == b,
                    "!=": lambda a, b: a != b,
                    ">": lambda a, b: a > b,
                    "<": lambda a, b: a < b,
                    ">=": lambda a, b: a >= b,
                    "<=": lambda a, b: a <= b,
                }[op](l_val, r_val)
        return bool(self._resolve_value(condition, context))

    @staticmethod
    def _resolve_value(expr: str, context: dict[str, Any]) -> Any:
        expr = expr.strip()
        if (expr.startswith("'") and expr.endswith("'")) or (
            expr.startswith('"') and expr.endswith('"')
        ):
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
        return _resolve_var(context, expr)
