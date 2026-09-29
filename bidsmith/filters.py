"""Stage 1: cheap, deterministic rules. A project must pass all of them."""
from __future__ import annotations

import re
import time

from .config import Profile
from .models import Project


def rule_filter(p: Project, profile: Profile, now: float | None = None) -> tuple[bool, list[str]]:
    s = profile.search
    now = now or time.time()
    fails: list[str] = []

    types = s.get("project_types") or ["fixed", "hourly"]
    if p.type not in types:
        fails.append(f"type {p.type} not wanted")

    min_budget = float(s.get("min_budget_usd", 0))
    if p.type == "fixed" and p.budget_max_usd and p.budget_max_usd < min_budget:
        fails.append(f"budget ${p.budget_max_usd:.0f} < ${min_budget:.0f}")
    if p.type == "hourly" and p.budget_max_usd and p.budget_max_usd < profile.hourly_floor_usd:
        fails.append(f"hourly max ${p.budget_max_usd:.0f} < floor ${profile.hourly_floor_usd:.0f}")

    max_bids = int(s.get("max_bid_count", 10_000))
    if p.bid_count > max_bids:
        fails.append(f"{p.bid_count} bids > {max_bids}")

    max_age_h = float(s.get("max_age_hours", 0) or 0)
    if max_age_h and p.time_submitted and (now - p.time_submitted) > max_age_h * 3600:
        fails.append("too old")

    if s.get("require_payment_verified") and not p.client.payment_verified:
        fails.append("client payment not verified")

    min_rating = float(s.get("min_client_rating", 0) or 0)
    if min_rating and p.client.reviews and p.client.rating < min_rating:
        fails.append(f"client rating {p.client.rating:.1f} < {min_rating}")

    blocked = {c.lower() for c in s.get("blocked_countries", [])}
    if p.client.country and p.client.country.lower() in blocked:
        fails.append(f"country {p.client.country} blocked")

    allowed_cur = {c.upper() for c in s.get("allowed_currencies", [])}
    if allowed_cur and p.currency.upper() not in allowed_cur:
        fails.append(f"currency {p.currency} not allowed")

    text = p.text.lower()
    for kw in s.get("exclude_keywords", []):
        # whole words only: "exam" must not match "example"
        if re.search(rf"(?<![a-z0-9]){re.escape(kw.lower())}(?![a-z0-9])", text):
            fails.append(f"excluded keyword '{kw}'")
            break

    if p.nda and s.get("skip_nda", True):
        fails.append("NDA project (review manually)")

    return (not fails, fails)
