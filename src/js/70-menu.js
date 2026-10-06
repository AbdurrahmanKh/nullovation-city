const Menu = (() => {
  let countEl, saveEl;

  function init() {
    $('#brandMark').innerHTML = iconSvg('brand', 32);
    $('#plusIcon').innerHTML = iconSvg('plus', 14);
    $('#plusIcon').style.display = 'inline-flex';
    $('#zoomIn').innerHTML = iconSvg('plus', 16);
    $('#zoomOut').innerHTML = iconSvg('minus', 16);
    countEl = $('#count'); saveEl = $('#saveStatus');

    $('#search').addEventListener('input', e => { App.filter.q = norm(e.target.value); MapView.invalidate(); refresh(); });

    const btnNew = $('#btnNew'), wrap = $('#newWrap'), inp = $('#newName');
    btnNew.addEventListener('click', () => {
      MapView.cancelMode();
      btnNew.hidden = true; wrap.hidden = false; inp.value = ''; inp.focus();
    });
    const next = () => {
      const name = inp.value.trim();
      if (!name) { inp.focus(); return; }
      hideNew();
      Picker.open({ name, onPick: id => MapView.startPlace(name, id).then(ok => { if (ok) closeDrawer(); }) });
    };
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();   // the same Enter must not activate whatever gets focus next
        next();
      } else if (e.key === 'Escape') {
        e.stopPropagation(); hideNew(); btnNew.focus();
      }
    });
    $('#newNext').addEventListener('mousedown', e => e.preventDefault());   // keep the name field from blurring first
    $('#newNext').addEventListener('click', next);
    inp.addEventListener('blur', () => { if (!inp.value.trim()) hideNew(); });
    $('#bannerCancel').addEventListener('click', () => MapView.cancelMode());

    $('#btnRecap').addEventListener('click', () => { closeDrawer(); openRecap(); });
    for (const id of ['foldTools', 'foldData']) {                  // each collapsible remembers whether it was open
      const d = $('#' + id), key = 'nullovation-city:' + id;
      try { d.open = localStorage.getItem(key) === '1'; } catch (e) { /* closed */ }
      d.addEventListener('toggle', () => { try { localStorage.setItem(key, d.open ? '1' : '0'); } catch (e) { /* this visit only */ } });
    }
    $('#btnPalette').addEventListener('click', () => paletteCanvas().toBlob(blob => {
      if (!blob) return;
      downloadBlob(blob, 'nullovation-city-palette.png');
      toast('Palette saved: 32 colors as 8 px swatches.');
    }, 'image/png'));
    $('#btnBrief').addEventListener('click', copyBrief);
    $('#btnBrief').after(OpenInClaude.button({ id: 'btnBriefClaude', text: () => statusBrief(), small: false }));
    const cr = $('#optCrowds');
    cr.value = Traffic.crowd();
    cr.addEventListener('change', () => { Traffic.setCrowd(cr.value); toast({ none: 'No crowds round busy buildings.', small: 'Small crowds round busy buildings.', medium: 'Medium crowds round busy buildings.', large: 'Large crowds round busy buildings.' }[cr.value]); });
    const ex = $('#optExplorer');
    ex.checked = explorerLinks();
    ex.addEventListener('change', () => {
      try { localStorage.setItem(EXPLORER_KEY, ex.checked ? '1' : '0'); } catch (e) { /* this visit only */ }
      FullView.render();
      toast(ex.checked ? 'Folder links now open in File Explorer, once the Windows setup has run on this PC.' : 'Folder links open in the browser again.');
    });
    $('#btnFolderSetup').addEventListener('click', () => {
      downloadBlob(new Blob([FOLDER_SETUP_PS1], { type: 'text/plain' }), 'nullovation-folder-links.ps1');
      toast('Saved nullovation-folder-links.ps1. Right-click it, choose Run with PowerShell, then turn on the setting.');
    });
    $('#btnGrow').addEventListener('click', () => { if (MapView.resizeWorld(1)) toast('Added a ring of plots.'); });
    $('#btnShrink').addEventListener('click', () => {
      if (!MapView.outerRingEmpty()) { toast('The outer ring has buildings on it. Move them inward first.', 'error'); return; }
      if (MapView.resizeWorld(-1)) toast('Removed the outer ring.');
    });
    $('#btnExport').addEventListener('click', exportAll);
    $('#btnImport').addEventListener('click', () => $('#fileImport').click());
    $('#fileImport').addEventListener('change', e => { const f = e.target.files[0]; e.target.value = ''; if (f) importFile(f); });
    $('#menuToggle').addEventListener('click', () => toggleDrawer());
    $('#menuClose').innerHTML = iconSvg('close', 18);
    $('#menuClose').addEventListener('click', () => { closeDrawer(); $('#menuToggle').focus(); });

    setSaveStatus(Store.persistent());
    refresh();
  }
  function hideNew() { $('#newWrap').hidden = true; $('#btnNew').hidden = false; }

  /* Red projects as tiny buildings with their bubble number; the section hides when none is red. */
  function renderUrgent() {
    const sec = $('#sbUrgent'), box = $('#urgentList');
    if (!sec) return;
    const reds = DB.projects.map(p => ({ p, u: urgencyOf(p) })).filter(x => x.u.color === 'red').sort((a, b) => b.u.count - a.u.count);
    sec.hidden = !reds.length;
    box.replaceChildren(...reds.map(({ p, u }) => h('button', { class: 'urgent-item', type: 'button', title: p.name + '. Red: ' + u.reasons.join('. ') + '.', 'aria-label': p.name + ', red, ' + u.count,
      onclick: () => { closeDrawer(); MapView.select(p.id); } },
      MapView.thumb(p), h('span', { class: 'urgent-badge', 'aria-hidden': 'true' }, u.count <= 1 ? '!' : String(Math.min(u.count, 99))))));
  }
  /* Open tasks due in the next 7 days, overdue first, each with a copy for Claude. */
  function renderDue() {
    const sec = $('#sbDue'), list = $('#dueList');
    if (!sec) return;
    const items = [];
    for (const p of DB.projects) for (const t of p.todos) {
      if (t.done || !t.due) continue;
      const d = dueInfo(t);
      if (d && d.diff <= 6) items.push({ p, t, d });
    }
    items.sort((a, b) => a.d.diff - b.d.diff || a.p.name.localeCompare(b.p.name));
    sec.hidden = !items.length;
    const shown = items.slice(0, 8);
    list.replaceChildren(...shown.map(({ p, t, d }) => h('li', { class: 'due-item' },
      h('button', { class: 'due-task', type: 'button', title: 'Open this task', onclick: () => { closeDrawer(); FullView.openTask(p.id, t.id); } },
        h('span', { class: 'due-text', dir: 'auto' }, t.text),
        h('span', { class: 'due-meta' }, h('span', { class: 'due ' + (d.tone || '') }, (d.tone === 'late' ? '! ' : '') + d.text), h('span', { class: 'due-proj', dir: 'auto' }, p.name))),
      h('button', { class: 'icon-btn due-copy', type: 'button', 'aria-label': 'Copy this task for Claude', title: 'Copy this task for Claude', html: iconSvg('copy', 14), onclick: () => copyTask(p, t) }))),
      ...(items.length > shown.length ? [h('li', { class: 'due-more' }, 'and ' + (items.length - shown.length) + ' more')] : []));
  }
  /* This week in numbers; the card opens the week. */
  function renderWeek() {
    const btn = $('#btnRecap');
    if (!btn) return;
    const cur = weekStartOf(Date.now()), parts = weekNumbers(weekOf(cur).tot);
    btn.replaceChildren(
      h('span', { class: 'week-top' }, iconEl('recap', 16), h('span', { class: 'sb-h' }, 'This week'), h('span', { class: 'week-dates' }, weekLabel(cur))),
      h('span', { id: 'weekNumbers', class: 'week-nums' }, parts.length ? parts.join(' \u00b7 ') : 'Nothing done yet this week'),
      h('span', { class: 'week-open' }, 'Open the week'));
  }
  function refresh() {
    if (!countEl) return;
    renderUrgent(); renderDue(); renderWeek();
    const n = WORLD.N;
    $('#mapSize').textContent = n + ' by ' + n + ' plots';
    $('#btnGrow').disabled = n >= WORLD.MAX_N;
    $('#btnShrink').disabled = n <= WORLD.MIN_N;
    const total = DB.projects.length;
    countEl.replaceChildren();
    if (!total) { countEl.append('No projects yet. Use New project to put up the first building.'); return; }
    if (filterActive()) {
      const shown = DB.projects.filter(matchesFilter).length;
      countEl.append('Showing ', h('b', null, String(shown)), ' of ', h('b', null, String(total)), total === 1 ? ' project' : ' projects');
    } else {
      countEl.append(h('b', null, String(total)), total === 1 ? ' project' : ' projects');
      const urg = DB.projects.map(p => urgencyOf(p).color), red = urg.filter(c => c === 'red').length, yel = urg.filter(c => c === 'yellow').length;
      if (red || yel) countEl.append(h('span', { class: 'urg-count' }, red ? h('span', { class: 'urg-red' }, red + ' red') : null, red && yel ? ', ' : null, yel ? h('span', { class: 'urg-yel' }, yel + ' yellow') : null));
    }
  }
  function setSaveStatus(ok) {
    if (!saveEl) return;
    const alertEl = $('#saveAlert');
    if (ok && Store.persistent()) { saveEl.textContent = 'Saved in this browser.'; saveEl.classList.remove('bad'); if (alertEl) alertEl.hidden = true; return; }
    saveEl.textContent = Store.persistent()
      ? 'Saving failed because browser storage is full. Export a backup now.'
      : 'Not saving: this browser blocks storage for local files. Export a backup before closing.';
    saveEl.classList.add('bad');
    if (alertEl) { alertEl.textContent = saveEl.textContent; alertEl.hidden = false; }      // something is wrong: it shows outside the collapsible
  }

  async function exportAll() {
    persistSoon.flush();
    const out = await buildBackup();
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'nullovation-city-backup-' + ymd() + '.json' });
    document.body.append(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
    toast('Backup exported with ' + out.projects.length + (out.projects.length === 1 ? ' project.' : ' projects.'));
  }

  /* One exported project joins the city on the first free plot; it never replaces anything. */
  async function importProject(data) {
    const free = [];
    for (let v = 0; v < WORLD.N; v++) for (let u = 0; u < WORLD.N; u++) if (!DB.projects.some(p => p.plot && p.plot.u === u && p.plot.v === v)) free.push({ u, v });
    if (!free.length) { toast('Every plot is taken. Grow the map, then import the project again.', 'error'); return; }
    const raw = Object.assign({}, data.project, { id: uid('p'), plot: free[0] });
    const [item] = sanitizeProjects([raw]);
    if (!item) { toast('That project file could not be read.', 'error'); return; }
    const p = item.p;
    p.art.has = false;
    const url = data.art && typeof data.art.dataUrl === 'string' && /^data:image\//.test(data.art.dataUrl) ? data.art.dataUrl : null;
    if (url) { try { await Store.putArt(p.id, url); await Art.set(p.id, url); p.art.has = true; } catch (e) { /* skip unreadable art */ } }
    logActivity(p, 'Imported into this city');
    DB.projects.push(p);
    persistNow(); refresh(); MapView.invalidate();
    MapView.select(p.id);
    toast('Imported ' + p.name + ' on a free plot.');
  }

  async function importFile(file) {
    let data;
    try { data = JSON.parse(await file.text()); } catch (e) { toast('That file is not valid JSON. Pick a backup exported from Nullovation City.', 'error'); return; }
    if (data && data.kind === 'project' && data.project) { await importProject(data); return; }
    if (!data || !Array.isArray(data.projects)) { toast('That file has no projects list, so it is not a Nullovation City backup.', 'error'); return; }
    const prevSize = WORLD.N;
    setWorldSize(worldSizeFrom(data));           // a backup restores its own map size
    const items = sanitizeProjects(data.projects);
    setWorldSize(prevSize);
    const ok = await Confirm.ask({
      title: 'Replace your projects?',
      body: 'This replaces the ' + DB.projects.length + ' project' + (DB.projects.length === 1 ? '' : 's') + ' in this browser with the ' + items.length + ' in the backup.',
      confirm: 'Replace projects', danger: true,
    });
    if (!ok) return;
    FullView.close(); MapView.deselect(); MapView.cancelMode();
    for (const p of DB.projects) { await Store.deleteArt(p.id); Art.drop(p.id); MapView.dropCache(p.id); }
    setWorldSize(worldSizeFrom(data));
    DB.world = { size: WORLD.N };
    MapView.applyWorld();
    DB.projects = items.map(x => x.p);
    let lost = 0;
    for (const { p, raw } of items) {
      const url = raw.art && typeof raw.art.dataUrl === 'string' && /^data:image\//.test(raw.art.dataUrl) ? raw.art.dataUrl : null;
      p.art.has = false;
      if (!url) continue;
      try {
        const kept = await Store.putArt(p.id, url);
        await Art.set(p.id, url);
        p.art.has = true;
        if (!kept) lost++;
      } catch (e) { /* skip unreadable art */ }
    }
    persistNow();
    MapView.frameAll(); MapView.invalidate(); refresh();
    const dropped = data.projects.length - items.length;
    let msg = 'Imported ' + items.length + (items.length === 1 ? ' project.' : ' projects.');
    if (dropped > 0) msg += ' ' + dropped + ' did not fit on the map.';
    if (lost) msg += ' Some art is held for this session only.';
    toast(msg, dropped || lost ? 'error' : '');
  }

  function toggleDrawer(force) {
    const m = $('#menu');
    const open = typeof force === 'boolean' ? force : !m.classList.contains('open');
    m.classList.toggle('open', open);
    $('#menuToggle').setAttribute('aria-expanded', String(open));
  }
  const closeDrawer = () => toggleDrawer(false);

  return { init, refresh, setSaveStatus, closeDrawer };
})();
