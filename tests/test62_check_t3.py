"""Check T3 (0.1.97, Check T3, Round 1): every page of Claude's takes you to its T3 conversation.

Check T3 takes the place of Go to it on Claude's pages (M1), a link on News and a button where a page has buttons; it
opens the task's thread, else the thread the watcher sees, else T3 Code itself (F1), and none for a session in a
terminal or with Open in Claude set to Claude only. A session with no task is named by its T3 thread's title once the
watcher sees it (F3); a click on a leader at work in News opens its T3 conversation too (M2's note). First the hooks:
a session file made again after three quiet days reads its task from the transcript, so the finish names the task."""
import json, os, pathlib, shutil, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, DATA, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

# ---------- the hooks: a session file made again keeps its task ----------
SCRIPT = ROOT / 'src' / 'setup' / 'nullovation-claude-status.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-t62-', dir=str(DATA)))
folder = work / 'Claude'
env = dict(os.environ, HOME=str(work), USERPROFILE=str(work), PYTHONUTF8='1')
env.pop('CLAUDE_CODE_ENTRYPOINT', None)
def hook(state, event):
    return subprocess.run([sys.executable, str(SCRIPT), 'hook', state, str(folder)], input=json.dumps(event).encode('utf-8'), env=env, capture_output=True, timeout=60)
def sess(name):
    f = folder / (name + '.json')
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None
def transcript(path, entries):
    path.write_text(''.join(json.dumps(e) + '\n' for e in entries), encoding='utf-8')
COPY = "[T3 Code: this message came through T3 Code's tools, not from the user typing in this chat.]\n\n# Task: Draw the beds on a grid\nProject: Garden planner\nLeader: Ahmed, Mine Supervisor\n\n## Description\nThe beds."
tr = work / 'old.jsonl'
entries = [
    {'type': 'user', 'message': {'role': 'user', 'content': COPY}},
    {'type': 'user', 'isMeta': True, 'message': {'content': [{'type': 'text', 'text': '# Task: A skill example\nProject: Nope'}]}},
    {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'content': '# Task: A file Claude read\nProject: Other'}]}},
    {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': '# Task: Claude quoting a copy\nProject: Other'}]}},
    {'type': 'user', 'message': {'content': '<task-notification>\n# Task: A notice\n</task-notification>'}},
    {'type': 'user', 'message': {'content': 'can we start building then?'}},
]
transcript(tr, entries)
base = {'session_id': 's-old', 'cwd': 'C:\\Users\\me\\garden', 'transcript_path': str(tr)}
r = hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': 'what is left for this task?'})
d = sess('s-old')
ok('a session file made again, after three quiet days cleared it, reads its task from the copy in the transcript', d and d.get('task') == 'Draw the beds on a grid' and d.get('project') == 'Garden planner', d)
ok('its ask is the new prompt, and the hook printed nothing', d and d.get('ask') == 'what is left for this task?' and r.stdout == b'' and r.returncode == 0, d)
transcript(tr, entries + [{'type': 'user', 'message': {'content': [{'type': 'text', 'text': '# Task: Water the beds on time\nProject: Garden planner'}]}}])
(folder / 's-old.json').unlink()
hook('working', {**base, 'hook_event_name': 'PostToolUse', 'tool_name': 'Edit'})
ok('the latest copy names it, as each prompt does, read from any event', (sess('s-old') or {}).get('task') == 'Water the beds on time', sess('s-old'))
tr2 = work / 'plain.jsonl'
transcript(tr2, [{'type': 'user', 'message': {'content': 'tidy the css'}}])
hook('working', {**base, 'session_id': 's-plain', 'transcript_path': str(tr2), 'hook_event_name': 'UserPromptSubmit', 'prompt': 'tidy the css'})
ok('a session that began on no copy has no task', 'task' not in (sess('s-plain') or {'task': 1}), sess('s-plain'))
transcript(tr2, [{'type': 'user', 'message': {'content': COPY}}])
hook('done', {**base, 'session_id': 's-plain', 'transcript_path': str(tr2), 'hook_event_name': 'Stop'})
ok('a file already there is not read again: the transcript is read only for a new file', 'task' not in (sess('s-plain') or {'task': 1}), sess('s-plain'))
hook('working', {**base, 'session_id': 's-gone', 'transcript_path': str(work / 'missing.jsonl'), 'hook_event_name': 'UserPromptSubmit', 'prompt': 'hello'})
ok('a transcript that is not there changes nothing', (sess('s-gone') or {}).get('ask') == 'hello' and 'task' not in sess('s-gone') and not (folder / 'hook-errors.log').exists())
shutil.rmtree(work, ignore_errors=True)

# ---------- the city ----------
FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
OPENED = """window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (/^(nullovation-t3|t3code|claude|claude-cli):/i.test(href)) { window.__opened.push(href); return; } return anchorClick.call(this); };"""
GARDEN = 'C:\\Users\\me\\garden'
def S(session, state, mins=0, **kw):
    """A session file as the hooks write it, last heard from mins minutes ago."""
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(GARDEN)}, at: {at}, since: {at} - 120000, started: {at} - 300000{extra} }})"

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t62')) { sessionStorage.setItem('nc-t62', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    ctx.add_init_script(OPENED)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(800)
    js = pg.evaluate
    for k in ['#gusSay', '#pxSay', '#ldSay']:
        js(f"() => {{ const x = document.querySelector('{k}'); if (x && !x.hidden) {{ const m = x.querySelector('.lc-min'); if (m) m.click(); }} }}")
    js("() => { News._test.forget(); News._test.typeMs(0); }")
    gp = js("() => DB.projects.find(p => p.name === 'Garden planner').id")
    js(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: uid('l'), label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true }});
      const l = blankLeader({{ name: 'Ahmed', role: 'Mine Supervisor', color: '#7FD6B5' }}); DB.leaders.push(l); p.leader = l.id; persistNow(); }}""")
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    js("() => { window.__cmark = true; }")
    close_settings(pg)
    beds = 'Draw the beds on a grid'
    other = js(f"() => getProject('{gp}').todos.find(t => !t.done && t.text !== {json.dumps(beds)}).text")
    poll = lambda ms=900: (js("() => ClaudeWork.poll()"), pg.wait_for_timeout(ms))
    say = lambda: js("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null;
      return { type: b.dataset.type, text: document.querySelector('#ldSayText').textContent, acts: [...b.querySelectorAll('#ldSayActs button')].map(x => x.textContent),
        links: [...b.querySelectorAll('.ld-t3-link')].map(x => [x.tagName, x.textContent, x.title]), go: !!b.querySelector('.ld-go') }; }""")
    mini = lambda: (js("() => { const c = document.querySelector('#ldSayMin'); if (!document.querySelector('#ldSay').hidden && c) c.click(); }"), pg.wait_for_timeout(300))
    def face(name):
        js(f"() => {{ const t = [...document.querySelectorAll('#newsList .news-tile')].find(x => x.textContent.includes({json.dumps(name)})); if (t) t.querySelector('.news-face').click(); }}")
        pg.wait_for_timeout(400)
    opened = lambda: js("() => window.__opened.splice(0)")

    # ---------- a finish with no thread to name: Check T3 opens T3 itself (F1) ----------
    js(S('f1', 'done', 5, entry='t3-code', ask='what is left for this task?', reply='There is no code left to write. What remains is setup and testing on your PC.'))
    poll()
    ok('the finish waits in News, as before (F2: waits with its leader)', say() is None and js("() => News.items().some(it => it.moment === 'finished')"))
    face('Ahmed')
    s = say()
    ok(f'its face opens it: a News page that names the conversation by its words, since it began on no task ({s and s["text"]})', s and s['type'] == 'news' and s['text'].startswith('Claude handed “what is left for this task?” back to you.'), s)
    ok('Check T3, a link, in place of Go to it: no buttons on News', s and s['acts'] == [] and not s['go'] and [l[:2] for l in s['links']] == [['A', 'Check T3']], s)
    ok('it says it opens T3 Code, since the city cannot tell which thread it is', s and s['links'][0][2] == 'Opens T3 Code: the city cannot tell which thread this is', s)
    pg.screenshot(path=str(SH / '620-check-t3-finish.png'), clip=pg.query_selector('#ldSay').bounding_box())
    opened()
    pg.click('#ldSay .ld-t3-link'); pg.wait_for_timeout(200)
    ok('a click opens T3 Code, through the link Open T3 follows, and the bubble stays', opened() == ['t3code://new'] and say() is not None)
    js("() => { T3.setTiles('claude'); News.redraw(); }"); pg.wait_for_timeout(200)
    ok('with Open in Claude set to Claude only, there is no T3 to open: no Check T3', (say() or {}).get('links') == [], say())
    js("() => { T3.setTiles('both'); News.redraw(); }"); pg.wait_for_timeout(200)
    mini()

    # ---------- a session in a terminal has no conversation in T3 ----------
    js(S('f2', 'done', 4, entry='cli', ask='tidy the css', reply='Tidied.'))
    poll()
    js("() => News._test.flat(true)")
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    card = js("""() => [...document.querySelectorAll('#bubble .ld-line')].map(l => ({ moment: l.dataset.moment, says: l.querySelector('.ld-says').textContent,
      t3: [...l.querySelectorAll('.ld-t3-link, .ld-t3')].map(x => x.textContent), go: !!l.querySelector('.ld-go') }))""")
    fin = {c['says'].split(' back')[0]: c for c in card if c['moment'] == 'finished'}
    ok(f'on the status card the same: Check T3 on the finish in T3, none on the one in a terminal, no Go to it ({[(k, v["t3"]) for k, v in fin.items()]})',
       fin.get('Claude handed “what is left for this task?”', {}).get('t3') == ['Check T3'] and fin.get('Claude handed “tidy the css”', {}).get('t3') == []
       and not any(c['go'] for c in card), card)
    js("() => { MapView.select(null); News._test.flat(false); }"); pg.wait_for_timeout(300)

    # ---------- what Claude asks first, on its own: Check T3 after its buttons, and the ask stays ----------
    js(f"() => window.__sub.set('inbox/2026-11-27-1200-garden.json', {{ text: {json.dumps(json.dumps({'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'task': other, 'summary': 'A clearer description', 'changes': [{'do': 'edit-description', 'task': other, 'description': 'Clearer.'}]}))}, t: Date.now() }})")
    pg.wait_for_timeout(4500)
    s = say()
    ok(f'Need Approval opens by itself, with Check T3 after its buttons and no Go to it ({s and s["acts"]})', s and s['type'] == 'approval' and s['acts'] == ['Read', 'Apply', 'No', 'Check T3'] and not s['go'], s)
    pg.click('#ldSay .ld-t3'); pg.wait_for_timeout(300)
    ok('with no thread on its task, Check T3 opens T3 Code, and the ask stays until answered', opened() == ['t3code://new'] and (say() or {}).get('type') == 'approval', say())
    js(f"""() => {{ const t = getProject('{gp}').todos.find(x => x.text === {json.dumps(other)});
      t.threads = [{{ id: 'cli:t-7', env: 'env-1234', agent: 'Opus 5.5', kind: 'build', title: t.text, at: Date.now() - 600000, last: Date.now() - 60000 }}]; window.changed(getProject('{gp}')); News.redraw(); }}""")
    pg.wait_for_timeout(300)
    tip = js("() => (document.querySelector('#ldSay .ld-t3') || {}).title")
    pg.click('#ldSay .ld-t3'); pg.wait_for_timeout(200)
    ok(f'once the task has a thread, Check T3 opens it, saying where it lands ({tip})', opened() == ['t3code://threads/env-1234/cli%3At-7'] and tip.startswith('Opens its T3 thread, ' + other + ': Opus 5.5'), tip)
    js("() => { const n = document.querySelector('#ldSay .b-claude-dismiss'); if (n) n.click(); }"); pg.wait_for_timeout(400)
    mini()

    # ---------- waiting for your OK, and stopped on an error: Check T3 in place of Go to it ----------
    js(f"""() => {{ const t = getProject('{gp}').todos.find(x => x.text === {json.dumps(beds)});
      t.threads = [{{ id: 'cli:t-9', env: 'env-1234', agent: 'Opus 5.5', kind: 'build', title: t.text, at: Date.now() - 600000, last: Date.now() - 60000 }}]; window.changed(getProject('{gp}')); }}""")
    js(S('w1', 'waiting', 0, entry='t3-code', task=beds, project='Garden planner', ask='# Task: ' + beds, wait='approval', event='PermissionRequest'))
    poll(1500)
    s = say()
    ok(f'Claude needing your OK opens by itself, with Check T3 and no Go to it ({s and (s["type"], s["acts"])})', s and s['type'] == 'approval' and s['text'].startswith('Claude needs your OK on this task.') and s['acts'] == ['Check T3'] and not s['go'], s)
    pg.screenshot(path=str(SH / '621-check-t3-approval.png'), clip=pg.query_selector('#ldSay').bounding_box())
    pg.click('#ldSay .ld-t3'); pg.wait_for_timeout(200)
    ok('which opens the task\'s thread in T3', opened() == ['t3code://threads/env-1234/cli%3At-9'])
    js("() => { window.__cf.delete('w1.json'); }")
    js(S('e1', 'failed', 0, entry='t3-code', ask='run the tests'))
    poll(1500)
    s = say()
    ok(f'an error: Critical, with Check T3 that opens T3 Code ({s and (s["type"], s["acts"])})', s and s['type'] == 'critical' and s['acts'] == ['Check T3'] and not s['go'], s)
    mini()
    js("() => { window.__cf.delete('e1.json'); }"); poll(400)

    # ---------- a non-Claude page keeps Go to it ----------
    js(f"() => {{ const p = getProject('{gp}'), t = nextTask(p); News.add(p, 'due', {{ task: t.text }}, {{ ref: {{ day: ymd(), tid: t.id }}, key: 'due:t62' }}); }}")
    pg.wait_for_timeout(900)
    s = say()
    ok(f'what is not Claude\'s keeps Go to it, and has no Check T3 ({s and (s["type"], s["acts"])})', s and s['type'] == 'headsup' and s['acts'] == ['Go to it'] and s['links'] == [], s)
    mini()

    # ---------- the conversation's title, from the watcher (F3), and a leader at work (M2's note) ----------
    js(S('k1', 'working', 0, entry='t3-code', ask='can you fix the reminders please', thought='Checking the reminder times.'))
    poll()
    K = f"() => ClaudeWork.what(getProject('{gp}'), ClaudeWork.sessionsOf(getProject('{gp}')).find(s => s.session === 'k1'))"
    ok(f'with no watcher, a session with no task is named by its prompt in quotes ({js(K)})', js(K) == '“can you fix the reminders please”')
    w = {'app': 'nullovation-city', 'kind': 't3-watch', 'at': 0, 'running': True, 't3': '0.1.11', 'threads': [
        {'id': 'cli:w-1', 'env': 'env-1234', 'title': 'Fix the reminders', 'status': 'running', 'folder': GARDEN, 'updated': 0, 'last': {'text': 'Looking at the times.'}}]}
    js("(d) => { d.at = Date.now(); d.threads[0].updated = Date.now(); window.__sub.set('t3/watch.json', { text: JSON.stringify(d), t: Date.now() + (window.__ct++) }); }", w)
    js("() => T3.readWatch()"); pg.wait_for_timeout(500)
    ok(f'once the watcher sees its thread, by the thread\'s title as T3 lists it ({js(K)})', js(K) == '“Fix the reminders”')
    row = js("() => { const r = document.querySelector('#newsWork .news-work'); return r ? { title: r.querySelector('.news-work-face').title, thought: r.querySelector('.news-thought').textContent } : null; }")
    ok(f'the leader at work in News names it so too, and says it can check T3 ({row})', row and row['title'] == 'Ahmed, Mine Supervisor: Claude is working on “Fix the reminders” in Garden planner. Talk about it, and check T3.' and row['thought'] == 'Checking the reminder times.', row)
    opened()
    pg.click('#newsWork .news-work-face'); pg.wait_for_timeout(400)
    s = say()
    ok(f'a click opens its bubble on that conversation, and its T3 conversation too ({s and s["text"]})', s and s['text'].startswith('Claude is working on “Fix the reminders”') and opened() == ['t3code://threads/env-1234/cli%3Aw-1'], s)
    mini()

    ok('no console errors', not errors, errors[:3])
    b.close()
