# Quasar 2.7.1

## Performance
- Supabase/PostgreSQL startup no longer runs `create_all`, schema inspection, `ALTER TABLE`, or admin seeding.
- PostgreSQL connection pool reduced to a small warm pool with short connection timeout and recycling.
- Dashboard summary counters are collected with one SQL round-trip.
- Dashboard boot opens only the remembered section instead of loading overview/settings together.
- Local launcher disables Uvicorn access-log spam to reduce CPU and disk I/O during development.

## Stability
- Settings language switching pauses the translation observer while translating and never re-translates an entire parent subtree for a single text mutation.
- Added regression coverage for Supabase startup and the language-switch feedback-loop bug.
- Asset cache-buster moved to `2.7.1`.

## Database
- No Supabase schema migration is required for these changes.
- Existing Supabase tables/columns are treated as authoritative and untouched during application startup.
