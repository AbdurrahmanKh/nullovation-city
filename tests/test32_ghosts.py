"""Ghost tasks (Ghost Tasks, Round 1): every overdue task, and the next task of a building behind its pace, creeps round
its block on the sidewalk as a sheet ghost with glowing eyes and edges in its building's bubble color (G1, M1, L1, L2);
at most 5 to a block, the most overdue first (G2); 12 px tall (L3); a tick lays it to rest, rising and fading (M2); a
click opens its card with the task, its project, the due chip, Tick and Enter (C4, X1); resting the mouse shows its
task (X1); it peeks round corners (X1); its own switch (S1); hidden on Still, shown on the postcard and in the project
view's picture (S2)."""
import io, json, pathlib
from PIL import Image
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

EDGE_RED, EDGE_YELLOW = (255, 61, 127), (255, 200, 30)

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
    ghosts = lambda: ev("() => Ghosts._test.list()")
    texts = lambda pid: ev(f"() => Ghosts.hauntOf({P(pid)}).map(t => t.text)")
    def due(pid, text, days):                          # days from today: negative is overdue, None is no date
        ev(f"() => {{ const t = {T(pid, text)}; t.due = {'null' if days is None else f'ymd(Date.now() + ({days}) * 864e5)'}; changed({P(pid)}); }}")
    def fresh():
        """Every task open and undated, no urgency, the ghosts looked at afresh."""
        ev(f"""() => {{ for (const id of ['{gp}', '{nc}']) {{ const p = getProject(id); for (const t of p.todos) {{ t.done = false; t.doneAt = null; t.due = null; t.repeat = null; t.waiting = false; }}
            p.pin = null; p.star = null; p.urgency = {{ system: 'none', days: 1, lastWorked: null, pickedAt: null }}; changed(p); }}
            DB.city.rest = []; DB.city.away = ''; DB.city.awaySpans = []; Ghosts._test.reset(); }}""")
        pg.wait_for_timeout(1300)
    rect = lambda: ev("() => { const b = document.querySelector('#mapWrap').getBoundingClientRect(); return { x: b.left, y: b.top, w: b.width, h: b.height }; }")
    def center_on(wx, wy, z):
        ev(f"() => MapView.setCam({{ x: 0, y: 0, z: {z} }})"); pg.wait_for_timeout(60)
        r = rect()
        for _ in range(3):
            cx, cy = ev(f"() => MapView.worldCss({wx}, {wy})"); c = ev("() => MapView.camState()")
            ev(f"() => MapView.setCam({{ x: {c['x']} + ({cx} - {r['w']} / 2) / {z}, y: {c['y']} + ({cy} - {r['h']} / 2) / {z}, z: {z} }})")
            pg.wait_for_timeout(80)
    def hold(tid, **o):                                # a ghost set down by hand, and kept there
        return ev(f"() => Ghosts._test.set('{tid}', {json.dumps(dict({'mode': 'linger', 't': 9999, 'pos': None, 'alpha': 1, 'lift': 0}, **o))})")
    def find(tid): return next((g for g in ghosts() if g['tid'] == tid), None)
    def pixels(rgb, clip=None):
        img = Image.open(io.BytesIO(pg.screenshot(clip=clip) if clip else pg.screenshot())).convert('RGB')
        return sum(1 for px in img.get_flattened_data() if px == rgb)
    tid = lambda pid, text: ev(f"() => {T(pid, text)}.id")
    ev("() => { Light.setMode('day'); MapView.setBubbleMode('all'); }")

    # ---------- which tasks haunt (G1, G2) ----------
    fresh()
    ok('a city with nothing overdue and no building behind its pace has no ghosts', ghosts() == [] and texts(gp) == [] and texts(nc) == [])
    due(gp, 'Save a plan as a file', -1); due(gp, 'Draw the beds on a grid', -6); due(gp, 'Add plant icons', -3)
    ok('every overdue task haunts, the most overdue first', texts(gp) == ['Draw the beds on a grid', 'Add plant icons', 'Save a plan as a file'])
    pg.wait_for_timeout(1300)
    g3 = sorted(g['tid'] for g in ghosts() if g['pid'] == gp)
    ok('three ghosts round its block', len(g3) == 3 and all(g['u'] == ev(f"() => {P(gp)}.plot.u") and g['v'] == ev(f"() => {P(gp)}.plot.v") for g in ghosts()))
    ok('they glow red, its bubble\'s color', {g['color'] for g in ghosts()} == {'red'} and ev(f"() => urgencyOf({P(gp)}).color") == 'red')
    due(gp, 'Tune the watering reminders', 0); due(gp, 'Publish the app', 1)
    ok('a task due today or tomorrow is red on its bubble but does not haunt until it is late', len(texts(gp)) == 3)
    ev(f"() => {{ const p = {P(gp)}; p.urgency = {{ system: 'pace', days: 3, pickedAt: Date.now() - 0.5 * 864e5, lastWorked: null }}; changed(p); }}")
    ok('behind its pace with overdue tasks: the next task the card puts first is already one of them, so one ghost each', texts(gp) == ['Draw the beds on a grid', 'Add plant icons', 'Save a plan as a file'])
    ev(f"() => {{ setPin({P(gp)}, {T(gp, 'Publish the app')}, true); changed({P(gp)}); }}")
    ok('a pinned next task that is not overdue gets a ghost of its own, after the overdue ones', texts(gp) == ['Draw the beds on a grid', 'Add plant icons', 'Save a plan as a file', 'Publish the app'])
    ev(f"() => {{ const p = {P(gp)}; p.urgency = {{ system: 'none', days: 1, lastWorked: null, pickedAt: null }}; changed(p); }}")
    ok('not behind its pace, the pinned task does not haunt', len(texts(gp)) == 3)

    fresh()
    ev(f"() => {{ const p = {P(nc)}; p.urgency = {{ system: 'pace', days: 3, pickedAt: Date.now() - 0.5 * 864e5, lastWorked: null }}; changed(p); }}")
    first = ev(f"() => bubbleTodos({P(nc)}, 1).list[0].text")
    ok(f'one period behind its pace: its next task haunts ({first})', texts(nc) == [first] and ev(f"() => urgencyOf({P(nc)}).color") == 'yellow')
    pg.wait_for_timeout(1300)
    ok('in yellow, its bubble\'s color', [g['color'] for g in ghosts() if g['pid'] == nc] == ['yellow'])
    ev(f"() => {{ const p = {P(nc)}; p.urgency.pickedAt = Date.now() - 4 * 864e5; changed(p); }}")
    pg.wait_for_timeout(1300)
    ok('two periods behind: red, the same ghost', texts(nc) == [first] and [g['color'] for g in ghosts() if g['pid'] == nc] == ['red'])
    ev(f"() => {{ const p = {P(nc)}; p.urgency.lastWorked = Date.now() - 4 * 864e5; p.urgency.pickedAt = Date.now() - 9 * 864e5; changed(p); }}")
    ok('(a task finished 4 days ago: behind its pace)', texts(nc) == [first])
    ev("() => { DB.city.rest = [0, 1, 2, 3, 4, 5, 6]; }")
    ok('rest days pause the pace: no ghost', texts(nc) == [])
    ev("() => { DB.city.rest = []; DB.city.away = ymd(Date.now() + 3 * 864e5); }")
    due(nc, 'Build the block art skill', -4)
    ok('away: no building is behind its pace, but a task late before you left still haunts', texts(nc) == ['Build the block art skill'])
    ev("() => { DB.city.away = ''; }")
    due(nc, 'Build the block art skill', None)
    ev(f"() => {{ const p = {P(nc)}; p.urgency = {{ system: 'finish', days: 1, lastWorked: Date.now() - 2 * 864e5, pickedAt: Date.now() - 3 * 864e5 }}; changed(p); }}")
    ok('work until finished, no task finished for a day: its next task haunts', texts(nc) == [first])
    ev(f"() => {{ const p = {P(nc)}; p.urgency.lastWorked = Date.now() - 3600e3; changed(p); }}")
    ok('a task finished in the last day: no ghost', texts(nc) == [])
    due(nc, 'Build the block art skill', -4)
    ev(f"() => {{ const t = {T(nc, 'Build the block art skill')}; t.repeat = {{ every: 'week', days: [1] }}; tickTask({P(nc)}, t); changed({P(nc)}); }}")
    ok('a ticked repeat waiting for its next date never haunts', texts(nc) == [] and ev(f"() => isWaiting({T(nc, 'Build the block art skill')})"))

    # at most 5 to a block, the most overdue first; a tick lets the next one out
    fresh()
    ev(f"""() => {{ const p = {P(gp)}; for (let k = 0; k < 3; k++) p.todos.push({{ id: 'gx' + k, text: 'Extra task ' + k, description: '', done: false, doneAt: null, due: null, milestoneId: 'm_first' }}); changed(p); }}""")
    names = ['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons', 'Tune the watering reminders', 'Publish the app', 'Extra task 0', 'Extra task 1']
    for k, n in enumerate(names): due(gp, n, -(10 - k))
    ok('seven overdue: five ghosts, the five most overdue (G2)', texts(gp) == names[:5])
    pg.wait_for_timeout(1300)
    ok('and five on the map', len([g for g in ghosts() if g['pid'] == gp]) == 5)
    ev(f"() => {{ tickTask({P(gp)}, {T(gp, 'Draw the beds on a grid')}); changed({P(gp)}); }}")
    pg.wait_for_timeout(1300)
    out = [g for g in ghosts() if g['pid'] == gp]
    sixth = next((g for g in out if g['tid'] == tid(gp, 'Extra task 0')), None)
    ok('one ticked: the sixth comes out of its building\'s front, fading in', sixth is not None and sixth['mode'] in ('out', 'walk') and len([g for g in out if g['mode'] != 'leave']) == 5)
    ev(f"() => {{ const p = {P(gp)}; p.todos = p.todos.filter(t => !t.id.startsWith('gx')); changed(p); }}")

    # ---------- on the sidewalk, round its own block (C3, M1) ----------
    fresh()
    due(gp, 'Draw the beds on a grid', -6); due(gp, 'Add plant icons', -3)
    ev("() => Ghosts._test.reset()"); pg.wait_for_timeout(1300)
    gs = [g for g in ghosts() if g['pid'] == gp]
    ok('after the city opens they are already on their rounds, not coming out', len(gs) == 2 and all(g['mode'] != 'out' for g in gs))
    W = ev("() => ({ S: WORLD.S, M: WORLD.MARGIN, P: WORLD.PITCH })")
    u, v = gs[0]['u'], gs[0]['v']
    a0, b0 = W['M'] + u * W['P'], W['M'] + v * W['P']
    def on_loop(at):
        i, j = at; lo, hi = -0.15 - 1e-6, W['S'] + 0.15 + 1e-6
        di, dj = i - a0, j - b0
        edge = min(abs(di + 0.15), abs(di - W['S'] - 0.15), abs(dj + 0.15), abs(dj - W['S'] - 0.15))
        return lo <= di <= hi and lo <= dj <= hi and edge < 1e-6
    ok('each walks the sidewalk ring round its block, 0.15 tiles out from its lot', all(on_loop(g['at']) for g in gs))
    p0 = {g['tid']: g['p'] for g in gs}
    ev("() => { for (const g of Ghosts._test.list()) Ghosts._test.set(g.tid, { mode: 'walk', blocked: 0 }); }")
    ev("() => { window.__rnd = Math.random; Math.random = () => 0.99; }")    # no pauses, no peeks: just walking
    pg.wait_for_timeout(2000)
    moved = [abs(next(g for g in ghosts() if g['tid'] == k)['p'] - p0[k]) for k in p0]
    ev("() => { Math.random = window.__rnd; }")
    ok(f'they creep: about half walking speed ({", ".join(f"{m:.2f}" for m in moved)} tiles in 2 s)', all(0.12 < m < 0.4 for m in moved))
    ok('never off their block', all(on_loop(g['at']) for g in ghosts() if g['pid'] == gp))

    # peeking round a corner (X1)
    t0 = gs[0]['tid']
    side = W['S'] + 0.3
    hold(t0, mode='walk', p=side - 0.03, dir=1, blocked=0)
    hold(gs[1]['tid'], p=3 * side - 2)
    ev("() => { window.__rnd = Math.random; Math.random = () => 0.1; }")
    pg.wait_for_timeout(500)
    g = find(t0)
    ev("() => { Math.random = window.__rnd; }")
    ok('at a corner it stops and peeks round it', g['mode'] == 'peek' and abs(g['p'] - side) < 1e-6)
    pg.wait_for_timeout(800)
    g = find(t0)
    corner = ev(f"() => {{ const g = Ghosts._test.list().find(g => g.tid === '{t0}'); return [g.at, {a0} + {W['S']} + 0.15, {b0} - 0.15]; }}")
    ok('leaning round, its eyes on the new side', g['mode'] == 'peek' and g['look'] == [0, 1] and abs(g['at'][0] - corner[1]) < 1e-6 and 0.05 < g['at'][1] - corner[2] < 0.2)
    pg.wait_for_timeout(1500)
    g = find(t0)
    ok('then it carries on along the new side', g['mode'] in ('walk', 'pause', 'linger', 'peek') and g['p'] >= side - 1e-6)

    # its eyes look the way it goes
    def eyes(ex, ey):
        return ev(f"""() => {{ const c = Ghosts._test.art('red', 0, {ex}, {ey}).body, d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, out = [];
          for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {{ const k = (y * c.width + x) * 4; if (d[k] === 232 && d[k + 1] === 25 && d[k + 2] === 90) out.push([x, y]); }} return out; }}""")
    ok('the eyes: two of 1 by 2, glowing', sorted(eyes(0, 0)) == [[4, 5], [4, 6], [6, 5], [6, 6]])
    ok('to the right and low coming toward you, to the left and high going away', sorted(eyes(1, 1)) == [[5, 6], [5, 7], [7, 6], [7, 7]] and sorted(eyes(-1, -1)) == [[3, 4], [3, 5], [5, 4], [5, 5]])

    # ---------- how it looks (L1, L1a, L2, L3) ----------
    art = ev("""() => { const out = {}; for (const col of ['red', 'yellow']) { const c = Ghosts._test.art(col, 0, 0, 0).body, d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let x0 = 99, x1 = -1, y0 = 99, y1 = -1, solid = 0, see = 0; const cols = {};
        for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) { const k = (y * c.width + x) * 4; if (!d[k + 3]) continue;
          x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); if (d[k + 3] === 255) solid++; else see++; cols[[d[k], d[k + 1], d[k + 2], d[k + 3]].join()] = 1; }
        out[col] = { w: x1 - x0 + 1, h: y1 - y0 + 1, solid, see, cols: Object.keys(cols) }; } return out; }""")
    ok('a sheet ghost 9 px wide and 12 tall at 1x (L3)', art['red']['w'] == 9 and art['red']['h'] == 12)
    ok('see-through inside its glowing edge (L1a)', art['red']['see'] > 40 and art['red']['solid'] > 20)
    ok('its edge in red or yellow, its building\'s bubble color (L2)', '255,61,127,255' in art['red']['cols'] and '255,200,30,255' in art['yellow']['cols'])
    ok('the hem ripples: three frames', len({''.join(ev(f"() => Ghosts._test.shape({k})")) for k in range(3)}) == 3)

    # on the map, by day and by night: the glow keeps its color
    fresh()
    due(gp, 'Draw the beds on a grid', -6)
    ev("() => { MapView.setBubbleMode('none'); }"); pg.wait_for_timeout(1300)
    t1 = tid(gp, 'Draw the beds on a grid')
    hold(t1, p=(W['S'] + 0.3) * 1.5)
    pg.wait_for_timeout(300)
    bx = find(t1)['box']
    center_on((bx['x0'] + bx['x1']) / 2, (bx['y0'] + bx['y1']) / 2, 4)
    pg.wait_for_timeout(300)
    r = rect(); clip = {'x': r['x'] + r['w'] / 2 - 120, 'y': r['y'] + r['h'] / 2 - 120, 'width': 240, 'height': 240}
    day_px = pixels(EDGE_RED, clip)
    pg.screenshot(path=str(SHOTS / '320-ghost-day.png'), clip=clip)
    ev("() => Light.setMode('night')"); pg.wait_for_timeout(500)
    night_px = pixels(EDGE_RED, clip)
    pg.screenshot(path=str(SHOTS / '321-ghost-night.png'), clip=clip)
    ev("() => Light.setMode('day')"); pg.wait_for_timeout(300)
    ok(f'drawn on the map in its glowing red ({day_px} px at 4x)', day_px > 200)
    ok(f'and the same red at night, the glow keeping its color ({night_px} px)', night_px > 100)

    # ---------- the hover and the card (X1, C4) ----------
    gcss = lambda: ev(f"() => {{ const b = Ghosts._test.list().find(g => g.tid === '{t1}').box; return MapView.worldCss((b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2 + 1); }}")
    cx, cy = gcss()
    pg.mouse.move(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(400)
    ok('resting the mouse on a ghost shows its task by the pointer', pg.is_visible('#tip') and pg.text_content('#tip') == 'Draw the beds on a grid')
    ok('and no building is hovered', ev("() => document.querySelector('#hoverTask').hidden"))
    ev(f"() => MapView.select('{nc}', {{ glide: false }})"); pg.wait_for_timeout(300)
    ok('(a status card open first)', pg.is_visible('#bubble'))
    cx, cy = gcss()
    pg.mouse.click(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(400)
    ok('a click opens its card, and the pointer\'s tip makes way for it', pg.is_visible('#ghostCard') and not pg.is_visible('#tip'))
    ok('the card: its project, the task, its due chip, Tick and Enter',
       pg.text_content('#ghostCard .gc-project') == 'Garden planner' and pg.text_content('#ghostCard .gc-task') == 'Draw the beds on a grid'
       and pg.text_content('#ghostCard .due') == '6 days overdue' and pg.text_content('#ghostCard .gc-tick').strip() == 'Tick' and pg.text_content('#ghostCard .gc-enter').strip() == 'Enter')
    ok('the status card closes for it, and the ghost holds still', not pg.is_visible('#bubble') and find(t1)['mode'] == 'card')
    cb = pg.locator('#ghostCard').bounding_box(); gx, gy = gcss()
    ok('the card sits over its ghost', cb['y'] + cb['height'] <= r['y'] + gy and cb['x'] < r['x'] + gx < cb['x'] + cb['width'])
    pg.screenshot(path=str(SHOTS / '322-ghost-card.png'), clip={'x': cb['x'] - 40, 'y': cb['y'] - 20, 'width': cb['width'] + 80, 'height': cb['height'] + 140})
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it, and the ghost goes on', not pg.is_visible('#ghostCard') and find(t1)['mode'] == 'walk')
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(200)
    cx, cy = gcss(); pg.mouse.click(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(300)
    pg.mouse.click(r['x'] + 30, r['y'] + r['h'] - 30); pg.wait_for_timeout(300)
    ok('a click elsewhere on the map closes it', not pg.is_visible('#ghostCard'))
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(200)
    cx, cy = gcss(); pg.mouse.click(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(300)
    ev(f"() => MapView.select('{nc}', {{ glide: false }})"); pg.wait_for_timeout(200)
    ok('a building\'s status card closes it', not pg.is_visible('#ghostCard') and pg.is_visible('#bubble'))
    ev("() => MapView.deselect()")

    # Tick: done, with Undo; the ghost rises and fades (M2)
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(200)
    cx, cy = gcss(); pg.mouse.click(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(300)
    pg.click('#ghostCard .gc-tick'); pg.wait_for_timeout(250)
    g = find(t1)
    ok('Tick ticks the task off, as a tick anywhere does', ev(f"() => {T(gp, 'Draw the beds on a grid')}.done") and ev(f"() => {P(gp)}.activity.some(e => e.text === 'Done: Draw the beds on a grid')"))
    ok('the card closes, and a toast says so with Undo', not pg.is_visible('#ghostCard') and 'Ticked off: Draw the beds on a grid.' in pg.text_content('#toast') and pg.is_visible('#toast .toast-act'))
    ok('its ghost rises and fades', g is not None and g['mode'] == 'leave' and 0 < g['alpha'] < 1 and g['lift'] >= 1)
    pg.wait_for_timeout(1000)
    ok('and is gone in about a second', find(t1) is None)
    pg.click('#toast .toast-act'); pg.wait_for_timeout(1400)
    ok('Undo opens the task again, and it haunts again, coming out of its building', not ev(f"() => {T(gp, 'Draw the beds on a grid')}.done") and find(t1) is not None and find(t1)['mode'] in ('out', 'walk'))

    # a tick from anywhere else, and a task that stops haunting without a tick
    pg.wait_for_timeout(3500)
    ev(f"() => {{ tickTask({P(gp)}, {T(gp, 'Draw the beds on a grid')}); changed({P(gp)}); }}"); pg.wait_for_timeout(150)
    ok('a tick from the status card or the project view lays it to rest too, at once', find(t1)['mode'] == 'leave')
    ev(f"() => {{ untickTask({P(gp)}, {T(gp, 'Draw the beds on a grid')}); changed({P(gp)}); }}"); pg.wait_for_timeout(2600)
    due(gp, 'Draw the beds on a grid', 5); pg.wait_for_timeout(1300)
    g = find(t1)
    ok('a new due date ahead: it stops haunting, rising and fading the same way', g is None or g['mode'] == 'leave')

    # Enter: inside, with the task open
    due(gp, 'Draw the beds on a grid', -6); ev("() => Ghosts._test.reset()"); pg.wait_for_timeout(1300)
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(200)
    cx, cy = gcss(); pg.mouse.click(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(300)
    pg.click('#ghostCard .gc-enter'); pg.wait_for_timeout(500)
    ok('Enter steps inside the building, with the task open beside it', ev("() => FullView.isOpen()") and pg.is_visible('#pvTaskDesc') and pg.input_value('#pvTaskDesc') == ev(f"() => {T(gp, 'Draw the beds on a grid')}.description") and not pg.is_visible('#ghostCard'))
    pg.wait_for_timeout(300)
    pic = ev("""() => { const c = document.querySelector('.pv-scene canvas, .fv-scene canvas, .pv-hero canvas'); if (!c) return -1; const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0;
        for (let k = 0; k < d.length; k += 4) if (d[k] === 255 && d[k + 1] === 61 && d[k + 2] === 127) n++; return n; }""")
    ok(f'the project view\'s picture shows its ghost (S2: {pic} px)', pic > 0)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # a repeat ticked from its card moves on, with its own toast
    ev(f"() => {{ const t = {T(gp, 'Draw the beds on a grid')}; t.repeat = {{ every: 'day', n: 1 }}; changed({P(gp)}); }}")
    ev("() => Ghosts._test.reset()"); pg.wait_for_timeout(1300)
    center_on((bx['x0'] + bx['x1']) / 2, (bx['y0'] + bx['y1']) / 2, 4)
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(250)
    cx, cy = gcss(); pg.mouse.click(r['x'] + cx, r['y'] + cy); pg.wait_for_timeout(300)
    pg.click('#ghostCard .gc-tick'); pg.wait_for_timeout(300)
    ok('a repeat ticked from its card moves on to its next date, and says when it comes back', ev(f"() => isWaiting({T(gp, 'Draw the beds on a grid')})") and 'comes back' in pg.text_content('#toast'))
    ev(f"() => {{ const t = {T(gp, 'Draw the beds on a grid')}; t.repeat = null; t.waiting = false; t.due = ymd(Date.now() - 6 * 864e5); changed({P(gp)}); }}")

    # ---------- when they show (S1, S2) ----------
    ev("() => Ghosts._test.reset()"); pg.wait_for_timeout(1300)
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(250)
    ev("() => Traffic.setOn(false)"); pg.wait_for_timeout(400)
    ok('Traffic off leaves them', len(ev("() => Ghosts.items()")) == 1 and pixels(EDGE_RED, clip) > 200)
    ev("() => Traffic.setOn(true)")
    ok('so does No bubbles', ev("() => MapView.bubbleMode()") == 'none' and len(ev("() => Ghosts.items()")) == 1)
    pg.click('#btnOpenSettings'); pg.click('#setTabs [data-tab="look"]'); pg.wait_for_timeout(200)
    ok('Settings, Look: Ghosts, on by default', pg.is_visible('#optGhosts') and pg.is_checked('#optGhosts') and 'Ghosts' in pg.text_content('[data-set="ghosts"]'))
    pg.click('#optGhosts'); pg.wait_for_timeout(400)
    ok('off: no ghosts on the map', not ev("() => Ghosts.isOn()") and ev("() => Ghosts.items()") == [] and pixels(EDGE_RED, clip) == 0)
    ok('with a dot on the setting and its tab', ev("() => document.querySelector('[data-set=\"ghosts\"]').classList.contains('changed') && document.querySelector('.set-tab[data-tab=\"look\"]').classList.contains('changed')"))
    ok('kept on this computer', ev("() => localStorage.getItem('nullovation-city:ghosts')") == '0')
    pg.reload(); pg.wait_for_timeout(2000)
    ok('and after a reload', not ev("() => Ghosts.isOn()"))
    if not pg.is_visible('#settings'): pg.click('#btnOpenSettings')
    pg.click('#setTabs [data-tab="look"]'); pg.wait_for_timeout(200)
    pg.click('#btnTabReset')
    pg.wait_for_timeout(300)
    ok('Reset to defaults turns them on again', ev("() => Ghosts.isOn()") and pg.is_checked('#optGhosts'))
    pg.click('#setBack'); pg.wait_for_timeout(200)
    ev("() => { Light.setMode('day'); MapView.setBubbleMode('none'); }")
    pg.wait_for_timeout(1300)
    center_on((bx['x0'] + bx['x1']) / 2, (bx['y0'] + bx['y1']) / 2, 4)
    ok('back on their rounds after the reload, not coming out', len(ghosts()) == 1 and ghosts()[0]['mode'] != 'out')
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(250)

    ev("() => { Motion.set('still'); MapView.invalidate(); MapView.kick(); }"); pg.wait_for_timeout(400)
    ok('Motion on Still hides them (S2)', ev("() => Ghosts.items()") == [] and pixels(EDGE_RED, clip) == 0)
    ev("() => { Motion.set(null); MapView.invalidate(); MapView.kick(); }"); pg.wait_for_timeout(1300)
    ok('and back on Full, they are on their rounds again', len(ghosts()) == 1 and ghosts()[0]['mode'] != 'out')
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(250)
    ev("() => MapView.setEditing(true)"); pg.wait_for_timeout(300)
    ok('Edit City hides them', ev("() => Ghosts.items()") == [])
    ev("() => MapView.setEditing(false)"); pg.wait_for_timeout(1300)
    hold(t1, p=(W['S'] + 0.3) * 1.5); pg.wait_for_timeout(250)
    with pg.expect_download() as dl:
        pg.click('#btnPostcard')
    card = Image.open(io.BytesIO(pathlib.Path(dl.value.path()).read_bytes())).convert('RGB')
    ok('the postcard shows them (S2)', EDGE_RED in set(card.get_flattened_data()))

    # its building moves: its ghosts go with it
    ev(f"() => {{ const p = {P(gp)}; p.plot = {{ u: 0, v: 0 }}; changed(p, {{ touch: false }}); }}"); pg.wait_for_timeout(1300)
    ok('its building moved: its ghost goes round the new block', all(g['u'] == 0 and g['v'] == 0 for g in ghosts() if g['pid'] == gp) and len(ghosts()) == 1)
    ev(f"() => {{ const p = {P(gp)}; p.plot = {{ u: 2, v: 1 }}; changed(p, {{ touch: false }}); }}")

    # nothing new in the data
    saved = ev("() => localStorage.getItem('nullovation-city:v1')")
    ok('nothing about ghosts is saved in the city', 'ghost' not in saved.lower())

    # a crowd of five round a block, at 2x, by day and night, to look at
    fresh()
    for k, n in enumerate(['Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons', 'Tune the watering reminders', 'Publish the app']): due(gp, n, -(6 - k))
    ev(f"() => {{ const p = {P(nc)}; p.urgency = {{ system: 'pace', days: 3, pickedAt: Date.now() - 0.5 * 864e5, lastWorked: null }}; changed(p); MapView.setBubbleMode('all'); Ghosts._test.reset(); }}")
    pg.wait_for_timeout(5000)
    a = ev(f"() => MapView.anchors('{gp}')"); c = ev("() => MapView.camState()")
    center_on(*ev(f"() => {{ const [X, Y] = MapView.cssWorld({a['baseX']}, {a['baseY']}); return [X, Y + 20]; }}"), 2)
    pg.wait_for_timeout(400)
    r = rect(); clip2 = {'x': r['x'] + r['w'] / 2 - 360, 'y': r['y'] + r['h'] / 2 - 240, 'width': 720, 'height': 480}
    pg.screenshot(path=str(SHOTS / '323-ghosts-city-day.png'), clip=clip2)
    ev("() => Light.setMode('night')"); pg.wait_for_timeout(500)
    pg.screenshot(path=str(SHOTS / '324-ghosts-city-night.png'), clip=clip2)
    ev("() => Light.setMode('day')")
    ok('five red ghosts round the research lab and one yellow round the city hall', sorted(g['color'] for g in ghosts()) == ['red'] * 5 + ['yellow'])

    print('no console errors' if not errors else 'console errors: ' + ' | '.join(errors[:6]))
    b.close()
