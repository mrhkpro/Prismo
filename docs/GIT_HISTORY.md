# Git History

تاریخچه پروژه به‌صورت feature-branch و mergeهای `--no-ff` نگه‌داری می‌شود تا هر دسته تغییر در graph قابل تشخیص باشد.

## Release line

```text
main
├─ feature/repository-foundation
├─ feature/vercel-ai-resilience
├─ feature/deployment-docs
├─ feature/release-cleanup
├─ feature/release-notes
├─ feature/release-notes-doc
├─ feature/chat-performance
├─ feature/model-switching
├─ feature/chat-observability
└─ docs/vercel-chat-runbook
```

## Convention

- `feat:` برای قابلیت جدید
- `fix:` برای اصلاح رفتار
- `perf:` برای بهبود سرعت/مصرف
- `test:` برای قراردادهای تست
- `docs:` برای مستندات
- `chore:` برای نگه‌داری repository

برای حفظ graph، ادغام branchهای feature در `main` با `git merge --no-ff` انجام می‌شود.
## v2.2.2 release chain

- `feature/provider-diagnostics` → actionable upstream error classification
- `feature/error-surface` → dashboard/chat error details
- `feature/vercel-connection-tuning` → longer hosted provider windows
- `docs/provider-diagnostics` → deployment troubleshooting guide
- `docs/release-v2.2.2` → release notes

All branches were merged into `main` with `--no-ff` to preserve the graph.

## v2.4.0 release chain

Baseline first, then the redesign, then tests and the fixes they uncovered. Every branch was merged into `main` with `--no-ff`.

- `chore/v2.3.0-snapshot` → records the uncommitted v2.3.0 working tree as a baseline
- `test/admin-inspect-baseline` → tracks the existing admin inspection regression test
- `style/dual-theme-tokens` → violet night + gold day design tokens
- `style/base-controls` → base, buttons, inputs, badges, toasts
- `style/app-shell-components` → sidebar, cards, tables, chat, modals (removes the v2.3 override block)
- `style/landing-auth` → landing showcase and sign-in card
- `style/widget-dual-theme` → widget palettes, accent-aware text, theme-aware preview
- `fix/theme-visual-regressions` → preview iframe canvas, Persian mono fallback
- `fix/asset-cache-bust-2.4.0` → `?v=2.4.0` everywhere including the embed snippet
- `test/full-platform-flow` → 46-scenario end-to-end API suite
- `fix/dark-button-contrast` → WCAG AA for the dark primary button
- `test/theme-contracts` → static theme/contrast/wiring contracts
- `fix/widget-session-source-scope` → public widget only continues widget sessions
- `fix/knowledge-clear-order` → chunks deleted before documents on "clear all"
- `fix/playground-session-source-scope` → playground only continues playground sessions
- `docs/release-2.4.0` → changelog and this history

## v2.5.0 release chain

- `style/gentelella-shell` → topbar, breadcrumb, rail/drawer sidebar, card primitives, skeleton styles
- `style/ai-connection-redesign` → decluttered AI connection page
- `feature/streaming-chat` → SSE streaming for lab chat and public widget
- `feature/knowledge-file-import` → PDF/Office/OpenDocument/EPUB/... import in the browser
- `feature/widget-extras-backend` → `widget_extras` JSON column, safe raw-SQL access, migration 002
- `feature/widget-pixel-pet` → pixel pets, quick replies, teaser, live preview channel
- `feature/widget-builder-redesign` → tabbed widget builder with swatches and embed theme
- `fix/switch-knob-token` → token for the switch knob, sprite parity tests
- `feature/admin-security-alerts` → scanner v2, severity, flags enrichment, summary endpoint
- `feature/admin-security-ui` → live banner, badge, alert cards
- `perf/lazy-loading-and-click-guard` → skeletons, on-demand scripts, GET de-dup, click guard, cache headers
- `chore/release-2.5.0` → asset versions 2.5.0
- `docs/release-2.5.0` → this changelog and history

## v2.6.5 release chain

> The delivered v2.6.4 archive did not contain the `.git` directory, so the earlier branches listed above are not in this repository. History resumes from a baseline snapshot of v2.6.4; everything after it is merged into `main` with `--no-ff` as before.

- `chore/v2.6.4-baseline` → snapshot of the delivered v2.6.4 tree (on `main`)
- `chore/asset-version-2.6.5` → asset/embed versions `2.6.5` (cache bust)
- `fix/widget-extras-ddl-deadlock` → DDL on the request connection + catalog check + lock timeout; regression tests
- `fix/stream-detached-session` → SSE endpoints use their own short-lived sessions; no double retrieval
- `style/top-toast-bar` → notifications pinned to the top, no inline text beside save, unsaved-dot on the button
- `docs/release-2.6.5` → changelog and this history

`.env` stays untracked (see `.gitignore`).

## v2.7.0 release chain

- `feature/settings-center-2.7` → centralized settings, seven themes, language/RTL-LTR switching, response preferences and in-settings account.
- `feature/provider-dual-credentials-2.7` → separate chat/embedding credentials, verified capability probing and migration 003.
- `perf/request-widget-fix-2.7` → GET TTL cache, request de-duplication/invalidation, streaming preference wiring and widget bootstrap resilience.
- `docs/release-2.7.0` → release notes, asset version sweep and test/smoke verification.

All branches in the release line are merged into `main` with `--no-ff` to preserve the graph.

## v2.7.2

- `fix/supabase-compat-2.7.2` — Supabase/user-settings compatibility and admin safety.
- `feature/global-i18n-2.7.2` — global locale propagation and settings UI.
- `test/release-2.7.2` — regression tests and release verification.
- Release merged into `main` with `--no-ff` and tagged `v2.7.2`.


## v2.7.3

- `feature/english-admin-dates-2.7.3` — complete translations for reported mixed-language text, Latinize UI numerals in English, and show admin dates in Gregorian format.
- `feature/battle-stream-2.7.3` — simultaneous side-by-side token streaming for Model Battle, retaining the original endpoint as a compatibility fallback.
- `feature/widget-cursor-knowledge-progress-2.7.3` — remove the completed quick-reply caret and add gradual, capped knowledge indexing progress.
- `perf/knowledge-embedding-batch-2.7.3` — increase embedding batch size from 32 to 40 to reduce request overhead while leaving concurrent request count unchanged.
- `docs/release-2.7.3` — cache-bust updated assets, update the widget embed snippet and setup server version, and capture release notes/tests.
- Release line is merged with `--no-ff`; `main` is tagged `v2.7.3`.

- `fix/english-progress-polish-2.7.3` — translate mixed admin labels and fallback/upload success strings, and use Latin percent symbols for English file-import progress. Regression test added; final suite: 204 passed.


## v2.7.4 — Prismo rebrand and complete English UI polish

- `feature/prismo-brand-i18n-2.7.4` — complete English translations for Settings and Test Lab, add the FA/EN login switch, remove the login-page floating theme toggle, and prevent runtime chat/user content from being accidentally translated.
- `feature/prismo-identity-2.7.4` — update public brand text, page titles, SVG favicon/mark, setup page, widget credit, and project documentation to Prismo.
- `fix/settings-testlab-i18n-2.7.4` — close missing Settings strings, translate the built-in Test Lab greeting, localize the disabled account status value, and maintain consistent 2.7.4 asset cache keys.
- New environment variable names use the `PRISMO_` prefix while legacy `QUASAR_` settings remain accepted for upgrades.
- Release branch is merged with `--no-ff`; `main` is tagged `v2.7.4`.

## v2.7.7 release chain — 2026-10-10

- `feature/google-oauth-cookie-session-2.7.7` — server-side Google Authorization Code + PKCE, verified ID token, secure cookie session and logout; merged with `--no-ff`.
- `fix/theme-presets-nord-amber-rose-2.7.7` — unified persisted theme selection and polished Nord/Amber/Rose; merged with `--no-ff`.
- `fix/openrouter-catalog-full-models-2.7.7` — full OpenRouter metadata/pricing catalogue, free/paid counts and exact embedding-dimension probes; merged with `--no-ff`.
- `fix/separate-embedding-form-key-2.7.7` — uses unsaved form-entered embedding credentials for a read-only discovery request; merged with `--no-ff`.
- `work/oauth-themes-openrouter-2.7.7` — integration branch; release cache-busters and v2.7.7 changelog.
- Verification: 229 Python tests, Python compile check, JavaScript syntax checks and a local SQLite health/static smoke test. Google OAuth and OpenRouter cannot be called live without external credentials/network access; those flows were tested with mocks.
- Environment safety: `.env` had previously been tracked. It is removed from the delivered history and ignored going forward; the `.env.example` template remains.


## v2.7.8 — independent provider modes and auth recovery — 2026-10-10

- `feat/independent-chat-embedding-providers-v2.7.8` — independently select the chat source/model and embedding source/model; preserve custom embedding credentials when temporarily switching back to prepared embeddings; reduce chat discovery time by skipping unrelated embedding probes; add migration 005 and compatibility tests.
- `fix/google-supabase-config-fast-2.7.8` — accept common Supabase/Vercel env aliases, redirect directly to Supabase Auth with PKCE, preserve the legacy username/password flow, and document both Supabase-hosted and direct Google OAuth configuration.
- `chore/release-2.7.8` — bump app asset cache keys, update release docs, and verify frontend contracts.
- Release is merged to `main` with `--no-ff` and tagged `v2.7.8`; `.env` and API keys are excluded from deliverables.
- Verification: 238 Python tests passed; `compileall`, JavaScript `node --check`, and `git diff --check` passed. Live Google/Supabase OAuth and external model APIs were not exercised because valid production credentials/network access were not available in this environment.
