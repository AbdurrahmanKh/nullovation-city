"""The leaders' news (0.1.59, and the task and the building as links at 0.1.60), the third piece of the leader UX: the side bar's News section in place of Urgent and
Gus's part, each leader's news in its own bubble at the map's top left (Proxima's for a building with no leader), the
moments that open by themselves and those that wait, the pages with their arrows, reading and dismissing, the status card and the
leader card saying a building's news, Gus's report in his bubble, the leaders' faces in Reports, and nothing new in the
city's data. Since 0.1.96 (One Leader Card) the bubble is the leader's card: a page per message with its type, the task
in its own line and "this task" in the words, Minimize and an x on each page, no closing by itself after 14 seconds,
paging marks a page seen without reading it, what Claude added and one task from done wait in News, and a card reads
only the page it shows."""
import json
from playwright.sync_api import sync_playwright
import base64
from testkit import FILE, SHOTS, TEST_CITY, fixture

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t40')) { sessionStorage.setItem('nc-t40', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    tid = lambda text, pid=gp: ev(f"() => (getProject('{pid}').todos.find(t => t.text === {json.dumps(text)}) || {{}}).id || null")
    D = 86400000
    tiles = lambda: ev("() => [...document.querySelectorAll('#newsList .news-tile')].map(t => [t.dataset.k, t.querySelector('.news-badge').textContent, t.querySelector('.news-name').textContent, !!t.querySelector('.news-dismiss')])")
    # the bubble is the leader's card since 0.1.96: its type in its head with the pager, Minimize and the page's x; the
    # building and the task in the task's line (#ldSayWhere); its buttons, then Go to it
    say = lambda: ev("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null; const nx = $('#ldSayNext'), pv = $('#ldSayPrev'), tk = b.querySelector('#ldSayWhere .ld-task');
        return { k: b.dataset.k, moment: b.dataset.moment, type: b.dataset.type, name: $('#ldSayName').textContent, role: ($('#ldSayRole') || {}).textContent, where: ($('#ldSayWhere') || {}).textContent,
          task: tk ? tk.textContent : '', text: $('#ldSayText').textContent,
          acts: [...b.querySelectorAll('#ldSayActs button')].map(x => (x.textContent || x.getAttribute('aria-label')) + (x.disabled ? ' (off)' : '')), count: ($('#ldSayCount') || {}).textContent || '',
          next: nx ? !nx.disabled : null, prev: pv ? !pv.disabled : null, dotNext: !!b.querySelector('#ldSayNext .lc-dot'), dotPrev: !!b.querySelector('#ldSayPrev .lc-dot'),
          min: !!$('#ldSayMin'), x: !!$('#ldSayClose'), face: (b.querySelector('#ldSayFace .ld-face, #ldSayFace .gus-face') || {}).offsetWidth || 0,
          left: Math.round(b.getBoundingClientRect().left - document.querySelector('#mapWrap').getBoundingClientRect().left), top: Math.round(b.getBoundingClientRect().top - document.querySelector('#mapWrap').getBoundingClientRect().top),
          color: getComputedStyle(b).getPropertyValue('--ld').trim() }; }""")
    unread = lambda: ev("() => News.items().map(it => it.moment + ':' + (getProject(it.pid) || {}).name)")
    settle = lambda ms=400: pg.wait_for_timeout(ms)
    close_say = lambda: (pg.click('#ldSayClose'), settle(300))                 # the page's x (0.1.96)
    mini = lambda: (ev("() => { const m = document.querySelector('#ldSayMin'); if (m && !document.querySelector('#ldSay').hidden) m.click(); }"), settle(300))   # Minimize: it waits in News
    face_of = lambda k: (pg.click(f'#newsList .news-tile[data-k="{k}"] .news-face'), settle(300))
    ev("() => { News._test.typeMs(0); Garbage.setOn(false); }")   # Gus waits for his own part, below; lines show whole (their typing is test41's)

    # ---------- the side bar ----------
    order = ev("() => [...document.querySelectorAll('#sbLists > section')].map(s => s.id || s.getAttribute('aria-label'))")
    ok(f'Urgent and Gus\'s part are gone, and News sits between This week and Due this week ({order})',
       'sbUrgent' not in order and 'sbGus' not in order and order.index('sbNews') == order.index('This week') + 1 and order.index('sbDue') == order.index('sbNews') + 1)
    ok('with no news and a clean city, the News section is hidden', ev("() => document.querySelector('#sbNews').hidden") and tiles() == [])
    ok('the old [-] key is tidied away', ev("() => localStorage.getItem('nullovation-city:gusMin')") is None)

    # a leader for Garden planner; Nullovation City has none
    ev(f"""() => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Nullovations', color: '#8FD0F7' }}); DB.leaders.push(l);
        setLeader(getProject('{gp}'), l.id); persistNow(); Leaders.refreshAll(); }}""")
    lid = ev("() => DB.leaders[0].id")
    before_keys = ev(f"() => Object.keys(getProject('{gp}')).sort().join(',')")

    # ---------- behind its pace: opens by itself ----------
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'pace', days: 1, lastWorked: Date.now() - 3600e3, pickedAt: Date.now() - 30 * {D} }}; changed(p); }}")
    settle()
    ok('picking a pace, or ticking on time, is not news', say() is None and unread() == [])
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.5 * {D}; changed(p); }}")
    settle()
    s = say()
    ok(f'slipping behind its pace opens its leader\'s bubble by itself, a Heads up page, the words saying "this task" (0.1.96) ({s and s["text"]})',
       s and s['moment'] == 'behind' and s['type'] == 'headsup' and s['text'] == 'We slipped behind our pace. This task puts us back on track.')
    ok(f'the bubble: the face at 100 px, the name and role, the building then the task in its line, Minimize and the x, and Go to it ({s})',
       s and s['face'] == 100 and s['name'] == 'Talal' and s['role'] == 'Head of Nullovations' and s['where'] == 'Garden planner·Draw the beds on a grid' and s['task'] == 'Draw the beds on a grid'
       and s['min'] and s['x'] and s['acts'] == ['Go to it'] and s['count'] == '')
    ok(f'at the map\'s top left, where Gus and Proxima speak, in the leader\'s color ({s and (s["left"], s["top"], s["color"])})', s and s['left'] == 22 and s['top'] == 18 and s['color'].upper() == '#8FD0F7')
    ok('its building wears the hover ring while it shows', ev("() => MapView._lit()") == gp)
    t = tiles()
    ok(f'Talal shows in News with ! for one item, and a dismiss ({t})', t == [['ld:' + lid, '!', 'Talal', True]])
    ok('under each face the first word of its name, the tooltip saying it whole with the role', ev("() => document.querySelector('#newsList .news-face').title").startswith('Talal, Head of Nullovations: 1 piece of news.'))
    pg.screenshot(path=str(SHOTS / '400-news-behind.png'))
    pg.wait_for_timeout(15000)
    ok('opened by itself, it no longer closes by itself after 14 seconds (0.1.96)', say() is not None and unread() == ['behind:Garden planner'])
    mini()
    ok('Minimize: the bubble goes, the news waits in News, unread, the ring off', say() is None and unread() == ['behind:Garden planner'] and ev("() => MapView._lit()") is None
       and tiles() == [['ld:' + lid, '!', 'Talal', True]])
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 2.5 * {D}; changed(p); }}")
    settle()
    s = say()
    ok(f'falling further behind replaces it, and says so ({s and s["text"]})', s and s['text'] == "We're falling further behind. This task pulls us back." and unread() == ['behind_more:Garden planner'])
    close_say()
    ok('its x: the page is read, the bubble closes with its last page, and Talal leaves News', say() is None and unread() == [] and tiles() == [] and ev("() => document.querySelector('#sbNews').hidden"))
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.5 * {D}; changed(p); }}")
    settle()
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 2.5 * {D}; changed(p); }}")
    settle()
    mini()
    waiting = unread()
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === 'Publish the app')); changed(p); }}")
    settle()
    ok(f'a tick puts it back on pace: the news is no longer true, and goes ({waiting} then {unread()})', waiting == ['behind_more:Garden planner'] and unread() == [])
    ev(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.text === 'Publish the app'); untickTask(p, t, null, {{ log: false }}); changed(p); }}")
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'finish', days: 1, lastWorked: Date.now() - 3600e3, pickedAt: Date.now() }}; changed(p); }}")
    settle()
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.2 * {D}; changed(p); }}")
    settle()
    s = say()
    ok(f'Work until finished with a day gone by: "Nothing finished here for a day." ({s and s["text"]})', s and s['text'] == 'Nothing finished here for a day. This task gets us moving.')
    close_say()
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'none', days: 1, lastWorked: null, pickedAt: null }}; changed(p); }}")
    settle()

    # ---------- due today, and Proxima for a building with no leader ----------
    today = ev("() => ymd()")
    ev(f"""() => {{ const p = getProject('{gp}'); p.todos.find(t => t.text === 'Save a plan as a file').due = '{today}'; p.todos.find(t => t.text === 'Add plant icons').due = '{today}';
        const q = getProject('{nc}'); q.todos.find(t => t.text === 'Build the block art skill').due = '{today}'; changed(p); changed(q); }}""")
    settle()
    ok('a date set to today in the middle of the day is not news: due today is the day\'s first open', unread() == [])
    ev("() => { const s = JSON.parse(localStorage.getItem('nullovation-city:news')); s.dueDay = '2000-01-01'; localStorage.setItem('nullovation-city:news', JSON.stringify(s)); News.check(); }")
    settle()
    s = say()
    ok(f'the day\'s first open: one bubble, 1 / 2, the leader first, a red dot on the next arrow ({s and (s["text"], s["task"], s["count"], s["dotNext"])})',
       s and s['text'] == '2 tasks are due today. This one is first up.' and s['task'] == 'Save a plan as a file' and s['count'] == '1 / 2' and s['next'] and not s['prev'] and s['dotNext'])
    t = tiles()
    ok(f'News: Talal with !, then Proxima for the building with no leader ({t})', t == [['ld:' + lid, '!', 'Talal', True], ['px', '!', 'Proxima', True]])
    pg.screenshot(path=str(SHOTS / '401-news-two.png'))
    pg.click('#ldSayNext'); settle(200)
    s = say()
    ok(f'Next goes on to Proxima, saying the leaders\' line for its building ({s and (s["name"], s["where"], s["text"], s["count"])})',
       s and s['name'] == 'Proxima Pace' and s['role'] == 'Productivity Inspector' and s['where'] == 'Nullovation City·Build the block art skill' and s['text'] == 'This task is due today.'
       and s['count'] == '2 / 2' and not s['next'] and s['prev'] and not s['dotPrev'])
    seen = ev("() => News._test.state().items.filter(x => x.moment.startsWith('due')).map(x => [x.moment, !!x.seen]).sort()")
    ok(f'paging no longer reads (0.1.96): both still wait in News, each now seen, no dot left; the bubble stays ({unread()}, {seen})',
       unread() == ['due_many:Garden planner', 'due:Nullovation City'] and seen == [['due', True], ['due_many', True]] and say() is not None)
    close_say()
    s = say()
    ok(f'the x reads the page it is on, and the page before shows ({unread()})', unread() == ['due_many:Garden planner'] and s and s['name'] == 'Talal' and s['count'] == '')
    close_say()
    ok('the last x closes the bubble: both read, and News empties', say() is None and unread() == [] and tiles() == [])
    ev(f"""() => {{ for (const id of ['{gp}', '{nc}']) {{ const p = getProject(id); p.todos.forEach(t => t.due = ''); changed(p); }} }}""")

    # ---------- one task from done ----------
    for text in ['Draw the beds on a grid', 'Save a plan as a file']:
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === {json.dumps(text)})); changed(p); }}")
    settle()
    ok('ticks that leave two open are not news', unread() == [])
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === 'Add plant icons')); changed(p); }}")
    settle()
    ok(f'the tick that leaves one is news that waits in News: no bubble by itself any more (0.1.96) ({unread()})', say() is None and unread() == ['one_left:Garden planner'])
    face_of('ld:' + lid)
    s = say()
    ok(f'its face says it: "{{milestone}} is one task from done: this one", a News page, the task in its line ({s and (s["type"], s["text"], s["task"])})', s and s['type'] == 'news'
       and s['text'] == 'First release is one task from done: this one. Finish it and we throw a street party.' and s['task'] == 'Tune the watering reminders')
    mini()
    ev(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.text === 'Add plant icons'); untickTask(p, t); changed(p); tickTask(p, t); changed(p); }}")
    settle()
    ok('unticking takes it away, and ticking again the same day says nothing new', unread() == [] and say() is None)
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === 'Tune the watering reminders')); changed(p); }}")
    settle()
    ok(f'the last tick finishes it: the news is no longer true, and goes (Proxima has the party, waiting in News since 0.1.96) ({ev("() => Proxima.waiting()")})', unread() == [] and ev("() => Proxima.waiting()") == 1)
    for _ in range(4):                                              # her party heard, with her x, out of the way
        if not ev("() => Proxima.waiting()"): break
        ev("() => { if (document.querySelector('#pxSay').hidden) Proxima.open(); document.querySelector('#pxSayClose').click(); }"); settle(200)
    ev(f"() => {{ const p = getProject('{gp}'); for (const t of p.todos) untickTask(p, t, null, {{ log: false }}); changed(p); }}")
    settle()

    # ---------- the line's task and its building, as links; pictures that load late (0.1.60) ----------
    plan = tid('Save a plan as a file')
    ev(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Save a plan as a file', round: 'Plans, Round 2' }}, {{ ref: {{ tid: '{plan}' }} }})")
    settle()
    link = ev("""() => { const a = document.querySelector('#ldSayWhere .ld-task'); return a ? { text: a.textContent, tag: a.tagName, title: a.title, color: getComputedStyle(a).color, task: a.dataset.task,
        line: document.querySelector('#ldSayText').textContent, inWords: !!document.querySelector('#ldSayText .ld-task') } : null; }""")
    ok(f'the task is a link in its own color, in its own line after the building, the words saying "this task" (a button until 0.1.95, in the words until 0.1.96) ({link})', link and link['tag'] == 'A'
       and link['text'] == 'Save a plan as a file' and link['color'] == 'rgb(255, 210, 122)' and link['task'] == plan and link['line'] == 'Claude attached a wizard round to this task: Plans, Round 2.' and not link['inWords'])
    bld = ev("() => { const b = document.querySelector('#ldSayWhere .ld-say-bld'); return b ? [b.tagName, b.textContent, b.title] : null; }")
    ok(f'the building is a button too ({bld})', bld == ['BUTTON', 'Garden planner', 'Show Garden planner on the map'])
    ev("() => MapView.setCam({ x: -400, y: 200, z: 2 })"); settle(300)
    pg.click('#ldSay .ld-say-bld'); settle(900)
    ok('a click on the building goes to it on the map, opens nothing, and the bubble stays',
       ev(f"() => {{ const a = MapView.anchors('{gp}'), w = document.querySelector('#mapWrap'); return Math.abs(a.baseX - w.clientWidth / 2) < 60; }}") and not ev("() => FullView.isOpen()") and say() is not None)
    ev(f"() => News.add(getProject('{nc}'), 'added', {{ what: '1 link' }})"); settle()
    ok(f'what Claude added does not join it: it waits in News (0.1.96) ({unread()})', (say() or {}).get('count') == '' and 'added:Nullovation City' in unread())
    ev(f"() => News.add(getProject('{nc}'), 'round', {{ task: 'Build the block art skill', round: 'Blocks, Round 1' }}, {{ ref: {{ tid: '{tid('Build the block art skill', nc)}' }} }})"); settle()
    ok('with another page behind it, 1 / 2', (say() or {}).get('count') == '1 / 2')
    pg.click('#ldSay .ld-task'); settle(900)
    shown = ev("() => FullView.isOpen() && FullView.currentId() === '" + gp + "' ? (document.querySelector('#pvTaskName') || {}).textContent : null")
    ok(f'a click on the task opens it in its project, its panel beside the view ({shown})', shown == 'Save a plan as a file')
    ok(f'going to the task closes the bubble, the leader card inside reading its page; the rest waits in News ({unread()})', say() is None and unread() == ['round:Nullovation City', 'added:Nullovation City'])
    pg.screenshot(path=str(SHOTS / '404-news-task-link.png'))
    ev("() => FullView.close()"); ev("() => MapView.deselect()"); settle(300)
    ev("() => { const s = JSON.parse(localStorage.getItem('nullovation-city:news')); s.items = []; localStorage.setItem('nullovation-city:news', JSON.stringify(s)); }")
    # pictures that load after the bubble opened: the leader's portrait (what Claude added waits in News since 0.1.96: its face opens it)
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: '1 link' }})")   # its leader's (a round is Quill's since 0.1.69)
    settle()
    face_of('ld:' + lid)
    ok('before its portrait loads, the leader shows its silhouette', ev("() => !document.querySelector('#ldSayFace img') && !!document.querySelector('#ldSayFace svg')"))
    ev(f"""async () => {{ const l = DB.leaders[0]; await Store.putArt(portraitKey(l.id), PORTRAITS.gus); l.portrait = true; await Leaders.loadAll(); }}""")
    settle(300)
    ok('once it loads, the bubble and the face in News show the portrait', ev("() => !!document.querySelector('#ldSayFace img') && !!document.querySelector('#newsList .news-tile img')"))
    art = 'data:image/png;base64,' + base64.b64encode(open(fixture('test-still.png'), 'rb').read()).decode()
    ev(f"async () => {{ const p = getProject('{gp}'); p.art = {{ has: true, includesPlot: false }}; await Art.set(p.id, {json.dumps(art)}); }}")
    settle(300)
    bb = ev("() => { const w = document.querySelector('#ldSayWhere'); return w && [!!w.querySelector('canvas'), (w.querySelector('.ld-say-bld') || {}).textContent]; }")
    ok(f'the building is named in the task\'s line, a button with no picture since 0.1.96: its own art loading leaves the bubble as it was ({bb})', bb == [False, 'Garden planner'] and say() is not None)
    pg.screenshot(path=str(SHOTS / '405-news-late-pictures.png'), clip=pg.query_selector('#ldSay').bounding_box())
    ev(f"async () => {{ const p = getProject('{gp}'), l = DB.leaders[0]; p.art = {{ has: false, includesPlot: false }}; Art.drop(p.id); await Store.deleteArt(portraitKey(l.id)); l.portrait = false; await Leaders.loadAll(); }}")
    close_say()

    # ---------- Claude's additions: an Attachment page, waiting in News, each thing whole with Delete (0.1.96, C1) ----------
    ev(f"""() => {{ const p = getProject('{gp}'); const t = {{ id: 'tnew1', text: 'Mulch the beds', description: '', done: false, doneAt: null, due: '', milestoneId: 'm_first' }}; p.todos.push(t);
        p.notes.push({{ id: 'nnew1', title: 'Soil', text: 'Loam', at: Date.now() }}); changed(p);
        News.report(p, {{ summary: 'Mulch and soil', undo: {{ todos: ['tnew1'], ms: [], notes: ['nnew1'], links: [], rounds: [] }} }}); News.claude(); }}""")
    settle()
    ok(f'what Claude added waits in News: no bubble by itself (0.1.96) ({unread()})', say() is None and unread() == ['added:Garden planner'])
    face_of('ld:' + lid)
    s = say()
    dels = ev("() => [...document.querySelectorAll('#ldSay .lc-atts .ld-del')].map(x => x.textContent)")
    ok(f'its face opens it: "Claude added a task, Mulch the beds, and a note, Soil.", each with Delete in place of Undo ({s and (s["type"], s["text"], s["acts"])}, {dels})', s and s['type'] == 'attach'
       and s['text'].startswith('Claude added a task, Mulch the beds, and a note, Soil.') and s['acts'] == ['Go to it'] and dels == ['Delete', 'Delete'])
    pg.click('#ldSay .lc-att:not(.lc-att-note) .ld-del'); settle()
    ok('Delete takes the task out of the city; the page stays for the note', ev(f"() => !getProject('{gp}').todos.some(t => t.id === 'tnew1')") and say() is not None
       and ev("() => document.querySelectorAll('#ldSay .ld-del').length") == 1)
    pg.click('#ldSay .lc-att-note .ld-del'); settle()
    ok('the last Delete takes the note too, reads the news and closes the bubble', ev(f"() => !getProject('{gp}').notes.some(n => n.id === 'nnew1')") and unread() == [] and say() is None)
    ok('and its toast has Undo', ev("() => { const t = document.querySelector('#toast'); return t.textContent.includes('Deleted Soil.') && [...t.querySelectorAll('button')].some(b => b.textContent === 'Undo'); }"))

    # ---------- a click on a face: the bubble stays; Esc minimizes it ----------
    ev(f"() => News.add(getProject('{gp}'), 'week_quiet', {{ task: 'Publish the app' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())), tid: '{tid('Publish the app')}' }}, key: 'week:q' }})")
    settle()
    ok('the week waits with its leader: no bubble opens', say() is None and unread() == ['week_quiet:Garden planner'] and tiles()[0][0] == 'ld:' + lid)   # a round's answers are Quill's since 0.1.69 (test44)
    ev(f"() => News.add(getProject('{gp}'), 'week', {{ n: 3, task: 'Draw the beds on a grid' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:x' }})")
    settle()
    ok(f'two waiting: the face counts them ({tiles()})', tiles() == [['ld:' + lid, '2', 'Talal', True]])
    pg.click('#newsList .news-face'); settle(300)
    s = say()
    ok(f'a click on the face opens its bubble, the oldest first, 1 / 2, the arrows in its head ({s and (s["text"], s["task"], s["acts"], s["count"])})',
       s and s['text'] == 'Quiet week: nothing finished. This task is a good start.' and s['task'] == 'Publish the app' and s['acts'] == ['Go to it'] and s['count'] == '1 / 2' and s['next'] and not s['prev'])
    ok('the focus moves into the bubble', ev("() => document.querySelector('#ldSay').contains(document.activeElement)"))
    ok('opened by a click, it stays', say() is not None)
    pg.click('#ldSay .ld-go'); settle(900)
    ok('Go to it glides the map to the building and the bubble stays', say() is not None and ev(f"() => {{ const a = MapView.anchors('{gp}'), w = document.querySelector('#mapWrap'); return Math.abs(a.baseX - w.clientWidth / 2) < 60; }}"))
    pg.keyboard.press('Escape'); settle(300)
    ok(f'Esc minimizes it (0.1.96): nothing read, both still wait ({unread()})', say() is None and unread() == ['week_quiet:Garden planner', 'week:Garden planner'] and tiles() == [['ld:' + lid, '2', 'Talal', True]])
    ok('the focus goes back to the face', ev("() => document.activeElement && document.activeElement.classList.contains('news-face')"))
    ev(f"() => News.add(getProject('{nc}'), 'week_quiet', {{ task: 'Round 3: decide the block art loop' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:y' }})")
    settle()
    pg.hover('.news-tile[data-k="px"]')
    pg.click('.news-tile[data-k="px"] .news-dismiss'); settle()
    ok('each face has its own dismiss: Proxima\'s news read unheard, Talal\'s still waiting', unread() == ['week_quiet:Garden planner', 'week:Garden planner'] and [x[0] for x in tiles()] == ['ld:' + lid])

    # ---------- the status card says the building's news, a page at a time, and reads the page it shows ----------
    CARD = """() => { const l = document.querySelector('#bubble .b-leader'); return l ? { says: [...l.querySelectorAll('.ld-says')].map(x => x.textContent), task: (l.querySelector('.lc-tline') || {}).textContent,
        name: l.querySelector('.lc-nm').textContent, face: l.querySelector('.lc-face .ld-face').offsetWidth, flip: (l.querySelector('.lc-pgn') || {}).textContent || '' } : null; }"""
    ev(f"() => MapView.select('{gp}')"); settle(500)
    sc = ev(CARD)
    ok(f'opening the status card: its leader says the news there, one page at a time (0.1.96) ({sc})', sc and sc['says'] == ['Quiet week: nothing finished. This task is a good start.'] and sc['task'] == 'Publish the app'
       and sc['name'] == 'Talal' and sc['face'] == 48 and sc['flip'] == '1 / 2')
    ok(f'and the page it shows is read, only that one: the week still waits ({unread()})', unread() == ['week:Garden planner'] and tiles() == [['ld:' + lid, '!', 'Talal', True]])
    pg.click('#ldFlipNext-card'); settle(300)
    sc = ev(CARD)
    ok(f'its next page, read as it shows: Talal leaves News ({sc})', sc and sc['says'] == ['Last week we finished 3 tasks. This one is next.'] and sc['task'] == 'Draw the beds on a grid' and sc['flip'] == '2 / 2'
       and unread() == [] and tiles() == [])
    ok('its task is a link there too (0.1.60), in the task\'s line', ev("() => [...document.querySelectorAll('#bubble .b-leader .ld-task')].map(a => a.textContent)") == ['Draw the beds on a grid'])
    pg.screenshot(path=str(SHOTS / '402-news-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    ev("() => Bubble.refresh()"); settle(200)
    sc = ev(CARD)
    ok('the card keeps saying it while it stays open', sc and sc['says'] == ['Last week we finished 3 tasks. This one is next.'] and sc['flip'] == '2 / 2')
    ev(f"() => FullView.open('{gp}')"); settle(600)
    lc = ev("() => [[...document.querySelectorAll('#pvLeader .ld-says')].map(x => x.textContent), (document.querySelector('#pvLeader .lc-pgn') || {}).textContent]")
    ok(f'stepping inside, the leader card says the same pages, in place of the greeting ({lc})', lc == [['Quiet week: nothing finished. This task is a good start.'], '1 / 2'])
    pg.click('#pvLeader .ld-task'); settle(500)
    ok('a click on its task there opens the task beside the view', ev("() => (document.querySelector('#pvTaskName') || {}).textContent") == 'Publish the app')
    ev("() => FullView.close()"); ev("() => MapView.deselect()"); settle(300)
    ev(f"() => FullView.open('{gp}')"); settle(500)
    lc = ev("() => [[...document.querySelectorAll('#pvLeader .ld-says')].map(x => x.textContent), (document.querySelector('#pvLeader .lc-tline') || {}).textContent]")
    ok(f'closed and opened again: the greeting is back, the next task in its line ({lc})', lc == [[ev(f"() => leaderGreeting(getProject('{gp}'), Date.now(), true)")], 'Draw the beds on a grid']
       and lc[0][0].endswith('This one is next.'))
    ev("() => FullView.close()"); ev("() => MapView.deselect()"); settle(300)
    ev(f"() => {{ MapView.select('{nc}'); }}"); settle(400)
    ok('a building with no leader and nothing to say has no line in its card', ev("() => !document.querySelector('#bubble .b-leader')"))
    ev(f"() => News.add(getProject('{nc}'), 'week_quiet', {{ task: 'Round 3: decide the block art loop' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:z' }})"); settle()
    sc = ev("() => { const l = document.querySelector('#bubble .b-leader'); return l ? [l.querySelector('.lc-nm').textContent, [...l.querySelectorAll('.ld-says')].map(x => x.textContent), (l.querySelector('.lc-tline') || {}).textContent] : null; }")
    ok(f'news arriving while its card shows: Proxima says it there, for the building with no leader ({sc})', sc == ['Proxima Pace', ['Quiet week: nothing finished. This task is a good start.'], 'Round 3: decide the block art loop']
       and unread() == [])
    ev("() => MapView.deselect()"); settle(300)

    # ---------- several at once ----------
    ev("() => News.hide()")
    ev(f"""() => {{ const p = getProject('{gp}'), q = getProject('{nc}');
        News.add(q, 'added', {{ what: '2 links' }}); News.add(p, 'round', {{ task: 'Publish the app', round: 'Launch plan, Round 1' }}, {{ ref: {{ tid: '{tid('Publish the app')}' }} }});
        News.add(q, 'round', {{ task: 'Build the block art skill', round: 'Blocks, Round 2' }}, {{ ref: {{ tid: '{tid('Build the block art skill', nc)}' }} }}); }}""")
    settle()
    s = say()
    ok(f'news while a bubble shows joins it, one more page; what Claude added waits in News (0.1.96) ({s and s["count"]}, {unread()})', s and s['count'] == '1 / 2' and 'added:Nullovation City' in unread())
    close_say()
    ok(f'the x reads only the page it showed, and the next one shows; the one not reached waits with its leader ({unread()})', len(unread()) == 2 and (say() or {}).get('count') == ''
       and 'round:Nullovation City' in unread())
    mini()
    ev("() => { const s = JSON.parse(localStorage.getItem('nullovation-city:news')); s.items = []; localStorage.setItem('nullovation-city:news', JSON.stringify(s)); }")
    ev("() => News.check()"); settle()

    # ---------- Gus: first in News, his report in his bubble ----------
    ev("() => Garbage.setOn(true)")
    ev(f"() => {{ const p = getProject('{nc}'); p.todos[0].due = ymd(Date.now() - 3 * {D}); p.todos[1].due = ymd(Date.now() - 2 * {D}); changed(p); Garbage.refresh(); Gus.render(); }}")
    settle()
    ev(f"() => News.add(getProject('{gp}'), 'week', {{ n: 2, task: 'Draw the beds on a grid' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:g' }})"); settle()
    t = tiles()
    ok(f'Gus shows first while the city has garbage, with his count of tasks and no dismiss ({t})', t[0] == ['gus', '2', 'Gus', False] and t[1][0] == 'ld:' + lid)
    pg.click('.news-tile[data-k="gus"] .news-face'); settle(300)
    g = ev("() => ({ shown: !document.querySelector('#gusSay').hidden, report: $('#gusReport').textContent, fix: $('#gusFix').textContent, rows: [...document.querySelectorAll('#gusSay .gus-row')].map(x => x.textContent), face: document.querySelector('#gusSayFace').offsetWidth })")
    ok(f'a click opens his bubble with his report: overdue, Start with, and his rows ({g})',
       g['shown'] and g['report'] == "You have 2 overdue tasks. Let's clean them up." and g['fix'].startswith('Start with ') and g['rows'] == ['Nullovation City: 2 overdue tasks'] and g['face'] == 100)
    pg.screenshot(path=str(SHOTS / '403-news-gus.png'))
    ok('opened from his face, it stays', ev("() => !document.querySelector('#gusSay').hidden"))
    pg.click('#gusSay .gus-row'); settle(400)
    ok('a row goes to its building', ev("() => App.selectedId") == nc)
    ev("() => MapView.deselect()")
    pg.click('#gusSayClose'); settle(300)
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'pace', days: 1, lastWorked: Date.now() - 3600e3, pickedAt: Date.now() - 9 * {D} }}; changed(p); }}"); settle()
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.5 * {D}; changed(p); }}"); settle()
    ok('a leader\'s bubble up', say() is not None)
    ev("() => Gus.say('The city is getting dirty! We should do something about it.')"); settle(200)
    ok('Gus speaks: the leader gives way', say() is None and ev("() => !document.querySelector('#gusSay').hidden"))
    pg.wait_for_timeout(1500)
    ok('his bubble stays until closed (0.1.96), the leader waiting', say() is None and ev("() => !document.querySelector('#gusSay').hidden"))
    pg.click('#gusSayMin'); settle(900)
    s = say()
    ok(f'and once he is minimized, the leader says it again after him ({s and s["moment"]})', s and s['moment'] == 'behind')
    close_say()
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'none', days: 1, lastWorked: null, pickedAt: null }}; changed(p); const q = getProject('{nc}'); q.todos.forEach(t => t.due = ''); changed(q); Garbage.refresh(); Gus.render(); }}")
    settle()

    # ---------- Reports: the leader's face beside its building ----------
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === 'Draw the beds on a grid')); changed(p); const q = getProject('{nc}'); tickTask(q, q.todos[0]); changed(q); }}")
    ev("() => Reports.open()"); settle(500)
    rows = ev("() => [...document.querySelectorAll('#rpByProject .rp-row')].map(r => [r.querySelector('.rp-name').textContent, r.querySelector('.rp-leader') ? r.querySelector('.rp-leader').getAttribute('aria-label') : null])")
    ok(f'Reports, By project: the leader\'s face beside its building\'s row, none for a building with no leader ({rows})', sorted(rows) == [['Garden planner', 'Led by Talal'], ['Nullovation City', None]])
    ev("() => Reports.close()")

    # ---------- what is kept ----------
    ev(f"() => News.add(getProject('{gp}'), 'week', {{ n: 1, task: 'Save a plan as a file' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:k' }})"); settle()
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: '1 link' }})"); settle()
    ev(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Publish the app', round: 'Launch plan, Round 2' }}, {{ ref: {{ tid: '{tid('Publish the app')}' }}, undo: {{ todos: [], ms: [], notes: [], links: [], rounds: [] }} }})"); settle()
    s = say()
    ok(f'a round that opened by itself has Undo while the page stays open ({s and s["acts"]})', s and s['acts'] == ['Undo', 'Go to it'])
    mini()
    ok('the city keeps nothing new: the project and the leader as they were', ev(f"() => Object.keys(getProject('{gp}')).sort().join(',')") == before_keys
       and ev("() => Object.keys(DB.leaders[0]).sort().join(',')") == 'color,createdAt,id,name,portrait,role')
    pg.reload(); pg.wait_for_timeout(2200)
    ok('after a reload, the news still waits, and what already opened by itself does not open again',
       sorted(ev("() => News.items().map(it => it.moment)")) == ['added', 'round', 'week', 'week'] and ev("() => document.querySelector('#ldSay').hidden"))
    face_of('ld:quill')
    ok('Undo lasts while the page is open, as a toast\'s: after a reload the news has none', 'Undo' not in (say() or {}).get('acts', ['Undo']))
    close_say()

    # ---------- Tick it: the building's leader says it (0.1.63, Open in Claude Panel D1) ----------
    tk = lambda pid: ev(f"""() => {{ const p = getProject('{pid}'), t = p.todos.find(x => !x.done && !x.repeat); ClaudeWork.tick(p, t);
        const el = document.querySelector('#toast'), lead = el.querySelector('.toast-lead');
        return {{ task: t.text, lead: !!lead, name: lead ? lead.querySelector('.ld-name').textContent : '', where: lead ? lead.querySelector('.toast-who span').textContent : '',
          face: lead ? (lead.querySelector('.ld-face') || {{}}).offsetWidth || 0 : 0, msg: (el.querySelector('.toast-msg') || el.firstChild).textContent }}; }}""")
    r = tk(gp)
    ok(f'Tick it in a building with a leader: the leader says it, face at 40, name and building ({r})', r['lead'] and r['name'] == 'Talal' and r['where'] == 'Garden planner'
       and r['face'] == 40 and r['msg'] == 'Ticked off: ' + r['task'] + '.')
    settle(300)
    r = tk(nc)
    ok(f'in one with no leader, the toast says it plainly ({r})', not r['lead'] and r['msg'] == 'Ticked off: ' + r['task'] + '.')
    b.close()
print(errors or 'no console errors')
