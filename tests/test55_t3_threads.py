"""Pass 55: a task's T3 threads (0.1.90, City as My Terminal, Round 1, A1 and A2). Every task keeps the threads its
sends started; the T3 tile goes on in the task's thread (t3 thread send), Think's included, with New thread behind the
more button; Open on the task's row, in its panel and in its leader's news says where it lands, the agent and the
thread's state. First the helper alone, against a fake t3 command, as in pass 53; then the city with a Claude folder
held in memory, the helper run on what the city wrote."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

SETUP = ROOT / 'src' / 'setup' / 'nullovation-t3-links.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-t3th-'))
home, local, claude = work / 'home', work / 'local', work / 'Claude-Hooks'
t3home = home / '.t3'
garden = work / 'Garden planner'
for d in (home / '.claude', local, claude, t3home / 'bin', t3home / 'userdata', garden):
    d.mkdir(parents=True, exist_ok=True)
(t3home / 'userdata' / 'environment-id').write_text('env-1234\n', encoding='utf-8')
(home / '.claude' / 'nullovation-city.json').write_text(json.dumps({'app': 'nullovation-city', 'kind': 'claude-folder', 'folder': str(claude)}), encoding='utf-8')

# the fake t3: thread start and thread send, each recorded with what came on its input
FAKE_T3 = work / 'fake_t3.py'
LOG, STATE = work / 't3-calls.json', work / 't3-state.json'
FAKE_T3.write_text(r'''import json, os, sys
log, state = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
data = sys.stdin.buffer.read().decode('utf-8') if '-' in args else ''
calls = json.load(open(log, encoding='utf-8')) if os.path.exists(log) else []
calls.append({'args': args, 'stdin': data})
json.dump(calls, open(log, 'w', encoding='utf-8'))
st = json.load(open(state, encoding='utf-8')) if os.path.exists(state) else {'down': False}
if st['down']:
    sys.stderr.write('No running T3 Code server uses C:\\x\\.t3. Start T3 Code, then retry.\n'); sys.exit(1)
if args[:2] == ['thread', 'start']:
    print(json.dumps({'threadId': 'cli:thread-' + str(len(calls)), 'projectId': 'proj-1', 'runId': 'run-1'})); sys.exit(0)
if args[:2] == ['thread', 'send']:
    if args[2].startswith('gone'):
        sys.stderr.write('Thread ' + args[2] + ' was not found.\n'); sys.exit(1)
    print(json.dumps({'threadId': args[2], 'queued': False})); sys.exit(0)
sys.exit(2)
''', encoding='utf-8')
WRAP = work / 'wrap.py'
WRAP.write_text(f'import runpy, sys\nsys.argv = [{str(FAKE_T3)!r}, {str(LOG)!r}, {str(STATE)!r}] + sys.argv[1:]\nrunpy.run_path({str(FAKE_T3)!r}, run_name="__main__")\n', encoding='utf-8')
(t3home / 'bin' / 't3.cmd').write_text('@echo off\r\n' f'set "T3CODE_HOME={t3home}"\r\nset "ELECTRON_RUN_AS_NODE=1"\r\n' f'"{sys.executable}" "{WRAP}" %*\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')

env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(local), NULLOVATION_QUIET='1', PYTHONUTF8='1')
env.pop('T3CODE_HOME', None)
def helper(*args):
    return subprocess.run([sys.executable, str(SETUP), *map(str, args)], env=env, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
def calls():
    return json.loads(LOG.read_text(encoding='utf-8')) if LOG.exists() else []
def answer(ident):
    f = claude / 't3' / (ident + '.done.json')
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None
def put_send(ident, **o):
    (claude / 't3').mkdir(exist_ok=True)
    d = {'app': 'nullovation-city', 'kind': 't3-send', 'version': 1, 'id': ident, 'at': int(time.time() * 1000), 'project': 'Garden planner',
         'folder': str(garden), 'title': 'Draw the beds', 'message': '# Task: Draw the beds\n\nProject: Garden planner'}
    d.update(o)
    (claude / 't3' / ('send-' + ident + '.json')).write_text(json.dumps(d), encoding='utf-8')
def state(**o):
    st = {'down': False}; st.update(o); STATE.write_text(json.dumps(st), encoding='utf-8')
last = lambda: (local / 'Nullovation City' / 'last-t3.txt').read_text(encoding='utf-8') if (local / 'Nullovation City' / 'last-t3.txt').exists() else ''

try:
    # ---------- the helper: a send that names a thread goes on in it ----------
    state()
    r = helper('--help')
    ok('--help says a send naming a thread goes on in it', r.returncode == 0 and b't3 thread send <thread> - --json' in r.stdout)
    put_send('cont0001', thread='mcp:3ae4dcbf-871f', message='# Task: Draw the beds\n\nBuild it, in عربي too.')
    r = helper('open', 'nullovation-t3:send/cont0001')
    a, c = answer('cont0001'), calls()[-1]
    ok('it runs t3 thread send on that thread, the copy on its input', r.returncode == 0 and c['args'] == ['thread', 'send', 'mcp:3ae4dcbf-871f', '-', '--json']
       and c['stdin'] == '# Task: Draw the beds\n\nBuild it, in عربي too.', c)
    ok('and answers ok, naming the same thread, continued, with T3\'s environment', a and a['ok'] and a['thread'] == 'mcp:3ae4dcbf-871f' and a['continued'] is True and a['env'] == 'env-1234', a)
    ok('the run is noted as a send to that thread, without the copy', 'to T3 thread mcp:3ae4dcbf-871f' in last() and 'عربي' not in last(), last())
    put_send('cont0002', thread='mcp:x', provider='claudeAgent', model='claude-haiku-5-5')
    helper('open', 'nullovation-t3:send/cont0002')
    ok('a thread goes on with its own agent: no provider or model is passed', calls()[-1]['args'] == ['thread', 'send', 'mcp:x', '-', '--json'], calls()[-1]['args'])
    n = len(calls())
    put_send('cont0003', thread='bad thread & x')
    helper('open', 'nullovation-t3:send/cont0003')
    ok('a thread id T3 would not know is refused, and nothing runs', answer('cont0003')['ok'] is False and 'thread T3 would not know' in answer('cont0003')['error'] and len(calls()) == n, answer('cont0003'))
    put_send('cont0004', thread='gone-1')
    helper('open', 'nullovation-t3:send/cont0004')
    ok('a thread T3 no longer has says why, in the city\'s words', answer('cont0004')['error'] == 'T3 could not send it to the thread: Thread gone-1 was not found.', answer('cont0004'))
    put_send('cont0005', thread='mcp:y', folder=str(work / 'not on this PC'))
    helper('open', 'nullovation-t3:send/cont0005')
    ok('going on in a thread needs no folder on the PC', answer('cont0005')['ok'] is True, answer('cont0005'))
    state(down=True)
    put_send('cont0006', thread='mcp:y')
    helper('open', 'nullovation-t3:send/cont0006')
    ok('with T3 not running, it says so', answer('cont0006')['error'] == 'T3 Code is not running. Open it, then send again.', answer('cont0006'))
    state()
    put_send('start001')
    helper('open', 'nullovation-t3:send/start001')
    ok('a send naming no thread still starts one', calls()[-1]['args'][:2] == ['thread', 'start'] and answer('start001')['thread'].startswith('cli:thread-') and 'continued' not in answer('start001'))
    for f in (claude / 't3').iterdir():
        f.unlink()

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
  removeEntry: async n => { if (!window.__sub.has(prefix + '/' + n)) fail('NotFoundError'); window.__sub.delete(prefix + '/' + n); },
  entries: async function* () { } });
window.__cdir = { kind: 'directory', name: 'Claude-Hooks',
  queryPermission: async () => 'granted', requestPermission: async () => 'granted',
  getDirectoryHandle: async (n, o) => subdir(n),
  entries: async function* () { yield ['README-nullovation-city.txt', { kind: 'file', name: 'README-nullovation-city.txt', getFile: async () => new File(['x'], 'README-nullovation-city.txt') }]; } };
window.showDirectoryPicker = async () => window.__cdir;
window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (/^(nullovation-t3|t3code|claude|claude-cli):/i.test(href)) { window.__opened.push(href); return; } return anchorClick.call(this); };
"""
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        ctx.add_init_script(TEST_CITY)
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t55')) { sessionStorage.setItem('nc-t55', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        ev(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: 'l-t3', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }}); window.changed(p); }}""")
        task = ev(f"() => getProject('{gp}').todos.find(t => !t.done).text")
        tid = ev(f"() => getProject('{gp}').todos.find(t => !t.done).id")
        T = f"getProject('{gp}').todos.find(t => t.id === '{tid}')"
        quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true); }")
        said = lambda: ev("() => { const t = document.querySelector('#toast'); return t.classList.contains('show') ? t.textContent : ''; }")
        tile = lambda: ev("() => { const e = document.querySelector('.oc-panel .oc-tile[data-kind=\"t3\"]'); return e ? { note: (e.querySelector('.oc-tile-note') || {}).textContent || '', title: e.getAttribute('title') || '' } : null; }")
        sends = lambda: ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))")
        threads = lambda: ev(f"() => {T}.threads || []")
        def open_task_panel():
            ev("() => OpenInClaude.close()")
            if not ev("() => FullView.isOpen()"):
                ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
            if not ev("() => !!document.querySelector('#pvTaskClaude')"):
                pg.click(f'li.task[data-id="{tid}"] .task-title'); pg.wait_for_timeout(300)
            quiet()
            pg.locator('#pvTaskClaude').scroll_into_view_if_needed(); pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
        def sync_out():
            (claude / 't3').mkdir(exist_ok=True)
            files = ev("() => [...window.__sub].filter(([k]) => k.startsWith('t3/')).map(([k, f]) => [k, f.text])")
            for f in (claude / 't3').iterdir():
                if ('t3/' + f.name) not in dict(files): f.unlink()
            for path, text in files:
                (claude / path).write_text(text, encoding='utf-8')
        def sync_in():
            on_disk = {('t3/' + f.name): f.read_text(encoding='utf-8') for f in (claude / 't3').iterdir() if f.suffix == '.json'}
            ev("""(files) => { for (const k of [...window.__sub.keys()]) if (k.startsWith('t3/') && !(k in files)) window.__sub.delete(k);
              for (const [k, text] of Object.entries(files)) window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }""", on_disk)
        def run_link():
            href = ev("() => window.__opened.filter(x => x.startsWith('nullovation-t3:')).pop()")
            sync_out(); r = helper('open', href); sync_in()
            pg.wait_for_timeout(1400)
            return r

        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ev("() => Settings.close()")
        before = ev(f"() => getProject('{gp}').updatedAt")
        acts = ev(f"() => getProject('{gp}').activity.length")

        # ---------- the first send starts a thread, and the task keeps it ----------
        open_task_panel()
        ok('a task with no thread: the T3 tile starts one, on its agent, with no thread line', tile()['note'] == 'default' and 'A new T3 thread in' in tile()['title']
           and not ev("() => !!document.querySelector('.oc-thread')") and ev("() => !!document.querySelector('#ocAgentPick')"), tile())
        ev("() => { window.__opened.length = 0; }")
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = sends()[0]
        ok('the send names no thread', 'thread' not in s, s)
        run_link()
        th = threads()
        ok('once T3 answers, the task keeps the thread: its id, T3\'s environment, the agent, Build it, its title', len(th) == 1 and th[0]['id'].startswith('cli:thread-')
           and th[0]['env'] == 'env-1234' and th[0]['agent'] == 'default' and th[0]['kind'] == 'build' and th[0]['title'] == task and th[0]['last'] >= th[0]['at'], th)
        first = th[0]['id']
        ok('keeping it is not work: Updated stays and Activity is left alone', ev(f"() => getProject('{gp}').updatedAt") == before and ev(f"() => getProject('{gp}').activity.length") == acts)
        ok('the toast says it was sent, with Open', said().startswith('Sent to T3: ' + task + '.'), said())
        # its row and its panel
        row = ev(f"() => {{ const b = document.querySelector('li.task[data-id=\"{tid}\"] .t3-open'); return b ? {{ title: b.title, label: b.getAttribute('aria-label'), cls: b.className }} : null; }}")
        ok('its row wears the T3 mark, saying where it lands: the agent, and when it was sent', row and row['title'] == 'Opens its T3 thread, ' + task + ": T3's default agent, sent just now." and row['label'] == 'Open in T3: ' + task, row)
        ok('the mark sits after the title, before the shift', ev(f"() => {{ const li = document.querySelector('li.task[data-id=\"{tid}\"]'); const k = [...li.children]; return k.indexOf(li.querySelector('.t3-open')) > k.indexOf(li.querySelector('.task-title')); }}"))
        ok('the task panel lists its thread over Claude, saying where it lands', ev("() => [...document.querySelectorAll('.pv-t3-sec .t3-thread')].map(e => e.textContent)") == [task + "T3's default agent, sent just now"]
           and ev("() => document.querySelector('.pv-t3-sec .lbl').textContent") == 'T3 thread', ev("() => [...document.querySelectorAll('.pv-t3-sec .t3-thread')].map(e => e.textContent)"))
        pg.screenshot(path=str(SHOTS / '550-t3-thread-panel.png'))
        ev("() => { window.__opened.length = 0; }")
        pg.click('.pv-t3-sec .t3-thread'); pg.wait_for_timeout(100)
        ok('a click on it opens the thread in T3', ev("() => window.__opened.slice()") == ['t3code://threads/env-1234/' + first.replace(':', '%3A')], ev("() => window.__opened.slice()"))
        ev("() => { window.__opened.length = 0; }")
        pg.click(f'li.task[data-id="{tid}"] .t3-open'); pg.wait_for_timeout(100)
        ok('and so does the row\'s mark, without opening or dragging the task', ev("() => window.__opened.slice()") == ['t3code://threads/env-1234/' + first.replace(':', '%3A')])

        # ---------- Build it goes on in the task's thread ----------
        open_task_panel()
        ok('with a thread, the T3 tile says its thread, and its tooltip where it lands', tile()['note'] == 'its thread' and tile()['title'].startswith("Into this task's T3 thread, " + task + " (T3's default agent, sent just now)"), tile())
        line = ev("() => { const l = document.querySelector('.oc-thread'); return l ? l.textContent : ''; }")
        ok('a thread line names it and where it lands, with the more button, and no agent line', line == 'T3 thread: ' + task + "T3's default agent, sent just now"
           and ev("() => !!document.querySelector('#ocThreadMore')") and not ev("() => !!document.querySelector('#ocAgentPick')"), line)
        pg.screenshot(path=str(SHOTS / '551-t3-continue.png'))
        ev("() => { window.__opened.length = 0; }")
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = sends()[0]
        ok('the send names the task\'s thread, and no agent', s['thread'] == first and 'provider' not in s, s)
        ok('it says it is sending to its thread', said() == 'Sending ' + task + ' to its T3 thread.', said())
        r = run_link()
        ok('the helper sends it into that thread', calls()[-1]['args'][:3] == ['thread', 'send', first], calls()[-1]['args'])
        ok('the city says it went to its thread, with Open', said().startswith('Sent to its T3 thread: ' + task + '.') and ev("() => [...document.querySelectorAll('#toast .toast-act')].map(b => b.textContent)") == ['Open'], said())
        th = threads()
        ok('the task still has one thread, brought up to date', len(th) == 1 and th[0]['id'] == first and th[0]['last'] > th[0]['at'] - 1, th)
        # Think goes on in it too
        open_task_panel()
        pg.click('#ocTabThink'); pg.wait_for_timeout(100)
        ok('on Think the tile goes on in the thread too, asking for a round', tile()['note'] == 'its thread' and 'asking for a wizard round on this task, sent at once' in tile()['title'], tile())
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = sends()[0]
        ok('a Think send names the thread too', s['thread'] == first and s['title'] == 'Think: ' + task, s)
        run_link(); quiet()

        # ---------- New thread, behind the more button ----------
        open_task_panel()
        pg.click('#ocThreadMore'); pg.wait_for_timeout(100)
        menu = ev("() => [...document.querySelectorAll('.oc-thread-menu .oc-folder-opt')].map(e => e.querySelector('.oc-folder-name').textContent)")
        ok('the more button offers New thread, the focus on it', menu == ['New thread'] and ev("() => document.activeElement.id") == 'ocThreadSwap', menu)
        pg.screenshot(path=str(SHOTS / '552-t3-new-thread.png'))
        pg.click('#ocThreadSwap'); pg.wait_for_timeout(100)
        ok('picked, the tile starts a new thread on the agent picked, the agent line back', tile()['note'] == 'default' and 'A new T3 thread in' in tile()['title']
           and ev("() => !!document.querySelector('#ocAgentPick')") and ev("() => document.querySelector('.oc-thread').textContent") == 'T3 thread: a new one', tile())
        pg.click('#ocThreadMore'); pg.wait_for_timeout(100)
        ok('and the more button can go back to its thread', ev("() => document.querySelector('#ocThreadSwap .oc-folder-name').textContent") == 'Continue its thread')
        pg.click('#ocThreadSwap'); pg.wait_for_timeout(100)
        ok('which it does', tile()['note'] == 'its thread')
        pg.click('#ocThreadMore'); pg.click('#ocThreadSwap'); pg.wait_for_timeout(100)
        pg.click('#ocAgentPick'); pg.click('.oc-agents [data-agent="claude-sonnet-5-5"]'); pg.wait_for_timeout(100)
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = sends()[0]
        ok('a new thread names no thread, and its agent', 'thread' not in s and s['model'] == 'claude-sonnet-5-5', s)
        run_link()
        th = threads()
        ok('the task keeps both threads, the new one on Sonnet', len(th) == 2 and th[1]['agent'] == 'Sonnet 5.5' and th[1]['id'] != first, th)
        ok('the panel lists both, newest first', ev("() => [...document.querySelectorAll('.pv-t3-sec .t3-thread')].map(e => e.querySelector('.t3-thread-where').textContent)")
           == ['Sonnet 5.5, sent just now', "T3's default agent, sent just now"] and ev("() => document.querySelector('.pv-t3-sec .lbl').textContent") == 'T3 threads')
        ok('and the next send goes on in the newest', (open_task_panel() or True) and tile()['note'] == 'its thread' and 'Sonnet 5.5' in ev("() => document.querySelector('.oc-thread').textContent"))
        ev("() => OpenInClaude.close()"); quiet()

        # ---------- where it lands: the thread's state, from the task's Claude session ----------
        ev(f"""() => {{ window.__realSessions = ClaudeWork.sessionsOf; window.__realVoice = ClaudeWork.voice;
            const s = {{ session: 's-55', state: 'waiting', at: Date.now(), since: Date.now(), task: {json.dumps(task)}, project: 'Garden planner', ask: '', reply: '' }};
            ClaudeWork.sessionsOf = p => p.id === '{gp}' ? [s] : window.__realSessions(p);
            ClaudeWork.voice = p => p.id === '{gp}' ? [{{ s, moment: 'waiting', v: {{ task: s.task, ago: 'just now' }}, text: '', reply: '', tick: null }}] : window.__realVoice(p); }}""")
        ev("() => FullView.refreshRounds()"); pg.wait_for_timeout(100)
        row = ev(f"() => {{ const b = document.querySelector('li.task[data-id=\"{tid}\"] .t3-open'); return b ? {{ title: b.title, cls: b.className }} : null; }}")
        ok('with its session waiting, the row\'s mark says waiting on you, in its color', row['title'] == 'Opens its T3 thread, ' + task + ': Sonnet 5.5, waiting on you.' and 'waiting' in row['cls'], row)
        ok('and the panel\'s newest thread says so; the older one keeps when it was sent', ev("() => [...document.querySelectorAll('.pv-t3-sec .t3-thread-where')].map(e => e.textContent)")
           == ['Sonnet 5.5, waiting on you', "T3's default agent, sent just now"])
        # the leader's news: Open in T3 on Claude's line
        ev("() => FullView.close()"); pg.wait_for_timeout(300)
        ev(f"() => Bubble.open('{gp}')"); pg.wait_for_timeout(300)
        b3 = ev("() => { const b = document.querySelector('.ld-line .ld-t3'); return b ? { text: b.textContent, title: b.title } : null; }")
        ok('on the status card, Claude\'s waiting line has Open in T3, saying where it lands', b3 and b3['text'] == 'Open in T3' and b3['title'] == 'Opens its T3 thread, ' + task + ': Sonnet 5.5, waiting on you.', b3)
        pg.screenshot(path=str(SHOTS / '553-t3-card.png'))
        ev("() => { window.__opened.length = 0; }")
        pg.click('.ld-line .ld-t3'); pg.wait_for_timeout(100)
        ok('which opens the newest thread in T3', ev("() => window.__opened.slice()") == ['t3code://threads/env-1234/' + th[1]['id'].replace(':', '%3A')], ev("() => window.__opened.slice()"))
        ev("() => Bubble.close()")
        ev("() => { ClaudeWork.sessionsOf = window.__realSessions; ClaudeWork.voice = window.__realVoice; }")

        # ---------- a helper from before 0.1.90 starts a new thread: said ----------
        open_task_panel()
        ev("() => { window.__opened.length = 0; }")
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = sends()[0]
        ev("(s) => { window.__sub.delete('t3/send-' + s.id + '.json'); window.__sub.set('t3/' + s.id + '.done.json', { text: JSON.stringify({ app: 'nullovation-city', kind: 't3-sent', version: 1, id: s.id, ok: true, thread: 'cli:old-helper', project: 'proj-1', env: 'env-1234' }), t: Date.now() }); }", s)
        pg.wait_for_timeout(1400)
        ok('an old helper that started a new thread instead: the city says to run the setup again', 'run the T3 setup again' in said() and said().startswith('Sent to T3: '), said())
        ok('and keeps that thread too', [x['id'] for x in threads()][-1] == 'cli:old-helper')
        quiet()

        # ---------- Esc in the task panel leaves a thread kept while it was open ----------
        ok('the task panel is open, the focus on Claude', ev("() => document.activeElement.id") == 'pvTaskClaude', ev("() => document.activeElement.id"))
        ev(f"() => {{ const t = {T}; t.threads.push({{ id: 'cli:while-open', env: 'env-1234', agent: 'default', kind: 'build', title: 'x', at: Date.now(), last: Date.now() + 5 }}); }}")
        pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
        ok('Esc in the task panel keeps a thread that came while it was open', 'cli:while-open' in [x['id'] for x in threads()])

        # ---------- read back: kept, and made safe ----------
        ev(f"""() => {{ const t = {T}; t.threads.push({{ id: 'bad id &', env: 'e' }}, {{ id: 'cli:dup', env: 'env-1234', kind: 'nope', at: 5 }}, {{ id: 'cli:dup', env: 'x' }}, null); window.changed(getProject('{gp}')); }}""")
        got = ev(f"() => readThreads({T}).threads")
        ok('reading a task keeps good threads only: no bad id, no repeat, an unknown kind read as Build it', [x['id'] for x in got].count('cli:dup') == 1 and not any(x['id'] == 'bad id &' for x in got)
           and next(x for x in got if x['id'] == 'cli:dup')['kind'] == 'build', got)
        ok('at most 12 a task, the latest kept', len(ev("() => readThreads({ threads: Array.from({ length: 20 }, (_, i) => ({ id: 'cli:t' + i, env: 'e', at: i, last: i })) }).threads")) == 12
           and ev("() => readThreads({ threads: Array.from({ length: 20 }, (_, i) => ({ id: 'cli:t' + i, env: 'e', at: i, last: i })) }).threads[0].id") == 'cli:t8')
        pg.wait_for_timeout(1500)
        pg.reload(); pg.wait_for_timeout(2000)
        kept = ev(f"() => ({T}).threads.map(x => x.id)")
        ok('the city keeps a task\'s threads across a reload', first in kept and 'cli:old-helper' in kept and 'bad id &' not in kept, kept)
        b.close()
finally:
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
