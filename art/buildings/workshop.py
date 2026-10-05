"""Workshop, the original design at the new detail: the white block with its coral band, the roll-up door half
open with a warm glow inside, a teal window, windows down its side, the crane on the roof angled up and out with
its hook swaying and a blinking light, a cart that rolls out of the bay and back across the yard, and crates."""
import math
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, prism, rounded_rect, composite, ramp, save
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 200
A0, B0, A1, B1, H = 0.8, 1.15, 3.05, 3.0, 46
rnd = np.random.RandomState(9)
SIDE_LIT = [{(s + j) % N for s in [rnd.randint(N)] for j in range(rnd.randint(6, 16))} for _ in range(3)]


def body(s, z, sh, x, y):
    if z >= H - 6: return ramp(sh, ['peach', 'coral', 'coral', 'coralDk'], x, y)  # the coral band
    if z < 3: return ramp(sh, ['lsteel', 'slabK', 'slabShade'], x, y)
    return ramp(sh, ['pave', 'pave', 'lsteel', 'lsteel', 'slabK'], x, y)


def frame(f):
    cv = Canvas(300)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 0, 0.7, 3.2), (3.3, 0, 4, 1.4)], shrubs=[(0.35, 1.3), (0.4, 2.6), (3.7, 0.7)], seed=9)
    g.poly([P(0.7, 3.1), P(3.3, 3.1), P(3.3, 4), P(0.7, 4)], 'asphalt')            # the yard in front of the bay
    for k in range(3):
        g.poly([P(1.2 + k * 0.5, 3.8), P(1.4 + k * 0.5, 3.8), P(1.4 + k * 0.5, 3.88), P(1.2 + k * 0.5, 3.88)], 'butter')
    L = Layer(cv)
    prism(cv, L, rounded_rect(A0, B0, A1, B1, 0.01, 2), 0, H, facade=body, roof='white')
    L.poly([P(A0 + 0.1, B0 + 0.1, H), P(A1 - 0.1, B0 + 0.1, H), P(A1 - 0.1, B1 - 0.1, H), P(A0 + 0.1, B1 - 0.1, H)], 'lsteel')
    L.poly([P(1.05, B1 + 0.004, 33), P(2.45, B1 + 0.004, 33), P(2.45, B1 + 0.004, 0), P(1.05, B1 + 0.004, 0)], 'coral')   # the roll-up door, half open
    for z in range(10, 31):
        L.poly([P(1.12, B1 + 0.005, z + 1), P(2.38, B1 + 0.005, z + 1), P(2.38, B1 + 0.005, z), P(1.12, B1 + 0.005, z)], 'slabK' if z % 3 == 0 else 'lsteel')
    L.poly([P(1.12, B1 + 0.005, 10), P(2.38, B1 + 0.005, 10), P(2.38, B1 + 0.005, 0), P(1.12, B1 + 0.005, 0)], 'ink')
    glow = 'gold' if f % 9 in (2, 3) else 'goldDk'                                  # a warm glow from inside the bay
    L.poly([P(1.2, B1 + 0.006, 4), P(2.3, B1 + 0.006, 4), P(2.3, B1 + 0.006, 0), P(1.2, B1 + 0.006, 0)], glow)
    for (a0, a1, z0, z1, col) in ((2.6, 2.9, 17, 29, 'teal'), (2.63, 2.73, 21, 28, 'iteal')):
        L.poly([P(a0, B1 + 0.004, z1), P(a1, B1 + 0.004, z1), P(a1, B1 + 0.004, z0), P(a0, B1 + 0.004, z0)], col)
    for k in range(3):
        bb = B0 + 0.3 + k * 0.5
        L.poly([P(A1 + 0.004, bb, 29), P(A1 + 0.004, bb + 0.3, 29), P(A1 + 0.004, bb + 0.3, 17), P(A1 + 0.004, bb, 17)], 'butter' if f in SIDE_LIT[k] else 'asphalt')
    L.outlined()
    K = Layer(cv)                                                                   # the crane on the roof, angled up and out
    mx, my = P(2.7, 1.45, H)
    for d in (0, 1):
        K.line(mx + d, my, mx + d, my - 31, 'steel' if d == 0 else 'asphalt')
    for z in range(4, 30, 6):
        K.line(mx - 1, my - z, mx + 2, my - z - 3, 'slabShade')
    jx, jy = P(1.45, 2.65, H + 52)
    K.line(mx, my - 31, jx, jy, 'steel'); K.line(mx, my - 29, jx, jy + 2, 'coral'); K.line(mx, my - 30, jx, jy + 1, 'coralDk')
    K.line(mx, my - 31, mx + 13, my - 37, 'steel')                                  # the back arm and its counterweight
    for dx in range(0, 7):
        for dy in range(0, 5):
            K.px(mx + 10 + dx, my - 39 + dy - dx // 2, 'asphalt' if dy else 'steel')
    K.line(mx, my - 31, mx, my - 42, 'steel')
    sway = round(2 * math.sin(2 * math.pi * f / N))
    hx, hy = round(jx + 3), round(jy + 2)
    K.line(hx, hy, hx + sway, hy + 18, 'asphalt')
    K.px(hx + sway - 1, hy + 19, 'steel'); K.px(hx + sway, hy + 19, 'steel'); K.px(hx + sway + 1, hy + 18, 'steel')
    on = f % 10 < 4
    for dx, dy in ((0, -43), (1, -43), (0, -44), (1, -44)):
        K.px(mx + dx, my + dy, 'butter' if on else 'coral')
    K.outlined()
    V = Layer(cv)                                                                   # a little cart rolls out of the bay and back
    u = 0.4 * (0.5 - 0.5 * math.cos(2 * math.pi * f / N))
    vb = 3.1 + u
    prism(cv, V, rounded_rect(1.45, vb, 1.9, vb + 0.35, 0.03, 2), 2, 12, facade=lambda s, z, sh, x, y: ramp(sh, ['peach', 'coral', 'coralDk'], x, y), roof='white')
    for a in (1.52, 1.83):
        V.px(*P(a, vb + 0.35, 1), 'ink'); V.px(*P(a + 0.02, vb + 0.35, 1), 'ink')
    V.px(*P(1.9, vb + 0.15, 8), 'butter')
    V.outlined()
    Cr = Layer(cv)                                                                  # crates by the door
    for (a0, b0, a1, b1, z0, z1) in ((2.55, 3.25, 2.9, 3.6, 0, 12), (2.62, 3.3, 2.88, 3.56, 12, 21)):
        prism(cv, Cr, rounded_rect(a0, b0, a1, b1, 0.01, 2), z0, z1, facade=lambda s, z, sh, x, y: 'woodDk' if (s % 0.17) < 0.03 else ramp(sh, ['peach', 'wood', 'woodDk'], x, y), roof='peach')
    Cr.outlined()
    return cv, composite(cv, [g, Sh, L, K, V, Cr])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('workshop', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out'), disposal=2))   # the hook sways over open sky
