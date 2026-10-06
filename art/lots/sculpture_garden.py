"""The sculpture garden park lot, "floating stones", from its PixelLab still (Pro at 256 by 128, the first frame of
lot-park.gif as the style image). Pro drew no ground under it, so its stones, plinths, stepping stones, benches and
shrubs are laid on today's park lawn, drawn in code (ground() in art/lots/lots.py), then edged with art/kit/filllot.py.
Animated in place over an 8-second loop like the other lots: each of the six stones lifts a pixel off its plinth at its
own slow pace, showing a line of glow beneath it; the cyan glow on each plinth breathes at its own time; a butterfly
drifts over the lawn on a closed path. The glows take the city's own glow cyan, so they shine at night.
Reads art/sources/lot-sculpture-garden.png; writes art/out/lot-sculpture-garden.gif and .png, checked frame by frame
against the tool's own GIF decoder."""
import json, math, pathlib, subprocess, sys, tempfile
import numpy as np
from PIL import Image

NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
sys.path.insert(0, str(NC / 'art' / 'kit'))
sys.path.insert(0, str(NC / 'art' / 'lots'))
from filllot import fill_lot, trim_lot
from lots import ground, LT
from lots_kit import C, NAMES

SRC = NC / 'art' / 'sources' / 'lot-sculpture-garden.png'
OUT = NC / 'art' / 'out'
DECODER = (NC / 'src' / 'js' / '35-gif.js').as_posix()
N, DELAY = 40, 200                                      # 8 seconds, like the other lots
rnd = np.random.RandomState(5)

# ---- the lawn first, then the still's pieces on it ----
HEX = np.array([[0, 0, 0, 0]] + [[int(C[n][k:k + 2], 16) for k in (1, 3, 5)] + [255] for n in NAMES], np.uint8)
lawn = HEX[ground(seed=33).c[LT:LT + 128]]              # the lawn the concept sheet showed it on
still = np.array(Image.open(SRC).convert('RGBA'))
still[..., 3] = np.where(still[..., 3] >= 128, 255, 0)
still[still[..., 3] == 0] = 0
piece = still[..., 3] > 0
base = lawn.copy()
base[piece] = still[piece]
H, W = base.shape[:2]
print('edge: filled', fill_lot(base), 'px, trimmed', trim_lot(base), 'px')
base = base.astype(int)
piece = np.zeros((H, W), bool); piece[still[..., 3] > 0] = True
same = lambda c: (base[..., 0] == c[0]) & (base[..., 1] == c[1]) & (base[..., 2] == c[2]) & (base[..., 3] > 0)
yy, xx = np.mgrid[0:H, 0:W]

INK = (1, 2, 1)
ink = same(INK)

# ---- the glows: the still's mint cyan on each plinth top becomes the city's glow cyan, which the tool keeps lit by
#      night (isLightColor in src/js/30-pixel.js wants red under 120); four levels to breathe through ----
GLOW_LV = [(40, 206, 226), (63, 224, 240), (86, 236, 250), (112, 248, 255)]        # dim, rest, mid, peak
glow_px = same((133, 250, 230)) | same((181, 251, 234))   # the mint, blue and sky stones' highlights share it: taken out below

# ---- the six stones, each found by filling its body from a point inside it, plus the outline round that body ----
SEEDS = {'mint': (126, 15), 'lavender': (162, 30), 'gold': (197, 46), 'pink': (57, 51), 'blue': (93, 69), 'sky': (130, 86)}


def flood(x, y):
    m = np.zeros((H, W), bool)
    stack = [(y, x)]
    while stack:
        cy, cx = stack.pop()
        if not (0 <= cy < H and 0 <= cx < W) or m[cy, cx] or ink[cy, cx] or not piece[cy, cx]:
            continue
        m[cy, cx] = True
        stack += [(cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)]
    return m


def grow(m):
    g = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            g |= np.roll(np.roll(m, dy, 0), dx, 1)
    return g


STONES = {}
for name, (x, y) in SEEDS.items():
    body = flood(x, y)
    assert 40 <= body.sum() <= 250, (name, int(body.sum()))      # a stone, not the plinth or the lawn
    STONES[name] = body | (grow(body) & ink)
glow_px &= ~np.any(list(STONES.values()), axis=0)
base[glow_px, :3] = GLOW_LV[1]
# each stone's plinth, filled from the first pixel under the stone's middle, and the glow on its top
PLINTHS, GLOWS = {}, {}
for name, s in STONES.items():
    ys, xs = np.nonzero(s)
    x = int(round(xs.mean())); y = ys.max() + 1
    while ink[y, x] or s[y, x]:
        y += 1
    PLINTHS[name] = flood(x, y)
    GLOWS[name] = glow_px & PLINTHS[name]
    assert 60 <= PLINTHS[name].sum() <= 260 and GLOWS[name].sum() >= 10, (name, int(PLINTHS[name].sum()), int(GLOWS[name].sum()))
assert not (glow_px & ~np.any(list(GLOWS.values()), axis=0)).any(), 'a glow pixel belongs to no plinth'
print('stones (px):', {n: int(s.sum()) for n, s in STONES.items()}, '| glows (px):', {n: int(g.sum()) for n, g in GLOWS.items()})


PLINTH = np.any(list(PLINTHS.values()), axis=0)       # what a lifted stone's edge may rest on
assert not np.any([PLINTH & s for s in STONES.values()]), 'a plinth runs into its stone'


def lifted(fr, stone, glow_col):
    """The stone a pixel higher. In each column it leaves its lowest pixel: an outline pixel there stays when the
    plinth lies under it (the plinth's own edge, hidden by the stone till now); the stone's old contact row shows the
    glow, as light under a stone that floats; anything else shows what lies under it, lawn or plinth."""
    ys, xs = np.nonzero(stone)
    low = ys.max()
    src = fr.copy()
    fr[ys - 1, xs] = src[ys, xs]
    for x in set(xs.tolist()):
        y = ys[xs == x].max()                           # the pixel this column leaves
        below = y + 1 < H and PLINTH[y + 1, x]
        if y == low and below:
            fr[y, x, :3] = glow_col
        elif ink[y, x] and below:
            fr[y, x, :3] = INK
        else:
            fr[y, x, :3] = src[y + 1, x, :3] if y + 1 < H else base[y, x, :3]

# ---- the schedules: each stone up for a stretch of its own, slow and smooth; each glow breathes on its own curve ----
LIFT, BREATH = {}, {}
for name in STONES:
    ph, m = rnd.uniform(0, 2 * math.pi), rnd.choice([1, 1, 2])
    LIFT[name] = [math.sin(2 * math.pi * m * k / N + ph) > 0.35 for k in range(N)]
    ph2, m2 = rnd.uniform(0, 2 * math.pi), rnd.choice([1, 2])
    BREATH[name] = [int(round(1.5 + 1.5 * math.sin(2 * math.pi * m2 * k / N + ph2))) for k in range(N)]


# ---- a butterfly over the open lawn at the front left, on a smooth closed path, wings beating every frame ----
def butterfly(fr, k):
    t = 2 * math.pi * k / N
    x, y = round(66 + 26 * math.sin(t + 1.1)), round(100 + 7 * math.sin(2 * t))
    fr[y, x, :3] = INK
    wings = ((-1, -1), (1, -1), (-2, -1), (2, -1)) if k % 2 == 0 else ((-1, 0), (1, 0))
    for dx, dy in wings:
        fr[y + dy, x + dx, :3] = (244, 163, 195)        # the city's pink


frames = []
for k in range(N):
    fr = base.copy()
    for name in STONES:
        col = GLOW_LV[BREATH[name][k]]
        fr[GLOWS[name], :3] = col
    for name, stone in STONES.items():
        if LIFT[name][k]:
            lifted(fr, stone, GLOW_LV[min(3, BREATH[name][k] + 1)])
    butterfly(fr, k)
    frames.append(np.clip(fr, 0, 255).astype(np.uint8))

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
gif = str(OUT / 'lot-sculpture-garden.gif')
ims[0].save(gif, save_all=True, append_images=ims[1:], duration=[DELAY] * N, loop=0, transparency=0, disposal=1, optimize=False)
Image.fromarray(frames[0], 'RGBA').save(str(OUT / 'lot-sculpture-garden.png'))

dec = pathlib.Path(tempfile.gettempdir()) / '_sculpture_d.bin'
js = f"""const fs = require('fs'); const {{ decodeGif }} = require({json.dumps(DECODER)});
const g = decodeGif(new Uint8Array(fs.readFileSync({json.dumps(gif)})));
fs.writeFileSync({json.dumps(str(dec))}, Buffer.concat(g.frames.map(f => Buffer.from(f.rgba.buffer)))); console.log(g.frames.length);"""
n = int(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout.strip())
got = np.frombuffer(dec.read_bytes(), np.uint8).reshape(n, *frames[0].shape)
seen = lambda a: np.where(a[..., 3:4] > 0, a, 0)
exact = n == N and not np.any(seen(got) != seen(stack))
changed = [int((np.abs(f_.astype(int) - frames[0].astype(int)).max(-1) > 0).sum()) for f_ in frames]
print(f'sculpture garden: {W} x {H}, {N} frames at {DELAY} ms, {len(cols)} colors, {pathlib.Path(gif).stat().st_size // 1024} KB, '
      f'changed pixels per frame {min(changed[1:])} to {max(changed)}, '
      f'{"decodes exactly" if exact else "DOES NOT decode exactly"} in the tool')
