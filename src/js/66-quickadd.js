/* The city-wide quick add (Tasks, Round 2, O2), rethought in Rethink the One-Line Add, Round 1 (0.1.56). Enter on the
   map or T anywhere but in a field opens one line over the map for a task in any project. /name picks the project;
   without one it goes to the project open in the view, else the selected building, else the line starts with the
   project last added to. The other marks work as in every add field: !fri, #weekly, @name, +create.
   - Every mark suggests as it is typed (P1, P2, I1): / the projects, @ the line's milestones, ! dates, # repeats and
     + shifts, in a list under the line. Up and Down move, Tab or a click picks, Enter adds with the pick, Esc closes
     the list first. Only this line suggests (W1); the other add fields stay as they were.
   - Each kind of mark shows in its own color as typed, a shift in its own (I1, chips: no, colors instead).
   - The three shift tags sit under the line, the picked one pressed (S1).
   - The line's building lights with the hover ring on the map (I1).
   - Shift+Enter adds and stays open on the same project; Ctrl+Enter adds and opens the task (I1).
   - The toast is the building's leader's: "Task added: <task>.", with Open and Undo, which takes the task back out
     and reopens the line with what was typed (I1, and the chat on 23 October 2026).
   On a phone (0.1.76, The City on a Phone, Round 2), where marks are hard to type: + Task in the menu opens it (A2), four
   mark keys under it write a mark and open its list (A1, on a touch screen only, A1a), and the date list ends with
   Pick a date, the phone's own calendar (A4). */
const QuickAdd = (() => {
  let box = null, input = null, paint = null, list = null, keys = null, shifts = null, hint = null, prevFocus = null;
  let sug = null, lit = null, bare = -1;                     // bare: where a mark key wrote its sign, while nothing follows it
  const thumbs = new Map();                                  // a project's picture, drawn once each time the line opens
  const target = () => getProject((FullView.isOpen() && FullView.currentId()) || App.selectedId);
  const opts = () => ({ project: target(), cityWide: true });
  const markWord = name => String(name).trim().replace(/\s+/g, '-');
  const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const KIND = { '/': 'project', '@': 'ms', '!': 'date', '#': 'repeat', '+': 'shift' };
  const MARK_KEYS = [['/', 'Project'], ['@', 'Milestone'], ['!', 'Date'], ['#', 'Repeat']];

  /* ---------- which projects come first ---------- */
  /* When a project last had a task added to it, from its Activity. */
  function addedAt(p) {
    const a = Array.isArray(p.activity) ? p.activity : [];
    for (let i = a.length - 1; i >= 0; i--) if (String(a[i].text).startsWith('Added todo: ')) return a[i].at || 0;
    return 0;
  }
  /* The projects added to most recently first, then the rest by name (I1, recent). */
  const byRecent = () => DB.projects.map(p => [p, addedAt(p)]).sort((a, b) => b[1] - a[1] || a[0].name.localeCompare(b[0].name)).map(x => x[0]);
  const lastProject = () => { const p = byRecent()[0]; return p && addedAt(p) ? p : null; };

  /* How well a name fits what is typed after a mark: 0 it is the name, 1 the name starts with it, 2 a word of the
     name does, 3 its letters come in that order (I1, letters in order: /gp finds Garden planner); -1 none. */
  function rankOf(name, typed) {
    const key = markKey(typed), n = markKey(name);
    if (!key) return 0;
    if (n === key) return 0;
    if (n.startsWith(key)) return 1;
    if (n.split(' ').some(w => w.startsWith(key))) return 2;
    const a = n.replace(/\s/g, ''), b = key.replace(/\s/g, '');
    let j = 0;
    for (let i = 0; i < a.length && j < b.length; i++) if (a[i] === b[j]) j++;
    return j === b.length ? 3 : -1;
  }
  const ranked = (list, name, typed) => list.map((x, i) => [x, rankOf(name(x), typed), i]).filter(x => x[1] >= 0).sort((a, b) => a[1] - b[1] || a[2] - b[2]).map(x => x[0]);

  /* ---------- the suggestions for the mark at the caret ---------- */
  function tokenAt(v, caret) {
    let s = caret; while (s > 0 && !/\s/.test(v[s - 1])) s--;
    let e = caret; while (e < v.length && !/\s/.test(v[e])) e++;
    return { s, e, word: v.slice(s, e), typed: v.slice(s, caret) };
  }
  const dateNote = at => weekdayOf(ymd(at)) + ' ' + fmtDate(at);
  function itemsFor(mark, q, tok) {
    const low = q.toLowerCase(), now = Date.now(), today = startOfDay(now);
    if (mark === '/') {
      return ranked(byRecent(), p => p.name, q).map(p => ({ label: p.name, mark: '/' + markWord(p.name), note: plural(openTasks(p).length, 'open task', 'open tasks'), pid: p.id }));
    }
    if (mark === '@') {
      const r = readTaskLine(input.value, opts()), p = r.p;
      if (!p) return [{ info: 'Pick a project with / first' }];
      const first = defaultMilestone(p), live = liveMilestones(p), gone = p.milestones.filter(m => !live.includes(m));
      const order = [...live.filter(m => m.id === first), ...live.filter(m => m.id !== first), ...gone];
      const out = ranked(order, m => m.name, q).map(m => {
        const archived = gone.includes(m), open = p.todos.filter(t => t.milestoneId === m.id && isOpenTask(t)).length;
        return { label: m.name, mark: '@' + markWord(m.name), note: archived ? 'In the archive' : plural(open, 'open task', 'open tasks'), archived };
      });
      if (q && !out.some(x => markKey(x.label) === markKey(q))) out.push({ label: 'New milestone ' + q, mark: '@' + q, note: 'Made when you add', fresh: true });
      if (!out.length) return [{ info: 'Type a name for a new milestone' }];
      return out;
    }
    if (mark === '!') {
      const days = [{ w: 'today', label: 'Today', at: today }, { w: 'tomorrow', label: 'Tomorrow', at: plusDays(today, 1) }];
      for (let i = 2; i < 7; i++) { const at = plusDays(today, i), d = new Date(at).getDay(); days.push({ w: WEEKDAYS[d].toLowerCase(), label: DAY_NAMES[d], at }); }
      const fits = d => { const wd = DAY_NAMES[new Date(d.at).getDay()].toLowerCase(); return !low || d.w.startsWith(low) || d.label.toLowerCase().startsWith(low) || wd.startsWith(low); };
      const out = days.filter(fits)
        .map(d => ({ label: d.label, mark: '!' + d.w, note: dateNote(d.at) }));
      const typed = low && readDateMark(q, null, now);
      if (typed && typed.used === 1 && !days.some(d => d.at === typed.at && fits(d)))
        out.unshift({ label: dateNote(typed.at), mark: '!' + q, note: '' });
      if (touchScreen()) out.push({ label: 'Pick a date', note: 'The calendar', pickDate: true });   // A4
      return out;
    }
    if (mark === '#') {
      const reps = [['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly'], ['yearly', 'Yearly'], ['every', 'Every N days']];
      return reps.filter(([w, label]) => !low || w.startsWith(low) || label.toLowerCase().startsWith(low)).map(([w, label]) => {
        if (w === 'every') return { label, mark: '#every', note: 'Then type the number of days' };
        const v = input.value, line = v.slice(0, tok.s) + '#' + w + v.slice(tok.e), r = readTaskMarks(line, { now, cityWide: true });
        const when = !r.due || r.due === ymd(today) ? 'today' : dateNote(parseYmd(r.due));
        const on = r.repeat && r.repeat.every === 'week' ? 'On ' + repeatText(r.repeat).slice(10) + ', s'
          : r.repeat && r.repeat.every === 'month' ? 'On the ' + ordinal(r.repeat.day) + ', s'
          : r.repeat && r.repeat.every === 'year' ? 'On ' + r.repeat.day + ' ' + MONTHS[r.repeat.month - 1] + ', s' : 'S';
        return { label, mark: '#' + w, note: on + 'tarts ' + when };
      });
    }
    if (mark === '+') {
      if (q && !/^\p{L}/u.test(q)) return [];
      return SHIFTS.filter(([id]) => id.startsWith(low)).map(([id, name]) => ({ label: name, mark: '+' + id, note: SHIFT_HINTS[id] || '', shift: id }));
    }
    return [];
  }
  const selectable = () => (sug ? sug.items.filter(x => !x.info) : []);
  const current = () => (sug && sug.index >= 0 ? selectable()[sug.index] || null : null);

  /* Opens, keeps or closes the list for the mark the caret is in. */
  function refreshList() {
    const v = input.value, caret = input.selectionStart == null ? v.length : input.selectionStart;
    const tok = tokenAt(v, caret), mark = tok.word[0];
    const on = document.activeElement === input && caret > tok.s && KIND[mark] && input.selectionStart === input.selectionEnd;
    if (!on) return closeList();
    const q = tok.typed.slice(1), items = itemsFor(mark, q, tok);
    if (!items.length) return closeList();
    const same = sug && sug.mark === mark && sug.s === tok.s && sug.q === q;
    const keep = same ? sug.index : -1;
    sug = { mark, s: tok.s, e: tok.e, q, items, index: same ? keep : q ? 0 : -1 };
    if (sug.index >= selectable().length) sug.index = selectable().length - 1;
    drawList();
  }
  function drawList() {
    let k = -1;
    list.replaceChildren(...sug.items.map(it => {
      if (it.info) return h('li', { class: 'qa-opt info', role: 'presentation' }, it.info);
      k++;
      const i = k, on = i === sug.index;
      let lead;
      if (sug.mark === '/') {
        if (!thumbs.has(it.pid)) thumbs.set(it.pid, MapView.thumb(getProject(it.pid)));
        lead = h('span', { class: 'qa-thumb', 'aria-hidden': 'true' }, cloneThumb(thumbs.get(it.pid)));
      } else if (sug.mark === '+') lead = h('span', { class: 'shift-tag shift-' + it.shift, 'aria-hidden': 'true' }, it.label);
      else lead = h('span', { class: 'qa-glyph qa-m-' + KIND[sug.mark], 'aria-hidden': 'true' }, it.archived ? iconEl('archive', 13) : sug.mark);
      /* Pick a date (A4): the phone's own date field lies over the row, unseen, so a tap opens its calendar. */
      if (it.pickDate) {
        const s = sug.s, e = sug.e;
        it.cal = h('input', { type: 'date', class: 'qa-date', min: ymd(), tabindex: '-1', 'aria-label': 'Pick a date',
          onmousedown: ev => ev.stopPropagation(), onclick: ev => ev.stopPropagation(),       // its own tap opens its calendar
          onchange: () => { const at = parseYmd(it.cal.value); if (at != null) writeOver(s, e, dateMark(at)); } });
      }
      return h('li', { id: 'qaOpt' + i, class: 'qa-opt' + (on ? ' on' : '') + (it.archived ? ' archived' : '') + (it.fresh ? ' fresh' : '') + (it.pickDate ? ' pick-date' : ''), role: 'option', 'aria-selected': String(on),
        'data-mark': it.mark || null, onmousedown: e => e.preventDefault(), onclick: () => { pick(it); } },
        lead, sug.mark === '+' ? null : h('span', { class: 'qa-label', dir: 'auto' }, it.label), it.note ? h('span', { class: 'qa-note' }, it.note) : null, it.cal || null);
    }));
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    if (sug.index >= 0) input.setAttribute('aria-activedescendant', 'qaOpt' + sug.index); else input.removeAttribute('aria-activedescendant');
    const el = sug.index >= 0 && $('#qaOpt' + sug.index, list);
    if (el) el.scrollIntoView({ block: 'nearest' });
    lightUp();
  }
  function cloneThumb(src) {
    const c = document.createElement('canvas');
    c.width = src.width; c.height = src.height;
    c.getContext('2d').drawImage(src, 0, 0);
    return c;
  }
  function closeList() {
    if (!list) return;
    dropBare();
    sug = null;
    list.hidden = true; list.replaceChildren();
    if (input) { input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); }
    lightUp();
  }
  function move(d) {
    const n = selectable().length;
    if (!n) return;
    sug.index = sug.index < 0 ? (d > 0 ? 0 : n - 1) : Math.max(0, Math.min(n - 1, sug.index + d));
    drawList();
  }
  /* Writes the pick over the mark being typed, with one space after it. */
  function pick(it) {
    if (!it || it.info || !sug) return;
    if (it.pickDate) { try { it.cal.showPicker(); } catch (e) { it.cal.focus(); } return; }   // Enter on Pick a date
    writeOver(sug.s, sug.e, it.mark);
  }
  function writeOver(s, e, mark) {
    const v = input.value, before = v.slice(0, s), after = v.slice(e).replace(/^\s/, '');
    const ins = mark + ' ';
    input.value = before + ins + after;
    bare = -1;
    const at = before.length + ins.length;
    input.focus();
    input.setSelectionRange(at, at);
    closeList();
    sync(false);
  }
  /* A day from the calendar as a date mark: !nov 20, or !2027-11-20 when the month and day would read as another year. */
  function dateMark(at) {
    const d = new Date(at), short = MONTHS[d.getMonth()].toLowerCase() + ' ' + d.getDate(), r = readDateMark(MONTHS[d.getMonth()], String(d.getDate()));
    return '!' + (r && r.at === at ? short : ymd(at));
  }

  /* ---------- the mark keys, on a phone (A1) ----------
     A key writes its sign at the end of the line and opens its list, as typing the sign does; a pick writes the whole
     mark. With that kind of mark in the line already, it opens the list over it, every choice in it and the one there
     lit, so a pick writes over it. A sign a key wrote goes again when its list closes with nothing picked or typed. */
  function keyMark(sign) {
    closeList();
    const v = input.value, r = readTaskMarks(v, { cityWide: true });
    const sp = (r.spans || []).filter(x => x.kind === sign).pop();
    input.focus();
    if (sp) {
      input.setSelectionRange(sp.end, sp.end);
      const word = v.slice(sp.start, sp.end), items = itemsFor(sign, '', { s: sp.start, e: sp.end });
      if (!items.length) return;
      const at = items.filter(x => !x.info).findIndex(x => x.mark && markKey(x.mark) === markKey(word));
      sug = { mark: sign, s: sp.start, e: sp.end, q: word.slice(1), items, index: at };
      drawList();
      return;
    }
    const base = v.replace(/\s+$/, ''), nv = (base ? base + ' ' : '') + sign;
    input.value = nv;
    bare = nv.length - 1;
    input.setSelectionRange(nv.length, nv.length);
    sync();
  }
  function dropBare() {
    if (bare < 0 || !input) return;
    const v = input.value, at = bare;
    bare = -1;
    if (!KIND[v[at]] || (at > 0 && !/\s/.test(v[at - 1])) || (at + 1 < v.length && !/\s/.test(v[at + 1]))) return;
    const caret = input.selectionStart, nv = (v.slice(0, at).replace(/\s+$/, '') + ' ' + v.slice(at + 1).replace(/^\s+/, '')).replace(/^\s+/, '');
    input.value = nv.trim() ? nv : '';
    const c = Math.min(caret > at ? caret - (v.length - input.value.length) : caret, input.value.length);
    if (document.activeElement === input) input.setSelectionRange(c, c);
    sync(false);
  }

  /* ---------- the line: its colors, its shift tags, its building ---------- */
  function paintMarks(r) {
    const v = input.value, out = [];
    let pos = 0;
    for (const sp of r.spans || []) {
      if (sp.start > pos) out.push(v.slice(pos, sp.start));
      out.push(h('span', { class: 'qa-m qa-m-' + KIND[sp.kind] + (sp.shift ? ' shift-' + sp.shift : '') }, v.slice(sp.start, sp.end)));
      pos = sp.end;
    }
    out.push(v.slice(pos) + ' ');
    paint.replaceChildren(...out);
    paint.scrollLeft = input.scrollLeft;
  }
  function lightUp() {
    if (!input || !box || !box.isConnected) return;
    const it = sug && sug.mark === '/' && current();
    const r = readTaskLine(input.value, opts()), id = it ? it.pid : r.p ? r.p.id : null;
    if (id !== lit) { lit = id; MapView.light(id); }
  }
  function sync(list = true) {
    const r = taskLineHint(hint, input.value, opts());
    if (r.problem === 'Type the task too' && (r.spans || []).every(sp => sp.kind === '/')) {   // just the project so far: no alarm yet
      hint.classList.remove('bad'); hint.textContent = r.parts.join(' · ');
    }
    paintMarks(r);
    for (const b of shifts.querySelectorAll('.qa-shift')) b.setAttribute('aria-pressed', String(b.dataset.shift === r.shift));
    if (list) refreshList(); else lightUp();
    return r;
  }
  /* A click on a shift tag: picks it, or takes it off when it is the one picked, as a +mark in the line. */
  function toggleShift(id) {
    let v = input.value;
    const r = readTaskMarks(v, { cityWide: true }), marks = (r.spans || []).filter(sp => sp.kind === '+');
    if (r.shift === id) {
      for (const sp of marks.slice().reverse()) v = (v.slice(0, sp.start).replace(/\s+$/, '') + ' ' + v.slice(sp.end).replace(/^\s+/, '')).replace(/^\s+/, '');
      v = v.replace(/\s+$/, '') + (v.trim() ? ' ' : '');
    } else if (marks.length) {
      const sp = marks[marks.length - 1];
      v = v.slice(0, sp.start) + '+' + id + v.slice(sp.end);
    } else v = (v.trim() ? v.replace(/\s+$/, '') + ' ' : '') + '+' + id + ' ';
    input.value = v;
    input.focus();
    input.setSelectionRange(v.length, v.length);
    closeList();
    sync(false);
  }

  /* ---------- adding, and the leader's toast ---------- */
  function add({ stay = false, open = false } = {}) {
    dropBare();
    const r = taskLineHint(hint, input.value, opts());
    if (!r.ok) { if (!input.value.trim()) close(); return; }
    const text = input.value, p = r.p, had = new Set(p.milestones.map(m => m.id)), was = p.updatedAt;
    const t = addTaskLine(r);
    const info = { text, newMs: had.has(t.milestoneId) ? null : t.milestoneId, was };
    if (stay) {
      input.value = r.project ? '/' + markWord(p.name) + ' ' : '';
      input.setSelectionRange(input.value.length, input.value.length);
      info.stayValue = input.value;
      sync();
    } else close();
    if (FullView.shows(p.id)) FullView.render();
    added(p, t, info);
    if (open) FullView.openTask(p.id, t.id);
  }
  function added(p, t, info) {
    const acts = [{ label: 'Open', run: () => FullView.openTask(p.id, t.id) }, { label: 'Undo', run: () => undo(p, t, info) }];
    const lead = Leaders.toastLead(p);
    if (!lead) return toast('Added to ' + p.name + ': ' + t.text + '.', '', acts);
    toast('Task added: ' + t.text + '.', '', acts, { lead });
  }
  /* Undo: the task back out, with its Activity line and a milestone made for it, and the line open again with what
     was typed, to edit and add again. */
  function undo(p, t, info) {
    if (FullView.isOpen()) FullView.closeTaskOf(t.id);
    const i = p.todos.findIndex(x => x.id === t.id);
    if (i >= 0) p.todos.splice(i, 1);
    const drop = text => { const a = p.activity || []; for (let k = a.length - 1; k >= 0; k--) if (a[k].text === text) { a.splice(k, 1); return; } };
    drop('Added todo: ' + t.text);
    if (info.newMs && !p.todos.some(x => x.milestoneId === info.newMs)) {
      const m = p.milestones.find(x => x.id === info.newMs);
      if (m) { p.milestones.splice(p.milestones.indexOf(m), 1); drop('New milestone: ' + m.name); }
    }
    if (p.pin === t.id) p.pin = '';
    if (p.star === t.id) p.star = '';
    changed(p, { touch: false });
    if (info.was) p.updatedAt = info.was;
    if (FullView.shows(p.id)) FullView.render();
    if (isOpen() && input.value.trim() && input.value !== info.stayValue) return;     // something new is being typed: leave it
    open({ text: info.text });
  }

  /* ---------- the box ---------- */
  function build() {
    input = h('input', { id: 'quickAddIn', class: 'field quick-add-in', type: 'text', dir: 'auto', autocomplete: 'off', spellcheck: 'false', maxlength: '700',
      placeholder: touchScreen() ? 'A task' : 'A task, with /project !date #repeat @milestone +shift', 'aria-label': 'Add a task', 'aria-describedby': 'quickAddHint',
      role: 'combobox', 'aria-autocomplete': 'list', 'aria-controls': 'qaList', 'aria-expanded': 'false',
      oninput: () => { bare = -1; sync(); },
      onclick: () => refreshList(),
      onscroll: () => { paint.scrollLeft = input.scrollLeft; },
      onkeyup: e => { if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) refreshList(); paint.scrollLeft = input.scrollLeft; },
      onkeydown: e => {
        if (sug && !list.hidden) {
          if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); move(e.key === 'ArrowDown' ? 1 : -1); return; }
          if (e.key === 'Tab' && !e.shiftKey && selectable().length) { e.preventDefault(); pick(current() || selectable()[0]); return; }
          if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeList(); return; }
          if (e.key === 'Enter' && current()) pick(current());        // Enter adds with the pick (P1)
        }
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); return; }
        if (e.key !== 'Enter' || e.isComposing) return;
        e.preventDefault();
        add({ stay: e.shiftKey, open: e.ctrlKey || e.metaKey });
      },
      onblur: () => setTimeout(() => { if (box && !box.contains(document.activeElement)) close(false); }, 120) });
    paint = h('div', { class: 'qa-paint', dir: 'auto', 'aria-hidden': 'true' });
    list = h('ul', { id: 'qaList', class: 'qa-list', role: 'listbox', 'aria-label': 'Suggestions', hidden: '' });
    shifts = h('div', { class: 'qa-shifts', role: 'group', 'aria-label': 'Shift' }, h('span', { class: 'qa-shifts-lbl' }, 'Shift'),
      ...SHIFTS.map(([id, name]) => h('button', { type: 'button', class: 'qa-shift shift-' + id, 'data-shift': id, 'aria-pressed': 'false', title: name + ': ' + (SHIFT_HINTS[id] || ''),
        onmousedown: e => e.preventDefault(), onclick: () => toggleShift(id) }, name)));
    keys = h('div', { class: 'qa-keys', role: 'group', 'aria-label': 'Marks' },
      ...MARK_KEYS.map(([sign, name]) => h('button', { type: 'button', class: 'qa-key qa-m-' + KIND[sign], 'data-sign': sign, title: name + ': writes ' + sign,
        onmousedown: e => e.preventDefault(), onclick: () => keyMark(sign) }, name)));
    hint = h('p', { id: 'quickAddHint', class: 'add-hint quick-add-hint', 'aria-live': 'polite' });
    box = h('div', { id: 'quickAdd', class: 'quick-add', role: 'dialog', 'aria-label': 'Add a task' },
      h('div', { class: 'quick-add-head' }, h('span', { class: 'quick-add-title' }, iconEl('plus', 12), 'Add a task'),
        h('span', { class: 'quick-add-keys' }, 'Enter adds · Shift+Enter adds and stays · Ctrl+Enter adds and opens')),
      h('div', { class: 'qa-top' }, h('div', { class: 'qa-field' }, input, paint), keys, list), shifts, hint);   // the list opens under the keys, so they stay in reach
  }
  /* Opens the line; `text` fills it in (Undo). With no project open or selected, it starts on the project last added
     to (I1, remember the last project). */
  function open({ text = null } = {}) {
    if (!box) build();
    if (!box.isConnected) { prevFocus = document.activeElement; $('#mapWrap').append(box); thumbs.clear(); }
    if (typeof Wheel !== 'undefined') Wheel.close();
    let v = text != null ? text : '';
    if (text == null && !target()) { const lp = lastProject(); if (lp) v = '/' + markWord(lp.name) + ' '; }
    input.value = v;
    closeList();
    input.focus();
    input.setSelectionRange(v.length, v.length);
    sync(false);
  }
  function close(refocus = true) {
    if (!box || !box.isConnected) return false;
    closeList();
    box.remove();
    if (lit !== null) { lit = null; MapView.light(null); }
    if (refocus && prevFocus && document.contains(prevFocus) && prevFocus.focus) prevFocus.focus({ preventScroll: true });
    prevFocus = null;
    return true;
  }
  const isOpen = () => !!box && box.isConnected;
  /* A phone's back (0.1.75, G2), as Esc: the list first, then the line. */
  function back() {
    if (sug && list && !list.hidden) { closeList(); return true; }
    return close();
  }
  window.addEventListener('keydown', e => {
    if (e.code !== 'KeyT' || e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
    const t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (Confirm.isOpen() || Panel.isOpen()) return;
    e.preventDefault();
    open();
  });
  return { open, close, isOpen, back, rankOf, lastProject, byRecent,
    _list: () => (sug ? { mark: sug.mark, index: sug.index, items: sug.items.map(x => ({ ...x })) } : null) };   // for the tests
})();
