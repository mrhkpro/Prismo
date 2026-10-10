import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config, models
from app.database import Base, get_db
from app.main import app
from app.routers import auth as auth_router


class GoogleOAuthTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        self.config_patchers = [
            patch.object(config, "GOOGLE_OAUTH_ENABLED", True),
            patch.object(config, "GOOGLE_CLIENT_ID", "test-google-client.apps.googleusercontent.com"),
            patch.object(config, "GOOGLE_CLIENT_SECRET", "test-secret-not-for-frontend"),
            patch.object(config, "GOOGLE_REDIRECT_URI", "http://testserver/api/auth/google/callback"),
            patch.object(config, "APP_ENV", "development"),
            patch.object(config, "IS_VERCEL", False),
            patch.object(config, "SUPABASE_AUTH_ENABLED", False),
        ]
        for patcher in self.config_patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def _begin_google_flow(self):
        response = self.client.get("/api/auth/google/start", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        location = response.headers["location"]
        parsed = urlparse(location)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "accounts.google.com")
        self.assertEqual(params["redirect_uri"], ["http://testserver/api/auth/google/callback"])
        self.assertEqual(params["code_challenge_method"], ["S256"])
        self.assertNotIn("client_secret", location)
        state = self.client.cookies.get("prismo_google_oauth_state")
        nonce = self.client.cookies.get("prismo_google_oauth_nonce")
        self.assertTrue(state)
        self.assertTrue(nonce)
        self.assertTrue(self.client.cookies.get("prismo_google_oauth_verifier"))
        return state, nonce

    def test_start_uses_state_nonce_pkce_and_keeps_secret_server_side(self):
        _state, _nonce = self._begin_google_flow()

    def test_callback_creates_cookie_session_and_verified_google_user(self):
        state, nonce = self._begin_google_flow()
        claims = {
            "sub": "google-sub-123",
            "email": "person@example.com",
            "email_verified": True,
            "nonce": nonce,
            "name": "Test Person",
        }
        with patch("app.routers.auth._exchange_google_code", return_value={"id_token": "dummy"}), patch(
            "app.routers.auth._verify_google_id_token", return_value=claims
        ):
            response = self.client.get(f"/api/auth/google/callback?code=one-time-code&state={state}", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/index.html?oauth=success")
        cookie_headers = response.headers.get_list("set-cookie")
        access_cookie = next(value for value in cookie_headers if value.startswith("prismo_access_token="))
        self.assertIn("httponly", access_cookie.lower())
        self.assertIn("samesite=lax", access_cookie.lower())
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["username"], "person")

        db = self.Session()
        try:
            self.assertEqual(db.query(func.count(models.OAuthIdentity.id)).filter(models.OAuthIdentity.provider == "google", models.OAuthIdentity.subject == "google-sub-123").scalar(), 1)
            self.assertEqual(db.query(func.count(models.UserSettings.id)).scalar(), 1)
        finally:
            db.close()

    def test_same_google_sub_reuses_user_not_create_duplicate(self):
        state, nonce = self._begin_google_flow()
        claims = {"sub": "stable-sub", "email": "same@example.com", "email_verified": True, "nonce": nonce}
        with patch("app.routers.auth._exchange_google_code", return_value={"id_token": "dummy"}), patch(
            "app.routers.auth._verify_google_id_token", return_value=claims
        ):
            first = self.client.get(f"/api/auth/google/callback?code=first&state={state}", follow_redirects=False)
        self.assertEqual(first.status_code, 303)
        # Start a fresh independent OAuth request (state + nonce + verifier).
        state2, nonce2 = self._begin_google_flow()
        claims2 = dict(claims, nonce=nonce2)
        with patch("app.routers.auth._exchange_google_code", return_value={"id_token": "dummy"}), patch(
            "app.routers.auth._verify_google_id_token", return_value=claims2
        ):
            second = self.client.get(f"/api/auth/google/callback?code=second&state={state2}", follow_redirects=False)
        self.assertEqual(second.status_code, 303)
        db = self.Session()
        try:
            self.assertEqual(db.query(func.count(models.OAuthIdentity.id)).filter(models.OAuthIdentity.provider == "google", models.OAuthIdentity.subject == "stable-sub").scalar(), 1)
        finally:
            db.close()

    def test_callback_rejects_mismatched_state(self):
        self._begin_google_flow()
        response = self.client.get("/api/auth/google/callback?code=one-time-code&state=wrong-state", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn("auth_error=google_state", response.headers["location"])

    def test_logout_clears_cookie_backed_session(self):
        state, nonce = self._begin_google_flow()
        claims = {"sub": "logout-sub", "email": "logout@example.com", "email_verified": True, "nonce": nonce}
        with patch("app.routers.auth._exchange_google_code", return_value={"id_token": "dummy"}), patch(
            "app.routers.auth._verify_google_id_token", return_value=claims
        ):
            self.client.get(f"/api/auth/google/callback?code=one-time-code&state={state}", follow_redirects=False)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        logout = self.client.post("/api/auth/logout")
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)


    def test_google_identity_is_stored_without_changing_legacy_user_columns(self):
        columns = {column.name for column in models.User.__table__.columns}
        self.assertNotIn("email", columns)
        self.assertNotIn("google_sub", columns)
        self.assertIn("oauth_identities", Base.metadata.tables)

    def test_supabase_google_flow_uses_pkce_and_server_side_key(self):
        with patch.object(config, "GOOGLE_OAUTH_ENABLED", False), patch.object(config, "SUPABASE_AUTH_ENABLED", True), patch.object(config, "SUPABASE_URL", "https://example.supabase.co"), patch.object(config, "SUPABASE_ANON_KEY", "public-anon-key"), patch(
            "app.routers.auth.httpx.Client"
        ) as client_cls:
            response_obj = type("Response", (), {"status_code": 302, "headers": {"location": "https://accounts.google.com/o/oauth2/v2/auth?test=1"}, "content": b""})()
            client_cls.return_value.__enter__.return_value.get.return_value = response_obj
            response = self.client.get("/api/auth/google/start", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("accounts.google.com", response.headers["location"])
        self.assertTrue(self.client.cookies.get("prismo_google_oauth_verifier"))

    def test_google_login_is_gracefully_disabled_without_credentials(self):
        with patch.object(config, "GOOGLE_OAUTH_ENABLED", False), patch.object(config, "SUPABASE_AUTH_ENABLED", False):
            response = self.client.get("/api/auth/google/start", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn("auth_error=google_not_configured", response.headers["location"])


if __name__ == "__main__":
    unittest.main()
