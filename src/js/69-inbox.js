/*
  Claude updates the city (0.1.36): Claude drops a change file into inbox/ in the Claude folder, and the city picks it
  up within a few seconds, with no Load plan or tasks. Each kind of change follows its own rule, as decided in Even
  Better Claude Connections, Round 1 (A1):
    applies at once, with a toast and Undo:   add-tasks, add-note, add-link, add-round (0.1.55)
    asks first, with Apply and Dismiss:       done (tick tasks), edit-description, replace-plan
  A change file is { app: 'nullovation-city', kind: 'change', version: 1, project, summary, changes: [{ do, ... }] }.
  What applies at once is applied, what asks first waits in inbox/pending/, and the file itself moves to inbox/done/
  (or inbox/rejected/, when the city cannot read it or has no project by that name), so nothing applies twice.
  One tab takes new files: the one that writes the data file.
  Since 0.1.68 (Claude's News on the Status Card, Round 1) an update is one report, said by its building's leader
  under the finish of the task it reports on (News.report), and each change that asks first has its own line, applied
  or dismissed on its own.
*/
const ClaudeInbox = (() => {
  const AT_ONCE = new Set(['add-tasks', 'add-note', 'add-link', 'add-round']);
  const ASK = new Set(['done', 'edit-description', 'replace-plan']);
  const KEEP_DAYS = 14;                       // done and rejected files are cleared after two weeks
  let pending = [], pendingSig = '', busy = false, prunedDay = '';
  const str = (x, n) => (typeof x === 'string' ? x.trim().slice(0, n) : '');
  const keyOf = s => String(s || '').trim().toLowerCase();
  const projectNamed = name => DB.projects.find(p => keyOf(p.name) === keyOf(name)) || null;
  const taskNamed = (p, text, open = true) => p.todos.find(t => (open ? isOpenTask(t) : !t.archived) && keyOf(t.text) === keyOf(text)) || null;   // never one in the archive

  async function sub(dir, path) {
    let d = dir;
    for (const part of path.split('/')) d = await d.getDirectoryHandle(part, { create: true });
    return d;
  }
  async function put(d, name, text) {
    const w = await (await d.getFileHandle(name, { create: true })).createWritable();
    await w.write(text); await w.close();
  }
  /* Moves a file by writing its copy and removing it, which works in any Chrome that can write the folder. */
  async function move(from, name, to, text) {
    await put(to, name, text);
    await from.removeEntry(name);
  }

  /* ---------- reading the inbox ---------- */
  async function poll(dir, take) {
    if (busy || !dir) return false;
    busy = true;
    let moved = false;
    try {
      const inbox = await sub(dir, 'inbox');
      if (take) {
        const names = [];
        for await (const [name, fh] of inbox.entries()) if (fh.kind === 'file' && /\.json$/i.test(name)) names.push([name, fh]);
        for (const [name, fh] of names.sort((a, b) => a[0].localeCompare(b[0]))) { await arrive(dir, inbox, name, fh); moved = true; }
        if (prunedDay !== ymd()) { prunedDay = ymd(); await prune(inbox); }
      }
      const next = [], pend = await sub(dir, 'inbox/pending');
      for await (const [name, fh] of pend.entries()) {
        if (fh.kind !== 'file' || !/\.json$/i.test(name)) continue;
        try { const d = JSON.parse(await (await fh.getFile()).text()); if (d && Array.isArray(d.changes)) next.push({ name, project: str(d.project, 120), summary: str(d.summary, 300), changes: d.changes, at: d.received || 0, logged: !!d.logged }); } catch (e) { /* half written: next time */ }
      }
      next.sort((a, b) => a.at - b.at);
      const sig = next.map(x => x.name).join('|');
      if (sig !== pendingSig) { pendingSig = sig; moved = true; }
      pending = next;
    } catch (e) { /* no write access, or the folder went: the Claude folder's own state says so */ }
    busy = false;
    return moved;
  }
  async function arrive(dir, inbox, name, fh) {
    let text = '', data = null;
    try { text = await (await fh.getFile()).text(); data = JSON.parse(text); } catch (e) { data = null; }
    const p = data && data.app === 'nullovation-city' && data.kind === 'change' && Array.isArray(data.changes) ? projectNamed(data.project) : null;
    if (!p) {
      await move(inbox, name, await sub(dir, 'inbox/rejected'), text);
      toast(data && data.kind === 'change' ? 'Claude sent changes for ' + (str(data.project, 80) || 'a project with no name') + ', which is not in the city.' : 'Claude sent a file the city could not read: ' + name + '.', 'error');
      return;
    }
    const now = data.changes.filter(c => c && AT_ONCE.has(c.do)), later = data.changes.filter(c => c && ASK.has(c.do));
    let undo = null;
    for (const c of now) if (c.do === 'add-round') c._got = await Rounds.fromChange(dir, c);   // its round, read from wizard-rounds
    if (now.length) undo = applyNow(p, now, str(data.summary, 300), str(data.task, 500));
    if (later.length) await put(await sub(dir, 'inbox/pending'), name, JSON.stringify({ app: 'nullovation-city', kind: 'change', version: 1, project: p.name, summary: str(data.summary, 300), changes: later, received: Date.now() }, null, 1));
    await move(inbox, name, await sub(dir, 'inbox/done'), text);
    /* Its leader says it, in place of the toast (Leader UX, T1): one report, under the finish of the task it reports on
       (A1, 0.1.68). The task is the one the update names, else the one a tick, a description or a round is for. */
    const named = c => (c && (c.do === 'done' || c.do === 'edit-description' || c.do === 'add-round') ? str(c.task, 500) : '');
    News.report(p, { task: str(data.task, 500) || data.changes.map(named).find(Boolean) || '', named: !!str(data.task, 500),
      summary: str(data.summary, 300), undo: undo && undo.what ? undo : null, entry: later.length ? name : '' });
  }
  async function prune(inbox) {
    const cutoff = Date.now() - KEEP_DAYS * 86400e3;
    for (const folder of ['done', 'rejected']) {
      try {
        const d = await inbox.getDirectoryHandle(folder, { create: true }), old = [];
        for await (const [name, fh] of d.entries()) { if (fh.kind !== 'file') continue; try { if ((await fh.getFile()).lastModified < cutoff) old.push(name); } catch (e) { /* skip */ } }
        for (const name of old) await d.removeEntry(name);
      } catch (e) { /* next day */ }
    }
  }

  /* ---------- what applies at once: adding, never removing ---------- */
  function applyNow(p, changes, summary, task = '') {
    const before = { todos: new Set(p.todos.map(t => t.id)), ms: new Set(p.milestones.map(m => m.id)) };
    const added = { notes: [], links: [], rounds: [], updated: [] };
    let tasks = 0;
    for (const c of changes) {
      if (c.do === 'add-tasks') {
        let list;
        try { list = readTasks({ tasks: c.tasks }).tasks; } catch (e) { continue; }
        const name = str(c.milestone, 120), have = name && p.milestones.find(m => keyOf(m.name) === keyOf(name));
        const cur = currentGroup(p), live = liveMilestones(p);    // a milestone named in the archive comes back with them
        const target = have ? { id: have.id } : name ? { name } : cur && cur.ms ? { id: cur.ms.id } : live.length ? { id: live[live.length - 1].id } : { name: 'To do' };
        addTasks(p, list, target, { log: false });              // Claude writes nothing in Activity but its rounds (0.1.69, C2)
        tasks += list.length;
      } else if (c.do === 'add-note') {
        const title = str(c.title, 200), text = str(c.text, 8000);
        if (!title && !text) continue;
        /* Claude's Notes (0.1.71): a status, a plan or a decision goes in the task it is about, the note's own task or the
           update's, and with your notes when it names none here (K1, T1); how something works, and a note of no kind, go
           with your notes. A status, a plan and how something works stay one note, brought up to date: in a task its one
           of that kind, with your notes its one of that kind and title; a decision is a new note each time (K2). Claude
           only ever changes a note of its own. Its icon is the one it sends, else its kind's. */
        const kind = NOTE_KINDS.includes(c.kind) ? c.kind : '';
        const named = str(c.task, 500) || task;
        const t = kind && kind !== 'how' && named ? taskNamed(p, named) || taskNamed(p, named, false) : null;
        const list = t ? (t.notes || (t.notes = [])) : p.notes;
        const same = kind && kind !== 'decision' ? list.find(n => byClaude(n) && n.kind === kind && (t || keyOf(n.title) === keyOf(title))) : null;
        if (same) {
          added.updated.push({ id: same.id, was: JSON.parse(JSON.stringify(same)) });
          Object.assign(same, { title, text, updatedAt: Date.now() });
          continue;
        }
        const n = { id: uid('n'), title, text, at: Date.now(), icon: NOTE_ICONS.includes(c.icon) ? c.icon : KIND_ICON[kind] || 'sticky', by: 'claude', ...(kind ? { kind } : {}) };
        list.push(n); added.notes.push(n.id);
      } else if (c.do === 'add-link') {
        const url = str(c.url, 2000);
        if (!url || p.links.some(l => addressKey(l.url) === addressKey(url))) continue;
        const l = { id: uid('l'), label: str(c.label, 120), url, icon: LINK_ICONS.includes(c.icon) ? c.icon : guessIcon(url), shortcut: true };
        p.links.push(l); added.links.push(l.id);
      } else if (c.do === 'add-round') {
        /* a wizard round for a task (0.1.55, W1): it replaces any round the task had (W6) */
        const t = taskNamed(p, c.task) || taskNamed(p, c.task, false), got = c._got;
        if (!t || !got) continue;
        const was = t.round ? JSON.parse(JSON.stringify(t.round)) : null;
        t.round = makeRound(got.w, got.file);
        /* wizard rounds appear in Activity (Leader Bubbles, Round 2, C2), the one line Claude still writes there; Undo
           takes it back out */
        logActivity(p, 'Claude attached a wizard round to ' + t.text + ': ' + t.round.title);
        added.rounds.push({ id: t.id, was, line: p.activity[p.activity.length - 1] });
      }
    }
    const bits = [tasks && 'added ' + plural(tasks, 'task', 'tasks'), added.notes.length && (tasks ? 'a note' : 'wrote a note'), added.updated.length && 'brought a note up to date', added.links.length && (tasks || added.notes.length ? plural(added.links.length, 'link', 'links') : 'added ' + plural(added.links.length, 'link', 'links')),
      added.rounds.length && (added.rounds.length === 1 ? 'attached a wizard round' : 'attached ' + added.rounds.length + ' wizard rounds')].filter(Boolean);
    const what = bits.length > 1 ? bits.slice(0, -1).join(', ') + ' and ' + bits[bits.length - 1] : bits[0] || '';
    if (what) { window.changed(p); if ((added.rounds.length || added.notes.length || added.updated.length) && typeof FullView !== 'undefined' && FullView.isOpen()) FullView.refreshRounds(); }   // a round, or a note in a task (0.1.71)
    return { what, todos: p.todos.filter(t => !before.todos.has(t.id)).map(t => t.id), ms: p.milestones.filter(m => !before.ms.has(m.id)).map(m => m.id), ...added };
  }
  function undoNow(p, u) {
    const drop = new Set(u.todos), notes = new Set(u.notes), links = new Set(u.links);
    p.todos = p.todos.filter(t => !drop.has(t.id));
    p.notes = p.notes.filter(n => !notes.has(n.id));
    for (const t of p.todos) if (Array.isArray(t.notes)) { t.notes = t.notes.filter(n => !notes.has(n.id)); if (!t.notes.length) delete t.notes; }   // a note Claude put in a task (0.1.71)
    for (const w of u.updated || []) {                         // a note Claude brought up to date goes back to how it was
      const n = allNotes(p).find(x => x.id === w.id); if (!n) continue;
      for (const k of Object.keys(n)) delete n[k];
      Object.assign(n, JSON.parse(JSON.stringify(w.was)));
    }
    p.links = p.links.filter(l => !links.has(l.id));
    for (const r of u.rounds || []) {
      const k = r.line && Array.isArray(p.activity) ? p.activity.indexOf(r.line) : -1;
      if (k >= 0) p.activity.splice(k, 1);                      // its line goes with it
      const t = p.todos.find(x => x.id === r.id); if (!t) continue; if (r.was) t.round = r.was; else delete t.round;
    }
    p.milestones = p.milestones.filter(m => !u.ms.includes(m.id) || p.todos.some(t => t.milestoneId === m.id));
    window.changed(p);
    if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render();
    toast('Took back what Claude added to ' + p.name + '.');
  }

  /* ---------- what asks first ---------- */
  /* What a change would do: ok when it can, with the task it names (an edit may name a done task, never one in the
     archive) or the plan read. */
  function readable(p, c) {
    if (c.do === 'done') { const t = taskNamed(p, c.task); return { ok: !!t, t, why: t ? '' : 'not open in this project' }; }
    if (c.do === 'edit-description') { const t = taskNamed(p, c.task, false); return { ok: !!t, t, why: t ? '' : 'no task by that name' }; }
    if (c.do === 'replace-plan') {
      try { return { ok: true, plan: readPlan(c.plan) }; }
      catch (e) { return { ok: false, why: e.message }; }
    }
    return { ok: false, why: 'unknown' };
  }
  /* The changes still waiting in an entry. Since 0.1.68 each has its own line, applied or dismissed on its own, and
     marked so in its pending file until the last one goes; then the file moves to inbox/done. */
  const openIdx = entry => entry.changes.map((c, i) => (c && !c._settled ? i : -1)).filter(i => i >= 0);
  /* Applies one change (i), or every one still waiting. A tick from its own line is its leader's toast, as Tick it's. */
  async function apply(entry, i = null) {
    const p = projectNamed(entry.project), dir = ClaudeWork.folder();
    if (!p || !dir) return;
    const which = openIdx(entry).filter(k => i == null || k === i);
    let n = 0, one = null;
    for (const k of which) {
      const c = entry.changes[k], r = readable(p, c);
      c._settled = r.ok ? 'applied' : 'skipped';
      if (!r.ok) continue;
      if (c.do === 'done') { if (i == null) tickTask(p, r.t); else ClaudeWork.tick(p, r.t); }   // a repeat moves on to its next date
      else if (c.do === 'edit-description') r.t.description = str(c.description, 8000);
      else if (c.do === 'replace-plan') applyPlan(p, r.plan);
      n++; one = { c, r };
    }
    if (n) {
      window.changed(p);
      if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render();
    }
    await keep(dir, entry);
    if (i == null) toast(n ? 'Applied what Claude asked in ' + p.name + '.' : 'Nothing in it could be applied, so it was put away.');
    else if (one && one.c.do === 'edit-description') toast('Gave ' + one.r.t.text + ' its new description.');
    else if (one && one.c.do === 'replace-plan') toast('Replaced the plan of ' + p.name + '.');
  }
  async function dismiss(entry, i = null) {
    const dir = ClaudeWork.folder();
    if (!dir) return;
    const which = openIdx(entry).filter(k => i == null || k === i);
    for (const k of which) entry.changes[k]._settled = 'dismissed';
    await keep(dir, entry);
    const c = i != null && which.length ? entry.changes[which[0]] : null, task = c ? lineTitle(str(c.task, 200)) : '';
    toast(!c ? 'Dismissed what Claude asked.' : c.do === 'done' ? 'Left ' + task + ' open.' : c.do === 'edit-description' ? 'Kept the description of ' + task + '.'
      : c.do === 'replace-plan' ? 'Kept the plan of ' + entry.project + '.' : 'Dismissed what Claude asked.');
  }
  const entryFile = (entry, extra = {}) => JSON.stringify({ app: 'nullovation-city', kind: 'change', version: 1, project: entry.project, summary: entry.summary,
    changes: entry.changes, received: entry.at, logged: !!entry.logged, ...extra }, null, 1);
  /* What is left waits in its pending file, marked; with nothing left the file moves to inbox/done. */
  async function keep(dir, entry) {
    if (!openIdx(entry).length) { await settle(dir, entry, 'settled'); return; }
    try { await put(await sub(dir, 'inbox/pending'), entry.name, entryFile(entry)); } catch (e) { /* settled by another tab */ }
    pendingSig = '';
    ClaudeWork.redraw();
  }
  async function settle(dir, entry, how) {
    try {
      const pend = await sub(dir, 'inbox/pending');
      await move(pend, entry.name, await sub(dir, 'inbox/done'), entryFile(entry, { [how]: Date.now() }));
    } catch (e) { /* already settled by another tab */ }
    pending = pending.filter(x => x.name !== entry.name);
    pendingSig = pending.map(x => x.name).join('|');
    ClaudeWork.redraw();
  }

  /* What waits for this building: its leader says it in its status card and its bubble (Leader UX, 0.1.59). */
  const forProject = p => pending.filter(x => keyOf(x.project) === keyOf(p.name));
  /* A change in a few words, its task's title cut short as a leader's line cuts it. */
  const changeWords = c => (c.do === 'done' ? 'tick off ' + lineTitle(str(c.task, 200)) : c.do === 'edit-description' ? 'a new description for ' + lineTitle(str(c.task, 200))
    : c.do === 'replace-plan' ? 'a new plan' : 'a change');
  /* The change Claude asks about, for the leader's line (0.1.68): the change itself, or how many wait. Claude's summary
     is its own words, said on a line of its own (C2), never as the change. */
  function gist(p, entry) {
    const open = openIdx(entry), c = open.length === 1 ? entry.changes[open[0]] : null;
    if (!c) return plural(open.length || entry.changes.length, 'change', 'changes');
    const t = c.do === 'done' ? taskNamed(p, c.task) : null;
    return changeWords(c) + (t && t.repeat ? ', on to its next date' : '');
  }
  return { poll, gist, readable, openIdx, taskNamed, planSize: plan => plural(plan.milestones.length, 'milestone', 'milestones') + ' and ' + plural(plan.milestones.reduce((n, m) => n + m.tasks.length, 0), 'task', 'tasks'),
    apply, dismiss, undo: undoNow, count: p => forProject(p).length, total: () => pending.length, pending: () => pending, AT_ONCE, ASK };
})();
