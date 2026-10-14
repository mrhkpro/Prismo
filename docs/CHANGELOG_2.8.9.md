# Prismo v2.8.9

## Fixed

- Local + Supabase now uses the shared Supavisor Session Pooler on port 5432 when the configured URL uses the shared Transaction Pooler on port 6543.
- Vercel keeps the configured deployment pooler port (normally 6543). Local SQLite and direct PostgreSQL URLs are unchanged.
- Kept the user's `DATABASE_URL` intact; the port adjustment exists only in the SQLAlchemy engine URL.

## Why

The connection exception occurred before PostgreSQL authentication: all resolved IPs for `aws-0-ap-northeast-2.pooler.supabase.com:6543` timed out. Comparing the private local `.env` from v2.8.1 with the current v2.8.8 worktree found the same `DATABASE_URL` (compared without printing any credentials), and `app/database.py`'s connector configuration had not changed since v2.8.1. Local sessions now use the documented Session Pooler port.

## Validation

- Five focused URL-resolution tests cover local Session Pooler switching, Vercel preservation, explicit Session URLs, direct Supabase URLs and unrelated PostgreSQL providers.
- Full suite: 272 passed.
- Live connectivity from the user's Windows host was not available during this build; if port 5432 also times out, inspect local VPN/firewall and Supabase project availability.
