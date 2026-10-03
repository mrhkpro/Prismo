import unittest
from pathlib import Path

from app import config


class SecurityHardeningTests(unittest.TestCase):
    def test_production_requires_a_long_secret(self):
        with self.assertRaises(RuntimeError):
            config.validate_runtime_security("production", "")
        with self.assertRaises(RuntimeError):
            config.validate_runtime_security("production", "too-short")
        config.validate_runtime_security("production", "x" * 32)

    def test_env_file_is_ignored_by_git_rules(self):
        gitignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", gitignore.splitlines())

    def test_provider_key_has_no_hardcoded_literal_in_config(self):
        source = (Path(__file__).resolve().parents[1] / "app/config.py").read_text(encoding="utf-8")
        self.assertIn('DEFAULT_PROVIDER_API_KEY = os.getenv(', source)
        self.assertIn('"DEFAULT_PROVIDER_API_KEY",', source)


if __name__ == "__main__":
    unittest.main()
