import json, pathlib
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY

errors = []
def attach(page):
    page.on('console', lambda m: errors.append(f'console.{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
def ok(label, cond):
    print(('PASS ' if cond else 'FAIL ') + label)

FAKE_FS = """
window.__writes = [];
window.showSaveFilePicker = async () => ({
  name: 'nullovation-city-data.json',
  queryPermission: async () => 'granted',
  requestPermission: async () => 'granted',
  createWritable: async () => { let buf = ''; return { write: async d => { buf += d; }, close: async () => { window.__writes.push(buf); } }; },
});
"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    ctx.add_init_script(FAKE_FS)
    page = ctx.new_page(); attach(page)
    page.goto(FILE); page.wait_for_timeout(600)
    left = page.evaluate("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    ok('the test city loads at data version 2 on a 5 by 5 map', page.evaluate("() => DB.version === 2 && DB.world.size === 5 && WORLD.N === 5"))
    ok('key hint visible', page.is_visible('.keyhint'))

    # map size: grow shifts every plot by one and keeps the view on the same buildings
    before = page.evaluate("() => DB.projects.map(p => ({...p.plot}))")
    a0 = page.evaluate("() => MapView.anchors(DB.projects[0].id)")
    page.click('#btnGrow'); page.wait_for_timeout(200)
    after = page.evaluate("() => DB.projects.map(p => ({...p.plot}))")
    a1 = page.evaluate("() => MapView.anchors(DB.projects[0].id)")
    ok('grow makes 7 by 7', page.evaluate("() => WORLD.N === 7 && DB.world.size === 7") and page.text_content('#mapSize') == '7 by 7 plots')
    ok('plots shift by one ring', all(x['u'] == y['u'] + 1 and x['v'] == y['v'] + 1 for x, y in zip(after, before)))
    ok(f"view stays on the same building ({a0['baseY']:.0f} vs {a1['baseY']:.0f})", abs(a0['baseY'] - a1['baseY']) < 2 and abs(a0['baseX'] - a1['baseX']) < 2)
    page.screenshot(path=str(SHOTS / '40-grown.png'))
    page.click('#btnShrink'); page.wait_for_timeout(200)
    ok('shrink back to 5', page.evaluate("() => WORLD.N === 5"))
    ok('shrink disabled at 5', page.is_disabled('#btnShrink'))

    # full map: New project offers a ring
    page.evaluate("""() => { const free = freePlots(); for (const f of free) DB.projects.push(blankProject({ name: 'Filler ' + f.u + f.v, plot: f })); persistNow(); MapView.invalidate(); Menu.refresh(); }""")
    page.click('#btnNew'); page.fill('#newName', 'One too many'); page.keyboard.press('Enter'); page.wait_for_timeout(300)
    page.click('.pick-card >> nth=1'); page.wait_for_timeout(300)
    ok('full map asks to add a ring', page.is_visible('.backdrop.top') and 'Every plot is taken' in page.text_content('#cfTitle'))
    page.click('.confirm-actions .btn-accent'); page.wait_for_timeout(300)
    ok('map grew and placing started', page.evaluate("() => WORLD.N === 7") and page.is_visible('#banner'))
    page.keyboard.press('Escape')
    page.evaluate("() => { DB.projects = DB.projects.filter(p => !p.name.startsWith('Filler')); persistNow(); MapView.resizeWorld(-1); MapView.frameAll(); }")
    page.wait_for_timeout(200)
    ok('back to 2 projects on 5 by 5', page.evaluate("() => DB.projects.length === 2 && WORLD.N === 5"))

    # hop with E and Q
    page.mouse.click(left + 60, 60); page.wait_for_timeout(100)
    page.keyboard.press('e'); page.wait_for_timeout(500)
    s1 = page.evaluate("() => App.selectedId")
    page.keyboard.press('e'); page.wait_for_timeout(500)
    s2 = page.evaluate("() => App.selectedId")
    page.keyboard.press('q'); page.wait_for_timeout(500)
    s3 = page.evaluate("() => App.selectedId")
    ok('E and Q hop between buildings', s1 and s2 and s1 != s2 and s3 == s1 and page.is_visible('#bubble'))
    page.keyboard.press('BracketRight'); page.wait_for_timeout(400)
    ok('] hops too', page.evaluate("() => App.selectedId") == s2)
    page.keyboard.press('Escape')

    # postcard
    with page.expect_download() as dl:
        page.click('#btnPostcard')
    png = pathlib.Path(dl.value.path()).read_bytes()
    ok(f'postcard is a PNG ({len(png)//1024} KB)', png[:8] == b'\x89PNG\r\n\x1a\n')
    pathlib.Path(SHOTS / '41-postcard.png').write_bytes(png)

    # milestones, due dates, notes on the made-up project
    wid = page.evaluate("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    a = page.evaluate(f"() => MapView.anchors('{wid}')")
    page.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); page.wait_for_timeout(500)
    page.click('#enterBtn'); page.wait_for_timeout(300)
    # the starter project already has two milestones; add a third
    page.click('#pvAddMsBtn'); page.keyboard.type('Polish'); page.keyboard.press('Enter'); page.wait_for_timeout(200)
    ms = page.evaluate(f"() => DB.projects.find(p => p.id === '{wid}').milestones.map(m => m.name)")
    ok(f'three milestones named {ms}', ms == ['First release', 'Launch', 'Polish'])
    # keyboard: Alt+Down moves the last task of the first milestone into the second
    last1 = page.evaluate(f"() => {{ const p = DB.projects.find(p => p.id === '{wid}'); return groupsOf(p).filter(g => g.ms)[0].todos.slice(-1)[0].text; }}")
    page.focus('.ms >> nth=0 >> li.task:last-child .task-title'); page.keyboard.press('Alt+ArrowDown'); page.wait_for_timeout(150)
    t = page.evaluate(f"() => {{ const p = DB.projects.find(p => p.id === '{wid}'); return p.todos.filter(t => t.milestoneId === p.milestones[1].id).map(t => t.text); }}")
    ok(f'Alt and an arrow move a task into the next milestone ({t[0][:30]})', t[0] == last1)
    # drag the first task of the first milestone into the empty third milestone, aiming by eye as the list reflows
    src = page.query_selector('.ms >> nth=0 >> li.task >> nth=0').bounding_box()
    page.mouse.move(src['x'] + 80, src['y'] + src['height'] / 2); page.mouse.down()
    page.mouse.move(src['x'] + 80, src['y'] + 30, steps=4)
    for k in range(10):
        row = page.query_selector('.ms >> nth=2 >> .ms-row').bounding_box()
        page.mouse.move(src['x'] + 80, row['y'] + row['height'] + 12, steps=3); page.wait_for_timeout(16)
    page.mouse.up(); page.wait_for_timeout(250)
    t2 = page.evaluate(f"() => {{ const p = DB.projects.find(p => p.id === '{wid}'); return p.todos.filter(t => t.milestoneId === p.milestones[2].id).map(t => t.text); }}")
    ok(f'drag moves a task into the empty milestone ({t2})', len(t2) == 1)
    ok('a drag leaves the task closed', not page.is_visible('#pvSide'))
    order_ok = page.evaluate(f"() => {{ const p = DB.projects.find(p => p.id === '{wid}'); const g = groupsOf(p).flatMap(g => g.todos.map(t => t.id)); return JSON.stringify(g) === JSON.stringify(p.todos.map(t => t.id)); }}")
    ok('todo order matches group order', order_ok)
    # a due date tomorrow, set in the task's own panel
    import datetime
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    page.click('.ms >> nth=0 >> li.task >> nth=1 >> .task-title'); page.wait_for_timeout(300)
    page.fill('#pvTaskDue', tomorrow); page.wait_for_timeout(100)
    page.click('#pvSide >> text=Done'); page.wait_for_timeout(200)
    page.screenshot(path=str(SHOTS / '42-edit-milestones.png'))
    page.click('#pvAddNoteBtn'); page.wait_for_timeout(200)
    page.fill('#pvNoteBody', 'Walked the beds with the plan open.')
    page.click('#pvSide >> text=Done'); page.wait_for_timeout(200)
    ok('note added', page.evaluate(f"() => DB.projects.find(p => p.id === '{wid}').notes.length") == 1)
    page.screenshot(path=str(SHOTS / '43-edit-notes.png'))
    page.screenshot(path=str(SHOTS / '44-read-milestones.png'))
    ok('the list shows milestone names', page.eval_on_selector_all('.ms-name-btn', 'els => els.map(e => e.textContent)') == ['First release', 'Launch', 'Polish'])
    ok('the new milestone is in the activity log', page.evaluate(f"() => DB.projects.find(p => p.id === '{wid}').activity.some(e => e.text === 'New milestone: Polish')"))
    page.evaluate("() => { const m = document.querySelector('#pv'); m.scrollTop = m.scrollHeight; }"); page.wait_for_timeout(100)
    page.screenshot(path=str(SHOTS / '45-read-notes.png'))
    page.keyboard.press('Escape'); page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / '46-bubble-due.png'))
    first = page.text_content('#bubble .b-todos li:first-child .txt')
    ok(f'due-tomorrow todo leads the bubble ({first[:40]})', 'Due tomorrow' in first)

    # week recap: tick one, then open
    page.click('#bubble .b-todos li:nth-child(2) .cb'); page.wait_for_timeout(900)
    page.click('#btnRecap'); page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / '47-recap.png'))
    txt = page.text_content('.modal.panel')
    ok('the week lists the tick and the note', '1 task finished' in txt and '1 note written' in txt)
    page.click('.recap-name >> nth=0'); page.wait_for_timeout(500)
    ok('recap name selects the building', not page.is_visible('.modal.panel') and page.evaluate("() => !!App.selectedId"))

    # status brief to the clipboard
    page.click('#foldTools summary'); page.click('#btnBrief'); page.wait_for_timeout(200)
    clip = page.evaluate("() => navigator.clipboard.readText()")
    ok('brief copied with headings, todos, and milestone tags', clip.startswith('# Nullovation City status') and '## Garden planner' in clip and '(First release' in clip and 'Due tomorrow' in clip and 'Next task: ' in clip)
    (DATA / 'brief.txt').write_text(clip, encoding='utf-8')

    # data file (the picker is faked for the test)
    page.click('#foldData summary'); page.click('text=Keep a data file'); page.wait_for_timeout(1500)
    n0 = page.evaluate("() => window.__writes.length")
    data = json.loads(page.evaluate("() => window.__writes[window.__writes.length - 1]"))
    ok(f'data file written on connect ({n0} writes, {len(data["projects"])} projects)', n0 >= 1 and len(data['projects']) == 2 and data['version'] == 2)
    ok('status shows the file', 'nullovation-city-data.json' in page.text_content('#fileBox'))
    page.evaluate("() => { const p = DB.projects[0]; p.description = 'changed for the file test'; changed(p); }"); page.wait_for_timeout(1800)
    last = json.loads(page.evaluate("() => window.__writes[window.__writes.length - 1]"))
    ok('changes reach the file', any(q.get('description') == 'changed for the file test' for q in last['projects']))
    page.screenshot(path=str(SHOTS / '48-menu.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})

    # an old v1 backup still imports
    page.set_input_files('#fileImport', fixture('backup-v1.json')); page.wait_for_timeout(300)
    page.click('.confirm-actions .btn-danger'); page.wait_for_timeout(900)
    ok('v1 backup imports into v2', page.evaluate("() => DB.projects.length === 3 && DB.projects.every(p => Array.isArray(p.milestones) && Array.isArray(p.notes) && p.todos.every(t => 'due' in t))"))
    page.reload(); page.wait_for_timeout(700)
    ok('reload keeps v2 data', page.evaluate("() => DB.projects.length === 3 && DB.version === 2"))

    # the real start: a browser with nothing saved gets the one starter project, on the city hall
    fresh = b.new_context(viewport={'width': 1440, 'height': 900}); fp = fresh.new_page(); attach(fp)
    fp.goto(FILE); fp.wait_for_timeout(600)
    ok('a new city starts with one project, Nullovation City on the city hall',
       fp.evaluate("() => DB.projects.length === 1 && DB.projects[0].name === 'Nullovation City' && DB.projects[0].generic === 'city-hall'"))
    ok('it starts at data version 2 on a 5 by 5 map, with its history begun',
       fp.evaluate("() => DB.version === 2 && DB.world.size === 5 && WORLD.N === 5 && DB.projects[0].activity.some(e => e.text === 'Planted')"))
    fresh.close()
    b.close()
print('\n'.join(errors) if errors else 'no console errors')
