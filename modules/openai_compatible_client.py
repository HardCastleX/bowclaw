"""
Cliente asincrono generico para APIs compatibles con el formato de OpenAI
(chat completions). Sirve para:
  - DeepSeek (api.deepseek.com/v1 - API oficial real)
  - Servidores independientes / open-source auto-hospedados que exponen el
    mismo formato: Ollama, LM Studio, vLLM, text-generation-webui, llama.cpp
    server, etc.
"""
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = (
    "Eres un analista de ingenieria inversa. Analiza el siguiente codigo "
    "decompilado y describe brevemente su proposito, posibles riesgos de "
    "seguridad y comportamiento notable:\n\n{chunk}"
)


class OpenAICompatibleClient:
    def __init__(
        self,
        base_url,
        model,
        api_key=None,
        pro_model=None,
        max_concurrency=2,
        max_retries=5,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.pro_model = pro_model or model
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_retries = max_retries

    def _build_url(self):
        return "%s/chat/completions" % self.base_url

    def _build_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer %s" % self.api_key
        return headers

    def _build_payload(self, chunk, use_pro=False):
        return {
            "model": self.pro_model if use_pro else self.model,
            "messages": [
                {"role": "user", "content": ANALYSIS_PROMPT.format(chunk=chunk)}
            ],
        }

    async def analyze_chunk(self, session, chunk, use_pro=False):
        url = self._build_url()
        payload = self._build_payload(chunk, use_pro=use_pro)

        async with self.semaphore:
            for attempt in range(1, self.max_retries + 1):
                wait_seconds = min(60, 5 * (2 ** (attempt - 1)))
                try:
                    async with session.post(
                        url,
                        headers=self._build_headers(),
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                        if response.status == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    wait_seconds = max(wait_seconds, float(retry_after))
                                except ValueError:
                                    pass
                        logger.warning(
                            "OpenAI-compatible request failed (status %s), attempt %s/%s, esperando %ss",
                            response.status, attempt, self.max_retries, wait_seconds,
                        )
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    logger.warning(
                        "OpenAI-compatible request error: %s, attempt %s/%s, esperando %ss",
                        exc, attempt, self.max_retries, wait_seconds,
                    )
                await asyncio.sleep(wait_seconds)

        raise RuntimeError(
            "OpenAI-compatible analysis failed after %s retries" % self.max_retries
        )

    async def analyze_all_chunks(self, chunks, use_pro=False):
        async with aiohttp.ClientSession() as session:
            tasks = [self.analyze_chunk(session, chunk, use_pro=use_pro) for chunk in chunks]
            return await asyncio.gather(*tasks, return_exceptions=True)
