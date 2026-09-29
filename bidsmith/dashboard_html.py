"""The live dashboard page (single file, no build step). Data comes from /api/state every 3 seconds."""

PAGE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BidSmith · Live</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#f5f7fb;--panel:#ffffff;--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--acc:#2563eb;--acc2:#1d4ed8;
--ok:#059669;--warn:#d97706;--bad:#dc2626;--chip:#eef2ff;--chipk:#3730a3;--soft:#f1f5f9;--shadow:0 1px 2px rgba(15,23,42,.06),0 8px 24px rgba(15,23,42,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0b1120;--panel:#111827;--ink:#e5e7eb;--mut:#94a3b8;--line:#1f2937;
--acc:#3b82f6;--acc2:#60a5fa;--chip:#1e293b;--chipk:#c7d2fe;--soft:#0f172a;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.25)}}
*{box-sizing:border-box;min-width:0}html,body{margin:0;background:var(--bg);color:var(--ink);overflow-x:hidden}
body{font:15px/1.5 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;overflow-wrap:anywhere}
.wrap{max-width:880px;margin:0 auto;padding:20px 16px 60px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.brand{font-weight:700;font-size:20px;letter-spacing:-.02em}.brand span{color:var(--acc)}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.pill{display:inline-flex;align-items:center;gap:8px;background:var(--panel);border:1px solid var(--line);border-radius:999px;
padding:6px 12px;font-size:13px;color:var(--mut);box-shadow:var(--shadow)}
.pill b{color:var(--ink);font-weight:600}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 0 rgba(5,150,105,.6);animation:pulse 2s infinite}
.dot.off{background:var(--mut);animation:none}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(5,150,105,.55)}70%{box-shadow:0 0 0 8px rgba(5,150,105,0)}100%{box-shadow:0 0 0 0 rgba(5,150,105,0)}}
button{font:inherit;cursor:pointer;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink);
padding:8px 14px;font-weight:600;font-size:14px;transition:background .15s,transform .05s}
button:hover{background:var(--soft)}button:active{transform:translateY(1px)}button:disabled{opacity:.55;cursor:default}
.primary{background:var(--acc);border-color:var(--acc);color:#fff;padding:10px 22px}.primary:hover{background:var(--acc2)}
.ghost{border-color:transparent;background:transparent;color:var(--mut)}.ghost:hover{color:var(--ink);background:var(--soft)}
.notice{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--warn);border-radius:12px;padding:12px 14px;
margin-bottom:16px;font-size:14px;box-shadow:var(--shadow)}
.empty{background:var(--panel);border:1px dashed var(--line);border-radius:16px;padding:44px 20px;text-align:center;color:var(--mut)}
.empty .radar{width:44px;height:44px;margin:0 auto 14px;border-radius:50%;border:2px solid var(--acc);position:relative;opacity:.8}
.empty .radar:after{content:"";position:absolute;inset:-2px;border-radius:50%;border:2px solid var(--acc);animation:ping 1.8s infinite}
@keyframes ping{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.9);opacity:0}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;margin-bottom:14px;box-shadow:var(--shadow);
transition:opacity .35s,transform .35s}
.card.enter{animation:enter .45s ease-out}.card.leave{opacity:0;transform:scale(.98)}
@keyframes enter{from{opacity:0;transform:translateY(-8px);box-shadow:0 0 0 3px var(--acc)}to{opacity:1;transform:none}}
.top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.title{font-weight:600;font-size:16.5px;line-height:1.35;color:var(--ink);text-decoration:none}.title:hover{color:var(--acc)}
.new{background:var(--acc);color:#fff;font-size:11px;font-weight:700;border-radius:6px;padding:2px 7px;margin-right:6px;vertical-align:2px}
.ago{font-size:13px;color:var(--mut);white-space:nowrap}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0 10px;font-size:13.5px;color:var(--mut)}
.meta b{color:var(--ink);font-weight:600}.bids-ok{color:var(--ok)!important}.bids-mid{color:var(--warn)!important}.bids-hi{color:var(--bad)!important}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.chip{font-size:12px;padding:3px 9px;border-radius:999px;background:var(--soft);color:var(--mut);border:1px solid var(--line)}
.chip.m{background:var(--chip);color:var(--chipk);border-color:transparent;font-weight:600}
.fit{font-size:13px;color:var(--mut);margin-bottom:10px}.fit b{color:var(--ink);font-weight:600}
.pwrap{position:relative}
textarea{width:100%;min-height:300px;resize:vertical;border:1px solid var(--line);border-radius:12px;background:var(--soft);color:var(--ink);
font:14px/1.55 Inter,system-ui,sans-serif;padding:12px 14px;outline:none}
textarea:focus{border-color:var(--acc);box-shadow:0 0 0 3px rgba(37,99,235,.15)}
.polish{display:flex;justify-content:flex-end;font-size:12px;color:var(--acc);margin:0 2px 6px}
.note{font-size:12.5px;color:var(--warn);margin-top:6px}
.foot{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;margin-top:12px}
.price{display:flex;align-items:center;gap:8px;font-size:13.5px;color:var(--mut);flex-wrap:wrap}
.price input{width:92px;border:1px solid var(--line);border-radius:10px;background:var(--soft);color:var(--ink);padding:8px 10px;font:inherit;font-weight:600}
.actions{display:flex;gap:6px;align-items:center;margin-left:auto}
.applied{margin-top:28px}.applied h3{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin:0 0 8px}
.applied a{color:var(--ink);text-decoration:none}.applied li{padding:6px 0;border-bottom:1px solid var(--line);font-size:14px;list-style:none}
.applied ul{padding:0;margin:0}
.pill.link{cursor:pointer}.pill.link:hover{border-color:var(--acc);color:var(--ink)}
.tabs{display:flex;gap:6px;margin:-4px 0 16px;border-bottom:1px solid var(--line)}
.tab{background:none;border:0;border-bottom:2px solid transparent;border-radius:0;padding:8px 12px;color:var(--mut)}
.tab.on{color:var(--ink);border-bottom-color:var(--acc)}
.filters{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.filters button{padding:6px 12px;font-size:13px}.filters button.on{background:var(--acc);border-color:var(--acc);color:#fff}
.rows{background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden}
.row{display:flex;gap:12px;justify-content:space-between;align-items:flex-start;padding:12px 14px;border-bottom:1px solid var(--line)}
.row:last-child{border-bottom:0}.row a{color:var(--ink);text-decoration:none;font-weight:600}.row a:hover{color:var(--acc)}
.row .sub{font-size:12.5px;color:var(--mut);margin-top:2px}
.verdict{font-size:12.5px;white-space:nowrap;padding:3px 9px;border-radius:999px;background:var(--soft);color:var(--mut);border:1px solid var(--line)}
.verdict.ok{background:rgba(5,150,105,.12);color:var(--ok);border-color:transparent;font-weight:600}
@media(max-width:600px){.row{flex-direction:column}.verdict{white-space:normal}}
.toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%) translateY(20px);background:var(--ink);color:var(--bg);
padding:10px 16px;border-radius:12px;font-size:14px;opacity:0;transition:.25s;max-width:calc(100% - 32px);z-index:9}
.toast.show{opacity:1;transform:translateX(-50%)}
</style></head><body><div class="wrap">
<header><div class="brand">Bid<span>Smith</span></div>
<div class="bar"><span class="pill"><span id="dot" class="dot"></span><span id="status">Connecting…</span></span>
<span class="pill link" id="pChecked" title="See every job checked today">Checked today <b id="checked">0</b></span>
<span class="pill link" id="pMatched" title="See today's matches">Matched today <b id="matched">0</b></span>
<span class="pill">Open now <b id="open">0</b></span>
<span class="pill">Applied <b id="applied">0</b></span>
<button id="pause" class="ghost" title="Pause or resume searching">Pause</button></div></header>
<div class="tabs"><button class="tab on" data-tab="live">Live</button><button class="tab" data-tab="checked">Checked today</button></div>
<div id="checkedView" style="display:none">
<div class="filters"><button data-f="all" class="on">All</button><button data-f="matched">Matched</button><button data-f="not_matched">Not matched</button>
<span id="ckSummary" style="align-self:center;color:var(--mut);font-size:13px;margin-left:6px"></span></div>
<div class="rows" id="ckRows"></div></div>
<div id="liveView">
<div id="notice"></div>
<div id="cards"></div>
<div id="empty" class="empty" style="display:none"><div class="radar"></div>
<div style="font-weight:600;color:var(--ink);margin-bottom:4px">Watching Freelancer for projects that match you</div>
<div>New matches appear here automatically, within seconds. Keep this page open.</div>
<div id="counts" style="margin-top:14px;font-size:13px"></div></div>
<div class="applied" id="appliedBox" style="display:none"><h3>Today's matches that are no longer open</h3><ul id="appliedList"></ul></div>
</div>
</div><div id="toast" class="toast"></div>
<script>
const $=s=>document.querySelector(s), esc=t=>String(t??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const cards=new Map(), dirty=new Set(); let first=true, autoBid=true, live=true, baseTitle=document.title, flashT=null;
function ago(s){if(s==null)return"";if(s<60)return"just now";if(s<3600)return Math.floor(s/60)+"m ago";return Math.floor(s/3600)+"h ago"}
function money(c){const f=n=>Number(n||0).toLocaleString(undefined,{maximumFractionDigits:0});
 const r=c.budget_max&&c.budget_max!=c.budget_min?f(c.budget_min)+"–"+f(c.budget_max):f(c.budget_min||c.budget_max);
 return r+" "+c.currency+(c.type=="hourly"?"/hr":"")}
function bidsCls(n,max){return n<max*0.3?"bids-ok":n<max*0.7?"bids-mid":"bids-hi"}
function toast(m){const t=$("#toast");t.textContent=m;t.classList.add("show");clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove("show"),3800)}
function beep(){try{const a=new (window.AudioContext||window.webkitAudioContext)();[880,1175].forEach((f,i)=>{const o=a.createOscillator(),g=a.createGain();
 o.frequency.value=f;o.connect(g);g.connect(a.destination);g.gain.setValueAtTime(.0001,a.currentTime+i*.16);
 g.gain.exponentialRampToValueAtTime(.18,a.currentTime+i*.16+.02);g.gain.exponentialRampToValueAtTime(.0001,a.currentTime+i*.16+.15);
 o.start(a.currentTime+i*.16);o.stop(a.currentTime+i*.16+.16)})}catch(e){}}
function flash(n){clearInterval(flashT);let on=0,k=0;flashT=setInterval(()=>{document.title=(on^=1)?`(${n}) New project!`:baseTitle;if(++k>12){clearInterval(flashT);document.title=baseTitle}},900)}
function notify(c){try{if("Notification"in window&&Notification.permission=="granted")new Notification("New project: "+c.title,{body:money(c)+" · "+c.bids+" bids"})}catch(e){}}
async function api(path,body){const r=await fetch(location.origin+path,{method:body?"POST":"GET",headers:{"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined});
 if(!r.ok)throw new Error("HTTP "+r.status);return r.json()}
function metaHTML(c,max){return `<span><b>${esc(money(c))}</b> · ${c.type=="hourly"?"Hourly":"Fixed"}</span>
 <span class="${bidsCls(c.bids,max)}"><b class="${bidsCls(c.bids,max)}">${c.bids}</b> bids</span>
 ${c.country?`<span>${esc(c.country)}</span>`:""}${c.verified?`<span>✓ Payment verified</span>`:""}
 ${c.reviews?`<span>★ ${Number(c.rating).toFixed(1)} (${c.reviews})</span>`:`<span>New client</span>`}`}
function badge(c){return c.drafting?"✨ AI is writing the proposal…":c.ai?"✨ AI-written":c.edited?"✏️ Your edit":
 '<span style="color:var(--warn)">Basic draft · AI busy · press Rewrite</span>'}
function build(c,max){const el=document.createElement("div");el.className="card";el.dataset.id=c.id;
 el.dataset.basic=(!c.ai&&!c.edited&&!c.drafting)?"1":"";
 el.innerHTML=`<div class="top"><div><a class="title" href="${esc(c.url)}" target="_blank" rel="noopener">${c.posted_s!=null&&c.posted_s<600?'<span class="new">NEW</span>':""}${esc(c.title)}</a></div>
 <div class="ago" data-k="ago">${ago(c.posted_s)}</div></div>
 <div class="meta" data-k="meta">${metaHTML(c,max)}</div>
 <div class="chips">${c.skills.map(s=>`<span class="chip ${s.match?"m":""}">${esc(s.name)}</span>`).join("")}</div>
 ${c.fit?`<div class="fit">Matches your work: <b>${esc(c.fit)}</b></div>`:""}
 <div class="pwrap"><div class="polish" data-k="polish">${badge(c)}</div><textarea data-k="text">${esc(c.text)}</textarea></div>
 <div class="note" data-k="notes">${c.notes.map(esc).join("<br>")}</div>
 <div class="foot"><div class="price">Price <input data-k="amount" type="number" min="1" step="1" value="${Math.round(c.amount)}"> ${esc(c.currency)}${c.currency!="USD"?` <span title="US dollars">≈ $${Math.round(c.amount_usd)}</span>`:""}
 &nbsp;Delivery <input data-k="days" type="number" min="1" step="1" value="${c.days}"> days</div>
 <div class="actions"><button class="ghost" data-a="skip">Skip</button><button class="ghost" data-a="rewrite" title="Write a new proposal">Rewrite</button>
 <button class="primary" data-a="apply">${autoBid?"Apply":"Copy &amp; open"}</button></div></div>`;
 el.querySelectorAll("textarea,input").forEach(i=>i.addEventListener("input",()=>dirty.add(c.id)));
 el.querySelector('[data-a=apply]').onclick=()=>apply(c.id,el);
 el.querySelector('[data-a=skip]').onclick=()=>act(c.id,"skip",el,true);
 el.querySelector('[data-a=rewrite]').onclick=()=>{dirty.delete(c.id);act(c.id,"rewrite",el,false)};
 return el}
function update(el,c,max){el.querySelector('[data-k=ago]').textContent=ago(c.posted_s);el.querySelector('[data-k=meta]').innerHTML=metaHTML(c,max);
 el.querySelector('[data-k=polish]').innerHTML=badge(c);el.dataset.basic=(!c.ai&&!c.edited&&!c.drafting)?"1":"";el.querySelector('[data-k=notes]').innerHTML=c.notes.map(esc).join("<br>");
 const ta=el.querySelector('[data-k=text]');if(!dirty.has(c.id)&&document.activeElement!==ta&&ta.value!==c.text)ta.value=c.text;
 const am=el.querySelector('[data-k=amount]');if(!dirty.has(c.id)&&document.activeElement!==am)am.value=Math.round(c.amount)}
function removeCard(id){const el=cards.get(id);if(!el)return;el.classList.add("leave");setTimeout(()=>el.remove(),350);cards.delete(id);dirty.delete(id)}
async function apply(id,el){const b=el.querySelector('[data-a=apply]');
 if(el.dataset.basic&&!dirty.has(id)&&!confirm("This is the basic draft (the AI was busy). A stronger AI proposal usually wins more.\n\nApply with the basic draft anyway?"))return;
 b.disabled=true;
 const body={text:el.querySelector('[data-k=text]').value,amount:+el.querySelector('[data-k=amount]').value,days:+el.querySelector('[data-k=days]').value};
 if(!autoBid){try{await navigator.clipboard.writeText(body.text)}catch(e){const ta=el.querySelector('[data-k=text]');ta.select();document.execCommand("copy")}
  window.open(el.querySelector(".title").href,"_blank");b.textContent="Mark applied";b.disabled=false;
  b.onclick=async()=>{await api(`/api/cards/${id}/applied`,{});removeCard(id);toast("Marked as applied")};toast("Proposal copied — paste it on Freelancer");return}
 b.textContent="Applying…";try{const r=await api(`/api/cards/${id}/apply`,body);toast(r.message);if(r.ok)removeCard(id);else{b.disabled=false;b.textContent="Apply"}}
 catch(e){toast("Could not apply: "+e.message);b.disabled=false;b.textContent="Apply"}}
async function act(id,what,el,remove){try{const r=await api(`/api/cards/${id}/${what}`,{});toast(r.message);if(remove)removeCard(id)}catch(e){toast(e.message)}}
function render(st){autoBid=st.auto_bid;live=st.live;$("#applied").textContent=st.applied_today;
 $("#checked").textContent=st.checked_today;$("#matched").textContent=st.matched_today;
 $("#open").textContent=st.cards.length;
 $("#counts").textContent=st.checked_today?`${st.checked_today} new projects checked today · ${st.matched_today} matched your skills`+
  (st.matched_today&&!st.cards.length?" · none open right now (see below why)":""):"";
 $("#dot").className="dot"+(live?"":" off");$("#pause").textContent=live?"Pause":"Resume";
 $("#status").textContent=!live?"Paused":st.checked_s==null?"Starting…":`Live · checked ${st.checked_s<5?"just now":st.checked_s+"s ago"}`;
 $("#notice").innerHTML=autoBid?"":`<div class="notice"><b>Copy &amp; paste mode.</b> Freelancer did not accept your token for bidding, so Apply copies the proposal and opens the project for you to paste. Everything else is automatic.</div>`;
 const ids=new Set(st.cards.map(c=>c.id)),fresh=[];
 [...cards.keys()].forEach(id=>{if(!ids.has(id))removeCard(id)});
 [...st.cards].reverse().forEach(c=>{if(cards.has(c.id))update(cards.get(c.id),c,st.max_bids);else{const el=build(c,st.max_bids);
  if(!first){el.classList.add("enter");fresh.push(c)}$("#cards").prepend(el);cards.set(c.id,el)}});
 if(fresh.length){beep();flash(fresh.length);fresh.forEach(notify)}
 $("#empty").style.display=cards.size?"none":"";
 $("#appliedBox").style.display=st.gone_today.length?"":"none";
 $("#appliedList").innerHTML=st.gone_today.map(a=>`<li style="display:flex;justify-content:space-between;gap:10px"><a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.title)}</a><span style="color:var(--mut);white-space:nowrap;font-size:13px">${esc(a.why)}</span></li>`).join("");first=false}
async function tick(){try{render(await api("/api/state"))}catch(e){$("#status").textContent="Reconnecting…";$("#dot").className="dot off"}}
$("#pause").onclick=async()=>{const r=await api("/api/pause",{});toast(r.message);tick()};
document.addEventListener("click",()=>{if("Notification"in window&&Notification.permission=="default")Notification.requestPermission()},{once:true});
let tab="live",filt="all",ckTimer=null;
function showTab(t,f){tab=t;if(f)filt=f;history.replaceState(null,"",t=="checked"?"#checked":location.pathname);document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("on",b.dataset.tab==t));
 $("#liveView").style.display=t=="live"?"":"none";$("#checkedView").style.display=t=="checked"?"":"none";
 document.querySelectorAll(".filters button").forEach(b=>b.classList.toggle("on",b.dataset.f==filt));
 clearInterval(ckTimer);if(t=="checked"){loadChecked();ckTimer=setInterval(loadChecked,10000)}window.scrollTo(0,0)}
async function loadChecked(){try{const d=await api("/api/checked");
 const rows=d.rows.filter(r=>filt=="all"||r.group==filt);
 $("#ckSummary").textContent=`${d.total} checked today · ${d.matched} matched`;
 $("#ckRows").innerHTML=rows.length?rows.map(r=>`<div class="row"><div><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>
  <div class="sub">${esc(money(r))} · ${r.bids} bids${r.posted_s!=null?" · posted "+ago(r.posted_s):""}${r.skills.length?" · "+esc(r.skills.join(", ")):""}</div></div>
  <span class="verdict ${r.group=="matched"?"ok":""}">${esc(r.why)}</span></div>`).join("")
  :`<div class="row" style="color:var(--mut)">Nothing here yet today.</div>`}catch(e){toast("Could not load the list: "+e.message)}}
document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
document.querySelectorAll(".filters button").forEach(b=>b.onclick=()=>showTab("checked",b.dataset.f));
$("#pChecked").onclick=()=>showTab("checked","all");$("#pMatched").onclick=()=>showTab("checked","matched");
tick();setInterval(tick,3000);if(location.hash=="#checked")showTab("checked","all");
</script></body></html>"""
