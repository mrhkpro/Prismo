# Prismo v2.8.8 — Local + Supabase compatibility and consistent dashboard UX

## Fixed
- Local + Supabase startup now checks and repairs optional provider columns in `user_settings` before requests run; it skips all DDL when the existing schema is already current. This addresses `UndefinedColumn` for `separate_embedding_provider`, `embedding_api_key`, `embedding_base_url`, and `embedding_use_default_provider` when an existing Supabase schema is behind the current app.
- The repair is additive and idempotent: it adds missing columns, preserves all existing rows and credentials, and initializes `embedding_use_default_provider` from `use_default_provider` only when its value is NULL.
- The repair runs only when the app is launched locally against PostgreSQL/Supabase. SQLite's existing startup path is unchanged; Vercel retains its explicit migration workflow and performs no startup DDL.
- Admins now see a persistent security alert in the lower-left corner of the main dashboard while unresolved threat flags exist. The alert is populated only through the admin-only summary endpoint; regular users don't receive its details.
- Selecting the dashboard alert opens `admin.html#security`, and the admin page now honors that deep link.
- Applied the refreshed home-page style language to internal page headers, settings, tabs, panels, tables and stat cards. Frontend asset cache-busters are moved to v2.8.8.

## Preserved
- Existing Vercel RAG behavior, model and embedding-provider selection, widget features and database content.
- Local SQLite behavior and all existing SQL migrations.
- No new environment-variable names were added.

## Validation
- Added unit tests for missing-schema detection and idempotent column repair.
- Added a frontend contract test for the global admin-only alert and security deep-link.
- Verification: full suite **267 passed**; Python compile checks, JavaScript syntax checks, `git diff --check`, and the Local + Supabase schema-repair regression tests passed. No live Supabase credentials were available for an end-to-end remote database check.
- No live Supabase database was available for an end-to-end DB connection test in this environment.
