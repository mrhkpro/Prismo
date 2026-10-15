import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from . import config
from .database import Base
from .timeutils import utcnow


# ============================================================
# HELPERS
# ============================================================

def gen_uuid() -> str:
    return uuid.uuid4().hex


# ============================================================
# ENUMS
# ============================================================

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class ChatSource(str, enum.Enum):
    playground = "playground"
    widget = "widget"


# ============================================================
# EMBEDDING COLUMN TYPE
# ============================================================

if config.IS_POSTGRES:

    from pgvector.sqlalchemy import VECTOR

    EMBEDDING_COLUMN_TYPE = VECTOR(
        config.EMBEDDING_DIMENSIONS
    )

else:

    EMBEDDING_COLUMN_TYPE = JSON()


# ============================================================
# USER
# ============================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    org_name = Column(
        String(120),
        nullable=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        Enum(
            UserRole,
            name="userrole",
        ),
        default=UserRole.user,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    last_login_at = Column(
        DateTime,
        nullable=True,
    )

    settings = relationship(
        "UserSettings",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )

    documents = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    chat_sessions = relationship(
        "ChatSession",
        back_populates="owner",
        cascade="all, delete-orphan",
    )


# ============================================================
# USER SETTINGS
# ============================================================

class UserSettings(Base):

    __tablename__ = "user_settings"

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
        ),
        unique=True,
        nullable=False,
    )

    # Chat and embedding providers can be chosen independently. Nullable is
    # intentional for older hosted schemas before migration 005 is applied.
    use_default_provider = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    embedding_use_default_provider = Column(
        Boolean,
        default=True,
        nullable=True,
    )

    api_key = Column(
        String(255),
        nullable=True,
    )

    base_url = Column(
        String(255),
        nullable=True,
    )

    # اگر True باشد، provider مربوط به embedding می‌تواند Base URL و API Key مستقل داشته باشد.
    separate_embedding_provider = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    embedding_api_key = Column(
        String(255),
        nullable=True,
    )

    embedding_base_url = Column(
        String(255),
        nullable=True,
    )

    chat_model = Column(
        String(120),
        default=config.DEFAULT_CHAT_MODEL,
    )

    embedding_model = Column(
        String(120),
        default=config.DEFAULT_EMBEDDING_MODEL,
    )

    system_prompt = Column(
        Text,
        default=config.DEFAULT_SYSTEM_PROMPT,
    )

    temperature = Column(
        Float,
        default=config.DEFAULT_TEMPERATURE,
    )

    top_k = Column(
        Integer,
        default=config.DEFAULT_TOP_K,
    )

    similarity_threshold = Column(
        Float,
        default=config.DEFAULT_SIMILARITY_THRESHOLD,
    )

    widget_id = Column(
        String(64),
        unique=True,
        index=True,
        default=gen_uuid,
    )

    widget_title = Column(
        String(120),
        default=config.DEFAULT_WIDGET_TITLE,
    )

    widget_welcome_message = Column(
        Text,
        default=config.DEFAULT_WIDGET_WELCOME,
    )

    widget_color = Column(
        String(16),
        default="#7C5CFF",
    )

    user = relationship(
        "User",
        back_populates="settings",
    )


# ============================================================
# SAVED CHAT MODELS (per-user provider profiles)
# ============================================================

class SavedChatModel(Base):
    __tablename__ = "saved_chat_models"
    __table_args__ = (UniqueConstraint("user_id", "model_id", name="uq_saved_chat_model_user_model"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(200), nullable=False)
    base_url = Column(String(500), nullable=False)
    api_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


# ============================================================
# DOCUMENT
# ============================================================

class Document(Base):

    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
        ),
        nullable=False,
        index=True,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    updated_at = Column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
    )

    owner = relationship(
        "User",
        back_populates="documents",
    )

    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


# ============================================================
# CHUNK
# ============================================================

class Chunk(Base):

    __tablename__ = "chunks"

    id = Column(
        Integer,
        primary_key=True,
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
        ),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
        ),
        nullable=False,
        index=True,
    )

    chunk_index = Column(
        Integer,
        nullable=False,
    )

    text = Column(
        Text,
        nullable=False,
    )

    embedding = Column(
        EMBEDDING_COLUMN_TYPE,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    document = relationship(
        "Document",
        back_populates="chunks",
    )


# ============================================================
# CHAT SESSION
# ============================================================

class ChatSession(Base):

    __tablename__ = "chat_sessions"

    id = Column(
        String(64),
        primary_key=True,
        default=gen_uuid,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
        ),
        nullable=False,
        index=True,
    )

    source = Column(
        Enum(
            ChatSource,
            name="chatsource",
        ),
        nullable=False,
    )

    visitor_label = Column(
        String(64),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    owner = relationship(
        "User",
        back_populates="chat_sessions",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


# ============================================================
# CHAT MESSAGE
# ============================================================

class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
    )

    session_id = Column(
        String(64),
        ForeignKey(
            "chat_sessions.id",
        ),
        nullable=False,
        index=True,
    )

    role = Column(
        String(16),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    is_flagged = Column(
        Boolean,
        default=False,
    )

    flag_reason = Column(
        String(255),
        nullable=True,
    )

    resolved = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )

# ============================================================
# RAG ANSWER CACHE
# ============================================================

class AnswerCache(Base):
    """Per-user cache for exact repeat questions under the same model/settings/docs."""

    __tablename__ = "answer_cache"
    __table_args__ = (UniqueConstraint("user_id", "cache_key", name="uq_answer_cache_user_key"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cache_key = Column(String(64), nullable=False, index=True)
    answer = Column(Text, nullable=False)
    source_chunks = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utcnow, nullable=False)

# ============================================================
# SAVED EMBEDDING MODELS (per-user provider profiles)
# ============================================================

class SavedEmbeddingModel(Base):
    __tablename__ = "saved_embedding_models"
    __table_args__ = (UniqueConstraint("user_id", "model_id", "base_url", name="uq_saved_embedding_model_profile"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(200), nullable=False)
    base_url = Column(String(500), nullable=False)
    api_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
