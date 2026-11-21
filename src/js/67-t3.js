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
  /* Where Open lands, said before the click (Brainstorm 1, Round 2, i1): the agent, and the thread's state. Until T3
     Connection Research, Round 2 picks how the city reads T3, the state is the task's Claude session, from Claude's
     hooks: the one working, waiting or done on it; with none, when it was last sent. */
  const STATE_RANK = { waiting: 0, working: 1, failed: 2, done: 3 };
  const STATE_WORDS = { waiting: 'waiting on you', working: 'working', failed: 'stopped on an error', done: 'handed back to you' };
  function stateOf(p, t) {
    if (!p || !t || typeof ClaudeWork === 'undefined') return '';
    const mine = ClaudeWork.sessionsOf(p).filter(s => STATE_RANK[s.state] != null && ClaudeWork.taskOf(p, s) === t);
    mine.sort((a, b) => STATE_RANK[a.state] - STATE_RANK[b.state] || b.at - a.at);
    return mine.length ? mine[0].state : '';
  }
  function whereOf(p, t, th = latest(t)) {
    if (!th) return '';
    const st = th === latest(t) ? stateOf(p, t) : '';
    return (th.agent ? (th.agent === 'default' ? "T3's default agent" : th.agent) + ', ' : '') + (st ? STATE_WORDS[st] : 'sent ' + relAgo(th.last));
  }
  function openThread(th) { if (th && th.id && th.env) follow(threadHref(th.env, th.id)); }
  const openTitle = (p, t, th = latest(t)) => 'Opens its T3 thread' + (th.title ? ', ' + th.title : '') + ': ' + whereOf(p, t, th) + '.';
  /* The T3 mark on a task's row, as the hat is for a round: a click opens its latest thread, its tooltip saying where. */
  function rowButton(p, t, cls = '') {
    const th = latest(t);
    if (!th || !th.env) return null;
    const st = stateOf(p, t);
    return h('button', { class: 'icon-btn t3-open' + (st ? ' ' + st : '') + (cls ? ' ' + cls : ''), type: 'button', 'data-task': t.id, 'aria-label': 'Open in T3: ' + t.text,
      title: openTitle(p, t, th), html: iconSvg('t3', 12),
      onclick: e => { e.stopPropagation(); openThread(th); } });
  }
  /* A task's threads in its panel, newest first: each says where it lands and opens it. */
  function taskList(p, t) {
    const all = threadsOf(t).filter(th => th.env);
    if (!all.length) return null;
    const row = th => h('button', { class: 't3-thread', type: 'button', 'data-thread': th.id, title: openTitle(p, t, th), onclick: () => openThread(th) },
      h('span', { class: 'ic', 'aria-hidden': 'true', html: iconSvg('t3', 14) }),
      h('span', { class: 't3-thread-text' }, h('span', { class: 't3-thread-title', dir: 'auto' }, th.title || t.text), h('span', { class: 't3-thread-where' }, whereOf(p, t, th))));
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
    if (had) { had.last = now; if (a.env) had.env = a.env; }
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
      agent: thread ? thread.agent : a.short, ref: task && p ? { pid: p.id, tid: task.id } : null });
    toast(thread ? 'Sending ' + tname + ' to its T3 thread.' : 'Sending ' + name + ' to T3' + (a.provider ? ', on ' + a.label : '') + '.');
    watch(0);
    return true;
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
  function said(s, a) {
    if (s.test) {
      toast(a.running ? 'T3 links work, and T3 Code is running.' : a.t3 ? 'T3 links work, but T3 Code is not running: open it before you send.'
        : "T3 links work, but T3 Code's t3 command was not found on this PC: open T3 Code once.", a.running ? '' : 'error');
      return;
    }
    if (!a.ok) { toast(String(a.error || 'T3 could not start the thread.'), 'error'); return; }
    if (s.ref) keepThread(s.ref, a, s);
    const lead = s.p && typeof Leaders !== 'undefined' ? Leaders.toastLead(s.p) : null;
    const open = a.env && a.thread ? [{ label: 'Open', run: () => follow(threadHref(a.env, a.thread)) }] : [];
    /* A helper from before 0.1.90 knows no thread to send into, and starts a new one: said, so the setup runs again. */
    const old = s.thread && a.thread !== s.thread;
    if (s.thread && !old) { toast('Sent to its T3 thread: ' + s.name + '.', '', open, { lead }); return; }
    toast('Sent to T3: ' + s.title + '.' + (a.added ? ' T3 has its folder as a project now.' : '')
      + (old ? ' It started a new thread: run the T3 setup again, in Settings, Links, so the city can send into a task\'s thread.' : ''), '', open, { lead });
  }

  return { AGENTS, TILES, TILE_NOTES, tiles, setTiles, agentOf, keepAgent, why, send, test, threadHref, pending: () => pending.size,
    threadsOf, latest, stateOf, whereOf, openThread, openTitle, rowButton, taskList,
    _test: { times: (take, run) => { TAKE_MS = take; RUN_MS = run; } } };
})();
