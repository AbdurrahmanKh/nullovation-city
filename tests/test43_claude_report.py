"""Claude's news as one report (0.1.68, Claude's News on the Status Card, Round 1), as pages since 0.1.96.

An update Claude sends is said by its building's leader with the finish of the task it reports on (A1): since 0.1.96 (One
Leader Card, M2) a page per type, never one mixed message: what needs your OK (opening the bubble by itself, Read, Apply,
Tick it and No), what Claude added (the note whole and the link by name, each with Delete, waiting in News) and the
finish (Claude's summary in its own words, C2, with no buttons). An update whose session still works waits for its
finish; one with no finish to sit under is said on its own. Tick it shows only when Claude asks to tick the task off
(B3). The city opens with a Claude folder held in memory, as in test24."""
import json, pathlib, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, DATA, SKILLS, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# ---------- the skill's checker: an update names the task it reports on ----------
CHECK = SKILLS / 'nullovation-city' / 'scripts' / 'check_plan.py'
def check(d):
    f = pathlib.Path(tempfile.mkdtemp(dir=str(DATA))) / 'change.json'
    f.write_text(json.dumps(d), encoding='utf-8')
    r = subprocess.run([sys.executable, str(CHECK), str(f)], capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode('utf-8', 'replace')
base = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'Beds drawn', 'changes': [{'do': 'add-note', 'title': 'Beds', 'text': 'Drawn.'}]}
rc, out = check({**base, 'task': 'Draw the beds on a grid'})
ok(f'check_plan.py takes an update naming its task ({rc})', rc == 0 and 'OK' in out)
rc, out = check({**base, 'task': 7})
ok(f'and refuses a task that is not a title ({rc})', rc == 1 and '"task"' in out)

FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
def S(session, state, cwd, mins=0, **kw):
    """A session file as the hooks write it, last heard from mins minutes ago."""
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(cwd)}, at: {at}, since: {at} - 120000, started: {at} - 300000{extra} }})"
GARDEN = 'C:\\Users\\me\\garden'

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t43')) { sessionStorage.setItem('nc-t43', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(600)
    js = pg.evaluate
    js("() => News._test.flat(true)")   # every line of a card at once: topics flip in pass 59 (0.1.94)
    ids = js("() => Object.fromEntries(DB.projects.map(p => [p.name, p.id]))")
    gp, nc = ids['Garden planner'], ids['Nullovation City']
    js("""() => { const p = DB.projects.find(p => p.name === 'Garden planner');
      p.links.push({ id: uid('l'), label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true });
      const l = blankLeader({ name: 'Talal', role: 'Head of Gardens', color: '#7FD6B5' }); DB.leaders.push(l); p.leader = l.id;
      News._test.typeMs(0); News._test.sayMs(120000); persistNow(); }""")
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    js("() => { window.__cmark = true; }")
    close_settings(pg)
    def settle(ms=3600):
        pg.wait_for_timeout(ms)
    def drop(name, d):
        js(f"() => window.__sub.set('inbox/{name}', {{ text: {json.dumps(json.dumps(d))}, t: Date.now() }})")
    def change(task, summary, changes, project='Garden planner'):
        d = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': project, 'summary': summary, 'changes': changes}
        if task: d['task'] = task
        return d
    say = lambda: js("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null;
      return { text: $('#ldSayText').textContent, type: b.dataset.type, n: ($('#ldSayCount') || {}).textContent || '', where: ($('#ldSayWhere') || {}).textContent || '',
        words: [...b.querySelectorAll('#ldSayMore .b-claude-said')].map(x => x.textContent),
        parts: [...b.querySelectorAll('#ldSayMore .ld-part')].map(x => [x.querySelector('.ld-part-text').textContent, [...x.querySelectorAll('button.btn')].map(y => y.textContent)]),
        acts: [...b.querySelectorAll('#ldSayActs button')].map(x => x.textContent), when: b.querySelectorAll('.b-claude-when').length }; }""")
    items = lambda pid: js(f"() => News.items().filter(it => it.pid === '{pid}').map(it => it.moment)")
    close_say = lambda: js("() => { const c = document.querySelector('#ldSayClose'); if (!document.querySelector('#ldSay').hidden) c.click(); }")
    mini = lambda: js("() => { const c = document.querySelector('#ldSayMin'); if (!document.querySelector('#ldSay').hidden && c) c.click(); }")   # minimized, its pages wait in News (0.1.96)
    def face(name):
        """A click on a face in News: what waits there opens, every page its speaker has (0.1.96)."""
        js(f"() => {{ const t = [...document.querySelectorAll('#newsList .news-tile')].find(x => x.textContent.includes({json.dumps(name)})); if (t) t.querySelector('.news-face').click(); }}")
        pg.wait_for_timeout(400)
    nxt = lambda: (js("() => document.querySelector('#ldSayNext').click()"), pg.wait_for_timeout(200))
    CARD = """() => { const b = document.querySelector('#bubble'); if (b.hidden) return null;
      return [...b.querySelectorAll('.ld-line')].map(l => ({ moment: l.dataset.moment, type: l.dataset.type, task: (l.closest('.lc').querySelector('.lc-tline') || {}).textContent || '',
        says: l.querySelector('.ld-says').textContent, words: [...l.querySelectorAll('.b-claude-said')].map(x => x.textContent), quote: (l.querySelector('.lc-quote') || {}).textContent || '',
        parts: [...l.querySelectorAll('.ld-part-text')].map(x => x.textContent), btns: [...l.querySelectorAll('.ld-acts button')].map(x => x.textContent), tick: !!l.querySelector('.b-claude-tick'),
        h: Math.round(l.closest('.lc').getBoundingClientRect().height) })); }"""
    card = lambda: js(CARD)
    line = lambda c, m: next((x for x in (c or []) if x['moment'] == m), None)
    state = lambda: js(f"() => {{ const p = getProject('{gp}'); return {{ notes: p.notes.map(n => n.title), links: p.links.map(l => l.label), desc: p.todos.find(t => t.text === 'Draw the beds on a grid').description }}; }}")

    # ---------- A1: an update from a session still at work waits for its finish ----------
    st0 = state()
    js(S('r1', 'working', GARDEN, task='Draw the beds on a grid', project='Garden planner'))
    settle()
    drop('2026-10-24-1500-garden.json', change('Draw the beds on a grid', 'Beds drawn at 1:50; labels are left', [
        {'do': 'add-note', 'title': 'Bed layout', 'text': 'Six beds, drawn at 1:50.\nThe middle path stays wide.'},
        {'do': 'add-link', 'label': 'Beds sketch', 'url': 'https://example.com/beds'},
        {'do': 'edit-description', 'task': 'Draw the beds on a grid', 'description': 'Draw the six beds on a 1:50 grid.\nDone when: labels are on.'}]))
    settle()
    s1 = state()
    ok(f'what Claude added applies at once, as before ({s1["notes"][-1:]}, {s1["links"][-1:]})', s1['notes'][-1] == 'Bed layout' and s1['links'][-1] == 'Beds sketch' and s1['desc'] == st0['desc'])
    ok(f'but nothing is said while its session works: no bubble, and no item in News ({items(gp)})', say() is None and items(gp) == [])
    rep = js("() => News._test.reports()")
    ok(f'the update waits as a report, on the session it came from ({[(r["sid"], r["alone"], r["fin"]) for r in rep]})', len(rep) == 1 and rep[0]['sid'] == 'r1' and not rep[0]['alone'] and not rep[0]['fin'])
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    c = card()
    ok(f'the status card shows its parts meanwhile, a page per type beside the working page (0.1.96) ({c and [(x["type"], x["says"]) for x in c]})', c
       and [(x['type'], x['moment']) for x in c] == [('approval', 'asks'), ('attach', 'added'), ('news', 'working')]
       and line(c, 'working')['says'] == 'Claude is working on this task. Started 2 minutes ago.' and line(c, 'working')['task'] == 'Draw the beds on a grid'
       and line(c, 'added')['says'] == 'Claude added a note, Bed layout, and a link, Beds sketch. Sent just now.'
       and line(c, 'asks')['says'] == 'Claude wants your OK first: a new description for this task. Sent just now.')
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)

    js(S('r1', 'done', GARDEN, task='Draw the beds on a grid', project='Garden planner', reply='I drew the **beds** at `1:50`; see [the sketch](https://example.com/beds).'))
    settle()
    s = say()
    ok(f'once it finishes, what needs your OK opens the bubble by itself, alone, with its one time (0.1.96) ({s and (s["type"], s["n"], s["text"])})', s and s['type'] == 'approval' and s['n'] == ''
       and s['text'] == 'Claude wants your OK first: a new description for this task. Sent just now.' and s['when'] == 1 and s['where'] == 'Garden planner·Draw the beds on a grid')
    ok(f'one change: its buttons on the page, No in place of Dismiss (A2, 0.1.96) ({s and (s["parts"], s["acts"])})', s and s['parts'] == [] and s['acts'] == ['Read', 'Apply', 'No', 'Go to it'])
    ok(f'no Tick it: Claude did not ask to tick the task off, so work is left (B3) ({s and s["acts"]})', s and 'Tick it' not in s['acts'] and not js("() => !!document.querySelector('#ldSay .b-claude-tick')"))
    ok(f'a page per type in News, with one leader\'s face: what asks, what Claude added, the finish (0.1.96, M2) ({items(gp)})', items(gp) == ['asks', 'added', 'finished'] and js("() => document.querySelectorAll('#newsList .news-tile').length") == 1)
    pg.screenshot(path=str(SH / '430-report-bubble.png'), clip=pg.query_selector('#ldSay').bounding_box())

    # Read: a new description whole, in a small panel
    pg.click('#ldSay .ld-read'); pg.wait_for_timeout(300)
    rd = js("() => { const m = document.querySelector('.modal.panel.cr'); return m && { title: m.querySelector('#pnTitle').textContent, heads: [...m.querySelectorAll('.cr-h')].map(x => x.textContent), texts: [...m.querySelectorAll('.cr-text')].map(x => x.textContent), width: Math.round(m.getBoundingClientRect().width) }; }")
    ok(f'Read opens a small panel: the new description whole, over the one it would replace ({rd})', rd and rd['title'] == 'A new description for Draw the beds on a grid' and rd['heads'] == ['The new description', 'Its description now']
       and rd['texts'][0] == 'Draw the six beds on a 1:50 grid.\nDone when: labels are on.' and rd['texts'][1] == (st0['desc'] or 'No description yet.') and rd['width'] <= 560)
    pg.screenshot(path=str(SH / '431-report-read.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it, the page still there', not js("() => !!document.querySelector('.modal.panel.cr')") and say() is not None)

    # a click on the face in News: every page its leader has
    mini(); pg.wait_for_timeout(300)
    face('Talal')
    s = say()
    ok(f'its leader\'s face in News opens every page: what asks, what Claude added, the finish ({s and s["n"]})', s and s['n'] == '1 / 3' and s['type'] == 'approval')
    nxt()
    s = say()
    at = js("""() => { const b = document.querySelector('#ldSay'); return { notes: [...b.querySelectorAll('.lc-note')].map(n => [n.querySelector('.pv-tnote-t').textContent, (n.querySelector('.pv-tnote-b') || {}).textContent]),
      links: [...b.querySelectorAll('a.lc-att-link')].map(a => [a.textContent, a.href]), del: [...b.querySelectorAll('.ld-del')].map(x => x.textContent) }; }""")
    ok(f'what Claude added, on its own Attachment page: the note whole and the link by name, each with Delete (C1, 0.1.96) ({s and s["text"]}, {at})', s and s['type'] == 'attach'
       and s['text'] == 'Claude added a note, Bed layout, and a link, Beds sketch. Sent just now.' and at['notes'] == [['Bed layout', 'Six beds, drawn at 1:50.\nThe middle path stays wide.']]
       and at['links'] == [['Beds sketch', 'https://example.com/beds']] and at['del'] == ['Delete', 'Delete'])
    pg.screenshot(path=str(SH / '433-report-attachment.png'), clip=pg.query_selector('#ldSay').bounding_box())

    # Delete, each on its own: the rest stays (0.1.96: Delete in place of Undo)
    pg.click('#ldSay .lc-att-note .ld-del'); pg.wait_for_timeout(400)
    s, s2 = say(), state()
    ok(f'Delete takes the note out, and the page stays with what is left ({s and s["text"]})', s2['notes'] == st0['notes'] and s2['links'][-1] == 'Beds sketch'
       and s and s['type'] == 'attach' and s['text'] == 'Claude added a link, Beds sketch. Sent just now.')
    pg.click('#ldSay .ld-del'); pg.wait_for_timeout(400)
    s, s2 = say(), state()
    ok(f'Delete on the last takes the link out, and the bubble goes on to the next page: the finish ({s and (s["n"], s["type"])})', s2['notes'] == st0['notes'] and s2['links'] == st0['links']
       and s and s['type'] == 'news' and s['n'] == '2 / 2' and items(gp) == ['asks', 'finished'])
    ok(f'the finish: its words say "this task", the task in its own line (W1) ({s and (s["text"], s["where"])})', s and s['text'] == 'Claude handed this task back to you. Just now.' and s['where'] == 'Garden planner·Draw the beds on a grid')
    ok(f'Claude\'s summary under it, in its own words, not the start of its reply (C2) ({s and s["words"]})', s and s['words'] == ['Beds drawn at 1:50; labels are left'])
    ok(f'News has no buttons, Go to it aside, and no Tick it (M1) ({s and s["acts"]})', s and s['acts'] == ['Go to it'] and not js("() => !!document.querySelector('#ldSay .b-claude-tick')"))
    hgt = js("() => { const r = document.querySelector('#ldSay').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }")
    lines = js("() => [...document.querySelectorAll('#ldSay .ld-part-text, #ldSay .b-claude-said')].map(x => Math.round(x.getBoundingClientRect().height / parseFloat(getComputedStyle(x).lineHeight)))")
    ok(f'nothing in it takes more than two lines ({lines}, the bubble {hgt})', lines and all(n <= 2 for n in lines))
    mini(); pg.wait_for_timeout(300)

    # the status card: the same pages, for as long as the finish shows there
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    c = card()
    ok(f'the status card says the same pages: what needs your OK, and the finish with Claude\'s summary ({c and [(x["type"], x["says"]) for x in c]})', c
       and [(x['type'], x['moment']) for x in c] == [('approval', 'asks'), ('news', 'finished')]
       and line(c, 'asks')['says'] == 'Claude wants your OK first: a new description for this task. Sent just now.' and line(c, 'asks')['btns'] == ['Read', 'Apply', 'No']
       and line(c, 'finished')['says'] == 'Claude handed this task back to you. Just now.' and line(c, 'finished')['words'] == ['Beds drawn at 1:50; labels are left']
       and line(c, 'finished')['task'] == 'Draw the beds on a grid' and not line(c, 'finished')['tick'])
    ok(f'and each page keeps to a few lines, the next tasks in view under them ({c and [x["h"] for x in c]} px)', c and all(x['h'] <= 200 for x in c) and pg.is_visible('#bubble .b-todos'))
    pg.screenshot(path=str(SH / '432-report-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    pg.click('#bubble .ld-line[data-moment="asks"] .b-claude-apply'); pg.wait_for_timeout(800)
    ok('Apply gives the task its new description, and its page goes', state()['desc'] == 'Draw the six beds on a 1:50 grid.\nDone when: labels are on.' and pg.locator('#bubble .ld-line[data-moment="asks"]').count() == 0
       and js("() => window.__sub.has('inbox/done/2026-10-24-1500-garden.json') && !window.__sub.has('inbox/pending/2026-10-24-1500-garden.json')"))
    ok('with nothing left to act on, the finish shows its summary still, and no Tick it', (pg.text_content('#bubble .ld-line[data-moment="finished"] .b-claude-said') or '') == 'Beds drawn at 1:50; labels are left'
       and pg.locator('#bubble .ld-line[data-moment="finished"] .b-claude-tick').count() == 0)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)

    # ---------- B3: Tick it when Claude says the task is done ----------
    js(S('r2', 'working', GARDEN, task='Save a plan as a file', project='Garden planner'))
    settle()
    drop('2026-10-24-1510-garden.json', change('Save a plan as a file', 'Plans save as files', [
        {'do': 'add-note', 'title': 'Plan files', 'text': 'A plan saves as JSON.'}, {'do': 'done', 'task': 'Save a plan as a file'}]))
    settle()
    ok('again nothing is said while it works', say() is None)
    js(S('r2', 'done', GARDEN, task='Save a plan as a file', project='Garden planner', reply='Done.'))
    settle()
    s = say()
    ok(f'Claude asking to tick it off: Tick it on its own Need Approval page, opening by itself (B3, 0.1.96) ({s and (s["text"], s["acts"])})', s and s['type'] == 'approval'
       and s['text'] == 'Claude wants your OK first: tick this task off. Sent just now.' and s['where'] == 'Garden planner·Save a plan as a file' and s['acts'] == ['Tick it', 'No', 'Go to it']
       and items(gp) == ['asks', 'added', 'finished'])
    pg.click('#ldSay .b-claude-tick'); pg.wait_for_timeout(800)
    t = js(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.text === 'Save a plan as a file'); return [t.done, p.activity.slice(-3).map(e => e.text)]; }}")
    ok(f'Tick it ticks it off as a tick does, said by its leader ({t})', t[0] is True and 'Done: Save a plan as a file' in t[1] and not any(x.startswith('Claude') for x in t[1])   # Claude writes nothing in Activity since 0.1.69
       and 'Ticked off: Save a plan as a file.' in pg.text_content('#toast') and 'Talal' in pg.text_content('#toast'))
    ok(f'with nothing left on it the page is read and the bubble closes; what Claude added waits in News with the finish (0.1.96) ({items(gp)})', say() is None and items(gp) == ['added', 'finished'])
    close_say(); pg.wait_for_timeout(300)

    # ---------- B3, C2: a finish with no update, the start of its reply as plain words (no Tick it since 0.1.96) ----------
    js(S('r3', 'done', GARDEN, task='Tune the watering reminders', project='Garden planner', reply='## Done: the **reminders** now fire at `7:00`, see [the PR](https://x.example/pr/12).'))
    settle()
    ok(f'a finish alone waits with its leader, as before ({say() is None} {items(gp)})', say() is None and 'finished' in items(gp))
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    fin = next((x for x in (card() or []) if x['moment'] == 'finished' and x['task'] == 'Tune the watering reminders'), None)
    ok(f'its card page: the start of its reply as a quote, markdown taken off; News, so no Tick it and no buttons (M1) ({fin})', fin and fin['says'] == 'Claude handed this task back to you. Just now.'
       and fin['quote'] == '“Done: the reminders now fire at 7:00, see the PR.”' and fin['words'] == [] and not fin['tick'] and fin['btns'] == [] and fin['parts'] == [])
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    for k in ('r1', 'r2', 'r3'):
        js(f"() => window.__cf.delete('{k}.json')")
    settle()

    # ---------- an update with no finish to sit under is said on its own, as before ----------
    js(S('r4', 'working', GARDEN, task='Add plant icons', project='Garden planner'))
    settle()
    drop('2026-10-24-1520-garden.json', change('Publish the app', 'Store page written', [{'do': 'add-link', 'label': 'Store page', 'url': 'https://example.com/store'}]))
    settle()
    ok(f'one naming another task than the session works on is said on its own: an Attachment page waiting in News, no bubble by itself (0.1.96) ({items(gp)})', say() is None and items(gp) == ['added'])
    face('Talal')
    s = say()
    ok(f'its face opens it, with its summary, and Delete ({s and (s["text"], s["words"], s["acts"])})', s and s['type'] == 'attach' and s['text'] == 'Claude added a link, Store page. Sent just now.'
       and s['words'] == ['Store page written'] and s['acts'] == ['Go to it'] and js("() => [...document.querySelectorAll('#ldSay .ld-del')].map(x => x.textContent)") == ['Delete'])
    close_say(); mini(); js("() => window.__cf.delete('r4.json')"); settle()
    js(f"""() => {{ const p = getProject('{nc}'); addTasks(p, [{{ text: 'Rework how the leaders say what Claude asks on the status card, from the first line on', description: 'Old words.', due: '' }}], {{ id: p.milestones[0].id }}); persistNow(); }}""")
    drop('2026-10-24-1530-city.json', change('', 'A long summary of everything that happened, which is not the change asked about', [
        {'do': 'edit-description', 'task': 'Rework how the leaders say what Claude asks on the status card, from the first line on', 'description': 'New words.'}], project='Nullovation City'))
    settle()
    s = say()
    ok(f'what asks first names the change itself, never Claude\'s summary, its long title whole in the task\'s line (0.1.96) ({s and (s["text"], s["where"])})', s and s['text'] == 'Claude wants your OK first: a new description for this task. Sent just now.'
       and s['where'] == 'Nullovation City·Rework how the leaders say what Claude asks on the status card, from the first line on'
       and s['words'] == ['A long summary of everything that happened, which is not the change asked about'] and s['acts'][:3] == ['Read', 'Apply', 'No'])
    pg.click('#ldSay .b-claude-dismiss'); pg.wait_for_timeout(700)
    ok('No keeps the description, with its toast, and the bubble goes on', js(f"() => getProject('{nc}').todos.find(t => t.text.startsWith('Rework how the leaders')).description") == 'Old words.'
       and 'Kept the description of Rework how the leaders' in pg.text_content('#toast') and say() is None)

    # ---------- the start of a reply, as plain words ----------
    pr = js("""() => [News.plainReply('**Done**: see `a.py` and [the PR](https://x).'), News.plainReply('- fixed it * and more'), News.plainReply('Version 2. Then *this* and _that_ stay.'), News.plainReply('```js\\nx()\\n``` after')]""")
    ok(f'markdown comes off a reply: bold, code, links, a leading bullet ({pr})', pr == ['Done: see a.py and the PR.', 'fixed it and more', 'Version 2. Then this and _that_ stay.', 'after'])
    ok('nothing new in the city: reports are kept in this browser with the news', js("() => !('reports' in DB)") and len(js("() => News._test.reports()")) >= 4)

    b.close()

print(errors or 'no console errors')
