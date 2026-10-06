"""Fits a PixelLab building's lot to the city's plot, measured from a reference building (the city hall by default):
every shipped building stands on the same plot, its outline spanning x 5 to 250 of the 256 px art, with a 2:1
surface, a white front rim, a slab in two shades and a 1 px outline.

Pro, with the city hall as its style image, often draws that plot exactly (the drone port and Half Cards did); then
the art is kept as it is. When the lot is 2:1 but a different size or a little off center, it is redrawn on the
reference plot in the lot's own colors, with the original's lot surface and building laid on it. The ground that the
new plot adds beyond the original's edges is carried out from the original along the tile joints, so joint lines and
lawns reach the new rim, and the original's own rim, slab and outline are left out, so no double line remains. A lot
whose edges are not 2:1 (a turned camera) cannot be fixed this way without smearing it, and is refused.

  python art/kit/fixlot.py IN.png OUT.png [--ref src/buildings/city-hall.png]"""
import argparse, pathlib, sys
from collections import Counter
import numpy as np
from PIL import Image

NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
REF = NC / 'src' / 'buildings' / 'city-hall.png'
DARK = 150                                               # an outline pixel: r + g + b below this


def crop(a):
    """The art without empty rows at the top or bottom; the width stays 256."""
    ys = np.nonzero((a[..., 3] > 0).any(axis=1))[0]
    return a[ys.min():ys.max() + 1].copy()


def measure(a):
    """The lot of a cropped RGBA still: where its outline runs, its rim and slab, its colors, and its slopes."""
    H, W = a.shape[:2]
    op = a[..., 3] > 0
    dark = op & (a[..., :3].sum(-1) < DARK)
    low = np.array([np.nonzero(op[:, x])[0].max() if op[:, x].any() else -1 for x in range(W)])
    cols = np.nonzero((low >= 0) & dark[np.maximum(low, 0), np.arange(W)])[0]   # columns ending in the lot's outline
    xl, xr = int(cols.min()), int(cols.max())
    cx = (xl + xr) / 2
    rim = np.full(W, -1)
    slab = {}
    for x in range(xl + 1, xr):
        y = low[x]
        while y > 0 and dark[y, x]:
            y -= 1
        run = []
        while y > 0 and len(run) < 8:                    # the slab: one or two colors, darker than the rim above it
            c = tuple(a[y, x, :3])
            if run and c != run[0] and sum(c) > sum(run[0]) + 60:
                break
            run.append(c)
            y -= 1
        rim[x] = y
        slab[x] = run
    rim[xl + 1] = rim[xl + 2] = rim[xl + 3]              # at each side corner the rim runs level for three columns
    rim[xr - 1] = rim[xr - 2] = rim[xr - 3]
    side = lambda lo, hi: Counter(c for x in range(lo, hi) for c in slab.get(x, [])).most_common(1)[0][0]
    fit = lambda lo, hi: np.polyfit(np.arange(lo, hi), low[lo:hi], 1)[0]
    m = int(round(cx))
    ink = Counter(tuple(a[low[x], x, :3]) for x in cols).most_common(1)[0][0]
    rims = Counter(tuple(a[rim[x], x, :3]) for x in range(xl + 3, xr - 2) if rim[x] > 0).most_common(1)[0][0]
    return {'H': H, 'xl': xl, 'xr': xr, 'cx': cx, 'low': low, 'rim': rim,
            'slope': (float(fit(xl + 6, m - 6)), float(-fit(m + 6, xr - 6))),
            'slab': (side(xl + 3, m - 2), side(m + 2, xr - 2)), 'ink': ink, 'rimc': rims}


def back_edge(g):
    """The back edges of the surface, per column: the surface is as deep as the column is far from the nearer side
    corner, so the back edges mirror the front ones."""
    xl, xr, rim = g['xl'], g['xr'], g['rim']
    return {x: min(rim[x], rim[x] + 1 - int(min(x - xl - 0.5, xr - 0.5 - x))) for x in range(xl + 1, xr)}


def corner(g):
    """The row of the side corners: the plot's center row, the same for any plot size."""
    return g['rim'][g['xl'] + 1]


def same_plot(g, r):
    """True when the lot's outline runs exactly where the reference's does, counted from the bottom row."""
    if (g['xl'], g['xr']) != (r['xl'], r['xr']):
        return False
    return all(g['H'] - g['low'][x] == r['H'] - r['low'][x] for x in range(r['xl'], r['xr'] + 1))


def ground_colors(a, g):
    """The colors of the lot's ground near its edges: paving, joints, lawn. Not its rim, slab or outline, and not what
    stands near the back edge, such as shrubs: there only the two rows right under a bare back outline count."""
    back = back_edge(g)
    seen = Counter()
    for x in range(g['xl'] + 3, g['xr'] - 2):
        for y in range(g['rim'][x] - 7, g['rim'][x]):    # the band along the front edges
            seen[tuple(a[y, x, :3])] += 1
        top = np.nonzero(a[:, x, 3] > 0)[0].min()
        if abs(top - (back[x] - 1)) <= 1:
            for y in range(top + 1, top + 3):
                seen[tuple(a[y, x, :3])] += 1
    drop = {g['ink'], g['rimc'], *g['slab']}
    return {c for c, n in seen.items() if n >= 3 and c not in drop and sum(c) >= DARK}


def refit(a, g, r):
    """The original laid on the reference plot, which is drawn in the lot's own colors. The two lots' centers line up,
    so the building keeps its place on the plot."""
    shift = int(corner(r) - corner(g))                # an original row y lands on reference row y + shift
    top = min(0, shift)
    H = max(r['H'], g['H'] + shift) - top
    oy, ry = shift - top, -top
    dx = int(round(r['cx'] - g['cx']))
    out = np.zeros((H, 256, 4), int)
    src = np.zeros_like(out)
    for x in range(256):
        if 0 <= x - dx < 256:
            src[oy:oy + g['H'], x] = a[:, x - dx]
    G = ground_colors(a, g)
    rb, gb = back_edge(r), back_edge(g)
    is_ground = np.zeros(src.shape[:2], bool)
    for c in G:
        is_ground |= (src[..., 3] > 0) & np.all(src[..., :3] == c, axis=-1)
    on_lot = np.zeros_like(is_ground)                    # ground lies on the original's surface, never above it
    for sx in range(g['xl'] + 1, g['xr']):
        if 0 <= sx + dx < 256:
            on_lot[gb[sx] + oy:g['rim'][sx] + oy + 1, sx + dx] = True
    is_ground &= on_lot
    seed = np.zeros_like(is_ground)                      # and it is reached from the open ground along the front
    for sx in range(g['xl'] + 3, g['xr'] - 2):
        if 0 <= sx + dx < 256:
            seed[g['rim'][sx] + oy - 3:g['rim'][sx] + oy, sx + dx] = True
    reach = seed & is_ground
    while True:
        grow = reach.copy()
        grow[1:] |= reach[:-1]; grow[:-1] |= reach[1:]; grow[:, 1:] |= reach[:, :-1]; grow[:, :-1] |= reach[:, 1:]
        grow &= is_ground
        if (grow == reach).all():
            break
        reach = grow
    is_ground = reach
    # the reference plot: surface, back outline, rim, slab, front outline, and the two corner columns
    pave = Counter(tuple(c) for c in src[is_ground][:, :3]).most_common(1)[0][0]
    surf = np.zeros(src.shape[:2], bool)
    plot = np.zeros_like(out)
    for x in range(r['xl'], r['xr'] + 1):
        lo = r['low'][x] + ry
        if x in (r['xl'], r['xr']):
            plot[r['rim'][x + (1 if x == r['xl'] else -1)] + ry - 1: lo + 1, x] = g['ink'] + (255,)
            continue
        rm, bk = r['rim'][x] + ry, rb[x] + ry
        plot[bk:rm, x] = pave + (255,)
        surf[bk:rm, x] = True
        plot[bk - 1, x] = g['ink'] + (255,)
        plot[rm, x] = g['rimc'] + (255,)
        plot[rm + 1:lo, x] = g['slab'][0 if x < r['cx'] else 1] + (255,)
        plot[lo, x] = g['ink'] + (255,)
    # what is kept of the original: everything above its rim, except its back outline and corners, its ground outside
    # the new surface, and anything over the new rim, slab or outline
    keep = src[..., 3] > 0
    for x in range(256):
        sx = x - dx
        if not (g['xl'] <= sx <= g['xr']):
            continue
        if sx in (g['xl'], g['xr']):
            keep[:, x] &= ~(src[:, x, :3].sum(-1) < DARK)
            continue
        keep[g['rim'][sx] + oy:, x] = False
        t = np.nonzero(src[:, x, 3] > 0)[0].min()
        bo = gb[sx] - 1 + oy
        if abs(t - bo) <= 1:                             # its back outline, where nothing stands on it
            keep[t:bo + 2, x] &= ~(src[t:bo + 2, x, :3].sum(-1) < DARK)
    keep &= ~(is_ground & ~surf)
    low_band = np.arange(H)[:, None] >= corner(r) + ry - 8
    outside = np.zeros((1, 256), bool)
    outside[0, :r['xl'] + 1] = outside[0, r['xr']:] = True
    keep &= ~(outside & low_band)                        # nothing of the original's corners beyond the new ones
    for x in range(r['xl'] + 1, r['xr']):
        keep[r['rim'][x] + ry:, x] = False
    out[plot[..., 3] > 0] = plot[plot[..., 3] > 0]
    out[keep] = src[keep]
    # the new surface beyond the original's ground, carried out from the original: each new pixel takes the pixel
    # mirrored across the original's edge, along the tile joints, so joint lines run on and lawn texture does not streak
    ground_kept = keep & is_ground
    filled = 0
    for y, x in zip(*np.nonzero(surf & ~keep)):
        front = y > corner(r) + ry
        sx, sy = ((2, -1) if x < r['cx'] else (-2, -1)) if front else ((2, 1) if x < r['cx'] else (-2, 1))
        hit = None
        for k in range(1, 15):
            yy, xx = y + k * sy, x + k * sx
            if not (0 <= yy < H and 0 <= xx < 256):
                break
            if ground_kept[yy, xx]:
                hit = k
                break
        if hit is None:
            continue
        my, mx = y + (2 * hit - 1) * sy, x + (2 * hit - 1) * sx
        if 0 <= my < H and 0 <= mx < 256 and ground_kept[my, mx]:
            out[y, x] = src[my, mx]
        else:
            out[y, x] = src[y + hit * sy, x + hit * sx]
        filled += 1
    return out, filled


def fit(a, ref=REF):
    """The still with its lot on the reference plot, and a line saying what was done."""
    a = crop(np.asarray(a).astype(int))
    r = measure(crop(np.array(Image.open(ref).convert('RGBA')).astype(int)))
    g = measure(a)
    if same_plot(g, r):
        return a.astype(np.uint8), 'the lot is already the plot, exactly: kept as drawn'
    sl, sr = g['slope']
    if abs(sl - 0.5) > 0.03 or abs(sr - 0.5) > 0.03:
        raise ValueError(f'the lot is not 2:1 (front edges slope {sl:.2f} and {sr:.2f}); redraw the lot instead')
    out, filled = refit(a, g, r)
    return crop(out).astype(np.uint8), (f'lot refit: outline x {g["xl"]} to {g["xr"]} became {r["xl"]} to {r["xr"]}, '
                                        f'{filled} px of ground carried out to the new edges')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--ref', default=str(REF))
    o = ap.parse_args()
    try:
        img, note = fit(Image.open(o.src).convert('RGBA'), o.ref)
    except ValueError as e:
        sys.exit(str(e))
    Image.fromarray(img, 'RGBA').save(o.out)
    print(note)
