"""Compatibility layer for UserSettings across old/new Supabase schemas.

The original Supabase schema contains all core settings, while recent releases
added optional embedding-provider columns. This module deliberately uses narrow
SELECT/UPDATE statements so an older Supabase database can keep serving the app
without an ALTER TABLE or a blocking startup migration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from .. import config, models

OPTIONAL_COLUMNS = {
    "separate_embedding_provider",
    "embedding_api_key",
    "embedding_base_url",
}

LEGACY_FIELDS = (
    "use_default_provider",
    "api_key",
    "base_url",
    "chat_model",
    "embedding_model",
    "system_prompt",
    "temperature",
    "top_k",
    "similarity_threshold",
    "widget_id",
    "widget_title",
    "widget_welcome_message",
    "widget_color",
)

_schema_optional_cache: set[str] | None = None


@dataclass(slots=True)
class SettingsSnapshot:
    user_id: int
    use_default_provider: bool = True
    api_key: str | None = None
    base_url: str | None = None
    separate_embedding_provider: bool = False
    embedding_api_key: str | None = None
    embedding_base_url: str | None = None
    chat_model: str = config.DEFAULT_CHAT_MODEL
    embedding_model: str = config.DEFAULT_EMBEDDING_MODEL
    system_prompt: str = config.DEFAULT_SYSTEM_PROMPT
    temperature: float = config.DEFAULT_TEMPERATURE
    top_k: int = config.DEFAULT_TOP_K
    similarity_threshold: float = config.DEFAULT_SIMILARITY_THRESHOLD
    widget_id: str = ""
    widget_title: str = config.DEFAULT_WIDGET_TITLE
    widget_welcome_message: str = config.DEFAULT_WIDGET_WELCOME
    widget_color: str = "#7C5CFF"



def _default_row_values(user_id: int, widget_title: str | None = None) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "use_default_provider": True,
        "chat_model": config.DEFAULT_CHAT_MODEL,
        "embedding_model": config.DEFAULT_EMBEDDING_MODEL,
        "system_prompt": config.DEFAULT_SYSTEM_PROMPT,
        "temperature": config.DEFAULT_TEMPERATURE,
        "top_k": config.DEFAULT_TOP_K,
        "similarity_threshold": config.DEFAULT_SIMILARITY_THRESHOLD,
        "widget_id": models.gen_uuid(),
        "widget_title": widget_title or config.DEFAULT_WIDGET_TITLE,
        "widget_welcome_message": config.DEFAULT_WIDGET_WELCOME,
        "widget_color": "#7C5CFF",
    }


def optional_columns(db: Session) -> set[str]:
    """Return optional provider columns that actually exist in the database.

    Cached per process. Crucially, this is not executed during application
    startup; the first authenticated settings/provider call pays this tiny probe.
    """
    global _schema_optional_cache
    if not config.IS_POSTGRES:
        # Use the session connection for SQLite. SQLAlchemy Inspector can open
        # a second connection on StaticPool and interfere with an in-flight
        # transaction in tests/local development. PRAGMA keeps the probe on the
        # same transaction and costs virtually nothing for SQLite.
        try:
            rows = db.execute(text("PRAGMA table_info(user_settings)")).mappings().all()
            actual = {row["name"] for row in rows}
            return actual & OPTIONAL_COLUMNS
        except Exception:
            return set()
    if _schema_optional_cache is not None:
        return set(_schema_optional_cache)

    try:
        rows = db.execute(
            text(
                "SELECT column_name "
                "FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'user_settings' "
                "AND column_name IN ('separate_embedding_provider','embedding_api_key','embedding_base_url')"
            )
        ).scalars().all()
        _schema_optional_cache = set(rows)
    except Exception:
        # An unreachable/oddly-provisioned database should still allow the
        # legacy core settings path to operate where possible.
        _schema_optional_cache = set()
    return set(_schema_optional_cache)


def invalidate_optional_cache() -> None:
    global _schema_optional_cache
    _schema_optional_cache = None


def _row(db: Session, user_id: int):
    table = models.UserSettings.__table__
    cols = [getattr(table.c, name) for name in LEGACY_FIELDS if hasattr(table.c, name)]
    optional = optional_columns(db)
    cols += [getattr(table.c, name) for name in sorted(optional) if hasattr(table.c, name)]
    return db.execute(select(*cols).where(table.c.user_id == user_id)).mappings().first()


def ensure_settings(db: Session, user_id: int, widget_title: str | None = None) -> SettingsSnapshot:
    """Ensure a legacy-compatible row exists without selecting optional columns."""
    existing = _row(db, user_id)
    if existing:
        return snapshot_from_mapping(user_id, existing)

    table = models.UserSettings.__table__
    values = _default_row_values(user_id, widget_title)
    # Core/ORM INSERT applies Python-side Column defaults even when a field is
    # omitted. That would reintroduce newly-added optional columns on legacy
    # Supabase schemas. Use a narrow SQL INSERT containing only known legacy
    # columns instead. Column names are fixed constants from LEGACY_FIELDS.
    optional = optional_columns(db)
    insert_values = {name: values[name] for name in LEGACY_FIELDS if name in values}
    for name in optional:
        if name == "separate_embedding_provider":
            insert_values[name] = False
        else:
            insert_values[name] = None

    columns = ["user_id"] + list(insert_values)
    placeholders = [f":{name}" for name in columns]
    stmt = text(
        f"INSERT INTO user_settings ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    )
    params = {"user_id": user_id, **insert_values}
    db.execute(stmt, params)
    db.flush()
    existing = _row(db, user_id)
    return snapshot_from_mapping(user_id, existing or values)


def snapshot_from_mapping(user_id: int, row: Any) -> SettingsSnapshot:
    if row is None:
        return SettingsSnapshot(user_id=user_id)
    data = dict(row)
    return SettingsSnapshot(
        user_id=user_id,
        use_default_provider=bool(data.get("use_default_provider", True)),
        api_key=data.get("api_key"),
        base_url=data.get("base_url"),
        separate_embedding_provider=bool(data.get("separate_embedding_provider", False)),
        embedding_api_key=data.get("embedding_api_key"),
        embedding_base_url=data.get("embedding_base_url"),
        chat_model=data.get("chat_model") or config.DEFAULT_CHAT_MODEL,
        embedding_model=data.get("embedding_model") or config.DEFAULT_EMBEDDING_MODEL,
        system_prompt=data.get("system_prompt") or config.DEFAULT_SYSTEM_PROMPT,
        temperature=float(data.get("temperature") if data.get("temperature") is not None else config.DEFAULT_TEMPERATURE),
        top_k=int(data.get("top_k") if data.get("top_k") is not None else config.DEFAULT_TOP_K),
        similarity_threshold=float(data.get("similarity_threshold") if data.get("similarity_threshold") is not None else config.DEFAULT_SIMILARITY_THRESHOLD),
        widget_id=data.get("widget_id") or "",
        widget_title=data.get("widget_title") or config.DEFAULT_WIDGET_TITLE,
        widget_welcome_message=data.get("widget_welcome_message") or config.DEFAULT_WIDGET_WELCOME,
        widget_color=data.get("widget_color") or "#7C5CFF",
    )


def get(db: Session, user_id: int) -> SettingsSnapshot:
    row = _row(db, user_id)
    if not row:
        return ensure_settings(db, user_id)
    return snapshot_from_mapping(user_id, row)


def update_settings(db: Session, user_id: int, data: dict[str, Any]) -> SettingsSnapshot:
    table = models.UserSettings.__table__
    if not _row(db, user_id):
        ensure_settings(db, user_id)

    allowed = set(LEGACY_FIELDS) - {"user_id"}
    values = {k: v for k, v in data.items() if k in allowed}

    optional = optional_columns(db)
    for name in OPTIONAL_COLUMNS & optional:
        if name in data:
            values[name] = data[name]

    if data.get("separate_embedding_provider") is False and optional:
        if "embedding_api_key" in optional:
            values["embedding_api_key"] = None
        if "embedding_base_url" in optional:
            values["embedding_base_url"] = None

    if values:
        db.execute(update(table).where(table.c.user_id == user_id).values(**values))
    db.flush()
    return get(db, user_id)
