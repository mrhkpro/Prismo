# Prismo v2.8.14 — Saved chat model profiles

## Fixed
- Save the selected custom chat model profile before reporting provider settings as successfully saved, so a failed profile write cannot leave a misleading success message.
- Return a clear setup instruction when `saved_chat_models` is missing in a PostgreSQL/Supabase deployment instead of the generic temporary-service error.
- Add an idempotent Supabase repair migration: `supabase/migrations/012_repair_saved_chat_models.sql`.

## UI
- Redesigned the saved chat models area with a model count, provider endpoint cards, a privacy note, a useful empty state, and retry/error states.
- The list never returns or renders API keys.
- Updated only the dashboard stylesheet and script cache-busting values for this scoped change.

## Validation
- Added tests for saving/updating model profiles, keeping API keys out of responses, handling a missing saved-model table, and validating the repair migration.
