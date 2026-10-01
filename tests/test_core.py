from bidsmith import quality
from bidsmith.filters import rule_filter
from bidsmith.pricing import compute_price
from bidsmith.retrieval import PortfolioIndex
from bidsmith.scoring import heuristic_score

from .conftest import NOW


def test_rule_filter(profile, projects):
    assert rule_filter(projects[40100001], profile, NOW)[0]
    ok, why = rule_filter(projects[40100003], profile, NOW)
    assert not ok and any("logo design" in w for w in why)
    ok, why = rule_filter(projects[40100006], profile, NOW)
    assert not ok and any("NDA" in w for w in why)


def test_scores_rank_good_fits_above_bad(profile, projects):
    idx = PortfolioIndex(profile.portfolio)
    rag = heuristic_score(projects[40100001], profile, idx, NOW)
    wa = heuristic_score(projects[40100002], profile, idx, NOW)
    cv = heuristic_score(projects[40100004], profile, idx, NOW)
    uber = heuristic_score(projects[40100005], profile, idx, NOW)
    assert rag.score >= 70, rag
    assert wa.score >= 60, wa
    assert cv.score >= 60, cv
    assert uber.score < 40 and uber.red_flags


def test_portfolio_retrieval_picks_relevant_proof(profile, projects):
    idx = PortfolioIndex(profile.portfolio)
    assert "Receptionist" in idx.search(projects[40100002].text, 1)[0][0].title
    assert "CCTV" in idx.search(projects[40100004].text, 1)[0][0].title
    assert "RAG" in idx.search(projects[40100001].text, 1)[0][0].title


def test_price_respects_budget_floor_and_currency(profile, projects):
    rag = compute_price(projects[40100001], profile, 80)
    assert 250 <= rag.amount_usd <= 750 and rag.currency == "USD"
    cv = compute_price(projects[40100004], profile, 70)
    assert cv.currency == "INR" and 12500 <= cv.amount <= 37500
    assert abs(cv.amount * 0.012 - cv.amount_usd) < 2


def test_detect_hidden_instructions_and_questions(projects):
    d = projects[40100002].description
    assert quality.detect_instructions(d)["start_with"].lower() == "banana"
    assert quality.detect_questions(d) == ["What is your timeline?"]


def test_quality_gate(profile, projects):
    p = projects[40100002]
    bad = ("I hope this finds you well! I am thrilled to leverage my 10 years of seamless experience. " * 3)
    rep = quality.check(bad, p, profile.corpus, profile.style)
    joined = " ".join(rep.issues)
    assert not rep.passed
    assert "clichés" in joined and "banana" in joined and "'10'" in joined

    good = ("banana — you need a WhatsApp assistant that answers clinic FAQs and books appointments into "
            "Google Calendar in English and Urdu. I built an AI Receptionist that does this on WhatsApp, "
            "Messenger and Instagram, with Outlook booking and Urdu voice replies: "
            "https://github.com/dheerajkumar47/AI-receptionist\n"
            "Plan: 1) map your services and FAQs, 2) connect WhatsApp Business API and Google Calendar, "
            "3) test real booking conversations in both languages, 4) deploy and hand over. "
            "Timeline: 7 days, with a working demo on day 3 so you can try real conversations early. "
            "You get the full source code, deployment on your server and clear documentation, and I stay "
            "available for fixes after launch. The assistant will also hand a chat over to your staff whenever "
            "a customer asks something it should not answer on its own. "
            "Which calendar holds staff availability today? — Dheeraj")
    rep = quality.check(good, p, profile.corpus, profile.style, (7,))
    assert rep.passed, rep.issues


def _real_style_project(**kw):
    from bidsmith.models import Client, Project
    base = dict(id=77, title="AI chatbot for customer support using ChatGPT",
                description="For example, it should answer FAQs from our docs and hand over to a human. "
                            "Python backend preferred.",
                url="u", type="fixed", budget_min=250, budget_max=750, bid_count=12, bid_avg=400,
                skills=["Artificial Intelligence", "Machine Learning (ML)", "ChatGPT", "Python", "Chatbot"],
                time_submitted=int(NOW - 900), client=Client(payment_verified=True))
    base.update(kw)
    return Project(**base)


def test_exam_does_not_block_example(profile):
    ok, why = rule_filter(_real_style_project(), profile, NOW)
    assert ok, why
    ok, why = rule_filter(_real_style_project(description="Help with my exam questions"), profile, NOW)
    assert not ok


def test_freelancer_skill_names_match_profile(profile):
    r = heuristic_score(_real_style_project(), profile, PortfolioIndex(profile.portfolio), NOW)
    assert "5/5" in r.reasons[0], r.reasons
    assert r.score >= 75, r


def test_real_world_chatbot_project_with_extra_tags_still_matches(profile):
    from bidsmith.models import Client
    p = _real_style_project(title="AI chatbot for my website",
                            description="Need a chatbot on our website that answers customer questions.",
                            skills=["PHP", "JavaScript", "AI Chatbot", "Python", "Website Design"],
                            budget_min=30, budget_max=250, bid_count=5, client=Client())
    r = heuristic_score(p, profile, PortfolioIndex(profile.portfolio), NOW)
    assert r.score >= 60, r
    off = _real_style_project(title="Logo and brand kit", description="Modern logo for a bakery.",
                              skills=["Logo Design", "Graphic Design", "Illustrator"], bid_count=5)
    assert heuristic_score(off, profile, PortfolioIndex(profile.portfolio), NOW).score < 40


def test_generic_automation_project_is_not_a_match(profile):
    adobe = _real_style_project(title="Adobe Publishing Automation Script",
                                description="Write a script to automate exporting InDesign files to PDF.",
                                skills=["Adobe Photoshop", "Automation", "Scripting", "Python"], bid_count=3)
    assert heuristic_score(adobe, profile, PortfolioIndex(profile.portfolio), NOW).score < 60
    vision = _real_style_project(title="Micron-Level Vision Calibration",
                                 description="Calibrate a camera system for precise measurement.",
                                 skills=["Computer Vision", "OpenCV", "Python"], bid_count=3)
    assert heuristic_score(vision, profile, PortfolioIndex(profile.portfolio), NOW).score >= 60


def test_commission_only_sales_job_is_excluded(profile):
    sales = _real_style_project(
        title="Grow with CallMate AI",
        description="CallMate AI – Client Acquisition Partner. AI Voice Receptionist, AI WhatsApp Automation. "
                    "This is a performance-based opportunity. There is no upfront investment required. "
                    "Commission-Based Partnership: you receive your agreed commission.",
        skills=["Artificial Intelligence", "Sales", "Lead Generation"])
    ok, why = rule_filter(sales, profile, NOW)
    assert not ok and "excluded keyword" in why[0], why
    dev = _real_style_project(title="Build an AI voice receptionist",
                              description="Twilio + OpenAI voice agent that books appointments for our clinic.")
    assert rule_filter(dev, profile, NOW)[0]


def test_experience_years_copied_from_brief_are_rejected(profile):
    from bidsmith import quality
    p = _real_style_project(title="PHP developer with AI", description="Need 5+ years of PHP experience and OpenAI API.")
    text = ("You need PHP with AI chatbot features on your existing app. My PHP experience is 5+ years, "
            "AI integration with OpenAI API. Which framework do you use?")
    r = quality.check(text, p, "BS Software Engineering. AI Engineer.", {"min_words": 5, "max_words": 300})
    assert any("experience claim" in i for i in r.issues), r.issues
    ok = quality.check(text.replace("My PHP experience is 5+ years, AI", "AI"), p, "", {"min_words": 5, "max_words": 300})
    assert not any("experience claim" in i for i in ok.issues)


def _proj(title, desc, skills):
    from bidsmith.models import Client, Project
    return Project(id=9, title=title, description=desc, url="u", budget_min=100, budget_max=300, bid_count=6,
                   bid_avg=200, skills=skills, time_submitted=int(NOW - 600), client=Client(payment_verified=True))


def test_field_includes_automation_voice_scraping_but_not_unrelated_work(profile):
    idx = PortfolioIndex(profile.portfolio)
    want = [_proj("n8n workflow for invoice processing", "Build an n8n flow that logs invoices to Sheets.",
                  ["n8n", "Automation", "Google Sheets"]),
            _proj("Voice AI agent for dental clinic calls", "AI voice agent with Twilio that books appointments.",
                  ["Twilio", "Artificial Intelligence", "Voice Recognition"]),
            _proj("Text to speech narration for e-learning", "Generate natural narration audio.",
                  ["Text to Speech", "Python"])]
    skip = [_proj("Excel VBA macro for reports", "Automate monthly report in Excel VBA.", ["Excel", "VBA", "Automation"]),
            _proj("Laravel e-commerce bug fixes", "Fix checkout bugs.", ["PHP", "Laravel", "MySQL"]),
            _proj("Mobile app UI in Flutter", "Build Flutter screens from Figma.", ["Flutter", "Mobile App Development"]),
            _proj("Shopify product listing", "List 100 products.", ["Shopify", "Product Descriptions"])]
    for p in want:
        assert heuristic_score(p, profile, idx, NOW).score >= 60, p.title
    for p in skip:
        assert heuristic_score(p, profile, idx, NOW).score < 60, p.title


def test_client_first_name_greeting_and_type_playbooks(profile):
    from bidsmith import proposal
    from bidsmith.freelancer import first_name
    from bidsmith.models import Price
    assert first_name({"public_name": "John D.", "username": "jd88"}) == "John"
    assert first_name({"public_name": "techguy88", "username": "techguy88"}) == ""
    assert first_name({"display_name": "sarah khan"}) == "Sarah"
    assert first_name({}) == ""
    p = _proj("Voice AI agent for clinic calls", "We need an AI voice agent with Twilio that answers calls.",
              ["Twilio", "Artificial Intelligence"])
    p.client.name = "Sarah"
    d = proposal.write(p, profile, PortfolioIndex(profile.portfolio), Price(250, 7, "USD", 250, ""), llm=None)
    assert d.text.startswith("Hi Sarah,") and "speech-to-text" in d.text and len(d.text) <= 1500
    p2 = _proj("Scrape business directory", "Need data extraction from 3 directories into Google Sheets.",
               ["Web Scraping", "Data Extraction"])
    d2 = proposal.write(p2, profile, PortfolioIndex(profile.portfolio), Price(150, 5, "USD", 150, ""), llm=None)
    assert "de-duplication" in d2.text and not d2.text.startswith("Hi ")


def test_feed_failure_does_not_skip_the_time_window(make_bot):
    bot = make_bot()
    bot.store.kv_set("last_poll", "1000")

    def boom(*a, **k):
        raise RuntimeError("network down")
    bot.client.search_active = boom
    bot.run_live()
    assert bot.store.kv_get("last_poll") == "1000"


def test_roles_content_and_scraping_jobs_are_not_your_field(profile):
    idx = PortfolioIndex(profile.portfolio)
    off = [_proj("Freelance Proposal Writer & Account Manager", "Write proposals and manage our Freelancer account.",
                 ["Web Development", "Proposal Writing", "ChatGPT"]),
           _proj("Freelance Bidder & Portfolio Manager Needed", "Bid on projects for our agency and manage portfolio.",
                 ["Chatbot", "Project Management"]),
           _proj("Web Scraping Expert Needed | Real-World Scraping Experience", "Scrape e-commerce sites with Selenium.",
                 ["Selenium", "Web Scraping", "Python"]),
           _proj("AI Social Video Generator", "Generate short social videos with AI tools.",
                 ["AI Video", "Video Editing", "Artificial Intelligence"]),
           _proj("Virtual Assistant for ChatGPT content", "Daily posts with ChatGPT.", ["ChatGPT", "Virtual Assistant"])]
    for p in off:
        assert heuristic_score(p, profile, idx, NOW).score < 60, p.title
    still = [_proj("AI chatbot for our sales team", "Chatbot that answers sales questions from our CRM.",
                   ["AI Chatbot", "OpenAI"]),
             _proj("LLM agent that summarizes YouTube videos", "Agent pulls transcripts and summarizes them.",
                   ["Python", "OpenAI"])]
    for p in still:
        assert heuristic_score(p, profile, idx, NOW).score >= 60, p.title
