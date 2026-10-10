-- Prismo v2.7.9: Google sign-in was removed. Preserve application users and data;
-- only remove the obsolete mapping table introduced for external OAuth identities.
DROP TABLE IF EXISTS public.oauth_identities;
