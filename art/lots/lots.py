"""Empty lots: four little scenes with slow, natural motion, at the new standard's double detail."""
import math, random
import numpy as np
from lots_kit import Layer, C, ID, W, H, blob, composite, save
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked

N, DELAY = 40, 200                         # 8 seconds
LT = H - 128                               # lots lie flat on the ground: no slab


def LP(a, b, z=0):
    return (128 + (a - b) * 32, LT + (a + b) * 16 - z)


def ground(col='lw', seed=1, speckle=220):
    g = Layer()
    g.poly([(128, LT - 0.5), (257, LT + 64), (128, LT + 128.5), (-1, LT + 64)], col)
    rnd = np.random.RandomState(seed)
    for _ in range(speckle):
        x, y = LP(rnd.uniform(0.1, 3.9), rnd.uniform(0.1, 3.9))
        g.px(x, y, 'lwd' if rnd.rand() < 0.75 else 'lwh')
    for k in range(128):                     # a curb line all round, so the lot meets the sidewalk cleanly
        g.px(k, LT + 64 - k / 2, 'pvj'); g.px(255 - k, LT + 64 - k / 2, 'pvj')
        g.px(k, LT + 64 + k / 2, 'pvj'); g.px(255 - k, LT + 64 + k / 2, 'pvj')
    return g


def patch(g, pts, col):
    g.poly([LP(a, b) for a, b in pts], col)


def tree(L, a, b, r, tint=0):
    x, y = LP(a, b)
    x, y = round(x), round(y)
    L.ellipse(x + 3, y + 1, r * 0.9, r * 0.4, 'lws')                  # shadow on the grass
    for zz in range(0, 9):
        L.px(x, y - zz, 'bark'); L.px(x + 1, y - zz, 'bark')
    base, hi, dk = (('leaf', 'lw', 'leafd'), ('lwd', 'lwh', 'leafd'))[tint]
    blob(L, x, y - 10 - r * 0.8, r, base, hi, dk)
    blob(L, x - r * 0.45, y - 8 - r * 0.5, r * 0.65, base, hi, dk)


def bench(L, a, b):
    x, y = LP(a, b)
    for k in range(12):
        L.px(x + k, y + k // 2 - 5, 'pk2'); L.px(x + k, y + k // 2 - 4, 'pk3'); L.px(x + k, y + k // 2 - 8, 'pk1')
    L.px(x + 1, y - 3, 'ws3'); L.px(x + 10, y + 2, 'ws3')


def lamp(L, a, b):
    x, y = LP(a, b)
    for zz in range(0, 20):
        L.px(x, y - zz, 'ws3')
    for dx in (-1, 0, 1):
        L.px(x + dx, y - 20, 'warm')
    L.px(x, y - 21, 'warm')


def butterfly(L, x, y, f, col):
    wing = f % 2 == 0                        # wings beat every frame: fast, but tiny
    L.px(x, y, 'ol')
    if wing:
        L.px(x - 1, y - 1, col); L.px(x + 1, y - 1, col); L.px(x - 2, y - 1, col); L.px(x + 2, y - 1, col)
    else:
        L.px(x - 1, y, col); L.px(x + 1, y, col)


def drift(f, cx, cy, rx, ry, k1=1, k2=2, ph=0.0):
    """A smooth closed path (a Lissajous curve), so the loop joins without a jump."""
    t = 2 * math.pi * f / N
    return cx + rx * math.sin(k1 * t + ph), cy + ry * math.sin(k2 * t + ph * 1.7)


# ---------------- 1. park ----------------
def park(f):
    g = ground(seed=21)
    path = [(0.0, 2.3), (1.2, 2.1), (2.2, 1.6), (4.0, 1.4), (4.0, 1.9), (2.4, 2.1), (1.3, 2.6), (0.0, 2.8)]
    patch(g, path, 'pv')
    for (a, b) in ((0.6, 2.35), (1.8, 2.05), (3.0, 1.62)):
        x, y = LP(a, b); g.px(x, y, 'pvj'); g.px(x + 1, y, 'pvj')
    for (a, b, c) in ((0.7, 0.8, 'pk1'), (0.9, 0.95, 'pk0'), (3.2, 3.2, 'warm2'), (3.0, 3.4, 'pk1'), (2.6, 3.1, 'ws1')):
        x, y = LP(a, b); g.px(x, y, c); g.px(x + 1, y - 1, c)
    L = Layer()
    for (a, b, r, t) in ((0.9, 1.1, 10, 0), (2.9, 0.8, 11, 1), (1.2, 3.3, 9, 1), (3.3, 2.9, 10, 0)):
        tree(L, a, b, r, t)
    bench(L, 2.0, 2.45)
    lamp(L, 1.15, 1.95)
    L.outlined()
    B = Layer()
    x, y = drift(f, 150, LT + 58, 36, 12, 1, 2)
    butterfly(B, round(x), round(y), f, 'pk1')
    return composite([g, L, B])


# ---------------- 2. pond ----------------
POND = (2.0, 2.0, 1.25, 0.9)             # centre a, b and radii in tiles
rnd_p = random.Random(3)
glints = [(rnd_p.uniform(-0.8, 0.8), rnd_p.uniform(-0.55, 0.55), rnd_p.randrange(N), rnd_p.randint(3, 6)) for _ in range(14)]


def in_pond(a, b, shrink=0.0):
    ca, cb, ra, rb = POND
    return ((a - ca) / (ra - shrink)) ** 2 + ((b - cb) / (rb - shrink)) ** 2 < 1


def pond(f):
    g = ground(seed=22)
    for y in range(H):
        for x in range(W):
            # invert the iso mapping to test the pond in plot coordinates
            u, v = (x - 128) / 32, (y - LT) / 16
            a, b = (v + u) / 2, (v - u) / 2
            if in_pond(a, b):
                if not in_pond(a, b, 0.08):
                    col = 'pvj'                                    # a stone edge
                elif not in_pond(a, b, 0.2):
                    col = 'g5'                                     # deeper water along the rim
                else:
                    col = 'g3' if ((a - POND[0]) + (b - POND[1])) < -0.55 else 'g4'   # sky caught in the upper left
                g.px(x, y, col)
    for (da, db, start, length) in glints:           # glints that come and go at their own times
        if (f - start) % N < length:
            x, y = LP(POND[0] + da, POND[1] + db)
            g.px(x, y, 'g1'); g.px(x + 1, y, 'g0'); g.px(x + 2, y, 'g1')
    L = Layer()
    for (a, b) in ((0.95, 1.6), (1.1, 2.7), (2.9, 1.2), (3.05, 2.5)):   # reeds at the water's edge
        x, y = LP(a, b)
        for k, h in ((0, 7), (2, 9), (4, 6)):
            L.line(x + k, y, x + k + 1, y - h, 'leafd')
    tree(L, 3.4, 0.55, 10, 0)
    tree(L, 0.5, 3.4, 9, 1)
    bench(L, 3.0, 3.35)
    L.outlined()
    D = Layer()
    for ph, col in ((0.0, 'wh'), (2.6, 'wh2')):           # two ducks paddling slow circles
        t = 2 * math.pi * f / N + ph
        a, b = POND[0] + 0.62 * math.cos(t), POND[1] + 0.42 * math.sin(t)
        x, y = LP(a, b)
        x, y = round(x), round(y)
        heading = -math.sin(t) * 0.62 - math.cos(t) * 0.42      # screen direction of travel
        s = 1 if heading > 0 else -1
        for dx, dy, c in ((0, 0, col), (s, 0, col), (-s, 0, col), (2 * s, -1, col), (2 * s, -2, col), (3 * s, -2, 'warm2'), (-s, -1, col), (0, -1, col)):
            D.px(x + dx, y + dy, c)
        D.px(x - 2 * s, y + 1, 'g1')                        # a small wake
    D.outlined()
    return composite([g, L, D])


# ---------------- 3. plaza with a fountain ----------------
rnd_f = random.Random(5)
drops = [(rnd_f.uniform(0, 2 * math.pi), rnd_f.uniform(0.6, 1.0), rnd_f.randrange(8)) for _ in range(16)]


def plaza(f):
    g = ground(col='pv', seed=23, speckle=0)
    for k in range(1, 8):                               # paving joints across the plaza
        t = k * 0.5
        for s in range(0, 129):
            x, y = LP(t, s / 32); g.px(x, y, 'pvj')
            x, y = LP(s / 32, t); g.px(x, y, 'pvj')
    for (a0, b0) in ((0.25, 0.25), (3.2, 0.25), (0.25, 3.2), (3.2, 3.2)):   # corner planters
        patch(g, [(a0, b0), (a0 + 0.55, b0), (a0 + 0.55, b0 + 0.55), (a0, b0 + 0.55)], 'lw')
    L = Layer()
    for (a0, b0) in ((0.25, 0.25), (3.2, 0.25), (0.25, 3.2), (3.2, 3.2)):
        x, y = LP(a0 + 0.27, b0 + 0.27)
        blob(L, x, y - 5, 7, 'leaf', 'lw', 'leafd')
    cx, cy = LP(2.0, 2.0)
    cx, cy = round(cx), round(cy)
    L.ellipse(cx, cy + 2, 40, 20, 'ws2')                # basin rim
    L.ellipse(cx, cy, 40, 20, 'wh')
    L.ellipse(cx, cy + 1, 35, 17.5, 'g5')               # water
    L.ellipse(cx, cy, 33, 16.5, 'g4')
    ring = (f * 3) % 33                                 # a ripple that spreads slowly outward
    for k in range(0, 360, 6):
        ang = math.radians(k)
        L.px(cx + (ring + 2) * math.cos(ang), cy + (ring + 2) * 0.5 * math.sin(ang), 'g3')
    L.ellipse(cx, cy - 2, 6, 3, 'wh')                   # the jet's pedestal
    for zz in range(0, 10):
        L.px(cx - 1, cy - 2 - zz, 'ws1'); L.px(cx, cy - 2 - zz, 'wm')
    bench(L, 1.95, 3.45)
    bench(L, 3.45, 1.95)
    L.outlined()
    Wt = Layer()                                        # droplets rising and falling: quick, but small
    for (ang, reach, ph) in drops:
        k = ((f + ph) % 8) / 8
        r = reach * 18 * k
        x = cx + r * math.cos(ang)
        y = cy - 12 - 16 * k + 22 * k * k + r * 0.5 * math.sin(ang)
        Wt.px(x, y, 'g0' if k < 0.5 else 'g1')
    for zz in range(0, 5):
        Wt.px(cx - 1, cy - 12 - zz, 'g0'); Wt.px(cx, cy - 12 - zz, 'g1')
    return composite([g, L, Wt])


# ---------------- 4. flower garden ----------------
def garden(f):
    g = ground(seed=24)
    patch(g, [(1.85, 0.0), (2.15, 0.0), (2.15, 4.0), (1.85, 4.0)], 'pv')      # a path down the middle
    rows = ['pk1', 'warm2', 'ws1', 'pk0', 'warm2', 'pk2']
    rnd_g = np.random.RandomState(8)
    for i, (a0, a1) in enumerate(((0.3, 1.6), (2.4, 3.7))):
        for r in range(6 if i == 0 else 5):                  # the right bed starts lower, leaving room for the shed
            b0 = (0.35 if i == 0 else 0.9) + r * 0.55
            patch(g, [(a0, b0), (a1, b0), (a1, b0 + 0.32), (a0, b0 + 0.32)], 'lwd')
            for _ in range(48):
                x, y = LP(rnd_g.uniform(a0 + 0.05, a1 - 0.05), rnd_g.uniform(b0 + 0.04, b0 + 0.28))
                g.px(x, y - 1, rows[(r + i * 2) % len(rows)])
                g.px(x, y, 'leafd')
    L = Layer()                                         # a little potting shed at the back corner, fully on the lot
    a0, a1, b0, b1 = 2.72, 3.52, 0.12, 0.66              # footprint: the ridge runs along a
    bm, eave, ridge, o = (b0 + b1) / 2, 16, 25, 0.05     # o: how far the roof overhangs the walls
    L.poly([LP(a0, b1, 0), LP(a1, b1, 0), LP(a1, b1, eave), LP(a0, b1, eave)], 'wh')            # front wall
    L.poly([LP(a1, b1, 0), LP(a1, b0, 0), LP(a1, b0, eave), LP(a1, b1, eave)], 'ws1')           # right wall
    L.poly([LP(a1, b1 + o, eave - 1), LP(a1, bm, ridge + 1), LP(a1, b0, eave), LP(a1, b1, eave)], 'ws1')   # its gable, right up to the roof line, so no seam shows
    L.poly([LP(a1, b1 - 0.14, 6), LP(a1, b1 - 0.3, 6), LP(a1, b1 - 0.3, 12), LP(a1, b1 - 0.14, 12)], 'ws3')   # gable window
    L.poly([LP(a0 + 0.26, b1, 0), LP(a0 + 0.46, b1, 0), LP(a0 + 0.46, b1, 11), LP(a0 + 0.26, b1, 11)], 'pk3')  # door
    L.poly([LP(a0 - o, b1 + o, eave - 1), LP(a1, b1 + o, eave - 1), LP(a1, bm, ridge + 1), LP(a0 - o, bm, ridge + 1)], 'pk1')  # roof, front slope: eaves overhang at the front only
    L.line(*LP(a1, b1 + o, eave - 1), *LP(a1, bm, ridge + 1), 'pk2')                       # the roof's edge up the gable, flush with it
    L.line(*LP(a1, bm, ridge + 1), *LP(a1, b0, eave), 'pk2')
    L.line(*LP(a0 - o, bm, ridge + 1), *LP(a1, bm, ridge + 1), 'pk0')                     # a light ridge
    tree(L, 0.45, 3.55, 9, 1)
    L.outlined()
    Bz = Layer()
    for ph, col, (cx, cy, rx, ry) in ((0.0, 'warm', (80, LT + 70, 26, 10)), (1.9, 'pk0', (178, LT + 72, 24, 9))):
        x, y = drift(f, cx, cy, rx, ry, 1, 2, ph)
        butterfly(Bz, round(x), round(y), f, col)
    return composite([g, L, Bz])


LOTS = [('park', park), ('pond', pond), ('plaza', plaza), ('garden', garden)]


def save_lot(name, frames):
    stack = np.stack(frames)
    vis = (stack > 0).any(axis=0)
    ys, xs = np.nonzero(vis)
    assert xs.min() == 0 and xs.max() == W - 1 and ys.max() == H - 1, (name, xs.min(), xs.max(), ys.max())
    return save('lot-' + name, frames, [DELAY] * N, str(NC / 'art/out'))


if __name__ == '__main__':
    import json, os
    os.makedirs(str(NC / 'art/out'), exist_ok=True)
    meta = []
    for name, fn in LOTS:
        info = save_lot(name, [fn(f) for f in range(N)])
        print(info)
        meta.append({'id': name, 'h': info['h']})
    json.dump(meta, open(str(NC / 'art/out/lots.json'), 'w'))
