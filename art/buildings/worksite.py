"""Worksite, new standard: a building under construction, for projects that are still an idea.
Motion: the crane's jib swings slowly on an uneven rhythm, its load sways a little behind,
the crane-top light blinks now and then, and welding sparks flicker in short bursts (small and fast)."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, plot, prism, composite, ramp, save, HX, HY
import pathlib, tempfile
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
TMP = pathlib.Path(tempfile.gettempdir())

N, DELAY = 48, 250
rect = lambda a0, b0, a1, b1: [(a1, b0), (a1, b1), (a0, b1), (a0, b0)]   # counter-clockwise from above
CONCRETE = ['l1', 'tile', 'l3', 'l4', 'l5', 'l6']
LIGHT = {3, 4, 19, 33, 34, 44}                          # the crane-top light: irregular blinks
SPARKS = {7: 4, 8: 6, 9: 3, 25: 5, 26: 2, 39: 6, 40: 4}   # frame: how many sparks


def concrete(s, z, shade, x, y):
    return ramp(shade, CONCRETE, x, y)


def level_one(s, z, shade, x, y):
    """The finished ground floor: concrete with dark, unglazed openings."""
    if 7 <= z < 20 and (s % 0.42) > 0.1 and (s % 0.42) < 0.32:
        return 'l8' if shade < 0.5 else 'ink'
    if z < 3:
        return ramp(shade, ['l3', 'l4', 'l5', 'l6'], x, y)
    return ramp(shade, CONCRETE, x, y)


def lattice(s, z, shade, x, y):
    """A crane mast: corner chords and diagonal bracing, open in between."""
    edge = (s % 0.2) < 0.035 or (s % 0.2) > 0.165
    k = (z * 0.9 + s * 60) % 14
    brace = k < 1.6 or abs(k - 7) < 0.8
    if edge or brace:
        return 'craneDk' if shade > 0.55 else ('crane' if shade > 0.15 else 'craneHi')
    return False


def column(L, cv, a, b, z0, z1, r=0.065):
    prism(cv, L, rect(a - r, b - r, a + r, b + r), z0, z1, facade=concrete, roof='l1')


def frame(f):
    cv = Canvas(390)
    P = cv.P
    rnd = np.random.RandomState(100 + f)
    g = plot(cv, ground='dirt', seed=9)

    # the crane's foot and mast, behind the building on the right
    M = Layer(cv)
    ma, mb, top = 3.4, 0.95, 152
    prism(cv, M, rect(ma - 0.2, mb - 0.2, ma + 0.2, mb + 0.2), 0, 7, facade=concrete, roof='l3')
    prism(cv, M, rect(ma - 0.1, mb - 0.1, ma + 0.1, mb + 0.1), 7, top, facade=lattice, roof=None)
    M.outlined()

    # the building: a finished ground floor, an open frame above it, a half-poured third slab, rebar on top
    B = Layer(cv)
    a0, b0, a1, b1 = 1.3, 1.1, 2.9, 2.7
    prism(cv, B, rect(a0, b0, a1, b1), 0, 26, facade=level_one, roof='l1')
    prism(cv, B, rect(a0 - 0.05, b0 - 0.05, a1 + 0.05, b1 + 0.05), 26, 29, facade=lambda s, z, sh, x, y: ramp(sh, ['white', 'l1', 'tile', 'l3'], x, y), roof='l1')
    cols = [(1.35, 1.15), (2.1, 1.15), (2.85, 1.15), (1.35, 1.9), (2.85, 1.9), (1.35, 2.65), (2.1, 2.65), (2.85, 2.65)]
    for (a, b) in sorted(cols, key=lambda c: c[0] + c[1]):
        column(B, cv, a, b, 29, 52)
    prism(cv, B, rect(a0 - 0.05, b0 - 0.05, a1 + 0.05, 1.98), 52, 55, facade=lambda s, z, sh, x, y: ramp(sh, ['white', 'l1', 'tile', 'l3'], x, y), roof='l1')
    for (a, b) in sorted([(1.35, 1.15), (2.1, 1.15), (2.85, 1.15), (2.85, 1.9)], key=lambda c: c[0] + c[1]):
        column(B, cv, a, b, 55, 70)
    B.outlined()
    R = Layer(cv)                                        # rebar sticking up out of the columns
    for (a, b) in [(1.35, 1.15), (2.1, 1.15), (2.85, 1.15), (2.85, 1.9), (1.35, 1.9)]:
        zb = 70 if (a, b) != (1.35, 1.9) else 55
        for dx in (-2, 2):
            x, y = P(a, b, zb)
            R.line(x + dx, y, x + dx + (1 if dx > 0 else -1), y - 9, 'p6')
    # a green safety net over the open floor, on the right face
    Nn = Layer(cv)
    for i in range(160):
        bb = 1.2 + 1.4 * i / 159
        for z in range(30, 52):
            x, y = P(a1 + 0.1, bb, z)
            if (int(x) + int(y)) % 2 == 0:
                Nn.px(x, y, 'net' if z % 6 else 'netHi')
    # scaffolding across the front: poles, ledgers, and plank decks
    S = Layer(cv)
    sb = b1 + 0.12
    for k in range(6):
        a = 1.28 + k * 0.33
        x0, y0 = P(a, sb, 0); x1, y1 = P(a, sb, 60)
        S.line(x0, y0, x1, y1, 'steel')
    for z in (14, 28, 42, 56):
        xa, ya = P(1.28, sb, z); xb, yb = P(2.93, sb, z)
        S.line(xa, ya, xb, yb, 'steel')
    for z in (28, 42):
        S.poly([P(1.28, sb - 0.1, z + 2), P(2.93, sb - 0.1, z + 2), P(2.93, sb + 0.06, z + 2), P(1.28, sb + 0.06, z + 2)], 'wood')
        S.poly([P(1.28, sb + 0.06, z + 2), P(2.93, sb + 0.06, z + 2), P(2.93, sb + 0.06, z), P(1.28, sb + 0.06, z)], 'woodDk')
    for k in range(5):                                   # cross bracing
        a = 1.28 + k * 0.33
        xa, ya = P(a, sb, 14 + (k % 2) * 14); xb, yb = P(a + 0.33, sb, 28 + (k % 2) * 14)
        S.line(xa, ya, xb, yb, 'l5')
    S.outlined()
    # the site cabin, stacked beams, and cones at the front
    Cb = Layer(cv)
    prism(cv, Cb, rect(0.6, 2.95, 1.38, 3.45), 0, 20,
          facade=lambda s, z, sh, x, y: ('lit1' if 8 <= z < 15 and 0.18 < s % 1.3 < 0.42 else ('p3' if z > 17 else None)), roof='l4')
    Cb.outlined()
    St = Layer(cv)
    for layer, z in enumerate((0, 5, 10)):
        off = 0.04 * layer
        prism(cv, St, rect(2.95 + off, 3.0 + off, 3.42 - off, 3.36 - off), z, z + 5, facade=lambda s, zz, sh, x, y: ramp(sh, ['dirtHi', 'wood', 'woodDk'], x, y), roof='dirtHi')
    St.outlined()
    Co = Layer(cv)
    for (a, b) in ((1.72, 3.32), (2.08, 3.4)):
        x, y = P(a, b)
        x, y = round(x), round(y)
        for r in range(9):
            half = 1 + r * 0.45
            col = 'white' if r in (3, 4) else 'safety'
            for dx in range(-round(half), round(half) + 1):
                Co.px(x + dx, y - 9 + r, col)
    Co.outlined()

    # the crane's top: jib swinging slowly on an uneven rhythm, counter-jib, ties, trolley, and a swaying load
    K = Layer(cv)
    base = math.atan2(0.95, -1.3)
    th = base + math.radians(8) * math.sin(2 * math.pi * f / N) + math.radians(2.5) * math.sin(4 * math.pi * f / N + 1.1)
    ca, sa = math.cos(th), math.sin(th)
    jz = top + 4
    tip = (ma + 2.3 * ca, mb + 2.3 * sa)
    tail = (ma - 0.75 * ca, mb - 0.75 * sa)
    prism(cv, K, rect(ma - 0.13, mb - 0.13, ma + 0.13, mb + 0.13), top, top + 8, facade=lambda s, z, sh, x, y: ramp(sh, ['craneHi', 'crane', 'craneDk'], x, y), roof='crane')
    prism(cv, K, rect(ma + 0.02, mb + 0.1, ma + 0.2, mb + 0.26), top, top + 9, facade=lambda s, z, sh, x, y: 'g4' if z > top + 3 else ramp(sh, ['crane', 'craneDk'], x, y), roof='crane')
    for d0, d1 in ((0, 1),):
        pass
    K.outlined()
    J = Layer(cv)                                        # thin lattice lines: no outline, so the swing stays calm
    steps = 70
    for i in range(steps):                               # the jib: two chords with a zigzag between them
        t0, t1 = i / steps, (i + 1) / steps
        a_0, b_0 = ma + (tip[0] - ma) * t0, mb + (tip[1] - mb) * t0
        a_1, b_1 = ma + (tip[0] - ma) * t1, mb + (tip[1] - mb) * t1
        xa, ya = P(a_0, b_0, jz + 5); xb, yb = P(a_1, b_1, jz + 5)
        J.line(xa, ya, xb, yb, 'crane')
        xa, ya = P(a_0, b_0, jz); xb, yb = P(a_1, b_1, jz)
        J.line(xa, ya, xb, yb, 'craneDk')
        if i % 6 == 0:
            xc, yc = P(a_0, b_0, jz + (5 if (i // 6) % 2 else 0)); xd, yd = P(a_1 + (tip[0] - ma) * 5 / steps, b_1 + (tip[1] - mb) * 5 / steps, jz + (0 if (i // 6) % 2 else 5))
            J.line(xc, yc, xd, yd, 'crane')
    xa, ya = P(ma, mb, jz + 2); xb, yb = P(*tail, jz + 2)   # counter-jib and its counterweight
    J.line(xa, ya, xb, yb, 'craneDk'); J.line(xa, ya - 2, xb, yb - 2, 'crane')
    W = Layer(cv)
    wx, wy = P(*tail, jz)
    for dy in range(-6, 3):
        for dx in range(-5, 6):
            W.px(wx + dx, wy + dy, 'l4' if dx < 0 else 'l5')
    px_, py_ = P(ma, mb, top + 24)                       # the peak, with ties out to both ends
    J.line(px_, py_, *P(ma, mb, top + 8), 'crane')
    J.line(px_, py_, *P(tip[0] * 0.55 + ma * 0.45, tip[1] * 0.55 + mb * 0.45, jz + 5), 'craneDk')
    J.line(px_, py_, *P(*tail, jz + 3), 'craneDk')
    tr = (ma + (tip[0] - ma) * 0.62, mb + (tip[1] - mb) * 0.62)
    sway = round(1.2 * math.sin(2 * math.pi * f / N - 0.9))
    tx, ty = P(*tr, jz)
    lx, ly = P(*tr, 96)
    J.line(tx, ty, lx + sway, ly, 'l6')
    for dy in range(0, 5):                               # the load: a bundle of beams
        for dx in range(-9, 10):
            W.px(lx + sway + dx, ly + dy + 1, 'steel' if dy % 2 == 0 else 'l5')
    W.px(lx + sway, ly, 'ink')
    W.outlined()

    # the light on the peak, and welding sparks on the top floor
    Lt = Layer(cv)
    on = f in LIGHT
    for dx, dy in ((0, -1), (1, -1), (0, -2), (1, -2)):
        Lt.px(px_ + dx, py_ + dy, 'neonP' if on else 'p5')
    Sp = Layer(cv)
    if f in SPARKS:
        sx, sy = P(2.1, 1.15, 63)
        for _ in range(SPARKS[f]):
            Sp.px(sx + rnd.randint(-5, 6), sy + rnd.randint(-5, 3), rnd.choice(['lit0', 'white', 'lit1']))
        Sp.px(sx, sy, 'white'); Sp.px(sx + 1, sy, 'lit0')
    Wl = Layer(cv)                                       # red warning lights on the mast top and the jib tip, blinking slowly
    if f % 16 < 3:
        for (pa, pb, pz) in ((ma, mb, top + 10), (tip[0], tip[1], jz + 1)):
            x, y = P(pa, pb, pz)
            for dx, dy in ((0, 0), (1, 0), (0, -1), (1, -1)):
                Wl.px(x + dx, y + dy, 'neonP')
    return cv, composite(cv, [g, M, B, R, Nn, S, Cb, St, Co, J, K, W, Lt, Sp, Wl])


if __name__ == '__main__':
    frames = []
    for f in range(N):
        cv, fr = frame(f)
        frames.append(fr)
    info = save('worksite', cv, frames, [DELAY] * N, str(NC / 'art/out'), disposal=2)   # the jib swings over open sky
    print(info)
    import numpy as np
    np.save(str(TMP / 'worksite-src.npy'), np.stack(frames))
