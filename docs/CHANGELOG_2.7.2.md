# v2.7.2 — Global English/RTL-LTR, Admin & Supabase Compatibility

## Highlights
- Unified Persian/English locale propagation across dashboard, admin, Test Lab, widget, setup, API errors and built-in prompts.
- English mode switches the document to `lang="en"` and `dir="ltr"`; dynamic nodes added later are translated without recursive MutationObserver loops.
- Built-in system prompt, widget title and widget welcome defaults are localized consistently in API responses and RAG execution.
- Admin and settings routes no longer depend on optional/new `UserSettings` columns, preserving compatibility with older Supabase schemas.
- Supabase/PostgreSQL startup remains schema-free: no `create_all`, ALTER, inspection or admin seeding during startup.
- Legacy and current `user_settings` schemas are handled by a narrow compatibility layer without database migration.
- Settings center remains organized into Appearance, Chat, Workspace and Account tabs, with themes, streaming, accessibility and keyboard shortcuts.
- Widget public configuration is localized through `X-QZ-Language`.

## Verification
- `197 passed` in the full pytest suite.
- Frontend JavaScript syntax checks passed for the main settings/dashboard/widget/API bundles.
- Browser-isolated DOM regression test: English mode produced `0` Persian characters in translated UI, dynamic nodes were translated, and returning to Persian restored RTL/Persian UI.
- Local HTTP smoke: health, login, auth/me, settings and admin stats returned 200; public widget configuration returned an English welcome message.

## Supabase note
The code path is designed to avoid startup schema mutations and tolerate older settings schemas. This environment does not contain the `psycopg` package and cannot reach the user's external Supabase instance, so a live remote Supabase connection cannot be independently verified here. The relevant startup/compatibility regression tests are included in the suite.
