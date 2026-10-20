/* Gus Grimsby, the Garbage Man: chief of the city's cleanup crew, grumpy but fair. He lives in the side bar beside This
   week and Urgent while the city has garbage, with his overdue tasks in one line, the task to start with, and every
   building with garbage, most first; a click on one goes to it. He leaves urgent and needs attention to the map's
   bubbles. His [-] shrinks him to his face with a ! on it, kept on this computer until a click opens him again. He
   speaks up by himself four times: the first time the city is opened each day with garbage in it, when the garbage
   passes 50 pieces and again 200 (each once as it climbs past, at most once a day), and when the last piece goes,
   just before he steps away. His words show in a speech bubble at the map's top left, and under his face in the side
   bar. He never mentions pieces, only tasks. The Garbage switch
   sends him away with the garbage. His face is his portrait, on his dark coral (0.1.48). */
const Gus = (() => {
  const KEY = 'nullovation-city:gus';                          // the days he last spoke, on this computer
  const MIN_KEY = 'nullovation-city:gusMin';                   // shrunk to his face, on this computer
  const MARKS = [[200, 'filthy'], [50, 'dirty']];              // the worst first
  const SAY_MS = 14000;                                         // a speech bubble stays this long unless closed first
  const LINES = {
    open: ["You're back. {tasks} between this city and clean streets. Start with {task}.",
      'Took you long enough. {tasks} waiting. {task} first.',
      "I cannot clean what you don't fix. {tasks}. Start with {task}."],
    dirty: ['The city is getting dirty! We should do something about it.'],
    filthy: ['The city is filthy! This is unacceptable!'],
    clean: ["Clean streets. Don't get used to it.", "Not a wrapper in sight. I'll be off, then.", "Fine. Good work. Don't make me come back."],
  };
  let days = (() => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } })();
  const saveDays = () => { try { localStorage.setItem(KEY, JSON.stringify(days)); } catch (e) { /* this visit only */ } };
  let minimized = (() => { try { return localStorage.getItem(MIN_KEY) === '1'; } catch (e) { return false; } })();
  let line = '', sayTimer = 0, saying = false, lastTotal = null, lastOnMap = null, started = false, sayMs = SAY_MS;
  const armed = {};

  /* ---------- the report ---------- */
  function report(now = Date.now()) {
    const rows = [];
    for (const p of DB.projects) { const b = Garbage.breakdown(p, now); if (b.n > 0) rows.push({ p, b }); }
    rows.sort((a, b) => b.b.n - a.b.n || a.p.name.localeCompare(b.p.name));
    const overdue = rows.reduce((s, r) => s + r.b.late.length, 0);
    /* The tasks between the city and clean streets: every late task, and one in each project behind its pace with no late
       task of its own (finishing any of its tasks puts it back on pace, a late one included). */
    const tasks = overdue + rows.filter(r => r.b.level && !r.b.late.length).length;
    /* The task to start with: the one that clears the most. A late task also puts its project back on pace. */
    let fix = null;
    for (const { p, b } of rows) {
      for (const l of b.late) if (!fix || l.pts + b.sys > fix.v) fix = { v: l.pts + b.sys, p, t: l.t };
      if (b.sys && !b.late.length && (!fix || b.sys > fix.v)) fix = { v: b.sys, p, t: null };
    }
    return { rows, overdue, tasks, fix };
  }
  /* The overdue tasks only: which projects are urgent or need attention, the map's bubbles already show. */
  const reportLine = r => (r.overdue ? 'You have ' + plural(r.overdue, 'overdue task', 'overdue tasks') + '. ' + (r.overdue > 1 ? "Let's clean them up." : "Let's clean it up.") : '');
  const short = (s, n = 60) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s);
  const taskName = fix => (fix.t ? short(fix.t.text) : 'any task in ' + fix.p.name);
  const fixLine = r => (r.fix ? 'Start with ' + (r.fix.t ? short(r.fix.t.text) + ', in ' + r.fix.p.name : 'any task in ' + r.fix.p.name) + '.' : '');
  /* A building behind its pace with no late task: finishing any of its tasks clears it. */
  const rowText = ({ b }) => (b.late.length ? plural(b.late.length, 'overdue task', 'overdue tasks') : 'finish any task');
  /* A line with its blanks filled; a task that starts a sentence starts with a capital. */
  function fill(text, r) {
    const task = r.fix ? taskName(r.fix) : '';
    return text.replace('{tasks}', plural(r.tasks, 'task', 'tasks'))
      .replace(/(^|[.!?] )\{task\}/, (m, pre) => pre + task.charAt(0).toUpperCase() + task.slice(1)).replace('{task}', () => task);
  }
  const pick = list => list[Math.floor(Math.random() * list.length)];

  /* ---------- his face: his portrait (0.1.48), Abdurrahman's 256 px pixel art, shown shrunk in a frame of his dark
     coral; the frame sets the size ---------- */
  const face = () => h('img', { class: 'face-pic', alt: '', src: PORTRAITS.gus, width: 256, height: 256, draggable: 'false' });

  /* ---------- the side bar ---------- */
  function render() {
    const sec = $('#sbGus');
    if (!sec) return;
    const r = report(), onMap = Garbage.onMap();
    const show = Garbage.isOn() && (r.rows.length > 0 || onMap > 0 || saying);
    sec.hidden = !show;
    if (!show) return;
    if (!$('#gusFace').firstChild) { $('#gusFace').append(face()); $('#gusMiniFace').append(face()); }
    sec.classList.toggle('min', minimized);
    $('#gusFull').hidden = minimized; $('#gusMini').hidden = !minimized;
    if (minimized) return;
    $('#gusLine').hidden = !line; $('#gusLine').textContent = line;
    const rl = reportLine(r);
    $('#gusReport').hidden = !rl; $('#gusReport').textContent = rl;
    const fl = fixLine(r);
    $('#gusFix').hidden = !fl; $('#gusFix').textContent = fl;
    $('#gusRows').replaceChildren(...r.rows.map(row => h('li', null, h('button', { class: 'gus-row', type: 'button', title: 'Go to ' + row.p.name,
      onclick: () => { Menu.closeDrawer(); MapView.select(row.p.id); } },
      h('span', { class: 'gus-proj', dir: 'auto' }, row.p.name), ': ' + rowText(row)))));
  }

  /* ---------- speaking ---------- */
  function say(text) {
    line = text; saying = true;
    if (typeof Proxima !== 'undefined') Proxima.yieldToGus();   // never both at once: she says hers after him
    const box = $('#gusSay');
    $('#gusSayText').textContent = text;
    if (!$('#gusSayFace').firstChild) $('#gusSayFace').append(face());
    box.hidden = false;
    requestAnimationFrame(() => box.classList.add('show'));
    clearTimeout(sayTimer);
    sayTimer = setTimeout(hush, sayMs);
    render();
  }
  function hush() {
    clearTimeout(sayTimer);
    const box = $('#gusSay');
    if (box) { box.classList.remove('show'); box.hidden = true; }
    saying = false;
    render();
  }
  const today = () => ymd(Date.now());
  /* On every change to the garbage: the alarms as the total climbs, and the clean city when the last piece goes. */
  function changed() {
    if (!started) return;
    if (!Garbage.isOn()) { lastTotal = null; lastOnMap = null; hush(); line = ''; render(); return; }
    const total = Garbage.totals().total, onMap = Garbage.onMap(), d = today();
    if (lastTotal == null) { for (const [m] of MARKS) armed[m] = total < m; }
    else {
      /* Only the worst mark the total climbed past may speak, and only if it has not spoken today; the milder marks it
         passed on the way stay quiet until the total drops below them again. */
      const passed = MARKS.find(([m]) => total >= m && armed[m] && lastTotal < m);
      for (const [m] of MARKS) armed[m] = total < m ? true : armed[m] && lastTotal >= m ? armed[m] : false;
      if (passed && days[passed[1]] !== d) { days[passed[1]] = d; saveDays(); say(pick(LINES[passed[1]])); }
    }
    if (lastOnMap > 0 && onMap === 0 && total === 0) say(pick(LINES.clean));
    lastTotal = total; lastOnMap = onMap;
    render();
  }

  /* ---------- shrunk to his face, and open again ---------- */
  function minimize(on) {
    minimized = on;
    try { if (on) localStorage.setItem(MIN_KEY, '1'); else localStorage.removeItem(MIN_KEY); } catch (e) { /* this visit only */ }
    render();
    $(on ? '#gusMini' : '#gusMin').focus();
  }

  function init() {
    $('#gusSayClose').innerHTML = iconSvg('close', 16);
    $('#gusSayClose').addEventListener('click', hush);
    $('#gusMin').innerHTML = iconSvg('minus', 16);
    $('#gusMin').addEventListener('click', () => minimize(true));
    $('#gusMini').addEventListener('click', () => minimize(false));
    Garbage.onChange(changed);
    started = true;
    lastTotal = null; lastOnMap = null;
    changed();
    /* the first open of the day, with garbage in it */
    const d = today();
    if (days.open !== d) {
      days.open = d; saveDays();
      const r = report();
      if (Garbage.isOn() && r.rows.length) say(fill(pick(LINES.open), r));
    }
    setInterval(render, 60000);                                // a new day or a late task's new day, quietly
  }
  return { init, render, report, reportLine, fixLine, fill, LINES, hush, minimize, isMinimized: () => minimized, isSaying: () => saying, line: () => line,
    _test: { sayMs: ms => { sayMs = ms; }, days: () => ({ ...days }), forget: () => { days = {}; saveDays(); } } };
})();
