"""FastAPI server: WhatsApp webhook, mobile approval dashboard, background polling loop."""
from __future__ import annotations

import asyncio
import html
import json
import logging
import random
import secrets
import time
from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .app import BidSmith
from .notify import WhatsAppNotifier, parse_webhook, verify_signature

log = logging.getLogger(__name__)
security = HTTPBasic(auto_error=False)


def create_app(bot: BidSmith, run_loop: bool = True) -> FastAPI:
    s = bot.s

    async def poll_loop():
        await asyncio.sleep(3)
        while True:
            try:
                stats = await asyncio.to_thread(bot.run_once)
                log.info("poll: %s", stats)
            except Exception as e:
                log.exception("poll failed: %s", e)
            await asyncio.sleep(s.poll_interval_seconds + random.uniform(-15, 15))

    @asynccontextmanager
    async def lifespan(_app):
        task = asyncio.create_task(poll_loop()) if run_loop and bot.client else None
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

    # ------------------------------------------------------------ dashboard
    @app.get("/", response_class=HTMLResponse, dependencies=[Depends(auth)])
    def dashboard():
        rows = bot.store.list_projects(("pending",), 30)
        done = bot.store.list_projects(("bid_placed", "auto_bid", "bid_failed", "skipped"), 15)
        return HTMLResponse(render(bot, rows, done))

    def _after(msg: str):
        return RedirectResponse(f"/?msg={quote(msg)}", status_code=303)

    @app.post("/p/{pid}/approve", dependencies=[Depends(auth)])
    async def approve(pid: int):
        return _after(await asyncio.to_thread(bot.approve, pid))

    @app.post("/p/{pid}/skip", dependencies=[Depends(auth)])
    def skip(pid: int):
        return _after(bot.skip(pid))

    @app.post("/p/{pid}/regen", dependencies=[Depends(auth)])
    async def regen(pid: int):
        return _after(await asyncio.to_thread(bot.regenerate, pid))

    @app.post("/p/{pid}/edit", dependencies=[Depends(auth)])
    def edit(pid: int, text: str = Form(...), amount: float = Form(0), days: int = Form(0)):
        msgs = [bot.edit(pid, text)]
        d = bot.store.get_draft(pid)
        if d and amount and (amount != d["amount"] or (days and days != d["period_days"])):
            msgs.append(bot.set_price(pid, amount, days or None))
        return _after(" | ".join(msgs))

    @app.post("/run", dependencies=[Depends(auth)])
    async def run_now():
        return _after(f"Run: {await asyncio.to_thread(bot.run_once)}")

    @app.post("/toggle-pause", dependencies=[Depends(auth)])
    def toggle():
        bot.store.kv_set("paused", "0" if bot.paused() else "1")
        return _after("Paused" if bot.paused() else "Resumed")

    return app


# ---------------------------------------------------------------- HTML
CSS = """
:root{--bg:#f6f7f9;--card:#fff;--fg:#111;--mut:#667;--acc:#0a7cff;--ok:#11905a;--bad:#c62828;--bd:#e3e6ea}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a21;--fg:#e8eaed;--mut:#9aa0a6;--bd:#2a2f38}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}
main{max-width:760px;margin:auto;padding:16px}h1{font-size:20px;margin:4px 0 12px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px;margin:0 0 14px}
.t{font-weight:600}.m{color:var(--mut);font-size:13px}.score{float:right;font-weight:700}
textarea{width:100%;min-height:190px;font:inherit;padding:10px;border-radius:8px;border:1px solid var(--bd);background:var(--bg);color:var(--fg)}
input{width:90px;padding:8px;border-radius:8px;border:1px solid var(--bd);background:var(--bg);color:var(--fg)}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}
button{border:0;border-radius:8px;padding:10px 14px;font-weight:600;cursor:pointer;background:var(--bd);color:var(--fg)}
.go{background:var(--ok);color:#fff}.no{background:var(--bad);color:#fff}.pri{background:var(--acc);color:#fff}
.warn{color:var(--bad);font-size:13px}.msg{background:var(--acc);color:#fff;padding:8px 12px;border-radius:8px;margin-bottom:12px}
a{color:var(--acc)}ul{margin:6px 0;padding-left:18px}
"""


def render(bot: BidSmith, rows: list[dict], done: list[dict]) -> str:
    e = html.escape
    cards = []
    for r in rows:
        d = bot.store.get_draft(r["id"]) or {}
        q = json.loads(d.get("quality") or "{}")
        reasons = "".join(f"<li>{e(x)}</li>" for x in json.loads(r["reasons"] or "[]"))
        issues = "".join(f"<div class=warn>⚠ {e(i)}</div>" for i in q.get("issues", []))
        pid = r["id"]
        cards.append(f"""
<div class=card id=p{pid}><span class=score>{r['score']}</span>
<div class=t><a href="{e(r['url'])}" target=_blank rel=noopener>{e(r['title'])}</a></div>
<div class=m>#{pid} · {e(d.get('price_note') or '')}</div><ul class=m>{reasons}</ul>{issues}
<form method=post action="/p/{pid}/edit">
<textarea name=text>{e(d.get('text', ''))}</textarea>
<div class=row>Price <input name=amount type=number step=1 value="{d.get('amount', 0):.0f}"> {e(d.get('currency', ''))}
 · Days <input name=days type=number value="{d.get('period_days', 7)}"> <button>Save</button></div></form>
<div class=row>
<form method=post action="/p/{pid}/approve"><button class=go>✅ Place bid</button></form>
<form method=post action="/p/{pid}/regen"><button class=pri>🔁 Regenerate</button></form>
<form method=post action="/p/{pid}/skip"><button class=no>⏭ Skip</button></form></div></div>""")
    hist = "".join(f"<li>{e(r['status'])} · <a href='{e(r['url'])}'>{e(r['title'][:60])}</a></li>" for r in done)
    stats = bot.store.stats()
    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>BidSmith</title><style>{CSS}</style>
<script>const m=new URLSearchParams(location.search).get('msg');</script></head><body><main>
<h1>BidSmith · {len(rows)} pending</h1>
<script>if(m)document.write('<div class=msg>'+m.replace(/</g,'&lt;')+'</div>')</script>
<div class="row m">{e(json.dumps(stats))}
<form method=post action=/run><button>Run now</button></form>
<form method=post action=/toggle-pause><button>{'Resume' if bot.paused() else 'Pause'}</button></form></div>
{''.join(cards) or '<div class=card>No pending drafts. 🎉</div>'}
<div class=card><div class=t>Recent</div><ul class=m>{hist or '<li>none</li>'}</ul></div>
</main></body></html>"""
