from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_auth_page_uses_versioned_assets_and_theme_support():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert "/assets/css/style.css?v=2.2.0" in html
    assert "/assets/js/theme.js?v=2.2.0" in html
    assert "/assets/js/auth.js?v=2.2.0" in html


def test_admin_page_loads_theme_support():
    html = (ROOT / "frontend" / "admin.html").read_text(encoding="utf-8")
    assert "/assets/js/theme.js?v=2.2.0" in html
    assert "/assets/css/style.css?v=2.2.0" in html


def test_theme_script_is_safe_without_local_storage():
    js = (ROOT / "frontend" / "assets" / "js" / "theme.js").read_text(encoding="utf-8")
    assert 'localStorage.getItem(STORAGE_KEY)' in js
    assert 'try { localStorage.setItem(STORAGE_KEY, next); } catch (_) {}' in js
    assert 'root.dataset.theme = getInitialTheme();' in js


def test_api_client_enforces_request_timeout_and_accessible_toast():
    js = (ROOT / "frontend" / "assets" / "js" / "api.js").read_text(encoding="utf-8")
    assert 'timeoutMs = 25000' in js
    assert 'new AbortController()' in js
    assert 'setTimeout(() => controller.abort(), timeoutMs)' in js
    assert 'aria-live' in js
