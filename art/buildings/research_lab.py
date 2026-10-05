"""Research lab, the original design at the new detail, and weirder: the white block with sky-blue trims, ribbon
windows on both faces, the door, and over it a neon ticker: a pink tube frame round a dark board, cyan glyphs
scrolling across and stuttering now and then. On the roof, the dish sweeps all the way round."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, prism, rounded_rect, circle, composite, ramp, save
from lot import lot
from parks import bench
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 200
A0, B0, A1, B1, H = 1.0, 0.9, 3.15, 2.95, 57
rnd = np.random.RandomState(3)
LIT = {(row, k, side): {(s + j) % N for s in [rnd.randint(N)] for j in range(rnd.randint(4, 14))} if rnd.rand() < 0.5 else set()
       for row in range(2) for k in range(6) for side in range(2)}
GLYPHS = rnd.rand(64, 5) > 0.5                                                      # a strip of glyph columns that scrolls


def body(s, z, sh, x, y):
    if z < 6: return ramp(sh, ['skyHi', 'sky', 'sky', 'skyDk'], x, y)              # the sky-blue plinth
    if z >= H - 8: return ramp(sh, ['skyHi', 'sky', 'sky', 'skyDk'], x, y)         # and top trim
    return ramp(sh, ['pave', 'pave', 'lsteel', 'lsteel', 'slabK'], x, y)


def frame(f):
    cv = Canvas(300)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 3.1, 4, 4), (0, 0, 0.9, 3.1)], paths=[(1.3, 3.1, 1.8, 4)], shrubs=[(0.45, 1.0), (0.5, 2.3), (2.7, 3.55), (3.5, 3.5)], seed=3)
    L = Layer(cv)
    prism(cv, L, rounded_rect(A0, B0, A1, B1, 0.2, 4), 0, H, facade=body, roof='lsteel')          # rounded corners: less square
    L.poly([P(a, b, H) for (a, b) in rounded_rect(A0 + 0.12, B0 + 0.12, A1 - 0.12, B1 - 0.12, 0.1, 4)], 'slabK')
    for row, (z0, z1) in enumerate(((15, 25), (33, 42))):                          # ribbon windows, both faces
        for k in range(4):
            aa = 1.95 + k * 0.29
            on = f in LIT[(row, k, 0)]
            L.poly([P(aa, B1 + 0.004, z1), P(aa + 0.23, B1 + 0.004, z1), P(aa + 0.23, B1 + 0.004, z0), P(aa, B1 + 0.004, z0)], 'butter' if on else 'teal')
            L.poly([P(aa, B1 + 0.005, z1), P(aa + 0.1, B1 + 0.005, z1), P(aa + 0.1, B1 + 0.005, z1 - 4), P(aa, B1 + 0.005, z1 - 4)], 'white' if on else 'iteal')
        for k in range(5):
            bb = 1.16 + k * 0.32
            on = f in LIT[(row, k, 1)]
            L.poly([P(A1 + 0.004, bb, z1), P(A1 + 0.004, bb + 0.24, z1), P(A1 + 0.004, bb + 0.24, z0), P(A1 + 0.004, bb, z0)], 'butter' if on else 'dteal')
    for (a0, a1, z0, z1, col) in ((1.3, 1.75, 0, 23, 'sky'), (1.37, 1.68, 2, 21, 'g6'), (1.39, 1.52, 3, 20, 'g4')):   # the door
        L.poly([P(a0, B1 + 0.004, z1), P(a1, B1 + 0.004, z1), P(a1, B1 + 0.004, z0), P(a0, B1 + 0.004, z0)], col)
    L.outlined()
    S = Layer(cv)                                                                   # the neon ticker over the door
    s0, s1, z0, z1 = 1.22, 1.86, 26, 37
    S.poly([P(s0, B1 + 0.01, z1), P(s1, B1 + 0.01, z1), P(s1, B1 + 0.01, z0), P(s0, B1 + 0.01, z0)], 'ink')
    stutter = f in (11, 12, 27)
    frame_col = 'rose' if f in (12, 28) else 'neon'
    for t in np.linspace(0, 1, 40):                                                  # the pink tube frame
        S.px(*P(s0 + 0.02 + t * (s1 - s0 - 0.04), B1 + 0.011, z1 - 1), frame_col); S.px(*P(s0 + 0.02 + t * (s1 - s0 - 0.04), B1 + 0.011, z0 + 1), frame_col)
    for z in range(z0 + 1, z1):
        S.px(*P(s0 + 0.02, B1 + 0.011, z), frame_col); S.px(*P(s1 - 0.02, B1 + 0.011, z), frame_col)
    off = (f if not stutter else f - 2) % 64                                         # glyphs scroll left, and stutter now and then
    cols = 15
    for c in range(cols):
        col = GLYPHS[(off + c) % 64]
        a = s0 + 0.07 + c * (s1 - s0 - 0.14) / cols
        for r in range(5):
            if col[r]:
                S.px(*P(a, B1 + 0.012, z0 + 3 + r * 1.4), 'cyan' if (c + f) % 9 else 'white')
    S.outlined()
    Ac = Layer(cv)                                                                  # a rooftop AC unit, its fan turning
    prism(cv, Ac, rounded_rect(1.3, 2.15, 1.85, 2.6, 0.04, 3), H, H + 10,
          facade=lambda s, z, sh, x, y: ('slabShade' if (s % 0.1) < 0.025 and 2 < z - H < 8 else ramp(sh, ['pave', 'lsteel', 'slabK'], x, y)), roof='lsteel')
    fx0, fy0 = P(1.575, 2.375, H + 10)
    Ac.ellipse(fx0, fy0, 6, 3, 'slabShade'); Ac.ellipse(fx0, fy0, 5, 2.4, 'ink')
    for k in range(3):                                                              # three blades, turning
        t = 2 * math.pi * (k / 3 + f / 8)
        Ac.line(fx0, fy0, fx0 + 4.5 * math.cos(t), fy0 + 2.1 * math.sin(t), 'slabK')
    Ac.px(fx0, fy0, 'lsteel')
    Ac.outlined()
    D = Layer(cv)                                                                   # the dish sweeps all the way round
    ca, cb, cz = 2.2, 1.6, H + 18
    th = 2 * math.pi * f / N
    el = math.radians(38)
    n = (math.cos(el) * math.cos(th), math.cos(el) * math.sin(th), math.sin(el))
    u = (-math.sin(th), math.cos(th), 0.0)
    v = (-math.sin(el) * math.cos(th), -math.sin(el) * math.sin(th), math.cos(el))
    def rim(r, back=0.0):
        return [P(ca + r * (u[0] * math.cos(t) + v[0] * math.sin(t)) - back * n[0], cb + r * (u[1] * math.cos(t) + v[1] * math.sin(t)) - back * n[1],
                  cz + 30 * (r * (u[2] * math.cos(t) + v[2] * math.sin(t)) - back * n[2])) for t in np.linspace(0, 2 * math.pi, 36)]
    prism(cv, D, circle(ca, cb, 0.08), H, cz - 4, facade=lambda s, z, sh, x, y: ramp(sh, ['lsteel', 'slabK', 'slabShade'], x, y), roof='lsteel')
    facing = n[0] + n[1] > -0.2                                                     # its face shows when turned toward us
    D.poly(rim(0.52, 0.08), 'slabShade')
    D.poly(rim(0.5), 'white' if facing else 'slabK')
    D.poly(rim(0.36), 'lsteel' if facing else 'slabShade'); D.poly(rim(0.2), 'slabK')
    fx, fy = P(ca + n[0] * 0.38, cb + n[1] * 0.38, cz + n[2] * 0.38 * 30)
    D.line(*P(ca, cb, cz), fx, fy, 'slabShade'); D.px(fx, fy - 1, 'cyan'); D.px(fx + 1, fy - 1, 'cyan')
    D.outlined()
    return cv, composite(cv, [g, Sh, L, S, Ac, D, bench(cv, 1.95, 3.4)])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('research-lab', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out'), disposal=2))
