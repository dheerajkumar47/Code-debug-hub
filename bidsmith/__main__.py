"""CLI: python -m bidsmith <setup|check|demo|serve|run-once>"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from .app import BidSmith
from .config import Settings, mask
from .freelancer import parse_project


def keep_awake() -> None:
    """Windows: stop the PC from sleeping while the bot runs (the screen may still turn off)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        print("  Keeping this PC awake while BidSmith runs (the screen can still turn off).")
    except Exception:
        pass


def run_check(s: Settings) -> int:
    """Only a broken project search blocks start-up. Everything else degrades gracefully with a clear note."""
    bot = BidSmith.from_settings(s)

    # 1) Project search (public API) — the only hard requirement.
    try:
        found = bot.client.search_active("python", limit=3)
        print(f"✅ Freelancer project search works ({len(found)} live projects returned)")
    except Exception as e:
        print(f"❌ Cannot reach Freelancer: {e}\n   Check your internet connection, then run start.bat again.")
        return 1

    # 2) Bidding with the token.
    if not s.freelancer_token:
        print("🟡 No Freelancer token → COPY & PASTE mode (the bot finds, scores and writes; you paste the bid).")
    elif bot.can_bid():
        print(f"✅ Freelancer token accepted → AUTO-BID mode (user id {bot.client.self_id()})")
    else:
        print(f"🟡 Freelancer did not accept the token for bidding → COPY & PASTE mode.\n"
              f"   ({bot.client.auth_error[:160]}; token {mask(s.freelancer_token)})\n"
              f"   Everything else works. To retry later: new token in keys.txt, then start.bat.")

    # 3) AI writer.
    if bot.llm and bot.llm.enabled:
        res = bot.llm.ping()
        if res == "ok":
            bot.remember_model()
            print(f"✅ AI writer works ({getattr(bot.llm, 'names', s.llm_provider)} · model {bot.llm.model})")
        elif res == "busy":
            print(f"🟡 AI key accepted; {s.llm_provider} is busy right now. Proposals start from the ready draft"
                  f" and the AI polishes them when it is free.")
        else:
            print(f"🟡 AI writer not working ({res[:160]}; key {mask(s.llm_api_key)})\n"
                  f"   Drafts use the built-in template until it works. Fix: new key in keys.txt, then start.bat.")
    else:
        print("🟡 No AI key → drafts use the built-in template.")

    # 4) Dashboard login.
    if not s.dashboard_password:
        import secrets as _secrets
        from .setup_wizard import _read_env, _set
        from pathlib import Path
        s.dashboard_password = _secrets.token_urlsafe(12)
        env = Path(".env")
        env.write_text("\n".join(_set(_read_env(env), "DASHBOARD_PASSWORD", s.dashboard_password)) + "\n",
                       encoding="utf-8")
        print(f"✅ Dashboard password created: {s.dashboard_password}")
    print("\nStarting…")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bidsmith")
    ap.add_argument("cmd", choices=["setup", "serve", "run-once", "demo", "check", "leads"])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--file", default="tests/fixtures/projects.json", help="demo: API-shaped JSON file")
    ap.add_argument("--env", default=".env")
    a = ap.parse_args(argv)

    if a.cmd == "setup":
        from .setup_wizard import run
        run(a.env)
        return 0
    if a.cmd == "leads":
        from .leads import run_cli
        return run_cli(a.env)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "httpcore", "uvicorn.access"):  # keep the black window readable
        logging.getLogger(noisy).setLevel(logging.WARNING)
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
    s.background_drafts = True  # cards appear instantly; the AI polishes the proposal seconds later
    keep_awake()

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
    uvicorn.run(create_app(bot), host=a.host, port=a.port, access_log=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
