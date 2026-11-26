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
/* One Leader Card (0.1.96, One Leader Card, Rounds 1 and 2): the leader's bubble, the status card and the leader card
   are one card in three places, the same in each; the leader card adds what Claude did whole (S2).
   - Types (T1, M1): every message has one, with its icon and a small change of color: Critical, Need Approval and Your
     Answer red, Decision Wizard green, Heads up yellow, Attachment violet, News grey. News has no buttons.
   - One page per type (M2): a finish with updates is a page for what needs your OK, one for each round, one for what
     Claude added and one for the finish itself, never one mixed message. Pages come in the types' order, "< 1 / 4 >",
     with a red dot on the arrow toward a page not seen yet. The task a page is about has its own line, which stays put
     as you page; the words say "this task" (W1).
   - The x (X1): every page has one. On an ask (what needs your OK, your answer, T3 closed) it takes it off the bubble
     and the status card, and it waits on the leader card until answered; on the rest it takes the page away. Dismiss
     is No (X1a). The bubble has Minimize, which leaves its pages waiting in News, and no longer closes by itself (X2).
   - What opens the bubble by itself (the triggers list he approved): Critical, Need Approval, Your Answer, a round
     attached, and Heads up. What Claude added, a round's answers, and News wait in News. */
const NEWS_TYPES = {
  critical: { name: 'Critical', color: '#FF4D5E', icon: 'tCritical' },
  approval: { name: 'Need Approval', color: '#FF4D5E', icon: 'tApproval' },
  answer: { name: 'Your Answer', color: '#FF4D5E', icon: 'tAnswer' },
  wizard: { name: 'Decision Wizard', color: '#74C997', icon: 'tWizard' },
  headsup: { name: 'Heads up', color: '#FFE03D', icon: 'tHeadsup' },
  attach: { name: 'Attachment', color: '#B58CFF', icon: 'tAttach' },
  news: { name: 'News', color: '#A39BBD', icon: 'tNews' },
};
const NEWS_TYPE_ORDER = Object.keys(NEWS_TYPES);
/* A moment's type: a wait for a question or a form is your answer, any other wait an approval. */
function newsType(moment, v = {}) {
  if (moment === 'failed' || moment === 't3closed') return 'critical';
  if (moment === 'asks') return 'approval';
  if (moment === 'waiting') return v && (v.wait === 'question' || v.wait === 'form' || v.asking) ? 'answer' : 'approval';
  if (moment === 'round' || moment === 'answers') return 'wizard';
  if (/^(behind|due)/.test(moment)) return 'headsup';
  if (moment === 'added') return 'attach';
  return 'news';
}
const NEWS_OPENS = new Set(['behind', 'behind_more', 'behind_day', 'due', 'due_many', 'round', 'waiting', 'asks', 'failed', 't3closed']);
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
  const fresh = () => ({ items: [], raised: {}, lvl: {}, dueDay: '', week: '', reports: [], hidden: {} });
  function load() {
    try {
      const v = JSON.parse(localStorage.getItem(KEY));
      if (v && typeof v === 'object' && Array.isArray(v.items)) { const o = Object.assign(fresh(), v); if (!Array.isArray(o.reports)) o.reports = []; if (!o.hidden || typeof o.hidden !== 'object') o.hidden = {}; return o; }
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
    /* a round's answers are one message, its count brought up to date in place (One Leader Card, Round 1, T1: "only 7
       out of 14 should be updated"), still unread if it was */
    const was = moment === 'answers' && st.items.find(x => x.key === it.key);
    if (was) { was.v = v; was.ref = ref; st.raised[it.key] = now; return was; }
    st.items = st.items.filter(x => x.key !== it.key);      // the same news again replaces the one waiting
    delete st.hidden[it.key];                                // and shows again where its x took it away
    st.items.push(it);
    st.raised[it.key] = now;
    return it;
  }
  const wasRaised = key => st.raised[key] != null;
  function after() {
    renderSection();
    Bubble.refresh();
    Leaders.redrawCard();
    if (bub) { prune(); if (bub) grow(); } else pumpSoon();
  }
  /* A page whose news stopped being true (back on pace, nothing due today any more), or was read on its card, leaves the
     open bubble; with none left, it closes. Since 0.1.96 a bubble no longer closes by itself, so it must. */
  function prune() {
    const cur = bub.list[bub.i], keep = bub.list.filter(it => it.conv || st.items.some(x => x.id === it.id));
    if (keep.length === bub.list.length) return;
    if (!keep.length) { hide(); return; }
    bub.list = keep;
    bub.i = Math.max(0, Math.min(keep.indexOf(cur) >= 0 ? keep.indexOf(cur) : bub.i, keep.length - 1));
    draw();
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
      for (const [k, at] of Object.entries(st.hidden)) if (now - at > KEEP_RAISED) delete st.hidden[k];
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
        st.items = st.items.filter(it => it.moment !== 'asks' || entriesOf(it).some(n => names.has(n)));
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
  /* Under its finish: the finish's news carries its summary, with any other report of the same turn; what it added,
     each round and what it asks are pages of their own (One Leader Card, Round 2, M2: never one mixed message), so
     what asks opens the bubble by itself and the finish waits in News. A session with no task of its own names the
     task the report names. */
  function attach(p, rep, s) {
    rep.fin = s.at; rep.reply = s.reply || '';
    const key = finKey(s), it = st.items.find(x => x.key === key), task = s.task || rep.task || ClaudeWork.what(p, s);
    if (it) {
      const ids = repsOf(it).filter(r => r.reply === rep.reply).map(r => r.id);
      it.ref.reports = [...ids.filter(id => id !== rep.id), rep.id]; it.ref.report = rep.id;
      if (!s.task && rep.task) it.v = { ...it.v, task: ownTask(it.v.task, s, repsOf(it)) };
    } else raise(p, 'finished', { task }, { session: s.session, task: s.task, project: s.project, report: rep.id, reports: [rep.id] }, key);
    parted(p, rep, key, ownTask(task, s, [rep]));
  }
  /* On its own, with no finish to sit under: the same pages. */
  function alone(p, rep) {
    rep.alone = true;
    parted(p, rep, '', rep.task);
  }
  /* A report's pages, each its own item: what it asks, each round, and what Claude added. Under a finish, every update of
     its turn shares one page per type (M2): one Need Approval page and one Attachment page, joined as updates come. */
  function parted(p, rep, fin, task) {
    const join = (moment, key, list, id, v) => {
      const it = st.items.find(x => x.key === key);
      if (it) { if (!it.ref[list].includes(id)) it.ref[list].push(id); it.v = { ...it.v, ...v }; it.popped = false; it.seen = false; return; }
      raise(p, moment, v, { [list]: [id], report: rep.id, fin }, key);
    };
    if (rep.entry) join('asks', fin ? 'asks:' + fin : 'asks:' + rep.entry, 'entries', rep.entry, { change: 'a change', task });
    for (const r of rep.rounds) {
      const t = p.todos.find(x => x.id === r.tid);
      if (t && t.round) raise(p, 'round', { task: t.text, round: t.round.title }, { tid: t.id, report: rep.id, fin }, 'round:' + rep.id + ':' + t.id);
    }
    if (rep.add) join('added', fin ? 'added:' + fin : 'added:' + rep.id, 'reports', rep.id, { what: addedWords(p, rep.add) || 'what it sent', task });
  }
  /* The changes an asks item holds, and the reports an added item holds (one each until 0.1.96). */
  const entriesOf = it => (it.ref.entries || (it.ref.entry ? [it.ref.entry] : []));
  const addRepsOf = it => (it.ref.reports || (it.ref.report ? [it.ref.report] : [])).map(reportOf).filter(Boolean);
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
  /* An item's type, and its place among the pages: the types' order, the leaders before Proxima, then the oldest. */
  const typeOfItem = it => newsType(it.moment, it.v);
  const rankOf = it => NEWS_TYPE_ORDER.indexOf(typeOfItem(it));
  /* What opens a bubble by itself (the triggers he approved, 0.1.96): Critical, what asks, a round attached, Heads up. */
  const opens = it => NEWS_OPENS.has(it.moment);

  /* ---------- the side bar's News section ---------- */
  function faces() {
    const by = new Map();
    for (const it of shown()) {
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
    /* Proxima's own reports and street parties wait here too (0.1.96, the triggers he approved), with her face for the
       buildings with no leader: one Proxima in News, her own first */
    const pxOwn = typeof Proxima !== 'undefined' && Proxima.waiting ? Proxima.waiting() : 0, fs = faces();
    if (pxOwn && !fs.some(f => f.k === 'px')) fs.push({ k: 'px', l: null, name: 'Proxima Pace', role: 'Productivity Inspector', color: '#8FD0F7', items: [] });
    for (const f of fs) {
      const own = f.k === 'px' ? pxOwn : 0, n = f.items.length + own;
      tiles.push(tile({ k: f.k, name: f.name, face: faceOf(f, 48), n, color: f.color,
        title: f.name + (f.role ? ', ' + f.role : '') + ': ' + plural(n, 'piece of news', 'pieces of news') + '. Hear it.',
        open: () => { Menu.closeDrawer(); if (own) Proxima.open(); else openFace(f.k); }, dismiss: f.items.length ? () => dismiss(f.k) : null }));
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
    const ids = shown().filter(it => speakerFor(it).k === k).map(it => it.id);
    if (bub && bub.list.some(it => ids.includes(it.id))) hide();
    readIds(ids);
    const next = $('#newsList .news-face');
    if (next) next.focus(); else { const s = $('#search'); if (s) s.focus({ preventScroll: true }); }
  }

  /* ---------- the bubble ---------- */
  let bub = null, waitT = 0;                                 // { list, i, auto, k, from }
  const box = () => $('#ldSay');
  function blocked() {
    return (typeof Gus !== 'undefined' && Gus.isSaying()) || (typeof Proxima !== 'undefined' && Proxima.isSaying())
      || Panel.isOpen() || Confirm.isOpen() || !sayRoom();
  }
  /* What opens by itself: the news that opens by itself and has not shown yet, unless its x took it away. */
  function pump() {
    clearTimeout(waitT);
    if (!started || bub) return;
    let due = sortItems(shown().filter(it => !it.popped && opens(it)));
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
  /* New news while the bubble shows joins it, as one more page, in its type's place after the page it is on. */
  function grow() {
    const have = new Set(bub.list.map(it => it.id));
    const more = sortItems(shown().filter(it => !it.popped && opens(it) && !have.has(it.id)));
    if (!more.length) return;
    const cur = bub.list[bub.i];
    bub.list = [...bub.list.slice(0, bub.i + 1), ...sortItems([...bub.list.slice(bub.i + 1), ...more])];
    bub.i = Math.max(0, bub.list.indexOf(cur));
    popped(more);
    draw();
  }
  function popped(list) {
    const ids = new Set(list.map(it => it.id));
    edit(() => { for (const it of st.items) if (ids.has(it.id)) it.popped = true; });
  }
  /* A page shown: no longer dotted as not seen. It still waits in News until its x, its buttons or its card. */
  function seen(id) {
    const it = st.items.find(x => x.id === id);
    if (it && !it.seen) edit(() => { const x = st.items.find(y => y.id === id); if (x) x.seen = true; });
  }
  /* A leader's conversations with Claude on its buildings, as pages (0.1.94, L1: "each conversation with an agent is
     one topic"; i5: each leader carries the conversations of every project it leads, its building named on each):
     each session at work, waiting, stopped or finished there that no piece of news already holds, unless its x took it
     away. Not news: nothing is kept or read. */
  function convItems(k, have) {
    if (typeof ClaudeWork === 'undefined') return [];
    const out = [], covered = new Set(have.filter(it => it.ref && it.ref.session).map(it => it.ref.session));
    for (const p of DB.projects) {
      if (speakerOf(p).k !== k) continue;
      for (const x of ClaudeWork.voice(p)) {
        if (covered.has(x.s.session) || isHidden(sessKey(x.s))) continue;
        out.push({ id: 'conv:' + x.s.session, key: 'conv:' + x.s.session, pid: p.id, moment: x.moment, v: x.v, ref: { session: x.s.session, task: x.s.task, project: x.s.project }, at: x.s.at, popped: true, conv: true });
      }
    }
    return out;
  }
  function openFace(k, { session = null } = {}) {
    const news = shown().filter(it => speakerFor(it).k === k);
    const list = sortItems([...news, ...convItems(k, news)]);
    if (!list.length) return;
    if (typeof Gus !== 'undefined' && Gus.isSaying()) Gus.hush();
    show(list, { auto: false, k });
    if (session) { const at = list.findIndex(it => it.ref && it.ref.session === session); if (at > 0) { bub.i = at; draw(); } }
    if (typeof Proxima !== 'undefined') Proxima.yieldToGus();       // her bubble goes, and comes back after this one
    const b = box(), first = b && ($('.ld-acts .btn', b) || $('#ldSayMin'));
    if (first) first.focus({ preventScroll: true });
  }
  function show(list, { auto, k = null }) {
    bub = { list, i: 0, auto, k, from: auto ? null : document.activeElement };
    popped(list);
    const b = box();
    b.hidden = false;
    if (auto && typeof Sound !== 'undefined') Sound.bubble();           // opening by itself: its sound, then the voice (0.1.78)
    draw();
    requestAnimationFrame(() => b.classList.add('show'));
  }
  /* Once you act on the bubble it is yours, as one opened from a face. Since 0.1.96 none closes by itself (X2). */
  const hold = () => { if (bub) bub.auto = false; };
  function draw() {
    const b = box();
    if (!bub || !b) return;
    const it = bub.list[bub.i], p = it && getProject(it.pid);
    if (!p) { dropCur(); return; }
    const pg = pageOfItem(p, it), sp = pg.sp, n = bub.list.length;
    const keep = b.contains(document.activeElement) ? keyOf(document.activeElement) : null;
    seen(it.id);
    b.style.setProperty('--ld', sp.color);
    b.classList.toggle('px-voice', !sp.l);
    b.dataset.k = sp.k; b.dataset.moment = it.moment; b.dataset.type = pg.type || '';
    const unseen = j => { const x = bub.list[j]; return !!x && !x.conv && st.items.some(y => y.id === x.id && !y.seen); };
    const dots = [bub.list.slice(0, bub.i).some((x, j) => unseen(j)), bub.list.some((x, j) => j > bub.i && unseen(j))];
    b.replaceChildren(pageEl(p, pg, 'say', { i: bub.i, n, dots, go: d => { hold(); if (d < 0) prev(); else next(); } }));
    T.speak(it.id, voiceKey(sp));
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
    if (!bub || bub.i >= bub.list.length - 1) return;
    bub.i++;
    draw();
  }
  /* The page it shows is done with (its x, or acted on): it goes, and the next one shows; with none left, the bubble
     closes. */
  function dropCur() {
    if (!bub) return;
    bub.list.splice(bub.i, 1);
    if (!bub.list.length) { hide(); return; }
    bub.i = Math.min(bub.i, bub.list.length - 1);
    draw();
    const nb = $('.ld-acts .btn', box()) || $('#ldSayMin');
    if (nb && !bub.auto) nb.focus({ preventScroll: true });
  }
  /* Minimize, or given way to Gus or Proxima: the bubble goes, and what it held waits in News (X2). */
  function hide() {
    const b = box();
    if (!bub) return false;
    const was = bub, had = !!b && b.contains(document.activeElement);      // read before the card goes with the focus in it
    bub = null;
    hush();
    if (b) { b.classList.remove('show'); b.hidden = true; b.replaceChildren(); }
    if (MapView._lit() === (was.list[was.i] || {}).pid) MapView.light(null);
    renderSection();
    if (had && was.from && document.contains(was.from)) was.from.focus({ preventScroll: true });
    else if (had) { const f = $('#newsList .news-face'); if (f) f.focus({ preventScroll: true }); }
    waitT = setTimeout(pump, 400);
    return true;
  }
  const minimize = () => hide();
  /* Gus or Proxima speaks: the bubble gives way, and what it had not shown comes back after them. */
  function yieldTo() {
    if (!bub) return;
    const left = bub.list.slice(bub.i).map(it => it.id), auto = bub.auto;
    hide();
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
    return leaderParts(moment, v, !!t).map(x => {              // with the task on the card's own line, "this task" (W1)
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
      if (where === 'say') hide();                          // the leader card shows it there, and reads it
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
  function wordsEl(text, whole = false) {
    const t = whole ? String(text || '').trim() : cut(text, 200);
    return t ? h('p', { class: 'b-claude-said' + (whole ? ' whole' : ''), dir: 'auto', title: whole ? null : 'In Claude’s words: ' + String(text).trim() }, iconEl('claude', 12), h('span', null, t)) : null;
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
  /* A button acted: on what asks, its page stays while it has something left to answer, drawn again without what was
     done; else the page is done with: read, and in the bubble the next page shows. */
  function acted(p, pg, where, stay) {
    const left = !!pg && stay && !!pg.left && pg.left();
    const it = pg ? itemOf(pg) : null, was = it || (pg && pg.it && !pg.it.conv ? pg.it : null);   // a card read its item as it showed it
    if (where === 'say') { if (bub) { if (left) draw(); else { if (it) readIds([it.id]); dropCur(); } } return; }
    if (!left) { if (it) readIds([it.id]); if (was) dropHeld(p.id, was.id); }
    Bubble.refresh(); Leaders.redrawCard();
  }
  /* Read: a small panel with the whole of it (A2's note). */
  const readBtn = (title, body) => h('button', { class: 'btn btn-small btn-quiet ld-read', type: 'button', title: 'Read it whole', onclick: () => {
    hold();
    Panel.open(title, h('div', { class: 'cr-body' }, body()), 'cr');
  } }, 'Read');
  const crSec = (head, ...kids) => h('section', { class: 'cr-sec' }, h('h3', { class: 'cr-h', dir: 'auto' }, head), ...kids);
  const crText = (text, cls = '') => h('p', { class: 'cr-text' + (cls ? ' ' + cls : ''), dir: 'auto' }, text);
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

  /* ---------- pages (0.1.96, One Leader Card): one message each, its type, the task it is about, who says it ---------- */
  /* A page is known by keys: its item's, and for Claude's conversation its session's, so its x, its dot and reading
     hold wherever it shows. What asks (what needs your OK, your answer, T3 closed) keeps waiting on the leader card. */
  const ASK_MOMENTS = new Set(['asks', 'waiting', 't3closed']);
  const isHidden = key => !!key && st.hidden[key] != null;
  const hiddenPg = pg => pg.keys.some(isHidden);
  const itemOf = pg => st.items.find(x => pg.keys.includes(x.key)) || null;
  const unseenPg = pg => { const it = itemOf(pg); return !!it && !it.seen; };
  /* What waits in News and the bubble: the news its x did not take away. */
  const shown = () => live().filter(it => !isHidden(it.key));
  const sessKey = s => 'conv:' + s.session + ':' + s.state + ':' + (s.state === 'done' ? s.at : s.since);
  function mkPage(p, o) {
    const pg = Object.assign({ keys: [], it: null, t: null, sp: speakerOf(p), moment: '', type: 'news', left: null, view: null }, o);
    pg.keys = pg.keys.filter(Boolean);
    pg.ask = ASK_MOMENTS.has(pg.moment);
    return pg;
  }
  /* Its x (X1): an ask comes off the bubble and the status card and waits on the leader card; the rest goes. */
  function xOut(p, pg, where) {
    const it = itemOf(pg);
    edit(() => { const now = Date.now(); for (const k of pg.keys) st.hidden[k] = now; });
    if (it && !pg.ask) readIds([it.id]);
    if (it && !pg.ask) dropHeld(p.id, it.id);
    if (where === 'say') { dropCur(); return; }
    renderSection();
    Bubble.refresh(); Leaders.redrawCard();
    const again = $('#ldFlipNext-' + where) || $('#ldX-' + where);
    if (again) again.focus({ preventScroll: true });
  }

  /* Claude's conversation on a building: at work (or took your message), waiting for your OK or your answer, stopped
     on an error, or handed back with its updates' summaries. */
  function convPage(p, { moment, v, s, it = null, reps = [] }) {
    const task = ownTask(v.task, s, reps), t = taskNamed(p, task) || (s && (s.task || s.ask) ? taskNamed(p, s.task || s.ask) : null);
    const w = watchedOf(p, s), asking = !!(w && w.asks && w.asks[0] && w.asks[0].questions && w.asks[0].questions.length);
    const vv = { ...v, task, ...(asking ? { asking: true } : {}) };
    const keys = [s ? sessKey(s) : '', it ? it.key : '', s && moment === 'finished' ? finKey(s) : '', s && moment === 'waiting' ? 'waiting:' + s.session + ':' + s.since : '',
      s && moment === 'failed' ? 'failed:' + s.session + ':' + s.since : ''];
    const pg = mkPage(p, { keys, it, moment, type: newsType(moment, vv), t });
    pg.view = where => convView(p, pg, { moment, v: vv, s, t, w, reps, it }, where);
    return pg;
  }
  function convView(p, pg, { moment, v, s, t, w, reps, it }, where) {
    const whole = where === 'view', at = s ? (moment === 'finished' ? s.at : s.since) : it ? it.at : Date.now();
    const nodes = [...sayNodes(p, moment, { ...v, ago: relAgo(at) }, t, where, it), ...(moment === 'working' ? [] : [' ', whenEl(at)])];
    if (moment === 'finished') {
      const more = [whole ? timesEl(s, reps) : null, ...reps.map(rep => wordsEl(rep.summary, whole))];
      const raw = w && typeof T3 !== 'undefined' && T3.lastOf(w) ? T3.lastOf(w) : s && s.reply, link = t3Link(p, t, w);
      if (raw && plainReply(raw)) more.push(whole ? lastEl(raw, link) : quoteEl(raw), whole ? null : link);
      else more.push(link);
      return { nodes, more: [...more, ...talkEls(p, s, where)].filter(Boolean), acts: [] };
    }
    if (moment === 'working') {
      const more = [whole && s && s.thought ? h('p', { class: 'lc-thought', dir: 'auto', title: 'Claude’s latest thought' }, '“' + s.thought + '”') : null,
        ...reps.map(rep => wordsEl(rep.summary, whole)), lastWords(w), t3Link(p, t, w), ...talkEls(p, s, where)];
      return { nodes, more: more.filter(Boolean), acts: [] };
    }
    /* waiting, or stopped on an error: Open in T3, since only T3's window approves (i6: "take you to t3") */
    const more = moment === 'waiting' && v.asking ? talkEls(p, s, where) : [lastWords(w), ...talkEls(p, s, where)];   // its question says it; else its latest message
    return { nodes, more: more.filter(Boolean), acts: [t3Act(p, t, pg, where) || t3ActW(p, w, pg, where)].filter(Boolean) };
  }
  /* The leader card's extras (S2): when Claude started, how long it worked, and how many updates it sent. */
  function timesEl(s, reps) {
    if (!s || !s.since || !s.at) return null;
    const d = new Date(s.since), hm = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    const m = Math.max(1, Math.round((s.at - s.since) / 60000));
    const dur = m < 60 ? plural(m, 'minute', 'minutes') : plural(Math.floor(m / 60), 'hour', 'hours') + (m % 60 ? ' ' + plural(m % 60, 'minute', 'minutes') : '');
    return h('p', { class: 'lc-times' }, 'Started ' + hm + ' · worked ' + dur + (reps.length ? ' · ' + plural(reps.length, 'update', 'updates') : ''));
  }
  /* Claude's last message: a quote cut short, or on the leader card whole, a paragraph each (S2). */
  const paras = raw => String(raw || '').split(/\n\s*\n/).map(plainReply).filter(Boolean);
  const quoteEl = raw => { const t = plainReply(raw); return h('p', { class: 'lc-quote', dir: 'auto', title: t }, '“' + cut(t, 160) + '”'); };
  const lastEl = (raw, link) => h('div', { class: 'lc-last' }, h('div', { class: 'lc-last-h' }, 'Claude’s last message'),
    ...paras(raw).map(x => h('p', { dir: 'auto' }, x)), link);
  /* Check T3: on a page of News, a link in place of a button (Round 2, M1: News has no buttons). */
  function t3Link(p, t, w) {
    const th = t && typeof T3 !== 'undefined' ? T3.latest(t) : null;
    const go = th && th.env ? () => T3.openThread(th) : w && w.env && typeof T3 !== 'undefined' ? () => T3.openWatched(w) : null;
    if (!go) return null;
    return h('p', { class: 'lc-link' }, h('a', { class: 'ld-t3-link', href: '#', title: th && th.env ? T3.openTitle(p, t, th) : 'Opens its T3 thread' + (w.title ? ', ' + w.title : '') + '.',
      onclick: e => { e.preventDefault(); e.stopPropagation(); hold(); go(); } }, 'Check T3'));
  }

  /* One change Claude asks about: its words for the leader's line ("tick this task off") and for a part line, and its
     buttons: Tick it and No for a tick (B3), Read, Apply and No for a description or a plan (X1a: Dismiss is No). */
  function askOf(p, e, i, own, pg, where) {
    const c = e.changes[i], r = ClaudeInbox.readable(p, c), mine = !!own && tkey(c.task) === tkey(own);
    const name = t => (t ? taskLink(p, t, where, pg) : h('bdi', null, lineTitle(String(c.task || '').trim())));
    const no = title => act(p, pg, where, 'No', 'btn-quiet b-claude-dismiss', title, () => ClaudeInbox.dismiss(e, i), true);
    const ok = (label, cls, title) => act(p, pg, where, label, cls, title, () => ClaudeInbox.apply(e, i), true);
    if (c.do === 'done') {
      const on = r.ok && r.t.repeat ? ', on to its next date' : '';
      const gist = mine ? ['tick this task off' + on] : ['tick ', name(r.ok ? r.t : null), ' off' + on];
      const text = mine ? ['Tick this task off' + on] : ['Tick ', name(r.ok ? r.t : null), ' off' + on];
      if (!r.ok) {
        const was = p.todos.some(t => t.done && tkey(t.text) === tkey(c.task));
        return { gist, text: [...text, was ? '. It is ticked off already.' : '. It is not open here.'], acts: [no('Put it away: nothing changes')] };
      }
      return { gist, text: [...text, '.'], acts: [ok('Tick it', 'b-claude-tick', 'Tick off ' + r.t.text + (on ? ': it moves on to its next date' : '')), no('Leave ' + r.t.text + ' open')] };
    }
    if (c.do === 'edit-description') {
      if (!r.ok) return { gist: ['a new description for ', name(null)], text: ['A new description for ', name(null), '. It is not in this project.'], acts: [no('Put it away: nothing changes')] };
      return { gist: mine ? ['a new description for this task'] : ['a new description for ', name(r.t)], text: mine ? ['A new description for this task.'] : ['A new description for ', name(r.t), '.'],
        acts: [readBtn('A new description for ' + r.t.text, () => readDescription(r.t, c)), ok('Apply', 'b-claude-apply', 'Give ' + r.t.text + ' the new description'), no('Keep the description ' + r.t.text + ' has')] };
    }
    if (c.do === 'replace-plan') {
      if (!r.ok) return { gist: ['a new plan the city cannot read'], text: ['A new plan the city cannot read.'], acts: [no('Put it away: nothing changes')] };
      const size = ClaudeInbox.planSize(r.plan);
      return { gist: ['a new plan with ' + size], text: ['A new plan with ' + size + '.'],
        acts: [readBtn('A new plan for ' + p.name, () => readPlanBody(r.plan)), ok('Apply', 'b-claude-apply', 'Replace the About, milestones and tasks with the new plan'), no('Keep the plan ' + p.name + ' has')] };
    }
    return { gist: ['a change the city does not know'], text: ['A change the city does not know.'], acts: [no('Put it away')] };
  }
  /* Need Approval: what Claude asks first, every change of a finish on one page (M2): one change with its buttons on the
     page, several a short line each. */
  function asksPage(p, names, reps, own, key, it = null) {
    const opens = () => names.map(entryOf).filter(Boolean).flatMap(e => ClaudeInbox.openIdx(e).map(i => ({ e, i })));
    const o0 = opens(), one = o0.length === 1 ? o0[0].e.changes[o0[0].i] : null;
    const t = own ? taskNamed(p, own) : one && one.task ? taskNamed(p, one.task) : null;
    const pg = mkPage(p, { keys: [key, ...names.map(n => 'asks:' + n), it ? it.key : ''], it, moment: 'asks', type: 'approval', t });
    pg.left = () => opens().length > 0;
    pg.view = where => {
      const list = opens(), whole = where === 'view', mine = t ? t.text : '';
      if (!list.length) return { nodes: sayNodes(p, 'asks', { change: 'a change' }, null, where, it), more: [], acts: [] };
      const alone = reps.length ? reps.filter(r => r.alone) : [null];
      const sums = alone.map(r => wordsEl(r ? r.summary : list[0].e.summary, whole));
      const first = list[0].e, when = whenEl(first.at || (reps[0] ? reps[0].at : Date.now()), 'Sent ');
      if (list.length === 1) { const a = askOf(p, first, list[0].i, mine, pg, where); return { nodes: ['Claude wants your OK first: ', ...a.gist, '. ', when], more: sums.filter(Boolean), acts: a.acts }; }
      return { nodes: ['Claude wants your OK on ' + plural(list.length, 'change', 'changes') + '. ', when],
        more: [...sums, ...list.map(({ e, i }) => { const a = askOf(p, e, i, mine, pg, where); return partEl('ask ' + e.changes[i].do, a.text, a.acts); })].filter(Boolean), acts: [] };
    };
    return pg;
  }
  /* Attachment: what Claude added, each whole (One Leader Card, Round 1, C1: "the full clickable note, then [Delete]"):
     a note as it shows under a task's description, a task and a link by name, each with Delete; every update of a
     finish on one page (M2). */
  function addedPage(p, reps, own, key, it = null) {
    const t = own ? taskNamed(p, own) : null;
    const merged = () => { const live = reps.filter(r => r.add && addLive(p, r.add));
      if (!live.length) return null;
      const uniq = list => list.filter((id, i) => list.indexOf(id) === i), notes = uniq(live.flatMap(r => r.add.notes));
      /* a note added and brought up to date in the same turn is one note added */
      return { todos: uniq(live.flatMap(r => r.add.todos)), ms: [], notes, links: uniq(live.flatMap(r => r.add.links)), updated: uniq(live.flatMap(r => r.add.updated || [])).filter(id => !notes.includes(id)) }; };
    const pg = mkPage(p, { keys: [key, ...reps.map(r => 'added:' + r.id), it ? it.key : ''], it, moment: 'added', type: 'attach', t });
    pg.left = () => !!merged();
    pg.view = where => {
      const add = merged(), at = reps.length ? reps[reps.length - 1].at : it ? it.at : Date.now();
      const nodes = [...sayNodes(p, 'added', { what: add ? addedWords(p, add) : it ? it.v.what : 'what it sent' }, null, where, it), ' ', whenEl(at, reps.length ? 'Sent ' : '')];
      const sums = reps.filter(r => r.alone && !r.entry && !r.rounds.length).map(r => wordsEl(r.summary, where === 'view'));
      return { nodes, more: [...sums, add ? addedTiles(p, add, pg, where) : null].filter(Boolean), acts: [] };
    };
    return pg;
  }
  const noteTile = (p, n) => h('button', { class: 'pv-tnote lc-note' + (byClaude(n) ? ' by-claude' : ''), type: 'button', 'data-id': n.id, title: 'Open ' + noteHead(n),
    onclick: e => { e.stopPropagation(); hold(); if (bub) hide(); FullView.openNote(p.id, n.id); } },
    h('span', { class: 'pv-tnote-h', dir: 'auto' }, h('span', { class: 'note-ic', 'aria-hidden': 'true', html: iconSvg(noteIcon(n), 16) }), h('span', { class: 'pv-tnote-t' }, noteHead(n))),
    noteBody(n) ? h('span', { class: 'pv-tnote-b', dir: 'auto' }, noteBody(n).slice(0, 400)) : null,
    h('span', { class: 'pv-note-at' }, ...[byClaude(n) ? iconEl('claude', 12) : null, fmtStamp(n.updatedAt || n.at) + (byClaude(n) ? ' · By Claude' : '')].filter(Boolean)));
  function addedTiles(p, add, pg, where) {
    const a = addedOf(p, add);
    const del = (kind, id, name) => act(p, pg, where, 'Delete', 'btn-quiet ld-del', 'Delete ' + name, () => deleteAdded(p, kind, id), true);
    const rows = [
      ...a.ts.map(t => h('div', { class: 'lc-att' }, h('span', { class: 'lc-att-name' }, iconEl('task', 12), taskLink(p, t, where, pg)), del('task', t.id, t.text))),
      ...[...a.ns, ...a.us].map(n => h('div', { class: 'lc-att lc-att-note' }, noteTile(p, n), del('note', n.id, noteHead(n)))),
      ...a.ls.map(l => { const lt = linkTarget(l); return h('div', { class: 'lc-att' }, h('span', { class: 'lc-att-name' },
        lt.href ? h('a', { class: 'lc-att-link', href: lt.href, target: lt.blank ? '_blank' : null, rel: 'noopener', dir: 'auto', title: lt.title }, lt.name) : h('b', { dir: 'auto' }, lt.name)), del('link', l.id, lt.name)); }),
    ];
    return h('div', { class: 'lc-atts' }, ...rows);
  }
  /* Delete, on what Claude added: it goes from the city, with Undo in a toast. */
  function deleteAdded(p, kind, id) {
    let back = null, name = '';
    if (kind === 'task') { const i = p.todos.findIndex(t => t.id === id); if (i < 0) return; const t = p.todos[i]; name = t.text; p.todos.splice(i, 1); back = () => p.todos.splice(Math.min(i, p.todos.length), 0, t); }
    else if (kind === 'link') { const i = p.links.findIndex(l => l.id === id); if (i < 0) return; const l = p.links[i]; name = linkTarget(l).name; p.links.splice(i, 1); back = () => p.links.splice(Math.min(i, p.links.length), 0, l); }
    else {
      const t = noteTask(p, id), list = t ? t.notes : p.notes, i = list ? list.findIndex(n => n.id === id) : -1;
      if (i < 0) return;
      const n = list[i]; name = noteHead(n); list.splice(i, 1);
      if (t && !t.notes.length) delete t.notes;
      back = () => { const l = t ? (t.notes = t.notes || []) : p.notes; l.splice(Math.min(i, l.length), 0, n); };
    }
    const redo = () => { window.changed(p); if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render(); redrawTalk(); };
    redo();
    toast('Deleted ' + name + '.', '', { label: 'Undo', run: () => { back(); redo(); } });
  }
  /* Decision Wizard: a round Claude attached, said by Quill (C1), with Read and Undo. */
  function roundPage(p, rep, t, it = null) {
    const uk = rep ? rep.id + ':' + t.id : it ? it.id : '';
    const pg = mkPage(p, { keys: [rep ? 'round:' + rep.id + ':' + t.id : '', it ? it.key : ''], it, moment: 'round', type: 'wizard', t, sp: voiceOf(quillLeader()) });
    pg.left = () => undos.has(uk);
    pg.view = where => ({
      nodes: [...sayNodes(p, 'round', { task: t.text, round: t.round ? t.round.title : it ? it.v.round : '' }, t, where, it), ...(rep ? [' ', whenEl(rep.at, 'Sent ')] : [])],
      more: [rep && rep.alone && !rep.entry ? wordsEl(rep.summary, where === 'view') : null].filter(Boolean),
      acts: [t.round ? roundRead(p, t) : null, undos.has(uk) ? act(p, pg, where, 'Undo', 'ld-undo', 'Take back the wizard round', () => { ClaudeInbox.undo(p, undos.get(uk)); undos.delete(uk); }) : null].filter(Boolean) });
    return pg;
  }
  /* The pages of a turn's updates (or one update on its own), one per type (M2): what asks, each round, what it added.
     key names the turn: its finish, or its session while it works, or the update. */
  function repPages(p, reps, own, key) {
    const out = [], names = reps.map(r => r.entry).filter(n => { const e = entryOf(n); return !!e && ClaudeInbox.openIdx(e).length > 0; });
    if (names.length) out.push(asksPage(p, names, reps.filter(r => names.includes(r.entry)), own, 'asks:' + key));
    for (const rep of reps) for (const r of rep.rounds) {
      const t = p.todos.find(x => x.id === r.tid);
      if (t && t.round && t.round.title === r.title) out.push(roundPage(p, rep, t));   // taken off, or another round since
    }
    const adds = reps.filter(r => r.add && addLive(p, r.add));
    if (adds.length) out.push(addedPage(p, adds, own, 'added:' + key));
    return out;
  }
  /* Any other piece of news: its line, and its buttons. */
  function itemPage(p, it) {
    const t = taskFor(p, it);
    const pg = mkPage(p, { keys: [it.key], it, moment: it.moment, type: newsType(it.moment, it.v), t, sp: speakerFor(it) });
    pg.view = where => ({ nodes: sayNodes(p, it.moment, it.v, t, where, it), more: [], acts: actsOf(p, it, pg, where) });
    return pg;
  }
  /* A piece of news, or a conversation, as its page. */
  function pageOfItem(p, it) {
    if (it.ref && it.ref.session && ['working', 'waiting', 'failed', 'finished'].includes(it.moment)) {
      const s = sessOf(p, it.ref.session);
      return convPage(p, { moment: it.moment, v: it.v, s, it, reps: it.moment === 'finished' ? repsOf(it) : [] });
    }
    if (it.moment === 'asks' && entriesOf(it).length) return asksPage(p, entriesOf(it), entriesOf(it).map(n => [...st.reports].reverse().find(r => r.entry === n)).filter(Boolean), it.v.task || '', it.key, it);
    if (it.moment === 'added') return addedPage(p, addRepsOf(it), it.v.task || '', it.key, it);
    if (it.moment === 'round') { const t = taskFor(p, it); if (t) return roundPage(p, reportOf(it.ref.report), t, it); }
    return itemPage(p, it);
  }
  function actsOf(p, it, pg, where) {
    const out = [];
    /* a send held while T3 was closed (0.1.91, L3): Open T3, then Send it */
    if (it.moment === 't3closed' && typeof T3 !== 'undefined' && T3.held(it.ref.held)) {
      out.push(act(p, pg, where, 'Open T3', 'ld-t3', 'Opens T3 Code, so the send can go', () => T3.openApp(it.ref.held), true));
      out.push(act(p, pg, where, 'Send it', 'ld-open', 'Sends it to T3 again, now T3 is open', () => { readIds([it.id]); T3.retry(it.ref.held); }));
    }
    if (it.moment === 'answers') {
      const t = p.todos.find(x => x.id === it.ref.tid);
      if (t && t.round) out.push(roundRead(p, t));
      if (t) out.push(act(p, pg, where, 'Open', 'ld-open', 'Open ' + t.text + ' and its round', () => { if (where === 'say') { readIds([it.id]); hide(); } FullView.openTask(p.id, t.id); }));
    }
    return out;
  }

  /* ---------- the status card and the project view: a building's pages, read as they show them ---------- */
  /* Its waiting news, held while its status card or project view shows it; each is read as its page shows. */
  function take(pid) {
    const mine = live().filter(it => it.pid === pid);
    const have = held.get(pid) || [];
    held.set(pid, [...have, ...mine.filter(it => !have.some(x => x.id === it.id))]);
    return sortItems(held.get(pid) || []);
  }
  const dropHeld = (pid, id) => { const l = held.get(pid); if (l) held.set(pid, l.filter(x => x.id !== id)); };
  /* Let go of what a building held once neither its status card nor its project view shows it. */
  function release(pid) {
    if (!pid) return;
    if (Bubble.openId() === pid || (typeof FullView !== 'undefined' && FullView.shows(pid))) return;
    held.delete(pid);
  }
  /* A building's pages, the same on the status card and the leader card (S1): Claude at work and its updates, the
     building's news, and what Claude asks first while it waits, each page once, in the types' order. The status card
     leaves out what its x took away; the leader card keeps what asks until it is answered (X1). */
  function cardPages(p, where = 'card') {
    const pages = [], said = new Set();
    const voice = typeof ClaudeWork !== 'undefined' ? ClaudeWork.voice(p) : [];
    const pend = typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.pending().filter(e => tkey(e.project) === tkey(p.name)) : [];
    /* under the project view the status card is hidden: what it would say waits for the leader card, or News */
    const mine = where === 'card' && typeof FullView !== 'undefined' && FullView.shows(p.id) ? sortItems(held.get(p.id) || []) : take(p.id);
    const sayReps = (reps, own, key) => { for (const rep of reps) { said.add(rep.id); if (rep.entry) said.add('e:' + rep.entry); } pages.push(...repPages(p, reps, own, key)); };
    for (const x of voice) {
      const reps = x.moment === 'finished' ? finishReports(x.s) : heldReports(x.s);
      if (reps.length) sayReps(reps, ownTask(x.v.task, x.s, reps), x.moment === 'finished' ? finKey(x.s) : 'held:' + x.s.session);
      pages.push(convPage(p, { moment: x.moment, v: x.v, s: x.s, reps }));
    }
    /* a finish whose session the city no longer sees: its updates' pages from it */
    const gone = mine.filter(it => it.moment === 'finished' && !voice.some(x => x.s.session === it.ref.session));
    for (const it of gone) { const reps = repsOf(it); if (reps.length && !reps.some(r => said.has(r.id))) sayReps(reps, it.v.task, it.key); }
    for (const it of mine) {
      if (it.ref && it.moment !== 'finished' && [it.ref.report, ...(it.ref.reports || [])].some(r => r && said.has(r))) continue;
      if (it.moment === 'asks') continue;                     // said below for as long as it waits in inbox/pending; once applied or dismissed, gone
      if (it.moment === 'waiting') continue;                  // Claude's own page says it while it waits; once the session moves on, gone
      if (NEWS_CLAUDE.has(it.moment) && voice.some(x => x.s.session === it.ref.session)) continue;
      pages.push(pageOfItem(p, it));
    }
    for (const e of pend) {
      if (said.has('e:' + e.name) || !ClaudeInbox.openIdx(e).length) continue;
      const rep = [...st.reports].reverse().find(r => r.entry === e.name) || null;
      pages.push(asksPage(p, [e.name], rep ? [rep] : [], rep ? rep.task : '', 'asks:' + e.name));
    }
    const keep = pages.filter(pg => (where === 'view' && pg.ask) || !hiddenPg(pg));
    return keep.map((pg, i) => ({ pg, i })).sort((a, b) => NEWS_TYPE_ORDER.indexOf(a.pg.type) - NEWS_TYPE_ORDER.indexOf(b.pg.type) || a.i - b.i).map(x => x.pg);
  }
  /* The card in a place (S1): its pages one at a time with "< 1 / 3 >" (the 0.1.94 topics' arrows, going round at the
     ends), its page kept per building while the page stays open; with nothing to say, the leader's greeting. A page
     shown on a card is read. */
  const flipAt = new Map();
  let flat = false;                                          // the tests that check every page of a card at once lay them out flat
  function card(p, where) {
    const pages = cardPages(p, where), key = where + ':' + p.id;
    if (!pages.length) { flipAt.delete(key); return greetEl(p, where); }
    const again = () => (where === 'view' ? Leaders.redrawCard() : Bubble.refresh());
    const readPg = pg => { const it = itemOf(pg); if (it && it.moment !== 't3closed' && !(where === 'card' && FullView.shows(p.id))) readIds([it.id]); };
    if (flat) { pages.forEach(readPg); return h('div', { class: 'lc-flat' }, ...pages.map(pg => pageEl(p, pg, where))); }
    const at = flipAt.get(key) || { k: '', i: 0 };
    let i = pages.findIndex(pg => pg.keys[0] === at.k);
    if (i < 0) i = Math.min(at.i, pages.length - 1);
    const dots = [pages.slice(0, i).some(unseenPg), pages.slice(i + 1).some(unseenPg)];
    flipAt.set(key, { k: pages[i].keys[0], i });
    const go = d => {
      const j = (i + d + pages.length) % pages.length;
      flipAt.set(key, { k: pages[j].keys[0], i: j });
      again();
      const b = $('#ldFlip' + (d < 0 ? 'Prev' : 'Next') + '-' + where); if (b) b.focus({ preventScroll: true });
    };
    const el = pageEl(p, pages[i], where, { i, n: pages.length, dots, go });
    readPg(pages[i]);
    return el;
  }
  /* The greeting (S1: on the status card too): where the building stands, and its next task in the task's line. */
  function greetEl(p, where) {
    const l = leaderOf(p);
    if (!l) return null;
    const t = nextTask(p);
    const pg = mkPage(p, { keys: [], moment: 'greet', type: null, t });
    pg.view = () => ({ nodes: [leaderGreeting(p, Date.now(), true)], more: [], acts: [] });
    return pageEl(p, pg, where);
  }

  /* ---------- the card: one page, the same in the bubble, the status card and the leader card ---------- */
  /* The head: the type's icon and name in its color, the pages, and the x (Minimize too in the bubble). Then the face
     (100 px in the bubble and on the leader card, 48 on the status card, C2), the name and role, and the task's line,
     which stays put as you page (in the bubble the building before it); then the leader's words, what goes under them,
     and the buttons. */
  function pageEl(p, pg, where, { i = 0, n = 1, dots = [false, false], go = null } = {}) {
    const ty = pg.type ? NEWS_TYPES[pg.type] : null, sp = pg.sp, say = where === 'say', v = pg.view(where);
    const size = say ? sayFace() : where === 'view' ? 100 : 48;
    const pgBtn = (d, dot) => h('button', { id: say ? (d < 0 ? 'ldSayPrev' : 'ldSayNext') : 'ldFlip' + (d < 0 ? 'Prev' : 'Next') + '-' + where, class: 'icon-btn ld-flip-btn lc-pg' + (d > 0 ? ' next' : ''), type: 'button',
      disabled: say && (d < 0 ? i === 0 : i >= n - 1), 'aria-label': (d < 0 ? 'The page before' : 'The next page') + (dot ? ', one not seen yet' : ''), title: (d < 0 ? 'The page before' : 'The next page') + (dot ? ': one not seen yet' : ''),
      onclick: e => { e.stopPropagation(); go(d); } }, h('span', { class: 'lc-pg-ic', 'aria-hidden': 'true', html: iconSvg(d < 0 ? 'pgPrev' : 'pgNext', 5) }), dot ? h('i', { class: 'lc-dot', 'aria-hidden': 'true' }) : null);
    const pager = n > 1 && go ? h('span', { class: 'ld-flip lc-pager', role: 'group', 'aria-label': 'Pages' }, pgBtn(-1, dots[0]), h('span', { id: say ? 'ldSayCount' : null, class: 'ld-flip-n lc-pgn' }, (i + 1) + ' / ' + n), pgBtn(1, dots[1])) : null;
    const noX = !ty || (where === 'view' && pg.ask);
    const x = noX ? null : h('button', { id: say ? 'ldSayClose' : 'ldX-' + where, class: 'icon-btn lc-x', type: 'button',
      'aria-label': pg.ask ? 'Take it off here' : 'Take it away', title: pg.ask ? 'Take it off here: it waits on the leader card until you answer it' : 'Take it away',
      html: iconSvg('close', 12), onclick: e => { e.stopPropagation(); xOut(p, pg, where); } });
    const mini = say ? h('button', { id: 'ldSayMin', class: 'icon-btn lc-min', type: 'button', 'aria-label': 'Minimize', title: 'Minimize: it waits in News', html: iconSvg('minus', 12), onclick: e => { e.stopPropagation(); minimize(); } }) : null;
    const head = ty || say ? h('div', { class: 'lc-head' }, ty ? h('span', { class: 'lc-type' }, h('span', { class: 'lc-ticon', 'aria-hidden': 'true', html: iconSvg(ty.icon, 14) }), h('b', { class: 'lc-tname' }, ty.name)) : null,
      h('span', { class: 'lc-head-end' }, pager, mini, x)) : null;
    const bits = [];
    if (say) bits.push(h('button', { class: 'ld-say-bld', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } }, h('bdi', null, p.name)));
    if (pg.t) { if (bits.length) bits.push(h('span', { class: 'lc-sep', 'aria-hidden': 'true' }, '·')); bits.push(taskA(p, pg.t, pg.t.text, 'Open ' + pg.t.text, where, pg)); }
    const who = h('div', { class: 'lc-who' }, h('span', { id: say ? 'ldSayFace' : null, class: 'lc-face ld-say-face' }, faceOf(sp, size)),
      h('div', { class: 'lc-wn' }, h('div', { class: 'lc-nmrow' }, h('b', { id: say ? 'ldSayName' : null, class: 'lc-nm ld-name', dir: 'auto' }, sp.name), ' ',
        sp.role ? h('span', { id: say ? 'ldSayRole' : null, class: 'lc-role', dir: 'auto' }, sp.role) : null),
        bits.length ? h('div', { id: say ? 'ldSayWhere' : null, class: 'lc-tline' }, ...bits) : null));
    const acts = [...v.acts, say ? h('button', { class: 'btn btn-small btn-quiet ld-go', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } }, 'Go to it') : null].filter(Boolean);
    const msg = h('div', { class: 'ld-line lc-msg', 'data-moment': pg.moment, 'data-type': pg.type || '' },
      h('p', { id: say ? 'ldSayText' : null, class: 'ld-says', dir: 'auto' }, ...v.nodes),
      v.more.length ? h('div', { id: say ? 'ldSayMore' : null, class: 'ld-say-more lc-more' }, ...v.more) : null,
      acts.length ? h('div', { id: say ? 'ldSayActs' : null, class: 'ld-acts' }, ...acts) : null);
    const el = h('div', { class: 'lc ' + (ty ? 'typed' : 'plain') + (sp.l ? '' : ' px-voice'), 'data-type': pg.type || '', 'data-key': pg.keys[0] || '', 'data-where': where }, head, h('div', { class: 'lc-body' }, who, msg));
    el.style.setProperty('--t', ty ? ty.color : '#6B6388');
    el.style.setProperty('--ld', sp.color);
    return el;
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
    b.addEventListener('keydown', e => { if (e.key === 'Escape' && bub) { e.stopPropagation(); e.preventDefault(); minimize(); } });   // Esc minimizes (X2)
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
  return { init, check, claude, ticked, add, report, renderSection, take, release, card, cardPages, openFace, unanswer, reportFace, yieldTo, hide, pump, redraw, plainReply, typer,
    isShowing: () => !!bub, isHeld: () => !!bub && !bub.auto, items: () => sortItems(shown()), lineOf, showing: id => !!bub && bub.list.some(x => x.id === id), typeOf: typeOfItem,
    _test: { flat: v => { flat = !!v; }, sayMs: ms => { sayMs = ms; }, typeMs: ms => { typeMs = ms; }, talk: () => T.state(), state: () => JSON.parse(JSON.stringify(st)), bubble: () => bub && { ids: bub.list.map(x => x.id), i: bub.i, auto: bub.auto },
      forget: () => { st = fresh(); save(); held.clear(); undos.clear(); flipAt.clear(); }, held: pid => (held.get(pid) || []).map(x => x.id), reports: () => JSON.parse(JSON.stringify(st.reports)),
      pages: (pid, where = 'card') => { const p = getProject(pid); return p ? cardPages(p, where).map(pg => ({ type: pg.type, moment: pg.moment, keys: pg.keys, task: pg.t ? pg.t.text : '', ask: pg.ask, by: pg.sp.name })) : []; } } };
})();
