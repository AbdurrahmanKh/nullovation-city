"""Archiving (Tasks, Round 2, A1 to A3, and Archiving, Round 1): done tasks move into their project's archive by hand,
or by themselves 7 days after their tick; an Archive view in the more menu, by milestone, with Restore; the counts,
search and Reports still see archived work, while the lists, a milestone's copy and the city summary leave it out."""
import json, re
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# A fixed Monday noon for the model's sums: 19 October 2026
MON = 'new Date(2026, 9, 19, 12).getTime()'
at = lambda y, m, d, hr=12: f'new Date({y}, {m - 1}, {d}, {hr}).getTime()'
DAY = 86400000

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    P = f"getProject('{gp}')"
    task = lambda text: f"{P}.todos.find(t => t.text === {json.dumps(text)})"
    get = lambda text: ev(f"() => JSON.parse(JSON.stringify({task(text)} || null))")
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; }")
    toasted = lambda: ev("() => document.querySelector('#toast').classList.contains('show') ? document.querySelector('#toast').textContent : ''")
    undo = lambda: ev("() => { const b = document.querySelector('#toast .toast-act'); if (b) b.click(); return !!b; }")

    # ---------- the model ----------
    ok('A2a a done task archives itself 7 days after the day of its tick',
       ev(f"() => ymd(archiveDay({{ done: true, doneAt: {at(2026, 10, 12, 23)} }}))") == '2026-10-19')
    ok('C1 after a restore, 7 days after the later of the tick and the restore',
       ev(f"() => ymd(archiveDay({{ done: true, doneAt: {at(2026, 10, 12)}, archiveFrom: '2026-10-15' }}))") == '2026-10-22' and
       ev(f"() => ymd(archiveDay({{ done: true, doneAt: {at(2026, 10, 16)}, archiveFrom: '2026-10-15' }}))") == '2026-10-23')
    SET = f"""(() => {{
      const keep = DB.projects;
      const A = blankProject({{ name: 'Alpha', milestones: [{{ id: 'mA', name: 'One' }}, {{ id: 'mB', name: 'Two' }}, {{ id: 'mC', name: 'Empty' }}], todos: [
        {{ id: 'a1', text: 'Week ago', done: true, doneAt: {at(2026, 10, 12, 20)}, milestoneId: 'mA' }},
        {{ id: 'a2', text: 'Six days ago', done: true, doneAt: {at(2026, 10, 13, 8)}, milestoneId: 'mA' }},
        {{ id: 'a3', text: 'Open one', done: false, milestoneId: 'mA' }},
        {{ id: 'a4', text: 'No tick on record', done: true, doneAt: null, milestoneId: 'mA' }},
        {{ id: 'a5', text: 'Waiting repeat', done: false, repeat: {{ every: 'day', n: 7 }}, due: '2026-10-25', waiting: true, milestoneId: 'mA' }},
        {{ id: 'b1', text: 'Long ago', done: true, doneAt: {at(2026, 9, 1)}, milestoneId: 'mB' }},
        {{ id: 'b2', text: 'Also long ago', done: true, doneAt: {at(2026, 9, 3)}, milestoneId: 'mB' }}] }});
      DB.projects = [A];
      const n = archiveDueTasks({MON});
      const out = {{ n, archived: A.todos.filter(t => t.archived).map(t => t.id), from: A.todos.find(t => t.id === 'a4').archiveFrom || '',
        msA: milestoneArchived(A, A.milestones[0]), msB: milestoneArchived(A, A.milestones[1]), msC: milestoneArchived(A, A.milestones[2]),
        live: liveMilestones(A).map(m => m.id), def: defaultMilestone(A),
        groups: archiveGroups(A).map(g => [g.ms ? g.ms.id : '', g.whole, g.tasks.map(t => t.id)]),
        prog: progressOf(A), at: A.todos.find(t => t.id === 'a1').archivedAt === {MON} }};
      DB.projects = keep;
      return out;
    }})()"""
    m = ev(f"() => {SET}")
    ok('D1 every done task ticked a week or more ago goes at once; one ticked six days ago stays', m['archived'] == ['a1', 'b1', 'b2'] and m['n'] == 3 and m['at'])
    ok('an open task and a waiting repeat never archive', 'a3' not in m['archived'] and 'a5' not in m['archived'])
    ok('a done task with no tick on record counts its 7 days from the day it is first seen', 'a4' not in m['archived'] and m['from'] == '2026-10-19')
    ok('B1 a milestone whose every task is archived is in the archive; one with an open task, or none at all, is not',
       m['msB'] is True and m['msA'] is False and m['msC'] is False and m['live'] == ['mA', 'mC'])
    ok('a task added without @ skips a milestone in the archive', m['def'] == 'mA')
    ok('C3 the archive by milestone, the milestone with the newest task first, its tasks newest first',
       m['groups'] == [['mA', False, ['a1']], ['mB', True, ['b2', 'b1']]])
    ok('B2 the progress still counts archived tasks as done', m['prog']['done'] == 5 and m['prog']['total'] == 7)
    ok('archiving on a day before the 7th does nothing',
       ev(f"() => {{ const keep = DB.projects; const A = blankProject({{ todos: [{{ text: 'x', done: true, doneAt: {at(2026, 10, 13)} }}] }}); DB.projects = [A]; const n = archiveDueTasks({MON}); DB.projects = keep; return n; }}") == 0)
    rs = ev(f"""() => {{ const t = {{ text: 'x', done: true, doneAt: {at(2026, 9, 1)}, archived: true, archivedAt: {at(2026, 9, 8)} }};
        const s = restoreTask(t, {MON}); const after = JSON.parse(JSON.stringify(t)); putBackArchive(s);
        return {{ after, back: JSON.parse(JSON.stringify(t)) }}; }}""")
    ok('C1 Restore brings it back done, its 7 days counting from the restore', rs['after'].get('archived') is None and rs['after']['done'] is True and rs['after']['archiveFrom'] == '2026-10-19')
    ok('and Undo puts the archive back exactly', rs['back'].get('archived') is True and rs['back'].get('archivedAt') and 'archiveFrom' not in rs['back'])
    ok('unticking a task clears its restore day',
       ev("() => { const p = blankProject(); const t = { text: 'x', done: true, doneAt: 1, archiveFrom: '2026-10-19' }; p.todos.push(t); untickTask(p, t); return t.done === false && !('archiveFrom' in t); }"))
    order = ev("""() => { const p = blankProject({ milestones: [{ id: 'm', name: 'M' }] });
        p.todos = ['a', 'X', 'b', 'c'].map(id => ({ id, text: id, done: id === 'X', archived: id === 'X', milestoneId: 'm' }));
        reorderShown(p, ['c', 'a', 'b'].map(id => p.todos.find(t => t.id === id))); return p.todos.map(t => t.id).join(''); }""")
    ok('a new order of the shown tasks keeps each archived task in its place', order == 'cXab')
    rd = ev("""() => sanitizeProjects([{ name: 'R', todos: [
        { text: 'a', done: true, doneAt: 5, archived: true, archivedAt: 9 }, { text: 'b', done: true, doneAt: 5, archived: true },
        { text: 'c', done: false, archived: true }, { text: 'd', done: true, archiveFrom: '2026-10-19' }, { text: 'e', done: true, archiveFrom: 'soon' }] }])[0].p.todos
        .map(t => [t.text, !!t.archived, t.archivedAt || null, t.archiveFrom || null])""")
    ok('0.1.50 reading saved data keeps a milestone folded in the archive, apart from its fold in the list',
       ev("() => sanitizeProjects([{ name: 'F', milestones: [{ id: 'f1', name: 'A', archiveCollapsed: true }, { id: 'f2', name: 'B', archiveCollapsed: 'yes', collapsed: true }] }])[0].p.milestones.map(m => [!!m.archiveCollapsed, m.collapsed])") == [[True, False], [False, True]])
    ok('reading saved data keeps the archive, on done tasks only, with a restore day only when it reads',
       rd == [['a', True, 9, None], ['b', True, 5, None], ['c', False, None, None], ['d', False, None, '2026-10-19'], ['e', False, None, None]])

    # copies, the summary, search and Reports
    COPY = f"""(() => {{
      const A = blankProject({{ name: 'Copyland', milestones: [{{ id: 'mA', name: 'One' }}, {{ id: 'mB', name: 'Two' }}], todos: [
        {{ id: 'c1', text: 'Shown done', done: true, doneAt: Date.now(), milestoneId: 'mA' }},
        {{ id: 'c2', text: 'Archived done', done: true, doneAt: 1, archived: true, archivedAt: 2, milestoneId: 'mA' }},
        {{ id: 'c3', text: 'Still open', done: false, milestoneId: 'mA' }},
        {{ id: 'c4', text: 'Whole milestone gone', done: true, doneAt: 1, archived: true, archivedAt: 2, milestoneId: 'mB' }}] }});
      return A; }})()"""
    cp = ev(f"""() => {{ const A = {COPY}; const keep = DB.projects; DB.projects = keep.concat([A]);
        const ms = milestoneForClaude(A, A.milestones[0]), tk = taskForClaude(A, A.todos[1]);
        const sum = ClaudeWork.citySummary().projects.find(x => x.name === 'Copyland');
        App.filter.q = norm('Whole milestone gone'); const found = matchesFilter(A); App.filter.q = '';
        const fin = milestonesFinished([A]).map(x => x.m.id);
        DB.projects = keep;
        return {{ ms, tk, sum: sum.milestones, found, fin }}; }}""")
    ok('A3 a milestone\'s Copy for Claude leaves its archived tasks out of its list', '- Shown done' in cp['ms'] and 'Archived done' not in cp['ms'])
    ok('B2 while its Progress line still counts them', 'Progress: 2/3 done' in cp['ms'])
    ok('Copy task says an archived task is in the archive', 'State: done, in the archive' in cp['tk'])
    ok('A3 the city summary leaves archived tasks out, and a milestone in the archive with them',
       [x['name'] for x in cp['sum']] == ['No milestone', 'One'] and cp['sum'][1]['done'] == ['Shown done'] and [o['task'] for o in cp['sum'][1]['open']] == ['Still open'])
    ok('A3 search still finds a building by its archived tasks', cp['found'] is True)
    ok('A3 Records still count a milestone that went to the archive as finished', cp['fin'] == ['mB'])
    pl = ev(f"""() => {{ const A = {COPY}; const keep = DB.projects; DB.projects = keep.concat([A]);
        const plan = readPlan({{ project: JSON.parse(JSON.stringify(A)) }});
        applyPlan(A, {{ name: '', description: 'New', milestones: [{{ name: 'Fresh', tasks: [{{ text: 'New task', description: '', due: '' }}] }}], ideas: [], links: [] }});
        DB.projects = keep;
        return {{ plan: plan.milestones.map(m => [m.name, m.tasks.map(t => t.text)]),
          after: A.milestones.map(m => m.name), arch: A.todos.filter(t => t.archived).map(t => [t.text, A.milestones.find(m => m.id === t.milestoneId).name]),
          live: liveMilestones(A).map(m => m.name) }}; }}""")
    ok('a project export loaded as a plan leaves its archive out, and a milestone all in the archive', pl['plan'] == [['One', ['Shown done', 'Still open']]])
    ok('a plan loaded over a project leaves its archive alone, each task under its own milestone',
       pl['arch'] == [['Archived done', 'One'], ['Whole milestone gone', 'Two']] and pl['after'] == ['Fresh', 'One', 'Two'])
    ok('and those milestones stay in the archive with them', pl['live'] == ['Fresh'])
    ok('@name brings a milestone in the archive back with the task added to it',
       ev(f"""() => {{ const A = {COPY}; const keep = DB.projects; DB.projects = keep.concat([A]);
          const r = readTaskLine('Bring it back @two', {{ project: A }}); const t = addTaskLine(r);
          const back = !milestoneArchived(A, A.milestones[1]) && t.milestoneId === 'mB' && liveMilestones(A).length === 2;
          DB.projects = keep; return back; }}"""))

    # ---------- D1: the first open after the update ----------
    ev(f"""() => {{ const p = {P}, [a, b, c] = p.todos;
        a.done = true; a.doneAt = Date.now() - 10 * {DAY};
        b.done = true; b.doneAt = Date.now() - 3 * {DAY};
        const l = p.todos.find(t => t.text === 'Publish the app'); l.done = true; l.doneAt = Date.now() - 9 * {DAY};
        p.updatedAt = 1700000000000; persistNow(); }}""")
    acts = ev(f"() => {P}.activity.length")
    pg.reload(); pg.wait_for_timeout(2000)
    ok('D1 on opening, done tasks ticked a week or more ago are in the archive at once',
       get('Draw the beds on a grid').get('archived') is True and get('Publish the app').get('archived') is True)
    ok('one ticked 3 days ago stays in its list', not get('Save a plan as a file').get('archived'))
    ok('archiving touches neither Updated nor Activity', ev(f"() => {P}.updatedAt") == 1700000000000 and ev(f"() => {P}.activity.length") == acts)

    # ---------- the project view ----------
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    rows = lambda ms: ev(f"() => [...document.querySelectorAll('.ms[data-msid=\"{ms}\"] li.task .task-title')].map(b => b.textContent)")
    ok('the list leaves archived tasks out', rows('m_first') == ['Save a plan as a file', 'Add plant icons', 'Tune the watering reminders'])
    ok('B2 the milestone\'s count still counts them', ev("() => document.querySelector('.ms[data-msid=\"m_first\"] .ms-count').textContent") == '(2/4)')
    ok('B1 a milestone whose every task is archived leaves the list with them', not pg.is_visible('.ms[data-msid="m_launch"]'))
    foot = '.ms[data-msid="m_first"] .ms-arch-btn'
    ok('E1 a count with the archive icon at the milestone\'s foot, and no words', pg.is_visible(foot) and
       ev(f"() => document.querySelector('{foot}').textContent") == '1' and ev(f"() => !!document.querySelector('{foot} svg')") and
       ev(f"() => document.querySelector('{foot}').title") == '1 in the archive' and
       ev(f"() => [...document.querySelector('.ms[data-msid=\"m_first\"] ul.tasks').children].pop().classList.contains('ms-archived')"))
    pg.screenshot(path=str(SHOTS / '330-archive-list.png'))
    # the more menu
    pg.click('#pvMore'); pg.wait_for_timeout(150)
    items = ev("() => [...document.querySelectorAll('.pv-menu-item')].map(b => b.textContent)")
    ok('E1 the more menu has the Archive, with its count', items[0] == 'Archive (2)')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    # the foot opens the Archive view at its milestone
    pg.click(foot); pg.wait_for_timeout(300)
    ok('a click on the count opens the Archive view beside the project view, at its milestone', pg.is_visible('#pvSide .pv-archive') and
       ev("() => document.activeElement.closest('.pv-arch-group').dataset.msid") == 'm_first')
    groups = ev("() => [...document.querySelectorAll('.pv-arch-group')].map(g => [g.querySelector('.pv-arch-name').textContent, g.querySelector('.ms-count').textContent, !!g.querySelector('.pv-arch-whole'), [...g.querySelectorAll('.pv-arch-title')].map(b => b.textContent)])")
    ok('C3 by milestone, the milestone with the newest task first',
       groups == [['Launch', '(1)', True, ['Publish the app']], ['First release', '(1)', False, ['Draw the beds on a grid']]])
    day = ev("() => document.querySelector('.pv-arch-task[data-id] .pv-arch-day').textContent")
    ok('each task with the day it was ticked', re.fullmatch(r'Ticked [A-Z][a-z]{2} \d{1,2} [A-Z][a-z]{2}( \d{4})?', day) is not None)
    ok('each with Restore', ev("() => document.querySelectorAll('.pv-arch-restore').length") == 2)
    pg.screenshot(path=str(SHOTS / '331-archive-view.png'))

    # folding a milestone in the archive, as in the list (0.1.50)
    tog = lambda ms: f'.pv-arch-group[data-msid="{ms}"] .pv-arch-toggle'
    ok('0.1.50 every milestone in the archive has a fold toggle, and starts open',
       ev("() => [...document.querySelectorAll('.pv-arch-group')].map(g => g.querySelector('.pv-arch-toggle').getAttribute('aria-expanded') + ':' + !g.querySelector('.pv-arch-list').hidden)") == ['true:true', 'true:true'])
    up0 = ev(f"() => {P}.updatedAt")
    pg.click(tog('m_first')); pg.wait_for_timeout(200)
    ok('a click folds it: its tasks hide, its name and count stay', not pg.is_visible('.pv-arch-group[data-msid="m_first"] .pv-arch-list') and
       pg.is_visible('.pv-arch-group[data-msid="m_first"] .pv-arch-name') and ev(f"() => document.querySelector('{tog('m_first')}').getAttribute('aria-expanded')") == 'false')
    ok('the focus stays on its toggle, and the other milestone stays open',
       ev("() => document.activeElement.classList.contains('pv-arch-toggle') && document.activeElement.closest('.pv-arch-group').dataset.msid") == 'm_first' and
       pg.is_visible('.pv-arch-group[data-msid="m_launch"] .pv-arch-list'))
    ok('folding in the archive leaves the list\'s fold alone, and is not work',
       ev(f"() => {P}.milestones.find(m => m.id === 'm_first').collapsed") is False and pg.is_visible('.ms[data-msid="m_first"] ul.tasks') and
       ev(f"() => {P}.milestones.find(m => m.id === 'm_first').archiveCollapsed") is True and ev(f"() => {P}.updatedAt") == up0)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click('#pvMore'); pg.wait_for_timeout(100); pg.click('.pv-menu-item >> nth=0'); pg.wait_for_timeout(250)
    ok('it stays folded when the archive opens again', not pg.is_visible('.pv-arch-group[data-msid="m_first"] .pv-arch-list'))
    pg.screenshot(path=str(SHOTS / '334-archive-folded.png'))
    pg.focus(tog('m_first')); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    ok('Enter on the toggle opens it again', pg.is_visible('.pv-arch-group[data-msid="m_first"] .pv-arch-list') and
       ev(f"() => 'archiveCollapsed' in {P}.milestones.find(m => m.id === 'm_first')") is False)
    pg.click(tog('m_first')); pg.wait_for_timeout(150)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click(foot); pg.wait_for_timeout(300)
    ok('opening the archive at a milestone, from its foot, unfolds it', pg.is_visible('.pv-arch-group[data-msid="m_first"] .pv-arch-list') and
       ev("() => document.activeElement.closest('.pv-arch-group').dataset.msid") == 'm_first')

    # an archived task, opened from the archive (C2)
    pg.click('.pv-arch-title >> text=Draw the beds on a grid'); pg.wait_for_timeout(300)
    ok('C2 a click opens the archived task in the task panel, to read', pg.is_visible('#pvSide .pv-task-archived') and
       ev("() => document.querySelector('#pvTaskTitle').tagName") == 'H3' and not ev("() => !!document.querySelector('#pvSide input, #pvSide textarea, #pvSide select')"))
    ok('marked in the archive, with the day it was ticked', ev("() => document.querySelector('.pv-arch-state').textContent").startswith('In the archive. Ticked '))
    ok('with Restore, Back to the archive, Open in Claude (Copy in its panel) and Delete task', all(pg.is_visible(s) for s in ['#pvTaskRestore', '#pvTaskBackArch', '#pvSide .pv-claude-row #pvTaskClaude', '#pvTaskDelete']))
    pg.screenshot(path=str(SHOTS / '332-archived-task.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc goes back to the archive, with the task in view', pg.is_visible('#pvSide .pv-archive') and ev("() => document.activeElement.textContent") == 'Draw the beds on a grid')
    pg.click('.pv-arch-title >> text=Draw the beds on a grid'); pg.wait_for_timeout(200)
    ev(f"() => {{ {P}.milestones.find(m => m.id === 'm_first').archiveCollapsed = true; }}")
    pg.click('#pvTaskBackArch'); pg.wait_for_timeout(200)
    ok('Back to the archive does the same, unfolding its milestone to show it', pg.is_visible('#pvSide .pv-archive') and ev("() => document.activeElement.textContent") == 'Draw the beds on a grid')

    # Restore (C1) from the archive
    quiet()
    pg.click('.pv-arch-task[data-id] >> nth=1 >> .pv-arch-restore'); pg.wait_for_timeout(300)
    t = get('Draw the beds on a grid')
    ok('C1 Restore brings it back done, in its old place, its 7 days from today', t['done'] and not t.get('archived') and t['archiveFrom'] == ev("() => ymd()") and
       rows('m_first')[0] == 'Draw the beds on a grid')
    ok('with a toast and Undo', toasted().startswith('Restored Draw the beds on a grid to First release.') and 'Undo' in toasted())
    ok('the archive shows what is left', ev("() => [...document.querySelectorAll('.pv-arch-title')].map(b => b.textContent)") == ['Publish the app'])
    undo(); pg.wait_for_timeout(200)
    ok('Undo puts it back in the archive', get('Draw the beds on a grid').get('archived') is True and 'archiveFrom' not in get('Draw the beds on a grid'))
    # restoring the task of a milestone in the archive brings the milestone back
    pg.click('.pv-arch-title >> text=Publish the app'); pg.wait_for_timeout(200)
    pg.click('#pvTaskRestore'); pg.wait_for_timeout(300)
    ok('B1 restoring a task of a milestone in the archive brings the milestone back', pg.is_visible('.ms[data-msid="m_launch"]') and rows('m_launch') == ['Publish the app'])
    ok('Restore in the panel shows the task as it is now, done, with Archive', pg.is_visible('#pvTaskArchive') and ev("() => document.querySelector('#pvTaskTitle').tagName") == 'INPUT')

    # by hand from the task panel (A1, h1)
    quiet()
    pg.click('#pvTaskArchive'); pg.wait_for_timeout(300)
    ok('A1 Archive in a done task\'s panel closes it and archives the task', not pg.is_visible('#pvSide') and get('Publish the app').get('archived') is True and
       not pg.is_visible('.ms[data-msid="m_launch"]'))
    ok('with a toast and Undo', toasted().startswith('Archived Publish the app.') and 'Undo' in toasted())
    undo(); pg.wait_for_timeout(200)
    ok('Undo brings it back', not get('Publish the app').get('archived') and pg.is_visible('.ms[data-msid="m_launch"]'))
    ok('an open task\'s panel has no Archive', ev(f"() => {{ FullView.openTask('{gp}', {task('Add plant icons')}.id); return !document.querySelector('#pvTaskArchive'); }}"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # by hand from a done row (A1, h2)
    ok('A1 a done row has an archive button; an open row has none',
       ev("() => !!document.querySelector('.task.done .mark-archive') && !document.querySelector('.task:not(.done) .mark-archive')"))
    pg.hover('.task.done[data-id] >> nth=0'); pg.wait_for_timeout(150)
    op = ev("() => getComputedStyle(document.querySelector('.task.done .mark-archive')).opacity")
    ok('it shows while the row is pointed at', float(op) > 0.5)
    quiet()
    sid = ev(f"() => {task('Save a plan as a file')}.id")
    pg.click(f'.task[data-id="{sid}"] .mark-archive'); pg.wait_for_timeout(300)
    ok('a click archives the task, out of the list', get('Save a plan as a file').get('archived') is True and 'Save a plan as a file' not in rows('m_first'))
    ok('with a toast and Undo', toasted().startswith('Archived Save a plan as a file.'))
    ok('the focus moves on, to the milestone\'s +', ev("() => document.activeElement.classList.contains('ms-plus') || document.activeElement.classList.contains('mark-archive')"))
    ok('the foot counts 2', ev(f"() => document.querySelector('{foot}').textContent") == '2')
    ok('neither archiving nor restoring is work: Updated and Activity stay', ev(f"() => {P}.updatedAt") == 1700000000000 and ev(f"() => {P}.activity.length") == acts)

    # Alt and an arrow skip the archived tasks
    pg.focus('.ms[data-msid="m_first"] li.task >> nth=0 >> .task-title')
    first = rows('m_first')[0]
    pg.keyboard.press('Alt+ArrowDown'); pg.wait_for_timeout(200)
    ok('Alt and an arrow move a task past its shown neighbor, the archived ones keeping their places',
       rows('m_first') == ['Tune the watering reminders', first] and
       ev(f"() => {P}.todos.map(t => t.text)")[:2] == ['Draw the beds on a grid', 'Save a plan as a file'])

    # the milestone view (E1, s2, and A1, h3)
    ev(f"() => {{ const t = {task('Add plant icons')}; t.done = true; t.doneAt = Date.now(); FullView.render(); }}"); pg.wait_for_timeout(150)
    pg.click('.ms[data-msid="m_first"] .ms-name-btn'); pg.wait_for_timeout(300)
    lis = ev("() => [...document.querySelectorAll('.pv-ms-task')].map(l => [l.querySelector('.pv-ms-text').firstChild.textContent, l.classList.contains('archived'), !!l.querySelector('.pv-ms-arch svg')])")
    ok('E1 the milestone view lists its archived tasks dimmed, with the archive icon, under the rest',
       [x[1] for x in lis] == [False, False, True, True] and all(x[2] for x in lis if x[1]) and
       ev("() => +getComputedStyle(document.querySelector('.pv-ms-task.archived')).opacity") < 0.7)
    ok('B2 its line still counts them', ev("() => document.querySelector('#pvSide .note').textContent").startswith('3 of 4 tasks done.'))
    ok('A1 it has Archive done tasks', pg.is_visible('#pvMsArchive'))
    pg.screenshot(path=str(SHOTS / '333-milestone-view.png'))
    quiet()
    pg.click('#pvMsArchive'); pg.wait_for_timeout(300)
    ok('it archives every done task in the milestone at once', get('Add plant icons').get('archived') is True and not get('Tune the watering reminders').get('archived'))
    ok('with a toast and Undo', toasted().startswith('Archived Add plant icons.') and 'Undo' in toasted())
    ok('the view stays open while the milestone has a task left', pg.is_visible('#pvSide .pv-ms-tasks') and not pg.is_visible('#pvMsArchive'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    # Launch: its one done task, archived from its milestone view, takes the milestone with it
    ev(f"() => {{ const t = {task('Publish the app')}; t.done = true; t.doneAt = Date.now(); FullView.render(); }}"); pg.wait_for_timeout(150)
    pg.click('.ms[data-msid="m_launch"] .ms-name-btn'); pg.wait_for_timeout(200)
    quiet()
    pg.click('#pvMsArchive'); pg.wait_for_timeout(300)
    ok('archiving a milestone\'s last tasks takes the milestone to the archive and closes its view',
       not pg.is_visible('#pvSide') and not pg.is_visible('.ms[data-msid="m_launch"]'))
    ok('the toast names it', toasted().startswith('Archived Publish the app.'))

    # Delete from the archive (C2)
    pg.click('#pvMore'); pg.wait_for_timeout(100)
    ok('the menu counts 4', ev("() => document.querySelector('.pv-menu-item').textContent") == 'Archive (4)')
    pg.click('.pv-menu-item >> nth=0'); pg.wait_for_timeout(300)
    pg.click('.pv-arch-title >> text=Publish the app'); pg.wait_for_timeout(200)
    pg.click('#pvTaskDelete'); pg.wait_for_timeout(300)
    ok('C2 Delete task in an archived task\'s panel deletes it and goes back to the archive', get('Publish the app') is None and pg.is_visible('#pvSide .pv-archive'))
    ok('the last task of a milestone in the archive takes the milestone with it', ev(f"() => {P}.milestones.some(m => m.id === 'm_launch')") is False and
       not pg.is_visible('.ms[data-msid="m_launch"]'))

    # the Archive view, empty
    ev(f"() => {{ for (const t of {P}.todos) if (t.archived) restoreTask(t); FullView.render(); }}"); pg.wait_for_timeout(200)
    ok('an empty archive says so', ev("() => document.querySelector('#pvSide .fv-empty').textContent") == 'Nothing in the archive yet.')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    pg.click('#pvMore'); pg.wait_for_timeout(100)
    ok('with nothing in it, the menu says Archive alone', ev("() => document.querySelector('.pv-menu-item').textContent") == 'Archive')
    pg.keyboard.press('Escape')
    ok('the foot count goes when nothing is archived', not pg.is_visible('.ms-arch-btn'))

    # every milestone in the archive
    ev(f"() => {{ const p = {P}; for (const t of p.todos) {{ t.done = true; t.doneAt = Date.now(); }} archiveTasks(p.todos); FullView.render(); }}"); pg.wait_for_timeout(150)
    ok('with every milestone in the archive, the list says so', ev("() => document.querySelector('.ms-list .fv-empty').textContent") == 'Every milestone is in the archive. Add one to plan what is next.')
    ok('the status card\'s add field makes a new To do', ev(f"() => {{ const r = readTaskLine('A new start', {{ project: {P} }}); const t = addTaskLine(r); return {P}.milestones.find(m => m.id === t.milestoneId).name; }}") == 'To do')

    # saved and read back
    ev("() => persistNow()")
    pg.reload(); pg.wait_for_timeout(1800)
    ok('the archive is saved and read back', len(ev(f"() => {P}.todos.filter(t => t.archived).map(t => t.text)")) == 4)
    b.close()
print(errors or 'no console errors')
