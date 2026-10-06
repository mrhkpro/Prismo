from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import get_db
from ..services import injection_scanner
from ..security import create_impersonation_token, require_admin

router = APIRouter(prefix="/api/admin", tags=["پنل مدیریت (ادمین)"])


def _active_admin_count(db: Session) -> int:
    return (
        db.query(func.count(models.User.id))
        .filter(models.User.role == models.UserRole.admin, models.User.is_active.is_(True))
        .scalar()
        or 0
    )


def _ensure_admin_pool_survives(db: Session, user: models.User, making_admin: bool = False) -> None:
    if making_admin:
        return
    if user.role == models.UserRole.admin and user.is_active and _active_admin_count(db) <= 1:
        raise HTTPException(status_code=400, detail="حداقل یک مدیر فعال باید در سیستم باقی بماند.")



# ---------------------------------------------------------------------------
# ۲.۲ داشبورد آمار کلان و تله‌متری
# ---------------------------------------------------------------------------
@router.get("/stats", response_model=schemas.AdminStatsOut)
def stats(db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    active_users = db.query(func.count(models.User.id)).filter(models.User.is_active.is_(True)).scalar() or 0
    admin_users = db.query(func.count(models.User.id)).filter(models.User.role == models.UserRole.admin).scalar() or 0
    total_documents = db.query(func.count(models.Document.id)).scalar() or 0
    total_chunks = db.query(func.count(models.Chunk.id)).scalar() or 0
    total_sessions = db.query(func.count(models.ChatSession.id)).scalar() or 0
    total_messages = db.query(func.count(models.ChatMessage.id)).scalar() or 0
    widget_sessions = (
        db.query(func.count(models.ChatSession.id))
        .filter(models.ChatSession.source == models.ChatSource.widget).scalar() or 0
    )
    playground_sessions = total_sessions - widget_sessions
    flagged_messages = db.query(func.count(models.ChatMessage.id)).filter(models.ChatMessage.is_flagged.is_(True)).scalar() or 0
    unresolved_flags = (
        db.query(func.count(models.ChatMessage.id))
        .filter(models.ChatMessage.is_flagged.is_(True), models.ChatMessage.resolved.is_(False))
        .scalar() or 0
    )

    return schemas.AdminStatsOut(
        total_users=total_users,
        active_users=active_users,
        blocked_users=total_users - active_users,
        admin_users=admin_users,
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_sessions=total_sessions,
        total_messages=total_messages,
        widget_sessions=widget_sessions,
        playground_sessions=playground_sessions,
        flagged_messages=flagged_messages,
        unresolved_flags=unresolved_flags,
    )


# ---------------------------------------------------------------------------
# ۲.۳ مدیریت و پایش کاربران
# ---------------------------------------------------------------------------
def _user_to_admin_out(db: Session, user: models.User) -> schemas.AdminUserOut:
    doc_count = db.query(func.count(models.Document.id)).filter(models.Document.user_id == user.id).scalar() or 0
    session_count = db.query(func.count(models.ChatSession.id)).filter(models.ChatSession.user_id == user.id).scalar() or 0
    return schemas.AdminUserOut(
        id=user.id, username=user.username, org_name=user.org_name, role=user.role.value,
        is_active=user.is_active, created_at=user.created_at, last_login_at=user.last_login_at,
        document_count=doc_count, session_count=session_count,
    )


@router.get("/users", response_model=list[schemas.AdminUserOut])
def list_users(
    search: Optional[str] = Query(default=None, max_length=64),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    query = db.query(models.User)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(models.User.username.ilike(like), models.User.org_name.ilike(like)))
    users = query.order_by(models.User.created_at.desc()).offset(offset).limit(limit).all()
    user_ids = [u.id for u in users]
    if not user_ids:
        return []
    doc_counts = dict(
        db.query(models.Document.user_id, func.count(models.Document.id))
        .filter(models.Document.user_id.in_(user_ids))
        .group_by(models.Document.user_id)
        .all()
    )
    session_counts = dict(
        db.query(models.ChatSession.user_id, func.count(models.ChatSession.id))
        .filter(models.ChatSession.user_id.in_(user_ids))
        .group_by(models.ChatSession.user_id)
        .all()
    )
    return [
        schemas.AdminUserOut(
            id=u.id, username=u.username, org_name=u.org_name, role=u.role.value,
            is_active=u.is_active, created_at=u.created_at, last_login_at=u.last_login_at,
            document_count=int(doc_counts.get(u.id, 0)), session_count=int(session_counts.get(u.id, 0)),
        )
        for u in users
    ]


def _get_user_or_404(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    return user


@router.get("/users/{user_id}", response_model=schemas.AdminUserDetailOut)
def get_user_detail(user_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    user = _get_user_or_404(db, user_id)
    base = _user_to_admin_out(db, user)
    s = user.settings
    g = lambda name, default: (getattr(s, name, None) if s is not None and getattr(s, name, None) is not None else default)
    return schemas.AdminUserDetailOut(
        **base.model_dump(),
        use_default_provider=bool(g("use_default_provider", True)),
        api_key_set=bool(g("api_key", "")),
        base_url=g("base_url", None),
        chat_model=g("chat_model", config.DEFAULT_CHAT_MODEL),
        embedding_model=g("embedding_model", config.DEFAULT_EMBEDDING_MODEL),
        system_prompt=g("system_prompt", config.DEFAULT_SYSTEM_PROMPT),
        temperature=g("temperature", config.DEFAULT_TEMPERATURE),
        top_k=g("top_k", config.DEFAULT_TOP_K),
        similarity_threshold=g("similarity_threshold", config.DEFAULT_SIMILARITY_THRESHOLD),
        widget_id=g("widget_id", ""),
    )


@router.post("/users/{user_id}/block")
def block_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="نمی‌توانید حساب خودتان را مسدود کنید.")
    _ensure_admin_pool_survives(db, user)
    user.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/unblock")
def unblock_user(user_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    user = _get_user_or_404(db, user_id)
    user.is_active = True
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/role")
def change_role(
    user_id: int,
    payload: schemas.RoleUpdateRequest,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    if payload.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="نقش نامعتبر است.")
    user = _get_user_or_404(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="نمی‌توانید نقش خودتان را تغییر دهید.")
    _ensure_admin_pool_survives(db, user, making_admin=payload.role == "admin")
    user.role = models.UserRole(payload.role)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# ۲.۴ قابلیت بازرسی و پشتیبانی
# ---------------------------------------------------------------------------
@router.get("/users/{user_id}/documents", response_model=list[schemas.DocumentOut])
def inspect_user_documents(user_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    user = _get_user_or_404(db, user_id)
    rows = (
        db.query(models.Document, func.count(models.Chunk.id))
        .outerjoin(models.Chunk, models.Chunk.document_id == models.Document.id)
        .filter(models.Document.user_id == user.id)
        .group_by(models.Document.id)
        .order_by(models.Document.created_at.desc())
        .all()
    )
    return [
        schemas.DocumentOut(id=d.id, title=d.title, chunk_count=int(n), created_at=d.created_at, updated_at=d.updated_at)
        for d, n in rows
    ]


@router.get("/users/{user_id}/sessions", response_model=list[schemas.SessionOut])
def inspect_user_sessions(user_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    user = _get_user_or_404(db, user_id)
    sessions = (
        db.query(models.ChatSession).filter(models.ChatSession.user_id == user.id)
        .order_by(models.ChatSession.created_at.desc()).limit(200).all()
    )
    return _sessions_out(db, sessions)


@router.get("/sessions/{session_id}/messages", response_model=list[schemas.MessageOut])
def session_messages(session_id: str, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="نشست یافت نشد.")
    rows = (
        db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at, models.ChatMessage.id).all()
    )
    return [
        schemas.MessageOut(
            id=m.id, role=m.role, content=m.content or "", is_flagged=bool(m.is_flagged),
            flag_reason=m.flag_reason, resolved=bool(m.resolved), created_at=m.created_at,
        )
        for m in rows
    ]


@router.post("/users/{user_id}/impersonate", response_model=schemas.ImpersonateResponse)
def impersonate_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    """ورود موقت به‌جای کاربر (User as Login) برای عیب‌یابی/پشتیبانی."""
    user = _get_user_or_404(db, user_id)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="کاربر مسدود است و نمی‌توان به‌جای او وارد شد.")
    token = create_impersonation_token(target_user_id=user.id, admin_id=admin.id)
    return schemas.ImpersonateResponse(access_token=token, target_username=user.username)


# ---------------------------------------------------------------------------
# ۲.۵ گزارش جامع مکالمات و مانیتورینگ امنیتی
# ---------------------------------------------------------------------------
def _sessions_out(db: Session, sessions: list) -> list:
    ids = [x.id for x in sessions]
    counts, flags = {}, set()
    if ids:
        counts = dict(
            db.query(models.ChatMessage.session_id, func.count(models.ChatMessage.id))
            .filter(models.ChatMessage.session_id.in_(ids)).group_by(models.ChatMessage.session_id).all()
        )
        flags = {
            r[0] for r in db.query(models.ChatMessage.session_id)
            .filter(models.ChatMessage.session_id.in_(ids), models.ChatMessage.is_flagged.is_(True)).distinct().all()
        }
    return [
        schemas.SessionOut(
            id=x.id, source=x.source.value, visitor_label=x.visitor_label,
            created_at=x.created_at, message_count=int(counts.get(x.id, 0)), has_flag=x.id in flags,
        )
        for x in sessions
    ]


@router.get("/conversations", response_model=list[schemas.SessionOut])
def all_conversations(
    source: Optional[str] = Query(default=None),
    flagged_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    query = db.query(models.ChatSession)
    if source in ("playground", "widget"):
        query = query.filter(models.ChatSession.source == models.ChatSource(source))
    if flagged_only:
        query = query.filter(
            db.query(models.ChatMessage.id)
            .filter(models.ChatMessage.session_id == models.ChatSession.id)
            .filter(models.ChatMessage.is_flagged.is_(True))
            .exists()
        )
    sessions = query.order_by(models.ChatSession.created_at.desc()).offset(offset).limit(limit).all()
    return _sessions_out(db, sessions)


def _source_value(session: models.ChatSession) -> str:
    source = session.source
    return getattr(source, "value", source) or ""


@router.get("/security/flags", response_model=list[schemas.FlaggedMessageOut])
def security_flags(
    resolved: Optional[bool] = Query(default=None),
    severity: Optional[str] = Query(default=None, pattern="^(critical|high|medium)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    query = (
        db.query(models.ChatMessage, models.ChatSession, models.User)
        .join(models.ChatSession, models.ChatMessage.session_id == models.ChatSession.id)
        .join(models.User, models.ChatSession.user_id == models.User.id)
        .filter(models.ChatMessage.is_flagged.is_(True))
    )
    if resolved is not None:
        query = query.filter(models.ChatMessage.resolved.is_(resolved))
    # شدت از روی کدهای متن دلیل محاسبه می‌شود؛ برای فیلتر دقیق، کمی بیشتر می‌خوانیم و در پایتون برش می‌زنیم
    rows = query.order_by(models.ChatMessage.created_at.desc()).offset(offset).limit(limit if not severity else 500).all()

    result = []
    for msg, session, user in rows:
        info = injection_scanner.describe_reason(msg.flag_reason)
        if severity and info["severity"] != severity:
            continue
        result.append(
            schemas.FlaggedMessageOut(
                id=msg.id, session_id=session.id, owner_username=user.username, role=msg.role,
                content=msg.content, flag_reason=msg.flag_reason, resolved=bool(msg.resolved), created_at=msg.created_at,
                owner_id=user.id, owner_org_name=user.org_name, owner_is_active=bool(user.is_active),
                source=_source_value(session), visitor_label=session.visitor_label,
                severity=info["severity"], category=info["category"], label=info["label"], codes=info["codes"],
            )
        )
        if len(result) >= limit:
            break
    return result


@router.get("/security/summary", response_model=schemas.SecuritySummaryOut)
def security_summary(db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    """شمارنده‌های سبکِ هشدار برای نشان‌دادن Badge و اعلان زنده در همه‌ی صفحه‌های ادمین."""
    rows = (
        db.query(models.ChatMessage.id, models.ChatMessage.flag_reason, models.ChatMessage.created_at, models.ChatSession.source, models.User.username)
        .join(models.ChatSession, models.ChatMessage.session_id == models.ChatSession.id)
        .join(models.User, models.ChatSession.user_id == models.User.id)
        .filter(models.ChatMessage.is_flagged.is_(True), models.ChatMessage.resolved.is_(False))
        .order_by(models.ChatMessage.created_at.desc(), models.ChatMessage.id.desc())
        .limit(500)
        .all()
    )
    counts = {"critical": 0, "high": 0, "medium": 0}
    extraction = 0
    latest = None
    for msg_id, reason, created_at, source, username in rows:
        info = injection_scanner.describe_reason(reason)
        counts[info["severity"]] += 1
        if info["category"] == "prompt_extraction":
            extraction += 1
        if latest is None:
            latest = schemas.SecurityAlertOut(
                id=msg_id, owner_username=username, severity=info["severity"], label=info["label"],
                source=getattr(source, "value", source), created_at=created_at,
            )
    return schemas.SecuritySummaryOut(
        unresolved_total=len(rows), critical=counts["critical"], high=counts["high"], medium=counts["medium"],
        prompt_extraction=extraction, latest=latest,
    )


@router.post("/security/flags/{message_id}/resolve")
def resolve_flag(message_id: int, db: Session = Depends(get_db), _admin: models.User = Depends(require_admin)):
    msg = db.query(models.ChatMessage).filter(models.ChatMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="پیام یافت نشد.")
    msg.resolved = True
    db.commit()
    return {"ok": True}
