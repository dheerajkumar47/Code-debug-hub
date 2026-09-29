"""Setup: reads your keys from keys.txt (easiest) or asks for them, then writes .env.

keys.txt (in the bot folder, made with Notepad), for example:
    FREELANCER: <your freelancer token>
    GEMINI: <your gemini key>
It is deleted after import so the keys only live in .env.
"""
from __future__ import annotations

import os
import re
import secrets
from pathlib import Path

from .config import clean_secret, mask

REQUIRED = [
    # key, prompt, secret, default
    ("FREELANCER_OAUTH_TOKEN", "1/2  Freelancer token (Generate Token button)", True, ""),
    ("LLM_PROVIDER", "     AI provider: gemini / openai / anthropic / none", False, "gemini"),
    ("LLM_API_KEY", "2/2  AI API key (free Gemini key from aistudio.google.com)", True, ""),
]
WHATSAPP = [
    ("OWNER_WHATSAPP", "Your WhatsApp number, e.g. 923001234567", False, ""),
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


KEY_FILES = ("keys.txt", "keys.txt.txt", "keys")
_PROVIDER_LABELS = {"gemini": "gemini", "google": "gemini", "openai": "openai", "gpt": "openai",
                    "claude": "anthropic", "anthropic": "anthropic"}


def find_keys_file(folder: Path = Path(".")) -> Path | None:
    return next((folder / n for n in KEY_FILES if (folder / n).is_file()), None)


def parse_keys_file(text: str) -> dict[str, str]:
    """Lenient: 'FREELANCER: xxx', 'freelancer=xxx', 'GEMINI: xxx' or just two lines (token, then AI key)."""
    out: dict[str, str] = {}
    unlabeled = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z_ ]{2,30}?)\s*[:=]\s*(\S.*)$", line)
        label = m.group(1).strip().lower() if m else ""
        known = label and ("freelancer" in label or label in ("token", "fl") or
                           any(k in label for k in _PROVIDER_LABELS))
        if not known:
            m, label = None, ""
        value = clean_secret(m.group(2)) if m else clean_secret(line)
        if "freelancer" in label or label in ("token", "fl"):
            out["FREELANCER_OAUTH_TOKEN"] = value
        elif any(k in label for k in _PROVIDER_LABELS):
            prov = next(v for k, v in _PROVIDER_LABELS.items() if k in label)
            out["LLM_PROVIDER"], out["LLM_API_KEY"] = prov, value
        elif value:
            unlabeled.append(value)
    if "FREELANCER_OAUTH_TOKEN" not in out and unlabeled:
        out["FREELANCER_OAUTH_TOKEN"] = unlabeled.pop(0)
    if "LLM_API_KEY" not in out and unlabeled:
        out["LLM_PROVIDER"], out["LLM_API_KEY"] = "gemini", unlabeled.pop(0)
    return out


def _ask_field(lines, key, prompt, secret, default, ask, ask_secret) -> list[str]:
    cur = _current(lines, key)
    shown = ("set" if cur else "empty") if secret else (cur or default or "empty")
    raw = (ask_secret if secret else ask)(f"{prompt} [{shown}]: ")
    val = raw
    if secret:
        val = clean_secret(raw)
        if raw.strip() and len(val) < 20:  # something was pasted but it is not a real key
            print(f"   ⚠ Only {len(val)} characters arrived — the paste did not work.")
            val = clean_secret(ask("   Paste again, then Enter: "))
        if val:
            print(f"   ✔ received {mask(val)}")
    val = val.strip()
    if not val:
        val = cur or default
    if key == "OWNER_WHATSAPP":
        val = "".join(ch for ch in val if ch.isdigit())
    return _set(lines, key, val)


def run(env_path: str = ".env", ask=input, ask_secret=input) -> Path:
    path = Path(env_path)
    lines = _read_env(path)
    print(f"Writing {path.resolve()} (this file stays on your computer; it is git-ignored).")
    channels = ["web", "console"]
    keys_file = find_keys_file(path.parent)
    if keys_file:
        found = parse_keys_file(keys_file.read_text(encoding="utf-8-sig", errors="ignore"))
        for k, v in found.items():
            lines = _set(lines, k, v)
        print(f"Read {keys_file.name}:")
        if "FREELANCER_OAUTH_TOKEN" in found:
            print(f"   ✔ Freelancer token  {mask(found['FREELANCER_OAUTH_TOKEN'])}")
        if "LLM_API_KEY" in found:
            print(f"   ✔ {found['LLM_PROVIDER']} key  {mask(found['LLM_API_KEY'])}")
        missing = [k for k in ("FREELANCER_OAUTH_TOKEN", "LLM_API_KEY") if k not in found]
        for key, prompt, secret, default in REQUIRED:
            if key in missing or (key == "LLM_PROVIDER" and "LLM_API_KEY" in missing):
                lines = _ask_field(lines, key, prompt, secret, default, ask, ask_secret)
    else:
        print("Paste each key and press Enter (right-click or Ctrl+V). Enter alone keeps the current value.\n")
        for key, prompt, secret, default in REQUIRED:
            lines = _ask_field(lines, key, prompt, secret, default, ask, ask_secret)
    if not keys_file and ask("\nSet up WhatsApp now? You can do it later. (y/N): ").strip().lower().startswith("y"):
        for key, prompt, secret, default in WHATSAPP:
            lines = _ask_field(lines, key, prompt, secret, default, ask, ask_secret)
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
    if keys_file:
        try:
            keys_file.unlink()
            print(f"   ({keys_file.name} deleted — your keys are now only in .env)")
        except OSError:
            print(f"   Please delete {keys_file.name} yourself — your keys are now in .env")
    print("\nSaved. Next: python -m bidsmith check")
    return path
