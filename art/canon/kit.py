"""
Nullovation City drawing kit: SNES-style isometric pixel art drawn in code.
One pixel size, 2:1 isometric, light from the top left, a 1 px dark outline, colors only from
the 32-color city palette (at most 16 per building), and the city's exact standard plot.
"""
import math
import numpy as np
from PIL import Image

PALETTE = [
    ('ink', '#2B2542'), ('outline', '#5A5073'), ('steel', '#7A7394'), ('asphalt', '#908BA5'),
    ('slabShade', '#B6ABCA'), ('slab', '#CBC2DB'), ('lsteel', '#D6CEE2'), ('ground', '#E1DAE9'),
    ('pave', '#F4F1F8'), ('white', '#FFFFFF'),
    ('dleaf', '#58AF80'), ('leaf', '#74C997'), ('lawn', '#A9E2BE'), ('mint', '#D4F2DE'),
    ('rose', '#D9799F'), ('pink', '#F4A3C3'), ('blush', '#FBD3E3'),
    ('dteal', '#3FA79E'), ('teal', '#7FD6CE'), ('iteal', '#C4F0EB'),
    ('violet', '#8E7BD0'), ('lavender', '#B7A5F0'), ('lilac', '#E0D8FB'),
    ('sky', '#6FA5DE'), ('psky', '#9CC7F3'),
    ('gold', '#F2C75C'), ('butter', '#FFE38A'),
    ('coral', '#F29A74'), ('peach', '#FFB797'),
    ('neon', '#EE4C93'), ('cyan', '#3FE0F0'),
    ('wood', '#9C7C6B'),
]
ID = {name: i + 1 for i, (name, _) in enumerate(PALETTE)}
NAME = {v: k for k, v in ID.items()}
RGB = {name: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for name, h in PALETTE}

W, H = 128, 240
T = H - 67                      # the plot surface's top corner; the slab's bottom is the last row


def P(a, b, z=0):
    """Plot tile coordinates (0..4 on each axis) and a height in pixels, to canvas pixels."""
    return (64 + (a - b) * 16, T + (a + b) * 8 - z)


class Layer:
    def __init__(self):
        self.c = np.zeros((H, W), dtype=np.int16)

    def px(self, x, y, col):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < W and 0 <= y < H and col:
            self.c[y, x] = ID[col]

    def get(self, x, y):
        return NAME.get(int(self.c[y, x])) if 0 <= x < W and 0 <= y < H else None

    def poly(self, pts, col):
        """Scanline fill at pixel centers: the same rule the city tool uses, so edges match."""
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

    def outlined(self, col='outline'):
        m = self.c > 0
        n = np.zeros_like(m)
        n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        self.c[n & ~m] = ID[col]
        return self


def composite(layers):
    out = np.zeros((H, W), dtype=np.int16)
    for L in layers:
        m = L.c > 0
        out[m] = L.c[m]
    return out


# ---------------- the standard plot ----------------
def ground(lawns=(), paths=(), pools=(), shrubs=(), tiles=True, seed=1, frame=0):
    """lawns/paths/pools are (a0, b0, a1, b1) rectangles in plot tiles. Pools shimmer by frame."""
    g = Layer()
    L, B, R, Tp = P(0, 4), P(4, 4), P(4, 0), P(0, 0)
    g.poly([L, B, (B[0], B[1] + 3), (L[0], L[1] + 3)], 'slab')
    g.poly([B, R, (R[0], R[1] + 3), (B[0], B[1] + 3)], 'slabShade')
    g.poly([Tp, R, B, L], 'pave')
    if tiles:
        for k in (1, 2, 3):
            for i in range(0, 64):
                x0, y0 = P(0, k); g.px(x0 + i, y0 + i // 2, 'lsteel')
                x1, y1 = P(k, 0); g.px(x1 - i - 1, y1 + i // 2, 'lsteel')
    rnd = np.random.RandomState(seed)
    for (a0, b0, a1, b1) in lawns:
        g.poly([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], 'lawn')
        area = (a1 - a0) * (b1 - b0)
        for _ in range(int(area * 18)):
            x, y = P(rnd.uniform(a0 + 0.05, a1 - 0.05), rnd.uniform(b0 + 0.05, b1 - 0.05))
            g.px(x, y, 'leaf')
    for (a0, b0, a1, b1) in paths:
        g.poly([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], 'pave')
    for (a0, b0, a1, b1) in pools:
        g.poly([P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], 'white')
        g.poly([P(a0 + 0.08, b0 + 0.08), P(a1 - 0.08, b0 + 0.08), P(a1 - 0.08, b1 - 0.08), P(a0 + 0.08, b1 - 0.08)], 'teal')
        for k in range(10):                        # ripples move one step each frame
            u = ((k * 0.37 + frame * 0.125) % 1.0)
            v = (k * 0.61) % 1.0
            x, y = P(a0 + 0.15 + u * (a1 - a0 - 0.3), b0 + 0.15 + v * (b1 - b0 - 0.3))
            g.px(x, y, 'iteal'); g.px(x + 1, y, 'iteal')
            if k % 3 == 0:
                g.px(x + 2, y, 'white')
    for (a, b) in shrubs:
        x, y = P(a, b)
        x, y = round(x), round(y)
        for dx, dy, c in ((-1, 0, 'dleaf'), (0, 0, 'leaf'), (1, 0, 'dleaf'), (-1, -1, 'leaf'), (0, -1, 'lawn'), (1, -1, 'leaf'), (0, -2, 'leaf')):
            g.px(x + dx, y + dy, c)
    for k in range(32):                            # the rim of light on the front edges, as the city draws it
        for d in (0, 1):
            g.px(L[0] + 2 * k + d, L[1] + k - 1, 'white')
            g.px(B[0] + 2 * k + d, B[1] - k - 1, 'white')
    return g


def std_lawns():
    return [(0, 3.1, 4, 4), (0, 0, 0.9, 3.1)]


# ---------------- shapes ----------------
def box(L, a0, b0, a1, b1, z0, z1, left, right, top):
    """An upright box on the plot. Left face (facing down-left) is lit, right face is in shade."""
    L.poly([P(a0, b1, z0), P(a1, b1, z0), P(a1, b1, z1), P(a0, b1, z1)], left)
    L.poly([P(a1, b1, z0), P(a1, b0, z0), P(a1, b0, z1), P(a1, b1, z1)], right)
    L.poly([P(a0, b0, z1), P(a1, b0, z1), P(a1, b1, z1), P(a0, b1, z1)], top)


def win_left(L, a0, a1, b, z0, z1, col, frame_col=None):
    """A window on a left face (the plane b = const), from a0 to a1, between heights z0 and z1."""
    if frame_col:
        L.poly([P(a0, b, z1), P(a1, b, z1), P(a1, b, z0), P(a0, b, z0)], frame_col)
        a0 += 1 / 16; a1 -= 1 / 16; z0 += 1; z1 -= 1
    L.poly([P(a0, b, z1), P(a1, b, z1), P(a1, b, z0), P(a0, b, z0)], col)


def win_right(L, b0, b1, a, z0, z1, col, frame_col=None):
    """A window on a right face (the plane a = const), from b0 to b1."""
    if frame_col:
        L.poly([P(a, b0, z1), P(a, b1, z1), P(a, b1, z0), P(a, b0, z0)], frame_col)
        b0 += 1 / 16; b1 -= 1 / 16; z0 += 1; z1 -= 1
    L.poly([P(a, b0, z1), P(a, b1, z1), P(a, b1, z0), P(a, b0, z0)], col)


def cylinder(L, cx, cyb, rx, ry, h, bands, top=None, z0=0):
    """Upright cylinder with its base ellipse centred at (cx, cyb). bands: [(nx_from, color)...]
    shade across the width, lit from the left; a 2 px checker softens each band edge."""
    cyb -= z0
    for x in range(int(cx - rx), int(cx + rx) + 1):
        nx = (x + 0.5 - cx) / rx
        if abs(nx) >= 1:
            continue
        e = ry * math.sqrt(1 - nx * nx)
        col = bands[0][1]
        for i in range(len(bands) - 1, -1, -1):
            if nx >= bands[i][0]:
                col = bands[i][1]
                nxt = bands[i + 1][0] if i + 1 < len(bands) else None
                break
        for y in range(round(cyb - h + e), round(cyb + e)):
            c = col
            if nxt is not None and (cx + nxt * rx) - (x + 0.5) < 2 and (x + y) % 2 == 0:
                c = bands[i + 1][1]
            L.px(x, y, c)
    if top:
        L.ellipse(cx, cyb - h, rx, ry, top)


def wall_y(cx, cy, rx, ry, x):
    """Lower edge of an ellipse at column x (for things that follow a cylinder's curve)."""
    nx = (x + 0.5 - cx) / rx
    return cy + ry * math.sqrt(max(0.0, 1 - nx * nx))


def dome(L, cx, cy, rx, ry, h, fill, highlight='white'):
    """A dome sitting on the ellipse (cx, cy, rx, ry), rising h px. fill(x, y, nx) gives the color."""
    for y in range(int(cy - h) - 1, int(cy + ry) + 1):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 1):
            nx = (x + 0.5 - cx) / rx
            if abs(nx) >= 1:
                continue
            top = cy - h * math.sqrt(1 - nx * nx)
            bottom = cy + ry * math.sqrt(1 - nx * nx)
            if top <= y + 0.5 < bottom:
                L.px(x, y, fill(x, y, nx))
    if highlight:
        for k in range(8):
            ang = math.radians(205 + k * 8)
            L.px(cx + (rx - 4) * math.cos(ang), cy + (h - 3) * math.sin(ang), highlight)


def blob(L, cx, cy, r, base, hi, dk):
    for dy in range(-math.ceil(r), math.ceil(r) + 1):
        for dx in range(-math.ceil(r), math.ceil(r) + 1):
            if dx * dx + dy * dy > r * r:
                continue
            s = dx + dy
            L.px(cx + dx, cy + dy, hi if s < -r * 0.6 else (dk if s > r * 0.5 else base))


def steam(L, x, y, frame, period=8, height=10):
    """A puff that rises and fades over the loop."""
    t = (frame % period) / period
    yy = y - t * height
    r = 1 + t * 2
    col = 'white' if t < 0.5 else 'lsteel'
    if t < 0.85:
        for dy in range(-2, 3):
            for dx in range(-3, 4):
                if dx * dx / (r * r + 0.01) + dy * dy / (r * 0.7 + 0.3) ** 2 <= 1:
                    L.px(x + dx + t * 2, yy + dy, col)


# ---------------- export ----------------
def save(name, frames_idx, delays, out_dir):
    """Crops every frame to the union of what is ever visible, checks the rules, writes GIF and PNG."""
    stack = np.stack(frames_idx)
    vis = (stack > 0).any(axis=0)
    ys, xs = np.nonzero(vis)
    assert xs.min() == 0 and xs.max() == W - 1 and ys.max() == H - 1, (name, xs.min(), xs.max(), ys.max())
    top = int(ys.min())
    stack = stack[:, top:, :]
    used = sorted({NAME[int(v)] for v in np.unique(stack) if v})
    assert len(used) <= 16, (name, len(used), used)
    order = [n for n, _ in PALETTE]
    pal = [0, 0, 0] + sum((list(RGB[n]) for n in order), [])
    pal += [0] * (768 - len(pal))
    ims = []
    for fr in stack:
        im = Image.fromarray(fr.astype(np.uint8), 'P'); im.putpalette(pal); ims.append(im)
    ims[0].save(f'{out_dir}/{name}.gif', save_all=True, append_images=ims[1:], duration=delays, loop=0,
                transparency=0, disposal=2, optimize=False)
    rgba = np.zeros(stack.shape[1:] + (4,), dtype=np.uint8)
    for v in np.unique(stack[0]):
        if v:
            rgba[stack[0] == v] = RGB[NAME[int(v)]] + (255,)
    Image.fromarray(rgba, 'RGBA').save(f'{out_dir}/{name}.png')
    return {'name': name, 'w': W, 'h': int(stack.shape[1]), 'frames': len(frames_idx), 'colors': len(used), 'used': used}
