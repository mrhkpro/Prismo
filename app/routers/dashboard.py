from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["داشبورد"])


@router.get("/summary", response_model=schemas.DashboardSummaryOut)
def summary(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    document_count = (
        db.query(func.count(models.Document.id))
        .filter(models.Document.user_id == current_user.id)
        .scalar() or 0
    )
    chunk_count = (
        db.query(func.count(models.Chunk.id))
        .filter(models.Chunk.user_id == current_user.id)
        .scalar() or 0
    )
    playground_sessions = (
        db.query(func.count(models.ChatSession.id))
        .filter(
            models.ChatSession.user_id == current_user.id,
            models.ChatSession.source == models.ChatSource.playground,
        )
        .scalar() or 0
    )
    widget_sessions = (
        db.query(func.count(models.ChatSession.id))
        .filter(
            models.ChatSession.user_id == current_user.id,
            models.ChatSession.source == models.ChatSource.widget,
        )
        .scalar() or 0
    )
    message_count = (
        db.query(func.count(models.ChatMessage.id))
        .join(models.ChatSession, models.ChatMessage.session_id == models.ChatSession.id)
        .filter(models.ChatSession.user_id == current_user.id)
        .scalar() or 0
    )
    settings = current_user.settings
    provider_label = "مدل رایگان آماده" if settings.use_default_provider else "اتصال اختصاصی"
    return schemas.DashboardSummaryOut(
        document_count=document_count,
        chunk_count=chunk_count,
        playground_session_count=playground_sessions,
        widget_session_count=widget_sessions,
        message_count=message_count,
        provider_label=provider_label,
        widget_online=current_user.is_active,
    )
