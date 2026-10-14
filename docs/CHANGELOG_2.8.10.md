# Prismo v2.8.10 — Local + Supabase backend restored

## What changed

- Restored the v2.8.1 PostgreSQL/SQLAlchemy engine pool settings and startup lifecycle.
- Local Uvicorn uses the Supabase Session Pooler on port 5432 when `DATABASE_URL` was copied from the transaction pooler on 6543; Vercel keeps 6543. The original `DATABASE_URL` and `.env` are unchanged.
- Removed automatic PostgreSQL schema inspection/`ALTER TABLE` from Local+Supabase startup. Supabase schema remains managed explicitly with SQL migrations; this matches the simple v2.8.1 startup behavior.
- Kept SQLite-only `create_all` and legacy SQLite column upgrades.
- Tightened detection of the Vercel environment so `VERCEL=0`/`false` does not count as a deployed Vercel process, and local `.env.local` values do not masquerade as platform-provided environment variables.
- No UI, provider selection, RAG, widget, Google OAuth, or admin alert behavior was intentionally changed.

## Supabase requirements

The Supabase schema must already contain the columns used by the current application. The provided database inventory includes all four embedding-provider columns in `public.user_settings`; no new migration is needed solely for this change if that is the live schema.

## Validation

Automated tests cover local port selection, Vercel port preservation, startup avoiding PostgreSQL schema DDL, and existing SQLite upgrades. Actual connectivity to the user's Supabase server must be verified on their Windows network; a successful TCP probe alone does not prove database authentication or TLS works.
