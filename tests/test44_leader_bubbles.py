"""Leader Bubbles, Round 2 (0.1.69): each trigger designed on its own.

Quill, the Pocket Wizard, is the city's voice for wizard rounds: he says a round Claude attached with no finish to sit
under, and a round's answers coming in, for every building (C1), and a leader of the city's own named Quill is him. A
round reads in a small popup with Open in wizard, from his bubble, the cards and Show the answers (C1). Claude writes
nothing in Activity but a round it attaches, and a round's answers write a line there (C2). A finish says "Claude handed
<task> back to you." (C1). A task going overdue writes a line in Activity, which draws no crowd (N2). The leader card
in the project view says what the status card says, with its buttons (N1). The city opens with a Claude folder held in
memory, as in test24 and test43."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, TEST_CITY, open_settings, close_settings, portrait_sum, PORTRAIT_SUM

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
CAPTURE = """window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (this.target === '_blank' || /^web[+]dwizard:/i.test(href)) { window.__opened.push([href, this.target, this.rel]); return; } return anchorClick.call(this); };"""
def S(session, state, cwd, mins=0, **kw):
    """A session file as the hooks write it, last heard from mins minutes ago."""
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(cwd)}, at: {at}, since: {at} - 120000, started: {at} - 300000{extra} }})"
GARDEN = 'C:\\Users\\me\\garden'
TITLE = 'Bed layout, Round 1'
ROUND = {'config': {'title': TITLE, 'tagline': 'The beds', 'product': 'Garden planner', 'needs_wizard': '0.4.0'}, 'questions': [
    {'id': 'L1', 'section': 'Beds', 'title': 'Layout', 'question': 'How should the beds be laid out?', 'options': ['A grid', 'Rows']},
    {'id': 'L2', 'section': 'Beds', 'title': 'Paths', 'question': 'How wide are the paths?', 'options': ['30 cm', '50 cm']}]}
ANSWERS = {'meta': {'tool': 'decision-wizard', 'wizard_version': '0.10.1', 'wizard_title': TITLE, 'total': 2, 'answered': 1, 'open': 1},
           'answers': [{'id': 'L1', 'issue': 'Layout', 'question': 'How should the beds be laid out?', 'status': 'picked', 'answer': 'A grid', 'comment': 'keep it simple'},
                       {'id': 'L2', 'issue': 'Paths', 'question': 'How wide are the paths?', 'status': 'open', 'answer': ''}]}

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t44')) { sessionStorage.setItem('nc-t44', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    ctx.add_init_script(CAPTURE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(600)
    js = pg.evaluate
    ids = js("() => Object.fromEntries(DB.projects.map(p => [p.name, p.id]))")
    gp, nc = ids['Garden planner'], ids['Nullovation City']
    tid = lambda pid, text: js(f"() => getProject('{pid}').todos.find(t => t.text === {json.dumps(text)}).id")
    js("""() => { const p = DB.projects.find(p => p.name === 'Garden planner');
      p.links.push({ id: uid('l'), label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true });
      const l = blankLeader({ name: 'Talal', role: 'Head of Gardens', color: '#7FD6B5' }); DB.leaders.push(l); p.leader = l.id;
      News._test.typeMs(0); News._test.sayMs(120000); persistNow(); }""")
    lid = js("() => DB.leaders[0].id")
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    js("() => { window.__cmark = true; }")
    close_settings(pg)
    settle = lambda ms=3600: pg.wait_for_timeout(ms)
    def drop(name, d):
        js(f"() => window.__sub.set('inbox/{name}', {{ text: {json.dumps(json.dumps(d))}, t: Date.now() }})")
    say = lambda: js("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null;
      return { name: $('#ldSayName').textContent, role: $('#ldSayRole').textContent, text: $('#ldSayText').textContent, k: b.dataset.k,
        acts: [...b.querySelectorAll('#ldSayActs button')].map(x => x.textContent), img: !!b.querySelector('#ldSayFace img'), color: getComputedStyle(b).getPropertyValue('--ld').trim() }; }""")
    tiles = lambda: js("() => [...document.querySelectorAll('#newsList .news-tile')].map(t => [t.dataset.k, t.querySelector('.news-badge').textContent, t.querySelector('.news-name').textContent])")
    close_say = lambda: js("() => { const c = document.querySelector('#ldSayClose'); if (!document.querySelector('#ldSay').hidden) c.click(); }")
    activity = lambda pid: js(f"() => getProject('{pid}').activity.map(e => e.text)")
    forget = lambda: js("() => { const s = JSON.parse(localStorage.getItem('nullovation-city:news')); s.items = []; localStorage.setItem('nullovation-city:news', JSON.stringify(s)); News.renderSection(); }")

    # ---------- Quill's portrait ships with the city ----------
    ok('Quill\'s portrait is in the page, pixel for pixel', js(PORTRAIT_SUM, js("() => PORTRAITS.quill")) == portrait_sum('quill'))
    q = js("() => QUILL")
    ok(f'Quill, The Pocket Wizard, in his plum ({q})', q['name'] == 'Quill' and q['role'] == 'The Pocket Wizard' and q['color'] == '#8E5A9E')

    # ---------- C1: a round Claude attached, on its own: Quill says it, for any building ----------
    t_beds = tid(gp, 'Add plant icons')
    js(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.id === '{t_beds}'); t.round = makeRound(readWizardFile({json.dumps(ROUND)}), '2026-10-27-bed-layout-round1.json'); changed(p, {{ touch: false }}); }}")
    drop('2026-10-27-1000-garden.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'A round for the icons',
                                          'changes': [{'do': 'add-round', 'task': 'Publish the app', 'round': {**ROUND, 'config': {**ROUND['config'], 'title': 'Publishing, Round 1'}}, 'file': '2026-10-27-publishing-round1.json'}]})
    settle()
    s = say()
    ok(f'Quill says it, by himself, not the building\'s leader ({s})', s and s['name'] == 'Quill' and s['role'] == 'The Pocket Wizard' and s['k'] == 'ld:quill' and s['color'] == '#8E5A9E'
       and s['text'] == 'Claude attached a wizard round to Publish the app: Publishing, Round 1. Sent just now.')
    ok(f'with his portrait, Read and Undo ({s and s["acts"]})', s and s['img'] and s['acts'] == ['Read', 'Undo', 'Go to it'])
    ok(f'his face in News, apart from Talal ({tiles()})', [t[0] for t in tiles()] == ['ld:quill'] and tiles()[0][2] == 'Quill')
    pg.screenshot(path=str(SH / '440-quill-round.png'), clip=pg.query_selector('#ldSay').bounding_box())
    acts = activity(gp)
    ok(f'its line in Activity, the one Claude still writes there, and no summary (C2) ({acts[-2:]})', acts[-1] == 'Claude attached a wizard round to Publish the app: Publishing, Round 1' and not any(a.startswith('Claude: ') for a in acts))

    # Read: the round in its popup, with Open in wizard
    pg.click('#ldSay .ld-round-read'); pg.wait_for_timeout(300)
    pop = js("""() => { const m = document.querySelector('.modal.panel.rd'); return m && { title: m.querySelector('#pnTitle').textContent, state: m.querySelector('.pv-round-state').textContent,
      for: m.querySelector('.rd-for').textContent, qs: [...m.querySelectorAll('.pv-round-ans li')].map(l => [l.querySelector('.id').textContent, l.querySelector('.a').textContent]),
      btn: m.querySelector('#rdWizard').textContent.trim(), w: Math.round(m.getBoundingClientRect().width) }; }""")
    ok(f'Read opens the round in a small popup: where it stands, what it is for, each question, and Open in wizard ({pop})', pop and pop['title'] == 'Publishing, Round 1'
       and pop['state'] == 'Waiting: 0 of 2 answered' and pop['for'] == 'For Publish the app, in Garden planner.' and pop['qs'] == [['L1', 'Open'], ['L2', 'Open']] and pop['btn'] == 'Open in wizard' and pop['w'] <= 560)
    pg.screenshot(path=str(SH / '441-round-popup.png'))
    pg.click('#rdWizard'); pg.wait_for_timeout(500)
    ok(f'Open in wizard closes it and opens the round in the wizard, as Wizard it does ({len(js("() => window.__opened"))})', not js("() => !!document.querySelector('.modal.panel.rd')")
       and len(js("() => window.__opened")) >= 1 and 'Publishing, Round 1' in (pg.text_content('#toast') or ''))
    pg.click('#ldSay .ld-undo'); pg.wait_for_timeout(400)
    acts = activity(gp)
    ok('Undo takes the round off, and its line in Activity with it, writing nothing else', not js(f"() => !!getProject('{gp}').todos.find(t => t.text === 'Publish the app').round")
       and not any('Publishing, Round 1' in a for a in acts) and not any(a.startswith('Undid') for a in acts))
    close_say(); pg.wait_for_timeout(300)

    # ---------- the round's answers: Quill says them, waiting in News, with Read and Open, and a line in Activity ----------
    js(f"() => News.add(getProject('{gp}'), 'week', {{ n: 3, task: 'Draw the beds on a grid' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:t44' }})")
    js(f"""async () => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.id === '{t_beds}');
      await Rounds.writeFile(ClaudeWork.folder(), t.round); }}""")
    js(f"() => window.__sub.set('wizard-rounds/2026-10-27-bed-layout-round1.json', {{ text: {json.dumps(json.dumps({**ANSWERS, 'round': ROUND}))}, t: Date.now() + 5000 }})")
    pg.wait_for_timeout(3600 + 4500)
    ok(f'they wait in News, with Quill and with Talal apart: no bubble ({tiles()})', say() is None and sorted(t[0] for t in tiles()) == sorted(['ld:quill', 'ld:' + lid]))
    acts = activity(gp)
    ok(f'and write a line in Activity, how far it is (C2) ({acts[-1:]})', acts[-1] == 'Answers in for ' + TITLE + ': 1 of 2')
    pg.click('#newsList .news-tile[data-k="ld:quill"] .news-face'); pg.wait_for_timeout(300)
    s = say()
    ok(f'a click on his face: Quill says them, with Read and Open ({s and (s["text"], s["acts"])})', s and s['name'] == 'Quill' and s['text'] == 'Your answers are in for ' + TITLE + ': 1 of 2.' and s['acts'] == ['Read', 'Open', 'Go to it'])
    pg.click('#ldSay .ld-round-read'); pg.wait_for_timeout(300)
    pop = js("() => { const m = document.querySelector('.modal.panel.rd'); return m && [...m.querySelectorAll('.pv-round-ans li')].map(l => l.textContent); }")
    ok(f'Read shows each answer so far, with its note ({pop})', pop and 'A grid' in pop[0] and 'Note: keep it simple' in pop[0] and pop[1].endswith('Open'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it, and Quill\'s bubble is still there', not js("() => !!document.querySelector('.modal.panel.rd')") and say() is not None)
    close_say(); pg.wait_for_timeout(300)

    # the status card: Quill's line in the leader's card, with his face and name
    js(f"() => News.add(getProject('{gp}'), 'answers', {{ round: '{TITLE}', n: 1, total: 2 }}, {{ ref: {{ tid: '{t_beds}' }}, key: 'answers:t44b' }})"); settle(400)
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    sc = js("""() => { const l = document.querySelector('#bubble .b-leader'); if (!l) return null; const o = l.querySelector('.ld-line.by-other');
      return { name: l.querySelector('.ld-name').textContent, other: o && o.querySelector('.ld-says').textContent, face: o && Math.round(o.querySelector('.ld-by .ld-face').getBoundingClientRect().width), img: !!(o && o.querySelector('.ld-by img')),
        acts: o ? [...o.querySelectorAll('.ld-acts button')].map(b => b.textContent) : [] }; }""")
    ok(f'on the status card, Talal\'s line has Quill\'s say, his face and name before it ({sc})', sc and sc['name'] == 'Talal' and sc['other'] == 'Quill: Your answers are in for ' + TITLE + ': 1 of 2.'
       and sc['face'] == 20 and sc['img'] and sc['acts'] == ['Read', 'Open'])
    pg.screenshot(path=str(SH / '442-card-quill-line.png'), clip=pg.query_selector('#bubble').bounding_box())
    js("() => MapView.deselect()"); pg.wait_for_timeout(300)
    forget()

    # Show the answers in the task panel opens the same popup
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    js(f"() => FullView.openTask('{gp}', '{t_beds}')"); pg.wait_for_timeout(400)
    pg.click('#pvSide .pv-round-fold'); pg.wait_for_timeout(300)
    ok('Show the answers in the task panel opens the same popup', js("() => { const m = document.querySelector('.modal.panel.rd'); return !!m && m.querySelector('#pnTitle').textContent; }") == TITLE)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('and Esc leaves the task panel open', js("() => !!document.querySelector('#pvSide #pvTaskDesc')"))
    js("() => FullView.close()"); js("() => MapView.deselect()"); pg.wait_for_timeout(300)

    # a leader of the city's own named Quill is him: one face in News
    js(f"""() => {{ const l = blankLeader({{ name: 'Quill', role: 'Keeper of Rounds', color: '#5A6FA8' }}); DB.leaders.push(l); getProject('{nc}').leader = l.id; persistNow(); }}""")
    qid = js("() => DB.leaders.find(l => l.name === 'Quill').id")
    js(f"() => News.add(getProject('{gp}'), 'answers', {{ round: '{TITLE}', n: 1, total: 2 }}, {{ ref: {{ tid: '{t_beds}' }}, key: 'answers:t44c' }})")
    js(f"() => News.add(getProject('{nc}'), 'week_quiet', {{ task: 'Build the block art skill' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:t44c' }})")
    settle(400)
    t = tiles()
    ok(f'with a leader named Quill in the city, his rounds come under that leader\'s face: one Quill in News, counting both ({t})', [x[0] for x in t] == ['ld:' + qid] and t[0][1] == '2' and t[0][2] == 'Quill')
    pg.click(f'#newsList .news-tile[data-k="ld:{qid}"] .news-face'); pg.wait_for_timeout(300)
    s = say()
    ok(f'in his own role and color ({s and (s["role"], s["color"])})', s and s['name'] == 'Quill' and s['role'] == 'Keeper of Rounds' and s['color'].upper() == '#5A6FA8')
    close_say(); forget()
    js(f"() => {{ DB.leaders = DB.leaders.filter(l => l.id !== '{qid}'); getProject('{nc}').leader = ''; persistNow(); }}")

    # ---------- N1: the leader card in the project view says what the status card says ----------
    js(S('w1', 'working', GARDEN, task='Draw the beds on a grid', project='Garden planner'))
    settle()
    js("() => MapView.deselect()"); js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    lc = js("() => [...document.querySelectorAll('#pvLeader .ld-says')].map(x => x.textContent)")
    ok(f'Claude at work: the leader card says it, as the status card does, in place of the greeting ({lc})', lc == ['Claude is working on Draw the beds on a grid. Started 2 minutes ago.'])
    js(S('w1', 'waiting', GARDEN, task='Draw the beds on a grid', project='Garden planner'))
    settle()
    lc = js("() => [...document.querySelectorAll('#pvLeader .ld-says')].map(x => x.textContent)")
    ok(f'Claude waiting: the card follows, by itself ({lc})', lc == ['Claude is waiting for you on Draw the beds on a grid.'])
    drop('2026-10-27-1010-garden.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'The plan saves',
                                          'changes': [{'do': 'done', 'task': 'Save a plan as a file'}]})
    js("() => window.__cf.delete('w1.json')")
    settle()
    ask = js("""() => { const l = document.querySelector('#pvLeader .ld-line[data-moment="asks"]'); return l && [l.querySelector('.ld-says').textContent, [...l.querySelectorAll('.ld-acts button')].map(b => b.textContent)]; }""")
    ok(f'what Claude asks first, with its buttons, on the leader card too ({ask})', ask and ask[0] == 'Claude wants your OK first: tick off Save a plan as a file. Sent just now.' and ask[1] == ['Tick it', 'Dismiss'])
    ok('the session gone, its waiting line goes from the card too', js("() => !document.querySelector('#pvLeader .ld-line[data-moment=\"waiting\"]')"))
    pg.screenshot(path=str(SH / '443-leader-card.png'), clip=pg.query_selector('#pvLeader').bounding_box())
    pg.click('#pvLeader .ld-line[data-moment="asks"] .b-claude-tick'); pg.wait_for_timeout(900)
    done = js(f"() => getProject('{gp}').todos.find(t => t.text === 'Save a plan as a file').done")
    ok('and you can act on it there: Tick it ticks it off', done is True and pg.locator('#pvLeader .ld-line[data-moment="asks"]').count() == 0)
    acts = activity(gp)
    ok(f'a tick you make writes its Done line; Claude writes nothing ({acts[-2:]})', acts[-1] == 'Done: Save a plan as a file' and not any(a.startswith('Claude') and 'wizard round' not in a for a in acts))
    js("() => FullView.close()"); js("() => MapView.deselect()"); pg.wait_for_timeout(300)
    forget()

    # a building with no leader: Proxima says it on the card inside too, with Pick a leader
    js(f"() => News.add(getProject('{nc}'), 'week_quiet', {{ task: 'Build the block art skill' }}, {{ ref: {{ week: ymd(weekStartOf(Date.now())) }}, key: 'week:t44d' }})")
    js("() => MapView.deselect()"); js(f"() => FullView.open('{nc}')"); pg.wait_for_timeout(600)
    px = js("() => { const c = document.querySelector('#pvLeader'); return c && [c.classList.contains('px-voice'), c.querySelector('.ld-name').textContent, [...c.querySelectorAll('.ld-says')].map(x => x.textContent), c.querySelector('.ld-change').textContent]; }")
    ok(f'a building with no leader: Proxima says it on the card inside, with Pick a leader ({px})', px and px[0] and px[1] == 'Proxima Pace' and px[2] == ['Quiet week: nothing finished. Build the block art skill is a good start.'] and px[3] == 'Pick a leader')
    js("() => FullView.close()"); js("() => MapView.deselect()"); pg.wait_for_timeout(300)
    js(f"() => FullView.open('{nc}')"); pg.wait_for_timeout(500)
    ok('opened again with nothing to say, it offers to pick a leader, as before', js("() => document.querySelector('#pvLeader').classList.contains('empty')"))
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    # ---------- C2: Claude adds things: nothing in Activity, and no Added todo ----------
    before = activity(gp)
    drop('2026-10-27-1020-garden.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'Notes and tasks',
                                          'changes': [{'do': 'add-tasks', 'milestone': 'Later', 'tasks': [{'text': 'Label the beds'}]}, {'do': 'add-note', 'title': 'Soil', 'text': 'Loam.'},
                                                      {'do': 'add-link', 'label': 'Seeds', 'url': 'https://example.com/seeds'}]})
    settle()
    got = js(f"() => {{ const p = getProject('{gp}'); return [p.todos.some(t => t.text === 'Label the beds'), p.notes.some(n => n.title === 'Soil'), p.links.some(l => l.label === 'Seeds'), p.milestones.some(m => m.name === 'Later')]; }}")
    after = activity(gp)
    ok(f'what Claude adds applies at once, a new milestone too ({got})', got == [True, True, True, True])
    ok(f'and writes nothing in Activity: no task, milestone, note, link or summary line (C2) ({after[len(before):]})', after == before)
    close_say(); forget()

    # ---------- N2: a task going overdue writes a line in Activity, dated the day after its due date ----------
    js(f"""() => {{ const p = getProject('{gp}'), d = new Date(); d.setDate(d.getDate() - 3);
      p.todos.find(t => t.text === 'Tune the watering reminders').due = ymd(d.getTime());
      const w = p.todos.find(t => t.text === 'Draw the beds on a grid'); w.due = ymd(d.getTime()); w.done = true; w.doneAt = Date.now(); persistNow(); }}""")
    busy0 = js(f"() => Traffic.busyness(getProject('{gp}'))")
    wrote = js("() => logOverdue()")
    od = js(f"""() => {{ const p = getProject('{gp}'); return p.activity.filter(e => e.text.startsWith('Overdue: ')).map(e => [e.text, e.ref.startsWith('overdue:'), Math.round((Date.now() - e.at) / 864e5 * 10) / 10,
      new Date(e.at).getHours() + ':' + new Date(e.at).getMinutes()]); }}""")
    ok(f'a task past its due date: "Overdue: <task>", dated the start of the day after it (N2) ({od})', wrote and len(od) == 1 and od[0][0] == 'Overdue: Tune the watering reminders' and od[0][1] and od[0][3] == '0:0' and 1 < od[0][2] <= 3)
    ok('a done task past its date writes none', not any('Draw the beds' in x[0] for x in od))
    ok('once: a second look writes nothing more', js("() => logOverdue()") is False and len(js(f"() => getProject('{gp}').activity.filter(e => e.text.startsWith('Overdue: '))")) == 1)
    ok('in time order', js(f"() => getProject('{gp}').activity.every((x, i, a) => !i || a[i - 1].at <= x.at)"))
    busy1 = js(f"() => Traffic.busyness(getProject('{gp}'))")
    ok(f'it draws no crowd: the building is no busier ({busy0} then {busy1})', abs(busy1 - busy0) < 1e-6)   # time passing moves it by far less than a line would
    js(f"""() => {{ const p = getProject('{gp}'), d = new Date(); d.setDate(d.getDate() - 1); p.todos.find(t => t.text === 'Tune the watering reminders').due = ymd(d.getTime()); persistNow(); }}""")
    js("() => logOverdue()")
    n = js(f"() => getProject('{gp}').activity.filter(e => e.text === 'Overdue: Tune the watering reminders').length")
    ok(f'a new due date that goes by is a new line ({n})', n == 2)
    js(f"""() => {{ const p = getProject('{gp}'), d = new Date(); d.setDate(d.getDate() - 2); p.todos.find(t => t.text === 'Publish the app').due = ymd(d.getTime()); persistNow(); }}""")
    pg.reload()
    pg.wait_for_function("() => typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(500)
    ok('on opening the city, one gone overdue meanwhile gets its line', js(f"() => getProject('{gp}').activity.some(e => e.text === 'Overdue: Publish the app')"))
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.locator('.pv button:has-text("Activity")').first.click(); pg.wait_for_timeout(400)
    ok('the Activity panel shows it', 'Overdue: Publish the app' in (pg.text_content('.pv-activity') or ''))
    pg.screenshot(path=str(SH / '444-activity-overdue.png'))
    js("() => FullView.close()")

    print('errors:', errors)
    ok('no console errors', not errors)
    b.close()
