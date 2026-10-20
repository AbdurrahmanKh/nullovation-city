(function boot() {
  const saved = Store.load();
  /* Before version 3 the crowd size was kept in this browser; it moves into the city once, so nothing changes. */
  const oldCrowd = (() => { try { return localStorage.getItem('nullovation-city:crowds'); } catch (e) { return null; } })();
  if (saved && Array.isArray(saved.projects)) {
    setWorld(worldFrom(saved));
    DB = { app: 'nullovation-city', version: 3, world: worldState(), city: sanitizeCity(saved.city, oldCrowd), projects: sanitizeProjects(saved.projects).map(x => x.p) };
    archiveDueTasks();                                     // done tasks past their 7 days go to the archive (A2a, D1)
    Store.save(DB);
  } else {
    DB = { app: 'nullovation-city', version: 3, world: worldState(), city: sanitizeCity(null, oldCrowd), projects: seedProjects() };
    DB.projects.forEach(backfillActivity);   // seeds start with their history, like saved projects do
    Store.save(DB);
  }

  Menu.init();
  Bubble.init();
  MapView.init();
  Settings.init();
  Reports.init();
  Garbage.refresh();                                       // the garbage already lying there, with no truck
  Gus.init();                                              // the Garbage Man, and his first word of the day
  Proxima.init();                                          // the Productivity Inspector: a weekly or monthly report, after Gus
  Menu.refresh();                                          // the side bar's tiny buildings need the map's ground art

  const ui = Store.loadUi();
  const c = ui && ui.cam;
  if (c && [c.x, c.y, c.z].every(n => typeof n === 'number' && isFinite(n))) MapView.setCam(c);
  else MapView.frameAll();

  for (const p of DB.projects) if (p.art.has) Art.load(p.id);
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
  DataFile.init();
  Backups.init();
  ClaudeWork.init();

  /* Esc backs out of one layer at a time. The full view always closes on Esc. Edit City ends before Settings closes. */
  window.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (OpenInClaude.close(true)) return;
    if (Wheel.close()) return;
    if (Ghosts.closeCard()) return;
    if (Confirm.isOpen()) { Confirm.cancel(); return; }
    if (Panel.isOpen()) { Panel.close(); return; }
    if (FullView.isOpen()) { FullView.escape(); return; }
    if (MapView.cancelMode()) return;
    if (MapView.setEditing(false)) return;
    if (MapView.deselect()) return;
    if (Settings.close()) return;
    if (Reports.close()) return;
    Menu.closeDrawer();
  });
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
    if (ymd() === today) return;
    today = ymd();
    if (archiveDueTasks()) { persistSoon(); Menu.refresh(); }
    const a = document.activeElement;
    if (FullView.isOpen() && !(a && (a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)))) FullView.render();
  }, 60000);
})();
