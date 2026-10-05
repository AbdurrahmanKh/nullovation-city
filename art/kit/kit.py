"""
Nullovation City kit, new standard: 256 px wide art in the style of the user's city hall.
Black 1 px outlines, soft lilac shading with checker dithering, teal glass, pink trims,
and the plot recipe measured from that building (tile ring, recessed lawn, 4 px slab).
"""
import os
import math
import numpy as np
from PIL import Image

C = {  # sampled from the user's building, plus warm lights and neon for things that glow
    'ink': '#020104',
    'white': '#F4F1F8', 'rim': '#F1E8F8', 'l1': '#E4DCEE', 'tile': '#D6C7E4', 'l2': '#C3BDDD', 'l3': '#C1B1CD',
    'l4': '#B7A5CF', 'l5': '#A792C1', 'l6': '#9380A8', 'l7': '#8974A5', 'l8': '#6A5E7E',
    'lawn': '#90BD82', 'lawnHi': '#A4CC94', 'lawnEdge': '#578D80', 'lawnDark': '#485B6B', 'leaf': '#6FA870', 'leafDk': '#4E8A67',
    'g0': '#E7FAFB', 'g1': '#C2FBF5', 'g2': '#9FF4EA', 'g3': '#88EEE2', 'g4': '#57B8B3', 'g5': '#40858E', 'g6': '#387478',
    'g7': '#215E65', 'g8': '#2E4C5C', 'gm': '#96D0D4', 'gs': '#5F8993',
    'p0': '#F4CEDA', 'p1': '#F1B7BB', 'p2': '#E6ACB3', 'p3': '#E2A4B0', 'p4': '#AC778B', 'p5': '#A76E89', 'p6': '#9D617B',
    'lit0': '#FFF6D2', 'lit1': '#FFE38A', 'lit2': '#F2C75C',
    'neonP': '#EE4C93', 'neonC': '#3FE0F0', 'cyanDim': '#2FA7B4',
    'steel': '#7A7394', 'asphalt': '#908BA5', 'wood': '#9C7C6B', 'flower': '#F4A3C3', 'flowerHi': '#FBD3E3',
    'sky': '#6FA5DE', 'skyHi': '#9CC7F3', 'skyDk': '#5282B8',
    'cyan': '#3FE0F0', 'neon': '#EE4C93',
    'pCoral': '#F29A74', 'pSky': '#6FA5DE', 'pMint': '#74C997', 'pButter': '#FFE38A', 'pLav': '#B7A5F0', 'pPeach': '#FFB797', 'pCoralD': '#B98A80', 'pSkyD': '#6E9DB8', 'pMintD': '#7BB39C', 'pButterD': '#C9C79A', 'pLavD': '#A09AC8', 'pPeachD': '#C9A59A', 'mint': '#D4F2DE',
    'pink': '#F4A3C3', 'rose': '#D9799F',
    'violet': '#8E7BD0', 'violetDk': '#6F5DB4', 'lavender': '#B7A5F0', 'lilac': '#E0D8FB',
    'gold': '#F2C75C', 'goldDk': '#C99A3A', 'butter': '#FFE38A', 'coral': '#F29A74', 'coralDk': '#D2785A', 'peach': '#FFB797',
    'teal': '#7FD6CE', 'dteal': '#3FA79E', 'iteal': '#C4F0EB', 'pave': '#F4F1F8', 'lsteel': '#D6CEE2', 'slabK': '#CBC2DB', 'slabShade': '#B6ABCA',
    'crane': '#E8B84A', 'craneDk': '#B8872A', 'craneHi': '#E2BA66', 'dirt': '#A68A6D', 'dirtDk': '#86694F', 'dirtHi': '#C2A98C',
    'gravel': '#CDBFAE', 'safety': '#EE7A3C', 'net': '#4E8A67', 'netHi': '#6FA870', 'woodDk': '#6E5446',
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in C.items()}
NAMES = list(C.keys())
ID = {n: i + 1 for i, n in enumerate(NAMES)}
NAME = {i: n for n, i in ID.items()}

W = 256
TW = 245 / 4          # one plot tile, in pixels, across (the plot spans x 5..250)
HX, HY = TW / 2, TW / 4


class Canvas:
    def __init__(self, h):
        self.h = h
        self.cx = 127.5
        self.top = h - 1 - 4 - 2 * 4 * HY    # plot surface top corner, so the slab's outline is the last row
        self.c = np.zeros((h, W), dtype=np.int16)

    def P(self, a, b, z=0):
        return (self.cx + (a - b) * HX, self.top + (a + b) * HY - z)


class Layer:
    def __init__(self, cv):
        self.cv = cv
        self.c = np.zeros_like(cv.c)

    def px(self, x, y, col):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < W and 0 <= y < self.cv.h and col:
            self.c[y, x] = ID[col]

    def get(self, x, y):
        return NAME.get(int(self.c[y, x])) if 0 <= x < W and 0 <= y < self.cv.h else None

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

    def quad(self, a0, b0, a1, b1, col, z=0):
        P = self.cv.P
        self.poly([P(a0, b0, z), P(a1, b0, z), P(a1, b1, z), P(a0, b1, z)], col)

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

    def ellipse(self, cx, cy, rx, ry, col):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            d = (y + 0.5 - cy) / ry
            if abs(d) >= 1:
                continue
            half = rx * math.sqrt(1 - d * d)
            for x in range(round(cx - half), round(cx + half)):
                self.px(x, y, col(x, y) if callable(col) else col)

    def outlined(self, col='ink'):
        m = self.c > 0
        n = np.zeros_like(m)
        n[1:, :] |= m[:-1, :]; n[:-1, :] |= m[1:, :]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        self.c[n & ~m] = ID[col]
        return self


def composite(cv, layers):
    out = np.zeros_like(cv.c)
    for L in layers:
        m = L.c > 0
        out[m] = L.c[m]
    return out


def ramp(t, cols, x, y):
    """Pick from a light-to-dark ramp at t in 0..1, with a checker between neighbouring steps."""
    t = min(max(t, 0.0), 0.9999) * (len(cols) - 1)
    i = int(t)
    f = t - i
    if i + 1 < len(cols) and f > 0.5 and (x + y) % 2 == 0:
        return cols[i + 1]
    if i + 1 < len(cols) and f > 0.8:
        return cols[i + 1]
    return cols[i]


# ---------------- the standard plot ----------------
def plot(cv, lawn=True, path=None, ring=0.44, seed=0, ground='lawn'):
    """The plot, measured from the user's building. path: (a0, a1, b_from): a paved path from a door
    at b_from out to the front-left ring, between a0 and a1."""
    g = Layer(cv)
    P = cv.P
    Lc, B, R, Tp = P(0, 4), P(4, 4), P(4, 0), P(0, 0)
    g.poly([Lc, B, (B[0], B[1] + 4), (Lc[0], Lc[1] + 4)], 'l5')
    g.poly([B, R, (R[0], R[1] + 4), (B[0], B[1] + 4)], 'l7')
    g.poly([Tp, R, B, Lc], 'tile')
    w, px = ring, 1.25 / TW
    for (a0, b0, a1, b1, along_a) in ((0, 0, 4, w, True), (0, 4 - w, 4, 4, True), (0, 0, w, 4, False), (4 - w, 0, 4, 4, False)):
        for k in range(1, 9):                                     # joints across the ring, big square-ish tiles
            s_ = k * 4 / 9
            if along_a:
                g.quad(s_, b0, s_ + px, b1, 'l5')
            else:
                g.quad(a0, s_, a1, s_ + px, 'l5')
        mid = (b0 + b1) / 2 if along_a else (a0 + a1) / 2         # and one line down the middle
        if along_a:
            g.quad(0, mid, 4, mid + px, 'l4')
        else:
            g.quad(mid, 0, mid + px, 4, 'l4')
    if lawn:
        g.quad(w, w, 4 - w, 4 - w, 'l6')                           # the ring's inner edge casts a little shadow
        g.quad(w + px, w + px, 4 - w, 4 - w, 'lawnDark')
        g.quad(w + 2 * px, w + 2 * px, 4 - w, 4 - w, 'lawnEdge')
        g.quad(w + 3.5 * px, w + 3.5 * px, 4 - w, 4 - w, 'lawn' if ground == 'lawn' else 'dirt')
        if ground == 'dirt':
            rnd = np.random.RandomState(seed + 5)
            for _ in range(420):                                   # packed earth: gravel and darker clods
                a, b = rnd.uniform(w + 0.06, 4 - w - 0.04, 2)
                x, y = cv.P(a, b)
                g.px(x, y, 'dirtDk' if rnd.rand() < 0.5 else ('dirtHi' if rnd.rand() < 0.7 else 'gravel'))
            for off in (0.0, 0.16):                                 # tyre tracks sweeping in from the front
                for k in range(160):
                    t = k / 159
                    a = 1.0 + 1.9 * t + off * 0.3
                    b = 3.5 - 1.2 * t * t + off
                    x, y = cv.P(a, b)
                    g.px(x, y, 'dirtDk'); g.px(x + 1, y, 'dirtDk')
        if path:
            a0, a1, bf = path
            g.quad(a0, bf, a1, 4 - w + px, 'tile')
            g.quad(a0 - px, bf, a0, 4 - w, 'l6')
            n = max(1, int(round((4 - w - bf) / 0.4)))
            for k in range(1, n):
                s_ = bf + k * (4 - w - bf) / n
                g.quad(a0, s_, a1, s_ + px, 'l5')
    for k in range(int(2 * HX * 4) + 2):                          # the rim of light on the front edges
        t = k / (2 * HX * 4)
        g.px(Lc[0] + (B[0] - Lc[0]) * t, Lc[1] + (B[1] - Lc[1]) * t - 0.5, 'rim')
        g.px(B[0] + (R[0] - B[0]) * t, B[1] + (R[1] - B[1]) * t - 0.5, 'rim')
    return g.outlined()


# ---------------- a general upright prism: any footprint, shaded by its surface angle ----------------
LIGHT = (0.32, 0.95)      # in the plot plane: light comes from the +b side (the left face), a little from +a


def prism(cv, L, foot, z0, z1, facade=None, roof='white', roof_fn=None, samples=4000):
    """foot: closed polygon in plot tiles [(a, b), ...], counter-clockwise seen from above.
    facade(s, z, shade, x, y) returns a color or None (None = plain wall). s is the arc length in tiles."""
    P = cv.P
    pts = foot + [foot[0]]
    segs = []
    total = 0.0
    for i in range(len(foot)):
        (a0, b0), (a1, b1) = pts[i], pts[i + 1]
        ln = math.hypot(a1 - a0, b1 - b0)
        segs.append((a0, b0, a1, b1, total, ln))
        total += ln
    cols = {}
    for k in range(samples):
        s = total * k / samples
        hit = None
        for (a0, b0, a1, b1, s0, ln) in segs:
            if ln and s0 <= s < s0 + ln:
                hit = (a0, b0, a1, b1, s0, ln)
                break
        if not hit:
            continue
        a0, b0, a1, b1, s0, ln = hit
        t = (s - s0) / ln
        a, b = a0 + (a1 - a0) * t, b0 + (b1 - b0) * t
        ta, tb = (a1 - a0) / ln, (b1 - b0) / ln
        na, nb = tb, -ta                           # outward normal for a counter-clockwise loop
        if na + nb <= 0:                           # faces away from the viewer
            continue
        x, _ = P(a, b)
        xi = int(math.floor(x))
        depth = a + b
        if xi not in cols or depth > cols[xi][0]:
            cols[xi] = (depth, a, b, s, na, nb)
    for xi, (depth, a, b, s, na, nb) in cols.items():
        ln_ = math.hypot(*LIGHT)
        dot = (na * LIGHT[0] + nb * LIGHT[1]) / ln_
        shade = max(0.0, min(1.0, (0.95 - dot) / 0.85))      # 0 = facing the light, 1 = in full shade
        _, ybase = P(a, b)
        for y in range(int(math.floor(ybase - z1)), int(math.floor(ybase - z0))):
            z = ybase - (y + 0.5)
            col = facade(s, z, shade, xi, y) if facade else None
            if col is False:
                continue
            L.px(xi, y, col or ramp(shade, ['white', 'rim', 'l1', 'tile', 'l3', 'l4', 'l5'], xi, y))
    top = [P(a, b, z1) for (a, b) in foot]
    if roof_fn:
        L.poly(top, roof_fn)
    elif roof:
        L.poly(top, roof)
    return total


def rounded_rect(a0, b0, a1, b1, r, n=10):
    """Counter-clockwise rounded rectangle in the plot plane (seen from above: a to the right-down, b to the left-down)."""
    pts = []
    corners = [(a1 - r, b0 + r, -90, 0), (a1 - r, b1 - r, 0, 90), (a0 + r, b1 - r, 90, 180), (a0 + r, b0 + r, 180, 270)]
    for (ca, cb, d0, d1) in corners:
        for k in range(n + 1):
            ang = math.radians(d0 + (d1 - d0) * k / n)
            pts.append((ca + r * math.cos(ang), cb + r * math.sin(ang)))
    return pts


def circle(ca, cb, r, n=48):
    return [(ca + r * math.cos(2 * math.pi * k / n), cb + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def tree(L, x, y, r, seed=0):
    """A round tree in the user's style: trunk, three-tone canopy, black outline added by the layer."""
    x, y = round(x), round(y)
    for dy in range(0, 5):
        L.px(x, y - dy, 'wood'); L.px(x + 1, y - dy, 'p6')
    cy = y - 4 - r
    rnd = np.random.RandomState(seed)
    for dy in range(-r, r + 1):
        for dx in range(-r - 1, r + 2):
            d = (dx / (r + 0.8)) ** 2 + (dy / r) ** 2
            if d > 1:
                continue
            sh = (dx * 0.6 + dy * 0.8) / r
            col = 'lawnHi' if sh < -0.45 else ('lawn' if sh < 0.05 else ('leaf' if sh < 0.5 else 'leafDk'))
            if col == 'lawn' and rnd.rand() < 0.12:
                col = 'lawnHi'
            L.px(x + dx, cy + dy, col)


# ---------------- export ----------------
def save(name, cv, frames, delays, out_dir, disposal=1):
    """disposal=1 stores only what changes (small files); use 2 when something moves over empty sky."""
    os.makedirs(out_dir, exist_ok=True)              # art/out is kept by neither git nor the source archive
    stack = np.stack(frames)
    vis = (stack > 0).any(axis=0)
    ys, xs = np.nonzero(vis)
    top = int(ys.min())
    assert ys.max() == cv.h - 1, (name, ys.max(), cv.h)
    stack = stack[:, top:, :]
    used = sorted({NAME[int(v)] for v in np.unique(stack) if v})
    pal = [0, 0, 0] + sum((list(RGB[n]) for n in NAMES), [])
    pal += [0] * (768 - len(pal))
    ims = []
    for fr in stack:
        im = Image.fromarray(fr.astype(np.uint8), 'P'); im.putpalette(pal); ims.append(im)
    ims[0].save(f'{out_dir}/{name}.gif', save_all=True, append_images=ims[1:], duration=delays, loop=0,
                transparency=0, disposal=disposal, optimize=False)
    rgba = np.zeros(stack.shape[1:] + (4,), dtype=np.uint8)
    for v in np.unique(stack[0]):
        if v:
            rgba[stack[0] == v] = RGB[NAME[int(v)]] + (255,)
    Image.fromarray(rgba, 'RGBA').save(f'{out_dir}/{name}.png')
    return {'name': name, 'w': W, 'h': int(stack.shape[1]), 'frames': len(frames), 'colors': len(used)}
