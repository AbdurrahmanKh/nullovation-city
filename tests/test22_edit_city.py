"""Edit City: lines and rings added or taken off on any side keep the parks, street marks and props with their
buildings; the city can be a rectangle, 5 to 11 plots each way; parks picked in Edit City stay with their plot."""
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# Everything dealt by place, read by the city's plot (U, V) = (u + OU, v + OV): parks, props, crossing marks, the
# buildings' plots, and the ground's pixels round every plot that is not on the map's edge.
SNAP = """() => { const W = WORLD, out = { parks: {}, props: [], marks: {}, plots: {}, ground: {} };
  for (let u = 0; u < W.NU; u++) for (let v = 0; v < W.NV; v++) {
    const U = u + W.OU, V = v + W.OV, info = MapView.lotInfo(u, v);
    out.parks[U + ',' + V] = info.id + (info.flip ? ':f' : '');
    if (u > 0 && v > 0 && u < W.NU - 1 && v < W.NV - 1) out.ground[U + ',' + V] = MapView._groundHash(u, v, -80, -10, 160, 84);
  }
  out.props = MapView.props().map(q => [q.kind, q.u + W.OU, q.v + W.OV, q.side, q.a.toFixed(5)].join()).sort();
  for (let li = 0; li < W.NU; li++) for (let ri = 1; ri < W.NV; ri++) for (const e of [0, 1]) out.marks['i' + (li + W.OU) + ',' + (ri + W.OV) + ',' + e] = MapView.crossMark(li, ri, true, e);
  for (let li = 0; li < W.NV; li++) for (let ri = 1; ri < W.NU; ri++) for (const e of [0, 1]) out.marks['j' + (li + W.OV) + ',' + (ri + W.OU) + ',' + e] = MapView.crossMark(li, ri, false, e);
  for (const p of DB.projects) out.plots[p.name] = (p.plot.u + W.OU) + ',' + (p.plot.v + W.OV);
  return out; }"""

def kept(a, b):
    """What both snapshots share, and what differs there: parks, crossing marks and ground by place; props by the
    blocks both hold; the buildings' plots in the city."""
    bad = []
    for part in ('parks', 'marks', 'ground'):
        for k in set(a[part]) & set(b[part]):
            if a[part][k] != b[part][k]: bad.append((part, k, a[part][k], b[part][k]))
    blocks = set(a['parks']) & set(b['parks'])
    pa = sorted(x for x in a['props'] if ','.join(x.split(',')[1:3]) in blocks)
    pb = sorted(x for x in b['props'] if ','.join(x.split(',')[1:3]) in blocks)
    if pa != pb: bad.append(('props', len(pa), len(pb)))
    if a['plots'] != b['plots']: bad.append(('plots', a['plots'], b['plots']))
    return bad

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); localStorage.setItem('nullovation-city:traffic', '0'); } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof LOTS !== 'undefined' && LOTS.every(l => Art.get('lot:' + l.id))", timeout=20000)
    js = pg.evaluate

    ok('the city keeps its map as version 3: 5 by 5 plots at the city\'s origin',
       js("() => DB.version === 3 && JSON.stringify(DB.world) === JSON.stringify({ nu: 5, nv: 5, ou: 0, ov: 0 })"))
    base = js(SNAP)
    ok(f'the snapshot reads every park, prop, mark and building ({len(base["parks"])} parks, {len(base["props"])} props, {len(base["marks"])} marks)',
       len(base['parks']) == 25 and len(base['props']) > 30 and len(base['marks']) == 80 and len(base['ground']) == 9)

    # a line on each side, then off again; a ring, then off again
    anchor = lambda: js("() => MapView.anchors(DB.projects[0].id)")
    for side, label in (('nw', 'north-west'), ('ne', 'north-east'), ('se', 'south-east'), ('sw', 'south-west')):
        a0 = anchor()
        added = js(f"() => MapView.addLine('{side}', 1)")
        snap = js(SNAP); a1 = anchor()
        size = js("() => [WORLD.NU, WORLD.NV]")
        bad = kept(base, snap)
        ok(f'a line on the {label} side makes {size[0]} by {size[1]}, and keeps every park, mark, prop and building in place ({bad[:2] or "all kept"})',
           added and sorted(size) == [5, 6] and not bad and len(snap['parks']) == 30)
        ok(f'and the view stays on the same buildings ({a0["baseX"]:.0f},{a0["baseY"]:.0f} and {a1["baseX"]:.0f},{a1["baseY"]:.0f})',
           abs(a0['baseX'] - a1['baseX']) < 1 and abs(a0['baseY'] - a1['baseY']) < 1)
        js(f"() => MapView.addLine('{side}', -1)")
        back = js(SNAP)
        ok(f'taking it off again brings the city back exactly ({kept(base, back)[:2] or "the same"})', back == base)
    js("() => MapView.resizeWorld(1)")
    ring = js(SNAP)
    ok(f'a ring makes 7 by 7 and keeps everything in place ({kept(base, ring)[:2] or "all kept"})',
       js("() => WORLD.NU === 7 && WORLD.NV === 7 && WORLD.OU === -1 && WORLD.OV === -1") and not kept(base, ring))
    ok('the old ring road\'s inner plots now show their own ground, and the parks round them still differ from their neighbours',
       len(ring['ground']) == 25 and all(ring['parks'][f'{u},{v}'].split(':')[0] != ring['parks'][f'{u + 1},{v}'].split(':')[0] for u in range(-1, 5) for v in range(-1, 6)))
    js("() => MapView.resizeWorld(-1)")
    ok('taking the ring off again brings the city back exactly', js(SNAP) == base)

    # a rectangle: lines on one side, up to 11 and down to 5; a line with a building on it stays
    for k in range(6): js("() => MapView.addLine('se', 1)")
    ok('lines on one side make the city a rectangle, up to 11 plots that way', js("() => WORLD.NU === 11 && WORLD.NV === 5 && !MapView.canLine('se', 1) && !MapView.canLine('nw', 1) && MapView.canLine('ne', 1)"))
    ok('a ring does not fit once a side is at 11', js("() => !MapView.canResize(1) && !MapView.resizeWorld(1)"))
    st = js("() => { Traffic.reset(); return Traffic.stats(); }")
    ok(f'the traffic scales with the rectangle\'s area, 11 by 5 ({st})', st['cars'] + st['buses'] + st['drones'] == round(16 * 55 / 25) and st['bikes'] == round(2 * 55 / 25))
    for k in range(6): js("() => MapView.addLine('se', -1)")
    ok('lines come off again down to 5, and no further', js("() => WORLD.NU === 5 && !MapView.canLine('se', -1) && !MapView.addLine('se', -1)"))
    js("() => { DB.projects[0].plot = { u: 4, v: 2 }; MapView.addLine('se', 1); }")
    ok('a line with a building on it stays: only empty lines come off', js("() => !MapView.lineEmpty('se') || WORLD.NU === 6") and js("() => { DB.projects[0].plot = { u: 5, v: 2 }; return !MapView.canLine('se', -1) && !MapView.addLine('se', -1) && WORLD.NU === 6; }"))
    js("() => { DB.projects[0].plot = { u: 2, v: 2 }; MapView.addLine('se', -1); persistNow(); }")
    ok('the map is back to 5 by 5', js("() => WORLD.NU === 5 && WORLD.NV === 5 && WORLD.OU === 0 && WORLD.OV === 0"))

    # a park picked in Edit City is kept by its plot in the city
    pick = js("""() => { const u = 0, v = 4, was = MapView.lotInfo(u, v).id, next = LOTS[(LOTS.findIndex(l => l.id === was) + 1) % LOTS.length].id;
      DB.city.parks[(u + WORLD.OU) + ',' + (v + WORLD.OV)] = next; MapView.invalidate(); return { was, next }; }""")
    ok(f'a picked park shows its kind ({pick["was"]} to {pick["next"]})', js("() => MapView.lotInfo(0, 4).id") == pick['next'])
    js("() => MapView.addLine('nw', 1)")
    ok('and keeps it when a line moves the grid', js("() => MapView.lotInfo(1, 4).id") == pick['next'])
    js("() => MapView.addLine('nw', -1)")
    pg.reload(); pg.wait_for_function("() => typeof LOTS !== 'undefined'", timeout=20000)
    ok('the pick is kept after a reload, with the city', js("() => MapView.lotInfo(0, 4).id") == pick['next'] and js("() => Object.keys(DB.city.parks).length") == 1)
    js("() => { DB.city.parks = {}; persistNow(); MapView.invalidate(); }")

    # ---------- Edit City itself, opened from Settings, City ----------
    left = js("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    shown = lambda: sorted(js("() => [...document.querySelectorAll('#editArrows .edit-arrow')].filter(b => !b.hidden).map(b => b.closest('.edit-side').dataset.side + ':' + b.dataset.dir)"))
    js("() => MapView.setCam({ x: 0, y: 260, z: 3 })")
    open_settings(pg, 'city')
    pg.click('#btnEditCity'); pg.wait_for_timeout(300)
    ok('Edit City opens from the City tab: its bar shows the size, Grow, Shrink and Done', pg.is_visible('#editBar') and pg.text_content('#editSize') == '5 by 5 plots'
       and all(pg.is_visible(s) for s in ('#btnGrow', '#btnShrink', '#btnEditDone')) and pg.text_content('#btnEditCity') == 'Done editing')
    ok(f'on a 5 by 5 city each side has an arrow out and no arrow in ({shown()})', shown() == sorted(f'{s}:out' for s in ('ne', 'nw', 'se', 'sw')))
    in_view = lambda: js("""() => { const W = document.querySelector('#mapWrap').getBoundingClientRect();
      return [...document.querySelectorAll('#editArrows .edit-arrow')].filter(b => !b.hidden).every(b => { const r = b.getBoundingClientRect();
        return r.left >= W.left && r.right <= W.right && r.top >= W.top && r.bottom <= W.bottom; }); }""")
    ok('it frames the whole city, all four arrows in view', in_view())
    ok('Shrink waits at 5 by 5', pg.is_disabled('#btnShrink') and not pg.is_disabled('#btnGrow'))
    pg.screenshot(path=str(SH / '220-edit-city.png'))
    pg.click('.edit-side[data-side="nw"] [data-dir="out"]'); pg.wait_for_timeout(250)
    ok('the north-west arrow out adds a line on that side', js("() => [WORLD.NU, WORLD.NV, WORLD.OU, WORLD.OV]") == [6, 5, -1, 0] and pg.text_content('#editSize') == '6 by 5 plots' and pg.text_content('#mapSize') == '6 by 5 plots')
    ok(f'and the arrows in show on both ends of that way, their lines being empty ({shown()})', shown() == sorted(['ne:out', 'nw:out', 'se:out', 'sw:out', 'nw:in', 'se:in']))
    pg.click('.edit-side[data-side="se"] [data-dir="out"]'); pg.wait_for_timeout(250)
    ok('the south-east arrow out adds one on the other end: 7 by 5', js("() => [WORLD.NU, WORLD.NV, WORLD.OU]") == [7, 5, -1] and in_view())
    pg.screenshot(path=str(SH / '221-edit-city-rectangle.png'))
    # a park: a click deals its next kind, and the pointer names it
    u, v = 6, 0
    def plot_xy(u, v):
        x, y = js(f"() => MapView.plotCss({u}, {v})")
        return left + x, y + 4
    was = js(f"() => MapView.lotInfo({u}, {v}).id")
    x, y = plot_xy(u, v)
    pg.mouse.move(x, y); pg.wait_for_timeout(150)
    tip = pg.text_content('#tip') if pg.is_visible('#tip') else ''
    pg.mouse.click(x, y); pg.wait_for_timeout(200)
    now = js(f"() => MapView.lotInfo({u}, {v}).id")
    order = js("() => LOTS.map(l => l.id)")
    ok(f'pointing at a park names its kind ({tip})', tip.lower().startswith(was.replace('-', ' ')) and 'next kind' in tip)
    ok(f'a click on a park deals the next kind ({was} to {now}), kept with the city', now == order[(order.index(was) + 1) % len(order)] and js(f"() => DB.city.parks[({u} + WORLD.OU) + ',' + ({v} + WORLD.OV)]") == now)
    pg.screenshot(path=str(SH / '222-edit-city-park.png'))
    for k in range(len(order) - 1):
        pg.mouse.click(x, y); pg.wait_for_timeout(120)
    ok('round all seven kinds, back at the one its place deals, and the pick is dropped', js(f"() => MapView.lotInfo({u}, {v}).id") == was and js("() => Object.keys(DB.city.parks).length") == 0)
    # a building: a click does nothing, a plain drag moves it
    gid = js("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    a = js(f"() => MapView.anchors('{gid}')")
    bx, by = left + a['baseX'], a['baseY'] - 30
    pg.mouse.click(bx, by); pg.wait_for_timeout(300)
    ok('a click on a building does nothing in Edit City: no status bubble', js("() => App.selectedId") is None and not pg.is_visible('#bubble'))
    start = js(f"() => DB.projects.find(p => p.id === '{gid}').plot")
    sx, sy = js(f"() => MapView.plotCss({start['u']}, {start['v']})")
    tx, ty = js(f"() => MapView.plotCss({start['u'] + 1}, {start['v'] + 2})")
    pg.mouse.move(bx, by); pg.mouse.down(); pg.mouse.move(bx + 8, by + 4, steps=2)
    pg.mouse.move(bx + (tx - sx), by + (ty - sy), steps=6); pg.wait_for_timeout(100)
    ok('a plain drag picks it up at once, with no hold', js("() => MapView.moving()"))
    pg.screenshot(path=str(SH / '223-edit-city-drag.png'))
    pg.mouse.up(); pg.wait_for_timeout(250)
    ok('and sets it down on the plot it is dropped on', js(f"() => DB.projects.find(p => p.id === '{gid}').plot") == {'u': start['u'] + 1, 'v': start['v'] + 2})
    ok('Q and E do not hop between buildings in Edit City', (pg.keyboard.press('e'), pg.wait_for_timeout(300), js("() => App.selectedId"))[2] is None)
    # the ring, as before, on the rectangle
    pg.click('#btnGrow'); pg.wait_for_timeout(250)
    ok('Grow adds a ring round the rectangle: 9 by 7', js("() => [WORLD.NU, WORLD.NV]") == [9, 7] and pg.text_content('#editSize') == '9 by 7 plots')
    pg.click('#btnShrink'); pg.wait_for_timeout(250)
    ok('Shrink takes it off again', js("() => [WORLD.NU, WORLD.NV]") == [7, 5])
    js("() => { while (MapView.addLine('se', 1)); while (MapView.addLine('sw', 1)); }"); pg.wait_for_timeout(300)
    ok(f'on an 11 by 11 city, bigger than the view, every arrow stays in reach ({shown()})', js("() => [WORLD.NU, WORLD.NV]") == [11, 11] and in_view()
       and shown() == sorted(['ne:in', 'nw:in', 'se:in', 'sw:in']))
    pg.screenshot(path=str(SH / '224-edit-city-11.png'))
    js("() => { while (MapView.addLine('sw', -1)); while (WORLD.NU > 7 && MapView.addLine('se', -1)); }")
    ok('and back to 7 by 5', js("() => [WORLD.NU, WORLD.NV]") == [7, 5])
    # Esc leaves Edit City first, then closes Settings; closing Settings ends Edit City too
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc leaves Edit City, and Settings stays open', not js("() => MapView.editing()") and not pg.is_visible('#editBar') and not pg.is_visible('#editArrows') and pg.is_visible('#settings'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('a second Esc closes Settings', not pg.is_visible('#settings'))
    open_settings(pg, 'city'); pg.click('#btnEditCity'); pg.wait_for_timeout(200)
    pg.click('#setBack'); pg.wait_for_timeout(200)
    ok('closing Settings ends Edit City', not js("() => MapView.editing()") and not pg.is_visible('#editBar'))
    open_settings(pg, 'city'); pg.click('#btnEditCity'); pg.wait_for_timeout(200)
    pg.click('#btnEditDone'); pg.wait_for_timeout(200)
    ok('Done ends it too', not js("() => MapView.editing()") and pg.text_content('#btnEditCity') == 'Edit City')
    # outside Edit City, a quick drag on a building still pans, and a hold then a drag moves it
    a = js(f"() => MapView.anchors('{gid}')"); bx, by = left + a['baseX'], a['baseY'] - 30
    cam0 = js("() => MapView.camState()"); plot0 = js(f"() => DB.projects.find(p => p.id === '{gid}').plot")
    pg.mouse.move(bx, by); pg.mouse.down(); pg.mouse.move(bx + 60, by + 20, steps=4); pg.mouse.up(); pg.wait_for_timeout(200)
    ok('outside Edit City a quick drag on a building pans the map', js("() => MapView.camState()")['x'] != cam0['x'] and js(f"() => DB.projects.find(p => p.id === '{gid}').plot") == plot0)
    js("() => { for (const s of ['nw', 'se']) MapView.addLine(s, -1); }")
    ok('the lines come off again: 5 by 5 at the city\'s origin', js("() => [WORLD.NU, WORLD.NV, WORLD.OU, WORLD.OV]") == [5, 5, 0, 0])
    # planting a project ends Edit City
    open_settings(pg, 'city'); pg.click('#btnEditCity'); pg.wait_for_timeout(200)
    js("() => MapView.startPlace('A new one', null)"); pg.wait_for_timeout(200)
    ok('planting a project ends Edit City', not js("() => MapView.editing()") and pg.is_visible('#banner'))
    pg.keyboard.press('Escape')
    b.close()
print(errors or 'no console errors')
