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

    @app.post("/p/{pid}/draft", dependencies=[Depends(auth)])
    async def draft_anyway(pid: int):
        return _after(await asyncio.to_thread(bot.draft_anyway, pid))

    @app.post("/recheck", dependencies=[Depends(auth)])
    async def recheck():
        st = await asyncio.to_thread(bot.recheck_hidden)
        return _after(f"Re-checked hidden projects: {st.get('pending', 0)} new cards.")

    @app.post("/threshold", dependencies=[Depends(auth)])
    def threshold(value: int = Form(...)):
        return _after(bot.set_threshold(value))

    @app.post("/p/{pid}/done", dependencies=[Depends(auth)])
    def done(pid: int):
        return _after(bot.mark_done(pid))

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
        st = await asyncio.to_thread(bot.run_once)
        if st.get("paused"):
            return _after("Paused — press Resume first.")
        return _after(f"Checked Freelancer: {st['new']} new projects, {st['pending']} good matches added.")

    @app.post("/toggle-pause", dependencies=[Depends(auth)])
    def toggle():
        bot.store.kv_set("paused", "0" if bot.paused() else "1")
        return _after("Paused" if bot.paused() else "Resumed")

    return app


# ---------------------------------------------------------------- HTML
CSS = """
:root{--bg:#f6f7f9;--card:#fff;--fg:#111;--mut:#667;--acc:#0a7cff;--ok:#11905a;--bad:#c62828;--bd:#e3e6ea}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a21;--fg:#e8eaed;--mut:#9aa0a6;--bd:#2a2f38}}
*{box-sizing:border-box;min-width:0}html,body{max-width:100%;overflow-x:hidden}body{margin:0;overflow-wrap:anywhere;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}
main{width:100%;max-width:760px;margin:auto;padding:16px}h1{font-size:20px;margin:4px 0 12px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px;margin:0 0 14px}
.t{font-weight:600}.m{color:var(--mut);font-size:13px}.score{float:right;font-weight:700}
textarea{width:100%;max-width:100%;display:block;min-height:190px;font:inherit;padding:10px;border-radius:8px;border:1px solid var(--bd);background:var(--bg);color:var(--fg)}
input{width:96px;max-width:40%;padding:8px;border-radius:8px;border:1px solid var(--bd);background:var(--bg);color:var(--fg)}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;align-items:center}.row form{margin:0}.stats{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 12px}.cols{display:grid;grid-template-columns:1fr;gap:8px}@media(min-width:760px){.cols{grid-template-columns:1fr 1.4fr}}
.wl{list-style:none;padding:0}.wk{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid var(--bd)}
.wk button{padding:6px 10px;font-size:13px}.pill{background:var(--card);border:1px solid var(--bd);border-radius:999px;padding:4px 10px;font-size:13px}
button{border:0;border-radius:8px;padding:10px 14px;font-weight:600;cursor:pointer;background:var(--bd);color:var(--fg)}
.go{background:var(--ok);color:#fff}.no{background:var(--bad);color:#fff}.pri{background:var(--acc);color:#fff}
.warn{color:var(--bad);font-size:13px}.msg{background:var(--acc);color:#fff;padding:8px 12px;border-radius:8px;margin-bottom:12px}
a{color:var(--acc)}ul{margin:6px 0;padding-left:18px}
"""


def render(bot: BidSmith, rows: list[dict], done: list[dict]) -> str:
    e = html.escape
    auto_bid = bot.can_bid()
    mode = ("<div class=card>🟢 <b>Auto-bid ready</b>: press ✅ Place bid and the bot submits it for you.</div>"
            if auto_bid else
            "<div class=card>🟡 <b>Copy &amp; paste mode</b>: Freelancer did not accept the token for bidding, "
            "so for each card press 📋 Copy → ↗ Open → paste the text on Freelancer → Place Bid there → "
            "then ✔ Done here. Finding, scoring and writing are fully automatic.</div>")
    cards = []
    for r in rows:
        d = bot.store.get_draft(r["id"]) or {}
        q = json.loads(d.get("quality") or "{}")
        reasons = "".join(f"<li>{e(x)}</li>" for x in json.loads(r["reasons"] or "[]"))
        issues = "".join(f"<div class=warn>⚠ {e(i)}</div>" for i in q.get("issues", []))
        pid = r["id"]
        place_btn = (f'<form method=post action="/p/{pid}/approve"><button class=go>✅ Place bid</button></form>'
                     if auto_bid else
                     f'<form method=post action="/p/{pid}/done"><button class=go>✔ Done (I placed it)</button></form>')
        cards.append(f"""
<div class=card id=p{pid}><span class=score>{r['score']}</span>
<div class=t><a href="{e(r['url'])}" target=_blank rel=noopener>{e(r['title'])}</a></div>
<div class=m>#{pid} · {e(d.get('price_note') or '')}</div><ul class=m>{reasons}</ul>{issues}
<form method=post action="/p/{pid}/edit">
<textarea name=text>{e(d.get('text', ''))}</textarea>
<div class=row>Price <input name=amount type=number step=1 value="{d.get('amount', 0):.0f}"> {e(d.get('currency', ''))}
 · Days <input name=days type=number value="{d.get('period_days', 7)}"> <button>Save</button></div></form>
<div class=row>
{place_btn}
<button type=button onclick="copyDraft({pid},this)">📋 Copy</button>
<a href="{e(r['url'])}" target=_blank rel=noopener><button type=button>↗ Open</button></a>
<form method=post action="/p/{pid}/regen"><button class=pri>🔁 Regenerate</button></form>
<form method=post action="/p/{pid}/skip"><button class=no>⏭ Skip</button></form></div></div>""")
    reasons, weak, soft = bot.hidden_summary()
    reason_html = "".join(f"<li><b>{n}</b> × {e(k)}</li>" for k, n in reasons) or "<li>none</li>"
    weak_html = "".join(
        f"<li class=wk><span><b>{r['score']}</b> · <a href='{e(r['url'])}' target=_blank rel=noopener>{e(r['title'][:70])}</a></span>"
        f"<form method=post action='/p/{r['id']}/draft'><button>✍ Write bid</button></form></li>" for r in weak
    ) or "<li>none</li>"
    soft_html = "".join(
        f"<li class=wk><span><b>{r['score']}</b> · <a href='{e(r['url'])}' target=_blank rel=noopener>{e(r['title'][:70])}</a>"
        f"<br><span class=m>{e(r['note'])}</span></span>"
        f"<form method=post action='/p/{r['id']}/draft'><button>✍ Write bid</button></form></li>" for r in soft)
    soft_card = (f"""<div class=card><div class=t>⭐ Good fits hidden only because they are crowded or older</div>
<div class=m>Strong skill match. Worth a bid if you still want to try: press ✍ Write bid.</div>
<ul class="m wl">{soft_html}</ul></div>""" if soft else "")
    hidden = soft_card + f"""<div class=card><div class=t>Hidden projects: why</div>
<div class=m>Projects the bot skipped, so nothing is a black box.</div>
<div class=cols><div><div class=m><b>Filtered out, top reasons</b></div><ul class=m>{reason_html}</ul></div>
<div><div class=m><b>Weak matches (best first)</b>, press ✍ to write a bid anyway</div><ul class="m wl">{weak_html}</ul></div></div>
<div class=row><form method=post action=/threshold>Min score <input name=value type=number min=30 max=95 value="{bot.threshold()}">
<button>Set</button></form><form method=post action=/recheck><button class=pri>♻ Re-check hidden</button></form></div></div>"""
    hist = "".join(f"<li>{e(r['status'])} · <a href='{e(r['url'])}'>{e(r['title'][:60])}</a></li>" for r in done)
    stats = bot.store.stats()
    labels = [("pending", "waiting for you"), ("bid_placed", "bids placed"), ("skipped", "skipped"),
              ("low_score", "weak matches hidden"), ("filtered", "filtered out"), ("bids_placed_24h", "bids today")]
    pills = "".join(f"<span class=pill><b>{stats.get(k, 0)}</b> {lbl}</span>" for k, lbl in labels)
    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>BidSmith</title><style>{CSS}</style>
<script>const m=new URLSearchParams(location.search).get('msg');
function copyDraft(id,btn){{const t=document.querySelector('#p'+id+' textarea');
const done=()=>btn.textContent='✔ Copied';
if(navigator.clipboard&&window.isSecureContext){{navigator.clipboard.writeText(t.value).then(done);}}
else{{t.select();document.execCommand('copy');done();}}}}</script></head><body><main>
<h1>BidSmith · {len(rows)} pending</h1>{mode}
<script>if(m)document.write('<div class=msg>'+m.replace(/</g,'&lt;')+'</div>')</script>
<div class=stats>{pills}</div><div class="row m">
<form method=post action=/run><button>Run now</button></form>
<form method=post action=/toggle-pause><button>{'Resume' if bot.paused() else 'Pause'}</button></form></div>
{''.join(cards) or '<div class=card>No pending drafts. 🎉</div>'}
{hidden}
<div class=card><div class=t>Recent</div><ul class=m>{hist or '<li>none</li>'}</ul></div>
</main></body></html>"""
