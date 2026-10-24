"""The app (0.1.67): the hosted city installs like the Decision Wizard and opens offline. The manifest, the icons and
the service worker's source in src/app/, sw.js built beside the page; a local copy of the page installing nothing;
and the city served over http from a copy of its files: the manifest named, the worker keeping the page, the newest
version loading online, the copy opening offline with nothing else kept, and Install in Settings, Saving, with
Chrome itself offering the install in a real profile. Nothing is ever installed."""
import functools, http.server, json, shutil, tempfile, threading, pathlib
from PIL import Image
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY, VERSION

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

APP = ROOT / 'src' / 'app'

# ---------- the files ----------
man = json.loads((APP / 'manifest.webmanifest').read_text(encoding='utf-8'))
ok('the manifest names the city, standalone, its start and scope the page\'s own folder (two up from src/app/)',
   man['name'] == 'Nullovation City' and man['short_name'] == 'City' and man['display'] == 'standalone'
   and man['start_url'] == '../../' and man['scope'] == '../../', man)
icons = {(i['src'], i['sizes'], i.get('purpose', 'any')) for i in man['icons']}
ok('it lists a 192 and a 512 icon, and a 512 maskable one', icons == {('icon-192.png', '192x192', 'any'), ('icon-512.png', '512x512', 'any'),
   ('icon-maskable-512.png', '512x512', 'maskable')}, icons)
sizes = {i['src']: Image.open(APP / i['src']) for i in man['icons']}
ok('each icon is a PNG of the size it says', all(im.format == 'PNG' and im.size == tuple(int(n) for n in i['sizes'].split('x'))
   for i in man['icons'] for im in [sizes[i['src']]]))
plain = Image.open(APP / 'icon-512.png').convert('RGBA')
mask = Image.open(APP / 'icon-maskable-512.png').convert('RGBA')
touch = Image.open(APP / 'icon-180.png')
ok('the plain icon is a rounded square: its corners see-through, its middle solid', plain.getpixel((0, 0))[3] == 0 and plain.getpixel((256, 256))[3] == 255)
ok('the maskable icon fills its square, for Android to cut its own shape', mask.getchannel('A').getextrema() == (255, 255))
ok('an iPhone\'s home screen gets a solid 180 px icon, which it rounds itself', touch.size == (180, 180) and touch.mode == 'RGB')
ok('the icon is the dome on night violet, picked on 24 October 2026', mask.getpixel((4, 4))[:3] == (58, 45, 96))
ok("the window's title bar is the side bar's dark, and it opens on the page's own background", man['theme_color'] == '#1A1628' and man['background_color'] == '#120F1F')
src_sw = (APP / 'sw.js').read_text(encoding='utf-8')
built = (ROOT / 'sw.js').read_text(encoding='utf-8') if (ROOT / 'sw.js').exists() else ''
ok(f'sw.js sits beside the page, built from src/app/sw.js with this version ({VERSION})',
   built == src_sw.replace('{{VERSION}}', VERSION) and f'version {VERSION}.' in built)
page = (ROOT / 'index.html').read_text(encoding='utf-8')
ok('the page has the title bar color, and names no manifest of its own: the hosted page adds it',
   '<meta name="theme-color" content="#1A1628">' in page and 'rel="manifest"' not in page.split('<script>')[0])


class Quiet(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.webmanifest': 'application/manifest+json'}
    def log_message(self, *a): pass


def serve(folder, port=0):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
    b = p.chromium.launch(channel='chrome')

    # ---------- a local copy: nothing to install ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(1500)
    ev = pg.evaluate
    ok('opened from a file, the page adds no manifest and registers no worker (a file cannot have one)', ev("""async () => !document.querySelector('link[rel=manifest]')
        && !AppInstall.hosted() && (!navigator.serviceWorker || (await navigator.serviceWorker.getRegistrations().catch(() => [])).length === 0)"""))
    ev("() => Settings.open()"); ev("() => Settings.showTab('saving')"); pg.wait_for_timeout(300)
    first = ev("() => document.querySelector('[data-tab=saving].set-page .set-h').textContent")
    local = ev("() => document.querySelector('#appBox').textContent")
    link = ev("() => { const a = document.querySelector('#appBox a'); return a && [a.href, a.target, a.rel]; }")
    ok(f'Settings, Saving starts with The app ({first})', first == 'The app')
    ok('a local copy says it cannot be installed, and links the hosted city', 'local copy of the page, so it cannot be installed' in local
       and link == ['https://abdurrahmankh.github.io/nullovation-city/', '_blank', 'noopener'], [local, link])
    pg.screenshot(path=str(SHOTS / '420-app-local.png'))
    ctx.close()

    # ---------- served over http, as GitHub Pages serves it ----------
    site = pathlib.Path(tmp) / 'site'
    (site / 'src').mkdir(parents=True)
    shutil.copy(ROOT / 'index.html', site / 'index.html')
    shutil.copy(ROOT / 'sw.js', site / 'sw.js')
    shutil.copytree(APP, site / 'src' / 'app')
    (site / 'notes.txt').write_text('not part of the app\n', encoding='utf-8')
    srv = serve(site)
    port = srv.server_address[1]
    URL = f'http://127.0.0.1:{port}/'
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(URL); pg.wait_for_timeout(1500)
    ev = pg.evaluate
    links = ev("() => [...document.head.querySelectorAll('link[rel=manifest], link[rel=apple-touch-icon]')].map(l => l.getAttribute('href'))")
    ok(f'the hosted page names its manifest and the iPhone icon ({links})', links == ['src/app/manifest.webmanifest', 'src/app/icon-180.png'])
    got = ev("""async () => { const m = await (await fetch('src/app/manifest.webmanifest')).json();
        const base = new URL('src/app/manifest.webmanifest', location.href);
        const icons = await Promise.all(m.icons.map(async i => (await fetch(new URL(i.src, base))).ok));
        return { start: new URL(m.start_url, base).href, scope: new URL(m.scope, base).href, icons }; }""")
    ok('the manifest\'s start and scope are the page\'s own address, and every icon it lists loads',
       got['start'] == URL and got['scope'] == URL and all(got['icons']), got)
    reg = ev("""async () => { const r = await navigator.serviceWorker.ready; return { scope: r.scope, script: r.active && r.active.scriptURL }; }""")
    ok(f'the service worker registers beside the page and looks after its folder ({reg})', reg == {'scope': URL, 'script': URL + 'sw.js'})
    pg.reload(); pg.wait_for_timeout(1500)
    ok('after a reload it controls the page', ev("() => !!navigator.serviceWorker.controller"))
    kept = ev("""async () => { const c = await caches.open('nullovation-city-app'); return (await c.keys()).map(r => new URL(r.url).pathname).sort(); }""")
    ok(f'it keeps the page and the app\'s files in a cache of its own ({kept})', kept == ['/', '/src/app/icon-180.png', '/src/app/icon-192.png',
       '/src/app/icon-512.png', '/src/app/icon-maskable-512.png', '/src/app/manifest.webmanifest'])
    cdp = ctx.new_cdp_session(pg)
    parsed = cdp.send('Page.getAppManifest')
    # the test browser's own contexts are private, which alone stops an install; that is the browser, not the city
    stops = [s['errorId'] for s in cdp.send('Page.getInstallabilityErrors')['installabilityErrors'] if s['errorId'] != 'in-incognito']
    ok(f'Chrome reads the manifest with no error, and finds nothing stopping an install ({parsed.get("errors") or stops or "none"})',
       not parsed.get('errors') and not stops and parsed['url'] == URL + 'src/app/manifest.webmanifest')
    ok('the city runs as usual: its projects are there', ev("() => DB.projects.map(p => p.name).sort().join(',')") == 'Garden planner,Nullovation City')

    # a new version on the server shows at the next load, and the copy follows it
    html = (site / 'index.html').read_text(encoding='utf-8')
    (site / 'index.html').write_text(html.replace('<title>Nullovation City</title>', '<title>Nullovation City</title><meta name="nc-test" content="newer">'), encoding='utf-8')
    pg.reload(); pg.wait_for_timeout(1500)
    ok('online, the newest version loads: the network comes first', ev("() => !!document.querySelector('meta[name=nc-test]')"))
    ok('a file the app does not own passes by: nothing else is kept', ev("""async () => { await fetch('notes.txt');
        const c = await caches.open('nullovation-city-app'); return !(await c.match(new URL('notes.txt', location.href).href)); }"""))

    # ---------- Install, in Settings, Saving ----------
    ev("() => Settings.open()"); ev("() => Settings.showTab('saving')"); pg.wait_for_timeout(300)
    menu = ev("() => document.querySelector('#appBox').textContent")
    ok('with no offer from the browser, it points to the browser\'s menu', 'Your browser\'s menu may offer Install app' in menu and not ev("() => !!document.querySelector('#btnInstall')"), menu)
    offer = """(outcome) => { const e = new Event('beforeinstallprompt', { cancelable: true });
        e.prompt = () => { window.ncPrompted = (window.ncPrompted || 0) + 1; return Promise.resolve(); };
        e.userChoice = Promise.resolve({ outcome }); window.dispatchEvent(e); return e.defaultPrevented; }"""
    ok('the browser\'s install offer is kept for the button, not shown by itself', ev(offer, 'dismissed'))
    btn = ev("() => { const b = document.querySelector('#btnInstall'); return b && [b.textContent, document.querySelector('#appBox p').textContent]; }")
    ok('Install the app shows, with what the app does and that it opens this same city', btn and btn[0] == 'Install the app'
       and 'opens offline' in btn[1] and 'it opens this same city' in btn[1], btn)
    pg.screenshot(path=str(SHOTS / '421-app-install.png'))
    pg.click('#btnInstall'); pg.wait_for_timeout(300)
    ok('a click asks the browser, and a no keeps the button for later', ev("() => window.ncPrompted") == 1 and ev("() => !!document.querySelector('#btnInstall')"))
    ev(offer, 'accepted'); pg.click('#btnInstall'); pg.wait_for_timeout(300)
    ok('a yes takes the button away', ev("() => window.ncPrompted") == 2 and not ev("() => !!document.querySelector('#btnInstall')"))
    ev("() => window.dispatchEvent(new Event('appinstalled'))"); pg.wait_for_timeout(200)
    ok('once installed, a toast says so', ev("() => document.querySelector('#toast').textContent") == 'Installed. The city opens from your apps now, offline too.')
    ev("""() => { const real = window.matchMedia.bind(window); window.matchMedia = q => q === '(display-mode: standalone)'
        ? { matches: true, addEventListener() {} } : real(q); AppInstall.render(); }""")
    inside = ev("() => document.querySelector('#appBox').textContent")
    ok('inside the app, it says so, with no button', inside.startswith('You\'re in the installed app.') and not ev("() => !!document.querySelector('#btnInstall')"), inside)

    # a real profile, not a private one: Chrome itself offers the install, so the button shows with nothing faked
    real = p.chromium.launch_persistent_context(str(pathlib.Path(tmp) / 'profile'), channel='chrome', headless=True)
    rp = real.new_page()
    rp.on('pageerror', lambda e: errors.append(str(e))); rp.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    rp.goto(URL)
    rp.wait_for_function("() => !!document.querySelector('#btnInstall')", timeout=15000)
    ok('in a real profile Chrome offers the install, and Install the app shows', rp.evaluate("() => document.querySelector('#btnInstall').textContent") == 'Install the app')
    real.close()

    # ---------- offline ----------
    srv.shutdown(); srv.server_close()
    pg.reload(); pg.wait_for_timeout(2000)
    ok('with the server gone, the page opens from the copy, the newest one', ev("() => document.title") == 'Nullovation City'
       and ev("() => !!document.querySelector('meta[name=nc-test]')") and ev("() => DB.projects.length") == 2)
    ok('offline, a file the app does not own is not there', ev("() => fetch('notes.txt').then(() => false, () => true)"))
    ctx.close()
    b.close()
# the server gone, Chrome says that it could not reach the worker's script and the file the app does not own
errors = [e for e in errors if 'ERR_CONNECTION_REFUSED' not in e and 'Failed to fetch' not in e]
print(errors or 'no console errors')
