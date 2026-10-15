## v2.8.15 — Saved embedding profiles and Supabase connection resilience

- Fixed explicit saving of custom embedding model profiles; added migration 013 to repair/create both saved-model registries.
- Saved-model lists are hidden when the corresponding ready/default provider mode is selected.
- Improved SQLAlchemy pool health checks and reconnect behavior for local Supabase connections.

## 2.8.13
- Added session-scoped conversation memory recall before provider resolution, embeddings, semantic retrieval, and chat completion. Exact repeats, high-confidence phrasing variants, and short unambiguous follow-ups (for example, “اسمش چی بود؟”) can reuse a prior answer after intervening turns.
- Excluded flagged user messages and kept recall bounded to recent stored turns; different questions about the same entity are not treated as duplicates.
- Added regression coverage proving history recall avoids new provider, embedding, and completion calls.

## 2.8.12
- Added expandable lists of each user's saved chat and embedding models in the AI model settings section.
- Persisted custom embedding model profiles separately; API keys are never shown in the saved model lists.
- Clarified that built-in ready models require a local installation, with or without Supabase, and do not work from the hosted site.

## v2.8.11 — Persist multiple custom chat models per user

- Added per-user saved chat model profiles so adding a second external model no longer overwrites the first model's provider credentials.
- Saving a custom chat model registers/updates its model ID, base URL and API key server-side; API keys are never returned to the browser.
- Battle mode now resolves each saved model against its own provider profile, allowing models such as Cohere and Gamma to be compared together.
- Added Supabase migration `010_saved_chat_models.sql`. Existing settings and chat flows are otherwise unchanged.

# Changelog

## v2.8.14 — Saved chat model profiles

- Redesigned the saved chat model list and added explicit loading, empty, and database-migration error states.
- Saves a chat model profile before showing a success toast; failures now explain how to repair the missing Supabase table.
- Added idempotent migration `012_repair_saved_chat_models.sql`.


## v2.8.10 — Restore Local + Supabase backend behavior from v2.8.1

- Restored the v2.8.1 startup contract for PostgreSQL/Supabase: no schema inspection, automatic `ALTER TABLE`, or table creation during Local+Supabase startup. Explicit Supabase migrations remain the schema-management path.
- Restored the v2.8.1 SQLAlchemy engine/pool/session behavior, with one network-specific adjustment: local Uvicorn uses Supabase Session Pooler port 5432 when the configured pooler URL uses transaction port 6543. Vercel keeps port 6543.
- Restored `app/services/user_settings_compat.py` to its v2.8.1 form; the later `ensure_local_supabase_provider_schema` startup repair helper is removed.
- Made Vercel runtime detection require a truthy `VERCEL` flag plus a platform marker (`VERCEL_URL` or `VERCEL_ENV`) captured before dotenv loading, so a local `.env.local` cannot route Uvicorn to serverless settings.
- No UI, Google OAuth, RAG, caching, threat alerts, provider settings, or widget behavior was intentionally changed.
- Validation: 273 automated tests passed. Live Supabase database authentication could not be tested from this environment.

## v2.8.9 — Local Supabase session-pooler connectivity

- For local Uvicorn only, automatically use the Supabase shared Session Pooler port 5432 when the configured URL targets the shared Transaction Pooler on port 6543.
- Keep Vercel on its configured transaction pooler (6543); direct PostgreSQL URLs, local SQLite and non-Supabase PostgreSQL URLs are not rewritten.
- Preserve URL credentials and query parameters; no new environment variables are required.
- Add regression tests for local, Vercel, explicit-session, direct-DB and unrelated PostgreSQL URLs.
- Validation: 272 automated tests passed. The real Supabase database could not be reached from the build environment, so local connectivity should be confirmed from the user's Windows machine.

## v2.8.8 — Local + Supabase compatibility and consistent dashboard UX

- Auto-repair missing provider columns on local + Supabase startup only.
- Add persistent admin-only threat alert to the dashboard and deep-link it to security review.
- Refresh internal page headers, panels, stat cards and settings surfaces.
- Verification: 267 automated tests passed, including Local + Supabase schema compatibility and global admin alert contracts.

## v2.8.7 — Supabase provider-schema compatibility

- Added idempotent migration `009_repair_all_embedding_provider_columns.sql` to repair all four optional provider columns together: `separate_embedding_provider`, `embedding_api_key`, `embedding_base_url`, and `embedding_use_default_provider`.
- Updated the opt-in development admin bootstrap to use `user_settings_compat`, avoiding ORM relationship loads across columns that may be missing in older Supabase schemas.
- Added regression tests for migration safety and bootstrap compatibility with legacy settings schemas.

## v2.8.5 — Secure hosted OAuth, answer caching, and repeated-risk escalation

See [`CHANGELOG_2.8.5.md`](CHANGELOG_2.8.5.md) for the release summary.

# Changelog

## v2.8.4 — Vercel response reliability, Google Login and security monitoring

- Based on the v2.8.1 project tree and Git history; selectively brought over the bounded JSON RAG request behavior that worked in the v2.8.3 Vercel build while keeping local streaming intact.
- Added structured OpenAI-compatible message-content extraction, one retry for an empty model answer, and a final RAG guard that refuses blank assistant turns.
- Restored the active Google sign-in flow from `final-project-feat-my-work` through Supabase Auth, including the login button, callback page and a server-side token validation/exchange endpoint. The username/password flow remains available.
- Added persistent, admin-visible alerts for suspected system-prompt extraction, API-key/credential disclosure, prompt injection and destructive/system-bypass requests from Test Lab or public widget inputs. A suspicious attempt is recorded before model execution so it remains visible even if the provider fails; the admin banner covers critical/high items and the card displays the actual message plus detection reason.
- Refreshed static asset cache versions and enhanced the signed-in dashboard home panel with a themed hero illustration, status/stat cards, feature chips and responsive quick actions. Original overview statistic IDs and navigation targets are preserved.
- Verification: 252 automated tests passed; Python compile, JavaScript syntax, Git diff and desktop/mobile layout checks passed. Live Google/Supabase OAuth and OpenRouter API calls still require the target project's real provider configuration and network access.

## v2.8.1 — Local admin login hotfix

- Fixed the mismatch between the setup script's printed admin password and `.env.example`.
- Local bootstrap now synchronizes the configured admin password for an existing SQLite account, instead of only promoting the role.
- A local development process may explicitly enable bootstrap synchronization when it connects to Supabase; default and production startup behavior remains unchanged.
- Added an explicit, opt-in development-only bootstrap for local instances that use Supabase; it is disabled by default and never enabled in production.
- Added regression tests for existing admin passwords and fresh bootstrap.

## 2.8.0 — AI connection UX

- Rebuilt the AI provider settings flow into ordered steps: chat source/model, independent embedding source/model, then save/test at the bottom.
- Consolidated save/test actions into a single final action area; only actions for the active chat source are shown.
- Improved independent chat/embedding cards, contextual hints, accessible pressed states, and responsive mobile layout.
- Bumped front-end asset cache versions to 2.8.0.

# v2.7.9 — Remove Google sign-in

Google OAuth UI, JavaScript handlers, API endpoints, server configuration and the Google verification dependency have been removed. Username/password registration, login and logout remain the supported application auth flow. Migration `006_remove_oauth_identities.sql` removes only the obsolete OAuth identity-mapping table on Supabase/PostgreSQL.

See `CHANGELOG_2.7.9.md` for details and verification.

# v2.7.8 — Independent chat/embedding sources and Supabase auth recovery

See `CHANGELOG_2.7.8.md` for the complete release notes.

# v2.7.7 — Google OAuth, theme repair and complete OpenRouter catalogue

See `CHANGELOG_2.7.7.md` for the complete release notes.

# v2.7.3 — English UI, Streaming Model Battle & Knowledge Progress

See `CHANGELOG_2.7.3.md` for the complete release notes.

# Changelog

## v2.7.2 — Global i18n, Admin & Supabase Compatibility

See `CHANGELOG_2.7.2.md` for the complete release notes.

# Changelog

## v2.7.0 — 2026-10-08 — Settings center, multi-theme UI, provider capability detection, widget resilience and request speed

### UI / Settings
- Replaced the dashboard top Light Mode button with a centralized **Settings** section.
- Added Persian/English switching with immediate RTL/LTR layout and dynamic translation of newly-rendered UI.
- Added seven themes: Light, Dark, Ocean, Forest, Sunset, Lavender and Mono.
- Added response streaming on/off, auto-scroll, response sound, reduced motion, high contrast, compact sidebar, remembered last view and reset-to-default settings.
- Moved account details and logout into Settings while keeping the user identity in the bottom sidebar.

### AI provider
- Custom provider can now use one shared API key for chat + embeddings or separate credentials.
- Model discovery now verifies chat and embedding capability with bounded probes instead of trusting model names alone.
- Only verified chat models are offered to chat and verified embedding models to embeddings; the UI also reports models verified for both roles.

### Performance / Widget
- Added short TTL caching for hot read-only API endpoints plus in-flight GET de-duplication and write-triggered invalidation.
- Dashboard overview loads summary/settings in parallel.
- Public widget config no longer removes the widget on bootstrap failure; a readable error and retry action remain visible.
- Widget config now handles non-JSON error bodies and keeps the panel usable during recovery.
- Public widget owner lookup uses eager loading to avoid an extra query.

### Compatibility / Migration
- Local SQLite automatically adds the new provider credential columns for existing databases.
- Added `supabase/migrations/003_dual_provider_credentials.sql`.
- Asset/embed version bumped to `2.7.0`.

### Tests
- Full suite: **188 passed**.
- JavaScript syntax check passed for dashboard, settings, theme, API and widget scripts.
- HTTP smoke test passed for health, dashboard/static assets, registration, auth/me, settings, dashboard summary and public widget config using a local SQLite instance.


## v2.6.5 — 2026-10-07 — Save no longer hangs on PostgreSQL, top notification bar, streaming fix

> Entries for 2.6.0–2.6.4 were never written; this file resumes from the 2.5.0 notes below.

### Fixed
- **"سرویس موقتاً در دسترس نیست" on every save / widget load (PostgreSQL / Supabase).** Creating the `widget_extras` column ran `ALTER TABLE` on a *second* connection while the request's own transaction still held a lock on `user_settings`, so the request waited for itself until the platform cut it off. The existence check now reads the catalog (no lock) and, only when the column is really missing, the DDL runs on the request's own connection with `lock_timeout = 5s`. The public widget config endpoint had the same hang and is fixed by the same change. SQLite never showed it, which is why the test suite stayed green.
- **Streaming chat (playground and public widget).** The SSE generator kept using the request's database session and ORM objects after FastAPI had closed it (`DetachedInstanceError`, swallowed into an empty error event). It now opens short-lived sessions of its own, releases the connection before the long model call, and saves the turn with a separate session. The playground endpoint also stopped running retrieval (embedding) twice per message.

### UI
- Notifications are a bar at the **top** of the page (centered, above the topbar) with an icon, a close button, up to three at a time and a longer lifetime for errors; reduced-motion aware.
- The text next to the widget "save" button was removed. Unsaved changes are shown as a dot on the button; the migration-002 hint is a notification.

### Chore / tests
- Asset versions `2.6.4` → `2.6.5` (assets are cached as immutable).
- `tests/test_widget_extras_ddl.py` (DDL must not open a second connection; no-op when the column exists) and a toast/save-button contract in `tests/test_frontend_contracts.py`. Verified separately against a real PostgreSQL + pgvector instance: save, widget config, documents, chat, both streams, admin.

## v2.5.0 — 2026-10-05 — Gentelella-style UI, streaming, file import, widget pet, admin alerts, speed

### UI / UX
- New application shell inspired by Gentelella: sticky topbar with breadcrumb, collapsible icon-only sidebar on desktop (remembered), off-canvas drawer on mobile, card headers/toolbars/segmented controls. Home keeps its layout.
- AI connection page decluttered: *Connection* and *Model comparison* tabs, a segmented switch between the free models and a custom API, one panel instead of five boxes. All element ids are unchanged.

### Chat
- Replies stream chunk by chunk (SSE) in the lab chat and the public widget: `POST /api/playground/chat/stream` and `POST /public/widget/{id}/chat/stream` (events `meta`, `delta`, `done`, `error`). Blinking caret, stop button, partial replies are saved. If streaming is unavailable (404/405/415/501 or an old browser) the UI falls back to the one-shot endpoints automatically.

### Knowledge base
- Import PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), OpenDocument (.odt/.ods/.odp), EPUB, HTML, RTF, CSV, TSV, JSON, XML, YAML, Markdown, TXT, SRT/VTT and more. Text is extracted **in the browser** (no new Python dependency, no 4.5 MB request-body problem on Vercel); pdf.js is vendored and loaded only when a PDF is chosen. Drag-and-drop zone, multi-file import with per-file progress, automatic splitting of very long texts, Windows-1256 fallback for old Persian text files. Scanned (image-only) PDFs and legacy `.doc/.xls/.ppt` get a clear error.

### Widget
- Pixel pet (dog, cat or raccoon) in a chosen color walks along the top of the open widget, stops after a while, gives hearts when clicked; toggle on/off. It sits on the launcher while the panel is closed.
- Quick-reply chips (up to 4), optional teaser bubble, left/right placement, auto/light/dark embed snippet, live preview of unsaved changes, unsaved-changes hint, color swatches.
- Settings are stored in a new nullable column `user_settings.widget_extras` (JSON text). It is created automatically on first save (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) and read with raw SQL inside a savepoint, so a missing column can never break login, chat or any other query. `supabase/migrations/002_widget_extras.sql` is provided for manual runs.

### Admin security
- Scanner v2 with severity and category: system-prompt extraction (English and Persian) is *critical*; instruction override and jailbreak are *high*; knowledge-base dumping is *medium*. Reasons store only rule codes, severity is derived at read time (no schema change).
- Live monitoring: red banner on every admin page for unresolved critical alerts, pulsing sidebar badge, toast for new critical alerts (summary polled every 30 s while the tab is visible), `GET /api/admin/security/summary`, enriched `GET /api/admin/security/flags` (owner, organization, source, visitor, severity filter), alert cards with view-conversation / block-user / mark-reviewed actions.

### Performance and interaction
- Skeleton boxes while data loads (overview, sidebar identity, documents, widget preview, admin stats/users/conversations/alerts).
- extract.js and pets.js are loaded on demand; concurrent identical GET requests share one network call; fonts no longer block rendering; the background glow no longer repaints on scroll.
- `/assets/*?v=…` responses are sent with `Cache-Control: public, max-age=31536000, immutable`. Every changed asset therefore ships under a new `?v=` number (now `2.5.0`).
- Double click on edit/delete/inspect/view/block/impersonate runs once and the next click works normally; a second click on the same control within 350 ms is ignored.

### Tests
- `tests/test_full_platform_flow.py` grew to cover streaming, widget extras, security severity/summary and cache headers. `tests/test_prompt_security.py` and `tests/test_theme_contracts.py` were extended (scanner phrases and false positives, sprite parity, deferred scripts, non-blocking fonts).

## v2.4.0 — 2026-10-04 — Violet night / gold day redesign

### Changed
- Full UI/UX redesign for both themes. Dark theme: deep violet / indigo / fuchsia on near-black with ambient glow. Light theme: warm white with gold and yellow accents. All colors now come from design tokens (`:root` and `:root[data-theme="light"]`), so there is a single place to tweak a palette.
- Removed the v2.3 flat override block (and its `!important` rules); components are token-driven.
- Embedded widget got matching dark/light palettes. The text color on the widget accent is now computed from the chosen color (a yellow widget gets dark text), and the header gradient derives from the chosen color instead of a hard-coded purple.
- Dashboard widget preview follows the current site theme and re-renders when the theme is toggled.
- Asset versions bumped to `?v=2.4.0` on every page and in the embed snippet (`/api/widget/embed-code` was still emitting `widget.js?v=2.2.0`).

### Fixed
- White text on the old dark-theme gradient measured below WCAG AA; gradient stops darkened (now 4.7:1 or better).
- Widget preview iframe no longer paints an opaque white canvas in dark mode.
- Persian text inside mono-font stat cards falls back to Vazirmatn.
- Public widget chat can no longer continue a playground session id, and playground chat can no longer continue a visitor widget session id (they were only filtered by owner).
- Clearing the whole knowledge base deletes chunks before documents, so it is safe on databases that enforce foreign keys without `ON DELETE CASCADE`.

### Tests
- `tests/test_full_platform_flow.py`: 46 end-to-end API scenarios (auth, settings and custom provider lifecycle, widget color/title/embed code, knowledge CRUD and reindex, playground chat/search/battle/sessions, public widget limits, dashboard counters, admin stats/user detail/reading one person's messages/flags/block/roles/impersonation). AI calls are mocked; DB is in-memory SQLite.
- `tests/test_theme_contracts.py`: dependency-free checks for token parity, hue ranges, WCAG contrast, no hard-coded brand colors, shared asset versions and widget palettes.

## v2.2.2 — Provider diagnostics & hosted AI error clarity

- Added detailed provider diagnostics for DNS, TCP/TLS, HTTP, authentication, rate-limit, model and timeout failures.
- Chat/embedding failures now expose the real upstream cause without exposing API keys.
- Added `GET /api/settings/provider-diagnostics` for in-dashboard troubleshooting.
- Increased default upstream connection/read windows for slow hosted providers while keeping retries disabled.
- Preserved `/models` → chat probe fallback for OpenAI-compatible gateways that do not expose `/models`.
- Added request IDs to surfaced API errors.


## 2.2.1 - Hosted Chat Performance

- بهبود timeout و حذف retryهای تودرتو برای تماس‌های AI در Serverless.
- cache شدن کلاینت OpenAI-compatible در runtimeهای گرم.
- کاهش اندازه تاریخچه و context ارسالی به مدل.
- تست اتصال سبک‌تر با اولویت `/models`.
- ارسال صریح مدل انتخاب‌شده در هر درخواست چت و نمایش مدل واقعاً استفاده‌شده.
- ثبت زمان Embedding، Search و LLM برای عیب‌یابی Vercel.

# Changelog

## Unreleased — 2026-10-03

### Fixed

- Hardened OpenAI-compatible provider calls for Vercel with explicit request timeout and bounded retries.
- Added connection-failure logging that records the provider URL and exception type without logging API keys.
- Added hosted AI network troubleshooting steps to the deployment guide.

### Configuration

- Added `AI_REQUEST_TIMEOUT_SECONDS` (default `45`).
- Added `AI_MAX_RETRIES` (default `2`).


## v2.3.1 — 2026-10-01

### Fixed

- Hardened `setup.bat` against PyPI/file-host DNS failures by trying multiple HTTPS package indexes.
- Removed the mandatory pip self-upgrade from setup so an unreachable package index cannot fail setup before dependency installation.
- Added local pip restoration with `ensurepip` when a virtual environment has no working pip.
- Added an optional `QUASAR_PIP_INDEX_URL` override for networks that require a custom package mirror.

### Documentation

- Documented the Windows dependency-install fallback behavior and custom mirror override.

## v2.3.0 — 2026-10-01

### Added

- User-scoped dashboard summary endpoint.
- Provider model discovery and custom connection testing.
- Document reindexing endpoint.
- Owned playground session deletion.
- Public widget rate limiting.
- Prompt-injection flag categorization with normalized matching.
- Admin pagination and last-administrator safeguards.
- Request IDs and structured request timing logs.
- Frontend theme switching, responsive polish, accessible toasts and request timeouts.
- Deployment documentation and configurable Linux launcher.

### Improved

- Authentication validation and malformed JWT handling.
- Centralized application/provider errors.
- RAG context boundaries and bounded history.
- Semantic retrieval with configurable similarity threshold.
- Concurrent model Battle execution.
- Knowledge/admin aggregate queries to reduce repeated database work.
- Secret handling and production runtime configuration.
- Windows setup script reliability and encoding safety.

### Security

- Removed the committed `.env` from the current repository state and ignored future `.env` files.
- Removed the provider API-key fallback from source configuration.
- Production now requires explicit `SECRET_KEY` configuration.
- Public widget input is bounded and rate-limited.
- Prompt-injection flags store a category rather than echoing the original user prompt.

### Testing

The final suite covers API isolation, authentication, RAG, retrieval, knowledge reindexing, widget security, prompt monitoring, RBAC, admin pagination, logging, performance contracts and frontend asset contracts.

## 2.3.0
- Admin: fixed user inspection and chat viewing errors (chunk counting no longer loads embedding vectors, NULL-safe settings/messages, no N+1 on sessions).
- UI: flat minimal black/violet theme (tokens + override block in style.css).

## v2.8.6 — Supabase schema compatibility repair

- Added idempotent migration `008_repair_embedding_provider_mode.sql` for existing Supabase databases missing `user_settings.embedding_use_default_provider`.
- Backfilled old rows from `use_default_provider` while preserving existing non-NULL values; set a default and `NOT NULL` constraint without dropping or deleting data.
- Documented recovery steps and SQL verification for PostgreSQL `UndefinedColumn` errors.
