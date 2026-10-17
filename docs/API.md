# مرجع API — Prismo

پایه‌ی API در اجرای محلی به‌طور پیش‌فرض `http://127.0.0.1:8000` است. مستندات تعاملی FastAPI پس از اجرا در `/docs` و schema در `/openapi.json` در دسترس‌اند.

مگر جایی که صریحاً عمومی ذکر شده، endpointهای زیر به JWT معتبر Prismo در سربرگ زیر نیاز دارند:

```http
Authorization: Bearer <access_token>
```

## 1. احراز هویت — `/api/auth`

| متد | مسیر | کاربرد |
|---|---|---|
| `POST` | `/api/auth/register` | ایجاد حساب با نام کاربری، رمز عبور و نام سازمان اختیاری |
| `POST` | `/api/auth/login` | ورود و دریافت JWT برنامه |
| `POST` | `/api/auth/logout` | خروج از جریان API؛ کلاینت نیز باید توکن محلی را حذف کند |
| `GET` | `/api/auth/me` | اطلاعات کاربر جاری |
| `POST` | `/api/auth/google-pkce` | مبادله‌ی کد PKCE با Supabase و صدور JWT Prismo |
| `POST` | `/api/auth/google-supabase` | مسیر سازگاری قدیمی برای تبادل توکن Supabase |

## 2. داشبورد — `/api/dashboard`

| متد | مسیر | کاربرد |
|---|---|---|
| `GET` | `/api/dashboard/summary` | آمار محدودشده به کاربر جاری: سند، chunk، پیام، نشست و provider فعال |

## 3. تنظیمات و Provider — `/api/settings`

| متد | مسیر | کاربرد |
|---|---|---|
| `GET` | `/api/settings` | دریافت تنظیمات جاری مدل، RAG، prompt و ویجت |
| `PUT` | `/api/settings` | ذخیره‌ی فیلدهای تنظیمات ارسالی |
| `POST` | `/api/settings/discover-models` | دریافت/بررسی فهرست مدل‌های chat از API سازگار |
| `POST` | `/api/settings/discover-embedding-models` | کشف مدل‌های Embedding و بررسی سازگاری بردار |
| `POST` | `/api/settings/test-custom-connection` | تست اطلاعات اتصال واردشده در فرم بدون ذخیره‌ی آن فرم |
| `POST` | `/api/settings/test-connection` | تست provider فعال |
| `GET` | `/api/settings/provider-diagnostics` | تشخیص اطلاعات اتصال و خطاهای provider |
| `GET` | `/api/settings/saved-chat-models` | فهرست پروفایل‌های chat متعلق به کاربر |
| `POST` | `/api/settings/saved-chat-models` | افزودن/ذخیره‌ی پروفایل chat |
| `DELETE` | `/api/settings/saved-chat-models` | حذف پروفایل chat متعلق به کاربر طبق شناسه‌ی درخواست |
| `POST` | `/api/settings/saved-chat-models/use` | فعال کردن پروفایل chat انتخاب‌شده |
| `POST` | `/api/settings/saved-chat-models/test` | آزمایش پروفایل chat ذخیره‌شده |
| `GET` | `/api/settings/saved-embedding-models` | فهرست پروفایل‌های Embedding متعلق به کاربر |
| `POST` | `/api/settings/saved-embedding-models` | ذخیره‌ی پروفایل Embedding |
| `POST` | `/api/settings/saved-embedding-models/current` | ذخیره/ثبت پروفایل Embedding جاری طبق payload |
| `DELETE` | `/api/settings/saved-embedding-models` | حذف پروفایل Embedding انتخاب‌شده |
| `POST` | `/api/settings/saved-embedding-models/use` | فعال کردن پروفایل Embedding |
| `POST` | `/api/settings/saved-embedding-models/test` | آزمایش پروفایل Embedding ذخیره‌شده |

جزئیات فیلدهای هر درخواست در OpenAPI و مدل‌های `app/schemas.py` تعریف شده‌اند. کلید API در خروجی عادی تنظیمات برگردانده نمی‌شود.

## 4. دانشنامه — `/api/knowledge`

| متد | مسیر | کاربرد |
|---|---|---|
| `GET` | `/api/knowledge/documents` | فهرست اسناد کاربر جاری |
| `POST` | `/api/knowledge/documents` | ایجاد سند و ایندکس آن |
| `POST` | `/api/knowledge/documents/stream` | ایجاد سند همراه رویدادهای پیشرفت ایندکس |
| `GET` | `/api/knowledge/documents/{doc_id}` | دریافت جزئیات سند متعلق به کاربر |
| `PUT` | `/api/knowledge/documents/{doc_id}` | ویرایش اطلاعات/متن و بازسازی chunkها در صورت تغییر متن |
| `POST` | `/api/knowledge/documents/{doc_id}/reindex` | بازسازی ایندکس برداری از محتوای ذخیره‌شده |
| `DELETE` | `/api/knowledge/documents/{doc_id}` | حذف سند متعلق به کاربر و chunkهای آن |
| `DELETE` | `/api/knowledge/documents` | پاک کردن دانشنامه‌ی همان کاربر |

## 5. آزمایشگاه — `/api/playground`

| متد | مسیر | کاربرد |
|---|---|---|
| `POST` | `/api/playground/sessions/new` | ایجاد نشست آزمایشگاه |
| `DELETE` | `/api/playground/sessions/{session_id}` | حذف نشست متعلق به کاربر |
| `POST` | `/api/playground/chat` | اجرای یک چرخه‌ی RAG و دریافت پاسخ/منابع |
| `POST` | `/api/playground/chat/stream` | پاسخ استریم‌شده با SSE |
| `POST` | `/api/playground/search` | فقط بازیابی معنایی و امتیاز تکه‌ها؛ بدون chat completion |
| `GET` | `/api/playground/free-models` | فهرست مدل‌های آماده برای گزینه‌های Battle |
| `POST` | `/api/playground/battle` | مقایسه‌ی دو مدل به‌صورت موازی |
| `POST` | `/api/playground/battle/stream` | استریم پاسخ‌های دو مدل در Battle |

جست‌وجوی معنایی الزاماً مدل چت را فراخوانی نمی‌کند؛ پاسخ RAG از بازیابی اطلاعات و سپس تولید پاسخ تشکیل می‌شود. Battle برای مقایسه مستقیم پرامپت‌ها طراحی شده و به‌طور خودکار کل چرخه‌ی RAG را اجرا نمی‌کند.

## 6. ویجت — تنظیمات خصوصی `/api/widget`

| متد | مسیر | کاربرد |
|---|---|---|
| `GET` | `/api/widget/config` | دریافت تنظیمات ویجت کاربر |
| `PUT` | `/api/widget/config` | ذخیره‌ی تنظیمات ویجت |
| `GET` | `/api/widget/embed-code` | ساخت کد قابل جاسازی در سایت دیگر |

## 7. ویجت عمومی — `/public/widget`

این مسیرها برای بازدیدکننده‌ی سایت میزبان هستند و JWT حساب Prismo لازم ندارند. شناسه‌ی ویجت عمومی مشخص می‌کند کدام دستیار اجرا شود.

| متد | مسیر | کاربرد |
|---|---|---|
| `GET` | `/public/widget/{widget_id}/config` | عنوان، پیام خوش‌آمد و تنظیمات عمومی ویجت |
| `POST` | `/public/widget/{widget_id}/chat` | دریافت پاسخ چت عمومی |
| `POST` | `/public/widget/{widget_id}/chat/stream` | پاسخ چت عمومی به‌صورت SSE |

## 8. پنل ادمین — `/api/admin`

تمام مسیرهای این بخش به JWT کاربر دارای نقش `admin` نیاز دارند.

| متد | مسیر | کاربرد |
|---|---|---|
| `GET` | `/api/admin/stats` | آمار کلی پلتفرم |
| `GET` | `/api/admin/users?search=&limit=&offset=` | جست‌وجو و صفحه‌بندی کاربران |
| `GET` | `/api/admin/users/{user_id}` | جزئیات حساب کاربر |
| `POST` | `/api/admin/users/{user_id}/block` | مسدود کردن حساب |
| `POST` | `/api/admin/users/{user_id}/unblock` | فعال کردن حساب |
| `POST` | `/api/admin/users/{user_id}/role` | تغییر نقش user/admin با کنترل‌های حفاظتی |
| `GET` | `/api/admin/users/{user_id}/documents` | بازرسی اسناد حساب هدف |
| `GET` | `/api/admin/users/{user_id}/sessions` | فهرست نشست‌های حساب هدف |
| `GET` | `/api/admin/sessions/{session_id}/messages` | پیام‌های یک نشست |
| `POST` | `/api/admin/users/{user_id}/impersonate` | صدور توکن موقت برای پشتیبانی |
| `GET` | `/api/admin/conversations?source=&flagged_only=&limit=&offset=` | فهرست نشست‌ها و مکالمات |
| `GET` | `/api/admin/security/flags` | فهرست پیام‌های امنیتی علامت‌گذاری‌شده |
| `GET` | `/api/admin/security/summary` | خلاصه‌ی هشدارهای بررسی‌نشده |
| `POST` | `/api/admin/security/flags/{message_id}/resolve` | ثبت رسیدگی به هشدار |

## 9. سرویس عمومی و رفتار خطا

- `GET /api/health`: بررسی سبک در دسترس بودن برنامه؛ سلامت دیتابیس و provider را به‌طور کامل ثابت نمی‌کند.
- `GET /api/runtime`: اطلاعات حالت دیتابیس و تشخیص runtime را می‌دهد.
- پاسخ استریم از `text/event-stream` استفاده می‌کند. در استریم چت، رویدادهای متداول `meta`, `delta`, `done`, `error` هستند؛ در Battle رویدادهای مربوط به دو طرف نیز فرستاده می‌شوند.
- middleware شناسه‌ی درخواست را در سربرگ `X-Request-ID` قرار می‌دهد تا خطا در لاگ دنبال شود.
- محدودکننده‌ی نرخ ویجت عمومی در حافظه‌ی هر process است و کد `429` ممکن است برگرداند.

## 10. کدهای خطای متداول

| HTTP | معنا |
|---|---|
| `400` | درخواست معتبر نیست یا عملیات به دلیل قاعده‌ی برنامه رد شده است |
| `401` | توکن مفقود، منقضی یا نامعتبر است |
| `403` | حساب غیرفعال است یا نقش کافی ندارد |
| `404` | منبع متعلق به درخواست پیدا نشد یا در دسترس نیست |
| `422` | اعتبارسنجی payload یا پارامترها شکست خورده است |
| `429` | محدودیت نرخ درخواست فعال شده است |
| `502` | ارائه‌دهنده‌ی هوش مصنوعی پاسخ معتبر نداده یا تماس با آن شکست خورده است |
| `503` | سرویس یا دیتابیس موقتاً در دسترس نیست |

مرجع واقعی قراردادها، OpenAPI تولیدشده توسط برنامه و مدل‌های `app/schemas.py` هستند؛ این سند یک نقشه‌ی کاربردی از گروه‌های endpoint است.
