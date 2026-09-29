"""Quality gate: catches the things that make clients ignore a bid."""
from __future__ import annotations

import re

from .models import Project, QualityReport
from .retrieval import tokenize

CLICHES = [
    "i hope this message finds you", "i hope this finds you", "i am thrilled", "i'm thrilled", "i am excited",
    "i'm excited", "delve", "seamless", "leverage", "dear hiring manager", "i came across your",
    "i have carefully read", "i've carefully read", "look no further", "passionate", "cutting-edge",
    "cutting edge", "rest assured", "top-notch", "top notch", "game-changer", "game changer",
    "in today's fast-paced", "as an ai", "dedicated professional", "hard-working", "hardworking",
    "100% satisfaction", "i am the perfect", "i'm the perfect", "best fit for this", "tailored solution",
    "elevate", "unlock the power", "robust and scalable", "dear sir", "dear client", "kindly",
    "i can do this job", "i have read your project description",
]

# e.g. "start your bid with the word banana", "begin your proposal with 'blue'"
_START_RE = re.compile(
    r"(?:start|begin)\s+(?:your|the)\s+(?:bid|proposal|reply|response|message|application|cover letter)\s+"
    r"with\s+(?:the\s+(?:word|phrase|code)\s+)?[\"'“‘]?([A-Za-z0-9][\w\- ]{0,30}?)[\"'”’]?(?=[\s.,!;:)]|$)",
    re.I)
# e.g. "include the word 'pineapple' in your bid", "mention the code XJ-12"
_INCLUDE_RE = re.compile(
    r"(?:include|mention|write|put|use)\s+(?:the\s+)?(?:word|phrase|code|keyword)\s+"
    r"[\"'“‘]?([A-Za-z0-9][\w\-]{0,30})[\"'”’]?", re.I)


def detect_instructions(description: str) -> dict:
    """Hidden instructions clients use to filter out bots."""
    start = None
    m = _START_RE.search(description)
    if m:
        start = m.group(1).strip()
    include = [x.strip() for x in _INCLUDE_RE.findall(description)]
    if start and start in include:
        include.remove(start)
    return {"start_with": start, "include": include}


def detect_questions(description: str, limit: int = 5) -> list[str]:
    parts = re.split(r"(?<=[?.!])\s+|\n+", description)
    qs = [q.strip(" -•*\t") for q in parts if q.strip().endswith("?") and len(q.strip()) > 8]
    return qs[:limit]


def _specific_terms(p: Project) -> set[str]:
    """Distinctive words from the brief that a tailored bid should echo."""
    generic = {"chatbot", "llm", "agent", "ai", "app", "website", "system", "develop", "developer",
               "build", "create", "help", "freelancer", "python", "need", "want", "experience"}
    words = tokenize(p.title) + [w for s in p.skills for w in tokenize(s)] + tokenize(p.description[:1500])
    return {w for w in words if len(w) > 3 and w not in generic}


def check(text: str, p: Project, profile_corpus: str, style: dict,
          allowed_numbers: tuple = ()) -> QualityReport:
    issues, warnings = [], []
    low = text.lower()
    words = len(text.split())
    min_w, max_w = int(style.get("min_words", 70)), int(style.get("max_words", 170))
    max_chars = int(style.get("max_chars", 1500))

    if len(text) > max_chars:
        issues.append(f"{len(text)} chars > {max_chars} limit")
    if words < min_w:
        issues.append(f"too short ({words} words < {min_w})")
    elif words > max_w + 40:
        issues.append(f"too long ({words} words > {max_w})")
    elif words > max_w:
        warnings.append(f"a bit long ({words} words)")

    found = [c for c in CLICHES if c in low]
    if len(found) >= 2:
        issues.append(f"AI clichés: {', '.join(found)}")
    elif found:
        warnings.append(f"cliché: {found[0]}")

    terms = _specific_terms(p)
    echoed = {w for w in tokenize(text) if w in terms}
    if len(echoed) < 2:
        issues.append("does not mention project specifics")

    instr = detect_instructions(p.description)
    if instr["start_with"] and not low.lstrip(" \"'").startswith(instr["start_with"].lower()):
        issues.append(f"client asked to start with '{instr['start_with']}'")
    for token in instr["include"]:
        if token.lower() not in low:
            issues.append(f"client asked to include '{token}'")

    # Grounding: numbers/URLs in the bid must exist in the profile, the brief, or the price.
    allowed = (profile_corpus + "\n" + p.text).lower()
    price_bits = {str(int(float(n))) for n in allowed_numbers if n}
    allowed_plain = allowed.replace(",", "")
    for num in set(re.findall(r"\b\d[\d,.]*\+?%?", text)):
        core = num.rstrip("+%.,").replace(",", "")
        if len(core) < 2 or core in price_bits:
            continue
        if not re.search(rf"(?<![\d.]){re.escape(core)}(?![\d])", allowed_plain):
            issues.append(f"unsupported number '{num}' (not in profile/brief)")
    for url in set(re.findall(r"https?://[^\s)\]>\"']+", text)):
        url = url.rstrip(".,;:")
        if url.lower() not in allowed:
            issues.append(f"unknown link {url}")

    if "?" not in text:
        warnings.append("no clarifying question")

    return QualityReport(passed=not issues, issues=issues, warnings=warnings)
