"""The installed app's icons, drawn from the city's own art.

python art/app/icons.py            renders the three options shown on 24 October 2026 into art/out/app/, each as the
                                   plain icon (512, rounded square with see-through corners), the maskable icon (512,
                                   full bleed, for Android), and a sheet showing them at every size the operating
                                   systems use, on light and dark
python art/app/icons.py --install  also writes the one picked, C, the dome, into src/app/: icon-512.png and
                                   icon-192.png (plain), icon-maskable-512.png, and icon-180.png for an iPhone's home
                                   screen, which rounds the corners itself
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art' / 'out' / 'app'
APP = ROOT / 'src' / 'app'
PICKED = 'c-dome'          # Abdurrahman's pick, 24 October 2026
HALL = ROOT / 'src' / 'buildings' / 'city-hall.png'

INK = (43, 37, 66)
PINK = (238, 76, 147)
WHITE = (255, 255, 255)
LILAC = (224, 216, 251)
HAZE = (220, 229, 245)
PANEL = (245, 242, 250)
BLUSH = (251, 211, 227)
NIGHT = (58, 45, 96)

# the side bar's logo, `brand` in src/js/30-pixel.js: # ink, + the accent, o white
BRAND = ['.......#........', '......###.......', '......#+#.......', '......#o#.......', '......#+#.......',
         '..###.#o#.####..', '..#+#.#+#.#++#..', '..#o#.#o#.#oo#..', '..#+#.#+#.#++#..', '..#o#.#o#.#oo#..',
         '..#+#.#+#.#++#..', '################']

S = 512
RADIUS = 104      # the wizard's icon rounds its corners about this much


def rounded(bg, size=S, radius=RADIUS):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    mask = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius * 4, fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    im.paste(Image.new('RGBA', (size, size), bg + (255,)), (0, 0), mask)
    return im


def full(bg, size=S):
    return Image.new('RGBA', (size, size), bg + (255,))


def paste_center(base, art, dy=0):
    x = (base.width - art.width) // 2
    y = (base.height - art.height) // 2 + dy
    base.alpha_composite(art, (x, y))
    return base


def scaled(art, k):
    return art.resize((art.width * k, art.height * k), Image.NEAREST)


def brand_art():
    w, h = len(BRAND[0]), len(BRAND)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, row in enumerate(BRAND):
        for x, ch in enumerate(row):
            if ch != '.':
                im.putpixel((x, y), {'#': INK, '+': PINK, 'o': WHITE}[ch] + (255,))
    return im


def hall_art():
    im = Image.open(HALL).convert('RGBA')
    return im.crop(im.getbbox())


def dome_art():
    """The city hall's glass dome with the tiny city in it, cut at the foot of its pink rim."""
    im = Image.open(HALL).convert('RGBA')
    dome = im.crop((86, 0, 170, 80))
    px = dome.load()
    # each column keeps the rim's own dark outline under its pink band and drops the drum below it
    for x in range(dome.width):
        pink = False
        for y in range(dome.height):
            r, g, b, a = px[x, y]
            if not a:
                continue
            if pink and r + g + b < 30:
                for y2 in range(y + 1, dome.height):
                    px[x, y2] = (0, 0, 0, 0)
                break
            if r > 150 and g < 210 and b < 220 and r > g + 25:
                pink = True
    # only the dome itself: the piece joined to its middle, so bits of the wings below it go
    keep, todo = set(), [(dome.width // 2, 30)]
    while todo:
        x, y = todo.pop()
        if (x, y) in keep or not (0 <= x < dome.width and 0 <= y < dome.height) or not px[x, y][3]:
            continue
        keep.add((x, y))
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(dome.height):
        for x in range(dome.width):
            if (x, y) not in keep or (x == 0 and y >= 47):      # the drum's lip, left of the rim
                px[x, y] = (0, 0, 0, 0)
    # the rim's ends lost their outline where the drum was cut away: close them in the hall's own outline color
    OUTLINE = (2, 1, 4, 255)
    dark = lambda p: p[3] and sum(p[:3]) < 30
    edge = [(x, y) for y in range(40, dome.height) for x in range(dome.width) if not px[x, y][3]
            and any(0 <= x + dx < dome.width and 0 <= y + dy < dome.height and px[x + dx, y + dy][3] and not dark(px[x + dx, y + dy])
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        px[x, y] = OUTLINE
    return dome.crop(dome.getbbox())


OPTIONS = {
    # A: the whole city hall on its plot, the city's standard building
    'a-city-hall': lambda make, bg: paste_center(make(bg), scaled(hall_art(), 2), dy=4),
    # B: the side bar's logo, the city's skyline mark
    'b-skyline': lambda make, bg: paste_center(make(bg), scaled(brand_art(), 22), dy=8),
    # C: the dome with the tiny city inside
    'c-dome': lambda make, bg: paste_center(make(bg), scaled(dome_art(), 4), dy=0),
}
BACKGROUNDS = {'a-city-hall': HAZE, 'b-skyline': BLUSH, 'c-dome': NIGHT}
# the maskable icon keeps its art inside the middle 80% circle, so the art shrinks a step
MASK_SCALE = {'a-city-hall': 2, 'b-skyline': 20, 'c-dome': 4}


def maskable(key):
    bg = BACKGROUNDS[key]
    base = full(bg)
    if key == 'a-city-hall':
        art = hall_art()
    elif key == 'b-skyline':
        art = brand_art()
    else:
        art = dome_art()
    return paste_center(base, scaled(art, MASK_SCALE[key]), dy=4)


def sheet(icons):
    sizes = [192, 96, 64, 48, 32, 16]
    pad = 24
    col = 812
    out = Image.new('RGBA', (len(icons) * col + pad, 1180), (236, 232, 244, 255))
    d = ImageDraw.Draw(out)
    for i, (key, (icon, mask)) in enumerate(icons.items()):
        x0 = pad + i * col
        d.text((x0, 6), key, fill=INK + (255,))
        out.alpha_composite(icon, (x0, 24))
        # the maskable icon, cut to a circle as Android may
        m = mask.resize((256, 256), Image.LANCZOS)
        circ = Image.new('L', (256 * 4, 256 * 4), 0)
        ImageDraw.Draw(circ).ellipse((0, 0, 256 * 4 - 1, 256 * 4 - 1), fill=255)
        circ = circ.resize((256, 256), Image.LANCZOS)
        cm = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        cm.paste(m, (0, 0), circ)
        out.alpha_composite(cm, (x0 + 512 + 16, 24))
        d.text((x0 + 512 + 16, 284), 'maskable, as a circle', fill=INK + (255,))
        # each size on light and on dark
        for row, bgc in enumerate([(243, 243, 243), (32, 32, 32)]):
            y = 560 + row * 300
            d.rectangle((x0, y, x0 + 736, y + 280), fill=bgc + (255,))
            x = x0 + 12
            for s in sizes:
                im = icon.resize((s, s), Image.LANCZOS)
                out.alpha_composite(im, (x, y + 12 + (192 - s)))
                x += s + 14
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icons = {}
    for key, draw in OPTIONS.items():
        icon = draw(rounded, BACKGROUNDS[key])
        mask = maskable(key)
        icon.save(OUT / f'{key}-512.png')
        mask.save(OUT / f'{key}-maskable-512.png')
        icons[key] = (icon, mask)
    sheet(icons).save(OUT / 'icons-sheet.png')
    print('wrote', OUT)
    if '--install' in sys.argv:
        icon, mask = icons[PICKED]
        APP.mkdir(parents=True, exist_ok=True)
        # shrunk smooth, as the tool shrinks art; every size is drawn from the 512 so they match
        for name, im in (('icon-512.png', icon), ('icon-192.png', icon.resize((192, 192), Image.LANCZOS)),
                         ('icon-maskable-512.png', mask), ('icon-180.png', mask.resize((180, 180), Image.LANCZOS).convert('RGB'))):
            im.save(APP / name, optimize=True)
        print('installed', PICKED, 'into', APP)


if __name__ == '__main__':
    main()
