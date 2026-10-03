# Security Guide

## Authentication

Authentication uses JWT access tokens with a `sub` claim containing the numeric user ID. Invalid, expired or malformed tokens return `401`; inactive accounts return `403`.

Passwords are stored as PBKDF2-HMAC-SHA256 hashes with a per-password random salt. The project avoids a compiled password-hashing dependency so the one-click Windows setup stays reliable.

## Authorization and tenancy

Protected endpoints resolve the current user before business logic runs. Queries for documents, chunks and chat sessions are scoped to the owner. Admin endpoints require the `admin` role.

The admin impersonation flow issues a short-lived token and records the original admin token in browser storage so the UI can return to the admin account.

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

## Prompt injection monitoring

`injection_scanner.py` is a heuristic detection layer using normalized Persian/English patterns. It categorizes suspicious input and stores the category as the flag reason rather than copying the full user prompt into the reason field.

This is monitoring, not a complete prompt-injection defense. Suspicious messages require review or additional controls appropriate to the deployment.

## API and logging

Input schemas constrain string lengths, enum values, URLs, temperature, top-k and similarity threshold. Unexpected server exceptions are logged with a request ID while the raw exception text is not returned to the client.

Request logs include method, path, status and duration. Do not log API keys, passwords, JWTs or full sensitive message payloads.
