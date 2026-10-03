# Vercel Provider Diagnostics

برای مشکل «اتصال به سرویس هوش مصنوعی برقرار نشد» دیگر یک خطای عمومی نمایش داده نمی‌شود.

## داخل سایت

از پنل تنظیمات روی «تست اتصال» بزنید. endpoint زیر DNS، مرحله اتصال، HTTP status، نوع exception، مدل و زمان را برمی‌گرداند:

`GET /api/settings/provider-diagnostics`

API Key هرگز در پاسخ یا لاگ نوشته نمی‌شود.

## تفسیر مرحله‌ها

- `dns`: دامنه از محیط اجرا resolve نمی‌شود.
- `connect_timeout`: TCP/TLS در مهلت تعیین‌شده برقرار نشده است.
- `network`: اتصال رد/قطع شده یا شبکه در دسترس نیست.
- `tls`: خطای گواهی/SSL.
- `authentication`: API Key یا مجوز رد شده است.
- `http_404`: endpoint یا مدل اشتباه است.
- `rate_limit`: محدودیت 429.
- `http_5xx`: خطای سمت provider.
- `model`: سرویس در دسترس است ولی مدل انتخاب‌شده در `/models` دیده نشده است.

## نکته

اگر diagnostics مرحله `dns` یا `network` را در Vercel نشان دهد ولی همان Base URL در اجرای محلی کار کند، مشکل از مسیر Vercel تا provider است و تغییر در RAG/Frontend آن را برطرف نمی‌کند؛ در این حالت باید provider دسترسی Vercel را باز کند یا یک Base URL عمومی جایگزین ارائه شود.

## تست در صفحه

در Dashboard روی «تست اتصال» بزنید. پیام نتیجه به‌صورت چندخطی نمایش داده می‌شود و می‌توانید stage، آدرس، مدل، DNS، HTTP و نوع exception را ببینید.

در خود چت نیز خطای backend با همین جزئیات، به‌همراه `X-Request-ID`، داخل پیام خطا نمایش داده می‌شود.
