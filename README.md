# Prismo — RAG Widget Platform

**وب‌سایت / Live website:** https://rag-widget-beta.vercel.app/dashboard.html

[فارسی](#persian) · [English](#english)

---

<a id="persian"></a>

## فارسی


> **درباره این مخزن:** این پروژه سورس‌کد وب‌سایت بالا است. فایل `.env` و اطلاعات محرمانه‌ی اتصال در مخزن قرار داده نشده‌اند؛ بنابراین برنامه بدون تنظیم فایل محیطی اجرا نمی‌شود و به دیتابیس اصلی متصل نخواهد شد. با این حال، می‌توانید پروژه را به‌صورت کامل در محیط محلی اجرا کنید؛ کافی است فایل `.env` را بر اساس `.env.example` تنظیم کنید و از SQLite محلی و تنظیمات/کلیدهای API خودتان استفاده کنید.

### قابلیت‌های اصلی

- **حساب کاربری و دسترسی:** ثبت‌نام و ورود با نام کاربری و رمز عبور، نشست JWT، مسدودسازی حساب و ورود اختیاری با گوگل از طریق Supabase Auth و PKCE.
- **اتصال مدل‌ها:** پیکربندی APIهای سازگار با OpenAI، تست اتصال و کشف مدل‌ها؛ انتخاب مستقل ارائه‌دهنده و مدل چت و Embedding.
- **دانشنامه و RAG:** بارگذاری یا افزودن محتوا، استخراج و تکه‌بندی متن، ساخت بردارهای معنایی، جست‌وجوی شباهت، تنظیم `top_k` و `Similarity Threshold` و ایندکس‌گذاری مجدد اسناد.
- **آزمایشگاه:** گفت‌وگوی آزمایشی با نشست‌های ذخیره‌شده، جست‌وجوی معنایی و Battle Mode برای مقایسه‌ی دو مدل و زمان پاسخ‌دهی آن‌ها.
- **کش و استریم پاسخ:** تاریخچه‌ی محدود گفتگو، نمایش تدریجی پاسخ و کش پاسخ‌های واجد شرایط برای سریع‌تر شدن سؤال‌های تکراری.
- **ویجت قابل جاسازی:** تنظیم عنوان، پیام خوش‌آمدگویی، رنگ و ظاهر؛ دریافت کد Embed برای استفاده در وب‌سایت دیگر.
- **پنل ادمین:** آمار کلی، مدیریت کاربران و نقش‌ها، بررسی نشست‌ها و گفتگوها، ورود موقت برای پشتیبانی و هشدارهای مبتنی بر قواعد برای ورودی‌های مشکوک.
- **پایش و تجربه‌ی کاربری:** شناسه‌ی درخواست و لاگ زمان‌بندی API، رابط واکنش‌گرا، پوسته‌ی روشن/تیره و اعلان‌های رابط.

### معماری در یک نگاه

```text
مرورگر / ویجت جاسازی‌شده
          │ HTTP / SSE
          ▼
      FastAPI (Python)
       ├─ احراز هویت و نقش‌ها
       ├─ داشبورد و تنظیمات
       ├─ دانشنامه و آزمایشگاه
       ├─ ویجت عمومی
       └─ پنل ادمین
          │
          ├─ SQLAlchemy → SQLite (محلی)
          └─ RAG → جست‌وجوی برداری NumPy یا pgvector → API مدل
```

در حالت محلی، پروژه می‌تواند از SQLite استفاده کند و به سرویس دیتابیس جداگانه‌ای نیاز ندارد. برای اجرای ابری یا اجرای محلی با دیتابیس ابری، PostgreSQL در Supabase نیز پشتیبانی می‌شود. ورود با گوگل به پیکربندی Supabase Auth وابسته است؛ اجرای محلی برنامه به‌تنهایی به معنای اجرای آفلاین مدل‌های هوش مصنوعی نیست.

جریان معمول RAG چنین است:

```text
سؤال → Embedding → بازیابی تکه‌های متعلق به کاربر
      → اعمال Similarity Threshold و Top-K
      → تاریخچه‌ی محدود + دستور سیستم + زمینه‌ی بازیابی‌شده
      → مدل چت → ذخیره‌ی پیام و وضعیت‌های مرتبط
```

### شروع سریع

**پیش‌نیاز:** پیش از اجرا، فایل `.env` را از روی `.env.example` بسازید و تنظیمات لازم را وارد کنید. بدون تنظیمات محیطی معتبر، برنامه اجرا نمی‌شود.

**ویندوز:** فایل `setup.bat` را اجرا کنید. این اسکریپت محیط مجازی `.venv` را می‌سازد، وابستگی‌ها را نصب می‌کند، در صورت نیاز `.env` را از `.env.example` می‌سازد و برنامه را اجرا می‌کند.

**Linux / macOS:**

```bash
chmod +x run.sh
./run.sh
```

پس از اجرا، آدرس پیش‌فرض برنامه `http://127.0.0.1:8000/` است. مستندات تعاملی API نیز در `/docs` در دسترس‌اند.

فایل `.env` را از `.env.example` بسازید و اطلاعات لازم برای ارائه‌دهنده‌ی مدل را تنظیم کنید. کلیدهای API، رمزها، `SECRET_KEY` و فایل‌های دیتابیس حاوی اطلاعات واقعی را در Git یا مخازن عمومی قرار ندهید. برای محیط Production، `SECRET_KEY` باید صریح و دست‌کم ۳۲ نویسه باشد.

### APIهای اصلی

- `/api/auth` — ثبت‌نام، ورود و اطلاعات کاربر جاری
- `/api/dashboard` — آمار مختص کاربر
- `/api/settings` — تنظیمات مدل، RAG، پرامپت و ویجت
- `/api/knowledge` — مدیریت اسناد و ایندکس‌گذاری مجدد
- `/api/playground` — چت، جست‌وجوی معنایی، نشست‌ها و Battle
- `/api/widget` — تنظیمات ویجت و کد Embed
- `/public/widget` — پیکربندی و گفت‌وگوی عمومی ویجت
- `/api/admin` — عملیات مدیریتی و کنترل دسترسی
- `/api/health` — بررسی سلامت سبک برنامه

### مستندات

راهنماهای کامل‌تر در پوشه‌ی `docs/` قرار دارند:

- [فهرست راهنماهای فنی](docs/README.md)
- [ساختار و پوسته‌های سایت](docs/THEME.md)
- [معماری و مدل داده](docs/ARCHITECTURE.md)
- [مرجع API](docs/API.md)
- [راهنمای توسعه](docs/DEVELOPMENT.md)
- [جریان Git](docs/GIT_WORKFLOW.md) · [تاریخچه Git](docs/GIT_HISTORY.md)
- [معماری RAG](docs/RAG.md)
- [امنیت](docs/SECURITY.md)
- [استقرار](docs/DEPLOYMENT.md)
- [تاریخچه تغییرات](docs/CHANGELOG.md)
- [تغییرات نسخه 2.8.10](docs/CHANGELOG_2.8.10.md)
- [سازگاری اجرای محلی با Supabase](docs/SUPABASE_LOCAL_COMPAT.md)

برای پیکربندی OpenRouter، ورود با گوگل، Migrationهای Supabase و جزئیات استقرار، راهنمای [استقرار](docs/DEPLOYMENT.md) و مستندات مرتبط در `docs/` را ببینید.

### تست‌ها

از ریشه‌ی مخزن اجرا کنید:

```bash
pytest -q
```

تست‌ها بخش‌هایی مانند احراز هویت، جداسازی کاربران، اعتبارسنجی ورودی، رفتار ارائه‌دهنده‌ها، بازیابی RAG، ایندکس‌گذاری اسناد، محدودیت درخواست ویجت، بررسی الگوهای prompt injection، Battle، نقش‌های ادمین و لاگ‌ها را پوشش می‌دهند.

### محدوده و ملاحظات

- مخزن برداری فعلی برای جست‌وجوی محلی از NumPy و برای PostgreSQL از `pgvector` استفاده می‌کند؛ به سرویس برداری جداگانه‌ای نیاز نیست.
- تشخیص prompt injection مبتنی بر قواعد و الگوهاست و امنیت کامل مدل را تضمین نمی‌کند.
- محدودکننده‌ی نرخ ویجت عمومی در حافظه‌ی هر فرایند نگهداری می‌شود؛ در استقرار چندنمونه‌ای، به راهکار مشترک نیاز است.
- جزئیات تنظیمات، امنیت و استقرار را در مستندات مرتبط بررسی کنید.

---

<a id="english"></a>

## English

**Prismo** is a knowledge-powered AI assistant and embeddable chat-widget platform. Each user can maintain a private knowledge base, configure chat and embedding providers independently, test RAG responses, compare two models, and publish a customizable widget on another website.

> **About this repository:** This repository contains the source code for the website linked above. The `.env` file and private connection credentials are not included, so the application will not start until its environment is configured and it will not connect to the original production database. You can still run the project locally; create `.env` from `.env.example` and configure local SQLite plus your own provider/API credentials.

### Key features

- **Accounts and access control:** Username/password registration and login, JWT sessions, account blocking, and optional Google sign-in through Supabase Auth with PKCE.
- **AI providers:** OpenAI-compatible APIs, connection tests and model discovery, with separate chat and embedding provider settings.
- **Knowledge base and RAG:** Document management, text chunking, embeddings, semantic retrieval, configurable `top_k` and similarity threshold, and document reindexing.
- **Test Lab:** Persistent chat sessions, semantic search, and two-model Battle mode with independent errors and response timing.
- **Faster conversations:** Bounded history, streamed responses, and a scoped answer cache for eligible repeated questions.
- **Embeddable widget:** Custom title, welcome message and color, plus embed code for external websites.
- **Admin console:** Platform statistics, user and role management, conversation inspection, temporary impersonation, and heuristic prompt-risk alerts.
- **Operational tools:** Request IDs and timing logs, responsive UI, light/dark themes, and toast notifications.

### Architecture

```text
Browser / embedded widget
          │ HTTP / SSE
          ▼
      FastAPI (Python)
       ├─ Auth and RBAC
       ├─ Dashboard and settings
       ├─ Knowledge and playground
       ├─ Public widget
       └─ Admin console
          │
          ├─ SQLAlchemy → SQLite (local)
          └─ RAG → NumPy cosine search or pgvector → model API
```

The app can run locally with SQLite or use PostgreSQL on Supabase. Google sign-in depends on Supabase Auth, and running the application locally does not automatically make cloud-based AI providers offline.

Typical RAG flow:

```text
Question → embedding → owner-scoped semantic retrieval
         → similarity threshold + top-k
         → bounded history + system prompt + retrieved context
         → chat completion → persist the conversation turn
```

### Quick start

**Prerequisite:** Before running the app, create `.env` from `.env.example` and provide the required settings. The application will not start without valid environment configuration.

**Windows:** Run `setup.bat`. It creates `.venv`, installs dependencies, creates `.env` from `.env.example` when needed, and starts the application.

**Linux / macOS:**

```bash
chmod +x run.sh
./run.sh
```

Default URL: `http://127.0.0.1:8000/`. Interactive API documentation is available at `/docs`.

Create `.env` from `.env.example` and configure the required provider settings. Never commit API keys, passwords, JWT secrets, `.env` files, or sensitive runtime database files. Production requires an explicitly configured `SECRET_KEY` with at least 32 characters.

### Main API groups

- `/api/auth` — registration, login and current user
- `/api/dashboard` — user-scoped dashboard summary
- `/api/settings` — model, RAG, prompt and widget settings
- `/api/knowledge` — document management and reindexing
- `/api/playground` — chat, semantic search, sessions and Battle
- `/api/widget` — widget settings and embed code
- `/public/widget` — public widget configuration and chat
- `/api/admin` — administration and RBAC
- `/api/health` — lightweight health check

### Documentation

Project documentation is maintained in `docs/`:

- [Documentation index](docs/README.md)
- [Frontend structure and themes](docs/THEME.md)
- [Architecture and data model](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Git workflow](docs/GIT_WORKFLOW.md) · [Git history](docs/GIT_HISTORY.md)
- [RAG pipeline](docs/RAG.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Changelog](docs/CHANGELOG.md)
- [v2.8.17 changelog](docs/CHANGELOG_2.8.17.md)
- [Local + Supabase compatibility](docs/SUPABASE_LOCAL_COMPAT.md)

For OpenRouter setup, Google sign-in, Supabase migrations, and deployment details, consult the relevant guides in `docs/`, especially [Deployment](docs/DEPLOYMENT.md).

### Tests

Run from the repository root:

```bash
pytest -q
```

The suite covers authentication, tenant isolation, input validation, provider behavior, RAG retrieval, document reindexing, public-widget rate limits, prompt-injection heuristics, Battle execution, admin RBAC, and logging.

### Scope and limitations

- The project uses NumPy for local vector search and `pgvector` with PostgreSQL; no separate vector database is required.
- Prompt-injection detection is heuristic and is not a guarantee of complete model security.
- Public-widget rate limiting is in-memory per process; multi-instance deployments need a shared limiter.

---

**Release line:** v2.8.17 · See [`docs/CHANGELOG.md`](docs/CHANGELOG.md) for recent changes.
