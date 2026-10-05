"""Parks for empty lots, in the new standard. Still images; lamps glow at night through the palette swap."""
import math
import numpy as np
from kit import Canvas, Layer, plot, prism, circle, tree, composite, save, TW, ramp
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked

px = 1.25 / TW


def lamp(cv, a, b):
    L = Layer(cv)
    x, y = cv.P(a, b)
    x, y = round(x), round(y)
    for dy in range(0, 22):
        L.px(x, y - dy, 'l8'); L.px(x + 1, y - dy, 'l6')
    for dx in (-2, -1, 0, 1, 2, 3):
        L.px(x + dx, y - 22, 'l6')
    for dx in (-1, 0, 1, 2):
        for dy in (23, 24, 25):
            L.px(x + dx, y - dy, 'lit1' if dy != 25 else 'lit0')
    return L.outlined()


def bench(cv, a, b, along_a=True):
    L = Layer(cv)
    P = cv.P
    if along_a:
        L.quad(a, b, a + 0.32, b + 0.1, 'wood', z=4)
        L.poly([P(a, b + 0.1, 4), P(a + 0.32, b + 0.1, 4), P(a + 0.32, b + 0.1, 1), P(a, b + 0.1, 1)], 'p6')
        L.poly([P(a, b, 9), P(a + 0.32, b, 9), P(a + 0.32, b, 5), P(a, b, 5)], 'wood')
    else:
        L.quad(a, b, a + 0.1, b + 0.32, 'wood', z=4)
        L.poly([P(a + 0.1, b, 4), P(a + 0.1, b + 0.32, 4), P(a + 0.1, b + 0.32, 1), P(a + 0.1, b, 1)], 'p6')
        L.poly([P(a, b, 9), P(a, b + 0.32, 9), P(a, b + 0.32, 5), P(a, b, 5)], 'wood')
    return L.outlined()


def trees(cv, spots, seed):
    out = []
    for i, (a, b, r) in enumerate(sorted(spots, key=lambda t: t[0] + t[1])):
        L = Layer(cv)
        x, y = cv.P(a, b)
        tree(L, x, y, r, seed=seed + i)
        out.append(L.outlined())
    return out


def tile_path(g, a0, b0, a1, b1):
    g.quad(a0, b0, a1, b1, 'tile')
    along_a = (a1 - a0) > (b1 - b0)
    n = int(round(((a1 - a0) if along_a else (b1 - b0)) / 0.38))
    for k in range(1, n):
        if along_a:
            s = a0 + k * (a1 - a0) / n; g.quad(s, b0, s + px, b1, 'l5')
        else:
            s = b0 + k * (b1 - b0) / n; g.quad(a0, s, a1, s + px, 'l5')


def flowers(g, a0, b0, a1, b1, seed):
    rnd = np.random.RandomState(seed)
    g.quad(a0, b0, a1, b1, 'leafDk')
    g.quad(a0 + px, b0 + px, a1 - px, b1 - px, 'leaf')
    for _ in range(int((a1 - a0) * (b1 - b0) * 90)):
        x, y = g.cv.P(rnd.uniform(a0 + 0.04, a1 - 0.04), rnd.uniform(b0 + 0.04, b1 - 0.04))
        c = rnd.choice(['flower', 'flowerHi', 'p3', 'lit1'])
        g.px(x, y, c)
        if rnd.rand() < 0.4:
            g.px(x + 1, y, c)


def grove():
    cv = Canvas(224)
    g = plot(cv, seed=1)
    tile_path(g, 0.44, 1.84, 3.56, 2.16)
    tile_path(g, 1.84, 0.44, 2.16, 3.56)
    layers = [g, bench(cv, 2.3, 1.62), lamp(cv, 1.72, 2.3)]
    layers += trees(cv, [(0.95, 1.0, 12), (1.3, 1.45, 9), (2.9, 1.05, 11), (1.05, 2.9, 10), (2.85, 2.85, 12), (3.2, 2.45, 8)], 7)
    return cv, layers


def fountain():
    cv = Canvas(224)
    g = plot(cv, seed=2)
    for (a0, b0, a1, b1) in ((0.44, 1.86, 3.56, 2.14), (1.86, 0.44, 2.14, 3.56)):
        tile_path(g, a0, b0, a1, b1)
    g.poly([cv.P(a, b) for (a, b) in circle(2, 2, 0.78)], 'tile')
    g.poly([cv.P(a, b) for (a, b) in circle(2, 2, 0.8)], lambda x, y: g.get(x, y) or 'tile')
    Fn = Layer(cv)
    prism(cv, Fn, circle(2, 2, 0.42), 0, 7, facade=lambda s, z, sh, x, y: ramp(sh, ['white', 'rim', 'l1', 'tile', 'l4'], x, y), roof='l4')
    Fn.poly([cv.P(a, b, 7) for (a, b) in circle(2, 2, 0.34)], 'g4')
    for (a, b) in circle(2, 2, 0.25, 10):
        x, y = cv.P(a, b, 7); Fn.px(x, y, 'g2')
    prism(cv, Fn, circle(2, 2, 0.07, 12), 7, 20, roof='rim')
    x, y = cv.P(2, 2, 22)
    for dx, dy in ((0, 0), (-2, 1), (2, 1), (-3, 3), (3, 3)):
        Fn.px(x + dx, y + dy, 'g1')
    Fn.outlined()
    layers = [g, Fn, bench(cv, 1.25, 2.3), bench(cv, 2.55, 1.3, along_a=False), lamp(cv, 2.55, 2.55)]
    layers += trees(cv, [(1.0, 1.0, 11), (3.0, 1.0, 10), (1.0, 3.0, 10), (3.05, 3.0, 12)], 17)
    return cv, layers


def garden():
    cv = Canvas(224)
    g = plot(cv, seed=3)
    tile_path(g, 0.44, 2.6, 3.56, 2.9)
    for (a0, b0, a1, b1, sd) in ((0.8, 0.8, 1.9, 1.4, 1), (2.1, 0.8, 3.2, 1.4, 2), (0.8, 1.7, 1.9, 2.3, 3), (2.1, 1.7, 3.2, 2.3, 4)):
        flowers(g, a0, b0, a1, b1, sd)
    H = Layer(cv)
    prism(cv, H, [(0.7, 3.1), (3.3, 3.1), (3.3, 3.28), (0.7, 3.28)][::-1], 0, 8,
          facade=lambda s, z, sh, x, y: ramp(sh, ['lawnHi', 'leaf', 'leafDk', 'lawnEdge'], x, y), roof='leaf')
    H.outlined()
    layers = [g, H, bench(cv, 1.6, 2.42), lamp(cv, 3.3, 2.5)]
    layers += trees(cv, [(0.75, 3.55, 9), (3.45, 0.9, 11)], 27)
    return cv, layers


def pond():
    cv = Canvas(224)
    g = plot(cv, seed=4)
    shape = [(2.0 + 0.95 * math.cos(t) + 0.12 * math.cos(3 * t), 1.95 + 0.62 * math.sin(t) + 0.08 * math.sin(2 * t))
             for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    g.poly([cv.P(a, b) for (a, b) in shape], 'l4')
    inner = [(2.0 + (a - 2.0) * 0.9, 1.95 + (b - 1.95) * 0.86) for (a, b) in shape]
    g.poly([cv.P(a, b) for (a, b) in inner], 'g5')
    g.poly([cv.P(2.0 + (a - 2.0) * 0.7, 1.95 + (b - 1.95) * 0.62) for (a, b) in shape], 'g4')
    rnd = np.random.RandomState(5)
    for _ in range(26):
        a, b = 2.0 + rnd.uniform(-0.6, 0.6), 1.95 + rnd.uniform(-0.35, 0.35)
        x, y = cv.P(a, b)
        g.px(x, y, 'g2'); g.px(x + 1, y, 'g2')
    for (a, b) in ((1.35, 1.7), (2.55, 2.2)):                  # lily pads
        x, y = cv.P(a, b)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1), (1, -1)):
            g.px(x + dx, y + dy, 'leaf')
        g.px(x, y - 1, 'flower')
    tile_path(g, 1.0, 3.0, 3.56, 3.28)
    layers = [g, bench(cv, 2.0, 2.78), lamp(cv, 1.2, 3.35)]
    layers += trees(cv, [(0.85, 0.9, 12), (3.2, 0.95, 10), (0.9, 2.55, 9), (3.3, 2.7, 11)], 37)
    return cv, layers


if __name__ == '__main__':
    import json
    meta = []
    for name, fn in (('grove', grove), ('fountain', fountain), ('garden', garden), ('pond', pond)):
        cv, layers = fn()
        fr = composite(cv, layers)
        info = save('park-' + name, cv, [fr], [1000], str(NC / 'art/out'))
        meta.append({'id': name, 'h': info['h']})
        print(info)
    json.dump(meta, open(str(NC / 'art/out/parks.json'), 'w'))
