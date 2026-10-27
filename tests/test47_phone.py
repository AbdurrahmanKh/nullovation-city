"""The city on a phone (0.1.74), from the phone report (docs/phone-report.md): the map's bar fits, toasts sit over it,
the project view's top fits, the Menu button covers neither the status card nor a speech bubble, the drawer covers the
bubbles, a double tap steps inside, the shortcut wheel stays on the screen, fields are 16 px on a touch screen, no words
for keys a phone has not got, a phone on its side gets the drawer, and a bubble that opens by itself waits while the
project view covers the map. A desktop window is checked to stay as it was."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY, SAMPLE

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

BOX = "(sel) => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height }; }"
BAR = """() => [...document.querySelectorAll('.map-tools > *')].map(e => { const r = e.getBoundingClientRect();
    return { id: e.id || e.className, l: Math.round(r.left), r: Math.round(r.right) }; })"""


def page(p, w, h, mobile=True):
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=3 if mobile else 1, is_mobile=mobile, has_touch=mobile)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(1800)
    pg.evaluate("() => { Light.setMode('day'); document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true); }")
    return b, ctx, pg


def middle(pg, pid):
    """Where a building's middle sits on the screen."""
    return pg.evaluate(f"""() => {{ const a = MapView.anchors('{pid}'), r = document.querySelector('#map').getBoundingClientRect();
        return {{ x: r.left + a.topX, y: r.top + (a.topY + a.baseY) / 2 }}; }}""")


with sync_playwright() as p:
    # ---------- a phone, 390 by 844 ----------
    b, ctx, pg = page(p, 390, 844)
    ev = pg.evaluate
    cdp = ctx.new_cdp_session(pg)
    gp = ev(f"() => DB.projects.find(p => p.name === {json.dumps(SAMPLE)}).id")
    ok('a phone matches the small screens: the side bar is a drawer, behind the Menu button', ev("() => narrowScreen()") and pg.is_visible('#menuToggle'))

    # the map's bar
    bar = ev(BAR)
    ok(f'the map\'s bar fits the screen: Traffic, Bubbles, Time of day, Postcard, Zoom and Settings all inside 390 px ({bar})',
       len(bar) == 6 and all(x['l'] >= 0 and x['r'] <= 390 for x in bar))
    lab = ev("() => ['#trafficLabel', '#bubblesLabel', '#lightLabel', '#btnPostcard .mt-label'].map(s => { const e = document.querySelector(s), r = e.getBoundingClientRect(); return { w: r.width, text: e.textContent }; })")
    ok('its buttons wear their icons only: the words are hidden from sight', all(x['w'] <= 1 for x in lab))
    ok('and kept for screen readers, as the button\'s own words', [x['text'] for x in lab][:2] == ['Traffic', 'Bubbles'] and
       ev("() => document.querySelector('#btnPostcard').textContent.trim()") == 'Postcard')
    pg.tap('#btnBubbles'); pg.wait_for_timeout(300)
    drop = ev("() => [...document.querySelectorAll('.dropup button')].map(b => { const r = b.getBoundingClientRect(); return { text: b.textContent.trim(), l: r.left, r: r.right, t: r.top }; })")
    ok('Bubbles opens its drop-up with each option\'s words, inside the screen', len(drop) == 4 and all(d['l'] >= 0 and d['r'] <= 390 and d['t'] >= 0 for d in drop)
       and drop[0]['text'] == 'Bubbles', drop)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # a toast sits over the bar
    ev("() => toast('Saved the city.')"); pg.wait_for_timeout(400)
    t, mt = ev(BOX, '#toast'), ev(BOX, '.map-tools')
    ok(f'a toast sits over the map\'s bar, not on it ({round(t["b"])} over {round(mt["t"])})', t['b'] <= mt['t'] - 4)
    pg.screenshot(path=str(SHOTS / '470-phone-map.png'))
    ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; }")

    # the Menu button covers neither a speech bubble nor the status card
    ev("() => Gus.say('The city is getting dirty! We should do something about it.')"); pg.wait_for_timeout(400)
    g, m = ev(BOX, '#gusSay'), ev(BOX, '#menuToggle')
    ok(f'a speech bubble opens under the Menu button, so the menu stays in reach ({round(g["t"])} under {round(m["b"])})', g['t'] >= m['b'] + 4)
    ok('across the screen, inside it, with no arrow pointing at a side bar that is not there',
       g['l'] >= 0 and g['r'] <= 390 and ev("() => getComputedStyle(document.querySelector('#gusSay'), '::before').display") == 'none')
    pg.screenshot(path=str(SHOTS / '471-phone-bubble.png'))

    # the drawer covers the bubbles
    pg.tap('#menuToggle'); pg.wait_for_timeout(400)
    top = ev("([x, y]) => { const e = document.elementFromPoint(x, y); return e && e.closest('#menu') ? 'menu' : e && e.closest('.gus-say') ? 'bubble' : (e ? e.tagName : null); }", [120, g['t'] + 40])
    ok('the drawer opens over a speech bubble, not under it', top == 'menu', top)
    pg.tap('#menuClose'); pg.wait_for_timeout(400)
    ev("() => Gus.hush()"); pg.wait_for_timeout(300)

    ev(f"""() => {{ const p = getProject('{gp}'); const w = MapView.anchors(p.id), c = MapView.camState();
        MapView.setCam({{ x: c.x, y: c.y + (w.topY - 30) / (c.z / c.dpr), z: c.z / c.dpr }}); }}""")
    pg.wait_for_timeout(200)
    ev(f"() => MapView.select('{gp}', {{ glide: false }})"); pg.wait_for_timeout(400)
    card, m = ev(BOX, '#bubble'), ev(BOX, '#menuToggle')
    raw = ev(f"() => {{ const a = MapView.anchors('{gp}'), r = document.querySelector('#map').getBoundingClientRect(); return r.top + a.topY - document.querySelector('#bubble').offsetHeight - 20; }}")
    ok(f'the status card of a building near the top stays under the Menu button, so its name shows ({round(card["t"])} under {round(m["b"])}, '
       f'where it would have been {round(raw)})', card['t'] >= m['b'] + 4 and raw < m['b'])
    ok('a status card on a phone has its Add a task field at 16 px, so an iPhone does not zoom in on a tap',
       ev("() => getComputedStyle(document.querySelector('#bAdd')).fontSize") == '16px')
    pg.screenshot(path=str(SHOTS / '472-phone-card.png'))
    ev("() => MapView.deselect()"); pg.wait_for_timeout(200)

    # a double tap steps inside; two taps apart only select
    ev("() => MapView.frameAll()"); pg.wait_for_timeout(500)
    c = middle(pg, gp)
    pg.touchscreen.tap(c['x'], c['y']); pg.wait_for_timeout(700)
    c = middle(pg, gp)                                   # the map glides the building into view for its card
    pg.touchscreen.tap(c['x'], c['y']); pg.wait_for_timeout(700)
    ok('two taps apart select the building and open its card, not the project view', ev("() => App.selectedId") == gp and not ev("() => FullView.isOpen()"))
    ev("() => MapView.deselect()"); pg.wait_for_timeout(300)
    ev("() => MapView.frameAll()"); pg.wait_for_timeout(500)
    c = middle(pg, gp)
    cdp.send('Input.synthesizeTapGesture', {'x': c['x'], 'y': c['y'], 'duration': 40, 'tapCount': 2, 'gestureSourceType': 'touch'})
    pg.wait_for_timeout(1000)
    ok('a double tap on a building steps inside it, as a double-click does', ev("() => FullView.isOpen()") and
       ev("() => document.querySelector('#pv .pv-title').textContent") == SAMPLE)

    # the project view's top fits
    over = ev("""() => { const v = document.querySelector('#pv'), W = v.getBoundingClientRect().right; const out = [];
        for (const e of v.querySelectorAll('.pv-hero *, .pv-under *, #pvLeader *')) { const r = e.getBoundingClientRect(); if (r.width && r.right > W + 1) out.push((e.id || e.className) + ' ' + Math.round(r.right)); }
        return { scroll: v.scrollWidth - v.clientWidth, out: out.slice(0, 6) }; }""")
    ok(f'the project view\'s top fits a phone: the picture, the leader card and the About end inside it ({over})', over['scroll'] <= 0 and not over['out'])
    pg.screenshot(path=str(SHOTS / '473-phone-project.png'))

    # the task panel: 16 px fields, and no words for Esc
    tid = ev(f"() => getProject('{gp}').todos.find(t => t.text === 'Add plant icons').id")
    ev(f"() => FullView.openTask('{gp}', '{tid}')"); pg.wait_for_timeout(600)
    sizes = ev("() => ['#pvTaskDesc', '#pvTaskDue'].map(s => getComputedStyle(document.querySelector(s)).fontSize)")
    ok(f'the task panel\'s description and due date are 16 px on a touch screen ({sizes})', sizes == ['16px', '16px'])
    ok('its title keeps its own bigger size', float(ev("() => getComputedStyle(document.querySelector('#pvTaskTitle')).fontSize")[:-2]) > 16)
    note = ev("() => { const n = [...document.querySelectorAll('#pvSide p.note')].pop(); return { seen: n.innerText.trim(), all: n.textContent.trim() }; }")
    ok(f'its foot says what a phone can do: "{note["seen"]}"', note['seen'] == 'Saves as you type. Done closes it.')
    ok('while its words for Esc stay in the page for a keyboard', note['all'] == 'Saves as you type. Done closes it; Esc undoes everything since it opened.')
    ev("() => FullView.close()"); pg.wait_for_timeout(300)

    # the one-line add has no line about keys
    ev("() => QuickAdd.open()"); pg.wait_for_timeout(300)
    ok('the one-line add over the map shows no line about Enter, Shift+Enter and Ctrl+Enter', not pg.is_visible('.quick-add-keys'))
    ok('its field stays 16 px, as the colors under it', ev("() => getComputedStyle(document.querySelector('.quick-add-in')).fontSize") == '16px')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    pg.tap('#menuToggle'); pg.wait_for_timeout(300)
    ok('search, in the drawer, is 16 px', ev("() => getComputedStyle(document.querySelector('#search')).fontSize") == '16px')
    pg.tap('#menuClose'); pg.wait_for_timeout(300)

    # the shortcut wheel stays on the screen
    ev(f"""() => {{ const p = getProject('{gp}');
        for (const [label, url] of [['Project folder on the server', 'https://example.com/a'], ['Claude project for the garden', 'https://claude.ai/project/x'],
          ['The beds sketch in Figma', 'https://figma.com/b'], ['Seed catalogue', 'https://example.com/c']])
          p.links.push({{ id: uid('l'), label, url, icon: 'web', shortcut: true }}); changed(p); }}""")
    ev("() => MapView.frameAll()"); pg.wait_for_timeout(500)
    c = middle(pg, gp)
    ev("([x, y]) => document.querySelector('#map').dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, clientX: x, clientY: y }))", [c['x'], c['y']])
    pg.wait_for_timeout(400)
    wh = ev("""() => ({ r: getComputedStyle(document.querySelector('.wheel')).getPropertyValue('--r').trim(),
        parts: [...document.querySelectorAll('.wheel > *')].map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)]; }) })""")
    ok(f'the shortcut wheel stays on the screen: every shortcut, the name and Enter inside 390 px ({wh["parts"]})', all(a >= 0 and z <= 390 for a, z in wh['parts']))
    ok(f'wider than the map, it stands on a smaller ring ({wh["r"]})', wh['r'] == '76px')
    pg.screenshot(path=str(SHOTS / '474-phone-wheel.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # a bubble that opens by itself waits while the project view covers the map
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    ok('with the project view over the whole map, there is no room beside it for a speech bubble', not ev("() => sayRoom()"))
    ev("() => { Celebrate._test.end(); Celebrate._test.forget(); Proxima.hush(false); Proxima._test.forget(); Proxima._test.sayMs(60000); }")
    ev(f"() => {{ const p = getProject('{gp}'); for (const t of p.todos.filter(t => t.milestoneId === 'm_first')) tickTask(p, t); changed(p); }}")
    pg.wait_for_timeout(900)
    ok('a finished milestone\'s party starts, while Proxima waits to say it rather than speak out of sight',
       ev("() => Celebrate._test.parties()") == [gp] and not ev("() => Proxima.isSaying()") and len(ev("() => Proxima._test.queue()")) == 1)
    ev("() => FullView.close()"); pg.wait_for_timeout(1000)
    px = ev(BOX, '#pxSay')
    ok('once the project view closes, she says it, under the Menu button', ev("() => Proxima.saying()") == 'milestone' and px and px['t'] >= ev(BOX, '#menuToggle')['b'])
    pg.screenshot(path=str(SHOTS / '475-phone-proxima.png'))
    b.close()

    # ---------- 0.1.75: The City on a Phone, Round 1 ----------
    b, ctx, pg = page(p, 390, 844)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    ev = pg.evaluate
    cdp = ctx.new_cdp_session(pg)
    gp = ev(f"() => DB.projects.find(p => p.name === {json.dumps(SAMPLE)}).id")
    guard = lambda: ev("() => !!(history.state && history.state.nc === 'back')")
    plot = lambda: ev(f"() => JSON.stringify(getProject('{gp}').plot)")
    ev("() => MapView.frameAll()"); pg.wait_for_timeout(500)

    # G1: a long press opens the wheel; nothing moves
    was, c = plot(), middle(pg, gp)
    cdp.send('Input.synthesizeTapGesture', {'x': c['x'], 'y': c['y'], 'duration': 900, 'tapCount': 1, 'gestureSourceType': 'touch'})
    pg.wait_for_timeout(700)
    ok('G1 a long press on a building opens its shortcut wheel', ev("() => Wheel.owner()") == gp)
    ok('the finger lifting leaves it open, and clicks nothing: no card opens', ev("() => Wheel.isOpen()") and not ev("() => App.selectedId"))
    ok('nothing is lifted or moved: the building stays on its plot', not ev("() => MapView.moving()") and plot() == was)
    pg.screenshot(path=str(SHOTS / '477-phone-hold-wheel.png'))

    # G2: back closes one layer at a time, keeping what was typed
    ok('G2 with the wheel open, one entry in the history stands guard for it', guard())
    pg.go_back(); pg.wait_for_timeout(400)
    ok('back closes the wheel, and the city stays', not ev("() => Wheel.isOpen()") and pg.url.startswith('file:') and not guard())
    c = middle(pg, gp)
    pg.touchscreen.tap(c['x'], c['y']); pg.wait_for_timeout(800)
    ok('a status card opened by a tap stands guard too', ev("() => App.selectedId") == gp and guard())
    pg.tap('#enterBtn'); pg.wait_for_timeout(800)
    tid = ev(f"() => getProject('{gp}').todos.find(t => t.text === 'Add plant icons').id")
    pg.evaluate(f"() => {{ const b = [...document.querySelectorAll('#pv li.task button.task-title')].find(x => x.textContent.includes('Add plant icons')); b.scrollIntoView({{ block: 'center' }}); }}")
    pg.locator('#pv li.task button.task-title', has_text='Add plant icons').tap(); pg.wait_for_timeout(600)
    pg.locator('#pvTaskDesc').tap(); pg.keyboard.type('Pixel icons for each plant.'); pg.wait_for_timeout(300)
    pg.go_back(); pg.wait_for_timeout(500)
    ok('back closes the task panel keeping what was typed, as Done does, not undoing it as Esc does',
       not pg.is_visible('#pvTaskDesc') and ev(f"() => getProject('{gp}').todos.find(t => t.id === '{tid}').description") == 'Pixel icons for each plant.')
    ok('the project view stays open, and still stands guard', ev("() => FullView.isOpen()") and guard())
    pg.go_back(); pg.wait_for_timeout(500)
    ok('back again closes the project view, back to its building\'s card', not ev("() => FullView.isOpen()") and ev("() => App.selectedId") == gp and guard())
    pg.go_back(); pg.wait_for_timeout(500)
    ok('and the card; on the bare map nothing stands guard, so the next back leaves the city, as before', not ev("() => App.selectedId") and not guard())
    pg.tap('#btnSettings'); pg.wait_for_timeout(500)
    ok('the gear opens Settings in the drawer, which stands guard', ev("() => Settings.isOpen()") and guard())
    pg.go_back(); pg.wait_for_timeout(400)
    ok('back takes Settings back to the side bar\'s lists, the drawer still open', not ev("() => Settings.isOpen()") and ev("() => document.querySelector('#menu').classList.contains('open')") and guard())
    pg.go_back(); pg.wait_for_timeout(400)
    ok('back again closes the drawer', not ev("() => document.querySelector('#menu').classList.contains('open')") and not guard())
    pg.tap('#menuToggle'); pg.wait_for_timeout(400); pg.tap('#menuClose'); pg.wait_for_timeout(400)
    ok('closed with its own button, the drawer takes its guard with it', not guard())

    # B2: bigger areas, the same look
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    hit = ev("""() => { const row = [...document.querySelectorAll('#pv li.task')].find(r => r.offsetParent && !r.classList.contains('done'));
        row.scrollIntoView({ block: 'center' });
        const pin = row.querySelector('.task-mark'), cb = row.querySelector('.cb');
        const at = (x, y) => document.elementFromPoint(x, y);
        const p = pin.getBoundingClientRect(), c = cb.getBoundingClientRect();
        return { pin: [Math.round(p.width), Math.round(p.height)], cb: [Math.round(c.width), Math.round(c.height)],
          pinOut: at(p.left + p.width / 2, p.top - 4) === pin, cbLeft: at(c.left - 6, c.top + c.height / 2) === cb,
          cbBelow: at(c.left + c.width / 2, c.bottom + 6) === cb, cbRight: at(c.right + 6, c.top + c.height / 2) !== cb }; }""")
    ok(f'B2 a pin answers a tap 4 px above it, at its own size ({hit["pin"]})', hit['pinOut'] and hit['pin'][0] <= 30)
    ok(f'a checkbox answers taps left of it and under it, at its own size ({hit["cb"]})', hit['cbLeft'] and hit['cbBelow'] and hit['cb'] == [18, 18])
    ok('and stops short of the task\'s name beside it', hit['cbRight'])
    dis = ev("""() => { const w = h('div', { class: 'news-face', style: 'position: fixed; z-index: 100; left: 100px; top: 300px; width: 48px; height: 48px' }),
        d = h('button', { class: 'icon-btn news-dismiss', type: 'button' }); w.append(d); document.body.append(w);
        const r = d.getBoundingClientRect(), at = (x, y) => document.elementFromPoint(x, y);
        const out = { upLeft: at(r.left - 5, r.top - 5) === d, intoFace: at(r.right + 4, r.bottom + 4) !== d }; w.remove(); return out; }""")
    ok(f'a news face\'s dismiss reaches out up and left, away from its face, not into it ({dis})', dis['upLeft'] and dis['intoFace'])
    ev("() => FullView.close()"); pg.wait_for_timeout(300)

    # B4: Open in Claude is Copy only
    ev(f"() => FullView.openTask('{gp}', '{tid}')"); pg.wait_for_timeout(600)
    pg.evaluate("() => { const b = [...document.querySelectorAll('#pvSide button')].find(x => /Open in Claude/.test(x.textContent)); b.scrollIntoView({ block: 'center' }); }")
    pg.locator('#pvSide button', has_text='Open in Claude').first.tap(); pg.wait_for_timeout(400)
    oc = ev("() => ({ kinds: [...document.querySelectorAll('.oc-panel [data-kind]')].map(e => e.dataset.kind), tabs: document.querySelectorAll('.oc-panel .oc-tab').length, folder: !!document.querySelector('.oc-panel .oc-folder'), label: (document.querySelector('.oc-panel [data-kind=copy]') || {}).textContent })")
    ok(f'B4 on a phone Open in Claude offers Copy alone, no Chat, Cowork, Code or Terminal, and no folder ({oc})', oc['kinds'] == ['copy'] and not oc['folder'] and oc['label'] == 'Copy')
    ok('a task keeps Build it and Think, which say what Copy copies', oc['tabs'] == 2)
    pg.screenshot(path=str(SHOTS / '478-phone-open-in-claude.png'))
    pg.tap('.oc-panel [data-kind=copy]'); pg.wait_for_timeout(400)
    ok('Copy copies the task, with its toast', 'Task copied for Claude.' in pg.text_content('#toast') and '# Task: Add plant icons' in ev("() => navigator.clipboard.readText()"))
    ev("() => FullView.close()"); pg.wait_for_timeout(300)

    # L2: the speech bubbles' face is 64 px on a phone, the words beside it
    ev("() => Gus.say('The city is getting dirty! We should do something about it.')"); pg.wait_for_timeout(400)
    sq = ev("""() => { const b = document.querySelector('#gusSay'), f = b.querySelector('.gus-face').getBoundingClientRect(), t = document.querySelector('#gusSayText').getBoundingClientRect();
        return { face: Math.round(f.width), beside: t.left >= f.right, narrow: b.classList.contains('narrow') }; }""")
    ok(f'L2 a speech bubble\'s face is 64 px on a phone, with the words beside it ({sq})', sq['face'] == 64 and sq['beside'] and not sq['narrow'])
    ok('and a leader\'s face in its bubble is drawn at 64 px there', ev("() => sayFace()") == 64)
    pg.screenshot(path=str(SHOTS / '479-phone-bubble-64.png'))
    ev("() => Gus.hush()"); pg.wait_for_timeout(300)

    # S1: the phone's own guide; S2: the zoom in screen pixels
    pg.tap('#btnSettings'); pg.wait_for_timeout(400); pg.tap('#setHelpBtn'); pg.wait_for_timeout(200)
    seen = pg.inner_text('#setHelp')
    ok(f'S1 the ? shows the phone\'s own guide: hold for shortcuts, double tap to step inside, back', 'Hold a building' in seen and 'Double tap a building' in seen
       and 'Closes one layer at a time' in seen and 'Pinch' in seen)
    ok('and none of the keys', 'WASD' not in seen and 'comma' not in seen)
    pg.screenshot(path=str(SHOTS / '480-phone-guide.png'))
    pg.tap('#setHelpBtn'); pg.wait_for_timeout(100)
    pg.tap('#menuClose'); pg.wait_for_timeout(300)
    ev("() => MapView.frameAll()"); pg.wait_for_timeout(500)
    z = ev("() => ({ label: document.querySelector('#zoomLevel').textContent, z: MapView.camState().z })")
    ok(f'S2 the zoom counts screen pixels on a phone, in whole numbers ({z})', z['label'] == str(z['z']) + 'x')
    pg.tap('#zoomIn'); pg.wait_for_timeout(500)
    z2 = ev("() => ({ label: document.querySelector('#zoomLevel').textContent, z: MapView.camState().z })")
    ok(f'and steps in them ({z2})', z2['label'] == str(z2['z']) + 'x' and z2['z'] > z['z'])
    b.close()

    # ---------- a small phone, 360 by 740 ----------
    b, ctx, pg = page(p, 360, 740)
    bar = pg.evaluate(BAR)
    ok(f'on a small phone the bar fits too, inside 360 px ({bar})', all(x['l'] >= 0 and x['r'] <= 360 for x in bar))
    b.close()

    # ---------- a phone on its side, 844 by 390 ----------
    b, ctx, pg = page(p, 844, 390)
    ok('a phone on its side gets the drawer too: the Menu button shows and the side bar is out of the way',
       pg.evaluate("() => narrowScreen()") and pg.is_visible('#menuToggle') and pg.evaluate(BOX, '#menu')['r'] <= 0)
    ok('so the map has the whole width', round(pg.evaluate(BOX, '#mapWrap')['w']) == 844)
    pg.tap('#menuToggle'); pg.wait_for_timeout(400)
    ok('the Menu button opens the drawer over the map', pg.evaluate(BOX, '#menu')['l'] >= 0 and pg.is_visible('#btnOpenSettings'))
    pg.screenshot(path=str(SHOTS / '476-phone-side.png'))
    pg.tap('#menuClose'); pg.wait_for_timeout(300)
    pg.evaluate("() => Gus.say('Clean streets. Don\\'t get used to it.')"); pg.wait_for_timeout(400)
    ok('a speech bubble keeps its 400 px at most, under the Menu button', pg.evaluate(BOX, '#gusSay')['w'] <= 401 and pg.evaluate(BOX, '#gusSay')['t'] >= pg.evaluate(BOX, '#menuToggle')['b'])
    b.close()

    # ---------- a desktop window stays as it was ----------
    b, ctx, pg = page(p, 1440, 900, mobile=False)
    ok('a desktop window is not a small screen: the side bar stays docked', not pg.evaluate("() => narrowScreen()") and not pg.is_visible('#menuToggle'))
    ok('the bar\'s buttons keep their words', pg.evaluate("() => document.querySelector('#trafficLabel').getBoundingClientRect().width") > 20)
    ok('fields keep their 15 px', pg.evaluate("() => getComputedStyle(document.querySelector('#search')).fontSize") == '15px')
    pg.evaluate("() => Gus.say('The city is getting dirty! We should do something about it.')"); pg.wait_for_timeout(400)
    g, w = pg.evaluate(BOX, '#gusSay'), pg.evaluate(BOX, '#mapWrap')
    ok('a speech bubble keeps its place at the map\'s top left, by the side bar', round(g['l'] - w['l']) == 22 and round(g['t'] - w['t']) == 18)
    ok('and its 100 px face', round(pg.evaluate(BOX, '#gusSay .gus-face')['w']) == 100 and pg.evaluate("() => sayFace()") == 100)
    pg.evaluate("() => Gus.hush()"); pg.wait_for_timeout(300)
    pg.evaluate("() => Settings.open('city')"); pg.click('#setHelpBtn'); pg.wait_for_timeout(150)
    seen = pg.inner_text('#setHelp')
    ok('the ? shows the keys, and not the phone\'s guide', 'WASD' in seen and 'Hold a building' not in seen)
    pg.click('#setHelpBtn'); pg.evaluate("() => Settings.close()"); pg.wait_for_timeout(150)
    z = pg.evaluate("() => ({ label: document.querySelector('#zoomLevel').textContent, z: MapView.camState().z })")
    ok(f'the zoom reads as before ({z})', z['label'] == str(z['z']) + 'x')
    a = pg.evaluate("() => { const p = DB.projects[0], a = MapView.anchors(p.id), r = document.querySelector('#map').getBoundingClientRect(); return { x: r.left + a.topX, y: r.top + (a.topY + a.baseY) / 2, id: p.id }; }")
    pg.mouse.click(a['x'], a['y']); pg.wait_for_timeout(500)
    ok('a click opening a card leaves the history alone: back is the browser\'s own', pg.evaluate("() => App.selectedId") == a['id'] and pg.evaluate("() => history.state") is None)
    pg.evaluate("() => MapView.deselect()")
    gp = pg.evaluate(f"() => DB.projects.find(p => p.name === {json.dumps(SAMPLE)}).id")
    pg.evaluate(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
    ok('beside the project view there is room for a bubble, as before', pg.evaluate("() => sayRoom()"))
    ok('the task panel\'s foot names Esc', 'Esc undoes' in pg.evaluate("() => { const t = getProject('" + gp + "').todos[0]; FullView.openTask('" + gp + "', t.id); return [...document.querySelectorAll('#pvSide p.note')].pop().innerText; }"))
    b.close()

print('\n'.join(errors) if errors else 'no console errors')
