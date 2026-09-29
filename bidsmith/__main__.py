"""CLI: python -m bidsmith <serve|run-once|demo|check>"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from .app import BidSmith
from .config import Settings
from .freelancer import parse_project


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bidsmith")
    ap.add_argument("cmd", choices=["serve", "run-once", "demo", "check"])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--file", default="tests/fixtures/projects.json", help="demo: API-shaped JSON file")
    ap.add_argument("--env", default=".env")
    a = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    s = Settings.load(a.env)

    if a.cmd == "check":
        problems = []
        if not s.freelancer_token:
            problems.append("FREELANCER_OAUTH_TOKEN missing (needed to search and bid)")
        if s.llm_provider == "none" or not s.llm_api_key:
            problems.append("No LLM configured — template drafts only (set LLM_PROVIDER + LLM_API_KEY)")
        if "whatsapp" in s.notify_channels and not (s.whatsapp_token and s.whatsapp_phone_number_id and s.owner_whatsapp):
            problems.append("WhatsApp enabled but WHATSAPP_TOKEN / WHATSAPP_PHONE_NUMBER_ID / OWNER_WHATSAPP missing")
        if "web" in s.notify_channels and not s.dashboard_password:
            problems.append("Web dashboard enabled but DASHBOARD_PASSWORD not set")
        bot = BidSmith.from_settings(s)
        if bot.client:
            try:
                problems.append(f"OK: Freelancer user id {bot.client.self_id()}")
            except Exception as e:
                problems.append(f"Freelancer API error: {e}")
        print("\n".join(problems) or "All good.")
        return 0

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

    import uvicorn
    from .web import create_app
    uvicorn.run(create_app(bot), host=a.host, port=a.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
