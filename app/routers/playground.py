import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import llm_client, rag_pipeline, rag_store, streaming

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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_or_create_session(db, current_user, payload.session_id)
    try:
        selected_model = payload.model or current_user.settings.chat_model
        reply, matches = rag_pipeline.run_rag_chat(
            db, current_user, session, payload.message, model=selected_model
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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """نسخه‌ی استریم چت آزمایشگاه (SSE): meta → delta... → done (یا error)."""
    session = _get_or_create_session(db, current_user, payload.session_id)
    selected_model = payload.model or current_user.settings.chat_model
    session_id, owner_id, message = session.id, current_user.id, payload.message
    db.commit()

    def event_stream():
        collected: list[str] = []
        # اولین بایت را زود بفرست تا کاربر معطل آماده‌سازی embedding نشود.
        yield ": qz-ready\n\n"
        try:
            plan = rag_pipeline.prepare_rag_chat(db, current_user, session, message, model=selected_model)
            yield streaming.sse("meta", {"session_id": session_id, "model": selected_model, "sources": streaming.sources_payload(plan.matches)})
            if plan.instant_reply or plan.no_answer:
                reply = plan.instant_reply or plan.no_answer
                collected.append(reply or "")
                yield streaming.sse("delta", {"t": reply or ""})
            else:
                started = time.perf_counter()
                pieces = llm_client.stream_chat_completion(
                    plan.messages, plan.provider, temperature=plan.temperature, model=plan.model
                )
                yield from streaming.relay_model_stream(pieces, collected)
                rag_pipeline.log_rag_timing(owner_id, plan, int((time.perf_counter() - started) * 1000))
            yield streaming.sse("done", {})
        except llm_client.LLMError as exc:
            yield streaming.sse("error", {"message": str(exc), "retry": True, "partial": bool(collected)})
        except Exception:  # noqa: BLE001
            yield streaming.sse("error", {"message": "", "retry": True, "partial": bool(collected)})
        finally:
            text = "".join(collected)
            if text:
                try:
                    rag_pipeline.save_turn(db, session_id, message, text)
                except Exception:  # noqa: BLE001
                    db.rollback()

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=streaming.SSE_HEADERS)


@router.post("/search", response_model=list[schemas.SemanticSearchResult])
def semantic_search(
    payload: schemas.SemanticSearchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    provider = llm_client.resolve_provider(current_user.settings)
    query_embedding = llm_client.embed_text(payload.query, provider)
    matches = rag_store.search(db, current_user.id, query_embedding, top_k=payload.top_k, similarity_threshold=current_user.settings.similarity_threshold or 0.0)
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
):
    """یک پرامپت را هم‌زمان به دو مدل رایگان می‌فرستد تا پاسخ‌ها کنار هم مقایسه شوند."""
    if payload.model_a not in config.DEFAULT_CHAT_MODELS or payload.model_b not in config.DEFAULT_CHAT_MODELS:
        raise HTTPException(status_code=400, detail="مدل انتخاب‌شده در لیست مدل‌های رایگان آماده نیست.")

    provider = llm_client.ProviderConfig(
        base_url=config.DEFAULT_PROVIDER_BASE_URL,
        api_key=config.DEFAULT_PROVIDER_API_KEY,
        chat_model=payload.model_a,
        embedding_model=config.DEFAULT_EMBEDDING_MODEL,
        is_default=True,
    )
    messages = [{"role": "user", "content": payload.prompt}]

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="battle") as executor:
        future_a = executor.submit(llm_client.timed_chat_completion, messages, provider, payload.model_a)
        future_b = executor.submit(llm_client.timed_chat_completion, messages, provider, payload.model_b)
        reply_a, ms_a, err_a = future_a.result()
        reply_b, ms_b, err_b = future_b.result()

    return schemas.BattleResponse(
        side_a=schemas.BattleSide(model=payload.model_a, reply=reply_a, elapsed_ms=ms_a, error=err_a),
        side_b=schemas.BattleSide(model=payload.model_b, reply=reply_b, elapsed_ms=ms_b, error=err_b),
    )
