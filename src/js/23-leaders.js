/* Leaders (0.1.51): the city's characters who run its buildings, designed over two rounds on 5 October 2026 and set up
   in Leaders, 20 October 2026. For now a leader holds a name, a role, a signature color and a portrait (L2); talking
   comes later. One leader per building, and one leader can run several. The leaders live in the side bar's Leaders
   section, are picked from a building's more menu or its project view, and show in the wheel's middle, the leader card
   in the project view and the status card (L1). Claude's copies and the city summary name them (L3). A portrait sits in
   the art store under 'leader:' and the leader's id, and travels inline in backups and the data file. Since 0.1.82 a
   leader may carry a voice, picked in its editor. */
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
    const voice = sanitizeVoice(r.voice);
    out.push({ id, name: s(r.name, LEADER_MAX.name) || 'Leader', role: s(r.role, LEADER_MAX.role),
      color: /^#[0-9a-f]{6}$/i.test(r.color || '') ? r.color.toUpperCase() : leaderColor(id), portrait: !!r.portrait,
      createdAt: typeof r.createdAt === 'number' ? r.createdAt : Date.now(), ...(voice ? { voice } : {}) });
  }
  return out;
}
/* A leader's voice (0.1.82, Character voices): the settings it talks with, picked in its editor, the preset it
   started from, and the pitch moved from it; none, and it talks in its own voice, from its id. Read with care, as every
   number is kept in its slider's range. */
const VOICE_KEYS = ['tone', 'range', 'speed', 'every', 'len', 'wobble', 'robot', 'radio'];   // what a preset sets, with its note
function sanitizeVoice(v) {
  if (!v || typeof v !== 'object') return null;
  const n = (x, lo, hi, d) => (typeof x === 'number' && isFinite(x) ? Math.min(hi, Math.max(lo, x)) : d);
  return { from: typeof v.from === 'string' && /^[\w-]{1,20}$/.test(v.from) ? v.from : 'own', pitch: Math.round(n(v.pitch, -12, 12, 0)),
    base: n(v.base, 40, 1500, 196), tone: n(v.tone, 0, 1, 0.55), range: Math.round(n(v.range, 0, 8, 4)), speed: n(v.speed, 0.6, 1.6, 1),
    every: Math.round(n(v.every, 1, 4, 2)), len: n(v.len, 0.03, 0.1, 0.055), wobble: n(v.wobble, 0, 1, 0), robot: !!v.robot, radio: !!v.radio,
    gain: n(v.gain, 0.2, 5, 1) };
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
  /* City as My Terminal (0.1.91), written at the build: an approval (L3, his i6 answer "take you to t3"), a message
     from the city taken (L3, card only), and a send held while T3 is closed (L3, its bubble carrying Open T3) */
  waiting_ok: 'Claude needs your OK on {task}.',
  took: 'Claude took your message on {task}. Started {ago}.',                    // the status card only
  t3closed: 'T3 is closed, so {task} waits to be sent.',
  asks: 'Claude wants your OK first: {change}.',
  failed: 'Claude stopped on an error while working on {task}.',
  finished: 'Claude handed {task} back to you.',                             // whether it is done is yours to say (0.1.69)
  answers: 'Your answers are in for {round}: {n} of {total}.',
  week: 'Last week we finished {n} tasks. Next up: {task}.',
  week_quiet: 'Quiet week: nothing finished. {task} is a good start.',
  working: 'Claude is working on {task}. Started {ago}.',                       // the status card only
  /* the leader card only: where the building stands, then its next task (General UX, Round 1, P3: "where it stands
     should be said by the leader"); written at 0.1.86 from the approved "We finished one today, 12 to go. Next up:" */
  greet_done: 'We finished {count} today, {togo}. Next up: {task}.',          // a task ticked today
  greet_on: "We're on pace, {togo}. Next up: {task}.",                        // One task per N days, on its pace
  greet_behind: 'We slipped behind our pace, {togo}. Next up: {task}.',       // yellow, under One task per N days
  greet_behind_more: "We're falling further behind, {togo}. Next up: {task}.", // red, under One task per N days
  greet_day: 'Nothing finished here for a day, {togo}. Next up: {task}.',     // red, under Work until finished
  greet: '{togo}. Next up: {task}.',                                          // no system, or away, and nothing ticked today
  greet_empty: 'Nothing open here yet. Add the next task.',
};
/* Quill, the Pocket Wizard (0.1.69, Leader Bubbles, Round 2): the city's voice for wizard rounds, as Gus is for the
   garbage and Proxima for the reports. For every building he says a round Claude attached with no finish to sit under,
   and a round's answers coming in; under a finish, a round is part of its leader's report. His portrait ships with
   the city. A leader of the city's own named Quill is him: his rounds come under that leader's face, portrait and
   color, so one Quill shows in News, never two (Abdurrahman has him lead Decision Wizard). */
const QUILL = { id: 'quill', name: 'Quill', role: 'The Pocket Wizard', color: '#8E5A9E', portrait: true };
const QUILL_MOMENTS = new Set(['round', 'answers']);
const quillLeader = () => (Array.isArray(DB.leaders) && DB.leaders.find(l => leaderName(l).toLowerCase() === 'quill')) || QUILL;
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
  /* an approval says so (0.1.91); a working line from the city's own message says it was taken */
  const text = LEADER_LINES[moment === 'waiting' && v.wait === 'approval' ? 'waiting_ok' : moment === 'working' && v.took ? 'took' : moment];
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
function leaderGreeting(p, now = Date.now()) {
  const t = nextTask(p);
  if (!t) return leaderSay('greet_empty');
  const open = openTasks(p, now), today = ymd(now);
  const late = open.filter(x => { const d = dueInfo(x, now); return d && d.diff < 0; }).length;
  const togo = open.length + ' to go' + (late ? ', ' + late + ' of them overdue' : '');
  const count = typeof taskTicks === 'function' ? taskTicks([p], now).filter(e => e.day === today).length : 0;
  const u = urgencyOf(p, now), sys = (p.urgency || {}).system;
  const moment = count ? 'greet_done'
    : sys === 'pace' && !awayNow(now) ? (u.system === 'red' ? 'greet_behind_more' : u.system === 'yellow' ? 'greet_behind' : 'greet_on')
    : sys === 'finish' && u.system === 'red' ? 'greet_day' : 'greet';
  return leaderSay(moment, { task: t.text, togo, count: countWord(count) });
}
/* A small count in words, as the leader says it: one to nine, then the number. */
const countWord = n => ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'][n] || String(n);

/* A signature color, darker or lighter: f below 0 mixes in black, above 0 white. */
function shadeHex(hex, f) {
  const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255];
  const m = c.map(x => Math.round(f < 0 ? x * (1 + f) : x + (255 - x) * f));
  return '#' + m.map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
}
