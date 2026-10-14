-- Prismo v2.8.5: per-user cache for repeated RAG questions.
-- Cache keys include the model/provider settings, system prompt, language, and a
-- fingerprint of the user's current knowledge base. Raw API keys are never stored
-- in cache keys (only a one-way SHA-256 fingerprint is used by the app).

CREATE TABLE IF NOT EXISTS public.answer_cache (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    cache_key VARCHAR(64) NOT NULL,
    answer TEXT NOT NULL,
    source_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_answer_cache_user_key UNIQUE (user_id, cache_key)
);

CREATE INDEX IF NOT EXISTS ix_answer_cache_user_id ON public.answer_cache(user_id);
CREATE INDEX IF NOT EXISTS ix_answer_cache_cache_key ON public.answer_cache(cache_key);
