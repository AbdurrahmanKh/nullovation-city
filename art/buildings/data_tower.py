"""Data tower, new standard: a glass tower with rounded corners and light strips, calm and irregular motion."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, plot, prism, rounded_rect, circle, tree, composite, ramp, save, HX, HY
from parks import bench, lamp
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked

N = 32
DELAY = 200
rnd = np.random.RandomState(12)

A0, A1, R = 1.4, 2.6, 0.3          # shaft footprint and corner radius
Z_POD, Z_SHAFT, Z_CROWN = 26, 204, 218
FLOOR = 14


def cyclic_on(n_events, min_len, max_len):
    """A set of frames, as a few on-stretches spread round the loop at random."""
    on = set()
    for _ in range(n_events):
        st = rnd.randint(0, N)
        ln = rnd.randint(min_len, max_len + 1)
        for k in range(ln):
            on.add((st + k) % N)
    return on


# which office panes are lit, frame by frame: a handful of stretches each, spread out
PANES = {}
for fl in range(13):
    for col in range(40):
        r_ = rnd.rand()
        PANES[(fl, col)] = cyclic_on(rnd.randint(1, 3), 5, 14) if r_ < 0.2 else (set(range(N)) if r_ < 0.26 else set())
BEACON = {3, 4, 15, 16, 25}                        # irregular gaps, a slow blink
PULSE_START = 17                                    # one soft pulse climbs the front strip each loop
FAN_STEP = 1


def corner_arcs(total, a0, a1, r):
    """Arc-length ranges of the four rounded corners, in the order rounded_rect builds them."""
    side = (a1 - a0) - 2 * r
    arc = math.pi * r / 2
    arcs, s = [], 0.0
    for k in range(4):
        arcs.append((s, s + arc))
        s += arc + side
    return arcs


def shaft_facade(f):
    arcs = corner_arcs(None, A0, A1, R)
    white = ['white', 'rim', 'l1', 'tile', 'l3', 'l4', 'l5']

    def fac(s, z, shade, x, y):
        zz = z - Z_POD
        for i, (s0, s1) in enumerate(arcs):
            if s0 <= s < s1:                              # a rounded white corner column
                mid = (s0 + s1) / 2
                if i < 3 and abs(s - mid) < 0.035:       # with a light strip up its middle
                    breath = 0.5 + 0.5 * math.sin(2 * math.pi * f / N + i * 2.1)
                    lv = breath * 4                        # five steps, checkered in between, so the glow eases
                    steps = ['g5', 'cyanDim', 'cyanDim', 'neonC', 'neonC']
                    k = min(4, int(lv))
                    col = steps[k]
                    if k < 4 and (lv - k) > 0.5 and (x + y) % 2 == 0:
                        col = steps[k + 1]
                    if i == 1:
                        p = (f - PULSE_START) % N
                        if p < 8:
                            head = (p + 1) / 8 * (Z_SHAFT - Z_POD)
                            if head - 26 < zz < head:
                                col = 'g0' if zz > head - 8 else 'neonC'
                    return col
                return ramp(shade, white, x, y)
        fl = int(zz // FLOOR)
        in_fl = zz - fl * FLOOR
        if in_fl < 4:                                    # floor band
            return ramp(shade, white, x, y)
        colw = 0.23
        col = int(s // colw)
        if (s % colw) < 0.03:                            # pane frame
            return 'g8' if shade > 0.5 else 'g7'
        if f in PANES.get((fl, col), ()):
            return 'lit0' if in_fl < 7 and (s % colw) < 0.1 else ('lit1' if in_fl < 11 else 'lit2')
        glass = ramp(0.25 + shade * 0.7, ['g2', 'g3', 'g4', 'g5', 'g6', 'g7'], x, y)
        if ((x * 2 - y) % 46) < 5:                       # diagonal reflections, like the reference windows
            glass = {'g2': 'g1', 'g3': 'g2', 'g4': 'g3', 'g5': 'g4', 'g6': 'g5', 'g7': 'g6'}[glass]
        return glass
    return fac


def podium_facade(s, z, shade, x, y):
    if z < 4:
        return ramp(shade, ['white', 'rim', 'l1', 'tile', 'l4'], x, y)
    if z >= Z_POD - 5:
        return ramp(shade, ['p0', 'p1', 'p2', 'p3', 'p4'], x, y)
    if 7 <= z < Z_POD - 8:
        if (s % 0.26) < 0.03:
            return 'g7'
        return ramp(shade, ['g2', 'g3', 'g4', 'g5', 'g6'], x, y)
    return ramp(shade, ['white', 'rim', 'l1', 'tile', 'l4'], x, y)


def crown_facade(s, z, shade, x, y):
    zz = z - Z_SHAFT
    if zz < 2:
        return 'p4'
    return ramp(shade, ['p0', 'p1', 'p2', 'p3', 'p4', 'p5'], x, y)


def frame(f):
    cv = Canvas(430)
    P = cv.P
    g = plot(cv, path=(1.78, 2.22, 2.85))
    # a tree on the lawn, and a cooling unit with a small fan
    T = Layer(cv)
    tx, ty = P(0.95, 3.1)
    tree(T, tx, ty, 11, seed=3)
    T.outlined()
    U = Layer(cv)
    prism(cv, U, rounded_rect(3.0, 2.2, 3.5, 2.9, 0.06, 3), 0, 16,
          facade=lambda s, z, sh, x, y: ('l6' if (s % 0.12) < 0.03 and 4 < z < 13 else None), roof='rim')
    fx, fy = P(3.25, 2.55, 16)
    U.ellipse(fx, fy, 10, 5, 'l5')
    U.ellipse(fx, fy, 8.5, 4.2, 'l8')
    ang0 = f * FAN_STEP * math.pi / 5
    for k in range(3):
        ang = ang0 + k * 2 * math.pi / 3
        for t_ in (0.3, 0.55, 0.8):
            for w_ in (-0.35, 0, 0.35):
                U.px(fx + math.cos(ang + w_ * t_) * 7.5 * t_, fy + math.sin(ang + w_ * t_) * 3.7 * t_, 'l3')
    U.px(fx, fy, 'rim'); U.px(fx + 1, fy, 'rim')
    U.outlined()
    # the lobby podium, with its canopy, door, and sign
    Pd = Layer(cv)
    prism(cv, Pd, rounded_rect(1.22, 1.22, 2.78, 2.78, 0.36), 0, Z_POD, facade=podium_facade, roof='l1')
    Pd.outlined()
    E = Layer(cv)
    # door on the front-left face (b = 2.78), centred at a = 2.0
    for (a0, a1, z0, z1, col) in ((1.8, 2.2, 0, 16, 'p3'), (1.83, 2.17, 0, 15, 'g6'), (1.85, 1.99, 0, 14, 'g3'), (2.01, 2.15, 0, 14, 'g4'),
                                  (1.72, 2.28, 17, 22, 'p4'), (1.74, 2.26, 18, 21, 'p0')):
        E.poly([P(a0, 2.79, z1), P(a1, 2.79, z1), P(a1, 2.79, z0), P(a0, 2.79, z0)], col)
    for k in range(6):
        aa = 1.78 + k * 0.08
        E.poly([P(aa, 2.79, 20), P(aa + 0.05, 2.79, 20), P(aa + 0.05, 2.79, 19), P(aa, 2.79, 19)], 'p5')
    # canopy over the door
    E.poly([P(1.68, 2.79, 23.5), P(2.32, 2.79, 23.5), P(2.32, 3.0, 22), P(1.68, 3.0, 22)], 'white')
    E.poly([P(1.68, 3.0, 22), P(2.32, 3.0, 22), P(2.32, 3.0, 20.5), P(1.68, 3.0, 20.5)], 'p3')
    E.outlined()
    # the glass shaft
    S = Layer(cv)
    prism(cv, S, rounded_rect(A0, A0, A1, A1, R), Z_POD, Z_SHAFT, facade=shaft_facade(f), roof=None)
    S.outlined()
    # a pink crown and the roof
    K = Layer(cv)
    prism(cv, K, rounded_rect(A0 - 0.03, A0 - 0.03, A1 + 0.03, A1 + 0.03, R + 0.03), Z_SHAFT, Z_CROWN, facade=crown_facade, roof='rim')
    K.poly([P(a, b, Z_CROWN) for (a, b) in rounded_rect(A0 + 0.1, A0 + 0.1, A1 - 0.1, A1 - 0.1, R - 0.08)], 'l3')
    K.outlined()
    # rooftop: a small plant room and the antenna with its beacon
    Rf = Layer(cv)
    prism(cv, Rf, rounded_rect(1.75, 1.6, 2.2, 2.05, 0.05, 3), Z_CROWN, Z_CROWN + 10, roof='rim')
    mx, my = P(2.3, 2.25, Z_CROWN)
    Rf.line(mx, my, mx, my - 34, 'l6'); Rf.line(mx + 1, my, mx + 1, my - 34, 'l4')
    for k in (10, 20):
        Rf.line(mx - 2, my - k, mx + 3, my - k, 'l6')
    on = f in BEACON
    for dx, dy in ((0, -36), (1, -36), (0, -37), (1, -37)):
        Rf.px(mx + dx, my + dy, 'neonP' if on else 'p4')
    Rf.outlined()
    Bn = bench(cv, 2.62, 3.12)
    Lp = lamp(cv, 1.52, 3.2)
    return cv, composite(cv, [g, T, Pd, E, U, Bn, S, K, Rf, Lp])   # the cooling unit and the bench stand in front of the lobby


if __name__ == '__main__':
    import sys
    frames = []
    for f in range(N):
        cv, fr = frame(f)
        frames.append(fr)
    info = save('data-tower', cv, frames, [DELAY] * N, str(NC / 'art/out'))
    print(info)
