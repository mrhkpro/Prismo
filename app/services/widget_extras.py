"""تنظیمات اضافه‌ی ویجت (حیوان خانگی، موقعیت، پاسخ‌های سریع، پیام تیزر).

این تنظیمات عمداً در ستون جدا و با SQL خام خوانده/نوشته می‌شوند، نه از طریق مدل ORM:
  * اگر ستون `widget_extras` هنوز در دیتابیس نباشد، هیچ query دیگری از سایت (لاگین، چت، ...) خراب نمی‌شود؛
  * خواندنِ ناموفق فقط مقادیر پیش‌فرض را برمی‌گرداند و ویجت مثل قبل کار می‌کند؛
  * اولین ذخیره‌ی موفق، ستون را خودکار می‌سازد (ALTER TABLE ... ADD COLUMN IF NOT EXISTS)؛ اگر دیتابیس
    اجازه‌ی ALTER ندهد، کاربر پیام روشنی می‌گیرد که فایل supabase/migrations/002_widget_extras.sql را اجرا کند.
"""
import json
import logging
import re
import time
import weakref
from typing import Any, Dict, Tuple

from fastapi import HTTPException
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .. import config

logger = logging.getLogger("quasar.widget_extras")

PETS = ("dog", "cat", "raccoon")
POSITIONS = ("bottom-left", "bottom-right")
MAX_QUICK_REPLIES = 4
MAX_QUICK_REPLY_CHARS = 60
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULTS: Dict[str, Any] = {
    "pet_enabled": False,
    "pet": "dog",
    "pet_color": "#C98A4B",
    "position": "bottom-left",
    "teaser_enabled": False,
    "quick_replies": [],
}

MIGRATION_HINT = (
    "برای ذخیره‌ی این تنظیمات، فایل supabase/migrations/002_widget_extras.sql را یک‌بار در Supabase (SQL Editor) اجرا کن."
)

# موتورهایی که ستون برایشان تأیید شده؛ کلید = خودِ engine تا تست‌ها (با دیتابیس‌های جدا) به هم نریزند
_ready_engines: "weakref.WeakSet" = weakref.WeakSet()
_last_failed_at: Dict[int, float] = {}
_RETRY_AFTER_SECONDS = 60


def _ensure_column(bind) -> bool:
    """ستون widget_extras را (در صورت نبود) می‌سازد. نتیجه‌ی موفق در حافظه‌ی پروسه کش می‌شود."""
    if bind in _ready_engines:
        return True
    if time.time() - _last_failed_at.get(id(bind), 0.0) < _RETRY_AFTER_SECONDS:
        return False
    try:
        if config.IS_POSTGRES:
            with bind.begin() as conn:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS widget_extras text"))
        else:
            columns = {c["name"] for c in inspect(bind).get_columns("user_settings")}
            if "widget_extras" not in columns:
                with bind.begin() as conn:
                    conn.execute(text("ALTER TABLE user_settings ADD COLUMN widget_extras TEXT"))
        _ready_engines.add(bind)
        return True
    except Exception as exc:  # noqa: BLE001
        _last_failed_at[id(bind)] = time.time()
        logger.warning("widget_extras column is not available: %s", exc)
        return False


def sanitize(raw: Any, base: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """ورودی کاربر را اعتبارسنجی می‌کند و روی مقدارهای فعلی (یا پیش‌فرض) ادغام می‌کند."""
    result = dict(DEFAULTS)
    result["quick_replies"] = []
    if base:
        result.update({k: v for k, v in base.items() if k in DEFAULTS})
    if not isinstance(raw, dict):
        return result

    if "pet_enabled" in raw:
        result["pet_enabled"] = bool(raw["pet_enabled"])
    if "teaser_enabled" in raw:
        result["teaser_enabled"] = bool(raw["teaser_enabled"])
    if "pet" in raw:
        if raw["pet"] not in PETS:
            raise HTTPException(status_code=422, detail="حیوان خانگی نامعتبر است.")
        result["pet"] = raw["pet"]
    if "pet_color" in raw:
        if not isinstance(raw["pet_color"], str) or not _HEX.match(raw["pet_color"]):
            raise HTTPException(status_code=422, detail="رنگ حیوان خانگی باید به شکل #RRGGBB باشد.")
        result["pet_color"] = raw["pet_color"]
    if "position" in raw:
        if raw["position"] not in POSITIONS:
            raise HTTPException(status_code=422, detail="موقعیت ویجت نامعتبر است.")
        result["position"] = raw["position"]
    if "quick_replies" in raw:
        items = raw["quick_replies"]
        if not isinstance(items, list):
            raise HTTPException(status_code=422, detail="پاسخ‌های سریع باید یک لیست باشند.")
        cleaned = []
        for item in items:
            if not isinstance(item, str):
                continue
            item = " ".join(item.split())
            if item:
                cleaned.append(item[:MAX_QUICK_REPLY_CHARS])
        result["quick_replies"] = cleaned[:MAX_QUICK_REPLIES]
    return result


def _in_savepoint(db: Session):
    # روی SQLite (فقط توسعه‌ی محلی) savepoint با درایور pysqlite ناپایدار است؛ آنجا لازم هم نیست
    return db.begin_nested() if config.IS_POSTGRES else None


def _read(db: Session, user_id: int) -> Tuple[Dict[str, Any], bool]:
    query = text("SELECT widget_extras FROM user_settings WHERE user_id = :uid")
    for attempt in (1, 2):
        savepoint = _in_savepoint(db)
        try:
            raw = db.execute(query, {"uid": user_id}).scalar()
            if savepoint is not None:
                savepoint.commit()
            if not raw:
                return dict(DEFAULTS, quick_replies=[]), True
            try:
                stored = json.loads(raw)
            except ValueError:
                return dict(DEFAULTS, quick_replies=[]), True
            try:
                return sanitize(stored), True
            except HTTPException:
                return dict(DEFAULTS, quick_replies=[]), True
        except Exception as exc:  # noqa: BLE001
            if savepoint is not None:
                savepoint.rollback()
            else:
                db.rollback()
            logger.info("widget_extras read failed (attempt %s): %s", attempt, exc)
            if attempt == 1 and _ensure_column(db.get_bind()):
                continue
            return dict(DEFAULTS, quick_replies=[]), False
    return dict(DEFAULTS, quick_replies=[]), False


def load(db: Session, user_id: int) -> Tuple[Dict[str, Any], bool]:
    """(extras, available) برمی‌گرداند. هرگز خطا نمی‌دهد؛ available=False یعنی ستون هنوز ساخته نشده."""
    return _read(db, user_id)


def save(db: Session, user_id: int, incoming: Dict[str, Any]) -> Dict[str, Any]:
    current, _available = _read(db, user_id)
    merged = sanitize(incoming, base=current)
    if not _ensure_column(db.get_bind()):
        raise HTTPException(status_code=503, detail=MIGRATION_HINT)
    try:
        db.execute(
            text("UPDATE user_settings SET widget_extras = :v WHERE user_id = :uid"),
            {"v": json.dumps(merged, ensure_ascii=False), "uid": user_id},
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("widget_extras save failed: %s", exc)
        raise HTTPException(status_code=503, detail=MIGRATION_HINT) from exc
    return merged
