"""SQLite storage: every project seen, its score, draft, decision and bid."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import Draft, Project, ScoreResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  title TEXT, url TEXT, data TEXT,
  score INTEGER, reasons TEXT,
  status TEXT NOT NULL,            -- filtered | low_score | pending | approved | bid_placed | bid_failed | skipped | auto_bid
  note TEXT,
  created_at REAL, updated_at REAL
);
CREATE TABLE IF NOT EXISTS drafts (
  project_id INTEGER PRIMARY KEY,
  text TEXT, amount REAL, amount_usd REAL, currency TEXT, period_days INTEGER,
  milestone_percentage INTEGER, price_note TEXT, quality TEXT, portfolio TEXT, version INTEGER DEFAULT 1,
  updated_at REAL
);
CREATE TABLE IF NOT EXISTS bids (
  project_id INTEGER PRIMARY KEY,
  bid_id INTEGER, amount REAL, amount_usd REAL, period_days INTEGER, placed_at REAL, status TEXT, raw TEXT
);
CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
"""


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._db.executescript(SCHEMA)

    def _x(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._db.execute(sql, args)
            self._db.commit()
            return cur

    # --- projects ------------------------------------------------------
    def seen(self, project_id: int) -> bool:
        return self._x("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is not None

    def save_project(self, p: Project, status: str, score: ScoreResult | None = None, note: str = "") -> None:
        now = time.time()
        self._x(
            """INSERT INTO projects(id,title,url,data,score,reasons,status,note,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET score=excluded.score, reasons=excluded.reasons,
                 status=excluded.status, note=excluded.note, data=excluded.data, updated_at=excluded.updated_at""",
            (p.id, p.title, p.url, json.dumps(asdict(p)), score.score if score else None,
             json.dumps((score.reasons + [f"⚠ {f}" for f in score.red_flags]) if score else []),
             status, note, now, now))

    def set_status(self, project_id: int, status: str, note: str = "") -> None:
        self._x("UPDATE projects SET status=?, note=?, updated_at=? WHERE id=?",
                (status, note, time.time(), project_id))

    def update_bid_count(self, project_id: int, bid_count: int) -> None:
        row = self.get_project(project_id)
        if not row:
            return
        d = json.loads(row["data"] or "{}")
        d["bid_count"] = bid_count
        self._x("UPDATE projects SET data=? WHERE id=?", (json.dumps(d), project_id))

    def get_project(self, project_id: int) -> dict[str, Any] | None:
        row = self._x("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return dict(row) if row else None

    def list_projects(self, statuses: tuple[str, ...] = ("pending",), limit: int = 50) -> list[dict]:
        q = f"SELECT * FROM projects WHERE status IN ({','.join('?' * len(statuses))}) ORDER BY updated_at DESC LIMIT ?"
        return [dict(r) for r in self._x(q, (*statuses, limit)).fetchall()]

    def project_obj(self, project_id: int) -> Project | None:
        from .models import Client
        row = self.get_project(project_id)
        if not row:
            return None
        d = json.loads(row["data"])
        d["client"] = Client(**d.get("client", {}))
        return Project(**d)

    # --- drafts --------------------------------------------------------
    def save_draft(self, d: Draft) -> None:
        self._x(
            """INSERT INTO drafts(project_id,text,amount,amount_usd,currency,period_days,milestone_percentage,
                 price_note,quality,portfolio,version,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,1,?)
               ON CONFLICT(project_id) DO UPDATE SET text=excluded.text, amount=excluded.amount,
                 amount_usd=excluded.amount_usd, period_days=excluded.period_days, quality=excluded.quality,
                 price_note=excluded.price_note, portfolio=excluded.portfolio,
                 version=drafts.version+1, updated_at=excluded.updated_at""",
            (d.project_id, d.text, d.price.amount, d.price.amount_usd, d.price.currency, d.price.period_days,
             d.price.milestone_percentage, d.price.explanation, json.dumps(asdict(d.quality)),
             json.dumps(d.portfolio_used), time.time()))

    def get_draft(self, project_id: int) -> dict | None:
        row = self._x("SELECT * FROM drafts WHERE project_id=?", (project_id,)).fetchone()
        return dict(row) if row else None

    def update_draft_text(self, project_id: int, text: str, quality_json: str) -> None:
        self._x("UPDATE drafts SET text=?, quality=?, version=version+1, updated_at=? WHERE project_id=?",
                (text, quality_json, time.time(), project_id))

    def update_draft_price(self, project_id: int, amount: float, amount_usd: float, period_days: int) -> None:
        self._x("UPDATE drafts SET amount=?, amount_usd=?, period_days=?, updated_at=? WHERE project_id=?",
                (amount, amount_usd, period_days, time.time(), project_id))

    # --- bids ----------------------------------------------------------
    def save_bid(self, project_id: int, bid_id: int | None, amount: float, amount_usd: float,
                 period_days: int, status: str, raw: dict | None = None) -> None:
        self._x("""INSERT OR REPLACE INTO bids(project_id,bid_id,amount,amount_usd,period_days,placed_at,status,raw)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (project_id, bid_id, amount, amount_usd, period_days, time.time(), status, json.dumps(raw or {})))

    def bids_since(self, ts: float) -> int:
        return self._x("SELECT COUNT(*) FROM bids WHERE status='placed' AND placed_at>=?", (ts,)).fetchone()[0]

    def last_bid_at(self) -> float:
        v = self._x("SELECT MAX(placed_at) FROM bids WHERE status='placed'").fetchone()[0]
        return float(v or 0)

    def stats(self) -> dict:
        rows = self._x("SELECT status, COUNT(*) c FROM projects GROUP BY status").fetchall()
        out = {r["status"]: r["c"] for r in rows}
        out["bids_placed_24h"] = self.bids_since(time.time() - 86400)
        return out

    # --- key/value -----------------------------------------------------
    def kv_get(self, key: str, default: str | None = None) -> str | None:
        row = self._x("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def kv_set(self, key: str, value: str) -> None:
        self._x("INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)", (key, value))

    def kv_del(self, key: str) -> None:
        self._x("DELETE FROM kv WHERE key=?", (key,))
