"""Sync, part 1 (0.1.73): every city that syncs keeps the same city through one shared copy in a private GitHub
repository (Quick Sync, S1). A fake GitHub runs here, answering only what the city asks (the repository, the branch's
latest commit with "nothing new", commits, trees, files, writing a commit, moving the branch and refusing a move on an
old version), and two browser contexts are two cities: the PC and the phone. The merge is checked alone, every case;
then Connect and its checks, starting the shared copy, taking it with a backup first, a change in one city showing in
the other, a send on an old version refused, merged and sent again, pictures once by fingerprint, applying in place
with a panel open and waiting while typing, offline and back, the version guard, a token refused, Pause and Disconnect,
a second tab following, and no token anywhere it must not be. The passes never reach the real GitHub."""
import base64, hashlib, http.server, json, re, threading, time, urllib.parse
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY, VERSION, fixture, open_settings, close_settings

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got)[:1500] + ')'))


class FakeGitHub:
    """One repository, me/city-data, as GitHub's Git Data API shows it."""
    def __init__(self):
        self.lock = threading.RLock()
        self.objs, self.ref, self.private, self.down = {}, None, True, False
        self.tokens = {'tok-pc': 'rw', 'tok-phone': 'rw', 'tok-ro': 'ro'}
        self.log, self.lag = [], {}
    def blob(self, data):
        sha = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
        self.objs[sha] = ('blob', data)
        return sha
    def tree(self, entries):
        sha = hashlib.sha1(b'tree ' + json.dumps(sorted(entries.items())).encode()).hexdigest()
        self.objs[sha] = ('tree', dict(entries))
        return sha
    def commit(self, tree, parents, message):
        c = {'tree': tree, 'parents': parents, 'message': message, 'date': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        sha = hashlib.sha1(b'commit ' + json.dumps(c, sort_keys=True).encode() + str(time.time_ns()).encode()).hexdigest()
        self.objs[sha] = ('commit', c)
        return sha
    def readme(self):
        """The repository as GitHub makes it with Add a README ticked."""
        self.ref = self.commit(self.tree({'README.md': self.blob(b'# city-data\n')}), [], 'Initial commit')
    def ancestor(self, a, b):
        todo, seen = [b], set()
        while todo:
            x = todo.pop()
            if x == a: return True
            if x in seen or x not in self.objs: continue
            seen.add(x); todo += self.objs[x][1]['parents']
        return False
    def files(self, sha=None):
        with self.lock:
            t = self.objs[self.objs[sha or self.ref][1]['tree']][1]
            return {p: self.objs[s][1] for p, s in t.items()}
    def json(self, path): return json.loads(self.files()[path].decode('utf-8'))
    def put_files(self, changes, message='by hand'):
        """A commit made straight in the repository, as another city or a hand edit would."""
        with self.lock:
            t = dict(self.objs[self.objs[self.ref][1]['tree']][1])
            for p, data in changes.items():
                if data is None: t.pop(p, None)
                else: t[p] = self.blob(data)
            self.ref = self.commit(self.tree(t), [self.ref], message)
    def count(self, tok, method=None, rest=None, status=None):
        return sum(1 for e in self.log if e['tok'] == tok and (method is None or e['method'] == method)
                   and (rest is None or re.search(rest, e['path'])) and (status is None or e['status'] == status))


gh = FakeGitHub()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Expose-Headers', 'ETag')
    def do_OPTIONS(self):
        self.send_response(204); self.cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type, If-None-Match, Accept')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Max-Age', '600')
        self.end_headers()
    def reply(self, code, data=None, etag=None):
        self.entry['status'] = code
        body = b'' if data is None else json.dumps(data).encode()
        self.send_response(code); self.cors()
        if etag: self.send_header('ETag', etag)
        self.send_header('Cache-Control', 'private, max-age=60, s-maxage=60')
        if code != 304:
            self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if code != 304: self.wfile.write(body)
    def do_GET(self): self.route('GET')
    def do_POST(self): self.route('POST')
    def do_PATCH(self): self.route('PATCH')
    def route(self, method):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        with gh.lock:
            u = urllib.parse.urlparse(self.path)
            tok = (self.headers.get('Authorization') or '').split(' ')[-1]
            self.entry = {'method': method, 'path': u.path, 'tok': tok, 'status': 0, 'body': raw[:4000]}
            gh.log.append(self.entry)
            body = json.loads(raw.decode('utf-8')) if raw else None
            if gh.down: return self.reply(503, {'message': 'Service unavailable'})
            role = gh.tokens.get(tok)
            if not role: return self.reply(401, {'message': 'Bad credentials'})
            m = re.match(r'^/repos/([^/]+)/([^/]+)(/.*)?$', u.path)
            if not m or (m[1], m[2]) != ('me', 'city-data'): return self.reply(404, {'message': 'Not Found'})
            rest = m[3] or ''
            if rest == '' and method == 'GET':
                return self.reply(200, {'full_name': 'me/city-data', 'private': gh.private, 'default_branch': 'main', 'permissions': {'admin': True, 'push': True, 'pull': True}})
            if method != 'GET' and role != 'rw': return self.reply(403, {'message': 'Resource not accessible by personal access token'})
            if gh.ref is None: return self.reply(409, {'message': 'Git Repository is empty.'})
            if rest == '/git/ref/heads/main' and method == 'GET':
                sha = gh.lag.pop(tok, None) or gh.ref                       # a read that lags behind a write, once
                etag = 'W/"' + sha + '"'
                if self.headers.get('If-None-Match') == etag: return self.reply(304, None, etag)
                return self.reply(200, {'ref': 'refs/heads/main', 'object': {'sha': sha, 'type': 'commit'}}, etag)
            g = re.match(r'^/git/(commits|trees|blobs)/([0-9a-f]+)$', rest)
            if g and method == 'GET':
                kind, sha = g[1], g[2]
                o = gh.objs.get(sha)
                if not o: return self.reply(404, {'message': 'Not Found'})
                if kind == 'commits':
                    c = o[1]
                    return self.reply(200, {'sha': sha, 'tree': {'sha': c['tree']}, 'parents': [{'sha': x} for x in c['parents']], 'message': c['message'],
                                            'author': {'date': c['date']}, 'committer': {'date': c['date']}})
                if kind == 'trees':
                    t = o[1]
                    dirs = sorted({p.rsplit('/', 1)[0] for p in t if '/' in p})
                    return self.reply(200, {'sha': sha, 'truncated': False, 'tree': [{'path': d, 'mode': '040000', 'type': 'tree', 'sha': '0' * 40} for d in dirs]
                                            + [{'path': p, 'mode': '100644', 'type': 'blob', 'sha': s, 'size': len(gh.objs[s][1])} for p, s in sorted(t.items())]})
                b64 = base64.b64encode(o[1]).decode()
                return self.reply(200, {'sha': sha, 'size': len(o[1]), 'encoding': 'base64', 'content': '\n'.join(b64[i:i + 60] for i in range(0, len(b64), 60))})
            if rest == '/git/blobs' and method == 'POST':
                data = base64.b64decode(body['content']) if body.get('encoding') == 'base64' else body['content'].encode('utf-8')
                return self.reply(201, {'sha': gh.blob(data)})
            if rest == '/git/trees' and method == 'POST':
                t = dict(gh.objs[body['base_tree']][1]) if body.get('base_tree') else {}
                for e in body['tree']:
                    if 'content' in e: t[e['path']] = gh.blob(e['content'].encode('utf-8'))
                    elif e.get('sha') is None: t.pop(e['path'], None)
                    else: t[e['path']] = e['sha']
                return self.reply(201, {'sha': gh.tree(t)})
            if rest == '/git/commits' and method == 'POST':
                sha = gh.commit(body['tree'], body['parents'], body['message'])
                return self.reply(201, {'sha': sha, 'tree': {'sha': body['tree']}, 'parents': [{'sha': x} for x in body['parents']]})
            if rest == '/git/refs/heads/main' and method == 'PATCH':
                if not body.get('force') and not gh.ancestor(gh.ref, body['sha']): return self.reply(422, {'message': 'Update is not a fast forward'})
                gh.ref = body['sha']
                return self.reply(200, {'ref': 'refs/heads/main', 'object': {'sha': gh.ref, 'type': 'commit'}})
            return self.reply(404, {'message': 'Not Found'})


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
API = 'http://127.0.0.1:%d' % srv.server_address[1]

QUIET = ("try { if (!sessionStorage.getItem('nc-t46')) { sessionStorage.setItem('nc-t46', '1'); localStorage.setItem('nullovation-city:light', 'day'); "
         "localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
data_url = lambda name, mime='image/png': 'data:' + mime + ';base64,' + base64.b64encode(open(fixture(name), 'rb').read()).decode()
sha256 = lambda name: hashlib.sha256(open(fixture(name), 'rb').read()).hexdigest()

# ---------- the merge, alone ----------
MERGE = r"""() => {
  const M = (b, l, r, n) => Sync._test.merge(b, l, r, n);
  const T = (id, text, o = {}) => Object.assign({ id, text, done: false, milestoneId: 'm1' }, o);
  const P = (o = {}) => Object.assign({ id: 'p1', name: 'Garden', plot: { u: 1, v: 1 }, todos: [T('a', 'One'), T('b', 'Two'), T('c', 'Three')],
    milestones: [{ id: 'm1', name: 'First' }], notes: [], links: [], activity: [{ at: 1, text: 'Planted' }], urgency: { system: 'none', days: 1, lastWorked: 5, pickedAt: null },
    updatedAt: 10, createdAt: 1, star: '', pin: '' }, o);
  const F = (p, o = {}) => Object.assign({ world: { nu: 5, nv: 5, ou: 0, ov: 0 }, city: { crowd: 'medium', night: '19:00', day: '06:30' }, leaders: [], order: Object.keys(p), projects: p }, o);
  const c = x => JSON.parse(JSON.stringify(x));
  const base = F({ p1: P() });
  const out = {};
  let l = c(base), r = c(base);
  r.projects.p1.todos[1].text = 'Two, theirs';
  out.remoteOnly = M(base, l, r, true).projects.p1.todos[1].text;
  l = c(base); r = c(base); l.projects.p1.todos[1].text = 'Two, mine';
  out.localOnly = M(base, l, r, false).projects.p1.todos[1].text;
  l = c(base); r = c(base); l.projects.p1.todos[0].text = 'One, mine'; r.projects.p1.todos[2].done = true;
  let m = M(base, l, r, false);
  out.both = [m.projects.p1.todos[0].text, m.projects.p1.todos[2].done];
  l = c(base); r = c(base); l.projects.p1.todos[0].text = 'Mine'; r.projects.p1.todos[0].text = 'Theirs';
  out.clashLocal = M(base, l, r, true).projects.p1.todos[0].text; out.clashRemote = M(base, l, r, false).projects.p1.todos[0].text;
  l = c(base); r = c(base); l.projects.p1.todos[1].text = 'Two, renamed here'; r.projects.p1.todos[1].description = 'Described there';
  m = M(base, l, r, false); out.fields = [m.projects.p1.todos[1].text, m.projects.p1.todos[1].description];
  l = c(base); r = c(base); l.projects.p1.todos[0].notes = [{ id: 'n1', title: 'Mine', text: 'a', at: 1 }]; r.projects.p1.todos[0].notes = [{ id: 'n2', title: 'Theirs', text: 'b', at: 2 }];
  out.taskNotes = M(base, l, r, false).projects.p1.todos[0].notes.map(n => n.id);
  l = c(base); r = c(base); l.projects.p1.todos.splice(1, 0, T('n1', 'New here')); r.projects.p1.todos.push(T('n2', 'New there'));
  out.added = M(base, l, r, false).projects.p1.todos.map(t => t.id);
  l = c(base); r = c(base); r.projects.p1.todos.splice(1, 1);
  out.deleted = M(base, l, r, true).projects.p1.todos.map(t => t.id);
  l = c(base); r = c(base); r.projects.p1.todos.splice(1, 1); l.projects.p1.todos[1].text = 'Two, changed';
  out.deletedChangedNewer = M(base, l, r, true).projects.p1.todos.map(t => t.id);
  out.deletedChangedOlder = M(base, l, r, false).projects.p1.todos.map(t => t.id);
  l = c(base); r = c(base); l.projects.p1.todos.reverse(); r.projects.p1.todos.splice(2, 0, T('n3', 'After two'));
  out.order = M(base, l, r, false).projects.p1.todos.map(t => t.id);
  l = c(base); r = c(base); l.projects.p1.activity.push({ at: 20, text: 'Done: One' }); r.projects.p1.activity.push({ at: 21, text: 'Done: Three' });
  out.activity = M(base, l, r, false).projects.p1.activity.map(e => e.text);
  const b2 = c(base); b2.projects.p1.activity.push({ at: 15, text: 'Added todo: Four' });
  l = c(b2); r = c(b2); l.projects.p1.activity.pop(); r.projects.p1.activity.push({ at: 22, text: 'Wrote a note' });
  out.undone = M(b2, l, r, false).projects.p1.activity.map(e => e.text);
  l = c(base); r = c(base); l.projects.p1.updatedAt = 50; r.projects.p1.updatedAt = 40; l.projects.p1.urgency.lastWorked = 30; r.projects.p1.urgency.lastWorked = 60;
  m = M(base, l, r, false); out.times = [m.projects.p1.updatedAt, m.projects.p1.urgency.lastWorked];
  l = c(base); r = c(base); l.projects.p2 = P({ id: 'p2', name: 'Mine', plot: { u: 0, v: 0 } }); l.order.push('p2'); r.projects.p3 = P({ id: 'p3', name: 'Theirs', plot: { u: 0, v: 0 } }); r.order.push('p3');
  m = M(base, l, r, false); out.projects = m.order;
  l = c(base); r = c(base); delete r.projects.p1; r.order = [];
  out.projectGone = Object.keys(M(base, l, r, true).projects);
  l = c(base); r = c(base); l.city.night = '20:00'; r.city.crowd = 'large';
  m = M(base, l, r, false); out.city = [m.city.night, m.city.crowd];
  l = c(base); r = c(base); l.projects.p1.star = 'a'; r.projects.p2 = P({ id: 'p2', star: 'x', todos: [T('x', 'X')] });
  m = M(base, l, r, true); out.star = Object.values(m.projects).filter(p => p.star).map(p => p.id);
  const lb = c(base); lb.leaders = [{ id: 'L1', name: 'Mira', role: 'Gardener' }];
  l = c(lb); r = c(lb); r.leaders[0].role = 'Head gardener';
  out.leader = M(lb, l, r, true).leaders[0].role;
  out.firstTake = Object.keys(M(null, F({}), base, false).projects);
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    def city(name):
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
        ctx.add_init_script(TEST_CITY); ctx.add_init_script(QUIET)
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(name + ': ' + str(e)))
        pg.on('console', lambda m: errors.append(name + ': ' + m.text) if m.type in ('error', 'warning') and 'Failed to load resource' not in m.text else None)
        pg.goto(FILE); pg.wait_for_function("() => typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
        pg.evaluate("() => Sync._test.fast()"); pg.evaluate(f"() => Sync._test.api('{API}')")
        return ctx, pg
    ctxA, A = city('PC')
    ev = A.evaluate

    m = ev(MERGE)
    ok('a thing changed only in the shared copy takes its version', m['remoteOnly'] == 'Two, theirs', m['remoteOnly'])
    ok('a thing changed only in this city keeps this city\'s', m['localOnly'] == 'Two, mine', m['localOnly'])
    ok('two things changed, one on each side, keep both changes', m['both'] == ['One, mine', True], m['both'])
    ok('the same thing changed on both sides goes to the newer side', m['clashLocal'] == 'Mine' and m['clashRemote'] == 'Theirs', [m['clashLocal'], m['clashRemote']])
    ok('a task goes field by field: its title changed on one side and its description on the other both stay', m['fields'] == ['Two, renamed here', 'Described there'], m['fields'])
    ok('a note added to the same task on each side: both stay', m['taskNotes'] == ['n1', 'n2'], m['taskNotes'])
    ok('a task new on each side is kept, each where its side had it', m['added'] == ['a', 'n1', 'b', 'c', 'n2'], m['added'])
    ok('a task deleted on one side and not changed on the other goes', m['deleted'] == ['a', 'c'], m['deleted'])
    ok('deleted on one side and changed on the other: kept when the change is newer, gone when it is older',
       m['deletedChangedNewer'] == ['a', 'b', 'c'] and m['deletedChangedOlder'] == ['a', 'c'], [m['deletedChangedNewer'], m['deletedChangedOlder']])
    ok('the order comes from the side that changed it, and what is new goes after what its side had before it', m['order'] == ['c', 'b', 'n3', 'a'], m['order'])
    ok('Activity keeps both sides\' lines, in time order', m['activity'] == ['Planted', 'Done: One', 'Done: Three'], m['activity'])
    ok('a line taken out on one side, by an Undo, stays out', m['undone'] == ['Planted', 'Wrote a note'], m['undone'])
    ok('Updated and the last work keep the later', m['times'] == [50, 60], m['times'])
    ok('a project new on each side is kept, both in the order', m['projects'] == ['p1', 'p2', 'p3'], m['projects'])
    ok('a project deleted in the shared copy and not changed here goes', m['projectGone'] == [], m['projectGone'])
    ok('two city settings changed, one on each side, keep both', m['city'] == ['20:00', 'large'], m['city'])
    ok('one star in the city: the newer side\'s', m['star'] == ['p1'], m['star'])
    ok('a leader changed in the shared copy takes its version', m['leader'] == 'Head gardener', m['leader'])
    ok('with no base, a city with nothing of its own takes the shared copy whole', m['firstTake'] == ['p1'], m['firstTake'])

    # ---------- Connect and its checks ----------
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    ev("""async ([art, face]) => { const p = DB.projects.find(x => x.name === 'Garden planner');
        await Store.putArt(p.id, art); await Art.set(p.id, art); p.art = { has: true, includesPlot: false };
        const l = blankLeader({ name: 'Mira Fern', role: 'Head gardener' }); DB.leaders.push(l); await Leaders.keep(l.id, face); l.portrait = true; p.leader = l.id;
        persistNow(); }""", [data_url('test-still.png'), data_url('test-block.png')])
    open_settings(A, 'saving')
    ok('Settings, Saving has Sync after The app', ev("() => [...document.querySelectorAll('[data-tab=saving].set-page .set-h')].map(x => x.textContent).slice(0, 3).join(',')") == 'The app,Sync,The data file')
    box = A.text_content('#syncBox')
    ok('off, it says what sync does, with the repository, the token and Connect', 'Keep this city the same on your PC and your phone, through a private GitHub repository.' in box
       and A.input_value('#syncRepo') == 'AbdurrahmanKh/nullovation-city-data' and A.get_attribute('#syncToken', 'type') == 'password' and A.is_visible('#btnSyncConnect'), box)
    A.click('#btnSyncHow')
    ok('How to set it up unfolds the three steps', A.locator('.sync-steps li').count() == 3 and 'Fine-grained tokens' in A.text_content('.sync-steps'))
    A.screenshot(path=str(SH / '460-sync-off.png'))
    def connect(pg, repo, token):
        pg.fill('#syncRepo', repo); pg.fill('#syncToken', token); pg.click('#btnSyncConnect')
        pg.wait_for_function("() => Sync.state() !== 'connecting' && !document.querySelector('#syncBox').textContent.includes('Connecting')", timeout=15000)
        pg.wait_for_timeout(200)
    def said(pg): return pg.text_content('#syncMsg') if pg.locator('#syncMsg').count() else ''
    connect(A, 'me/city-data', 'nope')
    ok('a wrong token is refused, saying so', said(A) == 'GitHub refused the token. Check it was copied whole.', said(A))
    connect(A, 'me/other', 'tok-pc')
    ok('a repository the token does not reach is named', said(A).startswith('GitHub finds no me/other for this token.'), said(A))
    gh.private = False
    connect(A, 'me/city-data', 'tok-pc')
    ok('a public repository is refused', said(A).startswith('me/city-data is public.'), said(A))
    gh.private = True
    connect(A, 'me/city-data', 'tok-pc')
    ok('an empty repository is named, with what to do', said(A) == 'me/city-data is empty. On GitHub, add a README to it, then connect again.', said(A))
    gh.readme()
    connect(A, 'me/city-data', 'tok-ro')
    ok('a token that can only read is named', said(A) == 'The token can only read. Give it Contents: Read and write, then paste it again.', said(A))
    ok('none of the refused tries kept the token', ev("() => localStorage.getItem('nullovation-city:sync')") is None)
    readme = gh.ref
    connect(A, 'me/city-data', 'tok-pc')
    ok('the first city starts the shared copy, with a toast', A.text_content('#toast') == 'Synced. This city started the shared copy in me/city-data.', A.text_content('#toast'))
    files = gh.files()
    ok('the shared copy: city.json, a file per project, each picture once by fingerprint, and the README rewritten',
       sorted(files) == sorted(['README.md', 'city.json', 'projects/' + gp + '.json', 'projects/' + ev("() => DB.projects.find(p => p.name === 'Nullovation City').id") + '.json',
                                'art/' + sha256('test-still.png') + '.png', 'art/' + sha256('test-block.png') + '.png']) and b'shared copy' in files['README.md'], sorted(files))
    cj = gh.json('city.json')
    ok(f'city.json says what it is, the version that wrote it ({VERSION}), the map, the settings, the leaders and the order',
       cj['kind'] == 'shared-city' and cj['format'] == 1 and cj['data'] == 3 and cj['wrote'] == VERSION and cj['world']['nu'] == 5 and cj['city']['night'] == '19:00'
       and cj['leaders'][0]['name'] == 'Mira Fern' and cj['leaders'][0]['portraitFile'] == sha256('test-block.png') + '.png' and len(cj['order']) == 2, cj)
    pj = gh.json('projects/' + gp + '.json')
    ok('a project\'s file is the project, its picture named by fingerprint', pj['name'] == 'Garden planner' and pj['art']['file'] == sha256('test-still.png') + '.png' and len(pj['todos']) == 5)
    ok('pictures go as their own bytes', files['art/' + sha256('test-still.png') + '.png'] == open(fixture('test-still.png'), 'rb').read())
    ok('one commit on top of the README\'s, named for the version', gh.objs[gh.ref][1]['parents'] == [readme] and gh.objs[gh.ref][1]['message'].startswith('City ' + VERSION + ': the first copy'), gh.objs[gh.ref][1]['message'])
    box = A.text_content('#syncBox')
    ok('on, it says where and when it checked, with Pause sync and Disconnect', box.startswith('Synced with me/city-data.') and 'Pause sync' in box and 'Disconnect' in box, box)
    A.screenshot(path=str(SH / '461-sync-on.png'))
    store = ev("() => localStorage.getItem('nullovation-city:v1')")
    backup = ev("async () => JSON.stringify(await buildBackup())")
    base = ev("async () => JSON.stringify(await Store.getSync('base'))")
    repo_text = b''.join(files.values())
    ok('the token is in this browser\'s sync key, and nowhere else: not in the city, a backup, the base or the repository',
       'tok-pc' in ev("() => localStorage.getItem('nullovation-city:sync')") and 'tok-pc' not in store and 'tok-pc' not in backup and 'tok-pc' not in base and b'tok-pc' not in repo_text)
    A.wait_for_timeout(2500)
    ok('a check that finds nothing new is a quick "not changed"', gh.count('tok-pc', 'GET', 'ref/heads', 304) >= 1)
    ok('with nothing changed, nothing more is sent', gh.count('tok-pc', 'POST', 'git/commits') == 1)

    # ---------- the phone takes the shared copy ----------
    ctxB, B = city('phone')
    evb = B.evaluate
    evb("() => { const p = DB.projects.find(x => x.name === 'Nullovation City'); p.name = 'Phone city'; persistNow(); }")
    open_settings(B, 'saving')
    B.fill('#syncRepo', 'me/city-data'); B.fill('#syncToken', 'tok-phone'); B.click('#btnSyncConnect')
    B.wait_for_selector('#cfTitle', timeout=10000)
    ok('another city asks before taking the shared copy, saying a backup comes first', B.text_content('#cfTitle') == 'Take the shared city?'
       and 'with 2 projects. A backup of this city downloads first.' in B.text_content('#cfBody'), B.text_content('#cfBody'))
    with B.expect_download() as dl:
        B.click('.confirm-actions .btn-accent')
    d = dl.value
    saved = json.loads(open(d.path(), encoding='utf-8').read())
    ok('the backup of this city before sync downloads first', d.suggested_filename == 'nullovation-city-backup-before-sync-' + time.strftime('%Y-%m-%d') + '.json'
       and 'Phone city' in [x['name'] for x in saved['projects']], d.suggested_filename)
    B.wait_for_function("() => Sync.state() === 'on' && DB.projects.some(p => p.name === 'Nullovation City')", timeout=15000)
    ok('then the phone holds the shared city', sorted(evb("() => DB.projects.map(p => p.name)")) == ['Garden planner', 'Nullovation City'] and evb("() => DB.leaders.map(l => l.name)") == ['Mira Fern'])
    B.wait_for_timeout(500)
    ok('with its pictures: the building\'s art and the leader\'s portrait, as the PC has them',
       evb(f"async () => (await Store.getArt('{gp}')) === {json.dumps(data_url('test-still.png'))} && !!Art.get('{gp}')")
       and evb("async () => { const l = DB.leaders[0]; return (await Store.getArt(portraitKey(l.id))) === Leaders.url(l.id); }") and evb("() => DB.leaders[0].portrait === true"))
    ok('its toast says it took the copy, with the backup in the downloads', 'This city took the shared copy' in B.text_content('#toast'))
    close_settings(B); close_settings(A)

    # ---------- a change in one city shows in the other ----------
    def wait(pg, js, timeout=12000):
        try: pg.wait_for_function(js, timeout=timeout); return True
        except Exception: return False
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos[0]); changed(p); }}")
    ok('a tick on the PC shows on the phone', wait(B, f"() => getProject('{gp}').todos[0].done === true"))
    evb(f"() => {{ const p = getProject('{gp}'); p.todos[1].text = 'Save the plan as a file'; changed(p); }}")
    ok('a task renamed on the phone shows on the PC', wait(A, f"() => getProject('{gp}').todos[1].text === 'Save the plan as a file'"))
    ok('its Done line came too', evb(f"() => getProject('{gp}').activity.some(e => e.text === 'Done: Draw the beds on a grid')"))
    newp = ev("() => createProject('Recipe box', freePlots()[0]).id")
    ok('a project planted on the PC is planted on the phone', wait(B, f"() => !!getProject('{newp}')"))
    ev(f"() => deleteProject('{newp}')")
    ok('and taken out there when deleted', wait(B, f"() => !getProject('{newp}')"))
    ok('its file left the shared copy', wait(A, "() => true") and 'projects/' + newp + '.json' not in gh.files())

    # ---------- both cities change at once ----------
    ev("() => Sync._test.hold(true)"); evb("() => Sync._test.hold(true)")
    ev(f"() => {{ const p = getProject('{gp}'); p.todos[2].text = 'Add plant icons, PC'; p.todos[4].text = 'Publish, PC'; changed(p); }}")
    A.wait_for_timeout(50)
    evb(f"() => {{ const p = getProject('{gp}'); p.todos[3].description = 'From the phone'; p.todos[4].text = 'Publish, phone'; changed(p); }}")
    ev("() => Sync._test.hold(false)")
    wait(A, f"() => Sync._test.info().sends >= 1 && !!Sync._test.info().base", 5000)
    A.wait_for_timeout(1500)
    pc_head = gh.ref
    with gh.lock: gh.lag['tok-phone'] = gh.objs[pc_head][1]['parents'][0]        # the phone's next read still shows the copy before the PC's send
    refused0 = evb("() => Sync._test.info().refusals")
    evb("() => Sync._test.hold(false)")
    merged = f"() => {{ const t = getProject('{gp}').todos; return t[2].text === 'Add plant icons, PC' && t[3].description === 'From the phone' && t[4].text === 'Publish, phone'; }}"
    ok('a send on an old version is refused by GitHub, and the phone merges and sends again', wait(B, f"() => Sync._test.info().refusals > {refused0}") and gh.count('tok-phone', 'PATCH', 'refs/heads', 422) >= 1)
    ok('after it, the phone holds both cities\' changes, the newer one winning the clash', wait(B, merged), evb(f"() => getProject('{gp}').todos.map(t => t.text + '|' + t.description)"))
    ok('and so does the PC', wait(A, merged), ev(f"() => getProject('{gp}').todos.map(t => t.text + '|' + t.description)"))
    head_now = gh.ref
    with gh.lock: gh.lag['tok-pc'] = gh.objs[head_now][1]['parents'][0]
    rec = ev("() => Sync._test.info().receives")
    A.wait_for_timeout(2000)
    ok('a read that lags behind a send is passed over', ev("() => Sync._test.info().receives") == rec and ev("() => Sync._test.info().base") == gh.ref)

    # ---------- pictures once ----------
    blobs = gh.count('tok-pc', 'POST', 'git/blobs') + gh.count('tok-phone', 'POST', 'git/blobs')
    ev(f"() => {{ const p = getProject('{gp}'); p.plot = freePlots()[0]; changed(p); MapView.dropCache(p.id); }}")
    ok('a building moved on the PC moves on the phone', wait(B, f"() => JSON.stringify(getProject('{gp}').plot) === JSON.stringify({json.dumps(ev(f'() => getProject({json.dumps(gp)}).plot'))})"))
    ok('with no picture sent again', gh.count('tok-pc', 'POST', 'git/blobs') + gh.count('tok-phone', 'POST', 'git/blobs') == blobs and len([f for f in gh.files() if f.startswith('art/')]) == 2)
    ev("async ([art]) => { const p = DB.projects.find(x => x.name === 'Nullovation City'); await Store.putArt(p.id, art); await Art.set(p.id, art); p.art = { has: true, includesPlot: false }; changed(p); }", [data_url('test-block.png')])
    ok('a building given a picture the copy already has sends no picture again', wait(B, "() => DB.projects.find(x => x.name === 'Nullovation City').art.has === true")
       and len([f for f in gh.files() if f.startswith('art/')]) == 2 and gh.count('tok-pc', 'POST', 'git/blobs') + gh.count('tok-phone', 'POST', 'git/blobs') == blobs)
    ok('and the phone has it', wait(B, "() => { const p = DB.projects.find(x => x.name === 'Nullovation City'); return !!Art.get(p.id); }"))

    # ---------- applying in place, and waiting while typing ----------
    evb(f"() => FullView.open('{gp}')"); B.wait_for_timeout(300)
    t3 = evb(f"() => getProject('{gp}').todos[3].id")
    evb(f"() => FullView.openTask('{gp}', '{t3}')"); B.wait_for_timeout(300)
    ok('on the phone, the task panel is open with the focus in its description', evb("() => document.activeElement && document.activeElement.id === 'pvTaskDesc'"))
    ev(f"() => {{ const p = getProject('{gp}'); p.todos[0].text = 'Draw the beds, renamed'; p.description = 'Plans the garden.'; changed(p); }}")
    A.wait_for_timeout(2500)
    ok('while you type there, the change waits', evb(f"() => getProject('{gp}').todos[0].text") == 'Draw the beds on a grid' and evb("() => Sync._test.info().deferred"))
    evb("() => document.activeElement.blur()")
    ok('leaving the field takes it in', wait(B, f"() => getProject('{gp}').todos[0].text === 'Draw the beds, renamed'"))
    B.wait_for_timeout(300)
    ok('in place: the project view and its task panel stay open, and show it', evb("() => FullView.isOpen() && !!document.querySelector('.pv-side')")
       and 'Plans the garden.' in B.text_content('#pv') and 'Draw the beds, renamed' in B.text_content('#pv'))
    t3obj = evb(f"() => {{ window.__t = getProject('{gp}').todos.find(t => t.id === '{t3}'); return true; }}")
    ev(f"() => {{ const p = getProject('{gp}'); p.todos.find(t => t.id === '{t3}').text = 'Tune the reminders'; changed(p); }}")
    ok('a task changed while its panel is open is the same task, changed', wait(B, f"() => window.__t === getProject('{gp}').todos.find(t => t.id === '{t3}') && window.__t.text === 'Tune the reminders'"))
    B.screenshot(path=str(SH / '462-sync-in-place.png'))
    evb("() => FullView.close()")

    # ---------- offline and back ----------
    ctxB.set_offline(True)
    evb(f"() => {{ const p = getProject('{gp}'); p.todos[1].description = 'Written offline'; changed(p); }}")
    ev(f"() => {{ const p = getProject('{gp}'); p.todos[2].description = 'Written on the PC'; changed(p); }}")
    ok('offline, the phone keeps its change and says, after a while, that it waits for the network',
       wait(B, "() => !document.querySelector('#syncAlert').hidden && document.querySelector('#syncAlert').textContent === 'Sync is waiting for the network.'", 8000))
    B.screenshot(path=str(SH / '463-sync-waiting.png'))
    ctxB.set_offline(False)
    both = f"() => {{ const t = getProject('{gp}').todos; return t[1].description === 'Written offline' && t[2].description === 'Written on the PC'; }}"
    ok('back online, both changes are in both cities', wait(B, both) and wait(A, both))
    ok('and the line goes', wait(B, "() => document.querySelector('#syncAlert').hidden"))

    # ---------- both plant on the same plot ----------
    ev("() => Sync._test.hold(true)"); evb("() => Sync._test.hold(true)")
    free = ev("() => freePlots()[0]")
    ev(f"() => createProject('Bird feeder', {json.dumps(free)})"); A.wait_for_timeout(30)
    evb(f"() => createProject('Bike repair', {json.dumps(free)})")
    ev("() => Sync._test.hold(false)"); A.wait_for_timeout(1500); evb("() => Sync._test.hold(false)")
    four = "() => ['Bird feeder', 'Bike repair'].every(n => DB.projects.some(p => p.name === n))"
    ok('two buildings planted on one plot at once both stand, on different plots', wait(A, four) and wait(B, four)
       and ev("() => new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v)).size === DB.projects.length")
       and evb("() => new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v)).size === DB.projects.length"))
    A.wait_for_timeout(1500)
    ok('and the two cities agree on where', sorted(ev("() => DB.projects.map(p => p.name + '@' + p.plot.u + ',' + p.plot.v)")) == sorted(evb("() => DB.projects.map(p => p.name + '@' + p.plot.u + ',' + p.plot.v)")))

    # ---------- a second tab follows ----------
    A2 = ctxA.new_page()
    A2.on('pageerror', lambda e: errors.append('PC tab 2: ' + str(e)))
    A2.goto(FILE); A2.wait_for_function("() => typeof DB !== 'undefined' && DB.projects.length > 2", timeout=20000)
    A2.evaluate("() => Sync._test.fast()")
    A.bring_to_front(); A.mouse.click(5, 450)
    ev(f"() => {{ const p = getProject('{gp}'); p.name = 'Garden planner'; p.todos[4].text = 'Publish the app, from tab 1'; changed(p); }}")
    ok('a second tab of the same city follows a change made in the first', wait(A2, f"() => getProject('{gp}').todos[4].text === 'Publish the app, from tab 1'"))
    ok('it stands by: one tab syncs', A2.evaluate("() => Sync.state()") == 'standby' and ev("() => Sync._test.info().writer"))
    evb(f"() => {{ const p = getProject('{gp}'); p.todos[4].description = 'From the phone, to both tabs'; changed(p); }}")
    reached = wait(A2, f"() => getProject('{gp}').todos[4].description === 'From the phone, to both tabs'")
    ok('a change from the phone reaches the tab that stands by too, through the one that syncs', reached,
       None if reached else [ev("() => [Sync._test.info(), document.visibilityState, document.activeElement && document.activeElement.outerHTML.slice(0, 80)]"),
                             A2.evaluate("() => [Sync._test.info(), document.visibilityState, document.activeElement && document.activeElement.outerHTML.slice(0, 80)]"),
                             evb("() => Sync._test.info()"), ev(f"() => getProject('{gp}').todos.map(t => t.text + '|' + t.description)"),
                             evb(f"() => getProject('{gp}').todos.map(t => t.text + '|' + t.description)"),
                             [x['text'] + '|' + x['description'] for x in gh.json('projects/' + gp + '.json')['todos']],
                             [(e['method'], e['path'][-30:], e['tok'], e['status']) for e in gh.log[-25:]]])
    A2.evaluate("() => Settings.open('saving')"); A2.wait_for_timeout(200)
    ok('its Settings say another tab syncs, and that this one takes over once used', 'Another tab of this city syncs with me/city-data. This tab takes over as soon as you use it.' in A2.text_content('#syncBox'), A2.text_content('#syncBox'))
    A2.mouse.click(5, 450)
    ok('used, it takes over, and the first tab stands by', wait(A2, "() => Sync.state() === 'on' && Sync._test.info().writer") and wait(A, "() => Sync.state() === 'standby'"))
    A2.close()
    A.mouse.click(5, 450)
    ok('the first tab takes over again once the second closes and it is used', wait(A, "() => Sync.state() === 'on' && Sync._test.info().writer"))
    A.bring_to_front()

    # ---------- the version guard ----------
    cj = gh.json('city.json'); cj['wrote'] = '9.9.9'
    gh.put_files({'city.json': json.dumps(cj).encode()}, 'City 9.9.9: the map and the settings')
    guard = 'Sync stopped: the shared copy is from a newer city (9.9.9). Reload to update.'
    ok('a shared copy from a newer city stops sync, saying to reload', wait(A, f"() => document.querySelector('#syncAlert').textContent.startsWith({json.dumps(guard)})"), A.text_content('#syncAlert'))
    commits = gh.count('tok-pc', 'POST', 'git/commits')
    ev(f"() => {{ const p = getProject('{gp}'); p.description = 'Not sent'; changed(p); }}"); A.wait_for_timeout(1500)
    ok('and sends nothing', gh.count('tok-pc', 'POST', 'git/commits') == commits)
    A.screenshot(path=str(SH / '464-sync-newer.png'))
    cj['wrote'] = VERSION
    gh.put_files({'city.json': json.dumps(cj).encode()}, 'back')
    A.reload(); A.wait_for_function("() => typeof DB !== 'undefined' && DB.projects.length > 2", timeout=20000)
    A.evaluate("() => Sync._test.fast()")
    ok('after a reload it syncs again, and what waited is sent', wait(A, f"() => Sync.state() === 'on' && !Sync._test.info().problem") and wait(B, f"() => getProject('{gp}').description === 'Not sent'"))
    ok('a city stopped by the newer copy goes on by itself once the copy can be read again', evb("() => !Sync._test.info().problem") and B.is_hidden('#syncAlert'))

    # ---------- a token refused, and a new one ----------
    with gh.lock: gh.tokens.pop('tok-phone')
    evb(f"() => {{ const p = getProject('{gp}'); p.todos[0].description = 'After the new token'; changed(p); }}")
    ok('a token GitHub refuses stops sync, saying to paste a new one', wait(B, "() => document.querySelector('#syncAlert').textContent.startsWith('Sync stopped: GitHub refused the token. Paste a new one.')"), B.text_content('#syncAlert'))
    with gh.lock: gh.tokens['tok-phone-2'] = 'rw'
    B.click('#syncAlert .linkish'); B.wait_for_timeout(200)
    ok('Paste it opens Sync in Settings, at the new token\'s field', evb("() => document.activeElement && document.activeElement.id === 'syncNewToken'"))
    B.fill('#syncNewToken', 'tok-phone-2'); B.click('#btnSyncToken')
    ok('with the new token, sync goes on and sends what waited', wait(A, f"() => getProject('{gp}').todos[0].description === 'After the new token'")
       and 'tok-phone-2' in evb("() => localStorage.getItem('nullovation-city:sync')"))
    close_settings(B)

    # ---------- Pause and Disconnect ----------
    open_settings(A, 'saving')
    A.click('#syncBox .linkish:has-text("Pause sync")')
    ok('paused, the city says so under the logo, with Resume', A.text_content('#syncAlert') == 'Sync is paused. Resume' and 'is paused: this city neither sends nor receives.' in A.text_content('#syncBox'))
    reqs = gh.count('tok-pc')
    evb(f"() => {{ const p = getProject('{gp}'); p.todos[1].text = 'While the PC was paused'; changed(p); }}")
    B.wait_for_timeout(2500)
    ok('a paused city neither asks nor takes', gh.count('tok-pc') == reqs and ev(f"() => getProject('{gp}').todos[1].text") != 'While the PC was paused')
    A.click('#syncAlert .linkish')
    ok('Resume takes in what came meanwhile', wait(A, f"() => getProject('{gp}').todos[1].text === 'While the PC was paused'"))
    close_settings(A)
    names = sorted(evb("() => DB.projects.map(p => p.name)"))
    open_settings(B, 'saving')
    B.click('#syncBox .linkish:has-text("Disconnect")')
    wait(B, "() => document.querySelector('#toast').textContent.startsWith('Sync is off.')", 5000)
    gone = [evb("() => localStorage.getItem('nullovation-city:sync')"), sorted(evb("() => DB.projects.map(p => p.name)")), B.text_content('#toast')]
    ok('Disconnect forgets the token and leaves the city as it is', gone == [None, names, 'Sync is off. This city stays as it is, and the repository keeps its copy.'], [gone, names])
    ok('and it is off again, ready to connect', B.is_visible('#btnSyncConnect') and evb("async () => !(await Store.getSync('base'))"))
    exported = evb("async () => JSON.stringify(await buildBackup())")
    ok('no token anywhere it must not be: not in either city, a backup, or the shared copy',
       all(t not in exported for t in ('tok-phone', 'tok-pc')) and all(t.encode() not in b''.join(gh.files().values()) for t in ('tok-phone', 'tok-pc'))
       and 'tok-pc' not in ev("() => localStorage.getItem('nullovation-city:v1')"))

    print('errors:', errors)
    ok('no console errors', not errors)
    b.close()
srv.shutdown()
