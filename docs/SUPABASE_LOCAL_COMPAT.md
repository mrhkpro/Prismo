# Local + Supabase schema compatibility

The application keeps the explicit SQL migration flow for Vercel, but a local Python process connected to Supabase performs a small idempotent compatibility check before serving requests.

## What it changes

On startup, when `DATABASE_URL` points to PostgreSQL and the real process environment is local (the Vercel flag is captured before loading `.env` files), Prismo inspects `user_settings` and adds only missing optional embedding-provider columns. If those columns already exist and the embedding selector has its expected default/NOT NULL constraint, no DDL or backfill runs:
- `separate_embedding_provider BOOLEAN NOT NULL DEFAULT FALSE`
- `embedding_api_key VARCHAR(255)`
- `embedding_base_url VARCHAR(255)`
- `embedding_use_default_provider BOOLEAN NOT NULL DEFAULT TRUE`

Existing rows and values are preserved. `embedding_use_default_provider` is initialized from the existing `use_default_provider` selection only for rows where the new field is NULL. No tables or user records are dropped.

This is intended to fix errors like:

`psycopg.errors.UndefinedColumn: column user_settings.separate_embedding_provider does not exist`

## If automatic repair cannot run

The PostgreSQL role in `DATABASE_URL` must have permission to alter `user_settings`. If permissions prevent startup repair, run `supabase/migrations/009_repair_all_embedding_provider_columns.sql` in Supabase SQL Editor as a database owner. If the `user_settings` table itself is missing, initialize the database from `supabase/migrations/001_initial_schema.sql` first, then run subsequent migrations in order.

No new environment variables are required. The repair is scoped to local + Supabase mode; Vercel's cold starts remain free of schema DDL.


## Pooler port selection (v2.8.9)

The shared Supavisor pooler supports Session mode at port 5432 and Transaction mode at port 6543. The current `DATABASE_URL` in the provided v2.8.1 and v2.8.8 archives is the same transaction-pooler host/port, and `app/database.py` had the same connector settings; therefore an error that times out on all resolved IPs at port 6543 is a TCP reachability problem, not a missing-column or ORM-schema error.

For a local, long-running Uvicorn process, Prismo now changes only the in-memory SQLAlchemy engine URL from 6543 to 5432 when all of these are true: process is local (not Vercel), host ends with `.pooler.supabase.com`, and configured port is 6543. Vercel stays on 6543. The `.env` file itself is not modified, no new variables are required, and username/password/database/query parameters are preserved. Direct database URLs and other providers are unaffected.
