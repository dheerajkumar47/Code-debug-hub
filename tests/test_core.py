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
            "Timeline: 7 days. Which calendar holds staff availability today? — Dheeraj")
    rep = quality.check(good, p, profile.corpus, profile.style, (7,))
    assert rep.passed, rep.issues
