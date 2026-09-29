import hashlib
import hmac
import json

import httpx
from fastapi.testclient import TestClient

from bidsmith.notify import WhatsAppNotifier, parse_webhook, verify_signature
from bidsmith.store import Store
from bidsmith.web import create_app

from .conftest import NOW

OWNER = "923001234567"


def _wa_payload(frm, button=None, text=None):
    msg = {"from": frm, "id": "wamid.1", "timestamp": "1"}
    if button:
        msg.update(type="interactive", interactive={"type": "button_reply", "button_reply": {"id": button, "title": "x"}})
    else:
        msg.update(type="text", text={"body": text})
    return {"object": "whatsapp_business_account",
            "entry": [{"changes": [{"field": "messages", "value": {"messages": [msg]}}]}]}


def test_parse_and_signature():
    ev = parse_webhook(_wa_payload(OWNER, button="approve:1"))
    assert ev == [{"from": OWNER, "kind": "button", "value": "approve:1", "id": "wamid.1"}]
    body = b'{"a":1}'
    sig = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert verify_signature("secret", body, sig)
    assert not verify_signature("secret", body, "sha256=bad")


def test_whatsapp_card_uses_buttons_inside_window_and_template_outside():
    sent = []

    def handler(req: httpx.Request):
        sent.append(json.loads(req.content))
        return httpx.Response(200, json={"messages": [{"id": "x"}]})

    store = Store(":memory:")
    wa = WhatsAppNotifier("tok", "123", OWNER, store, template_name="bid_alert",
                          transport=httpx.MockTransport(handler))
    from bidsmith.notify import Card
    card = Card(7, "RAG bot", "https://f/p/7", 80, ["skills match"], "300 USD", "draft text", [])

    wa.send_card(card)  # window closed → template
    assert sent[-1]["type"] == "template" and sent[-1]["template"]["name"] == "bid_alert"

    store.kv_set("wa_last_inbound", str(__import__("time").time()))
    sent.clear()
    wa.send_card(card)
    assert [m["type"] for m in sent] == ["text", "interactive"]
    buttons = sent[1]["interactive"]["action"]["buttons"]
    assert [b["reply"]["id"] for b in buttons] == ["approve:7", "edit:7", "skip:7"]
    assert all(len(b["reply"]["title"]) <= 20 for b in buttons)


def test_webhook_flow_and_dashboard(make_bot, projects):
    bot = make_bot(owner_whatsapp=OWNER, whatsapp_verify_token="vt", whatsapp_app_secret="",
                   dashboard_password="pw")
    bot.process([projects[40100001]], NOW)
    client = TestClient(create_app(bot, run_loop=False))

    r = client.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "vt",
                                                "hub.challenge": "42"})
    assert r.text == "42"
    assert client.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "no"}).status_code == 403

    # stranger is ignored
    client.post("/webhook/whatsapp", json=_wa_payload("111", button="approve:40100001"))
    assert bot.client.bids == []
    # owner approves
    client.post("/webhook/whatsapp", json=_wa_payload(OWNER, button="approve:40100001"))
    assert bot.client.bids and bot.client.bids[0]["project_id"] == 40100001
    assert bot.store.kv_get("wa_last_inbound")

    assert client.get("/").status_code == 401
    assert client.get("/", auth=("owner", "pw")).status_code == 200
    assert client.get("/health").json()["ok"]


def test_copy_paste_mode_dashboard_and_approve(make_bot, projects):
    bot = make_bot(dashboard_password="pw")
    bot.client.can_bid = lambda: False
    bot.process([projects[40100001]], NOW)
    assert bot.approve(40100001) == bot.MANUAL
    assert bot.client.bids == [] and bot.store.get_project(40100001)["status"] == "pending"
    c = TestClient(create_app(bot, run_loop=False))
    assert "BidSmith" in c.get("/", auth=("owner", "pw")).text
    st = c.get("/api/state", auth=("owner", "pw")).json()
    assert st["auto_bid"] is False and [x["id"] for x in st["cards"]] == [40100001]
    r = c.post("/api/cards/40100001/applied", auth=("owner", "pw")).json()
    assert r["ok"] and bot.store.get_project(40100001)["status"] == "bid_placed"


def test_live_api_apply_with_edits_and_skip(make_bot, projects):
    bot = make_bot(dashboard_password="pw")
    bot.process([projects[40100001], projects[40100004]], NOW)
    c = TestClient(create_app(bot, run_loop=False))
    auth = ("owner", "pw")
    assert c.get("/api/state").status_code == 401
    st = c.get("/api/state", auth=auth).json()
    card = next(x for x in st["cards"] if x["id"] == 40100001)
    assert card["text"] and card["amount"] > 0 and card["bids"] == 7 and "score" not in card
    assert any(sk["match"] for sk in card["skills"])
    r = c.post("/api/cards/40100001/apply", auth=auth,
               json={"text": "My edited proposal for the RAG chatbot with FastAPI and cited PDF answers.",
                     "amount": 500, "days": 10}).json()
    assert r["ok"], r
    bid = bot.client.bids[0]
    assert bid["amount"] == 500 and bid["period"] == 10 and bid["description"].startswith("My edited")
    assert c.post("/api/cards/40100004/skip", auth=auth).json()["ok"]
    assert c.get("/api/state", auth=auth).json()["cards"] == []
    assert c.post("/api/pause", auth=auth).json()["message"].startswith("⏸")


def test_checked_today_tab_lists_every_job_with_a_verdict(make_bot, projects):
    import dataclasses, time as _t
    bot = make_bot(dashboard_password="pw")
    fresh = [dataclasses.replace(p, time_submitted=int(_t.time()) - 300) for p in projects.values()]
    bot.process(fresh)
    bot.skip(40100004)
    c = TestClient(create_app(bot, run_loop=False))
    d = c.get("/api/checked", auth=("owner", "pw")).json()
    assert d["total"] == 6
    why = {r["title"][:12]: (r["group"], r["why"]) for r in d["rows"]}
    assert why["RAG chatbot "] == ("matched", "✅ Matched · open on your Live tab")
    assert why["YOLO people "] == ("matched", "Matched · you skipped")
    assert why["Logo design "][0] == "not_matched" and "Excluded: logo design" in why["Logo design "][1]
    assert why["Build Uber c"][0] == "not_matched"
    assert why["Confidential"] == ("not_matched", "NDA project")
    assert "Checked today" in c.get("/", auth=("owner", "pw")).text
