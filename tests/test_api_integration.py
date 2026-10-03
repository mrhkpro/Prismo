import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.security import get_current_user


class APIIntegrationTests(unittest.TestCase):
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
        app.dependency_overrides.pop(get_current_user, None)
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_registration_login_and_me_flow(self):
        registered = self.client.post(
            "/api/auth/register",
            json={"username": " user-a ", "password": "strongpass", "org_name": "Org"},
        )
        self.assertEqual(registered.status_code, 200)
        token = registered.json()["access_token"]

        me = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["username"], "user-a")

        login = self.client.post("/api/auth/login", json={"username": " USER-A ", "password": "strongpass"})
        self.assertEqual(login.status_code, 200)

    def test_document_isolation_across_users(self):
        a = self.client.post("/api/auth/register", json={"username": "user-a", "password": "strongpass"}).json()["access_token"]
        b = self.client.post("/api/auth/register", json={"username": "user-b", "password": "strongpass"}).json()["access_token"]

        from unittest.mock import patch
        with patch("app.routers.knowledge.llm_client.embed_texts", return_value=[[1.0, 0.0]]):
            created = self.client.post(
                "/api/knowledge/documents",
                headers={"Authorization": f"Bearer {a}"},
                json={"title": "Private", "content": "Only for A"},
            )
        self.assertEqual(created.status_code, 201)
        doc_id = created.json()["id"]

        hidden = self.client.get(
            f"/api/knowledge/documents/{doc_id}",
            headers={"Authorization": f"Bearer {b}"},
        )
        self.assertEqual(hidden.status_code, 404)


if __name__ == "__main__":
    unittest.main()
