"""Links: the icons (GitHub and Claude in, Task and Design out), the larger add panel with the address and label on
their own lines, the shortcut switch and its warning past 8, dragging links to reorder them, and the shortcut wheel
a right-click on a building opens. Also: Copy task, copies without the project's About, the About opening with the
description, and the Claude icon on Open in Claude. Since 0.1.27, from the links round: a label the address suggests,
the same address twice, pasting an address to add it, Undo for a deleted link, search by address, and on the wheel
its larger buttons, Enter (the button and the key), the F key, and the wheel and the status bubble closing each
other."""
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t23')) { sessionStorage.setItem('nc-t23', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:traffic', '0'); localStorage.setItem('nullovation-city:bubbles', 'none'); } } catch (e) {}")
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    js = pg.evaluate
    clip = lambda: js("() => navigator.clipboard.readText()").replace('\r\n', '\n')
    gid = js("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    proj = lambda: js(f"() => getProject('{gid}')")
    left = js("() => document.querySelector('#mapWrap').getBoundingClientRect().left")

    # ---------- the icons ----------
    ok(f'the link icons: Doc, Code, GitHub, Claude, Chat, Folder, Web ({js("() => LINK_ICONS")})', js("() => LINK_ICONS") == ['doc', 'code', 'github', 'claude', 'chat', 'folder', 'web'])
    guesses = js("""() => ['https://claude.ai/project/1', 'claude://claude.ai/new', 'https://github.com/a/b', 'https://linear.app/t/1', 'https://www.figma.com/file/x', 'https://gitlab.com/a', 'https://docs.google.com/d/1', 'D:\\\\Work']
      .map(guessIcon).join()""")
    ok(f'an address picks its icon: Claude and GitHub by their own, the old Task and Design addresses as web ({guesses})', guesses == 'claude,claude,github,web,web,code,doc,folder')
    old = js("""() => sanitizeProjects([{ name: 'Old', links: [{ url: 'https://github.com/a/b', label: 'Repo', icon: 'task' }, { url: 'https://www.figma.com/file/x', label: 'Mock', icon: 'design' }, { url: 'https://example.com', label: 'Site', icon: 'web' }] }])[0].p.links
      .map(l => l.icon + ':' + l.shortcut).join()""")
    ok(f'links saved with Task or Design get an icon picked from their address, and every old link is a shortcut ({old})', old == 'github:true,web:true,web:true')

    # ---------- the About: description first ----------
    js(f"() => FullView.open('{gid}')"); pg.wait_for_timeout(700)
    order = js("() => { const a = document.querySelector('[data-sec=\"about\"]'), d = a.querySelector('.fv-desc'), n = a.querySelector('.pv-next'); return !!(d && n && (d.compareDocumentPosition(n) & Node.DOCUMENT_POSITION_FOLLOWING)); }")
    ok('the About opens with the description, then What is next', order)
    pg.screenshot(path=str(SH / '233-about.png'))
    ok('What is next copies the task with Copy task', pg.is_visible('.pv-next-row >> text=Copy task') and pg.locator('.pv-next-row >> text=Copy for Claude').count() == 0)
    oc = js("() => { const want = iconEl('claude', 14).innerHTML; return [...document.querySelectorAll('.oc-btn .ic')].every(s => s.innerHTML === want); }")
    ok('Open in Claude wears the Claude icon, not the chat one', oc and pg.locator('.oc-btn').count() >= 2)

    # ---------- the add panel ----------
    pg.click('#pvAddLinkBtn'); pg.wait_for_timeout(200)
    box = lambda sel: js(f"() => {{ const r = document.querySelector('{sel}').getBoundingClientRect(); return [r.left, r.top, r.width]; }}")
    u, l, panel = box('#pvLinkUrl'), box('#pvLinkLabel'), box('.pv-add-link')
    ok(f'the address and the label are on their own lines, one over the other ({u}, {l})', abs(u[0] - l[0]) < 1 and l[1] > u[1] + 20 and u[2] > 250)
    ok(f'in a larger panel, the width of the links column ({panel[2]:.0f} px)', panel[2] > 350)
    ok('Add to shortcuts is on by default', pg.is_checked('#pvLinkShortcut') and 'Add to shortcuts' in pg.text_content('.pv-add-link'))
    pops = None
    pg.click('#pvLinkIcon'); pg.wait_for_timeout(150)
    pops = js("() => [...document.querySelectorAll('.icon-pop button')].map(b => b.getAttribute('aria-label')).join()")
    ok(f'the icon picker offers GitHub and Claude, no Task or Design ({pops})', pops == 'Doc,Code,GitHub,Claude,Chat,Folder,Web')
    pg.click('.icon-pop button[aria-label="Claude"]'); pg.wait_for_timeout(100)
    pg.fill('#pvLinkUrl', 'https://example.com/claude-project'); pg.fill('#pvLinkLabel', 'Claude project')
    pg.screenshot(path=str(SH / '230-links-add.png'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    last = proj()['links'][-1]
    ok(f'the link is added with its icon, as a shortcut ({last["icon"]}, {last["shortcut"]})', last['label'] == 'Claude project' and last['icon'] == 'claude' and last['shortcut'] is True)
    pg.click('#pvAddLinkBtn'); pg.fill('#pvLinkUrl', 'https://github.com/example/garden'); pg.fill('#pvLinkLabel', 'Repo'); pg.uncheck('#pvLinkShortcut'); pg.click('.pv-add-link .link-actions .btn-accent'); pg.wait_for_timeout(250)
    last = proj()['links'][-1]
    ok('with the switch off, it is added but kept off the wheel', last['icon'] == 'github' and last['shortcut'] is False)

    # ---------- the warning past 8 ----------
    js(f"""() => {{ const p = getProject('{gid}'); for (let k = 1; k <= 4; k++) p.links.push({{ id: uid('l'), label: 'Page ' + k, url: 'https://example.com/' + k, icon: 'web', shortcut: true }}); changed(p); FullView.render(); }}""")
    n_sc = js(f"() => getProject('{gid}').links.filter(l => l.shortcut).length")
    pg.click('#pvAddLinkBtn'); pg.wait_for_timeout(150)
    ok(f'with {n_sc} shortcuts, adding one more says only 8 fit, the first 8 showing', n_sc == 7 and not pg.is_visible('.pv-add-link .link-warn'))
    pg.keyboard.press('Escape'); js(f"() => {{ const p = getProject('{gid}'); p.links.push({{ id: uid('l'), label: 'Page 5', url: 'https://example.com/5', icon: 'web', shortcut: true }}); changed(p); FullView.render(); }}")
    pg.click('#pvAddLinkBtn'); pg.wait_for_timeout(150)
    ok('at 8 shortcuts the add panel warns that only 8 fit in a building', pg.is_visible('.pv-add-link .link-warn') and 'Only 8 shortcuts fit' in pg.text_content('.pv-add-link .link-warn'))
    pg.uncheck('#pvLinkShortcut'); pg.wait_for_timeout(100)
    ok('and the warning goes with the switch off', not pg.is_visible('.pv-add-link .link-warn'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)

    # ---------- editing: two lines, the switch, and dragging to reorder ----------
    pg.click('[data-sec="links"] .pv-pencil'); pg.wait_for_timeout(300)
    rows = pg.locator('.link-edit')
    ok(f'each link, while editing, has a grip, its icon, the address over the label, and the shortcut switch ({rows.count()} links)',
       rows.count() == len(proj()['links']) and pg.locator('.link-edit .link-grip').count() == rows.count() and pg.locator('.link-edit .link-sc input').count() == rows.count()
       and js("() => { const r = document.querySelector('.link-edit'), f = r.querySelectorAll('.link-fields .field'); return f[0].getAttribute('aria-label') === 'Link address' && f[1].getBoundingClientRect().top > f[0].getBoundingClientRect().top + 20; }"))
    ok('with 8 shortcuts while editing, no warning', not pg.is_visible('[data-sec="links"] .link-warn'))
    pg.locator('.link-edit').nth(0).locator('.link-sc input').uncheck(); pg.wait_for_timeout(150)
    ok('a link can leave the wheel while editing', proj()['links'][0]['shortcut'] is False)
    pg.locator('.link-edit').nth(0).locator('.link-sc input').check(); pg.locator('.link-edit').nth(3).locator('.link-sc input').check(); pg.wait_for_timeout(150)
    ok('past 8 the warning shows while editing too', pg.is_visible('[data-sec="links"] .link-warn'))
    pg.locator('.link-edit').nth(3).locator('.link-sc input').uncheck(); pg.wait_for_timeout(100)
    before = [x['label'] for x in proj()['links']]
    g3 = pg.locator('.link-edit').nth(2).locator('.link-grip').bounding_box()
    r0 = pg.locator('.link-edit').nth(0).bounding_box()
    pg.mouse.move(g3['x'] + g3['width'] / 2, g3['y'] + g3['height'] / 2); pg.mouse.down()
    pg.mouse.move(g3['x'] + g3['width'] / 2, r0['y'] + 10, steps=8); pg.wait_for_timeout(100)
    pg.screenshot(path=str(SH / '231-links-edit-drag.png'))
    pg.mouse.up(); pg.wait_for_timeout(250)
    after = [x['label'] for x in proj()['links']]
    ok(f'dragging a link by its grip moves it ({before[:3]} to {after[:3]})', after[0] == before[2] and after[1:3] == before[0:2] and len(after) == len(before))
    pg.locator('.link-edit').nth(0).locator('.link-grip').focus(); pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(150)
    ok('and the arrow keys on the grip move it one place', [x['label'] for x in proj()['links']][1] == before[2])
    pg.screenshot(path=str(SH / '231-links-edit.png'))
    pg.click('[data-sec="links"] .pv-done'); pg.wait_for_timeout(200)
    ok('Done keeps the new order', [x['label'] for x in proj()['links']][1] == before[2])

    # ---------- copies leave out the About ----------
    pg.click('#pvNextTask'); pg.wait_for_timeout(400)
    pg.click('#pvSide >> text=Copy task'); pg.wait_for_timeout(200)
    c = clip()
    ok('the task panel copies with Copy task, without the About', c.startswith('# Task: ') and '## About the project' not in c and 'A small app that plans' not in c)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    nc = js(f"() => noteForClaude(getProject('{gid}'), {{ title: 'T', text: 'x', at: Date.now() }}) + milestoneForClaude(getProject('{gid}'), getProject('{gid}').milestones[0])")
    ok('notes and milestones copy without it too', '## About the project' not in nc and 'A small app that plans' not in nc)

    # ---------- 0.1.27: a label from the address ----------
    sug = js("""() => ['https://github.com/example/garden', 'https://github.com/example/garden/issues/12', 'C:\\\\Work\\\\Seed Box', 'D:\\\\',
      'https://claude.ai/project/abc', 'https://claude.ai/chat/abc', 'claude://claude.ai/new', 'https://example.github.io/planner/', 'https://www.figma.com/file/x',
      'slack://channel?id=1', 'mailto:me@example.com', 'localhost:3000/app'].map(suggestLabel).join('|')""")
    ok(f'an address suggests a label: the repository, the folder, Claude, the page, the site, the app ({sug})',
       sug == 'garden|garden #12|Seed Box|D:|Claude project|Claude chat|Claude|planner|figma.com|Slack|me@example.com|localhost:3000')
    same = js("""() => [addressKey('https://www.Example.com/a/') === addressKey('http://example.com/a'), addressKey('C:\\\\Work\\\\') === addressKey('c:/work'),
      addressKey('https://example.com/a') !== addressKey('https://example.com/b')]""")
    ok(f'the same address written two ways counts as one ({same})', same == [True, True, True])
    pg.click('#pvAddLinkBtn'); pg.fill('#pvLinkUrl', 'https://github.com/example/seed-box'); pg.wait_for_timeout(100)
    ok('the label field offers the name the address suggests', pg.get_attribute('#pvLinkLabel', 'placeholder') == 'seed-box' and pg.input_value('#pvLinkLabel') == '')
    pg.focus('#pvLinkLabel'); pg.keyboard.press('Tab'); pg.wait_for_timeout(100)
    ok('Tab in the empty label takes it, to edit', pg.input_value('#pvLinkLabel') == 'seed-box' and js("() => document.activeElement.id") == 'pvLinkLabel')
    pg.fill('#pvLinkLabel', ''); pg.uncheck('#pvLinkShortcut'); pg.click('.pv-add-link .link-actions .btn-accent'); pg.wait_for_timeout(250)
    last = proj()['links'][-1]
    shown = js("() => [...document.querySelectorAll('[data-sec=\"links\"] .link-btn')].pop().textContent")
    ok(f'left empty, the label stays empty and the link shows the suggested name ({shown})', last['label'] == '' and shown == 'seed-box')

    # ---------- 0.1.27: the same address twice ----------
    pg.click('#pvAddLinkBtn'); pg.fill('#pvLinkUrl', 'https://www.github.com/example/seed-box/'); pg.wait_for_timeout(100)
    dup = pg.text_content('.pv-add-link .link-dupe') if pg.is_visible('.pv-add-link .link-dupe') else ''
    ok(f'an address the project already links says so, as its name ({dup})', 'already links this address, as seed-box' in dup)
    ok('and Add becomes Add anyway', pg.locator('.pv-add-link .link-actions .btn-accent').text_content() == 'Add anyway')
    pg.locator('.pv-add-link').scroll_into_view_if_needed(); pg.screenshot(path=str(SH / '235-links-dupe.png'))
    pg.fill('#pvLinkUrl', 'https://github.com/example/other'); pg.wait_for_timeout(100)
    ok('a new address clears it', not pg.is_visible('.pv-add-link .link-dupe') and pg.locator('.pv-add-link .link-actions .btn-accent').text_content() == 'Add')
    pg.fill('#pvLinkUrl', 'https://github.com/example/seed-box'); n0 = len(proj()['links'])
    pg.uncheck('#pvLinkShortcut'); pg.click('.pv-add-link .link-actions .btn-accent'); pg.wait_for_timeout(250)
    ok('Add anyway adds it', len(proj()['links']) == n0 + 1)

    # ---------- 0.1.27: pasting an address ----------
    js("() => navigator.clipboard.writeText('https://github.com/example/compost')")
    js("() => document.activeElement && document.activeElement.blur()")
    pg.keyboard.press('Control+V'); pg.wait_for_timeout(250)
    ok('Ctrl+V with an address, no field in use, opens Add link with it filled in',
       pg.is_visible('.pv-add-link') and pg.input_value('#pvLinkUrl') == 'https://github.com/example/compost' and pg.get_attribute('#pvLinkIcon', 'aria-label').startswith('Icon: GitHub'))
    ok('ready for a label, which it suggests', js("() => document.activeElement.id") == 'pvLinkLabel' and pg.get_attribute('#pvLinkLabel', 'placeholder') == 'compost')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    js("() => navigator.clipboard.writeText('just some words: not a link')")
    js("() => document.activeElement && document.activeElement.blur()")
    pg.keyboard.press('Control+V'); pg.wait_for_timeout(200)
    ok('text that is not an address opens nothing', not pg.is_visible('.pv-add-link'))
    js("() => navigator.clipboard.writeText('https://github.com/example/compost')")
    pg.click('#search'); pg.keyboard.press('Control+V'); pg.wait_for_timeout(200)
    ok('pasting into a field pastes as always', pg.input_value('#search') == 'https://github.com/example/compost' and not pg.is_visible('.pv-add-link'))
    pg.fill('#search', ''); pg.wait_for_timeout(150)

    # ---------- 0.1.27: Undo a deleted link ----------
    pg.click('[data-sec="links"] .pv-pencil'); pg.wait_for_timeout(300)
    before_del = [x['id'] for x in proj()['links']]
    pg.locator('.link-edit').nth(1).locator('button[aria-label="Delete link"]').click(); pg.wait_for_timeout(150)
    pg.screenshot(path=str(SH / '236-links-undo.png'))
    ok('deleting a link shows a toast with Undo', len(proj()['links']) == len(before_del) - 1 and pg.is_visible('#toast .toast-act') and pg.text_content('#toast .toast-act') == 'Undo')
    pg.click('#toast .toast-act'); pg.wait_for_timeout(200)
    ok('Undo puts it back in its place, the section still open', [x['id'] for x in proj()['links']] == before_del and pg.locator('.link-edit').count() == len(before_del))
    pg.locator('.link-edit').nth(1).locator('button[aria-label="Delete link"]').click(); pg.wait_for_timeout(150)
    pg.click('[data-sec="links"] .pv-done'); pg.wait_for_timeout(200)
    ok('after Done the link is gone, with Undo still offered', len(proj()['links']) == len(before_del) - 1 and pg.is_visible('#toast .toast-act'))
    pg.click('#toast .toast-act'); pg.wait_for_timeout(200)
    ok('and Undo then brings it back too, in the activity', [x['id'] for x in proj()['links']] == before_del and proj()['activity'][-1]['text'].startswith('Added link: '))

    # ---------- 0.1.27: search reads addresses ----------
    js("() => FullView.close()"); pg.wait_for_timeout(300)
    pg.fill('#search', 'compost'); pg.wait_for_timeout(250)
    hits = js("() => DB.projects.filter(matchesFilter).map(p => p.name)")
    pg.fill('#search', 'seed-box'); pg.wait_for_timeout(250)
    hits2 = js("() => DB.projects.filter(matchesFilter).map(p => p.name)")
    ok(f'search finds a project by what is in a link\'s address ({hits2})', hits2 == ['Garden planner'] and hits == [])
    pg.fill('#search', ''); pg.wait_for_timeout(200)

    # ---------- the shortcut wheel ----------
    js("() => { MapView.deselect(); MapView.setCam({ x: 0, y: 260, z: 2 }); }"); pg.wait_for_timeout(300)
    def right_click(pid):
        a = js(f"() => MapView.anchors('{pid}')")
        pg.mouse.click(left + a['baseX'], a['baseY'] - 30, button='right'); pg.wait_for_timeout(300)
    right_click(gid)
    want = js(f"() => shortcutLinks(getProject('{gid}')).slice(0, 8).map(l => l.label)")
    items = js("() => [...document.querySelectorAll('.wheel .wheel-item')].map(a => a.querySelector('.wheel-label').textContent)")
    ok(f'a right-click on a building opens its wheel: its shortcuts, in the links\' order, 8 at most ({len(items)})', js("() => Wheel.isOpen()") and items == want and len(items) == 8)
    ok('the links kept off the wheel are not on it', 'Repo' not in items)
    ok('the middle is kept empty for the leader\'s face, with the building\'s name over the wheel', js("() => { const h = document.querySelector('.wheel-hub'); return !!h && h.children.length === 0 && h.textContent === ''; }") and pg.text_content('.wheel-name') == 'Garden planner')
    ok('it does not select the building or open its status bubble', js("() => App.selectedId") is None and not pg.is_visible('#bubble'))
    hrefs = js(f"() => [...document.querySelectorAll('.wheel .wheel-item')].map(a => a.getAttribute('href')).join('|') === shortcutLinks(getProject('{gid}')).slice(0, 8).map(l => linkTarget(l).href).join('|')")
    ok('each shortcut goes where its link goes in the project view', hrefs)
    inside = js("() => { const W = document.querySelector('#mapWrap').getBoundingClientRect(); return [...document.querySelectorAll('.wheel .wheel-item, .wheel-name')].every(e => { const r = e.getBoundingClientRect(); return r.left >= W.left - 1 && r.right <= W.right + 1 && r.top >= W.top - 1 && r.bottom <= W.bottom + 1; }); }")
    overlap = js("() => { const r = [...document.querySelectorAll('.wheel .wheel-item, .wheel-name, .wheel-hub')].map(e => e.getBoundingClientRect()); for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) { const a = r[i], c = r[j]; if (a.left < c.right - 1 && c.left < a.right - 1 && a.top < c.bottom - 1 && c.top < a.bottom - 1) return true; } return false; }")
    ok('all of it in view, nothing overlapping', inside and not overlap)
    pg.screenshot(path=str(SH / '232-wheel.png'))
    js("() => document.querySelector('.wheel .wheel-item').addEventListener('click', e => e.preventDefault())")
    pg.click('.wheel .wheel-item >> nth=0'); pg.wait_for_timeout(150)
    ok('a click on a shortcut closes the wheel', not js("() => Wheel.isOpen()"))
    right_click(gid); pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes it', not js("() => Wheel.isOpen()"))
    right_click(gid); pg.mouse.click(left + 60, 120); pg.wait_for_timeout(150)
    ok('a click elsewhere closes it', not js("() => Wheel.isOpen()"))
    right_click(gid)
    ok('it opens with no shortcut picked, so Enter steps inside', js("() => document.activeElement === document.querySelector('.wheel')"))
    at0 = js(f"() => MapView.anchors('{gid}')")
    pg.keyboard.press('ArrowRight'); first = js("() => [...document.querySelectorAll('.wheel-item')].indexOf(document.activeElement)")
    pg.keyboard.press('ArrowRight'); second = js("() => [...document.querySelectorAll('.wheel-item')].indexOf(document.activeElement)")
    ok(f'the arrow keys move between the shortcuts, from the first ({first}, {second})', first == 0 and second == 1)
    ok('and leave the map where it is', js(f"() => MapView.anchors('{gid}')") == at0)
    pg.keyboard.press('Escape')

    # ---------- 0.1.27: Enter, the button and the key ----------
    right_click(gid)
    eb, ib = js("() => document.querySelector('.wheel-enter').getBoundingClientRect().top"), js("() => Math.max(...[...document.querySelectorAll('.wheel-item')].map(e => e.getBoundingClientRect().bottom))")
    ok('Enter sits under the wheel', pg.is_visible('.wheel-enter') and 'Enter' in pg.text_content('.wheel-enter') and eb > ib)
    pg.click('.wheel-enter'); pg.wait_for_timeout(500)
    ok('the Enter button steps inside the building, closing the wheel', js("() => FullView.isOpen() && FullView.currentId()") == gid and not js("() => Wheel.isOpen()"))
    js("() => { FullView.close(); MapView.deselect(); MapView.setCam({ x: 0, y: 260, z: 2 }); }"); pg.wait_for_timeout(400)
    right_click(gid); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    ok('so does the Enter key', js("() => FullView.isOpen() && FullView.currentId()") == gid and not js("() => Wheel.isOpen()"))
    js("() => { FullView.close(); MapView.deselect(); MapView.setCam({ x: 0, y: 260, z: 2 }); }"); pg.wait_for_timeout(400)

    # ---------- 0.1.27: the wheel and the status bubble close each other ----------
    def left_click(pid):
        a = js(f"() => MapView.anchors('{pid}')")
        pg.mouse.click(left + a['baseX'], a['baseY'] - 30); pg.wait_for_timeout(400)
    left_click(gid)
    ok('a click shows the status bubble', pg.is_visible('#bubble') and js("() => App.selectedId") == gid)
    right_click(gid)
    ok('a right-click then closes the bubble for the wheel', js("() => Wheel.isOpen()") and not pg.is_visible('#bubble') and js("() => App.selectedId") is None)
    left_click(gid)
    ok('and a click closes the wheel for the bubble', not js("() => Wheel.isOpen()") and pg.is_visible('#bubble'))
    js("() => document.activeElement && document.activeElement.blur()")
    pg.keyboard.press('Enter'); pg.wait_for_timeout(500)
    ok('Enter steps inside the selected building', js("() => FullView.isOpen() && FullView.currentId()") == gid)
    js("() => { FullView.close(); MapView.setCam({ x: 0, y: 260, z: 2 }); }"); pg.wait_for_timeout(400)

    # ---------- 0.1.27: the F key ----------
    js("() => document.activeElement && document.activeElement.blur()")
    ok('with a building selected', js("() => App.selectedId") == gid and pg.is_visible('#bubble'))
    pg.keyboard.press('f'); pg.wait_for_timeout(300)
    a = js(f"() => MapView.anchors('{gid}')")
    c = js("() => { const w = document.querySelector('.wheel').getBoundingClientRect(); return [w.left, w.top]; }")
    ok(f'F opens its wheel round the building, closing the bubble ({c[0] - left:.0f}, {c[1]:.0f})', js("() => Wheel.owner()") == gid and not pg.is_visible('#bubble')
       and abs(c[0] - left - a['baseX']) < 2 and a['topY'] < c[1] < a['baseY'])
    pg.keyboard.press('f'); pg.wait_for_timeout(150)
    ok('and F again closes it', not js("() => Wheel.isOpen()"))
    nxt = js(f"""() => {{ const list = DB.projects.filter(matchesFilter).sort((a, b) => (a.plot.u + a.plot.v) - (b.plot.u + b.plot.v) || (a.plot.u - a.plot.v) - (b.plot.u - b.plot.v));
      return list[(list.findIndex(p => p.id === '{gid}') + 1) % list.length].id; }}""")
    right_click(gid); pg.keyboard.press('e'); pg.wait_for_timeout(300)
    ok('E with the wheel open hops on from its building, closing the wheel', js("() => App.selectedId") == nxt and not js("() => Wheel.isOpen()"))
    js("() => { MapView.deselect(); MapView.setCam({ x: 0, y: 260, z: 2 }); }"); pg.wait_for_timeout(300)
    nid = js("() => DB.projects.find(p => p.name === 'Nullovation City').id")
    right_click(nid)
    ok('a building with no shortcuts shows its empty wheel, saying so', js("() => Wheel.isOpen()") and pg.locator('.wheel .wheel-item').count() == 0 and 'No shortcuts yet' in pg.text_content('.wheel-empty'))
    pg.screenshot(path=str(SH / '232-wheel-empty.png'))
    pg.keyboard.press('Escape')
    x, y = js("() => MapView.plotCss(4, 0)")
    pg.mouse.click(left + x, y + 4, button='right'); pg.wait_for_timeout(200)
    ok('a right-click on a park opens nothing', not js("() => Wheel.isOpen()"))
    js("() => { Settings.open('city'); MapView.setEditing(true); }"); pg.wait_for_timeout(300)
    right_click(gid)
    ok('nor does one in Edit City', not js("() => Wheel.isOpen()"))
    js("() => { MapView.setEditing(false); Settings.close(); }")
    pg.reload(); pg.wait_for_timeout(1500)
    ok('the order and the shortcuts are kept after a reload', [x['label'] for x in proj()['links']][1] == before[2] and proj()['links'][[x['label'] for x in proj()['links']].index('Repo')]['shortcut'] is False)

    # ---------- 0.1.27: buttons for about three words, from 1 to 8 shortcuts ----------
    words = ['Design system docs', 'Weekly planning chat', 'Garden planner repo', 'Claude project notes', 'Shared drive folder', 'Seed catalog site', 'Budget sheet', 'Notes']
    js("() => { MapView.deselect(); MapView.setCam({ x: 0, y: 260, z: 2 }); }"); pg.wait_for_timeout(300)
    bad = []
    for n in range(1, 9):
        js("(a) => { const p = getProject(a[0]); p.links = a[1].map((t, k) => ({ id: uid('l'), label: t, url: 'https://example.com/' + k, icon: LINK_ICONS[k % 7], shortcut: true })); changed(p); }", [nid, words[:n]])
        right_click(nid)
        cut = js("() => [...document.querySelectorAll('.wheel-label')].filter(s => s.scrollWidth > s.clientWidth).length")
        lap = js("() => { const r = [...document.querySelectorAll('.wheel > *')].map(e => e.getBoundingClientRect()); for (let i = 0; i < r.length; i++) for (let j = i + 1; j < r.length; j++) { const a = r[i], c = r[j]; if (a.left < c.right - 1 && c.left < a.right - 1 && a.top < c.bottom - 1 && c.top < a.bottom - 1) return true; } return false; }")
        out = js("() => { const W = document.querySelector('#mapWrap').getBoundingClientRect(); return ![...document.querySelectorAll('.wheel > *')].every(e => { const r = e.getBoundingClientRect(); return r.left >= W.left - 1 && r.right <= W.right + 1 && r.top >= W.top - 1 && r.bottom <= W.bottom + 1; }); }")
        if cut or lap or out: bad.append((n, cut, lap, out))
        if n == 8: pg.screenshot(path=str(SH / '234-wheel-words.png'))
        pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok(f'labels of about three words fit whole, with 1 to 8 shortcuts, in view and apart ({bad or "all fine"})', not bad)
    js(f"() => {{ const p = getProject('{nid}'); Wheel.open(p, 10, 10); }}"); pg.wait_for_timeout(200)
    out = js("() => { const W = document.querySelector('#mapWrap').getBoundingClientRect(); return [...document.querySelectorAll('.wheel > *')].every(e => { const r = e.getBoundingClientRect(); return r.left >= W.left + 7 && r.top >= W.top + 7; }); }")
    ok('opened at the map\'s corner, the wheel moves in to stay whole', out)
    js("() => Wheel.close()")

    # ---------- 0.1.27: the controls guide ----------
    js("() => Settings.open('city')"); pg.click('#setHelpBtn'); pg.wait_for_timeout(100)
    g = pg.text_content('#setHelp')
    ok('the controls guide names F for the wheel and Enter to step inside', 'Right-click a building, or F' in g and 'Enter, with a building selected' in g)
    b.close()
print(errors or 'no console errors')
