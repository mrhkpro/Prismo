import unittest

from fastapi.testclient import TestClient

from app.main import app


class LoggingTests(unittest.TestCase):
    def test_health_response_contains_request_id(self):
        response = TestClient(app).get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertRegex(response.headers.get("X-Request-ID", ""), r"^[0-9a-f]{32}$")


if __name__ == "__main__":
    unittest.main()
