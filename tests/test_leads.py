import json

import httpx

from bidsmith import leads as L


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
