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
const NEWS_RANK = { behind_more: 0, behind_day: 0, behind: 0, waiting: 1, asks: 1, failed: 1, t3closed: 1, due: 2, due_many: 2, one_left: 3,
  added: 4, round: 4, finished: 5, answers: 5, week: 6, week_quiet: 6, working: 7 };
const NEWS_OPENS = new Set(['behind', 'behind_more', 'behind_day', 'due', 'due_many', 'one_left', 'added', 'round', 'waiting', 'asks', 'failed', 't3closed']);
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
  const voiceOf = l => ({ k: 'ld:' + l.id, l, name: leaderName(l), role: l.role, color: l.color });
  function speakerOf(p) {
    const l = p && leaderOf(p);
    return l ? voiceOf(l) : { k: 'px', l: null, name: 'Proxima Pace', role: 'Productivity Inspector', color: '#8FD0F7' };
  }
  /* Who says an item: Quill says a round Claude attached on its own and a round's answers, for every building (0.1.69,
     Leader Bubbles, Round 2, C1); its building's leader, or Proxima, the rest. */
  const speakerFor = it => (it && QUILL_MOMENTS.has(it.moment) ? voiceOf(quillLeader()) : speakerOf(getProject(it.pid)));
  /* A speaker's face; Proxima breathes too while she brings a building's news in the leaders' place (0.1.62). */
  const faceOf = (sp, size) => (sp.l ? Leaders.face(sp.l, size) : Leaders.breathe(Proxima.faceEl(size), 'proxima'));
  const lineOf = it => leaderSay(it.moment, it.v);
  /* The most pressing first; among the same, the leaders before Proxima, as in the side bar, then the oldest first. */
  const proximaSays = it => (speakerFor(it).k === 'px' ? 1 : 0);
  const sortItems = list => [...list].sort((a, b) => rankOf(a) - rankOf(b) || proximaSays(a) - proximaSays(b) || a.at - b.at);
  const live = () => st.items.filter(it => getProject(it.pid) && !heldGone(it));

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
  /* a send held while T3 is closed is news only while the page keeps it: gone after a reload, or once sent */
  const heldGone = it => it.moment === 't3closed' && !(typeof T3 !== 'undefined' && T3.held(it.ref && it.ref.held));
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
          const task = ClaudeWork.what(p, s);
          if (s.state === 'waiting') {
            const key = 'waiting:' + s.session + ':' + s.since;
            if (!wasRaised(key)) { raise(p, 'waiting', { task, ...(s.wait ? { wait: s.wait } : {}) }, { session: s.session }, key); moved = true; }
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
    if (moved) after(); else renderSection();               // the leaders at work, and their thoughts, follow every change (0.1.92)
  }

  /* ---------- Claude's reports (0.1.68, Claude's News on the Status Card, A1) ---------- */
  const tkey = s => String(s || '').trim().toLowerCase();
  const finKey = s => 'finished:' + s.session + ':' + tkey(s.task || s.ask || 'a task').slice(0, 160);
  const reportOf = id => (id && st.reports.find(r => r.id === id)) || null;
  const entryOf = name => (name && typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.pending().find(e => e.name === name) : null) || null;
  /* The reports a finish heads: every one its session sent in the turn that finished, known by the turn's reply, the
     oldest first. Two updates in one turn, or two that came in together while the city was closed, are one report
     under one finish (0.1.95); until then a finish carried only the last, and the first was said nowhere. */
  const finishReports = s => st.reports.filter(r => r.sid === s.session && r.fin && r.reply === (s.reply || ''));
  /* The reports a session still working has sent, waiting for its finish. */
  const heldReports = s => st.reports.filter(r => r.sid === s.session && !r.alone && !r.fin);
  /* A finish item's reports: the list since 0.1.95, else the one it carried. */
  const repsOf = it => (it && it.ref ? (Array.isArray(it.ref.reports) ? it.ref.reports : it.ref.report ? [it.ref.report] : []) : []).map(reportOf).filter(Boolean);
  /* The task a finish or a working line names: the session's own, else, for a session that has none (a thread started
     in T3 itself, or a prompt typed in a terminal), the task its update names (0.1.95). */
  const ownTask = (task, s, reps) => { const r = !(s && s.task) && reps.find(x => x.task); return r ? r.task : task; };
  /* The session an update came from: the one working on the task it names (or that just finished it); else one with no
     task of its own, since the city cannot tell what that one works on (0.1.95: a thread started in T3 sent its
     updates for a task, and each was said on its own); else, when the update names none of its own, any. From those:
     the one session working on the building, or the one that finished there a moment ago, or whose run the update was
     written in, so updates that wait while the city is closed still find their finish. */
  function sessionFor(p, rep, named) {
    if (typeof ClaudeWork === 'undefined') return null;
    const all = ClaudeWork.sessionsOf(p), k = tkey(rep.task), now = Date.now();
    const busy = s => s.state === 'working' || s.state === 'waiting';
    const best = list => [...list].sort((a, b) => busy(b) - busy(a) || b.at - a.at)[0] || null;
    let ss = all;
    if (k) {
      const m = all.filter(s => tkey(s.task || s.ask) === k && (busy(s) || (s.state === 'done' && now - s.at < FIN_NEAR)));
      if (m.length) return best(m);
      if (named) ss = all.filter(s => !s.task);
    }
    const b = ss.filter(busy);
    if (b.length) return b.length === 1 ? b[0] : null;
    const w = rep.written || 0;
    const d = ss.filter(s => s.state === 'done' && (now - s.at < FIN_JUST || (w && s.started && w >= s.started - FIN_JUST && w <= s.at + FIN_JUST)));
    return d.length === 1 ? d[0] : null;
  }
  /* An update Claude sent (the inbox, 0.1.68): what it added, with Undo, what it asks first, and its summary, as one
     report. Its session still working, it waits for the finish; finished, it is said under the finish; with no session,
     it is said on its own, as before: what it added, each round, and what it asks. Said once the poll that brought it
     is done (claude), so what it asks is read by then. */
  function report(p, { task = '', named = false, summary = '', undo = null, entry = '', written = 0 } = {}) {
    if (!p) return null;
    const upd = undo && Array.isArray(undo.updated) ? undo.updated : [];
    const add = undo && (undo.todos.length || undo.notes.length || undo.links.length || upd.length) ? { todos: [...undo.todos], notes: [...undo.notes], links: [...undo.links], updated: upd.map(w => w.id) } : null;
    const rounds = (undo && undo.rounds || []).map(r => { const t = p.todos.find(x => x.id === r.id); return { tid: r.id, title: t && t.round ? t.round.title : '' }; });
    if (!add && !rounds.length && !entry) return null;
    const rep = { id: uid('rp'), pid: p.id, task, summary, at: Date.now(), written: written || 0, sid: '', fin: 0, reply: '', alone: false, entry, add, rounds };
    const none = { todos: [], ms: [], notes: [], links: [], rounds: [], updated: [] };
    if (add) undos.set(rep.id, { ...none, todos: undo.todos, ms: undo.ms, notes: undo.notes, links: undo.links, updated: upd });
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
  /* Under its finish: the finish's news carries it, with any other report of the same turn, and opens by itself again
     while it holds something to act on. A session with no task of its own names the task the report names. */
  function attach(p, rep, s) {
    rep.fin = s.at; rep.reply = s.reply || '';
    const key = finKey(s), it = st.items.find(x => x.key === key), task = s.task || rep.task || ClaudeWork.what(p, s);
    if (it) {
      const ids = repsOf(it).filter(r => r.reply === rep.reply).map(r => r.id);
      it.ref.reports = [...ids.filter(id => id !== rep.id), rep.id]; it.ref.report = rep.id; it.popped = false;
      if (!s.task && rep.task) it.v = { ...it.v, task: ownTask(it.v.task, s, repsOf(it)) };
    } else raise(p, 'finished', { task }, { session: s.session, task: s.task, project: s.project, report: rep.id, reports: [rep.id] }, key);
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
    ns: add.notes.map(id => allNotes(p).find(n => n.id === id)).filter(Boolean), ls: add.links.map(id => p.links.find(l => l.id === id)).filter(Boolean),
    us: (add.updated || []).map(id => allNotes(p).find(n => n.id === id)).filter(Boolean) });     // notes Claude put in a task, and brought up to date (0.1.71)
  const addLive = (p, add) => { const a = addedOf(p, add); return a.ts.length + a.ns.length + a.ls.length + a.us.length > 0; };
  /* What Claude added, named, not just counted: one of a kind by its name, more by their count. */
  function addedWords(p, add) {
    const a = addedOf(p, add);
    const kind = (list, one, many, name) => (!list.length ? '' : list.length > 1 ? plural(list.length, one, many) : 'a ' + one + (name(list[0]) ? ', ' + cut(name(list[0]), 40) : ''));
    const bits = [kind(a.ts, 'task', 'tasks', t => t.text), kind(a.ns, 'note', 'notes', n => n.title), kind(a.ls, 'link', 'links', l => l.label || suggestLabel(l.url)),
      a.us.length ? (a.us.length > 1 ? 'new versions of ' + plural(a.us.length, 'note', 'notes') : 'a new version of ' + cut(noteHead(a.us[0]), 40)) : ''].filter(Boolean);
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
    if (it.moment === 'finished') return repsOf(it).some(rep => repActs(p, rep));
    return false;
  }
  /* A report ranks by the most pressing thing in it: what asks first, then what Claude added, then the finish. */
  function repRank(p, rep) {
    const e = entryOf(rep.entry);
    if (e && ClaudeInbox.openIdx(e).length) return NEWS_RANK.asks;
    return repActs(p, rep) ? NEWS_RANK.added : NEWS_RANK.finished;
  }
  function rankOf(it) {
    const p = it.moment === 'finished' ? getProject(it.pid) : null, reps = p ? repsOf(it) : [];
    return reps.length ? Math.min(...reps.map(rep => repRank(p, rep))) : NEWS_RANK[it.moment] ?? 9;
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
      const sp = speakerFor(it);
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
  /* ---------- the leaders at work (0.1.92, Brainstorm 1, Round 2, i6: "the leaders who are currently working will show
     as working in the side bar", and Round 1, T1, The leader thinks it) ---------- */
  /* Each leader whose building Claude works on, Proxima for one with no leader, heads News: its face with Claude's
     spark, wearing a thought bubble with Claude's latest thought, as the wizard's companions think, moving on as Claude
     thinks; with no thought (hooks from before 0.1.92, or another agent), the working line. A click shows the building
     and its card, which says what Claude is doing there. */
  const thoughtSeen = new Map();                             // a speaker: the thought it showed last, so a new one moves in
  function workRows() {
    if (typeof ClaudeWork === 'undefined') return [];
    const by = new Map(), when = s => s.thoughtAt || s.at;
    for (const p of DB.projects) {
      const ss = ClaudeWork.sessionsOf(p).filter(s => s.state === 'working');
      if (!ss.length) continue;
      const sp = speakerOf(p), s = [...ss].sort((a, b) => (!!b.thought - !!a.thought) || when(b) - when(a))[0], cur = by.get(sp.k);
      if (!cur) by.set(sp.k, { sp, p, s, n: ss.length });
      else { cur.n += ss.length; if ((!!s.thought - !!cur.s.thought) > 0 || (!!s.thought === !!cur.s.thought && when(s) > when(cur.s))) Object.assign(cur, { p, s }); }
    }
    return [...by.values()].sort((a, b) => a.sp.name.localeCompare(b.sp.name));
  }
  function renderWork() {
    const box = $('#newsWork');
    if (!box) return 0;
    const rows = workRows();
    const els = rows.map(({ sp, p, s, n }) => {
      const what = ClaudeWork.what(p, s), text = s.thought || leaderSay('working', { task: what, ago: relAgo(s.since) });
      const moved = !!s.thought && thoughtSeen.has(sp.k) && thoughtSeen.get(sp.k) !== s.thought;
      thoughtSeen.set(sp.k, s.thought || '');
      const who = sp.name + (sp.role ? ', ' + sp.role : '');
      return h('div', { class: 'news-work', 'data-k': sp.k, 'data-pid': p.id },
        h('button', { class: 'news-work-face', type: 'button', title: who + ': Claude is working on ' + what + ' in ' + p.name + (n > 1 ? ', and ' + plural(n - 1, 'more', 'more') : '') + '. Talk about it.',
          'aria-label': sp.name + ' is at work on ' + p.name, onclick: () => { Menu.closeDrawer(); openFace(sp.k, { session: s.session }); } },
          faceOf(sp, 40), h('span', { class: 'news-work-spark', 'aria-hidden': 'true', html: iconSvg('claude', 12) })),
        h('p', { class: 'news-thought' + (s.thought ? '' : ' plain') + (moved ? ' new' : ''), dir: 'auto', title: s.thought ? 'Claude thinks, working on ' + what + ': ' + s.thought : text }, h('span', null, text)));
    });
    for (const k of [...thoughtSeen.keys()]) if (!rows.some(r => r.sp.k === k)) thoughtSeen.delete(k);
    box.replaceChildren(...els);
    box.hidden = !els.length;
    return els.length;
  }
  function renderSection() {
    const sec = $('#sbNews'), box = $('#newsList');
    if (!sec) return;
    const working = renderWork();
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
    /* Quiet (0.1.91): the switch in the section's head, the section kept in view while it is on */
    const q = typeof Hold !== 'undefined' && Hold.quiet(), qb = $('#newsQuiet');
    if (qb) { qb.setAttribute('aria-pressed', String(q)); qb.title = q ? 'Quiet is on: news waits here. Turn it off to hear it' : 'Quiet: every bubble waits here, until you turn it off'; }
    sec.hidden = !tiles.length && !q && !working;
    sec.classList.toggle('quiet', q);
    if (q && !tiles.length && !working) tiles.push(h('p', { class: 'news-quiet-note' }, 'Quiet: news waits here.'));
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
    const ids = live().filter(it => speakerFor(it).k === k).map(it => it.id);
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
      || Panel.isOpen() || Confirm.isOpen() || !sayRoom();
  }
  /* What opens by itself: the news that opens by itself and has not shown yet, unless its building's card has it. */
  function pump() {
    clearTimeout(waitT);
    if (!started || bub) return;
    let due = sortItems(live().filter(it => !it.popped && opens(it)));
    if (!due.length) return;
    if (blocked()) { waitT = setTimeout(pump, 500); return; }
    /* held for a break (0.1.91): while you are at something, only what answers your own click opens now, and with
       Quiet on, nothing */
    if (typeof Hold !== 'undefined' && Hold.busy()) {
      const now = Hold.quiet() ? [] : due.filter(it => it.ref && it.ref.direct);
      if (!now.length) { waitT = setTimeout(pump, 500); return; }
      due = now;
    }
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
  /* A leader's conversations with Claude on its buildings, as topics (0.1.94, L1: "each conversation with an agent is
     one topic"; i5: each leader carries the conversations of every project it leads, its building named on each):
     each session at work, waiting, stopped or finished there that no piece of news already holds. Not news: nothing is
     kept or read. */
  function convItems(k, have) {
    if (typeof ClaudeWork === 'undefined') return [];
    const out = [], covered = new Set(have.filter(it => it.ref && it.ref.session).map(it => it.ref.session));
    for (const p of DB.projects) {
      if (speakerOf(p).k !== k) continue;
      for (const x of ClaudeWork.voice(p)) {
        if (covered.has(x.s.session)) continue;
        out.push({ id: 'conv:' + x.s.session, key: 'conv:' + x.s.session, pid: p.id, moment: x.moment, v: x.v, ref: { session: x.s.session, task: x.s.task, project: x.s.project }, at: x.s.at, popped: true, conv: true });
      }
    }
    return out;
  }
  function openFace(k, { session = null } = {}) {
    const news = sortItems(live().filter(it => speakerFor(it).k === k));
    const list = [...news, ...convItems(k, news)];
    if (!list.length) return;
    if (typeof Gus !== 'undefined' && Gus.isSaying()) Gus.hush();
    show(list, { auto: false, k });
    if (session) { const at = list.findIndex(it => it.ref && it.ref.session === session); if (at > 0) { bub.i = at; draw(); } }
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
    if (auto && typeof Sound !== 'undefined') Sound.bubble();           // opening by itself: its sound, then the voice (0.1.78)
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
    const sp = speakerFor(it), n = bub.list.length;
    b.style.setProperty('--ld', sp.color);
    b.classList.toggle('px-voice', !sp.l);
    b.dataset.k = sp.k; b.dataset.moment = it.moment;
    $('#ldSayFace').replaceChildren(faceOf(sp, sayFace()));             // 100 px, 64 on a small screen (0.1.75, L2)
    $('#ldSayName').textContent = sp.name;
    $('#ldSayRole').textContent = sp.role || '';
    $('#ldSayRole').hidden = !sp.role;
    const keep = b.contains(document.activeElement) ? keyOf(document.activeElement) : null;
    /* the building: a click goes to it on the map, as Go to it does, without opening it (0.1.60) */
    $('#ldSayWhere').replaceChildren(h('button', { class: 'ld-say-bld', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } },
      h('span', { class: 'ld-say-thumb', 'aria-hidden': 'true' }, MapView.thumb(p)), h('bdi', null, p.name)));
    const v = viewOf(p, it, 'say');
    $('#ldSayText').replaceChildren(...v.nodes);
    T.speak(it.id, voiceKey(sp));
    $('#ldSayMore').replaceChildren(...v.more);
    $('#ldSayActs').replaceChildren(...[...v.acts,
      h('button', { class: 'btn btn-small btn-quiet ld-go', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } }, 'Go to it'),
      /* the topics, flipped with arrows (0.1.94, i5's variant), in place of Next */
      n > 1 ? h('span', { class: 'ld-flip ld-say-flip', role: 'group', 'aria-label': 'Topics' },
        h('button', { id: 'ldSayPrev', class: 'icon-btn ld-flip-btn', type: 'button', disabled: bub.i === 0, 'aria-label': 'The topic before', title: 'The topic before', html: iconSvg('back', 14), onclick: () => { hold(); prev(); } }),
        h('span', { id: 'ldSayCount', class: 'ld-say-count ld-flip-n' }, (bub.i + 1) + ' of ' + n),
        h('button', { id: 'ldSayNext', class: 'icon-btn ld-flip-btn next', type: 'button', disabled: bub.i >= n - 1, 'aria-label': 'Next', title: 'The next topic', html: iconSvg('back', 14), onclick: () => { hold(); next(); } })) : null].filter(Boolean));
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
  function prev() {
    if (!bub || bub.i <= 0) return;
    bub.i--;
    draw();
  }
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
     whole; Next types the next one. Motion on Still shows it whole, with the face still. Since 0.1.78 (City Sounds) Gus's
     and Proxima's bubbles type theirs too, and each line carries its speaker's voice, a blip per letter. */
  const TYPE_MS = 26, TYPE_ALL_MS = 1800;                   // a letter every 26 ms, a long line in 1.8 seconds at most
  let typeMs = TYPE_MS;
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
  /* A bubble's line and face: speak(id, who) types the line, paced by the clock a frame at a time, so a busy map makes
     no letter wait; who is the voice it carries (Sound.say), a speaker or a voice itself, and its speed paces the
     letters too (0.1.82), so a quick voice types its line quicker. */
  function typer(textSel, faceSel) {
    let talk = { id: null, n: 0, done: false, raf: 0, voice: null };
    const quiet = () => { if (talk.voice) talk.voice.stop(); talk.voice = null; };
    function speak(id, who = null) {
      const el = $(textSel), f = $(faceSel);
      cancelAnimationFrame(talk.raf);
      if (talk.id !== id) { quiet(); talk = { id, n: 0, done: false, raf: 0, voice: null }; }
      if (talk.done || Motion.still() || typeMs <= 0) { settle(); return; }
      const ls = letters(el);
      if (!ls.length) { settle(); return; }
      const speed = who && typeof Sound !== 'undefined' && Sound.voices ? Sound.voices.speed(who) : 1;
      const every = Math.max(8, Math.min(typeMs, TYPE_ALL_MS / ls.length) / speed);
      talk.n = Math.min(talk.n, ls.length);
      ls.slice(0, talk.n).forEach(x => x.classList.add('on'));
      el.classList.add('typing');
      if (f) f.classList.add('talking');
      if (!talk.voice && who && typeof Sound !== 'undefined') talk.voice = Sound.say(who, ls.slice(talk.n).map(x => x.textContent), every / 1000);
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
      const el = $(textSel), f = $(faceSel);
      if (f) f.classList.remove('talking');
      if (!el) return;
      el.classList.remove('typing');
      const ty = $$('.ty', el);
      if (!ty.length) return;
      for (const x of ty) x.replaceWith(x.firstChild || '');
      el.normalize();
    }
    /* Closed: the line stops, voice and all. */
    function hush() { settle(); quiet(); talk = { id: null, n: 0, done: false, raf: 0, voice: null }; }
    return { speak, settle, hush, state: () => ({ id: talk.id, n: talk.n, done: talk.done }) };
  }
  const T = typer('#ldSayText', '#ldSayFace');
  const hush = () => T.hush();
  /* The voice a speaker talks in: Proxima's for a building with no leader; the voice picked for a leader (0.1.82), a
     leader named Quill's too; else Quill's for him, or the leader's own, from its id. */
  const voiceKey = sp => (!sp.l ? 'proxima' : !sp.l.voice && leaderName(sp.l).toLowerCase() === 'quill' ? 'quill' : 'ld:' + sp.l.id);

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
      return taskA(p, t, x.text, 'Open ' + x.full, where, it);
    });
  }
  /* A task named in a line: a link in its own color, a click opening it. A link and not a button since 0.1.95: Chrome
     lays a button out as a box of its own, so a title that wrapped broke the line around it, and the line's end fell
     out of sight ("Wants Get Claude to understand the game and its art" with no "ticked off"). */
  function taskA(p, t, text, title, where, it) {
    return h('a', { class: 'ld-task', href: '#', dir: 'auto', title, 'data-task': t.id, onclick: e => {
      e.preventDefault(); e.stopPropagation();
      if (where === 'say' && it) { readIds([it.id]); hide({ read: false }); }
      FullView.openTask(p.id, t.id);
    } }, text);
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
  const taskLink = (p, t, where, it) => taskA(p, t, lineTitle(t.text), 'Open ' + t.text, where, it);
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
  /* Open in T3 on Claude's lines, for a task whose send started a T3 thread (0.1.90, City as My Terminal): it opens the
     task's latest thread in T3's window, its tooltip saying where it lands, the agent and the thread's state. */
  function t3Act(p, t, it, where) {
    const th = t && typeof T3 !== 'undefined' ? T3.latest(t) : null;
    if (!th || !th.env) return null;
    return act(p, it, where, 'Open in T3', 'ld-t3', T3.openTitle(p, t, th), () => T3.openThread(th), true);
  }
  /* The same for a session's T3 thread the watcher sees (0.1.93, W2c), a thread started in T3 itself included. */
  function t3ActW(p, w, it, where) {
    if (!w || !w.env || typeof T3 === 'undefined') return null;
    const st = T3.T3_STATE[w.status] || '';
    return act(p, it, where, 'Open in T3', 'ld-t3', 'Opens its T3 thread' + (w.title ? ', ' + w.title : '') + (st ? ': ' + (w.approval ? 'waiting for your OK' : { waiting: 'waiting on you', working: 'working', failed: 'stopped', done: 'handed back to you' }[st]) : '') + '.',
      () => T3.openWatched(w), true);
  }
  const watchedOf = (p, s) => (s && typeof T3 !== 'undefined' ? T3.sessionThread(p, s) : null);

  /* ---------- talking back (0.1.94, City as My Terminal, Round 1, R1 to R3, L4, and Brainstorm 1, i6) ---------- */
  /* A conversation with Claude in a T3 thread the watcher sees ends with what it asks and a reply box, in the bubble
     and on the cards alike (i6: "I want to unify everything"). What it asks: each question with its choices as buttons,
     like the report buttons (L4), the one Claude recommends marked with the wizard's hat, one click taking it (i6,
     Yellow's change); several questions, or several choices allowed, are sent once each is answered. An approval goes
     to T3 (i6: "take you to t3"). The reply box (R1): Send steers a running turn, starts an idle thread on it; Queue,
     behind the more button (R2, his note: "Queue Is almost hidden"), sends it as the next turn; while Claude asks, what
     is typed answers its question (R3). Each goes through the T3 helper on the click. What is typed is kept per thread
     while the page stays open, so a redraw never loses it. */
  const drafts = new Map(), picks = new Map(), answered = new Map();
  const REC = /\s*\(recommended\)\s*$/i;
  const sessOf = (p, id) => (id && typeof ClaudeWork !== 'undefined' ? ClaudeWork.sessionsOf(p).find(x => x.session === id) || null : null);
  function sendAnswers(p, w, req) {
    const got = picks.get(req.request) || {};
    const answers = {};
    for (const q of req.questions) {
      const v = got[q.id];
      if (v == null || (Array.isArray(v) && !v.length)) return false;
      answers[q.id] = v;
    }
    answered.set(req.request, answers);
    picks.delete(req.request);
    T3.answer(getProject(p.id), w, req.request, answers);
    hold();
    redrawTalk();
    return true;
  }
  function redrawTalk() { if (bub) draw(); Bubble.refresh(); Leaders.redrawCard(); }
  /* An answer T3 did not take: its choices come back, to try again. */
  function unanswer(request) { if (answered.delete(request)) redrawTalk(); }
  function askEl(p, w, where) {
    const req = w && w.asks && w.asks[0];
    if (!req || !req.questions || !req.questions.length) return null;
    const done = answered.get(req.request);
    if (done) return h('p', { class: 'ld-asked' }, 'Answered: ', h('bdi', null, Object.values(done).map(v => (Array.isArray(v) ? v.join(', ') : String(v)).replace(REC, '')).join('; ')), '. Waiting for Claude.');
    const got = picks.get(req.request) || {};
    const one = req.questions.length === 1 && !req.questions[0].multi;
    const box = h('div', { class: 'ld-ask', 'data-request': req.request });
    req.questions.forEach((q, qi) => {
      const sel = got[q.id];
      box.append(h('div', { class: 'ld-q' },
        q.header ? h('span', { class: 'ld-q-head', dir: 'auto' }, q.header) : null,
        h('p', { class: 'ld-q-text', dir: 'auto' }, q.question),
        h('div', { class: 'ld-q-opts', role: q.multi ? 'group' : 'radiogroup', 'aria-label': q.header || q.question },
          ...q.options.map((o, oi) => {
            const rec = REC.test(o.label), label = o.label.replace(REC, ''), on = q.multi ? Array.isArray(sel) && sel.includes(o.label) : sel === o.label;
            return h('button', { id: 'ldQ-' + where + '-' + qi + '-' + oi, class: 'btn btn-small ld-q-opt' + (rec ? ' rec' : '') + (on ? ' on' : ''), type: 'button', 'aria-pressed': String(on),
              title: (o.description ? o.description + '. ' : '') + (rec ? 'Claude recommends it. ' : '') + (one ? 'One click answers.' : q.multi ? 'Pick as many as fit.' : 'Pick one.'),
              onclick: () => {
                hold();
                const cur = { ...(picks.get(req.request) || {}) };
                if (q.multi) { const s = new Set(Array.isArray(cur[q.id]) ? cur[q.id] : []); if (s.has(o.label)) s.delete(o.label); else s.add(o.label); cur[q.id] = [...s]; }
                else cur[q.id] = o.label;
                picks.set(req.request, cur);
                if (!(one && sendAnswers(p, w, req))) redrawTalk();
              } }, rec ? h('span', { class: 'ld-q-rec', 'aria-hidden': 'true', html: hatSvg(13) }) : null, label);
          }))));
    });
    if (!one) {
      const ready = req.questions.every(q => got[q.id] != null && (!Array.isArray(got[q.id]) || got[q.id].length));
      box.append(h('button', { id: 'ldQSend-' + where, class: 'btn btn-small btn-accent ld-q-send', type: 'button', disabled: !ready,
        title: ready ? 'Send your answers to Claude' : 'Answer each question first', onclick: () => sendAnswers(p, w, req) }, 'Send answers'));
    }
    return box;
  }
  function replyEl(p, w, where) {
    if (!w || !w.env || w.approval) return null;
    const asking = w.asks && w.asks[0] && w.asks[0].questions && w.asks[0].questions.length && !answered.has(w.asks[0].request);
    const running = typeof T3 !== 'undefined' && T3.T3_STATE[w.status] === 'working';
    const send = mode => {
      const inp = $('#ldReply-' + where), text = inp ? inp.value.trim() : '';
      if (!text) { if (inp) inp.focus(); return; }
      hold();
      if (asking && mode !== 'queue') {
        const req = w.asks[0], q = req.questions.find(x => !(picks.get(req.request) || {})[x.id]) || req.questions[0];
        picks.set(req.request, { ...(picks.get(req.request) || {}), [q.id]: q.multi ? [text] : text });
        if (!sendAnswers(p, w, req)) { redrawTalk(); }
      } else T3.reply(getProject(p.id), w, text, mode === 'queue' ? 'queue' : running ? 'steer' : 'auto');
      drafts.delete(w.id);
      if (inp) inp.value = '';
    };
    const hint = asking ? 'Answer Claude' : running ? 'Steer Claude' : 'Reply to Claude';
    const says = asking ? 'Answer Claude’s question, or pick a choice above' : running ? 'Steer Claude, mid-turn' : 'Reply to Claude';
    const inp = h('input', { id: 'ldReply-' + where, class: 'field ld-reply-in', type: 'text', dir: 'auto', 'data-thread': w.id, placeholder: hint, 'aria-label': says, title: says, maxlength: '20000',
      oninput: e => { drafts.set(w.id, e.target.value); hold(); }, onfocus: () => hold(),
      onkeydown: e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); e.stopPropagation(); send(e.ctrlKey || e.metaKey ? 'queue' : 'send'); } } });
    inp.value = drafts.get(w.id) || '';
    const menuId = 'ldReplyMenu-' + where;
    const more = h('button', { id: 'ldReplyMore-' + where, class: 'icon-btn ld-reply-more', type: 'button', 'aria-haspopup': 'menu', 'aria-expanded': 'false', 'aria-label': 'More ways to send',
      title: 'Queue: send it as the next turn', html: iconSvg('more', 14), onclick: e => {
        e.stopPropagation(); hold();
        const m = $('#' + menuId);
        if (m) { m.remove(); more.setAttribute('aria-expanded', 'false'); return; }
        more.setAttribute('aria-expanded', 'true');
        more.closest('.ld-reply').append(h('div', { id: menuId, class: 'ld-reply-menu', role: 'menu' },
          h('button', { id: 'ldReplyQueue-' + where, class: 'oc-folder-opt', type: 'button', role: 'menuitem', title: 'Waits for Claude’s turn to end, then goes as its next turn',
            onclick: () => { send('queue'); const mm = $('#' + menuId); if (mm) mm.remove(); } },
            h('span', { class: 'oc-folder-name' }, 'Queue'), h('span', { class: 'oc-folder-full' }, 'Send it as the next turn, interrupting nothing'))));
        const q = $('#ldReplyQueue-' + where); if (q) q.focus();
      } });
    return h('div', { class: 'ld-reply' }, h('div', { class: 'ld-reply-row' }, inp,
      h('button', { id: 'ldReplySend-' + where, class: 'btn btn-small btn-accent ld-reply-send', type: 'button',
        title: asking ? 'Answers Claude’s question with what you typed' : running ? 'Steers Claude’s running turn' : 'Sends it to Claude now', onclick: () => send('send') }, 'Send'), more));
  }
  /* The extras of a conversation's line: what it asks, then the reply box, for a session whose T3 thread the watcher
     sees. */
  function talkEls(p, s, where) {
    const w = watchedOf(p, s);
    return w ? [askEl(p, w, where), replyEl(p, w, where)].filter(Boolean) : [];
  }
  const lastWords = w => (w && typeof T3 !== 'undefined' && T3.lastOf(w) ? wordsEl(plainReply(T3.lastOf(w))) : null);
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
      ...[...a.ns, ...a.us].map(n => { const t = noteTask(p, n.id);
        return crSec(n.title || 'A note', ...(t || a.us.includes(n) ? [crText((a.us.includes(n) ? 'Brought up to date' : 'A note') + (t ? ', in ' + t.text : ', in Notes') + '.', 'was')] : []),
          n.text ? crText(n.text) : crText('Nothing written in it.', 'was')); }),
      ...a.ls.map(l => { const lt = linkTarget(l); return crSec('A link', lt.href ? h('a', { class: 'cr-title', href: lt.href, target: lt.blank ? '_blank' : null, rel: 'noopener', dir: 'auto', title: lt.title }, lt.name) : h('b', { class: 'cr-title', dir: 'auto' }, lt.name),
        h('p', { class: 'cr-url', dir: 'ltr' }, l.url)); }),
    ];
  }
  const readDescription = (t, c) => [crSec('The new description', crText(String(c.description || '').trim())),
    crSec('Its description now', (t.description || '').trim() ? crText(t.description.trim(), 'was') : crText('No description yet.', 'was'))];
  /* A wizard round's Read (0.1.69, Leader Bubbles, Round 2, C1): the round in a small popup, the one Show the answers
     opens in the task panel, with Open in wizard. */
  const roundRead = (p, t) => h('button', { class: 'btn btn-small btn-quiet ld-read ld-round-read', type: 'button', title: 'Read the round, and its answers so far', onclick: () => {
    hold();
    Rounds.view(p, t);
  } }, 'Read');
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
  /* A report's parts, under its finish: what Claude added, with Read and Undo; each wizard round; what it asks. Own is
     the task the line over them names, said as "this task". */
  function parts(p, rep, it, where, own = rep.task) {
    const out = [];
    if (rep.add && addLive(p, rep.add)) {
      const u = undos.get(rep.id);
      out.push(partEl('added', ['Added ' + addedWords(p, rep.add) + '.'], [readBtn('What Claude added to ' + p.name, () => readAdded(p, rep.add)),
        u ? act(p, it, where, 'Undo', 'ld-undo', 'Take back what Claude added', () => { ClaudeInbox.undo(p, u); undos.delete(rep.id); }, true) : null]));
    }
    for (const r of rep.rounds) {
      const t = p.todos.find(x => x.id === r.tid), uk = rep.id + ':' + r.tid, u = undos.get(uk);
      if (!t || !t.round || t.round.title !== r.title) continue;                        // taken off, or another round since
      const same = tkey(t.text) === tkey(own);
      out.push(partEl('round', same ? ['Attached a wizard round, ', h('bdi', null, t.round.title), '.'] : ['Attached a wizard round to ', taskLink(p, t, where, it), ', ', h('bdi', null, t.round.title), '.'],
        [roundRead(p, t), u ? act(p, it, where, 'Undo', 'ld-undo', 'Take back the wizard round', () => { ClaudeInbox.undo(p, u); undos.delete(uk); }, true) : null]));
    }
    const e = entryOf(rep.entry);
    if (e) out.push(...askParts(p, e, own, it, where));
    return out;
  }
  /* Several reports under one line (0.1.95): each one's summary, then its parts, the oldest first. */
  const repsMore = (p, reps, it, where, own) => reps.flatMap(rep => [wordsEl(rep.summary), ...parts(p, rep, it, where, own)]);
  /* A finish heads its report (A1): Claude's summary under it (C2), then its parts. Tick it comes only from Claude
     asking to tick the task off (B3); a finish with no update keeps Tick it, with the start of the reply as its words. */
  function finishView(p, { task, at, s, reps = [], it = null, tick }, where) {
    task = ownTask(task, s || (it && it.ref.task ? { task: it.ref.task } : null), reps);
    const named = task ? taskNamed(p, task) : null, w = watchedOf(p, s), t3 = t3Act(p, named, it, where) || t3ActW(p, w, it, where);
    const nodes = [...sayNodes(p, 'finished', { task }, named, where, it), ' ', whenEl(at)];
    if (reps.length) return { nodes, more: [...repsMore(p, reps, it, where, task), ...talkEls(p, s, where)].filter(Boolean), acts: t3 ? [t3] : [] };
    const tk = tick !== undefined ? tick : typeof ClaudeWork === 'undefined' ? null : s ? ClaudeWork.taskOf(p, s)
      : it && it.ref.task ? ClaudeWork.taskOf(p, { task: it.ref.task, project: it.ref.project || '' }) : null;
    /* the thread's latest message, whole as the watcher read it, else the start of the reply the hooks kept */
    return { nodes, more: [lastWords(w) || wordsEl(plainReply(s && s.reply)), ...talkEls(p, s, where)].filter(Boolean),
      acts: [tk ? act(p, it, where, 'Tick it', 'b-claude-tick', 'Tick off ' + tk.text + ', the task this session started from', () => ClaudeWork.tick(p, tk)) : null, t3].filter(Boolean) };
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
    const rep = reportOf(it.ref && it.ref.report), uk = rep ? rep.id + ':' + it.ref.tid : it.id, u = undos.get(uk), t = taskFor(p, it);
    return { nodes: [...sayNodes(p, 'round', it.v, t, where, it), ...(rep ? [' ', whenEl(rep.at, 'Sent ')] : [])],
      more: [rep && !rep.add ? wordsEl(rep.summary) : null].filter(Boolean),
      acts: [t && t.round ? roundRead(p, t) : null, u ? act(p, it, where, 'Undo', 'ld-undo', 'Take back the wizard round', () => { ClaudeInbox.undo(p, u); undos.delete(uk); }) : null].filter(Boolean) };
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
      return finishView(p, { task: it.v.task, at: s && s.state === 'done' ? s.at : it.at, s, reps: repsOf(it), it }, where);
    }
    if (it.moment === 'added') return addedView(p, it, where);
    if (it.moment === 'round') return roundView(p, it, where);
    if (it.moment === 'asks') return asksView(p, entryOf(it.ref.entry), it, where);
    const talk = it.ref && it.ref.session ? (() => { const s = sessOf(p, it.ref.session), w = watchedOf(p, s); return [w && it.moment !== 'waiting' ? lastWords(w) : null, ...talkEls(p, s, where)]; })() : [];
    return { nodes: sayNodes(p, it.moment, it.v, taskFor(p, it), where, it), more: talk.filter(Boolean), acts: actsOf(p, it, where) };
  }
  function actsOf(p, it, where) {
    const out = [];
    /* a send held while T3 was closed (0.1.91, L3): Open T3, then Send it */
    if (it.moment === 't3closed' && typeof T3 !== 'undefined' && T3.held(it.ref.held)) {
      out.push(act(p, it, where, 'Open T3', 'ld-t3', 'Opens T3 Code, so the send can go', () => T3.openApp(it.ref.held), true));
      out.push(act(p, it, where, 'Send it', 'ld-open', 'Sends it to T3 again, now T3 is open', () => { readIds([it.id]); T3.retry(it.ref.held); }));
    }
    if (it.moment === 'waiting' || it.moment === 'failed' || (it.conv && it.moment === 'working')) {
      const s = typeof ClaudeWork !== 'undefined' ? ClaudeWork.sessionsOf(p).find(x => x.session === it.ref.session) : null;
      const b = t3Act(p, taskFor(p, it), it, where) || t3ActW(p, watchedOf(p, s), it, where);
      if (b) out.push(b);
    }
    if (it.moment === 'answers') {
      const t = p.todos.find(x => x.id === it.ref.tid);
      if (t && t.round) out.push(roundRead(p, t));
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
      /* a send held while T3 is closed stays news until it goes (0.1.91): the card says it, and it waits in News */
      readIds(mine.filter(it => it.moment !== 't3closed').map(it => it.id));
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
  /* One line the leader says, with what goes under it and its buttons. A line someone else says on the leader's card,
     Quill's (0.1.69), starts with his face and his name, its bar in his color. */
  function lineEl(nodes, { more = [], acts = [], moment = '', cls = '', by = null } = {}) {
    const lead = by ? [h('span', { class: 'ld-by', title: by.name + (by.role ? ', ' + by.role : '') }, faceOf(by, 20), h('b', { dir: 'auto' }, by.name + ':')), ' '] : [];
    const el = h('div', { class: 'ld-line' + (by ? ' by-other' : '') + (cls ? ' ' + cls : ''), 'data-moment': moment },
      h('p', { class: 'ld-says', dir: 'auto' }, ...lead, ...nodes), ...more, acts.length ? h('div', { class: 'ld-acts' }, acts) : null);
    if (by) el.style.setProperty('--ld', by.color);
    return el;
  }
  /* The status card: its news, then what Claude is doing there, in the leader's voice, for as long as the card showed
     it before (B3): working, waiting, finished, stopped, and what asks first while it waits. A finish an update reports
     on is one report, its parts under it (A1, A2); an update a working session sent shows under its working line.
     Nothing is said twice. The leader card in the project view says the same, with the same buttons (0.1.69). */
  function cardLines(p, where = 'card') {
    const lines = [], said = new Set(), own = speakerOf(p).k;
    const voice = typeof ClaudeWork !== 'undefined' ? ClaudeWork.voice(p) : [];
    const pend = typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.pending().filter(e => tkey(e.project) === tkey(p.name)) : [];
    /* under the project view the card is hidden: what it would say waits for the leader card, or the News section */
    const mine = where === 'card' && typeof FullView !== 'undefined' && FullView.shows(p.id) ? sortItems(held.get(p.id) || []) : take(p.id);
    const VOICE_RANK = { waiting: 1, working: 1.2, failed: 1.4, finished: 5 };      // Claude's own order: waiting, working, stopped, finished
    for (const x of voice) {
      const reps = x.moment === 'finished' ? finishReports(x.s) : heldReports(x.s);
      for (const rep of reps) { said.add(rep.id); if (rep.entry) said.add('e:' + rep.entry); }
      if (x.moment === 'finished') {
        const v = finishView(p, { task: x.v.task, at: x.s.at, s: x.s, reps, tick: x.tick }, where);
        lines.push({ rank: reps.length ? Math.min(...reps.map(rep => repRank(p, rep))) : VOICE_RANK.finished, el: lineEl(v.nodes, { more: v.more, acts: v.acts, moment: 'finished', cls: 'b-claude ' + x.s.state }) });
      } else {
        /* a session with no task of its own works on the one its updates name (0.1.95) */
        const task = ownTask(x.v.task, x.s, reps), t = taskNamed(p, task) || (x.s.task || x.s.ask ? taskNamed(p, x.s.task || x.s.ask) : null);
        const w = watchedOf(p, x.s), t3 = t3Act(p, t, null, where) || t3ActW(p, w, null, where);
        /* its thread's latest message, while the watcher sees it (0.1.93, W2c) */
        lines.push({ rank: VOICE_RANK[x.moment] ?? 5, el: lineEl(sayNodes(p, x.moment, { ...x.v, task }, t, where),
          { more: [...(reps.length ? repsMore(p, reps, null, where, task) : [lastWords(w)]), ...talkEls(p, x.s, where)].filter(Boolean), acts: t3 ? [t3] : [], moment: x.moment, cls: 'b-claude ' + x.s.state }) });
      }
    }
    for (const it of mine) {
      if (it.ref && it.ref.report && said.has(it.ref.report)) continue;
      if (it.moment === 'finished' && repsOf(it).some(r => said.has(r.id))) continue;
      if (it.moment === 'asks') continue;                     // said below for as long as it waits in inbox/pending; once applied or dismissed, gone
      if (it.moment === 'waiting') continue;                  // Claude's own line says it while it waits; once the session moves on, gone
      if (NEWS_CLAUDE.has(it.moment) && it.moment !== 'asks' && voice.some(x => x.s.session === it.ref.session)) continue;
      const v = viewOf(p, it, where), sp = speakerFor(it);
      lines.push({ rank: rankOf(it), el: lineEl(v.nodes, { more: v.more, acts: v.acts, moment: it.moment, by: sp.k !== own ? sp : null }) });
    }
    for (const e of pend) {
      if (said.has('e:' + e.name)) continue;
      const v = asksView(p, e, null, where);
      lines.push({ rank: NEWS_RANK.asks, el: lineEl(v.nodes, { more: v.more, acts: v.acts, moment: 'asks', cls: 'b-claude-asks' }) });
    }
    return lines.sort((a, b) => a.rank - b.rank).map(x => x.el);
  }
  /* The leader card in the project view: what the status card says, read as it shows it (0.1.69, Leader Bubbles,
     Round 2, N1); with nothing to say, its greeting shows. */
  const viewLines = p => cardLines(p, 'view');
  /* Topics (0.1.94, Brainstorm 1, Round 2, i5's variant: "you get to talk to the leaders on different topics (I'd like
     arrows to flip the topics instead of having the UI grows very long)", and Round 1, L1): a card says one topic at a
     time, a piece of news or a conversation with Claude, the most pressing first, with arrows to flip them and where
     it is, "2 of 3". The place is kept per building while the page stays open. */
  const flipAt = new Map();
  let flat = false;                                          // the tests that check every line of a card at once lay them out flat
  function flip(key, lines, again) {
    if (lines.length < 2 || flat) { flipAt.delete(key); return lines; }
    const i = Math.min(flipAt.get(key) || 0, lines.length - 1), where = key.split(':')[0];
    flipAt.set(key, i);
    const go = d => { flipAt.set(key, (i + d + lines.length) % lines.length); again(); const b = $('#ldFlip' + (d < 0 ? 'Prev' : 'Next') + '-' + where); if (b) b.focus({ preventScroll: true }); };
    return [lines[i], h('div', { class: 'ld-flip', role: 'group', 'aria-label': 'Topics' },
      h('button', { id: 'ldFlipPrev-' + where, class: 'icon-btn ld-flip-btn', type: 'button', 'aria-label': 'The topic before', title: 'The topic before', html: iconSvg('back', 14), onclick: e => { e.stopPropagation(); go(-1); } }),
      h('span', { class: 'ld-flip-n' }, (i + 1) + ' of ' + lines.length),
      h('button', { id: 'ldFlipNext-' + where, class: 'icon-btn ld-flip-btn next', type: 'button', 'aria-label': 'The next topic', title: 'The next topic', html: iconSvg('back', 14), onclick: e => { e.stopPropagation(); go(1); } }))];
  }
  const cardTopics = p => flip('card:' + p.id, cardLines(p, 'card'), () => Bubble.refresh());
  const viewTopics = p => flip('view:' + p.id, cardLines(p, 'view'), () => Leaders.redrawCard());

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
    /* Quiet (0.1.91): its switch in the section's head; turning it off is a break, so what waited opens */
    $('#newsQuiet').addEventListener('click', () => { Hold.setQuiet(!Hold.quiet()); $('#newsQuiet').focus(); });
    Hold.onQuiet(q => {
      renderSection();
      if (typeof Settings !== 'undefined') Settings.refresh();
      toast(q ? 'Quiet: bubbles wait in News until you turn it off.' : 'Quiet is off: bubbles open again.');
      if (!q) pumpSoon();
    });
    check();
    claude();
    renderSection();
    pump();
    setInterval(check, 60000);                               // a new day, a new week, and pace slipping while the city stays open
  }
  return { init, check, claude, ticked, add, report, renderSection, take, release, cardLines, viewLines, cardTopics, viewTopics, openFace, unanswer, reportFace, yieldTo, hide, pump, redraw, plainReply, typer,
    isShowing: () => !!bub, isHeld: () => !!bub && !bub.auto, items: () => sortItems(live()), lineOf, showing: id => !!bub && bub.list.some(x => x.id === id),
    _test: { flat: v => { flat = !!v; }, sayMs: ms => { sayMs = ms; }, typeMs: ms => { typeMs = ms; }, talk: () => T.state(), state: () => JSON.parse(JSON.stringify(st)), bubble: () => bub && { ids: bub.list.map(x => x.id), i: bub.i, auto: bub.auto },
      forget: () => { st = fresh(); save(); held.clear(); undos.clear(); }, held: pid => (held.get(pid) || []).map(x => x.id), reports: () => JSON.parse(JSON.stringify(st.reports)) } };
})();
