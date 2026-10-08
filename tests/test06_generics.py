import pathlib
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY
errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(800)
    left = pg.evaluate("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    import time as _t; t0 = _t.time()
    pg.wait_for_function("() => typeof GENERICS !== 'undefined' && GENERICS.every(g => !!Art.get('g:' + g.id))", timeout=20000)
    print(f'NOTE all generic buildings decoded {(_t.time() - t0) + 0.8:.1f} s after the page loaded')
    ok('12 generic buildings decoded, the worksite among them', pg.evaluate("() => GENERICS.length === 12 && GENERICS.every(g => !!Art.get('g:' + g.id)) && GENERICS[1].id === 'worksite'"))
    ok('the two projects use the city hall and the research lab', pg.evaluate("() => DB.projects.map(p => p.generic).join() === 'city-hall,research-lab'"))
    pg.wait_for_function("() => typeof LOTS !== 'undefined' && LOTS.every(l => !!Art.get('lot:' + l.id))", timeout=20000)
    ok('7 park kinds decoded, the playground, sculpture garden and mini golf among them', pg.evaluate(
        "() => LOTS.map(l => l.id).join() === 'park,pond,plaza,garden,playground,sculpture-garden,mini-golf'"))
    ok('every park kind is 256 by 128', pg.evaluate("() => LOTS.every(l => { const a = Art.get('lot:' + l.id); return a.w === 256 && a.h === 128; })"))
    ok('the three new park kinds animate in 40 frames', pg.evaluate(
        "() => ['playground', 'sculpture-garden', 'mini-golf'].every(id => Art.get('lot:' + id).count === 40)"))
    ok('no park shows the same kind as the one above or to the left of it', pg.evaluate("""() => {
      const nu = WORLD.NU, nv = WORLD.NV, used = new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v)), ids = new Set(LOTS.map(l => l.id));
      for (let u = 0; u < nu; u++) for (let v = 0; v < nv; v++) {
        const k = MapView.lotInfo(u, v).id;
        if (!ids.has(k)) return false;
        if (u > 0 && MapView.lotInfo(u - 1, v).id === k) return false;
        if (v > 0 && MapView.lotInfo(u, v - 1).id === k) return false;
      }
      return true; }"""))
    kinds = pg.evaluate("() => { const nu = WORLD.NU, nv = WORLD.NV, used = new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v)), c = {}; "
                        "for (let u = 0; u < nu; u++) for (let v = 0; v < nv; v++) if (!used.has(u + ',' + v)) { const k = MapView.lotInfo(u, v).id; c[k] = (c[k] || 0) + 1; } return c; }")
    ok('the new kinds show up in the test city', all(kinds.get(k, 0) > 0 for k in ('playground', 'sculpture-garden', 'mini-golf')))
    print('NOTE parks by kind:', kinds)
    idx = [pg.evaluate("() => Art.indexAt(Art.get('g:city-hall'), performance.now())") for _ in range(1)]
    pg.evaluate("() => MapView.setCam({ x: 40, y: 200, z: 3 })"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(SH / '70-seed-generics.png'))
    # name it, then Next
    pg.click('#btnNew'); pg.fill('#newName', 'Card game achievements')
    pg.click('#newNext'); pg.wait_for_timeout(400)
    ok('Next opens the picker with 12 live cards', pg.is_visible('.modal.panel') and pg.locator('.pick-card').count() == 12)
    ok('the worksite sits second, right after City hall', pg.text_content('.pick-card >> nth=1 >> .pick-name') == 'Worksite')
    pg.screenshot(path=str(SH / '71-picker.png'))
    pg.click('.pick-card >> text=Hangar'); pg.wait_for_timeout(300)
    ok('picking starts planting', pg.is_visible('#banner') and 'Card game achievements' in pg.text_content('#banner'))
    pg.evaluate("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(200)
    pos = pg.evaluate("() => MapView.plotCss(1, 3)")
    pg.mouse.move(left + pos[0], pos[1]); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SH / '72-aiming.png'))
    pg.mouse.click(left + pos[0], pos[1]); pg.wait_for_timeout(120)
    pg.screenshot(path=str(SH / '73-planting.png'))
    pg.wait_for_timeout(700)
    newp = pg.evaluate("() => DB.projects.find(p => p.name === 'Card game achievements')")
    ok('planted as a hangar on plot 1,3', newp and newp['generic'] == 'hangar' and newp['plot'] == {'u': 1, 'v': 3})
    ok('then the project view opens to plan it', pg.is_visible('#pv') and pg.is_visible('[data-sec="about"] .pv-done'))
    pg.click('[data-sec="about"] .pv-done'); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SH / '74-edit-building.png'))
    # change the building: click its picture
    pg.click('.pv-scene'); pg.wait_for_timeout(400)
    ok('the side panel marks the current building', pg.locator('#pvSide .pick-card.on').count() == 1 and 'Hangar' in pg.text_content('#pvSide .pick-card.on'))
    pg.click('#pvSide .pick-card >> text=Home'); pg.wait_for_timeout(300)
    ok('changing the building updates the project', pg.evaluate("() => DB.projects.find(p => p.name === 'Card game achievements').generic") == 'home')
    ok('the header follows', 'home' in (pg.get_attribute('.pv-scene', 'aria-label') or '').lower())
    # your own art wins, and switching back asks first
    pg.set_input_files('#pvSide input[type=file]', fixture('test-live.gif')); pg.wait_for_timeout(700)
    ok('uploaded art overrides the generic', 'your own art' in (pg.get_attribute('.pv-scene', 'aria-label') or ''))
    pg.click('#pvSide .pick-card >> text=Kiosk'); pg.wait_for_timeout(300)
    ok('switching from your art asks first', pg.is_visible('.backdrop.top') and 'kiosk' in pg.text_content('#cfTitle').lower())
    pg.click('.confirm-actions .btn-danger'); pg.wait_for_timeout(400)
    ok('then the kiosk replaces the art', pg.evaluate("() => { const p = DB.projects.find(p => p.name === 'Card game achievements'); return p.generic === 'kiosk' && !p.art.has; }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes the side panel first', not pg.is_visible('#pvSide') and pg.is_visible('#pv'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # Esc in the picker cancels a new project cleanly
    n0 = pg.evaluate("() => DB.projects.length")
    pg.click('#btnNew'); pg.fill('#newName', 'Never mind'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc in the picker creates nothing', pg.evaluate("() => DB.projects.length") == n0 and not pg.is_visible('#banner'))
    pg.reload(); pg.wait_for_timeout(800)
    ok('the building choice survives reload', pg.evaluate("() => DB.projects.find(p => p.name === 'Card game achievements').generic") == 'kiosk')
    pg.evaluate("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(SH / '75-city.png'))
    b.close()
print(errors or 'no console errors')
