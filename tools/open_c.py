"""Open the mouth of C and c in the city's copy of Pixelify Sans (General UX, Round 1, X2).

Pixelify Sans closes C and c to a single pixel, so at the sizes the city uses they read as O and o
(Nullovation Oity, Olaude). This shortens the arms of both letters, keeping every weight of the variable
font: in both glyphs points 9 and 10 end the arm under the top bar and 15 and 16 the arm over the bottom bar,
and 11 and 14 are the bowl's inner corners. At weight 400 the gap goes from 80 units to 230 for C and 152 for c.

The upstream file, as fontsource ships it, is kept in tools/fonts/. The SIL Open Font License allows a
Modified Version, and Pixelify Sans names no Reserved Font Name; its name table says it is changed.

Needs fontTools and brotli (pip install fonttools brotli), only to run this once.
Usage: python tools/open_c.py            (writes src/fonts/pixelify-sans/pixelify-sans-latin-wght-normal.woff2)
"""
import pathlib
import sys
from fontTools.ttLib import TTFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'tools' / 'fonts' / 'pixelify-sans-latin-wght-normal.woff2'
OUT = ROOT / 'src' / 'fonts' / 'pixelify-sans' / 'pixelify-sans-latin-wght-normal.woff2'
KEEP = {'C': 0.24, 'c': 0.21}       # how much of the bowl's inner height each arm keeps


def main():
    f = TTFont(str(SRC))
    glyf, cmap = f['glyf'], f.getBestCmap()
    for ch, keep in KEEP.items():
        c = glyf[cmap[ord(ch)]].coordinates
        if not (len(c) == 20 and c[9][1] == c[10][1] and c[15][1] == c[16][1]):
            sys.exit(f'{ch}: not the outline this script knows; check the upstream file')
        top, bot = c[11][1], c[14][1]
        arm, old = round((top - bot) * keep), c[9][1] - c[15][1]
        for i in (9, 10): c[i] = (c[i][0], top - arm)
        for i in (15, 16): c[i] = (c[i][0], bot + arm)
        print(f'{ch}: the gap at weight 400 goes from {old} to {c[9][1] - c[15][1]} units')
    name = f['name']
    for rec in name.names:
        if rec.nameID == 5:
            name.setName(rec.toUnicode() + '; C and c opened for Nullovation City', 5, rec.platformID, rec.platEncID, rec.langID)
    f.flavor = 'woff2'
    f.save(str(OUT))
    print('wrote', OUT.relative_to(ROOT))


if __name__ == '__main__':
    main()
