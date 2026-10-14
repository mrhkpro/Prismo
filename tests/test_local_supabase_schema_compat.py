"""Regression tests for automatic additive schema repair in local+Supabase mode."""
from contextlib import contextmanager
from unittest.mock import patch

from app.services import user_settings_compat


class FakeConnection:
    def __init__(self):
        self.statements = []

    def execute(self, statement, *args, **kwargs):
        self.statements.append(str(statement))
        return None


class FakeEngine:
    def __init__(self):
        self.connection = FakeConnection()

    @contextmanager
    def begin(self):
        yield self.connection


class FakeInspector:
    def __init__(self, columns):
        self.columns = set(columns)

    def has_table(self, name):
        assert name == "user_settings"
        return True

    def get_columns(self, name):
        assert name == "user_settings"
        result = []
        for column in self.columns:
            row = {"name": column, "nullable": False, "default": None}
            if column == "embedding_use_default_provider":
                row["default"] = "true"
            result.append(row)
        return result


LEGACY_COLUMNS = {
    "id", "user_id", "use_default_provider", "api_key", "base_url",
    "chat_model", "embedding_model", "system_prompt", "temperature",
    "top_k", "similarity_threshold", "widget_id", "widget_title",
    "widget_welcome_message", "widget_color",
}


def test_local_supabase_additively_repairs_all_missing_provider_columns():
    engine = FakeEngine()
    with patch.object(user_settings_compat, "sa_inspect", return_value=FakeInspector(LEGACY_COLUMNS)):
        added = user_settings_compat.ensure_local_supabase_provider_schema(engine)

    assert set(added) == {
        "separate_embedding_provider", "embedding_api_key",
        "embedding_base_url", "embedding_use_default_provider",
    }
    sql = "\n".join(engine.connection.statements).lower()
    assert sql.count("add column if not exists") == 4
    assert "update user_settings" in sql
    assert "coalesce(use_default_provider, true)" in sql
    assert "set not null" in sql
    assert "drop column" not in sql
    assert "drop table" not in sql


def test_local_supabase_repair_does_not_recreate_existing_columns():
    engine = FakeEngine()
    columns = LEGACY_COLUMNS | {
        "separate_embedding_provider", "embedding_api_key",
        "embedding_base_url", "embedding_use_default_provider",
    }
    with patch.object(user_settings_compat, "sa_inspect", return_value=FakeInspector(columns)):
        added = user_settings_compat.ensure_local_supabase_provider_schema(engine)

    assert added == []
    sql = "\n".join(engine.connection.statements).lower()
    assert "add column if not exists" not in sql
    assert "update user_settings" not in sql
    assert "alter column embedding_use_default_provider" not in sql


def test_local_supabase_repair_explains_when_initial_schema_is_missing():
    engine = FakeEngine()
    inspector = FakeInspector(LEGACY_COLUMNS)
    inspector.has_table = lambda name: False
    with patch.object(user_settings_compat, "sa_inspect", return_value=inspector):
        try:
            user_settings_compat.ensure_local_supabase_provider_schema(engine)
        except RuntimeError as exc:
            assert "001_initial_schema.sql" in str(exc)
        else:
            raise AssertionError("missing base schema should have a clear startup error")
