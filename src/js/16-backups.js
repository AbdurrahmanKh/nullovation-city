/*
  Backups: one dated copy of the city a day, in a folder picked once, keeping the last 14 (Chrome and Edge, like the
  data file). The data file holds only the latest state, so a mistake it saves at once, such as a deleted project, can
  be undone from the day's copy. The copy is taken the first time the city is open each day, before the day's changes.
  Only files named nullovation-city-daily-YYYY-MM-DD.json are counted and pruned, so exported backups kept in the
  same folder are never touched. The folder belongs to this browser; it does not travel with the city.
*/
const Backups = (() => {
  const supported = typeof window.showDirectoryPicker === 'function';
  const KEEP = 14, NAME = /^nullovation-city-daily-(\d{4}-\d{2}-\d{2})\.json$/, HANDLE = 'backupDir';
  let dir = null, state = supported ? 'off' : 'unsupported', newest = '', kept = 0, busy = false, doneDay = '';

  async function init() {
    if (!supported) { render(); return; }
    dir = await Store.getHandle(HANDLE);
    if (!dir) { state = 'off'; render(); return; }
    try { state = (await dir.queryPermission({ mode: 'readwrite' })) === 'granted' ? 'on' : 'paused'; } catch (e) { state = 'paused'; }
    render();
    tick();
  }
  async function choose() {
    let d;
    try { d = await window.showDirectoryPicker({ id: 'nullovation-city-backups', mode: 'readwrite' }); } catch (e) {
      if (e && e.name === 'AbortError') return;
      toast('That folder could not be used. Pick a different folder.', 'error'); return;
    }
    dir = d; state = 'on'; doneDay = '';
    const stays = await Store.putHandle(d, HANDLE);
    await tick();
    if (state === 'on') toast(stays ? 'Daily backups go to ' + d.name + ', one copy a day, the last 14 kept.' : 'Daily backups go to ' + d.name + ' until you close this tab. Pick it again next time.');
  }
  async function allow() {
    if (!dir) return;
    try { state = (await dir.requestPermission({ mode: 'readwrite' })) === 'granted' ? 'on' : 'paused'; } catch (e) { state = 'paused'; }
    render();
    if (state === 'on') tick();
  }
  async function stop() {
    dir = null; state = 'off'; doneDay = ''; newest = ''; kept = 0;
    await Store.deleteHandle(HANDLE);
    render();
    toast('Stopped the daily backups. The copies already made stay in the folder.');
  }
  /* Takes today's copy if there is none yet, then keeps the newest 14. One tab does it: the one the data file uses. */
  async function tick() {
    if (state !== 'on' || !dir || busy || !DataFile.isWriter()) return;
    const today = ymd();
    if (doneDay === today) return;
    busy = true;
    try {
      const name = 'nullovation-city-daily-' + today + '.json';
      let have = true;
      try { await dir.getFileHandle(name); } catch (e) { if (e && e.name === 'NotFoundError') have = false; else throw e; }
      if (!have) {
        persistSoon.flush();
        const data = await buildBackup();
        const put = async () => { const fh = await dir.getFileHandle(name, { create: true }); const w = await fh.createWritable(); await w.write(JSON.stringify(data, null, 2)); await w.close(); };
        if (navigator.locks && navigator.locks.request) await navigator.locks.request('nullovation-city:backups', put); else await put();
      }
      const days = [];
      for await (const [n] of dir.entries()) { const m = NAME.exec(n); if (m) days.push(m[1]); }
      days.sort();
      while (days.length > KEEP) await dir.removeEntry('nullovation-city-daily-' + days.shift() + '.json');
      newest = days[days.length - 1] || ''; kept = days.length; doneDay = today;
      state = 'on';
    } catch (e) {
      const n = e && e.name;
      state = n === 'NotAllowedError' || n === 'SecurityError' ? 'paused' : 'failed';
    }
    busy = false;
    render();
  }
  function render() {
    const box = $('#backupBox');
    if (!box) return;
    const name = dir ? dir.name : '', kids = [];
    if (state === 'unsupported') kids.push(h('p', { class: 'save-status' }, 'Daily backups work in Chrome and Edge.'));
    else if (state === 'off') {
      kids.push(h('button', { class: 'btn btn-small', type: 'button', onclick: choose }, 'Pick a backups folder'));
      kids.push(h('p', { class: 'save-status' }, 'One dated copy a day, the last 14 kept, so a mistake the data file saves at once can be undone.'));
    } else if (state === 'on') {
      kids.push(h('p', { class: 'save-status file-on' }, 'A copy each day in this folder:'));
      kids.push(h('p', { class: 'file-path', dir: 'ltr' }, h('span', { class: 'fp-name' }, name)));
      kids.push(h('p', { class: 'save-status' }, newest ? 'Latest copy ' + fmtDate(parseYmd(newest)) + ', ' + plural(kept, 'copy', 'copies') + ' kept. ' : 'No copy yet. ',
        h('button', { class: 'linkish', type: 'button', onclick: stop }, 'Stop')));
    } else if (state === 'paused') {
      kids.push(h('button', { class: 'btn btn-small', type: 'button', onclick: allow }, 'Allow daily backups'));
      kids.push(h('p', { class: 'save-status' }, 'Daily backups to ', h('b', { dir: 'auto' }, name), ' are paused until you allow them. ', h('button', { class: 'linkish', type: 'button', onclick: stop }, 'Stop')));
    } else {
      kids.push(h('button', { class: 'btn btn-small', type: 'button', onclick: choose }, 'Pick a backups folder again'));
      kids.push(h('p', { class: 'save-status bad' }, 'The daily backup to ', h('b', { dir: 'auto' }, name), ' failed: the folder was moved, renamed, or deleted.'));
    }
    box.replaceChildren(...kids);
    /* Paused or failed shows in the side bar too, with its fix, like the data file. */
    const alertEl = $('#backupAlert');
    if (alertEl) {
      if (state === 'paused') alertEl.replaceChildren(h('span', null, 'Daily backups to ', h('b', { dir: 'auto' }, name), ' are paused. '), h('button', { class: 'linkish', type: 'button', onclick: allow }, 'Allow them'));
      else if (state === 'failed') alertEl.replaceChildren(h('span', null, 'The daily backup to ', h('b', { dir: 'auto' }, name), ' failed. '), h('button', { class: 'linkish', type: 'button', onclick: choose }, 'Pick the folder again'));
      alertEl.hidden = !(state === 'paused' || state === 'failed');
    }
  }
  return { init, tick, render, state: () => state, newest: () => newest, kept: () => kept, KEEP };
})();
