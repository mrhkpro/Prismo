
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
