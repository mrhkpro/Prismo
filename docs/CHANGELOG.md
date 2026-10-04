# Changelog

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
- `tests/test_full_platform_flow.py`: 45 end-to-end API scenarios (auth, settings and custom provider lifecycle, widget color/title/embed code, knowledge CRUD and reindex, playground chat/search/battle/sessions, public widget limits, dashboard counters, admin stats/user detail/reading one person's messages/flags/block/roles/impersonation). AI calls are mocked; DB is in-memory SQLite.
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
