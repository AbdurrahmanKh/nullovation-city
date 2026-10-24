/*
  The app (0.1.67): the hosted city installs like the Decision Wizard, in its own window with its own icon, and opens
  offline. A service worker (sw.js beside the page, built from src/app/sw.js) keeps a copy of the page, and online the
  newest version always loads. The manifest and the icons live in src/app/. A local copy of the page, opened from a
  file, skips all of it, so the tests and a chat's copy never install anything. Installed from a browser, the app
  shares that browser's storage for the address, so it opens the same city; Settings, Saving, has Install.
*/
const AppInstall = (() => {
  const HOSTED = 'https://abdurrahmankh.github.io/nullovation-city/';
  let offer = null;           // the browser's install offer, kept until Install is pressed
  const hosted = () => location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
  function standalone() {
    try { return !!((window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true); } catch (e) { return false; }
  }

  /* Only the hosted page names its manifest: a page opened from a file cannot fetch it, and would say so. */
  if (hosted()) {
    document.head.append(h('link', { rel: 'manifest', href: 'src/app/manifest.webmanifest' }),
      h('link', { rel: 'apple-touch-icon', href: 'src/app/icon-180.png' }));
    window.addEventListener('beforeinstallprompt', e => { e.preventDefault(); offer = e; render(); });
    window.addEventListener('appinstalled', () => { offer = null; render(); toast('Installed. The city opens from your apps now, offline too.'); });
    try { if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').then(null, () => {}); } catch (e) {}
  }

  function install() {
    const e = offer;
    if (!e || typeof e.prompt !== 'function') return;
    offer = null;
    render();
    const back = () => { offer = e; render(); };
    try {
      Promise.resolve(e.prompt()).then(() => e.userChoice).then(c => { if (!(c && c.outcome === 'accepted')) back(); }, back);
    } catch (err) { back(); }
  }

  function render() {
    const box = $('#appBox');
    if (!box) return;
    const kids = [];
    if (standalone()) {
      kids.push(h('p', { class: 'save-status file-on' }, 'You\'re in the installed app.'));
      kids.push(h('p', { class: 'save-status' }, 'It opens offline, and loads the newest version whenever you\'re online.'));
    } else if (!hosted()) {
      kids.push(h('p', { class: 'save-status' }, 'This is a local copy of the page, so it cannot be installed. The hosted city can: ',
        h('a', { class: 'linkish', href: HOSTED, target: '_blank', rel: 'noopener' }, 'abdurrahmankh.github.io/nullovation-city'), '.'));
    } else if (offer) {
      kids.push(h('button', { id: 'btnInstall', class: 'btn btn-small', type: 'button', onclick: install }, 'Install the app'));
      kids.push(h('p', { class: 'save-status' }, 'Its own window and icon. It opens offline, and loads the newest version whenever you\'re online. Installed from this browser, it opens this same city.'));
    } else {
      kids.push(h('p', { class: 'save-status' }, 'Your browser\'s menu may offer Install app, or Add to Home screen on a phone; once it is installed, the menu offers to open it. The app opens offline, and loads the newest version whenever you\'re online.'));
    }
    box.replaceChildren(...kids);
  }

  function init() {
    render();
    try { window.matchMedia('(display-mode: standalone)').addEventListener('change', render); } catch (e) {}
  }

  return { init, render, hosted, standalone };
})();
