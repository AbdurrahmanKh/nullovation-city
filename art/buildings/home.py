"""Home, new standard: a small pastel house with a gabled roof, a chimney, and windows, with a fence,
a tree, and a mailbox. Motion: a window's light changes now and then."""
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'kit'))   # the shared 256 px kit, in art/kit
from kit import Canvas, Layer, plot, prism, rounded_rect, circle, tree, composite, ramp, save
from parks import bench, lamp
from lot import lot
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
N, DELAY = 40, 250
A0, A1, B0, B1, ZE, ZR = 1.35, 2.7, 1.4, 2.65, 33, 52          # the original's footprint and height
BM = (B0 + B1) / 2
LIT = {(0, 0): set(range(40)), (1, 0): set(range(8, 28)), (0, 1): set(range(22, 40)) | set(range(0, 5)), (1, 1): set()}


def walls(f):
    def fac(s, z, sh, x, y):
        if z < 3: return ramp(sh, ['l3', 'l4', 'l5'], x, y)
        return ramp(sh, ['p0', 'p0', 'p1', 'p1', 'p2'], x, y)
    return fac


def frame(f):
    cv = Canvas(260)
    P = cv.P
    g, Sh = lot(cv, lawns=[(0, 2.9, 4, 4), (0, 0, 1.1, 2.9), (3.1, 0, 4, 1.1)], paths=[(1.9, 2.9, 2.3, 4)], shrubs=[(0.5, 1.1), (0.55, 2.4), (1.3, 3.5), (3.6, 0.6)], seed=11)
    T = Layer(cv)
    tree(T, *P(0.8, 3.15), 12, seed=29)
    T.outlined()
    H = Layer(cv)
    prism(cv, H, rounded_rect(A0, B0, A1, B1, 0.01, 2), 0, ZE, facade=walls(f), roof=None)
    H.poly([P(A1, B1, ZE), P(A1, BM, ZR), P(A1, B0, ZE)], 'p1')                         # the gable end, on the right
    H.poly([P(A0 - 0.05, B1 + 0.08, ZE - 1), P(A1 + 0.05, B1 + 0.08, ZE - 1), P(A1 + 0.05, BM, ZR + 1), P(A0 - 0.05, BM, ZR + 1)], 'p3')   # the front slope
    for k in range(1, 6):
        z = ZE - 1 + (ZR - ZE + 2) * k / 6
        b = B1 + 0.08 - (B1 + 0.08 - BM) * k / 6
        H.line(*P(A0 - 0.05, b, z), *P(A1 + 0.05, b, z), 'p4')                      # roof courses
    H.line(*P(A0 - 0.05, BM, ZR + 1), *P(A1 + 0.05, BM, ZR + 1), 'p2')
    prism(cv, H, rounded_rect(1.6, 1.62, 1.82, 1.84, 0.01, 2), ZR - 8, ZR + 11, facade=lambda s, z, sh, x, y: ramp(sh, ['l3', 'l4', 'l5'], x, y), roof='l6')   # the chimney
    for (a0, a1, z0, z1, col) in ((1.93, 2.27, 0, 21, 'wood'), (1.96, 2.24, 0, 20, 'woodDk')):   # the door, at the head of the path
        H.poly([P(a0, B1 + 0.01, z1), P(a1, B1 + 0.01, z1), P(a1, B1 + 0.01, z0), P(a0, B1 + 0.01, z0)], col)
    for (k, a0) in ((0, 1.5), (1, 2.35)):                                                  # two front windows either side of the door
        on = f in LIT[(k, 0)]
        H.poly([P(a0, B1 + 0.01, 25), P(a0 + 0.3, B1 + 0.01, 25), P(a0 + 0.3, B1 + 0.01, 11), P(a0, B1 + 0.01, 11)], 'white')
        H.poly([P(a0 + 0.03, B1 + 0.012, 24), P(a0 + 0.27, B1 + 0.012, 24), P(a0 + 0.27, B1 + 0.012, 12), P(a0 + 0.03, B1 + 0.012, 12)], 'lit1' if on else 'g4')
    for (k, b0) in ((1, 1.62), (0, 2.12)):                                                # two side windows, on the right
        on = f in LIT[(k, 1)]
        H.poly([P(A1 + 0.01, b0, 25), P(A1 + 0.01, b0 + 0.32, 25), P(A1 + 0.01, b0 + 0.32, 11), P(A1 + 0.01, b0, 11)], 'white')
        H.poly([P(A1 + 0.012, b0 + 0.03, 24), P(A1 + 0.012, b0 + 0.29, 24), P(A1 + 0.012, b0 + 0.29, 12), P(A1 + 0.012, b0 + 0.03, 12)], 'lit1' if on else 'g5')
    H.outlined()
    F = Layer(cv)                                                              # a low white fence along the front, and a mailbox
    for k in range(12):
        a = 2.15 + k * 0.1
        F.line(*P(a, 3.25, 0), *P(a, 3.25, 7), 'white')
    F.line(*P(2.15, 3.25, 5), *P(3.25, 3.25, 5), 'rim')
    F.line(*P(1.35, 3.0, 0), *P(1.35, 3.0, 9), 'l6')
    prism(cv, F, rounded_rect(1.29, 2.96, 1.43, 3.06, 0.02, 2), 9, 13, roof='sky')
    F.outlined()
    return cv, composite(cv, [g, Sh, T, H, F, lamp(cv, 3.3, 2.75)])


if __name__ == '__main__':
    frames = [frame(f)[1] for f in range(N)]
    print(save('home', frame(0)[0], frames, [DELAY] * N, str(NC / 'art/out')))
