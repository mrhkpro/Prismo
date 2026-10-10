from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

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
        api_key_set=bool(settings.api_key),
        base_url=settings.base_url,
        separate_embedding_provider=bool(settings.separate_embedding_provider),
        embedding_api_key_set=bool(settings.embedding_api_key) if settings.separate_embedding_provider else bool(settings.api_key),
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
    result = llm_client.discover_model_capabilities(base_url, api_key, **discover_kwargs)
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
    fallback_base = settings.embedding_base_url if settings.separate_embedding_provider else settings.base_url
    fallback_key = settings.embedding_api_key if settings.separate_embedding_provider else settings.api_key
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
    provider = llm_client.ProviderConfig(
        base_url=payload.base_url.strip(),
        api_key=api_key,
        chat_model=payload.chat_model.strip(),
        embedding_model=settings.embedding_model,
        is_default=False,
        embedding_base_url=settings.embedding_base_url if settings.separate_embedding_provider else payload.base_url.strip(),
        embedding_api_key=settings.embedding_api_key if settings.separate_embedding_provider else api_key,
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
