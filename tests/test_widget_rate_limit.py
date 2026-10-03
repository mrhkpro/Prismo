import sys
import types
import unittest
from unittest.mock import patch

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

from fastapi import HTTPException
from starlette.requests import Request

from app import models, schemas
from app.services.rate_limit import RateLimiter
from app.routers import public_widget


class WidgetRateLimitTests(unittest.TestCase):
    def test_rate_limiter_blocks_after_limit(self):
        limiter = RateLimiter(limit=2, window_seconds=60)
        self.assertTrue(limiter.allow("client"))
        self.assertTrue(limiter.allow("client"))
        self.assertFalse(limiter.allow("client"))

    def test_public_widget_returns_429_before_llm_work(self):
        request = Request({"type": "http", "client": ("127.0.0.1", 1234), "method": "POST", "path": "/"})
        owner = models.User(id=1, username="owner", password_hash="x", is_active=True)
        payload = schemas.WidgetChatRequest(message="hello")
        with patch("app.routers.public_widget._get_owner_by_widget", return_value=owner), \
             patch("app.routers.public_widget.rate_limit.public_widget_limiter.allow", return_value=False):
            with self.assertRaises(HTTPException) as caught:
                public_widget.widget_chat("widget-id", payload, request, None)
        self.assertEqual(caught.exception.status_code, 429)


if __name__ == "__main__":
    unittest.main()
