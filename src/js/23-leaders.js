/* Leaders (0.1.51): the city's characters who run its buildings, designed over two rounds on 5 October 2026 and set up
   in Leaders, 20 October 2026. For now a leader holds a name, a role, a signature color and a portrait (L2); talking
   comes later. One leader per building, and one leader can run several. The leaders live in the side bar's Leaders
   section, are picked from a building's more menu or its project view, and show in the wheel's middle, the leader card
   in the project view and the status card (L1). Claude's copies and the city summary name them (L3). A portrait sits in
   the art store under 'leader:' and the leader's id, and travels inline in backups and the data file. */
const LEADER_COLORS = ['#F29A74', '#F08BB4', '#D9536B', '#F2C75C', '#E8DCC4', '#7FD6B5', '#6FAE5C', '#3FA79E', '#8FD0F7', '#5A6FA8', '#B9A3E3', '#8E5A9E'];
const LEADER_MAX = { name: 60, role: 60 };
const leaderColor = seed => LEADER_COLORS[hashStr(String(seed)) % LEADER_COLORS.length];
const portraitKey = id => 'leader:' + id;

function blankLeader(o = {}) {
  const id = o.id || uid('ld');
  return Object.assign({ name: '', role: '', color: leaderColor(id), portrait: false, createdAt: Date.now() }, o, { id });
}
/* Makes loaded or imported leaders safe to use, as sanitizeProjects does for projects. */
function sanitizeLeaders(raw) {
  const out = [], seen = new Set();
  const s = (v, n) => (typeof v === 'string' ? v : '').replace(/\s+/g, ' ').trim().slice(0, n);
  for (const r of Array.isArray(raw) ? raw : []) {
    if (!r || typeof r !== 'object') continue;
    let id = typeof r.id === 'string' && r.id ? r.id.slice(0, 60) : uid('ld');
    if (seen.has(id)) id = uid('ld');
    seen.add(id);
    out.push({ id, name: s(r.name, LEADER_MAX.name) || 'Leader', role: s(r.role, LEADER_MAX.role),
      color: /^#[0-9a-f]{6}$/i.test(r.color || '') ? r.color.toUpperCase() : leaderColor(id), portrait: !!r.portrait,
      createdAt: typeof r.createdAt === 'number' ? r.createdAt : Date.now() });
  }
  return out;
}
const getLeader = id => (id && Array.isArray(DB.leaders) ? DB.leaders.find(l => l.id === id) : null) || null;
const leaderOf = p => (p ? getLeader(p.leader) : null);
const leaderProjects = l => DB.projects.filter(p => p.leader === l.id);
const leaderName = l => (l && l.name.trim()) || 'Leader';
/* A building whose leader is no longer in the city is left without one. */
function tidyLeaders() {
  if (!Array.isArray(DB.leaders)) DB.leaders = [];
  const ids = new Set(DB.leaders.map(l => l.id));
  for (const p of DB.projects) if (p.leader && !ids.has(p.leader)) p.leader = '';
}
/* One line for Claude: who leads the building, and as what (L3). Nothing when it has no leader. */
function leaderLine(p) {
  const l = leaderOf(p);
  return l ? 'Leader: ' + leaderName(l) + (l.role ? ', ' + l.role : '') : null;
}
/* Picking a building's leader is not work, like a pin: Updated stays, and nothing goes in Activity. */
function setLeader(p, id) {
  p.leader = getLeader(id) ? id : '';
}
/* ---------- the leaders' lines (0.1.58) ---------- */
/* One shared set for every leader, and for Proxima when she brings the news of a building with no leader, approved
   word for word in Leader UX, Round 4 (L1 to L3): one line per moment, until each leader gets lines of its own with the
   personality update. A line speaks for its building as "we" and never names it, since the bubble or the card round it
   shows the leader and the building. The moments that open by themselves, that wait with their leader, and that are
   not news are in Leader UX, M1; the greeting and the working line are not news, and show on the cards only. */
const LEADER_LINES = {
  behind: 'We slipped behind our pace. {task} puts us back on track.',          // its bubble turns yellow
  behind_more: "We're falling further behind. {task} pulls us back.",           // red, under One task per N days
  behind_day: 'Nothing finished here for a day. {task} gets us moving.',        // red, under Work until finished
  due: '{task} is due today.',
  due_many: '{n} tasks are due today. First up: {task}.',
  one_left: '{milestone} is one task from done: {task}. Finish it and we throw a street party.',
  added: 'Claude added {what}.',
  round: 'Claude attached a wizard round to {task}: {round}.',
  waiting: 'Claude is waiting for you on {task}.',
  asks: 'Claude wants your OK first: {change}.',
  failed: 'Claude stopped on an error while working on {task}.',
  finished: 'Claude finished {task}.',
  answers: 'Your answers are in for {round}: {n} of {total}.',
  week: 'Last week we finished {n} tasks. Next up: {task}.',
  week_quiet: 'Quiet week: nothing finished. {task} is a good start.',
  working: 'Claude is working on {task}. Started {ago}.',                       // the status card only
  greet: 'Welcome back. Next up: {task}.',                                      // the leader card only
  greet_empty: 'Nothing open here yet. Add the next task.',
};
const LEADER_TITLE_MAX = 60;                                 // a task's title in a line is cut short past this, as Gus cuts his
const lineTitle = s => (s.length > LEADER_TITLE_MAX ? s.slice(0, LEADER_TITLE_MAX - 1).trimEnd() + '\u2026' : s);
/* A moment's line with its blanks filled: {task} cut short past 60 characters, "{n} tasks" in the singular for one,
   a blank with nothing for it left as it is, and the line's first letter a capital, since a task's title may start it. */
function leaderSay(moment, v = {}) {
  return leaderParts(moment, v).map(x => x.text).join('');
}
/* The same line in parts (0.1.60): plain words, and each blank filled, with its name and its whole value, so a task in
   it can be shown as a link. */
function leaderParts(moment, v = {}) {
  const text = LEADER_LINES[moment];
  if (!text) return [];
  const out = [], re = /\{n\} tasks|\{(\w+)\}/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push({ text: text.slice(last, m.index) });
    if (!m[1]) out.push(v.n == null ? { text: m[0] } : { text: plural(v.n, 'task', 'tasks'), blank: 'n' });
    else if (v[m[1]] == null) out.push({ text: m[0] });
    else { const full = String(v[m[1]]); out.push({ text: m[1] === 'task' ? lineTitle(full) : full, blank: m[1], full }); }
    last = re.lastIndex;
  }
  if (last < text.length) out.push({ text: text.slice(last) });
  out[0] = { ...out[0], text: out[0].text.charAt(0).toUpperCase() + out[0].text.slice(1) };
  return out;
}
/* The greeting on the leader card, when its building has no news waiting: the next task, pinned or the current
   milestone's first open one, else that nothing is open. */
function leaderGreeting(p) {
  const t = nextTask(p);
  return t ? leaderSay('greet', { task: t.text }) : leaderSay('greet_empty');
}

/* A signature color, darker or lighter: f below 0 mixes in black, above 0 white. */
function shadeHex(hex, f) {
  const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255];
  const m = c.map(x => Math.round(f < 0 ? x * (1 + f) : x + (255 - x) * f));
  return '#' + m.map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
}
