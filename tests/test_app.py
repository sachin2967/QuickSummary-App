"""Offline tests for QuickSummary's request validation and API handling."""

import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("API_TOKEN", "test-token")

from app import app  # noqa: E402


class QuickSummaryTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_renders_default_length(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"50-1000 model tokens", response.data)

    def test_empty_text_is_rejected_without_api_call(self):
        with patch("app.requests.post") as post:
            response = self.client.post("/", data={"text": "   ", "maxL": "100"})
        self.assertEqual(response.status_code, 400)
        post.assert_not_called()

    def test_invalid_length_is_rejected(self):
        with patch("app.requests.post") as post:
            response = self.client.post("/", data={"text": "Some text", "maxL": "9999"})
        self.assertEqual(response.status_code, 400)
        post.assert_not_called()

    @patch.dict(os.environ, {"API_TOKEN": "test-token"})
    @patch("app.requests.post")
    def test_successful_summary_uses_json_and_timeout(self, post):
        response_obj = Mock()
        response_obj.json.return_value = [{"summary_text": "A concise summary."}]
        response_obj.raise_for_status.return_value = None
        post.return_value = response_obj

        response = self.client.post("/", data={"text": "Long source text.", "maxL": "100"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"A concise summary.", response.data)
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["json"]["parameters"]["max_length"], 100)
        self.assertEqual(kwargs["timeout"], (10, 60))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-token")

    @patch.dict(os.environ, {"API_TOKEN": ""})
    @patch("app.requests.post")
    def test_missing_token_is_reported_without_network_call(self, post):
        response = self.client.post("/", data={"text": "Some text", "maxL": "100"})
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"not configured", response.data)
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
