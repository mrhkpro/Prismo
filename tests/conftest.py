"""محیط تست را از SDK شبکه‌ای OpenAI مستقل می‌کند."""
import os
import sys
import types

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite://"


if "openai" not in sys.modules:
    fake_openai = types.ModuleType("openai")

    class OpenAI:  # noqa: N801
        pass

    class APIError(Exception):
        pass

    class APIConnectionError(APIError):
        pass

    class AuthenticationError(APIError):
        pass

    fake_openai.OpenAI = OpenAI
    fake_openai.APIError = APIError
    fake_openai.APIConnectionError = APIConnectionError
    fake_openai.AuthenticationError = AuthenticationError
    sys.modules["openai"] = fake_openai
