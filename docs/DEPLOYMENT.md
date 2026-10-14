# Deployment Guide

Prismo is a FastAPI application with a static frontend, SQLite for local development, Supabase PostgreSQL with pgvector for cloud deployment, and an OpenAI-compatible model provider.

## Local Windows

Run `setup.bat`. The script creates `.venv`, verifies Python 3.10+, checks/restores pip when necessary, prepares `.env` from `.env.example`, starts Uvicorn on `127.0.0.1:8000`, and opens the browser.

Dependency installation is resilient to common package-index/DNS problems. The installer tries the official PyPI index first and then HTTPS mirrors. You can override the order with `PRISMO_PIP_INDEX_URL` before running the setup script. The legacy `QUASAR_PIP_INDEX_URL` variable remains supported for existing setups.

The setup script does not ask for an API key. Provider credentials belong in the local `.env` file or can be configured through the application's provider settings.

## Local Linux / macOS

Run:

```bash
chmod +x run.sh
./run.sh
```

The launcher accepts:

```bash
HOST=127.0.0.1 PORT=8000 OPEN_BROWSER=true ./run.sh
```

For a hosted process, bind explicitly to the desired interface, for example `HOST=0.0.0.0`, and keep `OPEN_BROWSER=false`.

## Environment

Copy `.env.example` to `.env` and set production values before exposing the service publicly. At minimum, configure a strong `SECRET_KEY` (32+ characters) and provider credentials required by your selected model configuration.

Never commit `.env`, API keys, database files, or other runtime secrets.

## Health check

The service exposes `GET /api/health` for a lightweight availability check.

## Production notes

Run behind a reverse proxy or managed process service, terminate TLS at the edge, and restrict CORS to the origins that actually need access when the deployment is not serving the embeddable public widget.

The public widget rate limiter is in-memory and therefore scoped to one application process. A multi-instance deployment should use a shared rate-limit store before relying on the limit as a cross-instance control.

Cloud production requires a PostgreSQL `DATABASE_URL`. It must not fall back to a local SQLite file. PostgreSQL mode does not create a local data directory.

## مسیر فعلی: از مرحله ۱۴ تا Vercel

این راهنما برای همان پوشه `G:\desktop\پارت\راکد 2\Final Project\Supa Base` است. همه دستورها را در PowerShell همین پوشه اجرا کن. اجرای برنامه از طریق Python موجود در `.venv` است.

### ۱. پایان مرحله ۱۴

```powershell
Set-Location -LiteralPath 'G:\desktop\پارت\راکد 2\Final Project\Supa Base'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Test-Path Env:DATABASE_URL
```

خروجی دستور آخر باید `False` باشد.

### ۲. اعمال اصلاحات آماده

بسته `vercel-fixes.zip` را بیرون از پوشه پروژه باز کن. محتوای آن را داخل پوشه اصلی `Supa Base` کپی کن و جایگزینی فایل‌های هم‌نام را تأیید کن. بعد از کپی، `.vercelignore` باید کنار `requirements.txt` باشد.

بسته فقط شامل فایل‌های اصلاح‌شده، تست‌های مربوط و این راهنماست. `.env`، دیتابیس محلی، `.venv` و `.git` در آن نیستند.

اصلاحات: جلوگیری از نوشتن فایل دیتابیس در Vercel، الزام PostgreSQL در production، جلوگیری از آپلود فایل‌های خصوصی، جداسازی تست‌ها از Supabase، نمایش کنترل‌شده خطای embedding و جلوگیری از پاسخ‌سازی وقتی هیچ منبعی پیدا نمی‌شود.

تست‌های مرتبط را اجرا کن:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_cloud_runtime.py tests/test_cloud_rag.py tests/test_rag_store.py tests/test_rag_pipeline.py tests/test_knowledge_reindex.py tests/test_api_integration.py
```

نتیجه بررسی این نسخه: `23 passed`. در کل مجموعه `61 passed, 1 failed` مشاهده شد. همان تست صفحه‌بندی کاربران ادمین (`test_user_listing_honors_limit_and_offset`) قبل از اصلاحات هم شکست می‌خورد؛ این تغییرات آن بخش را دست نمی‌زنند.

### ۳. تست واقعی با Supabase، پیش از استقرار

در Supabase، بخش Table Editor باید این شش جدول را داشته باشد:

`users`، `user_settings`، `documents`، `chunks`، `chat_sessions`، `chat_messages`.

در PowerShell، به‌جای متن جایگزین، دقیقاً همان Connection String را قرار بده که قبلاً با آن خروجی `1` گرفته‌ای. در Supabase این آدرس از `Connect → Transaction pooler` گرفته می‌شود. اگر گذرواژه کاراکتر ویژه دارد، بخش گذرواژه در URL باید URL-encoded باشد؛ آدرسی که قبلاً تست موفق داشته را بدون تغییر استفاده کن.

```powershell
$env:DATABASE_URL='YOUR_TESTED_SUPABASE_CONNECTION_STRING'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

این اجرای برنامه واقعاً در Supabase داده ذخیره می‌کند. مرورگر را روی `http://127.0.0.1:8000` باز کن. با نام کاربری `ADMIN_USERNAME` و رمز `ADMIN_PASSWORD` فایل محلی `.env` وارد شو. در حالت SQLite، حساب ادمین در شروع برنامه ایجاد یا با مقدارهای تنظیم‌شده هماهنگ می‌شود. اگر اجرای محلی به Supabase متصل است، برای همگام‌سازی حساب پیکربندی‌شده فقط در محیط توسعه، `PRISMO_BOOTSTRAP_ADMIN_ON_STARTUP=true` را در `.env` محلی قرار بده؛ این گزینه در محیط عملیاتی نباید فعال شود.

در «دانشنامه → افزودن سند جدید» این سند را ثبت کن:

عنوان: `ساعات کاری`

متن: `شرکت از شنبه تا چهارشنبه، ساعت ۸ تا ۱۴ فعال است. پنجشنبه و جمعه تعطیل است.`

ثبت سند باید موفق باشد و تعداد تکه‌ها صفر نباشد. این مرحله علاوه بر چت، API واقعی embedding را هم امتحان می‌کند.

در SQL Editor سوپابیس اجرا کن:

```sql
select id, user_id, document_id,
       extensions.vector_dims(embedding) as dimensions
from public.chunks
order by id;
```

باید برای سند ثبت‌شده ردیف ببینی و `dimensions` برابر `2560` باشد.

در «آزمایشگاه تست» بپرس: `ساعات کاری شرکت چیست؟` پاسخ باید ۸ تا ۱۴ باشد و بخش «منابع بازیابی‌شده» سند ساعات کاری را نشان بدهد. سپس در یک گفت‌وگوی جدید بپرس: `دفتر شرکت در کدام خیابان است؟` پاسخ باید نبود اطلاعات را اعلام کند، نه آدرس ساختگی.

با یک حساب دیگر که سندی ندارد وارد شو و سؤال ساعات کاری را بپرس. سند حساب ادمین و پاسخ مستند آن نباید برای این حساب نمایش داده شود.

اگر ثبت سند، ابعاد بردار، منابع یا پاسخ‌ها درست نبود، همان‌جا متوقف شو و خطا را بفرست. اجرای مراحل بعدی مشکل RAG را حل نمی‌کند.

پس از موفقیت این مرحله، در Terminal برنامه `Ctrl+C` بزن و سپس:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
```

### ۴. اتصال به Vercel

Vercel CLI روی سیستم موجود است؛ نسخه بررسی‌شده `54.17.3` بود.

```powershell
vercel.cmd login
vercel.cmd link
```

ورود را در مرورگر خودت تأیید کن. در `link` حساب خودت را انتخاب کن، برای ساخت پروژه جدید به `Link to existing project?` پاسخ `N` بده، نام پروژه را `rag-widget` و مسیر کد را `./` قرار بده.

### ۵. متغیرهای Vercel

Vercel در حال حاضر FastAPI را با Python runtime به‌صورت zero-config پشتیبانی می‌کند؛ این پروژه عمداً ساختار فعلی خود را حفظ می‌کند تا مسیرهای موجود تغییر نکنند.

در داشبورد Vercel، پروژه را باز کن و به `Settings → Environment Variables` برو. برای هر پنج مقدار زیر، هر دو محیط `Preview` و `Production` را انتخاب کن. برای Preview مقدارها را به همه شاخه‌ها اعمال کن.

| نام | مقدار |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | همان Transaction Pooler URL تست‌شده |
| `SECRET_KEY` | مقدار فعلی `SECRET_KEY` از `.env` محلی؛ مقدار بررسی‌شده ۴۳ کاراکتر داشت |
| `DEFAULT_PROVIDER_API_KEY` | مقدار فعلی همین متغیر از `.env` محلی |
| `ADMIN_PASSWORD` | همان رمز ادمین استفاده‌شده در تست Supabase |
| `AI_REQUEST_TIMEOUT_SECONDS` | `45` |
| `AI_MAX_RETRIES` | `2` |

مقدارها را بدون نام متغیر، بدون علامت `=` و بدون کوتیشن وارد کن. فقط مقدار Secretها را در حساب Vercel خودت قرار بده؛ در پیام خطا یا اسکرین‌شات ارسالی منتشرشان نکن.

### ۶. Preview

```powershell
vercel.cmd
```

اگر درباره تغییر تنظیمات Build/Output سؤال شد، پاسخ `N` بده. Framework باید FastAPI تشخیص داده شود. پس از رسیدن deployment به `Ready`، URL خروجی را باز کن و این مسیرها را بررسی کن:

`/api/health` → `{"status":"ok"}`

`/docs` → مستندات API

`/` → صفحه پروژه

Health فقط اجرای برنامه را بررسی می‌کند؛ به‌تنهایی اثبات سالم بودن دیتابیس و RAG نیست.

با همان حساب ادمین وارد شو. سند ساعات کاری که در تست محلی با Supabase ساخته‌ای باید وجود داشته باشد. یک سند کوتاه جدید از خود سایت Vercel بساز تا ذخیره‌سازی از Vercel هم تأیید شود. سؤال ساعات کاری و سؤال آدرس را دوباره امتحان کن؛ منابع بازیابی‌شده را کنترل کن.

در «ویجت و کد امبد»، پیش‌نمایش ویجت را باز کن و سؤال ساعات کاری را بپرس. پاسخ باید از همان دانشنامه باشد.

### ۷. انتشار نهایی و ماندگاری داده

فقط بعد از موفق بودن تست‌های Preview:

```powershell
vercel.cmd --prod
```

در URL نهایی، ورود، سند ذخیره‌شده، سؤال ساعات کاری و ویجت را دوباره بررسی کن. سند جدیدی که روی Preview ساخته‌ای باید بعد از این استقرار هم باقی مانده باشد؛ داده‌ها در Supabase هستند، نه روی فایل‌سیستم Vercel.

اگر deployment شکست خورد، متن خطای قرمز Build Logs یا Runtime Logs را بفرست. کلیدها و Connection String را از متن حذف کن.

## محدوده بررسی این نسخه

- کد اصلی روی درایو G تغییر داده نشد؛ اصلاحات روی کپی پروژه آماده شدند.
- مدل PostgreSQL به‌صورت `VECTOR(2560)` و اتصال به‌صورت `NullPool` بدون اتصال شبکه‌ای import شدند.
- ۲۳ تست مرتبط با cloud، RAG، ثبت سند و جداسازی کاربران موفق شدند.
- آزمون واقعی endpoint مدل، جداول زنده Supabase و deployment انجام نشده است؛ اتصال دیتابیس در فایل `.env` ارسالی نبود و Vercel CLI هنوز به حساب وارد نشده بود.
- وجود migration در کد به معنی اجرای موفق آن روی دیتابیس زنده نیست. معیارهای مرحله ۳ برای تأیید واقعی لازم‌اند.

## مستندات رسمی بررسی‌شده در ۲ اکتبر ۲۰۲۶

- FastAPI، lifespan، frontend و entrypointهای Vercel: <https://vercel.com/docs/frameworks/backend/fastapi>
- Connection string و Transaction Pooler: <https://supabase.com/docs/guides/database/connecting-to-postgres>
- SQLAlchemy و NullPool: <https://supabase.com/docs/guides/troubleshooting/using-sqlalchemy-with-supabase-FUqebT>
- Psycopg و `prepare_threshold=None`: <https://supabase.com/docs/guides/troubleshooting/disabling-prepared-statements-qL8lEL>
- فایل‌های مجاز برای upload: <https://vercel.com/docs/deployments/vercel-ignore>
- متغیرهای Preview و Production: <https://vercel.com/docs/environment-variables>
- فایل‌سیستم read-only: <https://vercel.com/docs/functions/runtimes>
- مسیر CLI تا Production: <https://vercel.com/docs/projects/deploy-from-cli>

### عیب‌یابی خطای اتصال سرویس AI در Vercel

اگر لوکال مدل‌ها را می‌بیند اما Vercel پیام «اتصال به سرویس هوش مصنوعی برقرار نشد» نشان می‌دهد، این پیام مربوط به `APIConnectionError` است و قبل از دریافت پاسخ مدل رخ می‌دهد. نسخه فعلی کلاینت برای اجرای hosted، timeout و retry صریح دارد و خطای اتصال را در Runtime Logs با `base_url` و نوع خطا ثبت می‌کند؛ API key هرگز در لاگ ثبت نمی‌شود.

ابتدا در سایت Vercel این مسیر را باز کن:

`/api/settings/test-connection`

این endpoint به احراز هویت نیاز دارد و نتیجه اتصال provider را برمی‌گرداند. سپس در Runtime Logs دنبال عبارت `AI provider connection failed` بگرد. اگر خطا `ConnectError`، DNS یا timeout باشد، مشکل مسیر شبکه Vercel به `DEFAULT_PROVIDER_BASE_URL` است و تغییر RAG یا مدل‌های داخل پروژه آن را حل نمی‌کند. در این حالت باید دسترسی خروجی Vercel به `racode-llm.partschool.ir` از همان deployment تأیید شود یا provider از یک endpoint عمومی که Vercel بتواند به آن وصل شود ارائه شود.

برای تست مستقل، بعد از deployment این مسیرها را بررسی کن:

- `/api/health` → اجرای FastAPI
- `/api/settings/test-connection` → اتصال provider
- `/api/playground/free-models` → لیست مدل‌های پیش‌فرض بدون تماس با provider

نکته: وجود متغیر `DEFAULT_PROVIDER_API_KEY` در Vercel کافی نیست؛ deployment باید واقعاً بتواند به Base URL متصل شود.

## Google Login through Supabase Auth

Google sign-in is an optional login method alongside the existing username/password route. The login button redirects to the configured Supabase project's Google provider. Supabase returns to `frontend/auth-callback.html`; the callback sends the Supabase access token to `POST /api/auth/google-supabase`. The backend verifies that token by calling the Supabase Auth user endpoint with the public project anon key, then returns Prismo's normal bearer JWT.

Configure `SUPABASE_URL` and `SUPABASE_ANON_KEY` for the same project used by the frontend redirect. If not overridden, the application defaults target the Supabase project supplied with the original working Google-login flow. Set these variables explicitly when using another project.

In Supabase Dashboard, enable `Authentication → Providers → Google` and enter the Google OAuth Client ID and Client Secret from Google Cloud. In `Authentication → URL Configuration`, add the exact callback URL(s) to the redirect allow list:

- Local: `http://localhost:8000/auth-callback.html`
- Hosted: `https://YOUR-DOMAIN/auth-callback.html`

In Google Cloud, add the Supabase callback shown in the Supabase Google provider page as the authorized redirect URI (normally `https://YOUR-PROJECT-REF.supabase.co/auth/v1/callback`). Use the exact value displayed by your Supabase project. Google Client Secret must stay in Supabase/Google Cloud configuration; never put it in browser JavaScript or `.env.example`. The `SUPABASE_ANON_KEY` is a public client key, not a service-role secret.

The Google/Supabase route returns a normal Prismo JWT; the rest of the application keeps using the existing token-based authorization. The original username/password sign-in and registration endpoints remain enabled. Live OAuth must be tested with the actual Supabase Google provider and redirect allow list configured in the target deployment.


## v2.8.5: Google sign-in, answer-cache migration, and hosted callback

### Supabase Google Auth

For the production site `https://rag-widget-beta.vercel.app`, set Supabase **Authentication → URL Configuration → Site URL** to:

```text
https://rag-widget-beta.vercel.app
```

Add the following to the Supabase **Redirect URLs** allow-list:

```text
https://rag-widget-beta.vercel.app/auth-callback.html
http://localhost:8000/auth-callback.html
```

Keep the localhost URL only for development. When the user starts OAuth from the production `*.vercel.app` deployment, Prismo selects the canonical production callback; it does not direct a hosted sign-in to localhost. Configure Google as a provider in Supabase. In Google Cloud's OAuth web client, the authorized redirect URI is the Supabase callback (not the Prismo callback):

```text
https://<SUPABASE-PROJECT-REF>.supabase.co/auth/v1/callback
```

Ensure `SUPABASE_URL` and `SUPABASE_ANON_KEY` (public anon/publishable key only; never `service_role`) are set consistently in Vercel Production and in local `.env`. The callback uses PKCE: it expects a short-lived `?code=...`, removes it from the address bar before exchanging it, and posts the code and a session-held verifier to `/api/auth/google-pkce`. The backend returns only Prismo's application JWT. Do not enable/require the implicit fragment-token flow for this application.

After changing Supabase URL settings, redeploy only if environment variables changed; URL allow-list changes take effect at Supabase. Test sign-in from the production domain and confirm the final URL is `/dashboard.html` on that same domain, not `localhost` and not a URL containing `access_token`, `refresh_token` or `provider_token`.

### RAG answer cache migration

On PostgreSQL/Supabase, run `supabase/migrations/007_answer_cache.sql` once in SQL Editor. SQLite/local mode creates `answer_cache` via SQLAlchemy metadata at startup. If the migration is not present in a hosted schema, chat still works without the optional cache; repeated-question speedups will be unavailable.

### Security notifications

The lower-left red admin button is populated from `GET /api/admin/security/summary`, which queries flagged and unresolved `ChatMessage` rows in the current database. All authorized admins sharing that database see the same unresolved report count. Repeated detected extraction attempts in one session are elevated to critical. Local SQLite and the hosted Supabase database are separate alert stores unless both environments point to the same database.
