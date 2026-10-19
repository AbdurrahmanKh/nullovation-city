"""Recurring tasks and the one-line add (Tasks, Round 2, R1 to R4, O1, O2): a repeat ticked moves on to its next date
and waits out of sight until then; a task typed in one line with marks for its date, its repeat and its milestone, in
the project view, the status card, and the city-wide quick add on T."""
import json
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# A fixed Monday noon for the date sums, so they hold on any day the passes run
MON = 'new Date(2026, 9, 19, 12).getTime()'

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
    today = date.fromisoformat(ev("() => ymd()"))
    iso = lambda d: d.isoformat()
    def next_wd(w, frm=None):                    # Python's weekday: Monday 0 ... Sunday 6
        frm = frm or today
        return frm + timedelta(days=(w - frm.weekday()) % 7)

    # ---------- the model: schedules and their dates (R2, R3) ----------
    ok('R2 every schedule reads back whole', ev("""() => [sanitizeRepeat({ every: 'day', n: 1 }), sanitizeRepeat({ every: 'day', n: 3 }), sanitizeRepeat({ every: 'week', days: [4, 1, 1] }),
        sanitizeRepeat({ every: 'month', day: 31 }), sanitizeRepeat({ every: 'year', month: 2, day: 29 })]""") ==
       [{'every': 'day', 'n': 1}, {'every': 'day', 'n': 3}, {'every': 'week', 'days': [1, 4]}, {'every': 'month', 'day': 31}, {'every': 'year', 'month': 2, 'day': 29}])
    ok('a broken repeat is dropped', ev("() => [sanitizeRepeat({ every: 'week', days: [] }), sanitizeRepeat({ every: 'month', day: 32 }), sanitizeRepeat({ every: 'year', month: 2, day: 30 }), sanitizeRepeat('weekly'), sanitizeRepeat(null)]") == [None] * 5)
    ok('each schedule in words', ev("""() => [{ every: 'day', n: 1 }, { every: 'day', n: 3 }, { every: 'week', days: [1, 4, 6] }, { every: 'month', day: 22 }, { every: 'year', month: 10, day: 20 }].map(repeatText)""") ==
       ['Every day', 'Every 3 days', 'Weekly on Sat, Mon, Thu', 'Monthly on the 22nd', 'Yearly on 20 Oct'])
    nxt = lambda rep, due, now: ev(f"() => nextRepeatDue({{ repeat: {json.dumps(rep)}, due: {json.dumps(due)} }}, {now})")
    at = lambda y, m, d: f'new Date({y}, {m - 1}, {d}, 12).getTime()'
    ok('R3 every day counts from the tick', nxt({'every': 'day', 'n': 1}, '2026-10-19', MON) == '2026-10-20' and nxt({'every': 'day', 'n': 1}, '2026-10-12', MON) == '2026-10-20')
    ok('R3 every 7 days counts from the tick, even a late one', nxt({'every': 'day', 'n': 7}, '2026-10-19', MON) == '2026-10-26' and nxt({'every': 'day', 'n': 7}, '2026-10-15', MON) == '2026-10-26')
    wk = {'every': 'week', 'days': [1, 4]}
    ok('R3 weekly on Mon and Thu: ticked on Monday, Thursday next', nxt(wk, '2026-10-19', MON) == '2026-10-22')
    ok('R3 a late weekly tick keeps the rhythm and skips what was missed', nxt(wk, '2026-10-19', at(2026, 10, 23)) == '2026-10-26')
    ok('R3 an early weekly tick moves on from its own date, not today', nxt(wk, '2026-10-22', MON) == '2026-10-26')
    mo = {'every': 'month', 'day': 31}
    ok('R3 monthly on the 31st: November uses its last day, December its 31st',
       nxt(mo, '2026-10-31', at(2026, 10, 31)) == '2026-11-30' and nxt(mo, '2026-11-30', at(2026, 11, 30)) == '2026-12-31')
    ok('R3 a monthly repeat ticked two months late comes back on the next date not past', nxt({'every': 'month', 'day': 20}, '2026-08-20', MON) == '2026-10-20')
    yr = {'every': 'year', 'month': 2, 'day': 29}
    ok('R3 yearly on 29 February: 28 February in other years', nxt(yr, '2028-02-29', at(2028, 2, 29)) == '2029-02-28' and nxt(yr, '2031-02-28', at(2031, 2, 28)) == '2032-02-29')
    ok('a new repeat starts on its first date from today', ev(f"() => [firstRepeatDue({{ every: 'day', n: 3 }}, {MON}), firstRepeatDue({{ every: 'week', days: [5] }}, {MON}), firstRepeatDue({{ every: 'month', day: 1 }}, {MON})]") ==
       ['2026-10-19', '2026-10-23', '2026-11-01'])

    # ---------- ticking a repeat (R1, R4) ----------
    ev(f"() => {{ const p = getProject('{gp}'), t = {task(gp, 'Tune the watering reminders')}; t.repeat = {{ every: 'day', n: 7 }}; t.due = ymd(); setPin(p, t, true); changed(p); }}")
    n0 = ev(f"() => getProject('{gp}').todos.length")
    ev(f"() => tickTask(getProject('{gp}'), {task(gp, 'Tune the watering reminders')})")
    t = get(gp, 'Tune the watering reminders')
    ok(f"R4 one task moves on: the same task, not done, due a week on, waiting ({t['due']})", t['done'] is False and t['due'] == iso(today + timedelta(days=7)) and t['waiting'] is True
       and ev(f"() => getProject('{gp}').todos.length") == n0)
    ok('R4 and only Activity’s Done line records the tick', ev(f"() => getProject('{gp}').activity.slice(-1)[0].text") == 'Done: Tune the watering reminders'
       and ev(f"() => getProject('{gp}').urgency.lastWorked") is not None)
    ok('R1 it goes away: out of the open tasks, the status card, What is next and the hover count',
       ev(f"() => openTasks(getProject('{gp}')).some(t => t.text === 'Tune the watering reminders')") is False
       and 'Tune the watering reminders' not in ev(f"() => bubbleTodos(getProject('{gp}'), 9).list.map(t => t.text)")
       and ev(f"() => nextTask(getProject('{gp}')).text") == 'Draw the beds on a grid'
       and ev(f"() => openTasks(getProject('{gp}')).length") == 4)
    ev("() => persistNow()")
    ok('M5 ticking a pinned repeat clears its pin, as any tick does', ev(f"() => getProject('{gp}').pin") == '')
    ok('Copy task says it was ticked and when it comes back', 'State: ticked; it comes back ' in ev(f"() => taskForClaude(getProject('{gp}'), {task(gp, 'Tune the watering reminders')})")
       and 'Repeats: Every 7 days' in ev(f"() => taskForClaude(getProject('{gp}'), {task(gp, 'Tune the watering reminders')})"))
    st = ev(f"() => projectStatusForClaude(getProject('{gp}'))")
    ok('the project’s status lists it under the repeats waiting', 'Repeats waiting for their next date:\n- Tune the watering reminders (every 7 days, back ' in st)
    ms = ev(f"() => milestoneForClaude(getProject('{gp}'), getProject('{gp}').milestones[0])")
    ok('and the milestone’s copy too, not among its open tasks', '## Repeats waiting for their next date\n- Tune the watering reminders' in ms and '### Tune the watering reminders' not in ms)
    sm = ev(f"() => ClaudeWork.citySummary().projects.find(p => p.name === 'Garden planner').milestones.find(m => m.name === 'First release')")
    ok(f"the city summary for Claude lists it as waiting, with the day it comes back ({sm.get('waiting')})", sm.get('waiting') == [{'task': 'Tune the watering reminders', 'repeat': 'Every 7 days', 'back': iso(today + timedelta(days=7))}]
       and all(o['task'] != 'Tune the watering reminders' for o in sm['open']))
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'finish', days: 1, lastWorked: Date.now() - 3 * 86400000, pickedAt: Date.now() - 4 * 86400000 }}; p.todos.forEach(t => {{ if (!t.repeat) {{ t.done = true; t.doneAt = Date.now() - 3 * 86400000; }} }}); changed(p); }}")
    ok('with only a waiting repeat left, Work until finished asks nothing', ev(f"() => urgencyOf(getProject('{gp}')).color") is None)
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(500)
    ok('and the status card says when it comes back', (pg.text_content('#bubble .b-empty') or '').startswith('Nothing open now. Tune the watering reminders comes back '))
    ev("() => MapView.deselect()")
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'none', days: 1, lastWorked: null, pickedAt: null }}; p.todos.forEach(t => {{ if (!t.repeat) {{ t.done = false; t.doneAt = null; }} }}); changed(p); }}")

    # when its day comes it is back, due that day; a missed one stays one overdue task
    ev(f"() => {{ const t = {task(gp, 'Tune the watering reminders')}; t.due = ymd(); changed(getProject('{gp}')); }}")
    ok('R1 on its day it is back, due that day', ev(f"() => openTasks(getProject('{gp}')).some(t => t.text === 'Tune the watering reminders')") and ev(f"() => dueInfo({task(gp, 'Tune the watering reminders')}).text") == 'Due today')
    ev("() => persistNow()")
    ok('back, it stops waiting for good, so a later date does not hide it again', 'waiting' not in get(gp, 'Tune the watering reminders'))
    late = iso(today - timedelta(days=3))
    ev(f"() => {{ const t = {task(gp, 'Tune the watering reminders')}; t.due = '{late}'; changed(getProject('{gp}')); }}")
    ok('a repeat not ticked by its date is one overdue task, with its garbage', ev(f"() => dueInfo({task(gp, 'Tune the watering reminders')}).text") == '3 days overdue'
       and any(x['t']['text'] == 'Tune the watering reminders' for x in ev(f"() => Garbage.breakdown(getProject('{gp}')).late")))
    was = ev(f"() => {{ window.__was = tickTask(getProject('{gp}'), {task(gp, 'Tune the watering reminders')}); return window.__was; }}")
    ok('ticked late, every 7 days counts from the tick', get(gp, 'Tune the watering reminders')['due'] == iso(today + timedelta(days=7)) and not ev(f"() => Garbage.breakdown(getProject('{gp}')).late.length"))
    ev(f"() => untickTask(getProject('{gp}'), {task(gp, 'Tune the watering reminders')}, window.__was)")
    t = get(gp, 'Tune the watering reminders')
    ok('unticking puts back its date, open and late', t['due'] == late and 'waiting' not in t and ev(f"() => getProject('{gp}').activity.slice(-1)[0].text") == 'Reopened: Tune the watering reminders')

    # reading saved data
    read = ev(f"""() => {{ const r = JSON.parse(JSON.stringify(DB.projects)), a = r.find(p => p.id === '{gp}');
        a.todos[0].repeat = {{ every: 'week', days: [2] }}; a.todos[0].waiting = true; a.todos[0].due = ymd(Date.now() + 2 * 864e5);
        a.todos[1].repeat = {{ every: 'month', day: 40 }};
        a.todos[2].repeat = {{ every: 'day', n: 2 }}; a.todos[2].waiting = true; a.todos[2].due = ymd(Date.now() - 864e5);
        const q = sanitizeProjects(r).map(x => x.p).find(p => p.id === '{gp}');
        return [q.todos[0].repeat, !!q.todos[0].waiting, q.todos[1].repeat || null, q.todos[2].repeat, !!q.todos[2].waiting]; }}""")
    ok(f'reading a city keeps a whole repeat and its wait, drops a broken one, and a wait whose day has passed {read}',
       read == [{'every': 'week', 'days': [2]}, True, None, {'every': 'day', 'n': 2}, False])
    bk = ev(f"async () => {{ const b = await buildBackup(); return b.projects.find(p => p.id === '{gp}').todos.find(t => t.text === 'Tune the watering reminders').repeat; }}")
    ok('a backup and the data file carry the repeat', bk == {'every': 'day', 'n': 7})
    plan = ev(f"""() => {{ const x = readPlan({{ app: 'nullovation-city', kind: 'project', project: JSON.parse(JSON.stringify(getProject('{gp}'))) }});
        return x.milestones[0].tasks.find(t => t.text === 'Tune the watering reminders').repeat; }}""")
    ok('a project export loaded back as a plan keeps its repeats', plan == {'every': 'day', 'n': 7})

    # ---------- reading a typed line (O1) ----------
    dm = lambda a, b='': ev(f"() => {{ const d = readDateMark({json.dumps(a)}, {json.dumps(b)}, {MON}); return d && [ymd(d.at), d.used]; }}")
    ok('!today, !tomorrow', dm('today') == ['2026-10-19', 1] and dm('tomorrow') == ['2026-10-20', 1])
    ok('!fri is the next Friday; !mon on a Monday is today, not past', dm('fri') == ['2026-10-23', 1] and dm('Friday') == ['2026-10-23', 1] and dm('mon') == ['2026-10-19', 1] and dm('sun') == ['2026-10-25', 1])
    ok('!20 is the next 20th; !18 is next month’s', dm('20') == ['2026-10-20', 1] and dm('19') == ['2026-10-19', 1] and dm('18') == ['2026-11-18', 1])
    ok('!31 skips a month without one', ev(f"() => ymd(readDateMark('31', '', {at(2026, 11, 5)}).at)") == '2026-12-31')
    ok('!oct 20 and !20 oct, this year or the next not past', dm('oct', '20') == ['2026-10-20', 2] and dm('20', 'oct') == ['2026-10-20', 2] and dm('oct', '18') == ['2027-10-18', 2] and dm('feb', '29') == ['2028-02-29', 2])
    ok('!2026-12-01, and not an impossible date', dm('2026-12-01') == ['2026-12-01', 1] and dm('2026-02-30') is None and dm('soon') is None and dm('32') is None)
    mk = lambda text, cw=False: ev(f"() => {{ const r = readTaskMarks({json.dumps(text)}, {{ now: {MON}, cityWide: {json.dumps(cw)} }}); return [r.title, r.due, r.repeat, r.ms, r.project]; }}")
    ok('O1 "Water the beds !fri #weekly @launch"', mk('Water the beds !fri #weekly @launch') == ['Water the beds', '2026-10-23', {'every': 'week', 'days': [5]}, 'launch', None])
    ok('#weekly with several weekdays repeats on each, from the soonest', mk('Gym !thu !mon #weekly') == ['Gym', '2026-10-19', {'every': 'week', 'days': [1, 4]}, None, None])
    ok('#weekly with no date: today’s weekday, from today', mk('Bins out #weekly') == ['Bins out', '2026-10-19', {'every': 'week', 'days': [1]}, None, None])
    ok('#every 3 days and #every day start today', mk('Check soil #every 3 days') == ['Check soil', '2026-10-19', {'every': 'day', 'n': 3}, None, None]
       and mk('Stretch #every day')[2] == {'every': 'day', 'n': 1} and mk('Stretch #daily')[2] == {'every': 'day', 'n': 1})
    ok('#monthly !1 and #yearly !mar 1 take the date’s day', mk('Pay rent #monthly !1') == ['Pay rent', '2026-11-01', {'every': 'month', 'day': 1}, None, None]
       and mk('Renew the car #yearly !mar 1') == ['Renew the car', '2027-03-01', {'every': 'year', 'month': 3, 'day': 1}, None, None])
    ok('words that are not marks stay in the title', mk('#1 priority: mail bob@mail.com and/or ! @ !soon #every 400 days') == ['#1 priority: mail bob@mail.com and/or ! @ !soon #every 400 days', '', None, None, None])
    ok('/name is a mark only in the quick add', mk('/garden Water it')[0] == '/garden Water it' and mk('/garden Water it', True) == ['Water it', '', None, None, 'garden'])
    ok('the title can be Arabic', mk('اسقِ النباتات !fri #weekly') == ['اسقِ النباتات', '2026-10-23', {'every': 'week', 'days': [5]}, None, None])
    rl = lambda text, extra: ev(f"() => {{ const r = readTaskLine({json.dumps(text)}, {extra}); return {{ ok: r.ok, p: r.p && r.p.name, ms: r.msId && r.p.milestones.find(m => m.id === r.msId).name, msNew: r.msNew, problem: r.problem, parts: r.parts }}; }}")
    r = rl('Ship it @lau', f"{{ project: getProject('{gp}') }}")
    ok(f"@lau is the milestone whose name starts with it ({r['ms']})", r['ok'] and r['ms'] == 'Launch' and 'In Launch' in r['parts'])
    r = rl('Ship it @planner-notes', f"{{ project: getProject('{gp}') }}")
    ok('an @name no milestone has makes a new one, and says so', r['ok'] and r['msNew'] == 'planner-notes' and 'New milestone planner-notes' in r['parts'])
    r = rl('Ship it', f"{{ project: getProject('{gp}') }}")
    ok('without @ it goes to the current milestone', r['ms'] == 'First release' and r['parts'] == [])
    r = rl('/gard Water it !fri', "{ cityWide: true }")
    ok(f"the quick add names the project with /gard ({r['parts']})", r['ok'] and r['p'] == 'Garden planner' and r['parts'][:2] == ['Garden planner', 'In First release'] and r['parts'][2].startswith('Due '))
    ok('a /name no project has says so', rl('/nope Water it', "{ cityWide: true }")['problem'] == '/nope fits no project')
    ok('with no project named or open, it asks for one', rl('Water it', "{ cityWide: true }")['problem'] == 'Name the project with /name')
    ok('marks alone ask for the task too', rl('!fri #weekly', f"{{ project: getProject('{gp}') }}")['problem'] == 'Type the task too')

    # ---------- the status card's add field (O2) ----------
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    ok('O2 the status card has an add field', pg.is_visible('#bubble #bAdd') and pg.get_attribute('#bAdd', 'placeholder') == 'Add a task')
    pg.click('#bAdd'); pg.wait_for_timeout(100)
    ok('focused and empty, the line under it names the marks', pg.text_content('#bAddHint') == '!fri date · #weekly repeat · @name milestone')
    pg.keyboard.type('Water the beds !fri #weekly @launch'); pg.wait_for_timeout(150)
    fri = next_wd(4)
    hint = pg.text_content('#bAddHint')
    ok(f'as you type it says what it understood ({hint})', hint.startswith('In Launch · Due ') and hint.endswith('Repeats weekly on Fri'))
    pg.screenshot(path=str(SHOTS / '280-card-add.png'), clip=pg.query_selector('#bubble').bounding_box())
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    t = get(gp, 'Water the beds')
    ok(f"Enter adds it, in Launch, due Friday, weekly on Friday ({t and t['due']})", t and t['due'] == iso(fri) and t['repeat'] == {'every': 'week', 'days': [5]}
       and ev(f"() => getProject('{gp}').milestones.find(m => m.id === {json.dumps(t['milestoneId'])}).name") == 'Launch')
    ok('the field stays, empty and focused, for the next one', ev("() => document.activeElement.id") == 'bAdd' and pg.input_value('#bAdd') == '')
    pg.keyboard.type('Mulch the paths'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    t = get(gp, 'Mulch the paths')
    ok('a plain line goes to the current milestone, with no date', t and t['due'] == '' and 'repeat' not in t and ev(f"() => getProject('{gp}').milestones.find(m => m.id === {json.dumps(t['milestoneId'])}).name") == 'First release')
    pg.keyboard.type('!fri'); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    ok('marks alone add nothing, and say why', pg.text_content('#bAddHint').startswith('Type the task too') and 'bad' in pg.get_attribute('#bAddHint', 'class'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc clears the field first', pg.input_value('#bAdd') == '' and pg.is_visible('#bubble'))
    ev("() => Bubble.refresh()")
    ok('what is typed survives the card redrawing', ev("() => document.activeElement.id") == 'bAdd')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('then Esc closes the card', not pg.is_visible('#bubble'))

    # ticking a repeat in the status card
    ev(f"() => {{ const t = {task(gp, 'Water the beds')}; t.due = ymd(); changed(getProject('{gp}')); MapView.select('{gp}'); }}"); pg.wait_for_timeout(600)
    wid = ev(f"() => {task(gp, 'Water the beds')}.id")
    ok('a repeat in the card wears the repeat sign', pg.locator(f'#bubble li[data-id="{wid}"] .repeat-mark').count() == 1)
    pg.click(f'#bubble li[data-id="{wid}"] .cb'); pg.wait_for_timeout(200)
    ok('ticked in the card, it is struck through a moment, then slides away', pg.locator(f'#bubble li.ticked[data-id="{wid}"]').count() == 1)
    pg.wait_for_timeout(1000)
    t = get(gp, 'Water the beds')
    ok(f"and has moved on to next Friday, waiting ({t['due']})", pg.locator(f'#bubble li[data-id="{wid}"]').count() == 0 and t['due'] == iso(next_wd(4, today + timedelta(days=1))) and t['waiting'] is True)
    toast = pg.text_content('#toast')
    ok(f'a toast says when it comes back, with Undo ({toast})', toast.startswith('Water the beds comes back ') and 'Undo' in toast)
    pg.click('#toast .toast-act'); pg.wait_for_timeout(300)
    t = get(gp, 'Water the beds')
    ok('Undo brings it back as it was', t['due'] == iso(today) and 'waiting' not in t and pg.locator(f'#bubble li[data-id="{wid}"]').count() == 1)
    ev("() => MapView.deselect()")

    # ---------- the project view (R1, O2) ----------
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(700)
    ms_launch = ev(f"() => getProject('{gp}').milestones.find(m => m.name === 'Launch').id")
    ms_first = ev(f"() => getProject('{gp}').milestones.find(m => m.name === 'First release').id")
    pg.click(f'.ms[data-msid="{ms_first}"] .ms-plus'); pg.wait_for_timeout(200)
    ok('the add field shows the marks under it', pg.text_content('#pvAddHint') == '!fri date · #weekly repeat · @name milestone')
    pg.keyboard.type('Check the soil #every 3 days'); pg.wait_for_timeout(100)
    ok(f"and what it understood ({pg.text_content('#pvAddHint')})", pg.text_content('#pvAddHint') == 'Due today · Repeats every 3 days')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    t = get(gp, 'Check the soil')
    ok('Enter adds it to that milestone, due today, every 3 days', t and t['milestoneId'] == ms_first and t['due'] == iso(today) and t['repeat'] == {'every': 'day', 'n': 3})
    pg.click(f'.ms[data-msid="{ms_first}"] .ms-plus'); pg.wait_for_timeout(200)
    pg.keyboard.type('Write the launch post @launch !tomorrow'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    t = get(gp, 'Write the launch post')
    ok('@launch in another milestone’s field sends it there', t and t['milestoneId'] == ms_launch and t['due'] == iso(today + timedelta(days=1)))
    ok('and the focus goes to that milestone’s +', ev("() => document.activeElement.closest('.ms').dataset.msid") == ms_launch)
    cid = ev(f"() => {task(gp, 'Check the soil')}.id")
    row = f'li.task[data-id="{cid}"]'
    ok('a repeat’s row wears the repeat sign beside its date', pg.locator(f'{row} .repeat-mark').count() == 1 and pg.text_content(f'{row} .due').strip() == 'Due today')
    pg.click(f'{row} .cb'); pg.wait_for_timeout(400)
    back = today + timedelta(days=3)
    ok(f'R1 ticked, the row stays in its place, dimmed, with when it comes back ({pg.text_content(row + " .due")})', pg.locator(f'{row}.waiting').count() == 1 and pg.locator(f'{row} .cb').count() == 0
       and pg.locator(f'{row} .task-wait').count() == 1 and pg.text_content(f'{row} .due.back').strip().startswith('Back ') and get(gp, 'Check the soil')['due'] == iso(back))
    ok('the focus stays on the row', ev("() => document.activeElement.closest('li.task') && document.activeElement.closest('li.task').dataset.id") == cid)
    pg.evaluate(f"() => document.querySelector('{row}').scrollIntoView({{ block: 'center' }})"); pg.wait_for_timeout(150)
    pg.screenshot(path=str(SHOTS / '281-pv-waiting.png'), clip=pg.query_selector(f'.ms[data-msid="{ms_first}"]').bounding_box())
    ok('a waiting row has no pin', pg.locator(f'{row} .task-mark').count() == 0)
    ok('Due this week leaves it out while it waits', 'Check the soil' not in (pg.text_content('#dueList') or ''))

    # the task panel: a waiting repeat, then the repeat picker
    pg.click(f'{row} .task-title'); pg.wait_for_timeout(400)
    ok(f"its panel says it was ticked and when it is back ({pg.text_content('#pvSide .pv-task-back')})", pg.text_content('#pvSide .pv-task-back').startswith('Ticked. Back ') and pg.locator('#pvTaskDone').count() == 0)
    ok('and shows its repeat', pg.input_value('#pvRepeat') == 'days' and pg.input_value('#pvRepeatN') == '3')
    pg.screenshot(path=str(SHOTS / '282-panel-waiting.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.fill('#pvTaskDue', iso(today)); pg.dispatch_event('#pvTaskDue', 'change'); pg.wait_for_timeout(250)
    ok('a nearer due date brings it back sooner', ev(f"() => isOpenTask({task(gp, 'Check the soil')})") and pg.locator('#pvTaskDone').count() == 1)
    pg.focus('#pvTaskDesc'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc undoes that, so it waits again', get(gp, 'Check the soil')['due'] == iso(back) and get(gp, 'Check the soil')['waiting'] is True)

    pg.click('li.task:has-text("Add plant icons") .task-title'); pg.wait_for_timeout(400)
    ok('a plain task’s panel has Repeat: No repeat', pg.input_value('#pvRepeat') == 'none')
    pg.select_option('#pvRepeat', 'week'); pg.wait_for_timeout(250)
    t = get(gp, 'Add plant icons')
    ok(f"Weekly takes today’s weekday and, with no date, gives it today ({t['repeat']}, {t['due']})", t['repeat'] == {'every': 'week', 'days': [ev("() => new Date().getDay()")]} and t['due'] == iso(today)
       and ev("() => document.activeElement.id") == 'pvRepeat')
    sat = '#pvSide .pv-repeat-days [data-day="6"]'
    pg.click(sat); pg.wait_for_timeout(250)
    ok('a weekday button adds that day', 6 in get(gp, 'Add plant icons')['repeat']['days'] and pg.get_attribute(sat, 'aria-pressed') == 'true')
    pg.screenshot(path=str(SHOTS / '283-panel-weekly.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.click(sat); pg.wait_for_timeout(250)
    one = get(gp, 'Add plant icons')['repeat']['days']
    pg.click(f'#pvSide .pv-repeat-days [data-day="{one[0]}"]'); pg.wait_for_timeout(250)
    ok('the last weekday stays: a weekly repeat needs one', get(gp, 'Add plant icons')['repeat']['days'] == one)
    pg.select_option('#pvRepeat', 'month'); pg.wait_for_timeout(250)
    pg.select_option('#pvRepeatDay', '31'); pg.wait_for_timeout(250)
    ok('Monthly on the 31st, with a note on shorter months', get(gp, 'Add plant icons')['repeat'] == {'every': 'month', 'day': 31} and 'use their last day' in pg.text_content('#pvSide .pv-repeat-note'))
    pg.select_option('#pvRepeat', 'year'); pg.wait_for_timeout(250)
    pg.select_option('#pvRepeatMonth', '2'); pg.wait_for_timeout(250)
    ok('Yearly: a month without the day takes its last', get(gp, 'Add plant icons')['repeat']['month'] == 2 and get(gp, 'Add plant icons')['repeat']['day'] <= 29)
    pg.select_option('#pvRepeat', 'days'); pg.wait_for_timeout(250)
    pg.fill('#pvRepeatN', '10'); pg.dispatch_event('#pvRepeatN', 'change'); pg.wait_for_timeout(250)
    ok('Every N days', get(gp, 'Add plant icons')['repeat'] == {'every': 'day', 'n': 10})
    pg.focus('#pvTaskDesc'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    t = get(gp, 'Add plant icons')
    ok('Esc undoes the repeat and the date it brought', 'repeat' not in t and t['due'] == '')
    pg.click('li.task:has-text("Add plant icons") .task-title'); pg.wait_for_timeout(400)
    pg.select_option('#pvRepeat', 'daily'); pg.wait_for_timeout(250)
    pg.click('#pvTaskDone'); pg.wait_for_timeout(250)
    ok('ticked in the panel, it moves on and the panel says so', pg.text_content('#pvSide .pv-task-back').startswith('Ticked. Back tomorrow') and get(gp, 'Add plant icons')['due'] == iso(today + timedelta(days=1)))
    n_done = lambda: ev(f"() => getProject('{gp}').activity.filter(e => e.text === 'Done: Add plant icons').length")
    d0 = n_done()
    pg.click('#pvSide .pv-top .btn-accent, #pvSide .pv-top button[aria-label^="Close"]'); pg.wait_for_timeout(300)
    ok('closing the panel writes its Done line once, and the repeat as an edit', n_done() == d0 + 1 and ev(f"() => getProject('{gp}').activity.slice(-2).map(e => e.text)") == ['Done: Add plant icons', 'Edited task: Add plant icons'])
    pg.click('li.task:has-text("Add plant icons") .task-title'); pg.wait_for_timeout(400)
    pg.select_option('#pvRepeat', 'none'); pg.wait_for_timeout(250)
    t = get(gp, 'Add plant icons')
    ok('No repeat stops it, and it is back now, with its date', 'repeat' not in t and 'waiting' not in t and ev(f"() => isOpenTask({task(gp, 'Add plant icons')})"))
    ev("() => FullView.close()"); pg.wait_for_timeout(300)

    # nothing open but a waiting repeat
    ev(f"""() => {{ const p = getProject('{nc}'); p.todos.forEach(t => {{ t.done = true; t.doneAt = Date.now(); }});
        p.todos.push(Object.assign(todo('Back up the city', p.milestones[0].id), {{ repeat: {{ every: 'day', n: 7 }}, due: ymd(Date.now() + 2 * 864e5), waiting: true }})); changed(p); }}""")
    ev(f"() => FullView.open('{nc}')"); pg.wait_for_timeout(500)
    ok(f"What is next says what comes back, when nothing is open ({pg.text_content('.pv-next .fv-empty')})", pg.text_content('.pv-next .fv-empty').startswith('Nothing open now. Back up the city comes back '))
    ev("() => FullView.close()")

    # ---------- the city-wide quick add (O2) ----------
    ev("() => MapView.deselect()"); pg.wait_for_timeout(200)
    pg.mouse.move(700, 450)
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    ok('O2 T opens the quick add over the map, focused', pg.is_visible('#quickAdd') and ev("() => document.activeElement.id") == 'quickAddIn')
    ok('its line names /project with the marks', pg.text_content('#quickAddHint') == '/name project · !fri date · #weekly repeat · @name milestone')
    pg.keyboard.type('Weed the beds !tomorrow')
    ok('with no project named or selected, it asks for one, and Enter waits', pg.text_content('#quickAddHint').startswith('Name the project with /name'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    ok('(nothing added)', get(gp, 'Weed the beds') is None and pg.is_visible('#quickAdd'))
    pg.keyboard.press('Home'); pg.keyboard.type('/garden '); pg.wait_for_timeout(100)
    ok(f"/garden names Garden planner ({pg.text_content('#quickAddHint')})", pg.text_content('#quickAddHint').startswith('Garden planner · In First release · Due tomorrow'))
    pg.screenshot(path=str(SHOTS / '284-quick-add.png'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    t = get(gp, 'Weed the beds')
    ok('Enter adds it there and closes', t and t['due'] == iso(today + timedelta(days=1)) and not pg.is_visible('#quickAdd'))
    ok(f"a toast says where it went, with Open ({pg.text_content('#toast')})", pg.text_content('#toast').startswith('Added to Garden planner: Weed the beds.') and 'Open' in pg.text_content('#toast'))
    pg.click('#toast .toast-act'); pg.wait_for_timeout(500)
    ok('Open opens the task in its project', ev("() => FullView.currentId()") == gp and pg.input_value('#pvTaskTitle') == 'Weed the beds')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.keyboard.type('Rake the leaves #monthly !5')
    ok(f"with the project view open, the task goes to its project ({pg.text_content('#quickAddHint')})", pg.text_content('#quickAddHint').startswith('Garden planner · In First release'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    t = get(gp, 'Rake the leaves')
    ok('and the view shows it at once', t and t['repeat'] == {'every': 'month', 'day': 5} and pg.locator('li.task:has-text("Rake the leaves")').count() == 1)
    ev("() => FullView.close()"); pg.wait_for_timeout(200)
    ev(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(500)
    pg.click('#bAdd'); pg.keyboard.type('t'); pg.wait_for_timeout(150)
    ok('T in a field types a t, and opens nothing', not pg.is_visible('#quickAdd') and pg.input_value('#bAdd') == 't')
    pg.keyboard.press('Escape'); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ev(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(300)
    pg.mouse.move(700, 450); ev("() => document.activeElement.blur()")
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.keyboard.type('Plan the next round')
    ok('with a building selected, the task goes to it', pg.text_content('#quickAddHint').startswith('Nullovation City'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it, adding nothing', not pg.is_visible('#quickAdd') and get(nc, 'Plan the next round') is None and pg.is_visible('#bubble'))
    pg.keyboard.press('t'); pg.wait_for_timeout(200)
    pg.mouse.click(1300, 700); pg.wait_for_timeout(300)
    ok('a click elsewhere closes it', not pg.is_visible('#quickAdd'))
    ev("() => Settings.open('city')"); pg.click('#setHelpBtn'); pg.wait_for_timeout(100)
    ok('the controls guide names T', 'T, anywhere; /project names the building' in pg.text_content('#setHelp'))
    b.close()
print(errors or 'no console errors')
