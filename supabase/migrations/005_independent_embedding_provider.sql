-- Add an independent source selector for the embedding model without changing
-- the existing chat provider selection. Existing rows preserve their old mode.
ALTER TABLE public.user_settings
    ADD COLUMN IF NOT EXISTS embedding_use_default_provider BOOLEAN;

UPDATE public.user_settings
SET embedding_use_default_provider = use_default_provider
WHERE embedding_use_default_provider IS NULL;

ALTER TABLE public.user_settings
    ALTER COLUMN embedding_use_default_provider SET DEFAULT TRUE,
    ALTER COLUMN embedding_use_default_provider SET NOT NULL;
