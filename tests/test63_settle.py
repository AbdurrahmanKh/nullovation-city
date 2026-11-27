"""Pass 63: ticking a task settles its T3 threads (0.1.98, "Ticking the task also closes the T3"). The city writes what
it asks into the Claude folder as t3/organize-<id>.json; the T3 watcher takes it and settles each thread once Claude's
turn there ends, signing an agent in at full access through T3's own sign-in for agents for each batch and revoking
both keys after, since his threads run in full access and a key from t3 auth session issue acts at approval-required.
First the watcher against a fake T3 that signs agents in and refuses as T3 v0.1.11 does, with a fake t3 command for
its keys; then the city with a Claude folder held in memory."""
import base64, hashlib, http.server, json, os, pathlib, shutil, subprocess, sys, tempfile, threading, time, urllib.parse
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

SETUP = ROOT / 'src' / 'setup' / 'nullovation-t3-links.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-settle-'))
home, local, claude = work / 'home', work / 'local', work / 'Claude-Hooks'
t3home = home / '.t3'
garden = work / 'Garden planner'
for d in (home / '.claude', local, claude / 't3', t3home / 'bin', t3home / 'userdata', garden):
    d.mkdir(parents=True, exist_ok=True)
(t3home / 'userdata' / 'environment-id').write_text('env-1234\n', encoding='utf-8')
(home / '.claude' / 'nullovation-city.json').write_text(json.dumps({'app': 'nullovation-city', 'kind': 'claude-folder', 'folder': str(claude)}), encoding='utf-8')
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(local), NULLOVATION_QUIET='1', PYTHONUTF8='1')
env.pop('T3CODE_HOME', None)

# ---------- the fake t3 command: keys issued, listed and revoked, kept in a file the fake server shares ----------
STATE = work / 'sessions.json'
STATE.write_text('{"active": {}, "calls": [], "n": 0}', encoding='utf-8')
FAKE_T3 = work / 'fake_t3.py'
FAKE_T3.write_text(r'''import json, sys
state = sys.argv[1]; args = sys.argv[2:]
s = json.load(open(state))
s['calls'].append(args)
out, code = '', 2
if args[:3] == ['auth', 'session', 'issue']:
    s['n'] += 1
    owner = 'access:write' in args
    label = args[args.index('--label') + 1] if '--label' in args else ''
    sid = ('own-sess-%d' if owner else 'rd-sess-%d') % s['n']
    tok = ('own-%d' if owner else 'rd-%d') % s['n']
    s['active'][sid] = {'token': tok, 'subject': 'cli-issued-session' if owner else 'mcp-client', 'label': label}
    out, code = json.dumps({'sessionId': sid, 'token': tok, 'expiresAt': '2099-01-01T00:00:00.000Z'}, indent=2), 0
elif args[:3] == ['auth', 'session', 'list']:
    out, code = json.dumps([{'sessionId': k, 'subject': v['subject'], 'client': {'label': v['label']}} for k, v in s['active'].items()], indent=2), 0
elif args[:3] == ['auth', 'session', 'revoke']:
    s['active'].pop(args[3], None); out, code = 'Revoked.', 0
json.dump(s, open(state, 'w'))
print(out); sys.exit(code)
''', encoding='utf-8')
WRAP = work / 'wrap.py'
WRAP.write_text(f'import runpy, sys\nsys.argv = [{str(FAKE_T3)!r}, {str(STATE)!r}] + sys.argv[1:]\nrunpy.run_path({str(FAKE_T3)!r}, run_name="__main__")\n', encoding='utf-8')
(t3home / 'bin' / 't3.cmd').write_text('@echo off\r\n' f'set "T3CODE_HOME={t3home}"\r\n' f'"{sys.executable}" "{WRAP}" %*\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')
lock = threading.Lock()
def state():
    with lock: return json.loads(STATE.read_text())
def save(s):
    with lock: STATE.write_text(json.dumps(s))
issues = lambda: [c for c in state()['calls'] if c[:3] == ['auth', 'session', 'issue']]

# ---------- the fake T3 server: its agent tools at /mcp and its sign-in for agents ----------
now_iso = lambda ago=0: time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() - ago))
def thread(tid, status='completed', settled=False, **o):
    return {'threadId': tid, 'title': 'Thread ' + tid, 'status': status, 'providerInstanceId': 'claudeAgent', 'model': 'claude-opus-5-5', 'projectId': 'p-g',
            'updatedAt': now_iso(5), 'createdAt': now_iso(600), 'itemCount': 0, 'pendingBackgroundTasks': [], 'settled': settled, 'runtimeMode': 'full-access', **o}
srv = {'calls': [], 'origins': 0, 'signins': [], 'refuse': {}, 'grants': {}, 'fail_signin': False,
       'threads': {t['threadId']: t for t in [thread('cli:done'), thread('cli:run', 'running'), thread('cli:ask', 'waiting'), thread('cli:old', settled=True),
                                              thread('cli:arch', archived=True), thread('cli:bad'), thread('cli:race')]}}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, code, body=None, headers=None):
        self.send_response(code)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        data = json.dumps(body).encode() if body is not None else b''
        if body is not None: self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def token(self):
        return (self.headers.get('Authorization') or '').replace('Bearer ', '')
    def active(self, tok):
        return any(v['token'] == tok for v in state()['active'].values())
    def do_GET(self):
        if self.path == '/.well-known/oauth-protected-resource/mcp':
            return self.reply(200, {'resource': f'http://127.0.0.1:{port}/mcp', 'authorization_servers': [f'http://127.0.0.1:{port}']})
        return self.reply(404, {'error': 'not found'})
    def do_POST(self):
        if self.headers.get('Origin') is not None: srv['origins'] += 1; return self.reply(403)
        raw = self.rfile.read(int(self.headers.get('Content-Length') or 0)).decode()
        tok = self.token()
        if self.path == '/oauth/mcp/register':
            body = json.loads(raw); srv['signins'].append(('register', body))
            return self.reply(201, {'client_id': 'cid-' + body['client_name'], 'client_name': body['client_name'], 'redirect_uris': body['redirect_uris'],
                                    'grant_types': ['authorization_code'], 'response_types': ['code'], 'token_endpoint_auth_method': 'none'})
        if self.path == '/oauth/mcp/approval':
            body = json.loads(raw); srv['signins'].append(('approval', body, tok))
            if not tok.startswith('own-') or not self.active(tok): return self.reply(401, {'error': 'no session'})
            return self.reply(200, {'clientName': 'x', 'redirectHost': '127.0.0.1:9', 'environmentHost': '127.0.0.1', 'csrfToken': 'csrf-' + tok})
        if self.path == '/oauth/mcp/decision':
            body = json.loads(raw); srv['signins'].append(('decision', body, tok))
            if srv['fail_signin']: return self.reply(400, {'_tag': 'AuthMcpApprovalError', 'message': 'No.'})
            d, a = body['decision'], body['authorization']
            if not tok.startswith('own-') or not self.active(tok) or d.get('csrfToken') != 'csrf-' + tok or d.get('_tag') != 'browser-session': return self.reply(400, {'message': 'bad decision'})
            code = 'code-%d' % (len(srv['grants']) + 1)
            srv['grants'][code] = {'challenge': a['code_challenge'], 'access': d['access'], 'client': a['client_id'], 'redirect': a['redirect_uri']}
            return self.reply(200, {'redirectTo': a['redirect_uri'] + '?' + urllib.parse.urlencode({'code': code, 'state': a['state'], 'iss': 'x'})})
        if self.path == '/oauth/mcp/token':
            f = {k: v[0] for k, v in urllib.parse.parse_qs(raw).items()}; srv['signins'].append(('token', f))
            g = srv['grants'].pop(f.get('code'), None)
            pkce = g and base64.urlsafe_b64encode(hashlib.sha256(f.get('code_verifier', '').encode()).digest()).decode().rstrip('=') == g['challenge']
            if not g or not pkce or f.get('grant_type') != 'authorization_code' or f.get('redirect_uri') != g['redirect']: return self.reply(400, {'error': 'invalid_grant'})
            s = state(); s['n'] += 1
            s['active']['mcp-sess-%d' % s['n']] = {'token': ('full-%d' if g['access'] == 'full-access' else 'sup-%d') % s['n'], 'subject': 'mcp-client', 'label': g['client'][4:]}
            save(s)
            return self.reply(200, {'access_token': s['active']['mcp-sess-%d' % s['n']]['token'], 'token_type': 'Bearer', 'expires_in': 2592000, 'scope': 'orchestration:read orchestration:operate'})
        if self.path != '/mcp': return self.reply(404, {'error': 'not found'})
        body = json.loads(raw)
        if not self.active(tok): return self.reply(401, {'error': 'invalid_mcp_credential'})
        m, rid = body.get('method'), body.get('id')
        if m == 'initialize': return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'protocolVersion': '2025-06-18'}}, {'Mcp-Session-Id': 'mcp-1'})
        if rid is None: return self.reply(202)
        name, args = body['params']['name'], body['params'].get('arguments', {})
        srv['calls'].append((tok, name, args))
        def fail(msg): return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': json.dumps({'message': msg})}], 'isError': True}})
        out = {}
        if name == 't3_project_list': out = {'projects': [{'id': 'p-g', 'workspaceRoot': str(garden)}]}
        elif name == 't3_thread_list': out = {'threads': [t for t in srv['threads'].values() if not t.get('archived')]}
        elif name == 't3_thread_read': out = {'items': []}
        elif name == 't3_pending_request': out = {'requestIds': []}
        elif name == 't3_thread_organize':
            tid, t = args['threadId'], srv['threads'].get(args['threadId'])
            if tok.startswith('rd-'): return fail('This tool changes the environment, and this MCP client was approved for read-only access.')
            if not tok.startswith('full-'): return fail(f'Thread "{tid}" runs in full-access/default, above this caller\'s approval-required/default limit.')
            if t is None: return fail('Thread ' + tid + ' was not found.')
            if t.get('archived'): return fail('Thread ' + tid + ' is archived.')
            if tid in srv['refuse']: return fail(srv['refuse'][tid])
            if args['action'] == 'settle':
                if t['status'] in ('running', 'starting', 'preparing', 'queued'): return fail('Thread ' + tid + ' is still running. Stop it before settling.')
                if t['status'] == 'waiting': return fail('Thread ' + tid + ' is waiting on an approval or question. Answer it before settling.')
            t['settled'] = args['action'] == 'settle'
            out = {'sequence': 7}
        return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': json.dumps(out)}]}})
httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
port = httpd.server_address[1]
runtime = t3home / 'userdata' / 'server-runtime.json'
def t3_open(alive=True):
    if not alive:
        if runtime.exists(): runtime.unlink()
        return
    runtime.write_text(json.dumps({'pid': os.getpid(), 'origin': f'http://127.0.0.1:{port}', 'serverVersion': '0.1.11'}), encoding='utf-8')
def look():
    return subprocess.run([sys.executable, str(SETUP), 'watch', '--once'], env=env, capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
def watch():
    f = claude / 't3' / 'watch.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None
def ask(settle=(), unsettle=(), at=None, **o):
    d = {'app': 'nullovation-city', 'kind': 't3-organize', 'version': 1, 'id': 'ask-%d' % (len(list((claude / 't3').glob('organize-*'))) + time.time_ns() % 100000),
         'at': at if at is not None else int(time.time() * 1000), 'settle': list(settle), 'unsettle': list(unsettle)}
    d.update(o)
    (claude / 't3' / ('organize-' + d['id'] + '.json')).write_text(json.dumps(d), encoding='utf-8')
organizes = lambda: [(a['threadId'], a['action'], tok) for tok, n, a in srv['calls'] if n == 't3_thread_organize']
queue = lambda: json.loads((local / 'Nullovation City' / 't3-organize.json').read_text()) if (local / 'Nullovation City' / 't3-organize.json').exists() else {}
result = lambda tid: [r for r in (watch() or {}).get('organized', []) if r['thread'] == tid]
row = lambda tid: next((t for t in watch()['threads'] if t['id'] == tid), None)

try:
    # ---------- the watcher ----------
    t3_open()
    ask(settle=['cli:done', 'cli:run'])
    r = look()
    ok('a look takes the city\'s ask: the file is gone from the Claude folder', r.returncode == 0 and not list((claude / 't3').glob('organize-*')), r.stderr[-400:])
    ok('a thread whose turn has ended is settled through t3_thread_organize', ('cli:done', 'settle') in [x[:2] for x in organizes()] and srv['threads']['cli:done']['settled'], organizes())
    ok('with a key signed in at full access, as T3 needs for a full-access thread', all(x[2].startswith('full-') for x in organizes()), organizes())
    own = [c for c in issues() if 'access:write' in c]
    ok('the sign-in approved by a short session the t3 command issues: 5 minutes, labelled, with the scopes full access asks', own and own[0] == ['auth', 'session', 'issue', '--scope', 'orchestration:read',
       '--scope', 'orchestration:operate', '--scope', 'settings:write', '--scope', 'source-control:write', '--scope', 'access:write', '--ttl', '5m', '--label', 'Nullovation City settle sign-in', '--json'], own)
    steps = [s[0] for s in srv['signins']]
    dec = next(s for s in srv['signins'] if s[0] == 'decision')
    ok('T3\'s own sign-in for agents, in order: register, approval, decision, token', steps == ['register', 'approval', 'decision', 'token'], steps)
    ok('the decision: the owner\'s session approving full access, with its csrf token and PKCE', dec[1]['decision']['_tag'] == 'browser-session' and dec[1]['decision']['access'] == 'full-access'
       and dec[1]['authorization']['code_challenge_method'] == 'S256' and dec[2].startswith('own-'), dec)
    ok('the agent named Nullovation City settle', next(s for s in srv['signins'] if s[0] == 'register')[1]['client_name'] == 'Nullovation City settle')
    ok('both keys revoked after: no settle session left in T3', not [k for k, v in state()['active'].items() if v['label'].startswith('Nullovation City settle')], state()['active'])
    ok('no key that can write kept on disk, in AppData or the Claude folder', not any(x in f.read_text(encoding='utf-8', errors='replace') for f in list(local.rglob('*')) + list(claude.rglob('*')) if f.is_file() for x in ('own-', 'full-')))
    ok('it never sends an Origin header', srv['origins'] == 0)
    ok('a running thread is not asked: it waits for its turn to end', ('cli:run', 'settle') not in [x[:2] for x in organizes()] and 'cli:run' in queue().get('threads', {}), queue())
    w = watch()
    ok('watch.json says the watcher settles (organizes), and what it did', w.get('organizes') == 1 and result('cli:done') and result('cli:done')[0]['ok'] is True, w.get('organized'))
    ok('and the thread settled in this look\'s rows', row('cli:done')['settled'] is True and row('cli:run')['settled'] is False)

    n = len(issues()); look()
    ok('still running: no sign-in, no call', len(issues()) == n and ('cli:run', 'settle') not in [x[:2] for x in organizes()])
    srv['threads']['cli:run']['status'] = 'completed'
    look()
    ok('its turn ended: settled at the next look', ('cli:run', 'settle') in [x[:2] for x in organizes()] and srv['threads']['cli:run']['settled'] and not queue()['threads'])

    # T3 says it is still at it though the list said done: kept, and tried again after a while
    srv['refuse']['cli:race'] = 'Thread cli:race has a queued message. Send it or remove it from the queue before settling.'
    ask(settle=['cli:race']); look()
    q = queue()['threads']
    ok('a thread T3 will not settle yet (a queued message) is kept, and when it was tried', 'cli:race' in q and q['cli:race'].get('tried'), q)
    n = len(organizes()); look()
    ok('not tried again at once', len(organizes()) == n)
    del srv['refuse']['cli:race']
    q = queue(); q['threads']['cli:race']['tried'] = 0
    (local / 'Nullovation City' / 't3-organize.json').write_text(json.dumps(q))
    look()
    ok('tried again after a while, and settled', srv['threads']['cli:race']['settled'] and not queue()['threads'])

    # reopened: unsettled
    ask(unsettle=['cli:done']); look()
    ok('an unsettle makes the thread active again', ('cli:done', 'unsettle') in [x[:2] for x in organizes()] and srv['threads']['cli:done']['settled'] is False)
    # a settle still waiting, taken back: T3 never hears of it
    ask(settle=['cli:ask'], at=int(time.time() * 1000) - 5)
    ask(unsettle=['cli:ask'])
    n = len(organizes()); look()
    ok('a tick and its undo before the thread settled: nothing asked of T3, nothing left waiting', len(organizes()) == n and 'cli:ask' not in queue()['threads'], (organizes()[n:], queue()))
    ask(settle=['cli:ask']); look()
    ok('a thread waiting on you is not asked either: it settles once you answer and the turn ends', 'cli:ask' in queue()['threads'] and ('cli:ask', 'settle') not in [x[:2] for x in organizes()])
    ask(unsettle=['cli:ask']); look()
    # already as asked, gone, archived, refused
    n = len(organizes())
    ask(settle=['cli:old']); look()
    ok('a thread settled already (in T3 itself) is left alone, and counts as done', len(organizes()) == n and result('cli:old')[-1]['ok'] is True)
    ask(settle=['cli:arch', 'cli:gone']); look()
    ok('an archived thread, and one T3 no longer has: nothing to do, no error', result('cli:arch')[-1]['ok'] is True and result('cli:gone')[-1]['ok'] is True, (result('cli:arch'), result('cli:gone')))
    srv['refuse']['cli:bad'] = 'It broke.'
    ask(settle=['cli:bad']); look()
    ok('a refusal T3 gives for another reason is said, with its words', result('cli:bad')[-1]['ok'] is False and result('cli:bad')[-1]['error'] == 'It broke.', result('cli:bad'))
    # asks that are not the city's
    ask(settle=['bad id &', 'cli:x'], app='other')
    ask(settle=['bad id &'])
    ask(settle=['cli:x'], at=int(time.time() * 1000) - 3 * 86400000)
    n = len(organizes()); look()
    ok('an ask another app wrote, a thread id T3 would not know, and an ask days old are left out, and their files go', len(organizes()) == n and not list((claude / 't3').glob('organize-*'))
       and not [k for k in queue()['threads']], queue())
    # T3 closed: kept until it opens
    t3_open(alive=False)
    srv['threads']['cli:done']['settled'] = False
    ask(settle=['cli:done']); look()
    ok('T3 closed: the ask is taken and kept, nothing asked', 'cli:done' in queue()['threads'] and not list((claude / 't3').glob('organize-*')) and watch()['running'] is False and watch()['organizes'] == 1)
    t3_open(); look()
    ok('once T3 opens, it settles', srv['threads']['cli:done']['settled'] and not queue()['threads'])
    # the sign-in refused: kept, and said in watch.json
    srv['threads']['cli:done']['settled'] = False; srv['fail_signin'] = True
    ask(settle=['cli:done']); look()
    ok('T3 refusing the sign-in: the ask is kept, the failure said in watch.json, the owner\'s key revoked', 'cli:done' in queue()['threads'] and 'T3 refused /oauth/mcp/decision' in watch().get('organizeError', '')
       and not [k for k, v in state()['active'].items() if v['label'].startswith('Nullovation City settle')], (watch().get('organizeError'), state()['active']))
    srv['fail_signin'] = False
    q = queue(); q['threads']['cli:done']['tried'] = 0; (local / 'Nullovation City' / 't3-organize.json').write_text(json.dumps(q))
    look()
    ok('and settled once T3 lets it in, the failure no longer said', srv['threads']['cli:done']['settled'] and 'organizeError' not in watch())
    # given up after two days
    q = queue(); q['threads']['cli:ask'] = {'do': 'settle', 'at': int(time.time() * 1000) - 3 * 86400000}; (local / 'Nullovation City' / 't3-organize.json').write_text(json.dumps(q))
    look()
    ok('a settle whose turn never ended in two days is given up, and said', result('cli:ask')[-1]['ok'] is False and 'did not end within 2 days' in result('cli:ask')[-1]['error'] and 'cli:ask' not in queue()['threads'])
    r = subprocess.run([sys.executable, str(SETUP), '--help'], env=env, capture_output=True, timeout=60)
    ok('--help says the watcher settles a ticked task\'s threads', b'settles a task\'s T3 threads when the task is ticked off' in r.stdout)

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
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t63')) { sessionStorage.setItem('nc-t63', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        open_ids = ev(f"() => getProject('{gp}').todos.filter(t => !t.done && !t.repeat).map(t => t.id)")
        a, c, bare = open_ids[0], open_ids[1], open_ids[2]
        T = lambda tid: f"getProject('{gp}').todos.find(t => t.id === '{tid}')"
        now = int(time.time() * 1000)
        ev(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: 'l-g', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }});
            {T(a)}.threads = [{{ id: 'cli:a1', env: 'env-1234', agent: 'Opus 5.5', kind: 'think', title: 'Think it', at: {now - 9000}, last: {now - 9000} }},
                             {{ id: 'cli:a2', env: 'env-1234', agent: 'Opus 5.5', kind: 'build', title: 'Build it', at: {now - 5000}, last: {now - 5000} }}];
            {T(c)}.threads = [{{ id: 'cli:c1', env: 'env-1234', agent: 'default', kind: 'build', title: 'Other', at: {now - 5000}, last: {now - 5000} }}];
            window.changed(p); }}""")
        ev("() => { News._test.forget(); News.renderSection(); }")
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ev("() => Settings.close()"); pg.wait_for_timeout(200)
        def put(k, d): ev("([k, text]) => { window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }", [k, json.dumps(d)])
        def watched(threads, **o):
            put('t3/watch.json', {'app': 'nullovation-city', 'kind': 't3-watch', 'version': 1, 'at': int(time.time() * 1000), 'running': True, 't3': '0.1.11', 'organizes': 1, 'organized': [], 'threads': threads, **o})
            ev("() => T3.readWatch()"); pg.wait_for_timeout(300)
        wrow = lambda tid, status='completed', settled=False: {'id': tid, 'env': 'env-1234', 'title': 'x', 'status': status, 'folder': str(garden), 'model': 'claude-opus-5-5',
                                                                 'updated': now, 'created': now - 60000, 'background': 0, 'settled': settled}
        watched([wrow('cli:a1'), wrow('cli:a2', 'running'), wrow('cli:c1')])
        asks = lambda: ev("() => [...window.__sub].filter(([k]) => /^t3\\/organize-/.test(k)).map(([k, f]) => JSON.parse(f.text))")
        clear = lambda: ev("() => { for (const k of [...window.__sub.keys()]) if (/^t3\\/organize-/.test(k)) window.__sub.delete(k); }")
        said = lambda: ev("() => { const t = document.querySelector('#toast'); return t.classList.contains('show') ? t.textContent : ''; }")
        quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay, #ldSay').forEach(e => e.hidden = true); }")
        settled = lambda tid: ev(f"() => {T(tid)}.threads.map(x => !!x.settled)")

        # ---------- a tick in the project view ----------
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
        pg.click(f'li.task[data-id="{a}"] .cb'); pg.wait_for_timeout(300)
        s = asks()
        ok('ticking a task off writes one ask into the Claude folder: settle each of its T3 threads', len(s) == 1 and s[0]['kind'] == 't3-organize' and s[0]['app'] == 'nullovation-city'
           and sorted(s[0]['settle']) == ['cli:a1', 'cli:a2'] and s[0]['unsettle'] == [], s)
        ok('no link followed: nothing for the browser to ask', not [x for x in ev("() => window.__opened.slice()") if x.startswith('nullovation-t3:')])
        ok('each thread keeps that it was asked to settle', settled(a) == [True, True])
        ok('the watcher is live and settles, so nothing more is said', 'T3' not in said(), said())
        clear()
        pg.click(f'li.task[data-id="{a}"] .cb'); pg.wait_for_timeout(300)
        s = asks()
        ok('reopening it asks to make them active again, and the marks go', len(s) == 1 and sorted(s[0]['unsettle']) == ['cli:a1', 'cli:a2'] and s[0]['settle'] == [] and settled(a) == [False, False], s)
        clear()
        pg.click(f'li.task[data-id="{bare}"] .cb'); pg.wait_for_timeout(300)
        ok('a task with no T3 thread: no ask', asks() == [])
        pg.click(f'li.task[data-id="{bare}"] .cb'); pg.wait_for_timeout(300)
        # two ticks in one moment (Apply all): one ask
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, {T(a)}); tickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        s = asks()
        ok('two ticks at once, as Apply all makes: one ask with every thread', len(s) == 1 and sorted(s[0]['settle']) == ['cli:a1', 'cli:a2', 'cli:c1'], s)
        ok('the marks are kept with the task, in the data', ev(f"() => readThreads({T(a)}).threads.every(x => typeof x.settled === 'number')"))
        clear()
        ev(f"() => {{ const p = getProject('{gp}'); untickTask(p, {T(a)}); untickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        clear()

        # ---------- the task panel: where it lands, and Esc ----------
        pg.click(f'li.task[data-id="{a}"] .task-title'); pg.wait_for_timeout(300)
        quiet()
        pg.click('#pvTaskDone'); pg.wait_for_timeout(300)
        ok('ticked in the task panel: the same ask', len(asks()) == 1 and sorted(asks()[0]['settle']) == ['cli:a1', 'cli:a2'])
        where = lambda tid: ev(f"() => (document.querySelector('.pv-t3-sec .t3-thread[data-thread=\"{tid}\"] .t3-thread-where') || {{}}).textContent")
        ok('a thread at work says it settles when its turn ends', where('cli:a2') == 'Opus 5.5, working, settles when its turn ends', where('cli:a2'))
        ok('one whose turn ended says it is settling, until the watcher sees it settled', where('cli:a1') == 'Opus 5.5, settling', where('cli:a1'))
        watched([wrow('cli:a1', settled=True), wrow('cli:a2', 'running'), wrow('cli:c1')])
        ok('then says settled', where('cli:a1') == 'Opus 5.5, settled', where('cli:a1'))
        pg.screenshot(path=str(SHOTS / '630-settle-panel.png'))
        clear()
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        s = asks()
        ok('Esc undoes the tick, and the ask with it: its threads active again', ev(f"() => !{T(a)}.done") and len(s) == 1 and sorted(s[0]['unsettle']) == ['cli:a1', 'cli:a2'] and settled(a) == [False, False], s)
        clear()
        ev("() => FullView.close()"); pg.wait_for_timeout(200)

        # ---------- what the watcher did ----------
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        clear(); quiet()
        watched([wrow('cli:c1')], organized=[{'thread': 'cli:c1', 'do': 'settle', 'ok': False, 'at': int(time.time() * 1000), 'error': 'It broke.'}])
        ok('a thread T3 would not settle: said, with its words', said() == 'T3 did not settle the T3 thread of ' + ev(f"() => {T(c)}.text") + ': It broke.', said())
        ok('and it loses its mark', settled(c) == [False])
        quiet(); ev("() => T3.readWatch()"); pg.wait_for_timeout(300)
        ok('said once', said() == '')
        ev(f"() => {{ const p = getProject('{gp}'); untickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        clear()

        # ---------- a watcher that cannot settle yet ----------
        watched([wrow('cli:c1')], organizes=None)
        quiet()
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(1900)
        ok('a watcher from before 0.1.98: the ask waits, and the city says to run the setup again', len(asks()) == 1
           and said() == 'Run the T3 setup again, in Settings, Links, so ticking a task settles its T3 thread.', said())
        clear(); quiet()
        ev(f"() => {{ const p = getProject('{gp}'); untickTask(p, {T(c)}); tickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(1900)
        ok('said once a visit', said() == '', said())
        ev(f"() => {{ const p = getProject('{gp}'); untickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        clear()
        put('t3/watch.json', {'app': 'nullovation-city', 'kind': 't3-watch', 'version': 1, 'at': int(time.time() * 1000) - 200000, 'running': True, 'organizes': 1, 'threads': []})
        ev("() => { T3.readWatch(); T3._test.warned(false); }"); pg.wait_for_timeout(300)
        quiet()
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(1900)
        ok('a watcher not heard from: the ask waits for it, and that is said', len(asks()) == 1 and said().startswith('The T3 watcher is not running, so the task\'s T3 thread settles once it runs.'), said())
        ev(f"() => {{ const p = getProject('{gp}'); untickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        clear()

        # ---------- the switch ----------
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        ok('Settings, Links, T3 Code: the switch, on by default', ev("() => document.querySelector('#optT3Settle').checked") and not ev("() => document.querySelector('[data-set=\"t3Settle\"]').classList.contains('changed')"))
        pg.locator('#optT3Settle').scroll_into_view_if_needed()
        pg.click('#optT3Settle'); pg.wait_for_timeout(200)
        ok('turned off: kept in this browser, its dot shown', ev("() => localStorage.getItem('nullovation-city:t3Settle')") == '0' and ev("() => document.querySelector('[data-set=\"t3Settle\"]').classList.contains('changed')"))
        pg.screenshot(path=str(SHOTS / '631-settle-setting.png'))
        ev("() => Settings.close()"); pg.wait_for_timeout(200)
        ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, {T(c)}); window.changed(p); }}"); pg.wait_for_timeout(300)
        ok('off: a tick leaves its threads as they are', asks() == [] and settled(c) == [False])
        ev(f"() => {{ const p = getProject('{gp}'); untickTask(p, {T(c)}); window.changed(p); }}")
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnTabReset'); pg.wait_for_timeout(200)
        ok('the Links tab\'s Reset to defaults turns it on again', ev("() => T3.settles()") and ev("() => localStorage.getItem('nullovation-city:t3Settle')") is None)
        ev("() => Settings.close()")
        b.close()
finally:
    httpd.shutdown()
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
