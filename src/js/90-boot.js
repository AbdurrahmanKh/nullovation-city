(function boot() {
  const saved = Store.load();
  /* Before version 3 the crowd size was kept in this browser; it moves into the city once, so nothing changes. */
  const oldCrowd = (() => { try { return localStorage.getItem('nullovation-city:crowds'); } catch (e) { return null; } })();
  if (saved && Array.isArray(saved.projects)) {
    setWorld(worldFrom(saved));
    DB = { app: 'nullovation-city', version: 3, world: worldState(), city: sanitizeCity(saved.city, oldCrowd), leaders: sanitizeLeaders(saved.leaders), projects: sanitizeProjects(saved.projects).map(x => x.p) };
    tidyLeaders();
    archiveDueTasks();                                     // done tasks past their 7 days go to the archive (A2a, D1)
    logOverdue();                                          // a task gone overdue, a line in Activity (0.1.69)
    Store.save(DB);
  } else {
    DB = { app: 'nullovation-city', version: 3, world: worldState(), city: sanitizeCity(null, oldCrowd), leaders: [], projects: seedProjects() };
    DB.projects.forEach(backfillActivity);   // seeds start with their history, like saved projects do
    Store.save(DB);
  }

  Menu.init();
  Leaders.init();
  Bubble.init();
  MapView.init();
  Settings.init();
  Reports.init();
  AllTasks.init();
  Garbage.refresh();                                       // the garbage already lying there, with no truck
  Gus.init();                                              // the Garbage Man, and his first word of the day
  Proxima.init();                                          // the Productivity Inspector: a weekly or monthly report, after Gus
  News.init();                                             // the leaders' news, after Gus and Proxima (0.1.59)
  Menu.refresh();                                          // the side bar's tiny buildings need the map's ground art

  const ui = Store.loadUi();
  const c = ui && ui.cam;
  if (c && [c.x, c.y, c.z].every(n => typeof n === 'number' && isFinite(n))) MapView.setCam(c);
  else MapView.frameAll();

  for (const p of DB.projects) if (p.art.has) Art.load(p.id);
  Leaders.loadAll();                                       // the leaders' portraits, from the art store
  // the generic buildings and the lot scenes, decoded once, a few at a time so the page stays responsive
  (async () => {
    const jobs = [...GENERICS.map(g => ['g:' + g.id, g.url]), ...LOTS.map(l => ['lot:' + l.id, l.url]),
      ...PROPS.flatMap(p => [['prop:' + p.id + ':front', p.front], ['prop:' + p.id + ':back', p.back]])];
    for (const [key, url] of jobs) {
      try { await Art.set(key, url); } catch (e) {}
      await new Promise(r => setTimeout(r, 0));
    }
    Menu.refresh();                                        // the side bar's tiny buildings, now with their real art
  })();
  AppInstall.init();                                       // Install, in Settings, Saving (0.1.67)
  DataFile.init();
  Backups.init();
  ClaudeWork.init();
  Sync.init();                                             // the shared copy on GitHub, and the other tabs following (0.1.73)

  /* Esc backs out of one layer at a time: a leader's editor, the project view, All tasks, then the side bar's panels.
     Edit City ends before Settings closes. */
  window.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (OpenInClaude.close(true)) return;
    if (Wheel.close()) return;
    if (Ghosts.closeCard()) return;
    if (Confirm.isOpen()) { Confirm.cancel(); return; }
    if (Panel.isOpen()) { Panel.close(); return; }
    if (Leaders.editorOpen()) { Leaders.escape(); return; }  // a leader's editor sits over the project view and All tasks (0.1.64)
    if (FullView.isOpen()) { FullView.escape(); return; }
    if (MapView.cancelMode()) return;
    if (MapView.setEditing(false)) return;
    if (MapView.deselect()) return;
    if (AllTasks.close()) return;                          // on the map, over the side bar's panels (0.1.64)
    if (Settings.close()) return;
    if (Reports.close()) return;
    if (Leaders.escape()) return;                          // the list closes (0.1.61)
    Menu.closeDrawer();
  });
  /* A phone's back (0.1.75, G2): Android's back gesture or button closes what is open, one layer at a time, as Esc does,
     but keeping what was typed, as Done does; on the bare map it leaves the city, as before. While something is open on a
     touch screen, one entry in the browser's history stands guard: back takes it away, the city closes one layer, and
     stands guard again while more is open. Once everything is closed another way, the guard goes. */
  (() => {
    let guarded = false, skip = 0;
    const drawer = () => $('#menu').classList.contains('open');
    const openNow = () => QuickAdd.isOpen() || !!$('.dropup') || OpenInClaude.isOpen() || Wheel.isOpen() || Ghosts.cardOpen()
      || Confirm.isOpen() || Panel.isOpen() || Leaders.editorOpen() || FullView.isOpen() || MapView.placing() || MapView.moving()
      || MapView.editing() || Bubble.isOpen() || AllTasks.isOpen() || Settings.isOpen() || Reports.isOpen() || Leaders.isOpen() || drawer();
    function one() {
      if (QuickAdd.isOpen()) { QuickAdd.close(); return; }
      if (MapView.closeDrop()) return;
      if (OpenInClaude.close()) return;
      if (Wheel.close()) return;
      if (Ghosts.closeCard()) return;
      if (Confirm.isOpen()) { Confirm.cancel(); return; }
      if (Panel.isOpen()) { Panel.close(); return; }
      if (Leaders.editorOpen()) { Leaders.escape(); return; }
      if (FullView.isOpen()) { FullView.back(); return; }
      if (MapView.cancelMode()) return;
      if (MapView.setEditing(false)) return;
      if (MapView.deselect()) return;
      if (AllTasks.close()) return;
      if (Settings.close()) return;
      if (Reports.close()) return;
      if (Leaders.escape()) return;
      Menu.closeDrawer();
    }
    function guard() {
      if (!touchScreen()) return;
      const open = openNow();
      if (open && !guarded) { history.pushState({ nc: 'back' }, ''); guarded = true; }
      else if (!open && guarded) { guarded = false; skip++; history.back(); }
    }
    window.addEventListener('popstate', () => {
      if (skip) { skip--; return; }
      if (!guarded) return;
      guarded = false;
      one();
      setTimeout(guard, 0);
    });
    if (history.state && history.state.nc === 'back') history.replaceState(null, '');   // one left by the page before a reload
    for (const ev of ['pointerup', 'keyup', 'click']) document.addEventListener(ev, () => setTimeout(guard, 0), true);
  })();
  /* The comma key opens and closes Settings, unless you are typing or a dialog is open. */
  window.addEventListener('keydown', e => {
    if (e.key !== ',' || e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
    const t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (Confirm.isOpen() || Panel.isOpen()) return;
    e.preventDefault();
    Settings.toggle();
  });
  window.addEventListener('beforeunload', () => persistSoon.flush());
  window.addEventListener('pagehide', () => persistSoon.flush());

  /* Keeps "updated" times and the light current while the page stays open. On a new day, repeats due that day come
     back and done tasks past their 7 days go to the archive, so the project view redraws too, unless something in it
     is being typed. */
  let today = ymd();
  setInterval(() => {
    Light.update(); MapView.invalidate(); Bubble.refresh(); Menu.refresh(); Backups.tick();
    if (logOverdue()) persistSoon();                       // within a minute of a task going overdue, or a date set in the past
    if (ymd() === today) return;
    today = ymd();
    if (archiveDueTasks()) { persistSoon(); Menu.refresh(); }
    const a = document.activeElement;
    if (FullView.isOpen() && !(a && (a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)))) FullView.render();
  }, 60000);
})();
