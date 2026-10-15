"""Exact-query RAG cache scoped to the current user, provider, prompt, and knowledge base.

Only context-independent first-turn answers are cached across sessions. An immediately
repeated question in the same session may reuse its prior answer. Cache storage is an
optimization: a missing migration or cache-table error never blocks normal chat.
"""
from __future__ import annotations

import hashlib
import json
import logging
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .. import models

logger = logging.getLogger("prismo.answer_cache")
CACHE_TTL = timedelta(days=7)


def normalize_question(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = value.replace("ي", "ی").replace("ك", "ک").replace("‌", " ")
    return " ".join(value.split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()


# Conservative stop words for detecting a question already answered in the same
# conversation. These are used only for conversation recall; the broader RAG
# cache key continues to use normalize_question().
_RECALL_STOPWORDS = {
    "چی", "چیه", "چیست", "چه", "چرا", "چطور", "چگونه", "کجا", "کجاست", "کی", "کیه",
    "چند", "آیا", "است", "هست", "هستش", "بود", "بوده", "باشه", "میباشد", "میشه",
    "لطفا", "بگو", "بگید", "بهم", "من", "تو", "او", "اون", "آن", "این", "برای",
    "از", "به", "در", "با", "را", "رو", "هم", "پس", "و", "یا", "دوباره", "مجدد",
    "سوال", "پرسش", "جواب", "پاسخ", "what", "whats", "is", "are", "was", "were",
    "who", "how", "where", "when", "why", "the", "a", "an", "please", "tell", "me",
    "again", "s", "do", "does", "did", "can", "you", "of", "to", "and", "about",
}


def normalize_recall_question(value: str) -> str:
    """Normalize punctuation/spacing variants for same-conversation recall."""
    value = normalize_question(value or "")
    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    value = value.translate(digits)
    cleaned = []
    for char in value:
        category = unicodedata.category(char)
        cleaned.append(" " if category[0] in {"P", "S", "M"} else char)
    return " ".join("".join(cleaned).split())


def _recall_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for token in normalize_recall_question(value).split():
        # Normalize common Persian possessive/plural forms without using an
        # external NLP/model call. Keep a minimum 3-character stem.
        for suffix in ("شون", "شان", "مون", "مان", "تون", "تان", "های", "ها", "شه", "ش"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                token = token[:-len(suffix)]
                break
        if len(token) > 1 and token not in _RECALL_STOPWORDS:
            tokens.add(token)
    return tokens


def same_question_for_recall(current: str, previous: str) -> bool:
    """Match exact repeats and high-confidence paraphrases, not merely shared topics."""
    current_normalized = normalize_recall_question(current)
    previous_normalized = normalize_recall_question(previous)
    if not current_normalized or not previous_normalized:
        return False
    if current_normalized == previous_normalized:
        return True
    current_tokens = _recall_tokens(current_normalized)
    previous_tokens = _recall_tokens(previous_normalized)
    # Require the same informative words. This catches phrasing changes such as
    # "اسم ممد چیه؟" / "ممد اسمش چیست" while avoiding same-entity/different-fact
    # errors such as name vs. age.
    return len(current_tokens) >= 2 and current_tokens == previous_tokens


def _fact_intents(value: str) -> set[str]:
    tokens = _recall_tokens(value)
    intents = set()
    if tokens.intersection({"اسم", "نام", "name"}):
        intents.add("name")
    if tokens.intersection({"سن", "عمر", "سال", "age", "old"}):
        intents.add("age")
    if tokens.intersection({"شغل", "کار", "job", "profession", "occupation"}):
        intents.add("work")
    if tokens.intersection({"آدرس", "مکان", "محل", "شهر", "address", "location", "city"}):
        intents.add("location")
    return intents


def _has_referential_marker(value: str) -> bool:
    """Detect short follow-ups like Persian 'اسمش چی بود؟' or English 'his name?'."""
    words = normalize_recall_question(value).split()
    if any(word in {"او", "اون", "آن", "ایشون", "ایشان", "همون", "his", "her", "their", "its", "him", "them"} for word in words):
        return True
    return any(word.endswith("ش") and len(word) >= 4 for word in words)


def is_short_fact_followup(value: str) -> bool:
    """True for referential follow-ups whose fact type is explicit (name, age, etc.)."""
    return (
        len(_recall_tokens(value)) == 1
        and _has_referential_marker(value)
        and bool(_fact_intents(value))
    )


def same_fact_followup_for_recall(current: str, previous: str) -> bool:
    """Match an unambiguous short pronoun follow-up to an earlier question's fact type."""
    if not is_short_fact_followup(current):
        return False
    current_intents = _fact_intents(current)
    previous_intents = _fact_intents(previous)
    return bool(current_intents and current_intents.intersection(previous_intents))


def find_historical_answer(db: Session, session: models.ChatSession, question: str) -> str | None:
    """Reuse a prior answer in this exact conversation without embedding or LLM calls.

    Only complete user/assistant turn pairs are considered. Flagged user messages
    are excluded, and history is bounded so the fast path remains inexpensive.
    """
    if not getattr(session, "id", None) or not hasattr(db, "query"):
        return None
    normalized = normalize_recall_question(question)
    if len(normalized) < 3:
        return None
    try:
        rows = (
            db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == session.id)
            .order_by(models.ChatMessage.id.desc())
            .limit(500)
            .all()
        )
        rows.reverse()
        turns: list[tuple[models.ChatMessage, models.ChatMessage]] = []
        pending_user = None
        for row in rows:
            if row.role == "user":
                pending_user = row
            elif row.role == "assistant" and pending_user is not None:
                turns.append((pending_user, row))
                pending_user = None

        # Newest matching answer wins if the same question was asked more than once.
        for prior_user, prior_assistant in reversed(turns):
            answer = (prior_assistant.content or "").strip()
            if prior_user.is_flagged or not answer:
                continue
            if same_question_for_recall(question, prior_user.content or ""):
                return answer

        # For short pronoun follow-ups, only inspect the nearest prior answered
        # fact question. Do not jump to an older person's name/age if a newer
        # fact in the conversation may refer to someone else.
        if is_short_fact_followup(question):
            for prior_user, prior_assistant in reversed(turns):
                answer = (prior_assistant.content or "").strip()
                if prior_user.is_flagged or not answer:
                    continue
                previous_question = prior_user.content or ""
                if _fact_intents(previous_question):
                    if same_fact_followup_for_recall(question, previous_question):
                        return answer
                    break
    except SQLAlchemyError as exc:
        logger.info("conversation_memory_lookup_skipped reason=%s", type(exc).__name__)
    return None


def _session_context(db: Session, session: models.ChatSession, message: str) -> tuple[bool, str | None]:
    """Return (cache-safe, immediate-repeat-answer)."""
    if not getattr(session, "id", None) or not hasattr(db, "query"):
        return False, None
    try:
        last_two = (
            db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == session.id)
            .order_by(models.ChatMessage.id.desc())
            .limit(2)
            .all()
        )
        if len(last_two) >= 2:
            newest, previous = last_two[0], last_two[1]
            if (
                newest.role == "assistant"
                and previous.role == "user"
                and not bool(previous.is_flagged)
                and normalize_question(previous.content) == normalize_question(message)
                and (newest.content or "").strip()
            ):
                return True, newest.content.strip()
        # An empty session has no previous conversational context to contaminate a cross-chat cache hit.
        count = db.query(func.count(models.ChatMessage.id)).filter(models.ChatMessage.session_id == session.id).scalar() or 0
        return count == 0, None
    except SQLAlchemyError:
        db.rollback()
        return False, None


def make_cache_key(
    db: Session,
    owner: models.User,
    session: models.ChatSession,
    question: str,
    settings: Any,
    provider: Any,
    language: str,
) -> tuple[str | None, bool, str | None]:
    allowed, repeated_answer = _session_context(db, session, question)
    if not allowed or len(normalize_question(question)) < 4:
        return None, allowed, repeated_answer
    try:
        chunk_count, max_chunk_id = (
            db.query(func.count(models.Chunk.id), func.max(models.Chunk.id))
            .filter(models.Chunk.user_id == owner.id)
            .one()
        )
        latest_document_update = (
            db.query(func.max(models.Document.updated_at))
            .filter(models.Document.user_id == owner.id)
            .scalar()
        )
    except SQLAlchemyError:
        db.rollback()
        return None, allowed, repeated_answer

    # Hash API keys before including them in the signature; neither raw keys nor raw questions are stored in the key.
    key_material = {
        "user": owner.id,
        "question": _sha256(normalize_question(question)),
        "language": language,
        "chat_base": getattr(provider, "base_url", ""),
        "chat_key_fingerprint": _sha256(getattr(provider, "api_key", "") or ""),
        "chat_model": getattr(provider, "chat_model", ""),
        "embedding_base": getattr(provider, "embedding_base_url", "") or "",
        "embedding_key_fingerprint": _sha256(getattr(provider, "embedding_api_key", "") or ""),
        "embedding_model": getattr(provider, "embedding_model", ""),
        "system_prompt": _sha256(getattr(settings, "system_prompt", "") or ""),
        "temperature": getattr(settings, "temperature", None),
        "top_k": getattr(settings, "top_k", None),
        "similarity_threshold": getattr(settings, "similarity_threshold", None),
        "chunk_count": int(chunk_count or 0),
        "max_chunk_id": int(max_chunk_id or 0),
        "latest_document_update": latest_document_update.isoformat() if latest_document_update else None,
    }
    encoded = json.dumps(key_material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _sha256(encoded), allowed, repeated_answer


def lookup(db: Session, owner: models.User, cache_key: str | None) -> tuple[str, list[tuple[models.Chunk, float]]] | None:
    if not cache_key:
        return None
    try:
        # Use a savepoint: if a production deployment has not applied migration 007,
        # the failed optional cache query should not poison the chat transaction.
        with db.begin_nested():
            row = (
                db.query(models.AnswerCache)
                .filter(models.AnswerCache.user_id == owner.id, models.AnswerCache.cache_key == cache_key)
                .first()
            )
            if not row:
                return None
            created_at = row.created_at
            if created_at:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - created_at > CACHE_TTL:
                    return None
            refs = row.source_chunks if isinstance(row.source_chunks, list) else []
            ids = [int(item.get("id")) for item in refs if isinstance(item, dict) and str(item.get("id", "")).isdigit()]
            if not ids:
                return row.answer, []
            chunks = (
                db.query(models.Chunk)
                .join(models.Document, models.Chunk.document_id == models.Document.id)
                .filter(models.Chunk.id.in_(ids), models.Chunk.user_id == owner.id, models.Document.user_id == owner.id)
                .all()
            )
            by_id = {chunk.id: chunk for chunk in chunks}
            matches = [
                (by_id[int(item["id"])], float(item.get("score", 0.0)))
                for item in refs
                if isinstance(item, dict) and str(item.get("id", "")).isdigit() and int(item["id"]) in by_id
            ]
            if len(matches) != len(ids):
                # Deleted or changed source chunks: do not serve an incomplete/stale citation set.
                return None
            return row.answer, matches
    except SQLAlchemyError as exc:
        logger.info("answer_cache_lookup_skipped reason=%s", type(exc).__name__)
        return None


def store(
    db: Session,
    owner_id: int,
    cache_key: str | None,
    answer: str,
    matches: list[tuple[models.Chunk, float]],
) -> None:
    if not cache_key or not isinstance(answer, str) or not answer.strip():
        return
    refs = [{"id": int(chunk.id), "score": float(score)} for chunk, score in matches if getattr(chunk, "id", None) is not None]
    try:
        with db.begin_nested():
            row = (
                db.query(models.AnswerCache)
                .filter(models.AnswerCache.user_id == owner_id, models.AnswerCache.cache_key == cache_key)
                .first()
            )
            if row:
                row.answer = answer.strip()
                row.source_chunks = refs
                row.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            else:
                db.add(models.AnswerCache(user_id=owner_id, cache_key=cache_key, answer=answer.strip(), source_chunks=refs))
            db.flush()
    except SQLAlchemyError as exc:
        logger.info("answer_cache_store_skipped reason=%s", type(exc).__name__)
