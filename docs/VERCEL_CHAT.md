# Vercel Chat Performance Runbook

این پروژه برای Vercel طوری تنظیم شده که تماس‌های AI در محیط Serverless بی‌جهت با retryهای طولانی کش پیدا نکنند و مدل انتخاب‌شده واقعاً در همان درخواست استفاده شود.

## تنظیمات AI

Environment Variables زیر در Production و Preview قابل استفاده‌اند:

```env
AI_REQUEST_TIMEOUT_SECONDS=30
AI_CONNECT_TIMEOUT_SECONDS=6
AI_MAX_RETRIES=0
AI_MAX_OUTPUT_TOKENS=900
```

`AI_MAX_RETRIES=0` عمداً انتخاب شده تا زنجیره‌ی Embedding + Chat باعث چند برابر شدن زمان یک invocation نشود.

## بعد از تغییر مدل

از بخش «اتصال مدل هوش مصنوعی» مدل چت را انتخاب و ذخیره کنید. رابط تست RAG مقدار `chat_model` ذخیره‌شده را به‌صورت صریح در هر درخواست می‌فرستد و API نیز همان مدل را به کلاینت AI تحویل می‌دهد.

پاسخ `/api/playground/chat` علاوه بر متن و منابع، فیلد `model` را برمی‌گرداند تا مدل واقعاً استفاده‌شده قابل مشاهده و قابل تست باشد.

## تشخیص کندی در Vercel

در Runtime Logs برای هر چت خطی با این قالب ثبت می‌شود:

```text
rag_chat owner_id=... model=... embedding_ms=... search_ms=... llm_ms=... total_ms=... matches=...
```

با این اعداد می‌توان مشخص کرد کندی از سرویس embedding، جست‌وجوی Postgres/pgvector یا خود مدل چت است.

## خطای «پاسخ سرور بیش از حد طول کشید»

رابط کاربری برای درخواست گفت‌وگوی RAG مهلت ۹۰ ثانیه‌ای دارد؛ timeout عمومی API روی ۳۰ ثانیه است و مسیر چت صریحاً زمان بیشتری می‌گیرد. اگر invocation هنوز بیشتر طول بکشد، Runtime Logs را با `embedding_ms` و `llm_ms` بررسی کنید.

## Deploy ایمن

در این اصلاحات routing، dependencyهای Vercel و entrypoint پروژه تغییر نکرده‌اند. پس از تغییر Environment Variables فقط یک Redeploy لازم است.

در زمان بررسی، اگر پروژه روی Fluid Compute فعال باشد، Vercel برای Python Functions امکان اجرای طولانی‌تر و streaming را فراهم می‌کند؛ محدودیت واقعی deployment را از Settings/Functions پروژه خود بررسی کنید.
