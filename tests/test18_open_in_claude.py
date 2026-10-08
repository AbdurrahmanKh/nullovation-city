"""Pass 18: Open in Claude. Beside every Copy for Claude sits Open in Claude, whose menu opens the Claude desktop app
with the same text filled in: a new chat, a Cowork task with the project's local folders and files attached, or Claude
Code in the project's first folder. The links are read as written, and a click is caught before it leaves the page."""
import urllib.parse
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
# catches claude:// links on their way out, in the capture phase, so the page's own click handlers still run
CATCH = """() => { window.__opened = []; document.addEventListener('click', e => {
  const a = e.target.closest && e.target.closest('a[href^="claude:"]');
  if (a) { e.preventDefault(); window.__opened.push(a.getAttribute('href')); } }, true); }"""
ITEMS = """() => [...document.querySelectorAll('.oc-menu .oc-item')].map(e => ({ kind: e.dataset.kind, href: e.getAttribute('href'),
  note: e.querySelector('.oc-note').textContent, off: e.classList.contains('off') }))"""

def parse(u):
    base, _, qs = (u or '').partition('?')
    return base, urllib.parse.parse_qs(qs, keep_blank_values=True)

def q_of(item):
    return parse(item['href'])[1].get('q', [None])[0]

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

    # the project view: beside Copy status
    js(f"() => FullView.open('{gid}')"); pg.wait_for_timeout(600)
    ok('Open in Claude sits beside Copy status and beside What is next', pg.is_visible('#pvStatusClaude') and pg.is_visible('#pvNextClaude'))
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    items = js(ITEMS)
    ok(f'its menu offers Chat, Cowork and Claude Code ({[i["kind"] for i in items]})', [i['kind'] for i in items] == ['chat', 'cowork', 'code'])
    status = proj(f"projectStatus(DB.projects.find(p => p.id === '{gid}'))")
    chat, cowork, code = items
    ok('Chat opens a new chat with the project status filled in', parse(chat['href'])[0] == 'claude://claude.ai/new' and q_of(chat) == status)
    cw = parse(cowork['href'])
    ok(f'Cowork attaches both folders and the file ({cowork["note"]})', cw[0] == 'claude://cowork/new' and cw[1].get('folder') == pl['folders'] and cw[1].get('file') == pl['files']
       and cw[1].get('q', [None])[0] == status and cowork['note'] == 'with Garden Planner and 2 more')
    ok('and its note shows whole', js("() => { const n = document.querySelector('.oc-item[data-kind=cowork] .oc-note'); return [n, ...n.children].every(e => e.scrollWidth <= e.clientWidth); }"))
    cd = parse(code['href'])
    ok(f'Claude Code opens in the first folder ({code["note"]})', cd[0] == 'claude://code/new' and cd[1].get('folder') == [pl['folders'][0]] and 'file' not in cd[1] and code['note'] == 'in Garden Planner')
    box = js("() => { const r = document.querySelector('.oc-menu').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; }")
    ok('the menu sits on the screen', box[0] >= 0 and box[1] <= box[2])
    ok('the first item takes the focus, and the arrow keys move it', js("() => document.activeElement.dataset.kind") == 'chat'
       and (pg.keyboard.press('ArrowDown') or True) and js("() => document.activeElement.dataset.kind") == 'cowork')
    pg.screenshot(path=str(SHOTS / 'oc-1-status-menu.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ok('Esc closes the menu first, and the project view stays', not pg.is_visible('.oc-menu') and js("() => FullView.isOpen()")
       and js("() => document.activeElement.id") == 'pvStatusClaude')

    # a long first folder name gives way, and 'and 2 more' stays whole
    swap = "([id, url]) => { const l = DB.projects.find(p => p.id === id).links.find(l => l.label === 'Repo'), o = l.url; l.url = url; return o; }"
    old_url = js(swap, [gid, 'D:\\Work\\The garden planner for the spring and summer beds'])
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    fit = js("""() => { const n = document.querySelector('.oc-item[data-kind=cowork] .oc-note'), name = n.querySelector('.oc-name'), more = n.querySelector('.oc-more');
      return { text: n.textContent, cut: name.scrollWidth > name.clientWidth, whole: more.getBoundingClientRect().right <= n.getBoundingClientRect().right + 0.5 }; }""")
    ok(f'a long folder name is cut short, and the count stays whole ({fit["text"]})', fit['cut'] and fit['whole'] and fit['text'] == 'with The garden planner for the spring and summer beds and 2 more')
    pg.screenshot(path=str(SHOTS / 'oc-1b-long-folder.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    js(swap, [gid, old_url])

    # a click opens the link, copies the text, and says so
    js("() => navigator.clipboard.writeText('')")
    pg.click('#pvStatusClaude'); pg.wait_for_timeout(250)
    pg.click('.oc-menu .oc-item[data-kind="chat"]'); pg.wait_for_timeout(400)
    opened = js("() => window.__opened")
    ok('picking Chat opens its link', opened and parse(opened[-1])[0] == 'claude://claude.ai/new')
    ok('and puts the text on the clipboard too', clip() == status)
    ok('and says so', 'Opening Claude' in (pg.text_content('#toast') or ''))
    ok('the menu closes after a pick', not pg.is_visible('.oc-menu'))

    # the task panel, in Arabic too
    tid = proj(f"DB.projects.find(p => p.id === '{gid}').todos[0].id")
    js(f"() => FullView.openTask('{gid}', '{tid}')"); pg.wait_for_timeout(500)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(250)
    want = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return taskForClaude(p, p.todos[0]); }})()")
    items = js(ITEMS)
    ok('the task panel fills in the task, Arabic and all', q_of(items[0]) == want and 'ارسم الأحواض على شبكة' in want)
    box = js("() => { const r = document.querySelector('.oc-menu').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; }")
    ok(f'the task panel keeps Copy and Open in Claude on their own row, with nothing cut off ({[round(x) for x in box]})', box[0] >= 0 and box[1] <= box[2]
       and js("() => { const s = document.querySelector('.pv-side'); return s.scrollWidth <= s.clientWidth; }")
       and js("() => !!document.querySelector('.pv-claude-row #pvTaskClaude')"))
    pg.screenshot(path=str(SHOTS / 'oc-2-task-menu.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes the menu but keeps the task open', not pg.is_visible('.oc-menu') and pg.is_visible('#pvTaskClaude'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # the milestone panel
    pg.locator('.ms-name-btn').first.click(); pg.wait_for_timeout(500)
    pg.click('#pvMsClaude'); pg.wait_for_timeout(250)
    want = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return milestoneForClaude(p, p.milestones[0]); }})()")
    ok('the milestone panel fills in the milestone', q_of(js(ITEMS)[0]) == want and want.startswith('# Milestone: '))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # the note panel
    js(f"""() => {{ const p = DB.projects.find(p => p.id === '{gid}');
      p.notes.push({{ id: 'n_short', title: 'Watering', text: 'Water at dawn.', at: Date.now() - 7200e3 }}); changed(p); FullView.render(); }}""")
    pg.wait_for_timeout(300)
    pg.locator('.pv-note-cell', has=pg.locator('text=Watering')).locator('.pv-note-card').click(); pg.wait_for_timeout(400)
    pg.click('#pvNoteClaude'); pg.wait_for_timeout(250)
    want = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return noteForClaude(p, p.notes.find(n => n.id === 'n_short')); }})()")
    ok('the note panel fills in the note', q_of(js(ITEMS)[0]) == want and want.startswith('# Note: Watering'))
    ok('and nothing in the note panel is cut off', js("() => { const s = document.querySelector('.pv-side'); return s.scrollWidth <= s.clientWidth; }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)

    # a milestone whose tasks carry long descriptions: too long to fill in
    js(f"""() => {{ const p = DB.projects.find(p => p.id === '{gid}'), m = p.milestones[1];
      for (let k = 0; k < 3; k++) p.todos.push(Object.assign(todo('Long step ' + (k + 1), m.id), {{ description: 'Plant and log. '.repeat(500) }}));
      changed(p); FullView.render(); }}""")
    pg.wait_for_timeout(300)
    pg.locator('.ms-name-btn').nth(1).click(); pg.wait_for_timeout(500)
    pg.click('#pvMsClaude'); pg.wait_for_timeout(250)
    items = js(ITEMS)
    full = proj(f"(() => {{ const p = DB.projects.find(p => p.id === '{gid}'); return milestoneForClaude(p, p.milestones[1]); }})()")
    ok(f'a text over the limit opens Claude empty instead of cut short ({len(full)} characters)', len(full) > 13500 and 'q' not in parse(items[0]['href'])[1]
       and parse(items[1]['href'])[1].get('folder') == pl['folders'])
    pg.click('.oc-menu .oc-item[data-kind="chat"]'); pg.wait_for_timeout(400)
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
    chat, cowork, code = js(ITEMS)
    ok(f'without a folder link, Cowork opens with the text only ({cowork["note"]})', 'folder' not in parse(cowork['href'])[1] and cowork['note'] == 'no folder link')
    ok(f'and Claude Code waits for one ({code["note"]})', code['off'] and code['href'] is None and code['note'] == 'needs a folder link')
    pg.screenshot(path=str(SHOTS / 'oc-3-no-folder.png'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    js("() => FullView.close()"); pg.wait_for_timeout(300)

    # the side bar: the status brief of every project
    ok('Open in Claude sits beside Copy status brief, with the week', pg.is_visible('#btnBriefClaude'))
    pg.click('#btnBriefClaude'); pg.wait_for_timeout(250)
    chat, cowork, code = js(ITEMS)
    ok('the status brief fills in a new chat', q_of(chat) == proj("statusBrief()") and q_of(chat).startswith('# Nullovation City status'))
    ok('with no project, Claude Code has no folder to open', code['off'] and cowork['note'] == 'no project folder')
    pg.screenshot(path=str(SHOTS / 'oc-4-brief-menu.png'))
    pg.mouse.click(900, 450); pg.wait_for_timeout(250)
    ok('a click elsewhere closes the menu', not pg.is_visible('.oc-menu'))
    b.close()
print('\n'.join(errors) if errors else 'no console errors')
