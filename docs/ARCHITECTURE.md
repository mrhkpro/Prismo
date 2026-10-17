# معماری Prismo | Architecture

Prismo یک پلتفرم چندکاربره برای ساخت دستیارهای هوش مصنوعی دانش‌محور است. رابط کاربری، API، منطق RAG و اتصال دیتابیس در یک مخزن نگهداری می‌شوند. این سند ساختار جاری کد و مسیرهای اصلی اجرا را توضیح می‌دهد.

## 1. نمای کلی

```text
Browser (dashboard / admin / login)     External site (widget.js)
                 │ HTTP / SSE                         │ public API
                 └────────────────┬──────────────────┘
                                  ▼
                         FastAPI — app/main.py
       ┌──────────┬─────────┬────────────┬───────────┬─────────┐
       │ Auth/RBAC│Dashboard│ Knowledge  │ Playground│ Widget  │ Admin
       └──────────┴─────────┴────────────┴───────────┴─────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
          SQLAlchemy ORM                     RAG / AI services
                 │                                 │
       ┌─────────┴─────────┐          ┌─────────────┴──────────────┐
       ▼                   ▼          ▼                            ▼
 SQLite + JSON + NumPy   PostgreSQL + pgvector     OpenAI-compatible chat / embedding APIs
       (local)                 (Supabase/cloud)
```

- برنامه‌ی FastAPI می‌تواند فایل‌های استاتیک فرانت‌اند و APIها را با یک سرور ارائه کند؛ سرور فرانت‌اند جداگانه برای معماری اصلی لازم نیست.
- Uvicorn برنامه را در اجرای محلی اجرا می‌کند.
- محل اجرای برنامه، محل دیتابیس و محل اجرای مدل هوش مصنوعی مستقل از هم هستند. اجرای محلی با SQLite به معنی آفلاین بودن ارائه‌دهنده‌ی AI نیست.
- در PostgreSQL/Supabase، ساختار دیتابیس باید با Migrationهای SQL آماده شده باشد؛ برنامه هنگام startup جداول hosted را خودکار ایجاد یا اصلاح نمی‌کند.

## 2. ساختار مخزن

```text
Prismo/
├── app/
│   ├── main.py                 # ساخت FastAPI، lifespan، static assets و middleware
│   ├── config.py               # تنظیمات محیط، دیتابیس، مدل‌ها و پارامترهای RAG
│   ├── database.py             # SQLAlchemy engine، SessionLocal و get_db
│   ├── models.py               # مدل‌های ORM و جدول‌های دیتابیس
│   ├── schemas.py              # مدل‌های اعتبارسنجی درخواست/پاسخ API
│   ├── security.py             # هش رمز، JWT و وابستگی‌های احراز هویت
│   ├── i18n.py                 # پیام‌های بومی‌سازی‌شده سمت سرور
│   ├── exceptions.py           # خطاهای برنامه و پاسخ استاندارد
│   ├── seed.py                 # آماده‌سازی حساب مدیر در حالت محلی
│   ├── routers/                # endpointها بر اساس حوزه‌ی کاری
│   └── services/               # منطق RAG، مدل‌ها، کش، استریم و ایمنی
├── frontend/
│   ├── index.html              # ورود و ثبت‌نام
│   ├── auth-callback.html      # callback ورود گوگل
│   ├── dashboard.html          # فضای کاری کاربر
│   ├── admin.html              # پنل مدیریت
│   ├── widget.js               # اسکریپت قابل جاسازی در سایت دیگر
│   ├── widget-preview.html     # پیش‌نمایش ویجت
│   └── assets/                 # CSS، JavaScript، آیکون و PDF.js
├── supabase/migrations/        # Migrationهای SQL مخصوص PostgreSQL/Supabase
├── tests/                      # تست‌های واحد، API، یکپارچه و قرارداد رابط
├── docs/                       # راهنماهای فنی و تاریخچه‌ی نسخه‌ها
├── data/                       # داده‌های runtime محلی، مثل SQLite و لاگ راه‌اندازی
├── relay/                      # سرویس relay اختیاری؛ برای اجرای اصلی ضروری نیست
├── scripts/                    # اسکریپت‌های نگهداری/بررسی
├── requirements.txt            # وابستگی‌های Python برنامه اصلی
├── setup.bat                   # راه‌اندازی محلی Windows
├── run.sh                      # راه‌اندازی Linux/macOS
├── .env.example                # الگوی متغیرهای محیطی
└── README.md                   # معرفی و شروع سریع
```

### Routerهای اصلی

| فایل | مسئولیت |
|---|---|
| `app/routers/auth.py` | ثبت‌نام، ورود، خروج، کاربر جاری و جریان Google/Supabase |
| `app/routers/dashboard.py` | آمار محدودشده به مالک حساب |
| `app/routers/settings.py` | تنظیمات مدل، کشف/آزمون مدل‌ها و پروفایل‌های ذخیره‌شده |
| `app/routers/knowledge.py` | ساخت، ویرایش، حذف، ایندکس و reindex اسناد |
| `app/routers/playground.py` | چت آزمایشگاه، استریم، جست‌وجوی معنایی، نشست‌ها و Battle |
| `app/routers/widget.py` | تنظیمات ویجت و تولید کد embed |
| `app/routers/public_widget.py` | پیکربندی و گفت‌وگوی عمومی ویجت |
| `app/routers/admin.py` | آمار، مدیریت کاربران، بازرسی نشست‌ها و هشدارهای امنیتی |

### Serviceهای مهم

| فایل | مسئولیت |
|---|---|
| `services/llm_client.py` | حل تنظیمات ارائه‌دهنده و فراخوانی APIهای چت/Embedding سازگار با OpenAI |
| `services/text_split.py` | تقسیم متن به تکه‌های هم‌پوشان |
| `services/rag_store.py` | ثبت chunkها، بازیابی و شباهت کسینوسی؛ NumPy در SQLite و pgvector در PostgreSQL |
| `services/rag_pipeline.py` | هماهنگی بازیابی، ساخت prompt، اجرای مدل و ذخیره‌ی پاسخ |
| `services/answer_cache.py` | حافظه‌ی پاسخ برای تکرارهای واجد شرایط |
| `services/streaming.py` | رویدادهای استریم پاسخ |
| `services/injection_scanner.py` | بررسی heuristic ورودی‌های مشکوک |
| `services/rate_limit.py` | محدودکننده‌ی پایه برای چت عمومی ویجت |
| `services/response_quality.py` | کنترل‌های کیفیت خروجی مدل |

## 3. دیتابیس و مدل داده

مدل‌های ORM در `app/models.py` تعریف شده‌اند.

| جدول | کاربرد |
|---|---|
| `users` | نام کاربری، هش رمز، نقش، فعال/مسدود بودن و تاریخ‌های حساب |
| `user_settings` | تنظیمات اتصال چت و Embedding، prompt، Temperature، RAG و گزینه‌های ویجت |
| `saved_chat_models` | پروفایل‌های مدل چت ذخیره‌شده برای هر کاربر |
| `saved_embedding_models` | پروفایل‌های مدل Embedding ذخیره‌شده برای هر کاربر |
| `documents` | محتوای خام سند و فراداده‌ی مالکیت |
| `chunks` | تکه‌های متن، شناسه‌ی سند/مالک و embedding |
| `chat_sessions` | نشست‌های آزمایشگاه یا ویجت |
| `chat_messages` | پیام‌های کاربر/دستیار و نشان‌های امنیتی مرتبط |
| `answer_cache` | پاسخ‌های ذخیره‌شده‌ی واجد شرایط برای بازیابی سریع |

ستون‌های برداری با توجه به دیتابیس فرق می‌کنند:

- **SQLite:** embedding در قالب JSON ذخیره می‌شود و NumPy محاسبه‌ی cosine similarity را انجام می‌دهد.
- **PostgreSQL/Supabase:** embedding با نوع `pgvector` ذخیره می‌شود و query برداری در PostgreSQL اجرا می‌شود.

### انتخاب حالت دیتابیس

تنظیم `DATABASE_MODE` در `app/config.py` سه مقدار دارد:

- `local`: دیتابیس داخلی SQLite را انتخاب می‌کند.
- `supabase`: `DATABASE_URL` مربوط به PostgreSQL لازم است.
- `auto`: اگر `DATABASE_URL` وجود داشته باشد از PostgreSQL استفاده می‌کند؛ در غیر این صورت SQLite را انتخاب می‌کند.

محیط `production` به PostgreSQL نیاز دارد. حالت SQLite هنگام startup جدول‌های ORM و برخی اصلاحات سازگاری محلی را انجام می‌دهد. ساختار PostgreSQL/Supabase باید با فایل‌های `supabase/migrations/*.sql` مدیریت شود.

## 4. جریان یک درخواست RAG

1. Endpoint، هویت کاربر، ورودی و تنظیمات مؤثر را بررسی می‌کند.
2. مسیر گفتگو ابتدا امکان استفاده از پاسخ قبلی/کش را بررسی می‌کند، وقتی شرایط ایمن و زمینه‌ی مکالمه اجازه بدهند.
3. ارائه‌دهنده و مدل Embedding resolve می‌شوند و سؤال به بردار تبدیل می‌شود.
4. `rag_store.search` فقط chunkهای متعلق به مالک همان دستیار را بررسی می‌کند.
5. `similarity_threshold` نتایج کم‌شباهت را حذف و `top_k` تعداد نتایج منتخب را محدود می‌کند.
6. prompt سیستمی، زمینه‌ی بازیابی‌شده و تاریخچه‌ی محدود گفتگو کنار هم قرار می‌گیرند.
7. مدل چت پاسخ را تولید می‌کند؛ پاسخ و پیام‌ها ذخیره می‌شوند و زمان‌های مهم در لاگ ثبت می‌شوند.
8. رابط می‌تواند پاسخ کامل یا رویدادهای SSE را دریافت کند.

جزئیات بیشتر در [RAG.md](RAG.md) و [CHAT_ARCHITECTURE.md](CHAT_ARCHITECTURE.md) است.

## 5. احراز هویت و جداسازی کاربران

- مسیرهای خصوصی به JWT معتبر Prismo نیاز دارند.
- مسیرهای مدیریتی نقش `admin` را هم بررسی می‌کنند.
- اسناد، chunkها، نشست‌ها، تنظیمات و cache بر اساس مالک محدود می‌شوند.
- صاحب ویجت عمومی با شناسه‌ی عمومی/opaque ویجت پیدا می‌شود؛ کلید خصوصی Provider به مرورگر بازدیدکننده داده نمی‌شود.
- ورود با گوگل، در صورت پیکربندی، از Supabase Auth و PKCE استفاده می‌کند؛ رمز گوگل در اختیار Prismo قرار نمی‌گیرد.

این کنترل‌ها مانع هر سوءاستفاده‌ی ممکن نیستند؛ برای محدودیت‌ها و ملاحظات اجرایی [SECURITY.md](SECURITY.md) را ببینید.

## 6. خطا و پایش

Middleware درخواست شناسه‌ی `X-Request-ID` و زمان اجرا را ثبت می‌کند. خطاهای قابل پیش‌بینی پاسخ استاندارد می‌گیرند؛ جزئیات خام exception نباید به کلاینت برگردد. رخدادهای امنیتی علامت‌گذاری‌شده در مسیرهای مدیریتی قابل بررسی هستند، اما این با یک داشبورد جامع برای تمام خطاهای عملیاتی فرق دارد.

## 7. معماری رابط و پوسته‌ها

فرانت‌اند با HTML، CSS و JavaScript معمولی ساخته شده است. `frontend/assets/css/style.css` شامل design tokenها و قواعد کامپوننت‌هاست؛ `frontend/assets/js/theme.js` اعمال تم را مدیریت می‌کند و `settings.js` تنظیمات، زبان و جهت رابط را هماهنگ می‌کند. جزئیات و روش افزودن تم در [THEME.md](THEME.md) توضیح داده شده است.
