from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_auth_page_uses_versioned_assets_and_theme_support():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "/assets/css/style.css?v=2.8.9" in html
    assert "/assets/js/theme.js?v=2.8.9" in html
    assert "/assets/js/auth.js?v=2.8.9" in html


def test_admin_page_loads_theme_support():
    html = (ROOT / "frontend" / "admin.html").read_text(encoding="utf-8")
    assert "/assets/js/theme.js?v=2.8.9" in html
    assert "/assets/css/style.css?v=2.8.9" in html
    assert 'data-admin-dark-only="1"' in html
    assert 'id="themeToggle"' not in html
    assert 'id="sessionModalBody" class="chat-stream" aria-live="polite"' in html
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert "#sessionModal .modal-box" in css
    assert "max-width: 640px" in css
    assert "#sessionModal #sessionModalBody.chat-stream" in css


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
    assert "meta.model || selectedModel" in js
    assert "res.model || selectedModel" in js


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


def test_widget_embed_rendering_is_safe_when_embed_box_is_temporarily_missing():
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert 'const box = widgetEl("embedCodeBox");' in js
    assert 'if (!box) return;' in js
    assert 'const text = box.textContent;' in js


def test_toast_bar_is_pinned_to_the_top_and_save_has_no_inline_text():
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    host = css[css.index(".toast-host {"):]
    host = host[: host.index("}")]
    assert "top: 12px" in host and "bottom" not in host
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert "widgetDirtyHint" not in html and "widgetDirtyHint" not in js
    assert 'classList.toggle("has-changes"' in js



def test_english_settings_dictionary_covers_requested_dashboard_copy_and_admin_calendar():
    settings = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    admin = (ROOT / "frontend" / "assets" / "js" / "admin.js").read_text(encoding="utf-8")
    for source in (
        "پنل مدیریت",
        "این کد را پیش از </body> هر صفحه‌ی وب‌سایتت بگذار.",
        "قبل از انتشار ویجت، رفتار دستیار را همین‌جا امتحان کن.",
        "هنوز سندی اضافه نکرده‌ای",
        "این پروژه سه بخش اصلی داره — همه رو از منوی کناری در دسترس داری.",
    ):
        assert source in settings
    assert 'en-US-u-ca-gregory-nu-latn' in admin
    assert 'qz-language-change' in admin
    assert 'function latinizeUiNumbers' in settings


def test_battle_streaming_and_gradual_knowledge_progress_are_wired():
    router = (ROOT / "app" / "routers" / "playground.py").read_text(encoding="utf-8")
    api = (ROOT / "frontend" / "assets" / "js" / "api.js").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert '@router.post("/battle/stream")' in router
    assert 'llm_client.stream_chat_completion(messages, provider, model=model)' in router
    assert 'onEvent(event, data)' in api
    assert '/api/playground/battle/stream' in dashboard
    assert 'startDocProgressEstimator()' in dashboard
    assert 'Math.min(89, Math.floor(89 * (1 - Math.exp(-elapsedSeconds / 35))))' in dashboard
    assert 'stopDocProgressEstimator()' in dashboard


def test_saved_custom_model_is_rehydrated_for_battle_and_english_widget_labels():
    dashboard = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    assert "const savedCustomModel = !chatUsesDefault && s.chat_model ? s.chat_model : \"\";" in dashboard
    assert 'fillModelSelect(document.getElementById("battleModelB"), battleModels' in dashboard
    assert '{ dog: "Dog", cat: "Cat", raccoon: "Raccoon" }' in dashboard
    assert 'embedCodeBox.textContent = english ? "Loading…" : "در حال بارگذاری…";' in dashboard
    assert 'dashboard.js?v=2.8.17' in html


def test_widget_quick_replies_do_not_keep_the_streaming_caret():
    widget = (ROOT / "frontend" / "widget.js").read_text(encoding="utf-8")
    start = widget.index('var quickReply = getQuickReply(text);')
    end = widget.index('sendBtn.disabled = true;', start)
    quick_branch = widget[start:end]
    assert 'pending.classList.remove("pending", "streaming")' in quick_branch
    assert 'pending.classList.add("streaming")' not in quick_branch


def test_ai_connection_actions_appear_after_chat_and_embedding_configuration():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    start = html.index('id="aitab-connect"')
    end = html.index('id="aitab-battle"', start)
    connection = html[start:end]
    actions = connection.index('class="ai-connection-actions"')
    for control in (
        'id="chatModelSelect"',
        'id="customChatModelSelect"',
        'id="embeddingModelSelect"',
        'id="customEmbeddingModelSelect"',
    ):
        assert connection.index(control) < actions, f"{control} must come before the final action area"
    for action in ("saveProviderBtn", "saveCustomProviderBtn", "testConnectionBtn", "testCustomConnectionBtn"):
        assert connection.index(f'id="{action}"') > actions, f"{action} must appear at the end of the form"
    assert 'style.display = useDefault ? "inline-flex" : "none"' in js
    assert 'style.display = useDefault ? "none" : "inline-flex"' in js
    assert 'aria-pressed' in connection
    assert 'role="tablist" aria-label="بخش‌های هوش مصنوعی"' in html
    assert '>تنظیم مدل‌ها</div>' in html
    assert 'ArrowLeft' in js and 'ArrowRight' in js and 'aria-selected' in js
    assert 'مرحله ۳ · پایان تنظیمات' in connection


def test_ai_connection_layout_has_mobile_responsive_styles():
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert '#aitab-connect .ai-config-card' in css
    assert '#aitab-connect .ai-connection-actions' in css
    assert '@media (max-width:760px)' in css
    assert '#aitab-connect .ai-action-buttons .btn { flex:1 1 100%; }' in css


def test_ai_connection_copy_is_translated_for_english_ui():
    settings = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    for source, target in (
        ("اتصال مدل چت", "Connect chat model"),
        ("مدل جست‌وجوی دانشنامه (Embedding)", "Knowledge retrieval model (Embedding)"),
        ("ذخیره و فعال‌سازی", "Save and activate"),
        ("تنظیم مدل‌ها", "Model setup"),
        ("همه‌چیز آماده است؟", "Ready to go?"),
    ):
        assert source in settings and target in settings


def test_vercel_rag_chat_uses_bounded_json_path_and_ready_models_are_marked_local_only():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    translations = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    note = "توجه:</strong> این مدل‌های آماده هنگام ورود و استفاده از نسخهٔ سایت کار نمی‌کنند."
    install_note = "برای استفاده از مدل‌های آماده، پروژه را از GitLab دریافت و نصب کن و آن را به‌صورت لوکال، با Supabase یا بدون Supabase، اجرا کن."
    assert "/api/runtime" in js and "PRISMO_IS_VERCEL_RUNTIME" in js
    assert "await chatViaRequest(message, selectedModel, bubble, 65000)" in js
    assert 'bubble.dataset.hasText = "1";' in js and 'if (!reply) {' in js
    assert html.count(note) == 2
    assert html.count(install_note) == 2
    assert "مدل‌های چت ذخیره‌شدهٔ من" in html and "مدل‌های Embedding ذخیره‌شدهٔ من" in html
    assert "saved-embedding-models" in js
    assert "renderSavedChatModels(SAVED_CHAT_MODELS, loadError)" in js
    assert "saved-chat-models-retry" in js
    assert "توجه: این مدل‌های آماده هنگام ورود و استفاده از نسخهٔ سایت کار نمی‌کنند." in translations
    assert "/assets/js/dashboard.js?v=2.8.17" in html
    assert "v2.8.9" in html


def test_empty_model_reply_is_never_rendered_as_an_empty_chat_bubble():
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    translations = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    assert 'typeof res?.reply === "string" ? res.reply.trim() : ""' in js
    assert 'throw new Error(window.QZI18n ? window.QZI18n.t(message) : message)' in js
    assert "The model returned no visible text." in translations
    backend = (ROOT / "app" / "services" / "llm_client.py").read_text(encoding="utf-8")
    assert 'for attempt in range(2)' in backend
    assert 'provider_empty_chat_response' in backend
    assert 'مدل پاسخ متنی برنگرداند' in backend


def test_dashboard_home_refresh_keeps_live_bindings_and_quick_actions():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    translations = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    for element_id in ("ovDocCount", "ovChunkCount", "ovMessageCount", "ovPlaygroundSessions", "ovWidgetSessions", "ovProvider", "ovWidgetStatus"):
        assert f'id="{element_id}"' in html
    for section in ("overview-hero", "overview-stats-grid", "overview-health-panel", "overview-quick-grid"):
        assert section in html
        assert f"#view-overview .{section}" in css or section == "overview-health-panel"
    for route in ("knowledge", "test-lab", "widget"):
        assert f"Nav.go('{route}')" in html
    assert 'data-i18n-en="Turn your knowledge into an AI assistant"' in html
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in css
    assert "@media (max-width: 420px)" in css
    assert 'document.querySelectorAll("[data-i18n-fa][data-i18n-en]")' in translations


def test_admin_page_has_persistent_security_report_entrypoint():
    root = Path(__file__).resolve().parents[1]
    html = (root / "frontend" / "admin.html").read_text(encoding="utf-8")
    js = (root / "frontend" / "assets" / "js" / "admin.js").read_text(encoding="utf-8")
    css = (root / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert 'id="securityFloatingAlert"' in html
    assert 'id="securityFloatingCount"' in html
    assert 'Nav.go("security")' in js
    assert '.security-floating-alert[data-severity="critical"]' in css



def test_dashboard_shell_shows_persistent_admin_security_alert_outside_admin_page():
    root = Path(__file__).resolve().parents[1]
    shell = (root / "frontend" / "assets" / "js" / "shell.js").read_text(encoding="utf-8")
    admin = (root / "frontend" / "assets" / "js" / "admin.js").read_text(encoding="utf-8")
    css = (root / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert "initGlobalAdminThreatAlert();" in shell
    assert 'apiCall("/api/admin/security/summary"' in shell
    assert '"/admin.html#security"' in shell
    assert '.global-threat-alert[data-severity="critical"]' in css or '.global-threat-alert[data-severity="medium"]' in css
    assert "Nav.go(requestedView)" in admin


def test_ai_settings_shows_active_models_and_saved_model_use_test_actions():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    for element_id in (
        "activeChatModelName", "activeChatModelMeta", "activeChatModelBadge",
        "activeEmbeddingModelName", "activeEmbeddingModelMeta", "activeEmbeddingModelBadge",
    ):
        assert f'id="{element_id}"' in html
    assert '"/api/settings/saved-chat-models/use"' in js
    assert '"/api/settings/saved-chat-models/test"' in js
    assert '"/api/settings/saved-embedding-models/use"' in js
    assert '"/api/settings/saved-embedding-models/test"' in js
    assert 'savedModelActionButton(kind, entry, "use")' in js
    assert 'savedModelActionButton(kind, entry, "test")' in js
    assert ".ai-active-model-grid" in css and ".saved-model-action-btn" in css


def test_account_panel_does_not_expose_admin_shortcut_to_regular_users():
    html = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    account_actions = html.split('class="panel-foot account-actions"', 1)[1].split("</div>", 1)[0]
    assert 'id="logoutBtn"' in account_actions
    assert 'پنل ادمین' not in account_actions
    assert 'id="openAdminLink"' not in html
