# Kata 72 -- Template Rendering

[prev: 71-static-files](./71-static-files.md) | [next: 73-health-check](./73-health-check.md)

---

## What We're Building

A **minimal template engine** for our Ignite framework. We build all the core features from scratch:

1. **Variable substitution** -- `{{ user.name }}` with dotted path resolution
2. **Filters** -- `{{ name|upper|strip }}` for transforming values
3. **Control flow** -- `{% if %}`, `{% elif %}`, `{% else %}`, `{% endif %}`
4. **Loops** -- `{% for item in items %}` with loop variables (`loop.index`, `loop.first`, `loop.last`)
5. **Template inheritance** -- `{% extends "base" %}` with `{% block %}` overrides
6. **Comments** -- `{# ignored #}`

This is a simplified version of what Jinja2 and Django templates do internally.

## Concepts You'll Learn

| Concept | What It Does | When to Use |
|---|---|---|
| Regex tokenization | Split template into tokens | Parsing template syntax |
| Recursive descent | Process nested if/for blocks | Template control flow |
| Filter chains | Transform values through pipes | `name\|upper\|strip` |
| Dotted path resolution | Walk nested dicts/objects | `user.profile.name` |
| Template inheritance | Override blocks in parent templates | Shared layouts |
| `re.compile()` | Pre-compile regex patterns | Performance |

## The Code

### 1. Tokenizer

Split templates into TEXT, VAR, TAG, and COMMENT tokens:

```python
TOKEN_RE = re.compile(r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})", re.DOTALL)

def tokenize(template):
    tokens = []
    for part in TOKEN_RE.split(template):
        if part.startswith("{{"):
            tokens.append(Token(VAR, part[2:-2]))
        elif part.startswith("{%"):
            tokens.append(Token(TAG, part[2:-2]))
        elif part.startswith("{#"):
            tokens.append(Token(COMMENT, part[2:-2]))
        else:
            tokens.append(Token(TEXT, part))
    return tokens
```

### 2. Variable Resolution

Walk dotted paths through nested dicts, lists, and objects:

```python
def resolve_var(context, path):
    parts = path.split(".")
    value = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, "")
        elif isinstance(value, list):
            value = value[int(part)]
        elif hasattr(value, part):
            value = getattr(value, part)
    return value
```

### 3. Filters

Chain transformations with `|`:

```python
# "name|upper|strip" -> upper(strip(resolve("name")))
BUILTIN_FILTERS = {
    "upper": lambda v: str(v).upper(),
    "lower": lambda v: str(v).lower(),
    "title": lambda v: str(v).title(),
    "length": lambda v: len(v),
    "join": lambda v, sep=", ": sep.join(str(i) for i in v),
    "escape": lambda v: str(v).replace("<", "&lt;")...,
}
```

### 4. Control Flow

Walk tokens, tracking nesting depth for nested blocks:

```python
def _handle_if(self, tokens, start, context):
    # Collect branches: [(condition, tokens), ...]
    # Track depth for nested ifs
    # Evaluate first true condition
    # Render its tokens

def _handle_for(self, tokens, start, context):
    # Parse "for X in Y"
    # Collect body tokens
    # For each item, create context with loop variable
    # Render body for each item
```

### 5. Template Inheritance

```python
# base.html
"""
<html>
<head><title>{% block title %}Default{% endblock %}</title></head>
<body>{% block content %}{% endblock %}</body>
</html>
"""

# child.html
"""
{% extends "base" %}
{% block title %}My Page{% endblock %}
{% block content %}<h1>Hello!</h1>{% endblock %}
"""

# Result: parent structure with child's block content
```

## Playground

```bash
python playground/72_template_rendering.py
```

Expected output:

```
--- Section 1: Variable Substitution ---
  Simple: Hello, Alice! You are 30 years old.
  Dotted: Bob (bob@example.com)
  Missing: Hello, Charlie! Age:
  [PASS] Variable substitution works

--- Section 2: Filters ---
  upper: ALICE
  title: Hello World
  chain (lower|title): Alice Bob
  join: a, b, c
  [PASS] Filters work

--- Section 6: Full Template ---
<div class="user-list">
  <h1>TEAM MEMBERS</h1>
  <ul>
    <li class="first">
      Alice Smith - alice@co.com (Admin)
    </li>
    ...
  </ul>
  <p>Total: 3 users</p>
</div>
  [PASS] Full template works
```

## How It Works

### Token Flow

```
Template: "Hello, {{ name|upper }}! {% if admin %}Admin{% endif %}"

Tokenize:
  [TEXT "Hello, "]
  [VAR  "name|upper"]
  [TEXT "! "]
  [TAG  "if admin"]
  [TEXT "Admin"]
  [TAG  "endif"]

Render:
  TEXT  -> output "Hello, "
  VAR  -> resolve "name" -> "alice" -> upper -> "ALICE"
  TEXT  -> output "! "
  TAG   -> evaluate "if admin" -> True
           render inner tokens -> "Admin"
  TAG   -> endif (consumed by if handler)

Result: "Hello, ALICE! Admin"
```

### Template Inheritance Flow

```
Child: {% extends "base" %}
       {% block title %}My Page{% endblock %}

1. Find extends -> load parent template
2. Extract child blocks: {title: "My Page"}
3. In parent, replace {% block title %}Default{% endblock %}
   with child's "My Page"
4. Keep unreplaced blocks with their defaults
5. Render the resolved template
```

### Filter Pipeline

```
{{ items|join(', ')|upper }}

Value: ["a", "b", "c"]
  |
  v join(', ')
"a, b, c"
  |
  v upper
"A, B, C"
```

## Exercises

1. **Add `{% include "partial" %}` support** -- include another template inline, passing the current context to it. Useful for reusable components.

2. **Add whitespace control** -- implement `{%- tag -%}` and `{{- var -}}` that strip whitespace around tags (like Jinja2's whitespace control).

3. **Add macro support** -- `{% macro button(text, style) %}...{% endmacro %}` to define reusable template functions. Call with `{{ button("Submit", "primary") }}`.

4. **Add auto-escaping** -- by default, escape all variable output with HTML entities. Add a `|safe` filter to opt out: `{{ trusted_html|safe }}`.

5. **Add template compilation** -- instead of interpreting tokens at render time, compile the template to a Python function that directly builds the output string. Measure the speed improvement.

## What's Next

With template rendering, our Ignite framework can generate dynamic HTML pages with layouts, loops, and conditionals. In [Kata 73: Health Check](./73-health-check.md), we'll build health check endpoints that verify database connections, external services, and system resources.

---

[prev: 71-static-files](./71-static-files.md) | [next: 73-health-check](./73-health-check.md)
