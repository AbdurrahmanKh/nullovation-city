"""Comms spire, the original design at the new detail: a banded drum, a very tall violet needle tapering to a
point with beacons blinking up it in turn, a glowing antenna ring near the top, and an equipment shed."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, prism, rounded_rect, circle, composite, ramp, save, HX
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 200
TOP, RING_Z, RX, RY = 245, 199, 23, 9.6
rnd = np.random.RandomState(8)
WINDOWS = {(int(z), side) for z, side in zip(rnd.randint(8, 186, 16), rnd.randint(0, 2, 16))}


def frame(f):
    cv = Canvas(380)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 3.1, 4, 4), (0, 0, 0.9, 3.1), (3.2, 0, 4, 1.2)], paths=[(1.85, 3.1, 2.35, 4)],
                shrubs=[(0.45, 1.4), (0.5, 2.6), (3.6, 0.6), (2.9, 3.6)], seed=8)
    B = Layer(cv)
    band = lambda s, z, sh, x, y: ramp(sh, ['lavender', 'violet', 'violetDk'], x, y) if z < 3 or 9 <= z < 11 else ramp(sh, ['white', 'lilac', 'lilac', 'lavender', 'violet'], x, y)
    prism(cv, B, circle(2.0, 2.0, 0.75), 0, 14, facade=band, roof='lilac')
    B.poly([P(2 + 0.575 * math.cos(t), 2 + 0.575 * math.sin(t), 14) for t in np.linspace(0, 2 * math.pi, 40)], 'lavender')
    B.outlined()
    cx, cy0 = P(2.0, 2.0, 14)
    cx = round(cx)
    R = Layer(cv)                                                              # the back half of the antenna ring
    for x in range(cx - RX, cx + RX + 1):
        nx = (x + 0.5 - cx) / RX
        if abs(nx) < 1:
            yb = cy0 - RING_Z - RY * math.sqrt(1 - nx * nx)
            R.px(x, yb, 'violet'); R.px(x, yb + 1, 'violetDk')
    S = Layer(cv)                                                              # the needle, tapering to a point
    for z in range(TOP):
        w = max(1.9, 12.4 - z / 22)
        y = cy0 - z
        for x in range(round(cx - w), round(cx + w)):
            rel = (x + 0.5 - (cx - w)) / (2 * w)
            col = 'white' if rel < 0.3 else ('lilac' if rel < 0.6 else ('lavender' if rel < 0.85 else 'violet'))
            if z % 38 in (19, 20) and z < 190:
                col = 'violet' if rel < 0.85 else 'violetDk'                   # the violet bands
            elif z % 19 == 9 and z < 190:
                col = {'white': 'lilac', 'lilac': 'lavender', 'lavender': 'violet', 'violet': 'violetDk'}[col]   # panel seams
            S.px(x, y, col)
        for (wz, side) in WINDOWS:                                             # small lit slits, here and there
            if z == wz and w > 4:
                x = round(cx - w * 0.45) if side == 0 else round(cx + w * 0.2)
                S.px(x, y, 'teal' if (f // 7 + wz) % 5 else 'butter'); S.px(x + 1, y, 'teal')
    for i, z in enumerate((42, 88, 134, 180, TOP)):                            # beacons blink up the needle, in turn
        on = (f // 4) % 5 == i or (i == 4 and (f // 2) % 2 == 0)
        for dx in (-1, 0, 1):
            for dy in (0, 1) if i < 4 else (0, 1, 2):
                S.px(cx + dx, cy0 - z - dy, 'neon' if on else 'violet')
    S.outlined()
    F = Layer(cv)                                                              # the front half of the ring, glowing in turn
    for x in range(cx - RX, cx + RX + 1):
        nx = (x + 0.5 - cx) / RX
        if abs(nx) < 1:
            y = cy0 - RING_Z + RY * math.sqrt(1 - nx * nx)
            lit = ((x - cx + RX) // 6 + f // 2) % 7 == 0
            F.px(x, y - 1, 'white' if nx < -0.2 else 'lilac')
            F.px(x, y, 'neon' if lit else ('lilac' if nx < 0.3 else 'lavender'))
            F.px(x, y + 1, 'violet'); F.px(x, y + 2, 'violetDk')
    for sx in (-1, 1):
        F.line(cx + sx * RX * 0.5, cy0 - RING_Z + 5, cx, cy0 - RING_Z - 6, 'violet')
    for k in (-0.8, -0.3, 0.3, 0.8):                                           # little antenna tips on the ring
        x = round(cx + k * RX); y = cy0 - RING_Z + RY * math.sqrt(1 - k * k)
        F.line(x, y - 2, x, y - 6, 'violet')
    F.outlined()
    E = Layer(cv)                                                              # the equipment shed
    prism(cv, E, rounded_rect(2.85, 2.5, 3.35, 3.0, 0.02, 2), 0, 15, facade=lambda s, z, sh, x, y: ramp(sh, ['lilac', 'lavender', 'violet'], x, y), roof='white')
    E.poly([P(2.97, 3.001, 12), P(3.2, 3.001, 12), P(3.2, 3.001, 0), P(2.97, 3.001, 0)], 'violet')
    E.poly([P(3.0, 3.002, 10), P(3.17, 3.002, 10), P(3.17, 3.002, 0), P(3.0, 3.002, 0)], 'violetDk')
    E.px(*P(3.25, 3.002, 12), 'neon' if (f // 6) % 2 else 'violet')
    E.outlined()
    return cv, composite(cv, [g, Sh, B, R, S, F, E])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('comms-spire', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out')))
