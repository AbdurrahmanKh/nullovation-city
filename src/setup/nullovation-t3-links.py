"""Nullovation City: tasks sent to T3 Code.

Lets the city's T3 tile, in Open in Claude's panel, start a T3 Code thread in a building's folder with the task already
sent, so the agent is at work at once (T3 Connection, Round 1, A1 and A1a). A web page cannot run a program on this
PC, so this teaches Windows one new kind of link, nullovation-t3:, and the small helper it runs. Run it once on this
PC: a double-click, when .py files open with Python. No admin rights needed; it only touches your own user account.

    double-click it                                         add the link type, then wait for Enter
    python nullovation-t3-links.py --install                the same; --no-pause skips the wait
    python nullovation-t3-links.py --uninstall              take the link type out again
    python nullovation-t3-links.py --status                 say what is set up on this PC

How a send works: the city writes the send into the Claude folder, as t3/send-<id>.json (the building's folder, the
task's copy, its title, the agent and the model), then follows a link that names only that file:
nullovation-t3:send/<id>. Windows runs this helper with the link; the helper takes the file, runs T3's own command,

    t3 thread start "<building's folder>" - --title "<task>" --provider <agent> --model <model> --json

with the task's copy on its input, and writes what T3 said back beside it, as t3/<id>.done.json: the new thread's id,
or why it could not start. The city reads that and says it was sent, with Open, which shows the thread in T3.
A building's folder that no T3 project holds yet is added to T3 as a project first (t3 project add).

Since Nullovation City 0.1.90 a task keeps the threads its sends started, and a send that names one of them goes on in
it rather than starting another:

    t3 thread send <thread> - --json

with the copy on its input: an idle thread starts on it at once, and a busy one gets it as its next turn.

Since 0.1.93 it also watches T3 (T3 Connection Research, Round 2, W2): a small program that starts when you sign in,
reads Claude's T3 threads every few seconds while T3 is open, through T3's own agent tools, and writes what it sees
into the Claude folder as t3/watch.json, which the city reads: each thread's state, its latest message, and what it
asks while it waits. It rests while T3 is closed. Its key is a read-only token it asks T3 for, kept in
%LOCALAPPDATA%\\Nullovation City, never in the Claude folder.

    python nullovation-t3-links.py watch                    run the watcher (the setup starts it, and Windows at sign-in)
    python nullovation-t3-links.py watch --once             one look, then stop

A link carries only a file's name, never a prompt, and only the city writes that folder, so no other web page can make
this PC run anything: a link naming a file that is not there does nothing, a send is taken once, and one older than
two minutes is refused. The helper never runs anything but T3's own command. T3 Code has to be running (its app
open, or its background service). The Claude folder is the one the Claude Code at work setup picked, read from
~/.claude/nullovation-city.json, else from the hooks in ~/.claude/settings.json, so that setup runs first.

Each run is noted in %LOCALAPPDATA%\\Nullovation City\\last-t3.txt (never the task's copy itself).
"""
import json, os, pathlib, re, shutil, subprocess, sys, time

APP = 'nullovation-city'
SCHEME = 'nullovation-t3'
KEY = r'Software\Classes' + '\\' + SCHEME          # under HKEY_CURRENT_USER
NAME = 'nullovation-t3-links.py'                 # the installed copy's name
HOOK_NAME = 'nullovation-city-status.py'          # the Claude Code at work hooks, which name the Claude folder
SUB = 't3'                                       # where sends and answers go, inside the Claude folder
MAX_AGE = 120                                    # seconds: a send older than this is refused
WAIT_FOR_FILE = 5.0                              # seconds the helper waits for the city's file to land
KEEP_DAYS = 1                                    # answers the city never read are cleared after this
LINK = re.compile(r'^' + SCHEME + r':(?://)?(send|test)/([A-Za-z0-9-]{8,64})/?$', re.I)
SLUG = re.compile(r'^[A-Za-z0-9._:-]{1,80}$')
NO_WINDOW = 0x08000000                           # CREATE_NO_WINDOW: T3's command runs with no console showing


def home():
    return pathlib.Path(os.path.expanduser('~'))


def local_dir():
    base = os.environ.get('LOCALAPPDATA') or str(home() / 'AppData' / 'Local')
    return pathlib.Path(base) / 'Nullovation City'


def installed_path():
    return local_dir() / NAME


def t3_home():
    return pathlib.Path(os.environ.get('T3CODE_HOME') or (home() / '.t3'))


def note(text):
    """One line on the last run, beside the installed helper, for when something did not work."""
    try:
        local_dir().mkdir(parents=True, exist_ok=True)
        (local_dir() / 'last-t3.txt').write_text(time.strftime('%Y-%m-%dT%H:%M:%S') + '\n' + text + '\n', encoding='utf-8')
    except Exception:
        pass


def say(text):
    """A small window, for what the city cannot say itself: a link it never wrote, or no Claude folder."""
    note(text)
    if os.environ.get('NULLOVATION_QUIET') or sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, 'Nullovation City', 0x30 | 0x40000)   # a warning, on top
    except Exception:
        pass


def load_json(path):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def claude_folder():
    """The Claude folder the city and the hooks share: ~/.claude/nullovation-city.json first, else the folder the
    Claude Code at work hooks write to, in ~/.claude/settings.json."""
    cfg = load_json(home() / '.claude' / 'nullovation-city.json')
    if cfg and isinstance(cfg.get('folder'), str) and cfg['folder'].strip():
        return pathlib.Path(cfg['folder'])
    settings = load_json(home() / '.claude' / 'settings.json') or {}
    for groups in (settings.get('hooks') or {}).values():
        for g in groups if isinstance(groups, list) else []:
            for h in (g.get('hooks') or []) if isinstance(g, dict) else []:
                args = [str(a) for a in (h.get('args') or [])] if isinstance(h, dict) else []
                if len(args) >= 4 and args[0].replace('\\', '/').endswith('/' + HOOK_NAME):
                    return pathlib.Path(args[3])
    return None


# ---------- T3's own command ----------

def t3_command():
    """How to run T3's t3 command, and with what in its environment. T3 writes t3.cmd, which runs its desktop app's
    bundled CLI; the helper runs that same program straight, with the same settings, rather than through cmd.exe, so
    a task's title is passed exactly as written, whatever it holds. Returns (argv, env), or None when T3 is not
    installed."""
    cmd = t3_home() / 'bin' / 't3.cmd'
    try:
        text = cmd.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None
    m = re.search(r'^\s*"([^"\r\n]+)"\s+"([^"\r\n]+)"\s+%\*', text, re.M)
    if not m:
        return None
    env = dict(os.environ)
    for k, v in re.findall(r'^\s*set\s+"([A-Za-z0-9_]+)=([^"\r\n]*)"', text, re.M | re.I):
        env[k] = v
    env.setdefault('T3CODE_HOME', str(t3_home()))
    return [m.group(1), m.group(2)], env


def run_t3(args, stdin=b'', timeout=180):
    """(exit code, what it printed, what it printed as errors); exit code None when it could not run at all."""
    found = t3_command()
    if not found:
        return None, '', 'not found'
    argv, env = found
    try:
        r = subprocess.run(argv + args, input=stdin, capture_output=True, env=env, timeout=timeout,
                           creationflags=NO_WINDOW if sys.platform == 'win32' else 0)
    except subprocess.TimeoutExpired:
        return None, '', 'timeout'
    except Exception as e:
        return None, '', 'could not run: ' + str(e)
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def plain_error(code, err, doing='start the thread'):
    """T3's error, said the way the city says things."""
    first = next((line.strip() for line in err.splitlines() if line.strip()), '')
    if code is None and err == 'not found':
        return "T3 Code's t3 command was not found on this PC. Open T3 Code once, so it writes it."
    if code is None and err == 'timeout':
        return 'T3 Code took too long to answer. Check it is open, then send again.'
    if 'No running T3 Code server' in err:
        return 'T3 Code is not running. Open it, then send again.'
    if 'Could not reach' in err or 'unreachable' in err.lower() or 'ECONNREFUSED' in err:
        return 'T3 Code did not answer. Check it is open, then send again.'
    return 'T3 could not ' + doing + ': ' + (first[:300] or 'it gave no reason.')


def failed(code, err, doing='start the thread'):
    """A failed answer; T3 not running is marked, so the city holds the send until T3 is open (0.1.91)."""
    out = {'ok': False, 'error': plain_error(code, err, doing)}
    if 'No running T3 Code server' in (err or ''):
        out['down'] = True
    return out


def environment_id():
    try:
        return (t3_home() / 'userdata' / 'environment-id').read_text(encoding='utf-8').strip()
    except Exception:
        return ''


# ---------- a send ----------

def write_answer(folder, ident, data):
    """t3/<id>.done.json, swapped in whole so the city never reads half of it."""
    out = folder / SUB / (ident + '.done.json')
    tmp = out.with_suffix('.tmp')
    tmp.write_text(json.dumps({'app': APP, 'kind': 't3-sent', 'version': 1, 'id': ident, 'at': int(time.time() * 1000), **data}), encoding='utf-8')
    os.replace(tmp, out)


def tidy(folder):
    """Answers the city never read, and sends nobody took, are cleared after a day."""
    try:
        for f in (folder / SUB).iterdir():
            if f.is_file() and f.suffix == '.json' and time.time() - f.stat().st_mtime > KEEP_DAYS * 86400:
                f.unlink()
    except Exception:
        pass


def read_send(d, ident):
    """The send as the city wrote it, checked; (send, None) or (None, why)."""
    if not d or d.get('app') != APP or d.get('kind') != 't3-send' or d.get('id') != ident:
        return None, 'The send is not one Nullovation City wrote.'
    at = d.get('at')
    if not isinstance(at, (int, float)) or abs(time.time() * 1000 - at) > MAX_AGE * 1000:
        return None, 'The send is too old to start: send it again from the city.'
    thread = d.get('thread') or ''
    if thread and not (isinstance(thread, str) and SLUG.match(thread)):
        return None, 'The send names a thread T3 would not know.'
    action = d.get('action') or 'send'
    if action not in ('send', 'reply', 'answer'):
        return None, 'The send asks for something the helper does not do.'
    if action != 'send' and not thread:
        return None, 'A reply names its thread.'
    if action == 'answer':
        request, answers = d.get('request'), d.get('answers')
        if not (isinstance(request, str) and SLUG.match(request)):
            return None, 'The answer names no question T3 would know.'
        ok_value = lambda v: (isinstance(v, str) and 0 < len(v) <= 20000) or (isinstance(v, list) and 0 < len(v) <= 20 and all(isinstance(x, str) and 0 < len(x) <= 2000 for x in v))
        if not isinstance(answers, dict) or not 0 < len(answers) <= 8 or not all(isinstance(k, str) and len(k) <= 200 and ok_value(v) for k, v in answers.items()):
            return None, 'The answer holds nothing T3 would take.'
        return {'folder': '', 'message': '', 'title': '', 'provider': '', 'model': '', 'thread': thread, 'action': 'answer', 'request': request, 'answers': answers, 'mode': ''}, None
    mode = d.get('mode') or 'auto'
    if action == 'reply' and mode not in ('auto', 'steer', 'queue'):
        return None, 'The reply names a way T3 would not know.'
    where = d.get('folder')
    if not thread and (not isinstance(where, str) or not os.path.isabs(where) or not os.path.isdir(where)):
        return None, 'The building\'s folder was not found on this PC: ' + str(where)
    message = d.get('message')
    if not isinstance(message, str) or not message.strip() or len(message) > 120000:
        return None, 'The send has no task in it.'
    provider, model = d.get('provider') or '', d.get('model') or ''
    if bool(provider) != bool(model) or (provider and not (SLUG.match(str(provider)) and SLUG.match(str(model)))):
        return None, 'The send names an agent T3 would not know.'
    title = re.sub(r'\s+', ' ', d.get('title') if isinstance(d.get('title'), str) else '').strip()[:80]
    return {'folder': where if isinstance(where, str) else '', 'message': message, 'title': title, 'provider': str(provider), 'model': str(model),
            'thread': thread, 'action': action, 'mode': mode if action == 'reply' else ''}, None


# ---------- a reply and an answer (0.1.94, City as My Terminal, Round 1, R1 to R3) ----------
# Steering a running turn and answering a question take T3's agent tools with write access, which the t3 command does
# not offer: the helper asks T3 for a key for one minute's work (t3 auth session issue, an MCP client's, read and
# operate), uses it once and revokes it, so no key that can write is ever kept. A reply to an idle thread, and Queue,
# go through t3 thread send, as a task's send does.

def operate(call):
    # Runs call(mcp) with a short key that can write, revoked after, whatever happens.
    rt = t3_server()
    if not rt:
        return {'ok': False, 'down': True, 'error': 'T3 Code is not running. Open it, then send again.'}
    code, out, err = run_t3(['auth', 'session', 'issue', '--subject', 'mcp-client', '--scope', 'orchestration:read', '--scope', 'orchestration:operate',
                             '--ttl', '5m', '--label', 'Nullovation City reply', '--json'], timeout=60)
    issued = {}
    try:
        issued = json.loads(out[out.find('{'):]) if code == 0 and '{' in out else {}
    except Exception:
        issued = {}
    if not issued.get('token'):
        return {'ok': False, 'error': plain_error(code, err, 'give the helper a key')}
    try:
        mcp = Mcp(rt['origin'], issued['token'])
        mcp.open()
        return call(mcp)
    finally:
        if issued.get('sessionId'):
            run_t3(['auth', 'session', 'revoke', str(issued['sessionId'])], timeout=60)


def steer(s):
    # A running turn steered; when T3 will not steer it, the reply goes as the next turn, and says so.
    def go(mcp):
        mcp.tool('t3_thread_send', {'threadId': s['thread'], 'message': s['message'], 'mode': 'steer'})
        return {'ok': True, 'thread': s['thread'], 'env': environment_id(), 'continued': True, 'steered': True}
    try:
        got = operate(go)
    except Exception as e:
        note('Steering ' + s['thread'] + ' failed, queued instead: ' + str(e)[:200])
        got = None
    if got and (got.get('ok') or got.get('down')):
        return got
    queued = send_to_thread(s)
    return {**queued, 'queued': True} if queued.get('ok') else queued


def answer_question(s):
    # A pending question answered, as T3's window would (t3_pending_request respond).
    def go(mcp):
        mcp.tool('t3_pending_request', {'action': 'respond', 'threadId': s['thread'], 'requestId': s['request'], 'answers': s['answers']})
        return {'ok': True, 'thread': s['thread'], 'env': environment_id(), 'answered': True}
    try:
        return operate(go)
    except Exception as e:
        return {'ok': False, 'error': 'T3 did not take the answer: ' + str(e)[:300]}


def send_to_thread(s):
    """Runs t3 thread send: the copy goes on in the task's thread, at once on an idle one, as its next turn on a busy
    one. Returns the answer, naming the same thread, so the city knows it went where it was meant to."""
    code, _, err = run_t3(['thread', 'send', s['thread'], '-', '--json'], s['message'].encode('utf-8'))
    if code != 0:
        return failed(code, err, 'send it to the thread')
    return {'ok': True, 'thread': s['thread'], 'env': environment_id(), 'continued': True}


def start_thread(s):
    """Runs t3 thread start; adds the folder to T3 as a project first when none holds it. Returns the answer."""
    args = ['thread', 'start', s['folder'], '-'] + (['--title', s['title']] if s['title'] else [])
    if s['provider']:
        args += ['--provider', s['provider'], '--model', s['model']]
    args.append('--json')
    stdin = s['message'].encode('utf-8')
    code, out, err = run_t3(args, stdin)
    added = False
    if code not in (None, 0) and 'No T3 Code project matches' in err:
        acode, _, aerr = run_t3(['project', 'add', s['folder']])
        if acode != 0:
            return failed(acode, aerr)
        added = True
        code, out, err = run_t3(args, stdin)
    if code != 0:
        return {**failed(code, err), **({'added': True} if added else {})}
    launched = None
    for line in reversed(out.strip().splitlines()):
        try:
            launched = json.loads(line)
            break
        except Exception:
            continue
    if not isinstance(launched, dict) or not launched.get('threadId'):
        return {'ok': False, 'error': 'T3 started something but gave no thread id back.'}
    return {'ok': True, 'thread': str(launched['threadId']), 'project': str(launched.get('projectId') or ''),
            'env': environment_id(), **({'added': True} if added else {})}


def open_link(link):
    m = LINK.match(str(link).strip())
    if not m:
        say('Nullovation City could not read this T3 link:\n\n' + str(link)[:200])
        return 1
    what, ident = m.group(1).lower(), m.group(2)
    folder = claude_folder()
    if not folder or not folder.is_dir():
        say('Nullovation City sends tasks to T3 through the Claude folder, and it was not found. Run the Claude Code at work setup first (Settings, Links).')
        return 1
    (folder / SUB).mkdir(exist_ok=True)
    tidy(folder)
    if what == 'test':
        code, _, err = run_t3(['thread', 'list', '--project', str(folder), '--json'], timeout=60)
        found = code is not None or err != 'not found'
        running = found and 'No running T3 Code server' not in err and code is not None
        write_answer(folder, ident, {'ok': True, 'test': True, 't3': found, 'running': running})
        note('Test: T3 found ' + str(found) + ', running ' + str(running))
        return 0
    send = folder / SUB / ('send-' + ident + '.json')
    waited = 0.0
    while not send.exists() and waited < WAIT_FOR_FILE:
        time.sleep(0.2)
        waited += 0.2
    taken = folder / SUB / (ident + '.running.json')
    try:
        os.replace(send, taken)                   # taken once: a second click on the same link finds nothing
    except Exception:
        say('Nullovation City sent nothing for this link, or it was sent already.')
        return 1
    d = load_json(taken)
    s, why = read_send(d, ident)
    if not s:
        write_answer(folder, ident, {'ok': False, 'error': why})
        note('Refused ' + ident + ': ' + why)
        try:
            taken.unlink()
        except Exception:
            pass
        return 1
    answer = (answer_question(s) if s['action'] == 'answer' else steer(s) if s['action'] == 'reply' and s['mode'] == 'steer'
              else send_to_thread(s) if s['thread'] else start_thread(s))
    write_answer(folder, ident, answer)
    try:
        taken.unlink()
    except Exception:
        pass
    note(('Sent ' if answer.get('ok') else 'Not sent ') + ident + (' to T3 thread ' + s['thread'] if s['thread'] else ' to T3 in ' + s['folder']) + ': '
         + (answer.get('thread') or answer.get('error') or ''))
    return 0 if answer.get('ok') else 1


# ---------- the watcher (0.1.93, T3 Connection Research, Round 2, W2) ----------
# A small program that starts when you sign in (W2a), reads T3 every few seconds while T3 is open through its
# documented agent tools, and writes what it sees into the Claude folder as t3/watch.json, which the city reads as it
# reads Claude's hooks. Claude's threads only, until production (W2b). It rests while T3 is closed, and writes nothing
# but that file. Its key is a read-only token it gets from T3 for itself (t3 auth session issue, an MCP client's), kept
# beside the installed helper in your AppData, never in the Claude folder, which a web page can read.

WATCH_FILE = 'watch.json'                     # in the Claude folder's t3
WATCH_EVERY = 3.0                             # seconds between looks while T3 is open
REST_EVERY = 10.0                             # and while it is closed
BEAT = 30.0                                   # an unchanged file is written again this often, so the city knows the watcher is there
RECENT_MS = 24 * 3600 * 1000                  # a thread shows while it works or waits, or was busy this recently
MAX_THREADS = 40
LAST_MAX = 1500                               # characters of a thread's latest message
TOKEN_TTL = '30d'
TOKEN_LABEL = 'Nullovation City watcher'
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
RUN_NAME = 'Nullovation City T3 watcher'
ACTIVE = {'preparing', 'queued', 'starting', 'running', 'waiting'}


def token_path():
    return local_dir() / 't3-watch-token.json'


def watch_log(text):
    try:
        local_dir().mkdir(parents=True, exist_ok=True)
        (local_dir() / 'last-t3-watch.txt').write_text(time.strftime('%Y-%m-%dT%H:%M:%S') + '\n' + text + '\n', encoding='utf-8')
    except Exception:
        pass


def pid_alive(pid):
    """Whether a process still runs: T3's own runtime file can outlive T3."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if sys.platform != 'win32':
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False
    import ctypes
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, pid)                  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(k.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259   # STILL_ACTIVE
    finally:
        k.CloseHandle(h)


def t3_server():
    """T3's server while it runs: its address and version, from its own runtime file; None while it is closed."""
    rt = load_json(t3_home() / 'userdata' / 'server-runtime.json')
    if not rt or not isinstance(rt.get('origin'), str) or not rt['origin'].startswith('http://127.0.0.1:'):
        return None
    return rt if pid_alive(rt.get('pid')) else None


def watch_token(force=False):
    """The watcher's read-only key: kept until 2 days before it runs out, a new one asked of T3 otherwise, the old
    one revoked."""
    kept = load_json(token_path()) or {}
    if not force and kept.get('token') and isinstance(kept.get('expiresAt'), str):
        try:
            left = time.mktime(time.strptime(kept['expiresAt'][:19], '%Y-%m-%dT%H:%M:%S')) - time.mktime(time.gmtime())
            if left > 2 * 86400:
                return kept['token']
        except Exception:
            pass
    code, out, err = run_t3(['auth', 'session', 'issue', '--subject', 'mcp-client', '--scope', 'orchestration:read',
                             '--ttl', TOKEN_TTL, '--label', TOKEN_LABEL, '--json'], timeout=60)
    if code != 0:
        raise RuntimeError('T3 gave no key: ' + (err.strip().splitlines() or ['no reason'])[0][:200])
    issued = json.loads(out[out.find('{'):]) if '{' in out else {}
    if not issued.get('token'):
        raise RuntimeError('T3 gave no key back.')
    if kept.get('sessionId') and kept.get('sessionId') != issued.get('sessionId'):
        run_t3(['auth', 'session', 'revoke', str(kept['sessionId'])], timeout=60)
    local_dir().mkdir(parents=True, exist_ok=True)
    token_path().write_text(json.dumps({'sessionId': issued.get('sessionId'), 'token': issued['token'], 'expiresAt': issued.get('expiresAt')}), encoding='utf-8')
    return issued['token']


class Mcp:
    """T3's agent tools at /mcp, as an outside MCP client: no Origin header, the bearer key, one MCP session."""

    def __init__(self, origin, token):
        self.url, self.token, self.sid, self.n = origin.rstrip('/') + '/mcp', token, None, 0

    def post(self, body):
        import urllib.request
        req = urllib.request.Request(self.url, data=json.dumps(body).encode('utf-8'), method='POST', headers={
            'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
            **({'Mcp-Session-Id': self.sid} if self.sid else {})})
        with urllib.request.urlopen(req, timeout=30) as r:
            self.sid = r.headers.get('Mcp-Session-Id') or self.sid
            raw, kind = r.read().decode('utf-8', 'replace'), r.headers.get('Content-Type', '')
        if 'event-stream' in kind:
            datas = [line[5:].strip() for line in raw.splitlines() if line.startswith('data:')]
            raw = datas[-1] if datas else ''
        return json.loads(raw) if raw.strip() else None

    def rpc(self, method, params=None):
        self.n += 1
        got = self.post({'jsonrpc': '2.0', 'id': self.n, 'method': method, **({'params': params} if params is not None else {})})
        if not got or 'error' in got:
            raise RuntimeError('T3 refused ' + method + ': ' + json.dumps((got or {}).get('error'))[:200])
        return got['result']

    def open(self):
        self.sid = None
        self.rpc('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'nullovation-city-watcher', 'version': '1'}})
        self.post({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

    def tool(self, name, args):
        r = self.rpc('tools/call', {'name': name, 'arguments': args})
        text = ''.join(c.get('text', '') for c in r.get('content') or [] if isinstance(c, dict))
        try:
            data = json.loads(text)
        except Exception:
            data = text
        if r.get('isError'):
            raise RuntimeError(name + ': ' + (data.get('message') if isinstance(data, dict) else str(data))[:200])
        return data


def iso_ms(s):
    """An ISO time as milliseconds, or 0."""
    try:
        import datetime
        return int(datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp() * 1000)
    except Exception:
        return 0


class Watcher:
    def __init__(self, folder):
        self.folder, self.mcp, self.roots, self.rooted, self.last, self.wrote, self.beat = folder, None, {}, 0, {}, '', 0.0

    def connect(self, rt):
        self.mcp = Mcp(rt['origin'], watch_token())
        try:
            self.mcp.open()
        except Exception as e:
            if '401' not in str(e):
                raise
            self.mcp = Mcp(rt['origin'], watch_token(force=True))   # a key T3 no longer knows: a new one
            self.mcp.open()

    def projects(self):
        """Each T3 project's folder, refreshed each minute, or at once for a project not seen yet."""
        if time.time() - self.rooted > 60:
            got = self.mcp.tool('t3_project_list', {})
            items = got.get('projects', []) if isinstance(got, dict) else got if isinstance(got, list) else []
            self.roots = {p.get('id'): p.get('workspaceRoot') or '' for p in items if isinstance(p, dict)}
            self.rooted = time.time()
        return self.roots

    def latest(self, t):
        """A thread's latest message, read again only when the thread changed."""
        tid, stamp = t['threadId'], str(t.get('updatedAt')) + ':' + str(t.get('itemCount'))
        had = self.last.get(tid)
        if had and had[0] == stamp:
            return had[1]
        n = t.get('itemCount') if isinstance(t.get('itemCount'), int) else 0
        got = self.mcp.tool('t3_thread_read', {'threadId': tid, 'view': 'messages', 'limit': 4, 'maxCharsPerItem': LAST_MAX,
                                               **({'beforePosition': n + 1} if n else {})})
        items = got.get('items', []) if isinstance(got, dict) else []
        mine = [i for i in items if isinstance(i, dict) and i.get('type') == 'assistant_message' and str(i.get('text') or '').strip()]
        last = None
        if mine:
            i = mine[-1]
            last = {'text': str(i['text'])[:LAST_MAX], 'more': bool(i.get('textTruncated')), 'at': iso_ms(i.get('updatedAt'))}
        self.last[tid] = (stamp, last)
        return last

    def asks(self, tid):
        """What a waiting thread asks: its questions with their choices; none listed means an approval, which T3's
        tools leave out."""
        got = self.mcp.tool('t3_pending_request', {'action': 'list', 'threadId': tid})
        out = []
        for rid in (got.get('requestIds') if isinstance(got, dict) else [])[:3]:
            q = self.mcp.tool('t3_pending_request', {'action': 'read', 'threadId': tid, 'requestId': rid})
            qs = q.get('questions', []) if isinstance(q, dict) else []
            out.append({'request': rid, 'questions': [{'id': x.get('id'), 'header': x.get('header', ''), 'question': x.get('question', ''),
                'options': [{'label': o.get('label', ''), 'description': o.get('description', '')} for o in x.get('options') or [] if isinstance(o, dict)],
                'multi': bool(x.get('multiSelect')), 'custom': x.get('allowCustomAnswer') is not False} for x in qs if isinstance(x, dict)]})
        return out

    def snapshot(self, rt):
        got = self.mcp.tool('t3_thread_list', {'allProjects': True, 'limit': 100})
        now = int(time.time() * 1000)
        threads = [t for t in (got.get('threads', []) if isinstance(got, dict) else []) if isinstance(t, dict) and t.get('threadId')
                   and str(t.get('providerInstanceId') or '').startswith('claude')]                 # Claude only (W2b)
        keep = [t for t in threads if t.get('status') in ACTIVE or now - iso_ms(t.get('updatedAt')) < RECENT_MS]
        keep.sort(key=lambda t: iso_ms(t.get('updatedAt')), reverse=True)
        roots, env, out = self.projects(), environment_id(), []
        for t in keep[:MAX_THREADS]:
            if t.get('projectId') not in roots:
                self.rooted = 0
                roots = self.projects()
            status = str(t.get('status') or 'idle')
            row = {'id': t['threadId'], 'env': env, 'title': str(t.get('title') or '')[:200], 'status': status, 'folder': roots.get(t.get('projectId'), ''),
                   'model': str(t.get('model') or ''), 'updated': iso_ms(t.get('updatedAt')), 'created': iso_ms(t.get('createdAt')),
                   'background': len(t.get('pendingBackgroundTasks') or [])}
            try:
                row['last'] = self.latest(t)
                if status == 'waiting':
                    row['asks'] = self.asks(t['threadId'])
                    row['approval'] = not row['asks']
            except Exception as e:
                watch_log('Reading ' + t['threadId'] + ': ' + str(e))
            out.append(row)
        alive = {r['id'] for r in out}
        for k in [k for k in self.last if k not in alive]:
            del self.last[k]
        return {'running': True, 't3': str(rt.get('serverVersion') or ''), 'threads': out}

    def write(self, data):
        """t3/watch.json, swapped in whole; an unchanged look is written again only every BEAT seconds."""
        body = json.dumps(data, sort_keys=True)
        if body == self.wrote and time.time() - self.beat < BEAT:
            return
        self.wrote, self.beat = body, time.time()
        out = self.folder / SUB / WATCH_FILE
        tmp = out.with_suffix('.tmp')
        tmp.write_text(json.dumps({'app': APP, 'kind': 't3-watch', 'version': 1, 'at': int(time.time() * 1000), **data}), encoding='utf-8')
        os.replace(tmp, out)

    def look(self):
        """One look: T3's threads while it is open, else that it is closed. Returns the seconds until the next."""
        rt = t3_server()
        if not rt:
            self.mcp = None
            self.write({'running': False, 'threads': []})
            return REST_EVERY
        try:
            if not self.mcp:
                self.connect(rt)
            self.write(self.snapshot(rt))
        except Exception as e:
            self.mcp = None                       # T3 restarted, or a key it no longer takes: connect again next time
            watch_log('A look failed: ' + str(e))
            self.write({'running': True, 'error': str(e)[:200], 't3': str(rt.get('serverVersion') or ''), 'threads': []})
        return WATCH_EVERY


def watch(once=False):
    """The watcher's loop. One runs at a time; a newer installed helper takes over from an older one running."""
    folder = claude_folder()
    if not folder or not folder.is_dir():
        watch_log('No Claude folder: run the Claude Code at work setup first.')
        return 1
    (folder / SUB).mkdir(exist_ok=True)
    lock = None
    if not once:
        local_dir().mkdir(parents=True, exist_ok=True)
        lock = open(local_dir() / 't3-watch.lock', 'a+')
        try:
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return 0                              # one is running already
    w, me = Watcher(folder), pathlib.Path(__file__)
    born = me.stat().st_mtime
    stop = local_dir() / 't3-watch.stop'
    while True:
        wait = w.look()
        if once:
            return 0
        if stop.exists():
            try:
                stop.unlink()
            except Exception:
                pass
            return 0
        try:
            if me.stat().st_mtime != born:        # the setup installed a newer helper: it carries on
                lock.close()
                subprocess.Popen([pythonw(), str(me), 'watch'], creationflags=0x00000008 if sys.platform == 'win32' else 0, close_fds=True)
                return 0
        except Exception:
            pass
        time.sleep(wait)


def watcher_running():
    """Whether a watcher holds its lock now."""
    p = local_dir() / 't3-watch.lock'
    if not p.exists():
        return False
    try:
        with open(p, 'a+') as f:
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except OSError:
        return True


def run_at_signin(write, command=''):
    """HKCU's Run list: the watcher starts with Windows (W2a). Linux would use a systemd user service or an
    autostart entry instead; not set up yet."""
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
        if write:
            winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(k, RUN_NAME)
            except OSError:
                pass


def start_watcher(script):
    subprocess.Popen([pythonw(), str(script), 'watch'], creationflags=0x00000008, close_fds=True)   # DETACHED_PROCESS: no window, not tied to the setup's


# ---------- the link type ----------

def pythonw():
    """Python with no console window, beside the Python that runs this."""
    w = pathlib.Path(sys.executable).with_name('pythonw.exe')
    return str(w if w.exists() else sys.executable)


def link_command(script):
    return '"{}" "{}" open "%1"'.format(pythonw(), script)


def registry(write, command=''):
    """HKCU\\Software\\Classes\\nullovation-t3: added with its command, or taken out."""
    import winreg
    root = KEY
    if not write:
        for sub in (r'\shell\open\command', r'\shell\open', r'\shell', ''):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, root + sub)
            except OSError:
                pass
        return
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, root) as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, 'URL:Nullovation City T3 link')
        winreg.SetValueEx(k, 'URL Protocol', 0, winreg.REG_SZ, '')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, root + r'\shell\open\command') as k:
        winreg.SetValueEx(k, '', 0, winreg.REG_SZ, command)


def registered():
    if sys.platform != 'win32':
        return ''
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY + r'\shell\open\command') as k:
            return winreg.QueryValueEx(k, '')[0]
    except OSError:
        return ''


README = """This folder is how Nullovation City sends tasks to T3 Code, and sees T3's threads.

The city writes a send here as send-<id>.json, then follows a nullovation-t3: link that names it. The helper the
T3 setup added takes it, starts a T3 thread in the building's folder with the task sent, and writes what T3 said
back as <id>.done.json, which the city reads and clears.

The watcher the setup started writes watch.json here every few seconds while T3 is open: Claude's T3 threads, each
with its state, its latest message and what it asks while it waits. Nothing here needs keeping.
"""


def install(dry_run=False):
    if sys.platform != 'win32' and not dry_run:
        print('This setup is for Windows: the link type lives in your Windows user settings.')
        return 1
    folder = claude_folder()
    if not folder:
        print('The Claude folder was not found. Run the Claude Code at work setup first (Settings, Links, Get the setup),')
        print('then run this one: T3\'s sends go through the same folder.')
        return 1
    target = installed_path()
    command = link_command(target)
    watcher = '"{}" "{}" watch'.format(pythonw(), target)
    if dry_run:
        print('Would copy this script to ' + str(target))
        print('Would add HKEY_CURRENT_USER\\Software\\Classes\\' + SCHEME + ' with the command:')
        print('  ' + command)
        print('Would start the T3 watcher now, and at every sign-in (HKEY_CURRENT_USER\\' + RUN_KEY + ', ' + RUN_NAME + '):')
        print('  ' + watcher)
        print('Sends go through ' + str(folder / SUB))
        return 0
    local_dir().mkdir(parents=True, exist_ok=True)
    if pathlib.Path(__file__).resolve() != target.resolve():
        shutil.copyfile(__file__, target)
    registry(True, command)
    try:
        (folder / SUB).mkdir(parents=True, exist_ok=True)
        (folder / SUB / 'README-nullovation-t3.txt').write_text(README, encoding='utf-8')
    except Exception:
        pass
    print('Added the nullovation-t3: link type for this Windows user.')
    print('Sends go through ' + str(folder / SUB) + '.')
    run_at_signin(True, watcher)
    if not watcher_running():
        start_watcher(target)
    print('The T3 watcher runs now, and starts whenever you sign in: it reads Claude\'s T3 threads while T3 is open.')
    if not t3_command():
        print('T3 Code\'s t3 command was not found yet (' + str(t3_home() / 'bin' / 't3.cmd') + '). Open T3 Code once, and it writes it.')
    print('The first time the city sends a task, your browser asks to open Python: that is this helper. Allow it.')
    print('Done. In Nullovation City, open Settings, Links, and press Test T3 link.')
    return 0


def uninstall(dry_run=False):
    if dry_run:
        print('Would take out HKEY_CURRENT_USER\\Software\\Classes\\' + SCHEME + ' and ' + str(installed_path()))
        return 0
    if sys.platform == 'win32':
        registry(False)
        run_at_signin(False)
    try:
        local_dir().mkdir(parents=True, exist_ok=True)
        (local_dir() / 't3-watch.stop').write_text('stop', encoding='utf-8')   # the watcher running stops at its next look
    except Exception:
        pass
    kept = load_json(token_path()) or {}
    if kept.get('sessionId'):
        run_t3(['auth', 'session', 'revoke', str(kept['sessionId'])], timeout=60)
    for f in (token_path(), installed_path()):
        try:
            f.unlink()
        except Exception:
            pass
    print('Removed. The city\'s T3 tile does nothing on this PC, and the watcher stops, until the setup runs again.')
    return 0


def status():
    folder = claude_folder()
    found = t3_command()
    print('Link type: ' + (registered() or 'not added'))
    print('Claude folder: ' + (str(folder) if folder else 'not found (run the Claude Code at work setup first)'))
    print('T3\'s command: ' + (found[0][0] if found else 'not found (open T3 Code once)'))
    print('T3 watcher: ' + ('running' if watcher_running() else 'not running') + ('; T3 is open' if t3_server() else '; T3 is closed'))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[0] == 'open':
        return open_link(argv[1])
    if argv[:1] == ['watch']:
        return watch(once='--once' in argv)
    if '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0
    dry = '--dry-run' in argv
    if '--uninstall' in argv:
        code = uninstall(dry)
    elif '--status' in argv:
        code = status()
    else:
        try:
            code = install(dry)
        except Exception as e:
            print('The setup did not finish: ' + str(e))
            code = 1
    if not any(a in argv for a in ('--no-pause', '--dry-run', '--status')):
        try:
            input('Press Enter to close')
        except (EOFError, KeyboardInterrupt):
            pass
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
