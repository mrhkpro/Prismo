# Prismo — RAG Widget Platform

A multi-tenant, knowledge-powered AI widget platform built with FastAPI, SQLAlchemy, SQLite, an embedded NumPy vector store, and Vanilla HTML/CSS/JS.

Each user can create a private knowledge base, configure an OpenAI-compatible model provider, tune RAG behavior, test conversations, compare two models, and publish a customizable chat widget to another website. An admin area provides RBAC, user management, telemetry, conversation inspection, impersonation, and heuristic prompt-injection monitoring.

## Features

- User registration, login, JWT sessions, logout and account blocking.
- User-scoped documents, chunks, conversations and settings.
- Custom OpenAI-compatible provider configuration, connection testing and model discovery.
- Independent chat and embedding providers with a guided, responsive setup flow (v2.8.0).
- RAG with chunking, embeddings, cosine retrieval, configurable `top_k` and similarity threshold.
- Bounded conversation history and explicit retrieved-context boundaries.
- Knowledge-base CRUD plus explicit document reindexing.
- Chat playground with persistent sessions and owner-scoped session cleanup.
- Two-model Battle mode with independent errors and response timing.
- Embeddable widget using Shadow DOM, configurable title/message/color and cache-busted embed code.
- Public-widget input validation, account-state checks and per-process rate limiting.
- Admin dashboard, pagination, statistics, security flags, role management and safe impersonation.
- Persistent prompt-risk alerts for suspected system-prompt/API-key disclosure and dangerous requests from the Test Lab or public widget; administrators sharing the same database can inspect the message and reason.
- Centralized API errors, request IDs and request timing logs.
- Light/dark frontend theme support, responsive UI, accessible toast notifications and fetch timeouts.

## Latest release

See [`docs/CHANGELOG_2.8.0.md`](docs/CHANGELOG_2.8.0.md) for the AI connection UX refresh. Model selection now comes before a shared save/test action area at the bottom of the form.

## Architecture

```text
Browser / embedded widget
        │
        ▼
FastAPI
 ├─ Auth / RBAC
 ├─ Dashboard / Settings
 ├─ Knowledge / Playground
 ├─ Widget / Public Widget
 └─ Admin
        │
        ├─ SQLAlchemy → SQLite
        └─ RAG services → NumPy cosine search → OpenAI-compatible provider
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the detailed data model, request flow and design decisions.

## RAG flow

```text
message
  → embedding
  → owner-scoped semantic search
  → similarity threshold + top-k
  → bounded conversation history
  → system prompt + retrieved context
  → chat completion
  → persist turn + injection flag
```

See [`docs/RAG.md`](docs/RAG.md).

## Requirements

Python 3.10+ is supported by the setup flow. Runtime dependencies are pinned in `requirements.txt`.

No Docker, separate vector database, or separate frontend server is required for the current project architecture.

## Run locally

### Windows

Run `setup.bat`. It creates `.venv`, installs dependencies, creates a local `.env` from `.env.example` when needed, starts Uvicorn, and opens the application.

Default URL: `http://127.0.0.1:8000/`

Local demo admin account: `admin` / value of `ADMIN_PASSWORD` in the local `.env`.

### Linux / macOS

```bash
chmod +x run.sh
./run.sh
```

The launcher also supports `HOST`, `PORT` and `OPEN_BROWSER` environment variables.

## Environment

Copy `.env.example` to `.env` and configure provider credentials before using AI calls. `.env` is intentionally ignored by Git.

Production requires an explicitly configured `SECRET_KEY` with at least 32 characters. Do not commit API keys, JWT secrets, passwords, `.env` files, or runtime database files.

See [`docs/SECURITY.md`](docs/SECURITY.md) and [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## API

The interactive Swagger UI is available at `/docs` after startup.

The documented API includes:

- `/api/auth` — registration, login and current user.
- `/api/dashboard` — user-scoped summary.
- `/api/settings` — provider, model, RAG, prompt and widget settings.
- `/api/knowledge` — document CRUD and reindex.
- `/api/playground` — chat, semantic search, sessions and Battle.
- `/api/widget` — widget configuration and embed code.
- `/public/widget` — public widget config/chat without a user token.
- `/api/admin` — admin-only management, monitoring and RBAC operations.
- `/api/health` — lightweight health check.

See [`docs/API.md`](docs/API.md) for the full endpoint reference.

## Testing

Run from the repository root:

```bash
pytest -q
```

The suite covers authentication, tenant isolation, input validation, provider behavior, RAG pipeline/retrieval, knowledge reindexing, widget rate limiting, prompt-injection heuristics, Battle execution, admin pagination, RBAC safeguards, logging and frontend asset contracts.

## Git workflow

Development is organized around focused feature branches. Each completed feature is merged into `main` with `git merge --no-ff`, then the branch is deleted.

See [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md) and [`docs/GIT_HISTORY.md`](docs/GIT_HISTORY.md).

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/API.md`](docs/API.md)
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)
- [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md)
- [`docs/GIT_HISTORY.md`](docs/GIT_HISTORY.md)
- [`docs/RAG.md`](docs/RAG.md)
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md)

## اتصال API خارجی با OpenRouter

در تنظیمات برنامه، بخش هوش مصنوعی را روی **API اختصاصی** بگذارید و این Base URL را وارد کنید:

```text
https://openrouter.ai/api/v1
```

کلید OpenRouter را در فیلد API Key وارد کنید و «دریافت مدل‌ها» را بزنید. فهرست از کاتالوگ رسمی OpenRouter ساخته می‌شود و نام، شناسه، طول context و قیمت ورودی/خروجی هر مدل را نگه می‌دارد؛ در گزینه‌های مدل، مدل‌های رایگان، پولی و مواردی که قیمت اعلام نشده‌اند از هم مشخص می‌شوند. عدد «کل مدل‌ها» با تعداد مدل‌های چت فرق دارد، چون کاتالوگ می‌تواند مدل‌های تصویر/صوت یا قابلیت‌های دیگر را هم شامل شود.

برای اینکه یک مدل صرفاً به علت محدودیت probe از فهرست حذف نشود، گزینه‌های چت بر اساس modalityهای اعلام‌شده توسط OpenRouter نمایش داده می‌شوند. پس از انتخاب مدل، دکمهٔ **تست اتصال** را بزنید تا دسترسی واقعی حساب به همان مدل بررسی شود. برای embedding، برنامه درخواست آزمایشی واقعی می‌فرستد و فقط مدلی را قابل انتخاب اعلام می‌کند که طول بردارش دقیقاً با `EMBEDDING_DIMENSIONS` پروژه و فضای برداری پایگاه داده سازگار باشد؛ صرف حضور مدل در کاتالوگ به معنی سازگاری ابعاد نیست.

کلید API را در HTML/JavaScript یا Git قرار ندهید. با تنظیم API در صفحه، کلید از مرورگر به بک‌اند ارسال و طبق رفتار فعلی برنامه در تنظیمات همان حساب ذخیره می‌شود؛ پایگاه داده و نسخه‌های پشتیبان آن نیز باید محافظت شوند. برای استفاده از OpenRouter به‌عنوان provider پیش‌فرض سرور، به‌جای درج کلید در کد، متغیرهای `DEFAULT_PROVIDER_BASE_URL=https://openrouter.ai/api/v1` و `DEFAULT_PROVIDER_API_KEY` را در محیط محرمانهٔ سرور تنظیم کنید.

## Project boundary

The project uses a simple embedded vector store because the target deployment does not require a separate vector service. Prompt-injection detection is deliberately heuristic and is a monitoring/control layer, not a claim of complete model security. The public-widget rate limiter is currently in-memory per process.

## احراز هویت

ورود با نام کاربری و رمز عبور همچنان فعال است و قابلیت **ادامه با گوگل** نیز از طریق Supabase Auth در کنار آن قرار دارد. جریان Google OAuth در Supabase انجام می‌شود؛ پس از بازگشت به `frontend/auth-callback.html`، توکن Supabase در بک‌اند اعتبارسنجی می‌شود و برنامه توکن نشست اختصاصی Prismo را صادر می‌کند. ورود گوگل، ورود ایمیلی/نام‌کاربری موجود را جایگزین نمی‌کند.

برای Google Login، در Supabase به `Authentication → Providers → Google` بروید و Provider گوگل را با Client ID و Client Secret که از Google Cloud ساخته‌اید فعال کنید. سپس در `Authentication → URL Configuration` مسیرهای بازگشت زیر را به Redirect URLs مجاز اضافه کنید:

- `http://localhost:8000/auth-callback.html` برای اجرای محلی؛
- `https://YOUR-DOMAIN/auth-callback.html` برای دامنهٔ نهایی.

متغیرهای `SUPABASE_URL` و `SUPABASE_ANON_KEY` در سرور باید متعلق به همان پروژهٔ Supabase باشند. کلید `anon`/publishable عمومی است؛ از کلید `service_role` در مرورگر استفاده نکنید. Google Client Secret فقط در تنظیمات امن Supabase/Google Cloud نگهداری می‌شود و در فرانت‌اند قرار نمی‌گیرد. جزئیات استقرار در [راهنمای استقرار](docs/DEPLOYMENT.md) آمده است.

## مدل چت و embedding مستقل

در تنظیمات اتصال هوش مصنوعی، منبع و مدل چت و منبع و مدل embedding جداگانه انتخاب می‌شوند. برای ذخیرهٔ انتخاب مستقل روی پایگاه‌دادهٔ Supabase/PostgreSQL، فایل `supabase/migrations/005_independent_embedding_provider.sql` را یک بار در SQL Editor اجرا کنید.

برای پاک‌سازی جدول نگاشت OAuth که در نسخه‌های قدیمی ساخته شده بود، فایل `supabase/migrations/006_remove_oauth_identities.sql` را در صورت وجود جدول قدیمی، یک بار اجرا کنید. این migration فقط جدول نگاشت OAuth را حذف می‌کند؛ جدول کاربران، تنظیمات، اسناد و تاریخچهٔ چت را حذف نمی‌کند.
