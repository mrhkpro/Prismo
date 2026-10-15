import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]


class CloudRuntimeTests(unittest.TestCase):
    def load_config(self, database_url, app_env="production"):
        environment = {
            "APP_ENV": app_env,
            "SECRET_KEY": "test-secret-" * 4,
            "DATABASE_URL": database_url,
        }
        with patch.dict(os.environ, environment, clear=True), patch("dotenv.load_dotenv"):
            return runpy.run_path(str(PROJECT_DIR / "app" / "config.py"))

    def test_postgres_does_not_write_to_the_function_filesystem(self):
        with patch("os.makedirs", side_effect=PermissionError("read-only")) as make_directory:
            settings = self.load_config("postgresql://test:password@localhost/postgres")
        self.assertTrue(settings["IS_POSTGRES"])
        self.assertTrue(settings["DATABASE_URL"].startswith("postgresql+psycopg://"))
        make_directory.assert_not_called()

    def test_legacy_postgres_url_is_normalized(self):
        settings = self.load_config("postgres://test:password@localhost/postgres")
        self.assertTrue(settings["IS_POSTGRES"])

    def test_production_rejects_missing_database_url(self):
        with patch("os.makedirs") as make_directory:
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL"):
                self.load_config("")
        make_directory.assert_not_called()

    def test_production_rejects_sqlite(self):
        with self.assertRaisesRegex(RuntimeError, "PostgreSQL"):
            self.load_config("sqlite://")

    def test_local_development_keeps_sqlite_fallback(self):
        settings = self.load_config("", app_env="development")
        self.assertFalse(settings["IS_POSTGRES"])
        self.assertTrue(settings["DATABASE_URL"].startswith("sqlite:///"))
        self.assertTrue(settings["DATA_DIR"].exists())

    def test_deployment_uses_an_allowlist(self):
        patterns = (PROJECT_DIR / ".vercelignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".venv/", patterns)
        self.assertIn(".env", patterns)
        self.assertIn("tests/", patterns)
        self.assertIn("docs/", patterns)


if __name__ == "__main__":
    unittest.main()


def test_postgres_database_uses_warm_connection_pool():
    source = (Path(__file__).resolve().parents[1] / "app" / "database.py").read_text(encoding="utf-8")
    assert "pool_size=3" in source
    assert "max_overflow=2" in source
    assert "pool_timeout=10" in source
    assert "pool_recycle=300" in source
    assert "pool_pre_ping=True" in source
    assert '"connect_timeout": 10' in source
