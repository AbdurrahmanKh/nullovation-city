/* Gus Grimsby, the Garbage Man: chief of the city's cleanup crew, grumpy but fair. He lives in the side bar beside This
   week and Urgent while the city has garbage, with a report in one line, the task to start with, and every building
   with garbage, most first; a click on one goes to it. He speaks up by himself four times: the first time the city is
   opened each day with garbage in it, when the garbage passes 50 pieces and again 200 (each once as it climbs past,
   at most once a day), and when the last piece goes, just before he steps away. His words show in a speech bubble at
   the map's top left, and under his face in the side bar. He never mentions pieces, only tasks. The Garbage switch
   sends him away with the garbage. Until his portrait is made, a faceless stand-in in his colors takes its place. */
const Gus = (() => {
  const KEY = 'nullovation-city:gus';                          // the days he last spoke, on this computer
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
  let line = '', sayTimer = 0, saying = false, lastTotal = null, lastOnMap = null, started = false, sayMs = SAY_MS;
  const armed = {};

  /* ---------- the report ---------- */
  function report(now = Date.now()) {
    const rows = [];
    for (const p of DB.projects) { const b = Garbage.breakdown(p, now); if (b.n > 0) rows.push({ p, b }); }
    rows.sort((a, b) => b.b.n - a.b.n || a.p.name.localeCompare(b.p.name));
    const urgent = rows.filter(r => r.b.level === 'urgent').length, attention = rows.filter(r => r.b.level === 'attention').length;
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
    return { rows, urgent, attention, overdue, tasks, fix };
  }
  function reportLine(r) {
    const lead = [];
    if (r.urgent) lead.push(plural(r.urgent, 'project needs', 'projects need') + ' your urgent attention');
    if (r.attention) lead.push(plural(r.attention, 'project needs', 'projects need') + ' your attention');
    const out = [];
    if (lead.length) out.push(lead.join(', ') + '.');
    if (r.overdue) out.push('You have ' + plural(r.overdue, 'overdue task', 'overdue tasks') + '.');
    if (!out.length) return '';
    out.push(r.urgent + r.attention + r.overdue > 1 ? "Let's clean them up." : "Let's clean it up.");
    return out.join(' ');
  }
  const short = (s, n = 60) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s);
  const taskName = fix => (fix.t ? short(fix.t.text) : 'any task in ' + fix.p.name);
  const fixLine = r => (r.fix ? 'Start with ' + (r.fix.t ? short(r.fix.t.text) + ', in ' + r.fix.p.name : 'any task in ' + r.fix.p.name) + '.' : '');
  function rowText({ b }) {
    const bits = [];
    if (b.level) bits.push(b.level === 'urgent' ? 'urgent' : 'needs attention');
    if (b.late.length) bits.push(plural(b.late.length, 'overdue task', 'overdue tasks'));
    return bits.join(', ');
  }
  /* A line with its blanks filled; a task that starts a sentence starts with a capital. */
  function fill(text, r) {
    const task = r.fix ? taskName(r.fix) : '';
    return text.replace('{tasks}', plural(r.tasks, 'task', 'tasks'))
      .replace(/(^|[.!?] )\{task\}/, (m, pre) => pre + task.charAt(0).toUpperCase() + task.slice(1)).replace('{task}', () => task);
  }
  const pick = list => list[Math.floor(Math.random() * list.length)];

  /* ---------- his face: a faceless stand-in in his colors (yellow cap with the truck's teal badge, grey brows and walrus
     mustache, coral overalls with a gold band, a broom over his shoulder), until his portrait is made ---------- */
  const FACE = [
    '...........oooooo...........',
    '.........ooyyyyyyoo.........',
    '........oyyyyyyyyyyo........',
    '........oyyyyyyyyyyo........',
    '........oYYYYtYYYYYo......oB',
    '......oooooooooooooooo...oBB',
    '.......ommcccccccccmmo..oBBB',
    '........occccccccccco....oBB',
    '........occccccccccco.....b.',
    '.......ommmmmmmmmmmmmo....b.',
    '......ommmmmmmmmmmmmmmo..b..',
    '......ommmo.occco.ommmo..b..',
    '.......ooo..occco..ooo..b...',
    '........ooooccccooooo...b...',
    '......oo~cccccccccccoo.b....',
    '.....o~cccccccccccccccob....',
    '....o~ccccccccccccccccbco...',
    '...o~ccccccYYYYYYYYYYcccco..',
    '...occcccYYYYYYYYYYYYYccco..',
    '..o~cccccccccccccccccccccco.',
    '..occcccccccccccccccccccccco',
    '..occcccccccccccccccccccccco',
  ];
  const COLORS = { o: '#2B2542', c: '#F29A74', '~': '#FFB797', y: '#FFE38A', Y: '#F2C75C', t: '#3FA79E', m: '#CBC2DB', b: '#9C7C6B', B: '#F2C75C' };
  let faceCanvas = null;
  function face(scale) {
    if (!faceCanvas) {
      const w = Math.max(...FACE.map(r => r.length)), hh = FACE.length;
      const [c, g] = mkCanvas(w, hh);
      FACE.forEach((row, y) => [...row].forEach((ch, x) => { if (COLORS[ch]) { g.fillStyle = COLORS[ch]; g.fillRect(x, y, 1, 1); } }));
      faceCanvas = c;
    }
    const img = h('img', { class: 'gus-sil', alt: '', src: faceCanvas.toDataURL('image/png'), width: faceCanvas.width * scale, height: faceCanvas.height * scale });
    return img;
  }

  /* ---------- the side bar ---------- */
  function render() {
    const sec = $('#sbGus');
    if (!sec) return;
    const r = report(), onMap = Garbage.onMap();
    const show = Garbage.isOn() && (r.rows.length > 0 || onMap > 0 || saying);
    sec.hidden = !show;
    if (!show) return;
    if (!$('#gusFace').firstChild) $('#gusFace').append(face(2));
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
    const box = $('#gusSay');
    $('#gusSayText').textContent = text;
    if (!$('#gusSayFace').firstChild) $('#gusSayFace').append(face(2));
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

  function init() {
    $('#gusSayClose').innerHTML = iconSvg('close', 16);
    $('#gusSayClose').addEventListener('click', hush);
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
  return { init, render, report, reportLine, fixLine, fill, LINES, hush, isSaying: () => saying, line: () => line,
    _test: { sayMs: ms => { sayMs = ms; }, days: () => ({ ...days }), forget: () => { days = {}; saveDays(); } } };
})();
