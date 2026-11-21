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
            'thread': thread}, None


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
    answer = send_to_thread(s) if s['thread'] else start_thread(s)
    write_answer(folder, ident, answer)
    try:
        taken.unlink()
    except Exception:
        pass
    note(('Sent ' if answer.get('ok') else 'Not sent ') + ident + (' to T3 thread ' + s['thread'] if s['thread'] else ' to T3 in ' + s['folder']) + ': '
         + (answer.get('thread') or answer.get('error') or ''))
    return 0 if answer.get('ok') else 1


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


README = """This folder is how Nullovation City sends tasks to T3 Code.

The city writes a send here as send-<id>.json, then follows a nullovation-t3: link that names it. The helper the
T3 setup added takes it, starts a T3 thread in the building's folder with the task sent, and writes what T3 said
back as <id>.done.json, which the city reads and clears. Nothing here needs keeping.
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
    if dry_run:
        print('Would copy this script to ' + str(target))
        print('Would add HKEY_CURRENT_USER\\Software\\Classes\\' + SCHEME + ' with the command:')
        print('  ' + command)
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
    try:
        installed_path().unlink()
    except Exception:
        pass
    print('Removed. The city\'s T3 tile does nothing on this PC until the setup runs again.')
    return 0


def status():
    folder = claude_folder()
    found = t3_command()
    print('Link type: ' + (registered() or 'not added'))
    print('Claude folder: ' + (str(folder) if folder else 'not found (run the Claude Code at work setup first)'))
    print('T3\'s command: ' + (found[0][0] if found else 'not found (open T3 Code once)'))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[0] == 'open':
        return open_link(argv[1])
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
