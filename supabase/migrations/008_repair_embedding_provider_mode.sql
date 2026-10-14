-- Repair migration for hosted databases that are missing the independent
-- embedding provider selector expected by app.models.UserSettings.
-- Safe to run more than once; existing non-NULL selections are preserved.
BEGIN;

ALTER TABLE public.user_settings
    ADD COLUMN IF NOT EXISTS embedding_use_default_provider BOOLEAN;

UPDATE public.user_settings
SET embedding_use_default_provider = COALESCE(use_default_provider, TRUE)
WHERE embedding_use_default_provider IS NULL;

ALTER TABLE public.user_settings
    ALTER COLUMN embedding_use_default_provider SET DEFAULT TRUE,
    ALTER COLUMN embedding_use_default_provider SET NOT NULL;

COMMIT;
