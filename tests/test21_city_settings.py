"""The settings the panel brought: who is out and how many, street props (kinds, how many, Deal again), Auto's hours,
motion, the postcard, rest days and away until, daily backups, storage use, testing folder links; and which settings
travel with the city in the data file and backups, and which stay on this computer."""
import datetime, io, json, pathlib
from PIL import Image
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, DATA, TEST_CITY, fixture, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
TODAY = datetime.date.today().isoformat()

# a backups folder held in memory: 15 daily copies from September and two exported backups already in it
FAKE_DIR = """
window.__files = new Map(); window.__dirPerm = 'granted'; window.__failWrite = null; window.__dirWrites = 0;
for (let d = 1; d <= 15; d++) window.__files.set('nullovation-city-daily-2026-09-' + String(d).padStart(2, '0') + '.json', '{}');
window.__files.set('nullovation-city-backup-2026-09-01.json', '{}'); window.__files.set('nullovation-city-backup-2026-10-01.json', '{}');
const fileOf = name => ({ kind: 'file', name, createWritable: async () => {
  if (window.__failWrite) { const e = new Error('refused'); e.name = window.__failWrite; throw e; }
  let buf = ''; return { write: async d => { buf += d; }, close: async () => { window.__files.set(name, buf); window.__dirWrites++; } }; } });
window.__dir = { kind: 'directory', name: 'City backups',
  queryPermission: async () => window.__dirPerm, requestPermission: async () => { window.__dirPerm = 'granted'; return 'granted'; },
  getFileHandle: async (name, o) => { if (!window.__files.has(name) && !(o && o.create)) { const e = new Error('none'); e.name = 'NotFoundError'; throw e; } return fileOf(name); },
  entries: async function* () { for (const n of [...window.__files.keys()]) yield [n, fileOf(n)]; },
  removeEntry: async name => { window.__files.delete(name); } };
window.showDirectoryPicker = async () => window.__dir;
window.__opened = [];
HTMLAnchorElement.prototype.click = function () { if (/^nullovation-folder:/.test(this.href)) window.__opened.push(this.href); else HTMLElement.prototype.click.call(this); };
"""
KEY = "q => [q.kind, q.u, q.v, q.side, q.a.toFixed(5)].join()"
RULES = """() => { const plan = MapView.props(), per = {}, built = new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v));
  for (const q of plan) per[q.u + ',' + q.v + ',' + q.side] = (per[q.u + ',' + q.v + ',' + q.side] || 0) + 1;
  return { n: plan.length, two: Math.max(0, ...Object.values(per)) <= 2,
    vending: plan.filter(q => q.kind === 'vending').every(q => q.a >= 1.5 && q.a <= 2.5),
    billboard: plan.filter(q => q.kind === 'billboard').every(q => Math.abs(q.a - 0.62) < 1e-9),
    bins: plan.filter(q => q.kind === 'bin').every(q => (q.side === 'se' || q.side === 'sw') && built.has(q.u + ',' + q.v)),
    apart: plan.every(x => plan.every(y => x === y || x.u !== y.u || x.v !== y.v || x.side !== y.side || Math.abs(x.a - y.a) >= 0.8)) }; }"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t21')) { sessionStorage.setItem('nc-t21', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); } } catch (e) {}")
    ctx.add_init_script(FAKE_DIR)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof PROPS !== 'undefined' && PROPS.every(p => Art.get('prop:' + p.id + ':front'))", timeout=20000)
    pg.wait_for_timeout(800)
    js = pg.evaluate
    stats = lambda: js("() => Traffic.stats()")
    def slide(sel, v):
        js(f"() => {{ const r = document.querySelector('{sel}'); r.value = {v}; r.dispatchEvent(new Event('input')); }}"); pg.wait_for_timeout(120)

    # ---------- Life: who is out, and how many ----------
    open_settings(pg, 'life')
    s0 = stats()
    ok(f'today\'s counts by default on 5 by 5: 12 cars, 2 buses, 2 drones, 20 walkers and 2 cyclists ({s0})', s0['cars'] == 12 and s0['buses'] == 2 and s0['drones'] == 2 and s0['people'] - s0['extras'] == 20 and s0['bikes'] == 2)
    pg.uncheck('#optCars'); pg.wait_for_timeout(150); s = stats()
    ok(f'cars kept in: none on the streets, the buses and drones still out ({s})', s['cars'] == 0 and s['buses'] == 2 and s['drones'] == 2)
    pg.uncheck('#optBuses'); pg.uncheck('#optDrones'); pg.wait_for_timeout(150); s = stats()
    ok(f'buses and drones too ({s})', s['buses'] == 0 and s['drones'] == 0)
    pg.uncheck('#optCyclists'); pg.wait_for_timeout(150); s = stats()
    ok(f'cyclists kept in, the walkers still out ({s})', s['bikes'] == 0 and s['people'] > 0)
    pg.uncheck('#optWalkers'); pg.wait_for_timeout(150); s = stats()
    ok(f'walkers kept in: no one on foot, the crowds round busy buildings included ({s})', s['people'] == 0 and s['extras'] == 0)
    for sel in ('#optCars', '#optBuses', '#optDrones', '#optCyclists', '#optWalkers'): pg.check(sel)
    pg.wait_for_timeout(150); s = stats()
    ok('all back out', s['cars'] == 12 and s['buses'] == 2 and s['drones'] == 2 and s['bikes'] == 2 and s['people'] - s['extras'] == 20)
    rng = js("() => { const r = document.querySelector('#optStreet'); return [r.min, r.max, r.step, r.value]; }")
    ok(f'the sliders run from a quarter to twice today\'s counts, in quarter steps ({rng})', rng == ['0.25', '2', '0.25', '1'])
    slide('#optStreet', 2); s = stats()
    ok(f'street traffic at twice: 24 cars, 4 buses, 4 drones ({s}, {pg.text_content("#optStreetOut")})', s['cars'] == 24 and s['buses'] == 4 and s['drones'] == 4 and pg.text_content('#optStreetOut') == '2x')
    slide('#optStreet', 0.25); s = stats()
    ok(f'at a quarter: 2 cars, a bus and a drone ({s})', s['cars'] == 2 and s['buses'] == 1 and s['drones'] == 1)
    slide('#optStreet', 1)
    slide('#optWalk', 2); s = stats()
    ok(f'walkers at twice: 40 walkers and 4 cyclists, the street traffic as it was ({s})', s['people'] - s['extras'] == 40 and s['bikes'] == 4 and s['cars'] == 12)
    slide('#optWalk', 0.25); s = stats()
    ok(f'at a quarter: 5 walkers and a cyclist ({s})', s['people'] - s['extras'] == 5 and s['bikes'] == 1)
    slide('#optWalk', 2)
    js("() => { MapView.resizeWorld(1); MapView.resizeWorld(1); MapView.resizeWorld(1); Traffic.reset(); }"); s = stats()
    ok(f'on 11 by 11 at twice, the walkers stop at the city\'s 150, and the crowds have no room left ({s})', s['people'] == 150 and s['extras'] == 0)
    js("() => { MapView.resizeWorld(-1); MapView.resizeWorld(-1); MapView.resizeWorld(-1); }")
    slide('#optWalk', 1)
    pg.select_option('#optCrowds', 'large'); pg.wait_for_timeout(150)
    ok('the crowd size is the city\'s now', js("() => DB.city.crowd") == 'large' and stats()['extras'] == 40)

    # ---------- City: street props ----------
    open_settings(pg, 'city')
    plan1 = js(f"() => MapView.props().map({KEY})")
    pg.uncheck('#optBusstop'); pg.wait_for_timeout(150)
    nob = js(f"() => MapView.props().map({KEY})")
    ok(f'bus stops turned off: only the bus stops go, every other prop stays where it was ({len(plan1)} to {len(nob)})',
       sorted(nob) == sorted(k for k in plan1 if not k.startswith('busstop')) and len(nob) < len(plan1))
    ok('so the buses have no stop to pause at', js("() => MapView.props().every(q => q.kind !== 'busstop')"))
    pg.check('#optBusstop')
    slide('#optAmount', 0.25)
    few = js(f"() => MapView.props().map({KEY})"); rules_few = js(RULES)
    slide('#optAmount', 2)
    many = js(f"() => MapView.props().map({KEY})"); rules = js(RULES)
    ok(f'a quarter as many: fewer props, every one where it stood ({len(few)} of {len(plan1)})', set(few) < set(plan1) and len(few) < len(plan1) * 0.5)
    ok(f'twice as many: more props, the ones there before still in place ({len(many)})', len(many) > len(plan1) * 1.4 and len(set(plan1) - set(many)) <= len(plan1) * 0.15)
    ok(f'at any amount the rules hold: at most two to a side, kept apart, each kind in its place ({rules})', all(rules[k] for k in ('two', 'vending', 'billboard', 'bins', 'apart')) and all(rules_few[k] for k in ('two', 'apart')))
    ok('and the slider shows it', pg.text_content('#optAmountOut') == '2x' and js("() => document.querySelector('[data-set=\"amount\"]').classList.contains('changed')"))
    slide('#optAmount', 1)
    ok('back at today\'s amount, today\'s plan', js(f"() => MapView.props().map({KEY})") == plan1)
    pg.click('#btnDeal'); pg.wait_for_timeout(150)
    dealt = js(f"() => MapView.props().map({KEY})"); rules = js(RULES)
    ok(f'Deal again lays them out anew ({len(set(dealt) & set(plan1))} of {len(dealt)} as before)', js("() => DB.city.deal") == 1 and len(set(dealt) & set(plan1)) < len(dealt) * 0.5)
    ok(f'by the same rules ({rules})', all(rules[k] for k in ('two', 'vending', 'billboard', 'bins', 'apart')))
    pg.uncheck('#optProps'); pg.wait_for_timeout(300)
    ok('street props off: none on the map', js("() => MapView.props().length") == 0 and js("() => MapView.propsDrawn()") == 0 and pg.is_disabled('#optBin') and pg.is_disabled('#btnDeal'))
    pg.check('#optProps'); pg.wait_for_timeout(150)
    pg.reload(); pg.wait_for_function("() => typeof PROPS !== 'undefined'", timeout=20000); pg.wait_for_timeout(400)
    ok('the new layout stays until dealt again, after a reload too', js("() => DB.city.deal") == 1 and js(f"() => MapView.props().map({KEY})") == dealt)

    # ---------- Look: Auto's hours, motion, the postcard ----------
    at = lambda h, m: js(f"() => Light.fromClock(new Date(2026, 9, 8, {h}, {m}))")
    ok(f'Auto by default: day at noon and from 06:30, dusk halfway at 18:15, night from 19:00, dawn halfway at 05:45 ({[at(12, 0), at(6, 30), at(18, 15), at(19, 0), at(5, 45), at(2, 0)]})',
       [at(12, 0), at(6, 30), at(18, 15), at(19, 0), at(5, 45), at(2, 0)] == [0, 0, 0.5, 1, 0.5, 1])
    open_settings(pg, 'look')
    pg.fill('#optNight', '21:00'); pg.fill('#optDay', '07:00'); pg.wait_for_timeout(150)
    ok('the hours you set are the city\'s', js("() => [DB.city.night, DB.city.day]") == ['21:00', '07:00'] and js("() => document.querySelector('[data-set=\"hours\"]').classList.contains('changed')"))
    ok(f'night from 21:00, dusk blending from 19:30, day from 07:00, dawn from 05:30 ({[at(19, 0), at(20, 15), at(21, 0), at(6, 15), at(7, 0)]})',
       [at(19, 0), at(20, 15), at(21, 0), at(6, 15), at(7, 0)] == [0, 0.5, 1, 0.5, 0])
    # Still: nothing moves
    js("() => { Traffic.setOn(true); MapView.syncBar(); }")
    pg.click('#optMotion [data-value="still"]'); pg.wait_for_timeout(300)
    idx = js("() => { const a = Art.get('g:city-hall'); return [0, 777, 1555, 4321].map(t => Art.indexAt(a, t)); }")
    ok(f'Still: every building on its first frame ({idx}), and no traffic, whatever the button says', idx == [0, 0, 0, 0] and js("() => !Traffic.active() && Traffic.isOn()"))
    n0 = js("() => MapView._paints()"); pg.wait_for_timeout(1200); n1 = js("() => MapView._paints()")
    ok(f'and the map rests: {n1 - n0} redraws in 1.2 s', n1 - n0 <= 2)
    ok('the note says what Still does', 'Nothing moves' in pg.text_content('#motionNote'))
    def paints_while_panning():
        js("() => MapView.setCam({ x: 0, y: 260, z: 2 })"); pg.wait_for_timeout(200)
        pg.focus('#map'); a = js("() => MapView._paints()")
        pg.keyboard.down('ArrowRight'); pg.wait_for_timeout(1000); pg.keyboard.up('ArrowRight')
        return js("() => MapView._paints()") - a
    pg.click('#optMotion [data-value="full"]'); full = paints_while_panning()
    pg.click('#optMotion [data-value="saver"]'); saver = paints_while_panning()
    if full < 45: print(f'NOTE this browser drew only {full} frames a second while panning at Full')
    ok(f'Saver draws at most 30 frames a second while panning ({saver} against {full} at Full)', saver <= 33 and (saver < full or full <= 33))
    pg.click('#optMotion [data-value="full"]')
    # the postcard: caption on or off, as on screen or doubled
    js("() => MapView.setCam({ x: 0, y: 260, z: 2 })"); pg.wait_for_timeout(300)
    def card():
        with pg.expect_download() as dl:
            pg.click('#btnPostcard')
        return Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes())).convert('RGB')
    size = js("() => { const r = document.querySelector('#map').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }")
    on = card()
    pg.uncheck('#optCaption'); pg.click('#optCardSize [data-value="double"]'); pg.wait_for_timeout(150)
    off2 = card()
    ok(f'by default a postcard is the view at screen size, with the caption ({on.size}, {on.getpixel((18, size[1] - 18))})', on.size == tuple(size) and on.getpixel((18, size[1] - 18)) == (34, 29, 51))
    ok(f'doubled, it is twice the size, and without the caption no box is drawn ({off2.size})', off2.size == (size[0] * 2, size[1] * 2) and off2.getpixel((36, size[1] * 2 - 36)) != (34, 29, 51))
    off2.save(SH / '210-postcard-doubled.png')
    js("() => Settings.resetTab('look')"); js("() => { Light.setMode('day'); MapView.setBubbleMode('none'); MapView.syncBar(); }")

    # ---------- Projects: rest days and away until ----------
    open_settings(pg, 'projects')
    pg.click('#optRest [data-day="6"]'); pg.click('#optRest [data-day="0"]'); pg.wait_for_timeout(120)
    ok('rest days are picked by weekday, Saturday first as the week runs', js("() => DB.city.rest.join()") == '0,6' and pg.get_attribute('#optRest [data-day="6"]', 'aria-pressed') == 'true'
       and js("() => [...document.querySelectorAll('#optRest .set-day')].map(b => b.textContent).join()") == 'Sat,Sun,Mon,Tue,Wed,Thu,Fri')
    u = js("""() => { const save = JSON.stringify(DB.city);
      const mk = (sys, last) => Object.assign(blankProject({ name: 'T' }), { urgency: { system: sys, days: 1, lastWorked: last, pickedAt: new Date(2026, 8, 1).getTime() }, todos: [todo('a')] });
      const fri = new Date(2026, 9, 9, 17, 0).getTime(), mon = new Date(2026, 9, 12, 10, 0).getTime();
      const pace = mk('pace', fri), fin = mk('finish', fri), due = mk('pace', fri); due.todos[0].due = '2026-10-11';
      const out = {};
      DB.city.rest = []; out.paceNoRest = urgencyOf(pace, mon).color; out.finNoRest = urgencyOf(fin, mon).color;
      DB.city.rest = [6, 0]; out.paceRest = urgencyOf(pace, mon).color; out.finRest = urgencyOf(fin, mon).color; out.why = urgencyOf(fin, mon).reasons.join(' ');
      out.dueRest = urgencyOf(due, mon).color;
      DB.city.rest = []; DB.city.away = '2026-10-15';
      out.awayBefore = urgencyOf(pace, mon).color; out.awayDue = urgencyOf(due, mon).color;
      out.awayBack = urgencyOf(pace, new Date(2026, 9, 15, 10).getTime()).color; out.awayLater = urgencyOf(pace, new Date(2026, 9, 16, 1).getTime()).color;
      DB.city = JSON.parse(save); return out; }""")
    ok(f'last worked Friday at 17:00, on Monday at 10:00 a day\'s pace is red and Work until finished red ({u["paceNoRest"]}, {u["finNoRest"]})', u['paceNoRest'] == 'red' and u['finNoRest'] == 'red')
    ok(f'with the weekend as rest days only 17 hours count: neither goes red ({u["paceRest"]}, {u["finRest"]})', u['paceRest'] is None and u['finRest'] == 'yellow' and 'not counting rest days' in u['why'])
    ok(f'a task due on Sunday is overdue on Monday, rest days or not ({u["dueRest"]})', u['dueRest'] == 'red')
    ok(f'away until Thursday: no yellow or red from the systems, but a due date still turns red ({u["awayBefore"]}, {u["awayDue"]})', u['awayBefore'] is None and u['awayDue'] == 'red')
    ok(f'from Thursday every system counts from that day: calm at 10:00, yellow after 25 hours ({u["awayBack"]}, {u["awayLater"]})', u['awayBack'] is None and u['awayLater'] == 'yellow')
    gid = js("""() => { const p = DB.projects.find(p => p.name.startsWith('Garden')); p.urgency = { system: 'pace', days: 1, lastWorked: Date.now() - 5 * 864e5, pickedAt: Date.now() - 30 * 864e5 }; changed(p); MapView.setBubbleMode('all'); return p.id; }""")
    pg.wait_for_timeout(200)
    red = js(f"() => !!MapView.bubbleAt('{gid}')")
    soon = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    pg.fill('#optAway', soon); pg.wait_for_timeout(200)
    ok(f'set in Settings, the date is the city\'s, and the building waits with no bubble ({red} before)', red and js("() => DB.city.away") == soon and not js(f"() => !!MapView.bubbleAt('{gid}')"))
    pg.click('#btnAwayClear'); pg.wait_for_timeout(200)
    ok('Clear brings the bubble back', js("() => DB.city.away") == '' and js(f"() => !!MapView.bubbleAt('{gid}')"))
    js("() => MapView.setBubbleMode('none')")

    # ---------- Links: folder links and their test ----------
    open_settings(pg, 'links')
    pg.click('#btnFolderTest'); pg.wait_for_timeout(200)
    ok(f'Test folder links opens C:\\Windows through a folder link ({js("() => window.__opened")})', js("() => window.__opened") == ['nullovation-folder:C%3A%5CWindows'] and 'setup has not run' in pg.text_content('#toast'))
    pg.check('#optExplorer'); pg.wait_for_timeout(100)
    ok('the folder links setting stays on this computer, with a dot when on', js("() => explorerLinks()") and js("() => document.querySelector('[data-set=\"explorer\"]').classList.contains('changed')"))
    pg.click('#btnTabReset'); pg.wait_for_timeout(100)
    ok('and Reset to defaults turns it off', not js("() => explorerLinks()"))

    # ---------- Saving: daily backups and storage use ----------
    open_settings(pg, 'saving')
    ok('daily backups start off, with a folder to pick', 'Pick a backups folder' in pg.text_content('#backupBox'))
    pg.click('#backupBox >> text=Pick a backups folder'); pg.wait_for_timeout(800)
    files = js("() => [...window.__files.keys()].sort()")
    daily = [f for f in files if f.startswith('nullovation-city-daily-')]
    ok(f'picking a folder takes today\'s copy at once ({TODAY})', f'nullovation-city-daily-{TODAY}.json' in files and js("() => window.__dirWrites") == 1)
    copy = json.loads(js(f"() => window.__files.get('nullovation-city-daily-{TODAY}.json')"))
    ok('the copy is a whole backup: the map, the city\'s settings and every project', copy['version'] == 3 and len(copy['projects']) == 2 and copy['city']['crowd'] == 'large' and copy['world']['nu'] == 5)
    ok(f'and keeps the newest 14 daily copies ({len(daily)}, the oldest {daily[0]})', len(daily) == 14 and daily[0] == 'nullovation-city-daily-2026-09-03.json')
    ok('exported backups in the same folder are never touched', 'nullovation-city-backup-2026-09-01.json' in files and 'nullovation-city-backup-2026-10-01.json' in files)
    ok(f'Settings shows the folder and the latest copy ({pg.text_content("#backupBox")})', 'City backups' in pg.text_content('#backupBox') and '14 copies kept' in pg.text_content('#backupBox'))
    js("() => Backups.tick()"); pg.wait_for_timeout(300)
    ok('one copy a day: a second look the same day writes nothing', js("() => window.__dirWrites") == 1)
    js(f"() => {{ window.__files.delete('nullovation-city-daily-{TODAY}.json'); window.__failWrite = 'NotAllowedError'; }}")
    pg.click('#backupBox >> text=Stop'); pg.wait_for_timeout(200)
    pg.click('#backupBox >> text=Pick a backups folder'); pg.wait_for_timeout(600)
    ok('when the browser holds back permission, saving pauses and says so in the side bar too, with Allow', js("() => Backups.state()") == 'paused' and pg.is_visible('#backupAlert') and 'Allow them' in pg.text_content('#backupAlert'))
    js("() => { window.__failWrite = null; }")
    pg.click('#backupAlert >> text=Allow them'); pg.wait_for_timeout(600)
    ok('Allow saves the day\'s copy, and the alert goes', js("() => Backups.state()") == 'on' and not pg.is_visible('#backupAlert') and js(f"() => window.__files.has('nullovation-city-daily-{TODAY}.json')"))
    used0 = js("() => Settings.storageUsed()")
    txt = pg.text_content('#storageBox')
    ok(f'storage use shows how much this browser holds, against about 5 MB ({txt[:60]})', 'of about 5 MB' in txt and f'{max(1, round(used0 / 1024))} KB' in txt)
    js("() => { const p = DB.projects[0]; p.notes.push({ id: uid('n'), title: 'Long', text: 'x'.repeat(7000), at: Date.now() }); p.notes.push({ id: uid('n'), title: 'Long 2', text: 'y'.repeat(7000), at: Date.now() }); persistNow(); Settings.refresh(); }")
    pg.wait_for_timeout(200)
    ok(f'and grows with the city ({used0} to {js("() => Settings.storageUsed()")} characters)', js("() => Settings.storageUsed()") > used0 + 13000)
    pg.screenshot(path=str(SH / '211-settings-saving-on.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})

    # ---------- which settings travel ----------
    open_settings(pg, 'look'); pg.fill('#optNight', '21:00')
    open_settings(pg, 'projects'); pg.click('#optRest [data-day="5"]')
    open_settings(pg, 'saving')
    with pg.expect_download() as dl:
        pg.click('#btnExport')
    data = json.loads(pathlib.Path(dl.value.path()).read_text(encoding='utf-8'))
    (DATA / 'backup-v3-settings.json').write_text(json.dumps(data), encoding='utf-8')
    cityk = sorted(data['city'].keys())
    ok(f'a backup carries the city\'s settings ({len(cityk)} of them)', cityk == sorted(js("() => Object.keys(CITY_DEFAULTS)") + ['parks'])
       and data['city']['crowd'] == 'large' and data['city']['night'] == '21:00' and data['city']['deal'] == 1 and data['city']['rest'] == [0, 5, 6])
    ok('and nothing of this computer: no light, bubbles, traffic, motion, postcard or folder links', not any(k in json.dumps(data['city']) for k in ('"light"', '"bubbles"', '"traffic"', '"motion"', '"caption"', '"explorer"'))
       and set(data.keys()) == {'app', 'version', 'exportedAt', 'world', 'city', 'projects'})
    b.close()

# a fresh browser: importing that backup brings the city's settings, while this computer keeps its own
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(FILE); pg.wait_for_timeout(1500)
    js = pg.evaluate
    pg.set_input_files('#fileImport', str(DATA / 'backup-v3-settings.json')); pg.wait_for_timeout(300)
    pg.click('.confirm-actions .btn-danger'); pg.wait_for_timeout(900)
    ok('importing a backup brings the city\'s settings with it', js("() => [DB.city.crowd, DB.city.night, DB.city.deal, DB.city.rest.join()]") == ['large', '21:00', 1, '0,5,6'])
    ok('while this computer keeps its own: Auto, the bubbles, the traffic on, motion following the system', js("() => [Light.mode, MapView.bubbleMode(), Traffic.isOn(), Motion.mode()]") == ['auto', 'all', True, 'full'])
    pg.set_input_files('#fileImport', fixture('backup-v1.json')); pg.wait_for_timeout(300)
    pg.click('.confirm-actions .btn-danger'); pg.wait_for_timeout(900)
    ok('an older backup imports with default settings', js("() => Object.keys(CITY_DEFAULTS).every(k => JSON.stringify(DB.city[k]) === JSON.stringify(CITY_DEFAULTS[k]))"))
    b.close()

# a computer that asks for reduced motion: Still until another is chosen
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.goto(FILE); pg.wait_for_timeout(1200)
    open_settings(pg, 'look')
    ok('when the system asks for reduced motion, Still is the default, and the note says why', pg.evaluate("() => [Motion.mode(), Motion.dflt()]") == ['still', 'still'] and 'reduced motion' in pg.text_content('#motionNote')
       and not pg.evaluate("() => document.querySelector('[data-set=\"motion\"]').classList.contains('changed')"))
    pg.click('#optMotion [data-value="full"]'); pg.wait_for_timeout(100)
    ok('choosing Full there keeps Full, with a dot', pg.evaluate("() => Motion.mode()") == 'full' and pg.evaluate("() => document.querySelector('[data-set=\"motion\"]').classList.contains('changed')"))
    b.close()
print(errors or 'no console errors')
