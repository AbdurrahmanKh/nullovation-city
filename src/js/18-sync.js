/*
  Sync (0.1.73, Quick Sync, part 1): every city that syncs keeps the same city through one shared copy in a private
  GitHub repository, until production's database (S1, picked 27 October 2026; the plan is docs/quick-sync-plan.md).
  The page writes through GitHub's API with a fine-grained token pasted once in each city, kept in this browser only,
  never in the database, the data file, a backup or an export (J1). The shared copy is city.json (the map, the city's
  settings, the leaders and the order of the projects), one file per project in projects/, and each picture once in
  art/, named by its fingerprint. A city checks every 15 seconds while in view, and when it opens or comes back into
  view; it sends 3 seconds after the last change (S2). A send goes on top of the copy the city last synced, its base;
  when another city wrote since, GitHub refuses it, and the city receives, merges and sends again, so no send is lost.
  The merge is three ways, thing by thing: a change on one side is taken, and a clash goes to the newer side (C1).
  One tab of a browser syncs, the one in use, and every other tab follows it, reading the city again when it is saved.
*/
const Sync = (() => {
  const KEY = 'nullovation-city:sync';                 // { repo, token, branch, paused, at }: this browser only
  const WRITER_KEY = 'nullovation-city:syncWriter';    // which tab syncs
  const CITY_KEY = 'nullovation-city:v1';
  const ART_KEY = 'nullovation-city:artChanged';       // a picture put or taken out, so the other tabs load it; never kept
  const API = 'https://api.github.com';
  const FORMAT = 1;                                    // the shared copy's own format
  const REPO_DEFAULT = 'AbdurrahmanKh/nullovation-city-data';
  let T = { check: 15000, send: 3000, stale: 45000, offline: 180000, retry: [1000, 2000, 4000] };
  const TAB = Math.random().toString(36).slice(2) + Date.now().toString(36);

  /* ---------- the settings in this browser ---------- */
  let testApi = '';                                    // the tests' fake GitHub, kept with the token
  function cfg() {
    try { const v = JSON.parse(localStorage.getItem(KEY) || 'null'); return v && typeof v === 'object' && v.repo && v.token ? v : null; } catch (e) { return null; }
  }
  function setCfg(v) { try { if (v) localStorage.setItem(KEY, JSON.stringify(v)); else localStorage.removeItem(KEY); } catch (e) { /* this visit only */ } }
  function editCfg(fn) { const c = cfg(); if (!c) return null; fn(c); setCfg(c); return c; }

  /* ---------- small helpers ---------- */
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  function sortKeys(x) {
    if (Array.isArray(x)) return x.map(sortKeys);
    if (x && typeof x === 'object') { const o = {}; for (const k of Object.keys(x).sort()) if (x[k] !== undefined) o[k] = sortKeys(x[k]); return o; }
    return x;
  }
  /* The same thing written in any key order reads alike, so a city never sends what did not change. */
  const canon = x => (x === undefined ? 'undefined' : JSON.stringify(sortKeys(x)));
  const same = (a, b) => canon(a) === canon(b);
  const pretty = x => JSON.stringify(sortKeys(x), null, 1) + '\n';
  const clone = x => JSON.parse(JSON.stringify(x));
  function b64Bytes(b64) {
    const bin = atob(String(b64 || '').replace(/\s/g, ''));
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  const utf8 = bytes => new TextDecoder().decode(bytes);
  const EXT = { 'image/png': 'png', 'image/gif': 'gif', 'image/jpeg': 'jpg', 'image/webp': 'webp' };
  const MIME = { png: 'image/png', gif: 'image/gif', jpg: 'image/jpeg', webp: 'image/webp' };
  const extOf = url => EXT[(/^data:([^;,]+)/.exec(url) || [])[1]] || 'png';
  const payload = url => url.slice(url.indexOf(',') + 1);
  /* A picture's fingerprint: the SHA-256 of its bytes, so each picture goes into the shared copy once. */
  async function digest(url) {
    const bytes = b64Bytes(payload(url));
    if (window.crypto && crypto.subtle) {
      const d = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
      return Array.from(d, x => x.toString(16).padStart(2, '0')).join('');
    }
    return 'h' + hashStr(payload(url)).toString(16) + bytes.length.toString(16);
  }
  const projectPath = id => 'projects/' + (/^[\w.-]{1,80}$/.test(id) ? id : 'x-' + hashStr(id).toString(16)) + '.json';
  function newerThan(a, b) {
    const pa = String(a || '').split('.').map(Number), pb = String(b || '').split('.').map(Number);
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) { const x = pa[i] || 0, y = pb[i] || 0; if (x !== y) return x > y; }
    return false;
  }
  const version = () => (typeof APP_VERSION !== 'undefined' ? APP_VERSION : '0');

  /* ---------- the pictures this browser holds, by fingerprint ---------- */
  const fps = new Map();                               // art key -> { fp, ext }
  const fileOf = k => { const f = fps.get(k); return f ? f.fp + '.' + f.ext : ''; };
  const artKeys = () => [...DB.projects.filter(p => p.art && p.art.has).map(p => p.id), ...DB.leaders.filter(l => l.portrait).map(l => portraitKey(l.id))];
  async function artUrl(k) {
    const url = await Store.getArt(k);
    if (url) return url;
    if (k.startsWith('leader:')) return typeof Leaders !== 'undefined' ? Leaders.url(k.slice(7)) : null;
    return (Art.get(k) || {}).url || null;
  }
  async function ensureFps() {
    for (const k of artKeys()) {
      if (fps.has(k)) continue;
      const url = await artUrl(k);
      if (url && /;base64,/.test(url)) fps.set(k, { fp: await digest(url), ext: extOf(url) });
    }
  }

  /* ---------- the shared copy's shape ---------- */
  const EMPTY = { world: undefined, city: {}, leaders: [], order: [], projects: {} };
  /* This city as the shared copy holds it: pictures named by fingerprint, nothing of this browser's own. */
  function sharedOf() {
    const leaders = DB.leaders.map(l => { const o = clone(l); delete o.portraitFile; if (l.portrait && fileOf(portraitKey(l.id))) o.portraitFile = fileOf(portraitKey(l.id)); return o; });
    const projects = {};
    for (const p of DB.projects) {
      const o = clone(p);
      o.art = { has: !!(p.art && p.art.has), includesPlot: !!(p.art && p.art.includesPlot) };
      if (o.art.has && fileOf(p.id)) o.art.file = fileOf(p.id);
      projects[p.id] = o;
    }
    return { world: worldState(), city: clone(DB.city), leaders, order: DB.projects.map(p => p.id), projects };
  }
  const cityPart = f => ({ world: f.world, city: f.city, leaders: f.leaders, order: f.order });

  /* ---------- the merge (reasoned in the plan, section 4) ----------
     Three ways, thing by thing: the base (the shared copy this city last synced), this city, and the shared copy now.
     A task, milestone, note, link or leader goes field by field, so a title changed in one city and a description in
     the other both stay. A thing changed on one side takes that side's version; changed on both, the newer side's
     (C1), newer by this city's last change against the time the shared copy's last send was made. A thing deleted on one side goes, unless the
     other side changed it and is the newer. An order comes from the side that changed it. Activity keeps both sides'
     lines, less those either side took out; Updated and the last work keep the later. */
  function merge(base, local, remote, localNewer) {
    const B = base || EMPTY;
    const m3 = (b, l, r) => (same(l, r) ? l : same(b, l) ? r : same(b, r) ? l : localNewer ? l : r);
    /* one side only: new there, or deleted on the other */
    const lone = (b, x, isLocal) => (b === undefined ? x : same(b, x) ? undefined : (isLocal ? localNewer : !localNewer) ? x : undefined);
    /* an item field by field; a task's own notes as a list of their own */
    function fields(b, l, r) {
      b = b || {};
      const o = {};
      for (const k of new Set([...Object.keys(l), ...Object.keys(r)])) {
        const v = k === 'notes' && (Array.isArray(l[k]) || Array.isArray(r[k])) ? list(b[k], l[k] || [], r[k] || []) : m3(b[k], l[k], r[k]);
        if (v !== undefined && !(Array.isArray(v) && !v.length && k === 'notes')) o[k] = v;
      }
      return o;
    }
    function list(bl, ll, rl, item = fields) {
      const by = a => new Map((Array.isArray(a) ? a : []).map(x => [x.id, x]));
      const bm = by(bl), lm = by(ll), rm = by(rl), out = new Map();
      for (const id of new Set([...lm.keys(), ...rm.keys()])) {
        const b = bm.get(id), l = lm.get(id), r = rm.get(id);
        const v = l !== undefined && r !== undefined ? (item ? item(b, l, r) : m3(b, l, r)) : l !== undefined ? lone(b, l, true) : lone(b, r, false);
        if (v !== undefined) out.set(id, v);
      }
      return orderOf([...bm.keys()], [...lm.keys()], [...rm.keys()], out);
    }
    /* the order from the side that changed it, else the shared copy's; what is new goes where its side had it */
    function orderOf(bo, lo, ro, out) {
      const moved = side => { const inB = new Set(bo), inS = new Set(side); return !same(side.filter(id => inB.has(id)), bo.filter(id => inS.has(id))); };
      const lMoved = moved(lo), rMoved = moved(ro);
      const [first, second] = lMoved && rMoved ? (localNewer ? [lo, ro] : [ro, lo]) : lMoved ? [lo, ro] : [ro, lo];
      const res = first.filter(id => out.has(id));
      for (let i = 0; i < second.length; i++) {
        const id = second[i];
        if (!out.has(id) || res.includes(id)) continue;
        let at = 0;
        for (let j = i - 1; j >= 0; j--) { const k = res.indexOf(second[j]); if (k >= 0) { at = k + 1; break; } }
        res.splice(at, 0, id);
      }
      return res.map(id => out.get(id));
    }
    function activity(bl, ll, rl) {
      const key = e => e.at + '|' + e.text + '|' + (e.ref || '');
      const keys = a => new Set((a || []).map(key));
      const bk = keys(bl), lk = keys(ll), rk = keys(rl), seen = new Set(), out = [];
      for (const e of [...(ll || []), ...(rl || [])]) {
        const k = key(e);
        if (seen.has(k)) continue;
        seen.add(k);
        if (bk.has(k) && !(lk.has(k) && rk.has(k))) continue;          // taken out on one side, an Undo
        out.push(e);
      }
      return out.sort((a, b) => a.at - b.at).slice(-ACTIVITY_MAX);
    }
    const LISTS = ['todos', 'milestones', 'notes', 'links'];
    function project(b, l, r) {
      b = b || {};
      const o = {};
      for (const k of new Set([...Object.keys(l), ...Object.keys(r)])) {
        if (LISTS.includes(k)) o[k] = list(b[k], l[k], r[k]);
        else if (k === 'activity') o[k] = activity(b[k], l[k], r[k]);
        else if (k === 'updatedAt' || k === 'createdAt') o[k] = Math.max(l[k] || 0, r[k] || 0) || l[k] || r[k];
        else if (k === 'urgency' && l[k] && r[k]) {
          const strip = u => (u ? Object.assign({}, u, { lastWorked: null }) : u);
          o[k] = Object.assign({}, m3(strip(b[k]), strip(l[k]), strip(r[k])));
          const lw = Math.max(l[k].lastWorked || 0, r[k].lastWorked || 0);
          o[k].lastWorked = lw || null;
        } else { const v = m3(b[k], l[k], r[k]); if (v !== undefined) o[k] = v; }
      }
      return o;
    }
    const out = { world: m3(B.world, local.world, remote.world), city: {}, leaders: list(B.leaders, local.leaders, remote.leaders) };
    for (const k of new Set([...Object.keys(local.city || {}), ...Object.keys(remote.city || {})])) {
      const v = m3((B.city || {})[k], (local.city || {})[k], (remote.city || {})[k]);
      if (v !== undefined) out.city[k] = v;
    }
    const projects = {};
    for (const id of new Set([...Object.keys(local.projects), ...Object.keys(remote.projects)])) {
      const b = (B.projects || {})[id], l = local.projects[id], r = remote.projects[id];
      const v = l && r ? project(b, l, r) : l ? lone(b, l, true) : lone(b, r, false);
      if (v) projects[id] = v;
    }
    /* one star in the city: the newer side's */
    const starred = Object.values(projects).filter(p => p.star);
    if (starred.length > 1) {
      const side = localNewer ? local : remote;
      const keep = starred.find(p => side.projects[p.id] && side.projects[p.id].star === p.star) || starred[0];
      for (const p of starred) if (p !== keep) p.star = '';
    }
    const ids = Object.keys(projects).map(id => ({ id }));
    const order = orderOf((B.order || []).slice(), (local.order || []).slice(), (remote.order || []).slice(), new Map(ids.map(x => [x.id, x.id])));
    for (const id of Object.keys(projects)) if (!order.includes(id)) order.push(id);
    out.order = order;
    out.projects = projects;
    return out;
  }

  /* ---------- applying a city in place ----------
     The database takes the new city as a backup is read, with every project, task, milestone, note, link and leader
     still there kept as the same object, so what is open on the city stays open and keeps working. */
  function refill(o, n) {
    for (const k of Object.keys(o)) if (!(k in n)) delete o[k];
    return Object.assign(o, n);
  }
  function reuseProject(o, n) {
    for (const k of ['todos', 'milestones', 'notes', 'links']) {
      const m = new Map((o[k] || []).map(x => [x.id, x]));
      n[k] = (n[k] || []).map(x => {
        const y = m.get(x.id);
        if (!y) return x;
        if (k === 'todos' && Array.isArray(x.notes)) { const nm = new Map((y.notes || []).map(z => [z.id, z])); x.notes = x.notes.map(z => (nm.has(z.id) ? refill(nm.get(z.id), z) : z)); }
        return refill(y, x);
      });
    }
    return refill(o, n);
  }
  let applying = false;
  /* next is a database as it is saved: { world, city, leaders, projects: [...] }. Resolves what changed. */
  function applyDb(next, { persist = true } = {}) {
    const before = new Map(DB.projects.map(p => [p.id, canon(p)]));
    const w = worldFrom(next), worldChanged = !same(w, worldState());
    setWorld(w);
    const city = sanitizeCity(next.city), cityChanged = !same(city, DB.city);
    const leaders = sanitizeLeaders(next.leaders), leadersBefore = canon(DB.leaders);
    const items = sanitizeProjects(next.projects);
    const keep = new Set(items.map(x => x.p.id));
    const gone = DB.projects.filter(p => !keep.has(p.id));
    const oldP = new Map(DB.projects.map(p => [p.id, p])), oldL = new Map(DB.leaders.map(l => [l.id, l]));
    DB.projects = items.map(({ p }) => (oldP.has(p.id) ? reuseProject(oldP.get(p.id), p) : p));
    DB.leaders = leaders.map(l => (oldL.has(l.id) ? refill(oldL.get(l.id), l) : l));
    refill(DB.city, city);
    DB.world = worldState();
    tidyLeaders();
    for (const p of gone) {
      Art.drop(p.id); MapView.dropCache(p.id); fps.delete(p.id);
      if (FullView.shows(p.id)) FullView.close();
      if (App.selectedId === p.id) MapView.deselect();
    }
    for (const p of DB.projects) if (before.get(p.id) !== canon(p)) MapView.dropCache(p.id);
    if (worldChanged) MapView.applyWorld();
    if (worldChanged || cityChanged) Traffic.reset();
    if (cityChanged) { Light.update(); Settings.refresh(); }
    if (persist) { applying = true; try { persistNow(); } finally { applying = false; } }
    MapView.invalidate(); Bubble.refresh(); Menu.refresh();
    if (leadersBefore !== canon(DB.leaders) && typeof Leaders !== 'undefined') Leaders.refreshAll();
    if (FullView.isOpen()) FullView.render();
    return { gone, items };
  }
  /* A merged shared copy into this city: the database, then the pictures that came with it. */
  async function applyForm(form, incoming) {
    const order = [...(form.order || []).filter(id => form.projects[id]), ...Object.keys(form.projects).filter(id => !(form.order || []).includes(id))];
    const prevLeaders = new Map(DB.leaders.map(l => [l.id, l]));
    const { gone } = applyDb({ world: form.world, city: form.city, leaders: form.leaders, projects: order.map(id => form.projects[id]) });
    for (const p of gone) await Store.deleteArt(p.id);
    for (const p of DB.projects) {
      const file = form.projects[p.id] && form.projects[p.id].art && form.projects[p.id].art.file;
      if (p.art.has && file && file !== fileOf(p.id) && incoming.has(file)) {
        const url = incoming.get(file);
        await Store.putArt(p.id, url);
        fps.set(p.id, { fp: file.split('.')[0], ext: file.split('.')[1] });
        try { await Art.set(p.id, url); } catch (e) { /* an unreadable picture stays out */ }
      } else if (!p.art.has && fileOf(p.id)) { await Store.deleteArt(p.id); Art.drop(p.id); fps.delete(p.id); }
    }
    for (const l of DB.leaders) {
      const k = portraitKey(l.id), raw = (form.leaders || []).find(x => x.id === l.id), file = raw && raw.portraitFile;
      if (l.portrait && file && file !== fileOf(k) && incoming.has(file)) {
        await Leaders.keep(l.id, incoming.get(file));
        fps.set(k, { fp: file.split('.')[0], ext: file.split('.')[1] });
      } else if (!l.portrait && fileOf(k)) { await Leaders.forget(l.id); fps.delete(k); }
    }
    for (const id of prevLeaders.keys()) if (!DB.leaders.some(l => l.id === id)) { await Leaders.forget(id); fps.delete(portraitKey(id)); }
    MapView.invalidate(); Menu.refresh();
  }

  /* ---------- GitHub ---------- */
  function fail(kind, extra = {}) { const e = new Error(kind); e.kind = kind; Object.assign(e, extra); return e; }
  const repoPath = c => '/repos/' + c.repo.split('/').map(encodeURIComponent).join('/');
  async function gh(c, method, path, body, etag) {
    const headers = { Accept: 'application/vnd.github+json', Authorization: 'Bearer ' + c.token };
    if (body) headers['Content-Type'] = 'application/json';
    if (etag) headers['If-None-Match'] = etag;
    let r;
    try { r = await fetch((c.api || API) + path, { method, headers, body: body ? JSON.stringify(body) : undefined, cache: 'no-store' }); }
    catch (e) { throw fail('network'); }
    if (r.status === 304) return { status: 304 };
    let data = null;
    try { data = await r.json(); } catch (e) { /* no body */ }
    if (r.ok) return { status: r.status, data, etag: r.headers.get('ETag') };
    const kind = r.status === 401 ? 'token' : r.status === 403 && r.headers.get('x-ratelimit-remaining') === '0' ? 'github'
      : r.status === 403 ? 'readonly' : r.status === 404 ? 'missing' : r.status === 409 ? 'empty' : 'github';
    throw fail(kind, { status: r.status, message: data && data.message });
  }
  async function treeOf(c, treeSha) {
    const t = (await gh(c, 'GET', repoPath(c) + '/git/trees/' + treeSha + '?recursive=1')).data;
    const out = {};
    for (const e of (t && t.tree) || []) if (e.type === 'blob') out[e.path] = e.sha;
    return out;
  }
  const blobText = async (c, sha) => utf8(b64Bytes((await gh(c, 'GET', repoPath(c) + '/git/blobs/' + sha)).data.content));
  /* A few at a time, so a city taking the copy for the first time does not ask for everything at once. */
  async function each(list, n, fn) {
    const q = list.slice();
    await Promise.all(Array.from({ length: Math.min(n, q.length) }, async () => { while (q.length) await fn(q.shift()); }));
  }
  /* The shared copy at a commit: its files, read again only where they changed since the base. */
  async function readCopy(c, sha, b) {
    const cm = (await gh(c, 'GET', repoPath(c) + '/git/commits/' + sha)).data;
    const tree = await treeOf(c, cm.tree.sha);
    if (!tree['city.json']) return { commit: sha, treeSha: cm.tree.sha, tree, form: null };
    let file;
    try { file = JSON.parse(await blobText(c, tree['city.json'])); } catch (e) { throw fail('broken'); }
    if (!file || file.kind !== 'shared-city') throw fail('broken');
    if ((file.format || 0) > FORMAT || (file.data || 0) > 3 || newerThan(file.wrote, version())) throw fail('newer', { wrote: file.wrote });
    const known = new Map(b && b.form ? Object.keys(b.form.projects).map(id => [projectPath(id), b.form.projects[id]]) : []);
    const projects = {};
    const paths = Object.keys(tree).filter(p => /^projects\/[^/]+\.json$/.test(p));
    await each(paths, 6, async path => {
      let p = b && b.tree[path] === tree[path] ? known.get(path) : null;
      if (!p) { try { p = JSON.parse(await blobText(c, tree[path])); } catch (e) { p = null; } }
      if (p && typeof p.id === 'string') projects[p.id] = p;
    });
    const form = { world: file.world, city: file.city || {}, leaders: Array.isArray(file.leaders) ? file.leaders : [], order: Array.isArray(file.order) ? file.order : [], projects };
    return { commit: sha, treeSha: cm.tree.sha, tree, form, at: typeof file.at === 'number' ? file.at : 0, wrote: file.wrote };
  }
  /* The pictures the shared copy names that this city may need: those that changed there since the base. */
  async function fetchArt(c, copy, b) {
    const want = new Set(), bf = b && b.form;
    for (const p of Object.values(copy.form.projects)) {
      const f = p.art && p.art.file, was = bf && bf.projects[p.id] && bf.projects[p.id].art && bf.projects[p.id].art.file;
      if (f && f !== was && f !== fileOf(p.id)) want.add(f);
    }
    for (const l of copy.form.leaders) {
      const was = bf && (bf.leaders.find(x => x.id === l.id) || {}).portraitFile;
      if (l.portraitFile && l.portraitFile !== was && l.portraitFile !== fileOf(portraitKey(l.id))) want.add(l.portraitFile);
    }
    const got = new Map();
    await each([...want].filter(f => /^[\w]+\.(png|gif|jpg|webp)$/.test(f) && copy.tree['art/' + f]), 4, async f => {
      const blob = (await gh(c, 'GET', repoPath(c) + '/git/blobs/' + copy.tree['art/' + f])).data;
      got.set(f, 'data:' + MIME[f.split('.')[1]] + ';base64,' + String(blob.content || '').replace(/\s/g, ''));
    });
    return got;
  }
  const README = '# Nullovation City, the shared copy\n\nThis private repository keeps a Nullovation City the same in every city that syncs with it. ' +
    'The cities write it themselves through GitHub\'s API: `city.json` holds the map, the city\'s settings and the leaders, `projects/` one file per project, ' +
    'and `art/` each picture once, named by its fingerprint. Each commit is one send from a city, so the history keeps a version of the city for every send.\n\n' +
    'Change the city from a city, not here. The token each city uses stays in that city\'s browser and is never written here.\n';
  /* What this city would change in the shared copy, or null when nothing. */
  function diffOf(b, local) {
    const bf = (b && b.form) || EMPTY;
    const changed = Object.keys(local.projects).filter(id => !bf.projects[id] || !same(bf.projects[id], local.projects[id]));
    const removed = Object.keys(bf.projects).filter(id => !local.projects[id]);
    const pics = [];
    for (const p of Object.values(local.projects)) if (p.art.file) pics.push([p.id, p.art.file]);
    for (const l of local.leaders) if (l.portraitFile) pics.push([portraitKey(l.id), l.portraitFile]);
    const newPics = pics.filter(([, f]) => !(b && b.tree['art/' + f])).filter((x, i, a) => a.findIndex(y => y[1] === x[1]) === i);
    const cityChanged = !b || !b.form || !same(cityPart(bf), cityPart(local));
    if (!changed.length && !removed.length && !newPics.length && !cityChanged) return null;
    return { changed, removed, newPics, cityChanged };
  }
  function message(b, local, d) {
    const name = id => (local.projects[id] || (b.form && b.form.projects[id]) || {}).name || 'a project';
    const parts = [];
    if (!b.form) parts.push('the first copy');
    else {
      if (d.changed.length) parts.push(d.changed.slice(0, 3).map(name).join(', ') + (d.changed.length > 3 ? ' and ' + (d.changed.length - 3) + ' more' : ''));
      if (d.removed.length) parts.push('took out ' + d.removed.map(name).join(', '));
      if (d.cityChanged && !parts.length) parts.push('the map and the settings');
      if (d.newPics.length) parts.push(plural(d.newPics.length, 'picture', 'pictures'));
    }
    return 'City ' + version() + ': ' + parts.join('; ');
  }
  /* One send: the files that changed and any new picture as one commit on top of the base, then the branch moved to
     it. GitHub refuses the move when another city wrote since. */
  async function send(c, local, d) {
    const R = repoPath(c), entries = [];
    for (const [key, f] of d.newPics) {
      const url = await artUrl(key);
      if (!url) continue;
      const blob = (await gh(c, 'POST', R + '/git/blobs', { content: payload(url), encoding: 'base64' })).data;
      entries.push({ path: 'art/' + f, mode: '100644', type: 'blob', sha: blob.sha });
    }
    for (const id of d.changed) entries.push({ path: projectPath(id), mode: '100644', type: 'blob', content: pretty(local.projects[id]) });
    for (const id of d.removed) entries.push({ path: projectPath(id), mode: '100644', type: 'blob', sha: null });
    const at = (cfg() || c).at || Date.now();
    entries.push({ path: 'city.json', mode: '100644', type: 'blob', content: pretty({ app: 'nullovation-city', kind: 'shared-city', format: FORMAT, data: 3, wrote: version(), at, ...cityPart(local) }) });
    if (!base.form) entries.push({ path: 'README.md', mode: '100644', type: 'blob', content: README });
    const tree = (await gh(c, 'POST', R + '/git/trees', { base_tree: base.treeSha, tree: entries })).data;
    const cm = (await gh(c, 'POST', R + '/git/commits', { message: message(base, local, d), tree: tree.sha, parents: [base.commit] })).data;
    try { await gh(c, 'PATCH', R + '/git/refs/heads/' + encodeURIComponent(c.branch || 'main'), { sha: cm.sha, force: false }); }
    catch (e) { if (e.status === 422 || e.status === 409) { refusals++; throw fail('refused'); } throw e; }   // not a fast forward: another city wrote since
    sends++;
    old.add(base.commit);
    base = { repo: c.repo, commit: cm.sha, treeSha: tree.sha, tree: await treeOf(c, tree.sha), form: local, at, wrote: version() };
    sentAt = Date.now();
    await saveBase();
  }

  /* ---------- the base, kept in IndexedDB ---------- */
  let base = null;
  const old = new Set();                               // commits this city has moved past: a lagging read of one is passed over
  async function loadBase(c) {
    const b = await Store.getSync('base');
    return b && b.repo === c.repo && b.commit ? b : { repo: c.repo, commit: null, treeSha: null, tree: {}, form: null, at: 0 };
  }
  async function saveBase() { if (base) await Store.putSync('base', base); }

  /* ---------- one tab syncs ---------- */
  function writer() { try { return JSON.parse(localStorage.getItem(WRITER_KEY) || 'null'); } catch (e) { return null; } }
  function claim(force = false) {
    const w = writer(), now = Date.now();
    if (!w || w.id === TAB || force || now - (w.at || 0) > T.stale) {
      try { localStorage.setItem(WRITER_KEY, JSON.stringify({ id: TAB, at: now })); } catch (e) { /* this tab only */ }
      return true;
    }
    return false;
  }
  const isWriter = () => { const w = writer(); return !!w && w.id === TAB; };

  /* ---------- the state, and running ---------- */
  let state = 'off', problem = '', newer = '', msg = '', lastChecked = 0, netSince = 0, netKind = '', checkedRepo = false;
  let running = false, again = false, deferred = false, hold = false, sentAt = 0, sendTimer = null, lastEtag = '', lastHead = '';
  let newerHead = '';                                  // the commit a newer city wrote, not read again until another comes
  let gen = 1, cleanGen = 0, sends = 0, refusals = 0, receives = 0;   // gen counts this city's changes; cleanGen, the last one the shared copy has
  /* Typing in a field, a question open, or Edit City: receiving waits until you leave it. */
  function busyHere() {
    const a = document.activeElement;
    if (a && (a.isContentEditable || a.tagName === 'TEXTAREA' || a.tagName === 'SELECT' ||
      (a.tagName === 'INPUT' && !/^(checkbox|radio|range|button|submit|color|file)$/i.test(a.type || '')))) return true;
    if (typeof Confirm !== 'undefined' && Confirm.isOpen()) return true;
    if (typeof MapView !== 'undefined' && (MapView.moving() || MapView.editing())) return true;
    return false;
  }
  async function head(c, fresh) {
    const r = await gh(c, 'GET', repoPath(c) + '/git/ref/heads/' + encodeURIComponent(c.branch || 'main'), null, fresh ? '' : lastEtag);
    if (r.status === 304 && lastHead) return lastHead;
    lastEtag = r.etag || ''; lastHead = r.data && r.data.object ? r.data.object.sha : '';
    return lastHead;
  }
  async function receive(c, sha) {
    const copy = await readCopy(c, sha, base);
    if (!copy.form) throw fail('broken');
    problem = '';
    const incoming = await fetchArt(c, copy, base);
    await ensureFps();
    if (busyHere()) { deferred = true; return false; }
    persistSoon.flush();                                   // a change not yet saved gets its time before it is weighed
    const local = sharedOf(), mine = (cfg() || c).at || 0;
    const merged = merge(base.form, local, copy.form, mine > copy.at);
    await applyForm(merged, incoming);
    old.add(base.commit);
    base = { repo: c.repo, commit: copy.commit, treeSha: copy.treeSha, tree: copy.tree, form: copy.form, at: copy.at, wrote: copy.wrote };
    await saveBase();
    receives++; gen++;                                     // the merge may hold this city's own changes still to send
    return true;
  }
  async function cycle() {
    const c = cfg();
    if (!c) { setState('off'); return; }
    if (c.paused) { setState('paused'); return; }
    if ((problem && problem !== 'newer') || hold) { render(); return; }   // a newer copy is still checked: one that can be read again lifts it
    if (!claim()) { base = null; setState('standby'); return; }
    if (state !== 'on') setState('on');
    if (!base || base.repo !== c.repo) base = await loadBase(c);
    if (!checkedRepo) {
      const r = (await gh(c, 'GET', repoPath(c))).data;
      if (!r || r.private !== true) throw fail('public');
      checkedRepo = true;
    }
    for (let attempt = 0; attempt <= T.retry.length; attempt++) {
      const hd = await head(c, attempt > 0);
      lastChecked = Date.now(); netSince = 0;
      if (problem === 'newer' && hd === newerHead) { render(); return; }
      if (hd && hd !== base.commit && !old.has(hd)) {
        if (busyHere()) { deferred = true; render(); return; }
        if (!(await receive(c, hd))) { render(); return; }
      }
      persistSoon.flush();
      const g = gen;
      if (cleanGen === g) { render(); return; }            // nothing changed here since the shared copy had it all
      await ensureFps();
      const local = sharedOf(), d = diffOf(base, local);
      if (!d) { cleanGen = g; render(); return; }
      try { await send(c, local, d); cleanGen = g; render(); return; }
      catch (e) { if (e.kind !== 'refused') throw e; await sleep(T.retry[attempt] || 4000); }
    }
  }
  async function run() {
    if (running) { again = true; return; }
    running = true;
    try { await cycle(); }
    catch (e) {
      if (!e.kind) console.warn('Sync:', e);              // not GitHub's answer: something in the city went wrong
      const k = e.kind || 'github';
      if (k === 'network' || k === 'github' || k === 'refused') { if (!netSince) netSince = Date.now(); netKind = k === 'network' ? 'network' : 'github'; }
      else { problem = k; if (k === 'newer') { newer = e.wrote || ''; newerHead = lastHead; } }
      render();
    }
    running = false;
    if (again) { again = false; setTimeout(run, 0); }
  }
  function setState(s) { if (state !== s) { state = s; render(); } }
  function soon() { clearTimeout(sendTimer); sendTimer = setTimeout(run, T.send); }
  let lastLoop = Date.now();
  function loop() { setInterval(() => { if (document.visibilityState === 'visible' && Date.now() - lastLoop >= T.check) { lastLoop = Date.now(); if (cfg()) run(); } }, 250); }

  /* ---------- connecting ---------- */
  async function connect() {
    const repo = (($('#syncRepo') || {}).value || '').trim().replace(/^https?:\/\/github\.com\//i, '').replace(/\.git$/, '').replace(/\/+$/, '');
    const token = (($('#syncToken') || {}).value || '').trim();
    msg = '';
    if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) { msg = 'Write the repository as its owner and name, such as ' + REPO_DEFAULT + '.'; render(); return; }
    if (!token) { msg = 'Paste the token for this device.'; render(); return; }
    const c = { repo, token, branch: 'main', paused: false, at: 0, ...(testApi ? { api: testApi } : {}) };
    state = 'connecting'; render();
    try {
      let r;
      try { r = (await gh(c, 'GET', repoPath(c))).data; }
      catch (e) {
        throw new Error(e.kind === 'token' ? 'GitHub refused the token. Check it was copied whole.'
          : e.kind === 'missing' || e.kind === 'readonly' ? 'GitHub finds no ' + repo + ' for this token. Check the name, and that the token lists the repository.'
          : 'GitHub could not be reached. Try again.');
      }
      if (r.private !== true) throw new Error(repo + ' is public. The city holds every project, note, link and folder path, so sync needs a private repository.');
      c.branch = r.default_branch || 'main';
      let hd;
      try { hd = await head(c, true); }
      catch (e) { throw new Error(e.kind === 'empty' || e.kind === 'missing' ? repo + ' is empty. On GitHub, add a README to it, then connect again.' : 'GitHub could not be reached. Try again.'); }
      try { await gh(c, 'POST', repoPath(c) + '/git/blobs', { content: '', encoding: 'utf-8' }); }
      catch (e) { throw new Error(e.kind === 'readonly' || e.kind === 'missing' ? 'The token can only read. Give it Contents: Read and write, then paste it again.' : 'GitHub could not be reached. Try again.'); }
      let copy;
      try { copy = await readCopy(c, hd, null); }
      catch (e) { throw new Error(e.kind === 'newer' ? 'The shared copy is from a newer city (' + e.wrote + '). Reload to update, then connect.' : e.kind === 'broken' ? 'The repository holds something other than a city.' : 'GitHub could not be reached. Try again.'); }
      if (copy.form) {
        const n = Object.keys(copy.form.projects).length;
        state = 'off'; render();
        const yes = await Confirm.ask({ title: 'Take the shared city?', confirm: 'Take the shared city',
          body: 'This city is replaced by the one in ' + repo + ', with ' + plural(n, 'project', 'projects') + '. A backup of this city downloads first.' });
        if (!yes) return;
        state = 'connecting'; render();
        persistSoon.flush();
        const backup = await buildBackup();
        downloadBlob(new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' }), 'nullovation-city-backup-before-sync-' + ymd() + '.json');
        const incoming = await fetchArt(c, copy, null);
        await ensureFps();
        setCfg(c); claim(true);
        await applyForm(copy.form, incoming);
        base = { repo, commit: copy.commit, treeSha: copy.treeSha, tree: copy.tree, form: copy.form, at: copy.at, wrote: copy.wrote };
        await saveBase();
        toast('Synced with ' + repo + '. This city took the shared copy; its backup from before is in your downloads.');
      } else {
        setCfg(c); claim(true);
        base = { repo, commit: copy.commit, treeSha: copy.treeSha, tree: copy.tree, form: null, at: 0 };
        await ensureFps();
        const local = sharedOf();
        await send(c, local, diffOf(base, local));
        toast('Synced. This city started the shared copy in ' + repo + '.');
      }
      problem = ''; netSince = 0; checkedRepo = true; lastChecked = Date.now();
      state = 'on'; tokenField = false; render();
    } catch (e) {
      setCfg(null); base = null; state = 'off';
      msg = e.kind ? 'GitHub could not be reached. Try again.' : e.message || 'Sync could not connect.';
      render();
    }
  }
  function useToken() {
    const t = (($('#syncNewToken') || {}).value || '').trim();
    if (!t) return;
    editCfg(c => { c.token = t; });
    problem = ''; tokenField = false; checkedRepo = false; lastEtag = '';
    render(); run();
  }
  function pause(on) {
    editCfg(c => { c.paused = on; });
    state = on ? 'paused' : 'on';
    render();
    if (!on) run();
  }
  async function disconnect() {
    setCfg(null);
    if (isWriter()) { try { localStorage.removeItem(WRITER_KEY); } catch (e) { /* ignore */ } }
    base = null; problem = ''; netSince = 0; state = 'off'; checkedRepo = false; lastEtag = ''; lastHead = ''; old.clear();
    await Store.dropSync('base');
    render();
    toast('Sync is off. This city stays as it is, and the repository keeps its copy.');
  }

  /* ---------- in Settings, Saving, and under the logo ---------- */
  let howOpen = false, tokenField = false, lastSig = '';
  const waiting = () => !!netSince && Date.now() - netSince > T.offline;
  function render() {
    const box = $('#syncBox'), alertEl = $('#syncAlert');
    const c = cfg(), repo = c ? c.repo : '';
    const shown = c && c.paused ? 'paused' : c && problem ? 'stopped' : c ? (state === 'standby' ? 'standby' : 'on') : state === 'connecting' ? 'connecting' : 'off';
    const b = t => h('b', { dir: 'ltr' }, t);
    const link = (label, fn) => h('button', { class: 'linkish', type: 'button', onclick: fn }, label);
    const sep = ' · ';
    const problemLine = () => problem === 'token' ? 'Sync stopped: GitHub refused the token. Paste a new one.'
      : problem === 'readonly' ? 'Sync stopped: the token can only read. Give it Contents: Read and write, then paste it again.'
      : problem === 'missing' ? 'Sync stopped: GitHub finds no ' + repo + ' for this token.'
      : problem === 'public' ? 'Sync stopped: ' + repo + ' is public now. Make it private again on GitHub, then reload.'
      : problem === 'newer' ? 'Sync stopped: the shared copy is from a newer city' + (newer ? ' (' + newer + ')' : '') + '. Reload to update.'
      : problem === 'empty' || problem === 'broken' ? 'Sync stopped: the shared copy in ' + repo + ' cannot be read.' : 'Sync stopped.';
    const tokenFix = problem === 'token' || problem === 'readonly';
    /* drawn again only when what it says changed, so the keyboard keeps its place in it */
    const sig = [shown, repo, problem, newer, msg, howOpen, deferred, waiting(), netKind, lastChecked ? relAgo(lastChecked) : ''].join('|');
    if (box && sig !== lastSig && !(box.contains(document.activeElement) && document.activeElement.tagName === 'INPUT' && shown !== 'connecting')) {
      lastSig = sig;
      const kids = [];
      const keepRepo = ($('#syncRepo') || {}).value, keepTok = ($('#syncToken') || {}).value;
      if (shown === 'off' || shown === 'connecting') {
        kids.push(h('p', { class: 'save-status' }, 'Keep this city the same on your PC and your phone, through a private GitHub repository.'));
        kids.push(h('label', { class: 'set-field sync-field' }, h('span', null, 'Repository'),
          h('input', { id: 'syncRepo', class: 'field', type: 'text', dir: 'ltr', value: keepRepo != null ? keepRepo : REPO_DEFAULT, autocomplete: 'off', spellcheck: 'false', placeholder: 'owner/repository' })));
        kids.push(h('label', { class: 'set-field sync-field' }, h('span', null, 'Token for this device'),
          h('input', { id: 'syncToken', class: 'field', type: 'password', dir: 'ltr', value: keepTok || '', autocomplete: 'off', spellcheck: 'false', placeholder: 'github_pat_...',
            onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); connect(); } } })));
        kids.push(shown === 'connecting' ? h('p', { class: 'save-status' }, 'Connecting to GitHub...')
          : h('button', { id: 'btnSyncConnect', class: 'btn btn-small', type: 'button', onclick: connect }, 'Connect'));
        if (msg) kids.push(h('p', { id: 'syncMsg', class: 'save-status bad', role: 'alert' }, msg));
        kids.push(h('p', { class: 'save-status' }, 'The token stays in this browser: never in the data file, a backup or an export. ',
          h('button', { id: 'btnSyncHow', class: 'linkish', type: 'button', 'aria-expanded': String(howOpen), onclick: () => { howOpen = !howOpen; render(); } }, 'How to set it up')));
        if (howOpen) kids.push(h('ol', { class: 'sync-steps' },
          h('li', null, 'On github.com, make a new repository: Private, with Add a README ticked.'),
          h('li', null, 'Make a token for this device: Settings, Developer settings, Personal access tokens, Fine-grained tokens. Only select repositories: this one. Permissions: Contents, Read and write.'),
          h('li', null, 'Paste both here and connect, the PC\'s city first: it starts the shared copy. Every other city saves a backup of itself, then takes it.')));
      } else if (shown === 'on') {
        kids.push(h('p', { class: 'save-status file-on' }, 'Synced with ', b(repo), '. ', waiting() ? (netKind === 'network' ? 'Sync is waiting for the network.' : 'GitHub cannot be reached right now; it keeps trying.')
          : lastChecked ? 'Checked ' + relAgo(lastChecked) + '.' : 'Checking...'));
        if (deferred) kids.push(h('p', { class: 'save-status' }, 'A change from another city waits until you leave the field you are typing in.'));
        kids.push(h('p', { class: 'save-status' }, link('Pause sync', () => pause(true)), sep, link('Disconnect', disconnect)));
      } else if (shown === 'standby') {
        kids.push(h('p', { class: 'save-status' }, 'Another tab of this city syncs with ', b(repo), '. This tab takes over as soon as you use it.'));
        kids.push(h('p', { class: 'save-status' }, link('Pause sync', () => pause(true)), sep, link('Disconnect', disconnect)));
      } else if (shown === 'paused') {
        kids.push(h('p', { class: 'save-status' }, 'Sync with ', b(repo), ' is paused: this city neither sends nor receives.'));
        kids.push(h('p', { class: 'save-status' }, link('Resume sync', () => pause(false)), sep, link('Disconnect', disconnect)));
      } else {
        kids.push(h('p', { class: 'save-status bad' }, problemLine()));
        if (tokenFix) {
          kids.push(h('label', { class: 'set-field sync-field' }, h('span', null, 'New token for this device'),
            h('input', { id: 'syncNewToken', class: 'field', type: 'password', dir: 'ltr', autocomplete: 'off', spellcheck: 'false', placeholder: 'github_pat_...',
              onkeydown: e => { if (e.key === 'Enter') { e.preventDefault(); useToken(); } } })));
          kids.push(h('button', { id: 'btnSyncToken', class: 'btn btn-small', type: 'button', onclick: useToken }, 'Use this token'));
        }
        if (problem === 'newer' || problem === 'public') kids.push(h('button', { class: 'btn btn-small', type: 'button', onclick: () => location.reload() }, 'Reload'));
        kids.push(h('p', { class: 'save-status' }, link('Disconnect', disconnect)));
      }
      box.replaceChildren(...kids);
    }
    if (alertEl) {
      const kids = [];
      if (shown === 'stopped') {
        kids.push(h('span', null, problemLine(), ' '));
        if (tokenFix) kids.push(link('Paste it', () => { Settings.open('saving'); const f = $('#syncNewToken'); if (f) f.focus(); }));
        else if (problem === 'newer' || problem === 'public') kids.push(link('Reload', () => location.reload()));
        else kids.push(link('Settings', () => Settings.open('saving')));
      } else if (shown === 'paused') kids.push(h('span', null, 'Sync is paused. '), link('Resume', () => pause(false)));
      else if (shown === 'on' && waiting()) kids.push(h('span', null, netKind === 'network' ? 'Sync is waiting for the network.' : 'Sync cannot reach GitHub right now. It keeps trying.'));
      alertEl.replaceChildren(...kids);
      alertEl.hidden = !kids.length;
    }
  }

  /* ---------- another tab of this city follows ----------
     Every tab reads the city again when another tab saves it, and loads a picture another tab put, so a tab left open
     never sends an older city as if it were new. */
  let followDeferred = false;
  function follow() {
    if (busyHere()) { followDeferred = true; return; }
    followDeferred = false;
    const saved = Store.load();
    if (!saved || !Array.isArray(saved.projects)) return;
    applyDb(saved, { persist: false });
  }
  const followSoon = debounce(follow, 250);
  async function artFollow(raw) {
    let v; try { v = JSON.parse(raw); } catch (e) { return; }
    if (!v || typeof v.id !== 'string') return;
    fps.delete(v.id);
    if (v.id.startsWith('leader:')) {
      const lid = v.id.slice(7);
      if (v.gone) await Leaders.forget(lid, false);
      else { const url = await Store.getArt(v.id); if (url) await Leaders.keep(lid, url, false); }
    } else if (v.gone) { Art.drop(v.id); MapView.invalidate(); }
    else await Art.load(v.id);
  }
  /* Store tells of every picture put or taken out: its fingerprint is worked out again, and the other tabs load it. */
  function artChanged(id, gone = false) {
    fps.delete(id); gen++;
    try { localStorage.setItem(ART_KEY, JSON.stringify({ id, gone, at: Date.now(), n: Math.random() })); localStorage.removeItem(ART_KEY); } catch (e) { /* this tab only */ }   // heard by the other tabs, kept by none
  }

  /* persistNow tells of every save: a change of this city's, sent 3 seconds after the last one. */
  function changed() {
    gen++;
    if (applying || !cfg()) return;
    editCfg(c => { c.at = Date.now(); });
    soon();
  }

  function init() {
    window.addEventListener('storage', e => {
      if (e.storageArea && e.storageArea !== localStorage) return;
      if (e.key === CITY_KEY && e.newValue) followSoon();
      else if (e.key === ART_KEY && e.newValue) artFollow(e.newValue);
      else if (e.key === KEY) { if (!cfg()) { base = null; state = 'off'; problem = ''; } render(); }
      else if (e.key === WRITER_KEY && state === 'on' && !isWriter()) { base = null; setState('standby'); }
    });
    const using = () => { if (cfg() && !isWriter() && claim(true)) { base = null; run(); } };
    window.addEventListener('focus', using);
    window.addEventListener('pointerdown', using, true);
    window.addEventListener('keydown', using, true);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') { using(); run(); }
      else if (cfg() && isWriter()) run();                 // going out of view sends what is waiting at once
    });
    document.addEventListener('focusout', () => setTimeout(() => {
      if (deferred && !busyHere()) { deferred = false; run(); }
      if (followDeferred && !busyHere()) follow();
    }, 60));
    window.addEventListener('online', () => run());
    window.addEventListener('pagehide', () => { if (isWriter()) { try { localStorage.removeItem(WRITER_KEY); } catch (e) { /* ignore */ } } });
    setInterval(() => { const box = $('#syncBox'); if (box && box.offsetParent) render(); else if (waiting()) render(); }, 30000);
    render();
    loop();
    if (cfg()) setTimeout(run, 400);
  }

  return { init, render, changed, artChanged, connected: () => !!cfg(), state: () => state,
    _test: {
      fast: () => { T = { check: 700, send: 250, stale: 4000, offline: 2500, retry: [150, 300, 600] }; },
      api: url => { testApi = url; editCfg(c => { c.api = url; }); },
      hold: on => { hold = !!on; if (!hold) run(); },
      run, merge, canon, sharedOf, ensureFps,
      info: () => ({ state, problem, newer, deferred, base: base && base.commit, writer: isWriter(), lastChecked, netSince, sentAt, sends, refusals, receives }),
    } };
})();
