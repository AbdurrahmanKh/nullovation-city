import pathlib
from playwright.sync_api import sync_playwright
from testkit import FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture, TEST_CITY

SETUP = (ROOT / 'src' / 'setup' / 'nullovation-folder-links.ps1').read_text(encoding='utf-8')
errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2000)
    js = lambda code: pg.evaluate(code)
    left = js("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    wz = js("() => DB.projects.find(p => p.name.startsWith('Garden')).id")
    js(f"""() => {{ const p = DB.projects.find(p => p.id === '{wz}');
      p.links = [{{ id: uid('l'), label: 'Design folder', url: 'C:\\\\Users\\\\Abdurrahman\\\\My Designs', icon: 'folder' }},
                 {{ id: uid('l'), label: 'Old style', url: 'file:///D:/Work/Game%20Assets', icon: 'folder' }},
                 {{ id: uid('l'), label: 'Share', url: '\\\\\\\\nas\\\\team\\\\specs', icon: 'folder' }},
                 {{ id: uid('l'), label: 'Web', url: 'https://example.com', icon: 'web' }}]; changed(p); }}""")
    js("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(250)
    a = js(f"() => MapView.anchors('{wz}')")
    pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(450)
    pg.click('#enterBtn'); pg.wait_for_timeout(600)
    links = lambda: js("() => [...document.querySelectorAll('[data-sec=\"links\"] .link-btn')].map(a => [a.getAttribute('href'), a.getAttribute('target')])")
    L = links()
    ok('with the setting off, a Windows path opens in the browser as a file address', L[0] == ['file:///C:/Users/Abdurrahman/My%20Designs', '_blank'])
    ok('a file:// address and a network share do too', L[1][0] == 'file:///D:/Work/Game%20Assets' and L[2][0] == 'file://nas/team/specs')
    ok('web links are untouched', L[3] == ['https://example.com', '_blank'])
    ok('every local link has a copy-path button, web links do not', pg.locator('[data-sec="links"] .link-copy').count() == 3)
    pg.click('[data-sec="links"] .link-local >> nth=0 >> .link-copy'); pg.wait_for_timeout(150)
    ok('copy path copies the Windows path', js("() => navigator.clipboard.readText()") == 'C:\\Users\\Abdurrahman\\My Designs')
    pg.click('[data-sec="links"] .link-local >> nth=1 >> .link-copy'); pg.wait_for_timeout(150)
    ok('a file:// address copies as a Windows path', js("() => navigator.clipboard.readText()") == 'D:\\Work\\Game Assets')
    # the setting, in Tools
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    pg.click('#foldTools summary'); pg.wait_for_timeout(100)
    ok('Tools has the Explorer setting, off by default', pg.is_visible('#optExplorer') and not js("() => document.querySelector('#optExplorer').checked"))
    with pg.expect_download() as dl:
        pg.click('#btnFolderSetup')
    got = pathlib.Path(dl.value.path()).read_text()
    ok('Get the setup saves the setup script, exactly as written', dl.value.suggested_filename == 'nullovation-folder-links.ps1' and got == SETUP)
    ok('the setup registers only for this user, and can be undone', 'HKCU:\\Software\\Classes\\$scheme' in got and '-Uninstall' in got and 'HKLM' not in got)
    ok('the helper accepts drive and share paths only, and never runs a file', "'^(?:[A-Za-z]:\\\\|\\\\\\\\[^\\\\]+\\\\[^\\\\]+)'" in got and '/select,' in got and 'Invoke-Item' not in got)
    pg.check('#optExplorer'); pg.wait_for_timeout(150)
    open_btn = lambda: (js("() => MapView.setCam({ x: 0, y: 230, z: 2 })"), pg.wait_for_timeout(250))
    open_btn()
    a = js(f"() => MapView.anchors('{wz}')")
    pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(450)
    pg.click('#enterBtn'); pg.wait_for_timeout(600)
    L = links()
    ok('with the setting on, local links use the Explorer link type, in the same tab', L[0] == ['nullovation-folder:C%3A%5CUsers%5CAbdurrahman%5CMy%20Designs', None])
    ok('the share goes through Explorer too, and web links stay as they were', L[2][0] == 'nullovation-folder:%5C%5Cnas%5Cteam%5Cspecs' and L[3] == ['https://example.com', '_blank'])
    ok('the button says where it opens', 'Opens in File Explorer' in (pg.get_attribute('[data-sec="links"] .link-btn >> nth=0', 'title') or ''))
    pg.reload(); pg.wait_for_timeout(1600)
    ok('the setting is remembered', js("() => explorerLinks()") is True)
    # adding a Windows path from the add-link form: accepted, with the folder icon
    js("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(250)
    a = js(f"() => MapView.anchors('{wz}')")
    pg.mouse.click(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(450)
    pg.click('#enterBtn'); pg.wait_for_timeout(600)
    pg.click('#pvAddLinkBtn'); pg.fill('#pvLinkUrl', 'E:\\Builds\\Nullovation'); pg.wait_for_timeout(100)
    ok('a pasted Windows path gets the folder icon on its own', 'Folder' in pg.get_attribute('#pvLinkIcon', 'aria-label'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    last = js(f"() => DB.projects.find(p => p.id === '{wz}').links.slice(-1)[0]")
    ok('it is saved as typed, as a folder link', last['url'] == 'E:\\Builds\\Nullovation' and last['icon'] == 'folder')
    b.close()
print(errors or 'no console errors')
