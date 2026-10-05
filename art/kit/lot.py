"""The original lots, at the new detail: pale paving with fine joints, lawn patches with texture and an edge,
paths, and round shrubs. No grey ring round the building."""
import numpy as np
from kit import Layer


def lot(cv, lawns=(), paths=(), shrubs=(), seed=1, joints=1.0):
    P = cv.P
    g = Layer(cv)
    Lc, B, R, Tp = P(0, 4), P(4, 4), P(4, 0), P(0, 0)
    g.poly([Lc, B, (B[0], B[1] + 5), (Lc[0], Lc[1] + 5)], 'slabK')
    g.poly([B, R, (R[0], R[1] + 5), (B[0], B[1] + 5)], 'slabShade')
    g.poly([Tp, R, B, Lc], 'pave')
    rnd = np.random.RandomState(seed)
    k = joints
    while k < 4 - 1e-6:                                            # fine paving joints both ways
        g.line(*P(k, 0), *P(k, 4), 'lsteel'); g.line(*P(0, k), *P(4, k), 'lsteel')
        k += joints
    for _ in range(260):
        g.px(*P(rnd.uniform(0.05, 3.95), rnd.uniform(0.05, 3.95)), 'lsteel' if rnd.rand() < 0.7 else 'white')
    for (a0, b0, a1, b1) in paths:
        g.poly([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], 'white')
        g.line(*P(a0, b0), *P(a0, b1), 'lsteel'); g.line(*P(a1, b0), *P(a1, b1), 'lsteel')
    for (a0, b0, a1, b1) in lawns:
        g.poly([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], 'lawnEdge')
        g.poly([P(a0 + 0.04, b0 + 0.04), P(a1 - 0.04, b0 + 0.04), P(a1 - 0.04, b1 - 0.04), P(a0 + 0.04, b1 - 0.04)], 'lawn')
        for _ in range(int((a1 - a0) * (b1 - b0) * 60)):
            x, y = P(rnd.uniform(a0 + 0.08, a1 - 0.08), rnd.uniform(b0 + 0.08, b1 - 0.08))
            g.px(x, y, 'lawnHi' if rnd.rand() < 0.45 else 'leaf')
    S = Layer(cv)
    for (a, b) in shrubs:                                          # round shrubs, lit from the top left
        x, y = P(a, b)
        S.ellipse(x, y - 4, 7, 5, 'leafDk'); S.ellipse(x - 1, y - 5, 6, 4, 'leaf'); S.ellipse(x - 2, y - 6, 3, 2, 'lawnHi')
    S.outlined()
    return g, S
