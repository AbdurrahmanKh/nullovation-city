"""City sounds (0.1.78 and 0.1.79, City Sounds, Rounds 1 and 2): the events, then the city's own sounds.

Tasks and alerts in the SNES era style, the street party and the characters' voices in the 8-bit chip style (S1); since
0.1.79 the city's hum following Time of day, street life following the traffic on screen and the cleanup, in the SNES
era style, with no sharp sound among them (O1, his note). Sound
is on by default from the first click, tap or key (C1); the Sound button on the bar and in Settings, in step (C2); a
volume for each group as his Round 2 note groups them (C3); out of view only Claude Code's alerts play, the Claude folder
read while hidden too (C4); a sound with a place is panned by where it is on screen and a little louder zoomed in (C5).
Every sound is rendered offline for its level, since a test has no ears. The page's out of view is faked by giving
document.hidden a value the test sets; a Claude folder is held in memory, as in test24."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
HIDDEN = """window.__hidden = false;
Object.defineProperty(document, 'hidden', { configurable: true, get: () => window.__hidden });
Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => (window.__hidden ? 'hidden' : 'visible') });"""
def S(session, state, cwd, mins=0, **kw):
    """A session file as the hooks write it, last heard from mins minutes ago."""
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(cwd)}, at: {at}, since: {at}, started: {at} - 300000{extra} }})"
GARDEN = 'C:\\Users\\me\\garden'

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script(FAKE)
    ctx.add_init_script(HIDDEN)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    js = pg.evaluate
    log = lambda: js("() => Sound._test.log()")
    wears = lambda sel, name, size: js(f"() => {{ const s = document.createElement('span'); s.innerHTML = iconSvg('{name}', {size}); return document.querySelector('{sel}').innerHTML === s.innerHTML; }}")
    said = lambda: [x['id'] for x in log() if x['group'] != 'city']     # the events; the city's own are read apart
    clear = lambda: js("() => Sound._test.clear()")
    ids = js("() => Object.fromEntries(DB.projects.map(p => [p.name, p.id]))")
    gp, nc = ids['Garden planner'], ids['Nullovation City']
    quiet = lambda: js("() => { MapView.deselect(); Gus.hush(); Proxima.hush(false); News.hide({ read: true }); const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; }")

    # ---------- nothing before the first click, tap or key (C1) ----------
    ok('on by default: All sounds', js("() => Sound.mode()") == 'all')
    ok('before a click, tap or key the city makes no audio at all (browsers play nothing before)', js("() => Sound._test.state()") == 'none')
    ok('a volume for each of his four groups, 80% each by default (C3, O1)', js("() => [Sound.GROUPS, Sound.GROUPS.map(g => Sound.vol(g))]") == [['city', 'alerts', 'voices', 'music'], [0.8] * 4])
    js(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => !t.done)); }}")
    ok('a tick before then plays nothing', said() == [])

    # ---------- the bar's button (C2) ----------
    order = js("() => [...document.querySelectorAll('.map-tools > button')].map(b => b.id)")
    ok(f'the Sound button sits on the bar after Time of day, before Postcard ({order})', order[:5] == ['btnTraffic', 'btnBubbles', 'btnLight', 'btnSound', 'btnPostcard'])
    bar = js("""() => { const b = document.querySelector('#btnSound'), l = document.querySelector('#soundLabel'), r = l.getBoundingClientRect();
      return { svg: !!b.querySelector('#soundIcon svg'), label: l.textContent, w: r.width, title: b.title, h: b.getBoundingClientRect().height,
        gear: document.querySelector('#btnSettings').getBoundingClientRect().height }; }""")
    ok(f"it wears its speaker alone, the words kept for a screen reader ({bar['label']})", bar['svg'] and bar['label'] == 'All sounds' and bar['w'] <= 1)
    ok('its tooltip says what plays', bar['title'] == 'Sound: every sound the city makes. Click to choose.')
    ok(f"as tall as the bar's other buttons ({bar['h']}, {bar['gear']})", abs(bar['h'] - bar['gear']) < 1)
    icons = js("() => ['sound', 'soundEvents', 'soundOff'].map(n => ICONS[n].length + 'x' + ICONS[n][0].length)")
    ok(f'three pixel icons on the bar\'s 10 px grid: two waves, one wave, a cross ({icons})', icons == ['10x10'] * 3)

    # the first click: on the side bar's empty part, where it opens nothing
    pg.mouse.click(150, 560); pg.wait_for_timeout(300)
    ok('the first click lets the audio start', js("() => Sound._test.state()") == 'running')
    ok('each group at its volume', js("() => Sound._test.levels()") == {'city': 0.8, 'alerts': 0.8, 'voices': 0.8, 'music': 0.8})

    pg.click('#btnSound'); pg.wait_for_timeout(200)
    drop = js("() => [...document.querySelectorAll('.dropup .dropup-btn')].map(b => [b.textContent, b.getAttribute('aria-pressed'), !!b.querySelector('svg')])")
    ok(f'its drop-up: All sounds (pressed), Events only and No sound, each with its icon ({drop})',
       [d[0] for d in drop] == ['All sounds', 'Events only', 'No sound'] and [d[1] for d in drop] == ['true', 'false', 'false'] and all(d[2] for d in drop))
    pg.screenshot(path=str(SH / '490-sound-dropup.png'), clip={'x': 700, 'y': 640, 'width': 740, 'height': 260})
    ok('the focus on the one picked', js("() => document.activeElement.dataset.value") == 'all')
    pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok('Events only picked with the keys: kept, with its toast', js("() => [Sound.mode(), localStorage.getItem('nullovation-city:sound').includes('events'), document.querySelector('#toast').textContent]")
       == ['events', True, 'Only events make sound now.'])
    ok('the bar wears its one wave and says so', js("() => document.querySelector('#soundLabel').textContent") == 'Events only' and wears('#soundIcon', 'soundEvents', 16))
    clear()
    js(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => !t.done)); }}")
    ok('Events only: a tick still plays', said() == ['tick'])
    pg.wait_for_timeout(500)
    ok('and the city\'s own sounds are what it leaves out: their group silent, the hum stopped', js("() => [Sound._test.levels().city, Sound._test.city()]") == [0, None])
    pg.click('#btnSound'); pg.wait_for_timeout(150); pg.click('.dropup-btn[data-value="off"]'); pg.wait_for_timeout(250)
    ok('No sound: every group silent, the toast says so', js("() => [Sound._test.levels(), document.querySelector('#toast').textContent]") == [{'city': 0, 'alerts': 0, 'voices': 0, 'music': 0}, 'The city is silent.'])
    clear()
    js(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => !t.done)); Sound.claude('done', p); Sound.bubble(); }}")
    ok('and nothing plays, a tick, an alert or a bubble', said() == [])
    ok('the bar wears the speaker crossed out', wears('#soundIcon', 'soundOff', 16))

    # ---------- Settings, the Sound tab (C2, C3) ----------
    open_settings(pg, 'sound')
    tabs = js("() => [...document.querySelectorAll('#setTabs .set-tab')].map(t => t.dataset.tab)")
    ok(f'a Sound tab after Look ({tabs})', tabs == ['city', 'life', 'look', 'sound', 'projects', 'saving', 'links'])
    ok('the tab wears the speaker', wears('#setTabs [data-tab="sound"] .set-tab-ic', 'sound', 18))
    row = js("() => [...document.querySelectorAll('#optSound .set-choice')].map(b => [b.textContent, b.getAttribute('aria-pressed')])")
    ok(f'the same three choices as the bar, in step: No sound pressed ({row})', row == [['All sounds', 'false'], ['Events only', 'false'], ['No sound', 'true']])
    ok('its note says what plays', js("() => document.querySelector('#soundNote').textContent") == 'The city makes no sound.')
    ok('with sound off, the volumes wait', js("() => ['#optVolCity', '#optVolAlerts', '#optVolVoices', '#optVolMusic'].every(s => document.querySelector(s).disabled)"))
    ok('the dot on the choice and on the tab', js("() => [document.querySelector('[data-set=\"sound\"]').classList.contains('changed'), document.querySelector('#setTabs [data-tab=\"sound\"]').classList.contains('changed')]") == [True, True])
    js("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; }")
    pg.click('#optSound .set-choice[data-value="all"]'); pg.wait_for_timeout(200)
    ok('All sounds from Settings: the bar follows, with no toast', js("() => [Sound.mode(), document.querySelector('#soundLabel').textContent, document.querySelector('#toast').textContent]") == ['all', 'All sounds', ''])
    vols = js("() => [...document.querySelectorAll('#setBody [data-tab=\"sound\"] .set-slider')].map(r => [r.querySelector('label').textContent, r.querySelector('output').textContent, r.querySelector('input').min, r.querySelector('input').max])")
    ok(f'four volumes, his groups: City sounds, Alerts, Character voices, Music, each 0 to 100% ({vols})', vols == [['City sounds', '80%', '0', '1'], ['Alerts', '80%', '0', '1'], ['Character voices', '80%', '0', '1'], ['Music', '80%', '0', '1']])
    notes = js("() => [...document.querySelectorAll('#setBody [data-tab=\"sound\"] .set-slider + .note')].map(n => n.textContent)")
    ok('City sounds is the hum, the buildings at work and the street now and then, louder zoomed in', all(w in notes[0] for w in ('hum', 'buildings at work', 'now and then', 'zoom', 'Claude Code')))
    ok('Alerts holds the tasks too, as his note grouped them', 'your tasks' in notes[1] and 'Claude Code' in notes[1] and "Gus's alarms" in notes[1])
    ok('Music is the street party', 'street party' in notes[3])
    js("() => { const i = document.querySelector('#optVolVoices'); i.value = 0.35; i.dispatchEvent(new Event('input')); }"); pg.wait_for_timeout(250)
    ok('a volume moved: kept, shown, dotted, and the group follows', js("() => [Sound.vol('voices'), document.querySelector('#optVolVoicesOut').textContent, document.querySelector('[data-set=\"volVoices\"]').classList.contains('changed'), Sound._test.levels().voices]") == [0.35, '35%', True, 0.35])
    pg.screenshot(path=str(SH / '491-sound-settings.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})
    pg.click('#btnTabReset'); pg.wait_for_timeout(200)
    ok('Reset to defaults puts the choice and the volumes back', js("() => [Sound.mode(), Sound.vol('voices'), document.querySelector('#setTabs [data-tab=\"sound\"]').classList.contains('changed')]") == ['all', 0.8, False])
    js("() => { const i = document.querySelector('#optVolMusic'); i.value = 0.5; i.dispatchEvent(new Event('input')); }"); pg.wait_for_timeout(100)
    close_settings(pg)
    pg.reload(); pg.wait_for_timeout(2000)
    ok('after a reload: kept on this computer, and nothing made before the first click', js("() => [Sound.vol('music'), Sound._test.state()]") == [0.5, 'none'])
    js("() => { Settings.resetTab('sound'); News._test.sayMs(60000); }")
    js("() => { const i = document.querySelector('#optVolMusic'); Sound.setVol('music', 0.5); }")
    pg.keyboard.press('Shift'); pg.wait_for_timeout(300)
    ok('a key lets it start too, as a click does', js("() => Sound._test.state()") == 'running')

    # ---------- the events: tasks (SNES era) ----------
    def tick_first(pid):
        js(f"() => {{ const p = getProject('{pid}'); const t = p.todos.find(t => isOpenTask(t)); tickTask(p, t); changed(p); }}")
    MapView_select = lambda pid: js(f"() => MapView.select('{pid}')")
    MapView_select(gp); pg.wait_for_timeout(500)
    clear()
    box = pg.locator('#bubble input[type="checkbox"]').first
    box.click(); pg.wait_for_timeout(300)
    lg = [x for x in log() if x['group'] != 'city']
    pl = js(f"() => Sound._test.placeOf('{gp}')")
    ok(f"a tick in the status card chimes, in the Alerts group ({[x['id'] for x in lg]})", [x['id'] for x in lg] == ['tick'] and lg[0]['group'] == 'alerts')
    ok(f"from its building's place: panned by where it is on screen, louder zoomed in ({lg[0]['pan']}, {lg[0]['gain']})", abs(lg[0]['pan'] - round(pl['pan'], 2)) < 0.02 and abs(lg[0]['gain'] - round(pl['zoom'], 2)) < 0.02)
    js("() => MapView.deselect()")
    cam = js("() => MapView.camState()")
    zs = js(f"""() => {{ const c = MapView.camState(), out = []; for (const z of [1, 2, 4, 8]) {{ MapView.setCam({{ x: c.x, y: c.y, z }}); out.push(Sound._test.placeOf('{gp}').zoom); }} MapView.setCam(c); return out; }}""")
    ok(f'zooming in makes it a little louder (his note on A1): 1x to 8x {[round(z, 2) for z in zs]}', zs == sorted(zs) and zs[0] >= 0.79 and zs[-1] <= 1.11 and zs[-1] > zs[0])
    side = js(f"""() => {{ const c = MapView.camState(), p = getProject('{gp}'), [x] = MapView.plotCss(p.plot.u, p.plot.v), w = document.querySelector('#mapWrap').clientWidth;
      MapView.setCam({{ x: c.x - (w / 2 - x + 300) / (c.z / c.dpr), y: c.y, z: c.z }}); const r = Sound._test.placeOf('{gp}').pan; MapView.setCam(c); return r; }}""")
    ok(f'a building to the right of the middle plays from the right ({round(side, 2)})', side > 0.3)
    clear()
    js(f"() => {{ const p = getProject('{gp}'); p.particles = 'coins'; }}"); tick_first(gp)
    js(f"() => {{ const p = getProject('{gp}'); p.particles = 'dollars'; }}"); tick_first(gp)
    js(f"() => {{ const p = getProject('{gp}'); p.particles = 'hearts'; }}"); tick_first(gp)
    ok(f'by the building\'s particles: coins clink for coins and dollars, the chime for the rest ({said()[:3]})', said()[:3] == ['coins', 'coins', 'tick'])
    pg.wait_for_timeout(2500); quiet()
    clear()
    js(f"() => {{ const p = getProject('{nc}'); const t = p.todos.find(t => isOpenTask(t)); t.repeat = {{ every: 'day', n: 1 }}; tickTask(p, t); changed(p); }}")
    ok('a repeat moving on has its own sound', said() == ['repeat'])
    clear()
    js(f"() => {{ const p = getProject('{nc}'); const t = p.todos.find(t => isOpenTask(t) && !t.repeat); setStar(p, t, true); setStar(p, t, true); }}")
    ok('a task starred: its twinkle, once', said() == ['star'])
    clear()
    pg.keyboard.press('KeyT'); pg.wait_for_timeout(250)
    pg.keyboard.type('/garden Weed the beds'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    ok(f'a task added from the line over the map ({said()})', said() == ['added'])
    quiet(); clear()
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(500)
    arch = pg.locator('.task .mark-archive').first
    arch.hover(); arch.click(); pg.wait_for_timeout(300)
    ok(f'a done task archived by hand files itself away ({said()})', said() == ['archive'])
    js("() => FullView.close()"); pg.wait_for_timeout(300); quiet()

    # ---------- the street party (8-bit chip) ----------
    clear()
    js("() => Celebrate._test.partyMs(3000)")
    js(f"""() => {{ const p = getProject('{gp}'), m = {{ id: uid('m'), name: 'Party test' }}; p.milestones.push(m);
      p.todos.push({{ id: uid('t'), text: 'First of two', done: true, doneAt: Date.now(), milestoneId: m.id, due: '', description: '' }});
      const t = {{ id: uid('t'), text: 'Last of two', done: false, milestoneId: m.id, due: '', description: '' }}; p.todos.push(t); changed(p); tickTask(p, t); changed(p); }}""")
    pg.wait_for_timeout(300)
    ok(f"a finished milestone's party: the tick, then the cheer and its music in the Music group ({said()})", 'party' in said() and [x['group'] for x in log() if x['id'] == 'party'] == ['music'])
    ok('the music plays while the party lasts', js(f"() => Sound._test.parties().includes('{gp}')"))
    pg.wait_for_timeout(1800)
    ok(f"Proxima announces it: a bubble's sound, then her radio chirp as her line types out ({said()})", 'bubble' in said() and 'voice:proxima' in said())
    ok('her line types out in her bubble, and her face talks', js("() => [document.querySelector('#pxSayText').classList.contains('typing') || document.querySelector('#pxSayText').textContent.length > 0, !!document.querySelector('#pxSay:not([hidden])')]") == [True, True])
    pg.wait_for_timeout(2000)
    ok('the party over: its music stops with it', js("() => Sound._test.parties()") == [])
    ok('her line whole again, plain words', js("() => [document.querySelector('#pxSayText .ty'), document.querySelector('#pxSayText').classList.contains('typing')]") == [None, False])
    off = js(f"""() => {{ const c = MapView.camState(), p = getProject('{gp}'), [x] = MapView.plotCss(p.plot.u, p.plot.v), w = document.querySelector('#mapWrap').clientWidth;
      MapView.setCam({{ x: c.x + (x + w * 0.6) / (c.z / c.dpr), y: c.y, z: c.z }}); const r = Sound._test.placeOf('{gp}'); MapView.setCam(c); return r; }}""")
    ok(f"a block out of view is quieter, from its side, never silent ({round(off['near'], 2)}, {round(off['pan'], 2)})", 0.3 <= off['near'] < 0.8 and off['pan'] < -0.6)
    quiet()

    # ---------- the characters' voices (8-bit chip): a blip per letter as the line types out ----------
    js("() => News._test.typeMs(26)")
    clear()
    js("() => Gus.say('The city is getting dirty! We should do something about it.')"); pg.wait_for_timeout(120)
    st = js("() => [document.querySelector('#gusSayText').classList.contains('typing'), document.querySelector('#gusSayFace').classList.contains('talking'), document.querySelector('#gusSayText').textContent]")
    ok(f"Gus's line types out now, his face talking, every letter there from the start ({said()})", st[0] and st[1] and st[2] == 'The city is getting dirty! We should do something about it.')
    ok("a bubble's sound as he speaks up by himself, and his low voice", said() == ['bubble', 'voice:gus'])
    pg.wait_for_timeout(2200)
    ok('then his line settles, whole and plain', js("() => [document.querySelector('#gusSayText .ty'), document.querySelector('#gusSayFace').classList.contains('talking')]") == [None, False])
    clear()
    js("() => Gus.say('The city is filthy! This is unacceptable!', true)"); pg.wait_for_timeout(150)
    ok(f"his alarm at 50 and 200 sounds his horn instead ({said()})", said() == ['gusAlarm', 'voice:gus'])
    quiet(); clear()
    js(f"""() => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Gardens', color: '#7FD6B5' }}); DB.leaders.push(l); getProject('{gp}').leader = l.id; window.__talal = l.id; changed(getProject('{gp}')); }}""")
    talal = js("() => window.__talal")
    js(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'a note' }})"); pg.wait_for_timeout(400)
    ok(f"a leader's bubble opening by itself: its sound, then the leader's own voice ({said()})", said() == ['bubble', 'voice:ld:' + talal])
    ok("the line types out as before", js("() => document.querySelector('#ldSayText').classList.contains('typing')"))
    clear()
    js("() => News.hide({ read: true })"); pg.wait_for_timeout(100)
    js(f"() => News.add(getProject('{nc}'), 'added', {{ what: 'a link' }})"); pg.wait_for_timeout(400)
    ok(f"a building with no leader: Proxima brings it, in her voice ({said()})", said() == ['bubble', 'voice:proxima'])
    js("() => News.hide({ read: true })"); clear()
    js(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Draw the beds', round: 'Beds, Round 1' }})"); pg.wait_for_timeout(400)
    ok(f"Quill's rounds in his sparkle voice ({said()})", said() == ['bubble', 'voice:quill'])
    js("() => News.hide({ read: true })"); clear()
    js("() => Motion.set('still')")
    js(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'two notes' }})"); pg.wait_for_timeout(400)
    ok(f'Motion on Still: the line shows whole, so no voice; the bubble still sounds ({said()})', said() == ['bubble'])
    js("() => { News.hide({ read: true }); Motion.set(null); }"); clear()
    js(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'three notes' }})"); pg.wait_for_timeout(300)
    js("() => News.hide({ read: true })"); pg.wait_for_timeout(100)
    ok('a bubble closed mid-line stops its voice with its line', js("() => News._test.talk().id") is None)
    quiet(); clear()

    # ---------- out of view, only Claude Code's alerts (C4) ----------
    js(f"""() => {{ const p = getProject('{gp}'); p.links.push({{ id: uid('l'), label: '', url: {json.dumps(GARDEN)}, icon: 'folder', shortcut: true }}); persistNow(); }}""")
    js(S('s-old', 'done', GARDEN, 1, task='Old work', reply='Done earlier.'))
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(600)
    js("() => { window.__cmark = true; }")
    close_settings(pg); pg.wait_for_timeout(3500)
    ok(f'what the folder holds when the city first reads it is old news: no alert ({said()})', 'finished' not in said())
    clear()
    js(S('s1', 'waiting', GARDEN, 0, task='Draw the beds')); pg.wait_for_timeout(3600)
    ok(f"in view: Claude Code waiting for you plays its alert, from its building's side ({said()})", said()[:1] == ['waiting'])
    quiet(); clear()
    js("() => { window.__hidden = true; document.dispatchEvent(new Event('visibilitychange')); }"); pg.wait_for_timeout(300)
    lv = js("() => Sound._test.levels()")
    ok(f'out of view: the city, the voices and the music go quiet, the alerts stay up ({lv})', lv == {'city': 0, 'alerts': 0.8, 'voices': 0, 'music': 0} and js("() => Sound._test.city()") is None)
    tick_first(gp); js("() => Gus.say('Clean streets. Don\\'t get used to it.')"); pg.wait_for_timeout(200)
    ok(f'a tick, a bubble or a voice out of view plays nothing ({said()})', said() == [])
    js("() => Gus.hush()"); clear()
    js(S('s1', 'done', GARDEN, 0, task='Draw the beds', reply='Drawn.')); pg.wait_for_timeout(3600)
    lg = [x for x in log() if x['group'] != 'city']
    ok(f"Claude Code finishing out of view: the city reads the folder anyway and plays its alert ({[x['id'] for x in lg]})", [x['id'] for x in lg] == ['finished'] and lg[0]['hidden'])
    clear()
    js(S('s2', 'failed', GARDEN, 0, task='Water the beds')); pg.wait_for_timeout(3600)
    ok(f'and stopping on an error ({said()})', said() == ['error'])
    clear()
    js(S('s1', 'ended', GARDEN, 0, task='Draw the beds', reply='Drawn.')); pg.wait_for_timeout(3600)
    ok('a session closed after it finished is no news: no second alert', said() == [])
    js("() => { window.__hidden = false; document.dispatchEvent(new Event('visibilitychange')); }"); pg.wait_for_timeout(3600)
    lv = js("() => Sound._test.levels()")
    ok(f"back in view: every group up again, and the map shows what came while away ({lv})", lv == {'city': 0.8, 'alerts': 0.8, 'voices': 0.8, 'music': 0.5} and js(f"() => !!MapView.claudeBubbleAt('{gp}')"))
    js("() => Sound.setMode('off')"); clear()
    js("() => { window.__hidden = true; document.dispatchEvent(new Event('visibilitychange')); }")
    js(S('s3', 'waiting', GARDEN, 0, task='Plan the herbs')); pg.wait_for_timeout(3600)
    ok('with No sound, the city does not read the folder while hidden, and nothing plays', said() == [] and not js("() => Sound.listening()"))
    js("() => { window.__hidden = false; document.dispatchEvent(new Event('visibilitychange')); Sound.setMode('all'); }"); pg.wait_for_timeout(300)
    quiet()

    # ---------- the city's own loop (0.1.80), as the third sound board played it ----------
    quiet(); js("() => { Light.setMode('day'); Traffic.setOn(true); MapView.syncBar(); }")
    home = js("() => MapView.camState()")
    look = lambda z: js(f"() => MapView.setCam({{ x: {home['x']}, y: {home['y']}, z: {z} }})")
    city = lambda: js("() => Sound._test.city()")
    cityLog = lambda: [x['id'] for x in log() if x['group'] == 'city']
    zl = {}
    for z in (1, 2, 3, 4, 6, 8):
        look(z); pg.wait_for_timeout(250); zl[z] = js("() => Sound._test.zoomLevel()")
    ok(f"the street and the buildings at work by the zoom, as he set them: 40, 60, 75, 90, 100, 100% ({list(zl.values())})", list(zl.values()) == [0.4, 0.6, 0.75, 0.9, 1, 1])
    look(2); pg.wait_for_timeout(300); clear(); rel0 = (city() or {}).get('counts', {}); pg.wait_for_timeout(9000)
    c = city()
    ok(f"by day at 2x: the street at 55% of 60%, the buildings at 60%, on two layers ({c})", c['street'] == 0.33 and c['work'] == 0.6 and c['layers'] == 2 and c['dark'] == 0)
    day = cityLog()
    ok(f"now and then, about every 4 to 5 seconds on each of two layers: a car, a honk, the bus, a drone, the bell ({day})", 2 <= sum(k in ('car', 'honk', 'bus', 'drone', 'bell') for k in day) <= 6 and set(day) <= {'car', 'honk', 'bus', 'drone', 'bell', 'truck'})
    ok('no crowd below the closest zoom', 'crowd' not in day)
    rel = city()['counts']
    runs = sum(rel.get(k, 0) - rel0.get(k, 0) for k in ('relay:clicks', 'relay:knocks'))
    ok(f"the relays clicking on top, runs 1.6 to 6 seconds apart ({runs} in 9 s)", 1 <= runs <= 6)
    ok(f"two kinds, a third of them knocks over the whole run ({rel.get('relay:clicks', 0)} clicks, {rel.get('relay:knocks', 0)} knocks)", rel.get('relay:knocks', 0) >= 1 and rel.get('relay:clicks', 0) >= rel.get('relay:knocks', 0) * 0.8)
    ok('no computers while no Claude Code session works', not city()['claude'] and not rel.get('bleep'))
    look(8); clear(); pg.wait_for_timeout(9000)
    at8 = cityLog()
    ok(f"at the closest zoom, the crowd on a layer of its own, every 3 to 9 seconds ({at8.count('crowd')} in 9 s)", 1 <= at8.count('crowd') <= 4)
    js("() => { DB.city.cars = false; DB.city.buses = false; DB.city.drones = false; }"); clear(); pg.wait_for_timeout(7000)
    only = set(cityLog())
    ok(f"who is out: with cars, buses and drones kept in, only the bell and the crowd ({only})", only <= {'bell', 'crowd'} and 'bell' in only)
    js("() => { DB.city.cars = true; DB.city.buses = true; DB.city.drones = true; Traffic.setOn(false); }"); clear(); pg.wait_for_timeout(6000)
    ok(f"Traffic off: the street is quiet and the hum plays on ({cityLog()}, {city()['layers']} layers)", cityLog() == [] and city() is not None and city()['layers'] == 0)
    js("() => Traffic.setOn(true)"); look(2)
    js("() => Light.setMode('night')"); clear(); pg.wait_for_timeout(9000)
    cn = city()
    ok(f"by night: the subtler hum, one layer, and the crickets ({cn['layers']} layer, {cn['counts'].get('cricket', 0)} chirps so far)", cn['dark'] == 1 and cn['layers'] == 1 and cn['counts'].get('cricket', 0) >= 3)
    night = [k for k in cityLog() if k != 'truck']
    ok(f"at night's pace, every 4 to 5 seconds on one layer ({night})", 1 <= len(night) <= 3)
    js("() => Light.setMode('day')")
    # Claude Code working anywhere: the computers at work and the power hum join, and go when it stops
    js(S('s9', 'working', GARDEN, 0, task='Water the beds')); pg.wait_for_timeout(5000)
    cw = city()
    ok(f"a Claude Code session working: the computers at work and the power hum join ({cw['claude']}, {cw['counts'].get('bleep', 0)} bleeps)", cw['claude'] and cw['counts'].get('bleep', 0) >= 1 and 'claude-works' in cityLog())
    js(S('s9', 'done', GARDEN, 0, task='Water the beds', reply='Watered.')); pg.wait_for_timeout(4500)
    ok('and they go when it stops working; the server room stays', not city()['claude'] and city() is not None)
    quiet()
    # a cleanup: the truck's hover hum as it sets off
    clear(); js(f"() => Garbage._test.force('{gp}', 24)"); pg.wait_for_timeout(600); js(f"() => Garbage._test.force('{gp}', 0)")
    for _ in range(20):
        if 'truck' in cityLog(): break
        pg.wait_for_timeout(300)
    ok('a garbage truck setting off plays its hover hum, in the City sounds group', 'truck' in cityLog())
    js("() => Sound.setVol('city', 0)"); pg.wait_for_timeout(500)
    ok('City sounds at 0: the loop stops', city() is None)
    js("() => Sound.setVol('city', 0.8)"); pg.wait_for_timeout(600)
    ok('back up: the loop again', city() is not None)
    open_settings(pg, 'sound'); js("() => Sound.setMode('events')"); js("() => Settings.refresh()")
    ok('Events only: the City sounds volume waits, the others do not', js("() => ['#optVolCity', '#optVolAlerts'].map(s => document.querySelector(s).disabled)") == [True, False])
    pg.screenshot(path=str(SH / '493-sound-settings-city.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})
    js("() => Sound.setMode('all')"); close_settings(pg)
    look(home['z'])

    # ---------- every sound rendered offline: its level without ears ----------
    res = js("async () => { const out = []; for (const id of Sound._test.ids()) out.push(await Sound._test.render(id, id === 'party' ? 10 : 5)); return out; }")
    bad = [r['id'] for r in res if r['bad'] or r['peak'] <= 0.02 or r['peak'] >= 0.9]
    ok(f"all {len(res)} sounds render: no bad sample, heard, never near clipping ({bad})", not bad and len(res) == 32)
    CITY_IDS = {'hum-day', 'hum-night', 'car', 'honk-double', 'honk-far', 'honk-beep', 'bus', 'drone', 'bell', 'crowd', 'truck', 'relays', 'server', 'computers', 'power', 'crickets'}
    loud = {r['id']: r['rmsDb'] for r in res if r['id'] not in CITY_IDS}
    ok(f"the events sit within 12 dB of each other ({min(loud.values())} to {max(loud.values())} dB)", max(loud.values()) - min(loud.values()) <= 12)
    by = {r['id']: r for r in res}
    ok(f"the night's hum subtler than the day's, by 6 dB or more ({by['hum-day']['rmsDb']}, {by['hum-night']['rmsDb']})", by['hum-day']['rmsDb'] - by['hum-night']['rmsDb'] >= 6)
    ok(f"the street's sounds sit with the day's hum, none above it by more than 3 dB ({ {k: by[k]['rmsDb'] for k in ('hum-day', 'car', 'bus', 'drone', 'truck')} })", all(by[k]['rmsDb'] <= by['hum-day']['rmsDb'] + 3 for k in ('car', 'bus', 'drone', 'truck', 'bell', 'crowd')))
    ok(f"the cyclist's bell, a far trill since 0.1.81, under a passing car ({by['bell']['rmsDb']} against {by['car']['rmsDb']} dB)", by['bell']['rmsDb'] < by['car']['rmsDb'] and by['bell']['seconds'] > 0.5)
    ok(f"the relays heard over the hum: their clicks peak above it ({by['relays']['peak']} against {by['hum-day']['peak']})", by['relays']['peak'] > by['hum-day']['peak'])
    ok('the party runs on (10 seconds rendered, music all the way)', [r for r in res if r['id'] == 'party'][0]['seconds'] > 9.5)
    print('NOTE levels: ' + ', '.join(f"{r['id']} {r['rmsDb']} dB pk {r['peak']}" for r in res))
    ctx.close()

    # ---------- a fresh computer with No sound kept: no audio is ever made ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { localStorage.setItem('nullovation-city:sound', JSON.stringify({ mode: 'off', vol: { alerts: 0.8, voices: 0.8, music: 0.8 } })); } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(1800)
    pg.mouse.click(150, 560); pg.keyboard.press('Shift'); pg.wait_for_timeout(200)
    ok('No sound kept: clicks and keys make no audio', pg.evaluate("() => Sound._test.state()") == 'none')
    pg.click('#btnSound'); pg.wait_for_timeout(150); pg.click('.dropup-btn[data-value="all"]'); pg.wait_for_timeout(300)
    ok('All sounds picked from the bar starts it, the click that picks it letting it start', pg.evaluate("() => Sound._test.state()") == 'running')
    ctx.close()

    # ---------- narrower windows: the bar never runs under the side bar ----------
    for w in (1280, 1100, 1024, 820):
        ctx = b.new_context(viewport={'width': w, 'height': 800}, device_scale_factor=1)
        ctx.add_init_script(TEST_CITY)
        pg = ctx.new_page(); pg.goto(FILE); pg.wait_for_timeout(1200)
        r = pg.evaluate("""() => { const t = document.querySelector('.map-tools').getBoundingClientRect(), m = document.querySelector('#menu').getBoundingClientRect(),
          k = document.querySelector('.keyhint'), l = document.querySelector('#trafficLabel').getBoundingClientRect();
          return { left: t.left, right: t.right, side: m.right, hint: getComputedStyle(k).display, words: l.width > 1 }; }""")
        ok(f"{w} px: the bar clear of the side bar ({round(r['left'])} > {round(r['side'])}), its words {'shown' if r['words'] else 'hidden as on a phone'}, the Q and E hint {'shown' if r['hint'] != 'none' else 'aside'}",
           r['left'] > r['side'] + 8 and r['words'] == (w > 1180) and (r['hint'] == 'none') == (w <= 1320))
        if w == 1024: pg.screenshot(path=str(SH / '492-sound-bar-1024.png'), clip={'x': 280, 'y': 720, 'width': 744, 'height': 80})
        ctx.close()
    b.close()

bad = [e for e in errors if 'favicon' not in e]
ok('no console errors' + (': ' + ' | '.join(bad[:3]) if bad else ''), not bad)
