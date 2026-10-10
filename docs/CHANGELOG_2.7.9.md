# v2.7.9 — Remove Google sign-in

## Authentication
- Removed the Google sign-in button and its styles from the login/registration page.
- Removed frontend OAuth callback handling, error translations and redirect logic. The page retains its quick, existing username/password session flow without an OAuth-related extra request.
- Removed `/api/auth/google/start`, `/api/auth/google/callback` and `/api/auth/google/supabase-callback` endpoints and the associated authorization-code, PKCE, cookie, token-exchange, identity-linking and profile-verification code.
- Removed Google-only environment variables, Supabase Auth OAuth variables, the `OAuthIdentity` ORM model and the `google-auth` Python dependency.
- Kept username/password register, login, `/me` and logout endpoints.
- Added `supabase/migrations/006_remove_oauth_identities.sql`. It drops only the legacy OAuth mapping table and preserves users/application data. Run it manually on Supabase/PostgreSQL if that table exists.

## AI provider and app behaviour
- No chat or embedding provider code was changed in this release.
- `APP_PUBLIC_URL` remains because it is used for AI-provider attribution headers; it is no longer part of authentication setup.
- Bumped the login page asset cache keys to `2.7.9` for the changed CSS and authentication script.

## Verification
- The new regression tests assert the Google endpoints are no longer registered, the login page and JavaScript contain no Google sign-in controls, and the standard email/username-password routes remain registered.
- The full automated suite and frontend syntax checks are run for this release; results are recorded in the final response.
