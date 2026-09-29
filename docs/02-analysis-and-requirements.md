# Analysis, Gaps and Requirements: BidSmith (personal Freelancer.com bid agent)

Based on the 60 systems in [01-market-research.md](01-market-research.md).

---

## 1. What the market does: 7 shared patterns

| Pattern | Seen in | Verdict for us |
|---|---|---|
| **Keyword or skill discovery** (poll new projects) | Almost all | ✅ Required. Use the **official API**, not scraping. |
| **Rule filters** (budget, currency, country, project type, excluded words, client rating, payment verified, bid count) | FABB, Bidman, FreeBID, n8n #6048 | ✅ Required, as stage 1 of the filter. |
| **AI fit scoring** (score 1–10 or 0–100, then gate) | UpHunt, Upwex, GetMany, n8n #19333 | ✅ Required. This is what stops bids being wasted. |
| **AI proposal writing** | Everyone | ✅ Required. Grounded in the owner's real portfolio. |
| **Portfolio or past-work matching** (RAG) | BidPilotPro, PitchPilot, n8n #8015, the RAG MVP repo | ✅ Required. The biggest quality lever. |
| **Human approval in chat** (Telegram buttons) | n8n #6048, UpHunt, Vollna | ✅ Default mode. |
| **Full auto-submit, 24/7** | FABB, Bidswala, Autobidbot, BidMasterPro, Lancer | ⚠️ Opt-in only, capped and paced. |

## 2. Evidence on what wins

- **Speed matters.** Clients on Freelancer.com get 30 or more bids within about 60 seconds of posting. Early bids get read first.
- **Heavy AI text loses.** GigRadar looked at 133,872 Upwork proposals. Hand-edited templates got a 17% higher reply rate than GPT-4o auto-bidders (8.13% vs 7.13%). Proposals with **3 or more AI clichés got a 4.17% reply rate, and those with 4 or more got 0%**. Skipping human editing dropped reply rates from about 24% to almost zero (agency study).
- **Clients set traps.** For example, "start your reply with the word banana". The system must **detect and obey instructions buried in the brief**.
- **Specific proof beats generic claims.** Relevant case studies win about 55–65% of the time, generic testimonials about 40–45%, and no testimonials about 30–35%. These are vendor-published figures. Treat them as directional.
- **Competition cuts win rate.** As a sole bidder you win about 70–85%. Against 5 or more bidders, about 20–35%. So bid count should feed into the fit score.
- **Detection is about behaviour, not text.** Platforms flag submits less than about 4 seconds apart, headless-browser fingerprints, identical templates, and non-browser API bursts. Drafting text with AI is allowed. **Unattended bulk submission is the risk.**

## 3. Gaps in existing tools (our opportunity)

1. **Random template rotation** (FABB) and **one fixed bid amount** (n8n #6048). No project-specific pricing.
2. **Keyword-only matching**. No understanding of what the project actually needs, or whether the owner can deliver it.
3. **No grounding.** Most tools can invent experience, which is risky when the client asks for proof.
4. **Hosted tools want your password** (BidMasterPro, Bidman). That is a security and ToS risk.
5. **No learning loop.** Almost nobody feeds reply or award results back into scoring and prompts.
6. **No cliché or quality gate** before sending.
7. **Client questions and hidden instructions are ignored.** Only GetMany flags questions.
8. **No bid-budget awareness.** Tools spend limited bids on low-probability projects.

**Our edge:** a *personal*, safe, API-only agent that bids **less often but better**. It scores fit, grounds every claim in the owner's real work, prices each project on its own, and learns from outcomes.

---

## 4. Requirements

### 4.1 Functional (MoSCoW)

**MUST (MVP)**
- F1. OAuth2 connection to the Freelancer.com API. Store tokens, refresh them, and never store the password.
- F2. **Owner profile and knowledge base**: skills, hourly and fixed rate floors, bio, portfolio items (title, stack, result, link), past reviews, preferred and blocked categories, languages, and timezone.
- F3. **Discovery**: poll active projects every 1–5 minutes by skill IDs and keywords. Deduplicate them and skip projects already bid on.
- F4. **Stage-1 rule filter**: budget range, currency, country allow and block lists, fixed or hourly, max bid count, client payment verified, client rating, excluded words, NDA or IP handling (**never auto-sign**).
- F5. **Stage-2 AI fit score (0–100) with reasons**. Inputs: skill overlap, how deliverable the work is, budget vs rate floor, client quality, competition (bid count and average bid), recency, and red flags (such as "test task for free", off-platform contact, or an unrealistic scope).
- F6. **Proposal generator** (RAG over the portfolio) that follows the rules in `00-AGENT-PROMPT.md`. It detects client questions and hidden instructions and answers them.
- F7. **Price and duration engine**: `max(rate_floor, f(budget range, estimated hours, competitor average bid, fit score))`, with an explanation.
- F8. **Quality gate**: cliché scan, check that every claim appears in the knowledge base, length limits, and at least 2 brief specifics mentioned. Regenerate if the draft fails.
- F9. **Telegram approval card** showing the project summary, score and reasons, price, period and draft. Buttons: ✅ Bid · ✏️ Edit · 🔁 Regenerate · ⏭ Skip.
- F10. **Place the bid through the API** after approval. Log it.
- F11. **Database log** of projects, scores, drafts, the final text, price, and status (pending, replied, awarded, lost).

**SHOULD (v1.1)**
- F12. **Award tracker**: poll bids and notify on award or reply, with one-tap accept (as in n8n #6048).
- F13. **Dashboard**: bids used and remaining, reply rate, award rate, earnings, cost per win, and breakdowns by category and price band.
- F14. **Learning loop**: projects that won or got replies become few-shot examples. Tune the score weights using outcomes.
- F15. **Opt-in auto-submit** only when score is at least X and budget is at least Y. Daily cap, random spacing of at least 60–180 seconds, quiet hours.
- F16. **Bid-budget manager**: spend the remaining bid allowance on the highest expected value first.
- F17. Suggest paid upgrades (highlight or sealed) for top-score projects.

**COULD (later)**
- F18. Auto-reply drafts for client messages (the inbox assistant).
- F19. Attachments: a mini plan document or a Mermaid diagram for large projects (as in n8n #6174).
- F20. Short video intro script for the owner to record.
- F21. Multi-platform adapters (Upwork, PeoplePerHour, Guru).
- F22. Interview or call prep notes when a client replies.

### 4.2 Non-functional
- **N1 Safety:** respect API rate limits. At most N bids per hour (configurable). Always add random delays. No headless browser for submission.
- **N2 Security:** secrets in `.env` or a secret manager. Encrypt tokens at rest. The approval bot only answers the owner's Telegram chat ID.
- **N3 Latency:** from project posted to Telegram card in **90 seconds or less** (speed wins).
- **N4 Cost:** LLM cost of $0.01 or less per scored project, using a cheap model for scoring and a strong model only for drafts that pass the gate.
- **N5 Reliability:** idempotent jobs, a retry queue, and a persistent "already seen" set.
- **N6 Observability:** structured logs, plus an error alert to Telegram.
- **N7 Portability:** runs on a $5 VPS or free tier using Docker.

### 4.3 Success metrics
- Reply rate of 15% or more, award rate of 5% or more on bids placed, fewer than 5% of bids spent on projects the owner would have skipped, and 30 seconds or less of owner time per approval.

---

## 5. Recommended architecture

```
          ┌───────────── Scheduler (every 1–5 min) ─────────────┐
          ▼                                                      │
 Freelancer API ──► Discovery ──► Rule filter ──► AI fit scorer ─┤ (score < T → archive)
 (official OAuth)                                                ▼
                         Knowledge base (profile + portfolio + past wins)
                                   │  RAG
                                   ▼
                          Proposal + price engine ──► Quality gate ──(fail→regen)
                                                           │
                                                           ▼
                                  Telegram approval card  [Bid|Edit|Regen|Skip]
                                                           │ approve
                                                           ▼
                                       Freelancer API: place bid ──► DB (SQLite/Postgres)
                                                                          │
                                        Award/reply tracker ◄─────────────┘ ──► Dashboard + learning loop
```

**Proposed stack:** Python 3.12, the official `freelancersdk` or direct REST calls, FastAPI (webhooks and dashboard API), APScheduler, SQLite first (Postgres later), `python-telegram-bot`, an LLM through one provider-agnostic interface (Claude or OpenAI; a cheap model for scoring, a strong model for writing), and simple embeddings (or TF-IDF) for portfolio retrieval. Docker Compose to deploy.
*Alternative:* build the MVP quickly in **n8n**, extending template #6048 with scoring, RAG and a quality gate. It is faster to start with but harder to test and extend.

## 6. Build roadmap
1. **Week 1:** OAuth plus discovery plus rule filter plus DB; Telegram alerts only (no bidding).
2. **Week 2:** knowledge base plus fit scorer plus proposal generator plus quality gate; drafts sent to Telegram.
3. **Week 3:** approval and bid placement through the API; award and reply tracker.
4. **Week 4:** dashboard, metrics, learning loop; optional capped auto-submit.

## 7. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Account restriction for automation | Official API only, approval by default, caps, pacing, no browser bots |
| Hallucinated experience | Grounding check against the knowledge base; block unsupported claims |
| Bids wasted | Two-stage filter, expected-value ranking, bid-budget manager |
| Generic AI tone | Cliché blacklist, specifics check, few-shot examples from past wins |
| Scam or low-quality clients | Payment verified, rating and history checks, red-flag detector |
| API changes or limits | Adapter layer; Apify scraper as a read-only fallback |

## 8. Questions for the owner (needed before building)
1. Your main skills and categories, and your hourly and fixed-price floors.
2. Your Freelancer.com membership plan (it sets your bid limit).
3. 5–15 portfolio items with results and links, plus your best past reviews.
4. Approval-only, or auto-submit for very high scores?
5. Which LLM provider or API key you prefer (Claude, OpenAI, or local).
6. Hosting: your own VPS, a free tier, or local PC? Stack: Python code, or n8n first?

### Answers (2026-09-29, from your profile, GitHub and messages)
| # | Question | Answer used in the build |
|---|---|---|
| 1 | Skills and rate floors | AI engineer: RAG, agents, WhatsApp AI, computer vision, FastAPI. Floors: **$15/hr**, **$30 fixed**, target $20/hr (see `profile/owner_profile.yaml` and doc 03). |
| 2 | Membership plan | **Still unknown.** It decides your monthly bid count. Tell me and I'll set `MAX_BIDS_PER_DAY` to match. |
| 3 | Portfolio | 9 items pulled from your profile and GitHub (AI Receptionist, CCTV tracking, IntelliCourse RAG, PSX, Interview-Pilot, AI Tutor, Anomaly, Meeting AI, QA). |
| 4 | Approval mode | **Approval-only by default.** Auto-bid is available but off. |
| 5 | LLM | Provider-agnostic. **Gemini recommended to start** (free tier). OpenAI, Claude, Groq and OpenRouter also supported. |
| 6 | Stack and hosting | Python code (not n8n). Your PC plus a Cloudflare tunnel, or a free always-on VM. **WhatsApp replaces Telegram** (Telegram needs a VPN for you). |
