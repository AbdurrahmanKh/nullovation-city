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
/* A link's icon, guessed from its address. */
function guessIcon(url) {
  if (winPathOf(url)) return 'folder';
  const u = String(url || '').toLowerCase();
  if (/notion\.so|docs\.google|confluence|\.pdf|\.docx?\b/.test(u)) return 'doc';
  if (/asana|jira|linear\.app|trello|clickup|monday\.com/.test(u)) return 'task';
  if (/figma|miro|dribbble|behance|canva/.test(u)) return 'design';
  if (/github|gitlab|bitbucket|localhost|codepen|replit/.test(u)) return 'code';
  if (/slack|claude\.ai|chatgpt|discord|teams\.microsoft|whatsapp|t\.me/.test(u)) return 'chat';
  if (/drive\.google|dropbox|onedrive|^file:/.test(u)) return 'folder';
  return 'web';
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
    closePopover(); closeMenu(); closeSide();
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
    if (side && sideMode === 'task') { cancelTask(); return true; }
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
      h('div', { class: 'pv-cols' }, h('div', { class: 'pv-col' }, todos(p)), h('div', { class: 'pv-col' }, notes(p), links(p))));
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
        p.urgency.system !== 'none' ? h('button', { id: 'pvWorked', class: 'btn btn-small', type: 'button', title: 'Counts as finishing a task, for ' + urgencyName(p), onclick: () => workedNow(p) }, 'I worked!') : null));
  }
  function workedNow(p) {
    iWorked(p); changed(p); render(); Bubble.refresh();
    toast('Checked in. ' + (p.urgency.system === 'finish' ? 'Work until finished stays yellow for 24 hours.' : 'No bubble until ' + (p.urgency.days === 1 ? 'tomorrow at this time.' : p.urgency.days + ' days from now.')));
  }

  /* About: what is next (worked out from the todos), then what the project is, beside the picture */
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
    box.append(whatIsNext(p));
    const dl = deadlineInfo(p.deadline);
    if (dl) box.append(h('p', { class: 'pv-deadline ' + (dl.cls || '') }, dl.text));
    if (leader) box.append(h('p', { class: 'pv-leader', dir: 'auto' }, (leader.title ? leader.title + ': ' : '') + leader.text.replace(/\s+/g, ' ').trim()));
    box.append(p.description.trim() ? h('div', { class: 'fv-desc' }, paragraphs(p.description)) : h('p', { class: 'fv-empty' }, 'No description yet. The pencil adds one.'));
    box.append(h('div', { class: 'pv-about-btns' },
      h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => openSide('activity') }, iconEl('clock', 14), 'Activity'),
      h('button', { class: 'btn btn-quiet btn-small', type: 'button', title: 'Copies this project\u2019s full status as text for a Claude chat', onclick: () => copyProjectStatus(p) }, iconEl('copy', 14), 'Copy status')));
    return box;
  }
  /* The current milestone and its next open task. Overdue shows in red with a !. */
  function whatIsNext(p) {
    const box = h('div', { class: 'pv-next' }, h('span', { class: 'lbl' }, 'What is next'));
    const t = nextTask(p);
    if (!t) {
      box.append(h('p', { class: 'fv-empty' }, p.milestones.length ? 'Every task is done. Add a task to a milestone to plan what comes next.' : 'No milestones yet. Add one under Todos to plan what is next.'));
      return box;
    }
    const g = currentGroup(p), ms = g.ms;
    const d = dueInfo(t), late = d && d.tone === 'late';
    box.append(h('button', { class: 'pv-next-ms', type: 'button', title: 'Open this milestone', onclick: () => openMilestone(p, ms.id) },
      h('span', { class: 'ms-flag', html: iconSvg('flag', 14) }), h('span', { dir: 'auto' }, ms.name), h('span', { class: 'ms-count' }, countText(g))));
    box.append(h('button', { id: 'pvNextTask', class: 'pv-next-task' + (late ? ' late' : ''), type: 'button', dir: 'auto', title: 'Open this task', onclick: () => openTask(p, t.id) },
      late ? h('span', { class: 'pv-late-mark', 'aria-label': 'Overdue' }, '!') : null, h('span', null, t.text)));
    box.append(h('div', { class: 'pv-next-row' },
      d ? h('span', { class: 'due ' + (d.tone || '') }, d.text) : h('span', { class: 'note' }, 'No due date'),
      h('button', { class: 'btn btn-quiet btn-small', type: 'button', title: 'Copies this task, with its description, for a Claude chat', onclick: () => copyTask(p, t) }, iconEl('copy', 14), 'Copy for Claude')));
    const others = p.todos.filter(x => !x.done && x !== t && x.due && dueInfo(x) && dueInfo(x).tone === 'late').length;
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
      if (!g.ms) continue;
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
      for (const t of g.todos) ul.append(taskRow(p, t));
      if (adding === 'task:' + m.id) {
        const inp = h('input', { class: 'field', type: 'text', dir: 'auto', autocomplete: 'off', placeholder: 'New task, then Enter', 'aria-label': 'New task in ' + m.name,
          onkeydown: e => {
            if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeAdd(); const b = $(`.ms[data-msid="${m.id}"] .ms-plus`, root); if (b) b.focus(); return; }
            if (e.key !== 'Enter') return;
            e.preventDefault();
            const text = e.target.value.trim().slice(0, 500);
            adding = null;
            if (text) { p.todos.push(todo(text, m.id)); normalizeOrder(p); logActivity(p, 'Added todo: ' + text); changed(p); Bubble.refresh(); }
            render();
            const b = $(`.ms[data-msid="${m.id}"] .ms-plus`, root); if (b) b.focus();
          },
          onblur: () => setTimeout(() => { const cur = root && $('li.task-add .field', root); if (adding === 'task:' + m.id && !(cur && cur === document.activeElement)) closeAdd(); }, 150) });
        ul.append(h('li', { class: 'task-add', 'data-adding': 'task' }, inp));
      }
      list.append(h('div', { class: 'ms', 'data-msid': m.id }, row, ul));
    }
    if (!p.milestones.length && adding !== 'milestone') list.append(h('p', { class: 'fv-empty' }, 'No milestones yet. Every task lives in one.'));
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
  function taskRow(p, t) {
    const li = h('li', { class: 'task' + (t.done ? ' done' : '') + (sideMode === 'task' && sideTask === t.id ? ' on' : ''), 'data-id': t.id });
    const cb = h('input', { type: 'checkbox', class: 'cb', checked: t.done, 'aria-label': 'Done: ' + t.text, onchange: e => {
      t.done = e.target.checked; t.doneAt = t.done ? Date.now() : null;
      if (t.done) markWorked(p);
      logActivity(p, (t.done ? 'Done: ' : 'Reopened: ') + t.text);
      changed(p); render(); Bubble.refresh();
      const again = $(`.task[data-id="${t.id}"] .cb`, root); if (again) again.focus();
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
    li.addEventListener('pointerdown', e => { if (e.target.closest('.cb')) return; dragTask(e, p, li); });
    const d = t.done ? null : dueInfo(t);
    li.append(...[cb, title, (t.description || '').trim() ? h('span', { class: 'task-has-desc', title: 'Has a description', html: iconSvg('doc', 12) }) : null,
      d ? h('span', { class: 'due ' + (d.tone || '') }, (d.tone === 'late' ? '! ' : '') + d.text) : null].filter(Boolean));
    return li;
  }
  /* Up or down one place, crossing into the neighbouring milestone at an edge. */
  function moveTodo(p, t, dir) {
    const groups = groupsOf(p).filter(g => g.ms);
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
    p.todos = groups.flatMap(x => x.todos);
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
      p.todos = order.concat(p.todos.filter(x => !order.includes(x)));
      normalizeOrder(p);
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
  let sideTask = null, taskSnap = null, sideMs = null, msSnap = null;
  function openTask(p, id) {
    finishEdit(); adding = null;
    if (side) closeSide();
    const t = p.todos.find(x => x.id === id); if (!t) return;
    sideTask = id; taskSnap = clone(t);
    openSide('task');
    const f = $('#pvTaskDesc', side); if (f) f.focus();
  }
  function finishTask() {
    const p = P(); if (!p || !sideTask) return;
    const t = p.todos.find(x => x.id === sideTask);
    if (t && taskSnap) {
      if (!t.text.trim()) t.text = taskSnap.text || 'Untitled task';
      if (t.done !== taskSnap.done) logActivity(p, (t.done ? 'Done: ' : 'Reopened: ') + t.text);
      if (t.text !== taskSnap.text || t.description !== taskSnap.description || t.due !== taskSnap.due) logActivity(p, 'Edited task: ' + t.text);
      changed(p, { touch: t.text !== taskSnap.text || t.description !== taskSnap.description || t.due !== taskSnap.due || t.done !== taskSnap.done });
    }
    sideTask = null; taskSnap = null;
  }
  function cancelTask() {
    const p = P(); if (!p || !sideTask) return;
    const i = p.todos.findIndex(x => x.id === sideTask);
    if (i >= 0 && taskSnap) p.todos[i] = taskSnap;
    changed(p, { touch: false });
    sideTask = null; taskSnap = null;
    side.remove(); side = null; sideMode = null;
    if (root.style.width) root.style.width = '';
    render(); Bubble.refresh();
    toast('Task changes undone.');
  }
  function taskEditor(p) {
    const t = p.todos.find(x => x.id === sideTask);
    if (!t) return h('p', { class: 'fv-empty' }, 'This task is gone.');
    const ms = p.milestones.find(m => m.id === t.milestoneId);
    const title = h('input', { id: 'pvTaskTitle', class: 'field pv-note-title', type: 'text', dir: 'auto', maxlength: '500', value: t.text, 'aria-label': 'Task title', autocomplete: 'off',
      oninput: e => { t.text = e.target.value; changed(p, { touch: false }); const b = $(`.task[data-id="${t.id}"] .task-title`, root); if (b) b.textContent = t.text; } });
    const done = h('input', { type: 'checkbox', class: 'cb', checked: t.done, onchange: e => { t.done = e.target.checked; t.doneAt = t.done ? Date.now() : null; if (t.done) markWorked(p); changed(p, { touch: false }); render(); Bubble.refresh(); } });
    const due = h('input', { id: 'pvTaskDue', class: 'field', type: 'date', value: t.due, 'aria-label': 'Due date',
      onchange: e => { t.due = parseYmd(e.target.value) != null ? e.target.value : ''; changed(p, { touch: false }); render(); } });
    const d = dueInfo(t);
    const desc = h('textarea', { id: 'pvTaskDesc', class: 'field pv-note-body', dir: 'auto', rows: '14', placeholder: 'What this task is, in full: what done looks like, where things are, anything Claude should know', 'aria-label': 'Task description',
      oninput: e => { t.description = e.target.value.slice(0, 8000); changed(p, { touch: false }); } }, t.description || '');
    return h('div', { class: 'pv-note-ed' },
      h('p', { class: 'pv-task-ms' }, h('span', { class: 'ms-flag', html: iconSvg('flag', 14) }), ms ? ms.name : ''),
      title,
      h('div', { class: 'inline pv-task-meta' },
        h('label', { class: 'check' }, done, 'Done'),
        h('span', { class: 'lbl' }, 'Due'), due,
        h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => { t.due = ''; due.value = ''; changed(p, { touch: false }); render(); } }, 'Clear'),
        d && !t.done ? h('span', { class: 'due ' + (d.tone || '') }, (d.tone === 'late' ? '! ' : '') + d.text) : null),
      h('span', { class: 'lbl' }, 'Description'), desc,
      h('div', { class: 'pv-note-foot' },
        h('button', { class: 'btn btn-small', type: 'button', onclick: () => copyTask(p, t) }, iconEl('copy', 14), 'Copy for Claude'),
        h('button', { class: 'btn btn-danger btn-small', type: 'button', onclick: () => {
          p.todos.splice(p.todos.indexOf(t), 1);
          logActivity(p, 'Removed todo: ' + t.text);
          changed(p);
          sideTask = null; taskSnap = null;
          closeSide(); render(); Bubble.refresh();
          toast('Task deleted.');
        } }, 'Delete task')),
      h('p', { class: 'note' }, 'Saves as you type. Done closes it; Esc undoes everything since it opened.'));
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
    const tasks = g.todos.length
      ? h('ol', { class: 'pv-ms-tasks', 'aria-label': 'The tasks in this milestone' }, g.todos.map(t => {
          const d = dueInfo(t, now), first = (t.description || '').trim().split('\n')[0];
          return h('li', { class: 'pv-ms-task' + (t.done ? ' done' : '') },
            h('span', { class: 'pv-ms-box' + (t.done ? ' done' : ''), 'aria-hidden': 'true' }),
            h('span', { class: 'pv-ms-body' },
              h('span', { class: 'pv-ms-text', dir: 'auto' }, t.text, h('span', { class: 'visually-hidden' }, t.done ? ' (done)' : '')),
              d && !t.done ? h('span', { class: 'pv-ms-due' + (d.tone ? ' ' + d.tone : '') }, d.text) : null,
              first ? h('span', { class: 'pv-ms-desc', dir: 'auto' }, first.slice(0, 160)) : null));
        }))
      : h('p', { class: 'fv-empty' }, 'No tasks in this milestone yet.');
    return h('div', { class: 'pv-note-ed' }, name,
      h('p', { class: 'note' }, g.todos.filter(t => t.done).length + ' of ' + plural(g.todos.length, 'task', 'tasks') + ' done. To change them, use the list; drag the milestone by its flag to move it.'),
      tasks,
      h('div', { class: 'pv-note-foot' },
        h('button', { id: 'pvMsCopy', class: 'btn btn-small', type: 'button', title: 'Copies this milestone, its open tasks with their descriptions, and the project\u2019s About, for a Claude chat', onclick: () => copyMilestone(p, m) }, iconEl('copy', 14), 'Copy for Claude'),
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

  /* Links: open them in a click; Add link opens a small form only when asked for */
  function linkButton(l) {
    const win = winPathOf(l.url);
    if (win) {                                            // a folder or file on this PC: Explorer or the browser, plus a copy of the path
      const inExplorer = explorerLinks();
      const attrs = { class: 'btn link-btn', href: inExplorer ? explorerHref(win) : fileUrlOf(win), title: (inExplorer ? 'Opens in File Explorer: ' : 'Opens in the browser: ') + win };
      if (!inExplorer) { attrs.target = '_blank'; attrs.rel = 'noopener noreferrer'; }
      const a = h('a', attrs, iconEl(l.icon, 24), h('span', { dir: 'auto' }, l.label || win));
      const copy = h('button', { class: 'icon-btn link-copy', type: 'button', 'aria-label': 'Copy the path', title: 'Copy the path: ' + win, html: iconSvg('copy', 14),
        onclick: async () => { if (await copyText(win)) toast('Path copied: ' + win); else toast('The browser blocked copying. Try again.', 'error'); } });
      return h('span', { class: 'link-local' }, a, copy);
    }
    const url = safeUrl(l.url);
    const a = h('a', { class: 'btn link-btn' + (url ? '' : ' bad'), href: url, target: '_blank', rel: 'noopener noreferrer', title: url || 'This address cannot be opened. Fix it with the pencil.' },
      iconEl(l.icon, 24), h('span', { dir: 'auto' }, l.label || l.url || 'Link'));
    if (!url) a.addEventListener('click', e => e.preventDefault());
    return a;
  }
  function links(p) {
    const ed = editing && editing.key === 'links';
    const box = h('section', { class: 'pv-sec', 'data-sec': 'links' }, secHead('Links', 'links', addBtn('Add link', 'pvAddLinkBtn', () => openAdd('link'))));
    if (ed) {
      const list = h('div');
      const rerender = () => list.replaceChildren(...p.links.map(l => linkRow(p, l, rerender)));
      rerender();
      box.append(list, h('p', { class: 'note' }, 'Pick an icon, fix a label or an address, or remove a link. Done closes the section; Esc undoes everything since it opened.'));
      return box;
    }
    if (p.links.length) box.append(h('div', { class: 'links' }, p.links.map(linkButton)));
    else if (adding !== 'link') box.append(h('p', { class: 'fv-empty' }, 'No links yet.'));
    if (adding === 'link') {
      const url = h('input', { id: 'pvLinkUrl', class: 'field url', type: 'text', dir: 'ltr', inputmode: 'url', placeholder: 'Paste an address', 'aria-label': 'New link address', autocomplete: 'off', spellcheck: 'false' });
      let icon = 'web', picked = false;                      // guessed from the address as you type, until you pick one
      const pick = h('button', { id: 'pvLinkIcon', class: 'icon-pick', type: 'button', 'aria-haspopup': 'true', 'aria-label': 'Icon: ' + ICON_NAMES[icon] + '. Change it', html: iconSvg(icon, 24) });
      const setIcon = n => { icon = n; pick.innerHTML = iconSvg(n, 24); pick.setAttribute('aria-label', 'Icon: ' + ICON_NAMES[n] + '. Change it'); };
      url.addEventListener('input', () => { if (!picked) setIcon(guessIcon(url.value)); });
      pick.addEventListener('mousedown', e => e.preventDefault());
      pick.addEventListener('click', e => { e.stopPropagation(); openPopover(pick, icon, n => { picked = true; setIcon(n); url.focus(); }); });
      const label = h('input', { class: 'field', type: 'text', dir: 'auto', placeholder: 'Label (optional)', 'aria-label': 'New link label', autocomplete: 'off' });
      const add = () => {
        const u = url.value.trim(); if (!u) { url.focus(); return; }
        if (!safeUrl(u)) { toast('That address cannot be opened. Use https://, a folder path like C:\\Projects, or an app link like slack://.', 'error'); url.focus(); return; }
        const l = { id: uid('l'), label: label.value.trim().slice(0, 120), url: u.slice(0, 2000), icon: picked ? icon : guessIcon(u) };
        p.links.push(l);
        logActivity(p, 'Added link: ' + (l.label || l.url));
        adding = null; changed(p); render();
        const b = $('#pvAddLinkBtn', root); if (b) b.focus();
      };
      for (const inp of [url, label]) inp.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); add(); }
        else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeAdd(); const b = $('#pvAddLinkBtn', root); if (b) b.focus(); }
      });
      box.append(h('div', { class: 'pv-add-link', 'data-adding': 'link' }, pick, url, label,
        h('button', { class: 'btn btn-small', type: 'button', onclick: add }, 'Add'),
        h('button', { class: 'btn btn-quiet btn-small', type: 'button', onclick: () => closeAdd() }, 'Cancel')));
    }
    return box;
  }

  /* ---------- a note, open in full beside the view ---------- */
  let sideNote = null, noteSnap = null;
  function openNote(p, id) {
    finishEdit(); adding = null;
    if (side && sideMode === 'note') finishNote();
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
    const title = h('input', { id: 'pvNoteTitle', class: 'field pv-note-title', type: 'text', dir: 'auto', maxlength: '200', value: n.title, placeholder: 'Title', 'aria-label': 'Note title', autocomplete: 'off',
      oninput: e => { n.title = e.target.value; changed(p, { touch: false }); refreshCard(n); },
      onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); const b = $('#pvNoteBody', side); if (b) b.focus(); } } });
    const body = h('textarea', { id: 'pvNoteBody', class: 'field pv-note-body', dir: 'auto', rows: '16', placeholder: 'Write the note', 'aria-label': 'Note text',
      oninput: e => { n.text = e.target.value.slice(0, 8000); changed(p, { touch: false }); refreshCard(n); } }, n.text);
    return h('div', { class: 'pv-note-ed' }, title, body,
      h('div', { class: 'pv-note-foot' },
        h('span', { class: 'note' }, 'Written ' + fmtStamp(n.at) + '. Saves as you type; Esc undoes.'),
        h('span', { class: 'inline pv-foot-actions' },
        h('button', { id: 'pvNoteCopy', class: 'btn btn-small', type: 'button', title: 'Copies this note, with the project\u2019s About, for a Claude chat', onclick: () => copyNote(p, n) }, iconEl('copy', 14), 'Copy for Claude'),
        h('button', { class: 'btn btn-danger btn-small', type: 'button', onclick: () => {
          p.notes.splice(p.notes.indexOf(n), 1);
          if (noteSnap) logActivity(p, 'Deleted a note');
          changed(p, { touch: false });
          sideNote = null; noteSnap = null;
          closeSide(); render();
          toast('Note deleted.');
        } }, 'Delete note'))));
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

  /* ---------- the more menu ---------- */
  function openMenu(anchor) {
    closeMenu();
    const p = P();
    const item = (label, fn, danger) => h('button', { class: 'pv-menu-item' + (danger ? ' danger' : ''), type: 'button', role: 'menuitem', onclick: () => { closeMenu(); fn(); } }, label);
    menu = h('div', { class: 'pv-menu', role: 'menu', 'aria-label': 'More' },
      item('Copy for builder', () => copyBuilderCard(p)),
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
      const data = { app: 'nullovation-city', kind: 'project', version: 2, exportedAt: new Date().toISOString(), project: clone(p), art: art ? { dataUrl: art } : null };
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
  function linkRow(p, l, rerender) {
    const pick = h('button', { class: 'icon-pick', type: 'button', 'aria-haspopup': 'true', 'aria-label': 'Icon: ' + ICON_NAMES[l.icon] + '. Change it', html: iconSvg(l.icon, 24) });
    pick.addEventListener('click', e => {
      e.stopPropagation();
      openPopover(pick, l.icon, name => {
        l.icon = name; changed(p); rerender();
        const b = $(`[data-id="${l.id}"] .icon-pick`, root); if (b) b.focus();
      });
    });
    const label = h('input', { class: 'field', type: 'text', dir: 'auto', value: l.label, placeholder: 'Label', 'aria-label': 'Link label', autocomplete: 'off',
      oninput: e => { l.label = e.target.value; changed(p); } });
    const url = h('input', { class: 'field url', type: 'text', dir: 'ltr', inputmode: 'url', value: l.url, placeholder: 'https://, C:\\folder, or slack://', 'aria-label': 'Link address', autocomplete: 'off', spellcheck: 'false',
      oninput: e => { l.url = e.target.value; changed(p); } });
    const del = h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Delete link', html: iconSvg('close', 14),
      onclick: () => { p.links.splice(p.links.indexOf(l), 1); changed(p); rerender(); } });
    return h('div', { class: 'link-edit', 'data-id': l.id }, pick, label, url, del);
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
    popoverOpen: () => !!pop, closePopover,
  };
})();
