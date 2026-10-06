"""The street props, finished from their PixelLab stills: a bus stop, a vending machine, a holo billboard and a bin.
Each has a front (Pixflux, isometric, the city colors forced) and a back (a Pro Flash rotation of the front, picked
by eye); mirrored, the two serve all four sides of a block (the knowledge file, section 4, PixelLab workflow).

The cleanup, the same for every image: snap each pixel to the city's 32 colors, read from src/js/30-pixel.js;
clear the known flaws and any stray speck; give every edge that lacks one a 1 px dark outline; and set the back on
the front's canvas, standing on the same spot. Nothing here goes into the tool.
Reads art/sources/props/<prop>-front.png and -back.png; writes art/out/props/<prop>-front.png and -back.png,
and props-sheet.png to compare them with the stills."""
import pathlib, re
import numpy as np
from PIL import Image, ImageDraw, ImageOps

NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
SRC = NC / 'art' / 'sources' / 'props'
OUT = NC / 'art' / 'out' / 'props'
PROPS = ['busstop', 'vending', 'billboard', 'bin']
CANVAS = {'busstop': (64, 64), 'billboard': (64, 64), 'vending': (32, 48), 'bin': (32, 32)}   # art size, shown at half

js = (NC / 'src' / 'js' / '30-pixel.js').read_text(encoding='utf-8')
PALETTE = {n: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
           for n, h in re.findall(r"\['([^']+)', '(#[0-9A-Fa-f]{6})'\]", js.split('const CITY_PALETTE')[1].split('];')[0])}
assert len(PALETTE) == 32, len(PALETTE)
PAL = np.array(list(PALETTE.values()), int)
INK, OUTLINE = PALETTE['Ink'], PALETTE['Outline']
DARK = {INK, OUTLINE, PALETTE['Steel']}                 # colors that already read as an outline


def snap(a):
    m = a[..., 3] > 0
    a[..., 3] = np.where(m, 255, 0)
    px = a[m][:, :3][:, None, :]                        # the nearest city color by the redmean distance, which
    r = (px[..., 0] + PAL[None, :, 0]) / 2              # keeps a deep magenta pink rather than wood brown
    d = px - PAL[None]
    a[m, :3] = PAL[np.argmin((2 + r / 256) * d[..., 0] ** 2 + 4 * d[..., 1] ** 2 + (2 + (255 - r) / 256) * d[..., 2] ** 2, axis=1)]
    a[~m] = 0
    return a


def is_col(a, name):
    return np.all(a[..., :3] == PALETTE[name], axis=-1) & (a[..., 3] > 0)


def dark(a):
    return np.any([is_col(a, n) for n in ('Ink', 'Outline', 'Steel')], axis=0)


def box(a, x0, x1, y0, y1):
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    return (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)


OUTLINE_ALL = {'billboard'}                             # Pixflux left the billboard with no outline at all

# The known flaws, in each still's own pixels: what to clear.
FLAWS = {
    # the bench seen through the glass came out as a pale ghost below the panel, with no outline
    ('busstop', 'back'): lambda a: box(a, 27, 47, 46, 56) & ~dark(a),
    # a teal ground patch at the machine's foot, carried into its rotation
    ('vending', 'front'): lambda a: box(a, 0, 31, 37, 47) & (is_col(a, 'Deep teal') | is_col(a, 'Sky')),
    ('vending', 'back'): lambda a: box(a, 0, 47, 32, 47) & is_col(a, 'Deep teal'),
}


def components(m):
    """8-connected pieces of a mask, as lists of (y, x)."""
    seen, out = np.zeros_like(m), []
    for y, x in zip(*np.nonzero(m)):
        if seen[y, x]:
            continue
        stack, piece = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop(); piece.append((cy, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] and m[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; stack.append((ny, nx))
        out.append(piece)
    return out


def clean(prop, side):
    a = snap(np.array(Image.open(SRC / f'{prop}-{side}.png').convert('RGBA')).astype(int))
    before = a[..., 3] > 0
    flaw = FLAWS.get((prop, side))
    if flaw is not None:
        a[flaw(a)] = 0
    pieces = components(a[..., 3] > 0)                  # stray specks: anything but the prop's own body
    biggest = max(len(p) for p in pieces)
    for p in pieces:
        if len(p) < max(8, biggest // 20):
            for y, x in p:
                a[y, x] = 0
    # a dark outline on light edges: all round the billboard, elsewhere only where a flaw was cleared
    op = a[..., 3] > 0
    lightedge = op & ~dark(a)
    n = np.zeros_like(op)
    n[1:, :] |= lightedge[:-1, :]; n[:-1, :] |= lightedge[1:, :]; n[:, 1:] |= lightedge[:, :-1]; n[:, :-1] |= lightedge[:, 1:]
    where = n & ~op if prop in OUTLINE_ALL else n & ~op & before
    a[where] = INK + (255,)
    return a.astype(np.uint8)


def place(a, size, foot):
    """The art on a canvas of the given size, its bounding box's bottom center on the foot point."""
    im = Image.fromarray(a, 'RGBA')
    im = im.crop(im.getbbox())
    cv = Image.new('RGBA', size, (0, 0, 0, 0))
    x = int(round(foot[0] - im.width / 2)); y = foot[1] - im.height
    assert 0 <= x and x + im.width <= size[0] and 0 <= y, (size, foot, im.size)
    cv.alpha_composite(im, (x, y))
    return cv


def foot_of(a):
    b = Image.fromarray(a, 'RGBA').getbbox()
    return ((b[0] + b[2]) / 2, b[3])


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    done = {}
    for prop in PROPS:
        front, back = clean(prop, 'front'), clean(prop, 'back')
        size = CANVAS[prop]
        assert front.shape[1::-1] == size, (prop, front.shape)
        foot = foot_of(front)
        f_im, b_im = Image.fromarray(front, 'RGBA'), place(back, size, foot)
        f_im.save(OUT / f'{prop}-front.png'); b_im.save(OUT / f'{prop}-back.png')
        done[prop] = (f_im, b_im)
        ncol = lambda im: len({tuple(p[:3]) for p in np.array(im).reshape(-1, 4) if p[3]})
        print(f'{prop}: {size[0]} x {size[1]}, front {ncol(f_im)} colors, back {ncol(b_im)} colors')

    # the sheet: per prop, the stills, then the finished four sides (front, front mirrored, back, back mirrored)
    K, CELL, PAD = 4, 64 * 4 + 8, 8
    heads = ['front still', 'back still', 'front', 'front, mirrored', 'back', 'back, mirrored']
    sheet = Image.new('RGBA', (PAD + 120 + len(heads) * CELL, 22 + 2 * len(PROPS) * (CELL + 4)), (41, 36, 64, 255))
    d = ImageDraw.Draw(sheet)
    for i, h in enumerate(heads):
        d.text((PAD + 120 + i * CELL, 6), h, fill=(225, 218, 233, 255))
    y = 22
    for bg in ((41, 36, 64, 255), (225, 218, 233, 255)):
        for prop in PROPS:
            f_im, b_im = done[prop]
            raw = [Image.open(SRC / f'{prop}-{s}.png').convert('RGBA') for s in ('front', 'back')]
            cells = raw + [f_im, ImageOps.mirror(f_im), b_im, ImageOps.mirror(b_im)]
            h = max(c.height for c in cells) * K + 6
            d.rectangle([PAD + 120, y, sheet.width - PAD, y + h], fill=bg)
            d.text((PAD, y + 4), prop, fill=(225, 218, 233, 255))
            for i, c in enumerate(cells):
                big = c.resize((c.width * K, c.height * K), Image.NEAREST)
                sheet.alpha_composite(big, (PAD + 120 + i * CELL, y + 3))
            y += h + 4
    sheet = sheet.crop((0, 0, sheet.width, y + 4))
    sheet.save(OUT / 'props-sheet.png')
    print('sheet:', OUT / 'props-sheet.png')
