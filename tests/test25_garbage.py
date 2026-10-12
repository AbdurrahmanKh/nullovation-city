"""The garbage system: the points (pace, work until finished, late tasks, rest days, away and its spans), the city's
ceiling, the fixed spots, drawing by day and by night, the truck and its crew of three from the street's far end,
Traffic off, Still, Edit City, the switch in Settings, Look, and where garbage shows: the map and the postcard, not
the status card or the status brief."""
import base64, io, pathlib
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# A made-up project, scored at a fixed moment: the urgency system's fields in days before now, and tasks due n days from now.
POINTS = """([urg, todos]) => {
  const D = 864e5, now = Date.now(), u = Object.assign({ system: 'none', days: 1, lastWorked: null, pickedAt: null }, urg);
  for (const k of ['lastWorked', 'pickedAt']) if (u[k] != null) u[k] = now - u[k] * D;
  const p = blankProject({ urgency: u, todos: (todos || []).map((t, k) => ({ id: 't' + k, text: 'Task ' + k, description: '', done: !!t.done,
    doneAt: null, due: t.due == null ? '' : ymd(now + t.due * D), milestoneId: null })) });
  const r = Garbage.rulesOf(p, now); return [r.n, r.why, urgencyOf(p, now).system];
}"""
OPEN = [{}]                       # one open task with no due date, so work until finished has something to finish

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t25')) { sessionStorage.setItem('nc-t25', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); } } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(1500)
    js = pg.evaluate
    pts = lambda urg, todos=None: js(POINTS, [urg, todos])
    hall = js("() => DB.projects.find(p => p.generic === 'city-hall').id")
    lab = js("() => DB.projects.find(p => p.generic === 'research-lab').id")
    force = lambda pid, n: js(f"() => Garbage._test.force('{pid}', {'null' if n is None else n})")
    def snap():     # the map canvas alone, without the buttons and toasts over it
        url = js("() => document.querySelector('#map').toDataURL('image/png')")
        return Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')
    def changed_px(x, y): return ImageChops.difference(x, y).convert('L').point(lambda v: 255 if v > 24 else 0).histogram()[255]

    # ---------- the points ----------
    ok('the test city starts clean: no urgency system, no late task, no garbage', js("() => Garbage.totals().total") == 0 and js(f"() => Garbage.shownOf('{hall}') + Garbage.shownOf('{lab}')") == 0)
    ok('one task per 2 days, one period missed: yellow, 5', pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 2.5})[0::2] == [5, 'yellow'])
    ok('two periods missed: red, 10', pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 4.5})[0::2] == [10, 'red'])
    ok('three periods: 20, and 10 more each period after (five: 40)', pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 6.5})[0] == 20 and pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 10.5})[0] == 40)
    ok('a period not yet missed: nothing', pts({'system': 'pace', 'days': 1, 'pickedAt': 30, 'lastWorked': 0.5})[0] == 0)
    r = pts({'system': 'pace', 'days': 1, 'pickedAt': 1.5})
    ok(f'never worked since the pace was set a day and a half ago: red as its bubble says, 10 ({r})', r[0::2] == [10, 'red'])
    ok('work until finished with a task finished today: yellow, and no garbage', pts({'system': 'finish', 'lastWorked': 0.5}, OPEN)[0::2] == [0, 'yellow'])
    ok('no task finished for a day and a half: red, 10', pts({'system': 'finish', 'lastWorked': 1.5}, OPEN)[0::2] == [10, 'red'])
    ok('for 3.2 days: 30, 10 more each day', pts({'system': 'finish', 'lastWorked': 3.2}, OPEN)[0] == 30)
    ok('never finished, set 2.5 days ago: 20', pts({'system': 'finish', 'pickedAt': 2.5}, OPEN)[0] == 20)
    ok('work until finished with nothing left to do: nothing', pts({'system': 'finish', 'lastWorked': 5})[0] == 0)
    ok('a task a day late: 5', pts({}, [{'due': -1}])[0] == 5)
    ok('3 days late: 15; a month: 150', pts({}, [{'due': -3}])[0] == 15 and pts({}, [{'due': -30}])[0] == 150)
    ok('due today, or done though late: nothing', pts({}, [{'due': 0}])[0] == 0 and pts({}, [{'due': -4, 'done': True}])[0] == 0)
    r = pts({}, [{'due': -1}, {'due': -4}])
    ok(f'two late tasks add up, and the reason says so ({r})', r[0] == 25 and r[1] == '2 late tasks 25')
    r = pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 4.5}, [{'due': -2}])
    ok(f'red and a late task together: 20 ({r})', r[0] == 20 and r[1] == 'red 10, 1 late task 10')

    js("() => { DB.city.rest = [0, 1, 2, 3, 4, 5, 6]; }")
    ok('rest days pause the urgency points', pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 6.5})[0] == 0 and pts({'system': 'finish', 'lastWorked': 3}, OPEN)[0] == 0)
    ok('but not the late ones', pts({}, [{'due': -3}])[0] == 15)
    js("() => { DB.city.rest = []; DB.city.away = ymd(Date.now() + 2 * 864e5); }")
    ok('away: no urgency points', pts({'system': 'pace', 'days': 2, 'pickedAt': 30, 'lastWorked': 6.5})[0] == 0)
    js("() => { DB.city.away = ''; DB.city.awaySpans = [[ymd(Date.now() - 3 * 864e5), ymd(Date.now() - 864e5)]]; }")
    ok('a late task stops growing while away: away 3 days ago, back yesterday, a task due 5 days ago counts 4 days, 20', pts({}, [{'due': -5}])[0] == 20)
    js("() => { DB.city.awaySpans = [[ymd(Date.now() - 2 * 864e5), ymd(Date.now() + 3 * 864e5)]]; }")
    ok('away since 2 days ago: it keeps what it had that day, 3 days, 15', pts({}, [{'due': -5}])[0] == 15)
    ok('a task that fell due while away starts late on the day you are back', pts({}, [{'due': -1}])[0] == 0)
    js("() => { DB.city.awaySpans = []; }")

    # ---------- away records its days ----------
    open_settings(pg, 'projects')
    d = lambda n: js(f"() => ymd(Date.now() + {n} * 864e5)")
    pg.fill('#optAway', d(3)); pg.dispatch_event('#optAway', 'change'); pg.wait_for_timeout(150)
    ok('setting away opens a span from today to the day you are back', js("() => DB.city.awaySpans") == [[d(0), d(3)]])
    pg.fill('#optAway', d(5)); pg.dispatch_event('#optAway', 'change'); pg.wait_for_timeout(150)
    ok('changing the date moves its end', js("() => DB.city.awaySpans") == [[d(0), d(5)]])
    pg.click('#btnAwayClear'); pg.wait_for_timeout(150)
    ok('Clear on the same day leaves no span', js("() => DB.city.awaySpans") == [])
    js("() => { DB.city.awaySpans = [[ymd(Date.now() - 2 * 864e5), ymd(Date.now() + 3 * 864e5)]]; DB.city.away = ymd(Date.now() + 3 * 864e5); Settings.refresh(); }")
    pg.click('#btnAwayClear'); pg.wait_for_timeout(900)
    ok('Clear after a few days away ends the span today', js("() => DB.city.awaySpans") == [[d(-2), d(0)]])
    ok('the spans travel in the data', js("() => JSON.parse(localStorage.getItem('nullovation-city:v1')).city.awaySpans") == [[d(-2), d(0)]])
    ok('and are read with care: a broken or backward span is dropped',
       js("() => sanitizeCity({ awaySpans: [['2026-01-01', '2026-01-05'], ['bad', 'x'], ['2026-02-05', '2026-02-01'], 5] }).awaySpans") == [['2026-01-01', '2026-01-05']]
       and js("() => sanitizeCity(null).awaySpans") == [])
    js("() => { DB.city.awaySpans = []; persistNow(); }")
    close_settings(pg)

    # ---------- the ceiling ----------
    force(hall, 400); force(lab, 200)
    t = js("() => Garbage.totals()")
    ok(f'over the ceiling of {js("() => Garbage.CEILING")}: 600 pieces asked, 500 shown ({t})', t['total'] == 600 and t['shown'] == 500)
    sh = js(f"() => [Garbage.shownOf('{hall}'), Garbage.shownOf('{lab}')]")
    ok(f'every building\'s share shrinks in proportion: 333 and 167 ({sh})', sh == [333, 167])
    force(lab, 0); force(hall, 2000)
    ok('one building alone can take the whole ceiling', js(f"() => Garbage.shownOf('{hall}')") == 500)
    force(hall, 100); force(lab, 50)
    ok('under it, every building shows what it asks', js(f"() => [Garbage.shownOf('{hall}'), Garbage.shownOf('{lab}')]") == [100, 50])

    # ---------- the spots ----------
    W = js("() => ({ S: WORLD.S, M: WORLD.MARGIN, P: WORLD.PITCH, TI: WORLD.MARGIN * 2 + WORLD.NU * WORLD.PITCH - WORLD.GAP, TJ: WORLD.MARGIN * 2 + WORLD.NV * WORLD.PITCH - WORLD.GAP })")
    plot = js(f"() => getProject('{hall}').plot")
    a0, b0 = W['M'] + plot['u'] * W['P'], W['M'] + plot['v'] * W['P']; a1, b1 = a0 + W['S'], b0 + W['S']
    spots = js(f"() => Garbage._test.spots('{hall}').map(s => [s.i, s.j, s.kind, s.lift])")
    ok(f'640 fixed spots a building, so even a forgotten one has room ({len(spots)})', len(spots) == 640)
    ok('all four kinds: paper, sticky notes, cans and bags', {s[2] for s in spots} == {'paper', 'note', 'can', 'bag'})
    ok('every spot on the map', all(0.15 <= s[0] <= W['TI'] - 0.15 and 0.15 <= s[1] <= W['TJ'] - 0.15 for s in spots))
    first = spots[:15]
    ok('the first pieces lie on the building\'s front strip and front sidewalks',
       all((s[0] >= a1 - 0.56 or s[1] >= b1 - 0.56) and a0 - 0.06 <= s[0] <= a1 + 0.26 and b0 - 0.06 <= s[1] <= b1 + 0.26 for s in first))
    ok('those on the plot stand on it, lifted 3 px', any(s[3] == 3 for s in first) and all(s[3] == 3 for s in spots if a0 < s[0] < a1 - 0.1 and b0 < s[1] < b1 - 0.1))
    park = js(f"() => {{ const taken = new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v)), u = getProject('{hall}').plot.u, v = getProject('{hall}').plot.v; return [[1,0],[0,1],[1,1]].map(([a, b]) => [u + a, v + b]).find(([a, b]) => !taken.has(a + ',' + b)); }}")
    c0, d0 = W['M'] + park[0] * W['P'], W['M'] + park[1] * W['P']
    ok(f'some spill into the nearest park, at plot {park}', any(c0 < s[0] < c0 + W['S'] and d0 < s[1] < d0 + W['S'] for s in spots))
    sig = js(f"() => Garbage._test.spots('{hall}').slice(0, 60).map(s => [s.i.toFixed(4), s.j.toFixed(4), s.kind, s.variant].join()).join(';')")

    # ---------- drawn on the map: by day, with the switch, by night ----------
    js("() => { Motion.set('still'); MapView.frameAll(); MapView.invalidate(); }"); pg.wait_for_timeout(500)
    force(hall, 0); force(lab, 0); pg.wait_for_timeout(300)
    clean = snap()
    ok('nothing drawn with no garbage', js("() => Garbage._test.visible()") == 0)
    force(hall, 60); force(lab, 40); pg.wait_for_timeout(400)
    ok(f'every piece drawn on the map ({js("() => Garbage._test.visible()")} of 100)', js("() => Garbage._test.visible()") == 100)
    dirty = snap()
    nd = changed_px(clean, dirty)
    ok(f'and seen: {nd} pixels change', nd > 150)
    open_settings(pg, 'look')
    ok('Settings, Look has the Garbage switch, on by default', pg.is_visible('#optGarbage') and pg.is_checked('#optGarbage') and js("() => Garbage.isOn()"))
    pg.screenshot(path=str(SH / '253-garbage-settings.png'))
    pg.click('#optGarbage'); pg.wait_for_timeout(300)
    ok('off: the switch is kept on this computer, with a dot', js("() => Garbage.isOn()") is False and js("() => localStorage.getItem('nullovation-city:garbage')") == '0'
       and js("() => document.querySelector('[data-set=\"garbage\"]').classList.contains('changed')"))
    ok('and nothing is drawn', js("() => Garbage._test.visible()") == 0)
    close_settings(pg); pg.wait_for_timeout(300)
    off = snap()
    ok('the city looks clean: the same pixels as with no garbage', ImageChops.difference(clean, off).getbbox() is None)
    pg.reload(); pg.wait_for_timeout(1500)
    ok('it stays off after a reload', js("() => Garbage.isOn()") is False)
    ok('the spots are the same after a reload', js(f"() => Garbage._test.spots('{hall}').slice(0, 60).map(s => [s.i.toFixed(4), s.j.toFixed(4), s.kind, s.variant].join()).join(';')") == sig)
    js("() => Settings.resetTab('look')"); pg.wait_for_timeout(200)
    ok('Reset to defaults on Look turns it back on', js("() => Garbage.isOn()") is True)
    open_settings(pg, 'look')
    ok('and the switch shows it', pg.is_checked('#optGarbage'))
    close_settings(pg)

    js("() => { Light.setMode('day'); Motion.set('still'); }")
    sx, sy = js(f"() => {{ const p = getProject('{hall}').plot, M = WORLD.MARGIN, P = WORLD.PITCH; return MapView.tileToWorld(M + p.u * P + 2, M + p.v * P + 2); }}")
    js(f"() => {{ MapView.setCam({{ x: {sx}, y: {sy + 10}, z: 3 }}); MapView.invalidate(); }}")
    force(hall, 120); force(lab, 0); pg.wait_for_timeout(500)
    pg.screenshot(path=str(SH / '250-garbage-day.png'))
    js("() => { Light.setMode('night'); MapView.invalidate(); }"); pg.wait_for_timeout(500)
    pg.screenshot(path=str(SH / '251-garbage-night.png'))
    night_dirty = snap()
    force(hall, 0); pg.wait_for_timeout(300)
    night_clean = snap()
    nd = changed_px(night_clean, night_dirty)
    ok(f'garbage shows at night too, with no glow of its own: {nd} pixels change', nd > 150)
    glint = js("() => { const c = Garbage._test.art().can[0].plain, d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, out = []; for (let k = 0; k < d.length; k += 4) if (d[k + 3]) out.push([d[k], d[k + 1], d[k + 2]].join()); return out; }")
    ok('a can\'s cyan glint stays lit at night, brighter as the neon does', '79,240,255' in glint)
    js("() => { Light.setMode('day'); MapView.invalidate(); }")

    # ---------- where it shows: the postcard, not the status card or the brief ----------
    def card():
        with pg.expect_download() as dl:
            pg.click('#btnPostcard')
        pg.wait_for_timeout(300)
        return Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes())).convert('RGB')
    force(hall, 80); pg.wait_for_timeout(300)
    with_junk = card()
    force(hall, 0); pg.wait_for_timeout(300)
    without = card()
    nd = changed_px(with_junk, without)
    ok(f'the postcard carries the garbage: {nd} pixels change', nd > 150)
    force(hall, 80); pg.wait_for_timeout(200)
    js("() => Garbage.setOn(false)"); pg.wait_for_timeout(200)
    ok('and with the switch off, a clean postcard', ImageChops.difference(card(), without).getbbox() is None)
    js("() => Garbage.setOn(true)")
    js(f"() => MapView.select('{hall}', {{ glide: false }})"); pg.wait_for_timeout(400)
    ok('the status card says nothing of garbage', pg.is_visible('#bubble') and 'arbage' not in pg.text_content('#bubble'))
    js("() => MapView.deselect()")
    ok('nor does the status brief: garbage is visuals only', 'arbage' not in js("() => statusBrief()"))
    js(f"() => FullView.open('{hall}')"); pg.wait_for_timeout(700)
    scene = lambda: Image.open(io.BytesIO(pg.locator('.pv-scene canvas').screenshot())).convert('RGB')
    pv = scene(); pg.locator('.pv-hero-pic').screenshot(path=str(SH / '254-garbage-project-view.png'))
    force(hall, 0); pg.wait_for_timeout(500)
    nd = changed_px(pv, scene())
    ok(f'the project view\'s picture, the map\'s own drawing, shows it too: {nd} pixels change', nd > 100)
    js("() => FullView.close()"); force(hall, 80)
    js(f"() => {{ MapView.setCam({{ x: {sx}, y: {sy + 10}, z: 3 }}); MapView.invalidate(); }}"); pg.wait_for_timeout(400)

    # ---------- Edit City hides it ----------
    pg.wait_for_timeout(300)
    seen = js("() => Garbage._test.visible()")
    open_settings(pg, 'city'); pg.click('#btnEditCity'); pg.wait_for_timeout(400)
    ok(f'Edit City hides the garbage ({seen} before)', seen == 80 and js("() => Garbage._test.visible()") == 0 and js("() => Garbage.items().length") == 0)
    pg.click('#btnEditDone'); pg.wait_for_timeout(400); close_settings(pg)
    js(f"() => {{ MapView.setCam({{ x: {sx}, y: {sy + 10}, z: 3 }}); MapView.invalidate(); }}"); pg.wait_for_timeout(300)
    ok('and Done brings it back', js("() => Garbage._test.visible()") == seen)

    # ---------- Still: it just goes ----------
    force(hall, 30); pg.wait_for_timeout(200)
    force(hall, 10); pg.wait_for_timeout(300)
    ok('on Still, a drop just goes: no truck, no sparkle', js(f"() => [Garbage.waitingOf('{hall}'), Garbage.trucks(), Garbage._test.sparkles(), Garbage.shownOf('{hall}')]") == [0, 0, 0, 10])

    # ---------- the truck and its crew ----------
    js("() => { Motion.set('full'); MapView.invalidate(); MapView.kick(); }")
    pg.wait_for_timeout(300)
    ok('traffic is on', js("() => Traffic.isOn()"))
    force(hall, 30); pg.wait_for_timeout(500)
    ok('more garbage comes with no truck', js("() => Garbage.trucks()") == 0)
    force(hall, 12); pg.wait_for_timeout(400)
    ok('a drop calls the truck for the pieces that go, and leaves the rest', js(f"() => [Garbage.waitingOf('{hall}'), Garbage.shownOf('{hall}'), Garbage.trucks()]") == [18, 12, 1])
    job = js("() => Garbage._test.jobs()[0]")
    r = job['r']
    end = (r['s0'] == -0.8 and abs(r['s1'] - (W['TJ'] + 0.8)) < 1e-9) if r['h'] == 'j+' else (abs(r['s0'] - (W['TI'] + 0.8)) < 1e-9 and r['s1'] == -0.8)
    ok(f'it drives in from the map\'s edge at one end of the street and leaves by the other ({r["h"]}, {r["s0"]:.1f} to {r["s1"]:.1f})', end)
    ok('with a crew of three', len(job['crew']) == 3)
    crew_seen, sparks, shot = [], 0, False
    for k in range(120):
        pg.wait_for_timeout(250)
        st = js(f"() => ({{ jobs: Garbage._test.jobs(), waiting: Garbage.waitingOf('{hall}'), sparks: Garbage._test.sparkles(), trucks: Garbage.trucks() }})")
        sparks = max(sparks, st['sparks'])
        if st['jobs'] and st['jobs'][0]['phase'] == 'crew':
            work = [c['at'] for c in st['jobs'][0]['crew'] if c['state'] == 'work']
            if len(work) == 3 and not crew_seen:
                crew_seen = work
                pg.screenshot(path=str(SH / '252-garbage-crew.png')); shot = True
        if st['trucks'] == 0 and st['waiting'] == 0:
            break
    ok(f'the crew spread round the block, each to a spot of its own ({[[round(x, 2) for x in c] for c in crew_seen]})',
       len(crew_seen) == 3 and all(a0 - 0.35 <= c[0] <= a1 + 0.35 and b0 - 0.35 <= c[1] <= b1 + 0.35 for c in crew_seen)
       and all(((x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2) ** 0.5 > 0.9 for n, x in enumerate(crew_seen) for y in crew_seen[n + 1:]))
    ok(f'the pieces go with a sparkle (up to {sparks} at once), the rest stay, and the truck leaves', sparks > 0 and js(f"() => [Garbage.waitingOf('{hall}'), Garbage.shownOf('{hall}'), Garbage.trucks()]") == [0, 12, 0])

    # ---------- at most three trucks out; Traffic off sends the rest with a sparkle ----------
    extra = js("() => [[0, 0], [4, 4], [0, 4], [4, 0]].filter(([u, v]) => !DB.projects.some(p => p.plot.u === u && p.plot.v === v)).map(([u, v], k) => createProject('Spare ' + k, { u, v }, null, 'kiosk').id)")
    ids = [hall, lab] + extra
    for pid in ids: force(pid, 15)
    pg.wait_for_timeout(300)
    for pid in ids: force(pid, 0)
    pg.wait_for_timeout(400)
    ok(f'{len(ids)} buildings cleaned at once: 3 trucks out, the rest waiting their turn', js("() => [Garbage.trucks(), Garbage.queued()]") == [3, len(ids) - 3])
    pg.click('#btnTraffic'); pg.wait_for_timeout(400)
    waiting = js(f"() => {ids}.reduce((s, id) => s + Garbage.waitingOf(id), 0)")
    ok('Traffic off: every truck goes and the garbage goes with a sparkle alone', js("() => Traffic.isOn()") is False and waiting == 0 and js("() => [Garbage.trucks(), Garbage.queued()]") == [0, 0])
    force(hall, 20); pg.wait_for_timeout(200); force(hall, 5); pg.wait_for_timeout(300)
    ok('and a drop with Traffic off sparkles where each piece was', js(f"() => Garbage.waitingOf('{hall}')") == 0 and js("() => Garbage._test.sparkles()") > 0 and js("() => Garbage.trucks()") == 0)
    pg.click('#btnTraffic'); pg.wait_for_timeout(200)
    for pid in ids: force(pid, None)
    js(f"() => {{ for (const id of {extra}) deleteProject(id); }}"); pg.wait_for_timeout(300)

    # ---------- the city's own garbage: what is there on load comes with no truck ----------
    js(f"() => {{ const p = getProject('{hall}'); p.todos[0].due = ymd(Date.now() - 3 * 864e5); changed(p); persistNow(); }}"); pg.wait_for_timeout(1600)
    ok('a task 3 days late puts 15 pieces by its building, within a second', js(f"() => Garbage.shownOf('{hall}')") == 15)
    pg.reload(); pg.wait_for_timeout(1500)
    ok('on load the garbage is simply there: no truck', js(f"() => [Garbage.shownOf('{hall}'), Garbage.waitingOf('{hall}'), Garbage.trucks()]") == [15, 0, 0])
    js(f"() => {{ const p = getProject('{hall}'); p.todos[0].done = true; p.todos[0].doneAt = Date.now(); changed(p); }}"); pg.wait_for_timeout(1600)
    ok('ticking it off calls the truck for all 15', js(f"() => Garbage.waitingOf('{hall}')") == 15 and js("() => Garbage.trucks()") == 1)
    ok('the truck draws: teal, outlined', js("() => { const c = Garbage._test.truck('j+'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let k = 3; k < d.length; k += 4) n += d[k] > 0; return n; }") > 150)
    b.close()
print(errors or 'no console errors')
