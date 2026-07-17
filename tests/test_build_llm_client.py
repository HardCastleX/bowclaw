import unittest
from unittest.mock import patch

from main import build_llm_client
from modules.gemini_client import GeminiClient
from modules.openai_compatible_client import OpenAICompatibleClient


class TestBuildLlmClient(unittest.TestCase):
    @patch.dict("os.environ", {"GEMINI_API_KEY": "fake-gemini-key"})
    def test_defaults_to_gemini(self):
        client = build_llm_client({})
        self.assertIsInstance(client, GeminiClient)

    @patch.dict("os.environ", {"GEMINI_API_KEY": "fake-gemini-key"})
    def test_gemini_uses_configured_models(self):
        config = {
            "llm_provider": "gemini",
            "providers": {"gemini": {"model": "custom-model", "pro_model": "custom-pro"}},
        }
        client = build_llm_client(config)
        self.assertEqual(client.model, "custom-model")
        self.assertEqual(client.pro_model, "custom-pro")

    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fake-deepseek-key"})
    def test_deepseek_provider(self):
        config = {"llm_provider": "deepseek"}
        client = build_llm_client(config)
        self.assertIsInstance(client, OpenAICompatibleClient)
        self.assertEqual(client.base_url, "https://api.deepseek.com/v1")
        self.assertEqual(client.api_key, "fake-deepseek-key")

    def test_local_provider_does_not_require_api_key(self):
        config = {"llm_provider": "local"}
        client = build_llm_client(config)
        self.assertIsInstance(client, OpenAICompatibleClient)
        self.assertIsNone(client.api_key)
        self.assertEqual(client.base_url, "http://localhost:11434/v1")

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            build_llm_client({"llm_provider": "not-a-real-provider"})


if __name__ == "__main__":
    unittest.main()
