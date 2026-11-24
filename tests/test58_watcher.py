"""Pass 58: the T3 watcher (0.1.93, T3 Connection Research, Round 2, W2). A small program the T3 setup starts at
sign-in reads Claude's T3 threads through T3's agent tools while T3 is open and writes them into the Claude folder as
t3/watch.json; the city reads it: each of a task's threads its own state, its latest message, and Open in T3 on the
lines of a session in T3. First the watcher, run as the setup runs it, against a fake T3 server that answers as T3
v0.1.11's agent tools do, and a fake t3 command for its key; then the city with a Claude folder held in memory."""
import http.server, json, os, pathlib, shutil, subprocess, sys, tempfile, threading, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

SETUP = ROOT / 'src' / 'setup' / 'nullovation-t3-links.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-watch-'))
home, local, claude = work / 'home', work / 'local', work / 'Claude-Hooks'
t3home = home / '.t3'
garden, other = work / 'Garden planner', work / 'Other'
for d in (home / '.claude', local, claude, t3home / 'bin', t3home / 'userdata', garden, other):
    d.mkdir(parents=True, exist_ok=True)
(t3home / 'userdata' / 'environment-id').write_text('env-1234\n', encoding='utf-8')
(home / '.claude' / 'nullovation-city.json').write_text(json.dumps({'app': 'nullovation-city', 'kind': 'claude-folder', 'folder': str(claude)}), encoding='utf-8')
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(local), NULLOVATION_QUIET='1', PYTHONUTF8='1')
env.pop('T3CODE_HOME', None)

# ---------- the fake t3 command: its key, issued and revoked ----------
LOG = work / 't3-auth.json'
FAKE_T3 = work / 'fake_t3.py'
FAKE_T3.write_text(r'''import json, os, sys
log = sys.argv[1]; args = sys.argv[2:]
calls = json.load(open(log)) if os.path.exists(log) else []
calls.append(args); json.dump(calls, open(log, 'w'))
if args[:3] == ['auth', 'session', 'issue']:
    n = len([c for c in calls if c[:3] == ['auth', 'session', 'issue']])
    print(json.dumps({'sessionId': 'sess-%d' % n, 'token': 'tok-%d' % n, 'method': 'bearer-access-token', 'scopes': ['orchestration:read'],
                      'subject': 'mcp-client', 'expiresAt': '2099-01-01T00:00:00.000Z'}, indent=2)); sys.exit(0)
if args[:3] == ['auth', 'session', 'revoke']:
    print('Revoked.'); sys.exit(0)
sys.exit(2)
''', encoding='utf-8')
WRAP = work / 'wrap.py'
WRAP.write_text(f'import runpy, sys\nsys.argv = [{str(FAKE_T3)!r}, {str(LOG)!r}] + sys.argv[1:]\nrunpy.run_path({str(FAKE_T3)!r}, run_name="__main__")\n', encoding='utf-8')
(t3home / 'bin' / 't3.cmd').write_text('@echo off\r\n' f'set "T3CODE_HOME={t3home}"\r\n' f'"{sys.executable}" "{WRAP}" %*\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')
auth = lambda: json.loads(LOG.read_text()) if LOG.exists() else []

# ---------- the fake T3 server: its agent tools at /mcp ----------
now_iso = lambda ago=0: time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() - ago))
srv = {'tokens': {'tok-1'}, 'calls': [], 'origins': 0, 'fail': None,
       'threads': [
           {'threadId': 'cli:run', 'title': 'Draw the beds on a grid', 'status': 'running', 'providerInstanceId': 'claudeAgent', 'model': 'claude-opus-5-5', 'projectId': 'p-g',
            'updatedAt': now_iso(5), 'createdAt': now_iso(600), 'itemCount': 7, 'pendingBackgroundTasks': [{'id': 'b1'}]},
           {'threadId': 'cli:ask', 'title': 'Pick the soil', 'status': 'waiting', 'providerInstanceId': 'claudeAgent', 'model': 'claude-opus-5-5', 'projectId': 'p-g',
            'updatedAt': now_iso(30), 'createdAt': now_iso(900), 'itemCount': 3, 'pendingBackgroundTasks': []},
           {'threadId': 'cli:ok', 'title': 'Run the tests', 'status': 'waiting', 'providerInstanceId': 'claudeAgent', 'model': 'claude-sonnet-5-5', 'projectId': 'p-o',
            'updatedAt': now_iso(60), 'createdAt': now_iso(1200), 'itemCount': 2, 'pendingBackgroundTasks': []},
           {'threadId': 'cli:codex', 'title': 'Not Claude', 'status': 'running', 'providerInstanceId': 'codex', 'model': 'gpt', 'projectId': 'p-g',
            'updatedAt': now_iso(1), 'createdAt': now_iso(100), 'itemCount': 2, 'pendingBackgroundTasks': []},
           {'threadId': 'cli:old', 'title': 'Long done', 'status': 'completed', 'providerInstanceId': 'claudeAgent', 'model': 'claude-opus-5-5', 'projectId': 'p-g',
            'updatedAt': now_iso(3 * 86400), 'createdAt': now_iso(4 * 86400), 'itemCount': 9, 'pendingBackgroundTasks': []},
       ]}
MSGS = {'cli:run': [('user_message', '# Task: Draw the beds on a grid'), ('assistant_message', 'Reading the grid.'), ('assistant_message', 'The beds are **drawn**, 4 by 6.')],
        'cli:ask': [('user_message', 'Pick the soil'), ('assistant_message', 'Two soils fit; asking which.')],
        'cli:ok': [('user_message', 'Run the tests'), ('assistant_message', 'Running the full suite needs your OK.')]}

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, code, body=None, sse=False, headers=None):
        self.send_response(code)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        data = b''
        if body is not None:
            text = json.dumps(body)
            data = (('event: message\ndata: ' + text + '\n\n') if sse else text).encode()
            self.send_header('Content-Type', 'text/event-stream' if sse else 'application/json')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        if self.headers.get('Origin') is not None: srv['origins'] += 1; return self.reply(403)
        tok = (self.headers.get('Authorization') or '').replace('Bearer ', '')
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)))
        if tok not in srv['tokens']: return self.reply(401, {'error': 'invalid_mcp_credential'})
        m, rid = body.get('method'), body.get('id')
        if m == 'initialize': return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'protocolVersion': '2025-06-18', 'serverInfo': {'name': 'T3 Code', 'version': '0.1.11'}}}, sse=True, headers={'Mcp-Session-Id': 'mcp-1'})
        if rid is None: return self.reply(202)
        if self.headers.get('Mcp-Session-Id') != 'mcp-1': return self.reply(400, {'error': 'no session'})
        name, args = body['params']['name'], body['params'].get('arguments', {})
        srv['calls'].append((name, args))
        if srv['fail'] == name: return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': json.dumps({'message': 'It broke.'})}], 'isError': True}})
        if name == 't3_project_list': out = {'projects': [{'id': 'p-g', 'workspaceRoot': str(garden)}, {'id': 'p-o', 'workspaceRoot': str(other)}]}
        elif name == 't3_thread_list': out = {'threads': srv['threads'], 'total': len(srv['threads'])}
        elif name == 't3_thread_read':
            items = MSGS.get(args['threadId'], [])
            end = min(args.get('beforePosition', len(items)) - 1, len(items))      # positions start at 1; read before that
            out = {'items': [{'type': t, 'text': x, 'textTruncated': False, 'updatedAt': now_iso()} for t, x in items[max(0, end - args.get('limit', 50)):end]]}
        elif name == 't3_pending_request':
            if args['action'] == 'list': out = {'requestIds': ['req-1'] if args['threadId'] == 'cli:ask' else []}
            else: out = {'requestId': 'req-1', 'questions': [{'id': 'q1', 'header': 'Soil', 'question': 'Which soil should the beds use?',
                         'options': [{'label': 'Loam (Recommended)', 'description': 'Holds water well'}, {'label': 'Sand', 'description': 'Drains fast'}], 'multiSelect': False}]}
        else: out = {}
        return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': json.dumps(out)}]}})
httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
port = httpd.server_address[1]
runtime = t3home / 'userdata' / 'server-runtime.json'
def t3_open(alive=True):
    pid = os.getpid() if alive else subprocess.run([sys.executable, '-c', 'import os; print(os.getpid())'], capture_output=True, text=True).stdout.strip()
    runtime.write_text(json.dumps({'version': 1, 'pid': int(pid), 'host': '127.0.0.1', 'port': port, 'origin': f'http://127.0.0.1:{port}', 'serverVersion': '0.1.11'}), encoding='utf-8')
def look():
    return subprocess.run([sys.executable, str(SETUP), 'watch', '--once'], env=env, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
def watch():
    f = claude / 't3' / 'watch.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None
reads = lambda: [a['threadId'] for n, a in srv['calls'] if n == 't3_thread_read']

try:
    # ---------- the setup ----------
    r = subprocess.run([sys.executable, str(SETUP), '--install', '--dry-run'], env=env, capture_output=True, timeout=60)
    out = r.stdout.decode()
    ok('the setup (dry run) would start the watcher now and at every sign-in, with pythonw and no window', 'Would start the T3 watcher now, and at every sign-in' in out
       and 'CurrentVersion\\Run, Nullovation City T3 watcher' in out and '" watch' in out and 'pythonw' in out, out)
    r = subprocess.run([sys.executable, str(SETUP), '--help'], env=env, capture_output=True, timeout=60)
    ok('--help says what the watcher does', b'watch --once' in r.stdout and b't3/watch.json' in r.stdout)

    # ---------- a look while T3 is open ----------
    t3_open()
    r = look(); w = watch()
    ok('a look writes t3/watch.json: running, with T3\'s version', r.returncode == 0 and w and w['app'] == 'nullovation-city' and w['kind'] == 't3-watch' and w['running'] is True and w['t3'] == '0.1.11', (r.stderr[-300:], w))
    ids = [t['id'] for t in w['threads']]
    ok('Claude\'s threads only, busy or recent, newest first: no other agent\'s, none days old', ids == ['cli:run', 'cli:ask', 'cli:ok'], ids)
    run = w['threads'][0]
    ok('each with its folder from its T3 project, its state, model, environment and background commands', run['folder'] == str(garden) and run['status'] == 'running'
       and run['model'] == 'claude-opus-5-5' and run['env'] == 'env-1234' and run['background'] == 1, run)
    ok('and its latest message, read from the end of the thread', run['last']['text'] == 'The beds are **drawn**, 4 by 6.' and ('t3_thread_read', {'threadId': 'cli:run', 'view': 'messages', 'limit': 4, 'maxCharsPerItem': 1500, 'beforePosition': 8}) in srv['calls'], run.get('last'))
    ask = w['threads'][1]
    ok('a waiting thread carries its question, with the choices and their words', ask['status'] == 'waiting' and ask['approval'] is False and ask['asks'][0]['request'] == 'req-1'
       and ask['asks'][0]['questions'][0]['question'] == 'Which soil should the beds use?' and [o['label'] for o in ask['asks'][0]['questions'][0]['options']] == ['Loam (Recommended)', 'Sand'], ask)
    ok('a waiting thread with no question listed is an approval, which T3\'s tools leave out', w['threads'][2]['approval'] is True and not w['threads'][2]['asks'])
    ok('it never sends an Origin header', srv['origins'] == 0)
    a = auth()
    ok('its key: a read-only MCP client session for 30 days, labelled', a and a[0] == ['auth', 'session', 'issue', '--subject', 'mcp-client', '--scope', 'orchestration:read', '--ttl', '30d', '--label', 'Nullovation City watcher', '--json'], a)
    keyfile = local / 'Nullovation City' / 't3-watch-token.json'
    ok('kept in AppData beside the helper, never in the Claude folder a page can read', json.loads(keyfile.read_text())['token'] == 'tok-1'
       and not any('tok-1' in f.read_text(encoding='utf-8', errors='replace') for f in claude.rglob('*') if f.is_file()))
    # a second look: the same key, and a thread unchanged is not read again
    n = len(reads()); m = os.path.getmtime(claude / 't3' / 'watch.json')
    look()
    ok('the next look keeps its key', len([c for c in auth() if c[:3] == ['auth', 'session', 'issue']]) == 1)
    ok('a look reads every thread again only when changed (a new watcher remembers nothing, so it reads)', len(reads()) >= n)
    # a key T3 no longer takes: a new one, the old revoked
    srv['tokens'] = {'tok-2'}
    look(); w = watch()
    ok('a key T3 refuses: it asks for a new one, revokes the old, and goes on', w['running'] and len(w['threads']) == 3 and ['auth', 'session', 'revoke', 'sess-1'] in auth()
       and json.loads(keyfile.read_text())['token'] == 'tok-2', auth()[-3:])
    # a tool failing
    srv['fail'] = 't3_thread_list'
    look(); w = watch()
    ok('a look that fails says so, T3 still open, and keeps no threads', w['running'] is True and 'It broke.' in w.get('error', '') and w['threads'] == [], w)
    srv['fail'] = None
    # T3 closed
    t3_open(alive=False)
    look(); w = watch()
    ok('T3 closed (its runtime file left behind by a process gone): it says so, and rests', w['running'] is False and w['threads'] == [], w)
    runtime.unlink()
    look()
    ok('with no runtime file at all, too', watch()['running'] is False)
    r = subprocess.run([sys.executable, str(SETUP), '--status'], env=env, capture_output=True, timeout=60)
    ok('--status says whether the watcher runs, and whether T3 is open', b'T3 watcher: not running; T3 is closed' in r.stdout, r.stdout[-200:])
    t3_open(); srv['tokens'] = {'tok-2'}
    look(); snap = watch()

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
window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (/^(nullovation-t3|t3code|claude|claude-cli):/i.test(href)) { window.__opened.push(href); return; } return anchorClick.call(this); };
"""
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        ctx.add_init_script(TEST_CITY)
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t58')) { sessionStorage.setItem('nc-t58', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        ev(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: 'l-g', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }}); window.changed(p); }}""")
        task = ev(f"() => getProject('{gp}').todos.find(t => !t.done).text")
        tid = ev(f"() => getProject('{gp}').todos.find(t => !t.done).id")
        T = f"getProject('{gp}').todos.find(t => t.id === '{tid}')"
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ok('with no watcher on this PC, Settings, Links says to run the T3 setup again', ev("() => document.querySelector('#t3Watch').textContent").startswith('Watcher: not heard from on this PC.'))
        ev("() => Settings.close()")
        def put_watch(d):
            ev("(text) => { window.__sub.set('t3/watch.json', { text, t: Date.now() + (window.__ct++) }); }", json.dumps(d))
            ev("() => T3.readWatch()"); pg.wait_for_timeout(400)
        snap['at'] = int(time.time() * 1000)
        put_watch(snap)
        ok('the city reads what the watcher saw', ev("() => !!T3.watched() && T3.watched().threads.length") == 3)
        # a task's threads: each its own state
        ev(f"""() => {{ const t = {T}; t.threads = [
            {{ id: 'cli:ask', env: 'env-1234', agent: 'Opus 5.5', kind: 'think', title: 'Think: ' + t.text, at: Date.now() - 900000, last: Date.now() - 600000 }},
            {{ id: 'cli:run', env: 'env-1234', agent: 'Opus 5.5', kind: 'build', title: t.text, at: Date.now() - 600000, last: Date.now() - 5000 }}]; window.changed(getProject('{gp}')); }}""")
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
        pg.click(f'li.task[data-id="{tid}"] .task-title'); pg.wait_for_timeout(300)
        rows = ev("() => [...document.querySelectorAll('.pv-t3-sec .t3-thread')].map(e => ({ where: e.querySelector('.t3-thread-where').textContent, last: (e.querySelector('.t3-thread-last') || {}).textContent || '' }))")
        ok('each of a task\'s threads says its own state, from the watcher: working, and waiting on you', [r['where'] for r in rows] == ['Opus 5.5, working', 'Opus 5.5, waiting on you'], rows)
        ok('with its latest message, plain', rows[0]['last'] == 'The beds are drawn, 4 by 6.' and rows[1]['last'] == 'Two soils fit; asking which.', rows)
        ok('the row\'s mark says working, in its color', 'working' in ev(f"() => document.querySelector('li.task[data-id=\"{tid}\"] .t3-open').className"))
        pg.screenshot(path=str(SHOTS / '580-watch-panel.png'))
        ev("() => FullView.close()"); pg.wait_for_timeout(300)
        # a session in T3 whose thread belongs to no task: Open in T3 and its latest message on its line (W2c)
        now = int(time.time() * 1000)
        sess = {'v': 1, 'app': 'nullovation-city', 'kind': 'claude-session', 'session': 's-t3', 'state': 'waiting', 'event': 'PermissionRequest', 'wait': 'approval', 'cwd': str(other),
                'task': '', 'ask': 'Run the tests', 'project': '', 'entry': 't3-code', 'at': now, 'since': now - 60000, 'started': now - 60000}
        other_id = ev("() => DB.projects.find(p => p.name !== 'Garden planner').id")
        ev(f"""() => {{ const p = getProject('{other_id}'); p.links.push({{ id: 'l-o', label: '', url: {json.dumps(str(other))}, icon: 'folder', shortcut: true }}); window.changed(p); }}""")
        ev("([k, text]) => { window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }", ['s-t3.json', json.dumps(sess)])
        ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(800)
        ev(f"() => Bubble.open('{other_id}')"); pg.wait_for_timeout(300)
        line = ev("() => { const l = [...document.querySelectorAll('#bubble .ld-line, .ld-line')].find(e => /needs your OK/.test(e.textContent)); return l ? { text: l.textContent, t3: !!l.querySelector('.ld-t3'), title: (l.querySelector('.ld-t3') || {}).title || '' } : null; }")
        ok('a session in T3 in a building\'s folder: its line gets Open in T3, saying its thread waits for your OK', line and line['t3'] and line['title'] == 'Opens its T3 thread, Run the tests: waiting for your OK.', line)
        ok('and its thread\'s latest message', line and 'Running the full suite needs your OK.' in line['text'], line)
        pg.screenshot(path=str(SHOTS / '581-watch-card.png'))
        ev("() => { window.__opened.length = 0; }")
        pg.click('.ld-line .ld-t3 >> nth=0'); pg.wait_for_timeout(100)
        ok('which opens that thread in T3', ev("() => window.__opened.slice()") == ['t3code://threads/env-1234/cli%3Aok'], ev("() => window.__opened.slice()"))
        ev("() => Bubble.close()")
        # a session not in T3 (the terminal): no thread
        sess2 = dict(sess, session='s-term', entry='cli', state='working', wait=None)
        ev("([k, text]) => { window.__sub.delete('s-t3.json'); window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }", ['s-term.json', json.dumps(sess2)])
        ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(800)
        ok('a session in the terminal is no T3 thread\'s', ev(f"() => T3.sessionThread(getProject('{other_id}'), ClaudeWork.sessionsOf(getProject('{other_id}'))[0])") is None)
        # Settings
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        ok('Settings, Links says what the watcher sees', ev("() => document.querySelector('#t3Watch').textContent") == 'Watcher: sees 3 Claude threads in T3 v0.1.11, looking every few seconds.')
        ev("() => Settings.close()")
        # T3 closed, and a watcher gone quiet
        put_watch(dict(snap, running=False, threads=[], at=int(time.time() * 1000)))
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        ok('T3 closed: the watcher rests, and says so', ev("() => document.querySelector('#t3Watch').textContent") == 'Watcher: T3 is closed, so it rests.')
        ev("() => Settings.close()")
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(300)
        pg.click(f'li.task[data-id="{tid}"] .task-title'); pg.wait_for_timeout(300)
        ok('with T3 closed, a thread says when it was last sent, from the hooks as before', ev("() => document.querySelector('.pv-t3-sec .t3-thread-where').textContent").startswith('Opus 5.5, sent'))
        ev("() => FullView.close()")
        put_watch(dict(snap, at=int(time.time() * 1000) - 5 * 60000))
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        ok('a watcher not heard from for 5 minutes: said, and its threads left alone', ev("() => document.querySelector('#t3Watch').textContent").startswith('Watcher: last heard from 5 minutes ago.') and ev("() => T3.watched()") is None)
        ev("() => Settings.close()")
        b.close()
finally:
    httpd.shutdown()
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
