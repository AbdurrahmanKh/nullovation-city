/* T3 Code (0.1.87, T3 Connection, Round 1): Open in Claude's T3 tile starts a T3 Code thread in the building's folder
   with the task already sent (A1, Sent for you), through a link per send (A1a). A web page cannot run a program, so a
   one-time setup on the PC (Settings, Links, T3 Code) adds the link type nullovation-t3: and the helper it runs. The
   city writes the send into the Claude folder as t3/send-<id>.json and follows a link that names only that file; the
   helper runs T3's own t3 thread start and writes what T3 said back as t3/<id>.done.json, which the city reads within
   a second: the building's leader says it was sent, with Open, which shows the thread in T3 (C2, now). So the Claude
   folder must be connected, with the city let to write there. The agent and model come from a pick kept per building,
   as its folder is (A2). Which tiles the panel shows is a setting, T3 and Claude, T3 only or Claude only (A3, his
   note: "when you disable claude, only Copy stay"). A building with no folder link gets the tile greyed out, saying
   why (B1). The phone keeps Copy (D1). */
const T3 = (() => {
  const AGENT_KEY = 'nullovation-city:t3Agent';      // the agent and model picked in each building, in this browser
  const TILES_KEY = 'nullovation-city:openTiles';    // which tiles Open in Claude shows: both, t3 or claude
  const SETTLE_KEY = 'nullovation-city:t3Settle';    // '0' when ticking a task leaves its T3 threads as they are (0.1.98)
  const SUB = 't3', EVERY = 1000;
  let TAKE_MS = 15000, RUN_MS = 180000;              // nobody took the send; no answer from T3 after it was taken
  /* What a send can name. Only Claude is turned on in T3 on Abdurrahman's PC (16 November 2026); T3's default is the
     agent and model T3 starts a new thread with, set in T3's own settings, with its effort. */
  const AGENTS = [
    { id: 'default', label: "T3's default", short: 'default', hint: "The agent and model T3 starts a new thread with, and its effort, as T3's settings say" },
    { id: 'claude-opus-5-5', provider: 'claudeAgent', model: 'claude-opus-5-5', label: 'Claude Opus 5.5', short: 'Opus 5.5', hint: 'Claude, in T3, on Opus 5.5' },
    { id: 'claude-sonnet-5-5', provider: 'claudeAgent', model: 'claude-sonnet-5-5', label: 'Claude Sonnet 5.5', short: 'Sonnet 5.5', hint: 'Claude, in T3, on Sonnet 5.5' },
    { id: 'claude-haiku-5-5', provider: 'claudeAgent', model: 'claude-haiku-5-5', label: 'Claude Haiku 5.5', short: 'Haiku 5.5', hint: 'Claude, in T3, on Haiku 5.5' },
  ];
  const TILES = [
    { value: 'both', label: 'T3 and Claude', hint: "The T3 tile first, then the Claude app's Chat, Cowork, Code and Terminal, and Copy" },
    { value: 't3', label: 'T3 only', hint: 'The T3 tile and Copy' },
    { value: 'claude', label: 'Claude only', hint: "The Claude app's Chat, Cowork, Code and Terminal, and Copy, with no T3 tile" },
  ];
  const TILE_NOTES = { both: "Open in Claude shows the T3 tile first, then the Claude app's tiles and Copy.",
    t3: "Open in Claude shows the T3 tile and Copy; the Claude app's tiles are off.", claude: "Open in Claude shows the Claude app's tiles and Copy, with no T3 tile." };

  /* ---------- the settings ---------- */
  function tiles() { try { const v = localStorage.getItem(TILES_KEY); return v === 't3' || v === 'claude' ? v : 'both'; } catch (e) { return 'both'; } }
  function setTiles(v) { try { if (v === 't3' || v === 'claude') localStorage.setItem(TILES_KEY, v); else localStorage.removeItem(TILES_KEY); } catch (e) { /* this visit only */ } }
  function settles() { try { return localStorage.getItem(SETTLE_KEY) !== '0'; } catch (e) { return true; } }
  function setSettles(v) { try { if (v) localStorage.removeItem(SETTLE_KEY); else localStorage.setItem(SETTLE_KEY, '0'); } catch (e) { /* this visit only */ } }
  function saved() { try { const v = JSON.parse(localStorage.getItem(AGENT_KEY) || '{}'); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } }
  const agentOf = p => AGENTS.find(a => a.id === (p ? saved()[p.id] : '')) || AGENTS[0];
  function keepAgent(p, id) {
    if (!p) return;
    const v = saved();
    if (id && id !== AGENTS[0].id && AGENTS.some(a => a.id === id)) v[p.id] = id; else delete v[p.id];
    try { localStorage.setItem(AGENT_KEY, JSON.stringify(v)); } catch (e) { /* this visit only */ }
  }
  /* Why a send cannot go now, or '' when it can: it goes through the Claude folder, which the city must be let to
     write in. */
  function why() {
    if (typeof ClaudeWork === 'undefined') return 'T3 sends go through the Claude folder';
    if (ClaudeWork.folder()) return '';
    if (ClaudeWork.state() === 'unsupported') return 'T3 sends go through the Claude folder, which works in Chrome and Edge';
    return 'T3 sends go through the Claude folder: connect it in Settings, Links, and let the city write there';
  }

  /* ---------- a send ---------- */
  const threadHref = (env, thread) => 't3code://threads/' + encodeURIComponent(env) + '/' + encodeURIComponent(thread);
  function follow(href) { const a = h('a', { href, hidden: true }); document.body.append(a); a.click(); a.remove(); }
  const newId = () => Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  const pending = new Map();                          // id -> { p, title, at, test, taken }
  let timer = 0;

  /* ---------- a task's threads (0.1.90, City as My Terminal, Round 1, A1) ---------- */
  /* Every task keeps the threads its sends started (t.threads, read by readThreads in 20-model.js), so Build it goes on
     in the task's thread, Think's included, and Open on the task, its row and its leader's news reaches it. A thread
     started in T3 itself belongs to no task, for now (A2). */
  const threadsOf = t => (t && Array.isArray(t.threads) ? [...t.threads].sort((a, b) => b.last - a.last) : []);
  const latest = t => threadsOf(t)[0] || null;
  /* ---------- what the watcher sees (0.1.93, T3 Connection Research, Round 2, W2) ---------- */
  /* The watcher, a small program the T3 setup starts at sign-in (W2a), writes Claude's T3 threads into the Claude
     folder as t3/watch.json every few seconds while T3 is open: each thread's state, its folder, its latest message,
     and what it asks while it waits. The city reads it every 3 seconds, as it reads Claude's hooks. It is live while
     written in the last 90 seconds (the watcher writes at least every 30). */
  const WATCH_EVERY = 3000, WATCH_STALE = 90e3;
  let watched = null, watchT = 0, watchBusy = false;
  async function readWatch() {
    clearTimeout(watchT);
    if (!watchBusy && typeof ClaudeWork !== 'undefined' && ClaudeWork.folder() && !document.hidden) {
      watchBusy = true;
      let d = null;
      try { d = JSON.parse(await ClaudeWork.read(SUB + '/watch.json')); } catch (e) { d = null; }
      if (d && d.app === 'nullovation-city' && d.kind === 't3-watch' && typeof d.at === 'number') {
        const threads = Array.isArray(d.threads) ? d.threads.filter(x => x && typeof x.id === 'string') : [];
        const sig = JSON.stringify([d.running, d.error || '', d.organizeError || '', threads]), moved = !watched || watched.sig !== sig;
        watched = { at: d.at, running: !!d.running, error: typeof d.error === 'string' ? d.error : '', t3: typeof d.t3 === 'string' ? d.t3 : '', threads, sig,
          byId: new Map(threads.map(x => [x.id, x])), organizes: d.organizes === 1, organizeError: typeof d.organizeError === 'string' ? d.organizeError : '' };
        organized(Array.isArray(d.organized) ? d.organized : []);
        if (moved) watchMoved();
      }
      watchBusy = false;
    }
    watchT = setTimeout(readWatch, WATCH_EVERY);
  }
  setTimeout(readWatch, 1500);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) readWatch(); });
  const watchLive = () => !!watched && Date.now() - watched.at < WATCH_STALE;
  const watchedThread = id => (id && watchLive() && watched.running ? watched.byId.get(id) || null : null);
  function watchMoved() {
    if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.refreshThreads();
    if (typeof AllTasks !== 'undefined') AllTasks.refresh();
    if (typeof Bubble !== 'undefined') Bubble.refresh();
    if (typeof Leaders !== 'undefined') Leaders.redrawCard();
    if (typeof News !== 'undefined') News.renderSection();             // a leader at work names its thread by its title (0.1.97)
    if (typeof Settings !== 'undefined' && Settings.isOpen()) Settings.refresh();
  }
  /* The watcher in Settings, Links: what it sees now, or what is missing. */
  function watchWords() {
    if (!watched) return 'Watcher: not heard from on this PC. Run the T3 setup again to start it, then keep T3 open.';
    if (!watchLive()) return 'Watcher: last heard from ' + relAgo(watched.at) + '. It starts when you sign in; the T3 setup starts it again.';
    if (!watched.running) return 'Watcher: T3 is closed, so it rests.';
    if (watched.error) return 'Watcher: T3 is open, but its last look failed: ' + watched.error;
    const n = watched.threads.length;
    return 'Watcher: sees ' + plural(n, 'Claude thread', 'Claude threads') + (watched.t3 ? ' in T3 v' + watched.t3 : ' in T3') + ', looking every few seconds.'
      + (watched.organizeError ? ' Settling threads failed: ' + watched.organizeError : '');
  }

  /* ---------- settling a task's threads (0.1.98, "Ticking the task also closes the T3") ---------- */
  /* Ticking a task off settles its T3 threads, and reopening it makes them active again (tickTask and untickTask in
     22-repeat.js, wherever a task is ticked). The city writes what it asks into the Claude folder as
     t3/organize-<id>.json, all of one moment's ticks in one; the watcher takes it and asks T3, settling a thread once
     Claude's turn there has ended. Each thread keeps when it was asked to settle (th.settled), so reopening the task
     unsettles only the threads its tick settled. Not on a phone, which has no Claude folder. */
  const organizing = new Map();                       // thread id -> 'settle' or 'unsettle', until written
  let orgT = 0, orgWarned = false;
  const isTicked = t => !!(t && (t.done || (typeof isWaiting === 'function' && isWaiting(t))));
  function organizeTask(p, t, settle) {
    if (!settles() || !t || !Array.isArray(t.threads) || !t.threads.length || typeof ClaudeWork === 'undefined' || !ClaudeWork.folder()) return;
    const now = Date.now();
    for (const th of t.threads) {
      if (!th || !th.id || !!th.settled === settle) continue;
      if (settle) th.settled = now; else delete th.settled;
      organizing.set(th.id, settle ? 'settle' : 'unsettle');
    }
    if (organizing.size) { clearTimeout(orgT); orgT = setTimeout(writeOrganize, 0); }
  }
  const ticked = (p, t) => organizeTask(p, t, true);
  const unticked = (p, t) => organizeTask(p, t, false);
  async function writeOrganize() {
    const settle = [], unsettle = [];
    for (const [id, d] of organizing) (d === 'settle' ? settle : unsettle).push(id);
    organizing.clear();
    if (!settle.length && !unsettle.length) return;
    if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.refreshThreads();   // its rows say it now
    if (typeof AllTasks !== 'undefined') AllTasks.refresh();
    const id = newId();
    try {
      await ClaudeWork.write(SUB + '/organize-' + id + '.json', JSON.stringify({ app: 'nullovation-city', kind: 't3-organize', version: 1, id, at: Date.now(), settle, unsettle }));
    } catch (e) {
      toast('The city could not reach T3 through the Claude folder' + (e && e.name ? ' (' + e.name + ')' : '') + ', so its T3 thread stays as it is.', 'error');
      return;
    }
    /* said once a visit, and only when T3 will not take it soon: the tick's own toast, with its Undo, comes first */
    if (orgWarned) return;
    const w = watchLive() ? watched : null;
    const say = !w ? 'The T3 watcher is not running, so the task\'s T3 thread settles once it runs. The T3 setup starts it, in Settings, Links.'
      : !w.organizes ? 'Run the T3 setup again, in Settings, Links, so ticking a task settles its T3 thread.' : '';
    if (say) { orgWarned = true; setTimeout(() => toast(say, 'error'), 1500); }
  }
  /* What the watcher did, from watch.json: a thread T3 would not settle or unsettle loses its mark, and is said once. */
  const orgSeen = new Set(), orgFrom = Date.now() - 60e3, orgDone = new Map();   // thread id -> when T3 last settled it for a tick
  function organized(list) {
    for (const r of list) {
      if (!r || typeof r.thread !== 'string' || typeof r.at !== 'number') continue;
      if (r.ok === true) { if (r.do === 'settle') orgDone.set(r.thread, Math.max(r.at, orgDone.get(r.thread) || 0)); continue; }
      if (r.ok !== false) continue;
      const key = r.thread + ':' + r.at;
      if (orgSeen.has(key)) continue;
      orgSeen.add(key);
      for (const p of typeof DB !== 'undefined' ? DB.projects : []) for (const t of p.todos) for (const th of Array.isArray(t.threads) ? t.threads : []) {
        if (th.id !== r.thread) continue;
        if (r.do === 'settle' && th.settled && th.settled <= r.at) { delete th.settled; changed(p, { touch: false }); }
        if (r.at >= orgFrom) toast('T3 did not ' + (r.do === 'unsettle' ? 'make the T3 thread of ' + t.text + ' active again' : 'settle the T3 thread of ' + t.text) + (r.error ? ': ' + r.error : '.'), 'error');
      }
    }
  }
  /* A T3 thread's state in the city's words: working, waiting, failed or done. */
  const T3_STATE = { preparing: 'working', queued: 'working', starting: 'working', running: 'working', waiting: 'waiting', completed: 'done', idle: 'done',
    failed: 'failed', interrupted: 'failed', cancelled: 'failed', rolled_back: 'failed' };
  /* The thread a session of Claude Code's runs in, for a session in T3 (its hooks name T3 as where it was started): the
     task's thread when the session is on a task that has one, else the one watched thread at work in the session's
     folder, or the one in it last busy near the session's last word; none when that is not plain (A2: threads started
     in T3 itself belong to no task, but they show on their building, W2c). */
  function sessionThread(p, s) {
    if (!s || !watchLive() || !watched.running) return null;
    const t = typeof ClaudeWork !== 'undefined' ? ClaudeWork.taskOf(p, s) : null, th = t && latest(t);
    if (th && watched.byId.has(th.id)) return watched.byId.get(th.id);
    if (s.entry && s.entry !== 't3-code') return null;
    const k = typeof ClaudeWork !== 'undefined' ? ClaudeWork.pathKey(s.cwd) : '';
    if (!k) return null;
    const here = watched.threads.filter(x => ClaudeWork.pathKey(x.folder) === k);
    const busy = here.filter(x => T3_STATE[x.status] === 'working' || T3_STATE[x.status] === 'waiting');
    if (s.state === 'working' || s.state === 'waiting') {
      /* two at work in one building: the one in the same state, waiting with waiting, else the one its title names */
      if (busy.length === 1) return busy[0];
      const same = busy.filter(x => (T3_STATE[x.status] === 'waiting') === (s.state === 'waiting'));
      if (same.length === 1) return same[0];
      const ask = String(s.ask || s.task || '').trim().toLowerCase();
      const named = (same.length ? same : busy).filter(x => ask && x.title && ask.startsWith(String(x.title).trim().toLowerCase().slice(0, 40)));
      return named.length === 1 ? named[0] : null;
    }
    const near = here.filter(x => Math.abs((x.updated || 0) - s.at) < 3 * 60e3);
    return near.length === 1 ? near[0] : null;
  }
  /* The latest message a watched thread holds, its text plain. */
  const lastOf = w => (w && w.last && typeof w.last.text === 'string' ? w.last.text : '');

  /* Where Open lands, said before the click (Brainstorm 1, Round 2, i1): the agent, and the thread's state. Since 0.1.93
     each thread's own state comes from the watcher while it runs; without it, the latest thread's is the task's Claude
     session, from Claude's hooks: the one working, waiting or done on it; with neither, when it was last sent. */
  const STATE_RANK = { waiting: 0, working: 1, failed: 2, done: 3 };
  const STATE_WORDS = { waiting: 'waiting on you', approval: 'waiting for your OK', working: 'working', failed: 'stopped on an error', done: 'handed back to you' };
  function hookState(p, t) {
    if (!p || !t || typeof ClaudeWork === 'undefined') return '';
    const mine = ClaudeWork.sessionsOf(p).filter(s => STATE_RANK[s.state] != null && ClaudeWork.taskOf(p, s) === t);
    mine.sort((a, b) => STATE_RANK[a.state] - STATE_RANK[b.state] || b.at - a.at);
    return mine.length ? mine[0].state : '';
  }
  function threadState(p, t, th) {
    const w = th && watchedThread(th.id);
    if (w) return w.status === 'waiting' && w.approval ? 'approval' : T3_STATE[w.status] || '';
    return th && th === latest(t) ? hookState(p, t) : '';
  }
  const stateOf = (p, t) => threadState(p, t, latest(t));
  function whereOf(p, t, th = latest(t)) {
    if (!th) return '';
    const st = threadState(p, t, th), w = watchedThread(th.id);
    let words = st ? STATE_WORDS[st] : 'sent ' + relAgo(th.last);
    /* settled (0.1.98): as T3 says while the watcher sees it, else as the tick asked; asked while Claude is at it, it
       settles when the turn ends */
    if (w && w.settled) words = 'settled';
    /* (settled for the tick and busy again since, in T3 itself: as it is) */
    else if (th.settled && !(w && (orgDone.get(th.id) || 0) >= th.settled)) words = st === 'working' || st === 'waiting' || st === 'approval' ? words + ', settles when its turn ends' : w ? 'settling' : 'settled';
    return (th.agent ? (th.agent === 'default' ? "T3's default agent" : th.agent) + ', ' : '') + words;
  }
  function openThread(th) { if (th && th.id && th.env) follow(threadHref(th.env, th.id)); }
  const openTitle = (p, t, th = latest(t)) => 'Opens its T3 thread' + (th.title ? ', ' + th.title : '') + ': ' + whereOf(p, t, th) + '.';
  /* The T3 mark on a task's row, as the hat is for a round: a click opens its latest thread, its tooltip saying where. */
  function rowButton(p, t, cls = '') {
    const th = latest(t);
    if (!th || !th.env) return null;
    const st = stateOf(p, t);
    return h('button', { class: 'icon-btn t3-open' + (st ? ' ' + (st === 'approval' ? 'waiting' : st) : '') + (cls ? ' ' + cls : ''), type: 'button', 'data-task': t.id, 'aria-label': 'Open in T3: ' + t.text,
      title: openTitle(p, t, th), html: iconSvg('t3', 12),
      onclick: e => { e.stopPropagation(); openThread(th); } });
  }
  /* A task's threads in its panel, newest first: each says where it lands and opens it. */
  function taskList(p, t) {
    const all = threadsOf(t).filter(th => th.env);
    if (!all.length) return null;
    const row = th => h('button', { class: 't3-thread', type: 'button', 'data-thread': th.id, title: openTitle(p, t, th), onclick: () => openThread(th) },
      h('span', { class: 'ic', 'aria-hidden': 'true', html: iconSvg('t3', 14) }),
      h('span', { class: 't3-thread-text' }, h('span', { class: 't3-thread-title', dir: 'auto' }, th.title || t.text), h('span', { class: 't3-thread-where' }, whereOf(p, t, th)),
        /* its latest message, while the watcher sees it (W2c) */
        lastOf(watchedThread(th.id)) ? h('span', { class: 't3-thread-last', dir: 'auto' }, (typeof News !== 'undefined' ? News.plainReply(lastOf(watchedThread(th.id))) : lastOf(watchedThread(th.id)))) : null));
    const box = h('div', { class: 'pv-t3-sec' }, h('span', { class: 'lbl' }, all.length > 1 ? 'T3 threads' : 'T3 thread'));
    const SHOW = 3;
    box.append(...all.slice(0, SHOW).map(row));
    if (all.length > SHOW) {
      const more = h('button', { class: 'btn btn-small btn-plain t3-more', type: 'button', onclick: () => { more.replaceWith(...all.slice(SHOW).map(row)); } }, 'Show all ' + all.length);
      box.append(more);
    }
    return box;
  }
  /* The task a send was for, found again once T3 answers: by its id, in its project. */
  function taskById(ref) {
    if (!ref || typeof DB === 'undefined') return {};
    const p = DB.projects.find(x => x.id === ref.pid), t = p && p.todos.find(x => x.id === ref.tid);
    return t ? { p, t } : {};
  }
  /* Keeps the thread on its task: a new one added, one sent to again brought up to date. Not work: Updated, urgency and
     Activity stay, as for a pin. */
  function keepThread(ref, a, s) {
    const { p, t } = taskById(ref);
    if (!p || !a.thread) return;
    const now = Date.now(), list = Array.isArray(t.threads) ? t.threads : [];
    const had = list.find(x => x.id === a.thread);
    if (had) { had.last = now; if (a.env) had.env = a.env; delete had.settled; }   // sent to again: active, and a new tick settles it
    else list.push({ id: String(a.thread), env: String(a.env || ''), agent: s.agent || '', kind: s.kind || 'build', title: s.title.slice(0, 120), at: now, last: now });
    t.threads = readThreads({ threads: list }).threads || [];
    changed(p, { touch: false });
    if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.refreshThreads();
    if (typeof AllTasks !== 'undefined') AllTasks.refresh();
  }

  /* Writes the send, then follows its link while the click still counts as the user's, as a browser asks before it
     opens a link type of the PC's. With a thread, the helper sends it into that thread (t3 thread send) rather than
     starting one; a task's send names the task, so the thread it lands in is kept on it. */
  async function send({ project: p, folder, text, title, agent, task = null, thread = null, kind = 'build' }) {
    const no = why();
    if (no) { toast(no + '.', 'error'); return false; }
    if (!folder && !thread) { toast("T3 starts a thread in the building's folder: add a link to a folder on this computer.", 'error'); return false; }
    const a = agent || agentOf(p), id = newId(), name = String(title || '').trim() || 'the task';
    const doc = { app: 'nullovation-city', kind: 't3-send', version: 1, id, at: Date.now(), project: p ? p.name : '', folder, title: name.slice(0, 80), message: text,
      ...(thread ? { thread: thread.id } : a.provider ? { provider: a.provider, model: a.model } : {}) };
    try { await ClaudeWork.write(SUB + '/send-' + id + '.json', JSON.stringify(doc)); } catch (e) {
      toast('The city could not write the send into the Claude folder' + (e && e.name ? ' (' + e.name + ')' : '') + '.', 'error');
      return false;
    }
    follow('nullovation-t3:send/' + id);
    const tname = task ? task.text : name;
    pending.set(id, { p, title: name, at: Date.now(), test: false, taken: false, name: tname, kind, thread: thread ? thread.id : '',
      agent: thread ? thread.agent : a.short, ref: task && p ? { pid: p.id, tid: task.id } : null,
      args: { project: p, folder, text, title, agent: a, task, thread, kind } });
    toast(thread ? 'Sending ' + tname + ' to its T3 thread.' : 'Sending ' + name + ' to T3' + (a.provider ? ', on ' + a.label : '') + '.');
    watch(0);
    return true;
  }
  /* ---------- talking back (0.1.94, City as My Terminal, Round 1, R1 to R3) ---------- */
  /* A reply or an answer goes as a send does: written into the Claude folder, its link followed on the click, the
     helper doing it in T3. A reply names its mode: steer (a running turn, R2), auto (an idle thread starts on it) or
     queue (the next turn, R2); an answer names the request and each question's answer (R3, i6). */
  async function talk(p, w, doc, say) {
    const no = why();
    if (no) { toast(no + '.', 'error'); return false; }
    if (!w || !w.id) return false;
    const id = newId(), name = String(w.title || '').trim() || 'its thread';
    const full = { app: 'nullovation-city', kind: 't3-send', version: 1, id, at: Date.now(), project: p ? p.name : '', folder: w.folder || '', title: name.slice(0, 80), thread: w.id, ...doc };
    try { await ClaudeWork.write(SUB + '/send-' + id + '.json', JSON.stringify(full)); } catch (e) {
      toast('The city could not write it into the Claude folder' + (e && e.name ? ' (' + e.name + ')' : '') + '.', 'error');
      return false;
    }
    follow('nullovation-t3:send/' + id);
    pending.set(id, { p, title: name, name, at: Date.now(), test: false, taken: false, talk: true, action: doc.action, mode: doc.mode || '', request: doc.request || '', env: w.env, thread: w.id });
    toast(say);
    watch(0);
    return true;
  }
  const reply = (p, w, text, mode) => talk(p, w, { action: 'reply', mode, message: text },
    mode === 'steer' ? 'Steering Claude on ' + (w.title || 'its thread') + '.' : mode === 'queue' ? 'Queuing it for Claude’s next turn.' : 'Sending it to Claude.');
  const answer = (p, w, request, answers) => talk(p, w, { action: 'answer', request, answers }, 'Answering Claude on ' + (w.title || 'its thread') + '.');
  function saidTalk(s, a) {
    const lead = s.p && typeof Leaders !== 'undefined' ? Leaders.toastLead(s.p) : null;
    const open = s.env && s.thread ? [{ label: 'Check T3', run: () => follow(threadHref(s.env, s.thread)) }] : [];        // Check T3, Round 1, M2: the name everywhere
    if (!a.ok) {
      if (s.request && typeof News !== 'undefined') News.unanswer(s.request);
      toast(String(a.error || 'T3 did not take it.'), 'error', a.down ? [{ label: 'Open T3', run: () => follow(s.env && s.thread ? threadHref(s.env, s.thread) : 't3code://new') }] : open);
      return;
    }
    const words = s.action === 'answer' ? 'Answered Claude on ' + s.name + '.'
      : a.queued && s.mode === 'steer' ? 'T3 took it as Claude’s next turn on ' + s.name + ': the turn could not be steered.'
      : s.mode === 'steer' ? 'Steered Claude on ' + s.name + '.' : s.mode === 'queue' ? 'Queued for Claude’s next turn on ' + s.name + '.' : 'Sent to Claude on ' + s.name + '.';
    toast(words, '', open, { lead });
    readWatch();
  }
  /* Settings' Test T3 link: the helper answers, saying whether T3's command is there and T3 is running. */
  async function test() {
    if (why()) { toast('Connect the Claude folder first, in Claude Code at work above, and let the city write there: T3 sends go through it.', 'error'); return false; }
    const id = newId();
    follow('nullovation-t3:test/' + id);
    pending.set(id, { p: null, title: '', at: Date.now(), test: true, taken: true });
    toast('Asking the T3 helper to answer.');
    watch(0);
    return true;
  }
  function watch(ms = EVERY) { clearTimeout(timer); if (pending.size) timer = setTimeout(poll, ms); }
  let busy = false;
  async function poll() {
    if (busy) return watch();
    busy = true;
    const now = Date.now();
    for (const [id, s] of [...pending]) {
      let answer = null;
      try { answer = JSON.parse(await ClaudeWork.read(SUB + '/' + id + '.done.json')); } catch (e) { answer = null; }
      if (answer && answer.app === 'nullovation-city' && answer.id === id) {
        pending.delete(id);
        try { await ClaudeWork.remove(SUB + '/' + id + '.done.json'); } catch (e) { /* the helper clears it after a day */ }
        said(s, answer);
        continue;
      }
      if (!s.taken && now - s.at > TAKE_MS) {
        let left = false;
        try { left = (await ClaudeWork.read(SUB + '/send-' + id + '.json')) != null; } catch (e) { left = false; }
        if (left) {
          pending.delete(id);
          try { await ClaudeWork.remove(SUB + '/send-' + id + '.json'); } catch (e) { /* the helper clears it after a day */ }
          toast('T3 did not pick up ' + s.title + '. Has the T3 setup run on this PC? It is in Settings, Links.', 'error');
          continue;
        }
        s.taken = true;                               // the helper took it and T3 is starting the thread
      }
      if (s.test && now - s.at > TAKE_MS) { pending.delete(id); toast('No answer from the T3 helper: the T3 setup has not run on this PC, or the browser did not open the link.', 'error'); continue; }
      if (now - s.at > RUN_MS) { pending.delete(id); toast('No word from T3 on ' + s.title + ' yet. Look in T3 Code.', 'error'); }
    }
    busy = false;
    watch();
  }
  /* ---------- a send held while T3 is closed (0.1.91, City as My Terminal, Round 1, L3) ---------- */
  /* T3 runs only while its app is open. A send it could not take waits, kept while the page stays open, and its
     building's leader says so in a bubble by itself, with Open T3 and Send it; it answers your own click, so it opens
     at once where there is room, and a toast says it where there is not. Sent again, it goes as it would have. */
  const heldSends = new Map();                        // id -> the send's own arguments
  function holdSend(s) {
    const hid = newId(), t = s.args.task, p = s.p;
    heldSends.set(hid, { ...s.args, name: s.name });
    const key = 't3closed:' + p.id + ':' + (t ? t.id : s.name);
    for (const [k, v] of heldSends) if (k !== hid && v.key === key) heldSends.delete(k);   // the same send again replaces the one waiting
    heldSends.get(hid).key = key;
    const it = typeof News !== 'undefined' ? News.add(p, 't3closed', { task: s.name }, { ref: { held: hid, tid: t ? t.id : '', direct: true }, key }) : null;
    setTimeout(() => {
      if (it && News.showing(it.id)) return;
      toast('T3 Code is not running, so ' + s.name + ' waits in News.', 'error', [{ label: 'Open T3', run: () => openApp(hid) }]);
    }, 150);
  }
  const held = id => heldSends.get(id) || null;
  /* T3's window: the task's thread when it has one, else T3's own link for a new thread. Windows starts T3 for it. */
  function openApp(id) {
    const x = held(id), th = x && x.task ? latest(x.task) : null;
    follow(th && th.env ? threadHref(th.env, th.id) : 't3code://new');
  }
  function retry(id) {
    const x = held(id);
    if (!x) return false;
    heldSends.delete(id);
    const { name, key, ...args } = x;
    return send(args);
  }
  function said(s, a) {
    if (s.talk) { saidTalk(s, a); return; }
    if (s.test) {
      toast(a.running ? 'T3 links work, and T3 Code is running.' : a.t3 ? 'T3 links work, but T3 Code is not running: open it before you send.'
        : "T3 links work, but T3 Code's t3 command was not found on this PC: open T3 Code once.", a.running ? '' : 'error');
      return;
    }
    if (!a.ok && s.p && (a.down || /^T3 Code is not running/.test(String(a.error || '')))) { holdSend(s); return; }
    if (!a.ok) { toast(String(a.error || 'T3 could not start the thread.'), 'error'); return; }
    if (s.ref) keepThread(s.ref, a, s);
    /* a send that went makes any held for the same task, or the same title, needless: they go, and their news with them */
    for (const [k, v] of heldSends) if (v.task && s.args.task ? v.task.id === s.args.task.id : v.name === s.name) heldSends.delete(k);
    if (typeof News !== 'undefined') News.renderSection();
    const lead = s.p && typeof Leaders !== 'undefined' ? Leaders.toastLead(s.p) : null;
    const open = a.env && a.thread ? [{ label: 'Check T3', run: () => follow(threadHref(a.env, a.thread)) }] : [];        // Check T3, Round 1, M2: the name everywhere
    /* A helper from before 0.1.90 knows no thread to send into, and starts a new one: said, so the setup runs again. */
    const old = s.thread && a.thread !== s.thread;
    if (s.thread && !old) { toast('Sent to its T3 thread: ' + s.name + '.', '', open, { lead }); return; }
    toast('Sent to T3: ' + s.title + '.' + (a.added ? ' T3 has its folder as a project now.' : '')
      + (old ? ' It started a new thread: run the T3 setup again, in Settings, Links, so the city can send into a task\'s thread.' : ''), '', open, { lead });
  }

  return { AGENTS, TILES, TILE_NOTES, tiles, setTiles, agentOf, keepAgent, why, send, test, threadHref, pending: () => pending.size,
    threadsOf, latest, stateOf, whereOf, openThread, openTitle, rowButton, taskList, held, retry, openApp, reply, answer,
    watched: () => (watchLive() ? watched : null), watchedThread, watchWords, sessionThread, lastOf, T3_STATE,
    openWatched: w => { if (w && w.env && w.id) follow(threadHref(w.env, w.id)); }, readWatch,
    openNew: () => follow('t3code://new'),             // Check T3 with no thread to name: T3 Code itself (0.1.97, F1)
    settles, setSettles, ticked, unticked, isTicked,  // ticking a task settles its T3 threads (0.1.98)
    _test: { times: (take, run) => { TAKE_MS = take; RUN_MS = run; }, warned: v => { orgWarned = !!v; } } };
})();
