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
    assert calls[0].headers["Freelancer-OAuth-V1"] == "TOKEN"
    assert ("jobs[]", "13") in calls[0].url.params.multi_items()

    assert c.place_bid(1, 250, 7, "text")["id"] == 999
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
