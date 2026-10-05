"""Shared setup for the test passes.

Every path is built from the source folder, one up from here, so the passes run wherever the source is unpacked:
/home/claude/nc in a claude.ai chat, or any folder on Windows, macOS or Linux for Claude Code. The files the passes
upload are drawn here on first use, into tests/data/, so a fresh copy of the source needs nothing else."""
import json, os, pathlib, subprocess, sys

if os.name == 'nt' and not sys.flags.utf8_mode:      # Windows: run again in UTF-8 mode, so Arabic text reads and prints
    sys.exit(subprocess.call([sys.executable, '-X', 'utf8', *sys.argv]))

TESTS = pathlib.Path(__file__).resolve().parent              # this folder, tests/
ROOT = TESTS.parent                                          # the source folder
FILE = (ROOT / 'index.html').as_uri()                        # the page build.py writes
SHOTS = SH = TESTS / 'shots'                        # screenshots, to look at before presenting work
DATA = TESTS / 'data'                               # generated fixtures and files the passes write
SKILLS = ROOT / '.claude' / 'skills'
VERSION = (ROOT / 'src' / 'VERSION').read_text(encoding='utf-8').strip()
SHOTS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

# The city every browser pass starts from, written into the browser before the page first loads, so the passes do
# not depend on what a new city starts with: the starter project as it was at 0.1.16, plus a second, made-up
# project to work on. It is written once per tab and never on a reload, so a reload behaves as it does for a user.
# test04 opens one page without it, to check the real start; test14 needs no projects and goes without it.
SAMPLE = 'Garden planner'
_CITY = {'app': 'nullovation-city', 'version': 2, 'world': {'size': 5}, 'projects': [
    {'name': 'Nullovation City', 'plot': {'u': 2, 'v': 2}, 'generic': 'city-hall',
     'description': 'A personal project tracker drawn as a small isometric pixel city. Every project is one building: click it '
                    'for a quick status bubble, or step inside for everything else.\n\nRound 1 locked the foundations: a local HTML '
                    'file, isometric daytime pastels, separate decorated plots, and placeholder blocks until real art arrives. '
                    'Round 2 made block art the focus.',
     'milestones': [{'id': 'm_seed_art', 'name': 'Block art'}, {'id': 'm_seed_use', 'name': 'Move in'}],
     'todos': [{'text': 'Round 3: decide the block art loop', 'milestoneId': 'm_seed_art'},
               {'text': 'Build the block art skill', 'milestoneId': 'm_seed_art'},
               {'text': 'Make block art for each project', 'milestoneId': 'm_seed_art'},
               {'text': 'Try the project view for a week', 'milestoneId': 'm_seed_use'}]},
    {'name': SAMPLE, 'plot': {'u': 2, 'v': 1}, 'generic': 'research-lab',
     'description': 'A small app that plans a vegetable garden: the beds on a grid, what grows where, and when to water.\n\n'
                    'Its first release draws the beds and saves the plan; the launch adds reminders.',
     'milestones': [{'id': 'm_first', 'name': 'First release'}, {'id': 'm_launch', 'name': 'Launch'}],
     'todos': [{'text': 'Draw the beds on a grid', 'milestoneId': 'm_first'},
               {'text': 'Save a plan as a file', 'milestoneId': 'm_first'},
               {'text': 'Add plant icons', 'milestoneId': 'm_first'},
               {'text': 'Tune the watering reminders', 'milestoneId': 'm_first'},
               {'text': 'Publish the app', 'milestoneId': 'm_launch'}],
     'links': [{'label': 'Design chat', 'url': 'https://example.com/chat/design', 'icon': 'chat'},
               {'label': 'Planning chat', 'url': 'https://example.com/chat/planning', 'icon': 'chat'}]},
]}
TEST_CITY = ("try { if (!sessionStorage.getItem('nc-test-city')) { sessionStorage.setItem('nc-test-city', '1'); "
             "if (!localStorage.getItem('nullovation-city:v1')) localStorage.setItem('nullovation-city:v1', "
             + json.dumps(json.dumps(_CITY)) + "); } } catch (e) {}")

# the city's own colors, so the fixtures look like art the tool expects
_PAL = [(0, 0, 0), (43, 37, 66), (127, 214, 206), (244, 163, 195), (255, 235, 160), (90, 160, 150), (190, 230, 225)]


def _block(w, h, top, bottom, window=4):
    """Palette indices for a small isometric block: a 2:1 plot diamond across the full width with a tower on it.
    Rows above `top` and the last `bottom` rows stay empty (index 0, see-through)."""
    from PIL import Image, ImageDraw
    im = Image.new('P', (w, h), 0)
    im.putpalette([c for rgb in _PAL for c in rgb] + [0] * (768 - 3 * len(_PAL)))
    d = ImageDraw.Draw(im)
    base, q = h - bottom - 1, w // 4                # the plot's front corner sits on row `base`
    d.polygon([(0, base - q), (w // 2, base - 2 * q), (w - 1, base - q), (w // 2, base)], fill=5, outline=1)
    d.rectangle([q, top, w - q, base - q], fill=2, outline=1)
    d.rectangle([q + 6, top + 6, q + 18, top + 18], fill=window, outline=1)
    d.rectangle([w - q - 18, top + 6, w - q - 6, top + 18], fill=3, outline=1)
    return im


def _gif(path):
    """8 frames, 170 px wide, 14 empty rows on top and 9 below: a window that blinks."""
    frames = [_block(170, 200, 14, 9, window=4 if i % 2 else 6) for i in range(8)]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=120, loop=0,
                   transparency=0, disposal=2, optimize=False)


def _png(w, h, top, bottom):
    def draw(path):
        im = _block(w, h, top, bottom)
        im.info['transparency'] = 0                 # index 0 stays see-through in the PNG
        im.convert('RGBA').save(path)
    return draw


def _jpg(path):
    from PIL import Image
    Image.new('RGB', (64, 64), _PAL[2]).save(path, 'JPEG')


def _backup_v1(path):
    """A backup in the first data version: no milestones, no notes, no due dates."""
    projects = [{'id': 'p-v1-' + k, 'name': name, 'description': 'From a version 1 backup.', 'plot': {'u': u, 'v': 0},
                 'todos': [{'id': 't-' + k + '1', 'text': 'An open task', 'done': False},
                           {'id': 't-' + k + '2', 'text': 'A finished task', 'done': True, 'doneAt': 1700000000000}],
                 'links': [], 'art': {'has': False}, 'createdAt': 1700000000000, 'updatedAt': 1700000000000}
                for u, (k, name) in enumerate([('a', 'Old project A'), ('b', 'Old project B'), ('c', 'Old project C')])]
    path.write_text(json.dumps({'app': 'nullovation-city', 'version': 1, 'world': {'size': 5}, 'projects': projects}),
                    encoding='utf-8')


_DRAW = {
    'test.jpg': _jpg,                               # refused: not a PNG or GIF
    'test-wide.png': _png(700, 300, 20, 0),         # refused: 700 px wide
    'test-live.gif': _gif,                          # a live building with padded margins
    'test-still.png': _png(170, 160, 12, 0),        # a still building
    'test-block.png': _png(128, 100, 8, 0),         # block art at the old 128 px standard
    'backup-v1.json': _backup_v1,
}


def fixture(name):
    """The path of a test file, drawn the first time it is asked for."""
    path = DATA / name
    if not path.exists():
        _DRAW[name](path)
    return str(path)
