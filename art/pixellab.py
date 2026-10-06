"""Sends local images to PixelLab's v2 API, which the PixelLab MCP cannot read from disk, and fetches the results.
The token comes from the PIXELLAB_SECRET environment variable and is never written anywhere. Downloads go to
art/out/pixellab/, which git and tools/pack.py leave out. Only the standard library is needed.

  python art/pixellab.py balance
  python art/pixellab.py pro "prompt" --style src/buildings/city-hall.png [--size 256x256] [--name NAME]
  python art/pixellab.py job JOB_ID [--name NAME]          wait for a job and download its images

pro is the recipe for building stills and park lots (the knowledge file, section 4, PixelLab workflow): Pro at the
given size, with a local image of the city's own art as its style reference."""
import argparse, base64, json, os, pathlib, re, struct, sys, time, urllib.error, urllib.request
NC = pathlib.Path(__file__).resolve().parents[1]        # the source folder, wherever it is unpacked
API = 'https://api.pixellab.ai/v2'
OUT = NC / 'art' / 'out' / 'pixellab'
USAGE = "Match this city art's palette, outline, shading, scale and level of detail, so the new art belongs to the same city."


def token():
    t = os.environ.get('PIXELLAB_SECRET', '').strip()
    if not t:
        sys.exit('PIXELLAB_SECRET is not set')
    return t


def request(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {path}: HTTP {e.code} {e.read().decode(errors="replace")[:600]}')


def image(path):
    p = pathlib.Path(path)
    return {'type': 'base64', 'base64': base64.b64encode(p.read_bytes()).decode(), 'format': p.suffix.lstrip('.').lower()}


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        sys.exit(f'{path} is not a PNG')
    return struct.unpack('>II', head[16:24])


def pro_body(prompt, style, size, seed=None, usage=USAGE):
    w, h = (int(v) for v in size.lower().split('x'))
    sw, sh = png_size(style)
    body = {'description': prompt, 'image_size': {'width': w, 'height': h}, 'no_background': True,
            'style_image': {'image': image(style), 'size': {'width': sw, 'height': sh}, 'usage_description': usage}}
    if seed is not None:
        body['seed'] = seed
    return body


def balance():
    b = request('GET', '/balance')
    s = b.get('subscription', {})
    print(f"generations: {s.get('generations')} of {s.get('total')} left ({s.get('status')}, {s.get('plan')}); "
          f"credits: ${b.get('credits', {}).get('usd')}")


def strip(o):
    """The job's JSON without its image data, kept beside the frames."""
    if isinstance(o, dict):
        return {k: ('<%d chars>' % len(v) if k == 'base64' and isinstance(v, str) else strip(v)) for k, v in o.items()}
    return [strip(v) for v in o] if isinstance(o, list) else o


def save_images(job, folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'job.json').write_text(json.dumps(strip(job), indent=1), encoding='utf-8')
    lr = job.get('last_response') or {}
    imgs = lr.get('images') or ([lr['image']] if lr.get('image') else [])       # some jobs bring a list, some one
    for i, im in enumerate(imgs):
        if isinstance(im, str):
            im = {'url': im} if im.startswith('http') else {'base64': im}
        if im.get('base64'):
            raw = base64.b64decode(re.sub(r'^data:[^,]*,', '', im['base64']))
        elif im.get('url'):
            with urllib.request.urlopen(im['url'], timeout=120) as r:
                raw = r.read()
        else:
            print('frame', i, 'has no data:', list(im))
            continue
        (folder / f'frame_{i:02d}.png').write_bytes(raw)
    print(f'{len(imgs)} images in {folder}')


def wait(job_id, name):
    t0 = time.time()
    while True:
        job = request('GET', f'/background-jobs/{job_id}')
        st = job.get('status')
        if st != 'processing':
            break
        lr = job.get('last_response') or {}
        q = f", queue {lr['queue_position']}" if lr.get('queue_position') is not None else ''
        print(f'  {int(time.time() - t0)} s: processing{q}', flush=True)
        time.sleep(10)
    print('job', job_id, st, 'usage:', job.get('usage'))
    if st != 'completed':
        sys.exit(json.dumps(strip(job))[:1500])
    save_images(job, OUT / (name or job_id[:8]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('balance')
    p = sub.add_parser('pro', help='Pro with a local style reference: building stills and park lots')
    p.add_argument('prompt'); p.add_argument('--style', required=True, help='a PNG of the city\'s own art, at most the canvas size')
    p.add_argument('--size', default='256x256', help='WIDTHxHEIGHT: 256x256 for a building, 256x128 for a park lot')
    p.add_argument('--seed', type=int); p.add_argument('--name')
    j = sub.add_parser('job'); j.add_argument('job_id'); j.add_argument('--name')
    args = ap.parse_args()

    if args.cmd == 'balance':
        balance()
    elif args.cmd == 'job':
        wait(args.job_id, args.name)
    else:
        r = request('POST', '/generate-image-v2', pro_body(args.prompt, args.style, args.size, args.seed))
        print(json.dumps(strip(r)))
        wait(r['background_job_id'], args.name)


if __name__ == '__main__':
    main()
