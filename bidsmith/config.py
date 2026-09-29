"""Settings (from environment / .env) and the owner profile (from YAML)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None or v == "":
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def clean_secret(v: str | None) -> str:
    """Remove what copy-paste often adds: spaces, quotes, 'Bearer ', control characters."""
    v = "".join(ch for ch in (v or "") if ch.isprintable() or ch.isspace()).strip().strip("\"'`").strip()
    if v.lower().startswith("bearer "):
        v = v[7:].strip()
    # A key never contains spaces: if other text came along with the paste, keep the longest piece.
    if any(ch.isspace() for ch in v):
        v = max(v.split(), key=len)
    return v.strip("\"'`[](){}<>:;,")


def mask(v: str) -> str:
    return f"{len(v)} chars ({v[:4]}…{v[-4:]})" if len(v) >= 12 else f"{len(v)} chars"


def _int(v: str | None, default: int) -> int:
    try:
        return int(v) if v not in (None, "") else default
    except ValueError:
        return default


@dataclass
class Settings:
    # Freelancer.com
    freelancer_token: str = ""
    freelancer_api_url: str = "https://www.freelancer.com/api"
    freelancer_site_url: str = "https://www.freelancer.com"

    # LLM
    llm_provider: str = "none"  # gemini | openai | anthropic | none
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""  # optional, OpenAI-compatible (Groq, OpenRouter, ...)
    llm_score_enabled: bool = False

    # WhatsApp Cloud API (Meta, official)
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_api_version: str = "v23.0"
    whatsapp_template_name: str = ""
    whatsapp_template_lang: str = "en"
    owner_whatsapp: str = ""  # digits only, international format e.g. 923001234567

    # Web dashboard
    dashboard_user: str = "owner"
    dashboard_password: str = ""
    public_base_url: str = ""

    # Pipeline
    notify_channels: list[str] = field(default_factory=lambda: ["web", "console"])
    poll_interval_seconds: int = 180
    score_threshold: int = 70
    auto_submit: bool = False
    auto_submit_min_score: int = 85
    max_bids_per_day: int = 5
    min_seconds_between_bids: int = 90
    milestone_percentage: int = 50

    db_path: str = "data/bidsmith.db"
    profile_path: str = "profile/owner_profile.yaml"

    @classmethod
    def load(cls, env_file: str | None = ".env") -> "Settings":
        if env_file and Path(env_file).exists():
            load_dotenv(env_file, override=False)
        e = os.environ.get
        channels = [c.strip() for c in e("NOTIFY_CHANNELS", "web,console").split(",") if c.strip()]
        return cls(
            freelancer_token=clean_secret(e("FREELANCER_OAUTH_TOKEN", "")),
            freelancer_api_url=e("FREELANCER_API_URL", cls.freelancer_api_url).rstrip("/"),
            freelancer_site_url=e("FREELANCER_SITE_URL", cls.freelancer_site_url).rstrip("/"),
            llm_provider=e("LLM_PROVIDER", "none").lower(),
            llm_api_key=clean_secret(e("LLM_API_KEY", "")),
            llm_model=e("LLM_MODEL", ""),
            llm_base_url=e("LLM_BASE_URL", ""),
            llm_score_enabled=_bool(e("LLM_SCORE_ENABLED"), False),
            whatsapp_token=clean_secret(e("WHATSAPP_TOKEN", "")),
            whatsapp_phone_number_id=e("WHATSAPP_PHONE_NUMBER_ID", ""),
            whatsapp_verify_token=e("WHATSAPP_VERIFY_TOKEN", ""),
            whatsapp_app_secret=e("WHATSAPP_APP_SECRET", ""),
            whatsapp_api_version=e("WHATSAPP_API_VERSION", cls.whatsapp_api_version),
            whatsapp_template_name=e("WHATSAPP_TEMPLATE_NAME", ""),
            whatsapp_template_lang=e("WHATSAPP_TEMPLATE_LANG", "en"),
            owner_whatsapp="".join(ch for ch in e("OWNER_WHATSAPP", "") if ch.isdigit()),
            dashboard_user=e("DASHBOARD_USER", "owner"),
            dashboard_password=e("DASHBOARD_PASSWORD", ""),
            public_base_url=e("PUBLIC_BASE_URL", "").rstrip("/"),
            notify_channels=channels,
            poll_interval_seconds=_int(e("POLL_INTERVAL_SECONDS"), 180),
            score_threshold=_int(e("SCORE_THRESHOLD"), 70),
            auto_submit=_bool(e("AUTO_SUBMIT"), False),
            auto_submit_min_score=_int(e("AUTO_SUBMIT_MIN_SCORE"), 85),
            max_bids_per_day=_int(e("MAX_BIDS_PER_DAY"), 5),
            min_seconds_between_bids=_int(e("MIN_SECONDS_BETWEEN_BIDS"), 90),
            milestone_percentage=_int(e("MILESTONE_PERCENTAGE"), 50),
            db_path=e("DB_PATH", cls.db_path),
            profile_path=e("PROFILE_PATH", cls.profile_path),
        )


@dataclass
class PortfolioItem:
    title: str
    summary: str
    stack: list[str] = field(default_factory=list)
    result: str = ""
    link: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join([self.title, self.summary, " ".join(self.stack), self.result, " ".join(self.tags)])


@dataclass
class Profile:
    name: str
    headline: str
    bio: str
    skills_primary: list[str]
    skills_secondary: list[str]
    hourly_floor_usd: float
    fixed_floor_usd: float
    target_hourly_usd: float
    reviews_count: int
    portfolio: list[PortfolioItem]
    facts: list[str]  # verified claims the writer may use
    search: dict[str, Any]
    style: dict[str, Any]
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def all_skills(self) -> list[str]:
        return self.skills_primary + self.skills_secondary

    @property
    def corpus(self) -> str:
        """Everything the proposal writer is allowed to claim (for grounding checks)."""
        parts = [self.name, self.headline, self.bio, " ".join(self.all_skills), " ".join(self.facts)]
        parts += [p.text + " " + p.link for p in self.portfolio]
        return "\n".join(parts)

    @classmethod
    def load(cls, path: str) -> "Profile":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        owner = data.get("owner", {})
        rates = data.get("rates", {})
        skills = data.get("skills", {})
        return cls(
            name=owner.get("name", ""),
            headline=owner.get("headline", ""),
            bio=owner.get("bio", ""),
            skills_primary=list(skills.get("primary", [])),
            skills_secondary=list(skills.get("secondary", [])),
            hourly_floor_usd=float(rates.get("hourly_floor_usd", 15)),
            fixed_floor_usd=float(rates.get("fixed_floor_usd", 30)),
            target_hourly_usd=float(rates.get("target_hourly_usd", 20)),
            reviews_count=int(owner.get("reviews_count", 0)),
            portfolio=[PortfolioItem(**p) for p in data.get("portfolio", [])],
            facts=list(data.get("facts", [])),
            search=dict(data.get("search", {})),
            style=dict(data.get("style", {})),
            raw=data,
        )
