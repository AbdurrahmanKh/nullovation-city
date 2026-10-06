(function boot() {
  const saved = Store.load();
  if (saved && Array.isArray(saved.projects)) {
    setWorldSize(worldSizeFrom(saved));
    DB = { app: 'nullovation-city', version: 2, world: { size: WORLD.N }, projects: sanitizeProjects(saved.projects).map(x => x.p) };
    Store.save(DB);
  } else {
    DB = { app: 'nullovation-city', version: 2, world: { size: WORLD.N }, projects: seedProjects() };
    DB.projects.forEach(backfillActivity);   // seeds start with their history, like saved projects do
    Store.save(DB);
  }

  Menu.init();
  Bubble.init();
  MapView.init();
  Menu.refresh();                                          // the side bar's tiny buildings need the map's ground art

  const ui = Store.loadUi();
  const c = ui && ui.cam;
  if (c && [c.x, c.y, c.z].every(n => typeof n === 'number' && isFinite(n))) MapView.setCam(c);
  else MapView.frameAll();

  for (const p of DB.projects) if (p.art.has) Art.load(p.id);
  // the generic buildings and the lot scenes, decoded once, a few at a time so the page stays responsive
  (async () => {
    const jobs = [...GENERICS.map(g => ['g:' + g.id, g.url]), ...LOTS.map(l => ['lot:' + l.id, l.url])];
    for (const [key, url] of jobs) {
      try { await Art.set(key, url); } catch (e) {}
      await new Promise(r => setTimeout(r, 0));
    }
    Menu.refresh();                                        // the side bar's tiny buildings, now with their real art
  })();
  DataFile.init();

  /* Esc backs out of one layer at a time. The full view always closes on Esc. */
  window.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (OpenInClaude.close(true)) return;
    if (Confirm.isOpen()) { Confirm.cancel(); return; }
    if (Panel.isOpen()) { Panel.close(); return; }
    if (FullView.isOpen()) { FullView.escape(); return; }
    if (MapView.cancelMode()) return;
    if (MapView.deselect()) return;
    Menu.closeDrawer();
  });
  window.addEventListener('beforeunload', () => persistSoon.flush());
  window.addEventListener('pagehide', () => persistSoon.flush());

  /* Keeps "updated" times and the light current while the page stays open. */
  setInterval(() => { Light.update(); MapView.invalidate(); Bubble.refresh(); Menu.refresh(); }, 60000);
})();
