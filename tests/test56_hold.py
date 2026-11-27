"""Pass 56: bubbles held for a break, and Quiet (0.1.91, City as My Terminal, Brainstorm 1, Round 2, x2, and Round 1,
L2 and L3). A bubble that would open by itself waits while a panel is open, inside a building, while a field is typed
in or the tab is out of view, and opens at a break: closing the panel, stepping out of the building, coming back to
the tab; a pause in typing is not one. Quiet holds every bubble in News until it is turned off. The new moments: an
approval says so and opens by itself, a message from the city taken shows on the card only, and a send T3 could not
take because it is closed waits, its bubble carrying Open T3 and Send it. Waiting lasts until answered. First the
hooks and the T3 helper, run as Claude Code and Windows run them, then the city with a Claude folder held in memory."""
import json, os, pathlib, shutil, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:300] + ')'))

HOOK = ROOT / 'src' / 'setup' / 'nullovation-claude-status.py'
SETUP = ROOT / 'src' / 'setup' / 'nullovation-t3-links.py'
work = pathlib.Path(tempfile.mkdtemp(prefix='nc-hold-'))
home, local, claude = work / 'home', work / 'local', work / 'Claude-Hooks'
t3home = home / '.t3'
garden = work / 'Garden planner'
for d in (home / '.claude', local, claude, t3home / 'bin', t3home / 'userdata', garden):
    d.mkdir(parents=True, exist_ok=True)
(t3home / 'userdata' / 'environment-id').write_text('env-1234\n', encoding='utf-8')
(home / '.claude' / 'nullovation-city.json').write_text(json.dumps({'app': 'nullovation-city', 'kind': 'claude-folder', 'folder': str(claude)}), encoding='utf-8')
env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(local), NULLOVATION_QUIET='1', PYTHONUTF8='1')
env.pop('T3CODE_HOME', None)

# the fake t3: down, as T3 says when its app is closed
FAKE_T3 = work / 'fake_t3.py'
FAKE_T3.write_text(r'''import sys
sys.stdin.buffer.read()
sys.stderr.write('No running T3 Code server uses C:\\x\\.t3. Start T3 Code, then retry.\n'); sys.exit(1)
''', encoding='utf-8')
(t3home / 'bin' / 't3.cmd').write_text('@echo off\r\n' f'set "T3CODE_HOME={t3home}"\r\n' f'"{sys.executable}" "{FAKE_T3}" %*\r\nexit /b %ERRORLEVEL%\r\n', encoding='utf-8')

def hook(state, event, folder=claude):
    return subprocess.run([sys.executable, str(HOOK), 'hook', state, str(folder)], input=json.dumps(event).encode('utf-8'), env=env, capture_output=True, timeout=60)
def session(sid):
    f = claude / (sid + '.json')
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None

try:
    # ---------- the hooks: what a waiting session waits for ----------
    base = {'session_id': 'w-1', 'cwd': str(garden)}
    hook('working', {**base, 'hook_event_name': 'UserPromptSubmit', 'prompt': '# Task: Draw the beds\n\nProject: Garden planner'})
    hook('waiting', {**base, 'hook_event_name': 'PermissionRequest', 'tool_name': 'Bash'})
    ok('a permission request: waiting, for an approval', session('w-1')['state'] == 'waiting' and session('w-1')['wait'] == 'approval', session('w-1'))
    time.sleep(0.01)
    hook('working', {**base, 'hook_event_name': 'PostToolUse'})
    ok('working again: no longer waiting for anything', 'wait' not in session('w-1'), session('w-1'))
    hook('waiting', {**base, 'hook_event_name': 'PreToolUse', 'tool_name': 'AskUserQuestion'})
    ok('a question: waiting, for a question', session('w-1')['wait'] == 'question')
    hook('waiting', {**base, 'hook_event_name': 'Notification', 'notification_type': 'elicitation_dialog'})
    ok('an MCP form: waiting, for a form', session('w-1')['wait'] == 'form')
    hook('waiting', {**base, 'hook_event_name': 'Notification', 'notification_type': 'permission_prompt'})
    ok('a permission prompt: an approval', session('w-1')['wait'] == 'approval')
    for f in claude.iterdir():
        if f.is_file(): f.unlink()

    # ---------- the T3 helper: T3 not running is marked ----------
    (claude / 't3').mkdir(exist_ok=True)
    send = {'app': 'nullovation-city', 'kind': 't3-send', 'version': 1, 'id': 'down0001', 'at': int(time.time() * 1000), 'project': 'Garden planner',
            'folder': str(garden), 'title': 'Draw the beds', 'message': '# Task: Draw the beds'}
    (claude / 't3' / 'send-down0001.json').write_text(json.dumps(send), encoding='utf-8')
    subprocess.run([sys.executable, str(SETUP), 'open', 'nullovation-t3:send/down0001'], env=env, capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    a = json.loads((claude / 't3' / 'down0001.done.json').read_text(encoding='utf-8'))
    ok('the helper marks T3 not running, so the city can hold the send', a['ok'] is False and a.get('down') is True and a['error'] == 'T3 Code is not running. Open it, then send again.', a)
    shutil.rmtree(claude / 't3')

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
  getFileHandle: async (n, o) => { if (!window.__sub.has(n) && !(o && o.create)) fail('NotFoundError'); return subfile(n); },
  removeEntry: async n => { window.__sub.delete(n); },
  entries: async function* () { yield ['README-nullovation-city.txt', { kind: 'file', name: 'README-nullovation-city.txt', getFile: async () => new File(['x'], 'README-nullovation-city.txt') }];
    for (const k of [...window.__sub.keys()]) if (!k.includes('/')) yield [k, subfile(k)]; } };
window.showDirectoryPicker = async () => window.__cdir;
window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (/^(nullovation-t3|t3code|claude|claude-cli):/i.test(href)) { window.__opened.push(href); return; } return anchorClick.call(this); };
/* the tab out of view, at the test's word */
window.__hidden = false;
Object.defineProperty(Document.prototype, 'hidden', { get() { return window.__hidden; }, configurable: true });
"""
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        ctx.add_init_script(TEST_CITY)
        ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t56')) { sessionStorage.setItem('nc-t56', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
        ctx.add_init_script(FAKE)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.goto(FILE); pg.wait_for_timeout(2000)
        ev = pg.evaluate
        gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
        ev(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: 'l-h', label: '', url: {json.dumps(str(garden))}, icon: 'folder', shortcut: true }});
            const l = blankLeader({{ name: 'Fern Rowe', role: 'Head Gardener' }}); DB.leaders.push(l); setLeader(p, l.id); window.changed(p); }}""")
        other = ev("() => DB.projects.find(p => p.name !== 'Garden planner').id")      # news comes from the other building: a building's own is read by its cards
        task = ev(f"() => getProject('{gp}').todos.find(t => !t.done).text")
        tid = ev(f"() => getProject('{gp}').todos.find(t => !t.done).id")
        ev("() => { News._test.forget(); News._test.sayMs(60000); document.querySelectorAll('#gusSay, #pxSay').forEach(e => e.hidden = true); }")
        ev("() => { if (Gus.isSaying()) Gus.hush(); }")
        says = lambda: ev("() => { const b = document.querySelector('#ldSay'); return b && !b.hidden ? b.querySelector('#ldSayText').textContent : ''; }")
        # the page's type and its task line, the building then the task (0.1.96)
        say_page = lambda: ev("() => { const b = document.querySelector('#ldSay'); return b && !b.hidden ? [b.dataset.type, (b.querySelector('#ldSayWhere') || {}).textContent || ''] : null; }")
        close_say = lambda: ev("() => { News.hide(); }")
        n = [0]
        def news(what='Bed layout'):
            """A wizard round Claude attached: news that opens a bubble by itself (what Claude added no longer does, 0.1.96)."""
            n[0] += 1
            return ev(f"""() => {{ const p = getProject('{other}'), t = p.todos.find(t => !t.done);
              return News.add(p, 'round', {{ task: t.text, round: {json.dumps(what)} + ' {n[0]}' }}, {{ ref: {{ tid: t.id }} }}).id; }}""")
        why = lambda: ev("() => Hold.why()")
        ROUND = 'Claude attached a wizard round to this task: Bed layout'

        # ---------- on the map, nothing holds ----------
        ok('on the map, nothing holds a bubble', why() == '', why())
        ev(f"() => News.add(getProject('{other}'), 'added', {{ what: 'a note, Bed layout' }})"); pg.wait_for_timeout(1200)
        ok('what Claude added no longer opens a bubble by itself: it waits in News (0.1.96)', says() == '' and ev("() => News.items().some(it => it.moment === 'added')"), says())
        ev("() => News._test.forget()")
        news(); pg.wait_for_timeout(300)
        ok('news that opens by itself (a round attached) opens at once, as before', says().startswith(ROUND), says())
        close_say(); pg.wait_for_timeout(200)

        # ---------- inside a building: held until stepping out (L2, building) ----------
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
        ok('inside a building, it holds', why() == 'panel', why())
        news(); pg.wait_for_timeout(1500)
        ok('news while inside a building waits', says() == '' and ev("() => !document.querySelector('#sbNews').hidden"), says())
        pg.screenshot(path=str(SHOTS / '560-hold-inside.png'))
        ev("() => { FullView.close(); Bubble.close(); }"); pg.wait_for_timeout(1000)
        ok('stepping out back to the map is a break: it opens', says().startswith(ROUND), says())
        close_say(); pg.wait_for_timeout(200)

        # ---------- a panel: held until it closes (L2, panel) ----------
        ev("() => Settings.open('look')"); pg.wait_for_timeout(200)
        news(); pg.wait_for_timeout(1200)
        ok('with Settings open, it waits', says() == '' and why() == 'panel', (says(), why()))
        ev("() => Settings.close()"); pg.wait_for_timeout(1000)
        ok('closing the panel is a break: it opens', says().startswith(ROUND), says())
        close_say(); pg.wait_for_timeout(200)
        ev("() => Reports.open()"); pg.wait_for_timeout(200)
        ok('Reports holds too', why() == 'panel')
        ev("() => Reports.close()"); pg.wait_for_timeout(100)

        # ---------- typing: a pause is not a break (L2, typing) ----------
        pg.click('#search'); pg.keyboard.type('bed'); pg.wait_for_timeout(100)
        ok('typing in a field holds', why() == 'typing', why())
        news(); pg.wait_for_timeout(3500)
        ok('a pause of three seconds in typing is not a break: it still waits', says() == '', says())
        pg.keyboard.press('Control+A'); pg.keyboard.press('Delete')
        ev("() => document.activeElement.blur()"); pg.wait_for_timeout(1000)
        ok('leaving the field, it opens', says().startswith(ROUND), says())
        close_say(); pg.wait_for_timeout(200)

        # ---------- the tab out of view (L2, tab) ----------
        ev("() => { window.__hidden = true; }")
        ok('the tab out of view holds', why() == 'away', why())
        news(); pg.wait_for_timeout(1200)
        ok('news while the tab is out of view waits', says() == '')
        ev("() => { window.__hidden = false; document.dispatchEvent(new Event('visibilitychange')); }"); pg.wait_for_timeout(1000)
        ok('coming back to the tab is a break: it opens', says().startswith(ROUND), says())
        close_say(); pg.wait_for_timeout(200)

        # ---------- a click is never held ----------
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
        news(); pg.wait_for_timeout(300)
        ev("() => { FullView.close(); Bubble.close(); }"); pg.wait_for_timeout(100)
        close_say(); pg.wait_for_timeout(100)
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(300)
        news(); pg.wait_for_timeout(300)
        pg.click('#newsList .news-face'); pg.wait_for_timeout(300)
        ok('a click on a face opens its bubble, inside a building too', says().startswith(ROUND), says())
        close_say(); ev("() => { FullView.close(); Bubble.close(); }"); pg.wait_for_timeout(600); close_say(); pg.wait_for_timeout(200)

        # ---------- Gus: his word by himself waits too ----------
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(300)
        ev("() => Gus.say('The city is getting dirty! We should do something about it.')"); pg.wait_for_timeout(600)
        ok('Gus\'s word by himself waits inside a building', not ev("() => Gus.isSaying()") and ev("() => Gus.waiting()"))
        ev("() => { FullView.close(); Bubble.close(); }"); pg.wait_for_timeout(900)
        ok('and he says it at the break', ev("() => Gus.isSaying()") and not ev("() => Gus.waiting()"))
        ev("() => Gus.hush()"); pg.wait_for_timeout(600); close_say()

        # ---------- Quiet ----------
        ok('the News head has the Quiet switch, off', ev("() => document.querySelector('#newsQuiet').getAttribute('aria-pressed')") == 'false')
        pg.click('#newsQuiet'); pg.wait_for_timeout(200)
        ok('Quiet on: pressed, kept in this browser, and it says so', ev("() => document.querySelector('#newsQuiet').getAttribute('aria-pressed')") == 'true'
           and ev("() => localStorage.getItem('nullovation-city:quiet')") == '1' and 'Quiet: bubbles wait in News' in ev("() => document.querySelector('#toast').textContent"))
        ok('it holds on the map', why() == 'quiet')
        news(); pg.wait_for_timeout(1500)
        ok('news under Quiet waits in News, its face counting', says() == '' and ev("() => document.querySelectorAll('#newsList .news-tile').length") >= 1)
        pg.screenshot(path=str(SHOTS / '561-quiet.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 500})
        ev("() => Gus.say('Fine. Good work.')"); pg.wait_for_timeout(600)
        ok('Gus waits under Quiet too', not ev("() => Gus.isSaying()"))
        ev("() => Settings.open('look')"); pg.wait_for_timeout(200)
        ok('Settings, Look has Quiet, checked, with its dot', ev("() => document.querySelector('#optQuiet').checked") and ev("() => document.querySelector('[data-set=\"quiet\"]').classList.contains('changed')"))
        pg.click('#optQuiet'); pg.wait_for_timeout(100)
        ok('unchecked there, Quiet is off', not ev("() => Hold.quiet()") and ev("() => document.querySelector('#newsQuiet').getAttribute('aria-pressed')") == 'false')
        ev("() => Settings.close()"); pg.wait_for_timeout(1200)
        ok('Quiet off, at the break, what waited opens', says().startswith(ROUND) or ev("() => Gus.isSaying()"), (says(), ev("() => Gus.isSaying()")))
        ev("() => { if (Gus.isSaying()) Gus.hush(); }"); pg.wait_for_timeout(700); close_say(); pg.wait_for_timeout(700); close_say()
        ev("() => { if (Gus.isSaying()) Gus.hush(); }"); pg.wait_for_timeout(300)
        # the section in view while Quiet is on, with nothing in it
        ev("() => { News._test.forget(); News.renderSection(); }")
        ok('with no news and Quiet off, the section hides', ev("() => document.querySelector('#sbNews').hidden"))
        ev("() => Hold.setQuiet(true)"); pg.wait_for_timeout(100)
        ok('with Quiet on it stays in view, saying news waits there', not ev("() => document.querySelector('#sbNews').hidden") and ev("() => document.querySelector('.news-quiet-note').textContent") == 'Quiet: news waits here.')
        pg.reload(); pg.wait_for_timeout(2000)
        ok('Quiet is kept across a reload', ev("() => Hold.quiet()") and ev("() => document.querySelector('#newsQuiet').getAttribute('aria-pressed')") == 'true')
        ev("() => Hold.setQuiet(false)"); ev("() => { News._test.forget(); News._test.sayMs(60000); if (Gus.isSaying()) Gus.hush(); document.querySelectorAll('#pxSay').forEach(e => e.hidden = true); }")
        pg.wait_for_timeout(500); close_say()

        # ---------- the lines ----------
        ok('an approval says so', ev(f"() => leaderSay('waiting', {{ task: 'Draw the beds', wait: 'approval' }})") == 'Claude needs your OK on Draw the beds.')
        ok('a question keeps its line', ev(f"() => leaderSay('waiting', {{ task: 'Draw the beds', wait: 'question' }})") == 'Claude is waiting for you on Draw the beds.')
        ok('a message from the city taken', ev(f"() => leaderSay('working', {{ task: 'Draw the beds', ago: 'just now', took: true }})") == 'Claude took your message on Draw the beds. Started just now.')
        ok('waiting lasts until answered', ev("() => ClaudeWork.LASTS.waiting === Infinity"))

        # ---------- sessions: an approval opens by itself; a message taken shows on the card only ----------
        ev("() => Settings.open('links')"); pg.wait_for_timeout(200)
        pg.click('#btnClaudeConnect'); pg.wait_for_timeout(500)
        ev("() => Settings.close()"); pg.wait_for_timeout(300)
        now = int(time.time() * 1000)
        def put_session(sid, **o):
            d = {'v': 1, 'app': 'nullovation-city', 'kind': 'claude-session', 'session': sid, 'cwd': str(garden), 'task': task, 'project': 'Garden planner',
                 'at': int(time.time() * 1000), 'since': int(time.time() * 1000), 'started': int(time.time() * 1000)}
            d.update(o)
            ev("([k, text]) => { window.__sub.set(k, { text, t: Date.now() + (window.__ct++) }); }", [sid + '.json', json.dumps(d)])
        put_session('s-ok', state='waiting', event='PermissionRequest', wait='approval', at=now - 9 * 3600e3, since=now - 9 * 3600e3)
        ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(1500)
        ok('a session waiting 9 hours still shows as waiting (no longer let go after 8)', ev(f"() => ClaudeWork.sessionsOf(getProject('{gp}')).some(s => s.session === 's-ok' && s.state === 'waiting' && s.wait === 'approval')"))
        ok('an approval opens a bubble by itself, saying Claude needs your OK, the task in its own line (0.1.96)', says().startswith('Claude needs your OK on this task.')
           and say_page() == ['approval', 'Garden planner·' + task], (says(), say_page()))
        pg.screenshot(path=str(SHOTS / '562-approval.png'))
        close_say(); pg.wait_for_timeout(200)
        ev("() => { window.__sub.delete('s-ok.json'); }"); ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(800)
        # a send into the task's thread, then its session starting on it
        ev(f"""() => {{ const t = getProject('{gp}').todos.find(t => t.id === '{tid}'); t.threads = [{{ id: 'cli:t-1', env: 'env-1234', agent: 'Opus 5.5', kind: 'build', title: t.text, at: Date.now() - 60000, last: Date.now() - 2000 }}]; }}""")
        put_session('s-took', state='working', event='UserPromptSubmit', since=int(time.time() * 1000), at=int(time.time() * 1000))
        ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(1200)
        ok('a message the city sent, taken: no bubble', says() == '', says())
        ev(f"() => Bubble.open('{gp}')"); pg.wait_for_timeout(300)
        card = ev("() => [...document.querySelectorAll('.ld-line .ld-says')].map(e => e.textContent)")
        tline = lambda: ev("() => [...document.querySelectorAll('#bubble .lc-tline')].map(e => e.textContent)")
        ok('the status card says Claude took your message on this task, the task in its own line (0.1.96)', any(c.startswith('Claude took your message on this task. Started') for c in card)
           and tline() == [task], (card, tline()))
        ev("() => Bubble.close()")
        ev(f"""() => {{ const t = getProject('{gp}').todos.find(t => t.id === '{tid}'); t.threads[0].last = Date.now() - 3600e3; }}""")
        ev(f"() => Bubble.open('{gp}')"); pg.wait_for_timeout(300)
        card = ev("() => [...document.querySelectorAll('.ld-line .ld-says')].map(e => e.textContent)")
        ok('work that began long after the last send is just working', any(c.startswith('Claude is working on this task.') for c in card) and tline() == [task], (card, tline()))
        ev("() => Bubble.close()")
        ev("() => { window.__sub.delete('s-took.json'); }"); ev("() => ClaudeWork.poll()"); pg.wait_for_timeout(500)

        # ---------- a send while T3 is closed: held, with Open T3 and Send it ----------
        def t3_answer(extra):
            s = ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))[0]")
            ev("([s, extra]) => { window.__sub.delete('t3/send-' + s.id + '.json'); window.__sub.set('t3/' + s.id + '.done.json', { text: JSON.stringify(Object.assign({ app: 'nullovation-city', kind: 't3-sent', version: 1, id: s.id }, extra)), t: Date.now() }); }", [s, extra])
            return s
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
        pg.click(f'li.task[data-id="{tid}"] .task-title'); pg.wait_for_timeout(300)
        pg.locator('#pvTaskClaude').scroll_into_view_if_needed(); pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        first = t3_answer({'ok': False, 'error': 'T3 Code is not running. Open it, then send again.', 'down': True})
        pg.wait_for_timeout(1500)
        ok('with the task panel open there is no room for a bubble: a toast says it waits in News, with Open T3', ev("() => document.querySelector('#toast').textContent").startswith('T3 Code is not running, so ' + task + ' waits in News.')
           and ev("() => [...document.querySelectorAll('#toast .toast-act')].map(b => b.textContent)") == ['Open T3'])
        ok('and its leader holds it in News', ev("() => News.items().some(it => it.moment === 't3closed')"))
        ev("() => { window.__opened.length = 0; }")
        pg.click('#toast .toast-act'); pg.wait_for_timeout(100)
        ok('Open T3 opens the task\'s thread in T3, which starts T3', ev("() => window.__opened.slice()") == ['t3code://threads/env-1234/cli%3At-1'], ev("() => window.__opened.slice()"))
        ev("() => { FullView.close(); Bubble.close(); }"); pg.wait_for_timeout(1200)
        ok('out of the building, its bubble opens: T3 is closed, so it waits, Critical, the task in its own line (0.1.96)', says().startswith('T3 is closed, so your message for this task waits to be sent.')
           and say_page() == ['critical', 'Garden planner·' + task], (says(), say_page()))
        acts = ev("() => [...document.querySelectorAll('#ldSayActs .btn')].map(b => b.textContent)")
        ok('with Open T3 and Send it, and Go to it kept: no Check T3 on it (Check T3, Round 1, M1)', acts == ['Open T3', 'Send it', 'Go to it'], acts)
        pg.screenshot(path=str(SHOTS / '563-t3-closed.png'))
        ev("() => { window.__opened.length = 0; }")
        pg.click('#ldSay .btn:text-is("Send it")'); pg.wait_for_timeout(400)
        again = ev("() => [...window.__sub].filter(([k]) => /^t3\\/send-/.test(k)).map(([k, f]) => JSON.parse(f.text))")
        ok('Send it sends it again, as it was: the same copy, into the same thread', len(again) == 1 and again[0]['message'] == first['message'] and again[0].get('thread') == first.get('thread') and again[0]['id'] != first['id'], again)
        ok('and its news goes', not ev("() => News.items().some(it => it.moment === 't3closed')"))
        t3_answer({'ok': True, 'thread': 'cli:t-1', 'env': 'env-1234', 'continued': True}); pg.wait_for_timeout(1400)
        ok('once T3 takes it, its leader says it was sent to its thread', ('Sent to its T3 thread: ' + task) in ev("() => document.querySelector('#toast').textContent"))
        close_say(); pg.wait_for_timeout(200)
        # room for the bubble: it answers your click at once, even inside the building
        ev(f"() => {{ const t = getProject('{gp}').todos.find(t => t.id === '{tid}'); delete t.threads; }}")
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(400)
        ok('inside the building, with room beside it', ev("() => sayRoom()") and why() == 'panel')
        pg.locator('#pvNextClaude').scroll_into_view_if_needed(); pg.click('#pvNextClaude'); pg.wait_for_timeout(200)
        pg.click('.oc-panel .oc-tile[data-kind="t3"]'); pg.wait_for_timeout(300)
        news()                                         # other news, held
        t3_answer({'ok': False, 'error': 'T3 Code is not running. Open it, then send again.', 'down': True}); pg.wait_for_timeout(1500)
        ok('a send T3 could not take answers your click at once, beside the building', says().startswith('T3 is closed, so your message for this task waits to be sent.')
           and say_page() == ['critical', 'Garden planner·' + task], (says(), say_page()))
        ok('while the other news stays held', ev("() => News._test.bubble().ids.length") == 1)
        ev("() => { window.__opened.length = 0; }")
        pg.click('#ldSay .btn:text-is("Open T3")'); pg.wait_for_timeout(100)
        ok('a task with no thread: Open T3 opens T3 on a new thread', ev("() => window.__opened.slice()") == ['t3code://new'], ev("() => window.__opened.slice()"))
        close_say(); ev("() => { FullView.close(); Bubble.close(); }"); pg.wait_for_timeout(1200); close_say()
        # held sends live while the page does
        pg.reload(); pg.wait_for_timeout(2000)
        ok('after a reload the held send is gone, and so is its news', not ev("() => News.items().some(it => it.moment === 't3closed')"))
        b.close()
finally:
    shutil.rmtree(work, ignore_errors=True)

real = [e for e in errors if 'Failed to load resource' not in e]
ok('no console errors', not real)
for e in real[:10]: print('  ', e)
