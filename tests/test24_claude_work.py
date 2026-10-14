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
hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': '<task-notification>\n<task-id>b1</task-id> finished\n</task-notification>'})
ok('a turn Claude Code starts on its own keeps working, but replaces neither the ask nor the task', sess()['state'] == 'working' and sess()['ask'] == 'yes, go on' and sess()['task'] == 'Water the beds on time')
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
cfg0 = json.loads((home / '.claude' / 'nullovation-city.json').read_text(encoding='utf-8'))
r = run(SCRIPT, '--uninstall')
s3 = json.loads(settings.read_text(encoding='utf-8'))
ok('the setup writes the folder down for the nullovation-city skill, with the summary and the inbox in it',
   cfg0.get('folder') == str(folder.resolve()) and cfg0.get('summary') == str(folder.resolve() / 'city' / 'summary.json') and cfg0.get('inbox') == str(folder.resolve() / 'inbox'))
ok('--uninstall takes out only its own hooks', r.returncode == 0 and not our_hooks(s3) and s3['model'] == 'opus'
   and s3['hooks'] == mine['hooks'] and not installed.exists() and not (home / '.claude' / 'nullovation-city.json').exists())
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
window.__cf = new Map(); window.__cperm = 'granted'; window.__cwperm = 'granted'; window.__cgone = false; window.__ct = 1; window.__cmark = false;
window.__sub = new Map(); window.__dirs = new Set(); window.__writes = 0;
const fail = n => { const e = new Error(n); e.name = n; throw e; };
const subfile = path => ({ kind: 'file', name: path.split('/').pop(),
  getFile: async () => { const f = window.__sub.get(path); if (!f) fail('NotFoundError'); return new File([f.text], path.split('/').pop(), { lastModified: f.t }); },
  createWritable: async () => { if (window.__cwperm !== 'granted') fail('NotAllowedError'); let buf = '';
    return { write: async d => { buf += d; }, close: async () => { window.__sub.set(path, { text: buf, t: Date.now() + (window.__ct++) }); window.__writes++; } }; } });
const subdirOf = (path, o) => { if (!(o && o.create) && !window.__dirs.has(path) && ![...window.__sub.keys()].some(k => k.startsWith(path + '/'))) fail('NotFoundError');
  if (o && o.create && window.__cwperm !== 'granted') fail('NotAllowedError'); window.__dirs.add(path); return subdir(path); };
const subdir = prefix => ({ kind: 'directory', name: prefix.split('/').pop(),
  getDirectoryHandle: async (n, o) => subdirOf(prefix + '/' + n, o),
  getFileHandle: async (n, o) => { const path = prefix + '/' + n; if (!window.__sub.has(path)) { if (!(o && o.create)) fail('NotFoundError'); if (window.__cwperm !== 'granted') fail('NotAllowedError'); } return subfile(path); },
  removeEntry: async n => { if (window.__cwperm !== 'granted') fail('NotAllowedError'); if (!window.__sub.has(prefix + '/' + n)) fail('NotFoundError'); window.__sub.delete(prefix + '/' + n); },
  entries: async function* () { const ds = new Set();
    for (const k of [...window.__sub.keys()]) { if (!k.startsWith(prefix + '/')) continue; const rest = k.slice(prefix.length + 1);
      if (rest.includes('/')) { const d = rest.split('/')[0]; if (!ds.has(d)) { ds.add(d); yield [d, subdir(prefix + '/' + d)]; } } else yield [rest, subfile(k)]; } } });
window.__subjson = path => { const f = window.__sub.get(path); return f ? JSON.parse(f.text) : null; };
window.__put = (name, d) => window.__cf.set(name, { text: JSON.stringify(d), t: Date.now() + (window.__ct++) });
const cfile = name => ({ kind: 'file', name, getFile: async () => { const f = window.__cf.get(name); if (!f) { const e = new Error('gone'); e.name = 'NotFoundError'; throw e; } return new File([f.text], name, { lastModified: f.t }); } });
window.__cdir = { kind: 'directory', name: 'Claude',
  queryPermission: async o => (o && o.mode === 'readwrite') ? window.__cwperm : window.__cperm,
  requestPermission: async o => { if (o && o.mode === 'readwrite') window.__cwperm = window.__cwdeny ? 'denied' : 'granted'; if (!(o && o.mode === 'readwrite' && window.__cwdeny)) window.__cperm = 'granted'; return o && o.mode === 'readwrite' ? window.__cwperm : 'granted'; },
  getDirectoryHandle: async (n, o) => subdirOf(n, o),
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

    # Claude reads the city: city/summary.json, written by the city
    summ = js("() => window.__subjson('city/summary.json')")
    ok('connecting asks to write as well, and the city writes its summary for Claude at once', js("() => ClaudeWork.canWrite()") and summ is not None and summ['kind'] == 'city-summary')
    g = next((p for p in summ['projects'] if p['name'] == 'Garden planner'), None)
    ok(f'the summary holds every project, with its milestones, open tasks and their descriptions, done tasks, folders and urgency ({len(summ["projects"])} projects)',
       len(summ['projects']) == 2 and g and any(ms['open'] and ms['open'][0]['task'] == 'Draw the beds on a grid' for ms in g['milestones'])
       and g['folders'] == ['C:\\Users\\me\\garden'] and g['next'] == 'Draw the beds on a grid' and 'state' in g['urgency'])
    raw = js("() => window.__sub.get('city/summary.json').text")
    ok(f'and never the building art ({len(raw)} characters)', 'data:image' not in raw and 'dataUrl' not in raw)
    js("() => { const p = DB.projects.find(p => p.name === 'Garden planner'); addTasks(p, [{ text: 'Mulch the beds', description: 'Before winter.', due: '' }], { id: p.milestones[0].id }); persistNow(); }")
    pg.wait_for_timeout(2600)
    summ = js("() => window.__subjson('city/summary.json')")
    ok('a change in the city is in the summary a moment later', any(t['task'] == 'Mulch the beds' for p in summ['projects'] for ms in p['milestones'] for t in ms['open']))
    ok('Settings says Claude can read the city', 'Claude can read the city: written' in pg.text_content('#claudeBox'))
    js("() => { const get = Store.getHandle; Store.getHandle = async k => k === 'claudeDir' ? window.__cdir : get(k); window.__cwperm = 'prompt'; return ClaudeWork.init(); }"); pg.wait_for_timeout(500)
    ok('connected with reading only, as before 0.1.35, Settings asks to let the city write', pg.is_visible('#claudeWrite') and 'Let it write' in pg.text_content('#claudeWrite'))
    ok('and so does the side bar, under the logo', pg.is_visible('#claudeAlert') and 'Claude cannot read the city' in pg.text_content('#claudeAlert'))
    before = js("() => window.__writes")
    pg.click('#claudeWrite >> text=Let it write'); pg.wait_for_timeout(700)
    ok('Let it write asks once, and the summary is written at once', js("() => ClaudeWork.canWrite()") and js("() => window.__writes") > before and not pg.is_visible('#claudeAlert'))
    pg.screenshot(path=str(SH / '247-settings-links-claude-reads.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})

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

    # Tick it: the open task a city copy started, ticked from the finish line
    js(S('t1', 'done', 'C:\\Users\\me\\city', task='Build the block art skill', project='Nullovation City', reply='The skill is built.'))
    settle()
    js(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(800)
    acts = pg.locator('#bubble .b-claude-acts')
    ok(f'a finish from a city copy offers Tick it for its open task ({acts.count()})', acts.count() == 1 and pg.is_visible('#bubble .b-claude-tick'))
    pg.screenshot(path=str(SH / '246-claude-tick-it.png'), clip=pg.query_selector('#bubble').bounding_box())
    pg.click('#bubble .b-claude-tick'); pg.wait_for_timeout(500)
    t1 = js(f"() => {{ const p = getProject('{nc}'), t = p.todos.find(x => x.text === 'Build the block art skill'); return {{ done: t.done, at: !!t.doneAt, worked: Date.now() - (p.urgency.lastWorked || 0) < 60000, act: p.activity[p.activity.length - 1].text }}; }}")
    ok(f'Tick it ticks it off as a tick does: done, work for urgency, a line in Activity ({t1})', t1 == {'done': True, 'at': True, 'worked': True, 'act': 'Done: Build the block art skill'})
    ok('and the button goes, since the task is done', pg.locator('#bubble .b-claude-tick').count() == 0 and 'Ticked off: Build the block art skill.' in pg.text_content('#toast'))
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    js(S('t2', 'done', 'C:\\Users\\me\\city', task='Make block art for each project', project='Garden planner'))
    js(S('t3', 'done', 'C:\\Users\\me\\city', task='A task the city does not have', project='Nullovation City'))
    js(S('t4', 'working', 'C:\\Users\\me\\city', task='Try the project view for a week', project='Nullovation City'))
    js(S('t5', 'done', 'C:\\Users\\me\\city', task='Round 3: decide the block art loop', project='Nullovation City'))
    settle()
    js(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(800)
    fin = [x.strip() for x in pg.locator('#bubble .b-claude-fin').all_text_contents()]
    ok(f'with a session still working, a finished one\'s Tick it names its task; another project\'s copy and a missing task offer none ({fin})',
       fin == ['Finished: Round 3: decide the block art loop'] and pg.locator('#bubble .b-claude-tick').count() == 1 and (pg.text_content('#bubble .b-claude-line') or '').startswith('Claude Code is working'))
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    for k in ('t1', 't2', 't3', 't4', 't5'):
        js(f"() => window.__cf.delete('{k}.json')")
    js(S('t6', 'working', 'C:\\Users\\me\\city', ask='<task-notification> a background task finished'))
    settle()
    js(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(600)
    ok('a turn Claude Code starts on its own shows no <task-notification> as its ask', '<task-notification>' not in (pg.text_content('#bubble .b-claude') or '') and (pg.text_content('#bubble .b-claude-line') or '').startswith('Claude Code is working.'))
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    js("() => window.__cf.delete('t6.json')"); settle()

    # Claude updates the city: change files in inbox/
    def drop(name, d):
        js(f"() => window.__sub.set('inbox/{name}', {{ text: {json.dumps(json.dumps(d))}, t: Date.now() }})")
    gp_state = lambda: js(f"() => {{ const p = getProject('{gp}'); return {{ todos: p.todos.map(t => t.text), notes: p.notes.map(n => n.title), links: p.links.map(l => l.url), ms: p.milestones.map(m => m.name) }}; }}")
    st0 = gp_state()
    drop('2026-10-14-0900-garden.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'garden planner', 'summary': 'Reminders built',
        'changes': [{'do': 'add-tasks', 'milestone': 'Launch', 'tasks': [{'text': 'Test the reminders on a phone', 'description': 'Both platforms.'}, {'text': 'Write the reminder copy', 'description': 'Short and kind.'}]},
                    {'do': 'add-note', 'title': 'Reminder timing', 'text': 'They fire at 7, from the last watering.'},
                    {'do': 'add-link', 'label': 'Reminders PR', 'url': 'https://github.com/me/garden/pull/12'}]})
    settle()
    st1 = gp_state()
    launch = js(f"() => {{ const p = getProject('{gp}'), m = p.milestones.find(m => m.name === 'Launch'); return p.todos.filter(t => t.milestoneId === m.id).map(t => t.text); }}")
    ok(f'adding tasks, a note and a link applies at once, in the milestone named, by the project\'s name in any case ({launch[-2:]})',
       launch[-2:] == ['Test the reminders on a phone', 'Write the reminder copy'] and 'Reminder timing' in st1['notes'] and 'https://github.com/me/garden/pull/12' in st1['links'] and st1['ms'] == st0['ms'])
    tst = pg.text_content('#toast') or ''
    ok(f'with a toast and Undo ({tst})', tst.startswith('Claude added 2 tasks, a note and 1 link in Garden planner.') and 'Undo' in tst)
    ok('the file moves to inbox/done, so nothing applies twice', js("() => window.__sub.has('inbox/done/2026-10-14-0900-garden.json') && !window.__sub.has('inbox/2026-10-14-0900-garden.json')"))
    acts = js(f"() => getProject('{gp}').activity.slice(-6).map(e => e.text)")
    ok(f'and Activity says what Claude did ({acts[-3:]})', 'Claude: Reminders built' in acts and 'Claude wrote a note: Reminder timing' in acts and 'Added todo: Write the reminder copy' in acts)
    pg.click('#toast .toast-act'); pg.wait_for_timeout(400)
    ok('Undo takes back exactly what Claude added', gp_state() == st0)

    drop('2026-10-14-0910-garden.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'summary': 'Plans save as files',
        'changes': [{'do': 'done', 'task': 'Save a plan as a file'}, {'do': 'edit-description', 'task': 'Draw the beds on a grid', 'description': 'Drawn at 1:50. Left: labels.'},
                    {'do': 'done', 'task': 'A task that is not there'}]})
    drop('2026-10-14-0920-garden.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner',
        'changes': [{'do': 'replace-plan', 'plan': {'description': 'A new About.', 'milestones': [{'name': 'Only one', 'tasks': [{'text': 'One task', 'description': 'x'}]}]}}]})
    settle()
    ok('ticking, a new description and a new plan wait in inbox/pending, untouched', js("() => window.__sub.has('inbox/pending/2026-10-14-0910-garden.json') && window.__sub.has('inbox/pending/2026-10-14-0920-garden.json')")
       and gp_state() == st0 and not js(f"() => getProject('{gp}').todos.find(t => t.text === 'Save a plan as a file').done"))
    ok(f'the building\'s Claude bubble asks with a ?, over a session working there ({cb(gp)})', cb(gp)['state'] == 'waiting' and cb(gp)['text'] == '?')
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(800)
    asks = pg.locator('#bubble .b-claude-asks')
    first = asks.nth(0).text_content() if asks.count() else ''
    ok(f'the status card lists each, with Apply and Dismiss ({asks.count()} | {first[:90]})', asks.count() == 2 and 'Claude asks first: Plans save as files' in first and 'Tick off: Save a plan as a file' in first
       and 'New description for Draw the beds on a grid: Drawn at 1:50.' in first and '(not open in this project)' in first and 'Replace the plan: 1 milestone, 1 task' in asks.nth(1).text_content())
    pg.screenshot(path=str(SH / '248-claude-asks-first.png'), clip=pg.query_selector('#bubble').bounding_box())
    asks.nth(0).locator('.b-claude-apply').click(); pg.wait_for_timeout(700)
    g = js(f"() => {{ const p = getProject('{gp}'); return {{ done: p.todos.find(t => t.text === 'Save a plan as a file').done, desc: p.todos.find(t => t.text === 'Draw the beds on a grid').description }}; }}")
    ok(f'Apply ticks the task and writes the description, skipping what it cannot find ({g})', g == {'done': True, 'desc': 'Drawn at 1:50. Left: labels.'})
    ok('and the entry is put away in inbox/done', js("() => !window.__sub.has('inbox/pending/2026-10-14-0910-garden.json') && window.__sub.has('inbox/done/2026-10-14-0910-garden.json')") and pg.locator('#bubble .b-claude-asks').count() == 1)
    pg.locator('#bubble .b-claude-asks .b-claude-dismiss').click(); pg.wait_for_timeout(600)
    ok('Dismiss puts it away without applying it', js("() => !window.__sub.has('inbox/pending/2026-10-14-0920-garden.json')") and pg.locator('#bubble .b-claude-asks').count() == 0
       and js(f"() => getProject('{gp}').milestones.map(m => m.name)") == st0['ms'])
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    drop('2026-10-14-0930-nowhere.json', {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'A project the city has not', 'changes': [{'do': 'add-note', 'title': 'x', 'text': 'y'}]})
    js("() => window.__sub.set('inbox/broken.json', { text: '{ not json', t: Date.now() })")
    settle()
    ok('a change for a project the city has not, and a file it cannot read, go to inbox/rejected with a message', js("() => window.__sub.has('inbox/rejected/2026-10-14-0930-nowhere.json') && window.__sub.has('inbox/rejected/broken.json') && ![...window.__sub.keys()].some(k => /^inbox\\/[^/]+$/.test(k))"))
    ends = js(f"() => {{ const p = getProject('{gp}'); return [taskForClaude(p, p.todos[0]), noteForClaude(p, {{ title: 'T', text: 'x', at: Date.now() }}), milestoneForClaude(p, p.milestones[0]), projectStatusForClaude(p), statusBrief()].map(x => x.endsWith('\\n\\n' + REPORT_LINE)); }}")
    ok(f'every copy for Claude ends asking it to send the city an update ({ends})', ends == [True] * 5 and js("() => REPORT_LINE") == 'When you finish, send Nullovation City an update with the nullovation-city skill.')
    ok('but not the builder card, which is for the building', not js(f"() => builderCard(getProject('{gp}')).includes(REPORT_LINE)"))
    js(S('c2', 'failed', 'C:\\Users\\me\\city'))
    settle()
    ok('an error shows a cross, over a finish', cb(nc)['state'] == 'failed' and cb(nc)['color'] == 'failed')
    js("() => window.__cf.delete('c2.json')"); settle()
    js(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(600)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    c1 = js("() => window.__cf.get('c1.json').text")
    ok('seeing it again clears it again', cb(nc) is None)

    # a finish in Activity, once per session and what it worked on
    fins = js(f"() => getProject('{nc}').activity.filter(e => e.text.startsWith('Claude Code finished')).map(e => e.text)")
    ok(f'a finish leaves a line in its project\'s Activity, once per session and task, however often it finishes ({fins.count("Claude Code finished: Fix the bubble")})',
       fins.count('Claude Code finished: Fix the bubble') == 1 and 'Claude Code finished: Round 3: decide the block art loop' in fins)
    before = js(f"() => {{ const p = getProject('{gp}'); return {{ up: p.updatedAt, worked: p.urgency.lastWorked, n: p.activity.length }}; }}")
    js(S('f1', 'done', 'C:\\Users\\me\\garden', mins=5, task='Mulch the beds', reply='Mulched.'))
    js(S('w1', 'waiting', 'C:\\Users\\me\\garden', task='Pick a mulch'))
    settle()
    f1 = js(f"""() => {{ const p = getProject('{gp}'), k = p.activity.findIndex(e => e.text === 'Claude Code finished: Mulch the beds'), e = p.activity[k];
      return {{ found: k >= 0, ago: e ? Math.round((Date.now() - e.at) / 60000) : null, ordered: p.activity.every((x, i) => !i || p.activity[i - 1].at <= x.at), up: p.updatedAt, worked: p.urgency.lastWorked, n: p.activity.length }}; }}""")
    ok(f'at the time it finished, in order, and not as work: urgency and Updated stay as they were ({f1})', f1['found'] and f1['ago'] == 5 and f1['ordered']
       and f1['up'] == before['up'] and f1['worked'] == before['worked'] and f1['n'] == before['n'] + 1)
    ok(f'the tab\'s title counts sessions waiting for you and finishes you have not seen ({pg.title()})', pg.title() == '(2) Nullovation City')
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.locator('.pv button:has-text("Activity")').first.click()
    pg.wait_for_timeout(400)
    ok('the Activity panel shows it', 'Claude Code finished: Mulch the beds' in (pg.text_content('.pv-activity') or ''))
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    # the tab's title counts what waits for you
    ok(f'opening the project counts as seeing the finish: it leaves the count ({pg.title()})', pg.title() == '(1) Nullovation City')
    drop_pending = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'changes': [{'do': 'done', 'task': 'Draw the beds on a grid'}]}
    js(f"() => window.__sub.set('inbox/2026-10-14-1000-garden.json', {{ text: {json.dumps(json.dumps(drop_pending))}, t: Date.now() }})")
    settle()
    ok(f'a change that asks first counts too ({pg.title()})', pg.title() == '(2) Nullovation City')
    js("() => { window.__cf.delete('w1.json'); }")
    js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(600)
    pg.locator('#bubble .b-claude-asks .b-claude-dismiss').click(); pg.wait_for_timeout(500)
    js("() => MapView.deselect()"); pg.wait_for_timeout(200)
    settle()
    ok(f'with nothing waiting, the title is the city\'s own ({pg.title()})', pg.title() == 'Nullovation City')

    # Claude's drones: six fly in and work round the building while its session works
    js("() => { Traffic.setOn(true); MapView.invalidate(); MapView.kick(); }"); pg.wait_for_timeout(1600)
    crew = lambda: js(f"""() => {{ const key = [...MapView.layout()].find(([k, p]) => p.id === '{gp}')[0], [u, v] = key.split(',').map(Number),
      ci = WORLD.MARGIN + u * WORLD.PITCH + WORLD.S / 2, cj = WORLD.MARGIN + v * WORLD.PITCH + WORLD.S / 2, cd = Traffic._state().cdrones;
      return {{ n: cd.length, mine: cd.filter(d => d.plot === key && !d.leaving).length, leaving: cd.filter(d => d.leaving).length,
        far: Math.max(0, ...cd.filter(d => d.there).map(d => Math.hypot(d.i - ci, d.j - cj))), there: cd.filter(d => d.there).length, dist: cd.map(d => Math.hypot(d.i - ci, d.j - cj)) }}; }}""")
    c0 = crew()
    ok(f'with Traffic on, six of Claude\'s drones set off for the building Claude Code works on ({c0["mine"]} of {c0["n"]})', c0['n'] == 6 and c0['mine'] == 6 and js("() => Traffic.stats().crew") == 6)
    pg.wait_for_timeout(1500)
    c1d = crew()
    ok('and fly in towards it', sum(c1d['dist']) < sum(c0['dist']))
    pg.wait_for_timeout(12000)
    c2 = crew()
    ok(f'once there, they work round it, close by ({c2["there"]} there, farthest {c2["far"]:.1f} tiles)', c2['there'] == 6 and c2['far'] <= 2.5)
    alts = js("() => Traffic._state().cdrones.map(d => Math.round(d.altTo))")
    ok(f'at different heights ({alts})', len(set(alts)) > 1 and all(24 <= a <= 96 for a in alts))
    js("() => MapView.setCam({ x: 0, y: 160, z: 3 })"); pg.wait_for_timeout(300)
    ga = js(f"() => MapView.anchors('{gp}')")
    left = pg.query_selector('#mapWrap').bounding_box()['x']
    pg.screenshot(path=str(SH / '249-claude-drones.png'), clip={'x': max(0, left + ga['topX'] - 260), 'y': max(0, ga['topY'] - 160), 'width': 520, 'height': 440})
    js("() => { DB.city.drones = false; }"); pg.wait_for_timeout(1500)
    ok('with drones off in the city\'s settings, they head home', crew()['mine'] == 0 and crew()['leaving'] == 6)
    js("() => { DB.city.drones = true; }"); pg.wait_for_timeout(1500)
    ok('and back on, six come again', crew()['mine'] == 6)
    js("() => window.__cf.delete('a1.json')"); settle(); pg.wait_for_timeout(1200)
    ok('when the session stops working, they fly off the map', crew()['mine'] == 0 and js("() => Traffic.stats().crew") == 0)
    js("() => { for (const d of Traffic._state().cdrones) { d.i = d.to[0]; d.j = d.to[1]; d.hold = 0; } }"); pg.wait_for_timeout(600)
    ok('and are gone once off it', crew()['n'] == 0)
    js("() => { Traffic.setOn(false); MapView.invalidate(); }")
    js(S('a1', 'working', 'C:\\Users\\me\\garden\\src', task='Water the beds on time'))
    js("() => window.__cf.delete('f1.json')")
    settle()

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
    kept = js(f"() => getProject('{nc}').activity.filter(e => e.text === 'Claude Code finished: Fix the bubble').map(e => e.ref)")
    ok(f'a finish\'s line survives a reload with its mark, and is not written twice ({len(kept)})', len(kept) == 1 and kept[0].startswith('claude:c1:'))
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
