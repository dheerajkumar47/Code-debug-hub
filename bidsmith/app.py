"""The pipeline and owner actions. Channels (WhatsApp, web) call into BidSmith."""
from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import asdict

from . import proposal, quality
from .config import Profile, Settings
from .filters import rule_filter
from .freelancer import FreelancerAuthError, FreelancerClient, FreelancerError
from .llm import LLM
from .models import Price, Project
from .notify import Card, ConsoleNotifier, WebNotifier, WhatsAppNotifier
from .pricing import compute_price
from .retrieval import PortfolioIndex
from .scoring import heuristic_score, llm_refine
from .store import Store

log = logging.getLogger(__name__)

HELP = """BidSmith commands:
• list — pending drafts
• bid <id> — place the bid
• skip <id> — skip it
• edit <id> — then send the new text
• regen <id> — write a new draft
• price <id> <amount> [days] — change price/period
• stats — today's numbers
• pause / resume — stop/start searching
• cancel — cancel an edit"""


class BidSmith:
    def __init__(self, settings: Settings, profile: Profile, store: Store,
                 client: FreelancerClient | None = None, llm: LLM | None = None, notifiers=None):
        self.s = settings
        self.profile = profile
        self.store = store
        self.client = client
        self.llm = llm
        self.index = PortfolioIndex(profile.portfolio)
        self.notifiers = notifiers if notifiers is not None else [ConsoleNotifier()]
        remembered = store.kv_get("llm_model")
        if llm is not None and remembered and not settings.llm_model:
            llm.model = remembered  # a model that worked last time (Google retires names)

    def remember_model(self) -> None:
        if self.llm is not None and getattr(self.llm, "model", None):
            self.store.kv_set("llm_model", self.llm.model)

    # ---------------------------------------------------------------- build
    @classmethod
    def from_settings(cls, s: Settings) -> "BidSmith":
        profile = Profile.load(s.profile_path)
        store = Store(s.db_path)
        # Always create the client: project search is public; bidding only needs the token.
        client = FreelancerClient(s.freelancer_token or None, s.freelancer_api_url, s.freelancer_site_url)
        llm = LLM(s.llm_provider, s.llm_api_key, s.llm_model, s.llm_base_url)
        notifiers = []
        for ch in s.notify_channels:
            if ch == "console":
                notifiers.append(ConsoleNotifier())
            elif ch == "web":
                notifiers.append(WebNotifier())
            elif ch == "whatsapp":
                notifiers.append(WhatsAppNotifier(
                    s.whatsapp_token, s.whatsapp_phone_number_id, s.owner_whatsapp, store,
                    s.whatsapp_api_version, s.whatsapp_template_name, s.whatsapp_template_lang))
        return cls(s, profile, store, client, llm, notifiers)

    def notify_text(self, text: str) -> None:
        for n in self.notifiers:
            try:
                n.send_text(text)
            except Exception as e:
                log.error("notify %s failed: %s", n.name, e)

    def _card(self, pid: int) -> Card | None:
        row, d = self.store.get_project(pid), self.store.get_draft(pid)
        if not row or not d:
            return None
        q = json.loads(d["quality"] or "{}")
        dash = f"{self.s.public_base_url}/#p{pid}" if self.s.public_base_url else ""
        return Card(pid, row["title"], row["url"], row["score"] or 0, json.loads(row["reasons"] or "[]"),
                    f"{d['amount']:.0f} {d['currency']} (${d['amount_usd']:.0f}) · {d['period_days']}d",
                    d["text"], q.get("issues", []), dash)

    def push_card(self, pid: int) -> None:
        card = self._card(pid)
        if not card:
            return
        for n in self.notifiers:
            try:
                n.send_card(card)
            except Exception as e:
                log.error("notify %s failed: %s", n.name, e)

    # ------------------------------------------------------------- pipeline
    def paused(self) -> bool:
        return self.store.kv_get("paused") == "1"

    def discover(self) -> list[Project]:
        search = self.profile.search
        since = int(time.time() - float(search.get("max_age_hours", 24) or 24) * 3600)
        found: dict[int, Project] = {}
        for q in search.get("queries", [""]):
            try:
                for p in self.client.search_active(q, search.get("job_ids", []),
                                                   search.get("project_types", []), limit=50,
                                                   from_time=since):
                    found.setdefault(p.id, p)
            except FreelancerError as e:
                log.error("search '%s' failed: %s", q, e)
            time.sleep(random.uniform(0.8, 2.0))  # polite pacing
        return list(found.values())

    def process(self, projects: list[Project], now: float | None = None, recheck: bool = False) -> dict:
        stats = {"new": 0, "filtered": 0, "low_score": 0, "pending": 0, "auto_bid": 0}
        for p in projects:
            if not recheck and self.store.seen(p.id):
                continue
            stats["new"] += 1
            ok, why = rule_filter(p, self.profile, now)
            if not ok:
                # still score it, so crowded/old but perfect-fit projects can be shown to you
                self.store.save_project(p, "filtered", heuristic_score(p, self.profile, self.index, now),
                                        note="; ".join(why))
                stats["filtered"] += 1
                continue
            score = heuristic_score(p, self.profile, self.index, now)
            if self.s.llm_score_enabled and self.llm and self.llm.enabled and \
                    score.score >= self.threshold() - 15:
                score = llm_refine(score, p, self.profile, self.llm)
            if score.score < self.threshold():
                self.store.save_project(p, "low_score", score)
                stats["low_score"] += 1
                continue
            price = compute_price(p, self.profile, score.score, self.s.milestone_percentage)
            draft = proposal.write(p, self.profile, self.index, price, self.llm)
            self.store.save_project(p, "pending", score)
            self.store.save_draft(draft)
            if self._can_auto_submit(score.score, draft.quality.passed):
                res = self.approve(p.id, source="auto")
                if res.startswith("✅"):
                    stats["auto_bid"] += 1
                    self.notify_text(f"🤖 Auto-bid placed on #{p.id}: {p.title}\n{p.url}")
                    continue
            stats["pending"] += 1
            self.push_card(p.id)
        return stats

    def threshold(self) -> int:
        """Minimum score for a card. Set from the dashboard (saved), else from .env."""
        v = self.store.kv_get("score_threshold")
        return int(v) if v and v.isdigit() else self.s.score_threshold

    def set_threshold(self, value: int) -> str:
        value = max(30, min(95, int(value)))
        self.store.kv_set("score_threshold", str(value))
        return f"Minimum score set to {value}. Press ♻ Re-check hidden to apply it to projects already seen."

    def recheck_hidden(self) -> dict:
        """Run hidden projects (filtered / weak) through the current rules and score again."""
        rows = self.store.list_projects(("filtered", "low_score"), 500)
        projects = [p for p in (self.store.project_obj(r["id"]) for r in rows) if p]
        return self.process(projects, recheck=True)

    def draft_anyway(self, pid: int) -> str:
        """Owner override: write a bid for a hidden project."""
        p = self.store.project_obj(pid)
        if not p:
            return f"❓ #{pid} not found"
        score = heuristic_score(p, self.profile, self.index)
        price = compute_price(p, self.profile, score.score, self.s.milestone_percentage)
        self.store.save_project(p, "pending", score)
        self.store.save_draft(proposal.write(p, self.profile, self.index, price, self.llm))
        return f"✍ Bid written for #{pid} — it is at the top of your list."

    SOFT_REASONS = ("bids >", "too old")  # crowded or older: still worth a look if the fit is great

    def hidden_summary(self, limit: int = 8, now: float | None = None) -> tuple[list[tuple[str, int]], list[dict], list[dict]]:
        """(top filter reasons, best weak matches, good fits hidden only for being crowded/old)."""
        from collections import Counter
        reasons: Counter = Counter()
        for r in self.store.list_projects(("filtered",), 1000):
            for part in (r.get("note") or "").split("; "):
                if part:
                    key = part
                    key = "budget too small" if key.startswith("budget $") else key
                    key = "too many bids already" if " bids > " in key else key
                    key = "hourly rate below your floor" if key.startswith("hourly max") else key
                    key = "too old (over 24h)" if key.startswith("too old") else key
                    reasons[key] += 1
        weak = sorted(self.store.list_projects(("low_score",), 500), key=lambda r: r["score"] or 0, reverse=True)
        now = now or time.time()

        def worth_it(r: dict) -> bool:  # a week old or 150+ bids is not worth a paid bid
            d = json.loads(r["data"] or "{}")
            return d.get("bid_count", 0) <= 150 and (now - (d.get("time_submitted") or now)) <= 72 * 3600

        soft = [r for r in self.store.list_projects(("filtered",), 1000)
                if (r["score"] or 0) >= self.threshold() - 10 and r.get("note") and worth_it(r)
                and all(any(k in part for k in self.SOFT_REASONS) for part in r["note"].split("; "))]
        soft.sort(key=lambda r: r["score"] or 0, reverse=True)
        return reasons.most_common(6), weak[:limit], soft[:limit]

    def run_once(self) -> dict:
        if self.paused():
            return {"paused": True}
        stats = self.process(self.discover())
        self.remember_model()
        return stats

    # -------------------------------------------------------------- safety
    def _can_auto_submit(self, score: int, quality_ok: bool) -> bool:
        return (self.s.auto_submit and quality_ok and self.can_bid() and score >= self.s.auto_submit_min_score
                and self.store.bids_since(time.time() - 86400) < self.s.max_bids_per_day
                and time.time() - self.store.last_bid_at() >= self.s.min_seconds_between_bids)

    # ------------------------------------------------------------- actions
    MANUAL = "📋 Press Copy, then Open, and paste the bid on Freelancer. Then press ✔ Done."

    def can_bid(self) -> bool:
        """False → manual mode: the bot still finds, scores and writes; you paste the bid yourself."""
        if not self.client:
            return False
        check = getattr(self.client, "can_bid", None)
        return check() if check else True

    def mark_done(self, pid: int) -> str:
        if not self.store.get_project(pid):
            return f"❓ #{pid} not found"
        d = self.store.get_draft(pid) or {}
        self.store.save_bid(pid, None, d.get("amount", 0), d.get("amount_usd", 0), d.get("period_days", 0), "placed",
                            {"manual": True})
        self.store.set_status(pid, "bid_placed", "placed manually")
        return f"✔ Marked #{pid} as bid"

    def approve(self, pid: int, source: str = "owner") -> str:
        row, d = self.store.get_project(pid), self.store.get_draft(pid)
        if not row or not d:
            return f"❓ #{pid} not found"
        if row["status"] in ("bid_placed", "auto_bid"):
            return f"ℹ️ Already bid on #{pid}"
        if not self.can_bid():
            return self.MANUAL
        if source == "owner" and self.store.bids_since(time.time() - 86400) >= self.s.max_bids_per_day:
            log.warning("daily cap reached but owner approved #%s manually", pid)
        wait = self.s.min_seconds_between_bids - (time.time() - self.store.last_bid_at())
        if wait > 0:
            if source == "auto":
                return "⏳ spacing"
            time.sleep(min(wait, 180) + random.uniform(1, 5))
        try:
            res = self.client.place_bid(pid, d["amount"], d["period_days"], d["text"],
                                        d["milestone_percentage"] or self.s.milestone_percentage)
        except FreelancerAuthError:
            return self.MANUAL  # token not accepted for bidding; the card stays so you can paste it
        except FreelancerError as e:
            self.store.set_status(pid, "bid_failed", str(e))
            self.store.save_bid(pid, None, d["amount"], d["amount_usd"], d["period_days"], "failed",
                                {"error": str(e)})
            return f"❌ Bid failed on #{pid}: {e}. " + self.MANUAL
        bid_id = (res or {}).get("id")
        self.store.save_bid(pid, bid_id, d["amount"], d["amount_usd"], d["period_days"], "placed", res)
        self.store.set_status(pid, "auto_bid" if source == "auto" else "bid_placed", f"bid {bid_id}")
        return f"✅ Bid placed on #{pid} ({d['amount']:.0f} {d['currency']}, {d['period_days']}d)"

    def skip(self, pid: int) -> str:
        if not self.store.get_project(pid):
            return f"❓ #{pid} not found"
        self.store.set_status(pid, "skipped")
        return f"⏭ Skipped #{pid}"

    def edit(self, pid: int, text: str) -> str:
        p = self.store.project_obj(pid)
        d = self.store.get_draft(pid)
        if not p or not d:
            return f"❓ #{pid} not found"
        price = Price(d["amount"], d["period_days"], d["currency"], d["amount_usd"], "")
        rep = quality.check(text, p, self.profile.corpus, self.profile.style, proposal._numbers(price))
        self.store.update_draft_text(pid, text.strip(), json.dumps(asdict(rep)))
        self.store.set_status(pid, "pending")
        note = ("\n⚠ " + "; ".join(rep.issues)) if rep.issues else " (all checks passed)"
        return f"✏️ Draft #{pid} updated{note}"

    def regenerate(self, pid: int) -> str:
        p = self.store.project_obj(pid)
        row = self.store.get_project(pid)
        if not p or not row:
            return f"❓ #{pid} not found"
        price = compute_price(p, self.profile, row["score"] or 0, self.s.milestone_percentage)
        d = self.store.get_draft(pid)
        if d:  # keep any manual price change
            price = Price(d["amount"], d["period_days"], d["currency"], d["amount_usd"], d["price_note"] or "",
                          d["milestone_percentage"] or self.s.milestone_percentage)
        self.store.save_draft(proposal.write(p, self.profile, self.index, price, self.llm))
        self.store.set_status(pid, "pending")
        return f"🔁 New draft for #{pid}"

    def set_price(self, pid: int, amount: float, days: int | None = None) -> str:
        p, d = self.store.project_obj(pid), self.store.get_draft(pid)
        if not p or not d:
            return f"❓ #{pid} not found"
        usd = p.to_usd(amount)
        floor = self.profile.hourly_floor_usd if p.type == "hourly" else self.profile.fixed_floor_usd
        warn = f" ⚠ below your floor ${floor:.0f}" if usd < floor else ""
        self.store.update_draft_price(pid, amount, usd, days or d["period_days"])
        return f"💲 #{pid} price {amount:.0f} {p.currency} (${usd:.0f}), {days or d['period_days']}d{warn}"

    # ------------------------------------------------------- chat commands
    def handle_command(self, text: str) -> tuple[str, int | None]:
        """Returns (reply, project_id_to_show_again)."""
        t = text.strip()
        low = t.lower()
        editing = self.store.kv_get("editing")

        if low in ("help", "?", "menu"):
            return HELP, None
        if low == "cancel":
            self.store.kv_del("editing")
            return "Edit cancelled.", None
        if low == "pause":
            self.store.kv_set("paused", "1")
            return "⏸ Paused. Send 'resume' to continue.", None
        if low == "resume":
            self.store.kv_set("paused", "0")
            return "▶️ Resumed.", None
        if low == "stats":
            return "📊 " + json.dumps(self.store.stats()), None
        if low == "list":
            rows = self.store.list_projects(("pending",), 10)
            if not rows:
                return "No pending drafts.", None
            return "\n".join(f"#{r['id']} · {r['score']} · {r['title'][:50]}" for r in rows), None

        m = re.match(r"^(bid|approve|skip|edit|regen|price)\s+#?(\d+)(?:\s+([\d.]+))?(?:\s+(\d+))?\s*$", low)
        if m:
            cmd, pid = m.group(1), int(m.group(2))
            if cmd in ("bid", "approve"):
                return self.approve(pid), None
            if cmd == "skip":
                return self.skip(pid), None
            if cmd == "regen":
                return self.regenerate(pid), pid
            if cmd == "edit":
                if not self.store.get_draft(pid):
                    return f"❓ #{pid} not found", None
                self.store.kv_set("editing", str(pid))
                return f"Send the new proposal text for #{pid} (or 'cancel').", None
            if cmd == "price" and m.group(3):
                return self.set_price(pid, float(m.group(3)), int(m.group(4)) if m.group(4) else None), pid

        if editing:
            self.store.kv_del("editing")
            pid = int(editing)
            return self.edit(pid, t), pid
        return "Didn't understand. " + HELP, None

    def handle_button(self, button_id: str) -> tuple[str, int | None]:
        action, _, pid_s = button_id.partition(":")
        if not pid_s.isdigit():
            return "Unknown button.", None
        pid = int(pid_s)
        if action == "approve":
            return self.approve(pid), None
        if action == "skip":
            return self.skip(pid), None
        if action == "edit":
            self.store.kv_set("editing", str(pid))
            return (f"Send the new proposal text for #{pid}.\n"
                    f"Or: 'regen {pid}' for a new AI draft, 'price {pid} <amount> [days]' to change price."), None
        return "Unknown button.", None
