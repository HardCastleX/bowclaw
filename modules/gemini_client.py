"""Cliente asincrono para interactuar con la API de Gemini (Google AI Studio)."""
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3.5-flash"
DEFAULT_PRO_MODEL = "gemini-3.1-pro-preview"

ANALYSIS_PROMPT = (
    "Eres un analista de ingenieria inversa. Analiza el siguiente codigo "
    "decompilado y describe brevemente su proposito, posibles riesgos de "
    "seguridad y comportamiento notable:\n\n{chunk}"
)


class GeminiClient:
    def __init__(
        self,
        api_key,
        model=DEFAULT_MODEL,
        pro_model=DEFAULT_PRO_MODEL,
        max_concurrency=5,
        max_retries=3,
    ):
        self.api_key = api_key
        self.model = model
        self.pro_model = pro_model
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_retries = max_retries

    def _build_url(self, model):
        return "%s/%s:generateContent" % (GEMINI_API_BASE, model)

    def _build_headers(self):
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _build_payload(self, chunk, use_pro=False):
        payload = {
            "contents": [
                {"parts": [{"text": ANALYSIS_PROMPT.format(chunk=chunk)}]}
            ]
        }
        if use_pro:
            payload["generationConfig"] = {
                "thinkingConfig": {"thinkingLevel": "high"}
            }
        return payload

    async def analyze_chunk(self, session, chunk, use_pro=False):
        model = self.pro_model if use_pro else self.model
        url = self._build_url(model)
        payload = self._build_payload(chunk, use_pro=use_pro)

        async with self.semaphore:
            for attempt in range(1, self.max_retries + 1):
                try:
                    async with session.post(
                        url,
                        headers=self._build_headers(),
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                        logger.warning(
                            "Gemini request failed (status %s), attempt %s/%s",
                            response.status, attempt, self.max_retries,
                        )
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    logger.warning(
                        "Gemini request error: %s, attempt %s/%s",
                        exc, attempt, self.max_retries,
                    )
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("Gemini analysis failed after %s retries" % self.max_retries)

    async def analyze_all_chunks(self, chunks, use_pro=False):
        async with aiohttp.ClientSession() as session:
            tasks = [self.analyze_chunk(session, chunk, use_pro=use_pro) for chunk in chunks]
            return await asyncio.gather(*tasks, return_exceptions=True)
