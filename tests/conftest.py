import json
import time
from pathlib import Path

import pytest

from bidsmith.app import BidSmith
from bidsmith.config import Profile, Settings
from bidsmith.freelancer import parse_project
from bidsmith.store import Store

ROOT = Path(__file__).resolve().parent.parent
NOW = 1_790_000_000.0


@pytest.fixture
def profile():
    return Profile.load(str(ROOT / "profile" / "owner_profile.yaml"))


@pytest.fixture
def projects():
    data = json.loads((ROOT / "tests" / "fixtures" / "projects.json").read_text())["result"]
    out = {}
    for p in data["projects"]:
        p = dict(p, time_submitted=int(NOW - 600))
        out[p["id"]] = parse_project(p, data["users"])
    return out


class FakeClient:
    def __init__(self, projects=()):
        self.projects = list(projects)
        self.bids = []

    def search_active(self, *a, **k):
        return self.projects

    def place_bid(self, project_id, amount, period_days, description, milestone_percentage=50):
        self.bids.append(dict(project_id=project_id, amount=amount, period=period_days, description=description))
        return {"id": 555000 + len(self.bids)}

    def self_id(self):
        return 42


class FakeLLM:
    enabled = True

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, system, user, max_tokens=700, temperature=0.6):
        self.calls.append(user)
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


class Recorder:
    name = "rec"

    def __init__(self):
        self.cards, self.texts = [], []

    def send_card(self, card):
        self.cards.append(card)

    def send_text(self, text):
        self.texts.append(text)


@pytest.fixture
def make_bot(profile):
    def _make(projects=(), llm=None, **settings):
        s = Settings(db_path=":memory:", min_seconds_between_bids=0, **settings)
        rec = Recorder()
        bot = BidSmith(s, profile, Store(":memory:"), FakeClient(projects), llm, [rec])
        bot.rec = rec
        return bot
    return _make
