#!/usr/bin/env bash
# BidSmith server updater (Azure VM). Downloads the latest code from the public GitHub repo,
# keeps .env (keys) and data/ (history), reinstalls libraries and restarts the bot.
set -euo pipefail
APP=/opt/bidsmith/app
REPO="dheerajkumar47/Code-debug-hub"
BRANCH="claude/funny-noether-d41u0f"
TMP=$(mktemp -d)
curl -fsSL --retry 3 "https://codeload.github.com/${REPO}/tar.gz/refs/heads/${BRANCH}" \
  | tar -xz -C "$TMP" --strip-components=1
mkdir -p "$APP"
rsync -a --delete --exclude .env --exclude data --exclude .venv "$TMP"/ "$APP"/
rm -rf "$TMP"
[ -d "$APP/.venv" ] || python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install -q --disable-pip-version-check -r "$APP/requirements.txt"
mkdir -p "$APP/data"
chown -R bidsmith:bidsmith "$APP"
systemctl restart bidsmith || true
echo "BidSmith updated $(date)"
