"""The playground park lot, from its PixelLab still (Pro at 256 by 128, the first frame of lot-park.gif as the style
image): its edge filled out to the plot diamond and the ragged strips past it trimmed (art/kit/filllot.py), then
animated in place by changing existing pixels, over an 8-second loop like the other lots. The carousel's cyan orbs
light one at a time, travelling round it so it seems to turn; the front swing seat sways a pixel in the breeze; a glint
runs down each slide once a loop, at different times; a butterfly drifts over the lawn on a closed path. The orbs take
the city's own glow cyan, so they shine at night; the sand's cream is nudged paler, so it does not.
Reads art/sources/lot-playground.png; writes art/out/lot-playground.gif and .png, checked frame by frame against
the tool's own GIF decoder."""
import json, math, pathlib, subprocess, sys, tempfile
import numpy as np
from PIL import Image

NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
sys.path.insert(0, str(NC / 'art' / 'kit'))
from filllot import fill_lot, trim_lot

SRC = NC / 'art' / 'sources' / 'lot-playground.png'
OUT = NC / 'art' / 'out'
DECODER = (NC / 'src' / 'js' / '35-gif.js').as_posix()
N, DELAY = 40, 200                                      # 8 seconds, like the other lots
rnd = np.random.RandomState(11)

base = np.array(Image.open(SRC).convert('RGBA'))
H, W = base.shape[:2]
print('edge: filled', fill_lot(base), 'px, trimmed', trim_lot(base), 'px')
base = base.astype(int)
same = lambda c: (base[..., 0] == c[0]) & (base[..., 1] == c[1]) & (base[..., 2] == c[2]) & (base[..., 3] > 0)
yy, xx = np.mgrid[0:H, 0:W]
box = lambda x0, x1, y0, y1: (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)

INK, PINK, MID_PINK, LAWN = (1, 3, 1), (254, 161, 216), (187, 112, 155), (152, 204, 136)
CYAN_STILL = (82, 215, 205)
GLOW, GLOW_MID, GLOW_PEAK = (63, 224, 240), (86, 236, 250), (112, 248, 255)     # the city's glow cyan, kept by night

# ---- the carousel's orbs, in the order the light travels round: front ring left to right, then the canopy back ----
ORBS = [box(188, 190, 59, 61), box(196, 197, 61, 63), box(203, 204, 61, 61),
        box(203, 204, 52, 52), box(196, 197, 49, 51), box(188, 188, 51, 52)]
cyan = same(CYAN_STILL)
ORBS = [m & (cyan | same((138, 228, 187))) for m in ORBS]
assert all(m.any() for m in ORBS) and not (cyan & ~np.any(ORBS, axis=0)).any(), 'an orb pixel is missed'
base[cyan, :3] = GLOW                                   # the still's cyan, nudged to the city's glow cyan
base[same((251, 229, 188)), :3] = (244, 230, 210)       # the sand and the swing frame's cream, a touch paler, so the
                                                        # tool's night does not take them for lamps (30-pixel.js)
ORB_LV = [dict() for _ in range(N)]
f, o = rnd.randint(0, 3), 0
while f < N - 2:                                        # one orb at a time, round the ring, at uneven intervals
    for k, lv in enumerate((0.5, 1.0, 1.0, 0.5)[:rnd.randint(3, 5)]):
        ORB_LV[(f + k) % N][o] = lv
    f += 3 + rnd.randint(1, 3)
    o = (o + 1) % len(ORBS)

# ---- the front swing seat: rests, then sways a pixel to the right and back, a few times a loop, never in a rhythm.
#      The seat and the bottom of its left rope move together, so the rope takes a one-pixel step, as if angled ----
SEAT = box(100, 105, 36, 39) | box(100, 100, 33, 35)
SWAY = np.zeros(N, int)
for start, ln in ((4, 3), (9, 2), (21, 4), (27, 2), (33, 3)):
    SWAY[start:start + ln] = 1


def sway(fr):
    ys, xs = np.nonzero(SEAT)
    for y in set(ys.tolist()):                          # what shows behind: the ground just right of the moving run
        run = xs[ys == y]
        fr[y, run.min()] = base[y, run.max() + 1]
    fr[ys, xs + 1] = base[ys, xs]


# ---- a glint down each slide: a one-row line of light running down its pink, once a loop each ----
LEFT_SLIDE = box(111, 127, 46, 72) & (same(PINK) | same(MID_PINK))
RIGHT_SLIDE = box(130, 150, 46, 72) & (same(PINK) | same(MID_PINK))
GLINT_LIGHT = {PINK: (255, 198, 232), MID_PINK: (218, 138, 184)}


def glint(fr, mask, k):
    ys = np.nonzero(mask.any(axis=1))[0]
    y = ys.min() + 2 * k                                # two rows a frame, top to bottom
    if y > ys.max():
        return
    band = mask & (yy == y)
    for c, lit in GLINT_LIGHT.items():
        m = band & same(c)
        fr[m, :3] = lit


# ---- a butterfly over the lawn, on a smooth closed path, wings beating every frame as on the park lot ----
def butterfly(fr, k):
    t = 2 * math.pi * k / N
    x, y = round(100 + 34 * math.sin(t)), round(88 + 9 * math.sin(2 * t + 0.6))
    fr[y, x, :3] = INK
    wings = ((-1, -1), (1, -1), (-2, -1), (2, -1)) if k % 2 == 0 else ((-1, 0), (1, 0))
    for dx, dy in wings:
        fr[y + dy, x + dx, :3] = PINK


frames = []
for k in range(N):
    fr = base.copy()
    for o, lv in ORB_LV[k].items():
        fr[ORBS[o], :3] = GLOW_PEAK if lv >= 1 else GLOW_MID
    if SWAY[k]:
        sway(fr)
    if 6 <= k < 20:
        glint(fr, LEFT_SLIDE, k - 6)
    if 24 <= k < 38:
        glint(fr, RIGHT_SLIDE, k - 24)
    butterfly(fr, k)
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
gif = str(OUT / 'lot-playground.gif')
ims[0].save(gif, save_all=True, append_images=ims[1:], duration=[DELAY] * N, loop=0, transparency=0, disposal=1, optimize=False)
Image.fromarray(frames[0], 'RGBA').save(str(OUT / 'lot-playground.png'))

dec = pathlib.Path(tempfile.gettempdir()) / '_playground_d.bin'
js = f"""const fs = require('fs'); const {{ decodeGif }} = require({json.dumps(DECODER)});
const g = decodeGif(new Uint8Array(fs.readFileSync({json.dumps(gif)})));
fs.writeFileSync({json.dumps(str(dec))}, Buffer.concat(g.frames.map(f => Buffer.from(f.rgba.buffer)))); console.log(g.frames.length);"""
n = int(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout.strip())
got = np.frombuffer(dec.read_bytes(), np.uint8).reshape(n, *frames[0].shape)
seen = lambda a: np.where(a[..., 3:4] > 0, a, 0)
exact = n == N and not np.any(seen(got) != seen(stack))
changed = [int((np.abs(f_.astype(int) - frames[0].astype(int)).max(-1) > 0).sum()) for f_ in frames]
print(f'playground: {W} x {H}, {N} frames at {DELAY} ms, {len(cols)} colors, {pathlib.Path(gif).stat().st_size // 1024} KB, '
      f'changed pixels per frame {min(changed[1:])} to {max(changed)}, '
      f'{"decodes exactly" if exact else "DOES NOT decode exactly"} in the tool')
