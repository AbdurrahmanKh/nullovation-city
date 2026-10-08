/* Settings: the side bar turns into them, one tab at a time. Changes apply at once and are saved, with no toast;
   actions such as Export keep theirs. A setting that differs from its default shows a dot, and so does its tab.
   What the city is like (DB.city) travels with it in the data file and backups; how this computer shows it (the
   bar's buttons, motion, the postcard, folder links) stays in this browser. Resetting touches settings only. */
const Settings = (() => {
  const UI_KEY = 'nullovation-city:settings';
  const TABS = [
    { id: 'city', label: 'City', icon: 'brand' }, { id: 'life', label: 'Life', icon: 'walker' }, { id: 'look', label: 'Look', icon: 'sun' },
    { id: 'projects', label: 'Projects', icon: 'flag' }, { id: 'saving', label: 'Saving', icon: 'disk' }, { id: 'links', label: 'Links', icon: 'folder' },
  ];
  const LIFE = ['cars', 'buses', 'drones', 'cyclists', 'walkers', 'street', 'walk', 'crowd'];
  const PROPS_KEYS = ['props', 'busstop', 'vending', 'billboard', 'bin', 'amount', 'deal'];
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

  /* Every setting: the tab it sits in, how to read it, its default, and how to set it. */
  const city = k => ({ get: () => DB.city[k], def: () => CITY_DEFAULTS[k], set: v => setCity(k, v) });
  const DEFS = {
    props: { tab: 'city', ...city('props') }, busstop: { tab: 'city', ...city('busstop') }, vending: { tab: 'city', ...city('vending') },
    billboard: { tab: 'city', ...city('billboard') }, bin: { tab: 'city', ...city('bin') }, amount: { tab: 'city', ...city('amount') },
    deal: { tab: 'city', ...city('deal') },
    traffic: { tab: 'life', get: () => Traffic.isOn(), def: () => true, set: v => { Traffic.setOn(v); MapView.syncBar(); MapView.invalidate(); MapView.kick(); } },
    cars: { tab: 'life', ...city('cars') }, buses: { tab: 'life', ...city('buses') }, drones: { tab: 'life', ...city('drones') },
    cyclists: { tab: 'life', ...city('cyclists') }, walkers: { tab: 'life', ...city('walkers') },
    street: { tab: 'life', ...city('street') }, walk: { tab: 'life', ...city('walk') }, crowd: { tab: 'life', ...city('crowd') },
    light: { tab: 'look', get: () => Light.mode, def: () => 'auto', set: v => { Light.setMode(v); MapView.syncBar(); } },
    hours: { tab: 'look', get: () => [DB.city.night, DB.city.day], def: () => [CITY_DEFAULTS.night, CITY_DEFAULTS.day], set: v => { setCity('night', v[0]); setCity('day', v[1]); } },
    bubbles: { tab: 'look', get: () => MapView.bubbleMode(), def: () => 'all', set: v => { MapView.setBubbleMode(v); MapView.syncBar(); } },
    motion: { tab: 'look', get: () => Motion.mode(), def: () => Motion.dflt(), set: v => { Motion.set(v); MapView.invalidate(); MapView.kick(); } },
    caption: { tab: 'look', get: () => MapView.card().caption, def: () => MapView.CARD_DEFAULT.caption, set: v => MapView.setCard({ caption: v }) },
    cardSize: { tab: 'look', get: () => MapView.card().size, def: () => MapView.CARD_DEFAULT.size, set: v => MapView.setCard({ size: v }) },
    rest: { tab: 'projects', ...city('rest') }, away: { tab: 'projects', ...city('away') },
    explorer: { tab: 'links', get: () => explorerLinks(), def: () => false, set: v => { try { localStorage.setItem(EXPLORER_KEY, v ? '1' : '0'); } catch (e) { /* this visit only */ } if (FullView.isOpen()) FullView.render(); } },
  };
  const changedFromDefault = k => !same(DEFS[k].get(), DEFS[k].def());
  function setCity(k, v) {
    if (same(DB.city[k], v)) return;
    DB.city[k] = v;
    persistSoon();
    if (LIFE.includes(k)) Traffic.reset();
    if (k === 'night' || k === 'day') { Light.update(); MapView.syncBar(); }
    if (k === 'rest' || k === 'away') { Bubble.refresh(); Menu.refresh(); if (FullView.isOpen()) FullView.render(); }
    MapView.invalidate();
  }
  function set(k, v) { DEFS[k].set(v); refresh(); }

  /* ---------- the panel ---------- */
  let ui = (() => { try { const v = JSON.parse(localStorage.getItem(UI_KEY) || 'null'); return v && typeof v === 'object' ? v : {}; } catch (e) { return {}; } })();
  if (!TABS.some(t => t.id === ui.tab)) ui.tab = 'city';
  if (!ui.scroll || typeof ui.scroll !== 'object') ui.scroll = {};
  const writeUi = () => { try { localStorage.setItem(UI_KEY, JSON.stringify({ tab: ui.tab, scroll: ui.scroll })); } catch (e) { /* this visit only */ } };
  const saveUi = debounce(writeUi, 250);
  const isOpen = () => !$('#settings').hidden;
  function open(tab) {
    if (tab) ui.tab = tab;
    Menu.toggleDrawer(true);
    $('#sbLists').hidden = true; $('#settings').hidden = false;
    $('#menu').classList.add('in-settings');
    showTab(ui.tab);
    refresh();
    saveUi();
    const btn = $('#setTabs [aria-selected="true"]'); if (btn) btn.focus({ preventScroll: true });
  }
  function close() {
    if (!isOpen()) return false;
    MapView.setEditing(false);
    rememberScroll();
    $('#settings').hidden = true; $('#sbLists').hidden = false;
    $('#menu').classList.remove('in-settings');
    saveUi();
    $('#btnOpenSettings').focus({ preventScroll: true });
    return true;
  }
  const toggle = () => { if (isOpen()) close(); else open(); };
  function rememberScroll() { ui.scroll[ui.tab] = $('#menu').scrollTop; }
  function showTab(id) {
    if (isOpen() && id !== ui.tab) rememberScroll();
    ui.tab = id;
    for (const b of $$('#setTabs .set-tab')) { const on = b.dataset.tab === id; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; }
    for (const pg of $$('#setBody .set-page')) pg.hidden = pg.dataset.tab !== id;
    $('#setTabName').textContent = TABS.find(t => t.id === id).label;
    writeUi();
    $('#btnTabReset').hidden = !TAB_RESET[id];
    $('#menu').scrollTop = ui.scroll[id] || 0;
    if (id === 'saving') StorageUse.render();
    saveUi();
  }

  /* ---------- the controls ---------- */
  /* A row of choices drawn as the bar's buttons, the current one pressed. Redrawn on every refresh, it keeps the
     keyboard's place. */
  const choiceRow = (box, options, current, onPick) => {
    const had = box.contains(document.activeElement) ? document.activeElement.dataset.value : null;
    box.replaceChildren(...options.map(o => h('button', { class: 'btn set-choice', type: 'button', 'data-value': o.value, 'aria-pressed': String(same(o.value, current)), title: o.hint || o.label,
      onclick: () => onPick(o.value) }, o.icon ? h('span', { 'aria-hidden': 'true', html: iconSvg(o.icon, 14) }) : null, h('span', null, o.label))));
    if (had != null) { const b = box.querySelector(`[data-value="${had}"]`); if (b) b.focus(); }
  };
  const DAYS = [[6, 'Sat'], [0, 'Sun'], [1, 'Mon'], [2, 'Tue'], [3, 'Wed'], [4, 'Thu'], [5, 'Fri']];   // weeks run Saturday to Friday
  const MOTIONS = [{ value: 'full', label: 'Full' }, { value: 'saver', label: 'Saver', hint: 'At most 30 frames a second' }, { value: 'still', label: 'Still', hint: 'Nothing moves' }];
  const SIZES = [{ value: 'screen', label: 'As on screen' }, { value: 'double', label: 'Doubled' }];
  const times = v => (Math.round(v * 100) / 100) + 'x';
  function slider(id, key) {
    const inp = $('#' + id);
    Object.assign(inp, { min: AMOUNTS.min, max: AMOUNTS.max, step: AMOUNTS.step });
    inp.addEventListener('input', () => { set(key, +inp.value); });
  }
  function check(id, key) { $('#' + id).addEventListener('change', e => set(key, e.target.checked)); }

  function init() {
    $('#setBack').innerHTML = iconSvg('back', 18);
    $('#setHelpBtn').innerHTML = iconSvg('help', 14);
    $('#sbGearIcon').innerHTML = iconSvg('gear', 16);
    $('#sbGearIcon').style.display = 'inline-flex';
    $('#setTabs').replaceChildren(...TABS.map(t => h('button', { class: 'set-tab', type: 'button', role: 'tab', 'data-tab': t.id, 'aria-label': t.label, title: t.label,
      onclick: () => showTab(t.id) }, h('span', { class: 'set-tab-ic', 'aria-hidden': 'true', html: iconSvg(t.icon, 18) }), h('span', { class: 'set-tab-name' }, t.label), h('i', { class: 'set-dot', 'aria-hidden': 'true' }))));
    $('#setTabs').addEventListener('keydown', e => {
      const k = TABS.findIndex(t => t.id === ui.tab);
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const next = TABS[(k + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length].id;
        showTab(next); $('#setTabs [aria-selected="true"]').focus();
      }
    });
    $('#setTabs').after(h('p', { id: 'setTabName', class: 'set-tab-title', 'aria-hidden': 'true' }));
    for (const pg of $$('#setBody .set-page')) pg.setAttribute('aria-label', TABS.find(t => t.id === pg.dataset.tab).label);
    for (const row of $$('#setBody [data-set]')) row.prepend(h('i', { class: 'set-dot', 'aria-hidden': 'true', title: 'Changed from its default' }));
    $('#setBack').addEventListener('click', close);
    $('#btnOpenSettings').addEventListener('click', () => open());
    $('#setHelpBtn').addEventListener('click', () => {
      const box = $('#setHelp'), show = box.hidden;
      box.hidden = !show; $('#setHelpBtn').setAttribute('aria-expanded', String(show));
    });
    $('#menu').addEventListener('scroll', () => { if (isOpen()) { rememberScroll(); saveUi(); } }, { passive: true });

    /* City */
    $('#btnEditCity').addEventListener('click', () => { MapView.setEditing(!MapView.editing()); refresh(); });
    check('optProps', 'props');
    for (const k of ['busstop', 'vending', 'billboard', 'bin']) check('opt' + k[0].toUpperCase() + k.slice(1), k);
    slider('optAmount', 'amount');
    $('#btnDeal').addEventListener('click', () => set('deal', DB.city.deal + 1));
    /* Life */
    check('optTraffic', 'traffic');
    for (const k of ['cars', 'buses', 'drones', 'cyclists', 'walkers']) check('opt' + k[0].toUpperCase() + k.slice(1), k);
    slider('optStreet', 'street'); slider('optWalk', 'walk');
    $('#optCrowds').addEventListener('change', e => set('crowd', e.target.value));
    /* Look */
    const hoursIn = () => { const n = $('#optNight').value, d = $('#optDay').value; if (/^\d\d:\d\d$/.test(n) && /^\d\d:\d\d$/.test(d)) set('hours', [n, d]); };
    $('#optNight').addEventListener('change', hoursIn); $('#optDay').addEventListener('change', hoursIn);
    $('#optCaption').addEventListener('change', e => set('caption', e.target.checked));
    $('#btnPalette').addEventListener('click', () => paletteCanvas().toBlob(blob => {
      if (!blob) return;
      downloadBlob(blob, 'nullovation-city-palette.png');
      toast('Palette saved: 32 colors as 8 px swatches.');
    }, 'image/png'));
    /* Projects */
    $('#optAway').addEventListener('change', e => set('away', parseYmd(e.target.value) != null ? e.target.value : ''));
    $('#btnAwayClear').addEventListener('click', () => set('away', ''));
    /* Links */
    check('optExplorer', 'explorer');
    $('#btnFolderSetup').addEventListener('click', () => {
      downloadBlob(new Blob([FOLDER_SETUP_PS1], { type: 'text/plain' }), 'nullovation-folder-links.ps1');
      toast('Saved nullovation-folder-links.ps1. Right-click it, choose Run with PowerShell, then turn on the setting.');
    });
    $('#btnFolderTest').addEventListener('click', () => {
      const a = h('a', { href: explorerHref('C:\\Windows') });
      document.body.append(a); a.click(); a.remove();
      toast('Opening C:\\Windows through a folder link. If nothing opens, the setup has not run on this PC.');
    });
    /* Resets */
    $('#btnTabReset').addEventListener('click', () => resetTab(ui.tab));
    $('#btnResetAll').addEventListener('click', async () => {
      const ok = await Confirm.ask({ title: 'Reset all settings?', body: 'Every setting goes back to its default, in the city and on this computer. Your projects, the map, and the parks you picked stay as they are.', confirm: 'Reset all settings', danger: true });
      if (ok) for (const t of TABS) resetTab(t.id);
    });
    showTab(ui.tab);
    refresh();
  }
  /* What each tab's Reset to defaults puts back. The Saving tab holds connections, not preferences, so it has none. */
  const TAB_RESET = {
    city: () => { for (const k of PROPS_KEYS) DEFS[k].set(DEFS[k].def()); },
    life: () => { DEFS.traffic.set(true); for (const k of LIFE) DEFS[k].set(DEFS[k].def()); },
    look: () => { for (const k of ['light', 'hours', 'bubbles', 'caption', 'cardSize']) DEFS[k].set(DEFS[k].def()); Motion.set(null); MapView.invalidate(); MapView.kick(); },
    projects: () => { DEFS.rest.set([]); DEFS.away.set(''); },
    links: () => DEFS.explorer.set(false),
  };
  function resetTab(id) { if (TAB_RESET[id]) { TAB_RESET[id](); refresh(); } }

  /* Puts every control in step with the values, and the dots on what differs from its default. */
  function refresh() {
    if (!$('#setTabs') || !$('#setTabs').children.length) return;
    const c = DB.city;
    $('#mapSize').textContent = WORLD.NU + ' by ' + WORLD.NV + ' plots';
    $('#btnEditCity').textContent = MapView.editing() ? 'Done editing' : 'Edit City';
    $('#btnEditCity').setAttribute('aria-pressed', String(MapView.editing()));
    $('#optProps').checked = c.props;
    for (const k of ['busstop', 'vending', 'billboard', 'bin']) { const el = $('#opt' + k[0].toUpperCase() + k.slice(1)); el.checked = c[k]; el.disabled = !c.props; }
    $('#optAmount').value = c.amount; $('#optAmountOut').textContent = times(c.amount); $('#optAmount').disabled = !c.props;
    $('#btnDeal').disabled = !c.props;
    $('#optTraffic').checked = Traffic.isOn();
    for (const k of ['cars', 'buses', 'drones', 'cyclists', 'walkers']) $('#opt' + k[0].toUpperCase() + k.slice(1)).checked = c[k];
    $('#optStreet').value = c.street; $('#optStreetOut').textContent = times(c.street);
    $('#optWalk').value = c.walk; $('#optWalkOut').textContent = times(c.walk);
    $('#optCrowds').value = c.crowd;
    choiceRow($('#optLight'), MapView.lightOptions(), Light.mode, v => set('light', v));
    if (document.activeElement !== $('#optNight')) $('#optNight').value = c.night;
    if (document.activeElement !== $('#optDay')) $('#optDay').value = c.day;
    choiceRow($('#optBubbles'), MapView.bubbleOptions(), MapView.bubbleMode(), v => set('bubbles', v));
    choiceRow($('#optMotion'), MOTIONS, Motion.mode(), v => set('motion', v));
    $('#motionNote').textContent = { full: 'Everything moves.', saver: 'Drawn at most 30 times a second.', still: 'Nothing moves: no traffic, and every building and park on its first frame.' }[Motion.mode()]
      + (Motion.dflt() === 'still' ? ' This computer asks for reduced motion, so Still is the default.' : '');
    $('#optCaption').checked = MapView.card().caption;
    choiceRow($('#optCardSize'), SIZES, MapView.card().size, v => set('cardSize', v));
    const dayFocus = $('#optRest').contains(document.activeElement) ? document.activeElement.dataset.day : null;
    $('#optRest').replaceChildren(...DAYS.map(([d, name]) => h('button', { class: 'btn set-day', type: 'button', 'aria-pressed': String(c.rest.includes(d)), 'data-day': d,
      title: c.rest.includes(d) ? name + ': a rest day' : name + ': counts', onclick: () => { const r = DB.city.rest; set('rest', r.includes(d) ? r.filter(x => x !== d) : [...r, d].sort()); } }, name)));
    if (dayFocus != null) $(`#optRest [data-day="${dayFocus}"]`).focus();
    if (document.activeElement !== $('#optAway')) $('#optAway').value = c.away;
    $('#btnAwayClear').disabled = !c.away;
    $('#optExplorer').checked = explorerLinks();
    /* the dots */
    const tabs = new Set();
    for (const row of $$('#setBody [data-set]')) {
      const k = row.dataset.set, on = changedFromDefault(k);
      row.classList.toggle('changed', on);
      if (on) tabs.add(DEFS[k].tab);
    }
    for (const b of $$('#setTabs .set-tab')) b.classList.toggle('changed', tabs.has(b.dataset.tab));
    $('#btnResetAll').disabled = !Object.keys(DEFS).some(changedFromDefault);
    if (ui.tab === 'saving') StorageUse.render();
  }

  /* Storage use: how much this browser holds, against its limit, so the full-storage message never comes first. */
  const StorageUse = (() => {
    const LIMIT = 5 * 1024 * 1024;                     // browsers keep about 5 MB of text per site
    const kb = n => n < 1024 * 1024 ? Math.max(1, Math.round(n / 1024)) + ' KB' : n < 1024 ** 3 ? (n / 1024 / 1024).toFixed(1) + ' MB' : Math.round(n / 1024 ** 3) + ' GB';
    function used() {
      let n = 0;
      try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); n += k.length + (localStorage.getItem(k) || '').length; } } catch (e) { /* none */ }
      return n;
    }
    let art = null;
    async function estimate() {
      try { if (navigator.storage && navigator.storage.estimate) { const e = await navigator.storage.estimate(); art = { usage: e.usage || 0, quota: e.quota || 0 }; } } catch (e) { art = null; }
      render(false);
    }
    function render(ask = true) {
      const box = $('#storageBox');
      if (!box) return;
      const n = used(), pct = Math.min(100, Math.round(n / LIMIT * 100)), tone = pct >= 80 ? 'bad' : pct >= 60 ? 'soon' : '';
      box.replaceChildren(...[
        h('p', { class: 'save-status storage-line' }, 'Projects and settings: ', h('b', null, kb(n)), ' of about 5 MB'),
        h('div', { class: 'bar storage-bar ' + tone, role: 'meter', 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': pct, 'aria-label': 'Browser storage used' }, h('i', { style: 'width:' + pct + '%' })),
        tone ? h('p', { class: 'save-status ' + (tone === 'bad' ? 'bad' : '') }, 'Close to the limit. Export a backup, and keep a data file, so nothing is lost if saving stops.') : null,
        art ? h('p', { class: 'save-status' }, 'Building art and the rest: ', h('b', null, kb(art.usage)), art.quota ? ', of ' + kb(art.quota) + ' this browser allows' : '') : null].filter(Boolean));
      if (ask) estimate();
    }
    return { render, used, LIMIT };
  })();

  return { init, open, close, toggle, isOpen, refresh, showTab, tab: () => ui.tab, resetTab, set, changed: changedFromDefault, storageUsed: () => StorageUse.used() };
})();
