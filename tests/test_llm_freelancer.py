import json

import httpx
import pytest

from bidsmith.freelancer import FreelancerClient
from bidsmith.llm import LLM


@pytest.mark.parametrize("provider,reply,expect_url", [
    ("gemini", {"candidates": [{"content": {"parts": [{"text": "hi"}]}}]}, "generativelanguage.googleapis.com"),
    ("openai", {"choices": [{"message": {"content": "hi"}}]}, "api.openai.com/v1/chat/completions"),
    ("anthropic", {"content": [{"type": "text", "text": "hi"}]}, "api.anthropic.com/v1/messages"),
])
def test_llm_providers(provider, reply, expect_url):
    seen = {}

    def handler(req: httpx.Request):
        seen["url"], seen["headers"], seen["body"] = str(req.url), req.headers, json.loads(req.content)
        return httpx.Response(200, json=reply)

    llm = LLM(provider, "KEY", transport=httpx.MockTransport(handler))
    assert llm.complete("sys", "user") == "hi"
    assert expect_url in seen["url"]
    assert "KEY" in " ".join(seen["headers"].values())


def test_freelancer_client_search_and_bid():
    calls = []

    def handler(req: httpx.Request):
        calls.append(req)
        path = req.url.path
        if path.endswith("/users/0.1/self/"):
            return httpx.Response(200, json={"status": "success", "result": {"id": 42}})
        if path.endswith("/projects/0.1/projects/active/"):
            return httpx.Response(200, json={"status": "success", "result": {
                "projects": [{"id": 1, "owner_id": 5, "title": "RAG bot", "seo_url": "python/rag-bot",
                              "type": "fixed", "currency": {"code": "USD", "exchange_rate": 1},
                              "budget": {"minimum": 100, "maximum": 300},
                              "bid_stats": {"bid_count": 3, "bid_avg": 200},
                              "jobs": [{"id": 13, "name": "Python"}]}],
                "users": {"5": {"status": {"payment_verified": True}}}}})
        if path.endswith("/projects/0.1/bids/") and req.method == "POST":
            return httpx.Response(200, json={"status": "success", "result": {"id": 999}})
        return httpx.Response(404, json={"status": "error", "message": "nope"})

    c = FreelancerClient("TOKEN", transport=httpx.MockTransport(handler))
    ps = c.search_active("rag", job_ids=[13], project_types=["fixed"])
    assert ps[0].url == "https://www.freelancer.com/projects/python/rag-bot"
    assert ps[0].client.payment_verified and ps[0].skills == ["Python"]
    assert "Freelancer-OAuth-V1" not in calls[0].headers  # search is public, no token sent
    assert ("jobs[]", "13") in calls[0].url.params.multi_items()

    assert c.place_bid(1, 250, 7, "text")["id"] == 999
    assert calls[-1].headers["Freelancer-OAuth-V1"] == "TOKEN"
    body = json.loads(calls[-1].content)
    assert body == {"project_id": 1, "bidder_id": 42, "amount": 250.0, "period": 7,
                    "milestone_percentage": 50, "description": "text"}


def test_gemini_switches_when_model_retired():
    """Reproduces the real error: default model 404s and Google suggests a replacement."""
    urls = []

    def handler(req: httpx.Request):
        urls.append(req.url.path)
        if "gemini-flash-latest" in req.url.path or "gemini-2.5-flash" in req.url.path:
            return httpx.Response(404, json={"error": {"code": 404, "message":
                "This model models/gemini-2.5-flash is no longer available to new users. Please update your "
                "code to use models/gemini-3.8-flash for the latest features and improvements."}})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [
            {"text": "thinking...", "thought": True}, {"text": "OK"}]}}]})

    llm = LLM("gemini", "KEY", transport=httpx.MockTransport(handler))
    assert llm.complete("s", "u") == "OK"          # thought parts are dropped
    assert llm.model == "gemini-3.8-flash"
    assert urls[-1].endswith("gemini-3.8-flash:generateContent")


def test_gemini_discovers_model_from_list():
    def handler(req: httpx.Request):
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"models": [
                {"name": "models/gemini-3.1-flash", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-3.8-flash-lite", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-3.8-flash", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-4.0-flash-preview", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/text-embedding-9", "supportedGenerationMethods": ["embedContent"]}]})
        if "gemini-3.8-flash:" in req.url.path:
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "OK"}]}}]})
        return httpx.Response(404, json={"error": {"message": "not found"}})

    llm = LLM("gemini", "KEY", transport=httpx.MockTransport(handler))
    assert llm.complete("s", "u") == "OK" and llm.model == "gemini-3.8-flash"


def test_gemini_busy_retries_then_switches_model():
    calls = []

    def handler(req: httpx.Request):
        calls.append(req.url.path)
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"models": [
                {"name": "models/gemini-flash-latest", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/gemini-3.8-flash-lite", "supportedGenerationMethods": ["generateContent"]}]})
        if "flash-latest" in req.url.path:
            return httpx.Response(503, json={"error": {"code": 503, "message": "high demand"}})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "OK"}]}}]})

    llm = LLM("gemini", "KEY", transport=httpx.MockTransport(handler))
    llm._sleep = lambda s: None
    assert llm.complete("s", "u") == "OK"
    assert llm.model == "gemini-3.8-flash-lite"
    assert sum("flash-latest:" in c for c in calls) == 3  # retried before switching


def _auth_handler(accept: str | None):
    """Server that accepts the token only in the given header ('oauth', 'bearer' or None)."""
    def handler(req: httpx.Request):
        ok = (accept == "oauth" and req.headers.get("Freelancer-OAuth-V1") == "TOK") or \
             (accept == "bearer" and req.headers.get("Authorization") == "Bearer TOK")
        if req.url.path.endswith("/projects/active/"):
            return httpx.Response(200, json={"status": "success", "result": {"projects": [], "users": {}}})
        if not ok:
            return httpx.Response(401, json={"status": "error", "error_code": "NOT_AUTHENTICATED",
                                             "message": "You must be logged in"})
        if req.url.path.endswith("/self/"):
            return httpx.Response(200, json={"status": "success", "result": {"id": 7}})
        return httpx.Response(200, json={"status": "success", "result": {"id": 1}})
    return handler


def test_token_accepted_via_bearer_header():
    c = FreelancerClient("TOK", transport=httpx.MockTransport(_auth_handler("bearer")))
    assert c.can_bid() and c.self_id() == 7
    assert c.place_bid(1, 100, 3, "x")["id"] == 1


def test_rejected_token_means_copy_paste_mode_not_crash():
    c = FreelancerClient("TOK", transport=httpx.MockTransport(_auth_handler(None)))
    assert c.search_active("python") == []      # search still works
    assert c.can_bid() is False and "logged in" in c.auth_error
    assert FreelancerClient(None, transport=httpx.MockTransport(_auth_handler(None))).can_bid() is False


def test_search_asks_for_fresh_projects_and_falls_back_if_rejected():
    seen = []

    def handler(req: httpx.Request):
        seen.append(dict(req.url.params))
        if "from_time" in req.url.params:
            return httpx.Response(400, json={"status": "error", "message": "bad param"})
        return httpx.Response(200, json={"status": "success", "result": {"projects": [], "users": {}}})

    c = FreelancerClient(None, transport=httpx.MockTransport(handler))
    assert c.search_active("rag", from_time=123) == []
    assert seen[0]["from_time"] == "123" and "from_time" not in seen[1]
    c.search_active("rag", from_time=123)
    assert "from_time" not in seen[2]          # remembered: no repeated failing calls


def test_llm_cools_down_after_busy_streak():
    n = {"calls": 0}

    def handler(req):
        n["calls"] += 1
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"models": []})
        return httpx.Response(429, json={"error": {"code": 429, "message": "rate limit"}})

    llm = LLM("gemini", "KEY", model="gemini-x-flash", transport=httpx.MockTransport(handler))
    llm._sleep = lambda s: None
    with pytest.raises(Exception):
        llm.complete("s", "u")
    assert llm.cooling
    before = n["calls"]
    with pytest.raises(Exception):
        llm.complete("s", "u")
    assert n["calls"] == before          # no calls while cooling down


def test_backup_ai_writes_when_gemini_is_busy():
    from bidsmith.llm import LLMChain
    used = []

    def gemini(req):
        used.append("gemini")
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"models": []})
        return httpx.Response(503, json={"error": {"code": 503, "message": "high demand"}})

    def groq(req):
        used.append("groq")
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "whisper-large-v3"}, {"id": "llama-3.1-8b-instant"},
                                                      {"id": "llama-3.3-70b-versatile"}]})
        body = json.loads(req.content)
        assert body["model"] == "llama-3.3-70b-versatile"
        return httpx.Response(200, json={"choices": [{"message": {"content": "Groq proposal"}}]})

    main = LLM("gemini", "G", model="gemini-x-flash", transport=httpx.MockTransport(gemini))
    main._sleep = lambda s: None
    backup = LLM("openai", "K", base_url="https://api.groq.com/openai/v1", transport=httpx.MockTransport(groq))
    chain = LLMChain([main, backup])
    assert chain.complete("s", "u") == "Groq proposal"
    assert main.cooling and "groq" in used
    used.clear()
    assert chain.complete("s", "u") == "Groq proposal" and "gemini" not in used   # main skipped while cooling


def test_openai_handles_new_parameter_names_and_retired_models():
    sent = []

    def handler(req):
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "gpt-image-1"}, {"id": "gpt-5-mini"}]})
        b = json.loads(req.content)
        sent.append(b)
        if b["model"] == "gpt-4.1-mini":
            return httpx.Response(404, json={"error": {"code": "model_not_found", "message": "does not exist"}})
        if "max_tokens" in b:
            return httpx.Response(400, json={"error": {"message": "Unsupported parameter: 'max_tokens'"}})
        if "temperature" in b:
            return httpx.Response(400, json={"error": {"message": "Unsupported value: 'temperature'"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}]})

    llm = LLM("openai", "sk-x", transport=httpx.MockTransport(handler))
    assert llm.complete("s", "u") == "OK"
    assert llm.model == "gpt-5-mini" and "max_completion_tokens" in sent[-1] and "temperature" not in sent[-1]
