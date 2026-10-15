# Prismo v2.8.16 — Saved model deletion and a cleaner AI setup page

## Added
- Added a one-click delete action to each saved custom chat model and saved embedding model card.
- Added user-scoped `DELETE /api/settings/saved-chat-models?model_id=...` and `DELETE /api/settings/saved-embedding-models?model_id=...&base_url=...` endpoints. Embedding deletion is matched by both model ID and endpoint.
- Added regression coverage for deleting saved profiles and verifying that one user cannot delete another user's profile.

## Improved
- Collapsed the saved chat model registry by default so it takes up less space while keeping the count visible.
- Turned repeated ready-model deployment instructions into compact expandable help.
- Tightened spacing and typography across the AI model setup forms.
- Kept deletion limited to the reusable saved profile; the currently active model configuration is not silently changed.

## Verification
- `python -m compileall -q app`
- `node --check frontend/assets/js/dashboard.js`
- `git diff --check`
- Full test suite: 288 passed.
