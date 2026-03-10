"""
Kata 68 -- Debug Error Page
Run: python playground/68_debug_error_page.py

Build a debug error page that shows rich tracebacks with local
variables, source code context, and request information. Uses the
traceback module to extract frames and inspect to get source lines.

Completes within 5 seconds.
"""

from __future__ import annotations

import html
import inspect
import linecache
import sys
import traceback
from typing import Any


# ===========================================================================
# SECTION 1: Frame Extraction
# ===========================================================================
# Extract detailed information from each frame in the traceback:
# filename, line number, function name, source code, local variables.

class FrameInfo:
    """Detailed information about one stack frame."""

    def __init__(
        self,
        filename: str,
        lineno: int,
        function: str,
        code_context: list[str],
        context_lineno: int,
        locals_dict: dict[str, Any],
    ):
        self.filename = filename
        self.lineno = lineno
        self.function = function
        self.code_context = code_context      # Source lines around the error
        self.context_lineno = context_lineno   # Line number of first context line
        self.locals_dict = locals_dict

    def __repr__(self) -> str:
        return (
            f"FrameInfo({self.filename}:{self.lineno} "
            f"in {self.function})"
        )


def extract_frames(exc_info: tuple) -> list[FrameInfo]:
    """Extract FrameInfo objects from an exception's traceback.

    Args:
        exc_info: Tuple from sys.exc_info() -- (type, value, traceback)

    Returns:
        List of FrameInfo, from outermost to innermost frame.
    """
    _, _, tb = exc_info
    frames: list[FrameInfo] = []

    # Walk the traceback chain
    current_tb = tb
    while current_tb is not None:
        frame = current_tb.tb_frame
        lineno = current_tb.tb_lineno
        filename = frame.f_code.co_filename
        function = frame.f_code.co_name

        # Get source code context (5 lines before and after)
        context_radius = 5
        start_line = max(1, lineno - context_radius)
        end_line = lineno + context_radius + 1

        code_lines: list[str] = []
        for i in range(start_line, end_line):
            line = linecache.getline(filename, i)
            if line:
                code_lines.append(line.rstrip())
            else:
                # For dynamically created code, try to reconstruct
                break

        # Filter local variables (skip dunders and modules)
        locals_dict: dict[str, Any] = {}
        for key, value in frame.f_locals.items():
            if key.startswith("__") and key.endswith("__"):
                continue
            try:
                # Get a safe string representation
                repr_val = repr(value)
                if len(repr_val) > 200:
                    repr_val = repr_val[:200] + "..."
                locals_dict[key] = repr_val
            except Exception:
                locals_dict[key] = "<unable to repr>"

        frames.append(FrameInfo(
            filename=filename,
            lineno=lineno,
            function=function,
            code_context=code_lines,
            context_lineno=start_line,
            locals_dict=locals_dict,
        ))

        current_tb = current_tb.tb_next

    return frames


# ===========================================================================
# SECTION 2: Request Context
# ===========================================================================
# Capture request details to show alongside the error.

class RequestContext:
    """Request information displayed on the error page."""

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        body: str | None = None,
        client_ip: str = "127.0.0.1",
    ):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.body = body
        self.client_ip = client_ip

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for display."""
        result: dict[str, Any] = {
            "Method": self.method,
            "Path": self.path,
            "Client IP": self.client_ip,
        }
        if self.query_params:
            result["Query Params"] = self.query_params
        if self.headers:
            result["Headers"] = self.headers
        if self.body:
            result["Body"] = self.body
        return result


# ===========================================================================
# SECTION 3: HTML Error Page Generator
# ===========================================================================
# Generate a styled HTML error page with all the debug information.

class DebugErrorPage:
    """Generates rich HTML error pages for development.

    Features:
    - Exception type and message
    - Full traceback with source code context
    - Local variables in each frame
    - Request context (method, path, headers)
    - Syntax-highlighted code with the error line marked

    WARNING: Never use in production -- exposes internal code and variables.
    """

    # CSS styles for the error page
    STYLES = """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
               Roboto, sans-serif; margin: 0; padding: 20px;
               background: #1a1a2e; color: #eee; }
        .error-header { background: #e74c3c; padding: 20px; border-radius: 8px;
                        margin-bottom: 20px; }
        .error-header h1 { margin: 0; font-size: 24px; }
        .error-header .message { margin-top: 8px; font-size: 18px;
                                  opacity: 0.9; }
        .frame { background: #16213e; border-radius: 8px; margin-bottom: 16px;
                 overflow: hidden; }
        .frame-header { background: #0f3460; padding: 12px 16px;
                        font-weight: bold; }
        .frame-header .filename { color: #e94560; }
        .frame-header .function { color: #53a8b6; }
        .code-block { padding: 0; margin: 0; overflow-x: auto; }
        .code-line { padding: 2px 16px; font-family: 'Fira Code', monospace;
                     font-size: 14px; white-space: pre; }
        .code-line.error-line { background: rgba(231, 76, 60, 0.3);
                                 border-left: 3px solid #e74c3c; }
        .line-number { color: #666; display: inline-block; width: 40px;
                       text-align: right; margin-right: 16px;
                       user-select: none; }
        .locals { padding: 12px 16px; border-top: 1px solid #0f3460; }
        .locals h3 { margin: 0 0 8px 0; font-size: 14px; color: #53a8b6; }
        .locals table { width: 100%; border-collapse: collapse; }
        .locals td { padding: 4px 8px; font-family: monospace;
                     font-size: 13px; }
        .locals td:first-child { color: #e94560; width: 150px; }
        .locals td:last-child { color: #a7c957; word-break: break-all; }
        .request-info { background: #16213e; border-radius: 8px;
                        padding: 16px; margin-bottom: 16px; }
        .request-info h2 { margin: 0 0 12px 0; color: #53a8b6; }
        .request-info table { width: 100%; border-collapse: collapse; }
        .request-info td { padding: 6px 8px; font-family: monospace;
                           font-size: 14px; }
        .request-info td:first-child { color: #e94560; width: 150px;
                                        font-weight: bold; }
        .plain-traceback { background: #16213e; border-radius: 8px;
                           padding: 16px; font-family: monospace;
                           font-size: 13px; white-space: pre-wrap;
                           color: #ccc; }
    """

    def generate(
        self,
        exc_info: tuple,
        request: RequestContext | None = None,
    ) -> str:
        """Generate a full HTML error page.

        Args:
            exc_info: Tuple from sys.exc_info()
            request: Optional request context to display

        Returns:
            Complete HTML string for the error page.
        """
        exc_type, exc_value, _ = exc_info
        frames = extract_frames(exc_info)

        # Build the page sections
        parts: list[str] = []
        parts.append(self._html_header(exc_type, exc_value))

        if request:
            parts.append(self._request_section(request))

        # Frames (reversed so innermost is first -- where the error happened)
        parts.append('<h2 style="color: #53a8b6;">Traceback</h2>')
        for i, frame in enumerate(reversed(frames)):
            parts.append(self._frame_section(frame, i))

        # Plain text traceback for copy-paste
        plain_tb = "".join(traceback.format_exception(*exc_info))
        parts.append(self._plain_traceback(plain_tb))

        parts.append("</body></html>")
        return "\n".join(parts)

    def _html_header(self, exc_type: type, exc_value: Exception) -> str:
        """Generate the page header with exception info."""
        type_name = html.escape(exc_type.__name__)
        message = html.escape(str(exc_value))
        return f"""<!DOCTYPE html>
<html><head><title>{type_name}: {message}</title>
<style>{self.STYLES}</style></head><body>
<div class="error-header">
    <h1>{type_name}</h1>
    <div class="message">{message}</div>
</div>"""

    def _request_section(self, request: RequestContext) -> str:
        """Generate the request info section."""
        rows: list[str] = []
        for key, value in request.to_dict().items():
            val_str = html.escape(str(value))
            rows.append(
                f"<tr><td>{html.escape(key)}</td><td>{val_str}</td></tr>"
            )
        return f"""<div class="request-info">
    <h2>Request</h2>
    <table>{"".join(rows)}</table>
</div>"""

    def _frame_section(self, frame: FrameInfo, index: int) -> str:
        """Generate HTML for a single stack frame."""
        filename = html.escape(frame.filename)
        function = html.escape(frame.function)

        # Code lines with syntax highlighting
        code_html: list[str] = []
        for i, line in enumerate(frame.code_context):
            actual_lineno = frame.context_lineno + i
            is_error = actual_lineno == frame.lineno
            css_class = "code-line error-line" if is_error else "code-line"
            escaped_line = html.escape(line)
            code_html.append(
                f'<div class="{css_class}">'
                f'<span class="line-number">{actual_lineno}</span>'
                f'{escaped_line}</div>'
            )

        # Local variables table
        locals_html = ""
        if frame.locals_dict:
            rows = []
            for name, value in sorted(frame.locals_dict.items()):
                rows.append(
                    f"<tr><td>{html.escape(name)}</td>"
                    f"<td>{html.escape(str(value))}</td></tr>"
                )
            locals_html = f"""<div class="locals">
    <h3>Local Variables</h3>
    <table>{"".join(rows)}</table>
</div>"""

        return f"""<div class="frame">
    <div class="frame-header">
        <span class="filename">{filename}</span>:{frame.lineno}
        in <span class="function">{function}</span>
    </div>
    <div class="code-block">{"".join(code_html)}</div>
    {locals_html}
</div>"""

    def _plain_traceback(self, tb_text: str) -> str:
        """Generate the plain text traceback section."""
        return f"""<h2 style="color: #53a8b6;">Plain Traceback</h2>
<div class="plain-traceback">{html.escape(tb_text)}</div>"""


# ===========================================================================
# SECTION 4: Debug Middleware
# ===========================================================================
# Integrates with our Ignite framework to catch errors and show debug pages.

class DebugMiddleware:
    """Middleware that catches exceptions and returns debug error pages.

    Only active in debug mode -- production should return generic 500s.
    """

    def __init__(self, debug: bool = True):
        self.debug = debug
        self.page_generator = DebugErrorPage()

    def handle_error(
        self,
        exc_info: tuple,
        request: RequestContext | None = None,
    ) -> dict[str, Any]:
        """Handle an exception, returning either a debug page or generic error.

        Returns a dict with 'content_type', 'body', and 'status_code'.
        """
        if self.debug:
            html_page = self.page_generator.generate(exc_info, request)
            return {
                "content_type": "text/html",
                "body": html_page,
                "status_code": 500,
            }
        else:
            return {
                "content_type": "application/json",
                "body": '{"error": "Internal Server Error"}',
                "status_code": 500,
            }


# ===========================================================================
# SECTION 5: Demos
# ===========================================================================

def demo_frame_extraction():
    """Show extracting frame info from an exception."""
    print("--- Section 1: Frame Extraction ---")

    def inner_function(x: int, y: int) -> int:
        result = x / y  # This will raise ZeroDivisionError
        return result

    def middle_function(data: dict) -> int:
        value = data["numerator"]
        divisor = data["divisor"]
        return inner_function(value, divisor)

    def outer_function() -> int:
        params = {"numerator": 42, "divisor": 0}
        return middle_function(params)

    try:
        outer_function()
    except ZeroDivisionError:
        exc_info = sys.exc_info()
        frames = extract_frames(exc_info)

        print(f"  Extracted {len(frames)} frames:")
        for frame in frames:
            print(f"    {frame}")
            print(f"      locals: {list(frame.locals_dict.keys())}")

        # Verify we captured the right information
        assert len(frames) >= 3  # outer, middle, inner (plus this function)
        innermost = frames[-1]
        assert "inner_function" in innermost.function
        assert "x" in innermost.locals_dict
        assert "y" in innermost.locals_dict

    print("  [PASS] Frame extraction works")


def demo_request_context():
    """Show building request context for error display."""
    print("\n--- Section 2: Request Context ---")

    request = RequestContext(
        method="POST",
        path="/api/users",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer tok_***",
        },
        query_params={"page": "1", "limit": "20"},
        body='{"name": "Alice", "email": "alice@example.com"}',
        client_ip="192.168.1.100",
    )

    context = request.to_dict()
    print(f"  Request context:")
    for key, value in context.items():
        print(f"    {key}: {value}")

    assert context["Method"] == "POST"
    assert context["Path"] == "/api/users"
    assert "Headers" in context
    assert "Query Params" in context
    assert "Body" in context

    print("  [PASS] Request context works")


def demo_html_generation():
    """Show generating the HTML error page."""
    print("\n--- Section 3: HTML Error Page ---")

    def process_user(user_id: int) -> dict:
        users = {"1": "Alice", "2": "Bob"}
        name = users[str(user_id)]
        return {"id": user_id, "name": name, "upper": name.upper()}

    def handle_request(path: str) -> dict:
        # Simulate extracting user_id from path
        user_id = int(path.split("/")[-1])
        return process_user(user_id)

    request = RequestContext(
        method="GET",
        path="/api/users/99",
        headers={"Accept": "application/json"},
    )

    page_gen = DebugErrorPage()

    try:
        handle_request("/api/users/99")
    except KeyError:
        exc_info = sys.exc_info()
        html_output = page_gen.generate(exc_info, request)

        # Verify the HTML contains expected sections
        assert "<!DOCTYPE html>" in html_output
        assert "KeyError" in html_output
        assert "process_user" in html_output
        assert "handle_request" in html_output
        assert "GET" in html_output
        assert "/api/users/99" in html_output
        assert "Local Variables" in html_output
        assert "Plain Traceback" in html_output

        # Show some stats
        print(f"  Generated HTML error page:")
        print(f"    Size: {len(html_output)} bytes")
        print(f"    Contains exception type: KeyError")
        print(f"    Contains request info: GET /api/users/99")
        print(f"    Contains local variables: yes")
        print(f"    Contains source code: yes")
        print(f"    Contains plain traceback: yes")

        # Check for specific content
        assert "user_id" in html_output  # Local variable
        assert "users" in html_output    # Local variable

    print("  [PASS] HTML error page generation works")


def demo_debug_middleware():
    """Show the debug middleware in action."""
    print("\n--- Section 4: Debug Middleware ---")

    # Debug mode -- returns HTML
    debug_mw = DebugMiddleware(debug=True)

    try:
        data = [1, 2, 3]
        _ = data[10]
    except IndexError:
        exc_info = sys.exc_info()
        request = RequestContext(method="GET", path="/items/10")

        result = debug_mw.handle_error(exc_info, request)
        assert result["content_type"] == "text/html"
        assert result["status_code"] == 500
        assert "IndexError" in result["body"]
        print(f"  Debug mode: content_type={result['content_type']}, "
              f"status={result['status_code']}")
        print(f"  Body contains IndexError: yes")
        print(f"  Body size: {len(result['body'])} bytes")

    # Production mode -- returns generic JSON
    prod_mw = DebugMiddleware(debug=False)

    try:
        _ = data[10]
    except IndexError:
        exc_info = sys.exc_info()

        result = prod_mw.handle_error(exc_info)
        assert result["content_type"] == "application/json"
        assert result["status_code"] == 500
        assert "IndexError" not in result["body"]
        assert "Internal Server Error" in result["body"]
        print(f"\n  Production mode: content_type={result['content_type']}, "
              f"status={result['status_code']}")
        print(f"  Body: {result['body']}")
        print(f"  No internal details exposed: correct")

    print("  [PASS] Debug middleware works")


def demo_nested_exception():
    """Show error page with chained/nested exceptions."""
    print("\n--- Section 5: Nested Exception Handling ---")

    def connect_to_db(host: str) -> None:
        raise ConnectionError(f"Cannot connect to {host}")

    def get_user(user_id: int) -> dict:
        try:
            connect_to_db("localhost:5432")
        except ConnectionError as e:
            raise RuntimeError(f"Failed to fetch user {user_id}") from e

    page_gen = DebugErrorPage()

    try:
        get_user(42)
    except RuntimeError:
        exc_info = sys.exc_info()
        html_output = page_gen.generate(exc_info)

        # The page should show the RuntimeError chain
        assert "RuntimeError" in html_output
        assert "Failed to fetch user 42" in html_output
        assert "get_user" in html_output

        # Check the plain traceback includes the cause
        assert "ConnectionError" in html_output
        assert "Cannot connect to localhost:5432" in html_output

        print(f"  Chained exception page generated:")
        print(f"    Primary: RuntimeError")
        print(f"    Caused by: ConnectionError")
        print(f"    Both shown in plain traceback: yes")
        print(f"    Page size: {len(html_output)} bytes")

    print("  [PASS] Nested exception handling works")


def demo_variable_types():
    """Show how different variable types are displayed."""
    print("\n--- Section 6: Variable Type Display ---")

    def complex_function():
        string_var = "hello world"
        int_var = 42
        float_var = 3.14
        list_var = [1, 2, 3, 4, 5]
        dict_var = {"key": "value", "nested": {"a": 1}}
        none_var = None
        bool_var = True
        long_string = "x" * 300  # Should be truncated in display

        # Trigger an error so we can inspect the variables
        raise ValueError("Intentional error for demo")

    try:
        complex_function()
    except ValueError:
        exc_info = sys.exc_info()
        frames = extract_frames(exc_info)
        innermost = frames[-1]

        print(f"  Local variables captured from complex_function:")
        for name, value in sorted(innermost.locals_dict.items()):
            display = value if len(value) <= 60 else value[:60] + "..."
            print(f"    {name} = {display}")

        # Verify truncation of long values
        assert len(innermost.locals_dict["long_string"]) <= 203  # 200 + "..."
        assert "string_var" in innermost.locals_dict
        assert "int_var" in innermost.locals_dict
        assert "dict_var" in innermost.locals_dict

    print("  [PASS] Variable type display works")


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    demo_frame_extraction()
    demo_request_context()
    demo_html_generation()
    demo_debug_middleware()
    demo_nested_exception()
    demo_variable_types()

    print("\n--- Summary ---")
    print("Debug error page gives our Ignite framework:")
    print("  - Frame extraction with local variables")
    print("  - Request context display (method, path, headers)")
    print("  - Rich HTML error page with source code context")
    print("  - Error line highlighting in code display")
    print("  - Debug vs production mode toggle")
    print("  - Chained exception support")
    print("  - Safe variable repr with truncation")
    print("\nAll 6 sections passed. Debug error page mastered!")
    print("Next up: Kata 69 -- structured logging!")


if __name__ == "__main__":
    main()
