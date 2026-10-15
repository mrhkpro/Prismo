-- Idempotent repair for both custom chat and embedding model registries.
-- Run once in Supabase SQL Editor if either registry table is missing.
-- API keys are stored server-side and are never returned by list endpoints.

CREATE TABLE IF NOT EXISTS public.saved_chat_models (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    model_id VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_saved_chat_model_user_model UNIQUE (user_id, model_id)
);
CREATE INDEX IF NOT EXISTS ix_saved_chat_models_user_id ON public.saved_chat_models(user_id);

CREATE TABLE IF NOT EXISTS public.saved_embedding_models (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    model_id VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_saved_embedding_model_profile UNIQUE (user_id, model_id, base_url)
);
CREATE INDEX IF NOT EXISTS ix_saved_embedding_models_user_id ON public.saved_embedding_models(user_id);
