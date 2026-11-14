/* ---------- the week: Saturday to Friday ---------- */
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
/* A task added, from its Activity line: added, or turned from a note (0.1.54). */
const addedTodo = s => s.startsWith('Added todo: ') ? s.slice(12) : s.startsWith('Turned into a task: ') ? s.slice(20) : null;
/* The week as it was told until 0.1.82, in the side bar's This week card and the panel Your week, is Proxima's weekly
   report since 0.1.83 (Proxima Reports, Round 1): one weekly report in place of two, in 76-proxima.js. */

function projectStatus(p, now = Date.now()) {
  const L = [];
  const pr = progressOf(p);
  L.push('## ' + p.name);
  if (leaderLine(p)) L.push(leaderLine(p) + '.');
  L.push('Progress: ' + pr.pct + '%' + (pr.manual ? ', set manually.' : ' (' + pr.done + ' of ' + pr.total + ' todos done).'));
  const nx = nextTask(p);
  if (nx) { const d = dueInfo(nx, now); L.push('Next task: ' + nx.text + (d ? ' (' + d.text.toLowerCase() + ')' : '') + '.'); }
  const dl = deadlineInfo(p.deadline, now); if (dl) L.push(dl.text + '.');
  const cur = currentGroup(p);
  if (cur && cur.ms) L.push('Current milestone: ' + cur.ms.name + ' (' + cur.todos.filter(t => t.done).length + ' of ' + cur.todos.length + ' done).');
  const open = openTasks(p, now), waiting = waitingTasks(p, now);
  const msName = id => (p.milestones.find(m => m.id === id) || {}).name;
  if (open.length) {
    L.push('Open todos:');
    for (const t of open.slice(0, 15)) {
      const extra = [msName(t.milestoneId), t.due ? dueInfo(t, now).text : null, t.repeat ? 'repeats ' + repeatText(t.repeat).toLowerCase() : null].filter(Boolean).join(', ');
      L.push('- ' + t.text + (extra ? ' (' + extra + ')' : ''));
      if ((t.description || '').trim()) L.push('  ' + t.description.trim().replace(/\s+/g, ' ').slice(0, 300));
    }
    if (open.length > 15) L.push('- and ' + (open.length - 15) + ' more');
  } else L.push('No open todos.');
  if (waiting.length) {
    L.push('Repeats waiting for their next date:');
    for (const t of waiting.slice(0, 15)) L.push('- ' + t.text + ' (' + repeatText(t.repeat).toLowerCase() + ', back ' + backWhen(t, now) + ')');
  }
  const last = [...allNotes(p)].sort((a, b) => b.at - a.at)[0];
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
  L.push('', REPORT_LINE);
  return L.join('\n');
}
/* One project's status for Claude: the status, then the line asking Claude to report back. */
function projectStatusForClaude(p, now = Date.now()) {
  return projectStatus(p, now) + '\n\n' + REPORT_LINE;
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
  if (await copyText(projectStatusForClaude(p))) toast('Status copied. Paste it into Claude.');
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
    plural(allNotes(p).length, 'note', 'notes'), plural(p.links.length, 'link', 'links')].join(', '));
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
