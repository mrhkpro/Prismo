import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas, i18n
from ..database import get_db
from ..services import user_settings_compat
from ..services import answer_cache, llm_client, rag_pipeline, rate_limit, streaming, widget_extras
from ..services.response_quality import looks_like_mixed_script_noise


logger = logging.getLogger("prismo.public_widget")

router = APIRouter(prefix="/public/widget", tags=["ویجت عمومی (بدون نیاز به ورود)"])

WIDGET_PRIVATE_HEADERS = {
    "Cache-Control": "no-store, no-cache, no-transform, private",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Robots-Tag": "noindex, noarchive, nosnippet",
}


def _text_chunks(text: str, chunk_size: int = 48):
    """Split a retry response into small deltas to preserve the widget's typing effect."""
    for index in range(0, len(text), chunk_size):
        yield text[index:index + chunk_size]


def _recover_widget_model_reply(plan, collected: list[str], language: str):
    """Retry corrupted output once, then return a readable localized diagnostic."""
    logger.warning("widget_model_output_quality_rejected model=%s language=%s", plan.model, language)
    retry_text = ""
    try:
        retry_text = llm_client.chat_completion(
            plan.messages,
            plan.provider,
            temperature=min(float(plan.temperature or 0.2), 0.2),
            model=plan.model,
            max_tokens=480,
            widget_retry=True,
        )
    except llm_client.LLMError as exc:
        logger.warning("widget_model_quality_retry_failed model=%s error_type=%s", plan.model, type(exc).__name__)

    if retry_text and not looks_like_mixed_script_noise(retry_text):
        yield from streaming.relay_model_stream(_text_chunks(retry_text), collected)
    else:
        plan.cache_allowed = False
        fallback = (
            "The selected model returned unreadable text. Check the active chat model and test its connection in settings, then try again."
            if language == "en" else
            "مدل انتخاب‌شده متن قابل‌خواندنی تولید نکرد. مدل چت فعال و اتصال آن را در تنظیمات بررسی کنید و دوباره تلاش کنید."
        )
        yield from streaming.relay_model_stream([fallback], collected)


def _stream_checked_model_reply(plan, collected: list[str], language: str):
    """Stream normal answers quickly, but suppress obvious mixed-script noise before display.

    The first 180 characters are buffered solely for the quality check. If the response
    resembles corrupted token soup, retry once at a low temperature; never expose the
    corrupted stream to website visitors or save it in the answer cache.
    """
    pieces = iter(llm_client.stream_chat_completion(
        plan.messages, plan.provider, temperature=plan.temperature, model=plan.model
    ))
    pending: list[str] = []
    sample = ""
    released = False

    for piece in pieces:
        sample += piece
        if released:
            # Continue checking later chunks too. If corruption starts after a
            # plausible opening sentence, clear the already-rendered draft in the
            # widget and replace it with one clean recovery answer.
            if looks_like_mixed_script_noise(sample[-1600:]):
                close = getattr(pieces, "close", None)
                if callable(close):
                    close()
                yield streaming.sse("reset", {})
                collected.clear()
                yield from _recover_widget_model_reply(plan, collected, language)
                return
            yield from streaming.relay_model_stream([piece], collected)
            continue

        pending.append(piece)
        if len(sample) < 180:
            continue

        if looks_like_mixed_script_noise(sample):
            close = getattr(pieces, "close", None)
            if callable(close):
                close()
            yield from _recover_widget_model_reply(plan, collected, language)
            return

        released = True
        yield from streaming.relay_model_stream(pending, collected)
        pending.clear()

    if not sample.strip():
        # Some OpenAI-compatible providers complete an SSE request but send no
        # visible content delta. Recover once rather than ending with an empty bubble.
        yield from _recover_widget_model_reply(plan, collected, language)
    elif pending:
        if not released and looks_like_mixed_script_noise(sample):
            yield from _recover_widget_model_reply(plan, collected, language)
        else:
            yield from streaming.relay_model_stream(pending, collected)


def _get_owner_by_widget(db: Session, widget_id: str) -> models.User:
    """Find owner without loading the whole UserSettings ORM row."""
    owner = (
        db.query(models.User)
        .join(models.UserSettings, models.UserSettings.user_id == models.User.id)
        .filter(models.UserSettings.widget_id == widget_id)
        .first()
    )
    if not owner:
        raise HTTPException(status_code=404, detail="ویجت یافت نشد.")
    return owner


@router.get("/{widget_id}/config", response_model=schemas.WidgetPublicConfig)
def widget_public_config(widget_id: str, request: Request, db: Session = Depends(get_db)):
    owner = _get_owner_by_widget(db, widget_id)
    s = user_settings_compat.get(db, owner.id)
    language = i18n.get_language(request)
    payload = schemas.WidgetPublicConfig(
        widget_id=s.widget_id,
        title=i18n.localize_widget_title(s.widget_title, language),
        welcome_message=i18n.localize_widget_welcome(s.widget_welcome_message, language),
        color=s.widget_color,
        org_name=owner.org_name,
        online=owner.is_active,
        extras=widget_extras.load(db, owner.id)[0],
    )
    return JSONResponse(content=payload.model_dump(), headers=WIDGET_PRIVATE_HEADERS)


@router.post("/{widget_id}/chat", response_model=schemas.WidgetChatResponse)
def widget_chat(widget_id: str, payload: schemas.WidgetChatRequest, request: Request, db: Session = Depends(get_db)):
    owner = _get_owner_by_widget(db, widget_id)
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.public_widget_limiter.allow(f"{widget_id}:{client_ip}"):
        raise HTTPException(status_code=429, detail="تعداد درخواست‌ها زیاد است. چند لحظه بعد دوباره تلاش کنید.")

    if not owner.is_active:
        raise HTTPException(status_code=403, detail="این سرویس موقتاً در دسترس نیست.")

    session = None
    if payload.session_id:
        session = (
            db.query(models.ChatSession)
            .filter(
                models.ChatSession.id == payload.session_id,
                models.ChatSession.user_id == owner.id,
                models.ChatSession.source == models.ChatSource.widget,
            )
            .first()
        )
    if not session:
        session = models.ChatSession(
            user_id=owner.id, source=models.ChatSource.widget, visitor_label=payload.visitor_label
        )
        db.add(session)
        db.flush()

    try:
        reply, _matches = rag_pipeline.run_rag_chat(
            db, owner, session, payload.message,
            language=i18n.get_language(request), widget_mode=True,
        )
    except llm_client.LLMError:
        db.commit()
        raise

    rag_pipeline.save_turn(db, session, payload.message, reply)
    return JSONResponse(content=schemas.WidgetChatResponse(session_id=session.id, reply=reply).model_dump(), headers=WIDGET_PRIVATE_HEADERS)


@router.post("/{widget_id}/chat/stream")
def widget_chat_stream(widget_id: str, payload: schemas.WidgetChatRequest, request: Request, db: Session = Depends(get_db)):
    owner = _get_owner_by_widget(db, widget_id)
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.public_widget_limiter.allow(f"{widget_id}:{client_ip}"):
        raise HTTPException(status_code=429, detail="تعداد درخواست‌ها زیاد است. چند لحظه بعد دوباره تلاش کنید.")
    if not owner.is_active:
        raise HTTPException(status_code=403, detail="این سرویس موقتاً در دسترس نیست.")

    session = None
    if payload.session_id:
        session = (
            db.query(models.ChatSession)
            .filter(
                models.ChatSession.id == payload.session_id,
                models.ChatSession.user_id == owner.id,
                models.ChatSession.source == models.ChatSource.widget,
            )
            .first()
        )
    if not session:
        session = models.ChatSession(
            user_id=owner.id, source=models.ChatSource.widget, visitor_label=payload.visitor_label
        )
        db.add(session)
        db.flush()
    session_id, owner_id, message = session.id, owner.id, payload.message
    language = i18n.get_language(request)
    db.commit()
    bind = db.get_bind()

    def event_stream():
        collected: list[str] = []
        yield ": qz-ready\n\n"
        plan = None
        try:
            from sqlalchemy.orm import Session as DBSession
            with DBSession(bind=bind, autoflush=False) as work_db:
                chat_owner = work_db.get(models.User, owner_id)
                chat_session = work_db.get(models.ChatSession, session_id)
                plan = rag_pipeline.prepare_rag_chat(work_db, chat_owner, chat_session, message, language=language)
                meta = {"session_id": session_id, "sources": streaming.sources_payload(plan.matches)}
            yield streaming.sse("meta", meta)
            if plan.instant_reply or plan.no_answer:
                reply = plan.instant_reply or plan.no_answer
                collected.append(reply or "")
                yield streaming.sse("delta", {"t": reply or ""})
            else:
                yield from _stream_checked_model_reply(plan, collected, language)
            yield streaming.sse("done", {})
        except llm_client.LLMError:
            yield streaming.sse("error", {"message": "", "retry": True, "partial": bool(collected)})
        except Exception:  # noqa: BLE001
            logger.exception("public widget stream failed")
            yield streaming.sse("error", {"message": "", "retry": True, "partial": bool(collected)})
        finally:
            text = "".join(collected)
            if text:
                try:
                    from sqlalchemy.orm import Session as DBSession
                    with DBSession(bind=bind, autoflush=False) as save_db:
                        if plan is not None and plan.cache_allowed and not plan.cache_hit:
                            answer_cache.store(save_db, owner_id, plan.cache_key, text, plan.matches)
                        rag_pipeline.save_turn(save_db, session_id, message, text)
                except Exception:  # noqa: BLE001
                    logger.exception("could not save streamed widget turn")

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=streaming.SSE_HEADERS)
