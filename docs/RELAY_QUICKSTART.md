# حل مشکل Timeout سرویس AI از Vercel

خطای زیر:

`APITimeoutError` + `Request timed out` + `Base URL: https://racode-llm.partschool.ir/v1`

یعنی Vercel نام دامنه را resolve کرده، اما اتصال TCP/443 به سرویس مقصد برقرار نشده است. افزایش timeout در این حالت مشکل را حل نمی‌کند.

## راه‌حل پیشنهادی

Relay را روی همان سرور/شبکه‌ای اجرا کنید که به سرویس AI دسترسی مستقیم دارد و آن را با HTTPS در دسترس Vercel قرار دهید.

روی Vercel:

```env
AI_PROXY_BASE_URL=https://YOUR-RELAY-DOMAIN/v1
AI_PROXY_API_KEY=RELAY_API_KEY
```

روی Relay:

```env
UPSTREAM_BASE_URL=https://racode-llm.partschool.ir/v1
UPSTREAM_API_KEY=PROVIDER_API_KEY
RELAY_API_KEY=RELAY_API_KEY
RELAY_CONNECT_TIMEOUT=20
RELAY_READ_TIMEOUT=180
```

پس از تغییر Environment Variables، حتماً Redeploy کنید.

## چرا این روش؟

در مسیر مستقیم، Vercel باید خودش به `185.240.151.28:443` وصل شود و همین اتصال timeout می‌شود. با Relay، مسیر به شکل زیر است:

`Browser -> Vercel -> Relay -> AI provider`

در این حالت Relay می‌تواند در همان شبکه‌ای باشد که Provider در آن قابل دسترسی است.

## نکته

اگر سرور Provider متعلق به خودتان است، بهترین محل Relay همان سرور یا یک ماشین نزدیک به آن در همان شبکه است. در صورت استفاده از Cloudflare Tunnel یا Nginx، مقصد Relay را با HTTPS عمومی منتشر کنید.
