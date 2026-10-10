# Prismo v2.8.1 — Local admin login hotfix

## Fixed
- Restored the user's ignored local `.env` into the complete release archive so the packaged build uses the configured admin credentials and database profile instead of silently creating a placeholder environment.
- Fixed the first-run setup mismatch: `.env.example` now agrees with the fallback password reported by the setup script, and setup points users to the actual `ADMIN_PASSWORD` value in `.env`.
- Fixed local bootstrap for an existing SQLite database: the user named by `ADMIN_USERNAME` is now promoted/activated and its password hash is synchronized with `ADMIN_PASSWORD`, so stale hashes do not reject the configured password.
- Added a development-only opt-in (`PRISMO_BOOTSTRAP_ADMIN_ON_STARTUP=true`) to synchronize the configured admin for a local app that connects to Supabase. It is disabled by default and does not run in production.

## Validation
- Full automated suite: 241 passed.
- Local SQLite application smoke test: login returned HTTP 200 and an access token using the configured admin credentials.
- `git diff --check`: passed.
- Live Supabase connectivity was not tested from this environment.

## Important
- The complete release archive includes the `.env` from the user's supplied project and excludes it from Git history. Keep that archive private; do not commit or share `.env`.
