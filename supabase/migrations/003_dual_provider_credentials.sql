-- Quasar 2.7: optional independent embedding provider credentials.
-- Safe to run once after 001/002.
ALTER TABLE user_settings
  ADD COLUMN IF NOT EXISTS separate_embedding_provider boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS embedding_api_key text,
  ADD COLUMN IF NOT EXISTS embedding_base_url text;
