from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import config, models, schemas, security
from ..database import get_db
from ..services import user_settings_compat
from ..timeutils import utcnow

router = APIRouter(prefix="/api/auth", tags=["احراز هویت"])
logger = logging.getLogger("prismo.auth")

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_TIMEOUT_SECONDS = 15.0
GOOGLE_OAUTH_COOKIE_MAX_AGE = 10 * 60
GOOGLE_OAUTH_ERROR_MESSAGES = {
    "google_not_configured": "ورود با گوگل هنوز پیکربندی نشده است. تنظیمات سرور را بررسی کنید.",
    "google_denied": "ورود با گوگل لغو شد.",
    "google_state": "اعتبار درخواست ورود با گوگل تأیید نشد؛ دوباره تلاش کنید.",
    "google_exchange": "تبادل امن کد ورود با گوگل ناموفق بود. تنظیمات callback را بررسی کنید.",
    "google_profile": "دریافت پروفایل معتبر از گوگل ناموفق بود.",
    "google_blocked": "این حساب کاربری غیرفعال است.",
    "google_email_conflict": "این ایمیل به حساب دیگری متصل است. با روش ورود قبلی وارد شوید.",
    "google_failed": "ورود با گوگل کامل نشد. دوباره تلاش کنید.",
}


def _cookie_secure(request: Request) -> bool:
    return config.APP_ENV == "production" or config.IS_VERCEL or request.url.scheme == "https"


def _google_redirect_uri(request: Request) -> str:
    if config.GOOGLE_REDIRECT_URI:
        return config.GOOGLE_REDIRECT_URI
    base = config.APP_PUBLIC_URL or str(request.base_url).rstrip("/")
    return f"{base}/api/auth/google/callback"


def _clear_oauth_cookies(response: Response, secure: bool) -> None:
    for suffix in ("state", "nonce", "verifier"):
        response.delete_cookie(
            f"{config.GOOGLE_OAUTH_COOKIE_PREFIX}{suffix}",
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )


def _auth_error_redirect(code: str, request: Request) -> RedirectResponse:
    response = RedirectResponse(url=f"/index.html?auth_error={code}", status_code=303)
    response.headers["Cache-Control"] = "no-store"
    _clear_oauth_cookies(response, _cookie_secure(request))
    return response


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _exchange_google_code(code: str, redirect_uri: str, verifier: str) -> dict:
    """Exchange an authorization code server-side; client secret stays server-only."""
    response = httpx.post(
        GOOGLE_TOKEN_ENDPOINT,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
        timeout=GOOGLE_OAUTH_TIMEOUT_SECONDS,
        headers={"Accept": "application/json"},
    )
    if response.status_code >= 400:
        # Never log the request body or provider response, which may contain tokens.
        logger.warning("Google OAuth token exchange rejected (HTTP %s)", response.status_code)
        raise ValueError("token_exchange_rejected")
    result = response.json()
    if not isinstance(result, dict) or not result.get("id_token"):
        raise ValueError("id_token_missing")
    return result


def _verify_google_id_token(raw_id_token: str) -> dict:
    """Verify Google's signature, issuer, expiry and audience using Google's library."""
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import id_token

    claims = id_token.verify_oauth2_token(raw_id_token, GoogleRequest(), config.GOOGLE_CLIENT_ID)
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("issuer_invalid")
    return claims


def _google_username(db: Session, email: str) -> str:
    local_part = email.split("@", 1)[0].lower()
    base = re.sub(r"[^a-z0-9._-]+", "-", local_part).strip("._-")
    if len(base) < 3:
        base = f"google-{base or 'user'}"
    base = base[:54]
    candidate = base
    index = 1
    while db.query(models.User.id).filter(func.lower(models.User.username) == candidate.lower()).first():
        index += 1
        suffix = f"-{index}"
        candidate = f"{base[:64 - len(suffix)]}{suffix}"
    return candidate


def _get_or_create_google_user(db: Session, claims: dict) -> models.User:
    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    verified = claims.get("email_verified") is True or str(claims.get("email_verified", "")).lower() == "true"
    if not subject or not email or not verified or "@" not in email:
        raise ValueError("verified_email_required")

    user = db.query(models.User).filter(models.User.google_sub == subject).first()
    if user is None:
        user = db.query(models.User).filter(
            or_(func.lower(models.User.email) == email, func.lower(models.User.username) == email)
        ).first()
        if user is not None and user.google_sub and user.google_sub != subject:
            raise PermissionError("email_already_linked")
        if user is not None:
            # Google verifies this address; linking is safe only when it matches
            # the user's stored email or their existing email-style username.
            user.email = email
            user.google_sub = subject
        else:
            user = models.User(
                username=_google_username(db, email),
                email=email,
                google_sub=subject,
                password_hash=security.hash_password(secrets.token_urlsafe(48)),
                role=models.UserRole.user,
                is_active=True,
            )
            db.add(user)
            db.flush()
            user_settings_compat.ensure_settings(db, user.id, email.split("@", 1)[0][:120])

    if not user.is_active:
        raise PermissionError("account_inactive")
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.get("/google/start", name="google_oauth_start")
def google_oauth_start(request: Request):
    if not config.GOOGLE_OAUTH_ENABLED:
        return _auth_error_redirect("google_not_configured", request)

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    query = urlencode({
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": _google_redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": _pkce_challenge(verifier),
        "code_challenge_method": "S256",
        "prompt": "select_account",
    })
    response = RedirectResponse(url=f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{query}", status_code=302)
    response.headers["Cache-Control"] = "no-store"
    secure = _cookie_secure(request)
    for suffix, value in (("state", state), ("nonce", nonce), ("verifier", verifier)):
        response.set_cookie(
            f"{config.GOOGLE_OAUTH_COOKIE_PREFIX}{suffix}", value,
            max_age=GOOGLE_OAUTH_COOKIE_MAX_AGE, path="/", secure=secure,
            httponly=True, samesite="lax",
        )
    return response


@router.get("/google/callback", name="google_oauth_callback")
def google_oauth_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    secure = _cookie_secure(request)
    if error:
        return _auth_error_redirect("google_denied", request)
    expected_state = request.cookies.get(f"{config.GOOGLE_OAUTH_COOKIE_PREFIX}state", "")
    expected_nonce = request.cookies.get(f"{config.GOOGLE_OAUTH_COOKIE_PREFIX}nonce", "")
    verifier = request.cookies.get(f"{config.GOOGLE_OAUTH_COOKIE_PREFIX}verifier", "")
    if not code or not state or not expected_state or not hmac.compare_digest(state, expected_state):
        return _auth_error_redirect("google_state", request)
    if not expected_nonce or not verifier or not config.GOOGLE_OAUTH_ENABLED:
        return _auth_error_redirect("google_not_configured" if not config.GOOGLE_OAUTH_ENABLED else "google_state", request)

    try:
        token_data = _exchange_google_code(code, _google_redirect_uri(request), verifier)
        claims = _verify_google_id_token(token_data["id_token"])
        if not hmac.compare_digest(str(claims.get("nonce") or ""), expected_nonce):
            raise ValueError("nonce_invalid")
    except Exception as exc:  # noqa: BLE001 - provider errors are converted to safe UI messages.
        logger.warning("Google OAuth verification failed (%s)", type(exc).__name__)
        return _auth_error_redirect("google_exchange" if isinstance(exc, (httpx.HTTPError, ValueError)) else "google_profile", request)

    try:
        user = _get_or_create_google_user(db, claims)
    except PermissionError as exc:
        db.rollback()
        code = "google_blocked" if str(exc) == "account_inactive" else "google_email_conflict"
        return _auth_error_redirect(code, request)
    except IntegrityError:
        db.rollback()
        return _auth_error_redirect("google_failed", request)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.exception("Could not persist Google OAuth user (%s)", type(exc).__name__)
        return _auth_error_redirect("google_failed", request)

    token = security.create_access_token(user.id)
    response = RedirectResponse(url="/index.html?oauth=success", status_code=303)
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        config.ACCESS_TOKEN_COOKIE_NAME,
        token,
        max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        secure=secure,
        httponly=True,
        samesite="lax",
    )
    _clear_oauth_cookies(response, secure)
    return response


@router.post("/logout", status_code=204)
def logout(request: Request):
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(
        config.ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        secure=_cookie_secure(request),
        httponly=True,
        samesite="lax",
    )
    return response


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


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(security.get_current_user)):
    return current_user
