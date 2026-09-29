"""Interactive setup: asks for secrets (hidden input) and writes .env with owner-only permissions."""
from __future__ import annotations

import getpass
import os
import re
import secrets
from pathlib import Path

FIELDS = [
    # key, prompt, secret, default
    ("FREELANCER_OAUTH_TOKEN", "Freelancer token (Generate Token button)", True, ""),
    ("LLM_PROVIDER", "AI provider: gemini / openai / anthropic / none", False, "gemini"),
    ("LLM_API_KEY", "AI API key (Enter to skip = template drafts)", True, ""),
    ("OWNER_WHATSAPP", "Your WhatsApp number, e.g. 923001234567 (Enter to skip)", False, ""),
    ("WHATSAPP_TOKEN", "WhatsApp Cloud API token (Enter to skip)", True, ""),
    ("WHATSAPP_PHONE_NUMBER_ID", "WhatsApp phone number ID (Enter to skip)", False, ""),
    ("WHATSAPP_APP_SECRET", "Meta app secret (Enter to skip)", True, ""),
]


def _read_env(path: Path) -> list[str]:
    if path.exists():
        return path.read_text(encoding="utf-8").splitlines()
    example = Path(".env.example")
    return example.read_text(encoding="utf-8").splitlines() if example.exists() else []


def _set(lines: list[str], key: str, value: str) -> list[str]:
    pat = re.compile(rf"^{re.escape(key)}=")
    for i, line in enumerate(lines):
        if pat.match(line):
            lines[i] = f"{key}={value}"
            return lines
    return lines + [f"{key}={value}"]


def _current(lines: list[str], key: str) -> str:
    for line in lines:
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1]
    return ""


def run(env_path: str = ".env", ask=input, ask_secret=getpass.getpass) -> Path:
    path = Path(env_path)
    lines = _read_env(path)
    print(f"Writing {path.resolve()} (this file stays on your computer; it is git-ignored).")
    print("Secrets are hidden while you type/paste. Press Enter to keep the current value.\n")
    channels = ["web", "console"]
    for key, prompt, secret, default in FIELDS:
        cur = _current(lines, key)
        shown = ("set" if cur else "empty") if secret else (cur or default or "empty")
        val = (ask_secret if secret else ask)(f"{prompt} [{shown}]: ").strip()
        if not val:
            val = cur or default
        if key == "OWNER_WHATSAPP":
            val = "".join(ch for ch in val if ch.isdigit())
        lines = _set(lines, key, val)
    if _current(lines, "WHATSAPP_TOKEN") and _current(lines, "WHATSAPP_PHONE_NUMBER_ID"):
        channels.insert(0, "whatsapp")
    lines = _set(lines, "NOTIFY_CHANNELS", ",".join(channels))
    if not _current(lines, "WHATSAPP_VERIFY_TOKEN") or "choose-any" in _current(lines, "WHATSAPP_VERIFY_TOKEN"):
        lines = _set(lines, "WHATSAPP_VERIFY_TOKEN", secrets.token_urlsafe(24))
    if not _current(lines, "DASHBOARD_PASSWORD"):
        pw = secrets.token_urlsafe(12)
        lines = _set(lines, "DASHBOARD_PASSWORD", pw)
        print(f"\nDashboard login → user: owner  password: {pw}  (saved in .env)")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # Windows
    print(f"\nSaved. Next: python -m bidsmith check")
    return path
