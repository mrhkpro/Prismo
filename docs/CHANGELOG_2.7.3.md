# v2.7.3 — English UI, Streaming Model Battle & Knowledge Progress

## English interface

- Added complete English translations for the reported widget embed instructions, Test Lab helper text, empty knowledge state, project overview and Admin panel title.
- UI numerals and Persian percent signs are normalized to Latin numerals and `%` in English mode.
- Admin dates use the Gregorian calendar and Latin digits when English is selected; the active Admin view refreshes after a language change.

## Model comparison

- Added `POST /api/playground/battle/stream`, which streams both selected models concurrently and tags each token/timing/error with its side.
- Kept `POST /api/playground/battle` unchanged; the frontend falls back to it when the streaming endpoint is unavailable.
- Added regression tests for normal streaming and an isolated model-side failure.

## Widget and knowledge base

- Quick replies no longer keep the streaming/caret class after the instant response has finished.
- The knowledge indexing progress bar advances gradually while an embedding batch is in flight, never guesses 100%, and stays capped at 89% until server progress/completion confirms more work has finished.
- Increased default embedding batch size from 32 to 40 to reduce the number of upstream requests; embedding concurrency remains unchanged at 4. `EMBEDDING_BATCH_SIZE` remains configurable in the environment for providers with stricter batch limits.

## Release verification

- Updated frontend asset versions and generated widget embed code to `2.7.3` to prevent stale browser/CDN caches.
- Full test suite: **203 passed**. Regression checks cover English copy/date formats, battle stream events, quick-reply caret cleanup, embedding batching and gradual progress behavior.
