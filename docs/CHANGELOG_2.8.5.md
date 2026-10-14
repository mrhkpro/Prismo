# Prismo v2.8.5 — Hosted auth hardening and repeated-question performance

## Google OAuth / production callback

- Replaced the production implicit-token redirect path with Supabase Auth PKCE using a short-lived verifier stored only in `sessionStorage`.
- Production `*.vercel.app` sign-in returns to `https://rag-widget-beta.vercel.app/auth-callback.html`; localhost is used only when OAuth starts from localhost/127.0.0.1.
- The callback strips all query/fragment parameters from browser history before network calls, accepts only the PKCE one-time code and rejects implicit bearer-token redirects; it also validates the callback origin, stored verifier and a 10-minute initiation window.
- Added `/api/auth/google-pkce`: the server exchanges the one-time code with Supabase and verifies the resulting user before minting a Prismo JWT. It does not return Supabase access/refresh tokens or Google provider tokens to the browser.
- Kept username/password auth and the legacy `/google-supabase` backend route for compatibility, but the active callback page no longer accepts implicit token fragments; new sign-ins use PKCE only.

## RAG response speed and safe exact-answer cache

- Added a seven-day exact normalized-question cache scoped to user, provider URLs/models, fingerprints of provider credentials, system prompt, language, retrieval settings and the current knowledge-base state.
- Cross-session cache reads are permitted only for context-free first turns; immediate duplicate questions may use the immediately preceding answer. The key contains hashes/fingerprints rather than raw prompts or API credentials.
- Cached source chunks are revalidated against the user's current document ownership. Empty responses are never cached; optional cache SQL errors fall through to the regular RAG path.
- Added `supabase/migrations/007_answer_cache.sql`; local SQLite creates the table through SQLAlchemy metadata.

## Prompt extraction / admin notifications

- Refined the base system prompt to explicitly refuse disclosure of hidden instructions, API keys, tokens, credentials, environment values and cross-user private data even when the request is phrased as a threat, encoding request or roleplay.
- A message matched by existing extraction/dangerous-action scanner rules is stored as a flagged message before inference and returns a fixed refusal without calling the chat or embedding provider.
- A subsequent flagged attempt in the same chat session is annotated with `repeat-sensitive-attempt` and elevated to critical.
- The admin summary continues to report unresolved rows to every administrator on the shared database. The lower-left floating report button shows unresolved count and highest severity, opens the security review view, and pulses for critical events.
- Updated severity rendering and added tests for threatening Persian prompt-extraction requests and repeat escalation.

## UX / delivery

- Added small, cross-page keyboard focus and reduced-motion refinements while preserving page layouts and behavior.
- Updated the dashboard version label, all runtime asset cache-busters, and the generated embed snippet to `2.8.5`.
- Added documentation for the exact Supabase Site URL, allowed callback URLs, Google Cloud Supabase callback, and the cache migration.

## Validation

- `python -m pytest -q`: **257 passed** after temporarily removing local `.env` from test discovery and restoring it afterwards (the `.env` contents are never printed or committed).
- `python -m compileall -q app tests`, `node --check` for top-level frontend JavaScript, and `git diff --check` passed.
- Live Google/Supabase OAuth and a live external model request were not exercised end-to-end here; they require the real Supabase redirect allow-list and provider/network access. The answer cache requires migration 007 on the hosted database.
