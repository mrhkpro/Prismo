-- Keep the legacy public.users schema untouched so password login continues to
-- work on existing Supabase projects. External OAuth identities live separately.
CREATE TABLE IF NOT EXISTS public.oauth_identities (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    email VARCHAR(320),
    user_id INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_oauth_identities_provider_subject UNIQUE (provider, subject)
);

CREATE INDEX IF NOT EXISTS ix_oauth_identities_provider
    ON public.oauth_identities (provider);
CREATE INDEX IF NOT EXISTS ix_oauth_identities_email
    ON public.oauth_identities (email);
CREATE INDEX IF NOT EXISTS ix_oauth_identities_user_id
    ON public.oauth_identities (user_id);

-- Migrate Google identities created by the previous v2.7.7 schema, if those
-- optional columns happen to exist. This block is harmless on the old schema.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'google_sub'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'email'
    ) THEN
        EXECUTE $q$
            INSERT INTO public.oauth_identities (provider, subject, email, user_id)
            SELECT 'google', google_sub, email, id
            FROM public.users
            WHERE google_sub IS NOT NULL
            ON CONFLICT (provider, subject) DO NOTHING
        $q$;
    END IF;
END $$;
