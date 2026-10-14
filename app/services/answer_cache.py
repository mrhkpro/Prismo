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
