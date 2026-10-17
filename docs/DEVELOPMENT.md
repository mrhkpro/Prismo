# Development Guide — Prismo

این راهنما برای اجرای محلی، فهم ساختار کد و اجرای تست‌هاست. برای استقرار عمومی به [DEPLOYMENT.md](DEPLOYMENT.md) و برای رفتار سیستم به [ARCHITECTURE.md](ARCHITECTURE.md) مراجعه کنید.

## 1. ساختار کد

- `app/`: برنامه‌ی FastAPI، تنظیمات، مدل‌های SQLAlchemy، schemaهای Pydantic، امنیت، Routerها و serviceها.
- `frontend/`: رابط HTML/CSS/JavaScript شامل ورود، داشبورد، پنل ادمین و ویجت جاسازی‌شده.
- `supabase/migrations/`: فایل‌های SQL برای ساخت/تغییر schema مربوط به PostgreSQL/Supabase.
- `tests/`: تست‌های واحد، integration/API، امنیت و frontend-contract.
- `docs/`: معماری، RAG، theme، امنیت، API، استقرار و history.
- `data/`: فایل‌های runtime محلی؛ دیتابیس و لاگ runtime نباید artifact قابل‌انتشار تلقی شوند.
- `relay/`: سرویس relay اختیاری برای بعضی سناریوهای اتصال AI؛ اجرای اصلی برنامه به آن نیاز ندارد.

## 2. نیازمندی‌ها

Setup script پروژه Python 3.10 یا جدیدتر را بررسی می‌کند. وابستگی‌های runtime در `requirements.txt` ثبت شده‌اند. برای معماری اصلی Docker، دیتابیس برداری جدا یا سرور frontend جدا لازم نیست.

## 3. اجرای محلی روی Windows

روش ساده: از ریشه‌ی پروژه فایل `setup.bat` را اجرا کنید. این اسکریپت محیط مجازی `.venv` را ایجاد/بررسی می‌کند، وابستگی‌ها را نصب می‌کند، در صورت نیاز `.env` را از `.env.example` می‌سازد و برنامه را اجرا می‌کند.

اجرای دستی با محیط مجازی موجود در PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

آدرس برنامه: `http://127.0.0.1:8000/` و Swagger: `http://127.0.0.1:8000/docs`.

## 4. اجرای محلی روی Linux/macOS

```bash
chmod +x run.sh
./run.sh
```

اجرای دستی:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`run.sh` از متغیرهای `HOST`, `PORT` و `OPEN_BROWSER` نیز پشتیبانی می‌کند.

## 5. حالت‌های دیتابیس در development

در فایل `.env`:

```dotenv
APP_ENV=development
DATABASE_MODE=local
```

`DATABASE_MODE=local` دیتابیس SQLite در `data/app.db` را انتخاب می‌کند؛ `DATABASE_URL` برای این حالت لازم نیست. اگر می‌خواهید برنامه روی کامپیوتر شما اجرا شود ولی داده‌ها در Supabase باشند، `DATABASE_MODE=supabase` و `DATABASE_URL` معتبر تنظیم کنید. مقدار `auto` در صورت وجود `DATABASE_URL` به PostgreSQL می‌رود و در غیر این صورت SQLite را برمی‌گزیند.

اجرای محلی لزوماً آفلاین نیست: مدل پیش‌فرض یا Google Auth ممکن است به اینترنت نیاز داشته باشند. Provider مدل را فقط به endpoint محلی تغییر دهید وقتی واقعاً یک سرویس سازگار روی همان کامپیوتر اجرا می‌شود.

## 6. اجرای تست‌ها

از ریشه‌ی مخزن:

```bash
pytest -q
```

برای تست مشخص:

```bash
pytest -q tests/test_answer_cache.py
pytest -q tests/test_full_platform_flow.py
pytest -q tests/test_theme_contracts.py
```

نام فایل‌های تست ممکن است با اضافه‌شدن قابلیت‌ها تغییر کند؛ در صورت نبودن یکی از فایل‌های نمونه، فهرست `tests/` را بررسی کنید.

تست‌های پروژه بخش‌هایی مثل authentication، tenant isolation، RAG store/pipeline، provider، cache پاسخ، reindex، widget rate limit، prompt-injection rules، Battle، admin RBAC، logging و قراردادهای رابط را بررسی می‌کنند. تست‌های mocked جای تست واقعی Google OAuth، API مدل آنلاین، PostgreSQL زنده یا deployment را نمی‌گیرند.

## 7. گردش پیشنهادی توسعه

1. از شاخه‌ی به‌روز `main` یک شاخه‌ی کوچک و مشخص بسازید.
2. یک تغییر با دامنه‌ی محدود انجام دهید.
3. برای رفتار جدید یا باگ اصلاح‌شده تست اضافه/به‌روز کنید.
4. `pytest -q` و بررسی‌های مرتبط را اجرا کنید.
5. diff و فایل‌های محرمانه را بررسی کنید؛ `.env`، API Key، JWT secret و فایل دیتابیس را commit نکنید.
6. با پیام Conventional Commit ثبت کنید و پس از بررسی، طبق [GIT_WORKFLOW.md](GIT_WORKFLOW.md) ادغام کنید.

## 8. قواعد نگهداری

- هنگام افزودن query داده‌ی tenant، شناسه‌ی مالک را صریحاً فیلتر کنید.
- برای تغییر schema محلی و PostgreSQL، تفاوت مسیر auto-create در SQLite و Migrationهای دستی Supabase را رعایت کنید.
- API Key و Connection String را در log یا پاسخ معمول API نمایش ندهید.
- برای تغییر تم از design tokenها استفاده کنید؛ [THEME.md](THEME.md) را بخوانید.
- اسناد موضوعی را با تغییر behavior به‌روز کنید؛ `CHANGELOG*.md` برای تاریخچه است، نه جایگزین راهنمای فعلی.
- بهینه‌سازی عملکرد را با timing یا تست اندازه‌گیری کنید، نه فقط با برداشت ظاهری.
