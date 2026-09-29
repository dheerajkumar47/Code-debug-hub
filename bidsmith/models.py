"""Plain data types shared across the pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Client:
    user_id: Optional[int] = None
    country: str = ""
    payment_verified: bool = False
    rating: float = 0.0  # 0-5, employer reputation
    reviews: int = 0
    completed_projects: int = 0


@dataclass
class Project:
    id: int
    title: str
    description: str
    url: str
    type: str = "fixed"  # "fixed" | "hourly"
    currency: str = "USD"
    usd_rate: float = 1.0  # 1 unit of `currency` in USD
    budget_min: float = 0.0  # in project currency
    budget_max: float = 0.0
    bid_count: int = 0
    bid_avg: float = 0.0  # in project currency
    skills: list[str] = field(default_factory=list)
    skill_ids: list[int] = field(default_factory=list)
    time_submitted: int = 0  # unix seconds
    nda: bool = False
    sealed: bool = False
    featured: bool = False
    client: Client = field(default_factory=Client)

    # --- helpers -----------------------------------------------------
    def to_usd(self, amount: float) -> float:
        return round(amount * (self.usd_rate or 1.0), 2)

    def from_usd(self, usd: float) -> float:
        return round(usd / (self.usd_rate or 1.0), 2)

    @property
    def budget_min_usd(self) -> float:
        return self.to_usd(self.budget_min)

    @property
    def budget_max_usd(self) -> float:
        return self.to_usd(self.budget_max or self.budget_min)

    @property
    def bid_avg_usd(self) -> float:
        return self.to_usd(self.bid_avg)

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.description}\n{' '.join(self.skills)}"


@dataclass
class ScoreResult:
    score: int
    reasons: list[str]
    red_flags: list[str] = field(default_factory=list)


@dataclass
class Price:
    amount: float  # in project currency
    period_days: int
    currency: str
    amount_usd: float
    explanation: str
    milestone_percentage: int = 50


@dataclass
class QualityReport:
    passed: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Draft:
    project_id: int
    text: str
    price: Price
    quality: QualityReport
    portfolio_used: list[str] = field(default_factory=list)
    ai: bool = False  # True when the AI wrote it (False = ready-made draft)
