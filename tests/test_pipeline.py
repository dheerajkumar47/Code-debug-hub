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
    assert "AI Receptionist" in d["text"]


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
    _, _, soft = bot.hidden_summary()
    assert [r["id"] for r in soft] == [555]
    assert bot.draft_anyway(555).startswith("✍")
