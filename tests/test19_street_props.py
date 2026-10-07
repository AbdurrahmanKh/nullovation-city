"""Street props: the bus stop, vending machine, holo billboard and bin, round every block, fixed per block side."""
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY
errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    js = pg.evaluate
    pg.wait_for_function("() => typeof PROPS !== 'undefined' && PROPS.every(p => Art.get('prop:' + p.id + ':front') && Art.get('prop:' + p.id + ':back'))", timeout=20000)
    ok('the four street props decoded, a front and a back each', js("() => PROPS.map(p => p.id).join() === 'busstop,vending,billboard,bin'"))

    plan = js("() => MapView.props()")
    per = {}
    for q in plan: per[(q['u'], q['v'], q['side'])] = per.get((q['u'], q['v'], q['side']), 0) + 1
    kinds = {k: sum(1 for q in plan if q['kind'] == k) for k in ('busstop', 'vending', 'billboard', 'bin')}
    print('NOTE props by kind on the 5 by 5 test city:', kinds, 'on', len(per), 'of 100 block sides')
    ok('every kind stands somewhere, at most two to a block side', all(kinds.values()) and max(per.values()) <= 2)

    geo = js("() => ({ M: WORLD.MARGIN, P: WORLD.PITCH, S: WORLD.S, built: DB.projects.map(p => p.plot.u + ',' + p.plot.v) })")
    M, P, S = geo['M'], geo['P'], geo['S']
    def out_of(q):                                   # how far its foot stands out from the lot edge, and along it
        a0, b0 = M + q['u'] * P, M + q['v'] * P
        a1, b1 = a0 + S, b0 + S
        return {'ne': (b0 - q['j'], q['i'] - a0), 'se': (q['i'] - a1, q['j'] - b0), 'sw': (q['j'] - b1, a1 - q['i']), 'nw': (a0 - q['i'], b1 - q['j'])}[q['side']]
    ok('every prop stands on its sidewalk, beside its own block', all(0 < out_of(q)[0] < 0.3 and abs(out_of(q)[1] - q['a']) < 1e-9 for q in plan))
    ok('it faces its street: fronts on the south-east and south-west, backs on the north-east and north-west',
       all(q['back'] == (q['side'] in ('ne', 'nw')) for q in plan))
    # which way each front faces as PixelLab drew it, checked by eye on the art: the bus stop's and billboard's toward
    # the south-east street, the vending machine's (and the round bin's) toward the south-west one
    faces = js("() => Object.fromEntries(PROPS.map(p => [p.id, p.faces]))")
    ok(f'each prop names the street its front faces as drawn ({faces})', faces == {'busstop': 'se', 'vending': 'sw', 'billboard': 'se', 'bin': 'sw'})
    TURNED, MIRRORED = {'se': 'nw', 'sw': 'ne', 'ne': 'sw', 'nw': 'se'}, {'se': 'sw', 'sw': 'se', 'ne': 'nw', 'nw': 'ne'}
    def drawn_faces(q):                              # the street a prop faces as drawn: its view's own, turned by a mirror
        view = TURNED[faces[q['kind']]] if q['back'] else faces[q['kind']]
        return MIRRORED[view] if q['mirror'] else view
    wrong = [(q['kind'], q['side'], drawn_faces(q)) for q in plan if drawn_faces(q) != q['side']]
    ok(f'every prop, as drawn, faces its own street, mirrored only on the side its view does not face ({wrong[:3]})', not wrong)
    # measured on the art itself: a view's top edge over the middle half of its width rises to the right when its long
    # side runs from bottom left to top right; as drawn, that has to match its street, which rises to the right on the
    # south-east and north-west sides and falls on the other two. The round bin and the boxy vending machine's back
    # have no clear slope and are left out.
    slopes = js("""() => { const out = {};
      for (const p of PROPS) for (const view of ['front', 'back']) {
        const a = Art.get('prop:' + p.id + ':' + view), d = a.src.base, w = a.w, h = d.length / 4 / w, xs = [], ys = [];
        for (let x = Math.round(w / 4); x < Math.round(3 * w / 4); x++)
          for (let y = 0; y < h; y++) if (d[(y * w + x) * 4 + 3]) { xs.push(x); ys.push(y); break; }
        const mx = xs.reduce((s, v) => s + v, 0) / xs.length, my = ys.reduce((s, v) => s + v, 0) / ys.length;
        let num = 0, den = 0; xs.forEach((x, k) => { num += (x - mx) * (ys[k] - my); den += (x - mx) ** 2; });
        out[p.id + ':' + view] = num / den;
      }
      return out; }""")
    print('NOTE top edge slopes (negative rises to the right):', {k: round(v, 2) for k, v in slopes.items()})
    clear = [q for q in plan if abs(slopes[q['kind'] + ':' + ('back' if q['back'] else 'front')]) >= 0.2]
    along = [q for q in clear if (slopes[q['kind'] + ':' + ('back' if q['back'] else 'front')] * (-1 if q['mirror'] else 1) < 0) == (q['side'] in ('se', 'nw'))]
    ok(f'and on the art: every bus stop, billboard and vending machine front stands with its long side along its street ({len(along)} of {len(clear)})',
       len(clear) >= 30 and len(along) == len(clear) and {q['kind'] for q in clear} >= {'busstop', 'billboard', 'vending'})
    ok('bus stops follow the fixed pattern', all((q['u'] * 3 + q['v'] * 5 + ['ne', 'se', 'sw', 'nw'].index(q['side']) * 7) % 5 == 0 for q in plan if q['kind'] == 'busstop'))
    ok('vending machines stand mid-block', all(1.5 <= q['a'] <= 2.5 for q in plan if q['kind'] == 'vending'))
    ok('billboards stand by a corner', all(abs(q['a'] - 0.62) < 1e-9 for q in plan if q['kind'] == 'billboard'))
    ok('bins stand only on a building\'s two front sides', all(q['side'] in ('se', 'sw') and f"{q['u']},{q['v']}" in geo['built'] for q in plan if q['kind'] == 'bin'))
    ok('no prop stands on a zebra\'s landing, near either end of its side', all(0.45 <= q['a'] <= S - 0.45 for q in plan))
    ok('props on one side keep apart', all(abs(x['a'] - y['a']) >= 0.8 for x in plan for y in plan if x is not y and (x['u'], x['v'], x['side']) == (y['u'], y['v'], y['side'])))

    # planting a building adds bins on its own block only; everything else stays as it was
    diff = js("""() => { const key = q => [q.u, q.v, q.side, q.kind, q.a.toFixed(4)].join(), before = MapView.props().map(key);
      const free = []; for (let u = 0; u < WORLD.N; u++) for (let v = 0; v < WORLD.N; v++) if (!DB.projects.some(p => p.plot.u === u && p.plot.v === v)) free.push([u, v]);
      const best = free.map(([u, v]) => { DB.projects.push({ plot: { u, v } }); const after = MapView.props().map(key); DB.projects.pop(); return { u, v, after }; })
        .find(x => x.after.length > before.length);
      MapView.props();
      if (!best) return null;
      const added = best.after.filter(k => !before.includes(k)), lost = before.filter(k => !best.after.includes(k));
      return { added, lost, u: best.u, v: best.v }; }""")
    ok(f'planting a building only adds bins on its own block ({diff and diff["added"]})', diff is not None and not diff['lost'] and all(
        k.split(',')[3] == 'bin' and k.split(',')[0] == str(diff['u']) and k.split(',')[1] == str(diff['v']) for k in diff['added']))

    # drawn even with the traffic off, and fixed: the same plan after a reload
    pg.wait_for_timeout(600)
    ok('props are drawn on screen', js("() => MapView.propsDrawn()") > 0)
    js("() => { Traffic.setOn(false); MapView.invalidate(); }"); pg.wait_for_timeout(400)
    ok('they stay with the traffic off', js("() => MapView.propsDrawn()") > 0)
    js("() => { Traffic.setOn(true); MapView.invalidate(); }")
    pg.screenshot(path=str(SH / '190-street-props.png'))
    pg.reload(); pg.wait_for_function("() => typeof PROPS !== 'undefined'", timeout=20000); pg.wait_for_timeout(400)
    ok('the plan is fixed: the same after a reload', js("() => MapView.props()") == plan)

    # people pass in front of a prop or behind it, by depth
    order = js("""() => { const q = MapView.props()[0], box = { x0: -10, x1: 10, y0: -10, y1: 10 };
      const prop = { i: q.i, j: q.j, key: q.i + q.j, box, name: 'prop' };
      const behind = { i: q.i - 0.1, j: q.j - 0.05, key: q.i + q.j - 0.15, box, name: 'behind' }, front = { i: q.i + 0.1, j: q.j + 0.05, key: q.i + q.j + 0.15, box, name: 'front' };
      return MapView._depthOrder([front, prop, behind]).map(s => s.name).join(); }""")
    ok(f'someone behind a prop is drawn before it, someone in front after it ({order})', order == 'behind,prop,front')

    # a bus pauses at a bus stop on its side of the street, then drives on; on the far side it drives past
    PROBE = """far => { const st = Traffic._state(), P = WORLD.PITCH, C = r => r * P + WORLD.GAP / 2;
      const s = MapView.props().find(q => q.kind === 'busstop' && q.u > 0 && q.v > 0 && q.u < WORLD.N - 1 && q.v < WORLD.N - 1);
      const bus = st.cars.find(c => c.type === 'bus');
      if (!s || !bus) return null;
      const e = { ne: ['i+', s.u, s.v, s.i - C(s.u)], sw: ['i-', s.u + 1, s.v + 1, C(s.u + 1) - s.i],
                  se: ['j+', s.u + 1, s.v, s.j - C(s.v)], nw: ['j-', s.u, s.v + 1, C(s.v + 1) - s.j] }[s.side];
      const flip = { 'i+': 'i-', 'i-': 'i+', 'j+': 'j-', 'j-': 'j+' };
      let [h, ri, rj, t] = e;
      if (far) {                                   // the other lane, driving the other way: the stop is on its left
        const [a, b2] = { 'i+': [1, 0], 'i-': [-1, 0], 'j+': [0, 1], 'j-': [0, -1] }[h];
        ri += a; rj += b2; h = flip[h]; t = P - t;
      }
      st.cars.splice(0, st.cars.length, bus);
      Object.assign(bus, { h, ri, rj, t: t - 0.06, next: null, wait: 0, stopped: false, served: null });
      window.__bus = { bus, t, side: s.side }; return { side: s.side, h, t }; }"""
    res = js(PROBE, False)
    pg.wait_for_timeout(700)
    pr = js("() => ({ t: window.__bus.bus.t, tStop: window.__bus.t, wait: window.__bus.bus.wait, served: window.__bus.bus.served })")
    ok(f'a bus pulls up to a stop on its side and pauses ({res}, {pr})', res is not None and abs(pr['t'] - pr['tStop']) < 1e-6 and pr['wait'] > 0 and pr['served'])
    pg.wait_for_timeout(4200)
    ok('then drives on', js("() => window.__bus.bus.t > window.__bus.t + 0.05 || window.__bus.bus.ri !== undefined && window.__bus.bus.t < window.__bus.t - 1"))
    res = js(PROBE, True)
    pg.wait_for_timeout(1200)
    ok(f'a bus on the far side of the street drives past ({res})', res is not None and js("() => !window.__bus.bus.served && window.__bus.bus.t > window.__bus.t"))

    # by night the props take the city's night colors, and their neon keeps glowing
    night = js("""() => { const a = Art.get('prop:bin:front'), d = a.src.base, w = a.w;
      let k = -1; for (let n = 0; n < d.length; n += 4) if (d[n + 3] && d[n] === 0xF2 && d[n + 1] === 0x9A && d[n + 2] === 0x74) { k = n / 4; break; }
      const b = Art.get('prop:billboard:front'), e = b.src.base; let g = -1;
      for (let n = 0; n < e.length; n += 4) if (e[n + 3] && e[n] === 0x3F && e[n + 1] === 0xE0 && e[n + 2] === 0xF0) { g = n / 4; break; }
      Light.setMode('night');
      const px = (art, n) => Array.from(art.base.getContext('2d').getImageData(n % art.w, Math.floor(n / art.w), 1, 1).data.slice(0, 3));
      const out = { coral: k >= 0 ? px(Art.get('prop:bin:front'), k) : null, cyan: g >= 0 ? px(Art.get('prop:billboard:front'), g) : null };
      Light.setMode('day'); return out; }""")
    ok(f'by night the bin\'s coral turns the city\'s night coral ({night["coral"]})', night['coral'] == [0x8E, 0x46, 0x35])
    ok(f'and the billboard\'s cyan screen keeps glowing ({night["cyan"]})', night['cyan'] == [0x4F, 0xF0, 0xFF])

    # close-ups at 4x, to look at: a bus stop and a billboard on each side of a block
    js("() => { Traffic.setOn(false); MapView.invalidate(); }")
    mid = js("() => { const r = document.querySelector('canvas').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }")
    for kind in ('busstop', 'billboard'):
        for side in ('sw', 'se', 'ne', 'nw'):
            q = next((q for q in plan if q['kind'] == kind and q['side'] == side), None)
            if not q:
                continue
            x, y = js(f"() => MapView.tileToWorld({q['i']}, {q['j']})")
            js(f"() => MapView.setCam({{ x: {x}, y: {y - 12}, z: 4 }})")
            pg.wait_for_timeout(250)
            pg.screenshot(path=str(SH / f'191-{kind}-{side}.png'), clip={'x': mid[0] - 180, 'y': mid[1] - 150, 'width': 360, 'height': 300})
    b.close()
print(errors or 'no console errors')
