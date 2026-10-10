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
load_dotenv(BASE_DIR / ".env.local", override=False)


# ============================================================
# APP
# ============================================================

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).strip().lower()

IS_VERCEL = bool(os.getenv("VERCEL"))

APP_TITLE = "Prismo — RAG Widget Platform"

# Authentication supports either direct Google OIDC or Google through Supabase Auth.
# The Supabase anon/publishable key is designed for public client use, but the
# service-role key must never be used here or sent to the browser.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
APP_PUBLIC_URL = os.getenv("APP_PUBLIC_URL", "").strip().rstrip("/")
GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_ANON_KEY = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()
SUPABASE_AUTH_ENABLED = bool(SUPABASE_URL and SUPABASE_ANON_KEY)
ACCESS_TOKEN_COOKIE_NAME = "prismo_access_token"
GOOGLE_OAUTH_COOKIE_PREFIX = "prismo_google_oauth_"

# Logging is intentionally quiet by default in local development.
# This prevents high-frequency request logs from consuming CPU/disk while the UI boots.
LOG_LEVEL = os.getenv("PRISMO_LOG_LEVEL", os.getenv("QUASAR_LOG_LEVEL", "WARNING")).strip().upper()
REQUEST_LOGGING = os.getenv("PRISMO_REQUEST_LOGGING", os.getenv("QUASAR_REQUEST_LOGGING", "0")).strip().lower() in {"1", "true", "yes", "on"}
SLOW_REQUEST_MS = int(os.getenv("PRISMO_SLOW_REQUEST_MS", os.getenv("QUASAR_SLOW_REQUEST_MS", "800")))

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# SECURITY / JWT
# ============================================================

CONFIGURED_SECRET_KEY = os.getenv(
    "SECRET_KEY",
)

SECRET_KEY = (
    CONFIGURED_SECRET_KEY
    or "prismo-local-development-secret-key-2026"
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "43200" if APP_ENV == "development" else "1440",
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


DATABASE_MODE = os.getenv("DATABASE_MODE", "auto").strip().lower()
if DATABASE_MODE not in {"auto", "supabase", "local"}:
    raise RuntimeError("DATABASE_MODE must be one of: auto, supabase, local")

RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


use_supabase = DATABASE_MODE == "supabase" or (DATABASE_MODE == "auto" and bool(RAW_DATABASE_URL))

if use_supabase and RAW_DATABASE_URL:

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

elif DATABASE_MODE == "supabase" and not RAW_DATABASE_URL:
    if APP_ENV == "production" or IS_VERCEL:
        raise RuntimeError("DATABASE_URL is required for DATABASE_MODE=supabase.")
    raise RuntimeError("DATABASE_URL is required when DATABASE_MODE=supabase.")

else:
    DATABASE_URL = "sqlite:///" + str(DATA_DIR / "app.db")


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

# ============================================================
# کشف مدل (Discover models) برای Providerهای سفارشی
# ============================================================
# Gatewayهای بزرگ مثل OpenRouter می‌توانند صدها مدل برگردانند. این سقف‌ها
# فقط روی مدل‌هایی اعمال می‌شوند که صرفاً حدسی (بر اساس نام) شناسایی شده‌اند؛
# مدل‌هایی که خودِ provider نوع‌شان را اعلام کرده (architecture متادیتا) یا در
# کاتالوگ اختصاصی embedding آمده‌اند، همیشه probe می‌شوند و هرگز به‌خاطر این
# سقف حذف نمی‌شوند. probe همیشه با یک درخواست واقعی chat/embedding انجام
# می‌شود، نه فقط حدس بر اساس نام مدل.
MODEL_DISCOVERY_CONCURRENCY = max(1, int(os.getenv("MODEL_DISCOVERY_CONCURRENCY", "16")))
MAX_CHAT_MODEL_PROBES = max(1, int(os.getenv("MAX_CHAT_MODEL_PROBES", "120")))
MAX_EMBEDDING_MODEL_PROBES = max(1, int(os.getenv("MAX_EMBEDDING_MODEL_PROBES", "80")))

# probeهای کشف مدل از timeout کوتاه‌تری نسبت به چت/embedding واقعی استفاده
# می‌کنند تا یک مدل کند یا معلق، کل فرآیند کشف را کند نکند.
MODEL_PROBE_TIMEOUT_SECONDS = float(os.getenv("MODEL_PROBE_TIMEOUT_SECONDS", "15"))
MODEL_PROBE_CONNECT_TIMEOUT_SECONDS = float(os.getenv("MODEL_PROBE_CONNECT_TIMEOUT_SECONDS", "8"))

# برای ایندکس سریع اسناد، embeddingها به batchهای بزرگ‌تر و چند درخواست
# هم‌زمان تقسیم می‌شوند. این مقادیر از env قابل تنظیم‌اند تا با محدودیت
# provider یا Relay مقصد هماهنگ شوند.
EMBEDDING_BATCH_SIZE = max(1, int(os.getenv("EMBEDDING_BATCH_SIZE", "40")))
EMBEDDING_CONCURRENCY = max(1, int(os.getenv("EMBEDDING_CONCURRENCY", "4")))

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

DEFAULT_SYSTEM_PROMPT_EN = (
    "You are a helpful and polite AI assistant. Answer only from the knowledge base "
    "provided to the user. If the answer is not in the knowledge base, say that you "
    "do not have enough information and do not guess. Keep answers concise, accurate, "
    "and natural in English."
)

DEFAULT_WIDGET_TITLE = "دستیار هوشمند"
DEFAULT_WIDGET_TITLE_EN = "Smart Assistant"
DEFAULT_WIDGET_WELCOME = "سلام! چطور می‌تونم کمکتون کنم؟"
DEFAULT_WIDGET_WELCOME_EN = "Hello! How can I help you?"

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