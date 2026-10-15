# Prismo v2.8.15 — Saved custom embedding models and Supabase resilience

- Fixed custom embedding model registration by sending the selected model ID, endpoint, and available API key explicitly instead of reconstructing the profile from the previously saved settings.
- Added an idempotent Supabase repair migration for both `saved_chat_models` and `saved_embedding_models`.
- Added actionable migration errors when either model registry table is missing.
- Saved chat models are only visible in the custom Chat API mode; saved embedding profiles are only visible in custom Embedding API mode.
- Improved local PostgreSQL/Supabase connection recovery after network changes (including VPN reconnects) with longer connection timeouts, pool health checks, and more frequent recycling.
- API keys remain server-side and are never included in model-list responses.
