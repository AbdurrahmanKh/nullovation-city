"""Celebrations (Celebrations, Rounds 1 and 2): every tick sets off its building's particles (T1), in a kind picked in
the Building panel (T2), stars until then (T3); a milestone of 2 tasks or more (S1) throws a 30 second street party
(S2): particles all party long, party lights over its streets, a crowd dancing round the block, six party drones and a
bus that pulls up to watch; Proxima Pace announces it with Go to it, in one of her two approved lines."""
import io, json
from PIL import Image
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

KINDS = [['stars', 'Stars'], ['binary', 'Binary 0 and 1'], ['gold-binary', 'Gold 0 and 1'], ['dollars', 'Dollar signs'],
         ['lightning', 'Lightning'], ['sparkles', 'Wizard sparkles'], ['hearts', 'Hearts'], ['leaves', 'Leaves'], ['buttons', 'Game buttons'],
         ['bubbles', 'Speech bubbles'], ['coins', 'Coins'], ['confetti', 'Confetti']]
LINES = ["Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!",
         "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!"]

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    P = lambda pid: f"getProject('{pid}')"
    T = lambda pid, text: f"getProject('{pid}').todos.find(t => t.text === {json.dumps(text)})"
    tick = lambda pid, text: ev(f"() => {{ const p = {P(pid)}; tickTask(p, {T(pid, text)}); changed(p); }}")
    untick = lambda pid, text: ev(f"() => {{ const p = {P(pid)}; untickTask(p, {T(pid, text)}); changed(p); }}")
    bursts = lambda: ev("() => Celebrate._test.bursts()")
    parties = lambda: ev("() => Celebrate._test.parties()")
    def reopen_all(pid):
        ev(f"() => {{ const p = {P(pid)}; for (const t of p.todos) {{ t.done = false; t.doneAt = null; }} changed(p); }}")
    def calm():
        """Ends every burst and party, and forgets the day's parties, so a check starts clean."""
        ev("() => { Celebrate._test.end(); Celebrate._test.forget(); Proxima.hush(false); Proxima._test.forget(); }")
        pg.wait_for_timeout(1900)
    def center(pid, z=4):
        ev(f"() => MapView.setCam({{ x: 0, y: 0, z: {z} }})"); pg.wait_for_timeout(80)
        for _ in range(3):
            a = ev(f"() => MapView.anchors('{pid}')"); c = ev("() => MapView.camState()")
            w = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().width")
            ev(f"() => MapView.setCam({{ x: {c['x']} + ({a['topX']} - {w} / 2) / {z}, y: {c['y']} + (({a['topY']} + {a['baseY']}) / 2 - 450) / {z}, z: {z} }})")
            pg.wait_for_timeout(80)
    def shot_count(png, hexc):
        rgb = tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))
        return sum(1 for px in Image.open(io.BytesIO(png)).convert('RGB').getdata() if px == rgb)
    def count(pid, hexc):
        """Pixels of one exact color on the map round a building, read from a screenshot."""
        a = ev(f"() => MapView.anchors('{pid}')"); r = ev("() => { const b = document.querySelector('#mapWrap').getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; }")
        x0, y0 = max(0, a['topX'] - 260), max(0, a['topY'] - 200)
        clip = {'x': r['x'] + x0, 'y': r['y'] + y0, 'width': min(520, r['w'] - x0), 'height': min(a['baseY'] - a['topY'] + 300, r['h'] - y0)}
        return shot_count(pg.screenshot(clip=clip), hexc)
    ev("() => { Light.setMode('day'); MapView.setBubbleMode('none'); }")

    # ---------- the kinds (T2) and what every building starts on (T3) ----------
    ok('T2 twelve kinds: your four, gold 0 and 1 for keys, and the suggestions kept, with their names', ev("() => PARTICLE_KINDS") == KINDS)
    ok('T2 every kind has its art', sorted(ev("() => Celebrate._test.defs()")) == sorted(k for k, _ in KINDS))
    ok('T3 every building starts on stars', ev("() => DB.projects.map(p => p.particles)") == ['stars', 'stars'])
    ok('T3 a new project starts on stars', ev("() => blankProject().particles") == 'stars')
    ok('a kind the city does not have reads as stars, a known one is kept',
       ev("() => sanitizeProjects([{ name: 'A', particles: 'fireworks' }, { name: 'B', particles: 'coins' }]).map(x => (x.p || x).particles)") == ['stars', 'coins'])
    outlined = ev("""() => PARTICLE_IDS.every(id => { const s = Celebrate.sprite(id, 0), d = s.c.getContext('2d').getImageData(0, 0, s.w, s.h).data;
      let ink = 0, other = 0; for (let k = 0; k < d.length; k += 4) if (d[k + 3]) { if (d[k] === 43 && d[k + 1] === 37 && d[k + 2] === 66) ink++; else other++; } return ink > 0 && other > 0; })""")
    ok('every kind is drawn in its colors with the city\'s 1 px dark outline', outlined)
    ok('particles are about the size of the people: at most 9 px tall with the outline',
       ev("() => PARTICLE_IDS.every(id => Celebrate.sprite(id, 0).h <= 9)"))

    # ---------- a tick bursts (T1) ----------
    center(gp)
    gold0 = count(gp, '#F2C75C')
    tick(gp, 'Draw the beds on a grid')
    bs = bursts()
    ok('T1 a tick sets off a burst at its own building, of 16 particles', len(bs) == 1 and bs[0]['pid'] == gp and bs[0]['n'] == 16)
    pg.wait_for_timeout(450)
    ok('the burst shows on the map round the building, in its colors (stars: gold)', count(gp, '#F2C75C') >= gold0 + 20)
    pg.wait_for_timeout(1500)
    ok('the burst is over after 1.5 seconds', bursts() == [])
    tick(gp, 'Save a plan as a file'); tick(gp, 'Add plant icons')
    ok('T1 every tick bursts: two ticks, two bursts', len(bursts()) == 2)
    pg.wait_for_timeout(1700)
    untick(gp, 'Add plant icons')
    ok('unticking plays nothing', bursts() == [])
    pink0 = count(gp, '#EE4C93')
    ev(f"() => {{ {P(gp)}.particles = 'hearts'; }}")
    tick(gp, 'Add plant icons'); pg.wait_for_timeout(450)
    ok('the building\'s own kind bursts: hearts in neon pink', count(gp, '#EE4C93') >= pink0 + 20)
    pg.screenshot(path=str(SHOTS / '310-burst.png'))
    pg.wait_for_timeout(1500)
    ev("() => Light.setMode('night')"); pg.wait_for_timeout(500)
    pink0 = count(gp, '#EE4C93')
    untick(gp, 'Add plant icons'); tick(gp, 'Add plant icons'); pg.wait_for_timeout(450)
    ok('particles keep their colors at night, like the neon', count(gp, '#EE4C93') >= pink0 + 20)
    pg.wait_for_timeout(1500)
    ev("() => Light.setMode('day')"); pg.wait_for_timeout(400)
    ev("() => Motion.set('still')"); pg.wait_for_timeout(200)
    untick(gp, 'Add plant icons'); tick(gp, 'Add plant icons')
    ok('Motion on Still shows none of it', bursts() == [])
    ev("() => Motion.set('full')")
    reopen_all(gp); calm()

    # ticks from the status card and the project view count as any tick does
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(500)
    pg.locator('#bubble input.cb').first.check(); pg.wait_for_timeout(100)
    ok('a tick in the status card bursts', [x['pid'] for x in bursts()] == [gp])
    pg.wait_for_timeout(1700)
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.locator('#pv input.cb:not(:checked)').first.click(); pg.wait_for_timeout(100)
    ok('a tick in the project view bursts', [x['pid'] for x in bursts()] == [gp])
    pg.wait_for_timeout(300)
    shown = shot_count(pg.locator('#pv .pv-scene canvas').screenshot(), '#EE4C93')
    ok('it plays in the project view\'s picture of the building too', shown >= 20)
    pg.wait_for_timeout(1700)

    # ---------- the picker in the Building panel (T2) ----------
    pg.click('#pv .pv-scene'); pg.wait_for_timeout(400)
    tiles = pg.locator('.pv-particles .pick-particle')
    ok('the Building panel has Particles, with a tile per kind in order', tiles.count() == 12 and
       [tiles.nth(k).get_attribute('data-kind') for k in range(12)] == [k for k, _ in KINDS] and pg.locator('.pv-side h3', has_text='Particles').count() == 1)
    ok('each tile names its kind', [tiles.nth(k).inner_text().strip() for k in range(12)] == [n for _, n in KINDS])
    ok('the kind in use is pressed, and only it', pg.locator('.pick-particle[aria-pressed="true"]').count() == 1 and
       pg.locator('.pick-particle[aria-pressed="true"]').get_attribute('data-kind') == 'hearts')
    still_px = ev("() => document.querySelector('.pick-particle[data-kind=\"coins\"] canvas').toDataURL()")
    pg.hover('.pick-particle[data-kind="coins"]'); pg.wait_for_timeout(300)
    a = ev("() => document.querySelector('.pick-particle[data-kind=\"coins\"] canvas').toDataURL()"); pg.wait_for_timeout(250)
    b2 = ev("() => document.querySelector('.pick-particle[data-kind=\"coins\"] canvas').toDataURL()")
    ok('pointing at a tile plays its burst', a != still_px and a != b2)
    pg.mouse.move(5, 5); pg.wait_for_timeout(200)
    ok('and it rests again once the pointer leaves', ev("() => document.querySelector('.pick-particle[data-kind=\"coins\"] canvas').toDataURL()") == still_px)
    upd, acts = ev(f"() => [{P(gp)}.updatedAt, {P(gp)}.activity.length]")
    pg.click('.pick-particle[data-kind="binary"]'); pg.wait_for_timeout(150)
    ok('a click picks it: binary 0 and 1 is pressed now', ev(f"() => {P(gp)}.particles") == 'binary' and
       pg.locator('.pick-particle[aria-pressed="true"]').get_attribute('data-kind') == 'binary')
    ok('picking plays the burst on the map', [x['pid'] for x in bursts()] == [gp])
    ok('picking is not work: Updated stays and nothing goes in Activity', ev(f"() => [{P(gp)}.updatedAt, {P(gp)}.activity.length]") == [upd, acts])
    pg.screenshot(path=str(SHOTS / '311-picker.png'))
    pg.wait_for_timeout(1700)
    ev("() => persistNow()")
    ok('the pick travels with the city: in a backup', ev(f"async () => (await buildBackup()).projects.find(x => x.id === '{gp}').particles") == 'binary')
    ev("() => FullView.close()")

    # ---------- the milestone street party (S1, S2) ----------
    reopen_all(gp); calm()
    ev("() => Proxima._test.sayMs(60000)")
    first = ['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons']
    for t in first: tick(gp, t)
    ok('no party while the milestone has a task open', parties() == [])
    center(gp, 4)
    tick(gp, 'Tune the watering reminders'); pg.wait_for_timeout(300)
    ok('S1 the last task of a 4-task milestone throws a street party at its building', parties() == [gp])
    ok('E2 it lasts 30 seconds', 29000 <= ev(f"() => Celebrate.partyOf('{gp}').left") <= 30000)
    line = ev("() => document.querySelector('#pxSayText').textContent")
    want = [l.replace('{milestone}', 'First release').replace('{n} tasks', '4 tasks').replace('{n}', '4').replace('{project}', 'Garden planner') for l in LINES]
    ok('Proxima announces it, in one of her two approved lines, filled in', ev("() => Proxima.saying()") == 'milestone' and line in want)
    ok('V2 her lines for it, word for word as approved', ev("() => PROXIMA_LINES.milestone") == LINES)
    ok('her bubble has Go to it', pg.inner_text('#pxSayRead').strip() == 'Go to it' and pg.is_visible('#pxSay'))
    st = ev("() => { const s = Traffic._state(); return { drones: s.pdrones.length, colors: [...new Set(s.pdrones.map(d => d.color))], dancers: s.people.filter(q => q.mode === 'dance' || q.guest).length, bus: s.cars.filter(c => c.party).length }; }")
    ok('six party drones fly in, in the colors of its particles (binary: cyan)', st['drones'] == 6 and st['colors'] == ['#3FE0F0'])
    ok('a crowd of about 20 dances or walks over to dance', 12 <= st['dancers'] <= 40)
    ok('the nearest bus heads over', st['bus'] == 1)
    ok('party lights hang over its four streets, three to a street', ev("() => Celebrate.items().filter(x => x.light).length") == 12)
    seen = set()
    for _ in range(18):
        seen.update(round(x['t0']) for x in bursts() if x['pid'] == gp); pg.wait_for_timeout(250)
    ok('its particles burst every 2 seconds or so all party long', len(seen) >= 2 and ev(f"() => Celebrate.partyOf('{gp}') !== null"))
    dance = ev("() => Traffic._state().people.filter(q => q.mode === 'dance').length")
    ok('the block dances', dance >= 10)
    up = ev("() => Traffic._rows(Traffic._look(), 'up', false)")
    ok('dancing has its own frame: both arms up', up[0][0] == 'k' and up[0][4] == 'k')
    watching = False
    for _ in range(50):
        if ev("() => Traffic._state().cars.some(c => c.watching)"): watching = True; break
        pg.wait_for_timeout(500)
    ok('the bus pulls up at the block\'s curb to watch', watching)
    if watching:
        bus = ev(f"() => {{ const c = Traffic._state().cars.find(c => c.watching); return Traffic._curbs({P(gp)}.plot.u, {P(gp)}.plot.v).includes(c.ri + ',' + c.rj + ',' + c.h); }}")
        ok('alongside the party\'s block, with the block on its right', bus)
    pg.screenshot(path=str(SHOTS / '312-party.png'))
    ev("() => Light.setMode('night')"); pg.wait_for_timeout(700)
    pg.screenshot(path=str(SHOTS / '313-party-night.png'))
    ev("() => Light.setMode('day')")
    pg.click('#pxSayRead'); pg.wait_for_timeout(600)
    a = ev(f"() => MapView.anchors('{gp}')"); w = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().width")
    ok('Go to it closes her bubble and brings the building to the middle of the map', not pg.is_visible('#pxSay') and abs(a['topX'] - w / 2) < 40)
    untick(gp, 'Tune the watering reminders'); tick(gp, 'Tune the watering reminders'); pg.wait_for_timeout(200)
    ok('once a day: unticking and ticking again throws no second party, and she says nothing more',
       ev("() => Proxima._test.queue().length") == 0 and not ev("() => Proxima.isSaying()") and parties() == [gp])
    ok('the day is kept for the milestone', ev("() => Celebrate._test.state().ms.m_first") == ev("() => ymd(Date.now())"))
    ev("() => Celebrate._test.end()"); pg.wait_for_timeout(2500)
    st = ev("() => { const s = Traffic._state(); return { parties: s.parties.size, dancing: s.people.filter(q => q.mode === 'dance').length, leaving: s.pdrones.every(d => d.leaving), guests: s.people.filter(q => q.guest && !q.guestDone).length }; }")
    ok('when it ends: no one dances, the drones fly off, the guests walk off', st['parties'] == 0 and st['dancing'] == 0 and st['leaving'] and st['guests'] == 0)
    ok('and the lights come down', ev("() => Celebrate.items().length") == 0 and parties() == [])
    pg.wait_for_timeout(3000)
    ok('the bus drives on', not ev("() => Traffic._state().cars.some(c => c.party || c.watching)"))

    # a one-task milestone and a milestone with a repeat never party
    calm()
    tick(gp, 'Publish the app')
    ok('S1 a one-task milestone throws no party', parties() == [] and not ev("() => Proxima.isSaying()"))
    untick(gp, 'Publish the app')
    ev(f"""() => {{ const p = {P(nc)}; p.todos.push({{ id: 't_rep', text: 'Water the beds', description: '', done: false, doneAt: null, due: '2026-10-22',
      milestoneId: 'm_seed_use', repeat: {{ every: 'week', days: [4] }} }}); changed(p); }}""")
    tick(nc, 'Try the project view for a week'); tick(nc, 'Water the beds')
    ok('a milestone with a repeat in it never finishes, so it never parties', parties() == [])
    calm()

    # she waits while a panel is open, and two milestones are said one after another
    reopen_all(nc)
    ev("() => Panel.open('A panel', h('p', null, 'Open'))"); pg.wait_for_timeout(200)
    for t in ['Round 3: decide the block art loop', 'Build the block art skill', 'Make block art for each project']: tick(nc, t)
    ok('the party starts at once, while she waits for the open panel', parties() == [nc] and not ev("() => Proxima.isSaying()") and len(ev("() => Proxima._test.queue()")) == 1)
    ev("() => Panel.close()"); pg.wait_for_timeout(900)
    ok('she says it once the panel closes', ev("() => Proxima.saying()") == 'milestone' and 'Block art' in pg.inner_text('#pxSayText'))
    reopen_all(gp)
    for t in ['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons', 'Tune the watering reminders']: tick(gp, t)
    ok('a second milestone finished meanwhile waits its turn', len(ev("() => Proxima._test.queue()")) == 1)
    pg.click('#pxSayClose'); pg.wait_for_timeout(900)
    ok('and is said after the first', ev("() => Proxima.saying()") == 'milestone' and 'First release' in pg.inner_text('#pxSayText'))
    calm()

    # beside the project view
    reopen_all(gp)
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    for t in ['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons', 'Tune the watering reminders']: tick(gp, t)
    pg.wait_for_timeout(400)
    left = ev("() => document.querySelector('#pxSay').getBoundingClientRect().left - document.querySelector('#mapWrap').getBoundingClientRect().left")
    ok('with the project view open, her bubble sits beside it, over the map', pg.is_visible('#pxSay') and left >= ev("() => FullView.rightEdge()"))
    sq = ev("""() => { const b = document.querySelector('#pxSay'), t = document.querySelector('#pxSayText').getBoundingClientRect(),
        f = document.querySelector('#pxSayFace').getBoundingClientRect(), r = b.getBoundingClientRect(), m = document.querySelector('#mapWrap').getBoundingClientRect();
        return { narrow: b.classList.contains('narrow'), text: Math.round(t.width), face: Math.round(f.width), under: t.top >= f.bottom, inside: r.right <= m.right + 1 }; }""")
    ok(f'squeezed beside the view, her bubble keeps its 100 px face and puts her words under it, across the bubble, inside the map (0.1.57) ({sq})',
       sq['narrow'] and sq['face'] == 100 and sq['under'] and sq['text'] >= 180 and sq['inside'])
    pg.screenshot(path=str(SHOTS / '314-proxima-beside-view.png'))
    ev("() => FullView.close()"); pg.wait_for_timeout(300)
    calm()

    # with the traffic off: only the particles and the lights
    reopen_all(gp)
    ev("() => Traffic.setOn(false)"); pg.wait_for_timeout(200)
    for t in ['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons', 'Tune the watering reminders']: tick(gp, t)
    st = ev("() => { const s = Traffic._state(); return { parties: s.parties.size, drones: s.pdrones.filter(d => !d.leaving).length, dancing: s.people.filter(q => q.mode === 'dance').length }; }")
    ok('with the traffic off, the party has its particles and lights only', parties() == [gp] and ev("() => Celebrate.items().length") == 12 and st == {'parties': 0, 'drones': 0, 'dancing': 0})
    if st != {'parties': 0, 'drones': 0, 'dancing': 0}: print('  traffic off:', st)
    ev("() => Traffic.setOn(true)")
    calm()

    # on Still: no party, but Proxima still announces it
    reopen_all(gp); ev("() => Motion.set('still')"); pg.wait_for_timeout(200)
    for t in ['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons', 'Tune the watering reminders']: tick(gp, t)
    ok('on Still: no party on the map, but she still announces it', parties() == [] and ev("() => Proxima.saying()") == 'milestone')
    ev("() => Motion.set('full')")
    calm()

    pg.reload(); pg.wait_for_timeout(2200)
    ok('the pick is kept after a reload', ev(f"() => {P(gp)}.particles") == 'binary')

    ok('no console errors', not errors)
    if errors: print('\n'.join(errors[:10]))
    b.close()
