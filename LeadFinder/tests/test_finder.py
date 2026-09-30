import json

import httpx

from leadfinder import finder as L


def _place(i, reviews=(), count=50, site=""):
    return {"id": str(i), "displayName": {"text": f"Clinic {i}"}, "formattedAddress": "Ahmedabad",
            "internationalPhoneNumber": "+91 79 0000 000" + str(i), "websiteUri": site,
            "googleMapsUri": f"https://maps.google.com/?cid={i}", "rating": 4.2, "userRatingCount": count,
            "businessStatus": "OPERATIONAL",
            "reviews": [{"originalText": {"text": t}} for t in reviews]}


def test_find_leads_ranks_call_pain_first_and_uses_only_real_data():
    places = [
        _place(1, ["Great doctor."], count=40),
        _place(2, ["Good treatment but nobody picks up the phone, I called 5 times."], count=320,
               site="https://c2.example.in"),
        _place(3, ["Could not reach them on the phone for two days."], count=90),
    ]
    sent = []

    def handler(req: httpx.Request):
        if req.url.host == "places.googleapis.com":
            sent.append(json.loads(req.content))
            assert req.headers["X-Goog-Api-Key"] == "k" and "places.reviews" in req.headers["X-Goog-FieldMask"]
            return httpx.Response(200, json={"places": places})
        if req.url.path in ("", "/"):
            return httpx.Response(200, headers={"content-type": "text/html"},
                                  text="<p>Dr. Mehta Shah, contact info@c2clinic.in. Call us to fix a time.</p>")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    out = L.find_leads("k", "dental clinic", "Ahmedabad", n=2, llm=None, client=client, log=lambda *_: None)
    assert sent[0]["textQuery"] == "dental clinic in Ahmedabad"
    assert [x.name for x in out] == ["Clinic 2", "Clinic 3"]
    top = out[0]
    assert "nobody picks up the phone" in top.pain_quotes[0]
    assert top.emails == ["info@c2clinic.in"] and top.decision_maker.startswith("Dr. Mehta")
    assert top.has_online_booking is False and "no online booking" in top.why
    assert "Hello Dr. Mehta" in top.pitch and "CallMate AI" in top.pitch


def test_outputs(tmp_path):
    ld = L.Lead("A & B <Clinic>", "addr", "+91", "", "", 4.5, 10, ["can't reach them"], pitch="Hi")
    L.write_csv(tmp_path / "x.csv", [ld])
    L.write_html(tmp_path / "x.html", [ld], "dental clinic", "Pune")
    assert "Outreach message" in (tmp_path / "x.csv").read_text(encoding="utf-8-sig")
    page = (tmp_path / "x.html").read_text(encoding="utf-8")
    assert "A &amp; B &lt;Clinic&gt;" in page and "prefers-color-scheme:dark" in page


def test_hinglish_call_complaints_are_detected():
    p = _place(9, ["Doctor accha hai but phone nahi uthate, 3 baar try kiya", "Call receive nahi karte"])
    assert len(L.pain_quotes(p)) == 2
    assert L.pain_quotes(_place(8, ["Very good treatment, nice staff"])) == []


def test_serpapi_source_maps_to_same_pipeline():
    calls = []

    def handler(req: httpx.Request):
        q = dict(req.url.params)
        if req.url.host == "serpapi.com":
            calls.append(q["engine"])
            if q["engine"] == "google_maps":
                return httpx.Response(200, json={"local_results": [
                    {"title": "Smile Dental", "place_id": "P1", "data_id": "D1", "address": "Navrangpura",
                     "phone": "+91 99999 11111", "rating": 4.1, "reviews": 250,
                     "operating_hours": {"sunday": "10 AM–1 PM"}},
                    {"title": "Old Clinic", "place_id": "P2", "data_id": "D2", "reviews": 5,
                     "open_state": "Permanently closed"}]})
            assert q["sort_by"] == "ratingLow"
            return httpx.Response(200, json={"reviews": [
                {"snippet": "Phone nahi uthate, very hard to get appointment"}]})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    out = L.find_leads("s" * 40, "dental clinic", "Ahmedabad", n=5, client=client, log=lambda *_: None,
                       source="serpapi")
    assert [x.name for x in out] == ["Smile Dental"]
    ld = out[0]
    assert ld.pain_quotes and "place_id:P1" in ld.maps_url and ld.reviews_count == 250
    assert "open long hours / weekends" in ld.why
    assert calls.count("google_maps") == 1


def test_review_about_doctor_not_calls_is_not_call_pain():
    p = _place(7, ["Stay alert from such unethical doctors. His no response proves that he isn't guilty"])
    assert L.pain_quotes(p) == []
    assert L.pain_quotes(_place(6, ["No response on the phone for two days"]))


def test_chains_and_shared_call_centre_numbers_are_dropped():
    a = L.Lead("Clove Dental - Bodakdev", "", "+91 40 3824 5727", "", "", 4.8, 800)
    b = L.Lead("Some Branch", "", "+91 40 3824 5727", "", "", 4.8, 700)
    c = L.Lead("Aashu Dental", "", "+91 98251 58578", "", "", 4.9, 2364)
    d = L.Lead("No Phone Clinic", "", "", "", "", 5, 6000)
    assert [x.name for x in L.drop_unfit([a, b, c, d])] == ["Aashu Dental"]


def test_template_pitch_is_specific_and_clean():
    ld = L.Lead("Aashu Dental", "", "+91", "", "", 4.9, 2364, decision_maker="Dr. Manish Shah",
                has_online_booking=False)
    t = L.template_pitch(ld, "dental clinic")
    assert t.startswith("Hello Dr. Manish Shah,") and "2,364 Google reviews" in t and "booked by phone" in t
    assert not any(w in t.lower() for w in ("priority", "seamless", "enhance", "through your website"))


def test_dashboard_runs_area_search_dedupes_and_serves_downloads(tmp_path, monkeypatch):
    import time as _t
    from fastapi.testclient import TestClient
    from leadfinder import web as leads_web

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SERPAPI_KEY", "k" * 40)
    monkeypatch.delenv("LEADS_SOURCE", raising=False)
    queries = []

    def handler(req: httpx.Request):
        q = dict(req.url.params)
        if q.get("engine") == "google_maps":
            queries.append(q["q"])
            shared = {"title": "Smile Dental", "place_id": "P1", "data_id": "D1", "phone": "+91 99999 11111",
                      "rating": 4.5, "reviews": 400}
            extra = {"title": "Area Clinic " + q["q"][-12:], "place_id": "P" + q["q"], "data_id": "D" + q["q"],
                     "phone": "+91 98" + str(abs(hash(q["q"])))[:8], "rating": 4.2, "reviews": 120}
            return httpx.Response(200, json={"local_results": [shared, extra]})
        if q.get("engine") == "google_maps_reviews":
            return httpx.Response(200, json={"reviews": [{"snippet": "Nobody picks up the phone"}]})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    app = leads_web.create_app(str(tmp_path / ".env"), llm=False,
                               client=client)
    c = TestClient(app)
    assert c.get("/").status_code == 200 and "Lead Finder" in c.get("/").text
    assert c.post("/api/estimate", json={"n": 25, "deep": True, "areas": "A, B"}).json()["searches"] == 3 * 2 + 27
    assert c.post("/api/run", json={"industry": "", "city": "X"}).status_code == 400
    r = c.post("/api/run", json={"industry": "dental clinic", "city": "Ahmedabad", "n": 10, "deep": True,
                                 "areas": "Navrangpura, Satellite", "ai": False})
    assert r.json()["ok"]
    for _ in range(100):
        s = c.get("/api/status").json()
        if not s["running"]:
            break
        _t.sleep(0.05)
    assert not s["error"], s
    assert queries == ["dental clinic in Ahmedabad", "dental clinic in Navrangpura, Ahmedabad",
                       "dental clinic in Satellite, Ahmedabad"]
    names = [x["name"] for x in s["leads"]]
    assert names.count("Smile Dental") == 1 and len(names) == 4
    assert c.get("/download/csv").status_code == 200 and "Smile Dental" in c.get("/download/csv").text
    assert c.get("/download/html").status_code == 200
