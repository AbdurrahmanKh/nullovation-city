"""Renders the original 128 px designs (generics.py, drawn with kit.py) into art/canon/out, with a contact
sheet, to compare against the 256 px buildings. It never writes into src/.

    python art/canon/render.py [building ids]"""
import json, os, sys
import numpy as np
from PIL import Image
from kit import save, RGB, NAME
from generics import BUILDINGS, N
import pathlib
NC = pathlib.Path(__file__).resolve().parents[2]        # the source folder, wherever it is unpacked
OUT = str(NC / 'art/canon/out')
os.makedirs(OUT, exist_ok=True)
only = sys.argv[1:] 
meta = []
for bid, name, foot, fn, delays in BUILDINGS:
    if only and bid not in only: continue
    frames = [fn(f) for f in range(N)]
    info = save(bid, frames, delays, OUT)
    info.update(id=bid, title=name, footprint=foot)
    meta.append(info)
    print(f"{bid:16s} {info['w']}x{info['h']:<4d} {info['colors']} colors, {Image.open(OUT + '/' + bid + '.gif').n_frames} stored frames")
# contact sheet at 3x on the map's ground color, frame 0 and frame 4
cells = []
for m in meta:
    for fi in (0, 4):
        im = Image.open(f"{OUT}/{m['id']}.gif"); im.seek(min(fi, im.n_frames - 1))
        fr = im.convert('RGBA'); fr = fr.resize((fr.width * 3, fr.height * 3), Image.NEAREST)
        cells.append((m['id'], fi, fr))
cw = 128 * 3 + 20; ch = max(c[2].height for c in cells) + 20
cols = 4
rows = (len(cells) + cols - 1) // cols
sheet = Image.new('RGBA', (cw * cols, ch * rows), (226, 220, 234, 255))
for i, (bid, fi, fr) in enumerate(cells):
    x, y = (i % cols) * cw + 10, (i // cols) * ch + (ch - fr.height) - 10
    sheet.alpha_composite(fr, (x, y))
sheet.save(f'{OUT}/sheet.png')
json.dump(meta, open(f'{OUT}/meta.json', 'w'), indent=1)
print('sheet', sheet.size)
