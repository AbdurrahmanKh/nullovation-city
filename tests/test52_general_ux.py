"""General UX, Round 1 (0.1.86): the pixel font's c opened; tasks in place of todos; the side bar's Due and overdue and
Search the city; the project view's header with Activity and the status for Claude, Change and the milestone's + shown
when pointed at, the notes' icon and copy button as stickers, and the leader saying where the building stands; and the
task panel rethought: no pink Done, the title and the description read as text until clicked, Pin and Star by the
title, Due, Repeat and Shift in one label column, the due date's list, and Claude, Turn into a note and Delete task."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY, ROOT

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

# ---------- the font file: a Modified Version of the upstream one, kept beside its script ----------
up = (ROOT / 'tools' / 'fonts' / 'pixelify-sans-latin-wght-normal.woff2').read_bytes()
mine = (ROOT / 'src' / 'fonts' / 'pixelify-sans' / 'pixelify-sans-latin-wght-normal.woff2').read_bytes()
ok('the city ships its own copy of Pixelify Sans, changed from the upstream file kept in tools/fonts', up != mine and up[:4] == mine[:4] == b'wOF2')
ok('tools/open_c.py, the script that opens the c, is in the source', (ROOT / 'tools' / 'open_c.py').is_file())

GAP = """async ([ch, size]) => { await document.fonts.load(`400 ${size}px "Pixelify Sans"`, ch);
  const c = document.createElement('canvas'); c.width = c.height = size * 2; const g = c.getContext('2d');
  g.font = `400 ${size}px "Pixelify Sans"`; g.fillStyle = '#000'; g.textBaseline = 'top'; g.fillText(ch, 4, 4);
  const d = g.getImageData(0, 0, c.width, c.height).data, ink = (x, y) => d[(y * c.width + x) * 4 + 3] > 128;
  let x1 = -1, y0 = c.height, y1 = -1;
  for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) if (ink(x, y)) { x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  let top = -1, bot = -1;                                  // the open stretch between the ink at the top and the foot of its right edge
  for (let y = y0; y <= y1; y++) if (ink(x1, y)) { if (top < 0) top = y; bot = y; }
  let gap = 0; for (let y = top; y <= bot; y++) if (!ink(x1, y)) gap++;
  return gap; }"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    quiet = lambda: ev("() => { document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true); }")
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    tid = lambda text: ev(f"() => (getProject('{gp}').todos.find(t => t.text === {json.dumps(text)}) || {{}}).id || null")
    task = lambda text: ev(f"() => getProject('{gp}').todos.find(t => t.text === {json.dumps(text)}) || null")
    open_task = lambda text, **o: (ev(f"([t, o]) => FullView.openTask('{gp}', (getProject('{gp}').todos.find(x => x.text === t) || {{}}).id, o)", [text, o]), pg.wait_for_timeout(500))
    active = lambda: ev("() => document.activeElement && document.activeElement.id")
    box = lambda sel: ev(f"() => {{ const e = document.querySelector({json.dumps(sel)}); if (!e) return null; const r = e.getBoundingClientRect(); return {{ x: r.left, y: r.top, w: r.width, h: r.height, r: r.right, b: r.bottom }}; }}")
    style = lambda sel, prop: ev(f"() => {{ const e = document.querySelector({json.dumps(sel)}); return e ? getComputedStyle(e)[{json.dumps(prop)}] : null; }}")
    quiet()

    # ---------- X2: the pixel font's c, open ----------
    gc, gC, go = ev(GAP, ['c', 40]), ev(GAP, ['C', 40]), ev(GAP, ['o', 40])
    ok(f'the small c is open at 40 px: a gap of {gc} px down its right edge, where an o has none ({go})', gc >= 5 and go == 0)
    ok(f'the capital C is open at 40 px: a gap of {gC} px', gC >= 8)
    g16 = ev(GAP, ['c', 16])
    ok(f'and at the buttons\' 16 px the c still shows its gap ({g16} px)', g16 >= 2)

    # ---------- X1 and C1: tasks, and the side bar ----------
    ok('the side bar\'s list says Due and overdue', ev("() => document.querySelector('#sbDue .sb-h').textContent") == 'Due and overdue'
       and ev("() => document.querySelector('#sbDue').getAttribute('aria-label')") == 'Due and overdue')
    ok('search says Search the city', ev("() => document.querySelector('#search').placeholder") == 'Search the city')
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(600)
    more = ev("() => (document.querySelector('#bubble .b-more') || {}).textContent || null")
    ok(f'the status card says tasks: {more}', more == '2 more open tasks inside')
    ev("() => MapView.deselect()")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600); quiet()
    heads = ev("() => [...document.querySelectorAll('#pv .pv-sec-head h3, #pv .pv-h')].map(e => e.textContent)")
    ok(f'the project view\'s section says Tasks, not Todos ({heads})', 'Tasks' in heads and 'Todos' not in heads)
    det = ev("() => document.querySelector('#pv .fv-prog .detail').textContent")
    ok(f'its count says tasks ({det})', det == '0 of 5 tasks done')
    stats = ev("() => document.querySelector('#pv .pv-stats').textContent")
    ok(f'the line under the picture drops its count, which the bar has ({stats})', stats.startswith('Founded ') and ' · Updated ' in stats and 'done' not in stats)
    ok('no word todo is left on the project view', 'todo' not in ev("() => document.querySelector('#pv').innerText").lower())

    # ---------- P1: Activity and the status for Claude in the header ----------
    acts = ev("() => [...document.querySelectorAll('#pv .pv-top .pv-actions > *')].map(e => e.id || e.getAttribute('aria-label'))")
    ok(f'the header holds Activity and the status for Claude, then the more button and the close ({acts})', acts[:3] == ['pvActivityBtn', 'pvStatusClaude', 'pvMore'] and len(acts) == 4)
    ok('both are icons, named when pointed at', ev("""() => ['#pvActivityBtn', '#pvStatusClaude'].every(s => { const e = document.querySelector(s);
        return e.classList.contains('icon-btn') && !e.textContent.trim() && e.querySelector('svg') && e.title && e.getAttribute('aria-label'); })"""))
    ok('the About keeps what the project is and what is next: its Activity and Open in Claude are gone', not ev("() => document.querySelector('.pv-about-btns')")
       and not ev("() => [...document.querySelectorAll('#pv .pv-about button')].some(b => /Activity|Open in Claude/.test(b.textContent) && b.id !== 'pvNextClaude' && !b.closest('.pv-next'))"))
    pg.click('#pvActivityBtn'); pg.wait_for_timeout(400)
    ok('Activity opens the building\'s activity beside the view', ev("() => document.querySelector('#pvSide .pv-title').textContent") == 'Activity')
    ev("() => FullView.escape()"); pg.wait_for_timeout(300)
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(400)
    ok('the status for Claude opens Open in Claude\'s panel on the project\'s status', ev("() => document.querySelector('#pvStatusClaude').getAttribute('aria-expanded')") == 'true')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SHOTS / '520-ux-header.png'), clip={'x': 0, 'y': 0, 'width': 900, 'height': 120})

    # ---------- X3: the milestone's + and Change, shown when pointed at ----------
    ev(f"""() => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Nullovations' }}); DB.leaders.push(l); getProject('{gp}').leader = l.id; changed(getProject('{gp}'), {{ touch: false }}); FullView.render(); }}""")
    pg.wait_for_timeout(400); pg.mouse.move(5, 990); pg.wait_for_timeout(300)
    ok('the milestone\'s + is plain, with no box', style('#pv .ms-plus', 'boxShadow') == 'none')
    ok('with a mouse, it hides until its row is pointed at', style('#pv .ms-plus', 'opacity') == '0')
    pg.hover('#pv .ms-row'); pg.wait_for_timeout(200)
    ok('and shows on the row pointed at', style('#pv .ms-plus', 'opacity') == '1')
    ok('Change on the leader card hides until the card is pointed at', style('#pv .ld-change', 'opacity') == '0')
    pg.hover('#pvLeader'); pg.wait_for_timeout(300)
    ok('and shows when it is', style('#pv .ld-change', 'opacity') == '1')
    pg.mouse.move(5, 990); ev("() => document.querySelector('#pv .ld-change').focus()"); pg.wait_for_timeout(300)
    ok('and when it has the focus', style('#pv .ld-change', 'opacity') == '1')

    # ---------- P3: the leader says where the building stands ----------
    says = ev("() => [document.querySelector('#pvLeader .ld-says').textContent, (document.querySelector('#pvLeader .lc-tline') || {}).textContent]")
    ok(f'the leader card says where it stands, then the next task, in the task line since 0.1.96 ({says})', says == ['5 to go. This one is next.', 'Draw the beds on a grid'])
    G = f"""(o) => {{ const p = structuredClone(getProject('{gp}')), now = Date.now(), D = 864e5;
        Object.assign(p.urgency, o.u || {{}});
        for (const [i, k] of (o.ticks || []).entries()) {{ p.todos[i].done = true; p.todos[i].doneAt = now - k; }}
        if (o.late) p.todos[p.todos.length - 1].due = ymd(now - o.late * D);
        return leaderGreeting(p, now); }}"""
    g = lambda **o: ev(G, o)
    ok(f'a task ticked today: {g(ticks=[1000])}', g(ticks=[1000]) == 'We finished one today, 4 to go. Next up: Save a plan as a file.')
    ok(f'two: {g(ticks=[1000, 2000])}', g(ticks=[1000, 2000]) == 'We finished two today, 3 to go. Next up: Add plant icons.')
    D = 86400000
    on = ev(G.replace("Object.assign(p.urgency, o.u || {});", "Object.assign(p.urgency, { system: 'pace', days: 3, pickedAt: now - 2 * D, lastWorked: now - 3600000 });"), {})
    ok(f'on its pace: {on}', on == "We're on pace, 5 to go. Next up: Draw the beds on a grid.")
    yel = ev(G.replace("Object.assign(p.urgency, o.u || {});", "Object.assign(p.urgency, { system: 'pace', days: 3, pickedAt: now - D, lastWorked: 0 });"), {})
    ok(f'one period behind: {yel}', yel == 'We slipped behind our pace, 5 to go. Next up: Draw the beds on a grid.')
    red = ev(G.replace("Object.assign(p.urgency, o.u || {});", "Object.assign(p.urgency, { system: 'pace', days: 3, pickedAt: now - 4 * D, lastWorked: 0 });"), {})
    ok(f'two periods behind: {red}', red == "We're falling further behind, 5 to go. Next up: Draw the beds on a grid.")
    day = ev(G.replace("Object.assign(p.urgency, o.u || {});", "Object.assign(p.urgency, { system: 'finish', lastWorked: now - 2 * D });"), {})
    ok(f'Work until finished, nothing for a day: {day}', day == 'Nothing finished here for a day, 5 to go. Next up: Draw the beds on a grid.')
    late = g(late=3)
    ok(f'overdue tasks are counted in: {late}', late == '5 to go, 1 of them overdue. Next up: Publish the app.' or late.startswith('5 to go, 1 of them overdue. Next up:'))
    ok('nothing open still says so', ev("() => leaderGreeting({ todos: [], milestones: [], pin: '', urgency: { system: 'none' }, activity: [] })") == 'Nothing open here yet. Add the next task.')

    # ---------- P2: the notes' icon and copy button as stickers ----------
    ev(f"""() => {{ const p = getProject('{gp}'); p.notes.push({{ id: 'n1', title: 'Windows notification when Claude needs you', text: 'A line.', at: Date.now() }}); changed(p, {{ touch: false }}); FullView.render(); }}""")
    pg.wait_for_timeout(400)
    card, ic = box('#pv .pv-note-card'), box('#pv .pv-note-card .note-ic')
    ok(f'the note\'s icon sits on the card\'s top left corner, half off it ({ic and round(ic["y"] - card["y"])} px)', ic['y'] < card['y'] and ic['x'] < card['x'] + 4)
    ok('so its title takes the card\'s width, with no room kept for the copy button', style('#pv .pv-note-cell .pv-note-h', 'paddingInlineEnd') == '0px'
       and box('#pv .pv-note-ht')['w'] > card['w'] - 30)
    pg.hover('#pv .pv-note-cell'); pg.wait_for_timeout(300)
    cp = box('#pv .pv-note-copy')
    ok('its copy button sits on the top right corner when pointed at', cp['y'] < card['y'] and cp['r'] > card['r'] - 4 and style('#pv .pv-note-copy', 'opacity') == '1')
    pg.screenshot(path=str(SHOTS / '521-ux-notes.png'), clip={'x': card['x'] - 20, 'y': card['y'] - 20, 'width': 420, 'height': 200})

    # ---------- T1 to T4: the task panel ----------
    open_task('Draw the beds on a grid'); quiet()
    ok('the task panel has no pink Done: its x closes it', not ev("() => document.querySelector('#pvSide .pv-top .btn-accent')")
       and ev("() => document.querySelectorAll('#pvSide .pv-top button').length") == 1)
    ok('it opens with nothing being written: the panel has the focus', active() == 'pvSide' and not ev("() => document.querySelector('#pvSide textarea')"))
    head = ev("() => [...document.querySelector('#pvSide .pv-task-head').children].map(e => e.id || e.className)")
    ok(f'the title row: the Done check, the title, then Pin and Star ({head})', head[0] == 'pvTaskDone' and head[1] == 'pvTaskName' and 'pv-task-marks' in head[2])
    ok('the title reads as text, in the pixel font, as big as before', ev("() => document.querySelector('#pvTaskName').tagName") == 'BUTTON'
       and ev("() => document.querySelector('#pvTaskName').textContent") == 'Draw the beds on a grid' and style('#pvTaskName', 'fontSize') == '20px')
    marks = ev("() => [...document.querySelectorAll('#pvSide .pv-task-marks .pv-mark')].map(b => [b.dataset.mark, b.textContent.trim(), b.getAttribute('aria-label'), b.getAttribute('aria-pressed')])")
    ok(f'Pin and Star are icons with no words, named for a screen reader ({marks})', marks == [['pin', '', 'Pin as next', 'false'], ['star', '', 'Star for the city', 'false']])
    pg.click('#pvSide [data-mark="pin"]'); pg.wait_for_timeout(300)
    ok('Pin pins it, pressed, the focus kept', ev(f"() => getProject('{gp}').pin") == tid('Draw the beds on a grid')
       and ev("() => document.querySelector('#pvSide [data-mark=\"pin\"]').getAttribute('aria-pressed')") == 'true' and ev("() => document.activeElement.dataset.mark") == 'pin')
    pg.click('#pvSide [data-mark="pin"]'); pg.wait_for_timeout(300)
    lbls = ev("() => [...document.querySelectorAll('#pvSide .pv-fields > .pv-flbl')].map(e => e.textContent)")
    ok(f'Due, Repeat and Shift in one label column ({lbls})', lbls == ['Due', 'Repeat', 'Shift'])
    xs = ev("() => [...document.querySelectorAll('#pvSide .pv-fields > .pv-flbl')].map(e => Math.round(e.getBoundingClientRect().left))")
    cx = ev("() => [...document.querySelectorAll('#pvSide .pv-fields > :not(.pv-flbl)')].map(e => Math.round(e.getBoundingClientRect().left))")
    ok(f'the labels start on one line, and so do their values ({xs}, {cx})', len(set(xs)) == 1 and len(set(cx)) == 1 and cx[0] > xs[0] + 50)
    ok('Repeat reads as its words, with no box until clicked', style('#pvRepeat', 'borderTopColor') == 'rgba(0, 0, 0, 0)' and style('#pvRepeat', 'backgroundColor') == 'rgba(0, 0, 0, 0)'
       and ev("() => document.querySelector('#pvRepeat').selectedOptions[0].textContent") == 'No repeat')

    # the due date
    due_txt = lambda: ev("() => document.querySelector('#pvTaskDue').textContent")
    ok(f'Due reads No date, a button with its arrow ({due_txt()})', due_txt() == 'No date' and ev("() => !!document.querySelector('#pvTaskDue .pv-chev svg')")
       and not ev("() => document.querySelector('#pvTaskDueClear')") and not ev("() => document.querySelector('#pvSide input[type=date]')"))
    pg.click('#pvTaskDue'); pg.wait_for_timeout(300)
    opts = ev("() => [...document.querySelectorAll('#pvDueList [role=option]')].map(li => [li.querySelector('.qa-label').textContent, li.querySelector('.qa-note').textContent])")
    tomorrow, week = ev("() => { const f = n => { const d = new Date(startOfDay(Date.now())); d.setDate(d.getDate() + n); const s = ymd(d.getTime()); return weekdayOf(s) + ' ' + fmtDate(parseYmd(s)); }; return [f(1), f(7)]; }")
    ok(f'its list: Tomorrow, Next week and Pick a date, each with its day ({opts})', opts == [['Tomorrow', tomorrow], ['Next week', week], ['Pick a date', 'The calendar']])
    ok('with no ! marks', not ev("() => document.querySelector('#pvDueList .qa-glyph')") and '!' not in ev("() => document.querySelector('#pvDueList').textContent"))
    ok('the button says its list is open', ev("() => document.querySelector('#pvTaskDue').getAttribute('aria-expanded')") == 'true')
    pg.screenshot(path=str(SHOTS / '522-ux-due-list.png'), clip=box('#pvSide') and {'x': box('#pvSide')['x'], 'y': 0, 'width': box('#pvSide')['w'], 'height': 520})
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes the list alone, the focus back on the button, the panel open', not ev("() => document.querySelector('#pvDueList')") and ev("() => !!document.querySelector('#pvSide')") and active() == 'pvTaskDue')
    pg.click('#pvTaskDue'); pg.click('#pvDueList [role=option]:nth-child(1)'); pg.wait_for_timeout(300)
    ok(f'Tomorrow sets tomorrow, said in the city\'s words ({due_txt()})', due_txt() == tomorrow and task('Draw the beds on a grid')['due'] == ev("() => { const d = new Date(startOfDay(Date.now())); d.setDate(d.getDate() + 1); return ymd(d.getTime()); }")
       and active() == 'pvTaskDue')
    ok('a small x shows once there is a date', ev("() => !!document.querySelector('#pvTaskDueClear')") and not ev("() => document.querySelector('#pvTaskDue .pv-chev')"))
    pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(200)
    ok('the down arrow on the button opens the list on its first choice', ev("() => document.activeElement.closest('#pvDueList') && document.activeElement.textContent.startsWith('Tomorrow')"))
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    ok(f'the arrows and Enter pick Next week ({due_txt()})', due_txt() == week)
    pg.click('#pvTaskDue'); pg.wait_for_timeout(200); pg.click('#pvSide .pv-task-ms'); pg.wait_for_timeout(200)
    ok('a click elsewhere closes the list', not ev("() => document.querySelector('#pvDueList')"))
    pg.click('#pvTaskDue'); pg.wait_for_timeout(200)
    ok('Pick a date holds the browser\'s own calendar, unseen, under the mouse\'s reach', ev("() => { const i = document.querySelector('#pvTaskDuePick'); return i && i.type === 'date' && getComputedStyle(i).opacity === '0' && getComputedStyle(i).pointerEvents === 'none'; }"))
    ev("() => { const i = document.querySelector('#pvTaskDuePick'); i.value = '2030-03-14'; i.dispatchEvent(new Event('change', { bubbles: true })); }"); pg.wait_for_timeout(300)
    ok(f'a day picked in the calendar is the due date ({due_txt()})', task('Draw the beds on a grid')['due'] == '2030-03-14' and not ev("() => document.querySelector('#pvDueList')"))
    pg.click('#pvTaskDueClear'); pg.wait_for_timeout(300)
    ok('the x takes the date off, back to No date', task('Draw the beds on a grid')['due'] == '' and due_txt() == 'No date')
    ev(f"() => {{ const t = getProject('{gp}').todos.find(x => x.text === 'Draw the beds on a grid'); t.due = ymd(Date.now() - 3 * 864e5); FullView.render(); }}"); pg.wait_for_timeout(300)
    ok(f'an overdue date reads red, with how late ({ev("() => document.querySelector(\'#pvSide .pv-due\').textContent")})', 'late' in ev("() => document.querySelector('#pvTaskDue').className")
       and ev("() => document.querySelector('#pvSide .pv-due .due.late').textContent") == '! 3 days overdue')
    ev(f"() => {{ const t = getProject('{gp}').todos.find(x => x.text === 'Draw the beds on a grid'); t.due = ''; FullView.render(); }}"); pg.wait_for_timeout(300)

    # the description
    ev(f"() => {{ const t = getProject('{gp}').todos.find(x => x.text === 'Draw the beds on a grid'); t.description = 'Each bed on the grid.\\n\\nThe paths stay wide.'; FullView.render(); }}"); pg.wait_for_timeout(300)
    dv = box('#pvTaskDescView')
    ok(f'the description reads as text in its own box, at least as tall as before ({dv and round(dv["h"])} px)', ev("() => document.querySelector('#pvTaskDescView').tagName") == 'DIV'
       and dv['h'] >= 360 and style('#pvTaskDescView', 'borderTopStyle') == 'solid' and ev("() => document.querySelector('#pvTaskDescView').textContent") == 'Each bed on the grid.\n\nThe paths stay wide.')
    edge = style('#pvTaskDescView', 'borderTopColor'); pg.hover('#pvTaskDescView'); pg.wait_for_timeout(200)
    ok('pointed at, its edge lights, to say a click writes in it', style('#pvTaskDescView', 'borderTopColor') != edge)
    pg.screenshot(path=str(SHOTS / '523-ux-task-panel.png'), clip={'x': box('#pvSide')['x'], 'y': 0, 'width': box('#pvSide')['w'], 'height': 1000})
    pg.click('#pvTaskDescView', position={'x': 40, 'y': 22}); pg.wait_for_timeout(300)
    at = ev("() => [document.activeElement.id, document.activeElement.tagName, document.activeElement.selectionStart]")
    ok(f'a click writes in the same box, the caret where it landed ({at})', at[0] == 'pvTaskDesc' and at[1] == 'TEXTAREA' and 0 < at[2] < 10)
    ta = box('#pvTaskDesc')
    ok(f'writing, the box keeps its place and size ({round(ta["h"])} px)', abs(ta['y'] - dv['y']) < 2 and abs(ta['h'] - dv['h']) < 3)
    pg.keyboard.press('End'); pg.keyboard.type(' More beds.')
    ok('what is written is kept as it is typed', task('Draw the beds on a grid')['description'].startswith('Each bed on the grid. More beds.'))
    ev("() => FullView.render()"); pg.wait_for_timeout(200)
    ok('the panel drawing again keeps the writing and its caret', active() == 'pvTaskDesc' and ev("() => document.activeElement.selectionStart") == len('Each bed on the grid. More beds.'))
    long = 'A line of the plan, written out.\n' * 30
    ev("(s) => { const f = document.querySelector('#pvTaskDesc'); f.value = s; f.dispatchEvent(new Event('input', { bubbles: true })); }", long); pg.wait_for_timeout(200)
    ok(f'it grows with its text, with no scroll bar ({round(box("#pvTaskDesc")["h"])} px)', box('#pvTaskDesc')['h'] > 600 and ev("() => { const f = document.querySelector('#pvTaskDesc'); return f.scrollHeight <= f.clientHeight + 1; }"))
    pg.click('#pvSide .pv-task-ms'); pg.wait_for_timeout(300)
    ok('clicked away, it reads as text again, as tall as its text', ev("() => !!document.querySelector('#pvTaskDescView') && !document.querySelector('#pvTaskDesc')") and box('#pvTaskDescView')['h'] > 600)
    ev(f"() => {{ const t = getProject('{gp}').todos.find(x => x.text === 'Draw the beds on a grid'); t.description = ''; FullView.render(); }}"); pg.wait_for_timeout(300)
    ok('with none, it says what goes there, in a quiet color', 'empty' in ev("() => document.querySelector('#pvTaskDescView').className")
       and ev("() => document.querySelector('#pvTaskDescView').textContent").startswith('What this task is, in full'))
    ev("() => document.querySelector('#pvTaskDescView').focus()"); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    ok('Enter on it starts writing too', active() == 'pvTaskDesc')
    pg.keyboard.press('Tab'); pg.wait_for_timeout(200)

    # the title
    nb = box('#pvTaskName'); pg.click('#pvTaskName'); pg.wait_for_timeout(200)
    tb = box('#pvTaskTitle')
    ok(f'a click on the title writes it in place, in a box of the same size, so nothing under it moves ({round(nb["h"])} and {round(tb["h"])} px)',
       active() == 'pvTaskTitle' and abs(tb['y'] - nb['y']) < 1 and abs(tb['h'] - nb['h']) < 1.5 and abs(tb['w'] - nb['w']) < 1.5)
    pg.keyboard.press('End'); pg.keyboard.type(' and paths')
    ok('the list follows as it is typed', ev(f"() => document.querySelector('li.task[data-id=\"{tid('Draw the beds on a grid and paths')}\"] .task-title').textContent") == 'Draw the beds on a grid and paths')
    pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    ok('Enter ends it: no new line, the title read as text, the focus on it', active() == 'pvTaskName' and ev("() => document.querySelector('#pvTaskName').textContent") == 'Draw the beds on a grid and paths')

    # the foot
    foot = ev("() => [...document.querySelector('#pvSide .pv-task-foot').children].map(e => [e.id, e.textContent.trim(), e.className])")
    ok(f'the foot: Claude, then Turn into a note and Delete task under it ({[f[:2] for f in foot]})', [f[0] for f in foot] == ['pvTaskClaude', 'pvTaskToNote', 'pvTaskDelete']
       and foot[0][1] == 'Claude' and 'btn-accent' in foot[0][2])
    fb = [box('#pvTaskClaude'), box('#pvTaskToNote'), box('#pvTaskDelete')]
    ok('one under the other', fb[0]['b'] <= fb[1]['y'] + 1 and fb[1]['b'] <= fb[2]['y'] + 1)
    icx = ev("() => ['#pvTaskToNote', '#pvTaskDelete'].map(s => Math.round(document.querySelector(s + ' svg').getBoundingClientRect().left))")
    ok(f'the plain two start on Claude\'s left edge, icon then words ({icx} against {round(fb[0]["x"])})', all(abs(x - fb[0]['x']) <= 2 for x in icx))
    ok('they are plain: no box', style('#pvTaskToNote', 'boxShadow') == 'none' and style('#pvTaskDelete', 'boxShadow') == 'none'
       and style('#pvTaskToNote', 'backgroundColor') == 'rgba(0, 0, 0, 0)')
    ok('Delete task keeps its red, with the bin', style('#pvTaskDelete', 'color') == 'rgb(255, 111, 163)' and ev("() => document.querySelectorAll('#pvTaskDelete svg rect').length") > 5)
    ok('Claude is filled, its spark white', ev("() => [...document.querySelectorAll('#pvTaskClaude svg rect')].some(r => r.style.fill === 'rgb(255, 255, 255)' || r.style.fill === '#FFFFFF' || r.style.fill === '#ffffff')"))
    ok('the panel\'s note says the x closes it', ev("() => [...document.querySelectorAll('#pvSide .note')].pop().textContent").startswith('Saves as you type. The × closes it'))
    pg.click('#pvSide .pv-top .icon-btn'); pg.wait_for_timeout(400)
    ok('the x closes the panel, keeping what was typed, with its Activity line', not ev("() => document.querySelector('#pvSide')") and task('Draw the beds on a grid and paths') is not None
       and ev(f"() => getProject('{gp}').activity.some(a => a.text === 'Edited task: Draw the beds on a grid and paths')"))

    # Esc still undoes everything since it opened
    open_task('Save a plan as a file')
    pg.click('#pvTaskName'); pg.keyboard.press('End'); pg.keyboard.type(' now'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc undoes everything since the panel opened, a title being written too', task('Save a plan as a file') is not None and not ev("() => document.querySelector('#pvSide')"))

    # a done task: Archive by the title; a waiting repeat: its line, no check
    ev(f"() => {{ const t = getProject('{gp}').todos.find(x => x.text === 'Add plant icons'); t.done = true; t.doneAt = Date.now(); }}")
    open_task('Add plant icons')
    ok('a done task has Archive by its title, in place of Pin and Star', ev("() => [...document.querySelectorAll('#pvSide .pv-task-marks button')].map(b => b.id).join()") == 'pvTaskArchive'
       and not ev("() => document.querySelector('#pvSide .pv-fields #pvRepeat')"))
    ev("() => FullView.escape()"); pg.wait_for_timeout(200)
    ev(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(x => x.text === 'Tune the watering reminders'); t.repeat = {{ every: 'week', days: [1] }}; tickTask(p, t); }}")
    open_task('Tune the watering reminders')
    ok('a ticked repeat waiting for its day has no check, and says when it comes back', not ev("() => document.querySelector('#pvTaskDone')")
       and ev("() => document.querySelector('#pvSide .pv-task-back').textContent").startswith('Ticked. Back '))
    ev("() => FullView.escape()"); pg.wait_for_timeout(200)

    # Delete task
    ev(f"() => getProject('{gp}').todos.push(Object.assign(todo('Throw this one away', 'm_first')))"); open_task('Throw this one away')
    pg.click('#pvTaskDelete'); pg.wait_for_timeout(400)
    ok('Delete task deletes it and closes the panel', task('Throw this one away') is None and not ev("() => document.querySelector('#pvSide')"))

    # the note and milestone panels have no pink Done either
    ev(f"() => FullView.openNote('{gp}', 'n1')"); pg.wait_for_timeout(400)
    ok('the note panel has no pink Done', not ev("() => document.querySelector('#pvSide .pv-top .btn-accent')"))
    pg.click('#pvSide .pv-top .icon-btn'); pg.wait_for_timeout(300)
    ok('its x closes it, the focus back on Add note', not ev("() => document.querySelector('#pvSide')") and active() == 'pvAddNoteBtn')
    pg.click('#pv .ms-name-btn'); pg.wait_for_timeout(400)
    ok('nor the milestone panel, whose note says the x closes it', not ev("() => document.querySelector('#pvSide .pv-top .btn-accent')")
       and 'The × closes it' in ev("() => document.querySelector('#pvSide').textContent"))
    ev("() => FullView.escape()"); pg.wait_for_timeout(200)

    # the line over the map's Ctrl+Enter opens the task ready for a description
    ev("() => FullView.close()"); pg.wait_for_timeout(300)
    ev("() => QuickAdd.open({ text: '' })"); pg.wait_for_timeout(300)
    pg.fill('#quickAddIn', 'Hoe the rows /garden'); pg.keyboard.press('Control+Enter'); pg.wait_for_timeout(700)
    ok('Ctrl+Enter on the line over the map opens the task with its description being written', active() == 'pvTaskDesc')
    ev("() => FullView.close()"); pg.wait_for_timeout(300)

    # an archived task's panel has the same foot
    ev(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(x => x.text === 'Add plant icons'); archiveTasks([t]); changed(p, {{ touch: false }}); FullView.openTask('{gp}', t.id); }}"); pg.wait_for_timeout(500)
    af = ev("() => [...document.querySelector('#pvSide .pv-task-foot').children].map(e => e.id + ':' + e.textContent.trim())")
    ok(f'an archived task\'s panel has the same foot: Claude, then Delete task ({af})', af == ['pvTaskClaude:Claude', 'pvTaskDelete:Delete task'])
    ev("() => FullView.close()")
    ctx.close()

    # ---------- on a phone: what shows when pointed at shows all the time ----------
    ph = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ph.add_init_script(TEST_CITY)
    pp = ph.new_page()
    pp.on('pageerror', lambda e: errors.append(str(e)))
    pp.goto(FILE); pp.wait_for_timeout(2200)
    pe = pp.evaluate
    gp2 = pe("() => DB.projects.find(p => p.name === 'Garden planner').id")
    pe(f"""() => {{ const l = blankLeader({{ name: 'Talal' }}); DB.leaders.push(l); getProject('{gp2}').leader = l.id; FullView.open('{gp2}'); }}"""); pp.wait_for_timeout(600)
    ok('on a touch screen the milestone\'s + and Change show all the time', pe("() => getComputedStyle(document.querySelector('#pv .ms-plus')).opacity") == '1'
       and pe("() => getComputedStyle(document.querySelector('#pv .ld-change')).opacity") == '1')
    pe(f"() => FullView.openTask('{gp2}', getProject('{gp2}').todos[0].id)"); pp.wait_for_timeout(500)
    pp.tap('#pvTaskDue'); pp.wait_for_timeout(300)
    ok('Pick a date\'s calendar lies over its row for a finger to reach', pe("() => getComputedStyle(document.querySelector('#pvTaskDuePick')).pointerEvents") == 'auto')
    lst = pe("() => { const r = document.querySelector('#pvDueList').getBoundingClientRect(); return r.right <= innerWidth && r.left >= 0; }")
    ok('the list stays inside the screen', lst)
    ok('the description and the due date read at 16 px, as a phone\'s fields do', pe("() => getComputedStyle(document.querySelector('#pvTaskDescView')).fontSize") == '16px'
       and pe("() => getComputedStyle(document.querySelector('#pvTaskDue')).fontSize") == '16px')
    pp.screenshot(path=str(SHOTS / '524-ux-phone-panel.png'))
    b.close()
print(errors or 'no console errors')
