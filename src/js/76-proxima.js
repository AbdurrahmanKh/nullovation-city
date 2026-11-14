/* Proxima Pace, Productivity Inspector (Productivity Inspector, Rounds 1 and 2). A co-pilot who reads the city's
   instruments and calls out the numbers: delighted in numbers, a bit energetic, caring mostly about productivity. She
   lives at the top of Reports (J1) and makes the city's reports, rethought in Proxima Reports, Round 1 (0.1.83):
   - one weekly report, in place of two: the side bar's This week card opens it on the week so far, Reports and her
     bubble on the week just ended, and its arrows go back to any week (the panel Your week went with it);
   - the monthly one, laid out like the weekly, over a month, with its arrows back to any month;
   - the daily one, a morning brief on today, which she brings herself on the day's first open, as she brings the
     weekly one on the week's and the monthly one on the month's, in a speech bubble with Read.
   A report opens with her line, its numbers drawn as tokens, then a table of the buildings with something in the
   period: tasks finished, added, overdue and its milestone, each row opening on what it finished (B1); the quiet ones
   fold into one line under them (0.1.84). Every count is of ticks, as in Reports.
   Her voice (V1), a compass for her lines: quick, bright and exact; short call-outs with a little cockpit talk (inbound,
   logged, on deck, copy that); real numbers said precisely, an exclamation when a number is good; she opens with the
   number and closes with the next thing to do. She never scolds or nags (Gus's job), mentions garbage, makes up or
   rounds a number, praises with empty words, or crowds a report with more than it holds.
   Her face is her portrait, on her dark sky blue (0.1.48).
   She also announces a finished milestone's street party (Celebrations, Rounds 1 and 2), with Go to it, in one of two
   lines approved word for word, picked by the milestone; while the project view is open, her bubble sits beside it. */

/* ---------- her lines ---------- */
/* A report's line (Proxima Reports, Round 1, B1): the count landed, against the period before and her usual, what came
   in against it, and the flight plan; a blank in braces is a number, drawn as a token. The party's two lines are
   word for word as approved (Celebrations, Round 2). */
const PROXIMA_LINES = {
  open: {
    weekly: ['Copy that, week logged: {n} landed.', 'Weekly report inbound! {n} landed.'],
    monthly: ['{month} is logged: {n} landed.', 'Monthly report on deck! {n} landed in {month}.'],
    weeklyLive: ['This week so far: {n} landed.'],
    monthlyLive: ['{month} so far: {n} landed.'],
  },
  quiet: { weekly: 'Quiet week: no tasks landed.', monthly: 'Quiet month: no tasks landed in {month}.',
    weeklyLive: 'This week so far: no tasks landed yet.', monthlyLive: '{month} so far: no tasks landed yet.' },
  more: "That's {diff} than the {period} before", same: 'The same as the {period} before',
  above: ', and above your usual {usual}!', below: ', under your usual {usual}.', even: ', right on your usual {usual}.', end: '.',
  in: '{added} against them: {g} more in than out.', out: '{added} against them: {g} more out than in!',
  level: '{added} against them: even.', none: '{added}, none out yet.',
  plan: 'Flight plan: {due} this {period}, {late}.', planDue: 'Flight plan: {due} this {period}.', planLate: 'Flight plan: {late}.',
  planClear: 'Flight plan: clear for the rest of the {period}!',
  daily: ['Daily brief on deck!', "Copy that, today's brief is in."],
  today: 'Today: {due}, {late}.', todayDue: 'Today: {due}.', todayLate: 'Today: {late}.', todayClear: 'Today: nothing due.',
  yday: 'Yesterday: {yday} landed.', ydayNone: 'Yesterday: no tasks landed.',
  milestone: ["Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!",
    "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!"],
};
/* The party's line with its blanks filled; counts read in the singular when they are one. */
function proximaFill(text, v) {
  return text.replace('{n} tasks', () => plural(v.n, 'task', 'tasks')).replace(/\{(\w+)\}/g, (all, k) => (v[k] == null ? all : String(v[k])));
}
/* One line from a moment's list, the same one each time for the same report. */
const proximaPick = (list, seed) => list[hashStr(seed) % list.length];
/* A number in her line is a token (B1, his note: "make the in-line numbers change like Decision-Wizard changes its
   tokens when companions talk"): its icon and its words, in her sky blue. */
const PROXIMA_TOKENS = {
  n: v => ({ k: 'tick', t: plural(v.n, 'task', 'tasks') }),
  yday: v => ({ k: 'tick', t: plural(v.yday, 'task', 'tasks') }),
  diff: v => ({ k: v.diff > 0 ? 'up' : 'down', t: Math.abs(v.diff) + (v.diff > 0 ? ' more' : ' fewer') }),
  usual: v => ({ k: 'chart', t: String(v.usual) }),
  added: v => ({ k: 'plus', t: v.added + ' added' }),
  g: v => ({ k: v.g > 0 ? 'up' : 'down', t: String(Math.abs(v.g)) }),
  due: v => ({ k: 'clock', t: v.due + ' due' }),
  late: v => ({ k: 'alert', t: v.late + ' overdue' }),
};
/* A line as parts: words, and tokens { k, t }. */
function proximaParts(text, v) {
  const out = [];
  let last = 0;
  text.replace(/\{(\w+)\}/g, (all, k, i) => {
    if (i > last) out.push(text.slice(last, i));
    out.push(PROXIMA_TOKENS[k] ? PROXIMA_TOKENS[k](v) : v[k] == null ? all : String(v[k]));
    last = i + all.length;
    return all;
  });
  if (last < text.length) out.push(text.slice(last));
  return out;
}
const proximaPlain = parts => parts.map(x => typeof x === 'string' ? x : x.t).join('');
/* Her line as nodes: a token is its pixel icon and its words. */
function proximaLineNodes(parts) {
  return parts.map(x => typeof x === 'string' ? x : h('span', { class: 'px-tok', 'data-k': x.k }, iconEl(x.k, 11, 'currentColor'), h('b', null, x.t)));
}
/* Her line for a report: what landed, against before and her usual (a period over), what came in against it, and the
   flight plan (a report that reaches today). */
function proximaLine(r) {
  const L = PROXIMA_LINES, per = r.per, seed = r.kind + per.key, out = [];
  const add = (text, v) => { if (out.length) out.push(' '); out.push(...proximaParts(text, v)); };
  if (r.kind === 'daily') {
    add(proximaPick(L.daily, seed), {});
    const v = { due: r.due.length, late: r.overdue.length, yday: r.yday };
    add(v.due && v.late ? L.today : v.due ? L.todayDue : v.late ? L.todayLate : L.todayClear, v);
    add(r.yday ? L.yday : L.ydayNone, v);
    return out;
  }
  const kind = r.kind + (per.live ? 'Live' : ''), period = r.kind === 'weekly' ? 'week' : 'month';
  const v = { n: r.n, month: monthLabel(per.from, false), period, diff: r.n - r.before, usual: r.usual, added: r.totals.added, g: r.totals.added - r.n,
    due: (r.due || []).length, late: (r.overdue || []).length };
  add(r.n ? proximaPick(L.open[kind], seed) : L.quiet[kind], v);
  if (!per.live && (r.n || r.before)) {
    const tail = r.usual == null ? L.end : r.n > r.usual ? L.above : r.n < r.usual ? L.below : L.even;
    add((v.diff ? L.more : L.same) + tail, v);
  }
  if (v.added) add(!r.n ? L.none : v.g > 0 ? L.in : v.g < 0 ? L.out : L.level, v);
  if (per.latest) add(v.due && v.late ? L.plan : v.due ? L.planDue : v.late ? L.planLate : L.planClear, v);
  return out;
}

/* ---------- her reports ---------- */
const PROXIMA_KINDS = ['daily', 'weekly', 'monthly'];
const proximaStart = (kind, ts) => kind === 'weekly' ? weekStartOf(ts) : monthStartOf(ts);
const proximaStep = (kind, ts, n) => kind === 'weekly' ? addDays(ts, 7 * n) : addMonths(ts, n);
/* The period a report is on. The daily one is on today. A weekly or monthly one is on the period starting at `from`,
   by default the last one ended; `live` while it is in progress, `latest` for that one and the one just ended, which
   reach today, so they say what is overdue, due and next. */
function proximaPeriod(kind, now = Date.now(), from = null) {
  const today = startOfDay(now);
  if (kind === 'daily') return { kind, from: today, to: addDays(today, 1), prev: addDays(today, -1), key: ymd(today), live: true, latest: true, end: addDays(today, 1) };
  const cur = proximaStart(kind, now), last = proximaStep(kind, cur, -1);
  const f = from == null ? last : Math.min(proximaStart(kind, from), cur);
  return { kind, from: f, to: proximaStep(kind, f, 1), prev: proximaStep(kind, f, -1), key: kind === 'weekly' ? ymd(f) : ymd(f).slice(0, 7),
    live: f === cur, latest: f >= last, end: proximaStep(kind, cur, 1) };
}
const PROXIMA_WORDS = {
  daily: { title: 'Daily report', short: 'Daily', ahead: 'Today', none: 'Nothing due today.' },
  weekly: { title: 'Weekly report', short: 'Weekly', ahead: 'This week', none: 'Nothing due for the rest of this week.', copy: 'Copy the week' },
  monthly: { title: 'Monthly report', short: 'Monthly', ahead: 'This month', none: 'Nothing due for the rest of this month.', copy: 'Copy the month' },
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
/* The daily report starts the day after the city does; the others once their period ends after it started. */
const proximaRelevant = per => per.kind === 'daily' ? cityStartedAt() < per.from : per.to > cityStartedAt();
/* A tick of this task: Activity cuts a line at 300 characters, so the first 290 decide. */
const sameTask = (e, t) => e.text.slice(0, 290) === String(t.text).slice(0, 290);
/* Her usual (B2): the average of the periods before this one, up to 12, from the city's first; none under two. */
function proximaUsual(kind, ticks, from) {
  const start = cityStartedAt();
  if (!isFinite(start)) return null;
  const first = proximaStart(kind, start);
  let sum = 0, k = 0;
  for (let s = proximaStep(kind, from, -1); s >= first && k < 12; s = proximaStep(kind, s, -1)) {
    const e = proximaStep(kind, s, 1);
    sum += ticks.filter(x => x.at >= s && x.at < e).length; k++;
  }
  return k >= 2 ? Math.round(sum / k * 10) / 10 : null;
}
/* The milestone a building worked on in the period (B2): the one most of its tasks finished then went to, else, in a
   report that reaches today, its current one; with its count as it stood at the period's end and how far it moved. */
function proximaMilestone(p, per) {
  const inP = at => typeof at === 'number' && at >= per.from && at < per.to;
  const tally = new Map();
  for (const t of p.todos) if (t.done && inP(t.doneAt) && t.milestoneId) tally.set(t.milestoneId, (tally.get(t.milestoneId) || 0) + 1);
  let id = null, most = 0;
  for (const m of p.milestones) if ((tally.get(m.id) || 0) > most) { most = tally.get(m.id); id = m.id; }
  if (!id && per.latest) { const g = currentGroup(p); id = g && g.ms ? g.ms.id : null; }
  const m = id ? p.milestones.find(x => x.id === id) : null;
  if (!m) return null;
  const ts = p.todos.filter(t => t.milestoneId === m.id);
  return { m, total: ts.length, done: ts.filter(t => t.done && (typeof t.doneAt !== 'number' || t.doneAt < per.to)).length, moved: ts.filter(t => t.done && inP(t.doneAt)).length };
}
/* How long a building has gone without a tick, by the period's end or today, whichever comes first. */
function proximaQuiet(last, per, now) {
  if (last == null) return 'No task finished yet';
  const days = Math.max(0, Math.floor((Math.min(per.to, now) - last) / DAY));
  return days < 14 ? 'Quiet for ' + plural(Math.max(1, days), 'day', 'days') : 'Quiet for ' + plural(Math.floor(days / 7), 'week', 'weeks');
}
const proximaTask = (p, text) => p.todos.find(t => String(t.text).slice(0, 290) === String(text).slice(0, 290)) || null;
function proximaReport(kind, now = Date.now(), from = null) {
  const per = proximaPeriod(kind, now, from), ticks = taskTicks(DB.projects, now), today = startOfDay(now);
  const inP = at => typeof at === 'number' && at >= per.from && at < per.to;
  const count = (a, b) => ticks.filter(e => e.at >= a && e.at < b).length;
  const r = { kind, per, now, label: proximaLabel(per, now), n: count(per.from, per.to), before: count(per.prev, per.from), streak: streakOf(ticks, now) };
  const late = t => { const d = parseYmd(t.due); return d != null && d < today; };
  /* what reaches today: every overdue task, the oldest first; what is due from today to the end of the day, week or
     month in progress, a repeat coming back in it too; and what is next */
  if (per.latest) {
    r.overdue = [];
    for (const p of DB.projects) for (const t of openTasks(p, now)) if (late(t)) r.overdue.push({ p, t });
    r.overdue.sort((a, b) => parseYmd(a.t.due) - parseYmd(b.t.due) || a.p.name.localeCompare(b.p.name));
    r.due = [];
    for (const p of DB.projects) for (const t of p.todos) { const d = parseYmd(t.due); if (!t.done && d != null && d >= today && d < per.end) r.due.push({ p, t }); }
    r.due.sort((a, b) => parseYmd(a.t.due) - parseYmd(b.t.due) || a.p.name.localeCompare(b.p.name));
  }
  const nextOf = p => { const t = bubbleTodos(p, 1).list[0]; return t ? { p, t } : null; };
  if (kind === 'daily') {
    /* the morning brief (C1): today, what is next in each busy building (a tick in the last 7 days, the latest
       first), and yesterday as one line */
    const yday = ticks.filter(e => e.at >= per.prev && e.at < per.from);
    r.yday = yday.length;
    r.ydayIn = [...new Set(yday.map(e => e.p))];
    const last = new Map();
    for (const e of ticks) if (e.at >= addDays(today, -7) && e.at < now) last.set(e.p, e.at);
    r.next = [...last.entries()].sort((a, b) => b[1] - a[1]).map(([p]) => nextOf(p)).filter(Boolean);
    r.parts = proximaLine(r);
    r.line = proximaPlain(r.parts);
    return r;
  }
  r.usual = proximaUsual(kind, ticks, per.from);
  const finished = milestonesFinished(DB.projects).filter(x => inP(x.at)).reverse();
  r.milestones = finished;
  const lastTick = new Map();
  for (const e of ticks) if (e.at < per.to) lastTick.set(e.p, e.at);
  /* every building (A1: "every building will show"), the most finished first */
  r.rows = DB.projects.map(p => {
    const log = (p.activity || []).filter(e => inP(e.at));
    const done = ticks.filter(e => e.p === p && inP(e.at)).map(e => ({ text: e.text, at: e.at, t: proximaTask(p, e.text) }));
    const open = openTasks(p, now);
    const row = { p, n: done.length, done,
      added: log.map(e => ({ text: addedTodo(e.text), at: e.at })).filter(e => e.text != null),
      notes: allNotes(p).filter(n => inP(n.at)).sort((a, b) => a.at - b.at),
      worked: log.filter(e => e.text === 'I worked!').length,
      planted: inP(p.createdAt), ms: finished.filter(x => x.p === p),
      late: per.latest ? open.filter(late).length : 0, open: open.length, mile: proximaMilestone(p, per) };
    row.quiet = row.n ? null : per.latest && !row.open ? 'Nothing open' : proximaQuiet(lastTick.has(p) ? lastTick.get(p) : null, per, now);
    /* nothing in the period: no tick, nothing added, no note or check-in, not planted; the table folds these into one
       line (0.1.84: "I don't like that the report have bunch of 0 buildings") */
    row.idle = !(row.n || row.added.length || row.notes.length || row.worked || row.planted || row.ms.length);
    return row;
  }).sort((a, b) => b.n - a.n || b.added.length - a.added.length || a.p.name.localeCompare(b.p.name));
  r.totals = { n: r.n, added: r.rows.reduce((s, x) => s + x.added.length, 0), notes: r.rows.reduce((s, x) => s + x.notes.length, 0),
    worked: r.rows.reduce((s, x) => s + x.worked, 0), late: r.rows.reduce((s, x) => s + x.late, 0) };
  /* what is next: each building's next task; Next up holds those with something in the period, and the quiet ones'
     go with them in their folded line */
  if (per.latest) { for (const x of r.rows) x.next = nextOf(x.p); r.next = r.rows.filter(x => !x.idle && x.next).map(x => x.next); }
  if (kind === 'monthly') {
    /* what only a month shows (C2): repeats kept up */
    r.repeats = [];
    for (const p of DB.projects) for (const t of p.todos) {
      if (!t.repeat) continue;
      const k = ticks.filter(e => e.p === p && sameTask(e, t) && inP(e.at)).length;
      if (k) r.repeats.push({ p, t, k });
    }
    r.repeats.sort((a, b) => b.k - a.k || a.t.text.localeCompare(b.t.text));
  }
  r.parts = proximaLine(r);
  r.line = proximaPlain(r.parts);
  return r;
}
/* A weekly or monthly report as text, for Claude or Slack (A2, Copy the week). */
function proximaText(r) {
  const what = r.kind === 'weekly' ? 'week of ' + weekLabel(r.per.from, true) : monthLabel(r.per.from);
  const L = ['# Nullovation City, ' + what + (r.per.live ? ', so far' : ''), r.line];
  const s = r.streak;
  L.push('Streak: ' + plural(s.n, 'day', 'days') + ', the longest ' + plural(s.best.n, 'day', 'days') + '.');
  for (const x of r.rows.filter(x => !x.idle)) {
    L.push('', '## ' + x.p.name);
    const nums = [x.n + ' finished', x.added.length + ' added', x.notes.length ? plural(x.notes.length, 'note', 'notes') : null,
      x.worked ? plural(x.worked, 'I worked! check-in', 'I worked! check-ins') : null].filter(Boolean);
    L.push(nums.join(', ') + '.' + (x.planted ? ' Planted.' : ''));
    if (x.mile) L.push('Milestone: ' + x.mile.m.name + ', ' + x.mile.done + ' of ' + x.mile.total + (x.mile.moved ? ', ' + x.mile.moved + ' this ' + (r.kind === 'weekly' ? 'week' : 'month') : '') + '.');
    if (x.done.length) { L.push('Finished:'); for (const d of x.done) L.push('- ' + d.text); }
    if (x.ms.length) { L.push('Milestones finished:'); for (const m of x.ms) L.push('- ' + m.m.name); }
  }
  const quiet = r.rows.filter(x => x.idle);
  if (quiet.length) L.push('', 'Quiet buildings: ' + quiet.map(x => x.p.name + ' (' + x.quiet.toLowerCase() + (x.late ? ', ' + x.late + ' overdue' : '') + ')').join(', ') + '.');
  if (r.overdue && r.overdue.length) { L.push('', 'Overdue:'); for (const x of r.overdue) L.push('- ' + x.t.text + ' (' + x.p.name + ', ' + dueInfo(x.t, r.now).text.toLowerCase() + ')'); }
  if (r.due && r.due.length) { L.push('', PROXIMA_WORDS[r.kind].ahead + ':'); for (const x of r.due) L.push('- ' + x.t.text + ' (' + x.p.name + ', ' + weekdayOf(x.t.due) + ' ' + dayMonth(parseYmd(x.t.due)) + ')'); }
  if (r.repeats && r.repeats.length) { L.push('', 'Repeats kept up:'); for (const x of r.repeats) L.push('- ' + x.t.text + ': ' + plural(x.k, 'time', 'times')); }
  return L.join('\n');
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
      h('p', { id: 'pxLine', class: 'gus-line px-line' }, lead ? proximaLineNodes(proximaReport(lead.kind, now).parts) : 'Her first report comes tomorrow.'),
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
  let shownKind = null, shownFrom = null, body = null, openRows = new Set(), openNotes = new Set(), openQuiet = false;
  /* Opens a report: the daily one on today; a weekly or monthly one on the period starting at `from`, by default the
     last one ended, which is the one she brings and the one her card's tile marks read. */
  function openReport(kind, from = null) {
    shownKind = kind; shownFrom = from; openRows = new Set(); openNotes = new Set(); openQuiet = false;
    body = h('div', { class: 'px-report', 'data-kind': kind });
    Panel.open(PROXIMA_WORDS[kind].title, body, 'px-panel');
    draw();
    pump();                                                // the next one she has waits until this one is closed
  }
  /* Draws the report open, keeping the focus on the control that had it. */
  function draw() {
    if (!body || !document.contains(body)) return;
    const a = document.activeElement, key = a && body.contains(a) ? a.dataset.k : null;
    const now = Date.now(), kind = shownKind, r = proximaReport(kind, now, shownFrom), w = PROXIMA_WORDS[kind];
    shownFrom = kind === 'daily' ? null : r.per.from;
    if (r.per.key === proximaPeriod(kind, now).key) {      // the report on her card: read now, and nothing left to bring
      state.read[kind] = r.per.key; state.spoke[kind] = r.per.key; save();
      queue = queue.filter(k => k !== kind);
      if (saying && saying.kind === kind) hush(false);
      renderDot(); if (typeof Reports !== 'undefined') Reports.refresh();
    }
    body.dataset.from = String(r.per.from);
    body.replaceChildren(
      h('div', { class: 'px-says' }, face(), h('div', { class: 'px-says-body' }, nameTag(), h('p', { id: 'pxReportLine', class: 'px-quote' }, proximaLineNodes(r.parts)))),
      kind === 'daily' ? h('p', { class: 'px-when' }, r.label + ', today') : nav(r, now),
      ...[kind === 'daily' ? dailyBody(r, now) : periodBody(r, now)].flat(Infinity).filter(x => x != null && x !== false));
    if (key) { const b = body.querySelector(`[data-k="${CSS.escape(key)}"]`); if (b) b.focus({ preventScroll: true }); }
  }
  const goP = p => () => { Panel.close(); Menu.closeDrawer(); MapView.select(p.id); };
  const goT = (p, t) => () => { Panel.close(); FullView.openTask(p.id, t.id); };
  const sec = (title, ...kids) => h('section', { class: 'px-sec' }, h('h4', null, title), ...kids);
  const list = (items, attrs = {}) => h('ul', Object.assign({ class: 'px-list' }, attrs), items);
  const thumb = p => h('span', { class: 'px-thumb', 'aria-hidden': 'true' }, MapView.thumb(p));
  const projTag = p => h('span', { class: 'px-proj', dir: 'auto' }, p.name);
  const taskRow = (x, extra) => h('li', null, extra, h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goT(x.p, x.t) }, x.t.text), projTag(x.p));
  const dueChip = (x, now) => { const d = dueInfo(x.t, now); return h('span', { class: 'recap-day' + (d && d.tone ? ' ' + d.tone : '') }, weekdayOf(x.t.due) + ' ' + dayMonth(parseYmd(x.t.due))); };
  const lateChip = (x, now) => h('span', { class: 'recap-day late' }, dueInfo(x.t, now).text);
  function streakSec(r) {
    const s = r.streak;
    return sec('Streak', h('p', { id: 'pxStreak' }, iconEl('flame', 14), ' ', s.n ? plural(s.n, 'day', 'days') + (s.n >= s.best.n ? ', the longest.' : ', ' + (s.best.n - s.n) + ' short of the longest, ' + plural(s.best.n, 'day', 'days') + '.')
      : 'None now. The longest: ' + plural(s.best.n, 'day', 'days') + '.'));
  }
  function overdueSec(r, now) {
    return sec('Overdue', r.overdue.length ? list(r.overdue.map(x => taskRow(x, lateChip(x, now))), { id: 'pxOverdue' }) : h('p', { id: 'pxOverdue', class: 'px-none' }, 'Nothing overdue.'));
  }
  function aheadSec(r, now) {
    const w = PROXIMA_WORDS[r.kind];
    return sec(w.ahead, r.due.length ? list(r.due.map(x => taskRow(x, dueChip(x, now))), { id: 'pxDue' }) : h('p', { id: 'pxDue', class: 'px-none' }, w.none));
  }
  /* What is next (B2): each building's next task, the one its status card puts first. */
  function nextSec(r) {
    return r.next.length ? sec('Next up', list(r.next.map(x => h('li', null, h('button', { class: 'px-bname-link', type: 'button', dir: 'auto', onclick: goP(x.p) }, x.p.name),
      h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goT(x.p, x.t) }, x.t.text))), { id: 'pxNext', class: 'px-list px-next' })) : null;
  }
  /* The arrows and the list: back to the first week or month with a record, on to the one in progress. */
  function nav(r, now) {
    const kind = r.kind, cur = proximaStart(kind, now), start = cityStartedAt();
    const first = Math.min(cur, isFinite(start) ? proximaStart(kind, start) : cur);
    const all = [];
    for (let s = cur; s >= first; s = proximaStep(kind, s, -1)) all.push(s);
    const name = s => (kind === 'weekly' ? weekLabel(s) : monthLabel(s, new Date(s).getFullYear() !== new Date(now).getFullYear())) + (s === cur ? (kind === 'weekly' ? ' (this week)' : ' (this month)') : '');
    const unit = kind === 'weekly' ? 'week' : 'month', go = s => { shownFrom = s; openRows = new Set(); openNotes = new Set(); openQuiet = false; draw(); };
    return h('div', { class: 'px-nav' },
      h('button', { class: 'icon-btn', type: 'button', 'data-k': 'prev', 'aria-label': 'The ' + unit + ' before', title: 'The ' + unit + ' before', html: iconSvg('caretR', 10),
        style: 'transform: scaleX(-1)', disabled: r.per.from <= first, onclick: () => go(proximaStep(kind, r.per.from, -1)) }),
      h('h3', { id: 'pxWhen', class: 'px-when' }, (kind === 'weekly' ? weekLabel(r.per.from, true) : monthLabel(r.per.from)) + (r.per.live ? ', so far' : '')),
      h('button', { class: 'icon-btn', type: 'button', 'data-k': 'next', 'aria-label': 'The ' + unit + ' after', title: 'The ' + unit + ' after', html: iconSvg('caretR', 10),
        disabled: r.per.live, onclick: () => go(proximaStep(kind, r.per.from, 1)) }),
      h('select', { id: 'pxPick', class: 'field px-pick', 'data-k': 'pick', 'aria-label': kind === 'weekly' ? 'Every week' : 'Every month', onchange: e => go(Number(e.target.value)) },
        all.map(s => h('option', { value: String(s), selected: s === r.per.from }, name(s)))));
  }
  /* The table of buildings (B1): every building with something in the period, the most finished first, a row opening
     on what it finished (A1); the quiet ones, with nothing in it, folded into one line under them (0.1.84). */
  function table(r, now) {
    const unit = r.kind === 'weekly' ? 'week' : 'month', lateCol = r.per.latest;
    const cls = 'px-bgrid' + (lateCol ? ' with-late' : '');
    const head = h('div', { class: cls + ' px-bhead', 'aria-hidden': 'true' }, h('span', null, 'Building'), h('span', { class: 'px-num' }, 'Finished'), h('span', { class: 'px-num' }, 'Added'),
      lateCol ? h('span', { class: 'px-num' }, 'Overdue') : null, h('span', null, 'Milestone'));
    const mileCell = x => x.mile ? h('span', { class: 'px-mile', dir: 'auto', title: x.mile.m.name + ': ' + x.mile.done + ' of ' + x.mile.total + ' done' + (x.mile.moved ? ', ' + x.mile.moved + ' this ' + unit : '') },
      h('span', { class: 'px-mile-name' }, x.mile.m.name), h('span', { class: 'px-mile-n' }, x.mile.done + ' of ' + x.mile.total), x.mile.moved ? h('b', { class: 'px-mile-up' }, '+' + x.mile.moved) : null) : h('span', { class: 'px-mile px-none' }, '');
    const active = r.rows.filter(x => !x.idle), idle = r.rows.filter(x => x.idle);
    const rows = active.map(x => {
      const id = x.p.id, opens = !!(x.done.length || x.ms.length || x.notes.length || x.worked || x.planted), on = opens && openRows.has(id);
      const sub = [x.quiet, x.planted ? 'Planted this ' + unit : null, x.notes.length ? plural(x.notes.length, 'note', 'notes') : null, x.worked ? plural(x.worked, 'I worked! check-in', 'I worked! check-ins') : null].filter(Boolean).join(' · ');
      const cells = [
        h('span', { class: 'px-bname' }, opens ? h('span', { class: 'px-caret', 'aria-hidden': 'true', html: iconSvg('caretR', 8) }) : h('span', { class: 'px-caret' }), thumb(x.p),
          h('span', { class: 'px-bname-body' }, h('span', { class: 'px-bname-top' }, h('span', { class: 'px-bname-text', dir: 'auto' }, x.p.name), News.reportFace(x.p, 20)),
            sub ? h('span', { class: 'px-bsub' }, sub) : null)),
        h('b', { class: 'px-num' + (x.n ? '' : ' zero') }, String(x.n)), h('span', { class: 'px-num' + (x.added.length ? '' : ' zero') }, String(x.added.length)),
        lateCol ? h('span', { class: 'px-num' + (x.late ? ' late' : ' zero') }, String(x.late)) : null, mileCell(x)];
      const words = x.p.name + ': ' + plural(x.n, 'task', 'tasks') + ' finished, ' + x.added.length + ' added' + (lateCol ? ', ' + x.late + ' overdue' : '') + (x.quiet ? '. ' + x.quiet : '');
      const rowEl = opens ? h('button', { class: cls + ' px-brow', type: 'button', 'data-k': 'b-' + id, 'data-id': id, 'aria-expanded': String(on), 'aria-label': words, title: on ? 'Fold it' : 'Show what it finished',
        onclick: () => { if (openRows.has(id)) openRows.delete(id); else openRows.add(id); draw(); } }, cells)
        : h('div', { class: cls + ' px-brow still', 'data-id': id, 'aria-label': words, role: 'group' }, cells);
      return h('li', { class: 'px-bitem' + (on ? ' open' : '') }, rowEl, on ? detail(x, r) : null);
    });
    if (idle.length) rows.push(quietLine(idle, unit));
    const t = r.totals;
    const foot = h('div', { class: cls + ' px-bfoot' }, h('span', null, 'All buildings'), h('b', { class: 'px-num' }, String(t.n)), h('b', { class: 'px-num' }, String(t.added)),
      lateCol ? h('b', { class: 'px-num' + (t.late ? ' late' : '') }, String(t.late)) : null, h('span', null, ''));
    return h('section', { class: 'px-sec px-buildings' }, h('h4', null, 'Buildings'), active.length ? head : null, h('ul', { id: 'pxBuildings', class: 'px-blist' }, rows), foot);
  }
  /* The quiet buildings in one line, folded: opened, each with how long it has been quiet, its overdue tasks, and in a
     report that reaches today its next task; its name shows it on the map. */
  function quietLine(idle, unit) {
    const late = idle.reduce((s, x) => s + x.late, 0);
    const sub = 'Nothing finished or added this ' + unit + (late ? ' · ' + plural(late, 'overdue task', 'overdue tasks') : '');
    return h('li', { class: 'px-bitem px-qitem' + (openQuiet ? ' open' : '') },
      h('button', { class: 'px-qrow', type: 'button', 'data-k': 'quiet', 'aria-expanded': String(openQuiet), title: openQuiet ? 'Fold them' : 'Show them',
        onclick: () => { openQuiet = !openQuiet; draw(); } },
        h('span', { class: 'px-caret', 'aria-hidden': 'true', html: iconSvg('caretR', 8) }),
        h('span', { class: 'px-bname-body' }, h('span', { class: 'px-qname' }, plural(idle.length, 'quiet building', 'quiet buildings')), h('span', { class: 'px-bsub' }, sub))),
      openQuiet ? list(idle.map(x => h('li', { 'data-id': x.p.id }, thumb(x.p),
        h('span', { class: 'px-qwho' }, h('button', { class: 'px-bname-link', type: 'button', dir: 'auto', title: 'Show it on the map', onclick: goP(x.p) }, x.p.name),
          h('span', { class: 'px-bsub' }, x.quiet, x.late ? h('span', { class: 'px-qlate' }, ' · ' + x.late + ' overdue') : null)),
        x.next ? h('button', { class: 'px-link', type: 'button', dir: 'auto', title: 'Its next task', onclick: goT(x.p, x.next.t) }, x.next.t.text) : null)), { id: 'pxQuiet', class: 'px-list px-qlist' }) : null);
  }
  /* A building's row, opened: what it finished, by day, its milestones finished, its notes (a count that opens on
     them, A2), its I worked! check-ins, and planted. */
  function detail(x, r) {
    const day = at => new Date(at).toLocaleDateString('en-GB', r.kind === 'weekly' ? { weekday: 'short' } : { day: 'numeric', month: 'short' });
    const nOpen = openNotes.has(x.p.id);
    return h('div', { class: 'px-bdetail', 'data-id': x.p.id },
      x.done.length ? h('div', { class: 'px-dgroup' }, h('h5', null, 'Finished'), list(x.done.map(d => h('li', null, h('span', { class: 'recap-day' }, day(d.at)),
        d.t ? h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goT(x.p, d.t) }, d.text) : h('span', { dir: 'auto' }, d.text))))) : null,
      x.ms.length ? h('div', { class: 'px-dgroup' }, h('h5', null, 'Milestones finished'), list(x.ms.map(m => h('li', null, h('span', { class: 'recap-day' }, dayMonth(m.at)),
        h('span', { dir: 'auto' }, iconEl('flag', 11), ' ', m.m.name))))) : null,
      x.notes.length ? h('div', { class: 'px-dgroup' },
        h('button', { class: 'px-fold', type: 'button', 'data-k': 'notes-' + x.p.id, 'aria-expanded': String(nOpen), onclick: () => { if (nOpen) openNotes.delete(x.p.id); else openNotes.add(x.p.id); draw(); } },
          h('span', { class: 'px-caret', 'aria-hidden': 'true', html: iconSvg('caretR', 8) }), plural(x.notes.length, 'note', 'notes')),
        nOpen ? list(x.notes.map(n => h('li', null, h('span', { class: 'recap-day' }, day(n.at)),
          h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: () => { Panel.close(); FullView.openNote(x.p.id, n.id); } }, (n.title || '').trim() || n.text.replace(/\s+/g, ' ').trim().slice(0, 80) || 'Untitled note'))), { class: 'px-list px-notes' }) : null) : null,
      x.worked ? h('p', { class: 'px-dline' }, 'I worked!: ' + plural(x.worked, 'check-in', 'check-ins') + '.') : null,
      x.planted ? h('p', { class: 'px-dline' }, 'Planted this ' + (r.kind === 'weekly' ? 'week' : 'month') + '.') : null,
      h('button', { class: 'btn btn-quiet btn-small px-go', type: 'button', onclick: goP(x.p) }, 'Show it on the map'));
  }
  function periodBody(r, now) {
    const w = PROXIMA_WORDS[r.kind];
    return [
      streakSec(r),
      table(r, now),
      sec('Milestones finished', r.milestones.length ? list(r.milestones.map(x => h('li', null, h('span', { class: 'recap-day' }, fmtDate(x.at)),
        h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: () => { Panel.close(); FullView.open(x.p.id); } }, x.m.name),
        h('span', { class: 'px-mproj' }, thumb(x.p), h('span', { dir: 'auto' }, x.p.name)))), { id: 'pxMilestones' }) : h('p', { id: 'pxMilestones', class: 'px-none' }, 'None.')),
      r.kind === 'monthly' && r.repeats.length ? sec('Repeats kept up', list(r.repeats.map(x => h('li', null, h('button', { class: 'px-link', type: 'button', dir: 'auto', onclick: goT(x.p, x.t) }, x.t.text),
        h('span', { class: 'px-proj' }, plural(x.k, 'time', 'times')))))) : null,
      r.per.latest ? [overdueSec(r, now), aheadSec(r, now), nextSec(r)] : null,
      h('div', { class: 'px-foot' }, h('button', { class: 'btn', type: 'button', 'data-k': 'copy', onclick: async () => {
        if (await copyText(proximaText(r))) toast((r.kind === 'weekly' ? 'Week' : 'Month') + ' copied. Paste it into Claude or Slack.'); else toast('The browser blocked copying. Try again.', 'error');
      } }, iconEl('copy', 14), w.copy)),
    ];
  }
  /* The morning brief (C1): today, overdue, next up in each busy building, yesterday in one line, and the streak. */
  function dailyBody(r, now) {
    const names = r.ydayIn.map(p => p.name);
    const yline = r.yday ? plural(r.yday, 'task', 'tasks') + ' landed, in ' + (names.length > 3 ? names.slice(0, 3).join(', ') + ' and ' + (names.length - 3) + ' more' : names.length > 1 ? names.slice(0, -1).join(', ') + ' and ' + names[names.length - 1] : names[0]) + '.'
      : 'No tasks landed.';
    return [
      aheadSec(r, now),
      overdueSec(r, now),
      nextSec(r),
      sec('Yesterday', h('p', { id: 'pxYesterday' }, h('span', { class: 'recap-day' }, weekdayOf(ymd(r.per.prev)) + ' ' + dayMonth(r.per.prev)), ' ', yline)),
      streakSec(r),
    ];
  }

  /* ---------- speaking: the weekly, monthly and daily reports, after Gus ---------- */
  function check(now = Date.now()) {
    if (!started) return;
    for (const kind of ['weekly', 'monthly', 'daily']) {
      const per = proximaPeriod(kind, now);
      if (!proximaRelevant(per) || state.spoke[kind] === per.key || queue.includes(kind) || (saying && saying.kind === kind)) continue;
      queue.push(kind);
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
    $('#pxSayText').replaceChildren(...(party ? [r.line] : proximaLineNodes(r.parts)));
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
    busy: () => !!saying || queue.length > 0, redraw: () => draw(),
    _test: { sayMs: ms => { sayMs = ms; }, state: () => JSON.parse(JSON.stringify(state)), forget: () => { state = { read: {}, spoke: {} }; save(); queue = []; }, queue: () => [...queue] } };
})();
