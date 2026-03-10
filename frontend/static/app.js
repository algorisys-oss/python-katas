/* Python Katas -- HTMX + CodeMirror glue */

function getEditor() {
    const el = document.querySelector('.CodeMirror');
    return el ? el.CodeMirror : null;
}

function runCode(kataId) {
    const cm = getEditor();
    if (!cm) return;

    const code = cm.getValue();
    const output = document.getElementById('code-output');
    output.innerHTML = '<pre class="output-placeholder">Running...</pre>';

    fetch(`/kata/${kataId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'code=' + encodeURIComponent(code),
    })
    .then(r => r.text())
    .then(html => { output.innerHTML = html; })
    .catch(err => {
        output.innerHTML = `<pre class="stderr">Error: ${err.message}</pre>`;
    });
}

function saveCode(kataId) {
    const cm = getEditor();
    if (!cm) return;

    const code = cm.getValue();

    fetch(`/kata/${kataId}/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'code=' + encodeURIComponent(code),
    })
    .then(r => r.text())
    .then(() => {
        // Brief flash to confirm save
        const btn = document.querySelector('.btn-save');
        btn.textContent = 'Saved!';
        setTimeout(() => { btn.textContent = 'Save'; }, 1500);
    });
}

function resetCode(kataId) {
    fetch(`/kata/${kataId}/reset`, { method: 'POST' })
    .then(r => r.text())
    .then(code => {
        const cm = getEditor();
        if (cm) cm.setValue(code);
        const output = document.getElementById('code-output');
        output.innerHTML = '<pre class="output-placeholder">Code reset to original. Click "Run" to execute...</pre>';
        // Remove modified badge if present
        const badge = document.querySelector('.modified-badge');
        if (badge) badge.remove();
    });
}

function showSolution(kataId) {
    fetch(`/kata/${kataId}/solution`, { method: 'POST' })
    .then(r => r.text())
    .then(code => {
        const cm = getEditor();
        if (cm) cm.setValue(code);
    });
}

function loadSkeleton(kataId) {
    fetch(`/kata/${kataId}/skeleton`, { method: 'POST' })
    .then(r => r.text())
    .then(code => {
        const cm = getEditor();
        if (cm) cm.setValue(code);
        const output = document.getElementById('code-output');
        output.innerHTML = '<pre class="output-placeholder">Skeleton loaded. Click "Run" to execute...</pre>';
    });
}

// Panel minimize/maximize toggle
function togglePanel(panelClass) {
    const panel = document.querySelector('.' + panelClass);
    if (!panel) return;

    const otherClass = panelClass === 'tutorial-panel' ? 'editor-panel' : 'tutorial-panel';
    const other = document.querySelector('.' + otherClass);
    const btn = panel.querySelector('.panel-toggle');

    panel.classList.toggle('minimized');

    if (panel.classList.contains('minimized')) {
        btn.innerHTML = '&#x002B;'; // +
        btn.title = 'Maximize';
        if (other) other.classList.add('expanded');
    } else {
        btn.innerHTML = '&#x2212;'; // −
        btn.title = 'Minimize';
        if (other) other.classList.remove('expanded');
    }

    // Refresh CodeMirror if editor panel is being expanded
    if (panelClass === 'editor-panel' || otherClass === 'editor-panel') {
        setTimeout(function() {
            var cm = getEditor();
            if (cm) cm.refresh();
        }, 350);
    }
}

// Fullscreen maximize toggle
function maximizePanel(panelClass) {
    const panel = document.querySelector('.' + panelClass);
    if (!panel) return;

    const panels = document.querySelector('.panels');
    const btn = panel.querySelector('.panel-maximize');

    panel.classList.toggle('fullscreen');

    if (panel.classList.contains('fullscreen')) {
        panels.classList.add('has-fullscreen');
        btn.innerHTML = '&#x2716;'; // ✖
        btn.title = 'Exit Fullscreen';
        document.body.style.overflow = 'hidden';
    } else {
        panels.classList.remove('has-fullscreen');
        btn.innerHTML = '&#x2922;'; // ⤢
        btn.title = 'Fullscreen';
        document.body.style.overflow = '';
    }

    // Refresh CodeMirror after layout change
    setTimeout(function() {
        var cm = getEditor();
        if (cm) cm.refresh();
    }, 100);
}

// Keyboard shortcuts (global)
document.addEventListener('keydown', function(e) {
    // Escape to exit fullscreen
    if (e.key === 'Escape') {
        var fs = document.querySelector('.panel.fullscreen');
        if (fs) {
            var cls = fs.classList.contains('tutorial-panel') ? 'tutorial-panel' : 'editor-panel';
            maximizePanel(cls);
        }
    }
    // Ctrl/Cmd + Enter to run (when not in CodeMirror, which handles its own)
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const runBtn = document.querySelector('.btn-run');
        if (runBtn) runBtn.click();
    }
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const saveBtn = document.querySelector('.btn-save');
        if (saveBtn) saveBtn.click();
    }
});
