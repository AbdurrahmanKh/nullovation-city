"""Settings, the panel: the side bar turns into it, from its own button, the gear on the map's bar, or the comma key;
six tabs; today's controls in their new places; changes at once with no toast; dots, resets, and reopening where it
was left. Saves a screenshot of every tab."""
from playwright.sync_api import sync_playwright
from testkit import FILE, SH, TEST_CITY, open_settings, close_settings

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)
TABS = ['city', 'life', 'look', 'projects', 'saving', 'links']

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t20')) { sessionStorage.setItem('nc-t20', '1'); localStorage.setItem('nullovation-city:light', 'day'); } } catch (e) {}")
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    pg.goto(FILE); pg.wait_for_timeout(2200)
    js = pg.evaluate
    quiet = lambda: js("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; }")
    toasted = lambda: js("() => document.querySelector('#toast').classList.contains('show') ? document.querySelector('#toast').textContent : ''")

    # the way in: a Settings button at the bottom of the side bar, the gear on the map's bar, and the comma key
    ok('the side bar opens on its lists, with a Settings button at its foot', pg.is_visible('#btnRecap') and pg.is_visible('#btnOpenSettings') and not pg.is_visible('#settings'))
    foot = js("() => { const b = document.querySelector('#btnOpenSettings').getBoundingClientRect(); return [b.bottom, innerHeight]; }")
    ok(f'the button sits at the bottom of the side bar ({foot[0]:.0f} of {foot[1]})', foot[1] - foot[0] < 40)
    map0 = js("() => document.querySelector('#map').getBoundingClientRect().width")
    pg.click('#btnOpenSettings'); pg.wait_for_timeout(200)
    ok('the side bar turns into Settings: the lists give way, and the map stays in view at its size',
       pg.is_visible('#settings') and not pg.is_visible('#btnRecap') and js("() => document.querySelector('#map').getBoundingClientRect().width") == map0)
    ok('its header holds the title, a back arrow and the small ?', pg.text_content('.set-title') == 'Settings' and pg.is_visible('#setBack') and pg.is_visible('#setHelpBtn'))
    pg.click('#setBack'); pg.wait_for_timeout(150)
    ok('the back arrow returns to the lists', pg.is_visible('#btnRecap') and not pg.is_visible('#settings'))
    pg.click('#btnSettings'); pg.wait_for_timeout(150)
    ok('the gear on the map\'s bar opens it', pg.is_visible('#settings') and pg.get_attribute('#btnSettings', 'aria-label') == 'Settings')
    pg.click('#btnSettings'); pg.wait_for_timeout(150)
    ok('and closes it', not pg.is_visible('#settings'))
    pg.keyboard.press(','); pg.wait_for_timeout(150)
    ok('the comma key opens it', pg.is_visible('#settings'))
    pg.keyboard.press(','); pg.wait_for_timeout(150)
    ok('and closes it', not pg.is_visible('#settings'))
    pg.click('#search'); pg.keyboard.type('a,b'); pg.wait_for_timeout(100)
    ok('a comma typed in a field stays a comma', pg.input_value('#search') == 'a,b' and not pg.is_visible('#settings'))
    pg.fill('#search', ''); pg.keyboard.press('Tab')
    pg.keyboard.press(','); pg.wait_for_timeout(150); pg.keyboard.press('Escape'); pg.wait_for_timeout(150)
    ok('Esc closes it, like every other layer', not pg.is_visible('#settings'))

    # six tabs, each a pixel icon; each page shows only its own group
    open_settings(pg, 'city')
    names = js("() => [...document.querySelectorAll('#setTabs .set-tab')].map(b => b.dataset.tab + ':' + b.getAttribute('aria-label') + ':' + !!b.querySelector('svg'))")
    ok(f'six tabs, each a pixel icon: City, Life, Look, Projects, Saving, Links ({names})', names == [f'{t}:{n}:true' for t, n in zip(TABS, ['City', 'Life', 'Look', 'Projects', 'Saving', 'Links'])])
    for t in TABS:
        open_settings(pg, t)
        shown = js("() => [...document.querySelectorAll('#setBody .set-page')].filter(p => !p.hidden).map(p => p.dataset.tab)")
        ok(f'the {t} tab shows its own page, with its name', shown == [t] and pg.text_content('#setTabName').lower() == t and pg.get_attribute(f'.set-tab[data-tab="{t}"]', 'aria-selected') == 'true')
    open_settings(pg, 'city'); pg.focus('.set-tab[data-tab="city"]'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(100)
    ok('arrow keys move between the tabs', js("() => Settings.tab()") == 'life')

    # today's controls in their new places
    places = {
        'city': ['#mapSize', '#btnEditCity', '#optProps', '#optAmount', '#btnDeal'],
        'life': ['#optTraffic', '#optCars', '#optStreet', '#optWalk', '#optCrowds'],
        'look': ['#optLight', '#optNight', '#optDay', '#optBubbles', '#optMotion', '#optCaption', '#optCardSize', '#btnPalette'],
        'projects': ['#optRest', '#optAway'],
        'saving': ['#fileBox', '#saveStatus', '#backupBox', '#btnExport', '#btnImport', '#storageBox'],
        'links': ['#optExplorer', '#btnFolderSetup', '#btnFolderTest'],
    }
    for t, sels in places.items():
        open_settings(pg, t)
        missing = [s for s in sels if not pg.is_visible(s)]
        ok(f'{t}: {", ".join(sels)} ({missing or "all there"})', not missing)
    ok('the controls guide waits behind the ?, with the comma key in it', not pg.is_visible('#setHelp'))
    pg.click('#setHelpBtn'); pg.wait_for_timeout(100)
    ok('the ? shows the controls', pg.is_visible('#setHelp') and 'comma' in pg.text_content('#setHelp') and pg.get_attribute('#setHelpBtn', 'aria-expanded') == 'true')
    pg.click('#setHelpBtn')
    close_settings(pg)
    ok('Copy status brief and Open in Claude stay outside Settings, with the week', pg.is_visible('#btnBrief') and pg.is_visible('#btnBriefClaude')
       and js("() => !document.querySelector('#settings').contains(document.querySelector('#btnBrief'))"))
    ok('the old Tools and Backup sections and the Controls guide are gone from the lists', js("() => !document.querySelector('#foldTools') && !document.querySelector('#foldData') && !document.querySelector('#sbLists .help')"))

    # Traffic, Bubbles and Time of day in both places, in step, with the same choices and icons
    open_settings(pg, 'look')
    bar_icons = js("() => MapView.lightOptions().map(o => o.icon).join()")
    set_icons = js("() => [...document.querySelectorAll('#optLight .set-choice')].map(b => b.dataset.value).join()")
    ok(f'Time of day offers the bar\'s four choices ({set_icons})', set_icons == 'auto,day,dusk,night' and bar_icons == 'clock,sun,dusk,moon')
    quiet()
    pg.click('#optLight [data-value="night"]'); pg.wait_for_timeout(200)
    ok('a choice in Settings applies at once and shows on the bar', js("() => Light.mode") == 'night' and pg.text_content('#lightLabel') == 'Night')
    ok('with no toast for the change', toasted() == '')
    pg.click('#btnLight'); pg.wait_for_timeout(150); pg.click('.dropup [data-value="day"]'); pg.wait_for_timeout(200)
    ok('a choice on the bar shows in Settings', pg.get_attribute('#optLight [data-value="day"]', 'aria-pressed') == 'true' and pg.get_attribute('#optLight [data-value="night"]', 'aria-pressed') == 'false')
    pg.click('#optBubbles [data-value="red"]'); pg.wait_for_timeout(150)
    ok('Bubbles too, both ways', js("() => MapView.bubbleMode()") == 'red' and pg.text_content('#bubblesLabel') == 'Red only')
    pg.click('#btnBubbles'); pg.wait_for_timeout(150); pg.click('.dropup [data-value="all"]'); pg.wait_for_timeout(200)
    ok('and back from the bar', pg.get_attribute('#optBubbles [data-value="all"]', 'aria-pressed') == 'true')
    open_settings(pg, 'life')
    pg.uncheck('#optTraffic'); pg.wait_for_timeout(150)
    ok('the Traffic switch and the bar\'s button are one', js("() => Traffic.isOn()") is False and 'No traffic' in pg.text_content('#btnTraffic'))
    pg.click('#btnTraffic'); pg.wait_for_timeout(150)
    ok('both ways', pg.is_checked('#optTraffic'))

    # dots on what differs from its default, and on its tab (this pass keeps the city at Day for its screenshots)
    open_settings(pg, 'look'); pg.click('#optLight [data-value="auto"]'); open_settings(pg, 'life')
    ok('with everything at its default, no dot shows and Reset all settings waits', js("() => document.querySelectorAll('#setBody .changed, #setTabs .changed').length") == 0 and pg.is_disabled('#btnResetAll'))
    quiet()
    pg.select_option('#optCrowds', 'large'); pg.wait_for_timeout(150)
    ok('changing the crowds applies at once, with no toast', js("() => DB.city.crowd") == 'large' and toasted() == '')
    ok('its row and the Life tab show a dot', js("() => document.querySelector('[data-set=\"crowd\"]').classList.contains('changed') && document.querySelector('.set-tab[data-tab=\"life\"]').classList.contains('changed')")
       and pg.is_visible('[data-set="crowd"] > .set-dot') and pg.is_visible('.set-tab[data-tab="life"] > .set-dot'))
    pg.select_option('#optCrowds', 'medium'); pg.wait_for_timeout(100)
    ok('back at its default, the dot goes', not js("() => document.querySelector('[data-set=\"crowd\"]').classList.contains('changed')"))
    # an action keeps its toast
    open_settings(pg, 'look')
    with pg.expect_download():
        pg.click('#btnPalette')
    pg.wait_for_timeout(150)
    ok(f'an action keeps its toast ({toasted()})', 'Palette saved' in toasted())

    # Reset to defaults, per tab: only that tab's settings; never the projects or the map
    open_settings(pg, 'life')
    pg.uncheck('#optCars'); js("() => { const r = document.querySelector('#optStreet'); r.value = 1.5; r.dispatchEvent(new Event('input')); }"); pg.select_option('#optCrowds', 'small')
    open_settings(pg, 'look'); pg.click('#optMotion [data-value="saver"]')
    before = js("() => [DB.projects.length, JSON.stringify(DB.world)]")
    open_settings(pg, 'life'); pg.click('#btnTabReset'); pg.wait_for_timeout(150)
    ok('Reset to defaults puts back the tab\'s settings', js("() => DB.city.cars && DB.city.street === 1 && DB.city.crowd === 'medium'") and not js("() => document.querySelector('.set-tab[data-tab=\"life\"]').classList.contains('changed')"))
    ok('and only that tab\'s: Motion in Look stays as set', js("() => Motion.mode()") == 'saver' and js("() => document.querySelector('.set-tab[data-tab=\"look\"]').classList.contains('changed')"))
    ok('never the projects or the map', js("() => [DB.projects.length, JSON.stringify(DB.world)]") == before)
    open_settings(pg, 'saving')
    ok('the Saving tab holds connections, not preferences, so it has no Reset to defaults', not pg.is_visible('#btnTabReset') and pg.is_visible('#btnResetAll'))

    # Reset all settings, at the bottom, behind a confirm; the parks picked in Edit City stay
    open_settings(pg, 'projects'); pg.click('#optRest [data-day="6"]'); pg.wait_for_timeout(100)
    js("() => { DB.city.parks['0,4'] = 'pond'; }")
    pg.click('#btnResetAll'); pg.wait_for_timeout(200)
    ok('Reset all settings asks first', pg.is_visible('.backdrop.top') and 'Reset all settings' in pg.text_content('#cfTitle'))
    pg.click('.confirm-actions .btn:not(.btn-danger)'); pg.wait_for_timeout(150)
    ok('Cancel keeps every setting', js("() => DB.city.rest.join() === '6' && Motion.mode() === 'saver'"))
    pg.click('#btnResetAll'); pg.wait_for_timeout(150); pg.click('.confirm-actions .btn-danger'); pg.wait_for_timeout(200)
    ok('confirmed, every setting is back at its default', js("() => DB.city.rest.length === 0 && Motion.mode() === Motion.dflt() && Light.mode === 'auto' && document.querySelectorAll('#setBody .changed, #setTabs .changed').length === 0"))
    ok('and the projects, the map and the parks picked stay', js("() => [DB.projects.length, JSON.stringify(DB.world)]") == before and js("() => DB.city.parks['0,4']") == 'pond')
    js("() => { delete DB.city.parks['0,4']; Light.setMode('day'); MapView.syncBar(); persistNow(); Settings.refresh(); }")

    # reopening where it was left: the same tab, and the same place on the page
    open_settings(pg, 'look')
    js("() => { document.querySelector('#menu').scrollTop = 60; document.querySelector('#menu').dispatchEvent(new Event('scroll')); }"); pg.wait_for_timeout(350)
    top = js("() => document.querySelector('#menu').scrollTop")
    open_settings(pg, 'city'); pg.wait_for_timeout(100)
    ok('each tab opens at its top the first time', js("() => document.querySelector('#menu').scrollTop") == 0)
    open_settings(pg, 'look'); pg.wait_for_timeout(100)
    ok(f'and back at a tab, the same place on its page ({top})', top >= 50 and abs(js("() => document.querySelector('#menu').scrollTop") - top) <= 1)
    close_settings(pg); pg.click('#btnOpenSettings'); pg.wait_for_timeout(200)
    ok('closed and opened again: the same tab, the same place', js("() => Settings.tab()") == 'look' and abs(js("() => document.querySelector('#menu').scrollTop") - top) <= 1)

    # every tab, to look at
    js("() => { document.querySelector('#menu').scrollTop = 0; MapView.setCam({ x: 0, y: 260, z: 2 }); }")
    for t in TABS:
        open_settings(pg, t); js("() => { document.querySelector('#menu').scrollTop = 0; }"); pg.wait_for_timeout(250)
        pg.screenshot(path=str(SH / f'200-settings-{t}.png'))
    from PIL import Image                                   # the six side bars in one sheet, to look at together
    crops = [Image.open(SH / f'200-settings-{t}.png').crop((0, 0, 296, 900)) for t in TABS]
    sheet = Image.new('RGB', (296 * 6 + 10 * 5, 900), (18, 15, 31))
    for k, im in enumerate(crops): sheet.paste(im, (k * 306, 0))
    sheet.save(SH / '203-settings-all-tabs.png')
    open_settings(pg, 'look'); pg.click('#optMotion [data-value="saver"]'); open_settings(pg, 'life'); pg.select_option('#optCrowds', 'large'); pg.wait_for_timeout(150)
    pg.screenshot(path=str(SH / '201-settings-dots.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 900})
    js("() => { Settings.resetTab('life'); Settings.resetTab('look'); Light.setMode('day'); MapView.syncBar(); }")
    b.close()

# small screens: the side bar is a drawer, and the gear opens it on Settings
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    q = b.new_page(viewport={'width': 600, 'height': 860})
    q.add_init_script(TEST_CITY)
    q.on('pageerror', lambda e: errors.append(str(e)))
    q.goto(FILE); q.wait_for_timeout(1500)
    q.click('#btnSettings'); q.wait_for_timeout(350)
    ok('on a narrow window the gear opens the drawer on Settings', q.evaluate("() => document.querySelector('#menu').classList.contains('open')") and q.is_visible('#settings'))
    q.screenshot(path=str(SH / '202-settings-narrow.png'))
    b.close()
print(errors or 'no console errors')
