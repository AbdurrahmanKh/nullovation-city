"""Claude's notes (0.1.71, Claude's Notes, Rounds 1 and 2).

Claude names a note's kind and the city puts it in its place: where a piece of work stands, a plan and a decision in the
task they are about, how something works with your notes; with no task, with your notes (K1, T1). A status, a plan and
how something works stay one note, brought up to date; a decision is a new note each time (K2). Every note has an icon,
picked in its panel and changed any time, Claude's too, and Claude's carry its spark and By Claude (M1, I1). A note keeps
its lines on its card (L1). A task's notes show under its description, open in the note panel with Back to the task, and
you can add your own there (Y1); a task's copy and the city summary carry them. The skill's checker knows the kinds. The
city opens with a Claude folder held in memory, as in test24."""
import json, pathlib, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, DATA, SKILLS, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

# ---------- the skill's checker ----------
CHECK = SKILLS / 'nullovation-city' / 'scripts' / 'check_plan.py'
def check(changes):
    f = pathlib.Path(tempfile.mkdtemp(dir=str(DATA))) / 'change.json'
    f.write_text(json.dumps({'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'Notes', 'changes': changes}), encoding='utf-8')
    r = subprocess.run([sys.executable, str(CHECK), str(f)], capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode('utf-8', 'replace')
rc, out = check([{'do': 'add-note', 'kind': 'status', 'task': 'Draw the beds on a grid', 'title': 'Beds', 'text': '1. Drawn\n2. Labels left'}])
ok(f'the checker takes a note with its kind, task and a few lines ({rc})', rc == 0 and 'WARNING' not in out.upper())
rc, out = check([{'do': 'add-note', 'kind': 'diary', 'title': 'Beds', 'text': 'x'}])
ok(f'and refuses a kind it does not know ({rc})', rc == 1 and '"kind"' in out)
rc, out = check([{'do': 'add-note', 'kind': 'how', 'icon': 'map', 'title': 'Beds', 'text': 'x'}])
ok(f'and an icon it does not know ({rc})', rc == 1 and '"icon"' in out)
rc, out = check([{'do': 'add-note', 'title': 'Beds', 'text': 'x'}])
ok(f'a note with no kind is warned about ({rc})', rc == 0 and 'no "kind"' in out)
rc, out = check([{'do': 'add-note', 'kind': 'decision', 'title': 'Beds', 'text': '\n'.join(f'line {i}' for i in range(12))}])
ok(f'and a long one that is not a plan ({rc})', rc == 0 and 'over 8 lines' in out)
rc, out = check([{'do': 'add-note', 'kind': 'plan', 'title': 'Beds', 'text': '\n'.join(f'step {i}' for i in range(12))}])
ok(f'a plan may run longer ({rc})', rc == 0 and 'over 8 lines' not in out)

FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
T1, T2 = 'Draw the beds on a grid', 'Save a plan as a file'

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t45')) { sessionStorage.setItem('nc-t45', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(600)
    js = pg.evaluate
    gp = js("() => DB.projects.find(p => p.name === 'Garden planner').id")
    js("""() => { const p = DB.projects.find(p => p.name === 'Garden planner');
      const l = blankLeader({ name: 'Talal', role: 'Head of Gardens', color: '#7FD6B5' }); DB.leaders.push(l); p.leader = l.id;
      News._test.typeMs(0); News._test.sayMs(120000); persistNow(); }""")
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    js("() => { window.__cmark = true; }")
    close_settings(pg)
    settle = lambda ms=3600: pg.wait_for_timeout(ms)
    n_drop = [0]
    def send(changes, task=None):
        n_drop[0] += 1
        d = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'Notes ' + str(n_drop[0]), 'changes': changes}
        if task: d['task'] = task
        js(f"() => window.__sub.set('inbox/2026-10-27-12{n_drop[0]:02d}-garden.json', {{ text: {json.dumps(json.dumps(d))}, t: Date.now() }})")
        settle()
    tnotes = lambda text: js(f"() => (getProject('{gp}').todos.find(t => t.text === {json.dumps(text)}).notes || []).map(n => ({{ title: n.title, text: n.text, icon: n.icon, by: n.by, kind: n.kind, up: !!n.updatedAt, id: n.id }}))")
    pnotes = lambda: js(f"() => getProject('{gp}').notes.map(n => ({{ title: n.title, icon: n.icon, by: n.by, kind: n.kind, up: !!n.updatedAt }}))")
    acts = lambda: js(f"() => getProject('{gp}').activity.map(e => e.text)")
    say = lambda: js("() => { const b = document.querySelector('#ldSay'); return b.hidden ? null : $('#ldSayText').textContent; }")
    close_say = lambda: js("() => { const c = document.querySelector('#ldSayClose'); if (!document.querySelector('#ldSay').hidden) c.click(); }")

    # ---------- K1: a status goes in its task ----------
    a0, p0 = acts(), pnotes()
    send([{'do': 'add-note', 'kind': 'status', 'title': 'Beds: where it stands', 'text': '1. Grid drawn\n2. Labels left\n- the middle path is wide'}], task=T1)
    n1 = tnotes(T1)
    ok(f'a status goes in the task the update names, by Claude, with its kind and the sticky note ({n1})', len(n1) == 1 and n1[0]['title'] == 'Beds: where it stands' and n1[0]['by'] == 'claude'
       and n1[0]['kind'] == 'status' and n1[0]['icon'] == 'sticky')
    ok('not in the project\'s Notes, and nothing in Activity', pnotes() == p0 and acts() == a0)
    ok(f'its leader says it ({say()})', say() == 'Claude added a note, Beds: where it stands. Sent just now.')
    close_say()

    # K2: the same kind again is brought up to date, and Undo takes the new version back
    send([{'do': 'add-note', 'kind': 'status', 'title': 'Beds: where they stand now', 'text': '1. Grid drawn\n2. Labels on'}], task=T1)
    n2 = tnotes(T1)
    ok(f'a status again is the same note, brought up to date (K2) ({n2})', len(n2) == 1 and n2[0]['id'] == n1[0]['id'] and n2[0]['title'] == 'Beds: where they stand now' and n2[0]['up'])
    s = say()
    ok(f'its leader says it is a new version ({s})', s == 'Claude added a new version of Beds: where they stand now. Sent just now.')
    pg.click('#ldSay .ld-undo'); pg.wait_for_timeout(400)
    n3 = tnotes(T1)
    ok(f'Undo puts the version before it back, as it was ({n3})', len(n3) == 1 and n3[0]['title'] == 'Beds: where it stands' and not n3[0]['up'])
    close_say()

    # a plan in its task, with the blueprint; a decision is a new note each time; the note's own task wins
    send([{'do': 'add-note', 'kind': 'plan', 'title': 'Plan for the beds', 'text': '1. Draw\n2. Label'},
          {'do': 'add-note', 'kind': 'decision', 'title': 'Grid of 30 cm', 'text': 'You chose 30 cm squares.'},
          {'do': 'add-note', 'kind': 'decision', 'task': T2, 'title': 'JSON files', 'text': 'Plans save as JSON.'}], task=T1)
    send([{'do': 'add-note', 'kind': 'decision', 'title': 'Grid of 30 cm', 'text': 'Kept, after trying 25 cm.'}], task=T1)
    n4, n5 = tnotes(T1), tnotes(T2)
    ok(f'a plan goes in its task with the blueprint ({[(x["kind"], x["icon"]) for x in n4]})', any(x['kind'] == 'plan' and x['icon'] == 'blueprint' for x in n4))
    ok(f'a decision is a new note each time, with the bulb ({[x["title"] for x in n4 if x["kind"] == "decision"]})', len([x for x in n4 if x['kind'] == 'decision']) == 2 and all(x['icon'] == 'bulb' for x in n4 if x['kind'] == 'decision'))
    ok(f'a note naming its own task goes there ({n5})', len(n5) == 1 and n5[0]['title'] == 'JSON files')
    close_say()

    # how something works goes with your notes, one per title, brought up to date; no task, and no kind, with your notes
    send([{'do': 'add-note', 'kind': 'how', 'title': 'Where the plan file is', 'text': 'In the app folder.'}], task=T1)
    send([{'do': 'add-note', 'kind': 'how', 'title': 'Where the plan file is', 'text': 'In the app folder, under plans.'}], task=T1)
    send([{'do': 'add-note', 'kind': 'status', 'title': 'The app overall', 'text': '1. Beds done'}, {'do': 'add-note', 'title': 'Loose thought', 'text': 'x'}])
    pn = [x for x in pnotes() if x['by'] == 'claude']
    ok(f'how something works goes with your notes, with the book, one per title, brought up to date ({pn})', [x['title'] for x in pn if x['kind'] == 'how'] == ['Where the plan file is']
       and [x for x in pn if x['kind'] == 'how'][0]['icon'] == 'book' and [x for x in pn if x['kind'] == 'how'][0]['up'])
    ok('a status naming no task goes with your notes (T1), and a note of no kind too, with the sticky note', any(x['title'] == 'The app overall' and x['kind'] == 'status' for x in pn)
       and any(x['title'] == 'Loose thought' and x['kind'] is None and x['icon'] == 'sticky' for x in pn))
    close_say()
    js("() => { const s = JSON.parse(localStorage.getItem('nullovation-city:news')); s.items = []; localStorage.setItem('nullovation-city:news', JSON.stringify(s)); }")

    # ---------- the project view: the cards, the task's notes, the icon, your own note ----------
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    cards = js("""() => [...document.querySelectorAll('.pv-note-card')].map(c => ({ head: c.querySelector('.pv-note-ht').textContent, icon: !!c.querySelector('.pv-note-h .note-ic svg'),
      claude: c.classList.contains('by-claude'), at: c.querySelector('.pv-note-at').textContent, spark: !!c.querySelector('.pv-note-at svg'), ws: getComputedStyle(c.querySelector('.pv-note-b') || c).whiteSpace }))""")
    how = next((c for c in cards if c['head'] == 'Where the plan file is'), None)
    ok(f'a card in Notes has its icon before its title, and Claude\'s its spark and By Claude ({how})', how and how['icon'] and how['claude'] and how['spark'] and how['at'].endswith('By Claude'))
    ok('a card keeps a note\'s lines, so a list reads as one (L1)', how and how['ws'] == 'pre-line')
    sec = pg.query_selector('[data-sec="notes"]'); sec.scroll_into_view_if_needed(); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SH / '452-note-cards.png'), clip=sec.bounding_box())
    js(f"() => FullView.openTask('{gp}', getProject('{gp}').todos.find(t => t.text === '{T1}').id)"); pg.wait_for_timeout(500)
    tl = js("""() => { const s = document.querySelector('#pvSide .pv-tnotes'); return s && { after: !!(document.querySelector('#pvTaskDesc').compareDocumentPosition(s) & 4),
      rows: [...s.querySelectorAll('.pv-tnote')].map(r => [r.querySelector('.pv-tnote-t').textContent, r.classList.contains('by-claude'), !!r.querySelector('.note-ic svg')]), add: !!s.querySelector('#pvTaskAddNote') }; }""")
    ok(f'the task panel lists its notes under the description, newest first, Claude\'s marked, with Add a note (Y1) ({tl})', tl and tl['after'] and tl['add'] and len(tl['rows']) == 4
       and tl['rows'][0][0] == 'Grid of 30 cm' and all(r[1] and r[2] for r in tl['rows']))
    pg.screenshot(path=str(SH / '450-task-notes.png'), clip=pg.query_selector('#pvSide').bounding_box())
    up0 = js(f"() => getProject('{gp}').updatedAt")
    a1 = acts()
    pg.click('#pvSide .pv-tnote:has-text("Beds: where it stands")'); pg.wait_for_timeout(400)
    np = js("""() => { const s = document.querySelector('#pvSide'); return { in: (s.querySelector('.pv-note-task') || {}).textContent, back: !!s.querySelector('#pvNoteBackTask'), toTask: !!s.querySelector('#pvNoteToTask'),
      icons: [...s.querySelectorAll('.pv-note-icon')].map(b => [b.dataset.icon, b.getAttribute('aria-pressed')]), when: s.querySelector('.pv-note-ed > .note:last-child').textContent }; }""")
    ok(f'a click opens it in the note panel: In its task, Back to the task, no Turn into a task ({np["in"]})', np['in'] == T1 and np['back'] and not np['toTask'])
    ok(f'the four icons, its own pressed (I1) ({np["icons"]})', np['icons'] == [['sticky', 'true'], ['bulb', 'false'], ['book', 'false'], ['blueprint', 'false']])
    ok(f'and who wrote it and when ({np["when"][:40]})', np['when'].strip().startswith('By Claude, '))
    pg.click('#pvSide .pv-note-icon[data-icon="book"]'); pg.wait_for_timeout(200)
    ok('a click on an icon picks it, pressed, the focus on it', js("() => document.activeElement && document.activeElement.dataset.icon === 'book' && document.activeElement.getAttribute('aria-pressed') === 'true'")
       and [x for x in tnotes(T1) if x['title'] == 'Beds: where it stands'][0]['icon'] == 'book')
    pg.screenshot(path=str(SH / '451-note-icons.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
    ok('Esc undoes it and goes back to the task', [x for x in tnotes(T1) if x['title'] == 'Beds: where it stands'][0]['icon'] == 'sticky' and js("() => !!document.querySelector('#pvSide #pvTaskDesc')"))
    pg.click('#pvSide .pv-tnote:has-text("Beds: where it stands")'); pg.wait_for_timeout(300)
    pg.click('#pvSide .pv-note-icon[data-icon="book"]'); pg.wait_for_timeout(200)
    pg.click('#pvNoteBackTask'); pg.wait_for_timeout(400)
    ok('kept on Back to the task: Claude\'s note takes the icon you picked, and it is not work: Updated and Activity stay',
       [x for x in tnotes(T1) if x['title'] == 'Beds: where it stands'][0]['icon'] == 'book' and js(f"() => getProject('{gp}').updatedAt") == up0 and acts() == a1 and js("() => !!document.querySelector('#pvSide #pvTaskDesc')"))
    # your own note in the task
    pg.click('#pvTaskAddNote'); pg.wait_for_timeout(300)
    ok('Add a note opens a new note in the task, the focus on its title, the sticky note pressed', js("() => document.activeElement && document.activeElement.id === 'pvNoteTitle'")
       and pg.get_attribute('#pvSide .pv-note-icon[data-icon="sticky"]', 'aria-pressed') == 'true' and pg.text_content('#pvSide .pv-note-task') == T1)
    pg.fill('#pvNoteTitle', 'Ask about the soil'); pg.fill('#pvNoteBody', 'Check the pH first.')
    pg.click('#pvSide .pv-top .btn-accent'); pg.wait_for_timeout(400)
    mine = [x for x in tnotes(T1) if x['title'] == 'Ask about the soil']
    ok(f'Done keeps it in the task, yours, and goes back to the task ({mine})', len(mine) == 1 and mine[0]['by'] is None and js("() => !!document.querySelector('#pvSide #pvTaskDesc')"))
    ok(f'with its line in Activity ({acts()[-1]})', acts()[-1] == 'Wrote a note in ' + T1 + ': Ask about the soil')
    pg.click('#pvSide .pv-tnote:has-text("Ask about the soil")'); pg.wait_for_timeout(300)
    pg.click('#pvNoteDelete'); pg.wait_for_timeout(400)
    ok('Delete note takes it out of the task, back to the task', not any(x['title'] == 'Ask about the soil' for x in tnotes(T1)) and js("() => !!document.querySelector('#pvSide #pvTaskDesc')"))
    js("() => FullView.close()"); js("() => MapView.deselect()"); pg.wait_for_timeout(300)

    # ---------- the copies, the summary, search, saved data ----------
    copy = js(f"() => taskForClaude(getProject('{gp}'), getProject('{gp}').todos.find(t => t.text === '{T1}'))")
    ok('a task\'s copy carries its notes, for the next session (K1)', '## Notes on this task' in copy and '### Beds: where it stands' in copy and 'By Claude, status' in copy and '1. Grid drawn\n2. Labels left' in copy)
    js("() => ClaudeWork.cityChanged()"); pg.wait_for_timeout(2400)
    summ = js("() => window.__subjson('city/summary.json')")
    task = next(t for m in next(p for p in summ['projects'] if p['name'] == 'Garden planner')['milestones'] for t in m['open'] if t['task'] == T1)
    ok(f'the city summary gives an open task its notes, Claude\'s with by and kind ({[n["title"] for n in task.get("notes", [])]})', any(n['title'] == 'Beds: where it stands' and n.get('by') == 'Claude' and n.get('kind') == 'status' for n in task.get('notes', [])))
    found = js(f"() => {{ App.filter.q = norm('labels left'); const r = matchesFilter(getProject('{gp}')); App.filter.q = ''; return r; }}")
    ok('search finds a building by a note in one of its tasks', found)
    pg.reload()
    pg.wait_for_function("() => typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000); pg.wait_for_timeout(500)
    kept = tnotes(T1)
    ok(f'a task\'s notes, with their icons, kinds and authors, survive a reload ({len(kept)})', len(kept) == 4 and any(x['icon'] == 'book' and x['kind'] == 'status' and x['by'] == 'claude' for x in kept))

    # a task turned into a note: its notes join Notes; Undo puts them back in the task
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    js(f"() => FullView.openTask('{gp}', getProject('{gp}').todos.find(t => t.text === '{T2}').id)"); pg.wait_for_timeout(400)
    pg.click('#pvTaskToNote'); pg.wait_for_timeout(400)
    ok('a task turned into a note: its own notes join the project\'s Notes', any(x['title'] == 'JSON files' for x in pnotes()))
    js("() => document.querySelector('#toast .toast-act').click()"); pg.wait_for_timeout(400)
    ok('Undo puts them back in the task', [x['title'] for x in tnotes(T2)] == ['JSON files'] and not any(x['title'] == 'JSON files' for x in pnotes()))
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    print('errors:', errors)
    ok('no console errors', not errors)
    b.close()
