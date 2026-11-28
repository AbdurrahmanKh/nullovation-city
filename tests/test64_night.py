"""Night colors (0.1.99): warm colors drawn outside the city's palette (cream, peach, sandstone, pale pink) take their
night from the city's own hand-picked table instead of turning crimson and brick; the table, the lights, outlines and
every cool color keep the night they had."""
import base64, io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
from testkit import FILE, SH, TEST_CITY
errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# the formula until 0.1.98, for comparing: the same hue, darker, a quarter of the way toward blue-violet
OLD = """(r, g, b) => { const [hh, ss, ll] = rgbToHsl(r, g, b);
  let dh = 0.694 - hh; if (dh > 0.5) dh -= 1; if (dh < -0.5) dh += 1;
  return hslToRgb((hh + dh * 0.25 + 1) % 1, Math.min(1, ss * 0.55 + 0.05), 0.05 + ll * 0.36); }"""


def warm_block():
    """A small building drawn the way PixelLab draws, off the palette: cream walls lit and shaded, a peach roof,
    a cream plaza, a lit window and a dark warm outline."""
    im = Image.new('RGBA', (128, 96), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(0, 64), (64, 32), (127, 64), (64, 95)], fill=(247, 237, 205), outline=(11, 1, 1))      # the plaza
    d.rectangle([34, 20, 63, 70], fill=(253, 225, 205), outline=(11, 1, 1))                          # lit wall
    d.rectangle([64, 20, 93, 70], fill=(230, 175, 145), outline=(11, 1, 1))                          # wall in shade
    d.polygon([(34, 20), (64, 6), (93, 20)], fill=(250, 145, 124), outline=(11, 1, 1))               # roof
    d.rectangle([42, 34, 52, 46], fill=(255, 227, 138), outline=(11, 1, 1))                          # a lit window
    b = io.BytesIO(); im.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    js = pg.evaluate
    pg.wait_for_function("() => typeof GENERICS !== 'undefined' && GENERICS.every(g => !!Art.get('g:' + g.id))", timeout=20000)
    js(f"() => {{ window.__old = {OLD}; window.__table = new Set(Object.keys(NIGHT).map(h => parseInt(h.slice(1), 16))); }}")

    # ---------- what keeps its night ----------
    table = js("() => Object.entries(NIGHT).every(([d, n]) => nightOf(...hexToRgb(d)).join() === hexToRgb(n).join())")
    ok('every color in the city\'s night table keeps its hand-picked night', table)
    lit = js("() => [[255, 232, 150], [255, 92, 170], [96, 236, 246], [242, 199, 92]].map(c => nightOf(...c).join() === c.join())")
    ok(f'lit windows, neon pink, neon cyan and gold keep shining ({lit})', all(lit))
    cool = js("""() => { const bad = [];
      for (let h = 100; h <= 345; h += 1) for (const s of [0.2, 0.5, 0.9]) for (const l of [0.25, 0.5, 0.7, 0.85]) {
        const c = hslToRgb(h / 360, s, l); if (isLightColor(...c) || __table.has((c[0] << 16) | (c[1] << 8) | c[2])) continue;
        if (nightOf(...c).join() !== __old(...c).join()) bad.push([h, s, l]); }
      return bad.length; }""")
    ok(f'cool colors, green round to pink, keep the night they had ({cool} differ)', cool == 0)
    dark = js("() => [[11, 1, 1], [40, 20, 18], [30, 12, 6]].map(c => nightOf(...c).join() === __old(...c).join())")
    ok(f'outlines and other near-black warm colors keep theirs ({dark})', all(dark))

    # ---------- warm colors off the table ----------
    n = js("() => Object.fromEntries([['cream', [247, 237, 205]], ['peach', [253, 225, 205]], ['sand', [224, 190, 168]], ['coral', [250, 145, 124]], ['coralShade', [227, 102, 86]], ['yellow', [215, 195, 120]]].map(([k, c]) => [k, { now: nightOf(...c), old: __old(...c) }]))")
    print('NOTE warm nights, before and now:', {k: (v['old'], v['now']) for k, v in n.items()})
    ok(f"a cream plaza no longer turns brick red ({n['cream']['old']} then, {n['cream']['now']} now)",
       n['cream']['old'][0] - n['cream']['old'][1] > 60 and abs(n['cream']['now'][0] - n['cream']['now'][1]) < 20)
    ok(f"a peach wall turns a dusty mauve, not crimson ({n['peach']['old']} then, {n['peach']['now']} now)",
       n['peach']['old'][0] - n['peach']['old'][1] > 90 and n['peach']['now'][0] - n['peach']['now'][1] < 40 and n['peach']['now'][2] >= n['peach']['now'][1])
    lum = lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    ok(f"a coral's lit side stays lighter than its shade ({n['coral']['now']} over {n['coralShade']['now']})", lum(n['coral']['now']) > lum(n['coralShade']['now']) + 8)
    ramp = js("""() => { const out = [];
      for (const h of [10, 25, 40, 55]) { const row = [];
        for (let l = 0.35; l <= 0.92; l += 0.03) { const c = hslToRgb(h / 360, 0.55, l); if (!isLightColor(...c)) row.push(nightOf(...c)); }
        out.push(row); }
      return out; }""")
    flips = sum(1 for row in ramp for a, b in zip(row, row[1:]) if lum(b) < lum(a) - 0.5)
    ok(f"a warm wall's shades, lightest to darkest, keep their order by night ({flips} out of order)", flips == 0)
    ok(f"a pale yellow no longer turns red ({n['yellow']['old']} then, {n['yellow']['now']} now)",
       n['yellow']['old'][1] < n['yellow']['old'][0] - 40 and n['yellow']['now'][1] > n['yellow']['now'][0] - 25)
    # no jumps round the hue circle: one degree never changes a night by much (until 0.1.98, yellow at 70 degrees
    # jumped from red-orange to green)
    jump = js("""() => { let worst = [0, 0], oldWorst = [0, 0];
      for (const [s, l] of [[0.7, 0.65], [0.5, 0.55], [0.6, 0.45]]) for (let h = 0; h < 360; h += 0.5) {
        const a = hslToRgb(h / 360, s, l), b = hslToRgb(((h + 0.5) % 360) / 360, s, l);
        if (isLightColor(...a) || isLightColor(...b)) continue;
        const d = Math.max(...nightOf(...a).map((v, i) => Math.abs(v - nightOf(...b)[i])));
        const o = Math.max(...__old(...a).map((v, i) => Math.abs(v - __old(...b)[i])));
        if (d > worst[0]) worst = [d, h]; if (o > oldWorst[0]) oldWorst = [o, h]; }
      return { now: worst, old: oldWorst }; }""")
    ok(f"round the hue circle a night changes smoothly (at most {jump['now'][0]} a half degree, against {jump['old'][0]} until 0.1.98)", jump['now'][0] <= 12 and jump['old'][0] > 40)

    # ---------- on the map ----------
    # the city hall, the standard, drawn in cool colors: by night as before but for a few pixels of its pink trim
    hall = js("""() => { const a = Art.get('g:city-hall'), d = a.src.base; let seen = 0, moved = 0, far = 0;
      for (let i = 0; i < d.length; i += 4) { if (!d[i + 3]) continue; seen++;
        const x = nightOf(d[i], d[i + 1], d[i + 2]), y = __table.has((d[i] << 16) | (d[i + 1] << 8) | d[i + 2]) || isLightColor(d[i], d[i + 1], d[i + 2]) ? x : __old(d[i], d[i + 1], d[i + 2]);
        const m = Math.max(...x.map((v, k) => Math.abs(v - y[k]))); if (m) moved++; if (m > 24) far++; }
      return { seen, moved, far }; }""")
    ok(f"the city hall by night is as it was but for {hall['moved']} of {hall['seen']} pixels, {hall['far']} by more than a shade", hall['moved'] < hall['seen'] * 0.06 and hall['far'] < 150)
    url = warm_block()
    js(f"async () => {{ await Art.set('t:warm', '{url}'); }}")
    px = js("""() => { const a = Art.get('t:warm'), w = a.w;
      const at = (x, y) => Array.from(a.base.getContext('2d').getImageData(x, y - (96 - a.h), 1, 1).data.slice(0, 3));
      const day = { wall: at(48, 60), shade: at(80, 60), plaza: at(64, 80), window: at(47, 40), line: at(34, 50) };
      Light.setMode('night');
      const night = { wall: at(48, 60), shade: at(80, 60), plaza: at(64, 80), window: at(47, 40), line: at(34, 50) };
      Light.setMode('day'); return { day, night }; }""")
    print('NOTE the warm block by day and by night:', px)
    ok('uploaded art draws its warm walls by night in the new colors', px['night']['wall'] == js("() => nightOf(253, 225, 205)") and px['night']['plaza'] == js("() => nightOf(247, 237, 205)"))
    ok('its lit window keeps shining and its shaded wall stays darker than its lit one',
       px['night']['window'] == [255, 227, 138] and lum(px['night']['shade']) < lum(px['night']['wall']))
    ok('and by day it is exactly as drawn', px['day']['wall'] == [253, 225, 205] and px['day']['plaza'] == [247, 237, 205])

    # the hue sweep, to look at: by day, until 0.1.98, and now
    sweep = js("""() => { const rows = [];
      for (const [s, l] of [[0.5, 0.85], [0.7, 0.65], [0.6, 0.45]]) {
        const day = [], old = [], now = [];
        for (let h = 0; h < 360; h += 2) { const c = hslToRgb(h / 360, s, l); day.push(c);
          old.push(isLightColor(...c) ? c : __old(...c)); now.push(nightOf(...c)); }
        rows.push(day, old, now); }
      return rows; }""")
    im = Image.new('RGB', (180, len(sweep)))
    for y, row in enumerate(sweep):
        for x, c in enumerate(row): im.putpixel((x, y), tuple(c))
    im.resize((900, len(sweep) * 20), Image.NEAREST).save(SH / '640-night-sweep.png')
    js("() => { Light.setMode('night'); MapView.setCam({ x: 0, y: 160, z: 2 }); MapView.invalidate(); }"); pg.wait_for_timeout(600)
    pg.screenshot(path=str(SH / '641-night-city.png'))
    js("() => Light.setMode('day')")

    ok('no console errors', not errors)
    if errors: print(errors[:5])
    b.close()
