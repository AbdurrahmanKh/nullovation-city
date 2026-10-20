"""All tasks (All tasks, Rounds 1 to 3): every open task in the city in one list, in the side bar like Settings and
Reports, with shifts: Create, Think or Errand on a task, one or none."""
import json
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

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
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay').forEach(e => e.hidden = true); }")
    rows = lambda: ev("() => [...document.querySelectorAll('#atList .at-row')].map(r => r.querySelector('.at-task').firstChild.textContent)")
    groups = lambda: ev("() => [...document.querySelectorAll('#atList > section .at-gh, #atList > .at-gh')].map(h => h.firstChild.nodeType === 3 ? h.firstChild.textContent : h.textContent.replace(/\\d+$/, ''))")
    def settle(js):                                      # the words field redraws once typing pauses: wait for it, up to 3 seconds
        try: pg.wait_for_function(js, timeout=3000)
        except Exception: pass
    count_is = lambda n: f"() => document.querySelectorAll('#atList .at-row').length === {n}"
    nth_day = lambda n: (date.today() + timedelta(days=n)).isoformat()
    quiet()

    # ---------- the shift on a task: the model ----------
    m = ev("() => readTaskMarks('+create Fix the export')")
    ok('+create in a line gives the shift and leaves the title', m['shift'] == 'create' and m['title'] == 'Fix the export')
    ok('the start of a shift is enough: +t is Think, +err is Errand',
       ev("() => readTaskMarks('Plan it +t').shift") == 'think' and ev("() => readTaskMarks('+err Buy milk').shift") == 'errand')
    ok('a + word that names no shift stays in the title, and so do +1 and C++ (K4: none can be added)',
       ev("() => { const r = readTaskMarks('Learn +music in C++ for +1 day'); return r.shift === '' && r.title === 'Learn +music in C++ for +1 day'; }"))
    ok('the line under an add field says the shift it read', 'Shift: Errand' in ev(f"() => readTaskLine('Buy seeds +errand', {{ project: getProject('{gp}') }}).parts.join(' | ')"))
    ok('the empty field names the mark', ev("() => { const el = document.createElement('p'); taskLineHint(el, '', {}); return el.textContent; }").endswith('+create shift'))
    ok('reading a city keeps a shift and drops one it does not know (K4)',
       ev("() => { const ps = sanitizeProjects([{ name: 'X', todos: [{ text: 'a', shift: 'think' }, { text: 'b', shift: 'banana' }], milestones: [] }]).map(x => x.p); return ps[0].todos[0].shift === 'think' && !('shift' in ps[0].todos[1]); }"))
    ok('a tasks file and a plan carry a shift',
       ev("() => readTasks({ tasks: [{ text: 'a', shift: 'errand' }, { text: 'b', shift: 'x' }] }).tasks.map(t => t.shift).join(',')") == 'errand,'
       and ev("() => readPlan({ name: 'P', milestones: [{ name: 'M', tasks: [{ text: 'a', shift: 'create' }] }] }).milestones[0].tasks[0].shift") == 'create')

    # the city for the rest: dated tasks, shifts, a star, a building behind its pace
    ev(f"""() => {{
      const P = getProject('{gp}'), N = getProject('{nc}');
      const T = (p, text) => p.todos.find(t => t.text === text);
      Object.assign(T(P, 'Draw the beds on a grid'), {{ due: '{nth_day(-3)}', shift: 'create' }});
      Object.assign(T(P, 'Save a plan as a file'), {{ due: '{nth_day(0)}', shift: 'create', description: 'Write it as JSON next to the beds' }});
      Object.assign(T(N, 'Try the project view for a week'), {{ due: '{nth_day(1)}', shift: 'think' }});
      Object.assign(T(P, 'Publish the app'), {{ due: '{nth_day(30)}', shift: 'errand' }});
      Object.assign(T(N, 'Build the block art skill'), {{ shift: 'create' }});
      Object.assign(T(N, 'Round 3: decide the block art loop'), {{ shift: 'think' }});
      const ms = N.todos[0].milestoneId;
      for (const x of ['Extra one', 'Extra two', 'Extra three']) N.todos.push(Object.assign(todo(x, ms)));
      normalizeOrder(N);
      setStar(N, T(N, 'Build the block art skill'), true);
      N.urgency = {{ system: 'pace', days: 1, lastWorked: Date.now() - 6 * 86400000, pickedAt: Date.now() - 20 * 86400000 }};
      changed(N); changed(P);
    }}""")
    quiet()
    ok('the city: Nullovation City is behind its pace', ev(f"() => Garbage.breakdown(getProject('{nc}')).sys > 0"))

    copy = ev(f"() => taskForClaude(getProject('{nc}'), {task(nc, 'Try the project view for a week')})")
    ok('Copy task carries the shift', 'Shift: Think' in copy)
    ok('and a task with none carries no Shift line', 'Shift:' not in ev(f"() => taskForClaude(getProject('{gp}'), {task(gp, 'Add plant icons')})"))
    mcopy = ev(f"() => milestoneForClaude(getProject('{gp}'), getProject('{gp}').milestones[0])")
    ok("a milestone's copy names each open task's shift", '### Draw the beds on a grid' in mcopy and mcopy.count('Shift: Create') == 2)
    summ = ev("() => ClaudeWork.citySummary()")
    open_gp = [t for g in next(x for x in summ['projects'] if x['name'] == 'Garden planner')['milestones'] for t in g['open']]
    ok("the summary for Claude has each open task's shift, in words", next(t for t in open_gp if t['task'] == 'Publish the app')['shift'] == 'Errand'
       and 'shift' not in next(t for t in open_gp if t['task'] == 'Add plant icons'))
    before = ev(f"() => [getProject('{gp}').updatedAt, getProject('{gp}').activity.length]")
    ev(f"() => setShift(getProject('{gp}'), {task(gp, 'Tune the watering reminders')}, 'think')")
    ok('setting a shift is not work: Updated and Activity stay', ev(f"() => [getProject('{gp}').updatedAt, getProject('{gp}').activity.length]") == before
       and get(gp, 'Tune the watering reminders')['shift'] == 'think')
    ev(f"() => setShift(getProject('{gp}'), {task(gp, 'Tune the watering reminders')}, '')")
    ok('and an empty one takes it off', 'shift' not in get(gp, 'Tune the watering reminders'))

    # ---------- where a shift shows ----------
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(500)
    ok("the status card's row wears its tag", ev("() => { const li = [...document.querySelectorAll('#bubble .b-todos li')].find(l => l.textContent.includes('Draw the beds')); return !!li && li.querySelector('.shift-tag.shift-create').textContent === 'Create'; }"))
    pg.fill('#bubble .b-add input', 'Buy seed packets +errand'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    ok("the status card's add field reads +errand", (get(gp, 'Buy seed packets') or {}).get('shift') == 'errand')
    ev("() => MapView.deselect()")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    ok("the project view's row wears its tag", ev("() => { const r = [...document.querySelectorAll('.task')].find(l => l.textContent.includes('Publish the app')); return !!r && !!r.querySelector('.shift-tag.shift-errand'); }"))
    ev(f"() => FullView.close()"); pg.wait_for_timeout(200)
    ev(f"() => FullView.open('{nc}')"); pg.wait_for_timeout(600)
    ok('What is next wears the tag of its task', ev("() => { const b = document.querySelector('.pv-next'); return !!b && b.textContent.includes('Build the block art skill') && !!b.querySelector('.pv-next-shift.shift-create'); }"))
    ev(f"() => FullView.close()"); pg.wait_for_timeout(200)

    # the task panel's Shift row: a click picks, a second click takes it off, Esc undoes, and alone it is not work
    up = ev(f"() => getProject('{gp}').updatedAt")
    ev(f"() => FullView.openTask('{gp}', {task(gp, 'Publish the app')}.id)"); pg.wait_for_timeout(600)
    ok('the task panel has a Shift row with the three, its own pressed',
       ev("() => [...document.querySelectorAll('#pvSide .pv-shift')].map(b => b.dataset.shift + ':' + b.getAttribute('aria-pressed')).join(' ')") == 'create:false think:false errand:true')
    pg.click('#pvSide .pv-shift[data-shift="think"]'); pg.wait_for_timeout(150)
    ok('a click picks another, and the focus stays on it', get(gp, 'Publish the app')['shift'] == 'think'
       and ev("() => document.activeElement.dataset.shift") == 'think' and ev("() => document.querySelector('#pvSide .pv-shift[data-shift=\"think\"]').getAttribute('aria-pressed')") == 'true')
    pg.click('#pvSide .pv-shift[data-shift="think"]'); pg.wait_for_timeout(150)
    ok('a click on the pressed one takes it off', 'shift' not in get(gp, 'Publish the app'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc in the panel undoes it, as every edit there', get(gp, 'Publish the app')['shift'] == 'errand')
    ev(f"() => FullView.openTask('{gp}', {task(gp, 'Publish the app')}.id)"); pg.wait_for_timeout(500)
    pg.click('#pvSide .pv-shift[data-shift="create"]'); pg.wait_for_timeout(150)
    pg.click('#pvSide .pv-top button[title="Close"]'); pg.wait_for_timeout(300)
    ok('closing the panel after a shift alone leaves Updated', ev(f"() => getProject('{gp}').updatedAt") == up and get(gp, 'Publish the app')['shift'] == 'create')
    pg.screenshot(path=str(SHOTS / '350-task-shift.png'))
    ev(f"() => {{ setShift(getProject('{gp}'), {task(gp, 'Publish the app')}, 'errand'); FullView.close(); }}"); pg.wait_for_timeout(300)
    quiet()

    # ---------- the panel: ways in and out ----------
    foot = ev("() => [...document.querySelectorAll('.sb-foot button')].map(b => b.id)")
    ok('A1 an All tasks button at the side bar\'s foot, before Reports and Settings', foot == ['btnOpenAllTasks', 'btnOpenReports', 'btnOpenSettings'])
    ok('its tooltip names L', ev("() => document.querySelector('#btnOpenAllTasks').title") == 'All tasks (L)')
    ev("() => document.querySelector('#menu').scrollTop = 1e6"); pg.wait_for_timeout(150)
    box = pg.locator('.sb-foot').bounding_box(); pg.screenshot(path=str(SHOTS / '351-foot.png'), clip={'x': 0, 'y': box['y'] - 30, 'width': 292, 'height': box['height'] + 60})
    pg.click('#btnOpenAllTasks'); pg.wait_for_timeout(300)
    ok('L1 the side bar turns into All tasks, with the map in view', pg.is_visible('#allTasks') and not pg.is_visible('#sbLists') and pg.is_visible('#map'))
    ok('the focus goes to the panel, not the field, so L closes it again', ev("() => document.activeElement.id") == 'allTasks')
    pg.click('#atBack'); pg.wait_for_timeout(200)
    ok('the back arrow brings the lists back, the focus on the button', not pg.is_visible('#allTasks') and pg.is_visible('#sbLists') and ev("() => document.activeElement.id") == 'btnOpenAllTasks')
    pg.mouse.click(1000, 120); pg.keyboard.press('Escape')
    pg.keyboard.press('KeyL'); pg.wait_for_timeout(250)
    ok('A1 L opens it', pg.is_visible('#allTasks'))
    pg.mouse.click(1000, 120); pg.keyboard.press('KeyL'); pg.wait_for_timeout(250)
    ok('and L again closes it', not pg.is_visible('#allTasks'))
    pg.keyboard.press('KeyL'); pg.wait_for_timeout(200); pg.mouse.click(1000, 120); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it', not pg.is_visible('#allTasks'))
    pg.click('#search'); pg.keyboard.press('KeyL'); pg.wait_for_timeout(200)
    ok('L typed in a field does nothing', not pg.is_visible('#allTasks') and ev("() => document.querySelector('#search').value") == 'l')
    pg.fill('#search', ''); pg.mouse.click(1000, 120)
    pg.keyboard.press('KeyL'); pg.wait_for_timeout(200); pg.keyboard.press('KeyL'); pg.wait_for_timeout(200)
    ok('L, then L again with nothing in between: open, then closed', not pg.is_visible('#allTasks'))
    pg.mouse.click(1000, 120); pg.keyboard.press('KeyL'); pg.keyboard.press('Comma'); pg.wait_for_timeout(250)
    ok('Settings closes it, as they share the side bar', pg.is_visible('#settings') and not pg.is_visible('#allTasks'))
    pg.mouse.click(1000, 120); pg.keyboard.press('KeyL'); pg.wait_for_timeout(250)
    ok('and it closes Settings', pg.is_visible('#allTasks') and not pg.is_visible('#settings'))
    pg.mouse.click(1000, 120); pg.keyboard.press('KeyR'); pg.wait_for_timeout(250)
    ok('Reports closes it, and back', pg.is_visible('#reports') and not pg.is_visible('#allTasks'))
    pg.mouse.click(1000, 120); pg.keyboard.press('KeyL'); pg.wait_for_timeout(250)
    ok('it closes Reports', pg.is_visible('#allTasks') and not pg.is_visible('#reports') and not pg.is_visible('#sbLists'))
    ev("() => AllTasks.close()"); pg.wait_for_timeout(150)
    ok('the controls guide names L', 'L opens and closes the list' in ev("() => document.querySelector('#setHelp').textContent"))

    # ---------- what it shows ----------
    ev("() => AllTasks.open()"); pg.wait_for_timeout(300)
    today = date.today(); end = today - timedelta(days=(today.weekday() - 5) % 7) + timedelta(days=7)
    week = sum(1 for n in (0, 1) if today + timedelta(days=n) < end)
    ok('D1 the count line: open, overdue, due this week', pg.inner_text('#atSum') == f'13 open, 1 overdue, {week} due this week')
    g = groups()
    ok('B2 the starred task first, in its own purple card', g[0] == 'Starred' and pg.is_visible('#atList .at-star') and rows()[0] == 'Build the block art skill')
    ok('and not again further down', rows().count('Build the block art skill') == 1)
    ok('C1 the dated tasks in day groups, the empty ones left out', g[1:5] == ['Overdue', 'Today', 'Tomorrow', 'Later'])
    ok('each group in order, its rows by date', rows()[1:5] == ['Draw the beds on a grid', 'Save a plan as a file', 'Try the project view for a week', 'Publish the app'])
    meta = lambda text: ev(f"() => {{ const r = [...document.querySelectorAll('#atList .at-row')].find(r => r.querySelector('.at-task').firstChild.textContent === {json.dumps(text)}); return r ? r.querySelector('.at-meta').textContent : null; }}")
    ok('a late task says how late, in red', ev("() => !!document.querySelector('#atList [data-group=\"late\"] .due.late')") and '! 3 days overdue' in meta('Draw the beds on a grid'))
    ok('under Today and Tomorrow, no date chip', ev("() => !document.querySelector('#atList [data-group=\"today\"] .due, #atList [data-group=\"tomorrow\"] .due')"))
    later = (today + timedelta(days=30))
    ok('elsewhere the chip names the day', ev(f"() => weekdayOf('{later.isoformat()}') + ' ' + fmtDate(parseYmd('{later.isoformat()}'))") in meta('Publish the app'))
    ok('B1 a dated row says its project and milestone, after its shift', meta('Draw the beds on a grid').startswith('Create') and 'Garden planner · First release' in meta('Draw the beds on a grid'))
    ok('C2 the undated ones by building, the one behind its pace first', g[5:] == ['No due date', 'Nullovation City', 'Garden planner'])
    nc_rows = ev("() => [...document.querySelectorAll('#atList .at-bld')][0].querySelectorAll('.at-row').length")
    ok("C3 3 a building, in the project's own order, then Show all", nc_rows == 3 and pg.inner_text('#atList .at-bld .at-more') == 'Show all 5'
       and rows()[5:8] == ['Round 3: decide the block art loop', 'Make block art for each project', 'Extra one'])
    ok('an undated row says its milestone only', meta('Make block art for each project') == 'Block art')
    pg.click('#atList .at-more'); pg.wait_for_timeout(200)
    ok('Show all opens the rest in place', ev("() => [...document.querySelectorAll('#atList .at-bld')][0].querySelectorAll('.at-row').length") == 5 and not ev("() => !![...document.querySelectorAll('#atList .at-bld')][0].querySelector('.at-more')"))
    pg.screenshot(path=str(SHOTS / '352-all-tasks.png'))
    hgt = ev("() => document.getElementById('allTasks').getBoundingClientRect().height")
    pg.set_viewport_size({'width': 1440, 'height': int(hgt) + 160}); pg.wait_for_timeout(300)
    pg.screenshot(path=str(SHOTS / '353-all-tasks-list.png'), clip={'x': 0, 'y': 0, 'width': 292, 'height': int(hgt) + 120})
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(200)
    ev("() => AllTasks.close(); AllTasks.open()"); pg.wait_for_timeout(200)
    ok('it opens on everything each time, folds and all (L1: opening on the last pick left out)', ev("() => [...document.querySelectorAll('#atList .at-bld')][0].querySelectorAll('.at-row').length") == 3)

    # the shift chips
    chips = lambda: ev("() => [...document.querySelectorAll('#atShifts .at-chip')].map(c => c.dataset.shift + ':' + c.querySelector('.n').textContent + ':' + c.getAttribute('aria-pressed')).join(' ')")
    ok('L1 a chip for each shift with its count, and No shift', chips() == 'create:3:false think:2:false errand:2:false none:6:false', chips())
    pg.click('#atShifts [data-shift="create"]'); pg.wait_for_timeout(200)
    ok('a click shows one shift across the city', sorted(rows()) == sorted(['Build the block art skill', 'Draw the beds on a grid', 'Save a plan as a file']), rows())
    ok('and the rows drop their tags, every one being that shift', not ev("() => !!document.querySelector('#atList .at-meta .shift-tag')"))
    ok('the count line counts what the list shows', pg.inner_text('#atSum').startswith('3 open, 1 overdue'), pg.inner_text('#atSum'))
    tiles = lambda: ev("() => [...document.querySelectorAll('#atTiles .at-tile[data-p]')].map(t => t.title.split(':')[0] + ':' + t.querySelector('b').textContent).join(' ')")
    ok('L1 the building tiles count the shift picked, and only buildings with one show', tiles() == 'Garden planner:2 Nullovation City:1', tiles())
    pg.screenshot(path=str(SHOTS / '354-create.png'))
    pg.click('#atShifts [data-shift="create"]'); pg.wait_for_timeout(200)
    ok('a second click shows every shift', len(rows()) == 11)

    # A2 the building tiles
    ok('A2 a tile per building with open tasks, by name, after All', tiles() == 'Garden planner:6 Nullovation City:7' and ev("() => document.querySelector('#atTiles .at-tile').textContent") == 'All')
    pg.click(f'#atTiles [data-p="{gp}"]'); pg.wait_for_timeout(200)
    ok('a click on one shows only its tasks', set(ev("() => [...document.querySelectorAll('#atList .at-row')].map(r => r.dataset.p)")) == {gp})
    ok('the chips count within it', chips().startswith('create:2:false think:0:false errand:2:false'), chips())
    pg.click(f'#atTiles [data-p="{gp}"]'); pg.wait_for_timeout(200)
    ok('a second click shows every building again', len(set(ev("() => [...document.querySelectorAll('#atList .at-row')].map(r => r.dataset.p)"))) == 2)
    pg.click(f'#atTiles [data-p="{nc}"]'); pg.wait_for_timeout(200)
    ok('a building picked shows all its undated tasks', ev("() => document.querySelectorAll('#atList .at-bld .at-row').length") == 5 and not ev("() => !!document.querySelector('#atList .at-more')"))
    pg.click('#atTiles .at-tile.all'); pg.wait_for_timeout(200)
    ok('All shows every building', len(rows()) == 11)

    # D1 the words field
    pg.fill('#atFind', 'json'); settle(count_is(1))
    ok('D1 the words field finds a task by its description', rows() == ['Save a plan as a file'])
    pg.fill('#atFind', 'move in'); pg.wait_for_timeout(300); settle(count_is(1))
    ok('by its milestone', rows() == ['Try the project view for a week'])
    pg.fill('#atFind', 'garden'); settle(count_is(6))
    ok('by its project, with nothing folded', len(rows()) == 6 and not ev("() => !!document.querySelector('#atList .at-more')"), rows())
    ok('the focus stays in the field while typing', ev("() => document.activeElement.id") == 'atFind')
    pg.fill('#atFind', 'zzz'); settle("() => !!document.querySelector('#atList .at-empty')")
    ok('nothing fits: it says so, with a way back', pg.inner_text('#atList .at-empty') == 'No task fits.')
    pg.click('#atList button'); pg.wait_for_timeout(200)
    ok('Show every task clears the field', ev("() => document.querySelector('#atFind').value") == '' and len(rows()) == 11)

    # sorting: No shift, and one click on a shift
    pg.click('#atShifts [data-shift="none"]'); pg.wait_for_timeout(200)
    ok('No shift gathers the untagged tasks', rows() == ['Make block art for each project', 'Extra one', 'Extra two', 'Add plant icons', 'Tune the watering reminders'])
    first = pg.locator('#atList .at-row').first
    ok('a row shows no shifts to tag it until pointed at', not first.locator('.at-tagit').is_visible())
    first.hover(); pg.wait_for_timeout(150)
    ok('pointed at, it shows the three', first.locator('.at-tagit').is_visible() and first.locator('.at-tag').all_inner_texts() == ['Create', 'Think', 'Errand'])
    pg.screenshot(path=str(SHOTS / '355-sort.png'))
    up = ev(f"() => getProject('{nc}').updatedAt")
    first.locator('.at-tag', has_text='Errand').click(); pg.wait_for_timeout(200)
    ok('L1 a click tags it, and it leaves the untagged', get(nc, 'Make block art for each project')['shift'] == 'errand' and 'Make block art for each project' not in rows())
    ok('the focus goes on to the next row to sort', ev("() => document.activeElement.textContent") == 'Extra one')
    ok('tagging is not work', ev(f"() => getProject('{nc}').updatedAt") == up)
    pg.click('#atShifts [data-shift="none"]'); pg.wait_for_timeout(200)

    # D1 pointing at a row lights its building; the arrows, Enter and Space
    pg.locator('#atList .at-row', has_text='Publish the app').hover(); pg.wait_for_timeout(150)
    ok('D1 pointing at a row lights its building on the map', ev("() => MapView._lit()") == gp)
    pg.mouse.move(900, 500); pg.wait_for_timeout(150)
    ok('and moving off puts it out', ev("() => MapView._lit()") is None)
    cam0 = ev(f"() => MapView.anchors('{gp}')")
    pg.focus('#atFind'); pg.keyboard.press('ArrowDown')
    ok('D1 the down arrow goes from the field to the first row', ev("() => document.activeElement.textContent") == 'Build the block art skill')
    pg.keyboard.press('ArrowDown')
    ok('and on to the next', ev("() => document.activeElement.textContent") == 'Draw the beds on a grid' and ev("() => MapView._lit()") == gp)
    pg.keyboard.press('ArrowUp'); pg.keyboard.press('ArrowUp')
    ok('up from the first row goes back to the field', ev("() => document.activeElement.id") == 'atFind')
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('ArrowDown'); pg.keyboard.press('ArrowDown')
    ok('the third row', ev("() => document.activeElement.textContent") == 'Save a plan as a file')
    ok('and the map stays where it is: the list keeps its arrow keys', ev(f"() => MapView.anchors('{gp}')") == cam0)
    acts = ev(f"() => getProject('{gp}').activity.length")
    pg.keyboard.press('Space'); pg.wait_for_timeout(150)
    ok('Space ticks it, struck through for a moment', get(gp, 'Save a plan as a file')['done'] and ev("() => !!document.querySelector('#atList .at-row.ticked')")
       and not ev("() => FullView.isOpen()"))
    ok('a tick counts as a tick: its Done line', ev(f"() => getProject('{gp}').activity.slice(-1)[0].text") == 'Done: Save a plan as a file' and ev(f"() => getProject('{gp}').activity.length") == acts + 1)
    pg.wait_for_timeout(900)
    ok('then it goes', 'Save a plan as a file' not in rows())
    pg.focus('#atFind'); pg.keyboard.press('ArrowDown'); pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    enter_ok = ev(f"() => FullView.shows('{gp}')") and ev("() => document.querySelector('#pvTaskTitle').value") == 'Draw the beds on a grid'
    ok('Enter opens the task in its project', enter_ok)
    ev("() => FullView.close()"); pg.wait_for_timeout(200)
    # tagging with the project view open shows there too
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.click('#atShifts [data-shift="none"]'); pg.wait_for_timeout(200)
    row = pg.locator('#atList .at-row', has_text='Add plant icons'); row.hover(); row.locator('.at-tag', has_text='Create').click(); pg.wait_for_timeout(200)
    ok('tagging with the project view open shows the tag there at once', ev("() => { const r = [...document.querySelectorAll('.task')].find(l => l.textContent.includes('Add plant icons')); return !!r && !!r.querySelector('.shift-tag.shift-create'); }"))
    pg.click('#atShifts [data-shift="none"]'); pg.wait_for_timeout(200)
    ev("() => FullView.close()"); pg.wait_for_timeout(200)

    # a tick with the square, a repeat, and what stays out
    ev(f"() => {{ const P = getProject('{gp}'); P.todos.push(Object.assign(todo('Water the beds', P.milestones[0].id), {{ due: '{nth_day(0)}', repeat: {{ every: 'day', n: 1 }} }})); normalizeOrder(P); changed(P); }}")
    pg.wait_for_timeout(200); quiet()
    pg.locator('#atList .at-row', has_text='Water the beds').locator('.cb').click(); pg.wait_for_timeout(100)
    ok('ticked, it holds its place for its moment, struck through', ev("() => { const r = document.querySelector('#atList .at-row.ticked'); return !!r && r.closest('[data-group]').dataset.group; }") == 'today')
    pg.wait_for_timeout(250)
    ok('a repeat ticked here moves on, with its toast', get(gp, 'Water the beds')['waiting'] and 'comes back' in ev("() => document.querySelector('#toast').textContent"))
    pg.wait_for_timeout(900)
    ok('and waits out of the list', 'Water the beds' not in rows())
    ok('done tasks stay out', 'Save a plan as a file' not in rows())
    quiet()

    # the square keeps the focus, and a ticked starred task stays in its card for its moment
    pg.locator('#atList .at-star .cb').click()
    st = ev(f"""() => {{ const f = document.activeElement.dataset.k || ''; tidyMarks(); Menu.refresh();
      return {{ f, card: !!document.querySelector('#atList .at-star .at-row.ticked'), star: getProject('{nc}').star,
        create: document.querySelector('#atShifts [data-shift="create"] .n').textContent }}; }}""")
    ok('a tick with the square keeps the focus on it', st['f'].startswith('cb-'), st)
    ok('a ticked starred task stays in its card while it is struck through, after its star is cleared', st['card'] and st['star'] == '', st)
    ok('the chips leave the held row out of their counts', st['create'] == '2', st)
    settle("() => !document.querySelector('#atList .at-star')")
    ok('then it goes, and the card with it', not pg.is_visible('#atList .at-star'))
    quiet()

    # Due this week's "and N more"
    ev("() => AllTasks.close()")
    ev(f"() => {{ const P = getProject('{gp}'); for (let i = 0; i < 9; i++) P.todos.push(Object.assign(todo('Soon ' + i, P.milestones[0].id), {{ due: '{nth_day(2)}' }})); normalizeOrder(P); changed(P); }}")
    pg.wait_for_timeout(200)
    ok('A1 Due this week\'s "and N more" is a button', ev("() => document.querySelector('#dueList .due-more-btn').textContent").startswith('and '))
    pg.click('#dueList .due-more-btn'); pg.wait_for_timeout(250)
    ok('and it opens All tasks', pg.is_visible('#allTasks'))
    ev(f"() => {{ const P = getProject('{gp}'); P.todos = P.todos.filter(t => !t.text.startsWith('Soon ')); changed(P); }}")
    ev("() => AllTasks.close()")

    # kept: a shift travels with the city
    pg.reload(); pg.wait_for_timeout(2200)
    ok('a shift is kept after a reload', get(gp, 'Publish the app')['shift'] == 'errand' and get(nc, 'Make block art for each project')['shift'] == 'errand')

    # a narrow window: L opens the drawer on All tasks
    pg.set_viewport_size({'width': 700, 'height': 900}); pg.wait_for_timeout(300)
    pg.mouse.click(600, 300); pg.keyboard.press('KeyL'); pg.wait_for_timeout(400)
    ok('on a narrow window L opens the drawer on All tasks', ev("() => document.querySelector('#menu').classList.contains('open')") and pg.is_visible('#allTasks'))
    ok('with nothing past its edge', ev("() => { const m = document.querySelector('#menu'); return m.scrollWidth <= m.clientWidth + 1; }"))
    pg.screenshot(path=str(SHOTS / '356-narrow.png'))

    print('errors:', errors)
    ok('no console errors', not errors)
    b.close()
