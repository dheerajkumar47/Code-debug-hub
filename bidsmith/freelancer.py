"""Thin client for the official Freelancer.com REST API (OAuth token, no scraping).

Endpoints mirror the official SDK (github.com/freelancer/freelancer-sdk-python):
  GET  /projects/0.1/projects/active/   search active projects
  POST /projects/0.1/bids/              place a bid
  GET  /projects/0.1/bids/              list bids
  GET  /users/0.1/self/                 the authenticated user
"""
from __future__ import annotations

import logging
from typing import Any, Iterable

import httpx

from .models import Client, Project

log = logging.getLogger(__name__)


class FreelancerError(RuntimeError):
    pass


class FreelancerClient:
    def __init__(self, token: str, api_url: str = "https://www.freelancer.com/api",
                 site_url: str = "https://www.freelancer.com", timeout: float = 20.0,
                 transport: httpx.BaseTransport | None = None):
        if not token:
            raise FreelancerError("FREELANCER_OAUTH_TOKEN is not set")
        self.site_url = site_url.rstrip("/")
        self._http = httpx.Client(
            base_url=api_url.rstrip("/"),
            headers={"Freelancer-OAuth-V1": token, "User-Agent": "BidSmith/0.1 (personal)"},
            timeout=timeout,
            transport=transport,
        )
        self._self_id: int | None = None

    # ------------------------------------------------------------------
    def _request(self, method: str, path: str, **kw) -> Any:
        r = self._http.request(method, path, **kw)
        try:
            data = r.json()
        except ValueError:
            raise FreelancerError(f"{method} {path}: HTTP {r.status_code} (non-JSON)")
        if r.status_code >= 400 or data.get("status") == "error":
            raise FreelancerError(
                f"{method} {path}: HTTP {r.status_code} {data.get('error_code', '')} {data.get('message', '')}".strip())
        return data.get("result", data)

    def self_id(self) -> int:
        if self._self_id is None:
            self._self_id = int(self._request("GET", "/users/0.1/self/")["id"])
        return self._self_id

    def search_active(self, query: str = "", job_ids: Iterable[int] = (), project_types: Iterable[str] = (),
                      limit: int = 30, offset: int = 0) -> list[Project]:
        params: list[tuple[str, Any]] = [
            ("query", query), ("limit", limit), ("offset", offset),
            ("sort_field", "time_updated"), ("compact", "true"),
            ("full_description", "true"), ("job_details", "true"), ("upgrade_details", "true"),
            ("user_details", "true"), ("user_country_details", "true"),
            ("user_status", "true"), ("user_employer_reputation", "true"),
        ]
        params += [("jobs[]", j) for j in job_ids]
        params += [("project_types[]", t) for t in project_types]
        result = self._request("GET", "/projects/0.1/projects/active/", params=params)
        users = result.get("users") or {}
        return [parse_project(p, users, self.site_url) for p in result.get("projects", [])]

    def place_bid(self, project_id: int, amount: float, period_days: int, description: str,
                  milestone_percentage: int = 50) -> dict:
        body = {
            "project_id": int(project_id),
            "bidder_id": self.self_id(),
            "amount": float(amount),
            "period": int(period_days),
            "milestone_percentage": int(milestone_percentage),
            "description": description,
        }
        return self._request("POST", "/projects/0.1/bids/", json=body)

    def my_bids(self, project_ids: Iterable[int] = (), limit: int = 50) -> list[dict]:
        params: list[tuple[str, Any]] = [("bidders[]", self.self_id()), ("limit", limit)]
        params += [("projects[]", p) for p in project_ids]
        return self._request("GET", "/projects/0.1/bids/", params=params).get("bids", [])


# ----------------------------------------------------------------------
def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def parse_project(p: dict, users: dict, site_url: str = "https://www.freelancer.com") -> Project:
    """Convert a raw API project dict (+ users map) into a Project."""
    owner = users.get(str(p.get("owner_id"))) or users.get(p.get("owner_id")) or {}
    status = owner.get("status") or {}
    rep = ((owner.get("employer_reputation") or {}).get("entire_history") or {})
    country = ((owner.get("location") or {}).get("country") or {}).get("name", "")
    currency = p.get("currency") or {}
    budget = p.get("budget") or {}
    stats = p.get("bid_stats") or {}
    upgrades = p.get("upgrades") or {}
    jobs = p.get("jobs") or []
    seo = p.get("seo_url") or str(p.get("id"))
    return Project(
        id=int(p["id"]),
        title=p.get("title", ""),
        description=p.get("description") or p.get("preview_description") or "",
        url=f"{site_url}/projects/{seo}",
        type=p.get("type", "fixed"),
        currency=currency.get("code", "USD"),
        usd_rate=_f(currency.get("exchange_rate"), 1.0) or 1.0,
        budget_min=_f(budget.get("minimum")),
        budget_max=_f(budget.get("maximum"), _f(budget.get("minimum"))),
        bid_count=int(stats.get("bid_count") or 0),
        bid_avg=_f(stats.get("bid_avg")),
        skills=[j.get("name", "") for j in jobs if j.get("name")],
        skill_ids=[int(j["id"]) for j in jobs if j.get("id") is not None],
        time_submitted=int(p.get("time_submitted") or 0),
        nda=bool(upgrades.get("NDA") or upgrades.get("nda")),
        sealed=bool(upgrades.get("sealed")),
        featured=bool(upgrades.get("featured")),
        client=Client(
            user_id=p.get("owner_id"),
            country=country,
            payment_verified=bool(status.get("payment_verified")),
            rating=_f(rep.get("overall")),
            reviews=int(rep.get("reviews") or 0),
            completed_projects=int(rep.get("complete") or 0),
        ),
    )
