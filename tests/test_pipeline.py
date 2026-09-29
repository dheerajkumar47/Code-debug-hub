from .conftest import NOW, FakeLLM


def test_pipeline_routes_projects(make_bot, projects):
    bot = make_bot(list(projects.values()), score_threshold=60)
    stats = bot.process(list(projects.values()), NOW)
    assert stats["new"] == 6
    statuses = {pid: bot.store.get_project(pid)["status"] for pid in projects}
    assert statuses[40100001] == "pending"
    assert statuses[40100002] == "pending"
    assert statuses[40100004] == "pending"
    assert statuses[40100003] == "filtered"
    assert statuses[40100006] == "filtered"
    assert statuses[40100005] in ("low_score", "filtered")
    assert len(bot.rec.cards) == stats["pending"] == 3
    # second run: nothing new
    assert bot.process(list(projects.values()), NOW)["new"] == 0


def test_template_draft_obeys_client_instruction(make_bot, projects):
    bot = make_bot()
    bot.process([projects[40100002]], NOW)
    d = bot.store.get_draft(40100002)
    assert d["text"].lower().startswith("banana")
    assert "ai receptionist" in d["text"].lower() and "github.com/dheerajkumar47/AI-receptionist" in d["text"]


def test_llm_retry_on_failed_quality(make_bot, projects):
    bad = "I am thrilled to leverage seamless synergy. " * 12
    good = ("You need a RAG chatbot over ~800 internal PDFs that cites sources and doesn't hallucinate. "
            "I built a RAG Chatbot with a LangGraph router (Pinecone + FastAPI): "
            "https://github.com/dheerajkumar47/IntelliCourse\n"
            "Plan: 1) ingest and chunk the PDFs with metadata, 2) hybrid retrieval with citations, "
            "3) FastAPI + React chat widget, 4) Docker deploy and docs. For the vector database I'd use pgvector "
            "if you already run Postgres, otherwise FAISS. Do the PDFs contain scanned pages? — Dheeraj")
    llm = FakeLLM([bad, good])
    bot = make_bot(llm=llm)
    bot.process([projects[40100001]], NOW)
    assert len(llm.calls) == 2 and "FAILED CHECKS" in llm.calls[1]
    assert bot.store.get_draft(40100001)["text"] == good


def test_approve_edit_skip_and_commands(make_bot, projects):
    bot = make_bot()
    bot.process([projects[40100001], projects[40100004]], NOW)

    reply, _ = bot.handle_button("edit:40100001")
    assert "Send the new proposal" in reply
    reply, show = bot.handle_command("My own text about the RAG chatbot for internal PDFs with FastAPI.")
    assert show == 40100001 and "updated" in reply
    assert bot.store.get_draft(40100001)["text"].startswith("My own text")

    assert bot.handle_command("price 40100001 400 10")[0].startswith("💲")
    assert bot.handle_button("approve:40100001")[0].startswith("✅")
    bid = bot.client.bids[0]
    assert bid["project_id"] == 40100001 and bid["amount"] == 400 and bid["period"] == 10
    assert "Already" in bot.approve(40100001)

    assert bot.handle_command("skip 40100004")[0].startswith("⏭")
    assert bot.store.get_project(40100004)["status"] == "skipped"
    assert "pending" not in bot.store.stats()
    assert bot.handle_command("pause")[0].startswith("⏸") and bot.run_once() == {"paused": True}


def test_auto_submit_is_opt_in_and_capped(make_bot, projects):
    p = projects[40100001]
    bot = make_bot(auto_submit=False)
    bot.process([p], NOW)
    assert bot.client.bids == []

    bot = make_bot(auto_submit=True, auto_submit_min_score=1, max_bids_per_day=0)
    bot.process([p], NOW)
    assert bot.client.bids == []  # cap of 0 blocks it


def test_ai_forgetting_client_instruction_is_fixed_automatically(make_bot, projects):
    forgot = ("You need a WhatsApp assistant for clinic FAQs and bookings into Google Calendar in English and Urdu. "
              "I built an AI Receptionist on WhatsApp with booking and voice replies. Plan: 1) map FAQs, "
              "2) connect WhatsApp Business API and Google Calendar, 3) test bookings, 4) deploy. "
              "Which calendar holds staff availability? — Dheeraj")
    bot = make_bot(llm=FakeLLM([forgot]))
    bot.process([projects[40100002]], NOW)
    assert bot.store.get_draft(40100002)["text"].lower().startswith("banana")


def test_hidden_projects_threshold_recheck_and_draft_anyway(make_bot, projects):
    bot = make_bot()
    bot.process(list(projects.values()), NOW)
    reasons, weak, soft = bot.hidden_summary()
    assert any("logo design" in k for k, _ in reasons) and weak
    weak_id = weak[0]["id"]
    assert bot.draft_anyway(weak_id).startswith("✍")
    assert bot.store.get_project(weak_id)["status"] == "pending" and bot.store.get_draft(weak_id)
    # raising the bar hides nothing already pending, lowering it + recheck surfaces weak ones
    assert "95" in bot.set_threshold(200)
    bot.set_threshold(30)
    assert bot.threshold() == 30
    bot.recheck_hidden()
    assert all(r["status"] != "low_score" for r in bot.store.list_projects(("low_score",), 50))


def test_crowded_but_great_fit_is_shown_not_lost(make_bot, projects):
    import dataclasses
    crowded = dataclasses.replace(projects[40100001], id=555, bid_count=95)
    bot = make_bot()
    bot.process([crowded], NOW)
    row = bot.store.get_project(555)
    assert row["status"] == "filtered" and row["score"] >= 70
    _, _, soft = bot.hidden_summary(now=NOW)
    assert [r["id"] for r in soft] == [555]
    old = dataclasses.replace(crowded, id=556, time_submitted=int(NOW - 7 * 86400))
    bot.process([old], NOW)
    assert 556 not in [r["id"] for r in bot.hidden_summary(now=NOW)[2]]  # a week old: not worth a bid
    assert bot.draft_anyway(555).startswith("✍")


def test_live_cycle_finds_new_and_removes_cards_past_50_bids(make_bot, projects):
    import dataclasses, time as _t
    fresh = [dataclasses.replace(projects[i], time_submitted=int(_t.time()) - 120) for i in (40100001, 40100004)]
    bot = make_bot()
    bot.client.projects = fresh
    live = {40100001: {"bid_count": 9, "open": True}, 40100004: {"bid_count": 12, "open": True}}
    bot.client.refresh = lambda ids: {i: live[i] for i in ids if i in live}
    st = bot.run_live()
    assert st["pending"] == 2 and st["expired"] == 0 and bot.store.kv_get("last_poll")
    live[40100004] = {"bid_count": 51, "open": True}      # crossed 50 → disappears
    live[40100001] = {"bid_count": 14, "open": True}
    st = bot.run_live()
    assert st["expired"] == 1
    ids = [c["id"] for c in bot.live_state()["cards"]]
    assert ids == [40100001]
    assert bot.live_state()["cards"][0]["bids"] == 14     # bid count kept up to date
    live[40100001] = {"bid_count": 14, "open": False}     # client closed it → disappears
    bot.run_live()
    assert bot.live_state()["cards"] == []


def test_background_draft_shows_card_instantly_then_polishes(make_bot, projects):
    import threading
    gate = threading.Event()

    class SlowLLM(FakeLLM):
        def complete(self, *a, **k):
            gate.wait(5)
            return super().complete(*a, **k)

    good = ("You need a RAG chatbot over ~800 internal PDFs that cites sources. I built a RAG Chatbot with a "
            "LangGraph router (Pinecone + FastAPI): https://github.com/dheerajkumar47/IntelliCourse\n"
            "Plan: 1) ingest PDFs, 2) retrieval with citations, 3) FastAPI + React widget, 4) Docker deploy. "
            "Which vector database do you prefer? — Dheeraj")
    bot = make_bot(llm=SlowLLM([good]), background_drafts=True)
    bot.process([projects[40100001]], NOW)
    card = bot.live_state()["cards"][0]
    assert card["drafting"] and card["text"]          # ready draft already there
    gate.set()
    bot._drafter.shutdown(wait=True)
    card = bot.live_state()["cards"][0]
    assert not card["drafting"] and card["text"] == good


def test_card_gets_ai_proposal_later_if_ai_was_busy(make_bot, projects):
    good = ("You need a RAG chatbot over ~800 internal PDFs that cites sources. I built a RAG Chatbot with a "
            "LangGraph router (Pinecone + FastAPI): https://github.com/dheerajkumar47/IntelliCourse\n"
            "Plan: 1) ingest PDFs, 2) retrieval with citations, 3) FastAPI + React widget, 4) Docker deploy. "
            "Which vector database do you prefer? — Dheeraj")

    class FlakyLLM(FakeLLM):
        busy = True

        def complete(self, *a, **k):
            if self.busy:
                raise RuntimeError("gemini HTTP 503 busy")
            return super().complete(*a, **k)

    llm = FlakyLLM([good])
    bot = make_bot(llm=llm, background_drafts=True)
    import dataclasses, time as _t
    bot.client.projects = []
    bot.process([dataclasses.replace(projects[40100001], time_submitted=int(_t.time()) - 60)])
    bot._drafter.submit(lambda: None).result()
    first = bot.store.get_draft(40100001)["text"]
    assert first != good                       # AI busy → ready-made draft stays
    llm.busy = False
    bot.run_live()                             # next cycle re-polishes it
    bot._drafter.submit(lambda: None).result()
    assert bot.store.get_draft(40100001)["text"] == good


def test_card_says_whether_the_ai_wrote_it(make_bot, projects):
    bot = make_bot()                                    # no AI at all → basic draft
    bot.process([projects[40100001]], NOW)
    c = bot.live_state()["cards"][0]
    assert c["ai"] is False and c["edited"] is False
    bot.edit(40100001, "My own careful proposal for the RAG chatbot over your internal PDFs with FastAPI.")
    assert bot.live_state()["cards"][0]["edited"] is True
    good = ("You need a RAG chatbot over ~800 internal PDFs that cites sources. I built a RAG Chatbot with a "
            "LangGraph router (Pinecone + FastAPI): https://github.com/dheerajkumar47/IntelliCourse\n"
            "Plan: 1) ingest PDFs, 2) retrieval with citations, 3) FastAPI + React widget, 4) Docker deploy. "
            "Which vector database do you prefer? — Dheeraj")
    bot.llm = FakeLLM([good])
    assert bot.regenerate(40100001).startswith("🔁 New AI proposal")
    assert bot.live_state()["cards"][0]["ai"] is True
