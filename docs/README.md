# Prismo Documentation

[فارسی](#راهنمای-فارسی) · [English](#english-guide)

<a id="راهنمای-فارسی"></a>

## راهنمای فارسی

این پوشه مستندات فنی Prismo را در یک ساختار موضوعی نگه می‌دارد. برای شروع از معماری استفاده کنید و سپس با توجه به کاری که انجام می‌دهید، راهنمای مربوط را باز کنید.

### راهنماهای اصلی

| سند | چه چیزی را توضیح می‌دهد؟ |
|---|---|
| [معماری پروژه](ARCHITECTURE.md) | ساختار مخزن، نقش پوشه‌ها، Routerها، مدل داده، جریان درخواست و تفاوت اجرای Local با Supabase |
| [طراحی و پوسته‌های رابط](THEME.md) | سیستم رنگ، ۱۰ پوسته، تغییر تم و زبان، فایل‌های CSS/JS مربوط و نحوه افزودن پوسته جدید |
| [چرخه RAG](RAG.md) | استخراج متن، chunking، embedding، جست‌وجوی معنایی، context، تاریخچه و کش پاسخ |
| [امنیت](SECURITY.md) | رمز عبور، JWT، جداسازی مالکیت، کلیدها، ویجت عمومی و نظارت بر ورودی‌های مشکوک |
| [مرجع API](API.md) | گروه‌بندی endpointها، احراز هویت، استریم و خطاهای رایج |
| [توسعه و تست](DEVELOPMENT.md) | نصب محلی، اجرای تست‌ها، ساختار کد و گردش تغییرات |
| [استقرار](DEPLOYMENT.md) | SQLite محلی، اتصال محلی به Supabase، تنظیم Google OAuth و استقرار ابری |
| [معماری گفت‌وگو](CHAT_ARCHITECTURE.md) | مسیر جزئی درخواست چت و تفاوت پاسخ عادی و استریم |

### راهنماهای عملیاتی و تخصصی

| سند | زمان استفاده |
|---|---|
| [سازگاری Local و Supabase](SUPABASE_LOCAL_COMPAT.md) | هنگام عیب‌یابی اتصال محلی به PostgreSQL/Supabase یا Session Pooler |
| [تشخیص مشکل Provider در Vercel](VERCEL_PROVIDER_DEBUG.md) | وقتی مدل در محیط ابری پاسخ نمی‌دهد یا اتصال ناموفق است |
| [بهینه‌سازی چت در Vercel](VERCEL_CHAT.md) | عیب‌یابی تأخیر و خطاهای پاسخ در اجرای serverless |
| [استفاده از Provider Relay در Vercel](VERCEL_PROVIDER_RELAY.md) | فقط وقتی از relay اختیاری برای ارتباط با سرویس مدل استفاده می‌کنید |
| [شروع سریع Relay](RELAY_QUICKSTART.md) | نصب و تنظیم سرویس relay اختیاری |
| [جریان Git](GIT_WORKFLOW.md) | شاخه‌ها، commit و merge |
| [تاریخچه Git](GIT_HISTORY.md) | سابقه و زنجیره‌ی تغییرات ثبت‌شده |
| [تاریخچه تغییرات](CHANGELOG.md) | خلاصه نسخه‌های اخیر و پیوند به یادداشت‌های جزئی هر نسخه |

### نکته درباره اعتبار مستندات

این مستندات کد فعلی را توضیح می‌دهند، اما فایل‌های `CHANGELOG*.md` تاریخچه‌ی تغییرات هر نسخه‌اند و ممکن است درباره‌ی رفتار قدیمی صحبت کنند. برای رفتار جاری، ابتدا کد داخل `app/` و `frontend/` و سپس راهنمای موضوعی مربوط را بررسی کنید.

Migrationهای SQL مربوط به PostgreSQL/Supabase در `supabase/migrations/` هستند. وجود یک فایل Migration به‌تنهایی به معنی اجرای آن روی پایگاه‌داده‌ی واقعی نیست؛ آن را فقط طبق راهنمای استقرار و پس از تهیه‌ی نسخه‌ی پشتیبان اجرا کنید.

---

<a id="english-guide"></a>

## English guide

This folder documents Prismo by topic. Start with the architecture guide, then open the guide matching your task.

| Document | Purpose |
|---|---|
| [Architecture](ARCHITECTURE.md) | Repository layout, modules, data model, request flow, and local/cloud database modes |
| [Theme system](THEME.md) | Design tokens, all ten themes, language direction, theme persistence, and how to add a theme |
| [RAG pipeline](RAG.md) | Text extraction, chunking, embeddings, retrieval, context assembly, conversation memory, and answer cache |
| [Security](SECURITY.md) | Password hashing, JWT, tenant isolation, secrets, public widget, and prompt-risk monitoring |
| [API reference](API.md) | API groups, auth requirements, streaming routes, and common errors |
| [Development](DEVELOPMENT.md) | Local setup, tests, code layout, and development workflow |
| [Deployment](DEPLOYMENT.md) | Local SQLite, Local + Supabase, Google OAuth, and hosted deployment |
| [Chat architecture](CHAT_ARCHITECTURE.md) | Chat request flow and streaming details |
| [Local/Supabase compatibility](SUPABASE_LOCAL_COMPAT.md) | Local PostgreSQL connectivity and pooler troubleshooting |
| [Vercel provider diagnostics](VERCEL_PROVIDER_DEBUG.md) | Debugging hosted model-provider connections |
| [Vercel chat runbook](VERCEL_CHAT.md) | Troubleshooting hosted response latency and failures |
| [Provider relay](VERCEL_PROVIDER_RELAY.md) | Optional provider relay architecture |
| [Relay quick start](RELAY_QUICKSTART.md) | Optional relay setup |
| [Git workflow](GIT_WORKFLOW.md) | Branching and merging conventions |
| [Git history](GIT_HISTORY.md) | Recorded repository history |
| [Changelog](CHANGELOG.md) | Recent changes and links to detailed release notes |

**Current code vs. historical notes:** versioned `CHANGELOG*.md` files describe historical changes and may refer to older behavior. Use the current source under `app/` and `frontend/` together with the relevant topical guide to understand what is implemented now.
