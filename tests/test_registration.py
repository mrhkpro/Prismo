import unittest

from app.schemas import LoginRequest, RegisterRequest


class RegistrationValidationTests(unittest.TestCase):
    def test_username_and_org_are_trimmed(self):
        payload = RegisterRequest(username="  Alice  ", password="strongpass", org_name="  Acme  ")
        self.assertEqual(payload.username, "Alice")
        self.assertEqual(payload.org_name, "Acme")

    def test_username_length_is_validated_after_whitespace_is_removed(self):
        payload = RegisterRequest(username="  abc  ", password="strongpass")
        self.assertEqual(payload.username, "abc")

    def test_login_username_is_trimmed(self):
        payload = LoginRequest(username="  admin  ", password="secret")
        self.assertEqual(payload.username, "admin")


if __name__ == "__main__":
    unittest.main()
