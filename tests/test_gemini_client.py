import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from modules.gemini_client import GeminiClient


class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        self.client = GeminiClient(api_key="fake-key", max_retries=1)

    def test_build_headers_includes_api_key(self):
        headers = self.client._build_headers()
        self.assertEqual(headers["x-goog-api-key"], "fake-key")

    def test_build_url_uses_default_model(self):
        url = self.client._build_url(self.client.model)
        self.assertIn("gemini-3.1-flash-lite", url)
        self.assertTrue(url.endswith(":generateContent"))

    def test_build_payload_adds_thinking_config_for_pro(self):
        payload = self.client._build_payload("int main(){}", use_pro=True)
        self.assertEqual(
            payload["generationConfig"]["thinkingConfig"]["thinkingLevel"], "high"
        )

    def test_build_payload_omits_thinking_config_by_default(self):
        payload = self.client._build_payload("int main(){}", use_pro=False)
        self.assertNotIn("generationConfig", payload)

    def test_build_payload_includes_thoughts_when_verbose_and_pro(self):
        client = GeminiClient(api_key="fake-key", verbose=True)
        payload = client._build_payload("int main(){}", use_pro=True)
        self.assertTrue(payload["generationConfig"]["thinkingConfig"]["includeThoughts"])

    def test_extract_text_separates_thoughts_from_answer(self):
        data = {
            "candidates": [{"content": {"parts": [
                {"thought": True, "text": "razonando..."},
                {"text": "respuesta final"},
            ]}}]
        }
        result = self.client._extract_text(data)
        self.assertEqual(result, "respuesta final")

    def test_extract_text_logs_thoughts_when_verbose(self):
        client = GeminiClient(api_key="fake-key", verbose=True)
        data = {
            "candidates": [{"content": {"parts": [
                {"thought": True, "text": "razonando..."},
                {"text": "respuesta final"},
            ]}}]
        }
        with self.assertLogs("modules.gemini_client", level="INFO") as cm:
            result = client._extract_text(data)
        self.assertEqual(result, "respuesta final")
        self.assertTrue(any("razonando" in msg for msg in cm.output))

    def test_analyze_chunk_returns_content_on_success(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "candidates": [{"content": {"parts": [{"text": "analisis ok"}]}}]
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

        with patch("modules.gemini_client.asyncio.sleep", new=AsyncMock()):
            with self.assertRaises(RuntimeError):
                asyncio.run(self.client.analyze_chunk(mock_session, "int main(){}"))


if __name__ == "__main__":
    unittest.main()
