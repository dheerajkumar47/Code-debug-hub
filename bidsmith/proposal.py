"""Proposal writer: RAG over the portfolio + strict rules + quality gate with one retry."""
from __future__ import annotations

import logging
import re

from . import quality
from .config import Profile
from .models import Draft, Price, Project
from .retrieval import PortfolioIndex

log = logging.getLogger(__name__)

SYSTEM = """You are a senior freelance AI engineer writing a Freelancer.com proposal that wins the client's attention
in the first two lines. You write for ONE freelancer, described in FREELANCER FACTS and PROOF.

Hard rules:
- Use ONLY facts, projects and links from FREELANCER FACTS / PROOF. Never invent years, clients, metrics or reviews.
- Never copy the client's requirement as your own experience. If they ask for "5+ years of X", do NOT answer with
  years; show relevant proof instead. Never claim experience in a language or tool that is not in FREELANCER FACTS,
  skills or PROOF. If a required skill is missing, say honestly how your closest proven skill covers the need.
- {min_words}-{max_words} words and under {max_chars} characters. Plain text. Short paragraphs. "•" bullets allowed.
- Never start with "Re:", "Dear", "Hello Sir" or the project title. Never write "I hope", "I am excited/thrilled",
  "delve", "seamless", "leverage", "passionate", "cutting-edge", "look no further", "top-notch", "kindly".
- Sound like an expert talking to a client: specific, confident, calm. Match the client's language level.

Write it in this order:
1. Opening (1-2 sentences): if CLIENT NAME is given, start with "Hi <name>," on its own line. Then show you
   understood THEIR goal, using their words and one concrete detail from the brief. No self-introduction.
2. How I will build it: 3-5 bullets with concrete technical choices for THIS project (name the tools, e.g. FastAPI,
   LangGraph, pgvector, YOLO, WhatsApp Cloud API) and how each part solves a requirement from the brief.
3. Proof: the most relevant PROOF item - what it does and why it is close to their need - with its link.
4. Delivery: milestones inside {period} days (e.g. first working demo, then final version), what they receive
   (code, deployment, documentation).
5. Answer every CLIENT QUESTION directly. Obey every CLIENT INSTRUCTION exactly.
6. One or two sharp questions that show expertise (about their data, users, integrations or success criteria).
7. Close with a short call to action and sign as {signature}.
Output ONLY the proposal text."""

USER = """CLIENT NAME: {client_name}
PROJECT
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


# --- ready-made (no-AI) proposal: specific to the brief and the type of project -------------------------------
PLAYBOOKS = [
    ("voice", r"voice ?(ai|agent|bot|assistant)|phone (agent|assistant|calls?)|call(s|ing)? (agent|bot|automation)|"
              r"twilio|vapi|retell|ivr|speech|text.to.speech|tts|transcri",
     ["Define the call flows: greeting, the questions callers ask most, booking and hand-off to a person",
      "Connect telephony (Twilio or your provider) to fast speech-to-text, the LLM and natural text-to-speech",
      "Keep replies short and low-latency, with fallbacks when the caller is unclear",
      "Log every call with transcript and summary so your team can review and improve it"],
     ["Roughly how many calls a day, and in which languages?", "Should the agent book appointments or only answer?"]),
    ("automation", r"\bn8n\b|make\.com|integromat|zapier|workflow automation|automate (my|our|the)|automation workflow",
     ["Map your current process step by step and mark where AI adds value",
      "Build the workflow in n8n (or Make) with the AI steps calling OpenAI / Claude / Gemini",
      "Connect your apps (Sheets, CRM, email, WhatsApp) with error handling and retries",
      "Test with real data, then hand over with a short guide so your team can adjust it"],
     ["Which apps does the workflow start and end in?", "Is this already running somewhere, or built from scratch?"]),
    ("scraping", r"scrap(e|er|ing)|data extraction|extract (data|information)|crawl|lead (list|generation)|leads? from",
     ["Confirm the exact sources and the fields you need",
      "Build a robust extractor with retries, de-duplication and clean output",
      "Use AI to clean, classify or enrich the records where rules aren't enough",
      "Deliver CSV / Google Sheets output plus a script you can re-run any time"],
     ["Which websites or sources, and roughly how many records?", "One-time run, or should it update on a schedule?"]),
    ("whatsapp", r"whats ?app|messenger|instagram dm|receptionist|appointment|booking|customer support bot",
     ["Connect the official WhatsApp Business (Cloud) API and any other channels you use",
      "Teach the assistant your services, prices and FAQs so it answers like your team",
      "Add booking / CRM steps with confirmations and reminders",
      "Human hand-over plus a simple dashboard to watch every conversation"],
     ["Which channels do your customers use most today?", "Where are bookings or leads stored right now?"]),
    ("rag", r"\brag\b|knowledge base|pdfs?\b|documents?|docs\b|retrieval|vector|embedding|chat with|internal data|faq",
     ["Ingest and clean your documents with sensible chunking and metadata",
      "Hybrid search (vector + keyword) with source citations so answers stay grounded",
      "FastAPI backend with the LLM that fits your budget (OpenAI, Claude or Gemini) and guardrails",
      "Chat UI or widget, tested on real questions, then Docker deployment"],
     ["Roughly how many documents, and in which formats?", "Should every answer show its source?"]),
    ("vision", r"vision|image|video|camera|cctv|detect|yolo|opencv|ocr|recogni[sz]|track",
     ["Review sample images / video and agree on the accuracy target",
      "Build or fine-tune a YOLO + OpenCV pipeline for your exact objects and scenes",
      "Optimise for real-time speed and difficult cases (lighting, angles, occlusion)",
      "Deliver an API or dashboard with results, plus a short evaluation report"],
     ["Can you share a few sample images or clips?", "Will it run on a GPU server, a PC or an edge device?"]),
    ("agent", r"agent|agentic|automat|workflow|n8n|crewai|langgraph|langchain|tool|integration",
     ["Map the workflow step by step and define exactly what the AI may do on its own",
      "Build the agent with LangGraph / CrewAI and tool calls to your APIs and data",
      "Add guardrails, logging and human approval where mistakes would be costly",
      "Test on real cases, then deploy with monitoring"],
     ["Which systems or APIs must the agent connect to?", "Where should a human approve before the agent acts?"]),
    ("webapp", r"dashboard|web ?app|saas|admin panel|portal|next\.?js|react|full.?stack|frontend",
     ["Agree the screens and user roles, then a clickable first version early",
      "FastAPI (or Node) backend with clean REST APIs and a proper database",
      "React / Next.js frontend with the AI features built into the workflow, not bolted on",
      "Auth, testing and deployment, with documented code you fully own"],
     ["Who are the main users, and what do they do first after logging in?",
      "Do you already have designs, or should I propose the layout?"]),
    ("ml", r"machine learning|\bml\b|model|predict|forecast|classif|regression|anomaly|data scien|dataset",
     ["Explore and clean the data and agree on the success metric",
      "Build a strong baseline, then improved models, compared with clear metrics",
      "Package the best model behind a FastAPI endpoint",
      "Hand over code, notebook and a short results report"],
     ["How much labelled data is available?", "Which metric matters most to you?"]),
]
DEFAULT_PLAYBOOK = ("ai", "",
                    ["Confirm scope, inputs, outputs and what success looks like",
                     "Build the core AI feature with FastAPI and the right LLM for the job",
                     "Integrate it with your app and test with real examples",
                     "Deploy and hand over clean, documented code"],
                    ["What does success look like for you in the first week?",
                     "Is there an existing system this must fit into?"])

_REQ = re.compile(r"\b(need|needs|must|should|want|require|looking for|build|create|develop|integrate|"
                  r"able to|feature|goal|expect)\b", re.I)


def _playbook(p: Project):
    text = f"{p.title} {' '.join(p.skills)} {p.description[:1500]}".lower()
    return next((pb for pb in PLAYBOOKS if re.search(pb[1], text)), DEFAULT_PLAYBOOK)


def _requirements(p: Project, n: int = 3) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+|;|•|- ", p.description)
    out = []
    for s in parts:
        s = s.strip(" -*•\t")
        if len(s.split()) < 4 or s.endswith("?") or not _REQ.search(s):
            continue
        words = s.split()
        s = " ".join(words[:18]) + ("…" if len(words) > 18 else "")
        out.append(s[0].upper() + s[1:])
        if len(out) == n:
            break
    if not out:  # no "need/must" wording: use the first sentences of the brief
        for s in parts[:n]:
            s = s.strip(" -*•\t")
            if len(s.split()) >= 4 and not s.endswith("?"):
                words = s.split()
                out.append(" ".join(words[:18]) + ("…" if len(words) > 18 else ""))
    return out


def _phases(days: int) -> str:
    days = max(int(days or 1), 1)
    if days <= 2:
        return f"a working version within {days} day{'s' if days > 1 else ''}, then fixes from your feedback"
    demo = max(1, round(days * 0.4))
    return f"first working demo by day {demo}, final tested version by day {days}"


def template_bid(p: Project, profile: Profile, proof, price: Price, instr: dict, questions: list[str],
                 max_chars: int = 1500) -> str:
    """Ready-made proposal when the AI is unavailable: structured and specific to this brief."""
    _, _, steps, smart_qs = _playbook(p)
    reqs = _requirements(p)
    sign = profile.style.get("signature", profile.name)
    title = p.title.strip().rstrip(".")

    def build(n_req: int, n_steps: int, with_second_q: bool) -> str:
        out = []
        if instr.get("start_with"):
            out.append(instr["start_with"])
        elif p.client.name:
            out.append(f"Hi {p.client.name},")
        if reqs[:n_req]:
            out.append(f"I went through your brief for \"{title}\". The key points I noted:\n"
                       + "\n".join(f"• {r}" for r in reqs[:n_req]))
        else:
            out.append(f"I went through your brief for \"{title}\" and this is exactly the kind of system I build.")
        out.append("How I would build it:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(steps[:n_steps], 1)))
        if proof:
            item = proof[0][0]
            what = item.pitch or item.summary.strip().split(". ")[0].rstrip(".")
            link = f"\n{item.link}" if item.link else ""
            out.append(f"Closest work I have done: {what[0].lower() + what[1:]}.{link}".replace(
                "Closest work I have done: ", "Closest work I have done: I built ", 1))
        out.append(f"Delivery: {_phases(price.period_days)}. You get the full source code, deployment and "
                   f"clear documentation.")
        answers = []
        for q in questions[:2]:
            if re.search(r"timeline|how long|deadline|when can", q, re.I):
                answers.append(f"On \"{q}\": {price.period_days} days for a tested version.")
            else:
                answers.append(f"On \"{q}\": I will give you a concrete recommendation as soon as I know "
                               f"your data size and hosting, usually within the first call.")
        if answers:
            out.append("\n".join(answers))
        qs = smart_qs[:2] if with_second_q else smart_qs[:1]
        out.append("Quick question" + ("s" if len(qs) > 1 else "") + ": " + " ".join(qs))
        for t in instr.get("include", []):
            out.append(f"({t})")
        out.append(f"I can start right away. Send me a message and I will share a short plan for your case.\n\n{sign}")
        return "\n\n".join(out)

    for n_req, n_steps, q2 in ((3, 4, True), (2, 4, True), (2, 3, False), (1, 3, False), (0, 3, False)):
        text = build(n_req, n_steps, q2)
        if len(text) <= max_chars:
            return text
    return text[:max_chars]


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
    days = int(price.period_days or 0)
    return (price.amount, price.amount_usd, *range(1, days + 1))


def write(p: Project, profile: Profile, index: PortfolioIndex, price: Price, llm=None) -> Draft:
    style = profile.style
    proof = index.search(p.text, k=2)
    instr = quality.detect_instructions(p.description)
    questions = quality.detect_questions(p.description)
    corpus = profile.corpus

    text = None
    if llm is not None and getattr(llm, "enabled", False):
        system = SYSTEM.format(min_words=style.get("min_words", 120), max_words=style.get("max_words", 230),
                               max_chars=style.get("max_chars", 1500), tone=style.get("tone", "plain"),
                               period=price.period_days, signature=style.get("signature", profile.name))
        proof_txt = "\n".join(
            f"- {i.title}: {i.pitch or i.summary.strip()} Details: {i.summary.strip()} Stack: {', '.join(i.stack)}. "
            f"Result: {i.result} Link: {i.link or 'n/a'}"
            for i, _ in proof) or "- (no close match; rely on skills)"
        feedback = ""
        for attempt in range(2):
            user = USER.format(
                client_name=p.client.name or "unknown (no greeting name)", title=p.title, ptype=p.type, skills=", ".join(p.skills),
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
        text = template_bid(p, profile, proof, price, instr, questions, int(style.get("max_chars", 1500)))

    text = _obey_instructions(text, instr)
    report = quality.check(text, p, corpus, style, _numbers(price))
    return Draft(project_id=p.id, text=text, price=price, quality=report,
                 portfolio_used=[i.title for i, _ in proof], ai=ai)
