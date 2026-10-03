import unittest
from unittest.mock import Mock

from fastapi import HTTPException

from app import security


class LoginSecurityTests(unittest.TestCase):
    def test_malformed_subject_returns_401(self):
        db = Mock()
        with unittest.mock.patch("app.security.decode_token", return_value={"sub": "not-an-int"}):
            with self.assertRaises(HTTPException) as caught:
                security.get_current_user("token", db)
        self.assertEqual(caught.exception.status_code, 401)

    def test_expired_or_invalid_token_is_still_401(self):
        # Regression contract: decode_token owns token validation and exposes 401s.
        with unittest.mock.patch("jwt.decode", side_effect=security.jwt.InvalidTokenError):
            with self.assertRaises(HTTPException) as caught:
                security.decode_token("bad")
        self.assertEqual(caught.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
