"""FastAPI server: live dashboard + JSON API, WhatsApp webhook, and the live polling loop."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import secrets
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .app import BidSmith
from .dashboard_html import PAGE
from .notify import WhatsAppNotifier, parse_webhook, verify_signature

log = logging.getLogger(__name__)
security = HTTPBasic(auto_error=False)


def create_app(bot: BidSmith, run_loop: bool = True) -> FastAPI:
    s = bot.s

    async def poll_loop():
        await asyncio.sleep(2)
        while True:
            try:
                stats = await asyncio.to_thread(bot.run_live)
                if stats.get("pending") or stats.get("expired"):
                    log.info("live: %s", stats)
            except Exception as e:
                log.exception("live cycle failed: %s", e)
            await asyncio.sleep(s.live_poll_seconds + random.uniform(-2, 2))

    @asynccontextmanager
    async def lifespan(_app):
        task = asyncio.create_task(poll_loop()) if run_loop else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="BidSmith", lifespan=lifespan)

    def wa() -> WhatsAppNotifier | None:
        return next((n for n in bot.notifiers if isinstance(n, WhatsAppNotifier)), None)

    def auth(creds: HTTPBasicCredentials | None = Depends(security)):
        if not s.dashboard_password:
            raise HTTPException(503, "Set DASHBOARD_PASSWORD to enable the dashboard")
        ok = creds and secrets.compare_digest(creds.username, s.dashboard_user) and \
            secrets.compare_digest(creds.password, s.dashboard_password)
        if not ok:
            raise HTTPException(401, "auth required", headers={"WWW-Authenticate": "Basic"})

    @app.get("/health")
    def health():
        return {"ok": True, "paused": bot.paused(), **bot.store.stats()}

    # ------------------------------------------------------------ WhatsApp
    @app.get("/webhook/whatsapp")
    def wa_verify(request: Request):
        q = request.query_params
        if q.get("hub.mode") == "subscribe" and s.whatsapp_verify_token and \
                secrets.compare_digest(q.get("hub.verify_token", ""), s.whatsapp_verify_token):
            return PlainTextResponse(q.get("hub.challenge", ""))
        raise HTTPException(403, "verification failed")

    @app.post("/webhook/whatsapp")
    async def wa_receive(request: Request):
        raw = await request.body()
        if not verify_signature(s.whatsapp_app_secret, raw, request.headers.get("X-Hub-Signature-256")):
            raise HTTPException(401, "bad signature")
        events = parse_webhook(json.loads(raw or b"{}"))
        notifier = wa()
        for ev in events:
            if ev["from"] != s.owner_whatsapp:
                log.warning("ignored WhatsApp message from %s", ev["from"])
                continue
            bot.store.kv_set("wa_last_inbound", str(time.time()))  # opens 24h window
            if ev["kind"] == "button":
                reply, show = await asyncio.to_thread(bot.handle_button, ev["value"])
            else:
                reply, show = await asyncio.to_thread(bot.handle_command, ev["value"])
            if notifier:
                await asyncio.to_thread(notifier.send_text, reply)
                if show:
                    await asyncio.to_thread(bot.push_card, show)
        return {"ok": True}

    # ------------------------------------------------------------ live dashboard
    @app.get("/", response_class=HTMLResponse, dependencies=[Depends(auth)])
    def dashboard():
        return HTMLResponse(PAGE)

    @app.get("/api/state", dependencies=[Depends(auth)])
    async def state():
        return await asyncio.to_thread(bot.live_state)

    def _result(msg: str) -> dict:
        return {"ok": msg.startswith(("✅", "✔", "⏭", "🔁", "✍", "⏸", "▶")), "message": msg}

    @app.post("/api/cards/{pid}/apply", dependencies=[Depends(auth)])
    async def apply(pid: int, request: Request):
        try:
            body = await request.json()
        except ValueError:
            body = {}
        msg = await asyncio.to_thread(bot.apply, pid, body.get("text"), body.get("amount"), body.get("days"))
        return _result(msg)

    @app.post("/api/cards/{pid}/skip", dependencies=[Depends(auth)])
    def skip(pid: int):
        return _result(bot.skip(pid))

    @app.post("/api/cards/{pid}/rewrite", dependencies=[Depends(auth)])
    async def rewrite(pid: int):
        return _result(await asyncio.to_thread(bot.regenerate, pid))

    @app.post("/api/cards/{pid}/applied", dependencies=[Depends(auth)])
    def applied(pid: int):
        return _result(bot.mark_done(pid))

    @app.post("/api/pause", dependencies=[Depends(auth)])
    def pause():
        bot.store.kv_set("paused", "0" if bot.paused() else "1")
        return _result("⏸ Paused" if bot.paused() else "▶ Live again")

    return app
