from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_auth_page_uses_versioned_assets_and_theme_support():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "/assets/css/style.css?v=2.6.6" in html
    assert "/assets/js/theme.js?v=2.6.6" in html
    assert "/assets/js/auth.js?v=2.6.6" in html


def test_admin_page_loads_theme_support():
    html = (ROOT / "frontend" / "admin.html").read_text(encoding="utf-8")
    assert "/assets/js/theme.js?v=2.6.6" in html
    assert "/assets/css/style.css?v=2.6.6" in html


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
    assert 'err?.streamError || STREAM_FALLBACK_STATUSES.includes(err?.status)' in js
    assert 'await chatViaRequest(message, selectedModel, bubble);' in js
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


def test_all_entry_pages_are_not_indexed_or_archived():
    for name in ("index.html", "dashboard.html", "admin.html", "setup.html", "widget-preview.html"):
        html = (ROOT / "frontend" / name).read_text(encoding="utf-8")
        assert 'noindex, noarchive, nosnippet, noimageindex' in html


def test_greeting_demo_emoji_is_styled_instead_of_raw_text_only():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert 'class="demo-welcome-emoji"' in html
    assert '.demo-welcome-emoji' in css



def test_embedding_discovery_ui_and_scrollbars():
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    widget = (ROOT / "frontend" / "widget.js").read_text(encoding="utf-8")
    assert "embedding_models" in js
    assert "--qz-stream" in widget
    assert "scrollbar-width: thin" in css


def test_knowledge_upload_has_visible_progress_and_real_upload_tracking():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert 'id="operationProgress"' in html
    assert 'class="operation-progress-bar-fill"' in html
    assert 'XMLHttpRequest()' in js
    assert 'xhr.upload.onprogress' in js


def test_chat_stream_is_enabled_and_markdown_bold_is_rendered_safely():
    dashboard = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    widget = (ROOT / "frontend" / "widget.js").read_text(encoding="utf-8")
    playground = (ROOT / "app" / "routers" / "playground.py").read_text(encoding="utf-8")
    llm = (ROOT / "app" / "services" / "llm_client.py").read_text(encoding="utf-8")
    assert '/api/playground/chat/stream' in dashboard
    assert 'renderChatMarkdown' in dashboard
    assert 'renderChatMarkdown' in widget
    assert 'stream=True' in llm
    assert playground.count('plan = rag_pipeline.prepare_rag_chat') == 1


def test_streaming_ui_has_no_post_completion_typing_cursor():
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    widget = (ROOT / "frontend" / "widget.js").read_text(encoding="utf-8")
    assert 'caret-blink' not in css
    assert 'chat-msg.streaming:not(.pending)::after' not in css
    assert 'qz-msg.streaming::after' not in widget


def test_document_save_progress_is_inside_save_modal():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert 'id="docSaveProgress"' in html
    assert 'ensureDocSaveProgress' in js
    assert 'ensureOperationProgress("در حال ایندکس سند…")' not in js
