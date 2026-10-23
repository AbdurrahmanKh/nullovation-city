"""Pass 18: Open in Claude. Beside every copy for Claude sits one button, Open in Claude, whose panel (0.1.63) opens
Claude with the text filled in, or copies it: Chat, Cowork, Code, Terminal and Copy, and under them the one folder they
open in, with a > to pick another when the building links several. For a task it has two tabs, Build it and Think, and
Think can ask for a brainstorm instead of a round. The links are read as written, and a click is caught before it
leaves the page."""
import urllib.parse
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
# catches claude:// links on their way out, in the capture phase, so the page's own click handlers still run
CATCH = """() => { window.__opened = []; document.addEventListener('click', e => {
  const a = e.target.closest && e.target.closest('a[href^="claude:"], a[href^="claude-cli:"]');
  if (a) { e.preventDefault(); window.__opened.push(a.getAttribute('href')); } }, true); }"""
TILES = """() => [...document.querySelectorAll('.oc-panel .oc-tile')].map(e => ({ kind: e.dataset.kind, href: e.getAttribute('href'),
  note: (e.querySelector('.oc-tile-note') || {}).textContent || '', off: e.classList.contains('off'), title: e.getAttribute('title') || '' }))"""
FOLDER = "() => (document.querySelector('.oc-panel .oc-folder') || {}).textContent || ''"

def parse(u):
    base, _, qs = (u or '').partition('?')
    return base, urllib.parse.parse_qs(qs, keep_blank_values=True)

def q_of(item):
    return parse(item['href'])[1].get('q', [None])[0]

def kinds(tiles):
    return [t['kind'] for t in tiles]

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    js = lambda code, *a: pg.evaluate(code, *a)
    clip = lambda: js("() => navigator.clipboard.readText()").replace('\r\n', '\n')     # Windows reads line ends back as \r\n
    js(CATCH)
    gid = js("() => DB.projects.find(p => p.name === 'Garden planner').id")
    nid = js("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    links = [{'label': 'Repo', 'url': 'D:\\Work\\Garden Planner\\', 'icon': 'folder'},
             {'label': 'Art', 'url': 'file:///D:/Work/Garden%20Art', 'icon': 'folder'},
             {'label': 'Brief', 'url': 'D:\\Work\\Garden Planner\\brief.pdf', 'icon': 'doc'}]
    js("""([id, links]) => { const p = DB.projects.find(p => p.id === id);
      for (const l of links) p.links.push(Object.assign({ id: uid('l') }, l));
      p.todos[0].text = 'ارسم الأحواض على شبكة'; changed(p); }""", [gid, links])
    proj = lambda what: js(f"() => {what}")

    # the project's local links: folders, and files by their extension
    pl = js(f"() => OpenInClaude.places(DB.projects.find(p => p.id === '{gid}'))")
    ok(f'local links split into folders and files ({pl})', pl == {'folders': ['D:\\Work\\Garden Planner', 'D:\\Work\\Garden Art'], 'files': ['D:\\Work\\Garden Planner\\brief.pdf']})
    ok('Cowork has an icon of its own, apart from the folder icon', js("() => !!ICONS.cowork && ICONS.cowork.join() !== ICONS.folder.join()"))

    # the project view: one button where Copy status and Open in Claude were
    js(f"() => FullView.open('{gid}')"); pg.wait_for_timeout(600)
    ok('Open in Claude sits in the About and in What is next', pg.is_visible('#pvStatusClaude') and pg.is_visible('#pvNextClaude'))
    ok('and the separate copy buttons are gone: no Copy status, no Copy task in What is next',
       js("() => ![...document.querySelectorAll('.pv-about-btns button, .pv-next-row button')].some(b => /^Copy (status|task)$/.test(b.textContent.trim()))")
       and js("() => document.querySelectorAll('.pv-next-row button').length") == 1)
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    tiles = js(TILES)
    ok(f'its panel offers Chat, Cowork, Code, Terminal and Copy ({kinds(tiles)})', kinds(tiles) == ['chat', 'cowork', 'code', 'terminal', 'copy'])
    ok('a project\'s status has no tabs: Build it and Think are for a task', not pg.is_visible('.oc-panel .oc-tabs'))
    status = proj(f"projectStatusForClaude(DB.projects.find(p => p.id === '{gid}'))")
    chat, cowork, code, term, copy = tiles
    ok(f'Chat opens a new chat with the status filled in, and says it takes no folder ({chat["note"]})', parse(chat['href'])[0] == 'claude://claude.ai/new' and q_of(chat) == status and chat['note'] == 'no folder')
    cw = parse(cowork['href'])
    ok(f'Cowork takes the one folder, and no more folders or files ({cw[1].get("folder")})', cw[0] == 'claude://cowork/new' and cw[1].get('folder') == [pl['folders'][0]]
       and 'file' not in cw[1] and cw[1].get('q', [None])[0] == status)
    cd = parse(code['href'])
    ok('Code opens in the folder', cd[0] == 'claude://code/new' and cd[1].get('folder') == [pl['folders'][0]] and 'file' not in cd[1] and not code['off'])
    td = parse(term['href'])
    ok('Terminal opens Claude Code in a terminal in the folder, filled in', td[0] == 'claude-cli://open' and td[1].get('cwd') == [pl['folders'][0]]
       and td[1].get('q', [None])[0] == status and set(td[1]) == {'q', 'cwd'} and not term['off'])
    ok('and its line breaks travel as %0A', '%0A' in term['href'] and '\n' not in term['href'])
    ok('every tile draws its icon', js("() => [...document.querySelectorAll('.oc-panel .oc-tile .ic svg')].length") == 5)
    fl = js(FOLDER)
    ok(f'the folder line names the folder, with a > to pick another, the building linking two ({fl})', fl.startswith('Folder: D:\\Work\\Garden Planner') and fl.endswith('>') and pg.is_visible('#ocFolderPick'))
    box = js("() => { const r = document.querySelector('.oc-panel').getBoundingClientRect(); return [r.top, r.bottom, r.left, r.right, innerHeight, innerWidth]; }")
    ok('the panel sits on the screen', box[0] >= 0 and box[1] <= box[4] and box[2] >= 0 and box[3] <= box[5])
    ok('the first tile takes the focus, and the arrow keys move along the tiles', js("() => document.activeElement.dataset.kind") == 'chat'
       and (pg.keyboard.press('ArrowRight') or True) and js("() => document.activeElement.dataset.kind") == 'cowork'
       and (pg.keyboard.press('ArrowLeft') or True) and (pg.keyboard.press('ArrowLeft') or True) and js("() => document.activeElement.dataset.kind") == 'copy')
    pg.screenshot(path=str(SHOTS / 'oc-1-status-panel.png'))

    # picking the folder
    pg.click('#ocFolderPick'); pg.wait_for_timeout(200)
    opts = js("() => [...document.querySelectorAll('.oc-folder-opt')].map(o => [o.querySelector('.oc-folder-name').textContent, o.getAttribute('aria-selected')])")
    ok(f'the > lists the building\'s folders, the one in use picked ({opts})', opts == [['Garden Planner', 'true'], ['Garden Art', 'false']])
    pg.screenshot(path=str(SHOTS / 'oc-1b-folders.png'))
    pg.locator('.oc-folder-opt').nth(1).click(); pg.wait_for_timeout(200)
    chat, cowork, code, term, copy = js(TILES)
    ok('picking one sends Cowork, Code and Terminal there', parse(cowork['href'])[1].get('folder') == ['D:\\Work\\Garden Art'] and parse(code['href'])[1].get('folder') == ['D:\\Work\\Garden Art']
       and parse(term['href'])[1].get('cwd') == ['D:\\Work\\Garden Art'] and js(FOLDER).startswith('Folder: D:\\Work\\Garden Art') and not pg.is_visible('.oc-folders'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes the panel first, the project view stays, and the focus goes back to its button', not pg.is_visible('.oc-panel') and js("() => FullView.isOpen()")
       and js("() => document.activeElement.id") == 'pvStatusClaude')
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    ok('the building remembers the folder picked, in this browser', js(FOLDER).startswith('Folder: D:\\Work\\Garden Art'))
    pg.click('#ocFolderPick'); pg.locator('.oc-folder-opt').nth(0).click(); pg.wait_for_timeout(150)
    ok('picking the first again forgets it', js("() => JSON.parse(localStorage.getItem('nullovation-city:claudeFolder') || '{}')") == {})
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # Copy, in the panel
    js("() => navigator.clipboard.writeText('')")
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    pg.click('.oc-panel .oc-tile[data-kind="copy"]'); pg.wait_for_timeout(400)
    ok('Copy copies the status and says so, the panel closing', clip() == status and 'Status copied' in (pg.text_content('#toast') or '') and not pg.is_visible('.oc-panel'))

    # a click opens the link, copies the text, and says so
    js("() => navigator.clipboard.writeText('')")
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    pg.click('.oc-panel .oc-tile[data-kind="chat"]'); pg.wait_for_timeout(400)
    opened = js("() => window.__opened")
    ok('picking Chat opens its link', opened and parse(opened[-1])[0] == 'claude://claude.ai/new')
    ok('and puts the text on the clipboard too', clip() == status)
    ok('and says so', 'Opening Claude' in (pg.text_content('#toast') or ''))
    ok('the panel closes after a pick', not pg.is_visible('.oc-panel'))

    # the task panel: Build it and Think, in Arabic too
    tid = proj(f"DB.projects.find(p => p.id === '{gid}').todos[0].id")
    js(f"() => FullView.openTask('{gid}', '{tid}')"); pg.wait_for_timeout(500)
    ok('the task panel has Open in Claude alone, no Copy task beside it', pg.is_visible('#pvTaskClaude')
       and js("() => [...document.querySelectorAll('.pv-claude-row button')].map(b => b.id).join()") == 'pvTaskClaude')
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(250)
    tabs = js("() => [...document.querySelectorAll('.oc-panel .oc-tab')].map(t => [t.textContent.trim(), t.getAttribute('aria-selected')])")
    ok(f'a task has two tabs, Build it picked ({tabs})', tabs == [['Build it', 'true'], ['Think', 'false']] and js("() => document.activeElement.id") == 'ocTabBuild')
    want = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return taskForClaude(p, p.todos[0], Date.now(), {{ kind: 'chat' }}); }})()")
    tiles = js(TILES)
    ok('Build it fills in the task, Arabic and all', q_of(tiles[0]) == want and 'ارسم الأحواض على شبكة' in want and want.endswith(proj("REPORT_LINE")))
    ok('and offers no brainstorm', not pg.is_visible('#ocBrainstorm'))
    pg.screenshot(path=str(SHOTS / 'oc-2-task-build.png'))
    pg.click('#ocTabThink'); pg.wait_for_timeout(200)
    tiles = js(TILES)
    ok('Think asks for a wizard round about the task instead', js("() => document.querySelector('#ocTabThink').getAttribute('aria-selected')") == 'true'
       and q_of(tiles[0]).endswith(proj("ROUND_LINE")) and q_of(tiles[0]).startswith('# Task: ') and kinds(tiles) == ['chat', 'cowork', 'code', 'terminal', 'copy'])
    ok('with its five tiles and the folder, and Make a brainstorming round unticked', pg.is_visible('#ocBrainstorm') and not js("() => document.querySelector('#ocBrainstorm').checked")
       and parse(tiles[3]['href'])[1].get('cwd') == [pl['folders'][0]] and q_of(tiles[3]).endswith(proj("ROUND_LINE")))
    pg.screenshot(path=str(SHOTS / 'oc-3-task-think.png'))
    pg.click('#ocBrainstorm'); pg.wait_for_timeout(200)
    tiles = js(TILES)
    ok('ticked, it asks for a brainstorm instead', all(q_of(t).endswith(proj("BRAINSTORM_LINE")) for t in tiles if t['href']) and 'Explore this task with a brainstorm' in proj("BRAINSTORM_LINE")
       and js("() => document.activeElement.id") == 'ocBrainstorm')
    js("() => navigator.clipboard.writeText('')")
    pg.click('.oc-panel .oc-tile[data-kind="copy"]'); pg.wait_for_timeout(400)
    ok('and Copy copies the brainstorm ask, saying so', clip().endswith(proj("BRAINSTORM_LINE")) and 'brainstorm' in (pg.text_content('#toast') or ''))
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(250)
    ok('the panel opens on Build it again, the box unticked', js("() => document.querySelector('#ocTabBuild').getAttribute('aria-selected')") == 'true' and not pg.is_visible('#ocBrainstorm'))
    box = js("() => { const r = document.querySelector('.oc-panel').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; }")
    ok(f'nothing cut off in the task panel, the panel on the screen ({[round(x) for x in box]})', box[0] >= 0 and box[1] <= box[2]
       and js("() => { const s = document.querySelector('.pv-side'); return s.scrollWidth <= s.clientWidth; }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes the panel but keeps the task open', not pg.is_visible('.oc-panel') and pg.is_visible('#pvTaskClaude'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.click('#pvNextClaude'); pg.wait_for_timeout(250)
    ok('What is next\'s Open in Claude has Build it and Think too', pg.is_visible('#ocTabThink'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)

    # the milestone panel
    pg.locator('.ms-name-btn').first.click(); pg.wait_for_timeout(500)
    ok('the milestone panel has no Copy for Claude beside Open in Claude', not pg.is_visible('#pvMsCopy') and pg.is_visible('#pvMsClaude'))
    pg.click('#pvMsClaude'); pg.wait_for_timeout(250)
    want = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return milestoneForClaude(p, p.milestones[0]); }})()")
    ok('the milestone panel fills in the milestone, with no tabs', q_of(js(TILES)[0]) == want and want.startswith('# Milestone: ') and not pg.is_visible('.oc-panel .oc-tabs'))
    js("() => navigator.clipboard.writeText('')")
    pg.click('.oc-panel .oc-tile[data-kind="copy"]'); pg.wait_for_timeout(400)
    ok('and its Copy copies the milestone', clip() == want and 'Milestone copied' in (pg.text_content('#toast') or ''))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # the note panel
    js(f"""() => {{ const p = DB.projects.find(p => p.id === '{gid}');
      p.notes.push({{ id: 'n_short', title: 'Watering', text: 'Water at dawn.', at: Date.now() - 7200e3 }}); changed(p); FullView.render(); }}""")
    pg.wait_for_timeout(300)
    pg.locator('.pv-note-cell', has=pg.locator('text=Watering')).locator('.pv-note-card').click(); pg.wait_for_timeout(400)
    ok('the note panel has no Copy for Claude beside Open in Claude', not pg.is_visible('#pvNoteCopy') and pg.is_visible('#pvNoteClaude'))
    pg.click('#pvNoteClaude'); pg.wait_for_timeout(250)
    want = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return noteForClaude(p, p.notes.find(n => n.id === 'n_short')); }})()")
    ok('the note panel fills in the note', q_of(js(TILES)[0]) == want and want.startswith('# Note: Watering'))
    ok('and nothing in the note panel is cut off', js("() => { const s = document.querySelector('.pv-side'); return s.scrollWidth <= s.clientWidth; }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # a milestone whose tasks carry long descriptions: too long to fill in
    js(f"""() => {{ const p = DB.projects.find(p => p.id === '{gid}'), m = p.milestones[1];
      for (let k = 0; k < 3; k++) p.todos.push(Object.assign(todo('Long step ' + (k + 1), m.id), {{ description: 'Plant and log. '.repeat(500) }}));
      changed(p); FullView.render(); }}""")
    pg.wait_for_timeout(300)
    pg.locator('.ms-name-btn').nth(1).click(); pg.wait_for_timeout(500)
    pg.click('#pvMsClaude'); pg.wait_for_timeout(250)
    tiles = js(TILES)
    full = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return milestoneForClaude(p, p.milestones[1]); }})()")
    ok(f'a text over the limit opens Claude empty instead of cut short ({len(full)} characters)', len(full) > 13500 and 'q' not in parse(tiles[0]['href'])[1]
       and parse(tiles[1]['href'])[1].get('folder') == [pl['folders'][0]])
    ok('and Terminal, whose limit is 5,000, opens in the folder with nothing filled in', 'q' not in parse(tiles[3]['href'])[1] and parse(tiles[3]['href'])[1].get('cwd') == [pl['folders'][0]])
    pg.click('.oc-panel .oc-tile[data-kind="chat"]'); pg.wait_for_timeout(400)
    ok('and puts the whole text on the clipboard, saying so', clip() == full and 'Too long to fill in' in (pg.text_content('#toast') or ''))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # the builder card, from the more menu
    pg.click('#pvMore'); pg.wait_for_timeout(200)
    pg.click('.pv-menu-item >> text=Builder card in a Claude chat'); pg.wait_for_timeout(400)
    want = proj(f"builderCard(DB.projects.find(p => p.id === '{gid}'))")
    last = js("() => window.__opened")[-1]
    ok('the more menu sends the builder card to a new chat', parse(last)[0] == 'claude://claude.ai/new' and parse(last)[1].get('q', [None])[0] == want and want.startswith('# Nullovation City builder card'))
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    # a project with no local links
    js(f"() => FullView.open('{nid}')"); pg.wait_for_timeout(600)
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    chat, cowork, code, term, copy = js(TILES)
    ok('without a folder link, Cowork opens with the text only', 'folder' not in parse(cowork['href'])[1] and not cowork['off'])
    ok('and Code and Terminal wait for one, saying so', code['off'] and code['href'] is None and term['off'] and term['href'] is None and 'folder' in code['title'].lower()
       and js(FOLDER) == 'No folder link: Code and Terminal need one.' and not pg.is_visible('#ocFolderPick'))
    pg.screenshot(path=str(SHOTS / 'oc-4-no-folder.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    # a network folder: Code opens there, a terminal does not
    js(f"() => {{ const p = DB.projects.find(p => p.id === '{nid}'); p.links.push({{ id: uid('l'), label: 'NAS', url: '\\\\\\\\nas\\\\city', icon: 'folder' }}); changed(p); FullView.render(); }}")
    pg.wait_for_timeout(300)
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    chat, cowork, code, term, copy = js(TILES)
    ok(f'a network folder opens Code, but not a terminal, and says so ({term["title"]})', not code['off'] and parse(code['href'])[1].get('folder') == ['\\\\nas\\city'] and term['off']
       and 'on this computer' in term['title'] and js(FOLDER) == 'Folder: \\\\nas\\city')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    # the side bar: the status brief of every project
    ok('Status brief sits with the week, one button (0.1.64), and the old Copy status brief is gone', pg.is_visible('#btnBriefClaude') and not js("() => !!document.querySelector('#btnBrief')"))
    pg.click('#btnBriefClaude'); pg.wait_for_timeout(250)
    copy, chat, cowork, code, term = js(TILES)
    ok('its panel starts with Copy status brief, then the four Claude tiles (0.1.64)', copy['kind'] == 'copy' and [t['kind'] for t in (chat, cowork, code, term)] == ['chat', 'cowork', 'code', 'terminal'])
    ok('the status brief fills in a new chat', q_of(chat) == proj("statusBrief()") and q_of(chat).startswith('# Nullovation City status'))
    ok('with no project, Code and Terminal have no folder to open', code['off'] and term['off'] and js(FOLDER) == 'No project folder: Chat, Cowork or Copy.')
    pg.screenshot(path=str(SHOTS / 'oc-5-brief-panel.png'))
    js("() => navigator.clipboard.writeText('')")
    pg.click('.oc-panel .oc-tile[data-kind="copy"]'); pg.wait_for_timeout(400)
    ok('and Copy copies the brief, saying so', clip() == proj("statusBrief()") and 'Status brief copied' in (pg.text_content('#toast') or ''))
    pg.click('#btnBriefClaude'); pg.wait_for_timeout(250)
    pg.mouse.click(900, 450); pg.wait_for_timeout(250)
    ok('a click elsewhere closes the panel', not pg.is_visible('.oc-panel'))

    # a narrow window: the panel stays on the screen
    pg.set_viewport_size({'width': 390, 'height': 800}); pg.wait_for_timeout(400)
    js(f"() => FullView.open('{gid}')"); pg.wait_for_timeout(600)
    js(f"() => FullView.openTask('{gid}', '{tid}')"); pg.wait_for_timeout(500)
    js("() => document.querySelector('#pvTaskClaude').scrollIntoView({ block: 'center' })"); pg.wait_for_timeout(200)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(250)
    box = js("() => { const r = document.querySelector('.oc-panel').getBoundingClientRect(); return [r.left, r.right, innerWidth]; }")
    ok(f'on a narrow window the panel fits the screen ({[round(x) for x in box]})', box[0] >= 0 and box[1] <= box[2])
    b.close()
print('\n'.join(errors) if errors else 'no console errors')
