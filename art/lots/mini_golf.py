"""The mini golf park lot, the lagoon course, from its PixelLab still (Pro at 256 by 128, the first frame of lot-pond.gif
as the style image). Pro drew the course with no ground under it, so its pieces are laid whole on today's park lawn,
drawn in code (ground() in art/lots/lots.py), and any empty pixel left in the plot diamond is filled
(art/kit/filllot.py). Nothing is trimmed: what rises past the diamond is the lighthouse and two flag tips, the way tree
tops do on today's lots. Animated in place over an 8-second loop like the other lots: the lighthouse lantern keeps a
gold lamp and blinks softly three times a loop; glints come and go on the pond, drifting a pixel, in the pond lot's own
colors; each flag ripples now and then, a light fold running out to its tip. The little windmill near the front is too
small and rough to turn cleanly, so it stays still. The flags' pale gold is nudged a touch darker, so the tool's night
does not take it for a lamp (30-pixel.js); the lantern takes the city's gold and butter, which it keeps lit.
Reads art/sources/lot-mini-golf.png; writes art/out/lot-mini-golf.gif and .png, checked frame by frame against the
tool's own GIF decoder."""
import json, pathlib, subprocess, sys, tempfile
import numpy as np
from PIL import Image

NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
sys.path.insert(0, str(NC / 'art' / 'kit'))
from filllot import fill_lot
from lots import ground, LT                              # today's park lawn
from lots_kit import C, NAMES

SRC = NC / 'art' / 'sources' / 'lot-mini-golf.png'
OUT = NC / 'art' / 'out'
DECODER = (NC / 'src' / 'js' / '35-gif.js').as_posix()
N, DELAY = 40, 200                                      # 8 seconds, like the other lots
rnd = np.random.RandomState(17)

# ---- the course on the lawn ----
raw = np.array(Image.open(SRC).convert('RGBA'))
raw[..., 3] = np.where(raw[..., 3] >= 128, 255, 0)
HEX = np.array([[0, 0, 0, 0]] + [[int(C[n][k:k + 2], 16) for k in (1, 3, 5)] + [255] for n in NAMES], np.uint8)
base = HEX[ground(seed=27).c[LT:LT + 128]]
on = raw[..., 3] > 0
base[on] = raw[on]
print('lawn: Pro covered', int(on.sum()), 'px; filled', fill_lot(base), 'px')
base = base.astype(int)
H, W = base.shape[:2]
same = lambda c: (base[..., 0] == c[0]) & (base[..., 1] == c[1]) & (base[..., 2] == c[2]) & (base[..., 3] > 0)
yy, xx = np.mgrid[0:H, 0:W]
box = lambda x0, x1, y0, y1: (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)

PALE_GOLD, GOLD_DK, GOLD = (238, 206, 116), (181, 138, 36), (213, 172, 58)
FOLD = (232, 190, 118)                                  # the pale gold, just under what the tool's night keeps lit
LAMP_REST, LAMP_HALF, LAMP_PEAK = (242, 199, 92), (255, 227, 138), (255, 240, 190)    # the city's gold and butter
GLASS = [(205, 154, 120), (219, 201, 179)]
G1, G0 = (159, 244, 234), (231, 250, 251)               # the pond lot's glint colors
WATER = [(113, 222, 209), (87, 184, 179)]               # the pond lot's g3 and g4, which Pro copied


def piece(mask, y, x):
    """The 4-connected piece of a mask holding (y, x)."""
    out = np.zeros_like(mask); stack = [(y, x)]
    while stack:
        cy, cx = stack.pop()
        if 0 <= cy < H and 0 <= cx < W and mask[cy, cx] and not out[cy, cx]:
            out[cy, cx] = True
            stack += [(cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)]
    return out


# ---- the lighthouse lantern: the lamp in the middle, the glass round it ----
LANTERN = box(167, 176, 10, 14)
LAMP = LANTERN & same(PALE_GOLD)
GLASSES = LANTERN & np.any([same(c) for c in GLASS], axis=0)
assert LAMP.sum() == 4 and GLASSES.sum() >= 10, (LAMP.sum(), GLASSES.sum())
base[LAMP, :3] = LAMP_REST
BLINK = {}
for start in (3, 17, 31):                               # every 2.8 seconds or so, not quite even
    start += rnd.randint(-1, 2)
    for k, lv in enumerate((0.5, 1.0, 1.0, 0.5)):
        BLINK[start + k] = lv

# ---- the flags: each cloth's columns from the pole out to the tip; a fold of light runs out along them ----
base[same(PALE_GOLD), :3] = FOLD                        # the poles and flags, so night does not light them
cloth = same(GOLD) | same(GOLD_DK)
FLAGS, seen = [], np.zeros_like(cloth)
for y, x in zip(*np.nonzero(cloth)):
    if seen[y, x]:
        continue
    m = piece(cloth, y, x); seen |= m
    if m.sum() >= 8:
        xs = np.nonzero(m.any(axis=0))[0]
        FLAGS.append((m, list(range(xs.min() + 1, xs.max() + 1))))     # the column by the pole stays its dark fold
FLAGS.sort(key=lambda f: np.nonzero(f[0])[1].min())
assert len(FLAGS) == 4, len(FLAGS)
RIPPLE = [dict() for _ in range(N)]
for i, (m, cols) in enumerate(FLAGS):
    f = rnd.randint(0, 8)
    while f < N:
        for s, cx in enumerate(cols):                   # one column a frame, pole to tip
            RIPPLE[(f + s) % N][i] = cx
        f += len(cols) + rnd.randint(6, 14)


def ripple(fr, i, cx):
    m, cols = FLAGS[i]
    fr[m & (xx == cx), :3] = FOLD
    if cx - 1 >= cols[0]:
        fr[m & (xx == cx - 1), :3] = GOLD_DK


# ---- glints on the pond: a three-pixel streak in the pond lot's colors, coming and going, drifting a pixel ----
water = np.any([same(c) for c in WATER], axis=0) & box(82, 178, 38, 88)
POND, seen = np.zeros_like(water), np.zeros_like(water)
for y, x in zip(*np.nonzero(water)):                    # the bridge cuts the pond in two; take both halves
    if not seen[y, x]:
        m = piece(water, y, x); seen |= m
        if m.sum() >= 200:
            POND |= m
assert 1500 < POND.sum() < 4000, POND.sum()
spots = [(y, x) for y, x in zip(*np.nonzero(POND)) if POND[y, x:x + 4].all() and x + 4 < W]
GLINTS = []
for _ in range(9):
    y, x = spots[rnd.randint(len(spots))]
    GLINTS.append((y, x, rnd.randint(N), rnd.randint(4, 8)))


def glint(fr, y, x, age, life):
    x += age * 2 // life                                # a pixel to the right over its life
    lit = G0 if 0 < age < life - 1 else G1
    for dx, c in ((0, G1), (1, lit), (2, G1)):
        if POND[y, x + dx]:
            fr[y, x + dx, :3] = c


frames = []
for k in range(N):
    fr = base.copy()
    lv = BLINK.get(k)
    if lv:
        fr[LAMP, :3] = LAMP_PEAK if lv >= 1 else LAMP_HALF
        fr[GLASSES, :3] = LAMP_HALF if lv >= 1 else LAMP_REST
    for i, cx in RIPPLE[k].items():
        ripple(fr, i, cx)
    for y, x, start, life in GLINTS:
        age = (k - start) % N
        if age < life:
            glint(fr, y, x, age, life)
    frames.append(fr.astype(np.uint8))

# ---- one palette for every frame, transparency at 0; every frame covers the same pixels, so disposal 1 ----
stack = np.stack(frames)
vis = (stack[..., 3] > 0).any(axis=0)
ys, xs = np.nonzero(vis)
assert xs.min() == 0 and xs.max() == W - 1 and ys.max() == H - 1, (xs.min(), xs.max(), ys.max())
assert all((f_[..., 3] > 0).sum() == vis.sum() for f_ in frames), 'a frame changes the silhouette'
cols = sorted({tuple(p[:3]) for f_ in frames for p in f_[f_[..., 3] > 0]})
assert len(cols) <= 255, len(cols)
idx = {c: i + 1 for i, c in enumerate(cols)}
pal = [0, 0, 0] + [v for c in cols for v in c]
pal += [0] * (768 - len(pal))
ims = []
for f_ in frames:
    a = np.zeros(f_.shape[:2], np.uint8)
    m = f_[..., 3] > 0
    a[m] = [idx[tuple(c)] for c in f_[m, :3]]
    im = Image.fromarray(a, 'P'); im.putpalette(pal); ims.append(im)
OUT.mkdir(exist_ok=True)
gif = str(OUT / 'lot-mini-golf.gif')
ims[0].save(gif, save_all=True, append_images=ims[1:], duration=[DELAY] * N, loop=0, transparency=0, disposal=1, optimize=False)
Image.fromarray(frames[0], 'RGBA').save(str(OUT / 'lot-mini-golf.png'))

dec = pathlib.Path(tempfile.gettempdir()) / '_mini_golf_d.bin'
js = f"""const fs = require('fs'); const {{ decodeGif }} = require({json.dumps(DECODER)});
const g = decodeGif(new Uint8Array(fs.readFileSync({json.dumps(gif)})));
fs.writeFileSync({json.dumps(str(dec))}, Buffer.concat(g.frames.map(f => Buffer.from(f.rgba.buffer)))); console.log(g.frames.length);"""
n = int(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout.strip())
got = np.frombuffer(dec.read_bytes(), np.uint8).reshape(n, *frames[0].shape)
seen_ = lambda a: np.where(a[..., 3:4] > 0, a, 0)
exact = n == N and not np.any(seen_(got) != seen_(stack))
changed = [int((np.abs(f_.astype(int) - frames[0].astype(int)).max(-1) > 0).sum()) for f_ in frames]
print(f'mini golf: {W} x {H}, {N} frames at {DELAY} ms, {len(cols)} colors, {pathlib.Path(gif).stat().st_size // 1024} KB, '
      f'changed pixels per frame {min(changed[1:])} to {max(changed)}, '
      f'{"decodes exactly" if exact else "DOES NOT decode exactly"} in the tool')
