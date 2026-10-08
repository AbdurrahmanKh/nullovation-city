import datetime, json, pathlib
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY, open_settings, close_settings

errors = []
def attach(page):
    page.on('console', lambda m: errors.append(f'console.{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
def ok(label, cond):
    print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    page = ctx.new_page(); attach(page)
    page.goto(FILE); page.wait_for_timeout(500)
    left = page.evaluate("() => document.querySelector('#mapWrap').getBoundingClientRect().left")

    # wheel over the map zooms and settles on a whole number
    page.mouse.move(left + 300, 700)
    for _ in range(3): page.mouse.wheel(0, -120); page.wait_for_timeout(30)
    page.wait_for_timeout(600)
    cs = page.evaluate("() => MapView.camState()")
    levels = [1, 2, 3, 4, 6, 8]
    ok(f"wheel zoom settles on a zoom step: 1, 2, 3, or even (z={cs['z']})", cs['z'] > 2 and cs['z'] in levels)
    page.click('#zoomOut'); page.wait_for_timeout(400); page.click('#zoomOut'); page.wait_for_timeout(400)
    ok('zoom buttons step through the sharp levels', page.evaluate("() => MapView.camState().z") == levels[max(0, levels.index(cs['z']) - 2)])

    # keyboard pan with WASD (by physical key) and arrows
    x0 = page.evaluate("() => MapView.camState().x")
    page.keyboard.down('d'); page.wait_for_timeout(300); page.keyboard.up('d')
    x1 = page.evaluate("() => MapView.camState().x")
    ok('D pans right', x1 > x0 + 20)
    page.keyboard.down('ArrowLeft'); page.wait_for_timeout(300); page.keyboard.up('ArrowLeft')
    ok('Left arrow pans left', page.evaluate("() => MapView.camState().x") < x1 - 20)

    # new project with an Arabic name, placed on a chosen plot
    page.evaluate("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); page.wait_for_timeout(100)
    page.click('#btnNew'); page.fill('#newName', 'تحديث البلوت')
    page.keyboard.press('Enter'); page.wait_for_timeout(300)
    page.click('.pick-card >> nth=1'); page.wait_for_timeout(200)
    ok('banner shows while placing', page.is_visible('#banner'))
    pos = page.evaluate("() => MapView.plotCss(3, 3)")
    page.mouse.move(left + pos[0], pos[1]); page.wait_for_timeout(150)
    page.screenshot(path=str(SHOTS / '11-placing.png'))
    page.mouse.click(left + pos[0], pos[1]); page.wait_for_timeout(1100)
    newp = page.evaluate("() => DB.projects.find(p => p.name === 'تحديث البلوت')")
    ok('project created on plot 3,3', newp and newp['plot'] == {'u': 3, 'v': 3})
    ok('the project view opens with About ready to plan', page.is_visible('#pv') and page.is_visible('[data-sec="about"] .pv-done'))

    page.fill('#pvDesc', 'تحسين تجربة لعبة البلوت [بلوت] للاعبين الجدد.\n\nEnglish paragraph with an Arabic term: الصكة inside it.')
    soon = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()                 # far enough to show as a date
    page.fill('[data-sec="about"] input[type="date"]', soon)
    page.click('[data-sec="about"] .pv-done'); page.wait_for_timeout(200)
    ok('a new project starts with no milestones, so What is next says to add one', 'No milestones yet' in page.text_content('.pv-next'))
    page.click('#pvAddMsBtn'); page.keyboard.type('الجولة الأولى'); page.keyboard.press('Enter'); page.wait_for_timeout(150)
    for t in ['مراجعة الشاشة الرئيسية', 'Write the tooltip copy', 'اختبار مع ٥ لاعبين', 'Hand off to tech']:
        page.click('.ms >> nth=0 >> .ms-plus'); page.keyboard.type(t); page.keyboard.press('Enter'); page.wait_for_timeout(80)
    ok('four tasks land in the milestone, and What is next names the first', page.evaluate("() => { const p = DB.projects.find(p => p.name === 'تحديث البلوت'); return p.description.startsWith('تحسين') && p.todos.length === 4 && p.todos.every(t => t.milestoneId === p.milestones[0].id); }") and 'مراجعة الشاشة الرئيسية' in page.text_content('#pvNextTask'))
    page.click('#pvAddLinkBtn')
    page.fill('#pvLinkUrl', 'www.figma.com/file/abc')
    page.fill('.pv-add-link input[aria-label="New link label"]', 'Design file'); page.keyboard.press('Enter')
    page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / '13-read-arabic.png'))
    link = page.get_attribute('.link-btn', 'href')
    ok(f'bare domain link gets https ({link})', link == 'https://www.figma.com/file/abc')
    ok('a Figma link, with Design gone from the icons, gets the web icon on its own', page.evaluate("() => DB.projects.find(p => p.name === 'تحديث البلوت').links[0].icon") == 'web')
    ok('no field stays open after adding', page.eval_on_selector_all('#pv input:not([type=checkbox]), #pv textarea', 'els => els.length') == 0)
    page.keyboard.press('Escape'); page.wait_for_timeout(500)
    ok('Esc closes the view', not page.is_visible('#pv'))
    page.screenshot(path=str(SHOTS / '14-bubble-arabic.png'))
    want = page.evaluate(f"() => 'Due ' + fmtDate(parseYmd('{soon}'))")
    ok(f'bubble shows deadline ({want})', want in (page.text_content('#bubble .meta') or ''))

    # manual progress override, then back to automatic
    page.click('#enterBtn'); page.wait_for_timeout(300)
    page.click('[data-sec="about"] .pv-pencil'); page.wait_for_timeout(200)
    page.check('input[name="prog"] >> nth=1'); page.fill('.num', '70'); page.wait_for_timeout(100)
    page.click('[data-sec="about"] .pv-done'); page.wait_for_timeout(200)
    ok('manual override shows 70%', page.text_content('#pv .pct') == '70%')
    page.click('[data-sec="about"] .pv-pencil'); page.check('input[name="prog"] >> nth=0'); page.click('[data-sec="about"] .pv-done'); page.wait_for_timeout(200)
    ok('automatic again shows 0%', page.text_content('#pv .pct') == '0%')
    page.keyboard.press('Escape'); page.wait_for_timeout(200)

    # search filter dims non-matching buildings (Arabic search ignores hamza forms)
    page.keyboard.press('Escape'); page.wait_for_timeout(200)
    page.fill('#search', 'البلوت'); page.wait_for_timeout(300)
    ok('count line shows 1 of 3', '1 of 3' in page.text_content('#count'))
    page.screenshot(path=str(SHOTS / '15-search.png'))
    page.fill('#search', ''); page.wait_for_timeout(100)
    ok('no stage filters or fields remain', page.locator('.chip').count() == 0 and page.evaluate("() => DB.projects.every(p => !('stage' in p))"))

    # hold and drag a building to another plot
    page.evaluate("() => { MapView.deselect(); MapView.setCam({ x: 0, y: 230, z: 2 }); }"); page.wait_for_timeout(100)
    wiz = page.evaluate("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    a = page.evaluate(f"() => MapView.anchors('{wiz}')")
    sx, sy = left + a['topX'], (a['topY'] + a['baseY']) / 2
    dest = page.evaluate("() => MapView.plotCss(1, 1)")
    page.mouse.move(sx, sy); page.mouse.down(); page.wait_for_timeout(520)
    ok('hold picks the building up', page.evaluate("() => MapView.moving()"))
    before = page.evaluate(f"() => DB.projects.find(p => p.id === '{wiz}').plot")
    dx, dy = dest[0] + left - (left + page.evaluate(f"() => MapView.plotCss({before['u']}, {before['v']})")[0]), dest[1] - page.evaluate(f"() => MapView.plotCss({before['u']}, {before['v']})")[1]
    for k in range(1, 11): page.mouse.move(sx + dx * k / 10, sy + dy * k / 10); page.wait_for_timeout(16)
    page.screenshot(path=str(SHOTS / '16-moving.png'))
    page.mouse.up(); page.wait_for_timeout(300)
    after = page.evaluate(f"() => DB.projects.find(p => p.id === '{wiz}').plot")
    ok(f'building moved {before} -> {after}', after == {'u': 1, 'v': 1})

    # quick drag on the ground pans, does not select
    c0 = page.evaluate("() => MapView.camState()")
    page.mouse.move(left + 120, 820); page.mouse.down(); page.mouse.move(left + 220, 780, steps=6); page.mouse.up()
    ok('drag on ground pans', page.evaluate("() => MapView.camState().x") != c0['x'])

    # reload keeps everything
    page.wait_for_timeout(500)
    page.reload(); page.wait_for_timeout(600)
    ok('reload keeps 3 projects', page.evaluate("() => DB.projects.length") == 3)
    ok('reload keeps the moved plot', page.evaluate(f"() => DB.projects.find(p => p.id === '{wiz}').plot") == {'u': 1, 'v': 1})

    # block art upload, whole-block mode
    ncid = page.evaluate("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    a = page.evaluate(f"() => MapView.anchors('{ncid}')")
    page.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); page.wait_for_timeout(500)
    page.click('#enterBtn'); page.wait_for_timeout(300)
    page.click('.pv-scene'); page.wait_for_timeout(300)
    page.set_input_files('#pvSide input[type=file]', fixture('test-block.png')); page.wait_for_timeout(700)
    ok('art stored on project', page.evaluate(f"() => DB.projects.find(p => p.id === '{ncid}').art.has"))
    page.screenshot(path=str(SHOTS / '17-art-edit.png'))
    page.keyboard.press('Escape'); page.wait_for_timeout(200); page.keyboard.press('Escape'); page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / '18-art-map.png'))
    page.reload(); page.wait_for_timeout(900)
    ok('art survives reload', page.evaluate(f"() => !!Art.get('{ncid}')"))

    # export, then import it back
    with page.expect_download() as dl:
        open_settings(page, 'saving'); page.click('#btnExport')
    path = dl.value.path(); data = json.loads(pathlib.Path(path).read_text())
    ok(f"export has {len(data['projects'])} projects with art", len(data['projects']) == 3 and any('dataUrl' in q['art'] for q in data['projects']))
    (DATA / 'backup.json').write_text(json.dumps(data), encoding='utf-8')
    page.evaluate("() => { DB.projects = []; persistNow(); MapView.invalidate(); Menu.refresh(); }")
    page.set_input_files('#fileImport', str(DATA / 'backup.json')); page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / '19-import-confirm.png'))
    page.click('.confirm-actions .btn-danger'); page.wait_for_timeout(900)
    ok('import restores 3 projects', page.evaluate("() => DB.projects.length") == 3)
    ok('import restores art', page.evaluate(f"() => !!Art.get('{ncid}')"))

    # an old project: last touched 9 days ago
    page.evaluate(f"() => {{ const p = DB.projects.find(x => x.id === '{wiz}'); p.updatedAt = Date.now() - 9 * 864e5; persistNow(); MapView.invalidate(); Menu.refresh(); }}")
    page.wait_for_timeout(200)
    a = page.evaluate(f"() => MapView.anchors('{wiz}')")
    page.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); page.wait_for_timeout(600)
    page.screenshot(path=str(SHOTS / '20-stale.png'))
    ok('old projects just show their update time', 'Updated 9 days ago' in page.text_content('#bubble .meta') and 'Lights' not in page.text_content('#bubble .meta'))
    ok('menu has no lights note', 'Lights' not in page.text_content('#count'))

    # delete flow
    page.click('#enterBtn'); page.wait_for_timeout(300)
    page.click('#pvMore'); page.click('.pv-menu-item >> text=Delete project'); page.wait_for_timeout(200)
    page.screenshot(path=str(SHOTS / '21-delete-confirm.png'))
    page.keyboard.press('Escape'); page.wait_for_timeout(150)
    ok('Esc cancels the confirm but keeps the project view', page.is_visible('#pv') and page.evaluate("() => DB.projects.length") == 3)
    page.keyboard.press('Escape')
    b.close()

    # small screen and high density
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ctx.add_init_script(TEST_CITY)
    page = ctx.new_page(); attach(page)
    page.goto(FILE); page.wait_for_timeout(600)
    page.screenshot(path=str(SHOTS / '22-mobile.png'))
    page.click('#menuToggle'); page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / '23-mobile-menu.png'))
    b.close()

    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=2)
    ctx.add_init_script(TEST_CITY)
    page = ctx.new_page(); attach(page)
    page.goto(FILE); page.wait_for_timeout(600)
    page.screenshot(path=str(SHOTS / '24-dpr2.png'), clip={'x': 520, 'y': 300, 'width': 420, 'height': 320})
    b.close()

print('\n'.join(errors) if errors else 'no console errors')
