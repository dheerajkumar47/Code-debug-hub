"""Tiny TF-IDF + cosine retrieval over the portfolio (no vector DB needed)."""
from __future__ import annotations

import math
import re
from collections import Counter

from .config import PortfolioItem

_STOP = set("""a an and are as at be by for from has have i in is it its of on or our that the this to
we with you your will can need needs want looking someone who should must able project work job using
use also more than into about all any like get make new please""".split())

# Light normalisation so "chat bot" / "chatbot" / "bots" meet.
_SYNONYMS = {
    "bot": "chatbot", "bots": "chatbot", "chatbots": "chatbot", "assistant": "chatbot",
    "llms": "llm", "gpt": "llm", "chatgpt": "llm", "openai": "llm", "gemini": "llm", "claude": "llm",
    "agents": "agent", "agentic": "agent", "retrieval": "rag", "embeddings": "rag", "vector": "rag",
    "cctv": "camera", "cameras": "camera", "video": "camera", "detection": "detect", "detector": "detect",
    "yolov8": "yolo", "yolov5": "yolo", "yolov11": "yolo", "whatsapp": "whatsapp", "wa": "whatsapp",
    "automations": "automation", "automate": "automation", "workflow": "automation", "workflows": "automation",
    "dashboards": "dashboard", "scraping": "scrape", "scraper": "scrape",
}


def tokenize(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9+#.]+", text.lower())
    out = []
    for t in toks:
        t = t.strip(".")
        if len(t) < 2 or t in _STOP:
            continue
        out.append(_SYNONYMS.get(t, t))
    return out


class PortfolioIndex:
    def __init__(self, items: list[PortfolioItem]):
        self.items = items
        docs = [Counter(tokenize(i.text)) for i in items]
        n = max(len(docs), 1)
        df = Counter(t for d in docs for t in d)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vec(d) for d in docs]

    def _vec(self, counts: Counter) -> dict[str, float]:
        v = {t: (1 + math.log(c)) * self.idf.get(t, 1.0) for t, c in counts.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def search(self, text: str, k: int = 2) -> list[tuple[PortfolioItem, float]]:
        q = self._vec(Counter(tokenize(text)))
        scored = [(item, sum(q.get(t, 0.0) * w for t, w in vec.items()))
                  for item, vec in zip(self.items, self.vecs)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(i, round(s, 3)) for i, s in scored[:k] if s > 0]
