"""Regression guards for the v2.8.1 Local + Supabase schema contract.

PostgreSQL schema changes are performed explicitly with SQL migrations, not at
local Uvicorn startup. Settings compatibility still reads only columns that
exist, and migrations remain additive/non-destructive.
"""
from pathlib import Path

from app.services import user_settings_compat

ROOT = Path(__file__).resolve().parents[1]
OPTIONAL_PROVIDER_COLUMNS = {
    "separate_embedding_provider",
    "embedding_api_key",
    "embedding_base_url",
    "embedding_use_default_provider",
}


def test_v281_settings_compatibility_uses_narrow_legacy_aware_reads():
    source = (ROOT / "app" / "services" / "user_settings_compat.py").read_text(encoding="utf-8")
    assert "def optional_columns(db: Session) -> set[str]:" in source
    assert "information_schema.columns" in source
    assert "OPTIONAL_COLUMNS" in source
    # Do not restore the later automatic PostgreSQL DDL-at-startup patch.
    assert not hasattr(user_settings_compat, "ensure_local_supabase_provider_schema")


def test_local_supabase_startup_does_not_repair_postgres_schema_automatically():
    source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    lifespan = source.split("async def lifespan", 1)[1].split(
        "# ============================================================\n# APPLICATION", 1
    )[0]
    assert "ensure_local_supabase_provider_schema" not in lifespan
    assert "ALTER TABLE" in lifespan  # SQLite-only compatibility is retained.
    assert "if not config.IS_POSTGRES" in lifespan


def test_explicit_supabase_provider_migration_is_additive_and_idempotent():
    migration = ROOT / "supabase" / "migrations" / "009_repair_all_embedding_provider_columns.sql"
    sql = migration.read_text(encoding="utf-8").lower()
    assert "add column if not exists separate_embedding_provider" in sql
    assert "add column if not exists embedding_api_key" in sql
    assert "add column if not exists embedding_base_url" in sql
    assert "add column if not exists embedding_use_default_provider" in sql
    assert "coalesce(use_default_provider, true)" in sql
    assert "drop table" not in sql
    assert "drop column" not in sql


def test_schema_column_contract_matches_supabase_provider_migration():
    migration = (ROOT / "supabase" / "migrations" / "009_repair_all_embedding_provider_columns.sql").read_text(encoding="utf-8")
    for name in OPTIONAL_PROVIDER_COLUMNS:
        assert name in migration
