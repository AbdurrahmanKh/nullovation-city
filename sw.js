/* Nullovation City's service worker, version 0.1.75. It keeps a copy of the city so the installed app opens
   offline. Online, the newest version always loads: the network is tried first, and the copy is used only when the
   network fails. build.py writes it to sw.js beside the page, since a worker only looks after the pages in its own
   folder and GitHub Pages cannot widen that; each version changes this file, so the browser takes the new worker.
   It handles the page and the app's own files and nothing else: every other request passes by untouched. */
'use strict';
const CACHE = 'nullovation-city-app';     // the wizard's app shares this address, and keeps its own cache
const PAGE = new URL('./', self.location).href;
const FILES = ['src/app/manifest.webmanifest', 'src/app/icon-192.png', 'src/app/icon-512.png',
  'src/app/icon-maskable-512.png', 'src/app/icon-180.png'].map(f => new URL(f, self.location).href);

self.addEventListener('install', ev => {
  ev.waitUntil(caches.open(CACHE).then(c => c.add(new Request(PAGE, { cache: 'reload' }))
    .then(() => Promise.all(FILES.map(f => c.add(f).catch(() => {})))))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', ev => ev.waitUntil(self.clients.claim()));

self.addEventListener('fetch', ev => {
  const req = ev.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url), at = url.origin + url.pathname;
  const page = req.mode === 'navigate' && (at === PAGE || at === PAGE + 'index.html');
  if (!page && !FILES.includes(at)) return;
  const key = page ? PAGE : at;
  // the page asks the server every time (a quick "not changed" when it has not), so a new version shows at once
  ev.respondWith(fetch(page ? new Request(req.url, { cache: 'no-cache' }) : req).then(res => {
    if (!res.ok) return caches.open(CACHE).then(c => c.match(key)).then(hit => hit || res);
    const copy = res.clone();
    caches.open(CACHE).then(c => c.put(key, copy));
    return res;
  }, () => caches.open(CACHE).then(c => c.match(key)).then(hit => hit || Response.error())));
});
