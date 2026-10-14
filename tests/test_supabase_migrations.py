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


def test_supabase_provider_repair_migration_repairs_all_optional_columns():
    migration = (
        ROOT / "supabase" / "migrations" / "009_repair_all_embedding_provider_columns.sql"
    ).read_text(encoding="utf-8").lower()

    for column in (
        "separate_embedding_provider",
        "embedding_api_key",
        "embedding_base_url",
        "embedding_use_default_provider",
    ):
        assert f"add column if not exists {column}" in migration

    assert "coalesce(use_default_provider, true)" in migration
    assert "where embedding_use_default_provider is null" in migration
    assert "alter column embedding_use_default_provider set not null" in migration
    assert "drop table" not in migration
    assert "drop column" not in migration
    assert "delete from" not in migration


def test_bootstrap_seed_uses_legacy_compatible_settings_access():
    source = (ROOT / "app" / "seed.py").read_text(encoding="utf-8")
    assert "user_settings_compat.ensure_settings(" in source
    assert "if not admin.settings" not in source
    assert "models.UserSettings(" not in source
