"""Tasks on the map (Tasks, Round 2, M1 to M6): hovering a building shows its open tasks and its next task, a project
can pin its next task, and one task in the whole city can wear the star."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    left = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    proj = lambda pid: ev(f"() => JSON.parse(JSON.stringify(getProject('{pid}')))")
    tid = lambda pid, text: ev(f"() => getProject('{pid}').todos.find(t => t.text === {json.dumps(text)}).id")
    task = lambda pid, text: f"getProject('{pid}').todos.find(t => t.text === {json.dumps(text)})"
    bubbles = lambda pid: ev(f"() => MapView._bubblesOf('{pid}')")
    kinds = lambda pid: [x['kind'] for x in bubbles(pid)]
    label = lambda: (pg.text_content('#hoverTask') or '') if pg.is_visible('#hoverTask') else None

    # ---------- the model: pins and the star ----------
    ok('a project starts with no pin and no star', proj(gp)['pin'] == '' and proj(gp)['star'] == '')
    ok('with no pin, the next task is the first open one in the current milestone', ev(f"() => nextTask(getProject('{gp}')).text") == 'Draw the beds on a grid')
    ev(f"() => setPin(getProject('{gp}'), {task(gp, 'Add plant icons')}, true)")
    ok('M4 a pin makes its task the next one', ev(f"() => nextTask(getProject('{gp}')).text") == 'Add plant icons')
    ok('M4 the pinned task comes first in the status card’s list', ev(f"() => bubbleTodos(getProject('{gp}')).list.map(t => t.text)") ==
       ['Add plant icons', 'Draw the beds on a grid', 'Save a plan as a file'])
    ev(f"() => setPin(getProject('{gp}'), {task(gp, 'Publish the app')}, true)")
    ok('one pin per project: pinning another task moves it', proj(gp)['pin'] == tid(gp, 'Publish the app'))
    ok('a pinned task from another milestone still comes first', ev(f"() => bubbleTodos(getProject('{gp}')).list[0].text") == 'Publish the app')
    ok('a pin is not work: Updated and urgency stay as they were', ev(f"() => getProject('{gp}').urgency.lastWorked") is None)
    ev(f"() => {{ const p = getProject('{gp}'), t = {task(gp, 'Publish the app')}; t.done = true; t.doneAt = Date.now(); changed(p); persistNow(); t.done = false; t.doneAt = null; changed(p); persistNow(); }}")
    ok('M5 ticking the pinned task clears its pin for good: reopening it does not bring the pin back', proj(gp)['pin'] == '')
    ev(f"() => setPin(getProject('{gp}'), {task(gp, 'Add plant icons')}, true)")
    ev(f"() => setPin(getProject('{gp}'), {task(gp, 'Add plant icons')}, false)")
    ok('M5 unpinning clears it', proj(gp)['pin'] == '')

    ev(f"() => setStar(getProject('{gp}'), {task(gp, 'Add plant icons')}, true)")
    ok('M6 starring a task pins it in its project too', proj(gp)['star'] == proj(gp)['pin'] == tid(gp, 'Add plant icons'))
    ok('the city knows its starred task', ev("() => starredTask().t.text") == 'Add plant icons')
    ev(f"() => setStar(getProject('{nc}'), {task(nc, 'Build the block art skill')}, true)")
    ok('M6 one star in the whole city: starring another task moves it', proj(gp)['star'] == '' and proj(nc)['star'] == tid(nc, 'Build the block art skill'))
    ok('M6 the pin and the star are separate: the first task keeps its pin', proj(gp)['pin'] == tid(gp, 'Add plant icons'))
    ok('the star moving says where it went', 'The star moved to Build the block art skill.' in (pg.text_content('#toast') or ''))
    ev(f"() => setStar(getProject('{nc}'), {task(nc, 'Build the block art skill')}, false)")
    ok('unstarring leaves the pin', proj(nc)['star'] == '' and proj(nc)['pin'] == tid(nc, 'Build the block art skill'))
    ev(f"() => {{ const p = getProject('{nc}'); setStar(p, {task(nc, 'Build the block art skill')}, true); p.todos.splice(p.todos.indexOf({task(nc, 'Build the block art skill')}), 1); changed(p); persistNow(); }}")
    ok('deleting the starred task clears its star and pin', proj(nc)['star'] == '' and proj(nc)['pin'] == '' and ev("() => starredTask()") is None)
    read = ev(f"""() => {{ const r = JSON.parse(JSON.stringify(DB.projects)), a = r.find(p => p.id === '{gp}'), c = r.find(p => p.id === '{nc}');
        a.star = a.todos[0].id; c.star = c.todos[0].id; a.todos[2].done = true; a.pin = a.todos[2].id; c.pin = 'no-such-task';
        const k = sanitizeProjects(r).map(x => x.p); return [k.filter(p => p.star).length, k.find(p => p.id === '{gp}').pin, k.find(p => p.id === '{nc}').pin]; }}""")
    ok(f'reading a city keeps one star, and drops a pin on a done or missing task {read}', read == [1, '', ''])
    ev(f"() => setStar(getProject('{gp}'), {task(gp, 'Save a plan as a file')}, true)")
    ev("() => persistNow()"); pg.reload(); pg.wait_for_timeout(2000)
    ok('the pin and the star survive a reload', proj(gp)['star'] == proj(gp)['pin'] == tid(gp, 'Save a plan as a file'))
    bk = ev(f"async () => {{ const b = await buildBackup(); const q = b.projects.find(p => p.id === '{gp}'); return [q.pin, q.star]; }}")
    ok('a backup and the data file carry them', bk == [tid(gp, 'Save a plan as a file')] * 2)
    ok('the project\u2019s status for Claude names the pinned task as next', 'Next task: Save a plan as a file' in ev(f"() => projectStatusForClaude(getProject('{gp}'))"))
    ev(f"() => {{ const p = getProject('{gp}'); setStar(p, nextTask(p), false); setPin(p, nextTask(p), false); }}")

    # ---------- the hover (M1 to M3) ----------
    ev("() => MapView.setBubbleMode('all')")
    ev("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(300)
    a = ev(f"() => MapView.anchors('{gp}')")
    over = (left + a['topX'], (a['topY'] + a['baseY']) / 2)
    away = lambda: (pg.mouse.move(left + 40, 40), pg.wait_for_timeout(250))
    pg.mouse.move(*over); pg.wait_for_timeout(100)
    ok('M2 no hover yet, a moment after the pointer arrives', 'hover' not in kinds(gp) and label() is None)
    pg.wait_for_timeout(400)
    hb = [x for x in bubbles(gp) if x['kind'] == 'hover']
    ok(f'M1 after 250 ms: a white bubble with the open tasks ({hb})', len(hb) == 1 and hb[0]['color'] == 'grey' and hb[0]['text'] == '5')
    ok(f'M1 and the next task in one line under it ({label()})', label() == 'Draw the beds on a grid')
    lb = pg.query_selector('#hoverTask').bounding_box()
    mtop = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().top")
    ok(f"the label sits just under the bubble, centred on it ({lb['x'] + lb['width'] / 2 - left - a['topX']:.1f}, {lb['y'] - mtop - a['topY']:.1f})",
       abs(lb['x'] + lb['width'] / 2 - (left + a['topX'])) <= 2 and abs(lb['y'] - (mtop + a['topY'] - 4)) <= 3)
    pg.screenshot(path=str(SHOTS / '270-hover.png'), clip={'x': left + a['topX'] - 200, 'y': a['topY'] - 120, 'width': 400, 'height': 260})
    away()
    ok('leaving the building takes the hover away', 'hover' not in kinds(gp) and label() is None)

    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'finish', days: 1, lastWorked: Date.now() - 3 * 86400000, pickedAt: Date.now() - 4 * 86400000 }}; changed(p); }}")
    pg.wait_for_timeout(200)
    before = [x for x in bubbles(gp) if x['kind'] == 'urgency']
    pg.mouse.move(*over); pg.wait_for_timeout(500)
    after = bubbles(gp)
    urg = [x for x in after if x['kind'] == 'urgency']
    ok('the bubbles already there stay where they are', before and urg and before[0]['x'] == urg[0]['x'] and before[0]['y'] == urg[0]['y'])
    ok('the white count joins on their left', after[0]['kind'] == 'hover' and after[0]['x'] + after[0]['w'] <= urg[0]['x'])
    ev("() => MapView.setBubbleMode('tasks')"); pg.wait_for_timeout(250)
    ok(f'in the Tasks view the count is already there, so only the label is added {kinds(gp)}', kinds(gp) == ['urgency'] and bubbles(gp)[0]['color'] == 'grey' and label() == 'Draw the beds on a grid')
    ev("() => MapView.setBubbleMode('none')"); pg.wait_for_timeout(250)
    ok(f'M3 with No bubbles the hover still shows, on demand {kinds(gp)}', kinds(gp) == ['hover'] and label() == 'Draw the beds on a grid')
    ev("() => MapView.setBubbleMode('all')")
    long = 'Measure every bed twice and write the sizes on the plan'
    ev(f"() => {{ const p = getProject('{gp}'); {task(gp, 'Draw the beds on a grid')}.text = {json.dumps(long)}; changed(p); }}"); pg.wait_for_timeout(250)
    ok(f'a long next task is cut short at 40 characters ({label()})', label() == long[:39].rstrip() + '…' and pg.get_attribute('#hoverTask', 'title') == long)
    ev(f"() => {{ const p = getProject('{gp}'); {task(gp, long)}.text = 'Draw the beds on a grid'; setPin(p, {task(gp, 'Save a plan as a file')}, true); }}"); pg.wait_for_timeout(250)
    ok('the label shows the pinned task, with a pin', label() == 'Save a plan as a file' and pg.locator('#hoverTask .ic').count() == 1)
    pg.screenshot(path=str(SHOTS / '271-hover-pinned.png'), clip={'x': left + a['topX'] - 200, 'y': a['topY'] - 120, 'width': 400, 'height': 260})
    away()
    ev(f"() => {{ const p = getProject('{gp}'); p.todos.forEach(t => {{ t.done = true; t.doneAt = Date.now(); }}); changed(p); }}"); pg.wait_for_timeout(150)
    pg.mouse.move(*over); pg.wait_for_timeout(500)
    ok('with every task done: a 0, and no label', [x['text'] for x in bubbles(gp) if x['kind'] == 'hover'] == ['0'] and label() is None)
    away()
    ev(f"() => {{ const p = getProject('{gp}'); p.todos.forEach(t => {{ t.done = false; t.doneAt = null; }}); p.urgency.system = 'none'; changed(p); }}")
    pg.mouse.click(*over); pg.wait_for_timeout(600)
    ok('not on the selected building, whose card is open', pg.is_visible('#bubble') and 'hover' not in kinds(gp) and label() is None)
    ev("() => MapView.deselect()"); away()
    ev("() => MapView.setEditing(true)"); pg.wait_for_timeout(300)
    a2 = ev(f"() => MapView.anchors('{gp}')")
    pg.mouse.move(left + a2['topX'], (a2['topY'] + a2['baseY']) / 2); pg.wait_for_timeout(500)
    ok('not in Edit City', 'hover' not in kinds(gp) and label() is None)
    ev("() => MapView.setEditing(false)"); away()
    ev("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(300)

    # ---------- the star on the map (M6) ----------
    ev(f"() => setStar(getProject('{gp}'), {task(gp, 'Add plant icons')}, true)"); pg.wait_for_timeout(200)
    ok('M6 the starred task’s building wears the star', 'star' in kinds(gp) and 'star' not in kinds(nc))
    ev("() => MapView.setBubbleMode('red')")
    ok('the star shows with Red only', 'star' in kinds(gp))
    ev("() => MapView.setBubbleMode('tasks')")
    ok('and in the Tasks view, beside the count', kinds(gp) == ['urgency', 'star'])
    ev("() => MapView.setBubbleMode('none')")
    ok('No bubbles hides it', kinds(gp) == [])
    ev("() => MapView.setBubbleMode('all')"); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SHOTS / '272-star.png'), clip={'x': left + a['topX'] - 200, 'y': a['topY'] - 120, 'width': 400, 'height': 260})
    ev(f"() => {{ const p = getProject('{gp}'), t = {task(gp, 'Add plant icons')}; t.done = true; t.doneAt = Date.now(); changed(p); persistNow(); }}"); pg.wait_for_timeout(200)
    ok('M5 ticking the starred task takes the star off the map', 'star' not in kinds(gp) and proj(gp)['star'] == '')
    ev(f"() => {{ const p = getProject('{gp}'), t = {task(gp, 'Add plant icons')}; t.done = false; t.doneAt = null; changed(p); }}")

    # ---------- the star's own color (0.1.40) ----------
    ok('A1 A2 the star is gold again, as at 0.1.39', ev("() => ICON_ACCENT.star") == '#FFD23F')

    # ---------- pins in the status card (M4); the star is set only in the task panel (0.1.40) ----------
    pg.mouse.click(*over); pg.wait_for_timeout(600)
    rows = lambda: pg.eval_on_selector_all('#bubble .b-todos li', 'els => els.map(e => e.querySelector(".b-task").textContent.trim())')
    ok('every open row in the card has a pin, and no star', pg.locator('#bubble .b-todos li .mark-pin').count() == 3 and pg.locator('#bubble .mark-star').count() == 0)
    ok('they stay out of sight until the row is pointed at', ev("() => getComputedStyle(document.querySelector('#bubble .b-todos li .mark-pin')).opacity") == '0')
    save_row = pg.locator('#bubble .b-todos li', has_text='Save a plan as a file')
    save_row.hover(); pg.wait_for_timeout(100)
    ok('pointing at a row shows them', float(ev("() => getComputedStyle(document.querySelectorAll('#bubble .b-todos li')[1].querySelector('.mark-pin')).opacity")) > 0)
    save_row.locator('.mark-pin').click(); pg.wait_for_timeout(250)
    ok('M4 a pin in the card pins the task', proj(gp)['pin'] == tid(gp, 'Save a plan as a file'))
    ok(f'and the card puts it first {rows()}', rows()[0] == 'Save a plan as a file')
    ok('a pressed pin stays in view, and says so', pg.get_attribute('#bubble .b-todos li >> nth=0 >> .mark-pin', 'aria-pressed') == 'true'
       and ev("() => getComputedStyle(document.querySelector('#bubble .b-todos li .mark-pin')).opacity") == '1')
    ok('the focus stays on the pin', ev("() => document.activeElement && document.activeElement.dataset.mark") == 'pin')
    pg.screenshot(path=str(SHOTS / '273-card-marks.png'), clip=pg.query_selector('#bubble').bounding_box())
    ev(f"() => setStar(getProject('{gp}'), {task(gp, 'Draw the beds on a grid')}, true)"); pg.wait_for_timeout(250)
    ok('the card still has no star once a task in it is starred', pg.locator('#bubble .mark-star').count() == 0 and proj(gp)['star'] == proj(gp)['pin'] == tid(gp, 'Draw the beds on a grid'))

    # ---------- the starred task in the side bar (0.1.40) ----------
    card = '#sbStar .star-card'
    ok('the side bar shows the starred task', pg.is_visible(card) and pg.text_content('#sbStar .star-text').strip() == 'Draw the beds on a grid')
    ok('with its project and its building', pg.text_content('#sbStar .star-proj').strip() == 'Garden planner' and pg.locator('#sbStar .star-thumb canvas.thumb').count() == 1)
    ok('it says Starred, with the star', pg.text_content('#sbStar .star-top').strip() == 'Starred' and pg.locator('#sbStar .star-top svg').count() == 1)
    ok('A2 the card is purple with a gold edge', ev("() => { const c = getComputedStyle(document.querySelector('#sbStar .star-card')); return [c.backgroundColor, c.boxShadow.startsWith('rgb(255, 210, 63) 0px 0px 0px 2px')]; }") == ['rgb(58, 39, 102)', True])
    order = ev("() => ['#search', '#btnStar', '#btnRecap'].map(s => document.querySelector(s).getBoundingClientRect().top)")
    ok(f'it sits under search, over This week {order}', order[0] < order[1] < order[2])
    pg.screenshot(path=str(SHOTS / '275-side-star.png'), clip=pg.query_selector('#sbStar').bounding_box())
    ev(f"() => setStar(getProject('{nc}'), getProject('{nc}').todos.find(t => !t.done), true)"); pg.wait_for_timeout(200)
    ok('it follows the star when it moves', pg.text_content('#sbStar .star-proj').strip() == 'Nullovation City')
    ev(f"() => setStar(getProject('{nc}'), starredTask().t, false)"); pg.wait_for_timeout(200)
    ok('unstarred, the side bar lets it go', not pg.is_visible('#sbStar'))
    ev(f"() => setStar(getProject('{gp}'), {task(gp, 'Draw the beds on a grid')}, true)"); pg.wait_for_timeout(200)
    pg.click(card); pg.wait_for_timeout(900)
    ok('a click on it opens the task, in its project', ev("() => FullView.isOpen()") and pg.text_content('#pvTitle').strip() == 'Garden planner'
       and pg.locator('#pvSide #pvTaskDesc').count() == 1 and pg.input_value('#pvSide #pvTaskTitle') == 'Draw the beds on a grid')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # ---------- the project view (M4): rows, What is next, the task panel ----------
    ok('Esc closes the task, leaving its project open', ev("() => FullView.isOpen()") and pg.locator('#pvSide #pvTaskDesc').count() == 0)
    pin_chip = '.pv-next-head .pv-next-marks .mark-pin'
    ok('What is next shows the pinned task, and its pin says Pinned at the top right', pg.text_content('#pvNextTask').strip() == 'Draw the beds on a grid'
       and pg.get_attribute(pin_chip, 'aria-pressed') == 'true' and (pg.text_content(pin_chip) or '').strip() == 'Pinned')
    ok('A3 a starred task says Starred beside the pin, as a mark, not a button', (pg.text_content('.pv-next-marks .pv-starred') or '').strip() == 'Starred'
       and pg.locator('.pv-next .mark-star').count() == 0)
    st = ev("() => { const c = getComputedStyle(document.querySelector('.pv-next')); return [document.querySelector('.pv-next').classList.contains('starred'), c.backgroundColor, c.boxShadow]; }")
    ok(f'A2 while its task wears the star, What is next is purple with a gold edge {st[:2]}', st[0] and st[1] == 'rgb(58, 39, 102)' and 'rgb(255, 210, 63)' in st[2])
    pg.screenshot(path=str(SHOTS / '276-next-starred.png'), clip=pg.query_selector('.pv-next').bounding_box())
    ok('no row in the project view has a star button', pg.locator('#pv .mark-star').count() == 0 and pg.locator('li.task .mark-pin').count() > 0)
    pg.locator('li.task', has_text='Publish the app').locator('.mark-pin').click(); pg.wait_for_timeout(300)
    ok('M4 a pin on a task row pins it', proj(gp)['pin'] == tid(gp, 'Publish the app') and pg.text_content('#pvNextTask').strip() == 'Publish the app')
    ok('What is next names the pinned task’s own milestone', 'Launch' in pg.text_content('.pv-next-ms'))
    ok('a pin click neither opens the task nor drags the row', pg.locator('#pvSide #pvTaskDesc').count() == 0)
    ok('the star stays on its task: the two are separate', proj(gp)['star'] == tid(gp, 'Draw the beds on a grid'))
    pg.screenshot(path=str(SHOTS / '274-next-pinned.png'), clip=pg.query_selector('.pv-next').bounding_box())
    bg = ev("() => [getComputedStyle(document.querySelector('.pv-next')).backgroundColor, getComputedStyle(document.querySelector('#pv')).backgroundColor]")
    ok(f'unstarred, What is next has its own shade, not the star\'s {bg}', bg[0] not in ('rgba(0, 0, 0, 0)', bg[1], 'rgb(58, 39, 102)') and pg.locator('.pv-next-marks .pv-starred').count() == 0)
    pg.click(pin_chip); pg.wait_for_timeout(300)
    ok('M4 the pin in What is next unpins it, and turns back into a plain pin', proj(gp)['pin'] == '' and pg.get_attribute(pin_chip, 'aria-pressed') == 'false'
       and (pg.text_content(pin_chip) or '').strip() == '' and pg.text_content('#pvNextTask').strip() == 'Draw the beds on a grid')
    foc = ev("() => { const a = document.activeElement; return a ? [a.tagName, a.className, a.id] : null; }")
    ok(f'the focus stays on the pin {foc}', ev("() => document.activeElement && document.activeElement.matches('.pv-next-marks .mark-pin')"))

    # ---------- What is next, layout B (A3): the due date beside the milestone, nothing without one ----------
    order = ev("() => [...document.querySelector('.pv-next').children].map(e => e.className.split(' ')[0] || e.id)")
    ok(f'A3 the label and marks, the milestone line, the task, then the actions {order}', order[:4] == ['pv-next-head', 'pv-next-msrow', 'pv-next-task', 'pv-next-row'])
    nxt = task(gp, 'Draw the beds on a grid')
    ok('no due date: nothing says so', 'No due date' not in pg.text_content('.pv-next') and pg.locator('.pv-next-due').count() == 0)
    for days, want in ((4, 'Due ' + ev("() => new Date(Date.now() + 4 * 864e5).toLocaleDateString('en-GB', { weekday: 'short' })") + ' '), (1, 'Due tomorrow'), (-2, '2 days overdue')):
        ev(f"() => {{ const p = getProject('{gp}'); {nxt}.due = ymd(Date.now() + {days} * 864e5); changed(p); FullView.render(); }}"); pg.wait_for_timeout(250)
        due = (pg.text_content('.pv-next-msrow .pv-next-due') or '').strip()
        right = ev("() => { const r = document.querySelector('.pv-next-msrow').getBoundingClientRect(), d = document.querySelector('.pv-next-due').getBoundingClientRect(); return Math.abs(r.right - d.right) < 2; }")
        ok(f'a due date in {days} days sits at the right of the milestone line: {due}', due.startswith(want) and right)
    ok('overdue, the chip is red and the task has its !', 'late' in pg.get_attribute('.pv-next-due', 'class') and pg.locator('.pv-next-task.late .pv-late-mark').count() == 1)
    one_row = ev("() => { const b = [...document.querySelectorAll('.pv-next-row > *')].map(e => e.getBoundingClientRect().top); return b.length === 2 && Math.abs(b[0] - b[1]) < 2; }")
    ok('Copy task and Open in Claude share one row', one_row)
    pg.screenshot(path=str(SHOTS / '277-next-overdue.png'), clip=pg.query_selector('.pv-next').bounding_box())
    ev(f"() => {{ const p = getProject('{gp}'); {nxt}.due = null; changed(p); FullView.render(); }}"); pg.wait_for_timeout(250)
    pg.click('li.task:has-text("Add plant icons") .task-title'); pg.wait_for_timeout(500)
    pin_btn, star_btn = '#pvSide .pv-mark[data-mark="pin"]', '#pvSide .pv-mark[data-mark="star"]'
    ok('M4 the task panel has Pin as next and Star for the city', (pg.text_content(pin_btn) or '').strip() == 'Pin as next' and (pg.text_content(star_btn) or '').strip() == 'Star for the city')
    pg.click(pin_btn); pg.wait_for_timeout(250)
    ok('Pin as next pins it, and turns into Pinned', proj(gp)['pin'] == tid(gp, 'Add plant icons') and (pg.text_content(pin_btn) or '').strip() == 'Pinned' and pg.get_attribute(pin_btn, 'aria-pressed') == 'true')
    pg.click(star_btn); pg.wait_for_timeout(250)
    ok('Star for the city moves the star here', proj(gp)['star'] == tid(gp, 'Add plant icons') and (pg.text_content(star_btn) or '').strip() == 'Starred')
    ok('and the side bar shows it', pg.text_content('#sbStar .star-text').strip() == 'Add plant icons')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc, which undoes the task’s edits, leaves the pin and the star alone', proj(gp)['pin'] == proj(gp)['star'] == tid(gp, 'Add plant icons'))
    pg.locator('li.task', has_text='Add plant icons').locator('.cb').check(); pg.wait_for_timeout(400)
    ok('a done task has no pin or star buttons (its archive button since 0.1.49)', pg.locator('li.task.done', has_text='Add plant icons').locator('.task-mark:not(.mark-archive)').count() == 0)
    ok('M5 and ticking it in the list clears both', proj(gp)['pin'] == '' and proj(gp)['star'] == '')
    ok('done, it leaves the side bar', not pg.is_visible('#sbStar'))
    ev(f"() => setStar(getProject('{gp}'), {task(gp, 'Save a plan as a file')}, true)"); pg.wait_for_timeout(200)
    pg.locator('li.task:has-text("Save a plan as a file") .task-title').click(); pg.wait_for_timeout(500)
    pg.click(star_btn); pg.wait_for_timeout(250)
    ok('Starred in the task panel unstars it, and the side bar lets it go', proj(gp)['star'] == '' and (pg.text_content(star_btn) or '').strip() == 'Star for the city' and not pg.is_visible('#sbStar'))
    ev(f"() => {{ const p = getProject('{gp}'); setStar(p, {task(gp, 'Save a plan as a file')}, true); p.todos.splice(p.todos.indexOf({task(gp, 'Save a plan as a file')}), 1); changed(p); }}"); pg.wait_for_timeout(200)
    ok('deleting the starred task takes it out of the side bar', not pg.is_visible('#sbStar'))
    b.close()
print(errors or 'no console errors')
