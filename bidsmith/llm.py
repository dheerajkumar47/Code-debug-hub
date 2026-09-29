"""Provider-agnostic LLM call (Gemini, OpenAI-compatible, Anthropic) over plain HTTP."""
from __future__ import annotations

import logging
import re
import time

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
        self._sleep = time.sleep
        self.cooldown_until = 0.0  # after a busy streak we give the provider a break

    COOLDOWN_SECONDS = 90

    @property
    def cooling(self) -> bool:
        return time.time() < self.cooldown_until

    @property
    def enabled(self) -> bool:
        return self.provider in DEFAULT_MODELS and bool(self.api_key)

    def ping(self) -> str:
        """Quick start-up check, no retries: 'ok', 'busy', or the error text."""
        saved = self._sleep
        self._sleep = lambda s: None
        try:
            if self.provider == "gemini":
                body = {"contents": [{"role": "user", "parts": [{"text": "Say OK"}]}],
                        "generationConfig": {"maxOutputTokens": 2100}}
                r = self._http.post(f"{self._gemini_base()}/models/{self.model}:generateContent",
                                    headers={"x-goog-api-key": self.api_key}, json=body)
                if r.status_code in (429, 500, 502, 503, 504):
                    return "busy"
                if r.status_code == 404:  # retired name: let the normal path pick a live model
                    self.complete("Reply with one word.", "Say OK", max_tokens=50)
                    return "ok"
                return "ok" if r.status_code < 400 else f"HTTP {r.status_code}: {r.text[:200]}"
            self.complete("Reply with one word.", "Say OK", max_tokens=50)
            return "ok"
        except LLMError as e:
            return "busy" if any(c in str(e) for c in (" 503", " 429", " 500")) else str(e)
        finally:
            self._sleep = saved

    def complete(self, system: str, user: str, max_tokens: int = 700, temperature: float = 0.6) -> str:
        if not self.enabled:
            raise LLMError("LLM not configured")
        if self.cooling:
            raise LLMError(f"{self.provider} cooling down after being busy")
        fn = {"gemini": self._gemini, "openai": self._openai, "anthropic": self._anthropic}[self.provider]
        try:
            return fn(system, user, max_tokens, temperature).strip()
        except LLMError as e:
            if any(c in str(e) for c in (" 429", " 500", " 502", " 503", " 504")):
                self.cooldown_until = time.time() + self.COOLDOWN_SECONDS
            raise

    # ------------------------------------------------------------------
    def _post(self, url: str, headers: dict, body: dict) -> dict:
        for wait in (2, 6, 0):  # retry briefly when the provider is busy
            r = self._http.post(url, headers=headers, json=body)
            if r.status_code in (429, 500, 502, 503, 504) and wait:
                log.debug("%s busy (HTTP %s), retrying in %ss", self.provider, r.status_code, wait)
                self._sleep(wait)
                continue
            break
        if r.status_code >= 400:
            raise LLMError(f"{self.provider} HTTP {r.status_code}: {r.text[:600]}")
        return r.json()

    def _gemini_base(self) -> str:
        return self.base_url or "https://generativelanguage.googleapis.com/v1beta"

    def _gemini_pick_model(self, error_text: str = "", exclude: str = "") -> str | None:
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
            if "flash" not in name or name == exclude or \
                    any(x in name for x in ("image", "tts", "live", "audio", "exp", "embedding")):
                continue
            names.append(name)

        def rank(n: str):
            ver = [int(x) for x in re.findall(r"\d+", n.split("-flash")[0])] or [0]
            return ("preview" not in n, "lite" not in n, ver, "latest" in n)
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
                retired, busy = " 404" in str(e), any(c in str(e) for c in (" 503", " 429", " 500"))
                if not (retired or busy) or attempt == 2:
                    raise
                new = self._gemini_pick_model(str(e) if retired else "", exclude=self.model)
                if not new or new == self.model:
                    new = self._gemini_pick_model("", exclude=self.model)
                if not new or new == self.model:
                    raise
                log.info("Gemini model %s %s, switching to %s", self.model,
                            "unavailable" if retired else "busy", new)
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
