"""AI writer for outreach messages: every key in .env, OpenAI → Claude → Gemini → Groq, each backing up the last."""
from __future__ import annotations

import os
import re

from .llm import LLM, LLMChain


def _key(name: str) -> str:
    v = os.environ.get(name, "").strip().strip('"').strip("'")
    parts = re.split(r"\s+", v)
    return max(parts, key=len) if v else ""  # tolerate pasted extra text around the key


def build_llm():
    found: dict[str, LLM] = {}
    for name, env in (("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY"), ("gemini", "GEMINI_API_KEY")):
        if _key(env):
            found[name] = LLM(name, _key(env))
    if _key("LLM_FALLBACK_KEY"):
        found["groq"] = LLM("openai", _key("LLM_FALLBACK_KEY"), os.environ.get("LLM_FALLBACK_MODEL", ""),
                            os.environ.get("LLM_FALLBACK_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"))
    order = [x.strip() for x in os.environ.get("AI_ORDER", "openai,anthropic,gemini,groq").split(",")]
    chain = [found[n] for n in order if n in found] + [v for n, v in found.items() if n not in order]
    if not chain:
        return None
    return chain[0] if len(chain) == 1 else LLMChain(chain)
