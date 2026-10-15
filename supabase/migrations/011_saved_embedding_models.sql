-- Keep each user's custom embedding model profiles visible over time. API keys stay server-side.
CREATE TABLE IF NOT EXISTS saved_embedding_models (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model_id VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_saved_embedding_model_profile UNIQUE (user_id, model_id, base_url)
);
CREATE INDEX IF NOT EXISTS ix_saved_embedding_models_user_id ON saved_embedding_models(user_id);
