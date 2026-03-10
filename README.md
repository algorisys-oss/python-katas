# Python Katas

Core Python mastery, then build a FastAPI-like framework from scratch -- step by step.

## What's Inside

**79 katas** across 12 modules:

| Module | Katas | Focus |
|--------|-------|-------|
| Pythonic Foundations | 00–10 | Data model, generators, decorators, type hints |
| OOP & SOLID | 11–20 | Classes, descriptors, metaclasses, SOLID principles |
| Concurrency | 21–30 | Threading, GIL, multiprocessing, async, free-threaded Python |
| Advanced Features | 31–35 | Memory, imports, testing, packaging |
| Build Ignite (FastAPI clone) | 36–78 | HTTP, routing, DI, validation, WebSocket, auth, and more |

## Quick Start

```bash
# 1. Clone and enter the project
cd python-katas

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Seed the database with kata data
cd backend && python seed.py && cd ..

# 5. Start the webapp
cd backend && python app.py
```

Open **http://localhost:8000** in your browser.

## Running Without the Webapp

Each kata also has a standalone playground script:

```bash
python3 playground/00_project_setup.py
python3 playground/01_python_data_model.py
```

## Project Structure

```
backend/              -- FastAPI webapp (serves tutorials, runs code)
  app.py              -- Main application
  db.py               -- SQLite3 database layer
  runner.py           -- Sandboxed code execution
  seed.py             -- Load katas into database
  requirements.txt    -- Python dependencies
frontend/
  static/             -- CSS and JS (no npm, no build step)
  templates/          -- Jinja2 templates (HTMX + CodeMirror)
tutorial/             -- Markdown tutorial files
playground/           -- Standalone runnable scripts per kata
src/ignite/           -- Framework code (built from kata 36 onward)
```

## Tech Stack

- **Backend:** FastAPI + SQLite3 + Uvicorn
- **Frontend:** HTMX + CodeMirror 5 (CDN, no npm)
- **Templates:** Jinja2
- **Code execution:** Subprocess with timeout sandboxing

## Keyboard Shortcuts (in editor)

| Shortcut | Action |
|----------|--------|
| Ctrl/Cmd + Enter | Run code |
| Ctrl/Cmd + S | Save code |
