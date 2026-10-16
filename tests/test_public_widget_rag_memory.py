"""End-to-end widget regression: verify real local RAG retrieval and quick recall."""
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.services import llm_client, rag_store


def test_widget_answers_from_real_knowledge_chunk_then_recalls_without_second_search():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()
    owner = models.User(
        username="widget-rag-memory-owner",
        password_hash="test-hash",
        role=models.UserRole.user,
        is_active=True,
    )
    db.add(owner)
    db.flush()
    widget_id = "widget-rag-memory-test"
    db.add(models.UserSettings(
        user_id=owner.id,
        widget_id=widget_id,
        use_default_provider=False,
        base_url="https://provider.example/v1",
        api_key="unit-test-key",
        chat_model="unit-test-chat",
        embedding_model="unit-test-embedding",
        embedding_use_default_provider=False,
        separate_embedding_provider=False,
        top_k=4,
        similarity_threshold=0.0,
        system_prompt="فقط از دانشنامه پاسخ بده.",
    ))
    db.flush()
    doc = models.Document(
        user_id=owner.id,
        title="مشخصات هاشم",
        content="هاشم ۳۷ سال دارد. این مقدار از دانشنامه آزمایشی است.",
    )
    db.add(doc)
    db.flush()
    rag_store.add_chunks(
        db,
        owner.id,
        doc.id,
        ["طبق دانشنامه، هاشم ۳۷ سال دارد. این مقدار از رکورد مشخصات هاشم بازیابی شد."],
        [[1.0, 0.0]],
    )
    db.commit()
    db.close()

    def override_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    provider = llm_client.ProviderConfig(
        base_url="https://provider.example/v1",
        api_key="unit-test-key",
        chat_model="unit-test-chat",
        embedding_model="unit-test-embedding",
        is_default=False,
        embedding_base_url="https://provider.example/v1",
        embedding_api_key="unit-test-key",
    )
    chunk_phrase = "طبق دانشنامه، هاشم ۳۷ سال دارد"
    prompted_questions = []

    def mocked_chat_completion(messages, _provider, temperature=None, model=None):
        system_text = messages[0]["content"]
        # This is an assertion over the prompt sent to the model, not just the
        # final answer: the first widget reply really contained retrieved KB text.
        assert chunk_phrase in system_text
        question = messages[-1]["content"]
        prompted_questions.append(question)
        if "سن هاشم" in question:
            return "طبق دانشنامه، هاشم ۳۷ سال دارد."
        if "خلاصه" in question:
            return "سند دربارهٔ مشخصات هاشم است."
        return "اطلاعات موجود در سند دربارهٔ مشخصات هاشم است."

    real_search = rag_store.search
    try:
        with patch("app.services.rag_pipeline.llm_client.resolve_provider", return_value=provider) as resolve, \
             patch("app.services.rag_pipeline.llm_client.embed_text", return_value=[1.0, 0.0]) as embed, \
             patch("app.services.rag_pipeline.llm_client.chat_completion", side_effect=mocked_chat_completion) as chat, \
             patch("app.services.rag_pipeline.rag_store.search", wraps=real_search) as search:
            first = client.post(f"/public/widget/{widget_id}/chat", json={"message": "سن هاشم چیه؟"})
            assert first.status_code == 200, first.text
            first_body = first.json()
            assert first_body["reply"] == "طبق دانشنامه، هاشم ۳۷ سال دارد."
            session_id = first_body["session_id"]

            middle_one = client.post(
                f"/public/widget/{widget_id}/chat",
                json={"message": "اطلاعات این رکورد دربارهٔ چیست؟", "session_id": session_id},
            )
            assert middle_one.status_code == 200, middle_one.text
            middle_two = client.post(
                f"/public/widget/{widget_id}/chat",
                json={"message": "لطفاً سند را خلاصه کن.", "session_id": session_id},
            )
            assert middle_two.status_code == 200, middle_two.text

            # Same question, after other messages: historical recall must happen
            # before resolving a provider, creating embeddings or searching RAG.
            recalled = client.post(
                f"/public/widget/{widget_id}/chat",
                json={"message": "سن هاشم چیه؟", "session_id": session_id},
            )
            assert recalled.status_code == 200, recalled.text
            assert recalled.json()["reply"] == first_body["reply"]
            assert len(prompted_questions) == 3
            assert resolve.call_count == 3
            assert embed.call_count == 3
            assert search.call_count == 3
    finally:
        app.dependency_overrides.clear()
        client.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
