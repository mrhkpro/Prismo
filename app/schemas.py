from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, field_validator

from . import config


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    org_name: Optional[str] = Field(default=None, max_length=120)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("نام کاربری نمی‌تواند خالی باشد.")
        return value

    @field_validator("org_name")
    @classmethod
    def normalize_org_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    org_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    impersonated_by: Optional[int] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# تنظیمات (اتصال مدل + RAG/پرامپت + ویجت)
# ---------------------------------------------------------------------------
class SettingsOut(BaseModel):
    use_default_provider: bool
    api_key_set: bool
    base_url: Optional[str] = None
    chat_model: str
    embedding_model: str
    system_prompt: str
    temperature: float
    top_k: int
    similarity_threshold: float
    widget_id: str
    widget_title: str
    widget_welcome_message: str
    widget_color: str
    default_chat_models: List[str]
    default_embedding_models: List[str]


class SettingsUpdate(BaseModel):
    use_default_provider: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    top_k: Optional[int] = Field(default=None, ge=1, le=15)
    similarity_threshold: Optional[float] = Field(default=None, ge=0, le=1)


class TestConnectionResult(BaseModel):
    ok: bool
    message: str


class ProviderDiagnosticsResponse(BaseModel):
    ok: bool
    base_url: str
    model: str
    dns: List[str]
    stage: str
    status_code: Optional[int] = None
    error_type: Optional[str] = None
    message: str
    elapsed_ms: int


class DashboardSummaryOut(BaseModel):
    document_count: int
    chunk_count: int
    playground_session_count: int
    widget_session_count: int
    message_count: int
    provider_label: str
    widget_online: bool


class DiscoverModelsRequest(BaseModel):
    base_url: str = Field(min_length=1, max_length=500)
    api_key: Optional[str] = Field(default=None, max_length=500)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("Base URL باید با http:// یا https:// شروع شود.")
        return value


class DiscoverModelsResponse(BaseModel):
    models: List[str]


class CustomConnectionTestRequest(BaseModel):
    base_url: str = Field(min_length=1, max_length=500)
    chat_model: str = Field(min_length=1, max_length=200)
    api_key: Optional[str] = Field(default=None, max_length=500)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("Base URL باید با http:// یا https:// شروع شود.")
        return value

    @field_validator("chat_model")
    @classmethod
    def normalize_chat_model(cls, value: str) -> str:
        return value.strip()


# ---------------------------------------------------------------------------
# دانشنامه (Knowledge Base)
# ---------------------------------------------------------------------------
class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class DocumentOut(BaseModel):
    id: int
    title: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    content: str


# ---------------------------------------------------------------------------
# آزمایشگاه تست
# ---------------------------------------------------------------------------
class ChatTestRequest(BaseModel):
    message: str = Field(min_length=1, max_length=config.MAX_CHAT_MESSAGE_CHARS)
    session_id: Optional[str] = Field(default=None, max_length=64)
    model: Optional[str] = Field(default=None, min_length=1, max_length=200)

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class SourceChunk(BaseModel):
    document_title: str
    text: str
    score: float


class ChatTestResponse(BaseModel):
    session_id: str
    reply: str
    sources: List[SourceChunk]
    model: str


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SemanticSearchResult(BaseModel):
    document_title: str
    document_id: int
    text: str
    score: float


class BattleRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    prompt: str = Field(min_length=1, max_length=config.MAX_CHAT_MESSAGE_CHARS)
    model_a: str = Field(min_length=1, max_length=200)
    model_b: str = Field(min_length=1, max_length=200)


class BattleSide(BaseModel):
    model: str
    reply: str
    elapsed_ms: int
    error: Optional[str] = None


class BattleResponse(BaseModel):
    side_a: BattleSide
    side_b: BattleSide


# ---------------------------------------------------------------------------
# ویجت
# ---------------------------------------------------------------------------
class WidgetConfigUpdate(BaseModel):
    widget_title: Optional[str] = Field(default=None, max_length=120)
    widget_welcome_message: Optional[str] = Field(default=None, max_length=1000)
    widget_color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    extras: Optional[dict] = None


class WidgetPublicConfig(BaseModel):
    widget_id: str
    title: str
    welcome_message: str
    color: str
    org_name: Optional[str] = None
    online: bool
    extras: dict = Field(default_factory=dict)


class WidgetChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=config.MAX_CHAT_MESSAGE_CHARS)
    session_id: Optional[str] = Field(default=None, max_length=64)
    visitor_label: Optional[str] = Field(default=None, max_length=config.MAX_VISITOR_LABEL_CHARS)


class WidgetChatResponse(BaseModel):
    session_id: str
    reply: str


# ---------------------------------------------------------------------------
# ادمین
# ---------------------------------------------------------------------------
class AdminUserOut(BaseModel):
    id: int
    username: str
    org_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    document_count: int
    session_count: int

    model_config = {"from_attributes": True}


class AdminUserDetailOut(AdminUserOut):
    use_default_provider: bool
    api_key_set: bool
    base_url: Optional[str] = None
    chat_model: str
    embedding_model: str
    system_prompt: str
    temperature: float
    top_k: int
    similarity_threshold: float
    widget_id: str


class RoleUpdateRequest(BaseModel):
    role: Literal["user", "admin"]


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    blocked_users: int
    admin_users: int
    total_documents: int
    total_chunks: int
    total_sessions: int
    total_messages: int
    widget_sessions: int
    playground_sessions: int
    flagged_messages: int
    unresolved_flags: int


class SessionOut(BaseModel):
    id: str
    source: str
    visitor_label: Optional[str] = None
    created_at: datetime
    message_count: int
    has_flag: bool

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    is_flagged: bool
    flag_reason: Optional[str] = None
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FlaggedMessageOut(BaseModel):
    id: int
    session_id: str
    owner_username: str
    role: str
    content: str
    flag_reason: Optional[str] = None
    resolved: bool
    created_at: datetime
    # فیلدهای تکمیلیِ نظارت امنیتی (از روی کدهای flag_reason و نشست محاسبه می‌شوند؛ ستون جدیدی لازم نیست)
    owner_id: Optional[int] = None
    owner_org_name: Optional[str] = None
    owner_is_active: Optional[bool] = None
    source: Optional[str] = None
    visitor_label: Optional[str] = None
    severity: str = "high"
    category: str = "instruction_override"
    label: str = ""
    codes: list[str] = []

    model_config = {"from_attributes": True}


class SecurityAlertOut(BaseModel):
    id: int
    owner_username: str
    severity: str
    label: str
    source: Optional[str] = None
    created_at: datetime


class SecuritySummaryOut(BaseModel):
    unresolved_total: int
    critical: int
    high: int
    medium: int
    prompt_extraction: int
    latest: Optional[SecurityAlertOut] = None


class ImpersonateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    target_username: str
