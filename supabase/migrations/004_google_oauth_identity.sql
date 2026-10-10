-- Google OAuth identity fields for the existing FastAPI auth system.
-- Safe to run once on an already-initialized Supabase/PostgreSQL database.
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS email VARCHAR(320),
    ADD COLUMN IF NOT EXISTS google_sub VARCHAR(255);

-- Multiple password-only accounts may have NULL values; non-NULL identities
-- remain unique. Emails are normalized to lowercase by the OAuth callback.
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email
    ON public.users (email)
    WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub
    ON public.users (google_sub)
    WHERE google_sub IS NOT NULL;
