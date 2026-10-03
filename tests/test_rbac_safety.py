import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models, schemas
from app.database import Base
from app.routers.admin import block_user, change_role


class RBACSafetyTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        self.db = self.Session()
        self.admin = models.User(username="admin", password_hash="x", role=models.UserRole.admin, is_active=True)
        self.user = models.User(username="user", password_hash="x", role=models.UserRole.admin, is_active=True)
        self.db.add_all([self.admin, self.user])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.db.bind.dispose()

    def test_last_active_admin_cannot_be_blocked(self):
        block_user(self.user.id, self.db, self.admin)
        with self.assertRaises(HTTPException) as caught:
            block_user(self.admin.id, self.db, self.admin)
        self.assertEqual(caught.exception.status_code, 400)

    def test_last_active_admin_cannot_be_demoted(self):
        change_role(self.user.id, schemas.RoleUpdateRequest(role="user"), self.db, self.admin)
        with self.assertRaises(HTTPException) as caught:
            change_role(self.admin.id, schemas.RoleUpdateRequest(role="user"), self.db, self.admin)
        self.assertEqual(caught.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
