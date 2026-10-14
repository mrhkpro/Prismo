# Prismo v2.8.6

## Fix

Fixed a Supabase/PostgreSQL startup/runtime failure:

```text
psycopg.errors.UndefinedColumn:
column user_settings.embedding_use_default_provider does not exist
```

## What changed

- Added `supabase/migrations/008_repair_embedding_provider_mode.sql`.
- The migration adds the missing column only if absent.
- Existing rows are backfilled from the current `use_default_provider` value, falling back to `TRUE` only if the old value is NULL.
- Existing non-NULL values are preserved; no tables, columns, users, documents, or chat records are deleted.
- Added a test that checks idempotent/non-destructive migration expectations.
- Documented how to apply and verify the migration in Supabase SQL Editor.

## Required action

Run the new migration once in the Supabase SQL Editor, then restart the local app. The app intentionally does not alter PostgreSQL schemas automatically on startup.
