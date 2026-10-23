/* Open in Claude: opens Claude with a copy for Claude already filled in, through the Claude app's claude:// links, or
   Claude Code's own claude-cli:// link for a terminal. The text is only filled in, never sent, and it goes on the
   clipboard too, for when the app is not on this computer.
   Since 0.1.63 it is one small panel (Open in Claude Panel, Round 1, and Abdurrahman's sketch of it): five buttons,
   Chat, Cowork, Code, Terminal and Copy (A1), and under them the one folder Cowork, Code and Terminal open in, with a >
   to pick another when the building links several. Cowork takes that one folder, and no more folders or file links.
   For a task it has two tabs (A2): Build it, the work itself, and Think, which asks Claude for a decision wizard round
   about the task, or with Make a brainstorming round, a brainstorm (A3); either attaches to the task. A copy's text may
   differ by where it goes: a chat gets a round's answers written in, since it cannot read the round's file (C1). */
const OpenInClaude = (() => {
  const MAX_Q = 13500;                      // the app fills in about 14,000 characters; anything longer goes by clipboard
  const MAX_TERM = 5000;                    // Claude Code's terminal links fill in at most 5,000
  const BASE = { chat: 'claude://claude.ai/new', cowork: 'claude://cowork/new', code: 'claude://code/new', terminal: 'claude-cli://open' };
  const FOLDER_KEY = 'nullovation-city:claudeFolder';   // the folder picked in each building, in this browser
  const maxOf = kind => (kind === 'terminal' ? MAX_TERM : MAX_Q);
  /* The terminal link takes a local folder only: no network or UNC paths, no .. parts. */
  const termOk = f => !!f && !/^\\\\/.test(f) && !/(^|\\)\.\.(\\|$)/.test(f);
  let panel = null, owner = null;

  /* A project's local links: folders, and files (a path whose last part has an extension). */
  function places(p) {
    const folders = [], files = [];
    for (const l of (p && p.links) || []) {
      let w = winPathOf(l.url);
      if (!w) continue;
      if (w.length > 3) w = w.replace(/\\+$/, '');
      const list = w.length > 3 && /\.[A-Za-z0-9]{1,6}$/.test(w.split('\\').pop()) ? files : folders;
      if (!list.includes(w)) list.push(w);
    }
    return { folders, files };
  }
  /* The link for one place, with its one folder; Cowork also takes the files given (a task's round file). */
  function href(kind, text, folder = '', files = []) {
    const parts = [];
    if (text && text.length <= maxOf(kind)) parts.push('q=' + encodeURIComponent(text));
    if (kind === 'cowork') {
      if (folder) parts.push('folder=' + encodeURIComponent(folder));
      files.forEach(f => parts.push('file=' + encodeURIComponent(f)));
    }
    if (kind === 'code' && folder) parts.push('folder=' + encodeURIComponent(folder));
    if (kind === 'terminal' && termOk(folder)) parts.push('cwd=' + encodeURIComponent(folder));
    return BASE[kind] + (parts.length ? '?' + parts.join('&') : '');
  }
  async function hand(text, kind) {
    const copied = await copyText(text);
    if (text.length > maxOf(kind)) toast('Too long to fill in, so it is on your clipboard: paste it into Claude.');
    else toast(copied ? 'Opening Claude with this filled in. It is on your clipboard too.' : 'Opening Claude with this filled in.');
  }
  /* Opens one kind straight away, for places that offer only one, such as the builder card. */
  function go(kind, text, folder = '') {
    hand(text, kind);
    const a = h('a', { href: href(kind, text, folder), hidden: true });
    document.body.append(a); a.click(); a.remove();
  }
  const base = path => path.split('\\').filter(Boolean).pop() || path;

  /* ---------- the folder picked in a building ---------- */
  function savedFolders() { try { const v = JSON.parse(localStorage.getItem(FOLDER_KEY) || '{}'); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } }
  function folderOf(p, folders) {
    const want = p ? savedFolders()[p.id] : '';
    return folders.includes(want) ? want : (folders[0] || '');
  }
  function keepFolder(p, f) {
    if (!p) return;
    const v = savedFolders();
    if (f && f !== places(p).folders[0]) v[p.id] = f; else delete v[p.id];
    try { localStorage.setItem(FOLDER_KEY, JSON.stringify(v)); } catch (e) { /* this visit only */ }
  }

  /* ---------- the panel ---------- */
  /* opts: { text: kind => string, project, copied: the toast after Copy, id, quiet, small }, and for a task:
     think: (kind, { brainstorm }) => string, the copy that asks for a round or a brainstorm (Think), and files: () =>
     [path], the round's file for Cowork. */
  function open(btn, opts) {
    close();
    const p = opts.project || null, folders = p ? places(p).folders : [];
    const st = { tab: 'build', brainstorm: false, folder: folderOf(p, folders), listing: false };
    panel = h('div', { class: 'oc-panel', role: 'dialog', 'aria-label': 'Open in Claude' });
    const textFor = kind => (st.tab === 'think' && opts.think ? opts.think(kind, { brainstorm: st.brainstorm }) : opts.text(kind));
    const files = () => (opts.files ? opts.files() : []);

    function tile(kind, label, icon, { note = '', ok = true, title = '', off = '' } = {}) {
      const kids = [h('span', { class: 'ic', html: iconSvg(icon, 18) }), h('span', { class: 'oc-tile-label' }, label), note ? h('span', { class: 'oc-tile-note' }, note) : null];
      if (!ok) return h('span', { class: 'oc-tile off', 'aria-disabled': 'true', 'data-kind': kind, title: off }, kids);
      if (kind === 'copy') return h('button', { class: 'oc-tile', type: 'button', 'data-kind': kind, title, onclick: () => copyNow() }, kids);
      const text = textFor(kind);
      return h('a', { class: 'oc-tile', href: href(kind, text, st.folder, kind === 'cowork' ? files() : []), 'data-kind': kind, title,
        onclick: () => { hand(text, kind); setTimeout(close, 0); } }, kids);
    }
    async function copyNow() {
      const ok = await copyText(textFor(undefined));
      const said = st.tab === 'think' ? (st.brainstorm ? 'Copied: asking Claude for a brainstorm on this task.' : 'Copied: asking Claude for a wizard round on this task.') : (opts.copied || 'Copied for Claude.');
      toast(ok ? said : 'The browser blocked copying. Try again.', ok ? '' : 'error');
      if (ok) close(true);
    }
    const what = () => (st.tab === 'think' ? (st.brainstorm ? 'asking Claude for a brainstorm on this task' : 'asking Claude for a wizard round on this task') : 'with this filled in');
    function render() {
      const kids = [];
      if (opts.think) {
        const tab = (id, name, label, icon) => h('button', { id, class: 'oc-tab' + (st.tab === name ? ' on' : ''), type: 'button', role: 'tab', 'aria-selected': String(st.tab === name),
          onclick: () => { if (st.tab === name) return; st.tab = name; render(); const b = $('#' + id, panel); if (b) b.focus(); } },
          h('span', { class: 'ic', 'aria-hidden': 'true', html: icon }), label);
        kids.push(h('div', { class: 'oc-tabs', role: 'tablist' },
          tab('ocTabBuild', 'build', 'Build it', iconSvg('claude', 14)),
          tab('ocTabThink', 'think', 'Think', hatSvg(14))));
        if (st.tab === 'think') kids.push(h('label', { class: 'oc-brain', for: 'ocBrainstorm' },
          h('input', { id: 'ocBrainstorm', type: 'checkbox', checked: st.brainstorm, onchange: e => { st.brainstorm = e.target.checked; render(); const c = $('#ocBrainstorm', panel); if (c) c.focus(); } }),
          'Make a brainstorming round'));
      }
      const f = st.folder, need = p ? 'Add a link to a folder on this computer to open it there' : 'Opens from a project that links a folder on this computer';
      /* The status brief's Copy comes first, as its own row, then the Claude tiles (SideBar Cleanup, 0.1.64). */
      if (opts.copyFirst) kids.push(h('button', { class: 'oc-tile oc-wide', type: 'button', 'data-kind': 'copy', title: 'Copies it, to paste anywhere', onclick: () => copyNow() },
        h('span', { class: 'ic', html: iconSvg('copy', 18) }), h('span', { class: 'oc-tile-label' }, opts.copyFirst)));
      kids.push(h('div', { class: 'oc-tiles' + (opts.copyFirst ? ' four' : '') },
        tile('chat', 'Chat', 'chat', { note: 'no folder', title: 'A new Claude chat ' + what() }),
        tile('cowork', 'Cowork', 'cowork', { title: 'A new Cowork task ' + what() + (f ? ', in ' + f : '') }),
        tile('code', 'Code', 'code', { ok: !!f, off: need, title: 'A new Claude Code session in ' + f + ', ' + what() }),
        tile('terminal', 'Terminal', 'terminal', { ok: termOk(f), off: f ? 'A terminal opens only in a folder on this computer' : need,
          title: 'Claude Code in a new terminal in ' + f + ', ' + what() + '. Works once Claude Code has had a prompt in a terminal on this computer.' }),
        opts.copyFirst ? null : tile('copy', 'Copy', 'copy', { title: 'Copies it, to paste anywhere' })));
      const line = h('div', { class: 'oc-folder' });
      if (!f) line.append(h('span', { class: 'oc-folder-none' }, p ? 'No folder link: Code and Terminal need one.' : 'No project folder: Chat, Cowork or Copy.'));
      else if (folders.length < 2) line.append(h('b', null, 'Folder:'), ' ', h('span', { class: 'oc-folder-path', dir: 'ltr', title: f }, f));
      else {
        line.append(h('button', { id: 'ocFolderPick', class: 'oc-folder-pick', type: 'button', 'aria-expanded': String(st.listing), title: 'Pick the folder to open in',
          onclick: () => { st.listing = !st.listing; render(); const b = $('#ocFolderPick', panel); if (b) b.focus(); } },
          h('b', null, 'Folder:'), ' ', h('span', { class: 'oc-folder-path', dir: 'ltr', title: f }, f), h('span', { class: 'oc-folder-more', 'aria-hidden': 'true' }, st.listing ? '∨' : '>')));
      }
      kids.push(line);
      if (st.listing && folders.length > 1) kids.push(h('div', { class: 'oc-folders', role: 'listbox', 'aria-label': 'Folders' }, folders.map(x =>
        h('button', { class: 'oc-folder-opt' + (x === f ? ' on' : ''), type: 'button', role: 'option', 'aria-selected': String(x === f), dir: 'ltr', title: x,
          onclick: () => { st.folder = x; st.listing = false; keepFolder(p, x); render(); const b = $('#ocFolderPick', panel); if (b) b.focus(); } },
          h('span', { class: 'oc-folder-name' }, base(x)), h('span', { class: 'oc-folder-full' }, x)))));
      panel.replaceChildren(...kids);
    }
    render();
    document.body.append(panel);
    place(btn);
    owner = btn; btn.setAttribute('aria-expanded', 'true');
    const first = $('.oc-tab.on', panel) || $('.oc-tile:not(.off)', panel);
    if (first) first.focus();
    panel.addEventListener('keydown', e => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      const row = $$(document.activeElement && document.activeElement.classList.contains('oc-tab') ? '.oc-tab' : '.oc-tile:not(.off)', panel), i = row.indexOf(document.activeElement);
      if (i < 0) return;
      e.preventDefault();
      row[(i + (e.key === 'ArrowRight' ? 1 : row.length - 1)) % row.length].focus();
    });
    setTimeout(() => { document.addEventListener('mousedown', outside, true); window.addEventListener('scroll', onScroll, true); window.addEventListener('resize', onScroll); }, 0);
  }
  /* Under its button, or over it when there is no room below; kept on the screen. */
  function place(btn) {
    const r = btn.getBoundingClientRect(), mw = panel.offsetWidth, mh = panel.offsetHeight;
    panel.style.left = Math.round(Math.max(8, Math.min(r.left, innerWidth - mw - 8))) + 'px';
    panel.style.top = Math.round(r.bottom + 6 + mh > innerHeight - 8 ? Math.max(8, r.top - 6 - mh) : r.bottom + 6) + 'px';
  }
  function outside(e) { if (panel && !panel.contains(e.target) && !(owner && owner.contains(e.target))) close(); }
  function onScroll(e) { if (e && e.type === 'scroll' && panel && panel.contains(e.target)) return; close(); }
  function close(refocus) {
    if (!panel) return false;
    panel.remove(); panel = null;
    document.removeEventListener('mousedown', outside, true);
    window.removeEventListener('scroll', onScroll, true); window.removeEventListener('resize', onScroll);
    if (owner) { owner.setAttribute('aria-expanded', 'false'); if (refocus) owner.focus(); }
    owner = null;
    return true;
  }
  /* The one button for a copy for Claude: it opens the panel. Its words are Open in Claude, or opts.label (the status
     brief's); with opts.icon it is the Claude icon alone, as in a list's rows (SideBar Cleanup, 0.1.64). */
  function button(opts) {
    const title = opts.think ? 'Opens this in Claude, or copies it: build it, or think it through with a wizard round first' : 'Opens this in Claude, filled in and ready to send, or copies it';
    const btn = opts.icon
      ? h('button', { id: opts.id, class: 'icon-btn oc-btn oc-icon' + (opts.cls ? ' ' + opts.cls : ''), type: 'button', 'aria-haspopup': 'dialog', 'aria-expanded': 'false',
          'aria-label': 'Open in Claude' + (opts.name ? ': ' + opts.name : ''), title, html: iconSvg('claude', 14) })
      : h('button', { id: opts.id, class: 'btn oc-btn' + (opts.small === false ? '' : ' btn-small') + (opts.quiet ? ' btn-quiet' : '') + (opts.cls ? ' ' + opts.cls : ''), type: 'button', 'aria-haspopup': 'dialog', 'aria-expanded': 'false',
          title: opts.title || title }, iconEl('claude', 14), opts.label || 'Open in Claude');
    btn.addEventListener('click', e => { e.stopPropagation(); if (owner === btn) close(); else open(btn, opts); });
    return btn;
  }
  /* A task's panel: Build it sends the task; Think, on an open task, asks for a round or a brainstorm about it (Open in
     Claude Panel, A2, A3); Copy copies either; Cowork gets the round's file. The project view, Due this week and All
     tasks share it. */
  const forTask = (p, t) => ({ text: kind => taskForClaude(p, t, Date.now(), { kind }), copied: 'Task copied for Claude.', project: p, name: t.text,
    think: isOpenTask(t) ? (kind, o = {}) => taskForClaude(p, t, Date.now(), { kind, ask: o.brainstorm ? 'brainstorm' : true }) : null, files: () => Rounds.files(t) });
  return { button, forTask, go, places, close, isOpen: () => !!panel };
})();
