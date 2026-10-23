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
    return el;
  }
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
  async function loadAll() {
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

  /* ---------- the side bar's Leaders section ---------- */
  function init() {
    $('#ldPlus').innerHTML = iconSvg('plus', 12); $('#ldPlus').style.display = 'inline-flex';
    $('#btnNewLeader').addEventListener('click', () => create());
    renderSection();
  }
  function renderSection() {
    const grid = $('#leaderGrid');
    if (!grid) return;
    grid.replaceChildren(...DB.leaders.map(l => {
      const n = leaderProjects(l).length;
      return h('button', { class: 'ld-tile', type: 'button', 'data-id': l.id,
        title: leaderName(l) + (l.role ? ', ' + l.role : '') + '. ' + (n ? 'Leads ' + plural(n, 'building', 'buildings') : 'Leads no building yet') + '. Click to edit.',
        'aria-label': leaderName(l) + (l.role ? ', ' + l.role : '') + ', leads ' + plural(n, 'building', 'buildings'), onclick: () => edit(l.id) },
        face(l, 48), h('span', { class: 'ld-tile-name', dir: 'auto' }, leaderName(l)));
    }));
    if (!DB.leaders.length) grid.append(h('p', { class: 'ld-empty' }, 'No leaders yet. Add one with a portrait, then give it a building.'));
  }
  const refreshSoon = debounce(() => refreshAll(), 120);
  function refreshAll() {
    renderSection();
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
    const drawPortraitBtns = () => portraitBtns.replaceChildren(
      h('button', { class: 'btn btn-small', type: 'button', onclick: () => file.click() }, iconEl('plus', 14), has() ? 'Replace portrait' : 'Upload portrait'),
      has() ? h('button', { class: 'btn btn-small btn-quiet', type: 'button', onclick: async () => {
        if (isNew) draftUrl = null;
        else { await Store.deleteArt(portraitKey(l.id)); urls.delete(l.id); l.portrait = false; save(); }
        drawFace(); drawPortraitBtns();
      } }, 'Remove') : null);

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
        persistNow(); Panel.close(); refreshAll(); MapView.invalidate();
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
      persistNow(); Panel.close(); refreshAll(); MapView.invalidate();
      toast('Deleted ' + leaderName(l) + '.');
    }

    drawFace(); drawPortraitBtns(); drawSwatches(); drawBuildings();
    const foot = isNew
      ? h('div', { class: 'confirm-actions ld-actions' }, h('button', { class: 'btn', type: 'button', onclick: () => Panel.close() }, 'Cancel'),
          h('button', { id: 'ldAdd', class: 'btn btn-accent', type: 'button', onclick: add }, 'Add leader'))
      : h('div', { class: 'confirm-actions ld-actions' }, h('button', { id: 'ldDelete', class: 'btn btn-danger btn-small', type: 'button', onclick: remove }, 'Delete leader'),
          h('button', { id: 'ldDone', class: 'btn btn-accent', type: 'button', onclick: () => Panel.close() }, 'Done'));
    Panel.open(isNew ? 'New leader' : ['Leader: ', h('bdi', null, leaderName(l))], [
      h('div', { class: 'ld-form' },
        h('div', { class: 'ld-top' }, faceBox, h('div', { class: 'ld-portrait' }, portraitBtns,
          h('p', { class: 'note' }, 'A PNG, GIF, JPEG or WebP, up to 1024 px. 256 by 256 pixel art on a see-through background fits best.'), file)),
        err,
        h('label', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Name'), name),
        h('label', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Role'), role),
        h('div', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Signature color'), swatches),
        h('div', { class: 'ld-field' }, h('span', { class: 'lbl' }, 'Leads'), blds,
          h('p', { class: 'note' }, 'One leader per building; a leader can lead several.')),
        live ? h('p', { class: 'note' }, 'Changes save as you make them.') : null),
      foot]);
    const panel = $('.modal.panel'); if (panel) panel.classList.add('ld-panel');
    name.focus(); if (isNew) name.select();
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
     its color, the role, and what the leader says (0.1.58): its greeting with the next task, in a quote with a bar in
     its color. The full title is the line's tooltip when the line cuts it short. */
  function card(p, onPick) {
    const l = leaderOf(p);
    if (!l) return h('button', { id: 'pvLeader', class: 'ld-card empty', type: 'button', title: 'Pick a leader for this building', onclick: onPick },
      noFace(48), h('span', { class: 'ld-card-text' }, h('b', null, 'No leader yet'), h('span', null, 'Pick a leader')));
    const t = nextTask(p), says = leaderGreeting(p);
    const box = h('div', { id: 'pvLeader', class: 'ld-card' }, face(l, 96),
      h('span', { class: 'ld-card-text' }, h('b', { class: 'ld-name', dir: 'auto' }, leaderName(l)), l.role ? h('span', { dir: 'auto' }, l.role) : null,
        h('span', { class: 'ld-says', dir: 'auto', title: t && t.text.length > LEADER_TITLE_MAX ? t.text : null }, says)),
      h('button', { class: 'btn btn-quiet btn-small ld-change', type: 'button', title: 'Pick another leader, or edit this one', onclick: onPick }, 'Change'));
    box.style.setProperty('--ld', l.color);
    return box;
  }
  /* the status card's line under the building's name: the face at 48 px (32 until 0.1.57), the name and the role */
  function statusLine(p) {
    const l = leaderOf(p);
    if (!l) return null;
    const line = h('p', { class: 'b-leader' }, face(l, 48), h('span', { class: 'b-leader-text' }, h('b', { class: 'ld-name', dir: 'auto' }, leaderName(l)), l.role ? h('span', { dir: 'auto' }, l.role) : null));
    line.style.setProperty('--ld', l.color);
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
    urls.clear(); DB.leaders = [];
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

  return { init, loadAll, renderSection, refreshAll, create, edit, pickList, card, statusLine, hub, face,
    url: id => urls.get(id) || null, frame: url => frames.get(url) || null, measure, dropAll, restore, carry, adopt };
})();
