# مرجع API

آدرس پایه (به‌صورت پیش‌فرض، وقتی با `setup.bat` اجرا می‌شود): `http://127.0.0.1:8000`

مستندات تعاملی Swagger هم به‌صورت خودکار در دسترس است: **`/docs`**
(مثلاً `http://127.0.0.1:8000/docs`) — از آنجا می‌توانی هر endpoint را مستقیماً
تست کنی.

همه‌ی مسیرهای زیر (به‌جز مواردی که صراحتاً «بدون نیاز به توکن» نوشته شده) به
هدر `Authorization: Bearer <token>` نیاز دارند.

## احراز هویت — `/api/auth`

| متد | مسیر | توضیح |
|---|---|---|
| POST | `/api/auth/register` | ثبت‌نام؛ ورودی: `username`, `password`, `org_name?` → خروجی: `access_token` |
| POST | `/api/auth/login` | ورود؛ ورودی: `username`, `password` → خروجی: `access_token` |
| GET | `/api/auth/me` | اطلاعات کاربر لاگین‌شده |

## تنظیمات — `/api/settings`

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/settings` | تنظیمات فعلی (اتصال مدل + RAG/پرامپت + ویجت) |
| PUT | `/api/settings` | بروزرسانی هرکدام از فیلدها (partial update) |
| POST | `/api/settings/discover-models` | دریافت فهرست مدل‌های API اختصاصی از endpoint استاندارد `/models` بدون ذخیره‌ی کلید ارسال‌شده |
| POST | `/api/settings/test-custom-connection` | تست اتصال اختصاصی فعلی فرم، بدون ذخیره‌ی تنظیمات |
| POST | `/api/settings/test-connection` | یک تماس آزمایشی با ارائه‌دهنده‌ی فعلی برای اعتبارسنجی اتصال |

## داشبورد کاربر — `/api/dashboard`

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/dashboard/summary` | خلاصه‌ی scoped شامل وضعیت Provider، تعداد اسناد/چانک‌ها/پیام‌ها و نشست‌ها |

## دانشنامه — `/api/knowledge`

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/knowledge/documents` | لیست اسناد کاربر |
| POST | `/api/knowledge/documents` | افزودن سند جدید (تکه‌تکه + ایندکس خودکار) |
| GET | `/api/knowledge/documents/{id}` | مشاهده‌ی کامل یک سند |
| PUT | `/api/knowledge/documents/{id}` | ویرایش عنوان/محتوا (در صورت تغییر محتوا، دوباره ایندکس می‌شود) |
| POST | `/api/knowledge/documents/{id}/reindex` | بازسازی ایندکس برداری یک سند بدون تغییر محتوای خام |
| DELETE | `/api/knowledge/documents/{id}` | حذف یک سند |
| DELETE | `/api/knowledge/documents` | حذف کامل دانشنامه‌ی کاربر |

## آزمایشگاه تست — `/api/playground`

| متد | مسیر | توضیح |
|---|---|---|
| POST | `/api/playground/chat` | یک چرخه‌ی کامل RAG (بازیابی + پاسخ) با حفظ تاریخچه‌ی نشست |
| POST | `/api/playground/search` | فقط جست‌وجوی معنایی (بدون فراخوانی مدل چت) + امتیاز شباهت |
| GET | `/api/playground/free-models` | لیست مدل‌های رایگان آماده |
| POST | `/api/playground/battle` | ارسال یک پرامپت به دو مدل رایگان و مقایسه‌ی پاسخ‌ها |

## ویجت (داشبورد) — `/api/widget`

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/widget/config` | تنظیمات ظاهری فعلی ویجت |
| PUT | `/api/widget/config` | بروزرسانی عنوان/پیام خوش‌آمد/رنگ |
| GET | `/api/widget/embed-code` | تکه‌کد آماده برای جاسازی در وب‌سایت |

## ویجت عمومی (بدون نیاز به توکن) — `/public/widget`

این‌ها همان مسیرهایی هستند که فایل `widget.js` از داخل وب‌سایت شخص‌ثالث
صدا می‌زند.

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/public/widget/{widget_id}/config` | عنوان/پیام خوش‌آمد/رنگ/وضعیت آنلاین |
| POST | `/public/widget/{widget_id}/chat` | ارسال پیام و دریافت پاسخِ مبتنی بر دانشنامه‌ی صاحب ویجت |

## پنل ادمین — `/api/admin` (فقط نقش `admin`)

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/admin/stats` | آمار کلان (کاربران، اسناد، مکالمات، پرچم‌های امنیتی) |
| GET | `/api/admin/users?search=&limit=&offset=` | لیست/جست‌وجوی کاربران با صفحه‌بندی |
| GET | `/api/admin/users/{id}` | جزئیات کامل یک کاربر (شامل تنظیمات مدل) |
| GET | `/api/admin/users/{id}/documents` | بازرسی دانشنامه‌ی یک کاربر |
| GET | `/api/admin/users/{id}/sessions` | نشست‌های گفت‌وگوی یک کاربر |
| GET | `/api/admin/sessions/{session_id}/messages` | متن کامل یک مکالمه |
| POST | `/api/admin/users/{id}/block` | مسدودسازی کاربر |
| POST | `/api/admin/users/{id}/unblock` | رفع مسدودیت |
| POST | `/api/admin/users/{id}/role` | تغییر نقش (`user` / `admin`) |
| POST | `/api/admin/users/{id}/impersonate` | صدور توکن موقتِ «ورود به‌جای کاربر» |
| GET | `/api/admin/conversations?source=&flagged_only=&limit=&offset=` | لیست نشست‌های گفت‌وگو با صفحه‌بندی |
| GET | `/api/admin/security/flags?resolved=&limit=&offset=` | پیام‌های مظنون به تزریق پرامپت با صفحه‌بندی |
| POST | `/api/admin/security/flags/{message_id}/resolve` | علامت‌گذاری یک مورد به‌عنوان بررسی‌شده |

## رفتار عمومی API

پاسخ‌های خطای غیرمنتظره جزئیات استثناء داخلی را به کلاینت نمی‌دهند و در صورت تولید request ID، مقدار `X-Request-ID` و همان شناسه در بدنه‌ی خطای 500 قابل پیگیری است.

Endpoint عمومی ویجت می‌تواند در صورت عبور از محدودکننده‌ی نرخ با `429` پاسخ دهد. محدودکننده‌ی فعلی per-process است.

## کدهای خطا

| کد | معنی |
|---|---|
| 400 | ورودی نامعتبر (مثلاً نام کاربری تکراری) |
| 401 | توکن ارسال نشده یا نامعتبر/منقضی |
| 403 | توکن معتبر است ولی دسترسی کافی نیست (نقش عادی روی مسیر ادمین، یا حساب مسدود) |
| 404 | منبع پیدا نشد (سند/کاربر/نشست) |
| 422 | خطای اعتبارسنجی فیلدها (مثلاً `temperature` خارج از بازه‌ی مجاز) |
| 502 | تماس با سرویس هوش مصنوعی (چت یا امبدینگ) شکست خورد — پیام خطا فارسی و قابل‌فهم است |
