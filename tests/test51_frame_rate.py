"""The frame rate (0.1.85): a zoom between the even ones drawn whole at the next even zoom and shrunk onto the screen in
one go, the garbage lying still drawn once into pictures of its own, and the system's reduced motion read from one
query. Checked by what each frame draws, not by the clock: how many pictures reach the map, that none is copied piece
by piece any more, that the shrunk frame matches the old way of drawing pixel for pixel where it must, and when the
garbage's pictures are drawn again."""
import base64, io
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# Counts the canvas calls of one paint of the map: every drawImage and clearRect, and those that reach the map itself.
COUNT = """() => new Promise(res => { const P = CanvasRenderingContext2D.prototype, o = { drawImage: P.drawImage, clearRect: P.clearRect, fillRect: P.fillRect };
  const n = { drawImage: 0, clearRect: 0, mapDraw: 0, mapFill: 0 }, map = document.querySelector('#map');
  P.drawImage = function (...a) { n.drawImage++; if (this.canvas === map) n.mapDraw++; return o.drawImage.apply(this, a); };
  P.clearRect = function (...a) { n.clearRect++; return o.clearRect.apply(this, a); };
  P.fillRect = function (...a) { if (this.canvas === map) n.mapFill++; return o.fillRect.apply(this, a); };
  const before = MapView._paints(); MapView.invalidate();
  const wait = () => { if (MapView._paints() > before) { Object.assign(P, o); res(Object.assign(n, { staged: MapView._staged() })); } else requestAnimationFrame(wait); };
  requestAnimationFrame(wait); })"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t51')) { sessionStorage.setItem('nc-t51', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); localStorage.setItem('nullovation-city:motion', 'still'); } } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(1500)
    js = pg.evaluate
    hall = js("() => DB.projects.find(p => p.generic === 'city-hall').id")
    lab = js("() => DB.projects.find(p => p.generic === 'research-lab').id")
    force = lambda pid, n: js(f"() => Garbage._test.force('{pid}', {'null' if n is None else n})")
    def snap():     # the map canvas alone, without the buttons and toasts over it
        url = js("() => document.querySelector('#map').toDataURL('image/png')")
        return Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')
    def differ(x, y): return ImageChops.difference(x, y).convert('L').point(lambda v: 255 if v > 24 else 0).histogram()[255]
    def cam(z):
        js(f"""() => {{ const p = getProject('{hall}').plot, [x, y] = MapView.tileToWorld(WORLD.MARGIN + p.u * WORLD.PITCH + 2, WORLD.MARGIN + p.v * WORLD.PITCH + 2);
            MapView.setCam({{ x: x + 0.37, y: y - 9.6, z: {z} }}); MapView.invalidate(); }}""")
        pg.wait_for_timeout(300)
    count = lambda: js(COUNT)

    # ---------- the garbage at the ceiling: a few pictures, not a thousand pieces ----------
    force(hall, 600); force(lab, 400); pg.wait_for_timeout(400)
    ok('the city carries 1,000 pieces of garbage', js("() => Garbage.onMap()") == 1000)
    cam(2)
    n = count()
    ok(f'at 2x a frame draws {n["drawImage"]} pictures, where it drew more than 1,000 pieces one by one', n['drawImage'] < 150)
    ok('nothing is copied piece by piece at 2x, and the frame is drawn straight on the map', n['clearRect'] == 0 and n['staged'] is False and n['mapDraw'] > 20)
    pg.screenshot(path=str(SH / '510-frame-garbage-2x.png'))
    built = js("() => Garbage._test.builds()")
    count(); count()
    ok('the pictures are not drawn again while nothing changes', js("() => Garbage._test.builds()") == built)
    ok('each building has its pieces in a picture for its sidewalks and one for each plot it litters', js(f"() => Garbage._test.layers('{hall}')") >= 2 and js(f"() => Garbage._test.layers('{lab}')") >= 2)

    # the same pixels as the pieces drawn one by one, the old way
    for z in (2, 4, 1):
        cam(z)
        cached = snap()
        js("() => Garbage._test.cache(false)"); js("() => MapView.invalidate()"); pg.wait_for_timeout(300)
        live = snap()
        js("() => Garbage._test.cache(true)"); js("() => MapView.invalidate()"); pg.wait_for_timeout(300)
        d = differ(cached, live)
        if z == 1: ok(f'at 1x, shrunk smoothly, nearly the same as the pieces one by one: {d} pixels apart', d < 0.01 * cached.width * cached.height)
        else: ok(f'at {z}x the pictures draw the same pixels as the pieces one by one ({d} apart)', d == 0)

    # when the pictures are drawn again: a change in a building's garbage, only that building's; the light; the wind
    cam(2)
    count()
    built = js("() => Garbage._test.builds()")
    force(hall, 590); pg.wait_for_timeout(300); count()
    ok('less garbage on one building, under the ceiling, draws its pictures again, and only its', js("() => Garbage._test.builds()") == built + 1)
    built = js("() => Garbage._test.builds()")
    force(hall, 640); pg.wait_for_timeout(300); count()
    ok("more, past the ceiling, shrinks the other building's share too, so both are drawn again", js("() => Garbage._test.builds()") == built + 2 and js("() => Garbage.onMap()") == 1000)
    built = js("() => Garbage._test.builds()")
    js("() => { Light.setMode('night'); MapView.invalidate(); }"); pg.wait_for_timeout(300); count()
    ok('the light turning draws both buildings\' pictures again, in the night\'s colors', js("() => Garbage._test.builds()") == built + 2)
    js("() => { Light.setMode('day'); MapView.invalidate(); }"); pg.wait_for_timeout(300)

    js("() => { Traffic.setOn(false); Motion.set('full'); MapView.kick(); }"); pg.wait_for_timeout(300); count()
    built = js("() => Garbage._test.builds()")
    js("() => Garbage._test.gust()"); pg.wait_for_timeout(150)
    hop = js("() => Garbage._test.hops()")
    ok(f'a gust lifts a loose paper, which leaves its building\'s picture and is drawn live in the air ({hop})', len(hop) == 1 and js("() => Garbage._test.builds()") == built + 1 and js("() => Garbage._test.live()") >= 1)
    pg.wait_for_timeout(1400)
    ok('it lands where the wind left it, back in the picture, which is drawn once more', js("() => Garbage._test.hops()") == [] and js("() => Garbage._test.builds()") == built + 2
       and js(f"() => Garbage._test.drift('{hop[0] if hop else ''}')") is not None and js("() => Garbage._test.live()") == 0)
    js("() => { Motion.set('still'); Traffic.setOn(true); }"); pg.wait_for_timeout(300)

    # the switch off lets the pictures go; Edit City hides them, as before
    js("() => Garbage.setOn(false)"); pg.wait_for_timeout(200)
    ok('the garbage switch off lets the pictures go', js(f"() => Garbage._test.layers('{hall}')") == 0)
    js("() => Garbage.setOn(true)"); pg.wait_for_timeout(300); count()
    ok('and on again draws them once more', js(f"() => Garbage._test.layers('{hall}')") >= 2)

    # ---------- 3x: the whole frame at 4x, shrunk onto the screen in one go ----------
    force(lab, 0); force(hall, 400); pg.wait_for_timeout(300)
    cam(3)
    n = count()
    ok(f'at 3x the frame is drawn at 4x and reaches the map as one picture ({n["mapDraw"]} drawn on the map)', n['staged'] is True and n['mapDraw'] == 1 and n['mapFill'] == 0)
    ok(f'and nothing is copied piece by piece, where every building, park, prop and piece of garbage was ({n["clearRect"]} copies)', n['clearRect'] == 0)
    staged = snap()
    pg.screenshot(path=str(SH / '511-frame-3x.png'))
    js("() => MapView._stage(false)"); js("() => MapView.invalidate()"); pg.wait_for_timeout(300)
    old = count()
    each = snap()
    js("() => MapView._stage(true)"); js("() => MapView.invalidate()"); pg.wait_for_timeout(300)
    d = differ(staged, each)
    ok(f'drawn the old way, each building, park, prop and garbage picture was copied on its own ({old["clearRect"]} copies a frame)', old['clearRect'] > 20 and old['staged'] is False)
    ok(f'the shrunk frame matches the old way within a tenth of a percent: {d} of {staged.width * staged.height} pixels apart', d < 0.001 * staged.width * staged.height)
    # the ground lands on whole pixels: each of its pixels a 3 by 3 square, on the same grid as the old way
    px = staged.load(); W, H = staged.size
    tx, ty = js("() => MapView.worldCss(0, 0)")
    def uniform(ox, oy):
        same = total = 0
        for by in range(int(H * 0.1) // 3, int(H * 0.9) // 3, 2):
            for bx in range(int(W * 0.1) // 3, int(W * 0.9) // 3, 2):
                x0, y0 = bx * 3 + ox, by * 3 + oy
                c = px[x0, y0]; total += 1
                same += all(px[x0 + i, y0 + j] == c for i in range(3) for j in range(3))
        return same / total
    on_grid, off_grid = uniform(round(tx) % 3, round(ty) % 3), uniform((round(tx) + 1) % 3, (round(ty) + 1) % 3)
    ok(f'the ground stays crisp at 3x: {on_grid:.0%} of its squares one color on the map\'s grid, {off_grid:.0%} off it', on_grid > 0.6 and on_grid > off_grid + 0.2)

    # what follows the real camera still does: a click lands on the building drawn there, the hover's line sits under it
    a = js(f"() => MapView.anchors('{hall}')")
    box = pg.locator('#map').bounding_box()
    pg.mouse.click(box['x'] + a['baseX'], box['y'] + (a['topY'] + 2 * a['baseY']) / 3); pg.wait_for_timeout(500)
    ok('a click at 3x lands on the building drawn there', js("() => App.selectedId") == hall)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    js("() => MapView.setBubbleMode('all')")
    pg.mouse.move(box['x'] + a['baseX'], box['y'] + (a['topY'] + 2 * a['baseY']) / 3); pg.wait_for_timeout(600)
    lab_el = pg.locator('#hoverTask')
    lb = lab_el.bounding_box() if lab_el.is_visible() else None
    ok(f'the hover\'s line shows under the building at 3x, centred on it ({lb and round(lb["x"] + lb["width"] / 2 - box["x"])} for {round(a["baseX"])})',
       lb is not None and abs(lb['x'] + lb['width'] / 2 - box['x'] - a['baseX']) < 24 and lb['y'] - box['y'] < a['baseY'])
    pg.mouse.move(5, 5); js("() => MapView.setBubbleMode('none')")

    # a zoom on its way between two even ones is drawn whole too, and an even zoom is drawn straight
    cam(2); count()
    js("() => document.querySelector('#zoomIn').click()"); pg.wait_for_timeout(90)
    mid = js("() => [MapView.camState().z, MapView._staged()]")
    ok(f'a zoom gliding from 2x to 3x is drawn whole at 4x on its way ({mid[0]:.2f}x)', 2 < mid[0] < 3 and mid[1] is True)
    pg.wait_for_timeout(400)
    js("() => document.querySelector('#zoomIn').click()"); pg.wait_for_timeout(500)
    ok('and 4x is drawn straight on the map', js("() => [MapView.camState().z, MapView._staged()]") == [4, False])

    # ---------- the system's reduced motion, read from one query, still live ----------
    js("() => Motion.set(null)")
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(100)
    on = js("() => [reducedMotion(), Motion.still()]")
    pg.emulate_media(reduced_motion='no-preference'); pg.wait_for_timeout(100)
    off = js("() => [reducedMotion(), Motion.still()]")
    ok(f'the system asking for reduced motion is still heard at once ({on}, then {off})', on == [True, True] and off == [False, False])
    js("() => Motion.set('still')")
    print('console errors:', errors[:5]) if errors else None
    ok('no console errors', not errors)

    # ---------- a screen at 1.5: 5x is between, drawn at 6x; the project view's picture at 3 ----------
    ctx2 = b.new_context(viewport={'width': 1200, 'height': 800}, device_scale_factor=1.5)
    ctx2.add_init_script(TEST_CITY)
    ctx2.add_init_script("try { localStorage.setItem('nullovation-city:motion', 'still'); localStorage.setItem('nullovation-city:bubbles', 'none'); } catch (e) {}")
    errors2 = []
    q = ctx2.new_page()
    q.on('pageerror', lambda e: errors2.append(str(e))); q.on('console', lambda m: errors2.append(m.text) if m.type in ('error', 'warning') else None)
    q.goto(FILE); q.wait_for_timeout(1500)
    hall2 = q.evaluate("() => DB.projects.find(p => p.generic === 'city-hall').id")
    q.evaluate(f"() => Garbage._test.force('{hall2}', 300)")
    q.evaluate(f"""() => {{ const p = getProject('{hall2}').plot, [x, y] = MapView.tileToWorld(WORLD.MARGIN + p.u * WORLD.PITCH + 2, WORLD.MARGIN + p.v * WORLD.PITCH + 2);
        MapView.setCam({{ x, y, z: 5 / 1.5 }}); MapView.invalidate(); }}"""); q.wait_for_timeout(400)
    r = q.evaluate(COUNT)
    ok(f'on a screen at 1.5, 5 screen pixels to a building pixel is drawn at 6 and shrunk in one go ({q.evaluate("() => MapView.camState().z")})', r['staged'] is True and r['mapDraw'] == 1 and r['clearRect'] == 0)
    q.evaluate(f"() => FullView.open('{hall2}')"); q.wait_for_timeout(900)
    scene = Image.open(io.BytesIO(q.locator('.pv-scene canvas').screenshot())).convert('RGB')
    colors = len(set(scene.tobytes()[i:i + 3] for i in range(0, len(scene.tobytes()), 3)))
    ok(f'the project view\'s picture at 3 canvas pixels to a map pixel is drawn whole too, and shows its street ({colors} colors)', q.evaluate("() => MapView.previewScale()") == 3 and colors > 40)
    q.locator('.pv-hero-pic').screenshot(path=str(SH / '512-frame-scene-1.5.png'))
    print('console errors:', errors2[:5]) if errors2 else None
    ok('no console errors on the screen at 1.5', not errors2)
    b.close()
