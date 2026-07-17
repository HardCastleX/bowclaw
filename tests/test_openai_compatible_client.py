import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from modules.openai_compatible_client import OpenAICompatibleClient


class TestOpenAICompatibleClient(unittest.TestCase):
    def setUp(self):
        self.client = OpenAICompatibleClient(
            base_url="https://api.example.com/v1",
            model="test-model",
            api_key="fake-key",
            max_retries=1,
        )

    def test_build_url(self):
        self.assertEqual(self.client._build_url(), "https://api.example.com/v1/chat/completions")

    def test_build_headers_includes_bearer_token_when_api_key_set(self):
        headers = self.client._build_headers()
        self.assertEqual(headers["Authorization"], "Bearer fake-key")

    def test_build_headers_omits_auth_when_no_api_key(self):
        client = OpenAICompatibleClient(base_url="http://localhost:11434/v1", model="llama3")
        headers = client._build_headers()
        self.assertNotIn("Authorization", headers)

    def test_build_payload_uses_pro_model_when_requested(self):
        client = OpenAICompatibleClient(
            base_url="https://api.example.com/v1", model="fast", pro_model="smart"
        )
        payload = client._build_payload("int main(){}", use_pro=True)
        self.assertEqual(payload["model"], "smart")

    def test_analyze_chunk_returns_content_on_success(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "analisis ok"}}]
        })

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        result = asyncio.run(self.client.analyze_chunk(mock_session, "int main(){}"))
        self.assertEqual(result, "analisis ok")

    def test_analyze_chunk_raises_after_exhausting_retries(self):
        mock_response = AsyncMock()
        mock_response.status = 500

        mock_session = MagicMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("modules.openai_compatible_client.asyncio.sleep", new=AsyncMock()):
            with self.assertRaises(RuntimeError):
                asyncio.run(self.client.analyze_chunk(mock_session, "int main(){}"))


if __name__ == "__main__":
    unittest.main()
