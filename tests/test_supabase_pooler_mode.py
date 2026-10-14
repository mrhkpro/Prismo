from sqlalchemy.engine import make_url

from app.database import resolve_postgres_connection_url


def test_local_supabase_transaction_pooler_uses_session_port():
    raw = (
        "postgresql+psycopg://postgres.project-ref:pw%40ss@"
        "aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
    )
    resolved = resolve_postgres_connection_url(raw, is_vercel=False)
    parsed = make_url(resolved)
    assert parsed.port == 5432
    assert parsed.host == "aws-0-ap-northeast-2.pooler.supabase.com"
    assert parsed.username == "postgres.project-ref"
    assert parsed.password == "pw@ss"
    assert parsed.database == "postgres"
    assert parsed.query["sslmode"] == "require"


def test_vercel_keeps_supabase_transaction_pooler_port():
    raw = "postgresql+psycopg://postgres.project-ref:secret@aws-0-region.pooler.supabase.com:6543/postgres"
    resolved = resolve_postgres_connection_url(raw, is_vercel=True)
    assert make_url(resolved).port == 6543


def test_existing_session_pooler_url_is_unchanged():
    raw = "postgresql+psycopg://postgres.project-ref:secret@aws-0-region.pooler.supabase.com:5432/postgres"
    resolved = resolve_postgres_connection_url(raw, is_vercel=False)
    assert make_url(resolved).port == 5432


def test_direct_supabase_url_is_not_rewritten():
    raw = "postgresql+psycopg://postgres:secret@db.project-ref.supabase.co:5432/postgres"
    resolved = resolve_postgres_connection_url(raw, is_vercel=False)
    assert make_url(resolved).host == "db.project-ref.supabase.co"
    assert make_url(resolved).port == 5432


def test_other_postgres_provider_is_not_rewritten():
    raw = "postgresql+psycopg://user:secret@db.example.com:6543/postgres"
    resolved = resolve_postgres_connection_url(raw, is_vercel=False)
    assert make_url(resolved).port == 6543
