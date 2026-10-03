"""
تنظیمات مرکزی پروژه.
مقادیر حساس از Environment Variables خوانده می‌شوند.

Local:
    SQLite

Production / Vercel:
    PostgreSQL / Supabase
"""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# APP
# ============================================================

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).strip().lower()

IS_VERCEL = bool(os.getenv("VERCEL"))

APP_TITLE = "پلتفرم ویجت هوشمند RAG"

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# SECURITY / JWT
# ============================================================

CONFIGURED_SECRET_KEY = os.getenv(
    "SECRET_KEY",
)

SECRET_KEY = (
    CONFIGURED_SECRET_KEY
    or secrets.token_urlsafe(32)
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "1440",
    )
)

IMPERSONATION_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "IMPERSONATION_TOKEN_EXPIRE_MINUTES",
        "30",
    )
)


# ============================================================
# DATABASE
# ============================================================

if IS_VERCEL:
    DATA_DIR = Path("/tmp/data")
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


if RAW_DATABASE_URL:

    if RAW_DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = RAW_DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    elif RAW_DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = RAW_DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    else:
        DATABASE_URL = RAW_DATABASE_URL

else:

    if APP_ENV == "production" or IS_VERCEL:
        raise RuntimeError(
            "DATABASE_URL is required on Vercel/production."
        )

    DATABASE_URL = (
        "sqlite:///"
        + str(DATA_DIR / "app.db")
    )


IS_POSTGRES = DATABASE_URL.startswith(
    "postgresql+psycopg://"
)


if APP_ENV == "production" and not IS_POSTGRES:
    raise RuntimeError(
        "Production DATABASE_URL must be PostgreSQL/Supabase."
    )


# ============================================================
# EMBEDDING
# ============================================================

EMBEDDING_DIMENSIONS = int(
    os.getenv(
        "EMBEDDING_DIMENSIONS",
        "2560",
    )
)


# ============================================================
# DEFAULT AI PROVIDER
# ============================================================

DEFAULT_PROVIDER_NAME = (
    "مدل‌های رایگان آماده (RaCode)"
)

DEFAULT_PROVIDER_BASE_URL = os.getenv(
    "DEFAULT_PROVIDER_BASE_URL",
    "https://racode-llm.partschool.ir/v1",
)

DEFAULT_PROVIDER_API_KEY = os.getenv(
    "DEFAULT_PROVIDER_API_KEY",
    "",
).strip()

# در صورت فعال‌سازی Relay، درخواست‌های provider پیش‌فرض به Relay فرستاده می‌شوند
# تا Vercel لازم نباشد مستقیماً به شبکه/فایروال سرویس AI متصل شود.
AI_PROXY_BASE_URL = os.getenv("AI_PROXY_BASE_URL", "").strip().rstrip("/")
AI_PROXY_API_KEY = os.getenv("AI_PROXY_API_KEY", "").strip()

# شبکه‌ی سرویس مدل ممکن است روی Vercel کندتر از اجرای محلی باشد.
# در محیط Serverless، timeout کوتاه‌تر و بدون retry تودرتو از طولانی‌شدن
# درخواست‌های زنجیره‌ای (embedding + chat) جلوگیری می‌کند.
AI_REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("AI_REQUEST_TIMEOUT_SECONDS", "120")
)

AI_CONNECT_TIMEOUT_SECONDS = float(
    os.getenv("AI_CONNECT_TIMEOUT_SECONDS", "20")
)

AI_MAX_RETRIES = int(
    os.getenv("AI_MAX_RETRIES", "0")
)

AI_MAX_OUTPUT_TOKENS = int(
    os.getenv("AI_MAX_OUTPUT_TOKENS", "900")
)

DEFAULT_CHAT_MODELS = [
    "qwen-35b-a3b-instruct",
    "qwen-35b-a3b-reasoning",
    "deepseek-v4-flash-instruct",
    "deepseek-v4-flash-reasoning",
]

DEFAULT_EMBEDDING_MODELS = [
    "qwen3-embedding-4b",
]

DEFAULT_CHAT_MODEL = DEFAULT_CHAT_MODELS[0]

DEFAULT_EMBEDDING_MODEL = (
    DEFAULT_EMBEDDING_MODELS[0]
)


# ============================================================
# RAG DEFAULTS
# ============================================================

DEFAULT_SYSTEM_PROMPT = (
    "تو یک دستیار هوشمند و مؤدب هستی که فقط بر اساس «دانشنامه» "
    "ارائه‌شده به کاربر پاسخ می‌دهی. اگر پاسخ سؤال در دانشنامه نبود، "
    "صادقانه بگو که اطلاعاتی در این مورد نداری و حدس نزن. "
    "پاسخ‌ها را کوتاه، دقیق و به زبان فارسی روان بنویس."
)

DEFAULT_TEMPERATURE = 0.7

DEFAULT_TOP_K = 4

DEFAULT_SIMILARITY_THRESHOLD = float(
    os.getenv(
        "DEFAULT_SIMILARITY_THRESHOLD",
        "0.25",
    )
)

CHUNK_SIZE = 700

CHUNK_OVERLAP = 80

MAX_CHAT_MESSAGE_CHARS = int(
    os.getenv(
        "MAX_CHAT_MESSAGE_CHARS",
        "4000",
    )
)

MAX_VISITOR_LABEL_CHARS = int(
    os.getenv(
        "MAX_VISITOR_LABEL_CHARS",
        "64",
    )
)

PUBLIC_WIDGET_RATE_LIMIT = int(
    os.getenv(
        "PUBLIC_WIDGET_RATE_LIMIT",
        "20",
    )
)

PUBLIC_WIDGET_RATE_WINDOW_SECONDS = int(
    os.getenv(
        "PUBLIC_WIDGET_RATE_WINDOW_SECONDS",
        "60",
    )
)


# ============================================================
# ADMIN
# ============================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin",
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "Admin@12345",
)

ADMIN_ORG_NAME = os.getenv(
    "ADMIN_ORG_NAME",
    "مدیر سیستم",
)


# ============================================================
# SECURITY VALIDATION
# ============================================================

def validate_runtime_security(
    app_env: str,
    configured_secret_key: str,
) -> None:

    if (
        app_env == "production"
        and len(configured_secret_key) < 32
    ):
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters in production."
        )


validate_runtime_security(
    APP_ENV,
    CONFIGURED_SECRET_KEY or "",
)