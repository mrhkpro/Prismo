from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_auth_page_uses_versioned_assets_and_theme_support():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "/assets/css/style.css?v=2.6.0" in html
    assert "/assets/js/theme.js?v=2.6.0" in html
    assert "/assets/js/auth.js?v=2.6.0" in html


def test_admin_page_loads_theme_support():
    html = (ROOT / "frontend" / "admin.html").read_text(encoding="utf-8")
    assert "/assets/js/theme.js?v=2.6.0" in html
    assert "/assets/css/style.css?v=2.6.0" in html


def test_theme_script_is_safe_without_local_storage():
    js = (ROOT / "frontend" / "assets" / "js" / "theme.js").read_text(encoding="utf-8")
    assert 'localStorage.getItem(STORAGE_KEY)' in js
    assert 'try { localStorage.setItem(STORAGE_KEY, next); } catch (_) {}' in js
    assert 'root.dataset.theme = getInitialTheme();' in js


def test_api_client_enforces_request_timeout_and_accessible_toast():
    js = (ROOT / "frontend" / "assets" / "js" / "api.js").read_text(encoding="utf-8")
    assert 'timeoutMs = 30000' in js
    assert 'new AbortController()' in js
    assert 'setTimeout(() => controller.abort(), timeoutMs)' in js
    assert 'aria-live' in js


def test_chat_request_waits_without_a_client_deadline_and_explicitly_sends_selected_model():
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert 'timeoutMs: 0' in js
    assert 'selectedModel = CURRENT_SETTINGS && CURRENT_SETTINGS.chat_model' in js
    assert 'model: selectedModel' in js


def test_chat_ui_shows_model_used_by_backend():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert 'activeChatModelBadge' in html
    # مسیر استریم مدل را از رویداد meta می‌گیرد و مسیر پشتیبان (غیراستریم) از پاسخ یک‌جا
    assert 'getElementById("activeChatModelBadge").textContent = meta.model' in js
    assert 'getElementById("activeChatModelBadge").textContent = res.model' in js


def test_chat_streams_with_automatic_fallback_and_stop_button():
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "assets" / "js" / "api.js").read_text(encoding="utf-8")
    assert '/api/playground/chat/stream' in js
    assert 'STREAM_FALLBACK_STATUSES.includes(err.status)' in js
    assert 'CHAT_ABORT.abort()' in js
    assert 'async function apiStream' in api
    assert 'text/event-stream' in api


def test_double_click_guard_and_locks_exist():
    api = (ROOT / "frontend" / "assets" / "js" / "api.js").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    admin = (ROOT / "frontend" / "assets" / "js" / "admin.js").read_text(encoding="utf-8")
    assert 'function once(' in api and 'installClickGuard' in api
    assert 'once(`edit-doc:${id}`' in dashboard
    assert 'once(`inspect:${userId}`' in admin and 'once(`session:${sessionId}`' in admin


def test_file_import_supports_pdf_and_office_formats():
    js = (ROOT / "frontend" / "assets" / "js" / "extract.js").read_text(encoding="utf-8")
    for ext in ("pdf", "docx", "xlsx", "pptx", "odt", "epub", "rtf", "csv", "json", "html"):
        assert f'"{ext}"' in js, ext
    assert (ROOT / "frontend" / "assets" / "vendor" / "pdfjs" / "pdf.min.js").exists()
    assert (ROOT / "frontend" / "assets" / "vendor" / "pdfjs" / "pdf.worker.min.js").exists()
