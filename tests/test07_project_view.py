import json, pathlib
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    left = pg.evaluate("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    wz = pg.evaluate("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    nc = pg.evaluate("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    proj = lambda: pg.evaluate(f"() => JSON.parse(JSON.stringify(DB.projects.find(p => p.id === '{wz}')))")

    def open_project(pid):
        pg.evaluate("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(250)
        a = pg.evaluate(f"() => MapView.anchors('{pid}')")
        pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(500)
        pg.click('#enterBtn'); pg.wait_for_timeout(600)

    # the frame: a panel docked on the left, the bubble steps aside, the building stays in view
    ok('projects carry a backfilled activity log', pg.evaluate("() => DB.projects.every(p => p.activity.length && p.activity[0].text === 'Planted')"))
    open_project(wz)
    box = pg.query_selector('#pv').bounding_box()
    ok(f'the view docks at the left edge of the map, 880 wide ({box["x"]:.0f}, {box["width"]:.0f} wide)', abs(box['x'] - left) < 2 and abs(box['width'] - 880) < 2)
    ok('the bubble hides while the view shows its project', pg.evaluate("() => getComputedStyle(document.querySelector('#bubble')).visibility") == 'hidden')
    a = pg.evaluate(f"() => MapView.anchors('{wz}')")
    ok(f'the building sits in the open map, right of the panel (x {a["baseX"]:.0f})', a['baseX'] > box['width'] + 40)
    scene = pg.query_selector('.pv-scene canvas').bounding_box()
    ok(f'the building picture is 440 wide at two screen pixels per map pixel ({scene["width"]:.0f} by {scene["height"]:.0f})', abs(scene['width'] - 440) < 2 and scene['height'] >= 279)
    about = pg.query_selector('[data-sec="about"]').bounding_box()
    ok('About sits beside the picture', about['x'] > scene['x'] + scene['width'] and abs(about['y'] - scene['y']) < 30)
    ok('the sections sit in two columns', pg.evaluate("() => getComputedStyle(document.querySelector('.pv-cols')).gridTemplateColumns.split(' ').length") == 2)
    z0 = pg.evaluate("() => MapView.camState().z")
    pg.mouse.move(left + 400, 600); pg.mouse.wheel(0, 300); pg.wait_for_timeout(300)
    can = pg.evaluate("() => { const e = document.querySelector('#pv'); return e.scrollHeight > e.clientHeight + 2; }")
    ok('the wheel over the view scrolls it, not the map', (pg.evaluate("() => document.querySelector('#pv').scrollTop") > 0 or not can) and pg.evaluate("() => MapView.camState().z") == z0)
    pg.evaluate("() => document.querySelector('#pv').scrollTop = 0"); pg.wait_for_timeout(100)
    pg.mouse.move(left + 1060, 400); pg.mouse.wheel(0, 300); pg.wait_for_timeout(300)
    ok('the wheel over the map scrolls the view too, and never zooms', (pg.evaluate("() => document.querySelector('#pv').scrollTop") > 0 or not can) and pg.evaluate("() => MapView.camState().z") == z0)
    pg.evaluate("() => document.querySelector('#pv').scrollTop = 0"); pg.wait_for_timeout(100)
    ok('no previous or next arrows in the view', pg.locator('#pv [aria-label*="previous" i], #pv [aria-label*="next project" i]').count() == 0)

    # quick actions work without opening any section
    todo0 = proj()['todos'][0]
    pg.click(f'[data-sec="todos"] li[data-id="{todo0["id"]}"] .cb'); pg.wait_for_timeout(150)
    ok('a todo ticks straight from the page', proj()['todos'][0]['done'] is True)
    ok('no field sits open before you ask for one', pg.eval_on_selector_all('#pv input:not([type=checkbox]), #pv textarea', 'els => els.length') == 0)
    pg.click('.ms >> nth=1 >> .ms-plus'); pg.wait_for_timeout(100)
    pg.keyboard.type('Write the release note'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    ok('a task adds from its milestone’s [+], and the field closes', pg.locator('li.task-add').count() == 0 and 'Write the release note' in pg.text_content('.ms >> nth=1'))
    pg.click('.ms >> nth=0 >> .ms-plus'); pg.wait_for_timeout(100); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('Esc closes an empty add field, not the view', pg.locator('li.task-add').count() == 0 and pg.is_visible('#pv'))
    ok('a todo adds straight from the page', proj()['todos'][-1]['text'] == 'Write the release note')
    pg.click('#pvAddNoteBtn'); pg.wait_for_timeout(250)
    ok('Add note opens a new note beside the view, title first', pg.is_visible('#pvSide #pvNoteTitle') and pg.evaluate("() => document.activeElement.id") == 'pvNoteTitle')
    pg.fill('#pvNoteTitle', 'A week in'); pg.fill('#pvNoteBody', 'Tried the side panel for a week.')
    pg.click('#pvSide >> text=Done'); pg.wait_for_timeout(200)
    ok('the note is kept with its title', any(n['title'] == 'A week in' and n['text'] == 'Tried the side panel for a week.' for n in proj()['notes']))
    ok('it shows as a card', 'A week in' in pg.text_content('[data-sec="notes"] .pv-note-grid'))
    pg.click('[data-sec="notes"] .pv-note-card >> text=A week in'); pg.wait_for_timeout(200)
    pg.fill('#pvNoteBody', 'Changed my mind'); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc in an open note puts it back as it was', any(n['text'] == 'Tried the side panel for a week.' for n in proj()['notes']) and not pg.is_visible('#pvSide'))
    pg.click('#pvAddNoteBtn'); pg.wait_for_timeout(200); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc on a new note drops it', len([n for n in proj()['notes'] if not n['title'] and not n['text']]) == 0)
    pg.click('#pvAddLinkBtn'); pg.wait_for_timeout(100)
    pg.fill('#pvLinkUrl', 'https://github.com/example/garden-planner'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    ok('a link adds straight from the page, with a guessed icon', proj()['links'][-1]['icon'] == 'code')
    second = proj()['todos'][1]['text']
    ok('with the first task ticked, What is next moves to the second', pg.text_content('#pvNextTask').strip() == second)
    pg.click('.pv-next-row >> text=Copy for Claude'); pg.wait_for_timeout(150)
    ok('What is next copies that task for Claude', pg.evaluate("() => navigator.clipboard.readText()").startswith('# Task: ' + second))
    import datetime
    past = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    pg.click('#pvNextTask'); pg.wait_for_timeout(200); pg.fill('#pvTaskDue', past); pg.click('#pvSide >> text=Done'); pg.wait_for_timeout(200)
    ok('an overdue next task gets the red !', pg.locator('.pv-next-task.late .pv-late-mark').count() == 1 and '2 days overdue' in pg.text_content('.pv-next'))
    ok('no section opened for any of that', pg.locator('#pv .pv-done').count() == 0)
    log = [e['text'] for e in proj()['activity']]
    ok('each quick action lands in the activity log', all(any(x in e for e in log) for x in ['Done: ', 'Added todo: Write the release note', 'Wrote a note: A week in', 'Added link: ', 'Edited task: ']))

    # sections: a pencil opens one, Done keeps it, Esc undoes the whole session, one at a time
    desc0 = proj()['description']
    pg.click('[data-sec="about"] .pv-pencil'); pg.wait_for_timeout(150)
    ok('the About pencil puts the cursor in the description', pg.evaluate("() => document.activeElement && document.activeElement.id") == 'pvDesc')
    pg.fill('#pvDesc', 'A brand new description')
    pg.fill('[data-sec="about"] input[type="date"]', '2026-11-02'); pg.wait_for_timeout(100)
    ok('edits save as you type', proj()['description'] == 'A brand new description')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc undoes the whole session', proj()['description'] == desc0 and proj()['deadline'] == '' and 'undone' in pg.text_content('#toast'))
    ok('and closes the section, not the view', pg.is_visible('#pv') and pg.locator('#pv .pv-done').count() == 0)
    ok('Todos has no pencil: everything there drags in place', pg.locator('[data-sec="todos"] .pv-pencil').count() == 0)
    pg.click('[data-sec="about"] .pv-pencil'); pg.wait_for_timeout(150)
    pg.click('[data-sec="links"] .pv-pencil'); pg.wait_for_timeout(150)
    ok('opening links closes About: one section at a time', pg.locator('[data-sec="about"] .pv-done').count() == 0 and pg.locator('[data-sec="links"] .pv-done').count() == 1)
    pg.click('[data-sec="links"] .pv-done'); pg.wait_for_timeout(150)
    pg.click('[data-sec="name"] .pv-pencil'); pg.wait_for_timeout(100)
    pg.fill('#pvName', 'Garden app'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    ok('the name edits from its own pencil', proj()['name'] == 'Garden app' and pg.text_content('#pvTitle') == 'Garden app')
    pg.screenshot(path=str(SH / 'pv-7-sections.png'))

    # the profile line: activity in the side panel, and a copy of this project's status
    pg.click('#pv .pv-about-btns >> text=Activity'); pg.wait_for_timeout(250)
    ok('Activity opens in the side panel', pg.is_visible('#pvSide') and 'Today' in pg.text_content('#pvSide'))
    ok('the side panel never overlaps the view', pg.evaluate("() => document.querySelector('#pvSide').getBoundingClientRect().left >= document.querySelector('#pv').getBoundingClientRect().right"))
    ok('the feed lists today\u2019s changes, newest first', pg.text_content('#pvSide .pv-day li:first-child span') == 'Renamed to Garden app')
    pg.screenshot(path=str(SH / 'pv-8-activity.png'))
    pg.click('#pv .pv-about-btns >> text=Copy status'); pg.wait_for_timeout(150)
    st = pg.evaluate("() => navigator.clipboard.readText()")
    ok('Copy status copies this project only', st.startswith('## Garden app') and 'Nullovation City' not in st)

    # the more menu: builder, the builder card in a chat, export, delete; Esc peels layers one at a time
    pg.click('#pvMore'); pg.wait_for_timeout(100)
    items = pg.eval_on_selector_all('.pv-menu-item', 'els => els.map(e => e.textContent)')
    ok(f'the more menu holds exactly {items}', items == ['Copy for builder', 'Builder card in a Claude chat', 'Load plan or tasks', 'Export this project', 'Delete project'])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('Esc closes the menu first', pg.locator('.pv-menu').count() == 0 and pg.is_visible('#pvSide'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('then the side panel', not pg.is_visible('#pvSide') and pg.is_visible('#pv'))
    pg.click('#pvMore')
    with pg.expect_download() as dl:
        pg.click('.pv-menu-item >> text=Export this project')
    data = json.loads(pathlib.Path(dl.value.path()).read_text())
    ok('Export saves one project as a file', data.get('kind') == 'project' and data['project']['name'] == 'Garden app')
    (DATA / 'one-project.json').write_text(json.dumps(data), encoding='utf-8')

    # mirroring from the icon under the picture
    pg.click('.pv-scene-tools [aria-label="Mirror the building"]'); pg.wait_for_timeout(150)
    ok('the flip icon mirrors the building', proj()['flip'] is True and pg.get_attribute('.pv-scene-tools [aria-label="Mirror the building"]', 'aria-pressed') == 'true')

    # clicking another building on the map, then Enter, switches the view
    pg.evaluate(f"() => MapView.glideBeside('{nc}', document.querySelector('#pv').getBoundingClientRect().width)"); pg.wait_for_timeout(700)
    a = pg.evaluate(f"() => MapView.anchors('{nc}')")
    ok(f'another building can sit in the open strip of map ({a["baseX"]:.0f})', a['baseX'] > 900)
    pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(500)
    ok('the map still works while the view is open', pg.evaluate("() => App.selectedId") == nc and pg.is_visible('#pv'))
    pg.wait_for_timeout(500)
    e = pg.query_selector('#enterBtn').bounding_box(); pv = pg.query_selector('#pv').bounding_box()
    ok(f'selecting it keeps it and its Enter button clear of the view ({e["x"]:.0f} vs {pv["x"] + pv["width"]:.0f})', e['x'] >= pv['x'] + pv['width'])
    pg.click('#enterBtn'); pg.wait_for_timeout(500)
    ok('Enter on another building switches the view', pg.text_content('#pvTitle') == 'Nullovation City')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc closes the view', not pg.is_visible('#pv'))

    # importing the exported project adds a copy on a free plot
    n0 = pg.evaluate("() => DB.projects.length")
    pg.set_input_files('#fileImport', str(DATA / 'one-project.json')); pg.wait_for_timeout(600)
    ok('importing one project adds it without replacing anything', pg.evaluate("() => DB.projects.length") == n0 + 1 and pg.evaluate("() => DB.projects.filter(p => p.name === 'Garden app').length") == 2)

    # it all survives a reload
    pg.reload(); pg.wait_for_timeout(2000)
    ok('the activity log survives a reload', pg.evaluate(f"() => DB.projects.find(p => p.id === '{wz}').activity.some(e => e.text === 'Renamed to Garden app')"))
    b.close()
print(errors or 'no console errors')
