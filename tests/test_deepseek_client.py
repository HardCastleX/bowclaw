import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from modules.deepseek_client import DeepSeekClient


class TestDeepSeekClient(unittest.TestCase):
    def setUp(self):
        self.client = DeepSeekClient(api_key="fake-key", max_retries=1)

    def test_build_headers_includes_bearer_token(self):
        headers = self.client._build_headers()
        self.assertEqual(headers["Authorization"], "Bearer fake-key")

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

        with patch("modules.deepseek_client.asyncio.sleep", new=AsyncMock()):
            with self.assertRaises(RuntimeError):
                asyncio.run(self.client.analyze_chunk(mock_session, "int main(){}"))


if __name__ == "__main__":
    unittest.main()
