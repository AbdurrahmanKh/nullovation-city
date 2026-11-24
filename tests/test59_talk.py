"""Pass 59: talking to the leaders (0.1.94, City as My Terminal, Round 1, L1, L4, R1 to R3, and Brainstorm 1, i5, i6).
A conversation with Claude in a T3 thread is a topic: what it asks, with its choices as buttons and Claude's pick
marked, and a reply box that steers, queues, or answers a question; topics flip with arrows on the cards and in the
bubble. First the helper, which answers and steers through T3's agent tools with a key for one minute's work, against
a fake T3 server; then the city with a Claude folder held in memory, the helper's answers put back by hand."""
import http.server, json, os, pathlib, shutil, subprocess, sys, tempfile, threading, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

SETUP = ROOT / 'src' / 'setup' / 'nullovation-t3-links.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-talk-'))
home, local, claude = work / 'home', work / 'local', work / 'Claude-Hooks'
t3home = home / '.t3'
garden, other = work / 'Garden planner', work / 'Other'
for d in (home / '.claude', local, claude / 't3', t3home / 'bin', t3home / 'userdata', garden, other):
    d.mkdir(parents=True, exist_ok=True)
(t3home / 'userdata' / 'environment-id').write_text('env-1234\n', encoding='utf-8')
(home / '.claude' / 'nullovation-city.json').write_text(json.dumps({'app': 'nullovation-city', 'kind': 'claude-folder', 'folder': str(claude)}), encoding='utf-8')
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(local), NULLOVATION_QUIET='1', PYTHONUTF8='1')
env.pop('T3CODE_HOME', None)

LOG = work / 't3-calls.json'
FAKE_T3 = work / 'fake_t3.py'
FAKE_T3.write_text(r'''import json, os, sys
log = sys.argv[1]; args = sys.argv[2:]
data = sys.stdin.buffer.read().decode('utf-8') if '-' in args else ''
calls = json.load(open(log)) if os.path.exists(log) else []
calls.append({'args': args, 'stdin': data}); json.dump(calls, open(log, 'w'))
if args[:3] == ['auth', 'session', 'issue']:
    n = len([c for c in calls if c['args'][:3] == ['auth', 'session', 'issue']])
    print(json.dumps({'sessionId': 'op-%d' % n, 'token': 'op-%d' % n, 'expiresAt': '2099-01-01T00:00:00.000Z'}, indent=2)); sys.exit(0)
if args[:3] == ['auth', 'session', 'revoke']: sys.exit(0)
if args[:2] == ['thread', 'send']: print(json.dumps({'threadId': args[2]})); sys.exit(0)
sys.exit(2)
''', encoding='utf-8')
WRAP = work / 'wrap.py'
WRAP.write_text(f'import runpy, sys\nsys.argv = [{str(FAKE_T3)!r}, {str(LOG)!r}] + sys.argv[1:]\nrunpy.run_path({str(FAKE_T3)!r}, run_name="__main__")\n', encoding='utf-8')
(t3home / 'bin' / 't3.cmd').write_text('@echo off\r\n' f'set "T3CODE_HOME={t3home}"\r\n' f'"{sys.executable}" "{WRAP}" %*\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')
calls = lambda: json.loads(LOG.read_text()) if LOG.exists() else []

srv = {'calls': [], 'refuse': set()}
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def reply(self, code, body=None, headers=None):
        self.send_response(code)
        for k, v in (headers or {}).items(): self.send_header(k, v)
        data = json.dumps(body).encode() if body is not None else b''
        if body is not None: self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        tok = (self.headers.get('Authorization') or '').replace('Bearer ', '')
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)))
        if not tok.startswith('op-'): return self.reply(401, {'error': 'invalid_mcp_credential'})
        m, rid = body.get('method'), body.get('id')
        if m == 'initialize': return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'protocolVersion': '2025-06-18'}}, {'Mcp-Session-Id': 's-1'})
        if rid is None: return self.reply(202)
        name, args = body['params']['name'], body['params'].get('arguments', {})
        srv['calls'].append((tok, name, args))
        if name in srv['refuse']:
            return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': json.dumps({'message': 'The target cannot run with broader modes than yours.'})}], 'isError': True}})
        return self.reply(200, {'jsonrpc': '2.0', 'id': rid, 'result': {'content': [{'type': 'text', 'text': json.dumps({'ok': True})}]}})
httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
runtime = t3home / 'userdata' / 'server-runtime.json'
def t3_open(alive=True):
    if not alive:
        if runtime.exists(): runtime.unlink()
        return
    runtime.write_text(json.dumps({'pid': os.getpid(), 'origin': f'http://127.0.0.1:{httpd.server_address[1]}', 'serverVersion': '0.1.11'}), encoding='utf-8')
def helper_send(ident, **o):
    d = {'app': 'nullovation-city', 'kind': 't3-send', 'version': 1, 'id': ident, 'at': int(time.time() * 1000), 'project': 'Garden planner', 'folder': str(garden), 'title': 'Pick the soil'}
    d.update(o)
    (claude / 't3' / ('send-' + ident + '.json')).write_text(json.dumps(d), encoding='utf-8')
    subprocess.run([sys.executable, str(SETUP), 'open', 'nullovation-t3:send/' + ident], env=env, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    f = claude / 't3' / (ident + '.done.json')
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None

try:
    # ---------- the helper ----------
    t3_open()
    a = helper_send('answer01', action='answer', thread='cli:ask', request='req-1', answers={'q1': 'Loam (Recommended)'})
    ok('an answer goes to T3 as its window would give it: t3_pending_request respond, with the request and each answer', a and a['ok'] and a.get('answered')
       and srv['calls'][-1][1:] == ('t3_pending_request', {'action': 'respond', 'threadId': 'cli:ask', 'requestId': 'req-1', 'answers': {'q1': 'Loam (Recommended)'}}), (a, srv['calls'][-1:]))
    c = calls()
    ok('with a key for one minute\'s work that can write, asked for then and revoked after', c[0]['args'] == ['auth', 'session', 'issue', '--subject', 'mcp-client', '--scope', 'orchestration:read',
       '--scope', 'orchestration:operate', '--ttl', '5m', '--label', 'Nullovation City reply', '--json'] and c[1]['args'] == ['auth', 'session', 'revoke', 'op-1'], c[:2])
    ok('no key that can write is kept', not any('op-' in f.read_text(encoding='utf-8', errors='replace') for f in local.rglob('*') if f.is_file()))
    a = helper_send('steer001', action='reply', mode='steer', thread='cli:run', message='Use loam for the front beds.')
    ok('a steer goes as t3_thread_send in steer mode', a['ok'] and a.get('steered') and srv['calls'][-1][1:] == ('t3_thread_send', {'threadId': 'cli:run', 'message': 'Use loam for the front beds.', 'mode': 'steer'}), (a, srv['calls'][-1:]))
    srv['refuse'] = {'t3_thread_send'}
    a = helper_send('steer002', action='reply', mode='steer', thread='cli:run', message='And water them.')
    ok('a turn T3 will not steer: the reply goes as its next turn, through t3 thread send, and says so', a['ok'] and a.get('queued') is True
       and calls()[-1]['args'] == ['thread', 'send', 'cli:run', '-', '--json'] and calls()[-1]['stdin'] == 'And water them.', (a, calls()[-1]))
    srv['refuse'] = set()
    n = len([x for x in calls() if x['args'][:3] == ['auth', 'session', 'issue']])
    a = helper_send('queue001', action='reply', mode='queue', thread='cli:run', message='Then the paths.')
    ok('Queue goes through t3 thread send, with no key asked for', a['ok'] and calls()[-1]['args'][:3] == ['thread', 'send', 'cli:run'] and len([x for x in calls() if x['args'][:3] == ['auth', 'session', 'issue']]) == n)
    a = helper_send('bad00001', action='answer', thread='cli:ask', request='req-1', answers={'q1': ''})
    ok('an empty answer is refused, and nothing runs', a['ok'] is False and 'nothing T3 would take' in a['error'])
    a = helper_send('bad00002', action='reply', mode='shout', thread='cli:run', message='x')
    ok('a way to reply T3 does not know is refused', a['ok'] is False and 'a way T3 would not know' in a['error'])
    t3_open(alive=False)
    a = helper_send('down0001', action='answer', thread='cli:ask', request='req-1', answers={'q1': 'Sand'})
    ok('with T3 closed an answer says so, marked down', a['ok'] is False and a.get('down') is True)
    for f in (claude / 't3').iterdir(): f.unlink()

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
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t59')) { sessionStorage.setItem('nc-t59', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        op = ev("() => DB.projects.find(p => p.name !== 'Garden planner').id")
        ev(f"""() => {{ const p = getProject('{gp}'), o = getProject('{op}');
            p.links.push({{ id: 'l-g', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }});
            o.links.push({{ id: 'l-o', label: '', url: {json.dumps(str(other))}, icon: 'folder', shortcut: true }}); delete o.leader;
            const l = blankLeader({{ name: 'Fern Rowe', role: 'Head Gardener' }}); DB.leaders.push(l); setLeader(p, l.id); window.changed(p); window.changed(o); }}""")
        ev("() => { News._test.forget(); News.renderSection(); News._test.sayMs(600000); }")
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ev("() => Settings.close()"); pg.wait_for_timeout(200)
        now = int(time.time() * 1000)
        watch = {'app': 'nullovation-city', 'kind': 't3-watch', 'version': 1, 'at': now, 'running': True, 't3': '0.1.11', 'threads': [
            {'id': 'cli:ask', 'env': 'env-1234', 'title': 'Pick the soil', 'status': 'waiting', 'folder': str(garden), 'model': 'claude-opus-5-5', 'updated': now, 'created': now - 60000, 'background': 0,
             'last': {'text': 'Two soils fit; asking which.', 'more': False, 'at': now}, 'approval': False,
             'asks': [{'request': 'req-1', 'questions': [{'id': 'q1', 'header': 'Soil', 'question': 'Which soil should the beds use?',
                       'options': [{'label': 'Loam (Recommended)', 'description': 'Holds water well'}, {'label': 'Sand', 'description': 'Drains fast'}], 'multi': False, 'custom': True}]}]},
            {'id': 'cli:run', 'env': 'env-1234', 'title': 'Fix the roof', 'status': 'running', 'folder': str(other), 'model': 'claude-opus-5-5', 'updated': now, 'created': now - 60000, 'background': 0,
             'last': {'text': 'Laying the first tiles.', 'more': False, 'at': now}}]}
        def put(k, d): ev("([k, text]) => { window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }", [k, json.dumps(d)])
        put('t3/watch.json', watch)
        base = {'v': 1, 'app': 'nullovation-city', 'kind': 'claude-session', 'project': '', 'entry': 't3-code', 'at': now, 'since': now - 120000, 'started': now - 120000}
        put('s-ask.json', {**base, 'session': 's-ask', 'state': 'waiting', 'wait': 'question', 'cwd': str(garden), 'task': '', 'ask': 'Pick the soil'})
        put('s-run.json', {**base, 'session': 's-run', 'state': 'working', 'cwd': str(other), 'task': '', 'ask': 'Fix the roof'})
        ev("() => { T3.readWatch(); ClaudeWork.poll(); }"); pg.wait_for_timeout(1200)
        ev("() => { document.querySelectorAll('#ldSay, #gusSay, #pxSay').forEach(e => e.hidden = true); News.hide({ read: false }); }")
        sends = lambda: ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))")
        clear_sends = lambda: ev("() => { for (const k of [...window.__sub.keys()]) if (/^t3\\/send-/.test(k)) window.__sub.delete(k); }")
        def answer_back(extra):
            s = sends()[0]
            ev("([s, extra]) => { window.__sub.delete('t3/send-' + s.id + '.json'); window.__sub.set('t3/' + s.id + '.done.json', { text: JSON.stringify(Object.assign({ app: 'nullovation-city', kind: 't3-sent', version: 1, id: s.id }, extra)), t: Date.now() }); }", [s, extra])
            pg.wait_for_timeout(1400)
            return s

        # ---------- what Claude asks, on the status card ----------
        ev(f"() => MapView.select('{gp}', {{ glide: false }})"); pg.wait_for_timeout(400)
        q = ev("() => { const a = document.querySelector('#bubble .ld-ask'); return a ? { head: a.querySelector('.ld-q-head').textContent, text: a.querySelector('.ld-q-text').textContent,"
               " opts: [...a.querySelectorAll('.ld-q-opt')].map(b => ({ t: b.textContent, rec: b.classList.contains('rec'), hat: !!b.querySelector('.ld-q-rec svg'), title: b.title })) } : null; }")
        ok('Claude\'s question on the status card: its header, the question, its choices as buttons', q and q['head'] == 'Soil' and q['text'] == 'Which soil should the beds use?' and [o['t'] for o in q['opts']] == ['Loam', 'Sand'], q)
        ok('the one Claude recommends marked with the wizard\'s hat, its words in the tooltip', q['opts'][0]['rec'] and q['opts'][0]['hat'] and not q['opts'][1]['rec']
           and q['opts'][0]['title'] == 'Holds water well. Claude recommends it. One click answers.', q['opts'])
        ok('and a reply box that answers it', ev("() => document.querySelector('#ldReply-card').placeholder") == 'Answer Claude')
        pg.screenshot(path=str(SHOTS / '590-talk-question.png'))
        pg.click('#bubble .ld-q-opt.rec'); pg.wait_for_timeout(300)
        s = sends()
        ok('one click on Claude\'s pick answers: an answer send naming the thread, the request and the choice', len(s) == 1 and s[0]['action'] == 'answer' and s[0]['thread'] == 'cli:ask'
           and s[0]['request'] == 'req-1' and s[0]['answers'] == {'q1': 'Loam (Recommended)'}, s)
        ok('its link followed', ev("() => window.__opened.slice(-1)[0]") == 'nullovation-t3:send/' + s[0]['id'])
        ok('the card says it was answered, and waits for Claude', ev("() => (document.querySelector('#bubble .ld-asked') || {}).textContent") == 'Answered: Loam. Waiting for Claude.')
        answer_back({'ok': False, 'error': 'T3 did not take the answer: It broke.'})
        ok('an answer T3 did not take: said, and the choices come back', 'T3 did not take the answer' in ev("() => document.querySelector('#toast').textContent") and ev("() => !!document.querySelector('#bubble .ld-q-opt')"))
        clear_sends()
        # typed into the reply box: kept through a redraw, and it answers the question (R3)
        pg.click('#ldReply-card'); pg.keyboard.type('Loam, but sand by the')
        ev("() => Bubble.refresh()"); pg.wait_for_timeout(100)
        ok('what is typed survives the card drawn again, the focus and caret kept', ev("() => [document.activeElement.id, document.activeElement.value, document.activeElement.selectionStart]") == ['ldReply-card', 'Loam, but sand by the', 21])
        pg.keyboard.type(' path'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
        s = sends()
        ok('Enter while Claude asks answers its question with what was typed (R3)', len(s) == 1 and s[0]['action'] == 'answer' and s[0]['answers'] == {'q1': 'Loam, but sand by the path'}, s)
        answer_back({'ok': True, 'thread': 'cli:ask', 'env': 'env-1234', 'answered': True})
        ok('once T3 takes it, its leader says Claude was answered', 'Answered Claude on Pick the soil.' in ev("() => document.querySelector('#toast').textContent"))
        clear_sends()
        ev("() => MapView.deselect()"); pg.wait_for_timeout(200)

        # ---------- a running turn: Send steers, Queue waits for the next turn ----------
        ev(f"() => MapView.select('{op}', {{ glide: false }})"); pg.wait_for_timeout(400)
        ok('a running turn: the reply box steers it', ev("() => document.querySelector('#ldReply-card').placeholder") == 'Steer Claude' and not ev("() => !!document.querySelector('#bubble .ld-ask')"))
        ok('its line carries the thread\'s latest message', 'Laying the first tiles.' in ev("() => document.querySelector('#bubble .b-leader').textContent"))
        pg.click('#ldReply-card'); pg.keyboard.type('Use the red tiles.'); pg.click('#ldReplySend-card'); pg.wait_for_timeout(300)
        s = sends()
        ok('Send steers: a reply in steer mode, the box emptied', len(s) == 1 and s[0]['action'] == 'reply' and s[0]['mode'] == 'steer' and s[0]['message'] == 'Use the red tiles.' and s[0]['thread'] == 'cli:run'
           and ev("() => document.querySelector('#ldReply-card').value") == '', s)
        answer_back({'ok': True, 'thread': 'cli:run', 'env': 'env-1234', 'continued': True, 'queued': True})
        ok('a turn T3 would not steer: said, as Claude\'s next turn', 'T3 took it as Claude’s next turn on Fix the roof: the turn could not be steered.' in ev("() => document.querySelector('#toast').textContent"))
        clear_sends()
        pg.click('#ldReply-card'); pg.keyboard.type('Then the gutters.')
        pg.click('#ldReplyMore-card'); pg.wait_for_timeout(100)
        ok('Queue waits behind the more button (R2)', ev("() => document.querySelector('#ldReplyQueue-card .oc-folder-name').textContent") == 'Queue' and ev("() => document.activeElement.id") == 'ldReplyQueue-card')
        pg.screenshot(path=str(SHOTS / '591-talk-reply.png'))
        pg.click('#ldReplyQueue-card'); pg.wait_for_timeout(300)
        s = sends()
        ok('Queue sends it as the next turn', len(s) == 1 and s[0]['mode'] == 'queue' and s[0]['message'] == 'Then the gutters.', s)
        answer_back({'ok': True, 'thread': 'cli:run', 'env': 'env-1234', 'continued': True})
        ok('its leader says it was queued', 'Queued for Claude’s next turn on Fix the roof.' in ev("() => document.querySelector('#toast').textContent"))
        clear_sends()
        ev("() => MapView.deselect()"); pg.wait_for_timeout(200)

        # ---------- topics: arrows on the cards (i5's variant) ----------
        ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'a note, Bed layout' }})"); pg.wait_for_timeout(300)
        ev("() => { News.hide({ read: false }); }")
        ev(f"() => MapView.select('{gp}', {{ glide: false }})"); pg.wait_for_timeout(400)
        nav = ev("() => { const f = document.querySelector('#bubble .ld-flip'); return f ? f.querySelector('.ld-flip-n').textContent : ''; }")
        ok('two topics on a card: one shows, with arrows and where it is', nav == '1 of 2' and ev("() => document.querySelectorAll('#bubble .b-leader .ld-line').length") == 1, nav)
        first = ev("() => document.querySelector('#bubble .ld-line .ld-says').textContent")
        pg.click('#ldFlipNext-card'); pg.wait_for_timeout(150)
        ok('the arrow flips to the next, the focus kept on it', ev("() => document.querySelector('#bubble .ld-flip-n').textContent") == '2 of 2' and ev("() => document.activeElement.id") == 'ldFlipNext-card'
           and ev("() => document.querySelector('#bubble .ld-line .ld-says').textContent") != first)
        pg.screenshot(path=str(SHOTS / '592-talk-topics.png'))
        pg.click('#ldFlipNext-card'); pg.wait_for_timeout(150)
        ok('and round to the first', ev("() => document.querySelector('#bubble .ld-flip-n').textContent") == '1 of 2')
        ev("() => MapView.deselect()"); pg.wait_for_timeout(200)

        # ---------- the bubble: a leader's conversations as topics, flipped with arrows ----------
        ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'a link, Seed shop' }})"); pg.wait_for_timeout(300)
        ev("() => News.hide({ read: false })"); pg.wait_for_timeout(100)
        ev(f"() => News.openFace('ld:' + getProject('{gp}').leader)"); pg.wait_for_timeout(500)
        st = ev("() => News._test.bubble()")
        ok('a leader\'s bubble holds its news and its conversations, each a topic, the news first', st and len(st['ids']) >= 2 and any(i.startswith('conv:') for i in st['ids'])
           and not st['ids'][0].startswith('conv:'), st)
        ok('the arrows: the one before off at the first, "1 of N" between', ev("() => document.querySelector('#ldSayPrev').disabled") and ev("() => document.querySelector('#ldSayCount').textContent").startswith('1 of '))
        ev("() => News.hide({ read: false })"); pg.wait_for_timeout(200)
        # a leader at work opens its bubble on that conversation
        put('s-run.json', {**base, 'session': 's-run', 'state': 'working', 'cwd': str(garden), 'task': '', 'ask': 'Edge the beds'})
        watch['threads'][1]['folder'] = str(garden); watch['at'] = int(time.time() * 1000)
        put('t3/watch.json', watch)
        ev("() => { T3.readWatch(); ClaudeWork.poll(); }"); pg.wait_for_timeout(1200)
        ev("() => News.hide({ read: false })"); pg.wait_for_timeout(100)
        pg.click(f'#newsWork .news-work[data-pid="{gp}"] .news-work-face'); pg.wait_for_timeout(500)
        ok('a click on a leader at work opens its bubble on that conversation', 'working on Edge the beds' in ev("() => document.querySelector('#ldSayText').textContent")
           and ev("() => document.querySelector('#ldSay .ld-say-bld').textContent") == 'Garden planner', ev("() => document.querySelector('#ldSayText').textContent"))
        pg.screenshot(path=str(SHOTS / '593-talk-bubble.png'))
        b.close()
finally:
    httpd.shutdown()
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
