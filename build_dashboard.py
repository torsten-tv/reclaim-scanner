# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Baut aus results.json ein eigenstaendiges dashboard.html (Methode-A-Reclaim-Scanner)."""
import json, datetime, pathlib

BASE = pathlib.Path(__file__).resolve().parent
data = json.load(open(BASE / "results.json"))
rows = data["rows"]
stamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
from collections import Counter
cnt = Counter(r["status"] for r in rows)

# Top-ENTRY fuer die Konsole
tops = [r for r in rows if r["status"] == "ENTRY"][:12]
print("TOP ENTRY:")
for r in tops:
    print(f"  {r['ticker']:10} {r['region']}  Kurs {r['price']:>9}  Entry {r['entry']:>9}  "
          f"Stop {r['stop']:>9}  Ziel {r['target']:>9}  Abst {r['dist']:>5}%  RR {r['rr']}")

html = """<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reclaim-Scanner — Methode A</title>
<style>
  :root{--bg:#0f1115;--card:#171a21;--bd:#262b36;--tx:#e6e8ec;--mut:#8a90a0;
        --green:#3fb950;--yellow:#d9a441;--blue:#4d8fdd;--gray:#5a6072;--red:#e0533d;}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);
    font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;font-size:14px}
  header{padding:18px 20px;border-bottom:1px solid var(--bd)}
  h1{margin:0 0 4px;font-size:19px}.sub{color:var(--mut);font-size:13px}
  .bar{display:flex;gap:8px;flex-wrap:wrap;padding:14px 20px;align-items:center}
  .pill{padding:6px 12px;border:1px solid var(--bd);border-radius:20px;background:var(--card);
        color:var(--tx);cursor:pointer;font-size:13px;user-select:none}
  .pill.on{border-color:var(--blue);background:#1d2c44}
  .pill b{font-variant-numeric:tabular-nums}
  input{padding:7px 12px;border:1px solid var(--bd);border-radius:8px;background:var(--card);
        color:var(--tx);font-size:13px;min-width:140px}
  .wrap{padding:0 20px 40px}
  table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
  th,td{padding:9px 10px;text-align:right;border-bottom:1px solid var(--bd);white-space:nowrap}
  th:first-child,td:first-child,th:nth-child(2),td:nth-child(2),th:nth-child(3),td:nth-child(3){text-align:left}
  th{color:var(--mut);font-weight:600;cursor:pointer;position:sticky;top:0;background:var(--bg)}
  tr:hover td{background:#12151c}
  .st{padding:3px 9px;border-radius:6px;font-size:12px;font-weight:700;color:#0b0d10}
  .ENTRY{background:var(--green)}.BEOBACHTUNG{background:var(--yellow)}
  .GEFUELLT{background:var(--blue);color:#fff}.DOWNTREND{background:var(--gray);color:#fff}
  .UNTERWASSER{background:#e08a3d;color:#0b0d10}.ausgestoppt{background:#5a2a22;color:#e0a08a}
  .vorbei{background:#33384400;color:var(--mut)}
  .reg{color:var(--mut);font-size:12px}
  a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
</style></head><body>
<header><h1>Reclaim-Scanner — Methode A</h1>
<div class="sub">Stand __STAMP__ · __NSCAN__ Ticker gescannt · __NLIQ__ liquide analysiert ·
Long-Reversal: Daily-Schluss über 50%-Mitte → Pullback-Entry → Stop = Tief 1 → Ziel = altes Hoch</div></header>
<div class="bar" id="filters"></div>
<div class="bar" style="padding-top:0">
  <input id="q" placeholder="Ticker suchen…" oninput="render()">
  <span class="pill" data-reg="ALL" onclick="setReg(this)">Alle Regionen</span>
  <span class="pill" data-reg="US" onclick="setReg(this)">US</span>
  <span class="pill" data-reg="EU" onclick="setReg(this)">EU</span>
</div>
<div class="wrap"><table id="t"><thead><tr>
  <th onclick="sortBy('ticker')">Ticker</th><th>Region</th><th onclick="sortBy('status')">Status</th>
  <th onclick="sortBy('price')">Kurs</th><th onclick="sortBy('entry')">Entry</th>
  <th onclick="sortBy('stop')">Stop (Tief 1)</th><th onclick="sortBy('target')">Ziel (Hoch)</th>
  <th onclick="sortBy('reclaim')">50%-Linie</th><th onclick="sortBy('drop')">Drop %</th>
  <th onclick="sortBy('dist')">Abstand Entry %</th><th onclick="sortBy('rr')">RR</th>
</tr></thead><tbody id="tb"></tbody></table></div>
<script>
const ROWS=__DATA__;
const order={ENTRY:0,BEOBACHTUNG:1,GEFUELLT:2,UNTERWASSER:3,DOWNTREND:4,ausgestoppt:5,vorbei:6};
let flt="ENTRY", reg="ALL", sortk="dist", asc=true;
const counts={};ROWS.forEach(r=>counts[r.status]=(counts[r.status]||0)+1);
const labels={ENTRY:"🟢 Entry",BEOBACHTUNG:"🟡 Beobachtung",GEFUELLT:"🔵 Gefüllt",UNTERWASSER:"🟠 Unterwasser",DOWNTREND:"⚪ Downtrend",ausgestoppt:"⛔ Ausgestoppt",vorbei:"Vorbei",ALL:"Alle"};
const fb=document.getElementById("filters");
["ENTRY","BEOBACHTUNG","GEFUELLT","UNTERWASSER","DOWNTREND","ausgestoppt","vorbei","ALL"].forEach(k=>{
  const n=k==="ALL"?ROWS.length:(counts[k]||0);
  const p=document.createElement("span");p.className="pill"+(k===flt?" on":"");
  p.innerHTML=labels[k]+" <b>"+n+"</b>";p.onclick=()=>{flt=k;[...fb.children].forEach(c=>c.classList.remove("on"));p.classList.add("on");render()};
  fb.appendChild(p);});
function setReg(el){reg=el.dataset.reg;document.querySelectorAll("[data-reg]").forEach(e=>e.classList.remove("on"));el.classList.add("on");render();}
function sortBy(k){asc=(sortk===k)?!asc:true;sortk=k;render();}
function render(){
  const q=document.getElementById("q").value.toUpperCase();
  let r=ROWS.filter(x=>(flt==="ALL"||x.status===flt)&&(reg==="ALL"||x.region===reg)&&x.ticker.toUpperCase().includes(q));
  r.sort((a,b)=>{let v=(typeof a[sortk]==="string")?a[sortk].localeCompare(b[sortk]):a[sortk]-b[sortk];return asc?v:-v;});
  document.getElementById("tb").innerHTML=r.map(x=>`<tr>
    <td><a href="https://www.tradingview.com/chart/?symbol=${x.ticker}" target="_blank">${x.ticker}</a></td>
    <td class="reg">${x.region}</td><td><span class="st ${x.status}">${x.status}</span></td>
    <td>${x.price}</td><td>${x.entry}</td><td>${x.stop}</td><td>${x.target}</td>
    <td>${x.reclaim}</td><td>${x.drop}</td><td>${x.dist}</td><td>${x.rr}</td></tr>`).join("");
}
document.querySelector('[data-reg="ALL"]').classList.add("on");render();
</script></body></html>"""

html = (html.replace("__STAMP__", stamp).replace("__NSCAN__", str(data.get("n_scanned","?")))
        .replace("__NLIQ__", str(len(rows)))
        .replace("__DATA__", json.dumps(rows, ensure_ascii=False)))
(BASE / "dashboard.html").write_text(html, encoding="utf-8")
print("\nDashboard:", BASE / "dashboard.html")
