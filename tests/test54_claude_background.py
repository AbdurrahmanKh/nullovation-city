"""Pass 54: Claude Code at work keeps working while a command it started runs on in the background (0.1.88).

A long command, such as the full test run, goes to the background: Claude's reply ends while it runs, and Claude
comes back in a turn of its own once it reports. Until 0.1.87 the reply's Stop said done, so the city said Claude had
handed the task back while the tests still ran. Part one runs the hook script as Claude Code would, in a home folder
made for the test, on transcripts written here the way Claude Code writes them: a reply ending with a command still
out is background, until the command reports (as a turn of its own, queued while Claude was busy, or in the queue's
own record), is stopped, or runs out of time. Part two opens the city with a Claude folder held in memory and checks
that background shows as working, past working's 20 quiet minutes, and as finished once its time is up."""
import datetime, json, os, pathlib, shutil, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, DATA, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

SCRIPT = ROOT / 'src' / 'setup' / 'nullovation-claude-status.py'
SETUP = SCRIPT.read_text(encoding='utf-8')

# ---------- part one: the hook, on transcripts ----------
home = pathlib.Path(tempfile.mkdtemp(prefix='nc-bg-', dir=str(DATA)))
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONUTF8='1')
env.pop('CLAUDE_CODE_ENTRYPOINT', None)
def run(*args, stdin=''):
    return subprocess.run([sys.executable, *map(str, args)], input=stdin.encode('utf-8'), env=env, capture_output=True, timeout=60)
(home / '.claude').mkdir(parents=True)
r = run(SCRIPT, '--install', '--folder', home / 'Claude')
folder = (home / 'Claude').resolve()
installed = home / '.claude' / 'hooks' / 'nullovation-city-status.py'
ok(f'the setup installs ({r.returncode})', r.returncode == 0 and installed.exists())

now_ms = lambda: int(time.time() * 1000)
iso = lambda ms: datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
MIN = 60000

class Transcript:
    """A session's transcript, one JSON line per entry, as Claude Code writes it."""
    def __init__(self, name):
        self.path, self.lines, self.n = home / (name + '.jsonl'), [], 0
        self.path.write_text('', encoding='utf-8')
    def add(self, e, ago=0):
        e = {'parentUuid': None, 'isSidechain': False, 'timestamp': iso(now_ms() - ago * MIN), 'sessionId': 'x', **e}
        self.lines.append(json.dumps(e, separators=(',', ':')))
        self.path.write_text('\n'.join(self.lines) + '\n', encoding='utf-8')
    def use(self, name, inp, ago=0, side=False):
        self.n += 1; uid = 'toolu_%03d' % self.n
        self.add({'type': 'assistant', 'isSidechain': side, 'message': {'role': 'assistant', 'content': [{'type': 'tool_use', 'id': uid, 'name': name, 'input': inp}]}}, ago)
        return uid
    def result(self, uid, text, res, ago=0, error=False, side=False):
        self.add({'type': 'user', 'isSidechain': side, 'message': {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': uid, 'content': text, 'is_error': error}]}, 'toolUseResult': res}, ago)
    def bg(self, task, ago=0, timeout=None, tool='Bash', error=False, side=False):
        inp = {'command': 'python tests/run_tests.py', 'description': 'Run every test pass', 'run_in_background': True}
        if timeout is not None: inp['timeout'] = timeout
        uid = self.use(tool, inp, ago, side)
        if error: self.result(uid, 'Permission to use Bash was denied.', 'Error: denied', ago, error=True, side=side)
        else: self.result(uid, f'Command running in background with ID: {task}. Output is being written to: C:\\Temp\\{task}.output',
                          {'stdout': '', 'stderr': '', 'interrupted': False, 'isImage': False, 'backgroundTaskId': task}, ago, side=side)
        return uid
    def monitor(self, task, ago=0, timeout_ms=1800000, persistent=False):
        uid = self.use('Monitor', {'description': 'test passes finishing', 'timeout_ms': timeout_ms, 'command': 'tail -f log'}, ago)
        self.result(uid, f'Monitor started (task {task}, expires in 30m unless the source ends first).', {'taskId': task, 'timeoutMs': timeout_ms, 'persistent': persistent}, ago)
    @staticmethod
    def notice_text(task, status='completed'):
        st = f'<tool-use-id>toolu_x</tool-use-id>\n<output-file>C:\\Temp\\{task}.output</output-file>\n<status>{status}</status>\n' if status else ''
        return f'<task-notification>\n<task-id>{task}</task-id>\n{st}<summary>Background command "Run every test pass" {status or "event"}</summary>\n</task-notification>'
    def notice(self, task, status='completed', how='turn'):
        text = self.notice_text(task, status)
        if how == 'turn': self.add({'type': 'user', 'message': {'role': 'user', 'content': text}, 'origin': {'kind': 'task-notification', 'producer': 'session-task'}})
        elif how == 'queued': self.add({'type': 'attachment', 'attachment': {'type': 'queued_command', 'prompt': text, 'commandMode': 'task-notification'}})
        elif how == 'queue': self.add({'type': 'queue-operation', 'operation': 'enqueue', 'content': text})
        return text
    def quote(self, text):                            # a tool's output that quotes something, as a cat of a log would
        uid = self.use('Bash', {'command': 'cat notes.txt'})
        self.result(uid, text, {'stdout': text, 'stderr': '', 'interrupted': False, 'isImage': False})
    def reply(self, text):
        self.add({'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': text}], 'stop_reason': 'end_turn'}})

def hook(state, event, session='s-1', tr=None):
    ev = {'session_id': session, 'cwd': 'C:\\Users\\me\\garden', 'transcript_path': str(tr.path) if tr else '', **event}
    return run(installed, 'hook', state, folder, stdin=json.dumps(ev))
def sess(session='s-1'):
    return json.loads((folder / (session + '.json')).read_text(encoding='utf-8'))
def stop(session, tr, reply='The full run is going; I will report when it is done.'):
    hook('done', {'hook_event_name': 'Stop', 'stop_hook_active': False, 'last_assistant_message': reply}, session, tr)
    return sess(session)
near = lambda a, b, slack=5000: isinstance(a, (int, float)) and abs(a - b) <= slack

# the whole story: a prompt, a command sent to the background, the reply ending, the command reporting, the finish
tr = Transcript('s-1')
prompt = '# Task: Water the beds on time\nProject: Garden planner\nMilestone: Launch\n\n## Description\nThe reminders.'
hook('working', {'hook_event_name': 'UserPromptSubmit', 'prompt': prompt}, tr=tr)
since0 = sess()['since']; time.sleep(0.02)
t0 = now_ms(); tr.bg('bash1', timeout=60 * MIN)
hook('working', {'hook_event_name': 'PostToolUse', 'tool_name': 'Bash'}, tr=tr)
tr.reply('The full run is going; I will report when it is done.')
d = stop('s-1', tr)
ok(f'a reply that ends with a command still running in the background is background, not done ({d["state"]})', d['state'] == 'background', d)
ok('its until is when the command runs out of time: its own timeout, and 2 minutes more', near(d.get('until'), t0 + 62 * MIN), d.get('until'))
ok('it keeps the start of the reply, and the stretch of work its start time', d.get('reply', '').startswith('The full run is going') and d['since'] == since0)
r = hook('idle', {'hook_event_name': 'Notification', 'message': 'Claude is waiting for your input'}, tr=tr)
ok('the idle notice a minute later leaves it background, with its until', sess()['state'] == 'background' and near(sess().get('until'), t0 + 62 * MIN) and r.stdout == b'')
hook('start', {'hook_event_name': 'SessionStart', 'source': 'compact'}, tr=tr)
ok('and so does the session starting again after a compact', sess()['state'] == 'background')
text = tr.notice('bash1')
hook('working', {'hook_event_name': 'UserPromptSubmit', 'prompt': text}, tr=tr)
d = sess()
ok('the command reporting starts a turn: working again, one stretch with the same start, the ask and the task kept',
   d['state'] == 'working' and d['since'] == since0 and d['task'] == 'Water the beds on time' and d['ask'] == '# Task: Water the beds on time' and 'until' not in d, d)
tr.reply('All 50 passes are green.')
d = stop('s-1', tr, 'All 50 passes are green.')
ok(f'and that turn\'s reply, with nothing left out, is done ({d["state"]})', d['state'] == 'done' and d['reply'] == 'All 50 passes are green.' and 'until' not in d, d)

def case(name, build, reply='Running.'):
    t = Transcript(name)
    hook('working', {'hook_event_name': 'UserPromptSubmit', 'prompt': 'go'}, name, t)
    build(t)
    t.reply(reply)
    case.t = t
    return stop(name, t, reply)
t0 = now_ms(); d = case('s-2', lambda t: t.bg('b2'))
ok('a command given no timeout runs out after Claude Code\'s own 30 minutes, and 2 more', d['state'] == 'background' and near(d.get('until'), t0 + 32 * MIN), d)
t0 = now_ms(); d = case('s-3', lambda t: t.bg('b3', timeout=5 * 60 * MIN))
ok('one longer than 2 hours is held to 2 hours, Claude Code\'s most', d['state'] == 'background' and near(d.get('until'), t0 + 122 * MIN), d)
d = case('s-4', lambda t: t.bg('b4', ago=180, timeout=60 * MIN))
ok('one whose time ran out long ago (its session died without a word) is done', d['state'] == 'done', d)
t0 = now_ms(); d = case('s-5', lambda t: t.bg('b5', tool='PowerShell', timeout=10 * MIN))
ok('a PowerShell command in the background counts too', d['state'] == 'background' and near(d.get('until'), t0 + 12 * MIN), d)
d = case('s-6', lambda t: (t.bg('b6'), t.notice('b6', how='queued')))
ok('a report queued while Claude was still busy ends it: done', d['state'] == 'done', d)
d = case('s-7', lambda t: (t.bg('b7'), t.notice('b7', how='queue')))
ok('and so does one only in the queue\'s own record, not yet delivered', d['state'] == 'done', d)
d = case('s-8', lambda t: (t.bg('b8'), t.notice('b8', status='failed')))
d9 = case('s-9', lambda t: (t.bg('b9'), t.notice('b9', status='killed')))
ok('a command that failed or was killed has ended', d['state'] == 'done' and d9['state'] == 'done', (d, d9))
d = case('s-10', lambda t: (t.bg('b10'), t.use('TaskStop', {'task_id': 'b10'})))
ok('Claude stopping it with TaskStop ends it', d['state'] == 'done', d)
d = case('s-11', lambda t: (t.bg('b11'), t.quote('From the log:\n' + Transcript.notice_text('b11'))))
ok('a tool\'s output quoting its report does not end it', d['state'] == 'background', d)
d = case('s-12', lambda t: t.quote('Earlier: Command running in background with ID: q12. Output is being written to: x'))
ok('nor does a tool\'s output quoting a start begin one: done', d['state'] == 'done', d)
d = case('s-13', lambda t: t.bg('b13', error=True))
ok('a background command refused (an error) never ran: done', d['state'] == 'done', d)
d = case('s-14', lambda t: t.bg('b14', side=True))
ok('one a subagent started, in its own side chain, is the subagent\'s: done', d['state'] == 'done', d)
t0 = now_ms(); d = case('s-15', lambda t: (t.monitor('m15', timeout_ms=45 * MIN), t.notice('m15', status=''), t.notice('m15', status='', how='queued')))
ok('a Monitor counts, its events (no status) ending nothing, by its own timeout', d['state'] == 'background' and near(d.get('until'), t0 + 47 * MIN), d)
d = case('s-16', lambda t: (t.monitor('m16'), t.notice('m16', status='completed')))
ok('and its last report (a status) ends it', d['state'] == 'done', d)
t0 = now_ms(); d = case('s-17', lambda t: t.monitor('m17', persistent=True))
ok('a Monitor kept on persistently holds for 2 hours at most', d['state'] == 'background' and near(d.get('until'), t0 + 122 * MIN), d)
t0 = now_ms(); d = case('s-18', lambda t: (t.bg('b18a', timeout=10 * MIN), t.bg('b18b', timeout=40 * MIN)))
ok('with two out, its until is the later', d['state'] == 'background' and near(d.get('until'), t0 + 42 * MIN), d)
t18 = case.t
t18.notice('b18b'); t18.reply('One left.')
d = stop('s-18', t18, 'One left.')
ok('one reporting leaves the other: still background, until the one left runs out', d['state'] == 'background' and near(d.get('until'), t0 + 12 * MIN), d)
t18.notice('b18a'); d = stop('s-18', t18, 'Both done.')
ok('and with both reported, done', d['state'] == 'done', d)
d = case('s-19', lambda t: None)
ok('a reply with nothing in the background is done, as before', d['state'] == 'done', d)
hook('working', {'hook_event_name': 'UserPromptSubmit', 'prompt': 'go'}, 's-20')
d = stop('s-20', None)
ok('with no transcript to read, done, as before', d['state'] == 'done', d)
t21 = Transcript('s-21'); t21.add({'type': 'user', 'message': {'role': 'user', 'content': 'go'}}); t21.bg('b21')
with open(t21.path, 'a', encoding='utf-8') as f: f.write('{not json run_in_background\n\x00\x01 backgroundTaskId garbage\n')
hook('working', {'hook_event_name': 'UserPromptSubmit', 'prompt': 'go'}, 's-21', t21)
r = hook('done', {'hook_event_name': 'Stop'}, 's-21', t21)
ok('lines it cannot read are passed over, and the hook still prints nothing', sess('s-21')['state'] == 'background' and r.stdout == b'' and r.returncode == 0)

# a big transcript, as a long session's is: most lines are skipped unread
big = Transcript('s-22')
big.bg('b22', ago=1)
filler = json.dumps({'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': 'x' * 2000}]}}, separators=(',', ':'))
with open(big.path, 'a', encoding='utf-8') as f:
    for _ in range(15000): f.write(filler + '\n')
hook('working', {'hook_event_name': 'UserPromptSubmit', 'prompt': 'go'}, 's-22', big)
t = time.time(); stop('s-22', big); took = time.time() - t
mb = big.path.stat().st_size / 1e6
ok(f'a {mb:.0f} MB transcript is read in good time ({took:.2f} s with Python\'s start, in the background)', sess('s-22')['state'] == 'background' and took < 4, took)
r = run(SCRIPT, '--status')
ok('--status lists a session in the background', r.returncode == 0 and b'background' in r.stdout)
ok('the script has no dashes the tool refuses', '\u2014' not in SETUP and '\u2013' not in SETUP)
shutil.rmtree(home, ignore_errors=True)

# ---------- part two: the city ----------
FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
def put(session, state, mins=0, since=None, until=None, **kw):
    """A session file as the hooks write it: last heard from mins minutes ago, in this state since since minutes
    ago, and while background, until until minutes from now."""
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    u = f', until: Date.now() + {until} * 60000' if until is not None else ''
    s = since if since is not None else mins + 2
    return (f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', "
            f"cwd: 'C:\\\\Users\\\\me\\\\garden\\\\src', at: Date.now() - {mins} * 60000, since: Date.now() - {s} * 60000, started: Date.now() - {s + 3} * 60000{u}{extra} }})")
TASK = dict(task='Water the beds on time', project='Garden planner')

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t54')) { sessionStorage.setItem('nc-t54', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(600)
    js = pg.evaluate
    gp = js("() => DB.projects.find(p => p.name === 'Garden planner').id")
    js("""() => { const p = DB.projects.find(p => p.name === 'Garden planner');
      p.links.push({ id: uid('l'), label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true });
      addTasks(p, [{ text: 'Water the beds on time', description: '' }], { id: p.milestones[0].id }); persistNow();
      window.__alerts = []; Sound.claude = (st, pr) => { window.__alerts.push(st + ':' + pr.name); return true; }; }""")
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    js("() => { window.__cmark = true; }")
    def settle(ms=3600): pg.wait_for_timeout(ms)
    st = lambda: js(f"() => {{ const s = ClaudeWork.statusOf(getProject('{gp}')); return s && {{ state: s.state, count: s.count }}; }}")
    cb = lambda: js(f"() => {{ const b = MapView.claudeBubbleAt('{gp}'); return b && {{ color: b.color, state: b.state, frame: b.frame }}; }}")
    alerts = lambda: js("() => window.__alerts.slice()")

    js(put('w1', 'working', mins=1, **TASK)); settle()
    ok('a session working shows on its building', st() == {'state': 'working', 'count': 1})
    js(put('w1', 'background', mins=25, since=40, until=35, reply='The full run is going; I will report when it is done.', **TASK))
    js(put('w2', 'working', mins=25)); settle()
    ok(f'a session in the background shows as working, 25 minutes after its reply ended, past working\'s 20 quiet minutes ({st()})',
       st() == {'state': 'working', 'count': 1} and cb()['color'] == 'claude' and cb()['state'] == 'working')
    frames = set()
    for _ in range(8): frames.add(cb()['frame']); pg.wait_for_timeout(170)
    ok(f'its spark turns, as for any work ({sorted(frames)})', frames == {0, 1})
    ok('no finish alert plays, and the tab\'s title counts nothing waiting', alerts() == [] and pg.title() == 'Nullovation City', (alerts(), pg.title()))
    ok('Claude counts as at work in the city, for the computers\' sound', js("() => ClaudeWork.working()") is True)
    ok('Settings, Links counts it working', '1 working' in pg.text_content('#claudeBox'), pg.text_content('#claudeBox')[:200])
    close_settings(pg)
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(800)
    line = pg.text_content('#bubble .b-claude') or ''
    ok(f'the status card says Claude is working on the task, since the stretch of work began ({line[:80]})', line.startswith('Claude is working on Water the beds on time. Started 40 minutes ago.'), line)
    ok('and offers no Tick it, since nothing is finished', not pg.is_visible('#bubble .b-claude-tick'))
    pg.screenshot(path=str(SH / '540-background-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    js("() => { Traffic.setOn(true); MapView.invalidate(); MapView.kick(); }"); pg.wait_for_timeout(2000)
    n = js(f"() => {{ const key = [...MapView.layout()].find(([k, p]) => p.id === '{gp}')[0]; return Traffic._state().cdrones.filter(d => d.plot === key && !d.leaving).length; }}")
    ok(f'Claude\'s six drones work round the building ({n})', n == 6, n)
    js("() => { Traffic.setOn(false); MapView.invalidate(); }")

    # its time runs out with no word: the reply it ended on is Claude's last, so it is finished, with no alert
    js(put('w1', 'background', mins=25, since=40, until=0.08, reply='The full run is going; I will report when it is done.', **TASK)); settle()
    ok('until its time is up, it is working', st() == {'state': 'working', 'count': 1})
    settle(4000)
    ok(f'once its time is up, with the file unchanged, it is finished ({st()})', st() == {'state': 'done', 'count': 1} and cb()['color'] == 'done', (st(), cb()))
    ok('with no alert, being old news, and the tab\'s title counting it', alerts() == [] and pg.title() == '(1) Nullovation City', (alerts(), pg.title()))
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(800)
    line = pg.text_content('#bubble .b-claude') or ''
    ok(f'its card says Claude handed the task back, with its reply and Tick it ({line[:80]})', line.startswith('Claude handed Water the beds on time back to you.') and 'The full run is going' in line and pg.is_visible('#bubble .b-claude-tick'), line)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)

    # the usual way: back to work when the command reports, then finished, with its alert
    js(put('w1', 'background', mins=1, since=10, until=30, reply='Running the tests.', **TASK)); settle()
    js(put('w1', 'working', mins=0, since=10, **TASK)); settle()
    ok('the command reporting puts it back to work, still with no alert', st() == {'state': 'working', 'count': 1} and alerts() == [])
    js(put('w1', 'done', mins=0, reply='All 50 passes are green.', **TASK)); settle()
    ok(f'and the real finish is finished, with its alert ({alerts()})', st() == {'state': 'done', 'count': 1} and alerts() == ['done:Garden planner'], alerts())
    js(put('w3', 'background', mins=0, since=1, **TASK)); js("() => window.__cf.delete('w1.json')"); settle()
    ok('a background file with no until (never written by the hooks) lasts as working does', st() == {'state': 'working', 'count': 1})
    js(f"() => MapView.setCam({{ x: 0, y: 120, z: 2 }})"); js("() => MapView.invalidate()"); pg.wait_for_timeout(700)
    a = js(f"() => MapView.anchors('{gp}')"); left = pg.query_selector('#mapWrap').bounding_box()['x']
    pg.screenshot(path=str(SH / '541-background-bubble.png'), clip={'x': max(0, left + a['topX'] - 160), 'y': max(0, a['topY'] - 90), 'width': 320, 'height': 200})
    b.close()

ok(f'no console errors ({errors[:3]})', not errors)
