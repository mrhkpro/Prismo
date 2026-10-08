from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import user_settings_compat

router = APIRouter(prefix="/api/dashboard", tags=["داشبورد"])


@router.get("/summary", response_model=schemas.DashboardSummaryOut)
def summary(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all dashboard counters in one SQL round-trip."""
    uid = current_user.id

    doc_count = select(func.count(models.Document.id)).where(models.Document.user_id == uid).scalar_subquery()
    chunk_count = select(func.count(models.Chunk.id)).where(models.Chunk.user_id == uid).scalar_subquery()
    playground_count = select(func.count(models.ChatSession.id)).where(
        models.ChatSession.user_id == uid,
        models.ChatSession.source == models.ChatSource.playground,
    ).scalar_subquery()
    widget_count = select(func.count(models.ChatSession.id)).where(
        models.ChatSession.user_id == uid,
        models.ChatSession.source == models.ChatSource.widget,
    ).scalar_subquery()
    message_count = select(func.count(models.ChatMessage.id)).join(
        models.ChatSession, models.ChatMessage.session_id == models.ChatSession.id
    ).where(models.ChatSession.user_id == uid).scalar_subquery()

    row = db.query(
        doc_count.label("document_count"),
        chunk_count.label("chunk_count"),
        playground_count.label("playground_session_count"),
        widget_count.label("widget_session_count"),
        message_count.label("message_count"),
    ).one()

    settings = user_settings_compat.get(db, current_user.id)
    provider_label = "مدل رایگان آماده" if settings.use_default_provider else "اتصال اختصاصی"
    return schemas.DashboardSummaryOut(
        document_count=int(row.document_count or 0),
        chunk_count=int(row.chunk_count or 0),
        playground_session_count=int(row.playground_session_count or 0),
        widget_session_count=int(row.widget_session_count or 0),
        message_count=int(row.message_count or 0),
        provider_label=provider_label,
        widget_online=current_user.is_active,
    )
