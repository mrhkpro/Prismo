-- Per-user saved chat model profiles, so adding a new provider/model does not
-- overwrite earlier models used in Battle mode. API keys are server-side only.
CREATE TABLE IF NOT EXISTS saved_chat_models (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model_id VARCHAR(200) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_saved_chat_model_user_model UNIQUE (user_id, model_id)
);
CREATE INDEX IF NOT EXISTS ix_saved_chat_models_user_id ON saved_chat_models(user_id);
