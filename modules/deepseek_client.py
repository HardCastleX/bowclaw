"""Cliente asincrono para interactuar con la API de DeepSeek."""
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-coder"

ANALYSIS_PROMPT = (
    "Eres un analista de ingenieria inversa. Analiza el siguiente codigo "
    "decompilado y describe brevemente su proposito, posibles riesgos de "
    "seguridad y comportamiento notable:\n\n{chunk}"
)


class DeepSeekClient:
    def __init__(self, api_key, model=DEFAULT_MODEL, max_concurrency=5, max_retries=3):
        self.api_key = api_key
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_retries = max_retries

    def _build_headers(self):
        return {
            "Authorization": "Bearer %s" % self.api_key,
            "Content-Type": "application/json",
        }

    async def analyze_chunk(self, session, chunk):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": ANALYSIS_PROMPT.format(chunk=chunk)}
            ],
        }

        async with self.semaphore:
            for attempt in range(1, self.max_retries + 1):
                try:
                    async with session.post(
                        DEEPSEEK_API_URL,
                        headers=self._build_headers(),
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                        logger.warning(
                            "DeepSeek request failed (status %s), attempt %s/%s",
                            response.status, attempt, self.max_retries,
                        )
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    logger.warning(
                        "DeepSeek request error: %s, attempt %s/%s",
                        exc, attempt, self.max_retries,
                    )
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("DeepSeek analysis failed after %s retries" % self.max_retries)

    async def analyze_all_chunks(self, chunks):
        async with aiohttp.ClientSession() as session:
            tasks = [self.analyze_chunk(session, chunk) for chunk in chunks]
            return await asyncio.gather(*tasks, return_exceptions=True)
