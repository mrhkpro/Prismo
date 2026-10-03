"""
امنیت: هش کردن پسورد (با hashlib استاندارد پایتون - بدون نیاز به وابستگی
کامپایل‌شونده مثل bcrypt تا نصب روی ویندوز همیشه بی‌دردسر باشد)، ساخت/اعتبارسنجی
JWT، و Dependency های احراز هویت و کنترل سطح دسترسی (RBAC) برای FastAPI.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)

PBKDF2_ITERATIONS = 260_000


# ---------------------------------------------------------------------------
# هش پسورد
# ---------------------------------------------------------------------------
def hash_password(raw_password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return f"{salt}${digest}"


def verify_password(raw_password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$")
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return hmac.compare_digest(check, digest)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
def create_access_token(
    user_id: int, expires_minutes: Optional[int] = None, extra_claims: Optional[dict] = None
) -> str:
    expires_minutes = expires_minutes or config.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "iat": datetime.utcnow(),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_impersonation_token(target_user_id: int, admin_id: int) -> str:
    """توکن موقت برای قابلیت «ورود به جای کاربر» توسط ادمین."""
    return create_access_token(
        target_user_id,
        expires_minutes=config.IMPERSONATION_TOKEN_EXPIRE_MINUTES,
        extra_claims={"impersonated_by": admin_id},
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده؛ دوباره وارد شوید.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")


# ---------------------------------------------------------------------------
# Dependency های FastAPI
# ---------------------------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")
    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.") from exc
    user = db.query(models.User).filter(models.User.id == parsed_user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="کاربر یافت نشد.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="حساب کاربری شما مسدود شده است.")
    # اگر این یک توکنِ جانمایی (impersonation) است، برای شفافیت روی آبجکت کاربر نشان می‌گذاریم
    user.impersonated_by = payload.get("impersonated_by")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="این بخش فقط برای مدیر سیستم در دسترس است.")
    return current_user
