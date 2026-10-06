"""Slims the building and lot animations in src/buildings, keeping a result only if the tool's own decoder reproduces
every frame of the original exactly and it comes out smaller than the file already there. Run it after drawing a
building, before build.py. The originals stay in art/unslimmed, which git leaves out.

Two ways are tried, and the smallest exact result wins:
- gifsicle -O3, when gifsicle is on the PATH;
- a delta in Python: the first frame whole, then each frame with the pixels that did not change made see-through, so
  the decoder keeps the previous frame there, each cropped to its changed box. It needs no gifsicle, and is skipped
  for an animation where a pixel turns see-through.
Needs node on the PATH for the decoder check.

  python art/slim_gifs.py                     every GIF in src/buildings
  python art/slim_gifs.py lot-playground.gif  only the files named"""
import json, os, pathlib, shutil, subprocess, sys, tempfile, numpy as np
from PIL import Image, ImageSequence
NC = pathlib.Path(__file__).resolve().parents[1]        # the source folder, wherever it is unpacked
OUT, KEEP = str(NC / 'src' / 'buildings'), str(NC / 'art' / 'unslimmed')
TMP = pathlib.Path(tempfile.gettempdir())
DECODER = (NC / 'src' / 'js' / '35-gif.js').as_posix()
os.makedirs(KEEP, exist_ok=True)
vis = lambda a: np.where(a[..., 3:4] > 0, a, 0)


def frames_of(path):
    return np.stack([np.array(f.convert('RGBA')) for f in ImageSequence.Iterator(Image.open(path))])


def decodes_to(path, want):
    dec = str(TMP / '_slim_d.bin')
    js = f"""const fs = require('fs'); const {{ decodeGif }} = require({json.dumps(DECODER)});
const g = decodeGif(new Uint8Array(fs.readFileSync({json.dumps(str(path))})));
fs.writeFileSync({json.dumps(dec)}, Buffer.concat(g.frames.map(f => Buffer.from(f.rgba.buffer)))); console.log(g.frames.length);"""
    n = int(subprocess.run(['node', '-e', js], capture_output=True, text=True).stdout.strip() or 0)
    if n != len(want):
        return False
    got = np.frombuffer(open(dec, 'rb').read(), np.uint8).reshape(n, *want.shape[1:])
    return not np.any(vis(got) != vis(want))


def by_gifsicle(orig, dst):
    if not shutil.which('gifsicle'):
        return False
    subprocess.run(['gifsicle', '-O3', '--no-comments', '--no-names', orig, '-o', dst], check=True)
    return True


def by_delta(orig, dst, want):
    if np.any((want[1:, ..., 3] == 0) & (want[:-1, ..., 3] > 0)):
        return False                                     # a pixel turns see-through: a delta cannot clear it
    durs = [f.info.get('duration', 200) for f in ImageSequence.Iterator(Image.open(orig))]
    cols = sorted({tuple(p[:3]) for f in want for p in f[f[..., 3] > 0]})
    if len(cols) > 255:
        return False
    idx = {c: i + 1 for i, c in enumerate(cols)}        # 0 is see-through
    pal = [0, 0, 0] + [v for c in cols for v in c]; pal += [0] * (768 - len(pal))
    ims = []
    for k, f in enumerate(want):
        m = f[..., 3] > 0
        if k:
            m &= ~np.all(f == want[k - 1], axis=-1)     # unchanged: see-through, so the previous frame shows
        a = np.zeros(f.shape[:2], np.uint8)
        a[m] = [idx[tuple(c)] for c in f[m, :3]]
        p = Image.fromarray(a, 'P'); p.putpalette(pal); ims.append(p)
    ims[0].save(dst, save_all=True, append_images=ims[1:], duration=durs, loop=0, transparency=0, disposal=1, optimize=False)
    return True


names = sys.argv[1:] or sorted(f for f in os.listdir(OUT) if f.endswith('.gif'))
for nm in names:
    src = os.path.join(OUT, nm)
    if not os.path.exists(os.path.join(KEEP, nm)): shutil.copy(src, os.path.join(KEEP, nm))
    orig = os.path.join(KEEP, nm)
    want = frames_of(orig)
    best, best_size, how = None, os.path.getsize(src), None
    for label, make in (('gifsicle', lambda d: by_gifsicle(orig, d)), ('delta', lambda d: by_delta(orig, d, want))):
        tmp = str(TMP / f'_slim_{label}.gif')
        if make(tmp) and os.path.getsize(tmp) < best_size and decodes_to(tmp, want):
            best, best_size, how = tmp, os.path.getsize(tmp), label
    if best:
        shutil.copy(best, src); print(f'{nm}: {os.path.getsize(orig) // 1024} KB -> {best_size // 1024} KB by {how}, exact')
    else:
        print(f'{nm}: left as it was ({os.path.getsize(src) // 1024} KB)')
