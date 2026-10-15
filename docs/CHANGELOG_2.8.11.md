# Prismo v2.8.11 — Multiple saved custom chat models

## Fix
Previously, `user_settings` stored only one custom chat provider and model. Saving another model replaced the active profile, so the previous model disappeared from Battle mode or could not use its own provider.

## Changes
- Added `saved_chat_models`, scoped by user and model ID, storing provider URL and API key server-side.
- Custom model save now registers the selected model profile without removing older profiles.
- Battle mode includes all saved custom models and uses each profile's own provider credentials.
- Added migration `supabase/migrations/010_saved_chat_models.sql`.

## Supabase action required
Run `010_saved_chat_models.sql` once in Supabase SQL Editor. SQLite creates the new table automatically. Existing tables and settings are not deleted or rewritten.

## Validation
Automated Python tests and JavaScript syntax check are run for this patch. No live OpenRouter request is made by the tests.
