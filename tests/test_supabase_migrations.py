from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_supabase_embedding_provider_repair_migration_is_safe_and_non_destructive():
    migration = (
        ROOT / "supabase" / "migrations" / "008_repair_embedding_provider_mode.sql"
    ).read_text(encoding="utf-8").lower()

    assert "add column if not exists embedding_use_default_provider boolean" in migration
    assert "coalesce(use_default_provider, true)" in migration
    assert "where embedding_use_default_provider is null" in migration
    assert "alter column embedding_use_default_provider set default true" in migration
    assert "alter column embedding_use_default_provider set not null" in migration
    assert "drop table" not in migration
    assert "drop column" not in migration
    assert "delete from" not in migration


def test_previous_embedding_provider_migration_and_repair_migration_both_exist():
    migrations = ROOT / "supabase" / "migrations"
    assert (migrations / "005_independent_embedding_provider.sql").exists()
    assert (migrations / "008_repair_embedding_provider_mode.sql").exists()
