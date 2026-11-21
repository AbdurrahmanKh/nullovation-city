"""Pass 57: the leaders at work, and Claude's thought (0.1.92, City as My Terminal, Brainstorm 1, Round 2, i6's answer,
and Round 1, T1, The leader thinks it). The hooks read Claude's latest thought from the session's transcript as Claude
goes, after each tool it uses; the city puts each leader whose building Claude works on at the head of News, its face
with Claude's spark, wearing a thought bubble with that thought. First the hook, run as Claude Code runs it on
transcripts written as Claude Code writes them, then the city with a Claude folder held in memory."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

HOOK = ROOT / 'src' / 'setup' / 'nullovation-claude-status.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-think-'))
home, claude = work / 'home', work / 'Claude-Hooks'
garden = work / 'Garden planner'
for d in (home / '.claude', claude, garden):
    d.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONUTF8='1')

def line(kind, **o):
    return json.dumps({'type': kind, 'uuid': 'u' + str(time.time_ns()), 'timestamp': '2026-11-21T12:00:00.000Z', 'isSidechain': False, **o})
def assistant(*content, side=False):
    return line('assistant', isSidechain=side, message={'role': 'assistant', 'content': list(content)})
def thinking(text):
    return {'type': 'thinking', 'thinking': text, 'signature': 'sig'}
def write(path, *lines, pad=0):
    with open(path, 'w', encoding='utf-8') as f:
        if pad:
            filler = line('user', message={'role': 'user', 'content': 'x' * 2000}) + '\n'
            f.write(filler * (pad // len(filler) + 1))
        for l in lines:
            f.write(l + '\n')
def hook(state, event):
    return subprocess.run([sys.executable, str(HOOK), 'hook', state, str(claude)], input=json.dumps(event).encode('utf-8'), env=env, capture_output=True, timeout=60)
def session(sid):
    f = claude / (sid + '.json')
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None

try:
    # ---------- the hook ----------
    tr = work / 'transcript.jsonl'
    write(tr, line('user', message={'role': 'user', 'content': '# Task: Draw the beds'}),
          assistant(thinking('First I read how the beds are laid out.')),
          assistant({'type': 'tool_use', 'id': 't1', 'name': 'Read', 'input': {}}),
          assistant(thinking('The grid is 4 by 6, so each bed is one cell. I will draw them in the order they are planted.'), {'type': 'text', 'text': 'Drawing.'}),
          assistant(thinking('A subagent thinks something else.'), side=True))
    base = {'session_id': 'th-1', 'cwd': str(garden), 'transcript_path': str(tr)}
    hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': '# Task: Draw the beds'})
    ok('a new turn has no thought yet', 'thought' not in session('th-1'), session('th-1'))
    hook('working', {**base, 'hook_event_name': 'PostToolUse', 'tool_name': 'Read'})
    s = session('th-1')
    ok('after a tool, the session carries Claude\'s latest thought, a subagent\'s left out', s.get('thought') == 'The grid is 4 by 6, so each bed is one cell. I will draw them in the order they are planted.' and isinstance(s.get('thoughtAt'), int), s)
    long = ' '.join('Sentence number %d says a little more about the beds.' % i for i in range(30))
    write(tr, assistant(thinking(long)), assistant(thinking('')), assistant({'type': 'redacted_thinking', 'data': 'x'}))
    time.sleep(0.01); hook('working', {**base, 'hook_event_name': 'PostToolUse'})
    t = session('th-1')['thought']
    ok('a long thought shows its end, its last sentences, at most 240 characters and the ellipsis', t.startswith('…') and t.endswith('Sentence number 29 says a little more about the beds.') and len(t) <= 241, t)
    ok('an empty or redacted block is passed over for the one before it', 'Sentence number 29' in t)
    write(tr, assistant(thinking('Nearly done: the last bed is drawn.')), pad=3 * 1024 * 1024)
    t0 = time.time(); time.sleep(0.01); hook('working', {**base, 'hook_event_name': 'PostToolUse'})
    ok('a 3 MB transcript is read from its tail, in good time', session('th-1')['thought'] == 'Nearly done: the last bed is drawn.' and time.time() - t0 < 5, time.time() - t0)
    write(tr, line('user', message={'role': 'user', 'content': 'no thinking here'}))
    time.sleep(0.01); hook('working', {**base, 'hook_event_name': 'PostToolUse'})
    ok('a tool with no thought in reach keeps the last one', session('th-1')['thought'] == 'Nearly done: the last bed is drawn.')
    time.sleep(0.01); hook('done', {**base, 'hook_event_name': 'Stop'})
    ok('the reply ending takes the thought away', 'thought' not in session('th-1') and 'thoughtAt' not in session('th-1'), session('th-1'))
    time.sleep(0.01); hook('working', {**base, 'transcript_path': str(work / 'none.jsonl'), 'hook_event_name': 'PostToolUse'})
    ok('a transcript that is not there gives no thought, and the hook still writes', session('th-1')['state'] == 'working' and 'thought' not in session('th-1'))
    time.sleep(0.01); hook('working', {'session_id': 'th-2', 'cwd': str(garden), 'hook_event_name': 'PostToolUse'})
    ok('no transcript named: no thought', session('th-2') and 'thought' not in session('th-2'))
    for f in claude.iterdir():
        if f.is_file(): f.unlink()

    # ---------- the city ----------
    FAKE = """
window.__sub = new Map(); window.__ct = 1;
const fail = n => { const e = new Error(n); e.name = n; throw e; };
const subfile = path => ({ kind: 'file', name: path.split('/').pop(),
  getFile: async () => { const f = window.__sub.get(path); if (!f) fail('NotFoundError'); return new File([f.text], path.split('/').pop(), { lastModified: f.t }); },
  createWritable: async () => { let buf = ''; return { write: async d => { buf += d; }, close: async () => { window.__sub.set(path, { text: buf, t: Date.now() + (window.__ct++) }); } }; } });
const subdir = prefix => ({ kind: 'directory', name: prefix.split('/').pop(),
  getDirectoryHandle: async (n, o) => subdir(prefix + '/' + n),
  getFileHandle: async (n, o) => { const path = prefix + '/' + n; if (!window.__sub.has(path) && !(o && o.create)) fail('NotFoundError'); return subfile(path); },
  removeEntry: async n => { window.__sub.delete(prefix + '/' + n); },
  entries: async function* () { } });
window.__cdir = { kind: 'directory', name: 'Claude-Hooks',
  queryPermission: async () => 'granted', requestPermission: async () => 'granted',
  getDirectoryHandle: async (n, o) => subdir(n),
  getFileHandle: async (n, o) => { if (!window.__sub.has(n) && !(o && o.create)) fail('NotFoundError'); return subfile(n); },
  removeEntry: async n => { window.__sub.delete(n); },
  entries: async function* () { yield ['README-nullovation-city.txt', { kind: 'file', name: 'README-nullovation-city.txt', getFile: async () => new File(['x'], 'README-nullovation-city.txt') }];
    for (const k of [...window.__sub.keys()]) if (!k.includes('/')) yield [k, subfile(k)]; } };
window.showDirectoryPicker = async () => window.__cdir;
"""
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        ctx.add_init_script(TEST_CITY)
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t57')) { sessionStorage.setItem('nc-t57', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        other = ev("() => DB.projects.find(p => p.name !== 'Garden planner').id")
        other_name = ev(f"() => getProject('{other}').name")
        otherdir = work / 'Other'
        otherdir.mkdir()
        ev(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: 'l-g', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }});
            const o = getProject('{other}'); o.links.push({{ id: 'l-o', label: '', url: {json.dumps(str(otherdir))}, icon: 'folder', shortcut: true }}); delete o.leader;
            const l = blankLeader({{ name: 'Fern Rowe', role: 'Head Gardener' }}); DB.leaders.push(l); setLeader(p, l.id); window.changed(p); window.changed(o); }}""")
        task = ev(f"() => getProject('{gp}').todos.find(t => !t.done).text")
        ev("() => { News._test.forget(); News.renderSection(); }")
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ev("() => Settings.close()"); pg.wait_for_timeout(300)
        def put(sid, cwd, **o):
            now = int(time.time() * 1000)
            d = {'v': 1, 'app': 'nullovation-city', 'kind': 'claude-session', 'session': sid, 'cwd': str(cwd), 'task': task, 'project': '', 'state': 'working',
                 'at': now, 'since': now - 120000, 'started': now - 120000}
            d.update(o)
            ev("([k, text]) => { window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }", [sid + '.json', json.dumps(d)])
            ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(700)
        rows = lambda: ev("() => [...document.querySelectorAll('#newsWork .news-work')].map(r => ({ k: r.dataset.k, pid: r.dataset.pid, text: r.querySelector('.news-thought').textContent, cls: [...r.querySelector('.news-thought').classList], spark: !!r.querySelector('.news-work-spark svg') }))")

        ok('with nobody at work, no row, and News hides with nothing in it', ev("() => document.querySelector('#newsWork').hidden") and ev("() => document.querySelector('#sbNews').hidden"))
        put('c-1', garden, thought='The grid is 4 by 6, so each bed is one cell.', thoughtAt=int(time.time() * 1000))
        r = rows()
        ok('Claude at work on a building: its leader heads News, with Claude\'s spark, wearing the thought', len(r) == 1 and r[0]['pid'] == gp and r[0]['k'].startswith('ld:') and r[0]['spark']
           and r[0]['text'] == 'The grid is 4 by 6, so each bed is one cell.' and 'plain' not in r[0]['cls'], r)
        ok('News shows for it, though it holds no news', not ev("() => document.querySelector('#sbNews').hidden"))
        title = ev("() => document.querySelector('#newsWork .news-work-face').title")
        ok('its face says who works on what, where', title == 'Fern Rowe, Head Gardener: Claude is working on ' + task + ' in Garden planner. Show it.', title)
        ok('the thought\'s whole text is its tooltip', ev("() => document.querySelector('#newsWork .news-thought').title") == 'Claude thinks, working on ' + task + ': The grid is 4 by 6, so each bed is one cell.')
        pg.screenshot(path=str(SHOTS / '570-thought.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 520})
        put('c-1', garden, thought='I will draw them in the order they are planted.', thoughtAt=int(time.time() * 1000))
        r = rows()
        ok('a new thought moves in', r[0]['text'] == 'I will draw them in the order they are planted.' and 'new' in r[0]['cls'], r)
        ev("() => ClaudeWork.redraw()"); pg.wait_for_timeout(100)
        ok('the same thought drawn again stays put', 'new' not in rows()[0]['cls'])
        long = 'A ' + 'very ' * 80 + 'long thought.'
        put('c-1', garden, thought=long, thoughtAt=int(time.time() * 1000))
        ok('a long thought keeps to three lines', ev("() => { const s = document.querySelector('#newsWork .news-thought > span'); return s.getBoundingClientRect().height <= 3 * 12 * 1.35 + 2; }"))
        # no thought: the working line
        put('c-1', garden, thought='', thoughtAt=None)
        r = rows()
        ok('with no thought (older hooks, another agent), it says the working line', r[0]['text'] == 'Claude is working on ' + task + '. Started 2 minutes ago.' and 'plain' in r[0]['cls'], r)
        # a building with no leader: Proxima
        put('c-2', otherdir, task='Fix the roof', thought='The roof needs new tiles.', thoughtAt=int(time.time() * 1000))
        r = rows()
        ok('a building with no leader has Proxima at work for it, the rows by name', [x['k'] for x in r] == ['ld:' + ev(f"() => getProject('{gp}').leader"), 'px'], r)
        ok('Proxima wears her building\'s thought', any(x['k'] == 'px' and x['text'] == 'The roof needs new tiles.' for x in r), r)
        pg.screenshot(path=str(SHOTS / '571-thoughts-two.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 560})
        # a click shows the building and its card
        pg.click('#newsWork .news-work[data-pid="' + gp + '"] .news-work-face'); pg.wait_for_timeout(400)
        ok('a click on the face shows the building with its card', ev("() => Bubble.openId()") == gp)
        ev("() => Bubble.close()")
        # Quiet does not hide who is at work
        ev("() => Hold.setQuiet(true)"); pg.wait_for_timeout(100)
        ok('Quiet leaves the leaders at work in view', len(rows()) == 2)
        ev("() => Hold.setQuiet(false)")
        # the work over: the row goes
        put('c-1', garden, state='done', reply='Drew the beds.', thought='')
        put('c-2', otherdir, state='ended', task='Fix the roof', thought='')
        ok('once nobody works, the rows go', not rows() and ev("() => document.querySelector('#newsWork').hidden"), rows())
        b.close()
finally:
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
