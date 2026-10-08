from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_setup_page_is_separate_and_main_pages_do_not_ask_database_mode():
    setup = (ROOT / "frontend" / "setup.html").read_text(encoding="utf-8")
    index = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend" / "dashboard.html").read_text(encoding="utf-8")
    auth = (ROOT / "frontend" / "assets" / "js" / "auth.js").read_text(encoding="utf-8")
    assert 'data-mode="local"' in setup
    assert 'data-mode="supabase"' in setup
    assert "/__setup/choose" in setup
    assert "<style>" in setup
    assert "/assets/css/style.css" not in setup
    assert "database-mode.js" not in index
    assert "database-mode.js" not in dashboard
    assert "QzDatabaseMode.ready" not in auth


def test_setup_bat_opens_bootstrap_page_instead_of_fastapi_directly():
    bat = (ROOT / "setup.bat").read_text(encoding="utf-8")
    assert "app\\setup_bootstrap.py" in bat
    assert "uvicorn app.main:app" not in bat


def test_vercel_is_never_asked_to_choose_database_in_normal_pages():
    for name in ("index.html", "dashboard.html"):
        html = (ROOT / "frontend" / name).read_text(encoding="utf-8")
        assert "QzDatabaseMode" not in html



def test_setup_bootstrap_uses_separate_setup_port_and_main_port():
    bootstrap = (ROOT / "app" / "setup_bootstrap.py").read_text(encoding="utf-8")
    assert "SETUP_PORT = 8765" in bootstrap
    assert "APP_PORT = 8000" in bootstrap
    assert "/__setup/status" in bootstrap


def test_setup_choice_starts_main_app_on_8000_without_duplicate_response():
    bootstrap = (ROOT / "app" / "setup_bootstrap.py").read_text(encoding="utf-8")
    assert "APP_PORT = 8000" in bootstrap
    assert 'self._json(200, {"ok": True, "mode": mode, "app_port": APP_PORT})' in bootstrap
    assert 'self._json(200, {"ok": True, "mode": mode})' not in bootstrap
    assert "_close_when_ready" in bootstrap
    assert "--no-access-log" in bootstrap
