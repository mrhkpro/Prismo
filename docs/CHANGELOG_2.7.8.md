# v2.7.8 — Independent chat/embedding sources and Supabase auth recovery

## AI provider settings
- Chat source and embedding source now have independent toggles and selections: custom/OpenRouter chat can use the project's prepared embedding model, and prepared chat can use a separate embedding endpoint/model.
- Provider resolution passes the appropriate base URL, API key and selected embedding model to actual retrieval/indexing calls. Legacy rows preserve their former shared-mode behavior until migration 005 is applied.
- Chat model discovery skips embedding catalog calls and embedding probes; embedding discovery remains a separate action and checks vector dimensions against the configured store size. This reduces avoidable work while discovering large chat catalogs.
- Added SQLite startup migration and `supabase/migrations/005_independent_embedding_provider.sql` for persistent source choice on hosted PostgreSQL/Supabase.

## Authentication
- Removed new `email`/`google_sub` ORM-column requirements from the legacy users table, avoiding login failures when hosted databases still have their original schema.
- OAuth identity mappings remain in `oauth_identities` via migration 004; Google through Supabase Auth now redirects straight to Supabase's authorize endpoint and exchanges PKCE codes server-side, avoiding one server network round-trip.
- Common Supabase/Vercel public variable aliases are accepted. The application continues to use the legacy username/password login, its own session cookie, and server-only OAuth exchanges.
- Updated Google setup messaging and documentation. Real Google sign-in still requires the project's actual Google provider and redirect URLs to be configured; this run uses mocked callback tests, not live OAuth credentials.

## Frontend / cache
- Bumped application asset cache keys and dashboard badge to `2.7.8` so browsers pick up the repaired provider controls and OAuth messaging.

## Verification
- Full Python test suite: **238 passed** before final release-note updates.
- `compileall` passed for app/tests, and `node --check` passed for modified JavaScript.
- The test suite covers legacy username/password registration/login, Google/OAuth callback simulations, both provider-selection combinations, and saved settings. Live Supabase/Google and live model endpoints were not contacted by automated tests.
