/* Local paths: a Windows drive path, a network share, or a file:// address, read as one Windows path. */
function winPathOf(u) {
  const s = String(u || '').trim();
  let m;
  try {
    if (/^[A-Za-z]:[\\/]/.test(s)) return s.replace(/\//g, '\\');
    if (/^\\\\[^\\]+\\[^\\]+/.test(s)) return s;
    if ((m = s.match(/^file:\/\/\/([A-Za-z]:\/.*)$/i))) return decodeURIComponent(m[1]).replace(/\//g, '\\');
    if ((m = s.match(/^file:\/\/([^/]+)\/(.+)$/i)) && m[1].toLowerCase() !== 'localhost') return '\\\\' + m[1] + '\\' + decodeURIComponent(m[2]).replace(/\//g, '\\');
  } catch (e) { return null; }
  return null;
}
function fileUrlOf(win) {
  if (win.startsWith('\\\\')) return 'file://' + win.slice(2).split('\\').map(encodeURIComponent).join('/');
  return 'file:///' + win.split('\\').map((seg, i) => i === 0 ? seg : encodeURIComponent(seg)).join('/');
}
/* With the one-time Windows setup, this link type opens File Explorer. */
const explorerHref = win => 'nullovation-folder:' + encodeURIComponent(win);
const EXPLORER_KEY = 'nullovation-city:explorerLinks';
const explorerLinks = () => { try { return localStorage.getItem(EXPLORER_KEY) === '1'; } catch (e) { return false; } };
function safeUrl(u) {
  const s = String(u || '').trim();
  if (!s) return null;
  const w = winPathOf(s);
  if (w) return fileUrlOf(w);
  if (/^(javascript|data|vbscript):/i.test(s)) return null;
  if (/^[a-z][a-z0-9+.-]*:/i.test(s)) return s;             // https:, file:, slack:, mailto:, notion: ...
  if (/^[\w-]+(\.[\w-]+)+([/?#].*)?$/.test(s)) return 'https://' + s;
  return null;
}
function paragraphs(text) {
  return text.split(/\n{2,}/).filter(s => s.trim()).map(par => {
    const p = h('p', { dir: 'auto' });
    par.split('\n').forEach((line, i) => { if (i) p.append(h('br')); p.append(line); });
    return p;
  });
}
/* Where a link goes when clicked, the same in the project view and on the shortcut wheel: a folder or file on this
   PC opens in File Explorer with the setup, or else in the browser; anything else in a new tab. href is null when
   the address cannot be opened. A link without a label shows the name its address suggests. */
function linkTarget(l) {
  const win = winPathOf(l.url);
  if (win) {
    const inExplorer = explorerLinks();
    return { win, href: inExplorer ? explorerHref(win) : fileUrlOf(win), blank: !inExplorer, name: l.label || suggestLabel(win) || win,
      title: (inExplorer ? 'Opens in File Explorer: ' : 'Opens in the browser: ') + win };
  }
  const url = safeUrl(l.url);
  return { win: null, href: url, blank: true, name: l.label || suggestLabel(l.url) || l.url || 'Link', title: url || 'This address cannot be opened. Fix it with the pencil.' };
}
function dataUrlToBlob(url) {
  const [head, b64] = url.split(',');
  const mime = (head.match(/^data:([^;]+)/) || [])[1] || 'application/octet-stream';
  const bin = atob(b64), bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}

/* The Project view: a panel docked on the left of the map. Each section edits on its own. */
const FullView = (() => {
  let root = null, side = null, sideMode = null, menu = null, pop = null;
  let openId = null, lastFocus = null, allNotes = false;
  let editing = null;            // the one section open for editing: { key, snap }
  const P = () => getProject(openId);
  const clone = x => JSON.parse(JSON.stringify(x));
  const SECTION_NAMES = { name: 'the name', about: 'About', todos: 'Todos', notes: 'Notes', links: 'Links' };
  const SNAP = {
    name: p => ({ name: p.name }),
    about: p => ({ description: p.description, deadline: p.deadline, progressOverride: p.progressOverride }),
    todos: p => ({ todos: clone(p.todos), milestones: clone(p.milestones) }),
    notes: p => ({ notes: clone(p.notes) }),
    links: p => ({ links: clone(p.links) }),
  };

  /* ---------- open, close, Esc ---------- */
  function open(id, { section = null } = {}) {
    if (!getProject(id)) return;
    if (root && openId !== id) { finishEdit(); closeMenu(); closeSide(); adding = null; }
    if (!root) {
      lastFocus = document.activeElement;
      root = h('aside', { id: 'pv', class: 'pv', role: 'region', 'aria-label': 'Project', tabindex: '-1' });
      $('#mapWrap').append(root);
    }
    const switching = openId !== id;
    openId = id;
    if (switching) { allNotes = false; editing = null; adding = null; closeMenu(); closeSide(); }
    render();
    if (switching) root.scrollTop = 0;
    if (App.selectedId !== id) MapView.select(id, { glide: false });
    Bubble.position();
    MapView.glideBeside(id, rightEdge());
    if (section) startEdit(section);
    else root.focus({ preventScroll: true });
  }
  function close() {
    if (!root) return;
    finishEdit();
    persistSoon.flush();
    closePopover(); closeMenu(); closeSide(); OpenInClaude.close();
    root.remove(); root = null; openId = null; editing = null;
    Bubble.refresh(); Bubble.position();
    MapView.invalidate();
    const enter = $('#enterBtn');
    if (enter && !enter.hidden && enter.offsetParent) enter.focus();
    else if (lastFocus && document.contains(lastFocus) && lastFocus.focus) lastFocus.focus();
  }
  /* Esc peels one layer at a time: a popover, the more menu, an open section (undone), the side panel, the view. */
  function escape() {
    if (!root) return false;
    if (pop) { closePopover(); return true; }
    if (menu) { closeMenu(); return true; }
    if (adding) { closeAdd(); return true; }
    if (editing) { cancelEdit(); return true; }
    if (side && sideMode === 'note') { cancelNote(); return true; }
    if (side && sideMode === 'task') { if (backToArchive()) return true; cancelTask(); return true; }
    if (side && sideMode === 'milestone') { cancelMilestone(); return true; }
    if (side) { closeSide(); root.focus({ preventScroll: true }); return true; }
    close();
    return true;
  }
  const rightEdge = () => {
    const wrap = $('#mapWrap').getBoundingClientRect();
    const last = side || root;
    return last ? last.getBoundingClientRect().right - wrap.left : 0;
  };

  /* ---------- editing, one section at a time ---------- */
  function startEdit(key) {
    const p = P(); if (!p || !SNAP[key]) return;
    if (editing && editing.key === key) return;
    finishEdit();
    editing = { key, snap: SNAP[key](p) };
    render();
    const first = key === 'name' ? $('#pvName', root)
      : $(`[data-sec="${key}"] .pv-ed .field, [data-sec="${key}"] .todos-edit .field, [data-sec="${key}"] .notes.edit textarea, [data-sec="${key}"] .link-edit .field`, root);
    if (first) { first.focus(); if (first.select && key === 'name') first.select(); }
  }
  /* Done: keep what was typed, and log what changed. */
  function finishEdit() {
    const p = P();
    if (!editing || !p) { editing = null; return; }
    const { key, snap } = editing;
    editing = null;
    if (key === 'name') {
      if (!p.name.trim()) p.name = 'Untitled project';
      if (p.name !== snap.name) { logActivity(p, 'Renamed to ' + p.name); changed(p); }
    } else if (key === 'about') {
      if (p.description !== snap.description) logActivity(p, 'Edited About');
      if (p.deadline !== snap.deadline) logActivity(p, p.deadline ? 'Deadline set to ' + fmtDate(parseYmd(p.deadline)) : 'Deadline cleared');
      if (p.progressOverride !== snap.progressOverride) logActivity(p, p.progressOverride == null ? 'Progress back to automatic' : 'Progress set to ' + p.progressOverride + '%');
    } else if (key === 'todos') {
      const was = new Map(snap.todos.map(t => [t.id, t]));
      const now = new Set(p.todos.map(t => t.id));
      for (const t of p.todos) {
        const o = was.get(t.id);
        if (!o) logActivity(p, 'Added todo: ' + t.text);
        else if (o.done !== t.done) logActivity(p, (t.done ? 'Done: ' : 'Reopened: ') + t.text);
      }
      for (const o of snap.todos) if (!now.has(o.id)) logActivity(p, 'Removed todo: ' + o.text);
      const msWas = new Set(snap.milestones.map(m => m.id)), msNow = new Set(p.milestones.map(m => m.id));
      for (const m of p.milestones) if (!msWas.has(m.id)) logActivity(p, 'New milestone: ' + m.name);
      for (const m of snap.milestones) if (!msNow.has(m.id)) logActivity(p, 'Removed milestone: ' + m.name);
    } else if (key === 'notes') {
      const was = new Map(snap.notes.map(n => [n.id, n])), now = new Set(p.notes.map(n => n.id));
      for (const n of p.notes) if (was.has(n.id) && was.get(n.id).text !== n.text) logActivity(p, 'Edited a note');
      for (const n of snap.notes) if (!now.has(n.id)) logActivity(p, 'Deleted a note');
    } else if (key === 'links') {
      const was = new Map(snap.links.map(l => [l.id, l])), now = new Set(p.links.map(l => l.id));
      for (const l of p.links) if (!was.has(l.id) && l.url.trim()) logActivity(p, 'Added link: ' + (l.label || l.url));
      for (const l of snap.links) if (!now.has(l.id)) logActivity(p, 'Removed link: ' + (l.label || l.url));
      p.links = p.links.filter(l => l.url.trim() || l.label.trim());
    }
    changed(p, { touch: false });
  }
  function doneEdit() {
    const key = editing && editing.key;
    finishEdit(); render();
    const b = $(`[data-sec="${key}"] .pv-pencil`, root); if (b) b.focus();
  }
  /* Esc: put everything back as it was when the section opened. */
  function cancelEdit() {
    const p = P(); if (!p || !editing) return;
    const { key, snap } = editing;
    editing = null;
    Object.assign(p, clone(snap));
    changed(p, { touch: false });
    render();
    toast('Changes to ' + SECTION_NAMES[key] + ' undone.');
    const b = $(`[data-sec="${key}"] .pv-pencil`, root); if (b) b.focus();
  }
  const pencil = (key, label) => h('button', { class: 'icon-btn pv-pencil', type: 'button', 'aria-label': 'Edit ' + label, title: 'Edit ' + label, html: iconSvg('pencil', 14), onclick: () => startEdit(key) });
  const doneBtn = () => h('button', { class: 'btn btn-accent btn-small pv-done', type: 'button', onclick: doneEdit }, 'Done');

  /* ---------- render ---------- */
  let adding = null;             // which quick add is open: 'todo', 'link', or 'next'; nothing is open until asked for
  function render() {
    const p = P(); if (!p) { close(); return; }
    closePopover();
    const top = root.scrollTop;
    root.replaceChildren(topBar(p),
      h('div', { class: 'pv-hero' }, heroPicture(p), about(p)),
      h('div', { class: 'pv-cols' }, h('div', { class: 'pv-col' }, todos(p)), h('div', { class: 'pv-col' }, links(p), notes(p))));   // links first: the app runs on them (0.1.54)
    root.scrollTop = top;
    const inp = adding && $('[data-adding] .field', root); if (inp) inp.focus();
    if (side) renderSide();
  }
  const addBtn = (label, id, fn) => h('button', { id, class: 'btn btn-quiet btn-small pv-add-btn', type: 'button', onclick: fn }, iconEl('plus', 14), label);
  function openAdd(kind) { finishEdit(); adding = kind; render(); }
  function closeAdd() { adding = null; render(); }

  function topBar(p) {
    const edName = editing && editing.key === 'name';
    const title = edName
      ? h('input', { id: 'pvName', class: 'field pv-name-in', type: 'text', dir: 'auto', maxlength: '120', value: p.name, autocomplete: 'off', 'aria-label': 'Project name',
          oninput: e => { p.name = e.target.value; changed(p); },
          onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); doneEdit(); } } })
      : h('h2', { id: 'pvTitle', class: 'pv-title', dir: 'auto' }, p.name);
    const more = h('button', { id: 'pvMore', class: 'icon-btn', type: 'button', 'aria-label': 'More', title: 'More', 'aria-haspopup': 'menu', 'aria-expanded': 'false', html: iconSvg('more', 18) });
    more.addEventListener('click', e => { e.stopPropagation(); menu ? closeMenu() : openMenu(more); });
    return h('div', { class: 'pv-top', 'data-sec': 'name' },
      h('div', { class: 'pv-name' }, title, edName ? doneBtn() : pencil('name', 'the name')),
      h('div', { class: 'pv-actions' }, more,
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close project view', title: 'Close', html: iconSvg('close', 18), onclick: close })));
  }

  /* The building, like a profile picture: click it to change the building. The profile line and
     the mirror and download icons sit under it. */
  function heroPicture(p) {
    const gen = p.generic ? GENERICS.find(g => g.id === p.generic) : null;
    const which = p.art.has ? 'your own art' : gen ? 'the ' + gen.name.toLowerCase() : 'a placeholder';
    const done = p.todos.filter(t => t.done).length;
    return h('div', { class: 'pv-hero-pic' },
      h('button', { class: 'pv-scene', type: 'button', 'aria-label': 'Building: ' + which + '. Change it', title: 'Change the building', onclick: () => openSide('building') },
        MapView.profileScene(p, 440, 280), h('span', { class: 'pv-scene-hint' }, 'Change building')),
      h('div', { class: 'pv-under' },
        h('p', { class: 'pv-stats' }, 'Founded ' + fmtDate(p.createdAt) + ' \u00b7 ' + plural(done, 'todo', 'todos') + ' done \u00b7 Updated ' + relAgo(p.updatedAt)),
        h('div', { class: 'pv-scene-tools' },
          h('button', { class: 'icon-btn', type: 'button', 'aria-pressed': String(!!p.flip), 'aria-label': 'Mirror the building', title: p.flip ? 'Mirrored. Click to flip it back' : 'Mirror the building',
            html: iconSvg('flip', 16), onclick: () => { p.flip = !p.flip; MapView.dropCache(p.id); logActivity(p, p.flip ? 'Mirrored the building' : 'Unmirrored the building'); changed(p); render(); } }),
          h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Download the building', title: 'Download the building as a GIF', html: iconSvg('download', 16), onclick: () => downloadBuilding(p) }))),
      h('div', { class: 'pv-urgency-row' },
        h('button', { id: 'pvUrgencyBtn', class: 'pv-urgency-btn', type: 'button', title: 'Urgency: what raises bubbles over this building', onclick: () => openSide('urgency') },
          iconEl('alert', 16), h('span', null, urgencyName(p))),
        p.urgency.system !== 'none' ? h('button', { id: 'pvWorked', class: 'btn btn-small', type: 'button', title: 'Counts as finishing a task, for ' + urgencyName(p), onclick: () => workedNow(p) }, 'I worked!') : null),
      Leaders.card(p, () => openSide('leader')));                           // the leader card, beside the About (0.1.51)
  }
  function workedNow(p) {
    iWorked(p); changed(p); render(); Bubble.refresh();
    toast('Checked in. ' + (p.urgency.system === 'finish' ? 'Work until finished stays yellow for 24 hours.' : 'No bubble until ' + (p.urgency.days === 1 ? 'tomorrow at this time.' : p.urgency.days + ' days from now.')));
  }

  /* About: what the project is, then what is next (worked out from the todos), beside the picture */
  function about(p) {
    const ed = editing && editing.key === 'about';
    const box = h('section', { class: 'pv-sec pv-about', 'data-sec': 'about' }, secHead('About', 'about'));
    const leader = [...p.notes].sort((a, b) => b.at - a.at).find(n => /^\s*leader\b/i.test(n.title || '') || /^\s*leader\b/i.test(n.text));
    if (ed) {
      const desc = h('textarea', { id: 'pvDesc', class: 'field', dir: 'auto', rows: '6', placeholder: 'What this project is and anything worth keeping', 'aria-label': 'Description',
        oninput: e => { p.description = e.target.value; changed(p); } }, p.description);
      const due = h('input', { class: 'field', type: 'date', value: p.deadline, 'aria-label': 'Deadline', onchange: e => { p.deadline = parseYmd(e.target.value) != null ? e.target.value : ''; changed(p); } });
      const clear = h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => { p.deadline = ''; due.value = ''; changed(p); } }, 'Clear');
      box.append(h('div', { class: 'ed pv-ed' },
        h('div', null, h('span', { class: 'lbl' }, 'Description'), desc),
        h('div', null, h('span', { class: 'lbl' }, 'Deadline'), h('div', { class: 'inline' }, due, clear)),
        progressControls(p),
        h('p', { class: 'note' }, 'Changes save as you type. Done closes the section; Esc undoes everything since it opened.')));
      return box;
    }
    box.append(p.description.trim() ? h('div', { class: 'fv-desc' }, paragraphs(p.description)) : h('p', { class: 'fv-empty' }, 'No description yet. The pencil adds one.'));
    box.append(whatIsNext(p));
    const dl = deadlineInfo(p.deadline);
    if (dl) box.append(h('p', { class: 'pv-deadline ' + (dl.cls || '') }, dl.text));
    if (leader) box.append(h('p', { class: 'pv-leader', dir: 'auto' }, (leader.title ? leader.title + ': ' : '') + leader.text.replace(/\s+/g, ' ').trim()));
    box.append(h('div', { class: 'pv-about-btns' },
      h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => openSide('activity') }, iconEl('clock', 14), 'Activity'),
      h('button', { class: 'btn btn-quiet btn-small', type: 'button', title: 'Copies this project\u2019s full status as text for a Claude chat', onclick: () => copyProjectStatus(p) }, iconEl('copy', 14), 'Copy status'),
      OpenInClaude.button({ id: 'pvStatusClaude', text: () => projectStatusForClaude(p), project: p, quiet: true })));
    return box;
  }
  /* The next task, pinned or the first open one in the current milestone (Star and What is next, A3, layout B): the
     label with the pin and, while the task wears the star, Starred at its right; the task's own milestone with the
     due date at the right of its line, and nothing when there is none; the task, red with a ! when overdue; then Copy
     task and Open in Claude on one row. A starred task turns the box purple with a gold edge (A2). */
  function whatIsNext(p) {
    const t = nextTask(p), starred = !!(t && isStarred(p, t));
    const marks = h('span', { class: 'pv-next-marks' });
    const box = h('div', { class: 'pv-next' + (starred ? ' starred' : '') }, h('div', { class: 'pv-next-head' }, h('span', { class: 'pv-next-lbl' }, 'What is next'), marks));
    if (!t) {
      const w = waitingTasks(p)[0];
      box.append(h('p', { class: 'fv-empty' }, w ? 'Nothing open now. ' + w.text + ' comes back ' + backWhen(w) + '.'
        : p.milestones.length ? 'Every task is done. Add a task to a milestone to plan what comes next.' : 'No milestones yet. Add one under Todos to plan what is next.'));
      return box;
    }
    marks.append(...[Rounds.chip(p, t)].filter(Boolean), ...markButtons(p, t, 'next-mark', { chip: true }),
      ...(starred ? [h('span', { class: 'pv-starred', title: 'Starred for the city: set it in the task' }, iconEl('star', 12), 'Starred')] : []));
    const g = groupsOf(p).find(x => x.ms && x.ms.id === t.milestoneId) || currentGroup(p), ms = g.ms;
    const d = dueInfo(t), late = d && d.tone === 'late';
    box.append(h('div', { class: 'pv-next-msrow' },
      h('button', { class: 'pv-next-ms', type: 'button', title: 'Open this milestone', onclick: () => openMilestone(p, ms.id) },
        h('span', { class: 'ms-flag', html: iconSvg('flag', 14) }), h('span', { dir: 'auto' }, ms.name), h('span', { class: 'ms-count' }, countText(g))),
      shiftTag(t, 'pv-next-shift'),
      d ? h('span', { class: 'due pv-next-due ' + (d.tone || ''), title: t.due }, d.diff > 1 ? 'Due ' + weekdayOf(t.due) + ' ' + fmtDate(parseYmd(t.due)) : d.text) : null));
    box.append(h('button', { id: 'pvNextTask', class: 'pv-next-task' + (late ? ' late' : ''), type: 'button', dir: 'auto', title: 'Open this task', onclick: () => openTask(p, t.id) },
      late ? h('span', { class: 'pv-late-mark', 'aria-label': 'Overdue' }, '!') : null, h('span', null, t.text)));
    box.append(h('div', { class: 'pv-next-row' },
      h('button', { class: 'btn btn-quiet btn-small', type: 'button', title: 'Copies this task, with its description, for a Claude chat', onclick: () => copyTask(p, t) }, iconEl('copy', 14), 'Copy task'),
      OpenInClaude.button({ id: 'pvNextClaude', ...taskClaude(p, t), project: p, quiet: true })));
    const others = p.todos.filter(x => isOpenTask(x) && x !== t && x.due && dueInfo(x) && dueInfo(x).tone === 'late').length;
    if (others) box.append(h('p', { class: 'pv-late-note' }, '! ' + plural(others, 'other task is', 'other tasks are') + ' overdue'));
    return box;
  }
  const countText = g => '(' + g.todos.filter(t => t.done).length + '/' + g.todos.length + ')';
  function secHead(title, key, extra) {
    const ed = editing && editing.key === key;
    return h('div', { class: 'pv-sec-head' }, h('h3', { class: 'pv-h' }, title),
      ed ? null : extra || null,
      key ? (ed ? doneBtn() : pencil(key, title)) : null);
  }

  /* Todos: milestones with their tasks. Everything drags in place: a milestone by its flag, a task by its row.
     The square ticks a task; clicking a task, or a milestone's name, opens it beside the view. */
  let justDragged = false;
  function todos(p) {
    const box = h('section', { class: 'pv-sec', 'data-sec': 'todos' }, secHead('Todos', null, addBtn('Add milestone', 'pvAddMsBtn', () => openAdd('milestone'))));
    const pr = progressOf(p);
    const prog = progressRow(p, 'fv-prog');
    prog.append(h('span', { class: 'detail' }, pr.manual ? 'Set manually' : pr.total ? pr.done + ' of ' + pr.total + ' todos done' : 'No todos yet'));
    box.append(prog);
    const cur = currentGroup(p);
    const list = h('div', { class: 'ms-list' });
    for (const g of groupsOf(p)) {
      if (!g.ms || milestoneArchived(p, g.ms)) continue;        // a milestone in the archive goes with its tasks (B1)
      const m = g.ms;
      const toggle = h('button', { class: 'icon-btn ms-toggle', type: 'button', 'aria-expanded': String(!m.collapsed), 'aria-label': (m.collapsed ? 'Expand ' : 'Collapse ') + m.name,
        html: iconSvg(m.collapsed ? 'caretR' : 'caretD', 10), onclick: () => { m.collapsed = !m.collapsed; changed(p, { touch: false }); render(); } });
      const flag = h('button', { class: 'icon-btn ms-grip', type: 'button', 'aria-label': 'Move ' + m.name + ': drag, or use the up and down arrows', title: 'Drag to move', html: iconSvg('flag', 14) });
      flag.addEventListener('pointerdown', e => dragMilestone(e, p, m));
      flag.addEventListener('keydown', e => {
        if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
        e.preventDefault();
        const i = p.milestones.indexOf(m), j = i + (e.key === 'ArrowUp' ? -1 : 1);
        if (j < 0 || j >= p.milestones.length) return;
        p.milestones.splice(i, 1); p.milestones.splice(j, 0, m); normalizeOrder(p); changed(p); render();
        const again = $(`.ms[data-msid="${m.id}"] .ms-grip`, root); if (again) again.focus();
      });
      const plus = h('button', { class: 'icon-btn ms-plus', type: 'button', 'aria-label': 'Add a task to ' + m.name, title: 'Add a task', html: iconSvg('plus', 14),
        onclick: () => { if (m.collapsed) { m.collapsed = false; changed(p, { touch: false }); } openAdd('task:' + m.id); } });
      const row = h('div', { class: 'ms-row' }, toggle, flag,
        h('button', { class: 'ms-name-btn', type: 'button', dir: 'auto', title: 'Open this milestone', onclick: () => openMilestone(p, m.id) }, m.name),
        h('span', { class: 'ms-count' }, countText(g)),
        cur && cur.ms && cur.ms.id === m.id ? h('span', { class: 'tag ms-current' }, 'Current') : null,
        plus);
      const ul = h('ul', { class: 'tasks', 'data-ms': m.id, hidden: m.collapsed });
      const shown = shownTodos(g.todos);
      for (const t of shown) ul.append(taskRow(p, t));
      if (adding === 'task:' + m.id) {
        /* one line (O1, O2): !fri for the date, #weekly for a repeat, @name for another milestone; the line under it
           says what was understood before Enter */
        const opts = { project: p, msId: m.id };
        const hint = h('p', { id: 'pvAddHint', class: 'add-hint pv-add-hint', 'aria-live': 'polite' });
        const inp = h('input', { class: 'field', type: 'text', dir: 'auto', autocomplete: 'off', maxlength: '700', placeholder: 'New task, then Enter', 'aria-label': 'New task in ' + m.name, 'aria-describedby': 'pvAddHint',
          oninput: e => taskLineHint(hint, e.target.value, opts),
          onkeydown: e => {
            if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeAdd(); const b = $(`.ms[data-msid="${m.id}"] .ms-plus`, root); if (b) b.focus(); return; }
            if (e.key !== 'Enter') return;
            e.preventDefault();
            let goes = m.id;
            if (e.target.value.trim()) {
              const r = taskLineHint(hint, e.target.value, opts);
              if (!r.ok) return;
              goes = addTaskLine(r).milestoneId;
              Bubble.refresh();
            }
            adding = null;
            render();
            const b = $(`.ms[data-msid="${goes}"] .ms-plus`, root); if (b) b.focus();
          },
          onblur: () => setTimeout(() => { const cur = root && $('li.task-add .field', root); if (adding === 'task:' + m.id && !(cur && cur === document.activeElement)) closeAdd(); }, 150) });
        taskLineHint(hint, '', opts);
        ul.append(h('li', { class: 'task-add', 'data-adding': 'task' }, inp, hint));
      }
      /* its archived tasks, counted at its foot with the archive's icon and no words (E1, s1); a click opens them */
      const inArchive = g.todos.length - shown.length;
      if (inArchive) ul.append(h('li', { class: 'ms-archived' }, h('button', { class: 'ms-arch-btn', type: 'button', 'data-ms': m.id,
        title: inArchive + ' in the archive', 'aria-label': inArchive + ' in the archive. Open the archive', onclick: () => openArchive(p, m.id) },
        h('span', null, String(inArchive)), iconEl('archive', 14))));
      list.append(h('div', { class: 'ms', 'data-msid': m.id }, row, ul));
    }
    if (!p.milestones.length && adding !== 'milestone') list.append(h('p', { class: 'fv-empty' }, 'No milestones yet. Every task lives in one.'));
    else if (!liveMilestones(p).length && adding !== 'milestone') list.append(h('p', { class: 'fv-empty' }, 'Every milestone is in the archive. Add one to plan what is next.'));
    if (adding === 'milestone') {
      list.append(h('div', { class: 'pv-adding', 'data-adding': 'milestone' }, h('input', { class: 'field', type: 'text', dir: 'auto', autocomplete: 'off', placeholder: 'New milestone, then Enter', 'aria-label': 'New milestone name',
        onkeydown: e => {
          if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeAdd(); const b = $('#pvAddMsBtn', root); if (b) b.focus(); return; }
          if (e.key !== 'Enter') return;
          e.preventDefault();
          const name = e.target.value.trim().slice(0, 120);
          adding = null;
          if (name) { const m = { id: uid('m'), name, collapsed: false }; p.milestones.push(m); logActivity(p, 'New milestone: ' + name); changed(p); render(); const b = $(`.ms[data-msid="${m.id}"] .ms-plus`, root); if (b) b.focus(); }
          else render();
        },
        onblur: () => setTimeout(() => { const cur = root && $('[data-adding="milestone"] .field', root); if (adding === 'milestone' && !(cur && cur === document.activeElement)) closeAdd(); }, 150) })));
    }
    box.append(list);
    return box;
  }
  /* A ticked repeat waits for its next date (R1): dimmed in its place, with its repeat sign for the square and when it
     comes back, so it can still be opened, changed or stopped here, and nowhere else. */
  function taskRow(p, t) {
    const wait = isWaiting(t);
    const li = h('li', { class: 'task' + (t.done ? ' done' : '') + (wait ? ' waiting' : '') + (sideMode === 'task' && sideTask === t.id ? ' on' : ''), 'data-id': t.id });
    const cb = wait
      ? h('span', { class: 'task-wait', role: 'img', 'aria-label': repeatText(t.repeat) + ', ticked', title: repeatText(t.repeat) + '. Ticked: it comes back ' + backWhen(t) + '.', html: iconSvg('repeat', 14) })
      : h('input', { type: 'checkbox', class: 'cb', checked: t.done, 'aria-label': 'Done: ' + t.text, onchange: e => {
      if (e.target.checked) { const was = tickTask(p, t); if (t.repeat) repeatToast(p, t, was); }      // a repeat moves on (R4)
      else untickTask(p, t);
      changed(p); render(); Bubble.refresh();
      const again = $(`.task[data-id="${t.id}"] .cb`, root) || $(`.task[data-id="${t.id}"] .task-title`, root); if (again) again.focus();
    } });
    const title = h('button', { class: 'task-title', type: 'button', dir: 'auto', title: 'Open this task',
      onclick: () => { if (justDragged) { justDragged = false; return; } openTask(p, t.id); } }, t.text);
    title.addEventListener('keydown', e => {
      if (!e.altKey || (e.key !== 'ArrowUp' && e.key !== 'ArrowDown')) return;
      e.preventDefault();
      if (!moveTodo(p, t, e.key === 'ArrowUp' ? -1 : 1)) return;
      changed(p); render();
      const again = $(`.task[data-id="${t.id}"] .task-title`, root); if (again) again.focus();
    });
    li.addEventListener('pointerdown', e => { if (e.target.closest('.cb, .task-mark, .round-hat')) return; dragTask(e, p, li); });
    const d = t.done || wait ? null : dueInfo(t);
    li.append(...[cb, title, (t.description || '').trim() ? h('span', { class: 'task-has-desc', title: 'Has a description', html: iconSvg('doc', 12) }) : null,
      Rounds.hatButton(p, t, 'row-round'),                                      // its wizard round (0.1.55)
      t.repeat && !wait ? h('span', { class: 'repeat-mark', title: 'Repeats: ' + repeatText(t.repeat), html: iconSvg('repeat', 12) }) : null,
      shiftTag(t, 'row-shift'),
      wait ? h('span', { class: 'due back', title: repeatText(t.repeat) }, backText(t)) : null,
      d ? h('span', { class: 'due ' + (d.tone || '') }, (d.tone === 'late' ? '! ' : '') + d.text) : null, ...markButtons(p, t, 'row-mark'),
      canArchive(t) ? h('button', { class: 'icon-btn task-mark mark-archive', type: 'button', 'data-task': t.id, 'aria-label': 'Archive: ' + t.text,
        title: 'Archive it now. Done tasks go there by themselves 7 days after their tick', html: iconSvg('archive', 14),
        onclick: e => { e.stopPropagation(); rowArchive(p, t); } }) : null].filter(Boolean));
    return li;
  }
  /* After a row's archive button: the focus moves to the next done row's button, else the milestone's +. */
  function rowArchive(p, t) {
    const ul = $(`.task[data-id="${t.id}"]`, root)?.closest('ul.tasks'), msId = ul && ul.dataset.ms;
    const after = ul ? $$('.task', ul).map(r => r.dataset.id) : [];
    archiveByHand(p, [t]);
    const next = after.slice(after.indexOf(t.id) + 1).concat(after.slice(0, after.indexOf(t.id))).map(id => $(`.task[data-id="${id}"] .mark-archive`, root)).find(Boolean);
    const b = next || (msId && $(`.ms[data-msid="${msId}"] .ms-plus`, root)) || $('#pvAddMsBtn', root);
    if (b) b.focus();
  }
  /* ---------- the archive (Archiving, Round 1) ----------
     By hand (A1): a done row's button, a done task's panel, or every done task in a milestone, with a toast and Undo.
     Restore (C1) brings a task back done, for another 7 days. Neither is work: Updated and urgency stay. */
  function archiveByHand(p, list, from = '') {
    const snaps = archiveTasks(list);
    if (!snaps.length) return 0;
    changed(p, { touch: false }); render(); Bubble.refresh();
    toast(snaps.length === 1 ? 'Archived ' + snaps[0].t.text + '.' : 'Archived ' + snaps.length + ' done tasks' + (from ? ' from ' + from : '') + '.', '', { label: 'Undo', run: () => {
      snaps.forEach(putBackArchive); changed(p, { touch: false });
      if (root && openId === p.id) render();
    } });
    return snaps.length;
  }
  function restoreByHand(p, t) {
    const s = restoreTask(t);
    if (!p.milestones.some(m => m.id === t.milestoneId)) { t.milestoneId = homeMilestone(p).ms.id; normalizeOrder(p); }   // its milestone is gone
    const ms = p.milestones.find(m => m.id === t.milestoneId);
    if (ms) ms.collapsed = false;
    changed(p, { touch: false }); render(); Bubble.refresh();
    toast('Restored ' + t.text + (ms ? ' to ' + ms.name : '') + '.', '', { label: 'Undo', run: () => {
      putBackArchive(s); changed(p, { touch: false });
      if (root && openId === p.id) render();
    } });
  }
  /* Where a task with no milestone of its own goes, as one added without @ does: the current milestone, else the last
     one not in the archive, else a new To do. made says the milestone is new. */
  function homeMilestone(p) {
    const id = defaultMilestone(p);
    if (id) return { ms: p.milestones.find(m => m.id === id), made: false };
    const ms = { id: uid('m'), name: 'To do', collapsed: false };
    p.milestones.push(ms);
    return { ms, made: true };
  }
  /* The Archive view (A1, C3), beside the project view: by milestone, newest first, each task with Restore. */
  function openArchive(p, msId = null, taskId = null) {
    finishEdit(); adding = null;
    if (side) closeSide();
    const t = taskId ? p.todos.find(x => x.id === taskId) : null, at = msId || (t && t.milestoneId);
    const ms = at ? p.milestones.find(m => m.id === at) : null;
    if (ms ? archFolded(p, ms) : t && archFolded(p, null)) setArchFolded(p, ms, false);   // opened at it, so it shows
    openSide('archive');
    const target = taskId ? $(`.pv-arch-task[data-id="${taskId}"] .pv-arch-title`, side) : msId ? $(`.pv-arch-group[data-msid="${msId}"] .pv-arch-ms`, side) : null;
    if (target) { target.scrollIntoView({ block: 'nearest' }); target.focus({ preventScroll: true }); }
  }
  /* An archived task's panel backs out to the archive, with the task in view (Esc, and Back to the archive). */
  function backToArchive() {
    const p = P(); if (!p || sideMode !== 'task') return false;
    const t = p.todos.find(x => x.id === sideTask);
    if (!t || !t.archived || !taskSnap || !taskSnap.archived) return false;
    openArchive(p, null, t.id);
    return true;
  }
  const tickedDay = t => (t.doneAt ? 'Ticked ' + weekdayOf(ymd(t.doneAt)) + ' ' + fmtDate(t.doneAt) : 'Done');
  /* A milestone folds in the archive as it does in the list (0.1.50), each on its own: `archiveCollapsed` on the
     milestone, kept with the city like `collapsed`. The group with no milestone keeps it while the page is open. */
  const looseFolded = new Set();
  const archFolded = (p, ms) => (ms ? !!ms.archiveCollapsed : looseFolded.has(p.id));
  function setArchFolded(p, ms, on) {
    if (!ms) { if (on) looseFolded.add(p.id); else looseFolded.delete(p.id); return; }
    if (on) ms.archiveCollapsed = true; else delete ms.archiveCollapsed;
    changed(p, { touch: false });
  }
  function archiveView(p) {
    const groups = archiveGroups(p);
    const box = h('div', { class: 'pv-archive' },
      h('p', { class: 'note' }, 'Done tasks come here 7 days after their tick, or sooner by hand. Restore brings one back, done, for another 7 days.'));
    if (!groups.length) { box.append(h('p', { class: 'fv-empty' }, 'Nothing in the archive yet.')); return box; }
    for (const g of groups) {
      const name = g.ms ? g.ms.name : 'No milestone', folded = archFolded(p, g.ms), key = g.ms ? g.ms.id : '';
      const toggle = h('button', { class: 'icon-btn ms-toggle pv-arch-toggle', type: 'button', 'aria-expanded': String(!folded), 'aria-label': (folded ? 'Expand ' : 'Collapse ') + name,
        title: folded ? 'Show its tasks' : 'Fold it', html: iconSvg(folded ? 'caretR' : 'caretD', 10),
        onclick: () => { setArchFolded(p, g.ms, !folded); renderSide(); const b = side && $(`.pv-arch-group[data-msid="${key}"] .pv-arch-toggle`, side); if (b) b.focus(); } });
      box.append(h('section', { class: 'pv-arch-group' + (folded ? ' folded' : ''), 'data-msid': key },
        h('h3', { class: 'pv-arch-ms', tabindex: '-1' }, toggle, h('span', { class: 'ms-flag', html: iconSvg('flag', 14) }),
          h('span', { class: 'pv-arch-name', dir: 'auto' }, name), h('span', { class: 'ms-count' }, '(' + g.tasks.length + ')'),
          g.whole ? h('span', { class: 'pv-arch-whole', title: 'Every task in it is archived, so the milestone is in the archive too. Restoring one brings it back.' }, 'Milestone archived') : null),
        h('ul', { class: 'pv-arch-list', hidden: folded }, g.tasks.map(t => h('li', { class: 'pv-arch-task', 'data-id': t.id },
          h('div', { class: 'pv-arch-body' },
            h('button', { class: 'pv-arch-title', type: 'button', dir: 'auto', title: 'Open this task', onclick: () => openTask(p, t.id) }, t.text),
            h('span', { class: 'pv-arch-day' }, tickedDay(t))),
          h('button', { class: 'btn btn-small pv-arch-restore', type: 'button', 'aria-label': 'Restore ' + t.text, title: 'Back to its milestone, done',
            onclick: () => {
              const rows = $$('.pv-arch-task', side).map(r => r.dataset.id), i = rows.indexOf(t.id);
              restoreByHand(p, t);
              const next = side && ($(`.pv-arch-task[data-id="${rows[i + 1]}"] .pv-arch-restore`, side) || $(`.pv-arch-task[data-id="${rows[i - 1]}"] .pv-arch-restore`, side));
              if (next) next.focus(); else if (side) side.focus({ preventScroll: true });
            } }, 'Restore'))))));
    }
    return box;
  }
  /* Up or down one place, crossing into the neighbouring milestone at an edge. */
  function moveTodo(p, t, dir) {
    const groups = groupsOf(p).filter(g => g.ms && !milestoneArchived(p, g.ms)).map(g => ({ ms: g.ms, todos: shownTodos(g.todos) }));
    const gi = groups.findIndex(g => g.todos.includes(t)), g = groups[gi], i = g.todos.indexOf(t);
    if (dir < 0) {
      if (i > 0) { g.todos.splice(i, 1); g.todos.splice(i - 1, 0, t); }
      else if (gi > 0) { g.todos.splice(i, 1); groups[gi - 1].todos.push(t); t.milestoneId = groups[gi - 1].ms.id; }
      else return false;
    } else {
      if (i < g.todos.length - 1) { g.todos.splice(i, 1); g.todos.splice(i + 1, 0, t); }
      else if (gi < groups.length - 1) { g.todos.splice(i, 1); groups[gi + 1].todos.unshift(t); t.milestoneId = groups[gi + 1].ms.id; }
      else return false;
    }
    reorderShown(p, groups.flatMap(x => x.todos));                // archived tasks keep their places
    return true;
  }
  /* Near the panel's top or bottom edge a drag scrolls the list, but only once you move toward that edge,
     so a drag that starts near an edge does not run away. */
  function edgeScroll(y, y0) {
    const r = root.getBoundingClientRect();
    if (y > r.bottom - 48 && y > y0 + 12) root.scrollTop += 14;
    else if (y < r.top + 48 && y < y0 - 12) root.scrollTop -= 14;
  }
  /* A task follows the pointer once it moves a few pixels; a plain click still opens it. */
  function dragTask(e, p, li) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    const pid = e.pointerId, y0 = e.clientY, x0 = e.clientX;
    let dragging = false;
    const move = ev => {
      if (ev.pointerId !== pid) return;
      if (!dragging) {
        if (Math.hypot(ev.clientX - x0, ev.clientY - y0) < 5) return;
        dragging = true; li.classList.add('dragging'); document.body.classList.add('pv-dragging');
      }
      ev.preventDefault();
      edgeScroll(ev.clientY, y0);
      const anchors = $$('.ms-list .task:not(.dragging), .ms-list .ms-row', root).filter(a => a.offsetParent);
      const target = anchors.find(a => { const b = a.getBoundingClientRect(); return ev.clientY < b.top + b.height / 2; });
      const lists = $$('.ms-list ul.tasks', root);
      if (!target) { lists[lists.length - 1].append(li); return; }
      if (target.classList.contains('task')) { if (target.previousElementSibling !== li) target.parentElement.insertBefore(li, target); return; }
      const msEl = target.closest('.ms'), prev = msEl.previousElementSibling;
      if (prev && prev.classList.contains('ms')) $('ul.tasks', prev).append(li);
      else $('ul.tasks', msEl).prepend(li);
    };
    const up = ev => {
      if (ev.pointerId !== pid) return;
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); window.removeEventListener('pointercancel', up);
      if (!dragging) return;
      li.classList.remove('dragging'); document.body.classList.remove('pv-dragging');
      justDragged = true; setTimeout(() => { justDragged = false; }, 0);
      const order = [];
      for (const ul of $$('.ms-list ul.tasks', root)) for (const row of ul.children) {
        const t = p.todos.find(x => x.id === row.dataset.id); if (t) { t.milestoneId = ul.dataset.ms; order.push(t); }
      }
      const was = p.todos.map(x => x.id + ':' + x.milestoneId).join();
      reorderShown(p, order);                                     // archived tasks keep their places
      if (p.todos.map(x => x.id + ':' + x.milestoneId).join() !== was) changed(p);
      render();
    };
    window.addEventListener('pointermove', move, { passive: false }); window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up);
  }
  /* A milestone, with its tasks, follows the pointer by its flag. */
  function dragMilestone(e, p, m) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    e.preventDefault();
    const pid = e.pointerId, y0 = e.clientY, el = $(`.ms[data-msid="${m.id}"]`, root), list = el.parentElement;
    el.classList.add('dragging'); document.body.classList.add('pv-dragging');
    const move = ev => {
      if (ev.pointerId !== pid) return;
      edgeScroll(ev.clientY, y0);
      const blocks = $$('.ms', list).filter(b => b !== el);
      const target = blocks.find(b => { const bb = $('.ms-row', b).getBoundingClientRect(); return ev.clientY < bb.top + bb.height / 2; });
      if (target) { if (target.previousElementSibling !== el) list.insertBefore(el, target); }
      else if (list.lastElementChild !== el) list.append(el);
    };
    const up = ev => {
      if (ev.pointerId !== pid) return;
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); window.removeEventListener('pointercancel', up);
      el.classList.remove('dragging'); document.body.classList.remove('pv-dragging');
      const ids = $$('.ms', list).map(b => b.dataset.msid);
      const was = p.milestones.map(x => x.id).join();
      p.milestones.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id));
      if (p.milestones.map(x => x.id).join() !== was) { normalizeOrder(p); changed(p); }
      render();
    };
    window.addEventListener('pointermove', move); window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up);
  }
  function progressControls(p) {
    const pr0 = progressOf(p);
    const num = h('input', { class: 'field num', type: 'number', min: '0', max: '100', step: '5', value: String(pr0.manual ? pr0.pct : pr0.auto), disabled: !pr0.manual, 'aria-label': 'Manual progress, in percent',
      oninput: e => { const v = parseInt(e.target.value, 10); if (!isNaN(v)) { p.progressOverride = clamp(v, 0, 100); changed(p); } } });
    const rAuto = h('input', { type: 'radio', name: 'prog', checked: !pr0.manual, onchange: () => { p.progressOverride = null; num.disabled = true; changed(p); } });
    const rMan = h('input', { type: 'radio', name: 'prog', checked: pr0.manual, onchange: () => {
      const v = parseInt(num.value, 10); p.progressOverride = clamp(isNaN(v) ? progressOf(p).auto : v, 0, 100);
      num.disabled = false; num.focus(); changed(p);
    } });
    return h('div', { class: 'pv-prog-ed' }, h('span', { class: 'lbl' }, 'Progress'),
      h('div', { class: 'inline' }, h('label', { class: 'radio' }, rAuto, 'Automatic: ' + pr0.auto + '% from todos'), h('label', { class: 'radio' }, rMan, 'Set manually'), num, h('span', null, '%')));
  }

  /* ---------- a task or a milestone, open in full beside the view ---------- */
  let sideTask = null, taskSnap = null, sideMs = null, msSnap = null, sideTicked = false;
  function openTask(p, id) {
    finishEdit(); adding = null;
    if (side) closeSide();
    const t = p.todos.find(x => x.id === id); if (!t) return;
    sideTask = id; taskSnap = clone(t); sideTicked = false;
    Rounds.foldAll();                                                           // its round's answers start folded (P1a)
    openSide('task');
    const f = $('#pvTaskDesc', side); if (f) f.focus();
  }
  function finishTask() {
    const p = P(); if (!p || !sideTask) return;
    const t = p.todos.find(x => x.id === sideTask);
    if (t && taskSnap) {
      if (!t.text.trim()) t.text = taskSnap.text || 'Untitled task';
      if (t.done !== taskSnap.done) logActivity(p, (t.done ? 'Done: ' : 'Reopened: ') + t.text);
      if (sideTicked && isWaiting(t)) logActivity(p, 'Done: ' + t.text);                 // a repeat ticked here moved on
      const edited = t.text !== taskSnap.text || t.description !== taskSnap.description || (t.due !== taskSnap.due && !sideTicked)
        || JSON.stringify(t.repeat || null) !== JSON.stringify(taskSnap.repeat || null);
      if (edited) logActivity(p, 'Edited task: ' + t.text);
      changed(p, { touch: edited || t.done !== taskSnap.done || sideTicked });
    }
    sideTask = null; taskSnap = null; sideTicked = false;
  }
  function cancelTask() {
    const p = P(); if (!p || !sideTask) return;
    const i = p.todos.findIndex(x => x.id === sideTask);
    if (i >= 0 && taskSnap) {
      const live = p.todos[i].round;                // a round came, went or was answered while open: Esc leaves it, as it leaves pins
      p.todos[i] = taskSnap;
      if (live) taskSnap.round = live; else delete taskSnap.round;
    }
    changed(p, { touch: false });
    sideTask = null; taskSnap = null; sideTicked = false;
    side.remove(); side = null; sideMode = null;
    if (root.style.width) root.style.width = '';
    render(); Bubble.refresh();
    toast('Task changes undone.');
  }
  function taskEditor(p) {
    const t = p.todos.find(x => x.id === sideTask);
    if (!t) return h('p', { class: 'fv-empty' }, 'This task is gone.');
    if (t.archived) return archivedTask(p, t);
    const ms = p.milestones.find(m => m.id === t.milestoneId);
    const title = h('input', { id: 'pvTaskTitle', class: 'field pv-note-title', type: 'text', dir: 'auto', maxlength: '500', value: t.text, 'aria-label': 'Task title', autocomplete: 'off',
      oninput: e => { t.text = e.target.value; changed(p, { touch: false }); const b = $(`.task[data-id="${t.id}"] .task-title`, root); if (b) b.textContent = t.text; } });
    const wait = isWaiting(t);
    /* the Done line is written when the panel closes, as for any task; a repeat ticked here moves on, and waits */
    const done = h('input', { id: 'pvTaskDone', type: 'checkbox', class: 'cb', checked: t.done, onchange: e => {
      if (e.target.checked) { tickTask(p, t, { log: false }); if (t.repeat) sideTicked = true; }
      else untickTask(p, t, null, { log: false });
      changed(p, { touch: false }); render(); Bubble.refresh();
      const b = side && ($('#pvTaskDone', side) || $('#pvTaskDue', side)); if (b) b.focus();
    } });
    /* a waiting repeat's due date is the day it comes back: a nearer one brings it back sooner */
    const due = h('input', { id: 'pvTaskDue', class: 'field', type: 'date', value: t.due, 'aria-label': 'Due date',
      onchange: e => { const w = isWaiting(t); t.due = parseYmd(e.target.value) != null ? e.target.value : ''; setWaiting(t, w && !!t.due); changed(p, { touch: false }); render(); } });
    const d = wait ? null : dueInfo(t);
    const desc = h('textarea', { id: 'pvTaskDesc', class: 'field pv-note-body', dir: 'auto', rows: '14', placeholder: 'What this task is, in full: what done looks like, where things are, anything Claude should know', 'aria-label': 'Task description',
      oninput: e => { t.description = e.target.value.slice(0, 8000); changed(p, { touch: false }); } }, t.description || '');
    return h('div', { class: 'pv-note-ed' },
      h('p', { class: 'pv-task-ms' }, h('span', { class: 'ms-flag', html: iconSvg('flag', 14) }), ms ? ms.name : ''),
      title,
      h('div', { class: 'inline pv-task-meta' },
        wait ? h('p', { class: 'pv-task-back', title: 'Esc undoes the tick; a nearer due date brings it back sooner' }, iconEl('repeat', 14), 'Ticked. ' + backText(t) + ', due that day.') : h('label', { class: 'check' }, done, 'Done'),
        canArchive(t) ? h('button', { id: 'pvTaskArchive', class: 'btn btn-quiet btn-small', type: 'button', title: 'Archive it now. Done tasks go there by themselves 7 days after their tick',
          onclick: () => { closeSide(); archiveByHand(p, [t]); root.focus({ preventScroll: true }); } }, iconEl('archive', 14), 'Archive') : null,
        h('span', { class: 'lbl' }, 'Due'), due,
        h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => { t.due = ''; setWaiting(t, false); due.value = ''; changed(p, { touch: false }); render(); } }, 'Clear'),
        d && !t.done ? h('span', { class: 'due ' + (d.tone || '') }, (d.tone === 'late' ? '! ' : '') + d.text) : null),
      t.done ? null : repeatEditor(p, t),
      shiftEditor(p, t),
      !isOpenTask(t) ? null : h('div', { class: 'inline pv-task-marks' }, ...[
        ['pin', isPinned(p, t), 'Pinned', 'Pin as next', 'Comes first in What is next and the status card', on => setPin(p, t, on)],
        ['star', isStarred(p, t), 'Starred', 'Star for the city', 'The one task the whole city shows with a star, over its building; starring pins it too', on => setStar(p, t, on)],
      ].map(([kind, on, yes, no, title, set]) => h('button', { class: 'btn btn-quiet btn-small pv-mark' + (on ? ' on' : ''), type: 'button', 'data-mark': kind, 'data-task': t.id,
        'aria-pressed': String(on), title: on ? title + '. Click to take it off.' : title,
        onclick: () => { set(!on); render(); const b = side && $(`[data-mark="${kind}"]`, side); if (b) b.focus(); } }, iconEl(kind, 14, on ? undefined : 'transparent'), on ? yes : no))),
      h('div', { class: 'pv-round-slot' }, Rounds.card(p, t)),                 // its wizard round (0.1.55, P1)
      h('span', { class: 'lbl' }, 'Description'), desc,
      h('div', { class: 'pv-claude-row' },
        h('button', { class: 'btn btn-small', type: 'button', title: 'Copies this task, with its description, for a Claude chat', onclick: () => copyTask(p, t) }, iconEl('copy', 14), 'Copy task'),
        OpenInClaude.button({ id: 'pvTaskClaude', ...taskClaude(p, t), project: p })),
      h('div', { class: 'pv-note-foot' },
        h('button', { id: 'pvTaskToNote', class: 'btn btn-small', type: 'button', title: 'Keep it as an idea in Notes: its title and description stay; its date, repeat and shift go',
          onclick: () => turnIntoNote(p, t.id) }, iconEl('doc', 14), 'Turn into a note'),
        deleteTaskBtn(p, t)),
      h('p', { class: 'note' }, 'Saves as you type. Done closes it; Esc undoes everything since it opened.'));
  }
  /* Delete task. An archived task deleted from its panel goes back to the archive; the last task of a milestone in
     the archive takes the milestone with it, since nothing would show it again. */
  function deleteTaskBtn(p, t) {
    return h('button', { id: 'pvTaskDelete', class: 'btn btn-danger btn-small', type: 'button', onclick: () => {
      const wasArchived = !!t.archived, ms = p.milestones.find(m => m.id === t.milestoneId);
      const lastOfArchived = ms && milestoneArchived(p, ms) && p.todos.filter(x => x.milestoneId === ms.id).length === 1;
      p.todos.splice(p.todos.indexOf(t), 1);
      if (lastOfArchived) p.milestones.splice(p.milestones.indexOf(ms), 1);
      logActivity(p, 'Removed todo: ' + t.text);
      changed(p);
      sideTask = null; taskSnap = null;
      closeSide(); render(); Bubble.refresh();
      if (wasArchived) openArchive(p);
      toast('Task deleted.');
    } }, 'Delete task');
  }
  /* An archived task (C2): the same panel, to read, with Restore, Copy task and Delete task. */
  function archivedTask(p, t) {
    const ms = p.milestones.find(m => m.id === t.milestoneId);
    const desc = (t.description || '').trim();
    return h('div', { class: 'pv-note-ed pv-task-archived' },
      h('p', { class: 'pv-task-ms' }, h('span', { class: 'ms-flag', html: iconSvg('flag', 14) }), ms ? ms.name : 'No milestone'),
      h('h3', { id: 'pvTaskTitle', class: 'pv-arch-head', dir: 'auto' }, t.text),
      h('p', { class: 'pv-arch-state' }, iconEl('archive', 14), 'In the archive. ' + tickedDay(t) + '.'),
      h('div', { class: 'pv-arch-actions' },
        h('button', { id: 'pvTaskRestore', class: 'btn btn-accent btn-small', type: 'button', title: 'Back to its milestone, done, for another 7 days',
          onclick: () => { restoreByHand(p, t); const b = side && $('#pvTaskArchive', side); if (b) b.focus(); } }, 'Restore'),
        h('button', { id: 'pvTaskBackArch', class: 'btn btn-quiet btn-small', type: 'button', onclick: () => backToArchive() }, iconEl('back', 14), 'Back to the archive')),
      t.due ? h('p', { class: 'note' }, 'It was due ' + weekdayOf(t.due) + ' ' + fmtDate(parseYmd(t.due)) + '.') : null,
      t.round ? h('div', { class: 'pv-round-slot' }, Rounds.card(p, t, { readOnly: true })) : null,
      h('span', { class: 'lbl' }, 'Description'),
      desc ? h('div', { id: 'pvTaskDesc', class: 'note-text pv-arch-desc', tabindex: '-1' }, ...paragraphs(desc)) : h('p', { id: 'pvTaskDesc', class: 'fv-empty', tabindex: '-1' }, 'No description.'),
      h('div', { class: 'pv-claude-row' },
        h('button', { class: 'btn btn-small', type: 'button', title: 'Copies this task, with its description, for a Claude chat', onclick: () => copyTask(p, t) }, iconEl('copy', 14), 'Copy task'),
        OpenInClaude.button({ id: 'pvTaskClaude', text: kind => taskForClaude(p, t, Date.now(), { kind }), files: () => Rounds.files(t), project: p })),
      h('div', { class: 'pv-note-foot' }, deleteTaskBtn(p, t)),
      h('p', { class: 'note' }, 'To change it, restore it. Esc goes back to the archive.'));
  }
  /* Shift: Create, Think or Errand, one or none; a click on the pressed one takes it off. Like the rest of the panel,
     Esc undoes it; on its own it is not work, so closing the panel leaves Updated alone. */
  function shiftEditor(p, t) {
    return h('div', { class: 'inline pv-shift-row', role: 'group', 'aria-label': 'Shift' }, h('span', { class: 'lbl' }, 'Shift'),
      ...SHIFTS.map(([id, name]) => {
        const on = t.shift === id;
        return h('button', { class: 'btn btn-quiet btn-small pv-shift shift-' + id + (on ? ' on' : ''), type: 'button', 'data-shift': id, 'aria-pressed': String(on),
          title: on ? name + '. Click to take it off.' : SHIFT_HINTS[id],
          onclick: () => { setShift(p, t, on ? '' : id); render(); Bubble.refresh(); const b = side && $(`.pv-shift[data-shift="${id}"]`, side); if (b) b.focus(); } },
          h('i', { class: 'shift-dot', 'aria-hidden': 'true' }), name);
      }));
  }
  /* Repeat (R2): every day, every N days, weekly on chosen weekdays, monthly on a date, yearly. A task with no date
     gets the schedule's first one. Each change redraws the panel, so the focus goes back to the control it came from. */
  function repeatEditor(p, t) {
    const r = t.repeat || null;
    const kind = !r ? 'none' : r.every === 'day' ? (r.n === 1 ? 'daily' : 'days') : r.every;
    const set = (rep, focusSel) => {
      if (JSON.stringify(rep) === JSON.stringify(t.repeat || null)) return;          // also a change the redraw itself fires
      if (rep) { t.repeat = rep; if (!t.due) t.due = firstRepeatDue(rep); }
      else { delete t.repeat; setWaiting(t, false); }
      changed(p, { touch: false }); render(); Bubble.refresh();
      const b = side && $(focusSel || '#pvRepeat', side); if (b) b.focus();
    };
    const base = new Date(parseYmd(t.due) != null ? parseYmd(t.due) : startOfDay(Date.now()));
    const pick = h('select', { id: 'pvRepeat', class: 'field pv-repeat-kind', 'aria-label': 'Repeat', onchange: e => {
      const k = e.target.value;
      set(k === 'none' ? null : k === 'daily' ? { every: 'day', n: 1 } : k === 'days' ? { every: 'day', n: 2 }
        : k === 'week' ? { every: 'week', days: [base.getDay()] } : k === 'month' ? { every: 'month', day: base.getDate() }
        : { every: 'year', month: base.getMonth() + 1, day: base.getDate() });
    } }, [['none', 'No repeat'], ['daily', 'Every day'], ['days', 'Every N days'], ['week', 'Weekly'], ['month', 'Monthly'], ['year', 'Yearly']]
      .map(([v, l]) => h('option', { value: v, selected: v === kind }, l)));
    const opts = (from, to, label, on) => Array.from({ length: to - from + 1 }, (_, i) => h('option', { value: String(from + i), selected: from + i === on }, label(from + i)));
    const row = [pick];
    if (kind === 'days') row.push(h('input', { id: 'pvRepeatN', class: 'field num', type: 'number', min: '2', max: '365', value: String(r.n), 'aria-label': 'Every how many days',
      onchange: e => { const n = parseInt(e.target.value, 10); if (n >= 1 && n <= 365) set({ every: 'day', n }, '#pvRepeatN'); else e.target.value = String(r.n); } }), h('span', null, 'days'));
    if (kind === 'month') row.push(h('span', null, 'on the'), h('select', { id: 'pvRepeatDay', class: 'field pv-repeat-num', 'aria-label': 'Day of the month', onchange: e => set({ every: 'month', day: +e.target.value }, '#pvRepeatDay') },
      opts(1, 31, ordinal, r.day)));
    if (kind === 'year') row.push(h('span', null, 'on'),
      h('select', { id: 'pvRepeatDay', class: 'field pv-repeat-num', 'aria-label': 'Day', onchange: e => set({ every: 'year', month: r.month, day: +e.target.value }, '#pvRepeatDay') }, opts(1, daysInMonth(2024, r.month - 1), String, r.day)),
      h('select', { id: 'pvRepeatMonth', class: 'field pv-repeat-num', 'aria-label': 'Month', onchange: e => { const month = +e.target.value; set({ every: 'year', month, day: Math.min(r.day, daysInMonth(2024, month - 1)) }, '#pvRepeatMonth'); } },
        opts(1, 12, m => MONTHS[m - 1], r.month)));
    const days = kind === 'week' ? h('div', { class: 'pv-repeat-days', role: 'group', 'aria-label': 'Weekdays' }, WEEK_ORDER.map(d => h('button', { class: 'btn set-day', type: 'button', 'data-day': String(d),
      'aria-pressed': String(r.days.includes(d)), title: r.days.includes(d) ? (r.days.length > 1 ? 'Click to drop ' + WEEKDAYS[d] : 'A weekly repeat needs one day at least') : 'Click to add ' + WEEKDAYS[d],
      onclick: () => { const next = r.days.includes(d) ? r.days.filter(x => x !== d) : [...r.days, d]; if (next.length) set({ every: 'week', days: next.sort((a, b) => a - b) }, `.pv-repeat-days [data-day="${d}"]`); } }, WEEKDAYS[d]))) : null;
    return h('div', { class: 'pv-repeat' },
      h('div', { class: 'inline pv-repeat-row' }, h('span', { class: 'lbl' }, 'Repeat'), ...row), days,
      r ? h('p', { class: 'note pv-repeat-note' }, 'Ticked, it moves on to its next date and waits out of sight until then.'
        + (r.every === 'month' && r.day > 28 ? ' Months without the ' + ordinal(r.day) + ' use their last day.' : r.every === 'year' && r.month === 2 && r.day === 29 ? ' Other years use 28 February.' : '')) : null);
  }
  function openMilestone(p, id) {
    finishEdit(); adding = null;
    if (side) closeSide();
    const m = p.milestones.find(x => x.id === id); if (!m) return;
    sideMs = id; msSnap = clone(m);
    openSide('milestone');
    const f = $('#pvMsName', side); if (f) { f.focus(); f.select(); }
  }
  function finishMilestone() {
    const p = P(); if (!p || !sideMs) return;
    const m = p.milestones.find(x => x.id === sideMs);
    if (m && msSnap) {
      if (!m.name.trim()) m.name = msSnap.name || 'Untitled milestone';
      if (m.name !== msSnap.name) { logActivity(p, 'Renamed milestone to ' + m.name); changed(p); }
    }
    sideMs = null; msSnap = null;
  }
  function cancelMilestone() {
    const p = P(); if (!p || !sideMs) return;
    const i = p.milestones.findIndex(x => x.id === sideMs);
    if (i >= 0 && msSnap) p.milestones[i] = msSnap;
    changed(p, { touch: false });
    sideMs = null; msSnap = null;
    side.remove(); side = null; sideMode = null;
    if (root.style.width) root.style.width = '';
    render();
    toast('Milestone changes undone.');
  }
  function milestoneEditor(p) {
    const m = p.milestones.find(x => x.id === sideMs);
    if (!m) return h('p', { class: 'fv-empty' }, 'This milestone is gone.');
    const g = groupsOf(p).find(x => x.ms && x.ms.id === m.id);
    const name = h('input', { id: 'pvMsName', class: 'field pv-note-title', type: 'text', dir: 'auto', maxlength: '120', value: m.name, 'aria-label': 'Milestone name', autocomplete: 'off',
      oninput: e => { m.name = e.target.value; changed(p, { touch: false }); const b = $(`.ms[data-msid="${m.id}"] .ms-name-btn`, root); if (b) b.textContent = m.name; },
      onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); closeSide(); render(); } } });
    const now = Date.now();
    const order = [...shownTodos(g.todos), ...g.todos.filter(isArchived).sort((a, b) => archivedWhen(b) - archivedWhen(a))];
    const tasks = g.todos.length
      ? h('ol', { class: 'pv-ms-tasks', 'aria-label': 'The tasks in this milestone' }, order.map(t => {
          const d = dueInfo(t, now), first = (t.description || '').trim().split('\n')[0];
          return h('li', { class: 'pv-ms-task' + (t.done ? ' done' : '') + (t.archived ? ' archived' : ''), 'data-id': t.id },
            h('span', { class: 'pv-ms-box' + (t.done ? ' done' : ''), 'aria-hidden': 'true' }),
            h('span', { class: 'pv-ms-body' },
              h('span', { class: 'pv-ms-text', dir: 'auto' }, t.text, h('span', { class: 'visually-hidden' }, t.archived ? ' (done, in the archive)' : t.done ? ' (done)' : '')),
              isWaiting(t, now) ? h('span', { class: 'pv-ms-due back' }, backText(t, now)) : d && !t.done ? h('span', { class: 'pv-ms-due' + (d.tone ? ' ' + d.tone : '') }, d.text) : null,
              first ? h('span', { class: 'pv-ms-desc', dir: 'auto' }, first.slice(0, 160)) : null),
            t.archived ? h('span', { class: 'pv-ms-arch', title: 'In the archive', html: iconSvg('archive', 14) }) : null);
        }))
      : h('p', { class: 'fv-empty' }, 'No tasks in this milestone yet.');
    return h('div', { class: 'pv-note-ed' }, name,
      h('p', { class: 'note' }, g.todos.filter(t => t.done).length + ' of ' + plural(g.todos.length, 'task', 'tasks') + ' done. To change them, use the list; drag the milestone by its flag to move it.'),
      tasks,
      h('div', { class: 'pv-claude-row' },
        h('button', { id: 'pvMsCopy', class: 'btn btn-small', type: 'button', title: 'Copies this milestone and its open tasks with their descriptions, for a Claude chat', onclick: () => copyMilestone(p, m) }, iconEl('copy', 14), 'Copy for Claude'),
        OpenInClaude.button({ id: 'pvMsClaude', text: () => milestoneForClaude(p, m), project: p })),
      h('div', { class: 'pv-note-foot' },
        g.todos.some(canArchive) ? h('button', { id: 'pvMsArchive', class: 'btn btn-small', type: 'button', title: 'Every done task in it goes to the archive now',
          onclick: () => {
            archiveByHand(p, g.todos.filter(canArchive), m.name);
            if (milestoneArchived(p, m)) { sideMs = null; msSnap = null; closeSide(); root.focus({ preventScroll: true }); }
            else { const b = side && ($('#pvMsCopy', side)); if (b) b.focus(); }
          } }, iconEl('archive', 14), 'Archive done tasks') : null,
        h('button', { class: 'btn btn-danger btn-small', type: 'button', onclick: async () => {
          if (g.todos.length) {
            const ok = await Confirm.ask({ title: ['Delete ', h('bdi', null, m.name), '?'], body: 'Its ' + plural(g.todos.length, 'task goes', 'tasks go') + ' with it.', confirm: 'Delete milestone', danger: true });
            if (!ok) return;
          }
          p.todos = p.todos.filter(t => t.milestoneId !== m.id);
          p.milestones.splice(p.milestones.indexOf(m), 1);
          logActivity(p, 'Removed milestone: ' + m.name);
          changed(p);
          sideMs = null; msSnap = null;
          closeSide(); render(); Bubble.refresh();
          toast('Milestone deleted.');
        } }, 'Delete milestone')),
      h('p', { class: 'note' }, 'Saves as you type. Done closes it; Esc undoes the rename.'));
  }

  /* Notes: cards, newest first. A card opens the full note beside the view; Add note starts a new one there. */
  function notes(p) {
    const box = h('section', { class: 'pv-sec', 'data-sec': 'notes' }, secHead('Notes', null, addBtn('Add note', 'pvAddNoteBtn', () => openNote(p, null))));
    const list = [...p.notes].filter(n => n.title.trim() || n.text.trim()).sort((a, b) => b.at - a.at);
    if (!list.length) { box.append(h('p', { class: 'fv-empty' }, 'No notes yet.')); return box; }
    const shown = allNotes ? list : list.slice(0, 6);
    box.append(h('div', { class: 'pv-note-grid' }, shown.map(n => {
      const head = n.title.trim() || n.text.trim().split('\n')[0];
      const body = n.title.trim() ? n.text.trim() : n.text.trim().split('\n').slice(1).join(' ');
      return h('div', { class: 'pv-note-cell' },
        h('button', { class: 'pv-note-card' + (sideMode === 'note' && sideNote === n.id ? ' on' : ''), type: 'button', 'data-id': n.id, onclick: () => openNote(p, n.id) },
          h('span', { class: 'pv-note-h', dir: 'auto' }, head.slice(0, 120)),
          body ? h('span', { class: 'pv-note-b', dir: 'auto' }, body.replace(/\s+/g, ' ').slice(0, 220)) : null,
          h('time', { class: 'pv-note-at' }, fmtStamp(n.at))),
        h('button', { class: 'icon-btn pv-note-copy', type: 'button', 'data-copy': n.id, 'aria-label': 'Copy this note for Claude', title: 'Copy this note for Claude', html: iconSvg('copy', 14),
          onclick: e => { e.stopPropagation(); copyNote(p, n); } }));
    })));
    if (list.length > shown.length) box.append(h('button', { class: 'linkish', type: 'button', onclick: () => { allNotes = true; render(); } }, 'Show all ' + list.length + ' notes'));
    return box;
  }

  /* A label left empty shows the name the address suggests, as its placeholder; Tab in the empty field takes it. */
  function suggestInto(label, url) {
    const name = suggestLabel(url);
    label.placeholder = name || 'Label (optional)';
    label.title = name ? 'Left empty, the link shows ' + name + '. Tab takes it to edit.' : '';
  }
  function takeSuggestion(label) {
    label.addEventListener('keydown', e => {
      if (e.key !== 'Tab' || e.shiftKey || label.value || label.placeholder === 'Label (optional)') return;
      e.preventDefault();
      label.value = label.placeholder;
      label.dispatchEvent(new Event('input', { bubbles: true }));
    });
  }
  /* Ctrl+V with an address, in the project view with no field in use, opens Add link with it filled in. */
  const looksLikeAddress = s => !/\n/.test(s) && (!!winPathOf(s) || (!/\s/.test(s) && /^([a-z][a-z0-9+.-]*:\/\/|mailto:|www\.)/i.test(s) && !!safeUrl(s)));
  function pasteLink(text) {
    const p = P(); if (!p || !looksLikeAddress(text)) return false;
    if (adding !== 'link') openAdd('link');
    const url = $('#pvLinkUrl', root), label = $('#pvLinkLabel', root);
    if (!url) return false;
    url.value = text;
    url.dispatchEvent(new Event('input', { bubbles: true }));
    label.focus();
    $('.pv-add-link', root).scrollIntoView({ block: 'nearest' });
    return true;
  }
  document.addEventListener('paste', e => {
    const t = e.target;
    if (!root || Confirm.isOpen() || Panel.isOpen() || (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)))) return;
    const text = ((e.clipboardData && e.clipboardData.getData('text')) || '').trim();
    if (pasteLink(text)) e.preventDefault();
  });

  /* Links: open them in a click; Add link opens a small form only when asked for */
  function linkButton(l) {
    const t = linkTarget(l);
    const a = h('a', { class: 'btn link-btn' + (t.href ? '' : ' bad'), href: t.href, target: t.blank ? '_blank' : null, rel: t.blank ? 'noopener noreferrer' : null, title: t.title },
      iconEl(l.icon, 24), h('span', { dir: 'auto' }, t.name));
    if (!t.href) a.addEventListener('click', e => e.preventDefault());
    if (!t.win) return a;
    const copy = h('button', { class: 'icon-btn link-copy', type: 'button', 'aria-label': 'Copy the path', title: 'Copy the path: ' + t.win, html: iconSvg('copy', 14),   // a folder or file on this PC: and a copy of its path
      onclick: async () => { if (await copyText(t.win)) toast('Path copied: ' + t.win); else toast('The browser blocked copying. Try again.', 'error'); } });
    return h('span', { class: 'link-local' }, a, copy);
  }
  /* More shortcuts than a wheel holds are allowed; this says which show. */
  function shortcutWarning(p, extra = 0) {
    const n = p.links.filter(l => l.shortcut !== false).length + extra;
    return h('p', { class: 'note link-warn', role: 'status', hidden: n <= MAX_SHORTCUTS },
      'Only ' + MAX_SHORTCUTS + ' shortcuts fit in a building\u2019s wheel, so the first ' + MAX_SHORTCUTS + ' in the list show. Drag the links to choose which.');
  }
  function links(p) {
    const ed = editing && editing.key === 'links';
    const box = h('section', { class: 'pv-sec', 'data-sec': 'links' }, secHead('Links', 'links', addBtn('Add link', 'pvAddLinkBtn', () => openAdd('link'))));
    if (ed) {
      const list = h('div', { class: 'link-list' }), warn = h('div');
      const rerender = () => { list.replaceChildren(...p.links.map(l => linkRow(p, l, rerender, list))); warn.replaceChildren(shortcutWarning(p)); };
      rerender();
      box.append(list, warn, h('p', { class: 'note' }, 'Drag a link by its grip to move it, pick an icon, fix an address or a label, choose which are shortcuts, or remove a link. Done closes the section; Esc undoes everything since it opened.'));
      return box;
    }
    if (p.links.length) box.append(h('div', { class: 'links' }, p.links.map(linkButton)));
    else if (adding !== 'link') box.append(h('p', { class: 'fv-empty' }, 'No links yet.'));
    if (adding === 'link') {
      const url = h('input', { id: 'pvLinkUrl', class: 'field url', type: 'text', dir: 'ltr', inputmode: 'url', placeholder: 'Paste an address', 'aria-label': 'New link address', autocomplete: 'off', spellcheck: 'false' });
      let icon = 'web', picked = false;                      // guessed from the address as you type, until you pick one
      const pick = h('button', { id: 'pvLinkIcon', class: 'icon-pick', type: 'button', 'aria-haspopup': 'true', 'aria-label': 'Icon: ' + ICON_NAMES[icon] + '. Change it', html: iconSvg(icon, 24) });
      const setIcon = n => { icon = n; pick.innerHTML = iconSvg(n, 24); pick.setAttribute('aria-label', 'Icon: ' + ICON_NAMES[n] + '. Change it'); };
      const label = h('input', { class: 'field', type: 'text', dir: 'auto', placeholder: 'Label (optional)', 'aria-label': 'New link label', autocomplete: 'off' });
      const dupe = h('p', { class: 'note link-dupe', role: 'status', hidden: true });
      const addBtn = h('button', { class: 'btn btn-small btn-accent', type: 'button', onclick: () => add() }, 'Add');
      url.addEventListener('input', () => {
        if (!picked) setIcon(guessIcon(url.value));
        suggestInto(label, url.value);
        const key = addressKey(url.value), same = key && p.links.find(x => addressKey(x.url) === key);
        dupe.hidden = !same; addBtn.textContent = same ? 'Add anyway' : 'Add';
        if (same) dupe.textContent = 'This project already links this address, as ' + linkTarget(same).name + '.';
      });
      takeSuggestion(label);
      pick.addEventListener('mousedown', e => e.preventDefault());
      pick.addEventListener('click', e => { e.stopPropagation(); openPopover(pick, icon, n => { picked = true; setIcon(n); url.focus(); }); });
      const warn = shortcutWarning(p, 1);
      const sc = h('input', { id: 'pvLinkShortcut', type: 'checkbox', class: 'cb', checked: true, onchange: e => { warn.hidden = !e.target.checked || p.links.filter(l => l.shortcut !== false).length < MAX_SHORTCUTS; } });
      const add = () => {
        const u = url.value.trim(); if (!u) { url.focus(); return; }
        if (!safeUrl(u)) { toast('That address cannot be opened. Use https://, a folder path like C:\\Projects, or an app link like slack://.', 'error'); url.focus(); return; }
        const l = { id: uid('l'), label: label.value.trim().slice(0, 120), url: u.slice(0, 2000), icon: picked ? icon : guessIcon(u), shortcut: sc.checked };
        p.links.push(l);
        logActivity(p, 'Added link: ' + (l.label || l.url));
        adding = null; changed(p); render();
        const b = $('#pvAddLinkBtn', root); if (b) b.focus();
      };
      for (const inp of [url, label]) inp.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); add(); }
        else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeAdd(); const b = $('#pvAddLinkBtn', root); if (b) b.focus(); }
      });
      box.append(h('div', { class: 'pv-add-link', 'data-adding': 'link' },
        h('div', { class: 'link-form' }, pick, h('div', { class: 'link-fields' },
          h('label', { class: 'lbl', for: 'pvLinkUrl' }, 'Address'), url, dupe,
          h('label', { class: 'lbl', for: 'pvLinkLabel' }, 'Label'), label)),
        h('label', { class: 'check link-sc' }, sc, 'Add to shortcuts', h('span', { class: 'note' }, ' (right-click the building)')),
        warn,
        h('div', { class: 'inline link-actions' },
          addBtn,
          h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => closeAdd() }, 'Cancel'))));
      label.id = 'pvLinkLabel';
    }
    return box;
  }

  /* ---------- a note, open in full beside the view ---------- */
  let sideNote = null, noteSnap = null;
  function openNote(p, id) {
    finishEdit(); adding = null;
    if (side) closeSide();                                // a task or milestone open there closes as always first
    let n = id ? p.notes.find(x => x.id === id) : null;
    if (!n) { n = { id: uid('n'), title: '', text: '', at: Date.now() }; p.notes.push(n); noteSnap = null; }
    else noteSnap = clone(n);
    sideNote = n.id;
    openSide('note');
    const t = $(id ? '#pvNoteBody' : '#pvNoteTitle', side); if (t) t.focus();
  }
  /* Done or closing: keep what was written; an empty note is dropped. */
  function finishNote() {
    const p = P(); if (!p || !sideNote) return;
    const n = p.notes.find(x => x.id === sideNote);
    if (n) {
      if (!n.title.trim() && !n.text.trim()) { p.notes.splice(p.notes.indexOf(n), 1); changed(p, { touch: false }); }
      else if (!noteSnap) logActivity(p, 'Wrote a note' + (n.title.trim() ? ': ' + n.title.trim() : ''));
      else if (noteSnap.title !== n.title || noteSnap.text !== n.text) logActivity(p, 'Edited a note');
      changed(p);
    }
    sideNote = null; noteSnap = null;
  }
  /* Esc: a new note is dropped, an existing one goes back to how it was when it opened. */
  function cancelNote() {
    const p = P(); if (!p || !sideNote) return;
    const i = p.notes.findIndex(x => x.id === sideNote);
    if (i >= 0) { if (noteSnap) p.notes[i] = noteSnap; else p.notes.splice(i, 1); }
    changed(p, { touch: false });
    sideNote = null; noteSnap = null;
    side.remove(); side = null; sideMode = null;
    if (root.style.width) root.style.width = '';
    render();
    toast('Note changes undone.');
    const b = $('#pvAddNoteBtn', root); if (b) b.focus();
  }
  function noteEditor(p) {
    const n = p.notes.find(x => x.id === sideNote);
    if (!n) return h('p', { class: 'fv-empty' }, 'This note is gone.');
    const goes = p.milestones.find(m => m.id === defaultMilestone(p));
    const toTask = h('button', { id: 'pvNoteToTask', class: 'btn btn-small', type: 'button', disabled: !(n.title.trim() || n.text.trim()),
      title: 'Make it a task in ' + (goes ? goes.name : 'a new To do milestone') + ': the title names it, the text describes it',
      onclick: () => turnIntoTask(p, n.id) }, iconEl('task', 14), 'Turn into a task');
    const typed = () => { toTask.disabled = !(n.title.trim() || n.text.trim()); };   // an empty note has nothing to turn
    const title = h('input', { id: 'pvNoteTitle', class: 'field pv-note-title', type: 'text', dir: 'auto', maxlength: '200', value: n.title, placeholder: 'Title', 'aria-label': 'Note title', autocomplete: 'off',
      oninput: e => { n.title = e.target.value; changed(p, { touch: false }); refreshCard(n); typed(); },
      onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); const b = $('#pvNoteBody', side); if (b) b.focus(); } } });
    const body = h('textarea', { id: 'pvNoteBody', class: 'field pv-note-body', dir: 'auto', rows: '16', placeholder: 'Write the note', 'aria-label': 'Note text',
      oninput: e => { n.text = e.target.value.slice(0, 8000); changed(p, { touch: false }); refreshCard(n); typed(); } }, n.text);
    return h('div', { class: 'pv-note-ed' }, title, body,
      h('div', { class: 'pv-claude-row' },
        h('button', { id: 'pvNoteCopy', class: 'btn btn-small', type: 'button', title: 'Copies this note for a Claude chat', onclick: () => copyNote(p, n) }, iconEl('copy', 14), 'Copy for Claude'),
        OpenInClaude.button({ id: 'pvNoteClaude', text: () => noteForClaude(p, n), project: p })),
      h('div', { class: 'pv-note-foot' }, toTask,                        // as in the task panel: turn it on the left, delete on the right
        h('button', { id: 'pvNoteDelete', class: 'btn btn-danger btn-small', type: 'button', onclick: () => {
          p.notes.splice(p.notes.indexOf(n), 1);
          if (noteSnap) logActivity(p, 'Deleted a note');
          changed(p, { touch: false });
          sideNote = null; noteSnap = null;
          closeSide(); render();
          toast('Note deleted.');
        } }, 'Delete note')),
      h('p', { class: 'note' }, 'Written ' + fmtStamp(n.at) + '. Saves as you type; Esc undoes.'));
  }
  function refreshCard(n) {
    const card = root && $(`.pv-note-card[data-id="${n.id}"]`, root);
    if (!card) { if (root && !$(`.pv-note-card[data-id="${n.id}"]`, root) && (n.title.trim() || n.text.trim())) renderMainOnly(); return; }
    const hd = $('.pv-note-h', card); if (hd) hd.textContent = (n.title.trim() || n.text.trim().split('\n')[0]).slice(0, 120);
  }
  function renderMainOnly() {
    const p = P(); if (!p) return;
    const top = root.scrollTop;
    const old = $('[data-sec="notes"]', root);
    if (old) old.replaceWith(notes(p));
    root.scrollTop = top;
  }

  /* ---------- a task into a note, and a note into a task (0.1.54) ----------
     Some tasks are better kept as open ideas. A task's title and description become the note's; its milestone, date,
     repeat, shift, pin and star belong to a task, so they go. A note becomes a task where one added without @ goes,
     named by its title, or by its first line when it has none, with the rest as its description. The panel closes as
     it always does, the new one opens in its place, and the toast's Undo puts back exactly what was there. Neither is
     work: urgency stays. */
  const logged = (p, text) => { logActivity(p, text); return p.activity[p.activity.length - 1]; };
  const unlog = (p, e) => { const k = p.activity.indexOf(e); if (k >= 0) p.activity.splice(k, 1); };
  /* Undo puts back what the side panel showed, so the panel goes without closing as usual. */
  function dropSide() {
    sideTask = null; taskSnap = null; sideTicked = false; sideNote = null; noteSnap = null; sideMs = null; msSnap = null;
    if (side) { side.remove(); side = null; sideMode = null; }
    if (root && root.style.width) root.style.width = '';
  }
  function turnIntoNote(p, id) {
    closeSide();                                          // the task's Done and edit lines first, as for any close
    const i = p.todos.findIndex(x => x.id === id); if (i < 0) return;
    const t = p.todos[i], was = clone(t), pinned = p.pin === t.id, starred = p.star === t.id;
    const text = t.text.trim(), desc = (t.description || '').trim(), long = text.length > 200;    // a note's title holds 200
    const n = { id: uid('n'), title: long ? '' : text, text: (long ? text + (desc ? '\n\n' + desc : '') : desc).slice(0, 8000), at: Date.now() };
    p.todos.splice(i, 1); p.notes.push(n);
    if (pinned) p.pin = '';
    if (starred) p.star = '';
    const line = logged(p, 'Turned into a note: ' + text);
    changed(p); render(); Bubble.refresh();
    openNote(p, n.id);
    toast('Turned ' + text + ' into a note.', '', { label: 'Undo', run: () => {
      if (!getProject(p.id) || p.todos.some(x => x.id === was.id)) return;
      const showing = !!side && sideMode === 'note' && sideNote === n.id && openId === p.id;
      if (showing) dropSide();
      p.notes = p.notes.filter(x => x.id !== n.id);
      p.todos.splice(Math.min(i, p.todos.length), 0, was);
      if (!p.milestones.some(m => m.id === was.milestoneId)) was.milestoneId = homeMilestone(p).ms.id;   // its milestone is gone
      normalizeOrder(p);
      if (pinned && !pinnedTask(p)) p.pin = was.id;
      if (starred && !starredTask()) p.star = was.id;
      unlog(p, line);
      changed(p);
      if (root && openId === p.id) render();
      if (showing) { openTask(p, was.id); const b = side && $('#pvTaskToNote', side); if (b) b.focus(); }
    } });
  }
  function turnIntoTask(p, id) {
    closeSide();                                          // the note's Wrote or Edited line first, as for any close
    const i = p.notes.findIndex(x => x.id === id); if (i < 0) return;
    const n = p.notes[i], was = clone(n);
    const title = n.title.trim(), body = n.text.trim(), first = body.split('\n')[0].trim(), head = title || first;
    if (!head) return;
    const description = (title || head.length > 500 ? body : body.split('\n').slice(1).join('\n').trim()).slice(0, 8000);
    const lines = [], home = homeMilestone(p), ms = home.ms, folded = ms.collapsed;
    if (home.made) lines.push(logged(p, 'New milestone: ' + ms.name));
    ms.collapsed = false;
    const t = Object.assign(todo(head.slice(0, 500), ms.id), { description });
    p.notes.splice(i, 1); p.todos.push(t); normalizeOrder(p);
    lines.push(logged(p, 'Turned into a task: ' + t.text));
    changed(p); render(); Bubble.refresh();
    openTask(p, t.id);
    toast('Turned ' + t.text + ' into a task in ' + ms.name + '.', '', { label: 'Undo', run: () => {
      if (!getProject(p.id) || p.notes.some(x => x.id === was.id)) return;
      const showing = !!side && sideMode === 'task' && sideTask === t.id && openId === p.id;
      if (showing) dropSide();
      p.todos = p.todos.filter(x => x.id !== t.id);
      if (home.made && !p.todos.some(x => x.milestoneId === ms.id)) p.milestones = p.milestones.filter(m => m !== ms);
      else if (folded) ms.collapsed = true;
      p.notes.splice(Math.min(i, p.notes.length), 0, was);
      lines.forEach(e => unlog(p, e));
      changed(p);
      if (root && openId === p.id) render();
      if (showing) { openNote(p, was.id); const b = side && $('#pvNoteToTask', side); if (b) b.focus(); }
    } });
  }

  /* ---------- the more menu ---------- */
  function openMenu(anchor) {
    closeMenu();
    const p = P();
    const item = (label, fn, danger) => h('button', { class: 'pv-menu-item' + (danger ? ' danger' : ''), type: 'button', role: 'menuitem', onclick: () => { closeMenu(); fn(); } }, label);
    const inArchive = archivedTodos(p).length;
    menu = h('div', { class: 'pv-menu', role: 'menu', 'aria-label': 'More' },
      item(inArchive ? 'Archive (' + inArchive + ')' : 'Archive', () => openArchive(p)),
      item(leaderOf(p) ? 'Leader: ' + leaderName(leaderOf(p)) : 'Pick a leader', () => openSide('leader')),
      item('Copy for builder', () => copyBuilderCard(p)),
      item('Builder card in a Claude chat', () => OpenInClaude.go('chat', builderCard(p))),
      item('Load plan or tasks', () => openLoadPlan(p)),
      item('Export this project', () => exportProject(p)),
      item('Delete project', () => askDelete(p), true));
    root.append(menu);
    const rr = root.getBoundingClientRect(), ar = anchor.getBoundingClientRect();
    menu.style.top = Math.round(ar.bottom - rr.top + root.scrollTop + 6) + 'px';
    menu.style.right = Math.round(rr.right - ar.right) + 'px';
    anchor.setAttribute('aria-expanded', 'true');
    menu.firstChild.focus();
    menu.addEventListener('keydown', e => {
      const items = $$('.pv-menu-item', menu), i = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    });
    setTimeout(() => document.addEventListener('mousedown', outsideMenu), 0);
  }
  function outsideMenu(e) { if (menu && !menu.contains(e.target) && e.target.id !== 'pvMore' && !e.target.closest('#pvMore')) closeMenu(); }
  function closeMenu() {
    if (!menu) return;
    menu.remove(); menu = null;
    document.removeEventListener('mousedown', outsideMenu);
    const b = root && $('#pvMore', root); if (b) b.setAttribute('aria-expanded', 'false');
  }
  function exportProject(p) {
    (async () => {
      const art = p.art.has ? await Store.getArt(p.id) : null;
      const data = { app: 'nullovation-city', kind: 'project', version: 2, exportedAt: new Date().toISOString(), project: clone(p), art: art ? { dataUrl: art } : null,
        leader: await Leaders.carry(leaderOf(p)) };                          // its leader travels with it (0.1.51)
      downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }), slug(p.name) + '.json');
      toast('Project exported. Import backup in the side menu adds it to any city.');
    })();
  }

  /* Load a plan: pick the file the nullovation-city skill wrote, or paste it. It replaces the project's
     description, milestones, and tasks after a clear warning; ideas are added to the notes. */
  function openLoadPlan(p) {
    const err = h('p', { class: 'plan-err', role: 'alert', hidden: true });
    const text = h('textarea', { id: 'planText', class: 'field plan-text', rows: '10', spellcheck: 'false', placeholder: '{ "app": "nullovation-city", "kind": "tasks", ... }', 'aria-label': 'Paste the plan or tasks here',
      oninput: () => { go.disabled = !text.value.trim(); err.hidden = true; } });
    const file = h('input', { id: 'planFile', type: 'file', accept: 'application/json,.json', hidden: true, onchange: async e => {
      const f = e.target.files[0]; e.target.value = '';
      if (!f) return;
      try { text.value = await f.text(); go.disabled = false; err.hidden = true; await load(); } catch (x) { fail('That file could not be read.'); }
    } });
    const fail = msg => { err.textContent = msg; err.hidden = false; };
    const load = async () => {
      let data, plan;
      try { data = JSON.parse(text.value); }
      catch (x) { fail('That is not valid JSON. Copy all of it, from the first { to the last }.'); return; }
      if (isTasksFile(data)) {
        let pack;
        try { pack = readTasks(data); } catch (x) { fail(x.message); return; }
        pickMilestone(pack);
        return;
      }
      try { plan = readPlan(data); } catch (x) { fail(x.message); return; }
      const nt = plan.milestones.reduce((n, m) => n + m.tasks.length, 0);
      const ok = await Confirm.ask({
        title: ['Replace the plan for ', h('bdi', null, p.name), '?'],
        body: 'Its description, ' + plural(p.milestones.length, 'milestone', 'milestones') + ', and ' + plural(p.todos.length, 'task', 'tasks') + ' are replaced by the plan\u2019s ' +
          plural(plan.milestones.length, 'milestone', 'milestones') + ' and ' + plural(nt, 'task', 'tasks') + '.' +
          (plan.ideas.length ? ' ' + plural(plan.ideas.length, 'idea is', 'ideas are') + ' added to its notes.' : '') +
          (plan.name && plan.name !== p.name ? ' It is renamed to ' + plan.name + '.' : '') +
          ' Its building, place, notes, links, urgency, and history stay.',
        confirm: 'Replace the plan', danger: true,
      });
      if (!ok) return;
      Panel.close();
      const r = applyPlan(p, plan);
      changed(p); render(); Bubble.refresh(); MapView.invalidate(); Menu.refresh();
      toast('Plan loaded: ' + plural(r.milestones, 'milestone', 'milestones') + ', ' + plural(r.tasks, 'task', 'tasks') + (r.ideas ? ', ' + plural(r.ideas, 'idea', 'ideas') + ' in notes' : '') + '.');
    };
    /* A tasks file adds its tasks; you choose the milestone they go into. */
    const pickMilestone = pack => {
      const sug = pack.milestone.toLowerCase();
      const match = p.milestones.find(m => m.name.trim().toLowerCase() === sug);
      const cur = currentGroup(p);
      const def = match ? match.id : (!pack.milestone && cur && cur.ms ? cur.ms.id : (!pack.milestone && p.milestones.length ? p.milestones[p.milestones.length - 1].id : 'new'));
      const newName = pack.milestone || (p.milestones.length ? 'New milestone' : 'To do');
      const sel = h('select', { id: 'planMilestone', class: 'field', 'aria-label': 'Milestone for the new tasks' },
        p.milestones.map(m => h('option', { value: m.id, selected: m.id === def }, m.name)),
        h('option', { value: 'new', selected: def === 'new' }, 'A new milestone: ' + newName));
      const add = () => {
        Panel.close();
        const ms = addTasks(p, pack.tasks, sel.value === 'new' ? { name: newName } : { id: sel.value });
        changed(p); render(); Bubble.refresh(); MapView.invalidate(); Menu.refresh();
        toast(plural(pack.tasks.length, 'task', 'tasks') + ' added to ' + ms.name + '.');
      };
      Panel.open(['Add tasks to ', h('bdi', null, p.name)], [
        h('p', { class: 'recap-range' }, 'These are added to the milestone you pick. Nothing already in the project changes.'),
        h('ol', { class: 'plan-tasks' }, pack.tasks.map(x => h('li', { dir: 'auto' }, h('b', null, x.text), x.description ? h('span', { class: 'note' }, ' ' + x.description.split('\n')[0].slice(0, 140)) : null))),
        h('label', { class: 'lbl', for: 'planMilestone' }, 'Add them to'), sel,
        h('div', { class: 'inline plan-actions' }, h('button', { id: 'planAdd', class: 'btn btn-accent', type: 'button', onclick: add }, 'Add ' + plural(pack.tasks.length, 'task', 'tasks')))]);
      sel.focus();
    };
    const go = h('button', { id: 'planLoad', class: 'btn btn-accent', type: 'button', disabled: true, onclick: load }, 'Load');
    Panel.open(['Load a plan or tasks into ', h('bdi', null, p.name)], [
      h('p', { class: 'recap-range' }, 'Both come from the nullovation-city skill in a Claude chat. A tasks file adds its tasks to a milestone you pick. A plan replaces this project\u2019s description, milestones, and tasks, and adds its ideas to your notes; you see what changes before anything does.'),
      h('div', { class: 'inline plan-pick' }, h('button', { class: 'btn', type: 'button', onclick: () => file.click() }, iconEl('plus', 14), 'Choose the file'), h('span', { class: 'note' }, 'or paste it below')),
      file, text, err,
      h('div', { class: 'inline plan-actions' }, go)]);
    text.focus();
  }

  /* ---------- the second-level panel: the building, or the activity ---------- */
  function openSide(mode) {
    closeMenu();
    if (!side) {
      side = h('aside', { id: 'pvSide', class: 'pv-side', role: 'region', tabindex: '-1' });
      $('#mapWrap').append(side);
      dropOn(side);
    }
    sideMode = mode;
    renderSide();
    placeSide();
    side.focus({ preventScroll: true });
    MapView.glideBeside(openId, rightEdge());
  }
  /* The side panel docks beside the view. Where both do not fit, the view narrows while the side panel
     is open, so nothing overlaps; on the smallest screens the side panel covers the view instead. */
  function placeSide() {
    if (!side || !root) return;
    const W = $('#mapWrap').clientWidth, sw = side.offsetWidth, full = Math.min(880, W);
    let mw = full;
    if (full + sw + 2 > W) mw = W - sw - 2 >= 420 ? W - sw - 2 : full;
    const was = root.offsetWidth;
    root.style.width = mw === full ? '' : mw + 'px';
    side.style.left = (mw + sw + 2 <= W ? mw + 2 : Math.max(0, W - sw)) + 'px';
    if (Math.abs(root.offsetWidth - was) > 1) render();    // the banner redraws at the new width
  }
  window.addEventListener('resize', () => placeSide());
  /* A round file from a chat, or its answers, dropped on a task's panel (W1, P2): the line lights up while a file is
     over the panel, and the drop attaches it. An archived task is to read, so it takes none. */
  function dropOn(el) {
    const task = () => { const p = P(), t = p && sideMode === 'task' && p.todos.find(x => x.id === sideTask); return t && !t.archived ? { p, t } : null; };
    const files = e => !!(e.dataTransfer && [...e.dataTransfer.types].includes('Files'));
    const show = on => {
      const slot = $('.pv-round-slot', el), had = slot && $('.pv-round-drop', slot), at = task();
      if (on && slot && !had && at) slot.prepend(Rounds.dropLine(at.t));
      if (!on && had) had.remove();
    };
    el.addEventListener('dragover', e => { if (!files(e) || !task()) return; e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; show(true); });
    el.addEventListener('dragleave', e => { if (!el.contains(e.relatedTarget)) show(false); });
    el.addEventListener('drop', async e => {
      if (!files(e)) return;
      e.preventDefault();
      show(false);
      const at = task(); if (!at) return;
      await Rounds.dropFile(at.p, at.t, e.dataTransfer.files[0]);
    });
  }
  /* What Open in Claude sends for a task: its copy (the round's answers written in for a chat, C1), Make a wizard round's
     request (M1), and the round's file for Cowork when its path is known. */
  const taskClaude = (p, t) => ({ text: kind => taskForClaude(p, t, Date.now(), { kind }),
    round: isOpenTask(t) ? kind => taskForClaude(p, t, Date.now(), { kind, ask: true }) : null, files: () => Rounds.files(t) });
  /* A round came, changed or went: its card and its hats, redrawn in place, so a description being typed keeps its place. */
  function refreshRounds() {
    const p = P(); if (!p || !root) return;
    const typing = document.activeElement && side && side.contains(document.activeElement) && /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (!typing) { render(); return; }
    const t = sideMode === 'task' && p.todos.find(x => x.id === sideTask), slot = side && $('.pv-round-slot', side);
    if (t && slot) slot.replaceChildren(...[Rounds.card(p, t, { readOnly: !!t.archived })].filter(Boolean));
    for (const b of $$('li.task .round-hat', root)) { const x = p.todos.find(y => y.id === b.dataset.task), nu = x && Rounds.hatButton(p, x, 'row-round'); if (nu) b.replaceWith(nu); else b.remove(); }
  }
  function closeSide() {
    if (!side) return;
    if (sideMode === 'note') finishNote();
    if (sideMode === 'task') finishTask();
    if (sideMode === 'milestone') finishMilestone();
    side.remove(); side = null; sideMode = null;
    if (root && root.style.width) { root.style.width = ''; render(); }
    if (openId) MapView.glideBeside(openId, rightEdge());
  }
  function renderSide() {
    const p = P(); if (!p || !side) return;
    const head = (title) => h('div', { class: 'pv-top' }, h('h2', { class: 'pv-title small', dir: 'auto' }, title),
      h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close ' + title.toLowerCase(), title: 'Close', html: iconSvg('close', 18), onclick: () => { closeSide(); root.focus({ preventScroll: true }); } }));
    if (sideMode === 'note') {
      side.replaceChildren(h('div', { class: 'pv-top' }, h('h2', { class: 'pv-title small' }, 'Note'),
        h('div', { class: 'pv-actions' },
          h('button', { class: 'btn btn-accent btn-small', type: 'button', onclick: () => { closeSide(); render(); const b = $('#pvAddNoteBtn', root); if (b) b.focus(); } }, 'Done'),
          h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close the note', title: 'Close', html: iconSvg('close', 18), onclick: () => { closeSide(); render(); } }))),
        noteEditor(p));
      return;
    }
    if (sideMode === 'task' || sideMode === 'milestone') {
      const label = sideMode === 'task' ? 'Task' : 'Milestone';
      side.replaceChildren(h('div', { class: 'pv-top' }, h('h2', { class: 'pv-title small' }, label),
        h('div', { class: 'pv-actions' },
          h('button', { class: 'btn btn-accent btn-small', type: 'button', onclick: () => { closeSide(); render(); } }, 'Done'),
          h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close the ' + label.toLowerCase(), title: 'Close', html: iconSvg('close', 18), onclick: () => { closeSide(); render(); } }))),
        sideMode === 'task' ? taskEditor(p) : milestoneEditor(p));
      return;
    }
    if (sideMode === 'leader') {                                            // who leads the building (0.1.51)
      side.replaceChildren(head('Leader'), Leaders.pickList(p, () => render()));
      return;
    }
    if (sideMode === 'archive') {
      const top = side.scrollTop;
      side.replaceChildren(head('Archive'), archiveView(p));
      side.scrollTop = top;
      return;
    }
    if (sideMode === 'urgency') {
      const u = p.urgency, urg = urgencyOf(p);
      const pick = system => {
        if (u.system === system) return;
        u.system = system; u.pickedAt = Date.now();
        logActivity(p, 'Urgency: ' + urgencyName(p));
        changed(p); render(); Bubble.refresh();
      };
      const opt = (system, title, body, extra) => h('label', { class: 'urg-opt' + (u.system === system ? ' on' : '') },
        h('input', { type: 'radio', name: 'urgSystem', checked: u.system === system, onchange: () => pick(system) }),
        h('span', { class: 'urg-opt-text' }, h('b', null, title), h('span', null, body), extra || null));
      const days = u.system === 'pace' ? h('span', { class: 'urg-days' }, 'One task at least every ',
        h('input', { id: 'pvUrgDays', class: 'field num', type: 'number', min: '1', max: '30', value: String(u.days), 'aria-label': 'Days between tasks',
          onchange: e => { const v = clamp(parseInt(e.target.value, 10) || 1, 1, 30); u.days = v; e.target.value = v; logActivity(p, 'Urgency: ' + urgencyName(p)); changed(p); render(); Bubble.refresh(); } }),
        u.days === 1 ? ' day' : ' days') : null;
      side.replaceChildren(h('div', { class: 'pv-top' }, h('h2', { class: 'pv-title small' }, 'Urgency'),
        h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close urgency', title: 'Close', html: iconSvg('close', 18), onclick: () => { closeSide(); root.focus({ preventScroll: true }); } })),
        h('p', { class: 'urg-why ' + (urg.color || 'calm') }, h('span', { class: 'b-urg-dot', 'aria-hidden': 'true' }),
          urg.color ? (urg.color === 'red' ? 'Red: ' : 'Yellow: ') + urg.reasons.join('. ') + '.' : 'No bubble right now.' + (u.system === 'none' ? ' Due dates still raise red bubbles: any task with less than 2 days left.' : '')),
        h('div', { class: 'urg-opts', role: 'radiogroup', 'aria-label': 'Urgency system' },
          opt('none', 'None', 'Only due dates raise bubbles: any open task with less than 2 days left, or overdue, turns the building red.'),
          opt('finish', 'Work until finished', 'A bubble stays until every task is finished, showing how many are left. Red when no task was finished in the last 24 hours, yellow once you finish one or press I worked!.'),
          opt('pace', 'One task per day or more', 'A bubble when no task was finished in the period: yellow after one period, red after two. Finishing a task, or I worked!, clears it until the period passes again.', days)),
        u.system !== 'none' ? h('div', { class: 'inline urg-worked' },
          h('button', { class: 'btn btn-accent', type: 'button', onclick: () => workedNow(p) }, 'I worked!'),
          h('span', { class: 'note' }, 'Counts as finishing a task.')) : null,
        h('p', { class: 'note urg-last' }, u.lastWorked ? 'Last worked ' + relAgo(u.lastWorked) + ', from a finished task or I worked!.' : 'No finished task or I worked! yet.'));
      return;
    }
    if (sideMode === 'activity') {
      const ev = [...(p.activity || [])].sort((a, b) => b.at - a.at);
      const days = [];
      for (const e of ev) {
        const label = dayLabel(e.at);
        if (!days.length || days[days.length - 1].label !== label) days.push({ label, items: [] });
        days[days.length - 1].items.push(e);
      }
      side.replaceChildren(head('Activity'),
        ev.length ? h('div', { class: 'pv-activity' }, days.map(d => h('div', { class: 'pv-day' },
          h('h4', { class: 'pv-day-h' }, d.label),
          h('ol', null, d.items.map(e => h('li', null, h('time', null, fmtTime(e.at)), h('span', { dir: 'auto' }, e.text)))))))
          : h('p', { class: 'fv-empty' }, 'Nothing recorded yet.'));
      return;
    }
    const custom = p.art.has ? Art.get(p.id) : null;
    const file = h('input', { type: 'file', accept: 'image/png,image/gif,.png,.gif', hidden: true,
      onchange: async e => { const f = e.target.files[0]; e.target.value = ''; if (f) { await uploadArt(p, f); render(); } } });
    const own = h('div', { class: 'pv-own' },
      h('div', { class: 'inline' },
        h('button', { class: 'btn', type: 'button', onclick: () => file.click() }, iconEl('plus', 14), custom ? 'Replace your own art' : 'Upload your own art'),
        custom ? h('button', { class: 'btn btn-danger btn-small', type: 'button', onclick: async () => { await removeArt(p); render(); } }, 'Remove it') : null),
      custom ? h('label', { class: 'check' }, h('input', { type: 'checkbox', class: 'cb', checked: p.art.includesPlot,
        onchange: e => { p.art.includesPlot = e.target.checked; MapView.dropCache(p.id); changed(p); render(); } }), 'Art brings its own plot') : null,
      h('p', { class: 'note' }, custom
        ? 'Your art is showing: ' + custom.w + ' by ' + custom.h + ' px' + (custom.animated ? ', ' + custom.count + ' frames' : ', still') + '. Picking a generic building below removes it.'
        : 'A transparent PNG, or a GIF for a live building, 256 px wide in the new standard (128 px works too).'),
      file);
    side.replaceChildren(head('Building'), own,
      h('h3', { class: 'pv-h' }, 'Particles'),                                  // what its ticks set off (Celebrations, T2)
      h('p', { class: 'note' }, 'Every tick bursts round the building. Point at one to see it.'),
      Celebrate.picker(p, id => { const b = side.querySelector('.pv-particles'); if (b) for (const x of b.children) { const on = x.dataset.kind === id; x.classList.toggle('on', on); x.setAttribute('aria-pressed', String(on)); } }),
      h('h3', { class: 'pv-h' }, 'Generic buildings'),
      Picker.grid({ current: p.art.has ? null : p.generic, onPick: id => pickGeneric(p, id), zoom: 1 }));
  }
  function dayLabel(at) {
    const d = new Date(at), t = new Date();
    const key = x => x.getFullYear() + '-' + x.getMonth() + '-' + x.getDate();
    const y = new Date(t); y.setDate(t.getDate() - 1);
    if (key(d) === key(t)) return 'Today';
    if (key(d) === key(y)) return 'Yesterday';
    return fmtDate(at);
  }
  const fmtTime = at => new Date(at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  async function pickGeneric(p, id) {
    const g = GENERICS.find(x => x.id === id);
    if (p.art.has) {
      const ok = await Confirm.ask({ title: 'Switch to the ' + g.name.toLowerCase() + '?', body: 'Your uploaded art for this project is removed, and the generic building takes its place.', confirm: 'Switch building', danger: true });
      if (!ok) return;
      await Store.deleteArt(p.id); Art.drop(p.id); p.art.has = false;
    }
    if (p.generic === id && !p.art.has) return;
    p.generic = id;
    MapView.dropCache(p.id);
    logActivity(p, 'Building: ' + g.name);
    changed(p);
    render();
  }
  async function downloadBuilding(p) {
    let url = null;
    if (p.art.has) url = await Store.getArt(p.id);
    else if (p.generic) url = (GENERICS.find(g => g.id === p.generic) || {}).url;
    if (!url) { MapView.blockPng(p); return; }
    const blob = dataUrlToBlob(url);
    const ext = blob.type === 'image/gif' ? 'gif' : 'png';
    downloadBlob(blob, slug(p.name) + '-building.' + ext);
    toast('Building saved as a ' + ext.toUpperCase() + (ext === 'gif' ? ', live' : '') + '.');
  }

  /* ---------- rows used while a section is open ---------- */
  function linkRow(p, l, rerender, list) {
    const grip = h('button', { class: 'icon-btn grip link-grip', type: 'button', 'aria-label': 'Move ' + (l.label || l.url || 'this link') + ': drag, or use the up and down arrows', title: 'Drag to move', html: iconSvg('grip', 14) });
    grip.addEventListener('pointerdown', e => dragLink(e, p, row, list, rerender));
    grip.addEventListener('keydown', e => {
      if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
      e.preventDefault();
      const i = p.links.indexOf(l), j = i + (e.key === 'ArrowUp' ? -1 : 1);
      if (j < 0 || j >= p.links.length) return;
      p.links.splice(i, 1); p.links.splice(j, 0, l); changed(p, { touch: false }); rerender();
      const again = $(`.link-edit[data-id="${l.id}"] .link-grip`, root); if (again) again.focus();
    });
    const pick = h('button', { class: 'icon-pick', type: 'button', 'aria-haspopup': 'true', 'aria-label': 'Icon: ' + ICON_NAMES[l.icon] + '. Change it', html: iconSvg(l.icon, 24) });
    pick.addEventListener('click', e => {
      e.stopPropagation();
      openPopover(pick, l.icon, name => {
        l.icon = name; changed(p); rerender();
        const b = $(`[data-id="${l.id}"] .icon-pick`, root); if (b) b.focus();
      });
    });
    const label = h('input', { class: 'field', type: 'text', dir: 'auto', value: l.label, placeholder: 'Label (optional)', 'aria-label': 'Link label', autocomplete: 'off',
      oninput: e => { l.label = e.target.value; changed(p); } });
    const url = h('input', { class: 'field url', type: 'text', dir: 'ltr', inputmode: 'url', value: l.url, placeholder: 'https://, C:\\folder, or slack://', 'aria-label': 'Link address', autocomplete: 'off', spellcheck: 'false',
      oninput: e => { l.url = e.target.value; suggestInto(label, l.url); changed(p); } });
    suggestInto(label, l.url); takeSuggestion(label);
    const del = h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Delete link', title: 'Delete link', html: iconSvg('close', 14),
      onclick: () => { const i = p.links.indexOf(l); p.links.splice(i, 1); changed(p); rerender(); undoRemove(p, l, i); } });
    const sc = h('label', { class: 'check link-sc', title: 'Shows on the building\u2019s shortcut wheel' },
      h('input', { type: 'checkbox', class: 'cb', checked: l.shortcut !== false, 'aria-label': 'Shortcut: ' + (l.label || l.url),
        onchange: e => { l.shortcut = e.target.checked; changed(p, { touch: false }); rerender(); } }), 'Shortcut');
    const row = h('div', { class: 'link-edit', 'data-id': l.id }, grip, pick, h('div', { class: 'link-fields' }, url, label, sc), del);
    return row;
  }
  /* A deleted link can come back from the toast, to its place, for a few seconds: while the section is open, or after
     Done. Esc on the section already brings it back, so then Undo does nothing. */
  function undoRemove(p, l, i) {
    toast('Link removed: ' + linkTarget(l).name, '', { label: 'Undo', run: () => {
      if (!getProject(p.id) || p.links.some(x => x.id === l.id)) return;
      p.links.splice(Math.min(i, p.links.length), 0, l);
      if (!(editing && editing.key === 'links' && openId === p.id)) logActivity(p, 'Added link: ' + (l.label || l.url));
      changed(p);
      if (openId === p.id) render();
      toast('Link back: ' + linkTarget(l).name);
    } });
  }
  /* A link follows the pointer by its grip, among the others; the list's order is the wheel's order. */
  function dragLink(e, p, row, list, rerender) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    e.preventDefault();
    const pid = e.pointerId, y0 = e.clientY;
    row.classList.add('dragging'); document.body.classList.add('pv-dragging');
    const move = ev => {
      if (ev.pointerId !== pid) return;
      ev.preventDefault();
      edgeScroll(ev.clientY, y0);
      const others = [...list.children].filter(x => x !== row);
      const target = others.find(x => { const b = x.getBoundingClientRect(); return ev.clientY < b.top + b.height / 2; });
      if (target) { if (target.previousElementSibling !== row) list.insertBefore(row, target); }
      else if (list.lastElementChild !== row) list.append(row);
    };
    const up = ev => {
      if (ev.pointerId !== pid) return;
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); window.removeEventListener('pointercancel', up);
      row.classList.remove('dragging'); document.body.classList.remove('pv-dragging');
      const ids = [...list.children].map(x => x.dataset.id), was = p.links.map(l => l.id).join();
      p.links.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id));
      if (p.links.map(l => l.id).join() !== was) changed(p, { touch: false });
      rerender();
      const again = $(`.link-edit[data-id="${row.dataset.id}"] .link-grip`, root); if (again) again.focus();
    };
    window.addEventListener('pointermove', move, { passive: false }); window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up);
  }
  function openPopover(anchor, current, onPick) {
    closePopover();
    pop = h('div', { class: 'icon-pop', role: 'group', 'aria-label': 'Choose an icon' },
      LINK_ICONS.map(name => h('button', { type: 'button', title: ICON_NAMES[name], 'aria-label': ICON_NAMES[name], 'aria-pressed': String(name === current), html: iconSvg(name, 24),
        onclick: e => { e.stopPropagation(); closePopover(); onPick(name); } })));
    root.append(pop);
    const rr = root.getBoundingClientRect(), ar = anchor.getBoundingClientRect();
    pop.style.left = Math.round(ar.left - rr.left + root.scrollLeft) + 'px';
    pop.style.top = Math.round(ar.bottom - rr.top + root.scrollTop + 8) + 'px';
    (pop.querySelector('[aria-pressed="true"]') || pop.firstChild).focus();
    setTimeout(() => document.addEventListener('mousedown', outside), 0);
  }
  function outside(e) { if (pop && !pop.contains(e.target)) closePopover(); }
  function closePopover() { if (pop) { pop.remove(); pop = null; } document.removeEventListener('mousedown', outside); }

  async function uploadArt(p, f) {
    const isGif = f.type === 'image/gif' || /\.gif$/i.test(f.name), isPng = f.type === 'image/png' || /\.png$/i.test(f.name);
    if (!isGif && !isPng) { toast('Blocks take a PNG, or a GIF for a live building.', 'error'); return; }
    let url, info;
    try { url = await readAsDataURL(f); info = await Art.probe(url); }
    catch (e) { toast((e && e.message) || 'That image could not be read. Export it again and retry.', 'error'); return; }
    if (info.w > Art.MAX_W) { toast('This image is ' + info.w + ' px wide. Blocks are 128 or 256 px wide: export it at its native pixel size.', 'error'); return; }
    const kept = await Store.putArt(p.id, url);
    try { await Art.set(p.id, url); } catch (e) { toast('That image could not be read. Export it again and retry.', 'error'); return; }
    p.art.has = true;
    logActivity(p, 'Uploaded its own art');
    changed(p);
    const t = info.trimmed, cut = [['left', t.left], ['top', t.top], ['right', t.right], ['bottom', t.bottom]].filter(x => x[1] > 0);
    const notes = [];
    if (cut.length) notes.push('Trimmed empty margins (' + cut.map(([k, v]) => k + ' ' + v).join(', ') + ' px).');
    if (info.w !== 128 && info.w !== 256) notes.push('It is ' + info.w + ' px wide, so it is scaled to fit the plot, which can soften pixels.');
    if (!kept) toast('Art added for this session only: this browser is not saving it. Export a backup to keep it.', 'error');
    else toast(('Art added' + (info.frames > 1 ? ', ' + info.frames + ' frames.' : '.')) + (notes.length ? ' ' + notes.join(' ') : ''));
  }
  async function removeArt(p) {
    await Store.deleteArt(p.id);
    Art.drop(p.id);
    p.art.has = false;
    logActivity(p, 'Removed its own art');
    changed(p);
    toast(p.generic ? 'Art removed. The generic building is back.' : 'Art removed. The placeholder block is back.');
  }
  async function askDelete(p) {
    const ok = await Confirm.ask({
      title: ['Delete ', h('bdi', null, p.name), '?'],
      body: 'Its building, todos, links, and block art are removed from this browser. Export it first from the more menu if you might want it back.',
      confirm: 'Delete project', danger: true,
    });
    if (!ok) return;
    const name = p.name;
    close();
    await deleteProject(p.id);
    toast('Deleted ' + name + '.');
  }

  return {
    open, close, escape, render: () => { if (root) render(); },
    scrollBy: dy => { const el = side && side.matches(':hover') ? side : root; if (el) el.scrollTop += dy; },
    isOpen: () => !!root, currentId: () => openId, shows: id => !!root && openId === id, rightEdge,
    openTask: (pid, tid) => { open(pid); const p = getProject(pid); if (p) openTask(p, tid); },   // from the bubble: the view, with the task open beside it
    popoverOpen: () => !!pop, closePopover, refreshRounds,
    /* A task taken back out by the one-line add's Undo (0.1.56): its panel goes, with nothing written for it. */
    closeTaskOf: tid => {
      if (!side || sideMode !== 'task' || sideTask !== tid) return;
      side.remove(); side = null; sideMode = null; sideTask = null; taskSnap = null;
      if (root && root.style.width) root.style.width = '';
      render();
    },
  };
})();
