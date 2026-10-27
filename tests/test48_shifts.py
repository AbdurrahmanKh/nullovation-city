"""Shifts UX (Rounds 1 and 2): a shift's icon and colors, the full mark and the small mark in every place a task shows
one, the hollow mark of an open task with no shift and the three-part pick it opens, the pick in the task panel and the
line over the map, Open in Claude opening a Think task on Think, and the city skill writing a task's shift."""
import json, subprocess, sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))
nth = lambda n: (date.today() + timedelta(days=n)).isoformat()
COLORS = {'create': 'rgb(116, 201, 151)', 'think': 'rgb(183, 165, 240)', 'errand': 'rgb(242, 154, 116)'}   # leaf, lavender, coral (B1)
INK = 'rgb(43, 37, 66)'

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
    task = lambda pid, text: f"getProject('{pid}').todos.find(t => t.text === {json.dumps(text)})"
    get = lambda pid, text: ev(f"() => JSON.parse(JSON.stringify({task(pid, text)} || null))")
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true); }")
    act = lambda: ev("() => { const a = document.activeElement; return a ? (a.dataset.shift || a.id || a.className) : ''; }")

    # ---------- the art: three icons and the hollow mark, on the city's 12 px grid ----------
    icons = ev("() => ['shiftCreate', 'shiftThink', 'shiftErrand', 'shiftNone'].map(n => ICONS[n] ? ICONS[n].length + 'x' + ICONS[n][0].length : 'none')")
    ok(f'each shift has its pixel icon, and the hollow mark its own, 12 by 12 ({icons})', icons == ['12x12'] * 4)
    ok("Create wears the keyboard (Round 2, A1): three rows of keys over a space bar",
       ev("() => SHIFT_ICON.create === 'shiftCreate' && ICONS.shiftCreate[4] === '#.#.#.#.#.##' && ICONS.shiftCreate[8] === '###......###'"))
    ok('Think the thought cloud and Errand the running man (A1b, A1c)', ev("() => SHIFT_ICON.think === 'shiftThink' && SHIFT_ICON.errand === 'shiftErrand'"))
    col = ev("""() => { const out = {}; for (const s of ['create', 'think', 'errand']) { const m = shiftMark(s, { full: true }); document.body.append(m);
      const cs = getComputedStyle(m); out[s] = [cs.backgroundColor, cs.color, m.textContent, m.getBoundingClientRect().height]; m.remove(); } return out; }""")
    ok(f"B1 the colors: leaf, lavender and coral ({ {k: v[0] for k, v in col.items()} })", all(col[s][0] == COLORS[s] for s in COLORS))
    ok('the full mark: the icon and the name in ink on its color, 16 px tall', all(v[1] == INK and v[3] == 16 for v in col.values()) and [v[2] for v in col.values()] == ['Create', 'Think', 'Errand'])
    sm = ev("() => { const m = shiftMark('think'); document.body.append(m); const r = m.getBoundingClientRect(), o = [r.width, r.height, m.textContent, m.getAttribute('role'), m.getAttribute('aria-label'), !!m.querySelector('svg')]; m.remove(); return o; }")
    ok(f'A3 the small mark: the icon alone on its 16 px square, named for a screen reader ({sm})', sm == [16, 16, '', 'img', 'Shift: Think', True])

    # the city: a shift on most tasks, two with none, a star, an overdue task for a ghost
    ev(f"""() => {{
      const P = getProject('{gp}'), N = getProject('{nc}'); const T = (p, x) => p.todos.find(t => t.text === x);
      Object.assign(T(P, 'Draw the beds on a grid'), {{ due: '{nth(0)}', shift: 'create' }});
      Object.assign(T(P, 'Save a plan as a file'), {{ due: '{nth(-2)}', shift: 'think' }});
      Object.assign(T(P, 'Publish the app'), {{ due: '{nth(1)}', shift: 'errand' }});
      Object.assign(T(N, 'Build the block art skill'), {{ shift: 'create' }});
      Object.assign(T(N, 'Try the project view for a week'), {{ shift: 'think' }});
      setStar(N, T(N, 'Build the block art skill'), true);
      changed(P); changed(N);
    }}""")
    quiet()
    up, acts = ev(f"() => getProject('{gp}').updatedAt"), ev(f"() => getProject('{gp}').activity.length")

    # ---------- where each mark shows (Round 1, B1; Round 2, C1) ----------
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(500)
    card = ev("() => [...document.querySelectorAll('#bubble .b-todos li')].map(li => { const m = li.querySelector('.shift-mark'); return li.querySelector('.b-task').firstChild.textContent + ':' + (m ? m.className : ''); })")
    ok(f"the status card: each row's small mark ({card})", any('Save a plan as a file:shift-mark small shift-think b-shift' == c for c in card)
       and any(c.startswith('Draw the beds on a grid:shift-mark small shift-create') for c in card))
    ok('C1 and no hollow mark on the status card', not ev("() => !!document.querySelector('#bubble .shift-mark.none')"))
    ev("() => MapView.deselect()")

    due = ev("() => [...document.querySelectorAll('#dueList .due-item')].map(li => li.querySelector('.due-text').textContent + ':' + ((li.querySelector('.due-meta .shift-mark') || {}).className || ''))")
    ok(f'Due this week: the small mark first in each row\'s line ({due})', 'Publish the app:shift-mark small shift-errand' in due
       and ev("() => [...document.querySelectorAll('#dueList .due-meta')].every(m => !m.querySelector('.shift-mark') || m.firstElementChild.classList.contains('shift-mark'))"))
    ok("the starred card: its task's small mark before its project", ev("() => { const s = document.querySelector('#btnStar .star-proj'); return s.firstElementChild.className === 'shift-mark small shift-create' && s.textContent === 'Nullovation City'; }"))
    ok('C1 and no hollow mark in the side bar', not ev("() => !!document.querySelector('#menu .shift-mark.none')"))

    # the hover's line: the next task's small mark, on the light line in its own color
    left = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    ev("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(300)
    a = ev(f"() => MapView.anchors('{gp}')")
    pg.mouse.move(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(600)
    hv = ev("() => { const el = document.querySelector('#hoverTask'), m = el.querySelector('.shift-mark'); return [el.hidden, el.textContent, m && m.className, m && getComputedStyle(m).backgroundColor]; }")
    ok(f"the hover's line: the next task's small mark, in its color on the light line ({hv})", hv == [False, 'Draw the beds on a grid', 'shift-mark small shift-create', COLORS['create']])
    ev(f"() => setPin(getProject('{gp}'), {task(gp, 'Add plant icons')}, true)"); pg.mouse.move(left + 40, 40); pg.wait_for_timeout(300)
    pg.mouse.move(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(600)
    ok('C1 a next task with no shift: no mark on the hover\'s line', ev("() => { const el = document.querySelector('#hoverTask'); return !el.hidden && el.textContent === 'Add plant icons' && !el.querySelector('.shift-mark'); }"))
    pg.screenshot(path=str(SHOTS / '485-shift-hover.png'), clip={'x': left + a['topX'] - 200, 'y': a['topY'] - 60, 'width': 400, 'height': 260})
    pg.mouse.move(left + 40, 40); pg.wait_for_timeout(300)

    # a ghost's card: the overdue task's small mark beside its due chip
    ev("() => Ghosts._test.reset()"); pg.wait_for_timeout(1500)
    tid = ev(f"() => {task(gp, 'Save a plan as a file')}.id")
    ev(f"() => Ghosts._test.set('{tid}', {{ mode: 'linger', t: 9999, alpha: 1, lift: 0 }})"); pg.wait_for_timeout(300)
    box = ev(f"() => {{ const g = Ghosts._test.list().find(g => g.tid === '{tid}'); if (!g || !g.box) return null; const b = g.box; return MapView.worldCss((b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2 + 1); }}")
    r = pg.query_selector('#mapWrap').bounding_box()
    if box: pg.mouse.click(r['x'] + box[0], r['y'] + box[1]); pg.wait_for_timeout(400)
    gc = ev("() => { const c = document.querySelector('#ghostCard'); if (!c || c.hidden) return null; const d = c.querySelector('.gc-due'); return [d.firstElementChild.className, d.textContent]; }")
    ok(f"a ghost's card: its task's small mark before its due chip ({gc})", gc == ['shift-mark small shift-think', '2 days overdue'])
    ok('C1 and no hollow mark there', not ev("() => !!document.querySelector('#ghostCard .shift-mark.none')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # the project view: small marks on the rows, the hollow mark on an open task with none
    ev(f"() => setPin(getProject('{gp}'), {task(gp, 'Add plant icons')}, false)")
    ev(f"() => {{ const t = {task(gp, 'Tune the watering reminders')}; t.done = true; t.doneAt = Date.now(); changed(getProject('{gp}'), {{ touch: false }}); }}")
    up = ev(f"() => getProject('{gp}').updatedAt")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    rows = lambda: ev("() => Object.fromEntries([...document.querySelectorAll('.task')].map(li => [li.querySelector('.task-title').textContent, ((li.querySelector('.shift-mark') || {}).className || '')]))")
    rv = rows()
    ok(f"B1 the project view's rows: the small mark ({rv})", rv['Draw the beds on a grid'] == 'shift-mark small shift-create row-shift' and rv['Publish the app'] == 'shift-mark small shift-errand row-shift')
    ok('C1 an open task with no shift: the hollow mark where its mark would be', rv['Add plant icons'] == 'shift-mark none row-shift'
       and ev("() => { const b = [...document.querySelectorAll('.task')].find(l => l.textContent.includes('Add plant icons')).querySelector('.shift-mark.none'); return b.tagName === 'BUTTON' && b.getAttribute('aria-label') === 'Give it a shift: Add plant icons' && b.getAttribute('aria-haspopup') === 'dialog'; }"))
    ok('a done task with no shift has none', rv['Tune the watering reminders'] == '')
    nx = ev("() => { const m = document.querySelector('.pv-next .pv-next-shift'); return [m.className, m.textContent, getComputedStyle(m).backgroundColor]; }")
    ok(f'B1 What is next: the full mark ({nx})', nx == ['shift-mark full shift-create pv-next-shift', 'Create', COLORS['create']])
    pg.screenshot(path=str(SHOTS / '486-shift-view.png'))

    # the hollow mark's pick
    hol = pg.locator('.task', has_text='Add plant icons').locator('.shift-mark.none')
    hol.click(); pg.wait_for_timeout(200)
    pop = ev("() => { const p = document.querySelector('.shift-pop'); if (!p) return null; return [p.querySelector('.lbl').textContent, [...p.querySelectorAll('.sp-b')].map(b => b.textContent + ':' + b.getAttribute('aria-pressed'))]; }")
    ok(f'a click on it opens the three-part pick, "Give it a shift" over the three ({pop})', pop == ['Give it a shift', ['Create:false', 'Think:false', 'Errand:false']])
    hb, pb = hol.bounding_box(), pg.locator('.shift-pop').bounding_box()
    ok(f"under the mark, its right edge on the mark's ({hb}, {pb})", abs((pb['x'] + pb['width']) - (hb['x'] + hb['width'])) <= 1 and pb['y'] >= hb['y'] + hb['height'])
    ok('the focus on Create, the mark marked open, and no task panel opened', act() == 'create' and hol.get_attribute('aria-expanded') == 'true'
       and not ev("() => !!document.querySelector('#pvSide .pv-shift-row')"))
    pg.keyboard.press('ArrowLeft')
    ok('the arrow keys move along it, round from Create to Errand', act() == 'errand')
    pg.keyboard.press('ArrowRight')
    ok('and back', act() == 'create')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes it with nothing set, the focus back on the mark', not pg.is_visible('.shift-pop') and 'shift' not in get(gp, 'Add plant icons')
       and ev("() => document.activeElement.classList.contains('none')") and hol.get_attribute('aria-expanded') == 'false' and ev("() => FullView.isOpen()"))
    hol.click(); pg.wait_for_timeout(150)
    hol.click(); pg.wait_for_timeout(150)
    ok('a second click on the mark closes it', not pg.is_visible('.shift-pop'))
    hol.click(); pg.wait_for_timeout(150)
    pg.mouse.click(1000, 120); pg.wait_for_timeout(150)
    ok('so does a click elsewhere', not pg.is_visible('.shift-pop') and 'shift' not in get(gp, 'Add plant icons'))
    hol.click(); pg.wait_for_timeout(150)
    pg.screenshot(path=str(SHOTS / '487-shift-pick.png'))
    pg.click('.shift-pop .sp-b[data-shift="think"]'); pg.wait_for_timeout(250)
    ok('a pick gives the task its shift and closes', get(gp, 'Add plant icons').get('shift') == 'think' and not pg.is_visible('.shift-pop'))
    ok('the row wears its small mark now, the focus on its title', rows()['Add plant icons'] == 'shift-mark small shift-think row-shift'
       and ev("() => document.activeElement.className") == 'task-title' and ev("() => document.activeElement.textContent") == 'Add plant icons')
    ok('not work: Updated and Activity stay', ev(f"() => getProject('{gp}').updatedAt") == up and ev(f"() => getProject('{gp}').activity.length") == acts)
    # What is next with no shift: the hollow mark, and its pick
    ev(f"() => {{ const t = {task(gp, 'Draw the beds on a grid')}; delete t.shift; changed(getProject('{gp}'), {{ touch: false }}); FullView.render(); }}"); pg.wait_for_timeout(200)
    ok('C1 What is next with no shift: the hollow mark', ev("() => document.querySelector('.pv-next .pv-next-shift').className") == 'shift-mark none pv-next-shift')
    pg.click('.pv-next .shift-mark.none'); pg.wait_for_timeout(150)
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok('a pick there gives it its shift, the full mark back and the focus on the task', get(gp, 'Draw the beds on a grid').get('shift') == 'create'
       and ev("() => document.querySelector('.pv-next .pv-next-shift').className") == 'shift-mark full shift-create pv-next-shift' and act() == 'pvNextTask')
    # the milestone view
    pg.click('.ms[data-msid] .ms-name-btn'); pg.wait_for_timeout(400)
    mv = ev("() => Object.fromEntries([...document.querySelectorAll('.pv-ms-task')].map(li => [li.querySelector('.pv-ms-text').firstChild.textContent, ((li.querySelector('.shift-mark') || {}).className || '')]))")
    ok(f'B1 the milestone view: the small mark after an open task ({mv})', mv.get('Save a plan as a file') == 'shift-mark small shift-think pv-ms-shift'
       and mv.get('Add plant icons') == 'shift-mark small shift-think pv-ms-shift')
    ok('C1 and nothing on a done task, nor a hollow mark', mv.get('Tune the watering reminders') == '' and not ev("() => !!document.querySelector('.pv-ms-tasks .shift-mark.none')"))

    # ---------- the three-part pick in the task panel (Round 1, A1) ----------
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ev(f"() => FullView.openTask('{gp}', {task(gp, 'Publish the app')}.id)"); pg.wait_for_timeout(500)
    pk = ev("""() => [...document.querySelectorAll('#pvSide .pv-shift-row .shift-pick .sp-b')].map(b => { const cs = getComputedStyle(b);
      return [b.textContent, b.getAttribute('aria-pressed'), cs.backgroundColor, cs.color, !!b.querySelector('svg')]; })""")
    ok(f"the task panel's Shift row is the three-part pick, each with its icon ({[x[:2] for x in pk]})", [x[0] for x in pk] == ['Create', 'Think', 'Errand'] and all(x[4] for x in pk))
    ok('the one picked fills with its color, its name in ink; the others in their color', pk[2][1:4] == ['true', COLORS['errand'], INK]
       and pk[0][2] == 'rgba(0, 0, 0, 0)' and pk[0][3] == COLORS['create'] and pk[1][3] == COLORS['think'])
    pg.screenshot(path=str(SHOTS / '488-shift-panel.png'), clip={'x': 1000, 'y': 0, 'width': 440, 'height': 400})

    # ---------- Open in Claude opens a Think task on Think (Round 1, C2) ----------
    tab = lambda: ev("() => { const t = document.querySelector('.oc-panel .oc-tab[aria-selected=\"true\"]'); return t ? t.id : null; }")
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
    ok('an Errand task opens on Build it', tab() == 'ocTabBuild')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ev(f"() => FullView.openTask('{gp}', {task(gp, 'Save a plan as a file')}.id)"); pg.wait_for_timeout(500)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
    ok('a Think task opens on Think, the focus on it', tab() == 'ocTabThink' and act() == 'ocTabThink')
    ok('its tiles ask Claude for a wizard round', 'wizard round' in (pg.get_attribute('.oc-panel .oc-tile[data-kind="chat"]', 'title') or ''))
    pg.click('#ocTabBuild'); pg.wait_for_timeout(150)
    ok('one click switches to Build it', tab() == 'ocTabBuild')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
    ok('and the next time it opens on Think again', tab() == 'ocTabThink')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ev("() => FullView.close()"); pg.wait_for_timeout(300)
    pg.click('#dueList .due-item:has-text("Save a plan as a file") .due-claude'); pg.wait_for_timeout(200)
    ok('Due this week\'s Claude icon too', tab() == 'ocTabThink')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # ---------- All tasks: the full mark, the hollow mark, the chips' icons ----------
    ev("() => AllTasks.open()"); pg.wait_for_timeout(500)
    at = ev("() => Object.fromEntries([...document.querySelectorAll('#atList .at-row')].map(r => [r.querySelector('.at-task').firstChild.textContent, ((r.querySelector('.at-meta .shift-mark') || {}).className || '')]))")
    ok(f"B1 All tasks' rows: the full mark ({at})", at['Publish the app'] == 'shift-mark full shift-errand' and at['Build the block art skill'] == 'shift-mark full shift-create')
    ok('C1 and the hollow mark on a row with none, always shown', at['Make block art for each project'] == 'shift-mark none' and pg.locator('#atList .at-row', has_text='Make block art').locator('.shift-mark.none').is_visible())
    chip = ev("() => [...document.querySelectorAll('#atShifts .at-chip')].map(c => c.dataset.shift + ':' + getComputedStyle(c.querySelector('.ic')).color)")
    ok(f"the shift chips wear their icons in their colors, No shift the hollow mark's ({chip})",
       chip == ['create:' + COLORS['create'], 'think:' + COLORS['think'], 'errand:' + COLORS['errand'], 'none:rgb(138, 131, 163)'])
    pg.screenshot(path=str(SHOTS / '489-shift-all.png'))
    pg.locator('#atList .at-row', has_text='Make block art').locator('.shift-mark.none').click(); pg.wait_for_timeout(150)
    pg.keyboard.press('ArrowRight'); pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok('its pick tags the row, the full mark in place of the hollow one', get(nc, 'Make block art for each project').get('shift') == 'think'
       and ev("() => [...document.querySelectorAll('#atList .at-row')].find(r => r.textContent.includes('Make block art')).querySelector('.at-meta .shift-mark').className") == 'shift-mark full shift-think')
    ev("() => AllTasks.close()"); pg.wait_for_timeout(200)

    # ---------- the line over the map: the three-part pick, and + listing the full marks ----------
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.keyboard.type('/garden Buy compost +er'); pg.wait_for_timeout(250)
    sug = ev("() => [...document.querySelectorAll('#qaList .qa-opt .shift-mark')].map(m => m.className + ':' + m.textContent)")
    ok(f'+ lists the shifts with their full marks ({sug})', sug == ['shift-mark full shift-errand:Errand'])
    pg.keyboard.press('Tab'); pg.wait_for_timeout(150)
    qa = ev("() => [...document.querySelectorAll('.qa-shifts .shift-pick .sp-b')].map(b => b.textContent + ':' + b.classList.contains('on') + ':' + getComputedStyle(b).backgroundColor)")
    ok(f'the pick under the line fills the shift the line has ({qa})', qa == ['Create:false:rgba(0, 0, 0, 0)', 'Think:false:rgba(0, 0, 0, 0)', 'Errand:true:' + COLORS['errand']])
    pg.click('.qa-shift[data-shift="create"]'); pg.wait_for_timeout(150)
    ok('a click on another writes its mark, and fills it, the focus kept in the line', pg.input_value('#quickAddIn').endswith('+create ')
       and ev("() => document.querySelector('.qa-shift[data-shift=\"create\"]').classList.contains('on')") and act() == 'quickAddIn')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # ---------- the city skill writes a task's shift (Round 1, C2) ----------
    chk = ROOT / '.claude' / 'skills' / 'nullovation-city' / 'scripts' / 'check_plan.py'
    skill = (ROOT / '.claude' / 'skills' / 'nullovation-city' / 'SKILL.md').read_text(encoding='utf-8')
    ok("the skill says when to give a task a shift, and its version went up", '## A task\'s shift' in skill and '`create`' in skill and '`errand`' in skill
       and 'version: "0.1.0"' not in skill and '0.1.53 for a task\'s shift' in skill)
    def check(data):
        f = ROOT / 'tests' / 'data' / 'shift-check.json'; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps(data), encoding='utf-8')
        return subprocess.run([sys.executable, str(chk), str(f)], capture_output=True, text=True)
    t = lambda **o: dict({'text': 'Buy seed trays', 'description': 'Buy two seed trays.'}, **o)
    ok('its checker takes a shift in a tasks file', check({'app': 'nullovation-city', 'kind': 'tasks', 'version': 1, 'tasks': [t(shift='errand')]}).returncode == 0)
    ok('and in an update\'s add-tasks', check({'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'x',
       'changes': [{'do': 'add-tasks', 'tasks': [t(shift='think')]}]}).returncode == 0)
    bad = check({'app': 'nullovation-city', 'kind': 'tasks', 'version': 1, 'tasks': [t(shift='Create'), t(text='Plan it', shift='design')]})
    ok('and refuses one it does not know, in words or another name', bad.returncode != 0 and bad.stdout.count('shift, when given, is one of create, think, errand') == 2)
    ok('the city reads the shift Claude writes', ev("() => readTasks({ tasks: [{ text: 'a', description: 'b', shift: 'errand' }] }).tasks[0].shift") == 'errand')
    ctx.close()

    # ---------- on a phone: the hollow mark answers a finger, the pick is a finger's size, back closes it ----------
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    ev("() => document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true)")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    hol = pg.locator('.task', has_text='Add plant icons').locator('.shift-mark.none')
    hol.scroll_into_view_if_needed(); hb = hol.bounding_box()
    pg.touchscreen.tap(hb['x'] + hb['width'] + 4, hb['y'] + hb['height'] / 2); pg.wait_for_timeout(300)
    ok('a tap 4 px beside the hollow mark opens its pick', pg.is_visible('.shift-pop'))
    pb = pg.locator('.shift-pop').bounding_box()
    hs = ev("() => [...document.querySelectorAll('.shift-pop .sp-b')].map(b => Math.round(b.getBoundingClientRect().height))")
    ok(f"its buttons a finger's size, the pick inside the screen ({hs}, {pb})", all(x >= 30 for x in hs) and pb['x'] >= 0 and pb['x'] + pb['width'] <= 390)
    pg.screenshot(path=str(SHOTS / '484-shift-phone.png'))
    pg.go_back(); pg.wait_for_timeout(400)
    ok("a phone's back closes the pick, the project view staying", not pg.is_visible('.shift-pop') and ev("() => FullView.isOpen()") and 'shift' not in (ev(f"() => JSON.parse(JSON.stringify({task(gp, 'Add plant icons')}))") or {}))
    pg.touchscreen.tap(hb['x'] + hb['width'] / 2, hb['y'] + hb['height'] / 2); pg.wait_for_timeout(300)
    bb = pg.locator('.shift-pop .sp-b[data-shift="errand"]').bounding_box()
    pg.touchscreen.tap(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2); pg.wait_for_timeout(300)
    ok('a tap on a shift gives it', ev(f"() => {task(gp, 'Add plant icons')}.shift") == 'errand' and not pg.is_visible('.shift-pop'))
    b.close()

bad = [e for e in errors if 'favicon' not in e]
ok('no console errors' + (': ' + ' | '.join(bad[:3]) if bad else ''), not bad)
