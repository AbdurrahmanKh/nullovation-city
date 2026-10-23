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
  const fresh = () => ({ items: [], raised: {}, lvl: {}, dueDay: '', week: '' });
  function load() {
    try { const v = JSON.parse(localStorage.getItem(KEY)); if (v && typeof v === 'object' && Array.isArray(v.items)) return Object.assign(fresh(), v); } catch (e) { /* a fresh start */ }
    return fresh();
  }
  let st = load(), started = false, sayMs = SAY_MS;
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
  const sortItems = list => [...list].sort((a, b) => (NEWS_RANK[a.moment] ?? 9) - (NEWS_RANK[b.moment] ?? 9) || proximaSays(a) - proximaSays(b) || a.at - b.at);
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
    let moved = false;
    edit(() => {
      const n0 = st.items.length;
      for (const p of DB.projects) {
        const ss = ClaudeWork.sessionsOf(p);
        for (const s of ss) {
          const task = s.task || s.ask || 'a task';
          if (s.state === 'waiting') {
            const key = 'waiting:' + s.session + ':' + s.since;
            if (!wasRaised(key)) { raise(p, 'waiting', { task }, { session: s.session }, key); moved = true; }
          } else if (s.state === 'failed' && !ClaudeWork.isSeen(s)) {
            const key = 'failed:' + s.session + ':' + s.since;
            if (!wasRaised(key)) { raise(p, 'failed', { task }, { session: s.session }, key); moved = true; }
          } else if (s.state === 'done' && !ClaudeWork.isSeen(s)) {
            const key = 'finished:' + s.session + ':' + task.trim().toLowerCase().slice(0, 160);
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
      /* what asks first: one item for each change file waiting in inbox/pending, gone once applied or dismissed */
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

  /* ---------- the side bar's News section ---------- */
  function faces() {
    const by = new Map();
    for (const it of live()) {
      const sp = speakerOf(getProject(it.pid));
      if (!by.has(sp.k)) by.set(sp.k, { ...sp, items: [] });
      by.get(sp.k).items.push(it);
    }
    const list = [...by.values()].map(f => ({ ...f, items: sortItems(f.items) }));
    list.sort((a, b) => (a.k === 'px') - (b.k === 'px') || (NEWS_RANK[a.items[0].moment] ?? 9) - (NEWS_RANK[b.items[0].moment] ?? 9) || a.name.localeCompare(b.name));
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
    const due = sortItems(live().filter(it => !it.popped && NEWS_OPENS.has(it.moment)));
    if (!due.length) return;
    if (blocked()) { waitT = setTimeout(pump, 500); return; }
    show(due, { auto: true });
  }
  /* New news while the bubble shows joins it, as one more of N. */
  function grow() {
    const have = new Set(bub.list.map(it => it.id));
    const more = sortItems(live().filter(it => !it.popped && NEWS_OPENS.has(it.moment) && !have.has(it.id)));
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
    $('#ldSayText').replaceChildren(...sayNodes(p, it.moment, it.v, taskFor(p, it), 'say', it));
    speak(it.id);
    $('#ldSayMore').replaceChildren(...extraOf(p, it, 'say'));
    const acts = actsOf(p, it, 'say');
    $('#ldSayActs').replaceChildren(...[...acts,
      h('button', { class: 'btn btn-small btn-quiet ld-go', type: 'button', title: 'Show ' + p.name + ' on the map', onclick: () => { hold(); goTo(p.id); } }, 'Go to it'),
      n > 1 ? h('span', { id: 'ldSayCount', class: 'ld-say-count' }, (bub.i + 1) + ' of ' + n) : null,
      n > 1 && bub.i < n - 1 ? h('button', { id: 'ldSayNext', class: 'btn btn-small ld-next', type: 'button', onclick: () => { hold(); next(); } }, 'Next') : null].filter(Boolean));
    MapView.light(p.id);
    const view = typeof FullView !== 'undefined' && FullView.isOpen();      // beside the project view, as Proxima's
    b.style.left = view ? Math.round(FullView.rightEdge() + 22) + 'px' : '';
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
    MapView.glideBeside(pid, typeof FullView !== 'undefined' && FullView.isOpen() ? FullView.rightEdge() : 0);
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

  /* ---------- what an item adds under its line, and its buttons ---------- */
  function extraOf(p, it, where) {
    if (it.moment === 'asks') {
      const e = ClaudeInbox.pending().find(x => x.name === it.ref.entry);
      return e ? [ClaudeInbox.list(p, e)] : [];
    }
    return [];
  }
  /* Each button acts, then the item is read and the bubble goes on to the next one. */
  function actsOf(p, it, where) {
    const done = () => {
      if (where === 'say') next();
      else { dropHeld(p.id, it.id); Bubble.refresh(); Leaders.redrawCard(); }
    };
    const btn = (label, cls, title, run) => h('button', { class: 'btn btn-small ' + cls, type: 'button', title, onclick: () => { hold(); run(); done(); } }, label);
    const out = [];
    if ((it.moment === 'added' || it.moment === 'round') && undos.has(it.id))
      out.push(btn('Undo', 'ld-undo', 'Take back what Claude ' + (it.moment === 'round' ? 'attached' : 'added'), () => { ClaudeInbox.undo(p, undos.get(it.id)); undos.delete(it.id); }));
    if (it.moment === 'asks') {
      const e = ClaudeInbox.pending().find(x => x.name === it.ref.entry);
      if (e) out.push(btn('Apply', 'b-claude-apply', 'Apply what Claude asks', () => ClaudeInbox.apply(e)),
        btn('Dismiss', 'btn-quiet b-claude-dismiss', 'Dismiss what Claude asks: nothing changes', () => ClaudeInbox.dismiss(e)));
    }
    if (it.moment === 'finished') {
      const t = it.ref.task && ClaudeWork.taskOf(p, { task: it.ref.task, project: it.ref.project || '' });
      if (t) out.push(btn('Tick it', 'b-claude-tick', 'Tick off ' + t.text + ', the task this session started from', () => ClaudeWork.tick(p, t)));
    }
    if (it.moment === 'answers') {
      const t = p.todos.find(x => x.id === it.ref.tid);
      if (t) out.push(btn('Open', 'ld-open', 'Open ' + t.text + ' and its round', () => { if (where === 'say') { readIds([it.id]); hide({ read: false }); } FullView.openTask(p.id, t.id); }));
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
  function lineEl(nodes, { more = [], acts = [], moment = '' } = {}) {
    return h('div', { class: 'ld-line', 'data-moment': moment },
      h('p', { class: 'ld-says', dir: 'auto' }, ...nodes), ...more, acts.length ? h('div', { class: 'ld-acts' }, acts) : null);
  }
  /* The status card: its news, then what Claude is doing there, in the leader's voice, for as long as the card showed
     it before (B3): working, waiting, finished with Tick it and the start of its reply, stopped, asking first with
     Apply and Dismiss. Claude's news the live lines already say is not said twice. */
  function cardLines(p) {
    const lines = [];
    const voice = typeof ClaudeWork !== 'undefined' ? ClaudeWork.voice(p) : [];
    const pend = typeof ClaudeInbox !== 'undefined' ? ClaudeInbox.pending().filter(e => e.project.trim().toLowerCase() === p.name.trim().toLowerCase()) : [];
    /* under the project view the card is hidden: what it would say waits for the leader card, or the News section */
    const mine = typeof FullView !== 'undefined' && FullView.shows(p.id) ? sortItems(held.get(p.id) || []) : take(p.id);
    for (const it of mine) {
      if (it.moment === 'asks' && pend.some(e => e.name === it.ref.entry)) continue;
      if (NEWS_CLAUDE.has(it.moment) && it.moment !== 'asks' && voice.some(x => x.s.session === it.ref.session)) continue;
      lines.push({ rank: NEWS_RANK[it.moment], el: lineEl(sayNodes(p, it.moment, it.v, taskFor(p, it), 'card'), { more: extraOf(p, it, 'card'), acts: actsOf(p, it, 'card'), moment: it.moment }) });
    }
    for (const e of pend) {
      lines.push({ rank: NEWS_RANK.asks, el: h('div', { class: 'ld-line b-claude-asks', 'data-moment': 'asks' },
        h('p', { class: 'ld-says', dir: 'auto' }, leaderSay('asks', { change: ClaudeInbox.gist(p, e) }), ' ', h('span', { class: 'b-claude-when' }, 'Sent ' + relAgo(e.at) + '.')),
        ClaudeInbox.list(p, e),
        h('div', { class: 'ld-acts' },
          h('button', { class: 'btn btn-small b-claude-apply', type: 'button', onclick: () => ClaudeInbox.apply(e) }, 'Apply'),
          h('button', { class: 'btn btn-small btn-quiet b-claude-dismiss', type: 'button', onclick: () => ClaudeInbox.dismiss(e) }, 'Dismiss'))) });
    }
    const VOICE_RANK = { waiting: 1, working: 1.2, failed: 1.4, finished: 5 };      // Claude's own order: waiting, working, stopped, finished
    for (const x of voice) {
      lines.push({ rank: VOICE_RANK[x.moment] ?? 5, el: h('div', { class: 'ld-line b-claude ' + x.s.state, 'data-moment': x.moment },
        h('p', { class: 'ld-says', dir: 'auto' }, ...sayNodes(p, x.moment, x.v, x.s.task || x.s.ask ? taskNamed(p, x.s.task || x.s.ask) : null, 'card')),
        x.reply ? h('p', { class: 'b-claude-said', dir: 'auto', title: x.reply }, x.reply) : null,
        x.tick ? h('div', { class: 'ld-acts' }, h('button', { class: 'btn btn-small b-claude-tick', type: 'button', title: 'Tick off ' + x.tick.text + ', the task this session started from',
          onclick: () => ClaudeWork.tick(p, x.tick) }, 'Tick it')) : null) });
    }
    return lines.sort((a, b) => a.rank - b.rank).map(x => x.el);
  }
  /* The leader card in the project view: its news for this building, else nothing (its greeting shows). */
  function viewLines(p) {
    return take(p.id).filter(it => !NEWS_CLAUDE.has(it.moment) || it.moment === 'finished')
      .map(it => lineEl(sayNodes(p, it.moment, it.v, taskFor(p, it), 'view'), { more: extraOf(p, it, 'view'), acts: actsOf(p, it, 'view'), moment: it.moment }));
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
  return { init, check, claude, ticked, add, renderSection, take, release, cardLines, viewLines, reportFace, yieldTo, hide, pump, redraw,
    isShowing: () => !!bub, isHeld: () => !!bub && !bub.auto, items: () => sortItems(live()), lineOf,
    _test: { sayMs: ms => { sayMs = ms; }, typeMs: ms => { typeMs = ms; }, talk: () => ({ id: talk.id, n: talk.n, done: talk.done }), state: () => JSON.parse(JSON.stringify(st)), bubble: () => bub && { ids: bub.list.map(x => x.id), i: bub.i, auto: bub.auto },
      forget: () => { st = fresh(); save(); held.clear(); undos.clear(); }, held: pid => (held.get(pid) || []).map(x => x.id) } };
})();
