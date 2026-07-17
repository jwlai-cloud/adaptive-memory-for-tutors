import os
import unittest

from fastapi.testclient import TestClient

from api.rest.app import app


class RestApiSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_api_key = os.environ.get("API_KEY")
        os.environ["API_KEY"] = "test-demo-key"
        self.client = TestClient(app)

    def tearDown(self) -> None:
        if self.previous_api_key is None:
            os.environ.pop("API_KEY", None)
        else:
            os.environ["API_KEY"] = self.previous_api_key

    def test_health_is_public_for_platform_probes(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_pairs_rejects_path_traversal(self) -> None:
        response = self.client.get(
            "/v1/pairs?domain=../../.env",
            headers={"Authorization": "Bearer test-demo-key"},
        )

        self.assertEqual(response.status_code, 404)
