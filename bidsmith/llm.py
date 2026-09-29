"""Provider-agnostic LLM call (Gemini, OpenAI-compatible, Anthropic) over plain HTTP."""
from __future__ import annotations

import logging

import httpx

log = logging.getLogger(__name__)

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-sonnet-5-5",
}


class LLMError(RuntimeError):
    pass


class LLM:
    def __init__(self, provider: str, api_key: str, model: str = "", base_url: str = "",
                 timeout: float = 60.0, transport: httpx.BaseTransport | None = None):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model or DEFAULT_MODELS.get(self.provider, "")
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=timeout, transport=transport)

    @property
    def enabled(self) -> bool:
        return self.provider in DEFAULT_MODELS and bool(self.api_key)

    def complete(self, system: str, user: str, max_tokens: int = 700, temperature: float = 0.6) -> str:
        if not self.enabled:
            raise LLMError("LLM not configured")
        fn = {"gemini": self._gemini, "openai": self._openai, "anthropic": self._anthropic}[self.provider]
        return fn(system, user, max_tokens, temperature).strip()

    # ------------------------------------------------------------------
    def _post(self, url: str, headers: dict, body: dict) -> dict:
        r = self._http.post(url, headers=headers, json=body)
        if r.status_code >= 400:
            raise LLMError(f"{self.provider} HTTP {r.status_code}: {r.text[:300]}")
        return r.json()

    def _gemini(self, system, user, max_tokens, temperature):
        base = self.base_url or "https://generativelanguage.googleapis.com/v1beta"
        data = self._post(
            f"{base}/models/{self.model}:generateContent",
            {"x-goog-api-key": self.api_key},
            {"systemInstruction": {"parts": [{"text": system}]},
             "contents": [{"role": "user", "parts": [{"text": user}]}],
             "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}},
        )
        try:
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError) as e:
            raise LLMError(f"gemini: unexpected response {str(data)[:200]}") from e

    def _openai(self, system, user, max_tokens, temperature):
        base = self.base_url or "https://api.openai.com/v1"
        data = self._post(
            f"{base}/chat/completions",
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        )
        return data["choices"][0]["message"]["content"] or ""

    def _anthropic(self, system, user, max_tokens, temperature):
        base = self.base_url or "https://api.anthropic.com/v1"
        data = self._post(
            f"{base}/messages",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            {"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
             "system": system, "messages": [{"role": "user", "content": user}]},
        )
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
