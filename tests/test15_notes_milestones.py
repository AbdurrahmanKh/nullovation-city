from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    js = lambda code: pg.evaluate(code)
    wz = js("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    js(f"""() => {{ const p = DB.projects.find(p => p.id === '{wz}');
      p.notes.push({{ id: uid('n'), title: 'Idea: a seed library', text: 'Keep every seed in a side drawer, newest first.\\nPlant any of them again.', at: Date.now() - 3600e3 }});
      const ms = p.milestones[0], ts = p.todos.filter(t => t.milestoneId === ms.id);
      ts[0].description = 'Draw each bed on the grid.\\nDone when: every bed shows.'; ts[1].done = true; ts[1].doneAt = Date.now(); ts[0].due = ymd(new Date(Date.now() + 864e5));
      changed(p); }}""")
    left = js("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    js("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(250)
    a = js(f"() => MapView.anchors('{wz}')")
    pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(450)
    pg.click('#enterBtn'); pg.wait_for_timeout(700)
    clip = lambda: js("() => navigator.clipboard.readText()")
    # notes
    cells = pg.locator('.pv-note-cell')
    ok('every note card has its own copy button', cells.count() >= 1 and pg.locator('.pv-note-cell .pv-note-copy').count() == cells.count())
    card = pg.locator('.pv-note-cell', has=pg.locator('text=Idea: a seed library'))
    card.hover(); pg.wait_for_timeout(150)
    card.locator('.pv-note-copy').click(); pg.wait_for_timeout(200)
    c = clip()
    ok('the card button copies the note for Claude', c.startswith('# Note: Idea: a seed library') and 'Project: Garden planner' in c and 'Keep every seed in a side drawer' in c and 'Plant any of them again.' in c)
    ok('with the project About, as tasks copy', '## About the project' in c)
    ok('and it copies without opening the note', not pg.is_visible('#pvNoteTitle'))
    pg.screenshot(path=str(SHOTS / 'notes-copy.png'), clip=pg.query_selector('[data-sec="notes"]').bounding_box())
    card.locator('.pv-note-card').click(); pg.wait_for_timeout(400)
    js("() => navigator.clipboard.writeText('')")
    pg.click('#pvNoteCopy'); pg.wait_for_timeout(200)
    ok('the note panel copies the same thing', clip() == c)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # the milestone view
    pg.locator('.ms-name-btn').first.click(); pg.wait_for_timeout(500)
    ms = js(f"""() => {{ const p = DB.projects.find(p => p.id === '{wz}'), m = p.milestones[0];
      return {{ name: m.name, tasks: p.todos.filter(t => t.milestoneId === m.id).map(t => [t.text, t.done]) }}; }}""")
    items = pg.locator('.pv-ms-tasks .pv-ms-task')
    ok(f'the milestone view lists its {len(ms["tasks"])} tasks, in order', items.count() == len(ms['tasks']) and [items.nth(i).locator('.pv-ms-text').text_content().replace(' (done)', '') for i in range(items.count())] == [t for t, _ in ms['tasks']])
    ok('done tasks are marked done', [('done' in (items.nth(i).get_attribute('class') or '')) for i in range(items.count())] == [d for _, d in ms['tasks']])
    ok('the list is to read: nothing in it can be clicked or ticked', pg.locator('.pv-ms-tasks button, .pv-ms-tasks input, .pv-ms-tasks a, .pv-ms-tasks [draggable="true"]').count() == 0)
    ok('an open task shows its due date and the first line of its description', 'Due tomorrow' in items.nth(0).text_content() and 'Draw each bed on the grid' in items.nth(0).text_content() and 'Done when' not in items.nth(0).text_content())
    ok('the name can still be changed there', pg.is_visible('#pvMsName'))
    pg.screenshot(path=str(SHOTS / 'milestone-view.png'), clip=pg.query_selector('.pv-side').bounding_box())
    pg.click('#pvMsCopy'); pg.wait_for_timeout(200)
    c = clip()
    open_t = [t for t, d in ms['tasks'] if not d]; done_t = [t for t, d in ms['tasks'] if d]
    ok('Copy for Claude copies the milestone as a work package', c.startswith('# Milestone: ' + ms['name']) and 'Progress: 1/' in c and all('### ' + t in c for t in open_t))
    ok('with each open task\'s full description and due date', 'Draw each bed on the grid.\nDone when: every bed shows.' in c and 'Due tomorrow' in c)
    ok('then what is done, and the About', '## Done\n- ' + done_t[0] in c and '## About the project' in c)
    ok('the version shown is the one in src/VERSION', pg.text_content('#appVersion') == 'v' + VERSION)
    b.close()
print(errors or 'no console errors')
