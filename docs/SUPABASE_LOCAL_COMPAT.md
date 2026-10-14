# Local + Supabase schema compatibility

The application keeps the explicit SQL migration flow for Vercel, but a local Python process connected to Supabase performs a small idempotent compatibility check before serving requests.

## What it changes

On startup, when `DATABASE_URL` points to PostgreSQL and `VERCEL` is not set, Prismo inspects `user_settings` and adds only missing optional embedding-provider columns:
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
