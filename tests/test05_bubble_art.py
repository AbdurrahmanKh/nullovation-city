import json, pathlib, io
from playwright.sync_api import sync_playwright
from PIL import Image
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    page = ctx.new_page()
    page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
    page.on('console', lambda m: errors.append(f'console.{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    page.goto(FILE); page.wait_for_timeout(600)
    left = page.evaluate("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    nc = page.evaluate("() => DB.projects.find(p => p.name === 'Nullovation City').id")

    # the 7-day feature is gone
    page.evaluate(f"() => {{ const p = DB.projects.find(x => x.id === '{nc}'); p.updatedAt = Date.now() - 30 * 864e5; persistNow(); MapView.invalidate(); Menu.refresh(); }}")
    a = page.evaluate(f"() => MapView.anchors('{nc}')")
    page.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); page.wait_for_timeout(600)
    meta = page.text_content('#bubble .meta')
    ok(f'bubble shows only the update time ({meta})', 'Updated 30 days ago' in meta and 'Lights' not in meta)
    ok('menu has no lights note', 'Lights' not in page.text_content('#count'))
    page.evaluate("() => MapView.deselect()")
    page.click('#btnBrief'); page.wait_for_timeout(150)
    ok('status brief has no lights line', 'Lights' not in page.evaluate("() => navigator.clipboard.readText()"))
    ok('no lights-off code paths left', page.evaluate("() => typeof isStale === 'undefined' && typeof STALE_DAYS === 'undefined'"))

    # new art defaults to standing on the standard plot
    ok('art defaults to the standard plot', page.evaluate(f"() => DB.projects.find(x => x.id === '{nc}').art.includesPlot === false"))

    # rejected formats
    a = page.evaluate(f"() => MapView.anchors('{nc}')")
    page.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); page.wait_for_timeout(500)
    page.click('#enterBtn'); page.wait_for_timeout(300)
    page.click('.pv-scene'); page.wait_for_timeout(300)
    ok('clicking the building opens the side panel with upload on top', page.is_visible('#pvSide') and page.locator('#pvSide .pv-own').count() == 1)
    page.set_input_files('#pvSide input[type=file]', fixture('test.jpg')); page.wait_for_timeout(300)
    ok('JPEG is refused', 'PNG, or a GIF' in page.text_content('#toast') and not page.evaluate(f"() => DB.projects.find(x => x.id === '{nc}').art.has"))
    page.set_input_files('#pvSide input[type=file]', fixture('test-wide.png')); page.wait_for_timeout(400)
    ok('a 700 px wide image is refused', '700 px wide' in page.text_content('#toast') and not page.evaluate(f"() => DB.projects.find(x => x.id === '{nc}').art.has"))

    # live GIF with padded margins
    page.set_input_files('#pvSide input[type=file]', fixture('test-live.gif')); page.wait_for_timeout(800)
    info = page.evaluate(f"() => {{ const a = Art.get('{nc}'); return a && {{ w: a.w, h: a.h, n: a.count, animated: a.animated, trimmed: a.trimmed, total: a.total }}; }}")
    toast = page.text_content('#toast')
    ok(f'GIF stored as 8 live frames, trimmed top and bottom only ({info})', info and info['n'] == 8 and info['animated'] and info['w'] == 170 and info['trimmed']['left'] == 0 and info['trimmed']['right'] == 0 and info['trimmed']['bottom'] == 9)
    ok(f'upload notes the trim ({toast})', 'Trimmed empty margins' in toast and 'top' in toast and 'left' not in toast and '8 frames' in toast)
    page.screenshot(path=str(SHOTS / '50-art-live-edit.png'))

    # the palette lives in Settings, Look; the building downloads from under its picture
    open_settings(page, 'look')
    with page.expect_download() as dl:
        page.click('#btnPalette')
    pal = Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes())).convert('RGB')
    colors = sorted(set(pal.getdata()))
    expected = page.evaluate("() => CITY_PALETTE.map(c => c[1])")
    exp_rgb = sorted({tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in expected})
    ok(f'palette PNG is {pal.size[0]}x{pal.size[1]} with exactly the 32 city colors', pal.size == (256, 8) and colors == exp_rgb and len(colors) == 32)
    with page.expect_download() as dl:
        page.click('.pv-scene-tools [aria-label="Download the building"]')
    blk = Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes()))
    ok(f'the building downloads as its live GIF ({blk.format}, {getattr(blk, "n_frames", 1)} frames)', blk.format == 'GIF' and getattr(blk, 'n_frames', 1) == 8 and dl.value.suggested_filename.endswith('-building.gif'))
    page.keyboard.press('Escape'); page.wait_for_timeout(200)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)

    # the map animates: frames advance over time
    MapView_frames = []
    for k in range(4):
        MapView_frames.append(page.evaluate(f"() => Art.indexAt(Art.get('{nc}'), performance.now())"))
        page.wait_for_timeout(130)
    ok(f'map frame index advances ({MapView_frames})', len(set(MapView_frames)) >= 3)
    a = page.evaluate(f"() => MapView.anchors('{nc}')")
    clip = {'x': left + a['baseX'] - 140, 'y': a['topY'] - 30, 'width': 280, 'height': a['baseY'] - a['topY'] + 60}
    page.keyboard.press('Escape'); page.wait_for_timeout(150)
    page.evaluate("() => MapView.deselect()")
    s1 = page.screenshot(clip=clip); page.wait_for_timeout(250); s2 = page.screenshot(clip=clip)
    ok('the building visibly changes between frames', s1 != s2)
    pathlib.Path(SHOTS / '52-live-a.png').write_bytes(s1); pathlib.Path(SHOTS / '53-live-b.png').write_bytes(s2)
    page.screenshot(path=str(SHOTS / '54-map-live.png'))

    # art survives reload and stays live
    page.reload(); page.wait_for_timeout(900)
    ok('live art survives reload', page.evaluate(f"() => {{ const a = Art.get('{nc}'); return !!a && a.animated && a.count === 8; }}"))

    # still PNG on another project, bringing its own plot
    wz = page.evaluate("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    page.evaluate("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); page.wait_for_timeout(300)
    a = page.evaluate(f"() => MapView.anchors('{wz}')")
    page.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); page.wait_for_timeout(500)
    page.click('#enterBtn'); page.wait_for_timeout(300)
    page.click('.pv-scene'); page.wait_for_timeout(300)
    page.set_input_files('#pvSide input[type=file]', fixture('test-still.png')); page.wait_for_timeout(700)
    ok('still PNG stored as one frame', page.evaluate(f"() => {{ const a = Art.get('{wz}'); return !!a && !a.animated && a.count === 1 && a.w === 170; }}"))
    page.check('#pvSide .check .cb'); page.wait_for_timeout(200)
    ok('"brings its own plot" switches the mode', page.evaluate(f"() => DB.projects.find(x => x.id === '{wz}').art.includesPlot === true"))

    # a leader note, then the builder card
    page.keyboard.press('Escape'); page.wait_for_timeout(200)
    page.click('#pvAddNoteBtn'); page.wait_for_timeout(200)
    page.fill('#pvNoteBody', 'Leader: Captain Mira, chief of the signal tower. Silver coat, cyan visor, a floating quill.')
    page.click('#pvSide >> text=Done'); page.wait_for_timeout(200)
    ok('a Leader note shows as the leader line under the header', 'Captain Mira' in (page.text_content('#pv .pv-leader') or ''))
    page.click('#pvMore'); page.click('.pv-menu-item >> text=Copy for builder'); page.wait_for_timeout(200)
    card = page.evaluate("() => navigator.clipboard.readText()")
    (DATA / 'card.txt').write_text(card, encoding='utf-8')
    ok('card keeps name, size signals, description, and todos', all(k in card for k in ['# Nullovation City builder card', '## Project', 'Name: ', 'Size signals:', '## Description', '## Open todos']))
    ok('card drops status, notes, links, building, and leader', not any(k in card for k in ['Currently at', 'Progress', 'Deadline', 'Started', '## Recent notes', '## Links', '## Building today', 'Leader']))
    page.keyboard.press('Escape')
    b.close()
print('\n'.join(errors) if errors else 'no console errors')
