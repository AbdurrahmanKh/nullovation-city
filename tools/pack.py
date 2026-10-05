"""Packs this folder into the source archive that carries Nullovation City between claude.ai chats and Claude Code,
and brings this folder up to an archive that came back from a chat.

    python3 tools/pack.py                           write nullovation-city-source-v<version>.zip one folder up,
                                                    beside the source folder
    python3 tools/pack.py <folder>                  write the archive into another folder
    python3 tools/pack.py --apply <zip>             write every file in the archive over this folder, and remove
                                                    the files the archive no longer has
    python3 tools/pack.py --apply <zip> --dry-run   only list what would change

The archive holds one top folder, nc/, so in a chat it unpacks to /home/claude/nc. It leaves out what is rebuilt or
belongs to one machine: tests/shots/, tests/data/, art/out/, art/canon/out/, __pycache__/, .git/ and Claude Code's
local settings. It keeps what git leaves out but this machine's work needs: art/unslimmed/ and art/projects/.
--apply refuses an archive older than this folder unless --force is added. On Windows, use `python` for `python3`."""
import fnmatch, pathlib, sys, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]          # the source folder: this script sits in tools/
TOP = 'nc'
SKIP_DIRS = {'.git', '__pycache__', 'node_modules'}
SKIP_PATHS = {'tests/shots', 'tests/data', 'art/out', 'art/canon/out', '.claude/settings.local.json', 'CLAUDE.local.md',
              'dist', 'shots', 'testdata', 'art2/out'}           # the last four: where runs wrote before 0.1.18
SKIP_NAMES = ('*.pyc', '*.zip', '.DS_Store', 'Thumbs.db', 'desktop.ini')


def version():
    return (ROOT / 'src' / 'VERSION').read_text(encoding='utf-8').strip()


def order(v):
    """'0.1.16' -> (0, 1, 16), for comparing versions."""
    return tuple(int(x) for x in v.split('.'))


def kept(rel):
    """Whether a path inside the source folder, written with / separators, goes in the archive."""
    parts = rel.split('/')
    if any(p in SKIP_DIRS for p in parts):
        return False
    if any(rel == s or rel.startswith(s + '/') for s in SKIP_PATHS):
        return False
    return not any(fnmatch.fnmatch(parts[-1], pat) for pat in SKIP_NAMES)


def files():
    return [rel for rel in (p.relative_to(ROOT).as_posix() for p in sorted(ROOT.rglob('*')) if p.is_file()) if kept(rel)]


def pack(dest):
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f'nullovation-city-source-v{version()}.zip'
    names = files()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in names:
            z.write(ROOT / rel, f'{TOP}/{rel}')
    print(f'packed {len(names)} files into {out} ({out.stat().st_size / 1048576:.1f} MB)')
    return out


def apply(archive, dry=False, force=False):
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if not n.endswith('/')]
        if not names or not all(n.startswith(TOP + '/') for n in names):
            sys.exit(f'{archive} does not hold one {TOP}/ folder, so it is not a Nullovation City source archive.')
        incoming = {n[len(TOP) + 1:]: n for n in names}
        unsafe = [rel for rel in incoming if rel.startswith('/') or '..' in rel.split('/') or ':' in rel]
        if unsafe:
            sys.exit('The archive has unsafe paths, so nothing changed: ' + ', '.join(unsafe))
        if 'src/VERSION' not in incoming:
            sys.exit('The archive has no src/VERSION, so nothing changed.')
        theirs, ours = z.read(incoming['src/VERSION']).decode('utf-8').strip(), version()
        if order(theirs) < order(ours) and not force:
            sys.exit(f'The archive is v{theirs}, older than this folder at v{ours}, so nothing changed. '
                     'Add --force to apply it anyway.')
        incoming = {rel: n for rel, n in incoming.items() if kept(rel)}
        changed = [rel for rel, n in incoming.items() if not (ROOT / rel).is_file() or (ROOT / rel).read_bytes() != z.read(n)]
        stale = [rel for rel in files() if rel not in incoming]
        print(f'v{ours} -> v{theirs}: {len(changed)} files to write, {len(stale)} to remove')
        for rel in changed:
            print('  write  ' + rel)
        for rel in stale:
            print('  remove ' + rel)
        if dry:
            print('dry run: nothing changed')
            return
        for rel in changed:
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(z.read(incoming[rel]))
        for rel in stale:
            (ROOT / rel).unlink()
            for parent in (ROOT / rel).parents:          # drop folders the removal left empty
                if parent == ROOT or any(parent.iterdir()):
                    break
                parent.rmdir()
        print(f'this folder is now v{theirs}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--apply':
        rest = [a for a in args[1:] if not a.startswith('--')]
        if len(rest) != 1:
            sys.exit('Usage: python3 tools/pack.py --apply <archive.zip> [--dry-run] [--force]')
        apply(rest[0], dry='--dry-run' in args, force='--force' in args)
    else:
        pack(args[0] if args else ROOT.parent)
