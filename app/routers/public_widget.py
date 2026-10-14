import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas, i18n
from ..database import get_db
from ..services import user_settings_compat
from ..services import answer_cache, llm_client, rag_pipeline, rate_limit, streaming, widget_extras


logger = logging.getLogger("prismo.public_widget")

router = APIRouter(prefix="/public/widget", tags=["ویجت عمومی (بدون نیاز به ورود)"])

WIDGET_PRIVATE_HEADERS = {
    "Cache-Control": "no-store, no-cache, no-transform, private",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Robots-Tag": "noindex, noarchive, nosnippet",
}


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
        reply, _matches = rag_pipeline.run_rag_chat(db, owner, session, payload.message, language=i18n.get_language(request))
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
                pieces = llm_client.stream_chat_completion(
                    plan.messages, plan.provider, temperature=plan.temperature, model=plan.model
                )
                yield from streaming.relay_model_stream(pieces, collected)
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
