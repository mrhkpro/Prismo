import logging
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import answer_cache, llm_client, rag_pipeline, rag_store, streaming, user_settings_compat

logger = logging.getLogger("prismo.playground")

router = APIRouter(prefix="/api/playground", tags=["آزمایشگاه تست"])


def _get_or_create_session(db: Session, user: models.User, session_id: str | None) -> models.ChatSession:
    if session_id:
        session = (
            db.query(models.ChatSession)
            .filter(
                models.ChatSession.id == session_id,
                models.ChatSession.user_id == user.id,
                models.ChatSession.source == models.ChatSource.playground,
            )
            .first()
        )
        if session:
            return session
    session = models.ChatSession(user_id=user.id, source=models.ChatSource.playground)
    db.add(session)
    db.flush()
    return session


@router.post("/sessions/new")
def new_session(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = models.ChatSession(user_id=current_user.id, source=models.ChatSource.playground)
    db.add(session)
    db.commit()
    return {"session_id": session.id}


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == current_user.id,
            models.ChatSession.source == models.ChatSource.playground,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="نشست گفت‌وگو یافت نشد.")
    db.delete(session)
    db.commit()


@router.post("/chat", response_model=schemas.ChatTestResponse)
def chat_test(
    payload: schemas.ChatTestRequest,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_or_create_session(db, current_user, payload.session_id)
    try:
        selected_model = payload.model or user_settings_compat.get(db, current_user.id).chat_model
        reply, matches = rag_pipeline.run_rag_chat(
            db, current_user, session, payload.message, model=selected_model,
            language=request.headers.get("X-QZ-Language", "fa"),
            fast_mode=True,
        )
    except llm_client.LLMError:
        db.commit()  # نشست را حتی در صورت خطا نگه می‌داریم
        raise

    rag_pipeline.save_turn(db, session, payload.message, reply)

    sources = [
        schemas.SourceChunk(document_title=chunk.document.title, text=chunk.text, score=round(score, 4))
        for chunk, score in matches
    ]
    return schemas.ChatTestResponse(
        session_id=session.id,
        reply=reply,
        sources=sources,
        model=selected_model,
    )


@router.post("/chat/stream")
def chat_test_stream(
    payload: schemas.ChatTestRequest,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """نسخه‌ی استریم چت آزمایشگاه (SSE): meta → delta... → done (یا error)."""
    session = _get_or_create_session(db, current_user, payload.session_id)
    selected_model = payload.model or user_settings_compat.get(db, current_user.id).chat_model
    session_id, owner_id, message = session.id, current_user.id, payload.message
    language = request.headers.get("X-QZ-Language", "fa")
    db.commit()  # نشست حتی اگر مدل خطا بدهد حفظ می‌شود
    # نشست درخواست (db) پیش از شروع استریم بسته می‌شود؛ generator با نشست‌های کوتاه‌مدت خودش کار می‌کند.
    bind = db.get_bind()

    def event_stream():
        collected: list[str] = []
        # اولین بایت را زود بفرست تا کاربر معطل آماده‌سازی embedding نشود.
        yield ": qz-ready\n\n"
        plan = None
        try:
            with Session(bind=bind, autoflush=False) as work_db:
                owner = work_db.get(models.User, owner_id)
                chat_session = work_db.get(models.ChatSession, session_id)
                plan = rag_pipeline.prepare_rag_chat(
                    work_db, owner, chat_session, message,
                    model=selected_model, language=language, fast_mode=True,
                )
                meta = {"session_id": session_id, "model": selected_model, "sources": streaming.sources_payload(plan.matches)}
            # اتصال دیتابیس پیش از تماس طولانی با مدل آزاد شد.
            yield streaming.sse("meta", meta)
            if plan.instant_reply or plan.no_answer:
                reply = plan.instant_reply or plan.no_answer
                collected.append(reply or "")
                yield streaming.sse("delta", {"t": reply or ""})
            else:
                started = time.perf_counter()
                first_token_ms = None

                def mark_first_token() -> None:
                    nonlocal first_token_ms
                    if first_token_ms is None:
                        first_token_ms = int((time.perf_counter() - started) * 1000)

                pieces = llm_client.stream_chat_completion(
                    plan.messages, plan.provider, temperature=plan.temperature, model=plan.model,
                    max_tokens=plan.max_output_tokens, fast_mode=plan.fast_mode,
                )
                yield from streaming.relay_model_stream(pieces, collected, on_first_delta=mark_first_token)
                rag_pipeline.log_rag_timing(
                    owner_id, plan, int((time.perf_counter() - started) * 1000), first_token_ms=first_token_ms,
                )
            yield streaming.sse("done", {})
        except llm_client.LLMError as exc:
            yield streaming.sse("error", {
                "message": str(exc), "retry": True, "partial": bool(collected),
                "fast_timeout": bool(getattr(exc, "fast_timeout", False)),
            })
        except Exception:  # noqa: BLE001
            logger.exception("playground stream failed")
            yield streaming.sse("error", {"message": "", "retry": True, "partial": bool(collected)})
        finally:
            text = "".join(collected)
            if text:
                try:
                    with Session(bind=bind, autoflush=False) as save_db:
                        if plan is not None and plan.cache_allowed and not plan.cache_hit:
                            answer_cache.store(save_db, owner_id, plan.cache_key, text, plan.matches)
                        rag_pipeline.save_turn(save_db, session_id, message, text)
                except Exception:  # noqa: BLE001
                    logger.exception("could not save streamed turn")

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=streaming.SSE_HEADERS)


@router.post("/search", response_model=list[schemas.SemanticSearchResult])
def semantic_search(
    payload: schemas.SemanticSearchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = llm_client.resolve_provider(user_settings_compat.get(db, current_user.id))
    query_embedding = llm_client.embed_text(payload.query, provider)
    settings = user_settings_compat.get(db, current_user.id)
    matches = rag_store.search(db, current_user.id, query_embedding, top_k=payload.top_k, similarity_threshold=settings.similarity_threshold or 0.0)
    return [
        schemas.SemanticSearchResult(
            document_title=chunk.document.title,
            document_id=chunk.document_id,
            text=chunk.text,
            score=round(score, 4),
        )
        for chunk, score in matches
    ]


@router.get("/free-models")
def free_models(current_user: models.User = Depends(get_current_user)):
    """لیست مدل‌های رایگان آماده، برای پر کردن گزینه‌های حالت Battle."""
    return {"chat_models": config.DEFAULT_CHAT_MODELS}


@router.post("/battle", response_model=schemas.BattleResponse)
def battle(
    payload: schemas.BattleRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare built-in models and the user's saved custom chat model."""
    provider_a, provider_b = _battle_providers(payload, current_user, db)
    messages = [{"role": "user", "content": payload.prompt}]

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="battle") as executor:
        future_a = executor.submit(llm_client.timed_chat_completion, messages, provider_a, payload.model_a)
        future_b = executor.submit(llm_client.timed_chat_completion, messages, provider_b, payload.model_b)
        reply_a, ms_a, err_a = future_a.result()
        reply_b, ms_b, err_b = future_b.result()

    return schemas.BattleResponse(
        side_a=schemas.BattleSide(model=payload.model_a, reply=reply_a, elapsed_ms=ms_a, error=err_a),
        side_b=schemas.BattleSide(model=payload.model_b, reply=reply_b, elapsed_ms=ms_b, error=err_b),
    )


@router.post("/battle/stream")
def battle_stream(
    payload: schemas.BattleRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream two built-in/custom model answers concurrently as SSE events."""
    provider_a, provider_b = _battle_providers(payload, current_user, db)
    messages = [{"role": "user", "content": payload.prompt}]

    def event_stream():
        events: Queue[tuple[str, dict]] = Queue()

        def run_side(side: str, model: str, provider: llm_client.ProviderConfig) -> None:
            started = time.perf_counter()
            try:
                for piece in llm_client.stream_chat_completion(messages, provider, model=model):
                    if piece:
                        events.put(("delta", {"side": side, "t": piece}))
                events.put(("side_done", {
                    "side": side, "model": model,
                    "elapsed_ms": int((time.perf_counter() - started) * 1000), "error": None,
                }))
            except Exception as exc:  # a failure for one model must not cancel the other model
                events.put(("side_done", {
                    "side": side, "model": model,
                    "elapsed_ms": int((time.perf_counter() - started) * 1000), "error": str(exc),
                }))

        yield ": qz-ready\n\n"
        yield streaming.sse("meta", {"model_a": payload.model_a, "model_b": payload.model_b})
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="battle-stream") as executor:
            executor.submit(run_side, "a", payload.model_a, provider_a)
            executor.submit(run_side, "b", payload.model_b, provider_b)
            remaining = 2
            while remaining:
                try:
                    event, data = events.get(timeout=10)
                except Empty:
                    yield ": keepalive\n\n"
                    continue
                yield streaming.sse(event, data)
                if event == "side_done":
                    remaining -= 1
        yield streaming.sse("done", {})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=streaming.SSE_HEADERS,
    )


def _battle_provider_for_model(model_id: str, settings=None, db=None, user_id=None) -> llm_client.ProviderConfig:
    """Resolve a model only when it is built-in or the user's saved custom model."""
    if model_id in config.DEFAULT_CHAT_MODELS:
        return llm_client.ProviderConfig(
            base_url=config.DEFAULT_PROVIDER_BASE_URL,
            api_key=config.DEFAULT_PROVIDER_API_KEY,
            chat_model=model_id,
            embedding_model=config.DEFAULT_EMBEDDING_MODEL,
            is_default=True,
        )

    # A saved model has its own provider credentials, so saving a second model
    # never overwrites the first model's connection profile.
    if db is not None and user_id is not None:
        saved = db.query(models.SavedChatModel).filter_by(user_id=user_id, model_id=model_id).first()
        if saved:
            return llm_client.ProviderConfig(
                base_url=saved.base_url, api_key=saved.api_key, chat_model=model_id,
                embedding_model=config.DEFAULT_EMBEDDING_MODEL, is_default=False,
            )
    is_saved_custom_model = (
        settings is not None and not settings.use_default_provider
        and bool(settings.base_url) and bool(settings.api_key) and settings.chat_model == model_id
    )
    if is_saved_custom_model:
        return llm_client.resolve_provider(settings)

    raise HTTPException(status_code=400, detail="مدل باید یکی از مدل‌های آماده یا مدل اختصاصی ذخیره‌شده‌ی همین حساب باشد.")


def _battle_providers(payload: schemas.BattleRequest, current_user: models.User, db) -> tuple[llm_client.ProviderConfig, llm_client.ProviderConfig]:
    """Build one provider per side, allowing a saved custom model beside a default model."""
    requested_models = (payload.model_a, payload.model_b)
    settings = None
    if any(model_id not in config.DEFAULT_CHAT_MODELS for model_id in requested_models):
        # Direct function calls in legacy tests don't inject FastAPI's DB
        # dependency; they're still valid for built-in models. Real requests
        # always receive a Session and can validate a saved custom model.
        if hasattr(db, "execute"):
            settings = user_settings_compat.get(db, current_user.id)
    return (
        _battle_provider_for_model(payload.model_a, settings, db if hasattr(db, "query") else None, current_user.id),
        _battle_provider_for_model(payload.model_b, settings, db if hasattr(db, "query") else None, current_user.id),
    )
