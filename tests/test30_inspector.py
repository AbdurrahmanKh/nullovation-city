"""Proxima Pace, Productivity Inspector (Productivity Inspector, Rounds 1 and 2): her card at the top of Reports, her
daily, weekly and monthly reports, what each holds (L1), her facts (L2), her lines (V2) word for word, and her speech
bubble, which brings the weekly and monthly reports after Gus (J3)."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY, FACE_OF, PORTRAIT_SUM, portrait_sum

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# A fixed Monday noon, so the reports hold on any day the passes run: yesterday is Sunday 18 October, the last full
# week Saturday 10 to Friday 16 October, the last month September
MON = 'new Date(2026, 9, 19, 12).getTime()'
at = lambda m, d, hr=10: f'new Date(2026, {m - 1}, {d}, {hr}).getTime()'

LINES = {
    'week': ['Weekly report inbound! {n} tasks landed this week.', "Copy that, week logged: {n} tasks done. Report's ready."],
    'week0': ['Quiet week: no tasks landed. Next week holds {due} due.'],
    'month': ['Monthly report on deck! {n} tasks in {month}.', "{month} is logged: {n} tasks, {m} milestones. Report's ready."],
    'day': ["Yesterday: {n} tasks landed. Today's flight plan: {due} due."],
    'one_left': ["{milestone} is one task from done: {task}. Let's land it!"],
    'empty_week': ["Next week's flight plan is empty. Nothing due yet."],
    'repeat_run': ['{repeat}: ticked {k} weeks running. Steady hands!'],
    'milestone': ["Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!",          # Celebrations, Round 2 (0.1.46)
                  "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!"],
}

# The city on the fixed Monday. Garden planner waters its beds every week from 5 September; Nullovation City finishes
# two Block art tasks and the one task of a new milestone, Ground, in the week of 10 October.
FIXTURE = f"""() => {{
  const gp = DB.projects.find(p => p.name === 'Garden planner'), nc = DB.projects.find(p => p.name === 'Nullovation City');
  DB.city.rest = []; DB.city.awaySpans = [];
  for (const p of [gp, nc]) {{ p.activity = []; p.createdAt = {at(8, 1)}; }}
  const done = (p, when, text) => p.activity.push({{ at: when, text: 'Done: ' + text }});
  for (const d of [[9, 5], [9, 12], [9, 19], [9, 26], [10, 3], [10, 6], [10, 10], [10, 12], [10, 14]]) done(gp, new Date(2026, d[0] - 1, d[1], 10).getTime(), 'Water the beds');
  done(gp, {at(10, 15)}, 'Weed the beds'); done(gp, {at(10, 18)}, 'Weed the paths'); done(gp, {at(8, 20)}, 'Buy seeds');
  done(nc, {at(10, 8)}, 'Draw block 8');
  const t = text => nc.todos.find(x => x.text === text) || gp.todos.find(x => x.text === text);
  Object.assign(t('Round 3: decide the block art loop'), {{ done: true, doneAt: {at(10, 12)} }}); done(nc, {at(10, 12)}, 'Round 3: decide the block art loop');
  Object.assign(t('Build the block art skill'), {{ done: true, doneAt: {at(10, 13)} }}); done(nc, {at(10, 13)}, 'Build the block art skill');
  nc.milestones.push({{ id: 'm_ground', name: 'Ground' }});
  nc.todos.push({{ id: 't_ground', text: 'Level the ground', done: true, doneAt: {at(10, 14)}, milestoneId: 'm_ground', createdAt: {at(10, 1)} }});
  done(nc, {at(10, 14)}, 'Level the ground');
  t('Try the project view for a week').due = '2026-10-19';
  t('Draw the beds on a grid').due = '2026-10-21';
  t('Save a plan as a file').due = '2026-10-15';
  t('Publish the app').due = '2026-10-30';
  gp.todos.push({{ id: 't_water', text: 'Water the beds', done: false, repeat: {{ every: 'week', days: [4] }}, due: '2026-10-22', waiting: true, milestoneId: null, createdAt: {at(9, 1)} }});
  gp.notes.push({{ id: 'n_soil', title: 'Soil', text: 'The beds need more compost.', at: {at(9, 9)} }});
}}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')

    # ---------- her reports, on the fixed Monday ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    ok('V2 her lines, word for word as approved', ev("() => PROXIMA_LINES") == LINES)
    per = ev(f"() => PROXIMA_KINDS.map(k => {{ const x = proximaPeriod(k, {MON}); return [k, ymd(x.from), ymd(x.to), ymd(x.prev), ymd(x.next), x.key]; }})")
    ok('the daily report is on yesterday, looking ahead to today', per[0] == ['daily', '2026-10-18', '2026-10-19', '2026-10-17', '2026-10-20', '2026-10-18'])
    ok('the weekly one on the last full week, Saturday to Friday, looking ahead to this week', per[1] == ['weekly', '2026-10-10', '2026-10-17', '2026-10-03', '2026-10-24', '2026-10-10'])
    ok('the monthly one on the last month, looking ahead to this one', per[2] == ['monthly', '2026-09-01', '2026-10-01', '2026-08-01', '2026-11-01', '2026-09'])
    ok('a count of one reads in the singular', ev("() => proximaFill(PROXIMA_LINES.day[0], { n: 1, due: 2 })") == "Yesterday: 1 task landed. Today's flight plan: 2 due."
       and ev("() => proximaFill(PROXIMA_LINES.repeat_run[0], { repeat: 'Stretch', k: 1 })") == 'Stretch: ticked 1 week running. Steady hands!')

    ev(FIXTURE)
    R = lambda kind, now=MON: ev(f"""() => {{ const r = Proxima.report('{kind}', {now});
      const nm = x => x.p.name + ':' + (x.t ? x.t.text : x.m ? x.m.name : x.n ? x.n.title : '');
      return {{ line: r.line, label: r.label, n: r.n, before: r.before, streak: [r.streak.n, r.streak.best.n], ms: r.milestones.map(x => x.m.name), due: r.due.map(nm), facts: r.facts,
        buildings: (r.buildings || []).map(b => [b.p.name, b.n]), busiest: (r.busiest || []).map(b => b.p.name), quiet: (r.quiet || []).map(p => p.name),
        overdue: (r.overdue || []).map(nm), repeats: (r.repeats || []).map(x => [x.t.text, x.k]), notes: (r.notes || []).map(nm), has: Object.keys(r) }}; }}""")
    d, w, m = R('daily'), R('weekly'), R('monthly')
    ONE = "Block art is one task from done: Make block art for each project. Let's land it!"
    RUN = 'Water the beds: ticked 6 weeks running. Steady hands!'
    ok('L1 every report: tasks finished against the period before', (d['n'], d['before']) == (1, 0) and (w['n'], w['before']) == (7, 3) and (m['n'], m['before']) == (4, 1))
    ok('L1 every report: the streak and the longest (rest days and days away as in Reports)', d['streak'] == [1, 4] and w['streak'] == [1, 4])
    ok('L1 every report: milestones finished in its period', w['ms'] == ['Ground'] and d['ms'] == [] and m['ms'] == [])
    ok('L1 every report: what is due ahead, from today on; a repeat coming back in it counts; what is late is not in it',
       d['due'] == ['Nullovation City:Try the project view for a week'] and
       w['due'] == ['Nullovation City:Try the project view for a week', 'Garden planner:Draw the beds on a grid', 'Garden planner:Water the beds'] and
       m['due'] == w['due'] + ['Garden planner:Publish the app'])
    ok('L1 the daily report holds no buildings, overdue, repeats or notes', not any(k in d['has'] for k in ('buildings', 'busiest', 'quiet', 'overdue', 'repeats', 'notes')))
    ok('L1 weekly and monthly: by building, the most first, and the busiest', w['buildings'] == [['Garden planner', 4], ['Nullovation City', 3]] and w['busiest'] == ['Garden planner']
       and m['buildings'] == [['Garden planner', 4]])
    ok('L1 weekly and monthly: buildings with open tasks and nothing finished', w['quiet'] == [] and m['quiet'] == ['Nullovation City'])
    ok('L1 weekly and monthly: the overdue tasks, the oldest first', w['overdue'] == ['Garden planner:Save a plan as a file'] and m['overdue'] == w['overdue'])
    ok('L1 monthly only: repeats ticked and notes written', m['repeats'] == [['Water the beds', 4]] and m['notes'] == ['Garden planner:Soil'] and 'repeats' not in w['has'])
    ok('L2 a milestone one task from done, in every report', all(ONE in r['facts'] for r in (d, w, m)))
    ok('L2 a repeat kept up, weekly and monthly, with the weeks in a row', RUN in w['facts'] and RUN in m['facts'] and RUN not in d['facts'])
    ok('L2 next week empty only when nothing is due in it', LINES['empty_week'][0] not in w['facts'])
    ok('V2 the daily line', d['line'] == "Yesterday: 1 task landed. Today's flight plan: 1 due.")
    ok('V2 the weekly line, one of the two, filled', w['line'] in ('Weekly report inbound! 7 tasks landed this week.', "Copy that, week logged: 7 tasks done. Report's ready."))
    ok('V2 the monthly line, one of the two, filled', m['line'] in ('Monthly report on deck! 4 tasks in September.', "September is logged: 4 tasks, 0 milestones. Report's ready."))
    ok('the same report always gets the same line', all(R('weekly')['line'] == w['line'] for _ in range(3)))
    ok('the labels: the day, the week, the month', (d['label'], w['label'], m['label']) == ('Sun 18 Oct', '10 Oct to 16 Oct', 'September'))
    # a quiet week and month: 25 July to 31 July, and July
    q = R('weekly', 'new Date(2026, 7, 3, 12).getTime()')
    ok('V2 a quiet week', q['n'] == 0 and q['line'] == 'Quiet week: no tasks landed. Next week holds 0 due.')
    ok('L2 next week empty: said in the weekly report', LINES['empty_week'][0] in q['facts'])
    q = R('monthly', 'new Date(2026, 7, 5, 12).getTime()')
    ok('V2 a quiet month', q['line'] == "July is logged: 0 tasks, 0 milestones. Report's ready.")
    ok('a report on a period that ended before the city started is not given', ev(f"() => proximaRelevant(proximaPeriod('monthly', {MON}))")
       and not ev("() => proximaRelevant(proximaPeriod('monthly', new Date(2026, 7, 5, 12).getTime()))"))
    ok('a repeat ticked less than 3 weeks running is not a run', ev(f"() => repeatRuns(taskTicks(DB.projects, new Date(2026, 8, 21, 12).getTime()), new Date(2026, 8, 21, 12).getTime()).length") == 0)
    ok('a milestone with a repeat in it, or a single task, is never one task from done',
       ev("() => milestonesOneLeft().map(x => x.m.name)") == ['Block art'])
    ctx.close()

    # ---------- her card, her reports and her bubble, today ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    ok('a new city: nothing to report yet, no dot, no bubble', not ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')") and not pg.is_visible('#pxSay'))
    pg.click('#btnOpenReports'); pg.wait_for_timeout(200)
    ok('J1 her card at the top of Reports, above the tabs', pg.is_visible('#pxCard') and
       ev("() => document.querySelector('#pxCard').getBoundingClientRect().bottom <= document.querySelector('#rpTabs').getBoundingClientRect().top"))
    ok('her name and title, and her face', pg.text_content('#pxCard .px-name b') == 'Proxima Pace' and pg.text_content('#pxCard .px-name span') == 'Productivity Inspector'
       and ev("() => document.querySelector('#pxCard .px-face img').naturalWidth") == 256)
    # her face: her portrait (0.1.48)
    px = ev("() => PORTRAITS.proxima")
    ok('the page carries her portrait as a PNG', isinstance(px, str) and px.startswith('data:image/png;base64,'))
    ok('it decodes pixel for pixel, every pixel solid or see-through', ev(PORTRAIT_SUM, px) == portrait_sum('proxima'))
    f = ev(FACE_OF, '#pxCard .px-head')
    ok(f'on her card: her portrait, 256 px, shown at 64 by 64 and filling its frame ({f and {k: f[k] for k in ("nat", "w", "h", "fw", "fh")}})',
       f and f['url'] == px and f['imgs'] == 1 and f['nat'] == [256, 256] and f['w'] == f['h'] == f['fw'] == f['fh'] == 64)
    ok('shrunk smooth, as the map shrinks its buildings, on her dark sky blue', f['smooth'] and f['bg'] == 'rgb(31, 53, 80)')
    ok('with nothing to report: her first report comes tomorrow', pg.text_content('#pxLine') == 'Her first report comes tomorrow.' and not pg.is_visible('#pxReports'))
    pg.click('#rpBack'); pg.wait_for_timeout(100)

    # the city's history: ticks over 60 days, a task due today, one late, a repeat
    ev("""() => {
      const now = Date.now(), D = 86400000, gp = DB.projects.find(p => p.name === 'Garden planner'), nc = DB.projects.find(p => p.name === 'Nullovation City');
      const add = (p, ago, text) => p.activity.push({ at: startOfDay(now) - ago * D + 10 * 3600000, text: 'Done: ' + text });
      for (let d = 1; d <= 60; d++) { if (d % 3 === 0) add(gp, d, 'Water the beds'); if (d % 5 === 0) add(nc, d, 'Draw block ' + d); }
      for (const d of [1, 2, 4]) add(gp, d, 'Weed ' + d);
      gp.activity.sort((a, b) => a.at - b.at); nc.activity.sort((a, b) => a.at - b.at);
      gp.createdAt = nc.createdAt = now - 70 * D;
      gp.todos[1].due = ymd(now - 3 * D); nc.todos[3].due = ymd(now); gp.todos[0].due = ymd(now + 2 * D);
      gp.todos.push({ id: 't_water', text: 'Water the beds', done: false, repeat: { every: 'day', n: 3 }, due: ymd(now + D), waiting: true, milestoneId: null, createdAt: now - 70 * D });
      changed(gp); changed(nc);
    }""")
    pg.wait_for_timeout(150)
    ok('the Reports button wears a dot while a report waits unread', ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')")
       and 'Proxima has a report' in pg.get_attribute('#btnOpenReports', 'title'))
    ev("() => Proxima._test.sayMs(60000); Proxima.check()"); pg.wait_for_timeout(300)
    ok('J3 she brings the weekly report herself, in her bubble', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'weekly'
       and pg.text_content('#pxSayText') == ev("() => Proxima.report('weekly').line") and pg.text_content('#pxSay .px-name b') == 'Proxima Pace')
    ok('the monthly one waits its turn; the daily one never speaks', ev("() => Proxima._test.queue()") == ['monthly'])
    f = ev(FACE_OF, '#pxSayFace')
    ok(f'in her speech bubble: her portrait, bigger, 80 by 80, on her dark sky blue ({f and {k: f[k] for k in ("w", "h", "fw")}})',
       f and f['url'] == px and f['imgs'] == 1 and f['w'] == f['h'] == f['fw'] == 80 and f['smooth'] and f['bg'] == 'rgb(31, 53, 80)')
    pg.screenshot(path=str(SHOTS / '300-proxima-says.png'), clip={'x': 290, 'y': 0, 'width': 620, 'height': 200})
    ok('she says each report once', ev("() => Proxima._test.state().spoke.weekly") == ev("() => proximaPeriod('weekly').key"))
    # Gus cuts in: she gives way, and says it again after him
    ev("() => { window._gusSays = Gus.isSaying; Gus.isSaying = () => true; Proxima.yieldToGus(); }"); pg.wait_for_timeout(200)
    ok('never both at once: when Gus speaks, her bubble goes', not pg.is_visible('#pxSay') and ev("() => Proxima._test.queue()") == ['weekly', 'monthly'])
    pg.wait_for_timeout(700)
    ok('and she waits while he speaks', not pg.is_visible('#pxSay'))
    ev("() => { Gus.isSaying = window._gusSays; }"); pg.wait_for_timeout(800)
    ok('then she says hers', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'weekly')
    # Read: Reports open, with the report
    pg.click('#pxSayRead'); pg.wait_for_timeout(300)
    ok('Read opens Reports and the weekly report', pg.is_visible('#reports') and ev("() => Panel.isOpen()") and pg.text_content('#pnTitle') == 'Weekly report' and not pg.is_visible('#pxSay'))
    ok('the report opens with her line, then the week', pg.text_content('#pxReportLine') == ev("() => Proxima.report('weekly').line")
       and pg.text_content('.px-when') == ev("() => weekLabel(proximaPeriod('weekly').from)"))
    heads = ev("() => [...document.querySelectorAll('.px-report .px-sec h4')].map(h => h.textContent)")
    ok('L1 the weekly report: finished, streak, milestones, by building, the busiest, overdue, this week, and her facts',
       heads[:4] == ['Tasks finished', 'Streak', 'Milestones finished', 'By building'] and 'Busiest building' in heads and 'Overdue' in heads and 'This week' in heads
       and 'Repeats kept up' not in heads and 'Notes written' not in heads)
    ok('finished against the week before, in numbers', ev("() => { const r = Proxima.report('weekly'); return document.querySelector('#pxFinished').textContent.startsWith(r.n + ', '); }"))
    ok('the overdue task to close first', 'Close this one first' in pg.text_content('#pxOverdue') and pg.is_visible('.px-report .recap-day.late'))
    f = ev(FACE_OF, '.px-says')
    ok(f'the report opens with her portrait at 64 by 64 ({f and {k: f[k] for k in ("w", "h")}})', f and f['url'] == px and f['imgs'] == 1 and f['w'] == f['h'] == 64)
    pg.screenshot(path=str(SHOTS / '301-proxima-weekly.png'))
    ok('the next report waits while one is open', not pg.is_visible('#pxSay'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
    ok('read: no dot on the weekly report', not ev("() => document.querySelector('[data-k=px-weekly]').classList.contains('new')"))
    ok('then she brings the monthly one', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'monthly')
    pg.click('#pxSayClose'); pg.wait_for_timeout(200)
    ok('the close button sends her bubble away', not pg.is_visible('#pxSay') and ev("() => Proxima._test.queue()") == [])
    ok('closed unread, the monthly report keeps its dot', ev("() => document.querySelector('[data-k=px-monthly]').classList.contains('new')"))
    rows = ev("() => [...document.querySelectorAll('#pxReports .px-report-row')].map(b => [b.dataset.kind, b.querySelector('.px-report-kind').textContent])")
    ok('J1 three reports on her card: daily, weekly, monthly', rows == [['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly']])
    pg.screenshot(path=str(SHOTS / '302-proxima-card.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 420})
    pg.click('[data-k=px-monthly]'); pg.wait_for_timeout(250)
    heads = ev("() => [...document.querySelectorAll('.px-report .px-sec h4')].map(h => h.textContent)")
    ok('L1 the monthly report adds repeats and notes', pg.text_content('#pnTitle') == 'Monthly report' and 'Repeats kept up' in heads and 'Notes written' in heads and 'This month' in heads)
    pg.screenshot(path=str(SHOTS / '303-proxima-monthly.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click('[data-k=px-daily]'); pg.wait_for_timeout(250)
    heads = ev("() => [...document.querySelectorAll('.px-report .px-sec h4')].map(h => h.textContent)")
    ok('L1 the daily report: finished, streak, milestones and today', pg.text_content('#pnTitle') == 'Daily report' and heads[:3] == ['Tasks finished', 'Streak', 'Milestones finished']
       and heads[3] == 'Today' and 'By building' not in heads and 'Overdue' not in heads)
    ok('today, the task due today', 'Try the project view for a week' in pg.text_content('.px-report'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('every report read: no dots, none on the Reports button', ev("() => document.querySelectorAll('#pxReports .new').length") == 0
       and not ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')"))
    ok('Esc closed the report and left Reports open', pg.is_visible('#reports') and not ev("() => Panel.isOpen()"))
    # a link in a report goes to its building
    pg.click('[data-k=px-weekly]'); pg.wait_for_timeout(250)
    top = pg.text_content('.px-report .px-sec:nth-of-type(4) .px-link >> nth=0')
    pg.click('.px-report .px-sec:nth-of-type(4) .px-link >> nth=0'); pg.wait_for_timeout(300)
    ok('a building in a report goes to it on the map', not ev("() => Panel.isOpen()") and ev("() => App.selectedId") == ev(f"() => DB.projects.find(p => p.name === {json.dumps(top)}).id")
       and pg.is_visible('#bubble'))

    # a reload: what was read and said is kept
    pg.reload(); pg.wait_for_timeout(2200)
    ok('after a reload she says nothing again, and nothing is unread', not pg.is_visible('#pxSay') and not ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')"))
    # a fresh visit to the same city: she brings both, after Gus
    ev("() => Proxima._test.forget()")
    pg.reload(); pg.wait_for_timeout(2400)
    ok('on the first open after a week and a month end, she brings the weekly report first', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'weekly')
    ev("() => Proxima._test.sayMs(300)"); ev("() => Proxima.hush()"); pg.wait_for_timeout(1200)
    ok('her bubble goes by itself after a while', not pg.is_visible('#pxSay') and ev("() => Proxima.saying()") is None)
    ok('the daily report waits in Reports, unread', ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')"))

    # a narrow window: her card in the drawer
    pg.set_viewport_size({'width': 700, 'height': 800}); pg.wait_for_timeout(200)
    pg.keyboard.press('r'); pg.wait_for_timeout(300)
    ok('on a narrow window, her card shows in the drawer', pg.is_visible('#pxCard') and ev("() => document.querySelector('#pxCard').getBoundingClientRect().right") <= 700)
    pg.screenshot(path=str(SHOTS / '304-proxima-narrow.png'))
    ctx.close()

    ok('no console errors', not errors)
    if errors: print('\n'.join(errors[:10]))
    b.close()
