# Freelancer.com Profile Audit and Rewrite: Dheeraj (@dheerajk85)

**Date:** 2026-09-29
**Inputs:**
- Your Freelancer.com profile screenshot
- GitHub `dheerajkumar47` (34 repos; the READMEs of 11 were read)
- The `Next-js-Portfolio` README
- 33 comparable AI/LLM freelancer profiles (listed in §2)

**Could not open:** LinkedIn, `pak-industry-insight.vercel.app` and freelancer.com pages. The sandbox proxy blocks them. Please check anything in this doc marked ⚠️.

---

## 1. Current profile: what you have

| Field | Now | Verdict |
|---|---|---|
| Headline | "AI Engineer \| AI Agents, LLM&bots,RAG & Automation" | ⚠️ Generic, with typos ("LLM&bots", missing spaces). It says nothing about outcomes. |
| Rate | **$10/hr** | ❌ Bottom of the market. It signals low quality, even for AI work. |
| Reviews / earnings | 0 / $0 / 0% | Normal at the start. Needs a first-win strategy (§6). |
| Bio | Long, well-structured; "What I build / Recent work / Tech stack / How I work" | ✅ Good bones. Too long before the value is clear, and the first 2 lines don't sell. |
| Portfolio | 4 items: Time-Series Anomaly, AI Stock Dashboard (PSX), AI QA Platform, AI Meeting Intelligence | ⚠️ Missing your **strongest and most marketable work** (see §4). |
| Experience | AI Engineer, Independent (Jan 2026–now); AI Engineer, Bitscollision (Jan–Dec 2025) | ✅ Good. Add measurable results. |
| Education | Iqra University, BS Software Engineering, 2021–2025 | ✅ |
| Certifications | "AI Training – Freelancer Global Fleet" only | ⚠️ Add Freelancer skill exams and 1–2 recognised certificates. |
| Qualifications / Publications / Articles | Empty | ⚠️ Easy wins (§5). |
| Cover photo | Default | ⚠️ Upload a branded banner. |
| References | "No references" | ❌ Ask your Bitscollision lead for a reference **this week**. |

### Things you've built that are missing from the profile (found on GitHub)
| Repo | What it is | Why it sells |
|---|---|---|
| **AI-receptionist** (Sep 2026) | An AI receptionist that answers customers on **WhatsApp, Messenger, Instagram and X**. Books appointments in Outlook through Microsoft Graph, replies with **Urdu/English voice notes** (Azure Speech), sends reminders, and has a Blazor dashboard. | WhatsApp and AI-receptionist jobs are **among the most-posted on Freelancer right now**. This is your #1 portfolio piece. |
| **Gumcorp** (factory tracking) | Reads live RTSP camera feeds. **YOLO** (CUDA) person detection plus **ArUco** marker ID and tracking, heatmaps, one MP4 recording per employee, a live dashboard and telemetry. | Matches the "50+ CCTV cameras" claim in your bio. Real computer vision in production. |
| **IntelliCourse** | A **LangGraph** router with 4 nodes (router, Pinecone retriever, Tavily web search, generator) running on FastAPI | A clean example of agentic RAG |
| **AI-Tutor** | Multimodal tutor with **per-user FAISS long-term memory**, LangChain function-calling agent, SSE streaming, JWT and rate limiting | Memory plus security are senior-level signals |
| **Interview-Pilot** | 4 AI agents (Resume Analyst, Tech Interviewer, Knowledge Assessor, HR Coach), **ATS scoring**; Gemini as the main model with Groq Llama 3.3 as fallback | Multi-agent work plus LLM fallback design |
| **NeuroSync-AI** | Voice journaling: transcription, emotion detection and mood trends (Gemini plus HuggingFace) | Voice-AI category |
| **tharthreads-app** | FastAPI batch image pipeline: background removal and catalog compositing, ZIP export | E-commerce automation |
| **ai-job-search** | A **Claude Code** agent framework that scrapes, ranks, tailors CVs, has a reviewer agent and prepares interviews | Shows you build *agents that do work*, not just chatbots |

### Inconsistencies to fix ⚠️
1. The PSX app is described as "**79 companies and 18 sectors**" on Freelancer but as "**113+ companies**" in the GitHub README. Pick the real current number and use it everywhere.
2. The PSX README says **Gemini + FastAPI + MongoDB**. The Freelancer text says "Claude, React, FastAPI, MongoDB, LLM". Make them match.
3. The GitHub profile README still presents you as "**VR, frontend, QA intern**" with an old LinkedIn URL (`dheeraj-kumar-b21a741a2`). You sent a different one (`softwareengineerdheerajkumar`). Rewrite the README as an AI engineer page and use one LinkedIn URL.
4. The portfolio README says the deployed URL is `dheerajkumar.vercel.app` (placeholder). The Freelancer bio shows another portfolio domain. Use **one** working portfolio URL.
5. The **Time-Series Anomaly** README reports no numbers. Add precision, recall, F1 and AUC from a real run. Clients trust numbers.
6. Your GitHub has about 20 old HTML/Java student repos (2023). **Pin your 6 best AI repos** and archive or hide the rest.

---

## 2. Benchmark: 33 comparable profiles

These are search-engine summaries of public profile snippets. Individual Freelancer.com profile pages were blocked, so most samples come from Upwork. The patterns carry over.

| # | Profile (platform, location) | Headline / positioning | Proof shown |
|---|---|---|---|
| 1 | Ignas V. (Upwork, Brazil) | "AI Agent Development Expert \| RAG, Python, LangChain, LLM AI Engineer" | Top Rated; B2B and enterprise |
| 2 | Ambrose K. (Upwork) | "Agentic AI Developer \| RAG, LangChain, LLM Fine-tuning, Workflow Automation" | $300K+, 500+ projects, 100% JSS |
| 3 | IIT Guwahati AI engineer (Upwork, India) | Agents, n8n, voice AI, RAG in production | 10,000+ hrs, 93 jobs, "LLM work since 2021" |
| 4 | Sardar I. (Upwork, Abbottabad PK) | "RAG & AI Chatbot Developer \| Private, On-Prem, **No Data Leaks**" | Niche: privacy |
| 5 | Muhammad A. (Upwork, Multan PK) | "AI Developer \| ChatBot (LLM, LangChain, OpenAI, RAG) \| AI Agent" | Top Rated; voice agents |
| 6 | Ans I. (Upwork, PK) | "AI Automation ~ Voice AI, Chatbots, RAG, Multi Agent Systems" | Top Rated; "4+ yrs projects, 1.5 yrs pro" (**honest framing of junior experience**) |
| 7 | Muhammad F. (Upwork, Lahore PK) | "AI Integration Expert \| Sr. Full-Stack Developer \| Agents, RAG & LLMs" | Top Rated |
| 8 | Viktor S. (Upwork, India) | "AI Automation & Agents Engineer \| LangChain \| n8n \| DevOps \| 15 Yrs" | Years as the hook |
| 9 | Jumabek A. (Upwork, S. Korea) | "Expert Vetted AI Engineer \| Top 1 percent \| PhD \| 12 years" | Credentials as the hook |
| 10 | Faizan A. (Upwork, Rawalpindi PK) | "AI Developer \| Python & LLM Engineer \| RAG Systems & FastAPI" | 2+ yrs |
| 11 | Abdul W. (Upwork, Lahore PK) | "AI Agent Developer \| LangChain \| LangGraph \| RAG Systems \| FastAPI" | Production workloads |
| 12 | Abdullah A. (Upwork, Lahore PK) | "Python FastAPI Engineer \| RAG Chatbots + AI Search \| **B2B SaaS**" | "answers **with citations**" |
| 13 | Muhammad Atif I. (Upwork, Lahore PK) | "AI Engineer \| AI App Developer \| Python Backend Developer" | Generic (a weak example) |
| 14 | Muhammad A. (Upwork, Islamabad PK) | "Full Stack AI Engineer \| React Node \| Python FastAPI \| LangChain RAG" | Full-stack angle |
| 15 | M Wajeeh U. (Upwork, Islamabad PK) | "Machine Learning Engineer \| GenAI, RAG Systems, FastAPI, Data Analytics" | — |
| 16 | **Samran E. (Upwork, Karachi PK)** | "Senior AI Engineer \| ML Expert \| Computer Vision \| Chatbot Developer" | "**shipped 50+** AI agent and RAG chatbots", 5+ yrs |
| 17 | **Moaaz (Upwork, Karachi PK)** | "AI Engineer building **production-ready** AI agents (RAG & Voice AI)" | 3+ yrs |
| 18 | Top Rated Plus RAG engineer (Upwork, India) | "private **document brains** over Google Drive/SharePoint" | $300K+, 85 contracts, 4,638 hrs |
| 19 | AI OCR / RAG architect (Upwork, India) | "turns messy documents and **unreliable chatbots** into deterministic SaaS workflows" | Problem-first headline |
| 20 | IIT Guwahati "GraphRAG" engineer (Upwork, India) | "AI Engineer & Full-Stack \| Agentic Workflows, **GraphRAG**" | Trendy niche term |
| 21 | n8n and voice AI engineer (Upwork) | "AI Agents, n8n Automation, Voice AI Agents" | 100% JSS, 27 projects, 331 hrs |
| 22 | Automation architect (Upwork, US) | "Top 1% in Automation, **500+ systems delivered**" | Volume proof |
| 23 | Agents and chatbots engineer (Upwork) | "AI Agents, Chatbots & business automation (n8n, Claude, OpenAI)" | $300K+, 208 jobs |
| 24 | YOLO CV specialist (Upwork, Expert-Vetted) | "YOLO Detection, Pose, Tracking \| Sports, **CCTV**, Retail, Healthcare AI" | Industry list |
| 25 | Torchstack founder (Upwork, Expert-Vetted) | "Fractional CTO" | Leadership angle |
| 26 | $2M+ AI expert (Upwork, Expert-Vetted) | Full-time AI freelancer | Earnings proof |
| 27 | bohdan38 (Freelancer.com) | Portfolio item "Custom AI Chatbot with RAG" | Portfolio with a clear title |
| 28 | "The Sharp's AI" portfolio (Freelancer.com) | Python, Azure, OpenAI, Pinecone, LangGraph | Stack in the title |
| 29 | AI agent dev, 4.8★ / 136 reviews (Freelancer.com) | AI agent development | Review volume |
| 30 | AI agent dev, 4.9★ / 820+ reviews, 99% completion (Freelancer.com) | AI agent development | Completion rate |
| 31 | tangramua (Freelancer.com agency) | Company profile, portfolio and reviews | Agency format |
| 32 | 200+ engineer agency (Freelancer.com, US/UAE/PK) | AI and full-stack agency | Team size |
| 33 | WhatsApp n8n chatbot portfolio (Freelancer.com #10821623) | "WhatsApp chatbot \| n8n agent \| bot" | Niche-titled portfolio item |

### Patterns among the winners
1. **The headline follows "Role | 2–4 specialties | differentiator".** The best ones name an **outcome or niche** ("No Data Leaks", "with citations", "production-ready", "document brains").
2. **Proof comes in the first 2 lines:** numbers (projects shipped, years, companies served) or a sharp niche.
3. **Honest framing of junior experience works** (Ans I.: "4+ yrs projects, 1.5 yrs professional"). Never inflate.
4. **Portfolio titles are search keywords** ("Custom AI Chatbot with RAG", "WhatsApp chatbot | n8n agent").
5. **Pakistani engineers in Karachi and Lahore compete on production-readiness plus FastAPI plus RAG plus voice.** Your AI receptionist and CV tracking work set you apart.
6. **Rates:** Freelancer.com GenAI developers average about $20–100/hr. AI-agent job bids average about **$32/hr** (310 bids on one project). Beginner Python/AI jobs sit at about $15–25/hr. **$10 is below the beginner band.**

---

## 3. Rewrite: copy and paste

### Headline (pick one; trim if Freelancer's character limit cuts it)
- **A (recommended):** `AI Engineer | RAG Chatbots, AI Agents & WhatsApp AI`
- **B:** `AI Agents & RAG Chatbots | Python, FastAPI, LangGraph`
- **C (computer-vision-heavy):** `AI Engineer | RAG, AI Agents & Computer Vision (YOLO)`

### Hourly rate
- **Now:** **$15/hr** (in the beginner band, without looking cheap).
- **After 3–5 five-star reviews:** $20–25/hr. **After 10 or more:** $30 or more.
- For fixed-price bids, the bot works out a price for each project, never below your floor (`profile/owner_profile.yaml`).

### Summary / bio (about 230 words, outcome first)
```
I build AI systems that work in production — not demos that break on real data.

What I can build for you
• RAG chatbots that answer from YOUR documents, website or database — with citations and guardrails so they don't make things up.
• AI agents that do real work: classify, route, extract data, call your APIs and automate multi-step workflows (LangGraph, LangChain, CrewAI).
• WhatsApp / Messenger / Instagram AI assistants that answer customers 24/7, book appointments and reply with voice notes (English & Urdu).
• Computer vision: real-time detection and tracking on CCTV/RTSP feeds (YOLO, OpenCV), dashboards and reports.
• Clean Python backends: FastAPI, REST APIs, PostgreSQL/MongoDB, Docker — deployed on AWS, Azure, Render or Vercel.

Recent work
• AI receptionist for small businesses — WhatsApp + Messenger + Instagram + X, Outlook booking, voice replies.
• Real-time factory tracking — YOLO + ArUco on live CCTV, per-employee trails, heatmaps, live dashboard.
• PSX market intelligence platform — live data + AI-generated market summaries and SWOT per company.
• Multi-agent interview platform — 4 AI agents, ATS scoring, Gemini with Groq fallback.

How I work
I start with a short call or message to agree scope, show progress early (demo within the first days), write clear docs, and hand over clean code you own. Fixed-price or hourly — your choice.

Send me your use case and I'll reply with a clear plan, timeline and price.
```
*(⚠️ Make sure every line is true. Change the PSX company count to the real number.)*

### Experience entries: add results
- **AI Engineer, Independent (Jan 2026 to now):** "Built and deployed an AI receptionist (WhatsApp/Messenger/IG/X, Outlook booking, Urdu/English voice) and a real-time CCTV tracking system (YOLO + ArUco, 50+ cameras ⚠️ confirm number)."
- **AI Engineer, Bitscollision (2025):** keep it, and add **one** number (such as users, documents indexed, latency, or accuracy "90%+ ⚠️") and name one client industry.

---

## 4. Portfolio: target 8 items (you have 4)

Use this format in every description: **Problem → What I built → Stack → Result/metric → Link.**
Title each one like a search query, and add a 1200×900 thumbnail with the title plus a screenshot.

| # | Title (use exactly) | Source | Status |
|---|---|---|---|
| 1 | **AI Receptionist: WhatsApp, Instagram & Messenger AI Agent with Booking** | AI-receptionist | 🆕 add first |
| 2 | **Real-Time CCTV Employee Tracking: YOLO + ArUco Computer Vision** | Gumcorp | 🆕 |
| 3 | **RAG Chatbot with LangGraph Router: Pinecone + Web Search (FastAPI)** | IntelliCourse | 🆕 |
| 4 | **AI Stock Market Intelligence Dashboard (PSX): Live Data + AI SWOT** | PAK_Industry_Insight | ✅ keep; fix numbers |
| 5 | **Multi-Agent AI Interview Platform: ATS Scoring + 4 AI Agents** | Interview-Pilot | 🆕 |
| 6 | **AI Meeting Intelligence: Whisper Transcripts → Grounded Q&A** | existing | ✅ keep |
| 7 | **AI QA Platform: Agents Generate Test Cases from Tickets** | existing | ✅ keep |
| 8 | **Time-Series Anomaly Detection: Prophet + Isolation Forest (FastAPI)** | existing | ✅ keep; add metrics |
| (9) | AI Tutor with Long-Term Memory (FAISS, multimodal) | AI-Tutor | optional |

A screen recording (30–60 seconds, silent plus captions) of #1 and #2 will do more than any text.

---

## 5. Quick wins this week (checklist)
- [ ] Change the headline, the rate to $15 and the bio (§3).
- [ ] Add portfolio items 1, 2, 3 and 5 (§4).
- [ ] Upload a cover banner: "RAG Chatbots · AI Agents · WhatsApp AI · Computer Vision".
- [ ] Complete **all** verifications (ID, payment, phone, email, Facebook/LinkedIn).
- [ ] Pass 2–3 **Freelancer skill exams** (Python, AI or ML ones). The badges show on bids.
- [ ] Request a **reference** from your Bitscollision manager.
- [ ] Skills: add up to your limit, most important first: *Python, AI Development, Machine Learning, LangChain, Large Language Models, RAG, AI Chatbot, AI Agents, FastAPI, OpenAI, Computer Vision, OpenCV, YOLO, Automation, WhatsApp API, n8n, Docker, MongoDB, PostgreSQL, React.js*.
- [ ] GitHub: pin 6 AI repos, rewrite the profile README, add metrics to the anomaly README.
- [ ] Use one portfolio URL and one LinkedIn URL everywhere.
- [ ] Publish 1 Freelancer **article**, e.g. "How I built a WhatsApp AI receptionist that books appointments". It fills an empty section and helps you show up in search.

## 6. First-review strategy (0 → 5 reviews)
1. Bid on **small fixed-price jobs ($30–$250)** in your strongest niches: RAG chatbot, WhatsApp bot, a FastAPI fix, a YOLO fix. Clients risk less on a newcomer.
2. Bid **early**. Aim to be in the first 10 bids (the bot is built for this).
3. Offer a **tiny free proof** inside the bid, e.g. "here's the 3-step architecture for your case", **not** free work.
4. Over-deliver and ask for the review at handover.
5. The bot's fit-scoring gives **0-review-friendly projects** a bonus (small budget, few bids, a client new to hiring).
