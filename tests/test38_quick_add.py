"""The one-line add over the map, rethought (0.1.56): Rethink the One-Line Add, Round 1, and the leader's toast asked in
the chat. Enter on the map opens the line (E1) and a double-click steps inside; every mark suggests as it is typed,
with the arrows, Tab and Enter (P1, P2, I1); the shift tags under the line (S1); only this line suggests (W1); marks in
their own colors; the line's building lit; the last project; Shift+Enter and Ctrl+Enter; and the leader's toast with
Open and Undo, which reopens the line with what was typed. Since 0.1.76 (The City on a Phone, Round 2): + Task after
+ New project opens it (A2), the status card has no add field (A3), and a computer shows no mark keys (A1a) and no
Pick a date (A4), which are a phone's."""
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1400, 'height': 860})
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(FILE); pg.wait_for_timeout(1500)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    task = lambda pid, text: ev(f"() => {{ const t = getProject('{pid}').todos.find(t => t.text === {text!r}); return t ? {{ ...t, ms: getProject('{pid}').milestones.find(m => m.id === t.milestoneId).name }} : null; }}")
    hint = lambda: pg.text_content('#quickAddHint')
    val = lambda: pg.input_value('#quickAddIn')
    lst = lambda: ev("() => QuickAdd._list()")
    labels = lambda: [x.get('label') or x.get('info') for x in (lst() or {'items': []})['items']]
    today = date.today()

    # ---------- the model ----------
    sp = ev("""() => { const v = 'Fix it /garden !oct 20 #every 3 days +think @launch bob@mail.com #1';
      return readTaskMarks(v, { cityWide: true, now: new Date(2026, 9, 19).getTime() }).spans.map(s => [s.kind, v.slice(s.start, s.end), s.shift || '']); }""")
    ok(f'the reader says where each mark sits, a date or a repeat over several words, a shift with its shift ({sp})',
       sp == [['/', '/garden', ''], ['!', '!oct 20', ''], ['#', '#every 3 days', ''], ['+', '+think', 'think'], ['@', '@launch', '']])
    ok('words that are not marks get no place, and a line with none has none', ev("() => readTaskMarks('Plan C++ +1 #1 priority', { cityWide: true }).spans.length") == 0)
    ok('the places count from the line as typed, spaces and all', ev("() => readTaskMarks('   Do it   !today').spans[0].start") == 11)
    mm = ev("""() => { const list = [{ name: 'Half-Cards' }, { name: 'Garden  planner' }, { name: 'Half' }];
      return [markMatch(list, x => x.name, 'half-cards'), markMatch(list, x => x.name, 'Half_Cards'), markMatch(list, x => x.name, 'garden-planner'), markMatch(list, x => x.name, 'half')].map(x => x && x.name); }""")
    ok(f'a name with a hyphen or two spaces is matched by a pick written with hyphens ({mm})', mm == ['Half-Cards', 'Half-Cards', 'Garden  planner', 'Half'])
    rk = ev("() => [['Garden planner', 'garden planner'], ['Garden planner', 'gar'], ['Garden planner', 'plan'], ['Garden planner', 'gp'], ['Garden planner', 'xz'], ['Garden planner', '']].map(([n, q]) => QuickAdd.rankOf(n, q))")
    ok(f'a name fits what is typed: itself, its start, a word\'s start, its letters in order, or not ({rk})', rk == [0, 1, 2, 3, -1, 0])
    order = ev(f"""() => {{ const now = Date.now(); for (const p of DB.projects) p.activity = (p.activity || []).filter(a => !a.text.startsWith('Added todo: '));
      getProject('{nc}').activity.push({{ at: now - 5000, text: 'Added todo: An old one' }});
      return [QuickAdd.byRecent().map(p => p.name), QuickAdd.lastProject().name]; }}""")
    ok(f'projects added to most recently come first, the rest by name, and the last one is remembered ({order})', order == [['Nullovation City', 'Garden planner'], 'Nullovation City'])
    ev("() => { for (const p of DB.projects) p.activity = (p.activity || []).filter(a => !a.text.startsWith('Added todo: ')); }")
    ok('with no task added anywhere, nothing is remembered', ev("() => QuickAdd.lastProject()") is None)

    # ---------- E1: Enter opens the line; a double-click steps inside ----------
    ev("() => MapView.deselect()"); pg.mouse.move(700, 450); pg.wait_for_timeout(200)
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok('E1 Enter on the map opens the line, focused and empty when nothing is selected or remembered',
       pg.is_visible('#quickAdd') and ev("() => document.activeElement.id") == 'quickAddIn' and val() == '' and not ev("() => FullView.isOpen()"))
    ok('its placeholder names the shift too', pg.get_attribute('#quickAddIn', 'placeholder') == 'A task, with /project !date #repeat @milestone +shift')
    ok('its head names the keys', pg.text_content('.quick-add-keys') == 'Enter adds · Shift+Enter adds and stays · Ctrl+Enter adds and opens')
    ok('the three shift tags sit under the line, none pressed', ev("() => [...document.querySelectorAll('.qa-shift')].map(b => [b.textContent, b.getAttribute('aria-pressed')])") == [['Create', 'false'], ['Think', 'false'], ['Errand', 'false']])
    ok('no list until a mark is typed', lst() is None and pg.is_hidden('#qaList'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    a = ev(f"() => MapView.anchors('{gp}')"); left = ev("() => document.querySelector('#map').getBoundingClientRect().left")
    pg.mouse.click(left + a['baseX'], a['baseY'] - 30); pg.wait_for_timeout(120); pg.mouse.click(left + a['baseX'], a['baseY'] - 30); pg.wait_for_timeout(400)
    ok('two single clicks do not step inside', not ev("() => FullView.isOpen()") and ev("() => App.selectedId") == gp)
    ev("() => document.activeElement && document.activeElement.blur()")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    pg.keyboard.type('Sort the seeds')
    ok(f"with a building selected, Enter opens the line on it ({hint()})", pg.is_visible('#quickAdd') and hint().startswith('Garden planner · In First release'))
    ok('the status card stays open behind it', pg.is_visible('#bubble'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes it, adding nothing', not pg.is_visible('#quickAdd') and task(gp, 'Sort the seeds') is None)
    a = ev(f"() => MapView.anchors('{gp}')")
    pg.mouse.dblclick(left + a['baseX'], a['baseY'] - 30); pg.wait_for_timeout(600)
    ok('a double-click on a building steps inside it', ev("() => FullView.isOpen() && FullView.currentId()") == gp)
    ev("() => { FullView.close(); MapView.deselect(); }"); pg.wait_for_timeout(300)
    a = ev(f"() => MapView.anchors('{nc}')")
    pg.mouse.dblclick(left + a['baseX'], a['baseY'] - 40); pg.wait_for_timeout(600)
    ok('one that is not selected yet too, whatever the map glides', ev("() => FullView.isOpen() && FullView.currentId()") == nc)
    ev("() => { FullView.close(); MapView.deselect(); }"); pg.wait_for_timeout(300)
    ev("() => Settings.open('city')"); ev("() => MapView.setEditing(true)"); pg.wait_for_timeout(300)
    a = ev(f"() => MapView.anchors('{gp}')")
    pg.mouse.dblclick(left + a['baseX'], a['baseY'] - 30); pg.wait_for_timeout(500)
    ok('not in Edit City', not ev("() => FullView.isOpen()"))
    ev("() => { MapView.setEditing(false); Settings.close(); MapView.deselect(); }"); pg.wait_for_timeout(300)

    # ---------- the suggestions: / ----------
    ev(f"() => {{ getProject('{gp}').activity.push({{ at: Date.now(), text: 'Added todo: Seed it' }}); }}")
    pg.mouse.move(700, 450); pg.keyboard.press('t'); pg.wait_for_timeout(250)
    ok(f"I1 with nothing open or selected the line starts on the project last added to ({val()})", val() == '/Garden-planner ' and hint().startswith('Garden planner · '))
    ok('and its building lights up on the map', ev("() => MapView._lit()") == gp)
    pg.fill('#quickAddIn', ''); pg.wait_for_timeout(100)
    ok('emptied, it lights nothing', ev("() => MapView._lit()") is None)
    pg.keyboard.type('Water the herbs /'); pg.wait_for_timeout(150)
    l = lst()
    ok(f"/ lists every project, the one last added to first, nothing highlighted yet ({labels()})", l and l['mark'] == '/' and labels() == ['Garden planner', 'Nullovation City'] and l['index'] == -1 and pg.is_visible('#qaList'))
    ok('each with its picture and its open tasks', pg.locator('#qaList .qa-opt').count() == 2 and pg.locator('#qaList .qa-thumb canvas').count() == 2 and pg.text_content('#qaList .qa-opt >> nth=0').endswith('5 open tasks'))
    ok('the field says the list is open', pg.get_attribute('#quickAddIn', 'aria-expanded') == 'true' and pg.get_attribute('#quickAddIn', 'role') == 'combobox')
    pg.keyboard.type('nc'); pg.wait_for_timeout(150)
    ok(f"letters in order match: /nc finds Nullovation City, highlighted ({labels()})", labels() == ['Nullovation City'] and lst()['index'] == 0)
    ok('the highlighted project lights its building', ev("() => MapView._lit()") == nc)
    pg.screenshot(path=str(SHOTS / '390-suggest-project.png'))
    pg.keyboard.press('Backspace'); pg.keyboard.press('Backspace'); pg.keyboard.type('g'); pg.wait_for_timeout(150)
    ok(f"a name's start comes first ({labels()})", labels()[0] == 'Garden planner' and lst()['index'] == 0)
    pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(80)
    ok('Down stays on the last one it can reach', lst()['index'] == min(1, len(labels()) - 1))
    pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(80)
    ok('Up moves back', lst()['index'] == 0 and pg.get_attribute('#quickAddIn', 'aria-activedescendant') == 'qaOpt0')
    pg.keyboard.press('Tab'); pg.wait_for_timeout(120)
    ok(f"Tab writes the pick over the mark, with a space, and closes the list ({val()!r})", val() == 'Water the herbs /Garden-planner ' and lst() is None and ev("() => document.activeElement.id") == 'quickAddIn')
    ok('the caret stays at the end', ev("() => document.activeElement.selectionStart") == len('Water the herbs /Garden-planner '))
    pg.keyboard.type('/'); pg.wait_for_timeout(120)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(120)
    ok('Esc closes the list first, leaving the line open', lst() is None and pg.is_visible('#quickAdd'))
    pg.keyboard.press('Backspace'); pg.wait_for_timeout(80)

    # ---------- @ ----------
    pg.keyboard.type('@'); pg.wait_for_timeout(150)
    ok(f"P2 @ lists the line's project's milestones, the one a task lands in first ({labels()})", labels() == ['First release', 'Launch'] and lst()['index'] == -1)
    pg.keyboard.type('pub'); pg.wait_for_timeout(150)
    ok(f"a name no milestone has offers a new one ({labels()})", labels() == ['New milestone pub'] and lst()['index'] == 0)
    for _ in range(3): pg.keyboard.press('Backspace')
    pg.keyboard.type('la'); pg.wait_for_timeout(150)
    ok(f"@la: Launch first, First release by its letters after, and a new one last ({labels()})", labels() == ['Launch', 'First release', 'New milestone la'])
    pg.click('#qaList .qa-opt >> nth=0'); pg.wait_for_timeout(120)
    ok(f"a click picks it, the focus kept in the line ({val()!r})", val() == 'Water the herbs /Garden-planner @Launch ' and ev("() => document.activeElement.id") == 'quickAddIn')
    pg.fill('#quickAddIn', 'Fix it @'); pg.wait_for_timeout(120)
    ok(f"with no project yet, @ asks for one first ({labels()})", labels() == ['Pick a project with / first'] and pg.locator('#qaList .qa-opt.info').count() == 1)
    pg.keyboard.press('Tab'); pg.wait_for_timeout(80)
    ok('and nothing there can be picked', val() == 'Fix it @')
    ev(f"""() => {{ const p = getProject('{gp}'); p.milestones.push({{ id: 'm_old', name: 'Old beds', collapsed: false }});
      p.todos.push(Object.assign(todo('Dug the old beds', 'm_old'), {{ done: true, doneAt: Date.now(), archived: true, archivedAt: Date.now() }})); changed(p); }}""")
    pg.fill('#quickAddIn', 'Fix it /garden @'); pg.wait_for_timeout(150)
    l = lst()
    ok(f"a milestone in the archive shows last, dimmed with the archive's icon ({labels()})", labels() == ['First release', 'Launch', 'Old beds'] and l['items'][2]['archived'] and pg.locator('#qaList .qa-opt.archived svg').count() == 1)

    # ---------- ! # + ----------
    pg.fill('#quickAddIn', 'Fix it /garden !'); pg.wait_for_timeout(150)
    l = lst(); d = [today + timedelta(days=i) for i in range(7)]
    fmt = lambda x: x.strftime('%a') + ' ' + str(x.day) + ' ' + x.strftime('%b')
    want = ['Today', 'Tomorrow'] + [x.strftime('%A') for x in d[2:]]
    ok(f"! lists today, tomorrow and the next five days, each with its date ({labels()})", labels() == want and [x['note'] for x in l['items']] == [fmt(x) for x in d])
    ok('A4 on a computer the list has no Pick a date: a later date is typed', 'Pick a date' not in labels())
    pg.keyboard.type(str((today + timedelta(days=12)).day)); pg.wait_for_timeout(150)
    l = lst()
    ok(f"a number offers that date first ({l['items'][0] if l else None})", l and l['items'][0]['mark'] == '!' + str((today + timedelta(days=12)).day) and l['items'][0]['label'] == fmt(today + timedelta(days=12)))
    pg.fill('#quickAddIn', 'Fix it /garden !tom'); pg.wait_for_timeout(150)
    pg.keyboard.press('Tab'); pg.wait_for_timeout(100)
    ok(f"Tab picks the first ({val()!r})", val() == 'Fix it /garden !tomorrow ')
    pg.keyboard.type('#'); pg.wait_for_timeout(150)
    l = lst(); tm = today + timedelta(days=1)
    ok(f"# lists the repeats ({labels()})", labels() == ['Daily', 'Weekly', 'Monthly', 'Yearly', 'Every N days'])
    ok(f"each saying when it starts, from the line's date ({[x['note'] for x in l['items']]})",
       l['items'][0]['note'] == 'Starts ' + fmt(tm) and l['items'][1]['note'] == 'On ' + tm.strftime('%a') + ', starts ' + fmt(tm) and l['items'][4]['note'] == 'Then type the number of days')
    pg.keyboard.type('ev'); pg.keyboard.press('Tab'); pg.wait_for_timeout(100)
    ok(f"Every N days leaves the number to type ({val()!r})", val() == 'Fix it /garden !tomorrow #every ' and lst() is None)
    pg.keyboard.type('3 days +'); pg.wait_for_timeout(150)
    ok(f"+ lists the three shifts in their tags ({labels()})", labels() == ['Create', 'Think', 'Errand'] and pg.locator('#qaList .shift-tag').count() == 3)
    pg.keyboard.type('e'); pg.keyboard.press('Tab'); pg.wait_for_timeout(120)
    ok(f"and Tab picks one ({hint()})", val() == 'Fix it /garden !tomorrow #every 3 days +errand ' and hint().endswith('Repeats every 3 days · Shift: Errand'))
    pg.screenshot(path=str(SHOTS / '391-marks.png'))

    # ---------- the colors ----------
    pc = ev("() => [...document.querySelectorAll('.qa-paint .qa-m')].map(e => [e.textContent, e.className, getComputedStyle(e).color])")
    ok(f"each mark shows in its own color as typed ({[x[:2] for x in pc]})", [x[0] for x in pc] == ['/garden', '!tomorrow', '#every 3 days', '+errand'] and len(set(x[2] for x in pc)) == 4)
    ok('a shift in its shift\'s own color', pc[3][2] == 'rgb(169, 226, 190)' and 'shift-errand' in pc[3][1])
    ok('the words stay plain, and the colored copy matches the line', ev("() => document.querySelector('.qa-paint').textContent") == val() + ' '
       and ev("() => getComputedStyle(document.querySelector('#quickAddIn')).color") == 'rgba(0, 0, 0, 0)')
    ok('the line\'s own text sits under its copy, in the same font', ev("() => { const a = getComputedStyle(document.querySelector('#quickAddIn')), b = getComputedStyle(document.querySelector('.qa-paint')); return a.fontFamily === b.fontFamily && a.fontSize === b.fontSize && a.paddingLeft === b.paddingLeft && a.borderLeftWidth === b.borderLeftWidth; }"))

    pg.fill('#quickAddIn', 'A very long task line that runs well past the end of the field, to see the colors keep up as it scrolls /garden !tomorrow')
    pg.keyboard.press('End'); pg.wait_for_timeout(150)
    sc = ev("() => [document.querySelector('#quickAddIn').scrollLeft, document.querySelector('.qa-paint').scrollLeft]")
    ok(f"a line longer than the field scrolls, and its colors scroll with it ({sc})", sc[0] > 0 and abs(sc[0] - sc[1]) < 1)
    pg.fill('#quickAddIn', 'Fix it /garden !tomorrow #every 3 days +errand '); pg.wait_for_timeout(100)

    # ---------- S1: the shift tags ----------
    ok('the shift picked is pressed under the line', ev("() => [...document.querySelectorAll('.qa-shift')].map(b => b.getAttribute('aria-pressed'))") == ['false', 'false', 'true'])
    pg.click('.qa-shift[data-shift="think"]'); pg.wait_for_timeout(100)
    ok(f"a click on another changes the mark ({val()!r})", val() == 'Fix it /garden !tomorrow #every 3 days +think ' and ev("() => document.activeElement.id") == 'quickAddIn')
    pg.click('.qa-shift[data-shift="think"]'); pg.wait_for_timeout(100)
    ok(f"a click on the pressed one takes it off ({val()!r})", val() == 'Fix it /garden !tomorrow #every 3 days ' and 'Shift' not in hint())
    pg.fill('#quickAddIn', 'Fix it'); pg.click('.qa-shift[data-shift="create"]'); pg.wait_for_timeout(100)
    ok(f"with none, a click adds it at the end ({val()!r})", val() == 'Fix it +create ' and ev("() => document.querySelector('.qa-shift[data-shift=create]').getAttribute('aria-pressed')") == 'true')

    # ---------- P1: Enter adds with the pick; the toast ----------
    pg.fill('#quickAddIn', 'Water the herbs /garden @la'); pg.wait_for_timeout(150)
    ok('(Launch highlighted)', lst() and lst()['index'] == 0 and labels()[0] == 'Launch')
    upd = ev(f"() => getProject('{gp}').updatedAt")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(350)
    t = task(gp, 'Water the herbs')
    ok(f"P1 Enter adds with the highlighted pick ({t and t['ms']})", t and t['ms'] == 'Launch' and not pg.is_visible('#quickAdd'))
    ok(f"with no leader the toast says where it went, with Open and Undo ({pg.text_content('#toast')})", pg.text_content('#toast').startswith('Added to Garden planner: Water the herbs.')
       and ev("() => [...document.querySelectorAll('#toast .toast-act')].map(b => b.textContent)") == ['Open', 'Undo'] and pg.locator('#toast .ld-face').count() == 0)
    ok('the building goes dark when the line closes', ev("() => MapView._lit()") is None)
    pg.click('#toast .toast-act >> text=Undo'); pg.wait_for_timeout(300)
    ok('Undo takes the task back out, with its Activity line', task(gp, 'Water the herbs') is None and ev(f"() => getProject('{gp}').activity.some(a => a.text === 'Added todo: Water the herbs')") is False)
    ok('and Updated as it was', ev(f"() => getProject('{gp}').updatedAt") == upd)
    ok(f"and reopens the line with what was typed ({val()!r})", pg.is_visible('#quickAdd') and val() == 'Water the herbs /garden @Launch ' and ev("() => document.activeElement.id") == 'quickAddIn')
    pg.fill('#quickAddIn', 'Water the herbs /garden @Herb-bed'); pg.keyboard.press('Escape'); pg.wait_for_timeout(80)
    pg.keyboard.press('Enter'); pg.wait_for_timeout(350)
    ok('a new milestone named with @ is made with it', task(gp, 'Water the herbs')['ms'] == 'Herb-bed')
    pg.click('#toast .toast-act >> text=Undo'); pg.wait_for_timeout(300)
    ok('and Undo takes the milestone too, with its line', ev(f"() => getProject('{gp}').milestones.some(m => m.name === 'Herb-bed')") is False
       and ev(f"() => getProject('{gp}').activity.some(a => a.text === 'New milestone: Herb-bed')") is False)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # the leader says it
    ev(f"""async () => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Nullovations', color: '#7FD6CE' }}); DB.leaders.push(l); setLeader(getProject('{gp}'), l.id);
      await Store.putArt(portraitKey(l.id), PORTRAITS.gus); l.portrait = true; await Leaders.loadAll(); changed(getProject('{gp}')); }}""")
    pg.wait_for_timeout(300)
    pg.mouse.move(700, 450); ev("() => document.activeElement && document.activeElement.blur()")
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.fill('#quickAddIn', 'Label the rows /garden !today'); pg.keyboard.press('Enter'); pg.wait_for_timeout(400)
    ok(f"with a leader, the leader says it: \"Task added: <task>.\" ({pg.text_content('#toast .toast-msg')})", pg.text_content('#toast .toast-msg') == 'Task added: Label the rows.')
    ok('with the leader\'s face, name and building', pg.locator('#toast .ld-face img.face-pic').count() == 1 and pg.text_content('#toast .toast-who b') == 'Talal'
       and pg.text_content('#toast .toast-who span') == 'Garden planner' and 'has-lead' in pg.get_attribute('#toast', 'class'))
    ok('and Open and Undo', ev("() => [...document.querySelectorAll('#toast .toast-act')].map(b => b.textContent)") == ['Open', 'Undo'])
    pg.screenshot(path=str(SHOTS / '392-leader-toast.png'))
    pg.click('#toast .toast-act >> text=Open'); pg.wait_for_timeout(500)
    ok('Open opens the task in its project', ev("() => FullView.currentId()") == gp and pg.input_value('#pvTaskTitle') == 'Label the rows')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); ev("() => FullView.close()"); pg.wait_for_timeout(200)
    ev(f"() => setLeader(getProject('{nc}'), '')")
    ev(f"() => {{ const l = DB.leaders[0]; l.portrait = false; Leaders.refreshAll(); }}")
    pg.mouse.move(700, 450); pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.fill('#quickAddIn', 'Mulch the beds /garden'); pg.keyboard.press('Enter'); pg.wait_for_timeout(400)
    ok('a leader without a portrait shows its silhouette', pg.locator('#toast .ld-face svg').count() == 1 and pg.locator('#toast .ld-face img').count() == 0)

    # ---------- Shift+Enter and Ctrl+Enter ----------
    pg.mouse.move(700, 450); pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.fill('#quickAddIn', 'Sow the peas /garden'); pg.keyboard.press('Shift+Enter'); pg.wait_for_timeout(350)
    ok(f"Shift+Enter adds it and stays open, emptied, on the same project ({val()!r})", task(gp, 'Sow the peas') and pg.is_visible('#quickAdd') and val() == '/Garden-planner ' and ev("() => document.activeElement.id") == 'quickAddIn')
    pg.keyboard.type('Sow the beans'); pg.keyboard.press('Shift+Enter'); pg.wait_for_timeout(350)
    ok('and the next one goes there too', task(gp, 'Sow the beans') is not None and val() == '/Garden-planner ')
    pg.click('#toast .toast-act >> text=Undo'); pg.wait_for_timeout(300)
    ok(f"Undo with the line still empty fills it again ({val()!r})", task(gp, 'Sow the beans') is None and val() == '/Garden-planner Sow the beans')
    pg.fill('#quickAddIn', 'Hoe the rows /garden'); pg.keyboard.press('Control+Enter'); pg.wait_for_timeout(600)
    ok('Ctrl+Enter adds it and opens it in its panel, ready for a description', task(gp, 'Hoe the rows') and not pg.is_visible('#quickAdd') and ev("() => FullView.currentId()") == gp and pg.input_value('#pvTaskTitle') == 'Hoe the rows')
    pg.click('#toast .toast-act >> text=Undo'); pg.wait_for_timeout(400)
    ok('Undo then closes its panel, with nothing written for it', task(gp, 'Hoe the rows') is None and pg.locator('#pvTaskTitle').count() == 0
       and not ev(f"() => getProject('{gp}').activity.some(a => a.text.includes('Hoe the rows'))") and pg.is_visible('#quickAdd'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); ev("() => FullView.close()"); pg.wait_for_timeout(200)

    # ---------- W1: only the line over the map suggests; the status card has no add field since 0.1.76 (A3) ----------
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(500)
    ok('A3 the status card has no add field', pg.is_visible('#bubble') and pg.locator('#bubble input:not(.cb)').count() == 0)
    ev("() => MapView.deselect()"); pg.wait_for_timeout(200)
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.click('.ms >> nth=0 >> .ms-plus'); pg.keyboard.type('Rake it @la'); pg.wait_for_timeout(200)
    ok('W1 the project view\'s add field shows no list and no colors', pg.locator('#qaList:visible').count() == 0 and pg.locator('#pv .qa-paint').count() == 0)
    pg.keyboard.press('Escape'); ev("() => FullView.close()"); pg.wait_for_timeout(200)

    # ---------- + Task after + New project (0.1.76, A2); on a computer, no mark keys (A1a) ----------
    bt = ev("""() => { const n = document.querySelector('#btnNew').getBoundingClientRect(), b = document.querySelector('#btnTask'), t = b.getBoundingClientRect();
      return { same: Math.abs(n.top - t.top) < 2, after: t.left > n.right, text: b.textContent.trim(), name: b.getAttribute('aria-label'), title: b.title }; }""")
    ok(f'A2 + Task sits right after + New project, on its row ({bt})', bt['same'] and bt['after'] and bt['text'] == 'Task' and bt['name'] == 'Add a task' and bt['title'] == 'Add a task (T)')
    pg.screenshot(path=str(SHOTS / '393-task-button.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 200})
    pg.click('#btnTask'); pg.wait_for_timeout(250)
    ok('a click opens the line over the map, focused', pg.is_visible('#quickAdd') and ev("() => document.activeElement.id") == 'quickAddIn')
    ok('A1a on a computer the line has no mark keys: a mark is one key on a keyboard', pg.locator('.qa-keys').count() == 1 and not pg.is_visible('.qa-keys'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes it, the focus back on + Task', not pg.is_visible('#quickAdd') and ev("() => document.activeElement.id") == 'btnTask')
    pg.click('#btnNew'); pg.wait_for_timeout(150)
    ok('naming a new project takes the row: both buttons step aside for the name', pg.is_visible('#newName') and not pg.is_visible('#btnTask') and not pg.is_visible('#btnNew'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('and come back with Esc', pg.is_visible('#btnTask') and pg.is_visible('#btnNew') and ev("() => document.activeElement.id") == 'btnNew')

    # ---------- Arabic, and nothing saved for the line ----------
    pg.mouse.move(700, 450); ev("() => { MapView.deselect(); document.activeElement && document.activeElement.blur(); }")
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.fill('#quickAddIn', 'سقي الأعشاب /garden +t'); pg.wait_for_timeout(120)
    ok('an Arabic title keeps its marks colored', ev("() => [...document.querySelectorAll('.qa-paint .qa-m')].map(e => e.textContent)") == ['/garden', '+t'] and hint().startswith('Garden planner'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    ok('and adds', task(gp, 'سقي الأعشاب') is not None and task(gp, 'سقي الأعشاب')['shift'] == 'think')
    ok('nothing new is saved for the line', ev("() => Object.keys(localStorage).filter(k => /quick/i.test(k)).length") == 0)
    b.close()
print(errors or 'no console errors')
