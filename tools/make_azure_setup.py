"""Create the Azure VM 'Custom data' (cloud-init) file that installs BidSmith by itself.

    python tools/make_azure_setup.py      (or double-click azure.bat)

Reads your .env (keys), asks for a login password + a web address name, and writes
azure-cloud-init.txt — paste its whole content into Azure Portal → Create VM → Advanced → Custom data.
The file contains your keys: do not share it; it is git-ignored.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "azure-cloud-init.txt"
REGIONS = {"1": "uaenorth", "2": "centralindia", "3": "eastus", "4": "westeurope"}


def indent(text: str, n: int = 6) -> str:
    return "\n".join((" " * n + line) if line else "" for line in text.splitlines())


def build(env_text: str, fqdn: str) -> str:
    env = env_text.replace("\r", "").strip()
    env = re.sub(r"(?m)^(DB_PATH|PUBLIC_BASE_URL)=.*\n?", "", env).strip()
    env += f"\nDB_PATH=data/bidsmith.db\nPUBLIC_BASE_URL=https://{fqdn}\n"
    update = (ROOT / "deploy" / "update.sh").read_text(encoding="utf-8")
    service = """[Unit]
Description=BidSmith bid bot
After=network-online.target
Wants=network-online.target

[Service]
User=bidsmith
WorkingDirectory=/opt/bidsmith/app
ExecStart=/opt/bidsmith/app/.venv/bin/python -m bidsmith serve --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    caddy = f"{fqdn} {{\n  encode gzip\n  reverse_proxy 127.0.0.1:8000\n}}\n"
    return f"""#cloud-config
package_update: true
packages: [python3-venv, python3-pip, rsync, curl, debian-keyring, debian-archive-keyring, apt-transport-https, gnupg]
write_files:
  - path: /opt/bidsmith/update.sh
    permissions: '0750'
    content: |
{indent(update)}
  - path: /opt/bidsmith/env
    permissions: '0600'
    content: |
{indent(env)}
  - path: /etc/systemd/system/bidsmith.service
    content: |
{indent(service)}
  - path: /opt/bidsmith/Caddyfile
    content: |
{indent(caddy)}
runcmd:
  - useradd --system --home /opt/bidsmith --shell /usr/sbin/nologin bidsmith || true
  - mkdir -p /opt/bidsmith/app
  - install -m 600 /opt/bidsmith/env /opt/bidsmith/app/.env
  - rm -f /opt/bidsmith/env
  - curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  - curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt -o /etc/apt/sources.list.d/caddy-stable.list
  - apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y caddy
  - cp /opt/bidsmith/Caddyfile /etc/caddy/Caddyfile
  - systemctl daemon-reload
  - systemctl enable bidsmith
  - /opt/bidsmith/update.sh
  - chown -R bidsmith:bidsmith /opt/bidsmith
  - chown root:root /opt/bidsmith/update.sh
  - systemctl restart caddy
"""


def main() -> int:
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("No .env found. Run start.bat once first so your keys are saved.")
        return 1
    env_text = env_path.read_text(encoding="utf-8")
    print("BidSmith → Azure setup file\n")
    pw = input("1) Choose your login password (at least 8 characters, easy for you to remember): ").strip()
    if len(pw) < 8 or any(c in pw for c in " \"'#"):
        print("   Use at least 8 characters, without spaces, quotes or #.")
        return 1
    env_text = re.sub(r"(?m)^DASHBOARD_(PASSWORD|USER)=.*\n?", "", env_text).rstrip()
    env_text += f"\nDASHBOARD_USER=owner\nDASHBOARD_PASSWORD={pw}\n"
    env_path.write_text(env_text, encoding="utf-8")
    label = input("2) Web address name, e.g. bidsmith-dheeraj (letters, numbers, dashes): ").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,60}[a-z0-9]", label):
        print("   Use 4-62 lowercase letters, numbers or dashes, starting with a letter.")
        return 1
    print("3) Azure region (must be the SAME region you pick when creating the VM):")
    for k, v in REGIONS.items():
        print(f"   {k}. {v}")
    choice = input("   Number or region name [1]: ").strip() or "1"
    region = REGIONS.get(choice, choice.lower())
    fqdn = f"{label}.{region}.cloudapp.azure.com"
    OUT.write_text(build(env_text, fqdn), encoding="utf-8")
    print(f"\n✅ Created {OUT.name}")
    print(f"   Your bot's address will be:  https://{fqdn}")
    print(f"   DNS name label to set in Azure:  {label}")
    print(f"   Login:  owner  /  {pw}")
    print("   Next: follow docs/09-AZURE.md step 3 (paste the file into 'Custom data').")
    print("   ⚠ This file contains your keys. Do not share it. Delete it after the VM is created.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
