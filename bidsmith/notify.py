"""Notification channels. WhatsApp (official Meta Cloud API) + web dashboard + console.

WhatsApp rules that shape this design:
- Free-form/interactive messages are only allowed inside the 24h "customer service window",
  which opens every time YOU message the bot. Outside it we must send an approved template.
- Interactive reply buttons: max 3 buttons, titles max 20 chars, body max 1024 chars.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from typing import Protocol

import httpx

log = logging.getLogger(__name__)

WINDOW_SECONDS = 24 * 3600 - 300  # keep a 5-minute safety margin


@dataclass
class Card:
    project_id: int
    title: str
    url: str
    score: int
    reasons: list[str]
    price_line: str
    proposal: str
    issues: list[str]
    dashboard_url: str = ""

    def summary(self, limit: int = 1000) -> str:
        why = "; ".join(self.reasons[:4])
        issues = ("\n⚠ " + "; ".join(self.issues)) if self.issues else ""
        text = (f"*{self.title}*\nScore {self.score}/100 · {self.price_line}\n{why}{issues}\n{self.url}")
        return text[:limit]


class Notifier(Protocol):
    name: str

    def send_card(self, card: Card) -> None: ...

    def send_text(self, text: str) -> None: ...


class ConsoleNotifier:
    name = "console"

    def send_card(self, card: Card) -> None:
        log.info("NEW BID CARD #%s\n%s\n---\n%s", card.project_id, card.summary(), card.proposal)

    def send_text(self, text: str) -> None:
        log.info("NOTIFY: %s", text)


class WebNotifier:
    """The dashboard reads pending items from the DB, so nothing to push."""
    name = "web"

    def send_card(self, card: Card) -> None:
        pass

    def send_text(self, text: str) -> None:
        pass


class WhatsAppNotifier:
    name = "whatsapp"

    def __init__(self, token: str, phone_number_id: str, to: str, store, api_version: str = "v23.0",
                 template_name: str = "", template_lang: str = "en",
                 transport: httpx.BaseTransport | None = None):
        if not (token and phone_number_id and to):
            raise ValueError("WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID and OWNER_WHATSAPP are required")
        self.to = to
        self.store = store
        self.template_name = template_name
        self.template_lang = template_lang
        self._http = httpx.Client(
            base_url=f"https://graph.facebook.com/{api_version}/{phone_number_id}",
            headers={"Authorization": f"Bearer {token}"}, timeout=20, transport=transport)

    # --- window tracking -------------------------------------------------
    def window_open(self) -> bool:
        last = float(self.store.kv_get("wa_last_inbound", "0") or 0)
        return (time.time() - last) < WINDOW_SECONDS

    def _send(self, payload: dict) -> dict:
        body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": self.to, **payload}
        r = self._http.post("/messages", json=body)
        if r.status_code >= 400:
            log.error("WhatsApp send failed %s: %s", r.status_code, r.text[:300])
        return r.json() if r.content else {}

    def send_text(self, text: str) -> None:
        if not self.window_open():
            return self._send_template(text[:900])
        for i in range(0, len(text), 4000):
            self._send({"type": "text", "text": {"body": text[i:i + 4000], "preview_url": False}})

    def send_buttons(self, body: str, buttons: list[tuple[str, str]], footer: str = "") -> None:
        interactive = {
            "type": "button",
            "body": {"text": body[:1024]},
            "action": {"buttons": [{"type": "reply", "reply": {"id": bid, "title": title[:20]}}
                                   for bid, title in buttons[:3]]},
        }
        if footer:
            interactive["footer"] = {"text": footer[:60]}
        self._send({"type": "interactive", "interactive": interactive})

    def _send_template(self, text: str) -> None:
        if not self.template_name:
            log.warning("WhatsApp window closed and no WHATSAPP_TEMPLATE_NAME set — "
                        "send any message to the bot to reopen it. Item is waiting on the dashboard.")
            return
        self._send({"type": "template", "template": {
            "name": self.template_name, "language": {"code": self.template_lang},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": text[:900]}]}]}})

    def send_card(self, card: Card) -> None:
        if not self.window_open():
            link = card.dashboard_url or card.url
            return self._send_template(f"{card.title} — score {card.score}. Review: {link}")
        self.send_text(f"📝 Draft for #{card.project_id}:\n\n{card.proposal}")
        self.send_buttons(
            card.summary(),
            [(f"approve:{card.project_id}", "✅ Bid"),
             (f"edit:{card.project_id}", "✏️ Edit"),
             (f"skip:{card.project_id}", "⏭ Skip")],
            footer=f"#{card.project_id} · reply 'help' for commands")


# --- webhook helpers -----------------------------------------------------
def verify_signature(app_secret: str, raw_body: bytes, header: str | None) -> bool:
    if not app_secret:
        return True  # signature check disabled (dev only)
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.split("=", 1)[1])


def parse_webhook(payload: dict) -> list[dict]:
    """Return [{'from': '9230...', 'kind': 'button'|'text', 'value': str}] for incoming messages."""
    events = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in (change.get("value") or {}).get("messages", []) or []:
                kind, value = None, None
                t = m.get("type")
                if t == "text":
                    kind, value = "text", (m.get("text") or {}).get("body", "")
                elif t == "interactive":
                    it = m.get("interactive") or {}
                    rep = it.get("button_reply") or it.get("list_reply") or {}
                    kind, value = "button", rep.get("id", "")
                elif t == "button":  # quick-reply on a template
                    kind, value = "button", (m.get("button") or {}).get("payload", "")
                if kind:
                    events.append({"from": m.get("from", ""), "kind": kind, "value": value, "id": m.get("id")})
    return events
