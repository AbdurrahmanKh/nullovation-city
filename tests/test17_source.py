"""Pass 17: the source travels. No browser: it checks that the build, tests and art scripts work from any folder,
that the archive carries what a new chat or Claude Code needs, and that applying an archive is safe."""
import os, pathlib, re, subprocess, sys, tempfile, zipfile
from testkit import ROOT, VERSION

def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
py = lambda args, cwd: subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8',
                                       env=dict(os.environ, PYTHONUTF8='1'))
DASHES = re.compile('[\u2013\u2014]')

# no chat paths: every script finds the source from its own location (docstrings may still mention the chat folder)
scripts = [p for d in ('.', 'tools', 'tests') for p in (ROOT / d).glob('*.py')] + list((ROOT / 'art').rglob('*.py'))
SANDBOX = re.compile(r"""['"](file://)?/home/claude|['"]/tmp/|['"]/mnt/user-data""")
sandbox = [p.relative_to(ROOT).as_posix() for p in scripts if p.name != 'test17_source.py' and SANDBOX.search(p.read_text(encoding='utf-8'))]
ok(f'no script has a chat or /tmp path in its code ({len(scripts)} scripts; {sandbox or "none"})', not sandbox)

# the layout: the root keeps to the entry points, runs write nothing into src/, and git leaves out what runs make
loose = sorted(p.name for p in ROOT.glob('*.py'))
ok(f'the only script at the root is build.py ({loose})', loose == ['build.py'])
ok('src/js holds only hand-written modules: the build makes 25-generics.js, 26-extra.js and 27-portraits.js in memory',
   not any((ROOT / 'src' / 'js' / n).exists() for n in ('25-generics.js', '26-extra.js', '27-portraits.js')))

# the portraits (0.1.48): Gus's and Proxima's, 256 px on a see-through background with no half-see-through pixel, and in the page
from PIL import Image
import base64
shots = {p.stem: Image.open(p) for p in sorted((ROOT / 'src' / 'portraits').glob('*.png'))}
ok(f'src/portraits holds Gus\'s and Proxima\'s portraits ({sorted(shots)})', sorted(shots) == ['gus', 'proxima'])
for who, im in shots.items():
    a = im.convert('RGBA').getchannel('A')
    ok(f'{who}.png is 256 by 256 with a hard see-through background ({im.size}, alpha {sorted(set(a.getdata()))})',
       im.size == (256, 256) and set(a.getdata()) == {0, 255})
page_text = (ROOT / 'index.html').read_text(encoding='utf-8')
ok('the page carries both portraits, byte for byte, as PORTRAITS', 'const PORTRAITS = {' in page_text and all(
   base64.b64encode((ROOT / 'src' / 'portraits' / (who + '.png')).read_bytes()).decode() in page_text for who in shots))
ignored = (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines() if (ROOT / '.gitignore').exists() else []
made = ['tests/shots/', 'tests/data/', 'art/out/', 'art/canon/out/', 'art/unslimmed/']
ok(f'git leaves out every folder that runs make ({[m for m in made if m not in ignored] or "all listed"})', all(m in ignored for m in made))
ok('nothing builds into a dist/ folder any more, and git has no rule for one', 'dist/' not in ignored)
ok('GitHub Pages serves the page as it is: .nojekyll sits at the root', (ROOT / '.nojekyll').exists())
# The decision wizard has its own repo (0.1.17): its skill and the starter city's Decision Wizard project left this one.
# Since 0.1.55 the tool talks to it (a task's wizard round), so the checks are on what left, and on the wizard being
# opened at its own address rather than shipped here.
copies = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_dir() and '.git' not in p.parts
          and p.name.lower() in ('d-wizard', 'decision-wizard')]
ok(f'no copy of the d-wizard skill or of the wizard itself in the repo ({copies or "none"})', not copies)
model = (ROOT / 'src' / 'js' / '20-model.js').read_text(encoding='utf-8')
seed = model[model.index('function seedProjects'):]
seed = seed[:seed.index('\n}\n')]
ok('a new city starts with Nullovation City alone: no Decision Wizard project, no chat links', 'wizard' not in seed.lower() and 'claude.ai/chat' not in seed)
pages = [p.relative_to(ROOT).as_posix() for p in (ROOT / 'src').rglob('*.html') if p.name != 'body.html']
rounds = (ROOT / 'src' / 'js' / '21-rounds.js').read_text(encoding='utf-8')
ok(f'the wizard opens at its own address, and no page of it ships in the tool ({pages or "no other page"})',
   not pages and 'https://abdurrahmankh.github.io/decision-wizard/' in rounds)

# the knowledge, the rules and the skills travel with the code
claude = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8') if (ROOT / 'CLAUDE.md').exists() else ''
ok('CLAUDE.md loads the knowledge file with an import line', re.search(r'^@docs/nullovation-city-knowledge\.md\s*$', claude, re.M) is not None)
named = sorted({m for m in re.findall(r'`([\w./-]+\.(?:py|md|json|ps1))`', claude) if '<' not in m})
missing = [m for m in named if not (ROOT / m).exists()]
ok(f'every file CLAUDE.md names exists ({len(named)} named; missing {missing or "none"})', named and not missing)
knowledge = ROOT / 'docs' / 'nullovation-city-knowledge.md'
ok('the knowledge file is in docs/ and states this version', knowledge.exists() and f'version {VERSION}' in knowledge.read_text(encoding='utf-8'))
skills = sorted(p.parent.name for p in (ROOT / '.claude' / 'skills').glob('*/SKILL.md'))
names = [re.search(r'^name:\s*"?([\w-]+)"?', (ROOT / '.claude' / 'skills' / s / 'SKILL.md').read_text(encoding='utf-8'), re.M) for s in skills]
ok(f'the two skills of the city sit where Claude Code loads them ({skills})',
   skills == ['nullovation-city', 'nullovation-city-builder'] and all(n and n.group(1) == s for n, s in zip(names, skills)))
texts = [ROOT / 'CLAUDE.md', ROOT / 'README.md', ROOT / 'CHANGELOG.md', ROOT / 'requirements.txt', knowledge,
         ROOT / 'tests' / 'testkit.py', ROOT / 'tests' / 'run_tests.py', ROOT / 'tools' / 'pack.py', ROOT / 'build.py',
         ROOT / 'tests' / 'test17_source.py', ROOT / 'art' / 'sources' / 'README.md',
         *(ROOT / '.claude' / 'skills').rglob('*.md')]
dashed = [p.relative_to(ROOT).as_posix() for p in texts if p.exists() and DASHES.search(p.read_text(encoding='utf-8'))]
ok(f'no em or en dash in the docs, skills and tooling ({dashed or "none"})', not dashed)

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    # the archive: named for the version, one nc/ folder, the right things in and out
    r = py(['tools/pack.py', str(tmp)], ROOT)
    archive = tmp / f'nullovation-city-source-v{VERSION}.zip'
    ok(f'pack.py writes nullovation-city-source-v{VERSION}.zip', r.returncode == 0 and archive.exists())
    names = zipfile.ZipFile(archive).namelist() if archive.exists() else []
    need = ['nc/CLAUDE.md', 'nc/README.md', 'nc/docs/nullovation-city-knowledge.md', 'nc/src/VERSION', 'nc/build.py',
            'nc/tests/testkit.py', 'nc/tests/run_tests.py', 'nc/tools/pack.py', 'nc/src/buildings/meta.json', 'nc/index.html',
            'nc/.claude/skills/nullovation-city/SKILL.md', 'nc/.claude/skills/nullovation-city-builder/SKILL.md',
            'nc/src/portraits/gus.png', 'nc/src/portraits/proxima.png']
    ok('the archive holds the rules, the knowledge, the skills, the tooling and the portraits', all(n in names for n in need))
    left = [n for n in names if re.match(r'nc/(dist|tests/shots|tests/data|\.git|art/out|art/canon/out)/', n) or '__pycache__' in n]
    ok(f'the archive leaves out builds, screenshots, test data and caches ({len(names)} files; {left[:3] or "none left in"})',
       names and all(n.startswith('nc/') for n in names) and not left)

    # a fresh copy somewhere else builds the same file as this folder
    away = tmp / 'somewhere else'
    zipfile.ZipFile(archive).extractall(away)
    copy = away / 'nc'
    src_files = lambda: {p.relative_to(copy).as_posix(): p.read_bytes() for p in (copy / 'src').rglob('*') if p.is_file()}
    before = src_files()
    a, b = py(['build.py', str(tmp / 'here.html')], ROOT), py(['build.py', str(tmp / 'there.html')], copy)
    same = a.returncode == 0 and b.returncode == 0 and (tmp / 'here.html').read_bytes() == (tmp / 'there.html').read_bytes()
    ok('a copy unpacked in another folder builds a byte-identical tool', same)
    ok('building writes nothing into src/', b.returncode == 0 and src_files() == before)
    page = ROOT / 'index.html'
    ok('index.html at the root is the page this source builds, so the repo and GitHub Pages never show an old one',
       a.returncode == 0 and page.exists() and page.read_bytes() == (tmp / 'here.html').read_bytes())

    # applying an archive brings a folder back to it, keeping local test data
    (copy / 'build.py').write_text('changed locally\n', encoding='utf-8')
    (copy / 'src' / 'js' / '99-stray.js').write_text('// a file the archive no longer has\n', encoding='utf-8')
    (copy / 'tests' / 'data').mkdir(parents=True, exist_ok=True)
    (copy / 'tests' / 'data' / 'keep.txt').write_text('local\n', encoding='utf-8')
    r = py(['tools/pack.py', '--apply', str(archive), '--dry-run'], copy)
    ok('a dry run lists the changes and touches nothing', r.returncode == 0 and 'write  build.py' in r.stdout
       and 'remove src/js/99-stray.js' in r.stdout and (copy / 'build.py').read_text(encoding='utf-8') == 'changed locally\n')
    r = py(['tools/pack.py', '--apply', str(archive)], copy)
    ok('--apply restores changed files and removes stray ones', r.returncode == 0
       and (copy / 'build.py').read_bytes() == (ROOT / 'build.py').read_bytes() and not (copy / 'src' / 'js' / '99-stray.js').exists())
    ok('--apply keeps local test data', (copy / 'tests' / 'data' / 'keep.txt').exists())

    # an older archive is refused, so newer work is never overwritten by mistake
    old = tmp / 'old.zip'
    with zipfile.ZipFile(old, 'w') as z:
        z.writestr('nc/src/VERSION', '0.0.1\n')
        z.writestr('nc/build.py', 'old\n')
    r = py(['tools/pack.py', '--apply', str(old)], copy)
    ok('an older archive is refused and nothing changes', r.returncode != 0 and 'older' in (r.stdout + r.stderr)
       and (copy / 'build.py').read_bytes() == (ROOT / 'build.py').read_bytes())
    bad = tmp / 'bad.zip'
    with zipfile.ZipFile(bad, 'w') as z:
        z.writestr('nc/src/VERSION', '9.9.9\n')
        z.writestr('nc/../escape.txt', 'no\n')
    r = py(['tools/pack.py', '--apply', str(bad)], copy)
    ok('an archive with paths outside the folder is refused', r.returncode != 0 and not (away / 'escape.txt').exists())

print('no console errors (this pass has no browser)')
