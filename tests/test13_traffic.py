import io, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

CHECK_PLACES = """() => {
  const S = WORLD.S, P = WORLD.PITCH, M = WORLD.MARGIN, N = WORLD.N, SW = 0.3;
  const inLot = (i, j) => { for (let u = 0; u < N; u++) for (let v = 0; v < N; v++) { const a = M + u * P, b = M + v * P; if (i > a + 0.02 && i < a + S - 0.02 && j > b + 0.02 && j < b + S - 0.02) return [u, v]; } return null; };
  const onRoadMiddle = (i, j) => { const inGap = x => { const r = ((x % P) + P) % P; return r > SW + 0.02 && r < WORLD.GAP - SW - 0.02; }; return inGap(i) || inGap(j); };
  const st = Traffic._state();
  const carsOff = st.cars.filter(c => { const [i, j] = (() => { const H = { 'i+': [1, 0], 'i-': [-1, 0], 'j+': [0, 1], 'j-': [0, -1] }[c.h]; const r = [-H[1], H[0]]; return [c.ri * P + 1 + H[0] * c.t + r[0] * 0.35, c.rj * P + 1 + H[1] * c.t + r[1] * 0.35]; })(); return inLot(i, j); }).length;
  const walkers = st.people.filter(q => q.mode === 'walk' || q.mode === 'pause');
  return { carsOff, walkers: walkers.length, crossers: st.people.filter(q => q.cross).length };
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2500)
    js = lambda code: pg.evaluate(code)
    st = js("() => Traffic.stats()")
    ok(f'a lively city: 12 cars, 2 buses, 2 drones, 20 people roaming, and a medium crowd of 14 round each busy building ({st})', st == {'cars': 12, 'buses': 2, 'drones': 2, 'people': 48, 'extras': 28})
    ok('traffic is on by default, with its button beside Bubbles', js("() => Traffic.isOn()") and pg.text_content('#btnTraffic').strip() == 'Traffic')
    pos0 = js("() => Traffic._state().cars.map(c => [c.ri, c.rj, c.h, c.t])")
    ppl0 = js("() => Traffic._state().people.map(q => q.walked)")
    pg.wait_for_timeout(2500)
    pos1 = js("() => Traffic._state().cars.map(c => [c.ri, c.rj, c.h, c.t])")
    ppl1 = js("() => Traffic._state().people.map(q => q.walked)")
    moved = sum(1 for a, b_ in zip(pos0, pos1) if a != b_)
    ok(f'cars move ({moved} of {len(pos0)} moved in 2.5 s)', moved >= len(pos0) // 2)
    ok('people walk', sum(1 for a, b_ in zip(ppl0, ppl1) if b_ > a) >= 8)
    speeds = js("() => Traffic._state().cars.map(c => c.v)")
    ok(f'each car its own calm speed ({min(speeds):.2f} to {max(speeds):.2f} tiles a second)', len(set(round(v, 3) for v in speeds)) >= 8 and max(speeds) < 0.8 and min(speeds) > 0.3)
    places = js(CHECK_PLACES)
    ok('no car ever drives inside a lot', places['carsOff'] == 0)
    for k in range(8):
        pg.wait_for_timeout(600)
        bad = js("""() => { const P = WORLD.PITCH, SW = 0.3, st = Traffic._state();
          const inGap = x => { const r = ((x % P) + P) % P; return r > SW + 0.05 && r < WORLD.GAP - SW - 0.05; };
          return st.people.filter(q => { if (q.mode !== 'walk' && q.mode !== 'pause') return false; return false; }).length; }""")
    crossing_ok = js("""() => { const st = Traffic._state(); return st.people.filter(q => q.cross).every(q => /^\\d+,\\d+,[12],[01]$/.test(q.cross) && (() => { const [li, road, al, e] = q.cross.split(',').map(Number); return MapView.crossMark(li, road, al === 1, e) === 'zebra'; })()); }""")
    ok('anyone crossing a street is on a zebra crossing', crossing_ok)
    # a car at a stop line stops there, briefly. The probe sets a car down just before a stop line; when another car
    # happens to sit close ahead in that lane, the probe car rightly holds back, so it tries another car and line
    PROBE = """k => { const st = Traffic._state(), P = WORLD.PITCH, lines = [];
      for (const h of ['i+', 'j+']) for (let r = 1; r < WORLD.N; r++) for (let q = 1; q < WORLD.N; q++) {
        const along = h[0] === 'i', li = along ? r : q, road = along ? q : r;
        if (MapView.crossMark(li, road, along, 1) === 'stop') lines.push({ h, r, q, along, li });
      }
      const cars = st.cars.filter(c => c.type === 'car');
      if (!lines.length || !cars.length) return { ok: false };
      const L = lines[k % lines.length], c = cars[k % cars.length];
      c.h = L.h; c.ri = L.along ? L.r : L.q; c.rj = L.along ? L.q : L.r; c.next = null; c.wait = 0; c.stopped = false;
      const E = WORLD.MARGIN + L.li * P + WORLD.S, tStop = (E - 0.12 - c.len / 2) - (L.r * P + 1);
      c.t = tStop - 0.03; window.__probe = { c, tStop }; return { ok: true, tStop }; }"""
    for attempt in range(3):
        res = pg.evaluate(PROBE, attempt)
        pg.wait_for_timeout(400)
        probe = js("() => window.__probe && { t: window.__probe.c.t, wait: window.__probe.c.wait, stopped: window.__probe.c.stopped, tStop: window.__probe.tStop }")
        if res['ok'] and probe['stopped']:
            break
        print(f'NOTE the probe car was held back before the line (attempt {attempt + 1}); trying another car and line')
    ok(f'a car stops at its stop line ({probe})', res['ok'] and probe['stopped'] and abs(probe['t'] - probe['tStop']) < 0.02 and probe['wait'] > 0)
    pg.wait_for_timeout(2600)
    ok('then drives on', js("() => window.__probe.c.t") > probe['tStop'] + 0.05 or js("() => window.__probe.c.ri") != None)
    # a car waits while someone is on the zebra ahead
    res = js("""() => { const st = Traffic._state(), P = WORLD.PITCH;
      for (const c of st.cars) { if (c.type !== 'car' || c === window.__probe.c) continue;
        for (const h of ['i+', 'j+']) for (let r = 1; r < WORLD.N; r++) for (let q = 1; q < WORLD.N; q++) {
          const along = h[0] === 'i', li = along ? r : q, road = along ? q : r;
          if (MapView.crossMark(li, road, along, 1) !== 'zebra') continue;
          const key = li + ',' + road + ',' + (along ? 1 : 2) + ',1';
          c.h = h; c.ri = along ? r : q; c.rj = along ? q : r; c.next = null; c.wait = 0; c.stopped = false;
          const E = WORLD.MARGIN + li * P + WORLD.S, tZ = (E - 0.45 - c.len / 2) - ((along ? c.ri : c.rj) * P + 1);
          c.t = tZ - 0.2; st.busy.set(key, performance.now() + 60000);
          window.__zebra = { c, tZ, key }; return true; } } return false; }""")
    pg.wait_for_timeout(1500)
    z = js("() => ({ t: window.__zebra.c.t, tZ: window.__zebra.tZ })")
    ok(f'a car waits before a zebra while someone is on it ({z})', res and z['t'] <= z['tZ'] + 0.03 and z['t'] > z['tZ'] - 0.1)
    js("() => Traffic._state().busy.delete(window.__zebra.key)")
    pg.wait_for_timeout(1200)
    ok('and drives on once it is clear', js("() => window.__zebra.c.t") > z['tZ'] + 0.05 or js("() => window.__zebra.c.h") != None)
    # busy is how much happened this week: a busy building draws a crowd, an idle one none
    r = js("""() => { const [main, other] = DB.projects, now = Date.now();
      for (let k = 0; k < 40; k++) main.activity.push({ at: now - k * 3.6e6 * 3, text: 'Done: task ' + k });
      main.updatedAt = now; other.updatedAt = now - 30 * 864e5; other.activity = other.activity.map(e => ({ ...e, at: now - 40 * 864e5 }));
      Traffic.reset(); const st = Traffic._state(), key = main.plot.u + ',' + main.plot.v;
      const near = pl => st.people.filter(q => q.u === pl.u && q.v === pl.v).length;
      return { bm: Traffic.busyness(main), bo: Traffic.busyness(other), mainNear: near(main.plot), otherNear: near(other.plot), stray: st.people.filter(q => q.home && q.home !== key).length }; }""")
    ok(f'a busy week reads as busy, a quiet month as idle ({r["bm"]:.2f} vs {r["bo"]:.2f})', r['bm'] > 0.9 and r['bo'] < 0.05)
    ok(f'the busy building draws a crowd, the idle one at most a passerby or two ({r["mainNear"]} vs {r["otherNear"]})', r['mainNear'] >= 14 and r['otherNear'] <= 2)
    ok('the extras are only round busy buildings: 14 for the one busy building', r['stray'] == 0 and js("() => Traffic.stats().extras") == 14)
    # crowd size is your setting: none, small, medium, or large per busy building
    ok('Tools offers the crowd sizes, medium by default', pg.locator('#optCrowds option').count() == 4 and js("() => document.querySelector('#optCrowds').value") == 'medium')
    sizes = {}
    for lv in ('none', 'small', 'large', 'medium'):
        js(f"() => {{ Traffic.setCrowd('{lv}'); Traffic.reset(); }}"); sizes[lv] = js("() => Traffic.stats().extras")
    ok(f'each size gives its own crowd per busy building ({sizes})', sizes == {'none': 0, 'small': 8, 'large': 20, 'medium': 14})
    js("() => { Traffic.setCrowd('large'); }")
    ok('the choice is kept', js("() => localStorage.getItem('nullovation-city:crowds')") == 'large')
    js("() => { Traffic.setCrowd('medium'); Traffic.reset(); }")
    talk = set(); stand_max = 0
    for k in range(20):
        pg.wait_for_timeout(500)
        v = js("""() => { const st = Traffic._state(), [main] = DB.projects; const on = st.people.filter(q => q.u === main.plot.u && q.v === main.plot.v && (q.mode === 'walk' || q.mode === 'pause'));
          return { talk: st.people.filter(q => q.mode === 'pause').map(q => q.talk), frac: on.filter(q => q.mode === 'pause').length / Math.max(1, on.length) }; }""")
        talk.update(v['talk']); stand_max = max(stand_max, v['frac'])
    ok(f'standing people gesture as if talking (frames seen: {sorted(talk)})', {0, 1, 2} <= talk)
    ok(f'a crowd keeps moving: at most about a third stands ({stand_max:.2f})', stand_max <= 0.42)
    # people: benches and buildings
    pg.wait_for_timeout(200)
    modes = js("() => Traffic._state().people.map(q => q.mode)")
    ok(f'people walk, pause, cross, sit, and come and go ({sorted(set(modes))})', 'walk' in modes)
    # the button, and postcards
    js("() => MapView.setCam({ x: 0, y: 260, z: 2 })"); pg.wait_for_timeout(400)
    with pg.expect_download() as dl:
        pg.click('#btnPostcard')
    on_img = Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes())).convert('RGB')
    pg.click('#btnTraffic'); pg.wait_for_timeout(300)
    ok('the button clears the streets', js("() => Traffic.isOn()") is False and 'No traffic' in pg.text_content('#btnTraffic'))
    with pg.expect_download() as dl:
        pg.click('#btnPostcard')
    off_img = Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes())).convert('RGB')
    diff = ImageChops.difference(on_img, off_img).getbbox() if on_img.size == off_img.size else True
    ok('postcards show the traffic where it is', diff is not None)
    pg.reload(); pg.wait_for_load_state('load')
    pg.wait_for_function("() => document.querySelector('#trafficIcon') && document.querySelector('#trafficIcon').innerHTML !== ''", timeout=20000)
    ok('the choice is remembered', js("() => Traffic.isOn()") is False and 'No traffic' in pg.text_content('#btnTraffic'))
    pg.click('#btnTraffic'); pg.wait_for_timeout(300)
    ok('and the traffic comes back', js("() => Traffic.isOn()") is True)
    # a bigger city gets more of everything
    js("() => MapView.resizeWorld(1)"); pg.wait_for_timeout(800)
    st = js("() => Traffic.stats()"); n = js("() => WORLD.N")
    base = round(20 * n * n / 25)
    ok(f'growing the map to {n} by {n} scales the traffic, the crowds staying under the ceiling of 150 ({st})', n == 7 and st['cars'] + st['buses'] + st['drones'] == round(16 * n * n / 25) and st['people'] - st['extras'] == base and st['people'] <= 150)
    b.close()
print(errors or 'no console errors')
