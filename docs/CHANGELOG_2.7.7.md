# v2.7.7 — Google OAuth, theme repair and complete OpenRouter catalogue

## Authentication
- Added a server-side Google OAuth Authorization Code + PKCE flow, ID-token verification, state/nonce validation, account linking/creation, HttpOnly cookie session, logout cookie clearing and callback error handling.
- Preserved the existing email/password login and local JWT-compatible API behavior.
- Added the PostgreSQL migration `supabase/migrations/004_google_oauth_identity.sql` and Google Cloud/Supabase setup steps to the README.

## Appearance
- Unified theme selection around the `QZTheme` API and persisted theme key so settings cards, page root and initial page paint agree.
- Refined and tested Nord, Amber and Rose presets; they remain selectable from Settings → Appearance & Language.
- Bumped frontend asset cache-busters and dashboard version badge to `2.7.7`.

## OpenRouter
- Added direct retrieval of the OpenRouter `/api/v1/models` catalogue while keeping provider-supplied names, modalities, context length and prompt/completion prices.
- Chat models are listed inclusively from modality metadata rather than disappearing just because an inference probe is slow or unsupported. The selector distinguishes free, paid and unknown-price entries.
- Embedding catalogues are probed independently; a model is offered as compatible only when the real test vector matches the configured database embedding dimension.
- A separate embedding-provider catalogue outage no longer hides an otherwise available OpenRouter chat catalogue. Unsaved form credentials are honored by read-only discovery, without writing them to user settings.
- Added mocked contract tests for complete model listing, price classification, modality exclusion and embedding-dimension validation.

## Verification
- Full Python test suite: **229 passed**.
- JavaScript syntax checks passed for the modified dashboard, settings, theme, auth and API scripts.
- Google OAuth tests use mocked Google token exchange/profile verification; real Google sign-in still requires valid Cloud OAuth credentials.
- A live OpenRouter catalog request could not be completed from the current execution environment (outbound request unavailable); catalog and response handling were tested with mocked responses.
