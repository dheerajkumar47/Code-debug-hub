"""Lead finder: real businesses from Google Maps → call-pain evidence → AI score + personalised pitch.

    python -m leadfinder cli            (the dashboard is start.bat)

Data source: SerpApi (Google Maps data, free plan, no card — SERPAPI_KEY) or the official Google Places
API (New) (GOOGLE_MAPS_KEY, needs billing). Uses the AI keys the bot already has. Writes data/leads/<industry>-<city>.csv (opens in Excel / Google Sheets) and a .html report.
Nothing is invented: every lead, phone, review quote and email comes from Google Maps or the business's
own website.
"""
from __future__ import annotations

import csv
import html
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import httpx

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ",".join("places." + f for f in (
    "id", "displayName", "formattedAddress", "nationalPhoneNumber", "internationalPhoneNumber",
    "websiteUri", "googleMapsUri", "rating", "userRatingCount", "reviews", "regularOpeningHours",
    "businessStatus")) + ",nextPageToken"

# Phrases in reviews that show calls are being missed or are a pain point.
CALL_PAIN = [
    r"(no one|nobody|none) (picks?|picked|answers?|answered|responds?|responded)",
    r"(not|never|didn'?t|doesn'?t|don'?t|won'?t) (pick(ing)?|answer(ing)?|respond(ing)?|receiv(e|ing))\w* "
    r"(up )?(the )?(phone|call|calls)",
    r"(phone|call|calls|number) (is |was |are )?(always |never |not )?(busy|unreachable|not reachable|switched off"
    r"|not answered|unanswered|goes unanswered|not picked)",
    r"(couldn'?t|could not|can'?t|cannot|unable to|hard to|difficult to|impossible to) (reach|get through|contact"
    r"|call|connect)",
    r"(on hold|kept waiting on (the )?(phone|call)|call(ed)? (many|multiple|several|\d+) times)",
    r"((no response|no reply|no answer) (on|to|from) (the |my )?(phone|call|calls|number|whatsapp)"
    r"|never (called|call) back|didn'?t call back|no call ?back|(didn'?t|did not|never) return(ed)? (my )?calls?)",
    # Hinglish (common in Indian reviews): "phone nahi uthate", "call receive nahi karte"
    r"(phone|call|fone)\s+(koi\s+)?(nahi|nahin|nhi|na)\s+(uthat|uthay|uthaa|utha|lagt|lag|receive)",
    r"(phone|call)\s+(receive|pick)\s+(nahi|nahin|nhi)",
]
BOOKING_HINTS = ("calendly", "practo", "book now", "book an appointment", "book appointment", "online booking",
                 "schedule an appointment", "booking", "appointment form", "zocdoc", "fresha", "setmore")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NAME_RE = re.compile(r"\b(?:Dr\.?|Doctor|Founder|Owner|Director|Managing Director|Proprietor)[\s:,-]+"
                     r"([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})")


@dataclass
class Lead:
    name: str
    address: str
    phone: str
    website: str
    maps_url: str
    rating: float
    reviews_count: int
    pain_quotes: list[str] = field(default_factory=list)
    hours: str = ""
    has_online_booking: bool | None = None
    emails: list[str] = field(default_factory=list)
    decision_maker: str = ""
    score: int = 0
    why: str = ""
    pitch: str = ""


# ---------------------------------------------------------------- data collection
def search_places(key: str, query: str, want: int, client: httpx.Client) -> list[dict]:
    out, token = [], None
    while len(out) < want:
        body = {"textQuery": query, "pageSize": 20}
        if token:
            body["pageToken"] = token
        r = client.post(PLACES_URL, json=body,
                        headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS})
        if r.status_code != 200:
            raise RuntimeError(f"Google Maps said {r.status_code}: {r.text[:300]}")
        data = r.json()
        out += [p for p in data.get("places", []) if p.get("businessStatus", "OPERATIONAL") == "OPERATIONAL"]
        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(2)  # the next page needs a moment to become valid
    return out[:want]


SERPAPI_URL = "https://serpapi.com/search.json"


def _serp(client: httpx.Client, params: dict) -> dict:
    r = client.get(SERPAPI_URL, params=params)
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or data.get("error"):
        raise RuntimeError(f"SerpApi said {r.status_code}: {data.get('error') or r.text[:300]}")
    return data


def search_serpapi(key: str, query: str, want: int, client: httpx.Client, review_top: int = 12) -> list[dict]:
    """Same Google Maps data through SerpApi (free plan, no card). Returned in the Places-API shape.
    Uses 1 search per 20 businesses + 1 per business whose reviews are read (lowest-rated first)."""
    places = serp_list(key, query, want, client)
    serp_reviews(key, places, review_top, client)
    return places


def serp_list(key: str, query: str, want: int, client: httpx.Client) -> list[dict]:
    """Businesses for one query (1 search per 20 results, max ~120 per query), without reviews."""
    raw, start = [], 0
    while len(raw) < want:
        data = _serp(client, {"engine": "google_maps", "type": "search", "q": query, "hl": "en",
                              "start": start, "api_key": key})
        page = data.get("local_results") or []
        raw += page
        if len(page) < 20:
            break
        start += 20
    places = []
    for x in raw[:want]:
        hours = x.get("operating_hours") or {}
        places.append({
            "displayName": {"text": x.get("title", "")}, "formattedAddress": x.get("address", ""),
            "internationalPhoneNumber": x.get("phone", ""), "websiteUri": x.get("website", ""),
            "googleMapsUri": (f"https://www.google.com/maps/place/?q=place_id:{x['place_id']}"
                              if x.get("place_id") else ""),
            "rating": x.get("rating") or 0, "userRatingCount": x.get("reviews") or 0,
            "regularOpeningHours": {"weekdayDescriptions": [f"{d.title()}: {h}" for d, h in hours.items()]},
            "businessStatus": "CLOSED_PERMANENTLY" if "permanently closed" in str(x.get("open_state", "")).lower()
            else "OPERATIONAL",
            "_data_id": x.get("data_id", ""), "reviews": []})
    return places


def serp_reviews(key: str, places: list[dict], review_top: int, client: httpx.Client) -> None:
    """Read reviews (1 search each) for the busiest places only; lowest-rated first so complaints surface."""
    for p in sorted(places, key=lambda p: p["userRatingCount"], reverse=True)[:review_top]:
        if not p["_data_id"]:
            continue
        try:
            data = _serp(client, {"engine": "google_maps_reviews", "data_id": p["_data_id"], "hl": "en",
                                  "sort_by": "ratingLow", "api_key": key})
        except RuntimeError:
            continue
        p["reviews"] = [{"originalText": {"text": (rv.get("extracted_snippet") or {}).get("original")
                                          or rv.get("snippet") or ""}} for rv in data.get("reviews") or []]


def pain_quotes(place: dict) -> list[str]:
    quotes = []
    for rv in place.get("reviews", []) or []:
        text = ((rv.get("originalText") or rv.get("text") or {}).get("text") or "").strip()
        low = text.lower()
        for pat in CALL_PAIN:
            m = re.search(pat, low)
            if m:
                a, b = max(0, m.start() - 70), min(len(text), m.end() + 70)
                quotes.append(("…" if a else "") + text[a:b].replace("\n", " ").strip() + ("…" if b < len(text) else ""))
                break
    return quotes


def check_website(url: str, client: httpx.Client) -> tuple[bool | None, list[str], str]:
    """(has online booking?, public emails, decision-maker name) from the business's own site."""
    if not url:
        return None, [], ""
    pages, texts = [url], []
    base = url.rstrip("/")
    pages += [base + p for p in ("/contact", "/contact-us", "/about", "/about-us")]
    for i, u in enumerate(pages):
        try:
            r = client.get(u, timeout=10, follow_redirects=True)
            if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
                texts.append(r.text[:400_000])
        except httpx.HTTPError:
            if i == 0:
                return None, [], ""
    blob = "\n".join(texts)
    low = blob.lower()
    booking = any(h in low for h in BOOKING_HINTS)
    emails = sorted({e for e in EMAIL_RE.findall(blob)
                     if not e.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"))
                     and "example" not in e and "sentry" not in e and "wixpress" not in e})[:3]
    plain = re.sub(r"<[^>]+>", " ", blob)
    m = NAME_RE.search(plain)
    return booking, emails, (m.group(0).strip() if m else "")


def to_lead(p: dict) -> Lead:
    hours = "; ".join((p.get("regularOpeningHours") or {}).get("weekdayDescriptions", [])[:7])
    return Lead(name=(p.get("displayName") or {}).get("text", ""), address=p.get("formattedAddress", ""),
                phone=p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber") or "",
                website=p.get("websiteUri", ""), maps_url=p.get("googleMapsUri", ""),
                rating=float(p.get("rating") or 0), reviews_count=int(p.get("userRatingCount") or 0),
                pain_quotes=pain_quotes(p), hours=hours)


# National chains have central call centres: not a lead for a small AI-receptionist startup.
CHAINS = ("clove dental", "sabka dentist", "apollo white", "apollo dental", "32 pearls", "dentzz", "floss dental",
          "partha dental", "fms dental", "smile studio by", "aspen dental", "my dentist", "bupa dental")


def drop_unfit(leads: list[Lead]) -> list[Lead]:
    """Remove chains (by name or a phone shared by several branches) and places with no phone to call."""
    phones: dict[str, int] = {}
    for ld in leads:
        key = re.sub(r"\D", "", ld.phone)[-10:]
        if key:
            phones[key] = phones.get(key, 0) + 1
    out = []
    for ld in leads:
        key = re.sub(r"\D", "", ld.phone)[-10:]
        if not key or phones[key] > 1 or any(c in ld.name.lower() for c in CHAINS):
            continue
        out.append(ld)
    return out


# ---------------------------------------------------------------- scoring + pitch
def rule_score(ld: Lead) -> tuple[int, str]:
    s, why = 0, []
    if ld.pain_quotes:
        s += 45 + 10 * min(len(ld.pain_quotes) - 1, 2)
        why.append(f"{len(ld.pain_quotes)} review(s) complain about calls")
    if ld.reviews_count >= 300:
        s += 20; why.append(f"very busy ({ld.reviews_count} reviews)")
    elif ld.reviews_count >= 80:
        s += 12; why.append(f"busy ({ld.reviews_count} reviews)")
    if ld.has_online_booking is False:
        s += 15; why.append("no online booking, bookings happen by phone")
    elif ld.has_online_booking is None and not ld.website:
        s += 10; why.append("no website, phone is the only channel")
    if re.search(r"sunday: (?!closed)", ld.hours.lower()) or "24 hours" in ld.hours.lower():
        s += 5; why.append("open long hours / weekends")
    if ld.phone:
        s += 5
    if ld.decision_maker or ld.emails:
        s += 5; why.append("contact found")
    return min(s, 100), "; ".join(why) or "few signals"


SYSTEM = """You write short cold-outreach messages for CallMate AI, an AI voice receptionist that answers every
call 24/7, books appointments, answers common questions and forwards urgent calls to staff.
Structure: 1) one specific observation about THIS business from the facts (e.g. how many patients review
them, that booking happens by phone, a review about calls); 2) the problem it causes (calls missed while
staff are busy with patients or after hours); 3) what CallMate AI does, in one sentence; 4) ask for a free
10-minute demo.
Rules: use ONLY the facts given; quote at most one short review phrase, only if it is about calls; never
invent numbers, names or problems; never say CallMate books through their website; 60-90 words; warm,
plain English. Never use: "priority", "commitment", "seamless", "enhance", "streamline", "we understand".
No subject line, no emojis. Sign off as: Team CallMate AI."""


def ai_pitch(llm, ld: Lead, industry: str, city: str) -> str:
    facts = {"business": ld.name, "industry": industry, "city": city, "rating": ld.rating,
             "google_reviews": ld.reviews_count, "review_complaints_about_calls": ld.pain_quotes[:2],
             "online_booking_on_website": ld.has_online_booking, "contact_person": ld.decision_maker,
             "signals": ld.why}
    return llm.complete(SYSTEM, "Write the message for this business:\n" + json.dumps(facts, ensure_ascii=False),
                        max_tokens=300, temperature=0.5).strip()


def template_pitch(ld: Lead, industry: str) -> str:
    if ld.pain_quotes:
        hook = "A few of your Google reviews mention it can be hard to get through on the phone"
    elif ld.reviews_count >= 300:
        hook = (f"With {ld.reviews_count:,} Google reviews, your phone must ring all day, and while your team is "
                "with patients some of those calls go unanswered")
    else:
        hook = f"Busy {industry}s often miss calls while the team is with patients or after hours"
    if ld.has_online_booking is False:
        hook += ". Since appointments are booked by phone, each missed call can be a lost patient"
    else:
        hook += ", and each missed call can be a lost patient"
    hello = f"Hello {ld.decision_maker}," if ld.decision_maker else f"Hello {ld.name} team,"
    return (f"{hello}\n\n{hook}.\n\nCallMate AI is an AI receptionist that answers every call 24/7, books "
            "appointments, answers common questions and forwards urgent calls to your staff.\n\n"
            "Could we show you a free 10-minute demo this week?\n\nTeam CallMate AI")


# ---------------------------------------------------------------- output
def write_csv(path: Path, leads: list[Lead]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig so Excel shows ₹ and names right
        w = csv.writer(f)
        w.writerow(["Rank", "Score", "Business", "Phone", "Website", "Email", "Decision maker", "Rating",
                    "Reviews", "Why it's a fit", "Review evidence", "Online booking", "Address", "Google Maps",
                    "Outreach message", "Status"])
        for i, ld in enumerate(leads, 1):
            w.writerow([i, ld.score, ld.name, ld.phone, ld.website, ", ".join(ld.emails), ld.decision_maker,
                        ld.rating, ld.reviews_count, ld.why, " | ".join(ld.pain_quotes),
                        {True: "Yes", False: "No", None: "Unknown"}[ld.has_online_booking], ld.address,
                        ld.maps_url, ld.pitch, "New"])


def write_html(path: Path, leads: list[Lead], industry: str, city: str) -> None:
    e = html.escape
    cards = []
    for i, ld in enumerate(leads, 1):
        quotes = "".join(f"<blockquote>“{e(q)}”</blockquote>" for q in ld.pain_quotes[:2])
        contact = " · ".join(x for x in [e(ld.phone), e(", ".join(ld.emails)), e(ld.decision_maker)] if x)
        links = " · ".join(x for x in [
            f'<a href="{e(ld.website)}" target="_blank">Website</a>' if ld.website else "",
            f'<a href="{e(ld.maps_url)}" target="_blank">Google Maps</a>' if ld.maps_url else ""] if x)
        cards.append(f"""<article><div class="top"><span class="rank">#{i}</span><h2>{e(ld.name)}</h2>
<span class="score">{ld.score}</span></div>
<p class="meta">★ {ld.rating} · {ld.reviews_count} reviews · {e(ld.address)}</p>
<p class="meta">{contact}{' · ' + links if links else ''}</p>
<p class="why"><b>Why it's a fit:</b> {e(ld.why)}</p>{quotes}
<details><summary>Personalised outreach message</summary><pre>{e(ld.pitch)}</pre></details></article>""")
    path.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Leads · {e(industry)} · {e(city)}</title>
<style>:root{{--bg:#f6f7f9;--card:#fff;--ink:#14171c;--mut:#5b6472;--acc:#0b6bcb;--line:#e3e6ea}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f1115;--card:#171a20;--ink:#e8eaed;--mut:#9aa3ae;--acc:#5aa9ff;--line:#262a31}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:24px 16px}}h1{{margin:0 0 4px;font-size:24px}}
.sub{{color:var(--mut);margin:0 0 20px}}article{{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:16px 18px;margin:0 0 14px}}.top{{display:flex;align-items:center;gap:10px}}h2{{font-size:17px;margin:0;flex:1}}
.rank{{color:var(--mut);font-weight:600}}.score{{background:var(--acc);color:#fff;border-radius:999px;padding:2px 10px;
font-weight:700}}.meta{{color:var(--mut);margin:4px 0;font-size:14px;overflow-wrap:anywhere}}a{{color:var(--acc)}}
.why{{margin:10px 0 6px}}blockquote{{margin:6px 0;padding:6px 12px;border-left:3px solid var(--acc);color:var(--mut);
font-style:italic}}pre{{white-space:pre-wrap;font:inherit;background:var(--bg);padding:10px;border-radius:8px}}
summary{{cursor:pointer;color:var(--acc);margin-top:8px}}</style></head><body><div class="wrap">
<h1>Leads: {e(industry.title())} in {e(city.title())}</h1>
<p class="sub">{len(leads)} businesses from Google Maps, ranked by how much they need an AI receptionist.
Review quotes are real Google reviews; contacts are from each business's own website.</p>
{''.join(cards)}</div></body></html>""", encoding="utf-8")


# ---------------------------------------------------------------- main
def queries_for(industry: str, city: str, areas: list[str] | None = None) -> list[str]:
    return [f"{industry} in {city}"] + [f"{industry} in {a.strip()}, {city}" for a in (areas or []) if a.strip()]


def review_budget(n: int) -> int:
    return min(max(n + 2, 12), 40)


def estimate_searches(n: int, areas: list[str] | None = None, per_query: int = 40) -> int:
    """SerpApi searches one run will use (list pages + review reads)."""
    return len(queries_for("x", "y", areas)) * -(-per_query // 20) + review_budget(n)


def suggest_areas(llm, city: str, k: int = 8) -> list[str]:
    """Well-known neighbourhoods of a city, used only as extra search terms (a wrong one just finds nothing)."""
    raw = llm.complete("Reply with a JSON array of strings only.",
                       f"List {k} well-known commercial neighbourhoods/areas of {city}. Names only.",
                       max_tokens=200, temperature=0.2)
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        areas = json.loads(m.group(0)) if m else []
    except ValueError:
        return []
    return [str(a).strip() for a in areas if str(a).strip()][:k]


def _place_key(p: dict) -> str:
    return p.get("_data_id") or p.get("id") or p.get("googleMapsUri") or \
        ((p.get("displayName") or {}).get("text", "") + p.get("internationalPhoneNumber", ""))


def find_leads(key: str, industry: str, city: str, n: int = 10, llm=None, scan: int = 40,
               client: httpx.Client | None = None, log=print, source: str = "google",
               areas: list[str] | None = None) -> list[Lead]:
    own = client is None
    client = client or httpx.Client(timeout=20, headers={"User-Agent": "Mozilla/5.0 (LeadFinder)"})
    try:
        places, seen = [], set()
        for q in queries_for(industry, city, areas):
            log(f"Searching Google Maps: {q} …")
            try:
                got = serp_list(key, q, scan, client) if source == "serpapi" else search_places(key, q, scan, client)
            except RuntimeError:
                if not places:
                    raise
                log("  search failed for this area; continuing with what we have")
                continue
            new = [p for p in got if p.get("businessStatus", "OPERATIONAL") == "OPERATIONAL"
                   and _place_key(p) not in seen]
            seen.update(_place_key(p) for p in new)
            places += new
            log(f"  +{len(new)} new businesses (total {len(places)})")
        if source == "serpapi":
            log(f"Reading reviews of the {min(review_budget(n), len(places))} busiest …")
            serp_reviews(key, places, review_budget(n), client)
        log(f"Found {len(places)} open businesses. Checking reviews and websites …")
        leads = drop_unfit([to_lead(p) for p in places])
        if len(leads) < len(places):
            log(f"  Removed {len(places) - len(leads)} chains / duplicate numbers / listings without a phone")
        pain = sum(1 for x in leads if x.pain_quotes)
        log(f"  {pain} have reviews complaining about calls")
        # check websites for the most promising ones first (review pain + busy)
        leads.sort(key=lambda x: (len(x.pain_quotes), x.reviews_count), reverse=True)
        batch = leads[: min(max(n + 10, 20), 120)]

        def site(ld: Lead) -> None:
            ld.has_online_booking, ld.emails, ld.decision_maker = check_website(ld.website, client)

        with ThreadPoolExecutor(8) as pool:
            list(pool.map(site, batch))
        for ld in leads:
            ld.score, ld.why = rule_score(ld)
        leads.sort(key=lambda x: x.score, reverse=True)
        top = leads[:n]
        log(f"Writing personalised messages for the top {len(top)} …")

        def pitch(ld: Lead) -> None:
            try:
                ld.pitch = ai_pitch(llm, ld, industry, city) if llm is not None else ""
            except Exception as ex:  # AI busy → safe template, never block the run
                log(f"  AI unavailable for {ld.name} ({ex.__class__.__name__}); using template")
            ld.pitch = ld.pitch or template_pitch(ld, industry)

        with ThreadPoolExecutor(4) as pool:
            list(pool.map(pitch, top))
        log(f"Done: scanned {len(places)} · fit {len(leads)} · delivered top {len(top)}")
        return top
    finally:
        if own:
            client.close()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def run_cli(env_file: str = ".env") -> int:
    import os
    from dotenv import load_dotenv
    from .ai import build_llm

    load_dotenv(env_file)
    serp = os.environ.get("SERPAPI_KEY", "").strip()
    gkey = os.environ.get("GOOGLE_MAPS_KEY", "").strip()
    if not serp and not os.environ.get("LEADS_SOURCE", "") == "google":
        serp = input("SerpApi key (free, see README.md" + (", or press Enter to use Google" if gkey else "")
                     + "): ").strip()
        if serp:
            if len(serp) < 30:
                print("That doesn't look like a SerpApi key (it is a long code from serpapi.com/manage-api-key).")
                return 1
            with open(env_file, "a", encoding="utf-8") as f:
                f.write(f"\nSERPAPI_KEY={serp}\n")
            print("Saved in .env — you won't be asked again.\n")
    source, key = ("serpapi", serp) if serp else ("google", gkey)
    if not key:
        print("No key. Follow README.md Part A to get a free SerpApi key.")
        return 1
    industry = input("Industry (e.g. dental clinic, salon, hotel): ").strip() or "dental clinic"
    city = input("City (e.g. Ahmedabad): ").strip() or "Ahmedabad"
    n = int(input("How many leads? [10]: ").strip() or 10)
    llm = build_llm()
    try:
        leads = find_leads(key, industry, city, n, llm, source=source)
    except RuntimeError as ex:
        print(f"\n❌ {ex}\nSee README.md → 'If it fails'.")
        return 1
    out = Path("data/leads")
    out.mkdir(parents=True, exist_ok=True)
    base = out / f"{slug(industry)}-{slug(city)}"
    write_csv(base.with_suffix(".csv"), leads)
    write_html(base.with_suffix(".html"), leads, industry, city)
    print(f"\n✅ {len(leads)} leads ready:\n   {base.with_suffix('.html')}  (open in browser, screenshot for the client)"
          f"\n   {base.with_suffix('.csv')}   (Excel / upload to Google Sheets)")
    return 0
