from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .. import models, schemas, config, i18n
from ..database import get_db
from ..security import get_current_user
from ..services import llm_client, user_settings_compat

router = APIRouter(prefix="/api/settings", tags=["تنظیمات"])


def _settings_for_user(db, current_user):
    # Unit-level callers in the legacy test suite pass only a FakeUser; retain
    # that lightweight contract while real requests use the compatibility layer.
    if hasattr(db, "execute"):
        return user_settings_compat.get(db, current_user.id)
    legacy = getattr(current_user, "settings", None)
    if legacy is not None:
        return legacy
    return user_settings_compat.get(db, current_user.id)


def _to_out(settings: user_settings_compat.SettingsSnapshot, language: str = "fa") -> schemas.SettingsOut:
    return schemas.SettingsOut(
        use_default_provider=settings.use_default_provider,
        embedding_use_default_provider=(
            settings.embedding_use_default_provider
            if settings.embedding_use_default_provider is not None
            else settings.use_default_provider
        ),
        api_key_set=bool(settings.api_key),
        base_url=settings.base_url,
        separate_embedding_provider=bool(settings.separate_embedding_provider),
        embedding_api_key_set=(
            bool(settings.embedding_api_key)
            if settings.separate_embedding_provider
            else (bool(settings.api_key) if not settings.use_default_provider else False)
        ),
        embedding_base_url=settings.embedding_base_url if settings.separate_embedding_provider else settings.base_url,
        chat_model=settings.chat_model,
        embedding_model=settings.embedding_model,
        system_prompt=i18n.localize_default_system_prompt(settings.system_prompt, language),
        temperature=settings.temperature,
        top_k=settings.top_k,
        similarity_threshold=settings.similarity_threshold,
        widget_id=settings.widget_id,
        widget_title=i18n.localize_widget_title(settings.widget_title, language),
        widget_welcome_message=i18n.localize_widget_welcome(settings.widget_welcome_message, language),
        widget_color=settings.widget_color,
        default_chat_models=config.DEFAULT_CHAT_MODELS,
        default_embedding_models=config.DEFAULT_EMBEDDING_MODELS,
        embedding_dimensions=config.EMBEDDING_DIMENSIONS,
    )


@router.get("", response_model=schemas.SettingsOut)
def get_settings(request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _to_out(user_settings_compat.get(db, current_user.id), i18n.get_language(request))


@router.put("", response_model=schemas.SettingsOut)
def update_settings(
    payload: schemas.SettingsUpdate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    for key in ("base_url", "api_key", "embedding_api_key", "embedding_base_url"):
        if key in data:
            data[key] = data[key] or None
    settings = user_settings_compat.update_settings(db, current_user.id, data)
    db.commit()
    return _to_out(settings, i18n.get_language(request))


def _saved_chat_models_migration_error(exc: SQLAlchemyError) -> bool:
    """Identify the common deployment case where the Supabase migration was not run."""
    message = str(getattr(exc, "orig", exc)).lower()
    return any(
        marker in message
        for marker in (
            'relation "saved_chat_models" does not exist',
            "relation 'saved_chat_models' does not exist",
            "no such table: saved_chat_models",
            "undefined table: saved_chat_models",
        )
    )


def _saved_chat_models_schema_http_error() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=(
            "جدول saved_chat_models در دیتابیس وجود ندارد یا ساختار آن کامل نیست. "
            "فایل supabase/migrations/013_repair_saved_model_registries.sql را یک‌بار در SQL Editor سوپابیس اجرا کن."
        ),
    )


def _saved_embedding_models_migration_error(exc: SQLAlchemyError) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return any(marker in message for marker in (
        'relation "saved_embedding_models" does not exist',
        "relation 'saved_embedding_models' does not exist",
        "no such table: saved_embedding_models",
        "undefined table: saved_embedding_models",
    ))


def _saved_embedding_models_schema_http_error() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=(
            "جدول saved_embedding_models در دیتابیس وجود ندارد یا ساختار آن کامل نیست. "
            "فایل supabase/migrations/013_repair_saved_model_registries.sql را یک‌بار در SQL Editor سوپابیس اجرا کن."
        ),
    )


@router.get("/saved-chat-models", response_model=list[schemas.SavedChatModelOut])
def list_saved_chat_models(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(models.SavedChatModel)
            .filter(models.SavedChatModel.user_id == current_user.id)
            .order_by(models.SavedChatModel.model_id.asc())
            .all()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        if _saved_chat_models_migration_error(exc):
            raise _saved_chat_models_schema_http_error() from exc
        raise
    return [{"model_id": row.model_id, "base_url": row.base_url} for row in rows]


@router.post("/saved-chat-models", response_model=schemas.SavedChatModelOut)
def save_chat_model(payload: schemas.SaveChatModelRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = user_settings_compat.get(db, current_user.id)
    key = (payload.api_key or settings.api_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="برای ذخیرهٔ مدل، API Key لازم است.")
    try:
        row = db.query(models.SavedChatModel).filter_by(user_id=current_user.id, model_id=payload.model_id).first()
        if row is None:
            row = models.SavedChatModel(user_id=current_user.id, model_id=payload.model_id, base_url=payload.base_url, api_key=key)
            db.add(row)
        else:
            row.base_url = payload.base_url
            row.api_key = key
        db.commit()
        return {"model_id": row.model_id, "base_url": row.base_url}
    except SQLAlchemyError as exc:
        db.rollback()
        if _saved_chat_models_migration_error(exc):
            raise _saved_chat_models_schema_http_error() from exc
        raise


@router.post("/discover-models", response_model=schemas.DiscoverModelsResponse)
def discover_models(
    payload: schemas.DiscoverModelsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discover model capabilities without mutating the database."""
    settings = _settings_for_user(db, current_user)
    api_key = (payload.api_key or settings.api_key or "").strip()
    base_url = (payload.base_url or settings.base_url or "").strip()
    embedding_api_key = (payload.embedding_api_key or settings.embedding_api_key or "").strip()
    embedding_base_url = (payload.embedding_base_url or settings.embedding_base_url or "").strip()
    discover_kwargs = {}
    # Discovery is a read-only test action. Honor the credentials currently
    # entered in the form even if the user has not saved provider settings yet.
    if payload.separate_embedding_provider:
        discover_kwargs = {
            "embedding_base_url": embedding_base_url or None,
            "embedding_api_key": embedding_api_key or None,
        }
    # Keep the historical call shape for the default full-discovery mode so
    # integrations/mocks implementing the previous signature remain compatible.
    if payload.discover_embeddings:
        result = llm_client.discover_model_capabilities(base_url, api_key, **discover_kwargs)
    else:
        result = llm_client.discover_model_capabilities(
            base_url, api_key, include_embeddings=False, **discover_kwargs
        )
    result.setdefault("chat_probe_ok", bool(result.get("chat_models")))
    result.setdefault("embedding_probe_ok", bool(result.get("embedding_models")))
    result.setdefault(
        "dual_capable_models",
        sorted(set(result.get("chat_models", [])) & set(result.get("embedding_models", [])), key=str.casefold),
    )
    return schemas.DiscoverModelsResponse(**result)


@router.post("/discover-embedding-models", response_model=schemas.DiscoverEmbeddingModelsResponse)
def discover_embedding_models(
    payload: schemas.DiscoverEmbeddingModelsRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discover embedding models for the embedding provider's own key.

    Independent of the chat key/base URL on purpose: the embedding provider
    (e.g. a separate OpenRouter key) can be entirely different from the chat
    provider, and a user should be able to test/populate it on its own.
    """
    settings = _settings_for_user(db, current_user)
    fallback_base = settings.embedding_base_url if settings.separate_embedding_provider and settings.embedding_base_url else settings.base_url
    fallback_key = settings.embedding_api_key or settings.api_key
    base_url = (payload.base_url or fallback_base or "").strip()
    api_key = (payload.api_key or fallback_key or "").strip()
    result = llm_client.discover_embedding_models(base_url, api_key)
    result.setdefault("embedding_probe_ok", bool(result.get("embedding_models")))
    return schemas.DiscoverEmbeddingModelsResponse(**result)


@router.post("/test-custom-connection", response_model=schemas.TestConnectionResult)
def test_custom_connection(
    payload: schemas.CustomConnectionTestRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = user_settings_compat.get(db, current_user.id)
    api_key = (payload.api_key or settings.api_key or "").strip()
    embed_default = payload.embedding_use_default_provider
    if embed_default is None:
        embed_default = settings.embedding_use_default_provider
    if embed_default is None:
        embed_default = settings.use_default_provider

    if embed_default:
        embedding_base = config.AI_PROXY_BASE_URL or config.DEFAULT_PROVIDER_BASE_URL
        embedding_key = config.AI_PROXY_API_KEY or config.DEFAULT_PROVIDER_API_KEY
    elif payload.separate_embedding_provider:
        embedding_base = (payload.embedding_base_url or settings.embedding_base_url or "").strip()
        embedding_key = (payload.embedding_api_key or settings.embedding_api_key or "").strip()
    else:
        embedding_base, embedding_key = payload.base_url.strip(), api_key

    provider = llm_client.ProviderConfig(
        base_url=payload.base_url.strip(),
        api_key=api_key,
        chat_model=payload.chat_model.strip(),
        embedding_model=(payload.embedding_model or settings.embedding_model or config.DEFAULT_EMBEDDING_MODEL).strip(),
        is_default=False,
        embedding_base_url=embedding_base,
        embedding_api_key=embedding_key,
    )
    ok, message = llm_client.test_connection(provider)
    return schemas.TestConnectionResult(ok=ok, message=message)


@router.post("/test-connection", response_model=schemas.TestConnectionResult)
def test_connection(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    provider = llm_client.resolve_provider(user_settings_compat.get(db, current_user.id))
    ok, message = llm_client.test_connection(provider)
    return schemas.TestConnectionResult(ok=ok, message=message)


@router.get("/provider-diagnostics", response_model=schemas.ProviderDiagnosticsResponse)
def provider_diagnostics(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    provider = llm_client.resolve_provider(user_settings_compat.get(db, current_user.id))
    return llm_client.provider_diagnostics(provider)

@router.get("/saved-embedding-models", response_model=list[schemas.SavedEmbeddingModelOut])
def list_saved_embedding_models(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(models.SavedEmbeddingModel)
            .filter(models.SavedEmbeddingModel.user_id == current_user.id)
            .order_by(models.SavedEmbeddingModel.model_id.asc(), models.SavedEmbeddingModel.base_url.asc())
            .all()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        if _saved_embedding_models_migration_error(exc):
            raise _saved_embedding_models_schema_http_error() from exc
        raise
    return [{"model_id": row.model_id, "base_url": row.base_url} for row in rows]


@router.post("/saved-embedding-models", response_model=schemas.SavedEmbeddingModelOut)
def save_embedding_model(
    payload: schemas.SaveEmbeddingModelRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save an explicitly selected custom embedding profile without exposing its API key."""
    settings = user_settings_compat.get(db, current_user.id)
    key = (payload.api_key or settings.embedding_api_key or settings.api_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="برای ذخیرهٔ مدل Embedding، API Key لازم است.")
    base_url = payload.base_url.strip().rstrip("/")
    try:
        row = (
            db.query(models.SavedEmbeddingModel)
            .filter_by(user_id=current_user.id, model_id=payload.model_id, base_url=base_url)
            .first()
        )
        if row is None:
            row = models.SavedEmbeddingModel(
                user_id=current_user.id,
                model_id=payload.model_id,
                base_url=base_url,
                api_key=key,
            )
            db.add(row)
        else:
            row.api_key = key
        db.commit()
        return {"model_id": row.model_id, "base_url": row.base_url}
    except SQLAlchemyError as exc:
        db.rollback()
        if _saved_embedding_models_migration_error(exc):
            raise _saved_embedding_models_schema_http_error() from exc
        raise


@router.post("/saved-embedding-models/current", response_model=schemas.SavedEmbeddingModelOut)
def save_current_embedding_model(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Backward-compatible endpoint for older dashboard clients."""
    settings = user_settings_compat.get(db, current_user.id)
    embedding_uses_default = (
        settings.embedding_use_default_provider
        if settings.embedding_use_default_provider is not None
        else settings.use_default_provider
    )
    if embedding_uses_default:
        raise HTTPException(status_code=400, detail="مدل embedding آماده انتخاب شده است؛ مدل اختصاصی برای ذخیره وجود ندارد.")

    base_url = (settings.embedding_base_url if settings.separate_embedding_provider else settings.base_url) or ""
    api_key = (settings.embedding_api_key or (settings.api_key if not settings.use_default_provider else "")) if settings.separate_embedding_provider else (settings.api_key or "")
    model_id = (settings.embedding_model or "").strip()
    if not base_url.strip() or not api_key.strip() or not model_id:
        raise HTTPException(status_code=400, detail="برای ذخیره مدل embedding، مدل، آدرس API و کلید معتبر لازم است.")
    try:
        row = (
            db.query(models.SavedEmbeddingModel)
            .filter_by(user_id=current_user.id, model_id=model_id, base_url=base_url.strip().rstrip("/"))
            .first()
        )
        if row is None:
            row = models.SavedEmbeddingModel(user_id=current_user.id, model_id=model_id, base_url=base_url.strip().rstrip("/"), api_key=api_key.strip())
            db.add(row)
        else:
            row.api_key = api_key.strip()
        db.commit()
        return {"model_id": row.model_id, "base_url": row.base_url}
    except SQLAlchemyError as exc:
        db.rollback()
        if _saved_embedding_models_migration_error(exc):
            raise _saved_embedding_models_schema_http_error() from exc
        raise
