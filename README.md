# Prismo — RAG Widget Platform

A multi-tenant, knowledge-powered AI widget platform built with FastAPI, SQLAlchemy, SQLite, an embedded NumPy vector store, and Vanilla HTML/CSS/JS.

Each user can create a private knowledge base, configure an OpenAI-compatible model provider, tune RAG behavior, test conversations, compare two models, and publish a customizable chat widget to another website. An admin area provides RBAC, user management, telemetry, conversation inspection, impersonation, and heuristic prompt-injection monitoring.

## Features

- User registration, login, JWT sessions, logout and account blocking.
- User-scoped documents, chunks, conversations and settings.
- Custom OpenAI-compatible provider configuration, connection testing and model discovery.
- RAG with chunking, embeddings, cosine retrieval, configurable `top_k` and similarity threshold.
- Bounded conversation history and explicit retrieved-context boundaries.
- Knowledge-base CRUD plus explicit document reindexing.
- Chat playground with persistent sessions and owner-scoped session cleanup.
- Two-model Battle mode with independent errors and response timing.
- Embeddable widget using Shadow DOM, configurable title/message/color and cache-busted embed code.
- Public-widget input validation, account-state checks and per-process rate limiting.
- Admin dashboard, pagination, statistics, security flags, role management and safe impersonation.
- Centralized API errors, request IDs and request timing logs.
- Light/dark frontend theme support, responsive UI, accessible toast notifications and fetch timeouts.

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

## ورود با گوگل (اختیاری)

این نسخه جریان Authorization Code + PKCE را در بک‌اند FastAPI اجرا می‌کند؛ `GOOGLE_CLIENT_SECRET` هرگز به HTML یا JavaScript فرستاده نمی‌شود. در مخزن فعلی Supabase نقش PostgreSQL را دارد و برنامه از قبل از Supabase Auth استفاده نمی‌کند؛ حفظ همین backend auth باعث می‌شود حساب‌های محلی SQLite و حساب‌های میزبانی‌شده یک رفتار داشته باشند.

متغیرهای زیر را در فایل محلی `.env` یا Environment Variables سرویس میزبانی تنظیم کنید:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
APP_PUBLIC_URL=http://localhost:8000
```

`GOOGLE_REDIRECT_URI` باید دقیقاً با آدرس ثبت‌شده در Google Cloud Console برابر باشد؛ در محیط واقعی از HTTPS و دامنه‌ی واقعی برنامه استفاده کنید. نشست Google در کوکی امضاشده‌ی `HttpOnly`, `SameSite=Lax` ذخیره می‌شود. برای PostgreSQL/Supabase، قبل از استفاده از Google OAuth فایل `supabase/migrations/004_google_oauth_identity.sql` را یک‌بار در SQL Editor اجرا کنید. SQLite محلی ستون‌های لازم را هنگام راه‌اندازی به‌صورت سازگار اضافه می‌کند.

### مراحل Google Cloud و Supabase

1. در Google Cloud یک پروژه انتخاب یا بسازید و **Google Auth Platform / OAuth consent screen** را تکمیل کنید؛ هنگام توسعه، ایمیل حساب‌های آزمایشی را در Test users قرار دهید.
2. از بخش Credentials یک **OAuth client ID** از نوع **Web application** بسازید. برای توسعه، Authorized JavaScript origin را `http://localhost:8000` قرار دهید و Redirect URI را `http://localhost:8000/api/auth/google/callback` وارد کنید. اگر از `127.0.0.1` استفاده می‌کنید باید origin و redirect جداگانه همان میزبان را هم ثبت کنید.
3. Client ID و Client Secret را فقط در `.env` محلی یا تنظیمات رمزنگاری‌شده‌ی محیط اجرا ثبت کنید. در Vercel/میزبانی، `GOOGLE_REDIRECT_URI` باید مانند `https://YOUR-DOMAIN/api/auth/google/callback` باشد و همان مقدار عیناً در Google Cloud مجاز شده باشد.
4. اگر دیتابیس روی Supabase است، migration شماره 004 را در SQL Editor اجرا کنید. چون این نسخه مستقیماً با Google OIDC کار می‌کند، callback ثبت‌شده در Google Cloud به برنامه اشاره می‌کند، نه به `https://<project-ref>.supabase.co/auth/v1/callback`. تنظیم callback در Supabase Auth برای این جریان لازم نیست.
5. بعد از تنظیم، ورود با Google را روی همان دامنه‌ی HTTPS تست کنید. برای محیط تولید، یک `SECRET_KEY` قوی و یکتا نیز لازم است.
