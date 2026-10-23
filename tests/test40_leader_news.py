"""The leaders' news (0.1.59, and the task and the building as links at 0.1.60), the third piece of the leader UX: the side bar's News section in place of Urgent and
Gus's part, each leader's news in its own bubble at the map's top left (Proxima's for a building with no leader), the
moments that open by themselves and those that wait, 1 of N with Next, reading and dismissing, the status card and the
leader card saying a building's news, Gus's report in his bubble, the leaders' faces in Reports, and nothing new in the
city's data."""
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
    say = lambda: ev("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null;
        return { k: b.dataset.k, moment: b.dataset.moment, name: $('#ldSayName').textContent, role: $('#ldSayRole').textContent, where: $('#ldSayWhere').textContent, text: $('#ldSayText').textContent,
          acts: [...b.querySelectorAll('#ldSayActs button')].map(x => x.textContent), count: ($('#ldSayCount') || {}).textContent || '', face: (b.querySelector('#ldSayFace .ld-face, #ldSayFace .gus-face') || {}).offsetWidth || 0,
          left: Math.round(b.getBoundingClientRect().left - document.querySelector('#mapWrap').getBoundingClientRect().left), top: Math.round(b.getBoundingClientRect().top - document.querySelector('#mapWrap').getBoundingClientRect().top),
          color: getComputedStyle(b).getPropertyValue('--ld').trim() }; }""")
    unread = lambda: ev("() => News.items().map(it => it.moment + ':' + (getProject(it.pid) || {}).name)")
    settle = lambda ms=400: pg.wait_for_timeout(ms)
    close_say = lambda: (pg.click('#ldSayClose'), settle(300))
    ev("() => { News._test.sayMs(1500); Garbage.setOn(false); }")             # Gus waits for his own part, below

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
    ok(f'slipping behind its pace opens its leader\'s bubble by itself, with the line word for word ({s and s["text"]})',
       s and s['moment'] == 'behind' and s['text'] == 'We slipped behind our pace. Draw the beds on a grid puts us back on track.')
    ok(f'the bubble: the face at 100 px, the name and role, the building, and Go to it ({s})',
       s and s['face'] == 100 and s['name'] == 'Talal' and s['role'] == 'Head of Nullovations' and s['where'] == 'Garden planner' and s['acts'] == ['Go to it'] and s['count'] == '')
    ok(f'at the map\'s top left, where Gus and Proxima speak, in the leader\'s color ({s and (s["left"], s["top"], s["color"])})', s and s['left'] == 22 and s['top'] == 18 and s['color'].upper() == '#8FD0F7')
    ok('its building wears the hover ring while it shows', ev("() => MapView._lit()") == gp)
    t = tiles()
    ok(f'Talal shows in News with ! for one item, and a dismiss ({t})', t == [['ld:' + lid, '!', 'Talal', True]])
    ok('under each face the first word of its name, the tooltip saying it whole with the role', ev("() => document.querySelector('#newsList .news-face').title").startswith('Talal, Head of Nullovations: 1 piece of news.'))
    pg.screenshot(path=str(SHOTS / '400-news-behind.png'))
    pg.wait_for_timeout(1700)
    ok('opened by itself, it closes by itself and leaves the news waiting, unread', say() is None and unread() == ['behind:Garden planner'] and ev("() => MapView._lit()") is None)
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 2.5 * {D}; changed(p); }}")
    settle()
    s = say()
    ok(f'falling further behind replaces it, and says so ({s and s["text"]})', s and s['text'] == "We're falling further behind. Draw the beds on a grid pulls us back." and unread() == ['behind_more:Garden planner'])
    close_say()
    ok('closed, what it showed is read, and Talal leaves News', unread() == [] and tiles() == [] and ev("() => document.querySelector('#sbNews').hidden"))
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.5 * {D}; changed(p); }}")
    settle()
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 2.5 * {D}; changed(p); }}")
    settle()
    pg.wait_for_timeout(1700)
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
    ok(f'Work until finished with a day gone by: "Nothing finished here for a day." ({s and s["text"]})', s and s['text'] == 'Nothing finished here for a day. Draw the beds on a grid gets us moving.')
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
    ok(f'the day\'s first open: one bubble, 1 of 2, the leader first ({s and (s["text"], s["count"])})',
       s and s['text'] == '2 tasks are due today. First up: Save a plan as a file.' and s['count'] == '1 of 2' and 'Next' in s['acts'])
    t = tiles()
    ok(f'News: Talal with !, then Proxima for the building with no leader ({t})', t == [['ld:' + lid, '!', 'Talal', True], ['px', '!', 'Proxima', True]])
    pg.screenshot(path=str(SHOTS / '401-news-two.png'))
    pg.click('#ldSayNext'); settle(200)
    s = say()
    ok(f'Next goes on to Proxima, saying the leaders\' line for its building ({s and (s["name"], s["where"], s["text"], s["count"])})',
       s and s['name'] == 'Proxima Pace' and s['role'] == 'Productivity Inspector' and s['where'] == 'Nullovation City' and s['text'] == 'Build the block art skill is due today.' and s['count'] == '2 of 2' and 'Next' not in s['acts'])
    ok('Next went past the first: it is read, and the bubble stays now that you used it', unread() == ['due:Nullovation City'] and (pg.wait_for_timeout(1700), say())[1] is not None)
    close_say()
    ok('closed: both read, and News empties', unread() == [] and tiles() == [])
    ev(f"""() => {{ for (const id of ['{gp}', '{nc}']) {{ const p = getProject(id); p.todos.forEach(t => t.due = ''); changed(p); }} }}""")

    # ---------- one task from done ----------
    for text in ['Draw the beds on a grid', 'Save a plan as a file']:
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === {json.dumps(text)})); changed(p); }}")
    settle()
    ok('ticks that leave two open are not news', unread() == [])
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === 'Add plant icons')); changed(p); }}")
    settle()
    s = say()
    ok(f'the tick that leaves one: "{{milestone}} is one task from done" ({s and s["text"]})', s and s['text'] == 'First release is one task from done: Tune the watering reminders. Finish it and we throw a street party.')
    pg.wait_for_timeout(1700)
    ev(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.text === 'Add plant icons'); untickTask(p, t); changed(p); tickTask(p, t); changed(p); }}")
    settle()
    ok('unticking takes it away, and ticking again the same day says nothing new', unread() == [] and say() is None)
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.text === 'Tune the watering reminders')); changed(p); }}")
    settle()
    ok('the last tick finishes it: the news is no longer true, and goes (Proxima has the party)', unread() == [])
    ev("() => Proxima.hush(false)")
    ev(f"() => {{ const p = getProject('{gp}'); for (const t of p.todos) untickTask(p, t, null, {{ log: false }}); changed(p); }}")
    settle()

    # ---------- the line's task and its building, as links; pictures that load late (0.1.60) ----------
    plan = tid('Save a plan as a file')
    ev(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Save a plan as a file', round: 'Plans, Round 2' }}, {{ ref: {{ tid: '{plan}' }} }})")
    settle()
    link = ev("""() => { const a = document.querySelector('#ldSayText .ld-task'); return a ? { text: a.textContent, tag: a.tagName, title: a.title, color: getComputedStyle(a).color, task: a.dataset.task,
        line: document.querySelector('#ldSayText').textContent } : null; }""")
    ok(f'the task in the line is a button in its own color, the rest of the line as it was ({link})', link and link['tag'] == 'BUTTON' and link['text'] == 'Save a plan as a file'
       and link['color'] == 'rgb(255, 210, 122)' and link['task'] == plan and link['line'] == 'Claude attached a wizard round to Save a plan as a file: Plans, Round 2.')
    bld = ev("() => { const b = document.querySelector('#ldSayWhere .ld-say-bld'); return b ? [b.tagName, b.textContent, b.title] : null; }")
    ok(f'the building is a button too ({bld})', bld == ['BUTTON', 'Garden planner', 'Show Garden planner on the map'])
    ev("() => MapView.setCam({ x: -400, y: 200, z: 2 })"); settle(300)
    pg.click('#ldSay .ld-say-bld'); settle(900)
    ok('a click on the building goes to it on the map, opens nothing, and the bubble stays',
       ev(f"() => {{ const a = MapView.anchors('{gp}'), w = document.querySelector('#mapWrap'); return Math.abs(a.baseX - w.clientWidth / 2) < 60; }}") and not ev("() => FullView.isOpen()") and say() is not None)
    ev(f"() => News.add(getProject('{nc}'), 'added', {{ what: '1 link' }})"); settle()
    ok('with another item behind it, 1 of 2', (say() or {}).get('count') == '1 of 2')
    pg.click('#ldSay .ld-task'); settle(900)
    shown = ev("() => FullView.isOpen() && FullView.currentId() === '" + gp + "' ? (document.querySelector('#pvTaskTitle') || {}).value : null")
    ok(f'a click on the task opens it in its project, its panel beside the view ({shown})', shown == 'Save a plan as a file')
    ok(f'going to the task reads the news and closes the bubble; the other item waits ({unread()})', say() is None and unread() == ['added:Nullovation City'])
    pg.screenshot(path=str(SHOTS / '404-news-task-link.png'))
    ev("() => FullView.close()"); ev("() => MapView.deselect()"); settle(300)
    ev("() => { const s = JSON.parse(localStorage.getItem('nullovation-city:news')); s.items = []; localStorage.setItem('nullovation-city:news', JSON.stringify(s)); }")
    # pictures that load after the bubble opened: the leader's portrait and the building's own art
    ev(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Add plant icons', round: 'Icons, Round 3' }}, {{ ref: {{ tid: '{tid('Add plant icons')}' }} }})")
    settle()
    ok('before its portrait loads, the leader shows its silhouette', ev("() => !document.querySelector('#ldSayFace img') && !!document.querySelector('#ldSayFace svg')"))
    ev(f"""async () => {{ const l = DB.leaders[0]; await Store.putArt(portraitKey(l.id), PORTRAITS.gus); l.portrait = true; await Leaders.loadAll(); }}""")
    settle(300)
    ok('once it loads, the bubble and the face in News show the portrait', ev("() => !!document.querySelector('#ldSayFace img') && !!document.querySelector('#newsList .news-tile img')"))
    before = ev("() => document.querySelector('#ldSayWhere canvas').toDataURL()")
    art = 'data:image/png;base64,' + base64.b64encode(open(fixture('test-still.png'), 'rb').read()).decode()
    ev(f"async () => {{ const p = getProject('{gp}'); p.art = {{ has: true, includesPlot: false }}; await Art.set(p.id, {json.dumps(art)}); }}")
    settle(300)
    ok('once the building\'s own art loads, the bubble draws the building again with it', ev("() => document.querySelector('#ldSayWhere canvas').toDataURL()") != before)
    pg.screenshot(path=str(SHOTS / '405-news-late-pictures.png'), clip=pg.query_selector('#ldSay').bounding_box())
    ev(f"async () => {{ const p = getProject('{gp}'), l = DB.leaders[0]; p.art = {{ has: false, includesPlot: false }}; Art.drop(p.id); await Store.deleteArt(portraitKey(l.id)); l.portrait = false; await Leaders.loadAll(); }}")
    close_say()

    # ---------- Claude's additions: the leader says it, with Undo, in place of the toast ----------
    ev(f"""() => {{ const p = getProject('{gp}'); const t = {{ id: 'tnew1', text: 'Mulch the beds', description: '', done: false, doneAt: null, due: '', milestoneId: 'm_first' }}; p.todos.push(t);
        p.notes.push({{ id: 'nnew1', title: 'Soil', text: 'Loam', at: Date.now() }}); changed(p);
        News.add(p, 'added', {{ what: '1 task and a note' }}, {{ undo: {{ todos: ['tnew1'], ms: [], notes: ['nnew1'], links: [], rounds: [] }} }}); }}""")
    settle()
    s = say()
    ok(f'"Claude added 1 task and a note.", with Undo ({s and (s["text"], s["acts"])})', s and s['text'] == 'Claude added 1 task and a note.' and s['acts'] == ['Undo', 'Go to it'])
    toast_before = ev("() => document.querySelector('#toast').className")
    pg.click('#ldSay .ld-undo'); settle()
    ok('Undo takes back what Claude added, reads the news and closes the bubble', ev(f"() => !getProject('{gp}').todos.some(t => t.id === 'tnew1') && !getProject('{gp}').notes.some(n => n.id === 'nnew1')") and unread() == [] and say() is None)

    # ---------- a click on a face: the bubble stays; Esc closes it ----------
    ev(f"() => News.add(getProject('{gp}'), 'answers', {{ round: 'Leader UX, Round 1', n: 7, total: 8 }}, {{ ref: {{ tid: '{tid('Publish the app')}' }}, key: 'answers:x' }})")
    settle()
    ok('a round\'s answers wait with their leader: no bubble opens', say() is None and unread() == ['answers:Garden planner'] and tiles()[0][0] == 'ld:' + lid)
    ev(f"() => News.add(getProject('{gp}'), 'week', {{ n: 3, task: 'Draw the beds on a grid' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:x' }})")
    settle()
    ok(f'two waiting: the face counts them ({tiles()})', tiles() == [['ld:' + lid, '2', 'Talal', True]])
    pg.click('#newsList .news-face'); settle(300)
    s = say()
    ok(f'a click on the face opens its bubble, the answers first, with Open ({s and (s["text"], s["acts"], s["count"])})',
       s and s['text'] == 'Your answers are in for Leader UX, Round 1: 7 of 8.' and s['acts'] == ['Open', 'Go to it', 'Next'] and s['count'] == '1 of 2')
    ok('the focus moves into the bubble', ev("() => document.querySelector('#ldSay').contains(document.activeElement)"))
    pg.wait_for_timeout(1700)
    ok('opened by a click, it stays', say() is not None)
    pg.click('#ldSay .ld-go'); settle(900)
    ok('Go to it glides the map to the building and the bubble stays', say() is not None and ev(f"() => {{ const a = MapView.anchors('{gp}'), w = document.querySelector('#mapWrap'); return Math.abs(a.baseX - w.clientWidth / 2) < 60; }}"))
    pg.keyboard.press('Escape'); settle(300)
    ok('Esc closes it: the first read, the second still waiting', say() is None and unread() == ['week:Garden planner'] and tiles() == [['ld:' + lid, '!', 'Talal', True]])
    ok('the focus goes back to the face', ev("() => document.activeElement && document.activeElement.classList.contains('news-face')"))
    ev(f"() => News.add(getProject('{nc}'), 'week_quiet', {{ task: 'Round 3: decide the block art loop' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:y' }})")
    settle()
    pg.hover('.news-tile[data-k="px"]')
    pg.click('.news-tile[data-k="px"] .news-dismiss'); settle()
    ok('each face has its own dismiss: Proxima\'s news read unheard, Talal\'s still waiting', unread() == ['week:Garden planner'] and [x[0] for x in tiles()] == ['ld:' + lid])

    # ---------- the status card says the building's news, and reads it ----------
    ev(f"() => MapView.select('{gp}')"); settle(500)
    sc = ev("() => { const l = document.querySelector('#bubble .b-leader'); return l ? { says: [...l.querySelectorAll('.ld-says')].map(x => x.textContent), name: l.querySelector('.ld-name').textContent, face: l.querySelector('.ld-face').offsetWidth } : null; }")
    ok(f'opening the status card: its leader says the news there ({sc})', sc and sc['says'] == ['Last week we finished 3 tasks. Next up: Draw the beds on a grid.'] and sc['name'] == 'Talal' and sc['face'] == 48)
    ok('and it is read: Talal leaves News', unread() == [] and tiles() == [])
    ok('its task is a link there too (0.1.60)', ev("() => [...document.querySelectorAll('#bubble .b-leader .ld-task')].map(a => a.textContent)") == ['Draw the beds on a grid'])
    pg.screenshot(path=str(SHOTS / '402-news-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    ev("() => Bubble.refresh()"); settle(200)
    ok('the card keeps saying it while it stays open', ev("() => document.querySelectorAll('#bubble .b-leader .ld-says').length") == 1)
    ev(f"() => FullView.open('{gp}')"); settle(600)
    lc = ev("() => [...document.querySelectorAll('#pvLeader .ld-says')].map(x => x.textContent)")
    ok(f'stepping inside, the leader card says it too, in place of the greeting ({lc})', lc == ['Last week we finished 3 tasks. Next up: Draw the beds on a grid.'])
    pg.click('#pvLeader .ld-task'); settle(500)
    ok('a click on its task there opens the task beside the view', ev("() => (document.querySelector('#pvTaskTitle') || {}).value") == 'Draw the beds on a grid')
    ev("() => FullView.close()"); ev("() => MapView.deselect()"); settle(300)
    ev(f"() => FullView.open('{gp}')"); settle(500)
    lc = ev("() => [...document.querySelectorAll('#pvLeader .ld-says')].map(x => x.textContent)")
    ok(f'closed and opened again: the greeting is back ({lc})', lc == ['Welcome back. Next up: Draw the beds on a grid.'])
    ev("() => FullView.close()"); ev("() => MapView.deselect()"); settle(300)
    ev(f"() => {{ MapView.select('{nc}'); }}"); settle(400)
    ok('a building with no leader and nothing to say has no line in its card', ev("() => !document.querySelector('#bubble .b-leader')"))
    ev(f"() => News.add(getProject('{nc}'), 'week_quiet', {{ task: 'Round 3: decide the block art loop' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:z' }})"); settle()
    sc = ev("() => { const l = document.querySelector('#bubble .b-leader'); return l ? [l.querySelector('.ld-name').textContent, [...l.querySelectorAll('.ld-says')].map(x => x.textContent)] : null; }")
    ok(f'news arriving while its card shows: Proxima says it there, for the building with no leader ({sc})', sc == ['Proxima Pace', ['Quiet week: nothing finished. Round 3: decide the block art loop is a good start.']] and unread() == [])
    ev("() => MapView.deselect()"); settle(300)

    # ---------- several at once ----------
    ev("() => News.hide()")
    ev(f"""() => {{ const p = getProject('{gp}'), q = getProject('{nc}');
        News.add(q, 'added', {{ what: '2 links' }}); News.add(p, 'round', {{ task: 'Publish the app', round: 'Launch plan, Round 1' }}); }}""")
    settle()
    s = say()
    ok(f'news while a bubble shows joins it, as one more of N ({s and s["count"]})', s and s['count'] == '1 of 2')
    close_say()
    ok('closing reads only what it showed: the one not reached waits with its leader', len(unread()) == 1)
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
    pg.wait_for_timeout(1700)
    ok('opened from his face, it stays', ev("() => !document.querySelector('#gusSay').hidden"))
    pg.click('#gusSay .gus-row'); settle(400)
    ok('a row goes to its building', ev("() => App.selectedId") == nc)
    ev("() => MapView.deselect()")
    pg.click('#gusSayClose'); settle(300)
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'pace', days: 1, lastWorked: Date.now() - 3600e3, pickedAt: Date.now() - 9 * {D} }}; changed(p); }}"); settle()
    ev("() => Gus._test.sayMs(1200)")
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.5 * {D}; changed(p); }}"); settle()
    ok('a leader\'s bubble up', say() is not None)
    ev("() => Gus.say('The city is getting dirty! We should do something about it.')"); settle(200)
    ok('Gus speaks: the leader gives way', say() is None and ev("() => !document.querySelector('#gusSay').hidden"))
    pg.wait_for_timeout(2200)
    s = say()
    ok(f'and says it again after him ({s and s["moment"]})', s and s['moment'] == 'behind')
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
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: '1 link' }}, {{ undo: {{ todos: [], ms: [], notes: [], links: [], rounds: [] }} }})"); settle()
    pg.wait_for_timeout(1700)
    ok('the city keeps nothing new: the project and the leader as they were', ev(f"() => Object.keys(getProject('{gp}')).sort().join(',')") == before_keys
       and ev("() => Object.keys(DB.leaders[0]).sort().join(',')") == 'color,createdAt,id,name,portrait,role')
    pg.reload(); pg.wait_for_timeout(2200)
    ok('after a reload, the news still waits, and what already opened by itself does not open again',
       sorted(ev("() => News.items().map(it => it.moment)")) == ['added', 'week', 'week'] and ev("() => document.querySelector('#ldSay').hidden"))
    pg.click('#newsList .news-face'); settle(300)
    ok('Undo lasts while the page is open, as a toast\'s: after a reload the news has none', 'Undo' not in (say() or {}).get('acts', ['Undo']))
    close_say()
    b.close()
print(errors or 'no console errors')
