import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "events.json"
OUTPUT_FILE = Path(__file__).parent / "dashboard.html"
CALENDAR_MONTHS = 3

TEMPLATE = r"""<title>Chine à Paris</title>
<style>
:root{
  --paper:#eef1e8; --surface:#ffffff; --surface-2:#e4e8dc;
  --ink:#1f2a22; --ink-muted:#5b6b5c;
  --accent:#2f6f5c; --accent-ink:#ffffff;
  --stamp:#b6502c; --stamp-ink:#fff5ee;
  --border:#d3d9c8;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#151913; --surface:#1d231a; --surface-2:#262d20;
    --ink:#e9ede2; --ink-muted:#9aa693;
    --accent:#4fae90; --accent-ink:#08120d;
    --stamp:#e08256; --stamp-ink:#2a1710;
    --border:#313b29;
  }
}
:root[data-theme="dark"]{
  --paper:#151913; --surface:#1d231a; --surface-2:#262d20;
  --ink:#e9ede2; --ink-muted:#9aa693;
  --accent:#4fae90; --accent-ink:#08120d;
  --stamp:#e08256; --stamp-ink:#2a1710;
  --border:#313b29;
}
*{box-sizing:border-box}
body{
  background:var(--paper); color:var(--ink);
  font-family:'Archivo',system-ui,sans-serif;
  padding-inline:16px;
}
.wrap{max-width:640px; margin:0 auto; padding-block:20px 48px; display:flex; flex-direction:column; gap:16px;}
h1,h2{font-family:'Fraunces',Georgia,serif; text-wrap:balance; margin:0;}
h1{font-size:30px; font-weight:600; letter-spacing:-0.01em;}
.sub{color:var(--ink-muted); font-size:14px; margin-top:4px;}
.count{
  font-family:'IBM Plex Mono',monospace; font-size:12px; color:var(--ink-muted);
  font-variant-numeric:tabular-nums;
}
header.top{display:flex; flex-direction:column; gap:2px;}

.tabs{display:flex; gap:8px;}
.tab{
  font-family:'Archivo',sans-serif; font-weight:600; font-size:13px;
  padding:8px 16px; border-radius:999px; border:1px solid var(--border);
  background:var(--surface); color:var(--ink); cursor:pointer;
}
.tab[aria-selected="true"]{background:var(--accent); color:var(--accent-ink); border-color:var(--accent);}

.search{
  width:100%; padding:10px 14px; border-radius:10px; border:1px solid var(--border);
  background:var(--surface); color:var(--ink); font-family:'Archivo',sans-serif; font-size:14px;
}
.search::placeholder{color:var(--ink-muted);}

.chips{display:flex; gap:6px; overflow-x:auto; padding-bottom:2px; -webkit-overflow-scrolling:touch;}
.chip{
  flex:none; font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:500;
  padding:6px 11px; border-radius:8px; border:1px solid var(--border);
  background:var(--surface); color:var(--ink-muted); cursor:pointer; white-space:nowrap;
}
.chip[aria-pressed="true"]{background:var(--stamp); color:var(--stamp-ink); border-color:var(--stamp);}

section.view{display:flex; flex-direction:column; gap:20px;}
[hidden]{display:none!important;}

.day-group{display:flex; flex-direction:column; gap:8px;}
.day-heading{
  font-family:'Fraunces',Georgia,serif; font-size:16px; font-weight:600;
  position:sticky; top:env(safe-area-inset-top,0px); background:var(--paper);
  padding-block:4px; text-transform:capitalize;
}
.card{
  background:var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:14px; display:flex; flex-direction:column; gap:6px;
}
.card-title{font-weight:600; font-size:15px; line-height:1.3;}
.badges{display:flex; gap:6px; flex-wrap:wrap;}
.badge{
  font-family:'IBM Plex Mono',monospace; font-size:11px; padding:3px 8px; border-radius:6px;
  background:var(--surface-2); color:var(--ink-muted);
}
.badge.arr{color:var(--accent); background:color-mix(in srgb, var(--accent) 14%, var(--surface));}
.loc{font-size:13px; color:var(--ink-muted);}
.card a.link{
  align-self:flex-start; font-size:13px; font-weight:600; color:var(--accent);
  text-decoration:none; margin-top:2px;
}
.card a.link:hover{text-decoration:underline;}
.empty{color:var(--ink-muted); font-size:14px; padding-block:24px; text-align:center;}

.cal-month{display:flex; flex-direction:column; gap:8px;}
.cal-grid{display:grid; grid-template-columns:repeat(7,1fr); gap:4px;}
.cal-dow{
  font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--ink-muted);
  text-align:center; text-transform:uppercase; letter-spacing:0.04em;
}
.cal-cell{
  aspect-ratio:1; border-radius:8px; border:1px solid var(--border); background:var(--surface);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px;
  font-family:'IBM Plex Mono',monospace; font-size:13px; cursor:default;
}
.cal-cell.pad{visibility:hidden;}
.cal-cell.has-events{cursor:pointer; border-color:var(--accent);}
.cal-cell .dot{width:5px; height:5px; border-radius:50%; background:var(--stamp);}
.cal-cell .n{font-size:9px; color:var(--ink-muted); font-variant-numeric:tabular-nums;}
</style>

<div class="wrap">
  <header class="top">
    <h1>Chine à Paris</h1>
    <div class="sub">Vide-greniers, brocantes &amp; ventes de charité — Paris intra-muros</div>
    <div class="count" id="count"></div>
  </header>

  <div class="tabs" role="tablist">
    <button class="tab" id="tab-list" aria-selected="true" role="tab">Liste</button>
    <button class="tab" id="tab-cal" aria-selected="false" role="tab">Calendrier</button>
  </div>

  <input class="search" id="search" type="search" placeholder="Chercher un lieu, un quartier…" autocomplete="off">
  <div class="chips" id="chips"></div>

  <section class="view" id="view-list"></section>
  <section class="view" id="view-cal" hidden></section>
</div>

<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap">
<script>
const EVENTS = __EVENTS_JSON__;
const CAL_MONTHS = __CAL_MONTHS__;

const DOW = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];
const MONTH_NAMES = ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'];
const DAY_NAMES = ['dimanche','lundi','mardi','mercredi','jeudi','vendredi','samedi'];

function parseFr(d){
  const [day, month, year] = d.split('/').map(Number);
  return new Date(year, month - 1, day);
}

function fmtDayHeading(date){
  return `${DAY_NAMES[date.getDay()]} ${date.getDate()} ${MONTH_NAMES[date.getMonth()]}`;
}

const state = { view: 'list', search: '', arrs: new Set() };

function sourceLabel(s){ return s === 'vente-solidaire' ? 'Vente solidaire' : 'Vide-grenier / brocante'; }

function matches(e){
  if (state.arrs.size && !(e.arrondissement && state.arrs.has(e.arrondissement))) return false;
  if (state.search){
    const hay = `${e.name} ${e.location_name||''}`.toLowerCase();
    if (!hay.includes(state.search)) return false;
  }
  return true;
}

function renderChips(){
  const present = new Set();
  Object.values(EVENTS).forEach(e => { if (e.arrondissement) present.add(e.arrondissement); });
  const sorted = [...present].sort((a,b)=>a-b);
  const el = document.getElementById('chips');
  el.innerHTML = '';
  sorted.forEach(arr => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.textContent = arr + 'e';
    chip.setAttribute('aria-pressed', state.arrs.has(arr));
    chip.onclick = () => {
      if (state.arrs.has(arr)) state.arrs.delete(arr); else state.arrs.add(arr);
      renderAll();
    };
    el.appendChild(chip);
  });
}

function renderList(){
  const el = document.getElementById('view-list');
  const filtered = Object.values(EVENTS).filter(matches);
  filtered.sort((a,b) => parseFr(a.start_date) - parseFr(b.start_date));

  if (!filtered.length){
    el.innerHTML = '<div class="empty">Aucun événement pour ce filtre.</div>';
    return;
  }

  const groups = new Map();
  filtered.forEach(e => {
    const key = e.start_date;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(e);
  });

  el.innerHTML = '';
  [...groups.entries()].forEach(([dateStr, events]) => {
    const group = document.createElement('div');
    group.className = 'day-group';
    const heading = document.createElement('div');
    heading.className = 'day-heading';
    heading.textContent = fmtDayHeading(parseFr(dateStr));
    group.appendChild(heading);
    events.forEach(e => group.appendChild(renderCard(e)));
    el.appendChild(group);
  });
}

function renderCard(e){
  const card = document.createElement('div');
  card.className = 'card';
  const badges = [
    e.arrondissement ? `<span class="badge arr">Paris ${e.arrondissement}e</span>` : `<span class="badge">Paris</span>`,
    `<span class="badge">${sourceLabel(e.source)}</span>`,
  ].join('');
  card.innerHTML = `
    <div class="card-title">${e.name}</div>
    <div class="badges">${badges}</div>
    <div class="loc">${e.location_name || ''}</div>
    <a class="link" href="${e.url}" target="_blank" rel="noopener">Voir l'annonce →</a>
  `;
  return card;
}

function renderCalendar(){
  const el = document.getElementById('view-cal');
  el.innerHTML = '';
  const filtered = Object.values(EVENTS).filter(matches);
  const byDate = new Map();
  filtered.forEach(e => {
    const key = e.start_date;
    if (!byDate.has(key)) byDate.set(key, []);
    byDate.get(key).push(e);
  });

  const today = new Date();
  for (let m = 0; m < CAL_MONTHS; m++){
    const monthDate = new Date(today.getFullYear(), today.getMonth() + m, 1);
    const year = monthDate.getFullYear();
    const month = monthDate.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDow = (new Date(year, month, 1).getDay() + 6) % 7; // Monday-first

    const wrap = document.createElement('div');
    wrap.className = 'cal-month';
    const h = document.createElement('h2');
    h.textContent = `${MONTH_NAMES[month]} ${year}`;
    wrap.appendChild(h);

    const grid = document.createElement('div');
    grid.className = 'cal-grid';
    DOW.forEach(d => {
      const dow = document.createElement('div');
      dow.className = 'cal-dow';
      dow.textContent = d;
      grid.appendChild(dow);
    });
    for (let i = 0; i < firstDow; i++){
      const pad = document.createElement('div');
      pad.className = 'cal-cell pad';
      grid.appendChild(pad);
    }
    for (let d = 1; d <= daysInMonth; d++){
      const dateStr = `${String(d).padStart(2,'0')}/${String(month+1).padStart(2,'0')}/${year}`;
      const dayEvents = byDate.get(dateStr) || [];
      const cell = document.createElement('div');
      cell.className = 'cal-cell' + (dayEvents.length ? ' has-events' : '');
      cell.innerHTML = `<span>${d}</span>` + (dayEvents.length ? `<span class="dot"></span><span class="n">${dayEvents.length}</span>` : '');
      if (dayEvents.length){
        cell.onclick = () => {
          state.search = '';
          document.getElementById('search').value = '';
          switchView('list');
          renderList();
          const heading = [...document.querySelectorAll('.day-heading')]
            .find(hd => hd.textContent === fmtDayHeading(parseFr(dateStr)));
          if (heading) heading.scrollIntoView({behavior:'smooth', block:'start'});
        };
      }
      grid.appendChild(cell);
    }
    wrap.appendChild(grid);
    el.appendChild(wrap);
  }
}

function renderCount(){
  const filtered = Object.values(EVENTS).filter(matches);
  document.getElementById('count').textContent = `${filtered.length} événement${filtered.length>1?'s':''}`;
}

function switchView(view){
  state.view = view;
  document.getElementById('tab-list').setAttribute('aria-selected', view==='list');
  document.getElementById('tab-cal').setAttribute('aria-selected', view==='cal');
  document.getElementById('view-list').hidden = view !== 'list';
  document.getElementById('view-cal').hidden = view !== 'cal';
}

function renderAll(){
  renderChips();
  renderCount();
  renderList();
  renderCalendar();
}

document.getElementById('tab-list').onclick = () => switchView('list');
document.getElementById('tab-cal').onclick = () => switchView('cal');
document.getElementById('search').oninput = (e) => { state.search = e.target.value.trim().toLowerCase(); renderAll(); };

renderAll();
</script>
"""


def build():
    events = json.loads(DATA_FILE.read_text())
    html = TEMPLATE.replace("__EVENTS_JSON__", json.dumps(events, ensure_ascii=False))
    html = html.replace("__CAL_MONTHS__", str(CALENDAR_MONTHS))
    OUTPUT_FILE.write_text(html)
    print(f"{OUTPUT_FILE} généré ({len(events)} événements, {OUTPUT_FILE.stat().st_size // 1024} Ko).")


if __name__ == "__main__":
    build()
