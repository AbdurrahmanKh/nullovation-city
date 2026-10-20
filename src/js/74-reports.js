/* Reports, from the fourth of the task ideas (Tasks, Round 2, P1 to P3). The side bar turns into Reports as it does into
   Settings, with two tabs:
   - Weeks: tasks finished each week for the last 12 weeks, and by project for a week or a month;
   - Records: the streak and its longest, the busiest building of each month, and milestones finished with their dates.
   Every count is of ticks: Activity's Done lines, so a repeat counts each time it is ticked. The weekly review (V2 to V4),
   built at 0.1.43 as a third tab, was taken out at 0.1.44: tasks are managed in the city, not in the side bar. */

/* ---------- the counts ---------- */
const REPORT_WEEKS = 12;
/* Every tick in the city, oldest first: { at, day, p, text }. The Done lines in each project's Activity, less those a
   Reopened line took back; a done task whose Done line the log no longer holds (it keeps 400 lines) counts on the day
   it was finished. */
function taskTicks(projects = DB.projects, now = Date.now()) {
  const same = (a, b) => a.slice(0, 290) === b.slice(0, 290);          // Activity cuts a line at 300 characters
  const out = [];
  for (const p of projects) {
    const got = [];
    for (const e of [...(p.activity || [])].sort((a, b) => a.at - b.at)) {
      if (e.text.startsWith('Done: ')) got.push({ at: e.at, text: e.text.slice(6) });
      else if (e.text.startsWith('Reopened: ')) {
        const s = e.text.slice(10);
        for (let i = got.length - 1; i >= 0; i--) if (same(got[i].text, s)) { got.splice(i, 1); break; }
      }
    }
    for (const t of p.todos) {
      if (!t.done || typeof t.doneAt !== 'number') continue;
      if (!got.some(e => same(e.text, String(t.text)) && Math.abs(e.at - t.doneAt) < 36 * HOUR)) got.push({ at: t.doneAt, text: String(t.text) });
    }
    for (const e of got) if (e.at <= now) out.push({ at: e.at, day: ymd(e.at), p, text: e.text });
  }
  return out.sort((a, b) => a.at - b.at);
}
const monthStartOf = ts => { const d = new Date(ts); return new Date(d.getFullYear(), d.getMonth(), 1).getTime(); };
const addMonths = (ts, n) => { const d = new Date(ts); return new Date(d.getFullYear(), d.getMonth() + n, 1).getTime(); };
const monthLabel = (ts, withYear = true) => new Date(ts).toLocaleDateString('en-GB', withYear ? { month: 'long', year: 'numeric' } : { month: 'long' });
const dayMonth = ts => new Date(ts).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
/* Tasks finished in each of the last n weeks, Saturday to Friday, oldest first; the last one is this week so far. */
function weeklyTicks(ticks, n = REPORT_WEEKS, now = Date.now()) {
  const cur = weekStartOf(now);
  return Array.from({ length: n }, (_, k) => {
    const start = addDays(cur, -7 * (n - 1 - k)), end = addDays(start, 7);
    return { start, n: ticks.filter(e => e.at >= start && e.at < end).length, current: start === cur };
  });
}
/* Tasks finished by project between two moments, the most first. */
function ticksByProject(ticks, from, to) {
  const m = new Map();
  for (const e of ticks) if (e.at >= from && e.at < to) m.set(e.p, (m.get(e.p) || 0) + 1);
  return [...m.entries()].map(([p, n]) => ({ p, n })).sort((a, b) => b.n - a.n || a.p.name.localeCompare(b.p.name));
}
/* The streak: days in a row with a task finished (P2). Rest days and days away never break it (P3): one with no tick
   is passed over, one with a tick counts. Today does not break it before its first tick either. */
function streakOf(ticks, now = Date.now(), city = DB.city || {}) {
  const days = new Set(ticks.map(e => e.day)), today = ymd(now);
  const rest = new Set(city.rest || []), spans = city.awaySpans || [];
  const off = s => rest.has(new Date(parseYmd(s)).getDay()) || spans.some(([f, b]) => f <= s && s < b);
  let n = 0, from = null, to = null, best = { n: 0, from: null, to: null };
  const first = [...days].sort()[0];
  if (first) for (let d = parseYmd(first); ymd(d) <= today; d = addDays(d, 1)) {
    const s = ymd(d);
    if (days.has(s)) { if (!n) from = s; n++; to = s; if (n > best.n) best = { n, from, to }; }
    else if (!off(s) && s !== today) { n = 0; from = to = null; }
  }
  return { n, from, to, today: days.has(today), off: off(today), best };
}
/* The busiest building of each month, by its ticks: this month first, then each earlier month with a tick, at most n.
   Buildings tied at the top share it. */
function busiestByMonth(ticks, n = 12, now = Date.now()) {
  const out = [], cur = monthStartOf(now);
  if (!ticks.length) return [{ start: cur, top: [], n: 0 }];
  for (let m = cur, first = monthStartOf(ticks[0].at); m >= first && out.length < n; m = addMonths(m, -1)) {
    const rows = ticksByProject(ticks, m, addMonths(m, 1));
    if (!rows.length && m !== cur) continue;
    out.push({ start: m, top: rows.filter(r => r.n === rows[0].n), n: rows.length ? rows[0].n : 0 });
  }
  return out;
}
/* Milestones finished, newest first: every task in them done, on the day the last one was. A milestone with a repeat
   in it never finishes. */
function milestonesFinished(projects = DB.projects) {
  const out = [];
  for (const p of projects) for (const m of p.milestones) {
    const ts = p.todos.filter(t => t.milestoneId === m.id);
    if (!ts.length || !ts.every(t => t.done)) continue;
    const at = Math.max(...ts.map(t => t.doneAt || 0));
    if (at > 0) out.push({ p, m, at });
  }
  return out.sort((a, b) => b.at - a.at);
}

const Reports = (() => {
  const UI_KEY = 'nullovation-city:reports';
  const TABS = [{ id: 'weeks', label: 'Weeks', icon: 'chart' }, { id: 'records', label: 'Records', icon: 'trophy' }];
  let ui = (() => { try { const v = JSON.parse(localStorage.getItem(UI_KEY) || 'null'); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } })();
  if (!TABS.some(t => t.id === ui.tab)) ui.tab = 'weeks';
  if (ui.period !== 'month') ui.period = 'week';
  const saveUi = () => { try { localStorage.setItem(UI_KEY, JSON.stringify({ tab: ui.tab, period: ui.period })); } catch (e) { /* this visit only */ } };
  let at = null;                                           // the week or month By project shows; null is the current one
  const MILESTONES_SHOWN = 8;
  let allMilestones = false;

  const isOpen = () => !!$('#reports') && !$('#reports').hidden;
  function open(tab) {
    if (tab && TABS.some(t => t.id === tab)) ui.tab = tab;
    if (typeof Settings !== 'undefined') Settings.close(false);
    if (typeof AllTasks !== 'undefined') AllTasks.close(false);
    Menu.toggleDrawer(true);
    $('#sbLists').hidden = true; $('#reports').hidden = false;
    $('#menu').classList.add('in-reports');
    $('#menu').scrollTop = 0;
    render();
    saveUi();
    const btn = $('#rpTabs [aria-selected="true"]'); if (btn) btn.focus({ preventScroll: true });
  }
  function close(refocus = true) {
    if (!isOpen()) return false;
    $('#reports').hidden = true;
    if ((!$('#settings') || $('#settings').hidden) && (!$('#allTasks') || $('#allTasks').hidden)) $('#sbLists').hidden = false;
    $('#menu').classList.remove('in-reports');
    if (refocus) $('#btnOpenReports').focus({ preventScroll: true });
    return true;
  }
  const toggle = () => { if (isOpen()) close(); else open(); };
  function showTab(id) {
    if (id === ui.tab) return;
    ui.tab = id; saveUi();
    $('#menu').scrollTop = 0;
    render();
  }

  /* ---------- drawing ---------- */
  /* Redraws the open tab, keeping the focus on the control that had it and the side bar where it was. */
  function render() {
    if (!isOpen()) return;
    const a = document.activeElement, key = a && $('#reports').contains(a) ? a.dataset.k : null, top = $('#menu').scrollTop;
    const place = key ? $$('#reports [data-k]').indexOf(a) : -1;
    for (const b of $$('#rpTabs .set-tab')) { const on = b.dataset.tab === ui.tab; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; }
    const now = Date.now(), ticks = taskTicks(DB.projects, now);
    const page = ui.tab === 'weeks' ? weeksPage(ticks, now) : recordsPage(ticks, now);
    $('#rpBody').replaceChildren(h('div', { class: 'set-page rp-page', 'data-tab': ui.tab, role: 'tabpanel', 'aria-label': TABS.find(t => t.id === ui.tab).label }, page));
    if (typeof Proxima !== 'undefined') Proxima.renderCard();    // the Productivity Inspector, at the top
    $('#menu').scrollTop = top;
    if (key) {                                             // the same control, or the one now in its place when it went
      const all = $$('#reports [data-k]'), b = $(`#reports [data-k="${CSS.escape(key)}"]`) || all[Math.min(place, all.length - 1)];
      if (b) b.focus({ preventScroll: true });
    }
  }
  /* From the map: another change in the city redraws the open tab. */
  function refresh() { if (isOpen()) render(); }
  const group = (title, ...kids) => h('section', { class: 'set-group rp-group' }, h('h3', { class: 'set-h' }, title), ...kids);
  const note = text => h('p', { class: 'note' }, text);
  const thumb = p => h('span', { class: 'rp-thumb', 'aria-hidden': 'true' }, MapView.thumb(p));
  const goTo = p => { Menu.closeDrawer(); MapView.select(p.id); };

  /* Weeks: the last 12 weeks, then by project for a week or a month. */
  function weeksPage(ticks, now) {
    const weeks = weeklyTicks(ticks, REPORT_WEEKS, now), max = Math.max(1, ...weeks.map(w => w.n));
    const total = weeks.reduce((s, w) => s + w.n, 0), cur = weeks[weeks.length - 1];
    const span = period(ticks, now);
    const sel = ui.period === 'week' ? span.from : null;
    const chart = h('div', { class: 'rp-chart', role: 'group', 'aria-label': 'Tasks finished each week, the last 12 weeks' },
      weeks.map(w => {
        const words = weekLabel(w.start) + (w.current ? ', so far' : '') + ': ' + plural(w.n, 'task', 'tasks');
        return h('button', { class: 'rp-bar' + (w.current ? ' now' : ''), type: 'button', 'data-k': 'bar' + w.start, 'data-week': String(w.start), 'aria-pressed': String(sel === w.start),
          title: words + '. Show it by project.', 'aria-label': words, onclick: () => { ui.period = 'week'; at = w.start; saveUi(); render(); } },
          h('b', null, w.n ? String(w.n) : ''), h('i', { style: 'height:' + (w.n ? Math.max(4, Math.round(w.n / max * 72)) : 2) + 'px' }));
      }));
    const axis = h('div', { class: 'rp-axis', 'aria-hidden': 'true' }, [0, 4, 8].map(k => h('span', { style: 'grid-column: ' + (k + 1) + ' / span 4' }, dayMonth(weeks[k].start))));
    const rows = ticksByProject(ticks, span.from, span.to), top = Math.max(1, ...rows.map(r => r.n));
    const kinds = [{ value: 'week', label: 'Week' }, { value: 'month', label: 'Month' }];
    return [
      group('Tasks finished each week',
        h('p', { id: 'rpWeeksSum', class: 'rp-sum' }, 'This week so far: ', h('b', null, String(cur.n)), '. The last 12 weeks: ', h('b', null, String(total)),
          total ? ', about ' + (Math.round(total / REPORT_WEEKS * 10) / 10) + ' a week.' : '.'),
        chart, axis,
        note('Weeks run Saturday to Friday. Pick a week to see it by project.')),
      group('By project',
        h('div', { class: 'set-choices rp-kinds' }, kinds.map(k => h('button', { class: 'btn set-choice', type: 'button', 'data-k': 'kind-' + k.value, 'data-value': k.value,
          'aria-pressed': String(ui.period === k.value), onclick: () => { if (ui.period === k.value) return; ui.period = k.value; at = null; saveUi(); render(); } }, k.label))),
        h('div', { class: 'rp-nav' },
          h('button', { class: 'icon-btn', type: 'button', 'data-k': 'prev', 'aria-label': 'The ' + ui.period + ' before', title: 'The ' + ui.period + ' before', html: iconSvg('caretR', 10),
            style: 'transform: scaleX(-1)', disabled: !span.prev, onclick: () => { at = span.prev; render(); } }),
          h('span', { id: 'rpPeriod', class: 'rp-when' }, span.label),
          h('button', { class: 'icon-btn', type: 'button', 'data-k': 'next', 'aria-label': 'The ' + ui.period + ' after', title: 'The ' + ui.period + ' after', html: iconSvg('caretR', 10),
            disabled: !span.next, onclick: () => { at = span.next; render(); } })),
        rows.length ? h('ul', { id: 'rpByProject', class: 'rp-rows' }, rows.map(r => h('li', null,
          h('button', { class: 'rp-row', type: 'button', 'data-k': 'proj-' + r.p.id, title: 'Show ' + r.p.name + ' on the map', onclick: () => goTo(r.p) },
            thumb(r.p),
            h('span', { class: 'rp-row-body' },
              h('span', { class: 'rp-row-top' }, h('span', { class: 'rp-name', dir: 'auto' }, r.p.name), h('b', { class: 'rp-n' }, String(r.n))),
              h('span', { class: 'rp-meter', 'aria-hidden': 'true' }, h('i', { style: 'width:' + Math.max(4, Math.round(r.n / top * 100)) + '%' }))))))) :
          h('p', { id: 'rpByProject', class: 'rp-empty' }, 'No tasks finished ' + (span.current ? 'this ' + ui.period + ' yet.' : 'that ' + ui.period + '.'))),
    ];
  }
  /* The week or month By project shows, with where the arrows lead: back to the first one with a tick, on to now. */
  function period(ticks, now) {
    const week = ui.period === 'week', curStart = week ? weekStartOf(now) : monthStartOf(now);
    const firstAt = ticks.length ? ticks[0].at : now, first = Math.min(curStart, week ? weekStartOf(firstAt) : monthStartOf(firstAt));
    const step = (ts, n) => week ? addDays(ts, 7 * n) : addMonths(ts, n);
    let from = at == null ? curStart : clamp(week ? weekStartOf(at) : monthStartOf(at), first, curStart);
    const current = from === curStart;
    const label = week ? weekLabel(from, true) + (current ? ', this week' : '') : monthLabel(from) + (current ? ', this month' : '');
    return { from, to: step(from, 1), label, current, prev: from > first ? step(from, -1) : null, next: from < curStart ? step(from, 1) : null };
  }

  /* Records: the streak, the busiest building of each month, and milestones finished. */
  function recordsPage(ticks, now) {
    const s = streakOf(ticks, now), span = (a, b) => a === b ? dayMonth(parseYmd(a)) : dayMonth(parseYmd(a)) + ' to ' + dayMonth(parseYmd(b));
    const todayLine = s.today ? 'Today counts already.' : s.off ? 'Today is a day off, so it cannot break it.' : s.n ? 'Finish a task today to make it ' + plural(s.n + 1, 'day', 'days') + '.' : 'Finish a task today to start one.';
    const months = busiestByMonth(ticks, 12, now), [cur, ...past] = months;
    const ms = milestonesFinished(DB.projects), shown = allMilestones ? ms : ms.slice(0, MILESTONES_SHOWN);
    const who = m => m.top.map(r => r.p.name).join(' and ');
    return [
      group('Streak',
        h('div', { id: 'rpStreak', class: 'rp-streak' }, iconEl('flame', 30),
          h('span', { class: 'rp-streak-body' }, h('b', { class: 'rp-big' }, plural(s.n, 'day', 'days')), h('span', null, 'in a row with a task finished'))),
        h('p', { id: 'rpToday', class: 'rp-line' }, todayLine),
        h('p', { id: 'rpLongest', class: 'rp-line' }, 'Longest: ', h('b', null, plural(s.best.n, 'day', 'days')), s.best.n ? ', ' + span(s.best.from, s.best.to) + '.' : '.'),
        note('Rest days and days away never break it.')),
      group('Busiest building of the month',
        cur.top.length ? h('div', { id: 'rpBusiest', class: 'rp-busy' },
          h('span', { class: 'rp-busy-art', 'aria-hidden': 'true' }, MapView.thumb(cur.top[0].p)),
          h('span', { class: 'rp-busy-body' },
            h('b', { class: 'rp-busy-name', dir: 'auto' }, who(cur)),
            h('span', null, plural(cur.n, 'task', 'tasks') + ' finished in ' + monthLabel(cur.start, false) + (cur.top.length > 1 ? ' each' : '')))) :
          h('p', { id: 'rpBusiest', class: 'rp-empty' }, 'No tasks finished in ' + monthLabel(cur.start, false) + ' yet.'),
        past.length ? h('ul', { id: 'rpMonths', class: 'rp-list' }, past.map(m => h('li', null,
          h('span', { class: 'rp-date' }, monthLabel(m.start, new Date(m.start).getFullYear() !== new Date(now).getFullYear())),
          h('span', { class: 'rp-what', dir: 'auto' }, who(m)), h('b', { class: 'rp-n' }, String(m.n))))) : null),
      group('Milestones finished',
        ms.length ? h('ul', { id: 'rpMilestones', class: 'rp-list' }, shown.map(x => h('li', null,
          h('span', { class: 'rp-date' }, fmtDate(x.at)),
          h('button', { class: 'rp-what linkish', type: 'button', dir: 'auto', 'data-k': 'ms-' + x.m.id, title: 'Open ' + x.p.name, onclick: () => FullView.open(x.p.id) },
            x.m.name, h('span', { class: 'rp-proj' }, x.p.name))))) : h('p', { id: 'rpMilestones', class: 'rp-empty' }, 'No milestone finished yet.'),
        ms.length > MILESTONES_SHOWN ? h('button', { class: 'btn btn-quiet btn-small rp-more', type: 'button', 'data-k': 'ms-more', onclick: () => { allMilestones = !allMilestones; render(); } },
          allMilestones ? 'Show fewer' : 'Show all ' + ms.length) : null),
    ];
  }

  function init() {
    $('#rpBack').innerHTML = iconSvg('back', 18);
    $('#sbChartIcon').innerHTML = iconSvg('chart', 16);
    $('#sbChartIcon').style.display = 'inline-flex';
    $('#rpTabs').replaceChildren(...TABS.map(t => h('button', { class: 'set-tab rp-tab', type: 'button', role: 'tab', 'data-tab': t.id, 'aria-label': t.label, title: t.label,
      onclick: () => showTab(t.id) }, h('span', { class: 'set-tab-ic', 'aria-hidden': 'true', html: iconSvg(t.icon, 18, 'var(--rp-ic, var(--accent))') }), h('span', { class: 'set-tab-name' }, t.label))));
    $('#rpTabs').addEventListener('keydown', e => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      const k = TABS.findIndex(t => t.id === ui.tab);
      showTab(TABS[(k + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length].id);
      $('#rpTabs [aria-selected="true"]').focus();
    });
    $('#rpBack').addEventListener('click', () => close());
    $('#btnOpenReports').addEventListener('click', () => open());
    /* R opens and closes Reports, unless you are typing or a dialog is open, as the comma key does Settings. */
    window.addEventListener('keydown', e => {
      if (e.code !== 'KeyR' || e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
      const t = e.target;
      if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
      if (Confirm.isOpen() || Panel.isOpen()) return;
      e.preventDefault();
      toggle();
    });
  }
  return { init, open, close, toggle, isOpen, refresh, render, showTab, tab: () => ui.tab, reset: () => { at = null; allMilestones = false; } };
})();
