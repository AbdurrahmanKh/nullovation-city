"""One leader card in three places (0.1.96, One Leader Card, Rounds 1 and 2, and the triggers list he approved).

The leader's bubble, the status card and the leader card are one card: every message a page with its type (an icon and
a label in its color), "< 1 / 3 >" with a red dot toward a page not seen, the task in its own line and "this task" in
the words, an x on every page (an ask only comes off the bubble and the status card), Minimize in place of closing by
itself, the greeting on the status card, the leader card's extras, what Claude added whole with Delete, a round's
answers updated in place, and Gus and Proxima on the same card, Proxima's news waiting in News."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
def S(session, state, cwd, mins=0, **kw):
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(cwd)}, at: {at}, since: {at} - 120000, started: {at} - 300000{extra} }})"
GARDEN = 'C:\\Users\\me\\garden'
T1 = 'Get Claude to understand the game and its art'

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t61')) { sessionStorage.setItem('nc-t61', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof News !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(800)
    js = pg.evaluate
    for k in ['#gusSay', '#pxSay', '#ldSay']:
        js(f"() => {{ const x = document.querySelector('{k}'); if (x && !x.hidden) {{ const m = x.querySelector('.lc-min'); if (m) m.click(); }} }}")
    js("() => { News._test.forget(); Proxima._test.forget(); News._test.typeMs(0); }")
    gp = js("() => DB.projects.find(p => p.name === 'Garden planner').id")
    js(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: uid('l'), label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true }});
      const l = blankLeader({{ name: 'Ahmed', role: 'Mine Supervisor', color: '#7FD6B5' }}); DB.leaders.push(l); p.leader = l.id;
      addTasks(p, [{{ text: {json.dumps(T1)}, description: '', due: '' }}], {{ id: p.milestones[0].id }}); persistNow(); }}""")
    nxt = js(f"() => nextTask(getProject('{gp}')).text")

    # ---------- the types and the card's words ----------
    ty = js("() => Object.fromEntries(Object.entries(NEWS_TYPES).map(([k, v]) => [k, [v.name, v.color]]))")
    ok(f'seven types, the three that wait on you red, the wizard\'s green, an attachment violet, heads up yellow, news grey ({ty})', list(ty) == ['critical', 'approval', 'answer', 'wizard', 'headsup', 'attach', 'news']
       and ty['critical'][1] == ty['approval'][1] == ty['answer'][1] == '#FF4D5E' and ty['wizard'][1] == '#74C997' and ty['attach'][1] == '#B58CFF' and ty['headsup'][1] == '#FFE03D' and ty['news'][0] == 'News')
    m = js("""() => [['failed', {}], ['t3closed', {}], ['asks', {}], ['waiting', { wait: 'approval' }], ['waiting', { wait: 'question' }], ['waiting', { wait: 'form' }], ['round', {}], ['answers', {}],
      ['behind', {}], ['due_many', {}], ['added', {}], ['finished', {}], ['one_left', {}], ['week', {}], ['working', {}]].map(([m, v]) => newsType(m, v))""")
    ok(f'each trigger its type, as the approved list says ({m})', m == ['critical', 'critical', 'approval', 'approval', 'answer', 'answer', 'wizard', 'wizard', 'headsup', 'headsup', 'attach', 'news', 'news', 'news', 'news'])
    w = js("() => [leaderSay('due', { task: 'X' }, true), leaderSay('due_many', { task: 'X', n: 3 }, true), leaderSay('finished', { task: 'X' }, true), leaderSay('week', { task: 'X', n: 3 }, true), leaderSay('due', { task: 'X' })]")
    ok(f'the card\'s words say "this task", word for word as W1 approved; elsewhere the title stays ({w})', w == ['This task is due today.', '3 tasks are due today. This one is first up.', 'Claude handed this task back to you.',
       'Last week we finished 3 tasks. This one is next.', 'X is due today.'])

    # ---------- the bubble: Heads up opens by itself, News waits ----------
    js(f"""() => {{ const p = getProject('{gp}'), t = nextTask(p);
      News.add(p, 'behind_more', {{ task: t.text }}, {{ ref: {{ level: 2, tid: t.id }}, key: 'behind:' + p.id }});
      News.add(p, 'due_many', {{ task: t.text, n: 2 }}, {{ ref: {{ day: ymd(), tid: t.id }}, key: 'due:' + p.id + ':' + ymd() }});
      News.add(p, 'week', {{ task: t.text, n: 3 }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())), tid: t.id }}, key: 'week:' + p.id }}); }}""")
    pg.wait_for_timeout(700)
    bub = lambda: js("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null; const f = b.querySelector('.lc-face .ld-face, .lc-face');
      return { type: b.dataset.type, label: (b.querySelector('.lc-tname') || {}).textContent, n: (b.querySelector('#ldSayCount') || {}).textContent || '', text: b.querySelector('#ldSayText').textContent,
        where: (b.querySelector('#ldSayWhere') || {}).textContent, face: Math.round(b.querySelector('#ldSayFace').getBoundingClientRect().width), next: !!b.querySelector('#ldSayNext .lc-dot'), prev: !!b.querySelector('#ldSayPrev .lc-dot'),
        min: !!b.querySelector('#ldSayMin'), x: !!b.querySelector('#ldSayClose') }; }""")
    s = bub()
    ok(f'Heads up opens the bubble by itself, its label in the head, the week waiting ({s})', s and s['type'] == 'headsup' and s['label'] == 'Heads up' and s['n'] == '1 / 2'
       and s['text'] == "We're falling further behind. This task pulls us back.")
    ok(f'the task in its own line, after the building, the face 100 px, Minimize and the x in the head ({s and (s["where"], s["face"])})', s and s['where'] == 'Garden planner\u00b7' + nxt and s['face'] == 100 and s['min'] and s['x'])
    ok('a red dot on the next arrow: a page not seen yet', s and s['next'] and not s['prev'])
    pg.screenshot(path=str(SH / '610-card-bubble.png'), clip=pg.query_selector('#ldSay').bounding_box())
    pg.click('#ldSayNext'); pg.wait_for_timeout(200)
    s = bub()
    ok(f'the next page: the same task in the same place, no dot left ({s and (s["n"], s["text"])})', s and s['n'] == '2 / 2' and s['text'] == '2 tasks are due today. This one is first up.'
       and s['where'] == 'Garden planner\u00b7' + nxt and not s['next'] and not s['prev'])
    pg.wait_for_timeout(15000)
    ok('it no longer closes by itself after 14 seconds', bub() is not None)
    pg.click('#ldSayMin'); pg.wait_for_timeout(300)
    items = lambda: js(f"() => News.items().filter(it => it.pid === '{gp}').map(it => it.moment)")
    badge = lambda: js("() => { const t = [...document.querySelectorAll('#newsList .news-tile')].find(x => x.textContent.includes('Ahmed')); return t ? t.querySelector('.news-badge').textContent : null; }")
    ok(f'Minimize: the bubble goes, its pages wait in News, the week too ({items()}, {badge()})', bub() is None and items() == ['behind_more', 'due_many', 'week'] and badge() == '3')
    js("() => document.querySelector('#newsList .news-tile .news-face').click()"); pg.wait_for_timeout(400)
    s = bub()
    ok(f'a click on the face opens every page it has, News last ({s and s["n"]})', s and s['n'] == '1 / 3')
    pg.click('#ldSayNext'); pg.click('#ldSayNext'); pg.wait_for_timeout(200)
    s = bub()
    ok(f'News: grey, no buttons but Go to it ({s and (s["type"], s["text"])})', s and s['type'] == 'news' and s['text'] == 'Last week we finished 3 tasks. This one is next.'
       and js("() => [...document.querySelectorAll('#ldSay .ld-acts .btn')].map(x => x.textContent)") == ['Go to it'])
    pg.click('#ldSayClose'); pg.wait_for_timeout(300)
    ok(f'its x takes it away: out of News, the bubble on the page before ({items()})', items() == ['behind_more', 'due_many'] and (bub() or {}).get('n') == '2 / 2')
    pg.click('#ldSayClose'); pg.wait_for_timeout(200); pg.click('#ldSayClose'); pg.wait_for_timeout(300)
    ok(f'the last x closes the bubble, and News empties ({items()})', bub() is None and items() == [])

    # ---------- the status card: the greeting, the same pages ----------
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(800)
    g = js("""() => { const c = document.querySelector('#bubble .lc'); return c && { plain: c.classList.contains('plain'), says: c.querySelector('.ld-says').textContent, task: (c.querySelector('.lc-tline') || {}).textContent,
      face: Math.round(c.querySelector('.lc-face').getBoundingClientRect().width), x: !!c.querySelector('.lc-x') }; }""")
    ok(f'with nothing to say, the status card shows the greeting, its next task in the task\'s line, face 48 ({g})', g and g['plain'] and g['says'].endswith('This one is next.') and g['task'] == nxt and g['face'] == 48 and not g['x'])
    pg.screenshot(path=str(SH / '611-card-greeting.png'), clip=pg.query_selector('#bubble').bounding_box())
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)

    # ---------- Claude: one finish, a page per type; an ask's x; the leader card's extras ----------
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    close_settings(pg)
    settle = lambda ms=3600: pg.wait_for_timeout(ms)
    upd = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'task': T1, 'summary': 'Claude read the game and wrote what it understood.',
           'changes': [{'do': 'done', 'task': T1}, {'do': 'add-note', 'kind': 'status', 'task': T1, 'title': 'Where the understanding stands', 'text': '1. Read every scene.\n2. Wrote what each character wants.'}]}
    js(S('c1', 'working', GARDEN, task=T1, project='Garden planner')); settle()
    js(f"() => window.__sub.set('inbox/2026-11-27-0900-garden.json', {{ text: {json.dumps(json.dumps(upd))}, t: Date.now() }})"); settle()
    js(S('c1', 'done', GARDEN, mins=0, task=T1, project='Garden planner', reply='I read every scene.\n\nNext I check the art folder.')); settle()
    s = bub()
    ok(f'the finish opens the bubble on what needs your OK, alone: the attachment and the finish wait ({s and (s["type"], s["n"], s["text"])})', s and s['type'] == 'approval' and s['n'] == ''
       and s['text'].startswith('Claude wants your OK first: tick this task off.'))
    ok(f'News holds a page per type: Need Approval, Attachment, News ({items()})', items() == ['asks', 'added', 'finished'])
    ok('No in place of Dismiss', js("() => [...document.querySelectorAll('#ldSay .ld-acts .btn')].map(x => x.textContent)") == ['Tick it', 'No', 'Go to it'])
    pg.click('#ldSayClose'); pg.wait_for_timeout(300)
    pages = lambda where: js(f"() => News._test.pages('{gp}', '{where}').map(x => x.type)")
    ok(f'the x on an ask takes it off the bubble and the status card ({pages("card")})', bub() is None and pages('card') == ['attach', 'news'])
    ok(f'it waits on the leader card until answered ({pages("view")})', pages('view') == ['approval', 'attach', 'news'])
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(800)
    lc = js("""() => { const c = document.querySelector('#pvLeader .lc'); return c && { type: c.dataset.type, x: !!c.querySelector('.lc-x'), n: (c.querySelector('.lc-pgn') || {}).textContent,
      face: Math.round(c.querySelector('.lc-face').getBoundingClientRect().width) }; }""")
    ok(f'on the leader card the ask has no x, the face 100 px ({lc})', lc and lc['type'] == 'approval' and not lc['x'] and lc['n'] == '1 / 3' and lc['face'] == 100)
    pg.click('#ldFlipNext-view'); pg.wait_for_timeout(300)
    at = js("""() => { const c = document.querySelector('#pvLeader .lc'); return c && { type: c.dataset.type, says: c.querySelector('.ld-says').textContent, notes: [...c.querySelectorAll('.lc-note .pv-tnote-t')].map(x => x.textContent),
      del: [...c.querySelectorAll('.ld-del')].map(x => x.textContent) }; }""")
    ok(f'Attachment: the note whole, as under a task, with Delete ({at})', at and at['type'] == 'attach' and at['says'].startswith('Claude added a note, Where the understanding stands.')
       and at['notes'] == ['Where the understanding stands'] and at['del'] == ['Delete'])
    pg.screenshot(path=str(SH / '612-card-attachment.png'), clip=pg.query_selector('#pvLeader').bounding_box())
    pg.click('#pvLeader .ld-del'); pg.wait_for_timeout(400)
    gone = js(f"() => !allNotes(getProject('{gp}')).some(n => n.title === 'Where the understanding stands')")
    ok('Delete takes the note out of the city', gone)
    js("() => { const b = [...document.querySelectorAll('.toast button, #toast button')].find(x => x.textContent === 'Undo'); if (b) b.click(); }"); pg.wait_for_timeout(400)
    ok('and Undo in its toast brings it back', js(f"() => allNotes(getProject('{gp}')).some(n => n.title === 'Where the understanding stands')"))
    js(f"() => {{ for (let i = 0; i < 3; i++) {{ const c = document.querySelector('#pvLeader .lc'); if (c && c.dataset.type === 'news') break; document.querySelector('#ldFlipNext-view').click(); }} }}"); pg.wait_for_timeout(300)
    fin = js("""() => { const c = document.querySelector('#pvLeader .lc'); return c && { type: c.dataset.type, says: c.querySelector('.ld-says').textContent, times: (c.querySelector('.lc-times') || {}).textContent,
      said: [...c.querySelectorAll('.b-claude-said.whole')].map(x => x.textContent), last: [...c.querySelectorAll('.lc-last p')].map(x => x.textContent), btns: [...c.querySelectorAll('.ld-acts .btn')].length }; }""")
    ok(f'the finish on the leader card: when it worked, the summary whole, the last message whole, no buttons ({fin})', fin and fin['type'] == 'news' and fin['says'].startswith('Claude handed this task back to you.')
       and (fin['times'] or '').startswith('Started ') and 'worked 2 minutes' in fin['times'] and fin['times'].endswith('1 update') and fin['said'] == [upd['summary']]
       and fin['last'] == ['I read every scene.', 'Next I check the art folder.'] and fin['btns'] == 0)
    pg.screenshot(path=str(SH / '613-card-finish.png'), clip=pg.query_selector('#pvLeader').bounding_box())
    js("() => FullView.close()"); pg.wait_for_timeout(300)
    js("() => window.__cf.delete('c1.json')"); settle()

    # ---------- a round's answers: one message, its count brought up to date ----------
    js("() => News._test.forget()")
    a = js(f"""() => {{ const p = getProject('{gp}'), t = nextTask(p);
      const x = News.add(p, 'answers', {{ round: 'R', n: 3, total: 14 }}, {{ ref: {{ tid: t.id }}, key: 'answers:' + t.id }});
      const y = News.add(p, 'answers', {{ round: 'R', n: 7, total: 14 }}, {{ ref: {{ tid: t.id }}, key: 'answers:' + t.id }});
      return [x.id === y.id, News.items().filter(it => it.moment === 'answers').map(it => it.v.n)]; }}""")
    ok(f'a round\'s answers are one message, its count updated in place ({a})', a == [True, [7]])
    js("() => News._test.forget()")

    # ---------- Gus and Proxima on the same card ----------
    gs = js("() => { Gus.say('The city is getting dirty! We should do something about it.'); const c = document.querySelector('#gusCard'); return [c.dataset.type, c.querySelector('.lc-tname').textContent, !!document.querySelector('#gusSayMin')]; }")
    ok(f'Gus\'s word on the garbage: the card, Heads up, with Minimize ({gs})', gs == ['headsup', 'Heads up', True])
    js("() => document.querySelector('#gusSayMin').click()"); pg.wait_for_timeout(200)
    js(f"() => {{ const p = getProject('{gp}'); Proxima.announce(p, p.milestones[0], 3); }}"); pg.wait_for_timeout(500)
    px = js("() => [Proxima.waiting(), document.querySelector('#pxSay').hidden, !!document.querySelector('#newsList .news-tile[data-k=\"px\"]')]")
    ok(f'a street party waits in News with Proxima\'s face, no bubble by itself ({px})', px == [1, True, True])
    js("() => document.querySelector('#newsList .news-tile[data-k=\"px\"] .news-face').click()"); pg.wait_for_timeout(400)
    pc = js("() => { const b = document.querySelector('#pxSay'); return [b.hidden, b.querySelector('.lc-tname').textContent, document.querySelector('#pxSayRead').tagName, document.querySelector('#pxSayRead').textContent]; }")
    ok(f'her face opens her card, News, Go to it a link ({pc})', pc == [False, 'News', 'A', 'Go to it'])
    pg.screenshot(path=str(SH / '614-card-proxima.png'), clip=pg.query_selector('#pxSay').bounding_box())
    pg.click('#pxSayClose'); pg.wait_for_timeout(300)
    ok('her x: heard, and gone from News', js("() => [Proxima.waiting(), document.querySelector('#pxSay').hidden]") == [0, True])

    print('no console errors' if not errors else 'CONSOLE ERRORS: ' + ' | '.join(errors[:5]))
    b.close()
