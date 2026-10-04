from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import llm_client, rag_pipeline, rate_limit

router = APIRouter(prefix="/public/widget", tags=["ویجت عمومی (بدون نیاز به ورود)"])


def _get_owner_by_widget(db: Session, widget_id: str) -> models.User:
    settings = db.query(models.UserSettings).filter(models.UserSettings.widget_id == widget_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="ویجت یافت نشد.")
    return settings.user


@router.get("/{widget_id}/config", response_model=schemas.WidgetPublicConfig)
def widget_public_config(widget_id: str, db: Session = Depends(get_db)):
    owner = _get_owner_by_widget(db, widget_id)
    s = owner.settings
    return schemas.WidgetPublicConfig(
        widget_id=s.widget_id,
        title=s.widget_title,
        welcome_message=s.widget_welcome_message,
        color=s.widget_color,
        org_name=owner.org_name,
        online=owner.is_active,
    )


@router.post("/{widget_id}/chat", response_model=schemas.WidgetChatResponse)
def widget_chat(widget_id: str, payload: schemas.WidgetChatRequest, request: Request, db: Session = Depends(get_db)):
    owner = _get_owner_by_widget(db, widget_id)
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.public_widget_limiter.allow(f"{widget_id}:{client_ip}"):
        raise HTTPException(status_code=429, detail="تعداد درخواست‌ها زیاد است. چند لحظه بعد دوباره تلاش کنید.")

    if not owner.is_active:
        # مسدودشدن کاربر باید بلافاصله عملکرد ویجت روی سایت‌های دیگر را هم متوقف کند
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
        reply, _matches = rag_pipeline.run_rag_chat(db, owner, session, payload.message)
    except llm_client.LLMError:
        db.commit()
        raise

    rag_pipeline.save_turn(db, session, payload.message, reply)

    return schemas.WidgetChatResponse(session_id=session.id, reply=reply)
