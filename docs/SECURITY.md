# Security Guide

## Authentication

Authentication uses Prismo JWT access tokens with a `sub` claim containing the numeric user ID. Invalid, expired or malformed tokens return `401`; inactive accounts return `403`. The application supports the existing username/password flow and an optional Google sign-in flow through Supabase Auth. Google sign-in uses the PKCE authorization-code flow; the backend exchanges the one-time code with the session-held verifier, validates the resulting Supabase user, and issues the same Prismo JWT used by the rest of the application.

Configure the Google provider and exact redirect allow list in Supabase. Keep Google's Client Secret inside Google Cloud/Supabase provider settings; do not put it in frontend code. `SUPABASE_ANON_KEY` is the public anon/publishable key and is not interchangeable with the `service_role` key. The backend calls Supabase's `/auth/v1/user` endpoint to validate the returned access token before it creates the Prismo session.

Passwords are stored as PBKDF2-HMAC-SHA256 hashes with a per-password random salt. The project avoids a compiled password-hashing dependency so the one-click Windows setup stays reliable.

## Authorization and tenancy

Protected endpoints resolve the current user before business logic runs. Queries for documents, chunks and chat sessions are scoped to the owner. Admin endpoints require the `admin` role.

The admin impersonation flow issues a short-lived token and records the original admin token in browser storage so the UI can return to the admin account. Google sign-in uses Supabase Auth PKCE: the browser keeps a short-lived verifier in session storage, the one-time callback code is removed from browser history immediately, and the backend exchanges the code before issuing a Prismo JWT. Supabase and Google provider tokens are not written to Prismo localStorage.

The backend prevents an administrator from blocking themselves and from removing/blocking the last active administrator.

## Secrets

`.env` is ignored by Git. Provider API keys are never returned in settings responses; clients receive only an `api_key_set` boolean.

Production requires an explicitly configured `SECRET_KEY` of at least 32 characters. Development may use a generated runtime key.

The repository's original pre-hardening history contained a tracked `.env` file. This branch history does not reproduce or expose its value. Treat any real credential from that old history as compromised and rotate/revoke it before production use.

## Public widget

The public widget intentionally has unauthenticated endpoints because it runs on third-party sites. The design therefore relies on:

- opaque per-widget IDs rather than user IDs;
- no provider API key in browser responses;
- owner active-state checking before public chat;
- input length validation;
- a per-process rate limiter returning `429` after the configured window limit;
- Shadow DOM isolation for widget presentation.

CORS is intentionally open for the embeddable widget. A deployment that does not need cross-origin embedding should narrow CORS to known origins.

## Prompt injection monitoring and admin alerts

`app/services/injection_scanner.py` applies normalized Persian/English heuristic rules to incoming Test Lab and public-widget messages. Categories cover system-prompt extraction, instruction override/jailbreak, knowledge-base exfiltration, API keys and other credentials, environment files/variables, destructive database actions, disabling access controls, and requests to read other users' data.

When an incoming request matches an extraction or dangerous-action rule, `app/services/rag_pipeline.py` persists the user message as a flagged `ChatMessage` **before model inference** and returns a fixed refusal without forwarding the request to the chat model or embedding provider. The database row stores `is_flagged`, a stable `flag_reason` made of rule codes, and the original user-submitted message. The original message is deliberately not copied into application logs. Consequently, a provider timeout or inference error does not erase the security event. Duplicate insertion is avoided when the normal chat turn is subsequently saved. A further suspicious attempt in the same chat session adds a `repeat-sensitive-attempt` rule and sets severity to critical.

The admin security endpoints (`/api/admin/security/flags` and `/api/admin/security/summary`) query flagged messages from the shared application database, so every administrator authorized against that same database can inspect the message, reason/category, severity, originating source (Test Lab or widget), user and timestamp. The UI raises a banner/live notification for the latest unresolved critical/high alert and keeps all severities in the review list; admins can open the conversation, block the account, or mark the event reviewed. A newer medium-level event does not hide a still-unresolved critical/high alert from the headline notification.

This is **heuristic defense and monitoring, not a guarantee that every attack is detected or blocked**. Pattern-based rules can generate false positives and miss novel wording. Requests matched by current extraction/dangerous-action rules are refused before model inference; novel or unrecognized attacks may still reach the model, so model-provider/system-prompt controls and ordinary authorization checks remain necessary. Review the original message in the restricted admin panel and use a shared database if alerts must be visible across several application instances. A separate Local SQLite installation has its own isolated alert store unless it is explicitly connected to the same database.

## API and logging

Input schemas constrain string lengths, enum values, URLs, temperature, top-k and similarity threshold. Unexpected server exceptions are logged with a request ID while the raw exception text is not returned to the client.

Request logs include method, path, status and duration. Do not log API keys, passwords, JWTs or full sensitive message payloads.


## Repeated answer cache

`app/services/answer_cache.py` stores only non-empty, context-independent RAG answers for up to seven days. Cache keys are per user and are based on a normalized question hash, language, chat/embedding endpoint and model, fingerprints (not raw values) of provider keys, system-prompt hash, temperature/top-k/threshold, and the current document/chunk fingerprint. Raw questions and raw API keys are not used as cache-key material. A cross-session hit is allowed only for an empty chat session; an immediate exact repeat in the same session can return the prior assistant answer. Source chunks are revalidated as still belonging to that user before the cached result is returned. Cache-table errors are treated as an optimization miss, not as a reason to fail chat. Apply `supabase/migrations/007_answer_cache.sql` to enable the table on PostgreSQL/Supabase.
