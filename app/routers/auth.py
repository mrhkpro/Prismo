from __future__ import annotations

import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import config, models, schemas, security
from ..database import get_db
from ..services import user_settings_compat
from ..timeutils import utcnow

router = APIRouter(prefix="/api/auth", tags=["احراز هویت"])


@router.post("/logout", status_code=204)
def logout():
    # The browser holds the standard bearer token in localStorage; the client clears it.
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.post("/register", response_model=schemas.TokenResponse)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    # SQLite/PostgreSQL هر دو ممکن است در برابر حساسیت حروف متفاوت رفتار کنند؛
    # مقایسه‌ی case-insensitive را صریحاً در Query انجام می‌دهیم.
    existing = db.query(models.User).filter(func.lower(models.User.username) == username.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً ثبت شده است.")

    user = models.User(
        username=username,
        org_name=payload.org_name,
        password_hash=security.hash_password(payload.password),
        role=models.UserRole.user,
        is_active=True,
    )
    db.add(user)
    db.flush()  # برای گرفتن user.id قبل از commit
    user_settings_compat.ensure_settings(db, user.id, payload.org_name or "دستیار هوشمند")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="این نام کاربری قبلاً ثبت شده است.") from exc
    token = security.create_access_token(user.id)
    return schemas.TokenResponse(access_token=token)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    username = payload.username.strip()
    user = db.query(models.User).filter(func.lower(models.User.username) == username.lower()).first()
    if not user or not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز عبور اشتباه است.", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=403, detail="حساب کاربری شما مسدود شده است.")

    user.last_login_at = utcnow()
    db.commit()

    token = security.create_access_token(user.id)
    return schemas.TokenResponse(access_token=token)


@router.post("/google-supabase", response_model=schemas.TokenResponse)
def google_supabase_login(payload: schemas.SupabaseGoogleLoginRequest, db: Session = Depends(get_db)):
    """Exchange a Supabase Auth user token for Prismo's normal application JWT."""
    supabase_token = payload.supabase_token.strip()
    if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=503, detail="تنظیمات Supabase Auth روی سرور کامل نیست.")

    url = f"{config.SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {supabase_token}",
        "apikey": config.SUPABASE_ANON_KEY,
    }
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503, detail="خطا در ارتباط با سرور احراز هویت Supabase."
        ) from exc

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="توکن Supabase نامعتبر یا منقضی شده است.")

    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="پاسخ نامعتبر از سرور احراز هویت Supabase.") from exc
    email = data.get("email") if isinstance(data, dict) else None
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(status_code=401, detail="ایمیل کاربر در اطلاعات Supabase یافت نشد.")
    email = email.strip()

    user_metadata = data.get("user_metadata", {}) or {}
    if not isinstance(user_metadata, dict):
        user_metadata = {}
    name = user_metadata.get("full_name") or user_metadata.get("name") or email.split("@", 1)[0]

    user = db.query(models.User).filter(func.lower(models.User.username) == email.lower()).first()
    if not user:
        user = models.User(
            username=email,
            org_name=str(name)[:120],
            password_hash=security.hash_password(secrets.token_urlsafe(32)),
            role=models.UserRole.user,
            is_active=True,
        )
        db.add(user)
        db.flush()
        user_settings_compat.ensure_settings(db, user.id, str(name or "دستیار هوشمند")[:120])
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            user = db.query(models.User).filter(func.lower(models.User.username) == email.lower()).first()
            if not user:
                raise HTTPException(status_code=400, detail="خطا در ثبت‌نام کاربر با حساب گوگل.") from exc

    if not user.is_active:
        raise HTTPException(status_code=403, detail="حساب کاربری شما مسدود شده است.")

    user.last_login_at = utcnow()
    db.commit()
    return schemas.TokenResponse(access_token=security.create_access_token(user.id))


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(security.get_current_user)):
    return current_user
