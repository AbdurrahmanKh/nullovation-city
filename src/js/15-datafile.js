/*
  DataFile: an optional JSON file on disk that mirrors every save, so clearing the
  browser loses nothing. Uses the File System Access API (Chrome and Edge only).
  The file has the same format as an exported backup, so Import restores it.
*/
const DataFile = (() => {
  const supported = typeof window.showSaveFilePicker === 'function';
  let handle = null, state = supported ? 'off' : 'unsupported', lastSaved = 0, busy = false, again = false;
  let reason = '';                                    // why the last save failed: 'moved' or 'busy'
  let RETRIES = [1000, 3000, 8000];                   // quiet retries before a busy file counts as failed

  /* One writer at a time: the tab you are using writes the file, and any other Nullovation City tab
     stands by, so two versions open side by side never write over each other. */
  const TAB_ID = Math.random().toString(36).slice(2) + Date.now().toString(36);
  const WRITER_KEY = 'nullovation-city:fileWriter';
  function writerId() { try { const v = JSON.parse(localStorage.getItem(WRITER_KEY) || 'null'); return v && v.id; } catch (e) { return null; } }
  const isWriter = () => { const w = writerId(); return !w || w === TAB_ID; };
  function claim() {
    if (!handle || !(state === 'on' || state === 'standby')) return;
    if (writerId() !== TAB_ID) { try { localStorage.setItem(WRITER_KEY, JSON.stringify({ id: TAB_ID, at: Date.now() })); } catch (e) { /* this tab only */ } }
    if (state === 'standby') { state = 'on'; render(); }
  }
  window.addEventListener('storage', e => {
    if (e.key === WRITER_KEY && state === 'on' && !isWriter()) { state = 'standby'; render(); }
  });
  const using = () => { if (state === 'standby' || (state === 'on' && writerId() !== TAB_ID)) claim(); };
  window.addEventListener('focus', using);
  window.addEventListener('pointerdown', using, true);
  window.addEventListener('keydown', using, true);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') using(); });

  async function init() {
    if (!supported) { render(); return; }
    handle = await Store.getHandle();
    if (!handle) { state = 'off'; render(); return; }
    try {
      const perm = await handle.queryPermission({ mode: 'readwrite' });
      state = perm === 'granted' ? 'on' : 'paused';
    } catch (e) { state = 'paused'; }
    if (state === 'on') claim();                      // the tab opened last takes over
    render();
    if (state === 'on') writeSoon();
  }
  async function connect() {
    let h;
    try {
      h = await window.showSaveFilePicker({
        suggestedName: 'nullovation-city-data.json',
        types: [{ description: 'Nullovation City data', accept: { 'application/json': ['.json'] } }],
      });
    } catch (e) {
      if (e && e.name === 'AbortError') return;
      toast('That file could not be used. Pick a different file.', 'error');
      return;
    }
    handle = h; state = 'on'; reason = '';
    claim();
    const kept = await Store.putHandle(h);
    await writeNow();
    render();
    if (state === 'on') toast(kept ? 'Now also saving to ' + h.name + '.' : 'Saving to ' + h.name + ' until you close this tab. Pick it again next time.');
  }
  async function allow() {
    if (!handle) return;
    try {
      const perm = await handle.requestPermission({ mode: 'readwrite' });
      state = perm === 'granted' ? 'on' : 'paused';
    } catch (e) { state = 'paused'; }
    if (state === 'on') { reason = ''; claim(); await writeNow(); }
    render();
  }
  function tryAgain() { if (!handle) return; state = 'on'; reason = ''; claim(); render(); writeNow(); }
  async function stop() {
    handle = null; state = 'off';
    await Store.deleteHandle();
    render();
    toast('Stopped saving to the file. The file itself is untouched.');
  }
  /* A save. A file that is busy for a moment, held by a sync app or a scan, gets quiet retries;
     a moved file, or permission that ended, is said plainly with its fix. */
  async function writeNow(attempt = 0) {
    if (state !== 'on' || !handle) return;
    if (!isWriter()) { state = 'standby'; render(); return; }
    if (busy) { again = true; return; }
    busy = true;
    let err = null;
    try {
      const data = await buildBackup();
      const put = async () => { const w = await handle.createWritable(); await w.write(JSON.stringify(data, null, 2)); await w.close(); };
      if (navigator.locks && navigator.locks.request) await navigator.locks.request('nullovation-city:dataFile', put);   // never two writes at once
      else await put();
      lastSaved = Date.now(); reason = '';
    } catch (e) { err = e; }
    busy = false;
    if (err) {
      const name = err && err.name;
      if (name === 'NotFoundError') { state = 'failed'; reason = 'moved'; }
      else if (name === 'NotAllowedError' || name === 'SecurityError') {
        let perm = 'prompt';
        try { perm = await handle.queryPermission({ mode: 'readwrite' }); } catch (x) { /* treat as ended */ }
        if (perm === 'granted') { state = 'failed'; reason = 'busy'; } else state = 'paused';
      } else if (attempt < RETRIES.length) {
        setTimeout(() => writeNow(attempt + 1), RETRIES[attempt]);
        return;
      } else { state = 'failed'; reason = 'busy'; }
    }
    render();
    if (again) { again = false; writeSoon(); }
  }
  const writeSoon = debounce(() => { writeNow(); }, 1200);

  function render() {
    const box = $('#fileBox');
    if (!box) return;
    const name = handle ? handle.name : '';
    const kids = [];
    if (state === 'unsupported') {
      kids.push(h('p', { class: 'save-status' }, 'Keeping a data file works in Chrome and Edge.'));
    } else if (state === 'off') {
      kids.push(h('button', { class: 'btn', type: 'button', onclick: connect }, 'Keep a data file'));
      kids.push(h('p', { class: 'save-status' }, 'A JSON file on disk that updates on every change, so clearing the browser loses nothing.'));
    } else if (state === 'on') {
      kids.push(h('p', { class: 'save-status file-on' }, 'Also saving to this file' + (lastSaved ? ', ' + relAgo(lastSaved) : '') + ':'));
      kids.push(pathLine(name));
      kids.push(h('p', { class: 'save-status' }, editingFolder ? null : h('button', { class: 'linkish', type: 'button', title: 'Browsers keep a file\u2019s full path private, so type its folder once and it shows here', onclick: () => { editingFolder = true; render(); const f = $('#dataFolder'); if (f) f.focus(); } }, folder() ? 'Change the folder' : 'Add its folder'),
        editingFolder ? null : ' \u00b7 ', h('button', { class: 'linkish', type: 'button', onclick: stop }, 'Stop')));
      if (editingFolder) kids.push(h('input', { id: 'dataFolder', class: 'field', type: 'text', dir: 'ltr', value: folder(), spellcheck: 'false', autocomplete: 'off',
        placeholder: 'For example: C:\\Users\\you\\Documents', 'aria-label': 'The data file\u2019s folder',
        onkeydown: e => {
          if (e.key === 'Enter') { e.preventDefault(); setFolder(e.target.value); editingFolder = false; render(); }
          else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); editingFolder = false; render(); }
        },
        onblur: e => { if (editingFolder) { setFolder(e.target.value); editingFolder = false; render(); } } }));
    } else if (state === 'paused') {
      kids.push(h('button', { class: 'btn', type: 'button', onclick: allow }, 'Allow saving to the file'));
      kids.push(h('p', { class: 'save-status' }, 'Saving to ', h('b', { dir: 'auto' }, name), ' is paused until you allow it. ',
        h('button', { class: 'linkish', type: 'button', onclick: stop }, 'Stop')));
    } else if (state === 'standby') {
      kids.push(h('p', { class: 'save-status' }, 'Another Nullovation City tab is saving to ', h('b', { dir: 'auto' }, name), '. This tab takes over as soon as you use it.'));
      kids.push(pathLine(name));
    } else if (reason === 'busy') {
      kids.push(h('button', { class: 'btn', type: 'button', onclick: tryAgain }, 'Try saving again'));
      kids.push(h('p', { class: 'save-status bad' }, 'Saving to ', h('b', { dir: 'auto' }, name), ' failed: the file stayed busy, perhaps held by another program such as a sync app. ',
        h('button', { class: 'linkish', type: 'button', onclick: connect }, 'Pick the file again')));
    } else {
      kids.push(h('button', { class: 'btn', type: 'button', onclick: connect }, 'Pick the data file again'));
      kids.push(h('p', { class: 'save-status bad' }, 'Saving to ', h('b', { dir: 'auto' }, name), ' failed: the file was moved, renamed, or deleted.'));
    }
    box.replaceChildren(...kids);
    /* Paused or failed saving is something wrong: it also shows outside the collapsible, with its fix. */
    const alertEl = $('#fileAlert');
    if (alertEl) {
      if (state === 'paused') alertEl.replaceChildren(h('span', null, 'Saving to ', h('b', { dir: 'auto' }, name), ' is paused. '), h('button', { class: 'linkish', type: 'button', onclick: allow }, 'Allow it'));
      else if (state === 'failed' && reason === 'busy') alertEl.replaceChildren(h('span', null, 'Saving to ', h('b', { dir: 'auto' }, name), ' failed: the file was busy. '),
        h('button', { class: 'linkish', type: 'button', onclick: tryAgain }, 'Try again'), ' \u00b7 ', h('button', { class: 'linkish', type: 'button', onclick: connect }, 'Pick the file again'));
      else if (state === 'failed') alertEl.replaceChildren(h('span', null, 'Saving to ', h('b', { dir: 'auto' }, name), ' failed: it was moved or deleted. '), h('button', { class: 'linkish', type: 'button', onclick: connect }, 'Pick the file again'));
      alertEl.hidden = !(state === 'paused' || state === 'failed');
    }
  }
  /* The folder is typed by you: browsers never hand a page a file's full path. */
  let editingFolder = false;
  const FOLDER_KEY = 'nullovation-city:dataFolder';
  function folder() { try { return localStorage.getItem(FOLDER_KEY) || ''; } catch (e) { return ''; } }
  function setFolder(v) { try { const s = String(v || '').trim(); if (s) localStorage.setItem(FOLDER_KEY, s); else localStorage.removeItem(FOLDER_KEY); } catch (e) { /* this visit only */ } }
  function pathLine(name) {
    const dir = folder(), sep = dir.includes('\\') ? '\\' : '/';
    return h('p', { class: 'file-path', dir: 'ltr' }, dir ? h('span', { class: 'fp-dir' }, dir.replace(/[\\/]+$/, '') + sep) : null, h('span', { class: 'fp-name' }, name));
  }
  /* "Saved 2 minutes ago" stays current */
  setInterval(() => { if (state === 'on') render(); }, 60000);

  return { init, writeSoon, writeNow, state: () => state, reason: () => reason, isWriter,
    _test: { use: h => { handle = h; state = 'on'; reason = ''; claim(); render(); }, fast: () => { RETRIES = [60, 120, 180]; } } };
})();
