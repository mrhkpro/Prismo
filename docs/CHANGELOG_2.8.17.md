# Prismo v2.8.17 — Active model status, saved-model actions, and widget RAG regressions

## Added
- Added a compact active-model status panel to AI settings, showing the currently resolved chat and embedding model, the active provider mode, and the configured endpoint host/path.
- Added `Use` and `Test API` actions for saved chat and embedding profiles. Activation is scoped to the current user's saved model and only updates the matching provider settings; it does not overwrite the other provider's active configuration.
- Added authenticated endpoints:
  - `POST /api/settings/saved-chat-models/use`
  - `POST /api/settings/saved-chat-models/test`
  - `POST /api/settings/saved-embedding-models/use`
  - `POST /api/settings/saved-embedding-models/test`
- Chat profile testing uses provider diagnostics; embedding profile testing issues a real embedding request only when the user clicks **Test API**. API keys are not returned to the browser.

## Improved
- Added compact responsive actions and styles for saved model cards, with usable layout on smaller screens.
- Activating an embedding profile re-checks the existing optional provider columns before saving; the change does not modify database connection or Vercel runtime settings.
- Bumped the dashboard CSS/JS cache-busting version to `2.8.17`.

## Regression tests
- Added an end-to-end local widget test with a real SQLite knowledge chunk and the real RAG retrieval implementation. It asserts that the retrieved knowledge text is present in the first model prompt and that repeating the same question after two other turns reuses conversation memory without extra provider resolution, embeddings, semantic search, or completion requests.
- Added tests that saved chat/embedding profiles can be activated without overwriting the other provider, and that test actions pass saved credentials to the correct provider diagnostic/embedding call without activating the profile.

## Verification
- Full suite: **294 passed**.
- `node --check frontend/assets/js/dashboard.js`
- `python -m compileall -q app`
- `git diff --check`

Live Supabase/Vercel connectivity and live third-party provider credentials were not exercised in this automated environment. Network/connection configuration was intentionally not changed.
