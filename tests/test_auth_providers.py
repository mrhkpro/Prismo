from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def _test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    return engine, override_get_db


def test_supabase_google_route_and_existing_auth_routes_are_registered():
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/auth/google-supabase" in paths
    assert "/api/auth/register" in paths
    assert "/api/auth/login" in paths
    assert "/api/auth/logout" in paths
    assert "/api/auth/me" in paths


def test_login_page_and_script_have_google_sign_in_ui_without_replacing_email_auth():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "frontend" / "assets" / "js" / "auth.js").read_text(encoding="utf-8")
    css = (ROOT / "frontend" / "assets" / "css" / "style.css").read_text(encoding="utf-8")
    callback = (ROOT / "frontend" / "auth-callback.html").read_text(encoding="utf-8")
    assert "googleLoginBtn" in html
    assert "ادامه با گوگل" in html
    assert "googleLoginBtn" in js
    assert "auth/v1/authorize?provider=google" in js
    assert ".google-login-btn" in css
    assert ".google-auth-container" in css
    assert "/api/auth/google-supabase" in callback
    assert 'id="loginForm"' in html and 'id="registerForm"' in html
    assert 'apiCall("/api/auth/login"' in js and 'apiCall("/api/auth/register"' in js


def test_supabase_google_login_creates_prismo_session():
    engine, override_get_db = _test_db()
    app.dependency_overrides[get_db] = override_get_db
    mock_supabase_user = {
        "email": "supabase_google_user@example.com",
        "user_metadata": {"full_name": "Supabase Google User"},
    }
    try:
        with patch("app.routers.auth.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_supabase_user
            mock_get.return_value = mock_response
            with TestClient(app) as client:
                response = client.post("/api/auth/google-supabase", json={"supabase_token": "valid-mock-token"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
        mock_get.assert_called_once()
        assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer valid-mock-token"
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_supabase_google_login_rejects_invalid_supabase_token():
    engine, override_get_db = _test_db()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("app.routers.auth.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"message": "invalid token"}
            mock_get.return_value = mock_response
            with TestClient(app) as client:
                response = client.post("/api/auth/google-supabase", json={"supabase_token": "invalid-token"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
