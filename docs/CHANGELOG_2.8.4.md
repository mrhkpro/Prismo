# Prismo v2.8.4

## Scope and baseline

This release is based on the v2.8.1 source and Git history. It does not replace the project with the later v2.8.3 codebase. Changes are selective and grouped into separate feature branches/merges.

## Vercel and OpenRouter

- Only the Vercel runtime uses the regular JSON `/api/playground/chat` endpoint for Test Lab RAG responses; local and local+Supabase keep the existing SSE stream. Runtime detection defaults to the safer JSON route if detection times out.
- Provider text is extracted from normal string content and supported structured text-content parts. Reasoning-only fields are not shown as a final answer.
- An otherwise successful empty response is retried once at a lower temperature. Repeated empty responses become a visible, localized error and are not stored as a successful blank assistant reply.
- RAG adds a final output check before returning the response.

## Google Login

- Ported the active Supabase Google OAuth redirect/callback used by `final-project-feat-my-work`, without replacing the base auth router or other final-project modules.
- Added `/api/auth/google-supabase`, which validates the provided access token through Supabase Auth and creates/loads a Prismo user before issuing the normal Prismo JWT.
- Added Google sign-in button, callback page and styles. Existing username/password login and registration remain available.
- Documented Google Cloud and Supabase provider/redirect configuration. The live OAuth flow still depends on correct provider credentials and redirect allow-list settings in the target project.

## Admin security alerts

- Expanded heuristic detection for requests to disclose API keys, environment variables, credentials, database connection strings, system prompts, disable safeguards, access other users' data, or destructively alter databases/data.
- Suspected messages from Test Lab and widget flows are persisted before inference and can be viewed by all administrators authorized against the same database through `/api/admin/security/flags`, including the submitted message, reason, severity and source.
- If inference fails after a suspicious message is logged, the alert remains in the admin panel. The alert banner/notifications cover unresolved critical and high alerts, and a newer medium flag cannot hide an actionable alert. This is heuristic monitoring, not a guarantee to detect or block all threats.

## Dashboard home

- Updated the overview header with a branded hero illustration, clear primary actions, capability chips, six icon-led statistics cards, a service-health panel and three quick-action cards. The statistics element IDs and navigation targets are unchanged; the layout is responsive and bilingual.
- Bumped asset cache keys to v2.8.4 to prevent stale HTML/CSS/JavaScript from hiding the new behavior.

## Security and compatibility notes

- `SUPABASE_URL` and `SUPABASE_ANON_KEY` are public project settings; never use the service-role key in the browser. Google Client Secret remains configured in Google Cloud/Supabase and is not added to frontend code.
- `.env` remains ignored and is not committed to Git history; the delivered private full-project ZIP preserves the base archive's local `.env` for convenience. Treat it as confidential.

## Verification

- **252 automated tests passed.** The suite covers runtime-specific chat routing, empty provider replies, security-rule coverage, pre-inference alert persistence and admin visibility, and Google callback/token exchange with mocked Supabase responses.
- `python -m compileall -q app tests`, `node --check` on non-minified JavaScript, and `git diff --check` passed. A headless-browser layout check was performed at desktop and 390px mobile width; no horizontal overflow was detected.
- The Google OAuth provider and live OpenRouter API could not be exercised end-to-end from this build environment; live verification must be performed after configuration and deployment.
