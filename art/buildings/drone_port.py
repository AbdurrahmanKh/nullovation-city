"""The drone port, one of the held buildings (bus depot, drone port, apartment block, cafe, library), animated in place
from its PixelLab still (Pro, the city hall as the style image: PixelLab test 5). Its lot is checked against the
city's plot first (art/kit/fixlot.py); PixelLab drew that plot exactly, so it is kept as drawn.
Only existing pixels change, calmly, over a 10-second loop: the mint lights round the rooftop pad brighten in a slow,
uneven chase; the drone's four rotors spin and its nav lights blink; the control tower's pink beacon blinks softly every
few seconds; the hangar door's warm glow breathes; now and then a parcel locker's light comes on. The peaks use the
colors the tool keeps lit at night (cyan-mint, neon pink, warm yellow), so the port still shows life after dark.
Reads art/sources/drone-port.png; writes art/out/drone-port.gif and .png, checked frame by frame against the tool's
own GIF decoder. Two wall shades are nudged so the walls do not glow at night (below)."""
import colorsys, json, math, pathlib, subprocess, sys, tempfile
import numpy as np
from PIL import Image

NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
sys.path.insert(0, str(NC / 'art' / 'kit'))
from fixlot import fit

SRC = NC / 'art' / 'sources' / 'drone-port.png'
OUT = NC / 'art' / 'out'
DECODER = (NC / 'src' / 'js' / '35-gif.js').as_posix()
N, DELAY = 40, 250
rnd = np.random.RandomState(11)
still = Image.open(SRC).convert('RGBA')
T = int(np.nonzero(np.array(still)[..., 3].any(axis=1))[0].min())   # rows above the art; the boxes below use the still's rows
base, note = fit(still)
print('lot:', note)
# the tool keeps warm creams lit at night (isLightColor in src/js/30-pixel.js), which would make these two wall shades
# glow after dark; each is nudged just outside that rule, a change too small to see by day
for day, safe in (((226, 202, 175), (220, 202, 175)), ((236, 198, 166), (236, 190, 166))):
    base[np.all(base[..., :3] == day, axis=-1) & (base[..., 3] > 0), :3] = safe
base = base.astype(float)
H, W = base.shape[:2]
hsv = np.zeros((H, W, 3))
for y in range(H):
    for x in range(W):
        hsv[y, x] = colorsys.rgb_to_hsv(*(base[y, x, :3] / 255))
Hh, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
op = base[..., 3] > 0
yy, xx = np.mgrid[0:H, 0:W]
box = lambda x0, x1, y0, y1: op & (xx >= x0) & (xx <= x1) & (yy >= y0 - T) & (yy <= y1 - T)
ink = op & (base[..., :3].sum(-1) < 120)


def parts(mask):
    """The 4-connected pieces of a mask, largest first."""
    seen, out = np.zeros_like(mask), []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        stack, piece = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            piece.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v, u = y + dy, x + dx
                if 0 <= v < H and 0 <= u < W and mask[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    stack.append((v, u))
        out.append(piece)
    return sorted(out, key=len, reverse=True)


def toward(px, target, t):
    return px * (1 - t) + np.array(target, float) * t


# ---- the pad's mint lights: the gems on the pad's rim chase round it; the three on its side breathe ----
DRONE = box(117, 146, 63, 79)
GREEN = (Hh > 0.3) & (Hh < 0.45) & (S > 0.4) & (V > 0.6)
near = np.zeros_like(GREEN)
near[1:] |= GREEN[:-1]; near[:-1] |= GREEN[1:]; near[:, 1:] |= GREEN[:, :-1]; near[:, :-1] |= GREEN[:, 1:]
GEM = GREEN | (near & (S < 0.15) & (V > 0.9))                                          # each gem with its white glint
RIM_AT = [(131, 61), (150, 66), (158, 76), (150, 86), (131, 91), (111, 86), (103, 76), (111, 66)]   # clockwise
SIDE_AT = [(116, 93), (131, 96), (145, 93)]
centers = RIM_AT + SIDE_AT
lights = [[] for _ in centers]
for y, x in zip(*np.nonzero(box(96, 166, 56, 100) & GEM & ~DRONE)):                # each gem pixel to its nearest light
    d = [math.hypot(x - cx, y + T - cy) for cx, cy in centers]
    if min(d) <= 4.5:
        lights[int(np.argmin(d))].append((y, x))
RIM, SIDE = lights[:len(RIM_AT)], lights[len(RIM_AT):]
GLOW = lambda c: (min(119, c[0] * 0.6 + 40), 244, min(255, max(224, c[2] + 100)))   # cyan-mint: kept lit at night

# a slow lap of the rim, a light at a time, at uneven steps that add up to the loop
steps = rnd.randint(2, 6, len(RIM)).astype(float)
steps = np.round(steps / steps.sum() * N).astype(int)
steps[-1] += N - steps.sum()
RIM_LV = [dict() for _ in range(N)]
f = 0
for i, n in enumerate(steps):
    for k in range(n):
        RIM_LV[(f + k) % N][i] = 1.0
        RIM_LV[(f + k + n) % N].setdefault(i, 0.45)                                # it fades as the next one lights
    f += n
SIDE_LV = [[0.5 + 0.5 * math.sin(2 * math.pi * (k / N + j / 3) + 0.4 * math.sin(4 * math.pi * k / N)) for j in range(3)]
           for k in range(N)]

# ---- the drone: four rotors, each a small disc inside its ink ring, and two nav lights ----
ROTORS = []
for gx, gy in ((123, 67), (139, 67), (122, 75), (139, 75)):
    gy -= T
    ring = [(y, x) for y, x in zip(*np.nonzero(ink)) if abs(x - gx) <= 3 and abs(y - gy) <= 2]
    cy, cx = np.mean([y for y, _ in ring]), np.mean([x for _, x in ring])
    disc = [(y, x) for y in range(int(cy) - 2, int(cy) + 3) for x in range(int(cx) - 3, int(cx) + 4)
            if op[y, x] and not ink[y, x] and not GREEN[y, x] and not (0.05 < Hh[y, x] < 0.12 and S[y, x] > 0.4)
            and ((x - cx) / 2.6) ** 2 + ((y - cy) / 1.4) ** 2 <= 1]
    disc.sort(key=lambda p: math.atan2(p[0] - cy, (p[1] - cx) / 2))
    ROTORS.append(disc)
NAV_G = DRONE & GREEN
NAV_O = DRONE & (Hh > 0.05) & (Hh < 0.12) & (S > 0.4) & (V > 0.85)
NAV_ON = {k: (k // 3) % 2 == 0 for k in range(N)}                                  # green and orange take turns

# ---- the control tower's pink beacon: three soft blinks a loop ----
BEACON = box(170, 186, 32, 48) & ((Hh > 0.85) | (Hh < 0.03)) & (S > 0.25) & (V > 0.5)
BEACON_LV = {}                                                                      # neon, a pale flash, neon
for st in (2, 15, 29):
    for k, step in enumerate((((255, 95, 168), 1.0), ((255, 214, 232), 0.6), ((255, 95, 168), 0.8))):
        BEACON_LV[st + k] = step

# ---- the hangar door's warm glow, and its light on the paving, breathing slowly ----
DOOR = box(84, 122, 124, 160) & (Hh > 0.06) & (Hh < 0.17) & (S > 0.3) & (V > 0.85)
SPILL = box(70, 135, 130, 175) & np.all(base[..., :3] == (236, 224, 217), axis=-1)
DOOR_LV = []
for k in range(N):
    t = 2 * math.pi * k / N
    DOOR_LV.append(round(3 * min(1, max(0, 0.5 - 0.5 * math.cos(t) + 0.15 * math.sin(3 * t + 1)))) / 3)

# ---- parcel lockers: now and then one lights up, as if a parcel just went in ----
KEYHOLES = [(144, 187), (153, 170), (145, 195)]
LOCKER_LV = [dict() for _ in range(N)]
for j, st in enumerate((7, 22, 33)):
    for k, lv in enumerate((1.0, 1.0, 0.5)):
        LOCKER_LV[(st + k) % N][j] = lv

frames = []
for k in range(N):
    fr = base.copy()
    for i, lv in RIM_LV[k].items():
        for y, x in RIM[i]:
            fr[y, x, :3] = toward(base[y, x, :3], GLOW(base[y, x, :3]), lv)
    for j, p in enumerate(SIDE):
        lv = SIDE_LV[k][j % 3]
        for y, x in p:
            fr[y, x, :3] = toward(base[y, x, :3], (176, 240, 208), 0.35 * round(lv * 2) / 2)
    for disc in ROTORS:
        n = len(disc)
        for j in (3 * k % n, (3 * k + n // 2) % n):                                  # one blade, both its ends, spinning fast
            y, x = disc[j]
            fr[y, x, :3] = (150, 125, 174)
    if not NAV_ON[k]:
        fr[NAV_G, :3] = toward(base[NAV_G, :3], (40, 120, 80), 0.6)
    else:
        fr[NAV_O, :3] = toward(base[NAV_O, :3], (150, 100, 60), 0.6)
    if k in BEACON_LV:
        fr[BEACON, :3] = toward(base[BEACON, :3], *BEACON_LV[k])
    lv = DOOR_LV[k]
    fr[DOOR, :3] = toward(base[DOOR, :3], (236, 170, 95), 0.22 * lv)
    fr[SPILL, :3] = toward(base[SPILL, :3], (214, 199, 228), 0.4 * lv)
    for j, lv in LOCKER_LV[k].items():
        y, x = KEYHOLES[j]
        fr[y - T, x, :3] = toward(np.array((150, 230, 220.0)), (96, 244, 232), lv)
    frames.append(np.clip(np.round(fr), 0, 255).astype(np.uint8))

# ---- one palette for every frame, transparency at 0; the silhouette never changes ----
for f_ in frames:
    f_[f_[..., 3] == 0] = 0
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
gif = str(OUT / 'drone-port.gif')
ims[0].save(gif, save_all=True, append_images=ims[1:], duration=[DELAY] * N, loop=0, transparency=0, disposal=1, optimize=False)
Image.fromarray(frames[0], 'RGBA').save(str(OUT / 'drone-port.png'))

dec = pathlib.Path(tempfile.gettempdir()) / '_drone_port_d.bin'
js = f"""const fs = require('fs'); const {{ decodeGif }} = require({json.dumps(DECODER)});
const g = decodeGif(new Uint8Array(fs.readFileSync({json.dumps(gif)})));
fs.writeFileSync({json.dumps(str(dec))}, Buffer.concat(g.frames.map(f => Buffer.from(f.rgba.buffer)))); console.log(g.frames.length);"""
n = int(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout.strip())
got = np.frombuffer(dec.read_bytes(), np.uint8).reshape(n, *frames[0].shape)
seen = lambda a: np.where(a[..., 3:4] > 0, a, 0)
exact = n == N and not np.any(seen(got) != seen(np.stack(frames)))
changed = [int((np.abs(seen(f_).astype(int) - seen(frames[0]).astype(int)).max(-1) > 0).sum()) for f_ in frames]
print(f'parts: rim lights {[len(p) for p in RIM]} px, side lights {[len(p) for p in SIDE]} px, rotor discs {[len(d) for d in ROTORS]}, nav lights '
      f'{int(NAV_G.sum())} + {int(NAV_O.sum())} px, beacon {int(BEACON.sum())} px, door {int(DOOR.sum())} px, spill {int(SPILL.sum())} px')
print(f'drone port: {frames[0].shape[1]} x {frames[0].shape[0]}, {N} frames at {DELAY} ms, {len(cols)} colors, '
      f'{pathlib.Path(gif).stat().st_size // 1024} KB, changed pixels per frame {min(changed)} to {max(changed)}, '
      f'{"decodes exactly" if exact else "DOES NOT decode exactly"} in the tool')
