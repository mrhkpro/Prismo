# معماری درخواست چت | Chat Request Flow

این سند جریان درخواست‌های گفتگو را توضیح می‌دهد و مکمل [RAG.md](RAG.md) است.

## 1. مسیر چت عادی در آزمایشگاه

```text
Browser
  → POST /api/playground/chat
  → authenticate user and resolve owner-scoped session
  → look for eligible same-session recall / answer-cache hit
  → resolve chat + embedding provider settings
  → embed question
  → search owner's chunks
  → apply similarity threshold and top-k
  → assemble system prompt + retrieved context + bounded history
  → chat completion (when retrieval path requires it)
  → save the user/assistant turn
  → return response, sources, model, and session ID
```

`app/routers/playground.py` هماهنگ‌کننده‌ی endpoint است؛ منطق مشترک RAG در `app/services/rag_pipeline.py` قرار دارد. `app/services/answer_cache.py` امکان بازیابی پاسخ قبلی را قبل از تماس با provider بررسی می‌کند.

## 2. استریم چت

مسیر `POST /api/playground/chat/stream` از Server-Sent Events (SSE) استفاده می‌کند. رویدادهای اصلی:

- `meta`: شناسه‌ی نشست، مدل و منابع بازیابی‌شده.
- `delta`: بخش بعدی متن پاسخ.
- `done`: پایان موفق جریان.
- `error`: خطایی که در حین استریم قابل بازیابی نبود.

پیش از آماده شدن پاسخ کامل، سرور یک رویداد آماده‌سازی می‌فرستد تا اتصال باز بماند. generator از نشست‌های دیتابیس کوتاه‌مدت خودش استفاده می‌کند تا برای تماس طولانی مدل، connection غیرضروری باز نماند. متن جمع‌آوری‌شده پس از استریم برای حفظ تاریخچه ذخیره می‌شود.

## 3. جریان ویجت عمومی

ویجت درخواست را به `/public/widget/{widget_id}/chat` یا `/chat/stream` ارسال می‌کند. مالک بر اساس شناسه‌ی ویجت مشخص می‌شود؛ تنظیمات provider و دانشنامه‌ی مالک استفاده می‌شود و فعال بودن حساب بررسی می‌گردد. بازدیدکننده‌ی خارجی به حساب کاربر داشبورد وارد نمی‌شود.

## 4. Battle یکسان با RAG نیست

`/api/playground/battle` و `/battle/stream` یک پرامپت را به دو مدل انتخاب‌شده ارسال می‌کنند تا پاسخ و زمان هرکدام جداگانه مقایسه شود. این مسیر برای مقایسه‌ی مدل‌هاست و به خودی خود جست‌وجوی دانشنامه را انجام نمی‌دهد.

## 5. حافظه و تکرار سؤال

- پیام‌ها در `chat_messages` ذخیره می‌شوند.
- تاریخچه‌ی ورودی مدل محدود است و تمام مکالمه‌ی قدیمی بدون سقف ارسال نمی‌شود.
- `find_historical_answer` می‌تواند سؤال تکراری یا بعضی paraphraseهای قابل‌اطمینان را در همان نشست تشخیص دهد.
- answer cache فقط در شرایط مالک/تنظیمات/دانشنامه‌ی سازگار پاسخ قبلی را بازاستفاده می‌کند.

این کار به معنای تغییر وزن‌های مدل یا «آموزش حافظه‌ی دائمی به مدل» نیست؛ حافظه در لایه‌ی برنامه و دیتابیس مدیریت می‌شود.

## 6. عیب‌یابی عملکرد

لاگ‌های `rag_chat` زمان Embedding، retrieval، زمان تولید مدل، زمان اولین token و زمان کل را تا جایی که مسیر مربوط فراهم کند ثبت می‌کنند. `X-Request-ID` درخواست API را به لاگ‌های درخواست وصل می‌کند.

- اگر زمان Embedding زیاد است، اتصال/provider مدل embedding و شبکه را بررسی کنید.
- اگر retrieval کند است، اندازه‌ی دانشنامه، cache بردار SQLite و اجرای pgvector را بررسی کنید.
- اگر اولین token دیر می‌رسد ولی retrieval سریع است، علت محتمل در provider مدل چت یا شبکه‌ی آن است.
- اگر سؤال تکراری سریع است، بررسی کنید conversation recall یا answer cache پاسخ را بازگردانده باشد.
