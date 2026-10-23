/* ---------- recurring tasks and the one-line add (Tasks, Round 2: R1 to R4, O1, O2) ----------
   A task that repeats carries `repeat`, one of:
     { every: 'day', n }            every day (n 1) or every N days
     { every: 'week', days }        weekly on chosen weekdays, 0 for Sunday
     { every: 'month', day }        monthly on a date, 1 to 31; a month without that date uses its last day
     { every: 'year', month, day }  yearly, month 1 to 12
   Ticking it moves the same task on (R4): its due date becomes its next date, and it waits, out of every list, count
   and bubble, until that day comes and it is due again (R1, in Abdurrahman's words: "when you tick the task, it will
   go away. after 7 days it will get re-added"). `waiting` marks it; only Activity's Done line records each tick.
   The next date is by schedule (R3): weekdays, monthly dates and years keep their rhythm, the first such date after
   the later of today and its due date, so a late tick skips what was missed; every day and every N days count from
   the day of the tick. A repeat not ticked by its date stays one overdue task until it is. */
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const WEEK_ORDER = [6, 0, 1, 2, 3, 4, 5];                      // the city's weeks run Saturday to Friday
const ordinal = n => n + ((n % 100 >= 11 && n % 100 <= 13) ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' })[n % 10] || 'th');
const daysInMonth = (y, m) => new Date(y, m + 1, 0).getDate();  // m from 0; Date carries a month past December over
const dateOn = (y, m, d) => { const x = new Date(y, m, 1); return new Date(x.getFullYear(), x.getMonth(), Math.min(d, daysInMonth(x.getFullYear(), x.getMonth()))).getTime(); };
const plusDays = (ts, n) => { const d = new Date(ts); return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n).getTime(); };

/* A repeat read from saved data, a backup or a plan: kept only when whole. */
function sanitizeRepeat(r) {
  if (!r || typeof r !== 'object') return null;
  const int = (x, a, b) => (Number.isInteger(x) && x >= a && x <= b ? x : null);
  if (r.every === 'day') return { every: 'day', n: int(r.n, 1, 365) || 1 };
  if (r.every === 'week') {
    const days = [...new Set((Array.isArray(r.days) ? r.days : []).filter(x => int(x, 0, 6) != null))].sort((a, b) => a - b);
    return days.length ? { every: 'week', days } : null;
  }
  if (r.every === 'month') { const day = int(r.day, 1, 31); return day ? { every: 'month', day } : null; }
  if (r.every === 'year') {
    const month = int(r.month, 1, 12), day = int(r.day, 1, 31);
    return month && day && day <= daysInMonth(2024, month - 1) ? { every: 'year', month, day } : null;   // 2024 has a 29 February
  }
  return null;
}
/* "Every day", "Every 3 days", "Weekly on Mon, Thu", "Monthly on the 20th", "Yearly on 20 Oct". */
function repeatText(r) {
  if (!r) return '';
  if (r.every === 'day') return r.n === 1 ? 'Every day' : 'Every ' + r.n + ' days';
  if (r.every === 'week') return 'Weekly on ' + WEEK_ORDER.filter(d => r.days.includes(d)).map(d => WEEKDAYS[d]).join(', ');
  if (r.every === 'month') return 'Monthly on the ' + ordinal(r.day);
  if (r.every === 'year') return 'Yearly on ' + r.day + ' ' + MONTHS[r.month - 1];
  return '';
}
/* The first day of the schedule on or after a day. */
function repeatOnOrAfter(r, start) {
  if (r.every === 'week') {
    for (let i = 0; i < 7; i++) { const x = plusDays(start, i); if (r.days.includes(new Date(x).getDay())) return x; }
    return start;
  }
  const d = new Date(start), y = d.getFullYear(), m = d.getMonth();
  if (r.every === 'month') { const x = dateOn(y, m, r.day); return x >= start ? x : dateOn(y, m + 1, r.day); }
  if (r.every === 'year') { const x = dateOn(y, r.month - 1, r.day); return x >= start ? x : dateOn(y + 1, r.month - 1, r.day); }
  return start;
}
/* A new repeat's first date: today, or the schedule's first day from today. */
const firstRepeatDue = (r, now = Date.now()) => ymd(repeatOnOrAfter(r, startOfDay(now)));
/* Where a ticked repeat moves to (R3). */
function nextRepeatDue(t, now = Date.now()) {
  const r = t.repeat, today = startOfDay(now);
  if (!r) return t.due;
  if (r.every === 'day') return ymd(plusDays(today, r.n));
  const due = parseYmd(t.due);
  return ymd(repeatOnOrAfter(r, plusDays(Math.max(today, due == null ? today : due), 1)));
}

/* A ticked repeat waiting for its next date: out of every list, count and bubble until then. */
const isWaiting = (t, now = Date.now()) => !t.done && !!t.repeat && !!t.waiting && parseYmd(t.due) > startOfDay(now);
/* Open: not done and not waiting. Everything that shows or counts open tasks asks this. */
const isOpenTask = (t, now = Date.now()) => !t.done && !isWaiting(t, now);
const openTasks = (p, now = Date.now()) => p.todos.filter(t => isOpenTask(t, now));
const waitingTasks = (p, now = Date.now()) => p.todos.filter(t => isWaiting(t, now)).sort((a, b) => parseYmd(a.due) - parseYmd(b.due));
function setWaiting(t, on) { if (on) t.waiting = true; else delete t.waiting; }
/* "Due today", "Due tomorrow", "Due Fri 23 Oct", "2 days overdue": a due date in words, as What is next shows it. */
function dueWords(due, now = Date.now()) {
  const d = dueInfo({ due }, now);
  return !d ? '' : d.diff > 1 ? 'Due ' + weekdayOf(due) + ' ' + fmtDate(parseYmd(due)) : d.text;
}
/* "tomorrow" or "Mon 26 Oct": when a waiting repeat comes back. */
function backWhen(t, now = Date.now()) {
  const n = daysBetween(now, parseYmd(t.due));
  return n === 1 ? 'tomorrow' : weekdayOf(t.due) + ' ' + fmtDate(parseYmd(t.due));
}
const backText = (t, now) => 'Back ' + backWhen(t, now);

/* Ticking a task off, wherever it is ticked: done, or for a repeat, on to its next date and out of sight until then.
   Either way it is work for urgency, and one Done line in Activity (log: false leaves the line to the caller).
   Returns what the task was, for untickTask. */
function tickTask(p, t, { now = Date.now(), log = true } = {}) {
  const was = { done: t.done, doneAt: t.doneAt, due: t.due, waiting: !!t.waiting };
  if (t.repeat) { t.due = nextRepeatDue(t, now); setWaiting(t, true); }
  else { t.done = true; t.doneAt = now; }
  markWorked(p, now);
  if (log) logActivity(p, 'Done: ' + t.text);
  if (typeof Celebrate !== 'undefined') Celebrate.ticked(p, t);     // its particles, and a party for a finished milestone
  if (typeof Ghosts !== 'undefined') Ghosts.ticked(p, t);           // its ghost, if it haunts, rises and fades
  if (typeof News !== 'undefined') News.ticked(p, t);               // a milestone one task from done is its leader's news
  return was;
}
function untickTask(p, t, was = null, { log = true } = {}) {
  if (t.repeat && was && !was.done) { t.due = was.due; setWaiting(t, was.waiting); }
  else { t.done = false; t.doneAt = null; delete t.archiveFrom; }
  if (log) logActivity(p, 'Reopened: ' + t.text);
}
/* After a repeat is ticked: where it went, with Undo. */
function repeatToast(p, t, was) {
  toast(t.text + ' comes back ' + backWhen(t) + '.', '', { label: 'Undo', run: () => {
    untickTask(p, t, was); changed(p);
    if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render();
  } });
}

/* ---------- the one-line add (O1, O2) ----------
   A task typed in one line, with marks taken out of the title: !fri, !today, !tomorrow, !20, !oct 20 (or !20 oct, or
   !2026-10-20) for the due date, the next such date that is not past; #daily, #weekly, #monthly, #yearly, #every day
   and #every N days for a repeat, #weekly on the due date's weekday (on each weekday given, with several); @name for
   the milestone whose name starts with it, a new one by that name when none does; and in the city-wide quick add,
   /name for the project. A repeat with no date starts today. Marks are English; the title can be in any language.
   A word that does not read as a mark stays in the title, so "#1 priority" and "bob@mail.com" are left alone. */
const WEEKDAY_WORDS = { sun: 0, sunday: 0, mon: 1, monday: 1, tue: 2, tues: 2, tuesday: 2, wed: 3, weds: 3, wednesday: 3,
  thu: 4, thur: 4, thurs: 4, thursday: 4, fri: 5, friday: 5, sat: 6, saturday: 6 };
const MONTH_WORDS = { jan: 0, january: 0, feb: 1, february: 1, mar: 2, march: 2, apr: 3, april: 3, may: 4, jun: 5, june: 5,
  jul: 6, july: 6, aug: 7, august: 7, sep: 8, sept: 8, september: 8, oct: 9, october: 9, nov: 10, november: 10, dec: 11, december: 11 };
/* A date mark's words, a and the one after it, b: { at, used, weekday } or null. */
function readDateMark(a, b, now = Date.now()) {
  const today = startOfDay(now), s = String(a || '').toLowerCase(), n = String(b || '').toLowerCase();
  const num = x => (/^\d{1,2}$/.test(x) ? +x : null);
  if (s === 'today') return { at: today, used: 1 };
  if (s === 'tomorrow') return { at: plusDays(today, 1), used: 1 };
  if (s in WEEKDAY_WORDS) { const w = WEEKDAY_WORDS[s]; return { at: plusDays(today, (w - new Date(today).getDay() + 7) % 7), used: 1, weekday: w }; }
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) { const at = parseYmd(s); return at != null && ymd(at) === s ? { at, used: 1 } : null; }
  const yearly = (m, d) => {                                   // this year's, or the next year's that has it
    if (d < 1 || d > daysInMonth(2024, m)) return null;
    for (let y = new Date(today).getFullYear(); y < new Date(today).getFullYear() + 8; y++) {
      if (d > daysInMonth(y, m)) continue;
      const at = new Date(y, m, d).getTime();
      if (at >= today) return at;
    }
    return null;
  };
  if (s in MONTH_WORDS && num(n) != null) { const at = yearly(MONTH_WORDS[s], num(n)); return at == null ? null : { at, used: 2 }; }
  if (num(s) != null && n in MONTH_WORDS) { const at = yearly(MONTH_WORDS[n], num(s)); return at == null ? null : { at, used: 2 }; }
  if (num(s) != null && num(s) >= 1 && num(s) <= 31) {        // the next month, from this one, that has that date
    const d = new Date(today);
    for (let i = 0; i < 13; i++) {
      const y = new Date(d.getFullYear(), d.getMonth() + i, 1).getFullYear(), m = new Date(d.getFullYear(), d.getMonth() + i, 1).getMonth();
      if (num(s) > daysInMonth(y, m)) continue;
      const at = new Date(y, m, num(s)).getTime();
      if (at >= today) return { at, used: 1 };
    }
  }
  return null;
}
/* The marks in a line, before they are matched to a project or a milestone. `spans` says where each mark sits in
   the line as typed, { start, end, kind, shift }, kind one of / @ ! # +, so the line over the map can color them. */
function readTaskMarks(text, { now = Date.now(), cityWide = false } = {}) {
  const src = String(text || ''), toks = [...src.matchAll(/\S+/g)].map(m => ({ w: m[0], at: m.index }));
  const words = toks.map(x => x.w);
  const title = [], dates = [], spans = [];
  let rep = null, ms = null, project = null, shift = '', marks = 0;
  const mark = (i, used, kind, extra = {}) => { const a = toks[i], b = toks[i + used - 1]; spans.push({ start: a.at, end: b.at + b.w.length, kind, ...extra }); marks++; };
  for (let i = 0; i < words.length; i++) {
    const w = words[i], head = w[0], rest = w.slice(1), low = rest.toLowerCase();
    if (head === '!' && rest) {
      const d = readDateMark(rest, words[i + 1], now);
      if (d) { dates.push(d); mark(i, d.used, '!'); i += d.used - 1; continue; }
    } else if (head === '#' && rest) {
      if (['daily', 'weekly', 'monthly', 'yearly'].includes(low)) { rep = low; mark(i, 1, '#'); continue; }
      if (low === 'every') {
        const a = words[i + 1] || '', b = words[i + 2] || '';
        if (/^days?$/i.test(a)) { rep = { every: 'day', n: 1 }; mark(i, 2, '#'); i += 1; continue; }
        if (/^\d{1,3}$/.test(a) && +a >= 1 && +a <= 365 && /^days?$/i.test(b)) { rep = { every: 'day', n: +a }; mark(i, 3, '#'); i += 2; continue; }
      }
    } else if (head === '+' && /^\p{L}/u.test(rest)) {          // a shift: +create, +think, +errand, or the start of one
      const s = SHIFT_IDS.find(id => id.startsWith(low));         // a + word that names none stays in the title
      if (s) { shift = s; mark(i, 1, '+', { shift: s }); continue; }
    } else if (head === '@' && rest) { ms = rest; mark(i, 1, '@'); continue; }
    else if (head === '/' && rest && cityWide) { project = rest; mark(i, 1, '/'); continue; }
    title.push(w);
  }
  const today = startOfDay(now);
  const first = dates.length ? Math.min(...dates.map(d => d.at)) : null;
  const base = first != null ? first : today;
  let repeat = null;
  if (rep === 'daily') repeat = { every: 'day', n: 1 };
  else if (rep === 'weekly') {
    const days = dates.filter(d => d.weekday != null).map(d => d.weekday);
    repeat = sanitizeRepeat({ every: 'week', days: days.length ? days : [new Date(base).getDay()] });
  } else if (rep === 'monthly') repeat = { every: 'month', day: new Date(base).getDate() };
  else if (rep === 'yearly') repeat = { every: 'year', month: new Date(base).getMonth() + 1, day: new Date(base).getDate() };
  else if (rep) repeat = rep;
  const due = first != null ? ymd(first) : repeat ? ymd(today) : '';
  return { title: title.join(' ').slice(0, 500), due, repeat, ms, project, shift, marks, spans };
}
/* A name a mark points at: the first whose name is the mark, else starts with it, else has a word that starts with
   it; case, Arabic letter forms, and hyphens or underscores for spaces aside. */
const markKey = s => norm(String(s).replace(/[-_\s]+/g, ' '));
function markMatch(list, name, mark) {
  const key = markKey(mark), of = x => markKey(name(x));
  return list.find(x => of(x) === key) || list.find(x => of(x).startsWith(key)) || list.find(x => of(x).split(/\s+/).some(w => w.startsWith(key))) || null;
}
/* Where a task added without @ goes: the current milestone, else the last one not in the archive, else a new To do. */
function defaultMilestone(p) {
  const cur = currentGroup(p), live = liveMilestones(p);
  return cur && cur.ms ? cur.ms.id : live.length ? live[live.length - 1].id : null;
}
/* A typed line, read for one place: the project view's add field (project and milestone given), the status card's
   (project given) or the quick add (cityWide, the project by /name or the one given). What it understood comes back
   as a line to show under the field, and ok says whether Enter can add it. */
function readTaskLine(text, { project = null, msId = null, cityWide = false, now = Date.now() } = {}) {
  const r = readTaskMarks(text, { now, cityWide });
  const out = { ...r, p: null, msId: null, msNew: '', parts: [], problem: '', ok: false };
  if (cityWide && r.project) {
    out.p = markMatch(DB.projects, p => p.name, r.project);
    if (!out.p) out.problem = '/' + r.project + ' fits no project';
  } else out.p = project;
  if (cityWide && !out.p && !out.problem) out.problem = 'Name the project with /name';
  if (out.p) {
    if (cityWide) out.parts.push(out.p.name);
    if (r.ms) {
      const m = markMatch(out.p.milestones, m => m.name, r.ms);
      if (m) { out.msId = m.id; out.parts.push('In ' + m.name); }
      else { out.msNew = r.ms.slice(0, 120); out.parts.push('New milestone ' + out.msNew); }
    } else {
      out.msId = msId || defaultMilestone(out.p);
      const m = cityWide && out.p.milestones.find(x => x.id === out.msId);
      if (m) out.parts.push('In ' + m.name);
      else if (cityWide && !out.msId) out.parts.push('New milestone To do');
    }
  }
  if (r.due) out.parts.push(dueWords(r.due, now));
  if (r.repeat) out.parts.push('Repeats ' + repeatText(r.repeat).replace(/^\w/, c => c.toLowerCase()));
  if (r.shift) out.parts.push('Shift: ' + shiftName(r.shift));
  if (!out.problem && !r.title && r.marks) out.problem = 'Type the task too';
  out.ok = !out.problem && !!r.title && !!out.p;
  return out;
}
/* Adds what readTaskLine read: a new task at the end of its milestone. Returns the task. */
function addTaskLine(r) {
  const p = r.p;
  let msId = r.msId;
  if (!msId) {
    const ms = { id: uid('m'), name: r.msNew || 'To do', collapsed: false };
    p.milestones.push(ms); msId = ms.id;
    logActivity(p, 'New milestone: ' + ms.name);
  }
  const ms = p.milestones.find(m => m.id === msId);
  if (ms) ms.collapsed = false;
  const t = Object.assign(todo(r.title, msId), { due: r.due });
  if (r.repeat) t.repeat = r.repeat;
  if (r.shift) t.shift = r.shift;
  p.todos.push(t);
  normalizeOrder(p);
  logActivity(p, 'Added todo: ' + t.text);
  changed(p);
  return t;
}
/* The line under an add field: what was understood, or what is missing, or before anything is typed, the marks. */
function taskLineHint(el, text, opts) {
  const r = readTaskLine(text, opts), empty = !String(text || '').trim();
  el.classList.toggle('bad', !empty && !!r.problem);
  el.textContent = empty ? (opts.cityWide ? '/name project · ' : '') + '!fri date · #weekly repeat · @name milestone · +create shift'
    : [r.problem, ...r.parts].filter(Boolean).join(' · ');
  return r;
}
