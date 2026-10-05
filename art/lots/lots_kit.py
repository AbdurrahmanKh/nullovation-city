"""
Nullovation City drawing kit, new standard: double detail (a plot is 256 px wide), the materials of the
user's PixelLab city hall, its tiled lavender plot with a lawn inside, and a near-black outline.
"""
import math
import numpy as np
from PIL import Image

C = {
    'ol': '#020104',
    'pv': '#D6C7E4', 'pvj': '#B7A5CF', 'pvh': '#F1E8F8', 'sl': '#A792C1', 'sr': '#8974A5', 'sd': '#6A5E7E',
    'lw': '#90BD82', 'lwd': '#73A475', 'lws': '#578D80', 'lwh': '#A3CC93', 'dk': '#2E4C5C', 'dk2': '#485B6B',
    'wh': '#F4F1F8', 'wh2': '#F1E8F8', 'wm': '#DFF0F1', 'ws1': '#C1B1CD', 'ws2': '#B7A5CF', 'ws3': '#9380A8', 'ws4': '#8974A5',
    'g0': '#E7FAFB', 'g1': '#9FF4EA', 'g2': '#88EEE2', 'g3': '#71DED1', 'g4': '#57B8B3', 'g5': '#40858E', 'g6': '#387478', 'g7': '#215E65',
    'pk0': '#F4CEDA', 'pk1': '#F1B7BB', 'pk2': '#E2A4B0', 'pk3': '#AC778B', 'pk4': '#9D617B',
    'warm': '#FFE8C9', 'warm2': '#F6D28A', 'cy': '#3FE0F0', 'neon': '#FF5FA8', 'leaf': '#5E9E6E', 'leafd': '#467E5E', 'bark': '#8A6A5A',
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in C.items()}
NAMES = list(C.keys())
ID = {n: i + 1 for i, n in enumerate(NAMES)}
NAME = {v: k for k, v in ID.items()}

W, H = 256, 520
SLAB = 6
T = H - 128 - SLAB                # the surface's top corner; the slab's bottom is the last row


def P(a, b, z=0):
    return (128 + (a - b) * 32, T + (a + b) * 16 - z)


class Layer:
    def __init__(self):
        self.c = np.zeros((H, W), dtype=np.int16)

    def px(self, x, y, col):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < W and 0 <= y < H and col:
            self.c[y, x] = ID[col]

    def poly(self, pts, col):
        ys = [p[1] for p in pts]
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys)))):
            yc = y + 0.5
            xs = []
            for i in range(len(pts)):
                (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
                if (y1 <= yc < y2) or (y2 <= yc < y1):
                    xs.append(x1 + (yc - y1) / (y2 - y1) * (x2 - x1))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(round(xs[k]), round(xs[k + 1])):
                    self.px(x, y, col(x, y) if callable(col) else col)

    def ellipse(self, cx, cy, rx, ry, col):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            d = (y + 0.5 - cy) / ry
            if abs(d) >= 1:
                continue
            half = rx * math.sqrt(1 - d * d)
            for x in range(round(cx - half), round(cx + half)):
                self.px(x, y, col(x, y) if callable(col) else col)

    def line(self, x0, y0, x1, y1, col):
        x0, y0, x1, y1 = round(x0), round(y0), round(x1), round(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def outlined(self, col='ol'):
        m = self.c > 0
        n = np.zeros_like(m)
        n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        self.c[n & ~m] = ID[col]
        return self

    def inner_outline(self, col='ol'):
        """For the plot: its own edge pixels become the outline, so the block keeps its exact size."""
        m = self.c > 0
        edge = np.zeros_like(m)
        edge[0, :] |= m[0, :]; edge[-1, :] |= m[-1, :]; edge[:, 0] |= m[:, 0]; edge[:, -1] |= m[:, -1]
        inner = np.ones_like(m)
        inner[1:, :] &= m[:-1, :]; inner[:-1, :] &= m[1:, :]; inner[:, 1:] &= m[:, :-1]; inner[:, :-1] &= m[:, 1:]
        self.c[(m & ~inner) | edge] = ID[col]
        return self


def composite(layers):
    out = np.zeros((H, W), dtype=np.int16)
    for L in layers:
        m = L.c > 0
        out[m] = L.c[m]
    return out


# ---------------- the standard plot, in the new style ----------------
def plot(paths=(), lawn=True, seed=1, ring=0.42):
    g = Layer()
    L, B, R, Tp = P(0, 4), P(4, 4), P(4, 0), P(0, 0)
    g.poly([L, B, (B[0], B[1] + SLAB), (L[0], L[1] + SLAB)], 'sl')
    g.poly([B, R, (R[0], R[1] + SLAB), (B[0], B[1] + SLAB)], 'sr')
    for k in range(64):                                              # a darker line along the slab's foot
        g.px(L[0] + 2 * k, L[1] + SLAB + k - 1, 'sd'); g.px(L[0] + 2 * k + 1, L[1] + SLAB + k - 1, 'sd')
        g.px(B[0] + 2 * k, B[1] + SLAB - k - 1, 'sd'); g.px(B[0] + 2 * k + 1, B[1] + SLAB - k - 1, 'sd')
    g.poly([Tp, R, B, L], 'pv')
    r = ring
    if lawn:
        g.poly([P(r, r), P(4 - r, r), P(4 - r, 4 - r), P(r, 4 - r)], 'lw')
        rnd = np.random.RandomState(seed)
        for _ in range(260):
            a, b = rnd.uniform(r + 0.05, 4 - r - 0.05), rnd.uniform(r + 0.05, 4 - r - 0.05)
            x, y = P(a, b)
            g.px(x, y, 'lwd' if rnd.rand() < 0.75 else 'lwh')
        for k in range(int((4 - 2 * r) * 32)):                        # lawn edge shadow under the paving lip
            a = r + k / 32
            x, y = P(a, r); g.px(x, y + 1, 'lws'); g.px(x + 1, y + 1, 'lws')
            x, y = P(r, a); g.px(x, y + 1, 'lws'); g.px(x - 1, y + 1, 'lws')
    for (a0, b0, a1, b1) in paths:
        g.poly([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], 'pv')
    # paving joints: tiles half a tile long around the ring, and on paths
    def joint_a(a, b0, b1):
        for k in range(int((b1 - b0) * 32) + 1):
            x, y = P(a, b0 + k / 32); g.px(x, y, 'pvj')
    def joint_b(b, a0, a1):
        for k in range(int((a1 - a0) * 32) + 1):
            x, y = P(a0 + k / 32, b); g.px(x, y, 'pvj')
    for k in range(9):
        t = k * 0.5
        joint_a(t, 0, r); joint_a(t, 4 - r, 4); joint_b(t, 0, r); joint_b(t, 4 - r, 4)
    for (a0, b0, a1, b1) in paths:
        if (a1 - a0) < (b1 - b0):
            for bb in np.arange(b0 + 0.4, b1, 0.4):
                joint_b(bb, a0, a1)
            joint_a(a0, b0, b1); joint_a(a1, b0, b1)
        else:
            for aa in np.arange(a0 + 0.4, a1, 0.4):
                joint_a(aa, b0, b1)
            joint_b(b0, a0, a1); joint_b(b1, a0, a1)
    if lawn:
        joint_b(r, r, 4 - r); joint_b(4 - r, r, 4 - r); joint_a(r, r, 4 - r); joint_a(4 - r, r, 4 - r)
    for k in range(64):                                              # light rim along the two front edges
        for d in (0, 1):
            g.px(L[0] + 2 * k + d, L[1] + k, 'pvh')
            g.px(B[0] + 2 * k + d, B[1] - k - 1, 'pvh')
    return g.inner_outline()


# ---------------- shapes ----------------
def quad_left(L, a0, a1, b, z0, z1, col):
    L.poly([P(a0, b, z1), P(a1, b, z1), P(a1, b, z0), P(a0, b, z0)], col)


def quad_right(L, b0, b1, a, z0, z1, col):
    L.poly([P(a, b0, z1), P(a, b1, z1), P(a, b1, z0), P(a, b0, z0)], col)


def face(L, p0, p1, z0, z1, col):
    """A vertical face between two ground points (a, b), from height z0 to z1."""
    (a0, b0), (a1, b1) = p0, p1
    L.poly([P(a0, b0, z1), P(a1, b1, z1), P(a1, b1, z0), P(a0, b0, z0)], col)


def top(L, pts, z, col):
    L.poly([P(a, b, z) for a, b in pts], col)


def blob(L, cx, cy, r, base, hi, dk):
    for dy in range(-math.ceil(r), math.ceil(r) + 1):
        for dx in range(-math.ceil(r), math.ceil(r) + 1):
            if dx * dx + dy * dy > r * r:
                continue
            s = dx + dy
            L.px(cx + dx, cy + dy, hi if s < -r * 0.55 else (dk if s > r * 0.45 else base))


def on_window(N, start, length):
    return {(start + k) % N for k in range(length)}


def save(name, frames_idx, delays, out_dir):
    stack = np.stack(frames_idx)
    vis = (stack > 0).any(axis=0)
    ys, xs = np.nonzero(vis)
    assert xs.min() == 0 and xs.max() == W - 1 and ys.max() == H - 1, (name, xs.min(), xs.max(), ys.max())
    stack = stack[:, int(ys.min()):, :]
    used = sorted({NAME[int(v)] for v in np.unique(stack) if v})
    pal = [0, 0, 0] + sum((list(RGB[n]) for n in NAMES), [])
    pal += [0] * (768 - len(pal))
    ims = []
    for fr in stack:
        im = Image.fromarray(fr.astype(np.uint8), 'P'); im.putpalette(pal); ims.append(im)
    ims[0].save(f'{out_dir}/{name}.gif', save_all=True, append_images=ims[1:], duration=delays, loop=0,
                transparency=0, disposal=1, optimize=False)
    return {'name': name, 'w': W, 'h': int(stack.shape[1]), 'frames': len(frames_idx), 'colors': len(used)}
