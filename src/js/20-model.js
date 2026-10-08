const BUBBLE_TODOS = 3;        // open todos shown in the bubble
const DUE_SOON_DAYS = 3;       // todos due this soon (or overdue) jump to the top of the bubble
const LINK_ICONS = ['doc', 'code', 'github', 'claude', 'chat', 'folder', 'web'];
const MAX_SHORTCUTS = 8;       // a building's shortcut wheel holds at most this many links
/* A link's icon, guessed from its address. */
function guessIcon(url) {
  if (winPathOf(url)) return 'folder';
  const u = String(url || '').toLowerCase().trim();
  if (/^claude:|claude\.ai|claude\.com/.test(u)) return 'claude';
  if (/github\.com|github\.io|^git@github/.test(u)) return 'github';
  if (/notion\.so|docs\.google|confluence|\.pdf|\.docx?\b/.test(u)) return 'doc';
  if (/gitlab|bitbucket|localhost|codepen|replit/.test(u)) return 'code';
  if (/slack|chatgpt|discord|teams\.microsoft|whatsapp|t\.me/.test(u)) return 'chat';
  if (/drive\.google|dropbox|onedrive|^file:/.test(u)) return 'folder';
  return 'web';
}
/* A building's shortcuts: the links marked for its wheel that can be opened, in the links' order. Only the first
   MAX_SHORTCUTS show; more are allowed, with a warning where links are edited. */
const shortcutLinks = p => p.links.filter(l => l.shortcut !== false && safeUrl(l.url));

/* The map: NU by NV plots, each S x S tiles, GAP tiles of bare ground between. NU runs along u (down to the right on
   screen), NV along v (down to the left); each runs from MIN_N to MAX_N. OU and OV place the grid in the whole city:
   plot (u, v) is the city's plot (u + OU, v + OV). Everything dealt by place (parks, street details, props) is dealt
   by the city's plot, so it stays with its buildings when a line or a ring is added or taken off. */
const WORLD = { NU: 5, NV: 5, OU: 0, OV: 0, S: 4, GAP: 2, MARGIN: 2, TW: 32, TH: 16, MIN_N: 5, MAX_N: 11 };
WORLD.PITCH = WORLD.S + WORLD.GAP;
const spanTiles = n => WORLD.MARGIN * 2 + n * WORLD.S + (n - 1) * WORLD.GAP;
function setWorld(w) {
  WORLD.NU = w.nu; WORLD.NV = w.nv; WORLD.OU = w.ou; WORLD.OV = w.ov;
  WORLD.TI = spanTiles(w.nu); WORLD.TJ = spanTiles(w.nv);
}
const worldState = () => ({ nu: WORLD.NU, nv: WORLD.NV, ou: WORLD.OU, ov: WORLD.OV });
setWorld({ nu: 5, nv: 5, ou: 0, ov: 0 });

/* The city's settings: what the city is like, so they travel with it in the data file and every backup. How this
   computer shows the city (the bar's buttons, motion, the postcard, folder links) stays in this browser instead.
   parks holds the kinds picked in Edit City, by the city's plot; it is the city's layout, so no reset touches it. */
const CITY_DEFAULTS = {
  crowd: 'medium', cars: true, buses: true, drones: true, cyclists: true, walkers: true, street: 1, walk: 1,
  props: true, busstop: true, vending: true, billboard: true, bin: true, amount: 1, deal: 0,
  night: '19:00', day: '06:30', rest: [], away: '',
};
const AMOUNTS = { min: 0.25, max: 2, step: 0.25 };   // the sliders: a quarter to twice today's counts
function sanitizeCity(raw, crowdFallback = null) {
  const r = raw && typeof raw === 'object' ? raw : {}, out = {};
  const CROWDS = ['none', 'small', 'medium', 'large'];
  for (const [k, d] of Object.entries(CITY_DEFAULTS)) {           // in the defaults' order, so files read alike
    const v = r[k];
    if (k === 'crowd') out[k] = CROWDS.includes(v) ? v : CROWDS.includes(crowdFallback) ? crowdFallback : d;
    else if (typeof d === 'boolean') out[k] = typeof v === 'boolean' ? v : d;
    else if (k === 'deal') out[k] = Number.isInteger(v) && v >= 0 ? v : d;
    else if (typeof d === 'number') out[k] = typeof v === 'number' && isFinite(v) ? clamp(Math.round(v / AMOUNTS.step) * AMOUNTS.step, AMOUNTS.min, AMOUNTS.max) : d;
    else if (k === 'night' || k === 'day') out[k] = typeof v === 'string' && /^([01]\d|2[0-3]):[0-5]\d$/.test(v) ? v : d;
    else if (k === 'rest') out[k] = Array.isArray(v) ? [...new Set(v.filter(x => Number.isInteger(x) && x >= 0 && x <= 6))].sort() : [];
    else if (k === 'away') out[k] = parseYmd(v) != null ? v : '';
  }
  out.parks = {};
  if (r.parks && typeof r.parks === 'object') for (const [k, v] of Object.entries(r.parks)) if (/^-?\d+,-?\d+$/.test(k) && typeof v === 'string') out.parks[k] = v.slice(0, 60);
  return out;
}

let DB = { app: 'nullovation-city', version: 3, world: worldState(), city: sanitizeCity(null), projects: [] };

const App = {
  selectedId: null,
  filter: { q: '' },
};

function getProject(id) { return DB.projects.find(p => p.id === id) || null; }
function projectAt(u, v, list = DB.projects) { return list.find(p => p.plot.u === u && p.plot.v === v) || null; }
function freePlots() {
  const out = [];
  for (let v = 0; v < WORLD.NV; v++) for (let u = 0; u < WORLD.NU; u++) if (!projectAt(u, v)) out.push({ u, v });
  return out;
}

function progressOf(p) {
  const total = p.todos.length;
  const done = p.todos.filter(t => t.done).length;
  const auto = total ? Math.round((done / total) * 100) : 0;
  const manual = typeof p.progressOverride === 'number';
  return { pct: manual ? clamp(Math.round(p.progressOverride), 0, 100) : auto, auto, manual, done, total };
}
function openTodos(p, n = BUBBLE_TODOS) { return p.todos.filter(t => !t.done).slice(0, n); }

function filterActive() { return !!App.filter.q; }
function matchesFilter(p) {
  const f = App.filter;
  if (!f.q) return true;
  const gname = p.generic && typeof GENERICS !== 'undefined' ? (GENERICS.find(g => g.id === p.generic) || {}).name : '';
  const hay = norm([p.name, p.description, gname, ...p.todos.map(t => t.text + ' ' + (t.description || '')), ...p.links.map(l => l.label),
    ...p.milestones.map(m => m.name), ...p.notes.map(n => (n.title || '') + ' ' + n.text)].join(' \n '));
  return hay.includes(f.q);
}

function blankProject(o = {}) {
  const now = Date.now();
  return Object.assign({
    id: uid('p'), name: 'Untitled project', description: '',
    deadline: '', progressOverride: null, todos: [], links: [], milestones: [], notes: [],
    plot: { u: 0, v: 0 }, art: { has: false, includesPlot: false }, generic: null, activity: [], flip: false,
    urgency: { system: 'none', days: 1, lastWorked: null, pickedAt: null },
    createdAt: now, updatedAt: now,
  }, o);
}
const todo = (text, milestoneId = null) => ({ id: uid('t'), text, description: '', done: false, doneAt: null, due: '', milestoneId });

/* ---------- milestones and due dates ---------- */
/* Todos without a milestone come first, then each milestone in order. */
function groupsOf(p) {
  const known = new Set(p.milestones.map(m => m.id));
  const out = [{ ms: null, todos: p.todos.filter(t => !t.milestoneId || !known.has(t.milestoneId)) }];
  for (const m of p.milestones) out.push({ ms: m, todos: p.todos.filter(t => t.milestoneId === m.id) });
  return out;
}
/* The current milestone is the first group that still has open todos. */
function currentGroup(p) { return groupsOf(p).find(g => g.ms && g.todos.some(t => !t.done)) || null; }
/* What is next: the first open todo in the current milestone, in list order. */
function nextTask(p) { const g = currentGroup(p); return g ? g.todos.find(t => !t.done) || null : null; }
/* Every todo lives in a milestone. Anything outside one moves into "To do", at the top. */
function ensureMilestones(p) {
  const known = new Set(p.milestones.map(m => m.id));
  const loose = p.todos.filter(t => !t.milestoneId || !known.has(t.milestoneId));
  if (!loose.length) return;
  let home = p.milestones.find(m => m.name === 'To do');
  if (!home) { home = { id: uid('m'), name: 'To do', collapsed: false }; p.milestones.unshift(home); }
  for (const t of loose) t.milestoneId = home.id;
  normalizeOrder(p);
}
/* One task as text for a Claude chat: what it is, and where it sits. */
function taskForClaude(p, t, now = Date.now()) {
  const L = [];
  const ms = p.milestones.find(m => m.id === t.milestoneId);
  const g = ms ? groupsOf(p).find(x => x.ms && x.ms.id === ms.id) : null;
  L.push('# Task: ' + t.text);
  L.push('Project: ' + p.name);
  if (ms) L.push('Milestone: ' + ms.name + ' (' + g.todos.filter(x => x.done).length + '/' + g.todos.length + ' done)');
  const d = dueInfo(t, now);
  L.push('Due: ' + (d ? d.text : 'no date'));
  L.push('State: ' + (t.done ? 'done' : 'open'));
  L.push('');
  L.push('## Description');
  L.push((t.description || '').trim() || 'No description yet.');
  return L.join('\n');
}
/* A note, ready to paste into a Claude chat. */
function noteForClaude(p, n) {
  const title = n.title.trim() || (n.text.trim().split('\n')[0] || 'Untitled note').slice(0, 120);
  const body = n.title.trim() ? n.text.trim() : n.text.trim().split('\n').slice(1).join('\n').trim();
  const L = ['# Note: ' + title, 'Project: ' + p.name, 'Written: ' + fmtStamp(n.at), '', '## Note', body || (n.title.trim() ? 'No text yet.' : title)];
  return L.join('\n');
}
async function copyNote(p, n) {
  if (await copyText(noteForClaude(p, n))) toast('Note copied for Claude.');
  else toast('The browser blocked copying. Try again.', 'error');
}
/* A milestone as a work package: its open tasks with their descriptions, then what is done. */
function milestoneForClaude(p, m, now = Date.now()) {
  const g = groupsOf(p).find(x => x.ms && x.ms.id === m.id) || { todos: [] };
  const open = g.todos.filter(t => !t.done), done = g.todos.filter(t => t.done);
  const L = ['# Milestone: ' + m.name, 'Project: ' + p.name, 'Progress: ' + done.length + '/' + g.todos.length + ' done'];
  L.push('', '## Open tasks');
  if (!open.length) L.push('None: every task here is done.');
  for (const t of open) {
    const d = dueInfo(t, now);
    L.push('', '### ' + t.text);
    if (d) L.push(d.text);
    L.push((t.description || '').trim() || 'No description yet.');
  }
  if (done.length) { L.push('', '## Done'); for (const t of done) L.push('- ' + t.text); }
  return L.join('\n');
}
async function copyMilestone(p, m) {
  if (await copyText(milestoneForClaude(p, m))) toast('Milestone copied for Claude, with its tasks.');
  else toast('The browser blocked copying. Try again.', 'error');
}
async function copyTask(p, t) {
  if (await copyText(taskForClaude(p, t))) toast('Task copied for Claude.');
  else toast('The browser blocked copying. Try again.', 'error');
}
/* Keeps the todo list in group order, so list order always matches what you see. */
function normalizeOrder(p) {
  p.todos = groupsOf(p).flatMap(g => g.todos);
  const known = new Set(p.milestones.map(m => m.id));
  for (const t of p.todos) if (t.milestoneId && !known.has(t.milestoneId)) t.milestoneId = null;
}
function dueInfo(t, now = Date.now()) {
  const due = parseYmd(t.due);
  if (due == null) return null;
  const diff = daysBetween(now, due);
  if (diff === 0) return { text: 'Due today', tone: 'soon', diff };
  if (diff === 1) return { text: 'Due tomorrow', tone: 'soon', diff };
  if (diff > 1) return { text: 'Due ' + fmtDate(due), tone: diff <= DUE_SOON_DAYS ? 'soon' : '', diff };
  return { text: (-diff === 1 ? '1 day' : -diff + ' days') + ' overdue', tone: 'late', diff };
}
/* The bubble: todos due soon or overdue first (any milestone), then the current milestone in list order. */
function bubbleTodos(p, n = BUBBLE_TODOS, keep = null) {
  const visible = t => !t.done || (keep && keep.has(t.id));
  const urgent = p.todos.filter(t => visible(t) && t.due && dueInfo(t) && dueInfo(t).diff <= DUE_SOON_DAYS)
    .sort((a, b) => parseYmd(a.due) - parseYmd(b.due));
  const cur = currentGroup(p);
  const rest = cur ? cur.todos.filter(t => visible(t) && !urgent.includes(t)) : [];
  return { list: [...urgent, ...rest].slice(0, n), current: cur };
}

function seedProjects() {
  return [
    blankProject({
      name: 'Nullovation City',
      plot: { u: 2, v: 2 },
      generic: 'city-hall',
      description: 'A personal project tracker drawn as a small isometric pixel city. Every project is one building: click it for a quick status bubble, or step inside for everything else.\n\n' +
        'Round 1 locked the foundations: a local HTML file, isometric daytime pastels, separate decorated plots, and placeholder blocks until real art arrives. Round 2 made block art the focus.',
      milestones: [{ id: 'm_seed_art', name: 'Block art', collapsed: false }, { id: 'm_seed_use', name: 'Move in', collapsed: false }],
      todos: [
        todo('Round 3: decide the block art loop', 'm_seed_art'),
        todo('Build the block art skill', 'm_seed_art'),
        todo('Make block art for each project', 'm_seed_art'),
        todo('Try the project view for a week', 'm_seed_use'),
      ],
    }),
  ];
}

/* Makes any loaded or imported data safe to use: fills gaps, fixes types, resolves plot clashes. */
function sanitizeProjects(raw) {
  const out = [];
  const seen = new Set();
  const taken = new Set();
  const str = (v, max = 20000) => (typeof v === 'string' ? v : '').slice(0, max);
  for (const r of Array.isArray(raw) ? raw : []) {
    if (!r || typeof r !== 'object') continue;
    let id = typeof r.id === 'string' && r.id ? r.id : uid('p');
    if (seen.has(id)) id = uid('p');
    seen.add(id);
    const now = Date.now();
    const p = blankProject({
      id,
      name: str(r.name, 120).trim() || 'Untitled project',
      description: str(r.description),
      deadline: parseYmd(r.deadline) != null ? r.deadline : '',
      progressOverride: typeof r.progressOverride === 'number' && isFinite(r.progressOverride) ? clamp(Math.round(r.progressOverride), 0, 100) : null,
      todos: (Array.isArray(r.todos) ? r.todos : []).filter(t => t && typeof t.text === 'string').map(t => ({
        id: typeof t.id === 'string' && t.id ? t.id : uid('t'), text: t.text.slice(0, 500), description: typeof t.description === 'string' ? t.description.slice(0, 8000) : '',
        done: !!t.done, doneAt: typeof t.doneAt === 'number' ? t.doneAt : null,
        due: parseYmd(t.due) != null ? t.due : '', milestoneId: typeof t.milestoneId === 'string' ? t.milestoneId : null,
      })),
      milestones: (Array.isArray(r.milestones) ? r.milestones : []).filter(m => m && typeof m.name === 'string').map(m => ({
        id: typeof m.id === 'string' && m.id ? m.id : uid('m'), name: m.name.slice(0, 120) || 'Untitled milestone', collapsed: !!m.collapsed,
      })),
      notes: (Array.isArray(r.notes) ? r.notes : []).filter(n => n && typeof n.text === 'string' && typeof n.at === 'number').map(n => ({
        id: typeof n.id === 'string' && n.id ? n.id : uid('n'), title: typeof n.title === 'string' ? n.title.slice(0, 200) : '', text: n.text.slice(0, 8000), at: n.at,
      })),
      links: (Array.isArray(r.links) ? r.links : []).filter(l => l && typeof l.url === 'string').map(l => ({
        id: typeof l.id === 'string' && l.id ? l.id : uid('l'), label: str(l.label, 120), url: l.url.slice(0, 2000), icon: LINK_ICONS.includes(l.icon) ? l.icon : guessIcon(l.url),
        shortcut: l.shortcut !== false,
      })),
      art: { has: !!(r.art && r.art.has), includesPlot: !!(r.art && r.art.has && r.art.includesPlot === true) },
      generic: typeof GENERIC_IDS !== 'undefined' && GENERIC_IDS.has(r.generic) ? r.generic : null,
      flip: !!r.flip,
      urgency: (() => {
        const u = r.urgency && typeof r.urgency === 'object' ? r.urgency : {};
        const num = x => typeof x === 'number' && isFinite(x) ? x : null;
        const done = (Array.isArray(r.todos) ? r.todos : []).map(t => t && typeof t.doneAt === 'number' ? t.doneAt : 0);
        return {
          system: ['none', 'finish', 'pace'].includes(u.system) ? u.system : 'none',
          days: clamp(Math.round(num(u.days) || 1), 1, 30),
          lastWorked: num(u.lastWorked) ?? (done.length && Math.max(...done) > 0 ? Math.max(...done) : null),
          pickedAt: num(u.pickedAt),
        };
      })(),
      activity: (Array.isArray(r.activity) ? r.activity : []).filter(e => e && typeof e.at === 'number' && typeof e.text === 'string')
        .map(e => ({ at: e.at, text: e.text.slice(0, 300) })).slice(-ACTIVITY_MAX),
      createdAt: typeof r.createdAt === 'number' ? r.createdAt : now,
      updatedAt: typeof r.updatedAt === 'number' ? r.updatedAt : now,
    });
    normalizeOrder(p);
    ensureMilestones(p);
    backfillActivity(p);
    const u = r.plot && Number.isInteger(r.plot.u) ? r.plot.u : -1;
    const v = r.plot && Number.isInteger(r.plot.v) ? r.plot.v : -1;
    p.plot = (u >= 0 && v >= 0 && u < WORLD.NU && v < WORLD.NV && !taken.has(u + ',' + v)) ? { u, v } : null;
    if (p.plot) taken.add(u + ',' + v);
    out.push({ p, raw: r });
  }
  /* Anything without a valid plot takes the free plot nearest the middle. */
  const mu = (WORLD.NU - 1) / 2, mv = (WORLD.NV - 1) / 2;
  const spare = [];
  for (let v = 0; v < WORLD.NV; v++) for (let u = 0; u < WORLD.NU; u++) if (!taken.has(u + ',' + v)) spare.push({ u, v });
  spare.sort((a, b) => Math.hypot(a.u - mu, a.v - mv) - Math.hypot(b.u - mu, b.v - mv));
  const kept = [];
  for (const item of out) {
    if (!item.p.plot) {
      const s = spare.shift();
      if (!s) continue; /* the map is full; extra projects are dropped */
      item.p.plot = s;
    }
    kept.push(item);
  }
  return kept;
}

/* ---------- saving ---------- */
const persistSoon = debounce(persistNow, 300);
function persistNow() {
  const ok = Store.save(DB);
  if (typeof Menu !== 'undefined') Menu.setSaveStatus(ok);
  if (typeof DataFile !== 'undefined') DataFile.writeSoon();
  return ok;
}
/* The complete backup: the map, the city's settings, and every project with block art inlined. Used by export, the
   data file and the daily backups. */
async function buildBackup() {
  const out = { app: 'nullovation-city', version: 3, exportedAt: new Date().toISOString(), world: worldState(), city: JSON.parse(JSON.stringify(DB.city)), projects: [] };
  for (const p of DB.projects) {
    const q = JSON.parse(JSON.stringify(p));
    if (p.art.has) { const url = await Store.getArt(p.id) || (Art.get(p.id) || {}).url; if (url) q.art.dataUrl = url; }
    out.projects.push(q);
  }
  return out;
}
/* The map a database or backup holds. Before version 3 a map was square, N by N, placed at the city's origin. */
function worldFrom(data) {
  const w = data && data.world && typeof data.world === 'object' ? data.world : {};
  const side = n => clamp(n, WORLD.MIN_N, WORLD.MAX_N), int = x => Number.isInteger(x) ? x : 0;
  if (Number.isInteger(w.nu) && Number.isInteger(w.nv)) return { nu: side(w.nu), nv: side(w.nv), ou: int(w.ou), ov: int(w.ov) };
  const n = Number.isInteger(w.size) ? w.size : 5, sq = side(n % 2 ? n : n + 1);
  return { nu: sq, nv: sq, ou: 0, ov: 0 };
}
/* Call after any change. touch updates the project's last-updated time. */
function changed(p, { touch = true, redraw = true } = {}) {
  if (p && touch) p.updatedAt = Date.now();
  persistSoon();
  if (redraw) MapView.invalidate();
  Bubble.refresh();
  Menu.refresh();
}

function createProject(name, plot, id, generic = null) {
  const p = blankProject({ id: id || uid('p'), name: name.trim().slice(0, 120) || 'Untitled project', plot: { u: plot.u, v: plot.v }, generic });
  logActivity(p, 'Planted' + (generic && typeof GENERICS !== 'undefined' ? ' as a ' + (GENERICS.find(g => g.id === generic) || { name: 'building' }).name.toLowerCase() : ''));
  DB.projects.push(p);
  persistNow();
  return p;
}
async function deleteProject(id) {
  DB.projects = DB.projects.filter(p => p.id !== id);
  if (App.selectedId === id) { App.selectedId = null; Bubble.close(); }
  await Store.deleteArt(id);
  Art.drop(id);
  MapView.dropCache(id);
  persistNow();
  MapView.invalidate();
  Menu.refresh();
}

/* Activity: a short log of what happened to a project, oldest first, capped. */
const ACTIVITY_MAX = 400;
function logActivity(p, text) {
  if (!p) return;
  if (!Array.isArray(p.activity)) p.activity = [];
  const last = p.activity[p.activity.length - 1];
  const now = Date.now();
  if (last && last.text === text && now - last.at < 60000) { last.at = now; return; }   // the same thing twice in a minute counts once
  p.activity.push({ at: now, text: String(text).slice(0, 300) });
  if (p.activity.length > ACTIVITY_MAX) p.activity.splice(0, p.activity.length - ACTIVITY_MAX);
}
/* Projects saved before the log existed get their history back from what they already record. */
function backfillActivity(p) {
  if (Array.isArray(p.activity) && p.activity.length) return;
  const ev = [{ at: p.createdAt, text: 'Planted' }];
  for (const t of p.todos) if (t.done && t.doneAt) ev.push({ at: t.doneAt, text: 'Done: ' + t.text });
  for (const n of p.notes) ev.push({ at: n.at, text: 'Wrote a note' });
  p.activity = ev.filter(e => typeof e.at === 'number').sort((a, b) => a.at - b.at).slice(-ACTIVITY_MAX);
}

/* ---------- urgency: the red and yellow bubbles over buildings ---------- */
const HOUR = 3600000;
function urgencyName(p) {
  const u = p.urgency;
  if (u.system === 'finish') return 'Work until finished';
  if (u.system === 'pace') return u.days === 1 ? 'One task per day' : 'One task per ' + u.days + ' days';
  return 'No urgency system';
}
/* Work, for urgency, is ticking a task done or pressing I worked!. */
function markWorked(p, now = Date.now()) { p.urgency.lastWorked = now; }
function iWorked(p) { markWorked(p); logActivity(p, 'I worked!'); }
/* The time an urgency system counts between two moments: rest days (the city's setting) do not count, nor does any
   time before the day you come back from being away. Due dates are not counted here: they count every day. */
function countedMs(from, to) {
  const c = DB.city || {}, back = parseYmd(c.away), rest = new Set(c.rest || []);
  const a = Math.max(from, back != null ? back : -Infinity);
  if (!(to > a)) return 0;
  if (!isFinite(a)) return Infinity;
  if (!rest.size) return to - a;
  let n = 0;
  for (let d = startOfDay(a); d < to;) {
    const next = new Date(d); next.setDate(next.getDate() + 1);
    const s = Math.max(d, a), e = Math.min(next.getTime(), to);
    if (e > s && !rest.has(new Date(d).getDay())) n += e - s;
    d = next.getTime();
  }
  return n;
}
/* Away: until that day no urgency system turns a building yellow or red. */
const awayNow = (now = Date.now()) => { const back = DB.city ? parseYmd(DB.city.away) : null; return back != null && startOfDay(now) < back; };
/* What floats over a building: red or yellow, how many distinct things need you, and why.
   Red: open tasks with less than 2 days left or overdue, or a system gone red. Yellow: a system waiting. */
function urgencyOf(p, now = Date.now()) {
  const open = p.todos.filter(t => !t.done);
  const due = open.filter(t => { const d = dueInfo(t, now); return d && d.diff <= 1; });
  const u = p.urgency || { system: 'none' };
  let sys = null, why = '';
  const span = d => d === 1 ? '24 hours' : d + ' days';
  const away = awayNow(now), rested = DB.city && DB.city.rest && DB.city.rest.length ? ', not counting rest days' : '';
  if (away) { /* systems wait until the day you come back; due dates still count */ }
  else if (u.system === 'finish' && open.length) {
    const fresh = countedMs(u.lastWorked || -Infinity, now) < 24 * HOUR;
    sys = fresh ? 'yellow' : 'red';
    why = (fresh ? 'A task was finished in the last 24 hours' : 'No task finished in the last 24 hours') + rested + '; ' + plural(open.length, 'task', 'tasks') + ' left to finish';
  } else if (u.system === 'pace') {
    const N = Math.max(1, u.days || 1) * DAY, start = u.pickedAt || now;
    const worked = u.lastWorked && u.lastWorked >= start;
    const gone = worked ? countedMs(u.lastWorked, now) : countedMs(start, now) + N;
    if (gone >= N) {
      sys = gone >= 2 * N ? 'red' : 'yellow';
      why = worked ? 'No task finished in the last ' + span(gone >= 2 * N ? 2 * u.days : u.days) : 'No task finished since ' + urgencyName(p).toLowerCase() + ' was set';
      if (!worked && sys === 'red') why += ', ' + span(u.days) + ' ago';
      why += rested;
    }
  }
  const ids = new Set(due.map(t => t.id));
  if (u.system === 'finish' && sys) for (const t of open) ids.add(t.id);
  const count = ids.size + (u.system === 'pace' && sys ? 1 : 0);
  const color = due.length || sys === 'red' ? 'red' : sys === 'yellow' ? 'yellow' : null;
  const reasons = [];
  if (due.length) reasons.push(plural(due.length, 'task is', 'tasks are') + ' due within 2 days or overdue');
  if (why) reasons.push(why);
  return { color, count, due: due.length, system: sys, reasons };
}

/* ---------- plans: a project's whole to-do structure, written elsewhere (by the nullovation-city skill) and loaded in ---------- */
const PLAN_ICONS = LINK_ICONS;
function validDue(x) { return typeof x === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(x) && parseYmd(x) != null ? x : ''; }
/* Reads a plan file, or one of the tool's own project exports, into one plain shape. Throws with a readable reason. */
function readPlan(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('That is not a plan: it holds no JSON object.');
  const src = data.project && typeof data.project === 'object' ? data.project : data;
  const str = (x, n) => typeof x === 'string' ? x.trim().slice(0, n) : '';
  const out = { name: str(src.name, 120), description: str(src.description, 8000), milestones: [], ideas: [], links: [] };
  const task = t => ({ text: str(t.text, 500), description: str(t.description, 8000), due: validDue(t.due), done: !!t.done });
  if (Array.isArray(src.todos) && Array.isArray(src.milestones) && src.milestones.every(m => m && typeof m.id === 'string')) {
    for (const m of src.milestones) out.milestones.push({ name: str(m.name, 120) || 'Untitled milestone',
      tasks: src.todos.filter(t => t && t.milestoneId === m.id && typeof t.text === 'string' && t.text.trim()).map(task) });
  } else {
    if (!Array.isArray(src.milestones)) throw new Error('A plan needs a milestones list.');
    for (const m of src.milestones) {
      if (!m || typeof m !== 'object') continue;
      out.milestones.push({ name: str(m.name, 120) || 'Untitled milestone',
        tasks: (Array.isArray(m.tasks) ? m.tasks : []).filter(t => t && typeof t.text === 'string' && t.text.trim()).map(task) });
    }
  }
  for (const i of (Array.isArray(src.ideas) ? src.ideas : Array.isArray(src.notes) ? src.notes : []))
    if (i && typeof i === 'object' && (str(i.title, 200) || str(i.text, 8000))) out.ideas.push({ title: str(i.title, 200), text: str(i.text, 8000) });
  for (const l of (Array.isArray(src.links) ? src.links : []))
    if (l && typeof l.url === 'string' && l.url.trim()) out.links.push({ label: str(l.label, 120), url: l.url.trim().slice(0, 2000), icon: PLAN_ICONS.includes(l.icon) ? l.icon : guessIcon(l.url) });
  if (!out.milestones.length) throw new Error('The plan has no milestones, so there is nothing to load.');
  return out;
}
/* A tasks file: one or a few tasks to add to a project, with an optional milestone name as a suggestion. */
function readTasks(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('That is not a tasks file: it holds no JSON object.');
  const str = (x, n) => typeof x === 'string' ? x.trim().slice(0, n) : '';
  const tasks = (Array.isArray(data.tasks) ? data.tasks : []).filter(t => t && typeof t.text === 'string' && t.text.trim())
    .map(t => ({ text: str(t.text, 500), description: str(t.description, 8000), due: validDue(t.due) }));
  if (!tasks.length) throw new Error('The file has no tasks, so there is nothing to add.');
  return { milestone: str(data.milestone, 120), tasks };
}
const isTasksFile = data => !!data && typeof data === 'object' && (data.kind === 'tasks' || (Array.isArray(data.tasks) && !data.project && !Array.isArray(data.milestones)));
/* Adds tasks at the end of one milestone: an existing one by id, or a new one by name. */
function addTasks(p, tasks, target) {
  let ms = target.id ? p.milestones.find(m => m.id === target.id) : null;
  if (!ms) { ms = { id: uid('m'), name: (target.name || '').trim().slice(0, 120) || 'To do', collapsed: false }; p.milestones.push(ms); logActivity(p, 'New milestone: ' + ms.name); }
  ms.collapsed = false;
  for (const t of tasks) {
    p.todos.push(Object.assign(todo(t.text, ms.id), { description: t.description, due: t.due }));
    logActivity(p, 'Added todo: ' + t.text);
  }
  normalizeOrder(p);
  return ms;
}
/* Replaces the description, milestones, and tasks; adds ideas as notes and new links; keeps everything else. */
function applyPlan(p, plan, now = Date.now()) {
  if (plan.name) p.name = plan.name;
  p.description = plan.description;
  p.milestones = []; p.todos = [];
  let tasks = 0;
  for (const m of plan.milestones) {
    const ms = { id: uid('m'), name: m.name, collapsed: false };
    p.milestones.push(ms);
    for (const t of m.tasks) {
      p.todos.push(Object.assign(todo(t.text, ms.id), { description: t.description, due: t.due, done: t.done, doneAt: t.done ? now : null }));
      tasks++;
    }
  }
  p.progressOverride = null;
  const seen = new Set(p.notes.map(n => (n.title || '') + '\n' + n.text));
  let ideas = 0;
  plan.ideas.forEach((i, k) => {
    const key = i.title + '\n' + i.text;
    if (seen.has(key)) return;
    seen.add(key); ideas++;
    p.notes.push({ id: uid('n'), title: i.title, text: i.text, at: now + k });
  });
  const urls = new Set(p.links.map(l => l.url));
  let links = 0;
  for (const l of plan.links) if (!urls.has(l.url)) { urls.add(l.url); links++; p.links.push({ id: uid('l'), label: l.label, url: l.url, icon: l.icon, shortcut: true }); }
  logActivity(p, 'Loaded a plan: ' + plural(plan.milestones.length, 'milestone', 'milestones') + ', ' + plural(tasks, 'task', 'tasks') + (ideas ? ', ' + plural(ideas, 'idea', 'ideas') : ''));
  return { milestones: plan.milestones.length, tasks, ideas, links };
}
