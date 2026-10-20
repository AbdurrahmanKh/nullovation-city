/* ---------- the archive (Archiving, Round 1) ----------
   A done task moves into its project's archive by hand, or by itself 7 days after its tick (A2, A2a). It stays in the
   project's todos, marked `archived`, so the counts and progress (B2), search, Reports, the recap, Proxima and the
   builder card keep seeing it (A3), while the project view's lists, a milestone's Copy for Claude and the city summary
   leave it out. A milestone whose every task is archived goes to the archive with them (B1), and comes back as soon as
   one of them is restored or a task is added to it. Restore brings a task back done, and it archives itself again 7
   days after the restore (C1). Archiving is tidying, not work: it touches neither Updated nor urgency, and writes
   nothing in Activity. */
const ARCHIVE_DAYS = 7;
const isArchived = t => !!(t && t.archived);
const shownTodos = list => list.filter(t => !t.archived);
const archivedTodos = p => p.todos.filter(isArchived);
const canArchive = t => !!t.done && !t.archived;

/* The day a done task archives itself: 7 days after the later of its tick and its last restore (`archiveFrom`). */
function archiveDay(t) {
  const from = Math.max(t.doneAt ? startOfDay(t.doneAt) : 0, parseYmd(t.archiveFrom) || 0);
  return from ? plusDays(from, ARCHIVE_DAYS) : null;
}
/* A milestone is in the archive when it has tasks and every one of them is archived. */
function milestoneArchived(p, m) {
  let any = false;
  for (const t of p.todos) if (t.milestoneId === m.id) { if (!t.archived) return false; any = true; }
  return any;
}
const liveMilestones = p => p.milestones.filter(m => !milestoneArchived(p, m));

/* What archiving or restoring changes on a task, kept so Undo can put it back exactly. */
const archiveSnap = t => ({ t, archived: !!t.archived, archivedAt: t.archivedAt ?? null, archiveFrom: t.archiveFrom || '' });
function putBackArchive(s) {
  const t = s.t;
  if (s.archived) { t.archived = true; t.archivedAt = s.archivedAt; } else { delete t.archived; delete t.archivedAt; }
  if (s.archiveFrom) t.archiveFrom = s.archiveFrom; else delete t.archiveFrom;
}
/* Into the archive, by hand (A1) or by itself. Returns what Undo needs. */
function archiveTasks(list, now = Date.now()) {
  const snaps = [];
  for (const t of list) if (canArchive(t)) { snaps.push(archiveSnap(t)); t.archived = true; t.archivedAt = now; }
  return snaps;
}
/* Back out of the archive (C1): done, in its old place, for another 7 days. */
function restoreTask(t, now = Date.now()) {
  const s = archiveSnap(t);
  delete t.archived; delete t.archivedAt;
  t.archiveFrom = ymd(now);
  return s;
}
/* Every done task past its 7 days goes to the archive (A2a); on the first open with archiving that takes every done
   task ticked a week or more ago at once (D1). A done task with no tick on record counts from the day this first sees
   it. Runs on start-up and when the day changes; returns how many went. */
function archiveDueTasks(now = Date.now()) {
  const today = startOfDay(now);
  let n = 0;
  for (const p of DB.projects) for (const t of p.todos) {
    if (!canArchive(t)) continue;
    if (!t.doneAt && !t.archiveFrom) t.archiveFrom = ymd(now);
    const day = archiveDay(t);
    if (day != null && today >= day) { t.archived = true; t.archivedAt = now; n++; }
  }
  return n;
}
/* The Archive view's groups (C3): by milestone, the milestone with the newest task first, its tasks newest first, by
   the day each was ticked. `whole` marks a milestone that went to the archive with its tasks (B1). */
const archivedWhen = t => t.doneAt || t.archivedAt || 0;
function archiveGroups(p) {
  const known = new Map(p.milestones.map(m => [m.id, m]));
  const by = new Map();
  for (const t of archivedTodos(p)) {
    const m = known.get(t.milestoneId) || null, k = m ? m.id : '';
    if (!by.has(k)) by.set(k, { ms: m, tasks: [] });
    by.get(k).tasks.push(t);
  }
  const out = [...by.values()];
  for (const g of out) { g.tasks.sort((a, b) => archivedWhen(b) - archivedWhen(a)); g.whole = !!g.ms && milestoneArchived(p, g.ms); }
  return out.sort((a, b) => archivedWhen(b.tasks[0]) - archivedWhen(a.tasks[0]));
}
/* The shown tasks in a new order (a drag, or Alt and an arrow), while every archived task keeps its place among them,
   so Restore puts it back where it was. */
function reorderShown(p, order) {
  const shown = order.concat(p.todos.filter(t => !t.archived && !order.includes(t)));
  let i = 0;
  p.todos = p.todos.map(t => (t.archived ? t : shown[i++]));
  normalizeOrder(p);
}
