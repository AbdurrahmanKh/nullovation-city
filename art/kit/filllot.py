"""Lot fix for a flat park lot that falls a pixel or two short of the plot diamond, or spills a pixel or two past it.
The diamond is the one today's lots cover (art/lots/lots.py): the full width and height of the image, reaching its
first and last columns and its bottom row.
- fill_lot fills every empty pixel inside the diamond from its nearest filled neighbor, until the diamond is full.
- trim_lot clears the ragged strips just outside it, and keeps what rises well past it, such as tree tops.
usage: python filllot.py IN.png OUT.png"""
import sys
import numpy as np
from PIL import Image


def _excess(H, W):
    """How far each pixel lies outside the diamond, in rows (0 or less inside)."""
    yy, xx = np.mgrid[0:H, 0:W]
    t = np.abs(xx + 0.5 - W / 2) / (W / 2) + np.abs(yy + 0.5 - H / 2) / (H / 2)
    return (t - (1 + 2 / W)) * (H / 2)


def fill_lot(a):
    """Fill the diamond of an RGBA array (H, W, 4) in place; returns the number of pixels filled."""
    dia = _excess(*a.shape[:2]) <= 0
    filled = 0
    while True:
        op = a[..., 3] > 0
        todo = dia & ~op
        if not todo.any():
            return filled
        for oy, ox in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src = np.roll(np.roll(a, oy, 0), ox, 1)
            take = todo & (src[..., 3] > 0) & (a[..., 3] == 0)
            a[take] = src[take]
            filled += int(take.sum())


def trim_lot(a, reach=2.5):
    """Clear, in place, every patch of pixels outside the diamond that stays within `reach` rows of it; a patch that
    reaches further, such as a tree top, is kept whole. Returns the number of pixels cleared."""
    ex = _excess(*a.shape[:2])
    out = (a[..., 3] > 0) & (ex > 0)
    seen = np.zeros_like(out)
    cleared = 0
    for y0, x0 in zip(*np.nonzero(out)):
        if seen[y0, x0]:
            continue
        patch, todo = [], [(y0, x0)]
        seen[y0, x0] = True
        while todo:                                     # the patch: outside pixels touching, corners included
            y, x = todo.pop()
            patch.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    v, u = y + dy, x + dx
                    if 0 <= v < out.shape[0] and 0 <= u < out.shape[1] and out[v, u] and not seen[v, u]:
                        seen[v, u] = True
                        todo.append((v, u))
        if max(ex[p] for p in patch) <= reach:
            for p in patch:
                a[p] = 0
            cleared += len(patch)
    return cleared


if __name__ == '__main__':
    a = np.array(Image.open(sys.argv[1]).convert('RGBA'))
    n, m = fill_lot(a), trim_lot(a)
    Image.fromarray(a, 'RGBA').save(sys.argv[2])
    print('filled', n, 'px, cleared', m, 'px; diamond now full')
