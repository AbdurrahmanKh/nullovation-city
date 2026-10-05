"""The user's city hall, animated in place: only existing pixels change."""
import colorsys, json
import numpy as np
from PIL import Image
from scipy import ndimage
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked

SRC = str(NC / 'art' / 'sources' / 'city-hall.png')          # the PixelLab city hall still: see art/sources/README.md
N, DELAY = 40, 250
rnd = np.random.RandomState(21)
base = np.array(Image.open(SRC).convert('RGBA'))
H, W = base.shape[:2]
hsv = lambda c: colorsys.rgb_to_hsv(*(np.array(c[:3], float) / 255))
LIT = {0: (255, 246, 210), 1: (255, 227, 138), 2: (242, 199, 92)}


def cyclic(n_events, lo, hi):
    on = set()
    for _ in range(n_events):
        st, ln = rnd.randint(0, N), rnd.randint(lo, hi + 1)
        on |= {(st + k) % N for k in range(ln)}
    return on


# ---- office panes: glass pieces below the dome, big enough to be a window, not the door ----
glass = np.zeros((H, W), bool)
for y in range(H):
    for x in range(W):
        r, g, b, a = base[y, x]
        if a:
            h, s, v = hsv((r, g, b))
            glass[y, x] = 0.42 < h < 0.56 and s > 0.18 and v > 0.62
lab, n = ndimage.label(glass, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])
panes = []
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    if len(ys) >= 35 and ys.min() >= 88 and not (ys.min() >= 155 and xs.min() >= 95 and xs.max() <= 110):
        panes.append((ys, xs))
schedule = []
for k, _ in enumerate(panes):
    r_ = rnd.rand()
    schedule.append(cyclic(1, 8, 18) if r_ < 0.45 else (cyclic(2, 6, 12) if r_ < 0.6 else set()))
print(len(panes), 'office panes;', sum(1 for s in schedule if s), 'of them switch on at some point')

# ---- the tiny city's window dots ----
cands = []
for y in range(56, 83):
    for x in range(110, 149):
        r, g, b, a = base[y, x]
        if a and hsv((r, g, b))[2] > 0.9 and hsv((r, g, b))[1] < 0.2:
            cands.append((y, x))
rnd.shuffle(cands)
twinkle = [(yx, cyclic(rnd.randint(1, 3), 1, 3)) for yx in cands[:16]]

# ---- the drone: four rotor rings and a light on its body ----
pad = np.zeros((H, W), bool)
for y in range(138, 158):
    for x in range(188, 220):
        r, g, b, a = base[y, x]
        if a:
            h, s, v = hsv((r, g, b))
            pad[y, x] = 0.4 < h < 0.6 and s > 0.15
rl, rn = ndimage.label(pad)
rotors = []
for i in range(1, rn + 1):
    ys, xs = np.nonzero(rl == i)
    if 4 <= len(ys) <= 40:
        cy, cx = ys.mean(), xs.mean()
        order = np.argsort(np.arctan2(ys - cy, xs - cx))
        rotors.append((ys[order], xs[order]))
print(len(rotors), 'rotors')
body = [(y, x) for y in range(144, 152) for x in range(198, 208)
        if base[y, x, 3] and 0.85 < hsv(base[y, x])[0] + (1 if hsv(base[y, x])[0] < 0.1 else 0) < 1.05 and hsv(base[y, x])[1] > 0.2]
body.sort(key=lambda p: (abs(p[0] - 148) + abs(p[1] - 203)))
light = body[:2]
blink = {4, 5, 17, 29, 30}

# ---- a glint that sweeps the dome once a loop ----
dome = np.zeros((H, W), bool)
for y in range(33, 86):
    for x in range(88, 168):
        r, g, b, a = base[y, x]
        if a:
            h, s, v = hsv((r, g, b))
            dome[y, x] = 0.4 < h < 0.6 and v > 0.7 and not (110 <= x <= 149 and 56 <= y <= 83)

frames = []
for f in range(N):
    fr = base.copy()
    for (ys, xs), sch in zip(panes, schedule):
        if f in sch:
            for y, x in zip(ys, xs):
                v = hsv(base[y, x])[2]
                fr[y, x, :3] = LIT[0] if v > 0.92 else (LIT[1] if v > 0.72 else LIT[2])
    for (y, x), sch in twinkle:
        if f in sch:
            fr[y, x, :3] = LIT[1]
    for ys, xs in rotors:
        k = f % len(ys)
        for j in (k, (k + len(ys) // 2) % len(ys)):
            fr[ys[j], xs[j], :3] = (231, 250, 251)
    if f in blink:
        for (y, x) in light:
            fr[y, x, :3] = (238, 76, 147)
    g = f - 22
    if 0 <= g < 6:
        off = 60 + g * 16
        band = dome & (np.abs((np.arange(W)[None, :] + np.arange(H)[:, None]) - off - 70) < 3)
        fr[band, :3] = np.minimum(255, fr[band, :3].astype(int) + 40)
    frames.append(fr)

# crop to the plot's bottom corner and the top of the dome; keep the full 256 width
vis = np.stack([f[..., 3] for f in frames]).max(axis=0)
ys = np.nonzero(vis.any(axis=1))[0]
top, bot = ys.min(), ys.max()
frames = [f[top:bot + 1] for f in frames]
cols = sorted({tuple(p[:3]) for f in frames for p in f.reshape(-1, 4) if p[3]})
assert len(cols) < 255, len(cols)
pal = [0, 0, 0] + [c for col in cols for c in col]
pal += [0] * (768 - len(pal))
idx = {c: i + 1 for i, c in enumerate(cols)}
ims = []
for f in frames:
    a = np.zeros(f.shape[:2], np.uint8)
    for y in range(f.shape[0]):
        for x in range(f.shape[1]):
            if f[y, x, 3]:
                a[y, x] = idx[tuple(f[y, x, :3])]
    im = Image.fromarray(a, 'P'); im.putpalette(pal); ims.append(im)
out = str(NC / 'art/out/city-hall')
ims[0].save(out + '.gif', save_all=True, append_images=ims[1:], duration=[DELAY] * N, loop=0, transparency=0, disposal=1, optimize=False)
Image.fromarray(frames[0], 'RGBA').save(out + '.png')
print('city hall:', frames[0].shape[1], 'x', frames[0].shape[0], len(cols), 'colors,', N, 'frames')
