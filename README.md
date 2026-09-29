# BidSmith: Personal AI Bid Agent for Freelancer.com

It finds Freelancer.com projects that match **your** profile, scores each one for fit, and writes a proposal
grounded in your real portfolio. It suggests a price and delivery time, then sends you the draft on
**WhatsApp** (or a mobile web dashboard). The bid is only placed when you tap **✅ Bid**.

```
Official Freelancer API → rule filter → fit score (0-100) → portfolio match (RAG) → price engine
   → AI draft → quality gate (clichés, client instructions, invented facts, length) → WhatsApp / dashboard
   → you approve → bid placed via API → logged in SQLite
```

## Quick start
```bash
pip install -r requirements.txt
python -m bidsmith setup     # paste your tokens (hidden), writes .env
python -m bidsmith check     # verifies them
python -m bidsmith demo      # offline demo on sample projects, no keys needed
pytest -q                    # 19 tests
```
Full setup (Freelancer token, WhatsApp Cloud API, AI key, hosting): **[docs/04-setup.md](docs/04-setup.md)**

## What makes it different from the 60 tools we researched
- **Account-safe:** it uses the official API only, never a browser bot. You approve every bid by default. Opt-in auto-bid has a daily cap and spacing.
- **No invented experience:** the quality gate blocks numbers or links that are not in your profile or the client's brief.
- **Catches hidden client instructions:** for example, if the brief says "start your bid with banana", the bot obeys, and the bid fails the check if the word is missing.
- **Prices each project:** based on budget, the average bid, your floor and your review count. It handles non-USD currencies.
- **Smart about your first jobs:** small budgets and new clients score higher while you have 0 reviews.

## Layout
| Path | What |
|---|---|
| `bidsmith/freelancer.py` | Official REST client (search, bid, self) |
| `bidsmith/filters.py`, `scoring.py`, `retrieval.py`, `pricing.py` | Filter → score → portfolio RAG → price |
| `bidsmith/proposal.py`, `quality.py`, `llm.py` | Writer (Gemini, OpenAI or Claude), quality gate, template fallback |
| `bidsmith/notify.py`, `web.py`, `app.py` | WhatsApp Cloud API, dashboard and webhook, actions and commands |
| `profile/owner_profile.yaml` | **Your** facts, portfolio, rates and search settings |

## Docs
- [00: Agent operating prompt](docs/00-AGENT-PROMPT.md)
- [01: Market research, 60 systems](docs/01-market-research.md)
- [02: Analysis and requirements](docs/02-analysis-and-requirements.md)
- [03: Your profile audit and rewrite](docs/03-profile-audit-and-rewrite.md)
- [04: Setup guide](docs/04-setup.md)
- [05: **Profile copy-paste pack**](docs/05-PROFILE-COPY-PASTE.md)
- [06: **Portfolio items**, form-ready](docs/06-PORTFOLIO-ITEMS.md) + 17 images in `profile/images/` (regenerate with `python tools/make_profile_images.py`)
