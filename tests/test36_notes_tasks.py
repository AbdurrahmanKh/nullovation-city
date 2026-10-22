"""Tasks into notes, and notes into tasks (0.1.54): some tasks are better kept as open ideas, and an idea can become a
task again. And the project view shows its links above its notes."""
import json, time
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
    proj = lambda pid=gp: ev(f"() => JSON.parse(JSON.stringify(getProject('{pid}')))")
    tid_of = lambda text, pid=gp: ev(f"() => (getProject('{pid}').todos.find(t => t.text === {json.dumps(text)}) || {{}}).id || null")
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay').forEach(e => e.hidden = true); }")
    toast = lambda: ev("() => { const t = document.querySelector('#toast'); return t.classList.contains('show') ? t.firstChild.textContent : ''; }")
    undo = lambda: ev("() => { const b = document.querySelector('#toast.show .toast-act'); if (!b) return false; b.click(); return true; }")
    active = lambda: ev("() => document.activeElement && document.activeElement.id")
    side_has = lambda sel: pg.locator('#pvSide ' + sel).count() > 0
    lines = lambda pid=gp: [e['text'] for e in proj(pid)['activity']]
    day = lambda n: (date.today() + timedelta(days=n)).isoformat()
    def done_btn():
        pg.click('#pvSide .pv-top .btn-accent'); pg.wait_for_timeout(250)
    def open_view(pid):
        ev(f"() => FullView.open('{pid}')"); pg.wait_for_timeout(500); quiet()

    # the city: notes, and a task with everything a task can carry
    ev(f"""() => {{ const p = getProject('{gp}');
      p.notes.push({{ id: 'n_seed', title: 'A seed library', text: 'Keep every seed packet in a drawer.\\nSort them by month.', at: Date.now() - 2 * 86400000 }});
      p.notes.push({{ id: 'n_bare', title: '', text: 'Try raised beds\\nThey drain better and save the back.', at: Date.now() - 86400000 }});
      const t = p.todos.find(x => x.text === 'Tune the watering reminders');
      Object.assign(t, {{ description: 'Morning and evening, by the weather.', due: '{day(3)}', repeat: {{ every: 'week', days: [1] }}, shift: 'think' }});
      setPin(p, t, true);
      changed(p); }}""")
    open_view(gp)

    # ---------- links above notes ----------
    order = ev("() => [...document.querySelectorAll('#pv .pv-cols > .pv-col')].map(c => [...c.querySelectorAll(':scope > .pv-sec')].map(s => s.dataset.sec))")
    ok('Todos keeps the left column; Links come first in the right one, Notes under them', order == [['todos'], ['links', 'notes']], order)
    lb = pg.query_selector('[data-sec="links"]').bounding_box(); nb = pg.query_selector('[data-sec="notes"]').bounding_box()
    tb = pg.query_selector('[data-sec="todos"]').bounding_box()
    ok('on screen: Links above Notes, in one column beside Todos', lb['y'] + lb['height'] <= nb['y'] + 1 and abs(lb['x'] - nb['x']) < 2 and lb['x'] > tb['x'] + tb['width'])
    ok('Links sit at the top of the column, level with Todos', abs(lb['y'] - tb['y']) < 2)
    pg.screenshot(path=str(SHOTS / '360-links-above-notes.png'), clip=pg.query_selector('#pv .pv-cols').bounding_box())

    # ---------- a task into a note ----------
    before = proj()
    tid = tid_of('Tune the watering reminders')
    idx = [t['id'] for t in before['todos']].index(tid)
    pg.click(f'li.task[data-id="{tid}"] .task-title'); pg.wait_for_timeout(300)
    ok('the task panel has Turn into a note', pg.is_visible('#pvSide #pvTaskToNote') and pg.text_content('#pvTaskToNote').strip() == 'Turn into a note')
    tn = pg.query_selector('#pvTaskToNote').bounding_box(); dl = pg.query_selector('#pvTaskDelete').bounding_box()
    ok('at the panel\'s foot, on Delete task\'s row, left of it', abs(tn['y'] - dl['y']) < 2 and tn['x'] + tn['width'] < dl['x'])
    ok('its tooltip says what stays and what goes', 'title and description stay' in pg.get_attribute('#pvTaskToNote', 'title') and 'date, repeat and shift go' in pg.get_attribute('#pvTaskToNote', 'title'))
    ev("() => { const s = document.querySelector('#pvSide'); s.scrollTop = s.scrollHeight; }"); pg.wait_for_timeout(100)
    pg.screenshot(path=str(SHOTS / '361-task-to-note.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.fill('#pvTaskTitle', 'Tune the watering reminders by season'); pg.wait_for_timeout(100)
    t0 = time.time() * 1000
    pg.click('#pvTaskToNote'); pg.wait_for_timeout(450)
    after = proj()
    note = next((n for n in after['notes'] if n['title'] == 'Tune the watering reminders by season'), None)
    ok('the task is gone from the project', tid not in [t['id'] for t in after['todos']] and pg.locator(f'li.task[data-id="{tid}"]').count() == 0)
    ok('a note in its place: the title, as edited in the panel, and the description as its text', note is not None and note['text'] == 'Morning and evening, by the weather.', note)
    ok('written now', note is not None and abs(note['at'] - t0) < 15000)
    ok('the note opens where the task was, the focus in its text', side_has('#pvNoteBody') and not side_has('#pvTaskTitle') and active() == 'pvNoteBody'
       and pg.input_value('#pvNoteTitle') == 'Tune the watering reminders by season')
    ok('its card shows under Notes, picked', note is not None and pg.locator(f'.pv-note-card.on[data-id="{note["id"]}"]').count() == 1)
    ok('the toast says so, with Undo', toast() == 'Turned Tune the watering reminders by season into a note.' and pg.locator('#toast.show .toast-act').text_content() == 'Undo', toast())
    log = lines()
    ok('Activity: the edit, then "Turned into a note: <title>"', log[-1] == 'Turned into a note: Tune the watering reminders by season' and log[-2] == 'Edited task: Tune the watering reminders by season', log[-3:])
    ok('Updated changes; urgency does not, since it is not work', after['updatedAt'] > before['updatedAt'] and after['urgency']['lastWorked'] == before['urgency']['lastWorked'])
    ok('the pin goes with the task', after['pin'] == '')
    ok('its milestone counts one task fewer', pg.text_content('.ms[data-msid="m_first"] .ms-count') == '(0/3)')
    pg.screenshot(path=str(SHOTS / '362-turned-into-note.png'))

    # Undo puts back exactly what was there
    ok('Undo is offered', undo()); pg.wait_for_timeout(450)
    back = proj()
    bt = next((t for t in back['todos'] if t['id'] == tid), None)
    ok('Undo brings the task back to its place in the list', [t['id'] for t in back['todos']] == [t['id'] for t in before['todos']] and [t['id'] for t in back['todos']].index(tid) == idx)
    ok('with its milestone, due date, repeat, shift and description', bt is not None and bt['milestoneId'] == 'm_first' and bt['due'] == day(3) and bt['repeat'] == {'every': 'week', 'days': [1]}
       and bt['shift'] == 'think' and bt['description'] == 'Morning and evening, by the weather.', bt)
    ok('as it was just before: the panel\'s edit kept', bt is not None and bt['text'] == 'Tune the watering reminders by season')
    ok('and its pin', back['pin'] == tid)
    ok('the note is gone, and so is its line in Activity', not any(n['title'] == 'Tune the watering reminders by season' for n in back['notes'])
       and 'Turned into a note: Tune the watering reminders by season' not in lines())
    ok('its panel opens again, the focus on Turn into a note', side_has('#pvTaskTitle') and active() == 'pvTaskToNote')
    done_btn(); quiet()

    # ---------- a note into a task ----------
    before = proj()
    nidx = [n['id'] for n in before['notes']].index('n_seed')
    pg.click('.pv-note-card[data-id="n_seed"]'); pg.wait_for_timeout(300)
    ok('the note panel has Turn into a task', pg.is_visible('#pvSide #pvNoteToTask') and pg.text_content('#pvNoteToTask').strip() == 'Turn into a task')
    tt = pg.query_selector('#pvNoteToTask').bounding_box(); dn = pg.query_selector('#pvNoteDelete').bounding_box()
    ok('at the panel\'s foot, as in the task panel: on Delete note\'s row, left of it', abs(tt['y'] - dn['y']) < 2 and tt['x'] + tt['width'] < dn['x'])
    ok('the line on when it was written sits under them', pg.query_selector('#pvSide .pv-note-foot + .note').bounding_box()['y'] > dn['y'] + dn['height']
       and pg.text_content('#pvSide .pv-note-foot + .note').startswith('Written '))
    ok('its tooltip names the milestone it goes to', 'a task in First release' in pg.get_attribute('#pvNoteToTask', 'title'))
    pg.screenshot(path=str(SHOTS / '363-note-to-task.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.click('#pvNoteToTask'); pg.wait_for_timeout(450)
    after = proj()
    nt = next((t for t in after['todos'] if t['text'] == 'A seed library'), None)
    first = [t for t in after['todos'] if t['milestoneId'] == 'm_first']
    ok('a task named by the note\'s title, its text as the description', nt is not None and nt['description'] == 'Keep every seed packet in a drawer.\nSort them by month.', nt)
    ok('in the current milestone, at its end, as a task added without @', nt is not None and nt['milestoneId'] == 'm_first' and first[-1]['id'] == nt['id'])
    ok('open, with no date, repeat or shift', nt is not None and not nt['done'] and nt['due'] == '' and 'repeat' not in nt and 'shift' not in nt)
    ok('the note is gone', not any(n['id'] == 'n_seed' for n in after['notes']) and pg.locator('.pv-note-card[data-id="n_seed"]').count() == 0)
    ok('the task opens where the note was, its row picked in the list', side_has('#pvTaskTitle') and pg.input_value('#pvTaskTitle') == 'A seed library'
       and nt is not None and pg.locator(f'li.task.on[data-id="{nt["id"]}"]').count() == 1)
    ok('the toast says where it went, with Undo', toast() == 'Turned A seed library into a task in First release.', toast())
    ok('Activity: "Turned into a task: <title>"', lines()[-1] == 'Turned into a task: A seed library')
    ok('it is not work either', after['urgency']['lastWorked'] == before['urgency']['lastWorked'] and after['updatedAt'] >= before['updatedAt'])
    recap_added = f"() => (weekOf(weekStartOf(Date.now())).rows.find(r => r.p.id === '{gp}') || {{ added: [] }}).added.map(a => a.text)"
    ok('the week\'s recap counts it as a task added', 'A seed library' in ev(recap_added))
    ok('Undo is offered', undo()); pg.wait_for_timeout(450)
    back = proj()
    bn = next((n for n in back['notes'] if n['id'] == 'n_seed'), None)
    ok('Undo puts the note back, as it was and in its place', bn is not None and [n['id'] for n in back['notes']].index('n_seed') == nidx and bn['title'] == 'A seed library'
       and bn['text'] == 'Keep every seed packet in a drawer.\nSort them by month.' and bn['at'] == next(n for n in before['notes'] if n['id'] == 'n_seed')['at'])
    ok('the task is gone, and so is its line', not any(t['text'] == 'A seed library' for t in back['todos']) and 'Turned into a task: A seed library' not in lines())
    ok('the recap no longer counts it', 'A seed library' not in ev(recap_added))
    ok('the note\'s panel opens again, the focus on Turn into a task', side_has('#pvNoteTitle') and active() == 'pvNoteToTask')
    done_btn(); quiet()

    # a note without a title: its first line names the task, the rest describes it
    pg.click('.pv-note-card[data-id="n_bare"]'); pg.wait_for_timeout(300)
    pg.click('#pvNoteToTask'); pg.wait_for_timeout(450)
    bt = next((t for t in proj()['todos'] if t['text'] == 'Try raised beds'), None)
    ok('a note with no title: its first line names the task, the rest describes it', bt is not None and bt['description'] == 'They drain better and save the back.', bt)
    # and back: the round trip keeps the words
    pg.click('#pvTaskToNote'); pg.wait_for_timeout(450)
    rn = next((n for n in proj()['notes'] if n['title'] == 'Try raised beds'), None)
    ok('and back into a note: the words survive the round trip', rn is not None and rn['text'] == 'They drain better and save the back.', rn)
    pg.fill('#pvNoteBody', 'Changed my mind'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    rn2 = next((n for n in proj()['notes'] if rn and n['id'] == rn['id']), None)
    ok('Esc in the note it became undoes only the typing since it opened: the note stays', rn2 is not None and rn2['text'] == 'They drain better and save the back.' and not pg.is_visible('#pvSide'), rn2)
    quiet()

    # a title too long for a note's: the note opens with it, the description after it
    long_t = 'Plan the beds ' + 'and the paths between them ' * 9
    long_t = long_t.strip()
    ev(f"() => {{ const p = getProject('{gp}'); p.todos.push(Object.assign(todo({json.dumps(long_t)}, 'm_launch'), {{ description: 'Sketch first.' }})); normalizeOrder(p); changed(p); FullView.render(); }}")
    lt = tid_of(long_t)
    pg.click(f'li.task[data-id="{lt}"] .task-title'); pg.wait_for_timeout(300)
    pg.click('#pvTaskToNote'); pg.wait_for_timeout(450)
    ln = next((n for n in proj()['notes'] if n['text'].startswith('Plan the beds')), None)
    ok(f'a title over 200 characters ({len(long_t)}) is not cut: the note has no title and opens with it', ln is not None and ln['title'] == '' and ln['text'] == long_t + '\n\nSketch first.', ln)
    ok('its card shows it as the heading', ln is not None and pg.text_content(f'.pv-note-card[data-id="{ln["id"]}"] .pv-note-h').startswith('Plan the beds'))
    pg.click('#pvNoteToTask'); pg.wait_for_timeout(450)
    lt2 = next((t for t in proj()['todos'] if t['text'] == long_t), None)
    ok('and back into a task: the whole title, the description after it', lt2 is not None and lt2['description'] == 'Sketch first.', lt2)
    done_btn(); quiet()

    # ---------- which tasks and notes ----------
    pg.click('#pvAddNoteBtn'); pg.wait_for_timeout(250)
    ok('a new, empty note cannot be turned yet', pg.is_disabled('#pvNoteToTask'))
    pg.fill('#pvNoteTitle', 'Compost corner'); pg.wait_for_timeout(100)
    ok('once it has words, it can', not pg.is_disabled('#pvNoteToTask'))
    pg.click('#pvNoteToTask'); pg.wait_for_timeout(450)
    log = lines()
    ok('a new note turned at once: written, then turned', log[-2:] == ['Wrote a note: Compost corner', 'Turned into a task: Compost corner'], log[-3:])
    done_btn(); quiet()
    dt = tid_of('Save a plan as a file')
    pg.click(f'li.task[data-id="{dt}"] .cb'); pg.wait_for_timeout(200)
    pg.click(f'li.task[data-id="{dt}"] .task-title'); pg.wait_for_timeout(300)
    ok('a done task can be turned too', pg.is_visible('#pvTaskToNote'))
    done_btn(); quiet()
    ev(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(x => x.id === '{dt}'); archiveTasks([t]); changed(p, {{ touch: false }}); FullView.render(); }}")
    ev(f"() => FullView.openTask('{gp}', '{dt}')"); pg.wait_for_timeout(300)
    ok('an archived task is to read: no Turn into a note until it is restored', side_has('#pvTaskRestore') and not side_has('#pvTaskToNote'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200); pg.keyboard.press('Escape'); pg.wait_for_timeout(200); quiet()

    # a starred task: the star goes with it, and comes back with Undo
    open_view(gp)
    st = tid_of('Add plant icons')
    ev(f"() => {{ const p = getProject('{gp}'); setStar(p, p.todos.find(t => t.id === '{st}'), true); FullView.render(); }}"); pg.wait_for_timeout(200); quiet()
    ok('the side bar shows the starred task', pg.is_visible('#sbStar'))
    pg.click(f'li.task[data-id="{st}"] .task-title'); pg.wait_for_timeout(300)
    pg.click('#pvTaskToNote'); pg.wait_for_timeout(450)
    ok('turned into a note, the star leaves the city', not pg.is_visible('#sbStar') and ev("() => starredTask()") is None and proj()['star'] == '')
    undo(); pg.wait_for_timeout(450)
    ok('Undo brings the star back, and the pin it gave', pg.is_visible('#sbStar') and proj()['star'] == st and proj()['pin'] == st)
    done_btn(); quiet()

    # an overdue task haunts; turned into a note, its ghost goes
    ev(f"() => {{ const t = getProject('{gp}').todos.find(t => t.id === '{st}'); t.due = '{day(-3)}'; changed(getProject('{gp}')); FullView.render(); }}"); pg.wait_for_timeout(200)
    haunts = lambda: ev(f"() => Ghosts.hauntOf(getProject('{gp}')).some(t => t.id === '{st}')")
    ok('an overdue task haunts its block', haunts())
    pg.click(f'li.task[data-id="{st}"] .task-title'); pg.wait_for_timeout(300)
    pg.click('#pvTaskToNote'); pg.wait_for_timeout(450)
    ok('turned into a note, it haunts no more', not haunts())
    done_btn(); quiet()

    # ---------- a note into a task when every milestone is in the archive: a new To do ----------
    ev(f"""() => {{ const p = getProject('{nc}');
      for (const t of p.todos) {{ t.done = true; t.doneAt = Date.now() - 10 * 86400000; }}
      archiveTasks(p.todos.slice());
      p.notes.push({{ id: 'n_nc', title: 'A night mode for the hall', text: '', at: Date.now() }});
      changed(p, {{ touch: false }}); }}""")
    open_view(nc)
    ms0 = proj(nc)['milestones']
    ok('the project has every milestone in the archive', ev(f"() => liveMilestones(getProject('{nc}')).length") == 0)
    pg.click('.pv-note-card[data-id="n_nc"]'); pg.wait_for_timeout(300)
    ok('its tooltip says a new To do', 'a new To do milestone' in pg.get_attribute('#pvNoteToTask', 'title'))
    pg.click('#pvNoteToTask'); pg.wait_for_timeout(450)
    after = proj(nc)
    todo_ms = [m for m in after['milestones'] if m['name'] == 'To do']
    nt = next((t for t in after['todos'] if t['text'] == 'A night mode for the hall'), None)
    ok('it goes to a new To do, as a task added without @ does', len(todo_ms) == 1 and nt is not None and nt['milestoneId'] == todo_ms[0]['id'] and nt['description'] == '')
    ok('the toast names it', toast() == 'Turned A night mode for the hall into a task in To do.', toast())
    ok('Activity: the new milestone, then the task', lines(nc)[-2:] == ['New milestone: To do', 'Turned into a task: A night mode for the hall'])
    undo(); pg.wait_for_timeout(450)
    ok('Undo takes the new To do away with the task, and both lines', [m['id'] for m in proj(nc)['milestones']] == [m['id'] for m in ms0]
       and not any('A night mode' in x or x == 'New milestone: To do' for x in lines(nc)) and any(n['id'] == 'n_nc' for n in proj(nc)['notes']))
    done_btn(); quiet()

    # ---------- a panel that closes for another closes as always ----------
    open_view(gp)
    pt = tid_of('Publish the app')
    pg.click(f'li.task[data-id="{pt}"] .task-title'); pg.wait_for_timeout(300)
    pg.click('#pvTaskDone'); pg.wait_for_timeout(200)
    pg.click('.pv-note-card[data-id="n_seed"]'); pg.wait_for_timeout(300)
    ok('a note opened over a task\'s panel closes the task as always: its Done line is written', lines().count('Done: Publish the app') == 1 and side_has('#pvNoteTitle'))
    done_btn(); quiet()

    # it all keeps after a reload
    pg.reload(); pg.wait_for_timeout(2200)
    kept = proj()
    ok('after a reload: the turned task is still a note, the turned note still a task', any(n['title'] == 'Try raised beds' for n in kept['notes'])
       and any(t['text'] == 'Compost corner' for t in kept['todos']) and not any(t['text'] == 'Add plant icons' for t in kept['todos']))
    b.close()
print(errors or 'no console errors')
