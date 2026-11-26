"""One report under one finish, and a card that reads (0.1.95, from "seriously wtf is this UX?").

A thread started in T3 has no task of the city's, so the updates it sent for a task found no session, and each part
was said on its own: two "Claude wants your OK first" lines, what it added, Quill's round, and a finish that named the
prompt as its task. Since 0.1.96 (One Leader Card, M2) a finish's updates are a page per type, never one mixed message, so
this pass checks one Need Approval page with every change, Quill's round, one Attachment page and the finish ("Claude handed he is the main voice right now... back to you"). Now an update that names a task no
session works on goes to the one session with no task of its own, at work or finished, or whose run it was written in;
every update of a turn sits under its finish, each summary with its parts; the finish names the update's task; and a
session with no task is named by its prompt in quotes. A task in a line is a link that wraps with the words, a part's
buttons follow its words, a status card taller than the map scrolls, and Enter never sits on the card. The city opens
with a Claude folder held in memory, as in test24."""
import json
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SH, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

FAKE = (ROOT / 'tests' / 'test24_claude_work.py').read_text(encoding='utf-8').split('FAKE = """', 1)[1].split('"""', 1)[0]
def S(session, state, cwd, mins=0, **kw):
    """A session file as the hooks write it, last heard from mins minutes ago."""
    at = f'Date.now() - {mins} * 60000'
    extra = ''.join(f', {k}: {json.dumps(v)}' for k, v in kw.items())
    return f"window.__put('{session}.json', {{ v: 1, app: 'nullovation-city', kind: 'claude-session', session: '{session}', state: '{state}', cwd: {json.dumps(cwd)}, at: {at}, since: {at} - 120000, started: {at} - 300000{extra} }})"
GARDEN = 'C:\\Users\\me\\garden'
T1, T2, T3 = 'Get Claude to understand the game and its art', 'Rebuild the Ludum Dare jam version as is', 'Write a GDD with the voice of every character'
ASK = 'he is the main voice right now because I worked a lot on that situation, once I work on other situations he will be so dominant.'
ROUND = {"config": {"title": "Understand the game and its art, Round 2", "tagline": "Claims", "product": "Garden planner", "needs_wizard": "0.4.0"},
         "questions": [{"id": "C1", "section": "Rules", "title": "Fire", "question": "Can the fire end a run?", "options": ["Right", "Wrong", "Partly"]}]}
UPD1 = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'task': T1,
        'summary': 'Claude studied the game and wrote the document; Round 2 asks you to check its claims.',
        'changes': [{'do': 'add-round', 'task': T1, 'file': '2026-11-25-understand-round2.json'},
                    {'do': 'edit-description', 'task': T1, 'description': 'Claude studies the game until it understands it.'},
                    {'do': 'add-note', 'kind': 'status', 'task': T1, 'title': 'Where the understanding stands', 'text': '1. Started.'},
                    {'do': 'add-link', 'label': 'Understanding the game (doc)', 'url': 'https://example.com/doc'}]}
UPD2 = {'app': 'nullovation-city', 'kind': 'change', 'version': 1, 'project': 'Garden planner', 'task': T1,
        'summary': 'Claude fixed the game document from your Round 2 marks.',
        'changes': [{'do': 'done', 'task': T1},
                    {'do': 'add-note', 'kind': 'status', 'task': T1, 'title': 'Where the understanding stands', 'text': '1. Done.'},
                    {'do': 'edit-description', 'task': T2, 'description': 'Rebuild the jam version as it was.'},
                    {'do': 'edit-description', 'task': T3, 'description': 'Develop the voice of every character.'}]}

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t60')) { sessionStorage.setItem('nc-t60', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:garbage', '0'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE)
    pg.wait_for_function("() => typeof ClaudeWork !== 'undefined' && typeof DB !== 'undefined' && DB.projects.length === 2", timeout=20000)
    pg.wait_for_timeout(600)
    js = pg.evaluate
    gp = js("() => DB.projects.find(p => p.name === 'Garden planner').id")
    js(f"""() => {{ const p = getProject('{gp}');
      p.links.push({{ id: uid('l'), label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true }});
      const l = blankLeader({{ name: 'Ahmed', role: 'Mine Supervisor', color: '#7FD6B5' }}); DB.leaders.push(l); p.leader = l.id;
      addTasks(p, [{{ text: {json.dumps(T1)}, description: '', due: '' }}, {{ text: {json.dumps(T2)}, description: '', due: '' }}, {{ text: {json.dumps(T3)}, description: '', due: '' }}], {{ id: p.milestones[0].id }});
      News._test.typeMs(0); News._test.sayMs(120000); persistNow(); }}""")
    open_settings(pg, 'links')
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(400)
    js("() => { window.__cmark = true; }")
    close_settings(pg)
    js(f"() => window.__sub.set('wizard-rounds/2026-11-25-understand-round2.json', {{ text: {json.dumps(json.dumps(ROUND))}, t: Date.now() }})")
    settle = lambda ms=3600: pg.wait_for_timeout(ms)
    def drop(name, d, ago_min=0):
        js(f"() => window.__sub.set('inbox/{name}', {{ text: {json.dumps(json.dumps(d))}, t: Date.now() - {ago_min} * 60000 }})")
    items = lambda: js(f"() => News.items().filter(it => it.pid === '{gp}').map(it => it.moment)")
    close_say = lambda: js("() => { const c = document.querySelector('#ldSayMin'); if (!document.querySelector('#ldSay').hidden && c) c.click(); }")
    say = lambda: js("""() => { const b = document.querySelector('#ldSay'); if (b.hidden) return null;
      return { text: $('#ldSayText').textContent, type: b.dataset.type, n: ($('#ldSayCount') || {}).textContent || '', words: [...b.querySelectorAll('#ldSayMore .b-claude-said')].map(x => x.textContent),
        parts: [...b.querySelectorAll('#ldSayMore .ld-part-text')].map(x => x.textContent) }; }""")
    CARD = """() => { const b = document.querySelector('#bubble'); if (b.hidden) return null;
      return { lines: [...b.querySelectorAll('.ld-line')].map(l => ({ moment: l.dataset.moment, type: l.dataset.type, task: (l.closest('.lc').querySelector('.lc-tline') || {}).textContent || '',
        says: l.querySelector('.ld-says').textContent, words: [...l.querySelectorAll('.b-claude-said')].map(x => x.textContent),
        parts: [...l.querySelectorAll('.ld-part')].map(x => [x.querySelector('.ld-part-text').textContent, [...x.querySelectorAll('button.btn')].map(y => y.textContent)]),
        kids: [...l.children].map(x => x.classList.contains('b-claude-said') ? 'said' : x.classList.contains('ld-part') ? 'part' : x.className.split(' ')[0]) })),
        flip: (b.querySelector('.ld-flip-n') || {}).textContent || '' }; }"""
    card = lambda: js(CARD)
    flat = lambda v: js(f"() => News._test.flat({'true' if v else 'false'})")
    line = lambda c, ty: next((x for x in (c or {'lines': []})['lines'] if x['type'] == ty), None)
    def open_card():
        js(f"() => MapView.select('{gp}')"); pg.wait_for_timeout(900)
    shut = lambda: (js("() => MapView.deselect()"), pg.wait_for_timeout(200))

    # ---------- a thread started in T3, at work with no task of the city's: its updates wait for its finish ----------
    js(S('m1', 'working', GARDEN, ask=ASK))
    settle()
    drop('2026-11-25-0700-garden.json', UPD1)
    settle()
    rep = js("() => News._test.reports()")
    ok(f'an update naming a task no session works on goes to the one session with no task of its own ({[(r["sid"], r["alone"]) for r in rep]})',
       len(rep) == 1 and rep[0]['sid'] == 'm1' and not rep[0]['alone'])
    ok(f'and nothing is said on its own meanwhile: no bubble, no item in News ({items()})', say() is None and items() == [])
    flat(True); open_card()
    c = card()
    ok(f'its working page names the update\'s task in the task\'s line, the update\'s parts as pages of their own ({c and [(x["type"], x["moment"]) for x in c["lines"]]})', c
       and [(x['type'], x['moment']) for x in c['lines']] == [('approval', 'asks'), ('wizard', 'round'), ('attach', 'added'), ('news', 'working')]
       and line(c, 'news')['says'] == 'Claude is working on this task. Started 2 minutes ago.' and line(c, 'news')['task'] == T1
       and line(c, 'approval')['says'] == 'Claude wants your OK first: a new description for this task. Sent just now.')
    shut()
    js(S('m1', 'working', GARDEN, ask=ASK))                    # a second update in the same run
    drop('2026-11-25-0800-garden.json', UPD2)
    settle()
    open_card()
    c = card()
    ok(f'a second update in the same run joins the first: one page per type, the working page with both summaries ({c and [x["says"] for x in c["lines"]]})', c and len(c['lines']) == 4
       and line(c, 'approval')['says'] == 'Claude wants your OK on 4 changes. Sent just now.' and len(line(c, 'approval')['parts']) == 4
       and line(c, 'news')['words'] == [UPD1['summary'], UPD2['summary']]
       and line(c, 'attach')['says'] == 'Claude added a note, Where the understanding stands, and a link, Understanding the game (doc). Sent just now.')
    shut(); flat(False)

    # ---------- its finish: one report, every part of both updates under it ----------
    js(S('m1', 'done', GARDEN, ask=ASK, reply="I've fixed the document. It now says the Scouts Leader is the main voice today."))
    settle()
    s = say()
    ok(f'the finish opens one bubble on what needs your OK: every change of both updates on one page, the oldest first ({s and (s["n"], s["text"], s["parts"])})', s and s['n'] == '1 / 2'
       and s['type'] == 'approval' and s['text'] == 'Claude wants your OK on 4 changes. Sent just now.'
       and s['parts'] == ['A new description for this task.', 'Tick this task off.', f'A new description for {T2}.', f'A new description for {T3}.'])
    ok(f'a page per type in News, not one mixed message nor six: what asks, the round, what Claude added, the finish ({items()})', items() == ['asks', 'round', 'added', 'finished'])
    js("() => document.querySelector('#ldSayNext').click()"); pg.wait_for_timeout(200)
    s = say()
    ok(f'the bubble\'s second page: Quill\'s round; what Claude added and the finish wait in News ({s and s["text"]})', s and s['type'] == 'wizard'
       and s['text'] == 'Claude attached a wizard round to this task: Understand the game and its art, Round 2. Sent just now.')
    js("() => document.querySelector('#ldSayPrev').click()"); pg.wait_for_timeout(200)
    pg.screenshot(path=str(SH / '600-one-report-bubble.png'), clip=pg.query_selector('#ldSay').bounding_box())
    close_say(); settle(300)
    open_card()
    c = card()
    ok(f'the status card opens on the same page, four to flip ({c and (c["flip"], [x["says"] for x in c["lines"]])})', c and len(c['lines']) == 1 and c['flip'] == '1 / 4'
       and c['lines'][0]['says'] == 'Claude wants your OK on 4 changes. Sent just now.' and len(c['lines'][0]['parts']) == 4)
    ok(f'each change with its own buttons, No in place of Dismiss ({c and [x[1] for x in c["lines"][0]["parts"]]})', c and [x[1] for x in c['lines'][0]['parts']] == [
        ['Read', 'Apply', 'No'], ['Tick it', 'No'], ['Read', 'Apply', 'No'], ['Read', 'Apply', 'No']])

    # the task in its own line, a link that wraps
    lk = js("""() => { const a = document.querySelector('#bubble .lc-tline .ld-task'); return { tag: a.tagName, text: a.textContent, rects: a.getClientRects().length }; }""")
    ok(f'the task is in its own line, a link that wraps ({lk})', lk['tag'] == 'A' and lk['text'] == T1 and lk['rects'] >= 1)
    pk = js("""() => [...document.querySelectorAll('#bubble .ld-part')].map(x => { const t = x.querySelector('.ld-part-text'), a = x.querySelector('.ld-part-acts'), tr = t.getBoundingClientRect(), ar = a.getBoundingClientRect();
      const lh = parseFloat(getComputedStyle(t).lineHeight);
      return { text: t.textContent, whole: t.scrollHeight <= t.clientHeight + 1, lines: Math.round(tr.height / lh), follows: Math.abs(ar.left - tr.left) <= 1 || (ar.left >= tr.right && ar.left - tr.right <= 12 && Math.abs(ar.top - tr.top) < lh) }; })""")
    ok(f'every part keeps to two lines, its buttons following its words, under them or beside a short line ({[(x["lines"], x["follows"]) for x in pk]})', all(x['lines'] <= 2 and x['follows'] for x in pk))
    tick = next(x for x in pk if x['text'] == 'Tick this task off.')
    reb = next(x for x in pk if x['text'] == f'A new description for {T2}.')
    ok(f'a short part reads whole: "Tick this task off." and the jam rebuild\'s line, no end cut off ({tick["whole"]}, {reb["whole"]})', tick['whole'] and reb['whole'])
    pg.screenshot(path=str(SH / '601-one-report-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    pg.click('#bubble .lc-tline .ld-task'); pg.wait_for_timeout(600)
    ok('a click on the task opens it, in its project', js(f"() => FullView.shows('{gp}') && !!document.querySelector('#pvSide .pv-desc, #pvSide')") is True)
    js("() => FullView.close()"); pg.wait_for_timeout(300)
    shut()

    # ---------- the leader card in the project view says the same ----------
    js(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(700)
    v = js("() => { const l = document.querySelector('#pvLeader .ld-line'); return l && [l.querySelector('.ld-says').textContent, l.querySelectorAll('.ld-part').length, document.querySelector('#pvLeader .lc-pgn').textContent]; }")
    ok(f'the leader card in the project view says the same pages ({v})', v == ['Claude wants your OK on 4 changes. Sent just now.', 4, '1 / 4'])
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    # ---------- acting on a part keeps the rest ----------
    open_card()
    pg.click('#bubble .ld-part[data-part="ask done"] .b-claude-tick'); pg.wait_for_timeout(1500)
    c = card()
    ok(f'Tick it ticks the task off, and the page keeps the other changes ({c and len(c["lines"][0]["parts"])})', js(f"() => getProject('{gp}').todos.find(t => t.text === {json.dumps(T1)}).done") is True
       and c and len(c['lines']) == 1 and len(c['lines'][0]['parts']) == 3)
    shut()
    js("() => window.__cf.delete('m1.json')"); settle()

    # ---------- the city closed: a run that finished half an hour ago still takes the updates written in it ----------
    js("() => News._test.forget()")
    js(S('m2', 'done', GARDEN, mins=30, ask='go on', reply='Done: the second pass is in.'))
    settle()
    close_say(); settle(300)
    drop('2026-11-25-0900-garden.json', {**UPD1, 'summary': 'Written while the city was closed.', 'changes': [{'do': 'add-note', 'task': T2, 'title': 'Jam notes', 'text': 'x'}], 'task': T2}, ago_min=31)
    settle()
    rep = js("() => News._test.reports()")
    ok(f'an update written during a run that finished 30 minutes ago sits under that finish ({[(r["sid"], r["alone"], bool(r["fin"])) for r in rep]})',
       len(rep) == 1 and rep[0]['sid'] == 'm2' and rep[0]['fin'] and not rep[0]['alone'])
    pgs = js(f"() => News._test.pages('{gp}', 'view').map(x => [x.type, x.moment, x.task])")
    ok(f'said with the finish of the task it names, what it added a page of its own, waiting in News; what the earlier updates still ask waits too ({pgs})', say() is None
       and [x for x in pgs if x[0] != 'approval'] == [['attach', 'added', T2], ['news', 'finished', T2]])
    close_say(); settle(300)
    drop('2026-11-25-0910-garden.json', {**UPD1, 'summary': 'Written long after.', 'changes': [{'do': 'add-note', 'title': 'Later', 'text': 'y'}], 'task': ''}, ago_min=0)
    settle()
    rep = js("() => News._test.reports()")
    ok(f'one written after that run ended is said on its own ({[(r["sid"], r["alone"]) for r in rep][-1:]})', rep[-1]['alone'] and rep[-1]['sid'] == '')
    close_say(); js("() => window.__cf.delete('m2.json')"); settle()

    # ---------- a session with no task and no update: its prompt, in quotes ----------
    js("() => { News._test.forget(); News._test.flat(true); }")    # what the earlier updates still ask waits as topics of its own
    js(S('m3', 'done', GARDEN, ask=ASK, reply='Fixed.'))
    settle()
    open_card()
    fin = next((x for x in (card() or {'lines': []})['lines'] if x['moment'] == 'finished'), None)
    q = '\u201che is the main voice right now because I worked\u2026\u201d'
    ok(f'a finish with no task names the prompt in quotes, cut short, never as a task ({fin and fin["says"]})', fin and fin['says'] == f'Claude handed {q} back to you. Just now.'
       and not js("() => !!document.querySelector('#bubble .ld-line[data-moment=\"finished\"] .ld-says .ld-task')"))
    shut()
    js(S('m3', 'working', GARDEN, ask=T3))
    settle()
    open_card()
    wk = next((x for x in (card() or {'lines': []})['lines'] if x['moment'] == 'working'), None)
    ok(f'a prompt that is a task\'s title is that task, as a link in the task\'s line ({wk and (wk["says"], wk["task"])})', wk and wk['says'].startswith('Claude is working on this task.') and wk['task'] == T3
       and js("() => (document.querySelector('#bubble .ld-line[data-moment=\"working\"]').closest('.lc').querySelector('.lc-tline .ld-task') || {}).textContent") == T3)
    shut()
    js(S('m3', 'working', GARDEN, ask='make the build faster'))
    settle()
    w = js("() => { const r = document.querySelector('#newsWork .news-thought'); return r && r.textContent; }")
    ok(f'the leader at work says the prompt in quotes too ({w})', w == 'Claude is working on \u201cmake the build faster\u201d. Started 2 minutes ago.')
    js("() => window.__cf.delete('m3.json')"); settle()

    # ---------- a card taller than the map scrolls, and Enter never sits on it ----------
    js("() => { News._test.forget(); News._test.flat(false); }")
    js(S('m4', 'working', GARDEN, ask=ASK))
    settle()
    drop('2026-11-25-1000-garden.json', UPD2)
    settle()
    js(S('m4', 'done', GARDEN, ask=ASK, reply='Done.'))
    settle()
    close_say(); settle(300)
    pg.set_viewport_size({'width': 1440, 'height': 640}); pg.wait_for_timeout(400)
    open_card()
    tall = js("""() => { const b = document.querySelector('#bubble'), r = b.getBoundingClientRect(), t = document.querySelector('.map-tools').getBoundingClientRect();
      return { tall: b.classList.contains('tall'), scrolls: b.scrollHeight > b.clientHeight, bottom: Math.round(r.bottom), tools: Math.round(t.top), tail: getComputedStyle(b.querySelector('.tail')).display }; }""")
    ok(f'in a short window the card scrolls, its foot over the map\'s buttons, its tail hidden ({tall})', tall['tall'] and tall['scrolls'] and tall['bottom'] <= tall['tools'] and tall['tail'] == 'none')
    z0 = pg.text_content('#zoomLevel')
    box = pg.query_selector('#bubble').bounding_box()
    pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    pg.mouse.wheel(0, 300); pg.wait_for_timeout(400)
    st = js("() => document.querySelector('#bubble').scrollTop")
    ok(f'the wheel over it scrolls the card, and the map keeps its zoom ({st}, {z0} to {pg.text_content("#zoomLevel")})', st > 0 and pg.text_content('#zoomLevel') == z0)
    js("() => Bubble.refresh()"); pg.wait_for_timeout(200)
    ok('drawn again, it keeps its place', js("() => document.querySelector('#bubble').scrollTop") == st)
    pg.screenshot(path=str(SH / '602-tall-card.png'))
    # the building under the card: Enter moves off it
    js(f"""() => {{ const c = MapView.camState(), a = MapView.anchors('{gp}'), b = document.querySelector('#bubble').getBoundingClientRect(), w = document.querySelector('#mapWrap').getBoundingClientRect();
      MapView.setCam({{ x: c.x, y: c.y + (a.baseY - (b.top - w.top + b.height * 0.6)) / c.z, z: c.z }}); }}""")
    pg.wait_for_timeout(500); js("() => Bubble.position()"); pg.wait_for_timeout(100)
    en = js(f"""() => {{ const e = document.querySelector('#enterBtn').getBoundingClientRect(), b = document.querySelector('#bubble').getBoundingClientRect(), a = MapView.anchors('{gp}'), w = document.querySelector('#mapWrap').getBoundingClientRect();
      const under = a.baseY + w.top > b.top && a.baseY + w.top < b.bottom && a.baseX + w.left > b.left && a.baseX + w.left < b.right;
      return {{ under, overlap: e.left < b.right && e.right > b.left && e.top < b.bottom && e.bottom > b.top, shown: getComputedStyle(document.querySelector('#enterBtn')).visibility !== 'hidden' }}; }}""")
    ok(f'with the building\'s door under the card, Enter stands beside the card, never on it ({en})', en['under'] and en['shown'] and not en['overlap'])
    pg.screenshot(path=str(SH / '603-enter-beside.png'))
    pg.click('#enterBtn'); pg.wait_for_timeout(500)
    ok('and still steps inside', js(f"() => FullView.shows('{gp}')") is True)
    js("() => FullView.close()"); pg.wait_for_timeout(300)
    pg.set_viewport_size({'width': 1440, 'height': 1000}); pg.wait_for_timeout(400)
    open_card()
    ok('in a tall window the card is whole again, with its tail', js("() => !document.querySelector('#bubble').classList.contains('tall') && getComputedStyle(document.querySelector('#bubble .tail')).display !== 'none'"))
    shut()

    print('no console errors' if not errors else 'CONSOLE ERRORS: ' + ' | '.join(errors[:5]))
    b.close()
