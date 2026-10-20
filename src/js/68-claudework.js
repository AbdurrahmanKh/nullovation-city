/*
  Claude Code at work: a bubble over a building while Claude Code works in one of its folders, and when it needs you
  or has finished. Hooks in Claude Code's user settings (the setup in Settings, Links) write one small JSON file per
  session into a folder; this reads that folder every few seconds (Chrome and Edge, like the data file). A session
  belongs to the project whose folder link holds its working folder, the deepest one when several do; failing that,
  to the project named on the "Project:" line of a copy from the city that started it.
  Allowed to write there too (0.1.35), the city keeps city/summary.json, the city without its art, for Claude to read.
  A finish leaves a line in its project's Activity, and the tab's title counts what waits for you (0.1.37).
  The folder belongs to this browser; it does not travel with the city.
*/
const ClaudeWork = (() => {
  const supported = typeof window.showDirectoryPicker === 'function';
  const HANDLE = 'claudeDir', SEEN_KEY = 'nullovation-city:claudeSeen', EVERY = 3000;
  /* How long each state shows after its last event. Working goes quiet after 20 minutes without a word, since an
     interrupt (Esc) ends a turn without telling the hooks; finished and failed show until you look, or for 12 hours. */
  const LASTS = { working: 20 * 60e3, waiting: 8 * 3600e3, done: 12 * 3600e3, failed: 12 * 3600e3 };
  const RANK = { waiting: 4, working: 3, failed: 2, done: 1 };
  let dir = null, state = supported ? 'off' : 'unsupported', timer = 0, busy = false;
  let canWrite = false, summaryAt = 0, summaryErr = '';   // write access, and when the summary was last written
  const files = new Map();                  // file name -> { stamp, s: the session }
  let byProject = new Map(), unplaced = [], lastHeard = 0, marked = true;   // marked: the setup's README is in the folder
  let seen = (() => { try { const v = JSON.parse(localStorage.getItem(SEEN_KEY) || '{}'); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } })();

  async function init() {
    if (!supported) { render(); return; }
    dir = await Store.getHandle(HANDLE);
    if (!dir) { state = 'off'; render(); return; }
    try { state = (await dir.queryPermission({ mode: 'read' })) === 'granted' ? 'on' : 'paused'; } catch (e) { state = 'paused'; }
    await checkWrite();
    render();
    schedule(0);
  }
  async function checkWrite() {
    try { canWrite = !!dir && (await dir.queryPermission({ mode: 'readwrite' })) === 'granted'; } catch (e) { canWrite = false; }
    return canWrite;
  }
  async function choose() {
    let d;
    try { d = await window.showDirectoryPicker({ id: 'nullovation-city-claude', mode: 'readwrite' }); } catch (e) {
      if (e && e.name === 'AbortError') return;
      toast('That folder could not be used. Pick a different folder.', 'error'); return;
    }
    dir = d; state = 'on'; files.clear(); summaryAt = 0;
    const stays = await Store.putHandle(d, HANDLE);
    await checkWrite();
    await poll();
    if (state === 'on') toast(stays ? 'Watching ' + d.name + ' for Claude Code.' : 'Watching ' + d.name + ' until you close this tab. Pick it again next time.');
  }
  async function allow() {
    if (!dir) return;
    try { canWrite = (await dir.requestPermission({ mode: 'readwrite' })) === 'granted'; } catch (e) { canWrite = false; }
    try { state = canWrite || (await dir.queryPermission({ mode: 'read' })) === 'granted' ? 'on' : 'paused'; } catch (e) { state = 'paused'; }
    render();
    if (state === 'on') poll();
  }
  /* Writing is asked for apart from reading, so a folder connected before 0.1.35 keeps its bubbles meanwhile. */
  async function allowWrite() {
    if (!dir) return;
    try { canWrite = (await dir.requestPermission({ mode: 'readwrite' })) === 'granted'; } catch (e) { canWrite = false; }
    summaryAt = 0;
    render();
    if (canWrite) { await writeSummary(); toast('The city writes in ' + dir.name + ' now, so Claude can read it.'); }
  }
  async function stop() {
    dir = null; state = 'off'; files.clear(); clearTimeout(timer); canWrite = false; summaryAt = 0;
    await Store.deleteHandle(HANDLE);
    place(); redraw();
    toast('Stopped watching for Claude Code. The setup on this PC stays until you take it out.');
  }

  /* ---------- reading the folder ---------- */
  function schedule(ms = EVERY) { clearTimeout(timer); timer = setTimeout(poll, ms); }
  async function poll() {
    clearTimeout(timer);
    if (state !== 'on' || !dir || busy) { if (state === 'on') schedule(); return; }
    if (document.hidden) { schedule(); return; }       // nobody is looking: read again when the tab shows
    busy = true;
    let moved = false;
    try {
      const present = new Set();
      let mark = false;
      for await (const [name, fh] of dir.entries()) {
        if (fh.kind === 'file' && name === 'README-nullovation-city.txt') mark = true;
        if (fh.kind !== 'file' || !/\.json$/i.test(name)) continue;
        present.add(name);
        let f;
        try { f = await fh.getFile(); } catch (e) { continue; }          // being swapped by a hook: next time
        const stamp = f.lastModified + ':' + f.size, had = files.get(name);
        if (had && had.stamp === stamp) continue;
        let s = null;
        try { s = sessionOf(JSON.parse(await f.text())); } catch (e) { s = null; }
        files.set(name, { stamp, s });
        moved = true;
      }
      for (const name of [...files.keys()]) if (!present.has(name)) { files.delete(name); moved = true; }
      if (mark !== marked) { marked = mark; moved = true; }
      state = 'on';
    } catch (e) {
      const n = e && e.name;
      state = n === 'NotAllowedError' || n === 'SecurityError' ? 'paused' : 'failed';
      files.clear(); moved = true;
    }
    busy = false;
    const writer = typeof DataFile === 'undefined' || DataFile.isWriter();
    if (canWrite && !summaryAt) writeSummary();
    if (canWrite && typeof ClaudeInbox !== 'undefined' && await ClaudeInbox.poll(dir, writer)) moved = true;
    const placed = place();
    if (writer) logFinishes();
    if (placed || moved) redraw();
    else if (shown()) render();                        // keeps "last heard" true while Settings shows it
    if (state === 'on') schedule();
  }
  function sessionOf(d) {
    if (!d || d.app !== 'nullovation-city' || d.kind !== 'claude-session' || !d.session || typeof d.at !== 'number') return null;
    const str = v => (typeof v === 'string' ? v : '');
    /* A session that finished and then closed (its last reply kept, since a new prompt clears it) still shows its
       tick until you look: the finish is news either way. Closed in the middle of work, it shows nothing. */
    const state = str(d.state) === 'ended' && str(d.reply) ? 'done' : str(d.state);
    /* A turn Claude Code starts on its own (a background task's notice) arrives as a prompt in a tag; it is no ask. */
    const ask = /^\s*<[a-z][\w-]*[\s>]/i.test(str(d.ask)) ? '' : str(d.ask);
    return { session: str(d.session), state, at: d.at, since: typeof d.since === 'number' ? d.since : d.at,
      cwd: str(d.cwd), project: str(d.project), task: str(d.task), ask, reply: str(d.reply) };
  }

  /* ---------- which project a session belongs to ---------- */
  /* One spelling for a local path: backslashes, lower case, no trailing slash. WSL's /mnt/c/... and Git Bash's
     /c/... become C:\... so a session started there still finds its project. */
  function pathKey(p) {
    let s = String(p || '').trim();
    if (!s) return '';
    let m;
    if ((m = s.match(/^\/mnt\/([a-z])(\/.*)?$/i)) || (m = s.match(/^\/([a-z])(\/.*)?$/i))) s = m[1] + ':' + (m[2] || '\\');
    s = s.replace(/\//g, '\\').toLowerCase();
    while (s.length > 3 && s.endsWith('\\')) s = s.slice(0, -1);
    return s;
  }
  function folderIndex() {
    const out = [];
    for (const p of DB.projects) {
      const pl = OpenInClaude.places(p);
      const roots = pl.folders.concat(pl.files.map(f => f.slice(0, f.lastIndexOf('\\'))));
      for (const r of roots) { const k = pathKey(r); if (k) out.push({ k, p }); }
    }
    return out;
  }
  function owner(s, index) {
    const c = pathKey(s.cwd);
    let best = null;
    if (c) for (const e of index) if ((c === e.k || c.startsWith(e.k.endsWith('\\') ? e.k : e.k + '\\')) && (!best || e.k.length > best.k.length)) best = e;
    if (best) return best.p;
    const name = s.project.trim().toLowerCase();
    return name ? DB.projects.find(p => p.name.trim().toLowerCase() === name) || null : null;
  }
  const live = (s, now) => LASTS[s.state] != null && now - s.at <= LASTS[s.state];
  /* Groups the sessions by project. Returns whether anything a viewer sees changed. */
  let lastSig = '';
  function place() {
    const now = Date.now(), index = folderIndex(), next = new Map(), lost = [];
    lastHeard = 0;
    for (const { s } of files.values()) {
      if (!s) continue;
      lastHeard = Math.max(lastHeard, s.at);
      const p = owner(s, index);
      if (!p) { if (now - s.at <= LASTS.done) lost.push(s); continue; }
      if (!live(s, now)) continue;
      if (!next.has(p.id)) next.set(p.id, []);
      next.get(p.id).push(s);
    }
    byProject = next; unplaced = lost.sort((a, b) => b.at - a.at);
    const sig = [...next].map(([id, ss]) => id + ':' + ss.map(s => s.session + s.state + s.at + (isSeen(s) ? 's' : '')).join(',')).join(';') + '|' + lost.map(s => s.session + s.at).join(',');
    const moved = sig !== lastSig;
    lastSig = sig;
    return moved;
  }
  const isSeen = s => (s.state === 'done' || s.state === 'failed') && seen[s.session] >= s.at;

  /* What a building shows: the session that matters most, and how many share its state. With all, finished
     sessions you have already seen count too (the status card shows them; the map does not). */
  function statusOf(p, all = false) {
    const ss = (byProject.get(p.id) || []).filter(s => all || !isSeen(s));
    if (!ss.length) return null;
    const top = Math.max(...ss.map(s => RANK[s.state] || 0));
    const same = ss.filter(s => (RANK[s.state] || 0) === top).sort((a, b) => b.at - a.at);
    return { state: same[0].state, count: same.length, session: same[0], sessions: ss };
  }
  /* What the map's bubble shows: the sessions, and Claude's changes that ask first, which wait for you like a
     session asking a question. */
  function mapStatus(p) {
    const st = statusOf(p), n = typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.count(p) : 0;
    if (!n) return st;
    if (st && st.state === 'waiting') return { ...st, count: st.count + n };
    return { state: 'waiting', count: n + (st && st.state === 'waiting' ? st.count : 0), session: null, sessions: st ? st.sessions : [] };
  }
  /* Looking at a building's status card counts as seeing what Claude Code finished there. */
  function markSeen(id) {
    let any = false;
    for (const s of byProject.get(id) || []) if ((s.state === 'done' || s.state === 'failed') && !(seen[s.session] >= s.at)) { seen[s.session] = s.at; any = true; }
    if (!any) return;
    const keep = new Set([...files.values()].filter(f => f.s).map(f => f.s.session));
    for (const k of Object.keys(seen)) if (!keep.has(k)) delete seen[k];
    try { localStorage.setItem(SEEN_KEY, JSON.stringify(seen)); } catch (e) { /* this visit only */ }
    place();
    MapView.invalidate();
    title();
  }

  /* A finish, once per session and what it worked on, as a line in the project's Activity at the time it finished.
     It makes the building busier for the week, as Activity does; it is not work for urgency (only a tick is). */
  const FIN = 'Claude Code finished';
  function logFinishes() {
    for (const [id, ss] of byProject) {
      const p = DB.projects.find(x => x.id === id);
      if (!p) continue;
      let added = false;
      for (const s of ss) {
        if (s.state !== 'done') continue;
        const what = s.task || s.ask, ref = 'claude:' + s.session + ':' + what.trim().toLowerCase().slice(0, 160);
        if (!Array.isArray(p.activity)) p.activity = [];
        if (p.activity.some(e => e.ref === ref)) continue;
        const e = { at: s.at, text: (what ? FIN + ': ' + what : FIN).slice(0, 300), ref };
        const k = p.activity.findIndex(x => x.at > e.at);
        if (k < 0) p.activity.push(e); else p.activity.splice(k, 0, e);
        if (p.activity.length > ACTIVITY_MAX) p.activity.splice(0, p.activity.length - ACTIVITY_MAX);
        added = true;
      }
      if (added) window.changed(p, { touch: false });
    }
  }

  /* The tab's title: '(2) Nullovation City' while sessions wait for you, finished or stopped unseen, or Claude's
     changes ask first, so it shows from another tab. */
  const TITLE = document.title || 'Nullovation City';
  function waitingCount() {
    let n = 0;
    for (const p of DB.projects) { const ss = (byProject.get(p.id) || []).filter(s => !isSeen(s)); n += ss.filter(s => s.state === 'waiting' || s.state === 'done' || s.state === 'failed').length; }
    return n + (typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.total() : 0);
  }
  function title() {
    const n = waitingCount(), t = n ? '(' + n + ') ' + TITLE : TITLE;
    if (document.title !== t) document.title = t;
  }

  /* The open task a city copy started, in this project, found by its title. */
  function taskOf(p, s) {
    if (!s || !s.task) return null;
    if (s.project && s.project.trim().toLowerCase() !== p.name.trim().toLowerCase()) return null;
    const key = s.task.trim().toLowerCase();
    return p.todos.find(t => isOpenTask(t) && t.text.trim().toLowerCase() === key) || null;
  }
  /* Ticks it off as a tick in the project view does: done now (a repeat on to its next date), work for urgency, a
     line in Activity. */
  function tick(p, t) {
    const was = tickTask(p, t);
    window.changed(p);
    if (t.repeat) repeatToast(p, t, was);
    else toast('Ticked off: ' + t.text + '.');
  }

  /* The line in the status card. */
  function line(p) {
    const st = statusOf(p, true);
    if (!st) return null;
    const s = st.session, what = s.task || s.ask;
    const n = st.count > 1 ? st.count : 0;
    const text = {
      working: (n ? n + ' Claude Code sessions are working' : 'Claude Code is working') + (what ? ': ' : '.'),
      waiting: (n ? n + ' Claude Code sessions need you' : 'Claude Code needs you') + (what ? ': ' : '.'),
      done: 'Claude Code finished' + (what ? ': ' : '.'),
      failed: 'Claude Code stopped on an error' + (what ? ': ' : '.'),
    }[st.state];
    const when = { working: 'Started ', waiting: 'Asked ', done: 'Finished ', failed: 'Stopped ' }[st.state] + relAgo(s.since) + '.';
    return h('div', { class: 'b-claude ' + st.state },
      h('p', { class: 'b-claude-line' }, h('span', { class: 'b-claude-dot', 'aria-hidden': 'true' }),
        h('span', null, text, what ? h('bdi', null, what) : null, what ? '. ' : ' ', h('span', { class: 'b-claude-when' }, when))),
      st.state === 'done' && s.reply ? h('p', { class: 'b-claude-said', dir: 'auto', title: s.reply }, s.reply) : null,
      ...ticks(p, st, what));
  }
  /* Tick it, for each open task a finished session started from: the top line's own task without a name, the
     others named, since a session still working on the building takes the line. */
  function ticks(p, st, what) {
    const out = [], done = new Set();
    for (const s of st.sessions.filter(x => x.state === 'done').sort((a, b) => b.at - a.at)) {
      const t = taskOf(p, s);
      if (!t || done.has(t.id)) continue;
      done.add(t.id);
      const own = st.state === 'done' && t.text === what;
      out.push(h('div', { class: 'b-claude-acts' },
        own ? null : h('span', { class: 'b-claude-fin', dir: 'auto' }, 'Finished: ', h('bdi', null, t.text)),
        h('button', { class: 'btn btn-small b-claude-tick', type: 'button', title: 'Tick off ' + t.text + ', the task this session started from', onclick: () => tick(p, t) }, 'Tick it')));
    }
    return out;
  }

  /* ---------- the city for Claude: city/summary.json, the city without its art ---------- */
  /* Everything Claude needs to name projects and tasks exactly and to see what is next: about a tenth of the data
     file, which is mostly building art. Rewritten a moment after every change, by the tab that writes the data file. */
  function citySummary(now = Date.now()) {
    const iso = ts => (ts ? new Date(ts).toISOString().slice(0, 10) : null);
    return { app: 'nullovation-city', kind: 'city-summary', version: 1, written: new Date(now).toISOString(),
      about: 'Nullovation City, Abdurrahman\'s project tracker, rewrites this file on every change. Each project is a building. '
        + 'To change the city, write a change file into the inbox folder beside this one, as the nullovation-city skill says.',
      leaders: DB.leaders.map(l => ({ name: leaderName(l), role: l.role || '', projects: leaderProjects(l).map(p => p.name) })),
      projects: DB.projects.map(p => {
        const u = urgencyOf(p, now), pl = OpenInClaude.places(p), next = nextTask(p);
        const l = leaderOf(p);
        return { name: p.name, description: p.description || '', deadline: p.deadline || null, folders: pl.folders,
          leader: l ? { name: leaderName(l), role: l.role || '' } : null,                                     // who leads it (0.1.51, L3)
          urgency: { system: urgencyName(p), state: u.color || 'calm', reasons: u.reasons },
          next: next ? next.text : null,
          milestones: groupsOf(p).filter(g => !(g.ms && milestoneArchived(p, g.ms))).map(g => ({ name: g.ms ? g.ms.name : 'No milestone',   // the archive stays out (A3)
            open: g.todos.filter(t => isOpenTask(t, now)).map(t => ({ task: t.text, description: t.description || '', due: t.due || null, ...(t.repeat ? { repeat: repeatText(t.repeat) } : {}) })),
            ...(g.todos.some(t => isWaiting(t, now)) ? { waiting: g.todos.filter(t => isWaiting(t, now)).map(t => ({ task: t.text, repeat: repeatText(t.repeat), back: t.due })) } : {}),
            done: g.todos.filter(t => t.done && !t.archived).map(t => t.text) })),
          notes: p.notes.map(n => ({ title: n.title || '', text: n.text || '', written: iso(n.at) })),
          links: p.links.map(l => ({ label: l.label || suggestLabel(l.url), url: l.url })) };
      }) };
  }
  async function writeFile(path, text) {
    let d = dir;
    const parts = path.split('/');
    for (const part of parts.slice(0, -1)) d = await d.getDirectoryHandle(part, { create: true });
    const w = await (await d.getFileHandle(parts[parts.length - 1], { create: true })).createWritable();
    await w.write(text); await w.close();
  }
  let writing = false;
  async function writeSummary() {
    if (state !== 'on' || !dir || !canWrite || writing) return false;
    if (typeof DataFile !== 'undefined' && !DataFile.isWriter()) return false;      // one tab writes, as for the data file
    writing = true;
    try {
      await writeFile('city/summary.json', JSON.stringify(citySummary(), null, 1));
      summaryAt = Date.now(); summaryErr = '';
    } catch (e) {
      const n = e && e.name;
      if (n === 'NotAllowedError' || n === 'SecurityError') canWrite = false;
      summaryErr = n || 'Error';
    }
    writing = false;
    if (shown()) render();
    return !!summaryAt;
  }
  const cityChanged = debounce(() => writeSummary(), 1500);

  /* ---------- Settings, Links ---------- */
  const shown = () => { const b = $('#claudeBox'); return !!(b && b.offsetParent); };
  function redraw() {
    render();
    title();
    if (typeof MapView !== 'undefined') MapView.invalidate();
    if (typeof Bubble !== 'undefined') Bubble.refresh();
  }
  function render() {
    const box = $('#claudeBox');
    if (box) {
      const name = dir ? dir.name : '', kids = [];
      if (state === 'unsupported') kids.push(h('p', { class: 'save-status' }, 'Claude Code bubbles work in Chrome and Edge.'));
      else if (state === 'off') {
        kids.push(h('button', { id: 'btnClaudeConnect', class: 'btn btn-small', type: 'button', onclick: choose }, 'Connect the Claude folder'));
        kids.push(h('p', { class: 'save-status' }, 'Pick the folder you picked when the setup ran. The setup puts its path on your clipboard.'));
      } else if (state === 'on') {
        kids.push(h('p', { class: 'save-status file-on' }, 'Watching this folder:'));
        kids.push(h('p', { class: 'file-path', dir: 'ltr' }, h('span', { class: 'fp-name' }, name)));
        /* A folder the setup never wrote to: the hooks write somewhere else, so nothing would ever show. */
        if (!marked && !files.size) kids.push(h('p', { id: 'claudeUnmarked', class: 'save-status bad' },
          'Claude Code does not write to this folder: the setup never ran for it. Double-click the setup again and pick ', h('b', { dir: 'auto' }, name), '.'));
        const ss = [...files.values()].map(f => f.s).filter(Boolean), now = Date.now();
        const count = st => ss.filter(s => s.state === st && live(s, now)).length;
        const bits = [count('working') && count('working') + ' working', count('waiting') && count('waiting') + ' waiting for you'].filter(Boolean);
        kids.push(h('p', { class: 'save-status' },
          lastHeard ? 'Last heard from Claude Code ' + relAgo(lastHeard) + '.' + (bits.length ? ' Now: ' + bits.join(', ') + '.' : '') + ' '
            : 'Nothing from Claude Code yet. Once the setup has run, send Claude Code a prompt. ',
          h('button', { class: 'linkish', type: 'button', onclick: stop }, 'Stop')));
        if (!canWrite) kids.push(h('p', { id: 'claudeWrite', class: 'save-status' }, 'So Claude can read the city, let the city write in this folder too. ',
          h('button', { class: 'linkish', type: 'button', onclick: allowWrite }, 'Let it write')));
        else kids.push(h('p', { class: 'save-status' }, summaryAt ? 'Claude can read the city: written ' + relAgo(summaryAt) + '.' : summaryErr ? 'The city could not write here (' + summaryErr + ').' : 'Claude can read the city once it is written.'));
        if (unplaced.length) {
          kids.push(h('p', { class: 'save-status' }, 'Not on a building: add the folder as a link in its project.'));
          kids.push(h('ul', { class: 'claude-lost' }, unplaced.slice(0, 3).map(s => h('li', { dir: 'ltr', title: s.cwd }, s.cwd || '(no folder)'))));
        }
      } else if (state === 'paused') {
        kids.push(h('button', { class: 'btn btn-small', type: 'button', onclick: allow }, 'Allow Claude Code bubbles'));
        kids.push(h('p', { class: 'save-status' }, 'Reading ', h('b', { dir: 'auto' }, name), ' is paused until you allow it. ', h('button', { class: 'linkish', type: 'button', onclick: stop }, 'Stop')));
      } else {
        kids.push(h('button', { class: 'btn btn-small', type: 'button', onclick: choose }, 'Pick the Claude folder again'));
        kids.push(h('p', { class: 'save-status bad' }, 'The Claude folder ', h('b', { dir: 'auto' }, name), ' could not be read: it was moved, renamed, or deleted.'));
      }
      box.replaceChildren(...kids);
    }
    /* Paused or failed shows under the logo too, with its fix, like the data file and the backups. */
    const alertEl = $('#claudeAlert');
    if (alertEl) {
      const name = dir ? dir.name : '';
      if (state === 'paused') alertEl.replaceChildren(h('span', null, 'Claude Code bubbles are paused. '), h('button', { class: 'linkish', type: 'button', onclick: allow }, 'Allow them'));
      else if (state === 'failed') alertEl.replaceChildren(h('span', null, 'The Claude folder ', h('b', { dir: 'auto' }, name), ' could not be read. '), h('button', { class: 'linkish', type: 'button', onclick: choose }, 'Pick it again'));
      else if (state === 'on' && !canWrite) alertEl.replaceChildren(h('span', null, 'Claude cannot read the city until it may write in ', h('b', { dir: 'auto' }, name), '. '), h('button', { class: 'linkish', type: 'button', onclick: allowWrite }, 'Let it write'));
      alertEl.hidden = !(state === 'paused' || state === 'failed' || (state === 'on' && !canWrite));
    }
  }
  document.addEventListener('visibilitychange', () => { if (!document.hidden && state === 'on') poll(); });

  return { init, poll, render, redraw, statusOf, mapStatus, line, markSeen, pathKey, taskOf, cityChanged, citySummary, writeSummary, waitingCount,
    canWrite: () => canWrite, folder: () => (state === 'on' && canWrite ? dir : null), state: () => state,
    sessions: () => [...files.values()].map(f => f.s).filter(Boolean), unplaced: () => unplaced, LASTS };
})();
