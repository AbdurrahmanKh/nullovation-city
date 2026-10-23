"""The leaders come alive (0.1.62), the fifth piece of the leader UX (Leader UX, Round 1 E1): wherever a leader's face
shows it breathes, rising a pixel and back every few seconds, each leader on its own slow rhythm; in its bubble the
line types out and the face bobs with it, then settles; Proxima breathes and talks too while she brings a building's
news in the leaders' place; Gus is as he was; and Motion on Still holds all of it."""
import json
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t41')) { sessionStorage.setItem('nc-t41', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    ev = pg.evaluate
    D = 86400000
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nc = ev("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    ev("() => { News._test.sayMs(60000); Garbage.setOn(false); }")
    keys_before = ev("() => Object.keys(localStorage).sort()")

    # two leaders: Talal, with a portrait, leads Garden planner; Sara, a silhouette, leads nothing yet
    ev(f"""async () => {{
        const t = blankLeader({{ name: 'Talal', role: 'Head of Nullovations', color: '#8FD0F7' }}), s = blankLeader({{ name: 'Sara', role: 'Archivist', color: '#B7A5F0' }});
        DB.leaders.push(t, s); setLeader(getProject('{gp}'), t.id);
        await Store.putArt(portraitKey(t.id), PORTRAITS.gus); t.portrait = true; persistNow(); await Leaders.loadAll(); }}""")
    tal, sar = ev("() => [DB.leaders[0].id, DB.leaders[1].id]")
    # a face: does it breathe, its rhythm, where it is in it, and the picture's offset now
    FACE = """el => { const pic = el && el.firstElementChild; if (!pic) return null; const a = pic.getAnimations()[0];
        const dur = parseFloat(getComputedStyle(el).getPropertyValue('--breath'));
        return { breathes: el.classList.contains('breathes'), anim: getComputedStyle(pic).animationName, dur,
          phase: a && a.effect.getComputedTiming().progress != null ? a.effect.getComputedTiming().progress * dur : null, y: new DOMMatrix(getComputedStyle(pic).transform).f, w: el.offsetWidth }; }"""
    face = lambda sel: ev(f"() => ({FACE})(document.querySelector({json.dumps(sel)}))")

    # ---------- a breathing face, wherever it shows ----------
    ev("() => Leaders.open()"); pg.wait_for_timeout(300)
    rt, rs = face(f'#ldList .ld-row[data-id="{tal}"] .ld-face'), face(f'#ldList .ld-row[data-id="{sar}"] .ld-face')
    ok(f'E1 in the Leaders panel each face breathes ({rt}, {rs})', rt and rs and rt['breathes'] and rs['breathes'] and rt['anim'] == rs['anim'] == 'face-breathe')
    ok(f'each leader on its own slow rhythm, a breath every 3.4 to 5.4 seconds ({rt and rt["dur"]}, {rs and rs["dur"]})',
       rt and rs and rt['dur'] != rs['dur'] and all(3400 <= x['dur'] <= 5400 for x in (rt, rs)))
    ok('a silhouette breathes too, with no portrait', ev(f"() => !!document.querySelector('#ldList .ld-row[data-id=\"{sar}\"] .ld-face.breathes > svg')"))
    kf = ev("() => document.querySelector('#ldList .ld-face.breathes > *').getAnimations()[0].effect.getKeyframes().map(k => [Math.round(k.computedOffset * 100), k.transform])")
    ok(f'a breath: a pixel low at rest, its place for a third of the time, back down ({kf})',
       [x[0] for x in kf] == [0, 60, 94, 100] and kf[0][1] == kf[2][1] == 'translateY(1px)' and kf[1][1] in ('translateY(0)', 'translateY(0px)'))
    ok('in whole pixels, never sliding', ev("() => getComputedStyle(document.querySelector('#ldList .ld-face.breathes > *')).animationTimingFunction").replace(' ', '') in ('steps(1,end)', 'steps(1)'))

    # frames of one face: two pictures only, the second the first a pixel higher, its foot never lifting off the frame
    box = pg.locator(f'#ldList .ld-row[data-id="{tal}"] .ld-face').bounding_box()
    shots, seen = [], {}
    for i in range(36):
        pg.screenshot(path=str(SHOTS / '_t41.png'), clip=box)
        im = Image.open(SHOTS / '_t41.png').convert('RGB'); k = im.tobytes()
        if k not in seen: seen[k] = im
        if len(seen) >= 2 and i > 8: break
        pg.wait_for_timeout(180)
    ims = list(seen.values())
    def lifted(a, c):
        w, hh = a.size
        return ImageChops.difference(a.crop((0, 1, w, hh)), c.crop((0, 0, w, hh - 1))).getbbox() is None
    pair = None
    if len(ims) == 2: pair = (ims[0], ims[1]) if lifted(ims[0], ims[1]) else (ims[1], ims[0]) if lifted(ims[1], ims[0]) else None
    ok(f'on screen the face takes two pictures, the second the first a pixel higher ({len(ims)} seen)', pair is not None)
    if pair:
        rest, up = pair; w, hh = rest.size
        bg = (0x8F, 0xD0, 0xF7)
        ok('at rest and lifted, its foot still fills the frame\'s foot: no gap opens under it', all(im.getpixel((w // 2, hh - 1)) != bg for im in (rest, up)))
        sheet = Image.new('RGB', (w * 8 + 16, hh * 4), (33, 28, 48))
        sheet.paste(rest.resize((w * 4, hh * 4), Image.NEAREST), (0, 0)); sheet.paste(up.resize((w * 4, hh * 4), Image.NEAREST), (w * 4 + 16, 0))
        sheet.save(SHOTS / '411-alive-breath.png')

    # the status card, the leader card, the wheel, the toast and Reports: the same breath, in step with the panel's
    ev("() => Leaders.close(false)")
    ev(f"() => Bubble.open('{gp}')"); pg.wait_for_timeout(400)
    sc = face('#bubble .b-leader .ld-face')
    ok(f'the status card\'s face breathes ({sc})', sc and sc['breathes'] and sc['anim'] == 'face-breathe' and sc['w'] == 48)
    ev("() => Leaders.open()"); pg.wait_for_timeout(200)
    sync = ev(f"""() => {{ const f = {FACE}; const a = f(document.querySelector('#ldList .ld-row[data-id="{tal}"] .ld-face')), c = f(document.querySelector('#bubble .b-leader .ld-face'));
        const d = Math.abs(a.phase - c.phase); return Math.min(d, a.dur - d); }}""")
    ok(f'a leader\'s faces breathe together, wherever they show ({sync and round(sync)} ms apart)', sync is not None and sync < 60)
    late = ev(f"""async () => {{ const f = {FACE}, box = document.createElement('div'); box.style.display = 'none'; document.body.append(box);
        box.append(Leaders.face(getLeader('{tal}'), 48)); await new Promise(r => setTimeout(r, 900)); box.style.display = 'block';
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        const a = f(box.firstElementChild), c = f(document.querySelector('#bubble .b-leader .ld-face')); box.remove();
        const d = Math.abs(a.phase - c.phase); return Math.min(d, a.dur - d); }}""")
    ok(f'a face drawn while hidden falls in step once it shows ({late and round(late)} ms apart)', late is not None and late < 60)
    ev("() => Leaders.close(false)"); ev("() => Bubble.close()")
    ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(600)
    lc = face('#pvLeader .ld-face')
    ok(f'the leader card\'s face breathes, at 96 px ({lc})', lc and lc['breathes'] and lc['anim'] == 'face-breathe' and lc['w'] == 96)
    ev("() => FullView.close()"); pg.wait_for_timeout(300)
    ev(f"() => Wheel.open(getProject('{gp}'), 600, 400)"); pg.wait_for_timeout(250)
    wh = face('.wheel-hub .ld-face')
    ok(f'the wheel\'s middle breathes, round ({wh})', wh and wh['breathes'] and wh['anim'] == 'face-breathe' and ev("() => document.querySelector('.wheel-hub .ld-face').classList.contains('round')"))
    ev("() => Wheel.close()")
    ev("() => QuickAdd.open({ text: '/garden-planner Weed the paths ' })"); pg.wait_for_timeout(200); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    tf = face('.toast-lead .ld-face')
    ok(f'the toast\'s face breathes ({tf})', tf and tf['breathes'] and tf['anim'] == 'face-breathe' and tf['w'] == 40)
    wid = ev(f"() => getProject('{gp}').todos.find(t => t.text === 'Weed the paths').id")
    ev(f"() => {{ const p = getProject('{gp}'); tickTask(p, p.todos.find(t => t.id === '{wid}')); changed(p); }}"); pg.wait_for_timeout(300)
    ev("() => Reports.open()"); pg.wait_for_timeout(500)
    rp = face('.rp-row .rp-leader')
    ok(f'Reports\' face breathes ({rp})', rp and rp['breathes'] and rp['anim'] == 'face-breathe')
    ev("() => Reports.close()"); pg.wait_for_timeout(200)

    # ---------- talking in its bubble ----------
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency = {{ system: 'pace', days: 1, lastWorked: Date.now() - 3600e3, pickedAt: Date.now() - 30 * {D} }}; changed(p); }}")
    pg.wait_for_timeout(400)
    LINE = 'We slipped behind our pace. Draw the beds on a grid puts us back on track.'
    TALK = """() => { const t = document.querySelector('#ldSayText'), f = document.querySelector('#ldSayFace'), b = document.querySelector('#ldSay');
        return { shown: !b.hidden, typing: t.classList.contains('typing'), on: t.querySelectorAll('.ty.on').length, all: t.querySelectorAll('.ty').length, text: t.textContent,
          talking: f.classList.contains('talking'), anim: f.querySelector('.breathes > *') ? getComputedStyle(f.querySelector('.breathes > *')).animationName : '',
          seen: [...t.querySelectorAll('.ty')].filter(x => getComputedStyle(x).opacity === '1').length, h: Math.round(b.getBoundingClientRect().height),
          link: !!t.querySelector('button.ld-task'), plain: [...t.childNodes].every(n => n.nodeType === 3 || n.matches('button.ld-task')) }; }"""
    talk = lambda: ev(TALK)
    ev(f"() => {{ const p = getProject('{gp}'); p.urgency.lastWorked = Date.now() - 1.5 * {D}; changed(p); }}")
    pg.wait_for_timeout(120)
    t0 = talk()
    ok(f'E1 the bubble opens and its line types out ({t0["on"]} of {t0["all"]} letters)', t0['shown'] and t0['typing'] and 0 < t0['all'] and t0['on'] < t0['all'] and t0['seen'] == t0['on'])
    ok('every letter is in the line from the start, so a screen reader hears it whole, once', t0['text'] == LINE and t0['all'] == len(LINE))
    ok(f'the face bobs while it talks ({t0["anim"]})', t0['talking'] and t0['anim'] == 'face-talk')
    ok('the task stays a link while it types', t0['link'])
    pg.wait_for_timeout(250)
    mid = talk()
    ev("() => News.redraw()")
    mid2 = talk()
    ok(f'drawn again mid-line (a portrait loading, news joining), it carries on where it was ({mid["on"]} then {mid2["on"]})', mid2['typing'] and mid2['on'] >= mid['on'] > t0['on'])
    pg.wait_for_timeout(250)
    box = pg.locator('#ldSay').bounding_box(); pg.screenshot(path=str(SHOTS / '410-alive-typing.png'), clip=box)
    pg.wait_for_timeout(1800)
    t1 = talk()
    ok(f'a long line types out in under 2 seconds, then the face settles and breathes ({t1["anim"]})', not t1['typing'] and t1['all'] == 0 and not t1['talking'] and t1['anim'] == 'face-breathe')
    ok(f'the bubble kept its size the whole time ({t0["h"]}, {t1["h"]})', t0['h'] == t1['h'])
    ok('the line is plain words again, the task its link', t1['text'] == LINE and t1['plain'] and t1['link'])
    ev("() => News.redraw()")
    ok('a line said already stays whole when drawn again', not talk()['typing'])
    tb = face('#ldSayFace .ld-face')
    ok(f'the bubble\'s face breathes too, at 100 px ({tb})', tb and tb['breathes'] and tb['w'] == 100)

    # Next types the next line; closing, and opening it again from the face, types it again
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: '2 tasks' }})"); pg.wait_for_timeout(150)
    ok('news joining the bubble leaves the line on show as it is', not talk()['typing'] and ev("() => document.querySelector('#ldSayCount').textContent") == '1 of 2')
    pg.click('#ldSayNext'); pg.wait_for_timeout(60)
    n1 = talk()
    ok(f'Next types the next line ({n1["text"]})', n1['typing'] and n1['text'] == 'Claude added 2 tasks.' and n1['talking'])
    pg.wait_for_timeout(1000)
    ok('and settles', not talk()['typing'] and not talk()['talking'])
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'a note' }})"); pg.wait_for_timeout(1300)
    pg.click('#ldSayClose'); pg.wait_for_timeout(300)
    ok('closed, it stops talking', not talk()['shown'] and not talk()['talking'])
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: '1 link' }})"); pg.wait_for_timeout(60)
    ok('the next bubble types its line again', talk()['typing'])
    pg.wait_for_timeout(1200); pg.click('#ldSayClose'); pg.wait_for_timeout(300)

    # ---------- Proxima, in the leaders' place, and Gus as he was ----------
    ev(f"() => News.add(getProject('{nc}'), 'added', {{ what: '3 tasks' }})"); pg.wait_for_timeout(80)
    px = talk(); pf = face('#ldSayFace .gus-face')
    ok(f'Proxima, bringing a building with no leader\'s news, talks and breathes as a leader does ({pf})', px['typing'] and px['talking'] and pf and pf['breathes'] and pf['w'] == 100)
    pg.wait_for_timeout(1200); pg.click('#ldSayClose'); pg.wait_for_timeout(300)
    ev(f"() => News.add(getProject('{nc}'), 'added', {{ what: '1 note' }})"); pg.wait_for_timeout(1300)
    ev("() => News.hide({ read: false })"); pg.wait_for_timeout(200)
    nf = face('#newsList .news-tile[data-k="px"] .gus-face')
    ok(f'her face in News breathes ({nf})', nf and nf['breathes'] and nf['anim'] == 'face-breathe')
    ev(f"() => Bubble.open('{nc}')"); pg.wait_for_timeout(400)
    ok('and in the status card of a building with no leader', (face('.b-leader .gus-face') or {}).get('breathes') is True)
    ev("() => Bubble.close()")
    ev(f"""() => {{ Garbage.setOn(true); const p = getProject('{nc}'); const t = p.todos.find(t => !t.done); t.due = ymd(Date.now() - 4 * {D}); changed(p); }}"""); pg.wait_for_timeout(1500)
    ev("() => Gus.hush && Gus.hush()"); pg.wait_for_timeout(200)
    g = ev("() => { const f = document.querySelector('#newsList .news-tile[data-k=\"gus\"] .gus-face'); return f && [f.classList.contains('breathes'), getComputedStyle(f.firstElementChild).animationName]; }")
    ok(f'Gus is as he was: his face holds still ({g})', g == [False, 'none'])

    # ---------- Motion on Still holds both ----------
    ev("() => { Motion.set('still'); Leaders.open(); }"); pg.wait_for_timeout(100)
    st = face(f'#ldList .ld-row[data-id="{tal}"] .ld-face')
    ev("() => Leaders.close(false)")
    ok(f'Still: the page wears m-still, and every face rests a pixel low, not breathing ({st})',
       ev("() => document.documentElement.classList.contains('m-still')") and st and st['anim'] == 'none' and st['y'] == 1)
    ev(f"() => News.add(getProject('{gp}'), 'added', {{ what: '4 tasks' }})"); pg.wait_for_timeout(60)
    s = talk()
    ok(f'Still: a line shows whole at once, the face still ({s})', s['shown'] and not s['typing'] and s['all'] == 0 and s['text'] == 'Claude added 4 tasks.' and not s['talking'] and s['anim'] == 'none')
    pg.click('#ldSayClose'); pg.wait_for_timeout(200)
    ev("() => Motion.set(null)")
    ok('back to following the system, the page leaves m-still', not ev("() => document.documentElement.classList.contains('m-still')"))
    pg.emulate_media(reduced_motion='reduce'); pg.wait_for_timeout(150)
    ok('a system that asks for reduced motion holds the faces still too, as it does the map', ev("() => document.documentElement.classList.contains('m-still') && Motion.still()"))
    pg.emulate_media(reduced_motion='no-preference'); pg.wait_for_timeout(150)
    ok('and lets them breathe again when it stops asking', not ev("() => document.documentElement.classList.contains('m-still')"))

    # ---------- nothing new kept ----------
    ok('nothing new in the city or this browser', ev("() => Object.keys(DB.leaders[0]).sort().join(',')") == 'color,createdAt,id,name,portrait,role'
       and set(ev("() => Object.keys(localStorage).sort()")) <= set(keys_before) | {'nullovation-city:news', 'nullovation-city:gus', 'nullovation-city:motion', 'nullovation-city:reports', 'nullovation-city:ui'})
    (SHOTS / '_t41.png').unlink(missing_ok=True)
    ok('no console errors', not errors, errors)
    b.close()
