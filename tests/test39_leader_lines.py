"""The leaders' lines (0.1.58): one shared set for every leader, approved word for word in Leader UX, Round 4, and the
first of them in the city: the greeting with the next task on the leader card in the project view."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

# word for word, as approved (Leader UX, Round 4: L1 to L3)
LINES = {
    'behind': 'We slipped behind our pace. {task} puts us back on track.',
    'behind_more': "We're falling further behind. {task} pulls us back.",
    'behind_day': 'Nothing finished here for a day. {task} gets us moving.',
    'due': '{task} is due today.',
    'due_many': '{n} tasks are due today. First up: {task}.',
    'one_left': '{milestone} is one task from done: {task}. Finish it and we throw a street party.',
    'added': 'Claude added {what}.',
    'round': 'Claude attached a wizard round to {task}: {round}.',
    'waiting': 'Claude is waiting for you on {task}.',
    'asks': 'Claude wants your OK first: {change}.',
    'failed': 'Claude stopped on an error while working on {task}.',
    'finished': 'Claude finished {task}.',
    'answers': 'Your answers are in for {round}: {n} of {total}.',
    'week': 'Last week we finished {n} tasks. Next up: {task}.',
    'week_quiet': 'Quiet week: nothing finished. {task} is a good start.',
    'working': 'Claude is working on {task}. Started {ago}.',
    'greet': 'Welcome back. Next up: {task}.',
    'greet_empty': 'Nothing open here yet. Add the next task.',
}
LONG = 'Draw every raised bed on the grid with its soil, its sun and the plants it holds this year'

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    say = lambda moment, v=None: ev("([m, v]) => leaderSay(m, v || {})", [moment, v])
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    tid_of = lambda text, pid=gp: ev(f"() => (getProject('{pid}').todos.find(t => t.text === {json.dumps(text)}) || {{}}).id || null")
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; document.querySelectorAll('#gusSay, #pxSay').forEach(e => e.hidden = true); }")
    card = lambda: ev("""() => { const c = document.querySelector('#pvLeader'); if (!c) return null; const s = c.querySelector('.ld-says');
        return s ? { text: s.textContent, title: s.getAttribute('title'), bar: getComputedStyle(s).boxShadow, dir: s.getAttribute('dir'),
          under: !!c.querySelector('.ld-card-text span:not(.ld-says)') && (c.querySelector('.ld-card-text span:not(.ld-says)').compareDocumentPosition(s) & Node.DOCUMENT_POSITION_FOLLOWING) > 0 } : { text: null }; }""")

    # ---------- the lines, word for word ----------
    got = ev("() => LEADER_LINES")
    ok(f'every line is in the city, word for word, one per moment ({len(got)} moments)', got == LINES, {k: v for k, v in got.items() if LINES.get(k) != v})
    ok('no line names its building: each speaks for it as "we"', all('{project}' not in v and '{building}' not in v for v in got.values()))

    # ---------- filling the blanks ----------
    ok('a task fills its blank', say('behind', {'task': 'Draw the beds'}) == 'We slipped behind our pace. Draw the beds puts us back on track.')
    ok('a count of one reads in the singular', say('week', {'n': 1, 'task': 'Save a plan'}) == 'Last week we finished 1 task. Next up: Save a plan.')
    ok('and several in the plural', say('week', {'n': 5, 'task': 'Save a plan'}) == 'Last week we finished 5 tasks. Next up: Save a plan.'
       and say('due_many', {'n': 3, 'task': 'Add icons'}) == '3 tasks are due today. First up: Add icons.')
    ok('a line a task starts begins with a capital', say('due', {'task': 'water the beds'}) == 'Water the beds is due today.')
    cut = say('finished', {'task': LONG})
    ok(f'a title past 60 characters is cut short with an ellipsis ({len(cut)} characters)', cut == 'Claude finished ' + LONG[:59].rstrip() + '….')
    ok('every other blank fills as given', say('answers', {'round': 'Leader UX, Round 1', 'n': 7, 'total': 8}) == 'Your answers are in for Leader UX, Round 1: 7 of 8.'
       and say('added', {'what': '2 tasks, a note and 1 link'}) == 'Claude added 2 tasks, a note and 1 link.'
       and say('working', {'task': 'Fix the map', 'ago': '12 minutes ago'}) == 'Claude is working on Fix the map. Started 12 minutes ago.'
       and say('one_left', {'milestone': 'First release', 'task': 'Publish'}) == 'First release is one task from done: Publish. Finish it and we throw a street party.')
    ok('a blank with nothing for it stays as it is; a moment the city does not have says nothing', say('added') == 'Claude added {what}.' and say('nope') == '')

    # ---------- the greeting ----------
    ok('the greeting names the next task: the current milestone\'s first open one', ev(f"() => leaderGreeting(getProject('{gp}'))") == 'Welcome back. Next up: Draw the beds on a grid.')
    ev(f"() => {{ const p = getProject('{gp}'); setPin(p, p.todos.find(t => t.text === 'Publish the app'), true); }}")
    ok('a pinned task comes first, from any milestone', ev(f"() => leaderGreeting(getProject('{gp}'))") == 'Welcome back. Next up: Publish the app.')
    ev(f"() => {{ const p = getProject('{gp}'); setPin(p, p.todos.find(t => t.text === 'Publish the app'), false); }}")
    ok('with nothing open, it says so', ev("() => leaderGreeting({ todos: [{ id: 'a', text: 'Done', done: true, milestoneId: 'm' }], milestones: [{ id: 'm', name: 'M' }], pin: '' })")
       == 'Nothing open here yet. Add the next task.')

    # ---------- in the city: the leader card ----------
    ev(f"""() => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Nullovations', color: '#8FD0F7' }}); DB.leaders.push(l);
        setLeader(getProject('{gp}'), l.id); persistNow(); Leaders.refreshAll(); }}""")
    before = ev(f"() => {{ const p = getProject('{gp}'); return [p.updatedAt, p.activity.length]; }}")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600); quiet()
    c = card()
    ok(f'the leader card says its greeting with the next task, under the name and role ({c})', c and c['text'] == 'Welcome back. Next up: Draw the beds on a grid.' and c['under'] and c['dir'] == 'auto')
    ok(f'in a quote with a bar in the leader\'s color ({c and c["bar"]})', c and 'rgb(143, 208, 247)' in c['bar'])
    ok('a greeting is not work: Updated stays, and nothing goes in Activity', ev(f"() => {{ const p = getProject('{gp}'); return [p.updatedAt, p.activity.length]; }}") == before)
    pg.screenshot(path=str(SHOTS / '390-leader-greeting.png'), clip=pg.query_selector('.pv-hero').bounding_box())

    first = tid_of('Draw the beds on a grid')
    pg.click(f'li.task[data-id="{first}"] .cb'); pg.wait_for_timeout(500)
    ok(f'ticking the next task moves the greeting on to the one after it ({card()["text"]})', card()['text'] == 'Welcome back. Next up: Save a plan as a file.')
    pid = tid_of('Add plant icons')
    pg.hover(f'li.task[data-id="{pid}"]'); pg.click(f'li.task[data-id="{pid}"] .task-mark'); pg.wait_for_timeout(400)
    ok(f'pinning a task names it in the greeting ({card()["text"]})', card()['text'] == 'Welcome back. Next up: Add plant icons.')
    ev(f"""() => {{ const p = getProject('{gp}'), t = p.todos.find(x => x.text === 'Add plant icons'); t.text = {json.dumps(LONG)}; changed(p); }}""")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    c = card()
    ok(f'a long title is cut short in the line, the full title its tooltip ({c["text"]})', c['text'] == 'Welcome back. Next up: ' + LONG[:59].rstrip() + '….' and c['title'] == LONG)
    ev(f"() => {{ const p = getProject('{gp}'); for (const t of p.todos) {{ t.done = true; t.doneAt = Date.now(); }} p.pin = ''; changed(p); }}")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    ok(f'with every task done, it says nothing is open ({card()["text"]})', card()['text'] == 'Nothing open here yet. Add the next task.')

    # ---------- only on the leader card ----------
    ev(f"() => FullView.open('{nc}')"); pg.wait_for_timeout(500)
    ok('a building with no leader has no line: its card still asks for a leader', ev("() => !!document.querySelector('#pvLeader.empty') && !document.querySelector('#pvLeader .ld-says')"))
    ev("() => FullView.close()"); pg.wait_for_timeout(300)
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(600)
    sc = ev("() => { const l = document.querySelector('#bubble .b-leader'); return l ? [l.querySelector('.ld-name').textContent, l.querySelector('.b-leader-text span').textContent, !!l.querySelector('.ld-says')] : null; }")
    ok(f'the status card keeps its name and role, with no greeting: news comes there later ({sc})', sc == ['Talal', 'Head of Nullovations', False])

    pg.reload(); pg.wait_for_timeout(2200)
    ok('nothing new is saved: the lines live in the tool, not the city', ev("() => Object.keys(DB.leaders[0]).sort().join(',')") == 'color,createdAt,id,name,portrait,role')
    b.close()
print(errors or 'no console errors')
