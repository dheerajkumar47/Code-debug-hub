"""Proposal writer: RAG over the portfolio + strict rules + quality gate with one retry."""
from __future__ import annotations

import logging
import re

from . import quality
from .config import Profile
from .models import Draft, Price, Project
from .retrieval import PortfolioIndex

log = logging.getLogger(__name__)

SYSTEM = """You write winning Freelancer.com bids for one specific freelancer.
Hard rules:
- Use ONLY facts, numbers, projects and links given in FREELANCER FACTS / PROOF. Never invent experience, years, client names or metrics.
- {min_words}-{max_words} words, under {max_chars} characters. Plain text, no markdown headings, no emojis.
- No greeting fluff. Banned phrases: "I hope this finds you well", "I am thrilled/excited", "delve", "seamless", "leverage", "passionate", "cutting-edge", "look no further", "top-notch", "Dear Sir".
- Tone: {tone}. Match the client's language level.
Structure:
1. Hook: restate the client's actual problem in one line using THEIR specifics.
2. Proof: the most relevant 1-2 PROOF items with what they did (include the link if given).
3. Plan: 3-4 short numbered steps for THIS project.
4. Answer every CLIENT QUESTION briefly. Obey every CLIENT INSTRUCTION exactly.
5. One smart clarifying question.
6. Close with timeline ({period} days) and sign as {signature}.
Output ONLY the bid text."""

USER = """PROJECT
Title: {title}
Type: {ptype} | Budget: {budget} | Skills: {skills}
Description:
{description}

CLIENT QUESTIONS: {questions}
CLIENT INSTRUCTIONS: {instructions}

FREELANCER FACTS
{headline}
{facts}

PROOF (most relevant portfolio items)
{proof}

OUR PRICE: {price} for {period} days.
{feedback}"""


def _instructions_text(instr: dict) -> str:
    out = []
    if instr.get("start_with"):
        out.append(f"Start the bid with the exact word(s): {instr['start_with']}")
    for t in instr.get("include", []):
        out.append(f"Include the word: {t}")
    return "; ".join(out) or "none"


def template_bid(p: Project, profile: Profile, proof, price: Price, instr: dict, questions: list[str]) -> str:
    """No-LLM fallback. Plain but specific; the owner edits before sending."""
    lines = []
    if instr.get("start_with"):
        lines.append(instr["start_with"])
    title = p.title.strip().rstrip(".")
    if proof:
        item = proof[0][0]
        first = item.summary.strip().split(". ")[0].rstrip(".")
        link = f"\n{item.link}" if item.link else ""
        lines.append(f"Re: {title} - I have built a closely related system and can start right away.")
        lines.append(f"{item.title}: {first}.{link}")
    else:
        lines.append(f"Re: {title} - this matches my day-to-day work ({', '.join(p.skills[:3])}).")
    lines.append("Plan: 1) confirm scope, data and access, 2) build a working first version, "
                 "3) test it with your real examples, 4) deploy and hand over clean, documented code.")
    for q in questions[:2]:
        if re.search(r"timeline|how long|deadline|when can", q, re.I):
            lines.append(f"On \"{q}\" - {price.period_days} days for a working, tested version.")
        else:
            lines.append(f"On \"{q}\" - I will answer this in detail in chat once I see your setup.")
    for t in instr.get("include", []):
        lines.append(f"({t})")
    lines.append("Quick question: what does a successful result look like for you in the first week?")
    lines.append(f"I can deliver in {price.period_days} days. — {profile.style.get('signature', profile.name)}")
    return "\n\n".join(lines)


def _obey_instructions(text: str, instr: dict) -> str:
    """Guarantee the client's hidden instructions are followed, even if the AI forgot."""
    start = instr.get("start_with")
    if start and not text.lower().lstrip(" \"'").startswith(start.lower()):
        text = f"{start}\n\n{text}"
    missing = [t for t in instr.get("include", []) if t.lower() not in text.lower()]
    if missing:
        text = text.rstrip() + "\n\n(" + ", ".join(missing) + ")"
    return text


def _numbers(price: Price) -> tuple:
    return (price.amount, price.amount_usd, price.period_days)


def write(p: Project, profile: Profile, index: PortfolioIndex, price: Price, llm=None) -> Draft:
    style = profile.style
    proof = index.search(p.text, k=2)
    instr = quality.detect_instructions(p.description)
    questions = quality.detect_questions(p.description)
    corpus = profile.corpus

    text = None
    if llm is not None and getattr(llm, "enabled", False):
        system = SYSTEM.format(min_words=style.get("min_words", 70), max_words=style.get("max_words", 170),
                               max_chars=style.get("max_chars", 1500), tone=style.get("tone", "plain"),
                               period=price.period_days, signature=style.get("signature", profile.name))
        proof_txt = "\n".join(
            f"- {i.title}: {i.summary.strip()} Stack: {', '.join(i.stack)}. Result: {i.result} Link: {i.link or 'n/a'}"
            for i, _ in proof) or "- (no close match; rely on skills)"
        feedback = ""
        for attempt in range(2):
            user = USER.format(
                title=p.title, ptype=p.type, skills=", ".join(p.skills),
                budget=f"{p.budget_min:.0f}-{p.budget_max:.0f} {p.currency}",
                description=p.description[:4000],
                questions="; ".join(questions) or "none", instructions=_instructions_text(instr),
                headline=profile.headline, facts="\n".join(f"- {f}" for f in profile.facts),
                proof=proof_txt, price=f"{price.amount:.0f} {price.currency}", period=price.period_days,
                feedback=feedback)
            try:
                text = llm.complete(system, user)
            except Exception as e:
                log.warning("AI busy, using the ready draft for now (%s)", " ".join(str(e).split())[:90])
                text = None
                break
            report = quality.check(text, p, corpus, style, _numbers(price))
            if report.passed:
                break
            feedback = "PREVIOUS DRAFT FAILED CHECKS — fix these: " + "; ".join(report.issues)

    ai = bool(text)
    if not text:
        text = template_bid(p, profile, proof, price, instr, questions)

    text = _obey_instructions(text, instr)
    report = quality.check(text, p, corpus, style, _numbers(price))
    return Draft(project_id=p.id, text=text, price=price, quality=report,
                 portfolio_used=[i.title for i, _ in proof], ai=ai)
