# Vercel provider relay

## Why
If Vercel resolves the AI hostname but TCP/443 times out, changing Python timeouts cannot create a network path that the destination firewall/router does not allow. This project now supports an OpenAI-compatible relay via `AI_PROXY_BASE_URL`.

## Recommended deployment
Run the relay on the same server/network as the AI provider, or on a host that can reach `UPSTREAM_BASE_URL` reliably. Expose the relay publicly through HTTPS (Nginx, Cloudflare Tunnel, or another reverse proxy).

## Relay environment
```env
UPSTREAM_BASE_URL=https://racode-llm.partschool.ir/v1
UPSTREAM_API_KEY=...
RELAY_API_KEY=...
RELAY_CONNECT_TIMEOUT=20
RELAY_READ_TIMEOUT=180
```

## Vercel environment
```env
AI_PROXY_BASE_URL=https://YOUR-RELAY-DOMAIN/v1
AI_PROXY_API_KEY=the-same-value-as-RELAY_API_KEY
```

Redeploy after changing environment variables. The app will use the relay only for the default provider; custom user providers continue to use their own Base URL directly.

## Important
Do not set `AI_PROXY_BASE_URL` to the same `racode-llm.partschool.ir` URL; that does not change the network route.
