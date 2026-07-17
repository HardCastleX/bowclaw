"""Cliente asincrono para interactuar con la API de Gemini (Google AI Studio)."""
import asyncio
import logging

import aiohttp

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_PRO_MODEL = "gemini-3-flash-preview"

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
        max_concurrency=2,
        max_retries=5,
        verbose=False,
    ):
        self.api_key = api_key
        self.model = model
        self.pro_model = pro_model
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_retries = max_retries
        self.verbose = verbose

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
            thinking_config = {"thinkingLevel": "high"}
            if self.verbose:
                thinking_config["includeThoughts"] = True
            payload["generationConfig"] = {"thinkingConfig": thinking_config}
        return payload

    def _extract_text(self, data):
        """Separa las partes de razonamiento ('thought') de la respuesta final.
        Si verbose esta activo, loguea el razonamiento; siempre retorna solo
        el texto de la respuesta final."""
        parts = data["candidates"][0]["content"]["parts"]
        answer_parts = []
        thought_parts = []
        for part in parts:
            text = part.get("text", "")
            if part.get("thought"):
                thought_parts.append(text)
            else:
                answer_parts.append(text)

        if self.verbose and thought_parts:
            logger.info("[gemini-thinking] %s", "\n".join(thought_parts))

        return "".join(answer_parts)

    async def analyze_chunk(self, session, chunk, use_pro=False):
        model = self.pro_model if use_pro else self.model
        url = self._build_url(model)
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
                            return self._extract_text(data)
                        if response.status == 429:
                            retry_after = response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    wait_seconds = max(wait_seconds, float(retry_after))
                                except ValueError:
                                    pass
                        logger.warning(
                            "Gemini request failed (status %s), attempt %s/%s, esperando %ss",
                            response.status, attempt, self.max_retries, wait_seconds,
                        )
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    logger.warning(
                        "Gemini request error: %s, attempt %s/%s, esperando %ss",
                        exc, attempt, self.max_retries, wait_seconds,
                    )
                await asyncio.sleep(wait_seconds)

        raise RuntimeError("Gemini analysis failed after %s retries" % self.max_retries)

    async def analyze_all_chunks(self, chunks, use_pro=False):
        async with aiohttp.ClientSession() as session:
            tasks = [self.analyze_chunk(session, chunk, use_pro=use_pro) for chunk in chunks]
            return await asyncio.gather(*tasks, return_exceptions=True)
