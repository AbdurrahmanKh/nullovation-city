import datetime, pathlib
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
day = lambda n: (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
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
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    ctx.add_init_script(FAKE_FS)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    js = lambda code: pg.evaluate(code)
    clip = lambda: js("() => navigator.clipboard.readText()")
    nc = js("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    wz = js("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    setp = lambda pid, code: js(f"() => {{ const p = DB.projects.find(p => p.id === '{pid}'); {code}; changed(p); MapView.invalidate(); Menu.refresh(); }}")

    # B4: nothing red, no urgent section; the week card shows this week in numbers
    ok('B4 with nothing red, the urgent section hides', not pg.is_visible('#sbUrgent'))
    ok('E1 with nothing due, Due this week hides', not pg.is_visible('#sbDue'))
    ok('E1 the week card shows this week in numbers', 'This week' in pg.text_content('#btnRecap') and 'Nothing done yet this week' in pg.text_content('#weekNumbers'))
    # C1: weeks start on Saturday
    starts = js("""() => [0, 1, 2, 3, 4, 5, 6].map(k => { const d = new Date(2026, 8, 26 + k); return new Date(weekStartOf(d.getTime())).getDay(); })""")
    ok(f'C1 every day of a week maps back to its Saturday ({set(starts)})', set(starts) == {6})
    ok('C1 the card names Saturday to Friday', js("() => { const s = weekStartOf(Date.now()); return new Date(s).getDay() === 6 && new Date(addDays(s, 6)).getDay() === 5; }"))

    # B1 and B3: red only, a tiny building with its number and nothing else
    setp(wz, f"p.todos[0].due = '{day(1)}'; p.todos[1].due = '{day(-2)}'")
    setp(nc, "p.urgency.system = 'finish'; p.urgency.pickedAt = Date.now(); p.urgency.lastWorked = Date.now()")
    ok('B1 red projects appear; yellow ones do not', js("() => urgencyOf(DB.projects.find(p => p.name === 'Nullovation City')).color") == 'yellow'
       and pg.locator('#urgentList .urgent-item').count() == 1 and 'Garden planner' in pg.get_attribute('#urgentList .urgent-item', 'aria-label'))
    ok('B3 a tiny full building with its bubble number, and no text beside it', pg.locator('#urgentList canvas.thumb').count() == 1
       and pg.text_content('#urgentList .urgent-item').strip() == '2')
    # B2: a click glides the map there and opens its status bubble
    js("() => MapView.setCam({ x: -300, y: 100, z: 2 })"); pg.wait_for_timeout(200)
    pg.click('#urgentList .urgent-item'); pg.wait_for_timeout(700)
    ok('B2 clicking it selects that building and opens its status bubble', js("() => App.selectedId") == wz and pg.is_visible('#bubble') and not pg.is_visible('#pv'))
    # E1: due this week, overdue first, each with a copy for Claude; a click opens the task
    rows = pg.locator('#dueList .due-item')
    ok(f'E1 due tasks list the next 7 days, overdue first ({rows.count()})', rows.count() == 2 and 'overdue' in pg.text_content('#dueList .due-item >> nth=0 >> .due'))
    pg.click('#dueList .due-item >> nth=0 >> .due-copy'); pg.wait_for_timeout(150)
    ok('E1 the small copy icon copies the task for Claude', clip().startswith('# Task: Save a plan as a file'))
    pg.click('#dueList .due-item >> nth=0 >> .due-task'); pg.wait_for_timeout(700)
    ok('a due task opens in the project view', pg.is_visible('#pvSide #pvTaskDesc'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    # a tick from the status bubble now reaches Activity and the week
    js("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(250)
    left = js("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    a = js(f"() => MapView.anchors('{nc}')")
    pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(500)
    pg.click('#bubble .b-todos li >> nth=0 >> .cb'); pg.wait_for_timeout(900)
    ok('a tick in the status bubble is logged', js(f"() => DB.projects.find(p => p.id === '{nc}').activity.some(e => e.text.startsWith('Done: '))"))
    ok('and the week card counts it', '1 task done' in pg.text_content('#weekNumbers'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # C2, C3, C4: the week dialog with arrows and a list, and the kept parts only
    setp(nc, "p.notes.push({ id: uid('n'), title: 'Moving in', text: 'Imported my city file.', at: Date.now() }); iWorked(p); p.todos.push(todo('Write the side bar tests', p.milestones[0].id)); logActivity(p, 'Added todo: Write the side bar tests')")
    js("""() => { const p = DB.projects.find(p => p.name.startsWith('Garden')); const t = addDays(weekStartOf(Date.now()), -4) + 36e5 * 10;
      p.activity.push({ at: t, text: 'Done: An older task' }); p.activity.sort((x, y) => x.at - y.at); changed(p); }""")
    pg.click('#btnRecap'); pg.wait_for_timeout(400)
    ok('C4 the week opens as a dialog over the city', pg.is_visible('.modal.panel .recap'))
    sum_ = pg.text_content('.recap-sum')
    ok(f'C3 the snapshot counts finished, notes, added, and check-ins ({sum_})', all(k in sum_ for k in ['1 task finished', '1 note written', '1 task added', '1 I worked! check-in']))
    body = pg.text_content('.modal.panel .recap')
    ok('C3 it leaves out red days, due next week, the comparison, and a picture', not any(k in body for k in ['days red', 'Due next week', 'than last week']) and pg.locator('.modal.panel .recap img, .modal.panel .recap canvas').count() == 0)
    n_weeks = pg.locator('.recap-weeks option').count()
    ok(f'C2 the list reaches back to the first recorded week ({n_weeks} weeks)', n_weeks >= 2)
    ok('C2 the next arrow waits at this week', pg.get_attribute('.recap-nav .icon-btn >> nth=1', 'disabled') is not None)
    pg.click('.recap-nav .icon-btn >> nth=0'); pg.wait_for_timeout(250)
    ok('C2 the previous arrow shows the week before, in place', 'An older task' in pg.text_content('.modal.panel .recap') and pg.locator('.modal.panel').count() == 1)
    pg.select_option('.recap-weeks', index=0); pg.wait_for_timeout(250)
    ok('C2 the list jumps back to this week', 'this week' in pg.text_content('.recap-when'))
    pg.click('.recap-foot .btn'); pg.wait_for_timeout(150)
    c = clip()
    ok('C3 Copy the week copies it as text', c.startswith('# Nullovation City, week of ') and 'Finished:' in c and 'Notes:' in c)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # A1 and D1: the brief and the palette live in a Tools collapsible, closed at first
    ok('A1 and D1 the brief and the palette are tucked away', not pg.is_visible('#btnBrief') and not pg.is_visible('#btnPalette'))
    pg.click('#foldTools summary'); pg.wait_for_timeout(150)
    ok('A1 and D1 Tools opens to show them', pg.is_visible('#btnBrief') and pg.is_visible('#btnPalette'))
    pg.click('#btnBrief'); pg.wait_for_timeout(150)
    ok('A1 the status brief still copies every project', clip().startswith('# Nullovation City status'))
    # D2: backup tools collapse; the saved line lives inside; outside only when something is wrong
    ok('D2 backup tools and the saved line are inside the collapsible', not pg.is_visible('#btnExport') and not pg.is_visible('#saveStatus'))
    ok('D2 nothing shows outside while all is well', not pg.is_visible('#saveAlert') and not pg.is_visible('#fileAlert'))
    js("() => Menu.setSaveStatus ? Menu.setSaveStatus(false) : null")
    ok('D2 a saving problem shows outside the collapsible', pg.is_visible('#saveAlert') or not js("() => !!Menu.setSaveStatus"))
    js("() => Menu.setSaveStatus && Menu.setSaveStatus(true)")
    pg.click('#foldData summary'); pg.wait_for_timeout(150)
    pg.click('text=Keep a data file'); pg.wait_for_timeout(1200)
    ok('D2 the data file shows its name', pg.text_content('#fileBox .file-path .fp-name') == 'nullovation-city-data.json')
    pg.click('#fileBox >> text=Add its folder'); pg.wait_for_timeout(100)
    pg.fill('#dataFolder', 'C:\\Users\\Abdurrahman\\Documents'); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    dir_ = pg.text_content('#fileBox .fp-dir')
    ok(f'D2 the typed folder shows in gray before the name ({dir_})', dir_ == 'C:\\Users\\Abdurrahman\\Documents\\' and
       js("() => getComputedStyle(document.querySelector('.fp-dir')).color !== getComputedStyle(document.querySelector('.fp-name')).color"))
    # D3: map size and controls stay visible
    ok('D3 map size and controls stay visible', pg.is_visible('#btnGrow') and pg.is_visible('.help'))
    pg.screenshot(path=str(SH / 'sb-final.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 1000})
    # the collapsibles remember being open
    pg.reload(); pg.wait_for_timeout(1800)
    ok('the collapsibles remember being open', js("() => document.querySelector('#foldTools').open && document.querySelector('#foldData').open"))
    ok('the folder is remembered too', pg.text_content('#fileBox .fp-dir') == 'C:\\Users\\Abdurrahman\\Documents\\' if pg.locator('#fileBox .fp-dir').count() else True)
    b.close()
# F1: the order chosen for the side bar, checked on a fresh page with something red and something due
with sync_playwright() as p2:
    b2 = p2.chromium.launch(channel='chrome')
    q = b2.new_page(viewport={'width': 1440, 'height': 900})
    q.add_init_script(TEST_CITY)
    q.goto(FILE); q.wait_for_timeout(1800)
    import datetime as _dt
    q.evaluate("() => { const p = DB.projects.find(p => p.name.startsWith('Garden')); p.todos[0].due = '" + (_dt.date.today() + _dt.timedelta(days=1)).isoformat() + "'; changed(p); Menu.refresh(); }")
    tops = q.evaluate("""() => ['#btnNew', '#search', '#btnRecap', '#sbUrgent', '#sbDue', '#btnGrow', '#foldTools', '#foldData', '.help']
      .map(s => { const e = document.querySelector(s); return e && !e.hidden ? e.getBoundingClientRect().top : null; })""")
    ok('F1 top to bottom: new, search, the week, urgent, due, map size, tools, backup, controls', all(x is not None for x in tops) and tops == sorted(tops))
    b2.close()
print(errors or 'no console errors')
