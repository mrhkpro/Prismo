import unittest

from pydantic import ValidationError

from app import schemas


class APIHardeningTests(unittest.TestCase):
    def test_widget_message_limit_is_enforced(self):
        with self.assertRaises(ValidationError):
            schemas.WidgetChatRequest(message="x" * 4001)

    def test_custom_base_url_must_be_http_or_https(self):
        with self.assertRaises(ValidationError):
            schemas.DiscoverModelsRequest(base_url="file:///tmp/models", api_key="x")

    def test_widget_color_is_strict_hex(self):
        with self.assertRaises(ValidationError):
            schemas.WidgetConfigUpdate(widget_color="red")

    def test_role_is_an_explicit_enum_of_allowed_values(self):
        with self.assertRaises(ValidationError):
            schemas.RoleUpdateRequest(role="owner")


if __name__ == "__main__":
    unittest.main()
