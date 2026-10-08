/* Open in Claude: opens the Claude desktop app with a Copy for Claude text already filled in, through the app's
   claude:// links. Chat starts a new chat; Cowork starts a task with the project's local folders and files attached;
   Claude Code starts a session in the project's first folder. The text is only filled in, never sent, and it goes on
   the clipboard too, for when the app is not on this computer. */
const OpenInClaude = (() => {
  const MAX_Q = 13500;                      // the app fills in about 14,000 characters; anything longer goes by clipboard
  const BASE = { chat: 'claude://claude.ai/new', cowork: 'claude://cowork/new', code: 'claude://code/new' };
  let menu = null, owner = null;

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
  function href(kind, text, pl = { folders: [], files: [] }) {
    const parts = [];
    if (text && text.length <= MAX_Q) parts.push('q=' + encodeURIComponent(text));
    if (kind === 'cowork') {
      pl.folders.forEach(f => parts.push('folder=' + encodeURIComponent(f)));
      pl.files.forEach(f => parts.push('file=' + encodeURIComponent(f)));
    }
    if (kind === 'code' && pl.folders[0]) parts.push('folder=' + encodeURIComponent(pl.folders[0]));
    return BASE[kind] + (parts.length ? '?' + parts.join('&') : '');
  }
  async function hand(text) {
    const copied = await copyText(text);
    if (text.length > MAX_Q) toast('Too long to fill in, so it is on your clipboard: paste it into Claude.');
    else toast(copied ? 'Opening Claude with this filled in. It is on your clipboard too.' : 'Opening Claude with this filled in.');
  }
  /* Opens one kind straight away, for places that offer only one, such as the builder card. */
  function go(kind, text, pl) {
    hand(text);
    const a = h('a', { href: href(kind, text, pl), hidden: true });
    document.body.append(a); a.click(); a.remove();
  }
  const base = path => path.split('\\').filter(Boolean).pop() || path;
  function item(kind, label, icon, note, url, title, onPick) {
    const kids = [h('span', { class: 'ic', html: iconSvg(icon, 16) }), h('span', { class: 'oc-label' }, label), h('span', { class: 'oc-note' + (Array.isArray(note) ? ' oc-split' : ''), dir: 'auto' }, note)];
    if (!url) return h('span', { class: 'pv-menu-item oc-item off', role: 'menuitem', 'aria-disabled': 'true', 'data-kind': kind, title }, kids);
    return h('a', { class: 'pv-menu-item oc-item', role: 'menuitem', href: url, 'data-kind': kind, title, onclick: () => { onPick(); setTimeout(close, 0); } }, kids);
  }
  function open(btn, opts) {
    close();
    const text = opts.text(), pl = opts.project ? places(opts.project) : { folders: [], files: [] };
    const pick = () => hand(text);
    const where = pl.folders.concat(pl.files);
    // with several places, a long first name gives way before 'and N more' does
    const coworkNote = !where.length ? (opts.project ? 'no folder link' : 'no project folder')
      : where.length === 1 ? 'with ' + base(where[0])
      : [h('span', { class: 'oc-name' }, 'with ' + base(where[0])), h('span', { class: 'oc-more' }, ' and ' + (where.length - 1) + ' more')];
    menu = h('div', { class: 'pv-menu oc-menu', role: 'menu', 'aria-label': 'Open in Claude' },
      item('chat', 'Chat', 'chat', 'new chat', href('chat', text), 'A new Claude chat with this filled in', pick),
      item('cowork', 'Cowork', 'folder', coworkNote, href('cowork', text, pl),
        where.length ? 'A new Cowork task with this filled in and ' + where.join(', ') + ' attached' : 'A new Cowork task with this filled in', pick),
      item('code', 'Claude Code', 'code', pl.folders[0] ? 'in ' + base(pl.folders[0]) : 'needs a folder link', pl.folders[0] ? href('code', text, pl) : null,
        pl.folders[0] ? 'A new Claude Code session in ' + pl.folders[0] + ' with this filled in'
          : (opts.project ? 'Add a link to a folder on this computer to open Claude Code there' : 'Opens from a project that links a folder on this computer'), pick));
    document.body.append(menu);
    const r = btn.getBoundingClientRect(), mw = menu.offsetWidth, mh = menu.offsetHeight;
    menu.style.left = Math.round(Math.max(8, Math.min(r.left, innerWidth - mw - 8))) + 'px';
    menu.style.top = Math.round(r.bottom + 6 + mh > innerHeight - 8 ? Math.max(8, r.top - 6 - mh) : r.bottom + 6) + 'px';
    owner = btn; btn.setAttribute('aria-expanded', 'true');
    menu.firstChild.focus();
    menu.addEventListener('keydown', e => {
      const items = $$('a.oc-item', menu), i = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
      else if (e.key === 'Tab') close();
    });
    setTimeout(() => { document.addEventListener('mousedown', outside, true); window.addEventListener('scroll', onScroll, true); window.addEventListener('resize', onScroll); }, 0);
  }
  function outside(e) { if (menu && !menu.contains(e.target) && !(owner && owner.contains(e.target))) close(); }
  function onScroll() { close(); }
  function close(refocus) {
    if (!menu) return false;
    menu.remove(); menu = null;
    document.removeEventListener('mousedown', outside, true);
    window.removeEventListener('scroll', onScroll, true); window.removeEventListener('resize', onScroll);
    if (owner) { owner.setAttribute('aria-expanded', 'false'); if (refocus) owner.focus(); }
    owner = null;
    return true;
  }
  /* The button that sits beside a Copy for Claude. opts: { text: () => string, project, id, quiet, small } */
  function button(opts) {
    const btn = h('button', { id: opts.id, class: 'btn oc-btn' + (opts.small === false ? '' : ' btn-small') + (opts.quiet ? ' btn-quiet' : ''), type: 'button', 'aria-haspopup': 'menu', 'aria-expanded': 'false',
      title: 'Opens this in the Claude app, filled in and ready to send: a chat, a Cowork task, or Claude Code' },
      iconEl('claude', 14), 'Open in Claude');
    btn.addEventListener('click', e => { e.stopPropagation(); if (owner === btn) close(); else open(btn, opts); });
    return btn;
  }
  return { button, go, places, close };
})();
