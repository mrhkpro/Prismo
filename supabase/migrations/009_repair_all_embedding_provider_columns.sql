-- Repair all optional provider-mode columns on existing Supabase installations.
-- This is safe to run after any subset of migrations 003, 005, and 008.
-- It preserves all existing rows and settings; no table or column is dropped.
BEGIN;

ALTER TABLE public.user_settings
    ADD COLUMN IF NOT EXISTS separate_embedding_provider BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS embedding_api_key VARCHAR(255),
    ADD COLUMN IF NOT EXISTS embedding_base_url VARCHAR(255),
    ADD COLUMN IF NOT EXISTS embedding_use_default_provider BOOLEAN;

-- Preserve the previous chat-provider selection when initializing the new
-- embedding-provider selector for existing rows.
UPDATE public.user_settings
SET embedding_use_default_provider = COALESCE(use_default_provider, TRUE)
WHERE embedding_use_default_provider IS NULL;

ALTER TABLE public.user_settings
    ALTER COLUMN embedding_use_default_provider SET DEFAULT TRUE,
    ALTER COLUMN embedding_use_default_provider SET NOT NULL;

COMMIT;
