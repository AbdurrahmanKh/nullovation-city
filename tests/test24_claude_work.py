"""Claude Code at work: the setup script's hooks and install, and the city reading the folder they write.

Part one runs src/setup/nullovation-claude-status.py as Claude Code would, in a home folder made for the test: its
install and uninstall of the hooks in ~/.claude/settings.json, and the session file each hook event leaves. Part two
opens the city with a folder held in memory, standing in for the one the hooks write, and checks which building each
session lands on, the bubbles on the map, the status card, and Settings, Links."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, DATA, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

SCRIPT = ROOT / 'src' / 'setup' / 'nullovation-claude-status.py'
SETUP = SCRIPT.read_text(encoding='utf-8')

# ---------- part one: the script, as Claude Code runs it ----------
home = pathlib.Path(tempfile.mkdtemp(prefix='nc-claude-', dir=str(DATA)))
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PYTHONUTF8='1')
env.pop('CLAUDE_CODE_ENTRYPOINT', None)
def run(*args, stdin=''):
    return subprocess.run([sys.executable, *map(str, args)], input=stdin.encode('utf-8'), env=env, capture_output=True, timeout=60)

settings = home / '.claude' / 'settings.json'
settings.parent.mkdir(parents=True)
mine = {'model': 'opus', 'permissions': {'allow': ['Bash(npm test)']},
        'hooks': {'Stop': [{'hooks': [{'type': 'command', 'command': 'echo my own hook'}]}],
                  'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'my-check'}]}]}}
settings.write_text(json.dumps(mine), encoding='utf-8')
r = run(SCRIPT, '--install')
s1 = json.loads(settings.read_text(encoding='utf-8'))
folder = home / 'Nullovation City' / 'Claude'
installed = home / '.claude' / 'hooks' / 'nullovation-city-status.py'
ok(f'--install succeeds and says where the folder is ({r.returncode})', r.returncode == 0 and str(folder) in r.stdout.decode())
events = ['SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'PermissionRequest', 'Notification', 'Stop', 'StopFailure', 'SessionEnd']
ours = lambda h: str(installed) in (h.get('args') or [])
def our_hooks(s):
    return [(e, g.get('matcher'), h['args'][2]) for e, gs in s.get('hooks', {}).items() for g in gs for h in g['hooks'] if ours(h)]
got = our_hooks(s1)
ok(f'it adds a hook for each event it reads ({len(got)} hooks)', sorted({e for e, _, _ in got}) == sorted(events) and len(got) == 10)
ok('each event maps to its state', ('UserPromptSubmit', None, 'working') in got and ('Stop', None, 'done') in got and ('PermissionRequest', None, 'waiting') in got
   and ('Notification', 'idle_prompt', 'idle') in got and ('PreToolUse', 'AskUserQuestion', 'waiting') in got and ('StopFailure', None, 'failed') in got and ('SessionEnd', None, 'ended') in got)
hs = [h for gs in s1['hooks'].values() for g in gs for h in g['hooks'] if ours(h)]
ok('every hook runs in the background, as Python with no shell, on the copy in ~/.claude/hooks',
   all(h['async'] is True and h['command'] == sys.executable and h['args'][0] == str(installed) and h['args'][1] == 'hook' and h['args'][3] == str(folder) for h in hs) and installed.exists())
ok('every other setting and hook stays as it was', s1['model'] == 'opus' and s1['permissions'] == mine['permissions']
   and {'type': 'command', 'command': 'echo my own hook'} in [h for g in s1['hooks']['Stop'] for h in g['hooks']]
   and s1['hooks']['PreToolUse'][0] == mine['hooks']['PreToolUse'][0])
ok('the settings file as it was is kept beside it', json.loads((settings.parent / 'settings.json.nullovation-backup').read_text(encoding='utf-8')) == mine)
ok('it makes the folder the city reads, and leaves its README there for the city to find', folder.is_dir() and 'Nullovation City' in (folder / 'README-nullovation-city.txt').read_text(encoding='utf-8'))
run(SCRIPT, '--install')
s2 = json.loads(settings.read_text(encoding='utf-8'))
ok('installing again changes nothing: it replaces its own hooks, never doubles them', s2 == s1)

def hook(state, event):
    return run(installed, 'hook', state, folder, stdin=json.dumps(event))
def sess(name='s-1'):
    return json.loads((folder / (name + '.json')).read_text(encoding='utf-8'))
base = {'session_id': 's-1', 'cwd': 'C:\\Users\\me\\garden\\src', 'transcript_path': 'x.jsonl'}
r = hook('start', {**base, 'hook_event_name': 'SessionStart', 'source': 'startup'})
ok('a new session is noted as idle, with its folder', sess()['state'] == 'idle' and sess()['cwd'] == base['cwd'] and r.returncode == 0)
prompt = '# Task: Water the beds on time\nProject: Garden planner\nMilestone: Launch\nDue: no date\n\n## Description\nThe reminders.'
r = hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': prompt})
d = sess()
ok(f'a prompt sets it working and reads the copy\'s project and task ({d.get("project")}, {d.get("task")})', d['state'] == 'working' and d['project'] == 'Garden planner' and d['task'] == 'Water the beds on time' and d['ask'] == '# Task: Water the beds on time')
ok('a hook prints nothing, so Claude reads nothing from it, and always succeeds', r.stdout == b'' and r.returncode == 0)
since = d['since']; time.sleep(0.02)
hook('working', {**base, 'hook_event_name': 'PostToolUse', 'tool_name': 'Edit'})
ok('each tool call keeps it working, and its start time stays', sess()['state'] == 'working' and sess()['since'] == since and sess()['at'] > d['at'])
hook('waiting', {**base, 'hook_event_name': 'PermissionRequest', 'tool_name': 'Bash'})
ok('a permission prompt means it waits for you', sess()['state'] == 'waiting')
hook('working', {**base, 'hook_event_name': 'PostToolUse', 'tool_name': 'Bash'})
hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': 'yes, go on'})
ok('a short follow-up keeps the copy\'s task and notes the latest ask', sess()['task'] == 'Water the beds on time' and sess()['ask'] == 'yes, go on')
hook('done', {**base, 'hook_event_name': 'Stop', 'stop_hook_active': False, 'last_assistant_message': 'Done: the reminders fire at 7.\n\nDetails follow.'})
ok(f'finishing a reply means done, with the start of the reply ({sess().get("reply")})', sess()['state'] == 'done' and sess()['reply'] == 'Done: the reminders fire at 7.')
hook('idle', {**base, 'hook_event_name': 'Notification', 'message': 'Claude is waiting for your input'})
ok('the idle notice leaves a finished session finished', sess()['state'] == 'done')
hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': 'one more thing'})
hook('idle', {**base, 'hook_event_name': 'Notification', 'message': 'Claude is waiting for your input'})
ok('but ends a stretch of work that never reported its end, as after Esc', sess()['state'] == 'idle')
hook('failed', {**base, 'hook_event_name': 'StopFailure', 'error': 'overloaded'})
ok('an API error means failed', sess()['state'] == 'failed')
hook('ended', {**base, 'hook_event_name': 'SessionEnd', 'reason': 'prompt_input_exit'})
ok('closing the session means ended', sess()['state'] == 'ended')
future = sess(); future['at'] = int(time.time() * 1000) + 60000; future['state'] = 'working'
(folder / 's-1.json').write_text(json.dumps(future), encoding='utf-8')
hook('done', {**base, 'hook_event_name': 'Stop'})
ok('an event never overwrites a later one, since the hooks run in the background', sess()['state'] == 'working')
r = run(installed, 'hook', 'working', folder, stdin='not json')
ok('a bad event changes nothing, prints nothing and still succeeds, and is noted in hook-errors.log',
   r.returncode == 0 and r.stdout == b'' and (folder / 'hook-errors.log').exists())
r = run(installed, 'hook', 'working', folder, stdin=json.dumps({**base, 'session_id': '../escape'}))
ok('a session id that is not a plain name is refused', not (folder.parent / 'escape.json').exists() and r.returncode == 0)
old = folder / 'old-session.json'; old.write_text('{}', encoding='utf-8'); t = time.time() - 4 * 86400; os.utime(old, (t, t))
hook('start', {**base, 'session_id': 's-2', 'hook_event_name': 'SessionStart'})
ok('a new session clears files older than three days', not old.exists() and (folder / 's-2.json').exists())
r = run(SCRIPT, '--status')
ok('--status lists the sessions', r.returncode == 0 and b'working' in r.stdout)
r = run(SCRIPT, '--help')
ok('--help shows how to use it, and changes nothing', r.returncode == 0 and b'double-click' in r.stdout)
r = run(SCRIPT, '--uninstall')
s3 = json.loads(settings.read_text(encoding='utf-8'))
ok('--uninstall takes out only its own hooks', r.returncode == 0 and not our_hooks(s3) and s3['model'] == 'opus'
   and s3['hooks'] == mine['hooks'] and not installed.exists())
settings.write_text('{ "model": "opus", }', encoding='utf-8')
r = run(SCRIPT, '--install')
ok('a settings file that is not valid JSON is left alone, and the install says why', r.returncode == 1 and settings.read_text(encoding='utf-8') == '{ "model": "opus", }' and b'could not be read' in r.stdout)
settings.unlink()
r = run(SCRIPT)
ok('with no arguments, as from a double-click, it installs, and waits for Enter only in a console', r.returncode == 0 and our_hooks(json.loads(settings.read_text(encoding='utf-8'))) and b'Press Enter' not in r.stdout)
settings.unlink()
r = run(SCRIPT, '--install', '--folder', home / 'elsewhere')
s4 = json.loads(settings.read_text(encoding='utf-8'))
elsewhere = str((home / 'elsewhere').resolve())
ok('with no settings file it makes one, and --folder puts the sessions elsewhere',
   r.returncode == 0 and all(h['args'][3] == elsewhere for gs in s4['hooks'].values() for g in gs for h in g['hooks']) and (home / 'elsewhere' / 'README-nullovation-city.txt').exists())
folders = lambda: {h['args'][3] for gs in json.loads(settings.read_text(encoding='utf-8'))['hooks'].values() for g in gs for h in g['hooks']}
run(SCRIPT, '--install')
ok('running the setup again keeps the folder already set, rather than going back to the default', folders() == {elsewhere})
env['NULLOVATION_NO_GUI'] = '1'
picked = home / 'Nullovation City data' / 'Claude-Hooks'
r = run(SCRIPT, '--ask', stdin=str(picked) + '\n')
ok(f'asked for a folder (as a double-click asks), it moves the hooks there ({r.returncode})', r.returncode == 0 and folders() == {str(picked.resolve())} and (picked / 'README-nullovation-city.txt').exists())
r = run(SCRIPT, '--ask', stdin='\n')
ok('pressing Enter at the question keeps the folder already set', r.returncode == 0 and folders() == {str(picked.resolve())})
r = run(SCRIPT, '--ask', stdin='')
ok('cancelling the question changes nothing', r.returncode == 0 and b'Nothing changed' in r.stdout and folders() == {str(picked.resolve())})
del env['NULLOVATION_NO_GUI']
ok('the script has no dashes the tool refuses', '\u2014' not in SETUP and '\u2013' not in SETUP)
shutil.rmtree(home, ignore_errors=True)

# ---------- part two: the city reading the folder ----------
# a Claude folder held in memory: the files the hooks would write, by name
FAKE = """
window.__cf = new Map(); window.__cperm = 'granted'; window.__cgone = false; window.__ct = 1; window.__cmark = false;
window.__put = (name, d) => window.__cf.set(name, { text: JSON.stringify(d), t: Date.now() + (window.__ct++) });
const cfile = name => ({ kind: 'file', name, getFile: async () => { const f = window.__cf.get(name); if (!f) { const e = new Error('gone'); e.name = 'NotFoundError'; throw e; } return new File([f.text], name, { lastModified: f.t }); } });
window.__cdir = { kind: 'directory', name: 'Claude',
  queryPermission: async () => window.__cperm, requestPermission: async () => { window.__cperm = 'granted'; return 'granted'; },
  entries: async function* () {
    if (window.__cgone) { const e = new Error('gone'); e.name = 'NotFoundError'; throw e; }
    if (window.__cperm !== 'granted') { const e = new Error('no'); e.name = 'NotAllowedError'; throw e; }
    for (const n of [...window.__cf.keys()]) yield [n, cfile(n)];
    yield ['hook-errors.log', cfile('hook-errors.log')];
    if (window.__cmark) yield ['README-nullovation-city.txt', cfile('README-nullovation-city.txt')];
  } };
window.showDirectoryPicker = async () => window.__cdir;
"""
def S(session, state, cwd, mins=0, **kw):
    """A session file as the hooks write it, last heard from mins minutes ago."""
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(cwd)}, at: {at}, since: {at} - 120000, started: {at} - 300000{extra} }})"

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t24')) { sessionStorage.setItem('nc-t24', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(600)
    js = pg.evaluate
    ids = js("() => Object.fromEntries(DB.projects.map(p => [p.name, p.id]))")
    gp, nc = ids['Garden planner'], ids['Nullovation City']
    js("""() => { const add = (p, url) => p.links.push({ id: uid('l'), label: '', url, icon: 'folder', shortcut: true });
      add(DB.projects.find(p => p.name === 'Garden planner'), 'C:\\\\Users\\\\me\\\\garden');
      const c = DB.projects.find(p => p.name === 'Nullovation City');
      add(c, 'C:\\\\Users\\\\me\\\\city'); add(c, 'C:\\\\Users\\\\me\\\\garden\\\\tools\\\\city'); add(c, 'file:///D:/Notes/city-plan.md'); persistNow(); }""")

    open_settings(pg, 'links')
    box = pg.text_content('#claudeBox')
    ok(f'Settings, Links has Claude Code at work, starting off ({box[:40]})', 'Connect the Claude folder' in box and 'Claude Code at work' in pg.text_content('#settings'))
    with pg.expect_download() as dl:
        pg.click('#btnClaudeSetup')
    path = dl.value.path(); text = pathlib.Path(path).read_text(encoding='utf-8')
    ok('Get the setup saves the script, exactly as written', dl.value.suggested_filename == 'nullovation-claude-status.py' and text == SETUP)
    ok('the tool carries the same script it hands out', js("() => CLAUDE_SETUP_PY") == SETUP)
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    ok(f'connecting the folder watches it ({pg.text_content("#claudeBox")[:70]})', js("() => ClaudeWork.state()") == 'on' and 'Claude' in pg.text_content('#claudeBox') and 'Nothing from Claude Code yet' in pg.text_content('#claudeBox'))
    ok('an empty folder the setup never wrote to says Claude Code does not write there', pg.is_visible('#claudeUnmarked') and 'Double-click the setup again' in pg.text_content('#claudeUnmarked'))
    pg.screenshot(path=str(SH / '245-settings-links-wrong-folder.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})
    js("() => { window.__cmark = true; }"); pg.wait_for_timeout(3600)
    ok('with the setup\'s README in it, the warning goes', not pg.is_visible('#claudeUnmarked'))

    def settle(ms=3600):
        pg.wait_for_timeout(ms)
    def st(pid):
        return js(f"() => {{ const s = ClaudeWork.statusOf(getProject('{pid}')); return s && {{ state: s.state, count: s.count }}; }}")
    def cb(pid):
        return js(f"() => {{ const b = MapView.claudeBubbleAt('{pid}'); return b && {{ color: b.color, text: b.text, state: b.state, frame: b.frame, x: b.x, w: b.w }}; }}")

    js(S('a1', 'working', 'C:\\Users\\me\\garden\\src', task='Water the beds on time', project='Garden planner'))
    settle()
    ok(f'a session working in a project\'s folder puts a bubble on its building, without a reload ({cb(gp)})', st(gp) == {'state': 'working', 'count': 1} and cb(gp)['color'] == 'claude')
    frames = set()
    for _ in range(8):
        frames.add(cb(gp)['frame']); pg.wait_for_timeout(170)
    ok(f'the spark turns while it works ({sorted(frames)})', frames == {0, 1})
    ok('Settings says what it last heard', 'Last heard from Claude Code just now' in pg.text_content('#claudeBox') and '1 working' in pg.text_content('#claudeBox'))

    # which building a session belongs to
    js(S('a2', 'working', 'c:/USERS/me/Garden/', task=''))
    js(S('a3', 'working', '/mnt/c/Users/me/garden/docs'))
    js(S('a4', 'working', 'C:\\Users\\me\\garden\\tools\\city\\src'))
    js(S('a5', 'working', 'D:\\Notes'))
    js(S('a6', 'working', 'E:\\scratch', project='Nullovation City', task='Fix the bubble'))
    js(S('a7', 'working', 'E:\\lost\\thing'))
    settle()
    sessions = js("() => Object.fromEntries(DB.projects.map(p => [p.name, (ClaudeWork.statusOf(p) || { sessions: [] }).sessions.map(s => s.session).sort()]))")
    ok(f'a folder matches in any case and slash, and from WSL ({sessions["Garden planner"]})', sessions['Garden planner'] == ['a1', 'a2', 'a3'])
    ok(f'the deepest folder link wins; a file link counts by its folder; the copy\'s Project line places the rest ({sessions["Nullovation City"]})', sessions['Nullovation City'] == ['a4', 'a5', 'a6'])
    ok('several sessions at once show their count', cb(gp)['text'] == '3' and st(gp)['count'] == 3)
    ok('a session no building claims is listed in Settings, to link its folder', 'E:\\lost\\thing' in pg.text_content('#claudeBox') and 'Not on a building' in pg.text_content('#claudeBox'))
    for s in ['a2', 'a3', 'a4', 'a5', 'a6', 'a7']:
        js(f"() => window.__cf.delete('{s}.json')")
    settle()
    ok('a removed file takes its session away', st(gp)['count'] == 1 and st(nc) is None and 'Not on a building' not in pg.text_content('#claudeBox'))

    # the states
    js(S('a1', 'waiting', 'C:\\Users\\me\\garden\\src', task='Water the beds on time'))
    settle()
    ok(f'waiting for you shows a ? ({cb(gp)})', cb(gp)['state'] == 'waiting' and cb(gp)['text'] == '?')
    js(S('a1', 'working', 'C:\\Users\\me\\garden\\src', mins=21))
    settle()
    ok('working with no word for 20 minutes goes quiet, as after Esc', st(gp) is None and cb(gp) is None)
    js(S('a1', 'ended', 'C:\\Users\\me\\garden\\src'))
    js(S('b1', 'idle', 'C:\\Users\\me\\garden\\src'))
    settle()
    ok('an ended or idle session shows nothing', st(gp) is None)
    js(S('a1', 'ended', 'C:\\Users\\me\\garden\\src', reply='All done: the reminders fire at 7.'))
    settle()
    ok('a session that finished and then closed keeps its tick until you look', st(gp) == {'state': 'done', 'count': 1} and cb(gp)['color'] == 'done')
    js(S('a1', 'ended', 'C:\\Users\\me\\garden\\src'))
    js(S('z1', 'ended', 'D:\\Projects', reply='Done.'))
    settle()
    ok('a closed session in a folder no building links is still listed in Settings', st(gp) is None and 'D:\\Projects' in pg.text_content('#claudeBox'))
    js("() => window.__cf.delete('z1.json')")
    js("() => { const p = DB.projects.find(p => p.name === 'Nullovation City'); p.urgency.system = 'finish'; p.urgency.pickedAt = Date.now(); p.urgency.lastWorked = null; persistNow(); MapView.invalidate(); }")
    js(S('c1', 'done', 'C:\\Users\\me\\city', task='Fix the bubble', reply='Done: the bubble sits beside the red one now.'))
    js(S('a1', 'working', 'C:\\Users\\me\\garden\\src', task='Water the beds on time'))
    settle()
    red = js(f"() => MapView.bubbleAt('{nc}')"); done = cb(nc)
    ok(f'a finished session shows a tick in green ({done})', done['color'] == 'done' and done['state'] == 'done')
    ok(f'beside the red bubble, never over it ({red["x"]}+{red["w"]} < {done["x"]})', red['color'] == 'red' and red['x'] + red['w'] < done['x'])
    left = pg.query_selector('#mapWrap').bounding_box()['x']
    def shot(name, z, w, hh):
        a, g = js(f"() => MapView.anchors('{nc}')"), js(f"() => MapView.anchors('{gp}')")
        js(f"() => MapView.setCam({{ x: 0, y: 160, z: {z} }})"); pg.wait_for_timeout(700)
        a, g = js(f"() => MapView.anchors('{nc}')"), js(f"() => MapView.anchors('{gp}')")
        cx, top = left + (a['topX'] + g['topX']) / 2, min(a['topY'], g['topY'])
        pg.screenshot(path=str(SH / name), clip={'x': max(0, cx - w / 2), 'y': max(0, top - 110), 'width': w, 'height': hh})
    shot('240-claude-bubbles-4x.png', 4, 760, 420)
    shot('241-claude-bubbles-2x.png', 2, 520, 260)
    # the status card, and seeing what finished
    close_settings(pg)
    js(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(800)
    line = pg.text_content('#bubble .b-claude') or ''
    ok(f'the status card says Claude Code finished, what, and when ({line[:80]})', line.startswith('Claude Code finished: Fix the bubble.') and 'Finished 2 minutes ago' in line)
    ok('with the start of its reply', 'the bubble sits beside the red one now' in line)
    pg.screenshot(path=str(SH / '242-claude-card-done.png'), clip=pg.query_selector('#bubble').bounding_box())
    ok('looking at the card counts as seeing it: the tick goes', cb(nc) is None and js(f"() => MapView.bubbleAt('{nc}')['color']") == 'red')
    js("() => MapView.deselect()"); pg.wait_for_timeout(300)
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(800)
    line = pg.text_content('#bubble .b-claude') or ''
    ok(f'a working session\'s card says so, with its task and start ({line[:70]})', line.startswith('Claude Code is working: Water the beds on time.') and 'Started 2 minutes ago' in line)
    pg.screenshot(path=str(SH / '243-claude-card-working.png'), clip=pg.query_selector('#bubble').bounding_box())
    ok('a working session stays on the map while you look', cb(gp)['state'] == 'working')
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    js(S('c1', 'done', 'C:\\Users\\me\\city', task='Fix the bubble', reply='Done again.'))
    settle()
    ok('a newer finish shows the tick again', cb(nc)['state'] == 'done')
    js(S('c2', 'failed', 'C:\\Users\\me\\city'))
    settle()
    ok('an error shows a cross, over a finish', cb(nc)['state'] == 'failed' and cb(nc)['color'] == 'failed')
    js("() => window.__cf.delete('c2.json')"); settle()
    js(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(600)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    c1 = js("() => window.__cf.get('c1.json').text")
    ok('seeing it again clears it again', cb(nc) is None)

    # bubbles hidden, and the postcard
    js("() => MapView.setBubbleMode('none')"); pg.wait_for_timeout(300)
    ok('No bubbles hides Claude Code\'s too', cb(gp) is None and cb(nc) is None)
    js("() => MapView.setBubbleMode('tasks')"); pg.wait_for_timeout(300)
    ok('the Tasks view keeps them, beside the counts', cb(gp)['state'] == 'working' and js(f"() => MapView.bubbleAt('{gp}')['color']") == 'grey')
    js("() => MapView.setBubbleMode('all')"); pg.wait_for_timeout(300)
    js("() => Motion.set('still')"); pg.wait_for_timeout(300)
    frames = set()
    for _ in range(5):
        frames.add(cb(gp)['frame']); pg.wait_for_timeout(170)
    ok('with Motion on Still the spark holds still', frames == {0})
    js("() => Motion.set(null)")

    # seen survives a reload; paused and allowed; a missing folder
    pg.reload(); pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && DB.projects.length === 2", timeout=20000)
    js("() => { const get = Store.getHandle; Store.getHandle = async k => k === 'claudeDir' ? window.__cdir : get(k); }")
    js("t => window.__cf.set('c1.json', { text: t, t: Date.now() })", c1)
    js(S('a1', 'working', 'C:\\Users\\me\\garden\\src', task='Water the beds on time'))
    js("() => { window.__cperm = 'prompt'; return ClaudeWork.init(); }"); pg.wait_for_timeout(500)
    ok('after a reload the browser may hold the folder back: paused, and said under the logo with Allow', js("() => ClaudeWork.state()") == 'paused' and pg.is_visible('#claudeAlert') and 'Allow them' in pg.text_content('#claudeAlert'))
    pg.click('#claudeAlert >> text=Allow them'); pg.wait_for_timeout(800)
    nc_seen = js(f"() => ClaudeWork.statusOf(getProject('{nc}'))")
    ok('Allow reads it again and the alert goes', js("() => ClaudeWork.state()") == 'on' and not pg.is_visible('#claudeAlert') and st(gp)['state'] == 'working')
    ok('a finish you saw stays seen after a reload', nc_seen is None)
    js("() => { window.__cgone = true; }"); settle()
    ok('a folder that was moved or deleted says so, with Pick it again', js("() => ClaudeWork.state()") == 'failed' and 'Pick it again' in pg.text_content('#claudeAlert') and st(gp) is None)
    js("() => { window.__cgone = false; }")
    open_settings(pg, 'links')
    pg.click('#claudeBox >> text=Pick the Claude folder again'); pg.wait_for_timeout(600)
    ok('picking it again brings the bubbles back', js("() => ClaudeWork.state()") == 'on' and st(gp)['state'] == 'working')
    pg.screenshot(path=str(SH / '244-settings-links-claude.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})
    pg.click('#btnTabReset'); pg.wait_for_timeout(200)
    ok('Reset to defaults leaves the connection alone', js("() => ClaudeWork.state()") == 'on')
    pg.click('#claudeBox >> text=Stop'); pg.wait_for_timeout(300)
    ok('Stop forgets the folder and the bubbles go', js("() => ClaudeWork.state()") == 'off' and cb(gp) is None and 'Connect the Claude folder' in pg.text_content('#claudeBox'))

    b.close()

print(errors or 'no console errors')
