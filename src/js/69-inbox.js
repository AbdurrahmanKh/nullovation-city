/*
  Claude updates the city (0.1.36): Claude drops a change file into inbox/ in the Claude folder, and the city picks it
  up within a few seconds, with no Load plan or tasks. Each kind of change follows its own rule, as decided in Even
  Better Claude Connections, Round 1 (A1):
    applies at once, with a toast and Undo:   add-tasks, add-note, add-link
    asks first, with Apply and Dismiss:       done (tick tasks), edit-description, replace-plan
  A change file is { app: 'nullovation-city', kind: 'change', version: 1, project, summary, changes: [{ do, ... }] }.
  What applies at once is applied, what asks first waits in inbox/pending/, and the file itself moves to inbox/done/
  (or inbox/rejected/, when the city cannot read it or has no project by that name), so nothing applies twice.
  One tab takes new files: the one that writes the data file.
*/
const ClaudeInbox = (() => {
  const AT_ONCE = new Set(['add-tasks', 'add-note', 'add-link']);
  const ASK = new Set(['done', 'edit-description', 'replace-plan']);
  const KEEP_DAYS = 14;                       // done and rejected files are cleared after two weeks
  let pending = [], pendingSig = '', busy = false, prunedDay = '';
  const str = (x, n) => (typeof x === 'string' ? x.trim().slice(0, n) : '');
  const keyOf = s => String(s || '').trim().toLowerCase();
  const projectNamed = name => DB.projects.find(p => keyOf(p.name) === keyOf(name)) || null;
  const taskNamed = (p, text, open = true) => p.todos.find(t => (!open || !t.done) && keyOf(t.text) === keyOf(text)) || null;

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
        try { const d = JSON.parse(await (await fh.getFile()).text()); if (d && Array.isArray(d.changes)) next.push({ name, project: str(d.project, 120), summary: str(d.summary, 300), changes: d.changes, at: d.received || 0 }); } catch (e) { /* half written: next time */ }
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
    if (now.length) undo = applyNow(p, now, str(data.summary, 300));
    if (later.length) await put(await sub(dir, 'inbox/pending'), name, JSON.stringify({ app: 'nullovation-city', kind: 'change', version: 1, project: p.name, summary: str(data.summary, 300), changes: later, received: Date.now() }, null, 1));
    await move(inbox, name, await sub(dir, 'inbox/done'), text);
    if (undo && undo.what) toast('Claude ' + undo.what + ' in ' + p.name + '.' + (later.length ? ' It asks about more on the building.' : ''), '', { label: 'Undo', run: () => undoNow(p, undo) });
    else if (later.length) toast('Claude asks about changes to ' + p.name + ': see its building.');
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
  function applyNow(p, changes, summary) {
    const before = { todos: new Set(p.todos.map(t => t.id)), ms: new Set(p.milestones.map(m => m.id)) };
    const added = { notes: [], links: [] };
    let tasks = 0;
    for (const c of changes) {
      if (c.do === 'add-tasks') {
        let list;
        try { list = readTasks({ tasks: c.tasks }).tasks; } catch (e) { continue; }
        const name = str(c.milestone, 120), have = name && p.milestones.find(m => keyOf(m.name) === keyOf(name));
        const cur = currentGroup(p), target = have ? { id: have.id } : name ? { name } : cur && cur.ms ? { id: cur.ms.id } : p.milestones[0] ? { id: p.milestones[p.milestones.length - 1].id } : { name: 'To do' };
        addTasks(p, list, target);
        tasks += list.length;
      } else if (c.do === 'add-note') {
        const title = str(c.title, 200), text = str(c.text, 8000);
        if (!title && !text) continue;
        const n = { id: uid('n'), title, text, at: Date.now() };
        p.notes.push(n); added.notes.push(n.id);
        logActivity(p, 'Claude wrote a note' + (title ? ': ' + title : ''));
      } else if (c.do === 'add-link') {
        const url = str(c.url, 2000);
        if (!url || p.links.some(l => addressKey(l.url) === addressKey(url))) continue;
        const l = { id: uid('l'), label: str(c.label, 120), url, icon: LINK_ICONS.includes(c.icon) ? c.icon : guessIcon(url), shortcut: true };
        p.links.push(l); added.links.push(l.id);
        logActivity(p, 'Claude added a link: ' + (l.label || suggestLabel(url)));
      }
    }
    const bits = [tasks && 'added ' + plural(tasks, 'task', 'tasks'), added.notes.length && (tasks ? 'a note' : 'wrote a note'), added.links.length && (tasks || added.notes.length ? plural(added.links.length, 'link', 'links') : 'added ' + plural(added.links.length, 'link', 'links'))].filter(Boolean);
    const what = bits.length > 1 ? bits.slice(0, -1).join(', ') + ' and ' + bits[bits.length - 1] : bits[0] || '';
    if (what && summary) logActivity(p, 'Claude: ' + summary);
    if (what) window.changed(p);
    return { what, todos: p.todos.filter(t => !before.todos.has(t.id)).map(t => t.id), ms: p.milestones.filter(m => !before.ms.has(m.id)).map(m => m.id), ...added };
  }
  function undoNow(p, u) {
    const drop = new Set(u.todos), notes = new Set(u.notes), links = new Set(u.links);
    p.todos = p.todos.filter(t => !drop.has(t.id));
    p.notes = p.notes.filter(n => !notes.has(n.id));
    p.links = p.links.filter(l => !links.has(l.id));
    p.milestones = p.milestones.filter(m => !u.ms.includes(m.id) || p.todos.some(t => t.milestoneId === m.id));
    logActivity(p, 'Undid what Claude added');
    window.changed(p);
    if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render();
    toast('Took back what Claude added to ' + p.name + '.');
  }

  /* ---------- what asks first ---------- */
  function readable(p, c) {
    if (c.do === 'done') { const t = taskNamed(p, c.task); return { text: 'Tick off: ' + str(c.task, 200), ok: !!t, why: t ? '' : 'not open in this project' }; }
    if (c.do === 'edit-description') { const t = taskNamed(p, c.task, false); return { text: 'New description for ' + str(c.task, 200) + ': ' + str(c.description, 8000).replace(/\s+/g, ' ').slice(0, 140), ok: !!t, why: t ? '' : 'no task by that name' }; }
    if (c.do === 'replace-plan') {
      try { const plan = readPlan(c.plan); return { text: 'Replace the plan: ' + plural(plan.milestones.length, 'milestone', 'milestones') + ', ' + plural(plan.milestones.reduce((n, m) => n + m.tasks.length, 0), 'task', 'tasks') + '. The About, milestones and tasks are replaced.', ok: true, plan }; }
      catch (e) { return { text: 'Replace the plan', ok: false, why: e.message }; }
    }
    return { text: c.do, ok: false, why: 'unknown' };
  }
  async function apply(entry) {
    const p = projectNamed(entry.project), dir = ClaudeWork.folder();
    if (!p || !dir) return;
    let n = 0;
    for (const c of entry.changes) {
      const r = readable(p, c);
      if (!r.ok) continue;
      if (c.do === 'done') { const t = taskNamed(p, c.task); t.done = true; t.doneAt = Date.now(); markWorked(p); logActivity(p, 'Done: ' + t.text); }
      else if (c.do === 'edit-description') { const t = taskNamed(p, c.task, false); t.description = str(c.description, 8000); logActivity(p, 'Claude updated the description of ' + t.text); }
      else if (c.do === 'replace-plan') applyPlan(p, r.plan);
      n++;
    }
    if (n) { if (entry.summary) logActivity(p, 'Claude: ' + entry.summary); window.changed(p); if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render(); }
    await settle(dir, entry, 'applied');
    toast(n ? 'Applied what Claude asked in ' + p.name + '.' : 'Nothing in it could be applied, so it was put away.');
  }
  async function dismiss(entry) {
    const dir = ClaudeWork.folder();
    if (!dir) return;
    await settle(dir, entry, 'dismissed');
    toast('Dismissed what Claude asked.');
  }
  async function settle(dir, entry, how) {
    try {
      const pend = await sub(dir, 'inbox/pending');
      await move(pend, entry.name, await sub(dir, 'inbox/done'), JSON.stringify({ ...entry, [how]: Date.now() }, null, 1));
    } catch (e) { /* already settled by another tab */ }
    pending = pending.filter(x => x.name !== entry.name);
    pendingSig = pending.map(x => x.name).join('|');
    ClaudeWork.redraw();
  }

  /* What waits for this building, for its card and its bubble. */
  const forProject = p => pending.filter(x => keyOf(x.project) === keyOf(p.name));
  function cards(p) {
    return forProject(p).map(entry => h('div', { class: 'b-claude b-claude-asks' },
      h('p', { class: 'b-claude-line' }, h('span', { class: 'b-claude-dot', 'aria-hidden': 'true' }),
        h('span', null, 'Claude asks first' + (entry.summary ? ': ' : '.'), entry.summary ? h('bdi', null, entry.summary.replace(/[.!?]+$/, '')) : null, entry.summary ? '. ' : ' ',
          h('span', { class: 'b-claude-when' }, 'Sent ' + relAgo(entry.at) + '.'))),
      h('ul', { class: 'b-claude-list' }, entry.changes.map(c => { const r = readable(p, c); return h('li', { class: r.ok ? null : 'off', dir: 'auto', title: r.why || null }, r.text, r.ok ? null : ' (' + r.why + ')'); })),
      h('div', { class: 'b-claude-acts' },
        h('button', { class: 'btn btn-small b-claude-apply', type: 'button', onclick: () => apply(entry) }, 'Apply'),
        h('button', { class: 'btn btn-small btn-quiet b-claude-dismiss', type: 'button', onclick: () => dismiss(entry) }, 'Dismiss'))));
  }
  return { poll, cards, count: p => forProject(p).length, total: () => pending.length, pending: () => pending, AT_ONCE, ASK };
})();
