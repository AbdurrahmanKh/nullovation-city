"""Kiosk, the original design at the new detail, and weirder: the stall with its counter window, the striped
awning, and on the roof the neon sign, now a pink tube frame round a dark board with glyph cells flickering in
a wave, a steaming neon cup, and a moment where it half fails. A cyan strip glows under the awning, steam
rises from the cup, and a table waits under a striped umbrella."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, prism, rounded_rect, circle, composite, ramp, save
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 150
A0, B0, A1, B1, H = 1.45, 1.45, 2.55, 2.5, 38
FAIL = {17, 18, 31}


def steam(L, x, y, f, height=18):
    for k in range(4):
        t = (f / N * 3 + k / 4) % 1.0
        if t > 0.8:
            continue
        yy, xx, r = y - t * height, x + math.sin(t * 8 + k) * 1.8, 0.8 + t * 2.4
        for dx in range(-int(r), int(r) + 1):
            for dy in range(-int(r * 0.7), int(r * 0.7) + 1):
                if dx * dx + dy * dy * 2 <= r * r and (t < 0.5 or (dx + dy + int(yy)) % 2 == 0):
                    L.px(xx + dx, yy + dy, 'white' if dy < 0 else 'lsteel')


def frame(f):
    cv = Canvas(260)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 3.1, 4, 4), (0, 0, 0.9, 3.1)], shrubs=[(0.45, 1.3), (0.5, 2.5), (1.1, 3.6), (3.4, 3.55)], seed=10)
    L = Layer(cv)
    prism(cv, L, rounded_rect(A0, B0, A1, B1, 0.01, 2), 0, H, facade=lambda s, z, sh, x, y: ramp(sh, ['pave', 'pave', 'lsteel', 'slabK'], x, y), roof='white')
    for (a0, a1, z0, z1, col) in ((1.6, 2.4, 6, 22, 'teal'), (1.66, 2.34, 8, 20, 'butter')):   # the counter window, lit inside
        L.poly([P(a0, B1 + 0.004, z1), P(a1, B1 + 0.004, z1), P(a1, B1 + 0.004, z0), P(a0, B1 + 0.004, z0)], col)
    for k in range(5):
        L.px(*P(1.75 + k * 0.14, B1 + 0.005, 13), ['pink', 'teal', 'gold', 'lavender', 'coral'][k])
    L.poly([P(1.55, B1 + 0.2, 10), P(2.45, B1 + 0.2, 10), P(2.45, B1 + 0.2, 8), P(1.55, B1 + 0.2, 8)], 'wood')
    L.poly([P(1.55, B1, 10), P(2.45, B1, 10), P(2.45, B1 + 0.2, 10), P(1.55, B1 + 0.2, 10)], 'peach')
    for k in range(9):                                                                   # the striped awning, sloping out
        aa, ab = A0 + k * (A1 - A0) / 9, A0 + (k + 1) * (A1 - A0) / 9
        L.poly([P(aa, B1, H - 4), P(ab, B1, H - 4), P(ab, B1 + 0.36, H - 12), P(aa, B1 + 0.36, H - 12)], 'pink' if k % 2 == 0 else 'white')
        L.poly([P(aa, B1 + 0.36, H - 12), P(ab, B1 + 0.36, H - 12), P((aa + ab) / 2, B1 + 0.36, H - 15)], 'rose' if k % 2 == 0 else 'lsteel')
    L.line(*P(A0 + 0.02, B1 + 0.01, H - 13), *P(A1 - 0.02, B1 + 0.01, H - 13), 'cyan' if f % 7 else 'iteal')   # a neon strip under the awning
    L.outlined()
    Sg = Layer(cv)                                                                       # the neon sign on the roof
    a0s, a1s, bs, z0, z1 = 1.52, 2.48, 1.9, H + 2, H + 19
    Sg.poly([P(a0s, bs, z1), P(a1s, bs, z1), P(a1s, bs, z0), P(a0s, bs, z0)], 'ink')
    for (a, b_) in ((1.62, 1.85), (2.38, 1.85)):
        Sg.line(*P(a, b_, H), *P(a, b_, z0), 'steel')
    fail = f in FAIL
    for i in range(49):                                                                  # the pink tube frame
        t = i / 48
        for (za, col) in ((z1 - 1, 'neon'), (z0 + 1, 'neon')):
            Sg.px(*P(a0s + 0.03 + t * (a1s - a0s - 0.06), bs + 0.001, za), col if not (fail and t > 0.55) else 'rose')
    for z in range(z0 + 1, z1):
        Sg.px(*P(a0s + 0.03, bs + 0.001, z), 'neon'); Sg.px(*P(a1s - 0.03, bs + 0.001, z), 'neon' if not fail else 'rose')
    for k in range(5):                                                                   # the glyph cells, flickering in a wave
        on = ((k + f // 2) % 5 < 3) and not (fail and k > 2)
        col = ('cyan' if k % 2 else 'neon') if on else 'rose'
        aa = 1.7 + k * 0.14
        Sg.poly([P(aa, bs + 0.002, z0 + 12), P(aa + 0.09, bs + 0.002, z0 + 12), P(aa + 0.09, bs + 0.002, z0 + 5), P(aa, bs + 0.002, z0 + 5)], col)
        Sg.poly([P(aa + 0.03, bs + 0.003, z0 + 10), P(aa + 0.06, bs + 0.003, z0 + 10), P(aa + 0.06, bs + 0.003, z0 + 7), P(aa + 0.03, bs + 0.003, z0 + 7)], 'ink' if on else 'rose')
    Sg.outlined()
    Cup = Layer(cv)                                                                      # a steaming neon cup on the roof
    cx, cy = P(2.3, 1.62, H + 1)
    for dx in range(-3, 4):
        for dy in range(-5, 1):
            if abs(dx) <= 3 - (dy < -4):
                Cup.px(cx + dx, cy + dy, 'cyan' if abs(dx) == 3 or dy == 0 else 'iteal')
    Cup.px(cx + 4, cy - 3, 'cyan'); Cup.px(cx + 5, cy - 2, 'cyan'); Cup.px(cx + 4, cy - 1, 'cyan')
    steam(Cup, cx, cy - 7, f)
    U = Layer(cv)                                                                        # a table under a striped umbrella
    ux, uy = P(3.15, 2.95)
    ux, uy = round(ux), round(uy)
    U.ellipse(ux, uy - 10, 10, 5, 'white'); U.ellipse(ux, uy - 11, 9, 4, 'pave')
    U.line(ux, uy - 8, ux, uy, 'wood')
    U.line(ux, uy - 10, ux, uy - 30, 'wood')
    for dy in range(0, 10):
        half = 2 + dy * 2.2
        for dx in range(-round(half), round(half) + 1):
            seg = int((dx + 22) // 7) % 2
            col = ('pink' if seg == 0 else 'white') if dx < half * 0.4 else ('rose' if seg == 0 else 'lsteel')
            U.px(ux + dx, uy - 36 + dy, col)
    for dx in range(-19, 20, 2):
        U.px(ux + dx, uy - 26, 'rose' if dx > 6 else 'pink')
    for (a, b) in ((2.85, 3.2), (3.45, 2.7)):
        prism(cv, U, rounded_rect(a - 0.08, b - 0.08, a + 0.08, b + 0.08, 0.02, 2), 0, 8, roof='pink')
    U.outlined()
    return cv, composite(cv, [g, Sh, L, Sg, Cup, U])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('kiosk', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out'), disposal=2))
