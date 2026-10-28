/* Proxima Pace, Productivity Inspector (Productivity Inspector, Rounds 1 and 2). A co-pilot who reads the city's
   instruments and calls out the numbers: delighted in numbers, a bit energetic, caring mostly about productivity. She
   lives at the top of Reports (J1) and writes three reports to read (J3): the daily one, on yesterday, waits there with
   a dot on the Reports button until it is read; the weekly one, on the Saturday-to-Friday week just ended, and the
   monthly one, on the month just ended, she brings herself on the first open after their period ends, in a speech
   bubble with Read. She and Gus never speak at once: Gus first, then her. What each report holds is L1, her facts L2,
   her lines V2, word for word. Every count is of ticks, as in Reports.
   Her voice (V1), a compass for her lines: quick, bright and exact; short call-outs with a little cockpit talk (inbound,
   logged, on deck, copy that); real numbers said precisely, an exclamation when a number is good; she opens with the
   number and closes with the next thing to do. She never scolds or nags (Gus's job), mentions garbage, makes up or
   rounds a number, praises with empty words, or crowds a report with more than it holds.
   Her face is her portrait, on her dark sky blue (0.1.48).
   She also announces a finished milestone's street party (Celebrations, Rounds 1 and 2), with Go to it, in one of two
   lines approved word for word, picked by the milestone; while the project view is open, her bubble sits beside it. */

/* ---------- her lines (V2), approved word for word ---------- */
const PROXIMA_LINES = {
  week: ['Weekly report inbound! {n} tasks landed this week.', "Copy that, week logged: {n} tasks done. Report's ready."],
  week0: ['Quiet week: no tasks landed. Next week holds {due} due.'],
  month: ['Monthly report on deck! {n} tasks in {month}.', "{month} is logged: {n} tasks, {m} milestones. Report's ready."],
  day: ["Yesterday: {n} tasks landed. Today's flight plan: {due} due."],
  one_left: ["{milestone} is one task from done: {task}. Let's land it!"],
  empty_week: ["Next week's flight plan is empty. Nothing due yet."],
  repeat_run: ['{repeat}: ticked {k} weeks running. Steady hands!'],
  milestone: ["Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!",
    "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!"],
};
/* A line with its blanks filled; counts read in the singular when they are one. */
function proximaFill(text, v) {
  return text.replace('{n} tasks', () => plural(v.n, 'task', 'tasks')).replace('{m} milestones', () => plural(v.m, 'milestone', 'milestones'))
    .replace('{k} weeks', () => plural(v.k, 'week', 'weeks')).replace(/\{(\w+)\}/g, (all, k) => (v[k] == null ? all : String(v[k])));
}
/* One line from a moment's list, the same one each time for the same report. */
const proximaPick = (list, seed) => list[hashStr(seed) % list.length];

/* ---------- her reports (L1, L2) ---------- */
const PROXIMA_KINDS = ['daily', 'weekly', 'monthly'];
/* The period a report is on, the one before it, and the one after it, which the report looks ahead to. */
function proximaPeriod(kind, now = Date.now()) {
  const today = startOfDay(now);
  if (kind === 'daily') { const from = addDays(today, -1); return { kind, from, to: today, prev: addDays(from, -1), next: addDays(today, 1), key: ymd(from) }; }
  if (kind === 'weekly') { const to = weekStartOf(now), from = addDays(to, -7); return { kind, from, to, prev: addDays(from, -7), next: addDays(to, 7), key: ymd(from) }; }
  const to = monthStartOf(now), from = addMonths(to, -1);
  return { kind, from, to, prev: addMonths(from, -1), next: addMonths(to, 1), key: ymd(from).slice(0, 7) };
}
const PROXIMA_WORDS = {
  daily: { title: 'Daily report', short: 'Daily', before: 'the day before', ahead: 'Today', none: 'Nothing due today.' },
  weekly: { title: 'Weekly report', short: 'Weekly', before: 'the week before', ahead: 'This week', none: 'Nothing due this week.' },
  monthly: { title: 'Monthly report', short: 'Monthly', before: 'the month before', ahead: 'This month', none: 'Nothing due this month.' },
};
function proximaLabel(per, now = Date.now()) {
  if (per.kind === 'daily') return weekdayOf(ymd(per.from)) + ' ' + dayMonth(per.from);
  if (per.kind === 'weekly') return weekLabel(per.from);
  return monthLabel(per.from, new Date(per.from).getFullYear() !== new Date(now).getFullYear());
}
/* The first thing the city recorded: a report on a period that ended before it has nothing to say. */
function cityStartedAt() {
  let min = Infinity;
  for (const p of DB.projects) {
    if (typeof p.createdAt === 'number') min = Math.min(min, p.createdAt);
    for (const e of p.activity || []) min = Math.min(min, e.at);
  }
  return min;
}
const proximaRelevant = per => per.to > cityStartedAt();
/* A tick of this task: Activity cuts a line at 300 characters, so the first 290 decide. */
const sameTask = (e, t) => e.text.slice(0, 290) === String(t.text).slice(0, 290);
/* Repeats ticked every week in a row, up to the last full week: weekly or more often only. */
function repeatRuns(ticks, now = Date.now()) {
  const out = [], end = weekStartOf(now);
  for (const p of DB.projects) for (const t of p.todos) {
    const r = t.repeat;
    if (!r || !(r.every === 'week' || (r.every === 'day' && r.n <= 7))) continue;
    const mine = ticks.filter(e => e.p === p && sameTask(e, t));
    let k = 0;
    for (let w = addDays(end, -7); k < 520; w = addDays(w, -7)) { if (!mine.some(e => e.at >= w && e.at < addDays(w, 7))) break; k++; }
    if (k >= 3) out.push({ p, t, k });
  }
  return out.sort((a, b) => b.k - a.k || a.t.text.localeCompare(b.t.text));
}
/* Milestones one task from done: every other task in them done, and no repeat, which never finishes. */
function milestonesOneLeft() {
  const out = [];
  for (const p of DB.projects) for (const m of p.milestones) {
    const ts = p.todos.filter(t => t.milestoneId === m.id);
    if (ts.length < 2 || ts.some(t => t.repeat)) continue;
    const open = ts.filter(t => !t.done);
    if (open.length === 1) out.push({ p, m, t: open[0] });
  }
  return out;
}
function proximaReport(kind, now = Date.now()) {
  const per = proximaPeriod(kind, now), ticks = taskTicks(DB.projects, now), today = startOfDay(now);
  const count = (a, b) => ticks.filter(e => e.at >= a && e.at < b).length;
  const r = { kind, per, label: proximaLabel(per, now), n: count(per.from, per.to), before: count(per.prev, per.from), streak: streakOf(ticks, now) };
  r.milestones = milestonesFinished(DB.projects).filter(x => x.at >= per.from && x.at < per.to).reverse();
  /* what the coming day, week or month holds, from today on (what is late is under Overdue); a repeat waiting to come
     back in it is due then too */
  r.due = [];
  const ahead = Math.max(per.to, today);
  for (const p of DB.projects) for (const t of p.todos) { const d = parseYmd(t.due); if (!t.done && d != null && d >= ahead && d < per.next) r.due.push({ p, t }); }
  r.due.sort((a, b) => parseYmd(a.t.due) - parseYmd(b.t.due) || a.p.name.localeCompare(b.p.name));
  if (kind !== 'daily') {
    r.buildings = ticksByProject(ticks, per.from, per.to);
    r.busiest = r.buildings.filter(b => b.n === (r.buildings[0] || {}).n);
    r.quiet = DB.projects.filter(p => openTasks(p, now).length && !r.buildings.some(b => b.p === p)).sort((a, b) => a.name.localeCompare(b.name));
    r.overdue = [];
    for (const p of DB.projects) for (const t of openTasks(p, now)) { const d = parseYmd(t.due); if (d != null && d < today) r.overdue.push({ p, t }); }
    r.overdue.sort((a, b) => parseYmd(a.t.due) - parseYmd(b.t.due) || a.p.name.localeCompare(b.p.name));
  }
  if (kind === 'monthly') {
    r.repeats = [];
    for (const p of DB.projects) for (const t of p.todos) {
      if (!t.repeat) continue;
      const k = ticks.filter(e => e.p === p && sameTask(e, t) && e.at >= per.from && e.at < per.to).length;
      if (k) r.repeats.push({ p, t, k });
    }
    r.repeats.sort((a, b) => b.k - a.k || a.t.text.localeCompare(b.t.text));
    r.notes = DB.projects.flatMap(p => allNotes(p).filter(n => n.at >= per.from && n.at < per.to).map(n => ({ p, n }))).sort((a, b) => a.n.at - b.n.at);
  }
  /* her facts (L2): a milestone one task from done, next week with nothing due, a repeat kept up */
  r.facts = milestonesOneLeft().slice(0, 5).map(x => proximaFill(PROXIMA_LINES.one_left[0], { milestone: x.m.name, task: x.t.text }));
  if (kind === 'weekly' && !r.due.length) r.facts.push(PROXIMA_LINES.empty_week[0]);
  if (kind !== 'daily') for (const x of repeatRuns(ticks, now).slice(0, 5)) r.facts.push(proximaFill(PROXIMA_LINES.repeat_run[0], { repeat: x.t.text, k: x.k }));
  /* her first line */
  const seed = kind + per.key, v = { n: r.n, due: r.due.length, m: r.milestones.length, month: monthLabel(per.from, false) };
  r.line = proximaFill(kind === 'daily' ? PROXIMA_LINES.day[0] : kind === 'weekly' ? (r.n ? proximaPick(PROXIMA_LINES.week, seed) : PROXIMA_LINES.week0[0])
    : (r.n ? proximaPick(PROXIMA_LINES.month, seed) : PROXIMA_LINES.month[1]), v);
  return r;
}

const Proxima = (() => {
  const KEY = 'nullovation-city:proxima';                 // what was read and what she said, on this computer
  const SAY_MS = 14000;
  let state = (() => { try { const v = JSON.parse(localStorage.getItem(KEY)); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } })();
  if (!state.read || typeof state.read !== 'object') state.read = {};
  if (!state.spoke || typeof state.spoke !== 'object') state.spoke = {};
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* this visit only */ } };
  let queue = [], saying = null, sayTimer = 0, waitTimer = 0, sayMs = SAY_MS, started = false;

  const periods = (now = Date.now()) => PROXIMA_KINDS.map(k => proximaPeriod(k, now)).filter(proximaRelevant);
  const unread = per => state.read[per.kind] !== per.key;
  const anyUnread = () => periods().some(unread);

  /* ---------- her face: her portrait (0.1.48), Abdurrahman's 256 px pixel art, shown shrunk in a frame of her dark
     sky blue; the frame sets the size ---------- */
  const faceImg = () => h('img', { class: 'face-pic', alt: '', src: PORTRAITS.proxima, width: 256, height: 256, draggable: 'false' });
  const face = () => h('span', { class: 'gus-face px-face', 'aria-hidden': 'true' }, faceImg());
  /* Her face at a size: 48 px in the News section, 100 in a leader's bubble, when she brings a building's news. */
  const faceEl = (size = 48) => { const el = face(); el.style.setProperty('--face', size + 'px'); return el; };
  const nameTag = () => h('span', { class: 'gus-name px-name' }, h('b', null, 'Proxima Pace'), h('span', null, 'Productivity Inspector'));

  /* ---------- her card at the top of Reports (J1): her face, her latest line, and her three reports; Reports draws it
     with its tabs, keeping the focus where it was ---------- */
  function renderCard() {
    const box = $('#pxCard');
    if (!box) return;
    const now = Date.now(), list = periods(now);
    const lead = [...list].reverse().find(unread) || list[0];      // her line: the biggest report not read yet, else the daily one
    const rows = list.map(per => {
      const isNew = unread(per);
      return h('li', null, h('button', { class: 'px-report-row' + (isNew ? ' new' : ''), type: 'button', 'data-k': 'px-' + per.kind, 'data-kind': per.kind,
        title: 'Read the ' + PROXIMA_WORDS[per.kind].title.toLowerCase() + (isNew ? ', not read yet' : ''), onclick: () => openReport(per.kind) },
        h('i', { class: 'px-dot', 'aria-hidden': 'true' }),
        h('span', { class: 'px-report-kind' }, PROXIMA_WORDS[per.kind].short), h('span', { class: 'px-report-when' }, proximaLabel(per, now)),
        isNew ? h('span', { class: 'sr-only' }, ', new') : null));
    });
    box.replaceChildren(
      h('div', { class: 'gus-head px-head' }, face(), nameTag()),
      h('p', { id: 'pxLine', class: 'gus-line px-line' }, lead ? proximaReport(lead.kind, now).line : 'Her first report comes tomorrow.'),
      list.length ? h('ul', { id: 'pxReports', class: 'px-reports' }, rows) : null);
  }
  /* The Reports button wears a dot while a report waits unread. */
  function renderDot() {
    const b = $('#btnOpenReports');
    if (!b) return;
    const on = anyUnread();
    b.classList.toggle('has-news', on);
    b.title = on ? 'Reports (R). Proxima has a report for you.' : 'Reports (R)';
  }
  function refresh() { renderDot(); if (typeof Reports !== 'undefined') Reports.refresh(); }

  /* ---------- a report, to read ---------- */
  function openReport(kind) {
    const now = Date.now(), r = proximaReport(kind, now), w = PROXIMA_WORDS[kind];
    state.read[kind] = r.per.key;
    if (kind !== 'daily') state.spoke[kind] = r.per.key;    // read before she brought it: she has nothing to bring
    save();
    queue = queue.filter(k => k !== kind);
    if (saying && saying.kind === kind) hush(false);
    const goP = p => () => { Panel.close(); Menu.closeDrawer(); MapView.select(p.id); };
    const goT = (p, t) => () => { Panel.close(); FullView.openTask(p.id, t.id); };
    const sec = (title, ...kids) => h('section', { class: 'px-sec' }, h('h4', null, title), ...kids);
    const list = items => h('ul', { class: 'px-list' }, items);
    const diff = r.n - r.before;
    const vs = diff > 0 ? ', ' + diff + ' more than ' + w.before : diff < 0 ? ', ' + (-diff) + ' fewer than ' + w.before : ', the same as ' + w.before;
    const s = r.streak;
    const streakText = s.n ? plural(s.n, 'day', 'days') + (s.n >= s.best.n ? ', the longest.' : ', ' + (s.best.n - s.n) + ' short of the longest, ' + plural(s.best.n, 'day', 'days') + '.')
      : 'None now. The longest: ' + plural(s.best.n, 'day', 'days') + '.';
    const due = x => { const d = dueInfo(x.t, now); return h('span', { class: 'recap-day' + (d && d.tone ? ' ' + d.tone : '') }, weekdayOf(x.t.due) + ' ' + dayMonth(parseYmd(x.t.due))); };
    const taskRow = (x, extra) => h('li', null, extra, h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goT(x.p, x.t) }, x.t.text), h('span', { class: 'px-proj', dir: 'auto' }, x.p.name));
    const body = h('div', { class: 'px-report', 'data-kind': kind },
      h('div', { class: 'px-says' }, face(), h('div', { class: 'px-says-body' }, nameTag(), h('p', { id: 'pxReportLine', class: 'px-quote' }, r.line))),
      h('p', { class: 'px-when' }, r.label),
      sec('Tasks finished', h('p', { id: 'pxFinished' }, h('b', null, String(r.n)), vs + '.')),
      sec('Streak', h('p', { id: 'pxStreak' }, streakText)),
      sec('Milestones finished', r.milestones.length ? list(r.milestones.map(x => h('li', null, h('span', { class: 'recap-day' }, fmtDate(x.at)),
        h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: () => { Panel.close(); FullView.open(x.p.id); } }, x.m.name), h('span', { class: 'px-proj', dir: 'auto' }, x.p.name))))
        : h('p', { class: 'px-none' }, 'None.')),
      kind === 'daily' ? null : [
        sec('By building', r.buildings.length ? list(r.buildings.map(b => h('li', null, News.reportFace(b.p, 20), h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goP(b.p) }, b.p.name), h('b', { class: 'px-n' }, String(b.n)))))
          : h('p', { class: 'px-none' }, 'No tasks finished.')),
        r.busiest.length ? sec('Busiest building', h('p', { id: 'pxBusiest' }, r.busiest.map(b => b.p.name).join(' and ') + ', ' + plural(r.busiest[0].n, 'task', 'tasks') + (r.busiest.length > 1 ? ' each.' : '.'))) : null,
        r.quiet.length ? sec('Nothing finished', list(r.quiet.map(p => h('li', null, h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goP(p) }, p.name))))) : null,
        sec('Overdue', r.overdue.length ? [h('p', { id: 'pxOverdue' }, plural(r.overdue.length, 'overdue task', 'overdue tasks') + '. Close this one first:'),
          list([taskRow(r.overdue[0], h('span', { class: 'recap-day late' }, dueInfo(r.overdue[0].t, now).text))])] : h('p', { id: 'pxOverdue', class: 'px-none' }, 'Nothing overdue.')),
      ],
      kind === 'monthly' ? [
        r.repeats.length ? sec('Repeats kept up', list(r.repeats.map(x => h('li', null, h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goT(x.p, x.t) }, x.t.text),
          h('span', { class: 'px-proj' }, plural(x.k, 'time', 'times')))))) : null,
        sec('Notes written', r.notes.length ? [h('p', null, plural(r.notes.length, 'note', 'notes') + '.'), list(r.notes.map(x => h('li', null, h('span', { class: 'recap-day' }, dayMonth(x.n.at)),
          h('span', { dir: 'auto' }, noteLine(x.n).slice(0, 90)), h('span', { class: 'px-proj', dir: 'auto' }, x.p.name))))] : h('p', { class: 'px-none' }, 'None.')),
      ] : null,
      sec(w.ahead, r.due.length ? [h('p', null, plural(r.due.length, 'task', 'tasks') + ' due.'), list(r.due.map(x => taskRow(x, due(x))))] : h('p', { class: 'px-none' }, w.none)),
      r.facts.length ? h('section', { class: 'px-sec px-facts' }, h('h4', null, 'From Proxima'), h('ul', { id: 'pxFacts', class: 'px-list' }, r.facts.map(f => h('li', { dir: 'auto' }, f)))) : null);
    Panel.open(w.title, body);
    refresh();
    pump();                                                // the next one she has waits until this one is closed
  }

  /* ---------- speaking: the weekly and monthly reports, after Gus ---------- */
  function check(now = Date.now()) {
    if (!started) return;
    for (const per of periods(now)) {
      if (per.kind === 'daily' || state.spoke[per.kind] === per.key || queue.includes(per.kind) || (saying && saying.kind === per.kind)) continue;
      queue.push(per.kind);
    }
    pump();
  }
  function pump() {
    clearTimeout(waitTimer);
    if (saying || !queue.length) return;
    if ((typeof Gus !== 'undefined' && Gus.isSaying()) || (typeof News !== 'undefined' && News.isHeld()) || Panel.isOpen() || Confirm.isOpen() || !sayRoom()) { waitTimer = setTimeout(pump, 500); return; }
    const kind = queue.shift();
    if (typeof kind !== 'string') { if (getProject(kind.pid)) say(kind); else pump(); return; }   // a milestone's party
    const r = proximaReport(kind);
    state.spoke[kind] = r.per.key; save();
    say(r);
  }
  let T = null, shown = 0;                                 // her line, typing out (0.1.78)
  function say(r) {
    const party = r.kind === 'milestone';
    if (typeof News !== 'undefined') News.yieldTo();            // a leader's news waits for her (Leader UX, N3)
    saying = { kind: r.kind, key: party ? r.key : r.per.key, item: party ? r : null };
    const box = $('#pxSay'), act = $('#pxSayRead');
    if (T) T.hush();
    $('#pxSayText').textContent = r.line;
    if (!$('#pxSayFace').firstChild) $('#pxSayFace').append(faceImg());
    act.textContent = party ? 'Go to it' : 'Read';
    act.onclick = party ? () => { hush(false); goTo(r.pid); pump(); }
      : () => { hush(false); if (typeof Reports !== 'undefined') Reports.open(); openReport(r.kind); pump(); };
    const edge = panelEdge();                                                       // beside the panels on the map, over the map they leave open
    box.style.left = edge ? Math.round(edge + 22) + 'px' : '';
    box.hidden = false;
    fitSay(box);
    if (typeof Sound !== 'undefined') Sound.bubble();
    if (!T) T = News.typer('#pxSayText', '#pxSayFace');
    T.speak('px:' + ++shown, 'proxima');                   // her line types out in her voice, after a bubble's sound (0.1.78)
    requestAnimationFrame(() => box.classList.add('show'));
    clearTimeout(sayTimer);
    sayTimer = setTimeout(() => hush(), sayMs);
  }
  function hush(next = true) {
    clearTimeout(sayTimer);
    if (T) T.hush();
    const box = $('#pxSay');
    if (box) { box.classList.remove('show'); box.hidden = true; }
    saying = null;
    if (next) waitTimer = setTimeout(pump, 400);
  }

  /* Gus cuts in: her bubble goes, and she says it again once he is done. */
  function yieldToGus() {
    if (!saying) return;
    const kind = saying.item || saying.kind;
    hush(false);
    queue.unshift(kind);
    pump();
  }
  /* A finished milestone's street party: she says it after anything already waiting, and Go to it glides the map to the
     building, into the open part beside the project view when it is open. */
  function announce(p, m, n) {
    const line = proximaFill(proximaPick(PROXIMA_LINES.milestone, 'milestone:' + m.id), { milestone: m.name, project: p.name, n });
    queue.push({ kind: 'milestone', key: m.id, pid: p.id, line });
    pump();
  }
  function goTo(pid) {
    if (!getProject(pid)) return;
    MapView.glideBeside(pid, panelEdge());
  }

  function init() {
    $('#pxSayClose').innerHTML = iconSvg('close', 16);
    $('#pxSayClose').addEventListener('click', () => hush());
    started = true;
    renderDot();
    check();
    setInterval(() => { refresh(); check(); }, 60000);        // a new day, week or month while the city stays open
  }
  return { init, refresh, renderCard, renderDot, yieldToGus, openReport, check, hush, announce, faceEl, isSaying: () => !!saying, saying: () => saying && saying.kind, report: proximaReport,
    busy: () => !!saying || queue.length > 0,
    _test: { sayMs: ms => { sayMs = ms; }, state: () => JSON.parse(JSON.stringify(state)), forget: () => { state = { read: {}, spoke: {} }; save(); queue = []; }, queue: () => [...queue] } };
})();
