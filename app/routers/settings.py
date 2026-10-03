from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, config
from ..database import get_db
from ..security import get_current_user
from ..services import llm_client

router = APIRouter(prefix="/api/settings", tags=["تنظیمات"])


def _to_out(settings: models.UserSettings) -> schemas.SettingsOut:
    return schemas.SettingsOut(
        use_default_provider=settings.use_default_provider,
        api_key_set=bool(settings.api_key),
        base_url=settings.base_url,
        chat_model=settings.chat_model,
        embedding_model=settings.embedding_model,
        system_prompt=settings.system_prompt,
        temperature=settings.temperature,
        top_k=settings.top_k,
        similarity_threshold=settings.similarity_threshold,
        widget_id=settings.widget_id,
        widget_title=settings.widget_title,
        widget_welcome_message=settings.widget_welcome_message,
        widget_color=settings.widget_color,
        default_chat_models=config.DEFAULT_CHAT_MODELS,
        default_embedding_models=config.DEFAULT_EMBEDDING_MODELS,
    )


@router.get("", response_model=schemas.SettingsOut)
def get_settings(current_user: models.User = Depends(get_current_user)):
    return _to_out(current_user.settings)


@router.put("", response_model=schemas.SettingsOut)
def update_settings(
    payload: schemas.SettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = current_user.settings
    data = payload.model_dump(exclude_unset=True)

    for field in ("use_default_provider", "chat_model", "embedding_model",
                  "system_prompt", "temperature", "top_k", "similarity_threshold"):
        if field in data and data[field] is not None:
            setattr(settings, field, data[field])

    # base_url / api_key: اجازه‌ی خالی‌کردن عمدی هم می‌دهیم
    if "base_url" in data:
        settings.base_url = data["base_url"] or None
    if "api_key" in data:
        settings.api_key = data["api_key"] or None

    db.commit()
    db.refresh(settings)
    return _to_out(settings)


@router.post("/discover-models", response_model=schemas.DiscoverModelsResponse)
def discover_models(
    payload: schemas.DiscoverModelsRequest,
    current_user: models.User = Depends(get_current_user),
):
    """مدل‌های سرویس اختصاصی را از endpoint /models می‌خواند؛ چیزی در DB ذخیره نمی‌شود."""
    settings = current_user.settings
    api_key = (payload.api_key or settings.api_key or "").strip()
    base_url = (payload.base_url or settings.base_url or "").strip()
    models_list = llm_client.list_models(base_url, api_key)
    return schemas.DiscoverModelsResponse(models=models_list)


@router.post("/test-custom-connection", response_model=schemas.TestConnectionResult)
def test_custom_connection(
    payload: schemas.CustomConnectionTestRequest,
    current_user: models.User = Depends(get_current_user),
):
    """اتصال اختصاصی فعلی فرم را بدون ذخیره‌کردن تنظیمات تست می‌کند."""
    api_key = (payload.api_key or current_user.settings.api_key or "").strip()
    provider = llm_client.ProviderConfig(
        base_url=payload.base_url.strip(),
        api_key=api_key,
        chat_model=payload.chat_model.strip(),
        embedding_model=current_user.settings.embedding_model,
        is_default=False,
    )
    ok, message = llm_client.test_connection(provider)
    return schemas.TestConnectionResult(ok=ok, message=message)


@router.post("/test-connection", response_model=schemas.TestConnectionResult)
def test_connection(current_user: models.User = Depends(get_current_user)):
    provider = llm_client.resolve_provider(current_user.settings)
    ok, message = llm_client.test_connection(provider)
    return schemas.TestConnectionResult(ok=ok, message=message)


@router.get("/provider-diagnostics", response_model=schemas.ProviderDiagnosticsResponse)
def provider_diagnostics(current_user: models.User = Depends(get_current_user)):
    """جزئیات اتصال provider را بدون افشای API Key برای پنل برمی‌گرداند."""
    provider = llm_client.resolve_provider(current_user.settings)
    return llm_client.provider_diagnostics(provider)
