# Prismo v2.8.7 — Supabase user_settings repair

## Root cause

The application's SQLAlchemy `UserSettings` model contains optional provider columns added in later releases. The affected Supabase database had not applied all of those migrations. Although the code has a compatibility layer for settings reads, the development-only admin bootstrap accessed `admin.settings` as an ORM relationship. That generated a `SELECT` for every mapped column and failed as soon as any optional column was missing.

## Fixes

- The admin bootstrap now uses `user_settings_compat.ensure_settings()` instead of touching the full ORM relationship, so bootstrap remains compatible with legacy schemas.
- Migration `009_repair_all_embedding_provider_columns.sql` adds the four provider columns with `IF NOT EXISTS`, backfills the embedding-provider mode from the existing chat-provider mode, and sets the default/non-null constraints.
- The migration does not drop tables, drop columns, or delete user data.

## Apply to Supabase

Run `supabase/migrations/009_repair_all_embedding_provider_columns.sql` once in the Supabase SQL Editor. It is safe to run repeatedly. For full independent chat/embedding settings, this SQL migration is still required even though the legacy-compatible bootstrap no longer crashes before it is applied.

## Verification

- Added regression checks for all four provider columns and non-destructive DDL.
- Added a bootstrap compatibility guard to prevent reintroducing direct ORM relationship loading.
- The complete automated suite is run for this release; live Supabase database verification requires the user's database credentials and is not claimed here.
