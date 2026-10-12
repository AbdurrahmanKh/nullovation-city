"""Nullovation City: Claude Code at work.

Lets the city show a bubble over a building while Claude Code works in one of its folders, and when it needs you or
has finished. Claude Code runs this script from hooks in your user settings (~/.claude/settings.json), which apply in
the terminal, in VS Code and JetBrains, and in the Code tab of the Claude desktop app. Each hook writes one small
JSON file per session into a folder; the city reads that folder, once you connect it in Settings, Links.

    double-click it                                               ask which folder, then add the hooks
    python nullovation-claude-status.py --install --folder PATH   add the hooks, writing to that folder
    python nullovation-claude-status.py --install                 the same, keeping the folder already set
    python nullovation-claude-status.py --uninstall               take the hooks out again
    python nullovation-claude-status.py --status                  list what the folder holds now

Run with no arguments (a double-click, when .py files open with Python), it asks which folder Claude Code should
write to, starting at the one already set, then installs and waits for Enter before the window closes, so the result
stays on screen; --no-pause skips the wait. Running it again moves the hooks to the folder picked.

--install copies this script to ~/.claude/hooks/nullovation-city-status.py and points the hooks there, so the file
you downloaded can be deleted afterwards. It keeps every other setting and hook as it is, saves the settings file as
it was to settings.json.nullovation-backup first, and can run again safely: it replaces its own hooks, never doubles
them. The folder is the one picked or named, else the one already set, else ~/Nullovation City/Claude; Chrome cannot
open folders inside AppData. It leaves README-nullovation-city.txt in the folder, which is how the city knows the
folder it watches is the one the hooks write to.

The hooks never slow Claude down (they run in the background), never print anything Claude would read, and never
block or change anything Claude does: they only write the files. Nothing leaves this computer.

Each file is <session id>.json:
    state    working, waiting (a permission or a question for you), done (your turn), failed (an API error),
             idle (no longer working, such as after an interrupt) or ended (the session closed)
    cwd      the folder Claude Code runs in; the city matches it to a project's folder links
    project  the "Project:" line of a copy from the city, when the prompt was one
    task     the title of that copy (# Task:, # Note:, # Milestone:), kept for the whole session
    ask      the first line of the latest prompt
    reply    the start of Claude's last reply
    at, since, started   milliseconds since 1970: the last event, when this state began, when the session began
"""
import json, os, pathlib, shutil, sys, time

APP = 'nullovation-city'
NAME = 'nullovation-city-status.py'              # the installed copy's name, which marks the hooks as ours
STALE_DAYS = 3                                   # session files older than this are cleared at the next session start

# hook event -> [(matcher or None, state)]
HOOKS = {
    'SessionStart': [(None, 'start')],
    'UserPromptSubmit': [(None, 'working')],
    'PreToolUse': [('AskUserQuestion', 'waiting')],
    'PostToolUse': [(None, 'working')],
    'PermissionRequest': [(None, 'waiting')],
    'Notification': [('permission_prompt|elicitation_dialog', 'waiting'), ('idle_prompt', 'idle')],
    'Stop': [(None, 'done')],
    'StopFailure': [(None, 'failed')],
    'SessionEnd': [(None, 'ended')],
}
STATES = {'start', 'working', 'waiting', 'done', 'failed', 'idle', 'ended'}
MARK = 'README-nullovation-city.txt'             # left in the folder by the setup; the city looks for it


def home():
    return pathlib.Path(os.path.expanduser('~'))


def default_folder():
    return home() / 'Nullovation City' / 'Claude'


def settings_path():
    return home() / '.claude' / 'settings.json'


def installed_path():
    return home() / '.claude' / 'hooks' / NAME


def current_folder():
    """The folder the installed hooks write to, or None when they are not installed."""
    try:
        hooks = load_settings(settings_path()).get('hooks') or {}
        for groups in hooks.values():
            for g in groups if isinstance(groups, list) else []:
                for h in (g.get('hooks') or []) if isinstance(g, dict) else []:
                    if ours(h) and len(h.get('args') or []) >= 4:
                        return pathlib.Path(h['args'][3])
    except Exception:
        pass
    return None


def ask_folder(start):
    """Asks which folder Claude Code should write to: a folder picker, or a typed path when there is no picker.
    Returns None when the question is cancelled."""
    print('Which folder should Claude Code write its session notes to?')
    print('Pick the folder Nullovation City watches (Settings, Links, Claude Code at work), or a new one.')
    if not os.environ.get('NULLOVATION_NO_GUI'):
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            got = filedialog.askdirectory(parent=root, initialdir=str(start), mustexist=False,
                                          title='Nullovation City: the folder for Claude Code\'s session notes')
            root.destroy()
            return pathlib.Path(got) if got else None
        except Exception:
            pass                                   # no picker on this Python: ask in the window instead
    try:
        typed = input('Paste the folder\'s path, or press Enter for ' + str(start) + ': ').strip().strip('"')
    except (EOFError, KeyboardInterrupt):
        return None
    return pathlib.Path(typed) if typed else pathlib.Path(start)


def now_ms():
    return int(time.time() * 1000)


def one_line(text, n):
    for line in str(text or '').splitlines():
        line = ' '.join(line.split())
        if line:
            return line if len(line) <= n else line[:n - 3].rstrip() + '...'
    return ''


def read_copy(prompt):
    """The project and title of a copy from the city: '# Task: <title>' then 'Project: <name>' near the top."""
    lines = str(prompt or '').splitlines()[:12]
    task = project = ''
    for line in lines:
        s = line.strip()
        for head in ('# Task:', '# Note:', '# Milestone:'):
            if not task and s.startswith(head):
                task = one_line(s[len(head):], 160)
        if not project and s.startswith('Project:'):
            project = one_line(s[len('Project:'):], 160)
    return project, task


# ---------- the hook: one event in, one file out ----------

def log_error(folder, message):
    try:
        path = pathlib.Path(folder) / 'hook-errors.log'
        if path.exists() and path.stat().st_size > 64 * 1024:
            path.unlink()
        with open(path, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + message + '\n')
    except Exception:
        pass


def write_atomic(path, data):
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    for attempt in range(8):                       # Windows refuses the swap while a reader holds the file; try again
        try:
            os.replace(str(tmp), str(path))
            return
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
    try:
        tmp.unlink()
    except Exception:
        pass
    raise PermissionError('could not replace ' + path.name)


def prune(folder):
    cutoff = time.time() - STALE_DAYS * 86400
    for f in pathlib.Path(folder).iterdir():
        try:
            if f.suffix == '.json' and f.stat().st_mtime < cutoff:
                f.unlink()
            elif f.name.endswith('.tmp') and f.stat().st_mtime < time.time() - 3600:
                f.unlink()
        except Exception:
            pass


def hook(state, folder):
    at = now_ms()
    folder = pathlib.Path(folder)
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', 'replace')
        event = json.loads(raw) if raw.strip() else {}
        session = str(event.get('session_id') or '').strip()
        if not session or any(c in session for c in '/\\:*?"<>|') or state not in STATES:
            log_error(folder, 'skipped an event without a usable session id: ' + one_line(raw, 200))
            return
        folder.mkdir(parents=True, exist_ok=True)
        if state == 'start':
            prune(folder)
        path = folder / (session + '.json')
        old = {}
        if path.exists():
            try:
                old = json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                old = {}
        if isinstance(old.get('at'), (int, float)) and old['at'] > at:
            return                                 # a later event already landed; the hooks run in the background
        was = old.get('state')
        if state == 'start':
            state = was if was in ('working', 'waiting') else 'idle'
        elif state == 'idle' and was not in ('working', 'waiting'):
            state = was or 'idle'                  # idle only ends a stretch of work that never reported its end
        data = dict(old)
        data.update({'v': 1, 'app': APP, 'kind': 'claude-session', 'session': session, 'state': state,
                     'event': str(event.get('hook_event_name') or ''), 'at': at})
        data.setdefault('started', at)
        if state != was or 'since' not in data:
            data['since'] = at
        if event.get('cwd'):
            data['cwd'] = str(event['cwd'])
        entry = os.environ.get('CLAUDE_CODE_ENTRYPOINT')
        if entry:
            data['entry'] = entry
        if event.get('hook_event_name') == 'UserPromptSubmit' and event.get('prompt'):
            project, task = read_copy(event['prompt'])
            if project:
                data['project'] = project
            if task:
                data['task'] = task
            data['ask'] = one_line(event['prompt'], 160)
            data.pop('reply', None)
        if state == 'done' and event.get('last_assistant_message'):
            data['reply'] = one_line(event['last_assistant_message'], 240)
        write_atomic(path, data)
    except Exception as e:                         # never stop Claude Code over the city: note it and go on
        log_error(folder, state + ': ' + type(e).__name__ + ': ' + str(e))


# ---------- install and uninstall ----------

def ours(handler):
    if not isinstance(handler, dict):
        return False
    parts = [str(handler.get('command') or '')] + [str(a) for a in (handler.get('args') or [])]
    return any(p.replace('\\', '/').endswith('/' + NAME) or p == NAME for p in parts)


def strip_ours(hooks):
    """The hooks without ours, dropping groups and events that end up empty."""
    out = {}
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            out[event] = groups
            continue
        kept = []
        for g in groups:
            if isinstance(g, dict) and isinstance(g.get('hooks'), list):
                hs = [h for h in g['hooks'] if not ours(h)]
                if hs:
                    kept.append(dict(g, hooks=hs))
                elif not g['hooks']:
                    kept.append(g)
            else:
                kept.append(g)
        if kept:
            out[event] = kept
    return out


def load_settings(path):
    if not path.exists():
        return {}
    text = path.read_text(encoding='utf-8-sig')
    if not text.strip():
        return {}
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError('it does not hold a JSON object')
    return data


def save_settings(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.nullovation-tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(str(tmp), str(path))


def handler(state, script, folder):
    return {'type': 'command', 'command': sys.executable, 'args': [str(script), 'hook', state, str(folder)],
            'async': True, 'timeout': 10}


def install(folder):
    folder = pathlib.Path(folder).expanduser().resolve()
    path = settings_path()
    try:
        settings = load_settings(path)
    except Exception as e:
        print('Your Claude Code settings file could not be read, so nothing changed:')
        print('  ' + str(path))
        print('  ' + type(e).__name__ + ': ' + str(e))
        print('Fix the file (it must be valid JSON), then run this again.')
        return 1
    if path.exists():
        shutil.copy2(str(path), str(path.with_name(path.name + '.nullovation-backup')))
    script = installed_path()
    script.parent.mkdir(parents=True, exist_ok=True)
    if pathlib.Path(__file__).resolve() != script.resolve():
        shutil.copyfile(__file__, str(script))
    folder.mkdir(parents=True, exist_ok=True)
    try:
        (folder / MARK).write_text(
            'Claude Code writes here for Nullovation City: one small file per session, from the hooks the setup\n'
            'added to ' + str(path) + '.\n\n'
            'In Nullovation City, Settings, Links, Claude Code at work watches this folder.\n'
            'To write somewhere else, double-click the setup again and pick another folder.\n'
            'To take the hooks out: python "' + str(script) + '" --uninstall\n', encoding='utf-8')
    except Exception:
        pass
    hooks = settings.get('hooks') if isinstance(settings.get('hooks'), dict) else {}
    hooks = strip_ours(hooks)
    for event, pairs in HOOKS.items():
        groups = hooks.setdefault(event, [])
        for matcher, state in pairs:
            g = {'hooks': [handler(state, script, folder)]}
            if matcher:
                g = {'matcher': matcher, **g}
            groups.append(g)
    settings['hooks'] = hooks
    save_settings(path, settings)
    print('Claude Code at work is set up.')
    print('  Hooks added to ' + str(path) + ' (the old file is beside it as settings.json.nullovation-backup).')
    print('  The hooks run ' + str(script))
    print('  Sessions are written to this folder:')
    print('    ' + str(folder))
    print('In Nullovation City, Settings, Links, Claude Code at work must watch that same folder.')
    if os.name == 'nt':
        try:
            import subprocess
            subprocess.run(['clip'], input=str(folder).encode('utf-16-le'), check=True)
            print('The folder\'s path is on your clipboard: paste it into the picker\'s address bar.')
        except Exception:
            pass
    print('Claude Code picks the hooks up by itself; sessions already open may need a restart.')
    return 0


def uninstall():
    path = settings_path()
    try:
        settings = load_settings(path)
    except Exception as e:
        print('Your Claude Code settings file could not be read, so nothing changed: ' + type(e).__name__ + ': ' + str(e))
        return 1
    hooks = settings.get('hooks')
    if isinstance(hooks, dict):
        hooks = strip_ours(hooks)
        if hooks:
            settings['hooks'] = hooks
        else:
            settings.pop('hooks', None)
        save_settings(path, settings)
    script = installed_path()
    if script.exists() and pathlib.Path(__file__).resolve() != script.resolve():
        script.unlink()
    print('Took the Nullovation City hooks out of ' + str(path) + '. Every other setting is as it was.')
    print('The folder of session files stays; delete it if you like.')
    return 0


def status(folder):
    folder = pathlib.Path(folder).expanduser()
    files = sorted(folder.glob('*.json')) if folder.is_dir() else []
    if not files:
        print('No sessions in ' + str(folder) + ' yet.')
        return 0
    for f in files:
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            continue
        ago = max(0, (now_ms() - int(d.get('at') or 0)) // 60000)
        print('%-8s %4d min ago  %s  %s' % (d.get('state'), ago, d.get('cwd', ''), d.get('task') or d.get('ask') or ''))
    return 0


def main(argv):
    if argv[:1] == ['hook']:                       # from Claude Code: hook <state> <folder>
        if len(argv) >= 3:
            hook(argv[1], argv[2])
        return 0                                   # a hook always succeeds, whatever happened
    folder = current_folder() or default_folder()   # running again keeps the folder already set
    if '--folder' in argv:
        i = argv.index('--folder')
        if i + 1 >= len(argv):
            print('--folder needs a path.')
            return 2
        folder = pathlib.Path(argv[i + 1])
    if '--help' in argv or '-h' in argv:
        print('\n\n'.join(part for part in __doc__.strip().split('\n\n') if 'nullovation-claude-status.py' in part))
        return 0
    if '--uninstall' in argv:
        code = uninstall()
    elif '--status' in argv:
        code = status(folder)
    else:                                          # --install, or nothing at all, as from a double-click
        asking = '--ask' in argv or (not argv and sys.stdin is not None and sys.stdin.isatty())
        picked = ask_folder(folder) if asking else folder
        if picked is None:
            print('Nothing changed.')
            code = 0
        else:
            code = install(picked)
    if '--no-pause' not in argv and sys.stdin is not None and sys.stdin.isatty():
        try:
            input('\nPress Enter to close.')
        except (EOFError, KeyboardInterrupt):
            pass
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
