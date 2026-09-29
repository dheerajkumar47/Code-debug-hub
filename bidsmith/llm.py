"""Provider-agnostic LLM call (Gemini, OpenAI-compatible, Anthropic) over plain HTTP."""
from __future__ import annotations

import logging
import re

import httpx

log = logging.getLogger(__name__)

DEFAULT_MODELS = {
    "gemini": "gemini-flash-latest",  # auto-switches to a live model if Google retires a name
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
            raise LLMError(f"{self.provider} HTTP {r.status_code}: {r.text[:600]}")
        return r.json()

    def _gemini_base(self) -> str:
        return self.base_url or "https://generativelanguage.googleapis.com/v1beta"

    def _gemini_pick_model(self, error_text: str = "") -> str | None:
        """Find a working model: the one Google's error suggests, else the newest stable Flash model."""
        m = re.search(r"use (?:models/)?(gemini-[\w.\-]+)", error_text)
        if m:
            return m.group(1).rstrip(".")
        r = self._http.get(f"{self._gemini_base()}/models", params={"pageSize": 200},
                           headers={"x-goog-api-key": self.api_key})
        if r.status_code >= 400:
            return None
        names = []
        for mdl in r.json().get("models", []):
            name = mdl.get("name", "").split("/")[-1]
            if "generateContent" not in mdl.get("supportedGenerationMethods", []):
                continue
            if "flash" not in name or any(x in name for x in ("lite", "image", "tts", "live", "audio", "exp")):
                continue
            names.append(name)

        def rank(n: str):
            ver = [int(x) for x in re.findall(r"\d+", n.split("-flash")[0])] or [0]
            return ("preview" not in n, ver, "latest" in n)
        return max(names, key=rank) if names else None

    def _gemini(self, system, user, max_tokens, temperature):
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                # newer Gemini models "think" first; leave room so the answer isn't cut off
                "generationConfig": {"maxOutputTokens": max_tokens + 2048, "temperature": temperature}}
        headers = {"x-goog-api-key": self.api_key}
        url = lambda: f"{self._gemini_base()}/models/{self.model}:generateContent"  # noqa: E731
        for attempt in range(3):  # current model → model Google suggests → newest listed Flash model
            try:
                data = self._post(url(), headers, body)
                break
            except LLMError as e:
                if " 404" not in str(e) or attempt == 2:
                    raise
                new = self._gemini_pick_model(str(e) if attempt == 0 else "")
                if not new or new == self.model:
                    new = self._gemini_pick_model("") if attempt == 0 else None
                if not new or new == self.model:
                    raise
                log.warning("Gemini model %s unavailable, switching to %s", self.model, new)
                self.model = new
        parts = ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text:
            raise LLMError(f"gemini: empty response {str(data)[:200]}")
        return text

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
