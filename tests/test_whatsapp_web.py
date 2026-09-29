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
