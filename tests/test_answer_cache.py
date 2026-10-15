from types import SimpleNamespace
import json
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.database import Base
from app.services import llm_client, rag_pipeline


def _session(db, user_id, source=models.ChatSource.playground):
    result = models.ChatSession(user_id=user_id, source=source)
    db.add(result)
    db.commit()
    return result


def test_same_first_question_in_another_session_uses_cached_answer_without_ai_calls():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            owner = models.User(username="cache-owner", password_hash="hash", role=models.UserRole.user, is_active=True)
            db.add(owner)
            db.flush()
            doc = models.Document(user_id=owner.id, title="Hours", content="Support is open from 9 to 5.")
            db.add(doc)
            db.flush()
            chunk = models.Chunk(
                document_id=doc.id, user_id=owner.id, chunk_index=0,
                text="Support is open from 9 to 5.", embedding=json.dumps([1.0, 0.0]),
            )
            db.add(chunk)
            db.commit()
            first_session = _session(db, owner.id)
            second_session = _session(db, owner.id)
            settings = SimpleNamespace(
                chat_model="chat-model", embedding_model="embed-model", system_prompt="Answer from docs.",
                temperature=0.2, top_k=4, similarity_threshold=0.0,
                use_default_provider=False, base_url="https://provider.example/v1", api_key="test-key",
                embedding_use_default_provider=False, separate_embedding_provider=False,
                embedding_base_url=None, embedding_api_key=None,
            )
            provider = llm_client.ProviderConfig(
                base_url="https://provider.example/v1", api_key="test-key", chat_model="chat-model",
                embedding_model="embed-model", is_default=False,
                embedding_base_url="https://provider.example/v1", embedding_api_key="test-key",
            )
            question = "What are the support hours?"
            with patch.object(rag_pipeline.user_settings_compat, "get", return_value=settings), \
                 patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider), \
                 patch.object(rag_pipeline.llm_client, "embed_text", return_value=[1.0, 0.0]) as embed, \
                 patch.object(rag_pipeline.llm_client, "chat_completion", return_value="Support is open from 9 to 5.") as chat:
                first_answer, first_matches = rag_pipeline.run_rag_chat(db, owner, first_session, question, language="en")
                assert first_answer == "Support is open from 9 to 5."
                assert first_matches
                rag_pipeline.save_turn(db, first_session, question, first_answer)

                # A separate, context-free session asks the exact same question.
                second_answer, second_matches = rag_pipeline.run_rag_chat(db, owner, second_session, question, language="en")
                assert second_answer == first_answer
                assert second_matches
                assert embed.call_count == 1
                assert chat.call_count == 1
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_immediate_duplicate_in_same_session_reuses_previous_answer():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            owner = models.User(username="cache-repeat", password_hash="hash", role=models.UserRole.user, is_active=True)
            db.add(owner); db.flush()
            doc = models.Document(user_id=owner.id, title="A", content="A short answer.")
            db.add(doc); db.flush()
            db.add(models.Chunk(document_id=doc.id, user_id=owner.id, chunk_index=0, text="A short answer.", embedding=json.dumps([1.0, 0.0])))
            db.flush()
            chat_session = _session(db, owner.id)
            settings = SimpleNamespace(
                chat_model="m", embedding_model="e", system_prompt="base", temperature=0.1, top_k=3,
                similarity_threshold=0.0, use_default_provider=False, base_url="https://p.example/v1", api_key="k",
                embedding_use_default_provider=False, separate_embedding_provider=False, embedding_base_url=None, embedding_api_key=None,
            )
            provider = llm_client.ProviderConfig("https://p.example/v1", "k", "m", "e", False,
                embedding_base_url="https://p.example/v1", embedding_api_key="k")
            question = "What does the document say?"
            with patch.object(rag_pipeline.user_settings_compat, "get", return_value=settings), \
                 patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider), \
                 patch.object(rag_pipeline.llm_client, "embed_text", return_value=[1.0, 0.0]) as embed, \
                 patch.object(rag_pipeline.llm_client, "chat_completion", return_value="A short answer.") as chat:
                answer, _ = rag_pipeline.run_rag_chat(db, owner, chat_session, question, language="en")
                rag_pipeline.save_turn(db, chat_session, question, answer)
                repeated, _ = rag_pipeline.run_rag_chat(db, owner, chat_session, question, language="en")
                assert repeated == answer
                assert embed.call_count == 1
                assert chat.call_count == 1
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_repeated_question_after_other_turns_uses_conversation_memory_without_network_calls():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            owner = models.User(username="memory-owner", password_hash="hash", role=models.UserRole.user, is_active=True)
            db.add(owner)
            db.flush()
            doc = models.Document(user_id=owner.id, title="Names", content="Mamad's name is Hashem.")
            db.add(doc)
            db.flush()
            db.add(models.Chunk(
                document_id=doc.id, user_id=owner.id, chunk_index=0,
                text="اسم ممد هاشم است.", embedding=json.dumps([1.0, 0.0]),
            ))
            db.commit()
            chat_session = _session(db, owner.id)
            settings = SimpleNamespace(
                chat_model="chat-model", embedding_model="embed-model", system_prompt="Answer from docs.",
                temperature=0.2, top_k=4, similarity_threshold=0.0,
                use_default_provider=False, base_url="https://provider.example/v1", api_key="test-key",
                embedding_use_default_provider=False, separate_embedding_provider=False,
                embedding_base_url=None, embedding_api_key=None,
            )
            provider = llm_client.ProviderConfig(
                base_url="https://provider.example/v1", api_key="test-key", chat_model="chat-model",
                embedding_model="embed-model", is_default=False,
                embedding_base_url="https://provider.example/v1", embedding_api_key="test-key",
            )
            with patch.object(rag_pipeline.user_settings_compat, "get", return_value=settings), \
                 patch.object(rag_pipeline.llm_client, "resolve_provider", return_value=provider) as resolve, \
                 patch.object(rag_pipeline.llm_client, "embed_text", return_value=[1.0, 0.0]) as embed, \
                 patch.object(rag_pipeline.llm_client, "chat_completion", return_value="هاشم") as chat:
                first, _ = rag_pipeline.run_rag_chat(db, owner, chat_session, "اسم ممد چیه؟", language="fa")
                assert first == "هاشم"
                rag_pipeline.save_turn(db, chat_session, "اسم ممد چیه؟", first)

                # Several unrelated turns later, a phrasing variant should reuse
                # the old answer before provider resolution, embeddings, or RAG.
                rag_pipeline.save_turn(db, chat_session.id, "امروز چه خبر؟", "همه چیز خوب است.")
                rag_pipeline.save_turn(db, chat_session.id, "یک سؤال دیگر دارم", "بفرمایید.")
                recalled, matches = rag_pipeline.run_rag_chat(
                    db, owner, chat_session, "ممد اسمش چیست", language="fa"
                )
                assert recalled == "هاشم"
                assert matches == []

                # A short contextual follow-up for the same fact is recalled too.
                followup, _ = rag_pipeline.run_rag_chat(
                    db, owner, chat_session, "پس اسمش چی بود؟", language="fa"
                )
                assert followup == "هاشم"
                assert resolve.call_count == 1
                assert embed.call_count == 1
                assert chat.call_count == 1
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_conversation_recall_does_not_confuse_different_fact_about_same_person():
    from app.services.answer_cache import same_question_for_recall

    assert same_question_for_recall("اسم ممد چیه؟", "ممد اسمش چیست")
    assert not same_question_for_recall("اسم ممد چیه؟", "ممد چند سالشه؟")
