from playwright.sync_api import sync_playwright
from testkit import open_settings, FILE, ROOT, SHOTS, SH, DATA, SKILLS, VERSION, fixture

errors = []
def ok(label, cond): print(('PASS ' if cond else 'FAIL ') + label)

FAKE = """([plan, perm]) => {
  window.__writes = []; window.__tries = 0;
  const outcome = () => { const o = plan[Math.min(window.__tries, plan.length - 1)]; window.__tries++; return o; };
  window.__h = { name: 'nullovation-city-data.json', kind: 'file',
    queryPermission: async () => perm, requestPermission: async () => 'granted',
    createWritable: async () => {
      const o = outcome();
      if (o !== 'ok') throw new DOMException('simulated', o);
      let buf = '';
      return { write: async t => { buf += t; }, close: async () => { window.__writes.push(buf.length); } };
    } };
  DataFile._test.fast(); DataFile._test.use(window.__h);
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    # no test city here: this pass needs no projects, and an init script in the context makes its two-tab checks flaky
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(FILE); pg.wait_for_timeout(1500)
    js = lambda code, *a: pg.evaluate(code, *a)
    open_settings(pg, 'saving')
    alert = lambda: (pg.is_visible('#fileAlert'), pg.text_content('#fileAlert') or '')
    # a file busy for a moment: quiet retries, then saved, no error
    js(FAKE, [['NoModificationAllowedError', 'NoModificationAllowedError', 'ok'], 'granted'])
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(700)
    ok(f'a file busy twice saves on the quiet retry ({js("() => window.__tries")} tries)', js("() => DataFile.state()") == 'on' and js("() => window.__writes.length") == 1 and not alert()[0])
    # a file that stays busy: said plainly, with Try again and Pick the file again
    js(FAKE, [['NoModificationAllowedError'], 'granted'])
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(800)
    vis, txt = alert()
    ok(f'a file that stays busy fails only after its retries ({js("() => window.__tries")} tries)', js("() => DataFile.state()") == 'failed' and js("() => DataFile.reason()") == 'busy' and js("() => window.__tries") == 4)
    ok('its message names the cause and offers both fixes', vis and 'the file was busy' in txt and 'Try again' in txt and 'Pick the file again' in txt)
    ok('Settings, Saving, says it too', 'stayed busy' in (pg.text_content('#fileBox') or '') and 'sync app' in (pg.text_content('#fileBox') or ''))
    js("() => { window.__tries = 99; }")                       # the file frees up
    js("() => { window.__h.createWritable = async () => { let b = ''; return { write: async t => { b += t; }, close: async () => { window.__writes.push(b.length); } }; }; }")
    pg.click('#fileAlert >> text=Try again'); pg.wait_for_timeout(400)
    ok('Try again saves once the file is free, and the message goes', js("() => DataFile.state()") == 'on' and js("() => window.__writes.length") == 1 and not alert()[0])
    # a moved or deleted file: said at once, no retries
    js(FAKE, [['NotFoundError'], 'granted'])
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(500)
    vis, txt = alert()
    ok('a moved file is said at once, without retrying', js("() => DataFile.reason()") == 'moved' and js("() => window.__tries") == 1 and vis and 'moved or deleted' in txt and 'Pick the file again' in txt)
    # permission that ended: paused, with Allow
    js(FAKE, [['NotAllowedError'], 'prompt'])
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(400)
    vis, txt = alert()
    ok('permission that ended becomes paused, with Allow it', js("() => DataFile.state()") == 'paused' and vis and 'Allow it' in txt)
    # two tabs: the one opened last writes; the other stands by and never writes
    js(FAKE, [['ok'], 'granted'])
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(300)
    ok('tab A writes while it is the only one', js("() => DataFile.isWriter()") and js("() => window.__writes.length") == 1)
    pg2 = ctx.new_page()
    pg2.on('pageerror', lambda e: errors.append(str(e)))
    pg2.goto(FILE); pg2.wait_for_timeout(1500)
    pg2.evaluate(FAKE, [['ok'], 'granted'])
    pg.wait_for_timeout(400)
    ok('opening tab B makes it the writer, and tab A stands by', pg2.evaluate("() => DataFile.isWriter()") and js("() => DataFile.state()") == 'standby')
    before = js("() => window.__writes.length")
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(300)
    ok('a tab on standby never writes', js("() => window.__writes.length") == before)
    ok('it says so calmly, and shows no alert', 'Another Nullovation City tab is saving' in (pg.text_content('#fileBox') or '') and not alert()[0])
    pg.bring_to_front(); pg.mouse.click(700, 450); pg.wait_for_timeout(400)
    ok('using tab A takes the writing back', js("() => DataFile.state()") == 'on' and js("() => DataFile.isWriter()") and pg2.evaluate("() => DataFile.state()") == 'standby')
    js("() => DataFile.writeNow()"); pg.wait_for_timeout(300)
    ok('and it writes again', js("() => window.__writes.length") == before + 1)
    ok('the version shown is the one in src/VERSION', pg.text_content('#appVersion') == 'v' + VERSION)
    b.close()
print(errors or 'no console errors')
