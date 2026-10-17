# Deployment Guide — Prismo

Prismo یک برنامه‌ی Python/FastAPI با frontend استاتیک است. دیتابیس می‌تواند SQLite محلی یا PostgreSQL/Supabase باشد. مدل‌های چت و Embedding از طریق یک endpoint سازگار با OpenAI فراخوانی می‌شوند و می‌توانند بیرون از host برنامه قرار داشته باشند.

## 1. انتخاب معماری استقرار

| حالت | برنامه | دیتابیس | نیاز شبکه‌ای |
|---|---|---|---|
| Local-only app/data | FastAPI روی کامپیوتر | SQLite در `data/app.db` | API مدل و Google Auth در صورت استفاده همچنان ممکن است اینترنت بخواهند |
| Local + Supabase | FastAPI روی کامپیوتر | PostgreSQL/Supabase | دسترسی شبکه از کامپیوتر به Supabase و provider مدل |
| Hosted app + Supabase | runtime ابری مثل Vercel | PostgreSQL/Supabase | دسترسی خروجی runtime به Supabase و provider مدل |

**Local بودن برنامه با offline بودن مدل یکسان نیست.** برای AI کاملاً محلی باید chat و embedding provider روی خود سیستم اجرا شوند و Base URLها به آن‌ها اشاره کنند.

## 2. Local روی Windows

روش پیشنهادی: از ریشه‌ی پروژه `setup.bat` را اجرا کنید. پس از آماده شدن محیط، آدرس پیش‌فرض `http://127.0.0.1:8000/` و مستندات API در `/docs` هستند.

برای اجبار به SQLite، در `.env` تنظیم کنید:

```dotenv
APP_ENV=development
DATABASE_MODE=local
```

در حالت local، `DATABASE_URL` لازم نیست؛ فایل دیتابیس در `data/app.db` قرار می‌گیرد. حساب اولیه‌ی مدیر محلی از `ADMIN_USERNAME`, `ADMIN_PASSWORD` و `ADMIN_ORG_NAME` ساخته می‌شود. رمز دمو را پیش از اشتراک‌گذاری محیط تغییر دهید.

## 3. Local روی Linux/macOS

```bash
chmod +x run.sh
./run.sh
```

برای اجرای دستی، محیط مجازی بسازید، `pip install -r requirements.txt` را اجرا کنید و سپس `uvicorn app.main:app --reload --port 8000` را اجرا کنید.

## 4. اتصال Local به Supabase

در `.env`:

```dotenv
APP_ENV=development
DATABASE_MODE=supabase
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/postgres
```

مقدار واقعی را از Connect در داشبورد Supabase بردارید. اگر رمز شامل کاراکترهای ویژه‌ی URL باشد، باید درست URL-encode شود.

برای Local Uvicorn، اگر آدرس از shared Supavisor transaction pooler روی پورت `6543` استفاده کند و hostname از نوع `*.pooler.supabase.com` باشد، کد اتصال محلی پورت را به Session Pooler یعنی `5432` تغییر می‌دهد. این تغییر فقط در URL مؤثر روی engine است و مقدار نوشته‌شده در `.env` را عوض نمی‌کند. در Vercel پورت تنظیم‌شده برای runtime حفظ می‌شود. جزئیات در [SUPABASE_LOCAL_COMPAT.md](SUPABASE_LOCAL_COMPAT.md) آمده است.

### Schema و Migrationها

برخلاف SQLite، برنامه در startup به‌صورت خودکار schema دیتابیس PostgreSQL/Supabase را نمی‌سازد یا اصلاح نمی‌کند. Migrationهای موردنیاز باید روی دیتابیس هدف اعمال شده باشند.

1. از دیتابیس هدف backup بگیرید.
2. فایل‌های `supabase/migrations/` و توضیحات همان نسخه را بررسی کنید.
3. migrationهای پایه و هر migration مربوط به قابلیت‌های استفاده‌شده را در Supabase SQL Editor طبق ترتیب و راهنمای پروژه اجرا کنید.
4. migrationها را کورکورانه تکرار نکنید؛ به‌ویژه فایل‌هایی با واژه‌هایی مثل `remove` یا `drop` را پیش از اجرا بخوانید.
5. پس از اجرا، ستون‌ها و جدول‌های جدید را بررسی و چت، دانشنامه، saved models و cache را آزمایش کنید.

وجود فایل migration در repository ثابت نمی‌کند که آن روی دیتابیس واقعی اجرا شده است.

## 5. متغیرهای محیطی

تنظیم‌های مهم در `.env.example` فهرست شده‌اند:

| متغیر | کاربرد |
|---|---|
| `APP_ENV` | `development` یا `production` |
| `DATABASE_MODE` | `local`, `supabase` یا `auto` |
| `DATABASE_URL` | اتصال PostgreSQL؛ برای SQLite محلی لازم نیست |
| `SECRET_KEY` | امضای JWT؛ در Production باید صریح، یکتا و حداقل ۳۲ نویسه باشد |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_ORG_NAME` | مشخصات bootstrap مدیر محلی |
| `DEFAULT_PROVIDER_BASE_URL` | آدرس provider پیش‌فرض مدل |
| `DEFAULT_PROVIDER_API_KEY` | کلید محرمانه‌ی provider پیش‌فرض |
| `AI_REQUEST_TIMEOUT_SECONDS` | محدودیت زمانی درخواست مدل |
| `AI_MAX_RETRIES` | تعداد تلاش مجدد پیکربندی‌شده برای provider |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | تنظیمات عمومی لازم برای Google/Supabase Auth |
| `APP_PUBLIC_URL` | آدرس عمومی برنامه برای هدر/شناسه‌دهی provider در صورت نیاز |

فایل `.env` فقط برای محیط محلی باشد و وارد Git یا ZIP عمومی نشود. `SUPABASE_ANON_KEY` کلید عمومی client است؛ کلید `service_role` محرمانه است و نباید در فرانت‌اند قرار گیرد.

## 6. Google sign-in

ورود با گوگل اختیاری است و به Supabase Auth نیاز دارد.

1. در Supabase، Google provider را فعال کنید و Client ID/Secret را با تنظیمات Google Cloud هماهنگ کنید.
2. آدرس callback واقعی برنامه، مانند `http://localhost:8000/auth-callback.html` برای Local و دامنه‌ی HTTPS واقعی برای Hosted، را به allow-list مسیرهای بازگشت اضافه کنید.
3. در Google Cloud، URI مربوط به callback سرویس Supabase را طبق مقداری که داشبورد Supabase نشان می‌دهد ثبت کنید؛ callback گوگل به Supabase برمی‌گردد و سپس Supabase به callback Prismo هدایت می‌کند.
4. `SUPABASE_URL` و `SUPABASE_ANON_KEY` باید به همان پروژه‌ی Supabase اشاره کنند.
5. جریان PKCE را هم در Local و هم در دامنه‌ی نهایی آزمایش کنید. در پایان باید JWT خود Prismo صادر شود و توکن‌های provider در URL باقی نمانند.

اگر از ورود گوگل استفاده نمی‌کنید، مسیر username/password می‌تواند در حالت SQLite به‌صورت محلی کار کند.

## 7. Provider مدل و OpenRouter

می‌توانید provider را از صفحه‌ی اتصال هوش مصنوعی تعیین کنید یا از متغیرهای امن سرور برای provider پیش‌فرض استفاده کنید. برای OpenRouter، Base URL متداول این است:

```text
https://openrouter.ai/api/v1
```

کاتالوگ OpenRouter می‌تواند شناسه و متادیتای قیمت مدل را ارائه دهد؛ رایگان بودن یا قیمت به اطلاعات جاری خود ارائه‌دهنده وابسته است. پس از انتخاب مدل، تست اتصال اجرا شود. برای Embedding، برنامه خروجی واقعی را بررسی می‌کند تا بُعد بردار با `EMBEDDING_DIMENSIONS` و ستون دیتابیس سازگار باشد.

کلیدهای provider باید سمت سرور نگهداری شوند. افزودن کلید به صفحه باعث ارسال آن از مرورگر به backend می‌شود و برنامه آن را برای حساب مرتبط ذخیره می‌کند؛ بنابراین دسترسی به دیتابیس و backupها هم باید محافظت شود.

## 8. Hosted deployment / Vercel

برای اجرای Production:

- `APP_ENV=production` تنظیم شود.
- `DATABASE_URL` باید PostgreSQL/Supabase معتبر باشد؛ حالت Production نباید به SQLite محلی برگردد.
- `SECRET_KEY` قوی و سایر کلیدهای لازم را در Environment Variables سکوی میزبانی تنظیم کنید، نه در کد یا frontend.
- schema و Migrationهای Supabase را پیش از تست runtime اعمال کنید.
- در Preview و Production، envها را متناسب با همان محیط جداگانه تنظیم کنید.
- بعد از هر انتشار، `/api/health`, `/docs`, ورود، ایجاد سند، پاسخ RAG و ویجت عمومی را جداگانه تست کنید.

`GET /api/health` صرفاً بررسی سبکی از اجرای برنامه است و سلامت دیتابیس، provider یا کل RAG را تضمین نمی‌کند.

### محدودیت‌های استقرار

- فایل‌سیستم runtimeهای serverless را محل ذخیره‌ی دائمی دیتابیس قرار ندهید؛ برای Production از PostgreSQL استفاده کنید.
- rate limit عمومی ویجت فعلی در حافظه‌ی هر process است؛ برای چند instance به limit store مشترک نیاز دارید.
- شبکه‌ی runtime تا provider مدل باید واقعاً قابل دسترسی باشد. تنظیم API Key به‌تنهایی موفقیت اتصال را تضمین نمی‌کند.
- relay اختیاری است و برای معماری اصلی اجباری نیست؛ در صورت استفاده به [VERCEL_PROVIDER_RELAY.md](VERCEL_PROVIDER_RELAY.md) مراجعه کنید.

## 9. پس از استقرار

حداقل این سناریوها را آزمایش کنید:

1. ورود و خروج حساب، و Google login اگر فعال شده است.
2. ایجاد سند و تأیید غیرصفر بودن تعداد chunkها.
3. سؤال قابل پاسخ از دانشنامه و تأیید منبع بازیابی‌شده.
4. سؤال خارج از دانشنامه و بررسی اینکه پاسخ بی‌پشتوانه ساخته نشود.
5. استفاده از همان سؤال با حساب دیگر برای بررسی جداسازی مالکیت.
6. تست اتصال chat و embedding provider.
7. بارگذاری و پاسخ‌گویی ویجت در یک صفحه‌ی بیرونی.
8. ورود ادمین، بررسی هشدار و محدودیت نقش کاربر عادی.

برای عیب‌یابی provider در Vercel از [VERCEL_PROVIDER_DEBUG.md](VERCEL_PROVIDER_DEBUG.md) و برای عملکرد چت از [VERCEL_CHAT.md](VERCEL_CHAT.md) استفاده کنید.
