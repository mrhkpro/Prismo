from pathlib import Path

from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_google_oauth_api_routes_are_not_registered():
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/auth/google/start" not in paths
    assert "/api/auth/google/callback" not in paths
    assert "/api/auth/google/supabase-callback" not in paths


def test_username_password_auth_routes_remain_registered():
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/auth/logout" in paths
    assert "/api/auth/me" in paths


def test_login_page_and_script_have_no_google_sign_in_ui_or_flow():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "auth.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    assert "googleLoginBtn" not in html
    assert "ادامه با گوگل" not in html
    assert "googleLoginBtn" not in js
    assert "/api/auth/google/" not in js
    assert "auth_error" not in js and "oauth=success" not in js
    assert ".btn-google" not in css
    assert ".auth-google-note" not in css


def test_google_oauth_only_environment_variables_are_removed():
    config = (ROOT / "app" / "config.py").read_text(encoding="utf-8")
    template = (ROOT / ".env.example").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "GOOGLE_CLIENT_ID" not in config
    assert "GOOGLE_CLIENT_SECRET" not in config
    assert "GOOGLE_OAUTH_ENABLED" not in config
    assert "SUPABASE_AUTH_ENABLED" not in config
    assert "GOOGLE_CLIENT_ID" not in template
    assert "SUPABASE_ANON_KEY" not in template
    assert "google-auth" not in requirements


def test_oauth_table_cleanup_migration_preserves_application_tables():
    migration = (ROOT / "supabase" / "migrations" / "006_remove_oauth_identities.sql").read_text(encoding="utf-8")
    assert "DROP TABLE IF EXISTS public.oauth_identities" in migration
    assert "DROP TABLE public.users" not in migration
