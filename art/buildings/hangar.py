"""Hangar, the original design at the new detail, and weirder: the peach-and-coral ribbed vault with a white
crown, windows down its right wall, the pale arched front with its coral-framed bay door, a round window and a
warning light, the striped apron, and the little tug going back and forth, now hovering. New: a skylight strip
along the crown, a glow under the door, and chevron lights running toward the bay."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, composite, ramp, save
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 150
A0, A1, B0, B1, ZW, R = 0.75, 3.25, 0.7, 3.0, 21, 32.5
AC, RA = (A0 + A1) / 2, (A1 - A0) / 2
zf = lambda a: ZW + R * math.sqrt(max(0.0, 1 - ((a - AC) / RA) ** 2))


def frame(f):
    cv = Canvas(270)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 0, 0.6, 3.2), (3.6, 0, 4, 4)], paths=[(0.6, 3.2, 3.6, 4)], shrubs=[(0.3, 1.2), (3.8, 1.5), (3.8, 3.0)], seed=5)
    g.poly([P(0.9, 3.15), P(3.1, 3.15), P(3.1, 3.95), P(0.9, 3.95)], 'asphalt')           # the apron
    for k in range(4):
        aa = 1.1 + k * 0.5
        g.poly([P(aa, 3.5), P(aa + 0.25, 3.5), P(aa + 0.25, 3.58), P(aa, 3.58)], 'white')
    lead = (f // 3) % 6
    for k in range(6):                                                                    # chevron lights running toward the bay
        b = 3.9 - k * 0.12
        on = k == lead or k == (lead + 1) % 6
        for side in (-1, 1):
            g.px(*P(2.0 + side * 0.18, b), 'cyan' if on else 'steel'); g.px(*P(2.0 + side * 0.1, b - 0.05), 'cyan' if on else 'steel')
    L = Layer(cv)
    L.poly([P(A1, B1), P(A1, B0), P(A1, B0, ZW), P(A1, B1, ZW)], 'lsteel')              # the right wall, with glowing windows
    L.line(*P(A1, B1, 3), *P(A1, B0, 3), 'slabK')
    for k in range(4):
        bb = B0 + 0.3 + k * 0.5
        L.poly([P(A1 + 0.004, bb, 16), P(A1 + 0.004, bb + 0.3, 16), P(A1 + 0.004, bb + 0.3, 7), P(A1 + 0.004, bb, 7)], 'dteal')
        L.poly([P(A1 + 0.006, bb + 0.03, 14), P(A1 + 0.006, bb + 0.27, 14), P(A1 + 0.006, bb + 0.27, 9), P(A1 + 0.006, bb + 0.03, 9)], 'teal' if (k + f // 8) % 3 else 'iteal')
    steps = 128
    for i in range(steps):                                                                # the vault, strip by strip across a
        aa, ab = A0 + (A1 - A0) * i / steps, A0 + (A1 - A0) * (i + 1) / steps
        slope = zf(ab) - zf(aa)
        col = 'white' if abs(slope) < 0.15 else ('peach' if slope > 0.5 else ('pink' if slope > 0 else ('coral' if slope > -0.6 else 'coralDk')))
        L.poly([P(aa, B0, zf(aa)), P(ab, B0, zf(ab)), P(ab, B1, zf(ab)), P(aa, B1, zf(aa))], col)
    for i in range(steps):                                                                # a skylight strip along the crown
        aa = A0 + (A1 - A0) * i / steps
        if abs(aa - AC) < 0.16:
            for bb in np.linspace(B0 + 0.12, B1 - 0.12, 40):
                if (bb - B0) % 0.38 > 0.05:
                    L.px(*P(aa, bb, zf(aa)), 'iteal' if aa < AC else 'teal')
    for k in range(1, 6):                                                                 # the roof ribs
        bb = B0 + k * (B1 - B0) / 6
        for i in range(steps):
            aa = A0 + (A1 - A0) * i / steps
            x, y = P(aa, bb, zf(aa))
            L.px(x, y, 'coral' if zf(aa + 0.02) - zf(aa) > 0 else 'coralDk'); L.px(x, y + 1, 'peach' if zf(aa + 0.02) - zf(aa) > 0 else 'coral')
    arch = [P(A0, B1)] + [P(A0 + (A1 - A0) * i / 96, B1, zf(A0 + (A1 - A0) * i / 96)) for i in range(97)] + [P(A1, B1)]
    L.poly(arch, 'pave')                                                                  # the front, with its peach edge
    for i in range(97):
        aa = A0 + (A1 - A0) * i / 96
        x, y = P(aa, B1, zf(aa))
        for d in range(3):
            L.px(x, y + d, 'peach' if d < 2 else 'pink')
    for (a0, a1, z0, z1, col) in ((1.15, 2.85, 0, 35, 'coral'), (1.2, 2.8, 0, 33, 'coralDk')):
        L.poly([P(a0, B1 + 0.004, z1), P(a1, B1 + 0.004, z1), P(a1, B1 + 0.004, z0), P(a0, B1 + 0.004, z0)], col)
    for z in range(3, 32):                                                                # the slatted bay door, a glow under it
        L.poly([P(1.22, B1 + 0.006, z + 1), P(2.78, B1 + 0.006, z + 1), P(2.78, B1 + 0.006, z), P(1.22, B1 + 0.006, z)], 'asphalt' if z % 4 == 0 else ('lsteel' if z % 4 != 1 else 'slabK'))
    for z in range(0, 3):
        L.poly([P(1.22, B1 + 0.006, z + 1), P(2.78, B1 + 0.006, z + 1), P(2.78, B1 + 0.006, z), P(1.22, B1 + 0.006, z)], 'cyan' if z < 2 else 'iteal')
    L.ellipse(*P(2.0, B1 + 0.006, 45), 6, 5, 'coralDk'); L.ellipse(*P(2.0, B1 + 0.007, 45), 4, 3.5, 'teal'); L.px(*P(1.97, B1 + 0.008, 47), 'iteal')   # the round window
    on = (f // 4) % 2 == 0
    for dx in (-1, 0, 1):
        L.px(P(2.0, B1 + 0.008, 38)[0] + dx, P(2.0, B1 + 0.008, 38)[1], 'butter' if on else 'coral')
    L.outlined()
    C = Layer(cv)                                                                         # the little tug, hovering back and forth
    u = 0.5 - 0.5 * math.cos(2 * math.pi * f / N)
    ca = 1.3 + u * 1.3
    for (a, b, z, col) in ((ca, 3.5, 0, 'cyan'),):
        pass
    C.poly([P(ca + 0.05, 3.62, 0), P(ca + 0.4, 3.62, 0), P(ca + 0.4, 3.38, 0), P(ca + 0.05, 3.38, 0)], 'cyan' if (f % 2) else 'iteal')
    from kit import prism, rounded_rect
    prism(cv, C, rounded_rect(ca, 3.35, ca + 0.45, 3.65, 0.04, 2), 3, 12, facade=lambda s, z, sh, x, y: ('coral' if 5 <= z < 7 else ramp(sh, ['pave', 'lsteel', 'slabK'], x, y)), roof='white')
    C.px(*P(ca + 0.45, 3.5, 9), 'butter')
    C.outlined()
    return cv, composite(cv, [g, Sh, L, C])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('hangar', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out')))
