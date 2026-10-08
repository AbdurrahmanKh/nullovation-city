/*
  Store: the only code that knows where data lives.
  This local version keeps projects in localStorage and block art in IndexedDB
  (falling back to localStorage, then to memory). Moving the tool to a
  published page later means replacing this object only.
*/
const Store = (() => {
  const KEY = 'nullovation-city:v1';
  const UI_KEY = 'nullovation-city:ui';
  const ART_PREFIX = 'nullovation-city:art:';
  const memArt = new Map();

  let lsOk = false;
  try {
    const k = '__nc_probe';
    localStorage.setItem(k, '1');
    localStorage.removeItem(k);
    lsOk = true;
  } catch (e) { lsOk = false; }

  let dbPromise = null;
  function db() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise(resolve => {
      try {
        if (!window.indexedDB) return resolve(null);
        const req = indexedDB.open('nullovation-city', 2);
        req.onupgradeneeded = () => {
          for (const name of ['art', 'handles']) {
            try { if (!req.result.objectStoreNames.contains(name)) req.result.createObjectStore(name); } catch (e) { /* exists */ }
          }
        };
        req.onsuccess = () => { req.result.onversionchange = () => req.result.close(); resolve(req.result); };
        req.onerror = () => resolve(null);
        req.onblocked = () => resolve(null);
      } catch (e) { resolve(null); }
    });
    return dbPromise;
  }
  async function idb(mode, fn, store = 'art') {
    const d = await db();
    if (!d) throw new Error('IndexedDB unavailable');
    return new Promise((resolve, reject) => {
      let req;
      try {
        const tx = d.transaction(store, mode);
        req = fn(tx.objectStore(store));
        tx.oncomplete = () => resolve(req ? req.result : undefined);
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(tx.error);
      } catch (e) { reject(e); }
    });
  }

  return {
    persistent: () => lsOk,
    load() {
      if (!lsOk) return null;
      try { const raw = localStorage.getItem(KEY); return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
    },
    save(data) {
      if (!lsOk) return false;
      try { localStorage.setItem(KEY, JSON.stringify(data)); return true; } catch (e) { return false; }
    },
    loadUi() {
      if (!lsOk) return null;
      try { const raw = localStorage.getItem(UI_KEY); return raw ? JSON.parse(raw) : null; } catch (e) { return null; }
    },
    saveUi(o) {
      if (!lsOk) return;
      try { localStorage.setItem(UI_KEY, JSON.stringify(o)); } catch (e) { /* ignore */ }
    },
    async getArt(id) {
      try { const v = await idb('readonly', st => st.get(id)); if (v) return v; } catch (e) { /* fall through */ }
      if (lsOk) { try { const v = localStorage.getItem(ART_PREFIX + id); if (v) return v; } catch (e) { /* ignore */ } }
      return memArt.get(id) || null;
    },
    /* Resolves true when the art survives a reload, false when it is held in memory only. */
    async putArt(id, dataUrl) {
      try {
        await idb('readwrite', st => st.put(dataUrl, id));
        if (lsOk) { try { localStorage.removeItem(ART_PREFIX + id); } catch (e) { /* ignore */ } }
        memArt.delete(id);
        return true;
      } catch (e) { /* fall through */ }
      if (lsOk) {
        try { localStorage.setItem(ART_PREFIX + id, dataUrl); memArt.delete(id); return true; } catch (e) { /* quota */ }
      }
      memArt.set(id, dataUrl);
      return false;
    },
    /* File and folder handles (Chrome and Edge): the data file, and the daily backups' folder. Resolves false when a
       handle can only live in memory. */
    async putHandle(hdl, key = 'dataFile') { try { await idb('readwrite', st => st.put(hdl, key), 'handles'); return true; } catch (e) { return false; } },
    async getHandle(key = 'dataFile') { try { return (await idb('readonly', st => st.get(key), 'handles')) || null; } catch (e) { return null; } },
    async deleteHandle(key = 'dataFile') { try { await idb('readwrite', st => st.delete(key), 'handles'); } catch (e) { /* ignore */ } },
    async deleteArt(id) {
      try { await idb('readwrite', st => st.delete(id)); } catch (e) { /* ignore */ }
      if (lsOk) { try { localStorage.removeItem(ART_PREFIX + id); } catch (e) { /* ignore */ } }
      memArt.delete(id);
    },
  };
})();
