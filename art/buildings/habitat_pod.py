"""Habitat pod, the original design at the new detail, and weirder: the lavender banded pod under its dome,
a violet belt, four portholes glowing on and off, an airlock, an antenna, a solar panel on a post, a cyan
hover glow round its foot, and a hologram flickering by the door."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, prism, rounded_rect, circle, composite, ramp, save, HX
from shapes import dome
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 200
CA, CB, RT, HW_, HD = 2.15, 1.95, 0.97, 29, 29
RXP = RT * HX * math.sqrt(2)                                                   # the pod's half-width on screen


def band(nx):
    return 'lavender' if nx < -0.84 else ('white' if nx < -0.5 else ('lilac' if nx < 0.2 else ('lavender' if nx < 0.62 else 'violet')))


def frame(f):
    cv = Canvas(260)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 3.1, 4, 4), (0, 0, 0.9, 3.1)], paths=[(1.75, 3.1, 2.25, 4)], shrubs=[(0.45, 1.3), (3.3, 3.5), (0.6, 3.6)], seed=2)
    cx, _ = P(CA, CB)
    glow = 0.5 + 0.5 * math.sin(2 * math.pi * f / N)
    L = Layer(cv)
    def wall(s, z, sh, x, y):
        nx = (x + 0.5 - cx) / RXP
        if z < 3:
            return 'cyan' if (glow > 0.5 or (x + y) % 2) else 'iteal'                # the hover glow round its foot
        col = band(nx)
        if z in (11, 20):
            col = {'white': 'lilac', 'lilac': 'lavender', 'lavender': 'violet', 'violet': 'violetDk'}[col]   # panel seams
        return col
    prism(cv, L, circle(CA, CB, RT), 0, HW_, facade=wall, roof='lilac')
    dome(L, cv, CA, CB, HW_, RT, lambda n, pt, x, y: ('lavender' if ((math.degrees(math.atan2(n[1], n[0])) % 30) < 2.5 and band((x + 0.5 - cx) / RXP) in ('white', 'lilac')) else band((x + 0.5 - cx) / RXP)), zs=HD / RT)
    for x in range(int(cx - RXP), int(cx + RXP) + 1):                          # the violet belt where dome meets wall, with rivets
        nx = (x + 0.5 - cx) / RXP
        if abs(nx) < 1:
            y = P(CA + RT * nx / math.sqrt(2) * 0, CB, 0)[1]
            yb = P(CA, CB, HW_)[1] + RXP / 2 * math.sqrt(1 - nx * nx)
            L.px(x, yb, 'violet'); L.px(x, yb - 1, 'lavender' if nx < 0.5 else 'violet'); L.px(x, yb + 1, 'violetDk')
            if x % 7 == 0:
                L.px(x, yb, 'lilac')
    for i, ang in enumerate((-52, -18, 16, 50)):                               # portholes that glow on and off
        px_ = cx + RXP * math.sin(math.radians(ang))
        py_ = P(CA, CB, 15)[1] + RXP / 2 * math.cos(math.radians(ang))
        on = (i + f // 5) % 3 != 0
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                d = math.hypot(dx, dy)
                if d <= 4.4:
                    L.px(px_ + dx, py_ + dy, 'violet' if d > 3.1 else ('white' if (dx, dy) == (-1, -1) else ('butter' if on else 'teal')))
    L.outlined()
    A = Layer(cv)                                                              # the airlock, with its door and a light strip
    prism(cv, A, rounded_rect(1.55, 2.75, 2.25, 3.15, 0.02, 2), 0, 19, facade=lambda s, z, sh, x, y: ramp(sh, ['lilac', 'lavender', 'violet'], x, y), roof='white')
    for (a0, a1, z0, z1, col) in ((1.75, 2.05, 0, 15, 'violet'), (1.8, 2.0, 1, 13, 'teal'), (1.82, 1.9, 2, 12, 'iteal')):
        A.poly([P(a0, 3.151, z1), P(a1, 3.151, z1), P(a1, 3.151, z0), P(a0, 3.151, z0)], col)
    A.line(*P(1.72, 3.152, 17), *P(2.08, 3.152, 17), 'neon' if (f // 3) % 4 else 'lavender')
    A.outlined()
    T = Layer(cv)                                                              # the antenna, blinking
    tx, ty = P(CA, CB, HW_ + HD)
    T.line(tx, ty, tx, ty - 10, 'violet'); T.line(tx + 1, ty, tx + 1, ty - 10, 'violetDk')
    for dx, dy in ((0, -11), (1, -11), (0, -12), (1, -12)):
        T.px(tx + dx, ty + dy, 'neon' if (f // 4) % 2 == 0 else 'violet')
    T.outlined()
    Sp = Layer(cv)                                                             # the solar panel on its post
    sx, sy = P(3.35, 1.05)
    Sp.line(sx, sy, sx, sy - 13, 'violet'); Sp.line(sx + 1, sy, sx + 1, sy - 13, 'violetDk')
    Sp.poly([(sx - 13, sy - 17), (sx + 2, sy - 25), (sx + 13, sy - 19), (sx - 2, sy - 11)], 'dteal')
    for k in range(-10, 11, 4):
        Sp.line(sx + k - 1, sy - 15 - k * 0.3, sx + k + 2, sy - 21 - k * 0.3, 'teal')
    Sp.outlined()
    Hg = Layer(cv)                                                             # a small hologram by the door, flickering
    if f % 9 != 4:
        hx, hy = P(1.35, 3.25, 24)
        for dy in range(-4, 5):
            if (dy + f) % 3 == 0:
                continue
            for dx in range(-4, 5):
                if abs(math.hypot(dx, dy * 1.4) - 3.4) < 0.8 or (dx == 0 and abs(dy) < 2):
                    Hg.px(hx + dx, hy + dy, 'neon' if (dx + dy + f // 2) % 4 else 'cyan')
        Hg.line(hx, hy + 6, hx, hy + 20, 'lavender')
    return cv, composite(cv, [g, Sh, Sp, L, A, T, Hg])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('habitat-pod', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out'), disposal=2))
