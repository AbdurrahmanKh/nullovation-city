"""Slims the building and lot animations in src/buildings with gifsicle -O3, keeping a file only if the tool's own
decoder reproduces every frame of the original exactly and it comes out smaller. Run it after drawing a
building, before build.py. The originals stay in art/unslimmed, which git leaves out. Needs gifsicle and node on the PATH."""
import json, os, pathlib, shutil, subprocess, tempfile, numpy as np
from PIL import Image, ImageSequence
NC = pathlib.Path(__file__).resolve().parents[1]        # the source folder, wherever it is unpacked
OUT, KEEP = str(NC / 'src' / 'buildings'), str(NC / 'art' / 'unslimmed')
TMP = pathlib.Path(tempfile.gettempdir())
DECODER = (NC / 'src' / 'js' / '35-gif.js').as_posix()
os.makedirs(KEEP, exist_ok=True)
vis = lambda a: np.where(a[..., 3:4] > 0, a, 0)
for nm in sorted(f for f in os.listdir(OUT) if f.endswith('.gif')):
    src = os.path.join(OUT, nm)
    if not os.path.exists(os.path.join(KEEP, nm)): shutil.copy(src, os.path.join(KEEP, nm))
    orig = os.path.join(KEEP, nm)
    tmp, dec = str(TMP / '_slim.gif'), str(TMP / '_d.bin')
    subprocess.run(['gifsicle', '-O3', '--no-comments', '--no-names', orig, '-o', tmp], check=True)
    want = np.stack([np.array(f.convert('RGBA')) for f in ImageSequence.Iterator(Image.open(orig))])
    js = f"""const fs = require('fs'); const {{ decodeGif }} = require({json.dumps(DECODER)});
const g = decodeGif(new Uint8Array(fs.readFileSync({json.dumps(tmp)})));
fs.writeFileSync({json.dumps(dec)}, Buffer.concat(g.frames.map(f => Buffer.from(f.rgba.buffer)))); console.log(g.frames.length);"""
    n = int(subprocess.run(['node', '-e', js], capture_output=True, text=True).stdout.strip())
    got = np.frombuffer(open(dec, 'rb').read(), np.uint8).reshape(n, *want.shape[1:])
    if got.shape == want.shape and not np.any(vis(got) != vis(want)) and os.path.getsize(tmp) < os.path.getsize(orig):
        shutil.copy(tmp, src); print(f'{nm}: {os.path.getsize(orig) // 1024} KB -> {os.path.getsize(tmp) // 1024} KB, exact')
    else:
        shutil.copy(orig, src); print(f'{nm}: left as it was')
