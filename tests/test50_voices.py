"""Character voices (0.1.82): a leader picks its voice in its editor.

His rule: "a preset just change the settings below it". Every voice is one instrument, a blip per letter; a voice is
only its settings, and a preset only sets them. The editor's Voice: Its own (from its id, as since 0.1.78), five male,
five female and the city's three presets, a pitch slider, and Fine-tune with Tone, Range, Speed, Chatter, Length,
Wobble, Robot and Radio; no Kid ("I don't need the kid"). A pick or a slider let go says the leader's greeting in the
voice. A picked voice plays as loud as a leader's, as the voice board matched them. Quill's sparkle went. Gus, Proxima
and every leader without a picked voice sound exactly as before. A test has no ears: sounds are rendered offline."""
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

def fnv(s):
    x = 2166136261
    for c in s: x = ((x ^ ord(c)) * 16777619) & 0xFFFFFFFF
    return x
BASES, DUTY_TONE = [131, 147, 165, 175, 196, 220, 247], [0.85, 0.55, 0.25]   # duties 0.125, 0.25, 0.5, as tones

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    js = pg.evaluate
    pg.mouse.click(150, 560); pg.wait_for_timeout(300)                  # the first click, on the side bar's empty part, lets the audio start
    ids = js("() => Object.fromEntries(DB.projects.map(p => [p.name, p.id]))")
    gp = ids['Garden planner']
    said = lambda: [x['id'] for x in js("() => Sound._test.log()") if x['group'] == 'voices']
    clear = lambda: js("() => Sound._test.clear()")

    # ---------- the voices: one instrument, presets that only set its settings ----------
    pr = js("() => Sound.voices.presets.map(p => ({ id: p.id, group: p.group, name: p.name, keys: Object.keys(p.v).sort() }))")
    groups = {g: [x['name'] for x in pr if x['group'] == g] for g in ('male', 'female', 'city')}
    ok(f"13 presets: five male, five female, and the city's three ({groups})", groups == {'male': ['Deep', 'Gruff', 'Warm', 'Steady', 'Bright'], 'female': ['Low', 'Soft', 'Warm', 'Steady', 'Bright'], 'city': ['Gus', 'Proxima', 'Quill']} and len(pr) == 13)
    keys = sorted(['base', 'tone', 'range', 'speed', 'every', 'len', 'wobble', 'robot', 'radio', 'gain'])
    ok('every preset is the same settings, nothing more: no kid, no sparkle', all(x['keys'] == keys for x in pr))
    own = js("() => ['ld_a1', 'ld_b2', 'ld_c3', 'ld_x9q', 'x1'].map(id => { const v = Sound.voices.of('ld:' + id); return [id, v.base, v.tone, v.range, v.len, v.every, v.speed, v.gain, v.robot, v.radio]; })")
    want = [[i, BASES[fnv('ld:' + i) % 7], DUTY_TONE[(fnv('ld:' + i) >> 8) % 3], 4, 0.055, 2, 1, 1, False, False] for i in ['ld_a1', 'ld_b2', 'ld_c3', 'ld_x9q', 'x1']]
    ok("a leader with no voice picked keeps its own, from its id, as since 0.1.78", own == want, own)
    gus = js("() => [Sound.voices.of('gus'), Sound.voices.of('proxima'), Sound.voices.of('quill')]")
    ok("Gus, Proxima and Quill are the city's presets: Gus low with a blip every third letter, Proxima through her radio", gus[0]['base'] == 98 and gus[0]['every'] == 3 and gus[0]['tone'] == 0.25 and gus[1]['radio'] and gus[1]['base'] == 330 and gus[2]['base'] == 523)
    r = js("async () => [await Sound._test.render('voice:gus', 5), await Sound._test.render('voice:quill', 5), await Sound._test.render('voice:ld:x1', 5)]")
    ok(f"Gus and a leader sound as at 0.1.81 (peak, loudness, length: {[(x['peak'], x['rmsDb'], x['seconds']) for x in r]})", (r[0]['peak'], r[0]['rmsDb'], r[0]['seconds']) == (0.065, -28.3, 1.79) and (r[2]['peak'], r[2]['rmsDb'], r[2]['seconds']) == (0.072, -32.7, 1.79))
    ok(f"Quill's sparkle is gone: his line ends with its last letter ({r[1]['seconds']} s, 2.29 with the sparkle)", r[1]['seconds'] < 1.85 and not r[1]['bad'])

    # ---------- as loud as a leader's ----------
    g = js("async () => { const out = {}; for (const p of Sound.voices.presets) out[p.id] = await Sound.voices.loudness(p.v); out.leader = await Sound.voices.loudness(Sound.voices.make({ base: 196 })); out.robot = await Sound.voices.loudness({ ...Sound.voices.presets[3].v, robot: true }); return out; }")
    ok(f"the leaders' sound at 196 Hz is the measure, so its gain is 1 ({g['leader']})", g['leader'] == 1)
    ok(f"every preset gets a gain to play as loud as it, between a fifth and five times ({g})", all(0.2 <= v <= 5 for v in g.values()) and len(set(g.values())) > 5)
    ok('the soft triangle is turned down, as the voice board heard it', g['f-soft'] < 0.8)

    # ---------- the editor's Voice ----------
    lid = js(f"""() => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Gardens', color: '#B9A3E3' }}); DB.leaders.push(l); getProject('{gp}').leader = l.id; persistNow(); Leaders.refreshAll(); return l.id; }}""")
    before = js(f"() => {{ const p = getProject('{gp}'); return [p.updatedAt, p.activity.length]; }}")
    pg.click('#btnOpenLeaders'); pg.wait_for_timeout(200)
    pg.click(f'.ld-row[data-id="{lid}"]'); pg.wait_for_timeout(300)
    lay = js("""() => { const f = [...document.querySelectorAll('#ldEdit .ld-form > *')].map(e => e.className.split(' ').filter(c => c.startsWith('ld-')).pop() || e.className);
      const v = document.querySelector('.ld-voice'), r = v.getBoundingClientRect(), form = document.querySelector('#ldEdit .ld-form').getBoundingClientRect();
      return { order: f, label: v.querySelector('.ld-vhead .lbl').textContent, full: Math.round(r.width) >= Math.round(form.width) - 4,
        groups: [...v.querySelectorAll('.ld-vgroup')].map(g => [g.querySelector('.lbl') ? g.querySelector('.lbl').textContent : '', [...g.querySelectorAll('.ld-vchip')].map(c => c.textContent)]),
        pressed: [...v.querySelectorAll('.ld-vchip[aria-pressed="true"]')].map(c => c.textContent), line: document.querySelector('#ldVoiceLine').textContent,
        pitch: [document.querySelector('#ldV-pitch').min, document.querySelector('#ldV-pitch').max, document.querySelector('#ldV-pitch').value, document.querySelector('#ldV-pitch + output').textContent],
        fine: document.querySelector('#ldVFine').hidden, fineBtn: document.querySelector('.ld-vfine-btn').getAttribute('aria-expanded'),
        reset: document.querySelector('.ld-vreset').hidden, kid: /kid/i.test(v.textContent) }; }""")
    ok(f"the Voice section sits under Leads, across the editor ({lay['order']})", lay['order'].index('ld-voice') == lay['order'].index('ld-leads') + 1 and lay['label'] == 'Voice' and lay['full'])
    ok(f"its picks: Its own, then Male, Female and The city's ({lay['groups']})", lay['groups'] == [['', ['Its own']], ['Male', ['Deep', 'Gruff', 'Warm', 'Steady', 'Bright']], ['Female', ['Low', 'Soft', 'Warm', 'Steady', 'Bright']], ["The city's", ['Gus', 'Proxima', 'Quill']]])
    ok("a leader with no voice picked has Its own pressed, its greeting as the line, and no Kid anywhere", lay['pressed'] == ['Its own'] and ' Next up: ' in lay['line'] and not lay['kid'])
    own_hz = BASES[fnv('ld:' + lid) % 7]
    ok(f"the pitch slider, 12 semitones down to 12 up, in the middle at its note ({lay['pitch']})", lay['pitch'] == ['-12', '12', '0', f'{own_hz} Hz'])
    ok('Fine-tune folded, and nothing to go back to', lay['fine'] and lay['fineBtn'] == 'false' and lay['reset'])
    pg.screenshot(path=str(SH / '500-voice-editor.png'))

    clear()
    pg.click('#ldHear'); pg.wait_for_timeout(250)
    st = js("() => [document.querySelector('#ldVoiceLine').classList.contains('typing'), document.querySelector('#ldEdit .ld-big').classList.contains('talking'), document.querySelectorAll('#ldVoiceLine .ty').length]")
    ok(f"Hear it says its greeting in its voice: the line types out, the face talks ({said()})", st[0] and st[1] and st[2] > 20 and said() == ['voice:preview'])
    pg.wait_for_timeout(2200)
    ok('then the line settles, whole, and the face rests', js("() => [document.querySelector('#ldVoiceLine').classList.contains('typing'), document.querySelector('#ldEdit .ld-big').classList.contains('talking'), !!document.querySelector('#ldVoiceLine .ty')]") == [False, False, False])
    ok('nothing kept for Its own, heard', js(f"() => 'voice' in getLeader('{lid}')") is False)

    clear()
    pg.click('.ld-vchip[data-voice="f-soft"]'); pg.wait_for_timeout(500)
    v = js(f"() => getLeader('{lid}').voice")
    soft = js("() => Sound.voices.presets.find(p => p.id === 'f-soft').v")
    ok(f"a pick sets every setting to the preset's, and says the line in it ({said()})", v and v['from'] == 'f-soft' and v['pitch'] == 0 and all(v[k] == soft[k] for k in ('base', 'tone', 'range', 'speed', 'every', 'len', 'wobble', 'robot', 'radio')) and said() == ['voice:preview'])
    ok(f"its gain, measured as it is picked, plays it as loud as a leader's ({v['gain']})", abs(v['gain'] - g['f-soft']) < 0.002)
    ok('the pick pressed in the leader\'s color', js("() => { const c = document.querySelector('.ld-vchip[data-voice=\"f-soft\"]'); return [c.getAttribute('aria-pressed'), getComputedStyle(c).backgroundColor, document.querySelectorAll('.ld-vchip[aria-pressed=\"true\"]').length]; }") == ['true', 'rgb(185, 163, 227)', 1])
    pg.focus('#ldV-pitch')
    for _ in range(3): pg.keyboard.press('ArrowRight')
    pg.wait_for_timeout(500)
    v = js(f"() => getLeader('{lid}').voice")
    ok(f"the pitch slider moves its note in semitones: +3 from 262 Hz is 311.57 ({v['pitch']}, {v['base']})", v['pitch'] == 3 and abs(v['base'] - 311.57) < 0.01 and v['from'] == 'f-soft')
    ok('its readout says the note and how far it moved, and Back to Soft shows', js("() => [document.querySelector('#ldV-pitch + output').textContent, document.querySelector('.ld-vreset').hidden, document.querySelector('.ld-vreset').textContent]") == ['312 Hz, +3', False, 'Back to Soft'])
    ok('a slider let go says the line again', said().count('voice:preview') >= 2)
    pg.click('.ld-vreset'); pg.wait_for_timeout(500)
    ok('Back to Soft puts every setting back, the pitch in the middle', js(f"() => [getLeader('{lid}').voice.pitch, getLeader('{lid}').voice.base, document.querySelector('#ldV-pitch').value, document.querySelector('.ld-vreset').hidden]") == [0, 262, '0', True])

    pg.click('.ld-vfine-btn'); pg.wait_for_timeout(200)
    fine = js("""() => ({ open: !document.querySelector('#ldVFine').hidden, exp: document.querySelector('.ld-vfine-btn').getAttribute('aria-expanded'),
      sliders: [...document.querySelectorAll('#ldVFine .ld-vslider .lbl')].map(l => l.textContent), outs: [...document.querySelectorAll('#ldVFine output')].map(o => o.textContent),
      switches: [...document.querySelectorAll('#ldVFine .ld-vswitch b')].map(x => x.textContent) })""")
    ok(f"Fine-tune unfolds: Tone, Range, Speed, Chatter, Length and Wobble, then Robot and Radio ({fine})", fine['open'] and fine['exp'] == 'true' and fine['sliders'] == ['Tone', 'Range', 'Speed', 'Chatter', 'Length', 'Wobble'] and fine['switches'] == ['Robot', 'Radio'])
    ok(f"each says where it is in words ({fine['outs']})", fine['outs'] == ['Soft', 'Lively', '0.95x', 'Every 2nd letter', '60 ms', 'None'])
    pg.screenshot(path=str(SH / '501-voice-fine.png'))
    pg.evaluate("() => { const r = document.querySelector('#ldV-tone'); r.value = '85'; r.dispatchEvent(new Event('input')); r.dispatchEvent(new Event('change')); }")
    pg.click('#ldV-robot'); pg.wait_for_timeout(500)
    v = js(f"() => getLeader('{lid}').voice")
    ok(f"a fine-tune slider and a switch change only their setting, the pick still its start ({v['tone']}, {v['robot']}, {v['from']})", v['tone'] == 0.85 and v['robot'] is True and v['from'] == 'f-soft' and v['base'] == 262)
    ok('a thin robot is measured again', v['gain'] != g['f-soft'])
    r = js(f"async () => {{ const l = getLeader('{lid}'); return [await Sound._test.render('voice:ld:' + l.id, 5)]; }}")
    ok(f"the robot renders clean ({r[0]})", not r[0]['bad'] and r[0]['peak'] > 0.01 and r[0]['peak'] < 0.9)
    ok(f"not work: Updated and Activity stay ({before})", js(f"() => {{ const p = getProject('{gp}'); return [p.updatedAt, p.activity.length]; }}") == before)

    # ---------- the leader talks in it ----------
    # what Claude added waits in News (0.1.96), and a click on the leader's face opens it; the editor is closed first, as
    # an open editor holds a bubble that would open by itself for a break (0.1.91, City as My Terminal, L2)
    js("() => { Leaders.closeEditor(); Leaders.close(); }"); pg.wait_for_timeout(200)
    js("() => News._test.typeMs(26)")
    face = lambda: js(f"() => document.querySelector('#newsList .news-tile[data-k=\"ld:{lid}\"] .news-face').click()")
    heard = lambda: js("() => document.querySelector('#ldSayClose').click()")          # its x: read, and the bubble closes
    clear()
    js(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'a note' }})"); pg.wait_for_timeout(200)
    face(); pg.wait_for_timeout(400)
    ok(f"its news in its bubble, opened from its face, in the voice picked ({said()})", said() == ['voice:ld:' + lid] and js(f"() => JSON.stringify(Sound.voices.of('ld:{lid}')) === JSON.stringify(getLeader('{lid}').voice)"))
    heard(); pg.wait_for_timeout(100)

    # a quick voice types its line quicker: the same line, at 1.6x and at 0.6x; the card's line ends with its time
    # ("Just now."), so the words are short, for a line a 1.6x voice says whole in 0.75 s (35 letters)
    def typed_after(speed, ms):
        js(f"() => {{ const l = getLeader('{lid}'); l.voice = sanitizeVoice({{ ...l.voice, speed: {speed} }}); }}")
        js(f"() => News.add(getProject('{gp}'), 'added', {{ what: 'a note, ' + {speed} }})"); face(); pg.wait_for_timeout(ms)
        st = js("() => [document.querySelector('#ldSayText').classList.contains('typing'), document.querySelectorAll('#ldSayText .ty.on').length, document.querySelectorAll('#ldSayText .ty').length]")
        heard(); pg.wait_for_timeout(150)
        return st
    fast, slow = typed_after(1.6, 750), typed_after(0.6, 750)
    ok(f"its speed paces the typing too: after 0.75 s a 1.6x voice has said its line whole, a 0.6x one is still at it ({slow[1]} of {slow[2]} letters)", fast[0] is False and slow[0] is True and 0 < slow[1] < slow[2] * 0.75)

    # ---------- Its own again: nothing kept ----------
    js(f"() => {{ Leaders.open(); Leaders.edit('{lid}'); }}"); pg.wait_for_timeout(300)
    pg.click('.ld-vchip[data-voice="own"]'); pg.wait_for_timeout(400)
    ok('Its own picked back: the leader keeps no voice, and talks in its own again', js(f"() => ['voice' in getLeader('{lid}'), Sound.voices.of('ld:{lid}').base]") == [False, own_hz])

    # ---------- kept: saved, after a reload, in a backup and a project file ----------
    pg.click('.ld-vchip[data-voice="m-deep"]'); pg.wait_for_timeout(500)
    pg.focus('#ldV-pitch'); pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(600)
    kept = js(f"() => getLeader('{lid}').voice")
    pg.click('#ldDone'); pg.wait_for_timeout(500)
    pg.reload(); pg.wait_for_timeout(2000)
    ok(f"kept after a reload ({kept['from']}, {kept['pitch']})", js(f"() => getLeader('{lid}').voice") == kept and kept['from'] == 'm-deep' and kept['pitch'] == -1)
    bk = js(f"async () => {{ const b = await buildBackup(); return b.leaders.find(l => l.id === '{lid}').voice; }}")
    ok('a backup carries it', bk == kept)
    pf = js(f"async () => (await Leaders.carry(getLeader('{lid}'))).voice")
    ok('a project file carries it with its leader', pf == kept)
    bad = js("() => sanitizeLeaders([{ id: 'a', name: 'A', voice: { from: '<b>', pitch: 40, base: 9, tone: 7, range: 2.6, speed: 'x', every: 9, len: 1, wobble: -1, robot: 1, gain: 99 } }, { id: 'b', name: 'B', voice: 'loud' }, { id: 'c', name: 'C' }])")
    ok(f"a voice read with care: every number in its slider's range, a bad one dropped ({bad[0]['voice']})", bad[0]['voice'] == {'from': 'own', 'pitch': 12, 'base': 40, 'tone': 1, 'range': 3, 'speed': 1, 'every': 4, 'len': 0.1, 'wobble': 0, 'robot': True, 'radio': False, 'gain': 5} and 'voice' not in bad[1] and 'voice' not in bad[2])

    # ---------- Quill: his own voice, or the one picked for a leader named Quill ----------
    pg.mouse.click(150, 560); pg.wait_for_timeout(300)
    js("() => { if (Leaders.editorOpen()) Leaders.closeEditor(); if (Leaders.isOpen()) Leaders.close(); }"); pg.wait_for_timeout(200)
    js("() => News._test.typeMs(26)")
    clear()
    js(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Draw the beds', round: 'Beds, Round 1' }})"); pg.wait_for_timeout(400)
    ok(f"Quill says a round in his own voice ({said()})", said() == ['voice:quill'])
    js("() => News.hide({ read: true })"); clear()
    qid = js("() => { const l = blankLeader({ name: 'Quill', role: 'The Pocket Wizard', color: '#8E5A9E' }); DB.leaders.push(l); return l.id; }")
    ok("a leader named Quill has his voice as its own", js(f"() => Sound.voices.of('ld:{qid}').base") == 523)
    js(f"() => {{ getLeader('{qid}').voice = sanitizeVoice({{ ...Sound.voices.presets[0].v, from: 'm-deep', pitch: 0 }}); }}")
    js(f"() => News.add(getProject('{gp}'), 'round', {{ task: 'Draw the beds', round: 'Beds, Round 2' }})"); pg.wait_for_timeout(400)
    ok(f"with a voice picked, that leader says his rounds in it ({said()})", said() == ['voice:ld:' + qid])
    js("() => News.hide({ read: true })"); clear()

    # ---------- sound off, Still, and a new leader ----------
    js("() => Sound.setMode('off')")
    pg.click('#btnOpenLeaders') if not js("() => Leaders.isOpen()") else None
    pg.click(f'.ld-row[data-id="{lid}"]'); pg.wait_for_timeout(300)
    pg.click('#ldHear'); pg.wait_for_timeout(250)
    ok("with no sound, Hear it says why it is quiet, and plays nothing", js("() => [document.querySelector('.ld-voice-quiet').hidden, document.querySelector('.ld-voice-quiet').textContent]") == [False, "Sound is off, so the city says nothing. Turn it on with the speaker on the map's bar."] and said() == [])
    js("() => { Sound.setMode('all'); Motion.set('still'); }"); pg.wait_for_timeout(150); clear()
    pg.click('#ldHear'); pg.wait_for_timeout(250)
    ok(f"on Still the line shows whole, but Hear it still says it ({said()})", said() == ['voice:preview'] and not js("() => document.querySelector('#ldVoiceLine').classList.contains('typing')") and js("() => document.querySelector('.ld-voice-quiet').hidden"))
    js("() => Motion.set(null)")
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    pg.click('#btnNewLeader'); pg.wait_for_timeout(300)
    pg.fill('#ldName', 'Canto')
    pg.click('.ld-vchip[data-voice="f-bright"]'); pg.wait_for_timeout(500)
    pg.click('#ldAdd'); pg.wait_for_timeout(500)
    ok("a new leader's voice, picked before Add, is kept", js("() => { const l = DB.leaders.find(x => x.name === 'Canto'); return l && l.voice && l.voice.from; }") == 'f-bright')
    ctx.close()

    # ---------- a phone: the Voice section fits ----------
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    ctx.add_init_script(TEST_CITY)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(FILE); pg.wait_for_timeout(1800)
    lid = pg.evaluate(f"() => {{ const l = blankLeader({{ name: 'Talal', role: 'Head of Gardens', color: '#B9A3E3' }}); DB.leaders.push(l); persistNow(); Leaders.open(); Leaders.edit(l.id); return l.id; }}")
    pg.wait_for_timeout(400)
    pg.evaluate("() => document.querySelector('.ld-vfine-btn').click()"); pg.wait_for_timeout(200)
    fit = pg.evaluate("""() => { const v = document.querySelector('#ldView'), s = document.querySelector('.ld-voice').getBoundingClientRect();
      const out = [...document.querySelectorAll('.ld-voice *')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.right > innerWidth + 1; }).length;
      return { over: v.scrollWidth - v.clientWidth, right: s.right, out }; }""")
    ok(f"on a phone the presets wrap and nothing runs off the screen ({fit})", fit['over'] <= 1 and fit['out'] == 0)
    pg.evaluate("() => document.querySelector('.ld-voice').scrollIntoView()"); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SH / '502-voice-phone.png'))
    ctx.close()
    b.close()

bad = [e for e in errors if 'favicon' not in e]
ok('no console errors' + (': ' + ' | '.join(bad[:3]) if bad else ''), not bad)
