from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_supabase_startup_has_no_schema_mutation_or_seed_path():
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    lifespan = source.split("async def lifespan", 1)[1].split("# ============================================================\n# APPLICATION", 1)[0]
    assert "if not config.IS_POSTGRES" in lifespan
    assert lifespan.count("Base.metadata.create_all") == 1
    assert lifespan.count("seed_admin(db)") == 1
    # Both operations must be inside the SQLite-only branch; no Postgres schema work.
    assert lifespan.index("Base.metadata.create_all") > lifespan.index("if not config.IS_POSTGRES")
    assert lifespan.index("seed_admin(db)") > lifespan.index("if not config.IS_POSTGRES")


def test_language_switch_pauses_observer_and_does_not_translate_parent_for_each_character_mutation():
    js = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    assert "translationObserver.disconnect()" in js
    assert "translationObserver.observe(document.body" in js
    assert "translateNode(document.body, true)" in js
    # Regression guard for the old O(n^2) observer behavior that re-translated the whole parent.
    assert "translateNode(m.target.parentElement)" not in js
    assert "isTranslating" in js


def test_postgres_lifespan_does_not_touch_schema_or_seed(monkeypatch):
    import asyncio
    from app import config, main

    monkeypatch.setattr(config, "IS_POSTGRES", True)

    def fail(*_args, **_kwargs):
        raise AssertionError("Supabase startup must not mutate or inspect the schema")

    monkeypatch.setattr(main.Base.metadata, "create_all", fail)
    monkeypatch.setattr(main, "seed_admin", fail)

    async def run_lifespan():
        async with main.lifespan(None):
            return

    asyncio.run(run_lifespan())


def test_translation_dictionary_covers_admin_lab_widget_and_setup_critical_text():
    js = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    critical = [
        ("پنل ادمین", "Admin panel"),
        ("آزمایشگاه تست داخلی", "Internal test lab"),
        ("پیام خوش‌آمدگویی", "Welcome message"),
        ("پرامپت سیستمی (نقش و لحن دستیار)", "System prompt (role & tone)"),
        ("مدیریت و پایش کاربران", "User management and monitoring"),
        ("تنظیمات ذخیره نشد.", "Settings were not saved."),
        ("مثلاً: فروشگاه آنلاین رویا", "e.g. Online Roya Store"),
    ]
    for fa, en in critical:
        assert fa in js and en in js


def test_translation_observer_disconnects_before_processing_mutations_to_prevent_feedback_loops():
    js = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    observer = js.split("translationObserver = new MutationObserver", 1)[1].split("window.QZI18n", 1)[0]
    assert observer.count("translationObserver.disconnect()") >= 1
    assert observer.count("translationObserver.observe(document.body") >= 1
    assert "isTranslating = true" in observer
    assert "translateNode(n, true)" in observer
    assert "translateNode(m.target.parentElement)" not in observer


def test_widget_has_real_english_user_facing_fallbacks():
    js = (ROOT / "frontend" / "widget.js").read_text(encoding="utf-8")
    assert 'title: "Smart Assistant"' in js
    assert 'welcome: "Hello! How can I help you?"' in js
    assert 'petLabel: "Widget pet — click to show some love"' in js
    assert 'settingsUnavailable: "Widget settings could not be loaded. Check the server connection."' in js
    assert 'console.error("[Quasar widget]' in js


def test_settings_and_rag_localize_built_in_defaults_for_english_requests(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import patch
    from app import config
    from app.services import rag_pipeline

    settings = SimpleNamespace(
        chat_model="test-chat",
        temperature=0.7,
        top_k=4,
        similarity_threshold=0.25,
        system_prompt=config.DEFAULT_SYSTEM_PROMPT,
    )
    owner = SimpleNamespace(id=42, settings=settings)
    session = SimpleNamespace(messages=[])

    with patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=SimpleNamespace(chat_model="test-chat", embedding_model="embed")):
        with patch.object(rag_pipeline.llm_client, "embed_text", return_value=[0.1]):
            with patch.object(rag_pipeline.rag_store, "search", return_value=[]):
                plan = rag_pipeline.prepare_rag_chat(None, owner, session, "A knowledge question", language="en")

    assert plan.messages == []
    assert plan.no_answer
    assert not any("فارسی" in str(x) for x in plan.messages)


def test_legacy_settings_schema_works_without_optional_provider_columns():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.services import user_settings_compat

    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE user_settings (
                user_id INTEGER PRIMARY KEY,
                use_default_provider BOOLEAN, api_key VARCHAR(255), base_url VARCHAR(255),
                chat_model VARCHAR(120), embedding_model VARCHAR(120), system_prompt TEXT,
                temperature FLOAT, top_k INTEGER, similarity_threshold FLOAT,
                widget_id VARCHAR(64), widget_title VARCHAR(120),
                widget_welcome_message TEXT, widget_color VARCHAR(20)
            )
        """)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        row = user_settings_compat.ensure_settings(db, 1)
        assert row.user_id == 1
        assert user_settings_compat.optional_columns(db) == set()
        updated = user_settings_compat.update_settings(db, 1, {"chat_model": "legacy-chat", "embedding_api_key": "ignored"})
        assert updated.chat_model == "legacy-chat"
        assert db.execute(text("select chat_model from user_settings where user_id=1")).scalar_one() == "legacy-chat"
    finally:
        db.close()


def test_english_mode_covers_mixed_admin_labels_and_dynamic_upload_progress():
    settings = (ROOT / "frontend" / "assets" / "js" / "settings.js").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend" / "assets" / "js" / "dashboard.js").read_text(encoding="utf-8")
    for fa, en in [
        ("پنل Administration", "Admin panel"),
        ("پاسخی دریافت نشد.", "No response received."),
        ("✓ اضافه شد", "✓ Added"),
    ]:
        assert fa in settings and en in settings
    assert 'window.QZSettings.isEnglish() ? "%" : "٪"' in dashboard
    assert 'englishUI ? `✓ ${parts.length} sections added`' in dashboard
    assert 'englishUI ? "✓ Added" : "✓ اضافه شد"' in dashboard
