"""Pass 53: T3 Code (0.1.87, T3 Connection, Round 1). Open in Claude's T3 tile starts a T3 Code thread in the
building's folder with the task already sent: the city writes the send into the Claude folder as t3/send-<id>.json and
follows a nullovation-t3: link naming only that file; the helper the T3 setup adds runs T3's own t3 thread start and
writes the answer back as t3/<id>.done.json, which the city reads and says, with Open. First the helper alone, run as
Windows would run it, in a home folder made for the test, against a fake t3 command that records what it is given, so
nothing is ever sent to a real T3; then the city with a Claude folder held in memory, the helper run on what the city
wrote and its answer put back, as the folder on disk would carry it."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

SETUP = ROOT / 'src' / 'setup' / 'nullovation-t3-links.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-t3-'))
home, local, claude = work / 'home', work / 'local', work / 'Claude-Hooks'
t3home = home / '.t3'
garden = work / 'Garden planner'                       # the building's folder, on disk
for d in (home / '.claude', local, claude, t3home / 'bin', t3home / 'userdata', garden, work / 'Not in T3'):
    d.mkdir(parents=True, exist_ok=True)
(t3home / 'userdata' / 'environment-id').write_text('env-1234\n', encoding='utf-8')
(home / '.claude' / 'nullovation-city.json').write_text(json.dumps({'app': 'nullovation-city', 'kind': 'claude-folder', 'folder': str(claude)}), encoding='utf-8')

# the fake t3: records every call, with what came on its input, and answers as T3 would
FAKE_T3 = work / 'fake_t3.py'
LOG, STATE = work / 't3-calls.json', work / 't3-state.json'
FAKE_T3.write_text(r'''import json, os, sys
log, state = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
data = sys.stdin.buffer.read().decode('utf-8') if args[:2] == ['thread', 'start'] and '-' in args else ''
calls = json.load(open(log, encoding='utf-8')) if os.path.exists(log) else []
calls.append({'args': args, 'stdin': data, 'env': {k: os.environ.get(k, '') for k in ('ELECTRON_RUN_AS_NODE', 'T3CODE_HOME', 'T3CODE_DESKTOP_CLI_LAUNCHER')}})
json.dump(calls, open(log, 'w', encoding='utf-8'))
st = json.load(open(state, encoding='utf-8')) if os.path.exists(state) else {'down': False, 'projects': []}
if st['down']:
    sys.stderr.write('No running T3 Code server uses C:\\x\\.t3. Start T3 Code, then retry.\n'); sys.exit(1)
if args[:2] == ['project', 'add']:
    st['projects'].append(args[2]); json.dump(st, open(state, 'w', encoding='utf-8')); print('Added.'); sys.exit(0)
if args[:2] == ['thread', 'list']:
    sys.stderr.write("No T3 Code project matches '" + args[3] + "'. Pass a project id or a path inside a project.\n"); sys.exit(1)
if args[:2] == ['thread', 'start']:
    where = args[2]
    if 'Not in T3' in where and where not in st['projects']:
        sys.stderr.write("No T3 Code project matches '" + where + "'. Pass a project id or a path inside a project.\n"); sys.exit(1)
    print(json.dumps({'threadId': 'thread-' + str(len(calls)), 'projectId': 'proj-1', 'runId': 'run-1'})); sys.exit(0)
sys.exit(2)
''', encoding='utf-8')
# t3.cmd as T3 writes it: a program, its script and %*; the helper runs the two straight, never through cmd.exe
(t3home / 'bin' / 't3.cmd').write_text('@echo off\r\nrem Written by T3 Code: runs the desktop app\'s bundled t3 CLI.\r\nsetlocal EnableExtensions DisableDelayedExpansion\r\n'
    f'set "T3CODE_HOME={t3home}"\r\nset "ELECTRON_RUN_AS_NODE=1"\r\nset "T3CODE_DESKTOP_CLI_LAUNCHER=1"\r\n:run\r\n'
    f'"{sys.executable}" "{FAKE_T3}" %*\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')
# the fake t3 takes its log and state first: the helper passes T3's own arguments after the script, so a wrapper adds them
WRAP = work / 'wrap.py'
WRAP.write_text(f'import runpy, sys\nsys.argv = [{str(FAKE_T3)!r}, {str(LOG)!r}, {str(STATE)!r}] + sys.argv[1:]\nrunpy.run_path({str(FAKE_T3)!r}, run_name="__main__")\n', encoding='utf-8')
(t3home / 'bin' / 't3.cmd').write_text((t3home / 'bin' / 't3.cmd').read_text(encoding='utf-8').replace(str(FAKE_T3), str(WRAP)), encoding='utf-8')

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
    st = {'down': False, 'projects': []}; st.update(o); STATE.write_text(json.dumps(st), encoding='utf-8')
last = lambda: (local / 'Nullovation City' / 'last-t3.txt').read_text(encoding='utf-8') if (local / 'Nullovation City' / 'last-t3.txt').exists() else ''

try:
    # ---------- the setup ----------
    r = helper('--help')
    ok('--help shows how it works', r.returncode == 0 and b'nullovation-t3:send/<id>' in r.stdout and b'only the city writes that folder' in r.stdout)
    r = helper('--install', '--dry-run')
    out = r.stdout.decode('utf-8')
    ok('the install (dry run) would add the link type for this user only', r.returncode == 0 and 'HKEY_CURRENT_USER\\Software\\Classes\\nullovation-t3' in out, out)
    want = '"' + str(pathlib.Path(sys.executable).with_name('pythonw.exe')) + '" "' + str(local / 'Nullovation City' / 'nullovation-t3-links.py') + '" open "%1"'
    ok('its command runs the copy in LocalAppData with pythonw, so no window shows', want in out, out)
    ok('and says its sends go through the Claude folder\'s t3 folder', str(claude / 't3') in out)
    r = helper('--uninstall', '--dry-run')
    ok('the uninstall (dry run) names what it takes out', r.returncode == 0 and b'Would take out' in r.stdout)
    r = helper('--status')
    ok('--status names the Claude folder and T3\'s command', r.returncode == 0 and str(claude).encode() in r.stdout and str(sys.executable).encode() in r.stdout, r.stdout)
    # the Claude folder from the hooks, when the city's config file is not there (Abdurrahman's PC, November 2026)
    cfg = home / '.claude' / 'nullovation-city.json'
    cfg.rename(cfg.with_suffix('.off'))
    (home / '.claude' / 'settings.json').write_text(json.dumps({'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': sys.executable,
        'args': [str(home / '.claude' / 'hooks' / 'nullovation-city-status.py'), 'hook', 'done', str(claude)]}]}]}}), encoding='utf-8')
    r = helper('--status')
    ok('with no config file, the Claude folder is read from the Claude Code at work hooks', str(claude).encode() in r.stdout, r.stdout)
    (home / '.claude' / 'settings.json').unlink()
    r = helper('--install', '--no-pause', '--dry-run')
    ok('with neither, the install says the Claude Code at work setup runs first', r.returncode == 1 and b'Claude Code at work setup first' in r.stdout, r.stdout)
    cfg.with_suffix('.off').rename(cfg)

    # ---------- a send, run as Windows runs the link ----------
    state()
    put_send('abc12345', title='Beds & "paths" 100% ^done', provider='claudeAgent', model='claude-sonnet-5-5', message='# Task: Draw the beds\n\nThe beds, in عربي too.')
    r = helper('open', 'nullovation-t3:send/abc12345')
    a = answer('abc12345')
    ok('the link starts the thread and answers ok, with its thread, project and T3\'s environment', r.returncode == 0 and a and a['ok'] and a['thread'] == 'thread-1'
       and a['project'] == 'proj-1' and a['env'] == 'env-1234' and a['kind'] == 't3-sent', a)
    c = calls()[-1]
    ok('it runs t3 thread start in the building\'s folder, the copy on its input', c['args'][:4] == ['thread', 'start', str(garden), '-'] and c['args'][-1] == '--json', c['args'])
    ok('the title reaches T3 exactly, & " % ^ and all, since nothing goes through cmd.exe', c['args'][c['args'].index('--title') + 1] == 'Beds & "paths" 100% ^done', c['args'])
    ok('with the agent and the model picked', c['args'][c['args'].index('--provider') + 1] == 'claudeAgent' and c['args'][c['args'].index('--model') + 1] == 'claude-sonnet-5-5')
    ok('the task\'s copy arrives whole on its input, Arabic too', c['stdin'] == '# Task: Draw the beds\n\nThe beds, in عربي too.', c['stdin'])
    ok('in T3\'s own settings from t3.cmd', c['env'] == {'ELECTRON_RUN_AS_NODE': '1', 'T3CODE_HOME': str(t3home), 'T3CODE_DESKTOP_CLI_LAUNCHER': '1'}, c['env'])
    ok('the send is taken: gone from the folder, with nothing left running', not (claude / 't3' / 'send-abc12345.json').exists() and not (claude / 't3' / 'abc12345.running.json').exists())
    ok('the run is noted, without the task\'s copy', 'Sent abc12345' in last() and 'عربي' not in last())
    n = len(calls())
    r = helper('open', 'nullovation-t3:send/abc12345')
    ok('the same link a second time starts nothing', r.returncode == 1 and len(calls()) == n and 'sent already' in last())
    put_send('dflt0001', title='Water the beds')
    helper('open', 'nullovation-t3://send/dflt0001/')
    c = calls()[-1]
    ok('T3\'s default sends no agent, so T3 picks its own (a // and a / at the end read too)', answer('dflt0001')['ok'] and '--provider' not in c['args'] and '--model' not in c['args'], c['args'])

    # a folder no T3 project holds yet: added to T3 first
    put_send('noproj01', folder=str(work / 'Not in T3'))
    helper('open', 'nullovation-t3:send/noproj01')
    a, cs = answer('noproj01'), calls()[-3:]
    ok('a folder T3 has no project for is added to T3 as a project, then the thread starts', a['ok'] and a.get('added') is True
       and cs[0]['args'][:2] == ['thread', 'start'] and cs[1]['args'] == ['project', 'add', str(work / 'Not in T3')] and cs[2]['args'][:2] == ['thread', 'start'], [x['args'] for x in cs])
    # T3 not running
    state(down=True)
    put_send('down0001')
    r = helper('open', 'nullovation-t3:send/down0001')
    ok('with T3 not running, the answer says so in the city\'s words', r.returncode == 1 and answer('down0001') == {**answer('down0001'), 'ok': False, 'error': 'T3 Code is not running. Open it, then send again.'}, answer('down0001'))
    state()
    # what the helper refuses
    n = len(calls())
    put_send('old00001', at=int(time.time() * 1000) - 180000)
    helper('open', 'nullovation-t3:send/old00001')
    ok('a send older than two minutes is refused, and nothing runs', answer('old00001')['ok'] is False and 'too old' in answer('old00001')['error'] and len(calls()) == n)
    put_send('nofold01', folder=str(work / 'Gone'))
    helper('open', 'nullovation-t3:send/nofold01')
    ok('a folder that is not on this PC is refused', answer('nofold01')['ok'] is False and 'not found' in answer('nofold01')['error'])
    put_send('badagt01', provider='claudeAgent', model='')
    helper('open', 'nullovation-t3:send/badagt01')
    ok('an agent without its model is refused', answer('badagt01')['ok'] is False and 'agent' in answer('badagt01')['error'])
    put_send('other001', app='someone-else')
    helper('open', 'nullovation-t3:send/other001')
    ok('a file the city did not write is refused', answer('other001')['ok'] is False and 'not one Nullovation City wrote' in answer('other001')['error'])
    put_send('wrongid1', id='notthesame')
    helper('open', 'nullovation-t3:send/wrongid1')
    ok('a file naming another send is refused', answer('wrongid1')['ok'] is False)
    t0 = time.time()
    r = helper('open', 'nullovation-t3:send/nothing1')
    ok('a link naming no file waits a moment, then starts nothing', r.returncode == 1 and 4 < time.time() - t0 < 30 and len(calls()) == n and 'sent nothing' in last())
    for bad in ('nullovation-t3:send/../../x', 'nullovation-t3:send/a', 'nullovation-t3:run/abcdefgh', 'nullovation-t3:send/abcdefgh?prompt=rm'):
        r = helper('open', bad)
        if r.returncode != 1: break
    ok('a link that is not a send\'s name is refused, a prompt in it never read', r.returncode == 1 and len(calls()) == n and 'could not read' in last())
    # the test link
    r = helper('open', 'nullovation-t3:test/test0001')
    a = answer('test0001')
    ok('a test link answers that T3\'s command is there and T3 is running', r.returncode == 0 and a['ok'] and a['test'] and a['t3'] and a['running'], a)
    state(down=True)
    helper('open', 'nullovation-t3:test/test0002')
    ok('and when T3 is not running, says so', answer('test0002')['running'] is False and answer('test0002')['t3'] is True)
    state()
    (t3home / 'bin' / 't3.cmd').rename(t3home / 'bin' / 't3.off')
    put_send('not3cmd1')
    helper('open', 'nullovation-t3:send/not3cmd1')
    ok('with no t3 command on the PC, the answer says to open T3 once', 'Open T3 Code once' in answer('not3cmd1')['error'], answer('not3cmd1'))
    (t3home / 'bin' / 't3.off').rename(t3home / 'bin' / 't3.cmd')
    # an answer nobody read is cleared after a day
    old = claude / 't3' / 'stale001.done.json'
    old.write_text('{}', encoding='utf-8'); os.utime(old, (time.time() - 2 * 86400, time.time() - 2 * 86400))
    helper('open', 'nullovation-t3:test/test0003')
    ok('answers nobody read are cleared after a day', not old.exists())
    for f in (claude / 't3').iterdir():
        f.unlink()

    # ---------- the city ----------
    FAKE = """
window.__sub = new Map(); window.__ct = 1; window.__cwperm = 'granted';
const fail = n => { const e = new Error(n); e.name = n; throw e; };
const subfile = path => ({ kind: 'file', name: path.split('/').pop(),
  getFile: async () => { const f = window.__sub.get(path); if (!f) fail('NotFoundError'); return new File([f.text], path.split('/').pop(), { lastModified: f.t }); },
  createWritable: async () => { if (window.__cwperm !== 'granted') fail('NotAllowedError'); let buf = '';
    return { write: async d => { buf += d; }, close: async () => { window.__sub.set(path, { text: buf, t: Date.now() + (window.__ct++) }); } }; } });
const subdir = prefix => ({ kind: 'directory', name: prefix.split('/').pop(),
  getDirectoryHandle: async (n, o) => subdir(prefix + '/' + n),
  getFileHandle: async (n, o) => { const path = prefix + '/' + n; if (!window.__sub.has(path) && !(o && o.create)) fail('NotFoundError'); return subfile(path); },
  removeEntry: async n => { if (!window.__sub.has(prefix + '/' + n)) fail('NotFoundError'); window.__sub.delete(prefix + '/' + n); },
  entries: async function* () { } });
window.__cdir = { kind: 'directory', name: 'Claude-Hooks',
  queryPermission: async o => (o && o.mode === 'readwrite') ? window.__cwperm : 'granted', requestPermission: async () => 'granted',
  getDirectoryHandle: async (n, o) => subdir(n),
  entries: async function* () { yield ['README-nullovation-city.txt', { kind: 'file', name: 'README-nullovation-city.txt', getFile: async () => new File(['x'], 'README-nullovation-city.txt') }]; } };
window.showDirectoryPicker = async () => window.__cdir;
/* a link of the PC's is recorded rather than followed */
window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (/^(nullovation-t3|t3code|claude|claude-cli):/i.test(href)) { window.__opened.push(href); return; } return anchorClick.call(this); };
"""
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
        ctx.add_init_script(TEST_CITY)
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t53')) { sessionStorage.setItem('nc-t53', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        downloads = []
        pg.on('download', lambda d: downloads.append(d))
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        hall = ev("() => DB.projects.find(p => p.name !== 'Garden planner').id")
        ev(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: 'l-t3', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }}); window.changed(p); }}""")
        task = ev(f"() => getProject('{gp}').todos.find(t => !t.done).text")
        tid = ev(f"() => getProject('{gp}').todos.find(t => !t.done).id")
        quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true); }")
        said = lambda: ev("() => { const t = document.querySelector('#toast'); return t.classList.contains('show') ? t.textContent : ''; }")
        tiles = lambda: ev("() => [...document.querySelectorAll('.oc-panel .oc-tiles .oc-tile')].map(e => ({ kind: e.dataset.kind, off: e.classList.contains('off'), note: (e.querySelector('.oc-tile-note') || {}).textContent || '', title: e.getAttribute('title') || '' }))")
        def open_task_panel():
            ev("() => OpenInClaude.close()")
            ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
            pg.click(f'li.task[data-id="{tid}"] .task-title'); pg.wait_for_timeout(300); quiet()
            pg.locator('#pvTaskClaude').scroll_into_view_if_needed(); pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
        def sync_out():
            """What the city wrote in the Claude folder's t3 folder, onto the disk, where the helper reads it."""
            (claude / 't3').mkdir(exist_ok=True)
            files = ev("() => [...window.__sub].filter(([k]) => k.startsWith('t3/')).map(([k, f]) => [k, f.text])")
            for f in (claude / 't3').iterdir():
                if ('t3/' + f.name) not in dict(files): f.unlink()          # what the city read and cleared
            for path, text in files:
                (claude / path).write_text(text, encoding='utf-8')
        def sync_in():
            """And back: the helper's answers in, a send it took gone, as the folder on disk would show them."""
            on_disk = {('t3/' + f.name): f.read_text(encoding='utf-8') for f in (claude / 't3').iterdir() if f.suffix == '.json'}
            ev("""(files) => { for (const k of [...window.__sub.keys()]) if (k.startsWith('t3/') && !(k in files)) window.__sub.delete(k);
              for (const [k, text] of Object.entries(files)) window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }""", on_disk)
        def run_link():
            href = ev("() => window.__opened[window.__opened.length - 1]")
            sync_out()
            r = helper('open', href)
            sync_in()
            return href, r

        # with no Claude folder: the tile first, greyed out, saying why
        open_task_panel()
        ts = tiles()
        ok('the T3 tile comes first, then Chat, Cowork, Code, Terminal and Copy', [t['kind'] for t in ts] == ['t3', 'chat', 'cowork', 'code', 'terminal', 'copy'], ts)
        ok('the panel is wider for six tiles, and every tile\'s words fit', ev("() => document.querySelector('.oc-panel').offsetWidth") == 404
           and ev("() => [...document.querySelectorAll('.oc-panel .oc-tile')].every(e => e.scrollWidth <= e.clientWidth + 1)"))
        ok('with no Claude folder, the T3 tile is greyed out, saying sends go through it', ts[0]['off'] and 'Claude folder' in ts[0]['title'], ts[0])
        ok('and no agent line shows', ev("() => !document.querySelector('#ocAgentPick')"))
        ok('the T3 tile draws its icon', ev("() => !!document.querySelector('.oc-panel .oc-tile[data-kind=\"t3\"] .ic svg rect')"))
        # connect the Claude folder
        ev("() => OpenInClaude.close()")
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ev("() => Settings.close()")
        open_task_panel()
        ts = tiles()
        ok('with the Claude folder, the T3 tile is on, naming its agent: T3\'s default', not ts[0]['off'] and ts[0]['note'] == 'default' and str(garden) in ts[0]['title'], ts[0])
        ok('the focus starts on Build it, as before, and the first tile it reaches is T3', ev("() => document.activeElement.id") == 'ocTabBuild'
           and ev("() => document.querySelector('.oc-panel .oc-tile:not(.off)').dataset.kind") == 't3')
        ok('the agent line names T3\'s default', ev("() => document.querySelector('#ocAgentPick').textContent").startswith("T3 agent: T3's default"))
        pg.click('#ocAgentPick'); pg.wait_for_timeout(150)
        opts = ev("() => [...document.querySelectorAll('.oc-agents .oc-folder-opt')].map(e => [e.dataset.agent, e.querySelector('.oc-folder-name').textContent, e.getAttribute('aria-selected')])")
        ok('the pick offers T3\'s default and Claude\'s three models, the one in use picked', opts == [['default', "T3's default", 'true'], ['claude-opus-5-5', 'Claude Opus 5.5', 'false'],
           ['claude-sonnet-5-5', 'Claude Sonnet 5.5', 'false'], ['claude-haiku-5-5', 'Claude Haiku 5.5', 'false']], opts)
        pg.screenshot(path=str(SHOTS / '531-t3-agents.png'))
        pg.click('.oc-agents [data-agent="claude-sonnet-5-5"]'); pg.wait_for_timeout(150)
        ok('picking Sonnet names it on the tile and the line, the focus back on the line', tiles()[0]['note'] == 'Sonnet 5.5' and 'Claude Sonnet 5.5' in ev("() => document.querySelector('#ocAgentPick').textContent")
           and ev("() => document.activeElement.id") == 'ocAgentPick')
        ok('the building keeps its pick, in this browser', ev("() => JSON.parse(localStorage.getItem('nullovation-city:t3Agent'))") == {gp: 'claude-sonnet-5-5'})
        ev("() => OpenInClaude.close()"); open_task_panel()
        ok('opened again, the panel is still on Sonnet', tiles()[0]['note'] == 'Sonnet 5.5')
        pg.screenshot(path=str(SHOTS / '530-t3-panel.png'))
        # send it
        ev("() => { window.__opened.length = 0; }")
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        sends = ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => [k, JSON.parse(f.text)])")
        ok('a click writes one send into the Claude folder\'s t3 folder', len(sends) == 1, sends)
        k, s = sends[0]
        ident = s['id']
        ok('the send holds the building\'s folder, the task\'s title, its copy, the agent and the model', k == 't3/send-' + ident + '.json' and s['app'] == 'nullovation-city' and s['kind'] == 't3-send'
           and s['folder'] == str(garden) and s['title'] == task and s['message'].startswith('# Task: ' + task) and s['provider'] == 'claudeAgent' and s['model'] == 'claude-sonnet-5-5' and s['project'] == 'Garden planner', s)
        ok('the link it follows names only that file', ev("() => window.__opened.slice()") == ['nullovation-t3:send/' + ident])
        ok('the panel closes, the focus back on its button, and it says it is sending', not ev("() => OpenInClaude.isOpen()") and ev("() => document.activeElement.id") == 'pvTaskClaude'
           and said() == 'Sending ' + task + ' to T3, on Claude Sonnet 5.5.', said())
        ok('the copy asks for an update when it is done, as every copy does', 'send Nullovation City an update' in s['message'])
        href, r = run_link()
        ok('the helper, run on that link, starts the thread', r.returncode == 0 and calls()[-1]['args'][2] == str(garden) and calls()[-1]['stdin'] == s['message'])
        pg.wait_for_timeout(1400)
        msg = said()
        ok('within a second the city says it was sent, with Open', msg.startswith('Sent to T3: ' + task + '.') and ev("() => [...document.querySelectorAll('#toast .toast-act')].map(b => b.textContent)") == ['Open'], msg)
        ok('and clears the answer it read', not ev("() => [...window.__sub.keys()].some(k => k.startsWith('t3/'))"))
        pg.screenshot(path=str(SHOTS / '532-t3-sent.png'))
        ev("() => { window.__opened.length = 0; }")
        pg.click('#toast .toast-act'); pg.wait_for_timeout(150)
        ok('Open shows the thread in T3 through its own t3code://threads link', ev("() => window.__opened.slice()") == ['t3code://threads/env-1234/thread-' + str(len(calls()))], ev("() => window.__opened.slice()"))
        # the building's leader says it
        ev(f"""() => {{ const l = blankLeader({{ name: 'Fern Rowe', role: 'Head Gardener' }}); DB.leaders.push(l); setLeader(getProject('{gp}'), l.id); window.changed(getProject('{gp}')); }}""")
        open_task_panel(); ev("() => { window.__opened.length = 0; }")
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        run_link(); pg.wait_for_timeout(1400)
        ok('a building with a leader has its leader say it, face and all', ev("() => !!document.querySelector('#toast.show.has-lead')") and 'Fern Rowe' in said() and 'Sent to T3: ' + task in said(), said())
        # Think: the round's copy, and its title
        open_task_panel(); ev("() => { window.__opened.length = 0; }")
        pg.click('#ocTabThink'); pg.wait_for_timeout(100)
        ok('on Think the T3 tile asks for a wizard round, sent at once', 'asking for a wizard round on this task, sent at once' in tiles()[0]['title'], tiles()[0]['title'])
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))[0]")
        ok('a Think send is titled Think: and carries the copy asking for a round', s['title'] == 'Think: ' + task and 'decision wizard round' in s['message'], s['title'])
        run_link(); pg.wait_for_timeout(1400); quiet()
        open_task_panel(); ev("() => { window.__opened.length = 0; }")
        pg.click('#ocTabThink'); pg.click('#ocBrainstorm'); pg.wait_for_timeout(100)
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))[0]")
        ok('and a brainstorm, Brainstorm:', s['title'] == 'Brainstorm: ' + task and 'brainstorm' in s['message'], s['title'])
        run_link(); pg.wait_for_timeout(1400); quiet()
        # T3 not running: the helper's words, as an error
        state(down=True)
        open_task_panel(); pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        run_link(); pg.wait_for_timeout(1400)
        ok('with T3 not running, the city says so as an error', said() == 'T3 Code is not running. Open it, then send again.' and ev("() => document.querySelector('#toast').classList.contains('error')"), said())
        state(); quiet()
        # a send nobody takes: the setup has not run
        ev("() => T3._test.times(1500, 4000)")
        open_task_panel(); pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(3200)
        ok('a send nobody takes is cleared, saying the setup may not have run', said().startswith('T3 did not pick up ' + task + '. Has the T3 setup run on this PC?')
           and not ev("() => [...window.__sub.keys()].some(k => k.startsWith('t3/'))"), said())
        # taken, but no word from T3
        open_task_panel(); pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(200)
        ev("() => { for (const k of [...window.__sub.keys()]) if (k.startsWith('t3/send-')) window.__sub.delete(k); }")
        pg.wait_for_timeout(5200)
        ok('a send taken with no answer after a while says to look in T3', said() == 'No word from T3 on ' + task + ' yet. Look in T3 Code.', said())
        ev("() => T3._test.times(15000, 180000)"); quiet()
        # the default agent sends none
        open_task_panel(); pg.click('#ocAgentPick'); pg.click('.oc-agents [data-agent="default"]'); pg.wait_for_timeout(100)
        ok('picking T3\'s default back forgets the pick', ev("() => JSON.parse(localStorage.getItem('nullovation-city:t3Agent'))") == {})
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        s = ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))[0]")
        ok('a send on T3\'s default names no agent or model', 'provider' not in s and 'model' not in s and said() == 'Sending ' + task + ' to T3.', s)
        run_link(); pg.wait_for_timeout(1400); quiet()
        # a building with no folder link (B1)
        ev("() => OpenInClaude.close()")
        ev(f"() => FullView.open('{hall}')"); pg.wait_for_timeout(400)
        hall_folder = ev(f"() => OpenInClaude.places(getProject('{hall}')).folders.length")
        pg.click('#pvStatusClaude'); pg.wait_for_timeout(200)
        ts = tiles()
        ok('a building with no folder link greys the T3 tile out, saying it needs one', hall_folder == 0 and ts[0]['kind'] == 't3' and ts[0]['off'] and "building's folder" in ts[0]['title'], ts[0])
        ok('its folder line names T3 with Code and Terminal', ev("() => document.querySelector('.oc-panel .oc-folder').textContent") == 'No folder link: T3, Code and Terminal need one.')
        ok('and no agent line', ev("() => !document.querySelector('#ocAgentPick')"))
        ev("() => { OpenInClaude.close(); FullView.close(); }"); pg.wait_for_timeout(200)
        # the status brief: no project, so no folder
        pg.click('#btnBriefClaude'); pg.wait_for_timeout(200)
        kinds = ev("() => [...document.querySelectorAll('.oc-panel .oc-tile')].map(e => e.dataset.kind + (e.classList.contains('off') ? ':off' : ''))")
        ok('the status brief keeps Copy first, then T3 greyed out and the four Claude tiles', kinds == ['copy', 't3:off', 'chat', 'cowork', 'code:off', 'terminal:off'], kinds)
        ev("() => OpenInClaude.close()")

        # ---------- Settings, Links: which tiles show ----------
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        sec = ev("() => { const h = [...document.querySelectorAll('#setBody .set-h')].find(e => e.textContent === 'T3 Code'); return h ? h.closest('.set-group').textContent : ''; }")
        ok('Settings, Links has a T3 Code section', 'starts a T3 Code thread' in sec and 'Get the setup' in sec and 'Test T3 link' in sec)
        ok('its pick: T3 and Claude, T3 only, Claude only, the first pressed, with no dot', ev("() => [...document.querySelectorAll('#optTiles button')].map(b => b.textContent + ':' + b.getAttribute('aria-pressed'))")
           == ['T3 and Claude:true', 'T3 only:false', 'Claude only:false'] and not ev("() => document.querySelector('[data-set=\"tiles\"]').classList.contains('changed')"))
        ev("() => document.querySelector('#optTiles').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(100)
        pg.screenshot(path=str(SHOTS / '533-t3-settings.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})
        pg.click('#optTiles [data-value="t3"]'); pg.wait_for_timeout(100)
        ok('T3 only: a dot, on the tab too, and its note', ev("() => document.querySelector('[data-set=\"tiles\"]').classList.contains('changed') && document.querySelector('.set-tab[data-tab=\"links\"]').classList.contains('changed')")
           and 'Claude app\'s tiles are off' in ev("() => document.querySelector('#tilesNote').textContent"))
        ok('kept in this browser', ev("() => localStorage.getItem('nullovation-city:openTiles')") == 't3')
        ev("() => Settings.close()"); open_task_panel()
        ok('with T3 only, the panel holds the T3 tile and Copy (his note: when Claude is off, only Copy stays)', [t['kind'] for t in tiles()] == ['t3', 'copy'], tiles())
        ok('and its panel is the usual width', ev("() => document.querySelector('.oc-panel').offsetWidth") == 344)
        ev("() => { OpenInClaude.close(); FullView.close(); }"); pg.wait_for_timeout(200)
        pg.click('#btnBriefClaude'); pg.wait_for_timeout(200)
        ok('the status brief on T3 only: Copy first, then T3', ev("() => [...document.querySelectorAll('.oc-panel .oc-tile')].map(e => e.dataset.kind)") == ['copy', 't3'])
        ev("() => OpenInClaude.close()")
        ev("() => Settings.open('links')"); pg.click('#optTiles [data-value="claude"]'); ev("() => Settings.close()")
        open_task_panel()
        ok('with Claude only, the panel is as before T3: Chat, Cowork, Code, Terminal and Copy', [t['kind'] for t in tiles()] == ['chat', 'cowork', 'code', 'terminal', 'copy'] and not ev("() => !!document.querySelector('#ocAgentPick')"))
        ev("() => { OpenInClaude.close(); FullView.close(); }")
        ev("() => Settings.open('links')"); pg.click('#btnTabReset'); pg.wait_for_timeout(100)
        ok('Reset to defaults brings both back', ev("() => localStorage.getItem('nullovation-city:openTiles')") is None and ev("() => document.querySelector('#optTiles [data-value=\"both\"]').getAttribute('aria-pressed')") == 'true')
        # Get the setup and Test T3 link
        with pg.expect_download() as dl:
            pg.click('#btnT3Setup')
        d = dl.value
        got = pathlib.Path(d.path()).read_bytes()
        ok('Get the setup saves nullovation-t3-links.py, the same file as the source', d.suggested_filename == 'nullovation-t3-links.py' and got == SETUP.read_bytes())
        ok('and says to double-click it', 'Double-click it' in said())
        ev("() => { window.__opened.length = 0; }")
        pg.click('#btnT3Test'); pg.wait_for_timeout(200)
        href = ev("() => window.__opened[0]")
        ok('Test T3 link follows a test link', href and href.startswith('nullovation-t3:test/') and said() == 'Asking the T3 helper to answer.', href)
        run_link(); pg.wait_for_timeout(1400)
        ok('the helper\'s answer says T3 links work and T3 is running', said() == 'T3 links work, and T3 Code is running.', said())
        ev("() => Settings.close()")
        # no Claude folder: Test says what comes first
        ev("() => { window.__cwperm = 'denied'; }")
        ev("() => ClaudeWork.init()"); pg.wait_for_timeout(300)
        ev("() => Settings.open('links')"); pg.click('#btnT3Test'); pg.wait_for_timeout(100)
        ok('with the city not let to write in the Claude folder, Test says to connect it first', said().startswith('Connect the Claude folder first'), said())
        ev("() => Settings.close()")

        # ---------- nothing new in the city ----------
        db = ev("() => localStorage.getItem('nullovation-city:v1')")
        ok('nothing about T3 is saved in the city', not any(w in db for w in ('t3-send', 'nullovation-t3', 'claude-sonnet', 't3Agent', 'openTiles')))
        b.close()
finally:
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
