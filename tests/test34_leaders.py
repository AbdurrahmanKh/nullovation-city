"""Leaders (0.1.51): the city's characters who run its buildings. A leader holds a name, a role, a signature color and a
portrait; one leader per building, and one leader can run several. The side bar's Leaders section adds and edits them,
the more menu and the leader card pick a building's leader, and the face shows in the status card, the wheel's middle
and the project view. Claude's copies, the status brief and the city summary name them. Backups, the data file and a
project's export carry them, portraits included."""
import json, pathlib, random
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY, DATA, ROOT, fixture

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

GUS = str(ROOT / 'src' / 'portraits' / 'gus.png')
PROXIMA = str(ROOT / 'src' / 'portraits' / 'proxima.png')

# files a portrait refuses: not an image, over 1024 px, over 3 MB
DATA.mkdir(parents=True, exist_ok=True)
NOTES = DATA / 'leader-notes.txt'; NOTES.write_text('not a picture', encoding='utf-8')
BIG = DATA / 'leader-big.png'; HEAVY = DATA / 'leader-heavy.png'
from PIL import Image
if not BIG.exists(): Image.new('RGBA', (1100, 40), (90, 160, 150, 255)).save(BIG)
if not HEAVY.exists():
    rnd = random.Random(7)
    Image.frombytes('RGBA', (1000, 1000), bytes(rnd.getrandbits(8) for _ in range(4_000_000))).save(HEAVY)
# a portrait drawn small on a big see-through canvas, as Pro Flash's 128 px ones were (0.1.52): its figure from (19, 17)
# to (101, 111), with 16 px clear under it; and a tall photo with no see-through pixels
SMALL = DATA / 'leader-small.png'; TALL = DATA / 'leader-tall.jpg'
if not SMALL.exists():
    from PIL import ImageDraw
    im = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); ImageDraw.Draw(im).rectangle((19, 17, 101, 111), fill=(120, 80, 160, 255)); im.save(SMALL)
if not TALL.exists(): Image.new('RGB', (100, 160), (200, 120, 90)).save(TALL, quality=95)
import base64
data_url = lambda path, kind: 'data:image/' + kind + ';base64,' + base64.b64encode(pathlib.Path(path).read_bytes()).decode()

def watch(pg):
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page(); watch(pg)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    toasted = lambda: ev("() => document.querySelector('#toast').classList.contains('show') ? document.querySelector('#toast').textContent : ''")
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; }")
    lead = lambda pid: ev(f"() => getProject('{pid}').leader")
    def panel():
        """The Leaders panel, open on its list (0.1.61)."""
        ev("() => { if (!Leaders.isOpen()) document.querySelector('#btnOpenLeaders').click(); else if (Leaders.editing()) document.querySelector('#ldBack').click(); }"); pg.wait_for_timeout(200)
    def row(lid):
        panel(); pg.click(f'.ld-row[data-id="{lid}"]'); pg.wait_for_timeout(250)
    leaders = lambda: ev("() => DB.leaders.map(l => [l.name, l.role, l.color, l.portrait, leaderProjects(l).map(p => p.name).sort()])")

    # ---------- the model ----------
    ok('twelve signature colors, each a #RRGGBB', ev("() => LEADER_COLORS.length === 12 && LEADER_COLORS.every(c => /^#[0-9A-F]{6}$/.test(c))"))
    bl = ev("() => { const l = blankLeader(); return [l.id.slice(0, 2), LEADER_COLORS.includes(l.color), l.portrait, l.name, l.role]; }")
    ok(f'a blank leader: an id, a color dealt from its id, no portrait, no name or role ({bl})', bl == ['ld', True, False, '', ''])
    ok('the same id always deals the same color', ev("() => blankLeader({ id: 'ld-x' }).color === blankLeader({ id: 'ld-x' }).color"))
    sl = ev("""() => sanitizeLeaders([{ id: 'a', name: '  Gus   Grimsby ', role: ' Garbage  Man ', color: '#f29a74', portrait: 1 },
        { id: 'a', name: '', role: 'r'.repeat(80), color: 'red' }, 'junk', null, { name: 'n'.repeat(80) }])""")
    ok('loading trims names and roles and keeps a good color, uppercased',
       sl[0]['name'] == 'Gus Grimsby' and sl[0]['role'] == 'Garbage Man' and sl[0]['color'] == '#F29A74' and sl[0]['portrait'] is True and sl[0]['id'] == 'a')
    ok('a second leader with the same id gets its own; no name reads as Leader; a bad color is dealt again; a role stops at 60',
       sl[1]['id'] != 'a' and sl[1]['name'] == 'Leader' and sl[1]['color'] in ev("() => LEADER_COLORS") and len(sl[1]['role']) == 60 and sl[1]['portrait'] is False)
    ok('what is not a leader is skipped, and a name stops at 60', len(sl) == 3 and len(sl[2]['name']) == 60)
    td = ev("""() => { const keepL = DB.leaders, keepP = DB.projects;
        DB.leaders = [{ id: 'k', name: 'Kept', role: '', color: '#F29A74', portrait: false }];
        DB.projects = [blankProject({ leader: 'k' }), blankProject({ leader: 'gone' })];
        tidyLeaders(); const out = DB.projects.map(p => p.leader);
        const line = [leaderLine(DB.projects[0]), leaderLine(DB.projects[1])];
        DB.leaders[0].role = 'Mayor'; line.push(leaderLine(DB.projects[0]));
        setLeader(DB.projects[1], 'nobody'); out.push(DB.projects[1].leader);
        DB.leaders = keepL; DB.projects = keepP; return [out, line]; }""")
    ok(f'a building whose leader is gone is left without one ({td[0]})', td[0] == ['k', '', ''])
    ok(f'Claude\'s line: the name, and the role when there is one; nothing without a leader ({td[1]})',
       td[1] == ['Leader: Kept', None, 'Leader: Kept, Mayor'])
    ok('a darker and a lighter shade of a signature color', ev("() => [shadeHex('#808080', -0.5), shadeHex('#808080', 0.5), shadeHex('#F29A74', 0)]") == ['#404040', '#C0C0C0', '#F29A74'])
    ok('the test city starts with no leaders and no building led', ev("() => DB.leaders.length === 0 && DB.projects.every(p => p.leader === '')"))

    # ---------- the Leaders panel (0.1.61): a button at the side bar's foot, beside All tasks ----------
    ok('the side bar has no Leaders section any more', ev("() => !document.querySelector('#sbLeaders, #leaderGrid, .ld-tile')"))
    foot = ev("""() => { const a = document.querySelector('#btnOpenAllTasks').getBoundingClientRect(), l = document.querySelector('#btnOpenLeaders').getBoundingClientRect(),
        r = document.querySelector('#btnOpenReports').getBoundingClientRect(); return { text: document.querySelector('#btnOpenLeaders').textContent.trim(), row: Math.round(a.top) === Math.round(l.top),
        beside: l.left > a.right, under: r.top > l.bottom - 1, icon: !!document.querySelector('#btnOpenLeaders svg') }; }""")
    ok(f'a Leaders button at the foot, beside All tasks, over Reports and Settings ({foot})', foot == {'text': 'Leaders', 'row': True, 'beside': True, 'under': True, 'icon': True})
    pg.click('#btnOpenLeaders'); pg.wait_for_timeout(250)
    sec = ev("""() => ({ shown: !document.querySelector('#leadersPanel').hidden, lists: !document.querySelector('#sbLists').hidden, title: document.querySelector('#ldTitle').textContent,
        btn: document.querySelector('#btnNewLeader').textContent.trim(), empty: (document.querySelector('#ldList .ld-empty') || {}).textContent, focus: document.activeElement.id })""")
    ok(f'it turns the side bar into the Leaders panel, as All tasks does, with New leader at its top ({sec})', sec['shown'] and not sec['lists'] and sec['title'] == 'Leaders'
       and sec['btn'] == 'New leader' and sec['focus'] == 'leadersPanel')
    ok('with none, it says how to start', sec['empty'] == 'No leaders yet. Add one with a portrait, then give it a building.')
    pg.screenshot(path=str(SHOTS / '340-leaders-empty.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 200})
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes it, the focus back on its button', ev("() => !Leaders.isOpen() && !document.querySelector('#sbLists').hidden && document.activeElement.id === 'btnOpenLeaders'"))
    pg.click('#btnOpenAllTasks'); pg.wait_for_timeout(200); pg.click('#atBack'); pg.wait_for_timeout(150)
    pg.click('#btnOpenLeaders'); pg.wait_for_timeout(200)
    ok('it shares the side bar with All tasks, Reports and Settings: opening one closes the other', ev("() => Leaders.isOpen() && document.querySelector('#allTasks').hidden")
       and (pg.click('#ldBack'), pg.wait_for_timeout(150), ev("() => (AllTasks.open(), !Leaders.isOpen() && !document.querySelector('#allTasks').hidden)"))[2])
    ev("() => AllTasks.close()"); pg.wait_for_timeout(100)
    panel()

    # ---------- a new leader ----------
    g0 = ev(f"() => [getProject('{gp}').updatedAt, getProject('{gp}').activity.length]")
    pg.click('#btnNewLeader'); pg.wait_for_timeout(250)
    ok('New leader opens the editor in the panel, in the list\'s place', pg.is_visible('.ld-panel') and pg.text_content('#ldTitle') == 'New leader' and not pg.is_visible('#ldList')
       and not pg.is_visible('#btnNewLeader') and not ev("() => Panel.isOpen()"))
    ok('the name has the focus', ev("() => document.activeElement.id") == 'ldName')
    sil = ev("() => { const f = document.querySelector('.ld-big .ld-face'); return { svg: !!f.querySelector('svg'), img: !!f.querySelector('img'), w: Math.round(f.getBoundingClientRect().width) }; }")
    ok(f'with no portrait, a silhouette on its signature color, 128 px ({sil})', sil['svg'] and not sil['img'] and sil['w'] == 128)
    ok('Upload portrait, and no Remove yet (and no stray text beside it)', ev("() => [...document.querySelectorAll('.ld-portrait-btns button')].map(b => b.textContent.trim())") == ['Upload portrait']
       and ev("() => document.querySelector('.ld-portrait-btns').textContent.trim()") == 'Upload portrait')
    pg.click('#ldAdd'); pg.wait_for_timeout(150)
    ok('Add with no name asks for one and adds nothing', pg.is_visible('.ld-err') and pg.text_content('.ld-err') == 'Give the leader a name.' and ev("() => DB.leaders.length") == 0
       and ev("() => document.activeElement.id") == 'ldName')
    for f, want in ((NOTES, 'A portrait takes a PNG, GIF, JPEG or WebP.'),
                    (BIG, 'This image is 1100 by 40 px. A portrait is at most 1024 px; 256 by 256 is plenty.'),
                    (HEAVY, 'This image is over 3 MB. A portrait needs far less: 256 by 256 px is plenty.')):
        pg.set_input_files('.ld-panel input[type=file]', str(f)); pg.wait_for_timeout(300)
        ok(f'a portrait refuses {f.name}: "{pg.text_content(".ld-err")}"', pg.is_visible('.ld-err') and pg.text_content('.ld-err') == want
           and ev("() => !document.querySelector('.ld-big img')"))
    pg.set_input_files('.ld-panel input[type=file]', GUS); pg.wait_for_timeout(400)
    up = ev("() => { const i = document.querySelector('.ld-big img'); return i ? { nat: i.naturalWidth, data: i.src.startsWith('data:image/png'), smooth: getComputedStyle(i).imageRendering } : null; }")
    ok(f'a PNG portrait shows in the panel, shrunk smooth ({up})', up and up['nat'] == 256 and up['data'] and up['smooth'] == 'auto')
    ok('the error goes, and the buttons say Replace portrait and Remove', not pg.is_visible('.ld-err')
       and ev("() => [...document.querySelectorAll('.ld-portrait-btns button')].map(b => b.textContent.trim())") == ['Replace portrait', 'Remove'])
    ok('nothing is added before Add', ev("() => DB.leaders.length") == 0)
    pg.fill('#ldName', 'Gus Grimsby'); pg.fill('#ldRole', 'Garbage Man')
    pg.click('.ld-swatch[title="#F29A74"]'); pg.wait_for_timeout(100)
    ok('a swatch picks the signature color, pressed', ev("() => document.querySelector('.ld-swatch[title=\"#F29A74\"]').getAttribute('aria-pressed')") == 'true'
       and ev("() => document.querySelectorAll('.ld-swatch[aria-pressed=\"true\"]').length") == 1)
    blds = ev("() => [...document.querySelectorAll('.ld-bld')].map(l => l.querySelector('.ld-bld-name').textContent)")
    ok(f'Leads lists every building, by name ({blds})', blds == ['Garden planner', 'Nullovation City'])
    pg.check(f'.ld-bld[data-id="{gp}"] input'); pg.wait_for_timeout(100)
    ok('ticking a building keeps the focus on it', ev(f"() => document.activeElement === document.querySelector('.ld-bld[data-id=\"{gp}\"] input')"))
    pg.screenshot(path=str(SHOTS / '341-new-leader.png'))
    quiet(); pg.click('#ldAdd'); pg.wait_for_timeout(500)
    ok(f'Add adds it and goes back to the list, with a toast ({toasted()})', toasted() == 'Added Gus Grimsby, who leads Garden planner.' and not pg.is_visible('.ld-panel')
       and pg.is_visible('#ldList') and pg.text_content('#ldTitle') == 'Leaders')
    ok(f'the leader holds its name, role, color and portrait, and leads its building ({leaders()})',
       leaders() == [['Gus Grimsby', 'Garbage Man', '#F29A74', True, ['Garden planner']]])
    gid = ev("() => DB.leaders[0].id")
    ok('the portrait sits in the art store under leader: and its id', ev(f"async () => (await Store.getArt('leader:{gid}')) === Leaders.url('{gid}') && Leaders.url('{gid}').startsWith('data:image/png')"))
    ok('picking a leader is not work: Updated stays and nothing goes in Activity', ev(f"() => [getProject('{gp}').updatedAt, getProject('{gp}').activity.length]") == g0)
    tile = ev("""() => [...document.querySelectorAll('#ldList .ld-row')].map(t => ({ name: t.querySelector('.ld-row-text b').textContent, role: t.querySelector('.ld-row-role').textContent,
        blds: t.querySelector('.ld-row-blds').textContent, img: !!t.querySelector('img'), w: Math.round(t.querySelector('.ld-face').getBoundingClientRect().width), title: t.title,
        focus: document.activeElement === t }))""")
    ok(f'the list shows its face, 48 px, its name, role and buildings, the focus on it ({tile})', len(tile) == 1 and tile[0]['name'] == 'Gus Grimsby' and tile[0]['role'] == 'Garbage Man'
       and tile[0]['blds'] == 'Garden planner' and tile[0]['img'] and tile[0]['w'] == 48 and tile[0]['title'] == 'Edit Gus Grimsby. Leads 1 building.' and tile[0]['focus'])
    ok('and the empty line goes', ev("() => !document.querySelector('#ldList .ld-empty')"))
    saved = ev("() => { const d = JSON.parse(localStorage.getItem('nullovation-city:v1')); return [d.version, (d.leaders || []).map(l => l.name), d.projects.find(p => p.name === 'Garden planner').leader === DB.leaders[0].id, 'portraitUrl' in (d.leaders[0] || {})]; }")
    ok(f'the city saves its leaders and each building\'s leader, the portrait apart ({saved})', saved == [3, ['Gus Grimsby'], True, False])
    pg.screenshot(path=str(SHOTS / '342-leaders-side.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 260})

    # ---------- the status card ----------
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(700)
    sc = ev("""() => { const l = document.querySelector('#bubble .b-leader'); if (!l) return null;
        const t = document.querySelector('#bubble .b-title');
        return { name: l.querySelector('.ld-name').textContent, role: l.querySelector('.b-leader-text span').textContent, img: !!l.querySelector('img'),
          w: Math.round(l.querySelector('.ld-face').getBoundingClientRect().width), afterTitle: t.nextElementSibling === l }; }""")
    ok(f'the status card names the leader under the building\'s name, with a 48 px face (0.1.57; 32 before) ({sc})', sc and sc['name'] == 'Gus Grimsby' and sc['role'] == 'Garbage Man'
       and sc['img'] and sc['w'] == 48 and sc['afterTitle'])
    pg.screenshot(path=str(SHOTS / '343-leader-status.png'))
    ev(f"() => MapView.select('{nc}')"); pg.wait_for_timeout(500)
    ok('a building with no leader shows no line', ev("() => !document.querySelector('#bubble .b-leader')"))
    ev("() => MapView.deselect()"); pg.wait_for_timeout(200)

    # ---------- the wheel's middle ----------
    left = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    def right_click(pid):
        a = ev(f"() => MapView.anchors('{pid}')")
        pg.mouse.click(left + a['baseX'], a['baseY'] - 30, button='right'); pg.wait_for_timeout(350)
    ev("() => MapView.setCam({ x: 0, y: 260, z: 2 })"); pg.wait_for_timeout(300)
    right_click(gp)
    hub = ev("""() => { const h = document.querySelector('.wheel-hub'); if (!h) return null; const f = h.querySelector('.ld-face'), i = h.querySelector('img');
        return { has: h.classList.contains('has-leader'), img: !!i, round: f && getComputedStyle(f).borderRadius === '50%', w: f && Math.round(f.getBoundingClientRect().width),
          src: i && i.getAttribute('src'), label: document.querySelector('.wheel').getAttribute('aria-label'), pe: getComputedStyle(h).pointerEvents }; }""")
    ok(f'the wheel\'s middle shows the leader\'s face, round, 64 px ({ {k: v for k, v in (hub or {}).items() if k != "src"} })', hub and hub['has'] and hub['img'] and hub['round'] and hub['w'] == 64)
    ok('it is the leader\'s portrait', hub and hub['src'] == ev(f"() => Leaders.url('{gid}')"))
    ok('the wheel says who leads it, and a click in the middle still reaches the building', hub and hub['label'] == 'Shortcuts of Garden planner, led by Gus Grimsby' and hub['pe'] == 'none')
    pg.screenshot(path=str(SHOTS / '344-leader-wheel.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    right_click(nc)
    ok('a building with no leader keeps the middle empty', ev("() => { const h = document.querySelector('.wheel-hub'); return !!h && !h.classList.contains('has-leader') && h.children.length === 0; }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # ---------- the project view's leader card ----------
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(700)
    card = ev("""() => { const c = document.querySelector('#pvLeader'); if (!c) return null;
        return { name: c.querySelector('.ld-name').textContent, role: c.querySelector('.ld-card-text span').textContent, img: !!c.querySelector('img'),
          w: Math.round(c.querySelector('.ld-face').getBoundingClientRect().width), change: (c.querySelector('.ld-change') || {}).textContent,
          under: !!document.querySelector('.pv-scene') && (document.querySelector('.pv-scene').compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING) > 0 }; }""")
    ok(f'the project view has a leader card under the building: the face, 96 px (0.1.57; 64 before), the name, the role and Change ({card})', card and card['name'] == 'Gus Grimsby'
       and card['role'] == 'Garbage Man' and card['img'] and card['w'] == 96 and card['change'] == 'Change' and card['under'])
    pg.screenshot(path=str(SHOTS / '345-leader-card.png'))
    pg.click('#pvLeader .ld-change'); pg.wait_for_timeout(300)
    opts = ev("() => [...document.querySelectorAll('#pvSide .ld-opt')].map(o => [o.querySelector('b').textContent, o.getAttribute('aria-pressed')])")
    ok(f'Change opens the picker beside the view: No leader and each leader, the one in charge pressed ({opts})', pg.is_visible('#pvSide') and opts == [['No leader', 'false'], ['Gus Grimsby', 'true']])
    ok('with New leader and Edit beside them', ev("() => [...document.querySelectorAll('#pvSide .ld-pick-btns button')].map(b => b.textContent.trim())") == ['New leader', 'Edit Gus Grimsby'])
    pg.screenshot(path=str(SHOTS / '346-leader-picker.png'))

    # a second leader, made from the picker, with no portrait: it takes this building
    pg.click('#ldPickNew'); pg.wait_for_timeout(250)
    ok('New leader from the picker opens the editor in the side bar\'s panel, beside the view, with this building ticked', pg.is_visible('.ld-panel') and pg.is_visible('#pv')
       and ev("() => Leaders.isOpen()") and ev(f"() => document.querySelector('.ld-bld[data-id=\"{gp}\"] input').checked"))
    ok('a building led by another says by whom', ev(f"() => (document.querySelector('.ld-bld[data-id=\"{gp}\"] .ld-bld-other') || {{}}).textContent") is None
       and ev(f"() => !document.querySelector('.ld-bld[data-id=\"{nc}\"] .ld-bld-other')"))
    pg.uncheck(f'.ld-bld[data-id="{gp}"] input'); pg.wait_for_timeout(100)
    ok('unticked, it says Gus Grimsby leads it', ev(f"() => (document.querySelector('.ld-bld[data-id=\"{gp}\"] .ld-bld-other') || {{}}).textContent") == 'led by Gus Grimsby')
    pg.check(f'.ld-bld[data-id="{gp}"] input'); pg.wait_for_timeout(100)
    pg.fill('#ldName', 'Proxima Pace'); pg.fill('#ldRole', 'Productivity Inspector'); pg.click('.ld-swatch[title="#8FD0F7"]')
    quiet(); pg.press('#ldRole', 'Enter'); pg.wait_for_timeout(500)
    ok(f'Enter in the name or the role adds it too ({toasted()})', toasted() == 'Added Proxima Pace, who leads Garden planner.' and not pg.is_visible('.ld-panel'))
    pid = ev("() => DB.leaders.find(l => l.name === 'Proxima Pace').id")
    ok('it now leads the building, and the picker beside the view shows it pressed', lead(gp) == pid
       and ev("() => [...document.querySelectorAll('#pvSide .ld-opt')].map(o => o.getAttribute('aria-pressed'))") == ['false', 'false', 'true'])
    silc = ev("""() => { const f = document.querySelector('#pvLeader .ld-face'); return { svg: !!f.querySelector('svg'), img: !!f.querySelector('img'),
        bg: getComputedStyle(f).backgroundColor, fill: f.querySelector('svg').getAttribute('fill') }; }""")
    ok(f'with no portrait, the card shows a silhouette on its signature color ({silc})', silc['svg'] and not silc['img'] and silc['bg'] == 'rgb(143, 208, 247)'
       and silc['fill'] == ev("() => shadeHex('#8FD0F7', -0.42)"))
    pg.screenshot(path=str(SHOTS / '347-leader-silhouette.png'), clip={'x': 300, 'y': 340, 'width': 480, 'height': 220})

    # picking: one leader for several buildings, from the more menu too
    quiet(); pg.click(f'#pvSide .ld-opt[data-id="{gid}"]'); pg.wait_for_timeout(300)
    ok(f'a click on a leader picks it, with a toast ({toasted()})', lead(gp) == gid and toasted() == 'Gus Grimsby leads Garden planner now.')
    ev(f"() => FullView.open('{nc}')"); pg.wait_for_timeout(600)
    pg.click('#pvMore'); pg.wait_for_timeout(150)
    ok('the more menu says Pick a leader for a building with none', 'Pick a leader' in ev("() => [...document.querySelectorAll('.pv-menu-item')].map(e => e.textContent)"))
    pg.click('.pv-menu-item >> text=Pick a leader'); pg.wait_for_timeout(300)
    gus_opt = ev(f"() => document.querySelector('#pvSide .ld-opt[data-id=\"{gid}\"] .ld-opt-text span').textContent")
    ok(f'the picker says where a leader already leads ({gus_opt})', gus_opt == 'Garbage Man · also leads 1 building')
    quiet(); pg.click(f'#pvSide .ld-opt[data-id="{gid}"]'); pg.wait_for_timeout(300)
    ok('one leader can lead several buildings', lead(nc) == gid and leaders()[0][4] == ['Garden planner', 'Nullovation City'])
    pg.click('#pvMore'); pg.wait_for_timeout(150)
    ok('the more menu then names the leader', ev("() => [...document.querySelectorAll('.pv-menu-item')].map(e => e.textContent)")[1] == 'Leader: Gus Grimsby')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('its row in the Leaders panel says how many it leads, and names them', ev(f"() => document.querySelector('.ld-row[data-id=\"{gid}\"]').title") == 'Edit Gus Grimsby. Leads 2 buildings.'
       and ev(f"() => document.querySelector('.ld-row[data-id=\"{gid}\"] .ld-row-blds').textContent") == 'Garden planner, Nullovation City')
    quiet(); pg.click('#pvSide .ld-opt[data-id=""]'); pg.wait_for_timeout(300)
    ok(f'No leader leaves the building without one ({toasted()})', lead(nc) == '' and toasted() == 'Nullovation City has no leader now.')
    emp = ev("() => { const c = document.querySelector('#pvLeader'); return [c.tagName, c.classList.contains('empty'), c.textContent]; }")
    ok(f'and the card offers to pick one ({emp})', emp == ['BUTTON', True, 'No leader yetPick a leader'])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    pg.click('#pvLeader'); pg.wait_for_timeout(300)
    ok('a click on it opens the picker', pg.is_visible('#pvSide') and ev("() => document.querySelectorAll('#pvSide .ld-opt').length") == 3)
    ok('none of this is work', ev(f"() => getProject('{nc}').activity.some(e => /leader/i.test(e.text))") is False)
    pg.keyboard.press('Escape'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # ---------- editing: every change applies at once ----------
    row(gid)
    ok('a click on a leader opens it to edit, in the panel', pg.is_visible('.ld-panel') and pg.text_content('#ldTitle') == 'Leader: Gus Grimsby' and pg.is_visible('#ldDelete') and pg.is_visible('#ldDone'))
    ok('its buildings ticked', ev("() => [...document.querySelectorAll('.ld-bld input')].map(i => i.checked)") == [True, False])
    pg.fill('#ldName', 'Gus'); pg.fill('#ldRole', 'Chief of the cleanup crew'); pg.wait_for_timeout(300)
    ok('the name and role change as they are typed', leaders()[0][:2] == ['Gus', 'Chief of the cleanup crew'])
    pg.click('.ld-swatch[title="#F2C75C"]'); pg.wait_for_timeout(250)
    ok('so does the color', leaders()[0][2] == '#F2C75C')
    pg.fill('#ldName', ''); pg.press('#ldName', 'Tab'); pg.wait_for_timeout(200)
    ok('an emptied name reads as Leader', leaders()[0][0] == 'Leader')
    pg.fill('#ldName', 'Gus Grimsby'); pg.wait_for_timeout(200)
    pg.check(f'.ld-bld[data-id="{nc}"] input'); pg.wait_for_timeout(200)
    ok('ticking a building gives it the leader at once', lead(nc) == gid)
    pg.uncheck(f'.ld-bld[data-id="{nc}"] input'); pg.wait_for_timeout(200)
    ok('and unticking takes it away', lead(nc) == '')
    pg.click('.ld-portrait-btns >> text=Remove'); pg.wait_for_timeout(300)
    ok('Remove takes the portrait out of the art store, back to the silhouette', ev(f"async () => !(await Store.getArt('leader:{gid}')) && !DB.leaders[0].portrait && !Leaders.url('{gid}')")
       and ev("() => !!document.querySelector('.ld-big svg')"))
    pg.set_input_files('.ld-panel input[type=file]', GUS); pg.wait_for_timeout(500)
    ok('a portrait uploaded while editing is kept at once', ev(f"async () => DB.leaders[0].portrait && (await Store.getArt('leader:{gid}')) === Leaders.url('{gid}')"))
    pg.click('#ldDone'); pg.wait_for_timeout(300)
    ok('Done goes back to the list, which already shows the changes, the focus on the leader', not pg.is_visible('.ld-panel')
       and ev(f"() => document.querySelector('.ld-row[data-id=\"{gid}\"] .ld-row-text b').textContent") == 'Gus Grimsby'
       and ev(f"() => document.activeElement === document.querySelector('.ld-row[data-id=\"{gid}\"]')"))
    row(gid)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc in the editor goes back to the list, and again closes the panel', ev("() => Leaders.isOpen() && !Leaders.editing()")
       and (pg.keyboard.press('Escape'), pg.wait_for_timeout(200), ev("() => !Leaders.isOpen()"))[2])

    # ---------- framing (0.1.52): every portrait fills its frame by its figure ----------
    urls = {'small': data_url(SMALL, 'png'), 'gus': data_url(GUS, 'png'), 'tall': data_url(TALL, 'jpeg'), 'gif': data_url(fixture('test-live.gif'), 'gif')}
    fr = ev("""async (u) => { const out = {}; for (const [k, v] of Object.entries(u)) out[k] = await Leaders.measure(v); return out; }""", urls)
    sm = fr['small']
    ok(f'a portrait drawn small is framed by its figure: a square round it, its foot on the frame\'s foot ({ {k: round(v, 2) for k, v in sm.items()} })',
       abs(sm['s'] - 95 / 0.97) < 0.01 and abs(sm['y'] + sm['s'] - 112) < 0.01 and abs(sm['x'] + sm['s'] / 2 - (19 + 83 / 2)) < 0.01 and sm['w'] == 128)
    ok(f'Gus, who fills his canvas, keeps his framing within 1% ({round(fr["gus"]["s"], 1)} of 256)', 253 <= fr['gus']['s'] <= 259)
    ok(f'a picture with no see-through pixels is cropped square, from the top when tall ({fr["tall"]})', fr['tall'] == {'x': 0, 'y': 0, 's': 100, 'w': 100, 'h': 160})
    shown = ev("""(u) => { const l = blankLeader({ color: '#B9A3E3' }), box = document.createElement('div');
        box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;display:flex;gap:8px';
        const faces = [Leaders.face(l, 64, { url: u.small }), Leaders.face(l, 128, { url: u.small }), Leaders.face(l, 64, { url: u.gus }), Leaders.face(l, 64, { url: u.gif })];
        box.append(...faces); document.body.append(box);
        const fig = (f, x0, y0, x1, y1) => { const i = f.querySelector('img'), r = i.getBoundingClientRect(), F = f.getBoundingClientRect(), k = r.width / i.naturalWidth;
          const by = new DOMMatrix(getComputedStyle(i).transform).m42;     // the breath (0.1.62): measured in its place, a pixel up from rest
          return { top: r.top - by + y0 * k - F.top, bottom: r.top - by + y1 * k - F.top, left: r.left + x0 * k - F.left, right: r.left + x1 * k - F.left, size: F.width,
            render: getComputedStyle(i).imageRendering, src: i.getAttribute('src').slice(0, 15), by, breathes: f.classList.contains('breathes') }; };
        const out = [fig(faces[0], 19, 17, 102, 112), fig(faces[1], 19, 17, 102, 112), fig(faces[2], 6, 8, 250, 256), fig(faces[3], 0, 0, 1, 1)];
        box.remove(); return out; }""", urls)
    a, big, g, gif = shown
    ok(f'on screen it fills the face: the figure 97% of its height, its foot on the face\'s foot, centred ({round(a["top"], 1)} to {round(a["bottom"], 1)} of 64)',
       abs((a['bottom'] - a['top']) - 0.97 * 64) < 0.5 and abs(a['bottom'] - 64) < 0.5 and abs((a['left'] + a['right']) / 2 - 32) < 0.5)
    ok(f'grown past its own size it stays in whole pixels; shrunk it is smooth ({big["render"]}, {g["render"]})', big['render'] == 'pixelated' and g['render'] == 'auto'
       and abs(big['bottom'] - 128) < 0.5)
    ok('Gus\'s figure still fills his face, foot on the foot', abs(g['bottom'] - 64) < 0.5 and g['top'] < 4)
    ok('an animated GIF stays the GIF itself, framed by its first frame', gif['src'] == 'data:image/gif;')
    ok(f'and every face breathes (0.1.62): the figure a pixel low at rest, in its place as it breathes in ({[x["by"] for x in shown]})', all(x['breathes'] and x['by'] in (0, 1) for x in shown))
    sizes = ev("""(u) => { const l = blankLeader({ color: '#B9A3E3' }), box = document.createElement('div');
        box.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;display:flex;gap:8px';
        const faces = [Leaders.face(l, 96, { url: u.small }), Leaders.face(l, 48, { url: u.small }), Leaders.face(l, 96, { url: u.gus }), Leaders.face(l, 48, { url: u.gus })];
        box.append(...faces); document.body.append(box);
        const fig = (f, y0, y1) => { const i = f.querySelector('img'), r = i.getBoundingClientRect(), F = f.getBoundingClientRect(), k = r.width / i.naturalWidth;
          const by = new DOMMatrix(getComputedStyle(i).transform).m42;
          return { size: Math.round(F.width), top: r.top - by + y0 * k - F.top, bottom: r.top - by + y1 * k - F.top, render: getComputedStyle(i).imageRendering }; };
        const out = [fig(faces[0], 17, 112), fig(faces[1], 17, 112), fig(faces[2], 8, 256), fig(faces[3], 8, 256)];
        box.remove(); return out; }""", urls)
    ok(f'at the leader card\'s 96 px and the status card\'s 48 px (0.1.57) the figure still fills the face, foot on the foot, shrunk smooth ({[(s["size"], round(s["top"], 1), round(s["bottom"], 1)) for s in sizes]})',
       [s['size'] for s in sizes] == [96, 48, 96, 48] and all(abs(s['bottom'] - s['size']) < 0.5 for s in sizes)
       and abs((sizes[0]['bottom'] - sizes[0]['top']) - 0.97 * 96) < 0.5 and abs((sizes[1]['bottom'] - sizes[1]['top']) - 0.97 * 48) < 0.5
       and all(s['render'] == 'auto' for s in sizes))
    row(pid)
    pg.set_input_files('.ld-panel input[type=file]', str(SMALL)); pg.wait_for_timeout(500)
    up = ev(f"""async () => {{ const u = Leaders.url('{pid}'), i = document.querySelector('.ld-big img');
        return {{ same: (await Store.getArt('leader:{pid}')) === u, framed: !!i && i.classList.contains('framed'), w: i && Math.round(parseFloat(i.style.width)),
          card: !!document.querySelector('#pvLeader') }}; }}""")
    ok(f'uploaded, the small portrait fills the panel\'s face, and the file is kept as it came ({up})', up['same'] and up['framed'] and up['w'] == round(128 * 128 / (95 / 0.97)))
    pg.screenshot(path=str(SHOTS / '348-leader-framed.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 330})
    pg.click('.ld-portrait-btns >> text=Remove'); pg.wait_for_timeout(300)
    pg.click('#ldDone'); pg.wait_for_timeout(300)
    ok('and removed again, as it was', ev(f"() => !getLeader('{pid}').portrait"))

    # ---------- Claude knows the leader ----------
    cl = ev(f"""() => {{ const p = getProject('{gp}'), t = p.todos.find(t => !t.done), m = p.milestones[0];
        const n = {{ id: 'n1', title: 'Idea', text: 'Some text', at: Date.now() }};
        return {{ task: taskForClaude(p, t).split('\\n').slice(0, 3), note: noteForClaude(p, n).split('\\n').slice(0, 3), ms: milestoneForClaude(p, m).split('\\n').slice(0, 3),
          status: projectStatus(p).split('\\n').slice(0, 2), brief: statusBrief().includes('## Garden planner\\nLeader: Gus Grimsby, Chief of the cleanup crew.'),
          other: [taskForClaude(getProject('{nc}'), getProject('{nc}').todos[0]), projectStatus(getProject('{nc}'))].some(s => s.includes('Leader:')) }}; }}""")
    LINE = 'Leader: Gus Grimsby, Chief of the cleanup crew'
    ok(f'Copy task names the leader after the project ({cl["task"][1:]})', cl['task'][2] == LINE and cl['task'][1] == 'Project: Garden planner')
    ok('so do a note\'s and a milestone\'s copies', cl['note'][2] == LINE and cl['ms'][2] == LINE)
    ok(f'the project\'s status, and so the status brief ({cl["status"]})', cl['status'] == ['## Garden planner', LINE + '.'] and cl['brief'])
    ok('a building with no leader has no Leader line', cl['other'] is False)
    sm = ev("() => { const s = ClaudeWork.citySummary(); return { leaders: s.leaders, gp: s.projects.find(p => p.name === 'Garden planner').leader, nc: s.projects.find(p => p.name === 'Nullovation City').leader }; }")
    ok(f'the city summary lists the leaders with what they lead ({sm["leaders"]})', sm['leaders'] == [{'name': 'Gus Grimsby', 'role': 'Chief of the cleanup crew', 'projects': ['Garden planner']},
       {'name': 'Proxima Pace', 'role': 'Productivity Inspector', 'projects': []}])
    ok('and each project its leader, or null', sm['gp'] == {'name': 'Gus Grimsby', 'role': 'Chief of the cleanup crew'} and sm['nc'] is None)
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.click('#pv button:has-text("Copy task")')
    pg.wait_for_timeout(300)
    clip = ev("() => navigator.clipboard.readText()").replace('\r\n', '\n')
    ok('Copy task under What is next carries it', LINE in clip.split('\n')[:4])
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)

    # ---------- a reload ----------
    pg.reload(); pg.wait_for_timeout(2200)
    ok('after a reload: the leaders, their buildings and colors', leaders() == [['Gus Grimsby', 'Chief of the cleanup crew', '#F2C75C', True, ['Garden planner']],
       ['Proxima Pace', 'Productivity Inspector', '#8FD0F7', False, []]])
    panel()
    ok('the portrait comes back from the art store, in the Leaders panel', ev("() => { const t = document.querySelector('#ldList .ld-row img'); return !!t && t.src.startsWith('data:image/png'); }"))
    ev("() => Leaders.close(false)")
    ev(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(600)
    ok('and in the status card', ev("() => !!document.querySelector('#bubble .b-leader img')"))
    ev("() => MapView.deselect()")

    # ---------- a backup carries the leaders, portraits inline ----------
    pg.click('#btnOpenSettings'); pg.click('#setTabs [data-tab="saving"]'); pg.wait_for_timeout(150)
    with pg.expect_download() as dl:
        pg.click('#btnExport')
    bk = json.loads(pathlib.Path(dl.value.path()).read_text(encoding='utf-8'))
    (DATA / 'backup-leaders.json').write_text(json.dumps(bk), encoding='utf-8')
    bl = [(l['name'], l['role'], l['color'], l['portrait'], l.get('portraitUrl', '')[:22]) for l in bk.get('leaders', [])]
    ok(f'a backup carries every leader, the portrait inline ({bl})', bl == [('Gus Grimsby', 'Chief of the cleanup crew', '#F2C75C', True, 'data:image/png;base64,'), ('Proxima Pace', 'Productivity Inspector', '#8FD0F7', False, '')])
    ok('and each building\'s leader', {pp['name']: pp.get('leader') for pp in bk['projects']} == {'Garden planner': gid, 'Nullovation City': ''})
    pg.click('#setBack'); pg.wait_for_timeout(150)

    # ---------- a project's export carries its leader ----------
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    pg.click('#pvMore')
    with pg.expect_download() as dl:
        pg.click('.pv-menu-item >> text=Export this project')
    one = json.loads(pathlib.Path(dl.value.path()).read_text(encoding='utf-8'))
    (DATA / 'one-project-leader.json').write_text(json.dumps(one), encoding='utf-8')
    ld = one.get('leader') or {}
    ok(f'Export this project carries its leader: name, role, color and portrait ({ {k: v[:22] for k, v in ld.items()} })', ld.get('name') == 'Gus Grimsby' and ld.get('role') == 'Chief of the cleanup crew'
       and ld.get('color') == '#F2C75C' and ld.get('portraitUrl', '').startswith('data:image/png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    n0 = ev("() => DB.leaders.length")
    pg.set_input_files('#fileImport', str(DATA / 'one-project-leader.json')); pg.wait_for_timeout(800)
    cp = ev("() => DB.projects.filter(p => p.name === 'Garden planner').map(p => p.leader)")
    ok('imported into the same city, it keeps the leader of the same name, adding none', ev("() => DB.leaders.length") == n0 and cp == [gid, gid])

    # ---------- deleting a leader ----------
    row(gid)
    pg.click('#ldDelete'); pg.wait_for_timeout(250)
    body = pg.text_content('#cfBody')
    ok(f'Delete leader asks first, naming what happens ({body})', pg.text_content('#cfTitle') == 'Delete Gus Grimsby?'
       and body == 'Their 2 buildings keep running, with no leader. The portrait is removed from this browser.')
    pg.click('.backdrop.top .confirm-actions .btn:not(.btn-danger)'); pg.wait_for_timeout(200)
    ok('Cancel keeps it', ev("() => DB.leaders.length") == n0 and pg.is_visible('.ld-panel'))
    pg.click('#ldDelete'); pg.wait_for_timeout(250)
    quiet(); pg.click('.backdrop.top .btn-danger'); pg.wait_for_timeout(400)
    ok(f'confirmed, it goes, with a toast, back to the list ({toasted()})', toasted() == 'Deleted Gus Grimsby.' and not pg.is_visible('.ld-panel') and leaders() == [['Proxima Pace', 'Productivity Inspector', '#8FD0F7', False, []]]
       and pg.is_visible('#ldList') and not ev(f"() => !!document.querySelector('.ld-row[data-id=\"{gid}\"]')"))
    ok('its buildings keep running with no leader, and its portrait leaves the art store',
       ev("() => DB.projects.every(p => p.leader === '')") and ev(f"async () => !(await Store.getArt('leader:{gid}'))"))
    row(pid); pg.click('#ldDelete'); pg.wait_for_timeout(250)
    ok('a leader with no building and no portrait: "Nothing else changes."', pg.text_content('#cfBody') == 'Nothing else changes.')
    pg.click('.backdrop.top .btn-danger'); pg.wait_for_timeout(400)
    ok('with the last one gone, the panel says how to start again', ev("() => DB.leaders.length === 0 && !!document.querySelector('#ldList .ld-empty')"))

    # ---------- a saved building whose leader is missing ----------
    ev("() => { const d = JSON.parse(localStorage.getItem('nullovation-city:v1')); d.projects[0].leader = 'ld-missing'; localStorage.setItem('nullovation-city:v1', JSON.stringify(d)); }")
    pg.reload(); pg.wait_for_timeout(2000)
    ok('a saved building whose leader is not in the city loads with none', ev("() => DB.projects.every(p => p.leader === '')"))
    # on a narrow window the Leaders panel opens in the drawer, as All tasks does (0.1.61)
    pg.set_viewport_size({'width': 700, 'height': 800}); pg.wait_for_timeout(300)
    pg.click('#menuToggle'); pg.wait_for_timeout(300)
    pg.click('#btnOpenLeaders'); pg.wait_for_timeout(300)
    nar = ev("() => { const p = document.querySelector('#leadersPanel').getBoundingClientRect(); return [document.querySelector('#menu').classList.contains('open'), Leaders.isOpen(), Math.round(p.right) <= 700, document.documentElement.scrollWidth <= 700]; }")
    ok(f'on a narrow window it opens in the drawer, with nothing past its edge ({nar})', nar == [True, True, True, True])
    pg.click('#btnNewLeader'); pg.wait_for_timeout(250)
    ok('and the editor fits there too', ev("() => { const e = document.querySelector('#ldEdit').getBoundingClientRect(); return !document.querySelector('#ldEdit').hidden && e.right <= 700 && e.width > 200; }"))
    pg.screenshot(path=str(SHOTS / '349-leaders-narrow.png'))
    b.close()

# ---------- a fresh browser: the backup and the project file bring their leaders ----------
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page(); watch(pg)
    pg.goto(FILE); pg.wait_for_timeout(1800)
    ev = pg.evaluate
    pg.set_input_files('#fileImport', str(DATA / 'one-project-leader.json')); pg.wait_for_timeout(800)
    nl = ev("() => DB.leaders.map(l => [l.name, l.role, l.color, l.portrait])")
    ok(f'a project file into a city without its leader brings the leader, portrait and all ({nl})', nl == [['Gus Grimsby', 'Chief of the cleanup crew', '#F2C75C', True]]
       and ev("async () => { const l = DB.leaders[0]; return (await Store.getArt('leader:' + l.id)) === Leaders.url(l.id) && DB.projects.filter(p => p.leader === l.id).length === 1; }"))
    pg.set_input_files('#fileImport', str(DATA / 'backup-leaders.json')); pg.wait_for_timeout(300)
    pg.click('.confirm-actions .btn-danger'); pg.wait_for_timeout(1000)
    rl = ev("() => DB.leaders.map(l => [l.name, l.color, l.portrait, leaderProjects(l).map(p => p.name)])")
    ok(f'importing a backup replaces the leaders with its own ({rl})', rl == [['Gus Grimsby', '#F2C75C', True, ['Garden planner']], ['Proxima Pace', '#8FD0F7', False, []]])
    ok('their portraits go into the art store, and show', ev("async () => { const l = DB.leaders[0]; Leaders.open(); Leaders.renderSection(); return (await Store.getArt('leader:' + l.id)) === Leaders.url(l.id) && !!document.querySelector('#ldList .ld-row img'); }"))
    old = ev("() => DB.leaders[0].id")
    pg.set_input_files('#fileImport', fixture('backup-v1.json')); pg.wait_for_timeout(300)
    pg.click('.confirm-actions .btn-danger'); pg.wait_for_timeout(1000)
    ok('a backup from before leaders brings none, and clears the old portraits', ev("() => DB.leaders.length === 0 && DB.projects.every(p => p.leader === '')")
       and ev(f"async () => !(await Store.getArt('leader:{old}'))"))
    b.close()

print(errors or 'no console errors')
