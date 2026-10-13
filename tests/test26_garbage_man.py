"""Gus Grimsby, the Garbage Man: his place in the side bar and when he steps away, his report line in every case, the
task to start with and the rows under it, a click going to a building, his lines with their blanks, the first open of
the day, the alarms at 50 and 200 (once as the total climbs past, at most once a day, the worst only), the clean city,
the speech bubble (where it sits, closing, going by itself), and the Garbage switch sending him away."""
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# The test city, made dirty on purpose: urgency systems and due dates in days from now, on the two test projects and
# any extra ones (kiosks on free plots). Each spec: (name or None for a new one, urgency or None, [due offsets]).
STATE = """(specs) => {
  const D = 864e5, now = Date.now();
  for (const p of [...DB.projects]) if (p.name.startsWith('Extra ')) deleteProject(p.id);
  for (const p of DB.projects) { p.urgency = { system: 'none', days: 1, lastWorked: null, pickedAt: null }; p.todos.forEach(t => { t.due = ''; t.done = false; }); }
  const free = [[0, 0], [4, 4], [0, 4], [4, 0], [1, 3]];
  let k = 0;
  for (const [name, urg, dues] of specs) {
    let p = name ? DB.projects.find(x => x.name === name) : null;
    if (!p) { const [u, v] = free[k]; p = createProject('Extra ' + (++k), { u, v }, null, 'kiosk'); }
    if (urg) p.urgency = { system: urg[0], days: urg[1], lastWorked: urg[2] == null ? null : now - urg[2] * D, pickedAt: now - 30 * D };
    dues.forEach((d, i) => { if (!p.todos[i]) p.todos.push({ id: 'tx' + k + '_' + i, text: 'Extra task ' + i, description: '', done: false, doneAt: null, due: '', milestoneId: null }); p.todos[i].due = ymd(now + d * D); });
    changed(p);
  }
  persistNow(); Garbage.refresh(); Gus.render();
}"""
HALL, LAB = 'Nullovation City', 'Garden planner'
READ = "() => ({ shown: !document.querySelector('#sbGus').hidden, report: $('#gusReport').hidden ? '' : $('#gusReport').textContent, fix: $('#gusFix').hidden ? '' : $('#gusFix').textContent, rows: [...document.querySelectorAll('.gus-row')].map(b => b.textContent), line: $('#gusLine').hidden ? '' : $('#gusLine').textContent, saying: !document.querySelector('#gusSay').hidden, say: $('#gusSayText').textContent })"

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t26')) { sessionStorage.setItem('nc-t26', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'none'); } } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(1500)
    js = pg.evaluate
    state = lambda specs: (js(STATE, specs), pg.wait_for_timeout(300), js(READ))[2]

    # ---------- away while the city is clean ----------
    r = js(READ)
    ok('a clean city: Gus is away, and says nothing on the first open of the day', not r['shown'] and not r['saying'] and js("() => Gus._test.days().open") == js("() => ymd(Date.now())"))
    ok('his section sits between This week and Urgent', js("() => { const s = [...document.querySelectorAll('#sbLists > section')].map(x => x.id || x.getAttribute('aria-label')); return s.indexOf('sbGus') === s.indexOf('This week') + 1 && s.indexOf('sbUrgent') === s.indexOf('sbGus') + 1; }"))

    # ---------- the report line, in every case approved ----------
    r = state([[HALL, None, [-2]]])
    ok(f'one late task: he shows up, "You have 1 overdue task. Let\'s clean it up." ({r["report"]})', r['shown'] and r['report'] == "You have 1 overdue task. Let's clean it up.")
    ok(f'the task to start with, and its row ({r["fix"]} | {r["rows"]})', r['fix'] == 'Start with Round 3: decide the block art loop, in Nullovation City.' and r['rows'] == ['Nullovation City: 1 overdue task'])
    r = state([[LAB, ['pace', 2, 4.5], []]])
    ok(f'one project two periods behind ({r["report"]} | {r["fix"]} | {r["rows"]})', r['report'] == "1 project needs your urgent attention. Let's clean it up."
       and r['fix'] == 'Start with any task in Garden planner.' and r['rows'] == ['Garden planner: urgent'])
    r = state([[HALL, ['pace', 3, 4], []], [LAB, ['pace', 2, 2.5], []], [None, ['pace', 1, 1.5], []]])
    ok(f'three projects one period behind ({r["report"]} | {r["rows"]})', r['report'] == "3 projects need your attention. Let's clean them up." and all(x.endswith(': needs attention') for x in r['rows']) and len(r['rows']) == 3)
    r = state([[LAB, ['finish', 1, 1.5], [-1, -3]]])
    ok(f'work until finished with no task done for a day counts as urgent, with its late tasks ({r["report"]} | {r["rows"]})',
       r['report'] == "1 project needs your urgent attention. You have 2 overdue tasks. Let's clean them up." and r['rows'] == ['Garden planner: urgent, 2 overdue tasks'])
    r = state([[HALL, ['pace', 2, 4.5], [-1]], [LAB, ['pace', 1, 2.5], [-6, -2]], [None, ['pace', 3, 3.5], [-1]]])
    ok(f'all three at once ({r["report"]})', r['report'] == "2 projects need your urgent attention, 1 project needs your attention. You have 4 overdue tasks. Let's clean them up.")
    ok(f'the rows, the most garbage first ({r["rows"]})', r['rows'] == ['Garden planner: urgent, 2 overdue tasks', 'Nullovation City: urgent, 1 overdue task', 'Extra 1: needs attention, 1 overdue task'])
    ok(f'the task to start with clears the most: the latest task, which also puts its project back on pace ({r["fix"]})', r['fix'] == 'Start with Draw the beds on a grid, in Garden planner.')
    rep = js("() => Gus.report()")
    ok(f'the tasks between the city and clean streets: every late task, a project behind with none counts one ({rep["tasks"]})', rep['tasks'] == 4)
    r = state([[HALL, ['pace', 1, 2.5], []], [LAB, None, [-1]]])
    ok('a project behind with no late task adds one task to his count', js("() => Gus.report().tasks") == 2)
    ok('never pieces: the report, the fix and the rows count tasks and projects', not any('piece' in x for x in [r['report'], r['fix'], *r['rows']]))
    state([[LAB, None, [-3]]])
    js("() => { const p = DB.projects.find(x => x.name === 'Garden planner'); p.todos[0].text = 'A very long task title that keeps going well past what fits on one short line'; changed(p); Gus.render(); }")
    ok(f'a long task title is cut short ({js("() => $(\'#gusFix\').textContent")})', js("() => $('#gusFix').textContent").endswith('…, in Garden planner.') and len(js("() => $('#gusFix').textContent")) <= 91)
    js("() => { const p = DB.projects.find(x => x.name === 'Garden planner'); p.todos[0].text = 'Draw the beds on a grid'; changed(p); }")

    # ---------- his lines and their blanks ----------
    lines = js("() => Gus.LINES")
    ok('his lines never mention pieces', not any('piece' in l.lower() for ls in lines.values() for l in ls))
    ok('his lines for a clean city, as kept', lines['clean'] == ["Clean streets. Don't get used to it.", "Not a wrapper in sight. I'll be off, then.", "Fine. Good work. Don't make me come back."])
    ok('and the alarms in Abdurrahman\'s words', lines['dirty'] == ['The city is getting dirty! We should do something about it.'] and lines['filthy'] == ['The city is filthy! This is unacceptable!'])
    state([[LAB, ['pace', 2, 4.5], []]])
    filled = js("() => Gus.LINES.open.map(l => Gus.fill(l, Gus.report()))")
    ok(f'the blanks fill: "1 task", and a project behind reads "any task in", capitalized when it starts a sentence ({filled})',
       filled == ["You're back. 1 task between this city and clean streets. Start with any task in Garden planner.",
                  'Took you long enough. 1 task waiting. Any task in Garden planner first.',
                  "I cannot clean what you don't fix. 1 task. Start with any task in Garden planner."])
    state([[HALL, None, [-2]], [LAB, None, [-1, -3]]])
    filled = js("() => Gus.LINES.open.map(l => Gus.fill(l, Gus.report()))")
    ok(f'and with three late tasks ({filled[0]})', filled[0] == "You're back. 3 tasks between this city and clean streets. Start with Save a plan as a file.")

    # ---------- a click on a row goes to the building ----------
    pg.click('.gus-row >> nth=0'); pg.wait_for_timeout(500)
    ok('a click on a row selects its building and opens its card', js("() => App.selectedId") == js("() => DB.projects.find(x => x.name === 'Garden planner').id") and pg.is_visible('#bubble'))
    js("() => MapView.deselect()")

    # ---------- the first open of the day ----------
    js("() => Gus._test.forget()")
    pg.reload(); pg.wait_for_timeout(1500)
    r = js(READ)
    ok(f'the first open of the day with garbage in it: he speaks ({r["say"]})', r['saying'] and r['say'] in [js(f"() => Gus.fill(Gus.LINES.open[{i}], Gus.report())") for i in range(3)])
    ok('his words show under his face in the side bar too', r['line'] == r['say'])
    box, wrap, menu = (pg.locator(s).bounding_box() for s in ('#gusSay', '#mapWrap', '#menu'))
    ok(f'the speech bubble sits at the map\'s top left, clear of the side bar ({box})', abs(box['x'] - wrap['x'] - 22) <= 2 and abs(box['y'] - wrap['y'] - 18) <= 2 and box['x'] >= menu['x'] + menu['width'])
    pg.screenshot(path=str(SH / '260-gus-says.png'))
    pg.locator('#sbGus').screenshot(path=str(SH / '261-gus-side.png'))
    pg.click('#gusSayClose'); pg.wait_for_timeout(200)
    r = js(READ)
    ok('the close button sends the bubble away, his line stays in the side bar', not r['saying'] and r['line'])
    pg.reload(); pg.wait_for_timeout(1500)
    ok('the second open of the day: he says nothing', not js(READ)['saying'])

    # ---------- the alarms ----------
    hall = js(f"() => DB.projects.find(x => x.name === '{HALL}').id")
    state([])
    js("() => { Gus._test.forget(); Gus._test.sayMs(60000); }")
    force = lambda n: (js(f"() => Garbage._test.force('{hall}', {n})"), pg.wait_for_timeout(250))
    force(30)
    ok('30 pieces: no alarm yet', not js(READ)['saying'])
    force(60)
    r = js(READ)
    ok(f'past 50: "{r["say"]}"', r['saying'] and r['say'] == 'The city is getting dirty! We should do something about it.')
    js("() => Gus.hush()"); force(30); force(70)
    ok('climbing past 50 again the same day: quiet', not js(READ)['saying'])
    force(250)
    r = js(READ)
    ok(f'past 200: "{r["say"]}"', r['saying'] and r['say'] == 'The city is filthy! This is unacceptable!')
    js("() => { Gus.hush(); Gus._test.forget(); }"); force(0); force(600)
    r = js(READ)
    ok(f'jumping past both at once: only the worst speaks ({r["say"]})', r['say'] == 'The city is filthy! This is unacceptable!' and 'dirty' not in js("() => Gus._test.days()"))
    ok('the days he spoke are kept on this computer', js("() => JSON.parse(localStorage.getItem('nullovation-city:gus')).filthy") == js("() => ymd(Date.now())"))
    js("() => Gus.hush()")

    # ---------- a clean city again ----------
    js("() => { Motion.set('still'); }"); force(40); js("() => Gus.hush()")
    force(0); pg.wait_for_timeout(300)
    r = js(READ)
    ok(f'the last piece goes: he says so ({r["say"]})', r['saying'] and r['say'] in lines['clean'] and r['shown'])
    js("() => Gus.hush()"); pg.wait_for_timeout(200)
    ok('and steps away once his bubble closes', not js(READ)['shown'])
    js(f"() => Garbage._test.force('{hall}', null)")
    js("() => Motion.set('full')")
    state([[HALL, None, [-2]]])
    js("() => { Gus._test.sayMs(600); Gus.hush(); Gus._test.forget(); }")
    force(20); force(80)
    saying = js(READ)['saying']
    pg.wait_for_timeout(900)
    ok('a speech bubble goes by itself after a while', saying and not js(READ)['saying'])
    js(f"() => Garbage._test.force('{hall}', null)"); pg.wait_for_timeout(200)

    # ---------- the Garbage switch ----------
    js("() => Garbage.setOn(false)"); pg.wait_for_timeout(300)
    r = js(READ)
    ok('Garbage off: Gus goes with it, and says nothing as it goes', not r['shown'] and not r['saying'] and js("() => Gus.line()") == '')
    js("() => Garbage.setOn(true)"); pg.wait_for_timeout(300)
    r = js(READ)
    ok('Garbage on again: he is back, quietly', r['shown'] and not r['saying'])
    state([])
    b.close()
print(errors or 'no console errors')
