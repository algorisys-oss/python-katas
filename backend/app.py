"""Python Katas -- FastAPI webapp with HTMX frontend."""

from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

import markdown
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pygments.formatters import HtmlFormatter

from db import get_all_katas, get_kata, get_skeleton, get_solution, init_db, reset_user_code, save_run, save_user_code
from runner import run_code

PROJECT_ROOT = Path(__file__).parent.parent

md = markdown.Markdown(extensions=["fenced_code", "codehilite", "tables", "toc"], extension_configs={
    "codehilite": {"css_class": "highlight", "guess_lang": False},
})


def render_tutorial(tutorial_path: str) -> str:
    """Render a tutorial markdown file to HTML."""
    full_path = PROJECT_ROOT / tutorial_path
    if not full_path.exists():
        return "<p>Tutorial not yet written.</p>"
    md.reset()
    return md.convert(full_path.read_text())


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Python Katas", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "frontend" / "static")), name="static")

templates = Jinja2Templates(directory=str(PROJECT_ROOT / "frontend" / "templates"))


# --- HTML Pages (HTMX) ---


@app.get("/", response_class=HTMLResponse)
async def kata_list(request: Request):
    katas = get_all_katas()
    grouped = defaultdict(list)
    for k in katas:
        grouped[k["module"]].append(k)
    return templates.TemplateResponse("kata_list.html", {
        "request": request,
        "grouped_katas": dict(grouped),
    })


@app.get("/kata/{kata_id}", response_class=HTMLResponse)
async def kata_detail(request: Request, kata_id: str):
    kata = get_kata(kata_id)
    if not kata:
        return HTMLResponse("<h1>Kata not found</h1>", status_code=404)

    code = kata["user_code"] or kata["skeleton_code"] or kata["original_code"]
    is_modified = kata["user_code"] is not None
    tutorial_html = render_tutorial(kata["tutorial_path"]) if kata["tutorial_path"] else ""

    # Find prev/next katas
    all_katas = get_all_katas()
    current_idx = next((i for i, k in enumerate(all_katas) if k["id"] == kata_id), -1)
    prev_kata = all_katas[current_idx - 1] if current_idx > 0 else None
    next_kata = all_katas[current_idx + 1] if current_idx < len(all_katas) - 1 else None

    return templates.TemplateResponse("kata_detail.html", {
        "request": request,
        "kata": kata,
        "code": code,
        "is_modified": is_modified,
        "tutorial_html": tutorial_html,
        "prev_kata": prev_kata,
        "next_kata": next_kata,
        "pygments_css": HtmlFormatter().get_style_defs(".highlight"),
    })


@app.post("/kata/{kata_id}/run", response_class=HTMLResponse)
async def run_kata(request: Request, kata_id: str, code: str = Form(...)):
    kata = get_kata(kata_id)
    if not kata:
        return HTMLResponse("<pre>Kata not found</pre>", status_code=404)

    # Save user code if modified
    if code != kata["original_code"]:
        save_user_code(kata_id, code)

    result = run_code(code)
    save_run(kata_id, code, result.stdout, result.stderr, result.exit_code, result.duration_ms)

    return templates.TemplateResponse("partials/output.html", {
        "request": request,
        "result": result,
    })


@app.post("/kata/{kata_id}/reset", response_class=HTMLResponse)
async def reset_kata(kata_id: str):
    original = reset_user_code(kata_id)
    return HTMLResponse(original)


@app.post("/kata/{kata_id}/save", response_class=HTMLResponse)
async def save_kata(kata_id: str, code: str = Form(...)):
    save_user_code(kata_id, code)
    return HTMLResponse('<span class="saved-indicator">Saved</span>')


@app.post("/kata/{kata_id}/solution")
async def show_solution(kata_id: str):
    code = get_solution(kata_id)
    if not code:
        return HTMLResponse("Kata not found", status_code=404)
    return HTMLResponse(code, media_type="text/plain")


@app.post("/kata/{kata_id}/skeleton")
async def show_skeleton(kata_id: str):
    code = get_skeleton(kata_id)
    if not code:
        return HTMLResponse("Kata not found", status_code=404)
    return HTMLResponse(code, media_type="text/plain")


# --- JSON API ---


@app.get("/api/katas")
async def api_list_katas():
    return get_all_katas()


@app.get("/api/kata/{kata_id}")
async def api_get_kata(kata_id: str):
    kata = get_kata(kata_id)
    if not kata:
        return {"error": "not found"}
    return kata


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9999, reload=True)
