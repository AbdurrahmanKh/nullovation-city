"""Reports (Tasks, Round 2, P1 to P3): the side bar turns into Reports as it does into Settings, with tasks finished each
week and by project, the streak, the busiest building of the month and milestones finished. The weekly review, a third
tab at 0.1.43, was taken out at 0.1.44."""
import json
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# A fixed Monday noon for the sums, so they hold on any day the passes run: its week started on Saturday 17 October
MON = 'new Date(2026, 9, 19, 12).getTime()'
at = lambda y, m, d, hr=12: f'new Date({y}, {m - 1}, {d}, {hr}).getTime()'

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
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; }")
    toasted = lambda: ev("() => document.querySelector('#toast').classList.contains('show') ? document.querySelector('#toast').textContent : ''")

    # ---------- the counts, on made-up projects and a fixed day ----------
    # A, B: projects with a log and tasks. Every count is of ticks: Activity's Done lines.
    FAKE = f"""(() => {{
      const A = {{ name: 'Alpha', activity: [
          {{ at: {at(2026, 10, 19, 9)}, text: 'Done: Water' }}, {{ at: {at(2026, 10, 12, 9)}, text: 'Done: Water' }},
          {{ at: {at(2026, 10, 18, 9)}, text: 'Done: Paint' }}, {{ at: {at(2026, 10, 18, 10)}, text: 'Reopened: Paint' }},
          {{ at: {at(2026, 10, 17, 9)}, text: 'Claude Code finished: Paint' }}, {{ at: {at(2026, 10, 17, 9)}, text: 'Added todo: Paint' }},
          {{ at: {at(2026, 10, 16, 9)}, text: 'Done: Sand' }}, {{ at: {at(2026, 10, 15, 9)}, text: 'Removed todo: Dead one' }}],
        todos: [{{ text: 'Sand', done: true, doneAt: {at(2026, 10, 16, 9)} }}, {{ text: 'Old one', done: true, doneAt: {at(2026, 8, 3)} }},
          {{ text: 'Paint', done: false }}, {{ text: 'Water', done: false, repeat: {{ every: 'day', n: 7 }}, due: '2026-10-26', waiting: true }}],
        milestones: [] }};
      const B = {{ name: 'Beta', activity: [{{ at: {at(2026, 10, 18, 9)}, text: 'Done: One' }}, {{ at: {at(2026, 10, 18, 11)}, text: 'Done: Two' }}, {{ at: {at(2026, 9, 30)}, text: 'Done: Three' }}],
        todos: [], milestones: [] }};
      return [A, B];
    }})()"""
    ticks = ev(f"() => taskTicks({FAKE}, {MON}).map(e => e.p.name + ':' + e.text + ':' + e.day)")
    ok('P2 every Done line is a tick, a repeat each time it is ticked', ticks.count('Alpha:Water:2026-10-19') == 1 and ticks.count('Alpha:Water:2026-10-12') == 1)
    ok('a Reopened line takes its tick back', not any(t.startswith('Alpha:Paint') for t in ticks))
    ok('a done task counts once, by its Done line', ticks.count('Alpha:Sand:2026-10-16') == 1)
    ok('a done task whose Done line the log no longer holds counts on the day it was finished', 'Alpha:Old one:2026-08-03' in ticks)
    ok('Claude Code\'s finish lines, added and removed tasks never count', len([t for t in ticks if t.startswith('Alpha')]) == 4)
    ok('ticks come oldest first', ticks == sorted(ticks, key=lambda t: t.split(':')[-1]))
    wk = ev(f"() => weeklyTicks(taskTicks({FAKE}, {MON}), 12, {MON}).map(w => [ymd(w.start), w.n, w.current])")
    ok('P2 12 weeks, Saturday to Friday, oldest first, the last one this week so far',
       len(wk) == 12 and wk[-1] == ['2026-10-17', 3, True] and wk[-2] == ['2026-10-10', 2, False] and wk[0][0] == '2026-08-01' and not any(w[2] for w in wk[:-1]))
    ok('each week counts its ticks', [w[1] for w in wk] == [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 3])
    byp = ev(f"() => ticksByProject(taskTicks({FAKE}, {MON}), {at(2026, 10, 17, 0)}, {at(2026, 10, 24, 0)}).map(r => [r.p.name, r.n])")
    ok('P2 by project for a week, the most first', byp == [['Beta', 2], ['Alpha', 1]])
    bym = ev(f"() => ticksByProject(taskTicks({FAKE}, {MON}), monthStartOf({MON}), addMonths({MON}, 1)).map(r => [r.p.name, r.n])")
    ok('and for a month', bym == [['Alpha', 3], ['Beta', 2]])

    # the streak (P2, P3): days in a row with a tick
    streak = lambda days, now=MON, city="{ rest: [], awaySpans: [] }": ev(
        f"() => streakOf({json.dumps(days)}.map(d => ({{ day: d, at: parseYmd(d) }})), {now}, {city})")
    s = streak(['2026-10-16', '2026-10-17', '2026-10-18', '2026-10-19'])
    ok('P2 the streak counts days in a row with a tick, today included', s['n'] == 4 and s['from'] == '2026-10-16' and s['today'])
    s = streak(['2026-10-16', '2026-10-17', '2026-10-18'])
    ok('today, before its first tick, does not break it', s['n'] == 3 and not s['today'])
    s = streak(['2026-10-15', '2026-10-17', '2026-10-18'])
    ok('a day with no tick breaks it', s['n'] == 2 and s['from'] == '2026-10-17')
    s = streak(['2026-10-10', '2026-10-11', '2026-10-12', '2026-10-13', '2026-10-17', '2026-10-18'])
    ok('the longest, with its first and last day', s['best'] == {'n': 4, 'from': '2026-10-10', 'to': '2026-10-13'} and s['n'] == 2)
    s = streak(['2026-10-15', '2026-10-17', '2026-10-18'], city='{ rest: [5], awaySpans: [] }')
    ok('P3 a rest day with no tick never breaks it (Friday a rest day)', s['n'] == 3 and s['from'] == '2026-10-15')
    SAT = at(2026, 10, 17, 20)
    s = streak(['2026-10-15', '2026-10-16', '2026-10-17'], SAT, city='{ rest: [5], awaySpans: [] }')
    ok('P3 a tick on a rest day counts', s['n'] == 3)
    s = streak(['2026-10-12', '2026-10-17', '2026-10-18'], city="{ rest: [], awaySpans: [['2026-10-13', '2026-10-17']] }")
    ok('P3 days away never break it', s['n'] == 3 and s['from'] == '2026-10-12')
    s = streak(['2026-10-12', '2026-10-17'], SAT, city="{ rest: [], awaySpans: [['2026-10-13', '2026-10-16']] }")
    ok('the day you are back counts again', s['n'] == 1)
    s = streak([])
    ok('no ticks, no streak', s['n'] == 0 and s['best']['n'] == 0)
    s = streak(['2026-10-17', '2026-10-18'], city='{ rest: [1], awaySpans: [] }')
    ok('a day off today says so', s['off'] and s['n'] == 2)

    # the busiest building of each month, and milestones finished
    busy = ev(f"() => busiestByMonth(taskTicks({FAKE}, {MON}), 12, {MON}).map(m => [ymd(m.start), m.top.map(r => r.p.name), m.n])")
    ok('P2 the busiest building of the month, then each earlier month with a tick', busy[0] == ['2026-10-01', ['Alpha'], 3] and busy[1] == ['2026-09-01', ['Beta'], 1] and busy[2] == ['2026-08-01', ['Alpha'], 1])
    ok('months with no tick are left out', len(busy) == 3)
    tie = ev(f"() => busiestByMonth(taskTicks({FAKE}, {MON}).filter(e => ['2026-10-18', '2026-10-12', '2026-10-16'].includes(e.day)), 12, {MON})[0].top.map(r => r.p.name)")
    ok('buildings tied at the top share it', tie == ['Alpha', 'Beta'])
    ok('a month with nothing yet shows no building', ev(f"() => busiestByMonth([], 12, {MON})") == [{'start': ev(f"() => monthStartOf({MON})"), 'top': [], 'n': 0}])
    MS = f"""[{{ name: 'M', milestones: [{{ id: 'a', name: 'First' }}, {{ id: 'b', name: 'Second' }}, {{ id: 'c', name: 'Empty' }}, {{ id: 'd', name: 'With a repeat' }}],
      todos: [{{ milestoneId: 'a', done: true, doneAt: {at(2026, 9, 2)} }}, {{ milestoneId: 'a', done: true, doneAt: {at(2026, 9, 5)} }},
              {{ milestoneId: 'b', done: true, doneAt: {at(2026, 10, 1)} }}, {{ milestoneId: 'd', done: true, doneAt: {at(2026, 10, 2)} }}, {{ milestoneId: 'd', done: false, repeat: {{ every: 'day', n: 1 }} }}] }}]"""
    ms = ev(f"() => milestonesFinished({MS}).map(x => [x.m.name, ymd(x.at)])")
    ok('P2 milestones finished with their dates, the newest first', ms == [['Second', '2026-10-01'], ['First', '2026-09-05']])
    ok('an empty milestone, or one with a repeat in it, never finishes', len(ms) == 2)

    # ---------- the city: ticks over the weeks ----------
    ev("""() => {
      const now = Date.now(), D = 86400000, gp = DB.projects.find(p => p.name === 'Garden planner'), nc = DB.projects.find(p => p.name === 'Nullovation City');
      const add = (p, ago, text) => p.activity.push({ at: startOfDay(now) - ago * D + 10 * 3600000, text: 'Done: ' + text });
      for (let d = 1; d <= 60; d++) { if (d % 3 === 0) add(gp, d, 'Water the beds'); if (d % 5 === 0) add(nc, d, 'Draw block ' + d); }
      for (const d of [1, 2, 4]) add(gp, d, 'Weed ' + d);
      gp.activity.sort((a, b) => a.at - b.at); nc.activity.sort((a, b) => a.at - b.at);
      changed(gp); changed(nc);
    }""")

    # ---------- the panel (P1): a panel like Settings ----------
    ok('P1 a Reports button at the foot of the side bar, beside Settings', pg.is_visible('#btnOpenReports') and
       ev("() => { const a = document.querySelector('#btnOpenReports').getBoundingClientRect(), b = document.querySelector('#btnOpenSettings').getBoundingClientRect(); return Math.abs(a.top - b.top) < 2 && a.right < b.left; }"))
    ok('Settings stays at the very bottom', ev("() => innerHeight - document.querySelector('#btnOpenSettings').getBoundingClientRect().bottom") < 40)
    map0 = ev("() => document.querySelector('#map').getBoundingClientRect().width")
    pg.click('#btnOpenReports'); pg.wait_for_timeout(250)
    ok('P1 the side bar turns into Reports; the lists give way and the map stays in view at its size',
       pg.is_visible('#reports') and not pg.is_visible('#btnRecap') and ev("() => document.querySelector('#map').getBoundingClientRect().width") == map0)
    ok('its header: the back arrow and the title', pg.is_visible('#rpBack') and pg.text_content('.rp-title') == 'Reports')
    ok('two tabs, Weeks and Records, named; no Review since 0.1.44', ev("() => [...document.querySelectorAll('#rpTabs .set-tab')].map(b => b.textContent)") == ['Weeks', 'Records']
       and ev("() => ['reviewWeeks', 'overdueTasks', 'pickedTasks'].every(n => typeof window[n] === 'undefined')") and not pg.is_visible('.rv-task'))
    pg.click('.rp-tab[data-tab="weeks"]'); pg.wait_for_timeout(100)
    pg.focus('.rp-tab[data-tab="weeks"]'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(100)
    ok('the arrow keys move between the tabs', ev("() => Reports.tab()") == 'records' and ev("() => document.activeElement.dataset.tab") == 'records')
    pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(100)
    pg.click('#rpBack'); pg.wait_for_timeout(150)
    ok('the back arrow brings the lists back, with the focus on Reports', not pg.is_visible('#reports') and pg.is_visible('#btnRecap') and ev("() => document.activeElement.id") == 'btnOpenReports')
    pg.click('#map', position={'x': 700, 'y': 60}); pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    pg.keyboard.press('r'); pg.wait_for_timeout(200)
    ok('R opens Reports', pg.is_visible('#reports'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes them', not pg.is_visible('#reports'))
    pg.keyboard.press('r'); pg.wait_for_timeout(150); pg.keyboard.press('r'); pg.wait_for_timeout(150)
    ok('R again closes them', not pg.is_visible('#reports'))
    pg.focus('#search'); pg.keyboard.press('r'); pg.wait_for_timeout(150)
    ok('R in a field is only a letter', not pg.is_visible('#reports') and pg.input_value('#search') == 'r')
    pg.fill('#search', ''); pg.keyboard.press('Escape')
    pg.click('#btnOpenReports'); pg.wait_for_timeout(150); pg.click('#btnOpenSettings', force=True) if pg.is_visible('#btnOpenSettings') else ev("() => Settings.open()")
    pg.wait_for_timeout(150)
    ok('Settings and Reports share the side bar: opening Settings closes Reports', pg.is_visible('#settings') and not pg.is_visible('#reports'))
    ev("() => Reports.open()"); pg.wait_for_timeout(150)
    ok('and opening Reports closes Settings', pg.is_visible('#reports') and not pg.is_visible('#settings') and not pg.is_visible('#btnRecap'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('then Esc goes back to the lists', pg.is_visible('#btnRecap'))
    ev("() => Settings.open('city')"); pg.wait_for_timeout(100); pg.click('#setHelpBtn'); pg.wait_for_timeout(100)
    ok('the controls guide names R', 'R opens and closes them' in pg.text_content('#setHelp'))
    pg.click('#setHelpBtn'); ev("() => Settings.close()"); pg.wait_for_timeout(100)

    # ---------- Weeks ----------
    ev("() => Reports.open('weeks')"); pg.wait_for_timeout(200)
    want = ev("() => weeklyTicks(taskTicks()).map(w => w.n)")
    bars = ev("() => [...document.querySelectorAll('.rp-bar')].map(b => b.querySelector('b').textContent || '0').map(Number)")
    ok('P2 twelve bars, one a week, each with its count', len(bars) == 12 and bars == want and sum(want) > 10)
    ok('this week\'s bar is the last, marked as so far', ev("() => [...document.querySelectorAll('.rp-bar')].map(b => b.classList.contains('now')).lastIndexOf(true)") == 11
       and 'so far' in pg.get_attribute('.rp-bar >> nth=11', 'aria-label'))
    hts = ev("() => [...document.querySelectorAll('.rp-bar i')].map(i => i.getBoundingClientRect().height)")
    ok('the tallest week is the tallest bar', hts.index(max(hts)) == want.index(max(want)))
    ok('the sum line: this week so far, and the last 12 weeks', f'The last 12 weeks: {sum(want)}' in pg.text_content('#rpWeeksSum'))
    ok('By project opens on this week, its bar pressed', 'this week' in pg.text_content('#rpPeriod') and pg.get_attribute('.rp-bar >> nth=11', 'aria-pressed') == 'true')
    pg.locator('#menu').screenshot(path=str(SHOTS / '290-reports-weeks.png'))
    pg.click('.rp-bar >> nth=10'); pg.wait_for_timeout(150)
    lastweek = ev("() => { const s = addDays(weekStartOf(Date.now()), -7); return ticksByProject(taskTicks(), s, addDays(s, 7)).map(r => r.p.name + ' ' + r.n); }")
    rows = ev("() => [...document.querySelectorAll('#rpByProject .rp-row')].map(r => r.querySelector('.rp-name').textContent + ' ' + r.querySelector('.rp-n').textContent)")
    ok('a bar picks its week for By project', pg.get_attribute('.rp-bar >> nth=10', 'aria-pressed') == 'true' and 'this week' not in pg.text_content('#rpPeriod') and rows == lastweek and len(rows) >= 1)
    ok('the focus stays on the bar picked', ev("() => document.activeElement.classList.contains('rp-bar') && document.activeElement.getAttribute('aria-pressed') === 'true'"))
    pg.click('[data-k="next"]'); pg.wait_for_timeout(100)
    ok('the arrows step a week; on this week the one after is off', 'this week' in pg.text_content('#rpPeriod') and pg.is_disabled('[data-k="next"]'))
    pg.click('[data-k="kind-month"]'); pg.wait_for_timeout(100)
    mrows = ev("() => [...document.querySelectorAll('#rpByProject .rp-row .rp-n')].map(r => +r.textContent)")
    ok('Month shows this month by project, the most first', 'this month' in pg.text_content('#rpPeriod') and mrows == sorted(mrows, reverse=True) and
       sum(mrows) == ev("() => taskTicks().filter(e => e.at >= monthStartOf(Date.now())).length"))
    ok('no bar is pressed while a month shows', ev("() => [...document.querySelectorAll('.rp-bar')].every(b => b.getAttribute('aria-pressed') === 'false')"))
    pg.click('[data-k="prev"]'); pg.wait_for_timeout(100)
    ok('the month before', pg.text_content('#rpPeriod') == ev("() => monthLabel(addMonths(Date.now(), -1))"))
    for _ in range(4):
        if not pg.is_disabled('[data-k="prev"]'): pg.click('[data-k="prev"]'); pg.wait_for_timeout(60)
    ok('the arrows go back no further than the first month with a tick', pg.is_disabled('[data-k="prev"]'))
    pg.click('[data-k="kind-week"]'); pg.wait_for_timeout(100)
    ok('back to Week opens this week again', 'this week' in pg.text_content('#rpPeriod'))
    first = ev("() => document.querySelector('#rpByProject .rp-name').textContent")
    pg.click('#rpByProject .rp-row >> nth=0'); pg.wait_for_timeout(200)
    ok('a project row shows its building on the map', ev("() => App.selectedId && getProject(App.selectedId).name") == first)
    ev("() => MapView.deselect()")

    # ---------- Records ----------
    ev("() => Reports.showTab('records')"); pg.wait_for_timeout(150)
    st = ev("() => streakOf(taskTicks())")
    ok('P2 the streak, in days, with what today does', pg.text_content('#rpStreak .rp-big') == (f"{st['n']} day" + ('' if st['n'] == 1 else 's')) and
       ('Finish a task today' in pg.text_content('#rpToday') or 'counts already' in pg.text_content('#rpToday') or 'day off' in pg.text_content('#rpToday')))
    ok('and its longest, with its days', pg.text_content('#rpLongest').startswith('Longest: ' + str(st['best']['n']) + ' day'))
    ok('P3 says rest days and days away never break it', 'Rest days and days away never break it' in pg.text_content('#reports'))
    top = ev("() => busiestByMonth(taskTicks())[0].top.map(r => r.p.name).join(' and ')")
    ok('P2 the busiest building of the month, with its building', pg.text_content('#rpBusiest .rp-busy-name') == top and pg.is_visible('#rpBusiest canvas.thumb'))
    ok('and the months before it', ev("() => document.querySelectorAll('#rpMonths li').length") == ev("() => busiestByMonth(taskTicks()).length - 1") >= 1)
    ok('no milestone finished yet says so', pg.text_content('#rpMilestones') == 'No milestone finished yet.')
    ev(f"""() => {{ const p = getProject('{nc}'); const D = 86400000;
      for (let k = 0; k < 10; k++) {{ const m = {{ id: 'm_r' + k, name: 'Stage ' + k, collapsed: false }}; p.milestones.push(m);
        p.todos.push({{ id: 't_r' + k, text: 'Finish stage ' + k, description: '', done: true, doneAt: Date.now() - (k + 1) * D, due: '', milestoneId: m.id }}); }}
      changed(p); }}""")
    pg.wait_for_timeout(150)
    names = ev("() => [...document.querySelectorAll('#rpMilestones li .rp-what')].map(b => b.firstChild.textContent)")
    ok('P2 milestones finished, newest first, with their dates and projects', names[:3] == ['Stage 0', 'Stage 1', 'Stage 2'] and
       ev("() => document.querySelector('#rpMilestones li .rp-date').textContent") == ev("() => fmtDate(Date.now() - 86400000)") and 'Nullovation City' in pg.text_content('#rpMilestones'))
    ok('8 show, then Show all', len(names) == 8 and pg.text_content('[data-k="ms-more"]') == 'Show all 10')
    pg.click('[data-k="ms-more"]'); pg.wait_for_timeout(100)
    ok('Show all shows every one', ev("() => document.querySelectorAll('#rpMilestones li').length") == 10)
    pg.locator('#menu').screenshot(path=str(SHOTS / '291-reports-records.png'))
    pg.click('#rpMilestones li .rp-what >> nth=0'); pg.wait_for_timeout(300)
    ok('a milestone opens its project', ev("() => FullView.isOpen() && FullView.currentId()") == nc)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # a change elsewhere redraws the open tab; the tab is kept after a reload; nothing new is saved
    ev("() => Reports.showTab('weeks')"); pg.wait_for_timeout(100)
    before = ev("() => document.querySelector('.rp-bar:last-child b').textContent")
    ev(f"() => {{ const p = getProject('{gp}'), t = openTasks(p)[0]; tickTask(p, t); changed(p); }}"); pg.wait_for_timeout(150)
    after = ev("() => document.querySelector('.rp-bar:last-child b').textContent")
    ok('a tick on the map shows in the open report at once', int(after or 0) == int(before or 0) + 1)
    ev("() => persistSoon.flush()")
    ok('nothing new in the data: Reports keep only their tab and Week or Month in this browser',
       ev("() => Object.keys(JSON.parse(localStorage.getItem('nullovation-city:v1'))).sort().join()") == 'app,city,leaders,projects,version,world' and
       ev("() => Object.keys(DB.city).some(k => /report|review|streak/i.test(k))") is False and
       ev("() => Object.keys(JSON.parse(localStorage.getItem('nullovation-city:reports'))).sort().join()") == 'period,tab')
    pg.reload(); pg.wait_for_timeout(2000)
    ok('Reports stays closed after a reload, and opens on the tab last used', not pg.is_visible('#reports') and (ev("() => { Reports.open(); return Reports.tab(); }") == 'weeks'))
    ev("() => { Reports.showTab('records'); Reports.close(false); localStorage.setItem('nullovation-city:reports', JSON.stringify({ tab: 'review', period: 'week' })); }")
    pg.reload(); pg.wait_for_timeout(2000)
    ok('a browser last left on the Review tab of 0.1.43 opens on Weeks', ev("() => { Reports.open(); return Reports.tab(); }") == 'weeks' and pg.is_visible('.rp-chart'))

    # a narrow window: Reports in the drawer
    pg.set_viewport_size({'width': 700, 'height': 800}); pg.wait_for_timeout(200)
    ev("() => Reports.close(false)"); ev("() => Menu.closeDrawer()"); pg.wait_for_timeout(150)
    pg.keyboard.press('r'); pg.wait_for_timeout(300)
    ok('on a narrow window, R opens the drawer on Reports', pg.is_visible('#reports') and ev("() => document.querySelector('#menu').classList.contains('open')"))
    wide = ev("() => [...document.querySelectorAll('#reports *')].filter(e => e.getBoundingClientRect().right > document.querySelector('#menu').getBoundingClientRect().right + 1).map(e => e.className).slice(0, 3)")
    ok('nothing in Reports runs past the side bar', wide == [])
    b.close()
print(errors or 'no console errors')
