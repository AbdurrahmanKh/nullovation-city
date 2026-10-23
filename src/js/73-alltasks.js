/* All tasks, the eighth of the task ideas (All tasks, Rounds 1 to 3): every open task in the city in one list. The side
   bar turns into it as it does into Settings and Reports, with the map in view (L1). It opens from a button at the side
   bar's foot, from L, or from Due this week's "and N more" line (A1).
   - The words field narrows it by a task's title or description, its project's name or its milestone's (D1).
   - The shift chips show one shift across the city, or the tasks with none, which a click on a shift tags (L1, sort).
   - The building tiles show one building, each counting the shift picked; the map itself stays as it is (A2, L1).
   - The starred task comes first (B2); then the dated tasks in day groups (C1); then the undated ones by building,
     those behind their pace first, the furthest behind first, then by name (C2), 3 each and Show all (C3).
   - A row says its project and milestone (B1); pointing at it lights its building on the map (D1); the square ticks
     it, the text opens it, the arrow keys move between rows, Enter opens one and Space ticks it (D1).
   It opens on everything each time: opening on the last shift picked was left out (L1). */
const AllTasks = (() => {
  const FIRST = 3;                                              // undated tasks a building shows before Show all (C3)
  let shift = '';                                               // '' every shift, 'none' the untagged, else a shift
  let building = '';                                            // a project's id, or '' for every building
  let words = '';
  const unfolded = new Set();                                   // buildings showing all their undated tasks
  const ticking = new Map();                                    // a ticked row stays a moment, struck through
  const was = new Map();                                        // a ticked repeat's state, for unticking it
  const heldDue = new Map();                                    // a ticked row keeps its old date while it stays, so it stays put
  const heldMark = new Map();                                   // and its star and pin, which the tick clears

  const isOpen = () => !!$('#allTasks') && !$('#allTasks').hidden;
  function open() {
    shift = ''; building = ''; words = ''; unfolded.clear();
    if (typeof Settings !== 'undefined') Settings.close(false);  // the four share the side bar
    if (typeof Reports !== 'undefined') Reports.close(false);
    if (typeof Leaders !== 'undefined') Leaders.close(false);
    Menu.toggleDrawer(true);
    $('#sbLists').hidden = true; $('#allTasks').hidden = false;
    $('#menu').classList.add('in-alltasks');
    $('#menu').scrollTop = 0;
    $('#atFind').value = '';
    render();
    $('#allTasks').focus({ preventScroll: true });            // not the field, so L closes it again; the down arrow goes to the rows
  }
  function close(refocus = true) {
    if (!isOpen()) return false;
    $('#allTasks').hidden = true;
    Menu.listsBack();
    $('#menu').classList.remove('in-alltasks');
    MapView.light(null);
    if (refocus) $('#btnOpenAllTasks').focus({ preventScroll: true });
    return true;
  }
  /* Shown: open, and on a narrow window in the open drawer. Opening a task closes the drawer over the list; L then
     brings it back rather than closing it unseen. */
  const shown = () => isOpen() && (!window.matchMedia('(max-width: 760px)').matches || $('#menu').classList.contains('open'));
  const toggle = () => { if (shown()) close(); else open(); };

  /* ---------- what the list holds ---------- */
  const msOf = (p, t) => p.milestones.find(m => m.id === t.milestoneId) || null;
  const fitsShift = (t, s = shift) => !s || (s === 'none' ? !t.shift : t.shift === s);
  const fitsWords = (p, t, key) => !key || norm([t.text, t.description || '', p.name, (msOf(p, t) || {}).name || ''].join(' \n ')).includes(key);
  /* Every open task that fits the words, with a ticked one held for its moment. */
  function pool(now) {
    const key = norm(words.trim()), out = [];
    for (const p of DB.projects) for (const t of p.todos)
      if ((isOpenTask(t, now) || ticking.has(t.id)) && fitsWords(p, t, key)) {
        const m = heldMark.get(t.id);
        out.push({ p, t, due: heldDue.has(t.id) ? heldDue.get(t.id) : t.due, star: m ? m.star : p.star === t.id, pin: m ? m.pin : p.pin === t.id });
      }
    return out;
  }
  /* How far behind its pace a building is: its urgency garbage, which only a building behind its pace has (C2). */
  const behind = p => (typeof Garbage !== 'undefined' ? Garbage.breakdown(p).sys : 0);
  function groupsFor(list, now) {
    const ws = weekStartOf(now), thisEnd = addDays(ws, 7), nextEnd = addDays(ws, 14);
    const star = list.find(x => x.star) || null;               // a ticked star stays in its card for its moment too
    const rest = list.filter(x => x !== star);
    const dated = rest.filter(x => x.due && parseYmd(x.due) != null)
      .sort((a, b) => parseYmd(a.due) - parseYmd(b.due) || a.p.name.localeCompare(b.p.name));
    const days = [['late', 'Overdue'], ['today', 'Today'], ['tomorrow', 'Tomorrow'], ['week', 'Rest of this week'], ['next', 'Next week'], ['later', 'Later']]
      .map(([id, title]) => ({ id, title, rows: [] }));
    const at = id => days.find(d => d.id === id).rows;
    for (const x of dated) {
      const diff = daysBetween(now, parseYmd(x.due)), due = parseYmd(x.due);
      at(diff < 0 ? 'late' : diff === 0 ? 'today' : diff === 1 ? 'tomorrow' : due < thisEnd ? 'week' : due < nextEnd ? 'next' : 'later').push(x);
    }
    const undated = rest.filter(x => !(x.due && parseYmd(x.due) != null));
    const order = new Map();                                      // each project's own order: its pin, then its milestones
    const projects = [...new Set(undated.map(x => x.p))];
    for (const p of projects) {
      const seq = groupsOf(p).flatMap(g => g.todos);
      const marked = undated.find(x => x.p === p && x.pin), pin = marked ? marked.t : null;
      (pin ? [pin, ...seq.filter(t => t !== pin)] : seq).forEach((t, i) => order.set(t.id, i));
    }
    const lag = new Map(projects.map(p => [p.id, behind(p)]));
    projects.sort((a, b) => (lag.get(b.id) > 0) - (lag.get(a.id) > 0) || lag.get(b.id) - lag.get(a.id) || a.name.localeCompare(b.name));
    const buildings = projects.map(p => ({ p, rows: undated.filter(x => x.p === p).sort((a, b) => order.get(a.t.id) - order.get(b.t.id)) }));
    return { star, days: days.filter(d => d.rows.length), buildings };
  }

  /* ---------- drawing ---------- */
  /* Redraws the list, keeping the focus on the control that had it, or the one now in its place. */
  let lastSig = '';
  function render(force = true) {
    if (!isOpen()) return;
    const now = Date.now();
    const all = pool(now);
    if (building && !getProject(building)) building = '';
    /* A change elsewhere in the city redraws it only when something it shows changed, so a row under the pointer
       stays put, and its buttons with it. */
    const sig = JSON.stringify([ymd(now), shift, building, words, [...unfolded], all.map(x => [x.t.id, x.t.text, x.due, x.t.shift || '',
      !!x.t.repeat, ticking.has(x.t.id), x.pin, x.star, (msOf(x.p, x.t) || {}).name || '', x.t.round ? roundStateText(roundState(x.t)) : '']),
      DB.projects.map(p => [p.id, p.name, p.generic, p.art.has, p.flip, behind(p)])]);
    if (!force && sig === lastSig) return;
    lastSig = sig;
    const a = document.activeElement, key = a && $('#allTasks').contains(a) && a.id !== 'atFind' ? a.dataset.k : null;
    const place = key ? $$('#allTasks [data-k]').indexOf(a) : -1, top = $('#menu').scrollTop;
    const list = all.filter(x => fitsShift(x.t) && (!building || x.p.id === building));
    summary(list, now);
    chips(all.filter(x => !building || x.p.id === building));
    tiles(all.filter(x => fitsShift(x.t)));
    $('#atList').replaceChildren(...body(list, now));
    $('#menu').scrollTop = top;
    if (key) {
      const els = $$('#allTasks [data-k]'), b = $(`#allTasks [data-k="${CSS.escape(key)}"]`) || els[Math.min(place, els.length - 1)];
      if (b) b.focus({ preventScroll: true });
    }
  }
  function refresh() { if (isOpen()) render(false); }
  /* "34 open, 2 overdue, 5 due this week", for what the list shows (D1). */
  function summary(list, now) {
    const ws = weekStartOf(now), end = addDays(ws, 7);
    const open = list.filter(x => !ticking.has(x.t.id)), dated = open.filter(x => x.due && parseYmd(x.due) != null);
    const late = dated.filter(x => daysBetween(now, parseYmd(x.due)) < 0).length;
    const week = dated.filter(x => daysBetween(now, parseYmd(x.due)) >= 0 && parseYmd(x.due) < end).length;
    $('#atSum').replaceChildren(h('b', null, String(open.length)), ' open, ', h('b', { class: late ? 'late' : null }, String(late)), ' overdue, ',
      h('b', null, String(week)), ' due this week');
  }
  function chips(list) {
    const n = s => list.filter(x => !ticking.has(x.t.id) && fitsShift(x.t, s)).length, none = n('none');
    const chip = (s, label, count) => h('button', { class: 'at-chip' + (s === 'none' ? '' : ' shift-' + s), type: 'button', 'data-k': 'shift-' + s, 'data-shift': s,
      'aria-pressed': String(shift === s), title: shift === s ? 'Showing ' + label.toLowerCase() + '. Click to show every shift' : s === 'none' ? 'The tasks with no shift yet, to sort' : SHIFT_HINTS[s],
      onclick: () => { shift = shift === s ? '' : s; render(); } }, h('i', { class: 'shift-dot', 'aria-hidden': 'true' }), label, h('span', { class: 'n' }, String(count)));
    $('#atShifts').replaceChildren(...SHIFTS.map(([s, name]) => chip(s, name, n(s))), ...(none || shift === 'none' ? [chip('none', 'No shift', none)] : []));
  }
  function tiles(list) {
    const count = new Map();
    for (const x of list) if (!ticking.has(x.t.id)) count.set(x.p.id, (count.get(x.p.id) || 0) + 1);
    const projects = DB.projects.filter(p => count.get(p.id) || p.id === building).sort((a, b) => a.name.localeCompare(b.name));
    $('#atTiles').replaceChildren(
      h('button', { class: 'at-tile all', type: 'button', 'data-k': 'tile-all', 'aria-pressed': String(!building), title: 'Every building', onclick: () => { building = ''; render(); } }, 'All'),
      ...projects.map(p => {
        const n = count.get(p.id) || 0;
        return h('button', { class: 'at-tile', type: 'button', 'data-k': 'tile-' + p.id, 'data-p': p.id, 'aria-pressed': String(building === p.id),
          title: p.name + ': ' + plural(n, 'task', 'tasks') + (building === p.id ? '. Click to show every building' : ''), 'aria-label': p.name + ', ' + plural(n, 'task', 'tasks'),
          onclick: () => { building = building === p.id ? '' : p.id; render(); },
          onpointerenter: () => MapView.light(p.id), onpointerleave: () => MapView.light(null), onfocus: () => MapView.light(p.id), onblur: () => MapView.light(null) },
          MapView.thumb(p), h('b', null, String(n)));
      }));
  }
  function body(list, now) {
    if (!list.length) {
      const any = DB.projects.some(p => p.todos.some(t => isOpenTask(t, now)));
      return [h('p', { class: 'fv-empty at-empty' }, any ? 'No task fits.' : 'No open tasks in the city.'),
        any ? h('button', { class: 'btn btn-quiet btn-small', type: 'button', 'data-k': 'clear', onclick: () => { shift = ''; building = ''; words = ''; $('#atFind').value = ''; render(); } }, 'Show every task') : null].filter(Boolean);
    }
    const G = groupsFor(list, now), out = [];
    if (G.star) out.push(h('section', { class: 'at-star', 'aria-label': 'Starred' }, h('h3', { class: 'at-gh' }, iconEl('star', 12), 'Starred'),
      h('ul', { class: 'at-rows' }, row(G.star, { chip: 'full', proj: true }, now))));
    for (const d of G.days) out.push(h('section', { class: 'at-group', 'data-group': d.id },
      h('h3', { class: 'at-gh' + (d.id === 'late' ? ' late' : '') }, d.title, h('span', { class: 'n' }, String(d.rows.length))),
      h('ul', { class: 'at-rows' }, d.rows.map(x => row(x, { chip: d.id === 'today' || d.id === 'tomorrow' ? '' : 'day', proj: true }, now)))));
    if (G.buildings.length) {
      if (G.days.length || G.star) out.push(h('div', { class: 'at-sep', 'aria-hidden': 'true' }));
      out.push(h('h3', { class: 'at-gh at-nodate' }, 'No due date', h('span', { class: 'n' }, String(G.buildings.reduce((s, b) => s + b.rows.length, 0)))));
      const whole = !!building || !!words.trim();                 // one building picked, or words typed: everything shows
      for (const { p, rows } of G.buildings) {
        const all = whole || unfolded.has(p.id), shown = all ? rows : rows.slice(0, FIRST);
        out.push(h('section', { class: 'at-group at-bld', 'data-p': p.id },
          h('h3', { class: 'at-gh' }, h('span', { class: 'at-gt', 'aria-hidden': 'true' }, MapView.thumb(p)), h('span', { class: 'at-nm', dir: 'auto' }, p.name), h('span', { class: 'n' }, String(rows.length))),
          h('ul', { class: 'at-rows' }, shown.map(x => row(x, { chip: '', proj: false }, now))),
          rows.length > shown.length ? h('button', { class: 'at-more', type: 'button', 'data-k': 'more-' + p.id, onclick: () => { unfolded.add(p.id); render(); } }, 'Show all ' + rows.length) : null));
      }
    }
    return out;
  }
  /* A row: the square, the task (with its repeat sign), then its shift, its date and where it lives; the pin and Copy
     task while it is pointed at; and for a task with no shift, the three to tag it with one click. */
  function row({ p, t, due: on }, { chip, proj }, now) {
    const held = ticking.has(t.id), ms = msOf(p, t), d = dueInfo({ due: on }, now);
    const due = !d || !chip ? null : d.tone === 'late' ? h('span', { class: 'due late' }, '! ' + d.text)
      : h('span', { class: 'due ' + (d.tone || '') }, chip === 'full' ? dueWords(on, now) : weekdayOf(on) + ' ' + fmtDate(parseYmd(on)));
    const where = proj ? p.name + (ms ? ' · ' + ms.name : '') : ms ? ms.name : '';
    const meta = h('span', { class: 'at-meta' }, held ? null : Rounds.hatButton(p, t, 'at-round'), shift && shift !== 'none' ? null : shiftTag(t), due, where ? h('span', { class: 'at-where', dir: 'auto' }, where) : null);
    const li = h('li', { class: 'at-row' + (held ? ' ticked' : ''), 'data-id': t.id, 'data-p': p.id,
      onpointerenter: () => MapView.light(p.id), onpointerleave: () => MapView.light(null) });
    li.addEventListener('focusin', () => MapView.light(p.id));
    li.addEventListener('focusout', e => { if (!li.contains(e.relatedTarget)) MapView.light(null); });
    const kids = [
      h('input', { type: 'checkbox', class: 'cb', checked: held, 'data-k': 'cb-' + t.id, 'aria-label': 'Done: ' + t.text, onchange: e => tick(p, t, e.target.checked) }),
      h('span', { class: 'at-body' },
        h('button', { class: 'at-task', type: 'button', dir: 'auto', 'data-k': 'task-' + t.id, title: 'Open this task', onclick: () => openTask(p, t) },
          t.text, t.repeat ? h('span', { class: 'repeat-mark', title: 'Repeats: ' + repeatText(t.repeat), 'aria-label': 'Repeats: ' + repeatText(t.repeat), html: iconSvg('repeat', 12) }) : null),
        meta,
        !t.shift && !held ? h('span', { class: 'at-tagit', role: 'group', 'aria-label': 'Give it a shift' }, h('span', null, 'Shift:'),
          ...SHIFTS.map(([s, name]) => h('button', { class: 'shift-tag shift-' + s + ' at-tag', type: 'button', 'data-k': 'tag-' + t.id + '-' + s, title: SHIFT_HINTS[s],
            onclick: () => tag(p, t, s) }, name))) : null)];
    if (!held) kids.push(...markButtons(p, t, 'at-mark'),
      h('button', { class: 'icon-btn at-copy', type: 'button', 'aria-label': 'Copy this task for Claude', title: 'Copy this task for Claude', html: iconSvg('copy', 14), onclick: () => copyTask(p, t) }));
    li.append(...kids);
    return li;
  }
  function openTask(p, t) { Menu.closeDrawer(); FullView.openTask(p.id, t.id); }
  /* A tick plays as in the status card: the line stays struck through for a moment, then goes; a repeat moves on,
     with its toast. Its particles burst through tickTask, as for a tick anywhere. */
  function tick(p, t, checked) {
    clearTimeout(ticking.get(t.id)); ticking.delete(t.id);
    if (checked) {
      heldDue.set(t.id, t.due); heldMark.set(t.id, { star: p.star === t.id, pin: p.pin === t.id });
      const w = tickTask(p, t); if (t.repeat) { was.set(t.id, w); repeatToast(p, t, w); }
      ticking.set(t.id, setTimeout(() => { ticking.delete(t.id); heldDue.delete(t.id); heldMark.delete(t.id); was.delete(t.id); render(); }, reducedMotion() ? 0 : 750));
    } else { untickTask(p, t, was.get(t.id)); was.delete(t.id); heldDue.delete(t.id); heldMark.delete(t.id); }
    changed(p);
    if (FullView.isOpen()) FullView.render();
  }
  /* Sorting: a click on a shift tags the task, and the focus goes on to the next row still to sort. */
  function tag(p, t, s) {
    const rows = $$('#atList .at-row'), i = rows.findIndex(r => r.dataset.id === t.id);
    const next = rows.slice(i + 1).find(r => $('.at-tagit', r));
    setShift(p, t, s);                                           // redraws the list through the side bar's refresh
    if (FullView.isOpen()) FullView.render();
    const b = (next && $(`[data-k="${CSS.escape('task-' + next.dataset.id)}"]`, $('#atList'))) || $(`[data-k="${CSS.escape('task-' + t.id)}"]`, $('#atList'));
    if (b) b.focus({ preventScroll: true });
  }

  /* ---------- keys: the arrows move between rows, Enter opens one (a button's own), Space ticks it ---------- */
  function onKey(e) {
    const tasks = $$('#atList .at-task'), at = e.target.closest && e.target.closest('.at-task');
    if (e.key === 'ArrowDown' && (e.target.id === 'atFind' || e.target.id === 'allTasks') && tasks.length) { e.preventDefault(); e.stopPropagation(); tasks[0].focus(); return; }
    if (!at) return;
    const i = tasks.indexOf(at);
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault(); e.stopPropagation();       // the map's arrow keys would move it too
      const j = i + (e.key === 'ArrowDown' ? 1 : -1);
      if (j >= 0 && j < tasks.length) tasks[j].focus();
      else if (j < 0) $('#atFind').focus();
    } else if (e.key === ' ') {
      e.preventDefault(); e.stopPropagation();
      const li = at.closest('.at-row'), cb = li && $('.cb', li);
      if (cb && !cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change')); }
    }
  }

  function init() {
    $('#atBack').innerHTML = iconSvg('back', 18);
    $('#sbTaskIcon').innerHTML = iconSvg('task', 16);
    $('#sbTaskIcon').style.display = 'inline-flex';
    $('#atBack').addEventListener('click', () => close());
    $('#btnOpenAllTasks').addEventListener('click', () => open());
    const typed = debounce(() => render(), 120);
    $('#atFind').addEventListener('input', e => { words = e.target.value; typed(); });
    $('#allTasks').addEventListener('keydown', onKey);
    /* L opens and closes the list, unless you are typing or a dialog is open, as R does Reports. */
    window.addEventListener('keydown', e => {
      if (e.code !== 'KeyL' || e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
      const t = e.target;
      if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
      if (Confirm.isOpen() || Panel.isOpen()) return;
      e.preventDefault();
      toggle();
    });
  }
  return { init, open, close, toggle, isOpen, refresh, render, _state: () => ({ shift, building, words }), _groupsFor: groupsFor };   // the last two for the tests
})();
