"""Claude's news as one report (0.1.68, Claude's News on the Status Card, Round 1).

An update Claude sends is one report, said by its building's leader under the finish of the task it reports on (A1): the
finish with its one time, Claude's summary in its own words (C2), then a short line for each part with its own buttons,
Read and Undo for what it added, Tick it, Read, Apply and Dismiss for what it asks (A2). An update whose session still
works waits for its finish; one with no finish to sit under is said on its own. Tick it shows when Claude asks to tick
the task off, and on a finish with no update (B3). The city opens with a Claude folder held in memory, as in test24."""
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
      return { text: $('#ldSayText').textContent, words: [...b.querySelectorAll('#ldSayMore .b-claude-said')].map(x => x.textContent),
        parts: [...b.querySelectorAll('#ldSayMore .ld-part')].map(x => [x.querySelector('.ld-part-text').textContent, [...x.querySelectorAll('button.btn')].map(y => y.textContent)]),
        acts: [...b.querySelectorAll('#ldSayActs button')].map(x => x.textContent), when: b.querySelectorAll('.b-claude-when').length }; }""")
    items = lambda pid: js(f"() => News.items().filter(it => it.pid === '{pid}').map(it => it.moment)")
    close_say = lambda: js("() => { const c = document.querySelector('#ldSayClose'); if (!document.querySelector('#ldSay').hidden) c.click(); }")
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
    wl = js("() => { const l = document.querySelector('#bubble .b-claude.working'); return l && [l.querySelector('.ld-says').textContent, [...l.querySelectorAll('.ld-part-text')].map(x => x.textContent)]; }")
    ok(f'the status card shows it under the working line meanwhile ({wl})', wl and wl[0] == 'Claude is working on Draw the beds on a grid. Started 2 minutes ago.'
       and wl[1] == ['Added a note, Bed layout, and a link, Beds sketch.', 'Wants a new description for this task.'])
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)

    js(S('r1', 'done', GARDEN, task='Draw the beds on a grid', project='Garden planner', reply='I drew the **beds** at `1:50`; see [the sketch](https://example.com/beds).'))
    settle()
    s = say()
    ok(f'once it finishes, one report opens by itself, the finish heading it with its one time ({s and s["text"]})', s and s['text'] == 'Claude handed Draw the beds on a grid back to you. Just now.' and s['when'] == 1)
    ok(f'Claude\'s summary under it, in its own words, not the start of its reply (C2) ({s and s["words"]})', s and s['words'] == ['Beds drawn at 1:50; labels are left'])
    ok(f'a short line for each part, each with its own buttons (A2) ({s and s["parts"]})', s and s['parts'] == [['Added a note, Bed layout, and a link, Beds sketch.', ['Read', 'Undo']],
       ['Wants a new description for this task.', ['Read', 'Apply', 'Dismiss']]])
    ok(f'no Tick it: Claude did not ask to tick the task off, so work is left (B3) ({s and s["acts"]})', s and s['acts'] == ['Go to it'] and not js("() => !!document.querySelector('#ldSay .b-claude-tick')"))
    ok(f'one item in News, not three ({items(gp)})', items(gp) == ['finished'] and js("() => document.querySelectorAll('#newsList .news-tile').length") == 1)
    hgt = js("() => { const r = document.querySelector('#ldSay').getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }")
    pg.screenshot(path=str(SH / '430-report-bubble.png'), clip=pg.query_selector('#ldSay').bounding_box())
    lines = js("() => [...document.querySelectorAll('#ldSay .ld-part-text')].map(x => Math.round(x.getBoundingClientRect().height / parseFloat(getComputedStyle(x).lineHeight)))")
    ok(f'nothing in it takes more than two lines ({lines}, the bubble {hgt})', all(n <= 2 for n in lines))

    # Read: the whole of what was added, in a small panel
    pg.click('#ldSay .ld-part[data-part="added"] .ld-read'); pg.wait_for_timeout(300)
    rd = js("() => { const m = document.querySelector('.modal.panel.cr'); return m && { title: m.querySelector('#pnTitle').textContent, heads: [...m.querySelectorAll('.cr-h')].map(x => x.textContent), texts: [...m.querySelectorAll('.cr-text')].map(x => x.textContent), link: (m.querySelector('a.cr-title') || {}).href, width: Math.round(m.getBoundingClientRect().width) }; }")
    ok(f'Read opens a small panel with the note whole and the link (A2) ({rd})', rd and rd['title'] == 'What Claude added to Garden planner' and rd['heads'] == ['Bed layout', 'A link']
       and rd['texts'] == ['Six beds, drawn at 1:50.\nThe middle path stays wide.'] and rd['link'] == 'https://example.com/beds' and rd['width'] <= 560)
    pg.screenshot(path=str(SH / '431-report-read.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it, the report still there', not js("() => !!document.querySelector('.modal.panel.cr')") and say() is not None)
    pg.click('#ldSay .ld-part[data-part="ask edit-description"] .ld-read'); pg.wait_for_timeout(300)
    rd = js("() => { const m = document.querySelector('.modal.panel.cr'); return m && [[...m.querySelectorAll('.cr-h')].map(x => x.textContent), [...m.querySelectorAll('.cr-text')].map(x => x.textContent)]; }")
    ok(f'a new description reads whole, over the one it would replace ({rd})', rd and rd[0] == ['The new description', 'Its description now'] and rd[1][0] == 'Draw the six beds on a 1:50 grid.\nDone when: labels are on.' and rd[1][1] == (st0['desc'] or 'No description yet.'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # Undo, from its own line: the rest stays
    pg.click('#ldSay .ld-part[data-part="added"] .ld-undo'); pg.wait_for_timeout(400)
    s, s2 = say(), state()
    ok(f'Undo takes back the note and the link, and the report stays with what is left ({s and s["parts"]})', s2['notes'] == st0['notes'] and s2['links'] == st0['links']
       and s and s['parts'] == [['Wants a new description for this task.', ['Read', 'Apply', 'Dismiss']]])
    close_say(); pg.wait_for_timeout(300)

    # the status card: the same report under the finish, for as long as the finish shows there
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    card = js("""() => { const l = document.querySelector('#bubble .b-claude.done'); return l && { says: l.querySelector('.ld-says').textContent, words: [...l.querySelectorAll('.b-claude-said')].map(x => x.textContent),
      parts: [...l.querySelectorAll('.ld-part-text')].map(x => x.textContent), tick: !!l.querySelector('.b-claude-tick'), lead: Math.round(document.querySelector('#bubble .b-leader').getBoundingClientRect().height) }; }""")
    ok(f'the status card says the same report, in the leader\'s line ({card})', card and card['says'] == 'Claude handed Draw the beds on a grid back to you. Just now.' and card['words'] == ['Beds drawn at 1:50; labels are left']
       and card['parts'] == ['Wants a new description for this task.'] and not card['tick'])
    ok(f'and keeps to a few lines, the next tasks in view under it ({card and card["lead"]} px)', card and card['lead'] <= 200 and pg.is_visible('#bubble .b-todos'))
    pg.screenshot(path=str(SH / '432-report-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    pg.click('#bubble .b-claude.done .b-claude-apply'); pg.wait_for_timeout(800)
    ok('Apply gives the task its new description, and the line goes', state()['desc'] == 'Draw the six beds on a 1:50 grid.\nDone when: labels are on.' and pg.locator('#bubble .b-claude.done .ld-part').count() == 0
       and js("() => window.__sub.has('inbox/done/2026-10-24-1500-garden.json') && !window.__sub.has('inbox/pending/2026-10-24-1500-garden.json')"))
    ok('with nothing left to act on, the finish shows its summary still, and no Tick it', (pg.text_content('#bubble .b-claude.done .b-claude-said') or '') == 'Beds drawn at 1:50; labels are left' and pg.locator('#bubble .b-claude.done .b-claude-tick').count() == 0)
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
    ok(f'Claude asking to tick it off: Tick it on its own line (B3) ({s and s["parts"]})', s and s['text'] == 'Claude handed Save a plan as a file back to you. Just now.'
       and s['parts'] == [['Added a note, Plan files.', ['Read', 'Undo']], ['Wants this task ticked off.', ['Tick it', 'Dismiss']]] and s['acts'] == ['Go to it'])
    pg.click('#ldSay .ld-part[data-part="ask done"] .b-claude-tick'); pg.wait_for_timeout(800)
    t = js(f"() => {{ const p = getProject('{gp}'), t = p.todos.find(t => t.text === 'Save a plan as a file'); return [t.done, p.activity.slice(-3).map(e => e.text)]; }}")
    s = say()
    ok(f'Tick it ticks it off as a tick does, said by its leader ({t})', t[0] is True and 'Done: Save a plan as a file' in t[1] and not any(x.startswith('Claude') for x in t[1])   # Claude writes nothing in Activity since 0.1.69
       and 'Ticked off: Save a plan as a file.' in pg.text_content('#toast') and 'Talal' in pg.text_content('#toast'))
    ok(f'the report stays while it has something left: the Undo ({s and s["parts"]})', s and s['parts'] == [['Added a note, Plan files.', ['Read', 'Undo']]])
    close_say(); pg.wait_for_timeout(300)

    # ---------- B3, C2: a finish with no update keeps Tick it, the start of its reply as plain words ----------
    js(S('r3', 'done', GARDEN, task='Tune the watering reminders', project='Garden planner', reply='## Done: the **reminders** now fire at `7:00`, see [the PR](https://x.example/pr/12).'))
    settle()
    ok(f'a finish alone waits with its leader, as before ({say() is None} {items(gp)})', say() is None and 'finished' in items(gp))
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    fin = js("""() => { const l = [...document.querySelectorAll('#bubble .b-claude.done')].find(x => x.textContent.includes('Tune the watering reminders'));
      return l && [l.querySelector('.ld-says').textContent, (l.querySelector('.b-claude-said') || {}).textContent, !!l.querySelector('.b-claude-tick'), l.querySelectorAll('.ld-part').length]; }""")
    ok(f'its card line keeps Tick it, with the start of its reply, markdown taken off ({fin})', fin and fin[0] == 'Claude handed Tune the watering reminders back to you. Just now.'
       and fin[1] == 'Done: the reminders now fire at 7:00, see the PR.' and fin[2] and fin[3] == 0)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    for k in ('r1', 'r2', 'r3'):
        js(f"() => window.__cf.delete('{k}.json')")
    settle()

    # ---------- an update with no finish to sit under is said on its own, as before ----------
    js(S('r4', 'working', GARDEN, task='Add plant icons', project='Garden planner'))
    settle()
    drop('2026-10-24-1520-garden.json', change('Publish the app', 'Store page written', [{'do': 'add-link', 'label': 'Store page', 'url': 'https://example.com/store'}]))
    settle()
    s = say()
    ok(f'one naming another task than the session works on is said at once, on its own ({s and s["text"]})', s and s['text'] == 'Claude added a link, Store page. Sent just now.'
       and s['words'] == ['Store page written'] and s['acts'] == ['Read', 'Undo', 'Go to it'])
    close_say(); js("() => window.__cf.delete('r4.json')"); settle()
    js(f"""() => {{ const p = getProject('{nc}'); addTasks(p, [{{ text: 'Rework how the leaders say what Claude asks on the status card, from the first line on', description: 'Old words.', due: '' }}], {{ id: p.milestones[0].id }}); persistNow(); }}""")
    drop('2026-10-24-1530-city.json', change('', 'A long summary of everything that happened, which is not the change asked about', [
        {'do': 'edit-description', 'task': 'Rework how the leaders say what Claude asks on the status card, from the first line on', 'description': 'New words.'}], project='Nullovation City'))
    settle()
    s = say()
    ok(f'what asks first names the change itself, never Claude\'s summary, its long title cut with an ellipsis ({s and s["text"]})', s and s['text'] == 'Claude wants your OK first: a new description for Rework how the leaders say what Claude asks on the status c\u2026. Sent just now.'
       and s['words'] == ['A long summary of everything that happened, which is not the change asked about'] and s['acts'][:3] == ['Read', 'Apply', 'Dismiss'])
    pg.click('#ldSay .b-claude-dismiss'); pg.wait_for_timeout(700)
    ok('Dismiss keeps the description, with its toast, and the bubble goes on', js(f"() => getProject('{nc}').todos.find(t => t.text.startsWith('Rework how the leaders')).description") == 'Old words.'
       and 'Kept the description of Rework how the leaders' in pg.text_content('#toast') and say() is None)

    # ---------- the start of a reply, as plain words ----------
    pr = js("""() => [News.plainReply('**Done**: see `a.py` and [the PR](https://x).'), News.plainReply('- fixed it * and more'), News.plainReply('Version 2. Then *this* and _that_ stay.'), News.plainReply('```js\\nx()\\n``` after')]""")
    ok(f'markdown comes off a reply: bold, code, links, a leading bullet ({pr})', pr == ['Done: see a.py and the PR.', 'fixed it and more', 'Version 2. Then this and _that_ stay.', 'after'])
    ok('nothing new in the city: reports are kept in this browser with the news', js("() => !('reports' in DB)") and len(js("() => News._test.reports()")) >= 4)

    b.close()

print(errors or 'no console errors')
