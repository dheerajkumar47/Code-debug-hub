"""Stage 2: fit score 0-100 with human-readable reasons."""
from __future__ import annotations

import json
import logging
import re
import time

from .config import Profile
from .models import Project, ScoreResult
from .retrieval import PortfolioIndex, tokenize

log = logging.getLogger(__name__)

RED_FLAGS = [
    (r"\bfree (test|trial|sample)\b|\bunpaid\b|\bwithout pay", "asks for free/unpaid work"),
    (r"(contact|message|add) me (on|via) (whatsapp|telegram|skype|email)|\bmy (whatsapp|telegram)\b",
     "wants off-platform contact"),
    (r"\b(homework|exam|quiz answers|thesis)\b", "academic work"),
    (r"\bvery (low|small|tight) budget\b|\bcheap(est)?\b", "price-shopping client"),
    (r"\bclone of (facebook|uber|amazon|airbnb)\b|\blike (uber|facebook|amazon)\b", "huge scope, likely small budget"),
]


# Freelancer's own skill names → the words we use in the profile.
ALIASES = {
    "artificial intelligence": "ai development", "ai": "ai development", "ai development": "ai development",
    "chatgpt": "openai", "openai api": "openai", "gpt-4": "openai", "gpt": "openai",
    "machine learning (ml)": "machine learning", "ml": "machine learning",
    "chatbot": "ai chatbot", "ai chatbot development": "ai chatbot", "chatbot development": "ai chatbot",
    "natural language processing": "nlp", "large language model": "large language models", "llm": "large language models",
    "generative ai": "large language models", "genai": "large language models", "prompt engineering": "large language models",
    "ai agent development": "ai agents", "agentic ai": "ai agents", "ai agents": "ai agents",
    "retrieval augmented generation": "rag", "retrieval-augmented generation": "rag",
    "api": "rest api", "api development": "rest api", "api integration": "rest api", "restful api": "rest api",
    "whatsapp": "whatsapp api", "whatsapp business api": "whatsapp api", "whatsapp bot": "whatsapp api",
    "image processing": "computer vision", "object detection": "computer vision", "video processing": "computer vision",
    "automation": "automation", "workflow automation": "automation", "ai automation": "automation",
    "google gemini": "gemini", "anthropic claude": "claude", "react": "react.js", "reactjs": "react.js",
    "node.js": "node.js", "data science": "machine learning", "deep learning": "machine learning",
    "tensorflow": "tensorflow", "pytorch": "pytorch", "django": "rest api", "flask": "rest api",
    # automation platforms, voice AI and data work (Freelancer skill names)
    "n8n": "n8n", "n8n automation": "n8n", "make.com": "make.com", "make": "make.com", "integromat": "make.com",
    "speech recognition": "speech recognition", "voice recognition": "speech recognition",
    "speech to text": "speech recognition", "transcription": "speech recognition", "whisper": "speech recognition",
    "text to speech": "text to speech", "voice ai": "voice ai", "ai voice agent": "voice ai",
    "voice agent": "voice ai", "vapi": "voice ai", "retell ai": "voice ai", "elevenlabs": "text to speech",
    "twilio": "twilio", "web scraping": "data extraction", "data scraping": "data extraction",
    "data extraction": "data extraction", "scrapy": "data extraction", "beautifulsoup": "data extraction",
    "ai integration": "ai development", "ai model integration": "ai development", "ai automation": "automation",
    "fine tuning": "large language models", "fine-tuning": "large language models",
    "hugging face": "large language models", "huggingface": "large language models",
    "llama": "large language models", "mistral": "large language models", "deepseek": "large language models",
    "dialogflow": "ai chatbot", "botpress": "ai chatbot", "voiceflow": "ai chatbot", "manychat": "ai chatbot",
    "ai chatbot": "ai chatbot", "conversational ai": "ai chatbot", "ocr": "computer vision",
    "optical character recognition": "computer vision", "facial recognition": "computer vision",
    "next.js": "next.js", "nextjs": "next.js", "fastapi": "fastapi", "streamlit": "streamlit",
}


def _norm(skill: str) -> str:
    s = skill.lower().strip()
    if s in ALIASES:
        return ALIASES[s]
    s2 = re.sub(r"\s*\(.*?\)", "", s).strip()          # "machine learning (ml)" → "machine learning"
    return ALIASES.get(s2, s2)


def _skill_score(p: Project, profile: Profile) -> tuple[float, list[str]]:
    mine = {_norm(s) for s in profile.all_skills}
    primary = {_norm(s) for s in profile.skills_primary}
    tags = p.skills
    hits = [t for t in tags if _norm(t) in mine]
    prim_hits = [t for t in tags if _norm(t) in primary]
    ratio = len(hits) / len(tags) if tags else 0.0
    # Keyword hits in text for skills the project didn't tag.
    text_toks = set(tokenize(p.text))
    kw_hits = [s for s in profile.skills_primary if set(tokenize(s)) and set(tokenize(s)) <= text_toks]
    # What matters is how many of YOUR skills the project needs, not how many other skills it also lists.
    score = min(len(hits), 3) * 7 + 8 * ratio + min(len(prim_hits), 2) * 1.5 + min(len(kw_hits), 4) * 1.5
    reasons = []
    if hits:
        reasons.append(f"skills match {len(hits)}/{len(tags)}: {', '.join(hits[:5])}")
    elif kw_hits:
        reasons.append(f"keywords match: {', '.join(kw_hits[:4])}")
    else:
        reasons.append("no skill overlap")
    return min(score, 35.0), reasons


def _budget_score(p: Project, profile: Profile) -> tuple[float, str]:
    top = p.budget_max_usd
    if p.type == "hourly":
        if top >= profile.target_hourly_usd:
            return 20, f"hourly up to ${top:.0f} ≥ target"
        if top >= profile.hourly_floor_usd:
            return 12, f"hourly up to ${top:.0f} ≥ floor"
        return 0, f"hourly ${top:.0f} below floor"
    if top >= 500:
        return 20, f"budget up to ${top:.0f}"
    if top >= 150:
        return 16, f"budget up to ${top:.0f}"
    if top >= profile.fixed_floor_usd:
        # Small jobs are good for first reviews.
        return 12 if profile.reviews_count < 5 else 7, f"small budget ${top:.0f} (good for first reviews)"
    return 0, f"budget ${top:.0f} below floor"


def _competition_score(p: Project) -> tuple[float, str]:
    n = p.bid_count
    pts = 15 if n < 5 else 12 if n < 15 else 8 if n < 30 else 4 if n < 50 else 1
    return pts, f"{n} bids so far"


def _client_score(p: Project, profile: Profile) -> tuple[float, str]:
    c = p.client
    pts, notes = 0.0, []
    if c.payment_verified:
        pts += 6
        notes.append("payment verified")
    if c.reviews:
        if c.rating >= 4.5:
            pts += 6
        elif c.rating >= 4.0:
            pts += 3
        notes.append(f"client {c.rating:.1f}★ ({c.reviews} reviews)")
        pts += 3 if c.reviews >= 5 else 1
    else:
        # New clients rarely filter out 0-review freelancers.
        pts += 4 if profile.reviews_count < 5 else 1
        notes.append("new client")
    return min(pts, 15), ", ".join(notes)


def _freshness_score(p: Project, now: float) -> tuple[float, str]:
    if not p.time_submitted:
        return 5, "age unknown"
    mins = (now - p.time_submitted) / 60
    pts = 10 if mins < 10 else 8 if mins < 30 else 5 if mins < 120 else 2
    return pts, f"posted {int(mins)} min ago" if mins < 120 else f"posted {mins / 60:.0f} h ago"


def red_flags(p: Project) -> list[str]:
    text = p.text.lower()
    return [label for pat, label in RED_FLAGS if re.search(pat, text)]


# Your core specialties. A project must need at least one of these to reach you;
# generic tags like "Automation", "Python" or "Script" alone are not enough.
CORE_SKILLS = {"ai development", "ai chatbot", "ai agents", "large language models", "rag", "langchain",
               "langgraph", "openai", "gemini", "claude", "computer vision", "opencv", "yolo", "machine learning",
               "nlp", "whatsapp api", "crewai", "llamaindex", "pytorch", "tensorflow", "speech recognition",
               "text to speech", "voice ai", "n8n", "make.com"}
CORE_TITLE = re.compile(r"\b(ai|a\.i\.|llm|llms|gpt|chat ?gpt|chat ?bot|chatbot|agent|agents|agentic|rag|langchain|"
                        r"langgraph|openai|gemini|claude|deepseek|llama|machine learning|ml|deep learning|"
                        r"computer vision|vision|yolo|opencv|nlp|whatsapp|voice ?bot|voice ai|voice agent|ocr|"
                        r"detection|embedding|embeddings|vector|n8n|make\.com|speech|transcription|transcribe|"
                        r"text.to.speech|tts|fine.?tun(e|ing)|prompt)\b", re.I)

# Not your field even when tagged with an AI skill: job roles (bidding / account / sales / marketing work),
# content & media creation, and scraping-only jobs...
OFF_FIELD = re.compile(
    r"\b(proposal writ\w*|bidder|bidding|bid writ\w*|account manag\w*|portfolio manag\w*|profile manag\w*|"
    r"virtual assistant|personal assistant|\bva\b|sales (rep\w*|executive|manager|partner|agent needed|person)|"
    r"business develop\w*|\bbde\b|cold call\w*|telemarket\w*|recruit\w*|digital marketing|social media (manag\w*|"
    r"market\w*|post\w*)|marketing (manag\w*|specialist|expert|executive)|seo|content (writ\w*|creat\w*)|"
    r"copywrit\w*|ghostwrit\w*|article|blog|video (edit\w*|generat\w*|creat\w*|production)|ai video|"
    r"youtube|tiktok|reels?|shorts|thumbnail|voice ?over|ai art|image generat\w*|midjourney|graphic design\w*|"
    r"logo|data entry|scrap(e|er|ers|ing)|selenium|crawler|feedback needed|usability|user research|survey|"
    r"beta test\w*|testers? needed|professionals?:)\b", re.I)
# ...unless the title clearly asks for real AI engineering.
STRONG_AI = re.compile(r"\b(llm|llms|(chat ?)?gpt[- ]?(api|integration)|chat ?bot|chatbot|agent|agents|agentic|rag|"
                       r"langchain|langgraph|"
                       r"openai|gemini|claude|machine learning|deep learning|computer vision|yolo|opencv|nlp|"
                       r"voice ai|voice agent|n8n|fine.?tun(e|ing)|api integration)\b", re.I)


def has_core_need(p: Project) -> bool:
    if OFF_FIELD.search(p.title) and not STRONG_AI.search(p.title):
        return False
    return any(_norm(t) in CORE_SKILLS for t in p.skills) or bool(CORE_TITLE.search(p.title))


def heuristic_score(p: Project, profile: Profile, index: PortfolioIndex, now: float | None = None) -> ScoreResult:
    now = now or time.time()
    s1, r1 = _skill_score(p, profile)
    s2, r2 = _budget_score(p, profile)
    s3, r3 = _competition_score(p)
    s4, r4 = _client_score(p, profile)
    s5, r5 = _freshness_score(p, now)
    top = index.search(p.text, k=1)
    s6 = min(5.0, (top[0][1] * 12) if top else 0.0)
    r6 = f"best proof: {top[0][0].title}" if top else "no matching portfolio item"
    flags = red_flags(p)
    total = s1 + s2 + s3 + s4 + s5 + s6 - 12 * len(flags)
    if s1 < 5:  # cannot deliver → cap hard
        total = min(total, 35)
    if not has_core_need(p):  # not an AI / ML / vision / chatbot project → never a card
        total = min(total, 45)
        r1 = r1 + ["no core AI skill needed"]
    score = int(max(0, min(100, round(total))))
    return ScoreResult(score=score, reasons=r1 + [r2, r3, r4, r5, r6], red_flags=flags)


SCORE_PROMPT = """You judge whether a freelancer should bid on a project.
Freelancer profile:
{profile}

Project:
Title: {title}
Budget: {budget}
Skills: {skills}
Description:
{description}

Reply ONLY with JSON: {{"score": 0-100, "can_deliver": true/false, "reason": "<one sentence>"}}
Score = probability this freelancer can deliver well AND win at this budget."""


def llm_refine(result: ScoreResult, p: Project, profile: Profile, llm) -> ScoreResult:
    """Optional: blend heuristic with an LLM judgement (cheap model)."""
    prompt = SCORE_PROMPT.format(
        profile=f"{profile.headline}\nSkills: {', '.join(profile.all_skills)}\nFacts: {' '.join(profile.facts)}",
        title=p.title, budget=f"{p.budget_min:.0f}-{p.budget_max:.0f} {p.currency} ({p.type})",
        skills=", ".join(p.skills), description=p.description[:3000])
    try:
        raw = llm.complete("You are a strict, concise evaluator.", prompt, max_tokens=200)
        data = json.loads(re.search(r"\{.*\}", raw or "", re.S).group(0))
        llm_score = int(data.get("score", result.score))
        if data.get("can_deliver") is False:
            llm_score = min(llm_score, 30)
        blended = round(0.5 * result.score + 0.5 * llm_score)
        return ScoreResult(blended, result.reasons + [f"AI judge {llm_score}: {data.get('reason', '')}"],
                           result.red_flags)
    except Exception as e:  # never let the judge break the pipeline
        log.warning("LLM score failed: %s", e)
        return result
