import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.routers.admin import all_conversations, list_users, security_flags


class AdminPaginationTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)
        self.db = self.Session()
        for i in range(3):
            user = models.User(username=f"user-{i}", password_hash="x", role=models.UserRole.user)
            self.db.add(user)
            self.db.flush()
            self.db.add(models.UserSettings(user_id=user.id))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.db.bind.dispose()

    def test_user_listing_honors_limit_and_offset(self):
        users = list_users(search=None, limit=2, offset=1, db=self.db, _admin=None)
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].username, "user-1")

    def test_conversation_and_flag_queries_have_bounded_page_size(self):
        sessions = all_conversations(source=None, flagged_only=False, limit=1, offset=0, db=self.db, _admin=None)
        flags = security_flags(resolved=None, limit=1, offset=0, db=self.db, _admin=None)
        self.assertEqual(sessions, [])
        self.assertEqual(flags, [])


if __name__ == "__main__":
    unittest.main()
