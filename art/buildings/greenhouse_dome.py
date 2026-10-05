"""Greenhouse dome, new standard: a geodesic glass dome over plants on a white ring, a water tank, and
flower beds. Motion: a soft glint travels slowly across the glass."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, plot, prism, rounded_rect, circle, tree, composite, ramp, save
from parks import bench, lamp
from lot import lot
from shapes import dome, lit
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked

N, DELAY = 40, 250
rnd = np.random.RandomState(41)
PLANT = rnd.rand(400, 400)


def glass(f):
    glint = -2.6 + 1.6 * (f / N)                                               # the glint's bearing, drifting across the dome
    def col(n, pt, x, y):
        phi, th = math.atan2(n[1], n[0]), math.asin(max(-1, min(1, n[2])))
        if (phi * 6 / math.pi) % 1 < 0.1 or (th * 9 / math.pi) % 1 < 0.11:
            return 'white' if lit(n) < 0.45 else 'rim'                         # the geodesic frame
        if abs(((phi - glint + math.pi) % (2 * math.pi)) - math.pi) < 0.09 and th > 0.35:
            return 'white'
        if th < 0.12 and (phi * 9 / math.pi) % 1 < 0.22:
            return 'lit1'                                                      # a ring of grow lights round the base, glowing at night
        if th < 0.75:                                                          # plants inside, seen through the glass
            v = PLANT[int(y) % 400, int(x) % 400]
            if v > 0.988:
                return 'lit0'                                                  # a few lights among the plants
            return 'flower' if v > 0.96 else ('leaf' if v > 0.55 else ('leafDk' if v > 0.25 else 'g5'))
        return ramp(lit(n), ['g0', 'g1', 'g2', 'g3', 'g4'], x, y)
    return col


def frame(f):
    cv = Canvas(290)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 3.1, 4, 4), (0, 0, 0.8, 3.1)], shrubs=[(0.4, 1.35), (0.45, 2.4), (1.2, 3.6), (2.8, 3.6)], seed=6)   # the original lot
    pa0, pb0, pa1, pb1 = 3.15, 0.45, 3.85, 1.55                                # and its water pool, at the back right
    g.poly([P(pa0, pb0), P(pa1, pb0), P(pa1, pb1), P(pa0, pb1)], 'lsteel')
    g.poly([P(pa0 + 0.07, pb0 + 0.07), P(pa1 - 0.07, pb0 + 0.07), P(pa1 - 0.07, pb1 - 0.07), P(pa0 + 0.07, pb1 - 0.07)], 'teal')
    g.line(*P(pa0 + 0.07, pb0 + 0.07), *P(pa1 - 0.07, pb0 + 0.07), 'dteal'); g.line(*P(pa0 + 0.07, pb0 + 0.07), *P(pa0 + 0.07, pb1 - 0.07), 'dteal')
    for k in range(5):                                                         # a slow ripple of light across the water
        t = (f / N + k / 5) % 1.0
        g.px(*P(pa0 + 0.15 + t * (pa1 - pa0 - 0.3), pb0 + 0.2 + (k * 0.19) % (pb1 - pb0 - 0.4)), 'iteal')
    for _ in range(60):                                                        # flowers in the front lawn
        a, b = rnd.uniform(0.3, 3.7), rnd.uniform(3.25, 3.8)
        if 1.7 < a < 2.3:
            continue
        g.px(*P(a, b), 'flower' if rnd.rand() < 0.5 else 'flowerHi')
    rnd.seed(41)
    Tk = Layer(cv)                                                             # a water tank at the back right
    prism(cv, Tk, circle(0.42, 0.55, 0.24), 0, 30, facade=lambda s, z, sh, x, y: ramp(sh, ['skyHi', 'sky', 'skyDk'], x, y) if z % 9 > 1 else 'skyDk', roof='skyHi')
    Tk.outlined()
    D = Layer(cv)
    prism(cv, D, circle(2.0, 2.0, 1.24), 0, 8, facade=lambda s, z, sh, x, y: ramp(sh, ['white', 'rim', 'l1', 'tile', 'l3'], x, y), roof='l1')
    dome(D, cv, 2.0, 2.0, 8, 1.18, glass(f), zs=48)                          # the original's tall dome
    D.outlined()
    V = Layer(cv)                                                              # the entrance vestibule
    prism(cv, V, rounded_rect(1.8, 2.95, 2.2, 3.2, 0.03, 2), 0, 15, facade=lambda s, z, sh, x, y: ramp(sh, ['g2', 'g4', 'g6'], x, y) if 3 < z < 12 else ramp(sh, ['white', 'rim', 'l1', 'l3'], x, y), roof='white')
    V.outlined()
    return cv, composite(cv, [g, Sh, D, V, bench(cv, 2.55, 3.3), lamp(cv, 1.3, 3.3)])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('greenhouse-dome', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out')))
