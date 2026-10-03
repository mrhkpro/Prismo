import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.routers.admin import (
    get_user_detail, inspect_user_documents, inspect_user_sessions, session_messages,
)


class AdminInspectTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        u = models.User(username="u1", password_hash="x", role=models.UserRole.user)
        self.db.add(u)
        self.db.flush()
        self.uid = u.id  # بدون UserSettings عمداً: ادمین نباید کرش کند
        doc = models.Document(user_id=u.id, title="d", content="c")
        self.db.add(doc)
        self.db.flush()
        self.db.add(models.Chunk(document_id=doc.id, user_id=u.id, chunk_index=0, text="t", embedding=[0.1] * 4))
        s = models.ChatSession(user_id=u.id, source=models.ChatSource.widget)
        self.db.add(s)
        self.db.flush()
        self.sid = s.id
        self.db.add(models.ChatMessage(session_id=s.id, role="user", content="hi", is_flagged=None, resolved=None))
        self.db.commit()

    def test_admin_can_inspect_user_chats(self):
        detail = get_user_detail(self.uid, db=self.db, _admin=None)
        self.assertEqual(detail.username, "u1")
        docs = inspect_user_documents(self.uid, db=self.db, _admin=None)
        self.assertEqual(docs[0].chunk_count, 1)
        sessions = inspect_user_sessions(self.uid, db=self.db, _admin=None)
        self.assertEqual(sessions[0].message_count, 1)
        msgs = session_messages(self.sid, db=self.db, _admin=None)
        self.assertEqual(msgs[0].content, "hi")
        self.assertFalse(msgs[0].is_flagged)
