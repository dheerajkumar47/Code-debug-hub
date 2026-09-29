"""Price + delivery period per project. Never below the owner's floor."""
from __future__ import annotations

from .config import Profile
from .models import Price, Project


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x)) if hi >= lo else lo


def _period_days(usd: float) -> int:
    if usd < 100:
        return 3
    if usd < 300:
        return 7
    if usd < 1000:
        return 14
    return 21


def compute_price(p: Project, profile: Profile, score: int, milestone_percentage: int = 50) -> Price:
    new_seller = profile.reviews_count < 5
    lo, hi = p.budget_min_usd, max(p.budget_max_usd, p.budget_min_usd)

    if p.type == "hourly":
        floor = profile.hourly_floor_usd
        anchor = p.bid_avg_usd or (lo + hi) / 2 or profile.target_hourly_usd
        target = min(anchor, profile.target_hourly_usd) if new_seller else max(anchor, profile.target_hourly_usd)
        usd = max(floor, _clamp(target, lo or floor, hi or target))
        why = (f"hourly: budget ${lo:.0f}-${hi:.0f}, avg bid ${p.bid_avg_usd:.0f}, "
               f"floor ${floor:.0f}{', new-seller discount' if new_seller else ''}")
        days = 7
    else:
        floor = profile.fixed_floor_usd
        mid = (lo + hi) / 2 if hi else lo
        anchor = p.bid_avg_usd or mid
        # New sellers price slightly under the crowd; strong fits price at/above it.
        factor = 0.9 if new_seller else 1.0
        if score >= 85:
            factor += 0.08
        usd = anchor * factor
        if lo or hi:
            usd = _clamp(usd, lo, hi or usd)
        usd = max(usd, floor)
        why = (f"fixed: budget ${lo:.0f}-${hi:.0f}, avg bid ${p.bid_avg_usd:.0f}, x{factor:.2f}, "
               f"floor ${floor:.0f}")
        days = _period_days(usd)

    usd = round(usd, 0)
    amount = p.from_usd(usd)
    if p.currency != "USD":
        amount = round(amount, 0)
    return Price(amount=amount, period_days=days, currency=p.currency, amount_usd=usd,
                 explanation=why, milestone_percentage=milestone_percentage)
