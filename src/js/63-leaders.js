/* Leaders in the city (0.1.51): the side bar's Leaders section, the leader panel that adds or edits one (its portrait,
   name, role, signature color and the buildings it leads), the picker beside the project view, the leader card under
   the building's picture, the line in the status card, and the face in the shortcut wheel's middle. A leader without a
   portrait shows a silhouette on its signature color, as the October design said. Portraits are read from the art
   store once and kept here by leader. Every portrait is framed by its figure (0.1.52), so one drawn small on a big
   see-through canvas fills its frame like the rest; the file itself is never changed. */
const Leaders = (() => {
  const urls = new Map();                                    // a leader's id: its portrait's data address
  const frames = new Map();                                  // a portrait's data address: how to frame it
  const PORTRAIT_MAX = 1024, PORTRAIT_BYTES = 3 * 1024 * 1024;

  /* ---------- a face: the portrait shrunk smooth into a frame of its signature color, or a silhouette ---------- */
  const SIL = ['................', '................', '......####......', '.....######.....', '....########....', '....########....',
    '....########....', '.....######.....', '......####......', '.......##.......', '...##########...', '..############..',
    '.##############.', '.##############.', '################', '################'];
  function silhouette(color) {
    let rects = '';
    SIL.forEach((row, y) => { for (let x = 0; x < 16;) { if (row[x] !== '#') { x++; continue; } let e = x; while (row[e] === '#') e++; rects += `<rect x="${x}" y="${y}" width="${e - x}" height="1"/>`; x = e; } });
    return `<svg viewBox="0 0 16 16" fill="${shadeHex(color, -0.42)}" aria-hidden="true">${rects}</svg>`;
  }
  function face(l, size = 48, { round = false, url } = {}) {
    const el = h('span', { class: 'ld-face' + (round ? ' round' : ''), 'aria-hidden': 'true' });
    el.style.setProperty('--face', size + 'px');
    el.style.setProperty('--ld', l.color);
    el.style.setProperty('--ld-ring', shadeHex(l.color, -0.45));
    const src = url !== undefined ? url : (l.portrait ? urls.get(l.id) : null);
    if (src) el.append(placed(h('img', { class: 'face-pic', alt: '', src, draggable: 'false' }), frames.get(src), size));
    else el.innerHTML = silhouette(l.color);
    return breathe(el, l.id);
  }
  /* Alive (0.1.62, Leader UX E1): wherever a leader's face shows, it rises a pixel and back every few seconds, each
     leader on its own slow rhythm. The rhythm and its place in it come from the leader and the page's clock, so its
     faces breathe together, and a face drawn again carries on where it was. Motion on Still holds it (m-still). */
  const breathMs = k => 3400 + (k % 2001);                  // 3.4 to 5.4 seconds a breath
  function breathe(el, key) {
    const k = hashStr('breath:' + key);
    el.classList.add('breathes');
    el.dataset.breath = String(k);
    el.style.setProperty('--breath', breathMs(k) + 'ms');
    inStep(el);
    return el;
  }
  function inStep(el) {
    const k = Number(el.dataset.breath), dur = breathMs(k);
    el.style.setProperty('--breath-at', -Math.round((performance.now() + Math.floor(k / 2048) % dur) % dur) + 'ms');
  }
  /* A face drawn while hidden starts breathing only once it shows, and one that stops talking starts again: each
     time, it falls back in step with the leader's other faces. */
  document.addEventListener('animationstart', e => {
    const el = e.animationName === 'face-breathe' && e.target.parentElement;
    if (el && el.dataset.breath) inStep(el);
  }, true);
  /* The figure's frame: a square round the portrait's drawn pixels, its foot on the frame's foot and the head a
     little under its top, as Gus and Proxima fill theirs. A picture with no see-through pixels is cropped square,
     from the top when it is tall. Read from the first frame, so an animated GIF keeps playing. */
  const HEAD_ROOM = 0.97;                                    // the figure's height, of the frame's
  function frameOf(img) {
    const w = img.naturalWidth, hh = img.naturalHeight;
    const c = document.createElement('canvas'); c.width = w; c.height = hh;
    const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, w, hh).data;
    let x0 = w, y0 = hh, x1 = -1, y1 = -1;
    for (let y = 0; y < hh; y++) for (let x = 0; x < w; x++) if (d[(y * w + x) * 4 + 3] >= 8) {
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    if (x1 < 0 || (x0 === 0 && y0 === 0 && x1 === w - 1 && y1 === hh - 1)) {
      const s = Math.min(w, hh);
      return { x: (w - s) / 2, y: hh > w ? 0 : (hh - s) / 2, s, w, h: hh };
    }
    const bw = x1 - x0 + 1, bh = y1 - y0 + 1, s = Math.max(bw, bh / HEAD_ROOM);
    return { x: x0 + bw / 2 - s / 2, y: y1 + 1 - s, s, w, h: hh };
  }
  async function measure(url) {
    if (!url || frames.has(url)) return frames.get(url) || null;
    try { const f = frameOf(await loadImage(url)); frames.set(url, f); return f; } catch (e) { return null; }
  }
  /* The picture sized and moved so its frame fills the face; shrunk smooth, and grown in whole pixels. */
  function placed(img, f, size) {
    if (!f) return img;
    const k = size / f.s;
    img.classList.add('framed');
    if (k > 1) img.classList.add('up');
    Object.assign(img.style, { width: f.w * k + 'px', height: f.h * k + 'px', left: -f.x * k + 'px', top: -f.y * k + 'px' });
    return img;
  }
  const noFace = size => { const el = h('span', { class: 'ld-face ld-none', 'aria-hidden': 'true' }); el.style.setProperty('--face', size + 'px'); return el; };

  /* ---------- portraits ---------- */
  /* Quill's portrait ships with the city (0.1.69): kept with the leaders' under his id, so his face is framed and
     breathes as theirs do. */
  const keepQuill = () => { if (typeof PORTRAITS !== 'undefined' && PORTRAITS.quill) urls.set(QUILL.id, PORTRAITS.quill); };
  async function loadAll() {
    keepQuill();
    for (const l of DB.leaders) if (l.portrait && !urls.has(l.id)) { const u = await Store.getArt(portraitKey(l.id)); if (u) urls.set(l.id, u); }
    for (const u of urls.values()) await measure(u);
    refreshAll();
  }
  async function readPortrait(f) {
    if (!/^image\/(png|gif|jpeg|webp)$/.test(f.type) && !/\.(png|gif|jpe?g|webp)$/i.test(f.name)) throw new Error('A portrait takes a PNG, GIF, JPEG or WebP.');
    if (f.size > PORTRAIT_BYTES) throw new Error('This image is over 3 MB. A portrait needs far less: 256 by 256 px is plenty.');
    const url = await readAsDataURL(f);
    let img;
    try { img = await loadImage(url); } catch (e) { throw new Error('That image could not be read. Export it again and retry.'); }
    if (img.naturalWidth > PORTRAIT_MAX || img.naturalHeight > PORTRAIT_MAX)
      throw new Error('This image is ' + img.naturalWidth + ' by ' + img.naturalHeight + ' px. A portrait is at most 1024 px; 256 by 256 is plenty.');
    return url;
  }
  async function putPortrait(l, url) {
    const kept = await Store.putArt(portraitKey(l.id), url);
    await measure(url);
    urls.set(l.id, url); l.portrait = true;
    return kept;
  }

  /* ---------- the Leaders panel (0.1.61, Leader UX C1 and L3): a Leaders button beside All tasks at the side bar's foot
     turns the side bar into every leader, as Reports and Settings do; New leader at its top. The side bar is level 0, and
     since 0.1.64 (SideBar Cleanup) a click on a leader opens its editor at level 1, a panel docked on the left of the
     map like the project view, with room for all a leader will hold; its row stays marked in the list. It opens over
     the project view or All tasks, and they are back as they were once it closes. ---------- */
  let editing = null;                                        // the leader the editor shows, while it shows
  const isOpen = () => !!$('#leadersPanel') && !$('#leadersPanel').hidden;
  function init() {
    keepQuill();
    $('#ldPlus').innerHTML = iconSvg('plus', 12); $('#ldPlus').style.display = 'inline-flex';
    $('#sbLeaderIcon').innerHTML = iconSvg('leader', 16); $('#sbLeaderIcon').style.display = 'inline-flex';
    $('#ldBack').innerHTML = iconSvg('back', 18);
    $('#ldClose').innerHTML = iconSvg('close', 18);
    $('#btnNewLeader').addEventListener('click', () => create());
    $('#btnOpenLeaders').addEventListener('click', () => { open(); showList(); });
    $('#ldBack').addEventListener('click', () => close());
    $('#ldClose').addEventListener('click', () => { if (editing) showList(editing.id); });
    const esc = e => { if (e.key === 'Escape' && escape()) { e.preventDefault(); e.stopPropagation(); } };
    $('#leadersPanel').addEventListener('keydown', esc);
    $('#ldView').addEventListener('keydown', esc);
    renderSection();
  }
  function open() {
    if (typeof Settings !== 'undefined') Settings.close(false);  // the three share the side bar; All tasks is on the map (0.1.64)
    if (typeof Reports !== 'undefined') Reports.close(false);
    Menu.toggleDrawer(true);
    $('#sbLists').hidden = true; $('#leadersPanel').hidden = false;
    $('#menu').classList.add('in-leaders');
    $('#menu').scrollTop = 0;
  }
  function close(refocus = true) {
    if (!isOpen()) return false;
    closeEditor();                                           // its editor goes with it
    $('#leadersPanel').hidden = true;
    $('#menu').classList.remove('in-leaders');
    Menu.listsBack();
    if (refocus) $('#btnOpenLeaders').focus({ preventScroll: true });
    return true;
  }
  /* Esc: the editor goes back to the list, the list closes. */
  function escape() {
    if (editing) { showList(editing.id); return true; }
    if (!isOpen()) return false;
    return close();
  }
  /* The editor closes, back to whatever it covered on the map. */
  function closeEditor() {
    if (!editing) return false;
    editing = null;
    $('#ldView').hidden = true; $('#ldEdit').replaceChildren();
    renderSection();
    return true;
  }
  /* The list, with the editor closed and the focus on the leader just edited when there is one, else on the panel. */
  function showList(focusId = null) {
    closeEditor();
    if (!isOpen()) open();
    renderSection();
    const row = focusId && $(`.ld-row[data-id="${focusId}"]`);
    (row || $('#leadersPanel')).focus({ preventScroll: true });
  }
  /* Every leader: its face, its name in its color, its role, and the buildings it leads. */
  function renderSection() {
    const list = $('#ldList');
    if (!list) return;
    const a = document.activeElement, keep = a && list.contains(a) && a.dataset ? a.dataset.id : null;
    list.replaceChildren(...DB.leaders.map(l => {
      const ps = leaderProjects(l);
      const b = h('button', { class: 'ld-row', type: 'button', 'data-id': l.id, 'aria-current': editing && editing.id === l.id ? 'true' : null,
        title: 'Edit ' + leaderName(l) + '. ' + (ps.length ? 'Leads ' + plural(ps.length, 'building', 'buildings') : 'Leads no building yet') + '.',
        onclick: () => edit(l.id) },
        face(l, 48),
        h('span', { class: 'ld-row-text' }, h('b', { class: 'ld-name', dir: 'auto' }, leaderName(l)),
          l.role ? h('span', { class: 'ld-row-role', dir: 'auto' }, l.role) : null,
          h('span', { class: 'ld-row-blds', dir: 'auto' }, ps.length ? ps.map(p => p.name).sort((x, y) => x.localeCompare(y)).join(', ') : 'No building yet')));
      b.style.setProperty('--ld', l.color);
      return h('li', null, b);
    }));
    if (!DB.leaders.length) list.append(h('li', { class: 'ld-empty' }, 'No leaders yet. Add one with a portrait, then give it a building.'));
    if (keep) { const r = $(`.ld-row[data-id="${keep}"]`, list); if (r) r.focus({ preventScroll: true }); }
  }
  const refreshSoon = debounce(() => refreshAll(), 120);
  function refreshAll() {
    renderSection();
    if (typeof News !== 'undefined') { News.renderSection(); News.redraw(); }   // the faces in News and its bubble, once portraits load (0.1.60)
    Bubble.refresh();
    if (typeof FullView !== 'undefined') FullView.render();
  }

  /* ---------- the leader panel: add one, or edit one (changes apply at once) ---------- */
  function create({ assign = null, onAdded = null } = {}) { form(blankLeader(), { isNew: true, assign, onAdded }); }
  function edit(id) { const l = getLeader(id); if (l) form(l, { isNew: false }); }
  function form(l, { isNew, assign = null, onAdded = null }) {
    let draftUrl = null;                                      // a new leader's portrait, kept until Add
    const picked = new Set(assign ? [assign.id] : []);        // a new leader's buildings, until Add
    const live = !isNew;
    const save = () => { if (live) { persistSoon(); refreshSoon(); } };

    const faceBox = h('div', { class: 'ld-big' });
    const drawFace = () => faceBox.replaceChildren(face(l, 128, isNew ? { url: draftUrl } : {}));
    const has = () => (isNew ? !!draftUrl : l.portrait && urls.has(l.id));
    const err = h('p', { class: 'plan-err ld-err', role: 'alert', hidden: true });
    const file = h('input', { type: 'file', accept: 'image/png,image/gif,image/jpeg,image/webp,.png,.gif,.jpg,.jpeg,.webp', hidden: true,
      onchange: async e => {
        const f = e.target.files[0]; e.target.value = ''; if (!f) return;
        let url;
        try { url = await readPortrait(f); } catch (x) { err.textContent = x.message; err.hidden = false; return; }
        err.hidden = true;
        await measure(url);
        if (isNew) draftUrl = url;
        else { const kept = await putPortrait(l, url); save(); if (!kept) toast('Portrait added for this session only: this browser is not saving it. Export a backup to keep it.', 'error'); }
        drawFace(); drawPortraitBtns();
      } });
    const portraitBtns = h('div', { class: 'inline ld-portrait-btns' });
    const drawPortraitBtns = () => portraitBtns.replaceChildren(...[
      h('button', { class: 'btn btn-small', type: 'button', onclick: () => file.click() }, iconEl('plus', 14), has() ? 'Replace portrait' : 'Upload portrait'),
      has() ? h('button', { class: 'btn btn-small btn-quiet', type: 'button', onclick: async () => {
        if (isNew) draftUrl = null;
        else { await Store.deleteArt(portraitKey(l.id)); urls.delete(l.id); l.portrait = false; save(); }
        drawFace(); drawPortraitBtns();
      } }, 'Remove') : null].filter(Boolean));               // no stray "null" beside Upload portrait (0.1.61)

    const name = h('input', { id: 'ldName', class: 'field', type: 'text', dir: 'auto', maxlength: String(LEADER_MAX.name), value: l.name, placeholder: 'Name', autocomplete: 'off', 'aria-label': 'Name',
      oninput: e => { l.name = e.target.value; err.hidden = true; save(); },
      onblur: e => { if (live && !e.target.value.trim()) { l.name = 'Leader'; e.target.value = l.name; save(); } },
      onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); if (isNew) add(); } } });
    const role = h('input', { id: 'ldRole', class: 'field', type: 'text', dir: 'auto', maxlength: String(LEADER_MAX.role), value: l.role, placeholder: 'Mayor, Head chef, Chief of Staff', autocomplete: 'off', 'aria-label': 'Role',
      oninput: e => { l.role = e.target.value; save(); },
      onblur: e => { if (live) { l.role = e.target.value.replace(/\s+/g, ' ').trim(); e.target.value = l.role; save(); } },
      onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); if (isNew) add(); } } });

    const swatches = h('div', { class: 'ld-swatches', role: 'group', 'aria-label': 'Signature color' });
    const other = h('input', { class: 'ld-other', type: 'color', value: l.color.toLowerCase(), 'aria-label': 'Another color', title: 'Another color', oninput: e => pickColor(e.target.value) });
    const drawSwatches = () => swatches.replaceChildren(...LEADER_COLORS.map(c => {
      const b = h('button', { class: 'ld-swatch', type: 'button', 'aria-pressed': String(c === l.color), 'aria-label': 'Color ' + c, title: c, onclick: () => pickColor(c) });
      b.style.background = c;
      return b;
    }), other);
    function pickColor(c) { l.color = c.toUpperCase(); other.value = l.color.toLowerCase(); drawFace(); drawSwatches(); save(); }

    const blds = h('div', { class: 'ld-blds', role: 'group', 'aria-label': 'Buildings it leads' });
    const drawBuildings = () => blds.replaceChildren(...(DB.projects.length ? [...DB.projects].sort((a, b) => a.name.localeCompare(b.name)).map(p => {
      const on = isNew ? picked.has(p.id) : p.leader === l.id;
      const otherLeader = !on && leaderOf(p);
      return h('label', { class: 'check ld-bld' + (on ? ' on' : ''), 'data-id': p.id },
        h('input', { type: 'checkbox', class: 'cb', checked: on, 'aria-label': 'Leads ' + p.name, onchange: e => {
          if (isNew) { if (e.target.checked) picked.add(p.id); else picked.delete(p.id); }
          else { setLeader(p, e.target.checked ? l.id : ''); changed(p, { touch: false }); refreshSoon(); }
          drawBuildings();
          const again = $(`.ld-bld[data-id="${p.id}"] input`, blds); if (again) again.focus();
        } }),
        h('span', { class: 'ld-bld-thumb', 'aria-hidden': 'true' }, MapView.thumb(p)),
        h('span', { class: 'ld-bld-name', dir: 'auto' }, p.name),
        otherLeader ? h('span', { class: 'ld-bld-other', dir: 'auto' }, 'led by ' + leaderName(otherLeader)) : null);
    }) : [h('p', { class: 'note' }, 'No buildings yet.')]));

    function add() {
      const nm = name.value.replace(/\s+/g, ' ').trim();
      if (!nm) { err.textContent = 'Give the leader a name.'; err.hidden = false; name.focus(); return; }
      l.name = nm; l.role = role.value.replace(/\s+/g, ' ').trim(); l.createdAt = Date.now();
      DB.leaders.push(l);
      (async () => {
        let kept = true;
        if (draftUrl) kept = await putPortrait(l, draftUrl);
        const ps = DB.projects.filter(p => picked.has(p.id));
        for (const p of ps) setLeader(p, l.id);
        persistNow(); showList(l.id); refreshAll(); MapView.invalidate();
        toast('Added ' + leaderName(l) + (ps.length === 1 ? ', who leads ' + ps[0].name : ps.length ? ', who leads ' + plural(ps.length, 'building', 'buildings') : '') + '.'
          + (kept ? '' : ' The portrait is held for this session only.'), kept ? '' : 'error');
        if (onAdded) onAdded(l);
      })();
    }
    async function remove() {
      const ps = leaderProjects(l);
      const ok = await Confirm.ask({ title: ['Delete ', h('bdi', null, leaderName(l)), '?'],
        body: (ps.length === 1 ? ps[0].name + ' keeps running, with no leader. ' : ps.length ? 'Their ' + ps.length + ' buildings keep running, with no leader. ' : '')
          + (l.portrait ? 'The portrait is removed from this browser.' : '') || 'Nothing else changes.',
        confirm: 'Delete leader', danger: true });
      if (!ok) return;
      DB.leaders = DB.leaders.filter(x => x.id !== l.id);
      for (const p of DB.projects) if (p.leader === l.id) p.leader = '';
      await Store.deleteArt(portraitKey(l.id)); urls.delete(l.id);
      persistNow(); showList(); refreshAll(); MapView.invalidate();
      toast('Deleted ' + leaderName(l) + '.');
    }

    drawFace(); drawPortraitBtns(); drawSwatches(); drawBuildings();
    const foot = isNew
      ? h('div', { class: 'confirm-actions ld-actions' }, h('button', { id: 'ldCancel', class: 'btn', type: 'button', onclick: () => showList() }, 'Cancel'),
          h('button', { id: 'ldAdd', class: 'btn btn-accent', type: 'button', onclick: add }, 'Add leader'))
      : h('div', { class: 'confirm-actions ld-actions' }, h('button', { id: 'ldDelete', class: 'btn btn-danger btn-small', type: 'button', onclick: remove }, 'Delete leader'),
          h('button', { id: 'ldDone', class: 'btn btn-accent', type: 'button', onclick: () => showList(l.id) }, 'Done'));
    /* the editor, at level 1 on the map (0.1.64), with the list still in the side bar and its row marked; on a narrow
       window the drawer closes, as the editor covers the map */
    if (!isOpen()) open();
    editing = l;
    renderSection();
    if (window.matchMedia('(max-width: 760px)').matches) Menu.closeDrawer();
    $('#ldEditTitle').replaceChildren(...(isNew ? ['New leader'] : ['Leader: ', h('bdi', null, leaderName(l))]));
    $('#ldView').hidden = false;
    $('#ldView').scrollTop = 0;
    $('#ldEdit').replaceChildren(
      h('div', { class: 'ld-form' },
        h('div', { class: 'ld-top' }, faceBox, h('div', { class: 'ld-portrait' }, portraitBtns,
          h('p', { class: 'note' }, 'A PNG, GIF, JPEG or WebP, up to 1024 px. 256 by 256 pixel art on a see-through background fits best.'), file)),
        h('div', { class: 'ld-fields' },
          err,
          h('label', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Name'), name),
          h('label', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Role'), role),
          h('div', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Signature color'), swatches)),
        h('div', { class: 'ld-field ld-leads' }, h('span', { class: 'lbl' }, 'Leads'), blds,
          h('p', { class: 'note' }, 'One leader per building; a leader can lead several.')),
        live ? h('p', { class: 'note ld-saves' }, 'Changes save as you make them.') : null),
      foot);
    name.focus({ preventScroll: true }); if (isNew) name.select();
  }

  /* ---------- picking a building's leader, beside the project view ---------- */
  function pickList(p, after) {
    const opt = l => {
      const on = l ? p.leader === l.id : !p.leader;
      const also = l ? leaderProjects(l).filter(x => x.id !== p.id).length : 0;
      return h('button', { class: 'ld-opt' + (on ? ' on' : ''), type: 'button', 'aria-pressed': String(on), 'data-id': l ? l.id : '',
        onclick: () => {
          if (!on) {
            setLeader(p, l ? l.id : ''); changed(p, { touch: false });
            toast(l ? leaderName(l) + ' leads ' + p.name + ' now.' : p.name + ' has no leader now.');
          }
          after();
        } },
        l ? face(l, 48) : noFace(48),
        h('span', { class: 'ld-opt-text' }, h('b', { dir: 'auto' }, l ? leaderName(l) : 'No leader'),
          h('span', { dir: 'auto' }, l ? [l.role, also ? 'also leads ' + plural(also, 'building', 'buildings') : ''].filter(Boolean).join(' · ') || ' ' : 'The building runs on its own')));
    };
    return h('div', { class: 'ld-pick' },
      h('p', { class: 'note' }, 'Who leads ' + p.name + '. A leader can lead several buildings.'),
      h('div', { class: 'ld-opts', role: 'group', 'aria-label': 'Leaders' }, opt(null), ...DB.leaders.map(opt)),
      h('div', { class: 'inline ld-pick-btns' },
        h('button', { id: 'ldPickNew', class: 'btn', type: 'button', onclick: () => create({ assign: p, onAdded: () => after() }) }, iconEl('plus', 14), 'New leader'),
        p.leader ? h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => edit(p.leader) }, iconEl('pencil', 14), 'Edit ' + leaderName(leaderOf(p))) : null));
  }

  /* ---------- where a leader shows ---------- */
  /* the leader card under the building's picture in the project view: the face at 96 px (64 until 0.1.57), the name in
     its color, the role, and what the leader says (0.1.58): since 0.1.69 what the status card says, with its buttons
     (Leader Bubbles, Round 2, N1: "it tells you the latest things, and if there is an action you can take, you can take
     it there"), Claude at work included; else its greeting with the next task, in a quote with a bar in its color. The
     full title is the line's tooltip when the line cuts it short. A building with no leader has Proxima say it, as on
     the status card, with Pick a leader; with nothing to say, the card offers to pick one. */
  let lastPick = null;
  function card(p, onPick) {
    lastPick = { pid: p.id, onPick };
    const l = leaderOf(p), news = News.viewLines(p);
    if (!l && !news.length) return h('button', { id: 'pvLeader', class: 'ld-card empty', type: 'button', title: 'Pick a leader for this building', onclick: onPick },
      noFace(48), h('span', { class: 'ld-card-text' }, h('b', null, 'No leader yet'), h('span', null, 'Pick a leader')));
    if (!l) {
      const box = h('div', { id: 'pvLeader', class: 'ld-card has-news px-voice' }, breathe(Proxima.faceEl(96), 'proxima'),
        h('span', { class: 'ld-card-text' }, h('b', { class: 'ld-name' }, 'Proxima Pace'), h('span', null, 'Productivity Inspector'), ...news),
        h('button', { class: 'btn btn-quiet btn-small ld-change', type: 'button', title: 'Pick a leader for this building', onclick: onPick }, 'Pick a leader'));
      box.style.setProperty('--ld', '#8FD0F7');
      return box;
    }
    const t = nextTask(p);
    const says = news.length ? news : [h('span', { class: 'ld-says', dir: 'auto', title: t && t.text.length > LEADER_TITLE_MAX ? t.text : null }, leaderGreeting(p))];
    const box = h('div', { id: 'pvLeader', class: 'ld-card' + (news.length ? ' has-news' : '') }, face(l, 96),
      h('span', { class: 'ld-card-text' }, h('b', { class: 'ld-name', dir: 'auto' }, leaderName(l)), l.role ? h('span', { dir: 'auto' }, l.role) : null, ...says),
      h('button', { class: 'btn btn-quiet btn-small ld-change', type: 'button', title: 'Pick another leader, or edit this one', onclick: onPick }, 'Change'));
    box.style.setProperty('--ld', l.color);
    return box;
  }
  /* The card again, in place, when its building's news changes while the project view shows it. */
  function redrawCard() {
    const el = $('#pvLeader');
    if (!el || !lastPick || typeof FullView === 'undefined' || !FullView.shows(lastPick.pid)) return;
    const p = getProject(lastPick.pid);
    if (p) el.replaceWith(card(p, lastPick.onPick));
  }
  /* the status card's line under the building's name: the face at 48 px (32 until 0.1.57), the name and the role, then
     what its leader says (0.1.59): the building's news, read as the card shows it, and Claude's lines in its voice. A
     building with no leader has Proxima say it, when there is something to say. */
  function statusLine(p) {
    const l = leaderOf(p), lines = News.cardLines(p);
    if (!l && !lines.length) return null;
    const line = h('div', { class: 'b-leader' + (l ? '' : ' px-voice') + (lines.length ? ' has-news' : '') },
      l ? face(l, 48) : breathe(Proxima.faceEl(48), 'proxima'),
      h('div', { class: 'b-leader-text' }, h('b', { class: 'ld-name', dir: 'auto' }, l ? leaderName(l) : 'Proxima Pace'),
        (l ? l.role : 'Productivity Inspector') ? h('span', { class: 'b-leader-role', dir: 'auto' }, l ? l.role : 'Productivity Inspector') : null, ...lines));
    line.style.setProperty('--ld', l ? l.color : '#8FD0F7');
    return line;
  }
  /* the shortcut wheel's middle, kept for the leader's face since 0.1.26 */
  function hub(p) {
    const l = leaderOf(p);
    const el = h('div', { class: 'wheel-hub' + (l ? ' has-leader' : ''), 'aria-hidden': 'true' }, l ? face(l, 64, { round: true }) : null);
    if (l) el.style.setProperty('--ld', l.color);
    return el;
  }

  /* ---------- leaders in backups and project files ---------- */
  async function dropAll() {
    for (const l of DB.leaders) await Store.deleteArt(portraitKey(l.id));
    urls.clear(); keepQuill(); DB.leaders = [];
  }
  /* A backup's leaders, with their portraits; resolves how many portraits this browser holds for this session only. */
  async function restore(list) {
    const out = sanitizeLeaders(list), raws = (Array.isArray(list) ? list : []).filter(r => r && typeof r === 'object');
    let lost = 0;
    for (let i = 0; i < out.length; i++) {
      const l = out[i], r = raws[i], url = r && typeof r.portraitUrl === 'string' && /^data:image\//.test(r.portraitUrl) ? r.portraitUrl : null;
      l.portrait = false;
      if (url && !(await putPortrait(l, url))) lost++;
    }
    DB.leaders = out;
    return lost;
  }
  /* A portrait that came from another city, or another tab of this one (0.1.73): kept for its leader, in the art
     store too unless it is there already, and a portrait gone from the other side let go of. */
  async function keep(id, url, store = true) {
    if (store) await Store.putArt(portraitKey(id), url);
    await measure(url);
    urls.set(id, url);
    refreshSoon();
  }
  async function forget(id, store = true) {
    if (store) await Store.deleteArt(portraitKey(id));
    if (id !== QUILL.id) urls.delete(id);
    refreshSoon();
  }
  /* A project file carries its leader: its name, role, color and portrait. */
  async function carry(l) {
    if (!l) return null;
    const url = l.portrait ? (await Store.getArt(portraitKey(l.id))) || urls.get(l.id) || null : null;
    return { name: leaderName(l), role: l.role, color: l.color, ...(url ? { portraitUrl: url } : {}) };
  }
  /* A project file's leader in this city: one of its leaders by the same name, else a new one. Resolves its id. */
  async function adopt(info) {
    if (!info || typeof info !== 'object') return '';
    const [l] = sanitizeLeaders([Object.assign({}, info, { id: uid('ld') })]);
    if (!l) return '';
    const same = DB.leaders.find(x => norm(leaderName(x)) === norm(l.name));
    if (same) return same.id;
    l.portrait = false;
    const url = typeof info.portraitUrl === 'string' && /^data:image\//.test(info.portraitUrl) ? info.portraitUrl : null;
    if (url) await putPortrait(l, url);
    DB.leaders.push(l);
    return l.id;
  }

  /* A toast its leader says (0.1.56): the face at 40 px, its name in its color over the building's; null with no leader.
     The line over the map's Task added, and since 0.1.63 Tick it's Ticked off (Open in Claude Panel, D1). */
  function toastLead(p) {
    const l = typeof leaderOf === 'function' ? leaderOf(p) : null;
    if (!l) return null;
    const lead = h('span', { class: 'toast-lead' }, face(l, 40),
      h('span', { class: 'toast-who' }, h('b', { class: 'ld-name', dir: 'auto' }, leaderName(l)), h('span', { dir: 'auto' }, p.name)));
    lead.style.setProperty('--ld', l.color);
    return lead;
  }

  return { init, loadAll, renderSection, refreshAll, create, edit, open, close, closeEditor, escape, isOpen, editing: () => editing, editorOpen: () => !!editing, pickList, card, redrawCard, statusLine, hub, face, breathe, toastLead,
    url: id => urls.get(id) || null, frame: url => frames.get(url) || null, measure, dropAll, restore, carry, adopt, keep, forget };
})();
