"""CLI: python -m bidsmith <setup|check|demo|serve|run-once>"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from .app import BidSmith
from .config import Settings
from .freelancer import parse_project


def run_check(s: Settings) -> int:
    """Live checks with plain ✅ / ❌ lines, so problems are obvious."""
    ok = True

    def line(good: bool, text: str):
        nonlocal ok
        ok = ok and good
        print(("✅ " if good else "❌ ") + text)

    bot = BidSmith.from_settings(s)
    if not bot.client:
        line(False, "Freelancer token missing → run: python -m bidsmith setup")
    else:
        try:
            line(True, f"Freelancer token works (your user id {bot.client.self_id()})")
            found = bot.client.search_active("chatbot", limit=3)
            line(True, f"Project search works ({len(found)} live 'chatbot' projects returned)")
        except Exception as e:
            line(False, f"Freelancer API error: {e}")
    if bot.llm and bot.llm.enabled:
        try:
            reply = bot.llm.complete("Reply with one word.", "Say OK", max_tokens=20)
            line(True, f"AI writer works ({s.llm_provider}: {reply[:20]!r})")
        except Exception as e:
            line(False, f"AI key error ({s.llm_provider}): {e}")
    else:
        print("⚠️  No AI key → drafts use the simple template (works, but add a free Gemini key for best bids)")
    if "whatsapp" in s.notify_channels:
        good = bool(s.whatsapp_token and s.whatsapp_phone_number_id and s.owner_whatsapp)
        line(good, "WhatsApp settings present" if good else "WhatsApp enabled but settings missing")
    else:
        print("ℹ️  WhatsApp off → approve bids on the dashboard (add WhatsApp later with: python -m bidsmith setup)")
    line(bool(s.dashboard_password), "Dashboard password set" if s.dashboard_password else "DASHBOARD_PASSWORD missing")
    print("\nReady! Start with: python -m bidsmith serve" if ok else "\nFix the ❌ lines, then run check again.")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bidsmith")
    ap.add_argument("cmd", choices=["setup", "serve", "run-once", "demo", "check"])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--file", default="tests/fixtures/projects.json", help="demo: API-shaped JSON file")
    ap.add_argument("--env", default=".env")
    a = ap.parse_args(argv)

    if a.cmd == "setup":
        from .setup_wizard import run
        run(a.env)
        return 0

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    s = Settings.load(a.env)

    if a.cmd == "check":
        return run_check(s)

    if a.cmd == "demo":
        # Offline run on a saved API response: no Freelancer token, no bids placed.
        s.db_path = ":memory:"
        s.notify_channels = ["console"]
        bot = BidSmith.from_settings(s)
        data = json.load(open(a.file, encoding="utf-8"))
        res = data.get("result", data)
        now = time.time()
        projects = []
        for p in res["projects"]:
            p.setdefault("time_submitted", int(now - 600))
            projects.append(parse_project(p, res.get("users", {})))
        print(json.dumps(bot.process(projects, now), indent=2))
        for r in bot.store.list_projects(("pending", "low_score", "filtered"), 50):
            print(f"[{r['status']:>9}] {r['score'] if r['score'] is not None else '-':>3}  {r['title']}  {r['note'] or ''}")
        return 0

    bot = BidSmith.from_settings(s)
    if a.cmd == "run-once":
        print(json.dumps(bot.run_once(), indent=2))
        return 0

    import socket

    import uvicorn
    from .web import create_app
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sk:
            sk.connect(("8.8.8.8", 80))
            lan = sk.getsockname()[0]
    except OSError:
        lan = "your-pc-ip"
    print(f"\n  Dashboard on this PC:     http://localhost:{a.port}"
          f"\n  Dashboard on your phone:  http://{lan}:{a.port}   (same Wi-Fi)"
          f"\n  Login: {s.dashboard_user} / (DASHBOARD_PASSWORD in .env)\n")
    uvicorn.run(create_app(bot), host=a.host, port=a.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
