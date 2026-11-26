"""Proxima Pace, Productivity Inspector (Productivity Inspector, Rounds 1 and 2), and her reports as Proxima Reports,
Round 1 rethought them (0.1.83): one weekly report in place of two, which the side bar's This week card opens on the week
so far; a monthly one laid out the same; a daily one, a morning brief on today, which she brings herself; her line with
its numbers as tokens; the table of the buildings, a row opening on what it finished, and since 0.1.84 the quiet ones
folded into one line; and her speech bubble, after Gus. Since 0.1.96 (One Leader Card) her reports wait in News with her
face and open from it, in her card, a page each; her x marks one heard, Minimize leaves them waiting."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY, FACE_OF, PORTRAIT_SUM, portrait_sum

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# A fixed Monday noon, so the reports hold on any day the passes run: today is Monday 19 October, the last full week
# Saturday 10 to Friday 16 October, the week in progress from Saturday 17 October, the last month September
MON = 'new Date(2026, 9, 19, 12).getTime()'
at = lambda m, d, hr=10: f'new Date(2026, {m - 1}, {d}, {hr}).getTime()'

PARTY = ["Milestone landed! {milestone}: {n} tasks done in {project}. Street party's on!",          # Celebrations, Round 2 (0.1.46)
         "Copy that, {milestone} is logged: {n} for {n} in {project}. The block's dancing!"]

# The city on the fixed Monday, from 1 August. Garden planner waters its beds every week from 5 September; Nullovation
# City finishes two Block art tasks and the one task of a new milestone, Ground, in the week of 10 October.
FIXTURE = f"""() => {{
  const gp = DB.projects.find(p => p.name === 'Garden planner'), nc = DB.projects.find(p => p.name === 'Nullovation City');
  DB.city.rest = []; DB.city.awaySpans = [];
  for (const p of [gp, nc]) {{ p.activity = []; p.createdAt = {at(8, 1)}; }}
  const done = (p, when, text) => p.activity.push({{ at: when, text: 'Done: ' + text }});
  for (const d of [[9, 5], [9, 12], [9, 19], [9, 26], [10, 3], [10, 6], [10, 10], [10, 12], [10, 14]]) done(gp, new Date(2026, d[0] - 1, d[1], 10).getTime(), 'Water the beds');
  done(gp, {at(10, 15)}, 'Weed the beds'); done(gp, {at(10, 18)}, 'Weed the paths'); done(gp, {at(8, 20)}, 'Buy seeds');
  gp.activity.push({{ at: {at(10, 11)}, text: 'Added todo: Weed the beds' }}, {{ at: {at(10, 11, 11)}, text: 'Added todo: Weed the paths' }});
  done(nc, {at(10, 8)}, 'Draw block 8');
  nc.activity.push({{ at: {at(10, 11)}, text: 'I worked!' }});
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
  gp.notes.push({{ id: 'n_soil', title: 'Soil', text: 'The beds need more compost.', at: {at(10, 12)} }});
  for (const p of [gp, nc]) p.activity.sort((a, b) => a.at - b.at);
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
    ok('her two lines for a street party stay word for word as approved', ev("() => PROXIMA_LINES.milestone") == PARTY)
    ok('the facts are gone (A1: cut), and so is the busiest building', ev("() => ['one_left', 'empty_week', 'repeat_run', 'week', 'week0', 'day'].every(k => !(k in PROXIMA_LINES))")
       and ev("() => typeof milestonesOneLeft === 'undefined' && typeof repeatRuns === 'undefined'"))
    per = ev(f"""() => [proximaPeriod('daily', {MON}), proximaPeriod('weekly', {MON}), proximaPeriod('monthly', {MON}), proximaPeriod('weekly', {MON}, weekStartOf({MON})),
      proximaPeriod('weekly', {MON}, new Date(2026, 9, 5).getTime()), proximaPeriod('monthly', {MON}, {MON})]
      .map(x => [x.kind, ymd(x.from), ymd(x.to), x.key, x.live, x.latest])""")
    ok(f'C1 the daily report is on today ({per[0]})', per[0] == ['daily', '2026-10-19', '2026-10-20', '2026-10-19', True, True])
    ok('the weekly one, by default, on the last full week, Saturday to Friday', per[1] == ['weekly', '2026-10-10', '2026-10-17', '2026-10-10', False, True])
    ok('the monthly one, by default, on the last month', per[2] == ['monthly', '2026-09-01', '2026-10-01', '2026-09', False, True])
    ok('the week in progress, live', per[3] == ['weekly', '2026-10-17', '2026-10-24', '2026-10-17', True, True])
    ok('any week, from a day in it; an older one does not reach today', per[4] == ['weekly', '2026-10-03', '2026-10-10', '2026-10-03', False, False])
    ok('the month in progress, live (C2: arrows back to any month)', per[5] == ['monthly', '2026-10-01', '2026-11-01', '2026-10', True, True])
    toks = ev("""() => [proximaParts('{n} landed.', { n: 1 }), proximaParts('{diff} and {diff}', { diff: 3 }), proximaParts('{diff}', { diff: -2 }),
      proximaParts('{added}, {g}, {due}, {late}, {usual}', { added: 4, g: -5, due: 2, late: 1, usual: 15.6 })]""")
    ok(f'B1 a number in her line is a token, its icon and its words; one reads in the singular ({toks[0]})', toks[0] == [{'k': 'tick', 't': '1 task'}, ' landed.'])
    ok('more is an arrow up, fewer an arrow down', toks[1][0] == {'k': 'up', 't': '3 more'} and toks[2] == [{'k': 'down', 't': '2 fewer'}])
    ok('added, in or out, due, overdue and her usual each have their own', [x['k'] for x in toks[3] if isinstance(x, dict)] == ['plus', 'down', 'clock', 'alert', 'chart']
       and [x['t'] for x in toks[3] if isinstance(x, dict)] == ['4 added', '5', '2 due', '1 overdue', '15.6'])

    ev(FIXTURE)
    R = lambda kind, frm='null', now=MON: ev(f"""() => {{ const r = Proxima.report('{kind}', {now}, {frm});
      const nm = x => x.p.name + ':' + x.t.text;
      return {{ line: r.line, parts: r.parts, label: r.label, n: r.n, before: r.before, usual: r.usual, streak: [r.streak.n, r.streak.best.n],
        ms: (r.milestones || []).map(x => x.m.name), due: (r.due || []).map(nm), overdue: (r.overdue || []).map(nm), next: (r.next || []).map(nm),
        rows: (r.rows || []).map(x => ({{ name: x.p.name, n: x.n, done: x.done.map(d => d.text), linked: x.done.filter(d => d.t).length, added: x.added.length,
          notes: x.notes.map(n => n.title), worked: x.worked, late: x.late, quiet: x.quiet, ms: x.ms.map(m => m.m.name),
          mile: x.mile && [x.mile.m.name, x.mile.done, x.mile.total, x.mile.moved], idle: x.idle, next: x.next ? x.next.t.text : null }})),
        totals: r.totals, repeats: (r.repeats || []).map(x => [x.t.text, x.k]), yday: r.yday, ydayIn: (r.ydayIn || []).map(p => p.name), has: Object.keys(r) }}; }}""")
    w, m, d = R('weekly'), R('monthly'), R('daily')
    ok(f'weekly: tasks finished, the week before, and her usual: the average of the weeks before since the city started ({w["n"]}, {w["before"]}, {w["usual"]})',
       (w['n'], w['before'], w['usual']) == (7, 3, 0.8))
    ok('A1 every building shows, the most finished first', [x['name'] for x in w['rows']] == ['Garden planner', 'Nullovation City'] and [x['n'] for x in w['rows']] == [4, 3])
    gp, nc = w['rows']
    ok('0.1.84 a building with something in the week is not quiet', not gp['idle'] and not nc['idle'])
    ok('A1 a row holds what its building finished (A2: Finished, taken in), a task still there as a link', gp['done'] == ['Water the beds', 'Water the beds', 'Water the beds', 'Weed the beds']
       and gp['linked'] == 3 and nc['done'] == ['Round 3: decide the block art loop', 'Build the block art skill', 'Level the ground'] and nc['linked'] == 3)
    ok('A2 added, notes and I worked! as counts on their row', (gp['added'], gp['notes'], gp['worked']) == (2, ['Soil'], 0) and (nc['added'], nc['notes'], nc['worked']) == (0, [], 1))
    ok('A1 a building\'s milestones finished on its row', nc['ms'] == ['Ground'] and gp['ms'] == [])
    ok(f'B2 its milestone and how far it moved: the one most of its tasks went to, as it stood at the week\'s end ({nc["mile"]})', nc['mile'] == ['Block art', 2, 3, 2])
    ok(f'and with none finished, in a report that reaches today, its current one ({gp["mile"]})', gp['mile'] == ['First release', 0, 4, 0])
    ok('the overdue count on each row, in a report that reaches today', gp['late'] == 1 and nc['late'] == 0)
    ok('the totals, added against finished (B2)', w['totals'] == {'n': 7, 'added': 2, 'notes': 1, 'worked': 1, 'late': 1})
    ok('milestones finished, with their building', w['ms'] == ['Ground'])
    ok('A1 every overdue task, the oldest first', w['overdue'] == ['Garden planner:Save a plan as a file'])
    ok('what is due from today to the end of this week, a repeat coming back in it too',
       w['due'] == ['Nullovation City:Try the project view for a week', 'Garden planner:Draw the beds on a grid', 'Garden planner:Water the beds'])
    ok('B2 each building\'s next task, the one its status card puts first', w['next'] == ['Garden planner:Save a plan as a file', 'Nullovation City:Try the project view for a week'])
    WOPEN = ('Copy that, week logged: 7 tasks landed.', 'Weekly report inbound! 7 tasks landed.')
    WREST = " That's 4 more than the week before, and above your usual 0.8! 2 added against them: 5 more out than in! Flight plan: 3 due this week, 1 overdue."
    ok(f'B1 her weekly line: what landed, against the week before and her usual, what came in, and the flight plan ({w["line"]})',
       any(w['line'] == o + WREST for o in WOPEN))
    ok('her line\'s numbers are tokens', [x['t'] for x in w['parts'] if isinstance(x, dict)] == ['7 tasks', '4 more', '0.8', '2 added', '5', '3 due', '1 overdue'])
    ok('the same report always gets the same line', all(R('weekly')['line'] == w['line'] for _ in range(3)))
    ok('the labels: the day, the week, the month', (d['label'], w['label'], m['label']) == ('Mon 19 Oct', '10 Oct to 16 Oct', 'September'))
    # the monthly report: September
    ok('C2 monthly: like the weekly, over the month', (m['n'], m['before']) == (4, 1) and [x['name'] for x in m['rows']] == ['Garden planner', 'Nullovation City'])
    ok('a building with nothing finished says how long it has been quiet', m['rows'][1]['n'] == 0 and m['rows'][1]['quiet'] == 'No task finished yet')
    ok('0.1.84 one with nothing in the month (no tick, nothing added, no note or check-in, not planted) is quiet, to fold into one line',
       m['rows'][1]['idle'] and not m['rows'][0]['idle'])
    ok(f'0.1.84 Next up holds the buildings with something in it; a quiet one keeps its next task on its row ({m["next"]})',
       m['next'] == ['Garden planner:Save a plan as a file'] and m['rows'][1]['next'] == 'Try the project view for a week')
    ok('0.1.84 Copy the month names the quiet ones in a line, not under their own heading', ev(f"""() => {{ const t = proximaText(Proxima.report('monthly', {MON}));
      return t.includes('\\nQuiet buildings: Nullovation City (no task finished yet).') && !t.includes('## Nullovation City') && t.includes('## Garden planner'); }}"""))
    ok('C2 what only a month shows: repeats kept up', m['repeats'] == [['Water the beds', 4]] and w['repeats'] == [])
    MREST = " That's 3 more than the month before. Flight plan: 4 due this month, 1 overdue."
    ok(f'her monthly line: no usual with fewer than two months before ({m["line"]})', m['usual'] is None and any(m['line'] == o + MREST for o in ('September is logged: 4 tasks landed.', 'Monthly report on deck! 4 tasks landed in September.')))
    # the morning brief
    ok(f'C1 the morning brief: due today, overdue, and yesterday ({d["line"]})', d['due'] == ['Nullovation City:Try the project view for a week'] and d['overdue'] == ['Garden planner:Save a plan as a file']
       and d['line'] in ("Daily brief on deck! Today: 1 due, 1 overdue. Yesterday: 1 task landed.", "Copy that, today's brief is in. Today: 1 due, 1 overdue. Yesterday: 1 task landed."))
    ok('yesterday as one line: its count and its buildings', d['yday'] == 1 and d['ydayIn'] == ['Garden planner'])
    ok('next up in each busy building, a tick in the last 7 days, the latest first', d['next'] == ['Garden planner:Save a plan as a file', 'Nullovation City:Try the project view for a week'])
    ok('the brief holds no table', 'rows' not in d['has'] or not d['rows'])
    # the week in progress, an older week, a quiet week
    live = R('weekly', 'weekStartOf(' + MON + ')')
    ok(f'the week so far: no comparison yet, but the flight plan ({live["line"]})', live['n'] == 1 and live['line'] == 'This week so far: 1 task landed. Flight plan: 3 due this week, 1 overdue.')
    old = R('weekly', 'new Date(2026, 9, 5).getTime()')
    ok(f'an older week: its own numbers, and nothing about today ({old["line"]})', (old['n'], old['before'], old['usual']) == (3, 1, 0.6) and old['overdue'] == [] and old['due'] == [] and old['next'] == []
       and old['line'].endswith(" That's 2 more than the week before, and above your usual 0.6!") and all(x['late'] == 0 for x in old['rows']))
    q = R('weekly', 'null', 'new Date(2026, 7, 17, 12).getTime()')
    ok(f'a quiet week ({q["line"]})', q['n'] == 0 and q['line'] == 'Quiet week: no tasks landed. Flight plan: clear for the rest of the week!'
       and [x['quiet'] for x in q['rows']] == ['No task finished yet', 'No task finished yet'] and all(x['idle'] for x in q['rows']))
    ok('a report on a period that ended before the city started is not given', ev(f"() => proximaRelevant(proximaPeriod('monthly', {MON}))")
       and not ev("() => proximaRelevant(proximaPeriod('monthly', new Date(2026, 7, 5, 12).getTime()))"))
    ok('Copy the week: the week as text, for Claude or Slack', ev(f"""() => {{ const t = proximaText(Proxima.report('weekly', {MON}));
      return t.startsWith('# Nullovation City, week of 10 Oct to 16 Oct 2026\\n') && t.includes('## Garden planner') && t.includes('Finished:\\n- Water the beds') && t.includes('Milestone: Block art, 2 of 3, 2 this week.')
        && t.includes('Overdue:\\n- Save a plan as a file (Garden planner, 4 days overdue)'); }}"""))
    ctx.close()

    # ---------- her card, her reports and her bubble, today ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    ok('a new city: nothing to report yet, no dot, no bubble, nothing waiting', not ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')") and not pg.is_visible('#pxSay')
       and ev("() => Proxima.waiting()") == 0)
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
    ok('with nothing to report: her first report comes tomorrow, the daily one too (C1: it starts the day after the city)', pg.text_content('#pxLine') == 'Her first report comes tomorrow.' and not pg.is_visible('#pxReports'))
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
      const rb = createProject('Recipe box', freePlots()[0]);
      rb.createdAt = now - 70 * D; rb.activity = [];
      rb.todos.push({ id: 't_rb', text: 'Sort the recipes', done: false, due: ymd(now - 5 * D), milestoneId: null, createdAt: now - 70 * D });
      changed(gp); changed(nc); changed(rb);
    }""")
    pg.wait_for_timeout(150)
    ok('the Reports button wears a dot while a report waits unread', ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')")
       and 'Proxima has a report' in pg.get_attribute('#btnOpenReports', 'title'))
    ev("() => Proxima._test.sayMs(60000); Proxima.check()"); pg.wait_for_timeout(300)
    px_face = lambda: pg.click('#newsList .news-tile[data-k="px"] .news-face')
    ok('J3 her reports wait in News with her face, no bubble by itself (0.1.96)', not pg.is_visible('#pxSay') and ev("() => Proxima.waiting()") == 3
       and pg.locator('#newsList .news-tile[data-k="px"]').count() == 1)
    px_face(); pg.wait_for_timeout(300)
    ok('J3 a click on her face opens her card on the weekly report', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'weekly'
       and pg.text_content('#pxSayText') == ev("() => Proxima.report('weekly').line") and pg.text_content('#pxSay .lc-nm') == 'Proxima Pace')
    ok('C1 the monthly one waits its turn, and the daily one after it, pages of her card (1 / 3)', ev("() => Proxima._test.queue()") == ['weekly', 'monthly', 'daily']
       and pg.text_content('#pxPager .lc-pgn') == '1 / 3')
    tk = ev("""() => [...document.querySelectorAll('#pxSayText .px-tok')].map(t => [t.dataset.k, t.querySelector('b').textContent, !!t.querySelector('svg'), getComputedStyle(t).color])""")
    ok(f'B1 her line\'s numbers are tokens in her bubble: an icon and the words, in her sky blue ({tk[:2]})', len(tk) >= 2 and tk[0][0] == 'tick' and all(t[2] and t[3] == 'rgb(143, 208, 247)' for t in tk))
    f = ev(FACE_OF, '#pxSayFace')
    ok(f'in her speech bubble: her portrait, bigger, 100 by 100 (0.1.57; 80 before), on her dark sky blue ({f and {k: f[k] for k in ("w", "h", "fw")}})',
       f and f['url'] == px and f['imgs'] == 1 and f['w'] == f['h'] == f['fw'] == 100 and f['smooth'] and f['bg'] == 'rgb(31, 53, 80)')
    wide = ev("""() => { const b = document.querySelector('#pxSay'), t = document.querySelector('#pxSayText').getBoundingClientRect(), f = document.querySelector('#pxSayFace').getBoundingClientRect(),
        n = b.querySelector('.lc-wn').getBoundingClientRect();
        return { narrow: b.classList.contains('narrow'), beside: n.left >= f.right, under: t.top >= f.bottom, text: Math.round(t.width), w: Math.round(b.getBoundingClientRect().width) }; }""")
    ok(f'over the open map, the leaders\' card: her name beside her face, her words under them, at most 420 px wide (0.1.96; words beside the face and 400 px since 0.1.57) ({wide})',
       not wide['narrow'] and wide['beside'] and wide['under'] and wide['w'] <= 420)
    pg.wait_for_timeout(2200)
    pg.screenshot(path=str(SHOTS / '300-proxima-says.png'), clip={'x': 290, 'y': 0, 'width': 620, 'height': 230})
    ok('shown is not heard yet: the report waits until its x or Read (0.1.96)', ev("() => Proxima._test.state().spoke.weekly") != ev("() => proximaPeriod('weekly').key"))
    # Gus cuts in: she gives way; her pages wait in News, and her face opens them again after him
    ev("() => { window._gusSays = Gus.isSaying; Gus.isSaying = () => true; Proxima.yieldToGus(); }"); pg.wait_for_timeout(200)
    ok('never both at once: when Gus speaks, her bubble goes', not pg.is_visible('#pxSay') and ev("() => Proxima._test.queue()") == ['weekly', 'monthly', 'daily'])
    pg.wait_for_timeout(700)
    ok('and she waits while he speaks', not pg.is_visible('#pxSay'))
    ev("() => { Gus.isSaying = window._gusSays; }"); pg.wait_for_timeout(800)
    ok('after him she does not come back by herself: her three pages wait in News (0.1.96)', not pg.is_visible('#pxSay') and ev("() => Proxima.waiting()") == 3)
    px_face(); pg.wait_for_timeout(300)
    ok('then her face opens hers', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'weekly')
    # Read: a link now (0.1.96), Reports open, with the report
    ok('Read is a link', ev("() => [document.querySelector('#pxSayRead').tagName, document.querySelector('#pxSayRead').textContent]") == ['A', 'Read'])
    pg.click('#pxSayRead'); pg.wait_for_timeout(300)
    ok('Read opens Reports and the weekly report', pg.is_visible('#reports') and ev("() => Panel.isOpen()") and pg.text_content('#pnTitle') == 'Weekly report' and not pg.is_visible('#pxSay'))
    ok('she says each report once: Read marks it heard, gone from News', ev("() => Proxima._test.state().spoke.weekly") == ev("() => proximaPeriod('weekly').key")
       and ev("() => Proxima._test.queue()") == ['monthly', 'daily'])
    ok('the report opens with her line, its tokens drawn, then the week with its arrows', pg.text_content('#pxReportLine') == ev("() => Proxima.report('weekly').line")
       and pg.locator('#pxReportLine .px-tok').count() >= 2 and pg.text_content('#pxWhen') == ev("() => weekLabel(proximaPeriod('weekly').from, true)")
       and pg.get_attribute('.px-nav [data-k=next]', 'disabled') is None)
    heads = ev("() => [...document.querySelectorAll('.px-report .px-sec > h4')].map(h => h.textContent)")
    ok(f'the weekly report: streak, buildings, milestones finished, overdue, this week and next up; no busiest, no facts ({heads})',
       heads == ['Streak', 'Buildings', 'Milestones finished', 'Overdue', 'This week', 'Next up'])
    ok('B1 the table: a head with Finished, Added, Overdue and Milestone, and every building with something in the week, the most finished first',
       ev("() => [...document.querySelectorAll('.px-bhead span')].map(s => s.textContent)") == ['Building', 'Finished', 'Added', 'Overdue', 'Milestone']
       and ev("() => [...document.querySelectorAll('#pxBuildings .px-brow')].map(r => r.dataset.id)") == ev("() => Proxima.report('weekly').rows.filter(x => !x.idle).map(x => x.p.id)")
       and pg.locator('#pxBuildings .px-brow').count() == 2)
    ok('the row\'s numbers, and the totals under them, the quiet buildings counted too', ev("""() => { const r = Proxima.report('weekly'), row = document.querySelector('#pxBuildings .px-brow'), f = document.querySelectorAll('.px-bfoot .px-num');
        return row.querySelectorAll('.px-num')[0].textContent === String(r.rows[0].n) && f[0].textContent === String(r.n) && f[2].textContent === String(r.totals.late) && r.totals.late === r.overdue.length; }"""))
    # 0.1.84: the quiet buildings, no row each, but one line under the rows, folded
    rb = ev("() => DB.projects.find(p => p.name === 'Recipe box').id")
    ok('0.1.84 a quiet building has no row of zeros: one line under the rows, folded, counts them and their overdue tasks',
       pg.locator(f'#pxBuildings .px-brow[data-id="{rb}"]').count() == 0 and pg.text_content('.px-qrow .px-qname') == '1 quiet building'
       and pg.text_content('.px-qrow .px-bsub') == 'Nothing finished or added this week · 1 overdue task' and pg.get_attribute('.px-qrow', 'aria-expanded') == 'false'
       and pg.locator('#pxQuiet').count() == 0 and ev("() => document.querySelector('#pxBuildings').lastElementChild.classList.contains('px-qitem')"))
    ok('0.1.84 its next task is not in Next up', 'Sort the recipes' not in pg.text_content('#pxNext') and pg.locator('#pxNext li').count() == 2)
    pg.click('.px-qrow'); pg.wait_for_timeout(200)
    qi = f'#pxQuiet li[data-id="{rb}"]'
    ok('0.1.84 opened, with the focus kept: each quiet building, how long it has been quiet, its overdue tasks and its next task',
       pg.get_attribute('.px-qrow', 'aria-expanded') == 'true' and ev("() => document.activeElement.dataset.k") == 'quiet' and pg.locator('#pxQuiet li').count() == 1
       and pg.text_content(f'{qi} .px-bname-link') == 'Recipe box' and pg.text_content(f'{qi} .px-bsub') == 'No task finished yet · 1 overdue'
       and pg.text_content(f'{qi} .px-link') == 'Sort the recipes')
    pg.screenshot(path=str(SHOTS / '309-proxima-quiet.png'))
    pg.click('.px-qrow'); pg.wait_for_timeout(200)
    ok('0.1.84 and folds again', pg.get_attribute('.px-qrow', 'aria-expanded') == 'false' and pg.locator('#pxQuiet').count() == 0)
    ok('A1 every overdue task, each a link', pg.locator('#pxOverdue li').count() == ev("() => Proxima.report('weekly').overdue.length") and pg.is_visible('#pxOverdue .recap-day.late'))
    f = ev(FACE_OF, '.px-says')
    ok(f'the report opens with her portrait at 64 by 64 ({f and {k: f[k] for k in ("w", "h")}})', f and f['url'] == px and f['imgs'] == 1 and f['w'] == f['h'] == 64)
    pg.screenshot(path=str(SHOTS / '301-proxima-weekly.png'))
    # A1: a row opens on what its building finished, only when opened
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    row = f'#pxBuildings .px-brow[data-id="{gp}"]'
    ok('A1 a row is folded until opened', pg.get_attribute(row, 'aria-expanded') == 'false' and pg.locator('.px-bdetail').count() == 0)
    pg.click(row); pg.wait_for_timeout(200)
    ok('opened: what it finished, by day, with the focus kept on the row', pg.get_attribute(row, 'aria-expanded') == 'true' and pg.is_visible('.px-bdetail')
       and 'Water the beds' in pg.text_content('.px-bdetail') and ev("() => document.activeElement.dataset.k") == 'b-' + gp)
    pg.screenshot(path=str(SHOTS / '305-proxima-row-open.png'))
    pg.click('.px-bdetail .px-link >> text=Water the beds >> nth=0'); pg.wait_for_timeout(500)
    ok('a task it finished opens in its project', not ev("() => Panel.isOpen()") and pg.is_visible('#pvSide #pvTaskName') and pg.text_content('#pvTaskName') == 'Water the beds')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(900)
    ok('read: no dot on the weekly report', not ev("() => document.querySelector('[data-k=px-weekly]').classList.contains('new')"))
    ok('with Reports still open nothing opens: the monthly and the daily wait in News', not pg.is_visible('#pxSay') and ev("() => Proxima._test.queue()") == ['monthly', 'daily'])
    ev("() => Reports.close()"); pg.wait_for_timeout(900)
    ok('Reports closed, she still waits in News: no bubble by itself (0.1.96)', not pg.is_visible('#pxSay') and ev("() => Proxima.waiting()") == 2)
    px_face(); pg.wait_for_timeout(300)
    ok('her face opens the monthly one', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'monthly')
    pg.click('#pxSayClose'); pg.wait_for_timeout(900)
    ok('her x: the monthly one heard, and the daily one comes after it', ev("() => Proxima.saying()") == 'daily'
       and ev("() => Proxima._test.state().spoke.monthly") == ev("() => proximaPeriod('monthly').key") and ev("() => Proxima._test.queue()") == ['daily'])
    ev("() => Proxima.hush(false)"); pg.wait_for_timeout(150)
    ev("() => Reports.open()"); pg.wait_for_timeout(200)
    ok('closed unread, the monthly report keeps its dot', ev("() => document.querySelector('[data-k=px-monthly]').classList.contains('new')"))
    rows = ev("() => [...document.querySelectorAll('#pxReports .px-report-row')].map(b => [b.dataset.kind, b.querySelector('.px-report-kind').textContent, b.querySelector('.px-report-when').textContent])")
    ok(f'J1 three reports on her card: daily on today, weekly, monthly ({rows})', [r[:2] for r in rows] == [['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly']]
       and rows[0][2] == ev("() => proximaLabel(proximaPeriod('daily'))"))
    ok('her card\'s line draws its tokens too', pg.locator('#pxLine .px-tok').count() >= 1)
    pg.screenshot(path=str(SHOTS / '302-proxima-card.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 420})
    pg.click('[data-k=px-monthly]'); pg.wait_for_timeout(250)
    heads = ev("() => [...document.querySelectorAll('.px-report .px-sec > h4')].map(h => h.textContent)")
    ok(f'C2 the monthly report: the weekly\'s parts over the month, and repeats kept up ({heads})', pg.text_content('#pnTitle') == 'Monthly report'
       and heads == ['Streak', 'Buildings', 'Milestones finished', 'Repeats kept up', 'Overdue', 'This month', 'Next up'])
    pg.screenshot(path=str(SHOTS / '303-proxima-monthly.png'))
    pg.click('.px-nav [data-k=next]'); pg.wait_for_timeout(200)
    ok('C2 its arrows go on to the month in progress', 'so far' in pg.text_content('#pxWhen') and pg.get_attribute('.px-nav [data-k=next]', 'disabled') is not None
       and ev("() => document.activeElement.dataset.k") in ('next', None) and pg.text_content('#pxReportLine').endswith('.') and ' so far: ' in pg.text_content('#pxReportLine'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click('[data-k=px-daily]'); pg.wait_for_timeout(250)
    heads = ev("() => [...document.querySelectorAll('.px-report .px-sec > h4')].map(h => h.textContent)")
    ok(f'C1 the daily report, a morning brief: today, overdue, next up, yesterday and the streak ({heads})', pg.text_content('#pnTitle') == 'Daily report'
       and heads == ['Today', 'Overdue', 'Next up', 'Yesterday', 'Streak'] and pg.locator('.px-buildings').count() == 0)
    ok('today, the task due today; yesterday in one line', 'Try the project view for a week' in pg.text_content('#pxDue') and 'landed, in ' in pg.text_content('#pxYesterday'))
    pg.screenshot(path=str(SHOTS / '306-proxima-daily.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('every report read: no dots, none on the Reports button', ev("() => document.querySelectorAll('#pxReports .new').length") == 0
       and not ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')"))
    ok('Esc closed the report and left Reports open', pg.is_visible('#reports') and not ev("() => Panel.isOpen()"))
    pg.click('#rpBack'); pg.wait_for_timeout(150)

    # one weekly report: the side bar's This week card opens it, on the week so far (A2)
    ev(f"""() => {{ const p = DB.projects.find(p => p.id === '{gp}'); p.notes.push({{ id: 'n_week', title: 'Compost', text: 'Turn it weekly.', at: Date.now() }});
      p.activity.push({{ at: Date.now(), text: 'Added todo: Turn the compost' }}); changed(p); }}""")
    pg.wait_for_timeout(150)
    pg.click('#btnRecap'); pg.wait_for_timeout(400)
    ok('A2 This week opens the one weekly report, on the week so far', pg.text_content('#pnTitle') == 'Weekly report' and pg.text_content('#pxWhen').endswith(', so far')
       and pg.text_content('#pxReportLine').startswith('This week so far: ') and pg.get_attribute('.px-nav [data-k=next]', 'disabled') is not None)
    ok('and the card counts as the report does: ticks', ev("() => { const r = Proxima.report('weekly', Date.now(), weekStartOf(Date.now())); return r.n; }") ==
       ev("() => { const t = document.querySelector('#weekNumbers').textContent.match(/(\\d+) tasks? done/); return t ? Number(t[1]) : 0; }"))
    ok('A2 Your week is gone', not ev("() => typeof openRecap !== 'undefined' || typeof weekOf !== 'undefined'") and pg.locator('.recap').count() == 0)
    n_opts = pg.locator('#pxPick option').count()
    ok(f'A2 every week to go back to, since the city started ({n_opts})', n_opts >= 10 and pg.input_value('#pxPick') == str(ev("() => weekStartOf(Date.now())")))
    pg.click(f'#pxBuildings .px-brow[data-id="{gp}"]'); pg.wait_for_timeout(200)
    ok('A2 its notes as a count, folded', 'Compost' not in pg.text_content('.px-bdetail') and pg.is_visible('.px-bdetail .px-fold'))
    pg.click('.px-bdetail .px-fold'); pg.wait_for_timeout(200)
    ok('which opens on them', 'Compost' in pg.text_content('.px-bdetail') and pg.get_attribute('.px-bdetail .px-fold', 'aria-expanded') == 'true')
    pg.screenshot(path=str(SHOTS / '307-proxima-this-week.png'))
    pg.click('.px-notes .px-link >> text=Compost'); pg.wait_for_timeout(500)
    ok('A2 a note opens in its project', not ev("() => Panel.isOpen()") and pg.is_visible('#pvSide #pvNoteTitle') and pg.input_value('#pvNoteTitle') == 'Compost')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.click('#btnRecap'); pg.wait_for_timeout(400)
    pg.click('.px-nav [data-k=prev]'); pg.wait_for_timeout(200)
    ok('the week before, in place, the focus kept on the arrow', not pg.text_content('#pxWhen').endswith('so far') and pg.locator('.modal.panel').count() == 1
       and ev("() => document.activeElement.dataset.k") == 'prev' and pg.get_attribute('.px-nav [data-k=next]', 'disabled') is None)
    pg.select_option('#pxPick', index=0); pg.wait_for_timeout(200)
    ok('the list jumps back to this week', pg.text_content('#pxWhen').endswith(', so far'))
    pg.click('.px-foot .btn'); pg.wait_for_timeout(200)
    c = ev("() => navigator.clipboard.readText()").replace('\r\n', '\n')
    ok('A2 Copy the week copies it as text', c.startswith('# Nullovation City, week of ') and ', so far\n' in c and '## Garden planner' in c and '1 note' in c)
    ok('0.1.84 the quiet ones in a line, with their overdue tasks', 'Recipe box (no task finished yet, 1 overdue)' in c and '## Recipe box' not in c)
    pg.click(f'#pxBuildings .px-brow[data-id="{gp}"]'); pg.wait_for_timeout(150)
    pg.click('.px-bdetail .px-go'); pg.wait_for_timeout(400)
    ok('a building in a report goes to it on the map', not ev("() => Panel.isOpen()") and ev("() => App.selectedId") == gp and pg.is_visible('#bubble'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click('#btnRecap'); pg.wait_for_timeout(400)
    pg.click('.px-qrow'); pg.wait_for_timeout(200)
    pg.click(f'#pxQuiet li[data-id="{rb}"] .px-link'); pg.wait_for_timeout(500)
    ok('0.1.84 a quiet building\'s next task opens in its project', not ev("() => Panel.isOpen()") and pg.is_visible('#pvSide #pvTaskName') and pg.text_content('#pvTaskName') == 'Sort the recipes')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.click('#btnRecap'); pg.wait_for_timeout(400)
    pg.click('.px-qrow'); pg.wait_for_timeout(200)
    pg.click(f'#pxQuiet li[data-id="{rb}"] .px-bname-link'); pg.wait_for_timeout(400)
    ok('0.1.84 and its name shows it on the map', not ev("() => Panel.isOpen()") and ev("() => App.selectedId") == rb)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # a reload: what was read and said is kept
    pg.reload(); pg.wait_for_timeout(2200)
    ok('after a reload she says nothing again, nothing waits in News, and nothing is unread', not pg.is_visible('#pxSay') and ev("() => Proxima.waiting()") == 0
       and not ev("() => document.querySelector('#btnOpenReports').classList.contains('has-news')"))
    # a fresh visit to the same city: all three wait in News, the weekly first
    ev("() => Proxima._test.forget()")
    pg.reload(); pg.wait_for_timeout(2400)
    ok('on the first open after a week and a month end, her three reports wait in News, the weekly first, the monthly and daily after it; no bubble by itself (0.1.96)',
       not pg.is_visible('#pxSay') and ev("() => Proxima._test.queue()") == ['weekly', 'monthly', 'daily'] and ev("() => Proxima.waiting()") == 3)
    ev("() => Proxima._test.sayMs(300)")
    px_face(); pg.wait_for_timeout(1200)
    ok('her bubble no longer goes by itself: opened, it stays on the weekly one (0.1.96)', pg.is_visible('#pxSay') and ev("() => Proxima.saying()") == 'weekly')
    pg.click('#pxSayMin'); pg.wait_for_timeout(300)
    ok('Minimize: her bubble goes, and all three still wait in News', not pg.is_visible('#pxSay') and ev("() => Proxima.waiting()") == 3)
    ev("() => { Proxima.hush(false); }")

    # a narrow window: her card in the drawer, and a report that fits
    pg.set_viewport_size({'width': 700, 'height': 800}); pg.wait_for_timeout(200)
    pg.keyboard.press('r'); pg.wait_for_timeout(300)
    ok('on a narrow window, her card shows in the drawer', pg.is_visible('#pxCard') and ev("() => document.querySelector('#pxCard').getBoundingClientRect().right") <= 700)
    pg.screenshot(path=str(SHOTS / '304-proxima-narrow.png'))
    pg.click('[data-k=px-weekly]'); pg.wait_for_timeout(300)
    fit = ev("""() => { const m = document.querySelector('.modal.panel'); const r = document.querySelector('#pxBuildings .px-brow').getBoundingClientRect();
        return { over: m.scrollWidth - m.clientWidth, right: Math.round(r.right), w: window.innerWidth }; }""")
    ok(f'and the table fits it, the milestone under the numbers ({fit})', fit['over'] <= 0 and fit['right'] <= fit['w'])
    pg.screenshot(path=str(SHOTS / '308-proxima-narrow-report.png'))
    ctx.close()

    ok('no console errors', not errors)
    if errors: print('\n'.join(errors[:10]))
    b.close()
