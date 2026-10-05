"""Power station, the original design at the new detail, and weirder: the cream block with fins, a gold band,
hazard stripes, and on the roof the core. The orb now floats above its gold ring, energy arcs flicker between
them, sparks orbit it, the cage turns, and two vents puff steam."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, prism, rounded_rect, circle, composite, ramp, save
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 150
A0, B0, A1, B1, H = 0.95, 1.05, 3.05, 3.0, 40


def body(s, z, sh, x, y):
    return ramp(sh, ['pave', 'pave', 'lsteel', 'lsteel', 'slabK'], x, y)


def steam(L, x, y, f, ph, height=24):
    for k in range(5):
        t = ((f + ph) / N * 2 + k / 5) % 1.0
        yy = y - t * height
        xx = x + math.sin(t * 7 + k) * 2.2 + t * 3
        r = 1 + t * 3.2
        if t > 0.85:
            continue
        for dx in range(-int(r), int(r) + 1):
            for dy in range(-int(r * 0.7), int(r * 0.7) + 1):
                if dx * dx + dy * dy * 2 <= r * r and (t < 0.55 or (dx + dy + int(yy)) % 2 == 0):
                    L.px(xx + dx, yy + dy, 'white' if dy < 0 else 'lsteel')


def frame(f):
    cv = Canvas(300)
    P = cv.P
    rnd = np.random.RandomState(100 + f)
    g, Sh = lot(cv, lawns=[(0, 3.1, 4, 4), (0, 0, 0.9, 3.1)], paths=[(2.1, 3.1, 2.6, 4)], shrubs=[(0.45, 1.1), (0.45, 2.5), (3.4, 3.55)], seed=7)
    L = Layer(cv)
    prism(cv, L, rounded_rect(A0, B0, A1, B1, 0.01, 2), 0, H, facade=body, roof='white')
    for k in range(10):                                                        # fins along the left face
        aa = A0 + 0.12 + k * 0.19
        L.poly([P(aa, B1 + 0.005, H - 8), P(aa + 0.06, B1 + 0.005, H - 8), P(aa + 0.06, B1 + 0.005, 6), P(aa, B1 + 0.005, 6)], 'white')
        L.poly([P(aa + 0.06, B1 + 0.005, H - 8), P(aa + 0.12, B1 + 0.005, H - 8), P(aa + 0.12, B1 + 0.005, 6), P(aa + 0.06, B1 + 0.005, 6)], 'slabK')
        L.line(*P(aa + 0.12, B1 + 0.006, H - 8), *P(aa + 0.12, B1 + 0.006, 6), 'slabShade')
    L.poly([P(A0, B1 + 0.006, H), P(A1, B1 + 0.006, H), P(A1, B1 + 0.006, H - 6), P(A0, B1 + 0.006, H - 6)], 'gold')
    L.poly([P(A1 + 0.006, B1, H), P(A1 + 0.006, B0, H), P(A1 + 0.006, B0, H - 6), P(A1 + 0.006, B1, H - 6)], 'goldDk')
    L.poly([P(A1 + 0.006, B1, 6), P(A1 + 0.006, B0, 6), P(A1 + 0.006, B0, 0), P(A1 + 0.006, B1, 0)], 'asphalt')
    for k in range(5):                                                         # hazard stripes on the right plinth
        bb = B0 + 0.2 + k * 0.37
        L.poly([P(A1 + 0.007, bb, 6), P(A1 + 0.007, bb + 0.15, 6), P(A1 + 0.007, bb + 0.15, 0), P(A1 + 0.007, bb, 0)], 'butter')
    for (b0, b1, z0, z1, col) in ((1.4, 2.0, 10, 29, 'steel'), (1.46, 1.94, 12, 27, 'dteal')):   # the control-room window, glowing
        L.poly([P(A1 + 0.008, b0, z1), P(A1 + 0.008, b1, z1), P(A1 + 0.008, b1, z0), P(A1 + 0.008, b0, z0)], col)
    scan = 12 + (f * 3) % 15
    L.line(*P(A1 + 0.009, 1.47, scan), *P(A1 + 0.009, 1.93, scan), 'teal')
    L.outlined()
    V = Layer(cv)                                                              # two vents, puffing steam
    for (va, vb, ph) in ((1.2, 1.3, 0), (2.7, 1.3, 17)):
        prism(cv, V, rounded_rect(va, vb, va + 0.3, vb + 0.3, 0.01, 2), H, H + 13, facade=lambda s, z, sh, x, y: ramp(sh, ['lsteel', 'slabK', 'slabShade'], x, y), roof='asphalt')
        steam(V, *P(va + 0.15, vb + 0.15, H + 15), f, ph)
    V.outlined()
    cx, cy = P(2.0, 2.0, H)
    cx, cy = round(cx), round(cy)
    oy = cy - 30                                                               # the orb floats above its ring
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f / N) + 0.15 * math.sin(6 * math.pi * f / N)
    Cb = Layer(cv)                                                             # behind the orb: the ring, the far cage bars, far sparks
    Cb.ellipse(cx, cy - 2, 23, 9, 'goldDk'); Cb.ellipse(cx, cy - 3, 21, 8, 'gold'); Cb.ellipse(cx, cy - 3, 15, 5, 'asphalt'); Cb.ellipse(cx, cy - 3, 12, 4, 'dteal')
    for dy in range(4, 18):                                                    # a faint beam holding it up
        for dx in range(-3, 4):
            if (dx + dy) % 2 == 0 and abs(dx) <= 3 - dy // 8:
                Cb.px(cx + dx, cy - dy, 'cyan')
    bars = []
    for k in range(6):
        th = k * math.pi / 3 + f * 2 * math.pi / N / 2
        bars.append((math.cos(th), round(cx + 20 * math.sin(th))))
    for c, x in bars:
        if c < 0:
            Cb.line(x, cy - 5, x, oy - 16, 'steel')
    Cb.ellipse(cx, oy - 16, 20, 5, 'steel'); Cb.ellipse(cx, oy - 16, 18, 4, 'lsteel')
    sparks = [(2 * math.pi * ((f / N) * 2 + k / 3)) for k in range(3)]
    for s in sparks:
        if math.sin(s) < 0:
            Cb.px(cx + 27 * math.cos(s), oy + 9 * math.sin(s), 'butter')
    Cb.outlined()
    O = Layer(cv)                                                              # the orb, breathing
    for dy in range(-17, 18):
        for dx in range(-17, 18):
            d2 = dx * dx + dy * dy
            if d2 <= 289:
                col = 'white' if d2 <= 10 + pulse * 30 else ('cyan' if d2 <= 70 + pulse * 60 else ('iteal' if d2 <= 180 + pulse * 40 else 'teal'))
                if d2 > 250 and (dx - dy) > 6:
                    col = 'dteal'
                O.px(cx + dx, oy + dy, col)
    O.outlined()
    Cf = Layer(cv)                                                             # in front: the near cage bars, arcs, near sparks
    for c, x in bars:
        if c >= 0:
            Cf.line(x, cy - 5, x, oy - 16, 'lsteel'); Cf.line(x + 1, cy - 5, x + 1, oy - 16, 'steel')
    for _ in range(2 + (f % 3 == 0)):                                          # energy arcs between the ring and the orb, never the same twice
        x, y = cx + rnd.randint(-10, 11), cy - 5
        while y > oy + 13:
            nxp, nyp = x + rnd.randint(-2, 3), y - rnd.randint(2, 4)
            Cf.line(x, y, nxp, nyp, 'cyan' if rnd.rand() < 0.7 else 'white')
            x, y = nxp, nyp
    for s in sparks:
        if math.sin(s) >= 0:
            Cf.px(cx + 27 * math.cos(s), oy + 9 * math.sin(s), 'white'); Cf.px(cx + 27 * math.cos(s) + 1, oy + 9 * math.sin(s), 'butter')
    return cv, composite(cv, [g, Sh, L, V, Cb, O, Cf])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('power-station', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out'), disposal=2))
