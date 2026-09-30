"""Lead Finder dashboard: type industry + city, click Find, watch progress, get real leads.

    python -m leadfinder               (or double-click start.bat)

Runs only on this computer (http://127.0.0.1:8010). Keys come from .env in this folder.
"""
from __future__ import annotations

import os
import threading
import time
import webbrowser
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from . import finder as L

OUT = Path("data/leads")


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.running = False
        self.log: list[str] = []
        self.leads: list[dict] = []
        self.error = ""
        self.base = ""
        self.started = 0.0

    def add(self, line: str):
        with self.lock:
            self.log.append(line)


def create_app(env_file: str = ".env", llm=None, client=None) -> FastAPI:
    from dotenv import load_dotenv
    from .ai import build_llm

    load_dotenv(env_file)
    llm = llm if llm is not None else build_llm()
    job = Job()
    app = FastAPI(title="Lead Finder")

    def keys() -> tuple[str, str]:
        serp = os.environ.get("SERPAPI_KEY", "").strip()
        g = os.environ.get("GOOGLE_MAPS_KEY", "").strip()
        if serp and os.environ.get("LEADS_SOURCE", "") != "google":
            return "serpapi", serp
        return ("google", g) if g else ("", "")

    def run(industry: str, city: str, n: int, areas: list[str], deep: bool, use_ai: bool):
        source, key = keys()
        ai = llm if (use_ai and getattr(llm, "enabled", False)) else None
        try:
            if deep and not areas and ai is not None:
                job.add(f"Finding main areas of {city} …")
                try:
                    areas = L.suggest_areas(ai, city)
                    job.add("  Areas: " + ", ".join(areas))
                except Exception:
                    job.add("  Could not list areas; searching the whole city only")
            found = L.find_leads(key, industry, city, n, ai, source=source, areas=areas,
                                 log=job.add, client=client)
            OUT.mkdir(parents=True, exist_ok=True)
            base = OUT / f"{L.slug(industry)}-{L.slug(city)}"
            L.write_csv(base.with_suffix(".csv"), found)
            L.write_html(base.with_suffix(".html"), found, industry, city)
            with job.lock:
                job.leads = [asdict(x) for x in found]
                job.base = str(base)
        except Exception as ex:  # shown in the dashboard, never crashes the server
            with job.lock:
                job.error = str(ex)[:400]
        finally:
            with job.lock:
                job.running = False

    @app.get("/", response_class=HTMLResponse)
    def page():
        return HTMLResponse(PAGE)

    @app.get("/api/status")
    def status():
        source, key = keys()
        with job.lock:
            return {"running": job.running, "log": job.log[-200:], "leads": job.leads, "error": job.error,
                    "has_key": bool(key), "source": source, "ai": bool(getattr(llm, "enabled", False)),
                    "elapsed": int(time.time() - job.started) if job.started else 0,
                    "files": bool(job.base)}

    @app.post("/api/estimate")
    async def estimate(request: Request):
        b = await request.json()
        areas = [a for a in (b.get("areas") or "").split(",") if a.strip()]
        if b.get("deep") and not areas:
            areas = ["?"] * 8
        return {"searches": L.estimate_searches(int(b.get("n") or 10), areas)}

    @app.post("/api/key")
    async def save_key(request: Request):
        k = ((await request.json()).get("key") or "").strip()
        if len(k) < 30 or any(c.isspace() for c in k):
            raise HTTPException(400, "That doesn't look like a SerpApi key")
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"\nSERPAPI_KEY={k}\n")
        os.environ["SERPAPI_KEY"] = k
        return {"ok": True}

    @app.post("/api/run")
    async def start(request: Request):
        b = await request.json()
        industry, city = (b.get("industry") or "").strip(), (b.get("city") or "").strip()
        n = max(1, min(int(b.get("n") or 10), 200))
        areas = [a.strip() for a in (b.get("areas") or "").split(",") if a.strip()][:20]
        if not industry or not city:
            raise HTTPException(400, "Type an industry and a city")
        if not keys()[1]:
            raise HTTPException(400, "Add your SerpApi key first")
        with job.lock:
            if job.running:
                raise HTTPException(409, "A search is already running")
            job.reset()
            job.running, job.started = True, time.time()
        threading.Thread(target=run, args=(industry, city, n, areas, bool(b.get("deep")), bool(b.get("ai", True))),
                         daemon=True).start()
        return {"ok": True}

    @app.get("/download/{kind}")
    def download(kind: str):
        if kind not in ("csv", "html") or not job.base:
            raise HTTPException(404)
        p = Path(job.base).with_suffix("." + kind)
        return FileResponse(p, filename=p.name) if kind == "csv" else FileResponse(p, media_type="text/html")

    return app


def serve(env_file: str = ".env", port: int = 8010) -> int:
    import uvicorn
    url = f"http://127.0.0.1:{port}"
    print(f"\n  Lead Finder dashboard: {url}\n  (opening in your browser; keep this window open)\n")
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(create_app(env_file), host="127.0.0.1", port=port, access_log=False, log_level="warning")
    return 0


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Lead Finder</title>
<style>
:root{--bg:#f5f6f8;--card:#fff;--ink:#15181d;--mut:#5d6573;--line:#e2e5ea;--acc:#0b6bcb;--acc2:#e8f1fb;--ok:#177245;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a20;--ink:#e8eaed;--mut:#9aa3ae;--line:#272b33;--acc:#5aa9ff;--acc2:#16263a;--ok:#5cc98f;--bad:#ff8a80}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:24px 16px 60px}h1{font-size:22px;margin:0 0 2px}.sub{color:var(--mut);margin:0 0 18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:2fr 2fr 1fr;gap:12px}@media(max-width:640px){.grid{grid-template-columns:1fr}}
label{display:block;font-size:13px;color:var(--mut);margin-bottom:4px}
input,select,textarea{width:100%;font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:9px 10px}
.row{display:flex;flex-wrap:wrap;align-items:center;gap:14px;margin-top:12px}.row label{display:flex;gap:6px;align-items:center;margin:0;color:var(--ink);font-size:14px}
.row input[type=checkbox]{width:auto}
button{font:inherit;font-weight:600;border:0;border-radius:8px;padding:10px 18px;cursor:pointer;background:var(--acc);color:#fff}
button:disabled{opacity:.5;cursor:default}.ghost{background:var(--acc2);color:var(--acc)}
.est{color:var(--mut);font-size:13px}.log{margin-top:8px;font:13px/1.55 ui-monospace,Consolas,monospace;background:var(--bg);border-radius:8px;
padding:10px 12px;max-height:220px;overflow:auto;white-space:pre-wrap;color:var(--mut)}
.err{color:var(--bad);font-weight:600}.stats{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 14px}
.pill{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:14px}.pill b{color:var(--acc)}
.lead .top{display:flex;gap:10px;align-items:center}.lead h3{margin:0;font-size:16px;flex:1}.score{background:var(--acc);color:#fff;border-radius:999px;padding:1px 10px;font-weight:700;font-size:14px}
.meta{color:var(--mut);font-size:14px;margin:3px 0;overflow-wrap:anywhere}a{color:var(--acc)}
blockquote{margin:6px 0;padding:4px 10px;border-left:3px solid var(--acc);color:var(--mut);font-style:italic}
details summary{cursor:pointer;color:var(--acc);margin-top:6px}pre{white-space:pre-wrap;font:inherit;background:var(--bg);padding:10px;border-radius:8px}
.hidden{display:none}
</style></head><body><div class="wrap">
<h1>Lead Finder</h1><p class="sub">Real businesses from Google Maps · review evidence · website contacts · personalised message for each</p>

<div class="card hidden" id="keyBox"><b>Add your free SerpApi key once</b>
<p class="meta">Get it at serpapi.com/manage-api-key, then paste it here. It's saved on this computer only.</p>
<div class="row"><input id="key" placeholder="Paste SerpApi key" style="flex:1"><button id="saveKey">Save</button></div></div>

<div class="card">
<div class="grid">
<div><label for="industry">Industry</label><input id="industry" placeholder="dental clinic, salon, hotel…" value="dental clinic"></div>
<div><label for="city">City</label><input id="city" placeholder="Ahmedabad" value="Ahmedabad"></div>
<div><label for="n">How many leads</label><select id="n"><option>10</option><option selected>25</option><option>50</option><option>100</option><option>200</option></select></div>
</div>
<div class="row"><label><input type="checkbox" id="deep"> Search area by area (finds many more)</label>
<label><input type="checkbox" id="ai" checked> AI-written messages</label></div>
<div id="areasBox" class="hidden" style="margin-top:10px"><label for="areas">Areas (optional, comma separated; leave empty and AI picks the main areas)</label>
<input id="areas" placeholder="Navrangpura, Satellite, Vastrapur, Bopal, Maninagar"></div>
<div class="row"><button id="go">Find leads</button><span class="est" id="est"></span></div>
</div>

<div class="card hidden" id="progress"><b id="state">Working…</b><div class="log" id="log"></div></div>

<div id="results" class="hidden">
<div class="row" style="margin:0 0 6px"><h2 style="margin:0;font-size:18px;flex:1" id="rtitle">Results</h2>
<a href="/download/csv"><button class="ghost">Download CSV</button></a>
<a href="/download/html" target="_blank"><button class="ghost">Printable report (save as PDF)</button></a></div>
<div class="stats" id="stats"></div><div id="list"></div></div>
</div>
<script>
const $=s=>document.querySelector(s),esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function post(p,b){const r=await fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});
 const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.detail||r.statusText);return j}
function form(){return{industry:$("#industry").value,city:$("#city").value,n:+$("#n").value,deep:$("#deep").checked,
 areas:$("#deep").checked?$("#areas").value:"",ai:$("#ai").checked}}
async function estimate(){try{const e=await post("/api/estimate",form());$("#est").textContent=`Uses about ${e.searches} of your 250 free monthly searches`}catch(e){}}
["#n","#deep","#areas"].forEach(s=>$(s).addEventListener("input",()=>{$("#areasBox").classList.toggle("hidden",!$("#deep").checked);estimate()}));
$("#saveKey").onclick=async()=>{try{await post("/api/key",{key:$("#key").value});tick()}catch(e){alert(e.message)}};
$("#go").onclick=async()=>{try{await post("/api/run",form());$("#results").classList.add("hidden");tick()}catch(e){alert(e.message)}};
let timer=null;
function render(s){$("#keyBox").classList.toggle("hidden",s.has_key);$("#go").disabled=s.running||!s.has_key;
 if(s.running||s.log.length){$("#progress").classList.remove("hidden");$("#log").textContent=s.log.join("\n");$("#log").scrollTop=1e9}
 $("#state").innerHTML=s.running?`Working… ${s.elapsed}s`:s.error?`<span class="err">Stopped: ${esc(s.error)}</span>`:s.leads.length?"Done":"Ready";
 if(!s.running&&s.leads.length){const L=s.leads;$("#results").classList.remove("hidden");
  $("#rtitle").textContent=`${L.length} leads`;
  const pain=L.filter(x=>x.pain_quotes.length).length,mail=L.filter(x=>x.emails.length).length,dm=L.filter(x=>x.decision_maker).length;
  $("#stats").innerHTML=`<span class="pill">Leads <b>${L.length}</b></span><span class="pill">Call complaints in reviews <b>${pain}</b></span><span class="pill">Emails found <b>${mail}</b></span><span class="pill">Decision makers <b>${dm}</b></span>`;
  $("#list").innerHTML=L.map((x,i)=>`<div class="card lead"><div class="top"><span class="meta">#${i+1}</span><h3>${esc(x.name)}</h3><span class="score">${x.score}</span></div>
  <p class="meta">★ ${x.rating} · ${x.reviews_count} reviews · ${esc(x.address)}</p>
  <p class="meta">${[esc(x.phone),esc(x.emails.join(", ")),esc(x.decision_maker)].filter(Boolean).join(" · ")}
  ${x.website?` · <a href="${esc(x.website)}" target="_blank" rel="noopener">Website</a>`:""}${x.maps_url?` · <a href="${esc(x.maps_url)}" target="_blank" rel="noopener">Google Maps</a>`:""}</p>
  <p style="margin:6px 0"><b>Why it's a fit:</b> ${esc(x.why)}</p>${x.pain_quotes.slice(0,2).map(q=>`<blockquote>“${esc(q)}”</blockquote>`).join("")}
  <details><summary>Outreach message</summary><pre>${esc(x.pitch)}</pre></details></div>`).join("")}
 clearTimeout(timer);timer=setTimeout(tick,s.running?1000:5000)}
async function tick(){try{render(await (await fetch("/api/status")).json())}catch(e){timer=setTimeout(tick,3000)}}
tick();estimate();
</script></body></html>"""
