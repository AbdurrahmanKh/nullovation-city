/* ---------- the week: one snapshot per Saturday-to-Friday week, and every older week to go back to ---------- */
function weekStartOf(ts) {
  const d = new Date(ts);
  const back = (d.getDay() + 1) % 7;                     // days since Saturday
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() - back).getTime();
}
const addDays = (ts, n) => { const d = new Date(ts); return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n).getTime(); };
function weekLabel(start, withYear = false) {
  const f = (ts, y) => new Date(ts).toLocaleDateString('en-GB', y ? { day: 'numeric', month: 'short', year: 'numeric' } : { day: 'numeric', month: 'short' });
  return f(start) + ' to ' + f(addDays(start, 6), withYear);
}
/* What happened in one week, per project, from the activity log and the tasks and notes themselves. */
function weekOf(start) {
  const end = addDays(start, 7);
  const inWeek = at => typeof at === 'number' && at >= start && at < end;
  const rows = [], tot = { done: 0, notes: 0, ms: 0, added: 0, worked: 0, planted: 0 };
  for (const p of DB.projects) {
    const log = (p.activity || []).filter(e => inWeek(e.at));
    const doneMap = new Map();
    for (const e of log) if (e.text.startsWith('Done: ')) doneMap.set(e.text.slice(6), e.at);
    for (const t of p.todos) if (t.done && inWeek(t.doneAt) && !doneMap.has(t.text)) doneMap.set(t.text, t.doneAt);
    const done = [...doneMap.entries()].map(([text, at]) => ({ text, at })).sort((x, y) => x.at - y.at);
    const added = log.filter(e => e.text.startsWith('Added todo: ')).map(e => ({ text: e.text.slice(12), at: e.at }));
    const worked = log.filter(e => e.text === 'I worked!').length;
    const notes = p.notes.filter(n => inWeek(n.at)).sort((x, y) => x.at - y.at);
    const ms = p.milestones.filter(m => {
      const ts = p.todos.filter(t => t.milestoneId === m.id);
      return ts.length && ts.every(t => t.done) && inWeek(Math.max(...ts.map(t => t.doneAt || 0)));
    });
    const planted = inWeek(p.createdAt);
    if (done.length || added.length || worked || notes.length || ms.length || planted) rows.push({ p, done, added, worked, notes, ms, planted });
    tot.done += done.length; tot.notes += notes.length; tot.ms += ms.length; tot.added += added.length; tot.worked += worked; tot.planted += planted ? 1 : 0;
  }
  return { start, end, rows, tot };
}
/* The side bar's one line: tasks done, notes, milestones. */
function weekNumbers(tot) {
  return [tot.done ? plural(tot.done, 'task', 'tasks') + ' done' : null, tot.notes ? plural(tot.notes, 'note', 'notes') : null,
    tot.ms ? plural(tot.ms, 'milestone', 'milestones') : null].filter(Boolean);
}
function weekSummary(tot) {
  const parts = [tot.done ? plural(tot.done, 'task', 'tasks') + ' finished' : null, tot.notes ? plural(tot.notes, 'note', 'notes') + ' written' : null,
    tot.ms ? plural(tot.ms, 'milestone', 'milestones') + ' finished' : null, tot.added ? plural(tot.added, 'task', 'tasks') + ' added' : null,
    tot.worked ? plural(tot.worked, 'I worked! check-in', 'I worked! check-ins') : null, tot.planted ? plural(tot.planted, 'building', 'buildings') + ' planted' : null].filter(Boolean);
  return parts.length ? parts.join(', ') + '.' : 'Nothing recorded this week.';
}
const noteLine = n => ((n.title || '').trim() ? n.title.trim() + ': ' : '') + n.text.replace(/\s+/g, ' ').trim().slice(0, 160);
function weekText(w) {
  const L = ['# Nullovation City, week of ' + weekLabel(w.start, true), weekSummary(w.tot)];
  for (const r of w.rows) {
    L.push('', '## ' + r.p.name);
    if (r.planted) L.push('Planted this week.');
    if (r.done.length) { L.push('Finished:'); for (const d of r.done) L.push('- ' + d.text); }
    if (r.ms.length) { L.push('Milestones finished:'); for (const m of r.ms) L.push('- ' + m.name); }
    if (r.added.length) { L.push('Added:'); for (const d of r.added) L.push('- ' + d.text); }
    if (r.notes.length) { L.push('Notes:'); for (const n of r.notes) L.push('- ' + noteLine(n)); }
    if (r.worked) L.push('I worked!: ' + plural(r.worked, 'check-in', 'check-ins') + '.');
  }
  if (!w.rows.length) L.push('', 'Nothing recorded this week.');
  return L.join('\n');
}
/* The first week anything was recorded. */
function firstWeekStart() {
  let min = Date.now();
  for (const p of DB.projects) {
    min = Math.min(min, p.createdAt || min);
    for (const e of p.activity || []) min = Math.min(min, e.at);
    for (const n of p.notes) min = Math.min(min, n.at);
  }
  return weekStartOf(min);
}
function openRecap(start = weekStartOf(Date.now())) {
  const body = h('div', { class: 'recap' });
  const day = at => new Date(at).toLocaleDateString('en-GB', { weekday: 'short' });
  const show = s => {
    const cur = weekStartOf(Date.now()), first = Math.min(firstWeekStart(), cur);
    s = clamp(s, first, cur);
    const w = weekOf(s);
    const weeks = [];
    for (let k = cur; k >= first; k = addDays(k, -7)) weeks.push(k);
    const pick = h('select', { class: 'field recap-weeks', 'aria-label': 'All weeks', onchange: e => show(Number(e.target.value)) },
      weeks.map(k => { const t = weekOf(k).tot; return h('option', { value: String(k), selected: k === s }, weekLabel(k) + (k === cur ? ' (this week)' : '') + (t.done || t.notes ? ': ' + [t.done ? t.done + ' done' : null, t.notes ? plural(t.notes, 'note', 'notes') : null].filter(Boolean).join(', ') : '')); }));
    const nav = h('div', { class: 'recap-nav' },
      h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'The week before', title: 'The week before', html: iconSvg('caretR', 10), disabled: s <= first, style: 'transform: scaleX(-1)', onclick: () => show(addDays(s, -7)) }),
      h('h3', { class: 'recap-when' }, weekLabel(s, true) + (s === cur ? ', this week' : '')),
      h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'The week after', title: 'The week after', html: iconSvg('caretR', 10), disabled: s >= cur, onclick: () => show(addDays(s, 7)) }),
      pick);
    const list = (label, items) => items.length ? h('div', { class: 'recap-group' }, h('h4', null, label), h('ul', null, items)) : null;
    const rows = w.rows.map(r => h('section', { class: 'recap-proj' },
      h('button', { class: 'recap-name linkish', type: 'button', dir: 'auto', onclick: () => { Panel.close(); MapView.select(r.p.id); } }, r.p.name),
      r.planted ? h('p', { class: 'recap-tag' }, 'Planted this week') : null,
      list('Finished', r.done.map(d => h('li', { dir: 'auto' }, h('span', { class: 'recap-day' }, day(d.at)), d.text))),
      list('Milestones finished', r.ms.map(m => h('li', { dir: 'auto' }, m.name))),
      list('Added', r.added.map(d => h('li', { dir: 'auto' }, h('span', { class: 'recap-day' }, day(d.at)), d.text))),
      list('Notes', r.notes.map(n => h('li', { dir: 'auto' }, h('span', { class: 'recap-day' }, day(n.at)), noteLine(n)))),
      r.worked ? h('p', { class: 'recap-worked' }, 'I worked!: ' + plural(r.worked, 'check-in', 'check-ins')) : null));
    body.replaceChildren(nav,
      h('p', { class: 'recap-sum' }, weekSummary(w.tot)),
      ...rows,
      h('div', { class: 'recap-foot' }, h('button', { class: 'btn', type: 'button', onclick: async () => {
        if (await copyText(weekText(w))) toast('Week copied. Paste it into Claude or Slack.'); else toast('The browser blocked copying. Try again.', 'error');
      } }, iconEl('copy', 14), 'Copy the week')));
  };
  Panel.open('Your week', body);
  show(start);
}

function projectStatus(p, now = Date.now()) {
  const L = [];
  const pr = progressOf(p);
  L.push('## ' + p.name);
  L.push('Progress: ' + pr.pct + '%' + (pr.manual ? ', set manually.' : ' (' + pr.done + ' of ' + pr.total + ' todos done).'));
  const nx = nextTask(p);
  if (nx) { const d = dueInfo(nx, now); L.push('Next task: ' + nx.text + (d ? ' (' + d.text.toLowerCase() + ')' : '') + '.'); }
  const dl = deadlineInfo(p.deadline, now); if (dl) L.push(dl.text + '.');
  const cur = currentGroup(p);
  if (cur && cur.ms) L.push('Current milestone: ' + cur.ms.name + ' (' + cur.todos.filter(t => t.done).length + ' of ' + cur.todos.length + ' done).');
  const open = p.todos.filter(t => !t.done);
  if (open.length) {
    L.push('Open todos:');
    const msName = id => (p.milestones.find(m => m.id === id) || {}).name;
    for (const t of open.slice(0, 15)) {
      const extra = [msName(t.milestoneId), t.due ? dueInfo(t, now).text : null].filter(Boolean).join(', ');
      L.push('- ' + t.text + (extra ? ' (' + extra + ')' : ''));
      if ((t.description || '').trim()) L.push('  ' + t.description.trim().replace(/\s+/g, ' ').slice(0, 300));
    }
    if (open.length > 15) L.push('- and ' + (open.length - 15) + ' more');
  } else L.push('No open todos.');
  const last = [...p.notes].sort((a, b) => b.at - a.at)[0];
  if (last) L.push('Latest note (' + fmtDate(last.at) + '): ' + ((last.title || '').trim() ? last.title.trim() + '. ' : '') + last.text.replace(/\s+/g, ' ').slice(0, 300));
  L.push('Updated ' + relAgo(p.updatedAt, now) + '.');
  return L.join('\n');
}
function statusBrief(now = Date.now()) {
  const L = [];
  L.push('# Nullovation City status, ' + new Date(now).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }));
  L.push(plural(DB.projects.length, 'project', 'projects') + '.');
  const ordered = [...DB.projects].sort((a, b) => (a.plot.u + a.plot.v) - (b.plot.u + b.plot.v) || (a.plot.u - a.plot.v) - (b.plot.u - b.plot.v));
  for (const p of ordered) { L.push(''); L.push(projectStatus(p, now)); }
  return L.join('\n');
}
async function copyBrief() {
  const text = statusBrief();
  if (await copyText(text)) toast('Status brief copied. Paste it into any Claude chat.');
  else toast('The browser blocked copying. Try again, or use Export backup.', 'error');
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* fall back below */ }
  try {
    const ta = h('textarea', { style: 'position:fixed;left:-9999px;top:0', 'aria-hidden': 'true' });
    ta.value = text; document.body.append(ta); ta.select();
    const ok = document.execCommand('copy'); ta.remove(); return ok;
  } catch (e) { return false; }
}
async function copyProjectStatus(p) {
  if (await copyText(projectStatus(p))) toast('Status copied. Paste it into Claude.');
  else toast('The browser blocked copying. Try again.', 'error');
}
function builderCard(p) {
  const L = [];
  const open = p.todos.filter(t => !t.done), done = p.todos.filter(t => t.done);
  const clean = s => String(s || '').replace(/\s+/g, ' ').trim();
  L.push('# Nullovation City builder card');
  L.push('For the nullovation-city-builder skill. Add your own idea for the building under this card if you have one.');
  L.push('');
  L.push('## Project');
  L.push('Name: ' + p.name);
  L.push('Size signals: ' + [plural(p.todos.length, 'todo', 'todos') + ' (' + open.length + ' open)', plural(p.milestones.length, 'milestone', 'milestones'),
    plural(p.notes.length, 'note', 'notes'), plural(p.links.length, 'link', 'links')].join(', '));
  L.push('');
  L.push('## Description');
  L.push(p.description.trim() || 'none');
  if (p.milestones.length) {
    L.push('');
    L.push('## Milestones');
    for (const g of groupsOf(p)) if (g.ms) L.push('- ' + clean(g.ms.name));
  }
  if (open.length) {
    L.push('');
    L.push('## Open todos');
    for (const t of open.slice(0, 20)) L.push('- ' + clean(t.text));
    if (open.length > 20) L.push('- and ' + (open.length - 20) + ' more');
  }
  if (done.length) {
    L.push('');
    L.push('## Done todos');
    for (const t of done.slice(0, 10)) L.push('- ' + clean(t.text));
    if (done.length > 10) L.push('- and ' + (done.length - 10) + ' more');
  }
  return L.join('\n');
}
async function copyBuilderCard(p) {
  if (await copyText(builderCard(p))) toast('Builder card copied. Paste it into a chat with the nullovation-city-builder skill.');
  else toast('The browser blocked copying. Try again.', 'error');
}
