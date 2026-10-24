/* The leaders' news (Leader UX, piece 3, 0.1.59): each leader brings its own buildings' news, news nobody else gives,
   in the shared lines (LEADER_LINES); Proxima brings the news of a building with no leader, in the same lines. Gus and
   Proxima keep their own jobs. Designed in Leader UX, Rounds 1 to 4:
   - The moments (M1): behind its pace, due today, one task from done, Claude's additions and rounds, Claude waiting,
     asking first or stopped on an error open a bubble by themselves; Claude finishing, a round's answers and the week
     wait with their leader. A street party, Claude working and the greeting are not news.
   - The side bar's News section (N1, N3, G1, D1) replaces Urgent and Gus's part: Gus while the city has garbage, then
     each leader with news waiting, then Proxima for the buildings with none, each a face with ! for one item or a
     count for several. A click opens its bubble; each waiting face has its own dismiss; there is no Dismiss all.
   - The bubble (B1, N3) speaks where Gus and Proxima do, at the map's top left: the face at 100 px, the name in its
     color, the building, lit on the map while it shows, and Go to it. Several at once share one bubble, 1 of N with
     Next, the most pressing first. Gus and Proxima speak first. A bubble that opened by itself closes after 14 seconds
     and leaves what it held waiting; one opened by a click stays until closed.
   - Reading (D1): an item is read once its bubble showed it and was closed, or Next went past it. Opening a
     building's status card reads its news too: the card says it, and keeps saying it while it stays open.
   - Claude's reports (0.1.68, Claude's News on the Status Card, Round 1): an update Claude sends is one report, said
     under the finish of the task it reports on (A1): the finish, Claude's summary in its own words (C2), then a short
     line for each part with its own buttons, Read and Undo for what it added, Tick it, Apply and Dismiss for what it
     asks (A2). An update whose session still works waits for its finish; one with no finish to sit under is said on
     its own, as before. Tick it shows when Claude asks to tick the task off, and on a finish with no update (B3).
   Kept in this browser (nullovation-city:news): nothing new in the city. Undo, for Claude's additions, lasts while the
   page stays open, as a toast's does. */
const NEWS_RANK = { behind_more: 0, behind_day: 0, behind: 0, waiting: 1, asks: 1, failed: 1, due: 2, due_many: 2, one_left: 3,
  added: 4, round: 4, finished: 5, answers: 5, week: 6, week_quiet: 6, working: 7 };
const NEWS_OPENS = new Set(['behind', 'behind_more', 'behind_day', 'due', 'due_many', 'one_left', 'added', 'round', 'waiting', 'asks', 'failed']);
const NEWS_CLAUDE = new Set(['waiting', 'failed', 'finished', 'asks']);
/* How far behind a building is (M1): its pace one period behind (the bubble yellow), two or more (red), or a day
   without a tick under Work until finished (red). Work until finished's yellow is a fresh tick, not behind. */
function behindLevel(p, now = Date.now()) {
  const sys = p.urgency && p.urgency.system, u = urgencyOf(p, now);
  if (sys === 'pace') return u.system === 'red' ? 2 : u.system === 'yellow' ? 1 : 0;
  if (sys === 'finish') return u.system === 'red' ? 3 : 0;
  return 0;
}
const BEHIND_MOMENT = { 1: 'behind', 2: 'behind_more', 3: 'behind_day' };
/* The task a line points to: the next one, else any open task. */
const newsTask = p => nextTask(p) || openTasks(p)[0] || null;

const News = (() => {
  const KEY = 'nullovation-city:news', SAY_MS = 14000, KEEP_RAISED = 21 * 86400e3;
  /* A report lasts as long as a finish shows on the status card (12 hours); an update finds the finish of its task
     within 10 minutes, and one that names no task the one finish of the last 2 minutes. */
  const REPORT_KEEP = 13 * 3600e3, FIN_NEAR = 10 * 60e3, FIN_JUST = 2 * 60e3;
  const fresh = () => ({ items: [], raised: {}, lvl: {}, dueDay: '', week: '', reports: [] });
  function load() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY));
      if (v && typeof v === 'object' && Array.isArray(v.items)) { const o = Object.assign(fresh(), v); if (!Array.isArray(o.reports)) o.reports = []; return o; }
    } catch (e) { /* a fresh start */ }
    return fresh();
  }
  let st = load(), started = false, sayMs = SAY_MS, flush = false;
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* this visit only */ } };
  /* Another tab with the city open changes the same store: read it again first, so neither undoes the other. */
  const edit = fn => { st = load(); const was = JSON.stringify(st), r = fn(); if (JSON.stringify(st) !== was) save(); return r; };
  const undos = new Map();                                   // an item's id: what its Undo takes back, while the page is open
  const held = new Map();                                    // a building's id: the news its status card or project view read

  /* ---------- who says it ---------- */
  function speakerOf(p) {
    const l = p && leaderOf(p);
    return l ? { k: 'ld:' + l.id, l, name: leaderName(l), role: l.role, color: l.color } : { k: 'px', l: null, name: 'Proxima Pace', role: 'Productivity Inspector', color: '#8FD0F7' };
  }
  /* A speaker's face; Proxima breathes too while she brings a building's news in the leaders' place (0.1.62). */
  const faceOf = (sp, size) => (sp.l ? Leaders.face(sp.l, size) : Leaders.breathe(Proxima.faceEl(size), 'proxima'));
  const lineOf = it => leaderSay(it.moment, it.v);
  /* The most pressing first; among the same, the leaders before Proxima, as in the side bar, then the oldest first. */
  const proximaSays = it => { const p = getProject(it.pid); return p && !leaderOf(p) ? 1 : 0; };
  const sortItems = list => [...list].sort((a, b) => rankOf(a) - rankOf(b) || proximaSays(a) - proximaSays(b) || a.at - b.at);
  const live = () => st.items.filter(it => getProject(it.pid));

  /* ---------- raising news ---------- */
  function raise(p, moment, v, ref = {}, key = null) {
    if (!p || !LEADER_LINES[moment]) return null;
    const now = Date.now(), it = { id: uid('nw'), key: key || moment + ':' + p.id + ':' + now, pid: p.id, moment, v, ref, at: now, popped: false };
    st.items = st.items.filter(x => x.key !== it.key);      // the same news again replaces the one waiting
    st.items.push(it);
    st.raised[it.key] = now;
    return it;
  }
  const wasRaised = key => st.raised[key] != null;
  function after() {
    renderSection();
    Bubble.refresh();
    Leaders.redrawCard();
    if (bub) { grow(); } else pumpSoon();
  }
  const pumpSoon = () => { clearTimeout(waitT); waitT = setTimeout(pump, 30); };
  /* What reads an item: its bubble went past it or closed, its card showed it, or its face was dismissed. */
  function readIds(ids) {
    const set = new Set(ids);
    if (!set.size) return;
    edit(() => { st.items = st.items.filter(x => !set.has(x.id)); });
    renderSection();
  }

  /* One add from outside: Claude's additions and rounds (the inbox), and a round's answers. Undo is kept for its item. */
  function add(p, moment, v, { ref = {}, key = null, undo = null } = {}) {
    const it = edit(() => raise(p, moment, v, ref, key));
    if (it && undo) undos.set(it.id, undo);
    if (it) after();
    return it;
  }

  /* ---------- the moments the city sees for itself: behind, due today, the week, and stale news ---------- */
  function check(now = Date.now()) {
    if (!started) return;
    let moved = false;
    edit(() => {
      const today = ymd(now), wk = ymd(weekStartOf(now));
      const n0 = st.items.length;
      st.items = st.items.filter(it => getProject(it.pid));
      st.reports = st.reports.filter(r => getProject(r.pid) && now - r.at < REPORT_KEEP);   // Claude's reports, gone with their finish's 12 hours
      for (const p of DB.projects) {
        /* behind its pace: on the change, and not when you picked the system or its days yourself */
        const lv = behindLevel(p, now), u = p.urgency || {}, cfg = [u.system, u.days, u.pickedAt].join(':'), old = st.lvl[p.id];
        if (!old || typeof old !== 'object') st.lvl[p.id] = { l: 0, cfg };            // first seen: behind already is news
        else if (old.cfg !== cfg) st.lvl[p.id] = { l: lv, cfg };                       // your own change is not
        const prev = st.lvl[p.id].l;
        if (lv !== prev) {
          const t = newsTask(p);
          if (lv && t && (prev === 0 || (lv === 2 && prev === 1) || (lv === 3) !== (prev === 3))) { raise(p, BEHIND_MOMENT[lv], { task: t.text }, { level: lv, tid: t.id }, 'behind:' + p.id); moved = true; }
          st.lvl[p.id].l = lv;
        }
        /* news that is no longer true goes: back on pace, nothing due today any more, a milestone no longer one task
           from done, last week's news in a new week */
        st.items = st.items.filter(it => {
          if (it.pid !== p.id) return true;
          if (it.moment.startsWith('behind')) return lv > 0 && (lv === 3) === (it.ref.level === 3);
          if (it.moment === 'due' || it.moment === 'due_many') return it.ref.day === today && dueToday(p, today).length > 0;
          if (it.moment === 'one_left') return oneLeft(p, it.ref.mid) != null;
          if (it.moment === 'week' || it.moment === 'week_quiet') return it.ref.week === wk;
          return true;
        });
      }
      /* due today: the day's first open, one per building */
      if (st.dueDay !== today) {
        st.dueDay = today;
        for (const p of DB.projects) {
          const ts = dueToday(p, today);
          if (!ts.length) continue;
          raise(p, ts.length > 1 ? 'due_many' : 'due', { task: ts[0].text, n: ts.length }, { day: today, tid: ts[0].id }, 'due:' + p.id + ':' + today);
          moved = true;
        }
      }
      /* the week: the first open of a new Saturday-to-Friday week, one per building; the first week the city keeps
         news only starts counting */
      if (st.week !== wk) {
        const first = !st.week;
        st.week = wk;
        if (!first) {
          const ticks = typeof taskTicks === 'function' ? taskTicks(DB.projects, now) : [];
          const byP = typeof ticksByProject === 'function' ? ticksByProject(ticks, addDays(weekStartOf(now), -7), weekStartOf(now)) : [];
          for (const p of DB.projects) {
            const t = newsTask(p);
            if (!t) continue;
            const row = byP.find(r => r.p === p), n = row ? row.n : 0;
            raise(p, n ? 'week' : 'week_quiet', { n, task: t.text }, { week: wk, tid: t.id }, 'week:' + p.id + ':' + wk);
            moved = true;
          }
        }
      }
      for (const [k, at] of Object.entries(st.raised)) if (now - at > KEEP_RAISED) delete st.raised[k];
      st.reports = st.reports.filter(r => getProject(r.pid) && now - r.at < REPORT_KEEP);
      for (const id of Object.keys(st.lvl)) if (!getProject(id)) delete st.lvl[id];
      if (st.items.length !== n0) moved = true;
    });
    if (moved) after();
  }
  function dueToday(p, today = ymd()) {
    const pin = pinnedTask(p);
    const ts = openTasks(p).filter(t => t.due === today);
    return pin && ts.includes(pin) ? [pin, ...ts.filter(t => t !== pin)] : ts;
  }
  /* A milestone of two tasks or more, with no repeat, one task from done: its last open task. */
  function oneLeft(p, mid) {
    const m = (p.milestones || []).find(x => x.id === mid);
    const ts = p.todos.filter(t => t.milestoneId === mid);
    if (!m || ts.length < 2 || ts.some(t => t.repeat)) return null;
    const open = ts.filter(t => !t.done);
    return open.length === 1 ? { m, t: open[0] } : null;
  }
  /* A tick anywhere (tickTask): a milestone it leaves one task from done, once a day. */
  function ticked(p, t) {
    if (!started || !p || !t || !t.milestoneId) return;
    const x = oneLeft(p, t.milestoneId);
    if (!x) return;
    const key = 'one:' + x.m.id + ':' + ymd();
    if (wasRaised(key)) return;
    edit(() => raise(p, 'one_left', { milestone: x.m.name, task: x.t.text }, { mid: x.m.id, tid: x.t.id }, key));
    setTimeout(after, 0);                                    // after the tick has redrawn
  }

  /* ---------- Claude's moments: its sessions, and the changes that ask first ---------- */
  function claude() {
    if (!started || typeof ClaudeWork === 'undefined') return;
    let moved = flush;
    flush = false;
    edit(() => {
      const n0 = st.items.length;
      for (const p of DB.projects) {
        const ss = ClaudeWork.sessionsOf(p);
        /* an update waiting for its session: said with its finish once it finishes, or on its own once the session
           stops without one (A1) */
        for (const rep of st.reports.filter(r => r.pid === p.id && r.sid && !r.alone && !r.fin)) {
          const s = ss.find(x => x.session === rep.sid);
          if (s && s.state === 'done') { attach(p, rep, s); moved = true; }
          else if (!s || (s.state !== 'working' && s.state !== 'waiting')) { alone(p, rep); moved = true; }
        }
        for (const s of ss) {
          const task = s.task || s.ask || 'a task';
          if (s.state === 'waiting') {
            const key = 'waiting:' + s.session + ':' + s.since;
            if (!wasRaised(key)) { raise(p, 'waiting', { task }, { session: s.session }, key); moved = true; }
          } else if (s.state === 'failed' && !ClaudeWork.isSeen(s)) {
            const key = 'failed:' + s.session + ':' + s.since;
            if (!wasRaised(key)) { raise(p, 'failed', { task }, { session: s.session }, key); moved = true; }
          } else if (s.state === 'done' && !ClaudeWork.isSeen(s)) {
            const key = finKey(s);
            if (!wasRaised(key)) { raise(p, 'finished', { task }, { session: s.session, task: s.task, project: s.project }, key); moved = true; }
          }
        }
        /* waiting is over once the session moves on; an error once it works again */
        st.items = st.items.filter(it => {
          if (it.pid !== p.id || (it.moment !== 'waiting' && it.moment !== 'failed')) return true;
          const s = ss.find(x => x.session === it.ref.session);
          return it.moment === 'waiting' ? !!s && s.state === 'waiting' : !s || s.state === 'failed';
        });
      }
      /* what asks first: one item for each change file waiting in inbox/pending, gone once applied or dismissed; what a
         report holds is said with its report (report marks it raised) */
      if (typeof ClaudeInbox !== 'undefined') {
        const pend = ClaudeInbox.pending(), names = new Set(pend.map(x => x.name));
        for (const e of pend) {
          const p = DB.projects.find(x => x.name.trim().toLowerCase() === e.project.trim().toLowerCase());
          const key = 'asks:' + e.name;
          if (!p || wasRaised(key)) continue;
          raise(p, 'asks', { change: ClaudeInbox.gist(p, e) }, { entry: e.name }, key);
          moved = true;
        }
        st.items = st.items.filter(it => it.moment !== 'asks' || names.has(it.ref.entry));
      }
      if (st.items.length !== n0) moved = true;
    });
    if (moved) after();
  }

  /* ---------- Claude's reports (0.1.68, Claude's News on the Status Card, A1) ---------- */
  const tkey = s => String(s || '').trim().toLowerCase();
  const finKey = s => 'finished:' + s.session + ':' + tkey(s.task || s.ask || 'a task').slice(0, 160);
  const reportOf = id => (id && st.reports.find(r => r.id === id)) || null;
  const entryOf = name => (name && typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.pending().find(e => e.name === name) : null) || null;
  /* The report a finish heads: the one its session sent in the turn that finished, known by the turn's reply. */
  const finishReport = s => [...st.reports].reverse().find(r => r.sid === s.session && r.fin && r.reply === (s.reply || '')) || null;
  /* The report a session still working has sent, waiting for its finish. */
  const heldReport = s => [...st.reports].reverse().find(r => r.sid === s.session && !r.alone && !r.fin) || null;
  /* The session an update came from: the one working on the task it names (or that just finished it), else, when it
     names none of its own, the one session working on the building, or the one that finished there a moment ago. */
  function sessionFor(p, rep, named) {
    if (typeof ClaudeWork === 'undefined') return null;
    const ss = ClaudeWork.sessionsOf(p), k = tkey(rep.task), now = Date.now();
    const busy = s => s.state === 'working' || s.state === 'waiting';
    const best = list => [...list].sort((a, b) => busy(b) - busy(a) || b.at - a.at)[0] || null;
    if (k) {
      const m = ss.filter(s => tkey(s.task || s.ask) === k && (busy(s) || (s.state === 'done' && now - s.at < FIN_NEAR)));
      if (m.length) return best(m);
      if (named) return null;
    }
    const b = ss.filter(busy);
    if (b.length) return b.length === 1 ? b[0] : null;
    const d = ss.filter(s => s.state === 'done' && now - s.at < FIN_JUST);
    return d.length === 1 ? d[0] : null;
  }
  /* An update Claude sent (the inbox, 0.1.68): what it added, with Undo, what it asks first, and its summary, as one
     report. Its session still working, it waits for the finish; finished, it is said under the finish; with no session,
     it is said on its own, as before: what it added, each round, and what it asks. Said once the poll that brought it
     is done (claude), so what it asks is read by then. */
  function report(p, { task = '', named = false, summary = '', undo = null, entry = '' } = {}) {
    if (!p) return null;
    const add = undo && (undo.todos.length || undo.notes.length || undo.links.length) ? { todos: [...undo.todos], notes: [...undo.notes], links: [...undo.links] } : null;
    const rounds = (undo && undo.rounds || []).map(r => { const t = p.todos.find(x => x.id === r.id); return { tid: r.id, title: t && t.round ? t.round.title : '' }; });
    if (!add && !rounds.length && !entry) return null;
    const rep = { id: uid('rp'), pid: p.id, task, summary, at: Date.now(), sid: '', fin: 0, reply: '', alone: false, entry, add, rounds };
    const none = { todos: [], ms: [], notes: [], links: [], rounds: [] };
    if (add) undos.set(rep.id, { ...none, todos: undo.todos, ms: undo.ms, notes: undo.notes, links: undo.links });
    for (const r of undo && undo.rounds || []) undos.set(rep.id + ':' + r.id, { ...none, rounds: [r] });
    const s = sessionFor(p, rep, named);
    edit(() => {
      st.reports.push(rep);
      if (entry) st.raised['asks:' + entry] = rep.at;            // said in this report, never as an item of its own
      if (!s) alone(p, rep);
      else { rep.sid = s.session; if (s.state === 'done') attach(p, rep, s); }
    });
    flush = true;
    return rep;
  }
  /* Under its finish: the finish's news carries it, and opens by itself again while it holds something to act on. */
  function attach(p, rep, s) {
    rep.fin = s.at; rep.reply = s.reply || '';
    const key = finKey(s), it = st.items.find(x => x.key === key);
    if (it) { it.ref.report = rep.id; it.popped = false; }
    else raise(p, 'finished', { task: s.task || s.ask || 'a task' }, { session: s.session, task: s.task, project: s.project, report: rep.id }, key);
  }
  /* On its own, with no finish to sit under: as before, what it added, each round, and what it asks, each its item. */
  function alone(p, rep) {
    rep.alone = true;
    if (rep.add) raise(p, 'added', { what: addedWords(p, rep.add) || 'what it sent' }, { report: rep.id }, 'added:' + rep.id);
    for (const r of rep.rounds) {
      const t = p.todos.find(x => x.id === r.tid);
      if (t && t.round) raise(p, 'round', { task: t.text, round: t.round.title }, { tid: t.id, report: rep.id }, 'round:' + rep.id + ':' + t.id);
    }
    if (rep.entry) { const e = entryOf(rep.entry); raise(p, 'asks', { change: e ? ClaudeInbox.gist(p, e) : 'a change' }, { entry: rep.entry, report: rep.id }, 'asks:' + rep.entry); }
  }
  /* What is still there of what Claude added, and whether its Undo is. */
  const addedOf = (p, add) => ({ ts: add.todos.map(id => p.todos.find(t => t.id === id)).filter(Boolean),
    ns: add.notes.map(id => p.notes.find(n => n.id === id)).filter(Boolean), ls: add.links.map(id => p.links.find(l => l.id === id)).filter(Boolean) });
  const addLive = (p, add) => { const a = addedOf(p, add); return a.ts.length + a.ns.length + a.ls.length > 0; };
  /* What Claude added, named, not just counted: one of a kind by its name, more by their count. */
  function addedWords(p, add) {
    const a = addedOf(p, add);
    const kind = (list, one, many, name) => (!list.length ? '' : list.length > 1 ? plural(list.length, one, many) : 'a ' + one + (name(list[0]) ? ', ' + cut(name(list[0]), 40) : ''));
    const bits = [kind(a.ts, 'task', 'tasks', t => t.text), kind(a.ns, 'note', 'notes', n => n.title), kind(a.ls, 'link', 'links', l => l.label || suggestLabel(l.url))].filter(Boolean);
    if (bits.length < 2) return bits[0] || '';
    return bits.slice(0, -1).join(', ') + (bits.some(b => b.includes(', ')) ? ', and ' : ' and ') + bits[bits.length - 1];
  }
  /* Whether a report still holds something to act on: an Undo, or a change waiting for your OK. */
  function repActs(p, rep) {
    if (rep.add && undos.has(rep.id) && addLive(p, rep.add)) return true;
    if (rep.rounds.some(r => undos.has(rep.id + ':' + r.tid))) return true;
    const e = entryOf(rep.entry);
    return !!e && ClaudeInbox.openIdx(e).length > 0;
  }
  function hasActs(p, it) {
    if (it.moment === 'asks') { const e = entryOf(it.ref.entry); return !!e && ClaudeInbox.openIdx(e).length > 0; }
    if (it.moment === 'added') return undos.has(it.ref.report || it.id);
    if (it.moment === 'round') { const rep = reportOf(it.ref.report); return undos.has(rep ? rep.id + ':' + it.ref.tid : it.id); }
    if (it.moment === 'finished') { const rep = reportOf(it.ref.report); return !!rep && repActs(p, rep); }
    return false;
  }
  /* A report ranks by the most pressing thing in it: what asks first, then what Claude added, then the finish. */
  function repRank(p, rep) {
    const e = entryOf(rep.entry);
    if (e && ClaudeInbox.openIdx(e).length) return NEWS_RANK.asks;
    return repActs(p, rep) ? NEWS_RANK.added : NEWS_RANK.finished;
  }
  function rankOf(it) {
    const p = it.moment === 'finished' && it.ref && it.ref.report ? getProject(it.pid) : null, rep = p && reportOf(it.ref.report);
    return rep ? repRank(p, rep) : NEWS_RANK[it.moment] ?? 9;
  }
  /* What opens a bubble by itself: the moments that do, and a finish whose report holds something to act on. */
  function opens(it) {
    if (NEWS_OPENS.has(it.moment)) return true;
    const p = it.moment === 'finished' ? getProject(it.pid) : null;
    return !!p && hasActs(p, it);
  }

  /* ---------- the side bar's News section ---------- */
  function faces() {
    const by = new Map();
    for (const it of live()) {
      const sp = speakerOf(getProject(it.pid));
      if (!by.has(sp.k)) by.set(sp.k, { ...sp, items: [] });
      by.get(sp.k).items.push(it);
    }
    const list = [...by.values()].map(f => ({ ...f, items: sortItems(f.items) }));
    list.sort((a, b) => (a.k === 'px') - (b.k === 'px') || rankOf(a.items[0]) - rankOf(b.items[0]) || a.name.localeCompare(b.name));
    return list;
  }
  /* Under a face, the first word of its name, so Gus and Proxima fit as the leaders do; the tooltip has it whole. */
  const shortName = name => String(name).trim().split(/\s+/)[0] || name;
  const badge = n => h('span', { class: 'news-badge', 'aria-hidden': 'true' }, n <= 1 ? '!' : String(Math.min(n, 99)));
  function tile({ k, name, face, n, title, open, dismiss, color }) {
    const t = h('div', { class: 'news-tile', 'data-k': k },
      h('button', { class: 'news-face', type: 'button', title, 'aria-label': title, onclick: open }, face, badge(n), h('span', { class: 'news-name', dir: 'auto' }, shortName(name))),
      dismiss ? h('button', { class: 'icon-btn news-dismiss', type: 'button', 'aria-label': 'Dismiss ' + name + '’s news', title: 'Dismiss ' + name + '’s news', html: iconSvg('close', 12), onclick: dismiss }) : null);
    if (color) t.style.setProperty('--ld', color);
    return t;
  }
  function renderSection() {
    const sec = $('#sbNews'), box = $('#newsList');
    if (!sec) return;
    const a = document.activeElement, focus = a && box.contains(a) ? [a.closest('.news-tile') && a.closest('.news-tile').dataset.k, a.classList.contains('news-dismiss')] : null;
    const tiles = [];
    if (typeof Gus !== 'undefined' && Gus.shows()) {
      const r = Gus.report();
      tiles.push(tile({ k: 'gus', name: 'Gus Grimsby', face: Gus.faceEl(48), n: r.tasks, color: '#F29A74',
        title: 'Gus Grimsby, Garbage Man' + (r.tasks ? ': ' + plural(r.tasks, 'task', 'tasks') + ' between the city and clean streets' : '') + '. Open his report.',
        open: () => { Menu.closeDrawer(); Gus.open(); } }));
    }
    for (const f of faces()) {
      const n = f.items.length;
      tiles.push(tile({ k: f.k, name: f.name, face: faceOf(f, 48), n, color: f.color,
        title: f.name + (f.role ? ', ' + f.role : '') + ': ' + plural(n, 'piece of news', 'pieces of news') + '. Hear it.',
        open: () => { Menu.closeDrawer(); openFace(f.k); }, dismiss: () => dismiss(f.k) }));
    }
    sec.hidden = !tiles.length;
    box.replaceChildren(...tiles.filter(Boolean));
    if (focus && focus[0]) {
      const t = $(`.news-tile[data-k="${focus[0]}"]`, box);
      const b = t && (focus[1] ? $('.news-dismiss', t) : $('.news-face', t));
      if (b) b.focus({ preventScroll: true }); else { const any = $('.news-face', box); if (any) any.focus({ preventScroll: true }); }
    }
  }
  /* A face's dismiss: its news is read without being heard; what sticks for a reason (a bubble on the map, Claude's
     changes in the status card) stays where it shows (N2). */
  function dismiss(k) {
    const ids = live().filter(it => speakerOf(getProject(it.pid)).k === k).map(it => it.id);
    if (bub && bub.list.some(it => ids.includes(it.id))) hide();
    readIds(ids);
    const next = $('#newsList .news-face');
    if (next) next.focus(); else { const s = $('#search'); if (s) s.focus({ preventScroll: true }); }
  }

  /* ---------- the bubble ---------- */
  let bub = null, sayT = 0, waitT = 0;                       // { list, i, auto, k, from }
  const box = () => $('#ldSay');
  function blocked() {
    return (typeof Gus !== 'undefined' && Gus.isSaying()) || (typeof Proxima !== 'undefined' && Proxima.busy())
      || Panel.isOpen() || Confirm.isOpen();
  }
  /* What opens by itself: the news that opens by itself and has not shown yet, unless its building's card has it. */
  function pump() {
    clearTimeout(waitT);
    if (!started || bub) return;
    const due = sortItems(live().filter(it => !it.popped && opens(it)));
    if (!due.length) return;
    if (blocked()) { waitT = setTimeout(pump, 500); return; }
    show(due, { auto: true });
  }
  /* New news while the bubble shows joins it, as one more of N. */
  function grow() {
    const have = new Set(bub.list.map(it => it.id));
    const more = sortItems(live().filter(it => !it.popped && opens(it) && !have.has(it.id)));
    if (!more.length) return;
    bub.list.push(...more);
    popped(more);
    draw();
  }
  function popped(list) {
    const ids = new Set(list.map(it => it.id));
    edit(() => { for (const it of st.items) if (ids.has(it.id)) it.popped = true; });
  }
  function openFace(k) {
    const list = sortItems(live().filter(it => speakerOf(getProject(it.pid)).k === k));
    if (!list.length) return;
    if (typeof Gus !== 'undefined' && Gus.isSaying()) Gus.hush();
    show(list, { auto: false, k });
    if (typeof Proxima !== 'undefined') Proxima.yieldToGus();       // her bubble goes, and comes back after this one
    const b = box(), first = b && ($('.ld-say-acts .btn', b) || $('#ldSayClose'));
    if (first) first.focus({ preventScroll: true });
  }
  function show(list, { auto, k = null }) {
    clearTimeout(sayT);
    bub = { list, i: 0, auto, k, from: auto ? null : document.activeElement };
    popped(list);
    const b = box();
    b.hidden = false;
    draw();
    requestAnimationFrame(() => b.classList.add('show'));
    if (auto) sayT = setTimeout(() => hide({ read: false }), sayMs);
  }
  /* Once you act on the bubble, it stays until you close it. */
  const hold = () => { if (bub && bub.auto) { bub.auto = false; clearTimeout(sayT); } };
  function draw() {
    const b = box();
    if (!bub || !b) return;
    const it = bub.list[bub.i], p = getProject(it.pid);
    if (!p) { next(); return; }
    const sp = speakerOf(p), n = bub.list.length;
    b.style.setProperty('--ld', sp.color);
    b.classList.toggle('px-voice', !sp.l);
    b.dataset.k = sp.k; b.dataset.moment = it.moment;
    $('#ldSayFace').replaceChildren(faceOf(sp, 100));
    $('#ldSayName').textContent = sp.name;
    $('#ldSayRole').textContent = sp.role || '';
    $('#ldSayRole').hidden = !sp.role;
    const keep = b.contains(document.activeElement) ? keyOf(document.activeElement) : null;
    /* the building: a click goes to it on the map, as Go to it does, without opening it (0.1.60) */
    $('#ldSayWhere').replaceChildren(h('button', { class: 'ld-say-bld', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } },
      h('span', { class: 'ld-say-thumb', 'aria-hidden': 'true' }, MapView.thumb(p)), h('bdi', null, p.name)));
    const v = viewOf(p, it, 'say');
    $('#ldSayText').replaceChildren(...v.nodes);
    speak(it.id);
    $('#ldSayMore').replaceChildren(...v.more);
    $('#ldSayActs').replaceChildren(...[...v.acts,
      h('button', { class: 'btn btn-small btn-quiet ld-go', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } }, 'Go to it'),
      n > 1 ? h('span', { id: 'ldSayCount', class: 'ld-say-count' }, (bub.i + 1) + ' of ' + n) : null,
      n > 1 && bub.i < n - 1 ? h('button', { id: 'ldSayNext', class: 'btn btn-small ld-next', type: 'button', onclick: () => { hold(); next(); } }, 'Next') : null].filter(Boolean));
    MapView.light(p.id);
    const edge = panelEdge();                                                 // beside the project view or All tasks, as Proxima's
    b.style.left = edge ? Math.round(edge + 22) + 'px' : '';
    fitSay(b);
    if (keep) { const back = $(keep, b); if (back) back.focus({ preventScroll: true }); }
  }
  /* A button in the bubble, found again after a redraw: by its id, else its first class. */
  const keyOf = el => (el.id ? '#' + el.id : el.classList && el.classList.length ? '.' + el.classList[el.classList.length - 1] : null);
  /* Draws the bubble again, as it is: its portraits or its building's art loaded after it opened. */
  function redraw() { if (bub) draw(); }
  function next() {
    if (!bub) return;
    const cur = bub.list[bub.i];
    if (cur) readIds([cur.id]);
    if (bub.i >= bub.list.length - 1) { hide({ read: false }); return; }
    bub.i++;
    draw();
    const nb = $('#ldSayNext') || $('#ldSayClose');
    if (nb && box().contains(document.activeElement) === false && !bub.auto) nb.focus({ preventScroll: true });
  }
  /* Closed: what it showed is read. Gone by itself, or given way to Gus or Proxima: what it showed waits, unread. */
  function hide({ read = true } = {}) {
    clearTimeout(sayT);
    const b = box();
    if (!bub) return false;
    const was = bub;
    bub = null;
    hush();
    if (read) readIds([was.list[was.i].id]);
    if (b) { b.classList.remove('show'); b.hidden = true; }
    if (MapView._lit() === (was.list[was.i] || {}).pid) MapView.light(null);
    renderSection();
    if (was.from && document.contains(was.from) && b && b.contains(document.activeElement)) was.from.focus({ preventScroll: true });
    else if (b && b.contains(document.activeElement)) { const f = $('#newsList .news-face'); if (f) f.focus({ preventScroll: true }); }
    waitT = setTimeout(pump, 400);
    return true;
  }
  /* Gus or Proxima speaks: the bubble gives way, and what it had not read comes back after them. */
  function yieldTo() {
    if (!bub) return;
    const left = bub.list.slice(bub.i).map(it => it.id), auto = bub.auto;
    hide({ read: false });
    if (auto) edit(() => { for (const it of st.items) if (left.includes(it.id)) it.popped = false; });
  }
  function goTo(pid) {
    if (!getProject(pid)) return;
    MapView.glideBeside(pid, panelEdge());
  }

  /* ---------- talking (0.1.62, Leader UX E1): the line types out and the face bobs with it, then settles ---------- */
  /* Every letter is in the line from the start, see-through until its turn, so the bubble keeps its size and a screen
     reader hears the whole line once. A redraw of the same line carries on where it was; a line said already stays
     whole; Next types the next one. Motion on Still shows it whole, with the face still. */
  const TYPE_MS = 26, TYPE_ALL_MS = 1800;                   // a letter every 26 ms, a long line in 1.8 seconds at most
  let typeMs = TYPE_MS, talk = { id: null, n: 0, done: false, raf: 0 };
  const graphemes = str => (typeof Intl !== 'undefined' && Intl.Segmenter
    ? [...new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(str)].map(x => x.segment) : Array.from(str));
  function letters(root) {
    const out = [];
    const walk = node => {
      for (const c of [...node.childNodes]) {
        if (c.nodeType === 3) {
          const parts = graphemes(c.data).map(ch => { const s = document.createElement('span'); s.className = 'ty'; s.textContent = ch; out.push(s); return s; });
          c.replaceWith(...parts);
        } else if (c.nodeType === 1) walk(c);
      }
    };
    walk(root);
    return out;
  }
  /* Paced by the clock, a frame at a time, so a busy map makes no letter wait. */
  function speak(id) {
    const el = $('#ldSayText'), f = $('#ldSayFace');
    cancelAnimationFrame(talk.raf);
    if (talk.id !== id) talk = { id, n: 0, done: false, raf: 0 };
    if (talk.done || Motion.still() || typeMs <= 0) { settle(); return; }
    const ls = letters(el);
    if (!ls.length) { settle(); return; }
    const every = Math.max(8, Math.min(typeMs, TYPE_ALL_MS / ls.length));
    talk.n = Math.min(talk.n, ls.length);
    ls.slice(0, talk.n).forEach(x => x.classList.add('on'));
    el.classList.add('typing');
    if (f) f.classList.add('talking');
    const t0 = performance.now() - talk.n * every;
    const frame = now => {
      if (!document.contains(ls[0])) return;                      // drawn again: that draw carries on
      const n = Math.min(ls.length, Math.floor((now - t0) / every) + 1);
      while (talk.n < n) ls[talk.n++].classList.add('on');
      if (talk.n >= ls.length) settle(); else talk.raf = requestAnimationFrame(frame);
    };
    talk.raf = requestAnimationFrame(frame);
  }
  /* The line whole: its letters back to plain words, the face at rest. */
  function settle() {
    cancelAnimationFrame(talk.raf);
    if (talk.id) talk.done = true;
    const el = $('#ldSayText'), f = $('#ldSayFace');
    if (f) f.classList.remove('talking');
    if (!el) return;
    el.classList.remove('typing');
    const ty = $$('.ty', el);
    if (!ty.length) return;
    for (const x of ty) x.replaceWith(x.firstChild || '');
    el.normalize();
  }
  function hush() { settle(); talk = { id: null, n: 0, done: false, raf: 0 }; }

  /* ---------- the line: its task a link that opens it (0.1.60) ---------- */
  /* The task an item speaks of: the one it names by id, else by its title in the building. */
  function taskFor(p, it) {
    const byId = it.ref && it.ref.tid ? p.todos.find(t => t.id === it.ref.tid) : null;
    if (byId) return byId;
    const name = it.ref && it.ref.task || it.v && it.v.task;
    return name ? taskNamed(p, name) : null;
  }
  const taskNamed = (p, name) => { const k = String(name).trim().toLowerCase(); return p.todos.find(t => !t.archived && t.text.trim().toLowerCase() === k) || p.todos.find(t => t.text.trim().toLowerCase() === k) || null; };
  /* A line as nodes: the words, and the task in its own color, a click opening it in its project. From the bubble,
     going to the task is acting on the news: it is read and the bubble closes, as Open does; what else it held waits. */
  function sayNodes(p, moment, v, t, where, it = null) {
    return leaderParts(moment, v).map(x => {
      if (x.blank !== 'task' || !t) return x.text;
      return h('button', { class: 'ld-task', type: 'button', dir: 'auto', title: 'Open ' + x.full, 'data-task': t.id, onclick: e => {
        e.stopPropagation();
        if (where === 'say' && it) { readIds([it.id]); hide({ read: false }); }
        FullView.openTask(p.id, t.id);
      } }, x.text);
    });
  }

  /* ---------- how an item reads (0.1.68): its line with its one time, Claude's own words, and a short line for
     each part of a report with its own buttons, none longer than two lines (A2) ---------- */
  const cut = (s, n) => { s = String(s || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; };
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const whenEl = (at, lead = '') => h('span', { class: 'b-claude-when' }, (lead ? lead + relAgo(at) : cap(relAgo(at))) + '.');
  /* The start of Claude's last reply, written for the chat: its markdown comes off. */
  function plainReply(s) {
    return String(s || '').replace(/```[\s\S]*?(?:```|$)/g, ' ').replace(/`([^`]*)`/g, '$1').replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1')
      .replace(/(\*\*|__)(.+?)\1/g, '$2').replace(/(^|[\s(])\*(\S(?:[^*]*\S)?)\*(?=[\s).,;:!?]|$)/g, '$1$2')
      .replace(/(^|\s)#{1,6}\s+/g, '$1').replace(/^\s*(?:>|[-*+]|\d+\.)\s+/, '').replace(/\s\*\s/g, ' ').replace(/\s+/g, ' ').trim();
  }
  /* Claude's own words, on a line of their own, marked as its (C2): one line, cut short, whole in its tooltip. */
  function wordsEl(text) {
    const t = cut(text, 200);
    return t ? h('p', { class: 'b-claude-said', dir: 'auto', title: 'In Claude’s words: ' + String(text).trim() }, iconEl('claude', 12), h('span', null, t)) : null;
  }
  /* A task named in a part's line: in its own color, a click opening it, as in a leader's line. */
  function taskLink(p, t, where, it) {
    return h('button', { class: 'ld-task', type: 'button', dir: 'auto', title: 'Open ' + t.text, 'data-task': t.id, onclick: e => {
      e.stopPropagation();
      if (where === 'say' && it) { readIds([it.id]); hide({ read: false }); }
      FullView.openTask(p.id, t.id);
    } }, lineTitle(t.text));
  }
  const partEl = (kind, text, acts) => h('div', { class: 'ld-part', 'data-part': kind }, h('span', { class: 'ld-part-text', dir: 'auto' }, ...text),
    acts.filter(Boolean).length ? h('span', { class: 'ld-part-acts' }, ...acts.filter(Boolean)) : null);
  /* A button. It acts, then the item is read and the bubble goes on to the next one; a part's button (stay) keeps the
     item while it has something left to act on, drawn again without what was done. */
  function act(p, it, where, label, cls, title, run, stay = false) {
    return h('button', { class: 'btn btn-small ' + cls, type: 'button', title, onclick: () => {
      hold();
      Promise.resolve(run()).then(() => acted(p, it, where, stay));
    } }, label);
  }
  function acted(p, it, where, stay) {
    const left = !!it && stay && hasActs(p, it);
    if (where === 'say') { if (bub) { if (left) draw(); else next(); } return; }
    if (it && !left) dropHeld(p.id, it.id);
    Bubble.refresh(); Leaders.redrawCard();
  }
  /* Read: a small panel with the whole of it (A2's note). */
  const readBtn = (title, body) => h('button', { class: 'btn btn-small btn-quiet ld-read', type: 'button', title: 'Read it whole', onclick: () => {
    hold();
    Panel.open(title, h('div', { class: 'cr-body' }, body()), 'cr');
  } }, 'Read');
  const crSec = (head, ...kids) => h('section', { class: 'cr-sec' }, h('h3', { class: 'cr-h', dir: 'auto' }, head), ...kids);
  const crText = (text, cls = '') => h('p', { class: 'cr-text' + (cls ? ' ' + cls : ''), dir: 'auto' }, text);
  function readAdded(p, add) {
    const a = addedOf(p, add);
    return [
      ...a.ts.map(t => crSec('A task', h('button', { class: 'linkish cr-title', type: 'button', dir: 'auto', title: 'Open it in ' + p.name, onclick: () => { Panel.close(); FullView.openTask(p.id, t.id); } }, t.text),
        t.description ? crText(t.description) : null)),
      ...a.ns.map(n => crSec(n.title || 'A note', n.text ? crText(n.text) : crText('Nothing written in it.', 'was'))),
      ...a.ls.map(l => { const lt = linkTarget(l); return crSec('A link', lt.href ? h('a', { class: 'cr-title', href: lt.href, target: lt.blank ? '_blank' : null, rel: 'noopener', dir: 'auto', title: lt.title }, lt.name) : h('b', { class: 'cr-title', dir: 'auto' }, lt.name),
        h('p', { class: 'cr-url', dir: 'ltr' }, l.url)); }),
    ];
  }
  const readDescription = (t, c) => [crSec('The new description', crText(String(c.description || '').trim())),
    crSec('Its description now', (t.description || '').trim() ? crText(t.description.trim(), 'was') : crText('No description yet.', 'was'))];
  const readPlanBody = plan => [plan.description ? crSec('The About', crText(plan.description)) : null,
    ...plan.milestones.map(m => crSec(m.name, h('ul', { class: 'cr-list' }, m.tasks.map(t => h('li', { dir: 'auto' }, t.text)))))].filter(Boolean);

  /* One change Claude asks about: a short line saying it, its task a link (this task when it is the report's own),
     and its buttons: Tick it for a tick (B3), Read, Apply and Dismiss for a description or a plan. */
  function askOf(p, e, i, task, it, where) {
    const c = e.changes[i], r = ClaudeInbox.readable(p, c), mine = !!task && tkey(c.task) === tkey(task);
    const name = t => (t ? taskLink(p, t, where, it) : h('bdi', null, lineTitle(String(c.task || '').trim())));
    const no = title => act(p, it, where, 'Dismiss', 'btn-quiet b-claude-dismiss', title, () => ClaudeInbox.dismiss(e, i), true);
    const ok = (label, cls, title) => act(p, it, where, label, cls, title, () => ClaudeInbox.apply(e, i), true);
    if (c.do === 'done') {
      if (!r.ok) {
        const was = p.todos.some(t => t.done && tkey(t.text) === tkey(c.task));
        return { text: [mine ? 'Wants this task ticked off' : ['Wants ', name(null), ' ticked off'], was ? '. It is ticked off already.' : '. It is not open here.'], acts: [no('Put it away: nothing changes')] };
      }
      const on = r.t.repeat ? ', on to its next date' : '';
      return { text: mine ? ['Wants this task ticked off', on, '.'] : ['Wants ', name(r.t), ' ticked off', on, '.'],
        acts: [ok('Tick it', 'b-claude-tick', 'Tick off ' + r.t.text + (on ? ': it moves on to its next date' : '')), no('Leave ' + r.t.text + ' open')] };
    }
    if (c.do === 'edit-description') {
      if (!r.ok) return { text: ['Wants a new description for ', name(null), '. It is not in this project.'], acts: [no('Put it away: nothing changes')] };
      return { text: mine ? ['Wants a new description for this task.'] : ['Wants a new description for ', name(r.t), '.'],
        acts: [readBtn('A new description for ' + r.t.text, () => readDescription(r.t, c)), ok('Apply', 'b-claude-apply', 'Give ' + r.t.text + ' the new description'), no('Keep the description ' + r.t.text + ' has')] };
    }
    if (c.do === 'replace-plan') {
      if (!r.ok) return { text: ['Sent a new plan the city cannot read.'], acts: [no('Put it away: nothing changes')] };
      return { text: ['Wants to replace the plan with ' + ClaudeInbox.planSize(r.plan) + '.'],
        acts: [readBtn('A new plan for ' + p.name, () => readPlanBody(r.plan)), ok('Apply', 'b-claude-apply', 'Replace the About, milestones and tasks with the new plan'), no('Keep the plan ' + p.name + ' has')] };
    }
    return { text: ['Sent a change the city does not know.'], acts: [no('Put it away')] };
  }
  const askParts = (p, e, task, it, where) => ClaudeInbox.openIdx(e).map(i => { const a = askOf(p, e, i, task, it, where); return partEl('ask ' + e.changes[i].do, a.text, a.acts); });
  /* A report's parts, under its finish: what Claude added, with Read and Undo; each wizard round; what it asks. */
  function parts(p, rep, it, where) {
    const out = [];
    if (rep.add && addLive(p, rep.add)) {
      const u = undos.get(rep.id);
      out.push(partEl('added', ['Added ' + addedWords(p, rep.add) + '.'], [readBtn('What Claude added to ' + p.name, () => readAdded(p, rep.add)),
        u ? act(p, it, where, 'Undo', 'ld-undo', 'Take back what Claude added', () => { ClaudeInbox.undo(p, u); undos.delete(rep.id); }, true) : null]));
    }
    for (const r of rep.rounds) {
      const t = p.todos.find(x => x.id === r.tid), uk = rep.id + ':' + r.tid, u = undos.get(uk);
      if (!t || !t.round || t.round.title !== r.title) continue;                        // taken off, or another round since
      const same = tkey(t.text) === tkey(rep.task);
      out.push(partEl('round', same ? ['Attached a wizard round, ', h('bdi', null, t.round.title), '.'] : ['Attached a wizard round to ', taskLink(p, t, where, it), ', ', h('bdi', null, t.round.title), '.'],
        [u ? act(p, it, where, 'Undo', 'ld-undo', 'Take back the wizard round', () => { ClaudeInbox.undo(p, u); undos.delete(uk); }, true) : null]));
    }
    const e = entryOf(rep.entry);
    if (e) out.push(...askParts(p, e, rep.task, it, where));
    return out;
  }
  /* A finish heads its report (A1): Claude's summary under it (C2), then its parts. Tick it comes only from Claude
     asking to tick the task off (B3); a finish with no update keeps Tick it, with the start of the reply as its words. */
  function finishView(p, { task, at, s, rep, it = null, tick }, where) {
    const nodes = [...sayNodes(p, 'finished', { task }, task ? taskNamed(p, task) : null, where, it), ' ', whenEl(at)];
    if (rep) return { nodes, more: [wordsEl(rep.summary), ...parts(p, rep, it, where)].filter(Boolean), acts: [] };
    const tk = tick !== undefined ? tick : typeof ClaudeWork === 'undefined' ? null : s ? ClaudeWork.taskOf(p, s)
      : it && it.ref.task ? ClaudeWork.taskOf(p, { task: it.ref.task, project: it.ref.project || '' }) : null;
    return { nodes, more: [wordsEl(plainReply(s && s.reply))].filter(Boolean),
      acts: tk ? [act(p, it, where, 'Tick it', 'b-claude-tick', 'Tick off ' + tk.text + ', the task this session started from', () => ClaudeWork.tick(p, tk))] : [] };
  }
  /* On its own: what Claude added, with Read and Undo, and its summary. */
  function addedView(p, it, where) {
    const rep = reportOf(it.ref && it.ref.report), uk = rep ? rep.id : it.id, u = undos.get(uk), live = !!rep && !!rep.add && addLive(p, rep.add);
    return { nodes: [...sayNodes(p, 'added', { what: live ? addedWords(p, rep.add) : it.v.what }, null, where, it), ...(rep ? [' ', whenEl(rep.at, 'Sent ')] : [])],
      more: [rep ? wordsEl(rep.summary) : null].filter(Boolean),
      acts: [live ? readBtn('What Claude added to ' + p.name, () => readAdded(p, rep.add)) : null,
        u ? act(p, it, where, 'Undo', 'ld-undo', 'Take back what Claude added', () => { ClaudeInbox.undo(p, u); undos.delete(uk); }) : null].filter(Boolean) };
  }
  function roundView(p, it, where) {
    const rep = reportOf(it.ref && it.ref.report), uk = rep ? rep.id + ':' + it.ref.tid : it.id, u = undos.get(uk);
    return { nodes: [...sayNodes(p, 'round', it.v, taskFor(p, it), where, it), ...(rep ? [' ', whenEl(rep.at, 'Sent ')] : [])],
      more: [rep && !rep.add ? wordsEl(rep.summary) : null].filter(Boolean),
      acts: u ? [act(p, it, where, 'Undo', 'ld-undo', 'Take back the wizard round', () => { ClaudeInbox.undo(p, u); undos.delete(uk); })] : [] };
  }
  /* On its own: what Claude asks first, named (the change itself, never the summary), with its time; one change has its
     buttons on the line, several a short line each. */
  function asksView(p, e, it, where) {
    if (!e) return { nodes: sayNodes(p, 'asks', { change: it && it.v.change || 'a change' }, null, where, it), more: [], acts: [] };
    const rep = reportOf(it && it.ref.report) || [...st.reports].reverse().find(r => r.entry === e.name) || null, open = ClaudeInbox.openIdx(e);
    const more = [rep && (rep.add || rep.rounds.length) ? null : wordsEl(e.summary)];
    if (open.length > 1) more.push(...askParts(p, e, '', it, where));          // no finish heads it, so each names its task
    return { nodes: [...sayNodes(p, 'asks', { change: ClaudeInbox.gist(p, e) }, null, where, it), ' ', whenEl(e.at || (rep ? rep.at : Date.now()), 'Sent ')],
      more: more.filter(Boolean), acts: open.length === 1 ? askOf(p, e, open[0], '', it, where).acts : [] };
  }
  /* Any item: { nodes, more, acts }, the same on the status card, the leader card and in the bubble. */
  function viewOf(p, it, where) {
    if (it.moment === 'finished') {
      const s = typeof ClaudeWork !== 'undefined' ? ClaudeWork.sessionsOf(p).find(x => x.session === it.ref.session) || null : null;
      return finishView(p, { task: it.v.task, at: s && s.state === 'done' ? s.at : it.at, s, rep: reportOf(it.ref.report), it }, where);
    }
    if (it.moment === 'added') return addedView(p, it, where);
    if (it.moment === 'round') return roundView(p, it, where);
    if (it.moment === 'asks') return asksView(p, entryOf(it.ref.entry), it, where);
    return { nodes: sayNodes(p, it.moment, it.v, taskFor(p, it), where, it), more: [], acts: actsOf(p, it, where) };
  }
  function actsOf(p, it, where) {
    const out = [];
    if (it.moment === 'answers') {
      const t = p.todos.find(x => x.id === it.ref.tid);
      if (t) out.push(act(p, it, where, 'Open', 'ld-open', 'Open ' + t.text + ' and its round', () => { if (where === 'say') { readIds([it.id]); hide({ read: false }); } FullView.openTask(p.id, t.id); }));
    }
    return out;
  }

  /* ---------- the status card and the project view: a building's news, read as they show it ---------- */
  /* Its waiting news, read now, and held while its status card or project view shows it. */
  function take(pid) {
    const mine = live().filter(it => it.pid === pid);
    if (mine.length) {
      const have = held.get(pid) || [];
      held.set(pid, [...have, ...mine.filter(it => !have.some(x => x.id === it.id))]);
      if (bub && bub.list.some(it => it.pid === pid && mine.includes(it))) { /* the bubble keeps showing what it shows */ }
      readIds(mine.map(it => it.id));
    }
    return sortItems(held.get(pid) || []);
  }
  const dropHeld = (pid, id) => { const l = held.get(pid); if (l) held.set(pid, l.filter(x => x.id !== id)); };
  /* Let go of what a building held once neither its status card nor its project view shows it. */
  function release(pid) {
    if (!pid) return;
    if (Bubble.openId() === pid || (typeof FullView !== 'undefined' && FullView.shows(pid))) return;
    held.delete(pid);
  }
  /* One line the leader says, with what goes under it and its buttons. */
  function lineEl(nodes, { more = [], acts = [], moment = '', cls = '' } = {}) {
    return h('div', { class: 'ld-line' + (cls ? ' ' + cls : ''), 'data-moment': moment },
      h('p', { class: 'ld-says', dir: 'auto' }, ...nodes), ...more, acts.length ? h('div', { class: 'ld-acts' }, acts) : null);
  }
  /* The status card: its news, then what Claude is doing there, in the leader's voice, for as long as the card showed
     it before (B3): working, waiting, finished, stopped, and what asks first while it waits. A finish an update reports
     on is one report, its parts under it (A1, A2); an update a working session sent shows under its working line.
     Nothing is said twice. */
  function cardLines(p) {
    const lines = [], said = new Set();
    const voice = typeof ClaudeWork !== 'undefined' ? ClaudeWork.voice(p) : [];
    const pend = typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.pending().filter(e => tkey(e.project) === tkey(p.name)) : [];
    /* under the project view the card is hidden: what it would say waits for the leader card, or the News section */
    const mine = typeof FullView !== 'undefined' && FullView.shows(p.id) ? sortItems(held.get(p.id) || []) : take(p.id);
    const VOICE_RANK = { waiting: 1, working: 1.2, failed: 1.4, finished: 5 };      // Claude's own order: waiting, working, stopped, finished
    for (const x of voice) {
      const rep = x.moment === 'finished' ? finishReport(x.s) : heldReport(x.s);
      if (rep) { said.add(rep.id); if (rep.entry) said.add('e:' + rep.entry); }
      if (x.moment === 'finished') {
        const v = finishView(p, { task: x.v.task, at: x.s.at, s: x.s, rep, tick: x.tick }, 'card');
        lines.push({ rank: rep ? repRank(p, rep) : VOICE_RANK.finished, el: lineEl(v.nodes, { more: v.more, acts: v.acts, moment: 'finished', cls: 'b-claude ' + x.s.state }) });
      } else {
        const t = x.s.task || x.s.ask ? taskNamed(p, x.s.task || x.s.ask) : null;
        lines.push({ rank: VOICE_RANK[x.moment] ?? 5, el: lineEl(sayNodes(p, x.moment, x.v, t, 'card'),
          { more: rep ? [wordsEl(rep.summary), ...parts(p, rep, null, 'card')].filter(Boolean) : [], moment: x.moment, cls: 'b-claude ' + x.s.state }) });
      }
    }
    for (const it of mine) {
      if (it.ref && it.ref.report && said.has(it.ref.report)) continue;
      if (it.moment === 'asks' && pend.some(e => e.name === it.ref.entry)) continue;           // said below, for as long as it waits
      if (NEWS_CLAUDE.has(it.moment) && it.moment !== 'asks' && voice.some(x => x.s.session === it.ref.session)) continue;
      const v = viewOf(p, it, 'card');
      lines.push({ rank: rankOf(it), el: lineEl(v.nodes, { more: v.more, acts: v.acts, moment: it.moment }) });
    }
    for (const e of pend) {
      if (said.has('e:' + e.name)) continue;
      const v = asksView(p, e, null, 'card');
      lines.push({ rank: NEWS_RANK.asks, el: lineEl(v.nodes, { more: v.more, acts: v.acts, moment: 'asks', cls: 'b-claude-asks' }) });
    }
    return lines.sort((a, b) => a.rank - b.rank).map(x => x.el);
  }
  /* The leader card in the project view: its news for this building, else nothing (its greeting shows). */
  function viewLines(p) {
    return take(p.id).filter(it => !NEWS_CLAUDE.has(it.moment) || it.moment === 'finished')
      .map(it => { const v = viewOf(p, it, 'view'); return lineEl(v.nodes, { more: v.more, acts: v.acts, moment: it.moment }); });
  }

  /* ---------- Reports: the leader's face beside a building's row ---------- */
  function reportFace(p, size = 24) {
    const l = leaderOf(p);
    if (!l) return null;
    const f = Leaders.face(l, size);
    f.classList.add('rp-leader');
    f.title = leaderName(l) + (l.role ? ', ' + l.role : '');
    f.removeAttribute('aria-hidden');
    f.setAttribute('role', 'img');
    f.setAttribute('aria-label', 'Led by ' + leaderName(l));
    return f;
  }

  function init() {
    started = true;
    const b = box();
    $('#ldSayClose').innerHTML = iconSvg('close', 16);
    $('#ldSayClose').addEventListener('click', () => hide());
    b.addEventListener('keydown', e => { if (e.key === 'Escape' && bub) { e.stopPropagation(); e.preventDefault(); hide(); } });
    b.addEventListener('pointerdown', () => hold());
    window.addEventListener('storage', e => { if (e.key === KEY) { st = load(); renderSection(); } });
    Art.onLoad(id => { if (bub && bub.list[bub.i] && bub.list[bub.i].pid === id) draw(); });   // its building's own art, loaded after it opened
    check();
    claude();
    renderSection();
    pump();
    setInterval(check, 60000);                               // a new day, a new week, and pace slipping while the city stays open
  }
  return { init, check, claude, ticked, add, report, renderSection, take, release, cardLines, viewLines, reportFace, yieldTo, hide, pump, redraw, plainReply,
    isShowing: () => !!bub, isHeld: () => !!bub && !bub.auto, items: () => sortItems(live()), lineOf,
    _test: { sayMs: ms => { sayMs = ms; }, typeMs: ms => { typeMs = ms; }, talk: () => ({ id: talk.id, n: talk.n, done: talk.done }), state: () => JSON.parse(JSON.stringify(st)), bubble: () => bub && { ids: bub.list.map(x => x.id), i: bub.i, auto: bub.auto },
      forget: () => { st = fresh(); save(); held.clear(); undos.clear(); }, held: pid => (held.get(pid) || []).map(x => x.id), reports: () => JSON.parse(JSON.stringify(st.reports)) } };
})();
