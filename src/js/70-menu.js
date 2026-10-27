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
      $('#newBtns').hidden = true; wrap.hidden = false; inp.value = ''; inp.focus();
    });
    /* + Task, after + New project (The City on a Phone, Round 2, A2): the line over the map, on the PC too. On a phone it
       is Menu, then + Task: the drawer closes for the line, and the focus comes back to the Menu button after it. */
    $('#taskPlusIcon').innerHTML = iconSvg('plus', 14);
    $('#taskPlusIcon').style.display = 'inline-flex';
    $('#btnTask').addEventListener('click', () => {
      MapView.cancelMode();
      if ($('#menu').classList.contains('open')) { closeDrawer(); $('#menuToggle').focus({ preventScroll: true }); }
      QuickAdd.open();
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
    /* The status brief starts a planning chat, so it sits with the week rather than in Settings: one button, Status brief,
       whose panel starts with Copy status brief, then the Claude tiles (SideBar Cleanup, 0.1.64; Open in Claude with Copy
       last until then, and Copy status brief beside it until 0.1.63). */
    $('#briefRow').append(OpenInClaude.button({ id: 'btnBriefClaude', label: 'Status brief', copyFirst: 'Copy status brief',
      title: 'The status of every project, for a Claude chat: copy it, or open it in Claude', text: () => statusBrief(), copied: 'Status brief copied. Paste it into any Claude chat.', small: true }));
    /* Edit City's bar: the ring as before, and Done */
    $('#btnGrow').addEventListener('click', () => { if (MapView.resizeWorld(1)) toast('Added a ring of plots.'); });
    $('#btnShrink').addEventListener('click', () => {
      if (!MapView.outerRingEmpty()) { toast('The outer ring has buildings on it. Move them inward first.', 'error'); return; }
      if (MapView.resizeWorld(-1)) toast('Removed the outer ring.');
    });
    $('#btnExport').addEventListener('click', exportAll);
    $('#btnImport').addEventListener('click', () => $('#fileImport').click());
    $('#fileImport').addEventListener('change', e => { const f = e.target.files[0]; e.target.value = ''; if (f) importFile(f); });
    $('#btnEditDone').addEventListener('click', () => { MapView.setEditing(false); Settings.refresh(); });
    $('#menuToggle').addEventListener('click', () => toggleDrawer());
    $('#menuClose').innerHTML = iconSvg('close', 18);
    $('#menuClose').addEventListener('click', () => { closeDrawer(); $('#menuToggle').focus(); });

    setSaveStatus(Store.persistent());
    refresh();
  }
  /* The side bar's panels: Leaders, Reports and Settings take its place one at a time; the lists come back once none is
     open. All tasks is on the map since 0.1.64. */
  const PANELS = ['#settings', '#reports', '#leadersPanel'];
  function listsBack() { if (PANELS.every(s => !$(s) || $(s).hidden)) $('#sbLists').hidden = false; }
  function hideNew() { $('#newWrap').hidden = true; $('#newBtns').hidden = false; }

  /* Open tasks due in the next 7 days, overdue first, each with its Open in Claude: the Claude icon, opening the panel
     with Build it, Think and Copy (SideBar Cleanup, 0.1.64; a copy button until then). */
  function renderDue() {
    const sec = $('#sbDue'), list = $('#dueList');
    if (!sec) return;
    const items = [];
    for (const p of DB.projects) for (const t of p.todos) {
      if (!isOpenTask(t) || !t.due) continue;
      const d = dueInfo(t);
      if (d && d.diff <= 6) items.push({ p, t, d });
    }
    items.sort((a, b) => a.d.diff - b.d.diff || a.p.name.localeCompare(b.p.name));
    sec.hidden = !items.length;
    const shown = items.slice(0, 8);
    list.replaceChildren(...shown.map(({ p, t, d }) => h('li', { class: 'due-item' },
      h('button', { class: 'due-task', type: 'button', title: 'Open this task', onclick: () => { closeDrawer(); FullView.openTask(p.id, t.id); } },
        h('span', { class: 'due-text', dir: 'auto' }, t.text),
        h('span', { class: 'due-meta' }, shiftTag(t), h('span', { class: 'due ' + (d.tone || '') }, (d.tone === 'late' ? '! ' : '') + d.text), h('span', { class: 'due-proj', dir: 'auto' }, p.name))),
      OpenInClaude.button({ icon: true, cls: 'due-claude', ...OpenInClaude.forTask(p, t) }))),
      ...(items.length > shown.length ? [h('li', { class: 'due-more' }, h('button', { class: 'due-more-btn', type: 'button', title: 'Every open task: All tasks (L)',
        onclick: () => AllTasks.open() }, 'and ' + (items.length - shown.length) + ' more'))] : []));
  }
  /* The city's starred task (0.1.40): its building, the task and its project, a shortcut to the task. It shows
     until the task is unstarred, ticked or deleted. */
  function renderStar() {
    const sec = $('#sbStar'), btn = $('#btnStar');
    if (!sec) return;
    const s = starredTask();
    sec.hidden = !s;
    if (!s) { btn.replaceChildren(); btn.onclick = null; return; }
    const { p, t } = s;
    btn.onclick = () => { closeDrawer(); FullView.openTask(p.id, t.id); };
    btn.setAttribute('aria-label', 'Starred: ' + t.text + ', in ' + p.name + '. Open the task.');
    btn.replaceChildren(
      h('span', { class: 'star-thumb', 'aria-hidden': 'true' }, MapView.thumb(p)),
      h('span', { class: 'star-body' },
        h('span', { class: 'star-top' }, iconEl('star', 14), h('span', { class: 'sb-h' }, 'Starred')),
        h('span', { class: 'star-text', dir: 'auto', title: t.text }, t.text),
        h('span', { class: 'star-proj', dir: 'auto' }, shiftTag(t), h('span', null, p.name))));
  }
  /* This week in numbers, each with its small icon: a tick for tasks done, a note, a milestone's flag (SideBar Cleanup,
     0.1.64). The card opens the week. */
  function renderWeek() {
    const btn = $('#btnRecap');
    if (!btn) return;
    const cur = weekStartOf(Date.now()), tot = weekOf(cur).tot, parts = weekNumbers(tot);
    const icons = [tot.done ? 'tick' : null, tot.notes ? 'doc' : null, tot.ms ? 'flag' : null].filter(Boolean);
    btn.replaceChildren(
      h('span', { class: 'week-top' }, iconEl('recap', 16), h('span', { class: 'sb-h' }, 'This week'), h('span', { class: 'week-dates' }, weekLabel(cur))),
      h('span', { id: 'weekNumbers', class: 'week-nums' }, ...(parts.length
        ? parts.map((x, i) => h('span', { class: 'week-num' }, iconEl(icons[i], 12), x))
        : ['Nothing done yet this week'])));
  }
  function refresh() {
    if (!countEl) return;
    renderStar(); renderDue(); renderWeek();
    if (typeof Leaders !== 'undefined') Leaders.renderSection();
    if (typeof News !== 'undefined') { News.check(); News.renderSection(); }   // the leaders' news and Gus, in place of Urgent (0.1.59)
    if (typeof Gus !== 'undefined') Gus.render();
    if (typeof Reports !== 'undefined') Reports.refresh();
    if (typeof AllTasks !== 'undefined') AllTasks.refresh();
    if (typeof Proxima !== 'undefined') Proxima.renderDot();
    $('#mapSize').textContent = WORLD.NU + ' by ' + WORLD.NV + ' plots';
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
    if (alertEl) { alertEl.textContent = saveEl.textContent; alertEl.hidden = false; }      // something is wrong: it shows in the side bar too
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
    for (let v = 0; v < WORLD.NV; v++) for (let u = 0; u < WORLD.NU; u++) if (!DB.projects.some(p => p.plot && p.plot.u === u && p.plot.v === v)) free.push({ u, v });
    if (!free.length) { toast('Every plot is taken. Grow the map, then import the project again.', 'error'); return; }
    const raw = Object.assign({}, data.project, { id: uid('p'), plot: free[0] });
    const [item] = sanitizeProjects([raw]);
    if (!item) { toast('That project file could not be read.', 'error'); return; }
    const p = item.p;
    p.art.has = false;
    const url = data.art && typeof data.art.dataUrl === 'string' && /^data:image\//.test(data.art.dataUrl) ? data.art.dataUrl : null;
    if (url) { try { await Store.putArt(p.id, url); await Art.set(p.id, url); p.art.has = true; } catch (e) { /* skip unreadable art */ } }
    p.leader = await Leaders.adopt(data.leader);    // its leader: one of this city's by the same name, else a new one (0.1.51)
    logActivity(p, 'Imported into this city');
    DB.projects.push(p);
    archiveDueTasks();                           // its done tasks past their 7 days go to its archive
    persistNow(); refresh(); MapView.invalidate();
    MapView.select(p.id);
    toast('Imported ' + p.name + ' on a free plot.');
  }

  async function importFile(file) {
    let data;
    try { data = JSON.parse(await file.text()); } catch (e) { toast('That file is not valid JSON. Pick a backup exported from Nullovation City.', 'error'); return; }
    if (data && data.kind === 'project' && data.project) { await importProject(data); return; }
    if (!data || !Array.isArray(data.projects)) { toast('That file has no projects list, so it is not a Nullovation City backup.', 'error'); return; }
    const prevWorld = worldState();
    setWorld(worldFrom(data));                   // a backup restores its own map, and the city's settings with it
    const items = sanitizeProjects(data.projects);
    setWorld(prevWorld);
    const ok = await Confirm.ask({
      title: 'Replace your projects?',
      body: 'This replaces the ' + DB.projects.length + ' project' + (DB.projects.length === 1 ? '' : 's') + ' in this browser with the ' + items.length + ' in the backup.',
      confirm: 'Replace projects', danger: true,
    });
    if (!ok) return;
    FullView.close(); MapView.deselect(); MapView.cancelMode();
    for (const p of DB.projects) { await Store.deleteArt(p.id); Art.drop(p.id); MapView.dropCache(p.id); }
    await Leaders.dropAll();                     // the leaders go with the projects, and the backup brings its own
    setWorld(worldFrom(data));
    DB.world = worldState();
    DB.city = sanitizeCity(data.city);           // a backup from before version 3 brings default settings
    MapView.applyWorld();
    Traffic.reset();
    DB.projects = items.map(x => x.p);
    let lost = await Leaders.restore(data.leaders);
    tidyLeaders();
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
    archiveDueTasks();
    persistNow();
    Light.update(); Settings.refresh();          // the city's settings came with it: Auto's hours, props, life
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

  return { init, refresh, setSaveStatus, closeDrawer, toggleDrawer, listsBack };
})();
